"""Market Dashboard ReadModel contracts v1 — deterministic serialization.

Stable field order, timezone-preserving ISO-8601 timestamps, enum values as
strings, no NaN/Infinity JSON, no hidden current-time injection.
"""

from __future__ import annotations

import json
from datetime import datetime
from enum import Enum
from typing import Any, Mapping

from src.webui.market_dashboard_readmodels_v1.aggregate import (
    MarketDashboardPageSnapshotV1,
    new_market_dashboard_page_snapshot_v1,
)
from src.webui.market_dashboard_readmodels_v1.contracts import (
    AuthorityClassificationV1,
    CanonicalDecisionStatusV1,
    CanonicalDecisionSummaryV1,
    DashboardAvailabilityStateV1,
    DashboardFreshnessSnapshotV1,
    DecisionDirectionV1,
    DiagnosticsSummarySnapshotV1,
    DoublePlayDecisionSnapshotV1,
    EconomicGateStatusV1,
    EconomicSummarySnapshotV1,
    EligibilityStatusV1,
    ExecutionStateSnapshotV1,
    MarketInstrumentSnapshotV1,
    MarketRankingItemV1,
    MarketRankingSnapshotV1,
    OhlcvBarV1,
    OperatingModeV1,
    SafetyAuthoritySnapshotV1,
    SideAssessmentV1,
    SourceFreshnessEntryV1,
    TriStateV1,
    UnavailableSnapshotV1,
    new_canonical_decision_summary_v1,
    new_dashboard_freshness_snapshot_v1,
    new_diagnostics_summary_snapshot_v1,
    new_double_play_decision_snapshot_v1,
    new_economic_summary_snapshot_v1,
    new_execution_state_snapshot_v1,
    new_market_instrument_snapshot_v1,
    new_market_ranking_snapshot_v1,
    new_safety_authority_snapshot_v1,
    new_unavailable_snapshot_v1,
)
from src.webui.market_dashboard_readmodels_v1.provenance import (
    DashboardFreshnessStateV1,
    DashboardSnapshotProvenanceV1,
    DashboardSourceKindV1,
    new_dashboard_snapshot_provenance_v1,
)
from src.webui.market_dashboard_readmodels_v1.validation import (
    MarketDashboardReadModelContractError,
    require_aware_datetime,
    require_non_empty_str,
)

ContractObject = (
    DashboardSnapshotProvenanceV1
    | UnavailableSnapshotV1
    | MarketInstrumentSnapshotV1
    | MarketRankingSnapshotV1
    | CanonicalDecisionSummaryV1
    | DoublePlayDecisionSnapshotV1
    | SafetyAuthoritySnapshotV1
    | ExecutionStateSnapshotV1
    | EconomicSummarySnapshotV1
    | DiagnosticsSummarySnapshotV1
    | DashboardFreshnessSnapshotV1
    | MarketDashboardPageSnapshotV1
)


def _dt_to_iso(value: datetime) -> str:
    require_aware_datetime(value, field="timestamp")
    return value.isoformat()


def _dt_from_iso(value: Any, *, field: str) -> datetime:
    text = require_non_empty_str(value, field=field)
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError as exc:
        raise MarketDashboardReadModelContractError(
            f"{field} must be ISO-8601 datetime, got {text!r}"
        ) from exc
    return require_aware_datetime(parsed, field=field)


def _enum_value(value: Enum) -> str:
    return str(value.value)


def provenance_to_json_dict(model: DashboardSnapshotProvenanceV1) -> dict[str, Any]:
    return {
        "schema_id": model.schema_id,
        "schema_version": model.schema_version,
        "producer_module": model.producer_module,
        "producer_version": model.producer_version,
        "producer_git_sha": model.producer_git_sha,
        "generated_at": _dt_to_iso(model.generated_at),
        "effective_at": _dt_to_iso(model.effective_at),
        "source_kind": _enum_value(model.source_kind),
        "source_reference": model.source_reference,
        "evidence_digest": model.evidence_digest,
        "freshness_state": _enum_value(model.freshness_state),
    }


def provenance_from_json_dict(payload: Mapping[str, Any]) -> DashboardSnapshotProvenanceV1:
    return new_dashboard_snapshot_provenance_v1(
        producer_module=payload["producer_module"],
        generated_at=_dt_from_iso(payload["generated_at"], field="generated_at"),
        effective_at=_dt_from_iso(payload["effective_at"], field="effective_at"),
        source_kind=DashboardSourceKindV1(payload["source_kind"]),
        freshness_state=DashboardFreshnessStateV1(payload["freshness_state"]),
        producer_version=payload.get("producer_version"),
        producer_git_sha=payload.get("producer_git_sha"),
        source_reference=payload.get("source_reference"),
        evidence_digest=payload.get("evidence_digest"),
    )


def unavailable_to_json_dict(model: UnavailableSnapshotV1) -> dict[str, Any]:
    return {
        "schema_id": model.schema_id,
        "schema_version": model.schema_version,
        "availability_state": _enum_value(model.availability_state),
        "reason_code": model.reason_code,
        "detail": model.detail,
        "expected_source": model.expected_source,
        "generated_at": _dt_to_iso(model.generated_at),
        "source_reference": model.source_reference,
        "provenance": (
            provenance_to_json_dict(model.provenance) if model.provenance is not None else None
        ),
    }


def unavailable_from_json_dict(payload: Mapping[str, Any]) -> UnavailableSnapshotV1:
    provenance_payload = payload.get("provenance")
    return new_unavailable_snapshot_v1(
        availability_state=DashboardAvailabilityStateV1(payload["availability_state"]),
        reason_code=payload["reason_code"],
        detail=payload["detail"],
        expected_source=payload["expected_source"],
        generated_at=_dt_from_iso(payload["generated_at"], field="generated_at"),
        source_reference=payload.get("source_reference"),
        provenance=(
            provenance_from_json_dict(provenance_payload)
            if isinstance(provenance_payload, Mapping)
            else None
        ),
    )


def _ohlcv_to_json(model: OhlcvBarV1 | None) -> dict[str, Any] | None:
    if model is None:
        return None
    return {
        "open": model.open,
        "high": model.high,
        "low": model.low,
        "close": model.close,
        "volume": model.volume,
    }


def _ohlcv_from_json(payload: Any) -> OhlcvBarV1 | None:
    if payload is None:
        return None
    if not isinstance(payload, Mapping):
        raise MarketDashboardReadModelContractError("ohlcv must be an object")
    return OhlcvBarV1(
        open=payload["open"],
        high=payload["high"],
        low=payload["low"],
        close=payload["close"],
        volume=payload.get("volume"),
    )


def market_instrument_to_json_dict(model: MarketInstrumentSnapshotV1) -> dict[str, Any]:
    return {
        "schema_id": model.schema_id,
        "schema_version": model.schema_version,
        "instrument_id": model.instrument_id,
        "venue": model.venue,
        "effective_at": _dt_to_iso(model.effective_at),
        "mark_price": model.mark_price,
        "last_price": model.last_price,
        "change_abs": model.change_abs,
        "change_pct": model.change_pct,
        "volume": model.volume,
        "ohlcv": _ohlcv_to_json(model.ohlcv),
        "market_series_reference": model.market_series_reference,
        "freshness_state": _enum_value(model.freshness_state),
        "provenance": provenance_to_json_dict(model.provenance),
    }


def market_instrument_from_json_dict(payload: Mapping[str, Any]) -> MarketInstrumentSnapshotV1:
    return new_market_instrument_snapshot_v1(
        instrument_id=payload["instrument_id"],
        venue=payload["venue"],
        effective_at=_dt_from_iso(payload["effective_at"], field="effective_at"),
        freshness_state=DashboardFreshnessStateV1(payload["freshness_state"]),
        provenance=provenance_from_json_dict(payload["provenance"]),
        mark_price=payload.get("mark_price"),
        last_price=payload.get("last_price"),
        change_abs=payload.get("change_abs"),
        change_pct=payload.get("change_pct"),
        volume=payload.get("volume"),
        ohlcv=_ohlcv_from_json(payload.get("ohlcv")),
        market_series_reference=payload.get("market_series_reference"),
    )


def market_ranking_to_json_dict(model: MarketRankingSnapshotV1) -> dict[str, Any]:
    return {
        "schema_id": model.schema_id,
        "schema_version": model.schema_version,
        "ranked_items": [
            {
                "instrument_id": item.instrument_id,
                "rank": item.rank,
                "score": item.score,
                "eligibility_status": _enum_value(item.eligibility_status),
                "reason_codes": list(item.reason_codes),
            }
            for item in model.ranked_items
        ],
        "selected_instrument_id": model.selected_instrument_id,
        "effective_at": _dt_to_iso(model.effective_at),
        "allow_duplicate_ranks": model.allow_duplicate_ranks,
        "provenance": provenance_to_json_dict(model.provenance),
    }


def market_ranking_from_json_dict(payload: Mapping[str, Any]) -> MarketRankingSnapshotV1:
    items_raw = payload.get("ranked_items")
    if not isinstance(items_raw, list):
        raise MarketDashboardReadModelContractError("ranked_items must be a list")
    items = tuple(
        MarketRankingItemV1(
            instrument_id=item["instrument_id"],
            rank=item["rank"],
            score=item.get("score"),
            eligibility_status=EligibilityStatusV1(item["eligibility_status"]),
            reason_codes=tuple(item.get("reason_codes") or ()),
        )
        for item in items_raw
    )
    return new_market_ranking_snapshot_v1(
        ranked_items=items,
        selected_instrument_id=payload.get("selected_instrument_id"),
        effective_at=_dt_from_iso(payload["effective_at"], field="effective_at"),
        provenance=provenance_from_json_dict(payload["provenance"]),
        allow_duplicate_ranks=bool(payload.get("allow_duplicate_ranks", False)),
    )


def canonical_decision_to_json_dict(model: CanonicalDecisionSummaryV1) -> dict[str, Any]:
    return {
        "schema_id": model.schema_id,
        "schema_version": model.schema_version,
        "decision_status": _enum_value(model.decision_status),
        "direction": _enum_value(model.direction),
        "confidence": model.confidence,
        "evidence_status": model.evidence_status,
        "reason_codes": list(model.reason_codes),
        "blockers": list(model.blockers),
        "evidence_digest": model.evidence_digest,
        "evidence_reference": model.evidence_reference,
        "effective_at": _dt_to_iso(model.effective_at),
        "provenance": provenance_to_json_dict(model.provenance),
    }


def canonical_decision_from_json_dict(payload: Mapping[str, Any]) -> CanonicalDecisionSummaryV1:
    return new_canonical_decision_summary_v1(
        decision_status=CanonicalDecisionStatusV1(payload["decision_status"]),
        direction=DecisionDirectionV1(payload["direction"]),
        confidence=payload.get("confidence"),
        evidence_status=payload["evidence_status"],
        reason_codes=tuple(payload.get("reason_codes") or ()),
        blockers=tuple(payload.get("blockers") or ()),
        evidence_digest=payload.get("evidence_digest"),
        evidence_reference=payload.get("evidence_reference"),
        effective_at=_dt_from_iso(payload["effective_at"], field="effective_at"),
        provenance=provenance_from_json_dict(payload["provenance"]),
    )


def double_play_to_json_dict(model: DoublePlayDecisionSnapshotV1) -> dict[str, Any]:
    def _side(side: SideAssessmentV1) -> dict[str, Any]:
        return {
            "status": side.status,
            "score": side.score,
            "reason_codes": list(side.reason_codes),
        }

    return {
        "schema_id": model.schema_id,
        "schema_version": model.schema_version,
        "bull_assessment": _side(model.bull_assessment),
        "bear_assessment": _side(model.bear_assessment),
        "composition_result": model.composition_result,
        "arbitration_status": model.arbitration_status,
        "blockers": list(model.blockers),
        "evidence_digest": model.evidence_digest,
        "evidence_reference": model.evidence_reference,
        "effective_at": _dt_to_iso(model.effective_at),
        "provenance": provenance_to_json_dict(model.provenance),
    }


def double_play_from_json_dict(payload: Mapping[str, Any]) -> DoublePlayDecisionSnapshotV1:
    bull = payload["bull_assessment"]
    bear = payload["bear_assessment"]
    return new_double_play_decision_snapshot_v1(
        bull_assessment=SideAssessmentV1(
            status=bull["status"],
            score=bull.get("score"),
            reason_codes=tuple(bull.get("reason_codes") or ()),
        ),
        bear_assessment=SideAssessmentV1(
            status=bear["status"],
            score=bear.get("score"),
            reason_codes=tuple(bear.get("reason_codes") or ()),
        ),
        composition_result=payload["composition_result"],
        arbitration_status=payload["arbitration_status"],
        blockers=tuple(payload.get("blockers") or ()),
        evidence_digest=payload.get("evidence_digest"),
        evidence_reference=payload.get("evidence_reference"),
        effective_at=_dt_from_iso(payload["effective_at"], field="effective_at"),
        provenance=provenance_from_json_dict(payload["provenance"]),
    )


def safety_authority_to_json_dict(model: SafetyAuthoritySnapshotV1) -> dict[str, Any]:
    return {
        "schema_id": model.schema_id,
        "schema_version": model.schema_version,
        "authority_classification": _enum_value(model.authority_classification),
        "kill_switch_state": _enum_value(model.kill_switch_state),
        "risk_gate_state": _enum_value(model.risk_gate_state),
        "execution_permission_state": _enum_value(model.execution_permission_state),
        "fail_closed_reason_codes": list(model.fail_closed_reason_codes),
        "effective_at": _dt_to_iso(model.effective_at),
        "provenance": provenance_to_json_dict(model.provenance),
    }


def safety_authority_from_json_dict(payload: Mapping[str, Any]) -> SafetyAuthoritySnapshotV1:
    return new_safety_authority_snapshot_v1(
        authority_classification=AuthorityClassificationV1(payload["authority_classification"]),
        kill_switch_state=TriStateV1(payload["kill_switch_state"]),
        risk_gate_state=TriStateV1(payload["risk_gate_state"]),
        execution_permission_state=TriStateV1(payload["execution_permission_state"]),
        fail_closed_reason_codes=tuple(payload.get("fail_closed_reason_codes") or ()),
        effective_at=_dt_from_iso(payload["effective_at"], field="effective_at"),
        provenance=provenance_from_json_dict(payload["provenance"]),
    )


def execution_state_to_json_dict(model: ExecutionStateSnapshotV1) -> dict[str, Any]:
    return {
        "schema_id": model.schema_id,
        "schema_version": model.schema_version,
        "operating_mode": _enum_value(model.operating_mode),
        "intent_state": model.intent_state,
        "fill_state": model.fill_state,
        "reconciliation_state": model.reconciliation_state,
        "unknown_outcome_state": model.unknown_outcome_state,
        "effective_at": _dt_to_iso(model.effective_at),
        "provenance": provenance_to_json_dict(model.provenance),
    }


def execution_state_from_json_dict(payload: Mapping[str, Any]) -> ExecutionStateSnapshotV1:
    return new_execution_state_snapshot_v1(
        operating_mode=OperatingModeV1(payload["operating_mode"]),
        intent_state=payload["intent_state"],
        fill_state=payload["fill_state"],
        reconciliation_state=payload["reconciliation_state"],
        unknown_outcome_state=payload["unknown_outcome_state"],
        effective_at=_dt_from_iso(payload["effective_at"], field="effective_at"),
        provenance=provenance_from_json_dict(payload["provenance"]),
    )


def economic_summary_to_json_dict(model: EconomicSummarySnapshotV1) -> dict[str, Any]:
    return {
        "schema_id": model.schema_id,
        "schema_version": model.schema_version,
        "economic_gate_status": _enum_value(model.economic_gate_status),
        "gross_return": model.gross_return,
        "net_return": model.net_return,
        "profit_factor": model.profit_factor,
        "drawdown": model.drawdown,
        "cost_drag": model.cost_drag,
        "expectancy": model.expectancy,
        "sample_size": model.sample_size,
        "evidence_digest": model.evidence_digest,
        "evidence_reference": model.evidence_reference,
        "authoritative_gate": model.authoritative_gate,
        "effective_at": _dt_to_iso(model.effective_at),
        "provenance": provenance_to_json_dict(model.provenance),
    }


def economic_summary_from_json_dict(payload: Mapping[str, Any]) -> EconomicSummarySnapshotV1:
    return new_economic_summary_snapshot_v1(
        economic_gate_status=EconomicGateStatusV1(payload["economic_gate_status"]),
        sample_size=payload.get("sample_size"),
        evidence_digest=payload.get("evidence_digest"),
        evidence_reference=payload.get("evidence_reference"),
        effective_at=_dt_from_iso(payload["effective_at"], field="effective_at"),
        provenance=provenance_from_json_dict(payload["provenance"]),
        gross_return=payload.get("gross_return"),
        net_return=payload.get("net_return"),
        profit_factor=payload.get("profit_factor"),
        drawdown=payload.get("drawdown"),
        cost_drag=payload.get("cost_drag"),
        expectancy=payload.get("expectancy"),
        authoritative_gate=bool(payload.get("authoritative_gate", True)),
    )


def diagnostics_summary_to_json_dict(model: DiagnosticsSummarySnapshotV1) -> dict[str, Any]:
    return {
        "schema_id": model.schema_id,
        "schema_version": model.schema_version,
        "diagnostic_statuses": list(model.diagnostic_statuses),
        "bundle_digest": model.bundle_digest,
        "bundle_reference": model.bundle_reference,
        "non_authoritative": model.non_authoritative,
        "diagnostic_only": model.diagnostic_only,
        "effective_at": _dt_to_iso(model.effective_at),
        "provenance": provenance_to_json_dict(model.provenance),
    }


def diagnostics_summary_from_json_dict(
    payload: Mapping[str, Any],
) -> DiagnosticsSummarySnapshotV1:
    return new_diagnostics_summary_snapshot_v1(
        diagnostic_statuses=tuple(payload.get("diagnostic_statuses") or ()),
        bundle_digest=payload.get("bundle_digest"),
        bundle_reference=payload.get("bundle_reference"),
        effective_at=_dt_from_iso(payload["effective_at"], field="effective_at"),
        provenance=provenance_from_json_dict(payload["provenance"]),
        non_authoritative=bool(payload.get("non_authoritative", True)),
        diagnostic_only=bool(payload.get("diagnostic_only", True)),
    )


def freshness_to_json_dict(model: DashboardFreshnessSnapshotV1) -> dict[str, Any]:
    return {
        "schema_id": model.schema_id,
        "schema_version": model.schema_version,
        "page_generated_at": _dt_to_iso(model.page_generated_at),
        "source_entries": [
            {
                "source_key": entry.source_key,
                "freshness_state": _enum_value(entry.freshness_state),
                "source_age_seconds": entry.source_age_seconds,
                "missing": entry.missing,
                "stale": entry.stale,
            }
            for entry in model.source_entries
        ],
        "provenance": provenance_to_json_dict(model.provenance),
    }


def freshness_from_json_dict(payload: Mapping[str, Any]) -> DashboardFreshnessSnapshotV1:
    entries_raw = payload.get("source_entries")
    if not isinstance(entries_raw, list):
        raise MarketDashboardReadModelContractError("source_entries must be a list")
    entries = tuple(
        SourceFreshnessEntryV1(
            source_key=entry["source_key"],
            freshness_state=DashboardFreshnessStateV1(entry["freshness_state"]),
            source_age_seconds=entry.get("source_age_seconds"),
            missing=bool(entry["missing"]),
            stale=bool(entry["stale"]),
        )
        for entry in entries_raw
    )
    return new_dashboard_freshness_snapshot_v1(
        page_generated_at=_dt_from_iso(payload["page_generated_at"], field="page_generated_at"),
        source_entries=entries,
        provenance=provenance_from_json_dict(payload["provenance"]),
    )


_SECTION_SERIALIZERS: dict[type, Any] = {
    UnavailableSnapshotV1: unavailable_to_json_dict,
    MarketInstrumentSnapshotV1: market_instrument_to_json_dict,
    MarketRankingSnapshotV1: market_ranking_to_json_dict,
    CanonicalDecisionSummaryV1: canonical_decision_to_json_dict,
    DoublePlayDecisionSnapshotV1: double_play_to_json_dict,
    SafetyAuthoritySnapshotV1: safety_authority_to_json_dict,
    ExecutionStateSnapshotV1: execution_state_to_json_dict,
    EconomicSummarySnapshotV1: economic_summary_to_json_dict,
    DiagnosticsSummarySnapshotV1: diagnostics_summary_to_json_dict,
    DashboardFreshnessSnapshotV1: freshness_to_json_dict,
}

_SECTION_DESERIALIZERS: dict[str, Any] = {
    "unavailable": unavailable_from_json_dict,
    "market": market_instrument_from_json_dict,
    "ranking": market_ranking_from_json_dict,
    "decision": canonical_decision_from_json_dict,
    "double_play": double_play_from_json_dict,
    "safety_authority": safety_authority_from_json_dict,
    "execution": execution_state_from_json_dict,
    "economic": economic_summary_from_json_dict,
    "diagnostics": diagnostics_summary_from_json_dict,
    "freshness": freshness_from_json_dict,
}


def _section_to_json(section: object) -> dict[str, Any]:
    for cls, serializer in _SECTION_SERIALIZERS.items():
        if isinstance(section, cls):
            return serializer(section)
    raise MarketDashboardReadModelContractError(
        f"unsupported section type: {type(section).__name__}"
    )


def _section_kind_for_field(field: str, payload: Mapping[str, Any]) -> str:
    schema_id = str(payload.get("schema_id") or "")
    if "unavailable_snapshot" in schema_id or payload.get("availability_state"):
        return "unavailable"
    return field


def _section_from_json(field: str, payload: Mapping[str, Any]) -> object:
    kind = _section_kind_for_field(field, payload)
    if kind == "unavailable":
        return unavailable_from_json_dict(payload)
    deserializer = _SECTION_DESERIALIZERS[field]
    return deserializer(payload)


def page_snapshot_to_json_dict(model: MarketDashboardPageSnapshotV1) -> dict[str, Any]:
    return {
        "schema_id": model.schema_id,
        "schema_version": model.schema_version,
        "generated_at": _dt_to_iso(model.generated_at),
        "market": _section_to_json(model.market),
        "ranking": _section_to_json(model.ranking),
        "decision": _section_to_json(model.decision),
        "double_play": _section_to_json(model.double_play),
        "safety_authority": _section_to_json(model.safety_authority),
        "execution": _section_to_json(model.execution),
        "economic": _section_to_json(model.economic),
        "diagnostics": _section_to_json(model.diagnostics),
        "freshness": _section_to_json(model.freshness),
    }


def page_snapshot_from_json_dict(payload: Mapping[str, Any]) -> MarketDashboardPageSnapshotV1:
    return new_market_dashboard_page_snapshot_v1(
        generated_at=_dt_from_iso(payload["generated_at"], field="generated_at"),
        market=_section_from_json("market", payload["market"]),  # type: ignore[arg-type]
        ranking=_section_from_json("ranking", payload["ranking"]),  # type: ignore[arg-type]
        decision=_section_from_json("decision", payload["decision"]),  # type: ignore[arg-type]
        double_play=_section_from_json("double_play", payload["double_play"]),  # type: ignore[arg-type]
        safety_authority=_section_from_json("safety_authority", payload["safety_authority"]),  # type: ignore[arg-type]
        execution=_section_from_json("execution", payload["execution"]),  # type: ignore[arg-type]
        economic=_section_from_json("economic", payload["economic"]),  # type: ignore[arg-type]
        diagnostics=_section_from_json("diagnostics", payload["diagnostics"]),  # type: ignore[arg-type]
        freshness=_section_from_json("freshness", payload["freshness"]),  # type: ignore[arg-type]
    )


def to_json_dict(model: ContractObject) -> dict[str, Any]:
    if isinstance(model, DashboardSnapshotProvenanceV1):
        return provenance_to_json_dict(model)
    if isinstance(model, MarketDashboardPageSnapshotV1):
        return page_snapshot_to_json_dict(model)
    for cls, serializer in _SECTION_SERIALIZERS.items():
        if isinstance(model, cls):
            return serializer(model)
    raise MarketDashboardReadModelContractError(
        f"unsupported contract object: {type(model).__name__}"
    )


def dumps_json(model: ContractObject, *, indent: int | None = None) -> str:
    """Serialize with allow_nan=False so NaN/Infinity cannot leak into JSON."""

    return json.dumps(
        to_json_dict(model),
        ensure_ascii=False,
        separators=(",", ":") if indent is None else None,
        indent=indent,
        allow_nan=False,
        sort_keys=False,
    )


def loads_page_snapshot_json(text: str) -> MarketDashboardPageSnapshotV1:
    payload = json.loads(text)
    if not isinstance(payload, dict):
        raise MarketDashboardReadModelContractError("page snapshot JSON must be an object")
    return page_snapshot_from_json_dict(payload)


__all__ = [
    "canonical_decision_from_json_dict",
    "canonical_decision_to_json_dict",
    "diagnostics_summary_from_json_dict",
    "diagnostics_summary_to_json_dict",
    "double_play_from_json_dict",
    "double_play_to_json_dict",
    "dumps_json",
    "economic_summary_from_json_dict",
    "economic_summary_to_json_dict",
    "execution_state_from_json_dict",
    "execution_state_to_json_dict",
    "freshness_from_json_dict",
    "freshness_to_json_dict",
    "loads_page_snapshot_json",
    "market_instrument_from_json_dict",
    "market_instrument_to_json_dict",
    "market_ranking_from_json_dict",
    "market_ranking_to_json_dict",
    "page_snapshot_from_json_dict",
    "page_snapshot_to_json_dict",
    "provenance_from_json_dict",
    "provenance_to_json_dict",
    "safety_authority_from_json_dict",
    "safety_authority_to_json_dict",
    "to_json_dict",
    "unavailable_from_json_dict",
    "unavailable_to_json_dict",
]
