I# Medical Record Indexing System

This system indexes FHIR records and pain diary data into OpenSearch for efficient searching and analysis.

## Prerequisites

Docker must be installed.

## Usage

### Quick Start

Start up the docker image:
```bash
cd opensearch
docker-compose up -d
```

This Docker image will start up Opensearch and run an indexing process to index pain diaries and FHIR data.

A file named `rag_agent.py` gives an example of how to query the data in Opensearch. To run:

```bash
cd care-guard
uv run python -m opensearch.rag_agent
```

To spin down the Opensearch instance
```bash
cd opensearch
docker-compose down
```

Note that the indexes will be dropped, and the data will be re-indexed the next time the containers are started.

## Using the Dashboard

Navigate to http://localhost:5601/app/opensearch_index_management_dashboards#/indices and you should see `pain-diaries` and `fhir-medical-records` with some number of documents.

Go to Dashboard Management, then Index patterns.
Create a pattern for pain-diaries and fhir-, choosing date as the date field.

## Data Structure

### Pain Diaries Index (`pain-diaries`)

Each pain diary entry is indexed with the following structure:

```json
{
  "patient_id": "f420e6d4-55db-974f-05cb-52d06375b65f",
  "date": "2025-07-02",
  "pain_level": 8,
  "sleep_quality": 3,
  "mood": "low",
  "notes": "Very sore all day. Sleep was poor. Felt discouraged.",
  "source_file": "Allen322_Hickle134_f420e6d4-55db-974f-05cb-52d06375b65f.json",
  "indexed_at": "2024-01-15T10:30:00"
}
```

### FHIR Medical Records Index (`fhir-medical-records`)

Each FHIR resource is indexed with the following structure:

```json
{
  "resource_type": "Patient",
  "patient_id": "4403cbc3-78eb-fbe6-e5c5-bee837f31ea9",
  "resource_id": "4403cbc3-78eb-fbe6-e5c5-bee837f31ea9",
  "resource_data": { /* Full FHIR resource object */ },
  "source_file": "Zachery872_Cole117_4403cbc3-78eb-fbe6-e5c5-bee837f31ea9.json",
  "indexed_at": "2024-01-15T10:30:00"
}
```

## Directory Structure

The system expects the following directory structure:

```
patient/
└── generated_medical_records/
    ├── fhir/
    │   ├── patient_record_1.json
    │   ├── patient_record_2.json
    │   └── ...
    └── pain_diaries/
        ├── patient_pain_diary_1.json
        ├── patient_pain_diary_2.json
        └── ...
```

