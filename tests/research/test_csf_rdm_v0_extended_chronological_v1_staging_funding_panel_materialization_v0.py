"""Contract tests for CSF/RDM v0 extended_chronological_v1 staging/funding materialization."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from src.research.csf_rdm_v0_dataset_funding_binding_materialization_preflight_v0 import (
    PreflightTerminalStatus,
    run_dataset_funding_binding_materialization_preflight_v0,
)
from src.research.csf_rdm_v0_extended_chronological_v1_staging_funding_panel_materialization_v0 import (
    CANONICAL_DATASET_OWNER,
    CANONICAL_FUNDING_OWNER,
    CANONICAL_PREFLIGHT_OWNER,
    DEFAULT_STAGING_ROOT,
    CONFIRM_GO,
    MaterializationScopeVerdict,
    StagingReadinessStatus,
    assess_staging_readiness_v0,
    load_materialization_binding_config_v0,
    run_materialization_scope_v0,
)
from src.research.cross_sectional_funding_rate_delta_momentum_v0_offline_economic_evaluation_execution_v0 import (
    resolve_actual_repo_shas_v0,
)
from src.research.cross_sectional_funding_rate_delta_momentum_v0_versioned_research_binding_v0 import (
    materialize_versioned_research_binding_v0,
)
from src.research.cross_sectional_panel_staging_source_manifest_v1 import (
    SourceManifestStatus,
    materialize_panel_staging_source_manifests_v1,
)
from tests.research.fixtures.cross_sectional_funding_rate_delta_momentum_v0.fixture_builder import (
    build_synthetic_ohlcv_panel_v0,
)

_REPO_ROOT = Path(__file__).resolve().parents[2]


def _write_staging_with_funding(root: Path) -> Path:
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
    manifest = materialize_panel_staging_source_manifests_v1(root)
    assert manifest.status is SourceManifestStatus.VERIFIED
    return root


@pytest.fixture(name="complete_binding")
def fixture_complete_binding() -> dict:
    return materialize_versioned_research_binding_v0()


@pytest.fixture(name="bound_staging")
def fixture_bound_staging() -> Path:
    tmp = Path(tempfile.mkdtemp(prefix="csf_rdm_materialization_v0_"))
    return _write_staging_with_funding(tmp)


def test_confirm_go_constant() -> None:
    assert CONFIRM_GO == (
        "GO_BOUNDED_CSF_RDM_V0_EXTENDED_CHRONOLOGICAL_V1_STAGING_AND_BOUND_FUNDING_PANEL_MATERIALIZATION_V0"
    )


def test_binding_config_loads_canonical_owners() -> None:
    config = load_materialization_binding_config_v0(_REPO_ROOT)
    assert config["dataset_owner"] == CANONICAL_DATASET_OWNER
    assert config["funding_owner"] == CANONICAL_FUNDING_OWNER
    assert config["preflight_owner"] == CANONICAL_PREFLIGHT_OWNER
    assert config["staging_root"] == str(DEFAULT_STAGING_ROOT)


def test_missing_canonical_staging_fails_closed(complete_binding: dict) -> None:
    assessment = assess_staging_readiness_v0(
        DEFAULT_STAGING_ROOT, versioned_binding=complete_binding
    )
    assert assessment.status is StagingReadinessStatus.FAIL_CLOSED_MISSING_PRECONDITION
    assert not assessment.staging_root_exists
    assert "MISSING_CANONICAL_EXTENDED_CHRONOLOGICAL_V1_STAGING_ROOT" in assessment.reason_codes


def test_missing_staging_preflight_still_fails_closed(complete_binding: dict) -> None:
    _, actual_origin_main = resolve_actual_repo_shas_v0(_REPO_ROOT)
    result = run_materialization_scope_v0(
        repo_root=_REPO_ROOT,
        staging_root=DEFAULT_STAGING_ROOT,
        durable_evidence_root=Path(tempfile.mkdtemp(prefix="csf_rdm_durable_")),
        binding_origin_main_sha=actual_origin_main,
        attempt_fetch=False,
        versioned_binding=complete_binding,
    )
    assert (
        result.verdict
        is MaterializationScopeVerdict.FAIL_CLOSED_STAGING_OR_FUNDING_NOT_MATERIALIZED
    )
    assert result.ready_for_next_pre_evaluation_gate is False
    assert result.economic_evaluation_executed is False
    assert result.economic_evaluation_blocked is True


def test_complete_bound_staging_reaches_preflight_gate_not_evaluation(
    bound_staging: Path,
    complete_binding: dict,
) -> None:
    _, actual_origin_main = resolve_actual_repo_shas_v0(_REPO_ROOT)
    result = run_materialization_scope_v0(
        repo_root=_REPO_ROOT,
        staging_root=bound_staging,
        durable_evidence_root=Path(tempfile.mkdtemp(prefix="csf_rdm_durable_")),
        binding_origin_main_sha=actual_origin_main,
        attempt_fetch=False,
        versioned_binding=complete_binding,
    )
    assert result.verdict is (
        MaterializationScopeVerdict.PREFLIGHT_GATE_PASS_READY_FOR_NEXT_PRE_EVALUATION_GATE
    )
    assert result.ready_for_next_pre_evaluation_gate is True
    assert result.economic_evaluation_executed is False
    assert result.economic_evaluation_blocked is True
    assert result.preflight_status == (
        PreflightTerminalStatus.PREFLIGHT_GATE_PASS_READY_FOR_NEXT_PRE_EVALUATION_GATE.value
    )

    preflight = run_dataset_funding_binding_materialization_preflight_v0(
        repo_root=_REPO_ROOT,
        staging_root=bound_staging,
        expected_origin_main_sha=actual_origin_main,
        binding_origin_main_sha=actual_origin_main,
        versioned_binding=complete_binding,
    )
    assert preflight.economic_evaluation_executed is False
