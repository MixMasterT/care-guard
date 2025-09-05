"""
Agentic Monitor Integration

Provides integration between the Streamlit patient monitor and various agentic solutions.
Acts as an orchestrator that delegates to framework-specific integrations.
"""

import json
import tempfile
from pathlib import Path
import sys
from typing import Dict, Any, Optional
from datetime import datetime
import time

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

# Import the new integration system
try:
    # Try relative import first (when used as part of the patient package)
    from .integrations import get_integration, BaseIntegration
except ImportError:
    try:
        # Try absolute import from patient package
        from patient.integrations import get_integration, BaseIntegration
    except ImportError:
        # Final fallback - try direct import
        import sys
        sys.path.insert(0, str(Path(__file__).parent))
        from integrations import get_integration, BaseIntegration


class AgenticMonitorIntegration:
    """Handles integration between the patient monitor and various agentic frameworks."""
    
    def __init__(self):
        """Initialize the integration orchestrator."""
        self.framework_integrations = {}
        self._load_framework_integrations()
    
    def _load_framework_integrations(self):
        """Load all available framework integrations."""
        try:
            # This will be populated by the integrations package
            # For now, we'll keep the existing CrewAI logic as a fallback
            pass
        except Exception as e:
            print(f"⚠️ Warning: Could not load framework integrations: {e}")
    
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
                    paths['pain_diary_path'] = str(pain_file)  # Use pain_diary_path for consistency
                    break
        
        # Weight data - find the specific file matching the patient name
        weight_data_dir = patient_dir / "biometric" / "weight"
        if weight_data_dir.exists():
            weight_file = weight_data_dir / f"{patient_name.lower()}.json"
            if weight_file.exists():
                paths['weight_data_path'] = str(weight_file)  # Changed from weight_data_dir
        
        return paths

    def _process_temporal_data(self, patient_name: str) -> Dict[str, Any]:
        """
        Process temporal data (weight and pain diary) by converting offset_ms to actual timestamps.
        
        Args:
            patient_name: Name of the patient
            
        Returns:
            Dictionary with processed temporal data
        """
        import json
        from datetime import datetime, timedelta
        
        temporal_data = {
            'weight_data': [],
            'pain_diary_data': []
        }
        
        try:
            # Process weight data
            weight_file = Path(__file__).parent / "biometric" / "weight" / f"{patient_name.lower()}.json"
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
            pain_diaries_dir = Path(__file__).parent / "generated_medical_records" / "pain_diaries"
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
            
            print(f"   🕒 Processed temporal data for {patient_name}:")
            print(f"      Weight entries: {len(temporal_data['weight_data'])}")
            print(f"      Pain diary entries: {len(temporal_data['pain_diary_data'])}")
            
        except Exception as e:
            print(f"   ⚠️ Warning: Could not process temporal data for {patient_name}: {e}")
        
        return temporal_data

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

    def run_agentic_analysis(self, patient_name: str, run_id: Optional[str] = None, framework: str = "crewai", timestamp: Optional[str] = None) -> Dict[str, Any]:
        """
        Public method to run agentic analysis for a specific patient using the specified framework.
        
        Args:
            patient_name: Name of the patient to analyze
            run_id: Optional run ID (will generate one if not provided)
            framework: Framework to use for analysis (defaults to "crewai")
            timestamp: Optional timestamp from URL parameter (format: YYYY_MM_DD_HH_MM)
            
        Returns:
            Dictionary containing the analysis results
        """
        try:
            # Use the new integration system
            try:
                integration = get_integration(framework)
                print(f"🚀 Using {framework} integration for analysis")
                return integration.run_agentic_analysis(patient_name, run_id, timestamp=timestamp)
            except (ImportError, ValueError) as e:
                print(f"❌ Integration system not available: {e}")
                return {
                    "success": False,
                    "error": f"Integration system not available: {str(e)}",
                    "run_id": run_id,
                    "patient_name": patient_name,
                    "framework": framework
                }
                
        except Exception as e:
            print(f"❌ Error in agentic analysis: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": f"Error running agentic analysis: {str(e)}",
                "run_id": run_id,
                "patient_name": patient_name,
                "framework": framework
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
        This method is kept for backward compatibility.
        
        Returns:
            Dictionary with test results
        """
        try:
            # Use the new integration system
            try:
                integration = get_integration("crewai")
                return integration.test_availability()
            except (ImportError, ValueError) as e:
                return {
                    "available": False,
                    "error": f"Integration system not available: {str(e)}"
                }
                
        except Exception as e:
            return {
                "available": False,
                "error": f"Error testing crew availability: {str(e)}"
            }
