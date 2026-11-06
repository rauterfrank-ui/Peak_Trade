"""Contract tests for funding-rate extreme-carry-reversion execution infrastructure v0."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from src.research.cross_sectional_funding_rate_extreme_carry_reversion_v0_bound_panel_dataset_materialization_v0 import (
    MaterializationTerminalStatus,
    materialize_bound_funding_panel_dataset_v0,
)
from src.research.cross_sectional_funding_rate_extreme_carry_reversion_v0_offline_economic_evaluation_execution_v0 import (
    AUTHORITY_EFFECT,
    GO_TOKEN,
    INFRASTRUCTURE_GO_TOKEN,
    RUNTIME_EFFECT,
    entrypoint_result_to_dict,
    load_ops_evaluation_config_v0,
    materialize_infrastructure_summary_v0,
    run_contract_smoke_evaluation_v0,
    run_full_evaluation_entrypoint_dry_run_v1,
    verify_execution_start_state_v0,
    verify_full_evaluation_precheck_v1,
)
from src.research.cross_sectional_funding_rate_extreme_carry_reversion_v0_offline_economic_evaluation_infrastructure_readiness_v0 import (
    evaluate_extreme_carry_reversion_offline_evaluation_infrastructure_readiness_v0,
    readiness_result_to_dict,
)
from src.research.cross_sectional_funding_rate_extreme_carry_reversion_v0_offline_economic_evaluation_scope_ratification_v0 import (
    materialize_extreme_carry_reversion_offline_economic_evaluation_scope_ratification_v0,
)
from src.research.cross_sectional_funding_rate_extreme_carry_reversion_v0_versioned_research_binding_v0 import (
    materialize_and_validate_versioned_research_binding_v0,
    materialize_versioned_research_binding_v0,
)
from src.research.cross_sectional_panel_staging_source_manifest_v1 import (
    SourceManifestStatus,
    materialize_panel_staging_source_manifests_v1,
)
from tests.research.fixtures.cross_sectional_funding_rate_rank_delta_v0.fixture_builder import (
    build_synthetic_ohlcv_panel_v0,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
_INFRA_GO = INFRASTRUCTURE_GO_TOKEN


def _write_staging_with_funding(
    root: Path,
    *,
    with_manifests: bool = True,
) -> Path:
    panel = build_synthetic_ohlcv_panel_v0()
    panel_dir = root / "panel"
    lifecycle = root / "lifecycle"
    panel_dir.mkdir(parents=True, exist_ok=True)
    lifecycle.mkdir(parents=True, exist_ok=True)

    funding_rows: list[dict[str, object]] = []
    for series_idx, series in enumerate(panel):
        for bar_idx, bar in enumerate(series.bars):
            funding_rows.append(
                {
                    "instrument_id": bar.instrument_id,
                    "native_instrument_id": series.native_instrument_id,
                    "timestamp_utc": bar.timestamp_utc,
                    "open": bar.open,
                    "high": bar.high,
                    "low": bar.low,
                    "close": bar.close,
                    "volume": bar.volume,
                    "funding_rate": str(-0.0002 + series_idx * 0.00003 + bar_idx * 0.000001),
                    "is_final": bar.is_final,
                }
            )

    funding_rows.sort(key=lambda row: (str(row["instrument_id"]), str(row["timestamp_utc"])))
    funding_digest = (
        __import__("hashlib")
        .sha256(
            json.dumps(
                funding_rows, sort_keys=True, separators=(",", ":"), ensure_ascii=False
            ).encode("utf-8")
        )
        .hexdigest()
    )

    (panel_dir / "normalized_panel_bars_with_funding.json").write_text(
        json.dumps({"bars": funding_rows}, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (panel_dir / "panel_funding_dataset_manifest.json").write_text(
        json.dumps(
            {
                "schema_version": "pit_okx_pt1h_panel_funding_dataset_manifest_v1",
                "panel_id": "pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_research_v1",
                "dataset_extension": "extended_chronological_with_funding_v1",
                "row_count_total": len(funding_rows),
                "funding_panel_digest": funding_digest,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
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
    if with_manifests:
        manifest = materialize_panel_staging_source_manifests_v1(root)
        assert manifest.status is SourceManifestStatus.VERIFIED
    return root


@pytest.fixture(name="complete_binding")
def fixture_complete_binding() -> dict:
    return materialize_versioned_research_binding_v0()


@pytest.fixture(name="scope_ratification")
def fixture_scope_ratification(complete_binding: dict) -> dict:
    return materialize_extreme_carry_reversion_offline_economic_evaluation_scope_ratification_v0(
        repo_root=REPO_ROOT,
        versioned_binding=complete_binding,
    )


@pytest.fixture(name="bound_staging")
def fixture_bound_staging() -> Path:
    tmp = Path(tempfile.mkdtemp(prefix="cs_extreme_carry_reversion_exec_v0_"))
    return _write_staging_with_funding(tmp)


def test_go_token_constants() -> None:
    assert GO_TOKEN == (
        "GO_CROSS_SECTIONAL_FUNDING_RATE_EXTREME_CARRY_REVERSION_V0_OFFLINE_ECONOMIC_EVALUATION_"
        "EXECUTION_NO_RUNTIME_AUTHORITY_V0"
    )
    assert INFRASTRUCTURE_GO_TOKEN == (
        "GO_BOUNDED_CROSS_SECTIONAL_FUNDING_RATE_EXTREME_CARRY_REVERSION_V0_OFFLINE_ECONOMIC_EVALUATION_"
        "INFRASTRUCTURE_COMPLETION_V0"
    )


def test_no_runtime_authority_effect_constants() -> None:
    assert AUTHORITY_EFFECT == "NONE"
    assert RUNTIME_EFFECT == "NONE"


def test_binding_materialization_complete_accepted() -> None:
    result = materialize_and_validate_versioned_research_binding_v0()
    assert result.validation_verdict.value == "ACCEPTED_COMPLETE"


def test_readiness_fail_closed_before_wiring_removed(complete_binding: dict) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        incomplete_repo = Path(tmp)
        readiness = evaluate_extreme_carry_reversion_offline_evaluation_infrastructure_readiness_v0(
            repo_root=incomplete_repo,
            versioned_binding=complete_binding,
        )
        assert readiness.evaluation_infrastructure_ready is False
        assert readiness.blockers


def test_readiness_true_when_wiring_complete(
    complete_binding: dict,
    scope_ratification: dict,
) -> None:
    readiness = evaluate_extreme_carry_reversion_offline_evaluation_infrastructure_readiness_v0(
        repo_root=REPO_ROOT,
        versioned_binding=complete_binding,
        ratification=scope_ratification,
    )
    assert readiness.evaluation_infrastructure_ready is True
    assert readiness.blockers == ()
    assert readiness.evaluation_execution_authorized is False
    assert readiness.runtime_authority is False
    assert readiness.economic_evaluation_executed is False


def test_readiness_dict_contains_no_economic_metrics(
    scope_ratification: dict,
) -> None:
    readiness = evaluate_extreme_carry_reversion_offline_evaluation_infrastructure_readiness_v0(
        repo_root=REPO_ROOT,
        ratification=scope_ratification,
    )
    payload = readiness_result_to_dict(readiness)
    forbidden = ("net_return", "profit_factor", "sharpe", "max_drawdown", "calmar")
    serialized = json.dumps(payload)
    for key in forbidden:
        assert key not in serialized


def test_scope_ratification_reports_infrastructure_ready(
    scope_ratification: dict,
) -> None:
    assert scope_ratification["evaluation_infrastructure_ready"] is True
    assert scope_ratification["evaluation_infrastructure_blockers"] == []
    assert scope_ratification["runtime_authority"] is False
    assert scope_ratification["evaluation_execution_authorized"] is False


def test_start_state_verification_accepts_ratified_binding(
    scope_ratification: dict,
    complete_binding: dict,
) -> None:
    result = verify_execution_start_state_v0(
        repo_root=REPO_ROOT,
        ratification=scope_ratification,
        versioned_binding=complete_binding,
    )
    assert result.valid is True
    assert result.fail_reasons == ()


def test_bound_funding_materialization_is_complete(
    bound_staging: Path,
    complete_binding: dict,
) -> None:
    result = materialize_bound_funding_panel_dataset_v0(
        bound_staging,
        period_binding=complete_binding["period_binding"],
        expected_data_digest=complete_binding["data_digest"],
    )
    assert result.status is MaterializationTerminalStatus.DATASET_MATERIALIZATION_COMPLETE
    assert result.data_digest_match is True


def test_precheck_rejects_invalid_go_token(
    bound_staging: Path,
    scope_ratification: dict,
    complete_binding: dict,
) -> None:
    ok, reasons, _ = verify_full_evaluation_precheck_v1(
        repo_root=REPO_ROOT,
        ratification=scope_ratification,
        staging_root=bound_staging,
        versioned_binding=complete_binding,
        confirm_go="INVALID_TOKEN",
    )
    assert ok is False
    assert "GO_TOKEN_INVALID" in reasons


def test_contract_smoke_evaluation_produces_wiring_outputs(
    bound_staging: Path,
    complete_binding: dict,
) -> None:
    readiness = run_contract_smoke_evaluation_v0(
        panel_series=build_synthetic_ohlcv_panel_v0(),
        versioned_binding=complete_binding,
        staging_root=bound_staging,
    )
    assert readiness.execution_infrastructure_complete is True
    assert readiness.panel_wiring_complete is True
    assert readiness.bound_dataset_materialized is True
    assert readiness.economic_evaluation_executed is False
    assert readiness.smoke_trade_count is not None


def test_dry_run_entrypoint_stops_before_economic_execution(
    bound_staging: Path,
    scope_ratification: dict,
    complete_binding: dict,
) -> None:
    result = run_full_evaluation_entrypoint_dry_run_v1(
        repo_root=REPO_ROOT,
        ratification=scope_ratification,
        staging_root=bound_staging,
        panel_series=build_synthetic_ohlcv_panel_v0(),
        versioned_binding=complete_binding,
        confirm_go=_INFRA_GO,
    )
    assert result.dry_run_stopped_before_execution is True
    assert result.economic_evaluation_executed is False
    assert len(result.stage_wiring) == 6
    assert all(item.wired for item in result.stage_wiring)


def test_infrastructure_summary_flags_no_economic_evaluation(
    scope_ratification: dict,
    complete_binding: dict,
    bound_staging: Path,
) -> None:
    readiness = run_contract_smoke_evaluation_v0(
        panel_series=build_synthetic_ohlcv_panel_v0(),
        versioned_binding=complete_binding,
        staging_root=bound_staging,
    )
    summary = materialize_infrastructure_summary_v0(
        ratification=scope_ratification,
        readiness=readiness,
        origin_main_sha="test",
        execution_bundle_dir="/tmp/test",
    )
    assert summary["economic_evaluation_executed"] is False
    assert summary["economic_classification"] == "NONE"
    assert "net_return" not in summary
    assert summary["authority_effect"] == "NONE"


def test_ops_config_loads(complete_binding: dict) -> None:
    cfg = load_ops_evaluation_config_v0(REPO_ROOT)
    assert cfg["strategy_id"] == complete_binding["strategy_id"]
    assert (
        cfg["cross_sectional_evaluation_binding_v1"]["data_digest"]
        == complete_binding["data_digest"]
    )


def test_readiness_blocked_when_funding_panel_wiring_missing(complete_binding: dict) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        incomplete_repo = Path(tmp)
        readiness = evaluate_extreme_carry_reversion_offline_evaluation_infrastructure_readiness_v0(
            repo_root=incomplete_repo,
            versioned_binding=complete_binding,
        )
        assert readiness.evaluation_infrastructure_ready is False
        assert readiness.panel_materialization_readiness_status.value == "BLOCKED"


def test_readiness_blocked_when_cost_binding_removed(complete_binding: dict) -> None:
    broken = dict(complete_binding)
    broken["cost_execution_binding"] = {"execution_model_binding": {}}
    readiness = evaluate_extreme_carry_reversion_offline_evaluation_infrastructure_readiness_v0(
        repo_root=REPO_ROOT,
        versioned_binding=broken,
    )
    assert readiness.evaluation_infrastructure_ready is False
    assert readiness.cost_execution_model_binding_status.value == "BLOCKED"


def test_readiness_blocked_when_dataset_period_binding_removed(complete_binding: dict) -> None:
    broken = dict(complete_binding)
    broken["period_binding"] = {}
    readiness = evaluate_extreme_carry_reversion_offline_evaluation_infrastructure_readiness_v0(
        repo_root=REPO_ROOT,
        versioned_binding=broken,
    )
    assert readiness.evaluation_infrastructure_ready is False
    assert readiness.dataset_period_instrument_binding_status.value == "BLOCKED"


def test_readiness_blocked_when_evaluation_envelope_not_ratified(complete_binding: dict) -> None:
    readiness = evaluate_extreme_carry_reversion_offline_evaluation_infrastructure_readiness_v0(
        repo_root=REPO_ROOT,
        versioned_binding=complete_binding,
        ratification=None,
    )
    assert readiness.evaluation_infrastructure_ready is False
    assert readiness.evaluation_envelope_ratification_status.value == "BLOCKED"


def test_readiness_component_pass_when_wiring_complete(scope_ratification: dict) -> None:
    readiness = evaluate_extreme_carry_reversion_offline_evaluation_infrastructure_readiness_v0(
        repo_root=REPO_ROOT,
        ratification=scope_ratification,
    )
    assert readiness.orchestrator_readiness_status.value == "PASS"
    assert readiness.panel_materialization_readiness_status.value == "PASS"
    assert readiness.dataset_period_instrument_binding_status.value == "PASS"
    assert readiness.cost_execution_model_binding_status.value == "PASS"
    assert readiness.evaluation_envelope_ratification_status.value == "PASS"
    assert readiness.economic_evaluation_executed is False
    assert readiness.evaluation_execution_authorized is False
    assert readiness.runtime_authority is False
