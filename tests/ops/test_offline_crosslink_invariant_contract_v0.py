"""Offline crosslink invariant contract v0 (tests-only).

Verankert die im Traceability-Report beschriebene Semantik (Recorded public source → P67-Meta →
bounded replay / lokale Inventur) an stabilen Repo-Ankern — ohne /tmp-Gate-Artefakte, ohne Subprozesse,
ohne Netzwerk. Erzeugt keine Laufzeitfreigabe und keine parallele Evidenz-Oberfläche.
"""

from __future__ import annotations

import importlib
import json
import socket
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]

# Must stay aligned with `shadow_247_futures_start_wrapper_skeleton_v0` and wrapper contract tests.
RECORDED_PUBLIC_REST_REPLAY_KIND = "bounded_shadow_dry_run_recorded_public_rest_replay_heartbeat"

_RECORDED_ADAPTER = REPO_ROOT / "src/ops/p67/recorded_price_series_v0.py"
_P67_SCHEDULER = REPO_ROOT / "src/ops/p67/shadow_session_scheduler_v1.py"
_WRAPPER = REPO_ROOT / "scripts/ops/shadow_247_futures_start_wrapper_skeleton_v0.py"
_BRIDGE = REPO_ROOT / "scripts/ops/build_public_rest_to_supervised_observer_bridge_v0.py"
_WRAPPER_OWNER_TEST = REPO_ROOT / "tests/ops/test_shadow_247_futures_start_wrapper_skeleton_v0.py"
_PREFLIGHT = REPO_ROOT / "docs/ops/runbooks/PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V0.md"
_SUPERVISED_OBSERVER_TEST = (
    REPO_ROOT / "tests/ops/test_shadow_observation_supervised_timed_observer_v0.py"
)


def test_public_capture_and_recorded_adapter_surfaces_exist() -> None:
    matches = list(REPO_ROOT.glob("scripts/ops/capture_public_rest_binance*_v0.py"))
    assert matches, "expected at least one public REST capture script under scripts/ops/"
    assert _RECORDED_ADAPTER.is_file()


def test_recorded_price_adapter_documents_midpoint_and_returns_contract() -> None:
    text = _RECORDED_ADAPTER.read_text(encoding="utf-8")
    assert "load_simple_returns_from_recorded_price_source" in text
    assert "bidPrice" in text and "askPrice" in text
    assert "midpoint" in text.lower()


def test_p67_scheduler_exposes_recorded_price_meta_keys() -> None:
    body = _P67_SCHEDULER.read_text(encoding="utf-8")
    for key in (
        "recorded_price_source_used",
        "recorded_price_source_path",
        "recorded_price_series_count",
        "validate_recorded_price_source_path",
        "load_simple_returns_from_recorded_price_source",
    ):
        assert key in body, f"missing stable crosslink field/reference: {key!r}"


def test_bounded_wrapper_wires_recorded_public_rest_inventory_and_replay_kind() -> None:
    wrap = _WRAPPER.read_text(encoding="utf-8")
    assert RECORDED_PUBLIC_REST_REPLAY_KIND in wrap
    assert "def _inventory_recorded_public_rest_source" in wrap
    assert "recorded_public_rest_source_manifest_count" in wrap
    assert "nor supervised observer" in wrap
    assert "nor supervised-observer scripts are invoked in this mode." in wrap


def test_shadow_247_wrapper_owner_test_defines_matching_replay_constant() -> None:
    body = _WRAPPER_OWNER_TEST.read_text(encoding="utf-8")
    assert RECORDED_PUBLIC_REST_REPLAY_KIND in body
    assert "RECORDED_PUBLIC_REST_REPLAY_SOURCE_ATTACHED=true" in body


def test_optional_public_rest_to_supervised_observer_bridge_script_present() -> None:
    assert _BRIDGE.is_file()


def test_declarative_no_order_surfaces_reject_live_and_execution_authority() -> None:
    ac = importlib.import_module("src.shadow_no_order_proof.adapter_contract_v0")
    mv = importlib.import_module("src.shadow_no_order_proof.markers_v0")
    assert ac.LIVE_ALLOWED is False
    assert ac.EXECUTABLE_COMMAND_CREATED is False
    assert mv.LIVE_ALLOWED is False
    assert mv.EXECUTABLE_COMMAND_CREATED is False


def test_bounded_shadow_adapter_plan_is_non_authorizing() -> None:
    from src.shadow_no_order_proof.bounded_adapter_v0 import build_bounded_shadow_adapter_plan_v0

    plan = build_bounded_shadow_adapter_plan_v0(source="offline_crosslink_invariant_contract_v0")
    assert plan.live_allowed is False
    assert plan.testnet_allowed is False
    assert plan.exchange_allowed is False
    assert plan.broker_allowed is False
    assert plan.order_submission_allowed is False
    assert plan.executable_command_created is False
    assert plan.scheduler_allowed is False


def test_bounded_runtime_contract_module_rejects_execution_approval() -> None:
    mod = importlib.import_module("tests.ops.test_shadow_247_futures_bounded_runtime_contract_v0")
    assert mod.BOUNDED_RUNTIME_CONTRACT_APPROVES_EXECUTION is False


def test_preflight_contract_doc_states_blocked_non_authorizing() -> None:
    """Read-only doc anchor: contractual language must remain, but this test is not an approval."""
    text = _PREFLIGHT.read_text(encoding="utf-8")
    assert "BLOCKED" in text
    collapsed = text.lower().replace("*", "")
    assert "does not authorize activation" in collapsed


def test_supervised_observer_is_optional_test_surface_not_p67_gate() -> None:
    """Traceability crosslink reused gate artefacts; P67 Pfad referenziert kein supervised bundle."""
    assert _SUPERVISED_OBSERVER_TEST.is_file()
    p67_txt = _P67_SCHEDULER.read_text(encoding="utf-8").lower()
    assert "supervised" not in p67_txt


def test_p67_recorded_source_meta_matches_offline_crosslink_semantics(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def _deny_socket(*_a: object, **_kw: object) -> object:
        raise AssertionError("socket creation blocked for offline crosslink contract")

    monkeypatch.setattr(socket, "socket", _deny_socket)
    sys.modules.pop("src.ops.p67.shadow_session_scheduler_v1", None)

    gate = tmp_path / "recorded_gate"
    rows = []
    for i in range(61):
        rows.append(
            {
                "bidPrice": f"{100 + i}.00",
                "askPrice": f"{100 + i}.50",
                "symbol": "BTCUSDT",
            },
        )
    gate.mkdir(parents=True)
    (gate / "mids.json").write_text(json.dumps(rows) + "\n", encoding="utf-8")

    from src.ops.p67.shadow_session_scheduler_v1 import (
        P67RunContextV1,
        run_shadow_session_scheduler_v1,
    )

    out = run_shadow_session_scheduler_v1(
        P67RunContextV1(
            mode="shadow",
            iterations=1,
            interval_seconds=0.0,
            recorded_price_source=gate,
        ),
    )
    assert out["meta"]["recorded_price_source_used"] is True
    assert out["meta"]["recorded_price_series_count"] == 60
    assert out["meta"]["recorded_price_source_path"] == str(gate.resolve())
