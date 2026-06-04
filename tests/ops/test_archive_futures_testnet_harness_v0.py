"""Static + offline tests for archive_futures_testnet_harness_v0 (no network, no execute)."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pytest

from scripts.ops import archive_futures_testnet_harness_v0 as harness
from src.ops.bounded_futures_testnet_contract_v0 import (
    DEFAULT_INSTRUMENT,
    FUTURES_SESSION_AUTHORIZED_NOW,
    REJECTED_FUTURES_INSTRUMENT_PLACEHOLDERS,
    default_bounded_futures_zero_order_reachability_v0_spec,
    evaluate_bounded_futures_testnet_evidence,
)
from src.ops.bounded_futures_testnet_runtime_harness_contract_v0 import (
    ARCHIVE_HARNESS_SCRIPT_EXECUTE_AUTHORIZED_NOW,
    ARCHIVE_HARNESS_SCRIPT_PRESENT,
    ARCHIVE_HARNESS_SCRIPT_REL_PATH,
    RUNTIME_HARNESS_EXECUTE_ALLOWED,
    RUNTIME_HARNESS_NETWORK_ALLOWED,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
HARNESS_SCRIPT = REPO_ROOT / "scripts" / "ops" / "archive_futures_testnet_harness_v0.py"
RUN_TESTNET_SESSION = REPO_ROOT / "scripts" / "run_testnet_session.py"

TEST_PACKAGE_MARKER = "ARCHIVE_FUTURES_TESTNET_HARNESS_GUARD_V0=true"


class _FakeFetcher:
    def __init__(self) -> None:
        self.urls: list[str] = []

    def fetch(self, url: str, *, timeout_seconds: float) -> tuple[int, bytes]:
        self.urls.append(url)
        return 200, b"{}"


def _default_namespace(**overrides: object) -> argparse.Namespace:
    base = {
        "mode": harness.DEFAULT_MODE,
        "instrument": harness.DEFAULT_FUTURES_SYMBOL,
        "rest_base_url": harness.DEFAULT_REST_BASE_URL,
        "exchange": harness.DEFAULT_EXCHANGE,
        "market_type": harness.DEFAULT_MARKET_TYPE_LABEL,
        "order_cap": harness.DEFAULT_ORDER_CAP,
        "validate_only_order_cap": harness.DEFAULT_VALIDATE_ONLY_ORDER_CAP,
        "duration_cap_seconds": harness.DEFAULT_DURATION_CAP_SECONDS,
        "scheduler_enabled": False,
        "background_enabled": False,
        "allow_unbounded": False,
        "use_spot_testnet_session": False,
        "delegated_entrypoint": "",
    }
    base.update(overrides)
    return argparse.Namespace(**base)


def test_package_marker_and_entrypoint_file_present() -> None:
    assert TEST_PACKAGE_MARKER
    assert harness.PACKAGE_MARKER in HARNESS_SCRIPT.read_text(encoding="utf-8")
    assert HARNESS_SCRIPT.is_file()
    assert ARCHIVE_HARNESS_SCRIPT_PRESENT is True
    assert ARCHIVE_HARNESS_SCRIPT_REL_PATH == "scripts/ops/archive_futures_testnet_harness_v0.py"


def test_authority_flags_remain_blocked() -> None:
    assert FUTURES_SESSION_AUTHORIZED_NOW is False
    assert RUNTIME_HARNESS_EXECUTE_ALLOWED is False
    assert RUNTIME_HARNESS_NETWORK_ALLOWED is False
    assert ARCHIVE_HARNESS_SCRIPT_EXECUTE_AUTHORIZED_NOW is False


def test_defaults_pf_xbtusd_and_demo_futures_rest_base() -> None:
    assert harness.DEFAULT_FUTURES_SYMBOL == "PF_XBTUSD"
    assert harness.DEFAULT_INSTRUMENT == "PF_XBTUSD"
    assert harness.DEFAULT_REST_BASE_URL == (
        "https://demo-futures.kraken.com/derivatives/api/v3"
    )
    assert _validate_harness_defaults_pass()


def _validate_harness_defaults_pass() -> bool:
    args = _default_namespace()
    return harness.validate_harness_namespace(args) == []


def test_btcusdt_rejected_placeholder() -> None:
    args = _default_namespace(instrument="BTCUSDT")
    reasons = harness.validate_harness_namespace(args)
    assert any("rejected placeholder" in r for r in reasons)


def test_order_cap_above_zero_rejected() -> None:
    args = _default_namespace(order_cap=1)
    reasons = harness.validate_harness_namespace(args)
    assert any("order_cap" in r for r in reasons)


def test_duration_above_300_rejected() -> None:
    args = _default_namespace(duration_cap_seconds=301)
    reasons = harness.validate_harness_namespace(args)
    assert any("duration_cap_seconds" in r for r in reasons)


def test_spot_lane_entrypoint_forbidden() -> None:
    args = _default_namespace(use_spot_testnet_session=True)
    with pytest.raises(SystemExit):
        harness._reject_spot_lane_flags(args)
    args2 = _default_namespace(delegated_entrypoint="scripts/run_testnet_session.py")
    with pytest.raises(SystemExit):
        harness._reject_spot_lane_flags(args2)
    assert "run_testnet_session" in RUN_TESTNET_SESSION.read_text(encoding="utf-8")


def test_execute_network_without_confirm_token_fails(tmp_path: Path) -> None:
    argv = [
        "--archive-root",
        str(tmp_path),
        "--run-id",
        "testrun",
        "--execute-network",
        "--confirm-futures-zero-order-reachability",
        "WRONG",
    ]
    with pytest.raises(SystemExit) as exc:
        harness.main(argv)
    assert exc.value.code == harness.USAGE_EXIT


def test_execute_network_without_fetcher_fails_even_with_confirm(tmp_path: Path) -> None:
    argv = [
        "--archive-root",
        str(tmp_path),
        "--run-id",
        "testrun2",
        "--execute-network",
        "--confirm-futures-zero-order-reachability",
        harness.CONFIRM_TOKEN_ZERO_ORDER_REACHABILITY,
    ]
    with pytest.raises(SystemExit) as exc:
        harness.main(argv)
    assert exc.value.code == harness.USAGE_EXIT


def test_plan_only_dry_run_writes_durable_evidence(tmp_path: Path) -> None:
    rc = harness.main(
        ["--archive-root", str(tmp_path), "--run-id", "planonly"],
    )
    assert rc == 0
    runtime_dirs = list((tmp_path / "runtime").iterdir())
    assert len(runtime_dirs) == 1
    bundle = runtime_dirs[0]
    assert (bundle / "MANIFEST.sha256").is_file()
    evidence = json.loads((bundle / "FUTURES_EVIDENCE.json").read_text(encoding="utf-8"))
    assert evidence["order_attempt_count"] == 0
    assert evidence["real_orders_created_count"] == 0
    assert evidence["order_attempted"] is False
    assert evidence["fills"] == 0
    assert evidence["bounded_futures_testnet_pass"] is True
    assert "run_testnet_session" not in json.dumps(evidence)


def test_fake_fetcher_network_path_no_sendorder(tmp_path: Path) -> None:
    fetcher = _FakeFetcher()
    rc = harness.main(
        [
            "--archive-root",
            str(tmp_path),
            "--run-id",
            "netfake",
            "--execute-network",
            "--confirm-futures-zero-order-reachability",
            harness.CONFIRM_TOKEN_ZERO_ORDER_REACHABILITY,
        ],
        fetcher=fetcher,
    )
    assert rc == 0
    assert fetcher.urls
    for url in fetcher.urls:
        assert "demo-futures.kraken.com" in url
        assert "sendorder" not in url
        assert "api.kraken.com" not in url


def test_pe8_zero_order_spec_accepts_harness_evidence() -> None:
    timing = harness.HarnessTiming(
        monotonic_start=0.0,
        monotonic_end=1.0,
        wall_clock_start_utc="2026-06-04T00:00:00Z",
        wall_clock_end_utc="2026-06-04T00:00:01Z",
    )
    evidence = harness.build_zero_order_evidence_payload(
        timing=timing,
        endpoints_called=list(harness.ZERO_ORDER_PUBLIC_ENDPOINTS),
        request_count=2,
        network_host="https://demo-futures.kraken.com",
        run_id="offline",
        pe8_pass=False,
    )
    spec = default_bounded_futures_zero_order_reachability_v0_spec()
    result = evaluate_bounded_futures_testnet_evidence(evidence, spec=spec)
    assert result["bounded_futures_testnet_pass"] is True


def test_rejected_placeholder_set_unchanged() -> None:
    assert "BTCUSDT" in REJECTED_FUTURES_INSTRUMENT_PLACEHOLDERS
    assert DEFAULT_INSTRUMENT == "PF_XBTUSD"
