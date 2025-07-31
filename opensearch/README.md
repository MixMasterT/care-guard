I# Medical Record Indexing System

This system indexes patient medical records and pain diary data into OpenSearch for efficient searching and analysis.

## Features

- **FHIR Medical Records Indexing**: Indexes all FHIR resources from patient medical record bundles
- **Pain Diary Indexing**: Indexes pain diary entries with structured data
- **Automatic Index Creation**: Creates properly mapped indices for both data types
- **Error Handling**: Robust error handling for file processing and indexing
- **Statistics**: Provides indexing statistics and document counts

## Prerequisites

1. **OpenSearch Server**: Ensure OpenSearch is running on `localhost:9200`
2. **Dependencies**: Install required Python packages:
   ```bash
   pip install opensearch-py
   ```

## Usage

### Quick Start

Start up the docker image:
```bash
cd opensearch
docker-compose up -d
```

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

## Search Examples

### Search for patients with high pain levels:

```json
{
  "query": {
    "range": {
      "pain_level": {
        "gte": 7
      }
    }
  }
}
```

### Search for specific patient's medical records:

```json
{
  "query": {
    "term": {
      "patient_id": "f420e6d4-55db-974f-05cb-52d06375b65f"
    }
  }
}
```

### Search for specific FHIR resource types:

```json
{
  "query": {
    "term": {
      "resource_type": "Observation"
    }
  }
}
```

## Error Handling

The system includes comprehensive error handling for:

- Missing directories
- Invalid JSON files
- OpenSearch connection issues
- Index creation failures
- File processing errors

## Performance Considerations

- Large FHIR bundles are processed entry by entry
- Each resource is indexed individually for better search granularity
- Metadata is added to track source files and indexing timestamps
- Proper index mappings ensure efficient searching

## Monitoring

The system provides detailed logging and statistics:

- Number of files processed
- Number of records indexed per file
- Total indexing statistics
- Index document counts 

---

## How to Fix

### 1. Explicitly Map the Field as `float`
You need to set the mapping for `resource_data.item.adjudication.amount.value` to `float` (which can store both integers and decimals) before any data is indexed.

#### Steps:
- Delete the existing `fhir-medical-records` index (to clear the old mapping).
- Update your mapping to explicitly set this field as `float`.
- Recreate the index with the new mapping.
- Re-run the indexer.

---

### 2. How to Update Your Mapping

Update the FHIR mapping in your Python code like this:

```python
fhir_mapping = {
    "mappings": {
        "properties": {
            "resource_type": {"type": "keyword"},
            "patient_id": {"type": "keyword"},
            "resource_id": {"type": "keyword"},
            "resource_data": {
                "type": "object",
                "dynamic": True,
                "properties": {
                    "item": {
                        "type": "object",
                        "dynamic": True,
                        "properties": {
                            "adjudication": {
                                "type": "object",
                                "dynamic": True,
                                "properties": {
                                    "amount": {
                                        "type": "object",
                                        "dynamic": True,
                                        "properties": {
                                            "value": {"type": "float"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "source_file": {"type": "keyword"},
            "indexed_at": {"type": "date"}
        }
    }
}
```

---

### 3. Delete and Recreate the Index

You can do this in your code (as you already do), or manually via OpenSearch Dashboards/Dev Tools:

```json
DELETE fhir-medical-records
```

Then let your script recreate it with the new mapping.

---

### 4. Re-run the Indexer

After the above changes, re-run your indexer. The error should be resolved, and both integer and decimal values will be accepted for that field.

---

**Summary:**  
- The error is due to OpenSearch type rigidity.
- Explicitly set the mapping for `resource_data.item.adjudication.amount.value` to `float`.
- Delete and recreate the index, then re-index.

Would you like me to update your code with the correct mapping? 