"""EG-ALT-CONSUMER I04/I05/I55 consumer-boundary tests (offline, no-order)."""

from __future__ import annotations

import json

import pytest

from src.features.canonical_alt_data_consumer_boundary_v1.constants_v1 import (
    CONTRACT_CONFIG_REL_PATH,
    MAX_AGE_ENFORCEMENT_ENABLED,
    MAX_AGE_ROLE,
    TARGET_BINDING,
)
from src.features.canonical_alt_data_consumer_boundary_v1.lineage_v1 import (
    digest_mapping,
    load_layer_config_v1,
    repo_root,
)
from src.features.canonical_alt_data_consumer_boundary_v1.matrix_v1 import (
    CONSUMER_MATRIX,
    primary_rows,
    require_consumer,
    require_producer,
    require_row,
    require_schema,
)
from src.features.canonical_alt_data_consumer_boundary_v1.models_v1 import (
    AltDataConsumerBoundaryError,
    PathClass,
)
from src.features.canonical_alt_data_consumer_boundary_v1.verifier_v1 import (
    evaluate_eg_alt_consumer_v1,
    validate_layer_config_v1,
)
from src.features.canonical_feature_data_contract_layer_v1.models_v1 import (
    ConsumerIntent,
    FeatureDataContractLayerError,
)
from src.features.canonical_feature_data_contract_layer_v1.selective_engine_v1 import (
    run_selective_engine_v1,
)
from src.features.canonical_feature_data_contract_layer_v1.verifier_v1 import (
    evaluate_r1_uq6_v1,
)
from src.regime.canonical_regime_meta_gated_selection_v1.verifier_v1 import (
    evaluate_r3_regime_meta_gated_selection_v1,
)
from src.strategies.canonical_strategy_registry_suitability_selection_v1.verifier_v1 import (
    evaluate_r2_registry_suitability_selection_v1,
)


def test_layer_config_exists_and_matches_constants() -> None:
    payload = load_layer_config_v1()
    validate_layer_config_v1(payload)
    path = repo_root() / CONTRACT_CONFIG_REL_PATH
    disk = json.loads(path.read_text(encoding="utf-8"))
    assert digest_mapping(payload) == digest_mapping(disk)


def test_primary_intents_are_keep_research_feeder_class_b() -> None:
    rows = primary_rows()
    assert [row.source_intent for row in rows] == ["I04", "I05", "I55"]
    for row in rows:
        assert row.path_class is PathClass.RESEARCH_FEEDER_VALID_NO_CANONICAL_CONSUMER_REQUIRED_YET
        assert row.recommended_target_binding == TARGET_BINDING
        assert row.missing_contract is False
        assert row.r2_suitability_consumer_present is False
        assert row.r3_meta_consumer_present is False
        assert row.promotion_consumer_present is False
        assert row.current_runtime_reachable is False
        assert row.current_authority_effect == "NONE"
        assert row.research_only is True
        assert row.r1_contract_compatible is True


def test_i05_adjacent_surfaces_are_not_shared_authority() -> None:
    venue = require_row("I05_VENUE_ORDERBOOK_API")
    kernel = require_row("I05_SAFETY_KERNEL_ORDERBOOK_GUARDS")
    bouchaud = require_row("I05_BOUCHAUD_OHLCV_PROXY")
    shadow = require_row("I05_SHADOW_TICK_NORMALIZER")
    assert venue.duplicate_path_risk == "DOCUMENTED_BOUNDARY_NOT_SHARED_AUTHORITY"
    assert kernel.consumer_class.value == "LEARNING_SAFETY_KERNEL_NOT_I05_FEATURE"
    assert bouchaud.consumer_class.value == "RESEARCH_STRATEGY_OHLCV_PROXY_NOT_I05_PRODUCER"
    assert shadow.consumer_class.value == "SHADOW_TICK_PARSE_NOT_I05_FEATURE"
    assert venue.current_authority_effect == "NONE"
    assert venue.r2_suitability_consumer_present is False


def test_i55_briefing_must_not_replace_r3_or_master() -> None:
    payload = load_layer_config_v1()
    assert payload["i55_replaces_r3"] is False
    assert payload["i55_replaces_master_v2"] is False
    assert payload["i55_replaces_double_play"] is False
    tilt = require_row("I55_BRIEFING_SIZING_TILT")
    assert tilt.current_consumer == "NONE_UNWIRED"
    assert tilt.consumer_class.value == "NON_AUTHORITY_BRIEFING_METADATA"


def test_unknown_producer_schema_consumer_fail_closed() -> None:
    with pytest.raises(AltDataConsumerBoundaryError, match="unknown_producer"):
        require_producer("not_a_producer")
    with pytest.raises(AltDataConsumerBoundaryError, match="unknown_schema"):
        require_schema("not_a_schema")
    with pytest.raises(AltDataConsumerBoundaryError, match="unknown_consumer"):
        require_consumer("not_a_consumer")
    with pytest.raises(AltDataConsumerBoundaryError, match="unknown_consumer_row"):
        require_row("NOT_A_ROW")


def test_research_feeders_cannot_enter_suitability_via_r1() -> None:
    for feature_id in (
        "I04_SENTIMENT_NEWS_ONCHAIN",
        "I05_ORDERBOOK_TICK",
        "I55_MACRO_REGIMES",
    ):
        with pytest.raises(FeatureDataContractLayerError):
            run_selective_engine_v1(feature_id=feature_id, intent=ConsumerIntent.SUITABILITY)
        with pytest.raises(FeatureDataContractLayerError):
            run_selective_engine_v1(feature_id=feature_id, intent=ConsumerIntent.EXECUTION)
        with pytest.raises(FeatureDataContractLayerError):
            run_selective_engine_v1(feature_id=feature_id, intent=ConsumerIntent.PROMOTION)


def test_config_activation_and_max_age_fail_closed() -> None:
    payload = dict(load_layer_config_v1())
    payload["activated"] = True
    with pytest.raises(AltDataConsumerBoundaryError, match="activated"):
        validate_layer_config_v1(payload)
    payload = dict(load_layer_config_v1())
    payload["consumer_wiring_present"] = True
    with pytest.raises(AltDataConsumerBoundaryError, match="consumer_wiring_present"):
        validate_layer_config_v1(payload)
    payload = dict(load_layer_config_v1())
    payload["max_age_role"] = "PRODUCTIVE_GATE"
    with pytest.raises(AltDataConsumerBoundaryError, match="max_age_role"):
        validate_layer_config_v1(payload)
    payload = dict(load_layer_config_v1())
    payload["max_age_enforcement_enabled"] = True
    with pytest.raises(AltDataConsumerBoundaryError, match="max_age_enforcement_enabled"):
        validate_layer_config_v1(payload)
    payload = dict(load_layer_config_v1())
    payload["i05_execution_authority"] = True
    with pytest.raises(AltDataConsumerBoundaryError, match="i05_execution_authority"):
        validate_layer_config_v1(payload)
    payload = dict(load_layer_config_v1())
    payload["direct_research_to_intent_path"] = True
    with pytest.raises(AltDataConsumerBoundaryError, match="direct_research_to_intent_path"):
        validate_layer_config_v1(payload)


def test_evaluate_pass_and_r1_r2_r3_remain_green() -> None:
    claims = evaluate_eg_alt_consumer_v1()
    assert claims["verdict"] == "PASS_EG_ALT_CONSUMER_BOUNDARY_V1"
    assert claims["eg_alt_consumer_status"] == "CLOSED_PROVEN_FORENSIC"
    assert claims["implementation_required"] is False
    assert claims["consumer_matrix_complete"] is True
    assert claims["path_class_all_primary"] == "B"
    assert claims["direct_research_to_intent_path"] is False
    assert claims["direct_research_to_order_path"] is False
    assert claims["second_feature_owner_risk"] == "NONE_R1_CATALOG_ONLY"
    assert claims["second_suitability_owner_risk"] == "NONE_R2_SUITABILITY_ONLY"
    assert claims["second_selection_owner_risk"] == "NONE_R2_SELECTION_ONLY"
    assert claims["second_regime_meta_owner_risk"] == "NONE_R3_GATE_ONLY"
    assert claims["llm_trading_authority"] == "PERMANENT_NON_AUTHORITY"
    assert claims["dashboard_authority"] is False
    assert claims["max_age_role"] == MAX_AGE_ROLE
    assert claims["max_age_enforcement_enabled"] is MAX_AGE_ENFORCEMENT_ENABLED
    assert claims["i05_execution_authority"] is False
    assert claims["i55_replaces_r3"] is False
    assert len(CONSUMER_MATRIX) == 8
    assert evaluate_r1_uq6_v1()["verdict"] == claims["r1_verdict"]
    assert evaluate_r2_registry_suitability_selection_v1()["verdict"] == claims["r2_verdict"]
    assert evaluate_r3_regime_meta_gated_selection_v1()["verdict"] == claims["r3_verdict"]
