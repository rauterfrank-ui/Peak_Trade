"""In-memory contract for Knowledge API request Pydantic models (v0).

No HTTP/TestClient, router execution, filesystem, subprocess, env, or network.

Prod definitions live in ``src.webui.knowledge_api`` unchanged by this slice.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

pytest.importorskip("fastapi")

from src.webui.knowledge_api import SearchQuery, SnippetCreate, StrategyCreate


def _model_dump_public(model: object) -> dict:
    """Stable dict shape for pydantic v2 primary; v1 fallback if ever present."""
    dump = getattr(model, "model_dump", None)
    if callable(dump):
        return dump(mode="python")
    legacy = getattr(model, "dict", None)
    if callable(legacy):
        return legacy()
    raise AssertionError("expected BaseModel-like model_dump()/dict()")


def test_snippet_create_minimal_contract_v0() -> None:
    s = SnippetCreate(content="hello")
    assert s.content == "hello"
    assert s.title is None
    assert s.category is None
    assert s.tags is None


def test_snippet_create_full_contract_v0() -> None:
    s = SnippetCreate(
        content="body",
        title="T",
        category="cat",
        tags=["a", "b"],
    )
    assert s.content == "body"
    assert s.title == "T"
    assert s.category == "cat"
    assert s.tags == ["a", "b"]


def test_snippet_create_rejects_invalid_contract_v0() -> None:
    with pytest.raises(ValidationError):
        SnippetCreate(content="")
    with pytest.raises(ValidationError):
        SnippetCreate(content="ok", tags=[str(i) for i in range(11)])


def test_snippet_create_model_fields_public_contract_v0() -> None:
    assert set(SnippetCreate.model_fields.keys()) == {"content", "title", "category", "tags"}


def test_snippet_create_dump_shape_stable_contract_v0() -> None:
    s = SnippetCreate(content="x", title=None, tags=None)
    assert _model_dump_public(s) == {
        "content": "x",
        "title": None,
        "category": None,
        "tags": None,
    }


def test_strategy_create_defaults_contract_v0() -> None:
    s = StrategyCreate(name="nm", description="long enough description")
    assert s.status == "rd"
    assert s.tier == "experimental"


def test_strategy_create_pattern_values_contract_v0() -> None:
    s_live = StrategyCreate(name="n", description="desc", status="live", tier="core")
    assert s_live.status == "live"
    assert s_live.tier == "core"


def test_strategy_create_rejects_invalid_patterns_contract_v0() -> None:
    with pytest.raises(ValidationError):
        StrategyCreate(name="n", description="desc", status="pending")
    with pytest.raises(ValidationError):
        StrategyCreate(name="n", description="desc", tier="unknown")


def test_strategy_create_empty_name_rejected_contract_v0() -> None:
    with pytest.raises(ValidationError):
        StrategyCreate(name="", description="some description")


def test_strategy_create_model_fields_public_contract_v0() -> None:
    assert set(StrategyCreate.model_fields.keys()) == {"name", "description", "status", "tier"}


def test_strategy_create_dump_shape_stable_contract_v0() -> None:
    s = StrategyCreate(name="alpha", description="Beta line for contract.")
    assert _model_dump_public(s) == {
        "name": "alpha",
        "description": "Beta line for contract.",
        "status": "rd",
        "tier": "experimental",
    }


def test_search_query_defaults_contract_v0() -> None:
    q = SearchQuery(query="find me")
    assert q.top_k == 5
    assert q.filter_type is None


def test_search_query_bounds_contract_v0() -> None:
    q_lo = SearchQuery(query="ok", top_k=1)
    q_hi = SearchQuery(query="ok", top_k=20)
    assert q_lo.top_k == 1
    assert q_hi.top_k == 20


def test_search_query_rejects_invalid_contract_v0() -> None:
    with pytest.raises(ValidationError):
        SearchQuery(query="")
    with pytest.raises(ValidationError):
        SearchQuery(query="ok", top_k=0)
    with pytest.raises(ValidationError):
        SearchQuery(query="ok", top_k=21)


def test_search_query_model_fields_public_contract_v0() -> None:
    assert set(SearchQuery.model_fields.keys()) == {"query", "top_k", "filter_type"}


def test_search_query_dump_shape_stable_contract_v0() -> None:
    q = SearchQuery(query="metrics", filter_type=None)
    assert _model_dump_public(q) == {
        "query": "metrics",
        "top_k": 5,
        "filter_type": None,
    }
