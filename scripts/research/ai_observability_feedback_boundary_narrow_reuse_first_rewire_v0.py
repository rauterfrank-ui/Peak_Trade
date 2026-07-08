from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from scripts.research.backtest_runtime_decision_parity_trace_matrix_v0 import NO_AUTHORITY_FLAGS
from trading.master_v2.ai_observability_boundary_backtest_state_file_binding_adapter_v0 import (
    AI_OBSERVABILITY_BOUNDARY_BACKTEST_STATE_FILE_BINDING_ADAPTER_OWNER,
)
from trading.master_v2.ai_observability_boundary_offline_replay_binding_adapter_v0 import (
    AI_LAYER_OBSERVABILITY_BOUNDARY_DOCUMENTED,
    AI_OBSERVABILITY_BOUNDARY_EFFECT_BOUND_OFFLINE,
    AI_OBSERVABILITY_BOUNDARY_OFFLINE_REPLAY_BINDING_ADAPTER_OWNER,
    AI_OBSERVABILITY_CANONICAL_OWNER,
    AiObservabilityBoundaryOfflineReplayContextV0,
    bind_ai_observability_boundary_offline_replay_evidence_v0,
    ai_observability_boundary_binding_non_authority_boundary_ok_v0,
)
from trading.master_v2.capital_risk_sizing_offline_replay_binding_adapter_v0 import (
    build_scenario_tick_decision_evidence_v0,
)
from trading.master_v2.feedback_learning_boundary_backtest_state_file_binding_adapter_v0 import (
    FEEDBACK_LEARNING_BOUNDARY_BACKTEST_STATE_FILE_BINDING_ADAPTER_OWNER,
)
from trading.master_v2.feedback_learning_boundary_offline_replay_binding_adapter_v0 import (
    FEEDBACK_LEARNING_BOUNDARY_DOCUMENTED,
    FEEDBACK_LEARNING_BOUNDARY_EFFECT_BOUND_OFFLINE,
    FEEDBACK_LEARNING_BOUNDARY_OFFLINE_REPLAY_BINDING_ADAPTER_OWNER,
    FEEDBACK_LEARNING_CANONICAL_OWNER,
    FeedbackLearningBoundaryOfflineReplayContextV0,
    bind_feedback_learning_boundary_offline_replay_evidence_v0,
    feedback_learning_boundary_binding_non_authority_boundary_ok_v0,
)
from trading.master_v2.integrated_vs_scenario_replay_full_system_parity_harness_v0 import (
    assert_ai_observability_boundary_non_authority_boundary_v0,
    assert_feedback_learning_boundary_non_authority_boundary_v0,
    canonical_owner_refs_v0,
    extract_ai_observability_boundary_parity_envelope_v0,
    extract_feedback_learning_boundary_parity_envelope_v0,
)

SURFACE_ID = "ai_observability_feedback_boundary"
PLAN_TYPE = "NARROW_REUSE_FIRST_REWIRE"
TRACE_ASSERTION_SOURCE_PR = 5015
REWIRE_STATE = "REWIRE_BOUND_OFFLINE_PARITY_PATH"

REUSED_AI_OBSERVABILITY_CANONICAL_OWNER = AI_OBSERVABILITY_CANONICAL_OWNER
REUSED_FEEDBACK_LEARNING_CANONICAL_OWNER = FEEDBACK_LEARNING_CANONICAL_OWNER
REUSED_AI_OBSERVABILITY_OFFLINE_REPLAY_ADAPTER_OWNER = (
    AI_OBSERVABILITY_BOUNDARY_OFFLINE_REPLAY_BINDING_ADAPTER_OWNER
)
REUSED_FEEDBACK_LEARNING_OFFLINE_REPLAY_ADAPTER_OWNER = (
    FEEDBACK_LEARNING_BOUNDARY_OFFLINE_REPLAY_BINDING_ADAPTER_OWNER
)
REUSED_AI_OBSERVABILITY_BOUNDARY_BACKTEST_ADAPTER_OWNER = (
    AI_OBSERVABILITY_BOUNDARY_BACKTEST_STATE_FILE_BINDING_ADAPTER_OWNER
)
REUSED_FEEDBACK_LEARNING_BOUNDARY_BACKTEST_ADAPTER_OWNER = (
    FEEDBACK_LEARNING_BOUNDARY_BACKTEST_STATE_FILE_BINDING_ADAPTER_OWNER
)

AI_OBSERVABILITY_CANONICAL_OWNER_PATH = (
    "src/trading/master_v2/canonical_trading_decision_evidence_v1.py"
)
FEEDBACK_LEARNING_CANONICAL_OWNER_PATH = "src/meta/learning_loop/runtime_observation_feedback_v1.py"
AI_OBSERVABILITY_OFFLINE_REPLAY_ADAPTER_PATH = (
    "src/trading/master_v2/ai_observability_boundary_offline_replay_binding_adapter_v0.py"
)
FEEDBACK_LEARNING_OFFLINE_REPLAY_ADAPTER_PATH = (
    "src/trading/master_v2/feedback_learning_boundary_offline_replay_binding_adapter_v0.py"
)
AI_OBSERVABILITY_BOUNDARY_BACKTEST_ADAPTER_PATH = (
    "src/trading/master_v2/ai_observability_boundary_backtest_state_file_binding_adapter_v0.py"
)
FEEDBACK_LEARNING_BOUNDARY_BACKTEST_ADAPTER_PATH = (
    "src/trading/master_v2/feedback_learning_boundary_backtest_state_file_binding_adapter_v0.py"
)
HARNESS_PATH = (
    "src/trading/master_v2/integrated_vs_scenario_replay_full_system_parity_harness_v0.py"
)
AI_OBSERVABILITY_OFFLINE_REPLAY_CONTRACT_TEST_PATH = "tests/trading/master_v2/test_ai_observability_boundary_offline_replay_binding_parity_rewire_contract_v0.py"
AI_OBSERVABILITY_BOUNDARY_BACKTEST_CONTRACT_TEST_PATH = "tests/trading/master_v2/test_ai_observability_boundary_backtest_state_file_binding_contract_v0.py"
FEEDBACK_LEARNING_OFFLINE_REPLAY_CONTRACT_TEST_PATH = "tests/trading/master_v2/test_feedback_learning_boundary_offline_replay_binding_parity_rewire_contract_v0.py"
FEEDBACK_LEARNING_BOUNDARY_BACKTEST_CONTRACT_TEST_PATH = "tests/trading/master_v2/test_feedback_learning_boundary_backtest_state_file_binding_contract_v0.py"
CHAINED_CONTRACT_TEST_PATH = (
    "tests/research/test_ai_observability_feedback_boundary_narrow_reuse_first_rewire_v0.py"
)
OWNER_BOUND_PATHS = (
    AI_OBSERVABILITY_CANONICAL_OWNER_PATH,
    FEEDBACK_LEARNING_CANONICAL_OWNER_PATH,
    AI_OBSERVABILITY_OFFLINE_REPLAY_ADAPTER_PATH,
    FEEDBACK_LEARNING_OFFLINE_REPLAY_ADAPTER_PATH,
    AI_OBSERVABILITY_BOUNDARY_BACKTEST_ADAPTER_PATH,
    FEEDBACK_LEARNING_BOUNDARY_BACKTEST_ADAPTER_PATH,
    HARNESS_PATH,
    AI_OBSERVABILITY_OFFLINE_REPLAY_CONTRACT_TEST_PATH,
    AI_OBSERVABILITY_BOUNDARY_BACKTEST_CONTRACT_TEST_PATH,
    FEEDBACK_LEARNING_OFFLINE_REPLAY_CONTRACT_TEST_PATH,
    FEEDBACK_LEARNING_BOUNDARY_BACKTEST_CONTRACT_TEST_PATH,
    CHAINED_CONTRACT_TEST_PATH,
)


@dataclass(frozen=True)
class RewireBinding:
    surface_id: str
    reused_ai_observability_canonical_owner: str
    reused_feedback_learning_canonical_owner: str
    reused_ai_observability_offline_replay_adapter_owner: str
    reused_feedback_learning_offline_replay_adapter_owner: str
    reused_ai_observability_boundary_backtest_adapter_owner: str
    reused_feedback_learning_boundary_backtest_adapter_owner: str
    ai_observability_canonical_owner_path: str
    feedback_learning_canonical_owner_path: str
    ai_observability_offline_replay_adapter_path: str
    feedback_learning_offline_replay_adapter_path: str
    ai_observability_boundary_backtest_adapter_path: str
    feedback_learning_boundary_backtest_adapter_path: str
    harness_path: str
    ai_observability_offline_replay_contract_test_path: str
    ai_observability_boundary_backtest_contract_test_path: str
    feedback_learning_offline_replay_contract_test_path: str
    feedback_learning_boundary_backtest_contract_test_path: str
    chained_contract_test_path: str
    promotion_gate_boundary_chain_preserved: bool
    ai_layer_observability_boundary_documented: bool
    feedback_learning_boundary_documented: bool
    ai_observability_read_only_evidence_only: bool
    feedback_learning_observe_only_no_mutation: bool
    ai_observability_boundary_effect: str
    feedback_learning_boundary_effect: str
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
    if refs["ai_observability_canonical_owner"] != REUSED_AI_OBSERVABILITY_CANONICAL_OWNER:
        raise ValueError("ai observability canonical owner drift")
    if refs["feedback_learning_canonical_owner"] != REUSED_FEEDBACK_LEARNING_CANONICAL_OWNER:
        raise ValueError("feedback learning canonical owner drift")
    if (
        refs["ai_observability_boundary_offline_replay_binding_adapter"]
        != REUSED_AI_OBSERVABILITY_OFFLINE_REPLAY_ADAPTER_OWNER
    ):
        raise ValueError("ai observability offline replay adapter owner drift")
    if (
        refs["feedback_learning_boundary_offline_replay_binding_adapter"]
        != REUSED_FEEDBACK_LEARNING_OFFLINE_REPLAY_ADAPTER_OWNER
    ):
        raise ValueError("feedback learning offline replay adapter owner drift")
    if (
        refs["ai_observability_boundary_backtest_state_file_binding_adapter"]
        != REUSED_AI_OBSERVABILITY_BOUNDARY_BACKTEST_ADAPTER_OWNER
    ):
        raise ValueError("ai observability backtest adapter owner drift")
    if (
        refs["feedback_learning_boundary_backtest_state_file_binding_adapter"]
        != REUSED_FEEDBACK_LEARNING_BOUNDARY_BACKTEST_ADAPTER_OWNER
    ):
        raise ValueError("feedback learning backtest adapter owner drift")


def evaluate_ai_observability_feedback_boundary_parity_fixtures_v0(
    *,
    context_reference: str = "ai-observability-feedback-boundary-narrow-rewire-v0",
) -> tuple[Any, Any]:
    evidence = build_scenario_tick_decision_evidence_v0(
        decision_id=f"{context_reference}-decision",
        replay_id=f"{context_reference}-replay",
        instrument_id="inst-eth-usdt-perp",
        trading_epoch=48,
        composition_result_id=f"{context_reference}-composition",
        entry_exit_policy_ref=f"{context_reference}-policy",
        selected_side="long",
        decision_outcome="observe",
        reason_codes=("PASS", "OBSERVABILITY_TRACE"),
        decision_precedence_trace=("observe",),
        config_digest="config",
        implementation_digest="impl",
    )
    ai_binding = bind_ai_observability_boundary_offline_replay_evidence_v0(
        evidence,
        context=AiObservabilityBoundaryOfflineReplayContextV0(),
    )
    ai_envelope = extract_ai_observability_boundary_parity_envelope_v0(
        ai_binding,
        decision_outcome="observe",
        composition_result_id=f"{context_reference}-composition",
    )
    assert_ai_observability_boundary_non_authority_boundary_v0(ai_envelope)
    if not ai_observability_boundary_binding_non_authority_boundary_ok_v0(ai_binding):
        raise ValueError("ai observability binding violated non-authority boundary")
    if not ai_binding.binding_applied:
        raise ValueError("fixture must bind ai observability boundary")
    if (
        ai_binding.ai_observability_boundary_effect
        != AI_OBSERVABILITY_BOUNDARY_EFFECT_BOUND_OFFLINE
    ):
        raise ValueError("fixture must remain offline-bound only for ai observability")
    if not ai_binding.boundary.ai_layer_observability_boundary_documented:
        raise ValueError("ai layer observability boundary must be documented")
    if not ai_binding.boundary.read_only_evidence_only:
        raise ValueError("ai observability must remain read-only evidence only")

    feedback_binding = bind_feedback_learning_boundary_offline_replay_evidence_v0(
        evidence,
        context=FeedbackLearningBoundaryOfflineReplayContextV0(),
    )
    feedback_envelope = extract_feedback_learning_boundary_parity_envelope_v0(
        feedback_binding,
        decision_outcome="observe",
        composition_result_id=f"{context_reference}-composition",
    )
    assert_feedback_learning_boundary_non_authority_boundary_v0(feedback_envelope)
    if not feedback_learning_boundary_binding_non_authority_boundary_ok_v0(feedback_binding):
        raise ValueError("feedback learning binding violated non-authority boundary")
    if not feedback_binding.binding_applied:
        raise ValueError("fixture must bind feedback learning boundary")
    if (
        feedback_binding.feedback_learning_boundary_effect
        != FEEDBACK_LEARNING_BOUNDARY_EFFECT_BOUND_OFFLINE
    ):
        raise ValueError("fixture must remain offline-bound only for feedback learning")
    if not feedback_binding.boundary.feedback_learning_boundary_documented:
        raise ValueError("feedback learning boundary must be documented")
    if not feedback_binding.boundary.observe_only_no_mutation:
        raise ValueError("feedback learning must remain observe-only without mutation")
    return ai_binding, feedback_binding


def build_rewire_binding(repo_root: Path) -> dict[str, Any]:
    _assert_owner_bound_paths_exist(repo_root)
    _assert_canonical_owner_reuse()
    ai_binding, feedback_binding = evaluate_ai_observability_feedback_boundary_parity_fixtures_v0()
    binding = RewireBinding(
        surface_id=SURFACE_ID,
        reused_ai_observability_canonical_owner=REUSED_AI_OBSERVABILITY_CANONICAL_OWNER,
        reused_feedback_learning_canonical_owner=REUSED_FEEDBACK_LEARNING_CANONICAL_OWNER,
        reused_ai_observability_offline_replay_adapter_owner=(
            REUSED_AI_OBSERVABILITY_OFFLINE_REPLAY_ADAPTER_OWNER
        ),
        reused_feedback_learning_offline_replay_adapter_owner=(
            REUSED_FEEDBACK_LEARNING_OFFLINE_REPLAY_ADAPTER_OWNER
        ),
        reused_ai_observability_boundary_backtest_adapter_owner=(
            REUSED_AI_OBSERVABILITY_BOUNDARY_BACKTEST_ADAPTER_OWNER
        ),
        reused_feedback_learning_boundary_backtest_adapter_owner=(
            REUSED_FEEDBACK_LEARNING_BOUNDARY_BACKTEST_ADAPTER_OWNER
        ),
        ai_observability_canonical_owner_path=AI_OBSERVABILITY_CANONICAL_OWNER_PATH,
        feedback_learning_canonical_owner_path=FEEDBACK_LEARNING_CANONICAL_OWNER_PATH,
        ai_observability_offline_replay_adapter_path=AI_OBSERVABILITY_OFFLINE_REPLAY_ADAPTER_PATH,
        feedback_learning_offline_replay_adapter_path=FEEDBACK_LEARNING_OFFLINE_REPLAY_ADAPTER_PATH,
        ai_observability_boundary_backtest_adapter_path=AI_OBSERVABILITY_BOUNDARY_BACKTEST_ADAPTER_PATH,
        feedback_learning_boundary_backtest_adapter_path=FEEDBACK_LEARNING_BOUNDARY_BACKTEST_ADAPTER_PATH,
        harness_path=HARNESS_PATH,
        ai_observability_offline_replay_contract_test_path=AI_OBSERVABILITY_OFFLINE_REPLAY_CONTRACT_TEST_PATH,
        ai_observability_boundary_backtest_contract_test_path=AI_OBSERVABILITY_BOUNDARY_BACKTEST_CONTRACT_TEST_PATH,
        feedback_learning_offline_replay_contract_test_path=FEEDBACK_LEARNING_OFFLINE_REPLAY_CONTRACT_TEST_PATH,
        feedback_learning_boundary_backtest_contract_test_path=FEEDBACK_LEARNING_BOUNDARY_BACKTEST_CONTRACT_TEST_PATH,
        chained_contract_test_path=CHAINED_CONTRACT_TEST_PATH,
        promotion_gate_boundary_chain_preserved=True,
        ai_layer_observability_boundary_documented=AI_LAYER_OBSERVABILITY_BOUNDARY_DOCUMENTED,
        feedback_learning_boundary_documented=FEEDBACK_LEARNING_BOUNDARY_DOCUMENTED,
        ai_observability_read_only_evidence_only=ai_binding.boundary.read_only_evidence_only,
        feedback_learning_observe_only_no_mutation=feedback_binding.boundary.observe_only_no_mutation,
        ai_observability_boundary_effect=ai_binding.ai_observability_boundary_effect,
        feedback_learning_boundary_effect=feedback_binding.feedback_learning_boundary_effect,
        rewire_state=REWIRE_STATE,
        functional_rewire_performed=True,
        new_parallel_owner_created=False,
    )
    return {
        "schema": "AiObservabilityFeedbackBoundaryNarrowReuseFirstRewireV1",
        "surface_id": SURFACE_ID,
        "plan_type": PLAN_TYPE,
        "trace_assertion_source_pr": TRACE_ASSERTION_SOURCE_PR,
        "rewire_scope": "ai_observability_feedback_boundary_only",
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
        "# AI Observability Feedback Boundary Narrow Reuse-First Rewire V1",
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
        "AI_LAYER_OBSERVABILITY_BOUNDARY_DOCUMENTED=true",
        "FEEDBACK_LEARNING_BOUNDARY_DOCUMENTED=true",
        "```",
        "",
        f"- reused_ai_observability_canonical_owner: `{binding['reused_ai_observability_canonical_owner']}`",
        f"- reused_feedback_learning_canonical_owner: `{binding['reused_feedback_learning_canonical_owner']}`",
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
    (
        output_dir / "ai_observability_feedback_boundary_narrow_reuse_first_rewire_v0.json"
    ).write_text(
        json.dumps(rewire, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_dir / "ai_observability_feedback_boundary_narrow_reuse_first_rewire_v0.md").write_text(
        render_markdown(rewire) + "\n",
        encoding="utf-8",
    )
    verdict = "PASS_AI_OBSERVABILITY_FEEDBACK_BOUNDARY_NARROW_REUSE_FIRST_REWIRE_BOUND"
    (output_dir / "verdict.txt").write_text(verdict + "\n", encoding="utf-8")
    manifest_rc = write_manifest(output_dir)
    (output_dir / "manifest_verify_rc.txt").write_text(f"{manifest_rc}\n", encoding="utf-8")
    manifest_rc = write_manifest(output_dir)
    print(verdict)
    print(f"REUSED_AI_OBSERVABILITY_CANONICAL_OWNER={REUSED_AI_OBSERVABILITY_CANONICAL_OWNER}")
    print(f"REUSED_FEEDBACK_LEARNING_CANONICAL_OWNER={REUSED_FEEDBACK_LEARNING_CANONICAL_OWNER}")
    print("FUNCTIONAL_REWIRE_PERFORMED=true")
    print(f"MANIFEST_VERIFY_RC={manifest_rc}")
    print(f"EVIDENCE_DIR={output_dir}")
    return 0 if manifest_rc == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
