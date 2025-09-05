"""
Base class for agentic monitoring framework integrations.
All framework-specific integrations should inherit from this class.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from pathlib import Path
from datetime import datetime, timedelta
import json
import time


class BaseIntegration(ABC):
    """Abstract base class for agentic monitoring integrations."""
    
    def __init__(self):
        """Initialize the integration with performance tracking."""
        self._performance_start_time = None
        self._performance_metrics = {
            'duration_ms': None,
            'tokens_used': None,
            'tool_calls': None,
            'steps_completed': None,
            'success': True,
            'error_message': None
        }
    
    def _start_performance_tracking(self):
        """Start tracking performance metrics. Override if custom tracking is needed."""
        self._performance_start_time = time.time()
        self._performance_metrics = {
            'duration_ms': None,
            'tokens_used': None,
            'tool_calls': None,
            'steps_completed': None,
            'success': True,
            'error_message': None
        }
    
    def _end_performance_tracking(self, success: bool = True, error_message: Optional[str] = None):
        """End performance tracking and calculate duration. Override if custom tracking is needed."""
        if self._performance_start_time:
            duration_ms = int((time.time() - self._performance_start_time) * 1000)
            self._performance_metrics.update({
                'duration_ms': duration_ms,
                'success': success,
                'error_message': error_message
            })
    
    def _add_performance_metrics(self, tokens_used: Optional[int] = None, 
                                tool_calls: Optional[int] = None, 
                                steps_completed: Optional[int] = None):
        """Add additional performance metrics. Override if custom tracking is needed."""
        if tokens_used is not None:
            self._performance_metrics['tokens_used'] = tokens_used
        if tool_calls is not None:
            self._performance_metrics['tool_calls'] = tool_calls
        if steps_completed is not None:
            self._performance_metrics['steps_completed'] = steps_completed
    
    def _get_performance_metrics(self) -> Dict[str, Any]:
        """Get the current performance metrics. Override if custom tracking is needed."""
        return self._performance_metrics.copy()
    
    @abstractmethod
    def run_agentic_analysis(self, patient_name: str, run_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Run agentic analysis for a patient.
        
        Args:
            patient_name: Name of the patient to analyze
            run_id: Optional run identifier for tracking
            
        Returns:
            Dictionary containing analysis results and status
        """
        pass
    
    @abstractmethod
    def test_availability(self) -> Dict[str, Any]:
        """
        Test if the framework is available and ready to run.
        
        Returns:
            Dictionary with 'available' boolean and optional 'error' message
        """
        pass
    
    def get_framework_name(self) -> str:
        """
        Get the human-readable name of this framework.
        
        Returns:
            Framework name string
        """
        return getattr(self, 'framework_name', 'Unknown Framework')
    
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
        patient_dir = Path(__file__).parent.parent
        
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
        temporal_data = {
            'weight_data': [],
            'pain_diary_data': []
        }
        
        try:
            # Process weight data
            weight_file = Path(__file__).parent.parent / "biometric" / "weight" / f"{patient_name.lower()}.json"
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
