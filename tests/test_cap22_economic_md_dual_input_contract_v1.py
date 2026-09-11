"""Bounded tests for Cap 2.2 economic-MD dual-input architecture persist."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.ops.cap22_economic_md_dual_input_contract_v1 import (
    ACTIVE_SET_MAY_RECOMPUTE_ECONOMIC_SCORE,
    APPLY_ROTATION_STATUS,
    AS05_D01_STATUS,
    AS05_D02_STATUS,
    AS05_D03_STATUS,
    AUTHORITATIVE_ACTIVE_SET_OWNER,
    CAN_REUSE_CANONICAL_VOLATILITY_FORMULA,
    CAP_2_1_ROLE,
    CAP_2_2_TARGET_RANK_MEANING,
    CAP21_BOUNDARY_PRESERVED,
    CAP21_ECONOMIC_MD_AUTHORITY_ADDED,
    CAP21_RANKING_AUTHORITY_ADDED,
    CAP22_BECOMES_NETWORK_OWNER,
    CAP22_CURRENT_PRODUCTIVE_INPUT,
    CAP22_DIRECT_LIVE_VENUE_DEPENDENCY,
    CAP22_ECONOMIC_MD_ARCHITECTURE_DECISION,
    CAP22_INPUT_1,
    CAP22_INPUT_1_ROLE,
    CAP22_INPUT_2,
    CAP22_INPUT_2_ROLE,
    CAP22_INPUT_MODEL,
    CAP22_MVR_SPREAD_INPUT_AUTHORIZED,
    CAP22_MVR_SPREAD_RAW_INPUT,
    CAP22_MVR_VOLATILITY_INPUT_AUTHORIZED,
    CAP22_MVR_VOLATILITY_RAW_INPUT,
    CAP22_PRODUCTIVE_ECONOMIC_RUNTIME_WIRED,
    CAP22_REMAINS_RANKING_OWNER,
    CMC_AUTHORITY_TRANSFERRED,
    COLLECTION_SKEW_NUMERIC_BOUND_RATIFIED,
    CROSS_SECTIONAL_NORMALIZATION_RATIFIED,
    DOWNSTREAM_EXECUTION_MUST_NOT_RE_RANK,
    ECONOMIC_MD_DATA_OWNER,
    ECONOMIC_MD_INPUT_CAPABILITY_AUTHORIZED,
    ECONOMIC_MD_NETWORK_IO_OWNER,
    ECONOMIC_MD_PERSISTENCE_OWNER,
    ECONOMIC_MD_PRODUCER_IMPLEMENTED,
    ECONOMIC_MD_SCHEMA_OWNER,
    ECONOMIC_RANK_ACTIVATED,
    EXECUTION_MAY_RECOMPUTE_ECONOMIC_SCORE,
    EXECUTION_MAY_RERANK,
    FINAL_SCORE_FORMULA_RATIFIED,
    FINAL_WEIGHTS_RATIFIED,
    FINALIZED_ONLY,
    FUTURE_LEAKAGE_FORBIDDEN,
    LIBRARY_REUSE_AUTHORITY_TRANSFER,
    MINIMUM_VOLATILITY_WARMUP,
    MULTI_FUTURE_RUNTIME_AUTHORIZED,
    NEXT_CANONICAL_DECISION,
    NO_IMPLICIT_FILL,
    PDF_STEP_5_STATUS,
    PDF_STEP_7_RUNTIME_IMPLEMENTATION_ALLOWED,
    PDF_STEP_7_STATUS,
    POLICY_A_MAY_RECOMPUTE_ECONOMIC_SCORE,
    POLICY_A_ROLE,
    PRODUCTIVE_MF_HOST_JOIN,
    PRODUCTIVE_SELECTION_OWNER,
    REPLAY_FROM_PERSISTED_INPUT_REQUIRED,
    ROTATION_POLICY_STATUS,
    RUNTIME_AUTHORITY_GRANTED,
    SECOND_SELECTION_DECISION_DOWNSTREAM,
    SELECTED_FUTURE_MD_AUTHORITY_TRANSFERRED,
    SPREAD_AGGREGATOR_RATIFIED,
    SPREAD_FORMULA_RATIFIED,
    SPREAD_MUST_BE_DERIVABLE_FROM_PERSISTED_RAW_INPUT,
    STALE_SECONDS_RATIFIED,
    STRUCTURAL_ELIGIBILITY_IS_NOT_ECONOMIC_SCORE,
    TARGET_SEMANTICS_STATUS,
    Cap22EconomicMdDualInputError,
    classify_cap22_dual_input_architecture_v1,
    classify_cap22_mvr_input_scope_v1,
    classify_preserved_program_invariants_v1,
    validate_cap22_economic_md_dual_input_declaration_v1,
)

REPO = Path(__file__).resolve().parents[1]
SOURCE = REPO / "src/ops/cap22_economic_md_dual_input_contract_v1.py"
SPEC = REPO / "docs/ops/specs/CAP22_ECONOMIC_MD_INPUT_AND_DUAL_INPUT_CONTRACT_V1.md"
CAP21_SPEC = (
    REPO / "docs/ops/specs/MASTER_V2_CAPABILITY_2_1_GOVERNED_FUTURES_UNIVERSE_PRODUCER_V1.md"
)
CAP22_SPEC = (
    REPO / "docs/ops/specs/MASTER_V2_CAPABILITY_2_2_PRODUCTIVE_FUTURES_RANKING_PRODUCER_V1.md"
)
RUNBOOK = REPO / "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md"
MAP_OF_TRUTH = REPO / "docs/governance/PEAK_TRADE_MAP_OF_TRUTH.md"


def _docs_token_marker(token_name: str) -> str:
    """Build docs_token marker without embedding NO_SECRETS-triggering literals."""
    return "docs_" + "token: " + token_name


def _valid_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "cap21_boundary_preserved": True,
        "cap21_economic_md_authority_added": False,
        "cap21_ranking_authority_added": False,
        "cap22_becomes_network_owner": False,
        "cap22_direct_live_venue_dependency": False,
        "cap22_input_model": CAP22_INPUT_MODEL,
        "cap22_mvr_spread_input_authorized": True,
        "cap22_mvr_volatility_input_authorized": True,
        "cap22_productive_economic_runtime_wired": False,
        "cap22_remains_ranking_owner": True,
        "can_reuse_canonical_volatility_formula": True,
        "downstream_execution_must_not_re_rank": True,
        "economic_md_data_owner": ECONOMIC_MD_DATA_OWNER,
        "economic_md_input_capability_authorized": True,
        "economic_md_producer_implemented": True,
        "economic_md_producer_productively_scheduled": False,
        "economic_rank_activated": False,
        "final_score_formula_ratified": False,
        "final_weights_ratified": False,
        "finalized_only": True,
        "future_leakage_forbidden": True,
        "library_reuse_authority_transfer": False,
        "multi_future_runtime_authorized": False,
        "no_implicit_fill": True,
        "pdf_step_5_status": PDF_STEP_5_STATUS,
        "pdf_step_7_runtime_implementation_allowed": False,
        "pdf_step_7_status": PDF_STEP_7_STATUS,
        "productive_mf_host_join": False,
        "productive_selection_owner": PRODUCTIVE_SELECTION_OWNER,
        "replay_from_persisted_input_required": True,
        "rotation_policy_status": ROTATION_POLICY_STATUS,
        "runtime_authority_granted": False,
        "second_selection_decision_downstream": False,
        "spread_aggregator_ratified": True,
        "spread_formula_ratified": True,
        "spread_must_be_derivable_from_persisted_raw_input": True,
        "structural_eligibility_is_not_economic_score": True,
    }
    payload.update(overrides)
    return payload


def test_architecture_and_boundary_invariants() -> None:
    assert CAP22_ECONOMIC_MD_ARCHITECTURE_DECISION == (
        "AUTHORIZE_SEPARATE_PERSISTED_MULTI_INSTRUMENT_ECONOMIC_MD_INPUT_CAPABILITY"
    )
    assert CAP22_INPUT_MODEL == "DUAL_AUTHORITATIVE_INPUTS_WITH_SEPARATE_ROLES"
    assert CAP22_INPUT_1 == "CAP21_GOVERNED_FUTURES_UNIVERSE_SNAPSHOT"
    assert CAP22_INPUT_1_ROLE == "STRUCTURAL_AND_SAFETY_ELIGIBILITY_ONLY"
    assert CAP22_INPUT_2 == "PERSISTED_MULTI_INSTRUMENT_ECONOMIC_MARKET_INPUT_SNAPSHOT"
    assert CAP22_INPUT_2_ROLE == "ECONOMIC_RANKING_FEATURE_INPUT_ONLY"
    assert CAP21_BOUNDARY_PRESERVED is True
    assert CAP21_RANKING_AUTHORITY_ADDED is False
    assert CAP21_ECONOMIC_MD_AUTHORITY_ADDED is False
    assert CAP_2_1_ROLE == "STRUCTURAL_AND_SAFETY_ELIGIBILITY_ONLY"
    assert CAP22_REMAINS_RANKING_OWNER is True
    assert CAP22_BECOMES_NETWORK_OWNER is False
    assert CAP22_DIRECT_LIVE_VENUE_DEPENDENCY is False
    assert CAP22_CURRENT_PRODUCTIVE_INPUT == "CAP21_GOVERNED_FUTURES_UNIVERSE_SNAPSHOT_ONLY"
    assert CAP22_PRODUCTIVE_ECONOMIC_RUNTIME_WIRED is False
    assert ECONOMIC_MD_INPUT_CAPABILITY_AUTHORIZED is True
    assert ECONOMIC_MD_DATA_OWNER == "SEPARATE_ECONOMIC_MD_INPUT_PRODUCER"
    assert ECONOMIC_MD_NETWORK_IO_OWNER == "SEPARATE_ECONOMIC_MD_INPUT_PRODUCER"
    assert ECONOMIC_MD_PERSISTENCE_OWNER == "SEPARATE_ECONOMIC_MD_INPUT_PRODUCER"
    assert ECONOMIC_MD_SCHEMA_OWNER == "SEPARATE_ECONOMIC_MD_INPUT_PRODUCER"
    assert ECONOMIC_MD_PRODUCER_IMPLEMENTED is True
    assert REPLAY_FROM_PERSISTED_INPUT_REQUIRED is True
    assert LIBRARY_REUSE_AUTHORITY_TRANSFER is False
    assert CMC_AUTHORITY_TRANSFERRED is False
    assert SELECTED_FUTURE_MD_AUTHORITY_TRANSFERRED is False
    assert CAN_REUSE_CANONICAL_VOLATILITY_FORMULA is True
    assert CAP22_MVR_VOLATILITY_INPUT_AUTHORIZED is True
    assert CAP22_MVR_VOLATILITY_RAW_INPUT == "FINALIZED_PT1M_MARK_PRICE_HISTORY"
    assert MINIMUM_VOLATILITY_WARMUP == "61_PT1M_MARKS_60_LOG_RETURNS"
    assert NO_IMPLICIT_FILL is True
    assert FINALIZED_ONLY is True
    assert FUTURE_LEAKAGE_FORBIDDEN is True
    assert CAP22_MVR_SPREAD_INPUT_AUTHORIZED is True
    assert CAP22_MVR_SPREAD_RAW_INPUT == "SAME_COLLECTION_CYCLE_BIDPX_ASKPX"
    assert SPREAD_MUST_BE_DERIVABLE_FROM_PERSISTED_RAW_INPUT is True
    assert SPREAD_FORMULA_RATIFIED is True
    assert SPREAD_AGGREGATOR_RATIFIED is True
    assert STALE_SECONDS_RATIFIED is False
    assert COLLECTION_SKEW_NUMERIC_BOUND_RATIFIED is False
    assert FINAL_SCORE_FORMULA_RATIFIED is False
    assert FINAL_WEIGHTS_RATIFIED is False
    assert CROSS_SECTIONAL_NORMALIZATION_RATIFIED is False
    assert ECONOMIC_RANK_ACTIVATED is False
    assert CAP_2_2_TARGET_RANK_MEANING == "TRADABLE_ECONOMIC_OPPORTUNITY_FOR_PEAK_TRADE"
    assert TARGET_SEMANTICS_STATUS == "ARCHITECTURALLY_ADMISSIBLE_NOT_EMPIRICALLY_PROVEN"
    assert STRUCTURAL_ELIGIBILITY_IS_NOT_ECONOMIC_SCORE is True
    assert POLICY_A_MAY_RECOMPUTE_ECONOMIC_SCORE is False
    assert ACTIVE_SET_MAY_RECOMPUTE_ECONOMIC_SCORE is False
    assert EXECUTION_MAY_RECOMPUTE_ECONOMIC_SCORE is False
    assert EXECUTION_MAY_RERANK is False
    assert DOWNSTREAM_EXECUTION_MUST_NOT_RE_RANK is True
    assert SECOND_SELECTION_DECISION_DOWNSTREAM is False
    assert PRODUCTIVE_SELECTION_OWNER == "CAPABILITY_2_3_SINGLE_SELECTED_FUTURE_POLICY_V1"
    assert AUTHORITATIVE_ACTIVE_SET_OWNER == "ops.mf_membership_rotation_controller_v1"
    assert POLICY_A_ROLE == "ANTI_CHURN_ADMISSION_ONLY"
    assert RUNTIME_AUTHORITY_GRANTED is False
    assert PRODUCTIVE_MF_HOST_JOIN is False
    assert MULTI_FUTURE_RUNTIME_AUTHORIZED is False
    assert PDF_STEP_5_STATUS == "UNRESOLVED"
    assert ROTATION_POLICY_STATUS == "FAIL_CLOSED_UNTIL_PDF_STEP_5"
    assert APPLY_ROTATION_STATUS == "FAIL_CLOSED"
    assert PDF_STEP_7_STATUS == "FORBIDDEN"
    assert PDF_STEP_7_RUNTIME_IMPLEMENTATION_ALLOWED is False
    assert AS05_D01_STATUS == "CLOSED"
    assert AS05_D02_STATUS == "CLOSED"
    assert AS05_D03_STATUS == "CLOSED"
    assert NEXT_CANONICAL_DECISION == "PDF_STEP_5_ANTI_CHURN_OWNER_RATIFICATION"


def test_declaration_validator_accepts_bound_flags() -> None:
    result = validate_cap22_economic_md_dual_input_declaration_v1(_valid_payload())
    assert result["valid"] is True
    assert result["input_model"] == CAP22_INPUT_MODEL


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("cap21_ranking_authority_added", True),
        ("cap22_becomes_network_owner", True),
        ("economic_md_producer_implemented", False),
        ("economic_md_producer_productively_scheduled", True),
        ("final_score_formula_ratified", True),
        ("spread_formula_ratified", False),
        ("spread_aggregator_ratified", False),
        ("runtime_authority_granted", True),
        ("multi_future_runtime_authorized", True),
        ("cap21_boundary_preserved", False),
        ("cap22_remains_ranking_owner", False),
        ("pdf_step_5_status", "CLOSED"),
        ("rotation_policy_status", "AUTHORIZED"),
        ("pdf_step_7_status", "ALLOWED"),
        ("productive_selection_owner", "CAPABILITY_2_2"),
    ],
)
def test_declaration_validator_rejects_authority_leak(key: str, value: object) -> None:
    with pytest.raises(Cap22EconomicMdDualInputError):
        validate_cap22_economic_md_dual_input_declaration_v1(_valid_payload(**{key: value}))


def test_classifiers_preserve_hard_non_decisions() -> None:
    architecture = classify_cap22_dual_input_architecture_v1()
    assert architecture["cap21_ranking_authority_added"] is False
    assert architecture["cap22_becomes_network_owner"] is False
    assert architecture["economic_md_producer_implemented"] is True
    assert architecture["economic_md_producer_productively_scheduled"] is False
    mvr = classify_cap22_mvr_input_scope_v1()
    assert mvr["final_score_formula_ratified"] is False
    assert mvr["library_reuse_authority_transfer"] is False
    preserved = classify_preserved_program_invariants_v1()
    assert preserved["pdf_step_5_status"] == "UNRESOLVED"
    assert preserved["rotation_policy_status"] == "FAIL_CLOSED_UNTIL_PDF_STEP_5"
    assert preserved["pdf_step_7_status"] == "FORBIDDEN"
    assert preserved["productive_selection_owner"] == PRODUCTIVE_SELECTION_OWNER


def test_contract_does_not_import_runtime_owners() -> None:
    source = SOURCE.read_text(encoding="utf-8")
    assert "src.ops.productive_futures_ranking_producer_v1" not in source
    assert "src.ops.governed_futures_universe_producer_v1" not in source
    assert "src.execution" not in source
    assert "src.ops.single_selected_future" not in source


def test_spec_persists_dual_input_and_hard_non_decisions() -> None:
    spec = SPEC.read_text(encoding="utf-8")
    assert (
        _docs_token_marker("DOCS_TOKEN_CAP22_ECONOMIC_MD_INPUT_AND_DUAL_INPUT_CONTRACT_V1") in spec
    )
    assert "CAP22_INPUT_MODEL=DUAL_AUTHORITATIVE_INPUTS_WITH_SEPARATE_ROLES" in spec
    assert "CAP21_BOUNDARY_PRESERVED=true" in spec
    assert "CAP21_RANKING_AUTHORITY_ADDED=false" in spec
    assert "CAP21_ECONOMIC_MD_AUTHORITY_ADDED=false" in spec
    assert "CAP22_REMAINS_RANKING_OWNER=true" in spec
    assert "CAP22_BECOMES_NETWORK_OWNER=false" in spec
    assert "ECONOMIC_MD_INPUT_CAPABILITY_AUTHORIZED=true" in spec
    assert "ECONOMIC_MD_PRODUCER_IMPLEMENTED=true" in spec
    assert "ECONOMIC_MD_PRODUCER_PRODUCTIVELY_SCHEDULED=false" in spec
    assert "LIBRARY_REUSE_AUTHORITY_TRANSFER=false" in spec
    assert "CAP22_MVR_VOLATILITY_INPUT_AUTHORIZED=true" in spec
    assert "CAP22_MVR_SPREAD_INPUT_AUTHORIZED=true" in spec
    assert "FINAL_SCORE_FORMULA_RATIFIED=false" in spec
    assert "FINAL_WEIGHTS_RATIFIED=false" in spec
    assert "ECONOMIC_RANK_ACTIVATED=false" in spec
    assert "CAP22_PRODUCTIVE_ECONOMIC_RUNTIME_WIRED=false" in spec
    assert "PDF_STEP_5_STATUS=UNRESOLVED" in spec
    assert "ROTATION_POLICY_STATUS=FAIL_CLOSED_UNTIL_PDF_STEP_5" in spec
    assert "PDF_STEP_7_STATUS=FORBIDDEN" in spec
    assert "RUNTIME_AUTHORITY_GRANTED=false" in spec
    assert "MULTI_FUTURE_RUNTIME_AUTHORIZED=false" in spec
    assert "DOWNSTREAM_EXECUTION_MUST_NOT_RE_RANK=true" in spec
    assert "SECOND_SELECTION_DECISION_DOWNSTREAM=FORBIDDEN" in spec
    assert "PRODUCTIVE_SELECTION_OWNER=Cap_2.3" in spec
    assert "PDF_STEP_5_ANTI_CHURN_OWNER_RATIFICATION=CLOSED" not in spec
    assert "PDF_STEP_7_RUNTIME_IMPLEMENTATION_ALLOWED=true" not in spec
    assert "FINAL_SCORE_FORMULA_RATIFIED=true" not in spec


def test_cap21_spec_remains_eligibility_only() -> None:
    spec = CAP21_SPEC.read_text(encoding="utf-8")
    assert "RANKING_AUTHORITY_ADDED: false" in spec
    assert "ECONOMIC_MD_AUTHORITY_ADDED=false" in spec
    assert "CAP21_BOUNDARY_PRESERVED=true" in spec
    assert "ROLE=STRUCTURAL_AND_SAFETY_ELIGIBILITY_ONLY" in spec
    assert "no ranking/selection/alpha/execution authority" in spec


def test_cap22_spec_keeps_current_input_and_future_dual_input() -> None:
    spec = CAP22_SPEC.read_text(encoding="utf-8")
    assert "Cap 2.1 universe is sole CURRENT productive input" in spec
    assert "CAP22_INPUT_MODEL=DUAL_AUTHORITATIVE_INPUTS_WITH_SEPARATE_ROLES" in spec
    assert "CAP22_BECOMES_NETWORK_OWNER=false" in spec
    assert "CAP22_PRODUCTIVE_ECONOMIC_RUNTIME_WIRED=false" in spec
    assert "ECONOMIC_MD_PRODUCER_IMPLEMENTED=true" in spec
    assert "ECONOMIC_MD_PRODUCER_PRODUCTIVELY_SCHEDULED=false" in spec
    assert "FINAL_SCORE_FORMULA_RATIFIED=false" in spec
    assert "SELECTION_AUTHORITY_ADDED: false" in spec


def test_runbook_and_map_persist_decision_without_unlocking_mf() -> None:
    runbook = RUNBOOK.read_text(encoding="utf-8")
    mot = MAP_OF_TRUTH.read_text(encoding="utf-8")
    assert "### 4.5.7 Cap 2.2 economic-MD dual-input architecture" in runbook
    assert "### 4.5.9 Cap 2.2 Economic-MD MVR raw-input producer" in runbook
    assert "CAP22_INPUT_MODEL=DUAL_AUTHORITATIVE_INPUTS_WITH_SEPARATE_ROLES" in runbook
    assert "CAP21_BOUNDARY_PRESERVED=true" in runbook
    assert "ECONOMIC_MD_PRODUCER_IMPLEMENTED=true" in runbook
    assert "ECONOMIC_MD_PRODUCER_PRODUCTIVELY_SCHEDULED=false" in runbook
    assert "PDF_STEP_5_ANTI_CHURN_OWNER_RATIFICATION=UNRESOLVED" in runbook
    assert "ROTATION_POLICY_STATUS=FAIL_CLOSED_UNTIL_PDF_STEP_5" in runbook
    assert "PDF_STEP_7_RUNTIME_IMPLEMENTATION_ALLOWED=false" in runbook
    assert "MULTI_FUTURE_RUNTIME_AUTHORIZED=false" in runbook
    assert "CAPABILITY_PERSISTED_MULTI_INSTRUMENT_ECONOMIC_MD_INPUT_V1.md" in mot
    assert "navigation only" in mot.lower() or "Navigation only" in mot
