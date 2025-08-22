# Care Guard Agentic AI - Patient Monitoring System

A real-time patient monitoring system with synthetic heartbeat data streaming, medical record integration, and agentic AI analysis capabilities.

## Quick Start

**Prerequisites**: Python 3.12+ and UV package manager

### Setup and Run

1. **Open three terminal windows, each starting in the project root directory**

2. **Terminal 1: Install dependencies and start biometric server**

   ```bash
   # Install dependencies (only needed if not already installed)
   uv sync

   # Alternative two-step installation:
   # uv venv
   # uv pip install -r requirements.txt

   # Start the biometric scenario server (simulates medical device data)
   python patient/biometric_scenario_server.py
   ```

   This server simulates IoT medical devices and streams biometric events to the monitoring system.

3. **Terminal 2: Start the main patient monitor**

   ```bash
   # Activate the virtual environment
   source .venv/bin/activate  # On macOS/Linux
   # or
   .venv\Scripts\activate     # On Windows

   # Start the main monitoring dashboard
   streamlit run patient/monitor.py
   ```

   The main monitor will open at `http://localhost:8501` and display real-time patient data.

4. **Terminal 3: Start the agentic monitor (when needed)**

   ```bash
   # Activate the virtual environment
   source .venv/bin/activate  # On macOS/Linux
   # or
   .venv\Scripts\activate     # On Windows

   # Start the agentic analysis monitor
   streamlit run patient/agentic_monitor_app.py --server.port 8502
   ```

   This opens at `http://localhost:8502` and runs when you click "Run Analysis" in the main monitor.

**Note**: The biometric scenario server (Terminal 1) must be running for the patient monitor to receive heartbeat data and run scenarios.

### Optional: OpenSearch Setup for RAG Knowledge Enhancement

If you want to use Retrieval-Augmented Generation (RAG) for enhanced medical knowledge:

```bash
# Navigate to the OpenSearch directory
cd opensearch/

# Start OpenSearch using Docker Compose
docker-compose up -d

# Verify OpenSearch is running (should show "green" status)
curl http://localhost:9200/_cluster/health
```

OpenSearch provides a knowledge base that AI research teams can populate with medical reference materials, enabling LLMs to access up-to-date medical information during patient analysis.

## System Architecture

### 1. Biometric Scenario Server (`patient/biometric_scenario_server.py`)

**Purpose**: Simulates IoT medical monitoring devices by streaming realistic biometric data

**Implementation**:

- **TCP Socket Server** (port 5000): Handles primary client connections and commands
- **WebSocket Server** (port 8092): Provides real-time event broadcasting for web components
- **Scenario Engine**: Loads predefined biometric patterns (normal, irregular, critical) from JSON files
- **Event Streaming**: Sends timestamped biometric events with realistic timing intervals
- **Command Interface**: Accepts start/stop scenario commands from monitoring applications

**Data Flow**: Reads scenario JSON files → Processes timing intervals → Broadcasts events via TCP and WebSocket → Maintains client connection state

### 2. Main Patient Monitor (`patient/monitor.py`)

**Purpose**: Real-time patient monitoring dashboard with live biometric visualization

**Implementation**:

- **Streamlit Dashboard**: Main interface for patient selection and monitoring
- **Real-time Data Display**: Live heartbeat visualization, EKG charts, and patient timelines
- **Biometric Buffer**: Collects and stores streaming biometric events in `simulation_biometrics.json`
- **Patient FHIR Records**: Parses and displays patient medical history from generated records
- **Scenario Controls**: Buttons to trigger different biometric scenarios (normal, irregular, critical)
- **Agentic Integration**: "Run Analysis" button that launches the agentic monitor

**Data Flow**: Receives biometric events → Updates real-time displays → Stores events in buffer → Triggers agentic analysis when requested

### 3. Agentic Monitor App (`patient/agentic_monitor_app.py`)

**Purpose**: Dedicated interface for running and monitoring AI-powered patient analysis

**Implementation**:

- **Separate Streamlit App**: Runs on port 8502 to avoid conflicts with main monitor
- **Background Analysis**: Launches CrewAI analysis in background threads for non-blocking operation
- **Progress Monitoring**: Real-time progress bars and status updates during analysis
- **Result Display**: Structured presentation of medical analysis findings and recommendations
- **Log Integration**: Reads analysis results from `patient/agentic_monitor_logs/` directory

**Data Flow**: Receives analysis requests → Launches CrewAI agents → Monitors progress → Displays structured results → Writes logs to filesystem

## Adding New Agentic Frameworks

The system is designed to support multiple agentic AI frameworks beyond CrewAI. Here's how to integrate a new framework:

### 1. Update Monitor Options

Add your framework to the dropdown in `patient/monitor.py`:

```python
solution_options = ["Crewai", "YourFramework"]  # Add your framework here
```

### 2. Create Framework Integration

Create a new integration class in `patient/integrations/your_framework_integration.py`:

```python
from .base_integration import BaseIntegration

class YourFrameworkIntegration(BaseIntegration):
    def __init__(self):
        super().__init__()
        self.framework_name = "YourFramework"
        # Initialize your framework-specific components

    def run_agentic_analysis(self, patient_name: str, run_id: Optional[str] = None) -> Dict[str, Any]:
        """Run analysis using your framework."""
        # Implement your framework's analysis logic
        # Use inherited methods: self._discover_patient_file_paths(), self._process_temporal_data()
        pass

    def test_availability(self) -> Dict[str, Any]:
        """Test if your framework is available."""
        # Return availability status
        pass
```

### 3. Register Your Integration

Add your integration to `patient/integrations/__init__.py`:

```python
FRAMEWORK_REGISTRY = {
    "crewai": CrewaiIntegration,
    "yourframework": YourFrameworkIntegration,  # Add this line
}
```

### 4. Framework-Specific Implementation

Your integration should:

- **Inherit from `BaseIntegration`** to get common utilities (file path discovery, temporal data processing)
- **Implement required methods**: `run_agentic_analysis()`, `test_availability()`
- **Use shared data models** from `agentic_types/models.py` for consistent output
- **Handle file paths** passed from the integration layer
- **Write structured output** to the `patient/agentic_monitor_logs/` directory

### 5. Testing Your Integration

```bash
# Test framework availability
python -c "from patient.integrations import get_integration; print(get_integration('yourframework').test_availability())"

# Run analysis through the UI
# Select your framework in the monitor dropdown and click "Run Analysis"
```

**Key Benefits**: Your framework automatically gets access to patient data discovery, temporal processing, and standardized output formats without additional development.

## Data Flow Overview

```
Biometric Server (Terminal 1)
    ↓ streams biometric events
Main Monitor (Terminal 2, port 8501)
    ↓ displays real-time data
    ↓ user clicks "Run Analysis"
Agentic Monitor (Terminal 3, port 8502)
    ↓ prepares data for agentic-monitoring-solution (via agentic_monitor_integration.py)
    ↓ runs CrewAI analysis
    ↓ writes results to logs
```

## Key Features

- **Real-time Monitoring**: Live biometric data streaming with animated visualizations
- **Scenario Simulation**: Predefined medical scenarios for testing and demonstration
- **Patient Records**: FHIR-based patient data display and timeline visualization
- **Agentic AI**: Automated patient status analysis using CrewAI framework
- **Framework Extensibility**: Easy integration of additional agentic frameworks (LangGraph, custom solutions)
- **Non-blocking UI**: Background analysis execution with real-time progress updates
- **Structured Output**: Standardized medical analysis results with actionable recommendations
- **RAG Enhancement**: Optional knowledge base integration via OpenSearch for enhanced medical insights

## File Structure

```
care-guard-agentic-ai/
├── patient/                        # Patient monitoring system
│   ├── biometric_scenario_server.py    # IoT device simulator
│   ├── monitor.py                      # Main monitoring dashboard
│   ├── agentic_monitor_app.py         # AI analysis interface
│   ├── agentic_monitor_logs/          # Analysis results and logs
│   ├── biometric/                     # Scenario data files
│   └── generated_medical_records/     # Patient FHIR data
├── crew/                           # Agentic AI solutions
│   ├── cardio_monitor/             # CrewAI-based cardiac monitoring
│   ├── knowledge_base_crew/        # Medical knowledge research and indexing
│   └── [future_solutions]/         # Additional agentic frameworks
├── opensearch/                     # Knowledge base for RAG enhancement
│   ├── docker-compose.yml          # OpenSearch container setup
│   ├── document_indexer.py         # Document indexing utilities
│   └── rag_agent.py                # RAG integration tools
├── agentic_types/                  # Shared data models and types
├── langgraph_agents/               # LangGraph-based agentic solutions
└── utils/                          # Shared utilities and helpers
```

**Note**: Each agentic monitoring solution (CrewAI, LangGraph, etc.) lives in its own root-level directory, allowing for independent development and deployment while sharing common infrastructure.

## Troubleshooting

- **Port Conflicts**: Ensure ports 5000, 8501, and 8502 are available
- **Dependencies**: Run `uv sync` in project root if you encounter import errors
- **Biometric Data**: The main monitor requires the biometric server to be running first
- **Analysis Launch**: Agentic analysis only works when both monitors are running
- **OpenSearch**: If using RAG features, ensure OpenSearch is running via Docker Compose

For detailed development information and adding new agentic frameworks, see the "Adding New Agentic Frameworks" section above and individual component documentation.
