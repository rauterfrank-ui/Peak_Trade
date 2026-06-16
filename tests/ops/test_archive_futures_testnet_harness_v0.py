"""Static + offline tests for archive_futures_testnet_harness_v0 (no network, no execute)."""

from __future__ import annotations

import argparse
import base64
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.ops import archive_futures_testnet_harness_v0 as harness
from src.ops.bounded_futures_private_readonly_contract_v0 import (
    CONFIRM_TOKEN_PRIVATE_READONLY_REACHABILITY,
    PRIVATE_READONLY_MODE,
)
from src.ops.bounded_futures_testnet_contract_v0 import (
    DEFAULT_INSTRUMENT,
    FUTURES_SESSION_AUTHORIZED_NOW,
    REJECTED_FUTURES_INSTRUMENT_PLACEHOLDERS,
    default_bounded_futures_private_readonly_reachability_v0_spec,
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


def _durable_test_archive_root(tmp_path: Path) -> Path:
    """Repo-local archive root for harness tests (CI tmp_path is under /tmp)."""
    root = REPO_ROOT / "tests" / ".pytest_archive_roots" / tmp_path.name
    if root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True, exist_ok=True)
    return root


class _FakeFetcher:
    def __init__(self, *, body: bytes | None = None) -> None:
        self.urls: list[str] = []
        self._body = body if body is not None else b'{"tickers":[{"symbol":"PF_XBTUSD"}]}'

    def fetch(self, url: str, *, timeout_seconds: float) -> tuple[int, bytes]:
        self.urls.append(url)
        return 200, self._body


class _PrivateTimeoutFetcher:
    def fetch(self, http_request, *, timeout_seconds: float) -> tuple[int, bytes]:
        raise TimeoutError("timed out")


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
    assert harness.DEFAULT_REST_BASE_URL == ("https://demo-futures.kraken.com/derivatives/api/v3")
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
    archive = _durable_test_archive_root(tmp_path)
    argv = [
        "--archive-root",
        str(archive),
        "--run-id",
        "testrun",
        "--execute-network",
        "--confirm-futures-zero-order-reachability",
        "WRONG",
    ]
    with pytest.raises(SystemExit) as exc:
        harness.main(argv)
    assert exc.value.code == harness.USAGE_EXIT


def test_safe_public_urllib_fetcher_marker_present() -> None:
    assert harness.SAFE_PUBLIC_URLLIB_FETCHER_PRESENT is True
    text = HARNESS_SCRIPT.read_text(encoding="utf-8")
    assert "SafePublicUrllibRestFetcher" in text
    assert "SAFE_PUBLIC_URLLIB_FETCHER_PRESENT" in text


def test_execute_network_default_fetcher_without_live_network(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    archive = _durable_test_archive_root(tmp_path)
    fake = _FakeFetcher()

    def _factory(rest_base_url: str) -> _FakeFetcher:
        assert rest_base_url == harness.DEFAULT_REST_BASE_URL
        return fake

    monkeypatch.setattr(harness, "default_safe_public_rest_fetcher", _factory)
    rc = harness.main(
        [
            "--archive-root",
            str(archive),
            "--run-id",
            "defaultfetcher",
            "--execute-network",
            "--confirm-futures-zero-order-reachability",
            harness.CONFIRM_TOKEN_ZERO_ORDER_REACHABILITY,
        ],
    )
    assert rc == 0
    assert fake.urls
    bundle = list((archive / "runtime").iterdir())[0]
    evidence = json.loads((bundle / "FUTURES_EVIDENCE.json").read_text(encoding="utf-8"))
    assert evidence["request_count"] == 2
    assert evidence["network_reachability_proven"] is True
    assert evidence["pf_xbtusd_symbol_visibility"] == "visible"


def test_plan_only_dry_run_writes_durable_evidence(tmp_path: Path) -> None:
    archive = _durable_test_archive_root(tmp_path)
    rc = harness.main(
        ["--archive-root", str(archive), "--run-id", "planonly"],
    )
    assert rc == 0
    runtime_dirs = list((archive / "runtime").iterdir())
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
    archive = _durable_test_archive_root(tmp_path)
    fetcher = _FakeFetcher()
    rc = harness.main(
        [
            "--archive-root",
            str(archive),
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
    bundle = list((archive / "runtime").iterdir())[0]
    evidence = json.loads((bundle / "FUTURES_EVIDENCE.json").read_text(encoding="utf-8"))
    assert evidence["request_count"] == 2
    assert "/derivatives/api/v3/tickers" in evidence["endpoints_called"]
    assert evidence["order_attempted"] is False
    assert evidence["fills"] == 0
    assert evidence["pf_xbtusd_symbol_visibility"] == "visible"
    evidence_dump = json.dumps(evidence)
    assert '{"tickers"' not in evidence_dump
    for call in evidence["network_calls"]:
        assert "response_sha256" in call
        assert call["response_size_bytes"] >= 0
        assert set(call.keys()) == {
            "endpoint",
            "http_status",
            "http_status_class",
            "response_size_bytes",
            "response_sha256",
        }


def test_assert_network_url_rejects_forbidden_host() -> None:
    with pytest.raises(SystemExit):
        harness._assert_network_url_allowed(
            "https://api.kraken.com/derivatives/api/v3/tickers",
            harness.DEFAULT_REST_BASE_URL,
        )


def test_assert_network_url_rejects_non_allowlisted_path() -> None:
    with pytest.raises(SystemExit):
        harness._assert_network_url_allowed(
            "https://demo-futures.kraken.com/derivatives/api/v3/sendorder",
            harness.DEFAULT_REST_BASE_URL,
        )


def test_tickers_path_increments_request_count_and_endpoints() -> None:
    fetcher = _FakeFetcher(body=b'{"tickers":[{"symbol":"PF_XBTUSD"}]}')
    result = harness.run_zero_order_public_reachability(
        rest_base_url=harness.DEFAULT_REST_BASE_URL,
        duration_cap_seconds=60,
        fetcher=fetcher,
    )
    assert result.request_count == 2
    assert "/derivatives/api/v3/tickers" in result.endpoints_called
    assert result.pf_xbtusd_symbol_visibility == "visible"
    assert result.network_reachability_proven is True


def test_pf_xbtusd_not_visible_classification() -> None:
    fetcher = _FakeFetcher(body=b'{"tickers":[{"symbol":"PF_ETHUSD"}]}')
    result = harness.run_zero_order_public_reachability(
        rest_base_url=harness.DEFAULT_REST_BASE_URL,
        duration_cap_seconds=60,
        fetcher=fetcher,
    )
    assert result.pf_xbtusd_symbol_visibility == "not_visible"


def test_pf_xbtusd_unparseable_classification() -> None:
    fetcher = _FakeFetcher(body=b"not-json")
    result = harness.run_zero_order_public_reachability(
        rest_base_url=harness.DEFAULT_REST_BASE_URL,
        duration_cap_seconds=60,
        fetcher=fetcher,
    )
    assert result.pf_xbtusd_symbol_visibility == "response_unparseable"


def test_plan_only_network_reachability_not_proven(tmp_path: Path) -> None:
    archive = _durable_test_archive_root(tmp_path)
    harness.main(["--archive-root", str(archive), "--run-id", "planonly2"])
    evidence = json.loads(
        list((archive / "runtime").iterdir())[0]
        .joinpath("FUTURES_EVIDENCE.json")
        .read_text(encoding="utf-8")
    )
    assert evidence["request_count"] == 0
    assert evidence["network_reachability_proven"] is False
    assert evidence["pf_xbtusd_symbol_visibility"] == "not_checked"


def test_pe8_zero_order_spec_accepts_harness_evidence() -> None:
    timing = harness.HarnessTiming(
        monotonic_start=0.0,
        monotonic_end=1.0,
        wall_clock_start_utc="2026-06-04T00:00:00Z",
        wall_clock_end_utc="2026-06-04T00:00:01Z",
    )
    evidence = harness.build_zero_order_evidence_payload(
        timing=timing,
        endpoints_called=list(harness.ZERO_ORDER_PUBLIC_ENDPOINT_ORDER),
        request_count=2,
        network_host="https://demo-futures.kraken.com",
        run_id="offline",
        pe8_pass=False,
        network_reachability_proven=True,
        pf_xbtusd_symbol_visibility="visible",
    )
    spec = default_bounded_futures_zero_order_reachability_v0_spec()
    result = evaluate_bounded_futures_testnet_evidence(evidence, spec=spec)
    assert result["bounded_futures_testnet_pass"] is True


def test_rejected_placeholder_set_unchanged() -> None:
    assert "BTCUSDT" in REJECTED_FUTURES_INSTRUMENT_PLACEHOLDERS
    assert DEFAULT_INSTRUMENT == "PF_XBTUSD"


def test_private_readonly_mode_plan_only_writes_evidence(tmp_path: Path) -> None:
    archive = _durable_test_archive_root(tmp_path)
    rc = harness.main(
        [
            "--archive-root",
            str(archive),
            "--run-id",
            "privro",
            "--mode",
            PRIVATE_READONLY_MODE,
        ],
    )
    assert rc == 0
    bundle = list((archive / "runtime").iterdir())[0]
    assert bundle.name.startswith("bounded_futures_private_readonly_")
    evidence = json.loads((bundle / "FUTURES_EVIDENCE.json").read_text(encoding="utf-8"))
    assert evidence["harness_mode"] == PRIVATE_READONLY_MODE
    assert evidence["request_count"] == 0
    assert evidence["private_readonly_reachability_proven"] is False
    assert evidence["futures_private_api_authorized"] is False
    assert evidence["credential_values_logged"] is False
    spec = default_bounded_futures_private_readonly_reachability_v0_spec()
    assert evaluate_bounded_futures_testnet_evidence(evidence, spec=spec)[
        "bounded_futures_testnet_pass"
    ]


def test_private_readonly_timeout_writes_durable_failure_evidence(tmp_path: Path) -> None:
    archive = _durable_test_archive_root(tmp_path)
    secret = base64.b64encode(b"test-secret-bytes-32chars-long!!").decode()
    rc = harness.main(
        [
            "--archive-root",
            str(archive),
            "--run-id",
            "privrotimeout",
            "--mode",
            PRIVATE_READONLY_MODE,
            "--execute-network",
            "--confirm-futures-private-readonly-reachability",
            CONFIRM_TOKEN_PRIVATE_READONLY_REACHABILITY,
        ],
        private_fetcher=_PrivateTimeoutFetcher(),
        environ={
            "KRAKEN_FUTURES_DEMO_API_KEY": "k",
            "KRAKEN_FUTURES_DEMO_API_SECRET": secret,
        },
    )
    assert rc == harness.USAGE_EXIT
    bundle = list((archive / "runtime").iterdir())[0]
    assert bundle.name.startswith("bounded_futures_private_readonly_privrotimeout_")
    evidence = json.loads((bundle / "FUTURES_EVIDENCE.json").read_text(encoding="utf-8"))
    assert evidence["fetch_failure"] is True
    assert evidence["failure_class"] == "network_timeout_or_fetch_exception"
    assert evidence["failed_endpoint"] == "/derivatives/api/v3/accounts"
    assert evidence["request_count_attempted"] == 1
    assert evidence["completed_request_count"] == 0
    assert evidence["private_readonly_reachability_proven"] is False
    assert evidence["partial_policy_accepted"] is True
    assert evidence["credential_values_logged"] is False
    dumped = json.dumps(evidence)
    assert "test-secret" not in dumped
    assert "Authent" not in dumped or evidence["network_calls"][0].get("auth_header_names") == [
        "APIKey",
        "Authent",
        "Nonce",
    ]
    assert "response_body" not in dumped
    assert (bundle / "MANIFEST.sha256").exists()


def test_private_readonly_execute_network_requires_confirm_token(tmp_path: Path) -> None:
    archive = _durable_test_archive_root(tmp_path)
    argv = [
        "--archive-root",
        str(archive),
        "--run-id",
        "privroexec",
        "--mode",
        PRIVATE_READONLY_MODE,
        "--execute-network",
    ]
    rc = harness.main(
        argv,
        environ={
            "KRAKEN_FUTURES_DEMO_API_KEY": "k",
            "KRAKEN_FUTURES_DEMO_API_SECRET": "c2VjcmV0LXNlY3JldC1zZWNyZXQtc2VjcmV0LXNlY3JldCE=",
        },
    )
    assert rc == harness.USAGE_EXIT


def test_cli_entrypoint_forwards_process_environ(tmp_path: Path) -> None:
    """CLI must pass os.environ so authority/credential namespace validation applies."""
    archive = _durable_test_archive_root(tmp_path)
    env = os.environ.copy()
    env["FUTURES_EXECUTE_AUTHORIZED"] = "true"
    result = subprocess.run(
        [
            sys.executable,
            str(HARNESS_SCRIPT),
            "--archive-root",
            str(archive),
            "--run-id",
            "clienv",
            "--mode",
            PRIVATE_READONLY_MODE,
        ],
        env=env,
        capture_output=True,
        text=True,
        check=False,
        cwd=str(REPO_ROOT),
    )
    assert result.returncode == harness.USAGE_EXIT
    assert "FUTURES_EXECUTE_AUTHORIZED" in result.stderr


def test_cli_execute_network_does_not_log_credential_values(tmp_path: Path) -> None:
    archive = _durable_test_archive_root(tmp_path)
    secret_marker = "peak-trade-test-secret-marker-v0-not-a-real-secret"
    env = os.environ.copy()
    env["KRAKEN_FUTURES_DEMO_API_KEY"] = "test-key-marker"
    env["KRAKEN_FUTURES_DEMO_API_SECRET"] = secret_marker
    result = subprocess.run(
        [
            sys.executable,
            str(HARNESS_SCRIPT),
            "--archive-root",
            str(archive),
            "--run-id",
            "clinosec",
            "--mode",
            PRIVATE_READONLY_MODE,
            "--execute-network",
        ],
        env=env,
        capture_output=True,
        text=True,
        check=False,
        cwd=str(REPO_ROOT),
    )
    assert result.returncode == harness.USAGE_EXIT
    combined = result.stdout + result.stderr
    assert secret_marker not in combined
    assert "test-key-marker" not in combined


def test_credentials_in_environ_alone_do_not_authorize_execute(tmp_path: Path) -> None:
    archive = _durable_test_archive_root(tmp_path)
    rc = harness.main(
        [
            "--archive-root",
            str(archive),
            "--run-id",
            "credonly",
            "--mode",
            PRIVATE_READONLY_MODE,
        ],
        environ={
            "KRAKEN_FUTURES_DEMO_API_KEY": "k",
            "KRAKEN_FUTURES_DEMO_API_SECRET": "c2VjcmV0LXNlY3JldC1zZWNyZXQtc2VjcmV0LXNlY3JldCE=",
        },
    )
    assert rc == 0
    bundle = list((archive / "runtime").iterdir())[0]
    evidence = json.loads((bundle / "FUTURES_EVIDENCE.json").read_text(encoding="utf-8"))
    assert evidence["request_count"] == 0
    assert evidence["private_readonly_reachability_proven"] is False
    assert evidence["futures_private_api_authorized"] is False
