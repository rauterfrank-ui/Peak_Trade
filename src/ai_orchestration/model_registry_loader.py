"""
Model Registry Loader

Loads and parses config/model_registry.toml into structured Python objects.

Reference:
- config/model_registry.toml
- docs/governance/matrix/AI_AUTONOMY_LAYER_MAP_MODEL_MATRIX.md
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import tomli as toml
except ImportError:
    import tomllib as toml

from .errors import ModelRegistryError


@dataclass
class ModelSpec:
    """Specification for a single AI model."""

    model_id: str
    provider: str
    family: str
    description: str
    context_window: int
    max_output_tokens: int
    cost_per_1k_input: float
    cost_per_1k_output: float
    latency_p50_ms: int
    latency_p99_ms: int
    capabilities: List[str]
    use_cases: List[str]
    rate_limit_rpm: int
    status: str
    deployment: Optional[str] = None
    notes: Optional[str] = None


@dataclass
class LayerMapping:
    """Layer-to-Model mapping from registry."""

    layer_id: str
    description: str
    primary: str
    fallback: List[str]  # Can be single string or list
    critic: str
    autonomy: str
    notes: Optional[str] = None


@dataclass
class ModelRegistry:
    """Parsed model registry with all models and layer mappings."""

    version: str
    effective_date: str
    owner: str
    models: Dict[str, ModelSpec]
    layer_mappings: Dict[str, LayerMapping]
    fallback_policy: Dict[str, Any]
    budget: Dict[str, Any]
    audit: Dict[str, Any]


class ModelRegistryLoader:
    """
    Loads and validates model_registry.toml.

    Usage:
        loader = ModelRegistryLoader()
        registry = loader.load()
        model = registry.models["gpt-5.2-pro"]
        layer = registry.layer_mappings["L2"]
    """

    def __init__(self, registry_path: Optional[Path] = None):
        """
        Initialize loader.

        Args:
            registry_path: Path to model_registry.toml (default: config/model_registry.toml)
        """
        if registry_path is None:
            repo_root = Path(__file__).parent.parent.parent
            registry_path = repo_root / "config" / "model_registry.toml"

        self.registry_path = registry_path

    def load(self) -> ModelRegistry:
        """
        Load and parse model_registry.toml.

        Returns:
            ModelRegistry object

        Raises:
            ModelRegistryError: If file not found or invalid
        """
        if not self.registry_path.exists():
            raise ModelRegistryError(f"Model registry not found: {self.registry_path}")

        try:
            with open(self.registry_path, "rb") as f:
                data = toml.load(f)
        except Exception as e:
            raise ModelRegistryError(f"Failed to parse model_registry.toml: {e}")

        # Validate required sections
        if "registry" not in data:
            raise ModelRegistryError("Missing 'registry' section")
        if "models" not in data:
            raise ModelRegistryError("Missing 'models' section")
        if "layer_mapping" not in data:
            raise ModelRegistryError("Missing 'layer_mapping' section")

        # Parse registry metadata
        registry_meta = data["registry"]
        version = registry_meta.get("version", "unknown")
        effective_date = registry_meta.get("effective_date", "unknown")
        owner = registry_meta.get("owner", "unknown")

        # Parse models
        models = {}
        for model_key, model_data in data["models"].items():
            try:
                # Extract model_id (strip "gpt-5-2-pro" -> "gpt-5.2-pro")
                model_id = model_data.get("model_id", model_key)
                models[model_id] = ModelSpec(
                    model_id=model_id,
                    provider=model_data["provider"],
                    family=model_data["family"],
                    description=model_data["description"],
                    context_window=model_data["context_window"],
                    max_output_tokens=model_data["max_output_tokens"],
                    cost_per_1k_input=model_data["cost_per_1k_input"],
                    cost_per_1k_output=model_data["cost_per_1k_output"],
                    latency_p50_ms=model_data["latency_p50_ms"],
                    latency_p99_ms=model_data["latency_p99_ms"],
                    capabilities=model_data["capabilities"],
                    use_cases=model_data["use_cases"],
                    rate_limit_rpm=model_data["rate_limit_rpm"],
                    status=model_data["status"],
                    deployment=model_data.get("deployment"),
                    notes=model_data.get("notes"),
                )
            except KeyError as e:
                raise ModelRegistryError(f"Model {model_key} missing required field: {e}")

        # Parse layer mappings
        layer_mappings = {}
        for layer_key, layer_data in data["layer_mapping"].items():
            try:
                layer_id = layer_data["layer_id"]
                # Fallback can be string or list
                fallback = layer_data["fallback"]
                if isinstance(fallback, str):
                    fallback = [fallback]
                layer_mappings[layer_id] = LayerMapping(
                    layer_id=layer_id,
                    description=layer_data["description"],
                    primary=layer_data["primary"],
                    fallback=fallback,
                    critic=layer_data["critic"],
                    autonomy=layer_data["autonomy"],
                    notes=layer_data.get("notes"),
                )
            except KeyError as e:
                raise ModelRegistryError(f"Layer mapping {layer_key} missing required field: {e}")

        # Parse optional sections
        fallback_policy = data.get("fallback_policy", {})
        budget = data.get("budget", {})
        audit = data.get("audit", {})

        return ModelRegistry(
            version=version,
            effective_date=effective_date,
            owner=owner,
            models=models,
            layer_mappings=layer_mappings,
            fallback_policy=fallback_policy,
            budget=budget,
            audit=audit,
        )

    def get_model(self, model_id: str) -> ModelSpec:
        """
        Get model spec by ID.

        Args:
            model_id: Model identifier (e.g., "gpt-5.2-pro")

        Returns:
            ModelSpec

        Raises:
            ModelRegistryError: If model not found
        """
        registry = self.load()
        if model_id not in registry.models:
            raise ModelRegistryError(f"Model not found in registry: {model_id}")
        return registry.models[model_id]

    def get_layer_mapping(self, layer_id: str) -> LayerMapping:
        """
        Get layer mapping by ID.

        Args:
            layer_id: Layer identifier (e.g., "L2")

        Returns:
            LayerMapping

        Raises:
            ModelRegistryError: If layer not found
        """
        registry = self.load()
        if layer_id not in registry.layer_mappings:
            raise ModelRegistryError(f"Layer not found in registry: {layer_id}")
        return registry.layer_mappings[layer_id]
