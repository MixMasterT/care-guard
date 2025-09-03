"""
LangGraph integration for agentic monitoring.
Handles LangGraph-specific setup and execution.
"""

import json
import tempfile
import sys
import time
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

from .base_integration import BaseIntegration


class LangGraphIntegration(BaseIntegration):
    """LangGraph-specific integration for agentic monitoring."""
    
    def __init__(self):
        super().__init__()
        self.framework_name = "LangGraph"
        self.workflow_module = None
        self._load_workflow_module()
    
    def _load_workflow_module(self):
        """Load the LangGraph workflow module."""
        try:
            # Import the patient monitoring workflow
            from langgraph_agents.workflows.patient_monitoring_workflow import run_patient_monitoring
            self.workflow_module = run_patient_monitoring
        except ImportError as e:
            print(f"⚠️ Warning: Could not import LangGraph workflow module: {e}")
            self.workflow_module = None
    
    def test_availability(self) -> Dict[str, Any]:
        """Test if LangGraph is available and ready to run."""
        if self.workflow_module is None:
            return {
                "available": False,
                "error": "LangGraph workflow module not available. Please ensure the langgraph_agents directory is properly set up."
            }
        
        try:
            # Try to import required dependencies
            from langgraph.graph import StateGraph
            from langchain_openai import ChatOpenAI
            return {
                "available": True,
                "message": "LangGraph is available and ready to run"
            }
        except Exception as e:
            return {
                "available": False,
                "error": f"Error testing LangGraph availability: {str(e)}"
            }

    def run_agentic_analysis(self, patient_name: str, run_id: Optional[str] = None, timestamp: Optional[str] = None) -> Dict[str, Any]:
        """Run LangGraph analysis for a patient."""
        if self.workflow_module is None:
            return {
                "success": False,
                "error": "LangGraph workflow module not available"
            }
        
        try:
            # Generate run_id if not provided
            if not run_id:
                run_id = f"run_{int(time.time())}"
            else:
                # Ensure run_id is clean for file naming
                run_id = str(run_id).replace(' ', '_').replace('/', '_').replace('\\', '_')
            
            print(f"🚀 Starting LangGraph analysis for {patient_name} with run_id: {run_id}")
            
            # Create logs directory
            logs_dir = Path(__file__).parent.parent / "agentic_monitor_logs"
            logs_dir.mkdir(exist_ok=True)
            
            # Create execution log
            if timestamp:
                # Use provided timestamp
                log_timestamp = timestamp
            else:
                # Generate new timestamp
                log_timestamp = datetime.now().strftime('%Y_%m_%d_%H_%M')
            
            formatted_patient_name = patient_name.title() if patient_name else "Unknown"
            execution_log_file = logs_dir / f"{log_timestamp}_{formatted_patient_name}_execution_log.json"
            
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
            add_event("analysis_started", f"Starting LangGraph analysis for {patient_name}")
            add_progress(10, "starting", "Analysis initialization")
            
            # Run the workflow
            add_event("workflow_started", "LangGraph workflow started")
            add_progress(20, "running", "Workflow execution started")
            
            result = self.workflow_module(patient_name, run_id, timestamp=log_timestamp)
            
            # Update progress based on result
            if result.get("success"):
                add_progress(100, "completed", "Analysis completed successfully")
                add_event("analysis_completed", "Analysis completed successfully", {"result": str(result)})
                
                print(f"✅ LangGraph analysis completed for {patient_name}")
                print(f"📊 Result: {result}")
                
                return {
                    "success": True,
                    "result": result,
                    "run_id": run_id,
                    "patient_name": patient_name,
                    "framework": "langgraph",
                    "execution_log": str(execution_log_file)
                }
            else:
                add_event("analysis_failed", f"Analysis failed: {result.get('error', 'Unknown error')}")
                add_progress(0, "failed", f"Analysis failed: {result.get('error', 'Unknown error')}")
                
                print(f"❌ LangGraph analysis failed: {result.get('error', 'Unknown error')}")
                
                return {
                    "success": False,
                    "error": result.get('error', 'Unknown error'),
                    "run_id": run_id,
                    "patient_name": patient_name,
                    "framework": "langgraph",
                    "execution_log": str(execution_log_file)
                }
                
        except Exception as e:
            print(f"❌ Error in LangGraph analysis: {e}")
            import traceback
            traceback.print_exc()
            
            return {
                "success": False,
                "error": f"Error running agentic analysis: {str(e)}",
                "run_id": run_id,
                "patient_name": patient_name,
                "framework": "langgraph"
            }