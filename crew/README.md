# CrewAI Solutions - Care Guard Agentic AI

This directory contains CrewAI-based agentic AI solutions for patient monitoring and medical knowledge management.

## 📁 Directory Structure

```
crew/
├── cardio_monitor/              # Cardiac monitoring crew
│   ├── src/cardio_monitor/     # Main crew implementation
│   │   ├── crew.py            # Crew definition and agents
│   │   ├── main.py            # Entry point and execution
│   │   ├── config/            # Agent and task configurations
│   │   └── tools/             # Custom tools and utilities
│   ├── tests/                 # Unit and integration tests
│   └── README.md              # Detailed crew documentation
├── knowledge_base_crew/        # Medical knowledge research crew
│   ├── src/knowledge_base_crew/ # Main crew implementation
│   │   ├── crew.py            # Crew definition and agents
│   │   ├── main.py            # Entry point and execution
│   │   ├── config/            # Agent and task configurations
│   │   └── tools/             # Custom tools and utilities
│   ├── tests/                 # Unit and integration tests
│   └── README.md              # Detailed crew documentation
├── pyproject.toml             # Project configuration and dependencies
├── requirements.txt           # Python dependencies
└── README.md                  # This file
```

## 🚀 Quick Start

### Prerequisites

- Python 3.12+
- UV package manager
- OpenAI API key
- OpenSearch (for knowledge base crew)

### Installation

```bash
# From project root
cd crew/
uv sync
```

### Running Individual Crews

#### Cardio Monitor Crew

```bash
cd cardio_monitor/
python src/cardio_monitor/main.py
```

#### Knowledge Base Crew

```bash
cd knowledge_base_crew/
python src/knowledge_base_crew/main.py
```

## 🏥 Cardio Monitor Crew

**Purpose**: Real-time cardiac patient monitoring and analysis using CrewAI agents.

### Features

- **Biometric Analysis**: Reviews heart rate, SpO2, blood pressure, and other vital signs
- **Triage Decision Making**: Determines appropriate care actions based on biometric data
- **Medical Logging**: Creates structured medical logs with findings and recommendations
- **RAG Integration**: Uses medical knowledge base for enhanced analysis

### Agents

1. **Biometric Reviewer**: Analyzes real-time biometric data and identifies anomalies
2. **Triage Nurse**: Makes care decisions based on biometric analysis and medical history
3. **Log Writer**: Creates comprehensive medical logs with findings and recommendations

### Configuration

- **Agents**: Defined in `src/cardio_monitor/config/agents.yaml`
- **Tasks**: Defined in `src/cardio_monitor/config/tasks.yaml`
- **Tools**: Custom tools in `src/cardio_monitor/tools/`

### Integration

The cardio monitor crew is integrated into the main patient monitoring system via:

- `patient/integrations/crewai_integration.py`
- Called from the agentic monitor app when "CrewAI" is selected

## 📚 Knowledge Base Crew

**Purpose**: Medical knowledge research and indexing for RAG-enhanced analysis.

### Features

- **Medical Research**: Searches and retrieves relevant medical articles
- **Knowledge Indexing**: Indexes articles into OpenSearch for RAG queries
- **Content Processing**: Extracts and structures medical information
- **Search Integration**: Provides searchable medical knowledge base

### Agents

1. **Medical Researcher**: Searches for relevant medical articles and information
2. **Knowledge Indexer**: Processes and indexes articles into OpenSearch

### Configuration

- **Agents**: Defined in `src/knowledge_base_crew/config/agents.yaml`
- **Tasks**: Defined in `src/knowledge_base_crew/config/tasks.yaml`
- **Tools**: Custom tools in `src/knowledge_base_crew/tools/`

### Integration

The knowledge base crew works with:

- OpenSearch for article storage and retrieval
- RAG tools for enhanced medical analysis
- Other crews for knowledge-enhanced decision making

## 🔧 Development

### Adding a New Crew

1. **Create Directory Structure**

   ```bash
   mkdir -p new_crew/src/new_crew/{config,tools}
   mkdir -p new_crew/tests
   ```

2. **Define Crew Configuration**

   - Create `config/agents.yaml` with agent definitions
   - Create `config/tasks.yaml` with task definitions
   - Implement custom tools in `tools/`

3. **Implement Crew Logic**

   - Create `crew.py` with crew definition
   - Create `main.py` with entry point
   - Add tests in `tests/`

4. **Update Dependencies**
   - Add crew-specific dependencies to `requirements.txt`
   - Update `pyproject.toml` if needed

### Testing

```bash
# Run all tests
cd crew/
python -m pytest

# Run specific crew tests
cd cardio_monitor/
python -m pytest tests/

cd knowledge_base_crew/
python -m pytest tests/
```

### Configuration Management

Each crew uses YAML configuration files for:

- **Agent definitions**: Roles, goals, backstories
- **Task definitions**: Descriptions, expected outputs, context
- **Tool configurations**: Parameters and settings

## 🔗 Integration with Main System

### Data Flow

```
Patient Monitor → Integration Layer → CrewAI Crew → Analysis Results → Logs
```

### Shared Components

- **Data Models**: Uses `agentic_types/models.py` for consistent output
- **File Discovery**: Inherits from `BaseIntegration` for patient data access
- **Logging**: Writes structured logs to `patient/agentic_monitor_logs/`

### Framework Registry

Crews are registered in `patient/integrations/__init__.py`:

```python
FRAMEWORK_REGISTRY = {
    "crewai": CrewaiIntegration,
    # Other frameworks...
}
```

## 📊 Performance Monitoring

The system includes performance tracking for:

- **Execution Time**: Duration of crew execution
- **Token Usage**: LLM token consumption
- **Tool Calls**: Number of tool invocations
- **Success Rates**: Analysis completion rates

## 🐛 Troubleshooting

### Common Issues

1. **Import Errors**: Ensure all dependencies are installed with `uv sync`
2. **OpenAI API**: Verify API key is set in `.env` file
3. **OpenSearch**: Ensure OpenSearch is running for knowledge base crew
4. **File Paths**: Check that patient data files are accessible

### Debug Mode

Enable debug logging by setting environment variables:

```bash
export CREWAI_DEBUG=true
export LOG_LEVEL=DEBUG
```

## 📈 Future Enhancements

- **Additional Medical Specialties**: Expand beyond cardiac monitoring
- **Multi-Patient Analysis**: Support for multiple patients simultaneously
- **Advanced RAG**: Enhanced knowledge base integration
- **Performance Optimization**: Improved execution speed and resource usage
- **Custom Tools**: Additional medical analysis tools and utilities

## 🤝 Contributing

1. **Follow CrewAI Best Practices**: Use proper agent and task definitions
2. **Maintain Configuration**: Keep YAML files well-documented
3. **Add Tests**: Include comprehensive test coverage
4. **Document Changes**: Update README files for new features
5. **Performance**: Monitor and optimize crew execution times

## 📚 Additional Resources

- [CrewAI Documentation](https://docs.crewai.com/)
- [Individual Crew READMEs](cardio_monitor/README.md) and [Knowledge Base Crew](knowledge_base_crew/README.md)
- [Integration Layer Documentation](../patient/integrations/README.md)
- [Shared Data Models](../agentic_types/models.py)
