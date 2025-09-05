# Care Guard Agentic AI - Patient Monitoring System

A real-time patient monitoring system with synthetic heartbeat data streaming, medical record integration, and multi-framework agentic AI analysis capabilities.

## Quick Start

**Prerequisites**: Python 3.12+, UV package manager, and Docker

### Setup

1. Install Python 3.12+
2. Install UV package manager
3. Install Docker
4. Clone this repo
5. Copy the example `.env.example` file to a file named `.env`, and set a value for `OPENAI_API_KEY` and any other API keys that you intend to use

### Run

1. **Open four terminal windows, each starting in the project root directory**

2. **Terminal 1: Install dependencies and start biometric server**

   ```bash
   # Install dependencies (only needed if not already installed)
   uv sync

   # Start the biometric scenario server (simulates medical device data)
   python patient/biometric_scenario_server.py
   ```

   This server simulates IoT medical devices and streams biometric events to the monitoring system.

3. **Terminal 2: Start OpenSearch in Docker**

   ```bash
   # Navigate to the OpenSearch directory
   cd opensearch/

   # Start OpenSearch using Docker Compose
   docker-compose up -d

   # Verify OpenSearch is running (should show "green" status)
   curl http://localhost:9200/_cluster/health
   ```

4. **Terminal 3: Start the main patient monitor**

   ```bash
   # Activate the virtual environment
   source .venv/bin/activate  # On macOS/Linux
   # or
   .venv\Scripts\activate     # On Windows

   # Start the main monitoring dashboard
   streamlit run patient/monitor.py
   ```

   The main monitor will open at `http://localhost:8501` and display real-time patient data.

5. **Terminal 4: Start the agentic monitor (when needed)**

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

## 📚 Documentation

### Core System

- **[Patient Monitoring System](patient/README.md)** - Main monitoring dashboard and biometric data handling
- **[Integration Layer](patient/integrations/README.md)** - How to add new agentic AI frameworks

### Agentic AI Solutions

- **[CrewAI Solutions](crew/README.md)** - CrewAI-based cardiac monitoring and knowledge base research
- **[LangGraph Solutions](langgraph_agents/README.md)** - LangGraph-based patient monitoring workflows

### Supporting Systems

- **[OpenSearch RAG](opensearch/README.md)** - Knowledge base and RAG integration for enhanced medical insights
- **[Shared Types](agentic_types/)** - Common data models used across all frameworks

## 🏗️ System Architecture

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
- **Background Analysis**: Launches agentic analysis in background threads for non-blocking operation
- **Progress Monitoring**: Real-time progress bars and status updates during analysis
- **Result Display**: Structured presentation of medical analysis findings and recommendations
- **Log Integration**: Reads analysis results from `patient/agentic_monitor_logs/` directory

**Data Flow**: Receives analysis requests → Launches agentic frameworks → Monitors progress → Displays structured results → Writes logs to filesystem

## 🔧 Adding New Agentic Frameworks

The system is designed to support multiple agentic AI frameworks. See the **[Integration Layer Documentation](patient/integrations/README.md)** for detailed instructions on adding new frameworks.

### Quick Integration Steps:

1. Create integration class inheriting from `BaseIntegration`
2. Implement `run_agentic_analysis()` and `test_availability()` methods
3. Register in `patient/integrations/__init__.py`
4. Add to monitor dropdown in `patient/monitor.py`

## 📊 Data Flow Overview

```
Biometric Server (Terminal 1)
    ↓ streams biometric events
Main Monitor (Terminal 2, port 8501)
    ↓ displays real-time data
    ↓ user clicks "Run Analysis"
Agentic Monitor (Terminal 3, port 8502)
    ↓ prepares data for agentic framework
    ↓ runs analysis (CrewAI, LangGraph, etc.)
    ↓ writes results to logs
```

## ✨ Key Features

- **Real-time Monitoring**: Live biometric data streaming with animated visualizations
- **Scenario Simulation**: Predefined medical scenarios for testing and demonstration
- **Patient Records**: FHIR-based patient data display and timeline visualization
- **Multi-Framework AI**: Support for CrewAI, LangGraph, and extensible framework architecture
- **Non-blocking UI**: Background analysis execution with real-time progress updates
- **Structured Output**: Standardized medical analysis results with actionable recommendations
- **RAG Enhancement**: Optional knowledge base integration via OpenSearch for enhanced medical insights

## 📁 File Structure

```
care-guard-agentic-ai/
├── patient/                        # Patient monitoring system
│   ├── biometric_scenario_server.py    # IoT device simulator
│   ├── monitor.py                      # Main monitoring dashboard
│   ├── agentic_monitor_app.py         # AI analysis interface
│   ├── agentic_monitor_logs/          # Analysis results and logs
│   ├── biometric/                     # Scenario data files
│   ├── generated_medical_records/     # Patient FHIR data
│   └── integrations/                  # Framework integration layer
├── crew/                           # CrewAI-based solutions
│   ├── cardio_monitor/             # Cardiac monitoring crew
│   └── knowledge_base_crew/        # Medical knowledge research crew
├── langgraph_agents/               # LangGraph-based solutions
│   ├── workflows/                  # Patient monitoring workflows
│   └── agents/                     # Individual agent implementations
├── opensearch/                     # Knowledge base for RAG enhancement
│   ├── docker-compose.yml          # OpenSearch container setup
│   └── [RAG utilities]             # Document indexing and search tools
├── agentic_types/                  # Shared data models and types
└── utils/                          # Shared utilities and helpers
```

## 🚨 Troubleshooting

- **Port Conflicts**: Ensure ports 5000, 8501, and 8502 are available
- **Dependencies**: Run `uv sync` in project root if you encounter import errors
- **Biometric Data**: The main monitor requires the biometric server to be running first
- **Analysis Launch**: Agentic analysis only works when both monitors are running
- **OpenSearch**: If using RAG features, ensure OpenSearch is running via Docker Compose

## 🔄 Getting Back Into Development

When returning to this project:

1. **Review the documentation** in each solution directory to understand current implementations
2. **Check the integration layer** to see how frameworks are connected
3. **Run the system** using the Quick Start guide above
4. **Test both frameworks** (CrewAI and LangGraph) to ensure they're working
5. **Review recent logs** in `patient/agentic_monitor_logs/` to see what's been tested

## 🤝 Contributing

See individual solution documentation for framework-specific contribution guidelines:

- [CrewAI Solutions](crew/README.md)
- [LangGraph Solutions](langgraph_agents/README.md)
- [Integration Layer](patient/integrations/README.md)
