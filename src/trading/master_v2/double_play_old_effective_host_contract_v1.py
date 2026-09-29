"""OLD effective Double-Play host contract compatibility v1 (boundary-only).

Restores historically proven DP-boundary semantics on CURRENT infrastructure
without modifying Double-Play core modules or falsifying freshness/provenance.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from src.governance.f1_m9_productive_runtime_threshold_consumer_wiring_v1 import (
    F1M9ProductiveRuntimeThresholdConsumerPathResultV1,
)
from trading.master_v2.double_play_runtime_typed_volatility_presence_gate_v1 import (
    DoublePlayTypedVolatilityPresenceGateResultV1,
)

SCHEMA_VERSION = "double_play_old_effective_host_contract/v1"
DECISION_CONFIG = "config/governance/double_play_old_effective_host_contract_v1_decision_v1.json"
REASON_PRESENCE_ALPHA_AT_DP_BOUNDARY = "OLD_EFFECTIVE_DP_PRESENCE_ALPHA_AT_BOUNDARY"

_REPO_ROOT = Path(__file__).resolve().parents[3]


def load_old_effective_host_contract_decision_v1(
    *, repo_root: Path | None = None
) -> dict[str, Any]:
    root = repo_root or _REPO_ROOT
    path = root / DECISION_CONFIG
    if not path.is_file():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def old_effective_host_contract_enabled_v1(*, repo_root: Path | None = None) -> bool:
    decision = load_old_effective_host_contract_decision_v1(repo_root=repo_root)
    return decision.get("owner_go") is True and decision.get("enabled") is True


def integrated_replay_presence_alpha_at_dp_boundary_v1(*, repo_root: Path | None = None) -> bool:
    if not old_effective_host_contract_enabled_v1(repo_root=repo_root):
        return False
    decision = load_old_effective_host_contract_decision_v1(repo_root=repo_root)
    return decision.get("integrated_replay_presence_alpha_at_dp_boundary") is True


def g17_cmc_bind_produced_only_v1(*, repo_root: Path | None = None) -> bool:
    if not old_effective_host_contract_enabled_v1(repo_root=repo_root):
        return False
    decision = load_old_effective_host_contract_decision_v1(repo_root=repo_root)
    return decision.get("g17_cmc_bind_produced_only") is True


def layered_core_cmc_mark_observation_init_v1(*, repo_root: Path | None = None) -> bool:
    if not old_effective_host_contract_enabled_v1(repo_root=repo_root):
        return False
    decision = load_old_effective_host_contract_decision_v1(repo_root=repo_root)
    return decision.get("layered_core_cmc_mark_observation_init") is True


def resolve_alpha_scope_entry_for_integrated_replay_v1(
    *,
    presence_gate: DoublePlayTypedVolatilityPresenceGateResultV1,
    consumer_path: F1M9ProductiveRuntimeThresholdConsumerPathResultV1,
    repo_root: Path | None = None,
) -> tuple[bool, tuple[str, ...]]:
    """Map F1/M9 consumer output to OLD effective DP admission at integrated replay."""
    enforced_alpha = bool(consumer_path.alpha_scope_entry_authority_allowed)
    presence_alpha = bool(presence_gate.alpha_scope_entry_authority_allowed)
    if not integrated_replay_presence_alpha_at_dp_boundary_v1(repo_root=repo_root):
        return enforced_alpha, ()
    if enforced_alpha == presence_alpha:
        return presence_alpha, ()
    return presence_alpha, (REASON_PRESENCE_ALPHA_AT_DP_BOUNDARY,)


def audit_consumer_enforcement_without_dp_block_v1(
    consumer_path: Mapping[str, Any] | F1M9ProductiveRuntimeThresholdConsumerPathResultV1,
) -> dict[str, Any]:
    """Non-authoritative audit slice; freshness/enforcement facts remain visible."""
    if hasattr(consumer_path, "to_dict"):
        payload = consumer_path.to_dict()
    else:
        payload = dict(consumer_path)
    return {
        "enforcement_applied": payload.get("enforcement_applied"),
        "alpha_scope_entry_authority_allowed_consumer": payload.get(
            "alpha_scope_entry_authority_allowed"
        ),
        "threshold_numeric_max_age_seconds": payload.get("threshold_numeric_max_age_seconds"),
        "reason_codes": list(payload.get("reason_codes") or ()),
    }


__all__ = [
    "DECISION_CONFIG",
    "REASON_PRESENCE_ALPHA_AT_DP_BOUNDARY",
    "SCHEMA_VERSION",
    "audit_consumer_enforcement_without_dp_block_v1",
    "g17_cmc_bind_produced_only_v1",
    "integrated_replay_presence_alpha_at_dp_boundary_v1",
    "layered_core_cmc_mark_observation_init_v1",
    "load_old_effective_host_contract_decision_v1",
    "old_effective_host_contract_enabled_v1",
    "resolve_alpha_scope_entry_for_integrated_replay_v1",
]
