"""Phase 19 — orthogonal DERIVATIVES_STATE and CROSS_MARKET_STATE materialization (AUTHORITY=NONE)."""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from types import MappingProxyType
from typing import Any, Final, Mapping, Sequence

import numpy as np
import pandas as pd

from src.learning.deterministic_decision_outcome_v0.common_v0 import (
    require_event_time_utc,
    require_mapping,
    require_record_id,
)
from src.learning.deterministic_decision_outcome_v0.serialization_v0 import compute_content_hash_v0
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.market_context_existing_fact_materialization_v1 import (
    ExistingFactMaterializationError,
    GovernedCanonicalFactV1,
    WP_A_PRODUCER,
    _decimal_text,
    _parse_utc,
    _present_slot_from_derivation,
    _quality_finalized,
    _state_ref_for_family,
    validate_governed_canonical_fact_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.market_context_v1 import (
    CROSS_MARKET_CONTEXT_ONLY,
)
from src.ops.peak_trade_public_market_data_runtime_v1.facts_v1 import fact_digest

PHASE_19_SCHEMA: Final[str] = "market_context_phase_19_orthogonal_materialization_v1"
PHASE_19_OWNER: Final[str] = (
    "learning.market_intelligence_forecast_calibration_offline_stack_v1."
    "market_context_phase_19_orthogonal_materialization_v1"
)

FACT_KIND_MARK_PRICE: Final[str] = "MarkPriceFactV1"
FACT_KIND_INDEX_PRICE: Final[str] = "IndexPriceFactV1"
FACT_KIND_LAST_TRADE: Final[str] = "LastTradePriceFactV1"
FACT_KIND_FUNDING_RATE: Final[str] = "FundingRateFactV1"
FACT_KIND_OPEN_INTEREST: Final[str] = "OpenInterestFactV1"
FACT_KIND_FINALIZED_PT1M_MARK: Final[str] = "FinalizedPt1mMarkFactV1"

_PHASE_19_FACT_KINDS: Final[frozenset[str]] = frozenset(
    {
        FACT_KIND_MARK_PRICE,
        FACT_KIND_INDEX_PRICE,
        FACT_KIND_LAST_TRADE,
        FACT_KIND_FUNDING_RATE,
        FACT_KIND_OPEN_INTEREST,
        FACT_KIND_FINALIZED_PT1M_MARK,
    }
)

DERIVATIVES_FEATURE_VERSION: Final[str] = "wp_a_derivatives_orthogonal_v1"
CROSS_MARKET_FEATURE_VERSION: Final[str] = "bounded_anchor_cross_market_v1"
ANCHOR_BINDING_CONFIG: Final[str] = (
    "config/governance/market_context_v1_phase_19_cross_market_anchor_binding_v1.json"
)

FUNDING_EXTREMENESS_MISSING: Final[str] = "FUNDING_EXTREMENESS_HISTORY_NOT_PROVEN_CURRENT"
OI_CHANGE_MISSING: Final[str] = "OPEN_INTEREST_CHANGE_REQUIRES_TWO_PIT_SNAPSHOTS"


def load_cross_market_anchor_binding_v1(*, repo_root: Path | None = None) -> Mapping[str, Any]:
    root = repo_root or Path(__file__).resolve().parents[3]
    doc = json.loads((root / ANCHOR_BINDING_CONFIG).read_text(encoding="utf-8"))
    if doc.get("context_only") is not True:
        raise ExistingFactMaterializationError("ANCHOR_BINDING_MUST_BE_CONTEXT_ONLY")
    if doc.get("cap23_selection_authority") is not False:
        raise ExistingFactMaterializationError("ANCHOR_BINDING_MUST_NOT_GRANT_CAP23")
    return doc


def validate_phase_19_canonical_fact_v1(
    fact: GovernedCanonicalFactV1,
    *,
    observed_at: str,
) -> Mapping[str, Any]:
    if fact.fact_kind in _PHASE_19_FACT_KINDS:
        if fact.producer_owner != WP_A_PRODUCER:
            raise ExistingFactMaterializationError("ungoverned_producer_rejected")
        payload = require_mapping(fact.payload, "fact_payload")
        if payload.get("fact_kind") not in (None, fact.fact_kind):
            raise ExistingFactMaterializationError("FACT_KIND_PAYLOAD_MISMATCH")
        if fact_digest(payload) != fact.fact_digest:
            raise ExistingFactMaterializationError("fact_digest_mismatch_rejected")
        if not _quality_finalized(payload):
            raise ExistingFactMaterializationError("unfinalized_fact_rejected")
        pit = _pit_for_phase_19_fact(fact.fact_kind, payload)
        if _parse_utc(pit) > _parse_utc(observed_at):
            raise ExistingFactMaterializationError("pit_lookahead_rejected")
        return payload
    return validate_governed_canonical_fact_v1(fact, observed_at=observed_at)


def _pit_for_phase_19_fact(kind: str, payload: Mapping[str, Any]) -> str:
    if kind == FACT_KIND_FINALIZED_PT1M_MARK:
        ms = int(payload["interval_start_ms"])
        return (
            datetime.fromtimestamp(ms / 1000.0, tz=timezone.utc)
            .replace(microsecond=0)
            .isoformat()
            .replace("+00:00", "Z")
        )
    timestamps = require_mapping(payload.get("timestamps"), "timestamps")
    effective = timestamps.get("effective_at") or timestamps.get("captured_at")
    return require_event_time_utc(str(effective), "pit")


def _mark_px_from_payload(kind: str, payload: Mapping[str, Any]) -> str:
    if kind == FACT_KIND_MARK_PRICE:
        return str(payload["mark_px"])
    if kind == FACT_KIND_FINALIZED_PT1M_MARK:
        return str(payload["mark_px"])
    raise ExistingFactMaterializationError("NOT_A_MARK_LEG")


@dataclass(frozen=True)
class Phase19OrthogonalMaterializationInputsV1:
    derivatives_mark_fact: GovernedCanonicalFactV1 | None = None
    derivatives_index_fact: GovernedCanonicalFactV1 | None = None
    derivatives_last_fact: GovernedCanonicalFactV1 | None = None
    funding_rate_fact: GovernedCanonicalFactV1 | None = None
    open_interest_facts: Sequence[GovernedCanonicalFactV1] | None = None
    cross_market_selected_marks: Sequence[GovernedCanonicalFactV1] | None = None
    cross_market_anchor_marks_by_ref: Mapping[str, Sequence[GovernedCanonicalFactV1]] | None = None
    cross_market_horizon_id: str | None = None
    cross_market_lookback_bars: int | None = None


def derive_derivatives_state_slot_v1(
    *,
    inputs: Phase19OrthogonalMaterializationInputsV1,
    observed_at: str,
) -> dict[str, Any] | None:
    mark_fact = inputs.derivatives_mark_fact
    if mark_fact is None:
        return None
    if mark_fact.fact_kind not in {FACT_KIND_MARK_PRICE, FACT_KIND_FINALIZED_PT1M_MARK}:
        raise ExistingFactMaterializationError("DERIVATIVES_MARK_LEG_INVALID")
    mark_payload = validate_phase_19_canonical_fact_v1(mark_fact, observed_at=observed_at)
    mark_px = _mark_px_from_payload(mark_fact.fact_kind, mark_payload)
    mark_pit = _pit_for_phase_19_fact(mark_fact.fact_kind, mark_payload)

    index_px: str | None = None
    index_digest: str | None = None
    if inputs.derivatives_index_fact is not None:
        idx_payload = validate_phase_19_canonical_fact_v1(
            inputs.derivatives_index_fact, observed_at=observed_at
        )
        if inputs.derivatives_index_fact.fact_kind != FACT_KIND_INDEX_PRICE:
            raise ExistingFactMaterializationError("DERIVATIVES_INDEX_LEG_INVALID")
        index_px = str(idx_payload["index_px"])
        index_digest = inputs.derivatives_index_fact.fact_digest

    last_px: str | None = None
    last_digest: str | None = None
    if inputs.derivatives_last_fact is not None:
        last_payload = validate_phase_19_canonical_fact_v1(
            inputs.derivatives_last_fact, observed_at=observed_at
        )
        if inputs.derivatives_last_fact.fact_kind != FACT_KIND_LAST_TRADE:
            raise ExistingFactMaterializationError("DERIVATIVES_LAST_LEG_INVALID")
        last_px = str(last_payload["last_px"])
        last_digest = inputs.derivatives_last_fact.fact_digest

    basis_log: str | None = None
    if index_px is not None:
        m = float(mark_px)
        i = float(index_px)
        if m <= 0 or i <= 0:
            raise ExistingFactMaterializationError("BASIS_NONPOSITIVE_PRICE")
        basis_log = _decimal_text(math.log(m / i))

    funding_rate: str | None = None
    funding_digest: str | None = None
    if inputs.funding_rate_fact is not None:
        fr_payload = validate_phase_19_canonical_fact_v1(
            inputs.funding_rate_fact, observed_at=observed_at
        )
        if inputs.funding_rate_fact.fact_kind != FACT_KIND_FUNDING_RATE:
            raise ExistingFactMaterializationError("FUNDING_FACT_INVALID")
        funding_rate = str(fr_payload["funding_rate"])
        funding_digest = inputs.funding_rate_fact.fact_digest

    oi_level: str | None = None
    oi_change: str | None = None
    oi_digests: tuple[str, ...] = ()
    if inputs.open_interest_facts:
        oi_rows: list[tuple[datetime, str, str]] = []
        for fact in inputs.open_interest_facts:
            payload = validate_phase_19_canonical_fact_v1(fact, observed_at=observed_at)
            if fact.fact_kind != FACT_KIND_OPEN_INTEREST:
                raise ExistingFactMaterializationError("OPEN_INTEREST_FACT_INVALID")
            pit = _parse_utc(_pit_for_phase_19_fact(fact.fact_kind, payload))
            oi_rows.append((pit, str(payload["open_interest"]), fact.fact_digest))
        oi_rows.sort(key=lambda row: row[0])
        oi_level = oi_rows[-1][1]
        oi_digests = tuple(sorted({row[2] for row in oi_rows}))
        if len(oi_rows) >= 2:
            oi_change = _decimal_text(float(oi_rows[-1][1]) - float(oi_rows[-2][1]))
        else:
            oi_change = OI_CHANGE_MISSING

    identity = {
        "family": "derivatives_state",
        "mark_px": mark_px,
        "mark_fact_digest": mark_fact.fact_digest,
        "index_px": index_px,
        "index_fact_digest": index_digest,
        "last_px": last_px,
        "last_fact_digest": last_digest,
        "basis_log_mark_over_index": basis_log,
        "funding_rate": funding_rate,
        "funding_fact_digest": funding_digest,
        "funding_extremeness": FUNDING_EXTREMENESS_MISSING if funding_rate else None,
        "open_interest_level": oi_level,
        "open_interest_change": oi_change,
        "open_interest_fact_digests": oi_digests,
    }
    return _present_slot_from_derivation(
        field_name="derivatives_state_ref",
        state_ref=_state_ref_for_family(family="derivatives_state", identity_body=identity),
        pit_observed_at_utc=mark_pit,
        producer_owner=WP_A_PRODUCER,
        feature_version=DERIVATIVES_FEATURE_VERSION,
    )


def _marks_to_series(
    facts: Sequence[GovernedCanonicalFactV1],
    *,
    observed_at: str,
) -> pd.Series:
    rows: list[tuple[datetime, float]] = []
    for fact in facts:
        payload = validate_phase_19_canonical_fact_v1(fact, observed_at=observed_at)
        if fact.fact_kind != FACT_KIND_FINALIZED_PT1M_MARK:
            raise ExistingFactMaterializationError("CROSS_MARKET_REQUIRES_PT1M_MARKS")
        pit = _parse_utc(_pit_for_phase_19_fact(fact.fact_kind, payload))
        rows.append((pit, float(payload["mark_px"])))
    rows.sort(key=lambda item: item[0])
    index = pd.DatetimeIndex([r[0] for r in rows], tz="UTC")
    return pd.Series([r[1] for r in rows], index=index, dtype=float)


def derive_cross_market_state_slot_v1(
    *,
    inputs: Phase19OrthogonalMaterializationInputsV1,
    observed_at: str,
    instrument_ref: str,
    repo_root: Path | None = None,
) -> dict[str, Any] | None:
    if not inputs.cross_market_selected_marks or not inputs.cross_market_anchor_marks_by_ref:
        return None
    binding = load_cross_market_anchor_binding_v1(repo_root=repo_root)
    allowed = frozenset(str(x) for x in binding.get("admissible_anchor_instrument_refs") or [])
    horizon = inputs.cross_market_horizon_id or str(binding.get("default_horizon_id"))
    lookback = int(inputs.cross_market_lookback_bars or binding.get("default_lookback_bars") or 60)

    selected = _marks_to_series(inputs.cross_market_selected_marks, observed_at=observed_at)
    observed_dt = _parse_utc(observed_at)
    selected = selected[selected.index <= observed_dt]
    if len(selected) < lookback:
        raise ExistingFactMaterializationError("insufficient_cross_market_warmup_rejected")

    anchor_metrics: dict[str, Any] = {}
    digests: list[str] = []
    for anchor_ref, anchor_facts in inputs.cross_market_anchor_marks_by_ref.items():
        anchor_id = require_record_id(anchor_ref, "anchor_ref")
        if anchor_id not in allowed:
            raise ExistingFactMaterializationError("ANCHOR_NOT_IN_GOVERNED_BINDING")
        if anchor_id == instrument_ref:
            raise ExistingFactMaterializationError("ANCHOR_MUST_NOT_EQUAL_SELECTED_INSTRUMENT")
        anchor = _marks_to_series(anchor_facts, observed_at=observed_at)
        anchor = anchor[anchor.index <= observed_dt]
        joined = pd.concat(
            [selected.rename("sel"), anchor.rename("anc")], axis=1, join="inner"
        ).dropna()
        if len(joined) < lookback:
            raise ExistingFactMaterializationError("insufficient_cross_market_overlap_rejected")
        window = joined.iloc[-lookback:]
        sel_ret = np.log(window["sel"]).diff().dropna()
        anc_ret = np.log(window["anc"]).diff().dropna()
        aligned = pd.concat([sel_ret, anc_ret], axis=1, join="inner").dropna()
        if len(aligned) < 2:
            raise ExistingFactMaterializationError("insufficient_cross_market_returns_rejected")
        s = aligned.iloc[:, 0]
        a = aligned.iloc[:, 1]
        corr = float(s.corr(a))
        beta = float(s.cov(a) / a.var()) if float(a.var()) != 0.0 else None
        rel_vol = float(s.std(ddof=0) / a.std(ddof=0)) if float(a.std(ddof=0)) != 0.0 else None
        rel_ret = (
            float(sel_ret.iloc[-1] - anc_ret.iloc[-1]) if len(sel_ret) and len(anc_ret) else None
        )
        common = float(beta * anc_ret.iloc[-1]) if beta is not None and len(anc_ret) else None
        idio = float(rel_ret - common) if rel_ret is not None and common is not None else None
        for fact in anchor_facts:
            digests.append(fact.fact_digest)
        anchor_metrics[anchor_id] = {
            "horizon_id": horizon,
            "lookback_bars": lookback,
            "correlation": _decimal_text(corr)
            if corr is not None and not math.isnan(corr)
            else None,
            "beta": _decimal_text(beta) if beta is not None else None,
            "relative_volatility": _decimal_text(rel_vol) if rel_vol is not None else None,
            "relative_return_1bar": _decimal_text(rel_ret) if rel_ret is not None else None,
            "common_move_1bar": _decimal_text(common) if common is not None else None,
            "idiosyncratic_move_1bar": _decimal_text(idio) if idio is not None else None,
        }

    pit_iso = selected.index[-1].replace(microsecond=0).isoformat().replace("+00:00", "Z")
    identity = {
        "family": "cross_market_state",
        "binding_id": binding.get("binding_id"),
        "instrument_ref": instrument_ref,
        "anchor_metrics": anchor_metrics,
        "fact_digests": tuple(sorted(set(digests))),
    }
    return _present_slot_from_derivation(
        field_name="cross_market_state_ref",
        state_ref=_state_ref_for_family(family="cross_market_state", identity_body=identity),
        pit_observed_at_utc=pit_iso,
        producer_owner=PHASE_19_OWNER,
        feature_version=CROSS_MARKET_FEATURE_VERSION,
        extra={"cross_market_authority": CROSS_MARKET_CONTEXT_ONLY},
    )


def assert_phase_19_authority_invariants_v1() -> Mapping[str, Any]:
    from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.constants_v1 import (
        EXTERNAL_EFFECT_AUTHORIZED,
        LEARNING_TRADING_AUTHORITY,
        MARKET_INTELLIGENCE_TRADING_AUTHORITY,
        MULTI_FUTURE_RUNTIME_AUTHORIZED,
        NO_AUTOMATIC_PROMOTION,
        OPTIMIZATION_PRODUCTIVE_AUTHORITY,
    )

    terminal = {
        "MARKET_CONTEXT_AUTHORITY": "NONE",
        "CROSS_MARKET_IS_CONTEXT_ONLY": True,
        "OPTIMIZATION_PROMOTION_AUTHORITY": "NONE",
        "META_EVIDENCE_AUTHORITY": "NONE",
        "MV2_DP_UNCHANGED": True,
        "NO_AUTHORITY_EXPANSION": True,
        "LEARNING_TRADING_AUTHORITY": LEARNING_TRADING_AUTHORITY,
        "MARKET_INTELLIGENCE_TRADING_AUTHORITY": MARKET_INTELLIGENCE_TRADING_AUTHORITY,
        "EXTERNAL_EFFECT_AUTHORIZED": EXTERNAL_EFFECT_AUTHORIZED,
        "MULTI_FUTURE_RUNTIME_AUTHORIZED": MULTI_FUTURE_RUNTIME_AUTHORIZED,
        "NO_AUTOMATIC_PROMOTION": NO_AUTOMATIC_PROMOTION,
        "OPTIMIZATION_PRODUCTIVE_AUTHORITY": OPTIMIZATION_PRODUCTIVE_AUTHORITY,
    }
    if terminal["MARKET_CONTEXT_AUTHORITY"] != "NONE":
        raise ExistingFactMaterializationError("AUTHORITY_EXPANSION_FORBIDDEN")
    if terminal["EXTERNAL_EFFECT_AUTHORIZED"] is not False:
        raise ExistingFactMaterializationError("EXTERNAL_EFFECT_FORBIDDEN")
    if terminal["MULTI_FUTURE_RUNTIME_AUTHORIZED"] is not False:
        raise ExistingFactMaterializationError("MULTI_FUTURE_FORBIDDEN")
    return MappingProxyType(terminal)


__all__ = [
    "ANCHOR_BINDING_CONFIG",
    "DERIVATIVES_FEATURE_VERSION",
    "CROSS_MARKET_FEATURE_VERSION",
    "PHASE_19_OWNER",
    "PHASE_19_SCHEMA",
    "Phase19OrthogonalMaterializationInputsV1",
    "assert_phase_19_authority_invariants_v1",
    "derive_cross_market_state_slot_v1",
    "derive_derivatives_state_slot_v1",
    "load_cross_market_anchor_binding_v1",
    "validate_phase_19_canonical_fact_v1",
]
