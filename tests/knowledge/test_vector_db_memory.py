"""Unit tests for MemoryVectorAdapter (no optional vector-db dependencies)."""

from __future__ import annotations

import pytest

from src.knowledge.vector_db import MemoryVectorAdapter, ReadonlyModeError, VectorDBFactory


def test_factory_creates_memory_backend() -> None:
    db = VectorDBFactory.create("memory", {})
    assert isinstance(db, MemoryVectorAdapter)


def test_memory_add_search_delete_clear() -> None:
    db = MemoryVectorAdapter({})
    db.add_documents(
        documents=["momentum alpha research", "mean reversion notes"],
        metadatas=[{"src": "a"}, {"src": "b"}],
        ids=["d1", "d2"],
    )
    out = db.search("momentum research alpha", top_k=2)
    assert len(out) == 2
    assert all(len(t) == 3 for t in out)
    texts = [t[0] for t in out]
    assert "momentum alpha research" in texts

    db.delete(["d1"])
    only = db.search("reversion mean", top_k=5)
    assert len(only) == 1
    assert "mean reversion" in only[0][0]

    db.clear()
    assert db.search("momentum", top_k=5) == []


def test_memory_search_respects_filter_dict() -> None:
    db = MemoryVectorAdapter({})
    db.add_documents(
        documents=["foo bar", "foo baz"],
        metadatas=[{"k": 1}, {"k": 2}],
        ids=["a", "b"],
    )
    hits = db.search("foo", top_k=5, filter_dict={"k": 2})
    assert len(hits) == 1
    assert hits[0][0] == "foo baz"


def test_memory_writes_blocked_in_readonly(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("KNOWLEDGE_READONLY", "true")
    db = MemoryVectorAdapter({})
    with pytest.raises(ReadonlyModeError):
        db.add_documents(["x"])
    monkeypatch.delenv("KNOWLEDGE_READONLY", raising=False)
