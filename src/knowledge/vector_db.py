"""
Vector Database Integration for Semantic Search

Supports multiple vector database backends:
- ChromaDB (local/embedded)
- Pinecone (cloud-based)
- Qdrant (local/cloud)

Usage:
    from src.knowledge.vector_db import VectorDBFactory

    db = VectorDBFactory.create("chroma", config={
        "persist_directory": "./data/chroma_db"
    })

    # Add documents
    db.add_documents(
        documents=["Market analysis...", "Trading strategy..."],
        metadatas=[{"source": "research"}, {"source": "strategy"}],
        ids=["doc1", "doc2"]
    )

    # Search
    results = db.search("What is the best momentum strategy?", top_k=5)
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class VectorDBInterface(ABC):
    """Abstract interface for vector databases."""

    @abstractmethod
    def add_documents(
        self,
        documents: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None,
    ) -> None:
        """Add documents to the vector database."""
        pass

    @abstractmethod
    def search(
        self, query: str, top_k: int = 5, filter_dict: Optional[Dict[str, Any]] = None
    ) -> List[Tuple[str, float, Dict[str, Any]]]:
        """
        Search for similar documents.

        Returns:
            List of tuples: (document_text, similarity_score, metadata)
        """
        pass

    @abstractmethod
    def delete(self, ids: List[str]) -> None:
        """Delete documents by IDs."""
        pass

    @abstractmethod
    def clear(self) -> None:
        """Clear all documents from the database."""
        pass


class ChromaDBAdapter(VectorDBInterface):
    """ChromaDB adapter for local vector storage."""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize ChromaDB adapter.

        Args:
            config: Configuration dict with keys:
                - persist_directory: Directory for persistent storage
                - collection_name: Name of the collection (default: "peak_trade")
        """
        try:
            import chromadb
        except ImportError:
            raise ImportError("chromadb not installed. Install with: pip install chromadb")

        self.persist_directory = config.get("persist_directory", "./data/chroma_db")
        self.collection_name = config.get("collection_name", "peak_trade")

        self.client = chromadb.PersistentClient(path=self.persist_directory)
        self.collection = self.client.get_or_create_collection(name=self.collection_name)
        logger.info(f"ChromaDB initialized: {self.collection_name} at {self.persist_directory}")

    def add_documents(
        self,
        documents: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None,
    ) -> None:
        """Add documents to ChromaDB."""
        if ids is None:
            ids = [f"doc_{i}" for i in range(len(documents))]

        self.collection.add(documents=documents, metadatas=metadatas, ids=ids)
        logger.info(f"Added {len(documents)} documents to ChromaDB")

    def search(
        self, query: str, top_k: int = 5, filter_dict: Optional[Dict[str, Any]] = None
    ) -> List[Tuple[str, float, Dict[str, Any]]]:
        """Search ChromaDB for similar documents."""
        results = self.collection.query(query_texts=[query], n_results=top_k, where=filter_dict)

        # Format results
        formatted_results = []
        if results["documents"] and len(results["documents"]) > 0:
            for i, doc in enumerate(results["documents"][0]):
                score = results["distances"][0][i] if results["distances"] else 0.0
                metadata = results["metadatas"][0][i] if results["metadatas"] else {}
                formatted_results.append((doc, score, metadata))

        return formatted_results

    def delete(self, ids: List[str]) -> None:
        """Delete documents from ChromaDB."""
        self.collection.delete(ids=ids)
        logger.info(f"Deleted {len(ids)} documents from ChromaDB")

    def clear(self) -> None:
        """Clear all documents from ChromaDB."""
        self.client.delete_collection(name=self.collection_name)
        self.collection = self.client.create_collection(name=self.collection_name)
        logger.info("Cleared ChromaDB collection")


class QdrantAdapter(VectorDBInterface):
    """Qdrant adapter for vector storage."""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Qdrant adapter.

        Args:
            config: Configuration dict with keys:
                - url: Qdrant server URL (default: ":memory:" for in-memory)
                - collection_name: Name of the collection
                - api_key: Optional API key for cloud Qdrant
        """
        try:
            from qdrant_client import QdrantClient
            from qdrant_client.models import Distance, VectorParams
        except ImportError:
            raise ImportError(
                "qdrant-client not installed. Install with: pip install qdrant-client"
            )

        self.url = config.get("url", ":memory:")
        self.collection_name = config.get("collection_name", "peak_trade")
        self.api_key = config.get("api_key")

        # Initialize client
        self.client = QdrantClient(url=self.url, api_key=self.api_key)

        # Create collection if it doesn't exist
        collections = self.client.get_collections().collections
        if not any(c.name == self.collection_name for c in collections):
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=384, distance=Distance.COSINE),
            )

        logger.info(f"Qdrant initialized: {self.collection_name} at {self.url}")

    def add_documents(
        self,
        documents: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None,
    ) -> None:
        """Add documents to Qdrant (requires embedding function)."""
        raise NotImplementedError(
            "Qdrant adapter requires custom embedding function. Use ChromaDB for simplicity."
        )

    def search(
        self, query: str, top_k: int = 5, filter_dict: Optional[Dict[str, Any]] = None
    ) -> List[Tuple[str, float, Dict[str, Any]]]:
        """Search Qdrant (requires embedding function)."""
        raise NotImplementedError(
            "Qdrant adapter requires custom embedding function. Use ChromaDB for simplicity."
        )

    def delete(self, ids: List[str]) -> None:
        """Delete documents from Qdrant."""
        from qdrant_client.models import PointIdsList

        self.client.delete(collection_name=self.collection_name, points_selector=PointIdsList(ids))
        logger.info(f"Deleted {len(ids)} documents from Qdrant")

    def clear(self) -> None:
        """Clear all documents from Qdrant."""
        self.client.delete_collection(collection_name=self.collection_name)
        logger.info("Cleared Qdrant collection")


class PineconeAdapter(VectorDBInterface):
    """Pinecone adapter for cloud vector storage."""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Pinecone adapter.

        Args:
            config: Configuration dict with keys:
                - api_key: Pinecone API key (required)
                - environment: Pinecone environment
                - index_name: Name of the index
        """
        try:
            import pinecone
        except ImportError:
            raise ImportError(
                "pinecone-client not installed. Install with: pip install pinecone-client"
            )

        self.api_key = config.get("api_key")
        if not self.api_key:
            raise ValueError("Pinecone API key is required")

        self.environment = config.get("environment", "us-west1-gcp")
        self.index_name = config.get("index_name", "peak-trade")

        pinecone.init(api_key=self.api_key, environment=self.environment)

        # Create index if it doesn't exist
        if self.index_name not in pinecone.list_indexes():
            pinecone.create_index(name=self.index_name, dimension=384, metric="cosine")

        self.index = pinecone.Index(self.index_name)
        logger.info(f"Pinecone initialized: {self.index_name}")

    def add_documents(
        self,
        documents: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None,
    ) -> None:
        """Add documents to Pinecone (requires embedding function)."""
        raise NotImplementedError(
            "Pinecone adapter requires custom embedding function. Use ChromaDB for simplicity."
        )

    def search(
        self, query: str, top_k: int = 5, filter_dict: Optional[Dict[str, Any]] = None
    ) -> List[Tuple[str, float, Dict[str, Any]]]:
        """Search Pinecone (requires embedding function)."""
        raise NotImplementedError(
            "Pinecone adapter requires custom embedding function. Use ChromaDB for simplicity."
        )

    def delete(self, ids: List[str]) -> None:
        """Delete documents from Pinecone."""
        self.index.delete(ids=ids)
        logger.info(f"Deleted {len(ids)} documents from Pinecone")

    def clear(self) -> None:
        """Clear all documents from Pinecone."""
        self.index.delete(delete_all=True)
        logger.info("Cleared Pinecone index")


class VectorDBFactory:
    """Factory for creating vector database instances."""

    _adapters = {
        "chroma": ChromaDBAdapter,
        "qdrant": QdrantAdapter,
        "pinecone": PineconeAdapter,
    }

    @classmethod
    def create(cls, db_type: str, config: Dict[str, Any]) -> VectorDBInterface:
        """
        Create a vector database instance.

        Args:
            db_type: Type of database ("chroma", "qdrant", "pinecone")
            config: Configuration dict for the database

        Returns:
            VectorDBInterface instance
        """
        if db_type not in cls._adapters:
            raise ValueError(
                f"Unknown database type: {db_type}. Available: {list(cls._adapters.keys())}"
            )

        adapter_class = cls._adapters[db_type]
        return adapter_class(config)

    @classmethod
    def register_adapter(cls, name: str, adapter_class: type) -> None:
        """Register a custom vector database adapter."""
        cls._adapters[name] = adapter_class
        logger.info(f"Registered custom adapter: {name}")
