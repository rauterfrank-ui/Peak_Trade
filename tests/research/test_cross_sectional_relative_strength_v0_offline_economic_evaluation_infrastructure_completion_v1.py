"""Contract tests for cross-sectional infrastructure completion v1."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from src.research.cross_sectional_bound_period_panel_source_materialization_v1 import (
    BoundPeriodSourceMaterializationStatus,
    materialize_bound_period_panel_from_raw_sources_v1,
    parse_native_instrument_id_from_raw_filename,
)
from src.research.cross_sectional_panel_staging_source_manifest_v1 import (
    SourceManifestStatus,
    materialize_panel_staging_source_manifests_v1,
    verify_panel_staging_source_manifests_v1,
)
from src.research.cross_sectional_relative_strength_v0_bound_panel_dataset_materialization_v0 import (
    MaterializationTerminalStatus,
    materialize_bound_panel_dataset_v0,
)
from src.research.cross_sectional_relative_strength_v0_offline_economic_evaluation_execution_v0 import (
    ALLOWED_EVALUATION_STAGES,
    INFRASTRUCTURE_GO_TOKEN,
    RUNNER_SCRIPT,
    EvaluationEntrypointTerminalStatus,
    run_full_evaluation_entrypoint_dry_run_v1,
    verify_full_evaluation_precheck_v1,
)
from src.research.cross_sectional_relative_strength_v0_offline_economic_evaluation_scope_ratification_v0 import (
    materialize_cross_sectional_offline_economic_evaluation_scope_ratification_v0,
)
from src.research.cross_sectional_relative_strength_v0_versioned_research_binding_v0 import (
    materialize_versioned_research_binding_v0,
)
from tests.research.fixtures.cross_sectional_relative_strength_v0.fixture_builder import (
    build_synthetic_panel_series_v0,
)
from tests.research.fixtures.cross_sectional_relative_strength_v0.staging_builder import (
    write_bound_period_staging_v0,
    write_foreign_2026_staging_v0,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
ARCHIVE_ROOT = Path("/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z")
FOREIGN_SOURCE_ROOT = (
    ARCHIVE_ROOT / "datasets/admissible_futures/pit_okx_linear_usdt_non_bitcoin_pt1h_panel/v1"
)


@pytest.fixture(name="complete_binding")
def fixture_complete_binding() -> dict:
    return materialize_versioned_research_binding_v0()


@pytest.fixture(name="scope_ratification")
def fixture_scope_ratification(complete_binding: dict) -> dict:
    return materialize_cross_sectional_offline_economic_evaluation_scope_ratification_v0(
        repo_root=REPO_ROOT,
        versioned_binding=complete_binding,
    )


@pytest.fixture(name="bound_staging")
def fixture_bound_staging() -> Path:
    tmp = Path(tempfile.mkdtemp(prefix="cs_rs_bound_staging_v1_"))
    staging = write_bound_period_staging_v0(tmp)
    lifecycle = staging / "lifecycle"
    lifecycle.mkdir(parents=True, exist_ok=True)
    (lifecycle / "SOURCE_REGISTRATION.json").write_text(
        json.dumps(
            {
                "source_snapshot_ref": "test:fixture",
                "source_snapshot_digest": "a" * 64,
                "registered": True,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    manifest_result = materialize_panel_staging_source_manifests_v1(staging)
    assert manifest_result.status is SourceManifestStatus.VERIFIED
    return staging


def test_infrastructure_go_token_v1_constant() -> None:
    assert (
        INFRASTRUCTURE_GO_TOKEN
        == "GO_BOUNDED_CROSS_SECTIONAL_RELATIVE_STRENGTH_V0_OFFLINE_ECONOMIC_EVALUATION_INFRASTRUCTURE_COMPLETION_V1"
    )


def test_parse_native_instrument_id_from_raw_filename() -> None:
    assert (
        parse_native_instrument_id_from_raw_filename("ohlcv_eth_usdt_swap_p0000_abc.json")
        == "ETH-USDT-SWAP"
    )


def test_source_manifest_generation_and_verify(bound_staging: Path) -> None:
    ok, rc, reasons = verify_panel_staging_source_manifests_v1(bound_staging)
    assert ok is True
    assert rc == 0
    assert reasons == ()
    assert (bound_staging / "MANIFEST.sha256").is_file()
    assert (bound_staging / "panel" / "MANIFEST.sha256").is_file()
    assert (bound_staging / "lifecycle" / "MANIFEST.sha256").is_file()


def test_bound_period_materialization_from_archive_raw_fail_closed(
    complete_binding: dict,
) -> None:
    if not FOREIGN_SOURCE_ROOT.is_dir():
        pytest.skip("foreign source archive not present")
    with tempfile.TemporaryDirectory() as tmp:
        output = Path(tmp) / "bound_output"
        result = materialize_bound_period_panel_from_raw_sources_v1(
            FOREIGN_SOURCE_ROOT,
            output,
            period_binding=complete_binding["period_binding"],
        )
        assert (
            result.status
            is BoundPeriodSourceMaterializationStatus.BOUND_DATA_UNAVAILABLE_FAIL_CLOSED
        )
        assert "FOREIGN_DATASET_PERIOD_REJECTED" in result.reason_codes or (
            "BOUND_PERIOD_SOURCE_DATA_UNAVAILABLE" in result.reason_codes
        )


def test_foreign_panel_rejected_after_manifests(complete_binding: dict) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        foreign = write_foreign_2026_staging_v0(Path(tmp) / "foreign")
        materialize_panel_staging_source_manifests_v1(foreign)
        result = materialize_bound_panel_dataset_v0(
            foreign,
            period_binding=complete_binding["period_binding"],
        )
        assert result.status is MaterializationTerminalStatus.BOUND_DATA_UNAVAILABLE_FAIL_CLOSED


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
        go_token=INFRASTRUCTURE_GO_TOKEN,
    )
    assert ok is True, reasons
    assert materialization.status is MaterializationTerminalStatus.DATASET_MATERIALIZATION_COMPLETE
    assert materialization.panel_data_digest != "0" * 64


def test_full_evaluation_entrypoint_dry_run_stops_before_execution(
    bound_staging: Path,
    scope_ratification: dict,
    complete_binding: dict,
) -> None:
    panel = build_synthetic_panel_series_v0()
    result = run_full_evaluation_entrypoint_dry_run_v1(
        repo_root=REPO_ROOT,
        ratification=scope_ratification,
        staging_root=bound_staging,
        panel_series=panel,
        versioned_binding=complete_binding,
        go_token=INFRASTRUCTURE_GO_TOKEN,
    )
    assert result.status is EvaluationEntrypointTerminalStatus.ENTRYPOINT_READY_DRY_RUN_STOPPED
    assert result.dry_run_stopped_before_execution is True
    assert result.economic_evaluation_executed is False
    assert len(result.stage_wiring) == len(ALLOWED_EVALUATION_STAGES)
    assert all(item.wired for item in result.stage_wiring)


def test_precheck_fails_without_manifests(
    complete_binding: dict,
    scope_ratification: dict,
) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        staging = write_bound_period_staging_v0(Path(tmp))
        ok, reasons, _ = verify_full_evaluation_precheck_v1(
            repo_root=REPO_ROOT,
            ratification=scope_ratification,
            staging_root=staging,
            versioned_binding=complete_binding,
            go_token=INFRASTRUCTURE_GO_TOKEN,
        )
        assert ok is False
        assert any("SOURCE_MANIFEST" in reason for reason in reasons)


def test_economic_evaluation_not_executed_regression(
    bound_staging: Path,
    scope_ratification: dict,
    complete_binding: dict,
) -> None:
    panel = build_synthetic_panel_series_v0()
    result = run_full_evaluation_entrypoint_dry_run_v1(
        repo_root=REPO_ROOT,
        ratification=scope_ratification,
        staging_root=bound_staging,
        panel_series=panel,
        versioned_binding=complete_binding,
    )
    assert result.economic_evaluation_executed is False


def test_runner_script_exists() -> None:
    assert (REPO_ROOT / RUNNER_SCRIPT).is_file()


def test_allowed_evaluation_stages_complete() -> None:
    assert ALLOWED_EVALUATION_STAGES == (
        "OFFLINE_BACKTEST",
        "WALK_FORWARD",
        "MONTE_CARLO",
        "STRESS",
        "PARAMETER_SENSITIVITY",
        "ECONOMIC_VIABILITY_EVIDENCE_MATERIALIZATION",
    )


def test_bound_staging_dataset_digest_deterministic(
    bound_staging: Path,
    complete_binding: dict,
) -> None:
    first = materialize_bound_panel_dataset_v0(
        bound_staging,
        period_binding=complete_binding["period_binding"],
    )
    second = materialize_bound_panel_dataset_v0(
        bound_staging,
        period_binding=complete_binding["period_binding"],
    )
    assert first.panel_data_digest == second.panel_data_digest
    assert first.idempotent_digest_stable is True
