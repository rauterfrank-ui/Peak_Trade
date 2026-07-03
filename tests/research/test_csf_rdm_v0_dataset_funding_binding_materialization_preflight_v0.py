"""Contract tests for CSF/RDM v0 dataset/funding binding materialization preflight."""

from __future__ import annotations

import json
import tempfile
from copy import deepcopy
from pathlib import Path

import pytest

from src.research.csf_rdm_v0_dataset_funding_binding_materialization_preflight_v0 import (
    FAIL_CLOSED_EXPECTED_ORIGIN_MAIN_SHA_BINDING_MISSING,
    FAIL_CLOSED_ORIGIN_MAIN_SHA_MISMATCH,
    GO_TOKEN,
    PreflightTerminalStatus,
    REASON_BINDING_ORIGIN_MAIN_SHA_MISMATCH,
    REASON_BOUND_DATA_UNAVAILABLE,
    REASON_FUNDING_BINDING_INCOMPLETE,
    REASON_FUNDING_DATA_UNAVAILABLE_NOT_MATERIALIZED,
    run_dataset_funding_binding_materialization_preflight_v0,
    verify_funding_model_binding_explicit_v0,
)
from src.research.cross_sectional_funding_rate_delta_momentum_v0_offline_economic_evaluation_execution_v0 import (
    resolve_actual_repo_shas_v0,
    verify_origin_main_sha_guard_v0,
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
_STALE_SHA = "525cd82535cd7c65f4cdbca282094e4fc174b0fe"
_MISSING_STAGING_ROOT = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "datasets/admissible_futures/"
    "pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_research_v1/extended_chronological_v1"
)


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
    tmp = Path(tempfile.mkdtemp(prefix="csf_rdm_preflight_v0_"))
    return _write_staging_with_funding(tmp)


def test_go_token_constant() -> None:
    assert GO_TOKEN == (
        "GO_BOUNDED_CSF_RDM_V0_DATASET_FUNDING_BINDING_MATERIALIZATION_PREFLIGHT_V0"
    )


def test_evaluation_remains_blocked_before_dataset_funding_binding(
    complete_binding: dict,
) -> None:
    _, actual_origin_main = resolve_actual_repo_shas_v0(_REPO_ROOT)
    result = run_dataset_funding_binding_materialization_preflight_v0(
        repo_root=_REPO_ROOT,
        staging_root=_MISSING_STAGING_ROOT,
        expected_origin_main_sha=actual_origin_main,
        binding_origin_main_sha=actual_origin_main,
        versioned_binding=complete_binding,
    )
    assert result.economic_evaluation_executed is False
    assert result.economic_evaluation_blocked is True
    assert result.ready_for_next_pre_evaluation_gate is False


def test_missing_funding_binding_fails_closed() -> None:
    binding = materialize_versioned_research_binding_v0()
    broken = deepcopy(binding)
    broken["cost_execution_binding"]["funding_model_binding"] = {"bind": False}
    ok, reasons, status = verify_funding_model_binding_explicit_v0(
        broken["cost_execution_binding"]["funding_model_binding"]
    )
    assert ok is False
    assert any(REASON_FUNDING_BINDING_INCOMPLETE in item for item in reasons)
    assert status == "NOT_BOUND"


def test_wrong_origin_main_sha_binding_fails_closed(complete_binding: dict) -> None:
    result = run_dataset_funding_binding_materialization_preflight_v0(
        repo_root=_REPO_ROOT,
        staging_root=_MISSING_STAGING_ROOT,
        expected_origin_main_sha=_STALE_SHA,
        binding_origin_main_sha=_STALE_SHA,
        versioned_binding=complete_binding,
    )
    assert result.status is PreflightTerminalStatus.FAIL_CLOSED_SHA_GUARD
    assert FAIL_CLOSED_ORIGIN_MAIN_SHA_MISMATCH in result.reason_codes


def test_stale_binding_origin_main_sha_fails_closed(complete_binding: dict) -> None:
    _, actual_origin_main = resolve_actual_repo_shas_v0(_REPO_ROOT)
    result = run_dataset_funding_binding_materialization_preflight_v0(
        repo_root=_REPO_ROOT,
        staging_root=_MISSING_STAGING_ROOT,
        expected_origin_main_sha=actual_origin_main,
        binding_origin_main_sha=_STALE_SHA,
        versioned_binding=complete_binding,
    )
    assert result.status is PreflightTerminalStatus.FAIL_CLOSED_BINDING_ORIGIN_MAIN_SHA
    assert REASON_BINDING_ORIGIN_MAIN_SHA_MISMATCH in result.reason_codes


def test_missing_origin_main_sha_binding_fails_closed() -> None:
    guard = verify_origin_main_sha_guard_v0(
        repo_root=_REPO_ROOT,
        expected_origin_main_sha=None,
        env={},
    )
    assert guard.passed is False
    assert FAIL_CLOSED_EXPECTED_ORIGIN_MAIN_SHA_BINDING_MISSING in guard.fail_reasons


def test_matching_sha_valid_bindings_reach_next_gate_not_evaluation(
    bound_staging: Path,
    complete_binding: dict,
) -> None:
    _, actual_origin_main = resolve_actual_repo_shas_v0(_REPO_ROOT)
    result = run_dataset_funding_binding_materialization_preflight_v0(
        repo_root=_REPO_ROOT,
        staging_root=bound_staging,
        expected_origin_main_sha=actual_origin_main,
        binding_origin_main_sha=actual_origin_main,
        versioned_binding=complete_binding,
    )
    assert result.status is (
        PreflightTerminalStatus.PREFLIGHT_GATE_PASS_READY_FOR_NEXT_PRE_EVALUATION_GATE
    )
    assert result.ready_for_next_pre_evaluation_gate is True
    assert result.economic_evaluation_executed is False
    assert result.economic_evaluation_blocked is True
    assert result.dataset_materialization is not None
    assert result.dataset_materialization.funding_manifest_path


def test_missing_staging_fails_closed_with_funding_unavailable_reason(
    complete_binding: dict,
) -> None:
    _, actual_origin_main = resolve_actual_repo_shas_v0(_REPO_ROOT)
    result = run_dataset_funding_binding_materialization_preflight_v0(
        repo_root=_REPO_ROOT,
        staging_root=_MISSING_STAGING_ROOT,
        expected_origin_main_sha=actual_origin_main,
        binding_origin_main_sha=actual_origin_main,
        versioned_binding=complete_binding,
    )
    assert result.status is PreflightTerminalStatus.FAIL_CLOSED_BOUND_DATA_UNAVAILABLE
    assert REASON_BOUND_DATA_UNAVAILABLE in result.reason_codes
    assert REASON_FUNDING_DATA_UNAVAILABLE_NOT_MATERIALIZED in result.reason_codes
