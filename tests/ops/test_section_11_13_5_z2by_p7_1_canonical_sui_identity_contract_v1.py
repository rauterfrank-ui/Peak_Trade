"""§11.13.5 P7.1 current-identity rebind fail-closed contract.

Validates the active SUI identity owner, equality gate, rejected SWAP/Demo
paths, SUI geometry without Exchange-algebra promotion, and unchanged
live/cover/authorization gates. Offline only. No venue access.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.ops.canonical_r6_s2_portfolio_risk_contracts_v1.constants_v1 import (
    MAX_POSITIONS_EFFECTIVE,
)
from src.ops.canonical_r6_s3_multi_future_runtime_architecture_v1.constants_v1 import (
    CANARY_AUTHORIZED,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.config_v1 import (
    example_incomplete_config_dict_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    CANARY_INSTRUMENT,
    CONFIRM_TOKEN_CANONICAL,
    DEFAULT_INST_FAMILY,
    DEFAULT_INSTRUMENT_ID,
    HISTORICAL_SUPERSEDED_CANONICAL_INSTRUMENT_ID,
    LIVE_ARMED,
    LIVE_AUTHORIZED,
    LIVE_ENABLED,
    POSITION_COUNT_LIMIT,
    SUBMIT_UNLOCKED,
    TESTNET_AUTHORIZED,
    LiveCanaryInstrumentBindingError,
    assert_live_canary_instrument_binding_v1,
    public_instruments_query_path_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.cover_usdc_fee_reserve_rates_rebind_get_path_v1 import (
    COVER_USDC_STATUS,
    SEALED_INST_FAMILY,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.position_value_fx_rounding_chain_v1 import (
    MULTI_FUTURE_AUTHORIZED,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.submit_transport_v1 import (
    LiveCanarySubmitTransportError,
    run_canary_submit_transport_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.xperp_310404_economic_baseline_contract_v1 import (
    live_eea_xperp_310404_economic_baseline_contract_v1,
)
from tests.ops.test_section_11_13_5_canary_submit_transport_v1 import (
    _assert_no_post,
    _transport_kwargs,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
EXAMPLE_CONFIG = (
    REPO_ROOT / "config" / "ops" / "section_11_13_5_live_canary_minimum_exposure_v1.example.json"
)
MASTER_RUNBOOK = REPO_ROOT / "docs" / "runbooks" / "canonical" / "PEAK_TRADE_MASTER_RUNBOOK.md"


def test_current_canonical_identity_is_sui_and_aliases_agree() -> None:
    assert DEFAULT_INSTRUMENT_ID == "SUI-USD_UM_XPERP-310404"
    assert CANARY_INSTRUMENT == DEFAULT_INSTRUMENT_ID
    assert DEFAULT_INST_FAMILY == "SUI-USD_UM_XPERP"
    assert SEALED_INST_FAMILY == DEFAULT_INST_FAMILY
    assert HISTORICAL_SUPERSEDED_CANONICAL_INSTRUMENT_ID == "BTC-USD_UM_XPERP-310404"
    assert_live_canary_instrument_binding_v1(instrument_id=DEFAULT_INSTRUMENT_ID)
    query = public_instruments_query_path_v1()
    assert DEFAULT_INSTRUMENT_ID in query
    assert "BTC-USD_UM_XPERP-310404" not in query


def test_empty_payload_instrument_id_falls_back_to_sui_default() -> None:
    kwargs = _transport_kwargs()
    kwargs["cfg"].payload["instrument_id"] = ""
    result = run_canary_submit_transport_v1(**kwargs)
    assert result["ok"] is True
    assert result["plan"]["instrument_id"] == DEFAULT_INSTRUMENT_ID


def test_nonempty_non_sui_payload_instrument_id_fails_closed() -> None:
    kwargs = _transport_kwargs()
    kwargs["cfg"].payload["instrument_id"] = "ETH-USD_UM_XPERP-999999"
    transport = kwargs["transport"]
    with pytest.raises(LiveCanarySubmitTransportError, match="INSTRUMENT_BINDING_MISMATCH"):
        run_canary_submit_transport_v1(**kwargs)
    _assert_no_post(transport)


def test_authorization_cover_and_cap_invariants_unchanged() -> None:
    assert LIVE_AUTHORIZED is False
    assert LIVE_ENABLED is False
    assert LIVE_ARMED is False
    assert TESTNET_AUTHORIZED is False
    assert CANARY_AUTHORIZED is False
    assert SUBMIT_UNLOCKED is False
    assert MULTI_FUTURE_AUTHORIZED is False
    assert MAX_POSITIONS_EFFECTIVE == 1
    assert POSITION_COUNT_LIMIT == 1
    assert COVER_USDC_STATUS == "UNINSTANTIATED"
    assert CONFIRM_TOKEN_CANONICAL == "I_KNOW_WHAT_I_AM_DOING"


def test_example_config_current_identity_is_sui_without_live_flags() -> None:
    payload = json.loads(EXAMPLE_CONFIG.read_text(encoding="utf-8"))
    assert payload["instrument_id"] == DEFAULT_INSTRUMENT_ID
    assert payload["inst_type"] == "FUTURES"
    assert payload["position_count_limit"] == 1
    incomplete = example_incomplete_config_dict_v1()
    assert incomplete["instrument_id"] == DEFAULT_INSTRUMENT_ID


def test_sui_geometry_is_not_promoted_to_exchange_algebra() -> None:
    contract = live_eea_xperp_310404_economic_baseline_contract_v1()
    assert contract["ctVal"] == "1"
    assert contract["ctValCcy"] == "SUI"
    assert contract["tickSz"] == "0.0001"
    assert contract["minSz"] == "1"
    assert contract["lotSz"] == "1"
    assert contract["ONE_CONTRACT_EQUALS_ONE_SUI"] is False
    assert contract["EXCHANGE_POSITION_VALUE_STATUS"] == "UNPROVEN"
    with pytest.raises(LiveCanaryInstrumentBindingError, match="INSTRUMENT_ID_REQUIRED"):
        assert_live_canary_instrument_binding_v1(instrument_id="")


def test_z2bx_composition_and_cover_status_remain_historical() -> None:
    text = MASTER_RUNBOOK.read_text(encoding="utf-8")
    z2bx_start = text.find("### 11.13.5.Z2BX Post-Z2BW P5 risk-envelope identity")
    z2by_start = text.find("### 11.13.5.Z2BY Post-Z2BX P7.1 canonical SUI identity rebind")
    z2bx = text[z2bx_start:z2by_start]
    z2by = text[z2by_start:]
    assert "RISK_ENVELOPE_IDENTITY_NUMERIC=0.01793372" in z2bx
    assert "COVER_USDC_STATUS=UNINSTANTIATED" in z2bx
    assert "USD_USDC_OPERATOR_STATUS=UNPROVEN" in z2by
    assert "RISK_ENVELOPE_IDENTITY_NUMERIC=0.01793372" in z2by
    assert "COVER_USDC_STATUS=UNINSTANTIATED" in z2by
