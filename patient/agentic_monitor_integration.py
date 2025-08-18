"""
Agentic Monitor Integration

Provides integration between the Streamlit patient monitor and CrewAI agentic solutions.
"""

import json
import tempfile
from pathlib import Path
import sys
from typing import Dict, Any, Optional
from datetime import datetime
import time # Added for time.time()

# Ensure repository root is on sys.path for root-level packages
ROOT_DIR = Path(__file__).parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

try:
    # When imported as part of a package
    from .agentic_data_loader import AgenticPatientDataLoader
except ImportError:
    # When run directly
    from agentic_data_loader import AgenticPatientDataLoader
from agentic_types.models import (
    Finding,
    Recommendation,
    DecisionPayload,
    ConfidenceLevel,
    ConfidenceLevelEvidence,
    AgenticFinalOutput,
    PatientIdentity,
    ExecutionMetrics,
    Artifacts,
)

class AgenticMonitorIntegration:
    """Handles integration between the patient monitor and CrewAI agents."""
    
    def __init__(self, crew_dir: str = None):
        """
        Initialize the integration.
        
        Args:
            crew_dir: Path to the CrewAI crew directory (defaults to crew/cardio_monitor)
        """
        if crew_dir is None:
            crew_dir = Path(__file__).parent.parent / "crew" / "cardio_monitor"
        self.crew_dir = Path(crew_dir)
    
    def _discover_patient_file_paths(self, patient_name: str) -> Dict[str, str]:
        """
        Discover all available file paths for a patient.
        This method centralizes path discovery so any framework can use the same paths.
        
        Args:
            patient_name: Name of the patient (e.g., 'allen', 'mark', 'zach')
            
        Returns:
            Dictionary mapping path keys to absolute file paths
        """
        # Get the patient directory (where this file is located)
        patient_dir = Path(__file__).parent
        
        # Discover all available paths
        paths = {}
        
        # Patient summary files
        summary_file = patient_dir / f"{patient_name.lower()}_biometric_summary.json"
        if summary_file.exists():
            paths['patient_summary_path'] = str(summary_file)
        
        # Pain journal files
        pain_journal_file = patient_dir / "pain_journals" / f"{patient_name.lower()}.json"
        if pain_journal_file.exists():
            paths['pain_journal_path'] = str(pain_journal_file)
        
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
            # Look for files that contain the patient name (case-insensitive)
            for pain_file in pain_diaries_dir.glob("*.json"):
                if patient_name.lower() in pain_file.name.lower():
                    paths['pain_diaries_path'] = str(pain_file)  # Changed from pain_diaries_dir
                    break
        
        # Weight data - find the specific file matching the patient name
        weight_data_dir = patient_dir / "biometric" / "weight"
        if weight_data_dir.exists():
            weight_file = weight_data_dir / f"{patient_name.lower()}.json"
            if weight_file.exists():
                paths['weight_data_path'] = str(weight_file)  # Changed from weight_data_dir
        
        return paths

    def get_framework_data_paths(self, patient_name: str) -> Dict[str, str]:
        """
        Get all available data paths for a patient.
        This method can be called by any framework to get the same path information.
        
        Args:
            patient_name: Name of the patient (e.g., 'allen', 'mark', 'zach')
            
        Returns:
            Dictionary mapping path keys to absolute file paths
        """
        return self._discover_patient_file_paths(patient_name)

    def run_agentic_analysis(self, patient_name: str, run_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Public method to run agentic analysis for a specific patient.
        
        Args:
            patient_name: Name of the patient to analyze
            run_id: Optional run ID (will generate one if not provided)
            
        Returns:
            Dictionary containing the analysis results
        """
        try:
            # Generate run_id if not provided
            if not run_id:
                run_id = f"{int(time.time())}"  # Just use timestamp, no date formatting
            
            print(f"🚀 Starting agentic analysis for {patient_name} with run_id: {run_id}")
            
            # Create logs directory
            logs_dir = Path(__file__).parent / "agentic_monitor_logs"
            logs_dir.mkdir(exist_ok=True)
            
            # Create consolidated execution log with correct naming: {timestamp}_{run_id}_{patient_name}_execution_log.json
            # Use a single timestamp for consistency across all file naming
            timestamp = datetime.now().strftime('%Y_%m_%d_%H_%M')
            execution_log_file = logs_dir / f"{timestamp}_{run_id}_{patient_name.lower()}_execution_log.json"
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
                    event["data"] = data
                execution_log["events"].append(event)
                
                # Write updated log to file
                try:
                    with open(execution_log_file, 'w') as f:
                        json.dump(execution_log, f, indent=2, default=str)
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
                
                # Write updated log to file
                try:
                    with open(execution_log_file, 'w') as f:
                        json.dump(execution_log, f, indent=2, default=str)
                except Exception as e:
                    print(f"⚠️ Warning: Could not write execution log: {e}")
            
            # Add initial event
            add_event("analysis_started", f"Starting agentic analysis for {patient_name}")
            add_progress(10, "starting", "Analysis initialization")
            
            # Note: We no longer write individual progress_signal files since we have the consolidated execution_log.json
            # The execution_log.json file provides all the progress and status information needed
            
            # Import the crew module
            import sys
            sys.path.insert(0, str(self.crew_dir / "src"))
            
            from cardio_monitor.crew import CardioMonitor
            
            # Get workspace root for file paths
            workspace_root = Path(__file__).parent.parent
            
            # Build inputs using the same pattern as main.py
            inputs = {
                'topic': 'Cardio Monitoring Analysis',
                'current_year': str(datetime.now().year),
                'patient_name': patient_name,
                'biometric_buffer_path': str(workspace_root / 'patient' / 'biometric' / 'buffer' / 'simulation_biometrics.json'),
                'patient_summary_path': str(workspace_root / f'patient/{patient_name.lower()}_biometric_summary.json'),
                'pain_journal_path': str(workspace_root / 'patient' / 'pain_journals' / f'{patient_name.lower()}.json'),
                'weight_data_path': str(workspace_root / 'patient' / 'biometric' / 'weight' / f'{patient_name.lower()}.json'),
                # Add template variables for output_file interpolation
                'timestamp': timestamp,  # Use the same timestamp variable
                'run_id': run_id,
            }
            
            add_event("inputs_configured", "Analysis inputs configured", {
                "file_paths": {k: v for k, v in inputs.items() if 'path' in k},
                "template_variables": {
                    "timestamp": inputs['timestamp'],
                    "run_id": inputs['run_id'],
                    "patient_name": inputs['patient_name']
                }
            })
            
            print(f"📁 File paths configured:")
            for key, path in inputs.items():
                if 'path' in key:
                    exists = "✅" if Path(path).exists() else "❌"
                    print(f"   {exists} {key}: {path}")
            
            print(f"🔧 Template variables for output_file interpolation:")
            print(f"   timestamp: {inputs['timestamp']}")
            print(f"   run_id: {inputs['run_id']}")
            print(f"   patient_name: {inputs['patient_name']}")
            
            # Update progress to running
            add_progress(30, "running", "CrewAI execution starting")
            
            # Note: The execution log is now updated via add_progress which preserves structure
            
            # Run the crew using the same pattern as main.py
            print(f"🤖 Creating CrewAI crew...")
            add_event("crew_creation", "Creating CrewAI crew")
            add_progress(40, "running", "CrewAI crew created")
            
            crew = CardioMonitor()
            print(f"🚀 Starting CrewAI execution with inputs: {list(inputs.keys())}")
            add_event("crew_execution_started", "Starting CrewAI execution")
            add_progress(50, "running", "CrewAI execution started")
            
            # Note: Progress will now be updated in real-time by TeeOutput as agents work
            
            # Capture stdout to see CrewAI output in real-time
            import io
            import contextlib
            import re
            
            # Create a custom stdout that captures and parses events
            class TeeOutput:
                def __init__(self, original_stdout, execution_log, add_event_func, add_progress_func):
                    self.original_stdout = original_stdout
                    self.captured = []
                    self.execution_log = execution_log
                    self.add_event_func = add_event_func
                    self.add_progress_func = add_progress_func
                    self.last_event_time = time.time()
                    self.last_progress_update = time.time()
                    self.agents_started = set()
                    self.tasks_completed = set()
                    self.current_progress = 30  # Start at 30% (crew creation)
                
                def write(self, text):
                    # Write to original stdout (terminal)
                    self.original_stdout.write(text)
                    self.original_stdout.flush()
                    
                    # Strip ANSI color codes and other formatting
                    clean_text = re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', text)
                    clean_text = re.sub(r'[^\x20-\x7E\n\r\t]', '', clean_text)  # Keep only printable ASCII
                    
                    # Also capture for logging
                    self.captured.append(clean_text)
                    
                    # Parse for important events in real-time
                    current_time = time.time()
                    if current_time - self.last_event_time > 1:  # Check every second
                        self.last_event_time = current_time
                        self._parse_for_events(clean_text)
                    
                    # Update progress more frequently
                    if current_time - self.last_progress_update > 0.5:  # Check every 0.5 seconds
                        self.last_progress_update = current_time
                        self._update_progress(clean_text)
                
                def flush(self):
                    self.original_stdout.flush()
                
                def get_captured(self):
                    return ''.join(self.captured)
                
                def _parse_for_events(self, text):
                    """Parse captured text for important events"""
                    text_lower = text.lower()
                    
                    # Detect agent start events
                    if "agent" in text_lower and "started" in text_lower:
                        # Look for specific agent names
                        for agent_name in ["biometric", "triage", "log"]:
                            if agent_name in text_lower and agent_name not in self.agents_started:
                                self.agents_started.add(agent_name)
                                self.add_event_func(f"{agent_name}_agent_started", f"{agent_name.title()} agent started")
                                # Update progress when agent starts
                                if len(self.agents_started) == 1:
                                    self.add_progress_func(60, "running", f"{agent_name.title()} agent started")
                                elif len(self.agents_started) == 2:
                                    self.add_progress_func(70, "running", f"{agent_name.title()} agent started")
                                elif len(self.agents_started) == 3:
                                    self.add_progress_func(80, "running", f"{agent_name.title()} agent started")
                    
                    # Detect task completion events
                    elif "task" in text_lower and "completed" in text_lower:
                        # Look for specific task types
                        for task_type in ["biometric", "triage", "medical"]:
                            if task_type in text_lower and task_type not in self.tasks_completed:
                                self.tasks_completed.add(task_type)
                                self.add_event_func(f"{task_type}_task_completed", f"{task_type.title()} task completed")
                                # Update progress when task completes
                                if len(self.tasks_completed) == 1:
                                    self.add_progress_func(75, "running", f"{task_type.title()} task completed")
                                elif len(self.tasks_completed) == 2:
                                    self.add_progress_func(85, "running", f"{task_type.title()} task completed")
                                elif len(self.tasks_completed) == 3:
                                    self.add_progress_func(95, "running", f"{task_type.title()} task completed")
                    
                    # Detect crew completion
                    elif "crew" in text_lower and "completed" in text_lower:
                        self.add_event_func("crew_completed", "CrewAI execution completed")
                    
                    # Detect errors
                    elif "error" in text_lower or "failed" in text_lower:
                        self.add_event_func("error_detected", "Error or failure detected", {"text": text[:200]})
                
                def _update_progress(self, text):
                    """Update progress based on current execution state"""
                    # If we have agents working, gradually increase progress
                    if self.agents_started and self.current_progress < 90:
                        # Gradual progress increase while agents are working
                        progress_increment = min(2, (90 - self.current_progress) / 10)
                        self.current_progress += progress_increment
                        self.add_progress_func(int(self.current_progress), "running", "Agents working...")
            
            # Replace stdout temporarily
            original_stdout = sys.stdout
            tee_output = TeeOutput(original_stdout, execution_log, add_event, add_progress)
            sys.stdout = tee_output
            
            try:
                print(f"🎯 Executing CrewAI crew...")
                crew_output = crew.crew(
                    biometric_buffer_path=inputs['biometric_buffer_path'],
                    pain_journal_path=inputs['pain_journal_path'],
                    weight_data_path=inputs['weight_data_path']
                ).kickoff(inputs=inputs)
                
                add_event("crew_execution_completed", "CrewAI execution completed successfully")
                add_progress(90, "running", "CrewAI execution completed, processing outputs")
                
                print(f"✅ CrewAI execution completed successfully!")
                print(f"📊 Output type: {type(crew_output)}")
                print(f"📊 Output length: {len(str(crew_output))} characters")
                
                # Update progress to completed
                add_progress(100, "completed", "Analysis completed successfully")
                
                try:
                    # Update the execution log instead of overwriting it
                    execution_log["status"] = "completed"
                    execution_log["progress_percent"] = 100
                    execution_log["completed_at"] = datetime.now().isoformat()
                    
                    # Add completion event
                    add_event("analysis_completed", "Analysis completed successfully")
                    
                    # Write the updated execution log (preserving pretty-print)
                    with open(execution_log_file, 'w') as f:
                        json.dump(execution_log, f, indent=2, default=str)
                    print(f"📊 Execution log updated: completed - 100%")
                except Exception as e:
                    print(f"⚠️ Warning: Could not update execution log: {e}")
                
                # Pretty-print the output files AFTER all updates are complete
                try:
                    print(f"🔧 Pretty-printing output files...")
                    for file_pattern in [
                        f"*_{run_id}_*_biometric_analysis.json",
                        f"*_{run_id}_*_triage_decision.json", 
                        f"*_{run_id}_*_medical_log.json"
                    ]:
                        output_files = list(logs_dir.glob(file_pattern))
                        for output_file in output_files:
                            try:
                                # Read the file
                                with open(output_file, 'r') as f:
                                    content = json.load(f)
                                
                                # Write it back with pretty-printing
                                with open(output_file, 'w') as f:
                                    json.dump(content, f, indent=2, default=str)
                                
                                print(f"✅ Pretty-printed: {output_file.name}")
                            except Exception as e:
                                print(f"⚠️ Warning: Could not pretty-print {output_file.name}: {e}")
                except Exception as e:
                    print(f"⚠️ Warning: Could not pretty-print output files: {e}")
                
                # Save captured output to a log file (keep for backward compatibility)
                try:
                    output_log_file = logs_dir / f"crew_output_{run_id}.log"
                    with open(output_log_file, 'w') as f:
                        f.write(tee_output.get_captured())
                    print(f"📝 CrewAI output saved to: {output_log_file}")
                except Exception as e:
                    print(f"⚠️ Warning: Could not save output log: {e}")
                
                # CrewAI will handle writing the 3 JSON output files via output_file parameters
                return {
                    "success": True,
                    "run_id": run_id,
                    "patient_name": patient_name,
                    "message": "Analysis completed successfully",
                    "output_log": str(output_log_file) if 'output_log_file' in locals() else None,
                    "execution_log": str(execution_log_file)
                }
                
            finally:
                # Restore original stdout
                sys.stdout = original_stdout
            
        except Exception as e:
            print(f"❌ ERROR in run_agentic_analysis: {e}")
            import traceback
            traceback.print_exc()
            
            add_event("analysis_failed", f"Analysis failed: {str(e)}", {"error": str(e)})
            add_progress(0, "failed", f"Analysis failed: {str(e)}")
            
            # Update progress to failed
            try:
                # Update the execution log instead of overwriting it
                execution_log["status"] = "failed"
                execution_log["progress_percent"] = 0
                execution_log["error"] = str(e)
                execution_log["failed_at"] = datetime.now().isoformat()
                
                # Write the updated execution log (preserving pretty-print)
                with open(execution_log_file, 'w') as f:
                    json.dump(execution_log, f, indent=2, default=str)
                print(f"📊 Execution log updated: failed - 0%")
            except Exception as e2:
                print(f"⚠️ Warning: Could not update execution log: {e2}")
            
            return {
                "success": False,
                "error": f"Error running agentic analysis: {str(e)}",
                "run_id": run_id,
                "patient_name": patient_name,
                "execution_log": str(execution_log_file) if 'execution_log_file' in locals() else None
            }

    def get_latest_logs(self, patient_name: str, limit: int = 5) -> list:
        """
        Get the latest log entries for a patient.
        
        Args:
            patient_name: Name of the patient
            limit: Maximum number of logs to return
            
        Returns:
            List of recent log entries
        """
        try:
            data_loader = AgenticPatientDataLoader(patient_name)
            return data_loader.get_latest_logs(limit)
        except Exception as e:
            print(f"Error loading logs: {e}")
            return []
    
    def test_crew_availability(self) -> Dict[str, Any]:
        """
        Test if the CrewAI crew is available and properly configured.
        
        Returns:
            Dictionary with test results
        """
        try:
            # Check if crew directory exists
            if not self.crew_dir.exists():
                return {
                    "available": False,
                    "error": f"Crew directory not found: {self.crew_dir}"
                }
            
            # Check if config files exist
            config_dir = self.crew_dir / "src" / "cardio_monitor" / "config"
            required_files = ["agents.yaml", "tasks.yaml"]
            
            missing_files = []
            for file_name in required_files:
                if not (config_dir / file_name).exists():
                    missing_files.append(file_name)
            
            if missing_files:
                return {
                    "available": False,
                    "error": f"Missing config files: {missing_files}"
                }
            
            # Check if crew module can be imported
            try:
                import sys
                sys.path.insert(0, str(self.crew_dir / "src"))
                from cardio_monitor.crew import CardioMonitor
                crew = CardioMonitor()
                return {
                    "available": True,
                    "crew_dir": str(self.crew_dir),
                    "config_dir": str(config_dir),
                    "crew_class": "CardioMonitor"
                }
            except ImportError as e:
                return {
                    "available": False,
                    "error": f"Crew module import failed: {str(e)}"
                }
            
        except Exception as e:
            return {
                "available": False,
                "error": f"Error testing crew availability: {str(e)}"
            } 