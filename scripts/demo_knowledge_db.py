#!/usr/bin/env python3
"""
Example: Knowledge Database Integration Demo

This script demonstrates the usage of the knowledge database integration
for AI-based research and portfolio decision-making.

Usage:
    python scripts/demo_knowledge_db.py
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from knowledge import (
    VectorDBFactory,
    TimeSeriesDBFactory,
    RAGPipeline,
    StrategyRAG,
    APIManager,
)
import pandas as pd
from datetime import datetime


def demo_vector_db():
    """Demo: Vector Database for semantic search."""
    print("\n" + "=" * 80)
    print("DEMO 1: Vector Database - Semantic Search")
    print("=" * 80)

    # Initialize API Manager and Vector DB
    api_manager = APIManager()
    config = api_manager.get_db_config("chroma")

    vector_db = VectorDBFactory.create("chroma", config)

    # Add sample strategy documents
    documents = [
        "RSI Strategy: Mean-reversion strategy using RSI indicator. "
        "Works best in ranging markets with RSI thresholds at 30/70. "
        "Risk level: Medium. Recommended timeframe: 1h-4h.",
        "Momentum Strategy: Trend-following strategy using price momentum. "
        "Performs well in trending markets with strong directional moves. "
        "Risk level: Medium-High. Recommended timeframe: 1h-4h.",
        "MA Crossover: Classic trend-following using moving average crossovers. "
        "Simple but robust in trending markets. "
        "Risk level: Medium. Recommended timeframe: 4h-1d.",
        "Bollinger Bands: Mean-reversion strategy using volatility bands. "
        "Best in ranging markets with low to medium volatility. "
        "Risk level: Medium. Recommended timeframe: 1h-4h.",
    ]

    metadatas = [
        {
            "source": "internal_strategy_docs",
            "timestamp": datetime.now().isoformat(),
            "category": "strategy",
            "strategy_type": "mean_reversion",
            "market_regime": "ranging",
        },
        {
            "source": "internal_strategy_docs",
            "timestamp": datetime.now().isoformat(),
            "category": "strategy",
            "strategy_type": "trend_following",
            "market_regime": "trending",
        },
        {
            "source": "internal_strategy_docs",
            "timestamp": datetime.now().isoformat(),
            "category": "strategy",
            "strategy_type": "trend_following",
            "market_regime": "trending",
        },
        {
            "source": "internal_strategy_docs",
            "timestamp": datetime.now().isoformat(),
            "category": "strategy",
            "strategy_type": "mean_reversion",
            "market_regime": "ranging",
        },
    ]

    ids = ["rsi_strategy", "momentum_strategy", "ma_crossover", "bollinger_bands"]

    print("\n📝 Adding strategy documents to vector database...")
    vector_db.add_documents(documents=documents, metadatas=metadatas, ids=ids)
    print("✅ Successfully added 4 strategy documents")

    # Search for strategies
    queries = [
        "What strategy works best for a ranging market?",
        "Find me a trend-following strategy",
        "Which strategy has medium risk?",
    ]

    for query in queries:
        print(f"\n🔍 Query: {query}")
        results = vector_db.search(query, top_k=2)

        for i, (doc, score, metadata) in enumerate(results, 1):
            print(f"\n  Result {i} (score: {score:.4f}):")
            print(f"    {doc[:100]}...")
            print(f"    Type: {metadata.get('strategy_type')}")
            print(f"    Regime: {metadata.get('market_regime')}")


def demo_timeseries_db():
    """Demo: Time-Series Database for portfolio history."""
    print("\n" + "=" * 80)
    print("DEMO 2: Time-Series Database - Portfolio History")
    print("=" * 80)

    # Initialize Time-Series DB
    ts_db = TimeSeriesDBFactory.create(
        "parquet", config={"base_path": "./data/timeseries_demo"}
    )

    # Create sample portfolio history
    dates = pd.date_range(start="2024-01-01", end="2024-12-31", freq="D")
    portfolio_data = pd.DataFrame(
        {
            "timestamp": dates,
            "equity": [10000 + i * 10 + (i % 30) * 5 for i in range(len(dates))],
            "cash": [5000 - i * 2 for i in range(len(dates))],
            "positions_value": [5000 + i * 12 + (i % 30) * 5 for i in range(len(dates))],
        }
    )

    print("\n📊 Writing portfolio history to time-series database...")
    ts_db.write_portfolio_history(
        portfolio_data, tags={"portfolio": "demo", "strategy": "multi"}
    )
    print("✅ Successfully written 365 days of portfolio history")

    # Query portfolio history
    print("\n📈 Querying portfolio history for Q4 2024...")
    results = ts_db.query_portfolio_history(
        start_time="2024-10-01", end_time="2024-12-31"
    )

    print(f"   Retrieved {len(results)} records")
    print(f"   Start equity: ${results.iloc[0]['equity']:.2f}")
    print(f"   End equity: ${results.iloc[-1]['equity']:.2f}")
    print(f"   Return: {((results.iloc[-1]['equity'] / results.iloc[0]['equity']) - 1) * 100:.2f}%")


def demo_rag_pipeline():
    """Demo: RAG Pipeline for knowledge-augmented queries."""
    print("\n" + "=" * 80)
    print("DEMO 3: RAG Pipeline - Knowledge-Augmented Queries")
    print("=" * 80)

    # Initialize RAG Pipeline
    api_manager = APIManager()
    config = api_manager.get_db_config("chroma")
    vector_db = VectorDBFactory.create("chroma", config)

    rag = RAGPipeline(vector_db=vector_db)

    # Add knowledge documents
    knowledge_docs = [
        "Backtest Result (2024-Q1): RSI Strategy on BTC/EUR achieved Sharpe Ratio 1.8, "
        "Max Drawdown 12%, Win Rate 58%. Best performance in ranging markets.",
        "Backtest Result (2024-Q2): Momentum Strategy on ETH/USD achieved Sharpe Ratio 2.1, "
        "Max Drawdown 15%, Win Rate 62%. Excelled during trending bull market.",
        "Risk Management: Always use stop-loss at 2% of position value. "
        "Maximum portfolio drawdown limit: 20%. Never risk more than 1% per trade.",
        "Market Regime Analysis (Dec 2024): Current volatility is elevated, "
        "trending regime with strong momentum. Favor trend-following strategies.",
    ]

    metadatas = [
        {"source": "backtest", "timestamp": "2024-03-31", "category": "performance"},
        {"source": "backtest", "timestamp": "2024-06-30", "category": "performance"},
        {"source": "risk_policy", "timestamp": "2024-01-01", "category": "risk"},
        {
            "source": "market_analysis",
            "timestamp": "2024-12-20",
            "category": "regime",
        },
    ]

    print("\n📚 Building knowledge base...")
    rag.add_documents(documents=knowledge_docs, metadatas=metadatas)
    print("✅ Added 4 knowledge documents")

    # Query with RAG
    queries = [
        "What strategy performed best in Q2 2024?",
        "What are the risk management rules?",
        "What strategy should I use in the current market regime?",
    ]

    for query in queries:
        print(f"\n❓ Query: {query}")
        response = rag.query(query, top_k=2)

        print("\n   📖 Context Retrieved:")
        print(response["context"][:300] + "...")

        if response.get("sources"):
            print(f"\n   📄 Sources: {len(response['sources'])} documents")


def demo_strategy_rag():
    """Demo: Specialized Strategy RAG for recommendations."""
    print("\n" + "=" * 80)
    print("DEMO 4: Strategy RAG - Smart Recommendations")
    print("=" * 80)

    # Initialize Strategy RAG
    api_manager = APIManager()
    config = api_manager.get_db_config("chroma")
    vector_db = VectorDBFactory.create("chroma", config)

    strategy_rag = StrategyRAG(vector_db=vector_db)

    # Add strategy knowledge
    strategy_docs = [
        "RSI Strategy (Conservative): RSI thresholds 25/75, stop-loss 2%, "
        "max drawdown 10%. Sharpe Ratio: 1.5. Best for: Low volatility ranging markets.",
        "RSI Strategy (Aggressive): RSI thresholds 35/65, stop-loss 3%, "
        "max drawdown 15%. Sharpe Ratio: 1.9. Best for: Medium volatility ranging markets.",
        "Momentum Strategy (Conservative): Momentum period 20, stop-loss 2%, "
        "max drawdown 12%. Sharpe Ratio: 1.7. Best for: Trending markets with confirmed trend.",
        "Momentum Strategy (Aggressive): Momentum period 10, stop-loss 3%, "
        "max drawdown 18%. Sharpe Ratio: 2.2. Best for: Strong trending markets.",
    ]

    metadatas = [
        {
            "source": "strategy_library",
            "category": "strategy",
            "type": "strategy",
            "risk_profile": "conservative",
        },
        {
            "source": "strategy_library",
            "category": "strategy",
            "type": "strategy",
            "risk_profile": "aggressive",
        },
        {
            "source": "strategy_library",
            "category": "strategy",
            "type": "strategy",
            "risk_profile": "conservative",
        },
        {
            "source": "strategy_library",
            "category": "strategy",
            "type": "strategy",
            "risk_profile": "aggressive",
        },
    ]

    print("\n📚 Building strategy knowledge base...")
    strategy_rag.add_documents(documents=strategy_docs, metadatas=metadatas)
    print("✅ Added 4 strategy configurations")

    # Get recommendations
    market_conditions = {
        "regime": "ranging",
        "volatility": "low",
        "risk_tolerance": "conservative",
    }

    print(f"\n🎯 Market Conditions: {market_conditions}")
    print("\n💡 Strategy Recommendation:")

    recommendation = strategy_rag.recommend_strategy(market_conditions, top_k=2)

    if recommendation["recommendations"].get("sources"):
        for i, source in enumerate(recommendation["recommendations"]["sources"], 1):
            print(f"\n   Option {i}:")
            print(f"     {source['text'][:150]}...")
            print(f"     Score: {source['score']:.4f}")


def demo_api_security():
    """Demo: API Security & Key Management."""
    print("\n" + "=" * 80)
    print("DEMO 5: API Security & Key Management")
    print("=" * 80)

    api_manager = APIManager()

    # Environment validation
    print("\n🔐 Environment Validation:")
    validation = api_manager.validate_environment()
    for api_name, is_valid in validation.items():
        status = "✅" if is_valid else "❌"
        print(f"   {status} {api_name}: {'Available' if is_valid else 'Not configured'}")

    # Security report
    print("\n📊 Security Report:")
    report = api_manager.get_security_report()

    print(f"   Timestamp: {report['timestamp']}")
    print(f"   Monitored APIs: {len(report['usage_summary'])}")

    # Track some requests
    print("\n📡 Tracking API requests...")
    api_manager.track_request("chroma", endpoint="/add_documents", metadata={"count": 4})
    api_manager.track_request("chroma", endpoint="/query", metadata={"top_k": 5})

    stats = api_manager.get_usage_stats("chroma", hours=1)
    print(f"   Recent requests (last 1h): {stats['request_count']}")

    # Rate limit check
    within_limit = api_manager.check_rate_limit("chroma")
    print(f"   Rate limit status: {'✅ OK' if within_limit else '❌ Exceeded'}")


def main():
    """Run all demos."""
    print("\n" + "=" * 80)
    print("PEAK_TRADE KNOWLEDGE DATABASE INTEGRATION DEMO")
    print("=" * 80)
    print("\nThis demo showcases:")
    print("  1. Vector Database for semantic search")
    print("  2. Time-Series Database for portfolio history")
    print("  3. RAG Pipeline for knowledge-augmented queries")
    print("  4. Strategy RAG for smart recommendations")
    print("  5. API Security & Key Management")

    try:
        demo_vector_db()
        demo_timeseries_db()
        demo_rag_pipeline()
        demo_strategy_rag()
        demo_api_security()

        print("\n" + "=" * 80)
        print("✅ ALL DEMOS COMPLETED SUCCESSFULLY")
        print("=" * 80)
        print("\nNext Steps:")
        print("  - Review docs/KNOWLEDGE_SOURCES_GOVERNANCE_PLAYBOOK.md")
        print("  - Add your own knowledge sources")
        print("  - Integrate with research pipeline")
        print("  - Set up monitoring and alerts")

    except ImportError as e:
        print(f"\n❌ Error: Missing dependency: {e}")
        print("\nTo install required packages:")
        print("  pip install chromadb  # For vector database")
        print("  # Optional: pip install qdrant-client pinecone-client influxdb-client")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
