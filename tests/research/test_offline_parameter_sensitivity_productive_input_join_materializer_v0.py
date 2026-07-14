"""Contract tests for offline parameter sensitivity productive input join materializer v0."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from research.linear_evidence.import_boundary import scan_file_import_boundary
from research.linear_evidence.parameter_sensitivity_productive_contract_v0 import (
    AUTHORITY_EFFECT,
    ProductiveBindingRejectionReason,
)
from research.linear_evidence.signal_matrix_productive_contract_v0 import (
    DECISION_TIME_KEY,
    FEATURE_TIME_KEY,
    INSTRUMENT_ID_KEY,
)
from src.research.offline_final_research_fleet_signal_matrix_productive_input_join_materializer_v0 import (
    materialize_offline_final_research_fleet_signal_matrix_v0,
    serialize_signal_matrix_rows_v0,
)
from src.research.offline_parameter_sensitivity_productive_input_join_materializer_v0 import (
    RUNTIME_EFFECT,
    MaterializationStatus,
    materialize_offline_parameter_sensitivity_productive_inputs_v0,
    materializer_to_contract_roundtrip_pass_v0,
    serialize_materialized_productive_inputs_v0,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
MATERIALIZER_MODULE = (
    REPO_ROOT
    / "src/research/offline_parameter_sensitivity_productive_input_join_materializer_v0.py"
)
CONTRACT_MODULE = (
    REPO_ROOT / "src/research/linear_evidence/parameter_sensitivity_productive_contract_v0.py"
)
RUNNER_MODULE = (
    REPO_ROOT
    / "scripts/research/offline_parameter_sensitivity_productive_input_join_materializer_v0.py"
)
SURFACE_RUNNER_MODULE = REPO_ROOT / "scripts/research/offline_parameter_sensitivity_surface_v0.py"
ARCHIVE_ROOT = Path("/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z")
STAGING_ROOT = (
    ARCHIVE_ROOT / "datasets/admissible_futures/"
    "pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_research_v1/"
    "extended_chronological_v1"
)
FORBIDDEN_IMPORT_PREFIXES = (
    "src.execution",
    "src.scheduler",
    "src.broker",
    "requests",
    "httpx",
    "urllib.request",
)


def _signal_matrix_row(
    *,
    instrument_id: str = "okx:linear_perpetual:ETH:USDT:USDT:perp",
    decision_time: str = "2024-05-31T10:00:00Z",
    feature_time: str = "2024-05-31T09:00:00Z",
) -> dict[str, object]:
    return {
        INSTRUMENT_ID_KEY: instrument_id,
        DECISION_TIME_KEY: decision_time,
        FEATURE_TIME_KEY: feature_time,
        "bollinger_bands": 1.0,
        "momentum_1h": 0.0,
        "trend_following": -1.0,
    }


def _materialize_productive_signal_matrix(
    tmp_path: Path,
) -> tuple[tuple[dict[str, object], ...], Path]:
    if not STAGING_ROOT.is_dir():
        pytest.skip("archive staging root unavailable")
    result = materialize_offline_final_research_fleet_signal_matrix_v0(
        repo_root=REPO_ROOT,
        staging_root=STAGING_ROOT,
    )
    signal_matrix_path = tmp_path / "signal_matrix.jsonl"
    signal_matrix_path.write_text(serialize_signal_matrix_rows_v0(result.rows), encoding="utf-8")
    return result.rows, signal_matrix_path


def test_productive_materialization_accepts_fleet_binding(tmp_path: Path) -> None:
    rows, _ = _materialize_productive_signal_matrix(tmp_path)
    result = materialize_offline_parameter_sensitivity_productive_inputs_v0(
        signal_matrix_rows=rows,
        repo_root=REPO_ROOT,
    )
    assert result.status == MaterializationStatus.PASS
    assert result.records
    assert result.grid_digest
    assert result.join_result.grid.grid_id == "okx_eth_perp_research_cost_grid_v1"


def test_missing_signal_matrix_fail_closed() -> None:
    from src.research.offline_final_research_fleet_signal_matrix_productive_input_join_materializer_v0 import (
        load_ratified_binding_completion_v0,
    )

    binding = load_ratified_binding_completion_v0(REPO_ROOT)
    result = materialize_offline_parameter_sensitivity_productive_inputs_v0(
        signal_matrix_rows=(),
        repo_root=REPO_ROOT,
        binding_completion=binding,
    )
    assert result.status == MaterializationStatus.INSUFFICIENT_DATA


def test_stale_binding_digest_rejected(tmp_path: Path) -> None:
    rows = tuple(
        _signal_matrix_row(decision_time=f"2024-05-31T{hour:02d}:00:00Z") for hour in range(10, 18)
    )
    with pytest.raises(ValueError, match="BINDING_DIGEST_MISMATCH"):
        materialize_offline_parameter_sensitivity_productive_inputs_v0(
            signal_matrix_rows=rows,
            repo_root=REPO_ROOT,
            source_binding_digest="stale-binding-digest",
        )


def test_stale_signal_matrix_digest_rejected() -> None:
    rows = (_signal_matrix_row(),)
    with pytest.raises(ValueError, match="SIGNAL_MATRIX_DIGEST_MISMATCH"):
        materialize_offline_parameter_sensitivity_productive_inputs_v0(
            signal_matrix_rows=rows,
            repo_root=REPO_ROOT,
            source_signal_matrix_digest="stale-signal-matrix-digest",
        )


def test_fixture_and_productive_modes_mutually_exclusive(tmp_path: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(SURFACE_RUNNER_MODULE),
            "--out",
            str(tmp_path / "mixed"),
            "--fixture",
            "--signal-matrix",
            str(tmp_path / "missing.jsonl"),
        ],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    assert result.returncode != 0
    assert "MIXED_MODE_BLOCKED" in result.stderr


def test_productive_runner_does_not_fallback_to_fixture(tmp_path: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(SURFACE_RUNNER_MODULE),
            "--out",
            str(tmp_path / "productive"),
            "--signal-matrix",
            str(tmp_path / "missing.jsonl"),
        ],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    assert result.returncode != 0
    assert "UNSUPPORTED_SIGNAL_MATRIX_FORMAT" in result.stderr or result.returncode == 1


def test_fixture_runner_still_works(tmp_path: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(SURFACE_RUNNER_MODULE),
            "--out",
            str(tmp_path / "fixture"),
            "--fixture",
        ],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    assert result.returncode == 0, result.stderr
    report = json.loads(
        (tmp_path / "fixture" / "parameter_sensitivity_surface_evidence_v1.json").read_text()
    )
    assert report["INPUT_MODE"] == "FIXTURE_SCAFFOLD"
    assert report["FIXTURE_SCAFFOLD_USED"] is True


def test_materializer_roundtrip_pass(tmp_path: Path) -> None:
    rows, _ = _materialize_productive_signal_matrix(tmp_path)
    result = materialize_offline_parameter_sensitivity_productive_inputs_v0(
        signal_matrix_rows=rows,
        repo_root=REPO_ROOT,
    )
    assert materializer_to_contract_roundtrip_pass_v0(result) is True


def test_deterministic_materialization(tmp_path: Path) -> None:
    rows, _ = _materialize_productive_signal_matrix(tmp_path)
    first = materialize_offline_parameter_sensitivity_productive_inputs_v0(
        signal_matrix_rows=rows,
        repo_root=REPO_ROOT,
    )
    second = materialize_offline_parameter_sensitivity_productive_inputs_v0(
        signal_matrix_rows=rows,
        repo_root=REPO_ROOT,
    )
    assert serialize_materialized_productive_inputs_v0(
        first.records
    ) == serialize_materialized_productive_inputs_v0(second.records)
    assert first.materialization_digest == second.materialization_digest
    assert first.productive_input_digest == second.productive_input_digest
    assert first.grid_digest == second.grid_digest


def test_grid_specs_only_fee_and_slippage(tmp_path: Path) -> None:
    rows, _ = _materialize_productive_signal_matrix(tmp_path)
    result = materialize_offline_parameter_sensitivity_productive_inputs_v0(
        signal_matrix_rows=rows,
        repo_root=REPO_ROOT,
    )
    assert [spec.parameter_name for spec in result.join_result.grid_specs] == [
        "fee_bps",
        "slippage_bps",
    ]


def test_materializer_cli_smoke(tmp_path: Path) -> None:
    rows, signal_matrix_path = _materialize_productive_signal_matrix(tmp_path)
    assert rows
    result = subprocess.run(
        [
            sys.executable,
            str(RUNNER_MODULE),
            "--out",
            str(tmp_path / "cli"),
            "--signal-matrix",
            str(signal_matrix_path),
            "--repo-root",
            str(REPO_ROOT),
        ],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    assert result.returncode == 0, result.stderr
    report = json.loads((tmp_path / "cli" / "materialization_report.json").read_text())
    assert report["status"] == "PASS"
    assert report["grid"]["grid_id"] == "okx_eth_perp_research_cost_grid_v1"


def test_materializer_module_has_no_forbidden_imports() -> None:
    violations = scan_file_import_boundary(MATERIALIZER_MODULE, repo_root=REPO_ROOT)
    assert violations == []


def test_contract_module_has_no_forbidden_imports() -> None:
    violations = scan_file_import_boundary(CONTRACT_MODULE, repo_root=REPO_ROOT)
    assert violations == []


def test_authority_and_runtime_effect_none() -> None:
    assert AUTHORITY_EFFECT == "NONE"
    assert RUNTIME_EFFECT == "NONE"
