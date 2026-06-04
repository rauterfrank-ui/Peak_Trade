"""Static + offline bounded Futures Testnet contract (v0).

Docs/tests-only Class-4 scoped exception. No runtime, network, credentials, or Testnet start.
Review: futures_readiness_gap_review_after_spot_btc_eur_testnet_evidence_no_run_v0_20260604T122058Z
"""

from __future__ import annotations

from pathlib import Path

import pytest

from src.ops.bounded_futures_testnet_contract_v0 import (
    DEFAULT_INSTRUMENT,
    DEFAULT_SESSION_CLASS,
    FUTURES_SESSION_AUTHORIZED_NOW,
    PACKAGE_MARKER,
    REQUIRED_FUTURES_EVIDENCE_FIELD_NAMES,
    SPOT_KRAKEN_ENDPOINT_PREFIXES,
    default_bounded_futures_normal_v0_spec,
    evaluate_bounded_futures_testnet_evidence,
    spot_evidence_misclassified_as_futures,
)
from src.ops.bounded_testnet_order_cap_contract_v0 import (
    DEFAULT_SESSION_CLASS as SPOT_SESSION_CLASS,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
CONTRACT_MODULE = REPO_ROOT / "src" / "ops" / "bounded_futures_testnet_contract_v0.py"
SPOT_CONTRACT_MODULE = REPO_ROOT / "src" / "ops" / "bounded_testnet_order_cap_contract_v0.py"
SECTION5_GAP_OWNER_MAP = (
    REPO_ROOT / "docs" / "ops" / "planning" / "SECTION5_PREFLIGHT_GAP_OWNER_MAP_CONTRACT_V0.md"
)
FUTURES_TESTNET_PROOF_SPEC = (
    REPO_ROOT / "docs" / "ops" / "specs" / "FUTURES_TESTNET_DRY_RUN_PROOF_CONTRACT_V0.md"
)

TEST_PACKAGE_MARKER = "BOUNDED_FUTURES_TESTNET_CONTRACT_GUARD_V0=true"
_CLASS4_SCOPED_EXCEPTION_MARKER = "BOUNDED_FUTURES_TESTNET_GUARD_CLASS4_SCOPED_EXCEPTION_V0=true"
REVIEW_BUNDLE_SUFFIX = (
    "futures_readiness_gap_review_after_spot_btc_eur_testnet_evidence_no_run_v0_20260604T122058Z"
)


def _valid_futures_evidence() -> dict:
    return {
        "session_class": DEFAULT_SESSION_CLASS,
        "order_policy": "normal-testnet-futures-bounded",
        "instrument": DEFAULT_INSTRUMENT,
        "market_type": "futures",
        "margin_mode": "isolated",
        "max_leverage": 5.0,
        "leverage_within_cap": True,
        "position_mode": "one_way",
        "order_side_semantics": "long",
        "reduce_only_supported": True,
        "order_attempt_count": 0,
        "real_orders_created_count": 0,
        "cancel_or_close_attempt_count": 0,
        "order_notional_eur": 0.0,
        "order_notional_within_cap": True,
        "position_flattened_by_end": True,
        "cancel_or_close_evidence_valid": True,
        "futures_endpoint_isolation_pass": True,
        "spot_endpoint_isolation_pass": True,
        "funding_risk_acknowledged": True,
        "liquidation_risk_acknowledged": True,
        "risk_killswitch_scope_active": True,
        "risk_killswitch_scope_pass": True,
        "master_v2_double_play_authority_used": False,
        "endpoints_called": ["/futures/v3/openOrders"],
        "network_host": "https://futures.testnet.example",
        "scheduler_started": False,
        "runtime_started": False,
        "live_env_present": False,
        "futures_session_authorized_now": False,
    }


def test_package_marker_present() -> None:
    text = Path(__file__).read_text(encoding="utf-8")
    assert TEST_PACKAGE_MARKER in text
    assert _CLASS4_SCOPED_EXCEPTION_MARKER in text
    assert PACKAGE_MARKER in CONTRACT_MODULE.read_text(encoding="utf-8")


def test_futures_session_not_authorized_in_contract_module() -> None:
    assert FUTURES_SESSION_AUTHORIZED_NOW is False


def test_spot_and_futures_contract_modules_are_separate() -> None:
    assert SPOT_CONTRACT_MODULE.is_file()
    assert CONTRACT_MODULE.is_file()
    assert "bounded_futures_testnet_contract_v0" in CONTRACT_MODULE.name
    assert SPOT_SESSION_CLASS == "bounded-normal-testnet-v0"
    assert DEFAULT_SESSION_CLASS == "bounded-futures-normal-testnet-v0"
    assert DEFAULT_SESSION_CLASS != SPOT_SESSION_CLASS


def test_section5_and_futures_testnet_proof_spec_crosslinks_present() -> None:
    section5 = SECTION5_GAP_OWNER_MAP.read_text(encoding="utf-8")
    assert "bounded_futures_testnet_contract_v0" in section5
    assert FUTURES_TESTNET_PROOF_SPEC.is_file()


def test_spot_btc_eur_evidence_rejected_by_futures_evaluator() -> None:
    spot = {
        "session_class": "bounded-normal-testnet-v0",
        "instrument": "BTC/EUR",
        "market_type": "spot",
        "endpoints_called": ["/0/private/AddOrder"],
        "network_host": "https://api.kraken.com",
    }
    assert spot_evidence_misclassified_as_futures(spot)
    result = evaluate_bounded_futures_testnet_evidence(spot)
    assert result["bounded_futures_testnet_pass"] is False


def test_valid_futures_evidence_passes_evaluator() -> None:
    result = evaluate_bounded_futures_testnet_evidence(_valid_futures_evidence())
    assert result["bounded_futures_testnet_pass"] is True
    assert result["fail_reasons"] == []


def test_missing_margin_mode_fails() -> None:
    evidence = _valid_futures_evidence()
    del evidence["margin_mode"]
    result = evaluate_bounded_futures_testnet_evidence(evidence)
    assert result["bounded_futures_testnet_pass"] is False
    assert any("margin_mode" in r for r in result["fail_reasons"])


def test_spot_endpoint_in_endpoints_called_fails() -> None:
    evidence = _valid_futures_evidence()
    evidence["endpoints_called"] = list(SPOT_KRAKEN_ENDPOINT_PREFIXES)[:1]
    result = evaluate_bounded_futures_testnet_evidence(evidence)
    assert result["bounded_futures_testnet_pass"] is False


def test_master_v2_authority_used_fails() -> None:
    evidence = _valid_futures_evidence()
    evidence["master_v2_double_play_authority_used"] = True
    result = evaluate_bounded_futures_testnet_evidence(evidence)
    assert result["master_v2_boundary_pass"] is False
    assert result["bounded_futures_testnet_pass"] is False


def test_required_evidence_field_names_documented() -> None:
    assert len(REQUIRED_FUTURES_EVIDENCE_FIELD_NAMES) >= 20
    assert "futures_endpoint_isolation_pass" in REQUIRED_FUTURES_EVIDENCE_FIELD_NAMES


def test_default_spec_matches_review_instrument() -> None:
    spec = default_bounded_futures_normal_v0_spec()
    assert spec.instrument == "BTCUSDT"
    assert spec.max_leverage == 5.0
    assert spec.margin_mode == "isolated"


def test_closeout_review_bundle_suffix_documented_in_test() -> None:
    assert REVIEW_BUNDLE_SUFFIX in Path(__file__).read_text(encoding="utf-8")
