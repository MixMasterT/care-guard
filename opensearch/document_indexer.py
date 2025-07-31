import json
import os
import glob
import time
from datetime import datetime
from opensearchpy import OpenSearch
from opensearchpy.exceptions import NotFoundError, RequestError, ConnectionError

class MedicalRecordIndexer:
    def __init__(self, hosts=[{'host': 'opensearch', 'port': 9200}], http_compress=True):
        """Initialize the OpenSearch client and create indices if they don't exist."""
        self.client = OpenSearch(hosts=hosts, http_compress=http_compress)
        self.setup_indices()
    
    def wait_for_opensearch(self, max_retries=60, retry_delay=3):
        """Wait for OpenSearch to be ready before proceeding."""
        print("Waiting for OpenSearch to be ready...")
        for attempt in range(max_retries):
            try:
                # Try to ping OpenSearch
                self.client.ping()
                # Also try a simple cluster health check to ensure it's fully ready
                health = self.client.cluster.health()
                if health['status'] in ['green', 'yellow']:
                    print("OpenSearch is ready!")
                    return True
                else:
                    print(f"OpenSearch cluster status: {health['status']}, waiting...")
            except (ConnectionError, Exception) as e:
                if attempt < max_retries - 1:
                    print(f"OpenSearch not ready yet (attempt {attempt + 1}/{max_retries}), retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                else:
                    print(f"Failed to connect to OpenSearch after {max_retries} attempts: {e}")
                    return False
        return False

    def setup_indices(self):
        """Create indices with proper mappings for medical records and pain diaries."""
        # Wait for OpenSearch to be ready first
        if not self.wait_for_opensearch():
            raise Exception("OpenSearch is not available")
        
        # Pain diaries index mapping
        pain_diaries_mapping = {
            "mappings": {
                "properties": {
                    "patient_id": {"type": "keyword"},
                    "date": {"type": "date"},
                    "pain_level": {"type": "integer"},
                    "sleep_quality": {"type": "integer"},
                    "mood": {"type": "keyword"},
                    "notes": {"type": "text"},
                    "source_file": {"type": "keyword"},
                    "indexed_at": {"type": "date"}
                }
            }
        }
        
        # FHIR medical records index mapping
        fhir_mapping = {
            "mappings": {
                "properties": {
                    "resource_type": {"type": "keyword"},
                    "patient_id": {"type": "keyword"},
                    "resource_id": {"type": "keyword"},
                    "resource_data": {
                        "type": "object",
                        "dynamic": True
                    },
                    "source_file": {"type": "keyword"},
                    "indexed_at": {"type": "date"}
                }
            }
        }
        
        # Create pain diaries index with retry
        for attempt in range(3):
            try:
                self.client.indices.create(index="pain-diaries", body=pain_diaries_mapping)
                print("Created pain-diaries index")
                break
            except RequestError as e:
                if "resource_already_exists_exception" in str(e):
                    print("Pain-diaries index already exists")
                    break
                elif attempt < 2:
                    print(f"Error creating pain-diaries index (attempt {attempt + 1}), retrying...")
                    time.sleep(2)
                else:
                    print(f"Failed to create pain-diaries index after 3 attempts: {e}")
            except Exception as e:
                if attempt < 2:
                    print(f"Unexpected error creating pain-diaries index (attempt {attempt + 1}), retrying...")
                    time.sleep(2)
                else:
                    print(f"Failed to create pain-diaries index: {e}")
        
        # Create FHIR medical records index with retry
        for attempt in range(3):
            try:
                self.client.indices.create(index="fhir-medical-records", body=fhir_mapping)
                print("Created fhir-medical-records index")
                break
            except RequestError as e:
                if "resource_already_exists_exception" in str(e):
                    print("Fhir-medical-records index already exists")
                    break
                elif attempt < 2:
                    print(f"Error creating fhir-medical-records index (attempt {attempt + 1}), retrying...")
                    time.sleep(2)
                else:
                    print(f"Failed to create fhir-medical-records index after 3 attempts: {e}")
            except Exception as e:
                if attempt < 2:
                    print(f"Unexpected error creating fhir-medical-records index (attempt {attempt + 1}), retrying...")
                    time.sleep(2)
                else:
                    print(f"Failed to create fhir-medical-records index: {e}")
        
        # Check if index exists and has documents, if so, delete and recreate to avoid mapping conflicts
        try:
            stats = self.client.indices.stats(index="fhir-medical-records")
            doc_count = stats['indices']['fhir-medical-records']['total']['docs']['count']
            if doc_count > 0:
                print(f"Found {doc_count} existing documents in fhir-medical-records index. Deleting and recreating to avoid mapping conflicts...")
                self.client.indices.delete(index="fhir-medical-records")
                time.sleep(2)
                self.client.indices.create(index="fhir-medical-records", body=fhir_mapping)
                print("Recreated fhir-medical-records index")
        except Exception as e:
            print(f"Error checking/recreating fhir-medical-records index: {e}")
        
        # Also check and recreate pain-diaries index if needed
        try:
            stats = self.client.indices.stats(index="pain-diaries")
            doc_count = stats['indices']['pain-diaries']['total']['docs']['count']
            if doc_count > 0:
                print(f"Found {doc_count} existing documents in pain-diaries index. Deleting and recreating to avoid mapping conflicts...")
                self.client.indices.delete(index="pain-diaries")
                time.sleep(2)
                self.client.indices.create(index="pain-diaries", body=pain_diaries_mapping)
                print("Recreated pain-diaries index")
        except Exception as e:
            print(f"Error checking/recreating pain-diaries index: {e}")
    
    def index_pain_diaries(self, pain_diaries_dir):
        """Index all pain diary records from the specified directory."""
        print(f"Indexing pain diaries from: {pain_diaries_dir}")
        
        # Find all JSON files in the pain diaries directory
        json_files = glob.glob(os.path.join(pain_diaries_dir, "*.json"))
        
        indexed_count = 0
        for file_path in json_files:
            if os.path.basename(file_path) == "prompts.md":
                continue  # Skip the prompts file
                
            try:
                with open(file_path, 'r') as f:
                    pain_diary_records = json.load(f)
                
                # Index each pain diary entry
                for record in pain_diary_records:
                    # Add metadata
                    record['source_file'] = os.path.basename(file_path)
                    record['indexed_at'] = datetime.now().isoformat()
                    
                    # Index the document
                    self.client.index(
                        index="pain-diaries",
                        body=record
                    )
                    indexed_count += 1
                
                print(f"Indexed {len(pain_diary_records)} records from {os.path.basename(file_path)}")
                
            except Exception as e:
                print(f"Error processing {file_path}: {e}")
        
        print(f"Total pain diary records indexed: {indexed_count}")
        return indexed_count
    
    def index_fhir_medical_records(self, fhir_dir):
        """Index all FHIR medical records from the specified directory."""
        print(f"Indexing FHIR medical records from: {fhir_dir}")
        
        # Find all JSON files in the FHIR directory
        json_files = glob.glob(os.path.join(fhir_dir, "*.json"))
        
        indexed_count = 0
        for file_path in json_files:
            try:
                with open(file_path, 'r') as f:
                    fhir_bundle = json.load(f)
                
                # Extract patient ID from filename or bundle
                filename = os.path.basename(file_path)
                patient_id = None
                
                # Try to extract patient ID from filename
                if "_" in filename:
                    parts = filename.split("_")
                    if len(parts) >= 2:
                        patient_id = parts[-1].replace(".json", "")
                
                # Process each entry in the FHIR bundle
                if fhir_bundle.get("resourceType") == "Bundle" and "entry" in fhir_bundle:
                    for entry in fhir_bundle["entry"]:
                        if "resource" in entry:
                            resource = entry["resource"]
                            resource_type = resource.get("resourceType", "Unknown")
                            resource_id = resource.get("id", "unknown")
                            
                            # Create document for indexing
                            doc = {
                                "resource_type": resource_type,
                                "resource_id": resource_id,
                                "resource_data": resource,
                                "source_file": filename,
                                "indexed_at": datetime.now().isoformat()
                            }
                            
                            # Add patient ID if available
                            if patient_id:
                                doc["patient_id"] = patient_id
                            elif resource_type == "Patient" and "id" in resource:
                                doc["patient_id"] = resource["id"]
                            
                            # Index the document with error handling
                            try:
                                self.client.index(
                                    index="fhir-medical-records",
                                    body=doc
                                )
                                indexed_count += 1
                            except Exception as e:
                                print(f"Failed to index FHIR resource {resource_id} from {filename}: {e}")
                                # Continue with next resource instead of failing entire file
                
                print(f"Indexed {len(fhir_bundle.get('entry', []))} FHIR resources from {filename}")
                
            except Exception as e:
                print(f"Error processing {file_path}: {e}")
        
        print(f"Total FHIR medical record resources indexed: {indexed_count}")
        return indexed_count
    
    def index_all_records(self, fhir_dir, pain_diaries_dir):
        """Index all medical records and pain diaries."""
        print("Starting comprehensive medical record indexing...")
        
        # Test connection one more time before starting
        try:
            self.client.ping()
            print("Connection test successful, proceeding with indexing...")
        except Exception as e:
            print(f"Connection test failed: {e}")
            return 0
        
        # Index FHIR medical records
        fhir_count = self.index_fhir_medical_records(fhir_dir)
        
        # Index pain diaries
        pain_count = self.index_pain_diaries(pain_diaries_dir)
        
        print(f"\nIndexing complete!")
        print(f"FHIR medical record resources indexed: {fhir_count}")
        print(f"Pain diary records indexed: {pain_count}")
        print(f"Total records indexed: {fhir_count + pain_count}")
        
        return fhir_count + pain_count
    
    def get_index_stats(self):
        """Get statistics about the indexed data."""
        try:
            pain_stats = self.client.indices.stats(index="pain-diaries")
            fhir_stats = self.client.indices.stats(index="fhir-medical-records")
            
            print("\nIndex Statistics:")
            print(f"Pain Diaries Index - Documents: {pain_stats['indices']['pain-diaries']['total']['docs']['count']}")
            print(f"FHIR Medical Records Index - Documents: {fhir_stats['indices']['fhir-medical-records']['total']['docs']['count']}")
            
        except Exception as e:
            print(f"Error getting index stats: {e}")

def main():
    """Main function to run the indexing process."""
    # Initialize the indexer
    indexer = MedicalRecordIndexer()
    
    # Define paths
    fhir_dir = "patient/generated_medical_records/fhir"
    pain_diaries_dir = "patient/generated_medical_records/pain_diaries"
    
    # Check if directories exist
    if not os.path.exists(fhir_dir):
        print(f"Error: FHIR directory not found: {fhir_dir}")
        return
    
    if not os.path.exists(pain_diaries_dir):
        print(f"Error: Pain diaries directory not found: {pain_diaries_dir}")
        return
    
    # Index all records
    total_indexed = indexer.index_all_records(fhir_dir, pain_diaries_dir)
    
    # Get statistics
    indexer.get_index_stats()
    
    print(f"\nSuccessfully indexed {total_indexed} total records!")

if __name__ == "__main__":
    main()
