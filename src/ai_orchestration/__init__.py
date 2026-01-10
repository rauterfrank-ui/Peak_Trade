"""
AI Orchestration Framework

Multi-model orchestration with Separation of Duties (SoD) checks,
Capability Scope enforcement, and deterministic audit trails.

Reference:
- Authoritative Matrix: docs/governance/ai_autonomy/AI_AUTONOMY_LAYER_MAP_MODEL_MATRIX.md
- Mandatory Fields Schema: docs/governance/ai_autonomy/SCHEMA_MANDATORY_FIELDS.md
"""

from .capability_scope_loader import CapabilityScope, CapabilityScopeLoader
from .errors import (
    CapabilityScopeError,
    ConfigurationError,
    DryRunError,
    ForbiddenAutonomyError,
    InvalidLayerError,
    InvalidModelError,
    ManifestGenerationError,
    ModelRegistryError,
    OrchestrationError,
    SoDViolationError,
)
from .evidence_pack_generator import (
    CapabilityScopeCheck,
    CriticArtifact,
    EvidencePackError,
    EvidencePackGenerator,
    ProposerArtifact,
)
from .l2_runner import (
    L2Runner,
    L2RunnerError,
    L2RunResult,
    SoDViolation,
    CapabilityScopeViolation,
)
from .model_client import (
    ModelClient,
    ModelClientError,
    ModelRequest,
    ModelResponse,
    OpenAIClient,
    ReplayClient,
    create_model_client,
)
from .model_registry_loader import LayerMapping, ModelRegistry, ModelRegistryLoader, ModelSpec
from .models import (
    AutonomyLevel,
    CapabilityScopeMetadata,
    CriticDecision,
    LayerRunMetadata,
    RunLogging,
    SoDCheckResult,
    SoDResult,
)
from .run_manifest import RunManifest, RunManifestGenerator, generate_operator_output
from .runner import MultiModelRunner
from .sod_checker import SoDCheck, SoDChecker
from .transcript_store import TranscriptStore, TranscriptStoreError

__all__ = [
    # Models
    "LayerRunMetadata",
    "CapabilityScopeMetadata",
    "RunLogging",
    "SoDCheckResult",
    "AutonomyLevel",
    "SoDResult",
    "CriticDecision",
    # Loaders
    "ModelRegistryLoader",
    "ModelRegistry",
    "ModelSpec",
    "LayerMapping",
    "CapabilityScopeLoader",
    "CapabilityScope",
    # SoD
    "SoDChecker",
    "SoDCheck",
    # Manifest
    "RunManifest",
    "RunManifestGenerator",
    "generate_operator_output",
    # Runner
    "MultiModelRunner",
    # Model Client (Phase 3)
    "ModelClient",
    "OpenAIClient",
    "ReplayClient",
    "create_model_client",
    "ModelRequest",
    "ModelResponse",
    "ModelClientError",
    # Transcript Store (Phase 3)
    "TranscriptStore",
    "TranscriptStoreError",
    # Evidence Pack (Phase 3)
    "EvidencePackGenerator",
    "ProposerArtifact",
    "CriticArtifact",
    "CapabilityScopeCheck",
    "EvidencePackError",
    # L2 Runner (Phase 3)
    "L2Runner",
    "L2RunResult",
    "L2RunnerError",
    "SoDViolation",
    "CapabilityScopeViolation",
    # Errors
    "OrchestrationError",
    "ConfigurationError",
    "ModelRegistryError",
    "CapabilityScopeError",
    "InvalidLayerError",
    "InvalidModelError",
    "ForbiddenAutonomyError",
    "SoDViolationError",
    "ManifestGenerationError",
    "DryRunError",
]
