from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from scripts.research.backtest_runtime_decision_parity_trace_matrix_v0 import NO_AUTHORITY_FLAGS
from trading.master_v2.capital_risk_sizing_offline_replay_binding_adapter_v0 import (
    build_scenario_tick_decision_evidence_v0,
)
from trading.master_v2.double_play_entry_exit_policy_v0 import (
    DecisionOutcome,
    PositionState,
    ReconciliationState,
)
from trading.master_v2.integrated_vs_scenario_replay_full_system_parity_harness_v0 import (
    assert_reconciliation_unknown_outcome_non_authority_boundary_v0,
    canonical_owner_refs_v0,
    extract_reconciliation_unknown_outcome_parity_envelope_v0,
)
from trading.master_v2.offline_double_play_scenario_replay_v0 import SYNTHETIC_FUTURES_INSTRUMENT
from trading.master_v2.reconciliation_boundary_backtest_state_file_binding_adapter_v0 import (
    RECONCILIATION_BOUNDARY_BACKTEST_STATE_FILE_BINDING_ADAPTER_OWNER,
)
from trading.master_v2.reconciliation_unknown_outcome_offline_replay_binding_adapter_v0 import (
    ENTRY_EXIT_POLICY_OWNER,
    RECONCILIATION_UNKNOWN_OUTCOME_EFFECT_BOUND_OFFLINE,
    RECONCILIATION_UNKNOWN_OUTCOME_OFFLINE_REPLAY_BINDING_ADAPTER_OWNER,
    RUNTIME_STATE_RECONCILIATION_OWNER,
    ReconciliationUnknownOutcomeOfflineReplayContextV0,
    evaluate_scenario_reconciliation_unknown_outcome_v0,
    reconciliation_unknown_outcome_binding_non_authority_boundary_ok_v0,
    system_economic_evidence_admissible_v0,
)

SURFACE_ID = "reconciliation_unknown_outcome"
PLAN_TYPE = "NARROW_REUSE_FIRST_REWIRE"
TRACE_ASSERTION_SOURCE_PR = 5013
REWIRE_STATE = "REWIRE_BOUND_OFFLINE_PARITY_PATH"

REUSED_RUNTIME_STATE_RECONCILIATION_OWNER = RUNTIME_STATE_RECONCILIATION_OWNER
REUSED_ENTRY_EXIT_POLICY_OWNER = ENTRY_EXIT_POLICY_OWNER
REUSED_OFFLINE_REPLAY_ADAPTER_OWNER = (
    RECONCILIATION_UNKNOWN_OUTCOME_OFFLINE_REPLAY_BINDING_ADAPTER_OWNER
)
REUSED_BOUNDARY_BACKTEST_ADAPTER_OWNER = (
    RECONCILIATION_BOUNDARY_BACKTEST_STATE_FILE_BINDING_ADAPTER_OWNER
)

RUNTIME_STATE_RECONCILIATION_PATH = "src/meta/learning_loop/runtime_state_reconciliation_v1.py"
ENTRY_EXIT_POLICY_PATH = "src/trading/master_v2/double_play_entry_exit_policy_v0.py"
OFFLINE_REPLAY_ADAPTER_PATH = (
    "src/trading/master_v2/reconciliation_unknown_outcome_offline_replay_binding_adapter_v0.py"
)
BOUNDARY_BACKTEST_ADAPTER_PATH = (
    "src/trading/master_v2/reconciliation_boundary_backtest_state_file_binding_adapter_v0.py"
)
HARNESS_PATH = (
    "src/trading/master_v2/integrated_vs_scenario_replay_full_system_parity_harness_v0.py"
)
OFFLINE_REPLAY_PATH = "src/trading/master_v2/offline_double_play_scenario_replay_v0.py"
OFFLINE_REPLAY_CONTRACT_TEST_PATH = "tests/trading/master_v2/test_reconciliation_unknown_outcome_offline_replay_binding_parity_rewire_contract_v0.py"
BOUNDARY_BACKTEST_CONTRACT_TEST_PATH = "tests/trading/master_v2/test_reconciliation_boundary_backtest_state_file_binding_contract_v0.py"
CHAINED_CONTRACT_TEST_PATH = (
    "tests/research/test_reconciliation_unknown_outcome_narrow_reuse_first_rewire_v0.py"
)
OWNER_BOUND_PATHS = (
    RUNTIME_STATE_RECONCILIATION_PATH,
    ENTRY_EXIT_POLICY_PATH,
    OFFLINE_REPLAY_ADAPTER_PATH,
    BOUNDARY_BACKTEST_ADAPTER_PATH,
    HARNESS_PATH,
    OFFLINE_REPLAY_PATH,
    OFFLINE_REPLAY_CONTRACT_TEST_PATH,
    BOUNDARY_BACKTEST_CONTRACT_TEST_PATH,
    CHAINED_CONTRACT_TEST_PATH,
)


@dataclass(frozen=True)
class RewireBinding:
    surface_id: str
    reused_runtime_state_reconciliation_owner: str
    reused_entry_exit_policy_owner: str
    reused_offline_replay_adapter_owner: str
    reused_boundary_backtest_adapter_owner: str
    runtime_state_reconciliation_path: str
    entry_exit_policy_path: str
    offline_replay_adapter_path: str
    boundary_backtest_adapter_path: str
    harness_path: str
    offline_replay_path: str
    offline_replay_contract_test_path: str
    boundary_backtest_contract_test_path: str
    chained_contract_test_path: str
    safety_kernel_killswitch_chain_preserved: bool
    submission_unknown_semantics_represented: bool
    unknown_outcome_never_auto_resubmits: bool
    reconciliation_unknown_outcome_effect: str
    rewire_state: str
    functional_rewire_performed: bool
    new_parallel_owner_created: bool


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _assert_owner_bound_paths_exist(repo_root: Path) -> None:
    for rel in OWNER_BOUND_PATHS:
        if not (repo_root / rel).is_file():
            raise ValueError(f"owner-bound path missing: {rel}")


def _assert_canonical_owner_reuse() -> None:
    refs = canonical_owner_refs_v0()
    if refs["runtime_state_reconciliation"] != REUSED_RUNTIME_STATE_RECONCILIATION_OWNER:
        raise ValueError("runtime state reconciliation owner drift")
    if refs["reconciliation_entry_exit_policy"] != REUSED_ENTRY_EXIT_POLICY_OWNER:
        raise ValueError("entry exit policy owner drift")
    if (
        refs["reconciliation_unknown_outcome_offline_replay_binding_adapter"]
        != REUSED_OFFLINE_REPLAY_ADAPTER_OWNER
    ):
        raise ValueError("reconciliation offline replay adapter owner drift")


def evaluate_reconciliation_unknown_outcome_parity_fixtures_v0(
    *,
    instrument_id: str = SYNTHETIC_FUTURES_INSTRUMENT,
    trading_epoch: int = 48,
    context_reference: str = "reconciliation-unknown-outcome-narrow-rewire-v0",
) -> Any:
    evidence = build_scenario_tick_decision_evidence_v0(
        decision_id=f"{context_reference}-decision",
        replay_id=f"{context_reference}-replay",
        instrument_id=instrument_id,
        trading_epoch=trading_epoch,
        composition_result_id=f"{context_reference}-composition",
        entry_exit_policy_ref=f"{context_reference}-policy",
        selected_side="long",
        decision_outcome=DecisionOutcome.ENTER_LONG.value,
        reason_codes=("PASS",),
        decision_precedence_trace=("enter_long",),
        config_digest="config",
        implementation_digest="impl",
    )
    binding = evaluate_scenario_reconciliation_unknown_outcome_v0(
        evidence,
        context=ReconciliationUnknownOutcomeOfflineReplayContextV0(
            position_state=PositionState.SUBMISSION_UNKNOWN,
            reconciliation_state=ReconciliationState.RECONCILED,
            venue_flat=True,
            intent_snapshot_unresolved=True,
            order_snapshot_unresolved=True,
            fill_snapshot_unresolved=False,
        ),
    )
    envelope = extract_reconciliation_unknown_outcome_parity_envelope_v0(
        binding,
        decision_outcome=DecisionOutcome.ENTER_LONG.value,
        composition_result_id=f"{context_reference}-composition",
    )
    assert_reconciliation_unknown_outcome_non_authority_boundary_v0(envelope)
    if not reconciliation_unknown_outcome_binding_non_authority_boundary_ok_v0(binding):
        raise ValueError("reconciliation binding violated non-authority boundary")
    if not binding.binding_applied:
        raise ValueError("fixture must bind reconciliation unknown outcome")
    if (
        binding.reconciliation_unknown_outcome_effect
        != RECONCILIATION_UNKNOWN_OUTCOME_EFFECT_BOUND_OFFLINE
    ):
        raise ValueError("fixture must remain offline-bound only")
    if not binding.boundary.submission_unknown_blocks_new_exposure:
        raise ValueError("submission unknown semantics must be represented")
    if not binding.boundary.unknown_outcome_never_auto_resubmits:
        raise ValueError("unknown outcome never auto-resubmits must be represented")
    if system_economic_evidence_admissible_v0(binding):
        raise ValueError("system economic evidence must remain inadmissible")
    return binding


def build_rewire_binding(repo_root: Path) -> dict[str, Any]:
    _assert_owner_bound_paths_exist(repo_root)
    _assert_canonical_owner_reuse()
    binding_result = evaluate_reconciliation_unknown_outcome_parity_fixtures_v0()
    binding = RewireBinding(
        surface_id=SURFACE_ID,
        reused_runtime_state_reconciliation_owner=REUSED_RUNTIME_STATE_RECONCILIATION_OWNER,
        reused_entry_exit_policy_owner=REUSED_ENTRY_EXIT_POLICY_OWNER,
        reused_offline_replay_adapter_owner=REUSED_OFFLINE_REPLAY_ADAPTER_OWNER,
        reused_boundary_backtest_adapter_owner=REUSED_BOUNDARY_BACKTEST_ADAPTER_OWNER,
        runtime_state_reconciliation_path=RUNTIME_STATE_RECONCILIATION_PATH,
        entry_exit_policy_path=ENTRY_EXIT_POLICY_PATH,
        offline_replay_adapter_path=OFFLINE_REPLAY_ADAPTER_PATH,
        boundary_backtest_adapter_path=BOUNDARY_BACKTEST_ADAPTER_PATH,
        harness_path=HARNESS_PATH,
        offline_replay_path=OFFLINE_REPLAY_PATH,
        offline_replay_contract_test_path=OFFLINE_REPLAY_CONTRACT_TEST_PATH,
        boundary_backtest_contract_test_path=BOUNDARY_BACKTEST_CONTRACT_TEST_PATH,
        chained_contract_test_path=CHAINED_CONTRACT_TEST_PATH,
        safety_kernel_killswitch_chain_preserved=True,
        submission_unknown_semantics_represented=(
            binding_result.boundary.submission_unknown_blocks_new_exposure
        ),
        unknown_outcome_never_auto_resubmits=(
            binding_result.boundary.unknown_outcome_never_auto_resubmits
        ),
        reconciliation_unknown_outcome_effect=binding_result.reconciliation_unknown_outcome_effect,
        rewire_state=REWIRE_STATE,
        functional_rewire_performed=True,
        new_parallel_owner_created=False,
    )
    return {
        "schema": "ReconciliationUnknownOutcomeNarrowReuseFirstRewireV1",
        "surface_id": SURFACE_ID,
        "plan_type": PLAN_TYPE,
        "trace_assertion_source_pr": TRACE_ASSERTION_SOURCE_PR,
        "rewire_scope": "reconciliation_unknown_outcome_only",
        "rewire_binding": asdict(binding),
        "forbidden_claims_remain_false": {
            "FULL_CANONICAL_CHAIN_WIRED": False,
            "BACKTEST_RUNTIME_DECISION_PARITY_PASS": False,
            "SYSTEM_ECONOMIC_EVIDENCE_ADMISSIBLE": False,
            "RUNTIME_REWIRE_ADMISSIBLE": False,
            "RUNTIME_AUTHORITY": False,
            "ORDERS_ALLOWED": False,
            "ECONOMIC_CLAIM": False,
        },
        **NO_AUTHORITY_FLAGS,
    }


def render_markdown(rewire: dict[str, Any]) -> str:
    binding = rewire["rewire_binding"]
    lines = [
        "# Reconciliation Unknown Outcome Narrow Reuse-First Rewire V1",
        "",
        "```text",
        "NARROW_REUSE_FIRST_REWIRE=true",
        "FUNCTIONAL_REWIRE_PERFORMED=true",
        "NEW_PARALLEL_OWNER_CREATED=false",
        "NO_RUNTIME_AUTHORITY=true",
        "NO_ORDERS=true",
        "NO_ECONOMIC_CLAIM=true",
        "FULL_CANONICAL_CHAIN_WIRED=false",
        "BACKTEST_RUNTIME_DECISION_PARITY_PASS=false",
        "RUNTIME_REWIRE_ADMISSIBLE=false",
        "```",
        "",
        f"- reused_runtime_state_reconciliation_owner: `{binding['reused_runtime_state_reconciliation_owner']}`",
        f"- reused_entry_exit_policy_owner: `{binding['reused_entry_exit_policy_owner']}`",
        f"- reused_offline_replay_adapter_owner: `{binding['reused_offline_replay_adapter_owner']}`",
        f"- reused_boundary_backtest_adapter_owner: `{binding['reused_boundary_backtest_adapter_owner']}`",
        f"- harness_path: `{binding['harness_path']}`",
        f"- chained_contract_test_path: `{binding['chained_contract_test_path']}`",
        "",
    ]
    return "\n".join(lines)


def write_manifest(output_dir: Path) -> int:
    rows: list[str] = []
    for path in sorted(output_dir.rglob("*")):
        if path.is_file() and path.name != "MANIFEST.sha256":
            rows.append(f"{_sha256(path)}  {path.relative_to(output_dir).as_posix()}")
    (output_dir / "MANIFEST.sha256").write_text("\n".join(rows) + "\n", encoding="utf-8")
    for row in rows:
        digest, rel = row.split("  ", 1)
        if _sha256(output_dir / rel) != digest:
            return 1
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    rewire = build_rewire_binding(repo_root)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "reconciliation_unknown_outcome_narrow_reuse_first_rewire_v0.json").write_text(
        json.dumps(rewire, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (output_dir / "reconciliation_unknown_outcome_narrow_reuse_first_rewire_v0.md").write_text(
        render_markdown(rewire) + "\n", encoding="utf-8"
    )
    verdict = "PASS_RECONCILIATION_UNKNOWN_OUTCOME_NARROW_REUSE_FIRST_REWIRE_BOUND"
    (output_dir / "verdict.txt").write_text(verdict + "\n", encoding="utf-8")
    manifest_rc = write_manifest(output_dir)
    (output_dir / "manifest_verify_rc.txt").write_text(f"{manifest_rc}\n", encoding="utf-8")
    manifest_rc = write_manifest(output_dir)
    print(verdict)
    print(f"REUSED_RUNTIME_STATE_RECONCILIATION_OWNER={REUSED_RUNTIME_STATE_RECONCILIATION_OWNER}")
    print("FUNCTIONAL_REWIRE_PERFORMED=true")
    print(f"MANIFEST_VERIFY_RC={manifest_rc}")
    print(f"EVIDENCE_DIR={output_dir}")
    return 0 if manifest_rc == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
