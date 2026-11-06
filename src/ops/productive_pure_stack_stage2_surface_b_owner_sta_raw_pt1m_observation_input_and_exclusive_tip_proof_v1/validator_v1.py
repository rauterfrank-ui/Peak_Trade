"""Fail-closed validator for raw PT1M observation-input + exclusive-tip proof v1.

Publishes the STA proof contract under DEC_RAW_INPUT_PACK_MATERIALIZATION.
Does not authorize download/network fetch, pack materialization, campaign start,
partition fill, input-authority/runtime flips, or productive numeric values.
Canonical numeric proof slots must remain null until a separate STA-authorized
fetch/pack tip proof supplies venue-native finalized PT1M rows.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from src.ops.productive_pure_stack_stage2_surface_b_owner_sta_raw_pt1m_observation_input_and_exclusive_tip_proof_v1 import (
    constants_v1 as C,
)


class ObservationInputExclusiveTipProofErrorV1(ValueError):
    """Fail-closed observation-input / exclusive-tip proof error."""


def _require_mapping(raw: Any, *, label: str) -> Mapping[str, Any]:
    if not isinstance(raw, Mapping):
        raise ObservationInputExclusiveTipProofErrorV1(f"MAPPING_REQUIRED:{label}")
    return raw


def _assert_false(value: Any, *, label: str) -> None:
    if value is True:
        raise ObservationInputExclusiveTipProofErrorV1(f"MUST_REMAIN_FALSE:{label}")
    if value not in (False, None):
        if bool(value):
            raise ObservationInputExclusiveTipProofErrorV1(f"MUST_REMAIN_FALSE:{label}")


def _assert_null(value: Any, *, label: str) -> None:
    if value is not None:
        raise ObservationInputExclusiveTipProofErrorV1(f"MUST_REMAIN_NULL:{label}")


def _assert_exact(value: Any, expected: Any, *, label: str) -> None:
    if value != expected:
        raise ObservationInputExclusiveTipProofErrorV1(f"VALUE_MISMATCH:{label}")


def _assert_no_forbidden_source_token(value: Any, *, label: str) -> None:
    if value is None:
        return
    text = str(value).strip().lower()
    if not text:
        return
    for forbidden in C.FORBIDDEN_SOURCE_TOKENS:
        if forbidden.lower() in text:
            raise ObservationInputExclusiveTipProofErrorV1(f"FORBIDDEN_SOURCE:{forbidden}:{label}")


def _require_int(value: Any, *, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ObservationInputExclusiveTipProofErrorV1(f"INT_REQUIRED:{label}")
    return int(value)


def _assert_pt1m_aligned(epoch_s: int, *, label: str) -> None:
    if epoch_s % C.BAR_INTERVAL_SECONDS != 0:
        raise ObservationInputExclusiveTipProofErrorV1(f"PT1M_ALIGNMENT_FAILED:{label}")


def derive_exclusive_tip_event_time_epoch_s_v1(
    last_finalized_bar_open_event_time_epoch_s: int,
) -> int:
    """Derive exclusive tip: last finalized PT1M bucket-open + 60s."""
    last_open = _require_int(
        last_finalized_bar_open_event_time_epoch_s,
        label="last_finalized_bar_open_event_time_epoch_s",
    )
    _assert_pt1m_aligned(last_open, label="last_finalized_bar_open_event_time_epoch_s")
    tip = last_open + C.EXCLUSIVE_TIP_OFFSET_SECONDS
    _assert_pt1m_aligned(tip, label="exclusive_tip_event_time_epoch_s")
    return tip


def evaluate_observation_input_and_exclusive_tip_proof_v1(
    *,
    binding_raw: Mapping[str, Any],
    candle_rows: Sequence[Mapping[str, Any]],
    mark_rows: Sequence[Mapping[str, Any]],
    candle_source_ref: str,
    mark_source_ref: str,
    download_or_network_fetch_authorized: bool,
    observation_pack_bytes: bytes | None = None,
    raw_source_bytes: bytes | None = None,
) -> dict[str, Any]:
    """Evaluate tip/contiguity/join proofs from explicit venue-native rows.

    Requires an explicit download/fetch authorization flag. Does not flip
    pack materialization, campaign start, or input authority.
    """
    if not download_or_network_fetch_authorized:
        raise ObservationInputExclusiveTipProofErrorV1("DOWNLOAD_OR_NETWORK_FETCH_NOT_AUTHORIZED")
    _assert_exact(
        candle_source_ref,
        C.CANDLE_AUTHORITY_SOURCE_REF,
        label="candle_source_ref",
    )
    _assert_exact(
        mark_source_ref,
        C.MARK_AUTHORITY_SOURCE_REF,
        label="mark_source_ref",
    )
    _assert_no_forbidden_source_token(candle_source_ref, label="candle_source_ref")
    _assert_no_forbidden_source_token(mark_source_ref, label="mark_source_ref")

    binding = _require_mapping(binding_raw, label="instrument_binding")
    for field in C.INSTRUMENT_BINDING_FIELDS:
        if field not in binding:
            raise ObservationInputExclusiveTipProofErrorV1(
                f"INSTRUMENT_BINDING_FIELD_MISSING:{field}"
            )
        _assert_exact(
            binding[field],
            C.REQUIRED_INSTRUMENT_BINDING_V1[field],
            label=f"instrument_binding.{field}",
        )

    if not isinstance(candle_rows, Sequence) or isinstance(candle_rows, (str, bytes)):
        raise ObservationInputExclusiveTipProofErrorV1("CANDLE_ROWS_MUST_BE_SEQUENCE")
    if not isinstance(mark_rows, Sequence) or isinstance(mark_rows, (str, bytes)):
        raise ObservationInputExclusiveTipProofErrorV1("MARK_ROWS_MUST_BE_SEQUENCE")
    if not candle_rows:
        raise ObservationInputExclusiveTipProofErrorV1("CANDLE_ROWS_REQUIRED")
    if not mark_rows:
        raise ObservationInputExclusiveTipProofErrorV1("MARK_ROWS_REQUIRED")

    candle_times = _validate_finalized_event_time_series(candle_rows, series_label="candles")
    mark_times = _validate_finalized_event_time_series(mark_rows, series_label="marks")
    if candle_times != mark_times:
        raise ObservationInputExclusiveTipProofErrorV1("CANDLE_MARK_BUCKET_JOIN_FAILED")

    first_open = candle_times[0]
    last_open = candle_times[-1]
    exclusive_tip = derive_exclusive_tip_event_time_epoch_s_v1(last_open)

    observation_pack_digest = None
    raw_source_digest = None
    if observation_pack_bytes is not None:
        observation_pack_digest = hashlib.sha256(observation_pack_bytes).hexdigest()
    if raw_source_bytes is not None:
        raw_source_digest = hashlib.sha256(raw_source_bytes).hexdigest()

    return {
        "ok": True,
        "authorized_source_classification": list(C.AUTHORIZED_SOURCE_CLASSES),
        "candle_row_count": len(candle_times),
        "mark_row_count": len(mark_times),
        "first_finalized_bucket_open_event_time_epoch_s": first_open,
        "last_finalized_bucket_open_event_time_epoch_s": last_open,
        "exclusive_tip_event_time_epoch_s": exclusive_tip,
        "pt1m_alignment_proof": True,
        "candle_mark_join_proof": True,
        "contiguity_proof": True,
        "duplicate_free_proof": True,
        "observation_pack_digest": observation_pack_digest,
        "raw_source_digest": raw_source_digest,
        "digest_provenance": {
            "observation_pack_digest_from_bytes": observation_pack_bytes is not None,
            "raw_source_digest_from_bytes": raw_source_bytes is not None,
        },
        "pack_materialization": False,
        "raw_input_pack_created": False,
        "campaign_start": False,
        "input_authority": False,
        "runtime_implemented": False,
        "productive_numeric_values_set": 0,
        "dashboard_authority_effect": "NONE",
        "orders_testnet_live": False,
    }


def _validate_finalized_event_time_series(
    rows: Sequence[Mapping[str, Any]],
    *,
    series_label: str,
) -> list[int]:
    times: list[int] = []
    seen: set[int] = set()
    previous: int | None = None
    for index, raw in enumerate(rows):
        row = _require_mapping(raw, label=f"{series_label}[{index}]")
        for forbidden_key in ("dashboard", "fixture", "demo", "synthetic", "notion"):
            if forbidden_key in {str(k).lower() for k in row}:
                raise ObservationInputExclusiveTipProofErrorV1(
                    f"FORBIDDEN_SOURCE_KEY:{forbidden_key}:{series_label}[{index}]"
                )
        et = _require_int(
            row.get("event_time_epoch_s"),
            label=f"{series_label}[{index}].event_time_epoch_s",
        )
        _assert_pt1m_aligned(et, label=f"{series_label}[{index}].event_time_epoch_s")
        if row.get("finalized") is not True and row.get("confirm") not in (1, "1", True):
            raise ObservationInputExclusiveTipProofErrorV1(
                f"FINALIZED_REQUIRED:{series_label}[{index}]"
            )
        binding = row.get("instrument_binding")
        if binding is not None:
            binding_map = _require_mapping(
                binding, label=f"{series_label}[{index}].instrument_binding"
            )
            for field in C.INSTRUMENT_BINDING_FIELDS:
                _assert_exact(
                    binding_map.get(field),
                    C.REQUIRED_INSTRUMENT_BINDING_V1[field],
                    label=f"{series_label}[{index}].instrument_binding.{field}",
                )
        if et in seen:
            raise ObservationInputExclusiveTipProofErrorV1(
                f"DUPLICATE_EVENT_TIME:{series_label}:{et}"
            )
        seen.add(et)
        if previous is not None:
            if et <= previous:
                raise ObservationInputExclusiveTipProofErrorV1(
                    f"NON_MONOTONIC_EVENT_TIME:{series_label}:{et}"
                )
            if et - previous != C.BAR_INTERVAL_SECONDS:
                raise ObservationInputExclusiveTipProofErrorV1(
                    f"CONTIGUITY_GAP:{series_label}:{previous}->{et}"
                )
        previous = et
        times.append(et)
    return times


def load_canonical_observation_input_and_exclusive_tip_proof_manifest_v1(
    repo_root: Path | str | None = None,
) -> dict[str, Any]:
    root = Path(repo_root) if repo_root is not None else Path(__file__).resolve().parents[3]
    path = root / C.DECISIONS_MANIFEST_REL
    if not path.is_file():
        raise ObservationInputExclusiveTipProofErrorV1(
            f"MANIFEST_MISSING:{C.DECISIONS_MANIFEST_REL}"
        )
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ObservationInputExclusiveTipProofErrorV1("MANIFEST_MUST_BE_OBJECT")
    return payload


def validate_observation_input_and_exclusive_tip_proof_manifest_v1(
    manifest: Mapping[str, Any],
) -> dict[str, Any]:
    """Validate the canonical proof-contract manifest fail-closed."""
    m = _require_mapping(manifest, label="manifest")
    _assert_exact(m.get("schema_version"), C.SCHEMA_VERSION, label="schema_version")
    _assert_exact(m.get("document_type"), C.DOCUMENT_TYPE, label="document_type")
    _assert_exact(m.get("capability_scope"), C.CAPABILITY_SCOPE, label="capability_scope")
    _assert_exact(
        m.get("status"),
        C.STATUS_PROOF_CONTRACT_READY_NUMERIC_UNRESOLVED,
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
        m.get("candle_event_time_semantics"),
        C.CANDLE_EVENT_TIME_SEMANTICS,
        label="candle_event_time_semantics",
    )
    _assert_exact(
        m.get("mark_event_time_semantics"),
        C.MARK_EVENT_TIME_SEMANTICS,
        label="mark_event_time_semantics",
    )
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
    _assert_false(m.get("download_or_network_fetch"), label="download_or_network_fetch")
    _assert_exact(m.get("proof_contract_ready"), True, label="proof_contract_ready")
    _assert_exact(
        m.get("sta_external_input_fields_ready"),
        False,
        label="sta_external_input_fields_ready",
    )
    _assert_exact(
        m.get("owner_partition_selection_ready"),
        False,
        label="owner_partition_selection_ready",
    )
    _assert_exact(
        m.get("numeric_proofs_resolved"),
        False,
        label="numeric_proofs_resolved",
    )

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
    _assert_no_forbidden_source_token(
        source_class.get("candle_authority_source_ref"),
        label="candle_authority_source_ref",
    )
    _assert_no_forbidden_source_token(
        source_class.get("mark_price_authority_source_ref"),
        label="mark_price_authority_source_ref",
    )

    proofs = _require_mapping(m.get("numeric_proof_slots"), label="numeric_proof_slots")
    for field in C.NUMERIC_PROOF_NULL_FIELDS:
        if field not in proofs:
            raise ObservationInputExclusiveTipProofErrorV1(f"NUMERIC_PROOF_SLOT_MISSING:{field}")
        _assert_null(proofs.get(field), label=f"numeric_proof_slots.{field}")

    rule_proofs = _require_mapping(m.get("rule_proofs"), label="rule_proofs")
    for key, expected in (
        ("require_finalized_candles", True),
        ("require_finalized_marks", True),
        ("require_candle_mark_bucket_join", True),
        ("open_bucket_at_as_of_forbidden", True),
        ("bar_after_as_of_forbidden", True),
        ("derive_exclusive_tip", True),
        ("require_exclusive_tip_pt1m_alignment", True),
        ("require_observation_pack_digest", True),
        ("require_raw_source_digest", True),
        ("require_digest_bound_row_counts", True),
        ("require_first_and_last_event_time_proof", True),
        ("require_contiguity_proof", True),
        ("require_duplicate_free_event_time_keys", True),
        ("require_monotonic_event_time", True),
        ("require_instrument_consistency", True),
        ("authorized_source_only", True),
        ("pt1m_alignment_rules_proven", True),
        ("candle_mark_join_rules_proven", True),
        ("contiguity_rules_proven", True),
        ("duplicate_free_rules_proven", True),
        ("pt1m_alignment_concrete_epoch_proof", False),
        ("candle_mark_join_concrete_proof", False),
        ("contiguity_concrete_proof", False),
        ("duplicate_free_concrete_proof", False),
    ):
        _assert_exact(rule_proofs.get(key), expected, label=f"rule_proofs.{key}")

    unresolved = m.get("unresolved_fields")
    if not isinstance(unresolved, list):
        raise ObservationInputExclusiveTipProofErrorV1("UNRESOLVED_FIELDS_MUST_BE_LIST")
    if unresolved != list(C.UNRESOLVED_FIELDS):
        raise ObservationInputExclusiveTipProofErrorV1("UNRESOLVED_FIELDS_MISMATCH")

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
        "download_or_network_fetch",
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

    digest_provenance = _require_mapping(m.get("digest_provenance"), label="digest_provenance")
    _assert_exact(
        digest_provenance.get("status"),
        "UNRESOLVED_NO_AUTHORIZED_PACK_OR_RAW_BYTES",
        label="digest_provenance.status",
    )
    _assert_null(
        digest_provenance.get("observation_pack_digest"),
        label="digest_provenance.observation_pack_digest",
    )
    _assert_null(
        digest_provenance.get("raw_source_digest"),
        label="digest_provenance.raw_source_digest",
    )

    return {
        "ok": True,
        "decision_id": C.DECISION_ID,
        "owner_go": C.OWNER_GO,
        "owner_value": C.OWNER_VALUE,
        "status": C.STATUS_PROOF_CONTRACT_READY_NUMERIC_UNRESOLVED,
        "proof_contract_ready": True,
        "sta_external_input_fields_ready": False,
        "owner_partition_selection_ready": False,
        "numeric_proofs_resolved": False,
        "unresolved_fields": list(C.UNRESOLVED_FIELDS),
        "pack_materialization": False,
        "raw_input_pack_created": False,
        "campaign_start": False,
        "input_authority": False,
        "runtime_implemented": False,
        "productive_numeric_values_set": 0,
        "dashboard_authority_effect": "NONE",
        "download_or_network_fetch": False,
    }
