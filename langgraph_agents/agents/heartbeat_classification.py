import json
import numpy as np
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, TypedDict
from pydantic import BaseModel
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
import os
import time
import json as _json
from datetime import datetime as _dt
import uuid as _uuid
from utils.logging_utils import log_llm_metadata

# Pydantic models for heartbeat data
class HeartbeatRecord(BaseModel):
    timestamp: datetime
    interval_ms: int

class HeartbeatAnalysis(BaseModel):
    total_heartbeats: int
    avg_heart_rate_bpm: float
    min_heart_rate_bpm: float
    max_heart_rate_bpm: float
    heart_rate_variability: float
    avg_interval_ms: float
    duration_seconds: float
    start_time: str
    end_time: str

class ClassificationResult(BaseModel):
    classification: str  # "normal", "critical", or "irregular"
    confidence: float
    reasoning: str
    key_metrics: Dict[str, float]
    recommendations: List[str]

# State for the Langgraph workflow
class AgentState(TypedDict):
    heartbeat_data: List[Dict]
    analysis: Optional[HeartbeatAnalysis]
    classification: Optional[ClassificationResult]
    error: Optional[str]

def estimate_tokens(text):
    # Rough estimate: 1 token ≈ 4 characters (for OpenAI models)
    return max(1, len(text) // 4)

def load_heartbeat_data() -> List[Dict]:
    """Load heartbeat data from the buffer file."""
    buffer_file = Path("patient/biometric/buffer/pulse_temp.json")
    #buffer_file = Path("patient/biometric/pulse/demo_stream_source/normal.json")
    
    if not buffer_file.exists():
        raise FileNotFoundError(f"Heartbeat buffer file not found: {buffer_file}")
    
    try:
        with open(buffer_file, 'r') as f:
            data = json.load(f)
        
        if not isinstance(data, list):
            raise ValueError("Invalid data format: expected list of heartbeat records")
        
        return data
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in heartbeat buffer: {e}")

def analyze_heartbeat_data(heartbeat_data: List[Dict]) -> HeartbeatAnalysis:
    """Analyze heartbeat data and calculate key metrics."""
    if not heartbeat_data:
        raise ValueError("No heartbeat data provided")
    
    # Convert to HeartbeatRecord objects
    records = []
    for record in heartbeat_data:
        if isinstance(record['timestamp'], str):
            # Parse timestamp string to datetime
            timestamp_str = record['timestamp'].replace('Z', '+00:00') if 'Z' in record['timestamp'] else record['timestamp']
            record['timestamp'] = datetime.fromisoformat(timestamp_str)
        records.append(HeartbeatRecord(**record))
    
    # Calculate intervals and heart rates
    intervals = [record.interval_ms for record in records]
    heart_rates = [60000 / interval for interval in intervals if interval > 0]  # Convert to BPM
    
    if not heart_rates:
        raise ValueError("No valid heart rate data found")
    
    # Calculate statistics
    avg_heart_rate = sum(heart_rates) / len(heart_rates)
    min_heart_rate = min(heart_rates)
    max_heart_rate = max(heart_rates)
    heart_rate_variability = float(np.std(heart_rates) if len(heart_rates) > 1 else 0)
    avg_interval = sum(intervals) / len(intervals)
    
    # Calculate time range
    start_time = min(record.timestamp for record in records)
    end_time = max(record.timestamp for record in records)
    duration_seconds = (end_time - start_time).total_seconds()
    
    return HeartbeatAnalysis(
        total_heartbeats=len(records),
        avg_heart_rate_bpm=round(avg_heart_rate, 1),
        min_heart_rate_bpm=round(min_heart_rate, 1),
        max_heart_rate_bpm=round(max_heart_rate, 1),
        heart_rate_variability=round(heart_rate_variability, 2),
        avg_interval_ms=round(avg_interval, 1),
        duration_seconds=round(duration_seconds, 1),
        start_time=start_time.isoformat(),
        end_time=end_time.isoformat()
    )

def classify_heartbeat(analysis: HeartbeatAnalysis) -> ClassificationResult:
    """Use LLM to classify heartbeat patterns."""
    # Initialize LLM (you'll need to set OPENAI_API_KEY environment variable)
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.1
    )
    # Create system prompt for medical classification
    system_prompt = """You are a medical AI assistant specializing in cardiac rhythm analysis. \
    Your task is to classify heartbeat patterns based on the provided metrics.\n\n    Classification criteria:\n    - NORMAL\n    - IRREGULAR\n    - CRITICAL\n\n    Provide your response in this exact JSON format:\n    {\n        \"classification\": \"normal|irregular|critical\",\n        \"confidence\": 0.0-1.0,\n        \"reasoning\": \"detailed explanation\",\n        \"key_metrics\": {\"metric_name\": value},\n        \"recommendations\": [\"action1\", \"action2\"]\n    }\n    """
    # Create analysis summary for the LLM
    analysis_summary = f"""
    Heartbeat Analysis Summary:
    - Total heartbeats: {analysis.total_heartbeats}
    - Average heart rate: {analysis.avg_heart_rate_bpm} BPM
    - Min heart rate: {analysis.min_heart_rate_bpm} BPM
    - Max heart rate: {analysis.max_heart_rate_bpm} BPM
    - Heart rate variability: {analysis.heart_rate_variability}
    - Average interval: {analysis.avg_interval_ms} ms
    - Duration: {analysis.duration_seconds} seconds
    - Time period: {analysis.start_time} to {analysis.end_time}
    """
    # Get LLM classification
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"Please classify this heartbeat pattern:\n\n{analysis_summary}")
    ]
    # Estimate prompt tokens
    prompt_tokens = sum(estimate_tokens(m.content) for m in messages)
    start = time.time()
    response = llm.invoke(messages)
    elapsed = time.time() - start
    # Estimate completion tokens
    response_content = response.content if hasattr(response, 'content') else str(response)
    if not isinstance(response_content, str):
        response_content = str(response_content)
    completion_tokens = estimate_tokens(response_content)
    # Log metadata
    log_llm_metadata(
        provider="OpenAI",
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": analysis_summary}],
        response=response_content,
        elapsed=elapsed,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens
    )
    try:
        # Parse the JSON response
        import re
        json_match = re.search(r'\{.*\}', response_content, re.DOTALL)
        if json_match:
            result_data = json.loads(json_match.group())
        else:
            raise ValueError("No JSON found in response")
        return ClassificationResult(**result_data)
    except Exception as e:
        # Fallback classification based on rules if LLM fails
        print(f"LLM classification failed: {e}. Using rule-based fallback.")
        return rule_based_classification(analysis)

def rule_based_classification(analysis: HeartbeatAnalysis) -> ClassificationResult:
    """Fallback rule-based classification if LLM fails."""
    avg_hr = analysis.avg_heart_rate_bpm
    hr_variability = analysis.heart_rate_variability
    min_hr = analysis.min_heart_rate_bpm
    max_hr = analysis.max_heart_rate_bpm
    # Rule-based classification
    if avg_hr < 50 or avg_hr > 120 or min_hr < 40 or max_hr > 140:
        classification = "critical"
        confidence = 0.9
        reasoning = f"Critical heart rate detected: average {avg_hr} BPM, range {min_hr}-{max_hr} BPM"
        recommendations = ["Immediate medical attention required", "Check patient vitals", "Consider emergency protocols"]
    elif hr_variability > 15 or abs(max_hr - min_hr) > 30:
        classification = "irregular"
        confidence = 0.8
        reasoning = f"Irregular heart rate variability: {hr_variability}, range {min_hr}-{max_hr} BPM"
        recommendations = ["Monitor closely", "Check for arrhythmia", "Consider ECG"]
    else:
        classification = "normal"
        confidence = 0.85
        reasoning = f"Normal heart rate pattern: average {avg_hr} BPM, low variability {hr_variability}"
        recommendations = ["Continue monitoring", "Document baseline"]
    return ClassificationResult(
        classification=classification,
        confidence=confidence,
        reasoning=reasoning,
        key_metrics={
            "avg_heart_rate": avg_hr,
            "heart_rate_variability": hr_variability,
            "min_heart_rate": min_hr,
            "max_heart_rate": max_hr
        },
        recommendations=recommendations
    ) 