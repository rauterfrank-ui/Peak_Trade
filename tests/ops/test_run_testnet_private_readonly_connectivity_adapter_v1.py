"""Tests for Path-C Testnet private-readonly connectivity adapter v1 (fake fetcher only)."""

from __future__ import annotations

import base64
import importlib.util
import io
import json
import shutil
import sys
from contextlib import redirect_stdout
from pathlib import Path

import pytest

from src.exchange.operative_venue_boundary_v1 import NoncanonicalVenueRejectedError
from src.ops.bounded_futures_private_readonly_contract_v0 import (
    FUTURES_PRIVATE_READONLY_GET_ENDPOINTS,
    PrivateReadonlyHttpRequest,
)

ROOT = Path(__file__).resolve().parent.parent.parent
ADAPTER_SCRIPT = (
    ROOT / "scripts" / "ops" / "run_testnet_private_readonly_connectivity_adapter_v1.py"
)
REVIEW_SCRIPT = (
    ROOT / "scripts" / "ops" / "review_testnet_private_readonly_connectivity_evidence_v1.py"
)
HARNESS_SCRIPT = ROOT / "scripts/ops/archive_futures_testnet_harness_v0.py"
APPROVAL_FIXTURE = (
    ROOT
    / "tests"
    / "fixtures"
    / "ops"
    / "testnet_path_c_private_readonly_connectivity_approval_sample.md"
)
ARCHIVE_ROOT = Path("/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z")

_FAKE_SECRET_B64 = base64.b64encode(b"test-secret-bytes-32chars-long!!").decode()
_FAKE_CRED_ENV = {
    "FOREIGN_VENUE_API_KEY": "demo-key-not-real",
    "FOREIGN_VENUE_API_SECRET": _FAKE_SECRET_B64,
}


class _FakePrivateFetcher:
    def __init__(self, *, body: bytes | None = None) -> None:
        self.requests: list[PrivateReadonlyHttpRequest] = []
        self._body = body if body is not None else b'{"accounts":[]}'

    def fetch(
        self,
        http_request: PrivateReadonlyHttpRequest,
        *,
        timeout_seconds: float,
    ) -> tuple[int, bytes]:
        self.requests.append(http_request)
        assert http_request.method == "GET"
        assert "sendorder" not in http_request.url.lower()
        assert "cancelorder" not in http_request.url.lower()
        return 200, self._body


def _load_module(script: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, script)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def _load_adapter():
    return _load_module(ADAPTER_SCRIPT, "run_testnet_private_readonly_connectivity_adapter_v1")


def _load_review():
    return _load_module(REVIEW_SCRIPT, "review_testnet_private_readonly_connectivity_evidence_v1")


def _staging(tmp_path: Path) -> Path:
    return Path("/tmp") / f"peak_trade_path_c_staging_test_{tmp_path.name}"


def _durable_archive(tmp_path: Path) -> Path:
    path = ROOT / "tests" / ".pytest_archive_roots" / tmp_path.name
    path.mkdir(parents=True, exist_ok=True)
    return path


def _base_argv(staging: Path, archive: Path | None = None) -> list[str]:
    return [
        "--staging-root",
        str(staging),
        "--archive-root",
        str(archive or ARCHIVE_ROOT),
        "--repo-root",
        str(ROOT),
        "--run-id",
        "testnet_path_c_private_readonly_connectivity_test_run",
        "--duration-seconds",
        "900",
        "--heartbeat-interval-seconds",
        "5",
    ]


def _mock_credential_checker(_repo: Path, _env: dict) -> tuple[bool, str]:
    return True, ""


@pytest.fixture(autouse=True)
def _cleanup_paths():
    yield
    archive_roots = ROOT / "tests" / ".pytest_archive_roots"
    if archive_roots.is_dir():
        shutil.rmtree(archive_roots, ignore_errors=True)
    for path in Path("/tmp").glob("peak_trade_path_c_staging_test_*"):
        shutil.rmtree(path, ignore_errors=True)


def _plan_dict(staging: Path, archive: Path | None = None) -> dict:
    mod = _load_adapter()
    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = mod.main(_base_argv(staging, archive) + ["--json"])
    assert rc == 0, buf.getvalue()
    return json.loads(buf.getvalue())


def test_adapter_and_review_scripts_exist() -> None:
    assert ADAPTER_SCRIPT.is_file()
    assert REVIEW_SCRIPT.is_file()
    assert HARNESS_SCRIPT.is_file()
    assert APPROVAL_FIXTURE.is_file()


def test_plan_only_default_no_harness_call(tmp_path: Path) -> None:
    mod = _load_adapter()
    staging = _staging(tmp_path)
    called = {"count": 0}

    def _runner(_ctx, _plan, _fetcher, _execute_network) -> tuple[int, dict | None]:
        called["count"] += 1
        return 0, {}

    rc = mod.main(_base_argv(staging), harness_runner=_runner)
    assert rc == 0
    assert called["count"] == 0


def test_plan_uses_private_readonly_harness_mode(tmp_path: Path) -> None:
    plan = _plan_dict(_staging(tmp_path))
    assert plan["harness_mode"] == "private_readonly_reachability_only"
    assert plan["session_class"] == "path_c_private_readonly_connectivity_v0"
    assert plan["max_orders"] == 0
    assert plan["max_cancel"] == 0
    assert plan["harness_duration_seconds"] == 300


def test_plan_forbids_staging_script_in_commands(tmp_path: Path) -> None:
    plan = _plan_dict(_staging(tmp_path))
    joined = json.dumps(plan["commands"]).lower()
    assert "run_testnet_bounded_evidence_staging_v0.sh" not in joined
    assert "run_testnet_session.py" not in joined


def test_plan_does_not_reference_removed_legacy_credential_script(tmp_path: Path) -> None:
    plan = _plan_dict(_staging(tmp_path))
    dumped = json.dumps(plan)
    assert "check_kraken_futures_demo_credentials_presence_readonly_v0.py" not in dumped
    assert plan.get("credential_presence_script") in ("", None)


def test_execute_without_approval_record_fails(tmp_path: Path) -> None:
    mod = _load_adapter()
    rc = mod.main(
        _base_argv(_staging(tmp_path)) + ["--execute", "--no-strict-repo-clean"],
        credential_presence_checker=_mock_credential_checker,
        repo_clean_checker=lambda _root: (True, ""),
        private_fetcher=_FakePrivateFetcher(),
        environ=_FAKE_CRED_ENV,
    )
    assert rc != 0


def test_execute_with_invalid_approval_token_fails(tmp_path: Path) -> None:
    mod = _load_adapter()
    bad = tmp_path / "bad.md"
    bad.write_text(
        "APPROVE_EXECUTE_TESTNET_PATH_C_PRIVATE_READONLY_CONNECTIVITY_NOW=false\n",
        encoding="utf-8",
    )
    rc = mod.main(
        _base_argv(_staging(tmp_path))
        + [
            "--execute",
            "--approval-record",
            str(bad),
            "--no-strict-repo-clean",
        ],
        credential_presence_checker=_mock_credential_checker,
        repo_clean_checker=lambda _root: (True, ""),
        private_fetcher=_FakePrivateFetcher(),
        environ=_FAKE_CRED_ENV,
    )
    assert rc != 0


def test_execute_blocks_live_network_without_allow_flag(tmp_path: Path) -> None:
    mod = _load_adapter()
    rc = mod.main(
        _base_argv(_staging(tmp_path))
        + [
            "--execute",
            "--approval-record",
            str(APPROVAL_FIXTURE),
            "--no-strict-repo-clean",
        ],
        credential_presence_checker=_mock_credential_checker,
        repo_clean_checker=lambda _root: (True, ""),
        environ=_FAKE_CRED_ENV,
    )
    assert rc != 0


def test_execute_blocks_forbidden_env(tmp_path: Path) -> None:
    mod = _load_adapter()
    env = dict(_FAKE_CRED_ENV)
    env["PT_LIVE_ENABLED"] = "true"
    rc = mod.main(
        _base_argv(_staging(tmp_path))
        + [
            "--execute",
            "--approval-record",
            str(APPROVAL_FIXTURE),
            "--no-strict-repo-clean",
        ],
        credential_presence_checker=_mock_credential_checker,
        repo_clean_checker=lambda _root: (True, ""),
        private_fetcher=_FakePrivateFetcher(),
        environ=env,
    )
    assert rc != 0


def test_fake_fetcher_execute_rejected_as_noncanonical_venue(tmp_path: Path) -> None:
    fetcher = _FakePrivateFetcher()
    mod = _load_adapter()
    staging = _staging(tmp_path)
    archive = _durable_archive(tmp_path)
    with pytest.raises(NoncanonicalVenueRejectedError):
        mod.main(
            _base_argv(staging, archive)
            + [
                "--execute",
                "--approval-record",
                str(APPROVAL_FIXTURE),
                "--no-strict-repo-clean",
            ],
            private_fetcher=fetcher,
            credential_presence_checker=_mock_credential_checker,
            repo_clean_checker=lambda _root: (True, ""),
            environ=_FAKE_CRED_ENV,
        )
    assert fetcher.requests == []


def test_execute_with_fake_fetcher_rejected_as_noncanonical_venue(tmp_path: Path) -> None:
    mod = _load_adapter()
    staging = _staging(tmp_path)
    archive = _durable_archive(tmp_path)
    with pytest.raises(NoncanonicalVenueRejectedError):
        mod.main(
            _base_argv(staging, archive)
            + [
                "--execute",
                "--approval-record",
                str(APPROVAL_FIXTURE),
                "--no-strict-repo-clean",
            ],
            private_fetcher=_FakePrivateFetcher(),
            credential_presence_checker=_mock_credential_checker,
            repo_clean_checker=lambda _root: (True, ""),
            environ=_FAKE_CRED_ENV,
        )
    assert not (archive / "runs" / "testnet").exists() or not list(
        (archive / "runs" / "testnet").glob("*")
    )


def test_missing_credentials_fail_before_harness(tmp_path: Path) -> None:
    mod = _load_adapter()
    called = {"count": 0}

    def _runner(_ctx, _plan, _fetcher, _execute_network) -> tuple[int, dict | None]:
        called["count"] += 1
        return 0, {}

    rc = mod.main(
        _base_argv(_staging(tmp_path))
        + [
            "--execute",
            "--approval-record",
            str(APPROVAL_FIXTURE),
            "--no-strict-repo-clean",
        ],
        harness_runner=_runner,
        private_fetcher=_FakePrivateFetcher(),
        credential_presence_checker=lambda _r, _e: (False, "missing keys"),
        repo_clean_checker=lambda _root: (True, ""),
        environ={},
    )
    assert rc != 0
    assert called["count"] == 0


def test_execute_rejection_does_not_leak_secret_marker(tmp_path: Path) -> None:
    mod = _load_adapter()
    staging = _staging(tmp_path)
    archive = _durable_archive(tmp_path)
    secret_env = dict(_FAKE_CRED_ENV)
    secret_env["FOREIGN_VENUE_API_SECRET"] = base64.b64encode(b"super-secret-value").decode()
    with pytest.raises(NoncanonicalVenueRejectedError) as exc:
        mod.main(
            _base_argv(staging, archive)
            + [
                "--execute",
                "--approval-record",
                str(APPROVAL_FIXTURE),
                "--no-strict-repo-clean",
            ],
            private_fetcher=_FakePrivateFetcher(),
            credential_presence_checker=_mock_credential_checker,
            repo_clean_checker=lambda _root: (True, ""),
            environ=secret_env,
        )
    assert "super-secret-value" not in str(exc.value)
