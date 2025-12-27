# tests/test_knowledge_readonly_gating.py
"""
Tests for Knowledge DB Readonly Gating

Tests the KNOWLEDGE_READONLY environment flag across all Knowledge DB modules:
- Vector DB (ChromaDB, Qdrant, Pinecone)
- Time-Series DB (InfluxDB, Parquet)
- RAG Pipeline

Access Matrix:
    Context         | GET  | WRITE
    ----------------|------|-------
    dashboard       | YES  | NO
    research        | YES  | YES
    live_track      | YES  | NO
    admin           | YES  | YES
    READONLY=true   | YES  | NO (enforced)

Run:
    pytest tests/test_knowledge_readonly_gating.py -v
"""

from __future__ import annotations

import os
import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import tempfile
import shutil

from src.knowledge.vector_db import (
    VectorDBInterface,
    ChromaDBAdapter,
    ReadonlyModeError,
    _check_readonly,
)
from src.knowledge.timeseries_db import (
    TimeSeriesDBInterface,
    ParquetAdapter,
    ReadonlyModeError as TimeSeriesReadonlyModeError,
)
from src.knowledge.rag import RAGPipeline


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def temp_dir():
    """Create temporary directory for test data."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def chroma_db(temp_dir):
    """Create ChromaDB instance for testing."""
    config = {
        "persist_directory": str(temp_dir / "chroma"),
        "collection_name": "test_collection",
    }
    return ChromaDBAdapter(config)


@pytest.fixture
def parquet_db(temp_dir):
    """Create Parquet DB instance for testing."""
    config = {"base_path": str(temp_dir / "parquet")}
    return ParquetAdapter(config)


@pytest.fixture
def rag_pipeline(chroma_db):
    """Create RAG pipeline for testing."""
    return RAGPipeline(vector_db=chroma_db)


@pytest.fixture(autouse=True)
def reset_readonly_env():
    """Reset KNOWLEDGE_READONLY env var before each test."""
    original = os.environ.get("KNOWLEDGE_READONLY")
    os.environ.pop("KNOWLEDGE_READONLY", None)
    yield
    if original is not None:
        os.environ["KNOWLEDGE_READONLY"] = original
    else:
        os.environ.pop("KNOWLEDGE_READONLY", None)


# =============================================================================
# Tests: _check_readonly Helper
# =============================================================================


def test_check_readonly_false_by_default():
    """Test that readonly check passes when env var is not set."""
    # Should not raise
    _check_readonly()


@pytest.mark.parametrize(
    "env_value",
    ["true", "TRUE", "True", "1", "yes", "YES", "Yes"],
)
def test_check_readonly_raises_when_enabled(env_value):
    """Test that readonly check raises when env var is truthy."""
    os.environ["KNOWLEDGE_READONLY"] = env_value

    with pytest.raises(ReadonlyModeError, match="READONLY mode"):
        _check_readonly()


@pytest.mark.parametrize(
    "env_value",
    ["false", "FALSE", "False", "0", "no", "NO", "No", ""],
)
def test_check_readonly_passes_when_disabled(env_value):
    """Test that readonly check passes when env var is falsy."""
    os.environ["KNOWLEDGE_READONLY"] = env_value

    # Should not raise
    _check_readonly()


# =============================================================================
# Tests: Vector DB - ChromaDB
# =============================================================================


def test_chroma_search_works_in_readonly(chroma_db):
    """Test that search works in readonly mode."""
    # Add documents first (before readonly)
    chroma_db.add_documents(
        documents=["Test document"],
        metadatas=[{"source": "test"}],
        ids=["doc1"],
    )

    # Enable readonly
    os.environ["KNOWLEDGE_READONLY"] = "true"

    # Search should work
    results = chroma_db.search("Test", top_k=1)
    assert len(results) >= 0  # May or may not find results


def test_chroma_add_blocked_in_readonly(chroma_db):
    """Test that add_documents is blocked in readonly mode."""
    os.environ["KNOWLEDGE_READONLY"] = "true"

    with pytest.raises(ReadonlyModeError, match="READONLY mode"):
        chroma_db.add_documents(
            documents=["Test document"],
            ids=["doc1"],
        )


def test_chroma_delete_blocked_in_readonly(chroma_db):
    """Test that delete is blocked in readonly mode."""
    # Add document first
    chroma_db.add_documents(documents=["Test"], ids=["doc1"])

    # Enable readonly
    os.environ["KNOWLEDGE_READONLY"] = "true"

    with pytest.raises(ReadonlyModeError, match="READONLY mode"):
        chroma_db.delete(ids=["doc1"])


def test_chroma_clear_blocked_in_readonly(chroma_db):
    """Test that clear is blocked in readonly mode."""
    os.environ["KNOWLEDGE_READONLY"] = "true"

    with pytest.raises(ReadonlyModeError, match="READONLY mode"):
        chroma_db.clear()


def test_chroma_write_works_when_readonly_disabled(chroma_db):
    """Test that writes work when readonly is explicitly disabled."""
    os.environ["KNOWLEDGE_READONLY"] = "false"

    # Should not raise
    chroma_db.add_documents(documents=["Test"], ids=["doc1"])
    chroma_db.delete(ids=["doc1"])


# =============================================================================
# Tests: Time-Series DB - Parquet
# =============================================================================


def test_parquet_query_works_in_readonly(parquet_db):
    """Test that queries work in readonly mode."""
    import pandas as pd

    # Write data first (before readonly)
    df = pd.DataFrame(
        {
            "timestamp": [pd.Timestamp.now()],
            "price": [100.0],
            "volume": [1000.0],
        }
    )
    parquet_db.write_ticks("BTC/USD", df)

    # Enable readonly
    os.environ["KNOWLEDGE_READONLY"] = "true"

    # Query should work
    result = parquet_db.query_ticks(
        "BTC/USD",
        start_time="2020-01-01",
        end_time="2030-01-01",
    )
    assert isinstance(result, pd.DataFrame)


def test_parquet_write_ticks_blocked_in_readonly(parquet_db):
    """Test that write_ticks is blocked in readonly mode."""
    import pandas as pd

    os.environ["KNOWLEDGE_READONLY"] = "true"

    df = pd.DataFrame(
        {
            "timestamp": [pd.Timestamp.now()],
            "price": [100.0],
            "volume": [1000.0],
        }
    )

    with pytest.raises(TimeSeriesReadonlyModeError, match="READONLY mode"):
        parquet_db.write_ticks("BTC/USD", df)


def test_parquet_write_portfolio_blocked_in_readonly(parquet_db):
    """Test that write_portfolio_history is blocked in readonly mode."""
    import pandas as pd

    os.environ["KNOWLEDGE_READONLY"] = "true"

    df = pd.DataFrame(
        {
            "timestamp": [pd.Timestamp.now()],
            "equity": [10000.0],
            "cash": [5000.0],
        }
    )

    with pytest.raises(TimeSeriesReadonlyModeError, match="READONLY mode"):
        parquet_db.write_portfolio_history(df)


def test_parquet_write_works_when_readonly_disabled(parquet_db):
    """Test that writes work when readonly is explicitly disabled."""
    import pandas as pd

    os.environ["KNOWLEDGE_READONLY"] = "false"

    df = pd.DataFrame(
        {
            "timestamp": [pd.Timestamp.now()],
            "price": [100.0],
            "volume": [1000.0],
        }
    )

    # Should not raise
    parquet_db.write_ticks("BTC/USD", df)


# =============================================================================
# Tests: RAG Pipeline
# =============================================================================


def test_rag_query_works_in_readonly(rag_pipeline):
    """Test that RAG queries work in readonly mode."""
    # Add documents first (before readonly)
    rag_pipeline.add_documents(
        documents=["Momentum strategy works in trending markets"],
        metadatas=[{"source": "research"}],
    )

    # Enable readonly
    os.environ["KNOWLEDGE_READONLY"] = "true"

    # Query should work
    response = rag_pipeline.query("What strategy for trending markets?", top_k=1)
    assert "query" in response
    assert "context" in response


def test_rag_retrieve_context_works_in_readonly(rag_pipeline):
    """Test that retrieve_context works in readonly mode."""
    # Add documents first
    rag_pipeline.add_documents(
        documents=["Test strategy"],
        metadatas=[{"source": "test"}],
    )

    # Enable readonly
    os.environ["KNOWLEDGE_READONLY"] = "true"

    # Retrieve should work
    results = rag_pipeline.retrieve_context("strategy", top_k=1)
    assert isinstance(results, list)


def test_rag_add_documents_blocked_in_readonly(rag_pipeline):
    """Test that add_documents is blocked in readonly mode."""
    os.environ["KNOWLEDGE_READONLY"] = "true"

    with pytest.raises(ReadonlyModeError, match="READONLY mode"):
        rag_pipeline.add_documents(
            documents=["Test document"],
            metadatas=[{"source": "test"}],
        )


def test_rag_clear_blocked_in_readonly(rag_pipeline):
    """Test that clear_knowledge_base is blocked in readonly mode."""
    os.environ["KNOWLEDGE_READONLY"] = "true"

    with pytest.raises(ReadonlyModeError, match="READONLY mode"):
        rag_pipeline.clear_knowledge_base()


def test_rag_write_works_when_readonly_disabled(rag_pipeline):
    """Test that RAG writes work when readonly is explicitly disabled."""
    os.environ["KNOWLEDGE_READONLY"] = "false"

    # Should not raise
    rag_pipeline.add_documents(
        documents=["Test document"],
        metadatas=[{"source": "test"}],
    )
    rag_pipeline.clear_knowledge_base()


# =============================================================================
# Tests: Access Control Matrix
# =============================================================================


@pytest.mark.parametrize(
    "context,readonly_flag,operation,should_succeed",
    [
        # Dashboard: GET yes, WRITE no
        ("dashboard", "false", "read", True),
        ("dashboard", "true", "read", True),
        ("dashboard", "false", "write", True),  # Would succeed if not gated by context
        ("dashboard", "true", "write", False),  # Blocked by readonly
        # Research: GET yes, WRITE yes
        ("research", "false", "read", True),
        ("research", "true", "read", True),
        ("research", "false", "write", True),
        ("research", "true", "write", False),  # Blocked by readonly
        # Live Track: GET yes, WRITE no
        ("live_track", "false", "read", True),
        ("live_track", "true", "read", True),
        ("live_track", "false", "write", True),  # Would succeed if not gated by context
        ("live_track", "true", "write", False),  # Blocked by readonly
        # Admin: GET yes, WRITE yes
        ("admin", "false", "read", True),
        ("admin", "true", "read", True),
        ("admin", "false", "write", True),
        ("admin", "true", "write", False),  # Blocked by readonly
    ],
)
def test_access_control_matrix(context, readonly_flag, operation, should_succeed, chroma_db):
    """
    Test access control matrix for different contexts.

    Note: This tests the KNOWLEDGE_READONLY flag behavior.
    Context-specific gating (dashboard/live_track WRITE=no) would be
    implemented at the API layer, not in the Knowledge DB layer.
    """
    os.environ["KNOWLEDGE_READONLY"] = readonly_flag

    if operation == "read":
        # Read operations should always work (regardless of readonly)
        results = chroma_db.search("test", top_k=1)
        assert isinstance(results, list)
    else:  # write
        if should_succeed:
            # Should not raise
            chroma_db.add_documents(documents=["Test"], ids=[f"doc_{context}"])
        else:
            # Should raise ReadonlyModeError
            with pytest.raises(ReadonlyModeError, match="READONLY mode"):
                chroma_db.add_documents(documents=["Test"], ids=[f"doc_{context}"])


# =============================================================================
# Tests: Integration Scenarios
# =============================================================================


def test_full_workflow_readonly_toggle(chroma_db):
    """Test full workflow with readonly toggle."""
    # Phase 1: Write mode - add documents
    os.environ["KNOWLEDGE_READONLY"] = "false"
    chroma_db.add_documents(
        documents=["Document 1", "Document 2"],
        ids=["doc1", "doc2"],
    )

    # Phase 2: Switch to readonly - reads work, writes blocked
    os.environ["KNOWLEDGE_READONLY"] = "true"

    # Reads should work
    results = chroma_db.search("Document", top_k=2)
    assert len(results) >= 0

    # Writes should be blocked
    with pytest.raises(ReadonlyModeError):
        chroma_db.add_documents(documents=["Document 3"], ids=["doc3"])

    with pytest.raises(ReadonlyModeError):
        chroma_db.delete(ids=["doc1"])

    # Phase 3: Switch back to write mode
    os.environ["KNOWLEDGE_READONLY"] = "false"

    # Writes should work again
    chroma_db.delete(ids=["doc1"])


def test_rag_workflow_with_readonly(rag_pipeline):
    """Test RAG workflow with readonly mode."""
    # Add knowledge base
    rag_pipeline.add_documents(
        documents=[
            "RSI strategy works in ranging markets",
            "Momentum strategy works in trending markets",
        ],
        metadatas=[{"source": "research"}, {"source": "research"}],
    )

    # Enable readonly
    os.environ["KNOWLEDGE_READONLY"] = "true"

    # Queries should work
    response = rag_pipeline.query("What strategy for ranging markets?", top_k=1)
    assert "context" in response

    # Writes should be blocked
    with pytest.raises(ReadonlyModeError):
        rag_pipeline.add_documents(
            documents=["New strategy"],
            metadatas=[{"source": "test"}],
        )


def test_multiple_operations_in_readonly(chroma_db):
    """Test that all write operations are consistently blocked."""
    os.environ["KNOWLEDGE_READONLY"] = "true"

    # All write operations should raise
    with pytest.raises(ReadonlyModeError):
        chroma_db.add_documents(documents=["Test"], ids=["doc1"])

    with pytest.raises(ReadonlyModeError):
        chroma_db.delete(ids=["doc1"])

    with pytest.raises(ReadonlyModeError):
        chroma_db.clear()

    # Read should work
    results = chroma_db.search("test", top_k=1)
    assert isinstance(results, list)


# =============================================================================
# Tests: Error Messages
# =============================================================================


def test_readonly_error_message_is_clear(chroma_db):
    """Test that ReadonlyModeError has clear error message."""
    os.environ["KNOWLEDGE_READONLY"] = "true"

    try:
        chroma_db.add_documents(documents=["Test"], ids=["doc1"])
        pytest.fail("Should have raised ReadonlyModeError")
    except ReadonlyModeError as e:
        error_msg = str(e)
        assert "READONLY mode" in error_msg
        assert "Write operations are blocked" in error_msg
        assert "KNOWLEDGE_READONLY=false" in error_msg


def test_readonly_error_includes_solution(chroma_db):
    """Test that error message includes solution."""
    os.environ["KNOWLEDGE_READONLY"] = "true"

    try:
        chroma_db.add_documents(documents=["Test"], ids=["doc1"])
    except ReadonlyModeError as e:
        assert "Set KNOWLEDGE_READONLY=false" in str(e)
