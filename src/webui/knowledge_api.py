# src/webui/knowledge_api.py
"""
Peak_Trade: Knowledge DB API v1.0
==================================

API-Endpoints für Knowledge Database Integration:
- GET  /api/knowledge/snippets - Liste von Dokumenten-Snippets
- POST /api/knowledge/snippets - Snippet hinzufügen
- GET  /api/knowledge/strategies - Liste von Strategie-Dokumenten
- POST /api/knowledge/strategies - Strategie hinzufügen
- GET  /api/knowledge/search - Semantische Suche
- GET  /api/knowledge/stats - Statistiken

Access Control:
- GET: Immer verfügbar
- POST: Nur wenn KNOWLEDGE_READONLY=false UND KNOWLEDGE_WEB_WRITE_ENABLED=true

Graceful Degradation:
- 501 Not Implemented wenn Backend nicht verfügbar
- Klare Fehlermeldungen mit Lösungshinweisen
"""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from src.webui.services.knowledge_service import (
    get_knowledge_service,
    is_vector_db_available,
)

logger = logging.getLogger(__name__)

# =============================================================================
# Router Setup
# =============================================================================

router = APIRouter(
    prefix="/api/knowledge",
    tags=["knowledge"],
)


# =============================================================================
# Request/Response Models
# =============================================================================


class SnippetCreate(BaseModel):
    """Request model for creating a snippet."""

    content: str = Field(..., min_length=1, max_length=10000)
    title: Optional[str] = Field(None, max_length=200)
    category: Optional[str] = Field(None, max_length=50)
    tags: Optional[List[str]] = Field(None, max_items=10)


class StrategyCreate(BaseModel):
    """Request model for creating a strategy."""

    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(..., min_length=1, max_length=5000)
    status: str = Field("rd", pattern="^(rd|live|deprecated)$")
    tier: str = Field("experimental", pattern="^(core|experimental|auxiliary)$")


class SearchQuery(BaseModel):
    """Request model for semantic search."""

    query: str = Field(..., min_length=1, max_length=500)
    top_k: int = Field(5, ge=1, le=20)
    filter_type: Optional[str] = Field(None, max_length=50)


# =============================================================================
# Access Control
# =============================================================================


def require_write_enabled() -> None:
    """
    Check if write operations are enabled.

    Raises:
        HTTPException(403): If KNOWLEDGE_READONLY=true
        HTTPException(403): If KNOWLEDGE_WEB_WRITE_ENABLED!=true
    """
    # Check 1: KNOWLEDGE_READONLY flag
    readonly = os.environ.get("KNOWLEDGE_READONLY", "false").lower() in (
        "true",
        "1",
        "yes",
    )
    if readonly:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "Knowledge DB is in readonly mode",
                "message": "Write operations are blocked by KNOWLEDGE_READONLY flag",
                "solution": "Set KNOWLEDGE_READONLY=false to enable writes",
            },
        )

    # Check 2: KNOWLEDGE_WEB_WRITE_ENABLED flag
    web_write_enabled = os.environ.get("KNOWLEDGE_WEB_WRITE_ENABLED", "false").lower() in (
        "true",
        "1",
        "yes",
    )
    if not web_write_enabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "WebUI write access disabled",
                "message": "Write operations via WebUI are disabled by default for safety",
                "solution": "Set KNOWLEDGE_WEB_WRITE_ENABLED=true to enable WebUI writes",
            },
        )


def require_backend_available() -> None:
    """
    Check if Knowledge DB backend is available.

    Raises:
        HTTPException(501): If backend is not available
    """
    if not is_vector_db_available():
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail={
                "error": "Knowledge DB backend not available",
                "message": "Vector database backend (chromadb) is not installed",
                "solution": "Install with: pip install chromadb",
            },
        )

    service = get_knowledge_service()
    if not service.is_available():
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail={
                "error": "Knowledge Service initialization failed",
                "message": "Could not initialize Knowledge DB service",
                "solution": "Check logs for details",
            },
        )


# =============================================================================
# Endpoints: Snippets
# =============================================================================


@router.get(
    "/snippets",
    response_model=Dict[str, Any],
    summary="Liste Dokumenten-Snippets",
    description="Liefert eine Liste von Dokumenten-Snippets mit optionalen Filtern.",
)
async def list_snippets(
    limit: int = Query(50, ge=1, le=500, description="Maximale Anzahl"),
    category: Optional[str] = Query(None, description="Filter nach Kategorie"),
    tag: Optional[str] = Query(None, description="Filter nach Tag"),
) -> Dict[str, Any]:
    """
    Liste Dokumenten-Snippets.

    Returns:
        Dict mit:
        - items: Liste von Snippets
        - total: Gesamtanzahl
        - backend_available: Backend-Status
    """
    service = get_knowledge_service()

    # Graceful degradation: Return empty list if backend not available
    if not service.is_available():
        return {
            "items": [],
            "total": 0,
            "backend_available": False,
            "message": "Knowledge DB backend not available (chromadb not installed)",
        }

    snippets = service.list_snippets(limit=limit, category=category, tag=tag)

    return {
        "items": snippets,
        "total": len(snippets),
        "backend_available": True,
    }


@router.post(
    "/snippets",
    response_model=Dict[str, Any],
    status_code=status.HTTP_201_CREATED,
    summary="Snippet hinzufügen",
    description="Fügt ein neues Dokumenten-Snippet zur Knowledge DB hinzu.",
)
async def create_snippet(snippet: SnippetCreate) -> Dict[str, Any]:
    """
    Füge ein Snippet hinzu.

    Requires:
        - KNOWLEDGE_READONLY=false
        - KNOWLEDGE_WEB_WRITE_ENABLED=true

    Returns:
        Created snippet with ID
    """
    # Access control checks
    require_write_enabled()
    require_backend_available()

    service = get_knowledge_service()

    try:
        created = service.add_snippet(
            content=snippet.content,
            title=snippet.title,
            category=snippet.category,
            tags=snippet.tags,
        )

        return {
            "success": True,
            "snippet": created,
        }
    except Exception as e:
        # Catch ReadonlyModeError from Knowledge DB layer
        if "READONLY" in str(e):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": "Write blocked by Knowledge DB layer",
                    "message": str(e),
                },
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Failed to create snippet",
                "message": str(e),
            },
        )


# =============================================================================
# Endpoints: Strategies
# =============================================================================


@router.get(
    "/strategies",
    response_model=Dict[str, Any],
    summary="Liste Strategie-Dokumente",
    description="Liefert eine Liste von Strategie-Dokumenten mit optionalen Filtern.",
)
async def list_strategies(
    limit: int = Query(50, ge=1, le=500, description="Maximale Anzahl"),
    status_filter: Optional[str] = Query(
        None, alias="status", description="Filter nach Status (rd/live/deprecated)"
    ),
    name: Optional[str] = Query(None, description="Filter nach Name (Substring)"),
) -> Dict[str, Any]:
    """
    Liste Strategie-Dokumente.

    Returns:
        Dict mit:
        - items: Liste von Strategien
        - total: Gesamtanzahl
        - backend_available: Backend-Status
    """
    service = get_knowledge_service()

    # Graceful degradation
    if not service.is_available():
        return {
            "items": [],
            "total": 0,
            "backend_available": False,
            "message": "Knowledge DB backend not available",
        }

    strategies = service.list_strategies(limit=limit, status=status_filter, name=name)

    return {
        "items": strategies,
        "total": len(strategies),
        "backend_available": True,
    }


@router.post(
    "/strategies",
    response_model=Dict[str, Any],
    status_code=status.HTTP_201_CREATED,
    summary="Strategie hinzufügen",
    description="Fügt ein neues Strategie-Dokument zur Knowledge DB hinzu.",
)
async def create_strategy(strategy: StrategyCreate) -> Dict[str, Any]:
    """
    Füge eine Strategie hinzu.

    Requires:
        - KNOWLEDGE_READONLY=false
        - KNOWLEDGE_WEB_WRITE_ENABLED=true

    Returns:
        Created strategy with ID
    """
    # Access control checks
    require_write_enabled()
    require_backend_available()

    service = get_knowledge_service()

    try:
        created = service.add_strategy(
            name=strategy.name,
            description=strategy.description,
            status=strategy.status,
            tier=strategy.tier,
        )

        return {
            "success": True,
            "strategy": created,
        }
    except Exception as e:
        if "READONLY" in str(e):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": "Write blocked by Knowledge DB layer",
                    "message": str(e),
                },
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Failed to create strategy",
                "message": str(e),
            },
        )


# =============================================================================
# Endpoints: Search
# =============================================================================


@router.get(
    "/search",
    response_model=Dict[str, Any],
    summary="Semantische Suche",
    description="Führt eine semantische Suche über die Knowledge Base durch.",
)
async def search_knowledge(
    q: str = Query(..., min_length=1, max_length=500, description="Suchanfrage"),
    k: int = Query(5, ge=1, le=20, description="Anzahl Ergebnisse"),
    type_filter: Optional[str] = Query(None, alias="type", description="Filter nach Dokumenttyp"),
) -> Dict[str, Any]:
    """
    Semantische Suche über Knowledge Base.

    Returns:
        Dict mit:
        - query: Original-Query
        - results: Liste von Suchergebnissen
        - backend_available: Backend-Status
    """
    # Check backend availability
    require_backend_available()

    service = get_knowledge_service()

    try:
        results = service.search(query=q, top_k=k, filter_type=type_filter)

        # Format results
        formatted_results = [
            {
                "content": doc,
                "score": float(score),
                "metadata": metadata,
            }
            for doc, score, metadata in results
        ]

        return {
            "query": q,
            "results": formatted_results,
            "total": len(formatted_results),
            "backend_available": True,
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Search failed",
                "message": str(e),
            },
        )


# =============================================================================
# Endpoints: Stats
# =============================================================================


@router.get(
    "/stats",
    response_model=Dict[str, Any],
    summary="Knowledge DB Statistiken",
    description="Liefert Statistiken über die Knowledge Database.",
)
async def get_stats() -> Dict[str, Any]:
    """
    Knowledge DB Statistiken.

    Returns:
        Dict mit Stats (document counts, backend info, readonly status)
    """
    service = get_knowledge_service()
    stats = service.get_stats()

    # Add environment flags
    stats["environment"] = {
        "KNOWLEDGE_READONLY": os.environ.get("KNOWLEDGE_READONLY", "false"),
        "KNOWLEDGE_WEB_WRITE_ENABLED": os.environ.get("KNOWLEDGE_WEB_WRITE_ENABLED", "false"),
    }

    return stats
