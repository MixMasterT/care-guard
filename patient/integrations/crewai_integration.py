"""
CrewAI integration for agentic monitoring.
Handles CrewAI-specific setup and execution.
"""

import json
import tempfile
import sys
import time
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

# Add the crew directory to the path so we can import CrewAI modules
crew_path = Path(__file__).parent.parent.parent / "crew"
if crew_path.exists():
    sys.path.insert(0, str(crew_path))

from .base_integration import BaseIntegration


class CrewaiIntegration(BaseIntegration):
    """CrewAI-specific integration for agentic monitoring."""
    
    def __init__(self):
        super().__init__()  # Call parent constructor
        self.framework_name = "CrewAI"
        self.crew_module = None
        self._load_crew_module()
    
    def _load_crew_module(self):
        """Load the CrewAI crew module."""
        try:
            # Try to import the cardio monitor crew using the correct path
            import sys
            crew_path = Path(__file__).parent.parent.parent / "crew" / "cardio_monitor" / "src"
            if crew_path.exists():
                sys.path.insert(0, str(crew_path))
                from cardio_monitor.crew import CardioMonitor
                self.crew_module = CardioMonitor
            else:
                print(f"⚠️ Warning: Crew path not found: {crew_path}")
                self.crew_module = None
        except ImportError as e:
            print(f"⚠️ Warning: Could not import CrewAI crew module: {e}")
            self.crew_module = None
    
        # get_framework_name is inherited from BaseIntegration
    
    def test_availability(self) -> Dict[str, Any]:
        """Test if CrewAI is available and ready to run."""
        if self.crew_module is None:
            return {
                "available": False,
                "error": "CrewAI crew module not available. Please ensure the crew directory is properly set up."
            }
        
        try:
            # Try to create a crew instance to test availability
            crew = self.crew_module()
            return {
                "available": True,
                "message": "CrewAI is available and ready to run"
            }
        except Exception as e:
            return {
                "available": False,
                "error": f"Error testing CrewAI availability: {str(e)}"
            }

    def run_agentic_analysis(self, patient_name: str, run_id: Optional[str] = None, timestamp: Optional[str] = None) -> Dict[str, Any]:
        """Run CrewAI analysis for a patient."""
        if self.crew_module is None:
            return {
                "success": False,
                "error": "CrewAI crew module not available"
            }
        
        # Start performance tracking
        self._start_performance_tracking()
        
        try:
            # Generate run_id if not provided
            if not run_id:
                # Generate a simple, clean run_id for file naming
                run_id = f"run_{int(time.time())}"
            else:
                # Ensure run_id is clean for file naming (remove any special characters)
                run_id = str(run_id).replace(' ', '_').replace('/', '_').replace('\\', '_')
            
            print(f"🚀 Starting CrewAI analysis for {patient_name} with run_id: {run_id}")
            
            # Create logs directory
            logs_dir = Path(__file__).parent.parent / "agentic_monitor_logs"
            logs_dir.mkdir(exist_ok=True)
            
            # Use provided timestamp or generate fallback
            if timestamp:
                print(f"✅ Using provided timestamp: {timestamp}")
                # Ensure timestamp is in the correct format for file naming
                formatted_timestamp = timestamp.replace('_', '_')  # Already in correct format
            else:
                # Generate fallback timestamp
                formatted_timestamp = datetime.now().strftime('%Y_%m_%d_%H_%M')
                print(f"⚠️ No timestamp provided, using generated: {formatted_timestamp}")
            
            # Create consolidated execution log with correct naming - use proper case for consistency
            # Ensure patient_name is properly formatted for file naming (first letter capitalized)
            formatted_patient_name = patient_name.title() if patient_name else "Unknown"
            execution_log_file = logs_dir / f"{formatted_timestamp}_{formatted_patient_name}_execution_log.json"
            execution_log = {
                "run_id": run_id,
                "patient_name": patient_name,
                "started_at": datetime.now().isoformat(),
                "events": [],
                "progress": [],
                "status": "starting",
                "progress_percent": 0
            }
            
            # Helper function to add events to execution log
            def add_event(event_type, message, data=None):
                event = {
                    "timestamp": datetime.now().isoformat(),
                    "type": event_type,
                    "message": message
                }
                if data:
                    # Ensure data is properly structured for JSON serialization
                    if isinstance(data, dict):
                        # Process nested structures to ensure they're JSON-serializable
                        processed_data = {}
                        for key, value in data.items():
                            if isinstance(value, str) and value.startswith('{') and value.endswith('}'):
                                # Try to parse as JSON if it looks like JSON
                                try:
                                    parsed = json.loads(value)
                                    processed_data[key] = parsed
                                except:
                                    processed_data[key] = value
                            else:
                                processed_data[key] = value
                        event["data"] = processed_data
                    else:
                        event["data"] = data
                execution_log["events"].append(event)
                
                # Write updated log to file immediately for real-time UI updates
                # Use atomic write to avoid file corruption
                try:
                    import tempfile
                    import os
                    
                    # Create a temporary file first
                    temp_file = execution_log_file.with_suffix('.tmp')
                    with open(temp_file, 'w') as f:
                        json.dump(execution_log, f, indent=2, default=str, ensure_ascii=False)
                    
                    # Atomic rename to avoid corruption
                    temp_file.replace(execution_log_file)
                except Exception as e:
                    print(f"⚠️ Warning: Could not write execution log: {e}")
            
            # Helper function to add progress updates
            def add_progress(percent, status, message=None):
                progress_entry = {
                    "timestamp": datetime.now().isoformat(),
                    "percent": percent,
                    "status": status
                }
                if message:
                    progress_entry["message"] = message
                execution_log["progress"].append(progress_entry)
                execution_log["status"] = status
                execution_log["progress_percent"] = percent
                
                # Write updated log to file immediately for real-time UI updates
                # Use atomic write to avoid file corruption
                try:
                    import tempfile
                    import os
                    
                    # Create a temporary file first
                    temp_file = execution_log_file.with_suffix('.tmp')
                    with open(temp_file, 'w') as f:
                        json.dump(execution_log, f, indent=2, default=str, ensure_ascii=False)
                    
                    # Atomic rename to avoid corruption
                    temp_file.replace(execution_log_file)
                except Exception as e:
                    print(f"⚠️ Warning: Could not write execution log: {e}")
            
            # Add initial event
            add_event("analysis_started", f"Starting CrewAI analysis for {patient_name}")
            add_progress(10, "starting", "Analysis initialization")
            
            # Create crew instance
            crew = self.crew_module()
            
            # Get workspace root for file paths - this should be the actual workspace root
            workspace_root = Path(__file__).parent.parent.parent  # patient/integrations/ -> patient/ -> workspace_root
            
            # Process temporal data to convert offset_ms to actual timestamps
            print(f"🕒 Processing temporal data for {patient_name}...")
            temporal_data = self._process_temporal_data(patient_name)
            
            # Use AgenticPatientDataLoader to get summarized data
            try:
                from agentic_data_loader import AgenticPatientDataLoader
                data_loader = AgenticPatientDataLoader(patient_name, workspace_root / 'patient')
                patient_context = data_loader.get_agent_specific_context("care_coordination", max_tokens=15000)
            except ImportError:
                print("⚠️ AgenticPatientDataLoader not available, using basic context")
                patient_context = f"Patient {patient_name} - basic context"
            
            # Get file paths
            file_paths = self._discover_patient_file_paths(patient_name)
            
            # Build inputs using the data loader approach
            inputs = {
                'topic': 'Cardio Monitoring Analysis',
                'current_year': str(datetime.now().year),
                'patient_name': formatted_patient_name,  # Use formatted name for consistency
                'biometric_buffer_path': str(workspace_root / 'patient' / 'biometric' / 'buffer' / 'simulation_biometrics.json'),
                'pain_diary_path': file_paths.get('pain_diary_path', ''),
                'weight_data_path': str(workspace_root / 'patient' / 'biometric' / 'weight' / f'{patient_name.lower()}.json'),
                # Template variables for output_file interpolation - these MUST match the template variables in tasks.yaml
                'timestamp': formatted_timestamp,  # Format: YYYY_MM_DD_HH_MM
                'run_id': run_id,        # Should be a simple string
                'patient_name': formatted_patient_name,  # For file naming - use formatted name
                'processed_weight_data': temporal_data['weight_data'],
                'processed_pain_diary_data': temporal_data['pain_diary_data'],
                'patient_context': patient_context,
                'framework': 'crewai'  # Add framework information for the agents
            }
            
            add_event("inputs_configured", "Analysis inputs configured", {
                "file_paths": {k: v for k, v in inputs.items() if 'path' in k},
                "template_variables": {
                    "timestamp": inputs['timestamp'],
                    "run_id": inputs['run_id'],
                    "patient_name": inputs['patient_name']
                }
            })
            
            # Update progress to running
            add_progress(30, "running", "CrewAI execution starting")
            
            # Run the crew using the run() function from main.py
            print(f"🤖 Starting CrewAI analysis...")
            add_event("crew_creation", "Starting CrewAI analysis")
            add_progress(40, "running", "CrewAI analysis started")
            
            try:
                # Import and call the run function from main.py
                import sys
                sys.path.insert(0, str(workspace_root / 'crew' / 'cardio_monitor' / 'src'))
                from cardio_monitor.main import run
                
                # Call the run function with our inputs dictionary
                result = run(inputs=inputs)
                
                # Final progress update
                add_progress(100, "completed", "Analysis completed successfully")
                add_event("analysis_completed", "Analysis completed successfully", {"result": str(result)})
                
                # Post-process output files to ensure proper JSON formatting
                self._format_output_files(patient_name, formatted_timestamp, run_id)
                
                # Ensure temporary files are cleaned up
                logs_dir = Path(__file__).parent.parent / "agentic_monitor_logs"
                self._cleanup_temp_files(logs_dir)
                
                print(f"✅ CrewAI analysis completed for {patient_name}")
                
                # End performance tracking with success
                self._end_performance_tracking(success=True)
                
                return {
                    "success": True,
                    "result": result,
                    "run_id": run_id,
                    "patient_name": patient_name,
                    "framework": "crewai",
                    "execution_log": str(execution_log_file),
                    "performance_metrics": self._get_performance_metrics()
                }
                
            except Exception as e:
                print(f"❌ Error during CrewAI execution: {e}")
                import traceback
                traceback.print_exc()
                
                add_event("analysis_failed", f"Analysis failed: {str(e)}", {"error": str(e)})
                add_progress(0, "failed", f"Analysis failed: {str(e)}")
                
                # Update progress to failed
                try:
                    execution_log["status"] = "failed"
                    execution_log["progress_percent"] = 0
                    execution_log["error"] = str(e)
                    execution_log["failed_at"] = datetime.now().isoformat()
                    
                    with open(execution_log_file, 'w') as f:
                        json.dump(execution_log, f, indent=2, default=str, ensure_ascii=False)
                    print(f"📊 Execution log updated: failed - 0%")
                except Exception as e2:
                    print(f"⚠️ Warning: Could not update execution log: {e2}")
                
                # Clean up temporary files even on failure
                try:
                    logs_dir = Path(__file__).parent.parent / "agentic_monitor_logs"
                    self._cleanup_temp_files(logs_dir)
                except Exception as cleanup_error:
                    print(f"⚠️ Warning: Could not cleanup temp files: {cleanup_error}")
                
                # End performance tracking with failure
                self._end_performance_tracking(success=False, error_message=str(e))
                
                return {
                    "success": False,
                    "error": f"Error running agentic analysis: {str(e)}",
                    "run_id": run_id,
                    "patient_name": patient_name,
                    "framework": "crewai",
                    "execution_log": str(execution_log_file) if 'execution_log_file' in locals() else None,
                    "performance_metrics": self._get_performance_metrics()
                }
            
        except Exception as e:
            print(f"❌ Error in CrewAI analysis: {e}")
            import traceback
            traceback.print_exc()
            
            # End performance tracking with failure
            self._end_performance_tracking(success=False, error_message=str(e))
            
            return {
                "success": False,
                "error": f"Error running agentic analysis: {str(e)}",
                "run_id": run_id,
                "patient_name": patient_name,
                "framework": "crewai",
                "performance_metrics": self._get_performance_metrics()
            }
    
    def _format_output_files(self, patient_name: str, timestamp: str, run_id: str):
        """
        Post-process output files to ensure proper JSON formatting.
        This method reads the raw output files created by CrewAI and reformats them with proper indentation.
        Also cleans up any temporary files.
        """
        try:
            logs_dir = Path(__file__).parent.parent / "agentic_monitor_logs"
            
            # List of output file types to format
            output_types = [
                'triage_decision',
                'medical_log', 
                'biometric_analysis'
            ]
            
            for output_type in output_types:
                # Updated to match new file naming convention
                file_path = logs_dir / f"{timestamp}_{patient_name}_{output_type}.json"
                
                if file_path.exists():
                    try:
                        # Read the raw file
                        with open(file_path, 'r') as f:
                            content = f.read().strip()
                        
                        # Try to parse as JSON and reformat
                        try:
                            data = json.loads(content)
                            # Write back with proper formatting
                            with open(file_path, 'w') as f:
                                json.dump(data, f, indent=2, default=str, ensure_ascii=False)
                            print(f"   ✅ Formatted {output_type} output file")
                        except json.JSONDecodeError:
                            print(f"   ⚠️ Could not parse {output_type} as JSON, skipping formatting")
                            
                    except Exception as e:
                        print(f"   ⚠️ Error formatting {output_type} file: {e}")
                else:
                    print(f"   ⚠️ {output_type} output file not found: {file_path}")
            
            # Clean up any temporary files
            self._cleanup_temp_files(logs_dir)
                    
        except Exception as e:
            print(f"⚠️ Warning: Could not format output files: {e}")
    
    def _cleanup_temp_files(self, logs_dir: Path):
        """Clean up any temporary files created during execution"""
        try:
            temp_files = list(logs_dir.glob("*.tmp"))
            for temp_file in temp_files:
                try:
                    temp_file.unlink()
                    print(f"   🗑️ Cleaned up temporary file: {temp_file.name}")
                except Exception as e:
                    print(f"   ⚠️ Could not remove temporary file {temp_file.name}: {e}")
        except Exception as e:
            print(f"   ⚠️ Error during temp file cleanup: {e}")

    def _discover_patient_file_paths(self, patient_name: str) -> Dict[str, str]:
        """Discover all available file paths for a patient."""
        # Get the correct workspace root for file paths
        workspace_root = Path(__file__).parent.parent.parent  # patient/integrations/ -> patient/ -> workspace_root
        patient_dir = workspace_root / "patient"
        
        # Discover all available paths
        paths = {}
        
        # Patient summary files
        summary_file = patient_dir / f"{patient_name.lower()}_biometric_summary.json"
        if summary_file.exists():
            paths['patient_summary_path'] = str(summary_file)
        
        # FHIR records - find the specific file matching the patient name
        fhir_dir = patient_dir / "generated_medical_records" / "fhir"
        if fhir_dir.exists():
            # Look for files that contain the patient name (case-insensitive)
            for fhir_file in fhir_dir.glob("*.json"):
                if patient_name.lower() in fhir_file.name.lower():
                    paths['fhir_records_path'] = str(fhir_file)
                    break
        
        # Pain diaries - find the specific file matching the patient name
        pain_diaries_dir = patient_dir / "generated_medical_records" / "pain_diaries"
        if pain_diaries_dir.exists():
            for pain_file in pain_diaries_dir.glob("*.json"):
                if patient_name.lower() in pain_file.name.lower():
                    paths['pain_diary_path'] = str(pain_file)
                    break
        
        # Weight data - find the specific file matching the patient name
        weight_data_dir = patient_dir / "biometric" / "weight"
        if weight_data_dir.exists():
            weight_file = weight_data_dir / f"{patient_name.lower()}.json"
            if weight_file.exists():
                paths['weight_data_path'] = str(weight_file)
        
        return paths

    def _process_temporal_data(self, patient_name: str) -> Dict[str, Any]:
        """Process temporal data (weight and pain diary) by converting offset_ms to actual timestamps."""
        from datetime import datetime, timedelta
        
        temporal_data = {
            'weight_data': [],
            'pain_diary_data': []
        }
        
        try:
            # Get the correct workspace root for file paths
            workspace_root = Path(__file__).parent.parent.parent  # patient/integrations/ -> patient/ -> workspace_root
            
            # Process weight data
            weight_file = workspace_root / "patient" / "biometric" / "weight" / f"{patient_name.lower()}.json"
            if weight_file.exists():
                with open(weight_file, 'r') as f:
                    weight_data = json.load(f)
                
                for entry in weight_data:
                    if isinstance(entry, dict) and 'offset_ms' in entry:
                        # Convert offset_ms (milliseconds BEFORE current time) to actual timestamp
                        current_time = datetime.now()
                        offset_seconds = entry['offset_ms'] / 1000
                        timestamp = current_time - timedelta(seconds=offset_seconds)
                        
                        processed_entry = entry.copy()
                        processed_entry['timestamp'] = timestamp.isoformat()
                        temporal_data['weight_data'].append(processed_entry)
            
            # Process pain diary data
            pain_diaries_dir = workspace_root / "patient" / "generated_medical_records" / "pain_diaries"
            if pain_diaries_dir.exists():
                for pain_file in pain_diaries_dir.glob("*.json"):
                    if patient_name.lower() in pain_file.name.lower():
                        with open(pain_file, 'r') as f:
                            pain_data = json.load(f)
                        
                        for entry in pain_data:
                            if isinstance(entry, dict) and 'offset_ms' in entry:
                                # Convert offset_ms (milliseconds BEFORE current time) to actual timestamp
                                current_time = datetime.now()
                                offset_seconds = entry['offset_ms'] / 1000
                                timestamp = current_time - timedelta(seconds=offset_seconds)
                                
                                processed_entry = entry.copy()
                                processed_entry['timestamp'] = timestamp.isoformat()
                                temporal_data['pain_diary_data'].append(processed_entry)
                        break
            
            # Temporal data processed successfully
            
        except Exception as e:
            print(f"   ⚠️ Warning: Could not process temporal data for {patient_name}: {e}")
        
        return temporal_data
