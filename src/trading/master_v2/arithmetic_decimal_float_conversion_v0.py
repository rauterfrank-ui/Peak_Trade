"""Master V2 arithmetic Decimal/float conversion boundary v0.

Fail-closed conversion for Master-V2-to-futures-kernel boundary fields.
Pure module: no wiring, no PnL/fee/funding formulas, no authority lift.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from enum import Enum
from typing import Callable, Final, Mapping

from src.execution.ledger import quantization as ledger_quantization
from src.execution.ledger.models import QuantizationPolicy

QUANTIZATION_OWNER_PATH: Final[str] = "src/execution/ledger/quantization.py"


class MasterV2BoundaryField(str, Enum):
    PRICE = "price"
    MARK_PRICE = "mark_price"
    ENTRY_PRICE = "entry_price"
    QTY = "qty"
    CONTRACT_SIZE = "contract_size"
    TICK_SIZE = "tick_size"
    MIN_QTY = "min_qty"
    REALIZED_PNL = "realized_pnl"
    UNREALIZED_PNL = "unrealized_pnl"
    NOTIONAL = "notional"
    FEE_BPS = "fee_bps"
    FUNDING_RATE = "funding_rate"
    EQUITY = "equity"
    INITIAL_MARGIN_RATE = "initial_margin_rate"
    MAINTENANCE_MARGIN_RATE = "maintenance_margin_rate"
    QUOTE_CURRENCY_NOTIONAL = "quote_currency_notional"
    FEE_RATE = "fee_rate"
    MAINTENANCE_MARGIN = "maintenance_margin"
    ADVERSE_SLIPPAGE_BPS = "adverse_slippage_bps"


class MasterV2BoundaryConversionErrorCode(str, Enum):
    MISSING_VALUE = "missing_value"
    WRONG_TYPE = "wrong_type"
    BOOL_AS_NUMBER = "bool_as_number"
    NAN = "nan"
    POSITIVE_INFINITY = "positive_infinity"
    NEGATIVE_INFINITY = "negative_infinity"
    OVERFLOW = "overflow"
    UNDERFLOW = "underflow"
    INVALID_NUMERIC_STRING = "invalid_numeric_string"
    NEGATIVE_DISALLOWED = "negative_disallowed"
    ZERO_DISALLOWED = "zero_disallowed"
    UNIT_MISMATCH = "unit_mismatch"
    SIGN_MISMATCH = "sign_mismatch"
    MISSING_PRECISION_METADATA = "missing_precision_metadata"
    MISSING_TICK_SIZE = "missing_tick_size"
    MISSING_LOT_SIZE = "missing_lot_size"
    QUANTIZATION_FAILURE = "quantization_failure"
    UNSUPPORTED_FIELD = "unsupported_field"
    DUPLICATE_FIELD = "duplicate_field"
    PARTIAL_CONVERSION_RESULT = "partial_conversion_result"
    INCOMPLETE_REQUIRED_FIELDS = "incomplete_required_fields"


@dataclass(frozen=True)
class _FieldConversionPolicy:
    unit: str
    target_unit: str
    sign_convention: str
    nullable: bool
    zero_allowed: bool
    negative_allowed: bool
    accepts_float: bool
    strict_positive: bool
    nonnegative_only: bool
    open_interval_01: bool
    tick_size_required: bool
    lot_size_required: bool
    quantization_owner_suffix: str | None


@dataclass(frozen=True)
class MasterV2BoundaryFieldInput:
    field: MasterV2BoundaryField
    value: float | Decimal | None
    tick_size: Decimal | None = None
    lot_size: Decimal | None = None
    quantization_policy: QuantizationPolicy | None = None
    apply_quantization: bool = False


@dataclass(frozen=True)
class MasterV2BoundaryConversionSuccess:
    field: MasterV2BoundaryField
    decimal_value: Decimal
    source_number_type: str
    target_number_type: str
    unit: str
    sign_convention: str
    quantization_applied: bool
    quantization_owner: str | None


@dataclass(frozen=True)
class MasterV2BoundaryConversionError:
    field: MasterV2BoundaryField | None
    error_code: MasterV2BoundaryConversionErrorCode
    message: str


@dataclass(frozen=True)
class MasterV2BoundaryConversionResult:
    success: MasterV2BoundaryConversionSuccess | None
    error: MasterV2BoundaryConversionError | None


@dataclass(frozen=True)
class MasterV2BoundaryBatchConversionResult:
    results: tuple[MasterV2BoundaryConversionResult, ...]
    all_fields_converted: bool
    errors: tuple[MasterV2BoundaryConversionError, ...]


_FIELD_POLICIES: Final[Mapping[MasterV2BoundaryField, _FieldConversionPolicy]] = {
    MasterV2BoundaryField.PRICE: _FieldConversionPolicy(
        unit="price",
        target_unit="price",
        sign_convention="nonnegative_magnitude",
        nullable=False,
        zero_allowed=False,
        negative_allowed=False,
        accepts_float=True,
        strict_positive=True,
        nonnegative_only=False,
        open_interval_01=False,
        tick_size_required=True,
        lot_size_required=False,
        quantization_owner_suffix="q_price",
    ),
    MasterV2BoundaryField.MARK_PRICE: _FieldConversionPolicy(
        unit="price",
        target_unit="price",
        sign_convention="nonnegative_magnitude",
        nullable=False,
        zero_allowed=False,
        negative_allowed=False,
        accepts_float=True,
        strict_positive=True,
        nonnegative_only=False,
        open_interval_01=False,
        tick_size_required=True,
        lot_size_required=False,
        quantization_owner_suffix="q_price",
    ),
    MasterV2BoundaryField.ENTRY_PRICE: _FieldConversionPolicy(
        unit="price",
        target_unit="price",
        sign_convention="nonnegative_magnitude",
        nullable=False,
        zero_allowed=False,
        negative_allowed=False,
        accepts_float=True,
        strict_positive=True,
        nonnegative_only=False,
        open_interval_01=False,
        tick_size_required=True,
        lot_size_required=False,
        quantization_owner_suffix="q_price",
    ),
    MasterV2BoundaryField.QTY: _FieldConversionPolicy(
        unit="quantity",
        target_unit="contracts",
        sign_convention="long_short_quantity",
        nullable=False,
        zero_allowed=False,
        negative_allowed=False,
        accepts_float=True,
        strict_positive=True,
        nonnegative_only=False,
        open_interval_01=False,
        tick_size_required=False,
        lot_size_required=True,
        quantization_owner_suffix="q_qty",
    ),
    MasterV2BoundaryField.CONTRACT_SIZE: _FieldConversionPolicy(
        unit="base_asset",
        target_unit="base_asset",
        sign_convention="nonnegative_magnitude",
        nullable=False,
        zero_allowed=False,
        negative_allowed=False,
        accepts_float=False,
        strict_positive=True,
        nonnegative_only=False,
        open_interval_01=False,
        tick_size_required=False,
        lot_size_required=False,
        quantization_owner_suffix=None,
    ),
    MasterV2BoundaryField.TICK_SIZE: _FieldConversionPolicy(
        unit="price",
        target_unit="price",
        sign_convention="nonnegative_magnitude",
        nullable=False,
        zero_allowed=False,
        negative_allowed=False,
        accepts_float=False,
        strict_positive=True,
        nonnegative_only=False,
        open_interval_01=False,
        tick_size_required=True,
        lot_size_required=False,
        quantization_owner_suffix=None,
    ),
    MasterV2BoundaryField.MIN_QTY: _FieldConversionPolicy(
        unit="quantity",
        target_unit="contracts",
        sign_convention="nonnegative_magnitude",
        nullable=False,
        zero_allowed=False,
        negative_allowed=False,
        accepts_float=False,
        strict_positive=True,
        nonnegative_only=False,
        open_interval_01=False,
        tick_size_required=False,
        lot_size_required=True,
        quantization_owner_suffix="q_qty",
    ),
    MasterV2BoundaryField.REALIZED_PNL: _FieldConversionPolicy(
        unit="pnl",
        target_unit="quote_notional",
        sign_convention="realized_pnl",
        nullable=False,
        zero_allowed=True,
        negative_allowed=True,
        accepts_float=True,
        strict_positive=False,
        nonnegative_only=False,
        open_interval_01=False,
        tick_size_required=False,
        lot_size_required=False,
        quantization_owner_suffix="q_money",
    ),
    MasterV2BoundaryField.UNREALIZED_PNL: _FieldConversionPolicy(
        unit="pnl",
        target_unit="quote_notional",
        sign_convention="unrealized_pnl",
        nullable=False,
        zero_allowed=True,
        negative_allowed=True,
        accepts_float=True,
        strict_positive=False,
        nonnegative_only=False,
        open_interval_01=False,
        tick_size_required=False,
        lot_size_required=False,
        quantization_owner_suffix="q_money",
    ),
    MasterV2BoundaryField.NOTIONAL: _FieldConversionPolicy(
        unit="quote_notional",
        target_unit="quote_notional",
        sign_convention="nonnegative_magnitude",
        nullable=False,
        zero_allowed=False,
        negative_allowed=False,
        accepts_float=True,
        strict_positive=True,
        nonnegative_only=False,
        open_interval_01=False,
        tick_size_required=True,
        lot_size_required=True,
        quantization_owner_suffix=None,
    ),
    MasterV2BoundaryField.FEE_BPS: _FieldConversionPolicy(
        unit="basis_points",
        target_unit="basis_points",
        sign_convention="fee_as_charge",
        nullable=False,
        zero_allowed=True,
        negative_allowed=False,
        accepts_float=True,
        strict_positive=False,
        nonnegative_only=True,
        open_interval_01=False,
        tick_size_required=False,
        lot_size_required=False,
        quantization_owner_suffix=None,
    ),
    MasterV2BoundaryField.FUNDING_RATE: _FieldConversionPolicy(
        unit="funding_rate",
        target_unit="funding_rate",
        sign_convention="funding_payment_or_receipt",
        nullable=True,
        zero_allowed=True,
        negative_allowed=True,
        accepts_float=True,
        strict_positive=False,
        nonnegative_only=False,
        open_interval_01=False,
        tick_size_required=False,
        lot_size_required=False,
        quantization_owner_suffix=None,
    ),
    MasterV2BoundaryField.EQUITY: _FieldConversionPolicy(
        unit="equity",
        target_unit="quote_notional",
        sign_convention="drawdown_loss",
        nullable=False,
        zero_allowed=True,
        negative_allowed=False,
        accepts_float=True,
        strict_positive=False,
        nonnegative_only=True,
        open_interval_01=False,
        tick_size_required=False,
        lot_size_required=False,
        quantization_owner_suffix="q_money",
    ),
    MasterV2BoundaryField.INITIAL_MARGIN_RATE: _FieldConversionPolicy(
        unit="percent",
        target_unit="percent",
        sign_convention="nonnegative_magnitude",
        nullable=False,
        zero_allowed=False,
        negative_allowed=False,
        accepts_float=False,
        strict_positive=False,
        nonnegative_only=False,
        open_interval_01=True,
        tick_size_required=False,
        lot_size_required=False,
        quantization_owner_suffix=None,
    ),
    MasterV2BoundaryField.MAINTENANCE_MARGIN_RATE: _FieldConversionPolicy(
        unit="percent",
        target_unit="percent",
        sign_convention="nonnegative_magnitude",
        nullable=False,
        zero_allowed=False,
        negative_allowed=False,
        accepts_float=False,
        strict_positive=False,
        nonnegative_only=False,
        open_interval_01=True,
        tick_size_required=False,
        lot_size_required=False,
        quantization_owner_suffix=None,
    ),
    MasterV2BoundaryField.QUOTE_CURRENCY_NOTIONAL: _FieldConversionPolicy(
        unit="quote_asset",
        target_unit="quote_asset",
        sign_convention="nonnegative_magnitude",
        nullable=False,
        zero_allowed=True,
        negative_allowed=False,
        accepts_float=True,
        strict_positive=False,
        nonnegative_only=True,
        open_interval_01=False,
        tick_size_required=False,
        lot_size_required=False,
        quantization_owner_suffix="q_money",
    ),
    MasterV2BoundaryField.FEE_RATE: _FieldConversionPolicy(
        unit="fee_rate",
        target_unit="fee_rate",
        sign_convention="fee_as_charge",
        nullable=False,
        zero_allowed=True,
        negative_allowed=False,
        accepts_float=True,
        strict_positive=False,
        nonnegative_only=True,
        open_interval_01=False,
        tick_size_required=False,
        lot_size_required=False,
        quantization_owner_suffix=None,
    ),
    MasterV2BoundaryField.MAINTENANCE_MARGIN: _FieldConversionPolicy(
        unit="margin",
        target_unit="margin",
        sign_convention="nonnegative_magnitude",
        nullable=False,
        zero_allowed=True,
        negative_allowed=False,
        accepts_float=True,
        strict_positive=False,
        nonnegative_only=True,
        open_interval_01=False,
        tick_size_required=False,
        lot_size_required=False,
        quantization_owner_suffix="q_money",
    ),
    MasterV2BoundaryField.ADVERSE_SLIPPAGE_BPS: _FieldConversionPolicy(
        unit="basis_points",
        target_unit="basis_points",
        sign_convention="adverse_slippage",
        nullable=False,
        zero_allowed=True,
        negative_allowed=False,
        accepts_float=True,
        strict_positive=False,
        nonnegative_only=True,
        open_interval_01=False,
        tick_size_required=False,
        lot_size_required=False,
        quantization_owner_suffix=None,
    ),
}

_ALL_FIELDS: Final[tuple[MasterV2BoundaryField, ...]] = tuple(MasterV2BoundaryField)
_DECIMAL_MAX_MAGNITUDE: Final[Decimal] = Decimal("1e308")


def _error(
    field: MasterV2BoundaryField | None,
    code: MasterV2BoundaryConversionErrorCode,
    message: str,
) -> MasterV2BoundaryConversionError:
    return MasterV2BoundaryConversionError(field=field, error_code=code, message=message)


def _failure(
    field: MasterV2BoundaryField | None,
    code: MasterV2BoundaryConversionErrorCode,
    message: str,
) -> MasterV2BoundaryConversionResult:
    return MasterV2BoundaryConversionResult(success=None, error=_error(field, code, message))


def _is_finite_number(
    value: float | Decimal,
) -> tuple[bool, MasterV2BoundaryConversionErrorCode | None]:
    if isinstance(value, float):
        if math.isnan(value):
            return False, MasterV2BoundaryConversionErrorCode.NAN
        if math.isinf(value):
            if value > 0:
                return False, MasterV2BoundaryConversionErrorCode.POSITIVE_INFINITY
            return False, MasterV2BoundaryConversionErrorCode.NEGATIVE_INFINITY
        return True, None
    if not value.is_finite():
        if value.is_nan():
            return False, MasterV2BoundaryConversionErrorCode.NAN
        if value < 0:
            return False, MasterV2BoundaryConversionErrorCode.NEGATIVE_INFINITY
        return False, MasterV2BoundaryConversionErrorCode.POSITIVE_INFINITY
    return True, None


def _to_decimal_text(value: float) -> Decimal | MasterV2BoundaryConversionErrorCode:
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError, OverflowError):
        return MasterV2BoundaryConversionErrorCode.OVERFLOW


def _validate_range(
    field: MasterV2BoundaryField,
    policy: _FieldConversionPolicy,
    decimal_value: Decimal,
) -> MasterV2BoundaryConversionError | None:
    if abs(decimal_value) > _DECIMAL_MAX_MAGNITUDE:
        return _error(
            field, MasterV2BoundaryConversionErrorCode.OVERFLOW, f"{field.value} overflow"
        )

    if policy.open_interval_01:
        if decimal_value <= 0 or decimal_value >= 1:
            if decimal_value == 0:
                return _error(
                    field,
                    MasterV2BoundaryConversionErrorCode.ZERO_DISALLOWED,
                    f"{field.value} must be in (0, 1)",
                )
            if decimal_value < 0:
                return _error(
                    field,
                    MasterV2BoundaryConversionErrorCode.NEGATIVE_DISALLOWED,
                    f"{field.value} must be in (0, 1)",
                )
            return _error(
                field,
                MasterV2BoundaryConversionErrorCode.OVERFLOW,
                f"{field.value} must be in (0, 1)",
            )
        return None

    if decimal_value == 0:
        if not policy.zero_allowed:
            return _error(
                field,
                MasterV2BoundaryConversionErrorCode.ZERO_DISALLOWED,
                f"{field.value} zero disallowed",
            )
        return None

    if decimal_value < 0:
        if not policy.negative_allowed:
            return _error(
                field,
                MasterV2BoundaryConversionErrorCode.NEGATIVE_DISALLOWED,
                f"{field.value} negative disallowed",
            )
        return None

    if policy.strict_positive and decimal_value <= 0:
        if decimal_value == 0:
            return _error(
                field,
                MasterV2BoundaryConversionErrorCode.ZERO_DISALLOWED,
                f"{field.value} must be > 0",
            )
        return _error(
            field,
            MasterV2BoundaryConversionErrorCode.NEGATIVE_DISALLOWED,
            f"{field.value} must be > 0",
        )

    if policy.nonnegative_only and decimal_value < 0:
        return _error(
            field,
            MasterV2BoundaryConversionErrorCode.NEGATIVE_DISALLOWED,
            f"{field.value} must be >= 0",
        )

    if policy.strict_positive and 0 < decimal_value < Decimal("1e-300"):
        return _error(
            field,
            MasterV2BoundaryConversionErrorCode.UNDERFLOW,
            f"{field.value} underflow",
        )

    return None


def _validate_precision_metadata(
    field: MasterV2BoundaryField,
    policy: _FieldConversionPolicy,
    input_data: MasterV2BoundaryFieldInput,
) -> MasterV2BoundaryConversionError | None:
    if not input_data.apply_quantization:
        return None
    if policy.tick_size_required and input_data.tick_size is None:
        return _error(
            field,
            MasterV2BoundaryConversionErrorCode.MISSING_TICK_SIZE,
            f"{field.value} requires tick_size metadata",
        )
    if policy.lot_size_required and input_data.lot_size is None:
        return _error(
            field,
            MasterV2BoundaryConversionErrorCode.MISSING_LOT_SIZE,
            f"{field.value} requires lot_size metadata",
        )
    if input_data.quantization_policy is None:
        return _error(
            field,
            MasterV2BoundaryConversionErrorCode.MISSING_PRECISION_METADATA,
            f"{field.value} requires quantization_policy when apply_quantization=True",
        )
    if input_data.tick_size is not None:
        if not isinstance(input_data.tick_size, Decimal) or input_data.tick_size <= 0:
            return _error(
                field,
                MasterV2BoundaryConversionErrorCode.UNIT_MISMATCH,
                "tick_size must be positive Decimal",
            )
    if input_data.lot_size is not None:
        if not isinstance(input_data.lot_size, Decimal) or input_data.lot_size <= 0:
            return _error(
                field,
                MasterV2BoundaryConversionErrorCode.UNIT_MISMATCH,
                "lot_size must be positive Decimal",
            )
    return None


def _delegate_quantize(
    field: MasterV2BoundaryField,
    policy: _FieldConversionPolicy,
    decimal_value: Decimal,
    quantization_policy: QuantizationPolicy,
) -> tuple[Decimal, str] | MasterV2BoundaryConversionError:
    suffix = policy.quantization_owner_suffix
    if suffix is None:
        return _error(
            field,
            MasterV2BoundaryConversionErrorCode.QUANTIZATION_FAILURE,
            f"{field.value} has no quantization delegate",
        )
    fn_map: Mapping[str, Callable[..., Decimal]] = {
        "q_price": ledger_quantization.q_price,
        "q_qty": ledger_quantization.q_qty,
        "q_money": ledger_quantization.q_money,
    }
    quant_fn = fn_map.get(suffix)
    if quant_fn is None:
        return _error(
            field,
            MasterV2BoundaryConversionErrorCode.QUANTIZATION_FAILURE,
            f"unknown quantization delegate for {field.value}",
        )
    try:
        quantized = quant_fn(decimal_value, policy=quantization_policy)
    except Exception as exc:  # noqa: BLE001 — fail-closed boundary
        return _error(
            field,
            MasterV2BoundaryConversionErrorCode.QUANTIZATION_FAILURE,
            f"quantization failed for {field.value}: {type(exc).__name__}",
        )
    owner = f"{QUANTIZATION_OWNER_PATH}::{suffix}"
    return quantized, owner


def _convert_field_with_policy(
    input_data: MasterV2BoundaryFieldInput,
    policy: _FieldConversionPolicy,
) -> MasterV2BoundaryConversionResult:
    field = input_data.field

    if input_data.value is None:
        if policy.nullable:
            return _failure(
                field,
                MasterV2BoundaryConversionErrorCode.MISSING_VALUE,
                f"{field.value} missing value",
            )
        return _failure(
            field,
            MasterV2BoundaryConversionErrorCode.MISSING_VALUE,
            f"{field.value} missing value",
        )

    value = input_data.value
    if isinstance(value, bool):
        return _failure(
            field,
            MasterV2BoundaryConversionErrorCode.BOOL_AS_NUMBER,
            f"{field.value} rejects bool",
        )

    if isinstance(value, str):
        return _failure(
            field,
            MasterV2BoundaryConversionErrorCode.WRONG_TYPE,
            f"{field.value} rejects string ingress in v0",
        )

    if isinstance(value, int) and not isinstance(value, bool):
        return _failure(
            field,
            MasterV2BoundaryConversionErrorCode.WRONG_TYPE,
            f"{field.value} rejects int ingress in v0",
        )

    source_type: str
    decimal_value: Decimal

    if isinstance(value, Decimal):
        finite_ok, finite_code = _is_finite_number(value)
        if not finite_ok:
            assert finite_code is not None
            return _failure(field, finite_code, f"{field.value} non-finite")
        decimal_value = value
        source_type = "Decimal"
    elif isinstance(value, float):
        if not policy.accepts_float:
            return _failure(
                field,
                MasterV2BoundaryConversionErrorCode.WRONG_TYPE,
                f"{field.value} requires Decimal identity path",
            )
        finite_ok, finite_code = _is_finite_number(value)
        if not finite_ok:
            assert finite_code is not None
            return _failure(field, finite_code, f"{field.value} non-finite")
        converted = _to_decimal_text(value)
        if isinstance(converted, MasterV2BoundaryConversionErrorCode):
            return _failure(field, converted, f"{field.value} conversion failed")
        decimal_value = converted
        source_type = "float"
    else:
        return _failure(
            field,
            MasterV2BoundaryConversionErrorCode.WRONG_TYPE,
            f"{field.value} unsupported input type",
        )

    range_error = _validate_range(field, policy, decimal_value)
    if range_error is not None:
        return MasterV2BoundaryConversionResult(success=None, error=range_error)

    metadata_error = _validate_precision_metadata(field, policy, input_data)
    if metadata_error is not None:
        return MasterV2BoundaryConversionResult(success=None, error=metadata_error)

    quantization_applied = False
    quantization_owner: str | None = None
    final_decimal = decimal_value

    if input_data.apply_quantization:
        if policy.quantization_owner_suffix is None:
            return _failure(
                field,
                MasterV2BoundaryConversionErrorCode.QUANTIZATION_FAILURE,
                f"{field.value} cannot be quantized",
            )
        assert input_data.quantization_policy is not None
        quant_result = _delegate_quantize(
            field,
            policy,
            decimal_value,
            input_data.quantization_policy,
        )
        if isinstance(quant_result, MasterV2BoundaryConversionError):
            return MasterV2BoundaryConversionResult(success=None, error=quant_result)
        final_decimal, quantization_owner = quant_result
        quantization_applied = True

    success = MasterV2BoundaryConversionSuccess(
        field=field,
        decimal_value=final_decimal,
        source_number_type=source_type,
        target_number_type="Decimal",
        unit=policy.target_unit,
        sign_convention=policy.sign_convention,
        quantization_applied=quantization_applied,
        quantization_owner=quantization_owner,
    )
    return MasterV2BoundaryConversionResult(success=success, error=None)


def convert_master_v2_boundary_field(
    input: MasterV2BoundaryFieldInput,
) -> MasterV2BoundaryConversionResult:
    policy = _FIELD_POLICIES.get(input.field)
    if policy is None:
        return _failure(
            input.field,
            MasterV2BoundaryConversionErrorCode.UNSUPPORTED_FIELD,
            "unsupported field",
        )
    return _convert_field_with_policy(input, policy)


def convert_master_v2_boundary_fields_batch(
    inputs: tuple[MasterV2BoundaryFieldInput, ...],
    *,
    require_all_fields: bool = False,
) -> MasterV2BoundaryBatchConversionResult:
    seen: set[MasterV2BoundaryField] = set()
    errors: list[MasterV2BoundaryConversionError] = []

    for input_data in inputs:
        if input_data.field in seen:
            errors.append(
                _error(
                    input_data.field,
                    MasterV2BoundaryConversionErrorCode.DUPLICATE_FIELD,
                    f"duplicate field {input_data.field.value}",
                )
            )
        seen.add(input_data.field)

    if errors:
        return MasterV2BoundaryBatchConversionResult(
            results=(),
            all_fields_converted=False,
            errors=tuple(errors),
        )

    if require_all_fields:
        present = {item.field for item in inputs}
        if present != set(_ALL_FIELDS):
            missing = sorted(
                (field.value for field in _ALL_FIELDS if field not in present),
                key=str,
            )
            batch_error = _error(
                None,
                MasterV2BoundaryConversionErrorCode.INCOMPLETE_REQUIRED_FIELDS,
                f"missing required fields: {', '.join(missing)}",
            )
            return MasterV2BoundaryBatchConversionResult(
                results=(),
                all_fields_converted=False,
                errors=(batch_error,),
            )

    sorted_inputs = sorted(inputs, key=lambda item: item.field.value)
    results: list[MasterV2BoundaryConversionResult] = []
    field_errors: list[MasterV2BoundaryConversionError] = []

    for input_data in sorted_inputs:
        result = convert_master_v2_boundary_field(input_data)
        results.append(result)
        if result.error is not None:
            field_errors.append(result.error)

    if field_errors:
        return MasterV2BoundaryBatchConversionResult(
            results=tuple(results),
            all_fields_converted=False,
            errors=tuple(field_errors),
        )

    all_ok = len(results) > 0 and all(r.success is not None for r in results)
    if not all_ok:
        partial_error = _error(
            None,
            MasterV2BoundaryConversionErrorCode.PARTIAL_CONVERSION_RESULT,
            "partial conversion result",
        )
        return MasterV2BoundaryBatchConversionResult(
            results=tuple(results),
            all_fields_converted=False,
            errors=(partial_error,),
        )

    return MasterV2BoundaryBatchConversionResult(
        results=tuple(results),
        all_fields_converted=True,
        errors=(),
    )
