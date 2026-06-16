"""Static contract tests for Master V2 Double Play Pure Stack Readiness Map (v0).

Machine-anchors the canonical pure-stack module/test inventory and non-authorizing
boundaries from the readiness map. Protects inventory legibility without importing
trading runtime modules or authorizing execution — static file-content tests only.

SLICE-MV2-2: static crosslink guard for
``docs/ops/CI_AUDIT_KNOWN_ISSUES.md`` Master V2 / Double Play Read-only Alignment
Inventory RC v0 meta-index (read-only; non-authorizing).
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SPECS = REPO_ROOT / "docs" / "ops" / "specs"
CI_AUDIT = REPO_ROOT / "docs" / "ops" / "CI_AUDIT_KNOWN_ISSUES.md"
REMOTE_RUNTIME_DOCS_GUARD = (
    REPO_ROOT / "tests" / "ops" / "test_remote_runtime_contract_docs_guard_v0.py"
)
THIS_MODULE = Path(__file__).name
SRC_MASTER_V2 = REPO_ROOT / "src" / "trading" / "master_v2"
TESTS_MASTER_V2 = REPO_ROOT / "tests" / "trading" / "master_v2"

MV2_READONLY_ALIGNMENT_RC_HEADING = (
    "## Master V2 / Double Play Read-only Alignment Inventory RC v0 — docs reflection v0"
)
MV2_READONLY_ALIGNMENT_RC_BLOCK_ANCHOR = (
    "MASTER_V2_DOUBLE_PLAY_READONLY_ALIGNMENT_INVENTORY_RC_V0=true"
)
MV2_READONLY_ALIGNMENT_RC_EXPECTED: dict[str, str] = {
    "MASTER_V2_DOUBLE_PLAY_READONLY_ALIGNMENT_INVENTORY_RC_V0": "true",
    "SLICE_MV2_0_EXTERNAL_INVENTORY_COMPLETE": "true",
    "SLICE_MV2_1_DOCS_REFLECTION_ONLY": "true",
    "COMPLETED_ARCS_MASTER_V2_COMPATIBLE": "true",
    "MASTER_V2_PRIORITY_PRESERVED": "true",
    "RUNTIME_PRODUCER_PARKING_LIFTED": "false",
    "PREFLIGHT_REMAINS_BLOCKED": "true",
    "STOP_IDLE_PRESERVED": "true",
    "NO_RUNTIME": "true",
    "NO_PAPER_SHADOW_TESTNET_LIVE": "true",
    "MASTER_V2_LOGIC_CHANGED": "false",
    "DOUBLE_PLAY_LOGIC_CHANGED": "false",
    "TRADING_AUTHORITY_CHANGED": "false",
    "PARALLEL_MASTER_V2_ALIGNMENT_INDEX_CREATED": "false",
    "FOLLOWUP_DOCS_SLICE_NEEDED": "false",
    "FOLLOWUP_TEST_GUARD_NEEDED": "false",
    "RUNTIME_STARTED": "false",
    "SCHEDULER_STARTED": "false",
    "LIVE_TOUCHED": "false",
    "READY_FOR_OPERATOR_ARMING": "false",
}
FENCED_BLOCK_RX = re.compile(r"```[^\n]*\n(.*?)```", re.DOTALL)

PURE_STACK_MAP = SPECS / "MASTER_V2_DOUBLE_PLAY_PURE_STACK_READINESS_MAP_V0.md"
TRADING_LOGIC_MANIFEST = SPECS / "MASTER_V2_DOUBLE_PLAY_TRADING_LOGIC_MANIFEST_V0.md"
CAPITAL_SLOT_CONTRACT = SPECS / "MASTER_V2_DOUBLE_PLAY_CAPITAL_SLOT_RATCHET_RELEASE_CONTRACT_V0.md"
FUTURES_INPUT_READ_MODEL = SPECS / "MASTER_V2_DOUBLE_PLAY_FUTURES_INPUT_READ_MODEL_V0.md"
FUTURES_INPUT_PRODUCER_CONTRACT = (
    SPECS / "MASTER_V2_DOUBLE_PLAY_FUTURES_INPUT_PRODUCER_CONTRACT_V0.md"
)

TRADING_LOGIC_MANIFEST_NAME = "MASTER_V2_DOUBLE_PLAY_TRADING_LOGIC_MANIFEST_V0.md"
CAPITAL_SLOT_CONTRACT_NAME = "MASTER_V2_DOUBLE_PLAY_CAPITAL_SLOT_RATCHET_RELEASE_CONTRACT_V0.md"

INVENTORY_MODULES: tuple[str, ...] = (
    "double_play_futures_input.py",
    "double_play_state.py",
    "double_play_survival.py",
    "double_play_suitability.py",
    "double_play_capital_slot.py",
    "double_play_composition.py",
)

INVENTORY_TESTS: tuple[str, ...] = (
    "test_double_play_futures_input.py",
    "test_double_play_state.py",
    "test_double_play_survival.py",
    "test_double_play_suitability.py",
    "test_double_play_capital_slot.py",
    "test_double_play_composition.py",
    "test_double_play_pure_stack_contract.py",
)


def _read(path: Path) -> str:
    assert path.is_file(), f"missing canonical doc: {path}"
    return path.read_text(encoding="utf-8")


def _plain(path: Path) -> str:
    text = _read(path)
    text = text.replace("&#47;", "/")
    return re.sub(r"[`*]", "", text)


def test_pure_stack_readiness_map_exists_v0() -> None:
    assert PURE_STACK_MAP.is_file()


def test_pure_stack_map_master_v2_double_play_and_readiness_v0() -> None:
    text = _plain(PURE_STACK_MAP)
    lowered = text.lower()
    assert "master v2" in lowered
    assert "double play" in lowered
    assert "readiness map" in lowered
    assert "pure stack readiness is not trading readiness" in lowered


def test_pure_stack_map_module_and_test_inventory_semantics_v0() -> None:
    text = _plain(PURE_STACK_MAP)
    lowered = text.lower()
    assert "inventory of the current pure double play stack" in lowered
    assert "modules + tests" in lowered
    assert "src/trading/master_v2" in text
    assert "tests/trading/master_v2" in text
    assert "cross-module contract tests" in lowered


def test_pure_stack_map_referenced_src_modules_exist_v0() -> None:
    text = _read(PURE_STACK_MAP)
    for module_name in INVENTORY_MODULES:
        assert module_name in text
        assert (SRC_MASTER_V2 / module_name).is_file(), module_name


def test_pure_stack_map_referenced_behavior_tests_exist_v0() -> None:
    text = _read(PURE_STACK_MAP)
    for test_name in INVENTORY_TESTS:
        assert test_name in text
        assert (TESTS_MASTER_V2 / test_name).is_file(), test_name


def test_pure_stack_map_pure_not_runtime_and_live_authorization_false_v0() -> None:
    text = _plain(PURE_STACK_MAP)
    lowered = text.lower()
    assert "runtime / execution / trading readiness" in lowered
    assert "not implied here" in lowered
    assert "live_authorization remains false" in lowered
    assert "live_authorization stays false" in lowered
    assert "no runtime state machine" in lowered
    assert "runtime integration" in lowered


def test_pure_stack_map_state_switch_and_kill_all_boundary_v0() -> None:
    text = _plain(PURE_STACK_MAP)
    lowered = text.lower()
    assert "state / dynamic scope" in lowered
    assert "state-switch vs kill-all" in lowered
    assert "kill_all" in lowered or "kill-all" in lowered


def test_pure_stack_map_side_pool_and_capital_slot_boundaries_v0() -> None:
    text = _plain(PURE_STACK_MAP)
    lowered = text.lower()
    assert "side-pool" in lowered or "side pool" in lowered
    assert "capital slot" in lowered
    assert "evaluate_capital_slot_ratchet" in _read(PURE_STACK_MAP)
    assert "evaluate_capital_slot_release" in _read(PURE_STACK_MAP)
    assert "no capital movement" in lowered


def test_pure_stack_map_runtime_separation_blockers_v0() -> None:
    text = _plain(PURE_STACK_MAP)
    lowered = text.lower()
    assert "pure evaluation" in lowered
    assert "hot-path" in lowered or "hot path" in lowered
    assert "eligible_model_only" in lowered
    assert "adapters, sessions, evidence, and gate closures belong outside" in lowered


def test_pure_stack_map_crosslinks_trading_manifest_and_capital_slot_v0() -> None:
    text = _read(PURE_STACK_MAP)
    assert TRADING_LOGIC_MANIFEST_NAME in text
    assert CAPITAL_SLOT_CONTRACT_NAME in text
    assert TRADING_LOGIC_MANIFEST.is_file()
    assert CAPITAL_SLOT_CONTRACT.is_file()


def test_pure_stack_map_crosslinks_futures_input_contracts_v0() -> None:
    text = _read(PURE_STACK_MAP)
    assert FUTURES_INPUT_READ_MODEL.name in text
    assert FUTURES_INPUT_PRODUCER_CONTRACT.name in text
    assert FUTURES_INPUT_READ_MODEL.is_file()
    assert FUTURES_INPUT_PRODUCER_CONTRACT.is_file()


def test_pure_stack_map_producer_contract_test_anchors_v0() -> None:
    text = _read(PURE_STACK_MAP)
    assert "test_contract_32" in text
    assert "`37`" in text or "test_contract_37" in text
    assert "runtime handle" in text.lower()
    assert "live_authorization" in text


def test_pure_stack_map_non_authorizing_posture_v0() -> None:
    text = _plain(PURE_STACK_MAP)
    lowered = text.lower()
    assert "non-authorizing" in lowered
    assert "testnet and live remain unauthorized" in lowered


def test_pure_stack_map_eligible_model_only_not_trading_permission_v0() -> None:
    text = _plain(PURE_STACK_MAP)
    assert "ELIGIBLE_MODEL_ONLY" in _read(PURE_STACK_MAP)
    assert "not trading permission" in text.lower()


def test_pure_stack_map_does_not_duplicate_decision_authority_map_owner_v0() -> None:
    """Pure stack map is inventory-focused; decision authority map has separate ops owner."""
    authority_map_test = (
        REPO_ROOT
        / "tests"
        / "ops"
        / "test_master_v2_decision_authority_map_static_crosslink_contract_v0.py"
    )
    assert authority_map_test.is_file()
    map_text = _read(PURE_STACK_MAP)
    assert "MASTER_V2_DECISION_AUTHORITY_MAP_V1.md" not in map_text
    assert "inventory" in map_text.lower()


def _ci_audit_text() -> str:
    assert CI_AUDIT.is_file()
    return CI_AUDIT.read_text(encoding="utf-8")


def _fenced_blocks(text: str) -> list[str]:
    return [block.strip() for block in FENCED_BLOCK_RX.findall(text)]


def _block_containing(text: str, anchor: str) -> str:
    for block in _fenced_blocks(text):
        if anchor in block:
            return block
    raise AssertionError(f"missing fenced machine-line block containing {anchor!r}")


def _machine_line_values(block: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in block.splitlines():
        stripped = line.strip()
        if "=" not in stripped or stripped.startswith("#"):
            continue
        key, _, value = stripped.partition("=")
        if key and value:
            values[key.strip()] = value.strip()
    return values


def _mv2_readonly_alignment_rc_section(text: str) -> str:
    start = text.find(MV2_READONLY_ALIGNMENT_RC_HEADING)
    assert start != -1, "missing Master V2 readonly alignment RC v0 section"
    return text[start:]


def test_ci_audit_mv2_readonly_alignment_rc_section_present_v0() -> None:
    text = _ci_audit_text()
    section = _mv2_readonly_alignment_rc_section(text)
    assert "SLICE-MV2-1" in section
    assert "SLICE-MV2-2" in section
    assert "Docs-only reflection" in section or "docs-only reflection" in section.lower()
    assert "MASTER_V2_REUSE_REWIRE_INVENTORY_V1.md" in section
    assert "MARKET_SURFACE_V0.md" in section
    assert "parallel alignment index" in section.lower()
    assert "this PR" in section or "SLICE-MV2-1" in section
    assert "test_master_v2_" in section
    assert THIS_MODULE not in section


def test_ci_audit_mv2_readonly_alignment_rc_machine_lines_v0() -> None:
    text = _ci_audit_text()
    block = _block_containing(text, MV2_READONLY_ALIGNMENT_RC_BLOCK_ANCHOR)
    values = _machine_line_values(block)
    missing = set(MV2_READONLY_ALIGNMENT_RC_EXPECTED) - values.keys()
    assert not missing, f"missing MV2 readonly alignment RC keys: {sorted(missing)}"
    for key, expected in MV2_READONLY_ALIGNMENT_RC_EXPECTED.items():
        assert values[key] == expected, f"{key}={values[key]!r} expected {expected!r}"


def test_ci_audit_mv2_readonly_alignment_slice_mv2_2_guard_owner_v0() -> None:
    section = _mv2_readonly_alignment_rc_section(_ci_audit_text())
    assert "SLICE-MV2-2" in section
    assert "Tests-ops" in section or "tests-ops" in section.lower()
    assert "complete" in section.lower()
    assert "#3937" in section or "3937" in section
    assert "test_master_v2_" in section
    assert "MASTER_V2_LOGIC_IMPLEMENTATION" in section
    assert "BLOCKED" in section


def test_pure_stack_map_reciprocal_remote_runtime_docs_guard_v0() -> None:
    guard_text = REMOTE_RUNTIME_DOCS_GUARD.read_text(encoding="utf-8")
    assert THIS_MODULE in guard_text
    owner_text = Path(__file__).read_text(encoding="utf-8")
    assert "test_remote_runtime_contract_docs_guard_v0.py" in owner_text
