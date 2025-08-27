# Patient Monitor

A Streamlit application that displays patient information from Synthea-generated FHIR data with integrated agentic AI analysis capabilities.

## Features

- 🎲 Dropdown patient selection
- 👤 Patient demographics display
- 🏥 Biometric scenarios -- 5 minute biometric streams for three scenarios: regular, irregular, and critical
- 🎨 Modern, responsive UI
- 🤖 **Agentic AI Integration** -- CrewAI-powered patient analysis with real-time monitoring

## Setup

### Using UV (Recommended)

1. Create a virtual environment and install dependencies:

```bash
uv venv
uv pip install -r requirements.txt
```

2. Activate the virtual environment:

```bash
source .venv/bin/activate  # On macOS/Linux
# or
.venv\Scripts\activate     # On Windows
```

### Alternative: Using pip

1. Install the required dependencies:

```bash
pip install -r requirements.txt
```

2. Ensure you have Synthea-generated FHIR data in the `../synthea/output/fhir/` directory.

## Running the Application

Run the Streamlit app on port 8501:

```bash
streamlit run monitor.py --server.port 8501
```

The application will be available at `http://localhost:8501`

## Usage

1. **Select a Patient**: Use the sidebar to choose a patient from the dropdown list

   - Allen is A-OK, Mark is just so-so, and Zach is really struggling

2. **View Patient Information**: The main area displays:

   - Patient name and demographics
   - Diagnosis information

3. **Run Agentic Analysis**:
   - Click "🚀 Run Analysis" in the sidebar
   - Agentic monitor opens in new window (port 8502)
   - Monitor progress using refresh button
   - View structured results when complete

## Agentic AI Framework Integration

The patient monitor now includes a modular agentic AI framework system that allows you to add new AI analysis solutions alongside the existing CrewAI implementation.

### Current Frameworks

- **CrewAI** (`crew/cardio_monitor/`): Multi-agent patient analysis system
  - Biometric Data Reviewer
  - Senior Cardiac Care Triage Nurse
  - Medical Records Specialist

### Adding a New Framework

To add a new agentic AI framework:

1. **Create Framework Directory**:

   ```bash
   mkdir -p crew/your_framework_name/src/your_framework_name
   ```

2. **Implement Framework Interface**:

   - Create `crew.py` with a main crew class
   - Implement `crew()` method that returns a crew object
   - Ensure compatibility with `agentic_monitor_integration.py`

3. **Update Integration Layer**:

   - Modify `agentic_monitor_integration.py` to support your framework
   - Add framework detection logic
   - Implement framework-specific execution paths

4. **Update UI**:
   - Add framework option to the dropdown in `monitor.py`
   - Implement framework-specific progress monitoring
   - Handle framework-specific output formats

### Framework Requirements

Your framework must provide:

- **Crew/Agent Definition**: Clear agent roles and capabilities
- **Task Execution**: Structured task processing
- **Output Format**: Consistent result structure
- **Error Handling**: Robust error management
- **Progress Reporting**: Real-time execution status

See `crew/cardio_monitor/` for a complete implementation example.

## Data Structure

The application parses FHIR Bundle resources and extracts:

- **Patient**: Basic demographics, name, address
- **Condition**: Diagnosis codes, descriptions, clinical status
- **AllergyIntolerance**: Allergy information, criticality, categories

The application also works together with the biometric_scenario_server (see `biometric_scenario_server.py`)
to run pseudo scenarios with various biometric streamed from the scenario server.

The monitor.py application receives these biometrics through a TCP connection, and then writes them in batches to:
`biometric/buffer/simulation_biometrics.json`.

Agentic monitoring solutions consume the content from `simulation_biometrics.json` along with other health data.
