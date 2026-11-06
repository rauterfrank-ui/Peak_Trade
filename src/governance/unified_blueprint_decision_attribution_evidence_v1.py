"""Unified Blueprint Phase 14 — decision attribution evidence (COMPOSE_REFERENCES_DONT_DUPLICATE_OWNERSHIP).

Conditions realized N_BARS outcomes on existing MV2/Double-Play decision references as evidence
only. Does not create trading, selection, promotion, or runtime-apply authority.
"""

from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from types import MappingProxyType
from typing import Any, Final, Mapping

from src.governance.optimization_proposal_governance_ingress_v1 import (
    PROMOTION_AUTHORITY as OPTIMIZATION_PROMOTION_AUTHORITY,
    direct_productive_write_possible_v1,
)
from src.learning.deterministic_decision_outcome_v0.decision_event_v0 import (
    validate_decision_event_v0,
)
from src.learning.deterministic_decision_outcome_v0.current_decision_consumer_v1 import (
    is_double_play_decision_event_v0,
    require_current_double_play_bundle_v1,
)
from src.learning.deterministic_decision_outcome_v0.enums_v0 import UNKNOWN
from src.learning.deterministic_decision_outcome_v0.errors_v0 import DdoValidationError
from src.learning.deterministic_decision_outcome_v0.evaluation_engine_v0 import (
    evaluate_offline_bundle_v0,
)
from src.learning.deterministic_decision_outcome_v0.evaluation_observation_v0 import (
    validate_evaluation_observation_v0,
)
from src.learning.deterministic_decision_outcome_v0.learning_outcome_evidence_ingest_v1 import (
    EXTERNAL_EFFECT_AUTHORIZED as LEARNING_INGEST_EXTERNAL_EFFECT,
    derive_learning_state_scope_id_v1,
    ingest_evaluation_bundle_into_learning_state_v1,
)
from src.learning.deterministic_decision_outcome_v0.real_outcome_horizon_contracts_v1 import (
    REAL_OUTCOME_HORIZON_V1_REAL_CAPABLE_TOKEN,
    validate_n_bars_observation_for_decision_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.decision_attribution_query_v1 import (
    query_market_intelligence_decision_attribution_v1,
)
from src.ops.peak_trade_ranking_feature_production_v1.constants_v1 import (
    PRODUCTIVE_SELECTION_OWNER,
)
from trading.master_v2.naked_mv2_double_play_core_authority_hardening_v1 import (
    LEARNING_CORE_MUTATION_AUTHORITY,
    OPTIMIZATION_CORE_MUTATION_AUTHORITY,
    TRADING_DECISION_AUTHORITY_OWNER,
)

SCHEMA_VERSION: Final[str] = "unified_blueprint_decision_attribution_evidence_v1"
NORMATIVE_SPEC: Final[str] = (
    "docs/ops/specs/UNIFIED_BLUEPRINT_PHASE_14_DECISION_ATTRIBUTION_NORMATIVE_V1.md"
)
DECISION_CONFIG: Final[str] = (
    "config/governance/unified_blueprint_decision_attribution_evidence_v1_decision_v1.json"
)
TOPOLOGY_CONFIG: Final[str] = (
    "config/governance/unified_blueprint_decision_attribution_topology_v1.json"
)

COMPOSE_REFERENCES_DONT_DUPLICATE_OWNERSHIP: Final[bool] = True
ATTRIBUTION_AUTHORITY: Final[str] = "NONE"
DECISION_AUTHORITY_DUPLICATED: Final[bool] = False
NO_SELF_DEPLOY: Final[bool] = True
OPTIMIZATION_DIRECT_PRODUCTIVE_WRITE: Final[bool] = direct_productive_write_possible_v1()
AUTHORIZED_PROMOTION_IMPLIES_RUNTIME_APPLY: Final[bool] = False
CAP23_SELECTION_OWNER_REF: Final[str] = PRODUCTIVE_SELECTION_OWNER
TRADING_DECISION_AUTHORITY_OWNER_REF: Final[str] = TRADING_DECISION_AUTHORITY_OWNER

DISPOSITION_EVIDENCE_ONLY: Final[str] = "EVIDENCE_ONLY"

_REPO_ROOT = Path(__file__).resolve().parents[2]

_EVIDENCE_BODY_KEYS: Final[tuple[str, ...]] = (
    "schema_version",
    "decision_attribution_evidence_id",
    "disposition",
    "compose_references_dont_duplicate_ownership",
    "attribution_authority",
    "trading_decision_authority_owner_ref",
    "cap23_selection_owner_ref",
    "decision_event_ref",
    "decision_event_content_hash",
    "outcome_record_ref",
    "attribution_record_ref",
    "counterfactual_record_ref",
    "evaluation_horizon",
    "n_bars_horizon_identity",
    "realized_outcome_ref",
    "selected_instrument_ref",
    "double_play_input_evidence_ref",
    "side_state_ref",
    "bull_bear_state_ref",
    "config_hash_ref",
    "forecast_evidence_id",
    "evaluation_bundle_fingerprint",
    "mi_attribution_query_schema_version",
    "learning_ingest_id",
    "learning_state_record_ref",
)


class DecisionAttributionDisposition(str, Enum):
    ATTRIBUTED = "ATTRIBUTED"
    INSUFFICIENT = "INSUFFICIENT"
    REJECTED = "REJECTED"


class UnifiedBlueprintDecisionAttributionError(ValueError):
    """Fail-closed Phase-14 decision attribution error."""


@dataclass(frozen=True)
class DecisionAttributionEvidenceRequestV1:
    decision_event: Mapping[str, Any]
    evaluation_observation: Mapping[str, Any]
    evaluation_identity: Mapping[str, Any]
    records_by_id: Mapping[str, Mapping[str, Any]] | None = None
    incident_record: Mapping[str, Any] | None = None
    side_state_ref: str | None = None
    bull_bear_state_ref: str | None = None
    forecast_evidence: Mapping[str, Any] | None = None
    calibration_evidence: Mapping[str, Any] | None = None


@dataclass(frozen=True)
class DecisionAttributionEvidenceResultV1:
    disposition: DecisionAttributionDisposition
    reason_codes: tuple[str, ...]
    decision_attribution_evidence: MappingProxyType[str, Any] | None
    evidence_digest: str | None
    offline_evaluation_bundle: MappingProxyType[str, Any] | None
    mi_attribution_query: MappingProxyType[str, Any] | None
    learning_ingest_result: Mapping[str, Any] | None


def compute_decision_attribution_evidence_digest_v1(body: Mapping[str, Any]) -> str:
    payload = {
        key: body[key] for key in _EVIDENCE_BODY_KEYS if key in body and key != "evidence_digest"
    }
    canonical = repr(sorted(payload.items())).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def _n_bars_horizon_identity_v1(observation: Mapping[str, Any]) -> Mapping[str, Any] | None:
    if str(observation.get("evaluation_horizon")) != REAL_OUTCOME_HORIZON_V1_REAL_CAPABLE_TOKEN:
        return None
    return {
        "n_bars": observation.get("n_bars"),
        "bar_spec_ref": observation.get("bar_spec_ref"),
        "instrument_ref": observation.get("instrument_ref"),
        "horizon_start_time_utc": observation.get("horizon_start_time_utc"),
        "horizon_observation_status": observation.get("horizon_observation_status"),
    }


def _evaluation_bundle_fingerprint_v1(bundle: Mapping[str, Any]) -> str:
    parts = []
    for key in ("outcome_record", "attribution_record", "counterfactual_record"):
        rec = bundle.get(key)
        if isinstance(rec, Mapping):
            parts.append(str(rec.get("content_hash") or rec.get("record_id")))
    digest = hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()
    return digest


def build_decision_attribution_evidence_v1(
    request: DecisionAttributionEvidenceRequestV1,
) -> DecisionAttributionEvidenceResultV1:
    """Compose typed attribution evidence from existing decision references + realized outcome."""
    reason_codes: list[str] = []
    try:
        decision = validate_decision_event_v0(request.decision_event)
        obs = validate_evaluation_observation_v0(request.evaluation_observation)
    except DdoValidationError as exc:
        return DecisionAttributionEvidenceResultV1(
            disposition=DecisionAttributionDisposition.REJECTED,
            reason_codes=(str(exc),),
            decision_attribution_evidence=None,
            evidence_digest=None,
            offline_evaluation_bundle=None,
            mi_attribution_query=None,
            learning_ingest_result=None,
        )

    if obs["decision_event_ref"] != decision["record_id"]:
        return DecisionAttributionEvidenceResultV1(
            disposition=DecisionAttributionDisposition.REJECTED,
            reason_codes=("DECISION_EVENT_REF_MISMATCH",),
            decision_attribution_evidence=None,
            evidence_digest=None,
            offline_evaluation_bundle=None,
            mi_attribution_query=None,
            learning_ingest_result=None,
        )

    horizon = str(obs.get("evaluation_horizon") or "")
    if horizon == REAL_OUTCOME_HORIZON_V1_REAL_CAPABLE_TOKEN:
        try:
            validate_n_bars_observation_for_decision_v1(decision, obs)
        except DdoValidationError as exc:
            return DecisionAttributionEvidenceResultV1(
                disposition=DecisionAttributionDisposition.REJECTED,
                reason_codes=(str(exc),),
                decision_attribution_evidence=None,
                evidence_digest=None,
                offline_evaluation_bundle=None,
                mi_attribution_query=None,
                learning_ingest_result=None,
            )

    dp_ref: str | None = None
    if is_double_play_decision_event_v0(decision):
        if request.records_by_id is None:
            reason_codes.append("DOUBLE_PLAY_RECORDS_INDEX_REQUIRED")
        else:
            try:
                bundle_dp = require_current_double_play_bundle_v1(
                    records_by_id=request.records_by_id,
                    decision_event_ref=str(decision["record_id"]),
                )
                dp_ref = str(bundle_dp.get("record_id") or bundle_dp.get("bundle_id") or "")
            except DdoValidationError as exc:
                reason_codes.append(str(exc))
    if reason_codes:
        return DecisionAttributionEvidenceResultV1(
            disposition=DecisionAttributionDisposition.INSUFFICIENT,
            reason_codes=tuple(reason_codes),
            decision_attribution_evidence=None,
            evidence_digest=None,
            offline_evaluation_bundle=None,
            mi_attribution_query=None,
            learning_ingest_result=None,
        )

    try:
        bundle = evaluate_offline_bundle_v0(
            decision,
            obs,
            incident_record=request.incident_record,
            identity=request.evaluation_identity,
            records_by_id=request.records_by_id,
        )
    except DdoValidationError as exc:
        return DecisionAttributionEvidenceResultV1(
            disposition=DecisionAttributionDisposition.REJECTED,
            reason_codes=(str(exc),),
            decision_attribution_evidence=None,
            evidence_digest=None,
            offline_evaluation_bundle=None,
            mi_attribution_query=None,
            learning_ingest_result=None,
        )

    if bundle.get("hindsight_leakage") is not False:
        return DecisionAttributionEvidenceResultV1(
            disposition=DecisionAttributionDisposition.REJECTED,
            reason_codes=("HINDSIGHT_LEAKAGE_NOT_ALLOWED",),
            decision_attribution_evidence=None,
            evidence_digest=None,
            offline_evaluation_bundle=MappingProxyType(dict(bundle)),
            mi_attribution_query=None,
            learning_ingest_result=None,
        )

    outcome = dict(bundle["outcome_record"])
    attribution = dict(bundle["attribution_record"])
    counterfactual = dict(bundle["counterfactual_record"])
    fingerprint = _evaluation_bundle_fingerprint_v1(bundle)
    decision_ref = str(decision["record_id"])
    evidence_id = str(
        uuid.uuid5(
            uuid.NAMESPACE_URL,
            f"phase14-decision-attribution:{decision_ref}:{fingerprint}",
        )
    )

    mi_query = query_market_intelligence_decision_attribution_v1(
        attribution_record=attribution,
        forecast_evidence=request.forecast_evidence,
        calibration_evidence=request.calibration_evidence,
        selected_instrument_ref=decision.get("selected_instrument_ref"),
        side_state_ref=request.side_state_ref,
        regime_ref=request.bull_bear_state_ref,
    )

    body: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "decision_attribution_evidence_id": evidence_id,
        "disposition": DISPOSITION_EVIDENCE_ONLY,
        "compose_references_dont_duplicate_ownership": COMPOSE_REFERENCES_DONT_DUPLICATE_OWNERSHIP,
        "attribution_authority": ATTRIBUTION_AUTHORITY,
        "trading_decision_authority_owner_ref": TRADING_DECISION_AUTHORITY_OWNER_REF,
        "cap23_selection_owner_ref": CAP23_SELECTION_OWNER_REF,
        "decision_event_ref": decision_ref,
        "decision_event_content_hash": str(decision.get("content_hash") or UNKNOWN),
        "outcome_record_ref": str(outcome["record_id"]),
        "attribution_record_ref": str(attribution["record_id"]),
        "counterfactual_record_ref": str(counterfactual["record_id"]),
        "evaluation_horizon": horizon,
        "n_bars_horizon_identity": _n_bars_horizon_identity_v1(obs),
        "realized_outcome_ref": str(outcome.get("actual_outcome_ref") or UNKNOWN),
        "selected_instrument_ref": decision.get("selected_instrument_ref"),
        "double_play_input_evidence_ref": dp_ref,
        "side_state_ref": request.side_state_ref,
        "bull_bear_state_ref": request.bull_bear_state_ref or decision.get("core_state_before_ref"),
        "config_hash_ref": str(decision.get("config_hash") or UNKNOWN),
        "forecast_evidence_id": mi_query.get("forecast_evidence_id"),
        "evaluation_bundle_fingerprint": fingerprint,
        "mi_attribution_query_schema_version": mi_query.get("schema_version"),
        "learning_ingest_id": None,
        "learning_state_record_ref": None,
    }
    body["evidence_digest"] = compute_decision_attribution_evidence_digest_v1(body)

    return DecisionAttributionEvidenceResultV1(
        disposition=DecisionAttributionDisposition.ATTRIBUTED,
        reason_codes=("DECISION_ATTRIBUTION_EVIDENCE_COMPOSED",),
        decision_attribution_evidence=MappingProxyType(body),
        evidence_digest=str(body["evidence_digest"]),
        offline_evaluation_bundle=MappingProxyType(dict(bundle)),
        mi_attribution_query=mi_query,
        learning_ingest_result=None,
    )


def ingest_decision_attribution_to_learning_state_v1(
    *,
    ledger: Any,
    attribution_result: DecisionAttributionEvidenceResultV1,
    session_id: str,
    event_time_utc: str,
    correlation_id: str,
) -> Mapping[str, Any]:
    """Wire through proven LEARNING_OUTCOME_EVIDENCE_INGEST_V1 (evidence-only)."""
    if attribution_result.disposition != DecisionAttributionDisposition.ATTRIBUTED:
        raise UnifiedBlueprintDecisionAttributionError("ATTRIBUTION_NOT_ATTRIBUTED")
    if attribution_result.offline_evaluation_bundle is None:
        raise UnifiedBlueprintDecisionAttributionError("OFFLINE_BUNDLE_MISSING")
    bundle = attribution_result.offline_evaluation_bundle
    scope = derive_learning_state_scope_id_v1(session_id=session_id)
    ingest = ingest_evaluation_bundle_into_learning_state_v1(
        ledger,
        state_scope_id=scope,
        outcome=bundle["outcome_record"],
        attribution=bundle["attribution_record"],
        counterfactual=bundle["counterfactual_record"],
        event_time_utc=event_time_utc,
        correlation_id=correlation_id,
    )
    if LEARNING_INGEST_EXTERNAL_EFFECT is not False:
        raise UnifiedBlueprintDecisionAttributionError("LEARNING_INGEST_EXTERNAL_EFFECT_FORBIDDEN")
    return ingest


def replay_decision_attribution_evidence_v1(
    request: DecisionAttributionEvidenceRequestV1,
    prior: DecisionAttributionEvidenceResultV1,
) -> bool:
    replay = build_decision_attribution_evidence_v1(request)
    if replay.disposition != prior.disposition:
        return False
    if prior.decision_attribution_evidence is None or replay.decision_attribution_evidence is None:
        return prior.decision_attribution_evidence is replay.decision_attribution_evidence
    return (
        prior.decision_attribution_evidence.get("decision_attribution_evidence_id")
        == replay.decision_attribution_evidence.get("decision_attribution_evidence_id")
        and prior.evidence_digest == replay.evidence_digest
    )


def build_decision_attribution_topology_census_v1() -> MappingProxyType[str, Any]:
    entries: tuple[dict[str, Any], ...] = (
        {
            "path_id": "evaluation_engine_v0",
            "module": "src/learning/deterministic_decision_outcome_v0/evaluation_engine_v0.py",
            "classification": "CURRENT",
            "role": "OFFLINE_OUTCOME_ATTRIBUTION_PRODUCER",
            "authority": "NONE",
            "duplicates_decision_authority": False,
        },
        {
            "path_id": "attribution_record_v0",
            "module": "src/learning/deterministic_decision_outcome_v0/evaluation_records_v0.py",
            "classification": "CURRENT",
            "role": "TYPED_ATTRIBUTION_RECORD_SCHEMA",
            "authority": "NONE",
            "duplicates_decision_authority": False,
        },
        {
            "path_id": "real_outcome_horizon_contracts_v1",
            "module": "src/learning/deterministic_decision_outcome_v0/real_outcome_horizon_contracts_v1.py",
            "classification": "CURRENT",
            "role": "N_BARS_LOOKAHEAD_GUARD",
            "authority": "NONE",
            "duplicates_decision_authority": False,
        },
        {
            "path_id": "learning_outcome_evidence_ingest_v1",
            "module": "src/learning/deterministic_decision_outcome_v0/learning_outcome_evidence_ingest_v1.py",
            "classification": "CURRENT",
            "role": "PROVEN_LEARNING_STATE_CONSUMER",
            "authority": "NONE",
            "duplicates_decision_authority": False,
        },
        {
            "path_id": "mi_decision_attribution_query_v1",
            "module": "src/learning/market_intelligence_forecast_calibration_offline_stack_v1/decision_attribution_query_v1.py",
            "classification": "CURRENT",
            "role": "MI_EVIDENCE_REFERENCE_QUERY",
            "authority": "NONE",
            "duplicates_decision_authority": False,
        },
        {
            "path_id": "unified_blueprint_decision_attribution_evidence_v1",
            "module": "src/governance/unified_blueprint_decision_attribution_evidence_v1.py",
            "classification": "CURRENT",
            "role": "PHASE_14_CANONICAL_COMPOSE_BOUNDARY",
            "authority": "NONE",
            "duplicates_decision_authority": False,
        },
        {
            "path_id": "learning_promotion_controller_v0",
            "module": "src/learning/deterministic_decision_outcome_v0/promotion_controller_v0.py",
            "classification": "HISTORICAL_DOMAIN_SCOPED",
            "role": "NOT_PHASE_14_ATTRIBUTION_AUTHORITY",
            "authority": "NONE",
            "duplicates_decision_authority": False,
        },
    )
    body = {
        "schema_version": "unified_blueprint_decision_attribution_topology_v1",
        "canonical_boundary_module": "src/governance/unified_blueprint_decision_attribution_evidence_v1.py",
        "compose_references_dont_duplicate_ownership": COMPOSE_REFERENCES_DONT_DUPLICATE_OWNERSHIP,
        "entries": list(entries),
    }
    body["census_digest"] = hashlib.sha256(repr(sorted(body.items())).encode("utf-8")).hexdigest()
    return MappingProxyType(body)


def prove_unified_blueprint_decision_attribution_evidence_v1(
    *, repo_root: Path | None = None
) -> bool:
    root = repo_root or _REPO_ROOT
    if not (root / NORMATIVE_SPEC).is_file():
        return False
    if not (root / DECISION_CONFIG).is_file():
        return False
    if ATTRIBUTION_AUTHORITY != "NONE":
        return False
    if DECISION_AUTHORITY_DUPLICATED is not False:
        return False
    if COMPOSE_REFERENCES_DONT_DUPLICATE_OWNERSHIP is not True:
        return False
    if OPTIMIZATION_PROMOTION_AUTHORITY != "NONE":
        return False
    if direct_productive_write_possible_v1() is not False:
        return False
    if OPTIMIZATION_CORE_MUTATION_AUTHORITY != "NONE":
        return False
    if LEARNING_CORE_MUTATION_AUTHORITY != "NONE":
        return False
    decision = _load_json_decision(root)
    return decision.get("phase_14_decision_attribution_status") == "PROVEN_COMPLETE"


def _load_json_decision(root: Path) -> dict[str, Any]:
    import json

    return json.loads((root / DECISION_CONFIG).read_text(encoding="utf-8"))


def authority_invariants_v1() -> MappingProxyType[str, Any]:
    return MappingProxyType(
        {
            "optimization_promotion_authority": OPTIMIZATION_PROMOTION_AUTHORITY,
            "optimization_direct_productive_write": OPTIMIZATION_DIRECT_PRODUCTIVE_WRITE,
            "no_self_deploy": NO_SELF_DEPLOY,
            "attribution_authority": ATTRIBUTION_AUTHORITY,
            "decision_authority_duplicated": DECISION_AUTHORITY_DUPLICATED,
            "cap23_selection_owner_ref": CAP23_SELECTION_OWNER_REF,
            "trading_decision_authority_owner_ref": TRADING_DECISION_AUTHORITY_OWNER_REF,
        }
    )
