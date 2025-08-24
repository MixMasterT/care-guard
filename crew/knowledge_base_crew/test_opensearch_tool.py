#!/usr/bin/env python3
"""
Test script for the OpenSearch tool in isolation.
This script tests the basic functionality of the OpenSearch tool before running the full crew.
"""

import sys
import os
import json
from datetime import datetime

# Add the src directory to the path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from knowledge_base_crew.tools.opensearch_tool import OpenSearchTool
from knowledge_base_crew.tools.knowledge_base_indexing import (
    create_medical_document, 
    TopicCategory, 
    ArticleType
)

def test_opensearch_connection():
    """Test basic OpenSearch connection."""
    print("🔍 Testing OpenSearch connection...")
    
    try:
        tool = OpenSearchTool()
        print("✅ OpenSearch tool initialized successfully")
        return tool
    except Exception as e:
        print(f"❌ Failed to initialize OpenSearch tool: {e}")
        print("💡 Make sure OpenSearch is running: docker-compose up -d")
        return None

def test_list_indices(tool):
    """Test listing indices."""
    print("\n📋 Testing list_indices operation...")
    
    try:
        result = tool._run("list_indices")
        print(f"✅ List indices result:\n{result}")
        return True
    except Exception as e:
        print(f"❌ Failed to list indices: {e}")
        return False

def test_create_index(tool):
    """Test creating the medical knowledge base index."""
    print("\n🏗️ Testing create_index operation...")
    
    try:
        result = tool._run("create_index", index_name="medical-knowledge-base")
        print(f"✅ Create index result:\n{result}")
        return True
    except Exception as e:
        print(f"❌ Failed to create index: {e}")
        return False

def test_index_document(tool):
    """Test indexing a sample medical document."""
    print("\n📄 Testing index_document operation...")
    
    try:
        # Create a sample medical document
        sample_doc = create_medical_document(
            title="Sample Post-Operative Cardiac Monitoring Guidelines",
            content="This is a sample medical article about post-operative cardiac monitoring. It covers vital signs monitoring, warning signs, and intervention protocols for cardiac surgery patients.",
            source="Test Medical Journal",
            topic_category=TopicCategory.PATIENT_MONITORING,
            url="https://example.com/sample-article",
            publication_date=datetime.now(),
            author="Dr. Test Author",
            institution="Test Medical Center",
            article_type=ArticleType.CLINICAL_GUIDELINE,
            keywords=["cardiac", "post-operative", "monitoring", "vital signs"],
            medical_terms=["heart_rate", "blood_pressure", "spo2", "temperature"],
            relevance_score=0.95
        )
        
        # Convert to dictionary for indexing
        doc_dict = sample_doc.dict()
        
        result = tool._run("index_document", index_name="medical-knowledge-base", document=doc_dict)
        print(f"✅ Index document result:\n{result}")
        return True
    except Exception as e:
        print(f"❌ Failed to index document: {e}")
        return False

def test_search_documents(tool):
    """Test searching for documents."""
    print("\n🔍 Testing search_documents operation...")
    
    try:
        # Test a simple search
        result = tool._run("search_documents", index_name="medical-knowledge-base")
        print(f"✅ Search documents result:\n{result}")
        return True
    except Exception as e:
        print(f"❌ Failed to search documents: {e}")
        return False

def test_get_index_info(tool):
    """Test getting index information."""
    print("\nℹ️ Testing get_index_info operation...")
    
    try:
        result = tool._run("get_index_info", index_name="medical-knowledge-base")
        print(f"✅ Get index info result:\n{result}")
        return True
    except Exception as e:
        print(f"❌ Failed to get index info: {e}")
        return False

def main():
    """Run all tests."""
    print("🚀 Starting OpenSearch Tool Tests")
    print("=" * 50)
    
    # Test connection
    tool = test_opensearch_connection()
    if not tool:
        print("\n❌ Cannot proceed without OpenSearch connection")
        return
    
    # Run all tests
    tests = [
        ("List Indices", lambda: test_list_indices(tool)),
        ("Create Index", lambda: test_create_index(tool)),
        ("Index Document", lambda: test_index_document(tool)),
        ("Search Documents", lambda: test_search_documents(tool)),
        ("Get Index Info", lambda: test_get_index_info(tool))
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Print summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    print("=" * 50)
    
    passed = 0
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {test_name}")
        if success:
            passed += 1
    
    print(f"\n🎯 Overall: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All tests passed! OpenSearch tool is ready for use.")
    else:
        print("⚠️ Some tests failed. Please check the errors above.")
        print("💡 Make sure OpenSearch is running and accessible at localhost:9200")

if __name__ == "__main__":
    main() 