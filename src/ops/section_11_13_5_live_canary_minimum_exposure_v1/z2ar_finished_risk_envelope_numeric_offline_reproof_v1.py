"""§11.13.5.Z2CX FINISHED_RISK_ENVELOPE_NUMERIC offline reproof.

CONTRACT / GOVERNANCE only. Adjudicates the already-bound finished
risk-envelope numeric class against repo-internal canonical persist,
forensic originals, and navigation indexes. Does not observe a venue.
Does not promote composition numeric or identity to finished proof.
Does not adjudicate COVER_USDC or reopen FX. Does not adjudicate
ROUNDING or USD_USDC_ACCOUNT_SETTLEMENT as this class. Does not
authorize Live, Testnet, orders, funding, GET, POST, flatten, Class D,
or Z2AP.
"""

from __future__ import annotations

from typing import Any, Mapping

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.exact_formula_body_v1 import (
    SUM_INTERNAL_NUMERIC_STATUS as BOUND_SUM_INTERNAL_NUMERIC_STATUS,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.position_value_fx_rounding_chain_v1 import (
    COVER_USDC_STATUS as BOUND_COVER_USDC_STATUS,
    ROUNDING_APPLIED as BOUND_ROUNDING_APPLIED,
    USD_USDC_CONVERSION_APPLIED as BOUND_USD_USDC_CONVERSION_APPLIED,
)

OWNER_GO = "PEAK_TRADE_OWNER_GO_Z2AR_REMAINING_UNRANKED_OFFLINE_REPROOF_BUNDLE_V1"
THIS_SLICE = "11.13.5.Z2CX"
PREDECESSOR_SLICE = "11.13.5.Z2CW"
LAST_CANONICALLY_CLOSED_11_13_5_SLICE = "SECTION_11_13_5_Z2CT"
THIS_PERSIST_DOES_NOT_SUPERSEDE_Z2CT_AS_LAST_CANONICALLY_CLOSED_11_13_5_SLICE = True
THIS_PERSIST_DOES_NOT_REWRITE_Z2CW = True
THIS_NAMED_CLASS_PERSIST_ID = "SECTION_11_13_5_Z2CX"

Z2AR_CLASS = "FINISHED_RISK_ENVELOPE_NUMERIC"
EXACT_Z2AR_CLASS = "FINISHED_RISK_ENVELOPE_NUMERIC"
AUTHORIZED_SCOPE = "P3_Z2AR_REMAINING_UNRANKED_SUI_REPROOF"
ADJUDICATION = "NOT_REPROVEN_MISSING_EVIDENCE"
CURRENT_FINISHED_RISK_ENVELOPE_NUMERIC_STATUS = "NOT_REPROVEN_MISSING_EVIDENCE"
REPROOF_PROVEN = False
RISK_ENVELOPE_NUMERIC_STATUS = "UNINSTANTIATED"
RISK_ENVELOPE_NUMERIC = "NONE"
RISK_ENVELOPE_NUMERIC_PROVEN = False
SUI_RISK_ENVELOPE_NUMERIC_PROVEN = False
NAMED_CLASS_RISK_ENVELOPE_NUMERICS_CLOSED = False
NO_PROMOTION_IDENTITY_TO_FINISHED_RISK_ENVELOPE_NUMERIC = True
NO_PROMOTION_COMPOSITION_NUMERIC_TO_RISK_ENVELOPE_NUMERIC_PROVEN = True

CURRENT_CANONICAL_INSTRUMENT = "SUI-USD_UM_XPERP-310404"
CURRENT_SUI_BINDING = "SUI-USD_UM_XPERP-310404"

SUI_REPROOF_CLASSES_RANKED = False
NO_RANKING_OF_REMAINDER = True
REMAINING_UNRANKED_AFTER_THIS_CLASS = ("USD_USDC_ACCOUNT_SETTLEMENT",)
FORBIDDEN_COLLAPSE_CLASSES = (
    "COVER_USDC",
    "FX",
    "ROUNDING",
    "USD_USDC_ACCOUNT_SETTLEMENT",
    "COMPOSITION_NUMERIC",
    "RISK_ENVELOPE_IDENTITY",
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
FORBIDDEN_UPGRADE_IDENTITY_TO_FINISHED = True
FORBIDDEN_UPGRADE_COMPOSITION_TO_FINISHED = True
BTC_ERA_GET_PACKS_ARE_NOT_CURRENT_SUI_FINISHED_ENVELOPE = True

REQUIRED_INPUTS_FOR_REPROVEN: tuple[str, ...] = (
    "FINISHED_NUMERIC_DISTINCT_FROM_IDENTITY_AND_COMPOSITION",
    "RISK_ENVELOPE_NUMERIC_INSTANTIATED",
    "NAMED_CLASS_RISK_ENVELOPE_NUMERICS_CLOSED",
    "NO_PROMOTION_FROM_INTERNAL_IDENTITY",
    "NO_PROMOTION_FROM_COMPOSITION_NUMERIC",
    "CURRENT_SUI_BINDING",
    "NO_CONTRADICTORY_CANONICAL_AUTHORITY",
)

CURRENT_REQUIRED_INPUT_STATE: Mapping[str, str] = {
    "FINISHED_NUMERIC_DISTINCT_FROM_IDENTITY": "IDENTITY_RATIFIED_FINISHED_UNINSTANTIATED",
    "RISK_ENVELOPE_NUMERIC": "NONE",
    "RISK_ENVELOPE_NUMERIC_STATUS": "UNINSTANTIATED",
    "NAMED_CLASS_CLOSED": "false",
    "IDENTITY_PROMOTION_PERMITTED": "false",
    "COMPOSITION_PROMOTION_PERMITTED": "false",
    "CURRENT_SUI_INSTRUMENT_BINDING": "SUI-USD_UM_XPERP-310404",
    "CONTRADICTORY_CANONICAL_AUTHORITY": "NONE",
}

BLOCKING_EVIDENCE_GAPS: tuple[str, ...] = (
    "RISK_ENVELOPE_NUMERIC_STATUS=UNINSTANTIATED",
    "RISK_ENVELOPE_NUMERIC=NONE",
    "RISK_ENVELOPE_NUMERIC_PROVEN=false",
    "SUI_RISK_ENVELOPE_NUMERIC_PROVEN=false",
    "NAMED_CLASS_RISK_ENVELOPE_NUMERICS_CLOSED=false",
    "NO_PROMOTION_IDENTITY_TO_FINISHED_RISK_ENVELOPE_NUMERIC",
    "NO_PROMOTION_COMPOSITION_NUMERIC_TO_RISK_ENVELOPE_NUMERIC_PROVEN",
    "SUM_INTERNAL_NUMERIC_STATUS=UNINSTANTIATED",
    "BTC_ERA_GET_PACKS_NOT_CURRENT_SUI_FINISHED_ENVELOPE",
)

CENSUS_ENTRIES: tuple[Mapping[str, str], ...] = (
    {
        "path": "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md#11.13.5.Z2AR",
        "claim": (
            "SUI_RISK_ENVELOPE_NUMERIC_PROVEN=false "
            "FORBIDDEN_UPGRADE_SUI_MARKPX_OR_TICKER_TO_FINISHED_RISK_ENVELOPE=true "
            "MARKPX_TICKER_NE_RISK_ENVELOPE=true"
        ),
        "evidence_source": "canonical persist Z2AR SUI reproof boundary",
        "epistemic_class": "CANONICAL_AUTHORITY",
        "current_applicability": "BINDING_NEGATIVE_STATUS",
        "superseded_stale": "false",
        "contradictions": "NONE",
        "relation_to_current_sui": "SET_MEMBER_risk_envelope_numerics_NOT_CLOSED",
    },
    {
        "path": "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md#11.13.5.Z2BW",
        "claim": "P4 composition numeric is not finished RISK_ENVELOPE_NUMERIC",
        "evidence_source": "canonical persist Z2BW P4 composition numeric",
        "epistemic_class": "CANONICAL_AUTHORITY",
        "current_applicability": "BINDING_NEGATIVE_NOT_FINISHED_ENVELOPE",
        "superseded_stale": "false",
        "contradictions": "NONE",
        "relation_to_current_sui": "COMPOSITION_NUMERIC_IS_NOT_FINISHED_ENVELOPE",
    },
    {
        "path": "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md#11.13.5.Z2BX",
        "claim": (
            "RISK_ENVELOPE_FORM_STATUS=RATIFIED_AS_INTERNAL_NUMERIC_IDENTITY "
            "RISK_ENVELOPE_NUMERIC_STATUS=UNINSTANTIATED "
            "RISK_ENVELOPE_NUMERIC=NONE "
            "SUI_RISK_ENVELOPE_NUMERIC_PROVEN=false "
            "NO_PROMOTION_IDENTITY_TO_FINISHED_RISK_ENVELOPE_NUMERIC=true"
        ),
        "evidence_source": "canonical persist Z2BX P5 identity plus Cover negative contract",
        "epistemic_class": "ALREADY_ADJUDICATED_CONCLUSIONS",
        "current_applicability": "CONTROLLING_NEGATIVE_FINISHED_PROOF_CONTRACT",
        "superseded_stale": "false",
        "contradictions": "NONE",
        "relation_to_current_sui": "IDENTITY_BOUND_FOR_SUI_FINISHED_NUMERIC_STILL_UNINSTANTIATED",
    },
    {
        "path": "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md#11.13.5.Z2BY",
        "claim": "SUI identity rebind is not finished RISK_ENVELOPE_NUMERIC",
        "evidence_source": "canonical persist Z2BY SUI identity rebind",
        "epistemic_class": "CANONICAL_AUTHORITY",
        "current_applicability": "CURRENT_INSTRUMENT_IS_SUI_FINISHED_ENVELOPE_STILL_UNINSTANTIATED",
        "superseded_stale": "false",
        "contradictions": "NONE",
        "relation_to_current_sui": "REBIND_IS_NOT_FINISHED_ENVELOPE",
    },
    {
        "path": "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md#11.13.5.Z2CG",
        "claim": (
            "FINISHED_RISK_ENVELOPE_NUMERIC_STATUS=UNINSTANTIATED "
            "OBS_SUM_IS_NOT_FINISHED_RISK_ENVELOPE_NUMERIC=true"
        ),
        "evidence_source": "canonical persist Z2CG Class A same-pack",
        "epistemic_class": "CANONICAL_AUTHORITY",
        "current_applicability": "BINDING_NEGATIVE_OBS_SUM_NOT_FINISHED",
        "superseded_stale": "false",
        "contradictions": "NONE",
        "relation_to_current_sui": "OBS_SUM_IS_NOT_FINISHED_ENVELOPE",
    },
    {
        "path": "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md#11.13.5.Z2CD",
        "claim": "P8_FINAL_FORENSIC_AUDIT_DOES_NOT_INSTANTIATE_FINISHED_RISK_ENVELOPE_NUMERIC=true",
        "evidence_source": "canonical persist Z2CD P8 forensic audit",
        "epistemic_class": "ALREADY_ADJUDICATED_CONCLUSIONS",
        "current_applicability": "BINDING_NEGATIVE_P8_NOT_FINISHED",
        "superseded_stale": "false",
        "contradictions": "NONE",
        "relation_to_current_sui": "AUDIT_IS_NOT_FINISHED_ENVELOPE",
    },
    {
        "path": "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md#11.13.5.Z2CU",
        "claim": (
            "REMAINING_UNRANKED_CLASSES includes FINISHED_RISK_ENVELOPE_NUMERIC "
            "as named unranked SUI reproof class"
        ),
        "evidence_source": "canonical persist Z2CU",
        "epistemic_class": "CANONICAL_AUTHORITY",
        "current_applicability": "TRACK_ELIGIBILITY_NOT_FINISHED_PROOF",
        "superseded_stale": "false",
        "contradictions": "NONE",
        "relation_to_current_sui": "NAMES_CLASS_DOES_NOT_PROVE_IT",
    },
    {
        "path": "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md#11.13.5.Z2CV",
        "claim": "FINISHED_RISK_ENVELOPE_NUMERIC_ADJUDICATED_THIS_PERSIST=false",
        "evidence_source": "canonical persist Z2CV COVER_USDC offline reproof",
        "epistemic_class": "CANONICAL_AUTHORITY",
        "current_applicability": "SIBLING_CLASS_NOT_FINISHED_PROOF",
        "superseded_stale": "false",
        "contradictions": "NONE",
        "relation_to_current_sui": "COVER_USDC_FAIL_CLOSED_DOES_NOT_PROVE_FINISHED_ENVELOPE",
    },
    {
        "path": "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md#11.13.5.Z2CW",
        "claim": "FINISHED_RISK_ENVELOPE_NUMERIC_ADJUDICATED_THIS_PERSIST=false",
        "evidence_source": "canonical persist Z2CW FX offline reproof",
        "epistemic_class": "CANONICAL_AUTHORITY",
        "current_applicability": "SIBLING_CLASS_NOT_FINISHED_PROOF",
        "superseded_stale": "false",
        "contradictions": "NONE",
        "relation_to_current_sui": "FX_FAIL_CLOSED_DOES_NOT_PROVE_FINISHED_ENVELOPE",
    },
    {
        "path": (
            "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/exact_formula_body_v1.py"
        ),
        "claim": "SUM_INTERNAL_NUMERIC_STATUS = UNINSTANTIATED NUMERIC_FUNDING_AMOUNT = NONE",
        "evidence_source": "current Python contract constant",
        "epistemic_class": "CANONICAL_AUTHORITY",
        "current_applicability": "CURRENT_RUNTIME_CONTRACT_STATUS",
        "superseded_stale": "false",
        "contradictions": "NONE",
        "relation_to_current_sui": "SUM_INTERNAL_IS_NOT_FINISHED_ENVELOPE",
    },
    {
        "path": (
            "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/"
            "position_value_fx_rounding_chain_v1.py"
        ),
        "claim": "COVER_USDC_STATUS = UNINSTANTIATED ROUNDING_APPLIED = False USD_USDC_CONVERSION_APPLIED = False",
        "evidence_source": "current Python contract constant",
        "epistemic_class": "CANONICAL_AUTHORITY",
        "current_applicability": "CURRENT_RUNTIME_CONTRACT_STATUS",
        "superseded_stale": "false",
        "contradictions": "NONE",
        "relation_to_current_sui": "STANDING_BLOCKERS_NOT_FINISHED_ENVELOPE",
    },
    {
        "path": (
            "evidence/ops/section_11_13_5_z2g_current_markpx_public_get_v1/"
            "20260818T200745Z/claims.json"
        ),
        "claim": "BTC-era markPx pack; COVER_USDC_STATUS=UNINSTANTIATED; not finished SUI envelope",
        "evidence_source": "forensic GET pack Z2G",
        "epistemic_class": "FORENSIC_RAW_ORIGINALS",
        "current_applicability": "NOT_CURRENT_SUI_FINISHED_ENVELOPE",
        "superseded_stale": "true_btc_era_and_explicitly_not_cover",
        "contradictions": "NONE",
        "relation_to_current_sui": "SCOPE_MISMATCH_BTC_NOT_SUI",
    },
    {
        "path": (
            "evidence/ops/section_11_13_5_z2k_current_public_tier_mmr_public_get_v1/"
            "20260819T085545Z/claims.json"
        ),
        "claim": "BTC-era public-tier MMR pack is not finished SUI RISK_ENVELOPE_NUMERIC",
        "evidence_source": "forensic GET pack Z2K",
        "epistemic_class": "FORENSIC_RAW_ORIGINALS",
        "current_applicability": "NOT_CURRENT_SUI_FINISHED_ENVELOPE",
        "superseded_stale": "true_btc_era",
        "contradictions": "NONE",
        "relation_to_current_sui": "SCOPE_MISMATCH_BTC_NOT_SUI",
    },
    {
        "path": (
            "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/governance_state_matrix_v1.py"
        ),
        "claim": "historical next pointers; identity/composition pointers are not finished numeric",
        "evidence_source": "governance state matrix historical pointers",
        "epistemic_class": "HISTORICAL_INTERMEDIATE_STATE",
        "current_applicability": "POINTER_NOT_CURRENT_FINISHED_PROOF",
        "superseded_stale": "historical_next_pointers",
        "contradictions": "NONE",
        "relation_to_current_sui": "DOES_NOT_PROVE_FINISHED_ENVELOPE",
    },
    {
        "path": "docs/governance/PEAK_TRADE_MAP_OF_TRUTH.md",
        "claim": "navigation pointers to Z2D-Z2BX envelope/rounding status; not finished numeric proof",
        "evidence_source": "Map of Truth",
        "epistemic_class": "NAVIGATION_INDEX_ONLY",
        "current_applicability": "NAVIGATION_NOT_AUTHORITY",
        "superseded_stale": "false_as_navigation",
        "contradictions": "NONE",
        "relation_to_current_sui": "POINTER_ONLY",
    },
    {
        "path": "docs/system_atlas/entities/catalog.yaml",
        "claim": "Atlas PHASE notes remaining unranked finished envelope; Atlas is not trading authority",
        "evidence_source": "Atlas catalog",
        "epistemic_class": "NAVIGATION_INDEX_ONLY",
        "current_applicability": "NAVIGATION_NOT_AUTHORITY",
        "superseded_stale": "false_as_navigation",
        "contradictions": "NONE",
        "relation_to_current_sui": "POINTER_ONLY",
    },
    {
        "path": "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md#11.13.5.Z2BO",
        "claim": (
            "SUI_COMPOSITION_ROLE=PEAK_TRADE_INTERNAL_CONSERVATIVE_RESERVE_COMPOSITION_"
            "NOT_COVER_USDC_NOT_RISK_ENVELOPE_NUMERIC_NOT_OKX_POSITION_VALUE"
        ),
        "evidence_source": "canonical persist Z2BO composition membership form",
        "epistemic_class": "CANONICAL_AUTHORITY",
        "current_applicability": "BINDING_NEGATIVE_FORM_NOT_FINISHED_NUMERIC",
        "superseded_stale": "false",
        "contradictions": "NONE",
        "relation_to_current_sui": "MEMBERSHIP_FORM_IS_NOT_FINISHED_ENVELOPE",
    },
    {
        "path": (
            "evidence/ops/section_11_13_5_z2h_current_ticker_bid_ask_public_get_v1/"
            "20260818T203435Z/claims.json"
        ),
        "claim": "BTC-era ticker pack; not finished SUI RISK_ENVELOPE_NUMERIC",
        "evidence_source": "forensic GET pack Z2H",
        "epistemic_class": "FORENSIC_RAW_ORIGINALS",
        "current_applicability": "NOT_CURRENT_SUI_FINISHED_ENVELOPE",
        "superseded_stale": "true_btc_era",
        "contradictions": "NONE",
        "relation_to_current_sui": "SCOPE_MISMATCH_BTC_NOT_SUI",
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
    "SEPARATE_OWNER_MERGE_GO_REQUIRED_NO_FINISHED_RISK_ENVELOPE_NUMERIC_UPGRADE_"
    "FROM_IDENTITY_OR_COMPOSITION_NO_GET_UNLESS_SEPARATELY_NAMED_NO_CLASS_D_"
    "NO_Z2AP_NO_FLATTEN"
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


class LiveCanaryZ2arFinishedRiskEnvelopeNumericOfflineReproofError(RuntimeError):
    """Fail-closed FINISHED_RISK_ENVELOPE_NUMERIC offline reproof violation."""


def _fail(code: str) -> None:
    raise LiveCanaryZ2arFinishedRiskEnvelopeNumericOfflineReproofError(code)


def reject_historical_or_navigation_upgrade_v1(
    *,
    upgrade_historical_to_proven: bool = False,
    upgrade_navigation_to_proven: bool = False,
) -> None:
    """Historical existence and navigation indexes are not finished-envelope proof."""
    if upgrade_historical_to_proven:
        _fail("FORBIDDEN_UPGRADE_HISTORICAL_TO_PROVEN")
    if upgrade_navigation_to_proven:
        _fail("FORBIDDEN_UPGRADE_NAVIGATION_TO_PROVEN")


def reject_identity_or_composition_upgrade_v1(
    *,
    treat_identity_as_finished: bool = False,
    treat_composition_as_finished: bool = False,
) -> None:
    """Internal identity and composition numeric are not finished proof."""
    if treat_identity_as_finished:
        _fail("FORBIDDEN_UPGRADE_IDENTITY_TO_FINISHED_RISK_ENVELOPE_NUMERIC")
    if treat_composition_as_finished:
        _fail("FORBIDDEN_UPGRADE_COMPOSITION_TO_FINISHED_RISK_ENVELOPE_NUMERIC")


def reject_class_collapse_v1(
    *,
    mix_with_fx: bool = False,
    mix_with_rounding: bool = False,
    mix_with_cover_usdc: bool = False,
    mix_with_account_settlement: bool = False,
    named_class: str = Z2AR_CLASS,
) -> None:
    """Finished envelope must not be collapsed onto sibling Z2AR classes."""
    if named_class != Z2AR_CLASS:
        _fail("FORBIDDEN_Z2AR_CLASS_MISMATCH")
    if mix_with_fx:
        _fail("FORBIDDEN_COLLAPSE_FINISHED_ENVELOPE_WITH_FX")
    if mix_with_rounding:
        _fail("FORBIDDEN_COLLAPSE_FINISHED_ENVELOPE_WITH_ROUNDING")
    if mix_with_cover_usdc:
        _fail("FORBIDDEN_COLLAPSE_FINISHED_ENVELOPE_WITH_COVER_USDC")
    if mix_with_account_settlement:
        _fail("FORBIDDEN_COLLAPSE_FINISHED_ENVELOPE_WITH_ACCOUNT_SETTLEMENT")


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


def adjudicate_finished_risk_envelope_numeric_offline_reproof_v1(
    *,
    claimed_status: str | None = None,
    claimed_reproof_proven: bool | None = None,
    mix_with_fx: bool = False,
    mix_with_rounding: bool = False,
    mix_with_cover_usdc: bool = False,
    mix_with_account_settlement: bool = False,
    implied_venue_observation: bool = False,
    execution_ready_claim: bool = False,
    get_performed_claim: bool = False,
    post_performed_claim: bool = False,
    flatten_performed_claim: bool = False,
    class_d_consumed_claim: bool = False,
    z2ap_consumed_claim: bool = False,
    upgrade_historical_to_proven: bool = False,
    upgrade_navigation_to_proven: bool = False,
    treat_identity_as_finished: bool = False,
    treat_composition_as_finished: bool = False,
    named_class: str = Z2AR_CLASS,
    reopen_fx: bool = False,
    adjudicate_cover_usdc: bool = False,
) -> dict[str, Any]:
    """Return the fail-closed finished-envelope offline reproof. Caller facts only."""
    if BOUND_SUM_INTERNAL_NUMERIC_STATUS != "UNINSTANTIATED":
        _fail("DRIFT_SUM_INTERNAL_NUMERIC_STATUS")
    if BOUND_COVER_USDC_STATUS != "UNINSTANTIATED":
        _fail("DRIFT_BOUND_COVER_USDC_STATUS_NOT_UNINSTANTIATED")
    if BOUND_ROUNDING_APPLIED is True:
        _fail("DRIFT_ROUNDING_APPLIED")
    if BOUND_USD_USDC_CONVERSION_APPLIED is True:
        _fail("DRIFT_USD_USDC_CONVERSION_APPLIED")
    if reopen_fx:
        _fail("FORBIDDEN_FX_REOPEN")
    if adjudicate_cover_usdc:
        _fail("FORBIDDEN_COVER_USDC_ADJUDICATION")

    reject_class_collapse_v1(
        mix_with_fx=mix_with_fx,
        mix_with_rounding=mix_with_rounding,
        mix_with_cover_usdc=mix_with_cover_usdc,
        mix_with_account_settlement=mix_with_account_settlement,
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
    reject_identity_or_composition_upgrade_v1(
        treat_identity_as_finished=treat_identity_as_finished,
        treat_composition_as_finished=treat_composition_as_finished,
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
        "CURRENT_FINISHED_RISK_ENVELOPE_NUMERIC_STATUS": (
            CURRENT_FINISHED_RISK_ENVELOPE_NUMERIC_STATUS
        ),
        "REPROOF_PROVEN": REPROOF_PROVEN,
        "RISK_ENVELOPE_NUMERIC_STATUS": RISK_ENVELOPE_NUMERIC_STATUS,
        "RISK_ENVELOPE_NUMERIC": RISK_ENVELOPE_NUMERIC,
        "RISK_ENVELOPE_NUMERIC_PROVEN": RISK_ENVELOPE_NUMERIC_PROVEN,
        "SUI_RISK_ENVELOPE_NUMERIC_PROVEN": SUI_RISK_ENVELOPE_NUMERIC_PROVEN,
        "NAMED_CLASS_RISK_ENVELOPE_NUMERICS_CLOSED": NAMED_CLASS_RISK_ENVELOPE_NUMERICS_CLOSED,
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
        "NO_PROMOTION_IDENTITY_TO_FINISHED_RISK_ENVELOPE_NUMERIC": (
            NO_PROMOTION_IDENTITY_TO_FINISHED_RISK_ENVELOPE_NUMERIC
        ),
    }
