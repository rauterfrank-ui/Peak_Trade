"""Static guard: allow_test_scope_event_injection must not default True; provenance required."""

from __future__ import annotations

import ast
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

REPLAY_OWNER = (
    REPO_ROOT / "src" / "trading" / "master_v2" / "offline_double_play_scenario_replay_v0.py"
)
TESTNET_WIRING_OWNER = (
    REPO_ROOT / "src" / "ops" / "bounded_master_v2_testnet_completion_path_wiring_v0.py"
)

# Explicit True only at known offline/test harness factories (never productive runtime).
SRC_ALLOW_TRUE_ALLOWLIST = frozenset(
    {
        "src/trading/master_v2/offline_double_play_scenario_replay_v0.py",
        "src/ops/offline_master_v2_replay_six_node_validation_graph_binding_v0.py",
        "src/trading/master_v2/integrated_vs_scenario_replay_full_system_parity_harness_v0.py",
    }
)

FORBIDDEN_PRODUCTIVE_PREFIXES = (
    "src/execution/",
    "src/runtime/",
    "scripts/live",
    "scripts/ops/run_testnet",
)


def _iter_py_files(root: Path) -> list[Path]:
    return sorted(p for p in root.rglob("*.py") if p.is_file())


def _dataclass_default_for_field(tree: ast.AST, field_name: str) -> object | None:
    for node in ast.walk(tree):
        if not isinstance(node, ast.AnnAssign):
            continue
        target = node.target
        if not isinstance(target, ast.Name) or target.id != field_name:
            continue
        if node.value is None:
            return None
        if isinstance(node.value, ast.Constant):
            return node.value.value
        return node.value
    return None


def _kw_true_assignments(tree: ast.AST, kw_name: str) -> list[ast.AST]:
    hits: list[ast.AST] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            for kw in node.keywords:
                if (
                    kw.arg == kw_name
                    and isinstance(kw.value, ast.Constant)
                    and kw.value.value is True
                ):
                    hits.append(node)
        if isinstance(node, ast.keyword):
            if (
                node.arg == kw_name
                and isinstance(node.value, ast.Constant)
                and node.value.value is True
            ):
                hits.append(node)
    return hits


def test_replay_input_default_is_false() -> None:
    tree = ast.parse(REPLAY_OWNER.read_text(encoding="utf-8"))
    assert _dataclass_default_for_field(tree, "allow_test_scope_event_injection") is False


def test_testnet_market_input_default_is_false() -> None:
    tree = ast.parse(TESTNET_WIRING_OWNER.read_text(encoding="utf-8"))
    assert _dataclass_default_for_field(tree, "allow_test_scope_event_injection") is False


def test_testnet_build_replay_input_does_not_hardcode_true() -> None:
    source = TESTNET_WIRING_OWNER.read_text(encoding="utf-8")
    tree = ast.parse(source)
    fn = None
    for node in tree.body:
        if (
            isinstance(node, ast.FunctionDef)
            and node.name == "build_replay_input_from_testnet_market_input"
        ):
            fn = node
            break
    assert fn is not None
    for call in ast.walk(fn):
        if not isinstance(call, ast.Call):
            continue
        for kw in call.keywords:
            if kw.arg == "allow_test_scope_event_injection":
                assert not (isinstance(kw.value, ast.Constant) and kw.value.value is True), (
                    "build_replay_input_from_testnet_market_input must not hardcode True"
                )


def test_src_explicit_true_only_on_allowlisted_offline_surfaces() -> None:
    violations: list[str] = []
    for path in _iter_py_files(REPO_ROOT / "src"):
        rel = path.relative_to(REPO_ROOT).as_posix()
        text = path.read_text(encoding="utf-8")
        if "allow_test_scope_event_injection=True" not in text:
            continue
        if rel in SRC_ALLOW_TRUE_ALLOWLIST:
            continue
        violations.append(rel)
    assert not violations, f"unexpected src True opt-in callsites: {violations}"


def test_no_productive_runtime_live_true_opt_in() -> None:
    violations: list[str] = []
    scan_roots = [REPO_ROOT / "src", REPO_ROOT / "scripts"]
    for root in scan_roots:
        if not root.is_dir():
            continue
        for path in _iter_py_files(root):
            rel = path.relative_to(REPO_ROOT).as_posix()
            if not any(rel.startswith(prefix) for prefix in FORBIDDEN_PRODUCTIVE_PREFIXES):
                continue
            text = path.read_text(encoding="utf-8")
            if "allow_test_scope_event_injection=True" in text:
                violations.append(rel)
    assert not violations, f"productive True opt-in forbidden: {violations}"


def test_replay_owner_requires_provenance_validation() -> None:
    text = REPLAY_OWNER.read_text(encoding="utf-8")
    assert "validate_offline_scenario_tick_provenance_v1" in text
    assert "scenario_tick_provenance_required" in text
    assert "OfflineScenarioTickProvenanceV1" in text
