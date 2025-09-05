# Patient Monitoring System - Care Guard Agentic AI

This directory contains the core patient monitoring system, including real-time biometric data streaming, medical record integration, and agentic AI analysis capabilities.

## 📁 Directory Structure

```
patient/
├── monitor.py                      # Main monitoring dashboard (Streamlit)
├── agentic_monitor_app.py         # Agentic analysis interface (Streamlit)
├── biometric_scenario_server.py   # IoT device simulator (TCP/WebSocket)
├── agentic_monitor_integration.py # Legacy integration (deprecated)
├── agentic_data_loader.py         # Patient data loading utilities
├── biometric_types.py             # Biometric data type definitions
├── integrations/                  # Framework integration layer
│   ├── __init__.py               # Framework registry
│   ├── base_integration.py       # Base integration class
│   ├── crewai_integration.py     # CrewAI integration
│   └── langgraph_integration.py  # LangGraph integration
├── monitor_components/            # Reusable UI components
│   ├── heartbeat_component.py    # Heartbeat visualization
│   ├── ekg_component.py          # EKG chart component
│   └── timeline_component.py     # Patient timeline component
├── utils/                         # Utility functions
│   ├── fhir_observations.py      # FHIR data processing
│   ├── generate_realistic_heartbeats.py # Heartbeat generation
│   └── heartbeat_analysis.py     # Heartbeat analysis utilities
├── biometric/                     # Biometric data and scenarios
│   ├── buffer/                   # Real-time data buffer
│   ├── demo_scenarios/           # Predefined medical scenarios
│   └── weight/                   # Patient weight data
├── generated_medical_records/     # Patient medical records
│   ├── fhir/                     # FHIR-formatted records
│   ├── metadata/                 # Record metadata
│   └── pain_diaries/             # Patient pain diary entries
├── agentic_monitor_logs/         # Analysis results and logs
└── README.md                     # This file
```

## 🚀 Quick Start

### Prerequisites

- Python 3.12+
- UV package manager
- OpenAI API key
- Docker (for OpenSearch)

### Running the System

1. **Start Biometric Server** (Terminal 1)

   ```bash
   python patient/biometric_scenario_server.py
   ```

2. **Start Main Monitor** (Terminal 2)

   ```bash
   streamlit run patient/monitor.py
   ```

3. **Start Agentic Monitor** (Terminal 3)
   ```bash
   streamlit run patient/agentic_monitor_app.py --server.port 8502
   ```

## 🏥 Main Monitor (`monitor.py`)

**Purpose**: Real-time patient monitoring dashboard with live biometric visualization.

### Features

- **Patient Selection**: Choose from available patients (Allen, Mark, Zach)
- **Real-time Visualization**: Live heartbeat, EKG, and vital signs display
- **Scenario Controls**: Trigger different medical scenarios (normal, irregular, critical)
- **Medical Records**: Display patient FHIR records and pain diaries
- **Agentic Analysis**: Launch AI-powered patient analysis

### Components

- **Heartbeat Component**: Real-time heartbeat visualization
- **EKG Component**: Electrocardiogram chart display
- **Timeline Component**: Patient data timeline
- **Scenario Controls**: Medical scenario triggers

### Data Sources

- **Biometric Server**: Real-time streaming data
- **FHIR Records**: Patient medical history
- **Pain Diaries**: Patient-reported symptoms
- **Weight Data**: Patient weight measurements

## 🤖 Agentic Monitor App (`agentic_monitor_app.py`)

**Purpose**: Dedicated interface for running and monitoring AI-powered patient analysis.

### Features

- **Framework Selection**: Choose between CrewAI, LangGraph, or other frameworks
- **Background Execution**: Non-blocking analysis execution
- **Progress Monitoring**: Real-time progress bars and status updates
- **Result Display**: Structured presentation of analysis findings
- **Log Integration**: Reads analysis results from logs directory

### Workflow

1. User selects framework and clicks "Run Analysis"
2. Analysis launches in background thread
3. Progress updates displayed in real-time
4. Results shown when analysis completes
5. Logs written to `agentic_monitor_logs/` directory

## 📡 Biometric Scenario Server (`biometric_scenario_server.py`)

**Purpose**: Simulates IoT medical monitoring devices by streaming realistic biometric data.

### Features

- **TCP Socket Server**: Handles client connections (port 5000)
- **WebSocket Server**: Real-time event broadcasting (port 8092)
- **Scenario Engine**: Loads predefined medical scenarios
- **Event Streaming**: Sends timestamped biometric events
- **Command Interface**: Accepts start/stop scenario commands

### Scenarios

- **Normal**: Healthy patient with stable vitals
- **Irregular**: Patient with minor abnormalities
- **Critical**: Patient requiring immediate attention

### Data Types

- **Heartbeat**: Heart rate and pulse strength
- **SpO2**: Blood oxygen saturation
- **Blood Pressure**: Systolic and diastolic pressure
- **Temperature**: Body temperature
- **Respiration**: Breathing rate
- **ECG Rhythm**: Heart rhythm patterns

## 🔗 Integration Layer (`integrations/`)

**Purpose**: Connects the patient monitoring system with various agentic AI frameworks.

### Supported Frameworks

- **CrewAI**: Multi-agent crew-based analysis
- **LangGraph**: State-based workflow analysis
- **Extensible**: Easy addition of new frameworks

### Key Components

- **BaseIntegration**: Common utilities and performance tracking
- **Framework Integrations**: Specific implementations for each framework
- **Framework Registry**: Central registry for framework discovery

See [Integration Layer Documentation](integrations/README.md) for detailed information.

## 📊 Data Flow

```
Biometric Server → Main Monitor → Agentic Monitor → Framework Integration → Analysis Results
     ↓                ↓              ↓                    ↓                    ↓
  Real-time        Live Display   Framework         AI Analysis         Structured
  Biometric        & Controls     Selection         Execution           Logs & Results
  Events
```

## 🔧 Development

### Adding New Patients

1. **Create Patient Data**

   ```bash
   # Add weight data
   echo '[]' > patient/biometric/weight/newpatient.json

   # Add FHIR records
   # Create patient FHIR record in generated_medical_records/fhir/

   # Add pain diary
   # Create pain diary in generated_medical_records/pain_diaries/
   ```

2. **Update Patient List**
   ```python
   # In monitor.py, add to patient list
   patients = ["Allen", "Mark", "Zach", "NewPatient"]
   ```

### Adding New Scenarios

1. **Create Scenario File**

   ```bash
   # Create new scenario in biometric/demo_scenarios/
   echo '{"scenario": "new_scenario", "events": [...]}' > biometric/demo_scenarios/new_scenario.json
   ```

2. **Update Scenario Controls**
   ```python
   # In monitor.py, add scenario button
   if st.button("New Scenario"):
       # Trigger new scenario
   ```

### Customizing Components

The system includes reusable UI components in `monitor_components/`:

- **Heartbeat Component**: Customize heartbeat visualization
- **EKG Component**: Modify EKG chart display
- **Timeline Component**: Adjust patient timeline view

## 🐛 Troubleshooting

### Common Issues

1. **Port Conflicts**: Ensure ports 5000, 8501, and 8502 are available
2. **Biometric Data**: Main monitor requires biometric server to be running
3. **Analysis Launch**: Agentic analysis needs both monitors running
4. **File Paths**: Check that patient data files are accessible
5. **Dependencies**: Run `uv sync` if encountering import errors

### Debug Mode

Enable debug logging:

```bash
export PATIENT_MONITOR_DEBUG=true
export LOG_LEVEL=DEBUG
```

### Log Files

- **Execution Logs**: `agentic_monitor_logs/` directory
- **Biometric Buffer**: `biometric/buffer/simulation_biometrics.json`
- **Patient Data**: `generated_medical_records/` directory

## 📈 Performance Considerations

### Optimization Tips

- **Biometric Buffer**: Monitor buffer size to prevent memory issues
- **Real-time Updates**: Adjust update frequency for performance
- **Analysis Execution**: Use background threads for non-blocking operation
- **File I/O**: Minimize file operations during real-time updates

### Monitoring

- **Memory Usage**: Monitor Streamlit app memory consumption
- **CPU Usage**: Check biometric server CPU usage
- **Network**: Monitor TCP/WebSocket connection performance
- **Analysis Time**: Track agentic analysis execution duration

## 🔄 Getting Back Into Development

When returning to patient monitoring development:

1. **Review System Architecture**: Understand data flow and component relationships
2. **Check Integration Status**: Verify framework integrations are working
3. **Test Patient Data**: Ensure patient records and scenarios are accessible
4. **Run Full System**: Test complete monitoring workflow
5. **Review Recent Logs**: Check analysis results and performance metrics

## 📚 Additional Resources

- [Integration Layer](integrations/README.md) - Framework integration details
- [CrewAI Solutions](../crew/README.md) - CrewAI-based analysis
- [LangGraph Solutions](../langgraph_agents/README.md) - LangGraph-based analysis
- [OpenSearch RAG](../opensearch/README.md) - Knowledge base integration
- [Shared Data Models](../agentic_types/models.py) - Common data structures

## 🤝 Contributing

1. **Follow UI Patterns**: Maintain consistent Streamlit interface design
2. **Handle Errors Gracefully**: Implement proper error handling and user feedback
3. **Optimize Performance**: Monitor and optimize real-time data processing
4. **Add Tests**: Include comprehensive test coverage for new features
5. **Document Changes**: Update README files for new functionality
6. **Maintain Compatibility**: Ensure changes work with all supported frameworks
