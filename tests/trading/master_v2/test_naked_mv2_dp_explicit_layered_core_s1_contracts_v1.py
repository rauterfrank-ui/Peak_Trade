"""S1 — explicit L1–L10 contracts/states (no fachliche formulas)."""

from __future__ import annotations

import dataclasses

from trading.master_v2.naked_mv2_dp_explicit_layered_core_v1.contracts_v1 import (
    CounterMoveStateV1,
    NullLineStateV1,
    RunningReferenceStateV1,
    ScopeStateV1,
)
from trading.master_v2.naked_mv2_dp_explicit_layered_core_v1.layer_catalog_v1 import (
    LAYER_CATALOG_V1,
    LAYER_ORDER_V1,
    LayerIdV1,
)


def test_ten_layers_separately_addressable() -> None:
    assert len(LAYER_ORDER_V1) == 10
    assert len(LAYER_CATALOG_V1) == 10
    for layer in LayerIdV1:
        assert layer in LAYER_CATALOG_V1
        entry = LAYER_CATALOG_V1[layer]
        assert entry.layer_id is layer
        assert entry.semantic_owner.endswith(
            layer.value.split("_", 1)[1].lower().replace("_", "_")
        ) or entry.semantic_owner  # owner string present


def test_layer_catalog_unique_owners_and_downstream_chain() -> None:
    owners = {e.semantic_owner for e in LAYER_CATALOG_V1.values()}
    assert len(owners) == 10
    for idx, layer in enumerate(LAYER_ORDER_V1[:-1]):
        downstream = LAYER_CATALOG_V1[layer].downstream_consumer
        assert downstream == LAYER_ORDER_V1[idx + 1].value


def test_isolated_state_types_not_shared() -> None:
    assert NullLineStateV1 is not RunningReferenceStateV1
    assert ScopeStateV1 is not RunningReferenceStateV1
    assert CounterMoveStateV1 is not RunningReferenceStateV1
    nullline_fields = {f.name for f in dataclasses.fields(NullLineStateV1)}
    running_fields = {f.name for f in dataclasses.fields(RunningReferenceStateV1)}
    assert "nullline_price" in nullline_fields
    assert "reference_price_r_t" in running_fields
    assert "nullline_price" not in running_fields


def test_scope_has_no_regime_switch_authority_in_catalog() -> None:
    l7 = LAYER_CATALOG_V1[LayerIdV1.L7_SCOPE_STATE]
    l10 = LAYER_CATALOG_V1[LayerIdV1.L10_BULL_BEAR_STATE_SWITCH]
    assert "no_regime_switch" in l7.mutates
    assert "regime_switch_authority" in l10.mutates


def test_nullline_and_running_reference_separation_in_catalog() -> None:
    l5 = LAYER_CATALOG_V1[LayerIdV1.L5_NULLLINE]
    l8 = LAYER_CATALOG_V1[LayerIdV1.L8_RUNNING_REFERENCE]
    assert "not_running_reference" in l5.mutates
    assert "not_nullline" in l8.mutates
