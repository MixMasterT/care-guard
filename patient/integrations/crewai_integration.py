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
            # Try to import the cardio monitor crew
            from cardio_monitor.src.cardio_monitor.crew import CardioMonitor
            self.crew_module = CardioMonitor
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

    def run_agentic_analysis(self, patient_name: str, run_id: Optional[str] = None) -> Dict[str, Any]:
        """Run CrewAI analysis for a patient."""
        if self.crew_module is None:
            return {
                "success": False,
                "error": "CrewAI crew module not available"
            }
        
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
            
            # Create consolidated execution log with correct naming - use proper case for consistency
            timestamp = datetime.now().strftime('%Y_%m_%d_%H_%M')
            # Ensure patient_name is properly formatted for file naming (first letter capitalized)
            formatted_patient_name = patient_name.title() if patient_name else "Unknown"
            execution_log_file = logs_dir / f"{timestamp}_{run_id}_{formatted_patient_name}_execution_log.json"
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
            add_event("analysis_started", f"Starting CrewAI analysis for {patient_name}")
            add_progress(10, "starting", "Analysis initialization")
            
            # Create crew instance
            crew = self.crew_module()
            
            # Get workspace root for file paths
            workspace_root = Path(__file__).parent.parent
            
            # Process temporal data to convert offset_ms to actual timestamps
            print(f"   🕒 Processing temporal data for {patient_name}...")
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
                'biometric_buffer_path': str(workspace_root / 'biometric' / 'buffer' / 'simulation_biometrics.json'),
                'pain_diary_path': file_paths.get('pain_diary_path', ''),
                'weight_data_path': str(workspace_root / 'patient' / 'biometric' / 'weight' / f'{patient_name.lower()}.json'),
                # Template variables for output_file interpolation - these MUST match the template variables in tasks.yaml
                'timestamp': timestamp,  # Format: YYYY_MM_DD_HH_MM
                'run_id': run_id,        # Should be a simple string
                'patient_name': formatted_patient_name,  # For file naming - use formatted name
                'processed_weight_data': temporal_data['weight_data'],
                'processed_pain_diary_data': temporal_data['pain_diary_data'],
                'patient_context': patient_context
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
            
            # Update progress to running
            add_progress(30, "running", "CrewAI execution starting")
            
            # Run the crew using the same pattern as main.py
            print(f"🤖 Creating CrewAI crew...")
            add_event("crew_creation", "Creating CrewAI crew")
            add_progress(40, "running", "CrewAI crew created")
            
            print(f"🚀 Starting CrewAI execution with inputs: {list(inputs.keys())}")
            add_event("crew_execution_started", "Starting CrewAI execution")
            add_progress(50, "running", "CrewAI execution started")
            
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
                    clean_text = re.sub(r'[^\x20-\x7E\n\r\t]', '', clean_text)
                    
                    # Also capture for logging
                    self.captured.append(clean_text)
                    
                    # Parse for important events in real-time
                    current_time = time.time()
                    if current_time - self.last_event_time > 1:
                        self.last_event_time = current_time
                        self._parse_for_events(clean_text)
                    
                    # Update progress more frequently
                    if current_time - self.last_progress_update > 0.5:
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
                        for agent_name in ["biometric", "triage", "log"]:
                            if agent_name in text_lower and agent_name not in self.agents_started:
                                self.agents_started.add(agent_name)
                                self.add_event_func(f"{agent_name}_agent_started", f"{agent_name.title()} agent started")
                                if len(self.agents_started) == 1:
                                    self.add_progress_func(60, "running", f"{agent_name.title()} agent started")
                                elif len(self.agents_started) == 2:
                                    self.add_progress_func(70, "running", f"{agent_name.title()} agent started")
                                elif len(self.agents_started) == 3:
                                    self.add_progress_func(80, "running", f"{agent_name.title()} agent started")
                    
                    # Detect task completion events
                    if "task" in text_lower and "completed" in text_lower:
                        for task_name in ["analyze", "create", "review"]:
                            if task_name in text_lower and task_name not in self.tasks_completed:
                                self.tasks_completed.add(task_name)
                                self.add_event_func(f"{task_name}_task_completed", f"{task_name.title()} task completed")
                                if len(self.tasks_completed) == 1:
                                    self.add_progress_func(85, "running", f"{task_name.title()} task completed")
                                elif len(self.tasks_completed) == 2:
                                    self.add_progress_func(90, "running", f"{task_name.title()} task completed")
                                elif len(self.tasks_completed) == 3:
                                    self.add_progress_func(95, "running", f"{task_name.title()} task completed")
                
                def _update_progress(self, text):
                    """Update progress based on captured text"""
                    text_lower = text.lower()
                    
                    # Detect completion indicators
                    if "analysis complete" in text_lower or "crew execution finished" in text_lower:
                        self.current_progress = 100
                        self.add_progress_func(100, "completed", "Analysis completed successfully")
                    
                    # Detect error indicators
                    elif "error" in text_lower or "failed" in text_lower:
                        self.current_progress = 0
                        self.add_progress_func(0, "failed", "Analysis failed")
                    
                    # Gradual progress updates based on time
                    elif time.time() - self.last_progress_update > 10:
                        if self.current_progress < 90:
                            self.current_progress += 1
                            self.add_progress_func(self.current_progress, "running", "Analysis in progress")
            
            # Capture stdout during crew execution
            original_stdout = sys.stdout
            tee_output = TeeOutput(original_stdout, execution_log, add_event, add_progress)
            sys.stdout = tee_output
            
            try:
                # Run the crew with proper inputs
                # Create the crew instance with file paths
                crew_instance = crew.crew(
                    biometric_buffer_path=inputs['biometric_buffer_path'],
                    pain_diary_path=inputs['pain_diary_path'],
                    weight_data_path=inputs['weight_data_path']
                )
                
                # Run the crew with the inputs (this includes template variables and other data)
                result = crew_instance.kickoff(inputs=inputs)
                
                # Restore stdout
                sys.stdout = original_stdout
                
                # Final progress update
                add_progress(100, "completed", "Analysis completed successfully")
                add_event("analysis_completed", "Analysis completed successfully", {"result": str(result)})
                
                # Post-process output files to ensure proper JSON formatting
                self._format_output_files(patient_name, timestamp, run_id)
                
                print(f"✅ CrewAI analysis completed for {patient_name}")
                print(f"📊 Result: {result}")
                
                return {
                    "success": True,
                    "result": result,
                    "run_id": run_id,
                    "patient_name": patient_name,
                    "framework": "crewai",
                    "execution_log": str(execution_log_file)
                }
                
            except Exception as e:
                # Restore stdout
                sys.stdout = original_stdout
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
                        json.dump(execution_log, f, indent=2, default=str)
                    print(f"📊 Execution log updated: failed - 0%")
                except Exception as e2:
                    print(f"⚠️ Warning: Could not update execution log: {e2}")
                
                return {
                    "success": False,
                    "error": f"Error running agentic analysis: {str(e)}",
                    "run_id": run_id,
                    "patient_name": patient_name,
                    "framework": "crewai",
                    "execution_log": str(execution_log_file) if 'execution_log_file' in locals() else None
                }
                
        except Exception as e:
            print(f"❌ Error in CrewAI analysis: {e}")
            import traceback
            traceback.print_exc()
            
            return {
                "success": False,
                "error": f"Error running agentic analysis: {str(e)}",
                "run_id": run_id,
                "patient_name": patient_name,
                "framework": "crewai"
            }
    
    def _format_output_files(self, patient_name: str, timestamp: str, run_id: str):
        """
        Post-process output files to ensure proper JSON formatting.
        This method reads the raw output files created by CrewAI and reformats them with proper indentation.
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
                file_path = logs_dir / f"{timestamp}_{run_id}_{patient_name}_{output_type}.json"
                
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
                                json.dump(data, f, indent=2, default=str)
                            print(f"   ✅ Formatted {output_type} output file")
                        except json.JSONDecodeError:
                            print(f"   ⚠️ Could not parse {output_type} as JSON, skipping formatting")
                            
                    except Exception as e:
                        print(f"   ⚠️ Error formatting {output_type} file: {e}")
                else:
                    print(f"   ⚠️ {output_type} output file not found: {file_path}")
                    
        except Exception as e:
            print(f"⚠️ Warning: Could not format output files: {e}")
