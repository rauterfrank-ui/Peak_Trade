"""Regression tests for the read-only H1 evidence-scope observer."""

from __future__ import annotations

import ast
import json
import sys
from pathlib import Path

import pytest

from scripts.ops.h1_evidence_scope_observation_v1.constants_v1 import (
    FORBIDDEN_OUTPUT_KEYS,
    H1_SCOPE_NODES,
    TOOL_SLOTS,
)
from scripts.ops.h1_evidence_scope_observation_v1.observe_v1 import observe_h1_evidence_scope_v1

EXPECTED_COMMIT = "f19a16f90968245851f8f7bf652f67515d2e2ccc"
EXPECTED_TREE = "befbabe38b59d5bacc44ff19f8de3b33b60def23"
CENSUS_PIN = "6216201d7acbc771f84b6b6884eccc41359927cf"
LANDSCAPE_COMMIT = "e5d9296fb269208b06980518d410b4f2b616bf5b"
LANDSCAPE_TREE = "6422bfde79fd5aa45d2939a821980abf9aa4e3df"
GRAPH_PIN = "b6ffca1d3b39b3dd8814c7c795a8aa6e04bc177a"
OTHER_PIN = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"

_PACKAGE_DIR = Path(__file__).resolve().parents[2] / "scripts/ops/h1_evidence_scope_observation_v1"
_FORBIDDEN_IMPORT_MARKERS = (
    "h1_get_evidence_admission_v1",
    "h1_decision_publication_consumer_v1",
    "okx_eea_private_account_state_runtime_v1",
    "private_account_state_ingestion",
    "scoped_causal_graph_adapter_v1",
    "requests",
    "urllib",
    "httpx",
    "socket",
    "subprocess",
)
_WRITE_ATTRS = frozenset(
    {"write_text", "write_bytes", "mkdir", "unlink", "rmdir", "rename", "replace", "touch"}
)

pytestmark = pytest.mark.filterwarnings("ignore::DeprecationWarning")


@pytest.fixture(scope="module")
def real_observation() -> dict[str, object]:
    root = Path(__file__).resolve().parents[2]
    return observe_h1_evidence_scope_v1(
        repository_root=root,
        authoritative_commit_sha=EXPECTED_COMMIT,
        authoritative_tree_sha=EXPECTED_TREE,
    )


def test_historical_pins_remain_historical(real_observation: dict[str, object]) -> None:
    integrity = real_observation["pin_integrity"]
    assert isinstance(integrity, dict)
    assert integrity["census_pin"] == CENSUS_PIN
    assert integrity["landscape_commit_pin"] == LANDSCAPE_COMMIT
    assert integrity["landscape_tree_pin"] == LANDSCAPE_TREE
    assert integrity["graph_pin"] == GRAPH_PIN
    assert integrity["census_pin_is_current"] is False
    assert integrity["landscape_commit_is_current"] is False
    assert integrity["landscape_tree_is_current"] is False
    assert integrity["graph_pin_is_current"] is False
    assert integrity["historical_pins_rewritten"] is False
    assert integrity["internal_pin_conflict"] is True
    assert integrity["graph_current_flag_adopted"] is False
    assert True in integrity["graph_current_flags_observed"]


def test_no_artificial_current_evidence(real_observation: dict[str, object]) -> None:
    assert real_observation["current_census_proven"] is False
    assert real_observation["h1_membership_complete"] is False
    assert real_observation["status"] != "ACCEPTED"
    provenance = real_observation["ghosv"]["provenance"]["source_provenance"]
    assert provenance["census"]["pin"] == CENSUS_PIN
    assert provenance["landscape"]["commit_pin"] == LANDSCAPE_COMMIT
    assert provenance["graph"]["pin"] == GRAPH_PIN
    assert provenance["census"]["pin"] != EXPECTED_COMMIT
    assert real_observation["admissible_nodes"] == []


def test_h1_nodes_without_proven_current_are_not_graph_nodes(
    real_observation: dict[str, object],
) -> None:
    evaluated = real_observation["evaluated_nodes"]
    proven = real_observation["proven_graph_nodes"]
    scoped = real_observation["scoped_ghv"]["evaluated_nodes"]
    for node in H1_SCOPE_NODES:
        assert node not in evaluated
        assert node not in proven
        assert node not in scoped
    assert real_observation["scope"]["allowed_nodes"] == []
    assert real_observation["scope"]["unassigned"] == list(H1_SCOPE_NODES)
    assert real_observation["scoped_ghv"]["composition_invoked"] is False


def test_historical_proven_current_label_is_not_admitted(tmp_path: Path) -> None:
    _write_repository(
        tmp_path,
        census_objects=[
            {
                "object_id": "H1_GET_EVIDENCE_ADMISSION",
                "epistemic_status": "PROVEN_CURRENT",
                "current_status": "PROVEN_CURRENT",
                "paths": ["src/ops/h1_get_evidence_admission_v1"],
            }
        ],
    )
    result = _observe(tmp_path)

    assert "H1_GET_EVIDENCE_ADMISSION" not in result["proven_graph_nodes"]
    assert result["scope"]["allowed_nodes"] == []
    assert result["scoped_ghv"]["composition_invoked"] is False
    assert result["current_census_proven"] is False


def test_coverage_gap_is_true(real_observation: dict[str, object]) -> None:
    assert real_observation["coverage_gap"] is True
    assert real_observation["fail_closed"] is True


def test_coverage_proof_is_false(real_observation: dict[str, object]) -> None:
    assert real_observation["coverage_proof"] is False
    assert real_observation["pin_binding"]["coverage_proof"] is False
    assert real_observation["scoped_ghv"]["coverage_proof"] is False
    assert real_observation["ghosv"]["coverage_proof"] is False
    assert real_observation["manifest"]["coverage_proof"] is False


def test_authority_is_none(real_observation: dict[str, object]) -> None:
    assert real_observation["authority"] == "NONE"
    assert real_observation["trading_authority"] == "NONE"
    assert real_observation["safety_authority"] == "NONE"
    assert real_observation["execution_authority"] == "NONE"
    assert real_observation["runtime_authorization_effect"] == "NONE"
    for finding in real_observation["submitted_findings"]:
        assert finding["category"] != "AUTHORITY"


def test_forbidden_pass_and_live_keys_are_absent(real_observation: dict[str, object]) -> None:
    found: list[str] = []
    _collect_keys(real_observation, found)
    assert FORBIDDEN_OUTPUT_KEYS.isdisjoint(found)
    assert real_observation["guardian_identity"] is False


def test_manifest_slots_stay_present_unbound(real_observation: dict[str, object]) -> None:
    assert real_observation["manifest_slots"] == dict(TOOL_SLOTS)
    assert real_observation["domain_verification"] is False
    assert real_observation["manifest"]["current_proven"] is False
    assert set(real_observation["manifest_slots"]) == {
        "DOMAIN_GHV",
        "DOMAIN_CURRENT_CAUSAL_GRAPH",
        "DOMAIN_GHOSV",
    }
    assert set(real_observation["manifest_slots"].values()) == {"PRESENT_UNBOUND"}


def test_causal_integrator_is_not_called(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []

    def _forbidden(*_args: object, **_kwargs: object) -> dict[str, object]:
        calls.append("run_scoped_causal_graph_v1")
        return {}

    monkeypatch.setattr(
        "scripts.ops.scoped_causal_graph_adapter_v1.adapt_v1.run_scoped_causal_graph_v1",
        _forbidden,
    )
    _write_repository(tmp_path)
    result = _observe(tmp_path)

    assert calls == []
    assert result["causal_integrator_invoked"] is False
    assert "run_scoped_causal_graph_v1" not in _package_source()


def test_h1_admission_is_not_imported() -> None:
    imported = _imported_modules()
    assert all("h1_get_evidence_admission_v1" not in name for name in imported)
    assert all("h1_decision_publication_consumer_v1" not in name for name in imported)
    assert "src.ops.h1_get_evidence_admission_v1" not in sys.modules
    assert "h1_get_evidence_admission_v1" not in sys.modules


def test_no_private_get_post_or_state_write(real_observation: dict[str, object]) -> None:
    assert real_observation["private_get_executed"] is False
    assert real_observation["post_executed"] is False
    assert real_observation["state_write_executed"] is False
    assert real_observation["network_access"] is False
    assert real_observation["repository_evidence_write"] is False
    imported = _imported_modules()
    for marker in _FORBIDDEN_IMPORT_MARKERS:
        assert all(marker not in name for name in imported)
    for path in _PACKAGE_DIR.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute):
                assert node.attr not in _WRITE_ATTRS
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                assert node.func.id not in {"open", "urlopen", "request"}


def test_missing_provenance_fails_closed(tmp_path: Path) -> None:
    _write_repository(tmp_path)
    result = _observe(tmp_path, provenance={})

    assert result["status"] == "INVALID_PROVENANCE"
    assert result["fail_closed"] is True
    assert result["coverage_gap"] is True
    assert result["coverage_proof"] is False
    assert result["proven_graph_nodes"] == []
    assert "provenance_missing" in result["reasons"]
    assert result["ghosv"]["findings"] == []


def test_contradictory_provenance_fails_closed(tmp_path: Path) -> None:
    _write_repository(tmp_path)
    artificial_current = {
        "census": {"pin": EXPECTED_COMMIT},
        "landscape": {"commit_pin": EXPECTED_COMMIT, "tree_pin": EXPECTED_TREE},
        "graph": {"pin": EXPECTED_COMMIT},
    }
    rejected = _observe(tmp_path, provenance=artificial_current)
    assert "artificial_current_provenance_rejected" in rejected["reasons"]
    assert rejected["status"] != "ACCEPTED"
    assert rejected["ghosv"]["provenance"]["source_provenance"]["census"]["pin"] == CENSUS_PIN
    assert rejected["proven_graph_nodes"] == []

    conflicting = {
        "census": {"pin": CENSUS_PIN},
        "landscape": {"commit_pin": LANDSCAPE_COMMIT, "tree_pin": LANDSCAPE_TREE},
        "graph": {"pin": OTHER_PIN},
    }
    contradicted = _observe(tmp_path, provenance=conflicting)
    assert contradicted["status"] != "ACCEPTED"
    assert contradicted["fail_closed"] is True
    assert "provenance_contradiction" in contradicted["reasons"]
    assert contradicted["proven_graph_nodes"] == []
    assert contradicted["coverage_proof"] is False


def _observe(root: Path, provenance: dict[str, object] | None = None) -> dict[str, object]:
    kwargs: dict[str, object] = {
        "repository_root": root,
        "authoritative_commit_sha": EXPECTED_COMMIT,
        "authoritative_tree_sha": EXPECTED_TREE,
    }
    if provenance is not None:
        kwargs["provenance"] = provenance
    return observe_h1_evidence_scope_v1(**kwargs)


def _write_repository(root: Path, census_objects: list[dict[str, object]] | None = None) -> None:
    census = {
        "source_baseline_head": CENSUS_PIN,
        "census_objects": [] if census_objects is None else census_objects,
    }
    landscape = {
        "evidence_baseline_sha": LANDSCAPE_COMMIT,
        "evidence_baseline_tree_sha": LANDSCAPE_TREE,
    }
    graph = {
        "authority": "NONE",
        "CURRENT_GRAPH_VERIFIED": True,
        "code_snapshot": {
            "git_head": GRAPH_PIN,
            "census_revision": LANDSCAPE_COMMIT,
            "landscape_revision": LANDSCAPE_COMMIT,
        },
    }
    _write_json(root, "config/governance/current_system_census_graph_v1/source_v1.json", census)
    _write_json(
        root,
        "config/governance/current_universe_landscape_snapshot_v1/source_v1.json",
        landscape,
    )
    for relative in (
        "evidence/ops/wp_r2b_r4_presentation_retirement_v1/20261016T041630Z/composed_forensic_graph.v1.json",
        "evidence/ops/wp_r2b_r4_presentation_retirement_v1/20261016T043611Z_r4_final/composed_forensic_graph.v1.json",
    ):
        _write_json(root, relative, graph)


def _write_json(root: Path, relative: str, payload: dict[str, object]) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _package_source() -> str:
    return "\n".join(path.read_text(encoding="utf-8") for path in _PACKAGE_DIR.glob("*.py"))


def _imported_modules() -> list[str]:
    imported: list[str] = []
    for path in _PACKAGE_DIR.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.append(node.module)
    return imported


def _collect_keys(payload: object, found: list[str]) -> None:
    if isinstance(payload, dict):
        for key, value in payload.items():
            found.append(str(key))
            _collect_keys(value, found)
    elif isinstance(payload, list):
        for item in payload:
            _collect_keys(item, found)
