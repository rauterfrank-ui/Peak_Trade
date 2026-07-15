"""Contract tests for trend_following_v2 canonical wiring map (repo-side SSOT)."""

from __future__ import annotations

import importlib
import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
WIRING_MAP_PATH = REPO_ROOT / "docs/architecture/trend_following_v2_canonical_wiring_v0.json"
MANDATORY_BINDING_KEYS = (
    "capital_risk_sizing",
    "canonical_order_intent",
    "safety_kernel",
    "killswitch",
    "reconciliation",
)


@pytest.fixture(name="wiring_map")
def fixture_wiring_map() -> dict:
    return json.loads(WIRING_MAP_PATH.read_text(encoding="utf-8"))


def test_wiring_map_file_exists_and_schema_version(wiring_map: dict) -> None:
    assert WIRING_MAP_PATH.is_file()
    assert wiring_map["schema_version"] == "trend_following_v2_canonical_wiring_v0"
    assert wiring_map["scope"] == "TREND_FOLLOWING_V2_MANDATORY_BOUNDARY_STATE_FILE_BINDING_REWIRE"


def test_wiring_map_referenced_repo_paths_exist(wiring_map: dict) -> None:
    missing: list[str] = []
    for node in wiring_map["nodes"]:
        owner_path = node["canonical_owner_path"]
        if owner_path.endswith(".py") or owner_path.endswith(".json"):
            if not (REPO_ROOT / owner_path).is_file():
                missing.append(owner_path)
    ref_cfg = wiring_map["mandatory_bindings"]["reference_config_path"]
    tgt_cfg = wiring_map["mandatory_bindings"]["target_config_path"]
    for path in (ref_cfg, tgt_cfg):
        if not (REPO_ROOT / path).is_file():
            missing.append(path)
    for key in MANDATORY_BINDING_KEYS:
        rel = wiring_map["mandatory_bindings"]["subdomains"][key]["state_file_path"]
        if not (REPO_ROOT / rel).is_file():
            missing.append(rel)
    assert missing == [], f"missing_repo_paths:{missing}"


def test_wiring_map_referenced_symbols_importable(wiring_map: dict) -> None:
    failures: list[str] = []
    for node in wiring_map["nodes"]:
        owner_path = node["canonical_owner_path"]
        symbol = node["canonical_symbol"]
        if not owner_path.endswith(".py"):
            continue
        module_path = owner_path.replace("/", ".").removesuffix(".py")
        try:
            mod = importlib.import_module(module_path)
        except ImportError as exc:
            failures.append(f"{module_path}:import_error:{exc}")
            continue
        if not hasattr(mod, symbol):
            failures.append(f"{module_path}.{symbol}:missing")
    assert failures == [], f"symbol_import_failures:{failures}"


def test_wiring_map_mandatory_bindings_complete(wiring_map: dict) -> None:
    bindings = wiring_map["mandatory_bindings"]
    assert bindings["section_key"] == (
        "mv2_research_backtest_mandatory_boundary_state_file_binding_v0"
    )
    for key in MANDATORY_BINDING_KEYS:
        entry = bindings["subdomains"][key]
        assert len(entry["expected_state_file_digest_ref"]) == 64
        assert entry["state_file_path"].startswith(
            "config/research/mv2_backtest_mandatory_boundary_state_files_v0/"
        )


def test_wiring_map_nodes_have_required_fields(wiring_map: dict) -> None:
    required = {
        "stage_id",
        "canonical_owner_path",
        "canonical_symbol",
        "input_contract",
        "output_contract",
        "authority_effect",
        "runtime_effect",
        "existing_tests",
        "required_proof",
    }
    stage_ids = [node["stage_id"] for node in wiring_map["nodes"]]
    assert len(stage_ids) == len(set(stage_ids)), "duplicate_stage_ids"
    for node in wiring_map["nodes"]:
        assert required <= set(node)
        assert node["authority_effect"] == "NONE"
        assert node["runtime_effect"] == "NONE"


def test_wiring_map_proof_tests_exist(wiring_map: dict) -> None:
    for rel in wiring_map["proof_tests"]:
        assert (REPO_ROOT / rel).is_file(), rel
