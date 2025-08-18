"""
Agentic Patient Data Loader

A flexible data loader for agentic monitoring solutions that can load patient data
from various sources and format it for different AI agents and monitoring systems.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
import pandas as pd

class AgenticPatientDataLoader:
    """
    Flexible data loader for patient monitoring agents.
    
    Loads and prepares patient data from various sources:
    - Biometric buffer (real-time device data)
    - Patient summaries (historical biometric data)
    - Pain journals (patient-reported symptoms)
    - FHIR records (medical history)
    - Existing agent logs (audit trail)
    """
    
    def __init__(self, patient_name: str, base_path: Optional[Path] = None):
        """
        Initialize the data loader for a specific patient.
        
        Args:
            patient_name: Name of the patient (Allen, Mark, Zach)
            base_path: Base path for patient data (defaults to current directory)
        """
        self.patient_name = patient_name
        self.base_path = base_path or Path(__file__).parent
        
        # Patient ID mapping
        self.patient_ids = {
            "Allen": "f420e6d4-55db-974f-05cb-52d06375b65f",
            "Mark": "29244161-9d02-b8b6-20cc-350f53ffe7a1.",
            "Zach": "4403cbc3-78eb-fbe6-e5c5-bee837f31ea9" 
        }
        
        self.patient_id = self.patient_ids.get(patient_name)
        if not self.patient_id:
            raise ValueError(f"Unknown patient: {patient_name}. Available: {list(self.patient_ids.keys())}")
    
    def load_biometric_buffer(self, buffer_file: Optional[Path] = None) -> List[Dict[str, Any]]:
        """
        Load the current biometric buffer.
        
        Args:
            buffer_file: Optional path to specific buffer file
            
        Returns:
            List of biometric events
        """
        if buffer_file is None:
            buffer_file = self.base_path / "biometric" / "buffer" / "simulation_biometrics.json"
        
        if not buffer_file.exists():
            return []
        
        try:
            with open(buffer_file, 'r') as f:
                data = json.load(f)
            return data if isinstance(data, list) else []
        except Exception as e:
            print(f"Error loading biometric buffer: {e}")
            return []
    
    def load_patient_summary(self) -> Dict[str, Any]:
        """
        Load patient's biometric summary.
        
        Returns:
            Patient summary data
        """
        summary_file = self.base_path / f"{self.patient_name.lower()}_biometric_summary.json"
        
        if not summary_file.exists():
            return {}
        
        try:
            with open(summary_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading patient summary: {e}")
            return {}
    
    def load_pain_journal(self) -> List[Dict[str, Any]]:
        """
        Load patient's pain journal entries.
        
        Returns:
            List of pain journal entries
        """
        # Pain journal file mapping
        pain_journal_files = {
            "Allen": self.base_path / "pain_journals" / "Allen322_Hickle134_f420e6d4-55db-974f-05cb-52d06375b65f.json",
            "Mark": self.base_path / "pain_journals" / "Mark765_Green467_29244161-9d02-b8b6-20cc-350f53ffe7a1.json", 
            "Zach": self.base_path / "pain_journals" / "Zachery872_Cole117_4403cbc3-78eb-fbe6-e5c5-bee837f31ea9.json"
        }
        
        pain_file = pain_journal_files.get(self.patient_name)
        
        if not pain_file or not pain_file.exists():
            return []
        
        try:
            with open(pain_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading pain journal: {e}")
            return []
    
    def load_fhir_records(self, fhir_dir: Optional[Path] = None) -> List[Dict[str, Any]]:
        """
        Load patient's FHIR medical records.
        
        Args:
            fhir_dir: Optional path to FHIR records directory
            
        Returns:
            List of FHIR records
        """
        if fhir_dir is None:
            fhir_dir = self.base_path / "generated_medical_records" / "fhir"
        
        if not fhir_dir.exists():
            return []
        
        fhir_records = []
        
        # Map patient names to exact FHIR file names
        fhir_file_mapping = {
            "Allen": "Allen322_Hickle134_f420e6d4-55db-974f-05cb-52d06375b65f.json",
            "Mark": "Mark765_Green467_29244161-9d02-b8b6-20cc-350f53ffe7a1.json",
            "Zach": "Zachery872_Cole117_4403cbc3-78eb-fbe6-e5c5-bee837f31ea9.json"
        }
        
        # Get the exact file name for this patient
        fhir_filename = fhir_file_mapping.get(self.patient_name)
        
        if not fhir_filename:
            return []
        
        fhir_file = fhir_dir / fhir_filename
        
        if not fhir_file.exists():
            return []
        
        # Load the specific patient's FHIR file
        try:
            with open(fhir_file, 'r') as f:
                records = json.load(f)
                if isinstance(records, list):
                    fhir_records.extend(records)
                else:
                    fhir_records.append(records)
        except Exception as e:
            print(f"Error loading FHIR file {fhir_file}: {e}")
            return []
        
        return fhir_records

    def summarize_fhir_records(self, fhir_records: List[Dict[str, Any]], max_summary_size: int = 5000, years_back: int = 0.5) -> Dict[str, Any]:
        """
        Extract only essential information from FHIR records to reduce context size.
        
        Args:
            fhir_records: List of FHIR records (can be individual resources or Bundle entries)
            max_summary_size: Maximum size of summary in characters
            years_back: Number of years back to include for time-sensitive records (observations, procedures, encounters)
            Default is 0.5 (6 months) for aggressive context reduction
            
        Returns:
            Dictionary with essential FHIR information
        """
        if not fhir_records:
            return {"summary": "No FHIR records available", "essential_data": {}}
        
        # Calculate cutoff date for filtering recent records
        from datetime import datetime, timedelta
        cutoff_date = datetime.now() - timedelta(days=years_back * 365)
        
        essential_data = {
            "patient_info": {},
            "conditions": [],
            "medications": [],
            "procedures": [],
            "observations": [],
            "encounters": [],
            "allergies": [],
            "immunizations": []
        }
        
        try:
            # Handle both individual resources and Bundle format
            resources_to_process = []
            
            for record in fhir_records:
                if "resourceType" in record and record["resourceType"] == "Bundle" and "entry" in record:
                    # This is a FHIR Bundle - extract resources from entries
                    for entry in record.get("entry", []):
                        if "resource" in entry:
                            resources_to_process.append(entry["resource"])
                else:
                    # This is an individual resource
                    resources_to_process.append(record)
            
            print(f"Processing {len(resources_to_process)} FHIR resources...")
            
            for resource in resources_to_process:
                # Extract patient information
                if "resourceType" in resource and resource["resourceType"] == "Patient":
                    patient = resource
                    essential_data["patient_info"] = {
                        "name": patient.get("name", [{}])[0].get("text", "Unknown"),
                        "birth_date": patient.get("birthDate", "Unknown"),
                        "gender": patient.get("gender", "Unknown"),
                        "marital_status": patient.get("maritalStatus", {}).get("text", "Unknown"),
                        "address": patient.get("address", [{}])[0].get("text", "Unknown") if patient.get("address") else "Unknown"
                    }
                
                # Extract conditions (diagnoses) - include all as they're ongoing
                elif "resourceType" in resource and resource["resourceType"] == "Condition":
                    condition = resource
                    essential_data["conditions"].append({
                        "code": condition.get("code", {}).get("text", "Unknown"),
                        "status": condition.get("clinicalStatus", {}).get("text", "Unknown"),
                        "onset": condition.get("onsetDateTime", "Unknown"),
                        "severity": condition.get("severity", {}).get("text", "Unknown")
                    })
                
                # Extract medications - include all active ones
                elif "resourceType" in resource and resource["resourceType"] == "MedicationRequest":
                    med = resource
                    essential_data["medications"].append({
                        "medication": med.get("medicationCodeableConcept", {}).get("text", "Unknown"),
                        "status": med.get("status", "Unknown"),
                        "intent": med.get("intent", "Unknown"),
                        "dosage": med.get("dosage", [{}])[0].get("text", "Unknown") if med.get("dosage") else "Unknown"
                    })
                
                # Extract procedures - only recent ones (within years_back)
                elif "resourceType" in resource and resource["resourceType"] == "Procedure":
                    proc = resource
                    performed_date_str = proc.get("performedDateTime", "")
                    
                    # Check if procedure is within the time window
                    if performed_date_str:
                        try:
                            performed_date = datetime.fromisoformat(performed_date_str.replace('Z', '+00:00'))
                            if performed_date >= cutoff_date:
                                essential_data["procedures"].append({
                                    "code": proc.get("code", {}).get("text", "Unknown"),
                                    "status": proc.get("status", "Unknown"),
                                    "performed": performed_date_str,
                                    "performer": proc.get("performer", [{}])[0].get("display", "Unknown") if proc.get("performer") else "Unknown"
                                })
                        except (ValueError, TypeError):
                            # If date parsing fails, include it anyway
                            essential_data["procedures"].append({
                                "code": proc.get("code", {}).get("text", "Unknown"),
                                "status": proc.get("status", "Unknown"),
                                "performed": performed_date_str,
                                "performer": proc.get("performer", [{}])[0].get("display", "Unknown") if proc.get("performer") else "Unknown"
                            })
                    else:
                        # If no date, include it (might be recent)
                        essential_data["procedures"].append({
                            "code": proc.get("code", {}).get("text", "Unknown"),
                            "status": proc.get("status", "Unknown"),
                            "performed": performed_date_str,
                            "performer": proc.get("performer", [{}])[0].get("display", "Unknown") if proc.get("performer") else "Unknown"
                        })
                
                # Extract observations (vital signs, lab results) - only recent ones
                elif "resourceType" in resource and resource["resourceType"] == "Observation":
                    obs = resource
                    effective_date_str = obs.get("effectiveDateTime", "")
                    
                    # Check if observation is within the time window
                    if effective_date_str:
                        try:
                            effective_date = datetime.fromisoformat(effective_date_str.replace('Z', '+00:00'))
                            if effective_date >= cutoff_date:
                                essential_data["observations"].append({
                                    "code": obs.get("code", {}).get("text", "Unknown"),
                                    "value": obs.get("valueQuantity", {}).get("value", "Unknown"),
                                    "unit": obs.get("valueQuantity", {}).get("unit", ""),
                                    "status": obs.get("status", "Unknown"),
                                    "effective": effective_date_str
                                })
                        except (ValueError, TypeError):
                            # If date parsing fails, include it anyway
                            essential_data["observations"].append({
                                "code": obs.get("code", {}).get("text", "Unknown"),
                                "value": obs.get("valueQuantity", {}).get("value", "Unknown"),
                                "unit": obs.get("valueQuantity", {}).get("unit", ""),
                                "status": obs.get("status", "Unknown"),
                                "effective": effective_date_str
                            })
                    else:
                        # If no date, include it (might be recent)
                        essential_data["observations"].append({
                            "code": obs.get("code", {}).get("text", "Unknown"),
                            "value": obs.get("valueQuantity", {}).get("value", "Unknown"),
                            "unit": obs.get("valueQuantity", {}).get("unit", ""),
                            "status": obs.get("status", "Unknown"),
                            "effective": effective_date_str
                        })
                
                # Extract encounters (visits) - only recent ones
                elif "resourceType" in resource and resource["resourceType"] == "Encounter":
                    enc = resource
                    period_start_str = enc.get("period", {}).get("start", "")
                    
                    # Check if encounter is within the time window
                    if period_start_str:
                        try:
                            period_start = datetime.fromisoformat(period_start_str.replace('Z', '+00:00'))
                            if period_start >= cutoff_date:
                                essential_data["encounters"].append({
                                    "type": enc.get("type", [{}])[0].get("text", "Unknown"),
                                    "status": enc.get("status", "Unknown"),
                                    "period_start": period_start_str,
                                    "period_end": enc.get("period", {}).get("end", "Unknown"),
                                    "reason": enc.get("reasonCode", [{}])[0].get("text", "Unknown") if enc.get("reasonCode") else "Unknown"
                                })
                        except (ValueError, TypeError):
                            # If date parsing fails, include it anyway
                            essential_data["encounters"].append({
                                "type": enc.get("type", [{}])[0].get("text", "Unknown"),
                                "status": enc.get("status", "Unknown"),
                                "period_start": period_start_str,
                                "period_end": enc.get("period", {}).get("end", "Unknown"),
                                "reason": enc.get("reasonCode", [{}])[0].get("text", "Unknown") if enc.get("reasonCode") else "Unknown"
                            })
                    else:
                        # If no date, include it (might be recent)
                        essential_data["encounters"].append({
                            "type": enc.get("type", [{}])[0].get("text", "Unknown"),
                            "status": enc.get("status", "Unknown"),
                            "period_start": period_start_str,
                            "period_end": enc.get("period", {}).get("end", "Unknown"),
                            "reason": enc.get("reasonCode", [{}])[0].get("text", "Unknown") if enc.get("reasonCode") else "Unknown"
                        })
                
                # Extract allergies - include all as they're ongoing
                elif "resourceType" in resource and resource["resourceType"] == "AllergyIntolerance":
                    allergy = resource
                    essential_data["allergies"].append({
                        "substance": allergy.get("code", {}).get("text", "Unknown"),
                        "status": allergy.get("clinicalStatus", {}).get("text", "Unknown"),
                        "severity": allergy.get("severity", "Unknown"),
                        "reaction": allergy.get("reaction", [{}])[0].get("manifestation", [{}])[0].get("text", "Unknown") if allergy.get("reaction") else "Unknown"
                    })
                
                # Extract immunizations - include all as they're permanent
                elif "resourceType" in resource and resource["resourceType"] == "Immunization":
                    imm = resource
                    essential_data["immunizations"].append({
                        "vaccine": imm.get("vaccineCode", {}).get("text", "Unknown"),
                        "status": imm.get("status", "Unknown"),
                        "date": imm.get("occurrenceDateTime", "Unknown"),
                        "lot": imm.get("lotNumber", "Unknown")
                    })
            
            # Create a summary that fits within the size limit
            summary_parts = []
            
            # Add patient info
            if essential_data["patient_info"]:
                summary_parts.append(f"Patient: {essential_data['patient_info'].get('name', 'Unknown')} ({essential_data['patient_info'].get('gender', 'Unknown')}, {essential_data['patient_info'].get('birth_date', 'Unknown')})")
            
            # Add counts and key information with time filtering note
            if essential_data["conditions"]:
                summary_parts.append(f"Conditions: {len(essential_data['conditions'])} active conditions")
            if essential_data["medications"]:
                summary_parts.append(f"Medications: {len(essential_data['medications'])} active prescriptions")
            if essential_data["procedures"]:
                summary_parts.append(f"Procedures: {len(essential_data['procedures'])} procedures (last {years_back} years)")
            if essential_data["observations"]:
                summary_parts.append(f"Observations: {len(essential_data['observations'])} vital signs/lab results (last {years_back} years)")
            if essential_data["encounters"]:
                summary_parts.append(f"Encounters: {len(essential_data['encounters'])} medical visits (last {years_back} years)")
            if essential_data["allergies"]:
                summary_parts.append(f"Allergies: {len(essential_data['allergies'])} documented allergies")
            if essential_data["immunizations"]:
                summary_parts.append(f"Immunizations: {len(essential_data['immunizations'])} vaccinations")
            
            summary = "; ".join(summary_parts)
            
            # Truncate if too long
            if len(summary) > max_summary_size:
                summary = summary[:max_summary_size-3] + "..."
            
            return {
                "summary": summary,
                "essential_data": essential_data,
                "total_records": len(fhir_records),
                "total_resources": len(resources_to_process),
                "summary_size_chars": len(summary),
                "filtering_applied": f"Observations, procedures, and encounters filtered to last {years_back} years"
            }
            
        except Exception as e:
            print(f"Error summarizing FHIR records: {e}")
            return {
                "summary": f"Error processing FHIR records: {str(e)}",
                "essential_data": {},
                "total_records": len(fhir_records),
                "total_resources": 0,
                "summary_size_chars": 0,
                "filtering_applied": "Error occurred during filtering"
            }
    
    def load_existing_logs(self, logs_dir: Optional[Path] = None, max_logs: int = 10, max_total_size_mb: float = 5.0) -> List[Dict[str, Any]]:
        """
        Load existing agentic monitor logs for this patient with aggressive filtering.
        
        Args:
            logs_dir: Optional path to logs directory
            max_logs: Maximum number of log files to load
            max_total_size_mb: Maximum total size in MB to load
            
        Returns:
            List of existing log entries (filtered and size-limited)
        """
        if logs_dir is None:
            logs_dir = self.base_path / "agentic_monitor_logs"
        
        patient_logs = []
        
        if not logs_dir.exists():
            return patient_logs
        
        # Get all log files for this patient, sorted by modification time (newest first)
        log_files = []
        for log_file in logs_dir.glob(f"{self.patient_name.lower()}_*.json"):
            try:
                mtime = log_file.stat().st_mtime
                log_files.append((log_file, mtime))
            except Exception:
                continue
        
        # Sort by modification time (newest first) and limit to max_logs
        log_files.sort(key=lambda x: x[1], reverse=True)
        log_files = log_files[:max_logs]
        
        total_size_mb = 0.0
        loaded_count = 0
        
        for log_file, _ in log_files:
            try:
                # Check file size before loading
                file_size_mb = log_file.stat().st_size / (1024 * 1024)
                
                # Skip if this file would exceed our size limit
                if total_size_mb + file_size_mb > max_total_size_mb:
                    print(f"   Skipping {log_file.name} ({file_size_mb:.1f}MB) - would exceed {max_total_size_mb}MB limit")
                    continue
                
                # Skip extremely large files (>10MB) as they're likely corrupted or contain too much data
                if file_size_mb > 10.0:
                    print(f"   Skipping {log_file.name} ({file_size_mb:.1f}MB) - file too large")
                    continue
                
                with open(log_file, 'r') as f:
                    log_entry = json.load(f)
                    patient_logs.append(log_entry)
                    total_size_mb += file_size_mb
                    loaded_count += 1
                    
                    print(f"   Loaded {log_file.name} ({file_size_mb:.1f}MB) - total: {total_size_mb:.1f}MB")
                    
            except Exception as e:
                print(f"Error loading log file {log_file}: {e}")
        
        print(f"   Loaded {loaded_count} log files, total size: {total_size_mb:.1f}MB")
        return patient_logs
    
    def analyze_biometric_trends(self, biometric_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze biometric data for trends and patterns.
        
        Args:
            biometric_data: List of biometric events
            
        Returns:
            Dictionary with trend analysis
        """
        if not biometric_data:
            return {}
        
        # Group by type
        by_type = {}
        for event in biometric_data:
            event_type = event.get('type', 'unknown')
            if event_type not in by_type:
                by_type[event_type] = []
            by_type[event_type].append(event)
        
        trends = {}
        
        # Analyze heart rate trends
        if 'heart_beat' in by_type:
            heart_rates = [e.get('value', 0) for e in by_type['heart_beat'] if e.get('value')]
            if heart_rates:
                trends['heart_rate'] = {
                    'count': len(heart_rates),
                    'min': min(heart_rates),
                    'max': max(heart_rates),
                    'avg': sum(heart_rates) / len(heart_rates),
                    'trend': 'increasing' if len(heart_rates) > 1 and heart_rates[-1] > heart_rates[0] else 'stable'
                }
        
        # Analyze SpO2 trends
        if 'spo2' in by_type:
            spo2_values = [e.get('value', 0) for e in by_type['spo2'] if e.get('value')]
            if spo2_values:
                trends['spo2'] = {
                    'count': len(spo2_values),
                    'min': min(spo2_values),
                    'max': max(spo2_values),
                    'avg': sum(spo2_values) / len(spo2_values),
                    'concern': any(v < 95 for v in spo2_values)
                }
        
        # Analyze blood pressure trends
        if 'blood_pressure' in by_type:
            systolic_values = [e.get('systolic', 0) for e in by_type['blood_pressure'] if e.get('systolic')]
            diastolic_values = [e.get('diastolic', 0) for e in by_type['blood_pressure'] if e.get('diastolic')]
            
            if systolic_values and diastolic_values:
                trends['blood_pressure'] = {
                    'count': len(systolic_values),
                    'systolic_avg': sum(systolic_values) / len(systolic_values),
                    'diastolic_avg': sum(diastolic_values) / len(diastolic_values),
                    'hypertension_risk': any(s > 140 or d > 90 for s, d in zip(systolic_values, diastolic_values))
                }
        
        return trends
    
    def get_patient_context(self, include_trends: bool = True, use_fhir_summary: bool = True, years_back: int = 0.5) -> Dict[str, Any]:
        """
        Get comprehensive patient context for analysis.
        
        Args:
            include_trends: Whether to include biometric trend analysis
            use_fhir_summary: Whether to use FHIR summary instead of full records
            years_back: Number of years back to include for time-sensitive FHIR records
            Default is 0.5 (6 months) for aggressive context reduction
            
        Returns:
            Dictionary with complete patient context
        """
        print(f"Loading context for patient: {self.patient_name}")
        
        biometric_buffer = self.load_biometric_buffer()
        patient_summary = self.load_patient_summary()
        pain_journal = self.load_pain_journal()
        fhir_records = self.load_fhir_records()
        existing_logs = self.load_existing_logs()
        
        # Use FHIR summary to reduce context size
        if use_fhir_summary and fhir_records:
            fhir_summary = self.summarize_fhir_records(fhir_records, years_back=years_back)
            print(f"FHIR Summary: {fhir_summary['summary_size_chars']} chars (vs {len(str(fhir_records))} chars for full records)")
            if 'filtering_applied' in fhir_summary:
                print(f"FHIR Filtering: {fhir_summary['filtering_applied']}")
            # Wrap summary in expected structure with 'data' field
            fhir_data = [{"data": fhir_summary}]  # Simple dict structure instead of FHIRBundle
        else:
            fhir_data = fhir_records
        
        print(f"Loaded data counts - Biometric: {len(biometric_buffer)}, Summary: {len(patient_summary)}, Pain: {len(pain_journal)}, FHIR: {len(fhir_records)} records, Logs: {len(existing_logs)}")
        
        context = {
            "patient_name": self.patient_name,
            "patient_id": self.patient_id,
            "biometric_buffer": biometric_buffer,
            "patient_summary": patient_summary,
            "pain_journal": pain_journal,
            "fhir_records": fhir_data,
            "existing_logs": existing_logs,
            "analysis_timestamp": datetime.now().isoformat(),
            "data_summary": {
                "biometric_events_count": len(biometric_buffer),
                "pain_journal_entries": len(pain_journal),
                "fhir_records_count": len(fhir_records),
                "existing_logs_count": len(existing_logs)
            }
        }
        
        if include_trends:
            context["biometric_trends"] = self.analyze_biometric_trends(biometric_buffer)
        
        return context

    def get_full_fhir_records(self, fhir_dir: Optional[Path] = None) -> List[Dict[str, Any]]:
        """
        Get full FHIR records when detailed information is needed.
        Use this sparingly as it can be very large.
        
        Args:
            fhir_dir: Optional path to FHIR records directory
            
        Returns:
            List of full FHIR records
        """
        return self.load_fhir_records(fhir_dir)

    def get_context_size_info(self, years_back: int = 0.5) -> Dict[str, Any]:
        """
        Get information about the size of different data components.
        Useful for debugging context window issues.
        
        Args:
            years_back: Number of years back to include for time-sensitive FHIR records
            Default is 0.5 (6 months) for aggressive context reduction
            
        Returns:
            Dictionary with size information for each data type
        """
        biometric_buffer = self.load_biometric_buffer()
        patient_summary = self.load_patient_summary()
        pain_journal = self.load_pain_journal()
        fhir_records = self.load_fhir_records()
        existing_logs = self.load_existing_logs()
        
        # Calculate sizes
        fhir_summary = self.summarize_fhir_records(fhir_records, years_back=years_back) if fhir_records else {}
        
        size_info = {
            "biometric_buffer": {
                "count": len(biometric_buffer),
                "size_chars": len(str(biometric_buffer)),
                "size_kb": len(str(biometric_buffer)) / 1024
            },
            "patient_summary": {
                "count": len(patient_summary),
                "size_chars": len(str(patient_summary)),
                "size_kb": len(str(patient_summary)) / 1024
            },
            "pain_journal": {
                "count": len(pain_journal),
                "size_chars": len(str(pain_journal)),
                "size_kb": len(str(pain_journal)) / 1024
            },
            "fhir_records": {
                "count": len(fhir_records),
                "full_size_chars": len(str(fhir_records)),
                "full_size_kb": len(str(fhir_records)) / 1024,
                "summary_size_chars": fhir_summary.get("summary_size_chars", 0),
                "summary_size_kb": fhir_summary.get("summary_size_chars", 0) / 1024,
                "reduction_ratio": fhir_summary.get("summary_size_chars", 0) / max(len(str(fhir_records)), 1) if fhir_records else 0,
                "filtering_applied": fhir_summary.get("filtering_applied", "None")
            },
            "existing_logs": {
                "count": len(existing_logs),
                "size_chars": len(str(existing_logs)),
                "size_kb": len(str(existing_logs)) / 1024
            }
        }
        
        # Calculate totals
        total_full_size = sum([
            size_info["biometric_buffer"]["size_chars"],
            size_info["patient_summary"]["size_chars"],
            size_info["pain_journal"]["size_chars"],
            size_info["fhir_records"]["full_size_chars"],
            size_info["existing_logs"]["size_chars"]
        ])
        
        total_summary_size = sum([
            size_info["biometric_buffer"]["size_chars"],
            size_info["patient_summary"]["size_chars"],
            size_info["pain_journal"]["size_chars"],
            size_info["fhir_records"]["summary_size_chars"],
            size_info["existing_logs"]["size_chars"]
        ])
        
        size_info["totals"] = {
            "full_size_chars": total_full_size,
            "full_size_kb": total_full_size / 1024,
            "summary_size_chars": total_summary_size,
            "summary_size_kb": total_summary_size / 1024,
            "reduction_ratio": total_summary_size / max(total_full_size, 1),
            "filtering_applied": f"Time-sensitive records filtered to last {years_back} years"
        }
        
        return size_info
    
    def save_log_entry(self, log_entry: Dict[str, Any], logs_dir: Optional[Path] = None) -> str:
        """
        Save a new log entry for the patient.
        
        Args:
            log_entry: Log entry to save
            logs_dir: Optional path to logs directory
            
        Returns:
            Path to saved log file
        """
        if logs_dir is None:
            logs_dir = self.base_path / "agentic_monitor_logs"
        
        logs_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = logs_dir / f"{self.patient_name.lower()}_{timestamp}.json"
        
        try:
            with open(log_file, 'w') as f:
                json.dump(log_entry, f, indent=2, default=str)
            return str(log_file)
        except Exception as e:
            print(f"Error saving log entry: {e}")
            return ""
    
    def get_latest_logs(self, limit: int = 5, logs_dir: Optional[Path] = None) -> List[Dict[str, Any]]:
        """
        Get the latest log entries for this patient.
        
        Args:
            limit: Maximum number of logs to return
            logs_dir: Optional path to logs directory
            
        Returns:
            List of recent log entries
        """
        logs = self.load_existing_logs(logs_dir)
        
        # Sort by timestamp and return latest
        logs.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        return logs[:limit]
    
    def export_for_crewai(self, output_file: Optional[Path] = None) -> str:
        """
        Export patient context in a format suitable for CrewAI.
        
        Args:
            output_file: Optional path for output file
            
        Returns:
            Path to exported file
        """
        context = self.get_patient_context()
        
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = self.base_path / f"{self.patient_name.lower()}_crewai_context_{timestamp}.json"
        
        try:
            with open(output_file, 'w') as f:
                json.dump(context, f, indent=2, default=str)
            return str(output_file)
        except Exception as e:
            print(f"Error exporting context: {e}")
            return "" 

    def get_minimal_context(self, max_tokens: int = 15000) -> Dict[str, Any]:
        """
        Get a minimal patient context that fits within token limits.
        This is the most aggressive data reduction method.
        
        Args:
            max_tokens: Maximum tokens to target (default 15K to leave room for prompts)
            
        Returns:
            Dictionary with minimal patient context
        """
        print(f"Loading minimal context for patient: {self.patient_name} (target: {max_tokens:,} tokens)")
        
        # Load minimal biometric data (only last 10 events)
        biometric_buffer = self.load_biometric_buffer()
        if len(biometric_buffer) > 10:
            biometric_buffer = biometric_buffer[-10:]  # Only last 10 events
            print(f"   Reduced biometric buffer from {len(biometric_buffer)} to 10 events")
        
        # Load minimal patient summary (only essential fields)
        patient_summary = self.load_patient_summary()
        if patient_summary:
            # Keep only essential fields
            essential_summary = {
                "patient_name": patient_summary.get("patient_name", self.patient_name),
                "age": patient_summary.get("age", "Unknown"),
                "gender": patient_summary.get("gender", "Unknown"),
                "risk_factors": patient_summary.get("risk_factors", [])[:3],  # Only top 3
                "chronic_conditions": patient_summary.get("chronic_conditions", [])[:5]  # Only top 5
            }
            patient_summary = essential_summary
            print(f"   Reduced patient summary to essential fields only")
        
        # Load minimal pain journal (only last 3 entries)
        pain_journal = self.load_pain_journal()
        if len(pain_journal) > 3:
            pain_journal = pain_journal[-3:]  # Only last 3 entries
            print(f"   Reduced pain journal from {len(pain_journal)} to 3 entries")
        
        # Load FHIR records and create ultra-minimal summary
        fhir_records = self.load_fhir_records()
        if fhir_records:
            fhir_summary = self.summarize_fhir_records(fhir_records, max_summary_size=1000, years_back=0.5)
            fhir_data = fhir_summary
            print(f"   FHIR Summary: {fhir_summary['summary_size_chars']} chars")
        else:
            fhir_data = {"summary": "No FHIR records available"}
        
        # Load only the most recent logs (max 2 files, max 1MB total)
        existing_logs = self.load_existing_logs(max_logs=2, max_total_size_mb=1.0)
        
        # Create minimal context
        context = {
            "patient_name": self.patient_name,
            "patient_id": self.patient_id,
            "biometric_buffer": biometric_buffer,
            "patient_summary": patient_summary,
            "pain_journal": pain_journal,
            "fhir_records": fhir_data,
            "existing_logs": existing_logs,
            "analysis_timestamp": datetime.now().isoformat()
        }
        
        # Calculate final size
        total_chars = len(str(context))
        estimated_tokens = total_chars / 4
        
        print(f"   Final context size: {total_chars:,} characters = {estimated_tokens:,.0f} tokens")
        print(f"   Target: {max_tokens:,} tokens")
        print(f"   Status: {'✅ UNDER LIMIT' if estimated_tokens <= max_tokens else '❌ OVER LIMIT'}")
        
        return context 

    def get_agent_specific_context(self, agent_type: str, max_tokens: int = 15000) -> Dict[str, Any]:
        """
        Get context data specific to a particular agent type.
        This prevents unnecessary data from bloating the context for each agent.
        
        Args:
            agent_type: Type of agent ('biometric_analysis', 'care_coordination', 'patient_communication')
            max_tokens: Maximum tokens to target
            
        Returns:
            Dictionary with agent-specific context
        """
        print(f"Loading {agent_type} context for patient: {self.patient_name} (target: {max_tokens:,} tokens)")
        
        if agent_type == "biometric_analysis":
            # Biometric analysis agent needs the FULL biometric buffer for comprehensive analysis
            # Do NOT truncate this data - it's essential for pattern recognition
            biometric_buffer = self.load_biometric_buffer()
            patient_summary = self.load_patient_summary()
            
            # Summarize patient summary to reduce size while keeping essential info
            if patient_summary and isinstance(patient_summary, dict):
                # Keep only the most essential fields for biometric analysis
                essential_summary = {
                    "patient_name": patient_summary.get("patient_name", self.patient_name),
                    "age": patient_summary.get("age", "Unknown"),
                    "gender": patient_summary.get("gender", "Unknown"),
                    "risk_factors": patient_summary.get("risk_factors", [])[:5],  # Top 5 risk factors
                    "chronic_conditions": patient_summary.get("chronic_conditions", [])[:5]  # Top 5 conditions
                }
                patient_summary = essential_summary
                print(f"   Summarized patient summary to essential fields only")
            
            print(f"   Loading FULL biometric buffer: {len(biometric_buffer)} events")
            print(f"   Biometric buffer size: {len(str(biometric_buffer)):,} characters")
            print(f"   Patient summary size: {len(str(patient_summary)):,} characters")
            
            context = {
                "patient_name": self.patient_name,
                "patient_id": self.patient_id,
                "biometric_buffer": biometric_buffer,
                "patient_summary": patient_summary,
                "analysis_timestamp": datetime.now().isoformat()
            }
            
        elif agent_type == "care_coordination":
            # Care coordination agent needs FHIR data and recent logs
            fhir_records = self.load_fhir_records()
            if fhir_records:
                # Use comprehensive FHIR summary - keep more essential information for care coordination
                fhir_summary = self.summarize_fhir_records(fhir_records, max_summary_size=3000, years_back=1.0)  # 1 year, larger summary
                
                # Create a more comprehensive FHIR summary that preserves critical medical information
                fhir_data = [{
                    "data": {
                        "summary": fhir_summary.get("summary", "No FHIR summary available"),
                        "filtering_applied": fhir_summary.get("filtering_applied", "Unknown"),
                        "essential_data": {
                            "conditions": fhir_summary.get("essential_data", {}).get("conditions", [])[:15],  # Top 15 conditions
                            "medications": fhir_summary.get("essential_data", {}).get("medications", []),  # All medications
                            "procedures": fhir_summary.get("essential_data", {}).get("procedures", [])[:20],  # Top 20 recent procedures
                            "observations": fhir_summary.get("essential_data", {}).get("observations", [])[:30],  # Top 30 recent observations
                            "encounters": fhir_summary.get("essential_data", {}).get("encounters", [])[:15],  # Top 15 recent encounters
                            "allergies": fhir_summary.get("essential_data", {}).get("allergies", []),  # All allergies
                            "immunizations": fhir_summary.get("essential_data", {}).get("immunizations", [])  # All immunizations
                        }
                    }
                }]
                print(f"   Comprehensive FHIR summary (1 year): {len(str(fhir_data))} chars (preserving essential medical data)")
            else:
                fhir_data = [{"data": {"summary": "No FHIR records available"}}]
            
            # Only load very recent logs for care coordination
            existing_logs = self.load_existing_logs(max_logs=2, max_total_size_mb=1.0)
            
            context = {
                "patient_name": self.patient_name,
                "patient_id": self.patient_id,
                "fhir_records": fhir_data,  # Now a list as expected
                "existing_logs": existing_logs,
                "analysis_timestamp": datetime.now().isoformat()
            }
            
        elif agent_type == "patient_communication":
            # Patient communication agent needs pain journal and basic patient info
            pain_journal = self.load_pain_journal()
            patient_summary = self.load_patient_summary()
            
            # Keep only essential patient info
            if patient_summary and isinstance(patient_summary, dict):
                essential_summary = {
                    "patient_name": patient_summary.get("patient_name", self.patient_name),
                    "age": patient_summary.get("age", "Unknown"),
                    "gender": patient_summary.get("gender", "Unknown")
                }
                patient_summary = essential_summary
            else:
                # If no patient summary or it's not a dict, create minimal one
                patient_summary = {
                    "patient_name": self.patient_name,
                    "age": "Unknown",
                    "gender": "Unknown"
                }
            
            context = {
                "patient_name": self.patient_name,
                "patient_id": self.patient_id,
                "pain_journal": pain_journal,
                "patient_summary": patient_summary,
                "analysis_timestamp": datetime.now().isoformat()
            }
            
        else:
            raise ValueError(f"Unknown agent type: {agent_type}. Available: biometric_analysis, care_coordination, patient_communication")
        
        # Calculate final size
        total_chars = len(str(context))
        estimated_tokens = total_chars / 4
        
        print(f"   {agent_type} context size: {total_chars:,} characters = {estimated_tokens:,.0f} tokens")
        print(f"   Target: {max_tokens:,} tokens")
        print(f"   Status: {'✅ UNDER LIMIT' if estimated_tokens <= max_tokens else '❌ OVER LIMIT'}")
        
        return context 