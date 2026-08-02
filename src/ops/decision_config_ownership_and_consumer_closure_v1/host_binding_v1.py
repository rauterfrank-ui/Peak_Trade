"""Productive Cap 6.3 decision-config binding for the single-future host.

CORE_LOGIC_CHANGE=false
NO_SILENT_FALLBACK=true
ONE_CONFIG_OWNER_PER_RUNTIME_VALUE=true
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from src.ops.decision_config_ownership_and_consumer_closure_v1.config_loader_v1 import (
    DecisionConfigError,
    load_canonical_decision_runtime_config_v1,
    reject_legacy_bridge_fallback_v1,
    reject_parallel_owner_conflict_v1,
)
from src.ops.decision_config_ownership_and_consumer_closure_v1.constants_v1 import (
    AUTHORITY_OWNER,
    CONFIG_VERSION,
    OWNER,
    PREDECESSOR_CAPABILITY,
    STATE_VERSION,
)
from src.ops.decision_config_ownership_and_consumer_closure_v1.models_v1 import (
    CanonicalDecisionRuntimeConfigV1,
    DecisionConfigBindingStateV1,
)
from src.ops.decision_config_ownership_and_consumer_closure_v1.persistence_v1 import (
    DecisionConfigPersistenceError,
    load_decision_config_state_v1,
    persist_decision_config_state_atomic_v1,
    prior_commit_exists,
)
from src.ops.decision_config_ownership_and_consumer_closure_v1.reason_codes_v1 import (
    DecisionConfigFailureCodeV1,
)


@dataclass
class HostDecisionConfigBindingV1:
    """Caller-owned Cap 6.3 config binding carried by BridgeSessionStateV1."""

    enabled: bool = True
    initialized: bool = False
    config_version: str = ""
    schema_version: str = ""
    config_digest: str = ""
    confirmation_epochs: int = 0
    up_distance: float = 0.0
    adverse_exit_distance: float = 0.0
    reversal_distance: float = 0.0
    owner: str = OWNER
    source_path: str = ""
    repository_sha: str = ""
    predecessor_config_digest_cap61: str = ""
    predecessor_config_digest_cap62: str = ""
    state_root: Optional[str] = None
    commit_sequence: int = 0
    prior_commit_seen: bool = False
    alpha_blocked: bool = False
    alpha_block_reason: str = ""
    typed_config: Optional[CanonicalDecisionRuntimeConfigV1] = field(default=None, repr=False)

    def effective_values(self) -> dict[str, Any]:
        return {
            "confirmation_epochs": int(self.confirmation_epochs),
            "up_distance": float(self.up_distance),
            "adverse_exit_distance": float(self.adverse_exit_distance),
            "reversal_distance": float(self.reversal_distance),
            "config_version": self.config_version,
            "config_digest": self.config_digest,
            "owner": self.owner,
        }

    def to_binding_state(self) -> DecisionConfigBindingStateV1:
        return DecisionConfigBindingStateV1(
            state_version=STATE_VERSION,
            config_version=self.config_version,
            schema_version=self.schema_version,
            config_digest=self.config_digest,
            confirmation_epochs=int(self.confirmation_epochs),
            up_distance=float(self.up_distance),
            adverse_exit_distance=float(self.adverse_exit_distance),
            reversal_distance=float(self.reversal_distance),
            owner=self.owner,
            repository_sha=self.repository_sha,
            predecessor_capability=PREDECESSOR_CAPABILITY,
            predecessor_config_digest_cap61=self.predecessor_config_digest_cap61,
            predecessor_config_digest_cap62=self.predecessor_config_digest_cap62,
            commit_sequence=int(self.commit_sequence),
            source_path=self.source_path,
        )


def _apply_typed_config(
    binding: HostDecisionConfigBindingV1,
    cfg: CanonicalDecisionRuntimeConfigV1,
) -> None:
    binding.typed_config = cfg
    binding.config_version = cfg.config_version
    binding.schema_version = cfg.schema_version
    binding.config_digest = cfg.config_digest()
    binding.confirmation_epochs = int(cfg.confirmation_epochs)
    binding.up_distance = float(cfg.up_distance)
    binding.adverse_exit_distance = float(cfg.adverse_exit_distance)
    binding.reversal_distance = float(cfg.reversal_distance)
    binding.owner = AUTHORITY_OWNER
    binding.source_path = cfg.source_path
    binding.initialized = True
    binding.alpha_blocked = False
    binding.alpha_block_reason = ""


def ensure_host_decision_config_binding_v1(
    binding: HostDecisionConfigBindingV1,
    *,
    repository_sha: str,
    state_root: Path | None = None,
    config_path: Path | None = None,
    predecessor_config_digest_cap61: str = "",
    predecessor_config_digest_cap62: str = "",
    persist: bool = True,
    allow_legacy_bridge_fallback: bool = False,
) -> HostDecisionConfigBindingV1:
    """Bind productive host to the canonical typed config owner (fail-closed)."""
    if not binding.enabled:
        return binding

    reject_legacy_bridge_fallback_v1(
        attempted=bool(allow_legacy_bridge_fallback),
        detail="allow_legacy_bridge_fallback",
    )

    try:
        cfg = load_canonical_decision_runtime_config_v1(config_path)
    except DecisionConfigError as exc:
        binding.alpha_blocked = True
        binding.alpha_block_reason = str(exc)
        raise

    root = (
        Path(state_root)
        if state_root is not None
        else (Path(binding.state_root) if binding.state_root else None)
    )
    binding.repository_sha = repository_sha
    binding.predecessor_config_digest_cap61 = predecessor_config_digest_cap61
    binding.predecessor_config_digest_cap62 = predecessor_config_digest_cap62
    if root is not None:
        binding.state_root = str(root)

    expected_digest = cfg.config_digest()
    if root is not None and prior_commit_exists(root):
        try:
            prior = load_decision_config_state_v1(
                root,
                expected_config_digest=expected_digest,
                expected_config_version=CONFIG_VERSION,
            )
        except DecisionConfigPersistenceError as exc:
            binding.alpha_blocked = True
            binding.alpha_block_reason = str(exc)
            raise
        binding.prior_commit_seen = True
        binding.commit_sequence = int(prior.commit_sequence)
        # Restart continuity: values must match persisted binding + live canonical owner.
        reject_parallel_owner_conflict_v1(
            owner_a_value=prior.confirmation_epochs,
            owner_b_value=cfg.confirmation_epochs,
            key="confirmation_epochs",
        )
        reject_parallel_owner_conflict_v1(
            owner_a_value=prior.up_distance,
            owner_b_value=cfg.up_distance,
            key="up_distance",
        )
        reject_parallel_owner_conflict_v1(
            owner_a_value=prior.adverse_exit_distance,
            owner_b_value=cfg.adverse_exit_distance,
            key="adverse_exit_distance",
        )
        reject_parallel_owner_conflict_v1(
            owner_a_value=prior.reversal_distance,
            owner_b_value=cfg.reversal_distance,
            key="reversal_distance",
        )

    _apply_typed_config(binding, cfg)

    if persist and root is not None:
        binding.commit_sequence = int(binding.commit_sequence) + 1
        persist_decision_config_state_atomic_v1(binding.to_binding_state(), state_root=root)
        binding.prior_commit_seen = True

    if not binding.initialized or not binding.config_digest:
        raise DecisionConfigError(
            DecisionConfigFailureCodeV1.PRODUCTIVE_CONSUMER_UNBOUND,
            "canonical_config_not_bound",
        )
    return binding


def require_bound_decision_config_v1(
    binding: HostDecisionConfigBindingV1,
) -> CanonicalDecisionRuntimeConfigV1:
    if binding.typed_config is None or not binding.initialized:
        raise DecisionConfigError(
            DecisionConfigFailureCodeV1.PRODUCTIVE_CONSUMER_UNBOUND,
            "host_binding_missing_typed_config",
        )
    if binding.alpha_blocked:
        raise DecisionConfigError(
            DecisionConfigFailureCodeV1.RESTART_CONFIG_MISMATCH,
            binding.alpha_block_reason,
        )
    return binding.typed_config
