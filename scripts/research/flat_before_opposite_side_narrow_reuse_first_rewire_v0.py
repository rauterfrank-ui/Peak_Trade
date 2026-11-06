from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from scripts.research.backtest_runtime_decision_parity_trace_matrix_v0 import NO_AUTHORITY_FLAGS
from trading.master_v2.double_play_entry_exit_policy_v0 import DecisionOutcome
from trading.master_v2.double_play_entry_exit_scenario_binding_adapter_v0 import (
    CANONICAL_ENTRY_EXIT_POLICY_OWNER,
)
from trading.master_v2.flat_before_opposite_side_scenario_binding_adapter_v0 import (
    FLAT_BEFORE_OPPOSITE_SIDE_SCENARIO_BINDING_ADAPTER_OWNER,
    flat_before_opposite_side_binding_non_authority_boundary_ok_v0,
    flat_before_opposite_side_blocks_opposite_entry_v0,
)
from trading.master_v2.integrated_vs_scenario_replay_full_system_parity_harness_v0 import (
    assert_flat_before_opposite_side_non_authority_boundary_v0,
    canonical_owner_refs_v0,
    evaluate_scenario_flat_before_opposite_side_for_fixture_v0,
    extract_flat_before_opposite_side_parity_envelope_v0,
)
from trading.master_v2.offline_double_play_scenario_replay_v0 import SYNTHETIC_FUTURES_INSTRUMENT

SURFACE_ID = "flat_before_opposite_side"
PLAN_TYPE = "NARROW_REUSE_FIRST_REWIRE"
TRACE_ASSERTION_SOURCE_PR = 5008
REWIRE_STATE = "REWIRE_BOUND_OFFLINE_PARITY_PATH"

REUSED_CANONICAL_OWNER = CANONICAL_ENTRY_EXIT_POLICY_OWNER
REUSED_ADAPTER_OWNER = FLAT_BEFORE_OPPOSITE_SIDE_SCENARIO_BINDING_ADAPTER_OWNER
CANONICAL_OWNER_PATH = "src/trading/master_v2/double_play_entry_exit_policy_v0.py"
ADAPTER_PATH = "src/trading/master_v2/flat_before_opposite_side_scenario_binding_adapter_v0.py"
HARNESS_PATH = (
    "src/trading/master_v2/integrated_vs_scenario_replay_full_system_parity_harness_v0.py"
)
OFFLINE_REPLAY_PATH = "src/trading/master_v2/offline_double_play_scenario_replay_v0.py"
CONTRACT_TEST_PATH = "tests/trading/master_v2/test_flat_before_opposite_side_scenario_replay_binding_parity_rewire_contract_v0.py"
OWNER_BOUND_PATHS = (
    CANONICAL_OWNER_PATH,
    ADAPTER_PATH,
    HARNESS_PATH,
    OFFLINE_REPLAY_PATH,
    CONTRACT_TEST_PATH,
)


@dataclass(frozen=True)
class RewireBinding:
    surface_id: str
    reused_canonical_owner: str
    reused_adapter_owner: str
    canonical_owner_path: str
    adapter_path: str
    harness_path: str
    offline_replay_path: str
    contract_test_path: str
    blocked_opposite_entry: bool
    decision_outcome: str
    position_flip_allowed: bool
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
    if refs["entry_exit_policy"] != REUSED_CANONICAL_OWNER:
        raise ValueError("entry-exit policy owner drift")
    if refs["flat_before_opposite_side_scenario_binding_adapter"] != REUSED_ADAPTER_OWNER:
        raise ValueError("flat-before-opposite-side adapter owner drift")


def evaluate_flat_before_opposite_side_parity_fixtures_v0(
    *,
    instrument_id: str = SYNTHETIC_FUTURES_INSTRUMENT,
    trading_epoch: int = 54,
    context_reference: str = "flat-before-opposite-narrow-rewire-v0",
) -> Any:
    decision = evaluate_scenario_flat_before_opposite_side_for_fixture_v0(
        instrument_id=instrument_id,
        trading_epoch=trading_epoch,
        context_reference=context_reference,
    )
    envelope = extract_flat_before_opposite_side_parity_envelope_v0(
        decision,
        composition_status="SHORT_SELECTED",
    )
    assert_flat_before_opposite_side_non_authority_boundary_v0(envelope)
    if not flat_before_opposite_side_blocks_opposite_entry_v0(decision):
        raise ValueError("fixture must block opposite entry while position not flat")
    if not flat_before_opposite_side_binding_non_authority_boundary_ok_v0(decision):
        raise ValueError("flat-before-opposite-side binding violated non-authority boundary")
    if decision.decision_outcome is DecisionOutcome.ENTER_SHORT:
        raise ValueError("fixture must not allow direct opposite entry")
    return decision


def build_rewire_binding(repo_root: Path) -> dict[str, Any]:
    _assert_owner_bound_paths_exist(repo_root)
    _assert_canonical_owner_reuse()
    decision = evaluate_flat_before_opposite_side_parity_fixtures_v0()
    binding = RewireBinding(
        surface_id=SURFACE_ID,
        reused_canonical_owner=REUSED_CANONICAL_OWNER,
        reused_adapter_owner=REUSED_ADAPTER_OWNER,
        canonical_owner_path=CANONICAL_OWNER_PATH,
        adapter_path=ADAPTER_PATH,
        harness_path=HARNESS_PATH,
        offline_replay_path=OFFLINE_REPLAY_PATH,
        contract_test_path=CONTRACT_TEST_PATH,
        blocked_opposite_entry=flat_before_opposite_side_blocks_opposite_entry_v0(decision),
        decision_outcome=decision.decision_outcome.value,
        position_flip_allowed=decision.position_flip_allowed,
        rewire_state=REWIRE_STATE,
        functional_rewire_performed=True,
        new_parallel_owner_created=False,
    )
    return {
        "schema": "FlatBeforeOppositeSideNarrowReuseFirstRewireV1",
        "surface_id": SURFACE_ID,
        "plan_type": PLAN_TYPE,
        "trace_assertion_source_pr": TRACE_ASSERTION_SOURCE_PR,
        "rewire_scope": "flat_before_opposite_side_only",
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
        "# Flat Before Opposite Side Narrow Reuse-First Rewire V1",
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
        f"- reused_canonical_owner: `{binding['reused_canonical_owner']}`",
        f"- reused_adapter_owner: `{binding['reused_adapter_owner']}`",
        f"- harness_path: `{binding['harness_path']}`",
        f"- contract_test_path: `{binding['contract_test_path']}`",
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
    (output_dir / "flat_before_opposite_side_narrow_reuse_first_rewire_v0.json").write_text(
        json.dumps(rewire, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_dir / "flat_before_opposite_side_narrow_reuse_first_rewire_v0.md").write_text(
        render_markdown(rewire) + "\n",
        encoding="utf-8",
    )
    verdict = "PASS_FLAT_BEFORE_OPPOSITE_SIDE_NARROW_REUSE_FIRST_REWIRE_BOUND"
    (output_dir / "verdict.txt").write_text(verdict + "\n", encoding="utf-8")
    manifest_rc = write_manifest(output_dir)
    (output_dir / "manifest_verify_rc.txt").write_text(f"{manifest_rc}\n", encoding="utf-8")
    manifest_rc = write_manifest(output_dir)
    print(verdict)
    print(f"REUSED_CANONICAL_OWNER={REUSED_CANONICAL_OWNER}")
    print(f"FUNCTIONAL_REWIRE_PERFORMED=true")
    print(f"MANIFEST_VERIFY_RC={manifest_rc}")
    print(f"EVIDENCE_DIR={output_dir}")
    return 0 if manifest_rc == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
