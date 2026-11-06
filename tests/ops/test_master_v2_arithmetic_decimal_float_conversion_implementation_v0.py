"""Bounded tests for Master V2 arithmetic Decimal/float conversion implementation v0.

26 collected nodes (19 parametrize expansions + 7 fixed). Non-authorizing. No runtime/network.
"""

from __future__ import annotations

import ast
import inspect
import math
from decimal import Decimal
from pathlib import Path
from typing import Final

import pytest

from src.execution.ledger.models import QuantizationPolicy
from src.trading.master_v2 import arithmetic_decimal_float_conversion_v0 as conv

REPO_ROOT = Path(__file__).resolve().parents[2]
PRODUCTION_MODULE = (
    REPO_ROOT / "src" / "trading" / "master_v2" / "arithmetic_decimal_float_conversion_v0.py"
)
MODULE_IMPORT = "src.trading.master_v2.arithmetic_decimal_float_conversion_v0"

_PACKAGE_MARKER = "MASTER_V2_ARITHMETIC_DECIMAL_FLOAT_CONVERSION_IMPLEMENTATION_V0=true"
_AUTHORITY_LIFT = False

_HAPPY_VALUES: Final[dict[conv.MasterV2BoundaryField, float | Decimal]] = {
    conv.MasterV2BoundaryField.PRICE: 100.5,
    conv.MasterV2BoundaryField.MARK_PRICE: 101.25,
    conv.MasterV2BoundaryField.ENTRY_PRICE: 99.0,
    conv.MasterV2BoundaryField.QTY: 2.0,
    conv.MasterV2BoundaryField.CONTRACT_SIZE: Decimal("0.001"),
    conv.MasterV2BoundaryField.TICK_SIZE: Decimal("0.01"),
    conv.MasterV2BoundaryField.MIN_QTY: Decimal("0.001"),
    conv.MasterV2BoundaryField.REALIZED_PNL: -12.5,
    conv.MasterV2BoundaryField.UNREALIZED_PNL: 3.75,
    conv.MasterV2BoundaryField.NOTIONAL: 5000.0,
    conv.MasterV2BoundaryField.FEE_BPS: 7.5,
    conv.MasterV2BoundaryField.FUNDING_RATE: 0.0001,
    conv.MasterV2BoundaryField.EQUITY: 10000.0,
    conv.MasterV2BoundaryField.INITIAL_MARGIN_RATE: Decimal("0.1"),
    conv.MasterV2BoundaryField.MAINTENANCE_MARGIN_RATE: Decimal("0.05"),
    conv.MasterV2BoundaryField.QUOTE_CURRENCY_NOTIONAL: 2500.0,
    conv.MasterV2BoundaryField.FEE_RATE: 0.0005,
    conv.MasterV2BoundaryField.MAINTENANCE_MARGIN: 150.0,
    conv.MasterV2BoundaryField.ADVERSE_SLIPPAGE_BPS: 2.0,
}

_ALL_FIELDS: Final[tuple[conv.MasterV2BoundaryField, ...]] = tuple(conv.MasterV2BoundaryField)


def _input_for(field: conv.MasterV2BoundaryField) -> conv.MasterV2BoundaryFieldInput:
    return conv.MasterV2BoundaryFieldInput(field=field, value=_HAPPY_VALUES[field])


def _imports_module(tree: ast.AST, module_suffix: str) -> bool:
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if module_suffix in (alias.name or ""):
                    return True
        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            if module_suffix in mod:
                return True
    return False


@pytest.mark.parametrize("field", _ALL_FIELDS, ids=[f.value for f in _ALL_FIELDS])
def test_all_19_field_policies_convert_successfully(field: conv.MasterV2BoundaryField) -> None:
    result = conv.convert_master_v2_boundary_field(_input_for(field))
    assert result.error is None, result.error
    assert result.success is not None
    success = result.success
    assert success.field == field
    assert isinstance(success.decimal_value, Decimal)
    assert success.target_number_type == "Decimal"
    assert success.unit
    assert success.sign_convention
    assert success.quantization_applied is False
    assert success.quantization_owner is None


def test_rejects_bool_missing_and_invalid_type() -> None:
    bool_result = conv.convert_master_v2_boundary_field(
        conv.MasterV2BoundaryFieldInput(field=conv.MasterV2BoundaryField.PRICE, value=True)
    )
    assert bool_result.success is None
    assert bool_result.error is not None
    assert bool_result.error.error_code == conv.MasterV2BoundaryConversionErrorCode.BOOL_AS_NUMBER

    missing = conv.convert_master_v2_boundary_field(
        conv.MasterV2BoundaryFieldInput(field=conv.MasterV2BoundaryField.PRICE, value=None)
    )
    assert missing.error is not None
    assert missing.error.error_code == conv.MasterV2BoundaryConversionErrorCode.MISSING_VALUE

    wrong_type = conv.convert_master_v2_boundary_field(
        conv.MasterV2BoundaryFieldInput(field=conv.MasterV2BoundaryField.PRICE, value="100.5")
    )
    assert wrong_type.error is not None
    assert wrong_type.error.error_code == conv.MasterV2BoundaryConversionErrorCode.WRONG_TYPE

    decimal_only = conv.convert_master_v2_boundary_field(
        conv.MasterV2BoundaryFieldInput(
            field=conv.MasterV2BoundaryField.CONTRACT_SIZE,
            value=1.5,
        )
    )
    assert decimal_only.error is not None
    assert decimal_only.error.error_code == conv.MasterV2BoundaryConversionErrorCode.WRONG_TYPE


def test_rejects_non_finite_values() -> None:
    for raw, code in (
        (float("nan"), conv.MasterV2BoundaryConversionErrorCode.NAN),
        (float("inf"), conv.MasterV2BoundaryConversionErrorCode.POSITIVE_INFINITY),
        (float("-inf"), conv.MasterV2BoundaryConversionErrorCode.NEGATIVE_INFINITY),
    ):
        result = conv.convert_master_v2_boundary_field(
            conv.MasterV2BoundaryFieldInput(field=conv.MasterV2BoundaryField.PRICE, value=raw)
        )
        assert result.success is None
        assert result.error is not None
        assert result.error.error_code == code


def test_negative_zero_and_overflow_boundaries() -> None:
    negative_price = conv.convert_master_v2_boundary_field(
        conv.MasterV2BoundaryFieldInput(field=conv.MasterV2BoundaryField.PRICE, value=-1.0)
    )
    assert negative_price.error is not None
    assert (
        negative_price.error.error_code
        == conv.MasterV2BoundaryConversionErrorCode.NEGATIVE_DISALLOWED
    )

    zero_price = conv.convert_master_v2_boundary_field(
        conv.MasterV2BoundaryFieldInput(field=conv.MasterV2BoundaryField.PRICE, value=0.0)
    )
    assert zero_price.error is not None
    assert zero_price.error.error_code == conv.MasterV2BoundaryConversionErrorCode.ZERO_DISALLOWED

    overflow = conv.convert_master_v2_boundary_field(
        conv.MasterV2BoundaryFieldInput(
            field=conv.MasterV2BoundaryField.CONTRACT_SIZE,
            value=Decimal("9e999"),
        )
    )
    assert overflow.error is not None
    assert overflow.error.error_code == conv.MasterV2BoundaryConversionErrorCode.OVERFLOW

    underflow = conv.convert_master_v2_boundary_field(
        conv.MasterV2BoundaryFieldInput(field=conv.MasterV2BoundaryField.PRICE, value=5e-324)
    )
    assert underflow.error is not None
    assert underflow.error.error_code == conv.MasterV2BoundaryConversionErrorCode.UNDERFLOW

    signed_ok = conv.convert_master_v2_boundary_field(
        conv.MasterV2BoundaryFieldInput(field=conv.MasterV2BoundaryField.REALIZED_PNL, value=-1.0)
    )
    assert signed_ok.success is not None

    margin_rate = conv.convert_master_v2_boundary_field(
        conv.MasterV2BoundaryFieldInput(
            field=conv.MasterV2BoundaryField.INITIAL_MARGIN_RATE,
            value=Decimal("1.5"),
        )
    )
    assert margin_rate.error is not None
    assert margin_rate.error.error_code == conv.MasterV2BoundaryConversionErrorCode.OVERFLOW


def test_deterministic_decimal_no_float_leakage() -> None:
    value = 0.1 + 0.2
    result_a = conv.convert_master_v2_boundary_field(
        conv.MasterV2BoundaryFieldInput(field=conv.MasterV2BoundaryField.FEE_BPS, value=value)
    )
    result_b = conv.convert_master_v2_boundary_field(
        conv.MasterV2BoundaryFieldInput(field=conv.MasterV2BoundaryField.FEE_BPS, value=value)
    )
    assert result_a.success is not None and result_b.success is not None
    assert result_a.success.decimal_value == result_b.success.decimal_value
    assert result_a.success.decimal_value == Decimal(str(value))
    assert isinstance(result_a.success.decimal_value, Decimal)
    assert not isinstance(result_a.success.decimal_value, float)


def test_conversion_quantization_tick_lot_separation() -> None:
    policy = QuantizationPolicy(
        price_quant=Decimal("0.01"),
        qty_quant=Decimal("0.001"),
        money_quant=Decimal("0.01"),
    )
    without_quant = conv.convert_master_v2_boundary_field(
        conv.MasterV2BoundaryFieldInput(
            field=conv.MasterV2BoundaryField.PRICE,
            value=100.555,
            tick_size=Decimal("0.01"),
        )
    )
    assert without_quant.success is not None
    assert without_quant.success.quantization_applied is False
    assert without_quant.success.decimal_value == Decimal("100.555")

    missing_tick = conv.convert_master_v2_boundary_field(
        conv.MasterV2BoundaryFieldInput(
            field=conv.MasterV2BoundaryField.PRICE,
            value=100.5,
            apply_quantization=True,
            quantization_policy=policy,
        )
    )
    assert missing_tick.error is not None
    assert (
        missing_tick.error.error_code == conv.MasterV2BoundaryConversionErrorCode.MISSING_TICK_SIZE
    )

    with_quant = conv.convert_master_v2_boundary_field(
        conv.MasterV2BoundaryFieldInput(
            field=conv.MasterV2BoundaryField.PRICE,
            value=100.555,
            tick_size=Decimal("0.01"),
            apply_quantization=True,
            quantization_policy=policy,
        )
    )
    assert with_quant.success is not None
    assert with_quant.success.quantization_applied is True
    assert with_quant.success.quantization_owner == f"{conv.QUANTIZATION_OWNER_PATH}::q_price"
    assert with_quant.success.decimal_value == Decimal("100.56")

    missing_lot = conv.convert_master_v2_boundary_field(
        conv.MasterV2BoundaryFieldInput(
            field=conv.MasterV2BoundaryField.QTY,
            value=1.5,
            apply_quantization=True,
            quantization_policy=policy,
        )
    )
    assert missing_lot.error is not None
    assert missing_lot.error.error_code == conv.MasterV2BoundaryConversionErrorCode.MISSING_LOT_SIZE

    src = PRODUCTION_MODULE.read_text(encoding="utf-8")
    tree = ast.parse(src)
    assert "round(" not in src
    assert "ledger_quantization" in src
    assert '"q_price"' in src or "'q_price'" in src
    assert conv.QUANTIZATION_OWNER_PATH.endswith("quantization.py")


def test_batch_partial_and_complete_semantics() -> None:
    duplicate_batch = conv.convert_master_v2_boundary_fields_batch(
        (
            conv.MasterV2BoundaryFieldInput(field=conv.MasterV2BoundaryField.PRICE, value=1.0),
            conv.MasterV2BoundaryFieldInput(field=conv.MasterV2BoundaryField.PRICE, value=2.0),
        )
    )
    assert duplicate_batch.all_fields_converted is False
    assert duplicate_batch.results == ()
    assert any(
        err.error_code == conv.MasterV2BoundaryConversionErrorCode.DUPLICATE_FIELD
        for err in duplicate_batch.errors
    )

    partial_batch = conv.convert_master_v2_boundary_fields_batch(
        (
            conv.MasterV2BoundaryFieldInput(field=conv.MasterV2BoundaryField.PRICE, value=100.0),
            conv.MasterV2BoundaryFieldInput(field=conv.MasterV2BoundaryField.QTY, value=-1.0),
        )
    )
    assert partial_batch.all_fields_converted is False
    assert partial_batch.errors
    assert any(r.error is not None for r in partial_batch.results)

    complete_inputs = tuple(_input_for(field) for field in _ALL_FIELDS)
    complete_batch = conv.convert_master_v2_boundary_fields_batch(
        complete_inputs,
        require_all_fields=True,
    )
    assert complete_batch.all_fields_converted is True
    assert complete_batch.errors == ()
    assert len(complete_batch.results) == 19

    incomplete = conv.convert_master_v2_boundary_fields_batch(
        (conv.MasterV2BoundaryFieldInput(field=conv.MasterV2BoundaryField.PRICE, value=1.0),),
        require_all_fields=True,
    )
    assert incomplete.all_fields_converted is False
    assert incomplete.results == ()
    assert (
        incomplete.errors[0].error_code
        == conv.MasterV2BoundaryConversionErrorCode.INCOMPLETE_REQUIRED_FIELDS
    )


def test_immutable_non_authorizing_no_wiring() -> None:
    assert _PACKAGE_MARKER
    assert _AUTHORITY_LIFT is False

    for cls in (
        conv.MasterV2BoundaryFieldInput,
        conv.MasterV2BoundaryConversionSuccess,
        conv.MasterV2BoundaryConversionError,
        conv.MasterV2BoundaryConversionResult,
        conv.MasterV2BoundaryBatchConversionResult,
    ):
        assert getattr(cls, "__dataclass_params__").frozen

    public_functions = {
        name
        for name, obj in inspect.getmembers(conv, inspect.isfunction)
        if obj.__module__ == conv.__name__ and not name.startswith("_")
    }
    assert public_functions == {
        "convert_master_v2_boundary_field",
        "convert_master_v2_boundary_fields_batch",
    }

    production_paths = [
        REPO_ROOT / "src" / "trading" / "master_v2",
        REPO_ROOT / "src" / "execution" / "paper",
        REPO_ROOT / "src" / "ops",
    ]
    importers: list[str] = []
    for base in production_paths:
        if not base.exists():
            continue
        for path in base.rglob("*.py"):
            if path.name == "arithmetic_decimal_float_conversion_v0.py":
                continue
            tree = ast.parse(path.read_text(encoding="utf-8"))
            if _imports_module(tree, "arithmetic_decimal_float_conversion_v0"):
                importers.append(str(path.relative_to(REPO_ROOT)))

    assert importers == [], f"unexpected production importers: {importers}"

    forbidden_runtime = ("requests", "socket", "urllib", "httpx", "aiohttp")
    src = PRODUCTION_MODULE.read_text(encoding="utf-8")
    for token in forbidden_runtime:
        assert token not in src

    formula_names = {
        "unrealized_pnl",
        "notional_value",
        "funding_payment_quote",
        "apply_fee_on_notional",
        "_to_decimal",
    }
    tree = ast.parse(src)
    defined = {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and not node.name.startswith("_")
    }
    assert defined.isdisjoint(formula_names)

    assert math.isfinite(1.0)
