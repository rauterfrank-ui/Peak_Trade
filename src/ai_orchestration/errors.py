"""
Custom Exceptions for AI Orchestration Framework

Centralized exception hierarchy for all orchestration operations.

Reference:
- docs/governance/matrix/AI_AUTONOMY_LAYER_MAP_MODEL_MATRIX.md
"""


class OrchestrationError(Exception):
    """Base exception for all orchestration errors."""

    pass


class ConfigurationError(OrchestrationError):
    """Configuration file missing or invalid."""

    pass


class ModelRegistryError(ConfigurationError):
    """Model registry TOML missing or invalid."""

    pass


class CapabilityScopeError(ConfigurationError):
    """Capability scope TOML missing or invalid."""

    pass


class InvalidLayerError(OrchestrationError):
    """Invalid layer_id (must be L0-L6)."""

    pass


class InvalidModelError(OrchestrationError):
    """Model not found in registry."""

    pass


class ForbiddenAutonomyError(OrchestrationError):
    """Forbidden autonomy level (e.g., EXEC without approval)."""

    pass


class SoDViolationError(OrchestrationError):
    """Separation of Duties violation (proposer == critic)."""

    pass


class ManifestGenerationError(OrchestrationError):
    """Failed to generate run manifest or operator output."""

    pass


class DryRunError(OrchestrationError):
    """Dry-run validation failed."""

    pass
