"""Contract tests for funding-rate carry execution infrastructure v0."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from src.research.cross_sectional_funding_rate_carry_v0_bound_panel_dataset_materialization_v0 import (
    MaterializationTerminalStatus,
    materialize_bound_funding_panel_dataset_v0,
)
from src.research.cross_sectional_funding_rate_carry_v0_offline_economic_evaluation_execution_v0 import (
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
from src.research.cross_sectional_funding_rate_carry_v0_offline_economic_evaluation_scope_ratification_v0 import (
    materialize_funding_carry_offline_economic_evaluation_scope_ratification_v0,
)
from src.research.cross_sectional_funding_rate_carry_v0_versioned_research_binding_v0 import (
    materialize_and_validate_versioned_research_binding_v0,
    materialize_versioned_research_binding_v0,
)
from src.research.cross_sectional_panel_staging_source_manifest_v1 import (
    SourceManifestStatus,
    materialize_panel_staging_source_manifests_v1,
)
from tests.research.fixtures.cross_sectional_funding_rate_carry_v0.fixture_builder import (
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

    ohlcv_rows: list[dict[str, object]] = []
    funding_rows: list[dict[str, object]] = []
    for series_idx, series in enumerate(panel):
        for bar_idx, bar in enumerate(series.bars):
            ohlcv_rows.append(
                {
                    "instrument_id": bar.instrument_id,
                    "timestamp_utc": bar.timestamp_utc,
                    "open": bar.open,
                    "high": bar.high,
                    "low": bar.low,
                    "close": bar.close,
                    "volume": bar.volume,
                    "is_final": bar.is_final,
                }
            )
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

    (panel_dir / "normalized_panel_bars.json").write_text(
        json.dumps(ohlcv_rows, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (panel_dir / "panel_dataset_manifest.json").write_text(
        json.dumps(
            {
                "panel_id": "pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_research_v1",
                "dataset_version": "v1",
                "bar_granularity": "PT1H",
                "instrument_ids": [s.instrument_id for s in panel],
                "native_instrument_ids": [s.native_instrument_id for s in panel],
                "manifest_digest": "0" * 64,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
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
                "dataset_extension": "with_funding_v1",
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
    return materialize_funding_carry_offline_economic_evaluation_scope_ratification_v0(
        repo_root=REPO_ROOT,
        versioned_binding=complete_binding,
    )


@pytest.fixture(name="bound_staging")
def fixture_bound_staging() -> Path:
    tmp = Path(tempfile.mkdtemp(prefix="cs_funding_exec_v0_"))
    return _write_staging_with_funding(tmp)


def test_go_token_constants() -> None:
    assert GO_TOKEN.endswith("_EXECUTION_V0")
    assert INFRASTRUCTURE_GO_TOKEN.endswith("_RECOVERY_V0")


def test_no_runtime_authority_effect_constants() -> None:
    assert AUTHORITY_EFFECT == "NONE"
    assert RUNTIME_EFFECT == "NONE"


def test_binding_materialization_complete_accepted() -> None:
    result = materialize_and_validate_versioned_research_binding_v0()
    assert result.validation_verdict.value == "ACCEPTED_COMPLETE"


def test_futures_only_and_bitcoin_exclusion(complete_binding: dict) -> None:
    constraints = complete_binding["system_constraints"]
    assert constraints["futures_only"] is True
    assert constraints["bitcoin_direction_allowed"] is False


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
        go_token="INVALID_TOKEN",
    )
    assert ok is False
    assert "GO_TOKEN_INVALID" in reasons


def test_precheck_rejects_data_digest_mismatch(
    bound_staging: Path,
    scope_ratification: dict,
    complete_binding: dict,
) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp)
        (repo / "config/ops").mkdir(parents=True, exist_ok=True)
        cfg = load_ops_evaluation_config_v0(REPO_ROOT)
        cfg["cross_sectional_evaluation_binding_v1"]["data_contract_digest"] = "f" * 64
        (
            repo / "config/ops/cross_sectional_funding_rate_carry_v0_economic_evaluation_v1.json"
        ).write_text(
            json.dumps(cfg, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        (repo / "config/research").mkdir(parents=True, exist_ok=True)
        (
            repo
            / "config/research/cross_sectional_funding_rate_carry_v0_versioned_research_binding_v0.json"
        ).write_text(
            json.dumps(complete_binding, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        ok, reasons, _ = verify_full_evaluation_precheck_v1(
            repo_root=repo,
            ratification=scope_ratification,
            staging_root=bound_staging,
            versioned_binding=complete_binding,
            go_token=_INFRA_GO,
        )
        assert ok is False
        assert "DATA_DIGEST_MISMATCH" in reasons


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
        go_token=_INFRA_GO,
    )
    assert result.dry_run_stopped_before_execution is True
    assert result.economic_evaluation_executed is False
    assert len(result.stage_wiring) == 6
    assert all(item.wired for item in result.stage_wiring)


def test_entrypoint_to_dict_carries_no_eval_flag(
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
        go_token=_INFRA_GO,
    )
    payload = entrypoint_result_to_dict(result)
    assert payload["economic_evaluation_executed"] is False


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
        origin_main_sha="deadbeef" * 5,
        execution_bundle_dir="/tmp/cs_funding_exec",
    )
    assert summary["economic_evaluation_executed"] is False
    assert summary["economic_classification"] == "NONE"


def test_precheck_fails_without_manifests(
    scope_ratification: dict,
    complete_binding: dict,
) -> None:
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


def test_ops_config_loads(complete_binding: dict) -> None:
    cfg = load_ops_evaluation_config_v0(REPO_ROOT)
    assert cfg["strategy_id"] == "cross_sectional_funding_rate_carry"
    assert cfg["binding_digest"] == complete_binding["binding_digest"]


def test_execution_path_has_no_runtime_imports() -> None:
    module_name = "src.research.cross_sectional_funding_rate_carry_v0_offline_economic_evaluation_execution_v0"
    module = __import__(module_name, fromlist=["__doc__"])
    source = Path(module.__file__).read_text(encoding="utf-8")
    for token in ("src.execution", "src.governance.live", "src.scheduler"):
        assert token not in source
