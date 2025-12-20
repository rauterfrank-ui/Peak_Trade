"""
Tests for Knowledge Database Integration

Tests for vector databases, time-series databases, RAG pipeline, and API manager.
"""

import pytest
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from knowledge import (
    VectorDBFactory,
    TimeSeriesDBFactory,
    RAGPipeline,
    StrategyRAG,
    MarketAnalysisRAG,
    APIManager,
)
import pandas as pd
from datetime import datetime
import tempfile
import shutil


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test data."""
    temp_path = tempfile.mkdtemp()
    yield temp_path
    shutil.rmtree(temp_path)


class TestVectorDB:
    """Tests for Vector Database integration."""

    def test_chroma_adapter_creation(self, temp_dir):
        """Test ChromaDB adapter creation."""
        config = {"persist_directory": temp_dir, "collection_name": "test_collection"}

        # May fail if chromadb not installed, which is fine
        try:
            vector_db = VectorDBFactory.create("chroma", config)
            assert vector_db is not None
        except ImportError:
            pytest.skip("ChromaDB not installed")

    def test_vector_db_factory_unknown_type(self):
        """Test VectorDBFactory with unknown type."""
        with pytest.raises(ValueError, match="Unknown database type"):
            VectorDBFactory.create("unknown_db", {})

    def test_chroma_add_and_search(self, temp_dir):
        """Test adding documents and searching in ChromaDB."""
        try:
            config = {
                "persist_directory": temp_dir,
                "collection_name": "test_collection",
            }
            vector_db = VectorDBFactory.create("chroma", config)

            # Add documents
            documents = ["Test document 1", "Test document 2"]
            metadatas = [{"source": "test1"}, {"source": "test2"}]
            ids = ["doc1", "doc2"]

            vector_db.add_documents(documents=documents, metadatas=metadatas, ids=ids)

            # Search
            results = vector_db.search("Test document", top_k=2)
            assert len(results) == 2
            assert all(isinstance(r, tuple) and len(r) == 3 for r in results)

        except ImportError:
            pytest.skip("ChromaDB not installed")


class TestTimeSeriesDB:
    """Tests for Time-Series Database integration."""

    def test_parquet_adapter_creation(self, temp_dir):
        """Test Parquet adapter creation."""
        config = {"base_path": temp_dir}
        ts_db = TimeSeriesDBFactory.create("parquet", config)
        assert ts_db is not None

    def test_timeseries_db_factory_unknown_type(self):
        """Test TimeSeriesDBFactory with unknown type."""
        with pytest.raises(ValueError, match="Unknown database type"):
            TimeSeriesDBFactory.create("unknown_db", {})

    def test_parquet_write_and_query_ticks(self, temp_dir):
        """Test writing and querying tick data."""
        config = {"base_path": temp_dir}
        ts_db = TimeSeriesDBFactory.create("parquet", config)

        # Create sample tick data
        data = pd.DataFrame(
            {
                "timestamp": pd.date_range("2024-01-01", periods=10, freq="H"),
                "price": [100 + i for i in range(10)],
                "volume": [1000 + i * 10 for i in range(10)],
            }
        )

        # Write ticks
        ts_db.write_ticks("BTC/USD", data, tags={"source": "test"})

        # Query ticks
        results = ts_db.query_ticks(
            "BTC/USD", start_time="2024-01-01", end_time="2024-01-02"
        )
        assert len(results) > 0
        assert "price" in results.columns
        assert "volume" in results.columns

    def test_parquet_write_and_query_portfolio(self, temp_dir):
        """Test writing and querying portfolio history."""
        config = {"base_path": temp_dir}
        ts_db = TimeSeriesDBFactory.create("parquet", config)

        # Create sample portfolio data
        data = pd.DataFrame(
            {
                "timestamp": pd.date_range("2024-01-01", periods=10, freq="D"),
                "equity": [10000 + i * 100 for i in range(10)],
                "cash": [5000 - i * 10 for i in range(10)],
                "positions_value": [5000 + i * 110 for i in range(10)],
            }
        )

        # Write portfolio history
        ts_db.write_portfolio_history(data, tags={"portfolio": "test"})

        # Query portfolio history
        results = ts_db.query_portfolio_history(
            start_time="2024-01-01", end_time="2024-01-10"
        )
        assert len(results) > 0
        assert "equity" in results.columns


class TestRAGPipeline:
    """Tests for RAG Pipeline."""

    def test_rag_pipeline_creation(self, temp_dir):
        """Test RAG pipeline creation."""
        try:
            config = {
                "persist_directory": temp_dir,
                "collection_name": "test_rag",
            }
            vector_db = VectorDBFactory.create("chroma", config)
            rag = RAGPipeline(vector_db=vector_db)
            assert rag is not None
        except ImportError:
            pytest.skip("ChromaDB not installed")

    def test_rag_add_documents_and_query(self, temp_dir):
        """Test RAG pipeline document addition and querying."""
        try:
            config = {
                "persist_directory": temp_dir,
                "collection_name": "test_rag",
            }
            vector_db = VectorDBFactory.create("chroma", config)
            rag = RAGPipeline(vector_db=vector_db)

            # Add documents
            documents = [
                "RSI strategy works in ranging markets",
                "Momentum strategy works in trending markets",
            ]
            metadatas = [{"type": "strategy"}, {"type": "strategy"}]

            rag.add_documents(documents=documents, metadatas=metadatas)

            # Query
            response = rag.query("What strategy for ranging market?", top_k=1)
            assert "query" in response
            assert "context" in response
            assert "sources" in response

        except ImportError:
            pytest.skip("ChromaDB not installed")

    def test_strategy_rag(self, temp_dir):
        """Test specialized Strategy RAG."""
        try:
            config = {
                "persist_directory": temp_dir,
                "collection_name": "test_strategy_rag",
            }
            vector_db = VectorDBFactory.create("chroma", config)
            strategy_rag = StrategyRAG(vector_db=vector_db)

            # Add strategy documents
            documents = ["RSI strategy for ranging markets with low risk"]
            metadatas = [{"type": "strategy", "risk": "low"}]

            strategy_rag.add_documents(documents=documents, metadatas=metadatas)

            # Get recommendation
            market_conditions = {"regime": "ranging", "volatility": "low"}
            recommendation = strategy_rag.recommend_strategy(
                market_conditions, top_k=1
            )

            assert "market_conditions" in recommendation
            assert "recommendations" in recommendation

        except ImportError:
            pytest.skip("ChromaDB not installed")

    def test_market_analysis_rag(self, temp_dir):
        """Test specialized Market Analysis RAG."""
        try:
            config = {
                "persist_directory": temp_dir,
                "collection_name": "test_market_rag",
            }
            vector_db = VectorDBFactory.create("chroma", config)
            market_rag = MarketAnalysisRAG(vector_db=vector_db)

            # Add market analysis documents
            documents = ["High volatility regime with trending behavior"]
            metadatas = [{"type": "regime_analysis"}]

            market_rag.add_documents(documents=documents, metadatas=metadatas)

            # Analyze regime
            current_metrics = {"volatility": 0.8, "trend_strength": 0.7}
            analysis = market_rag.analyze_regime(current_metrics, top_k=1)

            assert "current_metrics" in analysis
            assert "analysis" in analysis

        except ImportError:
            pytest.skip("ChromaDB not installed")


class TestAPIManager:
    """Tests for API Manager."""

    def test_api_manager_creation(self):
        """Test API Manager creation."""
        api_manager = APIManager()
        assert api_manager is not None

    def test_get_api_key_not_required(self):
        """Test getting API key that is not required."""
        api_manager = APIManager()
        key = api_manager.get_api_key("NONEXISTENT_KEY", required=False)
        assert key is None

    def test_get_api_key_required_missing(self):
        """Test getting required API key that is missing."""
        api_manager = APIManager()
        with pytest.raises(ValueError, match="API key .* not found"):
            api_manager.get_api_key("REQUIRED_MISSING_KEY", required=True)

    def test_validate_environment(self):
        """Test environment validation."""
        api_manager = APIManager()
        validation = api_manager.validate_environment()
        assert isinstance(validation, dict)
        assert "chroma" in validation
        assert validation["chroma"] is True  # No API key needed

    def test_get_db_config(self):
        """Test getting database configuration."""
        api_manager = APIManager()
        config = api_manager.get_db_config("chroma")
        assert isinstance(config, dict)
        assert "persist_directory" in config
        assert "collection_name" in config

    def test_track_request(self):
        """Test request tracking."""
        api_manager = APIManager()
        api_manager.track_request("test_api", "/test_endpoint", metadata={"foo": "bar"})
        stats = api_manager.get_usage_stats("test_api", hours=1)
        assert stats["request_count"] == 1
        assert stats["requests"][0]["endpoint"] == "/test_endpoint"

    def test_check_rate_limit(self):
        """Test rate limit checking."""
        api_manager = APIManager()
        # Should be within limits initially
        assert api_manager.check_rate_limit("test_api") is True

    def test_get_security_report(self):
        """Test security report generation."""
        api_manager = APIManager()
        report = api_manager.get_security_report()
        assert "timestamp" in report
        assert "environment_validation" in report
        assert "rotation_needed" in report
        assert "usage_summary" in report


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
