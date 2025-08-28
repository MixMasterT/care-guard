"""
Knowledge Crew Integration

Simple integration script for the knowledge_base_crew to index research articles
into OpenSearch using the existing infrastructure.
"""

import sys
import os
from pathlib import Path

# Add the opensearch directory to the path
opensearch_dir = Path(__file__).parent
if str(opensearch_dir) not in sys.path:
    sys.path.insert(0, str(opensearch_dir))

from medical_knowledge_indexer import MedicalKnowledgeIndexer

def index_research_articles(articles_data):
    """
    Index research articles from the knowledge_base_crew into OpenSearch.
    
    Args:
        articles_data: List of article dictionaries from the research crew
        
    Returns:
        Dict with indexing results
    """
    try:
        # Initialize the medical knowledge indexer
        indexer = MedicalKnowledgeIndexer()
        
        # Index all articles
        results = indexer.index_multiple_articles(articles_data)
        
        # Get final stats
        stats = indexer.get_index_stats()
        
        return {
            "success": True,
            "indexing_results": results,
            "final_stats": stats,
            "message": f"Successfully indexed {results['success']} articles"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to index articles"
        }

def search_medical_knowledge(query, category=None, topic=None, size=10):
    """
    Search the medical knowledge base.
    
    Args:
        query: Search query text
        category: Filter by category (optional)
        topic: Filter by topic (optional)
        size: Maximum number of results
        
    Returns:
        List of matching documents
    """
    try:
        indexer = MedicalKnowledgeIndexer()
        return indexer.search_medical_knowledge(query, category, topic, size)
    except Exception as e:
        print(f"❌ Error searching medical knowledge: {e}")
        return []

def get_knowledge_base_stats():
    """Get statistics about the medical knowledge base."""
    try:
        indexer = MedicalKnowledgeIndexer()
        return indexer.get_index_stats()
    except Exception as e:
        return {"error": str(e)}

# Example usage
if __name__ == "__main__":
    # Test the integration
    print("🧪 Testing Knowledge Crew Integration...")
    
    # Test stats
    stats = get_knowledge_base_stats()
    print(f"📊 Current knowledge base stats: {stats}")
    
    # Test search
    results = search_medical_knowledge("cardiac monitoring", size=5)
    print(f"🔍 Search test results: {len(results)} documents found")
    
    print("✅ Integration test complete!")
