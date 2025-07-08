#!/usr/bin/env python3
"""
Fallback search implementation that returns empty results on timeout
"""

import os
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class FallbackSearch:
    """Simple fallback search that always works"""
    
    def __init__(self, db_path="./chroma_db"):
        self.db_path = db_path
        logger.warning("Using fallback search - ChromaDB queries are hanging")
    
    def search(self, query: str, k: int = 10) -> List[Dict[str, Any]]:
        """Return empty results with warning"""
        logger.warning(f"Search for '{query}' using fallback - returning empty results")
        logger.warning("ChromaDB appears to be hanging on macOS. This is a known issue.")
        logger.warning("To fix: Consider using a different vector store or running on Linux")
        
        # Return a single dummy result to indicate the system is responsive
        return [{
            'content': f'[Search temporarily disabled] ChromaDB is hanging on macOS. Query was: "{query}"',
            'source': 'System Message',
            'page': '0',
            'type': 'error',
            'relevance_score': 0.0
        }]