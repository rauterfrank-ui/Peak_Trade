"""Fixtures for research_validity_evidence_v1 contract tests."""

from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any

from scripts.ops.primary_evidence_retention_v0 import write_manifest_sha256
from src.experiments.base import ExperimentConfig, ParamSweep
from src.experiments.experiment_identity_manifest_v1 import (
    ARTIFACT_FILENAME as EXPERIMENT_IDENTITY_ARTIFACT_REL,
    produce_experiment_identity_manifest_v1,
)
from src.meta.learning_loop.comparison_checkpoint_v1 import produce_comparison_checkpoint_v1
from src.meta.learning_loop.comparison_common_durable_evidence_binding_v1 import (
    produce_comparison_common_durable_evidence_bundle_v1,
)
from src.meta.learning_loop.comparison_metric_input_durable_evidence_binding_v1 import (
    produce_comparison_metric_input_durable_evidence_bundle_v1,
)
from src.meta.learning_loop.comparison_ssot_definition_durable_evidence_binding_v1 import (
    produce_comparison_ssot_definition_durable_evidence_bundle_v1,
)
from src.meta.learning_loop.comparison_ssot_result_durable_evidence_binding_v1 import (
    produce_comparison_ssot_result_durable_evidence_bundle_v1,
)
from src.meta.learning_loop.comparison_ssot_v1.producer import produce_comparison_offline_v1
from src.meta.learning_loop.contract_safety_v1 import (
    compute_content_sha256,
    deterministic_json_dumps,
)
from src.meta.learning_loop.research_validity_evidence_v1 import (
    INPUT_ARTIFACT_CONTRACT,
    INPUT_ARTIFACT_FILENAME,
    INPUT_ARTIFACT_VERSION,
    InputArtifactKind,
    ResearchValidityProducerInputs,
)
from tests.meta.comparison_ssot_v1_fixtures import produce_two_compatible_backtest_inputs


def _write_manifested_bundle(
    bundle_dir: Path, *, artifact_rel: str, payload: dict[str, Any]
) -> None:
    bundle_dir.mkdir(parents=True, exist_ok=True)
    artifact_path = bundle_dir / artifact_rel
    body = dict(payload)
    body["integrity"] = {
        "content_sha256": compute_content_sha256(
            {k: v for k, v in body.items() if k != "integrity"}
        )
    }
    artifact_path.write_text(deterministic_json_dumps(body), encoding="utf-8")
    write_manifest_sha256(bundle_dir)


def _build_input_artifact(
    *,
    kind: InputArtifactKind,
    producer_ref: str,
    evidence_status: str = "PASS",
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "contract_name": INPUT_ARTIFACT_CONTRACT,
        "contract_version": INPUT_ARTIFACT_VERSION,
        "artifact_kind": kind.value,
        "evidence_status": evidence_status,
        "producer_ref": producer_ref,
    }
    if extra:
        payload.update(extra)
    return payload


def produce_experiment_identity_bundle(tmp_path: Path, durable_root: Path) -> Path:
    out = durable_root / f"experiment_identity_{uuid.uuid4().hex[:8]}"
    config = ExperimentConfig(
        name="RV Test Experiment",
        strategy_name="ma_crossover",
        param_sweeps=[
            ParamSweep("fast", [5, 10]),
            ParamSweep("slow", [20, 30]),
        ],
        symbols=["ETH/EUR"],
        timeframe="1h",
        start_date="2024-01-01",
        end_date="2024-06-01",
        initial_capital=10000.0,
        base_params={"data_source": "synthetic_fixture_v1"},
    )
    produce_experiment_identity_manifest_v1(config, out)
    write_manifest_sha256(out)
    return out


def produce_research_input_bundle(
    durable_root: Path,
    *,
    kind: InputArtifactKind,
    producer_ref: str,
    extra: dict[str, Any] | None = None,
    evidence_status: str = "PASS",
) -> Path:
    out = durable_root / f"{kind.value}_{uuid.uuid4().hex[:8]}"
    payload = _build_input_artifact(
        kind=kind,
        producer_ref=producer_ref,
        evidence_status=evidence_status,
        extra=extra,
    )
    _write_manifested_bundle(out, artifact_rel=INPUT_ARTIFACT_FILENAME, payload=payload)
    return out


def produce_checkpoint_bundle(tmp_path: Path, durable_root: Path) -> Path:
    metric_root = durable_root / "metric_inputs"
    metric_root.mkdir(exist_ok=True)
    first, second = produce_two_compatible_backtest_inputs(tmp_path, metric_root)
    comparison_root = durable_root / "comparisons"
    comparison_root.mkdir(exist_ok=True)
    offline = produce_comparison_offline_v1(
        input_manifest_paths=[first, second],
        output_root=comparison_root,
        ranking_rule_version="NONE_V1",
    )
    metric_bindings = []
    for idx, manifest_path in enumerate([first, second]):
        out = durable_root / f"metric_input_binding_{idx}"
        produce_comparison_metric_input_durable_evidence_bundle_v1(
            manifest_path=manifest_path,
            output_dir=out,
        )
        metric_bindings.append(out)
    definition_binding = durable_root / "definition_binding"
    produce_comparison_ssot_definition_durable_evidence_bundle_v1(
        manifest_path=offline.definition_path,
        output_dir=definition_binding,
    )
    result_binding = durable_root / "result_binding"
    produce_comparison_ssot_result_durable_evidence_bundle_v1(
        manifest_path=offline.result_path,
        output_dir=result_binding,
    )
    common_out = durable_root / "common_bundle"
    produce_comparison_common_durable_evidence_bundle_v1(
        definition_bound_bundle_dir=definition_binding,
        result_bound_bundle_dir=result_binding,
        metric_input_bound_bundle_dirs=metric_bindings,
        output_dir=common_out,
    )
    checkpoint_out = durable_root / "checkpoint"
    produce_comparison_checkpoint_v1(common_bundle_dir=common_out, output_dir=checkpoint_out)
    return checkpoint_out


def produce_full_research_validity_inputs(
    tmp_path: Path,
    durable_root: Path,
    *,
    all_domains_pass: bool = True,
) -> ResearchValidityProducerInputs:
    experiment_bundle = produce_experiment_identity_bundle(tmp_path, durable_root)
    from src.meta.learning_loop.comparison_ssot_v1.io import read_manifest

    experiment_manifest = read_manifest(experiment_bundle / EXPERIMENT_IDENTITY_ARTIFACT_REL)
    experiment_id = experiment_manifest["experiment_identity_id"]
    end_date = experiment_manifest["identity_config"]["end_date"]

    dataset_bundle = produce_research_input_bundle(
        durable_root,
        kind=InputArtifactKind.DATASET_IDENTITY,
        producer_ref="src/meta/learning_loop/comparison_metric_input_v1/comparability.py",
        extra={
            "dataset_identity_id": compute_content_sha256(
                {"data_source": "synthetic_fixture_v1", "experiment_identity_id": experiment_id}
            ),
            "experiment_identity_id": experiment_id,
            "data_cutoff_timestamp": f"{end_date}T23:59:59+00:00",
            "dataset_lineage_ref": "synthetic_fixture_v1",
        },
    )
    partition_bundle = produce_research_input_bundle(
        durable_root,
        kind=InputArtifactKind.TRAIN_VALIDATION_TEST_PARTITION,
        producer_ref="src/backtest/walkforward.py",
        extra={
            "partition": {
                "train": {"start": "2024-01-01", "end": "2024-03-31"},
                "validation": {"start": "2024-04-01", "end": "2024-04-30"},
                "test": {"start": "2024-05-01", "end": "2024-06-01"},
            }
        },
    )
    selection_bundle = produce_research_input_bundle(
        durable_root,
        kind=InputArtifactKind.SELECTION_PROCEDURE,
        producer_ref="src/experiments/base.py",
        extra={
            "number_of_trials": 4,
            "selection_procedure": {
                "procedure_kind": "CARTESIAN_PARAM_SWEEP",
                "description": "Descriptive non-authorizing sweep metadata only",
                "ranking_applied": False,
            },
        },
    )
    wf_bundle = produce_research_input_bundle(
        durable_root,
        kind=InputArtifactKind.WALK_FORWARD_RESULT,
        producer_ref="src/backtest/walkforward.py",
    )
    cost_bundle = produce_research_input_bundle(
        durable_root,
        kind=InputArtifactKind.COST_STRESS_RESULT,
        producer_ref="src/experiments/stress_tests.py",
    )
    slip_bundle = produce_research_input_bundle(
        durable_root,
        kind=InputArtifactKind.SLIPPAGE_STRESS_RESULT,
        producer_ref="src/backtest/engine.py",
    )
    deferred_status = "PASS" if all_domains_pass else "NOT_EVALUABLE"
    overfit_status = "PASS" if all_domains_pass else "INCOMPLETE"

    fund_bundle = produce_research_input_bundle(
        durable_root,
        kind=InputArtifactKind.FUNDING_STRESS_RESULT,
        producer_ref="src/experiments/stress_tests.py",
        evidence_status=deferred_status,
        extra=None
        if all_domains_pass
        else {"deferred_reason": "FUTURES_ONLY funding stress artifact not present in min slice"},
    )
    param_bundle = produce_research_input_bundle(
        durable_root,
        kind=InputArtifactKind.PARAMETER_STABILITY_RESULT,
        producer_ref="src/backtest/walkforward.py",
    )
    regime_bundle = produce_research_input_bundle(
        durable_root,
        kind=InputArtifactKind.REGIME_BREAKDOWN,
        producer_ref="src/analytics/regimes.py",
    )
    overfit_bundle = produce_research_input_bundle(
        durable_root,
        kind=InputArtifactKind.OVERFITTING_RISK_RESULT,
        producer_ref="src/experiments/strategy_profiles.py",
        evidence_status=overfit_status,
        extra=None
        if all_domains_pass
        else {"deferred_reason": "Extended hardening not required for minimum safe slice"},
    )
    checkpoint_bundle = produce_checkpoint_bundle(tmp_path, durable_root)

    return ResearchValidityProducerInputs(
        checkpoint_bundle_dir=checkpoint_bundle,
        experiment_identity_bundle_dir=experiment_bundle,
        dataset_identity_bundle_dir=dataset_bundle,
        partition_evidence_bundle_dir=partition_bundle,
        selection_procedure_bundle_dir=selection_bundle,
        walk_forward_result_bundle_dir=wf_bundle,
        cost_stress_result_bundle_dir=cost_bundle,
        slippage_stress_result_bundle_dir=slip_bundle,
        funding_stress_result_bundle_dir=fund_bundle,
        parameter_stability_result_bundle_dir=param_bundle,
        regime_breakdown_bundle_dir=regime_bundle,
        overfitting_risk_result_bundle_dir=overfit_bundle,
    )
