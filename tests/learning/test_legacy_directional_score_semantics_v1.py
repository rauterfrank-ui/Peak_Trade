"""Resolve the legacy BRIER_SCORE_V1 wire token against native math and consumers."""

from dataclasses import replace
from fractions import Fraction
import json
from pathlib import Path

import pytest

from src.experiments.canonical_optimization_universe_mi_enriched_m4_intake_v1 import (
    run_mi_enriched_optimization_universe_experiment_plane_v1,
)
from src.experiments.canonical_optimization_universe_experiment_plane_v1 import (
    PLANE_STATUS_COMPLETE,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.calibration_evidence_v1 import (
    CalibrationEvidenceValidationError,
    build_calibration_evidence_v1,
    validate_calibration_evidence_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.integration_contracts_v1 import (
    bytes_v1,
    plain_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.measured_return_calibration_v1 import (
    MeasuredReturnCalibrationError,
    read_measured_return_calibration_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.mi_learning_evidence_learning_export_v1 import (
    export_mi_learning_evidence_onto_learning_path_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.mi_learning_evidence_store_v1 import (
    MiLearningEvidenceStoreV1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.mi_offline_durable_evidence_record_v1 import (
    build_mi_offline_durable_evidence_record_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.mi_offline_durable_evidence_store_v1 import (
    MiOfflineDurableEvidenceStoreV1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.mi_research_evidence_v1 import (
    project_market_intelligence_research_evidence_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.mi_to_learning_evidence_bridge_v1 import (
    compose_mi_to_learning_evidence_v1,
)
from tests.experiments.test_canonical_optimization_universe_mi_enriched_m4_intake_v1 import (
    _intake_request,
)
from tests.learning.test_forecast_probability_semantic_admission_v1 import (
    directional,
    native_forecast,
    original_result,
)

DIRECTIONS = ("UP", "DOWN", "FLAT")
BASE_PAYLOAD = directional(("0.5", "0.3", "0.2"))


def native_calibration(direction, payload=None):
    request, _ = original_result()
    forecast = native_forecast(
        request, probabilistic_payload=BASE_PAYLOAD if payload is None else payload
    )
    calibration = build_calibration_evidence_v1(
        forecast_evidence=forecast,
        evaluation_observation=request.evaluation_observation,
        realized_direction=direction,
    )
    return request, forecast, calibration


def unscaled_quadratic_reference(payload, direction):
    """Mathematical comparison only, not a new production metric or normalization."""
    return sum(
        (Fraction(str(payload["p_" + label.lower()])) - int(label == direction)) ** 2
        for label in DIRECTIONS
    )


@pytest.mark.parametrize("direction", DIRECTIONS)
@pytest.mark.parametrize(
    "values", [(1, 0, 0), (0, 1, 0), (0, 0, 1), ("0.5", "0.3", "0.2"), ("0.5", "0.4", "0.1")]
)
def test_native_v1_is_realized_class_complement_with_legacy_wire_identity(direction, values):
    payload = directional(values)
    _, _, calibration = native_calibration(direction, payload)
    expected = 1 - Fraction(str(payload["p_" + direction.lower()]))
    result = calibration["calibration_result"]
    assert result["score"] == pytest.approx(float(expected))
    assert 0 <= result["score"] <= 1
    assert result["realized_direction"] == direction
    assert result["method"] == calibration["calibration_method"] == "BRIER_SCORE_V1"
    assert calibration["calibration_evidence_authority"] == "NONE"


def test_other_class_probability_split_distinguishes_linear_loss_from_brier():
    left, right = BASE_PAYLOAD, directional(("0.5", "0.4", "0.1"))
    _, _, first = native_calibration("UP", left)
    _, _, second = native_calibration("UP", right)
    assert first["calibration_result"]["score"] == second["calibration_result"]["score"] == 0.5
    assert unscaled_quadratic_reference(left, "UP") == Fraction(38, 100)
    assert unscaled_quadratic_reference(right, "UP") == Fraction(42, 100)
    assert first["calibration_evidence_id"] != second["calibration_evidence_id"]


def test_linear_loss_is_not_a_proper_probability_forecast_quality_objective():
    # Exact ten-case population: six UP, three DOWN, one FLAT. No market-data claim.
    truth = directional(("0.6", "0.3", "0.1"))
    all_up = directional((1, 0, 0))
    weights = dict(
        zip(DIRECTIONS, (Fraction(6, 10), Fraction(3, 10), Fraction(1, 10)), strict=True)
    )
    native_means = []
    reference_means = []
    for payload in (truth, all_up):
        scores = {
            label: native_calibration(label, payload)[2]["calibration_result"]["score"]
            for label in DIRECTIONS
        }
        native_means.append(
            sum(weights[label] * Fraction(str(scores[label])) for label in DIRECTIONS)
        )
        reference_means.append(
            sum(
                weights[label] * unscaled_quadratic_reference(payload, label)
                for label in DIRECTIONS
            )
        )
    # Reporting the mode with certainty improves the legacy loss over truthful probabilities.
    assert native_means == [Fraction(54, 100), Fraction(40, 100)]
    assert reference_means == [Fraction(54, 100), Fraction(80, 100)]


def native_packet(root, direction, template=None):
    request, forecast, calibration = native_calibration(direction)
    legacy = template.legacy_learning_evidence if template is not None else None
    legacy_ref = legacy["record_id"] if legacy is not None else None
    research = project_market_intelligence_research_evidence_v1(
        forecast_evidence=forecast,
        calibration_evidence=calibration,
        legacy_learning_evidence_ref=legacy_ref,
    )
    triad = build_mi_offline_durable_evidence_record_v1(
        forecast_evidence=forecast, calibration_evidence=calibration, research_evidence=research
    )
    triad_root = root / "triad"
    store = MiOfflineDurableEvidenceStoreV1(triad_root)
    store.append(triad)
    cold_triad = MiOfflineDurableEvidenceStoreV1(triad_root).get(triad["durable_evidence_id"])
    learning = compose_mi_to_learning_evidence_v1(
        forecast_evidence=forecast,
        evaluation_observation=request.evaluation_observation,
        realized_direction=direction,
        calibration_evidence=calibration,
        legacy_learning_evidence_ref=legacy_ref,
    )
    learning_root = root / "learning"
    MiLearningEvidenceStoreV1(learning_root).append(learning)
    cold_learning = MiLearningEvidenceStoreV1(learning_root).get(
        learning["mi_learning_evidence_id"]
    )
    export = export_mi_learning_evidence_onto_learning_path_v1(
        cold_learning, legacy_learning_evidence=legacy
    )
    files = {str(p.relative_to(root)): p.read_bytes() for p in root.rglob("*.json")}
    assert bytes_v1(cold_triad) == bytes_v1(triad)
    assert bytes_v1(cold_learning) == bytes_v1(learning)
    assert bytes_v1(store.append(triad)) == bytes_v1(cold_triad)
    assert bytes_v1(MiLearningEvidenceStoreV1(learning_root).append(learning)) == bytes_v1(
        cold_learning
    )
    assert {str(p.relative_to(root)): p.read_bytes() for p in root.rglob("*.json")} == files
    packet = dict(
        forecast=forecast,
        calibration=calibration,
        research=research,
        triad=cold_triad,
        learning=cold_learning,
        export=export,
    )
    if template is not None:
        packet["plane"] = run_mi_enriched_optimization_universe_experiment_plane_v1(
            replace(
                template,
                market_intelligence_research_evidence=research,
                mi_learning_evidence_export=export,
            )
        )
    return plain_v1(packet)


@pytest.mark.parametrize("direction", DIRECTIONS)
def test_full_triad_and_learning_reference_have_distinct_storage_meanings(tmp_path, direction):
    packet = native_packet(tmp_path, direction)
    assert packet["triad"]["calibration_evidence"] == packet["calibration"]
    assert (
        packet["learning"]["calibration_evidence_id"]
        == packet["calibration"]["calibration_evidence_id"]
    )
    assert packet["learning"]["calibration_method"] == "BRIER_SCORE_V1"
    assert "calibration_result" not in packet["learning"]
    assert "calibration_result" not in packet["research"]
    assert packet["export"]["external_effect_authorized"] is False
    assert packet["export"]["consumer_route"]["productive_ddo_reducer_mutated"] is False


@pytest.mark.parametrize("direction", DIRECTIONS)
def test_existing_numeric_return_reader_does_not_consume_directional_loss(tmp_path, direction):
    packet = native_packet(tmp_path, direction)
    with pytest.raises(MeasuredReturnCalibrationError, match="DURABLE_RETURN_ERROR_REQUIRED"):
        read_measured_return_calibration_v1(
            durable_store_root=tmp_path / "triad",
            durable_evidence_id=packet["triad"]["durable_evidence_id"],
            forecast_evidence_id=packet["forecast"]["forecast_evidence_id"],
            actual_outcome_ref=packet["calibration"]["actual_outcome_ref"],
        )


def test_supplied_direction_changes_lineage_but_not_fixed_m4_numeric_chain(tmp_path):
    template = _intake_request(tmp_path / "legacy")
    packets = [native_packet(tmp_path / label, label, template) for label in DIRECTIONS]
    assert [p["calibration"]["calibration_result"]["score"] for p in packets] == [0.5, 0.7, 0.8]
    assert len({p["forecast"]["forecast_evidence_id"] for p in packets}) == 1
    assert len({p["calibration"]["actual_outcome_ref"] for p in packets}) == 1
    assert len({p["learning"]["mi_learning_evidence_id"] for p in packets}) == 3
    chains = []
    for packet in packets:
        plane = packet["plane"]
        assert plane["status"] == PLANE_STATUS_COMPLETE
        assert (
            plane["chain"]["mi_lineage_refs"]["calibration_evidence_id"]
            == packet["calibration"]["calibration_evidence_id"]
        )
        chains.append(
            bytes_v1(
                {
                    k: v
                    for k, v in plane["chain"].items()
                    if k not in {"mi_enriched_m4_intake", "mi_lineage_refs"}
                }
            )
        )
    assert chains[0] == chains[1] == chains[2]
    # These are controlled supplied labels, not three asserted natural market truths.


def test_joined_outcome_reference_does_not_invent_realized_direction():
    request, forecast, _ = native_calibration("UP")
    with pytest.raises(CalibrationEvidenceValidationError, match="REALIZED_DIRECTION_REQUIRED"):
        build_calibration_evidence_v1(
            forecast_evidence=forecast, evaluation_observation=request.evaluation_observation
        )


@pytest.mark.parametrize("index", range(3))
def test_retained_original_records_keep_their_legacy_values_and_identities(index):
    path = (
        Path(__file__).resolve().parents[2]
        / "docs/ops/evidence/self_learning_loop_a_causal_consumer_assessment_v1_2026_11_04/controlled_consumer_probes.json"
    )
    original = json.loads(path.read_text())["mi"][index]["calibration"]
    before = bytes_v1(original)
    assert bytes_v1(validate_calibration_evidence_v1(original)) == before
    assert original["calibration_method"] == "BRIER_SCORE_V1"
    assert original["calibration_result"]["score"] == [0.5, 0.7, 0.8][index]
