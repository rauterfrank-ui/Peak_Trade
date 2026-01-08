"""
Runtime Orchestrator for AI Model Selection

Implements fail-closed, deterministic model selection based on:
- Layer Map (L0-L6)
- Model Registry
- Capability Scopes
- Autonomy Levels

Reference:
- docs/architecture/ai_autonomy_layer_map_v1.md
- config/model_registry.toml
- config/capability_scopes/*.toml
"""

import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Dict, Any

try:
    import tomli as toml
except ImportError:
    import tomllib as toml

from .models import AutonomyLevel


@dataclass
class SelectionConstraints:
    """Constraints for model selection."""

    max_cost_per_1k_tokens: Optional[float] = None
    max_latency_ms: Optional[int] = None
    required_capabilities: List[str] = field(default_factory=list)


@dataclass
class ModelSelection:
    """Result of orchestrator model selection."""

    layer_id: str
    autonomy_level: AutonomyLevel
    primary_model_id: str
    fallback_model_ids: List[str]
    critic_model_id: str
    capability_scope_id: str
    registry_version: str
    selection_reason: str  # Explainability
    selection_timestamp: str
    sod_validated: bool  # SoD check result

    def to_dict(self) -> dict:
        """Convert to dictionary for logging/serialization."""
        return {
            "layer_id": self.layer_id,
            "autonomy_level": self.autonomy_level.value,
            "primary_model_id": self.primary_model_id,
            "fallback_model_ids": self.fallback_model_ids,
            "critic_model_id": self.critic_model_id,
            "capability_scope_id": self.capability_scope_id,
            "registry_version": self.registry_version,
            "selection_reason": self.selection_reason,
            "selection_timestamp": self.selection_timestamp,
            "sod_validated": self.sod_validated,
        }


class OrchestratorError(Exception):
    """Base exception for orchestrator errors."""

    pass


class InvalidLayerError(OrchestratorError):
    """Invalid layer_id."""

    pass


class InvalidModelError(OrchestratorError):
    """Model not found in registry."""

    pass


class ForbiddenAutonomyError(OrchestratorError):
    """Forbidden autonomy level (e.g., EXEC)."""

    pass


class SoDViolationError(OrchestratorError):
    """Separation of Duties violation."""

    pass


class Orchestrator:
    """
    Runtime Orchestrator for AI Model Selection.

    Implements fail-closed, deterministic model selection.
    """

    def __init__(self, config_dir: Optional[Path] = None):
        """
        Initialize orchestrator.

        Args:
            config_dir: Path to config directory (default: repo_root/config)

        Raises:
            FileNotFoundError: If registry or scopes not found
            ValueError: If registry is invalid
        """
        # Feature flag check (safety default: disabled)
        self.enabled = os.getenv("ORCHESTRATOR_ENABLED", "false").lower() == "true"

        if config_dir is None:
            # Default: repo_root/config
            repo_root = Path(__file__).parent.parent.parent
            config_dir = repo_root / "config"

        self.config_dir = config_dir
        self.registry_path = config_dir / "model_registry.toml"
        self.scopes_dir = config_dir / "capability_scopes"

        # Load registry and scopes
        self.registry = self._load_registry()
        self.scopes = self._load_scopes()

        # Cache layer mappings
        self.layer_mapping = self.registry.get("layer_mapping", {})

    def _load_registry(self) -> dict:
        """Load and validate model registry."""
        if not self.registry_path.exists():
            raise FileNotFoundError(f"Model registry not found: {self.registry_path}")

        with open(self.registry_path, "rb") as f:
            registry = toml.load(f)

        # Validate required sections
        if "models" not in registry:
            raise ValueError("Registry missing 'models' section")
        if "layer_mapping" not in registry:
            raise ValueError("Registry missing 'layer_mapping' section")

        return registry

    def _load_scopes(self) -> Dict[str, dict]:
        """Load capability scopes."""
        if not self.scopes_dir.exists():
            raise FileNotFoundError(f"Scopes directory not found: {self.scopes_dir}")

        scopes = {}
        for scope_file in self.scopes_dir.glob("*.toml"):
            with open(scope_file, "rb") as f:
                scope_config = toml.load(f)
                layer_id = scope_config.get("scope", {}).get("layer_id")
                if layer_id:
                    scopes[layer_id] = scope_config

        return scopes

    def _validate_layer(self, layer_id: str) -> None:
        """
        Validate layer_id.

        Args:
            layer_id: Layer ID (L0-L6)

        Raises:
            InvalidLayerError: If layer_id is invalid
        """
        valid_layers = ["L0", "L1", "L2", "L3", "L4", "L5", "L6"]
        if layer_id not in valid_layers:
            raise InvalidLayerError(
                f"Invalid layer_id: {layer_id}. Must be one of {valid_layers}"
            )

        if layer_id not in self.layer_mapping:
            raise InvalidLayerError(
                f"Layer {layer_id} not found in registry layer_mapping"
            )

    def _validate_autonomy(self, autonomy_level: AutonomyLevel, layer_id: str) -> None:
        """
        Validate autonomy level.

        Args:
            autonomy_level: Autonomy level
            layer_id: Layer ID (for error messages)

        Raises:
            ForbiddenAutonomyError: If autonomy level is EXEC
        """
        if autonomy_level == AutonomyLevel.EXEC:
            raise ForbiddenAutonomyError(
                f"EXEC is forbidden for layer {layer_id}. "
                "Execution requires explicit Evidence Packs + CodeGate + Go/NoGo."
            )

    def _validate_model(self, model_id: str) -> None:
        """
        Validate model_id exists in registry.

        Args:
            model_id: Model ID (can use dots or dashes)

        Raises:
            InvalidModelError: If model not found in registry
        """
        models = self.registry.get("models", {})
        # Normalize: try both dots and dashes
        normalized = model_id.replace(".", "-")
        if normalized not in models:
            available = list(models.keys())
            raise InvalidModelError(
                f"Model {model_id} (normalized: {normalized}) not found in registry. Available: {available}"
            )

    def _validate_sod(self, primary_model_id: str, critic_model_id: str) -> None:
        """
        Validate Separation of Duties (SoD).

        Args:
            primary_model_id: Primary model ID
            critic_model_id: Critic model ID

        Raises:
            SoDViolationError: If primary == critic
        """
        if primary_model_id == critic_model_id:
            raise SoDViolationError(
                f"SoD FAIL: primary_model_id == critic_model_id ({primary_model_id}). "
                "Proposer and Critic MUST be different models."
            )

    def _normalize_model_id(self, model_id: str) -> str:
        """
        Normalize model ID (handle registry vs. actual model IDs).

        Args:
            model_id: Model ID from registry

        Returns:
            Normalized model ID (with dots replaced by dashes)
        """
        # Registry uses dots (e.g., "gpt-5.2-pro")
        # Actual model keys use dashes (e.g., "gpt-5-2-pro")
        return model_id.replace(".", "-")

    def select_model(
        self,
        layer_id: str,
        autonomy_level: AutonomyLevel,
        task_type: str = "general",
        constraints: Optional[SelectionConstraints] = None,
        context: Optional[dict] = None,
    ) -> ModelSelection:
        """
        Select model based on layer, autonomy, constraints.

        Args:
            layer_id: Layer ID (L0-L6)
            autonomy_level: Autonomy level (RO, REC, PROP, EXEC)
            task_type: Task type (e.g., "general", "research", "critique")
            constraints: Optional selection constraints
            context: Optional context for selection

        Returns:
            ModelSelection with explainability

        Raises:
            InvalidLayerError: Invalid layer_id
            InvalidModelError: Model not found in registry
            ForbiddenAutonomyError: EXEC is forbidden
            SoDViolationError: SoD violation (primary == critic)
            RuntimeError: Orchestrator disabled (safety default)
        """
        # Safety check: Orchestrator enabled?
        if not self.enabled:
            raise RuntimeError(
                "Orchestrator is disabled (safety default). "
                "Set ORCHESTRATOR_ENABLED=true to enable."
            )

        # 1. Validate layer
        self._validate_layer(layer_id)

        # 2. Validate autonomy
        self._validate_autonomy(autonomy_level, layer_id)

        # 3. Lookup layer mapping
        layer_config = self.layer_mapping[layer_id]
        primary_raw = layer_config.get("primary")
        fallback_raw = layer_config.get("fallback")
        critic_raw = layer_config.get("critic")

        # Handle "none" for L5/L6
        if primary_raw == "none":
            raise InvalidModelError(
                f"Layer {layer_id} has no LLM support (primary='none')"
            )

        # 4. Validate models exist in registry
        self._validate_model(primary_raw)
        self._validate_model(critic_raw)

        # Normalize model IDs
        primary_model_id = self._normalize_model_id(primary_raw)
        critic_model_id = self._normalize_model_id(critic_raw)

        # Handle fallback (can be string or list)
        fallback_model_ids = []
        if isinstance(fallback_raw, str):
            if fallback_raw != "none":
                self._validate_model(fallback_raw)
                fallback_model_ids = [self._normalize_model_id(fallback_raw)]
        elif isinstance(fallback_raw, list):
            for fb in fallback_raw:
                if fb != "none":
                    self._validate_model(fb)
                    fallback_model_ids.append(self._normalize_model_id(fb))

        # 5. Validate SoD
        self._validate_sod(primary_model_id, critic_model_id)

        # 6. Determine capability scope
        capability_scope_id = f"{layer_id}_{layer_config.get('description', '').lower().replace(' ', '_').replace('/', '_')}"

        # 7. Get registry version
        registry_version = self.registry.get("registry", {}).get("version", "unknown")

        # 8. Explainability
        selection_reason = (
            f"Layer {layer_id} ({layer_config.get('description')}) "
            f"with autonomy {autonomy_level.value} → "
            f"primary={primary_model_id}, critic={critic_model_id} "
            f"per registry v{registry_version}"
        )

        # 9. Return ModelSelection
        return ModelSelection(
            layer_id=layer_id,
            autonomy_level=autonomy_level,
            primary_model_id=primary_model_id,
            fallback_model_ids=fallback_model_ids,
            critic_model_id=critic_model_id,
            capability_scope_id=capability_scope_id,
            registry_version=registry_version,
            selection_reason=selection_reason,
            selection_timestamp=datetime.now(timezone.utc).isoformat(),
            sod_validated=True,  # Validated in step 5
        )

    def health_check(self) -> dict:
        """
        Health check for orchestrator.

        Returns:
            dict with health status
        """
        return {
            "enabled": self.enabled,
            "registry_version": self.registry.get("registry", {}).get("version"),
            "models_count": len(self.registry.get("models", {})),
            "layers_mapped": len(self.layer_mapping),
            "scopes_loaded": len(self.scopes),
            "status": "healthy" if self.enabled else "disabled",
        }
