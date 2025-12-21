"""
Knowledge Database Integration for Peak_Trade

This module provides integration with external knowledge databases for AI-based
research and decision-making processes:

- Vector databases (Chroma, Pinecone, Qdrant) for semantic search
- Time-series databases for ticks and portfolio histories
- RAG (Retrieval-Augmented Generation) support
- API configuration and security management

Main components:
- vector_db: Vector database integration for semantic search
- timeseries_db: Time-series database for historical data
- rag: Retrieval-Augmented Generation pipeline
- api_manager: API key management and security
"""

# Explicit imports to avoid circular dependencies
from src.knowledge.vector_db import VectorDBFactory, VectorDBInterface
from src.knowledge.timeseries_db import TimeSeriesDBFactory, TimeSeriesDBInterface
from src.knowledge.rag import RAGPipeline, StrategyRAG, MarketAnalysisRAG
from src.knowledge.api_manager import APIManager

__all__ = [
    "VectorDBFactory",
    "VectorDBInterface",
    "TimeSeriesDBFactory",
    "TimeSeriesDBInterface",
    "RAGPipeline",
    "StrategyRAG",
    "MarketAnalysisRAG",
    "APIManager",
]
