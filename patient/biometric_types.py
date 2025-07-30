#!/usr/bin/env python3
"""
Pydantic type definitions for biometric events used in the patient monitoring system.
"""

from pydantic import BaseModel, Field
from typing import Optional, Union, Literal
from datetime import datetime

# Event type literals
EventType = Literal[
    "heartbeat",      # Discrete heartbeat events
    "respiration",    # Discrete respiration events (breath completion)
    "spo2",          # Continuous SpO2 measurements
    "temperature",    # Continuous temperature measurements
    "ecg_rhythm",    # Continuous ECG rhythm data
    "blood_pressure"  # Continuous blood pressure data
]

class BaseBiometricEvent(BaseModel):
    """Base class for all biometric events."""
    event_type: EventType
    timestamp: datetime = Field(description="ISO format timestamp when the event occurred")
    scenario: Optional[str] = Field(None, description="Scenario type (normal, irregular, critical)")

class HeartbeatEvent(BaseBiometricEvent):
    """Discrete heartbeat event representing a single heartbeat."""
    event_type: Literal["heartbeat"] = "heartbeat"
    interval_ms: int = Field(description="Time interval since last heartbeat in milliseconds")
    pulse_strength: float = Field(description="Strength/intensity of the pulse (0.0-2.0)")

class RespirationEvent(BaseBiometricEvent):
    """Discrete respiration event representing the completion of a breath."""
    event_type: Literal["respiration"] = "respiration"
    interval_ms: int = Field(description="Time interval since last breath in milliseconds")

class SpO2Event(BaseBiometricEvent):
    """Continuous SpO2 measurement event."""
    event_type: Literal["spo2"] = "spo2"
    spo2: int = Field(description="SpO2 percentage (0-100)")

class TemperatureEvent(BaseBiometricEvent):
    """Continuous temperature measurement event."""
    event_type: Literal["temperature"] = "temperature"
    temperature: float = Field(description="Temperature in Celsius")

class ECGRhythmEvent(BaseBiometricEvent):
    """Continuous ECG rhythm data event."""
    event_type: Literal["ecg_rhythm"] = "ecg_rhythm"
    ecg_rhythm: str = Field(description="ECG rhythm type (e.g., NSR, AF, VT)")

class BloodPressureEvent(BaseBiometricEvent):
    """Continuous blood pressure measurement event."""
    event_type: Literal["blood_pressure"] = "blood_pressure"
    systolic: int = Field(description="Systolic blood pressure (mmHg)")
    diastolic: int = Field(description="Diastolic blood pressure (mmHg)")

# Union type for all biometric events
BiometricEvent = Union[
    HeartbeatEvent,
    RespirationEvent,
    SpO2Event,
    TemperatureEvent,
    ECGRhythmEvent,
    BloodPressureEvent
]

# Type aliases for convenience
class BiometricEventList(BaseModel):
    """List of biometric events."""
    events: list[BiometricEvent] = Field(default_factory=list)

# Validation functions
def validate_biometric_event(data: dict) -> BiometricEvent:
    """Validate and create a biometric event from a dictionary."""
    event_type = data.get("event_type")
    
    if event_type == "heartbeat":
        return HeartbeatEvent(**data)
    elif event_type == "respiration":
        return RespirationEvent(**data)
    elif event_type == "spo2":
        return SpO2Event(**data)
    elif event_type == "temperature":
        return TemperatureEvent(**data)
    elif event_type == "ecg_rhythm":
        return ECGRhythmEvent(**data)
    elif event_type == "blood_pressure":
        return BloodPressureEvent(**data)
    else:
        raise ValueError(f"Unknown event type: {event_type}")

def validate_biometric_events_list(events: list) -> bool:
    """Validate a list of biometric events."""
    try:
        for event in events:
            if event.get("event_type") == "heartbeat":
                HeartbeatEvent(**event)
            elif event.get("event_type") == "respiration":
                RespirationEvent(**event)
            elif event.get("event_type") == "spo2":
                SpO2Event(**event)
            elif event.get("event_type") == "temperature":
                TemperatureEvent(**event)
            elif event.get("event_type") == "ecg_rhythm":
                ECGRhythmEvent(**event)
            elif event.get("event_type") == "blood_pressure":
                BloodPressureEvent(**event)
        return True
    except Exception as e:
        print(f"❌ Validation error: {e}")
        return False

# Demo scenario file event types (for source files)
class DemoScenarioEvent(BaseModel):
    """Event structure for demo scenario source files."""
    type: str = Field(description="Event type from source file")
    offset_ms: int = Field(description="Time offset in milliseconds")
    value: Optional[Union[int, float, str]] = Field(default=None, description="Event value")
    interval_ms: Optional[int] = Field(default=None, description="Interval for discrete events")
    pulse_strength: Optional[float] = Field(default=None, description="Pulse strength for heartbeats")

class DemoScenarioFile(BaseModel):
    """Structure for demo scenario JSON files."""
    events: list[DemoScenarioEvent] = Field(default_factory=list)

def convert_demo_event_to_biometric_event(demo_event: DemoScenarioEvent, timestamp: datetime) -> Optional[BiometricEvent]:
    """Convert a demo scenario event to a biometric event."""
    event_type = demo_event.type
    
    if event_type == "heart_beat":
        return HeartbeatEvent(
            event_type="heartbeat",
            timestamp=timestamp,
            interval_ms=demo_event.interval_ms or 1000,
            pulse_strength=demo_event.pulse_strength or 1.0
        )
    elif event_type == "respiration":
        return RespirationEvent(
            event_type="respiration", 
            timestamp=timestamp,
            interval_ms=demo_event.interval_ms or 0
        )
    elif event_type == "spo2":
        return SpO2Event(
            event_type="spo2",
            timestamp=timestamp,
            spo2=demo_event.value or 0
        )
    elif event_type == "temperature":
        return TemperatureEvent(
            event_type="temperature",
            timestamp=timestamp,
            temperature=demo_event.value or 37.0
        )
    elif event_type == "ecg_rhythm":
        return ECGRhythmEvent(
            event_type="ecg_rhythm",
            timestamp=timestamp,
            ecg_rhythm=demo_event.value or "NSR"
        )
    else:
        print(f"Warning: Unknown demo event type: {event_type}")
        return None 