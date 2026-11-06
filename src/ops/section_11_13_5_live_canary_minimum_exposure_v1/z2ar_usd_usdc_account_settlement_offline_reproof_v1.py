"""§11.13.5.Z2CX USD_USDC_ACCOUNT_SETTLEMENT offline reproof.

CONTRACT / GOVERNANCE only. Adjudicates the already-bound
USD_USDC_ACCOUNT_SETTLEMENT class against repo-internal canonical persist,
forensic originals, and navigation indexes. Does not observe a venue.
Does not treat Z2J semantic denomination as account-settlement proof.
Does not treat idxPx=1 or USD≈USDC as an operator. Does not adjudicate
COVER_USDC or reopen FX. Does not adjudicate ROUNDING or
FINISHED_RISK_ENVELOPE_NUMERIC as this class. Does not authorize Live,
Testnet, orders, funding, GET, POST, flatten, Class D, or Z2AP.
"""

from __future__ import annotations

from typing import Any, Mapping

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    SETTLEMENT_ACCOUNT_TRUTH as BOUND_SETTLEMENT_ACCOUNT_TRUTH,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.position_value_fx_rounding_chain_v1 import (
    ACCOUNT_SETTLE_CCY as BOUND_ACCOUNT_SETTLE_CCY,
    PUBLIC_SETTLE_CCY as BOUND_PUBLIC_SETTLE_CCY,
    USD_USDC_CONVERSION_APPLIED as BOUND_USD_USDC_CONVERSION_APPLIED,
    USD_USDC_PARITY_ASSUMED as BOUND_USD_USDC_PARITY_ASSUMED,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.z2ar_fx_offline_reproof_v1 import (
    CLIENT_FX_PROPOSITION_VERDICT as BOUND_CLIENT_FX_PROPOSITION_VERDICT,
    CONVERSION_NUMERIC_STATUS as BOUND_CONVERSION_NUMERIC_STATUS,
    CURRENT_FX_STATUS as BOUND_CURRENT_FX_STATUS,
    VENUE_NUMERIC_CONVERSION_OPERATOR_PROVEN as BOUND_VENUE_NUMERIC_CONVERSION_OPERATOR_PROVEN,
)

OWNER_GO = "PEAK_TRADE_OWNER_GO_Z2AR_REMAINING_UNRANKED_OFFLINE_REPROOF_BUNDLE_V1"
THIS_SLICE = "11.13.5.Z2CX"
PREDECESSOR_SLICE = "11.13.5.Z2CW"
LAST_CANONICALLY_CLOSED_11_13_5_SLICE = "SECTION_11_13_5_Z2CT"
THIS_PERSIST_DOES_NOT_SUPERSEDE_Z2CT_AS_LAST_CANONICALLY_CLOSED_11_13_5_SLICE = True
THIS_PERSIST_DOES_NOT_REWRITE_Z2CW = True
THIS_NAMED_CLASS_PERSIST_ID = "SECTION_11_13_5_Z2CX"

Z2AR_CLASS = "USD_USDC_ACCOUNT_SETTLEMENT"
EXACT_Z2AR_CLASS = "USD_USDC_ACCOUNT_SETTLEMENT"
AUTHORIZED_SCOPE = "P3_Z2AR_REMAINING_UNRANKED_SUI_REPROOF"
ADJUDICATION = "NOT_REPROVEN_MISSING_EVIDENCE"
CURRENT_USD_USDC_ACCOUNT_SETTLEMENT_STATUS = "NOT_REPROVEN_MISSING_EVIDENCE"
REPROOF_PROVEN = False
USD_USDC_ACCOUNT_SETTLEMENT_PROVEN = False
PUBLIC_SETTLE_CCY = "USD"
ACCOUNT_SETTLE_CCY = "USDC"
USD_AND_USDC_REMAIN_STRICTLY_DISTINCT_UNITS = True
NO_USD_EQUALS_USDC = True
USD_EQUALS_USDC_ASSUMED = False
IDXPX_1_IS_NOT_USD_USDC_OPERATOR = True
IDXPX_1_IS_NOT_ACCOUNT_SETTLEMENT_OPERATOR = True
Z2J_SEMANTIC_PROPOSITION_IS_NOT_ACCOUNT_SETTLEMENT_PROOF = True
CONVERSION_NUMERIC_STATUS = "UNINSTANTIATED_REQUIRES_LATER_PRODUCTIVE_USD_USDC_EVIDENCE"
VENUE_NUMERIC_CONVERSION_OPERATOR_PROVEN = False
CLIENT_FX_PROPOSITION_VERDICT = "UNPROVEN"
NO_CLIENT_CONVERSION_REQUIRED_PROVEN = False

CURRENT_CANONICAL_INSTRUMENT = "SUI-USD_UM_XPERP-310404"
CURRENT_SUI_BINDING = "SUI-USD_UM_XPERP-310404"

SUI_REPROOF_CLASSES_RANKED = False
NO_RANKING_OF_REMAINDER = True
REMAINING_UNRANKED_AFTER_THIS_CLASS: tuple[str, ...] = ()
FORBIDDEN_COLLAPSE_CLASSES = (
    "COVER_USDC",
    "FX",
    "ROUNDING",
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
FX_REOPENED = False
COVER_USDC_ADJUDICATED = False

FORBIDDEN_UPGRADE_HISTORICAL_TO_PROVEN = True
FORBIDDEN_UPGRADE_NAVIGATION_TO_PROVEN = True
FORBIDDEN_UPGRADE_FROM_IDXPX_1 = True
FORBIDDEN_UPGRADE_SEMANTIC_PROPOSITION_TO_ACCOUNT_SETTLEMENT = True
FORBIDDEN_UPGRADE_PUBLIC_SETTLECCY_USD_TO_ACCOUNT_SETTLEMENT = True
NUMERICAL_EQUALITY_IS_NOT_OPERATOR_PROOF = True

REQUIRED_INPUTS_FOR_REPROVEN: tuple[str, ...] = (
    "PRODUCTIVE_USD_USDC_ACCOUNT_CONVERSION_OR_SETTLEMENT_EVIDENCE",
    "NUMERIC_CONVERSION_OPERATOR_OR_NO_CLIENT_CONVERSION_REQUIRED_PROVEN",
    "NO_IDXPX_1_NORMALIZATION",
    "NO_USD_EQUALS_USDC_NORMALIZATION",
    "NO_UPGRADE_FROM_Z2J_SEMANTIC_PROPOSITION",
    "CURRENT_SUI_BINDING",
    "NO_CONTRADICTORY_CANONICAL_AUTHORITY",
)

CURRENT_REQUIRED_INPUT_STATE: Mapping[str, str] = {
    "PUBLIC_SETTLE_CCY": "USD",
    "ACCOUNT_SETTLE_CCY": "USDC",
    "UNITS": "STRICTLY_DISTINCT",
    "USD_USDC_ACCOUNT_SETTLEMENT_PROVEN": "false",
    "CONVERSION_NUMERIC_STATUS": "UNINSTANTIATED_REQUIRES_LATER_PRODUCTIVE_USD_USDC_EVIDENCE",
    "VENUE_NUMERIC_CONVERSION_OPERATOR_PROVEN": "false",
    "CLIENT_FX_PROPOSITION_VERDICT": "UNPROVEN",
    "Z2J_SEMANTIC_PROPOSITION": "PROVEN_DENOMINATION_NOT_ACCOUNT_SETTLEMENT_CLASS",
    "CURRENT_SUI_INSTRUMENT_BINDING": "SUI-USD_UM_XPERP-310404",
    "CONTRADICTORY_CANONICAL_AUTHORITY": "NONE",
}

BLOCKING_EVIDENCE_GAPS: tuple[str, ...] = (
    "USD_USDC_ACCOUNT_SETTLEMENT_PROVEN=false",
    "CONVERSION_NUMERIC_STATUS=UNINSTANTIATED_REQUIRES_LATER_PRODUCTIVE_USD_USDC_EVIDENCE",
    "VENUE_NUMERIC_CONVERSION_OPERATOR_PROVEN=false",
    "CLIENT_FX_PROPOSITION_VERDICT=UNPROVEN",
    "NO_CLIENT_CONVERSION_REQUIRED_PROVEN=false",
    "IDXPX_1_IS_NOT_USD_USDC_OPERATOR",
    "Z2J_SEMANTIC_PROPOSITION_IS_NOT_ACCOUNT_SETTLEMENT_PROOF",
    "FORBIDDEN_UPGRADE_PUBLIC_SETTLECCY_USD_TO_USD_USDC_OR_ACCOUNT_SETTLEMENT_PROVEN",
    "FRESH_SUI_BOUND_ACCOUNT_SETTLEMENT_OPERATOR_ABSENT",
)

CENSUS_ENTRIES: tuple[Mapping[str, str], ...] = (
    {
        "path": "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md#11.13.5.U",
        "claim": (
            "PUBLIC_SETTLE_CCY=USD ACCOUNT_SETTLE_CCY=USDC "
            "USD_AND_USDC_REMAIN_STRICTLY_DISTINCT_UNITS=true "
            "NO_IMPLICIT_ONE_TO_ONE_EQUIVALENCE=true "
            "CONVERSION_NUMERIC_STATUS=UNINSTANTIATED_REQUIRES_LATER_PRODUCTIVE_USD_USDC_EVIDENCE"
        ),
        "evidence_source": "canonical persist Z2U policy form",
        "epistemic_class": "CANONICAL_AUTHORITY",
        "current_applicability": "BINDING_UNIT_SPLIT_NOT_SETTLEMENT_OPERATOR",
        "superseded_stale": "false",
        "contradictions": "NONE",
        "relation_to_current_sui": "DEFINITION_INHERITED_SUI_BOUND_VIA_Z2BX_Z2BY",
    },
    {
        "path": "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md#11.13.5.Z2J",
        "claim": (
            "SEMANTIC_PROPOSITION_VERDICT=PROVEN "
            "NUMERIC_PROPOSITION_VERDICT=UNPROVEN "
            "CLIENT_FX_PROPOSITION_VERDICT=UNPROVEN "
            "VENUE_NUMERIC_CONVERSION_OPERATOR_PROVEN=false "
            "SEMANTIC_PROPOSITION_DOES_NOT_PROVE_QTY1_USDC_AMOUNT=true"
        ),
        "evidence_source": "canonical persist Z2J settlement-semantic adjudication",
        "epistemic_class": "ALREADY_ADJUDICATED_CONCLUSIONS",
        "current_applicability": "SEMANTIC_DENOMINATION_NOT_ACCOUNT_SETTLEMENT_CLASS",
        "superseded_stale": "false",
        "contradictions": "NONE",
        "relation_to_current_sui": "SEMANTIC_PROPOSITION_IS_NOT_SUI_ACCOUNT_SETTLEMENT_OPERATOR",
    },
    {
        "path": "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md#11.13.5.Z2AJ",
        "claim": (
            "GET_1_IDXPX=1 IDXPX_1_IS_NOT_USD_USDC_OPERATOR=true "
            "USD_USDC_OPERATOR_STATUS=UNPROVEN FORBIDDEN_UPGRADE_FROM_IDXPX_1=true"
        ),
        "evidence_source": "canonical persist Z2AJ of four prior public EEA GETs",
        "epistemic_class": "ALREADY_ADJUDICATED_CONCLUSIONS",
        "current_applicability": "BINDING_NEGATIVE_OPERATOR_CONTRACT",
        "superseded_stale": "GET_WINDOW_HISTORICAL_CONCLUSION_STILL_BINDING",
        "contradictions": "NONE",
        "relation_to_current_sui": "IDXPX_1_IS_NOT_CURRENT_SUI_ACCOUNT_SETTLEMENT_OPERATOR",
    },
    {
        "path": "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md#11.13.5.Z2AJ",
        "claim": (
            "GET_1_PATH=/api/v5/market/index-tickers?instId=USDC-USD "
            "GET_1_IDXPX=1 observation transcribed into SSOT; not a settlement operator"
        ),
        "evidence_source": "Z2AJ recorded public GET values; no separate evidence pack file",
        "epistemic_class": "FORENSIC_RAW_ORIGINALS",
        "current_applicability": "NOT_CURRENT_SUI_ACCOUNT_SETTLEMENT_OPERATOR",
        "superseded_stale": "true_btc_era_window_and_explicitly_non_operator",
        "contradictions": "NONE",
        "relation_to_current_sui": "SCOPE_MISMATCH_INDEX_OBSERVATION_NOT_SUI_SETTLEMENT",
    },
    {
        "path": "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md#11.13.5.Z2AR",
        "claim": (
            "REPROOF_SET_CONTAINS_USD_USDC_ACCOUNT_SETTLEMENT=true "
            "FORBIDDEN_UPGRADE_PUBLIC_SETTLECCY_USD_TO_USD_USDC_OR_ACCOUNT_SETTLEMENT_PROVEN=true "
            "BINDING_USD_USDC_HANDLING_REMAINS_UNPROVEN_PROBLEM_CLASS=true "
            "PUBLIC_SETTLECCY_USD_NE_ACCOUNT_SETTLEMENT_OR_FX_PROOF=true"
        ),
        "evidence_source": "canonical persist Z2AR SUI reproof boundary",
        "epistemic_class": "CANONICAL_AUTHORITY",
        "current_applicability": "BINDING_NEGATIVE_UPGRADE_FORBIDDEN",
        "superseded_stale": "false",
        "contradictions": "NONE",
        "relation_to_current_sui": "NAMES_REQUIREMENT_DOES_NOT_PROVE_IT",
    },
    {
        "path": "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md#11.13.5.Z2D",
        "claim": "USD_USDC_CONVERSION_APPLIED=false USD_USDC_PARITY_ASSUMED=false",
        "evidence_source": "canonical persist Z2D",
        "epistemic_class": "CANONICAL_AUTHORITY",
        "current_applicability": "BINDING_NEGATIVE_STATUS",
        "superseded_stale": "false",
        "contradictions": "NONE",
        "relation_to_current_sui": "STATUS_INHERITED_NOT_SUI_ACCOUNT_SETTLEMENT",
    },
    {
        "path": "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md#11.13.5.Z2BX",
        "claim": (
            "USD_USDC_ACCOUNT_SETTLEMENT_PROVEN=false USD_USDC_OPERATOR_STATUS=UNPROVEN "
            "USD_EQUALS_USDC_ASSUMED=false IDXPX_1_IS_NOT_USD_USDC_OPERATOR=true"
        ),
        "evidence_source": "canonical persist Z2BX P5 Cover negative contract",
        "epistemic_class": "CANONICAL_AUTHORITY",
        "current_applicability": "BINDING_NEGATIVE_STATUS",
        "superseded_stale": "false",
        "contradictions": "NONE",
        "relation_to_current_sui": "BOUND_FOR_SUI-USD_UM_XPERP-310404_NOT_SETTLEMENT_PROOF",
    },
    {
        "path": "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md#11.13.5.Z2CW",
        "claim": (
            "USD_USDC_ACCOUNT_SETTLEMENT_ADJUDICATED_THIS_PERSIST=false "
            "USD_USDC_ACCOUNT_SETTLEMENT_PROVEN=false as FX blocker only "
            "IDXPX_1_IS_NOT_USD_USDC_OPERATOR=true"
        ),
        "evidence_source": "canonical persist Z2CW FX offline reproof",
        "epistemic_class": "CANONICAL_AUTHORITY",
        "current_applicability": "SIBLING_CLASS_NOT_ACCOUNT_SETTLEMENT_PROOF",
        "superseded_stale": "false",
        "contradictions": "NONE",
        "relation_to_current_sui": "FX_FAIL_CLOSED_DOES_NOT_PROVE_ACCOUNT_SETTLEMENT",
    },
    {
        "path": "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md#11.13.5.Z2CV",
        "claim": "USD_USDC_ACCOUNT_SETTLEMENT_ADJUDICATED_THIS_PERSIST=false",
        "evidence_source": "canonical persist Z2CV COVER_USDC offline reproof",
        "epistemic_class": "CANONICAL_AUTHORITY",
        "current_applicability": "SIBLING_CLASS_NOT_ACCOUNT_SETTLEMENT_PROOF",
        "superseded_stale": "false",
        "contradictions": "NONE",
        "relation_to_current_sui": "COVER_USDC_FAIL_CLOSED_DOES_NOT_PROVE_ACCOUNT_SETTLEMENT",
    },
    {
        "path": "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md#11.13.5.Z2CU",
        "claim": "REMAINING_UNRANKED_CLASSES includes USD_USDC_ACCOUNT_SETTLEMENT",
        "evidence_source": "canonical persist Z2CU",
        "epistemic_class": "CANONICAL_AUTHORITY",
        "current_applicability": "TRACK_ELIGIBILITY_NOT_SETTLEMENT_PROOF",
        "superseded_stale": "false",
        "contradictions": "NONE",
        "relation_to_current_sui": "NAMES_CLASS_DOES_NOT_PROVE_IT",
    },
    {
        "path": (
            "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/"
            "position_value_fx_rounding_chain_v1.py"
        ),
        "claim": (
            "PUBLIC_SETTLE_CCY = USD ACCOUNT_SETTLE_CCY = USDC "
            "USD_USDC_CONVERSION_APPLIED = False USD_USDC_PARITY_ASSUMED = False"
        ),
        "evidence_source": "current Python contract constant",
        "epistemic_class": "CANONICAL_AUTHORITY",
        "current_applicability": "CURRENT_RUNTIME_CONTRACT_STATUS",
        "superseded_stale": "false",
        "contradictions": "NONE",
        "relation_to_current_sui": "UNIT_SPLIT_STANDING_OPERATOR_UNPROVEN",
    },
    {
        "path": ("src/ops/section_11_13_5_live_canary_minimum_exposure_v1/constants_v1.py"),
        "claim": "SETTLEMENT_ACCOUNT_TRUTH = USDC is account unit identity not USD/USDC operator",
        "evidence_source": "current Python contract constant",
        "epistemic_class": "CANONICAL_AUTHORITY",
        "current_applicability": "ACCOUNT_UNIT_IDENTITY_NOT_SETTLEMENT_OPERATOR",
        "superseded_stale": "false",
        "contradictions": "NONE",
        "relation_to_current_sui": "UNIT_LABEL_IS_NOT_OPERATOR",
    },
    {
        "path": (
            "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/z2ar_fx_offline_reproof_v1.py"
        ),
        "claim": (
            "CURRENT_FX_STATUS=NOT_REPROVEN_MISSING_EVIDENCE "
            "VENUE_NUMERIC_CONVERSION_OPERATOR_PROVEN=false "
            "CONVERSION_NUMERIC_STATUS=UNINSTANTIATED_REQUIRES_LATER_PRODUCTIVE_USD_USDC_EVIDENCE"
        ),
        "evidence_source": "already-adjudicated FX offline reproof contract",
        "epistemic_class": "ALREADY_ADJUDICATED_CONCLUSIONS",
        "current_applicability": "FX_REMAINS_NOT_REPROVEN_NOT_REOPENED",
        "superseded_stale": "false",
        "contradictions": "NONE",
        "relation_to_current_sui": "FX_STATUS_UNCHANGED_NOT_ACCOUNT_SETTLEMENT_PROOF",
    },
    {
        "path": (
            "evidence/ops/section_11_13_5_z2g_current_markpx_public_get_v1/"
            "20260818T200745Z/claims.json"
        ),
        "claim": "BTC-era markPx pack; FX_STATUS=UNPROVEN; not SUI USD/USDC account settlement",
        "evidence_source": "forensic GET pack Z2G",
        "epistemic_class": "FORENSIC_RAW_ORIGINALS",
        "current_applicability": "NOT_CURRENT_SUI_ACCOUNT_SETTLEMENT_OPERATOR",
        "superseded_stale": "true_btc_era_and_explicitly_unproven_fx",
        "contradictions": "NONE",
        "relation_to_current_sui": "SCOPE_MISMATCH_BTC_NOT_SUI",
    },
    {
        "path": (
            "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/governance_state_matrix_v1.py"
        ),
        "claim": "historical next pointers requiring later USD/USDC evidence; pointers are not operators",
        "evidence_source": "governance state matrix historical pointers",
        "epistemic_class": "HISTORICAL_INTERMEDIATE_STATE",
        "current_applicability": "POINTER_NOT_CURRENT_SETTLEMENT_PROOF",
        "superseded_stale": "historical_next_pointers",
        "contradictions": "NONE",
        "relation_to_current_sui": "DOES_NOT_PROVE_ACCOUNT_SETTLEMENT",
    },
    {
        "path": "docs/governance/PEAK_TRADE_MAP_OF_TRUTH.md",
        "claim": "navigation pointers RULE_FX_STATUS=UNPROVEN CLIENT_FX_PROPOSITION_VERDICT=UNPROVEN",
        "evidence_source": "Map of Truth",
        "epistemic_class": "NAVIGATION_INDEX_ONLY",
        "current_applicability": "NAVIGATION_NOT_AUTHORITY",
        "superseded_stale": "false_as_navigation",
        "contradictions": "NONE",
        "relation_to_current_sui": "POINTER_ONLY",
    },
    {
        "path": "docs/system_atlas/entities/catalog.yaml",
        "claim": "Atlas PHASE notes USD_USDC_ACCOUNT_SETTLEMENT not adjudicated; Atlas is not trading authority",
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
    "SEPARATE_OWNER_MERGE_GO_REQUIRED_NO_USD_USDC_ACCOUNT_SETTLEMENT_UPGRADE_"
    "FROM_SEMANTIC_PROPOSITION_OR_IDXPX_1_OR_USD_EQUALS_USDC_NO_GET_UNLESS_"
    "SEPARATELY_NAMED_NO_CLASS_D_NO_Z2AP_NO_FLATTEN"
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


class LiveCanaryZ2arUsdUsdcAccountSettlementOfflineReproofError(RuntimeError):
    """Fail-closed USD_USDC_ACCOUNT_SETTLEMENT offline reproof violation."""


def _fail(code: str) -> None:
    raise LiveCanaryZ2arUsdUsdcAccountSettlementOfflineReproofError(code)


def reject_historical_or_navigation_upgrade_v1(
    *,
    upgrade_historical_to_proven: bool = False,
    upgrade_navigation_to_proven: bool = False,
) -> None:
    """Historical existence and navigation indexes are not settlement proof."""
    if upgrade_historical_to_proven:
        _fail("FORBIDDEN_UPGRADE_HISTORICAL_TO_PROVEN")
    if upgrade_navigation_to_proven:
        _fail("FORBIDDEN_UPGRADE_NAVIGATION_TO_PROVEN")


def reject_idxpx_one_normalization_v1(
    *,
    treat_idxpx_one_as_settlement_proven: bool = False,
) -> None:
    """idxPx=1 is observation only. It is not an account-settlement operator."""
    if treat_idxpx_one_as_settlement_proven:
        _fail("FORBIDDEN_IDXPX_1_NORMALIZED_TO_ACCOUNT_SETTLEMENT_PROVEN")


def reject_usd_equals_usdc_normalization_v1(
    *,
    treat_usd_equals_usdc_as_operator: bool = False,
) -> None:
    """USD≈USDC is not a settlement-operator proof."""
    if treat_usd_equals_usdc_as_operator:
        _fail("FORBIDDEN_USD_EQUALS_USDC_NORMALIZED_TO_OPERATOR")


def reject_semantic_proposition_upgrade_v1(
    *,
    treat_z2j_semantic_proposition_as_account_settlement: bool = False,
) -> None:
    """Z2J semantic denomination is not the USD_USDC_ACCOUNT_SETTLEMENT class."""
    if treat_z2j_semantic_proposition_as_account_settlement:
        _fail("FORBIDDEN_UPGRADE_SEMANTIC_PROPOSITION_TO_ACCOUNT_SETTLEMENT")


def reject_class_collapse_v1(
    *,
    mix_with_fx: bool = False,
    mix_with_rounding: bool = False,
    mix_with_cover_usdc: bool = False,
    mix_with_risk_envelope_numeric: bool = False,
    named_class: str = Z2AR_CLASS,
) -> None:
    """Account settlement must not be collapsed onto sibling Z2AR classes."""
    if named_class != Z2AR_CLASS:
        _fail("FORBIDDEN_Z2AR_CLASS_MISMATCH")
    if mix_with_fx:
        _fail("FORBIDDEN_COLLAPSE_ACCOUNT_SETTLEMENT_WITH_FX")
    if mix_with_rounding:
        _fail("FORBIDDEN_COLLAPSE_ACCOUNT_SETTLEMENT_WITH_ROUNDING")
    if mix_with_cover_usdc:
        _fail("FORBIDDEN_COLLAPSE_ACCOUNT_SETTLEMENT_WITH_COVER_USDC")
    if mix_with_risk_envelope_numeric:
        _fail("FORBIDDEN_COLLAPSE_ACCOUNT_SETTLEMENT_WITH_RISK_ENVELOPE_NUMERIC")


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


def adjudicate_usd_usdc_account_settlement_offline_reproof_v1(
    *,
    claimed_status: str | None = None,
    claimed_reproof_proven: bool | None = None,
    mix_with_fx: bool = False,
    mix_with_rounding: bool = False,
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
    treat_idxpx_one_as_settlement_proven: bool = False,
    treat_usd_equals_usdc_as_operator: bool = False,
    treat_z2j_semantic_proposition_as_account_settlement: bool = False,
    named_class: str = Z2AR_CLASS,
    reopen_fx: bool = False,
    adjudicate_cover_usdc: bool = False,
) -> dict[str, Any]:
    """Return the fail-closed account-settlement offline reproof. Caller facts only."""
    if BOUND_PUBLIC_SETTLE_CCY != "USD":
        _fail("DRIFT_PUBLIC_SETTLE_CCY")
    if BOUND_ACCOUNT_SETTLE_CCY != "USDC":
        _fail("DRIFT_ACCOUNT_SETTLE_CCY")
    if BOUND_SETTLEMENT_ACCOUNT_TRUTH != "USDC":
        _fail("DRIFT_SETTLEMENT_ACCOUNT_TRUTH")
    if BOUND_USD_USDC_CONVERSION_APPLIED is True:
        _fail("DRIFT_USD_USDC_CONVERSION_APPLIED")
    if BOUND_USD_USDC_PARITY_ASSUMED is True:
        _fail("DRIFT_USD_USDC_PARITY_ASSUMED")
    if BOUND_CURRENT_FX_STATUS != "NOT_REPROVEN_MISSING_EVIDENCE":
        _fail("DRIFT_FX_STATUS_REOPENED")
    if BOUND_VENUE_NUMERIC_CONVERSION_OPERATOR_PROVEN is True:
        _fail("DRIFT_VENUE_NUMERIC_CONVERSION_OPERATOR_PROVEN")
    if BOUND_CONVERSION_NUMERIC_STATUS != (
        "UNINSTANTIATED_REQUIRES_LATER_PRODUCTIVE_USD_USDC_EVIDENCE"
    ):
        _fail("DRIFT_CONVERSION_NUMERIC_STATUS")
    if BOUND_CLIENT_FX_PROPOSITION_VERDICT != "UNPROVEN":
        _fail("DRIFT_CLIENT_FX_PROPOSITION_VERDICT")
    if reopen_fx:
        _fail("FORBIDDEN_FX_REOPEN")
    if adjudicate_cover_usdc:
        _fail("FORBIDDEN_COVER_USDC_ADJUDICATION")

    reject_class_collapse_v1(
        mix_with_fx=mix_with_fx,
        mix_with_rounding=mix_with_rounding,
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
        treat_idxpx_one_as_settlement_proven=treat_idxpx_one_as_settlement_proven,
    )
    reject_usd_equals_usdc_normalization_v1(
        treat_usd_equals_usdc_as_operator=treat_usd_equals_usdc_as_operator,
    )
    reject_semantic_proposition_upgrade_v1(
        treat_z2j_semantic_proposition_as_account_settlement=(
            treat_z2j_semantic_proposition_as_account_settlement
        ),
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
        "CURRENT_USD_USDC_ACCOUNT_SETTLEMENT_STATUS": (CURRENT_USD_USDC_ACCOUNT_SETTLEMENT_STATUS),
        "REPROOF_PROVEN": REPROOF_PROVEN,
        "USD_USDC_ACCOUNT_SETTLEMENT_PROVEN": USD_USDC_ACCOUNT_SETTLEMENT_PROVEN,
        "PUBLIC_SETTLE_CCY": PUBLIC_SETTLE_CCY,
        "ACCOUNT_SETTLE_CCY": ACCOUNT_SETTLE_CCY,
        "USD_EQUALS_USDC_ASSUMED": USD_EQUALS_USDC_ASSUMED,
        "IDXPX_1_IS_NOT_USD_USDC_OPERATOR": IDXPX_1_IS_NOT_USD_USDC_OPERATOR,
        "Z2J_SEMANTIC_PROPOSITION_IS_NOT_ACCOUNT_SETTLEMENT_PROOF": (
            Z2J_SEMANTIC_PROPOSITION_IS_NOT_ACCOUNT_SETTLEMENT_PROOF
        ),
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
        "FX_REOPENED": FX_REOPENED,
        "COVER_USDC_ADJUDICATED": COVER_USDC_ADJUDICATED,
        "NEXT_AUTHORITY_BOUNDARY": NEXT_AUTHORITY_BOUNDARY,
        "CONTRADICTION_COUNT": CONTRADICTION_COUNT,
    }
