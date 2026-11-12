"""Consume a canonical Meta cost investigation using a persisted F2 scenario grid."""

from __future__ import annotations

import math
from dataclasses import replace
from datetime import datetime, timezone
from fractions import Fraction
from itertools import product
from pathlib import Path
from typing import Any, Mapping

from src.backtest.admissible_versioned_futures_dataset_v1 import (
    DatasetProfileV1,
    L1ObservationStatusV1,
)
from src.backtest.cost_config_v0 import FEE_MODEL_VERSION
from src.backtest.okx_eth_perp_research_cost_grid_v1_constants import (
    BASELINE_FEE_BPS,
    BASELINE_SLIPPAGE_BPS,
    GRID_ID,
    OPERATOR_BOUND_FEE_BPS,
    OPERATOR_BOUND_SLIPPAGE_BPS,
)
from src.backtest.parameter_sensitivity_v1 import EvaluationStatus, MetricValueStatus
from src.experiments.canonical_experiment_identity_v1 import (
    domain_separated_digest,
    validate_canonical_experiment_identity_v1,
)
from src.experiments.canonical_experiment_memory_v1 import derive_experiment_id_v1
from src.experiments.canonical_f2_research_backtest_cost_grid_research_execution_v1 import (
    SCHEMA_VERSION as F2_EXECUTION_SCHEMA,
)
from src.experiments.canonical_f2_research_backtest_cost_grid_research_execution_v1 import (
    SURFACE_ID,
)
from src.experiments.canonical_meta_learning_v1 import (
    COST_DIMENSION_DIGEST_FIELDS,
    METRIC_DEFINITION_VERSION,
    PROPOSAL_INVESTIGATE,
    QUESTION_COST_MODEL_REALITY_UNDERESTIMATION,
    CanonicalMetaLearningRequestV1,
    MetaLearningExperimentUnitV1,
    build_canonical_meta_learning_v1,
    canonical_meta_learning_policy_v1,
    canonical_record_payload_v1,
    validate_canonical_meta_learning_v1,
)
from src.experiments.canonical_reality_gap_store_v1 import (
    ARTIFACT_KIND_STORE_RELATIVE_REF,
    EVIDENCE_KIND_EXPERIMENT_RECORD,
    CanonicalRealityGapRecordRequestV1,
    RealityGapDimensionV1,
    build_canonical_reality_gap_record_v1,
)
from src.experiments.canonical_research_prepared_execution_v1 import read_v1
from src.meta.learning_loop.contract_safety_v1 import compute_content_sha256
from src.ops.execution_fill_fee_observation_v1 import (
    measure_linear_swap_taker_fee_v1,
    read_authenticated_execution_fill_fee_observation_v1,
)

_BASELINE = (BASELINE_FEE_BPS, BASELINE_SLIPPAGE_BPS)
_GRID = frozenset(product(OPERATOR_BOUND_FEE_BPS, OPERATOR_BOUND_SLIPPAGE_BPS))
_AXIS_INDEX = {"fee": 0, "slippage": 1}


def _read_f2_grid(path: Path, expected_digest: str) -> dict[str, Any]:
    result = read_v1(path)
    if not isinstance(result, dict):
        raise ValueError("F2_META_ARCHIVE_INVALID")
    digest = result.get("execution_digest")
    if digest != expected_digest or digest != compute_content_sha256(
        {key: value for key, value in result.items() if key != "execution_digest"}
    ):
        raise ValueError("F2_META_EXECUTION_DIGEST_MISMATCH")
    if (
        result.get("schema_version") != F2_EXECUTION_SCHEMA
        or result.get("surface_id") != SURFACE_ID
        or result.get("grid_id") != GRID_ID
        or result.get("research_optimization_only") is not True
        or result.get("external_effect_authorized") is not False
        or result.get("productive_parameter_mutation") is not False
        or not isinstance(result.get("research_dataset_evidence"), dict)
        or not isinstance(result.get("parameter_sensitivity_result"), dict)
    ):
        raise ValueError("F2_META_ARCHIVE_GRID_REQUIRED")
    return result


def _metric(point: Mapping[str, Any], key: str) -> float | None:
    value = point[key].get("value")
    if (
        point[key].get("semantic") == MetricValueStatus.COMPUTED.value
        and type(value) in (int, float)
        and math.isfinite(value)
    ):
        return float(value)
    return None


def _axis_assessment(
    result: Mapping[str, Any], *, dimension: str
) -> tuple[str, list[dict[str, Any]]]:
    sensitivity = result["parameter_sensitivity_result"]
    grid = sensitivity["grid"]
    archive = result["research_dataset_evidence"]["dataset_admissibility"]
    if (
        archive["dataset_profile"] != DatasetProfileV1.ECONOMIC_RESEARCH_V1.value
        or archive["l1_observation_status"]
        != L1ObservationStatusV1.EXECUTION_MODEL_BOUND_NOT_OBSERVED.value
        or grid["grid_digest"] != result["grid_digest"]
        or grid["data_digest_or_explicit_missing"] != archive["dataset_digest"]
        or grid["out_of_sample_period"] != archive["out_of_sample_period"]
        or sensitivity["result_digest"] != result["parameter_sensitivity_result_digest"]
    ):
        raise ValueError("F2_META_GRID_LINEAGE_MISMATCH")
    points = {
        (point["parameter_values"]["fee_bps"], point["parameter_values"]["slippage_bps"]): point
        for point in sensitivity["points"]
    }
    if (
        points.keys() != _GRID
        or len(sensitivity["points"]) != len(_GRID)
        or any(
            point["data_digest"] != archive["dataset_digest"]
            or point["implementation_digest"] != grid["implementation_digest"]
            or point["config_digest"] != grid["config_digest"]
            for point in points.values()
        )
    ):
        raise ValueError("F2_META_GRID_LINEAGE_MISMATCH")
    if dimension not in _AXIS_INDEX:
        return "FUNDING_AXIS_UNAVAILABLE", []

    index = _AXIS_INDEX[dimension]
    fixed_index = 1 - index
    baseline_return = _metric(points[_BASELINE], "net_return")
    baseline_trades = _metric(points[_BASELINE], "trade_count")
    scenarios = []
    for coordinates, point in sorted(points.items()):
        if coordinates[fixed_index] != _BASELINE[fixed_index]:
            continue
        net_return = _metric(point, "net_return")
        trades = _metric(point, "trade_count")
        delta = None
        if (
            points[_BASELINE]["evaluation_status"] != EvaluationStatus.EVALUATED.value
            or point["evaluation_status"] != EvaluationStatus.EVALUATED.value
            or None in (net_return, trades, baseline_return, baseline_trades)
        ):
            status = "INCOMPLETE_OOS_RESULT"
        elif trades <= 0 or baseline_trades <= 0:
            status = "NO_OOS_TRADES_FOR_COMPARISON"
        else:
            status = "MODELED_OOS_DELTA_AVAILABLE"
            delta = net_return - baseline_return
        scenarios.append(
            {
                "fee_bps": coordinates[0],
                "slippage_bps": coordinates[1],
                "is_baseline": coordinates == _BASELINE,
                "parameter_set_id": point["parameter_set_id"],
                "oos_result_ref": point["out_of_sample_result_ref"],
                "evaluation_status": point["evaluation_status"],
                "reason_codes": point["reason_codes"],
                "status": status,
                "oos_trade_count": trades,
                "oos_net_return_ratio": net_return,
                "oos_net_return_delta_ratio": delta,
            }
        )
    statuses = {scenario["status"] for scenario in scenarios}
    if "INCOMPLETE_OOS_RESULT" in statuses:
        return "REQUIRE_COMPLETE_OOS_RESULTS", scenarios
    if "NO_OOS_TRADES_FOR_COMPARISON" in statuses:
        return "REQUIRE_OOS_TRADE_EVIDENCE", scenarios
    return "REVIEW_MODELED_COST_SENSITIVITY", scenarios


def _baseline_identity(result: Mapping[str, Any]) -> Mapping[str, Any]:
    baselines = [item for item in result["candidates"] if item["is_baseline"] is True]
    if len(baselines) != 1:
        raise ValueError("F2_META_BASELINE_MISMATCH")
    (baseline,) = baselines
    identity = baseline["experiment_identity"]
    validate_canonical_experiment_identity_v1(identity)
    source_digest = result["research_dataset_evidence"]["dataset_admissibility"]["dataset_digest"]
    if (baseline["fee_bps"], baseline["slippage_bps"]) != _BASELINE or identity[
        "dataset_digest"
    ] != domain_separated_digest("dataset", {"source_digest": source_digest}):
        raise ValueError("F2_META_BASELINE_MISMATCH")
    return identity


def build_f2_meta_cost_model_follow_up_v1(
    *,
    meta_record: Mapping[str, Any],
    expected_meta_identity: str,
    proposal_id: str,
    f2_result_path: Path,
    expected_f2_execution_digest: str,
) -> dict[str, Any]:
    """Bind one existing cost-model proposal to the matching F2 baseline model."""
    result = _read_f2_grid(f2_result_path, expected_f2_execution_digest)
    return _consume_meta_proposal(
        meta_record, expected_meta_identity, proposal_id, result, _baseline_identity(result)
    )


def _consume_meta_proposal(
    meta_record: Mapping[str, Any],
    expected_meta_identity: str,
    proposal_id: str,
    result: Mapping[str, Any],
    identity: Mapping[str, Any],
) -> dict[str, Any]:
    meta = canonical_record_payload_v1(meta_record)
    validate_canonical_meta_learning_v1(meta)
    if meta["meta_learning_identity"] != expected_meta_identity:
        raise ValueError("F2_META_RECORD_IDENTITY_MISMATCH")
    question = next(
        item
        for item in meta["questions"]
        if item["question_id"] == QUESTION_COST_MODEL_REALITY_UNDERESTIMATION
    )
    proposals = [
        proposal
        for proposal in question["research_proposals"]
        if proposal["proposal_id"] == proposal_id
    ]
    if len(proposals) != 1:
        raise ValueError("F2_META_COST_INVESTIGATION_REQUIRED")
    (proposal,) = proposals
    if (
        proposal not in meta["research_proposals"]
        or proposal["kind"] != PROPOSAL_INVESTIGATE
        or proposal["target_kind"] != "cost_model"
        or proposal["question_id"] != QUESTION_COST_MODEL_REALITY_UNDERESTIMATION
    ):
        raise ValueError("F2_META_COST_INVESTIGATION_REQUIRED")

    archive = result["research_dataset_evidence"]
    source_dataset_digest = archive["dataset_admissibility"]["dataset_digest"]
    dimensions = [
        name
        for name, field in COST_DIMENSION_DIGEST_FIELDS.items()
        if identity[field] == proposal["target"]
    ]
    if len(dimensions) != 1:
        raise ValueError("F2_META_COST_MODEL_NOT_BOUND_TO_BASELINE")
    (dimension,) = dimensions
    if not any(
        finding["dimension"] == dimension
        and finding["cost_model_digest"] == proposal["target"]
        and finding["underestimation_count"] > 0
        for finding in question["findings"]
    ):
        raise ValueError("F2_META_COST_FINDING_REQUIRED")
    disposition, scenarios = _axis_assessment(result, dimension=dimension)
    return {
        "schema_version": "f2_meta_cost_model_follow_up_v1",
        "authority": "NONE",
        "meta_learning_identity": expected_meta_identity,
        "proposal_id": proposal_id,
        "f2_execution_digest": result["execution_digest"],
        "f2_grid_result_digest": result["parameter_sensitivity_result_digest"],
        "baseline_identity_digest": identity["identity_digest"],
        "cost_model_digest": proposal["target"],
        "dimension": dimension,
        "instrument_id": archive["dataset_admissibility"]["instrument_id"],
        "native_instrument_id": archive["native_instrument_id"],
        "source_venue": archive["source_venue"],
        "dataset_digest": source_dataset_digest,
        "out_of_sample_period": archive["dataset_admissibility"]["out_of_sample_period"],
        "measurement_kind": "MODELED_OOS_COST_SCENARIOS",
        "disposition": disposition,
        "scenarios": scenarios,
    }


def build_f2_fill_fee_meta_follow_up_v1(
    *,
    proof_args: Mapping[str, Any],
    metadata_path: Path,
    expected_metadata_sha256: str,
    f2_result_path: Path,
    expected_f2_execution_digest: str,
    expected_fee_model_digest: str,
    as_of_utc: str,
    offline_fixture: bool = False,
) -> dict[str, Any]:
    """Investigate one confirmed order against the archived F2 taker fee assumption."""
    result = _read_f2_grid(f2_result_path, expected_f2_execution_digest)
    identity = _baseline_identity(result)
    fee_source = compute_content_sha256(
        {
            "f2_config_binding": "fee_model",
            "payload": {"fee_model_version": FEE_MODEL_VERSION, "fee_bps": BASELINE_FEE_BPS},
        }
    )
    if (
        not expected_fee_model_digest
        == identity["fee_model_digest"]
        == domain_separated_digest("fee_model", {"source_digest": fee_source})
    ):
        raise ValueError("F2_META_COST_MODEL_NOT_BOUND_TO_BASELINE")
    observation = read_authenticated_execution_fill_fee_observation_v1(**proof_args)
    archive = result["research_dataset_evidence"]
    instrument_id = archive["dataset_admissibility"]["instrument_id"]
    if (
        observation["instrument_id"],
        observation["native_instrument_id"],
        observation["venue"].upper(),
    ) != (instrument_id, archive["native_instrument_id"], archive["source_venue"].upper()):
        raise ValueError("F2_META_FILL_INSTRUMENT_MISMATCH")
    as_of = datetime.fromisoformat(as_of_utc)
    oos_period = archive["dataset_admissibility"]["out_of_sample_period"]
    if as_of.utcoffset() is None or as_of < datetime.fromisoformat(
        observation["reconciliation_known_at_utc"]
    ):
        raise ValueError("F2_META_FILL_LOOKAHEAD")
    if as_of < datetime.fromisoformat(oos_period.split("..")[1]):
        raise ValueError("F2_META_ARCHIVE_LOOKAHEAD")
    created_at = as_of.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    measurement = measure_linear_swap_taker_fee_v1(
        observation, metadata_path=metadata_path, expected_metadata_sha256=expected_metadata_sha256
    )
    observed_bps = float(Fraction(measurement["fee_bps_exact"]))
    experiment_id = derive_experiment_id_v1(identity["identity_digest"])
    gap = canonical_record_payload_v1(
        build_canonical_reality_gap_record_v1(
            CanonicalRealityGapRecordRequestV1(
                experiment_identity=identity,
                observed_surface=observation["execution_environment"],
                metric_definitions=METRIC_DEFINITION_VERSION,
                threshold_policy_digest=compute_content_sha256(
                    {"purpose": "descriptive_fee_difference", "threshold_bps": 0.0}
                ),
                gap_dimensions=(
                    RealityGapDimensionV1("fee", BASELINE_FEE_BPS, observed_bps, 0.0, "bps"),
                ),
                evidence_refs=(
                    {
                        "kind": EVIDENCE_KIND_EXPERIMENT_RECORD,
                        "ref": experiment_id,
                        "digest": expected_f2_execution_digest,
                    },
                    {
                        "kind": ARTIFACT_KIND_STORE_RELATIVE_REF,
                        "ref": f"{observation['budget_revision_ref'][1]}.json#fills-get-body",
                        "digest": observation["fills_get_body_sha256"],
                    },
                    {
                        "kind": ARTIFACT_KIND_STORE_RELATIVE_REF,
                        "ref": metadata_path.name,
                        "digest": expected_metadata_sha256,
                    },
                ),
                created_at=created_at,
            )
        )
    )
    unit = MetaLearningExperimentUnitV1(
        experiment_identity=identity,
        evidence_created_at=created_at,
        strategy_family=result["f2_config_authority"]["strategy_id"],
        hypothesis_id=GRID_ID,
        hypothesis_kind="fee_model_check",
        search_space_id=GRID_ID,
        parameter_region={"fee_bps": BASELINE_FEE_BPS},
        regime="unstratified",
        time_horizon={"out_of_sample": oos_period},
        market_universe=(instrument_id,),
        robustness_test_statuses={},
        backtest_metrics={},
    )
    # One order is a descriptive diagnostic. Keep the default associative sample gate.
    meta = canonical_record_payload_v1(
        build_canonical_meta_learning_v1(
            CanonicalMetaLearningRequestV1(
                units=(unit,),
                created_at=created_at,
                policy=replace(canonical_meta_learning_policy_v1(), min_sample_size_descriptive=1),
                reality_gap_records=(gap,),
            )
        )
    )
    question = next(
        item
        for item in meta["questions"]
        if item["question_id"] == QUESTION_COST_MODEL_REALITY_UNDERESTIMATION
    )
    (finding,) = question["findings"]
    follow_up = None
    if question["research_proposals"]:
        (proposal,) = question["research_proposals"]
        follow_up = _consume_meta_proposal(
            meta, meta["meta_learning_identity"], proposal["proposal_id"], result, identity
        )
    return {
        "schema_version": "f2_fill_fee_meta_follow_up_v1",
        "authority": "NONE",
        "evidence_profile": "OFFLINE_FIXTURE" if offline_fixture else "HISTORICAL_K1_ARCHIVE",
        "sample_scope": "ONE_CONFIRMED_ORDER",
        "f2_execution_digest": expected_f2_execution_digest,
        "fee_model_digest": expected_fee_model_digest,
        "fee_observation": observation,
        "fee_measurement": measurement,
        "reality_gap": gap,
        "meta_record": meta,
        "consumed_fee_finding": finding,
        "follow_up": follow_up,
        "disposition": follow_up["disposition"] if follow_up else "NO_FEE_UNDERESTIMATION_OBSERVED",
    }
