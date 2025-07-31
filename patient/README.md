# Patient Monitor

A Streamlit application that displays patient information from Synthea-generated FHIR data.

## Features

- 🎲 Dropdown atient selection
- 👤 Patient demographics display
- 🏥 Biometric scenarios -- 5 minute biometric streams for three scenarios: regular, irregular, and critical
- 🎨 Modern, responsive UI

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

Run the Streamlit app on port 8091:

```bash
streamlit run monitor.py --server.port 8091
```

The application will be available at `http://localhost:8091`

## Usage

1. **Select a Patient**: Use the sidebar to either:

   - Choose a patient from the dropdown list, Allen is A-OK, Mark is just so-so, and Zach is really struggling

2. **View Patient Information**: The main area displays:

   - Patient name and demographics
   - Diagnosis information

## Data Structure

The application parses FHIR Bundle resources and extracts:

- **Patient**: Basic demographics, name, address
- **Condition**: Diagnosis codes, descriptions, clinical status
- **AllergyIntolerance**: Allergy information, criticality, categories

The application also works together with the biometric_scenario_server (see `biometric_scenario_server.py`)
to run pseudo scenarios with various biometric streamed from the scenario server.

The monitor.py application receives these biometrics through a TCP connection, and then writes them in batches to:
`biometric/buffer/simulation_biometrics.json`.

Agentic monitoring solutions should consume the content from `simulation_biometrics.json` along with other health data.
