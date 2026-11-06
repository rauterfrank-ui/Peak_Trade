"""
Tests for Model Registry Loader

Tests TOML parsing, validation, and error handling.
"""

import pytest
from pathlib import Path

from src.ai_orchestration import (
    ModelRegistryLoader,
    ModelRegistryError,
    ModelSpec,
    LayerMapping,
)


def test_load_model_registry_success():
    """Test successful model registry loading."""
    loader = ModelRegistryLoader()
    registry = loader.load()

    # Check metadata
    assert registry.version == "1.0"
    assert registry.owner == "ops"

    # Check models exist
    assert "gpt-5.2-pro" in registry.models
    assert "deepseek-r1" in registry.models
    assert "o3-deep-research" in registry.models

    # Check layer mappings
    assert "L0" in registry.layer_mappings
    assert "L2" in registry.layer_mappings
    assert "L4" in registry.layer_mappings


def test_load_model_spec():
    """Test loading individual model spec."""
    loader = ModelRegistryLoader()
    model = loader.get_model("gpt-5.2-pro")

    assert isinstance(model, ModelSpec)
    assert model.model_id == "gpt-5.2-pro"
    assert model.provider == "openai"
    assert model.family == "gpt-5"
    assert model.context_window == 200000
    assert "reasoning" in model.capabilities
    assert "L2_market_outlook" in model.use_cases


def test_load_layer_mapping():
    """Test loading layer mapping."""
    loader = ModelRegistryLoader()
    layer = loader.get_layer_mapping("L2")

    assert isinstance(layer, LayerMapping)
    assert layer.layer_id == "L2"
    assert layer.description == "Market Outlook"
    assert layer.primary == "gpt-5.2-pro"
    assert layer.fallback == ["gpt-5.2"]
    assert layer.critic == "deepseek-r1"
    assert layer.autonomy == "PROP"


def test_load_deepseek_model():
    """Test loading DeepSeek heterogeneous model."""
    loader = ModelRegistryLoader()
    model = loader.get_model("deepseek-r1")

    assert model.model_id == "deepseek-r1"
    assert model.provider == "deepseek"
    assert "heterogeneous-sod" in model.capabilities
    assert "L0_critic" in model.use_cases
    assert "L2_critic" in model.use_cases


def test_model_not_found():
    """Test error when model not found."""
    loader = ModelRegistryLoader()

    with pytest.raises(ModelRegistryError, match="Model not found"):
        loader.get_model("nonexistent-model")


def test_layer_not_found():
    """Test error when layer not found."""
    loader = ModelRegistryLoader()

    with pytest.raises(ModelRegistryError, match="Layer not found"):
        loader.get_layer_mapping("L99")


def test_registry_has_budget_section():
    """Test that budget section is loaded."""
    loader = ModelRegistryLoader()
    registry = loader.load()

    assert "daily_cost_limit_usd" in registry.budget
    assert registry.budget["daily_cost_limit_usd"] == 50.0


def test_registry_has_audit_section():
    """Test that audit section is loaded."""
    loader = ModelRegistryLoader()
    registry = loader.load()

    assert registry.audit["log_all_model_calls"] is True
    assert "run_id" in registry.audit["required_log_fields"]


def test_layer_l6_forbidden():
    """Test L6 execution layer is marked as forbidden."""
    loader = ModelRegistryLoader()
    layer = loader.get_layer_mapping("L6")

    assert layer.layer_id == "L6"
    assert layer.description == "Execution"
    assert layer.primary == "none"
    assert "forbidden" in layer.autonomy.lower()


def test_fallback_as_list():
    """Test fallback can be a list (L1 has multiple fallbacks)."""
    loader = ModelRegistryLoader()
    layer = loader.get_layer_mapping("L1")

    assert isinstance(layer.fallback, list)
    assert len(layer.fallback) >= 2
    assert "o4-mini-deep-research" in layer.fallback
    assert "deepseek-r1" in layer.fallback
