"""Governance contracts for post-repair canonical SHORT binding reevaluation evidence."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[2]
_EVIDENCE = _REPO / "docs/evidence/canonical_short_binding_post_repair_reevaluation_v1"
_HARNESS = _EVIDENCE / "post_repair_reevaluation_probe_v1.py"
_WIRING = _REPO / "src/backtest/mv2_research_wiring_v1.py"

REQUIRED_ARTIFACTS = (
    "README.md",
    "verdict.txt",
    "manifest.json",
    "probe_summary.json",
    "direction_probe.json",
    "economics.json",
    "chain_binding_proof.json",
    "claims.json",
    "result_classification.json",
    "tests.txt",
    "ruff.txt",
    "commands.txt",
    "environment.txt",
)


def _load_harness():
    assert _HARNESS.is_file(), f"missing harness: {_HARNESS}"
    spec = importlib.util.spec_from_file_location(
        "canonical_short_binding_post_repair_reevaluation_probe_v1", _HARNESS
    )
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def harness():
    return _load_harness()


def test_evidence_artifacts_present() -> None:
    missing = [name for name in REQUIRED_ARTIFACTS if not (_EVIDENCE / name).is_file()]
    if missing:
        pytest.skip(f"post-repair reevaluation evidence not yet materialized: {missing}")


def test_harness_is_non_authoritative_and_offline_only(harness) -> None:
    src = _HARNESS.read_text(encoding="utf-8")
    assert "NON-AUTHORITATIVE" in src
    assert harness.AUDIT_AUTHORITY_EFFECT == "NONE"
    assert harness.AUDIT_RUNTIME_EFFECT == "NONE"
    assert harness.CONFIG_ID
    assert harness.DATASET_ID
    assert harness.SEED == 42
    assert "run_mv2_research_backtest_wiring_v1" in src
    assert str(_HARNESS.relative_to(_REPO)).startswith("docs/evidence/")


def test_repair_binding_still_present_in_source() -> None:
    wiring = _WIRING.read_text(encoding="utf-8")
    assert wiring.count("use_execution_pipeline=True") >= 2
    assert "use_execution_pipeline=False" not in wiring
    assert wiring.count("honor_mapped_short_entry=True") >= 2


def test_chain_binding_proof_static(harness) -> None:
    proof = harness.prove_chain_binding_static()
    assert proof["uses_run_mv2_research_backtest_wiring_v1"] is True
    assert proof["wiring_use_execution_pipeline_true_count"] >= 2
    assert proof["wiring_use_execution_pipeline_false_count"] == 0
    assert proof["honor_mapped_short_entry_true_count"] >= 2
    assert proof["direction_authority"] == "MasterV2_DoublePlay_sole"
    assert proof["live_authorized"] is False
    assert proof["orders"] is False


def test_result_classification_fail_closed(harness) -> None:
    assert (
        harness.classify_result(
            chain_ok=False,
            direction_ok=True,
            total_trades=5,
            short_flags_ok=True,
            net_return=-0.01,
            gross_return=-0.01,
        )
        == harness.RESULT_FAIL_CHAIN
    )
    assert (
        harness.classify_result(
            chain_ok=True,
            direction_ok=True,
            total_trades=0,
            short_flags_ok=True,
            net_return=0.0,
            gross_return=0.0,
        )
        == harness.RESULT_TERMINAL_INCONCLUSIVE
    )
    assert (
        harness.classify_result(
            chain_ok=True,
            direction_ok=True,
            total_trades=3,
            short_flags_ok=True,
            net_return=-0.005,
            gross_return=-0.005,
        )
        == harness.RESULT_PASS_CHAIN_ONLY
    )
    assert (
        harness.classify_result(
            chain_ok=True,
            direction_ok=True,
            total_trades=25,
            short_flags_ok=True,
            net_return=-0.02,
            gross_return=-0.01,
        )
        == harness.RESULT_ECONOMIC_FAIL
    )


def test_manifest_sha256_matches_when_present() -> None:
    manifest_path = _EVIDENCE / "manifest.json"
    if not manifest_path.is_file():
        pytest.skip("manifest not yet materialized")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    for entry in manifest["files"]:
        path = _REPO / entry["path"]
        assert path.is_file(), entry["path"]
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        assert digest == entry["sha256"], entry["name"]


def test_probe_summary_direction_counts_when_present() -> None:
    path = _EVIDENCE / "probe_summary.json"
    if not path.is_file():
        pytest.skip("probe_summary not yet materialized")
    summary = json.loads(path.read_text(encoding="utf-8"))
    totals = summary["totals"]
    assert "enter_long_count" in totals
    assert "enter_short_count" in totals
    assert "observe_count" in totals
    assert "total_trades" in totals
    flags = summary["direction_probe_flags"]
    for key in (
        "SHORT_ENTRY_REQUESTED",
        "SHORT_FILL_CREATED",
        "SHORT_POSITION_OBSERVED",
        "SHORT_EXIT_CREATED",
        "SHORT_ROUNDTRIP_LEDGERED",
        "LONG_FUNCTIONAL",
        "NONE_FAIL_CLOSED_PASS",
    ):
        assert key in flags
    assert summary["result_class"] in {
        "PASS_CHAIN_ONLY",
        "FAIL_CHAIN",
        "ECONOMIC_FAIL",
        "TERMINAL_INCONCLUSIVE",
    }
    assert summary["ECONOMIC_VALIDITY_OFFLINE_GATE_PASS"] is False
    assert summary["PROMOTION_ELIGIBLE"] == 0
    assert summary["productive_files_changed"] is False
    assert summary["live_authorized"] is False


def test_claims_and_verdict_when_present() -> None:
    claims_path = _EVIDENCE / "claims.json"
    verdict_path = _EVIDENCE / "verdict.txt"
    class_path = _EVIDENCE / "result_classification.json"
    if not claims_path.is_file() or not verdict_path.is_file() or not class_path.is_file():
        pytest.skip("claims/verdict/classification not yet materialized")
    claims = json.loads(claims_path.read_text(encoding="utf-8"))
    classification = json.loads(class_path.read_text(encoding="utf-8"))
    verdict = verdict_path.read_text(encoding="utf-8")
    assert "RESULT_CLASS" in claims
    assert classification["RESULT_CLASS"] == claims["RESULT_CLASS"]
    assert f"RESULT_CLASS={claims['RESULT_CLASS']}" in verdict
    assert "ECONOMIC_VALIDITY_OFFLINE_GATE_PASS=false" in verdict
    assert "PROMOTION_ELIGIBLE=0" in verdict
    assert "LIVE_AUTHORIZED=false" in verdict
