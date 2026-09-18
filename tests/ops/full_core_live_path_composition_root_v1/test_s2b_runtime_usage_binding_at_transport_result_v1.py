"""S2B runtime: bind DataSafetyContext at FreshPretradeGetTransportResultV1.

Proves the Owner-ratified Full-Core binder composes
DataSafetyContext(source_kind, LIVE_TRADE) before A1/A2/A3, fail-closed on
unbound stamps, without DataSafetyGate join or foreign-vocab inference.

AUTHORITY_EFFECT=RATIFIED_CONTEXT_BINDER_IMPLEMENTATION_ONLY
DATASAFETYGATE_JOIN=false
RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

import ast
import dataclasses
import inspect
from pathlib import Path

from src.data.safety import DataSafetyContext, DataSourceKind, DataUsageContextKind
from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    LIVE_ARMED,
    LIVE_ENABLED,
    OWNER,
    WIRE_SEND_PERMITTED,
)
from src.ops.full_core_live_path_composition_root_v1.datasafety_context_bind_from_fresh_pretrade_get_transport_result_v1 import (
    BINDING_BOUNDARY_MOMENT,
    BINDING_BOUNDARY_TYPE,
    BOUND_USAGE,
    DISPOSITION_BOUND,
    DISPOSITION_UNBOUND_FAIL_CLOSED,
    REASON_SOURCE_KIND_NOT_EXACT_REAL,
    REASON_SOURCE_KIND_UNBOUND,
    bind_full_core_datasafety_context_from_fresh_pretrade_get_transport_result_v1,
)
from src.ops.full_core_live_path_composition_root_v1.execution_admission_contract_v1 import (
    ADMISSION_CONTEXT_LIVE,
)
from src.ops.full_core_live_path_composition_root_v1.fresh_pretrade_runtime_get_v1 import (
    METHOD_GET,
    TRANSPORT_CLASS_INJECTED_TEST_DOUBLE,
    TRANSPORT_CLASS_PRODUCTIVE_READ_ONLY_GET,
    FreshPretradeGetItemEvidenceV1,
    FreshPretradeGetTransportResultV1,
)
from src.ops.full_core_live_path_composition_root_v1.productive_read_only_get_transport_v1 import (
    FullCoreProductiveReadOnlyGetTransportV1,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
_BIND_SRC = (
    REPO_ROOT
    / "src/ops/full_core_live_path_composition_root_v1"
    / "datasafety_context_bind_from_fresh_pretrade_get_transport_result_v1.py"
)
_TRANSPORT_SRC = (
    REPO_ROOT
    / "src/ops/full_core_live_path_composition_root_v1"
    / "productive_read_only_get_transport_v1.py"
)
_FRESH_SRC = (
    REPO_ROOT / "src/ops/full_core_live_path_composition_root_v1/fresh_pretrade_runtime_get_v1.py"
)
_V5_SRC = (
    REPO_ROOT
    / "src/ops/governed_productive_account_equity_authority_producer_v1"
    / "current_productive_one_runtime_cycle_after_new_finalized_1m_c1_observation_v5.py"
)


def _carrier(
    *,
    data_safety_source_kind: str | None,
    transport_class: str = TRANSPORT_CLASS_PRODUCTIVE_READ_ONLY_GET,
    venue_live_contact: bool = True,
    get_performed: bool = True,
) -> FreshPretradeGetTransportResultV1:
    return FreshPretradeGetTransportResultV1(
        get_performed=get_performed,
        method=METHOD_GET,
        endpoint="/api/v5/market/candles",
        http_status=200 if get_performed else 0,
        payload={"code": "0", "data": []} if get_performed else None,
        auth_header_sent=False,
        transport_class=transport_class,
        venue_live_contact=venue_live_contact,
        historical_reuse=False,
        error_class="" if get_performed else "UNBOUND",
        data_safety_source_kind=data_safety_source_kind,
    )


def test_real_stamped_result_binds_datasafety_context_live_trade() -> None:
    result = _carrier(data_safety_source_kind=DataSourceKind.REAL.value)
    bound = bind_full_core_datasafety_context_from_fresh_pretrade_get_transport_result_v1(result)
    assert bound.disposition == DISPOSITION_BOUND
    assert bound.context == DataSafetyContext(
        source_kind=DataSourceKind.REAL,
        usage=DataUsageContextKind.LIVE_TRADE,
    )
    assert bound.binder_owner == OWNER
    assert bound.binding_boundary_type == BINDING_BOUNDARY_TYPE
    assert bound.binding_boundary_moment == BINDING_BOUNDARY_MOMENT
    assert bound.datasafetygate_join is False
    assert BOUND_USAGE is DataUsageContextKind.LIVE_TRADE


def test_none_stamped_result_fail_closed_no_context() -> None:
    result = _carrier(
        data_safety_source_kind=None,
        transport_class=TRANSPORT_CLASS_INJECTED_TEST_DOUBLE,
        venue_live_contact=False,
        get_performed=False,
    )
    bound = bind_full_core_datasafety_context_from_fresh_pretrade_get_transport_result_v1(result)
    assert bound.disposition == DISPOSITION_UNBOUND_FAIL_CLOSED
    assert bound.context is None
    assert bound.reason_code == REASON_SOURCE_KIND_UNBOUND


def test_injected_default_cannot_inherit_real() -> None:
    omitted = FreshPretradeGetTransportResultV1(
        get_performed=True,
        method=METHOD_GET,
        endpoint="/api/v5/market/candles",
        http_status=200,
        payload={"code": "0", "data": []},
        auth_header_sent=False,
        transport_class=TRANSPORT_CLASS_INJECTED_TEST_DOUBLE,
        venue_live_contact=False,
        historical_reuse=False,
        error_class="",
    )
    assert omitted.data_safety_source_kind is None
    bound = bind_full_core_datasafety_context_from_fresh_pretrade_get_transport_result_v1(omitted)
    assert bound.context is None
    assert bound.disposition == DISPOSITION_UNBOUND_FAIL_CLOSED


def test_live_trade_not_inferred_from_foreign_live_predicates_or_non_exact_stamp() -> None:
    assert LIVE_ENABLED is True
    assert LIVE_ARMED is True
    assert WIRE_SEND_PERMITTED is True
    assert ADMISSION_CONTEXT_LIVE == "LIVE_ADMISSION"
    # Standing predicates true + non-REAL stamp must not bind LIVE_TRADE context.
    foreign = _carrier(data_safety_source_kind="LIVE_ADMISSION")
    bound = bind_full_core_datasafety_context_from_fresh_pretrade_get_transport_result_v1(foreign)
    assert bound.context is None
    assert bound.reason_code == REASON_SOURCE_KIND_NOT_EXACT_REAL
    historical = _carrier(data_safety_source_kind=DataSourceKind.HISTORICAL.value)
    bound_hist = bind_full_core_datasafety_context_from_fresh_pretrade_get_transport_result_v1(
        historical
    )
    assert bound_hist.context is None
    assert bound_hist.reason_code == REASON_SOURCE_KIND_NOT_EXACT_REAL
    # Binder AST must not reference standing predicates or admission tokens.
    tree = ast.parse(_BIND_SRC.read_text(encoding="utf-8"))
    forbidden = {
        "LIVE_ENABLED",
        "LIVE_ARMED",
        "WIRE_SEND_PERMITTED",
        "ADMISSION_CONTEXT_LIVE",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and node.id in forbidden:
            raise AssertionError(f"binder references foreign live token: {node.id}")


def test_binding_occurs_before_a1_a2_a3_on_transport_result_carrier() -> None:
    result = _carrier(data_safety_source_kind=DataSourceKind.REAL.value)
    # Binding consumes the transport result carrier itself (pre-unwrap).
    bound = bind_full_core_datasafety_context_from_fresh_pretrade_get_transport_result_v1(result)
    assert bound.disposition == DISPOSITION_BOUND
    assert "data_safety_source_kind" in {f.name for f in dataclasses.fields(type(result))}
    # A1: ItemEvidence has no stamp field — binding cannot depend on it.
    assert "data_safety_source_kind" not in {
        f.name for f in dataclasses.fields(FreshPretradeGetItemEvidenceV1)
    }
    # A2/A3 loss surfaces remain payload-only; binder takes the typed result, not payload.
    sig = inspect.signature(
        bind_full_core_datasafety_context_from_fresh_pretrade_get_transport_result_v1
    )
    assert list(sig.parameters) == ["result"]
    annotation = sig.parameters["result"].annotation
    assert annotation in {FreshPretradeGetTransportResultV1, "FreshPretradeGetTransportResultV1"}
    v5_src = _V5_SRC.read_text(encoding="utf-8")
    assert 'return result.payload, ""' in v5_src or "return result.payload, ''" in v5_src
    transport_src = _TRANSPORT_SRC.read_text(encoding="utf-8")
    assert "self.payloads_by_path[path_only] = payload" in transport_src


def test_s1_source_provenance_unchanged() -> None:
    transport_src = _TRANSPORT_SRC.read_text(encoding="utf-8")
    fresh_src = _FRESH_SRC.read_text(encoding="utf-8")
    bind_src = _BIND_SRC.read_text(encoding="utf-8")
    assert transport_src.count("DataSourceKind.REAL.value") == 1
    assert "DataSourceKind.REAL.value if get_performed and venue_live_contact" in transport_src
    assert "VENUE_NATIVE_" not in transport_src
    assert "VENUE_NATIVE_" not in bind_src
    assert "DataSourceKind.REAL" not in fresh_src
    # Binder parses exact REAL.value; does not assign REAL onto transport results.
    assert "data_safety_source_kind=" not in bind_src
    assert FullCoreProductiveReadOnlyGetTransportV1.__name__ == (
        "FullCoreProductiveReadOnlyGetTransportV1"
    )


def test_no_datasafetygate_invocation_in_binder() -> None:
    tree = ast.parse(_BIND_SRC.read_text(encoding="utf-8"))
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and (node.module or "").startswith("src.data.safety"):
            for alias in node.names:
                imported.add(alias.name)
        if isinstance(node, ast.Attribute) and node.attr in {"check", "ensure_allowed"}:
            raise AssertionError(f"binder must not call DataSafetyGate.{node.attr}")
        if isinstance(node, ast.Name) and node.id == "DataSafetyGate":
            raise AssertionError("binder must not reference DataSafetyGate")
    assert imported == {"DataSafetyContext", "DataSourceKind", "DataUsageContextKind"}
