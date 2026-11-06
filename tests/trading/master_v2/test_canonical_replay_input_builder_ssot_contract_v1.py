"""Static SSOT contract: single productive IntegratedOfflineReplayInputV1 builder."""

from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
SRC_ROOT = REPO_ROOT / "src"

_OWNER_MODULE = REPO_ROOT / "src/trading/master_v2/integrated_offline_trading_logic_replay_v1.py"
_PRODUCTIVE_SOURCE_ADAPTERS = (
    REPO_ROOT / "src/backtest/mv2_research_wiring_v1.py",
    REPO_ROOT / "src/trading/master_v2/canonical_core_runtime_integration_bridge_v0.py",
    REPO_ROOT
    / "src/trading/master_v2/integrated_vs_scenario_replay_full_system_parity_harness_v0.py",
)
_PUBLIC_BUILDER_NAME = "build_integrated_offline_replay_input_v1"
_INPUT_TYPE_NAME = "IntegratedOfflineReplayInputV1"
_AUTHORIZED_CONSTRUCTOR_REL_PATH = (
    "src/trading/master_v2/integrated_offline_trading_logic_replay_v1.py"
)
_TEST_ONLY_HELPER = (
    REPO_ROOT / "tests/trading/master_v2/test_integrated_offline_trading_logic_replay_v1.py"
)


@dataclass(frozen=True, order=True)
class DirectReplayInputConstructionHit:
    relative_path: str
    lineno: int
    enclosing_function: str

    def report_line(self) -> str:
        return f"{self.relative_path}:{self.lineno} in {self.enclosing_function}"


def _call_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return None


def _parent_map(tree: ast.AST) -> dict[ast.AST, ast.AST]:
    parents: dict[ast.AST, ast.AST] = {}
    for parent in ast.walk(tree):
        for child in ast.iter_child_nodes(parent):
            parents[child] = parent
    return parents


def _enclosing_function_name(node: ast.AST, parents: dict[ast.AST, ast.AST]) -> str:
    current: ast.AST | None = node
    while current is not None:
        if isinstance(current, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return current.name
        if isinstance(current, ast.Module):
            return "<module>"
        current = parents.get(current)
    return "<module>"


def _function_defs_by_name(tree: ast.AST) -> dict[str, ast.FunctionDef | ast.AsyncFunctionDef]:
    found: dict[str, ast.FunctionDef | ast.AsyncFunctionDef] = {}
    for node in tree.body if isinstance(tree, ast.Module) else []:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            found[node.name] = node
    return found


def _direct_input_constructions(tree: ast.AST) -> list[ast.Call]:
    hits: list[ast.Call] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and _call_name(node.func) == _INPUT_TYPE_NAME:
            hits.append(node)
    return hits


def _builder_calls(tree: ast.AST) -> list[ast.Call]:
    hits: list[ast.Call] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and _call_name(node.func) == _PUBLIC_BUILDER_NAME:
            hits.append(node)
    return hits


def collect_direct_replay_input_constructions(
    *,
    scan_root: Path,
    path_root: Path,
) -> list[DirectReplayInputConstructionHit]:
    """AST-scan ``scan_root`` for direct IntegratedOfflineReplayInputV1 constructions."""
    hits: list[DirectReplayInputConstructionHit] = []
    for path in sorted(p for p in scan_root.rglob("*.py") if p.is_file()):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        parents = _parent_map(tree)
        rel = path.resolve().relative_to(path_root.resolve()).as_posix()
        for call in _direct_input_constructions(tree):
            hits.append(
                DirectReplayInputConstructionHit(
                    relative_path=rel,
                    lineno=int(getattr(call, "lineno", 0) or 0),
                    enclosing_function=_enclosing_function_name(call, parents),
                )
            )
    return sorted(hits)


def authorized_direct_replay_input_constructions(
    hits: list[DirectReplayInputConstructionHit],
) -> list[DirectReplayInputConstructionHit]:
    return [
        hit
        for hit in hits
        if hit.relative_path == _AUTHORIZED_CONSTRUCTOR_REL_PATH
        and hit.enclosing_function == _PUBLIC_BUILDER_NAME
    ]


def unauthorized_direct_replay_input_constructions(
    hits: list[DirectReplayInputConstructionHit],
) -> list[DirectReplayInputConstructionHit]:
    authorized = set(authorized_direct_replay_input_constructions(hits))
    return [hit for hit in hits if hit not in authorized]


def assert_exactly_one_authorized_src_wide_productive_direct_replay_input_constructor(
    *,
    scan_root: Path | None = None,
    path_root: Path | None = None,
) -> DirectReplayInputConstructionHit:
    """Enforce PRODUCTIVE_DIRECT_REPLAY_INPUT_CONSTRUCTOR_COUNT=1 across scan_root."""
    root = scan_root if scan_root is not None else SRC_ROOT
    base = path_root if path_root is not None else REPO_ROOT
    hits = collect_direct_replay_input_constructions(scan_root=root, path_root=base)
    unauthorized = unauthorized_direct_replay_input_constructions(hits)
    assert not unauthorized, (
        "unauthorized productive IntegratedOfflineReplayInputV1 constructions:\n"
        + "\n".join(hit.report_line() for hit in unauthorized)
    )
    authorized = authorized_direct_replay_input_constructions(hits)
    assert len(authorized) == 1, (
        "PRODUCTIVE_DIRECT_REPLAY_INPUT_CONSTRUCTOR_COUNT must be 1; "
        f"found {len(authorized)} authorized hit(s): "
        + ", ".join(hit.report_line() for hit in authorized)
    )
    return authorized[0]


def test_public_builder_is_only_productive_direct_construction_authority_v1() -> None:
    tree = ast.parse(_OWNER_MODULE.read_text(encoding="utf-8"))
    defs = _function_defs_by_name(tree)
    assert _PUBLIC_BUILDER_NAME in defs

    builder_node = defs[_PUBLIC_BUILDER_NAME]
    constructions_in_builder = _direct_input_constructions(builder_node)
    assert len(constructions_in_builder) == 1

    all_constructions = _direct_input_constructions(tree)
    assert len(all_constructions) == 1
    assert all_constructions[0] is constructions_in_builder[0]


def test_productive_source_adapters_do_not_construct_replay_input_directly_v1() -> None:
    for path in _PRODUCTIVE_SOURCE_ADAPTERS:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        direct = _direct_input_constructions(tree)
        assert direct == [], f"{path.relative_to(REPO_ROOT)} still constructs {_INPUT_TYPE_NAME}"


def test_productive_source_adapters_delegate_to_public_builder_v1() -> None:
    for path in _PRODUCTIVE_SOURCE_ADAPTERS:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        calls = _builder_calls(tree)
        assert calls, f"{path.relative_to(REPO_ROOT)} missing call to {_PUBLIC_BUILDER_NAME}"


def test_test_only_helper_is_not_classified_as_productive_authority_v1() -> None:
    """Test helpers may construct fixtures; they are outside productive authority count."""
    tree = ast.parse(_TEST_ONLY_HELPER.read_text(encoding="utf-8"))
    # Presence of a test helper construction must not affect productive authority SSOT.
    assert _TEST_ONLY_HELPER.as_posix().endswith(
        "tests/trading/master_v2/test_integrated_offline_trading_logic_replay_v1.py"
    )
    sole = assert_exactly_one_authorized_src_wide_productive_direct_replay_input_constructor()
    assert sole.relative_path == _AUTHORIZED_CONSTRUCTOR_REL_PATH
    assert sole.enclosing_function == _PUBLIC_BUILDER_NAME
    # Test helper is optional: if present, ignored for productive authority.
    _ = _direct_input_constructions(tree)


def test_productive_direct_construction_authority_count_is_one_v1() -> None:
    sole = assert_exactly_one_authorized_src_wide_productive_direct_replay_input_constructor()
    assert sole.relative_path == _AUTHORIZED_CONSTRUCTOR_REL_PATH
    assert sole.enclosing_function == _PUBLIC_BUILDER_NAME
    for path in _PRODUCTIVE_SOURCE_ADAPTERS:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        assert _direct_input_constructions(tree) == []
        assert _builder_calls(tree)


def test_src_wide_constructor_scanner_rejects_non_owner_construction_fixture(
    tmp_path: Path,
) -> None:
    rogue = tmp_path / "rogue_replay_input_constructor_v0.py"
    rogue.write_text(
        "def build_rogue_input():\n    return IntegratedOfflineReplayInputV1()\n",
        encoding="utf-8",
    )
    hits = collect_direct_replay_input_constructions(scan_root=tmp_path, path_root=tmp_path)
    assert len(hits) == 1
    assert hits[0].enclosing_function == "build_rogue_input"
    assert unauthorized_direct_replay_input_constructions(hits)
    with pytest.raises(AssertionError, match="unauthorized productive"):
        assert_exactly_one_authorized_src_wide_productive_direct_replay_input_constructor(
            scan_root=tmp_path,
            path_root=tmp_path,
        )
