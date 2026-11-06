"""R1/UQ6 canonical Feature/Data Contract Layer v1 tests (offline, no-order)."""

from __future__ import annotations

import json

import pytest

from src.features.canonical_feature_data_contract_layer_v1.catalog_v1 import (
    FEATURE_CATALOG,
    catalog_entry,
    require_complete_uq6_catalog,
)
from src.features.canonical_feature_data_contract_layer_v1.constants_v1 import (
    CLASS_A_DECISION_SURFACES,
    CMC_FEATURE_ID,
    CONTRACT_CONFIG_REL_PATH,
    I25_FEATURE_ID,
    JUSTIFIED_PRODUCER_IDS,
    RESEARCH_FEEDER_IDS,
    UQ6_AFFECTED_FEATURE_IDS,
)
from src.features.canonical_feature_data_contract_layer_v1.lineage_v1 import (
    digest_mapping,
    load_layer_config_v1,
    repo_root,
)
from src.features.canonical_feature_data_contract_layer_v1.models_v1 import (
    AuthorityClass,
    ConsumerIntent,
    FeatureDataContractLayerError,
    ProducerStatus,
)
from src.features.canonical_feature_data_contract_layer_v1.producer_normalization_v1 import (
    normalize_justified_producer_v1,
)
from src.features.canonical_feature_data_contract_layer_v1.selective_engine_v1 import (
    engine_status_v1,
    run_selective_engine_v1,
)
from src.features.canonical_feature_data_contract_layer_v1.verifier_v1 import (
    evaluate_r1_uq6_v1,
    validate_layer_config_v1,
)
from src.trading.master_v2.canonical_market_context_v1 import FEATURE_CONTRACT_VERSION
from src.trading.master_v2.canonical_volatility_estimate_feature_contract_v1 import (
    compute_contract_digest_v1,
    load_contract_config_v1 as load_i25_config,
)


def test_layer_config_exists_and_matches_constants() -> None:
    payload = load_layer_config_v1()
    validate_layer_config_v1(payload)
    path = repo_root() / CONTRACT_CONFIG_REL_PATH
    disk = json.loads(path.read_text(encoding="utf-8"))
    assert digest_mapping(payload) == digest_mapping(disk)


def test_uq6_catalog_is_complete_and_research_feeders_have_no_core_rights() -> None:
    require_complete_uq6_catalog()
    assert frozenset(FEATURE_CATALOG) == frozenset(UQ6_AFFECTED_FEATURE_IDS)
    for feeder_id in RESEARCH_FEEDER_IDS:
        rights = catalog_entry(feeder_id).consumer_rights
        assert rights.core_decision is False
        assert rights.suitability is False
        assert rights.promotion is False
        assert rights.regime_classifier is False
        assert rights.dashboard_authority is False
        assert rights.execution_authority is False


def test_class_a_decision_surfaces_are_inventoried_not_engine_produced() -> None:
    assert len(CLASS_A_DECISION_SURFACES) == 13
    assert "Market Context" in CLASS_A_DECISION_SURFACES
    assert "Strategy Suitability Binding" in CLASS_A_DECISION_SURFACES
    for feature_id in FEATURE_CATALOG:
        assert catalog_entry(feature_id).equivalent_to_embedded_ta is False


def test_i25_is_justified_reuse_and_not_regime_authority() -> None:
    entry = catalog_entry(I25_FEATURE_ID)
    assert entry.producer_status.value == "JUSTIFIED_REUSE"
    assert entry.consumer_rights.core_decision is True
    assert entry.consumer_rights.regime_classifier is False
    record = normalize_justified_producer_v1(I25_FEATURE_ID)
    assert len(compute_contract_digest_v1(load_i25_config())) == 64
    assert record.producer_owner == entry.producer_owner
    assert len(record.payload_digest) == 64
    assert record.trading_authority is False
    assert record.runtime_effect is False
    assert record.activated is False


def test_cmc_pointer_reuses_existing_feature_contract_version() -> None:
    record = normalize_justified_producer_v1(CMC_FEATURE_ID)
    assert FEATURE_CONTRACT_VERSION == "canonical_market_context_feature_contract_v1"
    assert record.payload_digest
    assert record.trading_authority is False


def test_selective_engine_normalizes_justified_producers_only() -> None:
    status = engine_status_v1()
    assert status["activated"] is False
    assert status["productive_call_graph_hooked"] is False
    assert tuple(status["justified_producer_ids"]) == JUSTIFIED_PRODUCER_IDS
    for feature_id in JUSTIFIED_PRODUCER_IDS:
        record = run_selective_engine_v1(feature_id=feature_id, intent=ConsumerIntent.NORMALIZE)
        assert record.feature_id == feature_id
        assert record.freshness.max_age_enforcing is False
        assert record.freshness.max_age_role == "WATCHDOG_ONLY"
        assert record.freshness.can_block_canary is False
        assert record.freshness.productive_gate is False


@pytest.mark.parametrize(
    ("feature_id", "intent"),
    [
        (I25_FEATURE_ID, ConsumerIntent.CORE_DECISION),
        (I25_FEATURE_ID, ConsumerIntent.ACTIVATE_ENGINE),
        (I25_FEATURE_ID, ConsumerIntent.MAX_AGE_ENFORCE),
        (I25_FEATURE_ID, ConsumerIntent.SSOT_BYPASS),
        (I25_FEATURE_ID, ConsumerIntent.EXECUTION),
        ("I04_SENTIMENT_NEWS_ONCHAIN", ConsumerIntent.SUITABILITY),
        ("I04_SENTIMENT_NEWS_ONCHAIN", ConsumerIntent.NORMALIZE),
        ("I03_FEATURE_ENGINE_STAGED", ConsumerIntent.NORMALIZE),
        ("I07_MAX_AGE_DIAGNOSTIC", ConsumerIntent.MAX_AGE_ENFORCE),
        ("I55_MACRO_REGIMES", ConsumerIntent.CORE_DECISION),
        ("I76_PSYCHOLOGY_FEATURES", ConsumerIntent.PROMOTION),
        ("I38_WS_MARKET_STREAMS", ConsumerIntent.NORMALIZE),
    ],
)
def test_engine_fail_closed_on_forbidden_intents(feature_id: str, intent: ConsumerIntent) -> None:
    with pytest.raises(FeatureDataContractLayerError):
        run_selective_engine_v1(feature_id=feature_id, intent=intent)


def test_unknown_feature_id_fail_closed() -> None:
    with pytest.raises(FeatureDataContractLayerError, match="unknown_feature_id"):
        catalog_entry("I99_NOT_A_FEATURE")


def test_config_drift_fail_closed() -> None:
    payload = dict(load_layer_config_v1())
    payload["activated"] = True
    with pytest.raises(FeatureDataContractLayerError, match="activated"):
        validate_layer_config_v1(payload)
    payload = dict(load_layer_config_v1())
    payload["volatility_numeric_max_age_enforcing"] = True
    with pytest.raises(FeatureDataContractLayerError, match="volatility_numeric_max_age_enforcing"):
        validate_layer_config_v1(payload)
    payload = dict(load_layer_config_v1())
    payload["max_age_role"] = "PRODUCTIVE_GATE"
    with pytest.raises(FeatureDataContractLayerError, match="max_age_role"):
        validate_layer_config_v1(payload)
    payload = dict(load_layer_config_v1())
    payload["max_age_enforcement_enabled"] = True
    with pytest.raises(FeatureDataContractLayerError, match="max_age_enforcement_enabled"):
        validate_layer_config_v1(payload)
    payload = dict(load_layer_config_v1())
    payload["max_age_can_block_canary"] = True
    with pytest.raises(FeatureDataContractLayerError, match="max_age_can_block_canary"):
        validate_layer_config_v1(payload)
    payload = dict(load_layer_config_v1())
    payload["max_age_productive_gate"] = True
    with pytest.raises(FeatureDataContractLayerError, match="max_age_productive_gate"):
        validate_layer_config_v1(payload)


def test_i07_is_watchdog_only_not_a_productive_or_canary_gate() -> None:
    entry = catalog_entry("I07_MAX_AGE_DIAGNOSTIC")
    assert entry.authority_class is AuthorityClass.WATCHDOG_ONLY
    assert entry.producer_status is ProducerStatus.WATCHDOG_ONLY
    assert entry.freshness.max_age_role == "WATCHDOG_ONLY"
    assert entry.freshness.max_age_enforcing is False
    assert entry.freshness.can_block_trading is False
    assert entry.freshness.can_block_canary is False
    assert entry.freshness.can_change_selection is False
    assert entry.freshness.can_change_risk_decisions is False
    assert entry.freshness.can_change_execution is False
    assert entry.freshness.can_change_promotion is False
    assert entry.freshness.productive_gate is False
    assert "gate" not in entry.display_name.lower()


def test_evaluate_r1_uq6_pass_and_does_not_authorize_canary() -> None:
    claims = evaluate_r1_uq6_v1()
    assert claims["verdict"] == "PASS_R1_UQ6_FEATURE_DATA_CONTRACT_LAYER_V1"
    assert claims["eg_i03_classc_contracts_specified"] is True
    assert claims["ig_i03_engine_selective_inactive"] is True
    assert claims["canary_execute"] is False
    assert claims["live_authorized"] is False
    assert claims["order_effect"] is False
    assert claims["core_logic_change"] is False
    assert claims["runtime_effect"] is False
    assert claims["ssot_bypass"] is False
    assert claims["volatility_numeric_max_age_enforcing"] is False
    assert claims["max_age_role"] == "WATCHDOG_ONLY"
    assert claims["max_age_enforcement_enabled"] is False
    assert claims["max_age_can_block_canary"] is False
    assert claims["max_age_can_block_trading"] is False
    assert claims["max_age_can_change_selection"] is False
    assert claims["max_age_can_change_risk_decisions"] is False
    assert claims["max_age_can_change_execution"] is False
    assert claims["max_age_can_change_promotion"] is False
    assert claims["max_age_productive_gate"] is False
    assert claims["productive_caller_exists"] is False
