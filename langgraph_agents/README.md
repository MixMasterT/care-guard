# LangGraph Solutions - Care Guard Agentic AI

This directory contains LangGraph-based agentic AI solutions for patient monitoring and medical analysis.

## 📁 Directory Structure

```
langgraph_agents/
├── workflows/                   # LangGraph workflow implementations
│   ├── patient_monitoring_workflow.py  # Main patient monitoring workflow
│   ├── heartbeat_workflow.py           # Heartbeat classification workflow
│   └── __init__.py
├── agents/                      # Individual agent implementations
│   ├── heartbeat_classification.py    # Heartbeat classification agent
│   └── __init__.py
├── main.py                      # Entry point and workflow execution
├── README.md                    # This file
└── __init__.py
```

## 🚀 Quick Start

### Prerequisites

- Python 3.12+
- UV package manager
- OpenAI API key
- OpenSearch (optional, for RAG features)

### Installation

```bash
# From project root
uv sync
```

### Running LangGraph Solutions

#### Patient Monitoring Workflow

```bash
# Run directly
python langgraph_agents/workflows/patient_monitoring_workflow.py

# Or through main entry point
python langgraph_agents/main.py
```

#### Heartbeat Classification

```bash
python langgraph_agents/workflows/heartbeat_workflow.py
```

## 🏥 Patient Monitoring Workflow

**Purpose**: Comprehensive patient monitoring and analysis using LangGraph state management.

### Features

- **State-Based Workflow**: Uses LangGraph StateGraph for structured execution
- **Biometric Analysis**: Reviews heart rate, SpO2, blood pressure, and other vital signs
- **Triage Decision Making**: Determines appropriate care actions based on biometric data
- **Medical Logging**: Creates structured medical logs with findings and recommendations
- **RAG Integration**: Uses OpenSearch for enhanced medical context
- **Error Handling**: Conditional edges for graceful error handling

### Workflow Steps

1. **Load Biometric Data**: Reads biometric data from simulation buffer
2. **Biometric Reviewer**: Analyzes biometric data and identifies anomalies
3. **Load Patient Data**: Retrieves patient history using OpenSearch RAG
4. **Triage Nurse**: Makes care decisions based on analysis
5. **Log Writer**: Creates comprehensive medical logs

### State Management

The workflow uses `LangGraphState` TypedDict for state management:

```python
class LangGraphState(TypedDict):
    biometric_data: list
    biometric_analysis: TrendInsightPayload | None
    pain_diary_data: list
    weight_data: list
    fhir_records: dict
    patient_context: dict
    triage_decision: DecisionPayload | None
    medical_log: AgenticFinalOutput | None
    # ... execution tracking fields
```

### Output Files

The workflow generates four output files:

- `{timestamp}_{patient_name}_execution_log.json`
- `{timestamp}_{patient_name}_biometric_analysis.json`
- `{timestamp}_{patient_name}_triage_decision.json`
- `{timestamp}_{patient_name}_medical_log.json`

## 💓 Heartbeat Classification Workflow

**Purpose**: Specialized workflow for heartbeat rhythm classification and analysis.

### Features

- **Rhythm Classification**: Identifies normal, irregular, and critical heart rhythms
- **Real-time Analysis**: Processes streaming heartbeat data
- **Pattern Recognition**: Uses LLM for rhythm pattern analysis
- **Alert System**: Generates alerts for critical rhythms

### Integration

The heartbeat classification workflow can be used:

- As a standalone analysis tool
- Integrated into the main patient monitoring workflow
- For real-time rhythm monitoring

## 🔧 Development

### Adding a New Workflow

1. **Create Workflow File**

   ```python
   # workflows/new_workflow.py
   from langgraph.graph import StateGraph, START, END
   from typing import TypedDict

   class NewWorkflowState(TypedDict):
       # Define your state structure
       pass

   def create_new_workflow():
       workflow = StateGraph(NewWorkflowState)
       # Add nodes and edges
       return workflow.compile()
   ```

2. **Define State Structure**

   - Use TypedDict for type safety
   - Include all necessary data fields
   - Add execution tracking fields

3. **Implement Workflow Steps**

   - Create functions for each workflow step
   - Handle errors gracefully
   - Update state appropriately

4. **Add Conditional Logic**
   - Use `add_conditional_edges` for error handling
   - Implement proper state transitions

### Testing

```bash
# Run workflow tests
python -m pytest tests/

# Test specific workflow
python langgraph_agents/workflows/patient_monitoring_workflow.py
```

### Configuration

LangGraph workflows use:

- **Environment Variables**: For API keys and configuration
- **Pydantic Models**: For structured data validation
- **OpenSearch**: For RAG features (optional)

## 🔗 Integration with Main System

### Data Flow

```
Patient Monitor → Integration Layer → LangGraph Workflow → Analysis Results → Logs
```

### Shared Components

- **Data Models**: Uses `agentic_types/models.py` for consistent output
- **File Discovery**: Inherits from `BaseIntegration` for patient data access
- **Logging**: Writes structured logs to `patient/agentic_monitor_logs/`

### Framework Registry

LangGraph is registered in `patient/integrations/__init__.py`:

```python
FRAMEWORK_REGISTRY = {
    "langgraph": LangGraphIntegration,
    # Other frameworks...
}
```

## 📊 Performance Monitoring

The system includes performance tracking for:

- **Execution Time**: Duration of workflow execution
- **Token Usage**: LLM token consumption
- **Tool Calls**: Number of LLM invocations
- **State Transitions**: Workflow step completion
- **Error Rates**: Failed workflow steps

## 🐛 Troubleshooting

### Common Issues

1. **Pydantic Validation Errors**: Ensure data models match expected structure
2. **OpenAI API**: Verify API key is set in `.env` file
3. **OpenSearch**: Ensure OpenSearch is running for RAG features
4. **State Management**: Check state transitions and error handling

### Debug Mode

Enable debug logging:

```bash
export LANGGRAPH_DEBUG=true
export LOG_LEVEL=DEBUG
```

### Workflow Debugging

- Check state at each step
- Verify conditional edge logic
- Monitor token usage and performance
- Review error handling paths

## 📈 Future Enhancements

- **Advanced State Management**: More sophisticated state handling
- **Parallel Execution**: Concurrent workflow steps
- **Custom Tools**: Additional medical analysis tools
- **Performance Optimization**: Improved execution speed
- **Enhanced RAG**: Better medical knowledge integration
- **Multi-Patient Support**: Concurrent patient analysis

## 🤝 Contributing

1. **Follow LangGraph Best Practices**: Use proper state management
2. **Maintain Type Safety**: Use TypedDict for state definitions
3. **Add Error Handling**: Implement conditional edges for errors
4. **Include Tests**: Add comprehensive test coverage
5. **Document Workflows**: Update README files for new features
6. **Performance**: Monitor and optimize workflow execution

## 📚 Additional Resources

- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [LangChain Documentation](https://python.langchain.com/)
- [Integration Layer Documentation](../patient/integrations/README.md)
- [Shared Data Models](../agentic_types/models.py)
- [Patient Monitoring System](../patient/README.md)

## 🔄 Getting Back Into Development

When returning to LangGraph development:

1. **Review Workflow Structure**: Understand state management and step flow
2. **Check Integration**: Verify LangGraph integration with main system
3. **Test Workflows**: Run both patient monitoring and heartbeat classification
4. **Review Logs**: Check recent execution logs for issues
5. **Update Dependencies**: Ensure LangGraph and LangChain are up to date
