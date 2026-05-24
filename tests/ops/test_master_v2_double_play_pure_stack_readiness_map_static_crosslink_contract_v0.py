"""Static contract tests for Master V2 Double Play Pure Stack Readiness Map (v0).

Machine-anchors the canonical pure-stack module/test inventory and non-authorizing
boundaries from the readiness map. Protects inventory legibility without importing
trading runtime modules or authorizing execution — static file-content tests only.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SPECS = REPO_ROOT / "docs" / "ops" / "specs"
SRC_MASTER_V2 = REPO_ROOT / "src" / "trading" / "master_v2"
TESTS_MASTER_V2 = REPO_ROOT / "tests" / "trading" / "master_v2"

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
