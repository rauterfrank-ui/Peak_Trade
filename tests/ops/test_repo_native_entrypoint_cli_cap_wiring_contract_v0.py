"""Static + offline repo-native entrypoint CLI bounded cap wiring contract (v0).

Docs/tests-only Class-4 scoped exception. No runtime, network, credentials, or Testnet start.
Follow-up: repo_native_entrypoint_cli_cap_wiring_follow_up_pr_planning_v0
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.ops.bounded_testnet_order_cap_contract_v0 import (
    CLI_WIRING_COMPLETE_MARKER,
    DEFAULT_SESSION_CLASS,
    REQUIRED_BOUNDED_ORDER_CAP_CLI_FLAGS,
    add_bounded_order_cap_cli_arguments,
    bounded_cap_spec_from_namespace,
    build_entrypoint_bounded_cap_config_evidence,
    default_bounded_normal_v0_spec,
    validate_bounded_cap_cli_namespace,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
RUN_TESTNET_SESSION = REPO_ROOT / "scripts" / "run_testnet_session.py"
BOUNDED_ORDER_CAP_CONTRACT_TEST = (
    REPO_ROOT / "tests" / "ops" / "test_repo_native_bounded_order_cap_contract_v0.py"
)

PACKAGE_MARKER = "REPO_NATIVE_ENTRYPOINT_CLI_CAP_WIRING_CONTRACT_V0=true"
_CLASS4_SCOPED_EXCEPTION_MARKER = (
    "REPO_NATIVE_ENTRYPOINT_CLI_CAP_WIRING_GUARD_CLASS4_SCOPED_EXCEPTION_V0=true"
)
_EXIT_FAIL_CLOSED = 2


def test_package_marker_present() -> None:
    text = Path(__file__).read_text(encoding="utf-8")
    assert PACKAGE_MARKER in text
    assert _CLASS4_SCOPED_EXCEPTION_MARKER in text


def test_bounded_order_cap_contract_test_crosslink_present() -> None:
    assert BOUNDED_ORDER_CAP_CONTRACT_TEST.is_file()


def test_entrypoint_wires_contract_cli_helper() -> None:
    source = RUN_TESTNET_SESSION.read_text(encoding="utf-8")
    assert "add_bounded_order_cap_cli_arguments(parser)" in source
    assert "_enforce_bounded_order_cap_cli" in source
    assert "_emit_bounded_order_cap_config" in source
    assert CLI_WIRING_COMPLETE_MARKER in source


def test_all_required_cli_flags_registered_by_contract_helper() -> None:
    import argparse

    parser = argparse.ArgumentParser()
    add_bounded_order_cap_cli_arguments(parser)
    option_strings = {a.option_strings[0] for a in parser._actions if a.option_strings}
    for flag in REQUIRED_BOUNDED_ORDER_CAP_CLI_FLAGS:
        assert flag in option_strings


def test_validate_bounded_cap_cli_rejects_non_positive_caps() -> None:
    import argparse

    parser = argparse.ArgumentParser()
    add_bounded_order_cap_cli_arguments(parser)
    args = parser.parse_args(["--max-real-orders", "0"])
    assert validate_bounded_cap_cli_namespace(args)


@patch("scripts.run_testnet_session.build_testnet_session")
@patch("scripts.run_testnet_session.create_kraken_testnet_client_from_config")
@patch("scripts.run_testnet_session.load_config")
def test_main_dry_run_emits_bounded_cap_config_evidence(
    mock_load_config: MagicMock,
    mock_create_client: MagicMock,
    mock_build_session: MagicMock,
) -> None:
    from src.core.peak_config import PeakConfig
    from scripts.run_testnet_session import main

    testnet_config_dict = {
        "environment": {"mode": "testnet", "enable_live_trading": False, "testnet_dry_run": True},
        "testnet_session": {"enabled": True, "symbol": "BTC/EUR", "timeframe": "1m"},
        "exchange": {
            "kraken_testnet": {
                "enabled": True,
                "base_url": "https://api.kraken.com",
                "api_key_env_var": "KRAKEN_TESTNET_API_KEY",
                "api_secret_env_var": "KRAKEN_TESTNET_API_SECRET",
                "validate_only": True,
            }
        },
        "live_risk": {"enabled": True},
        "shadow_paper_logging": {"enabled": False},
        "strategy": {"ma_crossover": {"fast_period": 10, "slow_period": 30}},
    }
    mock_load_config.return_value = PeakConfig(raw=testnet_config_dict)
    mock_create_client.return_value = MagicMock(has_credentials=False)
    mock_build_session.return_value = MagicMock()

    env = {k: v for k, v in os.environ.items() if not k.startswith("KRAKEN_TESTNET_API")}
    with patch.dict(os.environ, env, clear=True):
        with patch(
            "sys.argv",
            [
                "run_testnet_session.py",
                "--dry-run",
                "--duration",
                "5",
                "--session-class",
                DEFAULT_SESSION_CLASS,
            ],
        ):
            with patch("pathlib.Path.exists", return_value=True):
                with patch("scripts.run_testnet_session.setup_logging") as mock_log_setup:
                    logger = MagicMock()
                    mock_log_setup.return_value = logger
                    rc = main()

    assert rc == 0
    spec = default_bounded_normal_v0_spec()
    expected = build_entrypoint_bounded_cap_config_evidence(spec, planned_duration_seconds=300)
    emitted = False
    for call in logger.info.call_args_list:
        if call.args and str(call.args[0]).startswith("Bounded order-cap config evidence:"):
            payload = json.loads(str(call.args[1]))
            assert payload["session_class"] == expected["session_class"]
            assert payload["planned_duration_seconds"] == 300
            assert payload["bounded_order_cap_config_emitted"] is True
            emitted = True
    assert emitted


@patch("scripts.run_testnet_session.load_config")
def test_main_rejects_invalid_bounded_cap_before_config_load(
    mock_load_config: MagicMock,
) -> None:
    from scripts.run_testnet_session import main

    with patch(
        "sys.argv",
        ["run_testnet_session.py", "--max-real-orders", "0"],
    ):
        with patch("scripts.run_testnet_session.setup_logging") as mock_log_setup:
            logger = MagicMock()
            mock_log_setup.return_value = logger
            rc = main()

    assert rc == _EXIT_FAIL_CLOSED
    mock_load_config.assert_not_called()


def test_bounded_cap_spec_from_namespace_matches_defaults() -> None:
    import argparse

    parser = argparse.ArgumentParser()
    add_bounded_order_cap_cli_arguments(parser)
    args = parser.parse_args([])
    spec = bounded_cap_spec_from_namespace(args)
    assert spec == default_bounded_normal_v0_spec()
