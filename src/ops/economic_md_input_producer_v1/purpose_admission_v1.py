"""Explicit point-in-time source admission; no global freshness or trading right."""

from dataclasses import dataclass
import math

from src.ops.peak_trade_public_market_data_runtime_v1.canonical_fact_decoder_v1 import (
    fact_capture_timestamp_v1,
    fact_event_time_ms_v1,
    capture_order_key_v1,
    canonical_fact_source_v1,
)


class PublicFactAvailabilityErrorV1(ValueError):
    """Preserve the existing reason token; expose age expiry vs absent PIT data."""

    def __init__(self, availability: str):
        super().__init__("DATA_ADMISSION_REQUIRED_KIND_UNAVAILABLE_ASOF")
        self.availability = availability


@dataclass(frozen=True)
class PublicFactPurposePolicyV1:
    purpose: str
    consumer: str
    canonical_instrument_id: str
    # Exact kind/channel pairs; no implicit books5->REST ticker substitution.
    allowed_sources: tuple[tuple[str, str], ...]
    # Per kind limits in seconds, including the full history needed by a window.
    maximum_ages_seconds: tuple[tuple[str, float, float], ...]
    maximum_capture_skew_seconds: float
    allow_corrected: bool
    finalized_kinds: tuple[str, ...]

    def validate_v1(self):
        if self.purpose not in {"RANKING", "TRADING", "LIQUIDITY", "OUTCOME", "RESEARCH"}:
            raise ValueError("DATA_ADMISSION_PURPOSE_INVALID")
        if any(
            not isinstance(s, str) or not s or s != s.strip()
            for s in (self.consumer, self.canonical_instrument_id)
        ):
            raise ValueError("DATA_ADMISSION_BINDING_REQUIRED")
        if type(self.allow_corrected) is not bool:
            raise ValueError("DATA_ADMISSION_CORRECTION_POLICY_REQUIRED")
        if (
            not isinstance(self.allowed_sources, tuple)
            or not self.allowed_sources
            or any(
                not isinstance(r, tuple)
                or len(r) != 2
                or any(not isinstance(x, str) or not x for x in r)
                for r in self.allowed_sources
            )
            or len(set(self.allowed_sources)) != len(self.allowed_sources)
        ):
            raise ValueError("DATA_ADMISSION_SOURCE_POLICY_INVALID")
        if not isinstance(self.maximum_ages_seconds, tuple) or not self.maximum_ages_seconds:
            raise ValueError("DATA_ADMISSION_AGE_POLICY_REQUIRED")
        for row in self.maximum_ages_seconds:
            if (
                not isinstance(row, tuple)
                or len(row) != 3
                or not isinstance(row[0], str)
                or any(
                    type(v) not in (int, float) or not math.isfinite(v) or v < 0 for v in row[1:]
                )
            ):
                raise ValueError("DATA_ADMISSION_AGE_POLICY_INVALID")
        kinds = [r[0] for r in self.maximum_ages_seconds]
        if len(kinds) != len(set(kinds)) or set(kinds) != {r[0] for r in self.allowed_sources}:
            raise ValueError("DATA_ADMISSION_KIND_POLICY_MISMATCH")
        if (
            not isinstance(self.finalized_kinds, tuple)
            or any(not isinstance(k, str) or k not in kinds for k in self.finalized_kinds)
            or len(set(self.finalized_kinds)) != len(self.finalized_kinds)
        ):
            raise ValueError("DATA_ADMISSION_FINALITY_POLICY_REQUIRED")
        if (
            type(self.maximum_capture_skew_seconds) not in (int, float)
            or not math.isfinite(self.maximum_capture_skew_seconds)
            or self.maximum_capture_skew_seconds < 0
        ):
            raise ValueError("DATA_ADMISSION_SKEW_POLICY_REQUIRED")


def admit_public_facts_for_purpose_v1(
    facts, *, policy, purpose, consumer, venue_native_id, as_of_ms
):
    if not isinstance(policy, PublicFactPurposePolicyV1):
        raise ValueError("DATA_ADMISSION_TYPED_POLICY_REQUIRED")
    policy.validate_v1()
    if policy.purpose != purpose or policy.consumer != consumer:
        raise ValueError("DATA_ADMISSION_CONSUMER_PURPOSE_MISMATCH")
    if type(as_of_ms) is not int or as_of_ms <= 0:
        raise ValueError("DATA_ADMISSION_EXPLICIT_ASOF_REQUIRED")
    limits = {r[0]: r[1:] for r in policy.maximum_ages_seconds}
    selected = []
    stale_kinds = set()
    heads = {}
    for fact in facts:
        kind = fact.get("fact_kind")
        if kind not in limits:
            raise ValueError("DATA_ADMISSION_UNDECLARED_KIND")
        if (
            fact.get("instrument", {}).get("venue_native_id") != venue_native_id
            or fact.get("instrument", {}).get("canonical_instrument_id")
            != policy.canonical_instrument_id
        ):
            raise ValueError("DATA_ADMISSION_INSTRUMENT_MISMATCH")
        event = fact_event_time_ms_v1(fact) * 1000000
        seconds, nanos = capture_order_key_v1(fact_capture_timestamp_v1(fact))
        capture = int(seconds.timestamp()) * 1000000000 + nanos
        asof = as_of_ms * 1000000
        # Later captures/corrections are unavailable to this historical consumer.
        if event > asof or capture > asof:
            continue
        effective = fact.get("timestamps", {}).get("effective_at")
        if effective is not None:
            effective_seconds, effective_nanos = capture_order_key_v1(effective)
            if int(effective_seconds.timestamp()) * 1000000000 + effective_nanos > asof:
                continue
        if (
            asof - event > limits[kind][0] * 1000000000
            or asof - capture > limits[kind][1] * 1000000000
        ):
            stale_kinds.add(kind)
            continue
        source = canonical_fact_source_v1(fact)
        if (kind, source["source_endpoint"]) not in policy.allowed_sources:
            raise ValueError("DATA_ADMISSION_SOURCE_FORBIDDEN")
        quality = fact.get("quality")
        if not isinstance(quality, dict) or any(
            type(quality.get(k)) is not bool
            for k in ("finalized", "in_progress", "missing", "stale", "corrected", "gap_detected")
        ):
            raise ValueError("DATA_ADMISSION_QUALITY_REQUIRED")
        if (
            quality["missing"]
            or quality["stale"]
            or quality["gap_detected"]
            or quality["in_progress"]
            or (kind in policy.finalized_kinds and not quality["finalized"])
        ):
            raise ValueError("DATA_ADMISSION_QUALITY_REJECTED")
        if quality["corrected"] and not policy.allow_corrected:
            raise ValueError("DATA_ADMISSION_CORRECTION_FORBIDDEN")
        if kind == "FinalizedPt1mMarkFactV1" and kind in policy.finalized_kinds:
            start = fact.get("interval_start_ms")
            if (
                type(start) is not int
                or start <= 0
                or (start + 60000) * 1000000 > min(capture, asof)
            ):
                raise ValueError("DATA_ADMISSION_FINALIZED_MARK_NOT_CLOSED_AT_CAPTURE_OR_ASOF")
        selected.append(fact)
        # Collection skew compares the newest observation head per kind.
        # Historical window members retain their own capture-age checks.
        key = (event, capture)
        if kind not in heads or key > heads[kind]:
            heads[kind] = key
    if {f["fact_kind"] for f in selected} != set(limits):
        missing = set(limits) - {f["fact_kind"] for f in selected}
        raise PublicFactAvailabilityErrorV1("STALE" if missing <= stale_kinds else "MISSING")
    captures = [key[1] for key in heads.values()]
    if max(captures) - min(captures) > policy.maximum_capture_skew_seconds * 1000000000:
        raise ValueError("DATA_ADMISSION_CAPTURE_SKEW")
    return tuple(selected)
