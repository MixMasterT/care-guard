# Integration Layer - Care Guard Agentic AI

This directory contains the integration layer that connects the patient monitoring system with various agentic AI frameworks (CrewAI, LangGraph, etc.).

## 📁 Directory Structure

```
patient/integrations/
├── __init__.py                 # Framework registry and integration factory
├── base_integration.py         # Base integration class with common utilities
├── crewai_integration.py       # CrewAI framework integration
├── langgraph_integration.py    # LangGraph framework integration
└── README.md                   # This file
```

## 🏗️ Architecture Overview

The integration layer provides a unified interface for different agentic AI frameworks while maintaining framework-specific implementations. This allows the patient monitoring system to work with multiple AI frameworks seamlessly.

### Key Components

1. **BaseIntegration**: Abstract base class with common utilities
2. **Framework Integrations**: Specific implementations for each framework
3. **Framework Registry**: Central registry for framework discovery
4. **Integration Factory**: Factory pattern for creating framework instances

## 🔧 Base Integration Class

The `BaseIntegration` class provides common functionality for all framework integrations:

### Core Methods

- `run_agentic_analysis()`: Main analysis execution method
- `test_availability()`: Framework availability testing
- `get_framework_name()`: Framework identification

### Utility Methods

- `_discover_patient_file_paths()`: Find patient data files
- `_process_temporal_data()`: Convert temporal data to timestamps
- `_start_performance_tracking()`: Begin performance monitoring
- `_end_performance_tracking()`: End performance monitoring
- `_get_performance_metrics()`: Retrieve performance data

### Performance Tracking

The base class includes comprehensive performance tracking:

- Execution duration
- Token usage
- Tool calls
- Success/failure rates
- Error tracking

## 🚀 Adding a New Framework

### Step 1: Create Integration Class

Create a new file `your_framework_integration.py`:

```python
from typing import Dict, Any, Optional
from .base_integration import BaseIntegration

class YourFrameworkIntegration(BaseIntegration):
    """Your framework-specific integration for agentic monitoring."""

    def __init__(self):
        super().__init__()
        self.framework_name = "YourFramework"
        # Initialize framework-specific components

    def test_availability(self) -> Dict[str, Any]:
        """Test if your framework is available and ready to run."""
        try:
            # Test framework availability
            # Import required modules
            # Check configuration
            return {
                "available": True,
                "message": "YourFramework is available and ready to run"
            }
        except Exception as e:
            return {
                "available": False,
                "error": f"Error testing YourFramework availability: {str(e)}"
            }

    def run_agentic_analysis(self, patient_name: str, run_id: Optional[str] = None,
                           timestamp: Optional[str] = None) -> Dict[str, Any]:
        """Run analysis using your framework."""
        # Start performance tracking
        self._start_performance_tracking()

        try:
            # Generate run_id if not provided
            if not run_id:
                run_id = f"run_{int(time.time())}"

            # Create logs directory
            logs_dir = Path(__file__).parent.parent / "agentic_monitor_logs"
            logs_dir.mkdir(exist_ok=True)

            # Use provided timestamp or generate fallback
            if timestamp:
                formatted_timestamp = timestamp
            else:
                formatted_timestamp = datetime.now().strftime('%Y_%m_%d_%H_%M')

            # Create execution log
            formatted_patient_name = patient_name.title() if patient_name else "Unknown"
            execution_log_file = logs_dir / f"{formatted_timestamp}_{formatted_patient_name}_execution_log.json"

            # Initialize your framework
            # Run analysis
            # Generate output files

            # End performance tracking with success
            self._end_performance_tracking(success=True)

            return {
                "success": True,
                "result": result,
                "run_id": run_id,
                "patient_name": patient_name,
                "framework": "yourframework",
                "execution_log": str(execution_log_file),
                "performance_metrics": self._get_performance_metrics()
            }

        except Exception as e:
            # End performance tracking with failure
            self._end_performance_tracking(success=False, error_message=str(e))

            return {
                "success": False,
                "error": f"Error running agentic analysis: {str(e)}",
                "run_id": run_id,
                "patient_name": patient_name,
                "framework": "yourframework",
                "performance_metrics": self._get_performance_metrics()
            }
```

### Step 2: Register Framework

Add your framework to the registry in `__init__.py`:

```python
from .your_framework_integration import YourFrameworkIntegration

FRAMEWORK_REGISTRY = {
    "crewai": CrewaiIntegration,
    "langgraph": LangGraphIntegration,
    "yourframework": YourFrameworkIntegration,  # Add this line
}

# Update __all__ list
__all__ = [
    "BaseIntegration",
    "CrewaiIntegration",
    "LangGraphIntegration",
    "YourFrameworkIntegration",  # Add this line
    "get_integration",
    "FRAMEWORK_REGISTRY"
]
```

### Step 3: Update Monitor Interface

Add your framework to the monitor dropdown in `../monitor.py`:

```python
solution_options = ["Crewai", "LangGraph", "YourFramework"]  # Add your framework
```

### Step 4: Implement Framework Logic

Your integration should:

1. **Inherit from BaseIntegration**: Get common utilities and performance tracking
2. **Implement Required Methods**: `run_agentic_analysis()` and `test_availability()`
3. **Use Shared Data Models**: Import from `agentic_types/models.py`
4. **Handle File Paths**: Use inherited methods for patient data discovery
5. **Write Structured Output**: Create files in `agentic_monitor_logs/` directory
6. **Follow Naming Conventions**: Use consistent file naming patterns

## 📊 Expected Output Files

All frameworks should generate these output files:

1. **Execution Log**: `{timestamp}_{patient_name}_execution_log.json`

   - Contains execution events, progress updates, and status
   - Used by monitoring app for progress tracking

2. **Biometric Analysis**: `{timestamp}_{patient_name}_biometric_analysis.json`

   - Contains biometric data analysis results
   - Uses `TrendInsightPayload` model

3. **Triage Decision**: `{timestamp}_{patient_name}_triage_decision.json`

   - Contains care decision and recommendations
   - Uses `DecisionPayload` model

4. **Medical Log**: `{timestamp}_{patient_name}_medical_log.json`
   - Contains comprehensive medical analysis
   - Uses `AgenticFinalOutput` model

## 🔍 Framework Registry

The framework registry allows dynamic framework discovery and instantiation:

```python
# Get integration instance
integration = get_integration("yourframework")

# Test availability
availability = integration.test_availability()

# Run analysis
result = integration.run_agentic_analysis("PatientName", "run_id", "timestamp")
```

## 📈 Performance Monitoring

All integrations include comprehensive performance tracking:

### Metrics Tracked

- **Execution Duration**: Total time for analysis
- **Token Usage**: LLM token consumption
- **Tool Calls**: Number of tool invocations
- **Success Rate**: Analysis completion rate
- **Error Tracking**: Failed executions and error messages

### Performance Data Structure

```python
{
    "duration_ms": 15000,
    "tokens_used": 2500,
    "tool_calls": 5,
    "success": True,
    "error_message": None,
    "start_time": "2025-01-01T10:00:00Z",
    "end_time": "2025-01-01T10:00:15Z"
}
```

## 🐛 Troubleshooting

### Common Issues

1. **Framework Not Found**: Check framework registration in `__init__.py`
2. **Import Errors**: Ensure all framework dependencies are installed
3. **File Path Issues**: Use inherited methods for patient data discovery
4. **Output Format**: Ensure output files match expected structure
5. **Performance Issues**: Monitor token usage and execution time

### Debug Mode

Enable debug logging:

```bash
export INTEGRATION_DEBUG=true
export LOG_LEVEL=DEBUG
```

### Testing Framework Integration

```bash
# Test framework availability
python -c "from patient.integrations import get_integration; print(get_integration('yourframework').test_availability())"

# Run analysis through UI
# Select your framework in the monitor dropdown and click "Run Analysis"
```

## 🔄 Getting Back Into Development

When returning to integration development:

1. **Review Framework Registry**: Check which frameworks are registered
2. **Test Existing Integrations**: Ensure CrewAI and LangGraph work
3. **Check Performance**: Review performance metrics and optimization opportunities
4. **Update Documentation**: Keep this README current with new frameworks
5. **Test New Frameworks**: Verify new framework integrations work correctly

## 📚 Additional Resources

- [Base Integration Class](base_integration.py)
- [CrewAI Integration](crewai_integration.py)
- [LangGraph Integration](langgraph_integration.py)
- [Shared Data Models](../../agentic_types/models.py)
- [Patient Monitoring System](../README.md)
- [CrewAI Solutions](../../crew/README.md)
- [LangGraph Solutions](../../langgraph_agents/README.md)

## 🤝 Contributing

1. **Follow Integration Patterns**: Use existing integrations as templates
2. **Maintain Compatibility**: Ensure new frameworks work with existing system
3. **Add Performance Tracking**: Include comprehensive performance monitoring
4. **Test Thoroughly**: Verify framework integration works end-to-end
5. **Document Changes**: Update this README for new frameworks
6. **Handle Errors Gracefully**: Implement proper error handling and logging
