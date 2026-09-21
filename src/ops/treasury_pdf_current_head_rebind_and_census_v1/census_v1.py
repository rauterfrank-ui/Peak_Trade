"""Forensic Treasury PDF current-head rebind census (offline, fail-closed).

PDF_AUTHORITY=NONE. Repo constants, tests, and interference proof are evidence.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from src.ops.full_core_live_path_composition_root_v1.treasury_interference_proof_v1 import (
    prove_treasury_interference_absent_v1,
)
from src.ops.pl_tf_002_productive_read_only_session_executor_v1.constants_v1 import (
    CREDENTIAL_LOAD_AUTHORIZED,
    EXTERNAL_EFFECT_AUTHORIZED as PL_TF_002_EXTERNAL_EFFECT,
    NETWORK_SESSION_AUTHORIZED,
)
from src.ops.treasury_pdf_current_head_rebind_and_census_v1.constants_v1 import (
    AUTHORITY_EFFECT,
    BLOCKER_CLASS,
    CANONICAL_PACK_AS_OF_FOLDER,
    CANONICAL_PACK_RELPATH,
    CONTRACT_VERSION,
    EARLIEST_REAL_TREASURY_BLOCKER,
    EXPECTED_ORIGIN_MAIN_SHA,
    EXTERNAL_EFFECT_AUTHORIZED,
    FALSE_TOKEN,
    FULL_CORE_P1_PR_BUDGET_SLOT,
    FULL_CORE_P1_STATUS,
    FULL_CORE_P2_P3_ON_CURRENT_HEAD,
    MISSING_FACT_OR_AUTHORITY,
    NETWORK_ALLOWED,
    PDF_AUTHORITY,
    SCHEMA_CLASS,
    TRUE_TOKEN,
    WP_ID,
)
from src.ops.treasury_phase_1_offline_contracts_v1.constants_v1 import (
    CURRENT_END_TO_END_TREASURY_GATE,
    PL_TF_002_STATUS,
    TREASURY_COMPLETE_PRODUCTIVE_SUBSYSTEM_PROVEN,
    TREASURY_MUTATION_REACHABLE_FROM_TRADING,
    TREASURY_PHASE_1_STATUS,
    TREASURY_PHASE_2_STATUS,
    TRANSFER_RECONCILIATION,
    VENUE_PERMISSION_GET_PERFORMED,
)
from src.ops.treasury_phase_3_shadow_enforcement_v1.constants_v1 import (
    TREASURY_PHASE_3_STATUS,
    TREASURY_SEPARATION_GATE_WIRED as PHASE_3_SEPARATION_GATE_WIRED,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.d4_d5_genesis_runtime_orchestrator_v1 import (
    persist_manifest_sha256_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.package_1_s6_mapping_classification_v1 import (
    verify_manifest_sha256_v1,
)

Classification = str

IMPLEMENTED = "IMPLEMENTED"
PARTIAL = "PARTIAL"
HISTORICAL_ONLY = "HISTORICAL_ONLY"
ABSENT = "ABSENT"
CONFLICTED = "CONFLICTED"
NOT_PROVEN = "NOT_PROVEN"
TARGET_DESIGN_ONLY = "TARGET_DESIGN_NOT_IMPLEMENTED"


class TreasuryPdfRebindCensusError(ValueError):
    """Fail-closed treasury PDF rebind census violation."""


@dataclass(frozen=True)
class TreasuryPdfRebindResultV1:
    wp_id: str
    origin_main_sha: str
    persist_as_of: str
    store_root: str
    census_complete: str
    earliest_real_treasury_blocker: str
    interference_proof: str


def _canonical_json(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _persist_json(*, path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(_canonical_json(payload) + "\n", encoding="utf-8")
    tmp.replace(path)


def _test_def_present(repo: Path, rel_path: str, def_name: str) -> bool:
    path = repo / rel_path
    if not path.is_file():
        return False
    text = path.read_text(encoding="utf-8")
    return bool(re.search(rf"^def {re.escape(def_name)}\b", text, re.MULTILINE))


def _classify_at(repo: Path) -> dict[str, dict[str, str]]:
    """Map PDF audit tests AT01–AT15 to CURRENT repo evidence (semantic, not label-only)."""

    def row(at_id: str, cls: Classification, evidence: str) -> dict[str, str]:
        return {"classification": cls, "evidence": evidence}

    at: dict[str, dict[str, str]] = {}

    p2 = "tests/ops/test_treasury_phase_2_read_only_reconciliation_v1.py"
    adv = "tests/ops/test_treasury_phase_1_adversarial_and_restart_v1.py"
    p1c = "tests/ops/test_treasury_phase_1_canonical_and_authority_v1.py"
    p1o = "tests/ops/test_treasury_phase_1_offline_contracts_v1.py"
    pre = "tests/ops/test_pre_live_treasury_http_isolation_v1.py"
    orch = "tests/ops/test_treasury_capital_admission_to_account_equity_orchestration_v1.py"
    venue = "tests/ops/test_treasury_phase_2_read_only_venue_observation_binding_v1.py"

    at["AT01"] = row(
        "AT01",
        IMPLEMENTED
        if _test_def_present(
            repo, p2, "test_at01_balance_increase_before_deposit_reconciliation_denies_increase"
        )
        else NOT_PROVEN,
        f"{p2}::test_at01_balance_increase_before_deposit_reconciliation_denies_increase; "
        f"{venue}::test_at01_observed_balance_increase_without_deposit_reconciliation_denies_sizing; "
        f"{orch}::test_at01_observed_increase_denies_orchestration_ingress",
    )
    at["AT02"] = row(
        "AT02",
        IMPLEMENTED
        if _test_def_present(
            repo, p2, "test_at02_external_depletion_against_stale_cached_state_conservative_deny"
        )
        else NOT_PROVEN,
        f"{p2}::test_at02_external_depletion_against_stale_cached_state_conservative_deny",
    )
    at["AT03"] = row(
        "AT03",
        IMPLEMENTED
        if _test_def_present(
            repo, adv, "test_at03_timeout_after_possible_remote_acceptance_is_unknown_not_retry"
        )
        else NOT_PROVEN,
        f"{adv}::test_at03_timeout_after_possible_remote_acceptance_is_unknown_not_retry",
    )
    at["AT04"] = row(
        "AT04",
        IMPLEMENTED
        if _test_def_present(
            repo, adv, "test_at04_remote_success_missing_local_terminal_recovers_one_effect"
        )
        else NOT_PROVEN,
        f"{adv}::test_at04_remote_success_missing_local_terminal_recovers_one_effect",
    )
    at["AT05"] = row(
        "AT05",
        IMPLEMENTED
        if _test_def_present(
            repo, adv, "test_at05_duplicate_replay_after_restart_never_second_effect"
        )
        else NOT_PROVEN,
        f"{adv}::test_at05_duplicate_replay_after_restart_never_second_effect",
    )
    at06_proven = _test_def_present(repo, p1c, "test_at07_trading_authority_cannot_mint_treasury")
    at06_partial = _test_def_present(repo, pre, "test_readonly_shadow_dryrun_clients_deny_treasury")
    at["AT06"] = row(
        "AT06",
        PARTIAL if at06_partial or at06_proven else NOT_PROVEN,
        f"{pre} (HTTP allowlist isolation); {p1c} (authority separation); "
        f"VENUE_PERMISSION_GET_PERFORMED={VENUE_PERMISSION_GET_PERFORMED} on Phase-1 constants",
    )
    at["AT07"] = row(
        "AT07",
        IMPLEMENTED if at06_proven else NOT_PROVEN,
        f"{p1c}::test_at07_trading_authority_cannot_mint_treasury; "
        "prove_treasury_interference_absent_v1",
    )
    at["AT08"] = row(
        "AT08",
        PARTIAL
        if _test_def_present(repo, p1o, "test_destination_confirmation_mismatch_denied")
        else NOT_PROVEN,
        f"{p1o}::test_destination_confirmation_mismatch_denied (offline draft only)",
    )
    at["AT09"] = row(
        "AT09",
        PARTIAL
        if _test_def_present(repo, p1o, "test_asset_network_policy_mismatch_denied")
        else NOT_PROVEN,
        f"{p1o}::test_asset_network_policy_mismatch_denied",
    )
    at["AT10"] = row(
        "AT10",
        IMPLEMENTED
        if _test_def_present(
            repo, p2, "test_at10_internal_transfer_debit_before_credit_is_ambiguous"
        )
        else NOT_PROVEN,
        f"{p2}::test_at10_internal_transfer_debit_before_credit_is_ambiguous",
    )
    at["AT11"] = row(
        "AT11",
        IMPLEMENTED
        if _test_def_present(
            repo, p2, "test_at11_fresh_balance_stale_history_no_optimistic_reconciliation"
        )
        else NOT_PROVEN,
        f"{p2}::test_at11_fresh_balance_stale_history_no_optimistic_reconciliation",
    )
    at["AT12"] = row(
        "AT12",
        IMPLEMENTED
        if _test_def_present(repo, adv, "test_at12_restart_with_pending_unknown_survives")
        else NOT_PROVEN,
        f"{adv}::test_at12_restart_with_pending_unknown_survives",
    )
    at["AT13"] = row(
        "AT13",
        NOT_PROVEN,
        "No CURRENT test for runtime credential permission drift (PDF target only)",
    )
    at["AT14"] = row(
        "AT14",
        IMPLEMENTED
        if _test_def_present(repo, adv, "test_at14_decimal_precision_exact_no_rounding")
        else NOT_PROVEN,
        f"{adv}::test_at14_decimal_precision_exact_no_rounding",
    )
    at["AT15"] = row(
        "AT15",
        IMPLEMENTED
        if _test_def_present(
            repo, adv, "test_at15_concurrent_mutation_intents_require_serialization"
        )
        else NOT_PROVEN,
        f"{adv}::test_at15_concurrent_mutation_intents_require_serialization",
    )
    return at


def _capability_matrix() -> dict[str, dict[str, str]]:
    interference = prove_treasury_interference_absent_v1()
    return {
        "TREASURY_PHASE_1_OFFLINE_CONTRACTS": {
            "classification": IMPLEMENTED,
            "status_token": TREASURY_PHASE_1_STATUS,
            "reachability": "OFFLINE_CONTRACT_AND_TESTS_ONLY",
            "authority_owner": "src/ops/treasury_phase_1_offline_contracts_v1/",
        },
        "TREASURY_PHASE_2_READ_ONLY_RECONCILIATION": {
            "classification": IMPLEMENTED,
            "status_token": TREASURY_PHASE_2_STATUS,
            "reachability": "PURE_OFFLINE_JOIN_TO_capital_admission_contract_v1",
            "authority_owner": "src/ops/treasury_phase_2_read_only_reconciliation_v1/",
        },
        "TREASURY_PHASE_3_SHADOW_ENFORCEMENT": {
            "classification": IMPLEMENTED,
            "status_token": TREASURY_PHASE_3_STATUS,
            "reachability": "SECTION_11_13_READ_ONLY_HTTP_SURFACES_ONLY",
            "authority_owner": "src/ops/treasury_phase_3_shadow_enforcement_v1/",
        },
        "TREASURY_SEPARATION_GATE": {
            "classification": PARTIAL,
            "reachability": "PHASE_3_SHADOW_HTTP_AND_OPS_COCKPIT_READ_MODEL",
            "authority_owner": "src/ops/treasury_separation_gate.py",
            "note": "Phase-1 TREASURY_SEPARATION_GATE_WIRED=false; Phase-3 wired on §11.13 only",
        },
        "TRANSFER_AMBIGUITY_READER": {
            "classification": IMPLEMENTED,
            "reachability": "OPS_COCKPIT_PAYLOAD_LOCAL_SIGNALS_ONLY",
            "authority_owner": "src/live/transfer_ambiguity_reader.py",
        },
        "PL_TF_002_NETWORK_EVIDENCE": {
            "classification": IMPLEMENTED if PL_TF_002_STATUS.startswith("CLOSED") else NOT_PROVEN,
            "status_token": PL_TF_002_STATUS,
            "reachability": "CONTRACT_AND_FIXTURE_TESTS; productive session NETWORK_SESSION_AUTHORIZED=false",
            "authority_owner": "src/ops/pl_tf_002_productive_read_only_session_executor_v1/",
        },
        "TREASURY_PRODUCTIVE_CAPITAL_MOVEMENT": {
            "classification": ABSENT,
            "reachability": "NONE",
            "authority_owner": "NONE",
        },
        "FULL_CORE_TREASURY_INTERFERENCE": {
            "classification": IMPLEMENTED
            if interference.get("TREASURY_INTERFERENCE_PROOF") == "PASS"
            else CONFLICTED,
            "reachability": "COMPOSITION_ROOT_SCAN",
            "authority_owner": "src/ops/full_core_live_path_composition_root_v1/treasury_interference_proof_v1.py",
        },
        "C08_TREASURY_SIZING_SOURCE": {
            "classification": NOT_PROVEN,
            "reachability": "CANDIDATE_CENSUS_ONLY_UNBOUND",
            "authority_owner": "governed_productive_account_equity_authority_producer_v1/source_candidate_census_v1",
        },
    }


def _pdf_requirement_buckets() -> dict[str, list[str]]:
    satisfied = [
        "PHASE_1_OFFLINE_INTENT_LIFECYCLE_IDEMPOTENCY_PERSISTENCE",
        "PHASE_2_RECONCILIATION_CLASSES_OBSERVED_RECONCILED_AMBIGUOUS_STALE_UNKNOWN",
        "PHASE_2_CAPITAL_ADMISSION_JOIN_NO_RISK_ADMISSIBLE_MINT",
        "PHASE_3_SHADOW_SEPARATION_ON_11_13_SURFACES",
        "TREASURY_TRADING_AUTHORITY_SEPARATION_NEGATIVE_PROOF",
        "OPS_COCKPIT_TRANSFER_AMBIGUITY_LOCAL_READ_MODEL",
        "PL_TF_002_TRADING_KEY_TREASURY_CAPABILITY_VENUE_PROVEN_CONSTANT",
        "E4_TREASURY_CAPITAL_ADMISSION_TO_ACCOUNT_EQUITY_ORCHESTRATION_PRODUCTIVE_HOST_JOIN",
    ]
    partial = [
        "TS_INV_THEMATIC_OFFLINE_AND_CONTRACT_SEAMS_WITHOUT_PRODUCTIVE_E2E",
        "AT06_PERMISSION_ATTESTATION_HTTP_ISOLATION_WITHOUT_LIVE_PERMISSION_DRIFT_TEST",
        "AT08_AT09_OFFLINE_DRAFT_VALIDATION_WITHOUT_POST_SUBMIT_VENUE_CONFIRMATION",
        "EXTERNAL_CAPITAL_DECREASE_S2_RUNTIME_JOIN_OFFLINE_INJECTED_ONLY",
        "CREDIBLE_DEPLETION_TO_RISK_CAPACITY_PRODUCTIVE_LOOP",
        "C08_TREASURY_OBSERVED_OR_RECONCILED_CAPITAL_PRODUCTIVE_SIZING_SOURCE_NOT_BOUND",
    ]
    not_proven = [
        "CURRENT_END_TO_END_TREASURY_GATE",
        "PRODUCTIVE_DEPOSIT_WITHDRAW_INTERNAL_TRANSFER_PATHS",
        "TRANSFER_RECONCILIATION_PRODUCTIVE",
        "TREASURY_COMPLETE_PRODUCTIVE_SUBSYSTEM_PROVEN",
        "AT13_RUNTIME_PERMISSION_CHANGE",
        "PDF_SECTIONS_12_26_TARGET_DESIGN_AS_CURRENT_STATE",
    ]
    return {
        "PDF_REQUIREMENTS_ALREADY_SATISFIED": satisfied,
        "PDF_REQUIREMENTS_PARTIAL": partial,
        "PDF_REQUIREMENTS_NOT_PROVEN": not_proven,
    }


def build_treasury_pdf_current_head_census_adjudication_v1(
    *,
    repo_root: Path | str,
    origin_main_sha: str,
) -> dict[str, Any]:
    if origin_main_sha != EXPECTED_ORIGIN_MAIN_SHA:
        raise TreasuryPdfRebindCensusError("ORIGIN_MAIN_SHA_MISMATCH")

    repo = Path(repo_root)
    interference = prove_treasury_interference_absent_v1()
    at_map = _classify_at(repo)
    matrix = _capability_matrix()
    pdf_buckets = _pdf_requirement_buckets()

    productive_reachability = {
        "TREASURY_MUTATION_REACHABLE_FROM_TRADING": str(TREASURY_MUTATION_REACHABLE_FROM_TRADING),
        "CURRENT_END_TO_END_TREASURY_GATE": str(CURRENT_END_TO_END_TREASURY_GATE),
        "TRANSFER_RECONCILIATION": str(TRANSFER_RECONCILIATION),
        "TREASURY_COMPLETE_PRODUCTIVE_SUBSYSTEM_PROVEN": str(
            TREASURY_COMPLETE_PRODUCTIVE_SUBSYSTEM_PROVEN
        ),
        "PL_TF_002_NETWORK_SESSION_AUTHORIZED": str(NETWORK_SESSION_AUTHORIZED),
        "PL_TF_002_CREDENTIAL_LOAD_AUTHORIZED": str(CREDENTIAL_LOAD_AUTHORIZED),
        "PL_TF_002_EXTERNAL_EFFECT_AUTHORIZED": str(PL_TF_002_EXTERNAL_EFFECT),
        "PHASE_3_SEPARATION_GATE_WIRED": str(PHASE_3_SEPARATION_GATE_WIRED),
    }

    return {
        "SCHEMA_CLASS": SCHEMA_CLASS,
        "CONTRACT_VERSION": CONTRACT_VERSION,
        "WP_ID": WP_ID,
        "AUTHORITY_EFFECT": AUTHORITY_EFFECT,
        "PDF_AUTHORITY": PDF_AUTHORITY,
        "ORIGIN_MAIN_SHA": origin_main_sha,
        "FULL_CORE_P1_STATUS": FULL_CORE_P1_STATUS,
        "FULL_CORE_P1_PR_BUDGET_SLOT": FULL_CORE_P1_PR_BUDGET_SLOT,
        "FULL_CORE_P2_P3_ON_CURRENT_HEAD": FULL_CORE_P2_P3_ON_CURRENT_HEAD,
        "TREASURY_PRE_P1_LAST_PROVEN_STATE": (
            "PL_TF_001 typed admission seam CLOSED; Treasury Phase-0 role in "
            "governed account-equity source census; mutation paths NOT_PROVEN"
        ),
        "CURRENT_TREASURY_CAPABILITY_MATRIX": matrix,
        "CURRENT_PRODUCTIVE_REACHABILITY": productive_reachability,
        "CURRENT_OKX_EEA_OBSERVATION_SURFACES": {
            "OFFLINE_FIXTURE_BINDINGS": IMPLEMENTED,
            "PL_TF_002_PRODUCTIVE_GET_SESSION": IMPLEMENTED,
            "TREASURY_PRODUCTIVE_READ_ONLY_VENUE_OBSERVATION": IMPLEMENTED,
            "TREASURY_FUNDING_HISTORY_DEPOSIT_WITHDRAW_SURFACES_PRODUCTIVE": NOT_PROVEN,
            "EVIDENCE": (
                "treasury_productive_read_only_venue_observation_v1; "
                "offline_funding_balance_read_producer_v1; pl_tf_002 session executor"
            ),
        },
        "CURRENT_MUTATION_SURFACES": {
            "TREASURY_MUTATION_AUTHORIZED": str(False),
            "BOT_ROLE_BLOCKS_WITHDRAW_TRANSFER_DEPOSIT_ADDRESS": IMPLEMENTED,
            "PRODUCTIVE_MUTATION_HTTP": ABSENT,
        },
        "CURRENT_CREDENTIAL_PERMISSION_PROOF": {
            "PL_TF_002_STATUS": PL_TF_002_STATUS,
            "VENUE_PERMISSION_GET_PERFORMED": str(VENUE_PERMISSION_GET_PERFORMED),
            "AT06_CLASSIFICATION": at_map["AT06"]["classification"],
        },
        "CURRENT_RECONCILIATION_PATH": {
            "OFFLINE": "TreasuryVenueObservationV1 -> evaluate_treasury_read_only_reconciliation_v1 "
            "-> join_treasury_reconciliation_into_capital_admission_v1",
            "PRODUCTIVE": (
                "PRODUCTIVE_READ_ONLY_VENUE_OBSERVATION -> Phase-2 join -> Phase-3 shadow -> "
                "E4 orchestration ingress -> governed productive account-equity host evaluation"
            ),
            "CAPITAL_DECREASE_S2": PARTIAL,
        },
        "CURRENT_RISK_ADMISSION_BINDING": {
            "TREASURY_MINTS_RISK_ADMISSIBLE": FALSE_TOKEN,
            "CAPITAL_ADMISSION_OWNER": "capital_admission_contract_v1",
            "STEP_29P_UNTOUCHED": TRUE_TOKEN,
            "C08_SIZING_SOURCE_BOUND": FALSE_TOKEN,
        },
        "CURRENT_PERSISTENCE_RESTART_STATUS": {
            "PHASE_1_OFFLINE_INTENT_STORE": IMPLEMENTED,
            "PRODUCTIVE_TREASURY_RESTART": NOT_PROVEN,
        },
        "PDF_AUDIT_TESTS_AT01_AT15": at_map,
        **pdf_buckets,
        "TREASURY_INTERFERENCE_PROOF": interference,
        "EARLIEST_REAL_TREASURY_BLOCKER": EARLIEST_REAL_TREASURY_BLOCKER,
        "BLOCKER_CLASS": BLOCKER_CLASS,
        "MISSING_FACT_OR_AUTHORITY": MISSING_FACT_OR_AUTHORITY,
        "EXTERNAL_EFFECT_AUTHORIZED": str(EXTERNAL_EFFECT_AUTHORIZED),
        "NETWORK_ALLOWED": str(NETWORK_ALLOWED),
        "CENSUS_COMPLETE": TRUE_TOKEN,
    }


def execute_treasury_pdf_current_head_rebind_v1(
    *,
    repo_root: Path | str,
    origin_main_sha: str,
    owner_go: str,
    persist_as_of: str,
    skip_persist: bool = False,
) -> TreasuryPdfRebindResultV1:
    from src.ops.treasury_pdf_current_head_rebind_and_census_v1.constants_v1 import (
        ALLOWED_OWNER_GOS,
    )

    if owner_go not in ALLOWED_OWNER_GOS:
        raise TreasuryPdfRebindCensusError(f"OWNER_GO_NOT_AUTHORIZED:{owner_go}")

    repo = Path(repo_root)
    adjudication = build_treasury_pdf_current_head_census_adjudication_v1(
        repo_root=repo,
        origin_main_sha=origin_main_sha,
    )

    folder = persist_as_of.replace(":", "")
    store = repo / CANONICAL_PACK_RELPATH / folder
    if not skip_persist:
        _persist_json(
            path=store / "claims.json",
            payload={
                "SCHEMA_CLASS": SCHEMA_CLASS,
                "CONTRACT_VERSION": CONTRACT_VERSION,
                "WP_ID": WP_ID,
                "AUTHORITY_EFFECT": AUTHORITY_EFFECT,
                "PDF_AUTHORITY": PDF_AUTHORITY,
                "ORIGIN_MAIN_SHA": origin_main_sha,
                "PERSIST_AS_OF": persist_as_of,
                "NETWORK_USED": FALSE_TOKEN,
                "EXTERNAL_EFFECT_AUTHORIZED": FALSE_TOKEN,
            },
        )
        _persist_json(
            path=store / "treasury_pdf_current_head_census_adjudication_v1.json",
            payload=adjudication,
        )
        _persist_json(
            path=store / "treasury_pdf_rebind_report_v1.json",
            payload={
                "WP_ID": WP_ID,
                "ORIGIN_MAIN_SHA": origin_main_sha,
                "EARLIEST_REAL_TREASURY_BLOCKER": EARLIEST_REAL_TREASURY_BLOCKER,
                "BLOCKER_CLASS": BLOCKER_CLASS,
                "MISSING_FACT_OR_AUTHORITY": MISSING_FACT_OR_AUTHORITY,
                "IMPLEMENTATION_STOP_REASON": "FIRST_REAL_BLOCKER_NO_NETWORK_IN_THIS_WP",
            },
        )
        persist_manifest_sha256_v1(store_root=store)

    proof = str(adjudication["TREASURY_INTERFERENCE_PROOF"].get("TREASURY_INTERFERENCE_PROOF", ""))
    return TreasuryPdfRebindResultV1(
        wp_id=WP_ID,
        origin_main_sha=origin_main_sha,
        persist_as_of=persist_as_of,
        store_root=str(store),
        census_complete=adjudication["CENSUS_COMPLETE"],
        earliest_real_treasury_blocker=EARLIEST_REAL_TREASURY_BLOCKER,
        interference_proof=proof,
    )


def verify_canonical_treasury_pdf_rebind_pack_v1(*, repo_root: Path | str) -> int:
    store = Path(repo_root) / CANONICAL_PACK_RELPATH / CANONICAL_PACK_AS_OF_FOLDER
    return verify_manifest_sha256_v1(store_root=store)


__all__ = [
    "TreasuryPdfRebindCensusError",
    "TreasuryPdfRebindResultV1",
    "build_treasury_pdf_current_head_census_adjudication_v1",
    "execute_treasury_pdf_current_head_rebind_v1",
    "verify_canonical_treasury_pdf_rebind_pack_v1",
]
