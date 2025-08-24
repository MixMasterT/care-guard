"""
Patient Monitoring Workflow for LangGraph
Replicates CrewAI functionality with three agents: biometric_reviewer, triage_nurse, and log_writer.
"""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, TypedDict, List
from langgraph.graph import StateGraph, START, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Import Pydantic models for structured output
from agentic_types.models import (
    TrendInsightPayload, DecisionPayload, AgenticFinalOutput,
    Finding, Recommendation, PatientIdentity, ExecutionMetrics, Artifacts
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
            "error": None,
            "progress": 20,
            "status": "biometric_data_loaded",
            "events": state.get("events", []) + [{
                "timestamp": datetime.now().isoformat(),
                "type": "biometric_data_loaded",
                "message": f"Loaded {len(biometric_data)} biometric records"
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
            if 'heart_rate' in record:
                heart_rates.append(record['heart_rate'])
            if 'spo2' in record:
                spo2_values.append(record['spo2'])
            if 'blood_pressure' in record:
                bp = record['blood_pressure']
                if isinstance(bp, dict):
                    blood_pressures.append(bp)
            if 'respiration_rate' in record:
                respiration_rates.append(record['respiration_rate'])
            if 'temperature' in record:
                temperatures.append(record['temperature'])
        
        # Calculate basic statistics
        stats = {}
        if heart_rates:
            stats['heart_rate'] = {
                'avg': round(sum(heart_rates) / len(heart_rates), 1),
                'min': round(min(heart_rates), 1),
                'max': round(max(heart_rates), 1),
                'count': len(heart_rates)
            }
        if spo2_values:
            stats['spo2'] = {
                'avg': round(sum(spo2_values) / len(spo2_values), 1),
                'min': round(min(spo2_values), 1),
                'max': round(max(spo2_values), 1),
                'count': len(spo2_values)
            }
        
        system_prompt = """You are an experienced technical expert in real-time patient monitoring and interpreting time-series biosignals.
        Review live and recent biometric signals to extract concise observations and identify any immediate risks.
        Provide concise summaries and highlight anomalies only.
        
        Provide response in this exact JSON format:
        {
            "metric": "comprehensive_biometrics",
            "description": "brief summary of what the data shows",
            "window": "Recent monitoring period",
            "stats": {"heart_rate": {...}, "spo2": {...}},
            "support_score": 0.85,
            "confidence_level": "high",
            "risk_assessment": "low|moderate|high|critical",
            "immediate_concerns": ["concern1", "concern2"],
            "recommendations": ["action1", "action2"],
            "requires_attention": true/false,
            "next_action": "immediate next step"
        }
        
        RISK ASSESSMENT GUIDELINES:
        - LOW: All values within normal ranges, stable trends
        - MODERATE: Some values outside normal ranges, minor fluctuations  
        - HIGH: Multiple values outside normal ranges, concerning trends
        - CRITICAL: Values in dangerous ranges, rapid changes
        
        EMERGENCY FLAGS:
        - Heart rate < 50 or > 120 bpm → critical
        - SpO2 < 90% → critical
        - Blood pressure < 90/60 or > 180/110 → high"""
        
        analysis_summary = f"""
        Biometric Data Summary:
        Heart Rate: {stats.get('heart_rate', {})}
        SpO2: {stats.get('spo2', {})}
        Blood Pressure Records: {len(blood_pressures)}
        Respiration Records: {len(respiration_rates)}
        Temperature Records: {len(temperatures)}
        Total Records: {len(biometric_data)}
        """
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Analyze this biometric data:\n\n{analysis_summary}")
        ]
        
        response = llm.invoke(messages)
        response_content = response.content if hasattr(response, 'content') else str(response)
        
        # Parse JSON response
        import re
        json_match = re.search(r'\{.*\}', response_content, re.DOTALL)
        if json_match:
            result_data = json.loads(json_match.group())
            biometric_analysis = TrendInsightPayload(**result_data)
        else:
            # Fallback analysis
            hr_avg = stats.get('heart_rate', {}).get('avg', 0)
            spo2_avg = stats.get('spo2', {}).get('avg', 0)
            
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
            "error": None,
            "progress": 40,
            "status": "biometrics_analyzed",
            "events": state.get("events", []) + [{
                "timestamp": datetime.now().isoformat(),
                "type": "biometrics_analyzed",
                "message": f"Biometric analysis completed - {biometric_analysis.risk_assessment} risk level"
            }]
        }
    except Exception as e:
        return {
            **state,
            "error": f"Failed to analyze biometrics: {e}",
            "status": "error"
        }

def load_patient_data_step(state: LangGraphState) -> LangGraphState:
    """Load patient data files."""
    if state.get("error"):
        return state
    
    try:
        workspace_root = Path(__file__).parent.parent.parent
        patient_name = state["patient_name"]
        
        # Load pain diary
        pain_file = workspace_root / "patient" / "generated_medical_records" / "pain_diaries" / f"{patient_name.lower()}.json"
        pain_diary_data = []
        if pain_file.exists():
            with open(pain_file, 'r') as f:
                pain_diary_data = json.load(f)
        
        # Load weight data
        weight_file = workspace_root / "patient" / "biometric" / "weight" / f"{patient_name.lower()}.json"
        weight_data = []
        if weight_file.exists():
            with open(weight_file, 'r') as f:
                weight_data = json.load(f)
        
        # Load FHIR records
        fhir_records = {}
        fhir_dir = workspace_root / "patient" / "generated_medical_records" / "fhir"
        if fhir_dir.exists():
            for fhir_file in fhir_dir.glob("*.json"):
                if patient_name.lower() in fhir_file.name.lower():
                    with open(fhir_file, 'r') as f:
                        fhir_records = json.load(f)
                    break
        
        # Load patient context using AgenticPatientDataLoader if available
        try:
            from patient.agentic_data_loader import AgenticPatientDataLoader
            data_loader = AgenticPatientDataLoader(patient_name, workspace_root / 'patient')
            patient_context = data_loader.get_agent_specific_context("care_coordination", max_tokens=15000)
        except ImportError:
            patient_context = f"Patient {patient_name} - basic context"
        
        return {
            **state,
            "pain_diary_data": pain_diary_data,
            "weight_data": weight_data,
            "fhir_records": fhir_records,
            "patient_context": patient_context,
            "error": None,
            "progress": 60,
            "status": "patient_data_loaded",
            "events": state.get("events", []) + [{
                "timestamp": datetime.now().isoformat(),
                "type": "patient_data_loaded",
                "message": f"Loaded patient data for {patient_name}"
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
        Analyze patient biometric data and medical history to determine appropriate care actions.
        Only report findings that you can verify from the actual data files.
        
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
        
        CRITICAL: Use the biometric analysis to inform your triage decision.
        - If biometrics show "critical" risk → priority MUST be "immediate" or "high"
        - If biometrics require_attention → next action MUST address the concern
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
            "error": None,
            "progress": 80,
            "status": "triage_decision_made",
            "events": state.get("events", []) + [{
                "timestamp": datetime.now().isoformat(),
                "type": "triage_decision_made",
                "message": f"Triage decision: {triage_decision.action}"
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
                steps_completed=len(state["events"])
            ),
            artifacts=Artifacts(
                log_file=f"patient/agentic_monitor_logs/execution_log_{state['run_id']}_{state['patient_name']}.json"
            )
        )
        
        return {
            **state,
            "medical_log": medical_log,
            "error": None,
            "progress": 100,
            "status": "completed",
            "events": state.get("events", []) + [{
                "timestamp": datetime.now().isoformat(),
                "type": "medical_log_created",
                "message": "Medical log created successfully"
            }]
        }
    except Exception as e:
        return {
            **state,
            "error": f"Failed to create medical log: {e}",
            "status": "error"
        }

def create_patient_monitoring_graph():
    """Create the patient monitoring workflow."""
    workflow = StateGraph(LangGraphState)
    
    # Add nodes
    workflow.add_node("load_biometric_data", load_biometric_data_step)
    workflow.add_node("biometric_reviewer", biometric_reviewer_step)
    workflow.add_node("load_patient_data", load_patient_data_step)
    workflow.add_node("triage_nurse", triage_nurse_step)
    workflow.add_node("log_writer", log_writer_step)
    
    # Add edges
    workflow.add_edge(START, "load_biometric_data")
    workflow.add_edge("load_biometric_data", "biometric_reviewer")
    workflow.add_edge("biometric_reviewer", "load_patient_data")
    workflow.add_edge("load_patient_data", "triage_nurse")
    workflow.add_edge("triage_nurse", "log_writer")
    workflow.add_edge("log_writer", END)
    
    return workflow.compile()

def run_patient_monitoring(patient_name: str, run_id: str) -> Dict[str, Any]:
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
            "events": []
        }
        
        result = app.invoke(initial_state)
        
        # Generate output files
        timestamp = datetime.now().strftime('%Y_%m_%d_%H_%M')
        logs_dir = Path("patient/agentic_monitor_logs")
        logs_dir.mkdir(exist_ok=True)
        
        # Biometric analysis file
        if result.get("biometric_analysis"):
            biometric_file = logs_dir / f"{timestamp}_{run_id}_{patient_name}_biometric_analysis.json"
            with open(biometric_file, 'w') as f:
                json.dump(result["biometric_analysis"].dict(), f, indent=2, default=str)
        
        # Triage decision file
        if result.get("triage_decision"):
            triage_file = logs_dir / f"{timestamp}_{run_id}_{patient_name}_triage_decision.json"
            with open(triage_file, 'w') as f:
                json.dump(result["triage_decision"].dict(), f, indent=2, default=str)
        
        # Medical log file
        if result.get("medical_log"):
            medical_file = logs_dir / f"{timestamp}_{run_id}_{patient_name}_medical_log.json"
            with open(medical_file, 'w') as f:
                json.dump(result["medical_log"].dict(), f, indent=2, default=str)
        
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
