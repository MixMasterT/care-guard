#!/usr/bin/env python
import sys
import warnings
import os
from pathlib import Path
from datetime import datetime

# Add the patient directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "patient"))

from agentic_data_loader import AgenticPatientDataLoader
from cardio_monitor.crew import CardioMonitor

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

# This main file is intended to be a way for you to run your
# crew locally, so refrain from adding unnecessary logic into this file.
# Replace with inputs you want to test with, it will automatically
# interpolate any tasks and agents information

def run():
    """
    Run the crew with consolidated data loading.
    This function is called from the UI (monitor.py and agentic_monitor_app.py).
    """
    # Get the workspace root directory (assuming this is run from the workspace root)
    workspace_root = Path(__file__).parent.parent.parent.parent.parent
    
    # Use the consolidated data service instead of hardcoded paths
    # This ensures we get summarized FHIR data, not the entire records
    try:
        # For demo purposes, default to "mark" - this can be parameterized later
        patient_name = "Mark"  # This could come from UI parameters
        
        # Use the consolidated data service to get agent-specific context
        data_loader = AgenticPatientDataLoader(patient_name)
        patient_context = data_loader.get_agent_specific_context("care_coordination", max_tokens=15000)
        
        # Build inputs using the consolidated data service
        inputs = {
            'topic': 'Cardio Monitoring Analysis',
            'current_year': str(datetime.now().year),
            'patient_name': patient_name,
            # Use the consolidated data service paths instead of hardcoded ones
            'biometric_buffer_path': str(workspace_root / 'patient' / 'biometric' / 'buffer' / 'simulation_biometrics.json'),
            'patient_summary_path': str(workspace_root / f'patient/{patient_name.lower()}_biometric_summary.json'),
            'pain_diary_path': str(workspace_root / 'patient' / 'generated_medical_records/pain_diaries' / f'{patient_name.lower()}.json'),
            'weight_data_path': str(workspace_root / 'patient' / 'biometric' / 'weight' / f'{patient_name.lower()}.json'),
            # Include the consolidated patient context for the crew
            'patient_context': patient_context
        }
        
        print(f"Starting CrewAI analysis for patient: {patient_name}")
        print(f"Using consolidated data service - FHIR summary size: {len(str(patient_context.get('fhir_records', [])))} chars")
        
        # Debug: Show exactly what paths are being passed
        print(f"\n=== Debug: File Paths Being Passed to Crew ===")
        print(f"biometric_buffer_path: {inputs['biometric_buffer_path']}")
        print(f"patient_summary_path: {inputs['patient_summary_path']}")
        print(f"pain_diary_path: {inputs['pain_diary_path']}")
        print(f"weight_data_path: {inputs['weight_data_path']}")
        
        # Verify files exist
        print(f"\n=== Debug: File Existence Check ===")
        print(f"biometric_buffer_path exists: {Path(inputs['biometric_buffer_path']).exists()}")
        print(f"patient_summary_path exists: {Path(inputs['patient_summary_path']).exists()}")
        print(f"pain_diary_path exists: {Path(inputs['pain_diary_path']).exists()}")
        print(f"weight_data_path exists: {Path(inputs['weight_data_path']).exists()}")
        
        # Run the crew and capture the output
        crew = CardioMonitor()
        print(f"\n=== Debug: Creating Crew with File Paths ===")
        print(f"Passing biometric_buffer_path: {inputs['biometric_buffer_path']}")
        print(f"Passing pain_diary_path: {inputs['pain_diary_path']}")
        print(f"Passing weight_data_path: {inputs['weight_data_path']}")
        
        crew_output = crew.crew(
            biometric_buffer_path=inputs['biometric_buffer_path'],
            pain_diary_path=inputs['pain_diary_path'],
            weight_data_path=inputs['weight_data_path']
        ).kickoff(inputs=inputs)
        
        # Access the structured output using CrewAI's documented attributes
        print(f"\n=== CrewAI Analysis Complete ===")
        print(f"Raw output length: {len(str(crew_output.raw))} chars")
        
        # Try to access the Pydantic output first (if tasks specify output_pydantic)
        if hasattr(crew_output, 'pydantic') and crew_output.pydantic:
            print(f"✅ Pydantic output available: {type(crew_output.pydantic)}")
            print(f"Pydantic data: {crew_output.pydantic}")
            return crew_output.pydantic
        
        # Fallback to JSON output
        elif hasattr(crew_output, 'json_dict') and crew_output.json_dict:
            print(f"✅ JSON output available: {type(crew_output.json_dict)}")
            print(f"JSON data: {crew_output.json_dict}")
            return crew_output.json_dict
        
        # Fallback to raw output
        else:
            print(f"⚠️ No structured output available, using raw output")
            print(f"Raw output: {crew_output.raw[:500]}...")  # Show first 500 chars
            return crew_output.raw
            
    except Exception as e:
        error_msg = f"An error occurred while running the crew: {e}"
        print(f"❌ ERROR: {error_msg}")
        raise Exception(error_msg)

if __name__ == "__main__":
    # When run directly, execute the run function
    result = run()
    print(f"\n=== Final Result ===")
    print(f"Type: {type(result)}")
    print(f"Content: {result}")
