#!/usr/bin/env python3
"""
Runner script for indexing medical records and pain diaries into OpenSearch.
"""

import sys
import os

# Add the parent directory to the path so we can import the indexer
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from opensearch.document_indexer import main

if __name__ == "__main__":
    print("Starting medical record indexing process...")
    main() 