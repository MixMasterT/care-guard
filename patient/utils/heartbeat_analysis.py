import json
import numpy as np
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional
from pydantic import BaseModel

# Pydantic model for heartbeat records
class HeartbeatRecord(BaseModel):
    timestamp: datetime
    interval_ms: int
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

def ensure_biometric_buffer_dir():
    """Ensure the biometric buffer directory exists."""
    buffer_dir = Path(__file__).parent.parent / "biometric" / "buffer"
    buffer_dir.mkdir(parents=True, exist_ok=True)
    return buffer_dir

def analyze_heartbeat_data() -> Optional[Dict]:
    """Analyze the current heartbeat buffer and return summary statistics."""
    try:
        buffer_dir = ensure_biometric_buffer_dir()
        pulse_temp_file = buffer_dir / "pulse_temp.json"
        
        if not pulse_temp_file.exists():
            return None
        
        with open(pulse_temp_file, 'r') as f:
            records = json.load(f)
        
        if not records:
            return None
        
        # Convert records back to HeartbeatRecord objects for analysis
        heartbeat_records = []
        for record in records:
            # Parse timestamp back to datetime
            if isinstance(record['timestamp'], str):
                record['timestamp'] = datetime.fromisoformat(record['timestamp'].replace('Z', '+00:00'))
            heartbeat_records.append(HeartbeatRecord(**record))
        
        # Calculate statistics
        intervals = [record.interval_ms for record in heartbeat_records]
        heart_rates = [60000 / interval for interval in intervals if interval > 0]  # Convert to BPM
        
        if not heart_rates:
            return None
        
        # Calculate summary statistics
        avg_heart_rate = sum(heart_rates) / len(heart_rates)
        min_heart_rate = min(heart_rates)
        max_heart_rate = max(heart_rates)
        
        # Calculate heart rate variability (standard deviation)
        heart_rate_variability = np.std(heart_rates) if len(heart_rates) > 1 else 0
        
        # Determine time range
        start_time = min(record.timestamp for record in heartbeat_records)
        end_time = max(record.timestamp for record in heartbeat_records)
        duration_seconds = (end_time - start_time).total_seconds()
        
        summary = {
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "duration_seconds": duration_seconds,
            "total_heartbeats": len(heartbeat_records),
            "avg_heart_rate_bpm": round(avg_heart_rate, 1),
            "min_heart_rate_bpm": round(min_heart_rate, 1),
            "max_heart_rate_bpm": round(max_heart_rate, 1),
            "heart_rate_variability": round(heart_rate_variability, 2),
            "avg_interval_ms": round(sum(intervals) / len(intervals), 1)
        }
        
        return summary
        
    except Exception as e:
        print(f"❌ Error analyzing heartbeat data: {e}")
        import traceback
        traceback.print_exc()
        return None 