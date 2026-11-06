"""In-memory contract for Knowledge service availability helpers (v0).

No TestClient, router/HTTP, filesystem, subprocess, env patches, or network.

Prod helpers live in ``src.webui.services.knowledge_service`` unchanged by this slice.
"""

from __future__ import annotations

from src.webui.services.knowledge_service import is_rag_available, is_vector_db_available


def test_is_vector_db_available_returns_bool_contract_v0() -> None:
    v = is_vector_db_available()
    assert isinstance(v, bool)


def test_is_rag_available_returns_bool_contract_v0() -> None:
    r = is_rag_available()
    assert isinstance(r, bool)


def test_is_rag_matches_vector_availability_contract_v0() -> None:
    """Public delegation: RAG availability follows vector DB probe (same process)."""
    assert is_rag_available() == is_vector_db_available()


def test_availability_stable_on_repeated_calls_contract_v0() -> None:
    v1 = is_vector_db_available()
    v2 = is_vector_db_available()
    assert v1 is v2 or v1 == v2
    assert is_rag_available() == v1 == v2
