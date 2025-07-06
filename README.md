# Care Guard Agentic AI - Patient Monitoring System

A real-time patient monitoring system with synthetic heartbeat data streaming and medical record integration.

## Quick Start

1. **Install dependencies:**

   ```bash
   uv sync
   ```

2. **Generate patient medical records (if needed):**
   This directory is git-ignored, so you will need to run this command to create some fake-patient FHIR medical records.

   ```bash
   # Check if patient records exist
   ls patient/generated_medical_records/fhir/

   # If directory is empty, generate patient records using Synthea
   docker run --rm -it \
     -v "$PWD":/opt/synthea \
     -v "$PWD/patient/generated_medical_records/":/opt/synthea/output \
     -w /opt/synthea \
     openjdk:17 \
     bash -c "./gradlew build -x test && ./run_synthea -p 10 Missouri"
   ```

3. **Run the monitoring system:**
   ```bash
   ./run_monitoring_system.sh
   ```

This will start both the pulse server and Streamlit monitoring app automatically.

## System Architecture

### Pulse Server (`patient/pulse-server.py`)

- **Purpose**: Simulates medical device data streaming
- **Protocols**: TCP socket (port 5000) + WebSocket (port 8765)
- **Data Sources**: JSON files in `patient/biometric/pulse/demo_stream_source/`
- **Scenarios**: Normal, irregular, and cardiac arrest heartbeat patterns
- **Real-time Streaming**: Sends heartbeat events with realistic timing and HRV

### Streamlit Monitoring App (`patient/monitor.py`)

- **Purpose**: Real-time patient monitoring dashboard
- **Features**:
  - Live heartbeat visualization with animated heart emoji
  - Patient FHIR record display and analysis
  - Heartbeat data recording and analysis
  - Medical observation generation

### Data Flow

1. **Pulse Server** reads heartbeat patterns from JSON files
2. **TCP/WebSocket** streams heartbeat events to Streamlit app
3. **JavaScript Component** animates heart emoji in real-time
4. **Heartbeat Buffer** stores events in memory (batch writing)
5. **JSON Storage** saves to `patient/biometric/buffer/pulse_temp.json`
6. **FHIR Integration** creates medical observations from analyzed data

## Biometric Data Storage

### Temporary Buffer (`patient/biometric/buffer/`)

- **Purpose**: Stores incoming biometric streams during monitoring sessions
- **File**: `pulse_temp.json` - Array of heartbeat records with timestamps
- **Format**: Clean IoT device data (timestamp, interval_ms only)
- **Processing**: Batch writing for performance and reliability
- **Analysis**: Automatic heart rate calculation and HRV analysis

### Medical Record Integration

- **FHIR Observations**: Generated from heartbeat analysis
- **Patient Records**: Stored in `patient/generated_medical_records/`
- **Data Flow**: Buffer → Analysis → FHIR Observation → Patient Record

## Development Purpose

This system provides a **UI foundation for agentic patient monitoring** by:

- **Real-time Data Streaming**: Simulates actual medical device feeds
- **Realistic Biometrics**: Heartbeat patterns with natural HRV and arrhythmia
- **Medical Data Integration**: FHIR-compliant patient records
- **Batch Processing**: Efficient handling of continuous data streams
- **Error Recovery**: Robust handling of data corruption and connection issues

The monitoring interface serves as a realistic backdrop for developing AI agents that can:

- Monitor patient vitals in real-time
- Detect anomalies in heartbeat patterns
- Generate medical observations
- Integrate with existing healthcare systems
- Provide clinical decision support

## Manual Setup (Alternative)

If you prefer to run components separately:

1. **Generate patient records (if needed):**

   ```bash
   # Check if patient records exist
   ls patient/generated_medical_records/fhir/

   # If directory is empty, generate patient records
   docker run --rm -it \
     -v "$PWD":/opt/synthea \
     -v "$PWD/patient/generated_medical_records/":/opt/synthea/output \
     -w /opt/synthea \
     openjdk:17 \
     bash -c "./gradlew build && ./run_synthea -p 10 Missouri"
   ```

2. **Start pulse server:**

   ```bash
   cd patient
   python pulse-server.py
   ```

3. **Start Streamlit app (new terminal):**
   ```bash
   cd patient
   streamlit run monitor.py
   ```

## Prerequisites

- **Docker**: Required for generating synthetic patient data
- **Patient Records**: At least one FHIR patient record in `patient/generated_medical_records/fhir/`
- **Python 3.12+**: For running the monitoring system
- **UV package manager**: For dependency management

## Requirements

- Python 3.12+
- UV package manager
- Dependencies: See `requirements.txt`
