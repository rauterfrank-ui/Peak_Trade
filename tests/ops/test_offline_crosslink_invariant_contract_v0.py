"""Offline crosslink invariant contract v0 (tests-only).

Verankert die im Traceability-Report beschriebene Semantik (Recorded public source → P67-Meta →
bounded replay / lokale Inventur) an stabilen Repo-Ankern — ohne /tmp-Gate-Artefakte, ohne Subprozesse,
ohne Netzwerk. Erzeugt keine Laufzeitfreigabe und keine parallele Evidenz-Oberfläche.

Ergänzt die statische Offline-Grenze zwischen ``build_static_market_capture_package_v0`` und
``build_public_rest_to_supervised_observer_bridge_v0`` (gemeinsames CONFIRM_TOKEN); schließt **kein**
neues supervised-observation-Bundle ein.

Ergänzt zudem einen statischen Scheduler-Anker für Paper/Shadow-247 Jobs und das Futures-Wrapper-TOML
(Pfade lösen unter ``REPO_ROOT``; keine Laufzeitfreigabe).

Ergänzt stabile Offline-Anker für ``snapshot_operator_stop_signals`` (Contract-ID / PT_STOP_KEYS).

Ergänzt Pfad-Anker für ``SHADOW_247_GOVERNANCE_CHARTER_V0.md`` und optionale Observation-Entrypoint-Skripte
(nur ``Path.is_file``; keine Charter-Semantik — siehe ``test_shadow247_governance_charter_doc_contract_v0``).
"""

from __future__ import annotations

import importlib
import importlib.util
import json
import socket
import sys
from pathlib import Path
from typing import Any

import pytest

try:
    import tomllib
except ImportError:
    import tomli as tomllib  # type: ignore[no-redef,import-not-found]

REPO_ROOT = Path(__file__).resolve().parents[2]

# Must stay aligned with `shadow_247_futures_start_wrapper_skeleton_v0` and wrapper contract tests.
RECORDED_PUBLIC_REST_REPLAY_KIND = "bounded_shadow_dry_run_recorded_public_rest_replay_heartbeat"

_RECORDED_ADAPTER = REPO_ROOT / "src/ops/p67/recorded_price_series_v0.py"
_P67_SCHEDULER = REPO_ROOT / "src/ops/p67/shadow_session_scheduler_v1.py"
_WRAPPER = REPO_ROOT / "scripts/ops/shadow_247_futures_start_wrapper_skeleton_v0.py"
_BRIDGE = REPO_ROOT / "scripts/ops/build_public_rest_to_supervised_observer_bridge_v0.py"
_STATIC_PKG = REPO_ROOT / "scripts/ops/build_static_market_capture_package_v0.py"
# Operator-supplied static package + public-rest→observer bridge share this offline gate (no new bundle).
_OFFLINE_GATE_CONFIRM_TOKEN = "NO_NETWORK_NO_BROKER_NO_EXCHANGE_NO_ORDERS"
_WRAPPER_OWNER_TEST = REPO_ROOT / "tests/ops/test_shadow_247_futures_start_wrapper_skeleton_v0.py"
_PREFLIGHT = REPO_ROOT / "docs/ops/runbooks/PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V0.md"
_CHARTER = REPO_ROOT / "docs/ops/runbooks/SHADOW_247_GOVERNANCE_CHARTER_V0.md"
_OBS_FILE_SNAPSHOT_SCRIPT = REPO_ROOT / "scripts/ops/run_shadow_observation_file_snapshot_v0.py"
_OBS_SUPERVISED_TIMED_SCRIPT = (
    REPO_ROOT / "scripts/ops/run_shadow_observation_supervised_timed_v0.py"
)
_SUPERVISED_OBSERVER_TEST = (
    REPO_ROOT / "tests/ops/test_shadow_observation_supervised_timed_observer_v0.py"
)
_OFFLINE_CROSSLINK_SELF = Path(__file__).resolve()
_JOBS_TOML = REPO_ROOT / "config" / "scheduler" / "jobs.toml"
_SHADOW247_WRAPPER_OPS_TOML = (
    REPO_ROOT / "config" / "ops" / "shadow_247_futures_wrapper_skeleton.toml"
)
# Stable scheduler names; static path contract only (preflight reporter may stay enabled elsewhere).
_OFFLINE_SHADOW247_SCHEDULER_JOB_NAMES = (
    "paper_shadow_247_paper_only_preflight_status_v0",
    "shadow_247_futures_prestart_evidence_drycheck_placeholder_v0",
    "paper_shadow_247_paper_only_runtime_high_vol_no_trade_v0",
)
_SNAPSHOT_OPERATOR_STOP_SCRIPT = REPO_ROOT / "scripts" / "ops" / "snapshot_operator_stop_signals.py"


def _load_scripts_ops_module(fake_name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(fake_name, path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


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


def test_static_market_capture_package_and_bridge_share_offline_confirm_token() -> None:
    """Static gate package and bridge share one explicit offline confirm line — metadata crosslink only."""
    assert _STATIC_PKG.is_file()
    pkg_mod = _load_scripts_ops_module("_offline_crosslink_static_pkg_v0", _STATIC_PKG)
    bridge_mod = _load_scripts_ops_module("_offline_crosslink_pub_rest_bridge_v0", _BRIDGE)
    assert pkg_mod.CONFIRM_TOKEN == _OFFLINE_GATE_CONFIRM_TOKEN
    assert bridge_mod.CONFIRM_TOKEN == _OFFLINE_GATE_CONFIRM_TOKEN
    assert pkg_mod.CONFIRM_TOKEN == bridge_mod.CONFIRM_TOKEN


def test_public_rest_capture_script_uses_distinct_confirm_token_from_static_offline_gate() -> None:
    """One-shot public REST capture keeps its own token; do not conflate with offline package/bridge gate."""
    cap = next(REPO_ROOT.glob("scripts/ops/capture_public_rest_binance*_v0.py"))
    body = cap.read_text(encoding="utf-8")
    assert 'CONFIRM_TOKEN = "ALLOW_PUBLIC_REST_MARKET_DATA_ONE_SHOT_NO_AUTH_NO_ORDERS"' in body
    assert f'CONFIRM_TOKEN = "{_OFFLINE_GATE_CONFIRM_TOKEN}"' not in body


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
    assert _OBS_SUPERVISED_TIMED_SCRIPT.is_file()
    assert _OBS_FILE_SNAPSHOT_SCRIPT.is_file()
    p67_txt = _P67_SCHEDULER.read_text(encoding="utf-8").lower()
    assert "supervised" not in p67_txt


def test_offline_crosslink_shadow247_governance_charter_path_anchor_v0() -> None:
    """Path-only anchor; charter semantics are covered by test_shadow247_governance_charter_doc_contract_v0."""
    assert _CHARTER.is_file()


def test_offline_crosslink_charter_lists_this_contract_module_v0() -> None:
    """Symmetric traceability: charter already references this offline crosslink test."""
    body = _CHARTER.read_text(encoding="utf-8")
    assert "test_offline_crosslink_invariant_contract_v0.py" in body
    assert _OFFLINE_CROSSLINK_SELF.name in body


def test_offline_jobs_shadow247_scripts_resolve_v0() -> None:
    """Scheduler anchors for Paper/Shadow-247: on-disk scripts match wrapper TOML (static only)."""
    ops = tomllib.loads(_SHADOW247_WRAPPER_OPS_TOML.read_text(encoding="utf-8"))
    wrapper_script = ops["wrapper_script"]
    jobs = tomllib.loads(_JOBS_TOML.read_text(encoding="utf-8")).get("job", [])
    by_name = {j["name"]: j for j in jobs if isinstance(j, dict) and "name" in j}

    for name in _OFFLINE_SHADOW247_SCHEDULER_JOB_NAMES:
        assert name in by_name, f"missing scheduler job: {name!r}"

    pre = by_name["paper_shadow_247_paper_only_preflight_status_v0"]
    script_rel = pre["args"]["script"]
    assert (REPO_ROOT / script_rel).is_file()

    ph = by_name["shadow_247_futures_prestart_evidence_drycheck_placeholder_v0"]
    assert ph["args"]["script"] == wrapper_script
    assert (REPO_ROOT / ph["args"]["script"]).is_file()

    rt = by_name["paper_shadow_247_paper_only_runtime_high_vol_no_trade_v0"]
    ra = rt["args"]
    assert (REPO_ROOT / ra["script"]).is_file()
    assert (REPO_ROOT / ra["spec"]).is_file()


def test_offline_crosslink_stop_snapshot_contract_ids_v0() -> None:
    """Stable read-only anchors for operator stop snapshot (no runtime, no authority grant)."""
    body = _SNAPSHOT_OPERATOR_STOP_SCRIPT.read_text(encoding="utf-8")
    assert 'CONTRACT_ID = "operator_stop_signal_snapshot_v1"' in body
    assert "PT_STOP_KEYS" in body
    low = body.lower()
    assert "does not authorize live trading" in low


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
