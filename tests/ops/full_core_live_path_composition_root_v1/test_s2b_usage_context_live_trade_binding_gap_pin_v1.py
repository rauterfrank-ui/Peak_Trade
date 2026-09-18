"""S2B: Full-Core LIVE_TRADE binder ratification + binding-gap pin.

Owner-GO ratifies the governed Full-Core composition root as the binder of
DataUsageContextKind.LIVE_TRADE at the S2A boundary
(FreshPretradeGetTransportResultV1 immediately after transport.get, before
A1/A2/A3). Runtime binding is confined to the authorized seam module; this
pin still forbids DataSafetyGate join and foreign-vocab equivalence.

AUTHORITY_EFFECT=CONTEXT_BINDER_RATIFICATION_ONLY
RUNTIME_BINDING_AUTHORIZED_SEAM=datasafety_context_bind_from_fresh_pretrade_get_transport_result_v1.py
DATASAFETYGATE_JOIN=false
RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

import ast
import dataclasses
import re
from pathlib import Path

from src.data.safety import DataSafetyContext, DataSafetyGate, DataSourceKind, DataUsageContextKind
from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    CAPABILITY_ID,
    LIVE_ARMED,
    LIVE_ENABLED,
    OWNER,
    PRODUCTIVE_LIVE_NEXT_POINTER_AUTHORITY,
    WIRE_SEND_PERMITTED,
)
from src.ops.full_core_live_path_composition_root_v1.execution_admission_contract_v1 import (
    ADMISSION_CONTEXT_LIVE,
)
from src.ops.full_core_live_path_composition_root_v1.fresh_pretrade_runtime_get_v1 import (
    METHOD_GET,
    TRANSPORT_CLASS_INJECTED_TEST_DOUBLE,
    FreshPretradeGetTransportResultV1,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
_COMPOSITION_ROOT = REPO_ROOT / "src/ops/full_core_live_path_composition_root_v1"
_SRC_TRANSPORT = _COMPOSITION_ROOT / "productive_read_only_get_transport_v1.py"
_SRC_FRESH = _COMPOSITION_ROOT / "fresh_pretrade_runtime_get_v1.py"
_MASTER_RUNBOOK = REPO_ROOT / "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md"
_THIS_TEST = Path(__file__)

# Owner-ratified binder identity / boundary (contract expectation; not runtime wiring).
OWNER_RATIFIED_USAGE_BINDER = OWNER
OWNER_RATIFIED_USAGE_BINDER_CAPABILITY_ID = CAPABILITY_ID
OWNER_RATIFIED_BINDING_BOUNDARY_TYPE = "FreshPretradeGetTransportResultV1"
OWNER_RATIFIED_BINDING_BOUNDARY_MOMENT = "IMMEDIATELY_AFTER_TRANSPORT_GET_BEFORE_A1_A2_A3_UNWRAP"
OWNER_RATIFIED_USAGE_VALUE = DataUsageContextKind.LIVE_TRADE
OWNER_RATIFIED_AUTHORITY_EFFECT = "CONTEXT_BINDER_RATIFICATION_ONLY"
FAIL_CLOSED_UNBOUND_USAGE = "NO_DATASAFETYCONTEXT_FABRICATION_NO_LIVE_TRADE_FALLBACK"
AUTHORIZED_RUNTIME_BIND_RELPATH = (
    "src/ops/full_core_live_path_composition_root_v1/"
    "datasafety_context_bind_from_fresh_pretrade_get_transport_result_v1.py"
)


def _field_names(cls: type) -> set[str]:
    return {f.name for f in dataclasses.fields(cls)}


def _composition_root_py_files() -> list[Path]:
    return sorted(_COMPOSITION_ROOT.rglob("*.py"))


def test_live_trade_vocabulary_exists_unchanged() -> None:
    assert DataUsageContextKind.LIVE_TRADE.value == "live_trade"
    assert DataUsageContextKind.BACKTEST.value == "backtest"
    assert DataUsageContextKind.RESEARCH.value == "research"
    assert DataUsageContextKind.PAPER_TRADE.value == "paper_trade"
    assert {member.name for member in DataUsageContextKind} == {
        "BACKTEST",
        "RESEARCH",
        "PAPER_TRADE",
        "LIVE_TRADE",
    }


def test_full_core_productive_usage_previously_unbound_on_s2a_carrier() -> None:
    fields = _field_names(FreshPretradeGetTransportResultV1)
    assert "data_safety_source_kind" in fields
    assert "usage" not in fields
    assert "usage_context" not in fields
    assert "data_usage_context" not in fields
    result = FreshPretradeGetTransportResultV1(
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
    assert result.data_safety_source_kind is None
    assert getattr(result, "usage", None) is None
    assert getattr(result, "usage_context", None) is None


def test_owner_ratified_binder_identity_and_boundary_contract_expectation() -> None:
    assert OWNER_RATIFIED_USAGE_BINDER == "ops.full_core_live_path_composition_root_v1"
    assert OWNER_RATIFIED_USAGE_BINDER_CAPABILITY_ID == "FULL_CORE_LIVE_PATH_COMPOSITION_ROOT_V1"
    assert OWNER_RATIFIED_BINDING_BOUNDARY_TYPE == "FreshPretradeGetTransportResultV1"
    assert OWNER_RATIFIED_BINDING_BOUNDARY_MOMENT == (
        "IMMEDIATELY_AFTER_TRANSPORT_GET_BEFORE_A1_A2_A3_UNWRAP"
    )
    assert OWNER_RATIFIED_USAGE_VALUE is DataUsageContextKind.LIVE_TRADE
    assert OWNER_RATIFIED_AUTHORITY_EFFECT == "CONTEXT_BINDER_RATIFICATION_ONLY"
    assert PRODUCTIVE_LIVE_NEXT_POINTER_AUTHORITY == "full_core_live_path_authority_v1"
    # Runtime wiring of usage binding must not already exist on the carrier.
    assert "usage" not in _field_names(FreshPretradeGetTransportResultV1)


def test_live_trade_not_equivalent_to_admission_or_master_live() -> None:
    assert ADMISSION_CONTEXT_LIVE == "LIVE_ADMISSION"
    assert DataUsageContextKind.LIVE_TRADE.value != ADMISSION_CONTEXT_LIVE
    assert DataUsageContextKind.LIVE_TRADE.name != "LIVE_ADMISSION"
    runbook = _MASTER_RUNBOOK.read_text(encoding="utf-8")
    assert "SHADOW | INTERNAL_SIMULATED_EXECUTION | PAPER_EXCHANGE | TESTNET | LIVE" in runbook
    # Master mode token LIVE appears in the mode list; it is not the enum value.
    assert DataUsageContextKind.LIVE_TRADE.value != "LIVE"
    assert "DataUsageContextKind" not in runbook
    assert "live_trade" not in runbook


def test_no_derivation_from_standing_live_predicates_or_real_stamp() -> None:
    # Standing predicates may be true without implying LIVE_TRADE usage binding.
    assert LIVE_ENABLED is True
    assert LIVE_ARMED is True
    assert WIRE_SEND_PERMITTED is True
    stamped = FreshPretradeGetTransportResultV1(
        get_performed=True,
        method=METHOD_GET,
        endpoint="/api/v5/market/candles",
        http_status=200,
        payload={"code": "0", "data": []},
        auth_header_sent=False,
        transport_class=TRANSPORT_CLASS_INJECTED_TEST_DOUBLE,
        venue_live_contact=True,
        historical_reuse=False,
        error_class="",
        data_safety_source_kind=DataSourceKind.REAL.value,
    )
    assert stamped.data_safety_source_kind == DataSourceKind.REAL.value
    # Orthogonal: REAL stamp does not create a usage field or LIVE_TRADE claim.
    assert not hasattr(stamped, "usage")
    assert getattr(stamped, "usage_context", None) is None
    transport_src = _SRC_TRANSPORT.read_text(encoding="utf-8")
    fresh_src = _SRC_FRESH.read_text(encoding="utf-8")
    assert "DataUsageContextKind" not in transport_src
    assert "LIVE_TRADE" not in transport_src
    assert "DataUsageContextKind" not in fresh_src
    assert "LIVE_TRADE" not in fresh_src


def test_unbound_usage_fail_closed_no_silent_live_trade_fallback() -> None:
    assert FAIL_CLOSED_UNBOUND_USAGE == ("NO_DATASAFETYCONTEXT_FABRICATION_NO_LIVE_TRADE_FALLBACK")
    unbound = FreshPretradeGetTransportResultV1(
        get_performed=False,
        method=METHOD_GET,
        endpoint="/api/v5/market/candles",
        http_status=0,
        payload=None,
        auth_header_sent=False,
        transport_class=TRANSPORT_CLASS_INJECTED_TEST_DOUBLE,
        venue_live_contact=False,
        historical_reuse=False,
        error_class="UNBOUND",
    )
    assert unbound.data_safety_source_kind is None
    # No silent fabrication: carrier has no usage; None must not become LIVE_TRADE.
    claimed_usage = getattr(unbound, "usage_context", None)
    assert claimed_usage is None
    assert claimed_usage is not DataUsageContextKind.LIVE_TRADE
    # Contract: source_kind=None remains UNBOUND and must not synthesize REAL usage pairing.
    assert unbound.data_safety_source_kind is not DataSourceKind.REAL.value
    assert unbound.data_safety_source_kind is not DataSourceKind.REAL
    # Outside the authorized binder seam, no LIVE_TRADE assignment may appear.
    authorized = (REPO_ROOT / AUTHORIZED_RUNTIME_BIND_RELPATH).resolve()
    for path in _composition_root_py_files():
        if path.resolve() == authorized:
            continue
        text = path.read_text(encoding="utf-8")
        assert "DataUsageContextKind.LIVE_TRADE" not in text
        assert "usage_context=DataUsageContextKind.LIVE_TRADE" not in text


def test_real_plus_live_trade_gate_allowance_is_not_admission_authority() -> None:
    ctx = DataSafetyContext(
        source_kind=DataSourceKind.REAL,
        usage=DataUsageContextKind.LIVE_TRADE,
    )
    result = DataSafetyGate.check(ctx)
    assert result.allowed is True
    assert result.details is not None
    assert result.details["rule"] == "REAL_HISTORICAL_ALLOWED"
    # Gate allowance is not Full-Core admission / activation / POST authority.
    assert OWNER_RATIFIED_AUTHORITY_EFFECT == "CONTEXT_BINDER_RATIFICATION_ONLY"
    assert LIVE_ENABLED is True  # standing predicate, not usage binder activation


def test_s1_real_none_provenance_unchanged() -> None:
    transport_src = _SRC_TRANSPORT.read_text(encoding="utf-8")
    fresh_src = _SRC_FRESH.read_text(encoding="utf-8")
    assert transport_src.count("DataSourceKind.REAL.value") == 1
    assert "DataSourceKind.REAL.value if get_performed and venue_live_contact" in transport_src
    assert "VENUE_NATIVE_" not in transport_src
    assert "DataSourceKind.REAL" not in fresh_src
    assert fresh_src.count("data_safety_source_kind:") == 1
    assert "data_safety_source_kind=" not in fresh_src.split("data_safety_source_kind:")[1][:200]


def test_no_full_core_datasafetygate_join_and_usage_confined_to_authorized_seam() -> None:
    authorized = (REPO_ROOT / AUTHORIZED_RUNTIME_BIND_RELPATH).resolve()
    assert authorized.is_file()
    hits: list[str] = []
    gate_hits: list[str] = []
    for path in _composition_root_py_files():
        rel = str(path.relative_to(REPO_ROOT))
        text = path.read_text(encoding="utf-8")
        tree = ast.parse(text)
        for node in ast.walk(tree):
            if isinstance(node, ast.Name) and node.id == "DataSafetyGate":
                gate_hits.append(rel)
            if isinstance(node, ast.Attribute) and node.attr == "ensure_allowed":
                gate_hits.append(rel)
        if path.resolve() == authorized:
            continue
        if (
            "DataUsageContextKind" in text
            or re.search(r"\bLIVE_TRADE\b", text) is not None
            or "DataSafetyContext" in text
        ):
            hits.append(rel)
    transport_src = _SRC_TRANSPORT.read_text(encoding="utf-8")
    tree = ast.parse(transport_src)
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and (node.module or "").startswith("src.data.safety"):
            for alias in node.names:
                imported.add(alias.name)
    assert imported == {"DataSourceKind"}
    assert "DataUsageContextKind" not in transport_src
    assert not hits, f"usage/context wiring outside authorized seam: {hits}"
    assert not gate_hits, f"DataSafetyGate join present in composition root: {gate_hits}"


def test_pin_itself_does_not_wire_gate_join() -> None:
    pin_src = _THIS_TEST.read_text(encoding="utf-8")
    assert "DATASAFETYGATE_JOIN=false" in pin_src
    assert "OWNER_RATIFIED_USAGE_BINDER" in pin_src
    assert "NO_DATASAFETYCONTEXT_FABRICATION_NO_LIVE_TRADE_FALLBACK" in pin_src
    assert "AUTHORIZED_RUNTIME_BIND_RELPATH" in pin_src
    tree = ast.parse(pin_src)
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and node.attr == "ensure_allowed":
            raise AssertionError("pin must not call DataSafetyGate.ensure_allowed")
        if isinstance(node, ast.Name) and node.id == "ensure_allowed":
            raise AssertionError("pin must not reference ensure_allowed as a call target")
