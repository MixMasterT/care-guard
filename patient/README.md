# Patient Monitor

A Streamlit application that displays patient information from Synthea-generated FHIR data.

## Features

- 🎲 Random patient selection
- 👤 Patient demographics display
- 🏥 Diagnosis information with expandable details
- ⚠️ Allergy information
- 📊 Patient statistics
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

   - Click "🎲 Select Random Patient" for a random selection
   - Choose a specific patient from the dropdown list

2. **View Patient Information**: The main area displays:

   - Patient name and demographics
   - Diagnosis count and allergy count
   - Detailed diagnosis information (click "🔍 Show All Diagnoses")
   - Allergy details

3. **Navigate**: Use the expandable sections to view detailed information about each diagnosis and allergy.

## Data Structure

The application parses FHIR Bundle resources and extracts:

- **Patient**: Basic demographics, name, address
- **Condition**: Diagnosis codes, descriptions, clinical status
- **AllergyIntolerance**: Allergy information, criticality, categories

## File Structure

```
patient/
├── montor.py          # Main Streamlit application
├── requirements.txt   # Python dependencies
└── README.md         # This file
```

## Requirements

- Python 3.7+
- UV (for package management)
- Streamlit
- Synthea-generated FHIR data in JSON format
