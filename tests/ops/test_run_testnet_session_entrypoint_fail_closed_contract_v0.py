"""Static + offline entrypoint fail-closed contract for scripts/run_testnet_session.py (v0)."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict
from unittest.mock import MagicMock, patch

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
RUN_TESTNET_SESSION = REPO_ROOT / "scripts" / "run_testnet_session.py"
BOUNDED_ADAPTER = REPO_ROOT / "scripts" / "ops" / "run_testnet_bounded_observation_adapter_v0.py"
LEGACY_SMOKE_TESTS = REPO_ROOT / "tests" / "test_run_testnet_session.py"

PACKAGE_MARKER = "RUN_TESTNET_SESSION_ENTRYPOINT_FAIL_CLOSED_CONTRACT_V0=true"
_EXIT_FAIL_CLOSED = 2


@pytest.fixture
def testnet_config_dict() -> Dict[str, Any]:
    return {
        "environment": {
            "mode": "testnet",
            "enable_live_trading": False,
            "testnet_dry_run": True,
        },
        "testnet_session": {
            "enabled": True,
            "symbol": "BTC/EUR",
            "timeframe": "1m",
            "poll_interval_seconds": 60.0,
            "warmup_candles": 200,
            "start_balance": 10000.0,
            "position_fraction": 0.1,
            "fee_rate": 0.0026,
            "slippage_bps": 5.0,
        },
        "exchange": {
            "kraken_testnet": {
                "enabled": True,
                "base_url": "https://api.kraken.com",
                "api_key_env_var": "KRAKEN_TESTNET_API_KEY",
                "api_secret_env_var": "KRAKEN_TESTNET_API_SECRET",
                "validate_only": True,
                "timeout_seconds": 30.0,
                "max_retries": 3,
                "rate_limit_ms": 1000,
            },
        },
        "live_risk": {
            "enabled": True,
            "max_order_notional": 1000.0,
            "max_total_exposure_notional": 5000.0,
            "block_on_violation": True,
        },
        "shadow_paper_logging": {
            "enabled": False,
            "base_dir": "test_runs",
            "flush_interval_steps": 50,
            "format": "parquet",
        },
        "strategy": {
            "ma_crossover": {
                "fast_period": 10,
                "slow_period": 30,
                "stop_pct": 0.02,
            },
        },
    }


def _source() -> str:
    return RUN_TESTNET_SESSION.read_text(encoding="utf-8")


def test_package_marker_present() -> None:
    text = Path(__file__).read_text(encoding="utf-8")
    assert PACKAGE_MARKER in text


def test_source_declares_not_authorized_normal_testnet_run() -> None:
    assert "RUN_TESTNET_SESSION_ALLOWED_NOW=false" in _source()


def test_source_has_fail_closed_enforcement_helper() -> None:
    text = _source()
    assert "_enforce_fail_closed_entrypoint" in text
    assert "EXIT_FAIL_CLOSED_ENTRYPOINT" in text


def test_source_requires_explicit_flag_for_run_forever() -> None:
    text = _source()
    assert "--allow-unbounded-session" in text
    assert "allow_unbounded_session" in text
    # run_forever only on explicit unsafe branch
    assert "elif args.allow_unbounded_session:" in text
    assert "session.run_forever()" in text


def test_source_does_not_warn_only_on_missing_credentials() -> None:
    text = _source()
    assert "WARNUNG: KRAKEN_TESTNET_API_KEY" not in text


def test_bounded_adapter_remains_canonical_repo_native_lane() -> None:
    adapter = BOUNDED_ADAPTER.read_text(encoding="utf-8")
    assert "run_testnet_session.py" in adapter
    assert "FORBIDDEN_COMMAND_SUBSTRINGS" in adapter


def test_legacy_smoke_tests_still_reference_dry_run() -> None:
    assert "test_main_dry_run" in LEGACY_SMOKE_TESTS.read_text(encoding="utf-8")


def test_pe2_hard_gate_uses_line_based_gap2a1_forbidden_tokens_v0() -> None:
    """Align with test_gap2a1_primary_evidence_enforcement_contract_v0 (prose may mention =true)."""
    hard_gate = (
        REPO_ROOT / "tests/ops/test_run_primary_evidence_retention_hard_gate_v0.py"
    ).read_text(encoding="utf-8")
    assert "gap2a1_lines" in hard_gate
    assert '"READY_FOR_OPERATOR_ARMING=true" not in gap2a1_lines' in hard_gate


@patch("scripts.run_testnet_session.create_kraken_testnet_client_from_config")
@patch("scripts.run_testnet_session.load_config")
def test_main_execute_rejects_missing_duration_and_credentials(
    mock_load_config: MagicMock,
    mock_create_client: MagicMock,
    testnet_config_dict: Dict[str, Any],
) -> None:
    from src.core.peak_config import PeakConfig
    from scripts.run_testnet_session import main

    mock_load_config.return_value = PeakConfig(raw=testnet_config_dict)
    mock_create_client.return_value = MagicMock(has_credentials=True)

    env = {k: v for k, v in os.environ.items() if not k.startswith("KRAKEN_TESTNET_API")}
    with patch.dict(os.environ, env, clear=True):
        with patch("sys.argv", ["run_testnet_session.py", "--config", "config/config.toml"]):
            with patch("pathlib.Path.exists", return_value=True):
                rc = main()

    assert rc == _EXIT_FAIL_CLOSED


@patch("scripts.run_testnet_session.create_kraken_testnet_client_from_config")
@patch("scripts.run_testnet_session.load_config")
def test_main_execute_rejects_missing_credentials_with_duration(
    mock_load_config: MagicMock,
    mock_create_client: MagicMock,
    testnet_config_dict: Dict[str, Any],
) -> None:
    from src.core.peak_config import PeakConfig
    from scripts.run_testnet_session import main

    mock_load_config.return_value = PeakConfig(raw=testnet_config_dict)
    mock_create_client.return_value = MagicMock(has_credentials=True)

    env = {k: v for k, v in os.environ.items() if not k.startswith("KRAKEN_TESTNET_API")}
    with patch.dict(os.environ, env, clear=True):
        with patch(
            "sys.argv",
            ["run_testnet_session.py", "--config", "config/config.toml", "--duration", "5"],
        ):
            with patch("pathlib.Path.exists", return_value=True):
                rc = main()

    assert rc == _EXIT_FAIL_CLOSED


@patch("scripts.run_testnet_session.create_kraken_testnet_client_from_config")
@patch("scripts.run_testnet_session.load_config")
def test_main_dry_run_skips_duration_and_credentials(
    mock_load_config: MagicMock,
    mock_create_client: MagicMock,
    testnet_config_dict: Dict[str, Any],
) -> None:
    from src.core.peak_config import PeakConfig
    from scripts.run_testnet_session import main

    mock_load_config.return_value = PeakConfig(raw=testnet_config_dict)
    mock_create_client.return_value = MagicMock(has_credentials=False)

    env = {k: v for k, v in os.environ.items() if not k.startswith("KRAKEN_TESTNET_API")}
    with patch.dict(os.environ, env, clear=True):
        with patch("sys.argv", ["run_testnet_session.py", "--dry-run"]):
            with patch("pathlib.Path.exists", return_value=True):
                rc = main()

    assert rc == 0


@patch("scripts.run_testnet_session.create_kraken_testnet_client_from_config")
@patch("scripts.run_testnet_session.load_config")
def test_main_rejects_non_positive_duration(
    mock_load_config: MagicMock,
    mock_create_client: MagicMock,
    testnet_config_dict: Dict[str, Any],
) -> None:
    from src.core.peak_config import PeakConfig
    from scripts.run_testnet_session import main

    mock_load_config.return_value = PeakConfig(raw=testnet_config_dict)
    mock_create_client.return_value = MagicMock(has_credentials=True)

    with patch.dict(
        os.environ,
        {
            "KRAKEN_TESTNET_API_KEY": "present",
            "KRAKEN_TESTNET_API_SECRET": "present",
        },
        clear=False,
    ):
        with patch(
            "sys.argv",
            ["run_testnet_session.py", "--config", "config/config.toml", "--duration", "0"],
        ):
            with patch("pathlib.Path.exists", return_value=True):
                rc = main()

    assert rc == _EXIT_FAIL_CLOSED
