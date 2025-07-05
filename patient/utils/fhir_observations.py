import time
import json
from pathlib import Path
from typing import Dict

def create_medical_observation(patient_id: str, heartbeat_summary: Dict) -> Dict:
    """Create a FHIR Observation resource from heartbeat summary."""
    observation = {
        "resourceType": "Observation",
        "id": f"heartbeat-{int(time.time())}",
        "status": "final",
        "category": [
            {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                        "code": "vital-signs",
                        "display": "Vital Signs"
                    }
                ]
            }
        ],
        "code": {
            "coding": [
                {
                    "system": "http://loinc.org",
                    "code": "8867-4",
                    "display": "Heart rate"
                }
            ],
            "text": "Heart Rate"
        },
        "subject": {
            "reference": f"Patient/{patient_id}"
        },
        "effectivePeriod": {
            "start": heartbeat_summary["start_time"],
            "end": heartbeat_summary["end_time"]
        },
        "valueQuantity": {
            "value": heartbeat_summary["avg_heart_rate_bpm"],
            "unit": "beats/min",
            "system": "http://unitsofmeasure.org",
            "code": "/min"
        },
        "component": [
            {
                "code": {
                    "coding": [
                        {
                            "system": "http://loinc.org",
                            "code": "8867-4",
                            "display": "Heart rate minimum"
                        }
                    ]
                },
                "valueQuantity": {
                    "value": heartbeat_summary["min_heart_rate_bpm"],
                    "unit": "beats/min"
                }
            },
            {
                "code": {
                    "coding": [
                        {
                            "system": "http://loinc.org",
                            "code": "8867-4",
                            "display": "Heart rate maximum"
                        }
                    ]
                },
                "valueQuantity": {
                    "value": heartbeat_summary["max_heart_rate_bpm"],
                    "unit": "beats/min"
                }
            },
            {
                "code": {
                    "coding": [
                        {
                            "system": "http://loinc.org",
                            "code": "8867-4",
                            "display": "Heart rate variability"
                        }
                    ]
                },
                "valueQuantity": {
                    "value": heartbeat_summary["heart_rate_variability"],
                    "unit": "beats/min"
                }
            }
        ],
        "note": [
            {
                "text": f"Heartbeat monitoring session: {heartbeat_summary['total_heartbeats']} heartbeats recorded over {heartbeat_summary['duration_seconds']:.1f} seconds"
            }
        ]
    }
    
    return observation

def save_heartbeat_observation_to_fhir(patient_id: str, heartbeat_summary: Dict):
    """Save heartbeat observation to the patient's FHIR record."""
    try:
        # Create the observation
        observation = create_medical_observation(patient_id, heartbeat_summary)
        
        # Find the patient's FHIR file
        fhir_dir = Path(__file__).parent.parent / "generated_medical_records"
        patient_file = fhir_dir / f"{patient_id}.json"
        
        if not patient_file.exists():
            print(f"❌ Patient FHIR file not found: {patient_file}")
            return False
        
        # Load existing FHIR bundle
        with open(patient_file, 'r') as f:
            fhir_bundle = json.load(f)
        
        # Add the observation to the bundle
        if 'entry' not in fhir_bundle:
            fhir_bundle['entry'] = []
        
        # Create bundle entry for the observation
        entry = {
            "fullUrl": f"urn:uuid:{observation['id']}",
            "resource": observation
        }
        
        fhir_bundle['entry'].append(entry)
        
        # Save updated FHIR bundle
        with open(patient_file, 'w') as f:
            json.dump(fhir_bundle, f, indent=2)
        
        print(f"✅ Saved heartbeat observation to {patient_file}")
        return True
        
    except Exception as e:
        print(f"❌ Error saving heartbeat observation: {e}")
        import traceback
        traceback.print_exc()
        return False 