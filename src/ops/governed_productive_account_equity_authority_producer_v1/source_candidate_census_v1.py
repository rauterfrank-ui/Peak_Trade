"""Read-only C17+ account-equity source-candidate census.

Existing repo/evidence inventory only. No plausibility reconstruction.
No C01-C16 revival. No fake C17 minting.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Mapping, Tuple

from src.ops.governed_productive_account_equity_authority_producer_v1.source_candidate_v1 import (
    C01_C16_IDS,
    GovernedAccountEquitySourceCandidateV1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.source_promotion_state_machine_v1 import (
    STATE_ACCEPTANCE_FAILED,
    STATE_EVIDENCE_INCOMPLETE,
)

SCHEMA_CLASS = "GOVERNED_ACCOUNT_EQUITY_SOURCE_CANDIDATE_CENSUS_V1"
CONTRACT_VERSION = "v1"
AUTHORITY_EFFECT = "NONE"
CANDIDATE_CENSUS_COMPLETE = True
C17_CREATED = False
GENUINELY_NEW_CANDIDATE_COUNT = 0
ACCEPTABLE_FOR_OWNER_RATIFICATION_COUNT = 0
C01_C16_REVIVAL_ALLOWED = False
NEXT_EVIDENCE_GENERATION_BLOCKER = (
    "NO_GOVERNED_RUNNING_ACCOUNT_EQUITY_SAMPLE_RUNTIME_INSTANCE_WITH_DISTINCT_C17_PLUS_PROVENANCE"
)

C01_C16_FINGERPRINTS: Mapping[str, str] = {
    "C01_Q_GET_PACK_DETAILS_AVAILEQ": (
        "GET /api/v5/account/balance details.availEq; AVAILABLE_MARGIN not 29P equity"
    ),
    "C02_FORBIDDEN_RAW_VENUE_EQ_FIELDS": ("raw venue totalEq|eq|adjEq|availEq|availBal|cashBal"),
    "C03_CAPITAL_ADMISSION_ENVELOPE": "CapitalAdmissionClaimV1 envelope not source",
    "C04_CRS_ACCOUNT_EQUITY_CONSUMER": "CRS injected consumer account_equity",
    "C05_OFFLINE_REPLAY_DEFAULT_10000": "offline Decimal(10000) default",
    "C06_INJECTED_RUNNING_ACCOUNT_EQUITY": "injected_running_account_equity fixture",
    "C07_FUNDING_ACCOUNT_BALANCE_OBSERVATION": (
        "FundingAccountBalanceObservationV1 asset/balances"
    ),
    "C08_TREASURY_OBSERVED_OR_RECONCILED_CAPITAL": "treasury OBSERVED/RECONCILED capital",
    "C09_CAP11_3_FIXTURE_PRIVATE_ACCOUNT_STATE": "PrivateAccountStateSnapshotV1 fixture",
    "C10_LEDGER_SNAPSHOT_EQUITY_BY_CCY": "LedgerSnapshot.equity_by_ccy",
    "C11_CAP31_PRODUCTIVE_FUTURES_ACCOUNTING": "productive_futures_accounting kernel",
    "C12_S1114_LIVE_ACCOUNTING_RECONSTRUCTED": (
        "section 11.14 reconstructed realized pnl not running equity"
    ),
    "C13_BACKTEST_STATE_FILE_ACCOUNT_EQUITY": "backtest state-file account_equity",
    "C14_START_BALANCE": "start_balance initial cash",
    "C15_LIVE_ACCOUNT_BOUND_IDENTITY": "LiveAccountBound identity seam",
    "C16_RESTART_RECONSTRUCTION_ACCOUNTING": "restart/fill reconstruction not 29P equity",
}


@dataclass(frozen=True)
class SourceCandidateCensusFindingV1:
    finding_id: str
    candidate_origin: str
    raw_object: str
    producer: str
    current_authority_class: str
    account_scope: str
    venue_scope: str
    currency: str
    freshness: str
    reconcilability: str
    restart_reconstructability: str
    step_29p_compatibility: str
    overlap_with_c01_c16: str
    evidence_refs: str
    acceptance_status: str
    rejection_or_gap_reason: str
    genuinely_new_source_generation: str
    c17_plus_materialized: str


@dataclass(frozen=True)
class SourceCandidateCensusReportV1:
    census_id: str
    census_complete: str
    raw_candidate_origins_found: str
    c01_c16_revival_equivalents_rejected: str
    genuinely_new_candidate_count: str
    candidate_ids_created: str
    c17_created: str
    acceptable_for_owner_ratification_count: str
    acceptable_candidate_ids: str
    candidate_gaps: str
    next_evidence_generation_blocker: str
    mapping_proven: str
    governed_producer_created: str
    productive_runtime_binding_added: str
    authority_effect: str
    findings: Tuple[SourceCandidateCensusFindingV1, ...]
    census_digest: str


def _digest(payload: Mapping[str, str]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _finding(
    *,
    finding_id: str,
    candidate_origin: str,
    raw_object: str,
    producer: str,
    current_authority_class: str,
    account_scope: str,
    venue_scope: str,
    currency: str,
    freshness: str,
    reconcilability: str,
    restart_reconstructability: str,
    step_29p_compatibility: str,
    overlap_with_c01_c16: str,
    evidence_refs: str,
    acceptance_status: str,
    rejection_or_gap_reason: str,
    genuinely_new: bool,
) -> SourceCandidateCensusFindingV1:
    return SourceCandidateCensusFindingV1(
        finding_id=finding_id,
        candidate_origin=candidate_origin,
        raw_object=raw_object,
        producer=producer,
        current_authority_class=current_authority_class,
        account_scope=account_scope,
        venue_scope=venue_scope,
        currency=currency,
        freshness=freshness,
        reconcilability=reconcilability,
        restart_reconstructability=restart_reconstructability,
        step_29p_compatibility=step_29p_compatibility,
        overlap_with_c01_c16=overlap_with_c01_c16,
        evidence_refs=evidence_refs,
        acceptance_status=acceptance_status,
        rejection_or_gap_reason=rejection_or_gap_reason,
        genuinely_new_source_generation="true" if genuinely_new else "false",
        c17_plus_materialized="false",
    )


def build_source_candidate_census_findings_v1() -> Tuple[SourceCandidateCensusFindingV1, ...]:
    rejected = STATE_ACCEPTANCE_FAILED
    incomplete = STATE_EVIDENCE_INCOMPLETE
    findings = [
        _finding(
            finding_id="F01_C01_C16_BASELINE_REJECTION",
            candidate_origin="MASTER_RUNBOOK_11_2_1_S_CENSUS",
            raw_object="C01_THROUGH_C16_EXISTING_SURFACES",
            producer="NONE_FOR_29P_EQUITY_AUTHORITY",
            current_authority_class="REJECTED_HISTORICAL_CENSUS",
            account_scope="MIXED_OR_UNBOUND",
            venue_scope="MIXED_OR_UNBOUND",
            currency="MIXED_OR_NON_AUTHORITY",
            freshness="NOT_ADMISSIBLE_AS_29P_EQUITY",
            reconcilability="FAILED_REQUIRED_COLUMN",
            restart_reconstructability="NOT_29P_EQUITY_RESTART",
            step_29p_compatibility="INCOMPATIBLE",
            overlap_with_c01_c16="IDENTITY",
            evidence_refs=(
                "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md#11.2.1.S;"
                "docs/ops/specs/FULL_CORE_STEP_29P_ACCOUNT_EQUITY_SOURCE_SEMANTIC_MAPPING_RATIFICATION_V1.md"
            ),
            acceptance_status=rejected,
            rejection_or_gap_reason="C01_C16_REJECTION_STILL_BINDING",
            genuinely_new=False,
        ),
        _finding(
            finding_id="F02_GOVERNED_SAMPLE_SCHEMA_ONLY",
            candidate_origin="PACKAGE_SCHEMA",
            raw_object="GOVERNED_RUNNING_ACCOUNT_EQUITY_SAMPLE_V1",
            producer="ops.governed_productive_account_equity_authority_producer_v1",
            current_authority_class="TYPED_SCHEMA_NOT_SOURCE",
            account_scope="SCHEMA_REQUIRES_BOUND_ACCOUNT",
            venue_scope="SCHEMA_REQUIRES_BOUND_VENUE",
            currency="USDC_REQUIRED_BY_SCHEMA",
            freshness="SCHEMA_REQUIRES_FRESHNESS_FIELDS",
            reconcilability="SCHEMA_ONLY_NO_RUNTIME_INSTANCE",
            restart_reconstructability="UNPROVEN",
            step_29p_compatibility="SCHEMA_NOT_PRODUCTIVE_INPUT",
            overlap_with_c01_c16="NONE_AS_SCHEMA_FUTURE_OBJECT_CLASS",
            evidence_refs=(
                "src/ops/governed_productive_account_equity_authority_producer_v1/sample_schema_v1.py;"
                "docs/ops/specs/FULL_CORE_GOVERNED_RUNNING_ACCOUNT_EQUITY_SAMPLE_SCHEMA_V1.md"
            ),
            acceptance_status=incomplete,
            rejection_or_gap_reason="SOURCE_OBJECT_PRESENT=false;SCHEMA_IS_NOT_SOURCE_GENERATION",
            genuinely_new=False,
        ),
        _finding(
            finding_id="F03_VENUE_WITNESS_SCHEMA_ONLY",
            candidate_origin="PACKAGE_SCHEMA",
            raw_object="TradingAccountVenueWitnessObservationV1",
            producer="ops.governed_productive_account_equity_authority_producer_v1",
            current_authority_class="OBSERVATION_SCHEMA_NOT_AUTHORITY",
            account_scope="SCHEMA_REQUIRES_BOUND_ACCOUNT",
            venue_scope="SCHEMA_REQUIRES_BOUND_VENUE",
            currency="SCHEMA_CURRENCY_DOMAIN",
            freshness="EXPLICIT_TIMESTAMPS_NOT_TTL_POLICY",
            reconcilability="RAW_TO_WITNESS_PROVEN=false",
            restart_reconstructability="UNPROVEN",
            step_29p_compatibility="OBSERVATION_NOT_29P_EQUITY",
            overlap_with_c01_c16="C01_OBSERVATION_CLASS",
            evidence_refs=(
                "src/ops/governed_productive_account_equity_authority_producer_v1/"
                "venue_witness_observation_v1.py"
            ),
            acceptance_status=rejected,
            rejection_or_gap_reason="VENUE_WITNESS_RUNTIME_INSTANCE_PRESENT=false;C01_CLASS_REVIVAL_RISK",
            genuinely_new=False,
        ),
        _finding(
            finding_id="F04_NORMALIZATION_SCHEMA_ONLY",
            candidate_origin="PACKAGE_SCHEMA",
            raw_object="NormalizationInclusionAdjudicationV1",
            producer="ops.governed_productive_account_equity_authority_producer_v1",
            current_authority_class="TYPED_ADJUDICATION_SCHEMA_NOT_SOURCE",
            account_scope="INHERITS_WITNESS_IF_PRESENT",
            venue_scope="INHERITS_WITNESS_IF_PRESENT",
            currency="INHERITS_WITNESS_IF_PRESENT",
            freshness="UNPROVEN",
            reconcilability="SEMANTIC_MAPPING_PROVEN=false",
            restart_reconstructability="UNPROVEN",
            step_29p_compatibility="NOT_A_SOURCE",
            overlap_with_c01_c16="DOWNSTREAM_OF_C01_CLASS_WITNESS",
            evidence_refs=(
                "src/ops/governed_productive_account_equity_authority_producer_v1/"
                "normalization_inclusion_adjudication_v1.py"
            ),
            acceptance_status=rejected,
            rejection_or_gap_reason="NORMALIZATION_RUNTIME_INSTANCE_PRESENT=false;NOT_SOURCE_GENERATION",
            genuinely_new=False,
        ),
        _finding(
            finding_id="F05_INTERNAL_RECONSTRUCTION_SCHEMA_ONLY",
            candidate_origin="PACKAGE_SCHEMA",
            raw_object="InternalReconstructionContractV1",
            producer="ops.governed_productive_account_equity_authority_producer_v1",
            current_authority_class="TYPED_RECONSTRUCTION_SCHEMA_NOT_SOURCE",
            account_scope="INHERITS_IF_PRESENT",
            venue_scope="INHERITS_IF_PRESENT",
            currency="INHERITS_IF_PRESENT",
            freshness="UNPROVEN",
            reconcilability="RECONSTRUCTION_ALGEBRA_COMPLETE=false",
            restart_reconstructability="UNPROVEN",
            step_29p_compatibility="NOT_A_SOURCE",
            overlap_with_c01_c16="C10_C16_CLASS_RISK_IF_ELEVATED",
            evidence_refs=(
                "src/ops/governed_productive_account_equity_authority_producer_v1/"
                "internal_reconstruction_contract_v1.py"
            ),
            acceptance_status=rejected,
            rejection_or_gap_reason="INTERNAL_RECONSTRUCTION_RUNTIME_INSTANCE_PRESENT=false",
            genuinely_new=False,
        ),
        _finding(
            finding_id="F06_FRESH_AVAILABLE_MARGIN_OBSERVATION",
            candidate_origin="CANARY_PRETRADE_OBSERVATION",
            raw_object="FreshAvailableMarginObservationV1",
            producer="section_11_13_5_live_canary_minimum_exposure_v1",
            current_authority_class="AVAILABLE_MARGIN_OBSERVATION_NOT_29P_EQUITY",
            account_scope="CANARY_ACCOUNT",
            venue_scope="OKX",
            currency="USDC_OR_OBSERVED_CCY",
            freshness="FRESH_GET_WHEN_PERFORMED",
            reconcilability="AVAILABLE_MARGIN_NOT_29P_EQUITY_RECON",
            restart_reconstructability="NOT_29P_EQUITY_RESTART",
            step_29p_compatibility="FORBIDDEN_FIELD_CLASS",
            overlap_with_c01_c16="C01",
            evidence_refs=(
                "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/"
                "available_margin_observation_v1.py"
            ),
            acceptance_status=rejected,
            rejection_or_gap_reason="C01_REVIVAL_EQUIVALENT_AVAILEQ_AVAILABLE_MARGIN",
            genuinely_new=False,
        ),
        _finding(
            finding_id="F07_SIMULATED_PORTFOLIO_STATE",
            candidate_origin="PAPER_SHADOW_SIMULATION",
            raw_object="SimulatedPortfolioStateV1",
            producer="integrated_paper_shadow_observation_session_v1",
            current_authority_class="OFFLINE_OR_SIMULATION_NOT_AUTHORITY",
            account_scope="SIMULATED",
            venue_scope="NONE_OR_PAPER",
            currency="SIMULATED",
            freshness="NONE_AS_LIVE_EQUITY",
            reconcilability="NONE_FOR_LIVE_29P",
            restart_reconstructability="SIMULATED_NOT_LIVE_RESTART",
            step_29p_compatibility="INCOMPATIBLE",
            overlap_with_c01_c16="C05_C10_CLASS",
            evidence_refs=(
                "src/ops/integrated_paper_shadow_observation_session_v1/"
                "portfolio_economics_model_v1.py"
            ),
            acceptance_status=rejected,
            rejection_or_gap_reason="SIMULATED_SUBSTITUTION_FORBIDDEN",
            genuinely_new=False,
        ),
        _finding(
            finding_id="F08_EMPTY_GOVERNED_PRODUCER_SLOT",
            candidate_origin="OWNER_ASSIGNMENT_SLOT",
            raw_object="GOVERNED_PRODUCTIVE_ACCOUNT_EQUITY_AUTHORITY_PRODUCER",
            producer="ops.governed_productive_account_equity_authority_producer_v1",
            current_authority_class="EMPTY_GOVERNED_AUTHORITY_OWNER_SLOT",
            account_scope="UNBOUND",
            venue_scope="UNBOUND",
            currency="UNBOUND",
            freshness="NONE",
            reconcilability="NONE",
            restart_reconstructability="NONE",
            step_29p_compatibility="SLOT_IS_NOT_SOURCE",
            overlap_with_c01_c16="NONE",
            evidence_refs=(
                "src/ops/governed_productive_account_equity_authority_producer_v1/constants_v1.py;"
                "docs/ops/specs/FULL_CORE_ACCOUNT_EQUITY_AUTHORITY_OWNER_CONCRETE_ASSIGNMENT_RATIFICATION_V1.md"
            ),
            acceptance_status=rejected,
            rejection_or_gap_reason="GOVERNED_PRODUCER_CREATED=false;SLOT_IS_EMPTY=true",
            genuinely_new=False,
        ),
        _finding(
            finding_id="F09_P08_POS_C17_DIFFERENT_DIMENSION",
            candidate_origin="SECTION_11_14_POS_TEMPORAL_PROVENANCE",
            raw_object="C17_P08_HISTORICAL_CAPTURED_POS",
            producer="section_11_14_live_order_and_economic_evidence_ladder_v1",
            current_authority_class="POSITION_EVIDENCE_NOT_ACCOUNT_EQUITY",
            account_scope="CANARY_OR_HISTORICAL",
            venue_scope="OKX",
            currency="NOT_RUNNING_ACCOUNT_EQUITY",
            freshness="HISTORICAL_CAPTURE",
            reconcilability="POS_NOT_29P_EQUITY",
            restart_reconstructability="POS_RESTART_NOT_EQUITY_SOURCE",
            step_29p_compatibility="DIFFERENT_DIMENSION",
            overlap_with_c01_c16="NONE_DIMENSION_MISMATCH",
            evidence_refs=(
                "src/ops/section_11_14_live_order_and_economic_evidence_ladder_v1/"
                "restart_reconstructed_pos_semantics_canonical_binding_v1.py;"
                "evidence/ops/section_11_14_live_order_and_economic_evidence_ladder_v1/"
                "20260906T221200Z/POS_TEMPORAL_PROVENANCE.json"
            ),
            acceptance_status=rejected,
            rejection_or_gap_reason="POS_CANDIDATE_ID_IS_NOT_ACCOUNT_EQUITY_SOURCE;ID_COLLISION_FENCE",
            genuinely_new=False,
        ),
        _finding(
            finding_id="F10_SAMPLE_SCHEMA_PRE_FENCED_TOKENS",
            candidate_origin="SAMPLE_SCHEMA_FORBIDDEN_OBJECT_TOKENS",
            raw_object="c17freshavailablemargin|c18simulatedportfolio|c19exchangebasebalance|c20reconbalancesnapshot|c21dryrunorderplaneqfallback",
            producer="NONE",
            current_authority_class="PRE_FENCED_NON_SOURCE",
            account_scope="UNBOUND",
            venue_scope="UNBOUND",
            currency="UNBOUND",
            freshness="NONE",
            reconcilability="NONE",
            restart_reconstructability="NONE",
            step_29p_compatibility="FORBIDDEN_OBJECT_CLASS",
            overlap_with_c01_c16="C01_C05_C07_C10_C16_CLASS",
            evidence_refs=(
                "src/ops/governed_productive_account_equity_authority_producer_v1/sample_schema_v1.py"
            ),
            acceptance_status=rejected,
            rejection_or_gap_reason="PRE_FENCED_TOKENS_ARE_NOT_NEW_SOURCE_GENERATIONS",
            genuinely_new=False,
        ),
        _finding(
            finding_id="F11_P01_CLOSEOUT_NOT_EQUITY_SOURCE",
            candidate_origin="MASTER_RUNBOOK_11_2_1_AP",
            raw_object="P01_RECONSTRUCTION_SEMANTIC_AND_ALGEBRA_CLOSEOUT_CONTRACT_V1",
            producer="ops.governed_productive_account_equity_authority_producer_v1",
            current_authority_class="P01_RECONSTRUCTION_DIRECTIVE_NOT_EQUITY_SOURCE",
            account_scope="RECONSTRUCTION_ONLY",
            venue_scope="NONE",
            currency="PARENT_DIMENSION_REDUCTION_AMOUNT",
            freshness="P01_INPUT_FRESHNESS_RULE_UNRESOLVED",
            reconcilability="P01_PRODUCTIVE_EXTERNAL_SOURCE_MAPPING_RESOLVED=false",
            restart_reconstructability="NOT_ACCOUNT_EQUITY_SOURCE",
            step_29p_compatibility="P01_IS_NOT_EQUITY_SOURCE",
            overlap_with_c01_c16="NONE_AS_P01_TERM",
            evidence_refs=(
                "src/ops/governed_productive_account_equity_authority_producer_v1/"
                "p01_reconstruction_semantic_and_algebra_closeout_contract_v1.py"
            ),
            acceptance_status=rejected,
            rejection_or_gap_reason="P01_IS_RECONSTRUCTION_TERM_NOT_ACCOUNT_EQUITY_SOURCE",
            genuinely_new=False,
        ),
    ]
    return tuple(findings)


def build_source_candidate_census_report_v1() -> SourceCandidateCensusReportV1:
    findings = build_source_candidate_census_findings_v1()
    revival_count = sum(
        1
        for item in findings
        if item.overlap_with_c01_c16
        not in {
            "NONE",
            "NONE_AS_SCHEMA_FUTURE_OBJECT_CLASS",
            "NONE_AS_P01_TERM",
            "NONE_DIMENSION_MISMATCH",
        }
        or item.finding_id == "F01_C01_C16_BASELINE_REJECTION"
    )
    payload = {
        "census_id": "EQUITY_RECOVERY_PR1_CANDIDATE_CENSUS_V1",
        "census_complete": "true",
        "raw_candidate_origins_found": str(len(findings)),
        "c01_c16_revival_equivalents_rejected": str(revival_count),
        "genuinely_new_candidate_count": "0",
        "candidate_ids_created": "NONE",
        "c17_created": "false",
        "acceptable_for_owner_ratification_count": "0",
        "acceptable_candidate_ids": "NONE",
        "candidate_gaps": NEXT_EVIDENCE_GENERATION_BLOCKER,
        "next_evidence_generation_blocker": NEXT_EVIDENCE_GENERATION_BLOCKER,
        "mapping_proven": "false",
        "governed_producer_created": "false",
        "productive_runtime_binding_added": "false",
        "authority_effect": AUTHORITY_EFFECT,
        "c01_c16_count": str(len(C01_C16_IDS)),
        "finding_ids": ",".join(item.finding_id for item in findings),
    }
    return SourceCandidateCensusReportV1(
        census_id=payload["census_id"],
        census_complete=payload["census_complete"],
        raw_candidate_origins_found=payload["raw_candidate_origins_found"],
        c01_c16_revival_equivalents_rejected=payload["c01_c16_revival_equivalents_rejected"],
        genuinely_new_candidate_count=payload["genuinely_new_candidate_count"],
        candidate_ids_created=payload["candidate_ids_created"],
        c17_created=payload["c17_created"],
        acceptable_for_owner_ratification_count=payload["acceptable_for_owner_ratification_count"],
        acceptable_candidate_ids=payload["acceptable_candidate_ids"],
        candidate_gaps=payload["candidate_gaps"],
        next_evidence_generation_blocker=payload["next_evidence_generation_blocker"],
        mapping_proven=payload["mapping_proven"],
        governed_producer_created=payload["governed_producer_created"],
        productive_runtime_binding_added=payload["productive_runtime_binding_added"],
        authority_effect=payload["authority_effect"],
        findings=findings,
        census_digest=_digest(payload),
    )


def materialize_c17_plus_candidates_v1() -> Tuple[GovernedAccountEquitySourceCandidateV1, ...]:
    report = build_source_candidate_census_report_v1()
    if report.c17_created != "false":
        raise RuntimeError("CENSUS_C17_CREATED_DRIFT")
    if report.genuinely_new_candidate_count != "0":
        raise RuntimeError("CENSUS_NEW_CANDIDATE_COUNT_DRIFT")
    return tuple()
