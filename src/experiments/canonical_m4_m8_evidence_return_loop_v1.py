"""M4–M8 canonical single-cycle evidence return loop (forward + return, authority=NONE).

Composes existing M1→M4→M5→M6→M7 contract owners only. Does not execute trading selection,
promotion, productive writes, or P5 L6 producer bridges.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Final, Mapping

from src.experiments.canonical_deterministic_multi_cycle_offline_replay_v1 import (
    BOUND_CONTRACT_VERSIONS,
    OfflineReplayCycleInputV1,
    run_offline_evidence_cycle_v1,
)
from src.experiments.canonical_meta_to_optimization_feedback_v1 import (
    SCHEMA_VERSION as M7_SCHEMA_VERSION,
    TRADING_SELECTION_EFFECT,
)
from src.experiments.canonical_meta_learning_ingest_v1 import (
    INGEST_STATUS_COMPLETE,
    SCHEMA_VERSION as M6_INGEST_SCHEMA_VERSION,
)
from src.experiments.canonical_optimization_experiment_evidence_v1 import (
    SCHEMA_VERSION as M5_EVIDENCE_SCHEMA_VERSION,
)
from src.experiments.canonical_optimization_universe_experiment_plane_v1 import (
    PLANE_STATUS_COMPLETE,
    OptimizationUniverseExperimentPlaneRequestV1,
    SCHEMA_VERSION as M4_SCHEMA_VERSION,
)
from src.experiments.canonical_self_learning_optimization_return_input_v1 import (
    SCHEMA_VERSION as M5_RETURN_SCHEMA_VERSION,
    STATUS_ACCEPTED_OFFLINE_EVIDENCE_INPUT,
)
from src.learning.deterministic_decision_outcome_v0.meta_learning_evidence_v1 import (
    META_EVIDENCE_AUTHORITY,
    SCHEMA_VERSION as M6_EVIDENCE_SCHEMA_VERSION,
)
from src.meta.learning_loop.contract_safety_v1 import compute_content_sha256, is_valid_sha256_hex

SCHEMA_VERSION: Final[str] = "canonical_m4_m8_evidence_return_loop_v1"
LOOP_DOMAIN: Final[str] = "peak_trade.canonical_m4_m8_evidence_return_loop.v1"

LOOP_STATUS_COMPLETE: Final[str] = "M4_M8_EVIDENCE_RETURN_LOOP_COMPLETE"
LOOP_STATUS_REJECTED_PLANE: Final[str] = "M4_M8_EVIDENCE_RETURN_LOOP_REJECTED_PLANE"
LOOP_STATUS_REJECTED_RETURN: Final[str] = "M4_M8_EVIDENCE_RETURN_LOOP_REJECTED_RETURN"
LOOP_STATUS_REJECTED_INGEST: Final[str] = "M4_M8_EVIDENCE_RETURN_LOOP_REJECTED_INGEST"

OPTIMIZATION_PRODUCTIVE_AUTHORITY: Final[str] = "NONE"
META_EVIDENCE_AUTHORITY_BOUND: Final[str] = META_EVIDENCE_AUTHORITY
EXTERNAL_EFFECT_AUTHORIZED: Final[bool] = False
LEARNING_STATE_MUTATION_PERFORMED: Final[bool] = False
SEARCH_EXECUTED: Final[bool] = False
P5_PRODUCER_BRIDGE_PERFORMED: Final[bool] = False

MECHANICAL_FIELD_BINDINGS: Final[tuple[Mapping[str, str], ...]] = (
    MappingProxyType(
        {
            "target": "meta_learning_evidence_v1.source_experiment_ids",
            "binding": "EXACT_SOURCE",
            "source": "canonical_optimization_experiment_evidence_v1.evidence_slices.SEARCH_EVIDENCE.experiment_id",
        }
    ),
    MappingProxyType(
        {
            "target": "meta_learning_evidence_v1.source_optimization_experiment_evidence_digest",
            "binding": "EXACT_SOURCE",
            "source": "canonical_optimization_experiment_evidence_v1.content_hash",
        }
    ),
    MappingProxyType(
        {
            "target": "meta_learning_evidence_v1.oos_robustness_pattern",
            "binding": "MECHANICAL_TRANSFORM",
            "source": "M5 evidence_slices OOS_EVIDENCE + ROBUSTNESS_EVIDENCE integrity projection",
        }
    ),
    MappingProxyType(
        {
            "target": "meta_learning_evidence_v1.observed_regime_or_context_ref",
            "binding": "MECHANICAL_TRANSFORM",
            "source": "OFFLINE_CONTEXT_KIND + SYNTHETIC_OFFLINE_SURFACE_ID (no instrument/epoch fabrication)",
        }
    ),
    MappingProxyType(
        {
            "target": "meta_learning_evidence_v1.optimization_family",
            "binding": "EXACT_SOURCE",
            "source": "UNKNOWN_UNAVAILABLE when not mechanically present on M5 artifact",
        }
    ),
    MappingProxyType(
        {
            "target": "meta_learning_evidence_v1.search_method.method_token",
            "binding": "EXACT_SOURCE",
            "source": "UNKNOWN_UNAVAILABLE when advanced search method token absent on plane chain",
        }
    ),
)

_LOGGER = logging.getLogger(__name__)


class M4M8EvidenceReturnLoopError(ValueError):
    """Fail-closed M4–M8 evidence return loop error."""


@dataclass(frozen=True)
class M4M8EvidenceReturnLoopRequestV1:
    learning_evidence: Mapping[str, Any]
    plane_request: OptimizationUniverseExperimentPlaneRequestV1
    replay_seed: int = 0
    cycle_index: int = 0
    requested_search_execution: bool = False
    requested_trading_instrument_selection: bool = False
    requested_promotion: bool = False
    requested_p5_producer_bridge: bool = False


def run_m4_m8_evidence_return_loop_v1(
    request: M4M8EvidenceReturnLoopRequestV1,
) -> MappingProxyType[str, Any]:
    if request.requested_search_execution:
        raise M4M8EvidenceReturnLoopError("SEARCH_EXECUTION_FORBIDDEN")
    if request.requested_trading_instrument_selection:
        raise M4M8EvidenceReturnLoopError("TRADING_INSTRUMENT_SELECTION_FORBIDDEN")
    if request.requested_promotion:
        raise M4M8EvidenceReturnLoopError("PROMOTION_FORBIDDEN")
    if request.requested_p5_producer_bridge:
        raise M4M8EvidenceReturnLoopError("P5_PRODUCER_BRIDGE_FORBIDDEN_IN_M4_M8_WP")

    cycle = run_offline_evidence_cycle_v1(
        OfflineReplayCycleInputV1(
            cycle_index=request.cycle_index,
            learning_evidence=request.learning_evidence,
            plane_request=request.plane_request,
            replay_seed=request.replay_seed,
            prior_feedback_decision=None,
        )
    )
    plane = cycle.get("experiment_plane_result") or {}
    if plane.get("status") != PLANE_STATUS_COMPLETE:
        return _loop_result(
            status=LOOP_STATUS_REJECTED_PLANE,
            reason="M4_PLANE_NOT_COMPLETE",
            cycle=cycle,
            loop_identity=None,
        )
    return_ack = cycle.get("return_input_ack") or {}
    if return_ack.get("status") != STATUS_ACCEPTED_OFFLINE_EVIDENCE_INPUT:
        return _loop_result(
            status=LOOP_STATUS_REJECTED_RETURN,
            reason="M5_RETURN_NOT_ACCEPTED",
            cycle=cycle,
            loop_identity=None,
        )
    ingest = cycle.get("meta_learning_ingest") or {}
    if ingest.get("status") != INGEST_STATUS_COMPLETE:
        return _loop_result(
            status=LOOP_STATUS_REJECTED_INGEST,
            reason="M6_INGEST_NOT_COMPLETE",
            cycle=cycle,
            loop_identity=None,
        )

    loop_identity = derive_m4_m8_loop_identity_v1(cycle=cycle)
    return _loop_result(
        status=LOOP_STATUS_COMPLETE,
        reason="CANONICAL_M4_M8_FORWARD_RETURN_LOOP",
        cycle=cycle,
        loop_identity=loop_identity,
    )


def derive_m4_m8_loop_identity_v1(*, cycle: Mapping[str, Any]) -> str:
    body = {
        "schema_version": SCHEMA_VERSION,
        "domain": LOOP_DOMAIN,
        "contract_versions": dict(BOUND_CONTRACT_VERSIONS),
        "cycle_digest": cycle.get("cycle_digest"),
        "plane_identity": (cycle.get("experiment_plane_result") or {}).get("plane_identity"),
        "optimization_experiment_evidence_digest": (
            (cycle.get("optimization_experiment_evidence") or {}).get("content_hash")
        ),
        "meta_evidence_id": (cycle.get("meta_learning_evidence") or {}).get("meta_evidence_id"),
        "feedback_decision_identity": (cycle.get("bounded_research_feedback_decision") or {}).get(
            "feedback_decision_identity"
        ),
    }
    digest = compute_content_sha256(body)
    if not is_valid_sha256_hex(digest):
        raise M4M8EvidenceReturnLoopError("LOOP_IDENTITY_DIGEST_INVALID")
    return digest


def _json_safe(value: Any) -> Any:
    if isinstance(value, MappingProxyType):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    return value


def _loop_result(
    *,
    status: str,
    reason: str,
    cycle: Mapping[str, Any],
    loop_identity: str | None,
) -> MappingProxyType[str, Any]:
    feedback = cycle.get("bounded_research_feedback_decision") or {}
    payload: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "domain": LOOP_DOMAIN,
        "status": status,
        "reason": reason,
        "loop_identity": loop_identity,
        "contract_versions": dict(BOUND_CONTRACT_VERSIONS),
        "bound_module_versions": {
            "m4_experiment_plane": M4_SCHEMA_VERSION,
            "m5_optimization_experiment_evidence": M5_EVIDENCE_SCHEMA_VERSION,
            "m5_return_input": M5_RETURN_SCHEMA_VERSION,
            "m6_meta_learning_ingest": M6_INGEST_SCHEMA_VERSION,
            "m6_meta_learning_evidence": M6_EVIDENCE_SCHEMA_VERSION,
            "m7_meta_to_optimization_feedback": M7_SCHEMA_VERSION,
        },
        "mechanical_field_bindings": [dict(binding) for binding in MECHANICAL_FIELD_BINDINGS],
        "cycle": dict(cycle),
        "optimization_productive_authority": OPTIMIZATION_PRODUCTIVE_AUTHORITY,
        "meta_evidence_authority": META_EVIDENCE_AUTHORITY_BOUND,
        "trading_selection_effect": TRADING_SELECTION_EFFECT,
        "external_effect_authorized": EXTERNAL_EFFECT_AUTHORIZED,
        "learning_state_mutation_performed": LEARNING_STATE_MUTATION_PERFORMED,
        "search_executed": SEARCH_EXECUTED,
        "p5_producer_bridge_performed": P5_PRODUCER_BRIDGE_PERFORMED,
        "forward_return_loop_closed": status == LOOP_STATUS_COMPLETE,
    }
    payload["result_digest"] = compute_content_sha256(
        _json_safe({k: v for k, v in payload.items() if k != "result_digest"})
    )
    _LOGGER.debug(
        "m4_m8 loop status=%s feedback=%s",
        status,
        feedback.get("feedback_decision_identity"),
    )
    return MappingProxyType(payload)


__all__ = [
    "EXTERNAL_EFFECT_AUTHORIZED",
    "LEARNING_STATE_MUTATION_PERFORMED",
    "LOOP_DOMAIN",
    "LOOP_STATUS_COMPLETE",
    "M4M8EvidenceReturnLoopError",
    "M4M8EvidenceReturnLoopRequestV1",
    "MECHANICAL_FIELD_BINDINGS",
    "OPTIMIZATION_PRODUCTIVE_AUTHORITY",
    "P5_PRODUCER_BRIDGE_PERFORMED",
    "SCHEMA_VERSION",
    "SEARCH_EXECUTED",
    "derive_m4_m8_loop_identity_v1",
    "run_m4_m8_evidence_return_loop_v1",
]
