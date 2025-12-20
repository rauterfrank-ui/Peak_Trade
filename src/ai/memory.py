"""
Memory and context management for AI agents.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime
import logging
import json


logger = logging.getLogger(__name__)


class AgentMemory:
    """
    Persistent memory for agents.
    
    Features:
    - Conversation History
    - Learned Patterns
    - Strategy Database
    - Performance History
    """
    
    def __init__(self, max_items: int = 1000):
        """
        Initialize agent memory.
        
        Args:
            max_items: Maximum number of items to store
        """
        self._storage: Dict[str, Any] = {}
        self._history: List[Dict[str, Any]] = []
        self._max_items = max_items
        logger.info("Initialized AgentMemory")
    
    def store(self, key: str, value: Any, metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Store a value in memory.
        
        Args:
            key: Storage key
            value: Value to store
            metadata: Optional metadata
        """
        self._storage[key] = value
        
        # Add to history
        history_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "action": "store",
            "key": key,
            "metadata": metadata or {},
        }
        self._history.append(history_entry)
        
        # Trim history if needed
        if len(self._history) > self._max_items:
            self._history.pop(0)
        
        logger.debug(f"Stored key: {key}")
    
    def retrieve(self, key: str, default: Any = None) -> Any:
        """
        Retrieve a value from memory.
        
        Args:
            key: Storage key
            default: Default value if key not found
            
        Returns:
            Stored value or default
        """
        value = self._storage.get(key, default)
        
        # Log retrieval
        history_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "action": "retrieve",
            "key": key,
            "found": key in self._storage,
        }
        self._history.append(history_entry)
        
        if len(self._history) > self._max_items:
            self._history.pop(0)
        
        logger.debug(f"Retrieved key: {key}")
        return value
    
    def delete(self, key: str) -> bool:
        """
        Delete a key from memory.
        
        Args:
            key: Storage key
            
        Returns:
            True if key was deleted, False if not found
        """
        if key in self._storage:
            del self._storage[key]
            logger.debug(f"Deleted key: {key}")
            return True
        return False
    
    def search(self, query: str) -> List[str]:
        """
        Search for keys matching a query.
        
        Args:
            query: Search query (simple substring match)
            
        Returns:
            List of matching keys
        """
        matching_keys = [k for k in self._storage.keys() if query.lower() in k.lower()]
        logger.debug(f"Search query '{query}' found {len(matching_keys)} matches")
        return matching_keys
    
    def get_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get memory access history.
        
        Args:
            limit: Maximum number of entries to return
            
        Returns:
            List of history entries
        """
        return self._history[-limit:]
    
    def clear(self) -> None:
        """Clear all memory."""
        self._storage.clear()
        self._history.clear()
        logger.info("Cleared all memory")
    
    def export_json(self) -> str:
        """
        Export memory to JSON string.
        
        Returns:
            JSON string of memory contents
        """
        return json.dumps(self._storage, indent=2)
    
    def import_json(self, json_str: str) -> None:
        """
        Import memory from JSON string.
        
        Args:
            json_str: JSON string to import
        """
        imported = json.loads(json_str)
        self._storage.update(imported)
        logger.info(f"Imported {len(imported)} items from JSON")


class VectorMemory:
    """
    Vector-based memory for semantic search.
    
    Note: This is a placeholder. Full implementation requires ChromaDB.
    
    Use Cases:
    - Strategy Knowledge Base
    - Historical Patterns
    - Market Context
    - Trading Lessons
    """
    
    def __init__(self, collection_name: str = "peak_trade"):
        """
        Initialize vector memory.
        
        Args:
            collection_name: Name of the vector collection
        """
        self.collection_name = collection_name
        self._documents: List[Dict[str, Any]] = []
        logger.info(f"Initialized VectorMemory (placeholder): {collection_name}")
    
    def add_document(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Add a document to the vector store.
        
        Args:
            text: Document text
            metadata: Document metadata
        """
        doc = {
            "text": text,
            "metadata": metadata or {},
            "timestamp": datetime.utcnow().isoformat(),
        }
        self._documents.append(doc)
        logger.debug(f"Added document to vector store: {len(text)} chars")
    
    def search_similar(
        self,
        query: str,
        k: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Search for similar documents.
        
        Note: This is a simple keyword-based fallback.
        Full semantic search requires ChromaDB integration.
        
        Args:
            query: Search query
            k: Number of results to return
            
        Returns:
            List of similar documents
        """
        # Simple keyword-based search as fallback
        query_lower = query.lower()
        results = []
        
        for doc in self._documents:
            if query_lower in doc["text"].lower():
                results.append(doc)
        
        logger.debug(f"Search query '{query}' found {len(results)} matches")
        return results[:k]
    
    def clear(self) -> None:
        """Clear all documents."""
        self._documents.clear()
        logger.info("Cleared vector memory")
