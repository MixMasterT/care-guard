#!/usr/bin/env python3
"""
Agentic Monitor App - Separate Streamlit app for agentic analysis monitoring
Runs on port 8502 and displays real-time agent progress and results
"""

import streamlit as st
import json
import time
import threading
from pathlib import Path
from datetime import datetime

def show_results(run_id, patient_name, timestamp, output_container):
    """Display the analysis results in a structured format"""
    try:
        # Look for the medical log file using the standard naming pattern
        logs_dir = Path(__file__).parent / "agentic_monitor_logs"
        
        # Standard naming pattern: {timestamp}_{patient_name}_medical_log.json
        # Use title case for patient name to match what the integration generates
        formatted_patient_name = patient_name.title() if patient_name else "Unknown"
        medical_log_file = logs_dir / f"{timestamp}_{formatted_patient_name}_medical_log.json"
        
        if not medical_log_file.exists():
            output_container.error(f"❌ Medical log file not found: {medical_log_file.name}")
            return
        
        output_container.info(f"🔍 Reading results from: {medical_log_file.name}")
        
        with open(medical_log_file, 'r') as f:
            results = json.load(f)
        
        # Debug: show what fields are available
        output_container.info(f"🔍 Available fields in results: {list(results.keys())}")
        
        # Test: show the actual summary and followups if they exist
        print(f"The medical log contains: {list(results.keys())}")
        if "summary" in results and results["summary"]:
            output_container.info(f"🔍 Summary found: {results['summary'][:100]}...")
        if "triage_decision" in results and results["triage_decision"]:
            triage = results["triage_decision"]
            if "followups" in triage and triage["followups"]:
                followups = triage['followups']
                if isinstance(followups, list):
                    output_container.info(f"🔍 Followups found: {len(followups)} items")
                    for i, f in enumerate(followups[:2]):  # Show first 2
                        if f:  # Check if followup is not None/empty
                            output_container.info(f"   {i+1}. {f[:50]}...")
                else:
                    output_container.info(f"🔍 Followups found but not in list format: {type(followups)}")
        
        # Display structured results
        output_container.subheader("📋 Analysis Results")
        
        # Show main summary if available
        if "summary" in results and results["summary"]:
            output_container.write("**Summary:**")
            output_container.write(results["summary"])
            output_container.markdown("---")
        else:
            output_container.info("⚠️ No summary field found in results")
        
        # Show triage decision action
        if "triage_decision" in results and results["triage_decision"]:
            triage = results["triage_decision"]
            output_container.write("**Action:**")
            output_container.write(triage.get('action', 'No action specified'))
            output_container.markdown("---")
            
            # Show followups if available
            if "followups" in triage and triage["followups"]:
                output_container.write("**Follow-ups:**")
                for i, followup in enumerate(triage["followups"], 1):
                    if followup:  # Check if followup is not None/empty
                        output_container.write(f"{i}. {followup}")
            else:
                output_container.write("**Follow-ups:** None specified")
            
            # Show priority if available
            if "priority" in triage and triage["priority"]:
                output_container.markdown("---")
                priority = triage['priority']
                if isinstance(priority, str):
                    output_container.write(f"**Priority:** {priority.title()}")
                else:
                    output_container.write(f"**Priority:** {priority}")
            
            # Show rationale if available
            if "rationale" in triage and triage["rationale"]:
                output_container.markdown("---")
                output_container.write("**Rationale:**")
                output_container.write(triage["rationale"])
        else:
            output_container.info("⚠️ No triage_decision field found in results")
        
        # Show findings if available
        if "findings" in results and results["findings"]:
            output_container.markdown("---")
            output_container.write("**Key Findings:**")
            for i, finding in enumerate(results["findings"], 1):
                if finding:  # Check if finding is not None
                    with output_container.expander(f"Finding {i}: {finding.get('title', 'Untitled')}"):
                        if finding.get('summary'):
                            output_container.write(f"**Summary:** {finding['summary']}")
                        if finding.get('risk_level'):
                            risk_level = finding['risk_level']
                            if isinstance(risk_level, str):
                                output_container.write(f"**Risk Level:** {risk_level.title()}")
                            else:
                                output_container.write(f"**Risk Level:** {risk_level}")
                        if finding.get('confidence_level'):
                            confidence_level = finding['confidence_level']
                            if isinstance(confidence_level, str):
                                output_container.write(f"**Confidence:** {confidence_level.title()}")
                            else:
                                output_container.write(f"**Confidence:** {confidence_level}")
        else:
            output_container.info("⚠️ No findings field found in results")
        
        # Show recommendations if available
        if "recommendations" in results and results["recommendations"]:
            output_container.markdown("---")
            output_container.write("**Recommendations:**")
            for i, rec in enumerate(results["recommendations"], 1):
                if rec:  # Check if recommendation is not None
                    with output_container.expander(f"Recommendation {i}"):
                        if rec.get('text'):
                            output_container.write(f"**Action:** {rec['text']}")
                        if rec.get('priority'):
                            priority = rec['priority']
                            if isinstance(priority, str):
                                output_container.write(f"**Priority:** {priority.title()}")
                            else:
                                output_container.write(f"**Priority:** {priority}")
                        if rec.get('rationale'):
                            output_container.write(f"**Rationale:** {rec['rationale']}")
        
        # Show Full JSON button
        output_container.markdown("---")
        if output_container.button("Show Full JSON", type="secondary"):
            output_container.json(results)
            
    except Exception as e:
        output_container.error(f"Error displaying results: {e}")
        import traceback
        output_container.error(f"Traceback: {traceback.format_exc()}")

def update_progress_from_execution_log(run_id: str, timestamp: str, patient_name: str):
    """
    Update progress information from execution log and refresh UI.
    This function should be called regularly to keep the UI updated.
    """
    if parse_execution_log(run_id, timestamp, patient_name):
        # Force a rerun to update the UI with new session state values
        st.rerun()


def parse_execution_log(run_id: str, timestamp: str, patient_name: str) -> bool:
    """
    Parse the execution log JSON file and update session state with progress information.
    
    Args:
        run_id: The run ID to look for in execution log files
        timestamp: The formatted timestamp (YYYY_MM_DD_HH_MM)
        patient_name: The patient name
        
    Returns:
        True if execution log was found and parsed, False otherwise
    """
    try:
        logs_dir = Path(__file__).parent / "agentic_monitor_logs"
        
        # Standard naming pattern: {timestamp}_{patient_name}_execution_log.json
        # Use title case for patient name to match what the integration generates
        formatted_patient_name = patient_name.title() if patient_name else "Unknown"
        execution_log_file = logs_dir / f"{timestamp}_{formatted_patient_name}_execution_log.json"
        print(f"!!! execution_log_file path: {execution_log_file}")
        
        if execution_log_file.exists():
            print(f"📋 Found execution log: {execution_log_file.name}")
            
            with open(execution_log_file, 'r') as f:
                log_data = json.load(f)
            
            # Extract progress information from the last item in the progress array
            if "progress" in log_data and log_data["progress"]:
                progress_array = log_data["progress"]
                latest_progress = progress_array[-1]  # Last element in array
                
                # Update session state with the parsed values
                st.session_state.percent = latest_progress.get("percent", 0)
                st.session_state.status = latest_progress.get("status", "unknown")
                st.session_state.status_message = latest_progress.get("message", "no status message found")
                
                return True
        
        # If no execution log found, try to determine progress from CrewAI output files
        print(f"🔍 No execution log found, checking CrewAI output files for progress...")
        
        # Look for CrewAI output files using standard naming pattern
        crewai_files = []
        
        # Check for each output file type - use title case for patient name
        file_types = ["biometric_analysis", "triage_decision", "medical_log"]
        for file_type in file_types:
            file_path = logs_dir / f"{timestamp}_{formatted_patient_name}_{file_type}.json"
            if file_path.exists():
                crewai_files.append((file_type, file_path))
        
        # If we found CrewAI files, estimate progress based on which files exist
        if crewai_files:
            print(f"🔍 Found {len(crewai_files)} CrewAI output files")
            
            # Estimate progress based on which files exist
            if len(crewai_files) == 1:
                st.session_state.percent = 33
                st.session_state.status = "in_progress"
                st.session_state.status_message = "Biometric analysis completed"
            elif len(crewai_files) == 2:
                st.session_state.percent = 66
                st.session_state.status = "in_progress"
                st.session_state.status_message = "Triage decision completed"
            elif len(crewai_files) == 3:
                st.session_state.percent = 100
                st.session_state.status = "completed"
                st.session_state.status_message = "All CrewAI tasks completed"
            
            return True
        
        # If no files found at all, assume analysis hasn't started
        print(f"🔍 No CrewAI output files found, analysis may not have started yet")
        st.session_state.percent = 0
        st.session_state.status = "not_started"
        st.session_state.status_message = "Waiting for analysis to start..."
        
        return False
            
    except Exception as e:
        print(f"❌ Error parsing execution log: {e}")
        return False
            
def start_analysis(run_id, patient_name, framework, timestamp):
    """Start the agentic analysis in a background thread"""
    try:
        # Import the integration module
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent))
        
        try:
            # Try package import first
            from patient.agentic_monitor_integration import AgenticMonitorIntegration
        except ImportError:
            try:
                # Fallback to direct import
                from agentic_monitor_integration import AgenticMonitorIntegration
            except ImportError as e:
                print(f"❌ Failed to import AgenticMonitorIntegration: {e}")
                return False
        
        # Initialize integration and start analysis
        integration = AgenticMonitorIntegration()
        print(f"🚀 Starting {framework} analysis for {patient_name} with run_id: {run_id}")
        
        # Test crew availability first
        availability = integration.test_crew_availability()
        
        if not availability.get("available"):
            print(f"❌ Crew not available: {availability.get('error', 'Unknown error')}")
            return False
        
        # Start the analysis with framework parameter
        results = integration.run_agentic_analysis(patient_name, run_id=run_id, framework=framework, timestamp=timestamp)
        print(f"📊 Analysis results: {results}")
        
        if results.get("success"):
            print(f"✅ Analysis started successfully for {patient_name} using {framework}!")
            return True
        else:
            print(f"❌ Analysis failed to start: {results.get('error', 'Unknown error')}")
            return False
        
    except Exception as e:
        print(f"❌ Error starting analysis: {e}")
        import traceback
        traceback.print_exc()
        return False



def main():
    st.set_page_config(
        page_title="Agentic Monitor",
        page_icon="🏥",
        layout="wide"
    )
    
    st.title("🏥 Agentic Patient Monitor")
    
    # Get parameters from query parameters
    run_id = st.query_params.get("run_id", None)
    patient_name = st.query_params.get("patient", None)
    framework = st.query_params.get("framework", "crewai")  # Default to crewai if not specified
    
    # Initialize session state variables if they don't exist
    if 'percent' not in st.session_state:
        st.session_state.percent = 0
    if 'status' not in st.session_state:
        st.session_state.status = "not_started"
    if 'status_message' not in st.session_state:
        st.session_state.status_message = ""
    
    # If no run_id provided, show error
    if not run_id:
        st.error("❌ No run ID specified. Please launch from the main monitor using 'Run Analysis' button.")
        return
    
    # Extract patient name and timestamp from run_id if not provided
    if not patient_name:
        try:
            parts = run_id.split('_')
            if len(parts) >= 2:
                patient_name = parts[1].title()  # Convert to title case
            else:
                patient_name = "Unknown"
        except:
            patient_name = "Unknown"
    
    if not patient_name:
        st.error("❌ Could not determine patient name.")
        return
    
    # Extract timestamp from run_id (format: YYYY_MM_DD_HH_MM_timestamp)
    timestamp = None
    try:
        parts = run_id.split('_')
        if len(parts) >= 5:  # YYYY_MM_DD_HH_MM_timestamp
            timestamp = f"{parts[0]}_{parts[1]}_{parts[2]}_{parts[3]}_{parts[4]}"
        else:
            st.warning("⚠️ Could not extract timestamp from run_id, using fallback search method")
    except:
        st.warning("⚠️ Could not extract timestamp from run_id, using fallback search method")
    
    st.header(f"Patient: {patient_name}")
    st.subheader(f"Run ID: {run_id}")
    if timestamp:
        st.subheader(f"Timestamp: {timestamp}")
    st.subheader(f"Framework: {framework.title()}")
    
    # Create containers for dynamic updates
    progress_container = st.empty()
    status_container = st.empty()
    status_message = st.empty()
    output_container = st.empty()
    
    # Check if analysis has been started in this session
    analysis_started_key = f"analysis_started_{run_id}"
    
    # Check if analysis has been started in this session
    if analysis_started_key not in st.session_state:
        st.session_state[analysis_started_key] = True
        
        # Start analysis in background thread for real-time UI updates
        import threading
        import queue
        
        # Create a queue for thread communication
        if 'analysis_queue' not in st.session_state:
            st.session_state.analysis_queue = queue.Queue()
        
        def run_analysis_background(run_id, patient_name, framework, timestamp, queue):
            """Run analysis in background thread"""
            try:
                print(f"🚀 Background thread starting analysis for {patient_name} using {framework}")
                success = start_analysis(run_id, patient_name, framework, timestamp)
                queue.put(("success", success))
                print(f"✅ Background thread completed with success: {success}")
            except Exception as e:
                print(f"❌ Background thread error: {e}")
                queue.put(("error", str(e)))
        
        # Start analysis in background thread
        analysis_thread = threading.Thread(
            target=run_analysis_background,
            args=(run_id, patient_name, framework, timestamp, st.session_state.analysis_queue),
            daemon=True
        )
        analysis_thread.start()
        
        # Show that analysis is starting
        status_container.info("🚀 Starting CrewAI analysis in background thread...")
        st.session_state.analysis_running = True
        st.session_state.analysis_thread = analysis_thread
    
    # Check for results from background thread
    if st.session_state.get('analysis_running', False):
        try:
            # Non-blocking check for results
            if not st.session_state.analysis_queue.empty():
                result_type, result_data = st.session_state.analysis_queue.get_nowait()
                
                if result_type == "success":
                    if result_data:
                        print(f"✅ Analysis started successfully for {patient_name}")
                        status_container.success("✅ Analysis started successfully! Monitoring progress...")
                    else:
                        print(f"❌ Analysis failed to start for {patient_name}")
                        status_container.error("❌ Analysis failed to start. Check terminal for errors.")
                        st.session_state.analysis_running = False
                elif result_type == "error":
                    print(f"❌ Analysis error: {result_data}")
                    status_container.error(f"❌ Analysis error: {result_data}")
                    st.session_state.analysis_running = False
                
                # Clear the queue after processing
                while not st.session_state.analysis_queue.empty():
                    st.session_state.analysis_queue.get_nowait()
                    
        except queue.Empty:
            # No results yet, continue monitoring
            pass
        except Exception as e:
            print(f"❌ Error checking analysis results: {e}")
            st.session_state.analysis_running = False
    
    # Always parse execution log to get latest status
    parse_execution_log(run_id, timestamp, patient_name)
    
    # Display current status from session state using containers
    progress_container.progress(st.session_state.percent / 100, text=f"Analysis Progress: {st.session_state.percent}%")
    
    # Show appropriate status message
    if st.session_state.percent == 0:
        if st.session_state.get('analysis_running', False):
            status_container.info("⏳ Analysis is starting...")
        else:
            status_container.info("⏳ Waiting for analysis to start...")
    elif st.session_state.percent < 100:
        status_container.info(f"🔄 Analysis in progress... ({st.session_state.percent}%)")
    else:
        status_container.success("✅ Analysis completed!")
    
    # Show status message if available
    if st.session_state.status_message:
        status_message.info(f"📊 {st.session_state.status_message}")
    
    # Show results when analysis is complete
    if st.session_state.percent >= 100:
        output_container.info("🎯 Loading analysis results...")
        show_results(run_id, patient_name, timestamp, output_container)
    
    # Add a refresh button for manual updates during analysis
    if st.session_state.get('analysis_running', False) and st.session_state.percent < 100:
        if st.button("🔄 Refresh Progress", key="refresh_progress"):
            # Force a rerun to update the display
            st.rerun()

if __name__ == "__main__":
    main() 