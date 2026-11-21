"""Original Phase-22 predecessor contents before the existing M4 consumer."""

from copy import deepcopy
from dataclasses import replace
import json

import pytest

from src.learning.market_intelligence_forecast_calibration_offline_stack_v1 import (
    phase_22_incremental_research_evidence_v1 as phase22,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.integration_contracts_v1 import (
    bytes_v1,
    plain_v1,
)
from src.meta.learning_loop.contract_safety_v1 import compute_content_sha256
from tests.experiments.test_canonical_optimization_universe_mi_enriched_m4_intake_v1 import (
    _intake_request,
)
from tests.learning.test_incremental_immediate_predecessor_binding_v1 import _request

VARIANTS = ("contiguous", "deferred", "missing", "different_horizon", "missing_family")


def _stage(stage="B0", **changes):
    return plain_v1(phase22.run_incremental_stage_research_v1(replace(_request(stage), **changes)))


def _reseal(record):
    record["content_digest"] = compute_content_sha256(
        {key: value for key, value in record.items() if key != "content_digest"}
    )
    return record


def _dataset(record, **changes):
    raw = {**record, **changes}
    return plain_v1(
        phase22.build_research_dataset_identity_v1(
            phase22.ResearchDatasetIdentityRequestV1(
                **{
                    name: raw[name]
                    for name in phase22.ResearchDatasetIdentityRequestV1.__dataclass_fields__
                }
            )
        )
    )


def _packet(variant):
    if variant in {"contiguous", "deferred"}:
        stages = ("B0", "B1", "B2", "B3", "B4") if variant == "contiguous" else ("B0", "B5")
        return plain_v1(
            phase22.run_phase_22_incremental_research_closure_v1(
                stage_requests=[_request(stage) for stage in stages]
            )
        )
    if variant == "missing":
        return _stage("B1")
    if variant == "different_horizon":
        predecessor = _stage(horizon_identity={"n_bars": 3, "bar_spec_ref": "bar.spec.test"})
        return _stage("B1", predecessor_stage_result=predecessor)
    source = plain_v1(_request("B0").source_market_context)
    # Native B0 projection does not require derivatives; its absence is explicit in B2.
    from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.market_context_v1 import (
        GovernedMarketContextInputsV1,
        compose_market_context_v1_from_governed_inputs,
    )

    context = plain_v1(
        compose_market_context_v1_from_governed_inputs(
            GovernedMarketContextInputsV1(
                observed_at=source["observed_at"],
                instrument_ref=source["instrument_ref"],
                information_set_identity_body={"fixture": "missing_derivatives"},
                provenance_refs=source["provenance_refs"],
                feature_versions=source["feature_versions"],
                price_state=source["price_state_ref"],
                flow_state=source["flow_state_ref"],
                liquidity_microstructure_state=source["liquidity_microstructure_state_ref"],
            )
        )
    )
    predecessor = _stage("B1", source_market_context=context)
    return _stage("B2", source_market_context=context, predecessor_stage_result=predecessor)


def _forbidden(*args, **kwargs):
    pytest.fail("An inconsistent original predecessor reached the actual M4 consumer")


def _reject_before_m4(tmp_path, monkeypatch, predecessor, reason):
    intake = _intake_request(tmp_path)
    before = deepcopy(predecessor)
    stored = {p.relative_to(tmp_path): p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    monkeypatch.setattr(
        phase22, "run_mi_enriched_optimization_universe_experiment_plane_v1", _forbidden
    )
    with pytest.raises(phase22.Phase22IncrementalResearchError, match=reason):
        phase22.run_incremental_stage_research_v1(
            replace(_request("B1", predecessor), plane_intake=intake)
        )
    assert predecessor == before
    assert stored == {
        p.relative_to(tmp_path): p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()
    }


@pytest.mark.parametrize(
    "field",
    [
        "research_disposition",
        "feature_digest",
        "plane_identity",
        "information_set",
        "dataset_identity",
    ],
)
def test_changed_predecessor_cannot_retain_original_digest(tmp_path, monkeypatch, field):
    predecessor = _stage()
    if field == "research_disposition":
        predecessor[field] = "INSUFFICIENT_EVIDENCE"
    elif field in {"feature_digest", "plane_identity"}:
        predecessor[field] = "changed.original.reference"
    elif field == "information_set":
        predecessor[field]["information_set_id"] = "changed.original.information_set"
    else:
        predecessor[field]["sample_range"]["end"] = "2025-01-01T00:00:00Z"
    _reject_before_m4(tmp_path, monkeypatch, predecessor, "PREDECESSOR_CONTENT_DIGEST_MISMATCH")


@pytest.mark.parametrize(
    "field", ["schema_version", "research_disposition_authority", "research_disposition"]
)
def test_resealed_predecessor_retains_native_schema_and_vocabulary(tmp_path, monkeypatch, field):
    predecessor = _stage()
    predecessor[field] = "UNSUPPORTED"
    _reject_before_m4(tmp_path, monkeypatch, _reseal(predecessor), "PREDECESSOR_CONTRACT_INVALID")


@pytest.mark.parametrize("record", ["information_set", "dataset_identity"])
def test_resealed_outer_record_cannot_mask_invalid_nested_identity(tmp_path, monkeypatch, record):
    predecessor = _stage()
    id_field = "information_set_id" if record == "information_set" else "dataset_identity_id"
    predecessor[record][id_field] = "changed.original.identity"
    _reject_before_m4(
        tmp_path, monkeypatch, _reseal(predecessor), "PREDECESSOR_NESTED_CONTENT_INVALID"
    )


@pytest.mark.parametrize(
    "fault", ["stage", "information_set_ref", "horizon", "behavior_version", "predecessor_ref"]
)
def test_valid_native_nested_records_cannot_be_crosswired(tmp_path, monkeypatch, fault):
    predecessor = _stage()
    if fault == "stage":
        predecessor["information_set"] = _stage("B1")["information_set"]
    elif fault == "information_set_ref":
        predecessor["dataset_identity"] = _stage(feature_versions={"fixture": "other"})[
            "dataset_identity"
        ]
    elif fault == "horizon":
        predecessor["dataset_identity"] = _dataset(
            predecessor["dataset_identity"],
            horizon_identity={"n_bars": 3, "bar_spec_ref": "bar.spec.test"},
        )
    elif fault == "behavior_version":
        original = predecessor["dataset_identity"]
        predecessor["dataset_identity"] = plain_v1(
            phase22.build_research_dataset_identity_v1(
                phase22.ResearchDatasetIdentityRequestV1(
                    **{
                        name: value
                        for name, value in original.items()
                        if name in phase22.ResearchDatasetIdentityRequestV1.__dataclass_fields__
                        and name != "behavior_contract_version"
                    },
                    behavior_contract_version="realized_behavior.other_original_version",
                )
            )
        )
    else:
        predecessor["predecessor_stage_id"] = "B1"
    _reject_before_m4(tmp_path, monkeypatch, _reseal(predecessor), "PREDECESSOR_BINDING_MISMATCH")


@pytest.mark.parametrize("variant", VARIANTS)
def test_valid_native_and_json_predecessors_preserve_original_packets(variant):
    packet = _packet(variant)
    assert json.loads(bytes_v1(packet)) == packet
    assert packet == _packet(variant)
    if variant == "contiguous":
        previous = None
        for result in packet["stage_results"]:
            replay = _stage(result["stage_id"], predecessor_stage_result=previous)
            assert replay == result
            previous = json.loads(bytes_v1(result))
    if variant == "deferred":
        assert packet["stage_results"][-1]["research_disposition"] == "DEFERRED"
    if variant in {"missing", "missing_family"}:
        assert packet["research_disposition"] == "INSUFFICIENT_EVIDENCE"


def test_deferred_b5_still_has_no_predecessor_or_plane_consumption(monkeypatch):
    monkeypatch.setattr(phase22, "project_market_context_to_stage_v1", _forbidden)
    monkeypatch.setattr(
        phase22, "run_mi_enriched_optimization_universe_experiment_plane_v1", _forbidden
    )
    result = _stage("B5", predecessor_stage_result={"stage_id": "unusable"})
    assert result["research_disposition"] == "DEFERRED"
    assert result["incremental_comparison"] is None
