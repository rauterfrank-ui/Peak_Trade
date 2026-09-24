"""D27 test-entry lifecycle enforcement tests (F1/F2 TEST_READY scope)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.governance.d27_research_test_entry_lifecycle_enforcement_v1 import (
    DECISION_CONFIG,
    D27ResearchTestEntryLifecycleError,
    F1_TEST_ENTRY_GATE,
    F2_TEST_ENTRY_GATE,
    enforce_d27_f1_test_entry_lifecycle_v1,
    enforce_d27_f2_test_entry_lifecycle_v1,
    enforce_d27_test_entry_lifecycle_admission_v1,
    prove_d27_f1_f2_test_entry_lifecycle_enforcement_v1,
)
from src.governance.platform_unified_native_vs_candidate_baseline_evidence_v1 import (
    InfluenceClassificationV1,
)
from research.canonical_volatility_numeric_max_age_parameter_research_execution_v1.contracts_v1 import (
    MaxAgeResearchExecutionError,
)
from research.canonical_volatility_numeric_max_age_parameter_research_execution_v1.runner_v1 import (
    run_max_age_parameter_research_execution_v1,
)
from tests.governance.d27_native_baseline_fixtures_v1 import (
    build_fixture_native_baseline_evidence_v1,
)
from tests.research.test_canonical_volatility_numeric_max_age_parameter_research_execution_v1 import (
    _fixture_records,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_d27_decision_and_closure_proof() -> None:
    assert prove_d27_f1_f2_test_entry_lifecycle_enforcement_v1(repo_root=REPO_ROOT)
    decision = json.loads((REPO_ROOT / DECISION_CONFIG).read_text(encoding="utf-8"))
    assert decision["d27_f1_f2_lifecycle_enforcement_implemented"] is True
    assert decision["enforced_family_gate_ids"] == ["F1", "F2"]
    assert decision["new_authority_created"] is False
    assert decision["external_effect_authorized"] is False


def test_f1_f2_admission_happy_path() -> None:
    native = build_fixture_native_baseline_evidence_v1()
    f1 = enforce_d27_f1_test_entry_lifecycle_v1(native_baseline_evidence=native)
    assert f1.test_entry_gate == F1_TEST_ENTRY_GATE
    assert f1.family_gate_id == "F1"
    f2 = enforce_d27_f2_test_entry_lifecycle_v1(native_baseline_evidence=native)
    assert f2.test_entry_gate == F2_TEST_ENTRY_GATE


def test_gate_mismatch_fail_closed() -> None:
    native = build_fixture_native_baseline_evidence_v1()
    with pytest.raises(D27ResearchTestEntryLifecycleError, match="TEST_ENTRY_GATE_MISMATCH"):
        enforce_d27_test_entry_lifecycle_admission_v1(
            family_gate_id="F1",
            declared_test_entry_gate="WRONG_GATE",
            native_baseline_evidence=native,
        )


def test_candidate_payload_not_native_fail_closed() -> None:
    native = dict(build_fixture_native_baseline_evidence_v1())
    native["influence_classification"] = InfluenceClassificationV1.CANDIDATE_OR_COUNTERFACTUAL.value
    with pytest.raises(D27ResearchTestEntryLifecycleError, match="NATIVE_BASELINE_CLASSIFICATION"):
        enforce_d27_f1_test_entry_lifecycle_v1(native_baseline_evidence=native)


def test_f1_runner_requires_native_baseline_admission(tmp_path: Path) -> None:
    records = _fixture_records()
    with pytest.raises(MaxAgeResearchExecutionError):
        run_max_age_parameter_research_execution_v1(
            repo_root=REPO_ROOT,
            native_baseline_evidence_v1={},
            output_root=tmp_path / "blocked",
            repository_sha="e03426f0250fbc55f95c044c6a904e059746125c",
            records=records,
            created_at_utc="2026-08-01T00:00:00Z",
        )

    native = build_fixture_native_baseline_evidence_v1()
    result = run_max_age_parameter_research_execution_v1(
        repo_root=REPO_ROOT,
        native_baseline_evidence_v1=native,
        output_root=tmp_path / "ok",
        repository_sha="e03426f0250fbc55f95c044c6a904e059746125c",
        records=records,
        created_at_utc="2026-08-01T00:00:00Z",
    )
    assert result["d27_test_entry_gate"] == F1_TEST_ENTRY_GATE
    assert result["d27_baseline_reference_identity"] == native["baseline_reference_identity"]
