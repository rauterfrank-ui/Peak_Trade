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
    "KRAKEN_FUTURES_DEMO_API_KEY": "demo-key-not-real",
    "KRAKEN_FUTURES_DEMO_API_SECRET": _FAKE_SECRET_B64,
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


def test_plan_references_credential_presence_script(tmp_path: Path) -> None:
    plan = _plan_dict(_staging(tmp_path))
    assert "check_kraken_futures_demo_credentials_presence_readonly_v0.py" in json.dumps(
        plan["commands"]
    )


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


def test_fake_fetcher_hits_allowlisted_endpoints_only(tmp_path: Path) -> None:
    fetcher = _FakePrivateFetcher()
    mod = _load_adapter()
    staging = _staging(tmp_path)
    archive = _durable_archive(tmp_path)

    def _review_runner(staging_root: Path, review_out: Path) -> tuple[int, dict]:
        review_mod = _load_review()
        result = review_mod.review_evidence(staging_root)
        review_out.parent.mkdir(parents=True, exist_ok=True)
        review_out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        return 0 if result["verdict"] == review_mod.PASS else 1, result

    rc = mod.main(
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
        review_runner=_review_runner,
        environ=_FAKE_CRED_ENV,
    )
    assert rc == 0
    assert len(fetcher.requests) == 3
    called_paths = {req.url.split("/derivatives/api/v3")[-1] for req in fetcher.requests}
    assert called_paths == {
        "/accounts",
        "/openpositions",
        "/openorders",
    }
    for req in fetcher.requests:
        assert req.method == "GET"
        assert "sendorder" not in req.url.lower()


def test_execute_with_fake_fetcher_produces_durable_manifest(tmp_path: Path) -> None:
    mod = _load_adapter()
    staging = _staging(tmp_path)
    archive = _durable_archive(tmp_path)

    def _review_runner(staging_root: Path, review_out: Path) -> tuple[int, dict]:
        review_mod = _load_review()
        result = review_mod.review_evidence(staging_root)
        review_out.parent.mkdir(parents=True, exist_ok=True)
        review_out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        return 0 if result["verdict"] == review_mod.PASS else 1, result

    rc = mod.main(
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
        review_runner=_review_runner,
        environ=_FAKE_CRED_ENV,
    )
    assert rc == 0
    run_dirs = list((archive / "runs" / "testnet").iterdir())
    assert run_dirs
    copied = run_dirs[0]
    assert (copied / "MANIFEST.sha256").is_file()
    ok, reason = mod.verify_manifest_sha256(copied)
    assert ok, reason
    manifest = json.loads((copied / "wrapper_evidence" / "manifest.json").read_text())
    assert manifest["path_b_is_not_path_c"] is True
    assert manifest["session_class"] == "path_c_private_readonly_connectivity_v0"
    assert manifest["private_readonly_reachability_proven"] is True
    assert manifest["order_submission_allowed"] is False
    assert manifest["max_orders"] == 0
    assert manifest["max_cancel"] == 0
    assert manifest["get_only"] is True
    assert set(manifest["endpoints_called"]) == set(FUTURES_PRIVATE_READONLY_GET_ENDPOINTS)
    assert (copied / "CLOSEOUT.md").is_file()
    assert (copied / "RUN_METADATA.json").is_file()


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


def test_logs_do_not_contain_secret_marker(tmp_path: Path) -> None:
    mod = _load_adapter()
    staging = _staging(tmp_path)
    archive = _durable_archive(tmp_path)
    secret_env = dict(_FAKE_CRED_ENV)
    secret_env["KRAKEN_FUTURES_DEMO_API_SECRET"] = base64.b64encode(b"super-secret-value").decode()

    def _review_runner(staging_root: Path, review_out: Path) -> tuple[int, dict]:
        review_mod = _load_review()
        result = review_mod.review_evidence(staging_root)
        review_out.write_text(json.dumps(result) + "\n", encoding="utf-8")
        return 0, result

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
        review_runner=_review_runner,
        environ=secret_env,
    )
    for log_name in ("wrapper_stdout.log", "wrapper_stderr.log"):
        text = (staging / "logs" / log_name).read_text(encoding="utf-8")
        assert "super-secret-value" not in text
        assert "KRAKEN_FUTURES_DEMO_API_SECRET" not in text
