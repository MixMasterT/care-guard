"""
Patient Monitoring Workflow for LangGraph
Replicates CrewAI functionality with three agents: biometric_reviewer, triage_nurse, and log_writer.
Enhanced with OpenSearch RAG for better context-aware analysis.
"""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, TypedDict, List, Optional
from langgraph.graph import StateGraph, START, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from dotenv import load_dotenv
import os

# OpenSearch imports for RAG
try:
    from opensearchpy import OpenSearch
    OPENSEARCH_AVAILABLE = True
except ImportError:
    OPENSEARCH_AVAILABLE = False
    print("Warning: opensearch-py not available. RAG features will be disabled.")

# Load environment variables from .env file
load_dotenv()

# Import Pydantic models for structured output
from agentic_types.models import (
    TrendInsightPayload, DecisionPayload, AgenticFinalOutput,
    Finding, Recommendation, PatientIdentity, ExecutionMetrics, Artifacts,
    BiometricMetricStats
)

# State for the LangGraph workflow
class LangGraphState(TypedDict):
    # Biometric data
    biometric_data: list
    biometric_analysis: TrendInsightPayload | None
    
    # Patient data
    pain_diary_data: list
    weight_data: list
    fhir_records: dict
    patient_context: dict
    
    # Analysis results
    triage_decision: DecisionPayload | None
    medical_log: AgenticFinalOutput | None
    
    # Execution tracking
    run_id: str
    patient_name: str
    error: str | None
    progress: int
    status: str
    events: list
    tokens_used: int
    current_step: int
    tool_calls: int

# Dynamic patient UUID discovery
def discover_patient_uuid(patient_name: str) -> str:
    """
    Dynamically discover a patient's UUID from available data files.
    Searches pain diary files first, then FHIR files as fallback.
    """
    workspace_root = Path(__file__).parent.parent.parent
    
    # Method 1: Search pain diary files
    pain_diaries_dir = workspace_root / "patient" / "generated_medical_records" / "pain_diaries"
    if pain_diaries_dir.exists():
        for pain_file in pain_diaries_dir.glob("*.json"):
            if patient_name.lower() in pain_file.name.lower():
                try:
                    with open(pain_file, 'r') as f:
                        pain_data = json.load(f)
                        if pain_data and isinstance(pain_data, list) and len(pain_data) > 0:
                            # Extract UUID from first entry
                            first_entry = pain_data[0]
                            if 'patient_id' in first_entry:
                                uuid = first_entry['patient_id']
                                print(f"Discovered UUID for {patient_name}: {uuid} (from pain diary)")
                                return uuid
                except Exception as e:
                    print(f"WARNING: Error reading pain diary file {pain_file}: {e}")
                    continue
    
    # Method 2: Search FHIR files
    fhir_dir = workspace_root / "patient" / "generated_medical_records" / "fhir"
    if fhir_dir.exists():
        for fhir_file in fhir_dir.glob("*.json"):
            if patient_name.lower() in fhir_file.name.lower():
                try:
                    with open(fhir_file, 'r') as f:
                        fhir_data = json.load(f)
                        if fhir_data and 'entry' in fhir_data:
                            for entry in fhir_data['entry']:
                                if 'resource' in entry and entry['resource'].get('resourceType') == 'Patient':
                                    uuid = entry['resource'].get('id')
                                    if uuid:
                                        print(f"Discovered UUID for {patient_name}: {uuid} (from FHIR)")
                                        return uuid
                except Exception as e:
                    print(f"WARNING: Error reading FHIR file {fhir_file}: {e}")
                    continue
    
    print(f"WARNING: Could not discover UUID for patient '{patient_name}'")
    return None

# OpenSearch RAG functions
def get_patient_uuid(patient_name: str) -> str:
    """Get the UUID for a patient name using dynamic discovery."""
    return discover_patient_uuid(patient_name)

def discover_all_patients() -> Dict[str, str]:
    """
    Discover all available patients and their UUIDs from data files.
    Returns a dictionary mapping patient names to UUIDs.
    """
    workspace_root = Path(__file__).parent.parent.parent
    patients = {}
    
    # Method 1: Search pain diary files
    pain_diaries_dir = workspace_root / "patient" / "generated_medical_records" / "pain_diaries"
    if pain_diaries_dir.exists():
        for pain_file in pain_diaries_dir.glob("*.json"):
            try:
                with open(pain_file, 'r') as f:
                    pain_data = json.load(f)
                    if pain_data and isinstance(pain_data, list) and len(pain_data) > 0:
                        first_entry = pain_data[0]
                        if 'patient_id' in first_entry:
                            uuid = first_entry['patient_id']
                            # Extract patient name from filename
                            filename = pain_file.stem
                            # Try to extract a readable name (remove UUID and other parts)
                            if '_' in filename:
                                name_parts = filename.split('_')
                                # Look for parts that look like names (not UUIDs)
                                for part in name_parts:
                                    if len(part) > 2 and not part.startswith('f') and not part.isdigit():
                                        # Clean up the name (remove numbers, keep only letters)
                                        clean_name = ''.join(c for c in part if c.isalpha()).lower()
                                        if clean_name and len(clean_name) > 2:
                                            patients[clean_name] = uuid
                                            break
            except Exception as e:
                print(f"WARNING: Error reading pain diary file {pain_file}: {e}")
                continue
    
    # Method 2: Search FHIR files (as backup)
    fhir_dir = workspace_root / "patient" / "generated_medical_records" / "fhir"
    if fhir_dir.exists():
        for fhir_file in fhir_dir.glob("*.json"):
            try:
                with open(fhir_file, 'r') as f:
                    fhir_data = json.load(f)
                    if fhir_data and 'entry' in fhir_data:
                        for entry in fhir_data['entry']:
                            if 'resource' in entry and entry['resource'].get('resourceType') == 'Patient':
                                uuid = entry['resource'].get('id')
                                if uuid:
                                    # Extract patient name from filename
                                    filename = fhir_file.stem
                                    if '_' in filename:
                                        name_parts = filename.split('_')
                                        for part in name_parts:
                                            if len(part) > 2 and not part.startswith('f') and not part.isdigit():
                                                # Clean up the name (remove numbers, keep only letters)
                                                clean_name = ''.join(c for c in part if c.isalpha()).lower()
                                                if clean_name and len(clean_name) > 2:
                                                    if clean_name not in patients:  # Don't overwrite existing
                                                        patients[clean_name] = uuid
                                                    break
            except Exception as e:
                print(f"WARNING: Error reading FHIR file {fhir_file}: {e}")
                continue
    
    print(f"Discovered {len(patients)} patients: {list(patients.keys())}")
    return patients

def get_pain_diary_entries_from_opensearch(patient_name: str, size: int = 50) -> List[Dict]:
    """Retrieve pain diary entries from OpenSearch for a patient."""
    if not OPENSEARCH_AVAILABLE:
        return []
    
    try:
        client = OpenSearch(hosts=[{'host': 'localhost', 'port': 9200}])
        
        # Get the patient's UUID
        patient_uuid = get_patient_uuid(patient_name)
        if not patient_uuid:
            print(f"WARNING: No UUID mapping found for patient '{patient_name}'")
            return []
        
        # Search by the patient's UUID
        query_body = {
            "query": {
                "bool": {
                    "must": [
                        {"term": {"patient_id": patient_uuid}},
                        {"exists": {"field": "pain_level"}}
                    ]
                }
            },
            "sort": [{"date": {"order": "desc"}}],
            "size": size
        }
        
        print(f"Pain diary search query: {json.dumps(query_body, indent=2)}")
        response = client.search(index="pain-diaries", body=query_body)
        
        entries = [hit["_source"] for hit in response["hits"]["hits"]]
        print(f"Found {len(entries)} pain diary entries for patient '{patient_name}'")
        return entries
    except Exception as e:
        print(f"Warning: Failed to retrieve pain diary entries from OpenSearch: {e}")
        return []

def get_fhir_entries_from_opensearch(patient_name: str, size: int = 100) -> List[Dict]:
    """Retrieve FHIR medical records from OpenSearch for a patient."""
    if not OPENSEARCH_AVAILABLE:
        return []
    
    try:
        client = OpenSearch(hosts=[{'host': 'localhost', 'port': 9200}])
        
        # Get the patient's UUID
        patient_uuid = get_patient_uuid(patient_name)
        if not patient_uuid:
            print(f"WARNING: No UUID mapping found for patient '{patient_name}'")
            return []
        
        # Search for FHIR records by the patient's UUID
        query_body = {
            "query": {
                "bool": {
                    "must": [
                        {"term": {"patient_id": patient_uuid}}
                    ]
                }
            },
            "sort": [{"indexed_at": {"order": "desc"}}],
            "size": size
        }
        
        print(f"FHIR search query: {json.dumps(query_body, indent=2)}")
        response = client.search(index="fhir-medical-records", body=query_body)
        
        entries = [hit["_source"] for hit in response["hits"]["hits"]]
        print(f"Found {len(entries)} FHIR records for patient '{patient_name}'")
        return entries
    except Exception as e:
        print(f"Warning: Failed to retrieve FHIR entries from OpenSearch: {e}")
        return []

def format_pain_diary_for_prompt(entries: List[Dict]) -> str:
    """Format pain diary entries for inclusion in prompts."""
    if not entries:
        return "No pain diary entries found."
    
    lines = []
    for entry in entries[:10]:  # Limit to most recent 10 entries
        date = entry.get('date', 'Unknown date')
        pain_level = entry.get('pain_level', 'N/A')
        mood = entry.get('mood', 'N/A')
        notes = entry.get('notes', '')
        lines.append(f"Date: {date}, Pain Level: {pain_level}/10, Mood: {mood}, Notes: {notes}")
    
    return f"Recent Pain Diary Entries ({len(entries)} total):\n" + "\n".join(lines)

def format_fhir_entries_for_prompt(entries: List[Dict]) -> str:
    """Format FHIR entries for inclusion in prompts."""
    if not entries:
        return "No FHIR medical records found."
    
    # Group by resource type for better organization
    resource_groups = {}
    for entry in entries:
        resource_type = entry.get('resource_type', 'Unknown')
        if resource_type not in resource_groups:
            resource_groups[resource_type] = []
        resource_groups[resource_type].append(entry)
    
    lines = []
    for resource_type, resources in resource_groups.items():
        lines.append(f"\n{resource_type} Records ({len(resources)}):")
        for resource in resources[:5]:  # Limit to 5 per type
            resource_data = resource.get('resource_data', {})
            summary = extract_fhir_summary(resource_type, resource_data)
            lines.append(f"  - {summary}")
    
    return f"Medical Records Summary ({len(entries)} total resources):" + "".join(lines)

def extract_fhir_summary(resource_type: str, resource_data: Dict) -> str:
    """Extract a meaningful summary from FHIR resource data."""
    try:
        if resource_type == 'Observation':
            value = resource_data.get('valueQuantity', {})
            return f"{resource_data.get('code', {}).get('text', 'Observation')}: {value.get('value', 'N/A')} {value.get('unit', '')}"
        elif resource_type == 'Condition':
            return f"{resource_data.get('code', {}).get('text', 'Condition')} - {resource_data.get('clinicalStatus', {}).get('text', 'Unknown status')}"
        elif resource_type == 'MedicationRequest':
            return f"{resource_data.get('medicationCodeableConcept', {}).get('text', 'Medication')} - {resource_data.get('status', 'Unknown status')}"
        elif resource_type == 'Patient':
            name = resource_data.get('name', [{}])[0] if resource_data.get('name') else {}
            return f"Patient: {name.get('text', 'Unknown name')}"
        elif resource_type == 'Procedure':
            return f"{resource_data.get('code', {}).get('text', 'Procedure')} - {resource_data.get('status', 'Unknown status')}"
        else:
            return f"{resource_type}: {resource_data.get('id', 'Unknown ID')}"
    except Exception:
        return f"{resource_type}: Data available"

def load_biometric_data_step(state: LangGraphState) -> LangGraphState:
    """Load biometric data from buffer file."""
    try:
        workspace_root = Path(__file__).parent.parent.parent
        buffer_path = str(workspace_root / "patient" / "biometric" / "buffer" / "simulation_biometrics.json")
        
        with open(buffer_path, 'r') as f:
            biometric_data = json.load(f)
        
        return {
            **state,
            "biometric_data": biometric_data,
            "current_step": state.get("current_step", 0) + 1,
            "tool_calls": state.get("tool_calls", 0) + 0,  # No LLM calls in this step
            "error": None,
            "progress": 20,
            "status": "biometric_data_loaded",
            "events": state.get("events", []) + [{
                "timestamp": datetime.now().isoformat(),
                "type": "biometric_data_loaded",
                "message": f"Step {state.get('current_step', 0) + 1}: Loaded {len(biometric_data)} biometric records"
            }]
        }
    except Exception as e:
        return {
            **state,
            "error": f"Failed to load biometric data: {e}",
            "status": "error"
        }

def biometric_reviewer_step(state: LangGraphState) -> LangGraphState:
    """Biometric reviewer agent - analyzes biometric data."""
    if state.get("error"):
        return state
    
    try:
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.1)
        
        biometric_data = state["biometric_data"]
        
        # Prepare biometric data summary for analysis
        heart_rates = []
        spo2_values = []
        blood_pressures = []
        respiration_rates = []
        temperatures = []
        
        for record in biometric_data:
            event_type = record.get('event_type', '')
            
            # Handle heartbeat events - convert interval_ms to heart rate
            if event_type == 'heartbeat':
                interval_ms = record.get('interval_ms', 1000)
                if interval_ms > 0:
                    heart_rate = 60000 / interval_ms  # Convert to BPM
                    heart_rates.append(heart_rate)
                # Also check if there's a direct 'value' field (heart rate in BPM)
                elif 'value' in record and record['value'] is not None:
                    heart_rates.append(float(record['value']))
            
            # Handle SpO2 events
            elif event_type == 'spo2':
                spo2_value = record.get('spo2') or record.get('value')
                if spo2_value is not None:
                    spo2_values.append(float(spo2_value))
            
            # Handle blood pressure events
            elif event_type == 'blood_pressure':
                bp = {
                    'systolic': record.get('systolic', 0),
                    'diastolic': record.get('diastolic', 0)
                }
                if bp['systolic'] > 0 and bp['diastolic'] > 0:
                    blood_pressures.append(bp)
            
            # Handle respiration events
            elif event_type == 'respiration':
                interval_ms = record.get('interval_ms', 0)
                if interval_ms > 0:
                    respiration_rate = 60000 / interval_ms  # Convert to breaths per minute
                    respiration_rates.append(respiration_rate)
            
            # Handle temperature events
            elif event_type == 'temperature':
                temp_value = record.get('temperature') or record.get('value')
                if temp_value is not None:
                    temperatures.append(float(temp_value))
        
        # Calculate basic statistics using BiometricMetricStats objects
        stats = []
        if heart_rates:
            stats.append(BiometricMetricStats(
                metric_name="heart_rate",
                average=round(sum(heart_rates) / len(heart_rates), 1),
                min_value=round(min(heart_rates), 1),
                max_value=round(max(heart_rates), 1),
                count=len(heart_rates),
                unit="bpm",
                trend="Stable"  # Could be enhanced with actual trend analysis
            ))
        if spo2_values:
            stats.append(BiometricMetricStats(
                metric_name="spo2",
                average=round(sum(spo2_values) / len(spo2_values), 1),
                min_value=round(min(spo2_values), 1),
                max_value=round(max(spo2_values), 1),
                count=len(spo2_values),
                unit="%",
                trend="Stable"  # Could be enhanced with actual trend analysis
            ))
        if blood_pressures:
            systolic_values = [bp['systolic'] for bp in blood_pressures]
            diastolic_values = [bp['diastolic'] for bp in blood_pressures]
            stats.append(BiometricMetricStats(
                metric_name="blood_pressure",
                average=round((sum(systolic_values) / len(systolic_values) + sum(diastolic_values) / len(diastolic_values)) / 2, 1),
                min_value=round(min(systolic_values), 1),
                max_value=round(max(systolic_values), 1),
                count=len(blood_pressures),
                unit="mmHg",
                trend="Stable"
            ))
        if respiration_rates:
            stats.append(BiometricMetricStats(
                metric_name="respiration",
                average=round(sum(respiration_rates) / len(respiration_rates), 1),
                min_value=round(min(respiration_rates), 1),
                max_value=round(max(respiration_rates), 1),
                count=len(respiration_rates),
                unit="breaths/min",
                trend="Stable"
            ))
        if temperatures:
            stats.append(BiometricMetricStats(
                metric_name="temperature",
                average=round(sum(temperatures) / len(temperatures), 1),
                min_value=round(min(temperatures), 1),
                max_value=round(max(temperatures), 1),
                count=len(temperatures),
                unit="°C",
                trend="Stable"
            ))
        
        system_prompt = """You are an experienced technical expert in real-time patient monitoring and interpreting time-series biosignals.
        Review live and recent biometric signals to extract concise observations and identify any immediate risks.
        Provide concise summaries and highlight anomalies only.
        
        Provide response in this exact JSON format:
        {
            "metric": "comprehensive_biometrics",
            "description": "brief summary of what the data shows",
            "window": "Recent monitoring period",
            "support_score": 0.85,
            "confidence_level": "high",
            "risk_assessment": "low|moderate|high|critical",
            "immediate_concerns": ["concern1", "concern2"],
            "recommendations": ["action1", "action2"],
            "requires_attention": true/false,
            "next_action": "immediate next step"
        }
        
        Note: The stats field will be populated automatically from the calculated statistics.
        
        RISK ASSESSMENT GUIDELINES:
        - LOW: All values within normal ranges, stable trends
        - MODERATE: Some values outside normal ranges, minor fluctuations  
        - HIGH: Multiple values outside normal ranges, concerning trends
        - CRITICAL: Values in dangerous ranges, rapid changes
        
        EMERGENCY FLAGS:
        - Heart rate < 50 or > 120 bpm → critical
        - SpO2 < 90% → critical
        - Blood pressure < 90/60 or > 180/110 → high"""
        
        # Create a summary of the calculated statistics
        stats_summary = []
        for stat in stats:
            stats_summary.append(f"{stat.metric_name}: avg={stat.average}{stat.unit}, range={stat.min_value}-{stat.max_value}{stat.unit}, count={stat.count}")
        
        analysis_summary = f"""
        Biometric Data Summary:
        {chr(10).join(stats_summary)}
        Total Records: {len(biometric_data)}
        """
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Analyze this biometric data:\n\n{analysis_summary}")
        ]
        
        response = llm.invoke(messages)
        response_content = response.content if hasattr(response, 'content') else str(response)
        
        # Track tokens used
        tokens_used = state.get("tokens_used", 0)
        if hasattr(response, 'usage') and response.usage:
            tokens_used += response.usage.total_tokens
        else:
            # Estimate tokens if usage not available
            estimated_tokens = len(response_content.split()) * 1.3  # Rough estimate
            tokens_used += int(estimated_tokens)
        
        # Parse JSON response
        import re
        json_match = re.search(r'\{.*\}', response_content, re.DOTALL)
        if json_match:
            result_data = json.loads(json_match.group())
            biometric_analysis = TrendInsightPayload(**result_data)
        else:
            # Fallback analysis
            hr_avg = 0
            spo2_avg = 0
            
            # Extract values from stats list
            for stat in stats:
                if stat.metric_name == "heart_rate":
                    hr_avg = stat.average or 0
                elif stat.metric_name == "spo2":
                    spo2_avg = stat.average or 0
            
            risk_level = "low"
            requires_attention = False
            immediate_concerns = []
            
            if hr_avg < 50 or hr_avg > 120:
                risk_level = "critical"
                requires_attention = True
                immediate_concerns.append(f"abnormal heart rate ({hr_avg} bpm)")
            elif hr_avg < 60 or hr_avg > 100:
                risk_level = "high"
                requires_attention = True
                immediate_concerns.append(f"elevated heart rate ({hr_avg} bpm)")
            
            if spo2_avg < 90:
                risk_level = "critical"
                requires_attention = True
                immediate_concerns.append(f"hypoxemia ({spo2_avg}%)")
            elif spo2_avg < 95:
                risk_level = "high"
                requires_attention = True
                immediate_concerns.append(f"low oxygen ({spo2_avg}%)")
            
            biometric_analysis = TrendInsightPayload(
                metric="comprehensive_biometrics",
                description=f"Biometric analysis shows {risk_level} risk level",
                window="Recent monitoring period",
                stats=stats,
                support_score=0.85,
                confidence_level="high",
                risk_assessment=risk_level,
                immediate_concerns=immediate_concerns,
                recommendations=["continue monitoring"] if not requires_attention else ["check patient immediately"],
                requires_attention=requires_attention,
                next_action="Continue monitoring" if not requires_attention else "Immediate assessment required"
            )
        
        return {
            **state,
            "biometric_analysis": biometric_analysis,
            "tokens_used": tokens_used,
            "current_step": state.get("current_step", 0) + 1,
            "tool_calls": state.get("tool_calls", 0) + 1,  # 1 LLM call for biometric analysis
            "error": None,
            "progress": 40,
            "status": "biometrics_analyzed",
            "events": state.get("events", []) + [{
                "timestamp": datetime.now().isoformat(),
                "type": "biometrics_analyzed",
                "message": f"Step {state.get('current_step', 0) + 1}: Biometric analysis completed - {biometric_analysis.risk_assessment} risk level"
            }]
        }
    except Exception as e:
        return {
            **state,
            "error": f"Failed to analyze biometrics: {e}",
            "status": "error"
        }

def load_patient_data_step(state: LangGraphState) -> LangGraphState:
    """Load patient data using OpenSearch RAG for enhanced context."""
    if state.get("error"):
        return state
    
    try:
        workspace_root = Path(__file__).parent.parent.parent
        patient_name = state["patient_name"]
        
        print(f"Loading patient data for {patient_name} using OpenSearch RAG...")
        
        # Check OpenSearch connectivity and indices
        if OPENSEARCH_AVAILABLE:
            try:
                client = OpenSearch(hosts=[{'host': 'localhost', 'port': 9200}])
                indices = client.cat.indices(format='json')
                print(f"Available OpenSearch indices: {[idx['index'] for idx in indices]}")
                
                # Check document counts in each index
                for index_info in indices:
                    if index_info['index'] in ['pain-diaries', 'fhir-medical-records']:
                        index_name = index_info['index']
                        doc_count = index_info['docs.count']
                        print(f"📈 {index_name}: {doc_count} documents")
                        
                        # Show a sample document to understand the structure
                        if int(doc_count) > 0:
                            sample_response = client.search(
                                index=index_name,
                                body={"query": {"match_all": {}}, "size": 1}
                            )
                            if sample_response['hits']['hits']:
                                sample_doc = sample_response['hits']['hits'][0]['_source']
                                print(f"📄 Sample {index_name} document keys: {list(sample_doc.keys())}")
                                if 'patient_id' in sample_doc:
                                    print(f"   patient_id example: {sample_doc['patient_id']}")
                                if 'source_file' in sample_doc:
                                    print(f"   source_file example: {sample_doc['source_file']}")
            except Exception as e:
                print(f"WARNING: OpenSearch connectivity issue: {e}")
        
        # Load pain diary entries from OpenSearch
        pain_diary_entries = get_pain_diary_entries_from_opensearch(patient_name, size=50)
        pain_diary_data = pain_diary_entries  # Keep original format for compatibility
        
        # Load weight data (still from file for now)
        weight_file = workspace_root / "patient" / "biometric" / "weight" / f"{patient_name.lower()}.json"
        weight_data = []
        if weight_file.exists():
            with open(weight_file, 'r') as f:
                weight_data = json.load(f)
        
        # Load FHIR records from OpenSearch
        fhir_entries = get_fhir_entries_from_opensearch(patient_name, size=100)
        fhir_records = {"entries": fhir_entries}  # Keep original format for compatibility
        
        # Create enhanced patient context using RAG data
        pain_context = format_pain_diary_for_prompt(pain_diary_entries)
        fhir_context = format_fhir_entries_for_prompt(fhir_entries)
        
        # Enhanced patient context combining RAG data
        patient_context = f"""
Patient: {patient_name}

MEDICAL HISTORY (from OpenSearch):
{fhir_context}

PAIN DIARY HISTORY (from OpenSearch):
{pain_context}

WEIGHT DATA: {len(weight_data)} measurements available
"""
        
        print(f"SUCCESS: Loaded {len(pain_diary_entries)} pain diary entries and {len(fhir_entries)} FHIR records from OpenSearch")
        
        return {
            **state,
            "pain_diary_data": pain_diary_data,
            "weight_data": weight_data,
            "fhir_records": fhir_records,
            "patient_context": patient_context,
            "current_step": state.get("current_step", 0) + 1,
            "tool_calls": state.get("tool_calls", 0) + 0,  # No LLM calls in this step
            "error": None,
            "progress": 60,
            "status": "patient_data_loaded",
            "events": state.get("events", []) + [{
                "timestamp": datetime.now().isoformat(),
                "type": "patient_data_loaded",
                "message": f"Step {state.get('current_step', 0) + 1}: Loaded patient data for {patient_name} using OpenSearch RAG ({len(pain_diary_entries)} pain entries, {len(fhir_entries)} FHIR records)"
            }]
        }
    except Exception as e:
        return {
            **state,
            "error": f"Failed to load patient data: {e}",
            "status": "error"
        }

def triage_nurse_step(state: LangGraphState) -> LangGraphState:
    """Triage nurse agent - makes care decisions."""
    if state.get("error") or not state.get("biometric_analysis"):
        return state
    
    try:
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.1)
        
        # Prepare context for triage decision
        biometric_analysis = state["biometric_analysis"]
        pain_diary = state["pain_diary_data"]
        weight_data = state["weight_data"]
        patient_context = state["patient_context"]
        
        system_prompt = """You are a senior cardiac care triage nurse with 15+ years of experience in post-operative monitoring.
        Analyze patient biometric data and comprehensive medical history to determine appropriate care actions.
        Use the provided medical history and pain diary data to inform your decision-making.
        
        Provide response in this exact JSON format:
        {
            "action": "contact_emergency_services|notify_physician|no_action",
            "priority": "immediate|high|medium|low",
            "summary": "brief summary",
            "rationale": "detailed reasoning",
            "followups": ["action1", "action2"],
            "emergency_flags": ["flag1", "flag2"],
            "requires_immediate_action": true/false
        }
        
        DECISION FACTORS:
        1. Biometric Analysis: Use current vital signs and trends
        2. Medical History: Consider past conditions, procedures, and medications
        3. Pain Diary: Evaluate pain patterns and patient-reported symptoms
        4. Risk Assessment: Combine all factors for comprehensive evaluation
        
        CRITICAL GUIDELINES:
        - If biometrics show "critical" risk → priority MUST be "immediate" or "high"
        - If biometrics require_attention → next action MUST address the concern
        - If pain diary shows worsening trends → consider escalating priority
        - If medical history shows relevant conditions → factor into decision
        - If biometrics show "high" risk → consider escalating priority"""
        
        analysis_summary = f"""
        Biometric Analysis: {biometric_analysis.description}
        Risk Assessment: {biometric_analysis.risk_assessment}
        Immediate Concerns: {biometric_analysis.immediate_concerns}
        Recommendations: {biometric_analysis.recommendations}
        
        Patient Context: {patient_context}
        Pain Diary Entries: {len(pain_diary)} entries
        Weight Data Points: {len(weight_data)} measurements
        """
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Make triage decision based on this data:\n\n{analysis_summary}")
        ]
        
        response = llm.invoke(messages)
        response_content = response.content if hasattr(response, 'content') else str(response)
        
        # Track tokens used
        tokens_used = state.get("tokens_used", 0)
        if hasattr(response, 'usage') and response.usage:
            tokens_used += response.usage.total_tokens
        else:
            # Estimate tokens if usage not available
            estimated_tokens = len(response_content.split()) * 1.3  # Rough estimate
            tokens_used += int(estimated_tokens)
        
        # Parse JSON response
        import re
        json_match = re.search(r'\{.*\}', response_content, re.DOTALL)
        if json_match:
            result_data = json.loads(json_match.group())
            triage_decision = DecisionPayload(**result_data)
        else:
            # Fallback triage decision
            triage_decision = DecisionPayload(
                action="notify_physician" if biometric_analysis.requires_attention else "no_action",
                priority="immediate" if biometric_analysis.requires_attention else "low",
                summary=f"Patient status: {biometric_analysis.risk_assessment} risk",
                rationale="Based on biometric analysis",
                followups=biometric_analysis.recommendations,
                emergency_flags=biometric_analysis.immediate_concerns,
                requires_immediate_action=biometric_analysis.requires_attention
            )
        
        return {
            **state,
            "triage_decision": triage_decision,
            "tokens_used": tokens_used,
            "current_step": state.get("current_step", 0) + 1,
            "tool_calls": state.get("tool_calls", 0) + 1,  # 1 LLM call for triage decision
            "error": None,
            "progress": 80,
            "status": "triage_decision_made",
            "events": state.get("events", []) + [{
                "timestamp": datetime.now().isoformat(),
                "type": "triage_decision_made",
                "message": f"Step {state.get('current_step', 0) + 1}: Triage decision: {triage_decision.action}"
            }]
        }
    except Exception as e:
        return {
            **state,
            "error": f"Failed to make triage decision: {e}",
            "status": "error"
        }

def log_writer_step(state: LangGraphState) -> LangGraphState:
    """Log writer agent - creates final medical log."""
    if state.get("error") or not state.get("triage_decision"):
        return state
    
    try:
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.1)
        
        # Create findings from biometric analysis
        biometric_analysis = state["biometric_analysis"]
        findings = [
            Finding(
                title="Biometric Status",
                summary=biometric_analysis.description,
                support_score=biometric_analysis.support_score,
                confidence_level=biometric_analysis.confidence_level,
                risk_level=biometric_analysis.risk_assessment
            )
        ]
        
        # Create recommendations from triage decision
        triage_decision = state["triage_decision"]
        recommendations = [
            Recommendation(
                text=followup,
                priority=triage_decision.priority,
                rationale=triage_decision.rationale,
                support_score=0.85,
                confidence_level="high"
            )
            for followup in triage_decision.followups
        ]
        
        # Create medical log
        medical_log = AgenticFinalOutput(
            success=True,
            run_id=state["run_id"],
            framework="langgraph",
            patient=PatientIdentity(
                name=state["patient_name"],
                id=f"patient_{state['patient_name'].lower()}"
            ),
            started_at=state["events"][0]["timestamp"] if state["events"] else datetime.now().isoformat(),
            completed_at=datetime.now().isoformat(),
            summary=f"Patient {state['patient_name']} analysis completed",
            triage_decision=triage_decision,
            findings=findings,
            recommendations=recommendations,
            metrics=ExecutionMetrics(
                duration_ms=int((datetime.now() - datetime.fromisoformat(state["events"][0]["timestamp"])).total_seconds() * 1000) if state["events"] else 0,
                tokens_used=state.get("tokens_used", 0),
                tool_calls=state.get("tool_calls", 0),
                steps_completed=len(state["events"])
            ),
            artifacts=Artifacts(
                log_file=f"patient/agentic_monitor_logs/execution_log_{state['run_id']}_{state['patient_name']}.json"
            )
        )
        
        return {
            **state,
            "medical_log": medical_log,
            "current_step": state.get("current_step", 0) + 1,
            "tool_calls": state.get("tool_calls", 0) + 0,  # No LLM calls in this step
            "error": None,
            "progress": 100,
            "status": "completed",
            "events": state.get("events", []) + [{
                "timestamp": datetime.now().isoformat(),
                "type": "medical_log_created",
                "message": f"Step {state.get('current_step', 0) + 1}: Medical log created successfully"
            }]
        }
    except Exception as e:
        return {
            **state,
            "error": f"Failed to create medical log: {e}",
            "status": "error"
        }

def should_continue(state: LangGraphState) -> str:
    """Determine if workflow should continue or end due to error."""
    if state.get("error"):
        return "end"
    return "continue"

def create_patient_monitoring_graph():
    """Create the patient monitoring workflow."""
    workflow = StateGraph(LangGraphState)
    
    # Add nodes
    workflow.add_node("load_biometric_data", load_biometric_data_step)
    workflow.add_node("biometric_reviewer", biometric_reviewer_step)
    workflow.add_node("load_patient_data", load_patient_data_step)
    workflow.add_node("triage_nurse", triage_nurse_step)
    workflow.add_node("log_writer", log_writer_step)
    
    # Add edges with conditional logic
    workflow.add_edge(START, "load_biometric_data")
    workflow.add_conditional_edges("load_biometric_data", should_continue, {
        "continue": "biometric_reviewer",
        "end": END
    })
    workflow.add_conditional_edges("biometric_reviewer", should_continue, {
        "continue": "load_patient_data",
        "end": END
    })
    workflow.add_conditional_edges("load_patient_data", should_continue, {
        "continue": "triage_nurse",
        "end": END
    })
    workflow.add_conditional_edges("triage_nurse", should_continue, {
        "continue": "log_writer",
        "end": END
    })
    workflow.add_edge("log_writer", END)
    
    return workflow.compile()

def run_patient_monitoring(patient_name: str, run_id: str, timestamp: Optional[str] = None) -> Dict[str, Any]:
    """Run the patient monitoring workflow."""
    try:
        app = create_patient_monitoring_graph()
        
        initial_state: LangGraphState = {
            "biometric_data": [],
            "biometric_analysis": None,
            "pain_diary_data": [],
            "weight_data": [],
            "fhir_records": {},
            "patient_context": {},
            "triage_decision": None,
            "medical_log": None,
            "run_id": run_id,
            "patient_name": patient_name,
            "error": None,
            "progress": 0,
            "status": "starting",
            "events": [],
            "tokens_used": 0,
            "current_step": 0,
            "tool_calls": 0
        }
        
        result = app.invoke(initial_state)
        
        # Debug: Print the result to understand what was generated
        # print(f"🔍 LangGraph workflow result keys: {list(result.keys())}")
        # print(f"🔍 Biometric analysis present: {result.get('biometric_analysis') is not None}")
        # print(f"🔍 Triage decision present: {result.get('triage_decision') is not None}")
        # print(f"🔍 Medical log present: {result.get('medical_log') is not None}")
        # print(f"🔍 Error present: {result.get('error') is not None}")
        if result.get('error'):
            print(f"❌ Workflow error: {result.get('error')}")
        
        # Generate output files
        if timestamp:
            # Use provided timestamp
            file_timestamp = timestamp
        else:
            # Generate new timestamp
            file_timestamp = datetime.now().strftime('%Y_%m_%d_%H_%M')
        
        # Use absolute path to ensure files are created in the correct location
        workspace_root = Path(__file__).parent.parent.parent
        logs_dir = workspace_root / "patient" / "agentic_monitor_logs"
        logs_dir.mkdir(exist_ok=True)
        
        # Format patient name to match expected naming convention (title case)
        formatted_patient_name = patient_name.title() if patient_name else "Unknown"
        
        # Debug: file creation
        # print(f"📁 Creating output files in: {logs_dir}")
        # print(f"📝 Using formatted patient name: {formatted_patient_name}")
        
        # Biometric analysis file
        if result.get("biometric_analysis"):
            biometric_file = logs_dir / f"{file_timestamp}_{formatted_patient_name}_biometric_analysis.json"
            try:
                with open(biometric_file, 'w') as f:
                    json.dump(result["biometric_analysis"].dict(), f, indent=2, default=str)
                # print(f"✅ Created biometric analysis file: {biometric_file.name}")
            except Exception as e:
                print(f"❌ Error creating biometric analysis file: {e}")
        
        # Triage decision file
        if result.get("triage_decision"):
            triage_file = logs_dir / f"{file_timestamp}_{formatted_patient_name}_triage_decision.json"
            try:
                with open(triage_file, 'w') as f:
                    json.dump(result["triage_decision"].dict(), f, indent=2, default=str)
                # print(f"✅ Created triage decision file: {triage_file.name}")
            except Exception as e:
                print(f"❌ Error creating triage decision file: {e}")
        
        # Medical log file
        if result.get("medical_log"):
            medical_file = logs_dir / f"{file_timestamp}_{formatted_patient_name}_medical_log.json"
            try:
                with open(medical_file, 'w') as f:
                    json.dump(result["medical_log"].dict(), f, indent=2, default=str)
                # print(f"✅ Created medical log file: {medical_file.name}")
            except Exception as e:
                print(f"❌ Error creating medical log file: {e}")
        
        return {
            "success": True,
            "result": result,
            "run_id": run_id,
            "patient_name": patient_name,
            "framework": "langgraph"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "run_id": run_id,
            "patient_name": patient_name,
            "framework": "langgraph"
        }
