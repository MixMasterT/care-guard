import streamlit as st
import json
import os
import random
import socket
import threading
import time
from pathlib import Path
import re
from typing import Dict, List, Optional
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import asyncio
import websockets
from pydantic import BaseModel

try:
    # When imported as part of a package
    from .monitor_components.heartbeat_component import create_heartbeat_component
    from .monitor_components.ekg_component import create_ekg_component
    from .monitor_components.timeline_component import create_timeline_component
    from .utils import heartbeat_analysis
    from .utils import fhir_observations
except ImportError:
    # When run directly
    from monitor_components.heartbeat_component import create_heartbeat_component
    from monitor_components.ekg_component import create_ekg_component
    from monitor_components.timeline_component import create_timeline_component
    # Use explicit relative path to avoid conflict with root utils directory
    import sys
    from pathlib import Path
    utils_path = Path(__file__).parent / "utils"
    sys.path.insert(0, str(utils_path))
    import heartbeat_analysis
    import fhir_observations

# Set page config
st.set_page_config(
    page_title="Patient Monitor",
    page_icon="🏥",
    layout="wide"
)

# Global biometric buffer for batch writing
biometric_buffer = []
BATCH_SIZE = 10  # Write to file every 10 events
BUFFER_LOCK = threading.Lock()

def flush_biometric_buffer():
    """Write all buffered biometric events to the JSON file."""
    global biometric_buffer
    with BUFFER_LOCK:
        if not biometric_buffer:
            return
        
        try:
            # Ensure buffer directory exists
            buffer_dir = heartbeat_analysis.ensure_biometric_buffer_dir()
            biometric_file = buffer_dir / "simulation_biometrics.json"
            
            # Load existing records
            records = []
            if biometric_file.exists():
                try:
                    with open(biometric_file, 'r') as f:
                        records = json.load(f)
                    if not isinstance(records, list):
                        records = []
                except json.JSONDecodeError as e:
                    records = []
                except Exception as e:
                    records = []
            
            # Add all buffered records
            records.extend(biometric_buffer)
            
            # Write back to file with atomic write
            temp_file = biometric_file.with_suffix('.tmp')
            try:
                # Ensure the directory exists before writing
                buffer_dir.mkdir(parents=True, exist_ok=True)
                
                with open(temp_file, 'w') as f:
                    json.dump(records, f, indent=2, default=str)
                
                # Atomic move to replace the original file
                if temp_file.exists() and temp_file.stat().st_size > 0:
                    temp_file.replace(biometric_file)
                else:
                    print(f"⚠️ Temp file not created properly, skipping flush")
                    
            except Exception as e:
                # Clean up temp file if it exists
                if temp_file.exists():
                    try:
                        temp_file.unlink()
                    except:
                        pass  # Ignore cleanup errors
                print(f"❌ Error writing biometric buffer: {e}")
                import traceback
                traceback.print_exc()
            
            # Clear the buffer
            biometric_buffer = []
            
            # Trigger chart refresh by updating session state
            if 'chart_refresh_trigger' not in st.session_state:
                st.session_state.chart_refresh_trigger = 0
            st.session_state.chart_refresh_trigger += 1
            
        except Exception as e:
            print(f"❌ Error flushing biometric buffer: {e}")
            import traceback
            traceback.print_exc()

def record_biometric_event(event_type: str, timestamp: datetime, event_data: dict):
    """Record a biometric event to the in-memory buffer."""
    global biometric_buffer
    try:
        # Create biometric event record with medical data only
        event_record = {
            "event_type": event_type,
            "timestamp": timestamp.isoformat(),
            **event_data  # Spread medical data directly into the record
        }
        
        # Add to buffer
        with BUFFER_LOCK:
            biometric_buffer.append(event_record)
            buffer_size = len(biometric_buffer)
        
        # Flush buffer if it reaches batch size
        if buffer_size >= BATCH_SIZE:
            try:
                flush_biometric_buffer()
            except Exception as flush_error:
                print(f"⚠️ Biometric buffer flush failed, continuing: {flush_error}")
                # Don't let flush errors stop event recording
        
    except Exception as e:
        print(f"❌ Error recording biometric event: {e}")
        import traceback
        traceback.print_exc()

def clear_biometric_buffer():
    """Clear both the in-memory buffer and the biometric buffer file."""
    global biometric_buffer
    try:
        # Clear in-memory buffer
        with BUFFER_LOCK:
            biometric_buffer = []
        
        # Clear file buffer
        buffer_dir = heartbeat_analysis.ensure_biometric_buffer_dir()
        biometric_file = buffer_dir / "simulation_biometrics.json"
        if biometric_file.exists():
            biometric_file.unlink()
        
        # Chart data is cleared when buffer file is cleared
        
    except Exception as e:
        print(f"❌ Error clearing biometric buffer: {e}")

def load_fhir_files() -> List[Path]:
    """Load all FHIR patient files from the generated_medical_records (synthea output) directory."""
    # Debug: Print current working directory
    print(f"Current working directory: {os.getcwd()}")
    
    # Look for FHIR directory relative to the script location
    script_dir = Path(__file__).parent
    fhir_dir = script_dir / "generated_medical_records/fhir/"
    print(f"Looking for FHIR directory at: {fhir_dir}")
    print(f"Directory exists: {fhir_dir.exists()}")
    
    if not fhir_dir.exists():
        st.error(f"FHIR directory not found: {fhir_dir}")
        return []
    
    # Get all JSON files that look like patient files (contain patient names)
    patient_files = []
    for file_path in fhir_dir.glob("*.json"):
        if file_path.name.startswith(("practitionerInformation", "hospitalInformation")):
            continue  # Skip non-patient files
        patient_files.append(file_path)
    
    return patient_files

def calculate_age(birth_date_str: str) -> Optional[int]:
    """Calculate patient age from birth date string."""
    if not birth_date_str:
        return None
    
    try:
        birth_date = pd.to_datetime(birth_date_str)
        today = pd.Timestamp.now()
        age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
        return age
    except (ValueError, TypeError):
        return None

def parse_patient_data(file_path: Path) -> Dict:
    """Parse a FHIR patient file and extract relevant information."""
    
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        patient_info = {
            'file_path': file_path,
            'patient_name': None,
            'patient_id': None,
            'gender': None,
            'birth_date': None,
            'address': None,
            'diagnoses': [],
            'allergies': []
        }
        
        # Extract patient information from the bundle
        for entry in data.get('entry', []):
            resource = entry.get('resource', {})
            resource_type = resource.get('resourceType')
            
            if resource_type == 'Patient':
                # Extract patient basic info
                patient_info['patient_id'] = resource.get('id')
                
                # Extract name
                names = resource.get('name', [])
                if names:
                    name = names[0]  # Use the first name entry
                    given_names = name.get('given', [])
                    family_name = name.get('family', '')
                    prefix = name.get('prefix', [])
                    
                    full_name = ' '.join(prefix + given_names + [family_name])
                    patient_info['patient_name'] = full_name
                
                # Extract other patient info
                patient_info['gender'] = resource.get('gender')
                patient_info['birth_date'] = resource.get('birthDate')
                
                # Extract address
                addresses = resource.get('address', [])
                if addresses:
                    addr = addresses[0]
                    lines = addr.get('line', [])
                    city = addr.get('city', '')
                    state = addr.get('state', '')
                    postal_code = addr.get('postalCode', '')
                    
                    address_parts = lines + [city, state, postal_code]
                    patient_info['address'] = ', '.join(filter(None, address_parts))
            
            elif resource_type == 'Condition':
                # Extract diagnosis information
                code = resource.get('code', {})
                coding = code.get('coding', [])
                
                if coding:
                    diagnosis = {
                        'code': coding[0].get('code', ''),
                        'display': coding[0].get('display', ''),
                        'system': coding[0].get('system', ''),
                        'clinical_status': resource.get('clinicalStatus', {}).get('coding', [{}])[0].get('code', ''),
                        'onset_date': resource.get('onsetDateTime', ''),
                        'abatement_date': resource.get('abatementDateTime', ''),
                        'recorded_date': resource.get('recordedDate', '')
                    }
                    patient_info['diagnoses'].append(diagnosis)
            
            elif resource_type == 'AllergyIntolerance':
                # Extract allergy information
                code = resource.get('code', {})
                coding = code.get('coding', [])
                
                if coding:
                    allergy = {
                        'code': coding[0].get('code', ''),
                        'display': coding[0].get('display', ''),
                        'category': resource.get('category', []),
                        'criticality': resource.get('criticality', ''),
                        'recorded_date': resource.get('recordedDate', '')
                    }
                    patient_info['allergies'].append(allergy)
            
            elif resource_type == 'Procedure':
                # Extract procedure information
                code = resource.get('code', {})
                coding = code.get('coding', [])
                
                if coding:
                    # Get procedure date
                    procedure_date = resource.get('performedPeriod', {}).get('start', '')
                    if not procedure_date:
                        procedure_date = resource.get('performedDateTime', '')
                    
                    # Filter out procedures older than 3 months
                    from datetime import timezone
                    three_months_ago = datetime.now(timezone.utc) - timedelta(days=90)
                    if procedure_date:
                        try:
                            # Parse the procedure date
                            if 'T' in procedure_date:
                                proc_dt = datetime.fromisoformat(procedure_date.replace('Z', '+00:00'))
                            else:
                                proc_dt = datetime.fromisoformat(procedure_date)
                            
                            # Make sure procedure date is timezone-aware for comparison
                            if proc_dt.tzinfo is None:
                                # If procedure date is naive, assume it's in UTC
                                proc_dt = proc_dt.replace(tzinfo=timezone.utc)
                            
                            # Only include procedures from the last 3 months
                            if proc_dt >= three_months_ago:
                                procedure = {
                                    'code': coding[0].get('code', ''),
                                    'display': coding[0].get('display', ''),
                                    'system': coding[0].get('system', ''),
                                    'clinical_status': resource.get('status', ''),
                                    'onset_date': resource.get('performedPeriod', {}).get('start', ''),
                                    'abatement_date': resource.get('performedPeriod', {}).get('end', ''),
                                    'recorded_date': resource.get('performedDateTime', ''),
                                    'is_procedure': True
                                }
                                patient_info['diagnoses'].append(procedure)
                        except (ValueError, TypeError) as e:
                            # If date parsing fails, skip this procedure
                            print(f"Warning: Could not parse procedure date '{procedure_date}': {e}")
                            continue
                    else:
                        # If no date available, skip this procedure
                        continue
        
        return patient_info
        
    except Exception as e:
        st.error(f"Error parsing file {file_path}: {str(e)}")
        return None

def is_irrelevant_diagnosis(diagnosis: Dict) -> bool:
    """Check if a diagnosis is not actually medical and should be filtered out."""
    display = diagnosis.get('display', '').lower()
    
    # Filter out non-medical diagnoses
    education_keywords = [
        'education',
        'school',
        'college',
        'university',
        'degree',
        'graduation',
        'higher education',
        'received higher education',
        'academic',
        'learning',
        '(finding)',
        '(situation)'
    ]
    
    # Check if any education keywords are in the display text
    return any(keyword in display for keyword in education_keywords)

class HeartbeatClient:
    """Client for connecting to the heartbeat server."""
    
    def __init__(self, host='localhost', port=5000):
        self.host = host
        self.port = port
        self.socket = None
        self.connected = False
        self.running = False
        self.heartbeat_thread = None
        
    def connect(self):
        """Connect to the heartbeat server."""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            self.connected = True
            self.running = True
            
            # Start listening thread
            self.heartbeat_thread = threading.Thread(target=self._listen_for_biometrics)
            self.heartbeat_thread.daemon = True
            self.heartbeat_thread.start()
            
            st.success("Connected to heartbeat server!")
            return True
        except Exception as e:
            st.error(f"Failed to connect to heartbeat server: {e}")
            return False
    
    def _listen_for_biometrics(self):
        """Listen for biometric events from the server."""
        buffer = ""
        
        while self.running and self.connected:
            try:
                data = self.socket.recv(1024)
                if not data:
                    break
                
                buffer += data.decode('utf-8')
                
                # Process complete messages
                while '\n' in buffer:
                    message, buffer = buffer.split('\n', 1)
                    if message.strip():
                        try:
                            event = json.loads(message)
                            event_type = event.get('event_type')
                            
                            # Record only biometric events with medical data
                            if event_type in ['heartbeat', 'respiration', 'vital_signs']:
                                # Convert server timestamp to datetime
                                server_timestamp = event.get('timestamp', int(time.time() * 1000))
                                event_timestamp = datetime.fromtimestamp(server_timestamp / 1000.0)
                                
                                # Extract medical data based on event type and available fields
                                medical_data = {}
                                
                                if event_type == 'heartbeat':
                                    # Heartbeat events
                                    medical_data = {
                                        'interval_ms': event.get('interval_ms', 1000),
                                        'pulse_strength': event.get('pulse_strength', 1.0)
                                    }
                                    record_biometric_event('heartbeat', event_timestamp, medical_data)
                                    
                                elif event_type == 'respiration':
                                    # Respiration events (discrete breath completion)
                                    print(f'recording a respiration, for event: {event}')
                                    medical_data = {
                                        'interval_ms': event.get('interval_ms', 0)
                                    }
                                    record_biometric_event('respiration', event_timestamp, medical_data)
                                    
                                elif event_type == 'vital_signs':
                                    # Vital signs events can contain spo2, temperature, or ecg_rhythm
                                    if 'spo2' in event:
                                        medical_data = {
                                            'spo2': event.get('spo2')
                                        }
                                        record_biometric_event('spo2', event_timestamp, medical_data)
                                        
                                    elif 'temperature' in event:
                                        medical_data = {
                                            'temperature': event.get('temperature')
                                        }
                                        record_biometric_event('temperature', event_timestamp, medical_data)
                                        
                                    elif 'ecg_rhythm' in event:
                                        medical_data = {
                                            'ecg_rhythm': event.get('ecg_rhythm')
                                        }
                                        record_biometric_event('ecg_rhythm', event_timestamp, medical_data)
                                        
                                    elif 'blood_pressure' in event:
                                        medical_data = {
                                            'systolic': event.get('blood_pressure', {}).get('systolic'),
                                            'diastolic': event.get('blood_pressure', {}).get('diastolic')
                                        }
                                        record_biometric_event('blood_pressure', event_timestamp, medical_data)
                                
                            elif event_type == 'scenario_stopped':
                                # Update Streamlit session state to reflect that simulation has stopped
                                st.session_state.simulation_running = False
                                st.session_state.current_scenario = None
                                print(f"📊 Scenario stopped event received via TCP - session state updated")

                        except json.JSONDecodeError:
                            print('Unable to decode JSON in _listen_for_biometrics handler')
                            
            except Exception as e:
                break
        
        self.connected = False

def trigger_heartbeat_scenario(scenario: str):
    """Trigger a heartbeat scenario by sending command to server."""
    if 'heartbeat_client' not in st.session_state:
        st.error("Heartbeat client not connected!")
        return
    
    client = st.session_state.heartbeat_client
    if not client.connected:
        st.error("Not connected to heartbeat server!")
        return
    
    try:
        # Flush any remaining biometric events and clear buffer when starting new scenario
        flush_biometric_buffer()
        clear_biometric_buffer()
        
        # Update session state to track simulation
        st.session_state.simulation_running = True
        st.session_state.current_scenario = scenario
        
        # Send scenario command via TCP socket (primary method)
        command = json.dumps({"command": "start_scenario", "scenario": scenario})
        print(f"📤 Sending start command via TCP: {command}")
        client.socket.send((command + '\n').encode('utf-8'))
        
        # Also send via WebSocket as backup
        start_script = f"""
        <script>
        if (window.ws && window.ws.readyState === WebSocket.OPEN) {{
            window.ws.send(JSON.stringify({{
                command: 'start_scenario',
                scenario: '{scenario}'
            }}));
            console.log('🚀 Start command sent via WebSocket backup for {scenario}');
        }}
        </script>
        """
        st.components.v1.html(start_script, height=0)
        
        st.success(f"Started {scenario} heartbeat scenario!")
    except Exception as e:
        st.error(f"Failed to start scenario: {e}")
        # Reset state on error
        st.session_state.simulation_running = False
        st.session_state.current_scenario = None

def stop_heartbeat_scenario():
    """Stop the current heartbeat scenario."""
    if 'heartbeat_client' not in st.session_state:
        st.error("Heartbeat client not connected!")
        return
    
    client = st.session_state.heartbeat_client
    if not client.connected:
        st.error("Not connected to heartbeat server!")
        return
    
    try:
        print(f"🛑 Attempting to stop scenario: {st.session_state.current_scenario}")
        
        # Send stop command via TCP socket (primary method)
        command = json.dumps({"command": "stop_scenario"})
        print(f"📤 Sending stop command via TCP: {command}")
        client.socket.send((command + '\n').encode('utf-8'))
        
        # Also send via WebSocket as backup
        stop_script = """
        <script>
        if (window.ws && window.ws.readyState === WebSocket.OPEN) {
            window.ws.send(JSON.stringify({
                command: 'stop_scenario'
            }));
            console.log('🛑 Stop command sent via WebSocket backup');
        }
        </script>
        """
        st.components.v1.html(stop_script, height=0)
        
        # Flush any remaining biometric events before stopping
        flush_biometric_buffer()
        
        # Don't immediately reset session state - wait for backend confirmation
        # The session state will be updated when we receive the 'scenario_stopped' event
        
        print(f"✅ Stop command sent via TCP and WebSocket - waiting for backend confirmation")
        st.info("🔄 Stopping simulation... (waiting for backend confirmation)")
        
        # Note: We'll rely on the WebSocket handler to update session state when 'scenario_stopped' is received
        # The timeout mechanism was removed due to Streamlit session state thread safety issues
        
    except Exception as e:
        print(f"❌ Error stopping scenario: {e}")
        import traceback
        traceback.print_exc()
        st.error(f"Failed to stop scenario: {e}")


def create_diagnosis_timeline(diagnoses: List[Dict], time_window_percent: float = 100.0) -> go.Figure:
    """Create a timeline visualization of patient diagnoses."""
    if not diagnoses:
        return None
    
    # Filter out education-related diagnoses
    medical_diagnoses = [d for d in diagnoses if not is_irrelevant_diagnosis(d)]
    
    if not medical_diagnoses:
        return None
    
    # Prepare data for timeline
    timeline_data = []
    
    for diagnosis in medical_diagnoses:
        onset_date = diagnosis.get('onset_date')
        abatement_date = diagnosis.get('abatement_date')
        display = diagnosis.get('display', 'Unknown Diagnosis')
        status = diagnosis.get('clinical_status', 'unknown')
        
        if onset_date:
            try:
                # Parse onset date - handle different FHIR datetime formats
                onset_str = onset_date.replace('Z', '+00:00') if 'Z' in onset_date else onset_date
                onset_dt = pd.to_datetime(onset_str, utc=True)
                
                # Parse abatement date if it exists, otherwise use current date
                if abatement_date:
                    abatement_str = abatement_date.replace('Z', '+00:00') if 'Z' in abatement_date else abatement_date
                    abatement_dt = pd.to_datetime(abatement_str, utc=True)
                    end_date = abatement_dt
                    duration_days = (end_date - onset_dt).days
                else:
                    end_date = pd.Timestamp.now(tz='UTC')
                    duration_days = (end_date - onset_dt).days
                
                # Determine if this is a cardiac condition
                is_cardiac = any(keyword in display.lower() for keyword in [
                    'postoperative', 'coronary', 'heart', 'cardiac', 'bypass', 'cabg'
                ])
                
                # For cardiac conditions, ensure they have a reasonable duration for visibility
                if is_cardiac and abatement_date is None:
                    # If cardiac condition is active, extend it to show proper width
                    # Give each cardiac condition a different duration to avoid overlap
                    if 'postoperative' in display.lower():
                        end_date = onset_dt + pd.Timedelta(days=7)  # Postoperative state: 7 days
                    elif 'coronary' in display.lower():
                        end_date = onset_dt + pd.Timedelta(days=14)  # Coronary disease: 14 days
                    elif 'heart' in display.lower():
                        end_date = onset_dt + pd.Timedelta(days=21)  # Heart failure: 21 days
                    else:
                        end_date = onset_dt + pd.Timedelta(days=30)  # Default: 30 days
                
                timeline_data.append({
                    'Diagnosis': display,
                    'Start': onset_dt,
                    'End': end_date,
                    'Status': status,
                    'Duration_Days': duration_days,
                    'Is_Active': abatement_date is None,
                    'Is_Cardiac': is_cardiac
                })
                
            except (ValueError, TypeError) as e:
                print(f"Error parsing date for diagnosis {display}: {e}")
                continue
    
    if not timeline_data:
        return None
    
    # Create DataFrame
    df = pd.DataFrame(timeline_data)
    
    # Always create Display_Text column (needed for plotly)
    df['Display_Text'] = df['Diagnosis'].copy()
    
    # Apply time window filtering if not showing full timeline
    if time_window_percent < 100.0:
        # Calculate the time range to show
        if not df.empty:
            # Get the most recent date in the data
            max_date = df['Start'].max()
            
            # Calculate the time window (6 months = ~180 days)
            full_timeline_days = (df['Start'].max() - df['Start'].min()).days
            if full_timeline_days == 0:
                full_timeline_days = 1  # Avoid division by zero
            
            # Calculate how many days to show based on the slider percentage
            # At 0% slider, show full timeline. At 100% slider, show 6 months
            # Linear interpolation between full timeline and 6 months
            progress = time_window_percent / 100.0
            days_to_show = full_timeline_days - (full_timeline_days - 180) * progress
            days_to_show = max(180, int(days_to_show))  # At least 6 months
            
            # Calculate the cutoff date for the visible window
            cutoff_date = max_date - pd.Timedelta(days=days_to_show)
            
            # Instead of filtering out old diagnoses, mark them as past events
            # But cardiac conditions should always show their full width
            df['Is_Past_Event'] = (df['Start'] < cutoff_date) & (~df['Is_Cardiac'])
            df.loc[df['Is_Past_Event'], 'Display_Text'] = df.loc[df['Is_Past_Event'], 'Diagnosis'] + ' (past event)'
            
            # For past events (non-cardiac), set the visual timeline to be very short (just a dot)
            df.loc[df['Is_Past_Event'], 'End'] = df.loc[df['Is_Past_Event'], 'Start'] + pd.Timedelta(hours=1)
    
    # Sort by recency: most recent conditions first (by start date, then by active status)
    df['Sort_Key'] = df['Start'].astype(np.int64) * -1  # Most recent first
    df = df.sort_values('Sort_Key', ascending=True)
    
    # Reorder the y-axis to match the sorting (most recent at top)
    df = df.iloc[::-1].reset_index(drop=True)
    
    # Ensure datetime columns are properly formatted and convert to timezone-naive
    df['Start'] = pd.to_datetime(df['Start'], utc=True).dt.tz_localize(None)
    df['End'] = pd.to_datetime(df['End'], utc=True).dt.tz_localize(None)
    
    # Create custom color mapping for cardiac conditions
    color_mapping = {}
    for idx, row in df.iterrows():
        if row['Is_Cardiac']:
            color_mapping[row['Diagnosis']] = 'red'  # Cardiac conditions in red
        else:
            # Use status-based colors for non-cardiac conditions
            if row['Status'] == 'active':
                color_mapping[row['Diagnosis']] = 'orange'
            elif row['Status'] == 'resolved':
                color_mapping[row['Diagnosis']] = 'blue'
            elif row['Status'] == 'inactive':
                color_mapping[row['Diagnosis']] = 'lightgray'
            else:
                color_mapping[row['Diagnosis']] = 'lightgray'
    
    # Create timeline using plotly express with explicit color mapping
    fig = px.timeline(df, 
                     x_start="Start", 
                     x_end="End", 
                     y="Display_Text",  # Use display text that includes "(past event)" for old items
                     color="Diagnosis",  # Color by diagnosis name to use custom mapping
                     title="Patient Diagnosis Timeline",
                     hover_data=["Status"])
    
    # Apply custom colors manually to ensure cardiac conditions are red
    for trace in fig.data:
        diagnosis_name = trace.name
        if diagnosis_name in color_mapping:
            trace.marker.color = color_mapping[diagnosis_name]
    
    # Customize the layout
    fig.update_layout(
        title_x=0.5,
        title_font_size=20,
        xaxis_title="Time",
        yaxis_title="Diagnoses",
        height=400,  # Fixed height to prevent resizing
        showlegend=True
    )
    
    # Update x-axis to show dates nicely and scale with time window
    if time_window_percent < 100.0 and not df.empty:
        # Calculate the visible time range based on slider
        max_date = df['Start'].max()
        full_timeline_days = (df['Start'].max() - df['Start'].min()).days
        if full_timeline_days == 0:
            full_timeline_days = 1
        
        progress = time_window_percent / 100.0
        days_to_show = full_timeline_days - (full_timeline_days - 180) * progress
        days_to_show = max(180, int(days_to_show))
        
        # Set x-axis range to show only the visible time window
        min_visible_date = max_date - pd.Timedelta(days=days_to_show)
        fig.update_xaxes(
            range=[min_visible_date, max_date],
            tickformat="%Y-%m-%d",
            tickangle=45
        )
    else:
        # Show full timeline
        fig.update_xaxes(
            tickformat="%Y-%m-%d",
            tickangle=45
        )
    
    return fig

async def websocket_handler(websocket, path):
    # Handle WebSocket connections from browser
    while True:
        message = await websocket.recv()
        if message == 'heartbeat':
            # When heartbeat received, send to all WebSocket clients
            await websocket.send('heartbeat')

def main():
    print("🚀 Main function called")
    
    # Add custom CSS to ensure full width for components
    st.markdown("""
    <style>
    .stApp {
        max-width: 100%;
    }
    .main .block-container {
        max-width: 100%;
        padding-left: 1rem;
        padding-right: 1rem;
    }
    /* Force all iframes to full width */
    iframe {
        width: 100% !important;
        max-width: none !important;
        min-width: 100% !important;
    }
    /* Target Streamlit's specific iframe containers */
    [data-testid="stHorizontalBlock"] iframe,
    [data-testid="stVerticalBlock"] iframe,
    [data-testid="stBlock"] iframe {
        width: 100% !important;
        max-width: none !important;
        min-width: 100% !important;
    }
    /* Override any width constraints */
    .stHorizontalBlock iframe,
    .stVerticalBlock iframe,
    .stBlock iframe,
    .stMarkdown iframe {
        width: 100% !important;
        max-width: none !important;
        min-width: 100% !important;
    }
    /* Target the specific div that contains iframes */
    div[data-testid="stHorizontalBlock"] > div,
    div[data-testid="stVerticalBlock"] > div {
        width: 100% !important;
        max-width: none !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.title("🏥 Patient Monitor")
    
    # Initialize session state for simulation tracking
    if 'simulation_running' not in st.session_state:
        st.session_state.simulation_running = False
    if 'current_scenario' not in st.session_state:
        st.session_state.current_scenario = None
    if 'chart_refresh_counter' not in st.session_state:
        st.session_state.chart_refresh_counter = 0
    
    # Initialize session state for agentic solutions
    if 'agentic_solution' not in st.session_state:
        st.session_state.agentic_solution = "Crewai"
    if 'agentic_analysis_running' not in st.session_state:
        st.session_state.agentic_analysis_running = False
    if 'agentic_results' not in st.session_state:
        st.session_state.agentic_results = None
    if 'agent_monitor_data' not in st.session_state:
        st.session_state.agent_monitor_data = []
    
    # Heartbeat monitoring section
    st.subheader("💓 Heartbeat Monitoring")
    
    # Initialize heartbeat client if not exists
    if 'heartbeat_client' not in st.session_state:
        st.session_state.heartbeat_client = HeartbeatClient()
    
    # Heartbeat controls
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # Connection and scenario buttons
        if not st.session_state.heartbeat_client.connected:
            if st.button("🔌 Connect to Heartbeat Server"):
                if st.session_state.heartbeat_client.connect():
                    st.rerun()  # Force a rerun to update the UI immediately
        else:
            st.success("✅ Connected to heartbeat server")
            
            # Show current simulation status
            if st.session_state.simulation_running:
                st.info(f"🔄 Current simulation: {st.session_state.current_scenario}")
                
                # Show biometric recording status
                buffer_dir = heartbeat_analysis.ensure_biometric_buffer_dir()
                biometric_file = buffer_dir / "simulation_biometrics.json"
                
                # Count file records
                file_count = 0
                if biometric_file.exists():
                    try:
                        with open(biometric_file, 'r') as f:
                            records = json.load(f)
                        file_count = len(records) if isinstance(records, list) else 0
                    except (json.JSONDecodeError, Exception) as e:
                        st.error(f"❌ Error reading biometric data: {e}")
                        file_count = 0
                
                # When simulation is running, only show the stop button
                if st.button("⏹️ Stop Simulation", type="secondary"):
                    stop_heartbeat_scenario()
            else:
                st.info("⏸️ No simulation currently running")
                
                # When no simulation is running, show the scenario start buttons
                scenario_col1, scenario_col2, scenario_col3 = st.columns(3)
                
                with scenario_col1:
                    if st.button("❤️ Normal Heartbeat"):
                        trigger_heartbeat_scenario("normal")
                        st.rerun()  # Force a rerun to update the UI immediately
                
                with scenario_col2:
                    if st.button("💔 Irregular Heartbeat"):
                        trigger_heartbeat_scenario("irregular")
                        st.rerun()  # Force a rerun to update the UI immediately
                
                with scenario_col3:
                    if st.button("🚨 Critical"):
                        trigger_heartbeat_scenario("critical")
                        st.rerun()  # Force a rerun to update the UI immediately
    
    with col2:
        # Heartbeat visualization with JavaScript
        if st.session_state.heartbeat_client.connected:
            
            # JavaScript heartbeat component with WebSocket
            heartbeat_html = create_heartbeat_component()
            st.components.v1.html(heartbeat_html, height=200)
            
            # Add JavaScript to handle WebSocket events and update Streamlit state
            websocket_handler_script = """
            <script>
            // Listen for messages from the iframe
            window.addEventListener('message', function(event) {
                if (event.data.type === 'scenario_started') {
                    // The scenario state will be updated by the trigger function
                } else if (event.data.type === 'scenario_stopped') {
                    // Update the UI to reflect that simulation has stopped
                    // Don't reload the page - just update the display
                    console.log('Scenario stopped event received');
                    
                    // Find and update the simulation status display
                    const statusElements = document.querySelectorAll('[data-testid="stText"]');
                    statusElements.forEach(element => {
                        if (element.textContent.includes('Current simulation:')) {
                            element.textContent = '⏸️ No simulation currently running';
                        }
                    });
                    
                    // Update any other UI elements that show simulation status
                    // This prevents the need for a full page reload
                }
            });
            
            // Periodic check to sync state (every 2 seconds)
            setInterval(function() {
                // This will help catch any state mismatches between frontend and backend
            }, 2000);
            </script>
            """
            st.components.v1.html(websocket_handler_script, height=0)
        else:
            st.write("**Status:** Not connected to heartbeat server")
    
    # EKG Chart Section
    st.subheader("📈 Real-time EKG Monitor")
    
    if st.session_state.heartbeat_client.connected:
        # EKG visualization with D3.js
        ekg_html = create_ekg_component()
        # Create a full-width container for the EKG
        with st.container():
            st.components.v1.html(ekg_html, height=350, scrolling=True)
    else:
        st.info("🔌 Connect to heartbeat server to view EKG chart")
    
    st.markdown("---")

    # Handle agentic analysis execution in main area
    if st.session_state.agentic_analysis_running:
        # Get current patient name from session state
        patient_name = None
        fhir_file = None
        
        if 'selected_patient' in st.session_state:
            # Extract patient name from file path
            file_path = st.session_state.selected_patient
            filename = file_path.name  # Use full filename including extension
            fhir_file = filename
            
            if '_' in filename:
                parts = filename.split('_')
                if len(parts) >= 3:
                    # Map the extracted name to the expected patient names
                    first_name = parts[0]
                    last_name = parts[1]
                    
                    # Map to expected patient names
                    if first_name.lower().startswith('allen'):
                        patient_name = "Allen"
                    elif first_name.lower().startswith('mark'):
                        patient_name = "Mark"
                    elif first_name.lower().startswith('zach'):
                        patient_name = "Zach"
                    else:
                        # Fallback to original logic
                        patient_name = f"{first_name} {last_name}"
        
        if patient_name:
            # Launch agentic monitor app in new window
            agentic_url = f"http://localhost:8502/?run_id={st.session_state.current_run_id}&patient={patient_name}"
            
            # Use a more Safari-friendly approach
            js_code = f"""
            <script>
            // Try to open the window
            const newWindow = window.open('{agentic_url}', '_blank', 'width=1200,height=800,scrollbars=yes,resizable=yes');
            
            // Check if it was blocked
            if (!newWindow || newWindow.closed || typeof newWindow.closed == 'undefined') {{
                // Popup was blocked - show a more prominent message
                const popupBlockedDiv = document.createElement('div');
                popupBlockedDiv.innerHTML = `
                    <div style="background-color: #f8d7da; border: 1px solid #f5c6cb; padding: 15px; border-radius: 8px; margin: 15px 0; color: #721c24;">
                        <h4 style="margin: 0 0 10px 0;">⚠️ Popup Blocked</h4>
                        <p style="margin: 0 0 10px 0;">Your browser blocked the popup window. To view the agentic monitor:</p>
                        <ol style="margin: 0 0 10px 0; padding-left: 20px;">
                            <li>Click the link below to open manually</li>
                            <li>Or allow popups for this site in your browser settings</li>
                        </ol>
                        <a href="{agentic_url}" target="_blank" style="background-color: #007bff; color: white; padding: 8px 16px; text-decoration: none; border-radius: 4px; display: inline-block;">Open Agentic Monitor</a>
                    </div>
                `;
                document.body.appendChild(popupBlockedDiv);
            }} else {{
                // Successfully opened
                console.log('Agentic monitor window opened successfully');
            }}
            </script>
            """
            st.components.v1.html(js_code, height=0)
            
            st.success(f"🤖 Agentic Monitor launched for {patient_name}")
            st.info("The agentic analysis will run in a separate window. You can continue monitoring patients here.")
            
            # Always show manual link as backup
            st.markdown(f"""
            **Manual link:** [Open Agentic Monitor]({agentic_url})
            
            If the popup was blocked, click the manual link above to open the agentic monitor.
            """)
            
            # Reset the running state
            st.session_state.agentic_analysis_running = False
        else:
            st.error("❌ Could not determine patient name from selected file")
            st.session_state.agentic_analysis_running = False
    
    st.markdown("---")
    
    # Load patient files
    patient_files = load_fhir_files()
    
    if not patient_files:
        st.error("No patient files found. Please ensure the synthea output directory contains FHIR patient data.")
        return
    
    # Sidebar for controls
    st.sidebar.header("Controls")
    
    # Agentic Analysis Controls
    st.sidebar.subheader("🤖 Agentic Analysis")
    
    # Solution selector dropdown
    solution_options = ["Crewai"]  # Add other agentic monitoring solutions here as they become available
    selected_solution = st.sidebar.selectbox(
        "Select Agentic Solution:",
        solution_options,
        index=solution_options.index(st.session_state.agentic_solution)
    )
    st.session_state.agentic_solution = selected_solution
    
    # Run analysis button
    if st.sidebar.button("🚀 Run Analysis", key="run_analysis_button"):
        if 'selected_patient' in st.session_state:
            try:
                # Generate a run ID
                run_id = f"{datetime.now().strftime('%Y_%m_%d_%H_%M')}_{int(time.time())}"
                
                # Store run ID in session state
                st.session_state.current_run_id = run_id
                
                # Set session state to prevent multiple launches
                st.session_state.agentic_analysis_running = True
                
                # Show immediate feedback
                st.success(f"🚀 Starting agentic analysis for {st.session_state.selected_patient_display}...")
                st.info("This may take a few minutes. The analysis will run in the background.")
                
                # Launch agentic monitor with patient info
                agentic_url = f"http://localhost:8502?run_id={run_id}&patient={st.session_state.selected_patient_display}&framework={st.session_state.agentic_solution.lower()}"
                
                # Use Streamlit's link functionality instead of JavaScript popup
                st.markdown(f"""
                ## 🚀 Agentic Analysis Started!
                
                **Patient:** {st.session_state.selected_patient_display}  
                **Run ID:** {run_id}
                
                ### 📋 Next Steps:
                1. **Click the link below** to open the agentic monitor in a new tab
                2. The analysis will start automatically when the monitor opens
                3. You can continue monitoring patients here while the analysis runs
                
                **🔗 [Open Agentic Monitor]({agentic_url})**
                
                ---
                """)
                
                st.success(f"✅ Analysis setup complete! Click the link above to open the agentic monitor.")
                st.info(f"Framework: {st.session_state.agentic_solution}")
                
                # Force a rerun to update the UI state
                st.rerun()
                
            except Exception as e:
                st.error(f"❌ Error setting up analysis: {e}")
                # Reset session state on error
                st.session_state.agentic_analysis_running = False
                if 'current_run_id' in st.session_state:
                    del st.session_state.current_run_id
                return
        else:
            st.error("❌ Please select a patient first!")
            return
    

    
    # Patient selection
    st.sidebar.subheader("Select a patient:")
    patient_map = {}
    for file_path in patient_files:
        # Extract display name from filename, removing trailing digits
        filename = file_path.stem
        if '_' in filename:
            parts = filename.split('_')
            if len(parts) >= 3:
                first = re.sub(r"\d+$", "", parts[0])
                last = re.sub(r"\d+$", "", parts[1])
                display_name = f"{first} {last}".strip()
                patient_map[display_name] = file_path

    if patient_map:
        display_names = sorted(list(patient_map.keys()))

        # Determine current selection index from session state (stable across reruns)
        current_index = 0
        if 'selected_patient' in st.session_state:
            try:
                current_path = st.session_state.selected_patient
                # Find matching display name by path
                for name, path in patient_map.items():
                    if path == current_path:
                        current_index = display_names.index(name)
                        break
            except Exception:
                current_index = 0

        selected_display = st.sidebar.selectbox(
            "Choose a patient:",
            display_names,
            index=current_index,
            key="patient_select_name",
        )
        # Update session state immediately with current selection
        st.session_state.selected_patient = patient_map[selected_display]
        st.session_state.selected_patient_display = selected_display

    # Debug info in sidebar (placed after selection so it reflects current state)
    st.sidebar.markdown("---")
    st.sidebar.subheader("🔧 Debug Info")
    st.sidebar.write(f"Analysis Running: {st.session_state.agentic_analysis_running}")
    st.sidebar.write(f"Selected Patient: {'selected_patient' in st.session_state}")
    if 'selected_patient' in st.session_state:
        st.sidebar.write(f"Display Name: {st.session_state.get('selected_patient_display', 'N/A')}")
        st.sidebar.write(f"Patient File: {st.session_state.selected_patient.name}")

    # Agentic monitor status in sidebar
    st.sidebar.subheader("🤖 Agentic Monitor")

    # Check if agentic monitor is running
    try:
        import requests
        response = requests.get("http://localhost:8502", timeout=1)
        if response.status_code == 200:
            st.sidebar.success("✅ Agentic monitor ready")
            st.sidebar.info("Click 'Run Analysis' to launch the agentic monitor in a new window.")
        else:
            st.sidebar.warning("⚠️ Agentic monitor not responding")
    except:
        st.sidebar.error("❌ Agentic monitor not running")
        st.sidebar.markdown(
            """
        **To start the agentic monitor:**
        1. Open a new terminal
        2. Run: `cd patient && streamlit run agentic_monitor_app.py --server.port 8502`
        3. Or run: `python check_agentic_monitor.py --start`
        """
        )

    st.sidebar.markdown("The agentic analysis will run separately, allowing you to continue monitoring patients here.")

    st.sidebar.markdown("---")
    
    # Main content area
    if 'selected_patient' in st.session_state:
        patient_data = parse_patient_data(st.session_state.selected_patient)
        medical_diagnoses = [d for d in patient_data['diagnoses'] if not is_irrelevant_diagnosis(d)]
        
        if patient_data:
            # Filter out irrelevant diagnoses
            
            # Patient header
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.header(f"👤 {patient_data['patient_name'] or 'Unknown Patient'}")
                
                # Patient demographics
                st.subheader("📋 Patient Information")
                demo_col1, demo_col2 = st.columns(2)
                
                with demo_col1:
                    age = calculate_age(patient_data['birth_date'])
                    st.write(f"**Age:** {age} years old" if age is not None else "**Age:** Unknown")
                    st.write(f"**Gender:** {patient_data['gender'] or 'Unknown'}")
                
                with demo_col2:
                    st.write(f"**Birth Date:** {patient_data['birth_date'] or 'Unknown'}")
                    if patient_data['address']:
                        st.write(f"**Address:** {patient_data['address']}")
            
            with col2:
                st.metric("Diagnoses", len(medical_diagnoses))
                st.metric("Allergies", len(patient_data['allergies']))
            
            st.markdown("---")
            
            # Diagnoses section
            st.subheader("🏥 Diagnoses")
            
            if patient_data['diagnoses']:
                # Create D3-based timeline component
                timeline_html = create_timeline_component(patient_data)
                # Create a full-width container for the timeline
                with st.container():
                    st.components.v1.html(timeline_html, height=400, scrolling=True)
                
                st.markdown("---")
                
                # Button to show/hide detailed diagnoses
                if st.button("🔍 Show All Diagnoses"):
                    st.session_state.show_diagnoses = True
                
                if st.session_state.get('show_diagnoses', False):
                    for i, diagnosis in enumerate(medical_diagnoses, 1):
                        with st.expander(f"Diagnosis {i}: {diagnosis['display']}"):
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.write(f"**Code:** {diagnosis['code']}")
                                st.write(f"**System:** {diagnosis['system']}")
                                st.write(f"**Status:** {diagnosis['clinical_status']}")
                            
                            with col2:
                                if diagnosis['onset_date']:
                                    st.write(f"**Onset Date:** {diagnosis['onset_date']}")
                                if diagnosis['abatement_date']:
                                    st.write(f"**Abatement Date:** {diagnosis['abatement_date']}")
                                if diagnosis['recorded_date']:
                                    st.write(f"**Recorded Date:** {diagnosis['recorded_date']}")
            else:
                st.info("No diagnoses found for this patient.")
            
            # Allergies section
            if patient_data['allergies']:
                st.subheader("⚠️ Allergies")
                for allergy in patient_data['allergies']:
                    with st.expander(f"Allergy: {allergy['display']}"):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.write(f"**Code:** {allergy['code']}")
                            st.write(f"**Criticality:** {allergy['criticality']}")
                        
                        with col2:
                            if allergy['recorded_date']:
                                st.write(f"**Recorded Date:** {allergy['recorded_date']}")
                            if allergy['category']:
                                st.write(f"**Category:** {', '.join(allergy['category'])}")
    
    else:
        st.info("👈 Use the sidebar to select a patient to view their information.")
        
        # Show some statistics
        st.subheader("📊 Available Data")
        st.write(f"**Total Patients:** {len(patient_files)}")
        
        # Show a sample of available patients
        st.subheader("👥 Sample Patients")
        sample_patients = random.sample(patient_files, min(5, len(patient_files)))
        
        for file_path in sample_patients:
            filename = file_path.stem
            if '_' in filename:
                parts = filename.split('_')
                if len(parts) >= 3:
                    patient_name = f"{parts[0]} {parts[1]}"
                    st.write(f"• {patient_name}")

if __name__ == "__main__":
    main()
