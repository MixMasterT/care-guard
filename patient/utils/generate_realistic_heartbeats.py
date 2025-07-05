#!/usr/bin/env python3
"""
Generate realistic heartbeat patterns for medical simulation.
Based on Cleveland Clinic heart rate and HRV information.
"""

# Future update -- provide a way to set the average instead of using 60 bpms as a baseline

import json
import random
import math
from pathlib import Path

def generate_normal_heartbeat(duration_seconds=300, base_interval=1000):
    """
    Generate normal heartbeat with natural HRV variations.
    Based on Cleveland Clinic: Normal resting HR 60-100 bpm with natural variability.
    """
    timestamps = [0]
    current_time = 0
    
    # Normal HRV: ±2-3% variation in healthy adults
    hrv_variation = 0.03  # 3% variation
    
    while current_time < duration_seconds * 1000:
        # Add natural HRV variation
        variation = random.uniform(-hrv_variation, hrv_variation)
        interval = base_interval * (1 + variation)
        
        # Ensure interval stays within reasonable bounds (50-120 bpm)
        interval = max(500, min(1200, interval))
        
        current_time += interval
        timestamps.append(int(current_time))
    
    return timestamps

def generate_irregular_heartbeat(duration_seconds=300, base_interval=1000):
    """
    Generate irregular heartbeat with arrhythmia characteristics.
    Based on Cleveland Clinic: Arrhythmias show irregular intervals and premature beats.
    """
    timestamps = [0]
    current_time = 0
    
    # Irregular patterns: premature beats, varying intervals, irregular rhythms
    patterns = [
        # Normal intervals with occasional premature beats
        lambda: random.uniform(900, 1100),
        # Premature beats (shorter intervals)
        lambda: random.uniform(400, 600),
        # Compensatory pauses (longer intervals after premature beats)
        lambda: random.uniform(1200, 1600),
        # Irregular intervals
        lambda: random.uniform(600, 1400)
    ]
    
    pattern_weights = [0.7, 0.1, 0.1, 0.1]  # 70% normal, 30% irregular
    
    while current_time < duration_seconds * 1000:
        # Choose pattern based on weights
        pattern = random.choices(patterns, weights=pattern_weights)[0]
        interval = pattern()
        
        # Add some additional randomness
        interval += random.uniform(-50, 50)
        
        # Ensure interval stays within reasonable bounds
        interval = max(300, min(2000, interval))
        
        current_time += interval
        timestamps.append(int(current_time))
    
    return timestamps

def main():
    """Generate realistic heartbeat patterns."""
    
    # Create output directory
    output_dir = Path("patient/biometric/pulse/demo_stream_source")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate normal heartbeat (60-100 bpm with natural HRV)
    print("Generating normal heartbeat pattern...")
    normal_timestamps = generate_normal_heartbeat(duration_seconds=300, base_interval=1000)
    
    with open(output_dir / "normal.json", "w") as f:
        json.dump(normal_timestamps, f, indent=2)
    
    print(f"Normal heartbeat: {len(normal_timestamps)} beats, avg interval: {1000:.0f}ms")
    
    # Generate irregular heartbeat (arrhythmia pattern)
    print("Generating irregular heartbeat pattern...")
    irregular_timestamps = generate_irregular_heartbeat(duration_seconds=300, base_interval=1000)
    
    with open(output_dir / "irregular.json", "w") as f:
        json.dump(irregular_timestamps, f, indent=2)
    
    print(f"Irregular heartbeat: {len(irregular_timestamps)} beats, variable intervals")
    
    # Calculate statistics
    def calculate_stats(timestamps):
        intervals = [timestamps[i+1] - timestamps[i] for i in range(len(timestamps)-1)]
        heart_rates = [60000 / interval for interval in intervals if interval > 0]
        return {
            "avg_interval": sum(intervals) / len(intervals),
            "min_interval": min(intervals),
            "max_interval": max(intervals),
            "avg_hr": sum(heart_rates) / len(heart_rates),
            "min_hr": min(heart_rates),
            "max_hr": max(heart_rates),
            "hrv_std": math.sqrt(sum((hr - sum(heart_rates)/len(heart_rates))**2 for hr in heart_rates) / len(heart_rates))
        }
    
    normal_stats = calculate_stats(normal_timestamps)
    irregular_stats = calculate_stats(irregular_timestamps)
    
    print("\nNormal Heartbeat Statistics:")
    print(f"  Average HR: {normal_stats['avg_hr']:.1f} bpm")
    print(f"  HR Range: {normal_stats['min_hr']:.1f} - {normal_stats['max_hr']:.1f} bpm")
    print(f"  HRV (std): {normal_stats['hrv_std']:.2f} bpm")
    
    print("\nIrregular Heartbeat Statistics:")
    print(f"  Average HR: {irregular_stats['avg_hr']:.1f} bpm")
    print(f"  HR Range: {irregular_stats['min_hr']:.1f} - {irregular_stats['max_hr']:.1f} bpm")
    print(f"  HRV (std): {irregular_stats['hrv_std']:.2f} bpm")
    
    print(f"\nFiles generated in: {output_dir}")

if __name__ == "__main__":
    main() 