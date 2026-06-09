"""Tests for run_order_capability_dry_validation_adapter_v1 (offline only)."""

from __future__ import annotations

import importlib.util
import io
import json
import shutil
import subprocess
import sys
from contextlib import redirect_stdout
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
ADAPTER_SCRIPT = ROOT / "scripts" / "ops" / "run_order_capability_dry_validation_adapter_v1.py"
CONTRACT_MODULE = ROOT / "src" / "ops" / "order_capability_dry_validation_contract_v1.py"

REQUIRED_OPERATOR_GO_TOKEN = "GO_ORDER_CAPABILITY_DRY_VALIDATION_OFFLINE_EXECUTE_V1"
TEST_PACKAGE_MARKER = "RUN_ORDER_CAPABILITY_DRY_VALIDATION_ADAPTER_V1_TEST=true"


def _load_adapter():
    spec = importlib.util.spec_from_file_location(
        "run_order_capability_dry_validation_adapter_v1", ADAPTER_SCRIPT
    )
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def _durable_archive(tmp_path: Path) -> Path:
    path = ROOT / "tests" / ".pytest_archive_roots" / tmp_path.name
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def _base_argv(archive: Path, *, run_id: str = "order_cap_dry_validation_test_run") -> list[str]:
    return [
        "--archive-root",
        str(archive),
        "--run-id",
        run_id,
        "--instrument",
        "PF_XBTUSD",
        "--venue",
        "Kraken Futures Demo / demo-futures.kraken.com",
        "--max-loss-cap-eur",
        "1.00",
        "--max-notional-eur",
        "10.0",
        "--order-type",
        "limit",
        "--session-duration-seconds",
        "60",
        "--abort-ack-confirmed",
        "--max-notional-confirmed",
        "--no-network",
        "--no-order",
    ]


@pytest.fixture(autouse=True)
def _cleanup_archive_roots():
    yield
    archive_roots = ROOT / "tests" / ".pytest_archive_roots"
    if archive_roots.is_dir():
        shutil.rmtree(archive_roots, ignore_errors=True)


def test_scripts_exist() -> None:
    assert TEST_PACKAGE_MARKER
    assert ADAPTER_SCRIPT.is_file()
    assert CONTRACT_MODULE.is_file()


def test_help_smoke() -> None:
    proc = subprocess.run(
        [sys.executable, str(ADAPTER_SCRIPT), "--help"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0
    assert "--archive-root" in proc.stdout
    assert "--operator-go-token" in proc.stdout
    assert "--no-network" in proc.stdout
    assert "--no-order" in proc.stdout


def test_write_evidence_missing_operator_go_fails(tmp_path: Path) -> None:
    mod = _load_adapter()
    archive = _durable_archive(tmp_path)
    rc = mod.main(_base_argv(archive) + ["--write-evidence"])
    assert rc != 0


def test_write_evidence_with_invalid_operator_go_fails(tmp_path: Path) -> None:
    mod = _load_adapter()
    archive = _durable_archive(tmp_path)
    rc = mod.main(
        _base_argv(archive)
        + ["--write-evidence", "--operator-go-token", "INVALID_GO_TOKEN"]
    )
    assert rc != 0


def test_no_network_false_fails_closed(tmp_path: Path) -> None:
    mod = _load_adapter()
    archive = _durable_archive(tmp_path)
    argv = [
        item
        for item in _base_argv(archive)
        if item not in {"--no-network", "--no-order"}
    ] + [
        "--write-evidence",
        "--operator-go-token",
        REQUIRED_OPERATOR_GO_TOKEN,
        "--allow-network",
        "--no-order",
    ]
    rc = mod.main(argv)
    assert rc != 0


def test_plan_only_emits_json_without_evidence(tmp_path: Path) -> None:
    mod = _load_adapter()
    archive = _durable_archive(tmp_path)
    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = mod.main(_base_argv(archive) + ["--plan-only", "--json"])
    assert rc == 0
    plan = json.loads(buf.getvalue())
    assert plan["mode"] == "plan-only"
    assert plan["no_network"] is True
    assert plan["no_order"] is True
    assert not any(archive.rglob("ORDER_CAPABILITY_DRY_VALIDATION_RESULT.json"))


def test_write_evidence_creates_durable_bundle(tmp_path: Path) -> None:
    mod = _load_adapter()
    archive = _durable_archive(tmp_path)
    rc = mod.main(
        _base_argv(archive)
        + [
            "--write-evidence",
            "--operator-go-token",
            REQUIRED_OPERATOR_GO_TOKEN,
        ]
    )
    assert rc == 0
    dest = archive / "runs" / "testnet" / "order_cap_dry_validation_test_run"
    assert (dest / "RUN_METADATA.json").is_file()
    assert (dest / "ORDER_CAPABILITY_DRY_VALIDATION_RESULT.json").is_file()
    assert (dest / "CLOSEOUT.md").is_file()
    assert (dest / "MANIFEST.sha256").is_file()
    ok, _msg = mod.verify_manifest(dest)
    assert ok is True
    payload = json.loads(
        (dest / "ORDER_CAPABILITY_DRY_VALIDATION_RESULT.json").read_text(encoding="utf-8")
    )
    assert payload["verdict"] == "PASS"
    assert payload["safety_flags"]["order_submission_executed"] is False
    assert payload["safety_flags"]["network_api_called"] is False
    assert "order_submission_executed=true" not in (dest / "CLOSEOUT.md").read_text(
        encoding="utf-8"
    ).lower()
