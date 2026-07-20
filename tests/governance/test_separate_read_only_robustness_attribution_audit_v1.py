"""Contract tests for SEPARATE_READ_ONLY_ROBUSTNESS_ATTRIBUTION_AUDIT_V1.

Does not re-run the full offline panel. Validates audit harness markers,
fail-closed safety flags, evidence hygiene, and baseline reproduction match.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[2]
_EVIDENCE = _REPO / "docs/evidence/separate_read_only_robustness_attribution_audit_v1"
_HARNESS = _EVIDENCE / "run_attribution_audit_v1.py"

PRODUCTIVE_GLOBS = (
    "src/trading/",
    "src/execution/",
    "src/risk/",
    "src/strategies/",
    "src/governance/",
)

REQUIRED_EVIDENCE = (
    "README.md",
    "manifest.json",
    "baseline_reproduction.json",
    "attribution_by_instrument.csv",
    "attribution_by_direction.csv",
    "attribution_by_scope.csv",
    "attribution_by_composition.csv",
    "attribution_by_exit_reason.csv",
    "cost_turnover_attribution.csv",
    "chronological_segments.csv",
    "walk_forward_reaudit.csv",
    "stress_reaudit.csv",
    "leave_one_instrument_out.csv",
    "robustness_summary.json",
    "root_cause_classification.json",
    "decision_matrix.md",
    "commands.log",
    "run_attribution_audit_v1.py",
)


def _load_harness():
    assert _HARNESS.is_file(), f"missing harness: {_HARNESS}"
    spec = importlib.util.spec_from_file_location(
        "separate_read_only_robustness_attribution_audit_v1", _HARNESS
    )
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def harness():
    return _load_harness()


def test_harness_is_non_authoritative_and_offline_only(harness) -> None:
    src = _HARNESS.read_text(encoding="utf-8")
    assert "NON-AUTHORITATIVE" in src
    assert harness.AUDIT_AUTHORITY_EFFECT == "NONE"
    assert harness.AUDIT_RUNTIME_EFFECT == "NONE"
    assert harness.SEED == 42
    assert harness.EXPECTED_MAIN == "891044056537a4033e6136ba01652a0a2c6e76b7"
    assert harness.FEE_BPS == 10.0
    assert harness.SLIPPAGE_BPS == 5.0


def test_harness_lives_only_under_evidence() -> None:
    rel = str(_HARNESS.relative_to(_REPO))
    assert rel.startswith("docs/evidence/")
    for g in PRODUCTIVE_GLOBS:
        assert not rel.startswith(g)


def test_required_evidence_files_present() -> None:
    missing = [n for n in REQUIRED_EVIDENCE if not (_EVIDENCE / n).is_file()]
    assert missing == [], missing


def test_baseline_reproduction_matches_reference() -> None:
    payload = json.loads((_EVIDENCE / "baseline_reproduction.json").read_text(encoding="utf-8"))
    assert payload["reference_metrics_match"] is True
    assert payload["ECONOMIC_GATE_OPENED"] is False
    assert payload["PROMOTION_ELIGIBLE"] is False
    repro = payload["reproduced"]
    assert repro["total_trades"] == 454
    assert repro["long_trades"] == 69
    assert repro["short_trades"] == 385
    assert repro["cost_application"] == "APPLIED"
    assert repro["economic_measurement_valid"] is True
    assert repro["capital_double_counting"] is False


def test_robustness_summary_keeps_gate_closed() -> None:
    payload = json.loads((_EVIDENCE / "robustness_summary.json").read_text(encoding="utf-8"))
    assert payload["ECONOMIC_GATE_OPENED"] is False
    assert payload["PROMOTION_ELIGIBLE"] is False
    assert payload["ECONOMIC_MEASUREMENT_VALID"] is True
    assert payload["ECONOMIC_CLASS"] == "INCONCLUSIVE_UNSTABLE"
    assert payload["next_recommended_action"] == "ACQUIRE_LONGER_CHRONOLOGICAL_PIT_DATASET"


def test_root_cause_measurement_defect_not_confirmed() -> None:
    payload = json.loads((_EVIDENCE / "root_cause_classification.json").read_text(encoding="utf-8"))
    assert payload["classes"]["A_measurement_defect"]["status"] == "NOT_SUPPORTED"
    assert payload["ECONOMIC_GATE_OPENED"] is False
    assert payload["PROMOTION_ELIGIBLE"] is False


def test_manifest_lists_only_existing_files() -> None:
    manifest = json.loads((_EVIDENCE / "manifest.json").read_text(encoding="utf-8"))
    for name in manifest["files"]:
        assert (_EVIDENCE / name).is_file(), name


def test_pf_helper_is_deterministic(harness) -> None:
    assert harness._pf([1.0, -0.5]) == pytest.approx(2.0)
    assert harness._pf([1.0, 2.0]) is None
    assert harness._pf([-1.0, -2.0]) == pytest.approx(0.0)
