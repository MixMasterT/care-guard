#!/usr/bin/env python3
"""
Patient Data Tool for reading various types of patient data.
Follows CrewAI's tool design patterns for file access.
"""

import json
import jsonlines
from typing import Type
from pydantic import BaseModel, Field
from langchain.tools import BaseTool


class ReadPatientDataInput(BaseModel):
    """Input schema for ReadPatientDataTool."""
    data_type: str = Field(..., description="Type of data to read: 'biometric_buffer', 'patient_summary', 'pain_journal', 'fhir_records', 'existing_logs', or 'context_file'")
    file_path: str = Field(default="", description="Optional: File path (deprecated - tool now uses crew inputs automatically)")


class ReadPatientDataTool(BaseTool):
    """
    Tool for reading various types of patient data files.
    Follows CrewAI's tool design patterns for file access.
    """
    name: str = "read_patient_data"
    description: str = """
    Read patient data from various file types. Supports:
    - biometric_buffer: JSON file with biometric readings
    - patient_summary: JSON file with patient information
    - pain_journal: JSONL file with pain entries
    - fhir_records: JSON file with FHIR data
    - existing_logs: JSONL file with existing medical logs
    - context_file: JSON file with agentic input context
    
    Note: No file paths needed - the tool automatically accesses the correct files from crew inputs.
    """
    args_schema: Type[BaseModel] = ReadPatientDataInput

    def _run(self, data_type: str, file_path: str = "") -> str:
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

            # Get file paths from crew inputs
            biometric_buffer_path = crew_inputs.get('biometric_buffer_path', '')
            patient_summary_path = crew_inputs.get('patient_summary_path', '')
            pain_journal_path = crew_inputs.get('pain_journal_path', '')
            fhir_records_path = crew_inputs.get('fhir_records_path', '')
            agentic_input_path = crew_inputs.get('agentic_input_path', '')

            # Log for debugging (can be removed in production)
            if file_path:
                print(f"Note: file_path parameter '{file_path}' was provided but ignored - using crew inputs instead")

            if data_type == "biometric_buffer":
                if not biometric_buffer_path:
                    return "Error: No biometric buffer path available in crew inputs"
                try:
                    with open(biometric_buffer_path, 'r') as f:
                        content = f.read()
                    return f"Biometric Buffer Data:\n{content}"
                except FileNotFoundError:
                    return f"Error: File not found at {biometric_buffer_path}"
                except Exception as e:
                    return f"Error reading biometric buffer: {str(e)}"

            elif data_type == "patient_summary":
                if not patient_summary_path:
                    return "Error: No patient summary path available in crew inputs"
                try:
                    with open(patient_summary_path, 'r') as f:
                        content = f.read()
                    return f"Patient Summary Data:\n{content}"
                except FileNotFoundError:
                    return f"Error: File not found at {patient_summary_path}"
                except Exception as e:
                    return f"Error reading patient summary: {str(e)}"

            elif data_type == "pain_journal":
                if not pain_journal_path:
                    return "Error: No pain journal path available in crew inputs"
                try:
                    with open(pain_journal_path, 'r') as f:
                        content = f.read()
                    return f"Pain Journal Data:\n{content}"
                except FileNotFoundError:
                    return f"Error: File not found at {pain_journal_path}"
                except Exception as e:
                    return f"Error reading pain journal: {str(e)}"

            elif data_type == "fhir_records":
                if not fhir_records_path:
                    return "Error: No FHIR records path available in crew inputs"
                try:
                    with open(fhir_records_path, 'r') as f:
                        content = f.read()
                    return f"FHIR Records Data:\n{content}"
                except FileNotFoundError:
                    return f"Error: File not found at {fhir_records_path}"
                except Exception as e:
                    return f"Error reading FHIR records: {str(e)}"

            elif data_type == "existing_logs":
                if not agentic_input_path:
                    return "Error: No agentic input path available in crew inputs"
                try:
                    with open(agentic_input_path, 'r') as f:
                        content = f.read()
                    return f"Existing Logs Data:\n{content}"
                except FileNotFoundError:
                    return f"Error: File not found at {agentic_input_path}"
                except Exception as e:
                    return f"Error reading existing logs: {str(e)}"

            elif data_type == "context_file":
                if not agentic_input_path:
                    return "Error: No agentic input path available in crew inputs"
                try:
                    with open(agentic_input_path, 'r') as f:
                        content = f.read()
                    return f"Context File Data:\n{content}"
                except FileNotFoundError:
                    return f"Error: File not found at {agentic_input_path}"
                except Exception as e:
                    return f"Error reading context file: {str(e)}"

            else:
                return f"Error: Unknown data type '{data_type}'. Supported types: biometric_buffer, patient_summary, pain_journal, fhir_records, existing_logs, context_file"

        except Exception as e:
            return f"Error in ReadPatientDataTool: {str(e)}"
