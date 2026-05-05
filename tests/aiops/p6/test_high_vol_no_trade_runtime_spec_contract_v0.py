"""Offline contract for high-vol / no-trade runtime spec fixtures (no runner execution)."""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
SHADOW_SPEC = REPO_ROOT / "tests" / "fixtures" / "p6" / "shadow_session_high_vol_no_trade_v0.json"
P4C_CAPSULE = REPO_ROOT / "tests" / "fixtures" / "p4c" / "capsule_high_vol_no_trade_v0.json"
P5A_INPUT = REPO_ROOT / "tests" / "fixtures" / "p5a" / "input_high_vol_no_trade_v0.json"
P7_SPEC = REPO_ROOT / "tests" / "fixtures" / "p7" / "paper_run_high_vol_no_trade_v0.json"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_high_vol_no_trade_shadow_spec_links_portable_inputs() -> None:
    spec = _load(SHADOW_SPEC)

    assert spec["schema_version"] == "p6.shadow_session_spec.v0"
    assert spec["scenario"] == "high_vol_no_trade"
    assert spec["profile"] == "high_vol_no_trade"
    assert spec["expected_decision"] == "NO_TRADE"
    assert spec["expected_regime"] == "VOL_EXTREME"
    assert spec["inputs"] == {
        "capsule_path": "tests/fixtures/p4c/capsule_high_vol_no_trade_v0.json",
        "p5a_input_path": "tests/fixtures/p5a/input_high_vol_no_trade_v0.json",
        "paper_run_spec_path": "tests/fixtures/p7/paper_run_high_vol_no_trade_v0.json",
    }


def test_high_vol_no_trade_runtime_spec_inputs_are_consistent() -> None:
    spec = _load(SHADOW_SPEC)
    capsule = _load(P4C_CAPSULE)
    p5a = _load(P5A_INPUT)
    p7 = _load(P7_SPEC)

    assert capsule["scenario"] == spec["scenario"] == p5a["scenario"] == p7["scenario"]
    assert capsule["decision"] == p5a["decision"] == p7["decision"] == "NO_TRADE"
    assert capsule["regime"] == p5a["regime"] == spec["expected_regime"] == "VOL_EXTREME"
    assert p5a["no_trade"] is True
    assert p5a["trade_allowed"] is False
    assert p5a["should_trade"] is False
    assert p7["schema_version"] == "p7.paper_run.v0"
    assert p7["orders"] == []
    assert p7["expected_fills"] == []
    assert p7["expected_positions"] == {"BTC": 0.0}


def test_high_vol_no_trade_runtime_spec_is_non_authorizing() -> None:
    payloads = [_load(SHADOW_SPEC), _load(P4C_CAPSULE), _load(P5A_INPUT), _load(P7_SPEC)]

    for payload in payloads:
        assert payload.get("activation_authorized") is False
        assert payload.get("testnet_authorized") is False
        assert payload.get("live_authorized") is False

    spec = _load(SHADOW_SPEC)
    p7 = _load(P7_SPEC)
    for payload in (spec, p7):
        assert payload["scheduler_authorized"] is False
        assert payload["daemon_authorized"] is False
        assert payload["broker_authorized"] is False
        assert payload["exchange_authorized"] is False
        assert payload["order_submission_authorized"] is False


def test_high_vol_no_trade_runtime_spec_paths_are_portable() -> None:
    for path in (SHADOW_SPEC, P4C_CAPSULE, P5A_INPUT, P7_SPEC):
        text = path.read_text(encoding="utf-8")
        assert "/Users/" not in text
        assert "/tmp/" not in text
        assert "api_key" not in text.lower()
        assert "secret" not in text.lower()


def test_high_vol_no_trade_runtime_spec_is_offline_contract_only() -> None:
    spec = _load(SHADOW_SPEC)
    p7 = _load(P7_SPEC)

    assert "offline_spec_contract_only" in spec["notes"]
    assert "does_not_run_shadow" in spec["notes"]
    assert "does_not_run_paper" in spec["notes"]
    assert "offline_spec_contract_only" in p7["notes"]
    assert "flat_account_expected" in p7["notes"]
