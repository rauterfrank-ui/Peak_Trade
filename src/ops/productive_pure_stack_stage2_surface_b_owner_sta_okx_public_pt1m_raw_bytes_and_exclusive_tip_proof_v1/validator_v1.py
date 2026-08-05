"""Fail-closed validator for OKX public PT1M raw-bytes + exclusive-tip proof v1.

Authorized STA download / digest / numeric tip proof only. Does not flip pack
materialization, campaign start, partition fill, input authority, or runtime.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from src.ops.productive_pure_stack_stage2_surface_b_owner_sta_okx_public_pt1m_raw_bytes_and_exclusive_tip_proof_v1 import (
    constants_v1 as C,
)


class OkxPublicPt1mRawBytesExclusiveTipProofErrorV1(ValueError):
    """Fail-closed OKX public PT1M raw-bytes / exclusive-tip proof error."""


def _require_mapping(raw: Any, *, label: str) -> Mapping[str, Any]:
    if not isinstance(raw, Mapping):
        raise OkxPublicPt1mRawBytesExclusiveTipProofErrorV1(f"MAPPING_REQUIRED:{label}")
    return raw


def _assert_false(value: Any, *, label: str) -> None:
    if value is True:
        raise OkxPublicPt1mRawBytesExclusiveTipProofErrorV1(f"MUST_REMAIN_FALSE:{label}")
    if value not in (False, None):
        if bool(value):
            raise OkxPublicPt1mRawBytesExclusiveTipProofErrorV1(f"MUST_REMAIN_FALSE:{label}")


def _assert_null(value: Any, *, label: str) -> None:
    if value is not None:
        raise OkxPublicPt1mRawBytesExclusiveTipProofErrorV1(f"MUST_REMAIN_NULL:{label}")


def _assert_exact(value: Any, expected: Any, *, label: str) -> None:
    if value != expected:
        raise OkxPublicPt1mRawBytesExclusiveTipProofErrorV1(f"VALUE_MISMATCH:{label}")


def _require_int(value: Any, *, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise OkxPublicPt1mRawBytesExclusiveTipProofErrorV1(f"INT_REQUIRED:{label}")
    return int(value)


def _assert_pt1m_aligned(epoch_s: int, *, label: str) -> None:
    if epoch_s % C.BAR_INTERVAL_SECONDS != 0:
        raise OkxPublicPt1mRawBytesExclusiveTipProofErrorV1(f"PT1M_ALIGNMENT_FAILED:{label}")


def _assert_sha256_hex(value: Any, *, label: str) -> str:
    if not isinstance(value, str) or len(value) != 64:
        raise OkxPublicPt1mRawBytesExclusiveTipProofErrorV1(f"SHA256_HEX_REQUIRED:{label}")
    try:
        int(value, 16)
    except ValueError as exc:
        raise OkxPublicPt1mRawBytesExclusiveTipProofErrorV1(f"SHA256_HEX_REQUIRED:{label}") from exc
    return value


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def okx_row_is_finalized_v1(row: Sequence[Any]) -> bool:
    """Map OKX candle/mark confirm field to venue_finalized (confirm == '1')."""
    if not isinstance(row, Sequence) or isinstance(row, (str, bytes)):
        return False
    if len(row) >= 9:
        return str(row[8]) == "1"
    if len(row) >= 6:
        return str(row[5]) == "1"
    return False


def derive_exclusive_tip_from_last_common_bucket_open_v1(
    last_finalized_common_bucket_open_event_time_epoch_s: int,
) -> int:
    last_open = _require_int(
        last_finalized_common_bucket_open_event_time_epoch_s,
        label="last_finalized_common_bucket_open_event_time_epoch_s",
    )
    _assert_pt1m_aligned(last_open, label="last_finalized_common_bucket_open_event_time_epoch_s")
    tip = last_open + C.EXCLUSIVE_TIP_OFFSET_SECONDS
    _assert_pt1m_aligned(tip, label="exclusive_tip_event_time_epoch_s")
    return tip


def compose_raw_source_bytes_v1(*, candle_raw_bytes: bytes, mark_raw_bytes: bytes) -> bytes:
    return b"CANDLE\n" + candle_raw_bytes + b"\nMARK\n" + mark_raw_bytes


def parse_okx_finalized_pt1m_bucket_opens_v1(
    raw_http_response_bytes: bytes,
    *,
    series_label: str,
) -> list[int]:
    try:
        payload = json.loads(raw_http_response_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise OkxPublicPt1mRawBytesExclusiveTipProofErrorV1(
            f"RAW_JSON_PARSE_FAILED:{series_label}"
        ) from exc
    if not isinstance(payload, Mapping):
        raise OkxPublicPt1mRawBytesExclusiveTipProofErrorV1(
            f"RAW_JSON_OBJECT_REQUIRED:{series_label}"
        )
    if str(payload.get("code")) != "0":
        raise OkxPublicPt1mRawBytesExclusiveTipProofErrorV1(f"OKX_CODE_NOT_ZERO:{series_label}")
    rows = payload.get("data")
    if not isinstance(rows, list):
        raise OkxPublicPt1mRawBytesExclusiveTipProofErrorV1(f"DATA_LIST_REQUIRED:{series_label}")

    times: list[int] = []
    seen: set[int] = set()
    for index, row in enumerate(rows):
        if not isinstance(row, list) or not row:
            raise OkxPublicPt1mRawBytesExclusiveTipProofErrorV1(
                f"ROW_SHAPE_INVALID:{series_label}[{index}]"
            )
        try:
            ts_ms = int(str(row[0]))
        except (TypeError, ValueError) as exc:
            raise OkxPublicPt1mRawBytesExclusiveTipProofErrorV1(
                f"TS_MS_INVALID:{series_label}[{index}]"
            ) from exc
        if ts_ms % 1000 != 0:
            raise OkxPublicPt1mRawBytesExclusiveTipProofErrorV1(
                f"TS_MS_NOT_WHOLE_SECOND:{series_label}[{index}]"
            )
        et = ts_ms // 1000
        _assert_pt1m_aligned(et, label=f"{series_label}[{index}].event_time_epoch_s")
        if not okx_row_is_finalized_v1(row):
            continue
        if et in seen:
            raise OkxPublicPt1mRawBytesExclusiveTipProofErrorV1(
                f"DUPLICATE_EVENT_TIME:{series_label}:{et}"
            )
        seen.add(et)
        times.append(et)
    times.sort()
    previous: int | None = None
    for et in times:
        if previous is not None:
            if et <= previous:
                raise OkxPublicPt1mRawBytesExclusiveTipProofErrorV1(
                    f"NON_MONOTONIC_EVENT_TIME:{series_label}:{et}"
                )
            if et - previous != C.BAR_INTERVAL_SECONDS:
                raise OkxPublicPt1mRawBytesExclusiveTipProofErrorV1(
                    f"CONTIGUITY_GAP:{series_label}:{previous}->{et}"
                )
        previous = et
    if not times:
        raise OkxPublicPt1mRawBytesExclusiveTipProofErrorV1(f"NO_FINALIZED_ROWS:{series_label}")
    return times


def evaluate_okx_public_pt1m_raw_bytes_and_exclusive_tip_proof_v1(
    *,
    candle_raw_bytes: bytes,
    mark_raw_bytes: bytes,
    binding_raw: Mapping[str, Any],
    authorized_network_fetch: bool,
) -> dict[str, Any]:
    if not authorized_network_fetch:
        raise OkxPublicPt1mRawBytesExclusiveTipProofErrorV1("AUTHORIZED_NETWORK_FETCH_REQUIRED")

    binding = _require_mapping(binding_raw, label="instrument_binding")
    for field in C.INSTRUMENT_BINDING_FIELDS:
        _assert_exact(
            binding.get(field),
            C.REQUIRED_INSTRUMENT_BINDING_V1[field],
            label=f"instrument_binding.{field}",
        )

    candle_times = parse_okx_finalized_pt1m_bucket_opens_v1(
        candle_raw_bytes, series_label="candles"
    )
    mark_times = parse_okx_finalized_pt1m_bucket_opens_v1(mark_raw_bytes, series_label="marks")
    if candle_times != mark_times:
        raise OkxPublicPt1mRawBytesExclusiveTipProofErrorV1("CANDLE_MARK_BUCKET_JOIN_FAILED")

    first_open = candle_times[0]
    last_open = candle_times[-1]
    exclusive_tip = derive_exclusive_tip_from_last_common_bucket_open_v1(last_open)
    if any(t >= exclusive_tip for t in candle_times):
        raise OkxPublicPt1mRawBytesExclusiveTipProofErrorV1(
            "BAR_AFTER_AS_OF_OR_OPEN_BUCKET_PRESENT"
        )

    candle_digest = _sha256_bytes(candle_raw_bytes)
    mark_digest = _sha256_bytes(mark_raw_bytes)
    raw_source_bytes = compose_raw_source_bytes_v1(
        candle_raw_bytes=candle_raw_bytes,
        mark_raw_bytes=mark_raw_bytes,
    )
    raw_source_digest = _sha256_bytes(raw_source_bytes)

    return {
        "ok": True,
        "authorized_source_classification": list(C.AUTHORIZED_SOURCE_CLASSES),
        "authorized_endpoints": [C.CANDLE_ENDPOINT, C.MARK_ENDPOINT],
        "request_parameters": {
            "instId": C.REQUIRED_INSTRUMENT_BINDING_V1["venue_instrument_id"],
            "bar": "1m",
            "limit": C.CANONICAL_PAGE_LIMIT,
        },
        "request_window_source": C.REQUEST_WINDOW_SOURCE,
        "candle_raw_byte_count": len(candle_raw_bytes),
        "mark_raw_byte_count": len(mark_raw_bytes),
        "candle_raw_digest": candle_digest,
        "mark_raw_digest": mark_digest,
        "raw_source_digest": raw_source_digest,
        "candle_row_count": len(candle_times),
        "mark_row_count": len(mark_times),
        "first_finalized_common_bucket_open_event_time_epoch_s": first_open,
        "last_finalized_common_bucket_open_event_time_epoch_s": last_open,
        "exclusive_tip_event_time_epoch_s": exclusive_tip,
        "pt1m_alignment_proof": True,
        "candle_mark_join_proof": True,
        "contiguity_proof": True,
        "duplicate_free_proof": True,
        "monotonicity_proof": True,
        "digest_bound_row_count_proof": True,
        "authorized_observation_window_candidate": {
            "first_finalized_common_bucket_open_event_time_epoch_s": first_open,
            "last_finalized_common_bucket_open_event_time_epoch_s": last_open,
            "exclusive_tip_event_time_epoch_s": exclusive_tip,
            "bar_interval": C.BAR_INTERVAL,
            "row_count": len(candle_times),
            "semantics": "HALF_OPEN_EVENT_TIME_WINDOW_[first_open, exclusive_tip)",
        },
        "sta_external_input_fields_ready": True,
        "owner_partition_selection_ready": False,
        "numeric_proofs_resolved": True,
        "observation_pack_digest": None,
        "pack_materialization": False,
        "raw_input_pack_created": False,
        "campaign_start": False,
        "input_authority": False,
        "runtime_implemented": False,
        "productive_numeric_values_set": 0,
        "dashboard_authority_effect": "NONE",
        "orders_testnet_live": False,
        "wallclock_as_data_authority": False,
    }


def load_canonical_okx_public_pt1m_raw_bytes_tip_proof_manifest_v1(
    repo_root: Path | str | None = None,
) -> dict[str, Any]:
    root = Path(repo_root) if repo_root is not None else Path(__file__).resolve().parents[3]
    path = root / C.DECISIONS_MANIFEST_REL
    if not path.is_file():
        raise OkxPublicPt1mRawBytesExclusiveTipProofErrorV1(
            f"MANIFEST_MISSING:{C.DECISIONS_MANIFEST_REL}"
        )
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise OkxPublicPt1mRawBytesExclusiveTipProofErrorV1("MANIFEST_MUST_BE_OBJECT")
    return payload


def load_sealed_raw_bytes_v1(repo_root: Path | str | None = None) -> tuple[bytes, bytes, bytes]:
    root = Path(repo_root) if repo_root is not None else Path(__file__).resolve().parents[3]
    candle = (root / C.CANDLE_RAW_REL).read_bytes()
    mark = (root / C.MARK_RAW_REL).read_bytes()
    concat = (root / C.RAW_SOURCE_CONCAT_REL).read_bytes()
    expected_concat = compose_raw_source_bytes_v1(candle_raw_bytes=candle, mark_raw_bytes=mark)
    if concat != expected_concat:
        raise OkxPublicPt1mRawBytesExclusiveTipProofErrorV1("RAW_SOURCE_CONCAT_MISMATCH")
    return candle, mark, concat


def validate_okx_public_pt1m_raw_bytes_and_exclusive_tip_proof_manifest_v1(
    manifest: Mapping[str, Any],
    *,
    repo_root: Path | str | None = None,
) -> dict[str, Any]:
    m = _require_mapping(manifest, label="manifest")
    _assert_exact(m.get("schema_version"), C.SCHEMA_VERSION, label="schema_version")
    _assert_exact(m.get("document_type"), C.DOCUMENT_TYPE, label="document_type")
    _assert_exact(m.get("capability_scope"), C.CAPABILITY_SCOPE, label="capability_scope")
    _assert_exact(
        m.get("status"),
        C.STATUS_NUMERIC_TIP_PROOF_RESOLVED,
        label="status",
    )
    _assert_exact(m.get("decision_id"), C.DECISION_ID, label="decision_id")
    _assert_exact(
        m.get("decision_status"),
        C.DECISION_STATUS_RATIFIED,
        label="decision_status",
    )
    _assert_exact(m.get("owner_value"), C.OWNER_VALUE, label="owner_value")
    _assert_exact(m.get("owner_go"), C.OWNER_GO, label="owner_go")
    _assert_exact(
        m.get("owner_go_base_sha"),
        C.OWNER_GO_BASE_SHA,
        label="owner_go_base_sha",
    )
    _assert_exact(m.get("authority_surface"), C.AUTHORITY_SURFACE, label="authority_surface")
    _assert_exact(m.get("scope"), C.SCOPE, label="scope")
    _assert_exact(m.get("bar_interval"), C.BAR_INTERVAL, label="bar_interval")
    _assert_exact(
        m.get("exclusive_tip_formula"),
        C.EXCLUSIVE_TIP_FORMULA,
        label="exclusive_tip_formula",
    )
    _assert_exact(
        m.get("download_or_network_fetch_policy"),
        C.DOWNLOAD_OR_NETWORK_FETCH_POLICY,
        label="download_or_network_fetch_policy",
    )
    _assert_exact(m.get("authorized_network_fetch"), True, label="authorized_network_fetch")
    _assert_exact(m.get("download_or_network_fetch"), True, label="download_or_network_fetch")
    _assert_exact(m.get("proof_contract_ready"), True, label="proof_contract_ready")
    _assert_exact(
        m.get("sta_external_input_fields_ready"),
        True,
        label="sta_external_input_fields_ready",
    )
    _assert_exact(
        m.get("owner_partition_selection_ready"),
        False,
        label="owner_partition_selection_ready",
    )
    _assert_exact(m.get("numeric_proofs_resolved"), True, label="numeric_proofs_resolved")

    binding = _require_mapping(m.get("instrument_binding"), label="instrument_binding")
    for field in C.INSTRUMENT_BINDING_FIELDS:
        _assert_exact(
            binding.get(field),
            C.REQUIRED_INSTRUMENT_BINDING_V1[field],
            label=f"instrument_binding.{field}",
        )

    source_class = _require_mapping(
        m.get("authorized_source_classification"),
        label="authorized_source_classification",
    )
    _assert_exact(
        source_class.get("authorized_source_classes"),
        list(C.AUTHORIZED_SOURCE_CLASSES),
        label="authorized_source_classes",
    )
    _assert_exact(
        source_class.get("forbidden_source_classes"),
        list(C.FORBIDDEN_SOURCE_CLASSES),
        label="forbidden_source_classes",
    )
    _assert_exact(
        source_class.get("candle_authority_source_ref"),
        C.CANDLE_AUTHORITY_SOURCE_REF,
        label="candle_authority_source_ref",
    )
    _assert_exact(
        source_class.get("mark_price_authority_source_ref"),
        C.MARK_AUTHORITY_SOURCE_REF,
        label="mark_price_authority_source_ref",
    )

    fetch = _require_mapping(m.get("authorized_fetch"), label="authorized_fetch")
    _assert_exact(
        fetch.get("candle_endpoint"),
        C.CANDLE_ENDPOINT,
        label="authorized_fetch.candle_endpoint",
    )
    _assert_exact(
        fetch.get("mark_endpoint"),
        C.MARK_ENDPOINT,
        label="authorized_fetch.mark_endpoint",
    )
    _assert_exact(
        fetch.get("page_limit"),
        C.CANONICAL_PAGE_LIMIT,
        label="authorized_fetch.page_limit",
    )
    _assert_exact(
        fetch.get("request_window_source"),
        C.REQUEST_WINDOW_SOURCE,
        label="authorized_fetch.request_window_source",
    )
    _assert_exact(
        fetch.get("wallclock_as_data_authority"),
        False,
        label="authorized_fetch.wallclock_as_data_authority",
    )

    proofs = _require_mapping(m.get("numeric_proof_slots"), label="numeric_proof_slots")
    _assert_exact(
        proofs.get("candle_raw_byte_count"),
        C.SEALED_CANDLE_RAW_BYTE_COUNT,
        label="candle_raw_byte_count",
    )
    _assert_exact(
        proofs.get("mark_raw_byte_count"),
        C.SEALED_MARK_RAW_BYTE_COUNT,
        label="mark_raw_byte_count",
    )
    _assert_exact(
        _assert_sha256_hex(proofs.get("candle_raw_digest"), label="candle_raw_digest"),
        C.SEALED_CANDLE_RAW_DIGEST,
        label="candle_raw_digest",
    )
    _assert_exact(
        _assert_sha256_hex(proofs.get("mark_raw_digest"), label="mark_raw_digest"),
        C.SEALED_MARK_RAW_DIGEST,
        label="mark_raw_digest",
    )
    _assert_exact(
        _assert_sha256_hex(proofs.get("raw_source_digest"), label="raw_source_digest"),
        C.SEALED_RAW_SOURCE_DIGEST,
        label="raw_source_digest",
    )
    _assert_exact(
        proofs.get("candle_row_count"),
        C.SEALED_CANDLE_ROW_COUNT,
        label="candle_row_count",
    )
    _assert_exact(
        proofs.get("mark_row_count"),
        C.SEALED_MARK_ROW_COUNT,
        label="mark_row_count",
    )
    _assert_exact(
        proofs.get("first_finalized_common_bucket_open_event_time_epoch_s"),
        C.SEALED_FIRST_FINALIZED_COMMON_BUCKET_OPEN_EVENT_TIME_EPOCH_S,
        label="first_finalized_common_bucket_open_event_time_epoch_s",
    )
    _assert_exact(
        proofs.get("last_finalized_common_bucket_open_event_time_epoch_s"),
        C.SEALED_LAST_FINALIZED_COMMON_BUCKET_OPEN_EVENT_TIME_EPOCH_S,
        label="last_finalized_common_bucket_open_event_time_epoch_s",
    )
    _assert_exact(
        proofs.get("exclusive_tip_event_time_epoch_s"),
        C.SEALED_EXCLUSIVE_TIP_EVENT_TIME_EPOCH_S,
        label="exclusive_tip_event_time_epoch_s",
    )
    _assert_null(proofs.get("observation_pack_digest"), label="observation_pack_digest")

    rule_proofs = _require_mapping(m.get("rule_proofs"), label="rule_proofs")
    for key in (
        "pt1m_alignment_proof",
        "candle_mark_join_proof",
        "contiguity_proof",
        "duplicate_free_proof",
        "monotonicity_proof",
        "digest_bound_row_count_proof",
        "require_finalized_candles",
        "require_finalized_marks",
        "open_bucket_at_as_of_forbidden",
        "bar_after_as_of_forbidden",
        "derive_exclusive_tip",
        "require_exclusive_tip_pt1m_alignment",
        "authorized_source_only",
    ):
        _assert_exact(rule_proofs.get(key), True, label=f"rule_proofs.{key}")

    unresolved = m.get("unresolved_fields")
    if not isinstance(unresolved, list):
        raise OkxPublicPt1mRawBytesExclusiveTipProofErrorV1("UNRESOLVED_FIELDS_MUST_BE_LIST")
    if unresolved != list(C.UNRESOLVED_FIELDS):
        raise OkxPublicPt1mRawBytesExclusiveTipProofErrorV1("UNRESOLVED_FIELDS_MISMATCH")

    non_effects = _require_mapping(m.get("non_effects"), label="non_effects")
    for key in (
        "pack_materialization",
        "raw_input_pack_created",
        "raw_input_pack_materialization_authorized",
        "campaign_start",
        "input_authority",
        "runtime_implemented",
        "regime_coverage_producer_available",
        "productive_thresholds_lookbacks",
        "trading_logic_change",
        "orders_testnet_live",
        "fill_partition_boundaries",
        "owner_partition_selection",
        "invented_values",
        "silent_defaults",
        "proposed_values",
    ):
        _assert_false(non_effects.get(key), label=f"non_effects.{key}")
    _assert_exact(
        non_effects.get("productive_numeric_values_set"),
        0,
        label="non_effects.productive_numeric_values_set",
    )
    _assert_exact(
        non_effects.get("dashboard_authority_effect"),
        "NONE",
        label="non_effects.dashboard_authority_effect",
    )

    candle_bytes, mark_bytes, _concat = load_sealed_raw_bytes_v1(repo_root)
    evaluated = evaluate_okx_public_pt1m_raw_bytes_and_exclusive_tip_proof_v1(
        candle_raw_bytes=candle_bytes,
        mark_raw_bytes=mark_bytes,
        binding_raw=binding,
        authorized_network_fetch=True,
    )
    for key, expected in (
        ("candle_raw_digest", C.SEALED_CANDLE_RAW_DIGEST),
        ("mark_raw_digest", C.SEALED_MARK_RAW_DIGEST),
        ("raw_source_digest", C.SEALED_RAW_SOURCE_DIGEST),
        ("candle_row_count", C.SEALED_CANDLE_ROW_COUNT),
        ("mark_row_count", C.SEALED_MARK_ROW_COUNT),
        (
            "first_finalized_common_bucket_open_event_time_epoch_s",
            C.SEALED_FIRST_FINALIZED_COMMON_BUCKET_OPEN_EVENT_TIME_EPOCH_S,
        ),
        (
            "last_finalized_common_bucket_open_event_time_epoch_s",
            C.SEALED_LAST_FINALIZED_COMMON_BUCKET_OPEN_EVENT_TIME_EPOCH_S,
        ),
        ("exclusive_tip_event_time_epoch_s", C.SEALED_EXCLUSIVE_TIP_EVENT_TIME_EPOCH_S),
    ):
        _assert_exact(evaluated.get(key), expected, label=f"sealed_eval.{key}")

    return {
        "ok": True,
        "decision_id": C.DECISION_ID,
        "owner_go": C.OWNER_GO,
        "status": C.STATUS_NUMERIC_TIP_PROOF_RESOLVED,
        "sta_external_input_fields_ready": True,
        "owner_partition_selection_ready": False,
        "numeric_proofs_resolved": True,
        "exclusive_tip_event_time_epoch_s": C.SEALED_EXCLUSIVE_TIP_EVENT_TIME_EPOCH_S,
        "raw_source_digest": C.SEALED_RAW_SOURCE_DIGEST,
        "unresolved_fields": list(C.UNRESOLVED_FIELDS),
        "pack_materialization": False,
        "raw_input_pack_created": False,
        "campaign_start": False,
        "input_authority": False,
        "runtime_implemented": False,
        "productive_numeric_values_set": 0,
        "dashboard_authority_effect": "NONE",
        "authorized_network_fetch": True,
    }
