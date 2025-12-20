"""
LLM Configuration and Provider Management.
"""

from typing import Any, Dict, Optional
from enum import Enum
import logging
import os


logger = logging.getLogger(__name__)


class LLMProvider(Enum):
    """Supported LLM providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    LOCAL = "local"
    MOCK = "mock"  # For testing


# LLM Configuration
LLM_CONFIG = {
    "max_tokens": 4000,
    "temperature": 0.7,
    "cost_tracking": True,
    "default_provider": "openai",
}

# Token costs per provider (USD per 1K tokens)
LLM_COSTS = {
    "openai": {
        "gpt-4-turbo-preview": {"input": 0.01, "output": 0.03},
        "gpt-4": {"input": 0.03, "output": 0.06},
        "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},
    },
    "anthropic": {
        "claude-3-opus": {"input": 0.015, "output": 0.075},
        "claude-3-sonnet": {"input": 0.003, "output": 0.015},
    },
    "local": {
        "llama2": {"input": 0.0, "output": 0.0},
        "mixtral": {"input": 0.0, "output": 0.0},
    },
}


class LLMConfig:
    """
    LLM configuration manager.
    
    Handles configuration for multiple LLM providers and cost tracking.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize LLM configuration.
        
        Args:
            config: Configuration dict
        """
        self.config = config or LLM_CONFIG.copy()
        self.provider = self.config.get("default_provider", "openai")
        self.model = self._get_default_model()
        self.cost_tracking = self.config.get("cost_tracking", True)
        self.total_cost = 0.0
        self.total_tokens = {"input": 0, "output": 0}
        
        logger.info(f"Initialized LLM config: provider={self.provider}, model={self.model}")
    
    def _get_default_model(self) -> str:
        """Get default model for current provider."""
        defaults = {
            "openai": "gpt-4-turbo-preview",
            "anthropic": "claude-3-opus",
            "local": "llama2",
            "mock": "mock-model",
        }
        return defaults.get(self.provider, "gpt-3.5-turbo")
    
    def get_llm(self, provider: Optional[str] = None, model: Optional[str] = None):
        """
        Get LLM instance.
        
        Args:
            provider: LLM provider (uses default if not specified)
            model: Model name (uses default if not specified)
            
        Returns:
            LLM instance (or None if dependencies not available)
        """
        provider = provider or self.provider
        model = model or self.model
        
        if provider == "mock":
            return MockLLM(model=model)
        
        try:
            if provider == "openai":
                from langchain_openai import ChatOpenAI
                api_key = os.getenv("OPENAI_API_KEY")
                if not api_key:
                    logger.warning("OPENAI_API_KEY not set, using mock LLM")
                    return MockLLM(model=model)
                return ChatOpenAI(
                    model=model,
                    api_key=api_key,
                    max_tokens=self.config.get("max_tokens", 4000),
                    temperature=self.config.get("temperature", 0.7),
                )
            
            elif provider == "anthropic":
                from langchain_anthropic import ChatAnthropic
                api_key = os.getenv("ANTHROPIC_API_KEY")
                if not api_key:
                    logger.warning("ANTHROPIC_API_KEY not set, using mock LLM")
                    return MockLLM(model=model)
                return ChatAnthropic(
                    model=model,
                    api_key=api_key,
                    max_tokens=self.config.get("max_tokens", 4000),
                    temperature=self.config.get("temperature", 0.7),
                )
            
            elif provider == "local":
                # For local models, we would use Ollama or similar
                logger.warning("Local LLM not fully implemented, using mock")
                return MockLLM(model=model)
            
            else:
                raise ValueError(f"Unknown provider: {provider}")
        
        except ImportError as e:
            logger.warning(f"LLM dependencies not available: {e}. Using mock LLM.")
            return MockLLM(model=model)
    
    def track_usage(
        self,
        input_tokens: int,
        output_tokens: int,
        provider: Optional[str] = None,
        model: Optional[str] = None,
    ) -> float:
        """
        Track token usage and calculate cost.
        
        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            provider: LLM provider
            model: Model name
            
        Returns:
            Cost in USD
        """
        if not self.cost_tracking:
            return 0.0
        
        provider = provider or self.provider
        model = model or self.model
        
        # Update totals
        self.total_tokens["input"] += input_tokens
        self.total_tokens["output"] += output_tokens
        
        # Calculate cost
        if provider in LLM_COSTS and model in LLM_COSTS[provider]:
            costs = LLM_COSTS[provider][model]
            cost = (input_tokens / 1000 * costs["input"]) + (output_tokens / 1000 * costs["output"])
            self.total_cost += cost
            
            logger.debug(f"Usage tracked: {input_tokens} input, {output_tokens} output, ${cost:.4f}")
            return cost
        
        return 0.0
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get usage statistics.
        
        Returns:
            Dict with usage stats
        """
        return {
            "provider": self.provider,
            "model": self.model,
            "total_cost_usd": self.total_cost,
            "total_tokens": self.total_tokens,
        }
    
    def reset_stats(self) -> None:
        """Reset usage statistics."""
        self.total_cost = 0.0
        self.total_tokens = {"input": 0, "output": 0}
        logger.info("Reset LLM usage statistics")


class MockLLM:
    """Mock LLM for testing."""
    
    def __init__(self, model: str = "mock-model"):
        """Initialize mock LLM."""
        self.model = model
    
    def invoke(self, messages) -> Dict[str, Any]:
        """Mock invoke method."""
        return {
            "content": "This is a mock response from the LLM. Full implementation requires LangChain and API keys.",
            "model": self.model,
        }
    
    def __call__(self, *args, **kwargs):
        """Make the mock callable."""
        return self.invoke(args[0] if args else [])


# Global LLM config instance
_global_llm_config: Optional[LLMConfig] = None


def get_global_llm_config() -> LLMConfig:
    """
    Get the global LLM configuration.
    
    Returns:
        Global LLMConfig instance
    """
    global _global_llm_config
    if _global_llm_config is None:
        _global_llm_config = LLMConfig()
    return _global_llm_config
