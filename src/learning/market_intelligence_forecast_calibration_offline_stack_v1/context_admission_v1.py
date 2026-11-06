"""Validated read-only context composition over the original Phase18/19 owners.

Receipts bind source bytes and consumer-specific policy; they do not authenticate a
venue or create a second fact store. No implicit unit conversion or model selection.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import math
from typing import Any, Mapping, Sequence

from .integration_contracts_v1 import (
    IntelligenceIdentityV1,
    MarketIdentityV1,
    assert_offline_v1,
    bytes_v1,
    instant_v1,
    require_v1,
    seal_v1,
    strict_json_v1,
    text_v1,
)
from .market_context_existing_fact_materialization_v1 import (
    ExistingFactMaterializationRequestV1,
    GovernedCanonicalFactV1,
    materialize_market_context_v1_from_existing_facts_v1,
)
from .market_context_phase_19_orthogonal_materialization_v1 import (
    validate_phase_19_canonical_fact_v1,
)

CONTEXT_PACKAGE_SCHEMA = "admitted_intelligence_context_v1"
MARKET_CONTEXT_PACKAGE_SCHEMA = "admitted_independent_market_context_v1"


@dataclass(frozen=True)
class FactAdmissionReceiptV1:
    source_ref: str
    dataset_generation: str
    payload_bytes: bytes
    known_at: str
    available_at: str
    units: Mapping[str, str]


@dataclass(frozen=True)
class ContextAdmissionPolicyV1:
    """Explicit per-use freshness limits; no global TTL, units or default forecast."""

    policy_ref: str
    max_age_seconds_by_role: Mapping[str, int]
    required_families: Sequence[str]


def _fact_groups(request):
    groups = {
        "price_mark": (request.price_mark_fact,) if request.price_mark_fact else (),
        "price_o4": (request.price_o4_bar_fact,) if request.price_o4_bar_fact else (),
        "flow": request.trade_facts or (),
        "microstructure": request.ohlcv_facts or (),
        "volatility": request.volatility_mark_facts or (),
    }
    if request.phase_19 is not None:
        p = request.phase_19
        for role, fact in (
            ("derivatives_mark", p.derivatives_mark_fact),
            ("derivatives_index", p.derivatives_index_fact),
            ("derivatives_last", p.derivatives_last_fact),
            ("funding", p.funding_rate_fact),
        ):
            groups[role] = (fact,) if fact is not None else ()
        groups["open_interest"] = p.open_interest_facts or ()
        groups["cross_selected"] = p.cross_market_selected_marks or ()
        for ref, facts in (p.cross_market_anchor_marks_by_ref or {}).items():
            text_v1(ref, "ANCHOR_INSTRUMENT")
            groups["anchor:" + ref] = facts
    return groups


def _identity_and_time(fact, identity, expected_instrument):
    p = fact.payload
    if fact.fact_kind == "FinalizedPt1hO4BarFactV1":
        bar = p["bar"]
        actual = (bar.get("canonical_instrument_id"), bar.get("venue"))
        native = bar.get("venue_instrument_id")
        event = datetime.fromtimestamp(bar["bar_close_time"], timezone.utc)
        interval_end = event
    else:
        instrument = p.get("instrument", {})
        actual = (instrument.get("canonical_instrument_id"), instrument.get("venue"))
        native = instrument.get("venue_native_id")
        ts = p.get("timestamps", {})
        event = instant_v1(ts.get("effective_at") or ts.get("captured_at"))
        interval_end = event
        if fact.fact_kind in {"FinalizedPt1mMarkFactV1", "OhlcvIntervalFactV1"}:
            ms = p.get("interval_start_ms")
            require_v1(type(ms) is int and ms % 60000 == 0, "PT1M_GRID_REQUIRED")
            if fact.fact_kind == "OhlcvIntervalFactV1":
                require_v1(p.get("interval_id") == "PT1M", "UNSUPPORTED_OHLCV_GRID")
            event = datetime.fromtimestamp(ms / 1000, timezone.utc)
            interval_end = datetime.fromtimestamp(ms / 1000 + 60, timezone.utc)
    require_v1(actual == (expected_instrument, identity.venue), "FACT_ENTITY_MISMATCH")
    text_v1(native, "NATIVE_INSTRUMENT")
    if expected_instrument == identity.instrument_ref:
        require_v1(native == identity.native_instrument_ref, "NATIVE_INSTRUMENT_MISMATCH")
    return native, event, interval_end


def _validate_numbers_and_units(fact, receipt):
    p = fact.payload
    units = dict(receipt.units)
    require_v1(bool(units), "EXPLICIT_UNITS_REQUIRED")
    for key, value in units.items():
        text_v1(key, "UNIT_FIELD")
        text_v1(value, "UNIT_SEMANTICS")
        require_v1(value not in {"UNKNOWN", "MIXED"}, "UNIT_UNKNOWN")
    fields = {
        "FinalizedPt1mMarkFactV1": ("mark_px",),
        "MarkPriceFactV1": ("mark_px",),
        "IndexPriceFactV1": ("index_px",),
        "LastTradePriceFactV1": ("last_px",),
        "TradeFactV1": ("price", "size"),
        "OhlcvIntervalFactV1": ("open_px", "high_px", "low_px", "close_px", "volume"),
        "FundingRateFactV1": ("funding_rate",),
        "OpenInterestFactV1": ("open_interest",),
        "FinalizedPt1hO4BarFactV1": ("close",),
    }.get(fact.fact_kind)
    require_v1(fields is not None, "UNSUPPORTED_FACT_KIND")
    source = p["bar"] if fact.fact_kind == "FinalizedPt1hO4BarFactV1" else p
    for field in fields:
        raw = source.get(field)
        require_v1(type(raw) in (str, int, float), "NATIVE_NUMERIC_VALUE_REQUIRED")
        try:
            value = float(raw)
        except (ValueError, OverflowError) as exc:
            raise ValueError("NATIVE_NUMERIC_VALUE_INVALID") from exc
        require_v1(math.isfinite(value), "FINITE_FACT_REQUIRED")
        if field not in {"funding_rate", "size", "volume", "open_interest"}:
            require_v1(value > 0, "POSITIVE_PRICE_REQUIRED")
        elif field != "funding_rate":
            require_v1(value >= 0, "NONNEGATIVE_QUANTITY_REQUIRED")
    if "funding_rate" in fields:
        require_v1(units.get("funding_rate", "").startswith("RATE_PER:"), "FUNDING_PERIOD_REQUIRED")
    elif "open_interest" in fields:
        require_v1(bool(units.get("open_interest")), "OI_UNIT_REQUIRED")
    else:
        require_v1(bool(units.get("price")), "PRICE_UNIT_REQUIRED")
    if "size" in fields:
        require_v1(units.get("size") == "BASE", "NO_IMPLICIT_CONTRACT_NOTIONAL_CONVERSION")
    if "volume" in fields:
        require_v1(
            units.get("volume") == "BASE" and p.get("volume_unit_semantics") == "base",
            "NO_IMPLICIT_VOLUME_CONVERSION",
        )
    return units


def compose_admitted_intelligence_context_v1(
    *,
    identity: IntelligenceIdentityV1,
    request: ExistingFactMaterializationRequestV1,
    receipts_by_digest: Mapping[str, FactAdmissionReceiptV1],
    policy: ContextAdmissionPolicyV1,
) -> dict[str, Any]:
    """Admission → original formulas → resolvable sidecar → explicit no-provider abstention."""
    require_v1(isinstance(identity, IntelligenceIdentityV1), "DDO_CONTEXT_IDENTITY_REQUIRED")
    return _compose_admitted_context_v1(
        identity=identity,
        request=request,
        receipts_by_digest=receipts_by_digest,
        policy=policy,
        schema=CONTEXT_PACKAGE_SCHEMA,
    )


def compose_admitted_market_context_v1(
    *, identity: MarketIdentityV1, request, receipts_by_digest, policy
):
    """Independent market identity with the same original fact/time/unit admission."""
    require_v1(type(identity) is MarketIdentityV1, "MARKET_CONTEXT_IDENTITY_REQUIRED")
    return _compose_admitted_context_v1(
        identity=identity,
        request=request,
        receipts_by_digest=receipts_by_digest,
        policy=policy,
        schema=MARKET_CONTEXT_PACKAGE_SCHEMA,
    )


def _compose_admitted_context_v1(*, identity, request, receipts_by_digest, policy, schema):
    assert_offline_v1()
    identity_body = identity.payload()
    require_v1(request.instrument_ref == identity.instrument_ref, "REQUEST_ENTITY_MISMATCH")
    text_v1(policy.policy_ref, "ADMISSION_POLICY")
    require_v1(bool(policy.required_families), "REQUIRED_FAMILIES_POLICY_REQUIRED")
    as_of = instant_v1(request.observed_at)
    bindings = []
    used = set()
    instrument_units = {}
    native_refs = {}
    for role, facts in _fact_groups(request).items():
        expected = (
            role.removeprefix("anchor:") if role.startswith("anchor:") else identity.instrument_ref
        )
        events = []
        hashes = set()
        limit = policy.max_age_seconds_by_role.get(role)
        if facts:
            require_v1(type(limit) is int and limit >= 0, "ROLE_FRESHNESS_POLICY_REQUIRED")
        for ordinal, fact in enumerate(facts):
            require_v1(isinstance(fact, GovernedCanonicalFactV1), "GOVERNED_FACT_REQUIRED")
            validate_phase_19_canonical_fact_v1(fact, observed_at=request.observed_at)
            receipt = receipts_by_digest.get(fact.fact_digest)
            require_v1(receipt is not None, "FACT_ADMISSION_RECEIPT_MISSING")
            text_v1(receipt.source_ref, "SOURCE_REF")
            require_v1(
                receipt.dataset_generation == identity.dataset_generation, "GENERATION_MISMATCH"
            )
            require_v1(
                bytes_v1(strict_json_v1(receipt.payload_bytes)) == bytes_v1(fact.payload),
                "ORIGINAL_FACT_BYTES_MISMATCH",
            )
            require_v1(fact.fact_digest not in hashes, "DUPLICATE_FACT_REJECTED")
            hashes.add(fact.fact_digest)
            native, event, interval_end = _identity_and_time(fact, identity, expected)
            previous_native = native_refs.setdefault(expected, native)
            require_v1(previous_native == native, "ANCHOR_NATIVE_MAPPING_CONFLICT")
            captured = instant_v1(fact.payload.get("timestamps", {}).get("captured_at"))
            known = instant_v1(receipt.known_at)
            available = instant_v1(receipt.available_at)
            require_v1(event <= known <= available <= as_of, "KNOWLEDGE_LOOKAHEAD")
            require_v1(
                captured <= available and interval_end <= available, "FINAL_VALUE_NOT_AVAILABLE"
            )
            quality = fact.payload.get("quality", {})
            require_v1(
                not any(
                    quality.get(k) is True
                    for k in ("stale", "in_progress", "missing", "gap_detected")
                ),
                "FACT_QUALITY_REJECTED",
            )
            # Correction is admitted only as its own explicit source generation, never overwritten.
            units = _validate_numbers_and_units(fact, receipt)
            for field, unit in units.items():
                key = (expected, field)
                previous = instrument_units.setdefault(key, unit)
                require_v1(previous == unit, "INCOMPATIBLE_FACT_UNITS")
            events.append(event)
            used.add(fact.fact_digest)
            bindings.append(
                {
                    "role": role,
                    "ordinal": ordinal,
                    "fact_kind": fact.fact_kind,
                    "fact_digest": fact.fact_digest,
                    "source_ref": receipt.source_ref,
                    "producer_owner": fact.producer_owner,
                    "dataset_generation": receipt.dataset_generation,
                    "original_bytes_sha256": hashlib.sha256(receipt.payload_bytes).hexdigest(),
                    "original_payload_json": receipt.payload_bytes.decode("utf-8"),
                    "payload": strict_json_v1(receipt.payload_bytes),
                    "event_time": event.isoformat(),
                    "captured_at": captured.isoformat(),
                    "known_at": known.isoformat(),
                    "available_at": available.isoformat(),
                    "units": units,
                }
            )
        if events:
            require_v1((as_of - max(events)).total_seconds() <= limit, "CONTEXT_ROLE_STALE")
            if role == "open_interest":
                require_v1(len(events) == len(set(events)), "DUPLICATE_OI_TIME_REJECTED")
            if role in {"volatility", "microstructure", "cross_selected"} or role.startswith(
                "anchor:"
            ):
                ordered = sorted(events)
                require_v1(
                    all((b - a).total_seconds() == 60 for a, b in zip(ordered, ordered[1:])),
                    "CONTIGUOUS_PT1M_GRID_REQUIRED",
                )
    require_v1(set(receipts_by_digest) == used, "UNUSED_OR_MISSING_FACT_RECEIPTS")
    # Cross-market original inner join cannot be mistaken for proof of a common complete grid.
    groups = _fact_groups(request)
    selected_grid = {f.payload["interval_start_ms"] for f in groups.get("cross_selected", ())}
    for role, facts in groups.items():
        if role.startswith("anchor:") and facts:
            require_v1(
                {f.payload["interval_start_ms"] for f in facts} == selected_grid,
                "CROSS_MARKET_GRID_MISMATCH",
            )
    derivations: dict[str, Any] = {}
    context = dict(
        materialize_market_context_v1_from_existing_facts_v1(request, derivations=derivations)
    )
    require_v1(
        all(
            ref in derivations
            for ref in (
                slot["state_ref"]
                for key, slot in context.items()
                if key.endswith("_state_ref")
                and isinstance(slot, Mapping)
                and slot.get("presence") == "PRESENT"
            )
        ),
        "UNRESOLVED_CONTEXT_REF",
    )
    known_families = {
        k for k, v in context.items() if k.endswith("_state_ref") and isinstance(v, Mapping)
    }
    require_v1(set(policy.required_families) <= known_families, "UNKNOWN_REQUIRED_FAMILY")
    missing = [k for k in policy.required_families if context[k]["presence"] != "PRESENT"]
    return seal_v1(
        {
            "schema_version": schema,
            "authority": "NONE",
            "identity": identity_body,
            "as_of": request.observed_at,
            "admission_policy": {
                "policy_ref": policy.policy_ref,
                "max_age_seconds_by_role": dict(policy.max_age_seconds_by_role),
                "required_families": list(policy.required_families),
            },
            "market_context": context,
            "materialization_parameters": {
                "information_set_identity_body": request.information_set_identity_body,
                "phase_19_present": request.phase_19 is not None,
                "cross_market_horizon_id": getattr(
                    request.phase_19, "cross_market_horizon_id", None
                ),
                "cross_market_lookback_bars": getattr(
                    request.phase_19, "cross_market_lookback_bars", None
                ),
            },
            "derivations": derivations,
            "source_bindings": sorted(bindings, key=lambda x: (x["role"], x["fact_digest"])),
            "context_status": "INSUFFICIENT" if missing else "VALID",
            "missing_families": missing,
            "forecast_disposition": "ABSTAIN",
            "forecast_reason": "MISSING_REQUIRED_FAMILIES"
            if missing
            else "NO_ADMITTED_FORECAST_PROVIDER",
            "source_authenticated": False,
            "productive_apply_authorized": False,
        }
    )


def replay_admitted_intelligence_context_v1(package: Mapping[str, Any]) -> dict[str, Any]:
    """Revalidate source bytes and reproduce the original derivations at a later read."""
    return _replay_admitted_context_v1(package, market_only=False)


def replay_admitted_market_context_v1(package):
    return _replay_admitted_context_v1(package, market_only=True)


def _replay_admitted_context_v1(package, *, market_only):
    from .integration_contracts_v1 import validate_seal_v1
    from .market_context_phase_19_orthogonal_materialization_v1 import (
        Phase19OrthogonalMaterializationInputsV1,
    )

    record = validate_seal_v1(
        package, MARKET_CONTEXT_PACKAGE_SCHEMA if market_only else CONTEXT_PACKAGE_SCHEMA
    )
    groups: dict[str, list[GovernedCanonicalFactV1]] = {}
    receipts = {}
    for binding in sorted(record["source_bindings"], key=lambda b: (b["role"], b["ordinal"])):
        raw = binding["original_payload_json"].encode("utf-8")
        require_v1(
            hashlib.sha256(raw).hexdigest() == binding["original_bytes_sha256"],
            "ORIGINAL_BYTES_CHANGED",
        )
        payload = strict_json_v1(raw)
        require_v1(bytes_v1(payload) == bytes_v1(binding["payload"]), "ORIGINAL_PAYLOAD_CHANGED")
        fact = GovernedCanonicalFactV1(
            binding["fact_kind"], binding["fact_digest"], payload, binding["producer_owner"]
        )
        groups.setdefault(binding["role"], []).append(fact)
        receipt = FactAdmissionReceiptV1(
            binding["source_ref"],
            binding["dataset_generation"],
            raw,
            binding["known_at"],
            binding["available_at"],
            binding["units"],
        )
        if fact.fact_digest in receipts:
            require_v1(receipts[fact.fact_digest] == receipt, "SOURCE_RECEIPT_CONFLICT")
        receipts[fact.fact_digest] = receipt

    def one(role):
        facts = groups.get(role, [])
        require_v1(len(facts) <= 1, "SINGLE_SOURCE_ROLE_REQUIRED")
        return facts[0] if facts else None

    params = record["materialization_parameters"]
    phase = None
    if params["phase_19_present"]:
        phase = Phase19OrthogonalMaterializationInputsV1(
            derivatives_mark_fact=one("derivatives_mark"),
            derivatives_index_fact=one("derivatives_index"),
            derivatives_last_fact=one("derivatives_last"),
            funding_rate_fact=one("funding"),
            open_interest_facts=groups.get("open_interest"),
            cross_market_selected_marks=groups.get("cross_selected"),
            cross_market_anchor_marks_by_ref={
                k.removeprefix("anchor:"): v for k, v in groups.items() if k.startswith("anchor:")
            },
            cross_market_horizon_id=params["cross_market_horizon_id"],
            cross_market_lookback_bars=params["cross_market_lookback_bars"],
        )
    native = record["market_context"]
    request = ExistingFactMaterializationRequestV1(
        record["as_of"],
        native["instrument_ref"],
        native["provenance_refs"],
        price_mark_fact=one("price_mark"),
        price_o4_bar_fact=one("price_o4"),
        trade_facts=groups.get("flow"),
        ohlcv_facts=groups.get("microstructure"),
        volatility_mark_facts=groups.get("volatility"),
        information_set_identity_body=params["information_set_identity_body"],
        phase_19=phase,
    )
    compose = (
        compose_admitted_market_context_v1
        if market_only
        else compose_admitted_intelligence_context_v1
    )
    identity_type = MarketIdentityV1 if market_only else IntelligenceIdentityV1
    replay = compose(
        identity=identity_type(**record["identity"]),
        request=request,
        receipts_by_digest=receipts,
        policy=ContextAdmissionPolicyV1(**record["admission_policy"]),
    )
    require_v1(bytes_v1(replay) == bytes_v1(record), "CONTEXT_REPLAY_MISMATCH")
    return record
