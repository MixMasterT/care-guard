"""
Shared Pydantic models for agentic framework inputs, streaming step updates, and final outputs.
These types are framework-agnostic and reused across CrewAI, LangGraph, and future solutions.
"""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field

# Reuse existing biometric event types (avoid duplication)
from patient.biometric_types import BiometricEvent


# ---------- Confidence & evidence ----------

ConfidenceLevel = Literal["low", "medium", "high", "very_high"]


class ConfidenceLevelEvidence(BaseModel):
    consensus_ratio: Optional[float] = None  # e.g., 0.7 for 7/10 agreement
    validators_passed: Optional[int] = None
    validators_total: Optional[int] = None
    evidence_coverage: Optional[Dict[str, Any]] = None  # e.g., data windows, recency
    references: List[str] = Field(default_factory=list)  # brief evidence strings/ids
    notes: Optional[str] = None


# ---------- Core output types ----------


class Finding(BaseModel):
    title: str
    summary: str
    details: Optional[Dict[str, Any]] = None
    support_score: Optional[float] = None
    confidence_level: Optional[ConfidenceLevel] = None
    confidence_level_evidence: Optional[ConfidenceLevelEvidence] = None
    risk_level: Optional[Literal["low", "moderate", "high", "critical"]] = None


class Recommendation(BaseModel):
    text: str
    priority: Optional[Literal["low", "medium", "high", "immediate"]] = None
    rationale: Optional[str] = None
    support_score: Optional[float] = None
    confidence_level: Optional[ConfidenceLevel] = None
    confidence_level_evidence: Optional[ConfidenceLevelEvidence] = None


class DecisionPayload(BaseModel):
    action: str  # e.g., "contact_emergency_services", "notify_physician", "no_action"
    priority: Optional[Literal["immediate", "high", "medium", "low"]] = None
    summary: Optional[str] = None
    rationale: Optional[str] = None
    followups: List[str] = Field(default_factory=list)
    
    # Enhanced fields for emergency situations
    emergency_flags: List[str] = Field(default_factory=list)  # e.g., ["critical_bradycardia", "severe_hypoxemia"]
    requires_immediate_action: bool = False  # Flag for urgent intervention


class TrendInsightPayload(BaseModel):
    metric: Literal["heart_rate", "spo2", "blood_pressure", "respiration", "ecg"] | str
    description: str
    window: Optional[str] = None
    stats: Dict[str, Any] = Field(default_factory=dict)
    support_score: Optional[float] = None
    confidence_level: Optional[ConfidenceLevel] = None
    confidence_level_evidence: Optional[ConfidenceLevelEvidence] = None
    
    # Enhanced fields for actionable biometric insights
    risk_assessment: Optional[Literal["low", "moderate", "high", "critical"]] = None
    immediate_concerns: List[str] = Field(default_factory=list)  # e.g., ["bradycardia", "hypoxemia"]
    recommendations: List[str] = Field(default_factory=list)  # e.g., ["check patient immediately", "contact physician"]
    requires_attention: bool = False  # Flag for urgent review
    next_action: Optional[str] = None  # Immediate next step


# ---------- Supporting types ----------


FrameworkId = Literal["crewai", "langgraph", "unknown"]


class PatientIdentity(BaseModel):
    name: str
    id: str
    fhir_file: Optional[str] = None
    gender: Optional[str] = None
    birth_date: Optional[str] = None


class ExecutionMetrics(BaseModel):
    duration_ms: Optional[int] = None
    tokens_used: Optional[int] = None
    tool_calls: Optional[int] = None
    steps_completed: Optional[int] = None


class Artifacts(BaseModel):
    log_file: Optional[str] = None
    live_output_path: Optional[str] = None
    output_lines: List[str] = []
    raw_output: Optional[str] = None
    context_snapshot_path: Optional[str] = None
    framework_specific: Dict[str, Any] = Field(default_factory=dict)


# ---------- Final output ----------


class AgenticFinalOutput(BaseModel):
    success: bool
    run_id: str
    framework: FrameworkId
    patient: PatientIdentity
    started_at: str
    completed_at: Optional[str] = None
    summary: Optional[str] = None
    triage_decision: Optional[DecisionPayload] = None
    findings: List[Finding] = []
    recommendations: List[Recommendation] = []
    metrics: ExecutionMetrics = ExecutionMetrics()
    artifacts: Artifacts = Artifacts()
    error: Optional[str] = None


