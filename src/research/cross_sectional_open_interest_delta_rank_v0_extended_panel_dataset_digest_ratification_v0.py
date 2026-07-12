"""Extended panel dataset digest ratification for cross_sectional_open_interest_delta_rank/v0.

Ratifies the PR5119 materially extended self-accumulated OI panel dataset identity while
preserving unchanged ranking, eligibility, cost, execution, and risk semantics.
Research-only; no runtime or authority effect.
"""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Mapping, Sequence

from src.research.cross_sectional_open_interest_delta_rank_v0_pit_semantics_contract_v0 import (
    LOOKBACK_K,
    SIGNAL_LAG_BARS,
)
from src.research.cross_sectional_open_interest_delta_rank_v0_versioned_research_binding_v0 import (
    AUTHORITY_EFFECT,
    BINDING_SCHEMA_VERSION,
    CONFIG_REL_PATH,
    DATASET_ID,
    ORDER_EFFECT,
    PANEL_DATASET_SCHEMA,
    PANEL_ID,
    RESEARCH_SCOPE,
    RUNTIME_EFFECT,
    STRATEGY_ID,
    STRATEGY_VERSION,
    _stable_digest,
    build_cost_execution_binding_v0,
    build_dataset_binding_v0,
    build_economic_policy_binding_v0,
    build_instrument_binding_v0,
    build_parameter_binding_v0,
    build_period_binding_v0,
    build_pit_universe_binding_v0,
    compute_implementation_digest_v0,
    compute_material_difference_digest_v0,
    materialize_versioned_research_binding_v0,
    pit_semantics_contract_to_dict,
    serialize_versioned_binding_artifact_json_v0,
    validate_versioned_research_binding_v0,
)
from src.research.cross_sectional_open_interest_delta_rank_v0_pit_semantics_contract_v0 import (
    build_pit_open_interest_semantics_contract_v0,
)
from src.research.okx_self_accumulated_forward_open_interest_bound_panel_dataset_materialization_v0 import (
    DATASET_EXTENSION,
    materializer_roundtrip_contract_v0,
)

PACKAGE_MARKER = (
    "CROSS_SECTIONAL_OPEN_INTEREST_DELTA_RANK_V0_EXTENDED_PANEL_DATASET_DIGEST_RATIFICATION_V0=true"
)
MODULE_VERSION = (
    "cross_sectional_open_interest_delta_rank_v0_extended_panel_dataset_digest_ratification.v0"
)
CONFIRM_GO = (
    "GO_CROSS_SECTIONAL_OPEN_INTEREST_DELTA_RANK_V0_EXTENDED_PANEL_DATASET_DIGEST_RATIFICATION_V0"
)
RATIFICATION_CONFIG_REL_PATH = (
    "config/research/"
    "cross_sectional_open_interest_delta_rank_v0_extended_panel_dataset_digest_ratification_v0.json"
)

CURRENT_BINDING_ID = RESEARCH_SCOPE
OLD_BINDING_DIGEST = "c17b68949726fc340575070adb8572e26e63a30c569e73ffc8ca801fe28577ed"
OLD_DATASET_DIGEST = "0f57d48c40f02c3aeec9897ae7f2a43e313c01cff50dab68c8e08f879e0f2687"
OLD_BOUND_DATA_DIGEST = "fd2a020f055120eaa67e0087423333a41cb32b99b95076b18e3c1b50f543844a"
OLD_ARCHIVE_SOURCE_DIGEST = "12647433643badc0944d71a1268969845d32f7d6b52bd4ad843ea557c8ef2cf0"

NEW_DATASET_DIGEST = "37e492d6b2ef64ab681ca96ef5f2fc873d2d4f87c119b3ee2666d8489fc650a1"
NEW_BOUND_DATA_DIGEST = "82e8787c0cc19c15c120de4ee24821bba85b5c5a938b802cfa3f7bcd40f13a4d"
NEW_ARCHIVE_SOURCE_DIGEST = "cb10e99d7cd5fa158a38aec24e095dbd051f447a0665a7fce47bcc13cb44860a"
INSTRUMENT_UNIVERSE_DIGEST = "e286db0053596e771c2168e82ff61c326f7ba1d51e90d606880237576b2c4791"

HISTORY_DEPTH_BEFORE = 6
HISTORY_DEPTH_AFTER = 60
MINIMUM_REQUIRED_HISTORY_DEPTH = 55
FIRST_RANKABLE_EPOCH_INDEX = LOOKBACK_K + SIGNAL_LAG_BARS
EXPECTED_RANKABLE_EPOCH_COUNT = HISTORY_DEPTH_AFTER - FIRST_RANKABLE_EPOCH_INDEX
WINDOW_START_UTC = "2026-07-09T12:00:00Z"
WINDOW_END_UTC = "2026-07-11T23:00:00Z"
BAR_INTERVAL = "PT1H"

SUPERSESSION_MODE = "EXTENDED_PANEL_DATASET_DIGEST_REFRESH_V0"
BINDING_CLASSIFICATION = "UNCHANGED_STRATEGY_RANKING_SEMANTICS_MATERIAL_DATASET_IDENTITY_CHANGE"

DEFAULT_MATERIALIZATION_MANIFEST = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/research/"
    "cross_sectional_open_interest_delta_rank_v0_historical_panel_depth_extension_"
    "and_rematerialization_implementation_v0_20260712T004937Z/materialization/run_a/panel/"
    "panel_open_interest_dataset_manifest.json"
)


class RatificationTerminalStatus(str, Enum):
    RATIFICATION_COMPLETE = "RATIFICATION_COMPLETE"
    VALIDATE_ONLY_PASS = "VALIDATE_ONLY_PASS"
    FAIL_CLOSED_OPERATOR_GO = "FAIL_CLOSED_OPERATOR_GO"
    FAIL_CLOSED_DEFAULT_OFF = "FAIL_CLOSED_DEFAULT_OFF"
    FAIL_CLOSED_DATASET_IDENTITY = "FAIL_CLOSED_DATASET_IDENTITY"
    FAIL_CLOSED_BINDING_VALIDATION = "FAIL_CLOSED_BINDING_VALIDATION"
    FAIL_CLOSED_STALE_DIGEST = "FAIL_CLOSED_STALE_DIGEST"


class FieldClass(str, Enum):
    SEMANTIC_STRATEGY = "SEMANTIC_STRATEGY"
    SEMANTIC_RANKING = "SEMANTIC_RANKING"
    SEMANTIC_ELIGIBILITY = "SEMANTIC_ELIGIBILITY"
    SEMANTIC_COST = "SEMANTIC_COST"
    SEMANTIC_EXECUTION = "SEMANTIC_EXECUTION"
    SEMANTIC_RISK = "SEMANTIC_RISK"
    CRYPTOGRAPHIC_DATASET = "CRYPTOGRAPHIC_DATASET"
    CRYPTOGRAPHIC_BINDING = "CRYPTOGRAPHIC_BINDING"
    OBSERVED_MATERIALIZATION = "OBSERVED_MATERIALIZATION"
    SUPERSESSION = "SUPERSESSION"


@dataclass(frozen=True)
class ExtendedPanelDatasetDigestRatificationResultV0:
    status: RatificationTerminalStatus
    ratified_binding: dict[str, Any]
    binding_digest: str
    old_binding_digest: str
    old_dataset_digest: str
    new_dataset_digest: str
    ratification_roundtrip_pass: bool
    deterministic_ratification: bool
    second_ratification_diff_empty: bool
    unexpected_change_count: int
    unclassified_changed_field_count: int
    reason_codes: tuple[str, ...]


def _field_bound(*, value: Any = None, ref: str = "") -> dict[str, Any]:
    payload: dict[str, Any] = {"status": "BOUND"}
    if value is not None:
        payload["value"] = value
    if ref:
        payload["ref"] = ref
    return payload


def load_observed_dataset_identity_from_manifest_v0(
    manifest_path: Path,
) -> dict[str, Any]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    calendar = manifest.get("panel_calendar_timestamps_utc") or []
    return {
        "dataset_id": manifest.get("dataset_id", DATASET_ID),
        "dataset_schema": manifest.get("panel_dataset_schema", PANEL_DATASET_SCHEMA),
        "panel_id": manifest.get("panel_id", PANEL_ID),
        "dataset_extension": manifest.get("dataset_extension", DATASET_EXTENSION),
        "panel_dataset_digest": str(manifest.get("open_interest_panel_digest", "")),
        "bound_data_digest": str(manifest.get("bound_data_digest", "")),
        "archive_source_digest": str(manifest.get("archive_source_digest", "")),
        "instrument_universe_digest": str(manifest.get("instrument_universe_digest", "")),
        "window_start_utc": manifest.get("panel_calendar_start_utc", ""),
        "window_end_utc": manifest.get("panel_calendar_end_utc", ""),
        "history_depth_after": len(calendar),
        "instrument_ids": list(manifest.get("instrument_ids") or []),
        "manifest_path": str(manifest_path.resolve()),
    }


def verify_expected_extended_dataset_identity_v0(
    observed: Mapping[str, Any],
) -> tuple[bool, tuple[str, ...]]:
    reasons: list[str] = []
    checks = {
        "panel_dataset_digest": NEW_DATASET_DIGEST,
        "bound_data_digest": NEW_BOUND_DATA_DIGEST,
        "archive_source_digest": NEW_ARCHIVE_SOURCE_DIGEST,
        "instrument_universe_digest": INSTRUMENT_UNIVERSE_DIGEST,
        "window_start_utc": WINDOW_START_UTC,
        "window_end_utc": WINDOW_END_UTC,
    }
    for key, expected in checks.items():
        if observed.get(key) != expected:
            reasons.append(f"DATASET_IDENTITY_MISMATCH:{key}")
    if int(observed.get("history_depth_after", 0)) < MINIMUM_REQUIRED_HISTORY_DEPTH:
        reasons.append("INSUFFICIENT_HISTORY_DEPTH")
    if len(observed.get("instrument_ids") or []) != 5:
        reasons.append("INSTRUMENT_COUNT_MISMATCH")
    return not reasons, tuple(reasons)


def build_extended_dataset_binding_v0(
    *,
    panel_dataset_digest: str = NEW_DATASET_DIGEST,
    bound_data_digest: str = NEW_BOUND_DATA_DIGEST,
    archive_source_digest: str = NEW_ARCHIVE_SOURCE_DIGEST,
) -> dict[str, Any]:
    binding = build_dataset_binding_v0()
    binding.update(
        {
            "panel_dataset_digest": panel_dataset_digest,
            "bound_data_digest": bound_data_digest,
            "archive_source_digest": archive_source_digest,
            "observed_panel_window_start_utc": WINDOW_START_UTC,
            "observed_panel_window_end_utc": WINDOW_END_UTC,
            "observed_panel_history_depth": HISTORY_DEPTH_AFTER,
        }
    )
    return binding


def compute_ratified_binding_digest_v0(
    *,
    dataset_binding: Mapping[str, Any],
    data_digest: str,
) -> tuple[str, str]:
    parameter_binding = build_parameter_binding_v0()
    pit_universe_binding = build_pit_universe_binding_v0()
    period_binding = build_period_binding_v0()
    config_digest = _stable_digest(
        {
            "parameter_binding": parameter_binding,
            "pit_universe_binding": pit_universe_binding,
            "dataset_binding": dict(dataset_binding),
            "period_binding": period_binding,
        }
    )
    implementation_digest = compute_implementation_digest_v0()
    binding_digest = _stable_digest(
        {
            "config_digest": config_digest,
            "data_digest": data_digest,
            "implementation_digest": implementation_digest,
        }
    )
    return config_digest, binding_digest


def materialize_extended_panel_ratified_versioned_binding_v0(
    *,
    observed: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    observed = dict(
        observed
        or load_observed_dataset_identity_from_manifest_v0(DEFAULT_MATERIALIZATION_MANIFEST)
    )
    dataset_binding = build_extended_dataset_binding_v0(
        panel_dataset_digest=str(observed["panel_dataset_digest"]),
        bound_data_digest=str(observed["bound_data_digest"]),
        archive_source_digest=str(observed["archive_source_digest"]),
    )
    panel_dataset_binding = dict(dataset_binding)
    parameter_binding = build_parameter_binding_v0()
    pit_universe_binding = build_pit_universe_binding_v0()
    period_binding = build_period_binding_v0()
    instrument_binding = build_instrument_binding_v0()
    cost_binding = build_cost_execution_binding_v0()
    economic_policy = build_economic_policy_binding_v0()
    pit_contract = build_pit_open_interest_semantics_contract_v0()

    config_digest, binding_digest = compute_ratified_binding_digest_v0(
        dataset_binding=dataset_binding,
        data_digest=str(observed["panel_dataset_digest"]),
    )
    implementation_digest = compute_implementation_digest_v0()
    material_difference_digest = compute_material_difference_digest_v0()
    data_digest = str(observed["panel_dataset_digest"])

    binding: dict[str, Any] = {
        "binding_status": {
            "overall_binding_status": "COMPLETE",
            "universe_binding_status": "BOUND",
            "dataset_binding_status": "BOUND",
            "digest_binding_status": "BOUND",
            "numeric_bindings_status": "BOUND",
            "cost_model_binding_status": "BOUND",
            "period_binding_status": "BOUND",
            "policy_classes_status": "BOUND",
        },
        "digest_bindings": {
            "config_digest": _field_bound(value=config_digest),
            "data_digest": _field_bound(value=data_digest),
            "implementation_digest": _field_bound(value=implementation_digest),
            "material_difference_digest": _field_bound(value=material_difference_digest),
            "instrument_universe_digest": _field_bound(value=INSTRUMENT_UNIVERSE_DIGEST),
            "bound_data_digest": _field_bound(value=str(observed["bound_data_digest"])),
        },
        "direction_semantics": materialize_versioned_research_binding_v0()["binding"][
            "direction_semantics"
        ],
        "external_bindings": materialize_versioned_research_binding_v0()["binding"][
            "external_bindings"
        ],
        "parameter_binding": parameter_binding,
        "pit_universe_binding": pit_universe_binding,
        "dataset_binding": dataset_binding,
        "period_binding": period_binding,
        "instrument_binding": instrument_binding,
        "binding_supersession": {
            "supersession_mode": SUPERSESSION_MODE,
            "predecessor_binding_digest": OLD_BINDING_DIGEST,
            "predecessor_data_digest": OLD_DATASET_DIGEST,
            "predecessor_bound_data_digest": OLD_BOUND_DATA_DIGEST,
            "predecessor_archive_source_digest": OLD_ARCHIVE_SOURCE_DIGEST,
            "supersedes_binding_digest": OLD_BINDING_DIGEST,
            "historical_evidence_preserved": True,
            "prior_inconclusive_economic_evidence_preserved": True,
        },
    }

    envelope: dict[str, Any] = {
        "artifact_kind": "cross_sectional_open_interest_delta_rank_v0_versioned_research_binding",
        "artifact_version": "v0",
        "schema_version": BINDING_SCHEMA_VERSION,
        "strategy_id": STRATEGY_ID,
        "strategy_version": STRATEGY_VERSION,
        "research_hypothesis_id": "cross_sectional_open_interest_delta_rank_v0",
        "research_scope": RESEARCH_SCOPE,
        "binding": binding,
        "pit_semantics_contract": pit_semantics_contract_to_dict(pit_contract),
        "parameter_binding": parameter_binding,
        "pit_universe_binding": pit_universe_binding,
        "panel_dataset_binding": panel_dataset_binding,
        "period_binding": period_binding,
        "instrument_binding": instrument_binding,
        "cost_execution_binding": cost_binding,
        "economic_policy_binding": economic_policy,
        "binding_digest": binding_digest,
        "config_digest": config_digest,
        "data_digest": data_digest,
        "instrument_universe_digest": INSTRUMENT_UNIVERSE_DIGEST,
        "extended_panel_dataset_ratification": {
            "ratification_owner": MODULE_VERSION,
            "operator_go": CONFIRM_GO,
            "binding_classification": BINDING_CLASSIFICATION,
            "semantic_binding_fields_changed": False,
            "cryptographic_dataset_identity_changed": True,
            "cryptographic_binding_identity_changed": binding_digest != OLD_BINDING_DIGEST,
            "history_depth_before": HISTORY_DEPTH_BEFORE,
            "history_depth_after": int(observed.get("history_depth_after", HISTORY_DEPTH_AFTER)),
            "expected_rankable_epoch_count": EXPECTED_RANKABLE_EPOCH_COUNT,
            "economic_evaluation_executed": False,
            "economic_validity_offline_gate_pass": False,
            "runtime_rewire_admissible": False,
            "observed_materialization_manifest": observed.get("manifest_path"),
        },
        "system_constraints": {
            "futures_only": True,
            "bitcoin_direction_allowed": False,
            "spot_excluded": True,
            "synthetic_spot_excluded": True,
            "offline_only": True,
            "no_runtime": True,
            "no_parameter_optimization": True,
            "no_policy_rescue": True,
            "no_signal_logic_change": True,
            "no_universe_change": True,
            "dataset_identity_refresh_only": True,
            "no_dataset_semantic_change": True,
        },
        "authority_effect": AUTHORITY_EFFECT,
        "runtime_effect": RUNTIME_EFFECT,
        "order_effect": ORDER_EFFECT,
    }
    return envelope


def build_before_after_field_diff_v0(
    *,
    old_binding: Mapping[str, Any],
    new_binding: Mapping[str, Any],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []

    def add_row(
        *,
        field_path: str,
        old_value: Any,
        new_value: Any,
        field_class: FieldClass,
        canonical_owner: str,
        change_type: str,
        semantic_effect: str,
        cryptographic_effect: str,
        reason: str,
    ) -> None:
        if old_value == new_value:
            return
        rows.append(
            {
                "field_path": field_path,
                "old_value": old_value,
                "new_value": new_value,
                "field_class": field_class.value,
                "canonical_owner": canonical_owner,
                "change_type": change_type,
                "semantic_effect": semantic_effect,
                "cryptographic_effect": cryptographic_effect,
                "reason": reason,
            }
        )

    add_row(
        field_path="data_digest",
        old_value=old_binding.get("data_digest"),
        new_value=new_binding.get("data_digest"),
        field_class=FieldClass.CRYPTOGRAPHIC_DATASET,
        canonical_owner="cross_sectional_open_interest_delta_rank_v0_versioned_research_binding_v0",
        change_type="DATASET_DIGEST_REFRESH",
        semantic_effect="NONE",
        cryptographic_effect="DATASET_IDENTITY_CHANGED",
        reason="PR5119 extended panel rematerialization",
    )
    add_row(
        field_path="binding_digest",
        old_value=old_binding.get("binding_digest"),
        new_value=new_binding.get("binding_digest"),
        field_class=FieldClass.CRYPTOGRAPHIC_BINDING,
        canonical_owner="cross_sectional_open_interest_delta_rank_v0_versioned_research_binding_v0",
        change_type="BINDING_DIGEST_REFRESH",
        semantic_effect="NONE",
        cryptographic_effect="BINDING_IDENTITY_CHANGED",
        reason="Transitive dataset digest in binding digest",
    )
    observed_paths = (
        ("binding.dataset_binding.panel_dataset_digest", FieldClass.CRYPTOGRAPHIC_DATASET),
        ("binding.dataset_binding.bound_data_digest", FieldClass.CRYPTOGRAPHIC_DATASET),
        ("binding.dataset_binding.archive_source_digest", FieldClass.CRYPTOGRAPHIC_DATASET),
        (
            "binding.dataset_binding.observed_panel_window_start_utc",
            FieldClass.OBSERVED_MATERIALIZATION,
        ),
        (
            "binding.dataset_binding.observed_panel_window_end_utc",
            FieldClass.OBSERVED_MATERIALIZATION,
        ),
        (
            "binding.dataset_binding.observed_panel_history_depth",
            FieldClass.OBSERVED_MATERIALIZATION,
        ),
        ("binding.digest_bindings.data_digest.value", FieldClass.CRYPTOGRAPHIC_DATASET),
        ("binding.digest_bindings.bound_data_digest.value", FieldClass.CRYPTOGRAPHIC_DATASET),
        ("config_digest", FieldClass.CRYPTOGRAPHIC_BINDING),
        ("panel_dataset_binding.panel_dataset_digest", FieldClass.CRYPTOGRAPHIC_DATASET),
        ("panel_dataset_binding.bound_data_digest", FieldClass.CRYPTOGRAPHIC_DATASET),
        ("panel_dataset_binding.archive_source_digest", FieldClass.CRYPTOGRAPHIC_DATASET),
    )
    for path, field_class in observed_paths:
        old_val = old_binding
        new_val = new_binding
        for part in path.split("."):
            old_val = (old_val or {}).get(part) if isinstance(old_val, dict) else None
            new_val = (new_val or {}).get(part) if isinstance(new_val, dict) else None
        change_type = (
            "DATASET_DIGEST_REFRESH"
            if "digest" in path
            else "OBSERVED_DEPTH_EXTENSION"
            if "observed_panel" in path
            else "CONFIG_DIGEST_REFRESH"
        )
        add_row(
            field_path=path,
            old_value=old_val,
            new_value=new_val,
            field_class=field_class,
            canonical_owner=(
                "okx_self_accumulated_forward_open_interest_bound_panel_dataset_materialization_v0"
                if field_class is FieldClass.OBSERVED_MATERIALIZATION
                else "cross_sectional_open_interest_delta_rank_v0_versioned_research_binding_v0"
            ),
            change_type=change_type,
            semantic_effect="NONE",
            cryptographic_effect=(
                "DATASET_IDENTITY_CHANGED"
                if field_class is FieldClass.CRYPTOGRAPHIC_DATASET
                else "INDIRECT_BINDING_REFRESH"
            ),
            reason="PR5119 extended panel rematerialization",
        )
    add_row(
        field_path="binding.binding_supersession",
        old_value=old_binding.get("binding", {}).get("binding_supersession"),
        new_value=new_binding.get("binding", {}).get("binding_supersession"),
        field_class=FieldClass.SUPERSESSION,
        canonical_owner=MODULE_VERSION,
        change_type="SUPERSESSION_ADDED",
        semantic_effect="NONE",
        cryptographic_effect="LINEAGE_RECORDED",
        reason="Predecessor preserved per repo contract",
    )
    add_row(
        field_path="extended_panel_dataset_ratification",
        old_value=old_binding.get("extended_panel_dataset_ratification"),
        new_value=new_binding.get("extended_panel_dataset_ratification"),
        field_class=FieldClass.OBSERVED_MATERIALIZATION,
        canonical_owner=MODULE_VERSION,
        change_type="RATIFICATION_METADATA_ADDED",
        semantic_effect="NONE",
        cryptographic_effect="LINEAGE_RECORDED",
        reason="Extended panel ratification metadata recorded",
    )
    add_row(
        field_path="system_constraints.no_dataset_change",
        old_value=old_binding.get("system_constraints", {}).get("no_dataset_change"),
        new_value=new_binding.get("system_constraints", {}).get("no_dataset_change"),
        field_class=FieldClass.OBSERVED_MATERIALIZATION,
        canonical_owner=MODULE_VERSION,
        change_type="CONSTRAINT_REFRESH",
        semantic_effect="NONE",
        cryptographic_effect="NONE",
        reason="Replaced by dataset_identity_refresh_only flag",
    )
    add_row(
        field_path="system_constraints.dataset_identity_refresh_only",
        old_value=old_binding.get("system_constraints", {}).get("dataset_identity_refresh_only"),
        new_value=new_binding.get("system_constraints", {}).get("dataset_identity_refresh_only"),
        field_class=FieldClass.OBSERVED_MATERIALIZATION,
        canonical_owner=MODULE_VERSION,
        change_type="CONSTRAINT_REFRESH",
        semantic_effect="NONE",
        cryptographic_effect="NONE",
        reason="Dataset identity refresh only",
    )
    add_row(
        field_path="system_constraints.no_dataset_semantic_change",
        old_value=old_binding.get("system_constraints", {}).get("no_dataset_semantic_change"),
        new_value=new_binding.get("system_constraints", {}).get("no_dataset_semantic_change"),
        field_class=FieldClass.OBSERVED_MATERIALIZATION,
        canonical_owner=MODULE_VERSION,
        change_type="CONSTRAINT_REFRESH",
        semantic_effect="NONE",
        cryptographic_effect="NONE",
        reason="Dataset semantic unchanged",
    )
    semantic_paths = (
        ("parameter_binding.rank_lookback_k", FieldClass.SEMANTIC_RANKING),
        ("parameter_binding.signal_lag_bars", FieldClass.SEMANTIC_RANKING),
        ("pit_universe_binding.minimum_eligible_member_count", FieldClass.SEMANTIC_ELIGIBILITY),
        ("cost_execution_binding.fee_model_binding.fee_bps_per_side", FieldClass.SEMANTIC_COST),
        (
            "cost_execution_binding.execution_model_binding.execution_model_version",
            FieldClass.SEMANTIC_EXECUTION,
        ),
        ("economic_policy_binding.minimum_trade_count", FieldClass.SEMANTIC_RISK),
    )
    for path, field_class in semantic_paths:
        old_val = old_binding
        new_val = new_binding
        for part in path.split("."):
            old_val = (old_val or {}).get(part, {}) if isinstance(old_val, dict) else None
            new_val = (new_val or {}).get(part, {}) if isinstance(new_val, dict) else None
        if old_val != new_val:
            rows.append(
                {
                    "field_path": path,
                    "old_value": old_val,
                    "new_value": new_val,
                    "field_class": field_class.value,
                    "canonical_owner": "cross_sectional_open_interest_delta_rank_v0_versioned_research_binding_v0",
                    "change_type": "UNEXPECTED_SEMANTIC_CHANGE",
                    "semantic_effect": "CHANGED",
                    "cryptographic_effect": "UNKNOWN",
                    "reason": "Semantic field drift forbidden in this scope",
                }
            )
    return rows


def validate_ratified_extended_binding_v0(
    envelope: Mapping[str, Any],
) -> tuple[bool, tuple[str, ...]]:
    reasons: list[str] = []
    validation_verdict, validation_reasons = validate_versioned_research_binding_v0(envelope)
    if validation_verdict.value != "ACCEPTED_COMPLETE":
        reasons.extend(validation_reasons)

    if envelope.get("data_digest") == OLD_DATASET_DIGEST:
        reasons.append("STALE_DATASET_DIGEST_REJECTED")
    if envelope.get("binding_digest") == OLD_BINDING_DIGEST:
        reasons.append("STALE_BINDING_DIGEST_REJECTED")
    if envelope.get("data_digest") != NEW_DATASET_DIGEST:
        reasons.append("NEW_DATASET_DIGEST_MISMATCH")
    if (
        int(envelope.get("extended_panel_dataset_ratification", {}).get("history_depth_after", 0))
        < MINIMUM_REQUIRED_HISTORY_DEPTH
    ):
        reasons.append("HISTORY_DEPTH_INSUFFICIENT")
    if envelope.get("extended_panel_dataset_ratification", {}).get("economic_evaluation_executed"):
        reasons.append("ECONOMIC_EVALUATION_FORBIDDEN")
    supersession = envelope.get("binding", {}).get("binding_supersession", {})
    if supersession.get("supersedes_binding_digest") != OLD_BINDING_DIGEST:
        reasons.append("SUPERSESSION_PREDECESSOR_MISMATCH")
    return not reasons, tuple(dict.fromkeys(reasons))


def compare_ratification_envelopes_v0(
    first: Mapping[str, Any],
    second: Mapping[str, Any],
) -> tuple[bool, dict[str, Any]]:
    ignore = {"extended_panel_dataset_ratification"}
    first_cmp = {k: v for k, v in first.items() if k not in ignore}
    second_cmp = {k: v for k, v in second.items() if k not in ignore}
    diff = {}
    for key in sorted(set(first_cmp) | set(second_cmp)):
        if first_cmp.get(key) != second_cmp.get(key):
            diff[key] = (first_cmp.get(key), second_cmp.get(key))
    return not diff, {"diff": diff, "diff_empty": not diff}


def ratification_roundtrip_contract_v0(
    envelope: Mapping[str, Any],
) -> dict[str, Any]:
    ok, reasons = validate_ratified_extended_binding_v0(envelope)
    return {
        "ratification_roundtrip_pass": ok,
        "validator_owner": MODULE_VERSION,
        "binding_validator_owner": "cross_sectional_open_interest_delta_rank_v0_versioned_research_binding_v0",
        "materializer_roundtrip_owner": materializer_roundtrip_contract_v0()["materializer_owner"],
        "reason_codes": list(reasons),
    }


def execute_extended_panel_dataset_digest_ratification_v0(
    *,
    confirm: str,
    enabled: bool,
    manifest_path: Path = DEFAULT_MATERIALIZATION_MANIFEST,
    write_repo_config: bool = False,
    repo_root: Path | None = None,
) -> ExtendedPanelDatasetDigestRatificationResultV0:
    if not enabled:
        return ExtendedPanelDatasetDigestRatificationResultV0(
            status=RatificationTerminalStatus.FAIL_CLOSED_DEFAULT_OFF,
            ratified_binding={},
            binding_digest="",
            old_binding_digest=OLD_BINDING_DIGEST,
            old_dataset_digest=OLD_DATASET_DIGEST,
            new_dataset_digest="",
            ratification_roundtrip_pass=False,
            deterministic_ratification=False,
            second_ratification_diff_empty=False,
            unexpected_change_count=0,
            unclassified_changed_field_count=0,
            reason_codes=("DEFAULT_OFF_ENABLED_FLAG_REQUIRED",),
        )
    if confirm != CONFIRM_GO:
        return ExtendedPanelDatasetDigestRatificationResultV0(
            status=RatificationTerminalStatus.FAIL_CLOSED_OPERATOR_GO,
            ratified_binding={},
            binding_digest="",
            old_binding_digest=OLD_BINDING_DIGEST,
            old_dataset_digest=OLD_DATASET_DIGEST,
            new_dataset_digest="",
            ratification_roundtrip_pass=False,
            deterministic_ratification=False,
            second_ratification_diff_empty=False,
            unexpected_change_count=0,
            unclassified_changed_field_count=0,
            reason_codes=("OPERATOR_GO_MISMATCH",),
        )

    observed = load_observed_dataset_identity_from_manifest_v0(manifest_path)
    identity_ok, identity_reasons = verify_expected_extended_dataset_identity_v0(observed)
    if not identity_ok:
        return ExtendedPanelDatasetDigestRatificationResultV0(
            status=RatificationTerminalStatus.FAIL_CLOSED_DATASET_IDENTITY,
            ratified_binding={},
            binding_digest="",
            old_binding_digest=OLD_BINDING_DIGEST,
            old_dataset_digest=OLD_DATASET_DIGEST,
            new_dataset_digest=str(observed.get("panel_dataset_digest", "")),
            ratification_roundtrip_pass=False,
            deterministic_ratification=False,
            second_ratification_diff_empty=False,
            unexpected_change_count=0,
            unclassified_changed_field_count=0,
            reason_codes=identity_reasons,
        )

    old_binding = (
        json.loads((repo_root or Path(".")).joinpath(CONFIG_REL_PATH).read_text(encoding="utf-8"))
        if (repo_root and (repo_root / CONFIG_REL_PATH).is_file())
        else materialize_versioned_research_binding_v0()
    )
    first = materialize_extended_panel_ratified_versioned_binding_v0(observed=observed)
    second = materialize_extended_panel_ratified_versioned_binding_v0(observed=observed)
    diff_empty, _ = compare_ratification_envelopes_v0(first, second)
    roundtrip = ratification_roundtrip_contract_v0(first)
    field_diff = build_before_after_field_diff_v0(old_binding=old_binding, new_binding=first)
    unexpected = [
        row
        for row in field_diff
        if row["change_type"] == "UNEXPECTED_SEMANTIC_CHANGE"
        or row["field_class"]
        not in {
            FieldClass.CRYPTOGRAPHIC_DATASET.value,
            FieldClass.CRYPTOGRAPHIC_BINDING.value,
            FieldClass.OBSERVED_MATERIALIZATION.value,
            FieldClass.SUPERSESSION.value,
        }
    ]
    unclassified = [row for row in field_diff if not row.get("field_class")]
    ok, validation_reasons = validate_ratified_extended_binding_v0(first)
    if not ok:
        return ExtendedPanelDatasetDigestRatificationResultV0(
            status=RatificationTerminalStatus.FAIL_CLOSED_BINDING_VALIDATION,
            ratified_binding=first,
            binding_digest=str(first.get("binding_digest", "")),
            old_binding_digest=OLD_BINDING_DIGEST,
            old_dataset_digest=OLD_DATASET_DIGEST,
            new_dataset_digest=str(first.get("data_digest", "")),
            ratification_roundtrip_pass=roundtrip["ratification_roundtrip_pass"],
            deterministic_ratification=diff_empty,
            second_ratification_diff_empty=diff_empty,
            unexpected_change_count=len(unexpected),
            unclassified_changed_field_count=len(unclassified),
            reason_codes=validation_reasons,
        )

    if write_repo_config and repo_root is not None:
        binding_config_path = repo_root / CONFIG_REL_PATH
        binding_config_path.parent.mkdir(parents=True, exist_ok=True)
        binding_config_path.write_text(
            serialize_versioned_binding_artifact_json_v0(first), encoding="utf-8"
        )

    return ExtendedPanelDatasetDigestRatificationResultV0(
        status=RatificationTerminalStatus.RATIFICATION_COMPLETE,
        ratified_binding=first,
        binding_digest=str(first.get("binding_digest", "")),
        old_binding_digest=OLD_BINDING_DIGEST,
        old_dataset_digest=OLD_DATASET_DIGEST,
        new_dataset_digest=str(first.get("data_digest", "")),
        ratification_roundtrip_pass=bool(roundtrip["ratification_roundtrip_pass"]),
        deterministic_ratification=diff_empty,
        second_ratification_diff_empty=diff_empty,
        unexpected_change_count=len(unexpected),
        unclassified_changed_field_count=len(unclassified),
        reason_codes=(),
    )


def build_ratification_config_v0() -> dict[str, Any]:
    return {
        "schema_version": MODULE_VERSION,
        "go_token": CONFIRM_GO,
        "ratification_owner": MODULE_VERSION,
        "binding_owner": "cross_sectional_open_interest_delta_rank_v0_versioned_research_binding_v0",
        "dataset_owner": "okx_self_accumulated_forward_open_interest_bound_panel_dataset_materialization_v0",
        "digest_owner": "cross_sectional_open_interest_delta_rank_v0_versioned_research_binding_v0",
        "supersession_mode": SUPERSESSION_MODE,
        "old_binding_digest": OLD_BINDING_DIGEST,
        "old_dataset_digest": OLD_DATASET_DIGEST,
        "reuse_decision": "REUSE_WITH_NARROW_ADAPTER",
        "authority_effect": AUTHORITY_EFFECT,
        "runtime_effect": RUNTIME_EFFECT,
    }


def result_to_dict_v0(result: ExtendedPanelDatasetDigestRatificationResultV0) -> dict[str, Any]:
    return {
        "status": result.status.value,
        "binding_digest": result.binding_digest,
        "old_binding_digest": result.old_binding_digest,
        "old_dataset_digest": result.old_dataset_digest,
        "new_dataset_digest": result.new_dataset_digest,
        "ratification_roundtrip_pass": result.ratification_roundtrip_pass,
        "deterministic_ratification": result.deterministic_ratification,
        "second_ratification_diff_empty": result.second_ratification_diff_empty,
        "unexpected_change_count": result.unexpected_change_count,
        "unclassified_changed_field_count": result.unclassified_changed_field_count,
        "reason_codes": list(result.reason_codes),
        "authority_effect": AUTHORITY_EFFECT,
        "runtime_effect": RUNTIME_EFFECT,
    }
