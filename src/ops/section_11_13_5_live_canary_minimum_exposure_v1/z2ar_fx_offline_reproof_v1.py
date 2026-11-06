"""§11.13.5.Z2CW FX offline reproof.

CONTRACT / GOVERNANCE only. Adjudicates the already-bound FX class
against repo-internal canonical persist, forensic originals, and
navigation indexes. Does not observe a venue. Does not prove an FX
operator. Does not treat idxPx=1 or USD≈USDC as conversion proof.
Does not adjudicate COVER_USDC, ROUNDING, FINISHED_RISK_ENVELOPE_NUMERIC,
or USD_USDC_ACCOUNT_SETTLEMENT as classes. Does not authorize Live,
Testnet, orders, funding, GET, POST, flatten, Class D, or Z2AP.
"""

from __future__ import annotations

from typing import Any, Mapping

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.formula_term_instance_binding_v1 import (
    FX_APPLIED as BOUND_FX_APPLIED,
    FX_STATUS as BOUND_FX_STATUS,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.position_value_fx_rounding_chain_v1 import (
    RULE_FX as BOUND_RULE_FX,
    RULE_FX_STATUS as BOUND_RULE_FX_STATUS,
    ROUNDING_APPLIED as BOUND_ROUNDING_APPLIED,
    USD_USDC_CONVERSION_APPLIED as BOUND_USD_USDC_CONVERSION_APPLIED,
    USD_USDC_PARITY_ASSUMED as BOUND_USD_USDC_PARITY_ASSUMED,
)

OWNER_GO = "PEAK_TRADE_OWNER_GO_Z2AR_FX_REPROOF_OFFLINE_V1"
THIS_SLICE = "11.13.5.Z2CW"
PREDECESSOR_SLICE = "11.13.5.Z2CV"
LAST_CANONICALLY_CLOSED_11_13_5_SLICE = "SECTION_11_13_5_Z2CT"
THIS_PERSIST_DOES_NOT_SUPERSEDE_Z2CT_AS_LAST_CANONICALLY_CLOSED_11_13_5_SLICE = True
THIS_PERSIST_DOES_NOT_REWRITE_Z2CV = True
THIS_NAMED_CLASS_PERSIST_ID = "SECTION_11_13_5_Z2CW"

Z2AR_CLASS = "FX"
EXACT_Z2AR_CLASS = "FX"
AUTHORIZED_SCOPE = "P3_Z2AR_REMAINING_UNRANKED_SUI_REPROOF"
ADJUDICATION = "NOT_REPROVEN_MISSING_EVIDENCE"
CURRENT_FX_STATUS = "NOT_REPROVEN_MISSING_EVIDENCE"
REPROOF_PROVEN = False
RULE_FX = "FX-VENUE-CONVERT"
RULE_FX_STATUS = "UNPROVEN"
RULE_FX_IS_RATIFIED_FORM_NOT_PROVEN_CONVERSION = True
FX_STATUS = "UNPROVEN"
FX_APPLIED = False
FX_OPERATOR_PROVEN = False

CURRENT_CANONICAL_INSTRUMENT = "SUI-USD_UM_XPERP-310404"
CURRENT_SUI_BINDING = "SUI-USD_UM_XPERP-310404"

SUI_REPROOF_CLASSES_RANKED = False
NO_RANKING_OF_REMAINDER = True
REMAINING_UNRANKED_AFTER_THIS_CLASS = (
    "ROUNDING",
    "FINISHED_RISK_ENVELOPE_NUMERIC",
    "USD_USDC_ACCOUNT_SETTLEMENT",
)
FORBIDDEN_COLLAPSE_CLASSES = (
    "COVER_USDC",
    "ROUNDING",
    "USD_USDC_ACCOUNT_SETTLEMENT",
    "FINISHED_RISK_ENVELOPE_NUMERIC",
    "RISK_ENVELOPE_NUMERIC",
)

CLASS_D_CONSUMED = False
Z2AP_CONSUMED = False
EXECUTION_READY = False
LIVE_FLATTEN_PROVABILITY = "UNPROVEN"
THIS_GO_AUTHORIZES_GET = False
THIS_GO_AUTHORIZES_POST = False
THIS_GO_AUTHORIZES_FLATTEN = False
RUNTIME_AUTHORIZATION_EFFECT = "NONE"
RUNTIME_API_CALLS = 0
GET_PERFORMED = False
POST_PERFORMED = False
FLATTEN_PERFORMED = False

Z2J_REMAINS_CONTROLLING_FOR_CLIENT_FX_AND_NUMERIC_OPERATOR = True
Z2AJ_IDXPX_1_NON_OPERATOR_NEGATIVE_CONTRACT_REMAINS_IN_FORCE = True
IDXPX_1_IS_NOT_USD_USDC_OPERATOR = True
IDXPX_1_IS_NOT_FX_OPERATOR = True
IDXPX_1_IS_OBSERVATION_ONLY = True
USD_EQUALS_USDC_ASSUMED = False
NO_USD_EQUALS_USDC = True
NO_IMPLICIT_ONE_TO_ONE_EQUIVALENCE = True
USD_AND_USDC_REMAIN_STRICTLY_DISTINCT_UNITS = True
VENUE_NUMERIC_CONVERSION_OPERATOR_PROVEN = False
CLIENT_FX_PROPOSITION_VERDICT = "UNPROVEN"
CLIENT_SIDE_FX_REQUIRED_PROVEN = False
NO_CLIENT_CONVERSION_REQUIRED_PROVEN = False
CONVERSION_NUMERIC_STATUS = "UNINSTANTIATED_REQUIRES_LATER_PRODUCTIVE_USD_USDC_EVIDENCE"
FORBIDDEN_UPGRADE_FROM_IDXPX_1 = True
FORBIDDEN_UPGRADE_HISTORICAL_TO_PROVEN = True
FORBIDDEN_UPGRADE_NAVIGATION_TO_PROVEN = True
BTC_ERA_IDXPX_OBSERVATION_IS_NOT_CURRENT_SUI_FX_OPERATOR = True
NUMERICAL_EQUALITY_IS_NOT_OPERATOR_PROOF = True

REQUIRED_INPUTS_FOR_REPROVEN: tuple[str, ...] = (
    "CANONICAL_FX_DEFINITION_IDENTIFIED",
    "OPERATOR_OR_INPUT_TYPE_UNIQUELY_DEFINED_AND_INSTANTIATED",
    "DIRECTION_AND_UNITS_PROVEN",
    "SETTLEMENT_OR_INSTRUMENT_BINDINGS_CARRY",
    "PRIMARY_REPO_INTERNAL_CONVERSION_VALUES",
    "FRESHNESS_AND_SCOPE_WITHOUT_GAP",
    "NO_CONTRADICTORY_CANONICAL_AUTHORITY",
    "NO_IDXPX_1_NORMALIZATION",
    "NO_USD_EQUALS_USDC_NORMALIZATION",
)

CURRENT_REQUIRED_INPUT_STATE: Mapping[str, str] = {
    "CANONICAL_FX_DEFINITION": "RULE_FX=FX-VENUE-CONVERT_RATIFIED_FORM_NOT_PROVEN_INSTANCE",
    "OPERATOR_OR_INPUT_TYPE": "UNINSTANTIATED_REQUIRES_LATER_PRODUCTIVE_USD_USDC_EVIDENCE",
    "DIRECTION_AND_UNITS": "UNITS_DISTINCT_NUMERIC_OPERATOR_DIRECTION_UNPROVEN",
    "SETTLEMENT_OR_INSTRUMENT_BINDINGS": (
        "PUBLIC_SETTLE_CCY=USD_ACCOUNT_SETTLE_CCY=USDC_NUMERIC_ACCOUNT_SETTLEMENT_UNPROVEN"
    ),
    "PRIMARY_CONVERSION_VALUES": "ABSENT",
    "FRESHNESS_AND_SCOPE": "NO_CURRENT_SUI_BOUND_CONVERSION_OPERATOR",
    "CONTRADICTORY_CANONICAL_AUTHORITY": "NONE",
    "USD_USDC_OPERATOR_STATUS": "UNPROVEN",
    "VENUE_NUMERIC_CONVERSION_OPERATOR_PROVEN": "false",
    "CLIENT_FX_PROPOSITION_VERDICT": "UNPROVEN",
    "CURRENT_SUI_INSTRUMENT_BINDING": "SUI-USD_UM_XPERP-310404",
}

BLOCKING_EVIDENCE_GAPS: tuple[str, ...] = (
    "USD_USDC_OPERATOR_STATUS=UNPROVEN",
    "VENUE_NUMERIC_CONVERSION_OPERATOR_PROVEN=false",
    "CLIENT_FX_PROPOSITION_VERDICT=UNPROVEN",
    "CLIENT_SIDE_FX_REQUIRED_PROVEN=false",
    "NO_CLIENT_CONVERSION_REQUIRED_PROVEN=false",
    "CONVERSION_NUMERIC_STATUS=UNINSTANTIATED_REQUIRES_LATER_PRODUCTIVE_USD_USDC_EVIDENCE",
    "RULE_FX_IS_RATIFIED_FORM_NOT_PROVEN_CONVERSION",
    "IDXPX_1_IS_NOT_USD_USDC_OPERATOR",
    "DIRECTION_AND_UNITS_OF_NUMERIC_OPERATOR_UNPROVEN",
    "USD_USDC_ACCOUNT_SETTLEMENT_PROVEN=false",
    "FRESH_SUI_BOUND_CONVERSION_OPERATOR_ABSENT",
    "BTC_ERA_IDXPX_OBSERVATION_IS_NOT_CURRENT_SUI_FX_OPERATOR",
)

CENSUS_ENTRIES: tuple[Mapping[str, str], ...] = (
    {
        "path": "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md#11.13.5.U",
        "claim": (
            "RULE_FX=FX-VENUE-CONVERT RULE_OUTPUT_UNIT=FX-STATE-ALL-FINAL-FUNDS-IN-USDC "
            "NO_IMPLICIT_ONE_TO_ONE_EQUIVALENCE "
            "CONVERSION_NUMERIC_STATUS=UNINSTANTIATED_REQUIRES_LATER_PRODUCTIVE_USD_USDC_EVIDENCE"
        ),
        "evidence_source": "canonical persist Z2U policy form",
        "epistemic_class": "CANONICAL_AUTHORITY",
        "current_applicability": "BINDING_DEFINITION_STILL_IN_FORCE_FORM_NOT_INSTANCE",
        "superseded_stale": "false",
        "contradictions": "NONE",
        "relation_to_current_sui": "DEFINITION_INHERITED_SUI_BOUND_VIA_Z2BX_Z2BY",
    },
    {
        "path": "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md#11.13.5.Z2D",
        "claim": (
            "RULE_FX_STATUS=UNPROVEN USD_USDC_CONVERSION_APPLIED=false "
            "USD_USDC_PARITY_ASSUMED=false NO_FX_SOURCE_OR_OPERATOR=true"
        ),
        "evidence_source": "canonical persist Z2D",
        "epistemic_class": "CANONICAL_AUTHORITY",
        "current_applicability": "BINDING_NEGATIVE_STATUS",
        "superseded_stale": "false",
        "contradictions": "NONE",
        "relation_to_current_sui": "STATUS_INHERITED_NOT_SUI_NUMERIC_FX",
    },
    {
        "path": "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md#11.13.5.Z2F",
        "claim": "FX_STATUS=UNPROVEN ROUNDING_STATUS=UNPROVEN COVER_USDC_STATUS=UNINSTANTIATED",
        "evidence_source": "canonical persist Z2F term-instance adjudication",
        "epistemic_class": "CANONICAL_AUTHORITY",
        "current_applicability": "BINDING_NEGATIVE_STATUS",
        "superseded_stale": "false",
        "contradictions": "NONE",
        "relation_to_current_sui": "STATUS_INHERITED_NOT_SUI_NUMERIC_FX",
    },
    {
        "path": "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md#11.13.5.Z2J",
        "claim": (
            "CLIENT_FX_PROPOSITION_VERDICT=UNPROVEN "
            "VENUE_NUMERIC_CONVERSION_OPERATOR_PROVEN=false "
            "VENUE_INTERNAL_CONVERSION_SEMANTIC_PROVEN=true "
            "CLIENT_SIDE_FX_REQUIRED_PROVEN=false "
            "IDXPX_USDC_USD_1_IS_COVER_USDC_OPERATOR=false"
        ),
        "evidence_source": "canonical persist Z2J settlement-semantic adjudication",
        "epistemic_class": "ALREADY_ADJUDICATED_CONCLUSIONS",
        "current_applicability": "CONTROLLING_FOR_CLIENT_FX_AND_NUMERIC_OPERATOR",
        "superseded_stale": "false",
        "contradictions": "NONE",
        "relation_to_current_sui": ("SEMANTIC_VENUE_CONVERT_IS_NOT_NUMERIC_OPERATOR_FOR_SUI_FX"),
    },
    {
        "path": "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md#11.13.5.Z2AJ",
        "claim": (
            "GET_1_IDXPX=1 IDXPX_1_IS_NOT_USD_USDC_OPERATOR=true "
            "USD_USDC_OPERATOR_STATUS=UNPROVEN "
            "NO_CLIENT_CONVERSION_REQUIRED_PROVEN=false "
            "FORBIDDEN_UPGRADE_FROM_IDXPX_1=true"
        ),
        "evidence_source": "canonical persist Z2AJ of four prior public EEA GETs",
        "epistemic_class": "ALREADY_ADJUDICATED_CONCLUSIONS",
        "current_applicability": "BINDING_NEGATIVE_OPERATOR_CONTRACT",
        "superseded_stale": "GET_WINDOW_HISTORICAL_CONCLUSION_STILL_BINDING",
        "contradictions": "NONE",
        "relation_to_current_sui": "IDXPX_1_IS_NOT_CURRENT_SUI_FX_OPERATOR",
    },
    {
        "path": "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md#11.13.5.Z2AJ",
        "claim": (
            "GET_1_PATH=/api/v5/market/index-tickers?instId=USDC-USD "
            "GET_1_IDXPX=1 GET_1_INSTID=USDC-USD GET_2_OKX_CODE=51001 "
            "observation transcribed into SSOT; not a conversion operator"
        ),
        "evidence_source": "Z2AJ recorded public GET values; no separate evidence pack file",
        "epistemic_class": "FORENSIC_RAW_ORIGINALS",
        "current_applicability": "NOT_CURRENT_SUI_FX_OPERATOR",
        "superseded_stale": "true_btc_era_window_and_explicitly_non_operator",
        "contradictions": "NONE",
        "relation_to_current_sui": "SCOPE_MISMATCH_INDEX_OBSERVATION_NOT_SUI_FX",
    },
    {
        "path": "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md#11.13.5.Z2BW",
        "claim": "NOT FX; composition numeric is not FX operator",
        "evidence_source": "canonical persist Z2BW P4 composition numeric",
        "epistemic_class": "CANONICAL_AUTHORITY",
        "current_applicability": "BINDING_NEGATIVE_NOT_FX",
        "superseded_stale": "false",
        "contradictions": "NONE",
        "relation_to_current_sui": "INTERNAL_COMPOSITION_IS_NOT_FX",
    },
    {
        "path": "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md#11.13.5.Z2BX",
        "claim": "NOT FX; identity is not USD not USDC; FX not applied",
        "evidence_source": "canonical persist Z2BX P5 identity plus Cover negative contract",
        "epistemic_class": "CANONICAL_AUTHORITY",
        "current_applicability": "BINDING_NEGATIVE_NOT_FX",
        "superseded_stale": "false",
        "contradictions": "NONE",
        "relation_to_current_sui": "BOUND_FOR_SUI-USD_UM_XPERP-310404_NOT_FX",
    },
    {
        "path": "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md#11.13.5.Z2BY",
        "claim": "SUI identity rebind is not FX proof",
        "evidence_source": "canonical persist Z2BY SUI identity rebind",
        "epistemic_class": "CANONICAL_AUTHORITY",
        "current_applicability": "CURRENT_INSTRUMENT_IS_SUI_FX_STILL_UNPROVEN",
        "superseded_stale": "false",
        "contradictions": "NONE",
        "relation_to_current_sui": "REBIND_IS_NOT_FX",
    },
    {
        "path": "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md#11.13.5.Z2CU",
        "claim": "REMAINING_UNRANKED_CLASSES includes FX as named unranked SUI reproof class",
        "evidence_source": "canonical persist Z2CU",
        "epistemic_class": "CANONICAL_AUTHORITY",
        "current_applicability": "TRACK_ELIGIBILITY_NOT_FX_PROOF",
        "superseded_stale": "false",
        "contradictions": "NONE",
        "relation_to_current_sui": "NAMES_CLASS_DOES_NOT_PROVE_IT",
    },
    {
        "path": "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md#11.13.5.Z2CV",
        "claim": (
            "FX_ADJUDICATED_THIS_PERSIST=false "
            "REMAINING_UNRANKED_AFTER_THIS_CLASS includes FX "
            "FORBIDDEN_COLLAPSE_COVER_USDC_WITH_FX=true"
        ),
        "evidence_source": "canonical persist Z2CV COVER_USDC offline reproof",
        "epistemic_class": "CANONICAL_AUTHORITY",
        "current_applicability": "SIBLING_CLASS_NOT_FX_PROOF",
        "superseded_stale": "false",
        "contradictions": "NONE",
        "relation_to_current_sui": "COVER_USDC_FAIL_CLOSED_DOES_NOT_PROVE_FX",
    },
    {
        "path": (
            "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/"
            "position_value_fx_rounding_chain_v1.py"
        ),
        "claim": (
            "RULE_FX = FX-VENUE-CONVERT RULE_FX_STATUS = UNPROVEN "
            "USD_USDC_CONVERSION_APPLIED = False USD_USDC_PARITY_ASSUMED = False"
        ),
        "evidence_source": "current Python contract constant",
        "epistemic_class": "CANONICAL_AUTHORITY",
        "current_applicability": "CURRENT_RUNTIME_CONTRACT_STATUS",
        "superseded_stale": "false",
        "contradictions": "NONE",
        "relation_to_current_sui": "STANDING_UNPROVEN",
    },
    {
        "path": (
            "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/"
            "formula_term_instance_binding_v1.py"
        ),
        "claim": "FX_STATUS = UNPROVEN FX_APPLIED = False",
        "evidence_source": "current Python contract constant",
        "epistemic_class": "CANONICAL_AUTHORITY",
        "current_applicability": "CURRENT_RUNTIME_CONTRACT_STATUS",
        "superseded_stale": "false",
        "contradictions": "NONE",
        "relation_to_current_sui": "STANDING_UNPROVEN",
    },
    {
        "path": (
            "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/exact_formula_body_v1.py"
        ),
        "claim": "FX_STATUS = UNINSTANTIATED_REQUIRES_PRODUCTIVE_USD_USDC_EVIDENCE",
        "evidence_source": "current Python contract constant",
        "epistemic_class": "CANONICAL_AUTHORITY",
        "current_applicability": "CURRENT_RUNTIME_CONTRACT_STATUS",
        "superseded_stale": "false",
        "contradictions": "NONE",
        "relation_to_current_sui": "STANDING_UNINSTANTIATED_NOT_OPERATOR",
    },
    {
        "path": (
            "evidence/ops/section_11_13_5_z2g_current_markpx_public_get_v1/"
            "20260818T200745Z/claims.json"
        ),
        "claim": "FX_STATUS=UNPROVEN INSTRUMENT_ID=BTC-USD_UM_XPERP-310404 markPx observed not FX",
        "evidence_source": "forensic GET pack Z2G",
        "epistemic_class": "FORENSIC_RAW_ORIGINALS",
        "current_applicability": "NOT_CURRENT_SUI_FX_OPERATOR",
        "superseded_stale": "true_btc_era_and_explicitly_unproven_fx",
        "contradictions": "NONE",
        "relation_to_current_sui": "SCOPE_MISMATCH_BTC_NOT_SUI",
    },
    {
        "path": (
            "evidence/ops/section_11_13_5_z2h_current_ticker_bid_ask_public_get_v1/"
            "20260818T203435Z/claims.json"
        ),
        "claim": "FX_STATUS=UNPROVEN ticker bid/ask observed not FX",
        "evidence_source": "forensic GET pack Z2H",
        "epistemic_class": "FORENSIC_RAW_ORIGINALS",
        "current_applicability": "NOT_CURRENT_SUI_FX_OPERATOR",
        "superseded_stale": "true_btc_era_and_explicitly_unproven_fx",
        "contradictions": "NONE",
        "relation_to_current_sui": "SCOPE_MISMATCH_BTC_NOT_SUI",
    },
    {
        "path": (
            "evidence/ops/section_11_13_5_z2k_current_public_tier_mmr_public_get_v1/"
            "20260819T085545Z/claims.json"
        ),
        "claim": "FX_STATUS=UNPROVEN public-tier MMR observed not FX",
        "evidence_source": "forensic GET pack Z2K",
        "epistemic_class": "FORENSIC_RAW_ORIGINALS",
        "current_applicability": "NOT_CURRENT_SUI_FX_OPERATOR",
        "superseded_stale": "true_btc_era_and_explicitly_unproven_fx",
        "contradictions": "NONE",
        "relation_to_current_sui": "SCOPE_MISMATCH_BTC_NOT_SUI",
    },
    {
        "path": (
            "evidence/ops/section_11_13_5_v_fresh_xperp_trade_fee_get_evidence_v1/"
            "20260816T075803Z/claims.json"
        ),
        "claim": "RULE_FX_STATUS=UNPROVEN fee GET pack is not FX operator",
        "evidence_source": "forensic GET pack section V",
        "epistemic_class": "FORENSIC_RAW_ORIGINALS",
        "current_applicability": "NOT_CURRENT_SUI_FX_OPERATOR",
        "superseded_stale": "true_btc_era_fee_family_not_fx",
        "contradictions": "NONE",
        "relation_to_current_sui": "SCOPE_MISMATCH_BTC_FAMILY_NOT_SUI_FX",
    },
    {
        "path": (
            "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/"
            "cover_usdc_current_markpx_productive_evidence_v1.py"
        ),
        "claim": "GET-path helper carries FX_STATUS; name and FX field are not FX operator proof",
        "evidence_source": "historical GET-path module",
        "epistemic_class": "HISTORICAL_INTERMEDIATE_STATE",
        "current_applicability": "MODULE_EXISTS_NOT_CURRENT_FX_PROOF",
        "superseded_stale": "btc_era_get_path_not_re_run",
        "contradictions": "NONE",
        "relation_to_current_sui": "NAME_IS_NOT_PROOF",
    },
    {
        "path": (
            "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/governance_state_matrix_v1.py"
        ),
        "claim": "historical next pointers requiring later FX/rounding evidence",
        "evidence_source": "governance state matrix historical pointers",
        "epistemic_class": "HISTORICAL_INTERMEDIATE_STATE",
        "current_applicability": "POINTER_NOT_CURRENT_FX_PROOF",
        "superseded_stale": "historical_next_pointers",
        "contradictions": "NONE",
        "relation_to_current_sui": "DOES_NOT_PROVE_FX",
    },
    {
        "path": "docs/governance/PEAK_TRADE_MAP_OF_TRUTH.md",
        "claim": "navigation pointers RULE_FX_STATUS=UNPROVEN FX_STATUS=UNPROVEN CLIENT_FX_PROPOSITION_VERDICT=UNPROVEN",
        "evidence_source": "Map of Truth",
        "epistemic_class": "NAVIGATION_INDEX_ONLY",
        "current_applicability": "NAVIGATION_NOT_AUTHORITY",
        "superseded_stale": "false_as_navigation",
        "contradictions": "NONE",
        "relation_to_current_sui": "POINTER_ONLY",
    },
    {
        "path": "docs/system_atlas/entities/catalog.yaml",
        "claim": "Atlas PHASE:z2cv notes FX not adjudicated; Atlas is not trading authority",
        "evidence_source": "Atlas catalog",
        "epistemic_class": "NAVIGATION_INDEX_ONLY",
        "current_applicability": "NAVIGATION_NOT_AUTHORITY",
        "superseded_stale": "false_as_navigation",
        "contradictions": "NONE",
        "relation_to_current_sui": "POINTER_ONLY",
    },
    {
        "path": "tests/ops/test_section_11_13_5_z2aj_usd_usdc_public_get_adjudication_persist_v1.py",
        "claim": "offline tests bind idxPx=1 is not USD/USDC operator and forbid upgrade from idxPx=1",
        "evidence_source": "existing Z2AJ persist tests",
        "epistemic_class": "ALREADY_ADJUDICATED_CONCLUSIONS",
        "current_applicability": "BINDING_NEGATIVE_TEST_OWNER",
        "superseded_stale": "false",
        "contradictions": "NONE",
        "relation_to_current_sui": "NEGATIVE_CONTRACT_STILL_IN_FORCE",
    },
    {
        "path": "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md#11.13.5.Z2AR",
        "claim": (
            "SUI_REPROOF_REQUIREMENTS includes USD_USDC_account_settlement; "
            "FX is a later named remaining class and is not that settlement class"
        ),
        "evidence_source": "canonical persist Z2AR SUI reproof boundary",
        "epistemic_class": "CANONICAL_AUTHORITY",
        "current_applicability": "RELATED_SIBLING_NOT_FX_PROOF",
        "superseded_stale": "false",
        "contradictions": "NONE",
        "relation_to_current_sui": "DOES_NOT_COLLAPSE_FX_WITH_ACCOUNT_SETTLEMENT",
    },
)

FORENSIC_SOURCE_COUNT = len(CENSUS_ENTRIES)
CENSUS_COMPLETE = True
CONTRADICTION_COUNT = 0
EPISTEMIC_CLASSES_PRESENT: tuple[str, ...] = (
    "CANONICAL_AUTHORITY",
    "FORENSIC_RAW_ORIGINALS",
    "ALREADY_ADJUDICATED_CONCLUSIONS",
    "HISTORICAL_INTERMEDIATE_STATE",
    "NAVIGATION_INDEX_ONLY",
)

NEXT_AUTHORITY_BOUNDARY = (
    "SEPARATE_SCOPED_OWNER_GO_REQUIRED_REMAINING_UNRANKED_Z2AR_CLASSES_"
    "ROUNDING_FINISHED_RISK_ENVELOPE_NUMERIC_USD_USDC_ACCOUNT_SETTLEMENT_"
    "STILL_UNRANKED_OR_ALTERNATIVE_P3_ELIGIBLE_TRACK_NO_FX_UPGRADE_"
    "WITHOUT_NEW_FIRST_PARTY_PROOF_NO_IDXPX_1_NORMALIZATION_NO_USD_EQUALS_USDC_"
    "NO_GET_UNLESS_SEPARATELY_NAMED_NO_CLASS_D_NO_Z2AP_NO_FLATTEN_NO_MERGE"
)

ALLOWED_ADJUDICATION_STATES: frozenset[str] = frozenset(
    {
        "REPROVEN",
        "NOT_REPROVEN_MISSING_EVIDENCE",
        "NOT_REPROVEN_STALE_EVIDENCE",
        "NOT_REPROVEN_SCOPE_MISMATCH",
        "NOT_REPROVEN_CONTRADICTORY",
        "NOT_APPLICABLE",
    }
)


class LiveCanaryZ2arFxOfflineReproofError(RuntimeError):
    """Fail-closed FX offline reproof violation."""


def _fail(code: str) -> None:
    raise LiveCanaryZ2arFxOfflineReproofError(code)


def reject_historical_or_navigation_upgrade_v1(
    *,
    upgrade_historical_to_proven: bool = False,
    upgrade_navigation_to_proven: bool = False,
) -> None:
    """Historical existence and navigation indexes are not FX proof."""
    if upgrade_historical_to_proven:
        _fail("FORBIDDEN_UPGRADE_HISTORICAL_TO_PROVEN")
    if upgrade_navigation_to_proven:
        _fail("FORBIDDEN_UPGRADE_NAVIGATION_TO_PROVEN")


def reject_idxpx_one_normalization_v1(
    *,
    treat_idxpx_one_as_fx_proven: bool = False,
) -> None:
    """idxPx=1 is observation only. It is not an FX operator."""
    if treat_idxpx_one_as_fx_proven:
        _fail("FORBIDDEN_IDXPX_1_NORMALIZED_TO_FX_PROVEN")


def reject_usd_equals_usdc_normalization_v1(
    *,
    treat_usd_equals_usdc_as_operator: bool = False,
) -> None:
    """USD≈USDC is not a conversion-operator proof."""
    if treat_usd_equals_usdc_as_operator:
        _fail("FORBIDDEN_USD_EQUALS_USDC_NORMALIZED_TO_OPERATOR")


def reject_class_collapse_v1(
    *,
    mix_with_rounding: bool = False,
    mix_with_account_settlement: bool = False,
    mix_with_cover_usdc: bool = False,
    mix_with_risk_envelope_numeric: bool = False,
    named_class: str = Z2AR_CLASS,
) -> None:
    """FX must not be collapsed onto sibling Z2AR classes."""
    if named_class != Z2AR_CLASS:
        _fail("FORBIDDEN_Z2AR_CLASS_MISMATCH")
    if mix_with_rounding:
        _fail("FORBIDDEN_COLLAPSE_FX_WITH_ROUNDING")
    if mix_with_account_settlement:
        _fail("FORBIDDEN_COLLAPSE_FX_WITH_ACCOUNT_SETTLEMENT")
    if mix_with_cover_usdc:
        _fail("FORBIDDEN_COLLAPSE_FX_WITH_COVER_USDC")
    if mix_with_risk_envelope_numeric:
        _fail("FORBIDDEN_COLLAPSE_FX_WITH_RISK_ENVELOPE_NUMERIC")


def reject_implied_runtime_v1(
    *,
    implied_venue_observation: bool = False,
    execution_ready_claim: bool = False,
    get_performed_claim: bool = False,
    post_performed_claim: bool = False,
    flatten_performed_claim: bool = False,
    class_d_consumed_claim: bool = False,
    z2ap_consumed_claim: bool = False,
) -> None:
    """This reproof must not imply venue observation or execution."""
    if implied_venue_observation or get_performed_claim:
        _fail("FORBIDDEN_IMPLIED_VENUE_OBSERVATION")
    if post_performed_claim:
        _fail("FORBIDDEN_POST")
    if flatten_performed_claim:
        _fail("FORBIDDEN_FLATTEN")
    if class_d_consumed_claim:
        _fail("FORBIDDEN_CLASS_D_CONSUME")
    if z2ap_consumed_claim:
        _fail("FORBIDDEN_Z2AP_CONSUME")
    if execution_ready_claim:
        _fail("FORBIDDEN_EXECUTION_READY_FROM_REPROOF")


def reject_reproven_without_required_inputs_v1(
    *,
    claimed_status: str,
    claimed_reproof_proven: bool,
) -> None:
    """REPROVEN requires every current definitional input to be present."""
    if claimed_status == "REPROVEN" or claimed_reproof_proven is True:
        _fail("FORBIDDEN_REPROVEN_MISSING_REQUIRED_INPUTS")
    if claimed_status not in ALLOWED_ADJUDICATION_STATES:
        _fail("FORBIDDEN_UNKNOWN_ADJUDICATION_STATE")
    if claimed_status == "NOT_APPLICABLE":
        _fail("FORBIDDEN_NOT_APPLICABLE_CLASS_IS_NAMED_REMAINING")
    if claimed_status == "NOT_REPROVEN_CONTRADICTORY":
        _fail("FORBIDDEN_CONTRADICTION_CLAIM_WITHOUT_CONTRADICTION")


def adjudicate_fx_offline_reproof_v1(
    *,
    claimed_status: str | None = None,
    claimed_reproof_proven: bool | None = None,
    mix_with_rounding: bool = False,
    mix_with_account_settlement: bool = False,
    mix_with_cover_usdc: bool = False,
    mix_with_risk_envelope_numeric: bool = False,
    implied_venue_observation: bool = False,
    execution_ready_claim: bool = False,
    get_performed_claim: bool = False,
    post_performed_claim: bool = False,
    flatten_performed_claim: bool = False,
    class_d_consumed_claim: bool = False,
    z2ap_consumed_claim: bool = False,
    upgrade_historical_to_proven: bool = False,
    upgrade_navigation_to_proven: bool = False,
    treat_idxpx_one_as_fx_proven: bool = False,
    treat_usd_equals_usdc_as_operator: bool = False,
    named_class: str = Z2AR_CLASS,
) -> dict[str, Any]:
    """Return the fail-closed FX offline reproof. Caller facts only."""
    if BOUND_RULE_FX != "FX-VENUE-CONVERT":
        _fail("DRIFT_BOUND_RULE_FX")
    if BOUND_RULE_FX_STATUS != "UNPROVEN":
        _fail("DRIFT_BOUND_RULE_FX_STATUS_NOT_UNPROVEN")
    if BOUND_FX_STATUS != "UNPROVEN":
        _fail("DRIFT_BOUND_FX_STATUS_NOT_UNPROVEN")
    if BOUND_FX_APPLIED is True:
        _fail("DRIFT_FX_APPLIED")
    if BOUND_USD_USDC_CONVERSION_APPLIED is True:
        _fail("DRIFT_USD_USDC_CONVERSION_APPLIED")
    if BOUND_USD_USDC_PARITY_ASSUMED is True:
        _fail("DRIFT_USD_USDC_PARITY_ASSUMED")
    if BOUND_ROUNDING_APPLIED is True:
        _fail("DRIFT_ROUNDING_APPLIED")

    reject_class_collapse_v1(
        mix_with_rounding=mix_with_rounding,
        mix_with_account_settlement=mix_with_account_settlement,
        mix_with_cover_usdc=mix_with_cover_usdc,
        mix_with_risk_envelope_numeric=mix_with_risk_envelope_numeric,
        named_class=named_class,
    )
    reject_implied_runtime_v1(
        implied_venue_observation=implied_venue_observation,
        execution_ready_claim=execution_ready_claim,
        get_performed_claim=get_performed_claim,
        post_performed_claim=post_performed_claim,
        flatten_performed_claim=flatten_performed_claim,
        class_d_consumed_claim=class_d_consumed_claim,
        z2ap_consumed_claim=z2ap_consumed_claim,
    )
    reject_historical_or_navigation_upgrade_v1(
        upgrade_historical_to_proven=upgrade_historical_to_proven,
        upgrade_navigation_to_proven=upgrade_navigation_to_proven,
    )
    reject_idxpx_one_normalization_v1(
        treat_idxpx_one_as_fx_proven=treat_idxpx_one_as_fx_proven,
    )
    reject_usd_equals_usdc_normalization_v1(
        treat_usd_equals_usdc_as_operator=treat_usd_equals_usdc_as_operator,
    )

    status = claimed_status if claimed_status is not None else ADJUDICATION
    proven = claimed_reproof_proven if claimed_reproof_proven is not None else REPROOF_PROVEN
    reject_reproven_without_required_inputs_v1(
        claimed_status=status,
        claimed_reproof_proven=bool(proven),
    )
    if status != ADJUDICATION:
        _fail("FORBIDDEN_STATUS_MISMATCH_WITH_CENSUS")
    if proven is not False:
        _fail("FORBIDDEN_REPROOF_PROVEN")

    return {
        "OWNER_GO": OWNER_GO,
        "THIS_SLICE": THIS_SLICE,
        "PREDECESSOR_SLICE": PREDECESSOR_SLICE,
        "Z2AR_CLASS": Z2AR_CLASS,
        "ADJUDICATION": ADJUDICATION,
        "CURRENT_FX_STATUS": CURRENT_FX_STATUS,
        "REPROOF_PROVEN": REPROOF_PROVEN,
        "RULE_FX": RULE_FX,
        "RULE_FX_STATUS": RULE_FX_STATUS,
        "FX_STATUS": FX_STATUS,
        "FX_APPLIED": FX_APPLIED,
        "FX_OPERATOR_PROVEN": FX_OPERATOR_PROVEN,
        "CENSUS_COMPLETE": CENSUS_COMPLETE,
        "FORENSIC_SOURCE_COUNT": FORENSIC_SOURCE_COUNT,
        "BLOCKING_EVIDENCE_GAPS": BLOCKING_EVIDENCE_GAPS,
        "REMAINING_UNRANKED_AFTER_THIS_CLASS": REMAINING_UNRANKED_AFTER_THIS_CLASS,
        "SUI_REPROOF_CLASSES_RANKED": SUI_REPROOF_CLASSES_RANKED,
        "CURRENT_CANONICAL_INSTRUMENT": CURRENT_CANONICAL_INSTRUMENT,
        "CLASS_D_CONSUMED": CLASS_D_CONSUMED,
        "Z2AP_CONSUMED": Z2AP_CONSUMED,
        "EXECUTION_READY": EXECUTION_READY,
        "THIS_GO_AUTHORIZES_GET": THIS_GO_AUTHORIZES_GET,
        "THIS_GO_AUTHORIZES_POST": THIS_GO_AUTHORIZES_POST,
        "THIS_GO_AUTHORIZES_FLATTEN": THIS_GO_AUTHORIZES_FLATTEN,
        "RUNTIME_AUTHORIZATION_EFFECT": RUNTIME_AUTHORIZATION_EFFECT,
        "RUNTIME_API_CALLS": RUNTIME_API_CALLS,
        "GET_PERFORMED": GET_PERFORMED,
        "POST_PERFORMED": POST_PERFORMED,
        "FLATTEN_PERFORMED": FLATTEN_PERFORMED,
        "NEXT_AUTHORITY_BOUNDARY": NEXT_AUTHORITY_BOUNDARY,
        "IDXPX_1_IS_NOT_FX_OPERATOR": IDXPX_1_IS_NOT_FX_OPERATOR,
        "USD_EQUALS_USDC_ASSUMED": USD_EQUALS_USDC_ASSUMED,
        "CONTRADICTION_COUNT": CONTRADICTION_COUNT,
    }
