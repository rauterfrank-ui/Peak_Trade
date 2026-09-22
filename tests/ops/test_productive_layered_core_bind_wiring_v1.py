"""Productive layered-core bind wiring: explicit store + scope-carrier gate."""

from __future__ import annotations

import inspect
from pathlib import Path

from src.ops.governed_productive_account_equity_authority_producer_v1 import (
    current_productive_fresh_runtime_from_persisted_cursor_to_pre_external_effect_applicability_v1 as from_cursor_mod,
)
from src.ops.governed_productive_account_equity_authority_producer_v1 import (
    current_productive_fresh_runtime_to_pre_external_effect_applicability_v1 as pre_ext_mod,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_sidestate_confirmation_cursor_v1 import (
    CURSOR_SCHEMA_NAME,
    CURSOR_SCHEMA_VERSION,
)
from src.ops.p5_10_productive_activation_and_binding_v1 import (
    PRODUCTIVE_CYCLE_LAYERED_CORE_BIND_ENABLED,
    incoming_cursor_has_existing_scope_carrier_v1,
    productive_layered_core_bind_cycle_kwargs_v1,
)
from src.ops.p5_10_productive_activation_and_binding_v1.productive_cycle_layered_core_bind_wiring_v1 import (
    LAYERED_CORE_STORE_ROOT_COLOCATED_WITH_CURSOR_OWNER,
)


def test_scope_carrier_detection_mapping_and_object() -> None:
    scope = object()
    assert incoming_cursor_has_existing_scope_carrier_v1(None) is False
    assert incoming_cursor_has_existing_scope_carrier_v1({"existing_scope": None}) is False
    valid_cursor = {
        "schema_name": CURSOR_SCHEMA_NAME,
        "schema_version": CURSOR_SCHEMA_VERSION,
        "existing_scope": {"instrument_id": "x"},
    }
    assert incoming_cursor_has_existing_scope_carrier_v1(valid_cursor) is True
    assert (
        incoming_cursor_has_existing_scope_carrier_v1(
            {**valid_cursor, "schema_name": "not-canonical"}
        )
        is False
    )
    assert (
        incoming_cursor_has_existing_scope_carrier_v1(type("C", (), {"existing_scope": scope})())
        is True
    )


def test_bind_kwargs_empty_without_store_or_scope(tmp_path: Path) -> None:
    assert PRODUCTIVE_CYCLE_LAYERED_CORE_BIND_ENABLED is True
    assert (
        productive_layered_core_bind_cycle_kwargs_v1(
            layered_core_store_root=None,
            incoming_cursor={"existing_scope": {"instrument_id": "x"}},
        )
        == {}
    )
    assert (
        productive_layered_core_bind_cycle_kwargs_v1(
            layered_core_store_root=tmp_path,
            incoming_cursor=None,
        )
        == {}
    )


def test_bind_kwargs_explicit_when_store_and_scope(tmp_path: Path) -> None:
    kwargs = productive_layered_core_bind_cycle_kwargs_v1(
        layered_core_store_root=tmp_path,
        incoming_cursor={
            "schema_name": CURSOR_SCHEMA_NAME,
            "schema_version": CURSOR_SCHEMA_VERSION,
            "existing_scope": {"instrument_id": "INST-A"},
        },
    )
    assert kwargs == {
        "productive_layered_core_bind_requested": True,
        "layered_core_store_root": tmp_path,
    }


def test_governed_productive_callers_wire_explicit_kwargs() -> None:
    for module in (pre_ext_mod, from_cursor_mod):
        source = inspect.getsource(module)
        assert "productive_layered_core_bind_cycle_kwargs_v1(" in source
        assert "layered_core_store_root=cursor_store_root" in source
        assert "run_p5_layered_core_authority_seam_v1" not in source


def test_store_root_owner_colocated_with_cursor() -> None:
    assert "sidestate_confirmation_cursor" in LAYERED_CORE_STORE_ROOT_COLOCATED_WITH_CURSOR_OWNER
