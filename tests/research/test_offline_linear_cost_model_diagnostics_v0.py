from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
RUNNER_MODULE = REPO_ROOT / "scripts/research/offline_linear_cost_model_diagnostics_v0.py"
_SPEC = importlib.util.spec_from_file_location(
    "offline_linear_cost_model_diagnostics_v0",
    RUNNER_MODULE,
)
assert _SPEC is not None and _SPEC.loader is not None
_DIAGNOSTICS_CLI = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_DIAGNOSTICS_CLI)
discover_repo_root_from_script = _DIAGNOSTICS_CLI.discover_repo_root_from_script
resolve_repo_root = _DIAGNOSTICS_CLI.resolve_repo_root
validate_peak_trade_repo_root = _DIAGNOSTICS_CLI.validate_peak_trade_repo_root
from src.research.linear_evidence.feature_matrix import build_feature_matrix_binding
from src.research.linear_evidence.fitters import fit_ols_lstsq
from src.research.offline_linear_cost_diagnostic_row_materializer_v0 import TARGET_NAME

ARCHIVE_ROOT = Path("/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z")
LEDGER_PATH = (
    ARCHIVE_ROOT
    / "trade_ledger_equity_curve_persistence_offline_evaluation_execution_v0_20260705T083113Z"
    / "TRADE_LEDGER_V1.jsonl"
)
SNAPSHOT_PATH = (
    ARCHIVE_ROOT
    / "research/offline_linear_cost_entry_bar_reference_snapshot_materialization_v0_for_trend_following_v1_trade_ledger_binding_20260713T055132Z"
    / "entry_bar_snapshots.jsonl"
)
PARAMETER_BINDING_ID = (
    "config/ops/step31f_okx_inst_eth_usdt_perp_trend_following_v1_economic_evaluation_v1.json"
)
FORBIDDEN_IMPORT_PREFIXES = (
    "src.execution",
    "src.scheduler",
    "src.broker",
    "requests",
    "httpx",
    "urllib.request",
)


def _run_cli(
    tmp_path: Path,
    *,
    extra_args: list[str] | None = None,
    cwd: str | None = None,
) -> subprocess.CompletedProcess[str]:
    args = [
        sys.executable,
        str(RUNNER_MODULE),
        "--out",
        str(tmp_path),
    ]
    if extra_args:
        args.extend(extra_args)
    return subprocess.run(
        args,
        check=False,
        text=True,
        capture_output=True,
        cwd=cwd or str(REPO_ROOT),
    )


def _archive_inputs_available() -> bool:
    return LEDGER_PATH.is_file() and SNAPSHOT_PATH.is_file()


def test_feature_matrix_blocks_random_validation_split() -> None:
    with pytest.raises(ValueError, match="RANDOM_VALIDATION_SPLIT_BLOCKED"):
        build_feature_matrix_binding(
            [{"decision_time": "2026-01-01T00:00:00Z", "x": 1.0, "y": 2.0}],
            feature_names=("x",),
            target_name="y",
            validation_policy="RANDOM",
        )


def test_ols_evidence_is_authority_neutral() -> None:
    rows = [
        {
            "decision_time": f"2026-01-01T0{i}:00:00Z",
            "x": float(i),
            "z": float(i + 1),
            "y": float(2 * i + 1),
        }
        for i in range(8)
    ]
    x, y, binding = build_feature_matrix_binding(rows, feature_names=("x", "z"), target_name="y")
    evidence = fit_ols_lstsq(x, y, binding)

    assert evidence.solver == "numpy.linalg.lstsq"
    assert evidence.authority_effect == "NONE"
    assert evidence.runtime_effect == "NONE"
    assert evidence.cost_policy_output == "diagnostic_only"
    assert evidence.validation_policy == "TIME_ORDERED"


def test_explicit_repo_root_resolves_expected_repo() -> None:
    resolved = resolve_repo_root(REPO_ROOT)
    assert resolved == REPO_ROOT.resolve()


def test_implicit_repo_root_resolves_expected_repo() -> None:
    discovered = discover_repo_root_from_script()
    assert discovered == REPO_ROOT.resolve()
    assert resolve_repo_root(None) == REPO_ROOT.resolve()


def test_explicit_and_implicit_repo_root_identical() -> None:
    assert resolve_repo_root(REPO_ROOT) == resolve_repo_root(None)


def test_invalid_repo_root_fails_closed(tmp_path: Path) -> None:
    invalid = tmp_path / "not-a-repo"
    (invalid / "src").mkdir(parents=True)
    with pytest.raises(SystemExit, match="REPO_ROOT_INVALID_MISSING_GIT"):
        validate_peak_trade_repo_root(invalid)

    trade = {
        "trade_id": "t-1",
        "instrument_id": "inst-eth-usdt-perp",
        "entry_time": "2026-01-01T00:00:00+00:00",
        "side": "long",
        "entry_price": 100.0,
        "notional": 1000.0,
    }
    snapshot = {
        "instrument_id": "inst-eth-usdt-perp",
        "bar_timestamp": "2026-01-01T00:00:00+00:00",
        "close": 100.0,
        "spread_bps": 10.0,
        "volatility_estimate": 0.02,
        "is_finalized": True,
        "feature_timestamp": "2026-01-01T00:00:00+00:00",
    }
    ledger_path = tmp_path / "ledger.jsonl"
    snapshot_path = tmp_path / "snapshots.jsonl"
    ledger_path.write_text(json.dumps(trade, sort_keys=True) + "\n", encoding="utf-8")
    snapshot_path.write_text(json.dumps(snapshot, sort_keys=True) + "\n", encoding="utf-8")

    result = _run_cli(
        tmp_path / "out",
        extra_args=[
            "--repo-root",
            str(invalid),
            "--trade-ledger",
            str(ledger_path),
            "--entry-bar-snapshots",
            str(snapshot_path),
        ],
    )
    assert result.returncode != 0
    assert "REPO_ROOT_INVALID_MISSING_GIT" in result.stderr


def test_offline_linear_cost_model_diagnostics_cli_fail_closed_without_materialized_rows(
    tmp_path: Path,
) -> None:
    result = _run_cli(tmp_path)

    assert result.returncode == 0, result.stderr
    report = json.loads((tmp_path / "offline_linear_cost_model_diagnostics_v0.json").read_text())
    assert report["offline_only"] is True
    assert report["runtime_authority"] is False
    assert report["order_authority"] is False
    assert report["promotion_pass_authority"] is False
    assert report["backtest_cost_default_change"] is False
    assert report["n_productive_samples"] == 0
    assert report["ols_executed"] is False
    assert report["verdict"] == "OFFLINE_LINEAR_COST_MODEL_DIAGNOSTICS_V0_FAIL_CLOSED"


def test_offline_linear_cost_model_diagnostics_fixture_scaffold_cli(tmp_path: Path) -> None:
    result = _run_cli(tmp_path, extra_args=["--fixture-scaffold"])

    assert result.returncode == 0, result.stderr
    report = json.loads((tmp_path / "offline_linear_cost_model_diagnostics_v0.json").read_text())
    assert report["offline_only"] is True
    assert report["fixture_scaffold_only"] is True
    assert report["n_productive_samples"] == 0
    assert report["calibration"]["calibrated_cost_policy"] == "CONSERVATIVE_NOT_MEAN"


@pytest.mark.skipif(not _archive_inputs_available(), reason="archive evidence unavailable")
def test_direct_cli_resolves_219_samples(tmp_path: Path) -> None:
    out = tmp_path / "implicit"
    result = _run_cli(
        out,
        extra_args=[
            "--trade-ledger",
            str(LEDGER_PATH),
            "--entry-bar-snapshots",
            str(SNAPSHOT_PATH),
        ],
    )
    assert result.returncode == 0, result.stderr
    report = json.loads((out / "offline_linear_cost_model_diagnostics_v0.json").read_text())
    assert report["n_productive_samples"] == 219
    assert report["materialization_status"] == "PASS"


@pytest.mark.skipif(not _archive_inputs_available(), reason="archive evidence unavailable")
def test_direct_cli_no_longer_requires_test_harness(tmp_path: Path) -> None:
    explicit_out = tmp_path / "explicit"
    implicit_out = tmp_path / "implicit"
    common_args = [
        "--trade-ledger",
        str(LEDGER_PATH),
        "--entry-bar-snapshots",
        str(SNAPSHOT_PATH),
    ]
    explicit = _run_cli(
        explicit_out,
        extra_args=[*common_args, "--repo-root", str(REPO_ROOT)],
    )
    implicit = _run_cli(implicit_out, extra_args=common_args)
    assert explicit.returncode == 0, explicit.stderr
    assert implicit.returncode == 0, implicit.stderr
    explicit_report = json.loads(
        (explicit_out / "offline_linear_cost_model_diagnostics_v0.json").read_text()
    )
    implicit_report = json.loads(
        (implicit_out / "offline_linear_cost_model_diagnostics_v0.json").read_text()
    )
    assert explicit_report["n_productive_samples"] == 219
    assert implicit_report["n_productive_samples"] == 219
    assert explicit_report["materialization_digest"] == implicit_report["materialization_digest"]


def test_existing_explicit_repo_root_callers_compatible(tmp_path: Path) -> None:
    trade = {
        "trade_id": "t-1",
        "instrument_id": "inst-eth-usdt-perp",
        "entry_time": "2026-01-01T00:00:00+00:00",
        "side": "long",
        "entry_price": 100.5,
        "notional": 1000.0,
    }
    snapshot = {
        "instrument_id": "inst-eth-usdt-perp",
        "bar_timestamp": "2026-01-01T00:00:00+00:00",
        "close": 100.0,
        "spread_bps": 10.0,
        "volatility_estimate": 0.02,
        "is_finalized": True,
        "feature_timestamp": "2026-01-01T00:00:00+00:00",
    }
    ledger_path = tmp_path / "ledger.jsonl"
    snapshot_path = tmp_path / "snapshots.jsonl"
    ledger_path.write_text(json.dumps(trade, sort_keys=True) + "\n", encoding="utf-8")
    snapshot_path.write_text(json.dumps(snapshot, sort_keys=True) + "\n", encoding="utf-8")
    out = tmp_path / "out"
    result = _run_cli(
        out,
        extra_args=[
            "--repo-root",
            str(REPO_ROOT),
            "--trade-ledger",
            str(ledger_path),
            "--entry-bar-snapshots",
            str(snapshot_path),
        ],
    )
    assert result.returncode == 0, result.stderr
    report = json.loads((out / "offline_linear_cost_model_diagnostics_v0.json").read_text())
    assert report["n_productive_samples"] == 1


@pytest.mark.skipif(not _archive_inputs_available(), reason="archive evidence unavailable")
def test_target_binding_unchanged(tmp_path: Path) -> None:
    out = tmp_path / "out"
    result = _run_cli(
        out,
        extra_args=[
            "--trade-ledger",
            str(LEDGER_PATH),
            "--entry-bar-snapshots",
            str(SNAPSHOT_PATH),
        ],
    )
    assert result.returncode == 0, result.stderr
    report = json.loads((out / "offline_linear_cost_model_diagnostics_v0.json").read_text())
    assert report["target_name"] == TARGET_NAME
    assert report["n_productive_samples"] == 219


@pytest.mark.skipif(not _archive_inputs_available(), reason="archive evidence unavailable")
def test_entry_slippage_unique_values_remain_5_bps() -> None:
    binding = json.loads((REPO_ROOT / PARAMETER_BINDING_ID).read_text(encoding="utf-8"))
    assert binding["backtest"]["slippage_bps"] == 5.0


def test_feature_names_unchanged() -> None:
    source = RUNNER_MODULE.read_text(encoding="utf-8")
    assert '"spread_bps"' in source
    assert '"volatility_estimate"' in source
    assert '"order_notional"' in source


@pytest.mark.skipif(not _archive_inputs_available(), reason="archive evidence unavailable")
def test_dataset_binding_unchanged() -> None:
    ledger_row = json.loads(LEDGER_PATH.read_text(encoding="utf-8").splitlines()[0])
    assert ledger_row["parameter_binding_id"] == PARAMETER_BINDING_ID
    assert (
        ledger_row["input_digest"]
        == "815b33162adaa2ffd0834f129621f1942b8cb61bc19a6d6220b81b15b65578cc"
    )


@pytest.mark.skipif(not _archive_inputs_available(), reason="archive evidence unavailable")
def test_universe_binding_unchanged() -> None:
    ledger_rows = [
        json.loads(line)
        for line in LEDGER_PATH.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert all(row.get("market_type", "perp") == "perp" for row in ledger_rows)
    assert not any("btc" in str(row.get("instrument_id", "")).lower() for row in ledger_rows)


@pytest.mark.skipif(not _archive_inputs_available(), reason="archive evidence unavailable")
def test_strategy_binding_unchanged() -> None:
    ledger_row = json.loads(LEDGER_PATH.read_text(encoding="utf-8").splitlines()[0])
    assert ledger_row["candidate_id"] == "trend_following/v1"


def test_cost_policy_unchanged() -> None:
    binding = json.loads((REPO_ROOT / PARAMETER_BINDING_ID).read_text(encoding="utf-8"))
    assert binding["backtest"]["fee_bps"] == 10.0
    assert binding["backtest"]["slippage_bps"] == 5.0


def test_risk_sizing_semantics_unchanged() -> None:
    binding = json.loads((REPO_ROOT / PARAMETER_BINDING_ID).read_text(encoding="utf-8"))
    assert binding["backtest"]["initial_cash"] == 10000.0


def test_no_runtime_import() -> None:
    source = RUNNER_MODULE.read_text(encoding="utf-8")
    for token in FORBIDDEN_IMPORT_PREFIXES:
        assert token not in source


def test_no_order_adapter_import() -> None:
    source = RUNNER_MODULE.read_text(encoding="utf-8")
    for token in ("order_adapter", "src.orders", "src.trading.orders"):
        assert token not in source


def test_no_scheduler_import() -> None:
    source = RUNNER_MODULE.read_text(encoding="utf-8")
    assert "src.scheduler" not in source


def test_no_authority_effect() -> None:
    source = RUNNER_MODULE.read_text(encoding="utf-8")
    assert 'AUTHORITY_EFFECT = "NONE"' in source
    assert 'RUNTIME_EFFECT = "NONE"' in source


@pytest.mark.skipif(not _archive_inputs_available(), reason="archive evidence unavailable")
def test_deterministic_second_invocation_same_binding_and_counts(tmp_path: Path) -> None:
    out1 = tmp_path / "run1"
    out2 = tmp_path / "run2"
    args = [
        "--trade-ledger",
        str(LEDGER_PATH),
        "--entry-bar-snapshots",
        str(SNAPSHOT_PATH),
    ]
    first = _run_cli(out1, extra_args=args)
    second = _run_cli(out2, extra_args=args)
    assert first.returncode == 0, first.stderr
    assert second.returncode == 0, second.stderr
    report1 = json.loads((out1 / "offline_linear_cost_model_diagnostics_v0.json").read_text())
    report2 = json.loads((out2 / "offline_linear_cost_model_diagnostics_v0.json").read_text())
    assert report1["n_productive_samples"] == report2["n_productive_samples"] == 219
    assert report1["materialization_digest"] == report2["materialization_digest"]
