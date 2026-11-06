"""Cap 2.2 offline MVR threshold-set and evidence-harness contract V1.

Persists the injected Policy-B threshold-set contract and the
deterministic offline evidence harness. Does not ratify a Policy-B
threshold, does not wire productive economic ranking, does not close
PDF Step 5, and does not grant runtime authority.
"""

from __future__ import annotations

from typing import Any, Mapping

from src.ops.cap22_offline_mvr_evidence_harness_v1 import constants_v1 as c

CONTRACT_ID = c.CONTRACT_ID
SCHEMA_VERSION = c.HARNESS_VERSION
OWNER_GO_THIS_SLICE = c.OWNER_GO_THIS_SLICE
BOUND_ORIGIN_MAIN_SHA = c.BOUND_ORIGIN_MAIN_SHA
AUTHORITY_EFFECT = c.AUTHORITY_EFFECT
PRODUCTIVE_SELECTION_OWNER = c.PRODUCTIVE_SELECTION_OWNER

POLICY_B_THRESHOLD_MODE = c.POLICY_B_THRESHOLD_MODE
POLICY_B_THRESHOLD_SET_ID = c.POLICY_B_THRESHOLD_SET_ID
POLICY_B_THRESHOLD_SET_RATIFIED = c.POLICY_B_THRESHOLD_SET_RATIFIED
POLICY_B_SINGLE_THRESHOLD_RATIFIED = c.POLICY_B_SINGLE_THRESHOLD_RATIFIED
AUTHORITATIVE_POLICY_B_THRESHOLD_SCALE_FOUND = c.AUTHORITATIVE_POLICY_B_THRESHOLD_SCALE_FOUND
POLICY_B_TEST_ONLY_VALUES_USED = c.POLICY_B_TEST_ONLY_VALUES_USED

CHALLENGER_A_POLICY_ID = c.CHALLENGER_A_POLICY_ID
CHALLENGER_B_POLICY_ID = c.CHALLENGER_B_POLICY_ID
CHALLENGER_C_POLICY_ID = c.CHALLENGER_C_POLICY_ID
CHALLENGER_D_POLICY_ID = c.CHALLENGER_D_POLICY_ID
NEGATIVE_CONTROL_POLICY_ID = c.NEGATIVE_CONTROL_POLICY_ID
OFFLINE_CHALLENGER_A_IS_NOT_ANTI_CHURN_POLICY_A = c.OFFLINE_CHALLENGER_A_IS_NOT_ANTI_CHURN_POLICY_A
ANTI_CHURN_POLICY_A_UNCHANGED = c.ANTI_CHURN_POLICY_A_UNCHANGED
POLICY_A_ROLE = c.POLICY_A_ROLE

NEAR_ZERO_THRESHOLD_RATIFIED = c.NEAR_ZERO_THRESHOLD_RATIFIED
FINAL_SCORE_FORMULA_RATIFIED = c.FINAL_SCORE_FORMULA_RATIFIED
FINAL_WEIGHTS_RATIFIED = c.FINAL_WEIGHTS_RATIFIED
CROSS_SECTIONAL_NORMALIZATION_RATIFIED = c.CROSS_SECTIONAL_NORMALIZATION_RATIFIED
STALE_SECONDS_RATIFIED = c.STALE_SECONDS_RATIFIED
COLLECTION_SKEW_NUMERIC_BOUND_RATIFIED = c.COLLECTION_SKEW_NUMERIC_BOUND_RATIFIED
RANKING_CADENCE_RATIFIED = c.RANKING_CADENCE_RATIFIED
FORWARD_LABEL_HORIZON_RATIFIED = c.FORWARD_LABEL_HORIZON_RATIFIED
HISTORICAL_REPLAY_HORIZON_RATIFIED = c.HISTORICAL_REPLAY_HORIZON_RATIFIED
POLICY_RATIFICATION_JUSTIFIED = c.POLICY_RATIFICATION_JUSTIFIED
NO_CHALLENGER_WINS_BY_THIS_SLICE = c.NO_CHALLENGER_WINS_BY_THIS_SLICE
NO_OFFLINE_POLICY_CLASS_HAS_PRODUCTIVE_AUTHORITY = (
    c.NO_OFFLINE_POLICY_CLASS_HAS_PRODUCTIVE_AUTHORITY
)

ECONOMIC_MD_PRODUCER_IMPLEMENTED = c.ECONOMIC_MD_PRODUCER_IMPLEMENTED
ECONOMIC_MD_PRODUCER_PRODUCTIVELY_SCHEDULED = c.ECONOMIC_MD_PRODUCER_PRODUCTIVELY_SCHEDULED
CAP22_PRODUCTIVE_ECONOMIC_RUNTIME_WIRED = c.CAP22_PRODUCTIVE_ECONOMIC_RUNTIME_WIRED
ECONOMIC_RANK_ACTIVATED = c.ECONOMIC_RANK_ACTIVATED
PDF_STEP_5_STATUS = c.PDF_STEP_5_STATUS
ROTATION_POLICY_STATUS = c.ROTATION_POLICY_STATUS
PDF_STEP_7_STATUS = c.PDF_STEP_7_STATUS
PDF_STEP_7_RUNTIME_IMPLEMENTATION_ALLOWED = c.PDF_STEP_7_RUNTIME_IMPLEMENTATION_ALLOWED
RUNTIME_AUTHORITY_GRANTED = c.RUNTIME_AUTHORITY_GRANTED
PRODUCTIVE_MF_HOST_JOIN = c.PRODUCTIVE_MF_HOST_JOIN
MULTI_FUTURE_RUNTIME_AUTHORIZED = c.MULTI_FUTURE_RUNTIME_AUTHORIZED
NEXT_CANONICAL_DECISION = c.NEXT_CANONICAL_DECISION
NEXT_CAP22_DEPENDENCY = c.NEXT_CAP22_DEPENDENCY
TOP20_DIAGNOSTIC_ONLY = c.TOP20_DIAGNOSTIC_ONLY
HARNESS_NETWORK_READ_REQUIRED = c.HARNESS_NETWORK_READ_REQUIRED
POLICY_WINNER_OUTPUT_PRESENT = c.POLICY_WINNER_OUTPUT_PRESENT
FORWARD_LABEL_METRICS_PRESENT = c.FORWARD_LABEL_METRICS_PRESENT
HISTORICAL_PIT_WALK_FORWARD_EVIDENCE_PRESENT = c.HISTORICAL_PIT_WALK_FORWARD_EVIDENCE_PRESENT

FALSE_REQUIRED_FLAGS: tuple[str, ...] = (
    "cap22_productive_economic_runtime_wired",
    "economic_md_producer_productively_scheduled",
    "economic_rank_activated",
    "final_score_formula_ratified",
    "final_weights_ratified",
    "forward_label_horizon_ratified",
    "forward_label_metrics_present",
    "historical_pit_walk_forward_evidence_present",
    "historical_replay_horizon_ratified",
    "harness_network_read_required",
    "multi_future_runtime_authorized",
    "near_zero_threshold_ratified",
    "pdf_step_7_runtime_implementation_allowed",
    "policy_b_single_threshold_ratified",
    "policy_b_threshold_set_ratified",
    "policy_ratification_justified",
    "policy_winner_output_present",
    "productive_mf_host_join",
    "ranking_cadence_ratified",
    "runtime_authority_granted",
)

TRUE_REQUIRED_FLAGS: tuple[str, ...] = (
    "anti_churn_policy_a_unchanged",
    "economic_md_producer_implemented",
    "no_challenger_wins_by_this_slice",
    "no_offline_policy_class_has_productive_authority",
    "offline_challenger_a_is_not_anti_churn_policy_a",
    "policy_b_test_only_values_used",
    "top20_diagnostic_only",
)


class Cap22OfflineMvrThresholdSetAndEvidenceHarnessError(ValueError):
    """Fail-closed offline MVR threshold-set/harness contract error."""


def _require_mapping(payload: Mapping[str, Any] | None) -> Mapping[str, Any]:
    if not isinstance(payload, Mapping):
        raise Cap22OfflineMvrThresholdSetAndEvidenceHarnessError(
            "THRESHOLD_SET_HARNESS_DECLARATION_NOT_A_MAPPING"
        )
    return payload


def _require_false_flags(raw: Mapping[str, Any]) -> None:
    for key in FALSE_REQUIRED_FLAGS:
        if key not in raw:
            continue
        if raw[key] is not False:
            raise Cap22OfflineMvrThresholdSetAndEvidenceHarnessError(
                "THRESHOLD_SET_HARNESS_FALSE_FLAG_VIOLATION", key
            )


def _require_true_flags(raw: Mapping[str, Any]) -> None:
    for key in TRUE_REQUIRED_FLAGS:
        if key not in raw:
            continue
        if raw[key] is not True:
            raise Cap22OfflineMvrThresholdSetAndEvidenceHarnessError(
                "THRESHOLD_SET_HARNESS_TRUE_FLAG_VIOLATION", key
            )


def classify_cap22_offline_mvr_threshold_set_and_harness_v1() -> dict[str, Any]:
    return {
        "authoritative_policy_b_threshold_scale_found": (
            AUTHORITATIVE_POLICY_B_THRESHOLD_SCALE_FOUND
        ),
        "challenger_a_policy_id": CHALLENGER_A_POLICY_ID,
        "challenger_b_policy_id": CHALLENGER_B_POLICY_ID,
        "challenger_c_policy_id": CHALLENGER_C_POLICY_ID,
        "challenger_d_policy_id": CHALLENGER_D_POLICY_ID,
        "forward_label_metrics_present": FORWARD_LABEL_METRICS_PRESENT,
        "harness_network_read_required": HARNESS_NETWORK_READ_REQUIRED,
        "historical_pit_walk_forward_evidence_present": (
            HISTORICAL_PIT_WALK_FORWARD_EVIDENCE_PRESENT
        ),
        "negative_control_policy_id": NEGATIVE_CONTROL_POLICY_ID,
        "policy_b_single_threshold_ratified": POLICY_B_SINGLE_THRESHOLD_RATIFIED,
        "policy_b_test_only_values_used": POLICY_B_TEST_ONLY_VALUES_USED,
        "policy_b_threshold_mode": POLICY_B_THRESHOLD_MODE,
        "policy_b_threshold_set_id": POLICY_B_THRESHOLD_SET_ID,
        "policy_b_threshold_set_ratified": POLICY_B_THRESHOLD_SET_RATIFIED,
        "policy_winner_output_present": POLICY_WINNER_OUTPUT_PRESENT,
        "top20_diagnostic_only": TOP20_DIAGNOSTIC_ONLY,
    }


def validate_cap22_offline_mvr_threshold_set_and_harness_declaration_v1(
    payload: Mapping[str, Any] | None,
) -> dict[str, Any]:
    raw = _require_mapping(payload)
    _require_false_flags(raw)
    _require_true_flags(raw)
    if raw.get("policy_b_threshold_mode") not in (None, POLICY_B_THRESHOLD_MODE):
        raise Cap22OfflineMvrThresholdSetAndEvidenceHarnessError("POLICY_B_THRESHOLD_MODE_MISMATCH")
    if raw.get("policy_b_threshold_set_id") not in (None, POLICY_B_THRESHOLD_SET_ID):
        raise Cap22OfflineMvrThresholdSetAndEvidenceHarnessError(
            "POLICY_B_THRESHOLD_SET_ID_MISMATCH"
        )
    if raw.get("pdf_step_5_status") not in (None, PDF_STEP_5_STATUS):
        raise Cap22OfflineMvrThresholdSetAndEvidenceHarnessError(
            "PDF_STEP_5_MUST_REMAIN_UNRESOLVED"
        )
    if raw.get("pdf_step_7_status") not in (None, PDF_STEP_7_STATUS):
        raise Cap22OfflineMvrThresholdSetAndEvidenceHarnessError("PDF_STEP_7_MUST_REMAIN_FORBIDDEN")
    if raw.get("challenger_a_policy_id") not in (None, CHALLENGER_A_POLICY_ID):
        raise Cap22OfflineMvrThresholdSetAndEvidenceHarnessError(
            "CHALLENGER_A_MUST_REMAIN_VOLATILITY_RANK_ONLY"
        )
    return {
        "authority_effect": AUTHORITY_EFFECT,
        "contract_id": CONTRACT_ID,
        "policy_b_threshold_mode": POLICY_B_THRESHOLD_MODE,
        "schema_version": SCHEMA_VERSION,
        "valid": True,
    }
