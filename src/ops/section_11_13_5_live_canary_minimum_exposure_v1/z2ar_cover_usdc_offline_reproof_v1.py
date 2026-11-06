"""§11.13.5.Z2CV COVER_USDC offline reproof.

CONTRACT / GOVERNANCE only. Adjudicates the already-bound COVER_USDC
class against repo-internal canonical persist, forensic originals, and
navigation indexes. Does not observe a venue. Does not instantiate
COVER_USDC. Does not adjudicate FX, ROUNDING, FINISHED_RISK_ENVELOPE_NUMERIC,
or USD_USDC_ACCOUNT_SETTLEMENT as classes. Does not authorize Live,
Testnet, orders, funding, GET, POST, flatten, Class D, or Z2AP.
"""

from __future__ import annotations

from typing import Any, Mapping

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.position_value_fx_rounding_chain_v1 import (
    COVER_USDC_STATUS as BOUND_COVER_USDC_STATUS,
    ROUNDING_APPLIED as BOUND_ROUNDING_APPLIED,
    USD_USDC_CONVERSION_APPLIED as BOUND_USD_USDC_CONVERSION_APPLIED,
    USD_USDC_PARITY_ASSUMED as BOUND_USD_USDC_PARITY_ASSUMED,
)

OWNER_GO = "PEAK_TRADE_OWNER_GO_Z2AR_COVER_USDC_REPROOF_OFFLINE_V1"
THIS_SLICE = "11.13.5.Z2CV"
PREDECESSOR_SLICE = "11.13.5.Z2CU"
LAST_CANONICALLY_CLOSED_11_13_5_SLICE = "SECTION_11_13_5_Z2CT"
THIS_PERSIST_DOES_NOT_SUPERSEDE_Z2CT_AS_LAST_CANONICALLY_CLOSED_11_13_5_SLICE = True
THIS_PERSIST_DOES_NOT_REWRITE_Z2CU = True
THIS_NAMED_CLASS_PERSIST_ID = "SECTION_11_13_5_Z2CV"

Z2AR_CLASS = "COVER_USDC"
EXACT_Z2AR_CLASS = "COVER_USDC"
AUTHORIZED_SCOPE = "P3_Z2AR_REMAINING_UNRANKED_SUI_REPROOF"
ADJUDICATION = "NOT_REPROVEN_MISSING_EVIDENCE"
CURRENT_COVER_USDC_STATUS = "NOT_REPROVEN_MISSING_EVIDENCE"
REPROOF_PROVEN = False
COVER_USDC_STATUS = "UNINSTANTIATED"
COVER_USDC_INSTANTIATED = False
COVER_NEGATIVE_CONTRACT_REMAINS_IN_FORCE = True

CURRENT_CANONICAL_INSTRUMENT = "SUI-USD_UM_XPERP-310404"
CURRENT_SUI_BINDING = "SUI-USD_UM_XPERP-310404"

SUI_REPROOF_CLASSES_RANKED = False
NO_RANKING_OF_REMAINDER = True
REMAINING_UNRANKED_AFTER_THIS_CLASS = (
    "FX",
    "ROUNDING",
    "FINISHED_RISK_ENVELOPE_NUMERIC",
    "USD_USDC_ACCOUNT_SETTLEMENT",
)
FORBIDDEN_COLLAPSE_CLASSES = (
    "USD_USDC",
    "FX",
    "RISK_ENVELOPE_NUMERIC",
    "FINISHED_RISK_ENVELOPE_NUMERIC",
    "USD_USDC_ACCOUNT_SETTLEMENT",
    "ROUNDING",
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

Z2BX_COVER_NEGATIVE_CONTRACT_REMAINS_IN_FORCE = True
Z2AJ_COVER_NEGATIVE_CONTRACT_REMAINS_IN_FORCE = True
Z2J_REMAINS_CONTROLLING_FOR_CONVERSION_NUMERIC_STATUS = True
IDXPX_1_IS_NOT_COVER_USDC_OPERATOR = True
USD_EQUALS_USDC_ASSUMED = False
INTERNAL_ENVELOPE_IS_NOT_COVER_USDC = True
COMPOSITION_NUMERIC_IS_NOT_COVER_USDC = True
RISK_ENVELOPE_IDENTITY_IS_NOT_COVER_USDC = True
FORBIDDEN_UPGRADE_FROM_INTERNAL_PEAK_TRADE_ENVELOPES = True
FORBIDDEN_UPGRADE_IDENTITY_TO_COVER_USDC = True
FORBIDDEN_UPGRADE_HISTORICAL_TO_PROVEN = True
FORBIDDEN_UPGRADE_NAVIGATION_TO_PROVEN = True
BTC_ERA_GET_PACKS_ARE_NOT_CURRENT_SUI_COVER_USDC = True

REQUIRED_INPUTS_FOR_REPROVEN: tuple[str, ...] = (
    "USD_USDC_OPERATOR_STATUS=PROVEN",
    "USD_USDC_ACCOUNT_SETTLEMENT_PROVEN=true",
    "NO_CLIENT_CONVERSION_REQUIRED_PROVEN_OR_CLIENT_FX_OPERATOR_PROVEN",
    "CONVERSION_NUMERIC_STATUS_INSTANTIATED_FROM_FIRST_PARTY_PROOF",
    "FX_OPERATOR_PROVEN_WITHOUT_USD_EQUALS_USDC_ASSUMPTION",
    "ROUNDING_USDC_PRECISION_PROVEN",
    "COVER_USDC_NUMERIC_CALC_FOR_CURRENT_SUI",
    "CURRENT_SUI_INSTRUMENT_BINDING",
    "NO_UPGRADE_FROM_INTERNAL_ENVELOPE_OR_IDENTITY",
)

CURRENT_REQUIRED_INPUT_STATE: Mapping[str, str] = {
    "USD_USDC_OPERATOR_STATUS": "UNPROVEN",
    "USD_USDC_ACCOUNT_SETTLEMENT_PROVEN": "false",
    "NO_CLIENT_CONVERSION_REQUIRED_PROVEN": "false",
    "CONVERSION_NUMERIC_STATUS": ("UNINSTANTIATED_REQUIRES_LATER_PRODUCTIVE_USD_USDC_EVIDENCE"),
    "FX_APPLIED": "false",
    "ROUNDING_APPLIED": "false",
    "USDC_PRECISION_STATUS": "UNPROVEN",
    "COVER_CALC": "ABSENT",
    "COVER_USDC_NUMERIC": "UNINSTANTIATED",
    "CURRENT_SUI_INSTRUMENT_BINDING": "SUI-USD_UM_XPERP-310404",
    "INTERNAL_ENVELOPE_UPGRADE_PERMITTED": "false",
}

BLOCKING_EVIDENCE_GAPS: tuple[str, ...] = (
    "USD_USDC_OPERATOR_STATUS=UNPROVEN",
    "USD_USDC_ACCOUNT_SETTLEMENT_PROVEN=false",
    "NO_CLIENT_CONVERSION_REQUIRED_PROVEN=false",
    "CONVERSION_NUMERIC_STATUS=UNINSTANTIATED_REQUIRES_LATER_PRODUCTIVE_USD_USDC_EVIDENCE",
    "FX_APPLIED=false",
    "ROUNDING_APPLIED=false",
    "USDC_PRECISION_STATUS=UNPROVEN",
    "COVER_CALC_ABSENT",
    "INTERNAL_ENVELOPE_IS_NOT_COVER_USDC",
    "IDXPX_1_IS_NOT_COVER_USDC_OPERATOR",
    "BTC_ERA_GET_PACKS_NOT_CURRENT_SUI_COVER_USDC",
)

CENSUS_ENTRIES: tuple[Mapping[str, str], ...] = (
    {
        "path": "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md#11.13.5.Z2U",
        "claim": "EVERY_USD_DENOMINATED_COMPONENT_MUST_CONVERT_THROUGH_LATER_PRODUCTIVE_VENUE_OR_ACCOUNT_CONVERSION_EVIDENCE_BEFORE_COVER_USDC",
        "evidence_source": "canonical persist Z2U policy form",
        "epistemic_class": "CANONICAL_AUTHORITY",
        "current_applicability": "BINDING_DEFINITION_STILL_IN_FORCE",
        "superseded_stale": "false",
        "contradictions": "NONE",
        "relation_to_current_sui": "DEFINITION_INHERITED_SUI_BOUND_VIA_Z2BX_Z2BY",
    },
    {
        "path": "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md#11.13.5.Z2D",
        "claim": "COVER_USDC_STATUS=UNINSTANTIATED RULE_FX_STATUS=UNPROVEN RULE_ROUNDING_STATUS=UNPROVEN",
        "evidence_source": "canonical persist Z2D",
        "epistemic_class": "CANONICAL_AUTHORITY",
        "current_applicability": "BINDING_NEGATIVE_STATUS",
        "superseded_stale": "false",
        "contradictions": "NONE",
        "relation_to_current_sui": "STATUS_INHERITED_NOT_SUI_NUMERIC_COVER",
    },
    {
        "path": "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md#11.13.5.Z2E",
        "claim": "B08_INTERNAL_ALGEBRA_STATUS=RATIFIED_INTERNAL_CONSERVATIVE_QTY1_NOT_COVER_USDC",
        "evidence_source": "canonical persist Z2E",
        "epistemic_class": "CANONICAL_AUTHORITY",
        "current_applicability": "BINDING_NEGATIVE_NOT_COVER_USDC",
        "superseded_stale": "false",
        "contradictions": "NONE",
        "relation_to_current_sui": "INTERNAL_ALGEBRA_IS_NOT_COVER_USDC",
    },
    {
        "path": "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md#11.13.5.Z2J",
        "claim": "NAMED_REMAINING_COVER_USDC_TERM=FINITE_PHYSICAL_USDC_COVER_AMOUNT_ABSENT COVER_USDC_STATUS=UNINSTANTIATED VENUE_NUMERIC_CONVERSION_OPERATOR_PROVEN=false",
        "evidence_source": "canonical persist Z2J",
        "epistemic_class": "ALREADY_ADJUDICATED_CONCLUSIONS",
        "current_applicability": "CONTROLLING_FOR_CONVERSION_NUMERIC_STATUS",
        "superseded_stale": "false",
        "contradictions": "NONE",
        "relation_to_current_sui": "SETTLEMENT_SEMANTICS_STILL_BLOCK_COVER_USDC",
    },
    {
        "path": "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md#11.13.5.Z2AJ",
        "claim": "IDXPX_USDC_USD_1_IS_COVER_USDC_OPERATOR=false COVER_USDC_STATUS=UNINSTANTIATED USD_USDC_OPERATOR_STATUS=UNPROVEN",
        "evidence_source": "canonical persist Z2AJ of four prior public EEA GETs",
        "epistemic_class": "ALREADY_ADJUDICATED_CONCLUSIONS",
        "current_applicability": "BINDING_NEGATIVE_OPERATOR_CONTRACT",
        "superseded_stale": "GET_WINDOW_HISTORICAL_CONCLUSION_STILL_BINDING",
        "contradictions": "NONE",
        "relation_to_current_sui": "CONVERSION_OPERATOR_STILL_UNPROVEN_FOR_SUI_COVER",
    },
    {
        "path": "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md#11.13.5.Z2BX",
        "claim": "COVER_NEGATIVE_CONTRACT=true COVER_USDC_STATUS=UNINSTANTIATED RISK_ENVELOPE_IDENTITY_IS_NOT_COVER_USDC=true",
        "evidence_source": "canonical persist Z2BX P5 Cover negative contract",
        "epistemic_class": "CANONICAL_AUTHORITY",
        "current_applicability": "CONTROLLING_SUI_BOUND_NEGATIVE_CONTRACT",
        "superseded_stale": "false",
        "contradictions": "NONE",
        "relation_to_current_sui": "BOUND_FOR_SUI-USD_UM_XPERP-310404",
    },
    {
        "path": "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md#11.13.5.Z2BY",
        "claim": "CANONICAL_IDENTITY_REBIND_NE_COVER_USDC=true COVER_USDC_STATUS=UNINSTANTIATED",
        "evidence_source": "canonical persist Z2BY SUI identity rebind",
        "epistemic_class": "CANONICAL_AUTHORITY",
        "current_applicability": "CURRENT_INSTRUMENT_IS_SUI_COVER_STILL_UNINSTANTIATED",
        "superseded_stale": "false",
        "contradictions": "NONE",
        "relation_to_current_sui": "REBIND_IS_NOT_COVER_USDC",
    },
    {
        "path": "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md#11.13.5.Z2CU",
        "claim": "REMAINING_UNRANKED_CLASSES includes COVER_USDC as named unranked SUI reproof class",
        "evidence_source": "canonical persist Z2CU",
        "epistemic_class": "CANONICAL_AUTHORITY",
        "current_applicability": "TRACK_ELIGIBILITY_NOT_COVER_PROOF",
        "superseded_stale": "false",
        "contradictions": "NONE",
        "relation_to_current_sui": "NAMES_CLASS_DOES_NOT_PROVE_IT",
    },
    {
        "path": "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md#11.13.5.L4",
        "claim": "COVER_USDC_MEMBERSHIP=EXCLUDED_FROM_THIS_NAMED_SURFACE COVER_USDC_STATUS=UNINSTANTIATED",
        "evidence_source": "canonical persist L4 max-available surface",
        "epistemic_class": "CANONICAL_AUTHORITY",
        "current_applicability": "PARALLEL_SURFACE_EXCLUSION",
        "superseded_stale": "false",
        "contradictions": "NONE",
        "relation_to_current_sui": "EXCLUDED_NOT_INSTANTIATED",
    },
    {
        "path": (
            "evidence/ops/section_11_13_5_z2g_current_markpx_public_get_v1/"
            "20260818T200745Z/claims.json"
        ),
        "claim": "COVER_USDC_STATUS=UNINSTANTIATED INSTRUMENT_ID=BTC-USD_UM_XPERP-310404 markPx observed not cover",
        "evidence_source": "forensic GET pack Z2G",
        "epistemic_class": "FORENSIC_RAW_ORIGINALS",
        "current_applicability": "NOT_CURRENT_SUI_COVER_USDC",
        "superseded_stale": "true_btc_era_and_explicitly_not_cover",
        "contradictions": "NONE",
        "relation_to_current_sui": "SCOPE_MISMATCH_BTC_NOT_SUI",
    },
    {
        "path": (
            "evidence/ops/section_11_13_5_z2h_current_ticker_bid_ask_public_get_v1/"
            "20260818T203435Z/claims.json"
        ),
        "claim": "COVER_USDC_STATUS=UNINSTANTIATED ticker bid/ask observed not cover",
        "evidence_source": "forensic GET pack Z2H",
        "epistemic_class": "FORENSIC_RAW_ORIGINALS",
        "current_applicability": "NOT_CURRENT_SUI_COVER_USDC",
        "superseded_stale": "true_btc_era_and_explicitly_not_cover",
        "contradictions": "NONE",
        "relation_to_current_sui": "SCOPE_MISMATCH_BTC_NOT_SUI",
    },
    {
        "path": (
            "evidence/ops/section_11_13_5_z2k_current_public_tier_mmr_public_get_v1/"
            "20260819T085545Z/claims.json"
        ),
        "claim": "COVER_USDC_STATUS=UNINSTANTIATED public-tier MMR observed not cover",
        "evidence_source": "forensic GET pack Z2K",
        "epistemic_class": "FORENSIC_RAW_ORIGINALS",
        "current_applicability": "NOT_CURRENT_SUI_COVER_USDC",
        "superseded_stale": "true_btc_era_and_explicitly_not_cover",
        "contradictions": "NONE",
        "relation_to_current_sui": "SCOPE_MISMATCH_BTC_NOT_SUI",
    },
    {
        "path": (
            "evidence/ops/section_11_13_5_z2m_fee_reserve_rates_rebind_get_v1/"
            "20260819T102325Z/SUMMARY.json"
        ),
        "claim": "fee-reserve rates rebind GET; COVER_USDC remains uninstantiated",
        "evidence_source": "forensic GET pack Z2M/Z2N path",
        "epistemic_class": "FORENSIC_RAW_ORIGINALS",
        "current_applicability": "NOT_CURRENT_SUI_COVER_USDC",
        "superseded_stale": "true_btc_era_fee_family_not_cover",
        "contradictions": "NONE",
        "relation_to_current_sui": "SCOPE_MISMATCH_BTC_FAMILY_NOT_SUI_COVER",
    },
    {
        "path": (
            "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/"
            "position_value_fx_rounding_chain_v1.py"
        ),
        "claim": "COVER_USDC_STATUS = UNINSTANTIATED USD_USDC_CONVERSION_APPLIED = False",
        "evidence_source": "current Python contract constant",
        "epistemic_class": "CANONICAL_AUTHORITY",
        "current_applicability": "CURRENT_RUNTIME_CONTRACT_STATUS",
        "superseded_stale": "false",
        "contradictions": "NONE",
        "relation_to_current_sui": "STANDING_UNINSTANTIATED",
    },
    {
        "path": (
            "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/"
            "cover_usdc_current_markpx_productive_evidence_v1.py"
        ),
        "claim": "GET-path helper named for remaining COVER_USDC markPx term; does not instantiate COVER_USDC",
        "evidence_source": "historical GET-path module",
        "epistemic_class": "HISTORICAL_INTERMEDIATE_STATE",
        "current_applicability": "MODULE_EXISTS_NOT_CURRENT_COVER_PROOF",
        "superseded_stale": "btc_era_get_path_not_re_run",
        "contradictions": "NONE",
        "relation_to_current_sui": "NAME_IS_NOT_PROOF",
    },
    {
        "path": (
            "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/"
            "cover_usdc_current_ticker_bid_ask_productive_evidence_v1.py"
        ),
        "claim": "GET-path helper named for remaining COVER_USDC ticker term; does not instantiate COVER_USDC",
        "evidence_source": "historical GET-path module",
        "epistemic_class": "HISTORICAL_INTERMEDIATE_STATE",
        "current_applicability": "MODULE_EXISTS_NOT_CURRENT_COVER_PROOF",
        "superseded_stale": "btc_era_get_path_not_re_run",
        "contradictions": "NONE",
        "relation_to_current_sui": "NAME_IS_NOT_PROOF",
    },
    {
        "path": (
            "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/"
            "cover_usdc_current_public_tier_mmr_productive_evidence_v1.py"
        ),
        "claim": "GET-path helper named for remaining COVER_USDC MMR term; does not instantiate COVER_USDC",
        "evidence_source": "historical GET-path module",
        "epistemic_class": "HISTORICAL_INTERMEDIATE_STATE",
        "current_applicability": "MODULE_EXISTS_NOT_CURRENT_COVER_PROOF",
        "superseded_stale": "btc_era_get_path_not_re_run",
        "contradictions": "NONE",
        "relation_to_current_sui": "NAME_IS_NOT_PROOF",
    },
    {
        "path": (
            "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/"
            "cover_usdc_fee_reserve_rates_rebind_get_path_v1.py"
        ),
        "claim": "COVER_USDC_STATUS = UNINSTANTIATED; fee-path ratification is not cover",
        "evidence_source": "historical GET-path module",
        "epistemic_class": "HISTORICAL_INTERMEDIATE_STATE",
        "current_applicability": "MODULE_EXISTS_NOT_CURRENT_COVER_PROOF",
        "superseded_stale": "btc_era_get_path_not_re_run",
        "contradictions": "NONE",
        "relation_to_current_sui": "NAME_IS_NOT_PROOF",
    },
    {
        "path": "docs/governance/PEAK_TRADE_MAP_OF_TRUTH.md",
        "claim": "navigation pointers to Z2D-Z2AJ COVER_USDC_STATUS=UNINSTANTIATED",
        "evidence_source": "Map of Truth",
        "epistemic_class": "NAVIGATION_INDEX_ONLY",
        "current_applicability": "NAVIGATION_NOT_AUTHORITY",
        "superseded_stale": "false_as_navigation",
        "contradictions": "NONE",
        "relation_to_current_sui": "POINTER_ONLY",
    },
    {
        "path": "docs/system_atlas/reconciliation/inventories/terminology_census.yaml",
        "claim": "term COVER_USDC listed in Atlas terminology census",
        "evidence_source": "Atlas census",
        "epistemic_class": "NAVIGATION_INDEX_ONLY",
        "current_applicability": "NAVIGATION_NOT_AUTHORITY",
        "superseded_stale": "false_as_navigation",
        "contradictions": "NONE",
        "relation_to_current_sui": "TERM_LISTING_NOT_PROOF",
    },
    {
        "path": (
            "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/governance_state_matrix_v1.py"
        ),
        "claim": "historical next pointers requiring later COVER_USDC term evidence before funding",
        "evidence_source": "governance state matrix historical pointers",
        "epistemic_class": "HISTORICAL_INTERMEDIATE_STATE",
        "current_applicability": "POINTER_NOT_CURRENT_COVER_PROOF",
        "superseded_stale": "historical_next_pointers",
        "contradictions": "NONE",
        "relation_to_current_sui": "DOES_NOT_INSTANTIATE_COVER",
    },
    {
        "path": (
            "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/"
            "formula_term_instance_binding_v1.py"
        ),
        "claim": "COVER_USDC_STATUS imported as UNINSTANTIATED; FX_STATUS=UNPROVEN",
        "evidence_source": "current Python contract",
        "epistemic_class": "CANONICAL_AUTHORITY",
        "current_applicability": "CURRENT_RUNTIME_CONTRACT_STATUS",
        "superseded_stale": "false",
        "contradictions": "NONE",
        "relation_to_current_sui": "STANDING_UNINSTANTIATED",
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
    "FX_ROUNDING_FINISHED_RISK_ENVELOPE_NUMERIC_USD_USDC_ACCOUNT_SETTLEMENT_"
    "STILL_UNRANKED_OR_ALTERNATIVE_P3_ELIGIBLE_TRACK_NO_COVER_USDC_UPGRADE_"
    "WITHOUT_NEW_FIRST_PARTY_PROOF_NO_GET_UNLESS_SEPARATELY_NAMED_NO_CLASS_D_"
    "NO_Z2AP_NO_FLATTEN_NO_MERGE"
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


class LiveCanaryZ2arCoverUsdcOfflineReproofError(RuntimeError):
    """Fail-closed COVER_USDC offline reproof violation."""


def _fail(code: str) -> None:
    raise LiveCanaryZ2arCoverUsdcOfflineReproofError(code)


def reject_historical_or_navigation_upgrade_v1(
    *,
    upgrade_historical_to_proven: bool = False,
    upgrade_navigation_to_proven: bool = False,
) -> None:
    """Historical existence and navigation indexes are not COVER_USDC proof."""
    if upgrade_historical_to_proven:
        _fail("FORBIDDEN_UPGRADE_HISTORICAL_TO_PROVEN")
    if upgrade_navigation_to_proven:
        _fail("FORBIDDEN_UPGRADE_NAVIGATION_TO_PROVEN")


def reject_class_collapse_v1(
    *,
    mix_with_usd_usdc: bool = False,
    mix_with_fx: bool = False,
    mix_with_risk_envelope_numeric: bool = False,
    mix_with_rounding: bool = False,
    named_class: str = Z2AR_CLASS,
) -> None:
    """COVER_USDC must not be collapsed onto sibling Z2AR classes."""
    if named_class != Z2AR_CLASS:
        _fail("FORBIDDEN_Z2AR_CLASS_MISMATCH")
    if mix_with_usd_usdc:
        _fail("FORBIDDEN_COLLAPSE_COVER_USDC_WITH_USD_USDC")
    if mix_with_fx:
        _fail("FORBIDDEN_COLLAPSE_COVER_USDC_WITH_FX")
    if mix_with_risk_envelope_numeric:
        _fail("FORBIDDEN_COLLAPSE_COVER_USDC_WITH_RISK_ENVELOPE_NUMERIC")
    if mix_with_rounding:
        _fail("FORBIDDEN_COLLAPSE_COVER_USDC_WITH_ROUNDING")


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


def adjudicate_cover_usdc_offline_reproof_v1(
    *,
    claimed_status: str | None = None,
    claimed_reproof_proven: bool | None = None,
    mix_with_usd_usdc: bool = False,
    mix_with_fx: bool = False,
    mix_with_risk_envelope_numeric: bool = False,
    mix_with_rounding: bool = False,
    implied_venue_observation: bool = False,
    execution_ready_claim: bool = False,
    get_performed_claim: bool = False,
    post_performed_claim: bool = False,
    flatten_performed_claim: bool = False,
    class_d_consumed_claim: bool = False,
    z2ap_consumed_claim: bool = False,
    upgrade_historical_to_proven: bool = False,
    upgrade_navigation_to_proven: bool = False,
    named_class: str = Z2AR_CLASS,
) -> dict[str, Any]:
    """Return the fail-closed COVER_USDC offline reproof. Caller facts only."""
    if BOUND_COVER_USDC_STATUS != "UNINSTANTIATED":
        _fail("DRIFT_BOUND_COVER_USDC_STATUS_NOT_UNINSTANTIATED")
    if BOUND_USD_USDC_CONVERSION_APPLIED is True:
        _fail("DRIFT_USD_USDC_CONVERSION_APPLIED")
    if BOUND_USD_USDC_PARITY_ASSUMED is True:
        _fail("DRIFT_USD_USDC_PARITY_ASSUMED")
    if BOUND_ROUNDING_APPLIED is True:
        _fail("DRIFT_ROUNDING_APPLIED")

    reject_class_collapse_v1(
        mix_with_usd_usdc=mix_with_usd_usdc,
        mix_with_fx=mix_with_fx,
        mix_with_risk_envelope_numeric=mix_with_risk_envelope_numeric,
        mix_with_rounding=mix_with_rounding,
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
        "CURRENT_COVER_USDC_STATUS": CURRENT_COVER_USDC_STATUS,
        "REPROOF_PROVEN": REPROOF_PROVEN,
        "COVER_USDC_STATUS": COVER_USDC_STATUS,
        "COVER_USDC_INSTANTIATED": COVER_USDC_INSTANTIATED,
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
        "COVER_NEGATIVE_CONTRACT_REMAINS_IN_FORCE": (COVER_NEGATIVE_CONTRACT_REMAINS_IN_FORCE),
        "CONTRADICTION_COUNT": CONTRADICTION_COUNT,
    }
