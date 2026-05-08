"""Tests for read-only Testnet prerequisite checker."""

from __future__ import annotations

import ast
import json
import subprocess
import sys
from pathlib import Path

SCRIPT = Path("scripts/ops/check_testnet_prerequisites_readonly.py")

REQUIRED_A = "PEAK_TRADE_TESTNET_OPERATOR_GATE_ACK"
REQUIRED_B = "PEAK_TRADE_TESTNET_CONFIG_DECLARED"


def test_checker_uses_only_allowed_stdlib_imports() -> None:
    src = SCRIPT.read_text(encoding="utf-8")
    allowed_top = frozenset(
        {
            "__future__",
            "argparse",
            "json",
            "os",
            "sys",
            "pathlib",
            "typing",
        }
    )
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                base = alias.name.split(".", 1)[0]
                assert base in allowed_top, f"unexpected import: {alias.name}"
        if isinstance(node, ast.ImportFrom) and node.module:
            base = node.module.split(".", 1)[0]
            assert base in allowed_top, f"unexpected from-import: {node.module}"


def test_checker_source_has_no_exchange_or_broker_execution_hooks() -> None:
    src = SCRIPT.read_text(encoding="utf-8").lower()
    assert "ccxt" not in src
    assert "urllib.request" not in src
    assert "requests" not in src


def test_no_env_no_file_all_missing_blocked(monkeypatch) -> None:
    monkeypatch.delenv(REQUIRED_A, raising=False)
    monkeypatch.delenv(REQUIRED_B, raising=False)
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), "--json"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0
    payload = json.loads(proc.stdout)
    assert payload["status"] == "BLOCKED"
    assert payload["missing_count"] == 2
    assert payload["required_present_count"] == 0
    assert set(payload["missing"]) == {REQUIRED_A, REQUIRED_B}
    cb = payload["checker_boundary_v0"]
    assert cb["non_authorizing"] is True
    assert cb["testnet_authorized"] is False
    assert cb["live_authorized"] is False
    assert cb["checker_does_not_connect_to_exchange"] is True
    assert cb["checker_does_not_validate_credentials"] is True


def test_env_file_supplies_keys_ready_for_review(tmp_path, monkeypatch) -> None:
    monkeypatch.delenv(REQUIRED_A, raising=False)
    monkeypatch.delenv(REQUIRED_B, raising=False)
    f = tmp_path / "e.env"
    f.write_text(
        "\n".join(
            [
                f"# secret-looking line must not appear in checker stdout",
                f"{REQUIRED_A}=super_secret_value_xyz_999",
                f'{REQUIRED_B}="also_secret"',
                "",
            ]
        ),
        encoding="utf-8",
    )
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), "--json", "--env-file", str(f)],
        check=False,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0
    payload = json.loads(proc.stdout)
    assert payload["status"] == "READY_FOR_OPERATOR_REVIEW"
    assert payload["missing_count"] == 0
    assert payload["required_present_count"] == 2
    assert payload["missing"] == []
    cb = payload["checker_boundary_v0"]
    assert cb["non_authorizing"] is True
    assert cb["testnet_authorized"] is False
    assert "super_secret" not in proc.stdout
    assert "also_secret" not in proc.stdout
    assert "xyz_999" not in proc.stdout


def test_env_file_missing_exits_2(tmp_path) -> None:
    missing = tmp_path / "nope.env"
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), "--json", "--env-file", str(missing)],
        check=False,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 2
    assert proc.stdout.strip() == ""


def test_human_output_redacts_and_shows_authorization_false(tmp_path, monkeypatch) -> None:
    monkeypatch.delenv(REQUIRED_A, raising=False)
    monkeypatch.delenv(REQUIRED_B, raising=False)
    f = tmp_path / "e.env"
    leak = "UNIQUE_LEAK_TOKEN_FOR_TEST_7f3a"
    f.write_text(f"{REQUIRED_A}=x\n{REQUIRED_B}={leak}\n", encoding="utf-8")
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), "--env-file", str(f)],
        check=False,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0
    assert leak not in proc.stdout
    assert leak not in proc.stderr
    assert "status=READY_FOR_OPERATOR_REVIEW" in proc.stdout
    assert "testnet_authorized=false" in proc.stdout
    assert "live_authorized=false" in proc.stdout
    assert "value_redacted=true" in proc.stdout
