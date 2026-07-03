"""Completion tests for funding-rate carry infrastructure recovery v1."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from scripts.ops.materialize_cross_sectional_funding_rate_carry_v0_bound_panel_funding_dataset_v0 import (
    CONFIRM_GO as MATERIALIZE_CONFIRM_GO,
    materialize_bound_panel_funding_dataset_v0,
)
from scripts.ops.run_cross_sectional_funding_rate_carry_v0_offline_economic_evaluation_execution_v0 import (
    CONFIRM_GO,
    run_execution_infrastructure_recovery_v0,
)
from src.research.cross_sectional_funding_rate_carry_v0_offline_economic_evaluation_execution_v0 import (
    ALLOWED_EVALUATION_STAGES,
    INFRASTRUCTURE_GO_TOKEN,
    RUNNER_SCRIPT,
    EvaluationEntrypointTerminalStatus,
    load_ops_evaluation_config_v0,
    run_full_evaluation_entrypoint_dry_run_v1,
    verify_full_evaluation_precheck_v1,
)
from src.research.cross_sectional_funding_rate_carry_v0_offline_economic_evaluation_scope_ratification_v0 import (
    materialize_funding_carry_offline_economic_evaluation_scope_ratification_v0,
)
from src.research.cross_sectional_funding_rate_carry_v0_versioned_research_binding_v0 import (
    materialize_versioned_research_binding_v0,
)
from src.research.cross_sectional_panel_staging_source_manifest_v1 import (
    SourceManifestStatus,
    materialize_panel_staging_source_manifests_v1,
    verify_panel_staging_source_manifests_v1,
)
from tests.research.test_cross_sectional_funding_rate_carry_v0_offline_economic_evaluation_execution_infrastructure_v0 import (  # noqa: E501
    _write_staging_with_funding,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
_INFRA_GO = INFRASTRUCTURE_GO_TOKEN


@pytest.fixture(name="complete_binding")
def fixture_complete_binding() -> dict:
    return materialize_versioned_research_binding_v0()


@pytest.fixture(name="scope_ratification")
def fixture_scope_ratification(complete_binding: dict) -> dict:
    return materialize_funding_carry_offline_economic_evaluation_scope_ratification_v0(
        repo_root=REPO_ROOT,
        versioned_binding=complete_binding,
    )


@pytest.fixture(name="bound_staging")
def fixture_bound_staging() -> Path:
    tmp = Path(tempfile.mkdtemp(prefix="cs_funding_completion_v1_"))
    return _write_staging_with_funding(tmp)


def test_infrastructure_go_token_constant() -> None:
    assert INFRASTRUCTURE_GO_TOKEN == CONFIRM_GO
    assert MATERIALIZE_CONFIRM_GO == CONFIRM_GO


def test_runner_script_exists() -> None:
    assert (REPO_ROOT / RUNNER_SCRIPT).is_file()


def test_source_manifest_generation_and_verify(bound_staging: Path) -> None:
    result = materialize_panel_staging_source_manifests_v1(bound_staging)
    assert result.status is SourceManifestStatus.VERIFIED
    ok, rc, reasons = verify_panel_staging_source_manifests_v1(bound_staging)
    assert ok is True
    assert rc == 0
    assert reasons == ()


def test_materializer_reuses_verified_manifest(bound_staging: Path) -> None:
    first = materialize_bound_panel_funding_dataset_v0(
        confirm=INFRASTRUCTURE_GO_TOKEN,
        staging_root=bound_staging,
        skip_fetch=True,
    )
    second = materialize_bound_panel_funding_dataset_v0(
        confirm=INFRASTRUCTURE_GO_TOKEN,
        staging_root=bound_staging,
        skip_fetch=True,
    )
    assert first["verdict"] in {"BOUND_FUNDING_PANEL_READY", "BOUND_FUNDING_PANEL_READY_REUSED"}
    assert second["verdict"] == "BOUND_FUNDING_PANEL_READY_REUSED"
    assert second["manifest_verified"] is True


def test_full_precheck_passes_with_bound_staging(
    bound_staging: Path,
    scope_ratification: dict,
    complete_binding: dict,
) -> None:
    ok, reasons, materialization = verify_full_evaluation_precheck_v1(
        repo_root=REPO_ROOT,
        ratification=scope_ratification,
        staging_root=bound_staging,
        versioned_binding=complete_binding,
        go_token=_INFRA_GO,
    )
    assert ok is True, reasons
    assert materialization.data_digest_match is True
    assert materialization.panel_data_digest == complete_binding["data_digest"]


def test_precheck_fails_without_manifests(scope_ratification: dict, complete_binding: dict) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        staging = _write_staging_with_funding(Path(tmp), with_manifests=False)
        ok, reasons, _ = verify_full_evaluation_precheck_v1(
            repo_root=REPO_ROOT,
            ratification=scope_ratification,
            staging_root=staging,
            versioned_binding=complete_binding,
            go_token=_INFRA_GO,
        )
        assert ok is False
        assert any("SOURCE_MANIFEST" in reason for reason in reasons)


def test_full_entrypoint_dry_run_stops_before_execution(
    bound_staging: Path,
    scope_ratification: dict,
    complete_binding: dict,
) -> None:
    panel_series, _ = __import__(
        "src.research.pit_futures_cross_sectional_research_data_digest_period_split_materialization_v0",
        fromlist=["load_panel_series_from_staging"],
    ).load_panel_series_from_staging(bound_staging)
    result = run_full_evaluation_entrypoint_dry_run_v1(
        repo_root=REPO_ROOT,
        ratification=scope_ratification,
        staging_root=bound_staging,
        panel_series=panel_series,
        versioned_binding=complete_binding,
        go_token=_INFRA_GO,
    )
    assert result.status is EvaluationEntrypointTerminalStatus.ENTRYPOINT_READY_DRY_RUN_STOPPED
    assert result.economic_evaluation_executed is False
    assert result.dry_run_stopped_before_execution is True
    assert len(result.stage_wiring) == len(ALLOWED_EVALUATION_STAGES)


def test_infrastructure_recovery_runner_writes_bundle_without_eval(bound_staging: Path) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        durable = Path(tmp) / "archive"
        durable.mkdir(parents=True, exist_ok=True)
        result = run_execution_infrastructure_recovery_v0(
            confirm=INFRASTRUCTURE_GO_TOKEN,
            durable_evidence_root=durable,
            primary_worktree=REPO_ROOT,
            staging_root=bound_staging,
            skip_fetch=True,
        )
        assert result["economic_evaluation_executed"] is False
        assert result["manifest_verify_rc"] == 0
        bundle_dir = Path(result["bundle_dir"])
        assert (bundle_dir / "ECONOMIC_EVALUATION_EXECUTED.txt").is_file()
        assert (bundle_dir / "ECONOMIC_EVALUATION_EXECUTED.txt").read_text(
            encoding="utf-8"
        ).strip() == "ECONOMIC_EVALUATION_EXECUTED=false"


def test_runner_fails_with_invalid_token(bound_staging: Path) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        with pytest.raises(SystemExit):
            run_execution_infrastructure_recovery_v0(
                confirm="INVALID_TOKEN",
                durable_evidence_root=Path(tmp),
                primary_worktree=REPO_ROOT,
                staging_root=bound_staging,
                skip_fetch=True,
            )


def test_ops_config_contract_values() -> None:
    cfg = load_ops_evaluation_config_v0(REPO_ROOT)
    assert cfg["cross_sectional_evaluation_binding_v1"]["data_contract_digest"] == (
        "0c4f26bfa044f82c3bda505906bcf59da3ff43ad4a63b1e8da6b97ce8b730224"
    )
    assert cfg["economic_evaluation_v1"]["economic_policy_binding"] == "economic_validity_policy_v1"
    assert cfg["timeout_contract"]["max_runtime_seconds"] == 1500
