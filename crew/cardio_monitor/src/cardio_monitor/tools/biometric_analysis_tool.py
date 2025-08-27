#!/usr/bin/env python3
"""
Biometric Analysis Tool for analyzing patient biometric data.
Follows CrewAI's tool design patterns for file access.
"""

import json
import statistics
from datetime import datetime, timedelta
from typing import Type
from pydantic import BaseModel, Field
from langchain.tools import BaseTool


class AnalyzeBiometricsInput(BaseModel):
    """Input schema for AnalyzeBiometricsTool."""
    time_window_minutes: int = Field(default=60, description="Time window in minutes to analyze (default: 60)")
    buffer_path: str = Field(default="", description="Optional: Buffer path (deprecated - tool now uses crew inputs automatically)")


class AnalyzeBiometricsTool(BaseTool):
    """
    Tool for analyzing biometric data from patient monitoring.
    Follows CrewAI's tool design patterns for file access.
    """
    name: str = "analyze_biometrics"
    description: str = """
    Analyze biometric data from the patient's monitoring buffer.
    Provides statistical analysis of heart rate, blood pressure, respiration, and other vital signs
    within a specified time window. Follows CrewAI's tool design patterns.
    
    Note: No file paths needed - the tool automatically accesses the correct files from crew inputs.
    """
    args_schema: Type[BaseModel] = AnalyzeBiometricsInput

    def _run(self, time_window_minutes: int = 60, buffer_path: str = "") -> str:
        try:
            # Get crew inputs to access file paths
            crew_inputs = {}
            if hasattr(self, 'crew') and hasattr(self.crew, 'crew_inputs'):
                crew_inputs = self.crew.crew_inputs
            elif hasattr(self, '_crew') and hasattr(self._crew, 'crew_inputs'):
                crew_inputs = self._crew.crew_inputs
            else:
                try:
                    tool_context = getattr(self, '_context', {})
                    crew_inputs = tool_context.get('crew_inputs', {})
                except:
                    crew_inputs = {}

            actual_buffer_path = crew_inputs.get('biometric_buffer_path', '')

            # Log for debugging (can be removed in production)
            if buffer_path:
                print(f"Note: buffer_path parameter '{buffer_path}' was provided but ignored - using crew inputs instead")

            if not actual_buffer_path:
                return "Error: No biometric buffer path available in crew inputs"

            # Read the biometric buffer using standard Python file operations
            try:
                with open(actual_buffer_path, 'r') as f:
                    content = f.read()
                biometric_data = json.loads(content)
            except FileNotFoundError:
                return f"Error: File not found at {actual_buffer_path}"
            except json.JSONDecodeError:
                return f"Error: Invalid JSON in file {actual_buffer_path}"
            except Exception as e:
                return f"Error reading biometric buffer: {str(e)}"

            if not isinstance(biometric_data, list) or len(biometric_data) == 0:
                return "No biometric data available for analysis"

            # Calculate time threshold
            now = datetime.now()
            threshold_time = now - timedelta(minutes=time_window_minutes)

            # Filter data within time window
            recent_data = []
            for event in biometric_data:
                try:
                    event_time = datetime.fromisoformat(event.get('timestamp', '').replace('Z', '+00:00'))
                    if event_time >= threshold_time:
                        recent_data.append(event)
                except (ValueError, TypeError):
                    continue

            if not recent_data:
                return f"No biometric data found within the last {time_window_minutes} minutes"

            # Analyze different biometric types
            heart_rates = []
            systolic_bp = []
            diastolic_bp = []
            respiration_rates = []
            temperatures = []
            oxygen_saturations = []

            for event in recent_data:
                event_type = event.get('event_type', '')
                value = event.get('value')
                
                if event_type == 'heart_rate' and value is not None:
                    heart_rates.append(float(value))
                elif event_type == 'blood_pressure' and isinstance(value, dict):
                    if 'systolic' in value:
                        systolic_bp.append(float(value['systolic']))
                    if 'diastolic' in value:
                        diastolic_bp.append(float(value['diastolic']))
                elif event_type == 'respiration_rate' and value is not None:
                    respiration_rates.append(float(value))
                elif event_type == 'temperature' and value is not None:
                    temperatures.append(float(value))
                elif event_type == 'oxygen_saturation' and value is not None:
                    oxygen_saturations.append(float(value))

            # Generate analysis report
            report = f"Biometric Analysis Report\n"
            report += f"Time Window: Last {time_window_minutes} minutes\n"
            report += f"Buffer Path: {actual_buffer_path}\n"
            report += f"Total Events Analyzed: {len(recent_data)}\n"
            report += f"Analysis Time: {now.strftime('%Y-%m-%d %H:%M:%S')}\n\n"

            if heart_rates:
                report += f"Heart Rate Analysis:\n"
                report += f"  Count: {len(heart_rates)}\n"
                report += f"  Average: {statistics.mean(heart_rates):.1f} bpm\n"
                report += f"  Min: {min(heart_rates):.1f} bpm\n"
                report += f"  Max: {max(heart_rates):.1f} bpm\n"
                if len(heart_rates) > 1:
                    report += f"  Standard Deviation: {statistics.stdev(heart_rates):.1f} bpm\n"
                report += "\n"

            if systolic_bp and diastolic_bp:
                report += f"Blood Pressure Analysis:\n"
                report += f"  Systolic - Count: {len(systolic_bp)}, Avg: {statistics.mean(systolic_bp):.1f} mmHg\n"
                report += f"  Diastolic - Count: {len(diastolic_bp)}, Avg: {statistics.mean(diastolic_bp):.1f} mmHg\n\n"

            if respiration_rates:
                report += f"Respiration Rate Analysis:\n"
                report += f"  Count: {len(respiration_rates)}\n"
                report += f"  Average: {statistics.mean(respiration_rates):.1f} breaths/min\n"
                report += f"  Min: {min(respiration_rates):.1f} breaths/min\n"
                report += f"  Max: {max(respiration_rates):.1f} breaths/min\n\n"

            if temperatures:
                report += f"Temperature Analysis:\n"
                report += f"  Count: {len(temperatures)}\n"
                report += f"  Average: {statistics.mean(temperatures):.1f}°C\n"
                report += f"  Min: {min(temperatures):.1f}°C\n"
                report += f"  Max: {max(temperatures):.1f}°C\n\n"

            if oxygen_saturations:
                report += f"Oxygen Saturation Analysis:\n"
                report += f"  Count: {len(oxygen_saturations)}\n"
                report += f"  Average: {statistics.mean(oxygen_saturations):.1f}%\n"
                report += f"  Min: {min(oxygen_saturations):.1f}%\n"
                report += f"  Max: {max(oxygen_saturations):.1f}%\n\n"

            # Add summary of event types
            event_types = {}
            for event in recent_data:
                event_type = event.get('event_type', 'unknown')
                event_types[event_type] = event_types.get(event_type, 0) + 1

            report += "Event Type Summary:\n"
            for event_type, count in sorted(event_types.items()):
                report += f"  {event_type}: {count} events\n"

            return report

        except Exception as e:
            return f"Error in AnalyzeBiometricsTool: {str(e)}"
