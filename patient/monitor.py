import streamlit as st
import json
import os
import random
import socket
import threading
import time
from pathlib import Path
from typing import Dict, List, Optional
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import asyncio
import websockets
from pydantic import BaseModel
from monitor_components.heartbeat_component import create_heartbeat_component
from monitor_components.ekg_component import create_ekg_component
from monitor_components.timeline_component import create_timeline_component
import utils.heartbeat_analysis
import utils.fhir_observations

# Set page config
st.set_page_config(
    page_title="Patient Monitor",
    page_icon="🏥",
    layout="wide"
)

# Global heartbeat buffer for batch writing
heartbeat_buffer = []
BATCH_SIZE = 10  # Write to file every 10 heartbeats
BUFFER_LOCK = threading.Lock()

def flush_heartbeat_buffer():
    """Write all buffered heartbeats to the JSON file."""
    global heartbeat_buffer
    with BUFFER_LOCK:
        if not heartbeat_buffer:
            return
        
        try:
            # Ensure buffer directory exists
            buffer_dir = utils.heartbeat_analysis.ensure_biometric_buffer_dir()
            pulse_temp_file = buffer_dir / "pulse_temp.json"
            
            # Load existing records
            records = []
            if pulse_temp_file.exists():
                try:
                    with open(pulse_temp_file, 'r') as f:
                        records = json.load(f)
                    if not isinstance(records, list):
                        records = []
                except json.JSONDecodeError as e:
                    records = []
                except Exception as e:
                    records = []
            
            # Add all buffered records
            records.extend(heartbeat_buffer)
            
            # Write back to file with atomic write
            temp_file = pulse_temp_file.with_suffix('.tmp')
            try:
                # Ensure the directory exists before writing
                buffer_dir.mkdir(parents=True, exist_ok=True)
                
                with open(temp_file, 'w') as f:
                    json.dump(records, f, indent=2, default=str)
                
                # Atomic move to replace the original file
                if temp_file.exists() and temp_file.stat().st_size > 0:
                    temp_file.replace(pulse_temp_file)
                else:
                    print(f"⚠️ Temp file not created properly, skipping flush")
                    
            except Exception as e:
                # Clean up temp file if it exists
                if temp_file.exists():
                    try:
                        temp_file.unlink()
                    except:
                        pass  # Ignore cleanup errors
                print(f"❌ Error writing heartbeat buffer: {e}")
                import traceback
                traceback.print_exc()
            
            # Clear the buffer
            heartbeat_buffer = []
            
            # Trigger chart refresh by updating session state
            if 'chart_refresh_trigger' not in st.session_state:
                st.session_state.chart_refresh_trigger = 0
            st.session_state.chart_refresh_trigger += 1
            
        except Exception as e:
            print(f"❌ Error flushing heartbeat buffer: {e}")
            import traceback
            traceback.print_exc()

def record_heartbeat(timestamp: datetime, interval_ms: int = 0):
    """Record a heartbeat event to the in-memory buffer."""
    global heartbeat_buffer
    try:
        # Create heartbeat record
        heartbeat_record = utils.heartbeat_analysis.HeartbeatRecord(
            timestamp=timestamp,
            interval_ms=interval_ms
        )
        
        # Add to buffer
        with BUFFER_LOCK:
            heartbeat_buffer.append(heartbeat_record.dict())
            buffer_size = len(heartbeat_buffer)
        
        # Flush buffer if it reaches batch size
        if buffer_size >= BATCH_SIZE:
            try:
                flush_heartbeat_buffer()
            except Exception as flush_error:
                print(f"⚠️ Heartbeat buffer flush failed, continuing: {flush_error}")
                # Don't let flush errors stop heartbeat recording
        
    except Exception as e:
        print(f"❌ Error recording heartbeat: {e}")
        import traceback
        traceback.print_exc()

def clear_heartbeat_buffer():
    """Clear both the in-memory buffer and the heartbeat buffer file."""
    global heartbeat_buffer
    try:
        # Clear in-memory buffer
        with BUFFER_LOCK:
            heartbeat_buffer = []
        
        # Clear file buffer
        buffer_dir = utils.heartbeat_analysis.ensure_biometric_buffer_dir()
        pulse_temp_file = buffer_dir / "pulse_temp.json"
        if pulse_temp_file.exists():
            pulse_temp_file.unlink()
        
        # Chart data is cleared when buffer file is cleared
        
    except Exception as e:
        print(f"❌ Error clearing heartbeat buffer: {e}")

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
            self.heartbeat_thread = threading.Thread(target=self._listen_for_heartbeats)
            self.heartbeat_thread.daemon = True
            self.heartbeat_thread.start()
            
            st.success("Connected to heartbeat server!")
            return True
        except Exception as e:
            st.error(f"Failed to connect to heartbeat server: {e}")
            return False
    
    def _listen_for_heartbeats(self):
        """Listen for heartbeat events from the server."""
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
                            if event.get('event_type') == 'heartbeat':
                                interval_ms = event.get('interval_ms', 1000)
                                scenario = event.get('scenario', 'unknown')
                                event_number = event.get('event_number', 0)
                                
                                # Record heartbeat to JSON file with server timestamp
                                server_timestamp = event.get('timestamp', int(time.time() * 1000))
                                heartbeat_timestamp = datetime.fromtimestamp(server_timestamp / 1000.0)
                                record_heartbeat(heartbeat_timestamp, interval_ms)
                                
                            elif event.get('event_type') == 'scenario_stopped':
                                # Update Streamlit session state to reflect that simulation has stopped
                                st.session_state.simulation_running = False
                                st.session_state.current_scenario = None

                        except json.JSONDecodeError:
                            print('Unable to decode JSON in _listen_for_heartbeats handler')
                            
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
        # Flush any remaining heartbeats and clear buffer when starting new scenario
        flush_heartbeat_buffer()
        clear_heartbeat_buffer()
        
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
        
        # Flush any remaining heartbeats before stopping
        flush_heartbeat_buffer()
        
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

def trigger_heartbeat_animation():
    """Trigger heartbeat animation via JavaScript."""
    # We'll use st.components.html to inject JavaScript that can be called
    # This is a placeholder - the actual triggering will happen via session state
    pass

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
    st.title("🏥 Patient Monitor")
    
    # Initialize session state for simulation tracking
    if 'simulation_running' not in st.session_state:
        st.session_state.simulation_running = False
    if 'current_scenario' not in st.session_state:
        st.session_state.current_scenario = None
    if 'chart_refresh_counter' not in st.session_state:
        st.session_state.chart_refresh_counter = 0
    
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
                
                # Show heartbeat recording status
                buffer_dir = utils.heartbeat_analysis.ensure_biometric_buffer_dir()
                pulse_temp_file = buffer_dir / "pulse_temp.json"
                
                # Count file records
                file_count = 0
                if pulse_temp_file.exists():
                    try:
                        with open(pulse_temp_file, 'r') as f:
                            records = json.load(f)
                        file_count = len(records) if isinstance(records, list) else 0
                    except (json.JSONDecodeError, Exception) as e:
                        st.error(f"❌ Error reading heartbeat data: {e}")
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
                    if st.button("🫀 Cardiac Arrest"):
                        trigger_heartbeat_scenario("cardiac-arrest")
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
                    // Force a page reload to update the Streamlit state
                    window.location.reload();
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
        st.components.v1.html(ekg_html, height=350)
    else:
        st.info("🔌 Connect to heartbeat server to view EKG chart")
    
    st.markdown("---")
    
    # Load patient files
    patient_files = load_fhir_files()
    
    if not patient_files:
        st.error("No patient files found. Please ensure the synthea output directory contains FHIR patient data.")
        return
    
    # Sidebar for controls
    st.sidebar.header("Controls")
    
    # Random patient selection
    if st.sidebar.button("🎲 Select Random Patient"):
        selected_file = random.choice(patient_files)
        st.session_state.selected_patient = selected_file
    
    # Manual patient selection
    st.sidebar.subheader("Or select a specific patient:")
    patient_names = []
    for file_path in patient_files:
        # Try to extract a readable name from the filename
        filename = file_path.stem
        if '_' in filename:
            parts = filename.split('_')
            if len(parts) >= 3:
                patient_names.append((f"{parts[0]} {parts[1]}", file_path))
    
    if patient_names:
        selected_name, selected_file = st.sidebar.selectbox(
            "Choose a patient:",
            patient_names,
            format_func=lambda x: x[0]
        )
        st.session_state.selected_patient = selected_file
    
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
                st.components.v1.html(timeline_html, height=500)
                
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
