from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from opensearchpy import OpenSearch
from opensearchpy.exceptions import NotFoundError, RequestError, ConnectionError
import json
import time
from datetime import datetime
from typing import Optional, Dict, Any, List

class OpenSearchInput(BaseModel):
    """Input schema for OpenSearch operations."""
    operation: str = Field(
        ..., 
        description="Operation to perform: 'create_index', 'index_document', 'search_documents', 'get_index_info', 'list_indices'"
    )
    index_name: Optional[str] = Field(
        default=None, 
        description="Name of the OpenSearch index"
    )
    document: Optional[Dict[str, Any]] = Field(
        default=None, 
        description="Document to index (for index_document operation)"
    )
    query: Optional[Dict[str, Any]] = Field(
        default=None, 
        description="Search query (for search_documents operation)"
    )
    mapping: Optional[Dict[str, Any]] = Field(
        default=None, 
        description="Index mapping configuration (for create_index operation)"
    )

class OpenSearchTool(BaseTool):
    name: str = "opensearch_client"
    description: str = """
    Interact with OpenSearch database for indexing and searching medical articles.
    
    Available operations:
    - create_index: Create a new index with specified mapping
    - index_document: Add a document to an existing index
    - search_documents: Search for documents in an index
    - get_index_info: Get information about an index
    - list_indices: List all available indices
    
    For medical knowledge base, use index_name 'medical-knowledge-base'.
    """
    args_schema: type[BaseModel] = OpenSearchInput

    def __init__(self):
        super().__init__()
        self._client = None
        self._connect_to_opensearch()

    def _connect_to_opensearch(self):
        """Establish connection to OpenSearch."""
        try:
            self._client = OpenSearch(
                hosts=[{'host': 'localhost', 'port': 9200}],
                http_compress=True,
                timeout=30
            )
            # Test connection
            self._client.ping()
        except Exception as e:
            raise ConnectionError(f"Failed to connect to OpenSearch: {str(e)}")

    def _wait_for_opensearch(self, max_retries=10, retry_delay=2):
        """Wait for OpenSearch to be ready."""
        for attempt in range(max_retries):
            try:
                self._client.ping()
                return True
            except Exception:
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                else:
                    return False
        return False

    def _run(self, operation: str, index_name: Optional[str] = None, 
             document: Optional[Dict[str, Any]] = None, 
             query: Optional[Dict[str, Any]] = None,
             mapping: Optional[Dict[str, Any]] = None) -> str:
        """Execute OpenSearch operations."""
        
        if not self._wait_for_opensearch():
            return "Error: OpenSearch is not available. Please ensure the service is running."

        try:
            if operation == "create_index":
                return self._create_index(index_name, mapping)
            elif operation == "index_document":
                return self._index_document(index_name, document)
            elif operation == "search_documents":
                return self._search_documents(index_name, query)
            elif operation == "get_index_info":
                return self._get_index_info(index_name)
            elif operation == "list_indices":
                return self._list_indices()
            else:
                return f"Error: Unknown operation '{operation}'. Available operations: create_index, index_document, search_documents, get_index_info, list_indices"
        except Exception as e:
            return f"Error during {operation}: {str(e)}"

    def _create_index(self, index_name: str, mapping: Optional[Dict[str, Any]] = None) -> str:
        """Create a new index with medical knowledge mapping."""
        
        if not index_name:
            return "Error: index_name is required for create_index operation"

        # Default mapping for medical knowledge base
        if not mapping:
            mapping = {
                "mappings": {
                    "properties": {
                        "title": {
                            "type": "text",
                            "analyzer": "standard"
                        },
                        "content": {
                            "type": "text",
                            "analyzer": "standard"
                        },
                        "source": {
                            "type": "keyword"
                        },
                        "url": {
                            "type": "keyword"
                        },
                        "publication_date": {
                            "type": "date"
                        },
                        "keywords": {
                            "type": "keyword"
                        },
                        "medical_terms": {
                            "type": "keyword"
                        },
                        "topic_category": {
                            "type": "keyword"
                        },
                        "relevance_score": {
                            "type": "float"
                        },
                        "indexed_at": {
                            "type": "date"
                        },
                        "article_type": {
                            "type": "keyword"
                        },
                        "author": {
                            "type": "text"
                        },
                        "institution": {
                            "type": "keyword"
                        }
                    }
                },
                "settings": {
                    "number_of_shards": 1,
                    "number_of_replicas": 0,
                    "index": {
                        "max_result_window": 10000
                    }
                }
            }

        try:
            # Check if index already exists
            if self._client.indices.exists(index=index_name):
                return f"Index '{index_name}' already exists"
            
            # Create the index
            response = self._client.indices.create(index=index_name, body=mapping)
            
            if response.get('acknowledged'):
                return f"Successfully created index '{index_name}' with medical knowledge mapping"
            else:
                return f"Failed to create index '{index_name}': {response}"
                
        except RequestError as e:
            return f"Error creating index '{index_name}': {str(e)}"

    def _index_document(self, index_name: str, document: Dict[str, Any]) -> str:
        """Index a medical article document."""
        
        if not index_name:
            return "Error: index_name is required for index_document operation"
        
        if not document:
            return "Error: document is required for index_document operation"

        # Add timestamp if not present
        if 'indexed_at' not in document:
            document['indexed_at'] = datetime.now().isoformat()

        try:
            # Check if index exists
            if not self._client.indices.exists(index=index_name):
                return f"Error: Index '{index_name}' does not exist. Create it first."

            # Index the document
            response = self._client.index(index=index_name, body=document)
            
            if response.get('result') in ['created', 'updated']:
                return f"Successfully indexed document with ID '{response['_id']}' in index '{index_name}'"
            else:
                return f"Unexpected response from indexing: {response}"
                
        except RequestError as e:
            return f"Error indexing document: {str(e)}"

    def _search_documents(self, index_name: str, query: Optional[Dict[str, Any]] = None) -> str:
        """Search for documents in an index."""
        
        if not index_name:
            return "Error: index_name is required for search_documents operation"

        # Default query to get all documents
        if not query:
            query = {
                "query": {
                    "match_all": {}
                },
                "size": 10
            }

        try:
            # Check if index exists
            if not self._client.indices.exists(index=index_name):
                return f"Error: Index '{index_name}' does not exist"

            # Perform search
            response = self._client.search(index=index_name, body=query)
            
            hits = response['hits']['hits']
            total = response['hits']['total']['value']
            
            if not hits:
                return f"No documents found in index '{index_name}'"
            
            # Format results
            results = []
            for hit in hits:
                source = hit['_source']
                results.append({
                    "id": hit['_id'],
                    "score": hit['_score'],
                    "title": source.get('title', 'No title'),
                    "source": source.get('source', 'Unknown'),
                    "topic_category": source.get('topic_category', 'Uncategorized')
                })
            
            return f"Found {total} documents in '{index_name}'. Top results:\n{json.dumps(results, indent=2)}"
            
        except RequestError as e:
            return f"Error searching documents: {str(e)}"

    def _get_index_info(self, index_name: str) -> str:
        """Get information about an index."""
        
        if not index_name:
            return "Error: index_name is required for get_index_info operation"

        try:
            # Check if index exists
            if not self._client.indices.exists(index=index_name):
                return f"Error: Index '{index_name}' does not exist"

            # Get index information
            mapping = self._client.indices.get_mapping(index=index_name)
            settings = self._client.indices.get_settings(index=index_name)
            stats = self._client.indices.stats(index=index_name)
            
            # Count documents
            count_response = self._client.count(index=index_name)
            doc_count = count_response['count']
            
            info = {
                "index_name": index_name,
                "document_count": doc_count,
                "mapping": mapping[index_name]['mappings'],
                "settings": settings[index_name]['settings']
            }
            
            return f"Index Information for '{index_name}':\n{json.dumps(info, indent=2)}"
            
        except RequestError as e:
            return f"Error getting index info: {str(e)}"

    def _list_indices(self) -> str:
        """List all available indices."""
        
        try:
            # Get all indices
            indices = self._client.cat.indices(format='json')
            
            if not indices:
                return "No indices found in OpenSearch"
            
            # Format the response
            index_list = []
            for index in indices:
                index_list.append({
                    "name": index['index'],
                    "health": index['health'],
                    "status": index['status'],
                    "docs_count": index['docs.count'],
                    "store_size": index['store.size']
                })
            
            return f"Available indices:\n{json.dumps(index_list, indent=2)}"
            
        except Exception as e:
            return f"Error listing indices: {str(e)}" 