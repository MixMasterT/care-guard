# Care Guard Agentic AI - Patient Monitoring System

A real-time patient monitoring system with synthetic heartbeat data streaming and medical record integration.

## Quick Start

1. **Install dependencies:**

   ```bash
   uv sync
   uv pip install -r requirements.txt
   ```

   followed by

   ```bash
   source .venv/bin/activate  # On macOS/Linux
   # or
   .venv\Scripts\activate     # On Windows
   ```

2. **Run the monitoring system:**
   ```bash
   ./run_monitoring_system.sh
   ```
   This will start both the pulse server and Streamlit monitoring app automatically.

Alternatively, you can run these two commands in separate terminal windows from project root:

```bash
streamlit run patient/monitor.py
# and in another terminal
python patient/biometric_scenario_server.py
```

This arrangement allows separate log monitoring for the two servers, which may be more convenient

## System Architecture

### Pulse Server (`patient/biometric_scenario_server.py`)

- **Purpose**: Simulates medical device data streaming
- **Protocols**: TCP socket (port 5000) + WebSocket (port 8092)
- **Data Sources**: JSON files in `patient/biometric/pulse/demo_stream_source/`
- **Scenarios**: Normal, irregular, and critical heartbeat patterns
- **Real-time Streaming**: Sends heartbeat events with realistic timing and HRV

### Streamlit Monitoring App (`patient/monitor.py`)

- **Purpose**: Real-time patient monitoring dashboard
- **Features**:
  - Live heartbeat visualization with animated heart emoji
  - Patient FHIR record display and analysis
  - Heartbeat data recording and analysis
  - Medical observation generation

### Data Flow

1. **Biometric Scenario Server** reads demo scenarios from JSON files and streams to monitor.py and frontend JavaScript/d3 components
2. **TCP/WebSocket** streams heartbeat events to Streamlit app
3. **JavaScript Component** animates heart emoji in real-time
4. **simulation_biometrics.json Buffer** stores events in a local file (for subsequent agentic-monitor access)
5. **FHIR Integration** creates medical observations from analyzed data (this will be a job for the agentic-ai solutions)

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

## Prerequisites

- **Docker**: Required for running the open-search container (see opensearch/)
- **Patient Records**: Three records have been committed, see `patient/generated_medical_records/fhir/`
- **Python 3.12+**: For running the monitoring system
- **UV package manager**: For dependency management

## Requirements

- UV package manager
- Dependencies: See `requirements.txt`
