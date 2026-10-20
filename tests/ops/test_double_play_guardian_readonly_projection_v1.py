"""Tests for the Double Play guardian read-only gap projection."""

from __future__ import annotations

import ast
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.ops.double_play_guardian_readonly_projection_v1.constants_v1 import (
    EXPECTED_BASELINE_SHA,
    EXPECTED_BASELINE_TREE,
    FORBIDDEN_OUTPUT_KEYS,
)
from scripts.ops.double_play_guardian_readonly_projection_v1.project_v1 import (
    ProjectionInputsV1,
    load_projection_inputs_v1,
    project_double_play_guardian_gap_v1,
)

PACKAGE = ROOT / "scripts/ops/double_play_guardian_readonly_projection_v1"
REAL_HEADER = Path(
    "/Users/frnkhrz/Peak_Trade_Run_Evidence/guardian_current_m15_97c8c954/preflight_record.v1.json"
)


def _header(
    path: Path, *, head: str = EXPECTED_BASELINE_SHA, tree: str = EXPECTED_BASELINE_TREE
) -> None:
    path.write_text(
        json.dumps(
            {
                "authority": "NONE",
                "isolated": {"head": head, "tree": tree},
                "tool_identities": {
                    "GHV": "scripts.ops.ghv_forensic_whole_system_crosswalk_v1",
                    "GRAPH": "scripts.ops.ghv_forensic_whole_system_causal_integration_v1",
                },
            }
        ),
        encoding="utf-8",
    )


def _load(tmp_path: Path, **kwargs: object):
    header = tmp_path / "header.json"
    _header(header)
    sha = str(kwargs.pop("current_sha", EXPECTED_BASELINE_SHA))
    tree = str(kwargs.pop("current_tree", EXPECTED_BASELINE_TREE))
    claims = kwargs.pop("claims", None)
    return load_projection_inputs_v1(
        repository_root=ROOT,
        snapshot_header_path=header,
        current_sha=sha,
        current_tree=tree,
        claims=claims if isinstance(claims, dict) else None,
    )


def _assert_gap(report: dict) -> None:
    assert report["PROJECTION_STATUS"] == "GAP_REPORTED"
    assert report["REJECTION_REASONS"] == []
    assert report["DOMAIN"] == "DOUBLE_PLAY"
    assert report["INTERNAL_COMPONENT"] == "DYNAMIC_SCOPE"
    assert report["AUTHORITY"] == "NONE"
    assert report["TRADING_AUTHORITY"] == "NONE"
    assert report["SAFETY_AUTHORITY"] == "NONE"
    assert report["EXECUTION_AUTHORITY"] == "NONE"
    assert report["DOUBLE_PLAY_GHV_READY"] is False
    assert report["DOUBLE_PLAY_CURRENT_CAUSAL_GRAPH_READY"] is False
    assert report["DOUBLE_PLAY_GHOSV_READY"] is False
    assert [row["TOOL_ROLE"] for row in report["TOOL_ROLES"]] == [
        "DOUBLE_PLAY_GHV",
        "DOUBLE_PLAY_CURRENT_CAUSAL_GRAPH",
        "DOUBLE_PLAY_GHOSV",
    ]
    for row in report["TOOL_ROLES"]:
        assert row["READINESS_STATUS"] == "NOT_READY"
        assert row["IMPLEMENTATION_STATUS"] == "NO_IMPLEMENTATION_FOUND"
        assert row["EXECUTION_STATUS"] == "NOT_EXECUTED"
        assert row["DYNAMIC_SCOPE_COVERAGE_STATUS"] == "NOT_PROVEN"
        assert row["AUTHORITY"] == "NONE"
    assert FORBIDDEN_OUTPUT_KEYS.isdisjoint(report)
    assert report["ENTRY_EXIT_EFFECT_EVALUATED"] is False
    assert report["PRODUCTIVE_PERSISTENCE_INFERRED"] is False
    assert report["ABSENT_GRAPH_SYMBOL_IS_ISOLATION_PROOF"] is False
    assert report["OPS_CENSUS_NODE_IS_TRADING_SYMBOL"] is False


def test_valid_baseline_reports_gap(tmp_path: Path) -> None:
    report = project_double_play_guardian_gap_v1(_load(tmp_path))
    _assert_gap(report)
    assert report["BASELINE_SHA"] == EXPECTED_BASELINE_SHA
    assert report["BASELINE_TREE"] == EXPECTED_BASELINE_TREE
    assert report["OWNER_LOCK_STATUS"]["CATEGORY_3_FULL_OWNER_LOCK"] == "LEVEL_3"
    assert report["OWNER_LOCK_STATUS"]["PYTHON_ENFORCEMENT"] == "NOT_CLAIMED"
    assert report["OWNER_LOCK_STATUS"]["GATE_CREATED"] is False
    assert report["GHOSV_GAP_STATUS"] == {
        "MV2-04": "NOT_TESTED",
        "MV2-05": "NOT_TESTED",
        "MV2-06": "NOT_TESTED",
        "MV2-08": "NOT_TESTED",
    }
    assert report["GHOSV_PIN_IS_CURRENT_BASELINE"] is False
    assert report["GHOSV_CODE_PIN"] == "7628005ae495c115ff341d32fa932b7f4642f456"
    assert report["ARCHITECTURE_OBSERVATION"]["INDEPENDENT_DYNAMIC_SCOPE_GUARDIAN"] is False
    assert report["WHOLE_SYSTEM_HEADER_IS_DOMAIN_TOOL"] is False


def test_repeated_output_is_identical(tmp_path: Path) -> None:
    inputs = _load(tmp_path)
    assert project_double_play_guardian_gap_v1(inputs) == project_double_play_guardian_gap_v1(
        inputs
    )


@pytest.mark.parametrize(
    ("sha", "tree", "reason"),
    [
        ("0" * 40, EXPECTED_BASELINE_TREE, "BASELINE_SHA_MISMATCH"),
        (EXPECTED_BASELINE_SHA, "1" * 40, "BASELINE_TREE_MISMATCH"),
    ],
)
def test_baseline_mismatch_rejects(tmp_path: Path, sha: str, tree: str, reason: str) -> None:
    report = project_double_play_guardian_gap_v1(
        _load(tmp_path, current_sha=sha, current_tree=tree)
    )
    assert report["PROJECTION_STATUS"] == "REJECTED"
    assert reason in report["REJECTION_REASONS"]
    assert report["DOUBLE_PLAY_GHV_READY"] is False
    assert report["TOOL_ROLES"][0]["READINESS_STATUS"] == "NOT_READY"


def test_missing_evidence_rejects() -> None:
    report = project_double_play_guardian_gap_v1(
        ProjectionInputsV1(
            current_sha=EXPECTED_BASELINE_SHA,
            current_tree=EXPECTED_BASELINE_TREE,
            ghosv_contract_text=None,
            decision_path_text=None,
            ghosv_constants=None,
            snapshot_header=None,
            ghosv_contract_source="missing-contract",
            decision_path_source="missing-decision",
            ghosv_constants_source="missing-constants",
            snapshot_header_source="missing-header",
            claims={},
        )
    )
    assert report["PROJECTION_STATUS"] == "REJECTED"
    assert "MISSING_REQUIRED_EVIDENCE" in report["REJECTION_REASONS"]
    assert "MISSING_OWNER_LOCK_EVIDENCE" in report["REJECTION_REASONS"]
    assert report["OWNER_LOCK_STATUS"]["CATEGORY_3_FULL_OWNER_LOCK"] == "UNKNOWN"
    assert report["GHOSV_GAP_STATUS"]["MV2-04"] == "UNKNOWN"
    assert report["DOUBLE_PLAY_GHOSV_READY"] is False


def test_missing_lock_rejects(tmp_path: Path) -> None:
    inputs = _load(tmp_path)
    report = project_double_play_guardian_gap_v1(
        ProjectionInputsV1(
            current_sha=inputs.current_sha,
            current_tree=inputs.current_tree,
            ghosv_contract_text="MASTER V2 > DOUBLE PLAY > DYNAMIC SCOPE\nAUTHORITY_TRANSFER=false\n",
            decision_path_text=(
                "DOUBLE_PLAY_INTERNAL_FUNCTIONAL_AREA=true\nDOUBLE_PLAY_SEPARATE_UNIVERSE=false\n"
            ),
            ghosv_constants=inputs.ghosv_constants,
            snapshot_header=inputs.snapshot_header,
            ghosv_contract_source=inputs.ghosv_contract_source,
            decision_path_source=inputs.decision_path_source,
            ghosv_constants_source=inputs.ghosv_constants_source,
            snapshot_header_source=inputs.snapshot_header_source,
            claims={},
        )
    )
    assert report["PROJECTION_STATUS"] == "REJECTED"
    assert "MISSING_OWNER_LOCK_EVIDENCE" in report["REJECTION_REASONS"]
    assert report["OWNER_LOCK_STATUS"]["PYTHON_ENFORCEMENT"] == "NOT_CLAIMED"


@pytest.mark.parametrize(
    ("claims", "reason"),
    [
        ({"authority": "LIVE"}, "UNAUTHORIZED_AUTHORITY_CLAIM"),
        ({"trading_authority": "GRANTED"}, "UNAUTHORIZED_AUTHORITY_CLAIM"),
        ({"dynamic_scope_separate_universe": True}, "UNAUTHORIZED_UNIVERSE_CLAIM"),
        ({"treat_older_ghosv_pin_as_current": True}, "OLDER_GHOSV_PIN_TREATED_AS_CURRENT"),
        (
            {"treat_ops_census_node_as_trading_symbol": True},
            "OPS_CENSUS_NODE_TREATED_AS_TRADING_SYMBOL",
        ),
        ({"treat_catalog_check_as_executed": True}, "CATALOG_CHECK_TREATED_AS_EXECUTED"),
        (
            {"treat_missing_graph_symbol_as_isolation": True},
            "MISSING_GRAPH_SYMBOL_TREATED_AS_ISOLATION_PROOF",
        ),
        (
            {"infer_productive_persistence_from_state_persisted": True},
            "PRODUCTIVE_PERSISTENCE_INFERENCE_REJECTED",
        ),
    ],
)
def test_fail_closed_claims(tmp_path: Path, claims: dict, reason: str) -> None:
    report = project_double_play_guardian_gap_v1(_load(tmp_path, claims=claims))
    assert report["PROJECTION_STATUS"] == "REJECTED"
    assert reason in report["REJECTION_REASONS"]
    assert report["DOUBLE_PLAY_CURRENT_CAUSAL_GRAPH_READY"] is False
    assert "overall_pass" not in report


def test_package_does_not_import_protected_or_tool_runtimes() -> None:
    banned_modules = {
        "trading",
        "execution",
        "risk",
        "scripts.ops.ghosv_master_v2_bounded_context_v1",
        "scripts.ops.ghosv_master_v2_bounded_context_v1.check_v1",
        "scripts.ops.ghv_forensic_whole_system_crosswalk_v1",
        "scripts.ops.ghv_forensic_whole_system_causal_integration_v1",
    }
    for path in PACKAGE.glob("*.py"):
        parsed = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(parsed):
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                names = [node.module or ""]
            else:
                continue
            for name in names:
                assert name not in banned_modules
                assert not name.startswith("trading.")
                assert not name.startswith("execution.")
                assert not name.startswith("risk.")
    before = set(sys.modules)
    import scripts.ops.double_play_guardian_readonly_projection_v1 as projection

    loaded = set(sys.modules) - before
    assert banned_modules.isdisjoint(loaded)
    assert projection.project_double_play_guardian_gap_v1 is project_double_play_guardian_gap_v1


def test_projection_does_not_write_files(tmp_path: Path) -> None:
    header = tmp_path / "header.json"
    _header(header)
    before = {path.relative_to(tmp_path) for path in tmp_path.rglob("*")}
    inputs = load_projection_inputs_v1(
        repository_root=ROOT,
        snapshot_header_path=header,
        current_sha=EXPECTED_BASELINE_SHA,
        current_tree=EXPECTED_BASELINE_TREE,
    )
    project_double_play_guardian_gap_v1(inputs)
    after = {path.relative_to(tmp_path) for path in tmp_path.rglob("*")}
    assert before == after
    for path in PACKAGE.glob("*.py"):
        text = path.read_text(encoding="utf-8")
        assert "write_text" not in text
        assert "write_bytes" not in text


@pytest.mark.skipif(not REAL_HEADER.is_file(), reason="local frozen header is absent")
def test_local_frozen_header_matches_baseline() -> None:
    inputs = load_projection_inputs_v1(
        repository_root=ROOT,
        snapshot_header_path=REAL_HEADER,
        current_sha=EXPECTED_BASELINE_SHA,
        current_tree=EXPECTED_BASELINE_TREE,
    )
    report = project_double_play_guardian_gap_v1(inputs)
    _assert_gap(report)
    assert report["WHOLE_SYSTEM_HEADER_MATCHES_BASELINE"] is True
    assert report["SOURCE_PROVENANCE"][-1]["source"] == str(REAL_HEADER)
