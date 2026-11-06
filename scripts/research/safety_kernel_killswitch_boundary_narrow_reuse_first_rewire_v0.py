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
    SafetyMode,
    TradingGate,
)
from trading.master_v2.double_play_state import SideState
from trading.master_v2.integrated_vs_scenario_replay_full_system_parity_harness_v0 import (
    assert_killswitch_boundary_non_authority_boundary_v0,
    assert_safety_kernel_non_authority_boundary_v0,
    canonical_owner_refs_v0,
    extract_killswitch_boundary_parity_envelope_v0,
    extract_safety_kernel_parity_envelope_v0,
)
from trading.master_v2.killswitch_boundary_backtest_state_file_binding_adapter_v0 import (
    KILLSWITCH_BOUNDARY_BACKTEST_STATE_FILE_BINDING_ADAPTER_OWNER,
)
from trading.master_v2.killswitch_boundary_offline_replay_binding_adapter_v0 import (
    KILLSWITCH_BOUNDARY_EFFECT_BOUND_OFFLINE,
    KILLSWITCH_BOUNDARY_OFFLINE_REPLAY_BINDING_ADAPTER_OWNER,
    KILLSWITCH_FENCING_OWNER,
    KillSwitchBoundaryMode,
    KillSwitchBoundaryOfflineReplayContextV0,
    evaluate_scenario_killswitch_boundary_v0,
    killswitch_boundary_binding_non_authority_boundary_ok_v0,
    system_economic_evidence_admissible_v0 as killswitch_system_economic_evidence_admissible_v0,
)
from trading.master_v2.offline_double_play_scenario_replay_v0 import SYNTHETIC_FUTURES_INSTRUMENT
from trading.master_v2.safety_kernel_boundary_backtest_state_file_binding_adapter_v0 import (
    SAFETY_KERNEL_BOUNDARY_BACKTEST_STATE_FILE_BINDING_ADAPTER_OWNER,
)
from trading.master_v2.safety_kernel_offline_replay_binding_adapter_v0 import (
    RUNTIME_ELIGIBILITY_OWNER,
    SAFETY_BOUNDARY_EFFECT_BOUND_OFFLINE,
    SAFETY_KERNEL_OFFLINE_REPLAY_BINDING_ADAPTER_OWNER,
    SafetyKernelOfflineReplayContextV0,
    evaluate_scenario_safety_kernel_v0,
    safety_kernel_binding_non_authority_boundary_ok_v0,
    system_economic_evidence_admissible_v0 as safety_kernel_system_economic_evidence_admissible_v0,
)

SURFACE_ID = "safety_kernel_and_killswitch_boundary"
PLAN_TYPE = "NARROW_REUSE_FIRST_REWIRE"
TRACE_ASSERTION_SOURCE_PR = 5012
REWIRE_STATE = "REWIRE_BOUND_OFFLINE_PARITY_PATH"

REUSED_RUNTIME_ELIGIBILITY_OWNER = RUNTIME_ELIGIBILITY_OWNER
REUSED_KILLSWITCH_FENCING_OWNER = KILLSWITCH_FENCING_OWNER
REUSED_SAFETY_KERNEL_OFFLINE_REPLAY_ADAPTER_OWNER = (
    SAFETY_KERNEL_OFFLINE_REPLAY_BINDING_ADAPTER_OWNER
)
REUSED_KILLSWITCH_BOUNDARY_OFFLINE_REPLAY_ADAPTER_OWNER = (
    KILLSWITCH_BOUNDARY_OFFLINE_REPLAY_BINDING_ADAPTER_OWNER
)
REUSED_SAFETY_KERNEL_BOUNDARY_BACKTEST_ADAPTER_OWNER = (
    SAFETY_KERNEL_BOUNDARY_BACKTEST_STATE_FILE_BINDING_ADAPTER_OWNER
)
REUSED_KILLSWITCH_BOUNDARY_BACKTEST_ADAPTER_OWNER = (
    KILLSWITCH_BOUNDARY_BACKTEST_STATE_FILE_BINDING_ADAPTER_OWNER
)

RUNTIME_ELIGIBILITY_PATH = "src/meta/learning_loop/runtime_eligibility_v1.py"
KILLSWITCH_FENCING_PATH = (
    "src/meta/learning_loop/killswitch_writer_fencing_and_independent_read_paths_v1.py"
)
SAFETY_KERNEL_OFFLINE_REPLAY_ADAPTER_PATH = (
    "src/trading/master_v2/safety_kernel_offline_replay_binding_adapter_v0.py"
)
KILLSWITCH_BOUNDARY_OFFLINE_REPLAY_ADAPTER_PATH = (
    "src/trading/master_v2/killswitch_boundary_offline_replay_binding_adapter_v0.py"
)
SAFETY_KERNEL_BOUNDARY_BACKTEST_ADAPTER_PATH = (
    "src/trading/master_v2/safety_kernel_boundary_backtest_state_file_binding_adapter_v0.py"
)
KILLSWITCH_BOUNDARY_BACKTEST_ADAPTER_PATH = (
    "src/trading/master_v2/killswitch_boundary_backtest_state_file_binding_adapter_v0.py"
)
HARNESS_PATH = (
    "src/trading/master_v2/integrated_vs_scenario_replay_full_system_parity_harness_v0.py"
)
OFFLINE_REPLAY_PATH = "src/trading/master_v2/offline_double_play_scenario_replay_v0.py"
SAFETY_KERNEL_OFFLINE_REPLAY_CONTRACT_TEST_PATH = (
    "tests/trading/master_v2/test_safety_kernel_offline_replay_binding_parity_rewire_contract_v0.py"
)
KILLSWITCH_BOUNDARY_OFFLINE_REPLAY_CONTRACT_TEST_PATH = "tests/trading/master_v2/test_killswitch_boundary_offline_replay_binding_parity_rewire_contract_v0.py"
KILLSWITCH_BOUNDARY_BACKTEST_CONTRACT_TEST_PATH = (
    "tests/trading/master_v2/test_killswitch_boundary_backtest_state_file_binding_contract_v0.py"
)
CHAINED_CONTRACT_TEST_PATH = (
    "tests/research/test_safety_kernel_killswitch_boundary_narrow_reuse_first_rewire_v0.py"
)
OWNER_BOUND_PATHS = (
    RUNTIME_ELIGIBILITY_PATH,
    KILLSWITCH_FENCING_PATH,
    SAFETY_KERNEL_OFFLINE_REPLAY_ADAPTER_PATH,
    KILLSWITCH_BOUNDARY_OFFLINE_REPLAY_ADAPTER_PATH,
    SAFETY_KERNEL_BOUNDARY_BACKTEST_ADAPTER_PATH,
    KILLSWITCH_BOUNDARY_BACKTEST_ADAPTER_PATH,
    HARNESS_PATH,
    OFFLINE_REPLAY_PATH,
    SAFETY_KERNEL_OFFLINE_REPLAY_CONTRACT_TEST_PATH,
    KILLSWITCH_BOUNDARY_OFFLINE_REPLAY_CONTRACT_TEST_PATH,
    KILLSWITCH_BOUNDARY_BACKTEST_CONTRACT_TEST_PATH,
    CHAINED_CONTRACT_TEST_PATH,
)


@dataclass(frozen=True)
class SafetyKernelKillswitchFixtureResultV0:
    safety_binding: Any
    killswitch_binding: Any


@dataclass(frozen=True)
class RewireBinding:
    surface_id: str
    reused_runtime_eligibility_owner: str
    reused_killswitch_fencing_owner: str
    reused_safety_kernel_offline_replay_adapter_owner: str
    reused_killswitch_boundary_offline_replay_adapter_owner: str
    reused_safety_kernel_boundary_backtest_adapter_owner: str
    reused_killswitch_boundary_backtest_adapter_owner: str
    runtime_eligibility_path: str
    killswitch_fencing_path: str
    safety_kernel_offline_replay_adapter_path: str
    killswitch_boundary_offline_replay_adapter_path: str
    safety_kernel_boundary_backtest_adapter_path: str
    killswitch_boundary_backtest_adapter_path: str
    harness_path: str
    offline_replay_path: str
    safety_kernel_offline_replay_contract_test_path: str
    killswitch_boundary_offline_replay_contract_test_path: str
    killswitch_boundary_backtest_contract_test_path: str
    chained_contract_test_path: str
    capital_risk_sizing_chain_preserved: bool
    safety_boundary_effect: str
    killswitch_boundary_effect: str
    kill_switch_boundary_semantics_represented: bool
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
    if refs["runtime_eligibility"] != REUSED_RUNTIME_ELIGIBILITY_OWNER:
        raise ValueError("runtime eligibility owner drift")
    if refs["killswitch_fencing"] != REUSED_KILLSWITCH_FENCING_OWNER:
        raise ValueError("killswitch fencing owner drift")
    if (
        refs["safety_kernel_offline_replay_binding_adapter"]
        != REUSED_SAFETY_KERNEL_OFFLINE_REPLAY_ADAPTER_OWNER
    ):
        raise ValueError("safety kernel offline replay adapter owner drift")
    if (
        refs["killswitch_boundary_offline_replay_binding_adapter"]
        != REUSED_KILLSWITCH_BOUNDARY_OFFLINE_REPLAY_ADAPTER_OWNER
    ):
        raise ValueError("killswitch boundary offline replay adapter owner drift")


def evaluate_safety_kernel_killswitch_boundary_parity_fixtures_v0(
    *,
    instrument_id: str = SYNTHETIC_FUTURES_INSTRUMENT,
    trading_epoch: int = 48,
    context_reference: str = "safety-kernel-killswitch-boundary-narrow-rewire-v0",
) -> SafetyKernelKillswitchFixtureResultV0:
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
    safety_binding = evaluate_scenario_safety_kernel_v0(
        evidence,
        context=SafetyKernelOfflineReplayContextV0(
            killswitch_blocked=True,
            safety_decision_allowed=False,
            safety_mode=SafetyMode.BLOCKED,
            trading_gate=TradingGate.BLOCKED,
        ),
    )
    safety_envelope = extract_safety_kernel_parity_envelope_v0(
        safety_binding,
        decision_outcome=DecisionOutcome.ENTER_LONG.value,
        composition_result_id=f"{context_reference}-composition",
    )
    assert_safety_kernel_non_authority_boundary_v0(safety_envelope)
    if not safety_kernel_binding_non_authority_boundary_ok_v0(safety_binding):
        raise ValueError("safety kernel binding violated non-authority boundary")
    if safety_binding.safety_boundary_effect != SAFETY_BOUNDARY_EFFECT_BOUND_OFFLINE:
        raise ValueError("safety kernel fixture must remain offline-bound only")
    if safety_kernel_system_economic_evidence_admissible_v0(safety_binding):
        raise ValueError("system economic evidence must remain inadmissible")

    killswitch_binding = evaluate_scenario_killswitch_boundary_v0(
        safety_binding.evidence,
        context=KillSwitchBoundaryOfflineReplayContextV0(
            boundary_mode=KillSwitchBoundaryMode.EMERGENCY_FLATTEN,
            killswitch_active=True,
            prior_killswitch_active=True,
            side_state=SideState.KILL_ALL,
            safety_mode=SafetyMode.BLOCKED,
            trading_gate=TradingGate.BLOCKED,
            safety_decision_allowed=False,
        ),
    )
    killswitch_envelope = extract_killswitch_boundary_parity_envelope_v0(
        killswitch_binding,
        decision_outcome=DecisionOutcome.ENTER_LONG.value,
        composition_result_id=f"{context_reference}-composition",
    )
    assert_killswitch_boundary_non_authority_boundary_v0(killswitch_envelope)
    if not killswitch_boundary_binding_non_authority_boundary_ok_v0(killswitch_binding):
        raise ValueError("killswitch boundary binding violated non-authority boundary")
    if killswitch_binding.killswitch_boundary_effect != KILLSWITCH_BOUNDARY_EFFECT_BOUND_OFFLINE:
        raise ValueError("killswitch boundary fixture must remain offline-bound only")
    if killswitch_system_economic_evidence_admissible_v0(killswitch_binding):
        raise ValueError("system economic evidence must remain inadmissible")

    return SafetyKernelKillswitchFixtureResultV0(
        safety_binding=safety_binding,
        killswitch_binding=killswitch_binding,
    )


def build_rewire_binding(repo_root: Path) -> dict[str, Any]:
    _assert_owner_bound_paths_exist(repo_root)
    _assert_canonical_owner_reuse()
    fixture = evaluate_safety_kernel_killswitch_boundary_parity_fixtures_v0()
    binding = RewireBinding(
        surface_id=SURFACE_ID,
        reused_runtime_eligibility_owner=REUSED_RUNTIME_ELIGIBILITY_OWNER,
        reused_killswitch_fencing_owner=REUSED_KILLSWITCH_FENCING_OWNER,
        reused_safety_kernel_offline_replay_adapter_owner=(
            REUSED_SAFETY_KERNEL_OFFLINE_REPLAY_ADAPTER_OWNER
        ),
        reused_killswitch_boundary_offline_replay_adapter_owner=(
            REUSED_KILLSWITCH_BOUNDARY_OFFLINE_REPLAY_ADAPTER_OWNER
        ),
        reused_safety_kernel_boundary_backtest_adapter_owner=(
            REUSED_SAFETY_KERNEL_BOUNDARY_BACKTEST_ADAPTER_OWNER
        ),
        reused_killswitch_boundary_backtest_adapter_owner=(
            REUSED_KILLSWITCH_BOUNDARY_BACKTEST_ADAPTER_OWNER
        ),
        runtime_eligibility_path=RUNTIME_ELIGIBILITY_PATH,
        killswitch_fencing_path=KILLSWITCH_FENCING_PATH,
        safety_kernel_offline_replay_adapter_path=SAFETY_KERNEL_OFFLINE_REPLAY_ADAPTER_PATH,
        killswitch_boundary_offline_replay_adapter_path=(
            KILLSWITCH_BOUNDARY_OFFLINE_REPLAY_ADAPTER_PATH
        ),
        safety_kernel_boundary_backtest_adapter_path=SAFETY_KERNEL_BOUNDARY_BACKTEST_ADAPTER_PATH,
        killswitch_boundary_backtest_adapter_path=KILLSWITCH_BOUNDARY_BACKTEST_ADAPTER_PATH,
        harness_path=HARNESS_PATH,
        offline_replay_path=OFFLINE_REPLAY_PATH,
        safety_kernel_offline_replay_contract_test_path=(
            SAFETY_KERNEL_OFFLINE_REPLAY_CONTRACT_TEST_PATH
        ),
        killswitch_boundary_offline_replay_contract_test_path=(
            KILLSWITCH_BOUNDARY_OFFLINE_REPLAY_CONTRACT_TEST_PATH
        ),
        killswitch_boundary_backtest_contract_test_path=(
            KILLSWITCH_BOUNDARY_BACKTEST_CONTRACT_TEST_PATH
        ),
        chained_contract_test_path=CHAINED_CONTRACT_TEST_PATH,
        capital_risk_sizing_chain_preserved=True,
        safety_boundary_effect=fixture.safety_binding.safety_boundary_effect,
        killswitch_boundary_effect=fixture.killswitch_binding.killswitch_boundary_effect,
        kill_switch_boundary_semantics_represented=(
            fixture.killswitch_binding.boundary.emergency_flatten_boundary_only
            and fixture.killswitch_binding.boundary.block_new_entry
        ),
        rewire_state=REWIRE_STATE,
        functional_rewire_performed=True,
        new_parallel_owner_created=False,
    )
    return {
        "schema": "SafetyKernelKillswitchBoundaryNarrowReuseFirstRewireV1",
        "surface_id": SURFACE_ID,
        "plan_type": PLAN_TYPE,
        "trace_assertion_source_pr": TRACE_ASSERTION_SOURCE_PR,
        "rewire_scope": "safety_kernel_and_killswitch_boundary_only",
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
        "# Safety Kernel KillSwitch Boundary Narrow Reuse-First Rewire V1",
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
        f"- reused_runtime_eligibility_owner: `{binding['reused_runtime_eligibility_owner']}`",
        f"- reused_killswitch_fencing_owner: `{binding['reused_killswitch_fencing_owner']}`",
        f"- reused_safety_kernel_offline_replay_adapter_owner: `{binding['reused_safety_kernel_offline_replay_adapter_owner']}`",
        f"- reused_killswitch_boundary_offline_replay_adapter_owner: `{binding['reused_killswitch_boundary_offline_replay_adapter_owner']}`",
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
    (output_dir / "safety_kernel_killswitch_boundary_narrow_reuse_first_rewire_v0.json").write_text(
        json.dumps(rewire, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_dir / "safety_kernel_killswitch_boundary_narrow_reuse_first_rewire_v0.md").write_text(
        render_markdown(rewire) + "\n",
        encoding="utf-8",
    )
    verdict = "PASS_SAFETY_KERNEL_KILLSWITCH_BOUNDARY_NARROW_REUSE_FIRST_REWIRE_BOUND"
    (output_dir / "verdict.txt").write_text(verdict + "\n", encoding="utf-8")
    manifest_rc = write_manifest(output_dir)
    (output_dir / "manifest_verify_rc.txt").write_text(f"{manifest_rc}\n", encoding="utf-8")
    manifest_rc = write_manifest(output_dir)
    print(verdict)
    print(f"REUSED_RUNTIME_ELIGIBILITY_OWNER={REUSED_RUNTIME_ELIGIBILITY_OWNER}")
    print(f"REUSED_KILLSWITCH_FENCING_OWNER={REUSED_KILLSWITCH_FENCING_OWNER}")
    print("FUNCTIONAL_REWIRE_PERFORMED=true")
    print(f"MANIFEST_VERIFY_RC={manifest_rc}")
    print(f"EVIDENCE_DIR={output_dir}")
    return 0 if manifest_rc == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
