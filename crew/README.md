# Agentic AI Frameworks

This directory contains the agentic AI frameworks that power the patient monitoring system's intelligent analysis capabilities.

## Overview

The agentic framework system provides a modular approach to AI-powered patient analysis, allowing different AI solutions to be integrated while maintaining a consistent interface and user experience.

## Current Frameworks

### CrewAI (`cardio_monitor/`)

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

## Framework Architecture

### Standard Framework Structure

```
crew/
├── your_framework_name/
│   ├── src/
│   │   └── your_framework_name/
│   │       ├── __init__.py
│   │       ├── crew.py          # Main framework implementation
│   │       ├── config/          # Configuration files
│   │       │   ├── agents.yaml
│   │       │   └── tasks.yaml
│   │       └── tools/           # Framework-specific tools
│   ├── pyproject.toml          # Dependencies
│   └── README.md               # Framework documentation
```

### Required Interface

Your framework must implement:

```python
class YourFramework:
    def crew(self, **kwargs):
        """
        Main framework method that returns a crew/agent object.

        Args:
            **kwargs: Framework-specific parameters

        Returns:
            A crew/agent object with a .kickoff() method
        """
        # Your framework implementation
        pass
```

### Integration Requirements

1. **Compatible with `agentic_monitor_integration.py`**
2. **Structured output format** (JSON-compatible)
3. **Progress reporting** capability
4. **Error handling** and logging
5. **Configurable parameters** for different use cases

## Adding a New Framework

### Step 1: Create Framework Structure

```bash
mkdir -p crew/your_framework_name/src/your_framework_name
cd crew/your_framework_name
```

### Step 2: Implement Core Framework

Create `crew.py` with your framework implementation:

```python
class YourFramework:
    def __init__(self):
        # Initialize your framework
        pass

    def crew(self, **kwargs):
        # Return your crew/agent object
        return YourCrew(**kwargs)
```

### Step 3: Update Integration Layer

Modify `patient/agentic_monitor_integration.py`:

```python
# Add framework detection
if framework_name == "your_framework":
    from crew.your_framework.src.your_framework.crew import YourFramework
    crew = YourFramework()
```

### Step 4: Update UI

Add framework option in `patient/monitor.py`:

```python
solution_options = ["Crewai", "YourFramework"]
```

### Step 5: Test Integration

1. Run the patient monitor
2. Select your framework from dropdown
3. Test analysis execution
4. Verify output and progress tracking

## Framework Development Guidelines

### Best Practices

1. **Modular Design**: Keep framework logic separate from integration
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

See `crew/cardio_monitor/` for a complete, production-ready framework implementation that demonstrates all these patterns.

## Testing Your Framework

### Local Testing

```bash
cd crew/your_framework_name
python -m pytest tests/
```

### Integration Testing

1. Start the patient monitor
2. Select your framework
3. Run analysis on test patient
4. Verify output and progress

### Performance Testing

- Monitor memory usage during execution
- Check execution time for different patient datasets
- Validate output quality and consistency

## Contributing

When adding a new framework:

1. **Follow the established structure** and patterns
2. **Include comprehensive documentation**
3. **Add appropriate tests**
4. **Update this README** with framework details
5. **Test integration** with the main system

## Support

For questions about framework development or integration:

1. Check the existing CrewAI implementation as reference
2. Review `patient/agentic_monitor_integration.py` for integration patterns
3. Examine the UI integration in `patient/monitor.py`
4. Consult the main project documentation
