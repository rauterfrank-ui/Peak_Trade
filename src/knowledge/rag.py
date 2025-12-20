"""
Retrieval-Augmented Generation (RAG) Pipeline

Combines vector database search with AI prompts for knowledge-augmented responses.

Usage:
    from src.knowledge.rag import RAGPipeline
    
    # Initialize with vector DB
    rag = RAGPipeline(vector_db=my_vector_db)
    
    # Add knowledge documents
    rag.add_documents([
        "RSI strategy works best in ranging markets...",
        "Momentum strategies perform well in trending markets..."
    ])
    
    # Query with context
    response = rag.query(
        "What strategy should I use for a ranging market?",
        top_k=3
    )
"""

from typing import Any, Dict, List, Optional, Tuple
import logging
from .vector_db import VectorDBInterface

logger = logging.getLogger(__name__)


class RAGPipeline:
    """Retrieval-Augmented Generation pipeline for knowledge-enhanced AI responses."""

    def __init__(
        self,
        vector_db: VectorDBInterface,
        system_prompt: Optional[str] = None,
        max_context_length: int = 3000,
    ):
        """
        Initialize RAG pipeline.

        Args:
            vector_db: Vector database instance for document retrieval
            system_prompt: Optional system prompt for AI responses
            max_context_length: Maximum length of context to include
        """
        self.vector_db = vector_db
        self.max_context_length = max_context_length
        self.system_prompt = system_prompt or self._default_system_prompt()

        logger.info("RAG pipeline initialized")

    def _default_system_prompt(self) -> str:
        """Default system prompt for trading knowledge."""
        return """You are a trading strategy assistant for Peak_Trade.
You have access to a knowledge base of trading strategies, market analysis,
and historical performance data. Use the provided context to answer questions
accurately and provide actionable insights."""

    def add_documents(
        self,
        documents: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None,
    ) -> None:
        """
        Add documents to the knowledge base.

        Args:
            documents: List of document texts
            metadatas: Optional metadata for each document
            ids: Optional IDs for each document
        """
        self.vector_db.add_documents(documents=documents, metadatas=metadatas, ids=ids)
        logger.info(f"Added {len(documents)} documents to knowledge base")

    def retrieve_context(
        self, query: str, top_k: int = 5, filter_dict: Optional[Dict[str, Any]] = None
    ) -> List[Tuple[str, float, Dict[str, Any]]]:
        """
        Retrieve relevant context for a query.

        Args:
            query: Query string
            top_k: Number of documents to retrieve
            filter_dict: Optional metadata filters

        Returns:
            List of tuples: (document_text, similarity_score, metadata)
        """
        results = self.vector_db.search(query=query, top_k=top_k, filter_dict=filter_dict)
        logger.info(f"Retrieved {len(results)} context documents for query")
        return results

    def format_context(
        self, results: List[Tuple[str, float, Dict[str, Any]]]
    ) -> str:
        """
        Format retrieved documents into context string.

        Args:
            results: Search results from vector DB

        Returns:
            Formatted context string
        """
        if not results:
            return "No relevant context found."

        context_parts = []
        total_length = 0

        for i, (doc, score, metadata) in enumerate(results, 1):
            source = metadata.get("source", "unknown")
            doc_text = f"[Context {i} - Source: {source}]\n{doc}\n"

            if total_length + len(doc_text) > self.max_context_length:
                break

            context_parts.append(doc_text)
            total_length += len(doc_text)

        return "\n".join(context_parts)

    def query(
        self,
        query: str,
        top_k: int = 5,
        filter_dict: Optional[Dict[str, Any]] = None,
        include_sources: bool = True,
    ) -> Dict[str, Any]:
        """
        Query the RAG pipeline for knowledge-augmented responses.

        Args:
            query: User query
            top_k: Number of context documents to retrieve
            filter_dict: Optional metadata filters
            include_sources: Whether to include source documents in response

        Returns:
            Dict with:
                - query: Original query
                - context: Retrieved context
                - system_prompt: System prompt used
                - sources: List of source documents (if include_sources=True)
        """
        # Retrieve relevant context
        results = self.retrieve_context(query=query, top_k=top_k, filter_dict=filter_dict)

        # Format context
        context = self.format_context(results)

        # Prepare response
        response = {
            "query": query,
            "context": context,
            "system_prompt": self.system_prompt,
        }

        if include_sources:
            response["sources"] = [
                {
                    "text": doc,
                    "score": score,
                    "metadata": metadata,
                }
                for doc, score, metadata in results
            ]

        logger.info(f"Generated RAG response for query: {query[:50]}...")
        return response

    def query_with_history(
        self,
        query: str,
        conversation_history: List[Dict[str, str]],
        top_k: int = 5,
    ) -> Dict[str, Any]:
        """
        Query with conversation history for multi-turn interactions.

        Args:
            query: Current query
            conversation_history: List of previous exchanges (role, content)
            top_k: Number of context documents to retrieve

        Returns:
            Dict with query response and updated context
        """
        # Build enhanced query from history
        history_context = "\n".join(
            [f"{msg['role']}: {msg['content']}" for msg in conversation_history[-3:]]
        )
        enhanced_query = f"{history_context}\nCurrent question: {query}"

        # Query with enhanced context
        response = self.query(query=enhanced_query, top_k=top_k)
        response["original_query"] = query

        return response

    def clear_knowledge_base(self) -> None:
        """Clear all documents from the knowledge base."""
        self.vector_db.clear()
        logger.info("Cleared knowledge base")


class StrategyRAG(RAGPipeline):
    """Specialized RAG pipeline for trading strategies."""

    def _default_system_prompt(self) -> str:
        """Trading strategy-specific system prompt."""
        return """You are a trading strategy expert for Peak_Trade.
You have access to:
- Strategy definitions and parameters
- Backtest results and performance metrics
- Market regime analyses
- Risk management guidelines

Provide data-driven recommendations based on the retrieved context.
Always consider:
1. Risk management (max drawdown, position sizing)
2. Market conditions (regime, volatility)
3. Historical performance
4. Robustness across different scenarios"""

    def recommend_strategy(
        self, market_conditions: Dict[str, Any], top_k: int = 3
    ) -> Dict[str, Any]:
        """
        Recommend strategies based on current market conditions.

        Args:
            market_conditions: Dict with market state (regime, volatility, etc.)
            top_k: Number of strategy recommendations

        Returns:
            Dict with recommended strategies and reasoning
        """
        # Build query from market conditions
        condition_str = ", ".join(
            [f"{k}={v}" for k, v in market_conditions.items()]
        )
        query = f"Recommend trading strategies for: {condition_str}"

        # Query with strategy metadata filter
        response = self.query(
            query=query, top_k=top_k, filter_dict={"type": "strategy"}
        )

        return {
            "market_conditions": market_conditions,
            "recommendations": response,
        }


class MarketAnalysisRAG(RAGPipeline):
    """Specialized RAG pipeline for market analysis."""

    def _default_system_prompt(self) -> str:
        """Market analysis-specific system prompt."""
        return """You are a market analysis expert for Peak_Trade.
You have access to:
- Historical market data and patterns
- Regime change indicators
- Volatility analyses
- Correlation studies

Provide actionable insights based on historical context and current conditions.
Focus on:
1. Pattern recognition
2. Regime identification
3. Risk factors
4. Potential opportunities"""

    def analyze_regime(
        self, current_metrics: Dict[str, float], top_k: int = 5
    ) -> Dict[str, Any]:
        """
        Analyze current market regime based on metrics.

        Args:
            current_metrics: Current market metrics (volatility, trend, etc.)
            top_k: Number of historical comparisons

        Returns:
            Dict with regime analysis and historical context
        """
        # Build query from metrics
        metrics_str = ", ".join([f"{k}={v:.4f}" for k, v in current_metrics.items()])
        query = f"Analyze market regime with metrics: {metrics_str}"

        # Query with regime metadata filter
        response = self.query(
            query=query, top_k=top_k, filter_dict={"type": "regime_analysis"}
        )

        return {
            "current_metrics": current_metrics,
            "analysis": response,
        }
