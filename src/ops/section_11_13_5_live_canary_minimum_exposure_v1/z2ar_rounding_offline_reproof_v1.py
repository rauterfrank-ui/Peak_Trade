"""§11.13.5.Z2CX ROUNDING offline reproof.

CONTRACT / GOVERNANCE only. Adjudicates the already-bound ROUNDING class
against repo-internal canonical persist, forensic originals, and
navigation indexes. Does not observe a venue. Does not apply rounding.
Does not invent USDC precision. Does not treat tickSz as USDC precision.
Does not adjudicate COVER_USDC or reopen FX. Does not adjudicate
FINISHED_RISK_ENVELOPE_NUMERIC or USD_USDC_ACCOUNT_SETTLEMENT as this
class. Does not authorize Live, Testnet, orders, funding, GET, POST,
flatten, Class D, or Z2AP.
"""

from __future__ import annotations

from typing import Any, Mapping

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.exact_formula_body_v1 import (
    ROUNDING_STATUS as BOUND_EXACT_ROUNDING_STATUS,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.formula_term_instance_binding_v1 import (
    ROUNDING_STATUS as BOUND_TERM_ROUNDING_STATUS,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.position_value_fx_rounding_chain_v1 import (
    ROUNDING_APPLIED as BOUND_ROUNDING_APPLIED,
    RULE_ROUNDING as BOUND_RULE_ROUNDING,
    RULE_ROUNDING_STATUS as BOUND_RULE_ROUNDING_STATUS,
    TICK_SZ_IS_NOT_USDC_PRECISION as BOUND_TICK_SZ_IS_NOT_USDC_PRECISION,
    USDC_PRECISION_STATUS as BOUND_USDC_PRECISION_STATUS,
)

OWNER_GO = "PEAK_TRADE_OWNER_GO_Z2AR_REMAINING_UNRANKED_OFFLINE_REPROOF_BUNDLE_V1"
THIS_SLICE = "11.13.5.Z2CX"
PREDECESSOR_SLICE = "11.13.5.Z2CW"
LAST_CANONICALLY_CLOSED_11_13_5_SLICE = "SECTION_11_13_5_Z2CT"
THIS_PERSIST_DOES_NOT_SUPERSEDE_Z2CT_AS_LAST_CANONICALLY_CLOSED_11_13_5_SLICE = True
THIS_PERSIST_DOES_NOT_REWRITE_Z2CW = True
THIS_NAMED_CLASS_PERSIST_ID = "SECTION_11_13_5_Z2CX"

Z2AR_CLASS = "ROUNDING"
EXACT_Z2AR_CLASS = "ROUNDING"
AUTHORIZED_SCOPE = "P3_Z2AR_REMAINING_UNRANKED_SUI_REPROOF"
ADJUDICATION = "NOT_REPROVEN_MISSING_EVIDENCE"
CURRENT_ROUNDING_STATUS = "NOT_REPROVEN_MISSING_EVIDENCE"
REPROOF_PROVEN = False
RULE_ROUNDING = "RND-CEIL-VENUE-CCY-PRECISION-AFTER-COMPOSITION"
RULE_ROUNDING_STATUS = "UNPROVEN"
RULE_ROUNDING_IS_RATIFIED_FORM_NOT_PROVEN_INSTANCE = True
ROUNDING_STATUS = "UNPROVEN"
ROUNDING_APPLIED = False
USDC_PRECISION_STATUS = "UNPROVEN"
TICK_SZ_IS_NOT_USDC_PRECISION = True
NO_FIXED_USDC_ROUNDING_STEP_INVENTED = True
ROUNDING_ALLOWED_ONLY_AFTER_FULL_FORMULA_COMPOSITION = True

CURRENT_CANONICAL_INSTRUMENT = "SUI-USD_UM_XPERP-310404"
CURRENT_SUI_BINDING = "SUI-USD_UM_XPERP-310404"

SUI_REPROOF_CLASSES_RANKED = False
NO_RANKING_OF_REMAINDER = True
REMAINING_UNRANKED_AFTER_THIS_CLASS = (
    "FINISHED_RISK_ENVELOPE_NUMERIC",
    "USD_USDC_ACCOUNT_SETTLEMENT",
)
FORBIDDEN_COLLAPSE_CLASSES = (
    "COVER_USDC",
    "FX",
    "FINISHED_RISK_ENVELOPE_NUMERIC",
    "USD_USDC_ACCOUNT_SETTLEMENT",
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
FORBIDDEN_UPGRADE_FORM_TO_INSTANCE = True
FORBIDDEN_TICKSZ_AS_USDC_PRECISION = True
BTC_ERA_GET_PACKS_ARE_NOT_CURRENT_SUI_ROUNDING = True

REQUIRED_INPUTS_FOR_REPROVEN: tuple[str, ...] = (
    "CANONICAL_ROUNDING_DEFINITION_IDENTIFIED",
    "FULL_FORMULA_COMPOSITION_COMPLETE_IN_ACCOUNT_SETTLEMENT_UNIT",
    "USDC_PRECISION_PRODUCTIVELY_PROVEN",
    "VENUE_CCY_PRECISION_OPERATOR_INSTANTIATED",
    "ROUNDING_APPLIED_ONLY_AFTER_COMPOSITION",
    "TICK_SZ_NOT_USED_AS_USDC_PRECISION",
    "CURRENT_SUI_BINDING",
    "NO_CONTRADICTORY_CANONICAL_AUTHORITY",
)

CURRENT_REQUIRED_INPUT_STATE: Mapping[str, str] = {
    "CANONICAL_ROUNDING_DEFINITION": (
        "RULE_ROUNDING=RND-CEIL-VENUE-CCY-PRECISION-AFTER-COMPOSITION_RATIFIED_FORM_NOT_INSTANCE"
    ),
    "FULL_FORMULA_COMPOSITION": "ABSENT_COVER_USDC_UNINSTANTIATED_SUM_INTERNAL_UNINSTANTIATED",
    "USDC_PRECISION": "UNPROVEN",
    "VENUE_CCY_PRECISION_OPERATOR": "UNINSTANTIATED",
    "ROUNDING_APPLIED": "false",
    "TICK_SZ_AS_USDC_PRECISION": "FORBIDDEN_NOT_USED",
    "CURRENT_SUI_INSTRUMENT_BINDING": "SUI-USD_UM_XPERP-310404",
    "CONTRADICTORY_CANONICAL_AUTHORITY": "NONE",
}

BLOCKING_EVIDENCE_GAPS: tuple[str, ...] = (
    "RULE_ROUNDING_IS_RATIFIED_FORM_NOT_PROVEN_INSTANCE",
    "RULE_ROUNDING_STATUS=UNPROVEN",
    "ROUNDING_APPLIED=false",
    "USDC_PRECISION_STATUS=UNPROVEN",
    "TICK_SZ_IS_NOT_USDC_PRECISION=true",
    "FULL_FORMULA_COMPOSITION_ABSENT",
    "NO_FIXED_USDC_ROUNDING_STEP_INVENTED",
    "BTC_ERA_GET_PACKS_NOT_CURRENT_SUI_ROUNDING",
)

CENSUS_ENTRIES: tuple[Mapping[str, str], ...] = (
    {
        "path": "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md#11.13.5.U",
        "claim": (
            "RULE_ROUNDING=RND-CEIL-VENUE-CCY-PRECISION-AFTER-COMPOSITION "
            "ROUNDING_ALLOWED_ONLY_AFTER_FULL_FORMULA_COMPOSITION=true "
            "USDC_PRECISION_MUST_BE_LATER_PRODUCTIVELY_PROVEN=true "
            "TICK_SZ_IS_NOT_USDC_PRECISION=true "
            "NO_FIXED_USDC_ROUNDING_STEP_INVENTED=true "
            "ROUNDING_NOT_APPLIED_IN_THIS_STEP=true"
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
        "claim": "RULE_ROUNDING_STATUS=UNPROVEN ROUNDING_APPLIED=false USDC_PRECISION_STATUS=UNPROVEN",
        "evidence_source": "canonical persist Z2D",
        "epistemic_class": "CANONICAL_AUTHORITY",
        "current_applicability": "BINDING_NEGATIVE_STATUS",
        "superseded_stale": "false",
        "contradictions": "NONE",
        "relation_to_current_sui": "STATUS_INHERITED_NOT_SUI_NUMERIC_ROUNDING",
    },
    {
        "path": "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md#11.13.5.Z2F",
        "claim": "ROUNDING_STATUS=UNPROVEN RULE_ROUNDING_STATUS=UNPROVEN TICK_SZ_IS_NOT_USDC_PRECISION=true",
        "evidence_source": "canonical persist Z2F term-instance adjudication",
        "epistemic_class": "CANONICAL_AUTHORITY",
        "current_applicability": "BINDING_NEGATIVE_STATUS",
        "superseded_stale": "false",
        "contradictions": "NONE",
        "relation_to_current_sui": "STATUS_INHERITED_NOT_SUI_NUMERIC_ROUNDING",
    },
    {
        "path": "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md#11.13.5.Z2BW",
        "claim": "NOT ROUNDING; composition numeric is not a rounding operator",
        "evidence_source": "canonical persist Z2BW P4 composition numeric",
        "epistemic_class": "CANONICAL_AUTHORITY",
        "current_applicability": "BINDING_NEGATIVE_NOT_ROUNDING",
        "superseded_stale": "false",
        "contradictions": "NONE",
        "relation_to_current_sui": "INTERNAL_COMPOSITION_IS_NOT_ROUNDING",
    },
    {
        "path": "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md#11.13.5.Z2BX",
        "claim": "ROUNDING_APPLIED=false NO_ROUNDING=true FAIL_CLOSED_IF_FX_OR_ROUNDING_APPLIED=true",
        "evidence_source": "canonical persist Z2BX P5 identity plus Cover negative contract",
        "epistemic_class": "ALREADY_ADJUDICATED_CONCLUSIONS",
        "current_applicability": "BINDING_NEGATIVE_NOT_ROUNDING",
        "superseded_stale": "false",
        "contradictions": "NONE",
        "relation_to_current_sui": "IDENTITY_IS_NOT_ROUNDING_FOR_SUI-USD_UM_XPERP-310404",
    },
    {
        "path": "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md#11.13.5.Z2CU",
        "claim": "REMAINING_UNRANKED_CLASSES includes ROUNDING as named unranked SUI reproof class",
        "evidence_source": "canonical persist Z2CU",
        "epistemic_class": "CANONICAL_AUTHORITY",
        "current_applicability": "TRACK_ELIGIBILITY_NOT_ROUNDING_PROOF",
        "superseded_stale": "false",
        "contradictions": "NONE",
        "relation_to_current_sui": "NAMES_CLASS_DOES_NOT_PROVE_IT",
    },
    {
        "path": "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md#11.13.5.Z2CV",
        "claim": "ROUNDING_ADJUDICATED_THIS_PERSIST=false FORBIDDEN_COLLAPSE_COVER_USDC_WITH_ROUNDING",
        "evidence_source": "canonical persist Z2CV COVER_USDC offline reproof",
        "epistemic_class": "CANONICAL_AUTHORITY",
        "current_applicability": "SIBLING_CLASS_NOT_ROUNDING_PROOF",
        "superseded_stale": "false",
        "contradictions": "NONE",
        "relation_to_current_sui": "COVER_USDC_FAIL_CLOSED_DOES_NOT_PROVE_ROUNDING",
    },
    {
        "path": "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md#11.13.5.Z2CW",
        "claim": (
            "ROUNDING_ADJUDICATED_THIS_PERSIST=false "
            "REMAINING_UNRANKED_AFTER_THIS_CLASS includes ROUNDING "
            "FORBIDDEN_COLLAPSE_FX_WITH_ROUNDING=true"
        ),
        "evidence_source": "canonical persist Z2CW FX offline reproof",
        "epistemic_class": "CANONICAL_AUTHORITY",
        "current_applicability": "SIBLING_CLASS_NOT_ROUNDING_PROOF",
        "superseded_stale": "false",
        "contradictions": "NONE",
        "relation_to_current_sui": "FX_FAIL_CLOSED_DOES_NOT_PROVE_ROUNDING",
    },
    {
        "path": (
            "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/"
            "position_value_fx_rounding_chain_v1.py"
        ),
        "claim": (
            "RULE_ROUNDING = RND-CEIL-VENUE-CCY-PRECISION-AFTER-COMPOSITION "
            "RULE_ROUNDING_STATUS = UNPROVEN ROUNDING_APPLIED = False "
            "USDC_PRECISION_STATUS = UNPROVEN TICK_SZ_IS_NOT_USDC_PRECISION = True"
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
        "claim": "ROUNDING_STATUS = UNPROVEN ROUNDING_APPLIED = False",
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
        "claim": "ROUNDING_STATUS = UNINSTANTIATED_REQUIRES_PRODUCTIVE_USDC_PRECISION_EVIDENCE",
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
        "claim": "ROUNDING_STATUS=UNPROVEN INSTRUMENT_ID=BTC-USD_UM_XPERP-310404 markPx observed not rounding",
        "evidence_source": "forensic GET pack Z2G",
        "epistemic_class": "FORENSIC_RAW_ORIGINALS",
        "current_applicability": "NOT_CURRENT_SUI_ROUNDING_OPERATOR",
        "superseded_stale": "true_btc_era_and_explicitly_unproven_rounding",
        "contradictions": "NONE",
        "relation_to_current_sui": "SCOPE_MISMATCH_BTC_NOT_SUI",
    },
    {
        "path": (
            "evidence/ops/section_11_13_5_z2h_current_ticker_bid_ask_public_get_v1/"
            "20260818T203435Z/claims.json"
        ),
        "claim": "ROUNDING_STATUS=UNPROVEN ticker bid/ask observed not rounding",
        "evidence_source": "forensic GET pack Z2H",
        "epistemic_class": "FORENSIC_RAW_ORIGINALS",
        "current_applicability": "NOT_CURRENT_SUI_ROUNDING_OPERATOR",
        "superseded_stale": "true_btc_era_and_explicitly_unproven_rounding",
        "contradictions": "NONE",
        "relation_to_current_sui": "SCOPE_MISMATCH_BTC_NOT_SUI",
    },
    {
        "path": (
            "evidence/ops/section_11_13_5_z2k_current_public_tier_mmr_public_get_v1/"
            "20260819T085545Z/claims.json"
        ),
        "claim": "ROUNDING_STATUS=UNPROVEN public-tier MMR observed not rounding",
        "evidence_source": "forensic GET pack Z2K",
        "epistemic_class": "FORENSIC_RAW_ORIGINALS",
        "current_applicability": "NOT_CURRENT_SUI_ROUNDING_OPERATOR",
        "superseded_stale": "true_btc_era_and_explicitly_unproven_rounding",
        "contradictions": "NONE",
        "relation_to_current_sui": "SCOPE_MISMATCH_BTC_NOT_SUI",
    },
    {
        "path": (
            "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/"
            "cover_usdc_current_ticker_bid_ask_productive_evidence_v1.py"
        ),
        "claim": "GET-path helper may carry ROUNDING_STATUS; tickSz spread floor is not USDC precision",
        "evidence_source": "historical GET-path module",
        "epistemic_class": "HISTORICAL_INTERMEDIATE_STATE",
        "current_applicability": "MODULE_EXISTS_NOT_CURRENT_ROUNDING_PROOF",
        "superseded_stale": "btc_era_get_path_not_re_run",
        "contradictions": "NONE",
        "relation_to_current_sui": "NAME_AND_TICKSZ_ARE_NOT_USDC_PRECISION",
    },
    {
        "path": (
            "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/governance_state_matrix_v1.py"
        ),
        "claim": "historical next pointers requiring later FX/rounding evidence",
        "evidence_source": "governance state matrix historical pointers",
        "epistemic_class": "HISTORICAL_INTERMEDIATE_STATE",
        "current_applicability": "POINTER_NOT_CURRENT_ROUNDING_PROOF",
        "superseded_stale": "historical_next_pointers",
        "contradictions": "NONE",
        "relation_to_current_sui": "DOES_NOT_PROVE_ROUNDING",
    },
    {
        "path": "docs/governance/PEAK_TRADE_MAP_OF_TRUTH.md",
        "claim": "navigation pointers RULE_ROUNDING_STATUS=UNPROVEN ROUNDING_STATUS=UNPROVEN",
        "evidence_source": "Map of Truth",
        "epistemic_class": "NAVIGATION_INDEX_ONLY",
        "current_applicability": "NAVIGATION_NOT_AUTHORITY",
        "superseded_stale": "false_as_navigation",
        "contradictions": "NONE",
        "relation_to_current_sui": "POINTER_ONLY",
    },
    {
        "path": "docs/system_atlas/entities/catalog.yaml",
        "claim": "Atlas PHASE:z2cw notes ROUNDING not adjudicated; Atlas is not trading authority",
        "evidence_source": "Atlas catalog",
        "epistemic_class": "NAVIGATION_INDEX_ONLY",
        "current_applicability": "NAVIGATION_NOT_AUTHORITY",
        "superseded_stale": "false_as_navigation",
        "contradictions": "NONE",
        "relation_to_current_sui": "POINTER_ONLY",
    },
    {
        "path": "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md#11.13.5.Z2P",
        "claim": (
            "tickSz used as TOB spread floor for internal slippage algebra; "
            "ROUNDING_STATUS=UNPROVEN; tickSz is not USDC precision"
        ),
        "evidence_source": "canonical persist Z2P same-pack ticker",
        "epistemic_class": "CANONICAL_AUTHORITY",
        "current_applicability": "TICKSZ_ROLE_IS_NOT_USDC_PRECISION",
        "superseded_stale": "false_as_negative_role",
        "contradictions": "NONE",
        "relation_to_current_sui": "TICKSZ_IS_NOT_SUI_USDC_PRECISION",
    },
    {
        "path": "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md#11.13.5.Z2AR",
        "claim": "SUI_REPROOF_REQUIREMENTS listing is not rounding proof; no USDC precision invented",
        "evidence_source": "canonical persist Z2AR SUI reproof boundary",
        "epistemic_class": "CANONICAL_AUTHORITY",
        "current_applicability": "RELATED_SET_MEMBERSHIP_NOT_ROUNDING_PROOF",
        "superseded_stale": "false",
        "contradictions": "NONE",
        "relation_to_current_sui": "SET_MEMBERSHIP_IS_NOT_INSTANCE",
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
    "SEPARATE_OWNER_MERGE_GO_REQUIRED_NO_ROUNDING_UPGRADE_WITHOUT_NEW_"
    "FIRST_PARTY_USDC_PRECISION_AND_FULL_COMPOSITION_NO_TICKSZ_AS_USDC_"
    "PRECISION_NO_GET_UNLESS_SEPARATELY_NAMED_NO_CLASS_D_NO_Z2AP_NO_FLATTEN"
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


class LiveCanaryZ2arRoundingOfflineReproofError(RuntimeError):
    """Fail-closed ROUNDING offline reproof violation."""


def _fail(code: str) -> None:
    raise LiveCanaryZ2arRoundingOfflineReproofError(code)


def reject_historical_or_navigation_upgrade_v1(
    *,
    upgrade_historical_to_proven: bool = False,
    upgrade_navigation_to_proven: bool = False,
) -> None:
    """Historical existence and navigation indexes are not ROUNDING proof."""
    if upgrade_historical_to_proven:
        _fail("FORBIDDEN_UPGRADE_HISTORICAL_TO_PROVEN")
    if upgrade_navigation_to_proven:
        _fail("FORBIDDEN_UPGRADE_NAVIGATION_TO_PROVEN")


def reject_ticksz_as_usdc_precision_v1(
    *,
    treat_tick_sz_as_usdc_precision: bool = False,
) -> None:
    """tickSz is not USDC precision."""
    if treat_tick_sz_as_usdc_precision:
        _fail("FORBIDDEN_TICKSZ_AS_USDC_PRECISION")


def reject_form_to_instance_upgrade_v1(
    *,
    treat_rule_form_as_proven_instance: bool = False,
) -> None:
    """The ratified rounding form is not a proven instance."""
    if treat_rule_form_as_proven_instance:
        _fail("FORBIDDEN_UPGRADE_FORM_TO_INSTANCE")


def reject_class_collapse_v1(
    *,
    mix_with_fx: bool = False,
    mix_with_account_settlement: bool = False,
    mix_with_cover_usdc: bool = False,
    mix_with_risk_envelope_numeric: bool = False,
    named_class: str = Z2AR_CLASS,
) -> None:
    """ROUNDING must not be collapsed onto sibling Z2AR classes."""
    if named_class != Z2AR_CLASS:
        _fail("FORBIDDEN_Z2AR_CLASS_MISMATCH")
    if mix_with_fx:
        _fail("FORBIDDEN_COLLAPSE_ROUNDING_WITH_FX")
    if mix_with_account_settlement:
        _fail("FORBIDDEN_COLLAPSE_ROUNDING_WITH_ACCOUNT_SETTLEMENT")
    if mix_with_cover_usdc:
        _fail("FORBIDDEN_COLLAPSE_ROUNDING_WITH_COVER_USDC")
    if mix_with_risk_envelope_numeric:
        _fail("FORBIDDEN_COLLAPSE_ROUNDING_WITH_RISK_ENVELOPE_NUMERIC")


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


def adjudicate_rounding_offline_reproof_v1(
    *,
    claimed_status: str | None = None,
    claimed_reproof_proven: bool | None = None,
    mix_with_fx: bool = False,
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
    treat_tick_sz_as_usdc_precision: bool = False,
    treat_rule_form_as_proven_instance: bool = False,
    named_class: str = Z2AR_CLASS,
    reopen_fx: bool = False,
    adjudicate_cover_usdc: bool = False,
) -> dict[str, Any]:
    """Return the fail-closed ROUNDING offline reproof. Caller facts only."""
    if BOUND_RULE_ROUNDING != "RND-CEIL-VENUE-CCY-PRECISION-AFTER-COMPOSITION":
        _fail("DRIFT_BOUND_RULE_ROUNDING")
    if BOUND_RULE_ROUNDING_STATUS != "UNPROVEN":
        _fail("DRIFT_BOUND_RULE_ROUNDING_STATUS_NOT_UNPROVEN")
    if BOUND_TERM_ROUNDING_STATUS != "UNPROVEN":
        _fail("DRIFT_BOUND_TERM_ROUNDING_STATUS_NOT_UNPROVEN")
    if BOUND_EXACT_ROUNDING_STATUS != "UNINSTANTIATED_REQUIRES_PRODUCTIVE_USDC_PRECISION_EVIDENCE":
        _fail("DRIFT_BOUND_EXACT_ROUNDING_STATUS")
    if BOUND_ROUNDING_APPLIED is True:
        _fail("DRIFT_ROUNDING_APPLIED")
    if BOUND_USDC_PRECISION_STATUS != "UNPROVEN":
        _fail("DRIFT_USDC_PRECISION_STATUS")
    if BOUND_TICK_SZ_IS_NOT_USDC_PRECISION is not True:
        _fail("DRIFT_TICK_SZ_IS_NOT_USDC_PRECISION")
    if reopen_fx:
        _fail("FORBIDDEN_FX_REOPEN")
    if adjudicate_cover_usdc:
        _fail("FORBIDDEN_COVER_USDC_ADJUDICATION")

    reject_class_collapse_v1(
        mix_with_fx=mix_with_fx,
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
    reject_ticksz_as_usdc_precision_v1(
        treat_tick_sz_as_usdc_precision=treat_tick_sz_as_usdc_precision,
    )
    reject_form_to_instance_upgrade_v1(
        treat_rule_form_as_proven_instance=treat_rule_form_as_proven_instance,
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
        "CURRENT_ROUNDING_STATUS": CURRENT_ROUNDING_STATUS,
        "REPROOF_PROVEN": REPROOF_PROVEN,
        "RULE_ROUNDING": RULE_ROUNDING,
        "RULE_ROUNDING_STATUS": RULE_ROUNDING_STATUS,
        "ROUNDING_STATUS": ROUNDING_STATUS,
        "ROUNDING_APPLIED": ROUNDING_APPLIED,
        "USDC_PRECISION_STATUS": USDC_PRECISION_STATUS,
        "TICK_SZ_IS_NOT_USDC_PRECISION": TICK_SZ_IS_NOT_USDC_PRECISION,
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
