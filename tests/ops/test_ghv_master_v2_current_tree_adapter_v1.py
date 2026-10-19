"""Isolated tests for the current-tree Master V2 GHV adapter. AUTHORITY=NONE."""

from __future__ import annotations

import importlib
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.ops.ghv_master_v2_current_tree_adapter_v1.constants_v1 import (
    CURRENT_ORIGIN_MAIN_SHA,
    CURRENT_ORIGIN_MAIN_TREE,
)
from scripts.ops.ghv_master_v2_current_tree_adapter_v1.extract_v1 import (
    extract_bounded_anchor_edges_v1,
    run_ghv_master_v2_current_tree_adapter_v1,
)
from scripts.ops.ghv_master_v2_current_tree_adapter_v1.ghv_projection_v1 import (
    ProjectionRejected,
    ghv_native_id,
    traverse_projected_graph_v1,
)
from scripts.ops.ghv_master_v2_current_tree_adapter_v1 import ghv_projection_v1
from scripts.ops.ghv_master_v2_current_tree_adapter_v1.tree_reader_v1 import PinRejected

BASELINE_EDGE_COUNT = 130
BASELINE_EDGE_DIGEST = "b05a0c73c7e2cefd2b6630d00aafcb9d9f5221c36bd53851b25fe737688f94f2"
LITERAL_MODULES = (
    "trading.master_v2.capital_risk_sizing_offline_replay_binding_adapter_v0",
    "trading.master_v2.safety_kernel_offline_replay_binding_adapter_v0",
    "trading.master_v2.canonical_order_intent_offline_replay_binding_adapter_v0",
    "trading.master_v2.reconciliation_unknown_outcome_offline_replay_binding_adapter_v0",
    "trading.master_v2.killswitch_boundary_offline_replay_binding_adapter_v0",
)
NEW_CALL_SYMBOLS = {
    "derive_protective_stop_price_from_adverse_exit_v0",
    "bind_capital_risk_sizing_offline_replay_evidence_v0",
    "bind_safety_kernel_offline_replay_evidence_v0",
    "bind_canonical_order_intent_offline_replay_evidence_v0",
    "bind_reconciliation_unknown_outcome_offline_replay_evidence_v0",
    "bind_killswitch_boundary_offline_replay_evidence_v0",
}
BASELINE_ALIAS_SYMBOLS = {
    "SafetyKernelOfflineReplayContextV0",
    "ReconciliationUnknownOutcomeOfflineReplayContextV0",
    "KillSwitchBoundaryOfflineReplayContextV0",
    "derive_killswitch_boundary_mode_v0",
}

MAIN_REPO = Path("/Users/frnkhrz/Peak_Trade")
ADAPTER_DIR = ROOT / "scripts/ops/ghv_master_v2_current_tree_adapter_v1"


def _git(repo: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def _porcelain(repo: Path) -> bytes:
    return subprocess.check_output(["git", "-C", str(repo), "status", "--porcelain=v1"])


def _commit_fixture(repo: Path) -> None:
    (repo / "src/trading/master_v2").mkdir(parents=True)
    (repo / "src/ops/full_core_live_path_composition_root_v1").mkdir(parents=True)
    (repo / "src/trading/master_v2/foreign_safety.py").write_text(
        "def apply_capital_safety_veto():\n    return None\n",
        encoding="utf-8",
    )
    (repo / "src/trading/master_v2/double_play_state.py").write_text(
        "def update_dynamic_boundaries():\n"
        "    return 1\n"
        "\n"
        "def transition_state():\n"
        "    return update_dynamic_boundaries()\n",
        encoding="utf-8",
    )
    (repo / "src/trading/master_v2/integrated_offline_trading_logic_replay_v1.py").write_text(
        "from trading.master_v2.double_play_state import (\n"
        "    transition_state,\n"
        "    update_dynamic_boundaries,\n"
        ")\n"
        "from trading.master_v2.foreign_safety import apply_capital_safety_veto\n"
        "\n"
        "def run_integrated_offline_trading_logic_replay_v1():\n"
        "    update_dynamic_boundaries()\n"
        "    transition_state()\n"
        "    apply_capital_safety_veto()\n"
        "    unknown_membership_target()\n",
        encoding="utf-8",
    )
    cycle = repo / (
        "src/ops/full_core_live_path_composition_root_v1/"
        "current_productive_master_v2_runtime_cycle_v1.py"
    )
    cycle.write_text(
        "from trading.master_v2.integrated_offline_trading_logic_replay_v1 import (\n"
        "    run_integrated_offline_trading_logic_replay_v1,\n"
        ")\n"
        "\n"
        "def run_current_productive_master_v2_runtime_cycle_v1():\n"
        "    return run_integrated_offline_trading_logic_replay_v1()\n",
        encoding="utf-8",
    )
    subprocess.run(["git", "-C", str(repo), "init", "-b", "main"], check=True)
    subprocess.run(["git", "-C", str(repo), "add", "."], check=True)
    subprocess.run(
        [
            "git",
            "-C",
            str(repo),
            "-c",
            "user.email=adapter-test@example.com",
            "-c",
            "user.name=adapter-test",
            "commit",
            "-m",
            "fixture",
        ],
        check=True,
    )


def _edge(report: dict, source: str, target: str) -> dict:
    matches = [
        edge
        for edge in report["edges"]
        if edge["symbol"] == source and edge["target_symbol"] == target
    ]
    assert len(matches) == 1
    return matches[0]


def test_explicit_pin_rejects_head_and_wrong_tree_without_git(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def boom(*_args, **_kwargs):
        raise AssertionError("git invoked")

    monkeypatch.setattr(subprocess, "run", boom)
    with pytest.raises(PinRejected) as head_error:
        run_ghv_master_v2_current_tree_adapter_v1(
            repo_root=ROOT,
            commit_sha="HEAD",
            tree_sha=CURRENT_ORIGIN_MAIN_TREE,
        )
    assert head_error.value.reason == "EXPLICIT_OBJECT_ID_REQUIRED"
    with pytest.raises(PinRejected) as tree_error:
        run_ghv_master_v2_current_tree_adapter_v1(
            repo_root=ROOT,
            commit_sha="a" * 40,
            tree_sha="b" * 40,
        )
    assert tree_error.value.reason == "CURRENT_PIN_MISMATCH"


def test_commit_object_is_rejected_as_tree(tmp_path: Path) -> None:
    _commit_fixture(tmp_path)
    commit = _git(tmp_path, "rev-parse", "HEAD")
    with pytest.raises(PinRejected) as exc:
        extract_bounded_anchor_edges_v1(repo_root=tmp_path, commit_sha=commit, tree_sha=commit)
    assert exc.value.reason.startswith("TREE_OBJECT_REQUIRED")


def test_dirty_worktree_cannot_change_edges(tmp_path: Path) -> None:
    _commit_fixture(tmp_path)
    commit = _git(tmp_path, "rev-parse", "HEAD")
    tree = _git(tmp_path, "rev-parse", f"{commit}^{{tree}}")
    replay = tmp_path / "src/trading/master_v2/integrated_offline_trading_logic_replay_v1.py"
    replay.write_text(
        replay.read_text(encoding="utf-8").replace(
            "transition_state()",
            "dirty_only_call()",
        ),
        encoding="utf-8",
    )
    dirty = _porcelain(tmp_path)
    report = extract_bounded_anchor_edges_v1(
        repo_root=tmp_path,
        commit_sha=commit,
        tree_sha=tree,
    )
    targets = {edge["target_symbol"] for edge in report["edges"]}
    assert "transition_state" in targets
    assert "dirty_only_call" not in targets
    assert "dirty_only_call" in replay.read_text(encoding="utf-8")
    assert _porcelain(tmp_path) == dirty


def test_fixture_edges_are_deterministic_and_do_not_interpret_foreign_names(tmp_path: Path) -> None:
    _commit_fixture(tmp_path)
    commit = _git(tmp_path, "rev-parse", "HEAD")
    tree = _git(tmp_path, "rev-parse", f"{commit}^{{tree}}")
    first = extract_bounded_anchor_edges_v1(repo_root=tmp_path, commit_sha=commit, tree_sha=tree)
    second = extract_bounded_anchor_edges_v1(repo_root=tmp_path, commit_sha=commit, tree_sha=tree)
    assert first == second
    assert first["authority"] == "NONE"
    assert first["trading_authority"] == "NONE"
    assert first["safety_authority"] == "NONE"
    assert first["external_post_count"] == 0
    assert first["census_decision_flow_remap"] is False
    assert first["ghosv_invoked"] is False
    assert first["graph_engine_created"] is False
    assert first["coverage"]["universe_coverage"] == "NOT_CLAIMED"
    sources = {(edge["file"], edge["symbol"]) for edge in first["edges"]}
    assert sources <= {
        (
            "src/ops/full_core_live_path_composition_root_v1/"
            "current_productive_master_v2_runtime_cycle_v1.py",
            "run_current_productive_master_v2_runtime_cycle_v1",
        ),
        (
            "src/trading/master_v2/integrated_offline_trading_logic_replay_v1.py",
            "run_integrated_offline_trading_logic_replay_v1",
        ),
        ("src/trading/master_v2/double_play_state.py", "transition_state"),
        ("src/trading/master_v2/double_play_state.py", "update_dynamic_boundaries"),
    }
    replay_to_state = _edge(
        first, "run_integrated_offline_trading_logic_replay_v1", "transition_state"
    )
    assert replay_to_state["membership"] == "START_ANCHOR"
    assert replay_to_state["wiring"] == "WIRED"
    assert replay_to_state["reachability"] == "NOT_PROVEN"
    assert replay_to_state["activity"] == "NOT_PROVEN"
    assert replay_to_state["authorization"] == "NOT_AUTHORIZED"
    assert replay_to_state["edge_type"] == "CALLS"
    assert replay_to_state["trading_authority_implied"] is False
    foreign = _edge(
        first,
        "run_integrated_offline_trading_logic_replay_v1",
        "apply_capital_safety_veto",
    )
    assert foreign["membership"] == "UNKNOWN_MEMBERSHIP"
    assert foreign["foreign_semantics"] == "NOT_INTERPRETED"
    assert "safety_authority" not in foreign
    assert "domain" not in foreign
    unknown = _edge(
        first,
        "run_integrated_offline_trading_logic_replay_v1",
        "unknown_membership_target",
    )
    assert unknown["membership"] == "UNKNOWN_MEMBERSHIP"
    assert unknown["existence"] == "NOT_PROVEN"
    assert unknown["activity"] == "NOT_PROVEN"
    assert all(edge["activity"] != "ACTIVE" for edge in first["edges"])
    assert all(edge["edge_type"] == "CALLS" for edge in first["edges"])


def test_authority_flag_cannot_escalate(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _commit_fixture(tmp_path)
    commit = _git(tmp_path, "rev-parse", "HEAD")
    tree = _git(tmp_path, "rev-parse", f"{commit}^{{tree}}")

    def escalate(edge_type: str) -> dict:
        return {"edge_type": edge_type, "trading_authority_implied": True}

    monkeypatch.setattr(
        "scripts.ops.ghv_master_v2_current_tree_adapter_v1.extract_v1.edge_semantics_flags",
        escalate,
    )
    with pytest.raises(PinRejected) as exc:
        extract_bounded_anchor_edges_v1(repo_root=tmp_path, commit_sha=commit, tree_sha=tree)
    assert exc.value.reason == "AUTHORITY_ESCALATION_REJECTED"


def test_reader_does_not_open_worktree_files(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _commit_fixture(tmp_path)
    commit = _git(tmp_path, "rev-parse", "HEAD")
    tree = _git(tmp_path, "rev-parse", f"{commit}^{{tree}}")

    def boom(self: Path, *_args, **_kwargs):
        raise AssertionError(f"worktree read {self}")

    monkeypatch.setattr(Path, "read_text", boom)
    monkeypatch.setattr(Path, "read_bytes", boom)
    report = extract_bounded_anchor_edges_v1(repo_root=tmp_path, commit_sha=commit, tree_sha=tree)
    assert report["edges"]


def test_adapter_source_has_no_productive_or_census_remap_imports() -> None:
    text = "\n".join(path.read_text(encoding="utf-8") for path in ADAPTER_DIR.glob("*.py"))
    for banned in (
        "census_flow_to_typed_edge",
        "from trading",
        "import trading",
        "from src.execution",
        "from src.risk",
        "import execution",
        "import risk",
        "ghosv_bounded_context_v1",
        "rev-parse HEAD",
        "integrated_causal_graph",
    ):
        assert banned not in text


def test_pinned_current_tree_edges_ignore_dirty_main_worktree() -> None:
    before_main = _porcelain(MAIN_REPO)
    before_worktree = _porcelain(ROOT)
    pinned = run_ghv_master_v2_current_tree_adapter_v1(
        repo_root=ROOT,
        commit_sha=CURRENT_ORIGIN_MAIN_SHA,
        tree_sha=CURRENT_ORIGIN_MAIN_TREE,
    )
    from_dirty_checkout = run_ghv_master_v2_current_tree_adapter_v1(
        repo_root=MAIN_REPO,
        commit_sha=CURRENT_ORIGIN_MAIN_SHA,
        tree_sha=CURRENT_ORIGIN_MAIN_TREE,
    )
    assert pinned == from_dirty_checkout
    assert _porcelain(MAIN_REPO) == before_main
    assert _porcelain(ROOT) == before_worktree
    assert pinned["current_sha"] == CURRENT_ORIGIN_MAIN_SHA
    assert pinned["current_tree"] == CURRENT_ORIGIN_MAIN_TREE
    assert pinned["coverage"]["status"] == "PARTIAL"
    replay_state = _edge(
        pinned, "run_integrated_offline_trading_logic_replay_v1", "transition_state"
    )
    replay_scope = _edge(
        pinned,
        "run_integrated_offline_trading_logic_replay_v1",
        "update_dynamic_boundaries",
    )
    cycle_replay = _edge(
        pinned,
        "run_current_productive_master_v2_runtime_cycle_v1",
        "run_integrated_offline_trading_logic_replay_v1",
    )
    assert 1928 in replay_state["call_lines"]
    assert replay_state["membership"] == "START_ANCHOR"
    assert {1725, 1936} <= set(replay_scope["call_lines"])
    assert replay_scope["membership"] == "START_ANCHOR"
    assert 1056 in cycle_replay["call_lines"]
    assert cycle_replay["reachability"] == "NOT_PROVEN"
    assert cycle_replay["activity"] == "NOT_PROVEN"
    scope_out = _edge(
        pinned,
        "update_dynamic_boundaries",
        "compute_canonical_base_geometry_magnitude_from_mark_and_volatility_v1",
    )
    assert scope_out["membership"] == "UNKNOWN_MEMBERSHIP"
    assert scope_out["existence"] == "EXISTS"
    assert scope_out["foreign_semantics"] == "NOT_INTERPRETED"
    assert all(edge["edge_type"] == "CALLS" for edge in pinned["edges"])
    assert all(edge["activity"] == "NOT_PROVEN" for edge in pinned["edges"])
    assert all(edge["trading_authority_implied"] is False for edge in pinned["edges"])
    anchor_ids = {item["anchor_id"] for item in pinned["anchors"]}
    assert anchor_ids == {
        "productive_master_v2_runtime_cycle",
        "integrated_master_v2_replay",
        "double_play_transition_state",
        "dynamic_scope_update_dynamic_boundaries",
    }
    scope_anchor = next(
        item
        for item in pinned["anchors"]
        if item["anchor_id"] == "dynamic_scope_update_dynamic_boundaries"
    )
    state_anchor = next(
        item for item in pinned["anchors"] if item["anchor_id"] == "double_play_transition_state"
    )
    assert (
        scope_anchor["file"] == state_anchor["file"] == "src/trading/master_v2/double_play_state.py"
    )
    assert scope_anchor["universe_membership"] == "NOT_CLAIMED"


def _commit_named_fixture(repo: Path, replay_body: str, binding_source: str) -> tuple[str, str]:
    _commit_fixture(repo)
    binding = repo / "src/trading/master_v2/sample_binding_v1.py"
    binding.write_text(binding_source, encoding="utf-8")
    replay = repo / "src/trading/master_v2/integrated_offline_trading_logic_replay_v1.py"
    replay.write_text(replay_body, encoding="utf-8")
    subprocess.run(["git", "-C", str(repo), "add", "."], check=True)
    subprocess.run(
        [
            "git",
            "-C",
            str(repo),
            "-c",
            "user.email=adapter-test@example.com",
            "-c",
            "user.name=adapter-test",
            "commit",
            "-m",
            "dynamic fixture",
        ],
        check=True,
    )
    commit = _git(repo, "rev-parse", "HEAD")
    tree = _git(repo, "rev-parse", f"{commit}^{{tree}}")
    return commit, tree


def _replay_header() -> str:
    return (
        "import importlib\n"
        "from trading.master_v2.double_play_state import (\n"
        "    transition_state,\n"
        "    update_dynamic_boundaries,\n"
        ")\n"
        "from trading.master_v2.foreign_safety import apply_capital_safety_veto\n"
        "\n"
        "def run_integrated_offline_trading_logic_replay_v1():\n"
        "    update_dynamic_boundaries()\n"
        "    transition_state()\n"
        "    apply_capital_safety_veto()\n"
        "    unknown_membership_target()\n"
    )


def test_baseline_digest_stays_separate_from_new_edges() -> None:
    report = run_ghv_master_v2_current_tree_adapter_v1(
        repo_root=ROOT,
        commit_sha=CURRENT_ORIGIN_MAIN_SHA,
        tree_sha=CURRENT_ORIGIN_MAIN_TREE,
    )
    assert report["baseline_edge_count"] == BASELINE_EDGE_COUNT
    assert report["edge_digest_sha256"] == BASELINE_EDGE_DIGEST
    assert report["baseline_edge_digest_sha256"] == BASELINE_EDGE_DIGEST
    assert report["new_resolved_call_edge_count"] == 6
    assert report["execution_authority"] == "NONE"
    assert {edge["target_symbol"] for edge in report["resolved_dynamic_call_edges"]} == (
        NEW_CALL_SYMBOLS
    )
    baseline_pairs = {(edge["symbol"], edge["target_symbol"]) for edge in report["edges"]}
    for edge in report["resolved_dynamic_call_edges"]:
        assert (edge["symbol"], edge["target_symbol"]) not in baseline_pairs
        assert edge["target_symbol"] != "import_module"
        assert edge["activity"] == "NOT_PROVEN"
        assert edge["reachability"] == "NOT_PROVEN"
        assert edge["trading_authority_implied"] is False
        assert edge["binding_resolution"] == "LITERAL_IMPORT_MODULE"
    assert {edge["target_symbol"] for edge in report["resolved_baseline_unresolved_edges"]} == (
        BASELINE_ALIAS_SYMBOLS
    )
    for edge in report["edges"]:
        if edge["target_symbol"] in BASELINE_ALIAS_SYMBOLS:
            assert edge["target_file"] is None


def test_pinned_projection_is_schema_complete_and_depth_limited(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seen: list[int] = []

    def spy(*args, **kwargs):
        seen.append(kwargs["max_depth"])
        return original(*args, **kwargs)

    original = ghv_projection_v1.traverse_forensic_graph_v1
    monkeypatch.setattr(ghv_projection_v1, "traverse_forensic_graph_v1", spy)
    report = run_ghv_master_v2_current_tree_adapter_v1(
        repo_root=ROOT,
        commit_sha=CURRENT_ORIGIN_MAIN_SHA,
        tree_sha=CURRENT_ORIGIN_MAIN_TREE,
    )
    projection = report["ghv_projection"]
    assert projection["status"] == "PROJECTED"
    assert projection["rejected_count"] == 0
    assert projection["edge_count"] == BASELINE_EDGE_COUNT + 6
    assert projection["max_depth_enforced"] == 1
    assert projection["graph_neighborhood_is_runtime_reachability"] is False
    assert projection["trading_authority_implied"] is False
    assert seen
    assert set(seen) == {1}
    for edge in projection["edges"]:
        assert edge["source_native_id"]
        assert edge["target_native_id"]
        assert edge["edge_id"].startswith("calls:")
        assert edge["typed_edge"]["edge_type"] == "CALLS"
        assert isinstance(edge["causal_traversal_eligible"], bool)
        assert edge["trading_authority_implied"] is False
        assert edge["activity"] == "NOT_PROVEN"
        assert edge["runtime_reachability"] == "NOT_PROVEN"
        assert edge["current_sha"] == CURRENT_ORIGIN_MAIN_SHA
        assert edge["current_tree"] == CURRENT_ORIGIN_MAIN_TREE
    first_ids = [edge["edge_id"] for edge in projection["edges"]]
    again = run_ghv_master_v2_current_tree_adapter_v1(
        repo_root=ROOT,
        commit_sha=CURRENT_ORIGIN_MAIN_SHA,
        tree_sha=CURRENT_ORIGIN_MAIN_TREE,
    )
    assert [edge["edge_id"] for edge in again["ghv_projection"]["edges"]] == first_ids
    cycle = ghv_native_id(
        path=(
            "src/ops/full_core_live_path_composition_root_v1/"
            "current_productive_master_v2_runtime_cycle_v1.py"
        ),
        symbol="run_current_productive_master_v2_runtime_cycle_v1",
    )
    replay = ghv_native_id(
        path="src/trading/master_v2/integrated_offline_trading_logic_replay_v1.py",
        symbol="run_integrated_offline_trading_logic_replay_v1",
    )
    transition = ghv_native_id(
        path="src/trading/master_v2/double_play_state.py",
        symbol="transition_state",
    )
    forward_cycle = set(
        report["ghv_depth_1"]["forward"]["productive_master_v2_runtime_cycle"][
            "reachable_native_ids"
        ]
    )
    forward_replay = set(
        report["ghv_depth_1"]["forward"]["integrated_master_v2_replay"]["reachable_native_ids"]
    )
    reverse_transition = set(
        report["ghv_depth_1"]["reverse"]["double_play_transition_state"]["reachable_native_ids"]
    )
    assert transition not in forward_cycle
    assert replay in forward_cycle
    assert transition in forward_replay
    for symbol in NEW_CALL_SYMBOLS:
        target = next(
            edge["target_native_id"]
            for edge in projection["edges"]
            if edge["target_symbol"] == symbol
        )
        assert target in forward_replay
        assert target not in forward_cycle
    assert replay in reverse_transition
    assert cycle not in reverse_transition
    with pytest.raises(ProjectionRejected) as depth_two:
        traverse_projected_graph_v1(
            nodes=projection["nodes"],
            edges=projection["edges"],
            origin_native_id=cycle,
            direction="FORWARD",
            max_depth=2,
        )
    assert depth_two.value.reason == "DEPTH_LIMIT_REJECTED"
    with pytest.raises(ProjectionRejected) as depth_default:
        traverse_projected_graph_v1(
            nodes=projection["nodes"],
            edges=projection["edges"],
            origin_native_id=cycle,
            direction="REVERSE",
            max_depth=32,
        )
    assert depth_default.value.reason == "DEPTH_LIMIT_REJECTED"


def test_missing_schema_field_fails_before_traversal(monkeypatch: pytest.MonkeyPatch) -> None:
    def boom(*_args, **_kwargs):
        raise AssertionError("ghv traversal invoked")

    monkeypatch.setattr(ghv_projection_v1, "traverse_forensic_graph_v1", boom)
    with pytest.raises(ProjectionRejected) as exc:
        traverse_projected_graph_v1(
            nodes=[{"source_native_id": "a.py::a"}],
            edges=[{"source_native_id": "a.py::a", "edge_id": "x"}],
            origin_native_id="a.py::a",
            direction="FORWARD",
            max_depth=1,
        )
    assert exc.value.reason.startswith("GHV_SCHEMA_FIELD_ABSENT")


def test_literal_bindings_resolve_only_unique_calls(tmp_path: Path) -> None:
    commit, tree = _commit_named_fixture(
        tmp_path,
        _replay_header()
        + (
            "    bound = importlib.import_module('trading.master_v2.sample_binding_v1')\n"
            "    bound.proven_target()\n"
            "    bound.missing_target()\n"
            "    alias = bound.proven_target\n"
            "    alias()\n"
            "    computed = 'trading.master_v2.' + 'sample_binding_v1'\n"
            "    other = importlib.import_module(computed)\n"
            "    other.proven_target()\n"
        ),
        "def proven_target():\n    return 1\n",
    )
    report = extract_bounded_anchor_edges_v1(repo_root=tmp_path, commit_sha=commit, tree_sha=tree)
    assert [item["module_literal"] for item in report["dynamic_binding_candidates"]] == [
        "trading.master_v2.sample_binding_v1"
    ]
    resolved = report["resolved_dynamic_call_edges"]
    assert len(resolved) == 1
    assert resolved[0]["target_symbol"] == "proven_target"
    assert len(resolved[0]["call_lines"]) == 2
    assert "import_module" not in {edge["target_symbol"] for edge in report["edges"]}
    assert "import_module" not in {edge["target_symbol"] for edge in resolved}
    reasons = {item["reason"] for item in report["unresolved_dynamic_bindings"]}
    assert "SYMBOL_ABSENT" in reasons
    assert "COMPUTED_MODULE_NAME" in reasons
    assert all(
        item["status"] == "UNRESOLVED_DYNAMIC_BINDING"
        for item in report["unresolved_dynamic_bindings"]
    )


def test_duplicate_symbol_and_rebinding_stay_unresolved(tmp_path: Path) -> None:
    commit, tree = _commit_named_fixture(
        tmp_path,
        _replay_header()
        + (
            "    bound = importlib.import_module('trading.master_v2.sample_binding_v1')\n"
            "    bound = importlib.import_module('trading.master_v2.sample_binding_v1')\n"
            "    bound.proven_target()\n"
            "    once = importlib.import_module('trading.master_v2.sample_binding_v1')\n"
            "    once.proven_target()\n"
        ),
        "def proven_target():\n    return 1\n\ndef proven_target():\n    return 2\n",
    )
    report = extract_bounded_anchor_edges_v1(repo_root=tmp_path, commit_sha=commit, tree_sha=tree)
    assert report["resolved_dynamic_call_edges"] == []
    reasons = {item["reason"] for item in report["unresolved_dynamic_bindings"]}
    assert "BINDING_NOT_UNIQUE" in reasons
    assert "SYMBOL_NOT_UNIQUE" in reasons


def test_import_module_is_not_executed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    commit, tree = _commit_named_fixture(
        tmp_path,
        _replay_header()
        + (
            "    bound = importlib.import_module('trading.master_v2.sample_binding_v1')\n"
            "    bound.proven_target()\n"
        ),
        "def proven_target():\n    return 1\n",
    )

    def boom(*_args, **_kwargs):
        raise AssertionError("import_module executed")

    monkeypatch.setattr(importlib, "import_module", boom)
    before = set(sys.modules)
    report = extract_bounded_anchor_edges_v1(repo_root=tmp_path, commit_sha=commit, tree_sha=tree)
    assert report["resolved_dynamic_call_edges"][0]["target_symbol"] == "proven_target"
    added = set(sys.modules) - before
    assert all("sample_binding_v1" not in name for name in added)


def test_dirty_literal_does_not_enter_dynamic_edges(tmp_path: Path) -> None:
    commit, tree = _commit_named_fixture(
        tmp_path,
        _replay_header()
        + (
            "    bound = importlib.import_module('trading.master_v2.sample_binding_v1')\n"
            "    bound.proven_target()\n"
        ),
        "def proven_target():\n    return 1\n",
    )
    replay = tmp_path / "src/trading/master_v2/integrated_offline_trading_logic_replay_v1.py"
    replay.write_text(
        replay.read_text(encoding="utf-8") + "    dirty = importlib.import_module('os')\n",
        encoding="utf-8",
    )
    report = extract_bounded_anchor_edges_v1(repo_root=tmp_path, commit_sha=commit, tree_sha=tree)
    literals = [item["module_literal"] for item in report["dynamic_binding_candidates"]]
    assert literals == ["trading.master_v2.sample_binding_v1"]
    assert "os" not in literals


def test_adapter_sources_do_not_hardcode_binding_modules() -> None:
    text = "\n".join(path.read_text(encoding="utf-8") for path in ADAPTER_DIR.glob("*.py"))
    for module_name in LITERAL_MODULES:
        assert module_name not in text
    assert "EXECUTION_AUTHORITY" in text
    assert "max_depth=1" in text
    assert "max_depth=32" not in text
