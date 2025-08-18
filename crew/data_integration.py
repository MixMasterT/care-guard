#!/usr/bin/env python3
"""
Data integration layer for patient monitoring system.
Provides unified access to FHIR, biometric, and pain journal data.
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path
import requests

class PatientDataIntegrator:
    """Unified data access layer for patient monitoring."""
    
    def __init__(self, opensearch_url: str = "http://localhost:9200"):
        self.opensearch_url = opensearch_url
        self.patient_dir = Path(__file__).parent.parent / "patient"
        
    def get_patient_context(self, patient_id: str, time_window_hours: int = 24) -> Dict[str, Any]:
        """Get comprehensive patient context for assessment."""
        
        # Get current biometrics
        current_biometrics = self._get_current_biometrics()
        
        # Get historical data from OpenSearch (if available)
        historical_context = self._get_historical_context(patient_id, time_window_hours)
        
        # Get FHIR data
        fhir_data = self._get_fhir_data(patient_id)
        
        # Get pain journal data
        pain_data = self._get_pain_journal_data(patient_id)
        
        return {
            "patient_id": patient_id,
            "current_biometrics": current_biometrics,
            "historical_context": historical_context,
            "fhir_data": fhir_data,
            "pain_data": pain_data,
            "assessment_timestamp": datetime.now().isoformat()
        }
    
    def _get_current_biometrics(self) -> Dict[str, Any]:
        """Get current biometric data from simulation buffer."""
        buffer_file = self.patient_dir / "biometric/buffer/simulation_biometrics.json"
        
        if not buffer_file.exists():
            return {"status": "no_data", "message": "No biometric data available"}
        
        try:
            with open(buffer_file, 'r') as f:
                data = json.load(f)
            
            # Get the most recent events of each type
            latest_events = {}
            for event in data:
                event_type = event.get('event_type')
                if event_type not in latest_events:
                    latest_events[event_type] = event
                else:
                    # Keep the most recent event
                    current_time = datetime.fromisoformat(event['timestamp'])
                    existing_time = datetime.fromisoformat(latest_events[event_type]['timestamp'])
                    if current_time > existing_time:
                        latest_events[event_type] = event
            
            return {
                "status": "current",
                "latest_events": latest_events,
                "total_events": len(data)
            }
            
        except Exception as e:
            return {"status": "error", "message": f"Error reading biometric data: {e}"}
    
    def _get_historical_context(self, patient_id: str, hours: int) -> Dict[str, Any]:
        """Get historical context from OpenSearch."""
        # Placeholder for OpenSearch integration
        # In a real implementation, this would query the vector database
        return {
            "status": "placeholder",
            "message": "OpenSearch integration pending",
            "time_window_hours": hours
        }
    
    def _get_fhir_data(self, patient_id: str) -> Dict[str, Any]:
        """Get FHIR patient data."""
        fhir_dir = self.patient_dir / "fhir_data"
        
        if not fhir_dir.exists():
            return {"status": "no_data", "message": "No FHIR data directory found"}
        
        # Look for patient-specific FHIR files
        patient_files = list(fhir_dir.glob(f"*{patient_id}*.json"))
        
        if not patient_files:
            return {"status": "no_data", "message": f"No FHIR data found for patient {patient_id}"}
        
        fhir_data = {}
        for file_path in patient_files:
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    fhir_data[file_path.stem] = data
            except Exception as e:
                fhir_data[file_path.stem] = {"error": str(e)}
        
        return {
            "status": "loaded",
            "files": len(patient_files),
            "data": fhir_data
        }
    
    def _get_pain_journal_data(self, patient_id: str) -> Dict[str, Any]:
        """Get pain journal data."""
        # Placeholder for pain journal integration
        return {
            "status": "placeholder",
            "message": "Pain journal integration pending",
            "patient_id": patient_id
        }
    
    def assess_patient_status(self, patient_context: Dict[str, Any]) -> Dict[str, Any]:
        """Assess patient status based on current data."""
        
        biometrics = patient_context.get('current_biometrics', {})
        latest_events = biometrics.get('latest_events', {})
        
        # Extract current vital signs
        vitals = self._extract_vital_signs(latest_events)
        
        # Assess severity based on vital signs
        severity = self._assess_severity(vitals)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(severity, vitals)
        
        return {
            "severity": severity,
            "vital_signs": vitals,
            "recommendations": recommendations,
            "timestamp": datetime.now().isoformat()
        }
    
    def _extract_vital_signs(self, latest_events: Dict[str, Any]) -> Dict[str, Any]:
        """Extract current vital signs from biometric events."""
        vitals = {}
        
        # Extract heart rate from heartbeat events
        if 'heartbeat' in latest_events:
            heartbeat = latest_events['heartbeat']
            # Calculate heart rate from interval_ms
            interval_ms = heartbeat.get('interval_ms', 1000)
            if interval_ms > 0:
                vitals['heart_rate_bpm'] = round(60000 / interval_ms)
            vitals['pulse_strength'] = heartbeat.get('pulse_strength', 1.0)
        
        # Extract SpO2
        if 'spo2' in latest_events:
            vitals['spo2_percent'] = latest_events['spo2'].get('spo2', 0)
        
        # Extract temperature
        if 'temperature' in latest_events:
            vitals['temperature_celsius'] = latest_events['temperature'].get('temperature', 0)
        
        # Extract blood pressure
        if 'blood_pressure' in latest_events:
            bp = latest_events['blood_pressure']
            vitals['blood_pressure'] = {
                'systolic': bp.get('systolic', 0),
                'diastolic': bp.get('diastolic', 0)
            }
        
        # Extract ECG rhythm
        if 'ecg_rhythm' in latest_events:
            vitals['ecg_rhythm'] = latest_events['ecg_rhythm'].get('ecg_rhythm', 'Unknown')
        
        return vitals
    
    def _assess_severity(self, vitals: Dict[str, Any]) -> str:
        """Assess patient severity based on vital signs."""
        
        # Critical criteria
        if self._is_critical(vitals):
            return "critical"
        
        # Mild concern criteria
        if self._is_mild_concern(vitals):
            return "mild_concern"
        
        # Normal
        return "normal"
    
    def _is_critical(self, vitals: Dict[str, Any]) -> bool:
        """Check if patient is in critical condition."""
        
        # Heart rate critical
        hr = vitals.get('heart_rate_bpm', 0)
        if hr > 120 or hr < 50:
            return True
        
        # SpO2 critical
        spo2 = vitals.get('spo2_percent', 100)
        if spo2 < 90:
            return True
        
        # Blood pressure critical
        bp = vitals.get('blood_pressure', {})
        systolic = bp.get('systolic', 0)
        diastolic = bp.get('diastolic', 0)
        if systolic > 180 or systolic < 90 or diastolic > 110 or diastolic < 60:
            return True
        
        # Temperature critical
        temp = vitals.get('temperature_celsius', 37)
        if temp > 39 or temp < 35:
            return True
        
        # ECG rhythm critical
        rhythm = vitals.get('ecg_rhythm', '').lower()
        critical_rhythms = ['st elevation', 'vt', 'vf', 'asystole']
        if any(critical in rhythm for critical in critical_rhythms):
            return True
        
        return False
    
    def _is_mild_concern(self, vitals: Dict[str, Any]) -> bool:
        """Check if patient has mild concerns."""
        
        # Heart rate mild concern
        hr = vitals.get('heart_rate_bpm', 0)
        if (100 < hr <= 120) or (50 <= hr < 60):
            return True
        
        # SpO2 mild concern
        spo2 = vitals.get('spo2_percent', 100)
        if 90 <= spo2 < 95:
            return True
        
        # Blood pressure mild concern
        bp = vitals.get('blood_pressure', {})
        systolic = bp.get('systolic', 0)
        diastolic = bp.get('diastolic', 0)
        if (140 < systolic <= 180) or (90 <= systolic < 100) or (90 < diastolic <= 110) or (60 <= diastolic < 70):
            return True
        
        # Temperature mild concern
        temp = vitals.get('temperature_celsius', 37)
        if (37.8 < temp <= 39) or (35 <= temp < 36.1):
            return True
        
        return False
    
    def _generate_recommendations(self, severity: str, vitals: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on severity."""
        
        recommendations = []
        
        if severity == "critical":
            recommendations.extend([
                "IMMEDIATE: Contact emergency services",
                "IMMEDIATE: Notify on-call physician",
                "Monitor patient continuously",
                "Prepare emergency intervention equipment"
            ])
        elif severity == "mild_concern":
            recommendations.extend([
                "Schedule follow-up within 24-48 hours",
                "Monitor vital signs more frequently",
                "Consider patient outreach for symptom assessment",
                "Review medication compliance"
            ])
        else:  # normal
            recommendations.extend([
                "Continue routine monitoring",
                "Document stable status",
                "Maintain current care plan"
            ])
        
        return recommendations

# Example usage
if __name__ == "__main__":
    integrator = PatientDataIntegrator()
    
    # Get patient context
    context = integrator.get_patient_context("patient_001")
    
    # Assess status
    assessment = integrator.assess_patient_status(context)
    
    print("Patient Assessment:")
    print(f"Severity: {assessment['severity']}")
    print(f"Vital Signs: {assessment['vital_signs']}")
    print(f"Recommendations: {assessment['recommendations']}") 