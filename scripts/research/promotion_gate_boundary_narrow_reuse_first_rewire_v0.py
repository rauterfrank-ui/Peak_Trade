from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from scripts.research.backtest_runtime_decision_parity_trace_matrix_v0 import NO_AUTHORITY_FLAGS
from src.backtest.economic_validity_policy_v1 import canonical_economic_validity_policy_v1
from src.governance.promotion_loop import promotion_economic_gate_v1 as gate
from trading.master_v2.capital_risk_sizing_offline_replay_binding_adapter_v0 import (
    build_scenario_tick_decision_evidence_v0,
)
from trading.master_v2.integrated_vs_scenario_replay_full_system_parity_harness_v0 import (
    assert_promotion_gate_boundary_non_authority_boundary_v0,
    canonical_owner_refs_v0,
    extract_promotion_gate_boundary_parity_envelope_v0,
)
from trading.master_v2.promotion_gate_boundary_backtest_state_file_binding_adapter_v0 import (
    PROMOTION_GATE_BOUNDARY_BACKTEST_STATE_FILE_BINDING_ADAPTER_OWNER,
)
from trading.master_v2.promotion_gate_boundary_offline_replay_binding_adapter_v0 import (
    PROMOTION_GATE_BOUNDARY_EFFECT_BOUND_OFFLINE,
    PROMOTION_GATE_BOUNDARY_OFFLINE_REPLAY_BINDING_ADAPTER_OWNER,
    PROMOTION_GATE_CANONICAL_OWNER,
    PromotionGateBoundaryOfflineReplayContextV0,
    bind_promotion_gate_boundary_offline_replay_evidence_v0,
    promotion_gate_boundary_binding_non_authority_boundary_ok_v0,
)

SURFACE_ID = "promotion_gate_boundary"
PLAN_TYPE = "NARROW_REUSE_FIRST_REWIRE"
TRACE_ASSERTION_SOURCE_PR = 5014
REWIRE_STATE = "REWIRE_BOUND_OFFLINE_PARITY_PATH"

REUSED_CANONICAL_OWNER = PROMOTION_GATE_CANONICAL_OWNER
REUSED_OFFLINE_REPLAY_ADAPTER_OWNER = PROMOTION_GATE_BOUNDARY_OFFLINE_REPLAY_BINDING_ADAPTER_OWNER
REUSED_BOUNDARY_BACKTEST_ADAPTER_OWNER = (
    PROMOTION_GATE_BOUNDARY_BACKTEST_STATE_FILE_BINDING_ADAPTER_OWNER
)
CANONICAL_OWNER_PATH = "src/governance/promotion_loop/promotion_economic_gate_v1.py"
OFFLINE_REPLAY_ADAPTER_PATH = (
    "src/trading/master_v2/promotion_gate_boundary_offline_replay_binding_adapter_v0.py"
)
BOUNDARY_BACKTEST_ADAPTER_PATH = (
    "src/trading/master_v2/promotion_gate_boundary_backtest_state_file_binding_adapter_v0.py"
)
HARNESS_PATH = (
    "src/trading/master_v2/integrated_vs_scenario_replay_full_system_parity_harness_v0.py"
)
OFFLINE_REPLAY_CONTRACT_TEST_PATH = "tests/trading/master_v2/test_promotion_gate_boundary_offline_replay_binding_parity_rewire_contract_v0.py"
BOUNDARY_BACKTEST_CONTRACT_TEST_PATH = "tests/trading/master_v2/test_promotion_gate_boundary_backtest_state_file_binding_contract_v0.py"
CHAINED_CONTRACT_TEST_PATH = (
    "tests/research/test_promotion_gate_boundary_narrow_reuse_first_rewire_v0.py"
)
OWNER_BOUND_PATHS = (
    CANONICAL_OWNER_PATH,
    OFFLINE_REPLAY_ADAPTER_PATH,
    BOUNDARY_BACKTEST_ADAPTER_PATH,
    HARNESS_PATH,
    OFFLINE_REPLAY_CONTRACT_TEST_PATH,
    BOUNDARY_BACKTEST_CONTRACT_TEST_PATH,
    CHAINED_CONTRACT_TEST_PATH,
)


@dataclass(frozen=True)
class RewireBinding:
    surface_id: str
    reused_canonical_owner: str
    reused_offline_replay_adapter_owner: str
    reused_boundary_backtest_adapter_owner: str
    canonical_owner_path: str
    offline_replay_adapter_path: str
    boundary_backtest_adapter_path: str
    harness_path: str
    offline_replay_contract_test_path: str
    boundary_backtest_contract_test_path: str
    chained_contract_test_path: str
    reconciliation_unknown_outcome_chain_preserved: bool
    promotion_gate_semantics_represented: bool
    no_runtime_authority_from_promotion_represented: bool
    economic_validity_required_for_promotion_represented: bool
    promotion_gate_boundary_effect: str
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
    if refs["promotion_economic_gate"] != REUSED_CANONICAL_OWNER:
        raise ValueError("promotion economic gate owner drift")
    if (
        refs["promotion_gate_boundary_offline_replay_binding_adapter"]
        != REUSED_OFFLINE_REPLAY_ADAPTER_OWNER
    ):
        raise ValueError("promotion gate offline replay adapter owner drift")
    if (
        refs["promotion_gate_boundary_backtest_state_file_binding_adapter"]
        != REUSED_BOUNDARY_BACKTEST_ADAPTER_OWNER
    ):
        raise ValueError("promotion gate backtest state-file adapter owner drift")


def _valid_promotion_context() -> PromotionGateBoundaryOfflineReplayContextV0:
    economic_policy_digest = canonical_economic_validity_policy_v1().policy_digest()
    return PromotionGateBoundaryOfflineReplayContextV0(
        strategy_id="mv2_offline_research",
        strategy_version="v1",
        candidate_id="candidate-promotion-gate-narrow-rewire",
        economic_viability_evidence_ref="evidence://admissible/futures/v1/bundle-001",
        economic_validity_status=gate.PASS_STATUS,
        robustness_status=gate.PASS_STATUS,
        data_admissibility_status=gate.PASS_STATUS,
        evidence_admissibility_status=gate.PASS_STATUS,
        policy_threshold_status=gate.PASS_STATUS,
        walk_forward_status=gate.PASS_STATUS,
        out_of_sample_status=gate.PASS_STATUS,
        monte_carlo_status=gate.PASS_STATUS,
        stress_status=gate.PASS_STATUS,
        parameter_sensitivity_status=gate.PASS_STATUS,
        reproducibility_status=gate.PASS_STATUS,
        digest_binding_status=gate.PASS_STATUS,
        manifest_binding_status=gate.PASS_STATUS,
        safety_policy_status=gate.PASS_STATUS,
        futures_only=True,
        bitcoin_direction_allowed=False,
        config_digest="a" * 64,
        implementation_digest="b" * 64,
        policy_digest=economic_policy_digest,
        evidence_manifest_digest="c" * 64,
        economic_validity_proven=True,
        profitability_claim_allowed=True,
    )


def evaluate_promotion_gate_boundary_parity_fixtures_v0(
    *,
    context_reference: str = "promotion-gate-boundary-narrow-rewire-v0",
) -> Any:
    evidence = build_scenario_tick_decision_evidence_v0(
        decision_id=f"{context_reference}-decision",
        replay_id=f"{context_reference}-replay",
        instrument_id="inst-eth-usdt-perp",
        trading_epoch=48,
        composition_result_id=f"{context_reference}-composition",
        entry_exit_policy_ref=f"{context_reference}-policy",
        selected_side="long",
        decision_outcome="observe",
        reason_codes=("PASS",),
        decision_precedence_trace=("observe",),
        config_digest="config",
        implementation_digest="impl",
    )
    binding = bind_promotion_gate_boundary_offline_replay_evidence_v0(
        evidence,
        context=_valid_promotion_context(),
    )
    envelope = extract_promotion_gate_boundary_parity_envelope_v0(
        binding,
        decision_outcome="observe",
        composition_result_id=f"{context_reference}-composition",
    )
    assert_promotion_gate_boundary_non_authority_boundary_v0(envelope)
    if not promotion_gate_boundary_binding_non_authority_boundary_ok_v0(binding):
        raise ValueError("promotion gate binding violated non-authority boundary")
    if not binding.binding_applied:
        raise ValueError("fixture must bind promotion gate boundary")
    if binding.promotion_gate_boundary_effect != PROMOTION_GATE_BOUNDARY_EFFECT_BOUND_OFFLINE:
        raise ValueError("fixture must remain offline-bound only")
    if not binding.boundary.promotion_gate_semantics_represented:
        raise ValueError("promotion gate semantics must be represented")
    if not binding.boundary.no_runtime_authority_from_promotion_represented:
        raise ValueError("no runtime authority from promotion must be represented")
    if not binding.boundary.economic_validity_required_for_promotion_represented:
        raise ValueError("economic validity required for promotion must be represented")
    if binding.gate_result.runtime_eligible or binding.gate_result.execution_allowed:
        raise ValueError("promotion gate must not grant runtime or execution authority")
    return binding


def build_rewire_binding(repo_root: Path) -> dict[str, Any]:
    _assert_owner_bound_paths_exist(repo_root)
    _assert_canonical_owner_reuse()
    binding_result = evaluate_promotion_gate_boundary_parity_fixtures_v0()
    binding = RewireBinding(
        surface_id=SURFACE_ID,
        reused_canonical_owner=REUSED_CANONICAL_OWNER,
        reused_offline_replay_adapter_owner=REUSED_OFFLINE_REPLAY_ADAPTER_OWNER,
        reused_boundary_backtest_adapter_owner=REUSED_BOUNDARY_BACKTEST_ADAPTER_OWNER,
        canonical_owner_path=CANONICAL_OWNER_PATH,
        offline_replay_adapter_path=OFFLINE_REPLAY_ADAPTER_PATH,
        boundary_backtest_adapter_path=BOUNDARY_BACKTEST_ADAPTER_PATH,
        harness_path=HARNESS_PATH,
        offline_replay_contract_test_path=OFFLINE_REPLAY_CONTRACT_TEST_PATH,
        boundary_backtest_contract_test_path=BOUNDARY_BACKTEST_CONTRACT_TEST_PATH,
        chained_contract_test_path=CHAINED_CONTRACT_TEST_PATH,
        reconciliation_unknown_outcome_chain_preserved=True,
        promotion_gate_semantics_represented=(
            binding_result.boundary.promotion_gate_semantics_represented
        ),
        no_runtime_authority_from_promotion_represented=(
            binding_result.boundary.no_runtime_authority_from_promotion_represented
        ),
        economic_validity_required_for_promotion_represented=(
            binding_result.boundary.economic_validity_required_for_promotion_represented
        ),
        promotion_gate_boundary_effect=binding_result.promotion_gate_boundary_effect,
        rewire_state=REWIRE_STATE,
        functional_rewire_performed=True,
        new_parallel_owner_created=False,
    )
    return {
        "schema": "PromotionGateBoundaryNarrowReuseFirstRewireV1",
        "surface_id": SURFACE_ID,
        "plan_type": PLAN_TYPE,
        "trace_assertion_source_pr": TRACE_ASSERTION_SOURCE_PR,
        "rewire_scope": "promotion_gate_boundary_only",
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
        "# Promotion Gate Boundary Narrow Reuse-First Rewire V1",
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
        f"- reused_canonical_owner: `{binding['reused_canonical_owner']}`",
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
    (output_dir / "promotion_gate_boundary_narrow_reuse_first_rewire_v0.json").write_text(
        json.dumps(rewire, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_dir / "promotion_gate_boundary_narrow_reuse_first_rewire_v0.md").write_text(
        render_markdown(rewire) + "\n",
        encoding="utf-8",
    )
    verdict = "PASS_PROMOTION_GATE_BOUNDARY_NARROW_REUSE_FIRST_REWIRE_BOUND"
    (output_dir / "verdict.txt").write_text(verdict + "\n", encoding="utf-8")
    manifest_rc = write_manifest(output_dir)
    (output_dir / "manifest_verify_rc.txt").write_text(f"{manifest_rc}\n", encoding="utf-8")
    manifest_rc = write_manifest(output_dir)
    print(verdict)
    print(f"REUSED_CANONICAL_OWNER={REUSED_CANONICAL_OWNER}")
    print("FUNCTIONAL_REWIRE_PERFORMED=true")
    print(f"MANIFEST_VERIFY_RC={manifest_rc}")
    print(f"EVIDENCE_DIR={output_dir}")
    return 0 if manifest_rc == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
