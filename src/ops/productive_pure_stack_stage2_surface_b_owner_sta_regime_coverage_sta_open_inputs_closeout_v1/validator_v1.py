"""Fail-closed validator for regime-coverage STA open-inputs closeout v1.

Closes non_invented_coverage_counts and provable_eth_usdt_swap_compatibility
without producer reimplementation, consumer wiring, pack materialization,
campaign start, input-authority/runtime flips, or productive thresholds.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from src.ops.productive_pure_stack_stage2_surface_b_owner_sta_regime_coverage_sta_open_inputs_closeout_v1 import (
    constants_v1 as C,
)


class RegimeCoverageStaOpenInputsCloseoutErrorV1(ValueError):
    """Fail-closed STA open-inputs closeout error."""


def _require_mapping(raw: Any, *, label: str) -> Mapping[str, Any]:
    if not isinstance(raw, Mapping):
        raise RegimeCoverageStaOpenInputsCloseoutErrorV1(f"MAPPING_REQUIRED:{label}")
    return raw


def _assert_false(value: Any, *, label: str) -> None:
    if value is True:
        raise RegimeCoverageStaOpenInputsCloseoutErrorV1(f"MUST_REMAIN_FALSE:{label}")
    if value not in (False, None):
        if bool(value):
            raise RegimeCoverageStaOpenInputsCloseoutErrorV1(f"MUST_REMAIN_FALSE:{label}")


def _assert_null(value: Any, *, label: str) -> None:
    if value is not None:
        raise RegimeCoverageStaOpenInputsCloseoutErrorV1(f"MUST_REMAIN_NULL:{label}")


def load_canonical_sta_open_inputs_closeout_manifest_v1(
    repo_root: Path | str | None = None,
) -> dict[str, Any]:
    root = Path(repo_root) if repo_root is not None else Path(__file__).resolve().parents[3]
    path = root / C.DECISIONS_MANIFEST_REL
    if not path.is_file():
        raise RegimeCoverageStaOpenInputsCloseoutErrorV1(
            f"MANIFEST_MISSING:{C.DECISIONS_MANIFEST_REL}"
        )
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RegimeCoverageStaOpenInputsCloseoutErrorV1("MANIFEST_MUST_BE_OBJECT")
    return payload


def derive_non_invented_coverage_counts_v1(
    *,
    observations: Sequence[Mapping[str, Any]],
    versioned_producer_id: str,
    producer_digest: str,
    partition_id: str,
    threshold_authority_ref: str,
    lookback_authority_ref: str,
    caller_supplied_counts: Mapping[str, Any] | None = None,
) -> dict[str, int]:
    """Derive partition-bounded counts from authorized producer observations.

    While threshold/lookback authorities remain UNSET, only observed
    ``missing`` / ``unknown`` labels are countable. ``low|mid|high`` fail closed.
    Caller-supplied counts that differ from observation-derived counts fail closed.
    """
    if versioned_producer_id != C.VERSIONED_PRODUCER_ID:
        raise RegimeCoverageStaOpenInputsCloseoutErrorV1(
            "UNAUTHORIZED_PRODUCER_FOR_COVERAGE_COUNTS"
        )
    if not isinstance(producer_digest, str) or not producer_digest.strip():
        raise RegimeCoverageStaOpenInputsCloseoutErrorV1("PRODUCER_DIGEST_REQUIRED")
    if not isinstance(partition_id, str) or not partition_id.strip():
        raise RegimeCoverageStaOpenInputsCloseoutErrorV1("PARTITION_ID_REQUIRED")
    if not isinstance(observations, Sequence) or isinstance(observations, (str, bytes)):
        raise RegimeCoverageStaOpenInputsCloseoutErrorV1("OBSERVATIONS_MUST_BE_SEQUENCE")
    if not observations:
        raise RegimeCoverageStaOpenInputsCloseoutErrorV1("OBSERVATIONS_REQUIRED")

    if threshold_authority_ref != C.THRESHOLD_AUTHORITY_UNSET:
        raise RegimeCoverageStaOpenInputsCloseoutErrorV1(
            "THRESHOLD_AUTHORITY_MUST_REMAIN_UNSET_FOR_THIS_CLOSEOUT"
        )
    if lookback_authority_ref != C.LOOKBACK_AUTHORITY_UNSET:
        raise RegimeCoverageStaOpenInputsCloseoutErrorV1(
            "LOOKBACK_AUTHORITY_MUST_REMAIN_UNSET_FOR_THIS_CLOSEOUT"
        )

    counts: dict[str, int] = {"missing": 0, "unknown": 0}
    seen_event_times: set[int] = set()
    previous_et: int | None = None

    for index, raw in enumerate(observations):
        obs = _require_mapping(raw, label=f"observations[{index}]")
        label = obs.get("label")
        if not isinstance(label, str) or not label.strip():
            raise RegimeCoverageStaOpenInputsCloseoutErrorV1(f"OBSERVATION_LABEL_REQUIRED:{index}")
        if label in C.FORBIDDEN_LABELS_WHILE_UNSET:
            raise RegimeCoverageStaOpenInputsCloseoutErrorV1(
                f"LOW_MID_HIGH_FORBIDDEN_WHILE_THRESHOLDS_LOOKBACKS_UNSET:{label}"
            )
        if label not in C.COUNTABLE_LABELS_WHILE_UNSET:
            raise RegimeCoverageStaOpenInputsCloseoutErrorV1(
                f"UNCOUNTABLE_OR_UNKNOWN_TAXONOMY_LABEL:{label}"
            )
        et = obs.get("event_time_epoch_s")
        if not isinstance(et, int) or isinstance(et, bool):
            raise RegimeCoverageStaOpenInputsCloseoutErrorV1(
                f"OBSERVATION_EVENT_TIME_INVALID:{index}"
            )
        if et in seen_event_times:
            raise RegimeCoverageStaOpenInputsCloseoutErrorV1(
                f"DUPLICATE_OBSERVATION_EVENT_TIME:{et}"
            )
        if previous_et is not None and et <= previous_et:
            raise RegimeCoverageStaOpenInputsCloseoutErrorV1(
                f"PIT_CHRONOLOGY_VIOLATION:{previous_et}->{et}"
            )
        seen_event_times.add(et)
        previous_et = et
        counts[label] += 1

    if caller_supplied_counts is not None:
        supplied = _require_mapping(caller_supplied_counts, label="caller_supplied_counts")
        normalized_supplied = {str(k): int(v) for k, v in supplied.items()}
        if normalized_supplied != counts:
            raise RegimeCoverageStaOpenInputsCloseoutErrorV1(
                "CALLER_SUPPLIED_OR_INVENTED_COUNTS_REJECTED"
            )

    return dict(counts)


def assert_provable_eth_usdt_swap_compatibility_v1(
    *,
    instrument_binding: Mapping[str, Any],
    triad_manifest: Mapping[str, Any],
    candle_join_ref: str,
    mark_join_ref: str,
    raw_pt1m_pack_ref: str,
    allow_string_similarity_inference: bool = False,
) -> dict[str, Any]:
    """Prove ETH-USDT-SWAP compatibility via exact InstrumentBindingV1 match."""
    if allow_string_similarity_inference:
        raise RegimeCoverageStaOpenInputsCloseoutErrorV1(
            "STRING_NAME_SIMILARITY_INFERENCE_FORBIDDEN"
        )

    binding = _require_mapping(instrument_binding, label="instrument_binding")
    for field in C.INSTRUMENT_BINDING_FIELDS:
        if field not in binding:
            raise RegimeCoverageStaOpenInputsCloseoutErrorV1(
                f"INSTRUMENT_BINDING_FIELD_MISSING:{field}"
            )
        expected = C.REQUIRED_INSTRUMENT_BINDING_V1[field]
        actual = binding.get(field)
        if actual != expected:
            raise RegimeCoverageStaOpenInputsCloseoutErrorV1(
                f"INSTRUMENT_BINDING_FIELD_MISMATCH:{field}"
            )

    triad = _require_mapping(triad_manifest, label="triad_manifest")
    triad_binding = _require_mapping(
        triad.get("instrument_binding"), label="triad.instrument_binding"
    )
    for field in C.INSTRUMENT_BINDING_FIELDS:
        field_obj = _require_mapping(
            triad_binding.get(field), label=f"triad.instrument_binding.{field}"
        )
        owner_value = field_obj.get("owner_value")
        status = field_obj.get("status")
        if status != "RATIFIED":
            raise RegimeCoverageStaOpenInputsCloseoutErrorV1(
                f"TRIAD_INSTRUMENT_FIELD_NOT_RATIFIED:{field}"
            )
        if owner_value != C.REQUIRED_INSTRUMENT_BINDING_V1[field]:
            raise RegimeCoverageStaOpenInputsCloseoutErrorV1(
                f"TRIAD_INSTRUMENT_OWNER_VALUE_MISMATCH:{field}"
            )

    if candle_join_ref != (
        "docs/ops/PRODUCTIVE_PURE_STACK_STAGE2_SURFACE_B_OWNER_STA_"
        "CANDLE_MARK_INSTRUMENT_AUTHORITY_DECISION_V1.md#candle_source_authority"
    ):
        raise RegimeCoverageStaOpenInputsCloseoutErrorV1("CANDLE_JOIN_REF_MISMATCH")
    if mark_join_ref != (
        "docs/ops/PRODUCTIVE_PURE_STACK_STAGE2_SURFACE_B_OWNER_STA_"
        "CANDLE_MARK_INSTRUMENT_AUTHORITY_DECISION_V1.md#mark_source_authority"
    ):
        raise RegimeCoverageStaOpenInputsCloseoutErrorV1("MARK_JOIN_REF_MISMATCH")
    if raw_pt1m_pack_ref != C.PARENT_RAW_INPUT_PACK_OWNER_DECISION_REL:
        raise RegimeCoverageStaOpenInputsCloseoutErrorV1("RAW_PT1M_PACK_REF_MISMATCH")

    # Reject name-similarity style claims that omit exact field equality.
    for suspicious_key in (
        "symbol_guess",
        "name_similarity",
        "fuzzy_match",
        "inferred_from_string",
    ):
        if suspicious_key in binding:
            raise RegimeCoverageStaOpenInputsCloseoutErrorV1(
                f"STRING_INFERENCE_CLAIM_FORBIDDEN:{suspicious_key}"
            )

    return {
        "ok": True,
        "compatibility": "provable_eth_usdt_swap_compatibility",
        "instrument_binding": dict(C.REQUIRED_INSTRUMENT_BINDING_V1),
        "string_name_similarity_inference": False,
    }


def validate_sta_open_inputs_closeout_manifest_v1(
    manifest: Mapping[str, Any],
) -> dict[str, Any]:
    """Validate the canonical STA open-inputs closeout decision surface."""
    for key in C.REQUIRED_MANIFEST_TOP_KEYS:
        if key not in manifest:
            raise RegimeCoverageStaOpenInputsCloseoutErrorV1(f"MANIFEST_MISSING_KEY:{key}")

    if manifest.get("schema_version") != C.SCHEMA_VERSION:
        raise RegimeCoverageStaOpenInputsCloseoutErrorV1("SCHEMA_VERSION_MISMATCH")
    if manifest.get("document_type") != C.DOCUMENT_TYPE:
        raise RegimeCoverageStaOpenInputsCloseoutErrorV1("DOCUMENT_TYPE_MISMATCH")
    if manifest.get("capability_scope") != C.CAPABILITY_SCOPE:
        raise RegimeCoverageStaOpenInputsCloseoutErrorV1("CAPABILITY_SCOPE_MISMATCH")
    if manifest.get("status") != C.STATUS_CLOSEOUT_RATIFIED:
        raise RegimeCoverageStaOpenInputsCloseoutErrorV1("STATUS_MUST_BE_CLOSEOUT_RATIFIED")
    if manifest.get("decision_id") != C.DECISION_ID:
        raise RegimeCoverageStaOpenInputsCloseoutErrorV1("DECISION_ID_MISMATCH")
    if manifest.get("decision_status") != C.DECISION_STATUS_RATIFIED:
        raise RegimeCoverageStaOpenInputsCloseoutErrorV1("DECISION_STATUS_MUST_BE_RATIFIED")
    if manifest.get("owner_go") != C.OWNER_GO:
        raise RegimeCoverageStaOpenInputsCloseoutErrorV1("OWNER_GO_MISMATCH")
    if str(manifest.get("owner_go_base_sha") or "") != C.OWNER_GO_BASE_SHA:
        raise RegimeCoverageStaOpenInputsCloseoutErrorV1("OWNER_GO_BASE_SHA_MISMATCH")
    if manifest.get("authority_surface") != C.AUTHORITY_SURFACE:
        raise RegimeCoverageStaOpenInputsCloseoutErrorV1("AUTHORITY_SURFACE_MUST_BE_B")

    closed = manifest.get("closed_inputs")
    if not isinstance(closed, Sequence) or isinstance(closed, (str, bytes)):
        raise RegimeCoverageStaOpenInputsCloseoutErrorV1("CLOSED_INPUTS_MUST_BE_SEQUENCE")
    if tuple(closed) != C.CLOSED_INPUTS:
        raise RegimeCoverageStaOpenInputsCloseoutErrorV1("CLOSED_INPUTS_MISMATCH")

    remaining = manifest.get("sta_open_external_inputs_remaining")
    if not isinstance(remaining, Sequence) or isinstance(remaining, (str, bytes)):
        raise RegimeCoverageStaOpenInputsCloseoutErrorV1(
            "STA_OPEN_EXTERNAL_INPUTS_REMAINING_MUST_BE_SEQUENCE"
        )
    if tuple(remaining) != ():
        raise RegimeCoverageStaOpenInputsCloseoutErrorV1(
            "STA_OPEN_EXTERNAL_INPUTS_MUST_BE_EMPTY_AFTER_CLOSEOUT"
        )

    counts_block = _require_mapping(
        manifest.get("non_invented_coverage_counts"),
        label="non_invented_coverage_counts",
    )
    if counts_block.get("status") != "CLOSED":
        raise RegimeCoverageStaOpenInputsCloseoutErrorV1("COVERAGE_COUNTS_STATUS_MUST_BE_CLOSED")
    if counts_block.get("versioned_producer_id") != C.VERSIONED_PRODUCER_ID:
        raise RegimeCoverageStaOpenInputsCloseoutErrorV1("VERSIONED_PRODUCER_ID_MISMATCH")
    if counts_block.get("threshold_authority_ref") != C.THRESHOLD_AUTHORITY_UNSET:
        raise RegimeCoverageStaOpenInputsCloseoutErrorV1("THRESHOLD_AUTHORITY_MUST_REMAIN_UNSET")
    if counts_block.get("lookback_authority_ref") != C.LOOKBACK_AUTHORITY_UNSET:
        raise RegimeCoverageStaOpenInputsCloseoutErrorV1("LOOKBACK_AUTHORITY_MUST_REMAIN_UNSET")
    if tuple(counts_block.get("countable_labels_while_thresholds_lookbacks_unset") or ()) != (
        C.COUNTABLE_LABELS_WHILE_UNSET
    ):
        raise RegimeCoverageStaOpenInputsCloseoutErrorV1("COUNTABLE_LABELS_MISMATCH")
    if tuple(counts_block.get("forbidden_labels_while_thresholds_lookbacks_unset") or ()) != (
        C.FORBIDDEN_LABELS_WHILE_UNSET
    ):
        raise RegimeCoverageStaOpenInputsCloseoutErrorV1("FORBIDDEN_LABELS_MISMATCH")
    if (
        counts_block.get("derivation_rule")
        != "COUNTS_FROM_AUTHORIZED_PRODUCER_LABEL_OBSERVATIONS_ONLY"
    ):
        raise RegimeCoverageStaOpenInputsCloseoutErrorV1("DERIVATION_RULE_MISMATCH")
    if counts_block.get("caller_supplied_or_invented_counts") != "FAIL_CLOSED":
        raise RegimeCoverageStaOpenInputsCloseoutErrorV1("CALLER_SUPPLIED_COUNTS_MUST_FAIL_CLOSED")
    for flag in (
        "deterministic",
        "partition_bounded",
        "pit_no_lookahead_conformant",
        "digest_bound",
    ):
        if counts_block.get(flag) is not True:
            raise RegimeCoverageStaOpenInputsCloseoutErrorV1(f"COUNTS_FLAG_MUST_BE_TRUE:{flag}")
    _assert_null(
        counts_block.get("campaign_instance_regime_coverage_counts"),
        label="campaign_instance_regime_coverage_counts",
    )
    _assert_null(
        counts_block.get("campaign_instance_regime_coverage_instance"),
        label="campaign_instance_regime_coverage_instance",
    )

    compat = _require_mapping(
        manifest.get("provable_eth_usdt_swap_compatibility"),
        label="provable_eth_usdt_swap_compatibility",
    )
    if compat.get("status") != "CLOSED":
        raise RegimeCoverageStaOpenInputsCloseoutErrorV1("COMPATIBILITY_STATUS_MUST_BE_CLOSED")
    if compat.get("compatibility_mode") != ("EXACT_OWNER_RATIFIED_INSTRUMENTBINDINGV1_FIELD_MATCH"):
        raise RegimeCoverageStaOpenInputsCloseoutErrorV1("COMPATIBILITY_MODE_MISMATCH")
    if compat.get("string_name_similarity_inference") is not False:
        raise RegimeCoverageStaOpenInputsCloseoutErrorV1(
            "STRING_NAME_SIMILARITY_INFERENCE_MUST_BE_FALSE"
        )
    required_binding = _require_mapping(
        compat.get("required_instrument_binding_v1"),
        label="required_instrument_binding_v1",
    )
    if dict(required_binding) != C.REQUIRED_INSTRUMENT_BINDING_V1:
        raise RegimeCoverageStaOpenInputsCloseoutErrorV1("REQUIRED_INSTRUMENT_BINDING_V1_MISMATCH")
    if compat.get("incomplete_contradictory_or_unprovable_bindings") != "FAIL_CLOSED":
        raise RegimeCoverageStaOpenInputsCloseoutErrorV1("UNPROVABLE_BINDINGS_MUST_FAIL_CLOSED")
    if compat.get("raw_pt1m_pack_ref") != C.PARENT_RAW_INPUT_PACK_OWNER_DECISION_REL:
        raise RegimeCoverageStaOpenInputsCloseoutErrorV1("RAW_PT1M_PACK_REF_MISMATCH")

    authority_refs = _require_mapping(manifest.get("authority_refs"), label="authority_refs")
    expected_refs = {
        "parent_regime_coverage_decision": C.PARENT_REGIME_COVERAGE_DECISION_REL,
        "parent_triad": C.PARENT_TRIAD_DECISION_REL,
        "parent_raw_input_pack": C.PARENT_RAW_INPUT_PACK_OWNER_DECISION_REL,
        "producer_package": C.PRODUCER_PACKAGE_REL,
        "digest_contract": C.DIGEST_CONTRACT_REL,
        "pit_rules": C.PIT_RULES_REL,
        "label_semantics": C.LABEL_SEMANTICS_REL,
    }
    for key, expected in expected_refs.items():
        if authority_refs.get(key) != expected:
            raise RegimeCoverageStaOpenInputsCloseoutErrorV1(f"AUTHORITY_REF_MISMATCH:{key}")

    non_effects = _require_mapping(manifest.get("non_effects"), label="non_effects")
    for key in C.NON_EFFECT_FALSE_KEYS:
        _assert_false(non_effects.get(key), label=f"non_effects.{key}")
    if non_effects.get("productive_numeric_values_set") != 0:
        raise RegimeCoverageStaOpenInputsCloseoutErrorV1(
            "PRODUCTIVE_NUMERIC_VALUES_MUST_REMAIN_ZERO"
        )
    if non_effects.get("dashboard_authority_effect") != "NONE":
        raise RegimeCoverageStaOpenInputsCloseoutErrorV1("DASHBOARD_AUTHORITY_MUST_BE_NONE")
    if non_effects.get("runtime_authorization_effect") != "NONE":
        raise RegimeCoverageStaOpenInputsCloseoutErrorV1(
            "RUNTIME_AUTHORIZATION_EFFECT_MUST_BE_NONE"
        )

    decisions = _require_mapping(manifest.get("decisions"), label="decisions")
    if tuple(decisions.get("CLOSED_INPUTS") or ()) != C.CLOSED_INPUTS:
        raise RegimeCoverageStaOpenInputsCloseoutErrorV1("DECISIONS_CLOSED_INPUTS_MISMATCH")
    decisions_non_effects = _require_mapping(
        decisions.get("NON_EFFECTS"), label="decisions.NON_EFFECTS"
    )
    for key in C.NON_EFFECT_FALSE_KEYS:
        if key == "live_authorized":
            _assert_false(decisions_non_effects.get(key), label=f"decisions.NON_EFFECTS.{key}")
        elif key in decisions_non_effects:
            _assert_false(decisions_non_effects.get(key), label=f"decisions.NON_EFFECTS.{key}")
    if decisions_non_effects.get("productive_numeric_values_set") != 0:
        raise RegimeCoverageStaOpenInputsCloseoutErrorV1(
            "DECISIONS_PRODUCTIVE_NUMERIC_VALUES_MUST_REMAIN_ZERO"
        )
    if decisions_non_effects.get("dashboard_authority_effect") != "NONE":
        raise RegimeCoverageStaOpenInputsCloseoutErrorV1(
            "DECISIONS_DASHBOARD_AUTHORITY_MUST_BE_NONE"
        )

    return {
        "ok": True,
        "capability_scope": C.CAPABILITY_SCOPE,
        "decision_id": C.DECISION_ID,
        "status": C.STATUS_CLOSEOUT_RATIFIED,
        "decision_status": C.DECISION_STATUS_RATIFIED,
        "owner_go": C.OWNER_GO,
        "closed_inputs": list(C.CLOSED_INPUTS),
        "sta_open_external_inputs_remaining": [],
        "input_authority": False,
        "runtime_implemented": False,
        "regime_coverage_producer_available": False,
        "producer_reimplementation": False,
        "consumer_wiring": False,
        "dashboard_authority_effect": "NONE",
        "runtime_authorization_effect": "NONE",
    }


__all__ = [
    "RegimeCoverageStaOpenInputsCloseoutErrorV1",
    "assert_provable_eth_usdt_swap_compatibility_v1",
    "derive_non_invented_coverage_counts_v1",
    "load_canonical_sta_open_inputs_closeout_manifest_v1",
    "validate_sta_open_inputs_closeout_manifest_v1",
]
