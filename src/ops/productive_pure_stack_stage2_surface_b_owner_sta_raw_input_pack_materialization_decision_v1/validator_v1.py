"""Fail-closed validator for raw input-pack materialization decision v1.

Open Owner/STA decision surface only. Does not authorize pack materialization,
campaign start, input-authority/runtime flips, producer reimplementation,
consumer wiring, PT1M adapter binding, or productive thresholds/lookbacks.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Mapping, Sequence

from src.ops.productive_pure_stack_stage2_surface_b_owner_sta_raw_input_pack_materialization_decision_v1 import (
    constants_v1 as C,
)

_NUMERIC_VALUE_RE = re.compile(
    r"(?i)(?<![\w/])(?:threshold|lookback|coverage[_ ]?count|bucket[_ ]?size|"
    r"window[_ ]?size|regime[_ ]?pct|coverage[_ ]?pct)\s*[:=]\s*"
    r"(?:0|[1-9]\d*(?:\.\d+)?)"
)


class RawInputPackMaterializationDecisionErrorV1(ValueError):
    """Fail-closed raw input-pack materialization decision error."""


def _require_mapping(raw: Any, *, label: str) -> Mapping[str, Any]:
    if not isinstance(raw, Mapping):
        raise RawInputPackMaterializationDecisionErrorV1(f"MAPPING_REQUIRED:{label}")
    return raw


def _assert_false(value: Any, *, label: str) -> None:
    if value is True:
        raise RawInputPackMaterializationDecisionErrorV1(f"MUST_REMAIN_FALSE:{label}")
    if value not in (False, None):
        if bool(value):
            raise RawInputPackMaterializationDecisionErrorV1(f"MUST_REMAIN_FALSE:{label}")


def _assert_null(value: Any, *, label: str) -> None:
    if value is not None:
        raise RawInputPackMaterializationDecisionErrorV1(f"MUST_REMAIN_NULL:{label}")


def _assert_exact(value: Any, expected: Any, *, label: str) -> None:
    if value != expected:
        raise RawInputPackMaterializationDecisionErrorV1(f"VALUE_MISMATCH:{label}")


def _assert_no_forbidden_source_token(value: Any, *, label: str) -> None:
    if value is None:
        return
    text = str(value).strip().lower()
    if not text:
        return
    for forbidden in C.FORBIDDEN_SOURCE_TOKENS:
        if forbidden.lower() in text:
            raise RawInputPackMaterializationDecisionErrorV1(
                f"FORBIDDEN_SOURCE:{forbidden}:{label}"
            )


def _validate_authorize_detail_fields_all_null(detail_fields: Mapping[str, Any]) -> None:
    for field in C.AUTHORIZE_DETAIL_FIELDS:
        if field not in detail_fields:
            raise RawInputPackMaterializationDecisionErrorV1(
                f"AUTHORIZE_DETAIL_FIELD_MISSING:{field}"
            )
        _assert_null(detail_fields.get(field), label=f"authorize_detail_fields.{field}")
        _assert_no_forbidden_source_token(
            detail_fields.get(field), label=f"authorize_detail_fields.{field}"
        )


def _validate_authorize_detail_fields_provable_closed(detail_fields: Mapping[str, Any]) -> None:
    for field in C.AUTHORIZE_DETAIL_FIELDS:
        if field not in detail_fields:
            raise RawInputPackMaterializationDecisionErrorV1(
                f"AUTHORIZE_DETAIL_FIELD_MISSING:{field}"
            )
    for field in C.AUTHORIZE_DETAIL_PROVABLE_FIELDS:
        expected = C.AUTHORIZE_DETAIL_PROVABLE_FIELD_VALUES[field]
        value = detail_fields.get(field)
        _assert_exact(value, expected, label=f"authorize_detail_fields.{field}")
        _assert_no_forbidden_source_token(value, label=f"authorize_detail_fields.{field}")
    for field in C.AUTHORIZE_DETAIL_INSTANCE_NULL_FIELDS:
        _assert_null(detail_fields.get(field), label=f"authorize_detail_fields.{field}")
        _assert_no_forbidden_source_token(
            detail_fields.get(field), label=f"authorize_detail_fields.{field}"
        )


def _validate_open_null_instance_fields_all_null(open_fields: Mapping[str, Any]) -> None:
    for key in C.NULL_INSTANCE_KEYS:
        if key not in open_fields:
            raise RawInputPackMaterializationDecisionErrorV1(f"OPEN_NULL_FIELD_MISSING:{key}")
        _assert_null(open_fields.get(key), label=f"open_null_instance_fields.{key}")


def _validate_open_null_instance_fields_provable_closed(
    open_fields: Mapping[str, Any],
) -> None:
    for key in C.NULL_INSTANCE_KEYS:
        if key not in open_fields:
            raise RawInputPackMaterializationDecisionErrorV1(f"OPEN_NULL_FIELD_MISSING:{key}")
    for field in C.PROVABLE_INSTANCE_FIELDS:
        expected = C.PROVABLE_INSTANCE_FIELD_VALUES[field]
        value = open_fields.get(field)
        _assert_exact(value, expected, label=f"open_null_instance_fields.{field}")
        if isinstance(value, Mapping):
            for nested_value in value.values():
                _assert_no_forbidden_source_token(
                    nested_value, label=f"open_null_instance_fields.{field}"
                )
        else:
            _assert_no_forbidden_source_token(value, label=f"open_null_instance_fields.{field}")
    for key in C.REMAINING_NULL_INSTANCE_KEYS:
        _assert_null(open_fields.get(key), label=f"open_null_instance_fields.{key}")


def _validate_authorize_detail_fields_owner_sta_fill(detail_fields: Mapping[str, Any]) -> None:
    for field in C.AUTHORIZE_DETAIL_FIELDS:
        if field not in detail_fields:
            raise RawInputPackMaterializationDecisionErrorV1(
                f"AUTHORIZE_DETAIL_FIELD_MISSING:{field}"
            )
    for field in C.AUTHORIZE_DETAIL_PROVABLE_FIELDS:
        expected = C.AUTHORIZE_DETAIL_PROVABLE_FIELD_VALUES[field]
        value = detail_fields.get(field)
        _assert_exact(value, expected, label=f"authorize_detail_fields.{field}")
        _assert_no_forbidden_source_token(value, label=f"authorize_detail_fields.{field}")
    for field, expected in C.AUTHORIZE_DETAIL_FILLED_FIELD_VALUES.items():
        value = detail_fields.get(field)
        _assert_exact(value, expected, label=f"authorize_detail_fields.{field}")
        if isinstance(value, str):
            _assert_no_forbidden_source_token(value, label=f"authorize_detail_fields.{field}")
        elif isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
            for item in value:
                _assert_no_forbidden_source_token(item, label=f"authorize_detail_fields.{field}")
    for field in C.AUTHORIZE_DETAIL_REMAINING_NULL_FIELDS:
        _assert_null(detail_fields.get(field), label=f"authorize_detail_fields.{field}")


def _validate_open_null_instance_fields_owner_sta_fill(open_fields: Mapping[str, Any]) -> None:
    for key in C.NULL_INSTANCE_KEYS:
        if key not in open_fields:
            raise RawInputPackMaterializationDecisionErrorV1(f"OPEN_NULL_FIELD_MISSING:{key}")
    for field in C.PROVABLE_INSTANCE_FIELDS:
        expected = C.PROVABLE_INSTANCE_FIELD_VALUES[field]
        value = open_fields.get(field)
        _assert_exact(value, expected, label=f"open_null_instance_fields.{field}")
    for field, expected in C.OPEN_INSTANCE_FILLED_FIELD_VALUES.items():
        value = open_fields.get(field)
        _assert_exact(value, expected, label=f"open_null_instance_fields.{field}")
        if isinstance(value, str):
            _assert_no_forbidden_source_token(value, label=f"open_null_instance_fields.{field}")
        elif isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
            for item in value:
                _assert_no_forbidden_source_token(item, label=f"open_null_instance_fields.{field}")
    for field in C.OPEN_INSTANCE_EXPLICIT_NULL_RATIFIED_FIELDS:
        _assert_null(open_fields.get(field), label=f"open_null_instance_fields.{field}")
    for field in C.OPEN_INSTANCE_REMAINING_NULL_FIELDS:
        _assert_null(open_fields.get(field), label=f"open_null_instance_fields.{field}")


def _validate_partition_geometry_v1() -> None:
    bounds = list(C.FILLED_PARTITION_BOUNDARIES_EVENT_TIME_EPOCH_S)
    if bounds != sorted(bounds):
        raise RawInputPackMaterializationDecisionErrorV1("PARTITION_BOUNDS_NOT_STRICTLY_ORDERED")
    if any(int(b) % 60 != 0 for b in bounds):
        raise RawInputPackMaterializationDecisionErrorV1("PARTITION_BOUNDS_NOT_PT1M_ALIGNED")
    if bounds[0] != C.AUTHORIZED_OBSERVATION_WINDOW_START_EPOCH_S:
        raise RawInputPackMaterializationDecisionErrorV1("PARTITION_BOUNDS_START_MISMATCH")
    if bounds[-1] != C.AUTHORIZED_OBSERVATION_WINDOW_EXCLUSIVE_TIP_EPOCH_S:
        raise RawInputPackMaterializationDecisionErrorV1("PARTITION_BOUNDS_TIP_MISMATCH")
    if tuple(C.FILLED_FOLD_IDS) != C.PARTITION_SEGMENTS:
        raise RawInputPackMaterializationDecisionErrorV1("FOLD_IDS_MUST_MATCH_PARTITION_SEGMENTS")
    if len(C.FILLED_BOOTSTRAP_SEEDS) != len(C.FILLED_FOLD_IDS):
        raise RawInputPackMaterializationDecisionErrorV1("BOOTSTRAP_SEEDS_MUST_MAP_1_1_TO_FOLDS")
    for segment in C.PARTITION_SEGMENTS:
        pair = C.FILLED_PARTITION_BOUNDARIES[segment]
        if len(pair) != 2 or int(pair[0]) >= int(pair[1]):
            raise RawInputPackMaterializationDecisionErrorV1(f"PARTITION_SEGMENT_INVALID:{segment}")
    reconstructed = [
        C.FILLED_PARTITION_BOUNDARIES["train"][0],
        C.FILLED_PARTITION_BOUNDARIES["train"][1],
        C.FILLED_PARTITION_BOUNDARIES["calibration"][1],
        C.FILLED_PARTITION_BOUNDARIES["validation"][1],
        C.FILLED_PARTITION_BOUNDARIES["holdout"][1],
    ]
    if reconstructed != bounds:
        raise RawInputPackMaterializationDecisionErrorV1("PARTITION_SEGMENTS_BOUNDS_INCONSISTENT")


def load_canonical_raw_input_pack_materialization_decisions_manifest_v1(
    repo_root: Path | str | None = None,
) -> dict[str, Any]:
    root = Path(repo_root) if repo_root is not None else Path(__file__).resolve().parents[3]
    path = root / C.DECISIONS_MANIFEST_REL
    if not path.is_file():
        raise RawInputPackMaterializationDecisionErrorV1(
            f"MANIFEST_MISSING:{C.DECISIONS_MANIFEST_REL}"
        )
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RawInputPackMaterializationDecisionErrorV1("MANIFEST_MUST_BE_OBJECT")
    return payload


def validate_raw_input_pack_materialization_manifest_v1(
    manifest: Mapping[str, Any],
    *,
    require_open_status: bool | None = None,
) -> dict[str, Any]:
    """Validate the canonical raw input-pack materialization decision surface.

    When ``require_open_status`` is None, mode is inferred from ``status``.
    """
    for key in C.REQUIRED_MANIFEST_TOP_KEYS:
        if key not in manifest:
            raise RawInputPackMaterializationDecisionErrorV1(f"MANIFEST_MISSING_KEY:{key}")

    if manifest.get("schema_version") != C.SCHEMA_VERSION:
        raise RawInputPackMaterializationDecisionErrorV1("SCHEMA_VERSION_MISMATCH")
    if manifest.get("document_type") != C.DOCUMENT_TYPE:
        raise RawInputPackMaterializationDecisionErrorV1("DOCUMENT_TYPE_MISMATCH")
    if manifest.get("capability_scope") != C.CAPABILITY_SCOPE:
        raise RawInputPackMaterializationDecisionErrorV1("CAPABILITY_SCOPE_MISMATCH")
    if manifest.get("authority_surface") != C.AUTHORITY_SURFACE:
        raise RawInputPackMaterializationDecisionErrorV1("AUTHORITY_SURFACE_MUST_BE_B")
    if str(manifest.get("baseline_origin_main_sha") or "") != C.BASELINE_ORIGIN_MAIN_SHA:
        raise RawInputPackMaterializationDecisionErrorV1("BASELINE_ORIGIN_MAIN_SHA_MISMATCH")
    if manifest.get("decision_id") != C.DECISION_ID:
        raise RawInputPackMaterializationDecisionErrorV1("DECISION_ID_MISMATCH")

    allowed = manifest.get("allowed_owner_values")
    if not isinstance(allowed, Sequence) or isinstance(allowed, (str, bytes)):
        raise RawInputPackMaterializationDecisionErrorV1("ALLOWED_OWNER_VALUES_MUST_BE_SEQUENCE")
    if tuple(allowed) != C.ALLOWED_OWNER_VALUES:
        raise RawInputPackMaterializationDecisionErrorV1("ALLOWED_OWNER_VALUES_MISMATCH")

    _assert_false(manifest.get("input_authority"), label="input_authority")
    _assert_false(manifest.get("runtime_implemented"), label="runtime_implemented")
    _assert_false(manifest.get("campaign_start_authorized"), label="campaign_start_authorized")
    _assert_false(
        manifest.get("raw_input_pack_materialization_authorized"),
        label="raw_input_pack_materialization_authorized",
    )
    _assert_false(manifest.get("raw_input_pack_created"), label="raw_input_pack_created")
    _assert_false(manifest.get("campaign_started"), label="campaign_started")
    _assert_false(manifest.get("pack_materialization"), label="pack_materialization")
    _assert_false(manifest.get("producer_reimplementation"), label="producer_reimplementation")
    _assert_false(manifest.get("consumer_wiring"), label="consumer_wiring")
    _assert_false(manifest.get("pt1m_adapter"), label="pt1m_adapter")
    _assert_false(
        manifest.get("productive_thresholds_lookbacks"),
        label="productive_thresholds_lookbacks",
    )
    _assert_false(
        manifest.get("regime_coverage_producer_available"),
        label="regime_coverage_producer_available",
    )

    if int(manifest.get("productive_numeric_values_set", -1)) != 0:
        raise RawInputPackMaterializationDecisionErrorV1(
            "PRODUCTIVE_NUMERIC_VALUES_MUST_REMAIN_ZERO"
        )
    if manifest.get("dashboard_authority_effect") != "NONE":
        raise RawInputPackMaterializationDecisionErrorV1("DASHBOARD_AUTHORITY_MUST_BE_NONE")
    if manifest.get("notion_ssot") is True:
        raise RawInputPackMaterializationDecisionErrorV1("NOTION_SSOT_MUST_REMAIN_FALSE")
    if manifest.get("repository_is_ssot") is False:
        raise RawInputPackMaterializationDecisionErrorV1("REPOSITORY_MUST_REMAIN_SSOT")
    if manifest.get("regime_coverage_status") != C.REGIME_COVERAGE_STATUS:
        raise RawInputPackMaterializationDecisionErrorV1(
            "REGIME_COVERAGE_MUST_REMAIN_SEMANTICALLY_UNRESOLVED"
        )

    detail_fields = _require_mapping(
        manifest.get("authorize_detail_fields"), label="authorize_detail_fields"
    )
    open_fields = _require_mapping(
        manifest.get("open_null_instance_fields"), label="open_null_instance_fields"
    )

    parent_refs = _require_mapping(
        manifest.get("parent_authority_refs"), label="parent_authority_refs"
    )
    for key, expected in C.PARENT_AUTHORITY_REF_VALUES.items():
        if parent_refs.get(key) != expected:
            raise RawInputPackMaterializationDecisionErrorV1(f"PARENT_AUTHORITY_REF_MISMATCH:{key}")

    forbidden_sources = manifest.get("forbidden_sources")
    if not isinstance(forbidden_sources, Sequence) or isinstance(forbidden_sources, (str, bytes)):
        raise RawInputPackMaterializationDecisionErrorV1("FORBIDDEN_SOURCES_MUST_BE_SEQUENCE")
    for token in C.FORBIDDEN_SOURCE_TOKENS:
        if token not in forbidden_sources:
            raise RawInputPackMaterializationDecisionErrorV1(
                f"FORBIDDEN_SOURCE_TOKEN_MISSING:{token}"
            )

    reject_sem = _require_mapping(manifest.get("reject_semantics"), label="reject_semantics")
    for key, expected in (
        ("raw_input_pack_materializable", False),
        ("surface_b_campaign_startable", False),
        ("fixture_demo_dashboard_may_substitute_authority", False),
        ("instance_fields_remain_null_or_absent", True),
    ):
        if reject_sem.get(key) is not expected:
            raise RawInputPackMaterializationDecisionErrorV1(f"REJECT_SEMANTICS_INVALID:{key}")

    authorize_sem = _require_mapping(
        manifest.get("authorize_semantics"), label="authorize_semantics"
    )
    for key, expected in (
        ("input_authority", False),
        ("runtime_implemented", False),
        ("raw_input_pack_created", False),
        ("campaign_started", False),
        ("pack_materialization_execution_requires_separate_explicit_go", True),
        (
            "raw_input_pack_materialization_authorized_remains_false_until_instance_fields_ratified",
            True,
        ),
        (
            "owner_fields_and_sta_proofs_must_be_fully_ratified_before_materialization_authorized",
            True,
        ),
    ):
        if authorize_sem.get(key) is not expected:
            raise RawInputPackMaterializationDecisionErrorV1(f"AUTHORIZE_SEMANTICS_INVALID:{key}")

    decisions = _require_mapping(manifest.get("decisions"), label="decisions")
    for key in (
        "RAW_INPUT_PACK_MATERIALIZATION",
        "FORBIDDEN_SOURCES",
        "NON_EFFECTS",
    ):
        if key not in decisions:
            raise RawInputPackMaterializationDecisionErrorV1(f"DECISIONS_MISSING:{key}")

    mat_dec = _require_mapping(
        decisions.get("RAW_INPUT_PACK_MATERIALIZATION"),
        label="RAW_INPUT_PACK_MATERIALIZATION",
    )
    if mat_dec.get("decision_id") != C.DECISION_ID:
        raise RawInputPackMaterializationDecisionErrorV1("DECISIONS_DECISION_ID_MISMATCH")
    if tuple(mat_dec.get("allowed_owner_values") or ()) != C.ALLOWED_OWNER_VALUES:
        raise RawInputPackMaterializationDecisionErrorV1("DECISIONS_ALLOWED_OWNER_VALUES_MISMATCH")

    non_effects = _require_mapping(decisions.get("NON_EFFECTS"), label="NON_EFFECTS")
    for key in (
        "input_authority",
        "runtime_implemented",
        "raw_input_pack_created",
        "raw_input_pack_materialization_authorized",
        "campaign_started",
        "campaign_start_authorized",
        "pack_materialization",
        "producer_reimplementation",
        "consumer_wiring",
        "pt1m_adapter",
        "productive_thresholds_lookbacks",
        "trading_logic_changed",
        "orders_testnet_live_paper_effects",
        "exchange_credential_effects",
        "regime_coverage_producer_available",
    ):
        if non_effects.get(key) is not False:
            raise RawInputPackMaterializationDecisionErrorV1(f"NON_EFFECTS_MUST_BE_FALSE:{key}")
    if non_effects.get("productive_numeric_values_set") != 0:
        raise RawInputPackMaterializationDecisionErrorV1(
            "NON_EFFECTS_PRODUCTIVE_NUMERIC_VALUES_MUST_BE_ZERO"
        )
    if non_effects.get("dashboard_authority_effect") != "NONE":
        raise RawInputPackMaterializationDecisionErrorV1(
            "NON_EFFECTS_DASHBOARD_AUTHORITY_MUST_BE_NONE"
        )
    if non_effects.get("regime_coverage_status") != C.REGIME_COVERAGE_STATUS:
        raise RawInputPackMaterializationDecisionErrorV1(
            "NON_EFFECTS_REGIME_COVERAGE_STATUS_INVALID"
        )

    owner_value = manifest.get("owner_value")
    decision_status = manifest.get("decision_status")
    surface_status = manifest.get("status")

    if require_open_status is None:
        require_open_status = surface_status == C.STATUS_SURFACE_OPEN

    authorize_detail_provable_refs_closed = False
    provable_instance_fields_closed = False
    decision_packet_ready = False
    owner_sta_fill_recorded = False
    expected_provable_refs_closed = surface_status in (
        C.STATUS_AUTHORIZE_DETAIL_PROVABLE_REFS_CLOSED,
        C.STATUS_PROVABLE_INSTANCE_FIELDS_CLOSED,
        C.STATUS_NON_PROVABLE_INSTANCE_VALUES_DECISION_PACKET_READY,
        C.STATUS_NON_PROVABLE_INSTANCE_VALUES_OWNER_AND_STA_FILL_RECORDED,
    )
    expected_provable_instance_closed = surface_status in (
        C.STATUS_PROVABLE_INSTANCE_FIELDS_CLOSED,
        C.STATUS_NON_PROVABLE_INSTANCE_VALUES_DECISION_PACKET_READY,
        C.STATUS_NON_PROVABLE_INSTANCE_VALUES_OWNER_AND_STA_FILL_RECORDED,
    )
    expected_decision_packet_ready = surface_status in (
        C.STATUS_NON_PROVABLE_INSTANCE_VALUES_DECISION_PACKET_READY,
        C.STATUS_NON_PROVABLE_INSTANCE_VALUES_OWNER_AND_STA_FILL_RECORDED,
    )
    expected_still_null = (
        surface_status == C.STATUS_NON_PROVABLE_INSTANCE_VALUES_DECISION_PACKET_READY
    )
    expected_partial_fill = (
        surface_status == C.STATUS_NON_PROVABLE_INSTANCE_VALUES_OWNER_AND_STA_FILL_RECORDED
    )
    if (
        authorize_sem.get("authorize_detail_provable_refs_closed")
        is not expected_provable_refs_closed
    ):
        raise RawInputPackMaterializationDecisionErrorV1(
            "AUTHORIZE_SEMANTICS_INVALID:authorize_detail_provable_refs_closed"
        )
    if authorize_sem.get("authorize_detail_fields_complete") is not False:
        raise RawInputPackMaterializationDecisionErrorV1(
            "AUTHORIZE_SEMANTICS_INVALID:authorize_detail_fields_complete"
        )
    if (
        authorize_sem.get("provable_instance_fields_closed", False)
        is not expected_provable_instance_closed
    ):
        raise RawInputPackMaterializationDecisionErrorV1(
            "AUTHORIZE_SEMANTICS_INVALID:provable_instance_fields_closed"
        )
    if (
        authorize_sem.get("require_explicit_owner_values_for_non_provable_fields", False)
        is not expected_provable_instance_closed
    ):
        raise RawInputPackMaterializationDecisionErrorV1(
            "AUTHORIZE_SEMANTICS_INVALID:require_explicit_owner_values_for_non_provable_fields"
        )
    if authorize_sem.get("silent_defaults", False) is not False:
        raise RawInputPackMaterializationDecisionErrorV1(
            "AUTHORIZE_SEMANTICS_INVALID:silent_defaults"
        )
    if (
        authorize_sem.get("non_provable_instance_values_decision_packet_ready", False)
        is not expected_decision_packet_ready
    ):
        raise RawInputPackMaterializationDecisionErrorV1(
            "AUTHORIZE_SEMANTICS_INVALID:non_provable_instance_values_decision_packet_ready"
        )
    if expected_still_null and (
        authorize_sem.get("non_provable_instance_values_still_null") is not True
    ):
        raise RawInputPackMaterializationDecisionErrorV1(
            "AUTHORIZE_SEMANTICS_INVALID:non_provable_instance_values_still_null"
        )
    if expected_partial_fill:
        if authorize_sem.get("non_provable_instance_values_still_null") is not False:
            raise RawInputPackMaterializationDecisionErrorV1(
                "AUTHORIZE_SEMANTICS_INVALID:non_provable_instance_values_still_null"
            )
        if authorize_sem.get("non_provable_instance_values_partially_filled") is not True:
            raise RawInputPackMaterializationDecisionErrorV1(
                "AUTHORIZE_SEMANTICS_INVALID:non_provable_instance_values_partially_filled"
            )
        if authorize_sem.get("campaign_id_explicit_leave_null") is not True:
            raise RawInputPackMaterializationDecisionErrorV1(
                "AUTHORIZE_SEMANTICS_INVALID:campaign_id_explicit_leave_null"
            )
        if authorize_sem.get("observation_pack_digest_leave_null_until_computed") is not True:
            raise RawInputPackMaterializationDecisionErrorV1(
                "AUTHORIZE_SEMANTICS_INVALID:observation_pack_digest_leave_null_until_computed"
            )
        if authorize_sem.get("regime_coverage_leave_null_until_sta_producer_proof") is not True:
            raise RawInputPackMaterializationDecisionErrorV1(
                "AUTHORIZE_SEMANTICS_INVALID:regime_coverage_leave_null_until_sta_producer_proof"
            )
        for key in (
            "purge_explicit_null_ratification",
            "embargo_explicit_null_ratification",
            "fold_sizes_explicit_null_ratification",
        ):
            if authorize_sem.get(key) is not True:
                raise RawInputPackMaterializationDecisionErrorV1(
                    f"AUTHORIZE_SEMANTICS_INVALID:{key}"
                )

    closed_sta = manifest.get("closed_sta_external_inputs")
    if not isinstance(closed_sta, Sequence) or isinstance(closed_sta, (str, bytes)):
        raise RawInputPackMaterializationDecisionErrorV1(
            "CLOSED_STA_EXTERNAL_INPUTS_MUST_BE_SEQUENCE"
        )
    require_owner = manifest.get("require_explicit_owner_values_for")
    if not isinstance(require_owner, Sequence) or isinstance(require_owner, (str, bytes)):
        raise RawInputPackMaterializationDecisionErrorV1(
            "REQUIRE_EXPLICIT_OWNER_VALUES_FOR_MUST_BE_SEQUENCE"
        )

    sta_inputs = manifest.get("sta_open_external_inputs")
    if not isinstance(sta_inputs, Sequence) or isinstance(sta_inputs, (str, bytes)):
        raise RawInputPackMaterializationDecisionErrorV1(
            "STA_OPEN_EXTERNAL_INPUTS_MUST_BE_SEQUENCE"
        )

    if require_open_status:
        if surface_status != C.STATUS_SURFACE_OPEN:
            raise RawInputPackMaterializationDecisionErrorV1("STATUS_MUST_REMAIN_SURFACE_OPEN")
        if decision_status != C.DECISION_STATUS_OPEN:
            raise RawInputPackMaterializationDecisionErrorV1("DECISION_STATUS_MUST_REMAIN_OPEN")
        _assert_null(owner_value, label="owner_value")
        _assert_null(mat_dec.get("owner_value"), label="decisions.owner_value")
        if mat_dec.get("status") != C.DECISION_STATUS_OPEN:
            raise RawInputPackMaterializationDecisionErrorV1("DECISIONS_STATUS_MUST_REMAIN_OPEN")
        _validate_authorize_detail_fields_all_null(detail_fields)
        _validate_open_null_instance_fields_all_null(open_fields)
        if tuple(closed_sta) != ():
            raise RawInputPackMaterializationDecisionErrorV1(
                "CLOSED_STA_EXTERNAL_INPUTS_MUST_BE_EMPTY_WHILE_OPEN"
            )
        if tuple(require_owner) != ():
            raise RawInputPackMaterializationDecisionErrorV1(
                "REQUIRE_EXPLICIT_OWNER_VALUES_FOR_MUST_BE_EMPTY_WHILE_OPEN"
            )
        # Historical open surface listed all eight STA inputs.
        historical_open_sta = C.CLOSED_STA_EXTERNAL_INPUTS[:2] + C.STA_OPEN_EXTERNAL_INPUTS_PRE_FILL
        for required in historical_open_sta:
            if required not in sta_inputs:
                raise RawInputPackMaterializationDecisionErrorV1(
                    f"STA_OPEN_EXTERNAL_INPUT_MISSING:{required}"
                )
    elif surface_status == C.STATUS_OWNER_VALUE_RECORDED:
        # Historical intermediate status (authorize details still all null).
        if decision_status != C.DECISION_STATUS_RATIFIED:
            raise RawInputPackMaterializationDecisionErrorV1("DECISION_STATUS_MUST_BE_RATIFIED")
        if owner_value != C.RECORDED_OWNER_VALUE:
            raise RawInputPackMaterializationDecisionErrorV1("OWNER_VALUE_MUST_MATCH_RECORDED")
        if mat_dec.get("owner_value") != C.RECORDED_OWNER_VALUE:
            raise RawInputPackMaterializationDecisionErrorV1(
                "DECISIONS_OWNER_VALUE_MUST_MATCH_RECORDED"
            )
        if mat_dec.get("status") != C.DECISION_STATUS_RATIFIED:
            raise RawInputPackMaterializationDecisionErrorV1("DECISIONS_STATUS_MUST_BE_RATIFIED")
        _assert_no_forbidden_source_token(owner_value, label="owner_value")
        _validate_authorize_detail_fields_all_null(detail_fields)
        _validate_open_null_instance_fields_all_null(open_fields)
        if tuple(closed_sta) != ():
            raise RawInputPackMaterializationDecisionErrorV1(
                "CLOSED_STA_EXTERNAL_INPUTS_MUST_BE_EMPTY_WHILE_OWNER_VALUE_ONLY"
            )
        if tuple(require_owner) != ():
            raise RawInputPackMaterializationDecisionErrorV1(
                "REQUIRE_EXPLICIT_OWNER_VALUES_FOR_MUST_BE_EMPTY_WHILE_OWNER_VALUE_ONLY"
            )
        historical_open_sta = C.CLOSED_STA_EXTERNAL_INPUTS[:2] + C.STA_OPEN_EXTERNAL_INPUTS_PRE_FILL
        for required in historical_open_sta:
            if required not in sta_inputs:
                raise RawInputPackMaterializationDecisionErrorV1(
                    f"STA_OPEN_EXTERNAL_INPUT_MISSING:{required}"
                )
    elif surface_status == C.STATUS_AUTHORIZE_DETAIL_PROVABLE_REFS_CLOSED:
        # Historical intermediate status before instance-field closeout.
        if (
            str(manifest.get("owner_go_base_sha") or "")
            != "61d9abb07d4d88a0f1be19b9476db8ca0d3ba135"
        ):
            raise RawInputPackMaterializationDecisionErrorV1("OWNER_GO_BASE_SHA_MISMATCH")
        if decision_status != C.DECISION_STATUS_RATIFIED:
            raise RawInputPackMaterializationDecisionErrorV1("DECISION_STATUS_MUST_BE_RATIFIED")
        if owner_value != C.RECORDED_OWNER_VALUE:
            raise RawInputPackMaterializationDecisionErrorV1("OWNER_VALUE_MUST_MATCH_RECORDED")
        if mat_dec.get("owner_value") != C.RECORDED_OWNER_VALUE:
            raise RawInputPackMaterializationDecisionErrorV1(
                "DECISIONS_OWNER_VALUE_MUST_MATCH_RECORDED"
            )
        if mat_dec.get("status") != C.DECISION_STATUS_RATIFIED:
            raise RawInputPackMaterializationDecisionErrorV1("DECISIONS_STATUS_MUST_BE_RATIFIED")
        _assert_no_forbidden_source_token(owner_value, label="owner_value")
        _validate_authorize_detail_fields_provable_closed(detail_fields)
        _validate_open_null_instance_fields_all_null(open_fields)
        authorize_detail_provable_refs_closed = True
        if tuple(closed_sta) != ():
            raise RawInputPackMaterializationDecisionErrorV1(
                "CLOSED_STA_EXTERNAL_INPUTS_MUST_BE_EMPTY_WHILE_REFS_ONLY"
            )
        if tuple(require_owner) != ():
            raise RawInputPackMaterializationDecisionErrorV1(
                "REQUIRE_EXPLICIT_OWNER_VALUES_FOR_MUST_BE_EMPTY_WHILE_REFS_ONLY"
            )
        historical_open_sta = C.CLOSED_STA_EXTERNAL_INPUTS[:2] + C.STA_OPEN_EXTERNAL_INPUTS_PRE_FILL
        for required in historical_open_sta:
            if required not in sta_inputs:
                raise RawInputPackMaterializationDecisionErrorV1(
                    f"STA_OPEN_EXTERNAL_INPUT_MISSING:{required}"
                )
    elif surface_status == C.STATUS_PROVABLE_INSTANCE_FIELDS_CLOSED:
        if (
            str(manifest.get("owner_go_base_sha") or "")
            != C.OWNER_GO_BASE_SHA_PROVABLE_INSTANCE_FIELDS_CLOSED
        ):
            raise RawInputPackMaterializationDecisionErrorV1("OWNER_GO_BASE_SHA_MISMATCH")
        if decision_status != C.DECISION_STATUS_RATIFIED:
            raise RawInputPackMaterializationDecisionErrorV1("DECISION_STATUS_MUST_BE_RATIFIED")
        if owner_value != C.RECORDED_OWNER_VALUE:
            raise RawInputPackMaterializationDecisionErrorV1("OWNER_VALUE_MUST_MATCH_RECORDED")
        if mat_dec.get("owner_value") != C.RECORDED_OWNER_VALUE:
            raise RawInputPackMaterializationDecisionErrorV1(
                "DECISIONS_OWNER_VALUE_MUST_MATCH_RECORDED"
            )
        if mat_dec.get("status") != C.DECISION_STATUS_RATIFIED:
            raise RawInputPackMaterializationDecisionErrorV1("DECISIONS_STATUS_MUST_BE_RATIFIED")
        _assert_no_forbidden_source_token(owner_value, label="owner_value")
        _validate_authorize_detail_fields_provable_closed(detail_fields)
        _validate_open_null_instance_fields_provable_closed(open_fields)
        authorize_detail_provable_refs_closed = True
        provable_instance_fields_closed = True
        if tuple(closed_sta) != C.CLOSED_STA_EXTERNAL_INPUTS[:2]:
            raise RawInputPackMaterializationDecisionErrorV1("CLOSED_STA_EXTERNAL_INPUTS_MISMATCH")
        if tuple(require_owner) != C.REQUIRE_EXPLICIT_OWNER_VALUES_FOR_PRE_FILL:
            raise RawInputPackMaterializationDecisionErrorV1(
                "REQUIRE_EXPLICIT_OWNER_VALUES_FOR_MISMATCH"
            )
        for required in C.STA_OPEN_EXTERNAL_INPUTS_PRE_FILL:
            if required not in sta_inputs:
                raise RawInputPackMaterializationDecisionErrorV1(
                    f"STA_OPEN_EXTERNAL_INPUT_MISSING:{required}"
                )
        for closed in C.CLOSED_STA_EXTERNAL_INPUTS[:2]:
            if closed in sta_inputs:
                raise RawInputPackMaterializationDecisionErrorV1(
                    f"STA_OPEN_EXTERNAL_INPUT_MUST_BE_CLOSED:{closed}"
                )
    elif surface_status == C.STATUS_NON_PROVABLE_INSTANCE_VALUES_DECISION_PACKET_READY:
        if (
            str(manifest.get("owner_go_base_sha") or "")
            != C.OWNER_GO_BASE_SHA_DECISION_PACKET_READY
        ):
            raise RawInputPackMaterializationDecisionErrorV1("OWNER_GO_BASE_SHA_MISMATCH")
        if decision_status != C.DECISION_STATUS_RATIFIED:
            raise RawInputPackMaterializationDecisionErrorV1("DECISION_STATUS_MUST_BE_RATIFIED")
        if owner_value != C.RECORDED_OWNER_VALUE:
            raise RawInputPackMaterializationDecisionErrorV1("OWNER_VALUE_MUST_MATCH_RECORDED")
        if mat_dec.get("owner_value") != C.RECORDED_OWNER_VALUE:
            raise RawInputPackMaterializationDecisionErrorV1(
                "DECISIONS_OWNER_VALUE_MUST_MATCH_RECORDED"
            )
        if mat_dec.get("status") != C.DECISION_STATUS_RATIFIED:
            raise RawInputPackMaterializationDecisionErrorV1("DECISIONS_STATUS_MUST_BE_RATIFIED")
        _assert_no_forbidden_source_token(owner_value, label="owner_value")
        _validate_authorize_detail_fields_provable_closed(detail_fields)
        _validate_open_null_instance_fields_provable_closed(open_fields)
        authorize_detail_provable_refs_closed = True
        provable_instance_fields_closed = True
        if tuple(closed_sta) != C.CLOSED_STA_EXTERNAL_INPUTS[:2]:
            raise RawInputPackMaterializationDecisionErrorV1("CLOSED_STA_EXTERNAL_INPUTS_MISMATCH")
        if tuple(require_owner) != C.REQUIRE_EXPLICIT_OWNER_VALUES_FOR_PRE_FILL:
            raise RawInputPackMaterializationDecisionErrorV1(
                "REQUIRE_EXPLICIT_OWNER_VALUES_FOR_MISMATCH"
            )
        for required in C.STA_OPEN_EXTERNAL_INPUTS_PRE_FILL:
            if required not in sta_inputs:
                raise RawInputPackMaterializationDecisionErrorV1(
                    f"STA_OPEN_EXTERNAL_INPUT_MISSING:{required}"
                )
        for closed in C.CLOSED_STA_EXTERNAL_INPUTS[:2]:
            if closed in sta_inputs:
                raise RawInputPackMaterializationDecisionErrorV1(
                    f"STA_OPEN_EXTERNAL_INPUT_MUST_BE_CLOSED:{closed}"
                )
        _validate_non_provable_instance_values_decision_packet(
            manifest.get("non_provable_instance_values_decision_packet"),
            mode="packet_ready_still_null",
        )
        decision_packet_ready = True
    elif surface_status == C.STATUS_NON_PROVABLE_INSTANCE_VALUES_OWNER_AND_STA_FILL_RECORDED:
        if str(manifest.get("owner_go_base_sha") or "") != C.OWNER_GO_BASE_SHA:
            raise RawInputPackMaterializationDecisionErrorV1("OWNER_GO_BASE_SHA_MISMATCH")
        if decision_status != C.DECISION_STATUS_RATIFIED:
            raise RawInputPackMaterializationDecisionErrorV1("DECISION_STATUS_MUST_BE_RATIFIED")
        if owner_value != C.RECORDED_OWNER_VALUE:
            raise RawInputPackMaterializationDecisionErrorV1("OWNER_VALUE_MUST_MATCH_RECORDED")
        if mat_dec.get("owner_value") != C.RECORDED_OWNER_VALUE:
            raise RawInputPackMaterializationDecisionErrorV1(
                "DECISIONS_OWNER_VALUE_MUST_MATCH_RECORDED"
            )
        if mat_dec.get("status") != C.DECISION_STATUS_RATIFIED:
            raise RawInputPackMaterializationDecisionErrorV1("DECISIONS_STATUS_MUST_BE_RATIFIED")
        _assert_no_forbidden_source_token(owner_value, label="owner_value")
        _validate_partition_geometry_v1()
        _validate_authorize_detail_fields_owner_sta_fill(detail_fields)
        _validate_open_null_instance_fields_owner_sta_fill(open_fields)
        authorize_detail_provable_refs_closed = True
        provable_instance_fields_closed = True
        owner_sta_fill_recorded = True
        if tuple(closed_sta) != C.CLOSED_STA_EXTERNAL_INPUTS:
            raise RawInputPackMaterializationDecisionErrorV1("CLOSED_STA_EXTERNAL_INPUTS_MISMATCH")
        if tuple(require_owner) != C.REQUIRE_EXPLICIT_OWNER_VALUES_FOR:
            raise RawInputPackMaterializationDecisionErrorV1(
                "REQUIRE_EXPLICIT_OWNER_VALUES_FOR_MISMATCH"
            )
        for required in C.STA_OPEN_EXTERNAL_INPUTS:
            if required not in sta_inputs:
                raise RawInputPackMaterializationDecisionErrorV1(
                    f"STA_OPEN_EXTERNAL_INPUT_MISSING:{required}"
                )
        for closed in C.CLOSED_STA_EXTERNAL_INPUTS:
            if closed in sta_inputs:
                raise RawInputPackMaterializationDecisionErrorV1(
                    f"STA_OPEN_EXTERNAL_INPUT_MUST_BE_CLOSED:{closed}"
                )
        _validate_non_provable_instance_values_decision_packet(
            manifest.get("non_provable_instance_values_decision_packet"),
            mode="owner_sta_fill_recorded",
        )
        decision_packet_ready = True
    else:
        raise RawInputPackMaterializationDecisionErrorV1("STATUS_UNSUPPORTED")

    _reject_invented_numeric_payload(manifest)

    return {
        "ok": True,
        "capability_scope": C.CAPABILITY_SCOPE,
        "decision_id": C.DECISION_ID,
        "status": surface_status,
        "decision_status": decision_status,
        "owner_value": owner_value,
        "allowed_owner_values": list(C.ALLOWED_OWNER_VALUES),
        "authorize_detail_fields_null": not authorize_detail_provable_refs_closed,
        "authorize_detail_provable_refs_closed": authorize_detail_provable_refs_closed,
        "authorize_detail_fields_complete": False,
        "provable_instance_fields_closed": provable_instance_fields_closed,
        "non_provable_instance_values_decision_packet_ready": decision_packet_ready,
        "non_provable_instance_values_still_null": (
            decision_packet_ready and not owner_sta_fill_recorded
        ),
        "non_provable_instance_values_partially_filled": owner_sta_fill_recorded,
        "require_explicit_owner_values_for_non_provable_fields": (provable_instance_fields_closed),
        "silent_defaults": False,
        "proposed_values": False,
        "invented_values": False,
        "input_authority": False,
        "runtime_implemented": False,
        "raw_input_pack_created": False,
        "raw_input_pack_materialization_authorized": False,
        "pack_materialization": False,
        "campaign_started": False,
        "campaign_start_authorized": False,
        "productive_numeric_values_set": 0,
        "regime_coverage_status": C.REGIME_COVERAGE_STATUS,
        "dashboard_authority_effect": "NONE",
        "notion_ssot": False,
        "repository_is_ssot": True,
    }


def validate_raw_input_pack_materialization_owner_choice_v1(
    owner_value: Any,
    *,
    authorize_detail_fields: Mapping[str, Any] | None = None,
    claim: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Fail-closed gate for an Owner choice against the open surface.

    Accepts only the two allowed owner values. Does not flip materialization
    authorization, create packs, start campaigns, or flip input/runtime.
    """
    if owner_value not in C.ALLOWED_OWNER_VALUES:
        raise RawInputPackMaterializationDecisionErrorV1("OWNER_VALUE_NOT_ALLOWED")

    details = authorize_detail_fields or {}
    if not isinstance(details, Mapping):
        raise RawInputPackMaterializationDecisionErrorV1("AUTHORIZE_DETAIL_FIELDS_MUST_BE_MAPPING")

    if owner_value == C.AUTHORIZE_OWNER_VALUE:
        # Owner authorize-value recording keeps all detail fields null.
        # Provable-ref closeout is a separate Owner GO / status transition.
        for field in C.AUTHORIZE_DETAIL_FIELDS:
            value = details.get(field)
            _assert_null(value, label=f"authorize_detail_fields.{field}")
            _assert_no_forbidden_source_token(value, label=f"authorize_detail_fields.{field}")
    else:
        for field, value in details.items():
            _assert_null(value, label=f"reject.authorize_detail_fields.{field}")

    claim_map = claim or {}
    for key in (
        "input_authority",
        "runtime_implemented",
        "raw_input_pack_created",
        "raw_input_pack_materialization_authorized",
        "pack_materialization",
        "campaign_started",
        "campaign_start_authorized",
        "producer_reimplementation",
        "consumer_wiring",
        "pt1m_adapter",
    ):
        _assert_false(claim_map.get(key), label=f"claim.{key}")
    if claim_map.get("dashboard_authority_effect") not in (None, "NONE"):
        raise RawInputPackMaterializationDecisionErrorV1("DASHBOARD_AUTHORITY_MUST_BE_NONE")
    if claim_map.get("productive_numeric_values_set") not in (None, 0):
        raise RawInputPackMaterializationDecisionErrorV1(
            "PRODUCTIVE_NUMERIC_VALUES_MUST_REMAIN_ZERO"
        )

    return {
        "ok": True,
        "owner_value": owner_value,
        "input_authority": False,
        "runtime_implemented": False,
        "raw_input_pack_created": False,
        "raw_input_pack_materialization_authorized": False,
        "pack_materialization": False,
        "campaign_started": False,
        "dashboard_authority_effect": "NONE",
    }


def _validate_non_provable_instance_values_decision_packet(
    raw: Any,
    *,
    mode: str,
) -> None:
    packet = _require_mapping(raw, label="non_provable_instance_values_decision_packet")
    _assert_exact(packet.get("packet_id"), C.DECISION_PACKET_ID, label="decision_packet.packet_id")
    _assert_exact(packet.get("decision_id"), C.DECISION_ID, label="decision_packet.decision_id")
    _assert_exact(
        packet.get("document_type"),
        C.DECISION_PACKET_DOCUMENT_TYPE,
        label="decision_packet.document_type",
    )
    if mode == "packet_ready_still_null":
        expected_packet_status = C.DECISION_PACKET_STATUS_READY_STILL_NULL
        expected_count = len(C.NON_PROVABLE_INSTANCE_VALUES_DECISION_PACKET_FIELDS)
    elif mode == "owner_sta_fill_recorded":
        expected_packet_status = C.DECISION_PACKET_STATUS
        expected_count = C.DECISION_PACKET_ENUMERATED_REMAINING_NULL_FIELD_COUNT
    else:
        raise RawInputPackMaterializationDecisionErrorV1("DECISION_PACKET_MODE_UNSUPPORTED")
    _assert_exact(
        packet.get("status"),
        expected_packet_status,
        label="decision_packet.status",
    )
    _assert_exact(
        packet.get("owner_value_recorded"),
        C.RECORDED_OWNER_VALUE,
        label="decision_packet.owner_value_recorded",
    )
    for key in (
        "proposed_values",
        "silent_defaults",
        "invented_values",
        "pack_materialization",
        "raw_input_pack_created",
        "raw_input_pack_materialization_authorized",
        "campaign_start",
        "input_authority",
        "runtime_implemented",
    ):
        _assert_false(packet.get(key), label=f"decision_packet.{key}")

    fields = packet.get("fields")
    if not isinstance(fields, Sequence) or isinstance(fields, (str, bytes)):
        raise RawInputPackMaterializationDecisionErrorV1("DECISION_PACKET_FIELDS_MUST_BE_SEQUENCE")
    if len(fields) != len(C.NON_PROVABLE_INSTANCE_VALUES_DECISION_PACKET_FIELDS):
        raise RawInputPackMaterializationDecisionErrorV1("DECISION_PACKET_FIELD_COUNT_MISMATCH")
    if packet.get("enumerated_remaining_null_field_count") != expected_count:
        raise RawInputPackMaterializationDecisionErrorV1(
            "DECISION_PACKET_ENUMERATED_COUNT_MISMATCH"
        )

    seen: list[str] = []
    for index, row_raw in enumerate(fields):
        row = _require_mapping(row_raw, label=f"decision_packet.fields[{index}]")
        field = row.get("field")
        if field not in C.NON_PROVABLE_INSTANCE_VALUES_DECISION_PACKET_FIELD_SPECS:
            raise RawInputPackMaterializationDecisionErrorV1(
                f"DECISION_PACKET_UNKNOWN_FIELD:{field}"
            )
        if field in seen:
            raise RawInputPackMaterializationDecisionErrorV1(
                f"DECISION_PACKET_DUPLICATE_FIELD:{field}"
            )
        seen.append(str(field))
        expected = C.NON_PROVABLE_INSTANCE_VALUES_DECISION_PACKET_FIELD_SPECS[str(field)]
        _assert_exact(
            row.get("input_class"),
            expected["input_class"],
            label=f"decision_packet.fields[{field}].input_class",
        )
        _assert_exact(
            row.get("related_sta_open_input"),
            expected["related_sta_open_input"],
            label=f"decision_packet.fields[{field}].related_sta_open_input",
        )
        _assert_exact(
            row.get("allowed_format"),
            expected["allowed_format"],
            label=f"decision_packet.fields[{field}].allowed_format",
        )
        if mode == "packet_ready_still_null":
            for key in (
                "fillable_owner_value",
                "fillable_sta_value",
                "proposed_value",
            ):
                _assert_null(row.get(key), label=f"decision_packet.fields[{field}].{key}")
            _assert_exact(
                row.get("status"),
                C.DECISION_PACKET_FIELD_STATUS_OPEN,
                label=f"decision_packet.fields[{field}].status",
            )
        else:
            _assert_null(
                row.get("proposed_value"),
                label=f"decision_packet.fields[{field}].proposed_value",
            )
            _assert_exact(
                row.get("status"),
                expected["status"],
                label=f"decision_packet.fields[{field}].status",
            )
            _assert_exact(
                row.get("fillable_owner_value"),
                expected["fillable_owner_value"],
                label=f"decision_packet.fields[{field}].fillable_owner_value",
            )
            _assert_exact(
                row.get("fillable_sta_value"),
                expected["fillable_sta_value"],
                label=f"decision_packet.fields[{field}].fillable_sta_value",
            )
        for key in (
            "proposed_values_forbidden",
            "silent_defaults_forbidden",
            "invented_values_forbidden",
        ):
            if row.get(key) is not True:
                raise RawInputPackMaterializationDecisionErrorV1(
                    f"DECISION_PACKET_FLAG_REQUIRED_TRUE:{field}:{key}"
                )
        constraints = row.get("constraints")
        provenance = row.get("provenance_requirements")
        locations = row.get("manifest_locations")
        for label, value in (
            ("constraints", constraints),
            ("provenance_requirements", provenance),
            ("manifest_locations", locations),
        ):
            if not isinstance(value, Sequence) or isinstance(value, (str, bytes)) or len(value) < 1:
                raise RawInputPackMaterializationDecisionErrorV1(
                    f"DECISION_PACKET_{label.upper()}_REQUIRED:{field}"
                )
            for item in value:
                if not isinstance(item, str) or not item.strip():
                    raise RawInputPackMaterializationDecisionErrorV1(
                        f"DECISION_PACKET_{label.upper()}_ITEM_INVALID:{field}"
                    )

    if tuple(seen) != C.NON_PROVABLE_INSTANCE_VALUES_DECISION_PACKET_FIELDS:
        raise RawInputPackMaterializationDecisionErrorV1(
            "DECISION_PACKET_FIELD_ORDER_OR_SET_MISMATCH"
        )


def _reject_invented_numeric_payload(manifest: Mapping[str, Any]) -> None:
    blob = json.dumps(manifest, sort_keys=True, ensure_ascii=True)
    if _NUMERIC_VALUE_RE.search(blob):
        raise RawInputPackMaterializationDecisionErrorV1(
            "PRODUCTIVE_OR_INVENTED_NUMERIC_VALUES_FORBIDDEN"
        )
    decisions = _require_mapping(manifest.get("decisions"), label="decisions")
    mat_dec = _require_mapping(
        decisions.get("RAW_INPUT_PACK_MATERIALIZATION"),
        label="RAW_INPUT_PACK_MATERIALIZATION",
    )
    for key in ("purge", "embargo", "fold_sizes", "productive_thresholds", "productive_lookbacks"):
        if key in mat_dec and mat_dec.get(key) is not None:
            raise RawInputPackMaterializationDecisionErrorV1(
                f"INVENTED_NUMERIC_OR_POLICY_FORBIDDEN:{key}"
            )


__all__ = [
    "RawInputPackMaterializationDecisionErrorV1",
    "load_canonical_raw_input_pack_materialization_decisions_manifest_v1",
    "validate_raw_input_pack_materialization_manifest_v1",
    "validate_raw_input_pack_materialization_owner_choice_v1",
]
