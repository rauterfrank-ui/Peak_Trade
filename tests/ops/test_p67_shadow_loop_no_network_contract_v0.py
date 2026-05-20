"""v0 contract: P67 shadow-loop audited chain avoids network/trading IO surface (tests-only).

Exercises the static call path documented in the P66/P67 no-network audit:
run_shadow_loop_v1.sh -> p67 CLI -> scheduler -> P66 -> P64/P63 -> P61/P62 -> P58 -> P57 (+ switch-layer + evidence).
Does not execute the shell wrapper.
"""

from __future__ import annotations

import importlib
import re
import socket
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]

_SHADOW_LOOP_SH = REPO_ROOT / "scripts" / "ops" / "run_shadow_loop_v1.sh"

# Audited source files (same closure as P66/P67 shadow-loop audit + direct switch-layer deps).
_P67_CHAIN_SOURCE_RELPATHS: tuple[str, ...] = (
    "scripts/ops/run_shadow_loop_v1.sh",
    "src/ops/p67/shadow_session_scheduler_cli_v1.py",
    "src/ops/p67/shadow_session_scheduler_v1.py",
    "src/ops/p67/recorded_price_series_v0.py",
    "src/ops/p66/run_online_readiness_operator_entrypoint_v1.py",
    "src/ops/p65/run_online_readiness_loop_runner_v1.py",
    "src/ops/p64/run_online_readiness_runner_v1.py",
    "src/ops/p63/run_online_readiness_shadow_runner_v1.py",
    "src/ops/p62/run_online_readiness_shadow_session_v1.py",
    "src/ops/p61/run_online_readiness_v1.py",
    "src/ops/p61/online_readiness_contract_v1.py",
    "src/ops/p58/switch_layer_online_readiness_v1.py",
    "src/ops/p57/switch_layer_paper_shadow_v1.py",
    "src/ops/p53/switch_layer_evidence_v1.py",
    "src/ops/common/__init__.py",
    "src/ops/common/serialize_v1.py",
    "src/ai/switch_layer/switch_layer_v1.py",
    "src/ai/switch_layer/config_v1.py",
    "src/ai/switch_layer/types_v1.py",
    "src/ai_orchestration/switch_layer_routing_v1.py",
)

_BANNED_NETWORK_IMPORT_RE = re.compile(
    r"(?m)^\s*(?:from\s+(requests|httpx|websocket|websockets|aiohttp|ccxt)\b"
    r"|import\s+(requests|httpx|websocket|websockets|aiohttp|ccxt)\b"
    r"|from\s+urllib\.request\b"
    r"|import\s+urllib\.request\b"
    r"|import\s+socket\b"
    r"|from\s+socket\b)",
)

_CREDENTIAL_ORDER_RE = re.compile(
    r"(create_order|place_order|submit_order|order_submission|KrakenLiveCandleSource|api_key|\bsecret\b|\bcredential\b|\bcredentials\b)",
    re.IGNORECASE,
)

_FORBIDDEN_PHRASES: tuple[str, ...] = (
    "live trading",
    "broker execution",
    "private endpoint",
)


def _chain_texts() -> dict[str, str]:
    out: dict[str, str] = {}
    for rel in _P67_CHAIN_SOURCE_RELPATHS:
        path = REPO_ROOT / rel
        assert path.is_file(), f"missing audited chain file: {rel}"
        out[rel] = path.read_text(encoding="utf-8")
    return out


def test_run_shadow_loop_invokes_p67_cli_module() -> None:
    text = _SHADOW_LOOP_SH.read_text(encoding="utf-8")
    assert "python3 -m src.ops.p67.shadow_session_scheduler_cli_v1" in text


def test_run_shadow_loop_guards_rec_args_expansion_for_bash32_regression_v0() -> None:
    """Regression anchor for #3563 — empty REC_ARGS must not expand on bash 3.2."""
    text = _SHADOW_LOOP_SH.read_text(encoding="utf-8")

    assert "REC_ARGS=()" in text
    assert "PY_ARGS=(" in text
    assert re.search(r"\[\[\s*\$\{#REC_ARGS\[@\]\}\s*-gt\s*0\s*\]\]", text)

    guarded_match = re.search(
        r"if\s+\[\[\s*\$\{#REC_ARGS\[@\]\}\s*-gt\s*0\s*\]\];\s*then\s*\n"
        r"\s*python3 -m src\.ops\.p67\.shadow_session_scheduler_cli_v1 "
        r'"\$\{PY_ARGS\[@\]\}"\s+"\$\{REC_ARGS\[@\]\}"',
        text,
    )
    assert guarded_match is not None

    fallback_match = re.search(
        r"else\s*\n"
        r"\s*python3 -m src\.ops\.p67\.shadow_session_scheduler_cli_v1 "
        r'"\$\{PY_ARGS\[@\]\}"\s*$',
        text,
        re.MULTILINE,
    )
    assert fallback_match is not None

    # Pre-#3563 anti-pattern: one python3 invocation unconditionally trailing REC_ARGS.
    assert text.count("python3 -m src.ops.p67.shadow_session_scheduler_cli_v1") == 2

    rec_expansion_lines = [
        line for line in text.splitlines() if "${REC_ARGS[@]}" in line and "python3" in line
    ]
    assert len(rec_expansion_lines) == 1
    assert guarded_match.group(0).splitlines()[-1].strip() == rec_expansion_lines[0].strip()


def test_p67_scheduler_defines_synthetic_default_prices() -> None:
    body = (REPO_ROOT / "src/ops/p67/shadow_session_scheduler_v1.py").read_text(encoding="utf-8")
    assert "_DEFAULT_PRICES" in body
    assert "0.001" in body
    assert "KrakenLiveCandleSource" not in body


def test_p67_chain_sources_exclude_network_import_patterns() -> None:
    for rel, text in _chain_texts().items():
        m = _BANNED_NETWORK_IMPORT_RE.search(text)
        assert m is None, f"{rel}: disallowed import pattern near: {m.group(0)!r}"


def test_p67_chain_sources_exclude_trading_connector_markers() -> None:
    for rel, text in _chain_texts().items():
        assert "KrakenLiveCandleSource" not in text, rel
        m = _CREDENTIAL_ORDER_RE.search(text)
        assert m is None, f"{rel}: unexpected marker {m.group(0)!r}"
        lowered = text.lower()
        for phrase in _FORBIDDEN_PHRASES:
            assert phrase not in lowered, f"{rel}: forbidden phrase {phrase!r}"


def test_p67_chain_sources_exclude_testnet_literal() -> None:
    """'testnet' must not appear in audited production chain sources (mode guards use live/record)."""
    for rel, text in _chain_texts().items():
        assert "testnet" not in text.lower(), rel


def test_p67_scheduler_one_iteration_runs_under_socket_guard(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def _deny_socket(*_a: object, **_kw: object) -> object:
        raise AssertionError("socket creation blocked for no-network contract")

    monkeypatch.setattr(socket, "socket", _deny_socket)

    sys.modules.pop("src.ops.p67.shadow_session_scheduler_v1", None)
    importlib.import_module("src.ops.p67.shadow_session_scheduler_v1")
    from src.ops.p67.shadow_session_scheduler_v1 import (
        P67RunContextV1,
        run_shadow_session_scheduler_v1,
    )

    out = run_shadow_session_scheduler_v1(
        P67RunContextV1(
            mode="shadow",
            run_id="no_net_contract",
            out_dir=tmp_path,
            iterations=1,
            interval_seconds=0.0,
        ),
    )
    assert out["meta"]["iterations"] == 1
    assert len(out["events"]) == 1
    assert "p66" in out["events"][0]


def test_p67_cli_module_imports_under_socket_guard(monkeypatch: pytest.MonkeyPatch) -> None:
    def _deny_socket(*_a: object, **_kw: object) -> object:
        raise AssertionError("socket creation blocked for no-network contract")

    monkeypatch.setattr(socket, "socket", _deny_socket)

    sys.modules.pop("src.ops.p67.shadow_session_scheduler_cli_v1", None)
    sys.modules.pop("src.ops.p67.shadow_session_scheduler_v1", None)
    cli = importlib.import_module("src.ops.p67.shadow_session_scheduler_cli_v1")
    assert hasattr(cli, "main")
