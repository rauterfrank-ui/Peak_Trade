"""
Tests for LLM configuration.
"""

import pytest
from src.ai.llm_config import LLMConfig, LLMProvider, MockLLM


class TestLLMConfig:
    """Tests for LLMConfig."""
    
    def test_llm_config_initialization(self):
        """Test LLM config can be initialized."""
        config = LLMConfig()
        assert config.provider in ["openai", "anthropic", "local", "mock"]
        assert config.cost_tracking is True
    
    def test_llm_config_with_custom_config(self):
        """Test LLM config with custom settings."""
        custom_config = {
            "default_provider": "mock",
            "max_tokens": 2000,
            "temperature": 0.5,
        }
        config = LLMConfig(config=custom_config)
        
        assert config.provider == "mock"
        assert config.config["max_tokens"] == 2000
        assert config.config["temperature"] == 0.5
    
    def test_get_llm_mock(self):
        """Test getting mock LLM."""
        config = LLMConfig(config={"default_provider": "mock"})
        llm = config.get_llm()
        
        assert isinstance(llm, MockLLM)
    
    def test_track_usage(self):
        """Test tracking token usage."""
        config = LLMConfig()
        
        cost = config.track_usage(
            input_tokens=1000,
            output_tokens=500,
            provider="openai",
            model="gpt-3.5-turbo",
        )
        
        assert cost >= 0
        assert config.total_tokens["input"] == 1000
        assert config.total_tokens["output"] == 500
    
    def test_track_usage_accumulates(self):
        """Test that usage tracking accumulates."""
        config = LLMConfig()
        
        config.track_usage(input_tokens=1000, output_tokens=500)
        config.track_usage(input_tokens=500, output_tokens=250)
        
        assert config.total_tokens["input"] == 1500
        assert config.total_tokens["output"] == 750
    
    def test_get_stats(self):
        """Test getting usage statistics."""
        config = LLMConfig()
        config.track_usage(input_tokens=1000, output_tokens=500)
        
        stats = config.get_stats()
        
        assert "provider" in stats
        assert "model" in stats
        assert "total_cost_usd" in stats
        assert "total_tokens" in stats
        assert stats["total_tokens"]["input"] == 1000
        assert stats["total_tokens"]["output"] == 500
    
    def test_reset_stats(self):
        """Test resetting usage statistics."""
        config = LLMConfig()
        config.track_usage(input_tokens=1000, output_tokens=500)
        
        config.reset_stats()
        
        assert config.total_cost == 0.0
        assert config.total_tokens["input"] == 0
        assert config.total_tokens["output"] == 0
    
    def test_cost_tracking_disabled(self):
        """Test cost tracking can be disabled."""
        config = LLMConfig(config={"cost_tracking": False})
        
        cost = config.track_usage(input_tokens=1000, output_tokens=500)
        
        assert cost == 0.0


class TestMockLLM:
    """Tests for MockLLM."""
    
    def test_mock_llm_initialization(self):
        """Test mock LLM can be initialized."""
        llm = MockLLM()
        assert llm.model == "mock-model"
    
    def test_mock_llm_invoke(self):
        """Test mock LLM invoke."""
        llm = MockLLM()
        result = llm.invoke([{"role": "user", "content": "test"}])
        
        assert "content" in result
        assert "model" in result
    
    def test_mock_llm_callable(self):
        """Test mock LLM is callable."""
        llm = MockLLM()
        result = llm([{"role": "user", "content": "test"}])
        
        assert "content" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
