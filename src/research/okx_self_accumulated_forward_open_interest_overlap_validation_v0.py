"""OKX self-accumulated forward open-interest overlap validation v0.

Offline-only deterministic comparison between self-accumulated archive snapshots
and an explicit external reference input. Research-only; no runtime authority.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Mapping, Sequence

from src.research.cross_sectional_open_interest_delta_rank_v0_capability_gap_registration_and_scope_parking_v0 import (
    RESEARCH_SCOPE,
)
from src.research.okx_self_accumulated_forward_open_interest_archive_v0 import (
    OBSERVATIONS_JSONL_FILENAME,
    observation_from_row_dict_v0,
    serialize_canonical_json,
)

PACKAGE_MARKER = "OKX_SELF_ACCUMULATED_FORWARD_OPEN_INTEREST_OVERLAP_VALIDATION_V0=true"
MODULE_VERSION = "okx_self_accumulated_forward_open_interest_overlap_validation.v0"
CONFIRM_GO = "GO_OKX_SELF_ACCUMULATED_FORWARD_OPEN_INTEREST_OVERLAP_VALIDATION_V0"
CONFIG_REL_PATH = (
    "config/research/okx_self_accumulated_forward_open_interest_overlap_validation_v0.json"
)

AUTHORITY_EFFECT = "NONE"
RUNTIME_EFFECT = "NONE"
TIMESTAMP_ALIGNMENT_POLICY_EXACT = "EXACT_VENUE_TIMESTAMP_MS"
DUPLICATE_POLICY_REJECT = "REJECT_DUPLICATE_VENUE_TIMESTAMP"
MISSING_PAIR_POLICY_CLASSIFY = "CLASSIFY_MISSING_PAIRS"


class OverlapValidationStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
    BLOCKED_MISSING_REFERENCE = "BLOCKED_MISSING_REFERENCE"
    BLOCKED_INVALID_SELF_ACCUMULATED_ARCHIVE = "BLOCKED_INVALID_SELF_ACCUMULATED_ARCHIVE"
    BLOCKED_INVALID_REFERENCE = "BLOCKED_INVALID_REFERENCE"
    BLOCKED_TIMESTAMP_ALIGNMENT = "BLOCKED_TIMESTAMP_ALIGNMENT"
    BLOCKED_UNSUPPORTED_SCHEMA = "BLOCKED_UNSUPPORTED_SCHEMA"


class OverlapValidationVerdict(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
    NOT_EXECUTABLE = "NOT_EXECUTABLE"


class TimestampAlignmentStatus(str, Enum):
    NOT_EXECUTED = "NOT_EXECUTED"
    ALIGNED = "ALIGNED"
    PARTIAL = "PARTIAL"
    BLOCKED = "BLOCKED"


class ValueComparisonStatus(str, Enum):
    NOT_EXECUTED = "NOT_EXECUTED"
    ALL_MATCHED = "ALL_MATCHED"
    MISMATCH_PRESENT = "MISMATCH_PRESENT"
    INSUFFICIENT_PAIRS = "INSUFFICIENT_PAIRS"


@dataclass(frozen=True)
class OverlapValidationConfigV0:
    schema_version: str
    timestamp_alignment_policy: str
    maximum_timestamp_delta_seconds: int
    absolute_tolerance: str
    relative_tolerance: str
    minimum_aligned_pairs: int
    duplicate_policy: str
    missing_pair_policy: str
    fail_closed_on_missing_reference: bool


@dataclass(frozen=True)
class OverlapValidationResultV0:
    schema_version: str
    validation_id: str
    self_accumulated_source_ref: str
    external_reference_source_ref: str | None
    instrument_id: str | None
    requested_start_utc: str | None
    requested_end_utc: str | None
    self_accumulated_observation_count: int
    reference_observation_count: int
    aligned_pair_count: int
    matched_pair_count: int
    mismatched_pair_count: int
    missing_reference_count: int
    missing_self_accumulated_count: int
    timestamp_alignment_status: str
    value_comparison_status: str
    absolute_tolerance: str
    relative_tolerance: str
    status: str
    verdict: str
    reason_codes: tuple[str, ...] = ()
    authority_effect: str = AUTHORITY_EFFECT
    runtime_effect: str = RUNTIME_EFFECT


def compute_implementation_digest_v0() -> str:
    return hashlib.sha256(
        serialize_canonical_json(
            {
                "module": "okx_self_accumulated_forward_open_interest_overlap_validation_v0",
                "module_version": MODULE_VERSION,
                "confirm_go": CONFIRM_GO,
            }
        ).encode("utf-8")
    ).hexdigest()


def build_overlap_validation_config_v0() -> dict[str, Any]:
    config_path = Path(__file__).resolve().parents[2] / CONFIG_REL_PATH
    return json.loads(config_path.read_text(encoding="utf-8"))


def load_versioned_config_v0() -> OverlapValidationConfigV0:
    raw = build_overlap_validation_config_v0()
    return OverlapValidationConfigV0(
        schema_version=str(raw["schema_version"]),
        timestamp_alignment_policy=str(raw["timestamp_alignment_policy"]),
        maximum_timestamp_delta_seconds=int(raw["maximum_timestamp_delta_seconds"]),
        absolute_tolerance=str(raw["absolute_tolerance"]),
        relative_tolerance=str(raw["relative_tolerance"]),
        minimum_aligned_pairs=int(raw["minimum_aligned_pairs"]),
        duplicate_policy=str(raw["duplicate_policy"]),
        missing_pair_policy=str(raw["missing_pair_policy"]),
        fail_closed_on_missing_reference=bool(raw["fail_closed_on_missing_reference"]),
    )


def _resolve_jsonl_path(source: Path) -> Path | None:
    if source.is_file() and source.name.endswith(".jsonl"):
        return source
    if source.is_dir():
        candidate = source / OBSERVATIONS_JSONL_FILENAME
        if candidate.is_file():
            return candidate
    return None


def _canonical_source_ref(path: Path | None) -> str | None:
    if path is None:
        return None
    try:
        return str(path.resolve())
    except OSError:
        return str(path)


def _same_source_binding(
    self_accumulated_source: Path | None,
    external_reference_source: Path | None,
) -> bool:
    self_ref = _canonical_source_ref(self_accumulated_source)
    external_ref = _canonical_source_ref(external_reference_source)
    if self_ref is None or external_ref is None:
        return False
    return self_ref == external_ref


def _parse_open_interest_value(raw: str) -> tuple[float | None, str | None]:
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return None, "INVALID_OPEN_INTEREST_VALUE"
    if not math.isfinite(value):
        return None, "NON_FINITE_OPEN_INTEREST_VALUE"
    if value < 0:
        return None, "NEGATIVE_OPEN_INTEREST_VALUE"
    return value, None


def _load_observations_v0(
    jsonl_path: Path,
) -> tuple[list[dict[str, Any]], list[str]]:
    if not jsonl_path.is_file():
        return [], ["MISSING_OBSERVATIONS_JSONL"]
    observations: list[dict[str, Any]] = []
    reason_codes: list[str] = []
    seen_keys: set[tuple[str, int]] = set()
    for raw in jsonl_path.read_text(encoding="utf-8").splitlines():
        if not raw.strip():
            continue
        try:
            row = json.loads(raw)
        except json.JSONDecodeError:
            return [], ["MALFORMED_JSON"]
        if not isinstance(row, dict):
            return [], ["INVALID_FIELD_TYPE"]
        obs, reason = observation_from_row_dict_v0(row)
        if obs is None:
            return [], [reason or "UNSUPPORTED_SCHEMA"]
        oi_value, oi_reason = _parse_open_interest_value(obs.open_interest_raw)
        if oi_value is None:
            return [], [oi_reason or "INVALID_OPEN_INTEREST_VALUE"]
        key = (obs.instrument_id, obs.venue_timestamp_ms)
        if key in seen_keys:
            return [], ["DUPLICATE_VENUE_TIMESTAMP"]
        seen_keys.add(key)
        observations.append(
            {
                "instrument_id": obs.instrument_id,
                "native_instrument_id": obs.native_instrument_id,
                "venue_timestamp_ms": obs.venue_timestamp_ms,
                "venue_timestamp_utc": obs.venue_timestamp_utc,
                "open_interest_raw": obs.open_interest_raw,
                "open_interest_value": oi_value,
            }
        )
    observations.sort(key=lambda item: (item["instrument_id"], item["venue_timestamp_ms"]))
    return observations, reason_codes


def _values_match_v0(
    *,
    self_value: float,
    reference_value: float,
    absolute_tolerance: float,
    relative_tolerance: float,
) -> bool:
    abs_diff = abs(self_value - reference_value)
    if abs_diff <= absolute_tolerance:
        return True
    if reference_value == 0:
        return abs_diff <= absolute_tolerance
    return abs_diff / abs(reference_value) <= relative_tolerance


def _compute_validation_id(payload: Mapping[str, Any]) -> str:
    body = {k: v for k, v in payload.items() if k != "validation_id"}
    return hashlib.sha256(serialize_canonical_json(body).encode("utf-8")).hexdigest()


def _blocked_result(
    *,
    status: OverlapValidationStatus,
    verdict: OverlapValidationVerdict,
    self_accumulated_source_ref: str,
    external_reference_source_ref: str | None,
    config: OverlapValidationConfigV0,
    reason_codes: Sequence[str],
    instrument_id: str | None = None,
    requested_start_utc: str | None = None,
    requested_end_utc: str | None = None,
    self_accumulated_observation_count: int = 0,
    reference_observation_count: int = 0,
    aligned_pair_count: int = 0,
    matched_pair_count: int = 0,
    mismatched_pair_count: int = 0,
    missing_reference_count: int = 0,
    missing_self_accumulated_count: int = 0,
    timestamp_alignment_status: TimestampAlignmentStatus = TimestampAlignmentStatus.NOT_EXECUTED,
    value_comparison_status: ValueComparisonStatus = ValueComparisonStatus.NOT_EXECUTED,
) -> OverlapValidationResultV0:
    payload = {
        "schema_version": MODULE_VERSION,
        "self_accumulated_source_ref": self_accumulated_source_ref,
        "external_reference_source_ref": external_reference_source_ref,
        "instrument_id": instrument_id,
        "requested_start_utc": requested_start_utc,
        "requested_end_utc": requested_end_utc,
        "self_accumulated_observation_count": self_accumulated_observation_count,
        "reference_observation_count": reference_observation_count,
        "aligned_pair_count": aligned_pair_count,
        "matched_pair_count": matched_pair_count,
        "mismatched_pair_count": mismatched_pair_count,
        "missing_reference_count": missing_reference_count,
        "missing_self_accumulated_count": missing_self_accumulated_count,
        "timestamp_alignment_status": timestamp_alignment_status.value,
        "value_comparison_status": value_comparison_status.value,
        "absolute_tolerance": config.absolute_tolerance,
        "relative_tolerance": config.relative_tolerance,
        "status": status.value,
        "verdict": verdict.value,
        "reason_codes": list(reason_codes),
        "authority_effect": AUTHORITY_EFFECT,
        "runtime_effect": RUNTIME_EFFECT,
    }
    validation_id = _compute_validation_id(payload)
    return OverlapValidationResultV0(validation_id=validation_id, **payload)


def validate_overlap_v0(
    *,
    self_accumulated_source: Path | None,
    external_reference_source: Path | None,
    instrument_id: str | None = None,
    requested_start_utc: str | None = None,
    requested_end_utc: str | None = None,
    config: OverlapValidationConfigV0 | None = None,
) -> OverlapValidationResultV0:
    """Compare self-accumulated archive observations against explicit external reference."""
    cfg = config or load_versioned_config_v0()
    self_ref = _canonical_source_ref(self_accumulated_source) or ""
    external_ref = _canonical_source_ref(external_reference_source)

    if external_reference_source is None or external_ref is None:
        return _blocked_result(
            status=OverlapValidationStatus.BLOCKED_MISSING_REFERENCE,
            verdict=OverlapValidationVerdict.NOT_EXECUTABLE,
            self_accumulated_source_ref=self_ref,
            external_reference_source_ref=external_ref,
            config=cfg,
            reason_codes=("MISSING_EXTERNAL_REFERENCE",),
        )

    if _same_source_binding(self_accumulated_source, external_reference_source):
        return _blocked_result(
            status=OverlapValidationStatus.BLOCKED_INVALID_REFERENCE,
            verdict=OverlapValidationVerdict.NOT_EXECUTABLE,
            self_accumulated_source_ref=self_ref,
            external_reference_source_ref=external_ref,
            config=cfg,
            reason_codes=("SAME_INPUT_DUAL_BINDING_FORBIDDEN",),
        )

    if self_accumulated_source is None:
        return _blocked_result(
            status=OverlapValidationStatus.BLOCKED_INVALID_SELF_ACCUMULATED_ARCHIVE,
            verdict=OverlapValidationVerdict.NOT_EXECUTABLE,
            self_accumulated_source_ref=self_ref,
            external_reference_source_ref=external_ref,
            config=cfg,
            reason_codes=("MISSING_SELF_ACCUMULATED_ARCHIVE",),
        )

    self_jsonl = _resolve_jsonl_path(self_accumulated_source)
    if self_jsonl is None:
        return _blocked_result(
            status=OverlapValidationStatus.BLOCKED_INVALID_SELF_ACCUMULATED_ARCHIVE,
            verdict=OverlapValidationVerdict.NOT_EXECUTABLE,
            self_accumulated_source_ref=self_ref,
            external_reference_source_ref=external_ref,
            config=cfg,
            reason_codes=("MISSING_SELF_ACCUMULATED_OBSERVATIONS_JSONL",),
        )

    reference_jsonl = _resolve_jsonl_path(external_reference_source)
    if reference_jsonl is None:
        return _blocked_result(
            status=OverlapValidationStatus.BLOCKED_MISSING_REFERENCE,
            verdict=OverlapValidationVerdict.NOT_EXECUTABLE,
            self_accumulated_source_ref=self_ref,
            external_reference_source_ref=external_ref,
            config=cfg,
            reason_codes=("MISSING_EXTERNAL_REFERENCE_OBSERVATIONS_JSONL",),
        )

    self_observations, self_reasons = _load_observations_v0(self_jsonl)
    if self_reasons:
        blocked_status = OverlapValidationStatus.BLOCKED_UNSUPPORTED_SCHEMA
        if any(code in self_reasons for code in ("MALFORMED_JSON", "INVALID_FIELD_TYPE")):
            blocked_status = OverlapValidationStatus.BLOCKED_INVALID_SELF_ACCUMULATED_ARCHIVE
        return _blocked_result(
            status=blocked_status,
            verdict=OverlapValidationVerdict.NOT_EXECUTABLE,
            self_accumulated_source_ref=self_ref,
            external_reference_source_ref=external_ref,
            config=cfg,
            reason_codes=tuple(self_reasons),
            self_accumulated_observation_count=len(self_observations),
        )

    reference_observations, reference_reasons = _load_observations_v0(reference_jsonl)
    if reference_reasons:
        blocked_status = OverlapValidationStatus.BLOCKED_UNSUPPORTED_SCHEMA
        if any(code in reference_reasons for code in ("MALFORMED_JSON", "INVALID_FIELD_TYPE")):
            blocked_status = OverlapValidationStatus.BLOCKED_INVALID_REFERENCE
        return _blocked_result(
            status=blocked_status,
            verdict=OverlapValidationVerdict.NOT_EXECUTABLE,
            self_accumulated_source_ref=self_ref,
            external_reference_source_ref=external_ref,
            config=cfg,
            reason_codes=tuple(reference_reasons),
            self_accumulated_observation_count=len(self_observations),
            reference_observation_count=len(reference_observations),
        )

    if instrument_id is not None:
        self_observations = [o for o in self_observations if o["instrument_id"] == instrument_id]
        reference_observations = [
            o for o in reference_observations if o["instrument_id"] == instrument_id
        ]

    if not self_observations and not reference_observations:
        return _blocked_result(
            status=OverlapValidationStatus.INSUFFICIENT_DATA,
            verdict=OverlapValidationVerdict.INSUFFICIENT_DATA,
            self_accumulated_source_ref=self_ref,
            external_reference_source_ref=external_ref,
            config=cfg,
            reason_codes=("NO_OBSERVATIONS_FOR_INSTRUMENT",),
            instrument_id=instrument_id,
            requested_start_utc=requested_start_utc,
            requested_end_utc=requested_end_utc,
        )

    if self_observations and reference_observations:
        self_instruments = {o["instrument_id"] for o in self_observations}
        reference_instruments = {o["instrument_id"] for o in reference_observations}
        if self_instruments != reference_instruments:
            return _blocked_result(
                status=OverlapValidationStatus.BLOCKED_INVALID_REFERENCE,
                verdict=OverlapValidationVerdict.NOT_EXECUTABLE,
                self_accumulated_source_ref=self_ref,
                external_reference_source_ref=external_ref,
                config=cfg,
                reason_codes=("MISMATCHED_INSTRUMENT_ID",),
                instrument_id=instrument_id,
                self_accumulated_observation_count=len(self_observations),
                reference_observation_count=len(reference_observations),
            )
        if len(self_instruments) > 1 or len(reference_instruments) > 1:
            return _blocked_result(
                status=OverlapValidationStatus.BLOCKED_UNSUPPORTED_SCHEMA,
                verdict=OverlapValidationVerdict.NOT_EXECUTABLE,
                self_accumulated_source_ref=self_ref,
                external_reference_source_ref=external_ref,
                config=cfg,
                reason_codes=("MULTIPLE_INSTRUMENTS_NOT_SUPPORTED_IN_V0",),
                self_accumulated_observation_count=len(self_observations),
                reference_observation_count=len(reference_observations),
            )

    resolved_instrument_id = instrument_id
    if resolved_instrument_id is None and self_observations:
        resolved_instrument_id = self_observations[0]["instrument_id"]
    elif resolved_instrument_id is None and reference_observations:
        resolved_instrument_id = reference_observations[0]["instrument_id"]

    max_delta_ms = cfg.maximum_timestamp_delta_seconds * 1000
    absolute_tolerance = float(cfg.absolute_tolerance)
    relative_tolerance = float(cfg.relative_tolerance)

    reference_by_ts = {o["venue_timestamp_ms"]: o for o in reference_observations}
    self_by_ts = {o["venue_timestamp_ms"]: o for o in self_observations}

    aligned_pairs: list[tuple[dict[str, Any], dict[str, Any]]] = []
    missing_reference_count = 0
    missing_self_accumulated_count = 0

    for self_obs in self_observations:
        exact = reference_by_ts.get(self_obs["venue_timestamp_ms"])
        if exact is not None:
            aligned_pairs.append((self_obs, exact))
            continue
        if cfg.timestamp_alignment_policy == TIMESTAMP_ALIGNMENT_POLICY_EXACT:
            missing_reference_count += 1
            continue
        nearest: dict[str, Any] | None = None
        nearest_delta: int | None = None
        for ref_obs in reference_observations:
            delta = abs(self_obs["venue_timestamp_ms"] - ref_obs["venue_timestamp_ms"])
            if delta <= max_delta_ms and (nearest_delta is None or delta < nearest_delta):
                nearest = ref_obs
                nearest_delta = delta
        if nearest is None:
            missing_reference_count += 1
        else:
            aligned_pairs.append((self_obs, nearest))

    matched_self_ts = {pair[0]["venue_timestamp_ms"] for pair in aligned_pairs}
    for ref_obs in reference_observations:
        if (
            ref_obs["venue_timestamp_ms"] not in matched_self_ts
            and ref_obs["venue_timestamp_ms"] not in self_by_ts
        ):
            missing_self_accumulated_count += 1

    aligned_pair_count = len(aligned_pairs)
    matched_pair_count = 0
    mismatched_pair_count = 0
    for self_obs, ref_obs in aligned_pairs:
        if _values_match_v0(
            self_value=self_obs["open_interest_value"],
            reference_value=ref_obs["open_interest_value"],
            absolute_tolerance=absolute_tolerance,
            relative_tolerance=relative_tolerance,
        ):
            matched_pair_count += 1
        else:
            mismatched_pair_count += 1

    if aligned_pair_count == 0:
        return _blocked_result(
            status=OverlapValidationStatus.BLOCKED_TIMESTAMP_ALIGNMENT,
            verdict=OverlapValidationVerdict.NOT_EXECUTABLE,
            self_accumulated_source_ref=self_ref,
            external_reference_source_ref=external_ref,
            config=cfg,
            reason_codes=("NO_ALIGNED_PAIRS",),
            instrument_id=resolved_instrument_id,
            requested_start_utc=requested_start_utc,
            requested_end_utc=requested_end_utc,
            self_accumulated_observation_count=len(self_observations),
            reference_observation_count=len(reference_observations),
            missing_reference_count=missing_reference_count,
            missing_self_accumulated_count=missing_self_accumulated_count,
            timestamp_alignment_status=TimestampAlignmentStatus.BLOCKED,
            value_comparison_status=ValueComparisonStatus.INSUFFICIENT_PAIRS,
        )

    timestamp_alignment_status = TimestampAlignmentStatus.ALIGNED
    if missing_reference_count or missing_self_accumulated_count:
        timestamp_alignment_status = TimestampAlignmentStatus.PARTIAL

    if aligned_pair_count < cfg.minimum_aligned_pairs:
        return _blocked_result(
            status=OverlapValidationStatus.INSUFFICIENT_DATA,
            verdict=OverlapValidationVerdict.INSUFFICIENT_DATA,
            self_accumulated_source_ref=self_ref,
            external_reference_source_ref=external_ref,
            config=cfg,
            reason_codes=("INSUFFICIENT_ALIGNED_PAIRS",),
            instrument_id=resolved_instrument_id,
            requested_start_utc=requested_start_utc,
            requested_end_utc=requested_end_utc,
            self_accumulated_observation_count=len(self_observations),
            reference_observation_count=len(reference_observations),
            aligned_pair_count=aligned_pair_count,
            matched_pair_count=matched_pair_count,
            mismatched_pair_count=mismatched_pair_count,
            missing_reference_count=missing_reference_count,
            missing_self_accumulated_count=missing_self_accumulated_count,
            timestamp_alignment_status=timestamp_alignment_status,
            value_comparison_status=ValueComparisonStatus.INSUFFICIENT_PAIRS,
        )

    value_comparison_status = (
        ValueComparisonStatus.ALL_MATCHED
        if mismatched_pair_count == 0
        else ValueComparisonStatus.MISMATCH_PRESENT
    )
    status = (
        OverlapValidationStatus.PASS if mismatched_pair_count == 0 else OverlapValidationStatus.FAIL
    )
    verdict = (
        OverlapValidationVerdict.PASS
        if mismatched_pair_count == 0
        else OverlapValidationVerdict.FAIL
    )
    reason_codes: tuple[str, ...] = ()
    if missing_reference_count:
        reason_codes += ("MISSING_REFERENCE_TIMESTAMP",)
    if missing_self_accumulated_count:
        reason_codes += ("MISSING_SELF_ACCUMULATED_TIMESTAMP",)

    payload = {
        "schema_version": MODULE_VERSION,
        "self_accumulated_source_ref": self_ref,
        "external_reference_source_ref": external_ref,
        "instrument_id": resolved_instrument_id,
        "requested_start_utc": requested_start_utc,
        "requested_end_utc": requested_end_utc,
        "self_accumulated_observation_count": len(self_observations),
        "reference_observation_count": len(reference_observations),
        "aligned_pair_count": aligned_pair_count,
        "matched_pair_count": matched_pair_count,
        "mismatched_pair_count": mismatched_pair_count,
        "missing_reference_count": missing_reference_count,
        "missing_self_accumulated_count": missing_self_accumulated_count,
        "timestamp_alignment_status": timestamp_alignment_status.value,
        "value_comparison_status": value_comparison_status.value,
        "absolute_tolerance": cfg.absolute_tolerance,
        "relative_tolerance": cfg.relative_tolerance,
        "status": status.value,
        "verdict": verdict.value,
        "reason_codes": list(reason_codes),
        "authority_effect": AUTHORITY_EFFECT,
        "runtime_effect": RUNTIME_EFFECT,
    }
    validation_id = _compute_validation_id(payload)
    return OverlapValidationResultV0(validation_id=validation_id, **payload)


def overlap_validation_result_to_dict_v0(result: OverlapValidationResultV0) -> dict[str, Any]:
    return {
        "schema_version": result.schema_version,
        "validation_id": result.validation_id,
        "self_accumulated_source_ref": result.self_accumulated_source_ref,
        "external_reference_source_ref": result.external_reference_source_ref,
        "instrument_id": result.instrument_id,
        "requested_start_utc": result.requested_start_utc,
        "requested_end_utc": result.requested_end_utc,
        "self_accumulated_observation_count": result.self_accumulated_observation_count,
        "reference_observation_count": result.reference_observation_count,
        "aligned_pair_count": result.aligned_pair_count,
        "matched_pair_count": result.matched_pair_count,
        "mismatched_pair_count": result.mismatched_pair_count,
        "missing_reference_count": result.missing_reference_count,
        "missing_self_accumulated_count": result.missing_self_accumulated_count,
        "timestamp_alignment_status": result.timestamp_alignment_status,
        "value_comparison_status": result.value_comparison_status,
        "absolute_tolerance": result.absolute_tolerance,
        "relative_tolerance": result.relative_tolerance,
        "status": result.status,
        "verdict": result.verdict,
        "reason_codes": list(result.reason_codes),
        "authority_effect": result.authority_effect,
        "runtime_effect": result.runtime_effect,
        "research_scope": RESEARCH_SCOPE,
        "module_version": MODULE_VERSION,
        "config_schema_version": load_versioned_config_v0().schema_version,
    }


def exit_code_for_overlap_validation_result_v0(result: OverlapValidationResultV0) -> int:
    if result.status in {
        OverlapValidationStatus.PASS.value,
        OverlapValidationStatus.INSUFFICIENT_DATA.value,
    }:
        return 0
    return 2
