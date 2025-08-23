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

def show_results(run_id, patient_name, output_container):
    """Display the analysis results in a structured format"""
    try:
        # Look for the medical log file (contains the final output)
        logs_dir = Path(__file__).parent / "agentic_monitor_logs"
        
        # Try multiple patterns to handle case variations and different naming conventions
        search_patterns = [
            f"*_{run_id}_*_medical_log.json",  # Most flexible pattern - should work with new format
            f"*_{run_id}_{patient_name.lower()}_medical_log.json",  # lowercase
            f"*_{run_id}_{patient_name.title()}_medical_log.json",  # title case
            f"*_{run_id}_{patient_name}_medical_log.json",          # original case
        ]
        
        medical_log_files = []
        for pattern in search_patterns:
            files = list(logs_dir.glob(pattern))
            if files:
                medical_log_files.extend(files)
                break
        
        if not medical_log_files:
            # Debug: show what files exist
            all_files = list(logs_dir.glob(f"*_{run_id}_*"))
            output_container.error(f"❌ No results found. Please check the analysis logs.")
            output_container.info(f"🔍 Debug: Found {len(all_files)} files matching run_id {run_id}:")
            for f in all_files:
                output_container.info(f"   - {f.name}")
            return
        
        # Read the most recent medical log
        latest_log = max(medical_log_files, key=lambda x: x.stat().st_mtime)
        output_container.info(f"🔍 Reading results from: {latest_log.name}")
        
        with open(latest_log, 'r') as f:
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

def update_progress_from_execution_log(run_id: str):
    """
    Update progress information from execution log and refresh UI.
    This function should be called regularly to keep the UI updated.
    """
    if parse_execution_log(run_id):
        # Force a rerun to update the UI with new session state values
        st.rerun()


def parse_execution_log(run_id: str) -> bool:
    """
    Parse the execution log JSON file and update session state with progress information.
    
    Args:
        run_id: The run ID to look for in execution log files
        
    Returns:
        True if execution log was found and parsed, False otherwise
    """
    try:
        logs_dir = Path(__file__).parent / "agentic_monitor_logs"
        execution_log_files = list(logs_dir.glob(f"*_{run_id}_*_execution_log.json"))
        
        if not execution_log_files:
            return False
        
        # Get the most recent execution log file
        latest_log = max(execution_log_files, key=lambda x: x.stat().st_mtime)
        
        with open(latest_log, 'r') as f:
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
        else:
            return False
            
    except Exception as e:
        print(f"❌ Error parsing execution log: {e}")
        return False


def start_analysis(run_id, patient_name, framework):
    """Start the agentic analysis in a background thread"""
    try:
        # Import the integration module
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent))
        
        try:
            from agentic_monitor_integration import AgenticMonitorIntegration
        except ImportError as e:
            print(f"❌ Failed to import AgenticMonitorIntegration: {e}")
            return False
        
        # Initialize integration and start analysis
        integration = AgenticMonitorIntegration()
        print(f"🚀 Starting {framework} analysis for {patient_name} with run_id: {run_id}")
        
        # Framework-specific handling
        if framework.lower() == "crewai":
            # Execute existing code as-is for CrewAI
            availability = integration.test_crew_availability()
            
            if not availability.get("available"):
                print(f"❌ Crew not available: {availability.get('error', 'Unknown error')}")
                return False
            
            # Start the analysis with framework parameter
            results = integration.run_agentic_analysis(patient_name, run_id=run_id, framework=framework)
            print(f"📊 Analysis results: {results}")
            
            if results.get("success"):
                print(f"✅ Analysis started successfully for {patient_name} using {framework}!")
                return True
            else:
                print(f"❌ Analysis failed to start: {results.get('error', 'Unknown error')}")
                return False
                
        elif framework.lower() == "langgraph":
            # New block for LangGraph framework
            print(f"🔧 LangGraph framework selected - implementing LangGraph analysis...")
            # TODO: Implement LangGraph-specific analysis logic here
            print(f"⚠️ LangGraph analysis not yet implemented")
            return False
            
        else:
            # Error block for unsupported frameworks
            print(f"❌ Unsupported framework: {framework}")
            print(f"Supported frameworks: crewai, langgraph")
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
    
    # Extract patient name from run_id if not provided
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
    
    st.header(f"Patient: {patient_name}")
    st.subheader(f"Run ID: {run_id}")
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
        
        def run_analysis_background(run_id, patient_name, framework, queue):
            """Run analysis in background thread"""
            try:
                print(f"🚀 Background thread starting analysis for {patient_name} using {framework}")
                success = start_analysis(run_id, patient_name, framework)
                queue.put(("success", success))
                print(f"✅ Background thread completed with success: {success}")
            except Exception as e:
                print(f"❌ Background thread error: {e}")
                queue.put(("error", str(e)))
        
        # Start analysis in background thread
        analysis_thread = threading.Thread(
            target=run_analysis_background,
            args=(run_id, patient_name, framework, st.session_state.analysis_queue),
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
    parse_execution_log(run_id)
    
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
        show_results(run_id, patient_name, output_container)
    
    # Add a refresh button for manual updates during analysis
    if st.session_state.get('analysis_running', False) and st.session_state.percent < 100:
        if st.button("🔄 Refresh Progress", key="refresh_progress"):
            # Force a rerun to update the display
            st.rerun()

if __name__ == "__main__":
    main() 