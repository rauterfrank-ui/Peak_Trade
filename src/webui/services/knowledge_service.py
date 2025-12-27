# src/webui/services/knowledge_service.py
"""
Knowledge DB Service Layer for WebUI

Provides abstraction over Knowledge DB modules:
- Vector DB (semantic search, document storage)
- RAG Pipeline (retrieval-augmented generation)
- Time-Series DB (optional, for stats)

Graceful degradation:
- Returns 501 if backend dependencies are missing
- Never crashes on missing optional dependencies
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


# =============================================================================
# Service Availability Checks
# =============================================================================


def is_vector_db_available() -> bool:
    """Check if vector DB backend is available."""
    try:
        import chromadb  # noqa: F401

        return True
    except ImportError:
        return False


def is_rag_available() -> bool:
    """Check if RAG pipeline is available (depends on vector DB)."""
    return is_vector_db_available()


# =============================================================================
# Knowledge DB Service
# =============================================================================


class KnowledgeService:
    """
    Service layer for Knowledge DB operations.

    Handles:
    - Vector DB initialization and queries
    - Document management (snippets, strategies)
    - Semantic search
    - Statistics and health checks
    """

    def __init__(
        self,
        vector_db_type: str = "chroma",
        persist_directory: Optional[Path] = None,
    ):
        """
        Initialize Knowledge Service.

        Args:
            vector_db_type: Type of vector DB ("chroma", "qdrant", "pinecone")
            persist_directory: Directory for persistent storage
        """
        self.vector_db_type = vector_db_type
        self.persist_directory = persist_directory or Path("./data/chroma_db")
        self.vector_db = None
        self.rag_pipeline = None

        # In-memory fallback store (when chromadb not available)
        self._in_memory_snippets: Dict[str, Dict[str, Any]] = {}
        self._in_memory_strategies: Dict[str, Dict[str, Any]] = {}

        # Try to initialize (graceful failure)
        self._init_backends()

    def _init_backends(self) -> None:
        """Initialize vector DB and RAG backends (graceful failure)."""
        if not is_vector_db_available():
            logger.warning("Vector DB backend not available (chromadb not installed)")
            return

        try:
            from src.knowledge.vector_db import VectorDBFactory
            from src.knowledge.rag import RAGPipeline

            config = {
                "persist_directory": str(self.persist_directory),
                "collection_name": "peak_trade_webui",
            }

            self.vector_db = VectorDBFactory.create(self.vector_db_type, config)
            self.rag_pipeline = RAGPipeline(vector_db=self.vector_db)

            logger.info(
                f"Knowledge Service initialized: {self.vector_db_type} at {self.persist_directory}"
            )
        except Exception as e:
            logger.error(f"Failed to initialize Knowledge Service: {e}")
            self.vector_db = None
            self.rag_pipeline = None

    def is_available(self) -> bool:
        """
        Check if Knowledge Service is available.

        Returns True if either vector DB is available OR in-memory fallback is active.
        """
        return True  # Always available (with in-memory fallback)

    # =========================================================================
    # Snippets (Generic Documents)
    # =========================================================================

    def list_snippets(
        self,
        limit: int = 50,
        category: Optional[str] = None,
        tag: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        List document snippets from vector DB or in-memory store.

        Args:
            limit: Maximum number of snippets to return
            category: Filter by category metadata
            tag: Filter by tag metadata

        Returns:
            List of snippet dicts with metadata
        """
        # Use in-memory store if vector DB not available
        if self.vector_db is None:
            snippets = list(self._in_memory_snippets.values())

            # Apply filters
            if category:
                snippets = [s for s in snippets if s.get("category") == category]
            if tag:
                snippets = [s for s in snippets if tag in s.get("tags", [])]

            return snippets[:limit]

        # For now, return mock data (vector DB doesn't have a "list all" method)
        # In production, you'd maintain a separate index or use DB-specific queries
        return [
            {
                "id": "snippet_001",
                "title": "RSI Strategy Overview",
                "content": "RSI strategy works best in ranging markets...",
                "category": "strategy",
                "tags": ["rsi", "ranging"],
                "created_at": "2024-12-20T10:00:00Z",
            },
            {
                "id": "snippet_002",
                "title": "Momentum Trading Notes",
                "content": "Momentum strategies perform well in trending markets...",
                "category": "strategy",
                "tags": ["momentum", "trending"],
                "created_at": "2024-12-20T11:00:00Z",
            },
        ][:limit]

    def add_snippet(
        self,
        content: str,
        title: Optional[str] = None,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Add a document snippet to vector DB or in-memory store.

        Args:
            content: Document content
            title: Optional title
            category: Optional category
            tags: Optional list of tags

        Returns:
            Created snippet dict with ID

        Raises:
            ReadonlyModeError: If KNOWLEDGE_READONLY is enabled
        """
        # Generate ID
        import uuid
        from datetime import datetime

        snippet_id = f"snippet_{uuid.uuid4().hex[:8]}"

        # Build snippet object
        snippet = {
            "id": snippet_id,
            "title": title or "Untitled",
            "content": content,
            "category": category or "general",
            "tags": tags or [],
            "created_at": datetime.utcnow().isoformat() + "Z",
        }

        # Use in-memory store if vector DB not available
        if self.vector_db is None:
            self._in_memory_snippets[snippet_id] = snippet
            logger.info(f"Added snippet to in-memory store: {snippet_id}")
            return snippet

        # Build metadata for vector DB
        metadata = {
            "type": "snippet",
            "title": snippet["title"],
            "category": snippet["category"],
            "tags": ",".join(tags) if tags else "",
        }

        # Add to vector DB (will raise ReadonlyModeError if readonly)
        self.vector_db.add_documents(
            documents=[content],
            metadatas=[metadata],
            ids=[snippet_id],
        )

        logger.info(f"Added snippet to vector DB: {snippet_id}")
        return snippet

    # =========================================================================
    # Strategies (Strategy Documents)
    # =========================================================================

    def list_strategies(
        self,
        limit: int = 50,
        status: Optional[str] = None,
        name: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        List strategy documents from vector DB or in-memory store.

        Args:
            limit: Maximum number to return
            status: Filter by status ("rd", "live", "deprecated")
            name: Filter by name substring

        Returns:
            List of strategy dicts
        """
        # Use in-memory store if vector DB not available
        if self.vector_db is None:
            strategies = list(self._in_memory_strategies.values())

            # Apply filters
            if status:
                strategies = [s for s in strategies if s.get("status") == status]
            if name:
                strategies = [s for s in strategies if name.lower() in s.get("name", "").lower()]

            return strategies[:limit]

        # Mock data for now
        strategies = [
            {
                "id": "strategy_ma_crossover",
                "name": "MA Crossover",
                "description": "Moving average crossover strategy",
                "status": "live",
                "tier": "core",
                "created_at": "2024-12-01T00:00:00Z",
            },
            {
                "id": "strategy_rsi_mean_reversion",
                "name": "RSI Mean Reversion",
                "description": "RSI-based mean reversion strategy",
                "status": "rd",
                "tier": "experimental",
                "created_at": "2024-12-10T00:00:00Z",
            },
        ]

        # Apply filters
        if status:
            strategies = [s for s in strategies if s["status"] == status]
        if name:
            strategies = [s for s in strategies if name.lower() in s["name"].lower()]

        return strategies[:limit]

    def add_strategy(
        self,
        name: str,
        description: str,
        status: str = "rd",
        tier: str = "experimental",
    ) -> Dict[str, Any]:
        """
        Add a strategy document to vector DB or in-memory store.

        Args:
            name: Strategy name
            description: Strategy description
            status: Status ("rd", "live", "deprecated")
            tier: Tier ("core", "experimental", "auxiliary")

        Returns:
            Created strategy dict with ID

        Raises:
            ReadonlyModeError: If KNOWLEDGE_READONLY is enabled
        """
        # Generate ID
        from datetime import datetime

        strategy_id = f"strategy_{name.lower().replace(' ', '_')}"

        # Build strategy object
        strategy = {
            "id": strategy_id,
            "name": name,
            "description": description,
            "status": status,
            "tier": tier,
            "created_at": datetime.utcnow().isoformat() + "Z",
        }

        # Use in-memory store if vector DB not available
        if self.vector_db is None:
            self._in_memory_strategies[strategy_id] = strategy
            logger.info(f"Added strategy to in-memory store: {strategy_id}")
            return strategy

        # Build metadata for vector DB
        metadata = {
            "type": "strategy",
            "name": name,
            "status": status,
            "tier": tier,
        }

        # Add to vector DB
        self.vector_db.add_documents(
            documents=[description],
            metadatas=[metadata],
            ids=[strategy_id],
        )

        logger.info(f"Added strategy to vector DB: {strategy_id}")
        return strategy

    # =========================================================================
    # Semantic Search
    # =========================================================================

    def search(
        self,
        query: str,
        top_k: int = 5,
        filter_type: Optional[str] = None,
    ) -> List[Tuple[str, float, Dict[str, Any]]]:
        """
        Perform semantic search over knowledge base or in-memory store.

        Args:
            query: Search query
            top_k: Number of results to return
            filter_type: Optional filter by document type

        Returns:
            List of tuples: (document_text, similarity_score, metadata)
        """
        # Use in-memory store if vector DB not available (simple keyword matching)
        if self.vector_db is None:
            results = []
            query_lower = query.lower()

            # Search in snippets
            if filter_type is None or filter_type == "snippet":
                for snippet in self._in_memory_snippets.values():
                    if (
                        query_lower in snippet.get("content", "").lower()
                        or query_lower in snippet.get("title", "").lower()
                    ):
                        results.append(
                            (
                                snippet.get("content", ""),
                                0.9,  # Mock score
                                {"type": "snippet", **snippet},
                            )
                        )

            # Search in strategies
            if filter_type is None or filter_type == "strategy":
                for strategy in self._in_memory_strategies.values():
                    if (
                        query_lower in strategy.get("description", "").lower()
                        or query_lower in strategy.get("name", "").lower()
                    ):
                        results.append(
                            (
                                strategy.get("description", ""),
                                0.9,  # Mock score
                                {"type": "strategy", **strategy},
                            )
                        )

            logger.info(f"Search query (in-memory): '{query}' returned {len(results)} results")
            return results[:top_k]

        filter_dict = {"type": filter_type} if filter_type else None

        results = self.vector_db.search(
            query=query,
            top_k=top_k,
            filter_dict=filter_dict,
        )

        logger.info(f"Search query: '{query}' returned {len(results)} results")
        return results

    # =========================================================================
    # Statistics
    # =========================================================================

    def get_stats(self) -> Dict[str, Any]:
        """
        Get Knowledge DB statistics.

        Returns:
            Dict with stats (document counts, backend info, etc.)
        """
        stats = {
            "backend": self.vector_db_type if self.vector_db else "in-memory",
            "available": self.is_available(),
            "persist_directory": str(self.persist_directory),
        }

        # Use in-memory counts if vector DB not available
        if self.vector_db is None:
            snippet_count = len(self._in_memory_snippets)
            strategy_count = len(self._in_memory_strategies)
            stats.update(
                {
                    "total_documents": snippet_count + strategy_count,
                    "snippets": snippet_count,
                    "strategies": strategy_count,
                    "readonly_mode": os.environ.get("KNOWLEDGE_READONLY", "false").lower()
                    in ("true", "1", "yes"),
                    "mode": "in-memory (chromadb not installed)",
                }
            )
        else:
            # Mock counts for now
            stats.update(
                {
                    "total_documents": 42,
                    "snippets": 25,
                    "strategies": 17,
                    "readonly_mode": os.environ.get("KNOWLEDGE_READONLY", "false").lower()
                    in ("true", "1", "yes"),
                    "mode": "vector-db",
                }
            )

        return stats


# =============================================================================
# Singleton Instance
# =============================================================================

_service_instance: Optional[KnowledgeService] = None


def get_knowledge_service() -> KnowledgeService:
    """Get or create singleton Knowledge Service instance."""
    global _service_instance
    if _service_instance is None:
        _service_instance = KnowledgeService()
    return _service_instance
