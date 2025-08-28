# Care Guard Crews - Consolidated Agentic AI Framework

This directory contains consolidated CrewAI implementations for patient monitoring, all managed under a single UV environment for consistent dependency management.

## Overview

The consolidated crew system provides multiple AI-powered patient analysis solutions while maintaining a single, consistent dependency environment. This approach ensures version compatibility and simplifies maintenance.

## Current Crews

### 1. Cardio Monitor (`cardio_monitor/`)

**Status**: ✅ Production Ready

A multi-agent system for comprehensive patient analysis:

- **Biometric Data Reviewer**: Analyzes real-time biometric streams
- **Senior Cardiac Care Triage Nurse**: Evaluates patient status and makes triage decisions
- **Medical Records Specialist**: Creates comprehensive medical logs and recommendations

**Key Features**:

- Real-time biometric analysis
- Structured medical decision making
- Comprehensive output formatting
- Progress tracking and logging

**Implementation**: `crew/cardio_monitor/src/cardio_monitor/crew.py`

### 2. Knowledge Base Crew (`knowledge_base_crew/`)

**Status**: ✅ Production Ready

A specialized crew for medical knowledge management and research:

- **Researcher**: Gathers medical information from various sources
- **Indexer**: Processes and indexes medical documents
- **Knowledge Base Tools**: OpenSearch integration and document management

**Key Features**:

- Medical document indexing
- Research automation
- Knowledge base management
- OpenSearch integration

**Implementation**: `crew/knowledge_base_crew/src/knowledge_base_crew/crew.py`

## Crew Architecture

### Standard Crew Structure

```
crew/
├── your_crew_name/
│   ├── src/
│   │   └── your_crew_name/
│   │       ├── __init__.py
│   │       ├── crew.py          # Main crew implementation
│   │       ├── config/          # Configuration files
│   │       │   ├── agents.yaml
│   │       │   └── tasks.yaml
│   │       └── tools/           # Crew-specific tools
│   └── README.md                # Crew documentation
├── pyproject.toml               # Consolidated dependencies
├── uv.lock                      # Dependency lock file
└── .venv/                       # Shared virtual environment
```

### Required Interface

Your crew must implement:

```python
class YourCrew:
    def crew(self, **kwargs):
        """
        Main crew method that returns a crew/agent object.

        Args:
            **kwargs: Crew-specific parameters

        Returns:
            A crew/agent object with a .kickoff() method
        """
        # Your crew implementation
        pass
```

### Integration Requirements

1. **Compatible with `agentic_monitor_integration.py`**
2. **Structured output format** (JSON-compatible)
3. **Progress reporting** capability
4. **Error handling** and logging
5. **Configurable parameters** for different use cases

## Adding a New Crew

### Step 1: Create Crew Structure

```bash
mkdir -p crew/your_crew_name/src/your_crew_name
cd crew/your_crew_name
```

### Step 2: Implement Core Crew

Create `crew.py` with your crew implementation:

```python
class YourCrew:
    def __init__(self):
        # Initialize your crew
        pass

    def crew(self, **kwargs):
        # Return your crew/agent object
        return YourCrewInstance(**kwargs)
```

### Step 3: Add Dependencies (if needed)

If your crew needs additional dependencies, add them to the root `crew/pyproject.toml`:

```toml
dependencies = [
    # ... existing dependencies ...
    "your_new_dependency>=1.0.0",
]
```

Then run `uv sync` to update the environment.

### Step 4: Update Integration Layer

Modify `patient/agentic_monitor_integration.py`:

```python
# Add crew detection
if framework_name == "your_crew":
    from crew.your_crew_name.src.your_crew_name.crew import YourCrew
    crew = YourCrew()
```

### Step 5: Update UI

Add crew option in `patient/monitor.py`:

```python
solution_options = ["Crewai", "YourCrew"]
```

### Step 6: Test Integration

1. Run the patient monitor
2. Select your crew from dropdown
3. Test analysis execution
4. Verify output and progress tracking

## Crew Development Guidelines

### Best Practices

1. **Modular Design**: Keep crew logic separate from integration
2. **Error Handling**: Implement robust error handling and logging
3. **Configuration**: Use YAML configs for easy customization
4. **Documentation**: Provide clear usage examples and API docs
5. **Testing**: Include unit tests and integration tests

### Common Patterns

- **Agent Definition**: Clear role definitions and capabilities
- **Task Processing**: Structured task execution pipeline
- **Output Formatting**: Consistent result structure
- **Progress Tracking**: Real-time execution status updates
- **Resource Management**: Efficient memory and CPU usage

### Example Implementation

See `crew/cardio_monitor/` for a complete, production-ready crew implementation that demonstrates all these patterns.

## Testing Your Crew

### Local Testing

```bash
cd crew/your_crew_name
python -m pytest tests/
```

### Integration Testing

1. Start the patient monitor
2. Select your crew
3. Run analysis on test patient
4. Verify output and progress

### Performance Testing

- Monitor memory usage during execution
- Check execution time for different patient datasets
- Validate output quality and consistency

## Contributing

When adding a new crew:

1. **Follow the established structure** and patterns
2. **Include comprehensive documentation**
3. **Add appropriate tests**
4. **Update this README** with crew details
5. **Test integration** with the main system

## Support

For questions about crew development or integration:

1. Check the existing CrewAI implementation as reference
2. Review `patient/agentic_monitor_integration.py` for integration patterns
3. Examine the UI integration in `patient/monitor.py`
4. Consult the main project documentation
