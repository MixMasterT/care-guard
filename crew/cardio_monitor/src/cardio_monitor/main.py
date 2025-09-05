#!/usr/bin/env python
import sys
import warnings
import os
from pathlib import Path
from datetime import datetime
import glob

# Add the patient directory to the path for imports
# Use current working directory to find the patient directory
workspace_root = Path.cwd()
patient_dir = workspace_root / "patient"
sys.path.insert(0, str(patient_dir))

from agentic_data_loader import AgenticPatientDataLoader

# Import CardioMonitor using absolute import
import sys
sys.path.insert(0, str(Path(__file__).parent))
from crew import CardioMonitor

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

def find_patient_file(directory: Path, patient_name: str) -> str:
    """
    Find a patient-specific file in the given directory.
    Searches for files containing the patient name (case-insensitive).
    """
    patient_name_lower = patient_name.lower()
    
    # Look for files containing the patient name
    pattern = f"*{patient_name_lower}*"
    matching_files = list(directory.glob(pattern))
    
    if matching_files:
        # Return the first matching file
        return str(matching_files[0])
    
    # Fallback: try exact match with .json extension
    exact_pattern = f"{patient_name_lower}.json"
    exact_files = list(directory.glob(exact_pattern))
    
    if exact_files:
        return str(exact_files[0])
    
    # If still no match, return the pattern for debugging
    return str(directory / exact_pattern)

# This main file is intended to be a way for you to run your
# crew locally, so refrain from adding unnecessary logic into this file.
# Replace with inputs you want to test with, it will automatically
# interpolate any tasks and agents information

def run(inputs: dict):
    """
    Run the crew with consolidated data loading.
    This function is called from the UI (monitor.py and agentic_monitor_app.py).
    
    Args:
        inputs: Dictionary containing all necessary parameters:
            - timestamp: Timestamp from URL parameter (format: YYYY_MM_DD_HH_MM)
            - run_id: Run ID from URL parameter
            - patient_name: Patient name from URL parameter
            - biometric_buffer_path: Path to biometric data file
            - pain_diary_path: Path to pain diary file
            - weight_data_path: Path to weight data file
    """
    # Get the workspace root directory (assuming this is run from the workspace root)
    # Use a more standard approach that works from the normal execution location
    workspace_root = Path.cwd()  # Use current working directory
    
    # Use the consolidated data service instead of hardcoded paths
    # This ensures we get summarized FHIR data, not the entire records
    try:
        # Extract parameters from inputs
        timestamp = inputs.get('timestamp')
        run_id = inputs.get('run_id')
        patient_name = inputs.get('patient_name')
        biometric_buffer_path = inputs.get('biometric_buffer_path')
        pain_diary_path = inputs.get('pain_diary_path')
        weight_data_path = inputs.get('weight_data_path')
        
        # Use provided patient_name or default to "mark"
        if not patient_name:
            patient_name = "Mark"  # Default fallback
        
        # Use the consolidated data service to get agent-specific context
        try:
            data_loader = AgenticPatientDataLoader(patient_name)
            patient_context = data_loader.get_agent_specific_context("care_coordination", max_tokens=15000)
            print(f"✅ Successfully loaded patient context from AgenticPatientDataLoader")
        except Exception as e:
            print(f"⚠️ Warning: Could not load patient context from AgenticPatientDataLoader: {e}")
            print(f"   Using fallback patient context")
            patient_context = f"Patient {patient_name} - basic context from fallback"
        
        # Use provided file paths or fall back to discovery
        if not biometric_buffer_path:
            biometric_buffer_dir = workspace_root / 'patient' / 'biometric' / 'buffer'
            biometric_buffer_path = str(biometric_buffer_dir / 'simulation_biometrics.json')
        
        if not pain_diary_path:
            pain_diaries_dir = workspace_root / 'patient' / 'generated_medical_records' / 'pain_diaries'
            pain_diary_path = find_patient_file(pain_diaries_dir, patient_name)
        
        if not weight_data_path:
            weight_dir = workspace_root / 'patient' / 'biometric' / 'weight'
            weight_data_path = find_patient_file(weight_dir, patient_name)
        
        print(f"\n=== Debug: File Path Construction ===")
        print(f"workspace_root: {workspace_root}")
        print(f"biometric_buffer_path: {biometric_buffer_path}")
        print(f"pain_diary_path: {pain_diary_path}")
        print(f"weight_data_path: {weight_data_path}")
        
        # Use provided timestamp and run_id, or generate fallbacks
        if not timestamp:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            print(f"⚠️ No timestamp provided, using generated: {timestamp}")
        else:
            print(f"✅ Using provided timestamp: {timestamp}")
            
        if not run_id:
            run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
            print(f"⚠️ No run_id provided, using generated: {run_id}")
        else:
            print(f"✅ Using provided run_id: {run_id}")
        
        # Build inputs using the consolidated data service
        inputs = {
            'topic': 'Cardio Monitoring Analysis',
            'current_year': str(datetime.now().year),
            'patient_name': patient_name,
            'timestamp': timestamp,
            'run_id': run_id,
            'biometric_buffer_path': biometric_buffer_path,
            'pain_diary_path': pain_diary_path,
            'weight_data_path': weight_data_path,
            # Include the consolidated patient context for the crew
            'patient_context': patient_context,
            'framework': 'crewai'
        }
        
        print(f"Starting CrewAI analysis for patient: {patient_name}")
        
        # Run the crew and capture the output
        crew = CardioMonitor()
        
        # Create crew with file paths as parameters
        crew_instance = crew.crew(
            biometric_buffer_path=biometric_buffer_path,
            pain_diary_path=pain_diary_path,
            weight_data_path=weight_data_path
        )
        
        print(f"🚀 Starting CrewAI execution...")
        crew_output = crew_instance.kickoff(inputs=inputs)
        
        # Access the structured output using CrewAI's documented attributes
        if hasattr(crew_output, 'pydantic') and crew_output.pydantic:
            return crew_output.pydantic
        elif hasattr(crew_output, 'json_dict') and crew_output.json_dict:
            return crew_output.json_dict
        else:
            return crew_output.raw
            
    except Exception as e:
        error_msg = f"An error occurred while running the crew: {e}"
        print(f"❌ ERROR: {error_msg}")
        raise Exception(error_msg)

if __name__ == "__main__":
    # When run directly, execute the run function
    # You can test with specific values here
    test_timestamp = "2025_08_27_00_37"  # Example timestamp
    test_run_id = "2025_08_27_00_37_1756272991"  # Example run_id
    test_patient = "Mark"  # Example patient
    
    # Test file paths
    test_biometric_path = str(Path.cwd() / 'patient' / 'biometric' / 'buffer' / 'simulation_biometrics.json')
    test_pain_diary_path = str(Path.cwd() / 'patient' / 'generated_medical_records' / 'pain_diaries' / 'mark.json')
    test_weight_path = str(Path.cwd() / 'patient' / 'biometric' / 'weight' / 'mark.json')
    
    # Create test inputs dictionary
    test_inputs = {
        'timestamp': test_timestamp,
        'run_id': test_run_id,
        'patient_name': test_patient,
        'biometric_buffer_path': test_biometric_path,
        'pain_diary_path': test_pain_diary_path,
        'weight_data_path': test_weight_path
    }
    
    result = run(inputs=test_inputs)
    print(f"Test completed successfully")
