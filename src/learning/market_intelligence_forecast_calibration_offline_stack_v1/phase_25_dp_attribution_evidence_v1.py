"""Phase 25 — DP Attribution evidence (MARKET_CONTEXT + MV2/DP decision + REALIZED_BEHAVIOR).

Composes proven Phase-14 decision attribution with Phase-17/20 context/behavior references.
AUTHORITY=NONE; does not mutate MV2/Double-Play, selection, risk, or execution.
"""

from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from types import MappingProxyType
from typing import Any, Final, Mapping

from src.governance.unified_blueprint_decision_attribution_evidence_v1 import (
    ATTRIBUTION_AUTHORITY,
    COMPOSE_REFERENCES_DONT_DUPLICATE_OWNERSHIP,
    DecisionAttributionDisposition,
    DecisionAttributionEvidenceRequestV1,
    build_decision_attribution_evidence_v1,
    compute_decision_attribution_evidence_digest_v1,
)
from src.learning.deterministic_decision_outcome_v0.common_v0 import require_event_time_utc
from src.learning.deterministic_decision_outcome_v0.decision_event_v0 import (
    validate_decision_event_v0,
)
from src.learning.deterministic_decision_outcome_v0.enums_v0 import UNKNOWN
from src.learning.deterministic_decision_outcome_v0.errors_v0 import DdoValidationError
from src.learning.deterministic_decision_outcome_v0.evaluation_observation_v0 import (
    validate_evaluation_observation_v0,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.constants_v1 import (
    STACK_DOMAIN,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.market_context_v1 import (
    MARKET_CONTEXT_AUTHORITY,
    validate_market_context_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.realized_behavior_v1 import (
    REALIZED_BEHAVIOR_AUTHORITY,
    validate_realized_behavior_v1,
)
from src.meta.learning_loop.contract_safety_v1 import compute_content_sha256

PHASE_25_SCHEMA: Final[str] = "attribution_evidence_v1"
PHASE_25_OWNER: Final[str] = (
    "learning.market_intelligence_forecast_calibration_offline_stack_v1."
    "phase_25_dp_attribution_evidence_v1"
)
WRITER_ID: Final[str] = "peak_trade.learning.phase_25_dp_attribution_evidence_writer_v1"
READER_ID: Final[str] = "peak_trade.learning.phase_25_dp_attribution_evidence_inspector_v1"
DISPOSITION_EVIDENCE_ONLY: Final[str] = "EVIDENCE_ONLY"

_ATTRIBUTION_BODY_KEYS: Final[tuple[str, ...]] = (
    "schema_version",
    "attribution_evidence_id",
    "disposition",
    "compose_references_dont_duplicate_ownership",
    "attribution_authority",
    "decision_time_utc",
    "market_context_ref",
    "market_context_content_digest",
    "selected_future_ref",
    "mv2_dp_decision_ref",
    "side_state_ref",
    "configuration_ref",
    "realized_behavior_ref",
    "realized_behavior_content_digest",
    "horizon_identity",
    "quality_refs",
    "phase_14_decision_attribution_evidence_id",
    "phase_14_evidence_digest",
    "provenance",
    "pit_join_proven",
    "no_trading_gate_from_attribution",
)


class Phase25DpAttributionError(ValueError):
    """Fail-closed Phase 25 DP attribution compose."""


class DpAttributionDisposition(str, Enum):
    ATTRIBUTED = "ATTRIBUTED"
    INSUFFICIENT = "INSUFFICIENT"
    REJECTED = "REJECTED"


@dataclass(frozen=True)
class DpAttributionEvidenceRequestV1:
    """Inputs referencing existing owners only (no duplicated decision payloads)."""

    attribution_request: DecisionAttributionEvidenceRequestV1
    market_context: Mapping[str, Any]
    realized_behavior: Mapping[str, Any] | None = None


@dataclass(frozen=True)
class DpAttributionEvidenceResultV1:
    disposition: DpAttributionDisposition
    reason_codes: tuple[str, ...]
    attribution_evidence: MappingProxyType[str, Any] | None
    evidence_digest: str | None
    phase_14_result_digest: str | None
    phase_14_disposition: DecisionAttributionDisposition | None


def _parse_utc(value: str) -> datetime:
    text = require_event_time_utc(value, "utc")
    return datetime.fromisoformat(text.replace("Z", "+00:00")).astimezone(timezone.utc)


def _assert_market_context_pit_at_decision_v1(
    *,
    decision: Mapping[str, Any],
    market_context: Mapping[str, Any],
) -> None:
    decision_t = _parse_utc(str(decision["event_time_utc"]))
    context_t = _parse_utc(str(market_context["observed_at"]))
    if context_t > decision_t:
        raise Phase25DpAttributionError("MARKET_CONTEXT_AFTER_DECISION_TIME")
    info_ref = decision.get("decision_time_information_set_ref")
    ctx_info = market_context.get("information_set_ref")
    if info_ref is not None and ctx_info is not None and str(ctx_info) != str(info_ref):
        raise Phase25DpAttributionError("DECISION_INFORMATION_SET_MISMATCH")


def _assert_realized_behavior_horizon_join_v1(
    *,
    market_context: Mapping[str, Any],
    observation: Mapping[str, Any],
    realized_behavior: Mapping[str, Any],
) -> None:
    if str(realized_behavior.get("market_context_ref")) != str(market_context["context_id"]):
        raise Phase25DpAttributionError("REALIZED_BEHAVIOR_CONTEXT_REF_MISMATCH")
    rb_horizon = realized_behavior.get("horizon_identity")
    if not isinstance(rb_horizon, Mapping):
        raise Phase25DpAttributionError("REALIZED_BEHAVIOR_HORIZON_IDENTITY_MISSING")
    for key in ("n_bars", "bar_spec_ref", "horizon_start_time_utc", "evaluation_time_utc"):
        obs_val = observation.get(key)
        rb_val = rb_horizon.get(key)
        if obs_val is not None and rb_val is not None and str(obs_val) != str(rb_val):
            raise Phase25DpAttributionError(f"HORIZON_IDENTITY_MISMATCH:{key}")
    context_t = _parse_utc(str(market_context["observed_at"]))
    horizon_start = observation.get("horizon_start_time_utc")
    if horizon_start is not None and _parse_utc(str(horizon_start)) < context_t:
        raise Phase25DpAttributionError("LOOKAHEAD_HORIZON_BEFORE_CONTEXT")


def _build_quality_refs_v1(
    *,
    decision: Mapping[str, Any],
    market_context: Mapping[str, Any],
    realized_behavior: Mapping[str, Any] | None,
) -> MappingProxyType[str, Any]:
    missing: dict[str, bool] = {}
    refs: dict[str, Any] = {}
    dq = decision.get("data_quality_ref")
    refs["decision_data_quality_ref"] = dq
    missing["decision_data_quality_ref"] = dq is None
    qctx = market_context.get("quality_state_ref")
    refs["market_context_quality_state_ref"] = qctx
    missing["market_context_quality_state_ref"] = qctx is None
    if realized_behavior is not None:
        qs = realized_behavior.get("quality_state")
        refs["realized_behavior_quality_state"] = qs
        missing["realized_behavior_quality_state"] = qs is None
    else:
        refs["realized_behavior_quality_state"] = None
        missing["realized_behavior_quality_state"] = True
    return MappingProxyType(
        {
            "quality_refs": refs,
            "missing_explicit": missing,
        }
    )


def _mv2_dp_decision_ref_v1(
    *,
    decision: Mapping[str, Any],
    phase_14_body: Mapping[str, Any],
) -> MappingProxyType[str, Any]:
    return MappingProxyType(
        {
            "decision_event_ref": str(decision["record_id"]),
            "decision_event_content_hash": str(decision.get("content_hash") or UNKNOWN),
            "double_play_input_evidence_ref": phase_14_body.get("double_play_input_evidence_ref"),
            "trading_decision_authority_owner_ref": phase_14_body.get(
                "trading_decision_authority_owner_ref"
            ),
            "references_only": True,
        }
    )


def compute_attribution_evidence_digest_v1(body: Mapping[str, Any]) -> str:
    payload = {
        key: body[key] for key in _ATTRIBUTION_BODY_KEYS if key in body and key != "evidence_digest"
    }
    return hashlib.sha256(repr(sorted(payload.items())).encode("utf-8")).hexdigest()


def compose_dp_attribution_evidence_v1(
    request: DpAttributionEvidenceRequestV1,
) -> DpAttributionEvidenceResultV1:
    """PIT-safe join: decision(t) + market_context(t) + realized_behavior(t+N)."""
    try:
        decision = validate_decision_event_v0(request.attribution_request.decision_event)
        observation = validate_evaluation_observation_v0(
            request.attribution_request.evaluation_observation
        )
        context = validate_market_context_v1(request.market_context)
    except (DdoValidationError, Exception) as exc:
        return DpAttributionEvidenceResultV1(
            disposition=DpAttributionDisposition.REJECTED,
            reason_codes=(str(exc),),
            attribution_evidence=None,
            evidence_digest=None,
            phase_14_result_digest=None,
            phase_14_disposition=None,
        )

    try:
        _assert_market_context_pit_at_decision_v1(decision=decision, market_context=context)
    except Phase25DpAttributionError as exc:
        return DpAttributionEvidenceResultV1(
            disposition=DpAttributionDisposition.REJECTED,
            reason_codes=(str(exc),),
            attribution_evidence=None,
            evidence_digest=None,
            phase_14_result_digest=None,
            phase_14_disposition=None,
        )

    realized = None
    if request.realized_behavior is not None:
        try:
            realized = validate_realized_behavior_v1(request.realized_behavior)
            _assert_realized_behavior_horizon_join_v1(
                market_context=context,
                observation=observation,
                realized_behavior=realized,
            )
        except (Phase25DpAttributionError, Exception) as exc:
            return DpAttributionEvidenceResultV1(
                disposition=DpAttributionDisposition.REJECTED,
                reason_codes=(str(exc),),
                attribution_evidence=None,
                evidence_digest=None,
                phase_14_result_digest=None,
                phase_14_disposition=None,
            )
    elif observation.get("horizon_observation_status") == "OK":
        return DpAttributionEvidenceResultV1(
            disposition=DpAttributionDisposition.INSUFFICIENT,
            reason_codes=("REALIZED_BEHAVIOR_REQUIRED_FOR_OK_HORIZON",),
            attribution_evidence=None,
            evidence_digest=None,
            phase_14_result_digest=None,
            phase_14_disposition=None,
        )

    phase_14 = build_decision_attribution_evidence_v1(request.attribution_request)
    p14_digest = phase_14.evidence_digest
    if phase_14.disposition != DecisionAttributionDisposition.ATTRIBUTED:
        mapped = (
            DpAttributionDisposition.REJECTED
            if phase_14.disposition == DecisionAttributionDisposition.REJECTED
            else DpAttributionDisposition.INSUFFICIENT
        )
        return DpAttributionEvidenceResultV1(
            disposition=mapped,
            reason_codes=phase_14.reason_codes,
            attribution_evidence=None,
            evidence_digest=None,
            phase_14_result_digest=p14_digest,
            phase_14_disposition=phase_14.disposition,
        )

    p14_body = dict(phase_14.decision_attribution_evidence or {})
    quality = _build_quality_refs_v1(
        decision=decision,
        market_context=context,
        realized_behavior=realized,
    )

    horizon_identity = p14_body.get("n_bars_horizon_identity")
    if realized is not None:
        horizon_identity = dict(realized.get("horizon_identity") or horizon_identity or {})

    rb_ref = str(realized["behavior_id"]) if realized is not None else UNKNOWN
    rb_digest = str(realized["content_digest"]) if realized is not None else UNKNOWN

    identity_seed = compute_content_sha256(
        {
            "decision_event_ref": decision["record_id"],
            "market_context_ref": context["context_id"],
            "realized_behavior_ref": rb_ref,
            "phase_14_evidence_digest": p14_digest,
            "horizon_identity": horizon_identity,
        }
    )
    evidence_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"phase25-dp-attribution:{identity_seed}"))

    provenance = {
        "writer_id": WRITER_ID,
        "phase_25_owner": PHASE_25_OWNER,
        "phase_14_schema": p14_body.get("schema_version"),
        "market_context_authority": MARKET_CONTEXT_AUTHORITY,
        "realized_behavior_authority": REALIZED_BEHAVIOR_AUTHORITY,
        "phase_14_provenance_chain": {
            "decision_event_ref": p14_body.get("decision_event_ref"),
            "outcome_record_ref": p14_body.get("outcome_record_ref"),
            "attribution_record_ref": p14_body.get("attribution_record_ref"),
            "counterfactual_record_ref": p14_body.get("counterfactual_record_ref"),
            "evaluation_bundle_fingerprint": p14_body.get("evaluation_bundle_fingerprint"),
        },
    }

    body: dict[str, Any] = {
        "schema_version": PHASE_25_SCHEMA,
        "attribution_evidence_id": evidence_id,
        "disposition": DISPOSITION_EVIDENCE_ONLY,
        "compose_references_dont_duplicate_ownership": COMPOSE_REFERENCES_DONT_DUPLICATE_OWNERSHIP,
        "attribution_authority": ATTRIBUTION_AUTHORITY,
        "decision_time_utc": str(decision["event_time_utc"]),
        "market_context_ref": str(context["context_id"]),
        "market_context_content_digest": str(context["content_digest"]),
        "selected_future_ref": decision.get("selected_instrument_ref"),
        "mv2_dp_decision_ref": dict(
            _mv2_dp_decision_ref_v1(decision=decision, phase_14_body=p14_body)
        ),
        "side_state_ref": request.attribution_request.side_state_ref,
        "configuration_ref": str(decision.get("config_hash") or UNKNOWN),
        "realized_behavior_ref": rb_ref,
        "realized_behavior_content_digest": rb_digest,
        "horizon_identity": horizon_identity,
        "quality_refs": dict(quality["quality_refs"]),
        "quality_missing_explicit": dict(quality["missing_explicit"]),
        "phase_14_decision_attribution_evidence_id": p14_body.get(
            "decision_attribution_evidence_id"
        ),
        "phase_14_evidence_digest": p14_digest,
        "provenance": provenance,
        "pit_join_proven": True,
        "no_trading_gate_from_attribution": True,
        "domain": STACK_DOMAIN,
    }
    body["evidence_digest"] = compute_attribution_evidence_digest_v1(body)

    return DpAttributionEvidenceResultV1(
        disposition=DpAttributionDisposition.ATTRIBUTED,
        reason_codes=("DP_ATTRIBUTION_EVIDENCE_COMPOSED",),
        attribution_evidence=MappingProxyType(body),
        evidence_digest=str(body["evidence_digest"]),
        phase_14_result_digest=p14_digest,
        phase_14_disposition=phase_14.disposition,
    )


def inspect_dp_attribution_evidence_v1(
    record: Mapping[str, Any],
) -> MappingProxyType[str, Any]:
    """Reader path: validate typed evidence without mutating decision owners."""
    if str(record.get("schema_version")) != PHASE_25_SCHEMA:
        raise Phase25DpAttributionError("SCHEMA_VERSION_MISMATCH")
    expected = compute_attribution_evidence_digest_v1(record)
    if str(record.get("evidence_digest")) != expected:
        raise Phase25DpAttributionError("EVIDENCE_DIGEST_MISMATCH")
    if record.get("attribution_authority") != "NONE":
        raise Phase25DpAttributionError("ATTRIBUTION_AUTHORITY_FORBIDDEN")
    if record.get("no_trading_gate_from_attribution") is not True:
        raise Phase25DpAttributionError("TRADING_GATE_INVARIANT_BROKEN")
    p14_id = record.get("phase_14_decision_attribution_evidence_id")
    p14_digest = record.get("phase_14_evidence_digest")
    if not p14_id or not p14_digest:
        raise Phase25DpAttributionError("PHASE_14_BINDING_MISSING")
    return MappingProxyType(
        {
            "reader_id": READER_ID,
            "attribution_evidence_id": record.get("attribution_evidence_id"),
            "inspect_ok": True,
            "market_context_ref": record.get("market_context_ref"),
            "realized_behavior_ref": record.get("realized_behavior_ref"),
            "mv2_dp_decision_ref": record.get("mv2_dp_decision_ref"),
            "horizon_identity": record.get("horizon_identity"),
            "provenance_preserved": record.get("provenance") is not None,
        }
    )


def replay_dp_attribution_evidence_v1(
    request: DpAttributionEvidenceRequestV1,
    prior: DpAttributionEvidenceResultV1,
) -> bool:
    replay = compose_dp_attribution_evidence_v1(request)
    if replay.disposition != prior.disposition:
        return False
    if prior.attribution_evidence is None or replay.attribution_evidence is None:
        return prior.attribution_evidence is replay.attribution_evidence
    return (
        prior.attribution_evidence.get("attribution_evidence_id")
        == replay.attribution_evidence.get("attribution_evidence_id")
        and prior.evidence_digest == replay.evidence_digest
    )


def assert_phase_25_dp_attribution_authority_invariants_v1() -> Mapping[str, Any]:
    terminal = {
        "ATTRIBUTION_EVIDENCE_ONLY": True,
        "COMPOSE_REFERENCES_DONT_DUPLICATE_OWNERSHIP": COMPOSE_REFERENCES_DONT_DUPLICATE_OWNERSHIP,
        "ATTRIBUTION_AUTHORITY": ATTRIBUTION_AUTHORITY,
        "MV2_DP_UNCHANGED": True,
        "NO_TRADING_GATE_FROM_ATTRIBUTION": True,
        "NO_AUTHORITY_EXPANSION": True,
        "MARKET_CONTEXT_AUTHORITY": MARKET_CONTEXT_AUTHORITY,
        "REALIZED_BEHAVIOR_AUTHORITY": REALIZED_BEHAVIOR_AUTHORITY,
        "PHASE_26_STARTED": False,
        "RUNTIME_APPLY_AUTHORIZED": False,
        "PRODUCTIVE_ORDER_PATH": False,
    }
    if terminal["ATTRIBUTION_AUTHORITY"] != "NONE":
        raise Phase25DpAttributionError("AUTHORITY_EXPANSION_FORBIDDEN")
    return MappingProxyType(terminal)


__all__ = [
    "PHASE_25_SCHEMA",
    "DpAttributionDisposition",
    "DpAttributionEvidenceRequestV1",
    "DpAttributionEvidenceResultV1",
    "Phase25DpAttributionError",
    "assert_phase_25_dp_attribution_authority_invariants_v1",
    "compose_dp_attribution_evidence_v1",
    "compute_attribution_evidence_digest_v1",
    "inspect_dp_attribution_evidence_v1",
    "replay_dp_attribution_evidence_v1",
]
