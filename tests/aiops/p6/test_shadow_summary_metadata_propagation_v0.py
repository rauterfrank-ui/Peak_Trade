from __future__ import annotations

import json
from pathlib import Path

from scripts.aiops.run_shadow_session import _shadow_session_summary_metadata_v0
from src.aiops.p6.session_schema import ShadowSessionSummary

REPO_ROOT = Path(__file__).resolve().parents[3]
HIGH_VOL_RUNNER_SPEC = (
    REPO_ROOT / "tests" / "fixtures" / "p6" / "shadow_session_high_vol_no_trade_runner_v0.json"
)


def test_summary_metadata_helper_copies_only_non_authorizing_allowlist() -> None:
    spec = {
        "scenario": "high_vol_no_trade",
        "profile": "high_vol_no_trade",
        "expected_decision": "NO_TRADE",
        "expected_regime": "VOL_EXTREME",
        "expected_fills": [],
        "expected_positions": {"BTC": 0.0},
        "activation_authorized": True,
        "live_authorized": True,
        "testnet_authorized": True,
        "broker_authorized": True,
        "decision": "NO_TRADE",
    }

    metadata = _shadow_session_summary_metadata_v0(spec)

    assert metadata == {
        "scenario": "high_vol_no_trade",
        "profile": "high_vol_no_trade",
        "expected_decision": "NO_TRADE",
        "expected_regime": "VOL_EXTREME",
        "expected_fills": [],
        "expected_positions": {"BTC": 0.0},
    }


def test_high_vol_runner_spec_metadata_is_summary_schema_native() -> None:
    spec = json.loads(HIGH_VOL_RUNNER_SPEC.read_text(encoding="utf-8"))
    metadata = _shadow_session_summary_metadata_v0(spec)

    summary = ShadowSessionSummary(
        **metadata,
        run_id="unit",
        asof_utc="",
        steps=[],
        outputs={},
        no_trade=True,
        notes=[],
        p7_outputs={},
        p7_account_summary={},
    )

    payload = summary.to_dict()

    assert payload["scenario"] == "high_vol_no_trade"
    assert payload["profile"] == "high_vol_no_trade"
    assert payload["expected_decision"] == "NO_TRADE"
    assert payload["expected_regime"] == "VOL_EXTREME"
    assert payload["expected_fills"] == []
    assert payload["expected_positions"] == {"BTC": 0.0}

    for forbidden in (
        "activation_authorized",
        "live_authorized",
        "testnet_authorized",
        "broker_authorized",
        "exchange_authorized",
        "order_submission_authorized",
    ):
        assert forbidden not in payload


def test_min_v1_p7_spec_does_not_add_metadata_keys_to_summary() -> None:
    spec_path = REPO_ROOT / "tests" / "fixtures" / "p6" / "shadow_session_min_v1_p7.json"
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    metadata = _shadow_session_summary_metadata_v0(spec)
    assert metadata == {}

    summary = ShadowSessionSummary(
        **metadata,
        run_id="unit",
        asof_utc="2026-02-11T14:00:00Z",
        steps=[],
        outputs={},
        no_trade=False,
        notes=["dry_run_only"],
        p7_outputs={},
        p7_account_summary={},
    )
    payload = summary.to_dict()
    for key in (
        "scenario",
        "profile",
        "expected_decision",
        "expected_regime",
        "expected_fills",
        "expected_positions",
    ):
        assert key not in payload
