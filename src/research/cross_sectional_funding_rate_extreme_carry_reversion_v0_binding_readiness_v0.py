"""Binding readiness owner for cross-sectional funding-rate extreme carry/reversion v0.

Materializes and ratifies the two missing readiness bindings:
- absolute_funding_extreme
- cost_survival

Fail-closed until both bindings PASS. No economic evaluation execution or authority effect.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Mapping, Sequence

from src.research.cross_sectional_funding_rate_extreme_carry_reversion_absolute_funding_extreme_binding_v0 import (
    AbsoluteFundingExtremeBindingStatus,
    evaluate_absolute_funding_extreme_binding_v0,
    materialize_absolute_funding_extreme_binding_v0,
)
from src.research.cross_sectional_funding_rate_extreme_carry_reversion_cost_survival_binding_v0 import (
    CostSurvivalBindingStatus,
    evaluate_cost_survival_binding_v0,
    materialize_cost_survival_binding_v0,
)

PACKAGE_MARKER = "CROSS_SECTIONAL_FUNDING_RATE_EXTREME_CARRY_REVERSION_V0_BINDING_READINESS_V0=true"
READINESS_OWNER = "cross_sectional_funding_rate_extreme_carry_reversion_v0_binding_readiness_v0"
READINESS_SCHEMA_VERSION = (
    "cross_sectional_funding_rate_extreme_carry_reversion_v0_binding_readiness.v0"
)
CONFIG_REL_PATH = "config/research/cross_sectional_funding_rate_extreme_carry_reversion_v0_binding_readiness_v0.json"

STRATEGY_ID = "cross_sectional_funding_rate_extreme_carry_reversion"
STRATEGY_VERSION = "v0"
SCOPE_NAME = "CROSS_SECTIONAL_FUNDING_RATE_EXTREME_CARRY_REVERSION_V0_OFFLINE_RESEARCH_SCOPE"
SOURCE_OPERATOR_REVIEW_EVIDENCE_DIR = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/research/"
    "operator_review_selected_material_new_research_scope_extreme_carry_reversion_v0_after_rank_delta_"
    "negative_v0_20260707T222915Z"
)

REUSED_PERSISTENCE_REVERSAL_FILTER_OWNER = (
    "cross_sectional_funding_rate_persistence_reversal_filter_v0_versioned_research_binding_v0"
)
REUSED_CARRY_INFRASTRUCTURE_OWNER = (
    "cross_sectional_funding_rate_carry_v0_versioned_research_binding_v0"
)

AUTHORITY_EFFECT = "NONE"
RUNTIME_EFFECT = "NONE"
ORDER_EFFECT = "NONE"


class BindingReadinessVerdict(str, Enum):
    READY = "READY"
    FAIL_CLOSED = "FAIL_CLOSED"


class BindingRatificationStatus(str, Enum):
    BINDINGS_RATIFIED = "BINDINGS_RATIFIED"
    FAIL_CLOSED_NOT_RATIFIED = "FAIL_CLOSED_NOT_RATIFIED"


@dataclass(frozen=True)
class ScopeBindingReadinessResultV0:
    strategy_id: str
    strategy_version: str
    scope_name: str
    verdict: BindingReadinessVerdict
    ratification_status: BindingRatificationStatus
    absolute_funding_extreme_status: AbsoluteFundingExtremeBindingStatus
    cost_survival_status: CostSurvivalBindingStatus
    scope_readiness: bool
    binding_ratified: bool
    evaluation_infrastructure_ready: bool
    evaluation_execution_authorized: bool
    economic_evaluation_executed: bool
    runtime_authority_granted: bool
    promotion_authority_granted: bool
    order_authority_granted: bool
    blockers: tuple[str, ...]


def _stable_digest(payload: Mapping[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def materialize_binding_readiness_envelope_v0() -> dict[str, Any]:
    absolute_binding = materialize_absolute_funding_extreme_binding_v0()
    cost_binding = materialize_cost_survival_binding_v0()
    envelope: dict[str, Any] = {
        "artifact_kind": "cross_sectional_funding_rate_extreme_carry_reversion_v0_binding_readiness",
        "schema_version": READINESS_SCHEMA_VERSION,
        "readiness_owner": READINESS_OWNER,
        "strategy_id": STRATEGY_ID,
        "strategy_version": STRATEGY_VERSION,
        "scope_name": SCOPE_NAME,
        "source_operator_review_evidence_dir": SOURCE_OPERATOR_REVIEW_EVIDENCE_DIR,
        "required_bindings": {
            "absolute_funding_extreme": absolute_binding,
            "cost_survival": cost_binding,
        },
        "reuse_owners": {
            "persistence_reversal_filter_owner": REUSED_PERSISTENCE_REVERSAL_FILTER_OWNER,
            "carry_infrastructure_owner": REUSED_CARRY_INFRASTRUCTURE_OWNER,
        },
        "authority_effect": AUTHORITY_EFFECT,
        "runtime_effect": RUNTIME_EFFECT,
        "order_effect": ORDER_EFFECT,
        "offline_only": True,
        "research_only": True,
        "economic_evaluation_executed": False,
        "economic_evaluation_authorized": False,
        "runtime_authority_granted": False,
        "promotion_authority_granted": False,
        "order_authority_granted": False,
        "binding_ratified": False,
        "evaluation_infrastructure_ready": False,
        "scope_readiness": False,
    }
    envelope["binding_readiness_digest"] = _stable_digest(
        {
            "required_bindings": envelope["required_bindings"],
            "strategy_id": STRATEGY_ID,
            "strategy_version": STRATEGY_VERSION,
        }
    )
    return envelope


def evaluate_scope_binding_readiness_v0(
    *,
    panel_funding_rates: Sequence[tuple[str, float | None]] | None = None,
    expected_carry_bps: float | None = None,
    funding_drag_bps: float | None = None,
    epoch_index: int = 2,
    envelope: Mapping[str, Any] | None = None,
) -> ScopeBindingReadinessResultV0:
    resolved = dict(envelope or materialize_binding_readiness_envelope_v0())
    absolute_binding = resolved["required_bindings"]["absolute_funding_extreme"]
    cost_binding = resolved["required_bindings"]["cost_survival"]

    if panel_funding_rates is None:
        absolute_result_status = AbsoluteFundingExtremeBindingStatus.BLOCKED
        absolute_blocker = "absolute_funding_extreme:missing_panel_inputs"
    else:
        absolute_result = evaluate_absolute_funding_extreme_binding_v0(
            panel_funding_rates,
            epoch_index=epoch_index,
            binding=absolute_binding,
        )
        absolute_result_status = absolute_result.status
        absolute_blocker = f"absolute_funding_extreme:{absolute_result.reason_code}"

    cost_result = evaluate_cost_survival_binding_v0(
        expected_carry_bps=expected_carry_bps,
        funding_drag_bps=funding_drag_bps,
        binding=cost_binding,
    )
    cost_result_status = cost_result.status
    cost_blocker = f"cost_survival:{cost_result.reason_code}"

    blockers: list[str] = []
    if absolute_result_status is not AbsoluteFundingExtremeBindingStatus.PASS:
        blockers.append(absolute_blocker)
    if cost_result_status is not CostSurvivalBindingStatus.PASS:
        blockers.append(cost_blocker)

    binding_ratified = not blockers
    scope_readiness = binding_ratified
    ratification_status = (
        BindingRatificationStatus.BINDINGS_RATIFIED
        if binding_ratified
        else BindingRatificationStatus.FAIL_CLOSED_NOT_RATIFIED
    )
    verdict = (
        BindingReadinessVerdict.READY if scope_readiness else BindingReadinessVerdict.FAIL_CLOSED
    )

    return ScopeBindingReadinessResultV0(
        strategy_id=STRATEGY_ID,
        strategy_version=STRATEGY_VERSION,
        scope_name=SCOPE_NAME,
        verdict=verdict,
        ratification_status=ratification_status,
        absolute_funding_extreme_status=absolute_result_status,
        cost_survival_status=cost_result_status,
        scope_readiness=scope_readiness,
        binding_ratified=binding_ratified,
        evaluation_infrastructure_ready=False,
        evaluation_execution_authorized=False,
        economic_evaluation_executed=False,
        runtime_authority_granted=False,
        promotion_authority_granted=False,
        order_authority_granted=False,
        blockers=tuple(blockers),
    )


def ratify_binding_readiness_envelope_v0(
    *,
    panel_funding_rates: Sequence[tuple[str, float | None]],
    expected_carry_bps: float,
    funding_drag_bps: float,
    epoch_index: int = 2,
) -> dict[str, Any]:
    envelope = materialize_binding_readiness_envelope_v0()
    readiness = evaluate_scope_binding_readiness_v0(
        panel_funding_rates=panel_funding_rates,
        expected_carry_bps=expected_carry_bps,
        funding_drag_bps=funding_drag_bps,
        epoch_index=epoch_index,
        envelope=envelope,
    )
    ratified = dict(envelope)
    ratified.update(
        {
            "binding_ratified": readiness.binding_ratified,
            "scope_readiness": readiness.scope_readiness,
            "ratification_status": readiness.ratification_status.value,
            "readiness_verdict": readiness.verdict.value,
            "absolute_funding_extreme_status": readiness.absolute_funding_extreme_status.value,
            "cost_survival_status": readiness.cost_survival_status.value,
            "blockers": list(readiness.blockers),
        }
    )
    return ratified


def write_binding_readiness_artifacts_v0(repo_root: Path) -> Path:
    payload = materialize_binding_readiness_envelope_v0()
    config_path = repo_root / CONFIG_REL_PATH
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return config_path


def serialize_binding_readiness_canonical_v0(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"
