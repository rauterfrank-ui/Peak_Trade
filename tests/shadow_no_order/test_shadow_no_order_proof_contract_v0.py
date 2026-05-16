"""v0 contract: Shadow no-order proof markers stay declarative; canonical env defaults stay safe."""

from __future__ import annotations

import re
from pathlib import Path

from src.core.environment import EnvironmentConfig, TradingEnvironment
from src.shadow_no_order_proof import markers_v0

_FORBIDDEN_SOURCE_MARKERS = (
    "requests",
    "httpx",
    "urllib.request",
    "socket",
    "subprocess",
    "ccxt",
    "aiohttp",
    "if __name__",
)

# Whole-package guard: declarative surface only (no I/O, CLI, runtime, or trading clients).
_PACKAGE_ROOT = Path(__file__).resolve().parents[2] / "src" / "shadow_no_order_proof"
_NO_EXEC_SURFACE_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"if\s+__name__\s*==\s*[\"']__main__[\"']"), "__main__ guard"),
    (re.compile(r"\bdef\s+main\s*\("), "def main("),
    (re.compile(r"\b(import|from)\s+argparse\b"), "argparse import"),
    (re.compile(r"argparse\."), "argparse usage"),
    (re.compile(r"\b(import|from)\s+click\b"), "click import"),
    (re.compile(r"click\."), "click usage"),
    (re.compile(r"\b(import|from)\s+typer\b"), "typer import"),
    (re.compile(r"typer\."), "typer usage"),
    (re.compile(r"\buvicorn\b"), "uvicorn"),
    (re.compile(r"\brun_scheduler\b"), "run_scheduler"),
    (re.compile(r"\brun_with_timeout\b"), "run_with_timeout"),
    (re.compile(r"\b(import|from)\s+subprocess\b"), "subprocess import"),
    (re.compile(r"\bsubprocess\."), "subprocess call"),
    (re.compile(r"\bos\.system\s*\("), "os.system"),
    (re.compile(r"\bos\.popen\s*\("), "os.popen"),
    (re.compile(r"\b(import|from)\s+socket\b"), "socket import"),
    (re.compile(r"\bsocket\."), "socket usage"),
    (re.compile(r"\b(import|from)\s+multiprocessing\b"), "multiprocessing import"),
    (re.compile(r"\b(import|from)\s+threading\b"), "threading import"),
    (re.compile(r"\brequests\."), "requests usage"),
    (re.compile(r"\b(import|from)\s+requests\b"), "requests import"),
    (re.compile(r"\bhttpx\."), "httpx usage"),
    (re.compile(r"\b(import|from)\s+httpx\b"), "httpx import"),
    (re.compile(r"\b(import|from)\s+urllib\b"), "urllib import"),
    (re.compile(r"\burllib\.request\b"), "urllib.request"),
    (re.compile(r"\b(import|from)\s+aiohttp\b"), "aiohttp import"),
    (re.compile(r"\baiohttp\."), "aiohttp usage"),
    (re.compile(r"\bwebsocket"), "websocket"),
    (re.compile(r"\bccxt\b"), "ccxt"),
    (re.compile(r"\bcreate_order\b"), "create_order"),
    (re.compile(r"\bplace_order\b"), "place_order"),
    (re.compile(r"\bsend_order\b"), "send_order"),
    (re.compile(r"\bsubmit_order\b"), "submit_order"),
    (re.compile(r"\border_submission\b"), "order_submission"),
    (re.compile(r"\bapi_key\s*="), "api_key assignment"),
    (re.compile(r"\bsecret\s*="), "secret assignment"),
    (re.compile(r"\bprivate_key\s*="), "private_key assignment"),
    (re.compile(r"\bcredential\s*="), "credential assignment"),
    (re.compile(r"SHADOW_MODE_ALLOWED\s*=\s*True"), "SHADOW_MODE_ALLOWED true"),
    (re.compile(r"ORDER_SUBMISSION_ALLOWED\s*=\s*True"), "ORDER_SUBMISSION_ALLOWED true"),
    (re.compile(r"BROKER_ALLOWED\s*=\s*True"), "BROKER_ALLOWED true"),
    (re.compile(r"EXCHANGE_ALLOWED\s*=\s*True"), "EXCHANGE_ALLOWED true"),
    (re.compile(r"LIVE_ALLOWED\s*=\s*True"), "LIVE_ALLOWED true"),
    (re.compile(r"TESTNET_ALLOWED\s*=\s*True"), "TESTNET_ALLOWED true"),
    (re.compile(r"PAPER_ORDER_PATH_ALLOWED\s*=\s*True"), "PAPER_ORDER_PATH_ALLOWED true"),
    (re.compile(r"SCHEDULER_ALLOWED\s*=\s*True"), "SCHEDULER_ALLOWED true"),
    (re.compile(r"RUNTIME_ALLOWED\s*=\s*True"), "RUNTIME_ALLOWED true"),
    (re.compile(r"EXECUTABLE_COMMAND_CREATED\s*=\s*True"), "EXECUTABLE_COMMAND_CREATED true"),
)


def _shadow_no_order_proof_py_files() -> list[Path]:
    assert _PACKAGE_ROOT.is_dir(), f"missing package: {_PACKAGE_ROOT}"
    paths = sorted(
        p for p in _PACKAGE_ROOT.rglob("*.py") if p.is_file() and "__pycache__" not in p.parts
    )
    assert paths, "expected at least one Python file under shadow_no_order_proof"
    return paths


def test_shadow_no_order_proof_package_is_non_execution_surface() -> None:
    """Scan only `src/shadow_no_order_proof/` — no whole-repo walk."""
    for path in _shadow_no_order_proof_py_files():
        text = path.read_text(encoding="utf-8")
        for pattern, label in _NO_EXEC_SURFACE_PATTERNS:
            match = pattern.search(text)
            assert match is None, f"{label!r} matched in {path}: {match.group(0)!r}"


def test_shadow_no_order_markers_are_all_false_and_tagged() -> None:
    assert markers_v0.SHADOW_NO_ORDER_PROOF_V0 == "shadow_no_order_proof_v0"
    assert markers_v0.SHADOW_MODE_ALLOWED is False
    assert markers_v0.ORDER_SUBMISSION_ALLOWED is False
    assert markers_v0.BROKER_ALLOWED is False
    assert markers_v0.EXCHANGE_ALLOWED is False
    assert markers_v0.EXECUTABLE_COMMAND_CREATED is False
    assert markers_v0.LIVE_ALLOWED is False
    assert markers_v0.TESTNET_ALLOWED is False
    assert markers_v0.PAPER_ORDER_PATH_ALLOWED is False
    assert markers_v0.SCHEDULER_ALLOWED is False
    assert markers_v0.RUNTIME_ALLOWED is False


def test_markers_module_source_has_no_execution_or_network_tokens() -> None:
    path = Path(markers_v0.__file__).resolve()
    text = path.read_text(encoding="utf-8")
    low = text.lower()
    for needle in _FORBIDDEN_SOURCE_MARKERS:
        assert needle.lower() not in low, f"unexpected token {needle!r} in {path}"


def test_environment_config_defaults_remain_paper_and_gated() -> None:
    """Canonical owner: src.core.environment.EnvironmentConfig defaults."""
    cfg = EnvironmentConfig()
    assert cfg.environment == TradingEnvironment.PAPER
    assert cfg.enable_live_trading is False
    assert cfg.testnet_dry_run is True
    assert cfg.live_mode_armed is False
    assert cfg.live_dry_run_mode is True
