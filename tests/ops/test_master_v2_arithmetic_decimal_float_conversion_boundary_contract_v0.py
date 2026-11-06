"""Static fail-closed contract: Master V2 Decimal/float conversion boundary v0.

Documents mandatory preconditions before any future Master-V2-to-futures-accounting kernel
wiring. Master V2 and Double Play currently use float-based values; the canonical futures
accounting kernel uses Decimal. ``_to_decimal()`` normalizes certain kernel inputs but does
not constitute a complete Master-V2 seam conversion contract.

Non-authorizing. No runtime, network, testnet execution, conversion implementation, or
kernel wiring.
"""

from __future__ import annotations

import ast
import importlib
import inspect
from decimal import Decimal
from pathlib import Path
from typing import Final, Literal, TypedDict

from src.execution.ledger.quantization import d as strict_decimal_d

REPO_ROOT = Path(__file__).resolve().parents[2]

PACKAGE_MARKER = "MASTER_V2_ARITHMETIC_DECIMAL_FLOAT_CONVERSION_BOUNDARY_CONTRACT_V0=true"
AUTHORITY_LIFT = False

CANONICAL_FUTURES_KERNEL_OWNER = "src/execution/paper/futures_accounting.py"
STRICT_DECIMAL_QUANTIZATION_OWNER = "src/execution/ledger/quantization.py"
MASTER_V2_CAPITAL_SLOT_FLOAT_OWNER = "src/trading/master_v2/double_play_capital_slot.py"
MASTER_V2_REPLAY_FLOAT_OWNER = "src/trading/master_v2/offline_double_play_scenario_replay_v0.py"
FUTURE_KERNEL_WIRING_REQUIRES_EXPLICIT_CONVERSION_CONTRACT = True

OwnerRole = Literal[
    "MASTER_V2_FLOAT_SOURCE",
    "FUTURES_ACCOUNTING_DECIMAL_TARGET",
    "STRICT_DECIMAL_QUANTIZATION_OWNER",
    "VENUE_PRECISION_OWNER",
    "VALUE_TRANSPORT_ONLY",
    "CONVERSION_BOUNDARY",
    "UNIT_BOUNDARY",
    "SIGN_BOUNDARY",
    "ROUNDING_BOUNDARY",
    "MASTER_V2_ARITHMETIC_BINDING",
]

_BINDING_ROLES: Final[frozenset[str]] = frozenset({"MASTER_V2_ARITHMETIC_BINDING"})

_VALID_OWNER_ROLES: Final[frozenset[str]] = frozenset(
    {
        "MASTER_V2_FLOAT_SOURCE",
        "FUTURES_ACCOUNTING_DECIMAL_TARGET",
        "STRICT_DECIMAL_QUANTIZATION_OWNER",
        "VENUE_PRECISION_OWNER",
        "VALUE_TRANSPORT_ONLY",
        "CONVERSION_BOUNDARY",
        "UNIT_BOUNDARY",
        "SIGN_BOUNDARY",
        "ROUNDING_BOUNDARY",
    }
)

UnitKind = Literal[
    "price",
    "quantity",
    "contracts",
    "base_asset",
    "quote_asset",
    "quote_notional",
    "percent",
    "basis_points",
    "fee_rate",
    "funding_rate",
    "pnl",
    "equity",
    "margin",
]

SignConvention = Literal[
    "long_short_quantity",
    "realized_pnl",
    "unrealized_pnl",
    "fee_as_charge",
    "funding_payment_or_receipt",
    "adverse_slippage",
    "drawdown_loss",
    "nonnegative_magnitude",
    "signed_delta",
]


class ConversionOwnerRecord(TypedDict):
    path: str
    role: OwnerRole
    number_type: str
    rejects_float: bool
    fail_closed: bool


CONVERSION_OWNER_REGISTRY: tuple[ConversionOwnerRecord, ...] = (
    {
        "path": MASTER_V2_CAPITAL_SLOT_FLOAT_OWNER,
        "role": "MASTER_V2_FLOAT_SOURCE",
        "number_type": "float",
        "rejects_float": False,
        "fail_closed": True,
    },
    {
        "path": MASTER_V2_REPLAY_FLOAT_OWNER,
        "role": "MASTER_V2_FLOAT_SOURCE",
        "number_type": "float",
        "rejects_float": False,
        "fail_closed": True,
    },
    {
        "path": CANONICAL_FUTURES_KERNEL_OWNER,
        "role": "FUTURES_ACCOUNTING_DECIMAL_TARGET",
        "number_type": "Decimal",
        "rejects_float": False,
        "fail_closed": True,
    },
    {
        "path": STRICT_DECIMAL_QUANTIZATION_OWNER,
        "role": "STRICT_DECIMAL_QUANTIZATION_OWNER",
        "number_type": "Decimal",
        "rejects_float": True,
        "fail_closed": True,
    },
)


class ValueBoundaryRecord(TypedDict):
    field_name: str
    source: str
    target: str
    current_unit: UnitKind
    expected_target_unit: UnitKind
    current_number_type: str
    expected_target_number_type: str
    sign_convention: SignConvention
    rounding_or_quantization: str
    tick_lot_dependent: bool
    nan_inf_overflow_policy: str
    canonical_owner: str
    proof_status: str


VALUE_BOUNDARY_MATRIX: tuple[ValueBoundaryRecord, ...] = (
    {
        "field_name": "price",
        "source": MASTER_V2_REPLAY_FLOAT_OWNER,
        "target": CANONICAL_FUTURES_KERNEL_OWNER,
        "current_unit": "price",
        "expected_target_unit": "price",
        "current_number_type": "float",
        "expected_target_number_type": "Decimal",
        "sign_convention": "nonnegative_magnitude",
        "rounding_or_quantization": "explicit tick quantize required before kernel bind",
        "tick_lot_dependent": True,
        "nan_inf_overflow_policy": "fail_closed; replay rejects NaN price",
        "canonical_owner": CANONICAL_FUTURES_KERNEL_OWNER,
        "proof_status": "UNWIRED_CONVERSION_CONTRACT_REQUIRED",
    },
    {
        "field_name": "mark_price",
        "source": MASTER_V2_REPLAY_FLOAT_OWNER,
        "target": CANONICAL_FUTURES_KERNEL_OWNER,
        "current_unit": "price",
        "expected_target_unit": "price",
        "current_number_type": "float",
        "expected_target_number_type": "Decimal",
        "sign_convention": "nonnegative_magnitude",
        "rounding_or_quantization": "_to_decimal normalizes only; not tick contract",
        "tick_lot_dependent": True,
        "nan_inf_overflow_policy": "fail_closed via _to_decimal is_finite",
        "canonical_owner": CANONICAL_FUTURES_KERNEL_OWNER,
        "proof_status": "PARTIAL_TO_DECIMAL_ONLY",
    },
    {
        "field_name": "entry_price",
        "source": MASTER_V2_REPLAY_FLOAT_OWNER,
        "target": CANONICAL_FUTURES_KERNEL_OWNER,
        "current_unit": "price",
        "expected_target_unit": "price",
        "current_number_type": "float",
        "expected_target_number_type": "Decimal",
        "sign_convention": "nonnegative_magnitude",
        "rounding_or_quantization": "explicit tick quantize required before kernel bind",
        "tick_lot_dependent": True,
        "nan_inf_overflow_policy": "fail_closed",
        "canonical_owner": CANONICAL_FUTURES_KERNEL_OWNER,
        "proof_status": "UNWIRED_CONVERSION_CONTRACT_REQUIRED",
    },
    {
        "field_name": "qty",
        "source": "future Master V2 position projection",
        "target": CANONICAL_FUTURES_KERNEL_OWNER,
        "current_unit": "quantity",
        "expected_target_unit": "contracts",
        "current_number_type": "float",
        "expected_target_number_type": "Decimal",
        "sign_convention": "long_short_quantity",
        "rounding_or_quantization": "lot/min_qty quantize required; distinct from price",
        "tick_lot_dependent": True,
        "nan_inf_overflow_policy": "fail_closed",
        "canonical_owner": CANONICAL_FUTURES_KERNEL_OWNER,
        "proof_status": "UNWIRED_CONVERSION_CONTRACT_REQUIRED",
    },
    {
        "field_name": "contract_size",
        "source": "FuturesInstrumentSpec",
        "target": CANONICAL_FUTURES_KERNEL_OWNER,
        "current_unit": "base_asset",
        "expected_target_unit": "base_asset",
        "current_number_type": "Decimal",
        "expected_target_number_type": "Decimal",
        "sign_convention": "nonnegative_magnitude",
        "rounding_or_quantization": "validated >0; no implicit round",
        "tick_lot_dependent": False,
        "nan_inf_overflow_policy": "fail_closed ValueError",
        "canonical_owner": CANONICAL_FUTURES_KERNEL_OWNER,
        "proof_status": "KERNEL_VALIDATED_ONLY",
    },
    {
        "field_name": "tick_size",
        "source": "FuturesInstrumentSpec",
        "target": CANONICAL_FUTURES_KERNEL_OWNER,
        "current_unit": "price",
        "expected_target_unit": "price",
        "current_number_type": "Decimal",
        "expected_target_number_type": "Decimal",
        "sign_convention": "nonnegative_magnitude",
        "rounding_or_quantization": "venue precision owner; not Python round()",
        "tick_lot_dependent": True,
        "nan_inf_overflow_policy": "fail_closed ValueError",
        "canonical_owner": CANONICAL_FUTURES_KERNEL_OWNER,
        "proof_status": "VALIDATED_NOT_QUANTIZED",
    },
    {
        "field_name": "min_qty",
        "source": "FuturesInstrumentSpec",
        "target": CANONICAL_FUTURES_KERNEL_OWNER,
        "current_unit": "quantity",
        "expected_target_unit": "contracts",
        "current_number_type": "Decimal",
        "expected_target_number_type": "Decimal",
        "sign_convention": "nonnegative_magnitude",
        "rounding_or_quantization": "lot size owner; distinct from tick_size",
        "tick_lot_dependent": True,
        "nan_inf_overflow_policy": "fail_closed ValueError",
        "canonical_owner": CANONICAL_FUTURES_KERNEL_OWNER,
        "proof_status": "VALIDATED_NOT_QUANTIZED",
    },
    {
        "field_name": "realized_pnl",
        "source": MASTER_V2_CAPITAL_SLOT_FLOAT_OWNER,
        "target": CANONICAL_FUTURES_KERNEL_OWNER,
        "current_unit": "pnl",
        "expected_target_unit": "quote_notional",
        "current_number_type": "float",
        "expected_target_number_type": "Decimal",
        "sign_convention": "realized_pnl",
        "rounding_or_quantization": "money quantize via QuantizationPolicy when bound",
        "tick_lot_dependent": False,
        "nan_inf_overflow_policy": "fail_closed",
        "canonical_owner": CANONICAL_FUTURES_KERNEL_OWNER,
        "proof_status": "UNWIRED_CONVERSION_CONTRACT_REQUIRED",
    },
    {
        "field_name": "unrealized_pnl",
        "source": MASTER_V2_CAPITAL_SLOT_FLOAT_OWNER,
        "target": CANONICAL_FUTURES_KERNEL_OWNER,
        "current_unit": "pnl",
        "expected_target_unit": "quote_notional",
        "current_number_type": "float",
        "expected_target_number_type": "Decimal",
        "sign_convention": "unrealized_pnl",
        "rounding_or_quantization": "money quantize via QuantizationPolicy when bound",
        "tick_lot_dependent": False,
        "nan_inf_overflow_policy": "fail_closed",
        "canonical_owner": CANONICAL_FUTURES_KERNEL_OWNER,
        "proof_status": "UNWIRED_CONVERSION_CONTRACT_REQUIRED",
    },
    {
        "field_name": "notional",
        "source": "future Master V2 projection",
        "target": CANONICAL_FUTURES_KERNEL_OWNER,
        "current_unit": "quote_notional",
        "expected_target_unit": "quote_notional",
        "current_number_type": "float",
        "expected_target_number_type": "Decimal",
        "sign_convention": "nonnegative_magnitude",
        "rounding_or_quantization": "notional_value formula in kernel only",
        "tick_lot_dependent": True,
        "nan_inf_overflow_policy": "fail_closed",
        "canonical_owner": CANONICAL_FUTURES_KERNEL_OWNER,
        "proof_status": "UNWIRED_CONVERSION_CONTRACT_REQUIRED",
    },
    {
        "field_name": "fee_bps",
        "source": "future Master V2 projection",
        "target": CANONICAL_FUTURES_KERNEL_OWNER,
        "current_unit": "basis_points",
        "expected_target_unit": "basis_points",
        "current_number_type": "float",
        "expected_target_number_type": "Decimal",
        "sign_convention": "fee_as_charge",
        "rounding_or_quantization": "apply_fee_on_notional in kernel only",
        "tick_lot_dependent": False,
        "nan_inf_overflow_policy": "fail_closed",
        "canonical_owner": CANONICAL_FUTURES_KERNEL_OWNER,
        "proof_status": "UNWIRED_CONVERSION_CONTRACT_REQUIRED",
    },
    {
        "field_name": "funding_rate",
        "source": "future Master V2 projection",
        "target": CANONICAL_FUTURES_KERNEL_OWNER,
        "current_unit": "funding_rate",
        "expected_target_unit": "funding_rate",
        "current_number_type": "float",
        "expected_target_number_type": "Decimal",
        "sign_convention": "funding_payment_or_receipt",
        "rounding_or_quantization": "funding_payment_quote in kernel only",
        "tick_lot_dependent": False,
        "nan_inf_overflow_policy": "fail_closed",
        "canonical_owner": CANONICAL_FUTURES_KERNEL_OWNER,
        "proof_status": "UNWIRED_CONVERSION_CONTRACT_REQUIRED",
    },
    {
        "field_name": "equity",
        "source": MASTER_V2_CAPITAL_SLOT_FLOAT_OWNER,
        "target": CANONICAL_FUTURES_KERNEL_OWNER,
        "current_unit": "equity",
        "expected_target_unit": "quote_notional",
        "current_number_type": "float",
        "expected_target_number_type": "Decimal",
        "sign_convention": "drawdown_loss",
        "rounding_or_quantization": "money quantize when bound",
        "tick_lot_dependent": False,
        "nan_inf_overflow_policy": "fail_closed",
        "canonical_owner": CANONICAL_FUTURES_KERNEL_OWNER,
        "proof_status": "UNWIRED_CONVERSION_CONTRACT_REQUIRED",
    },
    {
        "field_name": "initial_margin_rate",
        "source": "FuturesMarginSpec",
        "target": CANONICAL_FUTURES_KERNEL_OWNER,
        "current_unit": "percent",
        "expected_target_unit": "percent",
        "current_number_type": "Decimal",
        "expected_target_number_type": "Decimal",
        "sign_convention": "nonnegative_magnitude",
        "rounding_or_quantization": "validated; no float bridge",
        "tick_lot_dependent": False,
        "nan_inf_overflow_policy": "fail_closed ValueError",
        "canonical_owner": CANONICAL_FUTURES_KERNEL_OWNER,
        "proof_status": "KERNEL_VALIDATED_ONLY",
    },
    {
        "field_name": "maintenance_margin_rate",
        "source": "FuturesMarginSpec",
        "target": CANONICAL_FUTURES_KERNEL_OWNER,
        "current_unit": "percent",
        "expected_target_unit": "percent",
        "current_number_type": "Decimal",
        "expected_target_number_type": "Decimal",
        "sign_convention": "nonnegative_magnitude",
        "rounding_or_quantization": "validated; no float bridge",
        "tick_lot_dependent": False,
        "nan_inf_overflow_policy": "fail_closed ValueError",
        "canonical_owner": CANONICAL_FUTURES_KERNEL_OWNER,
        "proof_status": "KERNEL_VALIDATED_ONLY",
    },
    {
        "field_name": "quote_currency_notional",
        "source": "future Master V2 projection",
        "target": CANONICAL_FUTURES_KERNEL_OWNER,
        "current_unit": "quote_asset",
        "expected_target_unit": "quote_asset",
        "current_number_type": "float",
        "expected_target_number_type": "Decimal",
        "sign_convention": "nonnegative_magnitude",
        "rounding_or_quantization": "money quantize when bound",
        "tick_lot_dependent": False,
        "nan_inf_overflow_policy": "fail_closed",
        "canonical_owner": CANONICAL_FUTURES_KERNEL_OWNER,
        "proof_status": "UNWIRED_CONVERSION_CONTRACT_REQUIRED",
    },
    {
        "field_name": "fee_rate",
        "source": "future Master V2 projection",
        "target": CANONICAL_FUTURES_KERNEL_OWNER,
        "current_unit": "fee_rate",
        "expected_target_unit": "fee_rate",
        "current_number_type": "float",
        "expected_target_number_type": "Decimal",
        "sign_convention": "fee_as_charge",
        "rounding_or_quantization": "apply_fee_on_notional in kernel only",
        "tick_lot_dependent": False,
        "nan_inf_overflow_policy": "fail_closed",
        "canonical_owner": CANONICAL_FUTURES_KERNEL_OWNER,
        "proof_status": "UNWIRED_CONVERSION_CONTRACT_REQUIRED",
    },
    {
        "field_name": "maintenance_margin",
        "source": "future Master V2 projection",
        "target": CANONICAL_FUTURES_KERNEL_OWNER,
        "current_unit": "margin",
        "expected_target_unit": "margin",
        "current_number_type": "float",
        "expected_target_number_type": "Decimal",
        "sign_convention": "nonnegative_magnitude",
        "rounding_or_quantization": "maintenance_margin_required in kernel only",
        "tick_lot_dependent": False,
        "nan_inf_overflow_policy": "fail_closed",
        "canonical_owner": CANONICAL_FUTURES_KERNEL_OWNER,
        "proof_status": "UNWIRED_CONVERSION_CONTRACT_REQUIRED",
    },
    {
        "field_name": "adverse_slippage_bps",
        "source": MASTER_V2_REPLAY_FLOAT_OWNER,
        "target": CANONICAL_FUTURES_KERNEL_OWNER,
        "current_unit": "basis_points",
        "expected_target_unit": "basis_points",
        "current_number_type": "float",
        "expected_target_number_type": "Decimal",
        "sign_convention": "adverse_slippage",
        "rounding_or_quantization": "explicit conversion required; not epsilon",
        "tick_lot_dependent": False,
        "nan_inf_overflow_policy": "fail_closed",
        "canonical_owner": CANONICAL_FUTURES_KERNEL_OWNER,
        "proof_status": "UNWIRED_CONVERSION_CONTRACT_REQUIRED",
    },
)

_REQUIRED_UNIT_KINDS: Final[frozenset[str]] = frozenset(
    {
        "price",
        "quantity",
        "contracts",
        "base_asset",
        "quote_asset",
        "quote_notional",
        "percent",
        "basis_points",
        "fee_rate",
        "funding_rate",
        "pnl",
        "equity",
        "margin",
    }
)

_REQUIRED_SIGN_CONVENTIONS: Final[frozenset[str]] = frozenset(
    {
        "long_short_quantity",
        "realized_pnl",
        "unrealized_pnl",
        "fee_as_charge",
        "funding_payment_or_receipt",
        "adverse_slippage",
        "drawdown_loss",
    }
)

_MASTER_V2_KERNEL_BINDING_PATHS: Final[tuple[Path, ...]] = (
    REPO_ROOT / "src" / "ops" / "bounded_master_v2_testnet_completion_path_wiring_v0.py",
    REPO_ROOT / "src" / "ops" / "offline_master_v2_replay_six_node_validation_graph_binding_v0.py",
    REPO_ROOT / "scripts" / "ops" / "run_testnet_bounded_observation_adapter_v0.py",
    *sorted((REPO_ROOT / "src" / "trading" / "master_v2").glob("*.py")),
    *sorted((REPO_ROOT / "src" / "trading" / "master_v2").glob("**/*.py")),
)

_FORBIDDEN_FORMULA_NAMES: Final[frozenset[str]] = frozenset(
    {
        "unrealized_pnl",
        "realize_pnl_on_close",
        "notional_value",
        "apply_fee_on_notional",
        "funding_payment_quote",
        "_to_decimal",
    }
)

_FORBIDDEN_CONVERSION_CLAIM_KEYS: Final[frozenset[str]] = frozenset(
    {
        "DECIMAL_FLOAT_CONVERSION_WIRED",
        "MASTER_V2_KERNEL_CONVERSION_BOUND",
        "FLOAT_DECIMAL_BRIDGE_PROVEN",
        "CONVERSION_BOUNDARY_PROVEN",
        "ARITHMETIC_KERNEL_WIRED",
    }
)


def _imports_futures_accounting_submodule(tree: ast.AST) -> list[str]:
    violations: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                name = alias.name or ""
                if name == "futures_accounting" or name.endswith(".futures_accounting"):
                    violations.append(f"import {name}")
        elif isinstance(node, ast.ImportFrom):
            mod = node.module
            if mod is not None and (
                mod == "futures_accounting"
                or mod.endswith(".futures_accounting")
                or mod == "src.execution.paper.futures_accounting"
            ):
                violations.append(f"from {mod} import ...")
            if mod == "src.execution.paper":
                for alias in node.names:
                    if alias.name == "futures_accounting":
                        violations.append("from src.execution.paper import futures_accounting")
    return violations


def _find_function_def(src_path: Path, name: str) -> ast.FunctionDef | None:
    tree = ast.parse(src_path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    return None


def _annotation_names(node: ast.AST | None) -> set[str]:
    if node is None:
        return set()
    if isinstance(node, ast.Name):
        return {node.id}
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return {node.value}
    if isinstance(node, ast.Subscript):
        names = _annotation_names(node.value)
        if isinstance(node.slice, ast.Tuple):
            for elt in node.slice.elts:
                names |= _annotation_names(elt)
        else:
            names |= _annotation_names(node.slice)
        return names
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):
        return _annotation_names(node.left) | _annotation_names(node.right)
    return set()


def _master_v2_float_field_names(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    fields: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            if "float" in _annotation_names(node.annotation):
                fields.add(node.target.id)
        elif isinstance(node, ast.ClassDef):
            for item in node.body:
                if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                    if "float" in _annotation_names(item.annotation):
                        fields.add(item.target.id)
    return fields


def test_master_v2_float_source_and_futures_kernel_decimal_target_not_interchangeable() -> None:
    float_sources = [
        record for record in CONVERSION_OWNER_REGISTRY if record["role"] == "MASTER_V2_FLOAT_SOURCE"
    ]
    decimal_targets = [
        record
        for record in CONVERSION_OWNER_REGISTRY
        if record["role"] == "FUTURES_ACCOUNTING_DECIMAL_TARGET"
    ]
    assert len(float_sources) >= 2
    assert len(decimal_targets) == 1
    assert decimal_targets[0]["path"] == CANONICAL_FUTURES_KERNEL_OWNER

    kernel_src = REPO_ROOT / CANONICAL_FUTURES_KERNEL_OWNER
    tree = ast.parse(kernel_src.read_text(encoding="utf-8"))
    import_roots = {
        alias.name.split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    import_from_roots = {
        node.module.split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module
    }
    assert "decimal" in import_roots | import_from_roots

    capital_slot_fields = _master_v2_float_field_names(
        REPO_ROOT / MASTER_V2_CAPITAL_SLOT_FLOAT_OWNER
    )
    replay_fields = _master_v2_float_field_names(REPO_ROOT / MASTER_V2_REPLAY_FLOAT_OWNER)
    assert "price" in replay_fields or "realized_or_settled_slot_equity" in replay_fields
    assert "unrealized_pnl" in capital_slot_fields
    assert float_sources[0]["number_type"] != decimal_targets[0]["number_type"]


def test_to_decimal_exists_but_is_not_complete_master_v2_seam_contract() -> None:
    kernel = importlib.import_module("src.execution.paper.futures_accounting")
    to_decimal = getattr(kernel, "_to_decimal", None)
    assert callable(to_decimal)

    sig = inspect.signature(to_decimal)
    param = sig.parameters["value"]
    annotation = str(param.annotation)
    assert "float" in annotation

    fn_def = _find_function_def(REPO_ROOT / CANONICAL_FUTURES_KERNEL_OWNER, "_to_decimal")
    assert fn_def is not None
    src = ast.get_source_segment(
        (REPO_ROOT / CANONICAL_FUTURES_KERNEL_OWNER).read_text(encoding="utf-8"), fn_def
    )
    assert src is not None
    assert "is_finite()" in src
    assert "Decimal(str(value))" in src

    assert FUTURE_KERNEL_WIRING_REQUIRES_EXPLICIT_CONVERSION_CONTRACT is True
    text = Path(__file__).read_text(encoding="utf-8")
    assert "does not constitute a complete Master-V2 seam conversion contract" in text


def test_strict_decimal_quantization_owner_rejects_float_and_remains_protected() -> None:
    owner = next(
        record
        for record in CONVERSION_OWNER_REGISTRY
        if record["role"] == "STRICT_DECIMAL_QUANTIZATION_OWNER"
    )
    assert owner["path"] == STRICT_DECIMAL_QUANTIZATION_OWNER
    assert owner["rejects_float"] is True

    quant_src = (REPO_ROOT / STRICT_DECIMAL_QUANTIZATION_OWNER).read_text(encoding="utf-8")
    assert "float inputs are forbidden" in quant_src
    assert "quantize" in quant_src
    assert "q_price" in quant_src
    assert "q_qty" in quant_src

    try:
        strict_decimal_d(1.0)
        raise AssertionError("expected TypeError for float input to strict_decimal_d")
    except TypeError as exc:
        assert "float inputs are forbidden" in str(exc)

    policy_mod = importlib.import_module("src.execution.ledger.models")
    policy = policy_mod.QuantizationPolicy()
    assert policy.rounding is not None
    assert "ROUND_" in policy.rounding


def test_value_boundary_matrix_complete_for_future_kernel_binding() -> None:
    field_names = [record["field_name"] for record in VALUE_BOUNDARY_MATRIX]
    assert len(field_names) == len(set(field_names)), "duplicate field names in matrix"

    matrix_units = {record["current_unit"] for record in VALUE_BOUNDARY_MATRIX}
    matrix_units |= {record["expected_target_unit"] for record in VALUE_BOUNDARY_MATRIX}
    assert _REQUIRED_UNIT_KINDS.issubset(matrix_units)

    matrix_signs = {record["sign_convention"] for record in VALUE_BOUNDARY_MATRIX}
    assert _REQUIRED_SIGN_CONVENTIONS.issubset(matrix_signs)

    for record in VALUE_BOUNDARY_MATRIX:
        assert record["canonical_owner"] == CANONICAL_FUTURES_KERNEL_OWNER
        assert record["proof_status"]
        if record["current_number_type"] == "float":
            assert record["expected_target_number_type"] == "Decimal"
        assert record["current_unit"] != record["expected_target_unit"] or record["field_name"] in {
            "price",
            "mark_price",
            "entry_price",
            "contract_size",
            "tick_size",
            "min_qty",
            "fee_bps",
            "fee_rate",
            "funding_rate",
            "initial_margin_rate",
            "maintenance_margin_rate",
            "maintenance_margin",
            "quote_currency_notional",
            "adverse_slippage_bps",
            "notional",
        }


def test_rounding_and_quantization_are_distinct_with_tick_lot_owners() -> None:
    kernel_src = (REPO_ROOT / CANONICAL_FUTURES_KERNEL_OWNER).read_text(encoding="utf-8")
    assert "quantize" not in kernel_src
    assert "ROUND_" not in kernel_src

    quant_src = (REPO_ROOT / STRICT_DECIMAL_QUANTIZATION_OWNER).read_text(encoding="utf-8")
    assert "def q(" in quant_src
    assert "def q_price(" in quant_src
    assert "def q_qty(" in quant_src
    assert "rounding=policy.rounding" in quant_src

    tick_record = next(
        record for record in VALUE_BOUNDARY_MATRIX if record["field_name"] == "tick_size"
    )
    lot_record = next(
        record for record in VALUE_BOUNDARY_MATRIX if record["field_name"] == "min_qty"
    )
    assert tick_record["current_unit"] == "price"
    assert lot_record["current_unit"] == "quantity"
    assert tick_record["rounding_or_quantization"] != lot_record["rounding_or_quantization"]

    fn_def = _find_function_def(
        REPO_ROOT / CANONICAL_FUTURES_KERNEL_OWNER, "validate_futures_accounting_inputs"
    )
    assert fn_def is not None
    validate_src = ast.get_source_segment(
        (REPO_ROOT / CANONICAL_FUTURES_KERNEL_OWNER).read_text(encoding="utf-8"), fn_def
    )
    assert validate_src is not None
    assert "tick_size" in validate_src
    assert "min_qty" in validate_src


def test_nan_infinity_overflow_and_special_values_require_fail_closed_wiring() -> None:
    kernel = importlib.import_module("src.execution.paper.futures_accounting")
    to_decimal = kernel._to_decimal

    for bad_name, bad_value in (
        ("nan_value", float("nan")),
        ("pos_inf", float("inf")),
        ("neg_inf", float("-inf")),
    ):
        try:
            to_decimal(bad_name, bad_value)
            raise AssertionError(f"expected ValueError for {bad_name}")
        except ValueError as exc:
            assert "finite" in str(exc)

    capital_src = (REPO_ROOT / MASTER_V2_CAPITAL_SLOT_FLOAT_OWNER).read_text(encoding="utf-8")
    assert "_SPLIT_EPS" in capital_src

    survival_src = (REPO_ROOT / "src/trading/master_v2/double_play_survival.py").read_text(
        encoding="utf-8"
    )
    assert "NaN" in survival_src

    for record in VALUE_BOUNDARY_MATRIX:
        assert "fail_closed" in record["nan_inf_overflow_policy"].lower()


def test_epsilon_tolerance_is_not_decimal_precision_contract() -> None:
    capital_src = (REPO_ROOT / MASTER_V2_CAPITAL_SLOT_FLOAT_OWNER).read_text(encoding="utf-8")
    assert "_SPLIT_EPS = 1e-9" in capital_src
    assert "1e-12" in capital_src
    assert "isclose" not in capital_src
    assert "Decimal" not in capital_src

    quant_src = (REPO_ROOT / STRICT_DECIMAL_QUANTIZATION_OWNER).read_text(encoding="utf-8")
    assert "isclose" not in quant_src
    assert "abs_tol" not in quant_src
    assert "rel_tol" not in quant_src

    text = Path(__file__).read_text(encoding="utf-8")
    assert "epsilon" in text.lower() or "_SPLIT_EPS" in capital_src
    assert "quantize" in quant_src
    assert "isclose" not in capital_src


def test_no_current_kernel_binding_and_contract_is_non_authorizing() -> None:
    seen: set[Path] = set()
    for path in _MASTER_V2_KERNEL_BINDING_PATHS:
        if not path.is_file() or path in seen:
            continue
        seen.add(path)
        tree = ast.parse(path.read_text(encoding="utf-8"))
        bad = _imports_futures_accounting_submodule(tree)
        assert not bad, f"{path.relative_to(REPO_ROOT)}: forbidden futures_accounting import: {bad}"

    tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    defined = {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and not node.name.startswith("test_")
    }
    assert defined.isdisjoint(_FORBIDDEN_FORMULA_NAMES)

    text = Path(__file__).read_text(encoding="utf-8")
    assert PACKAGE_MARKER in text
    assert AUTHORITY_LIFT is False
    for key in _FORBIDDEN_CONVERSION_CLAIM_KEYS:
        assert f"{key}=true" not in text

    roles = {record["role"] for record in CONVERSION_OWNER_REGISTRY}
    assert roles.isdisjoint(_BINDING_ROLES)
    assert all(role in _VALID_OWNER_ROLES for role in roles)
