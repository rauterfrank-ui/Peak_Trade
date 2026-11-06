"""Selective producer normalization — reuse existing owners, do not recompute.

Justified producers: I25 volatility contract (digest reuse) and CMC feature
contract version pointer. Does not materialize volatility or rebuild CMC.
"""

from __future__ import annotations

from typing import Any, Mapping

from src.features.canonical_feature_data_contract_layer_v1.catalog_v1 import catalog_entry
from src.features.canonical_feature_data_contract_layer_v1.constants_v1 import (
    ACTIVATED,
    CMC_FEATURE_CONTRACT_VERSION,
    CMC_FEATURE_ID,
    I25_FEATURE_ID,
    JUSTIFIED_PRODUCER_IDS,
    RUNTIME_EFFECT,
)
from src.features.canonical_feature_data_contract_layer_v1.lineage_v1 import (
    digest_mapping,
    lineage_sha256,
)
from src.features.canonical_feature_data_contract_layer_v1.models_v1 import (
    FeatureContractRecordV1,
    FeatureDataContractLayerError,
)


def _reject(message: str) -> None:
    raise FeatureDataContractLayerError(message)


def _record_from_payload(*, feature_id: str, payload: Mapping[str, Any]) -> FeatureContractRecordV1:
    entry = catalog_entry(feature_id)
    payload_digest = digest_mapping(payload)
    lineage = lineage_sha256(
        feature_id=feature_id,
        schema_id=entry.schema_id,
        payload_digest=payload_digest,
    )
    return FeatureContractRecordV1(
        feature_id=feature_id,
        schema_id=entry.schema_id,
        producer_owner=entry.producer_owner,
        authority_class=entry.authority_class,
        producer_status=entry.producer_status,
        consumer_rights=entry.consumer_rights,
        freshness=entry.freshness,
        lineage_sha256=lineage,
        payload_digest=payload_digest,
        runtime_effect=RUNTIME_EFFECT,
        activated=ACTIVATED,
        trading_authority=False,
    )


def normalize_i25_volatility_contract_v1() -> FeatureContractRecordV1:
    from src.trading.master_v2.canonical_volatility_estimate_feature_contract_v1 import (
        CONTRACT_OWNER as i25_module_owner,
        compute_contract_digest_v1,
        load_contract_config_v1,
        load_ratified_contract_v1,
    )

    ratified = load_ratified_contract_v1()
    config = load_contract_config_v1()
    if config.get("runtime_effect") is not False:
        _reject("i25_runtime_effect_not_false")
    if config.get("authority_effect") != "NONE":
        _reject("i25_authority_effect_not_none")
    if ratified.feature_name != "volatility_estimate":
        _reject("i25_feature_name_mismatch")
    digest = compute_contract_digest_v1(config)
    payload = {
        "contract_digest": digest,
        "contract_version": ratified.contract_version,
        "feature_name": ratified.feature_name,
        "owner": i25_module_owner,
        "recomputed": False,
        "reuse": True,
    }
    record = _record_from_payload(feature_id=I25_FEATURE_ID, payload=payload)
    if record.consumer_rights.regime_classifier:
        _reject("i25_must_not_be_regime_classifier_authority")
    return record


def normalize_cmc_feature_contract_pointer_v1() -> FeatureContractRecordV1:
    from src.trading.master_v2.canonical_market_context_v1 import FEATURE_CONTRACT_VERSION

    if FEATURE_CONTRACT_VERSION != CMC_FEATURE_CONTRACT_VERSION:
        _reject(
            "cmc_feature_contract_version_mismatch:"
            f"expected={CMC_FEATURE_CONTRACT_VERSION}:actual={FEATURE_CONTRACT_VERSION}"
        )
    payload = {
        "feature_contract_version": FEATURE_CONTRACT_VERSION,
        "rebuild_cmc": False,
        "reuse_pointer_only": True,
    }
    return _record_from_payload(feature_id=CMC_FEATURE_ID, payload=payload)


def normalize_justified_producer_v1(feature_id: str) -> FeatureContractRecordV1:
    if feature_id not in JUSTIFIED_PRODUCER_IDS:
        _reject(f"producer_not_justified_for_normalization:{feature_id}")
    if feature_id == I25_FEATURE_ID:
        return normalize_i25_volatility_contract_v1()
    if feature_id == CMC_FEATURE_ID:
        return normalize_cmc_feature_contract_pointer_v1()
    _reject(f"producer_not_justified_for_normalization:{feature_id}")
    raise AssertionError("unreachable")
