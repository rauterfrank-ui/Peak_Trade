"""Fail-closed validator for Surface-B Owner/STA candle/mark/instrument authority.

Ratification without separate candle/mark authority, complete InstrumentBindingV1,
and explicit Owner values remains blocked. Structure-open manifests keep instance
values null and ratification flags false.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping, MutableMapping, Optional, Sequence

from src.ops.productive_pure_stack_stage2_surface_b_owner_sta_candle_mark_instrument_authority_decision_v1 import (
    constants_v1 as C,
)


class OwnerStaAuthorityDecisionErrorV1(ValueError):
    """Fail-closed Owner/STA authority decision error."""


def _require_mapping(raw: Any, *, label: str) -> Mapping[str, Any]:
    if not isinstance(raw, Mapping):
        raise OwnerStaAuthorityDecisionErrorV1(f"MAPPING_REQUIRED:{label}")
    return raw


def _assert_false(value: Any, *, label: str) -> None:
    if value is True:
        raise OwnerStaAuthorityDecisionErrorV1(f"MUST_REMAIN_FALSE:{label}")
    if value not in (False, None):
        # Explicit non-bool truthy claims are also rejected.
        if bool(value):
            raise OwnerStaAuthorityDecisionErrorV1(f"MUST_REMAIN_FALSE:{label}")


def _assert_null(value: Any, *, label: str) -> None:
    if value is not None:
        raise OwnerStaAuthorityDecisionErrorV1(f"MUST_REMAIN_NULL:{label}")


def _assert_source_token_allowed(token: Any) -> None:
    text = str(token or "").strip().lower()
    if not text:
        return
    for forbidden in C.FORBIDDEN_SOURCE_TOKENS:
        if forbidden in text:
            raise OwnerStaAuthorityDecisionErrorV1(f"FORBIDDEN_SOURCE:{forbidden}")


def load_canonical_owner_sta_decisions_manifest_v1(
    repo_root: Path | str | None = None,
) -> dict[str, Any]:
    root = Path(repo_root) if repo_root is not None else Path(__file__).resolve().parents[3]
    path = root / C.DECISIONS_MANIFEST_REL
    if not path.is_file():
        raise OwnerStaAuthorityDecisionErrorV1(f"MANIFEST_MISSING:{C.DECISIONS_MANIFEST_REL}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise OwnerStaAuthorityDecisionErrorV1("MANIFEST_MUST_BE_OBJECT")
    return payload


def validate_owner_sta_authority_manifest_v1(
    manifest: Mapping[str, Any],
    *,
    require_structure_open_status: bool = True,
) -> dict[str, Any]:
    """Validate the canonical Owner/STA decision surface (structure-open by default)."""
    for key in C.REQUIRED_MANIFEST_TOP_KEYS:
        if key not in manifest:
            raise OwnerStaAuthorityDecisionErrorV1(f"MANIFEST_MISSING_KEY:{key}")

    if manifest.get("schema_version") != C.SCHEMA_VERSION:
        raise OwnerStaAuthorityDecisionErrorV1("SCHEMA_VERSION_MISMATCH")
    if manifest.get("document_type") != C.DOCUMENT_TYPE:
        raise OwnerStaAuthorityDecisionErrorV1("DOCUMENT_TYPE_MISMATCH")
    if manifest.get("capability_scope") != C.CAPABILITY_SCOPE:
        raise OwnerStaAuthorityDecisionErrorV1("CAPABILITY_SCOPE_MISMATCH")
    if manifest.get("authority_surface") != C.AUTHORITY_SURFACE:
        raise OwnerStaAuthorityDecisionErrorV1("AUTHORITY_SURFACE_MUST_BE_B")
    if str(manifest.get("baseline_origin_main_sha") or "") != C.BASELINE_ORIGIN_MAIN_SHA:
        raise OwnerStaAuthorityDecisionErrorV1("BASELINE_ORIGIN_MAIN_SHA_MISMATCH")

    _assert_false(manifest.get("input_authority"), label="input_authority")
    _assert_false(manifest.get("runtime_implemented"), label="runtime_implemented")
    _assert_false(manifest.get("campaign_start_authorized"), label="campaign_start_authorized")
    _assert_false(
        manifest.get("raw_input_pack_materialization_authorized"),
        label="raw_input_pack_materialization_authorized",
    )
    _assert_false(manifest.get("raw_input_pack_created"), label="raw_input_pack_created")
    _assert_false(manifest.get("campaign_started"), label="campaign_started")

    if int(manifest.get("productive_numeric_values_set", -1)) != 0:
        raise OwnerStaAuthorityDecisionErrorV1("PRODUCTIVE_NUMERIC_VALUES_MUST_REMAIN_ZERO")

    if manifest.get("dashboard_authority_effect") not in (None, "NONE"):
        if manifest.get("dashboard_authority_effect") != "NONE":
            raise OwnerStaAuthorityDecisionErrorV1("DASHBOARD_AUTHORITY_MUST_BE_NONE")
    if manifest.get("notion_ssot") is True:
        raise OwnerStaAuthorityDecisionErrorV1("NOTION_SSOT_MUST_REMAIN_FALSE")
    if manifest.get("repository_is_ssot") is False:
        raise OwnerStaAuthorityDecisionErrorV1("REPOSITORY_MUST_REMAIN_SSOT")
    if manifest.get("o4_unchanged") is False:
        raise OwnerStaAuthorityDecisionErrorV1("O4_MUST_REMAIN_UNCHANGED")

    if manifest.get("regime_coverage_producer_available") is not False:
        raise OwnerStaAuthorityDecisionErrorV1("REGIME_COVERAGE_PRODUCER_MUST_REMAIN_UNAVAILABLE")
    if manifest.get("regime_coverage_status") != C.REGIME_COVERAGE_STATUS:
        raise OwnerStaAuthorityDecisionErrorV1(
            "REGIME_COVERAGE_MUST_REMAIN_SEMANTICALLY_UNRESOLVED"
        )

    candle = _require_mapping(
        manifest.get("candle_source_authority"), label="candle_source_authority"
    )
    mark = _require_mapping(manifest.get("mark_source_authority"), label="mark_source_authority")
    binding = _require_mapping(manifest.get("instrument_binding"), label="instrument_binding")
    table = manifest.get("owner_decision_table")
    if not isinstance(table, Sequence) or isinstance(table, (str, bytes)):
        raise OwnerStaAuthorityDecisionErrorV1("OWNER_DECISION_TABLE_MUST_BE_SEQUENCE")

    _validate_candle_authority_structure(candle)
    _validate_mark_authority_structure(mark, candle_source_ref=candle.get("proposed_source_ref"))
    _validate_instrument_binding_structure(binding)
    _validate_owner_decision_table(table)

    open_fields = _require_mapping(
        manifest.get("open_null_instance_fields"), label="open_null_instance_fields"
    )
    for key in C.NULL_INSTANCE_KEYS:
        if key not in open_fields:
            raise OwnerStaAuthorityDecisionErrorV1(f"OPEN_NULL_FIELD_MISSING:{key}")
        _assert_null(open_fields.get(key), label=f"open_null_instance_fields.{key}")

    decisions = _require_mapping(manifest.get("decisions"), label="decisions")
    for key in (
        "CANDLE_SOURCE_AUTHORITY",
        "MARK_SOURCE_AUTHORITY",
        "INSTRUMENT_BINDING",
        "REGIME_COVERAGE",
        "FORBIDDEN_SOURCES",
        "NON_EFFECTS",
    ):
        if key not in decisions:
            raise OwnerStaAuthorityDecisionErrorV1(f"DECISIONS_MISSING:{key}")

    mark_dec = _require_mapping(
        decisions.get("MARK_SOURCE_AUTHORITY"), label="MARK_SOURCE_AUTHORITY"
    )
    if mark_dec.get("candle_mark_trade_equivalence") != "FORBIDDEN":
        raise OwnerStaAuthorityDecisionErrorV1(
            "DECISION_CANDLE_MARK_TRADE_EQUIVALENCE_MUST_REMAIN_FORBIDDEN"
        )
    if mark_dec.get("previous_candle_close_fallback") != "FORBIDDEN":
        raise OwnerStaAuthorityDecisionErrorV1(
            "DECISION_PREVIOUS_CANDLE_CLOSE_FALLBACK_MUST_REMAIN_FORBIDDEN"
        )

    if require_structure_open_status:
        if manifest.get("status") != C.STATUS_SURFACE_OPEN:
            raise OwnerStaAuthorityDecisionErrorV1("STATUS_MUST_REMAIN_SURFACE_OPEN")
        _assert_false(manifest.get("candle_authority_ratified"), label="candle_authority_ratified")
        _assert_false(manifest.get("mark_authority_ratified"), label="mark_authority_ratified")
        _assert_false(
            manifest.get("instrument_binding_ratified"), label="instrument_binding_ratified"
        )
        _assert_null(
            candle.get("owner_ratified_source_ref"), label="candle.owner_ratified_source_ref"
        )
        _assert_null(mark.get("owner_ratified_source_ref"), label="mark.owner_ratified_source_ref")
        for field in C.REQUIRED_INSTRUMENT_FIELDS:
            field_obj = _require_mapping(binding.get(field), label=f"instrument_binding.{field}")
            _assert_null(
                field_obj.get("owner_value"), label=f"instrument_binding.{field}.owner_value"
            )
            if field_obj.get("status") != "OPEN":
                raise OwnerStaAuthorityDecisionErrorV1(
                    f"INSTRUMENT_FIELD_STATUS_MUST_REMAIN_OPEN:{field}"
                )
        for row in table:
            row_map = _require_mapping(row, label="owner_decision_table.row")
            _assert_null(
                row_map.get("owner_value"),
                label=f"decision.{row_map.get('decision_id')}.owner_value",
            )
            if row_map.get("status") != "OPEN":
                raise OwnerStaAuthorityDecisionErrorV1(
                    f"DECISION_STATUS_MUST_REMAIN_OPEN:{row_map.get('decision_id')}"
                )

    return {
        "ok": True,
        "capability_scope": C.CAPABILITY_SCOPE,
        "status": manifest.get("status"),
        "input_authority": False,
        "runtime_implemented": False,
        "candle_authority_ratified": False,
        "mark_authority_ratified": False,
        "instrument_binding_ratified": False,
        "campaign_start_authorized": False,
        "raw_input_pack_materialization_authorized": False,
        "raw_input_pack_created": False,
        "campaign_started": False,
        "productive_numeric_values_set": 0,
        "regime_coverage_producer_available": False,
        "regime_coverage_status": C.REGIME_COVERAGE_STATUS,
        "dashboard_authority_effect": "NONE",
        "notion_ssot": False,
        "repository_is_ssot": True,
    }


def validate_owner_sta_ratification_claim_v1(
    claim: Mapping[str, Any],
    *,
    owner_manifest: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Fail-closed gate for any claim that authorities/bindings are ratified.

    Requires separate candle/mark source refs, complete InstrumentBindingV1, and
    explicit Owner values. Does not authorize pack materialization or campaign start.
    """
    manifest = owner_manifest or load_canonical_owner_sta_decisions_manifest_v1()
    validate_owner_sta_authority_manifest_v1(manifest, require_structure_open_status=True)

    _assert_false(claim.get("input_authority"), label="claim.input_authority")
    _assert_false(claim.get("runtime_implemented"), label="claim.runtime_implemented")
    _assert_false(claim.get("campaign_start_authorized"), label="claim.campaign_start_authorized")
    _assert_false(
        claim.get("raw_input_pack_materialization_authorized"),
        label="claim.raw_input_pack_materialization_authorized",
    )
    _assert_false(claim.get("raw_input_pack_created"), label="claim.raw_input_pack_created")
    _assert_false(claim.get("campaign_started"), label="claim.campaign_started")
    if claim.get("start_evidence_collection") is True:
        raise OwnerStaAuthorityDecisionErrorV1("CAMPAIGN_START_UNAUTHORIZED")

    for token_key in ("source_id", "authority_source", "candle_source", "mark_source"):
        if token_key in claim:
            _assert_source_token_allowed(claim.get(token_key))

    wants_candle = bool(claim.get("candle_authority_ratified"))
    wants_mark = bool(claim.get("mark_authority_ratified"))
    wants_binding = bool(claim.get("instrument_binding_ratified"))

    if not (wants_candle or wants_mark or wants_binding):
        return {
            "ok": True,
            "candle_authority_ratified": False,
            "mark_authority_ratified": False,
            "instrument_binding_ratified": False,
            "input_authority": False,
            "runtime_implemented": False,
        }

    candle_ref = claim.get("candle_source_ref")
    mark_ref = claim.get("mark_source_ref")
    binding_raw = claim.get("instrument_binding")

    if wants_candle or wants_mark or wants_binding:
        # Any ratification attempt requires the full triad to be explicit and separate.
        if not wants_candle or not wants_mark or not wants_binding:
            raise OwnerStaAuthorityDecisionErrorV1(
                "RATIFICATION_REQUIRES_SEPARATE_CANDLE_MARK_AND_COMPLETE_BINDING"
            )

    if candle_ref is None or not str(candle_ref).strip():
        raise OwnerStaAuthorityDecisionErrorV1("CANDLE_SOURCE_REF_REQUIRED_FOR_RATIFICATION")
    if mark_ref is None or not str(mark_ref).strip():
        raise OwnerStaAuthorityDecisionErrorV1("MARK_SOURCE_REF_REQUIRED_FOR_RATIFICATION")
    if str(candle_ref).strip() == str(mark_ref).strip():
        raise OwnerStaAuthorityDecisionErrorV1("CANDLE_AND_MARK_SOURCE_REF_MUST_DIFFER")

    _assert_source_token_allowed(candle_ref)
    _assert_source_token_allowed(mark_ref)
    _reject_forbidden_candle_ref(str(candle_ref))
    _reject_forbidden_mark_ref(str(mark_ref))

    if str(candle_ref).strip() not in C.ALLOWED_CANDLE_SOURCE_REF_CANDIDATES:
        raise OwnerStaAuthorityDecisionErrorV1("CANDLE_SOURCE_REF_NOT_IN_ALLOWED_CANDIDATES")
    if str(mark_ref).strip() not in C.ALLOWED_MARK_SOURCE_REF_CANDIDATES:
        raise OwnerStaAuthorityDecisionErrorV1("MARK_SOURCE_REF_NOT_IN_ALLOWED_CANDIDATES")

    if claim.get("previous_candle_close_fallback") is True:
        raise OwnerStaAuthorityDecisionErrorV1("PREVIOUS_CANDLE_CLOSE_FALLBACK_FORBIDDEN")
    if claim.get("candle_mark_trade_equivalence") not in (None, "FORBIDDEN", False):
        if claim.get("candle_mark_trade_equivalence") is True:
            raise OwnerStaAuthorityDecisionErrorV1("CANDLE_MARK_TRADE_EQUIVALENCE_FORBIDDEN")
        if str(claim.get("candle_mark_trade_equivalence")).upper() != "FORBIDDEN":
            raise OwnerStaAuthorityDecisionErrorV1("CANDLE_MARK_TRADE_EQUIVALENCE_FORBIDDEN")
    if claim.get("allow_candle_mark_equivalence") is True:
        raise OwnerStaAuthorityDecisionErrorV1("CANDLE_MARK_TRADE_EQUIVALENCE_FORBIDDEN")
    if claim.get("o4_pt1h_as_pt1m") is True:
        raise OwnerStaAuthorityDecisionErrorV1("O4_PT1H_AS_PT1M_FORBIDDEN")

    binding = _require_mapping(binding_raw, label="instrument_binding")
    for field in C.REQUIRED_INSTRUMENT_FIELDS:
        value = binding.get(field)
        if not isinstance(value, str) or not value.strip():
            raise OwnerStaAuthorityDecisionErrorV1(f"INSTRUMENT_BINDING_INCOMPLETE:{field}")
        _assert_source_token_allowed(value)

    venue_id = str(binding.get("venue_instrument_id") or "").upper()
    canonical_id = str(binding.get("canonical_instrument_id") or "").upper()
    if "BTC" in venue_id or "BTC" in canonical_id or "XBT" in venue_id or "XBT" in canonical_id:
        raise OwnerStaAuthorityDecisionErrorV1("BTC_TEST_BINDING_FORBIDDEN")

    # Structure-open canonical manifest still has null Owner values: claim may not
    # silently treat the open surface as ratified without a separate Owner GO artifact.
    if manifest.get("status") == C.STATUS_SURFACE_OPEN:
        raise OwnerStaAuthorityDecisionErrorV1("OWNER_STA_RATIFICATION_BLOCKED_WHILE_SURFACE_OPEN")

    return {
        "ok": True,
        "candle_authority_ratified": True,
        "mark_authority_ratified": True,
        "instrument_binding_ratified": True,
        "input_authority": False,
        "runtime_implemented": False,
    }


def _validate_candle_authority_structure(candle: Mapping[str, Any]) -> None:
    if candle.get("authority_class") != "VENUE_NATIVE_FINALIZED_PT1M_CANDLES":
        raise OwnerStaAuthorityDecisionErrorV1("CANDLE_AUTHORITY_CLASS_INVALID")
    if candle.get("timeframe") != C.BAR_INTERVAL:
        raise OwnerStaAuthorityDecisionErrorV1("CANDLE_TIMEFRAME_MUST_BE_PT1M")
    if candle.get("open_tip_bars") is not False:
        raise OwnerStaAuthorityDecisionErrorV1("OPEN_TIP_BARS_MUST_BE_FALSE")
    if candle.get("venue_finalized_required") is not True:
        raise OwnerStaAuthorityDecisionErrorV1("VENUE_FINALIZED_REQUIRED_MUST_BE_TRUE")
    if candle.get("event_time_semantics") != "PT1M_BUCKET_OPEN_EVENT_TIME":
        raise OwnerStaAuthorityDecisionErrorV1("CANDLE_EVENT_TIME_SEMANTICS_INVALID")
    if candle.get("o4_pt1h_as_pt1m") is not False:
        raise OwnerStaAuthorityDecisionErrorV1("O4_PT1H_AS_PT1M_MUST_BE_FALSE")
    if candle.get("technical_producer_is_raw_source_authority") is not False:
        raise OwnerStaAuthorityDecisionErrorV1("STA_PRODUCER_IS_NOT_RAW_SOURCE_AUTHORITY")
    proposed = candle.get("proposed_source_ref")
    if proposed not in C.ALLOWED_CANDLE_SOURCE_REF_CANDIDATES:
        raise OwnerStaAuthorityDecisionErrorV1("CANDLE_PROPOSED_SOURCE_REF_INVALID")
    _assert_null(candle.get("candles"), label="candle_source_authority.candles")
    _assert_null(candle.get("raw_rows"), label="candle_source_authority.raw_rows")


def _validate_mark_authority_structure(mark: Mapping[str, Any], *, candle_source_ref: Any) -> None:
    if mark.get("authority_class") != "VENUE_NATIVE_PT1M_BUCKET_MARK_SERIES":
        raise OwnerStaAuthorityDecisionErrorV1("MARK_AUTHORITY_CLASS_INVALID")
    if mark.get("timeframe") != C.BAR_INTERVAL:
        raise OwnerStaAuthorityDecisionErrorV1("MARK_TIMEFRAME_MUST_BE_PT1M")
    if mark.get("join_key") != C.JOIN_KEY:
        raise OwnerStaAuthorityDecisionErrorV1("MARK_JOIN_KEY_INVALID")
    if mark.get("candle_mark_trade_equivalence") != "FORBIDDEN":
        raise OwnerStaAuthorityDecisionErrorV1(
            "CANDLE_MARK_TRADE_EQUIVALENCE_MUST_REMAIN_FORBIDDEN"
        )
    if mark.get("previous_candle_close_fallback") != "FORBIDDEN":
        raise OwnerStaAuthorityDecisionErrorV1(
            "PREVIOUS_CANDLE_CLOSE_FALLBACK_MUST_REMAIN_FORBIDDEN"
        )
    if mark.get("snapshot_mark_price_endpoint_as_historical_authority") is not False:
        raise OwnerStaAuthorityDecisionErrorV1("SNAPSHOT_MARK_NOT_HISTORICAL_AUTHORITY")
    proposed = mark.get("proposed_source_ref")
    if proposed not in C.ALLOWED_MARK_SOURCE_REF_CANDIDATES:
        raise OwnerStaAuthorityDecisionErrorV1("MARK_PROPOSED_SOURCE_REF_INVALID")
    if proposed == candle_source_ref:
        raise OwnerStaAuthorityDecisionErrorV1("MARK_SOURCE_REF_MUST_DIFFER_FROM_CANDLE")
    _assert_null(mark.get("marks"), label="mark_source_authority.marks")
    _assert_null(mark.get("raw_rows"), label="mark_source_authority.raw_rows")


def _validate_instrument_binding_structure(binding: Mapping[str, Any]) -> None:
    if binding.get("mode") != "SINGLE_SELECTED_FUTURE_VENUE_NATIVE":
        raise OwnerStaAuthorityDecisionErrorV1("INSTRUMENT_BINDING_MODE_INVALID")
    if binding.get("multi_instrument_pooling") is not False:
        raise OwnerStaAuthorityDecisionErrorV1("MULTI_INSTRUMENT_POOLING_FORBIDDEN")
    candidates = binding.get("competing_candidates")
    if not isinstance(candidates, Sequence) or isinstance(candidates, (str, bytes)):
        raise OwnerStaAuthorityDecisionErrorV1("COMPETING_CANDIDATES_MUST_BE_SEQUENCE")
    candidate_ids = []
    for row in candidates:
        row_map = _require_mapping(row, label="competing_candidate")
        cid = str(row_map.get("candidate_id") or "")
        if not cid:
            raise OwnerStaAuthorityDecisionErrorV1("COMPETING_CANDIDATE_ID_REQUIRED")
        candidate_ids.append(cid)
        if cid in C.EXCLUDED_INSTRUMENT_CANDIDATE_IDS:
            if row_map.get("eligibility") != "EXCLUDED":
                raise OwnerStaAuthorityDecisionErrorV1(
                    f"EXCLUDED_CANDIDATE_MUST_BE_MARKED_EXCLUDED:{cid}"
                )
        status = row_map.get("status")
        if status not in {"OPEN", "EXCLUDED"}:
            raise OwnerStaAuthorityDecisionErrorV1(f"CANDIDATE_STATUS_INVALID:{cid}")
        # Never silently select a candidate in the structure-open surface.
        if row_map.get("selected") is True:
            raise OwnerStaAuthorityDecisionErrorV1(f"CANDIDATE_MUST_NOT_BE_PRESELECTED:{cid}")
    for required_id in C.INSTRUMENT_CANDIDATE_IDS:
        if required_id not in candidate_ids:
            raise OwnerStaAuthorityDecisionErrorV1(f"COMPETING_CANDIDATE_MISSING:{required_id}")
    for excluded_id in C.EXCLUDED_INSTRUMENT_CANDIDATE_IDS:
        if excluded_id not in candidate_ids:
            raise OwnerStaAuthorityDecisionErrorV1(f"EXCLUDED_CANDIDATE_MISSING:{excluded_id}")

    for field in C.REQUIRED_INSTRUMENT_FIELDS:
        if field not in binding:
            raise OwnerStaAuthorityDecisionErrorV1(f"INSTRUMENT_FIELD_MISSING:{field}")
        field_obj = _require_mapping(binding.get(field), label=f"instrument_binding.{field}")
        if "allowed_options" not in field_obj:
            raise OwnerStaAuthorityDecisionErrorV1(f"INSTRUMENT_FIELD_OPTIONS_MISSING:{field}")
        if "status" not in field_obj:
            raise OwnerStaAuthorityDecisionErrorV1(f"INSTRUMENT_FIELD_STATUS_MISSING:{field}")


def _validate_owner_decision_table(table: Sequence[Any]) -> None:
    seen: set[str] = set()
    for row in table:
        row_map = _require_mapping(row, label="owner_decision_table.row")
        for key in (
            "decision_id",
            "field",
            "allowed_options",
            "recommended_option",
            "rationale",
            "safety_semantic_consequences",
            "owner_value",
            "status",
        ):
            if key not in row_map:
                raise OwnerStaAuthorityDecisionErrorV1(f"DECISION_ROW_MISSING:{key}")
        decision_id = str(row_map.get("decision_id") or "")
        if decision_id in seen:
            raise OwnerStaAuthorityDecisionErrorV1(f"DECISION_ID_DUPLICATE:{decision_id}")
        seen.add(decision_id)
        if row_map.get("status") not in {"OPEN", "RATIFIED", "REJECTED"}:
            raise OwnerStaAuthorityDecisionErrorV1(f"DECISION_STATUS_INVALID:{decision_id}")
    for required_id in C.OWNER_DECISION_TABLE_IDS:
        if required_id not in seen:
            raise OwnerStaAuthorityDecisionErrorV1(f"DECISION_ID_MISSING:{required_id}")


def _reject_forbidden_candle_ref(ref: str) -> None:
    lowered = ref.lower()
    for forbidden in C.FORBIDDEN_CANDLE_SOURCE_REFS:
        if forbidden.lower() in lowered or lowered == forbidden.lower():
            raise OwnerStaAuthorityDecisionErrorV1(f"FORBIDDEN_CANDLE_SOURCE_REF:{forbidden}")
    if "pt1h" in lowered or "/market/candles" == lowered.split("?")[0].rstrip("/").split("v5")[-1]:
        # Explicit open-tip recent candles endpoint and PT1H substitutions.
        if "history-candles" not in lowered:
            raise OwnerStaAuthorityDecisionErrorV1(
                "FORBIDDEN_CANDLE_SOURCE_REF:non_history_or_pt1h"
            )


def _reject_forbidden_mark_ref(ref: str) -> None:
    lowered = ref.lower()
    for forbidden in C.FORBIDDEN_MARK_SOURCE_REFS:
        if forbidden.lower() in lowered or lowered == forbidden.lower():
            raise OwnerStaAuthorityDecisionErrorV1(f"FORBIDDEN_MARK_SOURCE_REF:{forbidden}")
    if "history-mark-price-candles" not in lowered:
        raise OwnerStaAuthorityDecisionErrorV1(
            "FORBIDDEN_MARK_SOURCE_REF:must_be_history_mark_price_candles"
        )


__all__ = [
    "OwnerStaAuthorityDecisionErrorV1",
    "load_canonical_owner_sta_decisions_manifest_v1",
    "validate_owner_sta_authority_manifest_v1",
    "validate_owner_sta_ratification_claim_v1",
]
