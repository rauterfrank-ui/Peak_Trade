from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from scripts.research.backtest_runtime_decision_parity_trace_matrix_v0 import NO_AUTHORITY_FLAGS
from trading.master_v2.deterministic_scope_event_generator_v1 import CanonicalScopeEventType
from trading.master_v2.double_play_entry_exit_policy_v0 import ExitClass
from trading.master_v2.integrated_vs_scenario_replay_full_system_parity_harness_v0 import (
    assert_reversal_preparation_non_authority_boundary_v0,
    assert_scope_event_non_authority_boundary_v0,
    canonical_owner_refs_v0,
    evaluate_scenario_reversal_preparation_for_fixture_v0,
    evaluate_scenario_scope_event_for_fixture_v0,
    extract_reversal_preparation_parity_envelope_v0,
    extract_scope_event_parity_envelope_v0,
)
from trading.master_v2.offline_double_play_scenario_replay_v0 import SYNTHETIC_FUTURES_INSTRUMENT
from trading.master_v2.double_play_entry_exit_scenario_binding_adapter_v0 import (
    CANONICAL_ENTRY_EXIT_POLICY_OWNER,
)
from trading.master_v2.reversal_preparation_scenario_binding_adapter_v0 import (
    REVERSAL_PREPARATION_SCENARIO_BINDING_ADAPTER_OWNER,
    reversal_preparation_binding_non_authority_boundary_ok_v0,
    reversal_preparation_decision_is_reduce_only_preparation_v0,
)
from trading.master_v2.scope_event_generator_scenario_binding_adapter_v0 import (
    CANONICAL_SCOPE_EVENT_GENERATOR_OWNER,
    SCOPE_EVENT_EFFECT_BOUND_OFFLINE,
    SCOPE_EVENT_GENERATOR_SCENARIO_BINDING_ADAPTER_OWNER,
    scope_event_binding_non_authority_boundary_ok_v0,
)

SURFACE_ID = "scope_adverse_exit_and_reversal_preparation"
PLAN_TYPE = "NARROW_REUSE_FIRST_REWIRE"
TRACE_ASSERTION_SOURCE_PR = 5007
REWIRE_STATE = "REWIRE_BOUND_OFFLINE_PARITY_PATH"

REUSED_SCOPE_CANONICAL_OWNER = CANONICAL_SCOPE_EVENT_GENERATOR_OWNER
REUSED_SCOPE_ADAPTER_OWNER = SCOPE_EVENT_GENERATOR_SCENARIO_BINDING_ADAPTER_OWNER
REUSED_REVERSAL_CANONICAL_OWNER = CANONICAL_ENTRY_EXIT_POLICY_OWNER
REUSED_REVERSAL_ADAPTER_OWNER = REVERSAL_PREPARATION_SCENARIO_BINDING_ADAPTER_OWNER
SCOPE_CANONICAL_OWNER_PATH = "src/trading/master_v2/deterministic_scope_event_generator_v1.py"
SCOPE_ADAPTER_PATH = "src/trading/master_v2/scope_event_generator_scenario_binding_adapter_v0.py"
REVERSAL_ADAPTER_PATH = "src/trading/master_v2/reversal_preparation_scenario_binding_adapter_v0.py"
HARNESS_PATH = (
    "src/trading/master_v2/integrated_vs_scenario_replay_full_system_parity_harness_v0.py"
)
OFFLINE_REPLAY_PATH = "src/trading/master_v2/offline_double_play_scenario_replay_v0.py"
SCOPE_CONTRACT_TEST_PATH = "tests/trading/master_v2/test_scope_event_generator_scenario_replay_binding_parity_rewire_contract_v0.py"
REVERSAL_CONTRACT_TEST_PATH = "tests/trading/master_v2/test_reversal_preparation_scenario_replay_binding_parity_rewire_contract_v0.py"
OWNER_BOUND_PATHS = (
    SCOPE_CANONICAL_OWNER_PATH,
    SCOPE_ADAPTER_PATH,
    REVERSAL_ADAPTER_PATH,
    HARNESS_PATH,
    OFFLINE_REPLAY_PATH,
    SCOPE_CONTRACT_TEST_PATH,
    REVERSAL_CONTRACT_TEST_PATH,
)


@dataclass(frozen=True)
class RewireBinding:
    surface_id: str
    reused_scope_canonical_owner: str
    reused_scope_adapter_owner: str
    reused_reversal_canonical_owner: str
    reused_reversal_adapter_owner: str
    scope_canonical_owner_path: str
    scope_adapter_path: str
    reversal_adapter_path: str
    harness_path: str
    offline_replay_path: str
    scope_contract_test_path: str
    reversal_contract_test_path: str
    adverse_scope_event_type: str
    adverse_exit_signal_triggered: bool
    reversal_preparation_exit_class: str
    reversal_preparation_reduce_only: bool
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
    if refs["scope_event_generator"] != REUSED_SCOPE_CANONICAL_OWNER:
        raise ValueError("scope event generator owner drift")
    if refs["scope_event_generator_scenario_binding_adapter"] != REUSED_SCOPE_ADAPTER_OWNER:
        raise ValueError("scope adapter owner drift")
    if refs["reversal_preparation_scenario_binding_adapter"] != REUSED_REVERSAL_ADAPTER_OWNER:
        raise ValueError("reversal preparation adapter owner drift")


def evaluate_scope_adverse_exit_and_reversal_parity_fixtures_v0(
    *,
    instrument_id: str = SYNTHETIC_FUTURES_INSTRUMENT,
    trading_epoch: int = 48,
    context_reference: str = "scope-reversal-narrow-rewire-v0",
) -> tuple[Any, Any]:
    scope_binding = evaluate_scenario_scope_event_for_fixture_v0(
        instrument_id=instrument_id,
        trading_epoch=trading_epoch,
        context_reference=f"{context_reference}-scope",
    )
    scope_env = extract_scope_event_parity_envelope_v0(scope_binding)
    assert_scope_event_non_authority_boundary_v0(scope_env)
    if not scope_event_binding_non_authority_boundary_ok_v0(scope_binding):
        raise ValueError("scope event binding violated non-authority boundary")
    if scope_binding.scope_event_effect != SCOPE_EVENT_EFFECT_BOUND_OFFLINE:
        raise ValueError("scope event effect must remain offline-bound")
    if not scope_binding.scope_adverse_exit_signal.triggered:
        raise ValueError("adverse exit signal must be triggered in fixture")
    _matched = scope_binding.scope_event_evidence.matched_conditions
    if "adverse_exit" not in _matched:
        raise ValueError("adverse scope fixture must match adverse_exit condition")
    _etype = scope_binding.scope_event_evidence.event_type
    if _etype not in (
        CanonicalScopeEventType.ADVERSE_EXIT_CANDIDATE,
        CanonicalScopeEventType.DOWNSCOPE_CANDIDATE,
        CanonicalScopeEventType.DOWNSCOPE_CONFIRMED,
    ):
        raise ValueError(
            "adverse scope fixture must keep adverse dimension "
            "(ADVERSE_EXIT_CANDIDATE or nested DOWNSCOPE_*)"
        )

    reversal_decision = evaluate_scenario_reversal_preparation_for_fixture_v0(
        instrument_id=instrument_id,
        trading_epoch=trading_epoch,
        context_reference=f"{context_reference}-reversal",
    )
    reversal_env = extract_reversal_preparation_parity_envelope_v0(reversal_decision)
    assert_reversal_preparation_non_authority_boundary_v0(reversal_env)
    if not reversal_preparation_binding_non_authority_boundary_ok_v0(reversal_decision):
        raise ValueError("reversal preparation binding violated non-authority boundary")
    if reversal_decision.exit_class is not ExitClass.REVERSAL_PREPARATION_EXIT:
        raise ValueError("reversal fixture must reach REVERSAL_PREPARATION_EXIT")
    if not reversal_preparation_decision_is_reduce_only_preparation_v0(reversal_decision):
        raise ValueError("reversal preparation must remain reduce-only preparation")

    return scope_binding, reversal_decision


def build_rewire_binding(repo_root: Path) -> dict[str, Any]:
    _assert_owner_bound_paths_exist(repo_root)
    _assert_canonical_owner_reuse()
    scope_binding, reversal_decision = evaluate_scope_adverse_exit_and_reversal_parity_fixtures_v0()
    binding = RewireBinding(
        surface_id=SURFACE_ID,
        reused_scope_canonical_owner=REUSED_SCOPE_CANONICAL_OWNER,
        reused_scope_adapter_owner=REUSED_SCOPE_ADAPTER_OWNER,
        reused_reversal_canonical_owner=REUSED_REVERSAL_CANONICAL_OWNER,
        reused_reversal_adapter_owner=REUSED_REVERSAL_ADAPTER_OWNER,
        scope_canonical_owner_path=SCOPE_CANONICAL_OWNER_PATH,
        scope_adapter_path=SCOPE_ADAPTER_PATH,
        reversal_adapter_path=REVERSAL_ADAPTER_PATH,
        harness_path=HARNESS_PATH,
        offline_replay_path=OFFLINE_REPLAY_PATH,
        scope_contract_test_path=SCOPE_CONTRACT_TEST_PATH,
        reversal_contract_test_path=REVERSAL_CONTRACT_TEST_PATH,
        adverse_scope_event_type=scope_binding.scope_event_evidence.event_type.value,
        adverse_exit_signal_triggered=scope_binding.scope_adverse_exit_signal.triggered,
        reversal_preparation_exit_class=reversal_decision.exit_class.value,
        reversal_preparation_reduce_only=True,
        rewire_state=REWIRE_STATE,
        functional_rewire_performed=True,
        new_parallel_owner_created=False,
    )
    return {
        "schema": "ScopeAdverseExitAndReversalPreparationNarrowReuseFirstRewireV1",
        "surface_id": SURFACE_ID,
        "plan_type": PLAN_TYPE,
        "trace_assertion_source_pr": TRACE_ASSERTION_SOURCE_PR,
        "rewire_scope": "scope_adverse_exit_and_reversal_preparation_only",
        "rewire_binding": asdict(binding),
        "forbidden_claims_remain_false": {
            "FULL_CANONICAL_CHAIN_WIRED": False,
            "BACKTEST_RUNTIME_DECISION_PARITY_PASS": False,
            "SYSTEM_ECONOMIC_EVIDENCE_ADMISSIBLE": False,
            "RUNTIME_AUTHORITY": False,
            "ORDERS_ALLOWED": False,
            "ECONOMIC_CLAIM": False,
        },
        **NO_AUTHORITY_FLAGS,
    }


def render_markdown(rewire: dict[str, Any]) -> str:
    binding = rewire["rewire_binding"]
    lines = [
        "# Scope Adverse Exit And Reversal Preparation Narrow Reuse-First Rewire V1",
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
        "```",
        "",
        f"- reused_scope_canonical_owner: `{binding['reused_scope_canonical_owner']}`",
        f"- reused_scope_adapter_owner: `{binding['reused_scope_adapter_owner']}`",
        f"- reused_reversal_adapter_owner: `{binding['reused_reversal_adapter_owner']}`",
        f"- harness_path: `{binding['harness_path']}`",
        f"- scope_contract_test_path: `{binding['scope_contract_test_path']}`",
        f"- reversal_contract_test_path: `{binding['reversal_contract_test_path']}`",
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
    (
        output_dir / "scope_adverse_exit_and_reversal_preparation_narrow_reuse_first_rewire_v0.json"
    ).write_text(
        json.dumps(rewire, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (
        output_dir / "scope_adverse_exit_and_reversal_preparation_narrow_reuse_first_rewire_v0.md"
    ).write_text(
        render_markdown(rewire) + "\n",
        encoding="utf-8",
    )
    verdict = "PASS_SCOPE_ADVERSE_EXIT_AND_REVERSAL_PREPARATION_NARROW_REUSE_FIRST_REWIRE_BOUND"
    (output_dir / "verdict.txt").write_text(verdict + "\n", encoding="utf-8")
    manifest_rc = write_manifest(output_dir)
    (output_dir / "manifest_verify_rc.txt").write_text(f"{manifest_rc}\n", encoding="utf-8")
    manifest_rc = write_manifest(output_dir)
    print(verdict)
    print(f"REUSED_SCOPE_CANONICAL_OWNER={REUSED_SCOPE_CANONICAL_OWNER}")
    print(f"FUNCTIONAL_REWIRE_PERFORMED=true")
    print(f"MANIFEST_VERIFY_RC={manifest_rc}")
    print(f"EVIDENCE_DIR={output_dir}")
    return 0 if manifest_rc == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
