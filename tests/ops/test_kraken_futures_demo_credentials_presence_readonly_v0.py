"""Tests for Kraken Futures Demo read-only credential presence checker."""

from __future__ import annotations

import ast
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

from src.ops.kraken_futures_demo_credential_presence_contract_v0 import (
    CONFIRM_TOKEN_PRESENCE_ONLY_MANUAL,
    FORBIDDEN_ALTERNATE_ENV_KEYS,
    KRAKEN_FUTURES_DEMO_API_KEY_ENV_NAME,
    KRAKEN_FUTURES_DEMO_API_SECRET_ENV_NAME,
    REQUIRED_CREDENTIAL_ENV_KEYS,
    build_checker_boundary_v0,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts/ops/check_kraken_futures_demo_credentials_presence_readonly_v0.py"


def _load_checker():
    spec = importlib.util.spec_from_file_location(
        "check_kraken_futures_demo_credentials_presence_readonly_v0",
        SCRIPT,
    )
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def checker():
    return _load_checker()


def test_contract_env_names_exact() -> None:
    assert REQUIRED_CREDENTIAL_ENV_KEYS == (
        "KRAKEN_FUTURES_DEMO_API_KEY",
        "KRAKEN_FUTURES_DEMO_API_SECRET",
    )
    assert KRAKEN_FUTURES_DEMO_API_KEY_ENV_NAME == "KRAKEN_FUTURES_DEMO_API_KEY"
    assert KRAKEN_FUTURES_DEMO_API_SECRET_ENV_NAME == "KRAKEN_FUTURES_DEMO_API_SECRET"


def test_spot_and_live_keys_listed_as_forbidden_alternates() -> None:
    assert "KRAKEN_TESTNET_API_KEY" in FORBIDDEN_ALTERNATE_ENV_KEYS
    assert "KRAKEN_API_KEY" in FORBIDDEN_ALTERNATE_ENV_KEYS


def test_checker_uses_only_allowed_stdlib_imports() -> None:
    src = SCRIPT.read_text(encoding="utf-8")
    allowed_top = frozenset(
        {
            "__future__",
            "argparse",
            "collections",
            "json",
            "os",
            "sys",
            "pathlib",
            "typing",
            "src",
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


def test_checker_source_has_no_network_or_hash_of_secrets() -> None:
    src = SCRIPT.read_text(encoding="utf-8").lower()
    assert "urllib" not in src
    assert "requests" not in src
    assert "ccxt" not in src
    assert "hashlib" not in src


def test_boundary_flags_non_authorizing() -> None:
    cb = build_checker_boundary_v0()
    assert cb["futures_private_api_authorized"] is False
    assert cb["next_execute_allowed"] is False
    assert cb["checker_does_not_read_credential_values"] is True
    assert cb["checker_does_not_hash_credential_values"] is True


def test_injected_mapping_all_missing_blocked(checker) -> None:
    def _empty(_key: str) -> str:
        return ""

    payload, code = checker.run_presence_check(get_env_value=_empty)
    assert code == 0
    assert payload["status"] == "BLOCKED"
    assert payload["missing_count"] == 2
    assert set(payload["missing"]) == set(REQUIRED_CREDENTIAL_ENV_KEYS)


def test_injected_mapping_both_present_ready(checker) -> None:
    values = {
        KRAKEN_FUTURES_DEMO_API_KEY_ENV_NAME: "secret_key_material",
        KRAKEN_FUTURES_DEMO_API_SECRET_ENV_NAME: "secret_secret_material",
    }

    def _lookup(key: str) -> str:
        return values.get(key, "")

    payload, code = checker.run_presence_check(get_env_value=_lookup)
    assert code == 0
    assert payload["status"] == "READY_FOR_OPERATOR_REVIEW"
    assert payload["missing"] == []
    text = json.dumps(payload)
    assert "secret_key_material" not in text
    assert "secret_secret_material" not in text


def test_spot_keys_only_do_not_satisfy_futures_demo(checker) -> None:
    def _lookup(key: str) -> str:
        if key == "KRAKEN_TESTNET_API_KEY":
            return "x"
        if key == "KRAKEN_TESTNET_API_SECRET":
            return "y"
        return ""

    payload, _ = checker.run_presence_check(get_env_value=_lookup)
    assert payload["status"] == "BLOCKED"
    assert payload["missing_count"] == 2


def test_forbidden_alternate_present_blocks_even_if_futures_keys_present(checker) -> None:
    def _lookup(key: str) -> str:
        if key in REQUIRED_CREDENTIAL_ENV_KEYS:
            return "present"
        if key == "KRAKEN_TESTNET_API_KEY":
            return "spot_only"
        return ""

    payload, _ = checker.run_presence_check(get_env_value=_lookup)
    assert payload["status"] == "BLOCKED"
    assert "KRAKEN_TESTNET_API_KEY" in payload["forbidden_alternate_keys_present"]


def test_cli_without_confirm_token_exits_3() -> None:
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), "--json"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 3
    assert proc.stdout.strip() == ""


def test_cli_with_confirm_and_env_file_no_value_leak(tmp_path) -> None:
    leak = "UNIQUE_FUTURES_DEMO_LEAK_abc123"
    env_file = tmp_path / "demo.env"
    env_file.write_text(
        "\n".join(
            [
                f"{KRAKEN_FUTURES_DEMO_API_KEY_ENV_NAME}={leak}",
                f'{KRAKEN_FUTURES_DEMO_API_SECRET_ENV_NAME}="also_{leak}"',
            ]
        ),
        encoding="utf-8",
    )
    proc = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--json",
            "--env-file",
            str(env_file),
            "--confirm-token",
            CONFIRM_TOKEN_PRESENCE_ONLY_MANUAL,
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0
    payload = json.loads(proc.stdout)
    assert payload["status"] == "READY_FOR_OPERATOR_REVIEW"
    assert leak not in proc.stdout
    assert leak not in proc.stderr
