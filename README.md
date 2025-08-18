# Care Guard Agentic AI - Patient Monitoring System

A real-time patient monitoring system with synthetic heartbeat data streaming, medical record integration, and agentic AI analysis capabilities.

## Quick Start

1. **Activate the virtual environment:**

   ```bash
   source .venv/bin/activate  # On macOS/Linux
   # or
   .venv\Scripts\activate     # On Windows
   ```

   The project uses a single virtual environment at the root level with all dependencies pre-installed.

2. **Run the monitoring system:**

   ```bash
   ./run_monitoring_system.sh
   ```

   This will start:

   - **Biometric Scenario Server** (background) - Simulates medical device data streaming
   - **Main Patient Monitor** on port 8501
   - **Agentic Monitor** on port 8502 (launched when needed)

Alternatively, you can run these three commands in separate terminal windows from project root:

```bash
# Terminal 1: Biometric scenario server (background)
python patient/biometric_scenario_server.py

# Terminal 2: Main patient monitor
streamlit run patient/monitor.py

# Terminal 3: Agentic monitor (when needed)
streamlit run patient/agentic_monitor_app.py --server.port 8502
```

**Note**: The biometric scenario server must be running for the patient monitor to receive heartbeat data and run scenarios.

## Agentic AI Features

The monitoring system now includes agentic AI analysis capabilities:

- **Agentic Analysis Button**: Located in the main monitor sidebar under "🤖 Agentic Analysis"
- **Dedicated Agentic Monitor**: Separate Streamlit app (port 8502) for focused agent monitoring
- **CrewAI Integration**: Automated patient status analysis using AI agents
- **Real-time Progress**: Manual refresh updates in the dedicated agentic monitor
- **Structured Results**: Comprehensive analysis output with medical recommendations

### Using Agentic Features

1. Select a patient from the main monitor sidebar
2. Click "🚀 Run Analysis" to launch the agentic monitor in a new window
3. Monitor progress using the refresh button in the agentic monitor
4. View structured results when analysis completes
5. Continue using the main monitor for patient data while analysis runs

For details on adding new agentic frameworks, see [Patient Monitor README](patient/README.md).

### Standardized Output Format

All agentic frameworks must produce comparable, structured output to ensure consistent UI rendering and data processing. The system uses standardized Pydantic models defined in [`agentic_types/models.py`](agentic_types/models.py) to enforce this consistency.

**Required Output Structure**:

- **Patient Information**: Identity, demographics, and context
- **Triage Decision**: Action, priority, rationale, and follow-ups
- **Medical Findings**: Structured insights with confidence levels and risk assessment
- **Recommendations**: Actionable care guidance with priority and rationale
- **Execution Metrics**: Performance and resource usage data
- **Framework Identification**: Source framework and version information

This standardization ensures that:

- The UI can consistently render results from any framework
- Data can be processed and compared across different AI solutions
- New frameworks can be integrated without UI changes
- Results maintain consistent quality and structure

**Example Output Fields**:

```json
{
  "success": true,
  "run_id": "unique_run_identifier",
  "framework": "crewai",
  "patient": { "name": "Patient Name", "id": "patient_id" },
  "started_at": "2023-10-11T10:00:00Z",
  "completed_at": "2023-10-11T10:05:00Z",
  "summary": "Patient summary text",
  "triage_decision": {
    "action": "notify_physician",
    "priority": "high",
    "summary": "Decision summary",
    "rationale": "Decision rationale",
    "followups": ["Follow-up action 1", "Follow-up action 2"]
  },
  "findings": [
    {
      "title": "Finding Title",
      "summary": "Finding summary",
      "risk_level": "moderate"
    }
  ],
  "recommendations": [
    {
      "text": "Action text",
      "priority": "medium"
    }
  ],
  "metrics": {
    "duration_ms": 5000,
    "tokens_used": 1200,
    "tool_calls": 3,
    "steps_completed": 3
  },
  "artifacts": {},
  "error": null
}
```

For complete schema details, see the Pydantic models in [`agentic_types/models.py`](agentic_types/models.py).

## System Architecture

### Pulse Server (`patient/biometric_scenario_server.py`)

- **Purpose**: Simulates medical device data streaming
- **Protocols**: TCP socket (port 5000) + WebSocket (port 8092)
- **Scenarios**: Normal, irregular, and critical heartbeat patterns
- **Real-time Streaming**: Sends heartbeat events with realistic timing and HRV

### Streamlit Monitoring App (`patient/monitor.py`)

- **Purpose**: Real-time patient monitoring dashboard
- **Features**:
  - Live heartbeat visualization with animated heart emoji
  - Patient FHIR record display and analysis
  - Heartbeat data recording and analysis
  - Agentic analysis integration

### Data Flow

1. **Biometric Scenario Server** streams demo scenarios to monitor.py and frontend components
2. **TCP/WebSocket** streams heartbeat events to Streamlit app
3. **JavaScript Component** animates heart emoji in real-time
4. **simulation_biometrics.json Buffer** stores events for agentic analysis
5. **Agentic AI** processes data and provides medical insights

## Prerequisites

- **Python 3.12+**: For running the monitoring system
- **UV package manager**: For dependency management (optional - virtual environment is pre-configured)
- **OpenAI API Key**: Required for CrewAI agentic analysis (set in `.env` file)

## Development Setup

If you need to install additional dependencies or modify the project:

```bash
# Activate the virtual environment
source .venv/bin/activate

# Install additional packages
uv pip install <package-name>

# Sync dependencies from pyproject.toml (if modified)
uv sync
```
