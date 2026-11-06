"""Canonical Feature/Data Contract Layer v1 (UQ6 / R1).

Additive, fail-closed, non-activating. Not a second SSOT. Not trading authority.
"""

from __future__ import annotations

from src.features.canonical_feature_data_contract_layer_v1.catalog_v1 import (
    FEATURE_CATALOG,
    catalog_entry,
    require_complete_uq6_catalog,
)
from src.features.canonical_feature_data_contract_layer_v1.constants_v1 import (
    CAPABILITY_ID,
    CONTRACT_VERSION,
    PACKAGE_MARKER,
    REMEDIATION_ID,
)
from src.features.canonical_feature_data_contract_layer_v1.models_v1 import (
    ConsumerIntent,
    FeatureDataContractLayerError,
)
from src.features.canonical_feature_data_contract_layer_v1.selective_engine_v1 import (
    engine_status_v1,
    run_selective_engine_v1,
)
from src.features.canonical_feature_data_contract_layer_v1.verifier_v1 import (
    evaluate_r1_uq6_v1,
)

__all__ = [
    "CAPABILITY_ID",
    "CONTRACT_VERSION",
    "ConsumerIntent",
    "FEATURE_CATALOG",
    "FeatureDataContractLayerError",
    "PACKAGE_MARKER",
    "REMEDIATION_ID",
    "catalog_entry",
    "engine_status_v1",
    "evaluate_r1_uq6_v1",
    "require_complete_uq6_catalog",
    "run_selective_engine_v1",
]
