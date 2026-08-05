"""Fail-closed validator for Surface-B Owner/STA regime-coverage producer decision.

Records authorize-detail completion and dedicated producer implementation while
keeping INPUT_AUTHORITY, pack materialization, campaign start, productive
numeric invention, and existing-producer elevation closed.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Mapping, Sequence

from src.ops.productive_pure_stack_stage2_surface_b_owner_sta_regime_coverage_producer_decision_v1 import (
    constants_v1 as C,
)

_NUMERIC_VALUE_RE = re.compile(
    r"(?i)(?<![\w/])(?:threshold|lookback|coverage[_ ]?count|bucket[_ ]?size|"
    r"window[_ ]?size|regime[_ ]?pct|coverage[_ ]?pct)\s*[:=]\s*"
    r"(?:0|[1-9]\d*(?:\.\d+)?)"
)


class RegimeCoverageProducerDecisionErrorV1(ValueError):
    """Fail-closed regime-coverage producer decision error."""


def _require_mapping(raw: Any, *, label: str) -> Mapping[str, Any]:
    if not isinstance(raw, Mapping):
        raise RegimeCoverageProducerDecisionErrorV1(f"MAPPING_REQUIRED:{label}")
    return raw


def _assert_false(value: Any, *, label: str) -> None:
    if value is True:
        raise RegimeCoverageProducerDecisionErrorV1(f"MUST_REMAIN_FALSE:{label}")
    if value not in (False, None):
        if bool(value):
            raise RegimeCoverageProducerDecisionErrorV1(f"MUST_REMAIN_FALSE:{label}")


def _assert_null(value: Any, *, label: str) -> None:
    if value is not None:
        raise RegimeCoverageProducerDecisionErrorV1(f"MUST_REMAIN_NULL:{label}")


def _assert_no_forbidden_producer_token(token: Any, *, label: str) -> None:
    text = str(token or "").strip().lower()
    if not text:
        return
    for forbidden in C.FORBIDDEN_EXISTING_PRODUCER_TOKENS:
        if forbidden.lower() in text:
            raise RegimeCoverageProducerDecisionErrorV1(
                f"EXISTING_PRODUCER_ELEVATION_FORBIDDEN:{forbidden}:{label}"
            )
    for forbidden in C.FORBIDDEN_SOURCE_TOKENS:
        if forbidden.lower() in text:
            raise RegimeCoverageProducerDecisionErrorV1(f"FORBIDDEN_SOURCE:{forbidden}:{label}")


def load_canonical_regime_coverage_producer_decisions_manifest_v1(
    repo_root: Path | str | None = None,
) -> dict[str, Any]:
    root = Path(repo_root) if repo_root is not None else Path(__file__).resolve().parents[3]
    path = root / C.DECISIONS_MANIFEST_REL
    if not path.is_file():
        raise RegimeCoverageProducerDecisionErrorV1(f"MANIFEST_MISSING:{C.DECISIONS_MANIFEST_REL}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RegimeCoverageProducerDecisionErrorV1("MANIFEST_MUST_BE_OBJECT")
    return payload


def _validate_authorize_detail_fields_complete(detail_fields: Mapping[str, Any]) -> None:
    for field in C.AUTHORIZE_DETAIL_FIELDS:
        if field not in detail_fields:
            raise RegimeCoverageProducerDecisionErrorV1(f"AUTHORIZE_DETAIL_FIELD_MISSING:{field}")
        expected = C.AUTHORIZE_DETAIL_FIELD_VALUES[field]
        value = detail_fields.get(field)
        if value != expected:
            raise RegimeCoverageProducerDecisionErrorV1(f"AUTHORIZE_DETAIL_FIELD_MISMATCH:{field}")
        if not isinstance(value, str) or not value.strip():
            raise RegimeCoverageProducerDecisionErrorV1(
                f"AUTHORIZE_DETAIL_FIELD_MUST_BE_NONEMPTY_STRING:{field}"
            )
        _assert_no_forbidden_producer_token(value, label=f"authorize_detail_fields.{field}")


def validate_regime_coverage_producer_manifest_v1(
    manifest: Mapping[str, Any],
    *,
    require_open_status: bool | None = None,
) -> dict[str, Any]:
    """Validate the canonical regime-coverage producer decision surface.

    When ``require_open_status`` is None, mode is inferred from ``status``.
    Canonical HEAD mode after this capability is authorize-details-complete.
    """
    for key in C.REQUIRED_MANIFEST_TOP_KEYS:
        if key not in manifest:
            raise RegimeCoverageProducerDecisionErrorV1(f"MANIFEST_MISSING_KEY:{key}")

    if manifest.get("schema_version") != C.SCHEMA_VERSION:
        raise RegimeCoverageProducerDecisionErrorV1("SCHEMA_VERSION_MISMATCH")
    if manifest.get("document_type") != C.DOCUMENT_TYPE:
        raise RegimeCoverageProducerDecisionErrorV1("DOCUMENT_TYPE_MISMATCH")
    if manifest.get("capability_scope") != C.CAPABILITY_SCOPE:
        raise RegimeCoverageProducerDecisionErrorV1("CAPABILITY_SCOPE_MISMATCH")
    if manifest.get("authority_surface") != C.AUTHORITY_SURFACE:
        raise RegimeCoverageProducerDecisionErrorV1("AUTHORITY_SURFACE_MUST_BE_B")
    if str(manifest.get("baseline_origin_main_sha") or "") != C.BASELINE_ORIGIN_MAIN_SHA:
        raise RegimeCoverageProducerDecisionErrorV1("BASELINE_ORIGIN_MAIN_SHA_MISMATCH")

    if manifest.get("decision_id") != C.DECISION_ID:
        raise RegimeCoverageProducerDecisionErrorV1("DECISION_ID_MISMATCH")

    allowed = manifest.get("allowed_owner_values")
    if not isinstance(allowed, Sequence) or isinstance(allowed, (str, bytes)):
        raise RegimeCoverageProducerDecisionErrorV1("ALLOWED_OWNER_VALUES_MUST_BE_SEQUENCE")
    if tuple(allowed) != C.ALLOWED_OWNER_VALUES:
        raise RegimeCoverageProducerDecisionErrorV1("ALLOWED_OWNER_VALUES_MISMATCH")

    taxonomy = manifest.get("taxonomy_sink_labels")
    if not isinstance(taxonomy, Sequence) or isinstance(taxonomy, (str, bytes)):
        raise RegimeCoverageProducerDecisionErrorV1("TAXONOMY_SINK_MUST_BE_SEQUENCE")
    if tuple(taxonomy) != C.TAXONOMY_SINK_LABELS:
        raise RegimeCoverageProducerDecisionErrorV1("TAXONOMY_SINK_MISMATCH")

    _assert_false(manifest.get("input_authority"), label="input_authority")
    _assert_false(manifest.get("runtime_implemented"), label="runtime_implemented")
    _assert_false(manifest.get("campaign_start_authorized"), label="campaign_start_authorized")
    _assert_false(
        manifest.get("raw_input_pack_materialization_authorized"),
        label="raw_input_pack_materialization_authorized",
    )
    _assert_false(manifest.get("raw_input_pack_created"), label="raw_input_pack_created")
    _assert_false(manifest.get("campaign_started"), label="campaign_started")
    _assert_false(manifest.get("existing_producers_elevated"), label="existing_producers_elevated")

    if int(manifest.get("productive_numeric_values_set", -1)) != 0:
        raise RegimeCoverageProducerDecisionErrorV1("PRODUCTIVE_NUMERIC_VALUES_MUST_REMAIN_ZERO")

    if manifest.get("dashboard_authority_effect") != "NONE":
        raise RegimeCoverageProducerDecisionErrorV1("DASHBOARD_AUTHORITY_MUST_BE_NONE")
    if manifest.get("notion_ssot") is True:
        raise RegimeCoverageProducerDecisionErrorV1("NOTION_SSOT_MUST_REMAIN_FALSE")
    if manifest.get("repository_is_ssot") is False:
        raise RegimeCoverageProducerDecisionErrorV1("REPOSITORY_MUST_REMAIN_SSOT")
    if manifest.get("regime_coverage_producer_available") is not False:
        raise RegimeCoverageProducerDecisionErrorV1(
            "REGIME_COVERAGE_PRODUCER_MUST_REMAIN_UNAVAILABLE"
        )
    if manifest.get("regime_coverage_status") != C.REGIME_COVERAGE_STATUS:
        raise RegimeCoverageProducerDecisionErrorV1(
            "REGIME_COVERAGE_MUST_REMAIN_SEMANTICALLY_UNRESOLVED"
        )

    detail_fields = _require_mapping(
        manifest.get("authorize_detail_fields"), label="authorize_detail_fields"
    )
    open_fields = _require_mapping(
        manifest.get("open_null_instance_fields"), label="open_null_instance_fields"
    )
    for key in C.NULL_INSTANCE_KEYS:
        if key not in open_fields:
            raise RegimeCoverageProducerDecisionErrorV1(f"OPEN_NULL_FIELD_MISSING:{key}")
        _assert_null(open_fields.get(key), label=f"open_null_instance_fields.{key}")

    forbidden_producers = manifest.get("forbidden_existing_producers")
    if not isinstance(forbidden_producers, Sequence) or isinstance(
        forbidden_producers, (str, bytes)
    ):
        raise RegimeCoverageProducerDecisionErrorV1("FORBIDDEN_EXISTING_PRODUCERS_MUST_BE_SEQUENCE")
    for token in forbidden_producers:
        if not isinstance(token, str) or not token.strip():
            raise RegimeCoverageProducerDecisionErrorV1("FORBIDDEN_EXISTING_PRODUCER_TOKEN_INVALID")

    sta_inputs = manifest.get("sta_open_external_inputs")
    if not isinstance(sta_inputs, Sequence) or isinstance(sta_inputs, (str, bytes)):
        raise RegimeCoverageProducerDecisionErrorV1("STA_OPEN_EXTERNAL_INPUTS_MUST_BE_SEQUENCE")
    if tuple(sta_inputs) != C.STA_OPEN_EXTERNAL_INPUTS:
        raise RegimeCoverageProducerDecisionErrorV1("STA_OPEN_EXTERNAL_INPUTS_MISMATCH")

    sta_closed = manifest.get("sta_closed_by_open_inputs_closeout")
    if not isinstance(sta_closed, Sequence) or isinstance(sta_closed, (str, bytes)):
        raise RegimeCoverageProducerDecisionErrorV1(
            "STA_CLOSED_BY_OPEN_INPUTS_CLOSEOUT_MUST_BE_SEQUENCE"
        )
    if tuple(sta_closed) != C.STA_CLOSED_BY_OPEN_INPUTS_CLOSEOUT:
        raise RegimeCoverageProducerDecisionErrorV1("STA_CLOSED_BY_OPEN_INPUTS_CLOSEOUT_MISMATCH")

    sta_satisfied = manifest.get("sta_satisfied_by_producer_impl")
    if not isinstance(sta_satisfied, Sequence) or isinstance(sta_satisfied, (str, bytes)):
        raise RegimeCoverageProducerDecisionErrorV1(
            "STA_SATISFIED_BY_PRODUCER_IMPL_MUST_BE_SEQUENCE"
        )
    if tuple(sta_satisfied) != C.STA_SATISFIED_BY_PRODUCER_IMPL:
        raise RegimeCoverageProducerDecisionErrorV1("STA_SATISFIED_BY_PRODUCER_IMPL_MISMATCH")

    reject_sem = _require_mapping(manifest.get("reject_semantics"), label="reject_semantics")
    for key, expected in (
        ("regime_coverage_materializable", False),
        ("surface_b_campaign_startable_while_regime_coverage_required", False),
        ("existing_observability_research_bridge_dashboard_may_substitute_authority", False),
        ("instance_fields_and_coverage_counts_remain_null_or_absent", True),
    ):
        if reject_sem.get(key) is not expected:
            raise RegimeCoverageProducerDecisionErrorV1(f"REJECT_SEMANTICS_INVALID:{key}")

    authorize_sem = _require_mapping(
        manifest.get("authorize_semantics"), label="authorize_semantics"
    )
    for key, expected in (
        ("input_authority", False),
        ("runtime_implemented", False),
        ("raw_input_pack_created", False),
        ("campaign_started", False),
        ("separate_explicit_implementation_order_required", False),
        ("authorize_detail_fields_complete", True),
        ("dedicated_producer_implemented", True),
        ("owner_fields_and_sta_proofs_must_be_fully_ratified_before_input_authority", True),
    ):
        if authorize_sem.get(key) is not expected:
            raise RegimeCoverageProducerDecisionErrorV1(f"AUTHORIZE_SEMANTICS_INVALID:{key}")

    decisions = _require_mapping(manifest.get("decisions"), label="decisions")
    for key in (
        "REGIME_COVERAGE_PRODUCER",
        "FORBIDDEN_EXISTING_PRODUCERS",
        "NON_EFFECTS",
    ):
        if key not in decisions:
            raise RegimeCoverageProducerDecisionErrorV1(f"DECISIONS_MISSING:{key}")

    producer_dec = _require_mapping(
        decisions.get("REGIME_COVERAGE_PRODUCER"), label="REGIME_COVERAGE_PRODUCER"
    )
    if producer_dec.get("decision_id") != C.DECISION_ID:
        raise RegimeCoverageProducerDecisionErrorV1("DECISIONS_DECISION_ID_MISMATCH")
    if tuple(producer_dec.get("allowed_owner_values") or ()) != C.ALLOWED_OWNER_VALUES:
        raise RegimeCoverageProducerDecisionErrorV1("DECISIONS_ALLOWED_OWNER_VALUES_MISMATCH")
    if tuple(producer_dec.get("taxonomy_sink_labels") or ()) != C.TAXONOMY_SINK_LABELS:
        raise RegimeCoverageProducerDecisionErrorV1("DECISIONS_TAXONOMY_SINK_MISMATCH")
    if producer_dec.get("dedicated_producer_package") != C.PRODUCER_PACKAGE_REL:
        raise RegimeCoverageProducerDecisionErrorV1("DEDICATED_PRODUCER_PACKAGE_MISMATCH")
    if producer_dec.get("invent_counts_or_labels") is not False:
        raise RegimeCoverageProducerDecisionErrorV1("INVENT_COUNTS_OR_LABELS_MUST_REMAIN_FALSE")
    if producer_dec.get("new_classifier_implemented") is not False:
        raise RegimeCoverageProducerDecisionErrorV1(
            "NEW_CLASSIFIER_WITH_THRESHOLDS_MUST_REMAIN_FALSE"
        )

    non_effects = _require_mapping(decisions.get("NON_EFFECTS"), label="NON_EFFECTS")
    for key in (
        "input_authority",
        "runtime_implemented",
        "raw_input_pack_created",
        "raw_input_pack_materialization_authorized",
        "campaign_started",
        "campaign_start_authorized",
        "existing_producers_elevated",
        "trading_logic_changed",
        "orders_testnet_live_paper_effects",
        "exchange_credential_effects",
    ):
        if non_effects.get(key) is not False:
            raise RegimeCoverageProducerDecisionErrorV1(f"NON_EFFECTS_MUST_BE_FALSE:{key}")
    if non_effects.get("productive_numeric_values_set") != 0:
        raise RegimeCoverageProducerDecisionErrorV1(
            "NON_EFFECTS_PRODUCTIVE_NUMERIC_VALUES_MUST_BE_ZERO"
        )
    if non_effects.get("dashboard_authority_effect") != "NONE":
        raise RegimeCoverageProducerDecisionErrorV1("NON_EFFECTS_DASHBOARD_AUTHORITY_MUST_BE_NONE")
    if non_effects.get("regime_coverage_status") != C.REGIME_COVERAGE_STATUS:
        raise RegimeCoverageProducerDecisionErrorV1("NON_EFFECTS_REGIME_COVERAGE_STATUS_INVALID")

    owner_value = manifest.get("owner_value")
    decision_status = manifest.get("decision_status")
    surface_status = manifest.get("status")

    if require_open_status is None:
        require_open_status = surface_status == C.STATUS_SURFACE_OPEN

    authorize_details_complete = False
    if require_open_status:
        if surface_status != C.STATUS_SURFACE_OPEN:
            raise RegimeCoverageProducerDecisionErrorV1("STATUS_MUST_REMAIN_SURFACE_OPEN")
        if decision_status != C.DECISION_STATUS_OPEN:
            raise RegimeCoverageProducerDecisionErrorV1("DECISION_STATUS_MUST_REMAIN_OPEN")
        _assert_null(owner_value, label="owner_value")
        _assert_null(producer_dec.get("owner_value"), label="decisions.owner_value")
        if producer_dec.get("status") != C.DECISION_STATUS_OPEN:
            raise RegimeCoverageProducerDecisionErrorV1("DECISIONS_STATUS_MUST_REMAIN_OPEN")
        for field in C.AUTHORIZE_DETAIL_FIELDS:
            _assert_null(detail_fields.get(field), label=f"authorize_detail_fields.{field}")
    elif surface_status == C.STATUS_OWNER_VALUE_RECORDED:
        if decision_status != C.DECISION_STATUS_RATIFIED:
            raise RegimeCoverageProducerDecisionErrorV1("DECISION_STATUS_MUST_BE_RATIFIED")
        if owner_value != C.RECORDED_OWNER_VALUE:
            raise RegimeCoverageProducerDecisionErrorV1("OWNER_VALUE_MISMATCH")
        if producer_dec.get("owner_value") != C.RECORDED_OWNER_VALUE:
            raise RegimeCoverageProducerDecisionErrorV1("DECISIONS_OWNER_VALUE_MISMATCH")
        if producer_dec.get("status") != C.DECISION_STATUS_RATIFIED:
            raise RegimeCoverageProducerDecisionErrorV1("DECISIONS_STATUS_MUST_BE_RATIFIED")
        if str(manifest.get("owner_go_base_sha") or "") != C.OWNER_GO_BASE_SHA:
            raise RegimeCoverageProducerDecisionErrorV1("OWNER_GO_BASE_SHA_MISMATCH")
        for field in C.AUTHORIZE_DETAIL_FIELDS:
            _assert_null(detail_fields.get(field), label=f"authorize_detail_fields.{field}")
        _assert_no_forbidden_producer_token(owner_value, label="owner_value")
    else:
        if surface_status not in (
            C.STATUS_AUTHORIZE_DETAILS_COMPLETE,
            C.STATUS_STA_OPEN_INPUTS_CLOSED,
        ):
            raise RegimeCoverageProducerDecisionErrorV1(
                "STATUS_MUST_BE_AUTHORIZE_DETAIL_FIELDS_COMPLETE_OR_STA_OPEN_INPUTS_CLOSED"
            )
        if decision_status != C.DECISION_STATUS_RATIFIED:
            raise RegimeCoverageProducerDecisionErrorV1("DECISION_STATUS_MUST_BE_RATIFIED")
        if owner_value != C.RECORDED_OWNER_VALUE:
            raise RegimeCoverageProducerDecisionErrorV1("OWNER_VALUE_MISMATCH")
        if producer_dec.get("owner_value") != C.RECORDED_OWNER_VALUE:
            raise RegimeCoverageProducerDecisionErrorV1("DECISIONS_OWNER_VALUE_MISMATCH")
        if producer_dec.get("status") != C.DECISION_STATUS_RATIFIED:
            raise RegimeCoverageProducerDecisionErrorV1("DECISIONS_STATUS_MUST_BE_RATIFIED")
        if str(manifest.get("owner_go_base_sha") or "") != C.OWNER_GO_BASE_SHA:
            raise RegimeCoverageProducerDecisionErrorV1("OWNER_GO_BASE_SHA_MISMATCH")
        if str(manifest.get("owner_impl_go_base_sha") or "") != C.OWNER_IMPL_GO_BASE_SHA:
            raise RegimeCoverageProducerDecisionErrorV1("OWNER_IMPL_GO_BASE_SHA_MISMATCH")
        if surface_status == C.STATUS_STA_OPEN_INPUTS_CLOSED:
            if (
                str(manifest.get("owner_sta_open_inputs_closeout_go_base_sha") or "")
                != C.OWNER_STA_OPEN_INPUTS_CLOSEOUT_GO_BASE_SHA
            ):
                raise RegimeCoverageProducerDecisionErrorV1(
                    "OWNER_STA_OPEN_INPUTS_CLOSEOUT_GO_BASE_SHA_MISMATCH"
                )
            if tuple(manifest.get("sta_open_external_inputs") or ()) != ():
                raise RegimeCoverageProducerDecisionErrorV1(
                    "STA_OPEN_EXTERNAL_INPUTS_MUST_BE_EMPTY_AFTER_CLOSEOUT"
                )
            if tuple(manifest.get("sta_closed_by_open_inputs_closeout") or ()) != (
                C.STA_CLOSED_BY_OPEN_INPUTS_CLOSEOUT
            ):
                raise RegimeCoverageProducerDecisionErrorV1(
                    "STA_CLOSED_BY_OPEN_INPUTS_CLOSEOUT_MISMATCH"
                )
        _validate_authorize_detail_fields_complete(detail_fields)
        authorize_details_complete = True
        _assert_no_forbidden_producer_token(owner_value, label="owner_value")

    _reject_invented_numeric_payload(manifest)

    return {
        "ok": True,
        "capability_scope": C.CAPABILITY_SCOPE,
        "decision_id": C.DECISION_ID,
        "status": surface_status,
        "decision_status": decision_status,
        "owner_value": owner_value,
        "allowed_owner_values": list(C.ALLOWED_OWNER_VALUES),
        "authorize_detail_fields_null": not authorize_details_complete,
        "authorize_detail_fields_complete": authorize_details_complete,
        "existing_producers_elevated": False,
        "input_authority": False,
        "runtime_implemented": False,
        "raw_input_pack_created": False,
        "raw_input_pack_materialization_authorized": False,
        "campaign_started": False,
        "campaign_start_authorized": False,
        "productive_numeric_values_set": 0,
        "regime_coverage_status": C.REGIME_COVERAGE_STATUS,
        "dashboard_authority_effect": "NONE",
        "notion_ssot": False,
        "repository_is_ssot": True,
    }


def validate_regime_coverage_owner_choice_v1(
    owner_value: Any,
    *,
    authorize_detail_fields: Mapping[str, Any] | None = None,
    claim: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Fail-closed gate for an Owner choice against the decision surface.

    Accepts only the two allowed owner values. Does not flip input authority,
    implement runtime, invent counts, elevate existing producers, or authorize
    pack/campaign effects.
    """
    if owner_value not in C.ALLOWED_OWNER_VALUES:
        raise RegimeCoverageProducerDecisionErrorV1("OWNER_VALUE_NOT_ALLOWED")

    details = authorize_detail_fields or {}
    if not isinstance(details, Mapping):
        raise RegimeCoverageProducerDecisionErrorV1("AUTHORIZE_DETAIL_FIELDS_MUST_BE_MAPPING")

    if owner_value == C.AUTHORIZE_OWNER_VALUE:
        if details:
            _validate_authorize_detail_fields_complete(details)
        else:
            for field in C.AUTHORIZE_DETAIL_FIELDS:
                value = details.get(field)
                _assert_null(value, label=f"authorize_detail_fields.{field}")
    else:
        for field, value in details.items():
            _assert_null(value, label=f"reject.authorize_detail_fields.{field}")

    claim_map = claim or {}
    _assert_false(claim_map.get("input_authority"), label="claim.input_authority")
    _assert_false(claim_map.get("runtime_implemented"), label="claim.runtime_implemented")
    _assert_false(claim_map.get("raw_input_pack_created"), label="claim.raw_input_pack_created")
    _assert_false(
        claim_map.get("raw_input_pack_materialization_authorized"),
        label="claim.raw_input_pack_materialization_authorized",
    )
    _assert_false(claim_map.get("campaign_started"), label="claim.campaign_started")
    _assert_false(
        claim_map.get("campaign_start_authorized"),
        label="claim.campaign_start_authorized",
    )
    _assert_false(
        claim_map.get("existing_producers_elevated"),
        label="claim.existing_producers_elevated",
    )
    if claim_map.get("dashboard_authority_effect") not in (None, "NONE"):
        raise RegimeCoverageProducerDecisionErrorV1("DASHBOARD_AUTHORITY_MUST_BE_NONE")
    if claim_map.get("canonical_producer") is not None:
        _assert_no_forbidden_producer_token(
            claim_map.get("canonical_producer"), label="claim.canonical_producer"
        )
    if "coverage_counts" in claim_map and claim_map.get("coverage_counts") is not None:
        raise RegimeCoverageProducerDecisionErrorV1("COVERAGE_COUNTS_MUST_REMAIN_NULL")
    if claim_map.get("productive_numeric_values_set") not in (None, 0):
        raise RegimeCoverageProducerDecisionErrorV1("PRODUCTIVE_NUMERIC_VALUES_MUST_REMAIN_ZERO")

    return {
        "ok": True,
        "owner_value": owner_value,
        "input_authority": False,
        "runtime_implemented": False,
        "raw_input_pack_created": False,
        "campaign_started": False,
        "existing_producers_elevated": False,
        "regime_coverage_status": C.REGIME_COVERAGE_STATUS,
        "dashboard_authority_effect": "NONE",
    }


def _reject_invented_numeric_payload(manifest: Mapping[str, Any]) -> None:
    blob = json.dumps(manifest, sort_keys=True, ensure_ascii=True)
    if _NUMERIC_VALUE_RE.search(blob):
        raise RegimeCoverageProducerDecisionErrorV1(
            "PRODUCTIVE_OR_INVENTED_NUMERIC_VALUES_FORBIDDEN"
        )
    decisions = _require_mapping(manifest.get("decisions"), label="decisions")
    producer_dec = _require_mapping(
        decisions.get("REGIME_COVERAGE_PRODUCER"), label="REGIME_COVERAGE_PRODUCER"
    )
    for key in ("coverage_counts", "thresholds", "lookbacks", "label_magnitudes"):
        if key in producer_dec and producer_dec.get(key) is not None:
            raise RegimeCoverageProducerDecisionErrorV1(
                f"INVENTED_NUMERIC_OR_COUNT_FORBIDDEN:{key}"
            )


__all__ = [
    "RegimeCoverageProducerDecisionErrorV1",
    "load_canonical_regime_coverage_producer_decisions_manifest_v1",
    "validate_regime_coverage_producer_manifest_v1",
    "validate_regime_coverage_owner_choice_v1",
]
