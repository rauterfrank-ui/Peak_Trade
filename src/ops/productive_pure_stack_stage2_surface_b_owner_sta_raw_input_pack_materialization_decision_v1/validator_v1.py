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
    require_open_status: bool = True,
) -> dict[str, Any]:
    """Validate the canonical raw input-pack materialization decision surface."""
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
    for field in C.AUTHORIZE_DETAIL_FIELDS:
        if field not in detail_fields:
            raise RawInputPackMaterializationDecisionErrorV1(
                f"AUTHORIZE_DETAIL_FIELD_MISSING:{field}"
            )
        _assert_null(detail_fields.get(field), label=f"authorize_detail_fields.{field}")
        _assert_no_forbidden_source_token(
            detail_fields.get(field), label=f"authorize_detail_fields.{field}"
        )

    open_fields = _require_mapping(
        manifest.get("open_null_instance_fields"), label="open_null_instance_fields"
    )
    for key in C.NULL_INSTANCE_KEYS:
        if key not in open_fields:
            raise RawInputPackMaterializationDecisionErrorV1(f"OPEN_NULL_FIELD_MISSING:{key}")
        _assert_null(open_fields.get(key), label=f"open_null_instance_fields.{key}")

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

    sta_inputs = manifest.get("sta_open_external_inputs")
    if not isinstance(sta_inputs, Sequence) or isinstance(sta_inputs, (str, bytes)):
        raise RawInputPackMaterializationDecisionErrorV1(
            "STA_OPEN_EXTERNAL_INPUTS_MUST_BE_SEQUENCE"
        )
    for required in C.STA_OPEN_EXTERNAL_INPUTS:
        if required not in sta_inputs:
            raise RawInputPackMaterializationDecisionErrorV1(
                f"STA_OPEN_EXTERNAL_INPUT_MISSING:{required}"
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

    if require_open_status:
        if surface_status != C.STATUS_SURFACE_OPEN:
            raise RawInputPackMaterializationDecisionErrorV1("STATUS_MUST_REMAIN_SURFACE_OPEN")
        if decision_status != C.DECISION_STATUS_OPEN:
            raise RawInputPackMaterializationDecisionErrorV1("DECISION_STATUS_MUST_REMAIN_OPEN")
        _assert_null(owner_value, label="owner_value")
        _assert_null(mat_dec.get("owner_value"), label="decisions.owner_value")
        if mat_dec.get("status") != C.DECISION_STATUS_OPEN:
            raise RawInputPackMaterializationDecisionErrorV1("DECISIONS_STATUS_MUST_REMAIN_OPEN")
    else:
        if owner_value is not None and owner_value not in C.ALLOWED_OWNER_VALUES:
            raise RawInputPackMaterializationDecisionErrorV1("OWNER_VALUE_NOT_ALLOWED")
        if owner_value is not None:
            _assert_no_forbidden_source_token(owner_value, label="owner_value")

    _reject_invented_numeric_payload(manifest)

    return {
        "ok": True,
        "capability_scope": C.CAPABILITY_SCOPE,
        "decision_id": C.DECISION_ID,
        "status": surface_status,
        "decision_status": decision_status,
        "owner_value": owner_value,
        "allowed_owner_values": list(C.ALLOWED_OWNER_VALUES),
        "authorize_detail_fields_null": True,
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
