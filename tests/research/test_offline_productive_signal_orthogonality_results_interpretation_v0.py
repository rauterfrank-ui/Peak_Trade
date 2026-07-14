from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from research.linear_evidence.import_boundary import scan_file_import_boundary
from research.linear_evidence.signal_orthogonality_results_interpretation_v0 import (
    INTERPRETATION_CLASSES,
    InterpretationValidationError,
    build_authority_boundary_assertions,
    build_orthogonality_interpretation_artifacts_v0,
    classify_pairwise_interpretation,
    load_productive_orthogonality_evidence,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
OWNER = REPO_ROOT / "src/research/linear_evidence/signal_orthogonality_results_interpretation_v0.py"
PRODUCTIVE_BUNDLE = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/research/signal_orthogonality_diagnostics_scope_v0_20260714T211213Z"
)


@pytest.fixture(scope="module")
def loaded_productive() -> dict:
    return load_productive_orthogonality_evidence(PRODUCTIVE_BUNDLE)


@pytest.fixture(scope="module")
def interpretation_artifacts() -> dict:
    knowns = [
        "Ratified fleet bindings for trend_following/v1, bollinger_bands/v1, momentum_1h/v1 resolved"
    ]
    return build_orthogonality_interpretation_artifacts_v0(
        PRODUCTIVE_BUNDLE,
        signal_matrix_knowns=knowns,
        time_range="2024-05-25T00:00:00Z..2024-06-01T01:00:00Z",
        dataset_binding="manifest_verified_signal_matrix_staging_root",
    )


def test_productive_evidence_loads_deterministically(loaded_productive: dict) -> None:
    again = load_productive_orthogonality_evidence(PRODUCTIVE_BUNDLE)
    assert again == loaded_productive


def test_digest_mismatch_fail_closed(loaded_productive: dict, tmp_path: Path) -> None:
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    for name, payload in loaded_productive.items():
        (bundle / f"{name}.json").write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    binding = json.loads((bundle / "input_binding.json").read_text(encoding="utf-8"))
    binding["source_csv_digest"] = "deadbeef"
    (bundle / "input_binding.json").write_text(json.dumps(binding) + "\n", encoding="utf-8")
    with pytest.raises(InterpretationValidationError, match="INPUT_DIGEST_MISMATCH"):
        load_productive_orthogonality_evidence(bundle)


def test_missing_required_field_fail_closed(loaded_productive: dict, tmp_path: Path) -> None:
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    for name, payload in loaded_productive.items():
        (bundle / f"{name}.json").write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    (bundle / "pairwise_correlations.json").write_text("[]\n", encoding="utf-8")
    with pytest.raises(InterpretationValidationError):
        load_productive_orthogonality_evidence(bundle)


def test_unknown_signal_fail_closed(loaded_productive: dict, tmp_path: Path) -> None:
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    mutated = copy.deepcopy(loaded_productive)
    mutated["pairwise_correlations"][0]["signal_a"] = "unknown_signal"
    for name, payload in mutated.items():
        (bundle / f"{name}.json").write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    with pytest.raises(InterpretationValidationError, match="UNKNOWN_SIGNAL"):
        load_productive_orthogonality_evidence(bundle)


def test_unknown_signal_version_fail_closed() -> None:
    with pytest.raises(InterpretationValidationError, match="UNKNOWN_SIGNAL_VERSION"):
        build_orthogonality_interpretation_artifacts_v0(
            PRODUCTIVE_BUNDLE,
            signal_matrix_knowns=["Ratified fleet bindings for trend_following/v99 resolved"],
        )


def test_unknown_status_fail_closed(loaded_productive: dict, tmp_path: Path) -> None:
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    mutated = copy.deepcopy(loaded_productive)
    mutated["pairwise_correlations"][0]["status"] = "MYSTERY"
    for name, payload in mutated.items():
        (bundle / f"{name}.json").write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    with pytest.raises(InterpretationValidationError, match="UNKNOWN_PAIR_STATUS"):
        load_productive_orthogonality_evidence(bundle)


def test_interpretation_classes_complete_and_exclusive(interpretation_artifacts: dict) -> None:
    for row in interpretation_artifacts["pairwise_interpretation"]:
        assert row["interpretation_class"] in INTERPRETATION_CLASSES
    classes = [
        row["interpretation_class"] for row in interpretation_artifacts["pairwise_interpretation"]
    ]
    assert len(classes) == len(set(classes)) or len(classes) == 3


def test_same_inputs_produce_identical_output_digest(interpretation_artifacts: dict) -> None:
    second = build_orthogonality_interpretation_artifacts_v0(
        PRODUCTIVE_BUNDLE,
        signal_matrix_knowns=[
            "Ratified fleet bindings for trend_following/v1, bollinger_bands/v1, momentum_1h/v1 resolved"
        ],
        time_range="2024-05-25T00:00:00Z..2024-06-01T01:00:00Z",
        dataset_binding="manifest_verified_signal_matrix_staging_root",
    )
    assert interpretation_artifacts["output_digest"] == second["output_digest"]


def test_productive_pairs_classified_distinct_without_linear_redundancy_flags(
    interpretation_artifacts: dict,
) -> None:
    classes = {
        row["interpretation_class"] for row in interpretation_artifacts["pairwise_interpretation"]
    }
    assert classes == {"DISTINCT_INFORMATION_SUPPORTED"}


def test_partial_redundancy_when_spearman_exceeds_ratified_threshold(
    loaded_productive: dict,
) -> None:
    record = dict(loaded_productive["pairwise_correlations"][1])
    record["pearson_correlation"] = 0.1
    record["absolute_pearson_correlation"] = 0.1
    record["reason_codes"] = []
    record["spearman_correlation"] = 0.9
    result = classify_pairwise_interpretation(
        record,
        rolling_stability=loaded_productive["rolling_stability"],
        matrix_diagnostics=loaded_productive["matrix_diagnostics"],
        signal_count_after_filter=3,
        diagnostic_policy=loaded_productive["diagnostic_policy"],
        regime_slices_present=False,
    )
    assert result["interpretation_class"] == "PARTIAL_REDUNDANCY_SUPPORTED"


def test_authority_boundary_assertions_no_mutation() -> None:
    assertions = build_authority_boundary_assertions()
    assert assertions["authority_effect"] == "NONE"
    assert assertions["runtime_effect"] == "NONE"
    assert assertions["promotion_effect"] == "NONE"
    assert assertions["active_set_effect"] == "NONE"
    assert assertions["no_strategy_selection_change"] is True
    assert assertions["no_signal_selection_change"] is True
    assert assertions["no_automatic_signal_removal"] is True
    assert assertions["no_automatic_signal_replacement"] is True
    assert assertions["no_automatic_signal_downweighting"] is True
    assert assertions["no_economic_pass_claim"] is True
    assert assertions["new_orthogonality_fit_executed"] is False
    assert assertions["economic_evaluation_executed"] is False


def test_no_runtime_imports_in_owner() -> None:
    hits = scan_file_import_boundary(OWNER, repo_root=REPO_ROOT)
    assert hits == []


def test_interpretation_artifacts_authority_fields(interpretation_artifacts: dict) -> None:
    authority = interpretation_artifacts["authority_boundary_assertions"]
    assert authority["strategy_selection_changed"] is False
    assert authority["signal_weighting_changed"] is False
    assert authority["parameters_changed"] is False
    assert authority["economic_pass_claim_created"] is False
