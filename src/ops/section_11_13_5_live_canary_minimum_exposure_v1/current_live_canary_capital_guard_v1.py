"""Independent fail-closed live-canary capital guard (CURRENT_LIVE_CANARY_CAPITAL_GUARD_V1).

Does not resize quantities. Does not authorize live POST by itself.
Decimal-only monetary comparisons. AUTHORITY_EFFECT=NONE on Full-Core sizing.
"""

from __future__ import annotations

import hashlib
import json
from contextvars import ContextVar
from contextvars import Token as _CtxReset
from dataclasses import dataclass, field, replace
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Mapping, Sequence

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    OWNER_GO_EXECUTE,
    REUSED_BINDING_ACCOUNT_SCOPE,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.order_plan_v1 import (
    CanaryFlattenOrderPlanV1,
    CanaryOrderPlanV1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.venue_contract_count_v1 import (
    SUI_OPERATIVE_ORDER_SZ,
    canary_venue_contract_count_v1,
)

CONTRACT_ID = "CURRENT_LIVE_CANARY_CAPITAL_GUARD_V1"
SCHEMA_VERSION = "current_live_canary_capital_guard.v1"
DEFAULT_CONFIG_REL_PATH = "config/ops/current_live_canary_capital_guard_v1.json"

GUARD_AUTHORITY_EFFECT = "NONE"
GUARD_CHANGES_RUNTIME_SEMANTICS = False

IMR_SOURCE_PUBLIC_POSITION_TIERS_QTY_ONE = "PUBLIC_POSITION_TIERS_QTY_ONE"
IMR_SOURCE_INSTRUMENTS_METADATA_FORBIDDEN = "INSTRUMENTS_METADATA_IMR_FORBIDDEN"


class CanaryCapitalGuardError(RuntimeError):
    """Fail-closed canary capital guard violation."""


def _dec(raw: Any, *, field: str) -> Decimal:
    try:
        value = Decimal(str(raw))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise CanaryCapitalGuardError(f"INVALID_DECIMAL:{field}") from exc
    return value


def _require_positive_cap(raw: Any, *, field: str) -> Decimal:
    value = _dec(raw, field=field)
    if not value.is_finite() or value <= 0:
        raise CanaryCapitalGuardError(f"NON_POSITIVE_CAP:{field}")
    return value


def _canonical_json(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def compute_canary_plan_digest_v1(*, plan_payload: Mapping[str, Any]) -> str:
    return hashlib.sha256(_canonical_json(plan_payload).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class CanaryCapitalGuardConfigV1:
    schema_version: str
    live_canary_allowed: bool
    owner_caps_ratified: bool
    currency: str
    max_single_order_notional: Decimal | None
    max_incremental_initial_margin: Decimal | None
    max_aggregate_exposure: Decimal | None
    max_leverage: Decimal | None
    max_open_positions: int | None
    max_submitted_orders: int | None
    max_session_capital_commitment: Decimal | None
    scale_in_forbidden: bool
    automatic_retry_forbidden: bool
    fee_buffer_usdc: Decimal | None
    max_new_orders: int
    max_new_positions: int
    config_digest: str

    def to_dict(self) -> dict[str, Any]:
        def _fmt(d: Decimal | None) -> str | None:
            return None if d is None else format(d, "f")

        return {
            "schema_version": self.schema_version,
            "contract_id": CONTRACT_ID,
            "live_canary_allowed": self.live_canary_allowed,
            "owner_caps_ratified": self.owner_caps_ratified,
            "currency": self.currency,
            "max_single_order_notional": _fmt(self.max_single_order_notional),
            "max_incremental_initial_margin": _fmt(self.max_incremental_initial_margin),
            "max_aggregate_exposure": _fmt(self.max_aggregate_exposure),
            "max_leverage": _fmt(self.max_leverage),
            "max_open_positions": self.max_open_positions,
            "max_submitted_orders": self.max_submitted_orders,
            "max_session_capital_commitment": _fmt(self.max_session_capital_commitment),
            "scale_in_forbidden": self.scale_in_forbidden,
            "automatic_retry_forbidden": self.automatic_retry_forbidden,
            "fee_buffer_usdc": _fmt(self.fee_buffer_usdc),
            "max_new_orders": self.max_new_orders,
            "max_new_positions": self.max_new_positions,
            "config_digest": self.config_digest,
        }


def _parse_strict_flag(raw: Any, *, field: str, default: bool) -> bool:
    """Only a JSON boolean sets a guard flag; any other type fails closed."""
    if raw is None:
        return default
    if isinstance(raw, bool):
        return raw
    raise CanaryCapitalGuardError(f"INVALID_BOOL_FLAG:{field}")


def _parse_optional_decimal(raw: Any, *, field: str = "cap") -> Decimal | None:
    if raw is None:
        return None
    if isinstance(raw, bool):
        raise CanaryCapitalGuardError(f"INVALID_DECIMAL:{field}")
    text = str(raw).strip()
    if not text:
        return None
    value = _dec(text, field=field)
    if not value.is_finite():
        raise CanaryCapitalGuardError(f"NON_FINITE_CAP:{field}")
    return value


def parse_optional_finite_decimal_cap_v1(raw: Any, *, field: str) -> Decimal | None:
    return _parse_optional_decimal(raw, field=field)


def _parse_optional_non_negative_int(raw: Any, *, field: str) -> int | None:
    if raw is None:
        return None
    return _parse_required_non_negative_int(raw, field=field)


def _parse_required_non_negative_int(raw: Any, *, field: str) -> int:
    """Parse required int cap; preserves explicit zero; fail-closed on missing/invalid."""
    if raw is None:
        raise CanaryCapitalGuardError(f"MISSING_INT_CAP:{field}")
    if isinstance(raw, bool):
        raise CanaryCapitalGuardError(f"INVALID_INT_CAP:{field}")
    if isinstance(raw, int):
        value = raw
    elif isinstance(raw, str):
        text = raw.strip()
        if not text:
            raise CanaryCapitalGuardError(f"MISSING_INT_CAP:{field}")
        try:
            value = int(text, 10)
        except ValueError as exc:
            raise CanaryCapitalGuardError(f"INVALID_INT_CAP:{field}") from exc
    else:
        try:
            value = int(raw)
        except (TypeError, ValueError) as exc:
            raise CanaryCapitalGuardError(f"INVALID_INT_CAP:{field}") from exc
    if value < 0:
        raise CanaryCapitalGuardError(f"NEGATIVE_INT_CAP:{field}")
    return value


def load_canary_capital_guard_config_v1(
    *,
    repo_root: Path | None = None,
    config_path: Path | None = None,
) -> CanaryCapitalGuardConfigV1:
    root = repo_root or Path(__file__).resolve().parents[3]
    path = config_path or (root / DEFAULT_CONFIG_REL_PATH)
    raw_text = path.read_text(encoding="utf-8")
    payload = json.loads(raw_text)
    if not isinstance(payload, Mapping):
        raise CanaryCapitalGuardError("GUARD_CONFIG_NOT_MAPPING")
    digest = hashlib.sha256(raw_text.encode("utf-8")).hexdigest()
    return parse_canary_capital_guard_config_v1(payload, config_digest=digest)


def parse_canary_capital_guard_config_v1(
    payload: Mapping[str, Any],
    *,
    config_digest: str,
) -> CanaryCapitalGuardConfigV1:
    schema = str(payload.get("schema_version") or "").strip()
    if schema != SCHEMA_VERSION:
        raise CanaryCapitalGuardError(f"GUARD_SCHEMA_MISMATCH:{schema or '<empty>'}")
    currency = str(payload.get("currency") or "").strip().upper()
    if not currency:
        raise CanaryCapitalGuardError("GUARD_CURRENCY_MISSING")
    return CanaryCapitalGuardConfigV1(
        schema_version=schema,
        live_canary_allowed=_parse_strict_flag(
            payload.get("live_canary_allowed"), field="live_canary_allowed", default=False
        ),
        owner_caps_ratified=_parse_strict_flag(
            payload.get("owner_caps_ratified"), field="owner_caps_ratified", default=False
        ),
        currency=currency,
        max_single_order_notional=_parse_optional_decimal(
            payload.get("max_single_order_notional"), field="max_single_order_notional"
        ),
        max_incremental_initial_margin=_parse_optional_decimal(
            payload.get("max_incremental_initial_margin"), field="max_incremental_initial_margin"
        ),
        max_aggregate_exposure=_parse_optional_decimal(
            payload.get("max_aggregate_exposure"), field="max_aggregate_exposure"
        ),
        max_leverage=_parse_optional_decimal(payload.get("max_leverage"), field="max_leverage"),
        max_open_positions=_parse_optional_non_negative_int(
            payload.get("max_open_positions"), field="max_open_positions"
        ),
        max_submitted_orders=_parse_optional_non_negative_int(
            payload.get("max_submitted_orders"), field="max_submitted_orders"
        ),
        max_session_capital_commitment=_parse_optional_decimal(
            payload.get("max_session_capital_commitment"), field="max_session_capital_commitment"
        ),
        scale_in_forbidden=_parse_strict_flag(
            payload.get("scale_in_forbidden"), field="scale_in_forbidden", default=True
        ),
        automatic_retry_forbidden=_parse_strict_flag(
            payload.get("automatic_retry_forbidden"),
            field="automatic_retry_forbidden",
            default=True,
        ),
        fee_buffer_usdc=_parse_optional_decimal(
            payload.get("fee_buffer_usdc"), field="fee_buffer_usdc"
        ),
        max_new_orders=_parse_required_non_negative_int(
            payload.get("max_new_orders"), field="max_new_orders"
        ),
        max_new_positions=_parse_required_non_negative_int(
            payload.get("max_new_positions"), field="max_new_positions"
        ),
        config_digest=str(config_digest or "").strip().lower(),
    )


def offline_proof_guard_config_v1(
    *, config_digest: str = "offline_proof_not_owner_ratified"
) -> CanaryCapitalGuardConfigV1:
    """Test/offline-proof fixture only — not Owner-ratified production authority."""
    return CanaryCapitalGuardConfigV1(
        schema_version=SCHEMA_VERSION,
        live_canary_allowed=True,
        owner_caps_ratified=False,
        currency="USDC",
        max_single_order_notional=Decimal("100"),
        max_incremental_initial_margin=Decimal("100"),
        max_aggregate_exposure=Decimal("100"),
        max_leverage=Decimal("20"),
        max_open_positions=1,
        max_submitted_orders=1,
        max_session_capital_commitment=Decimal("100"),
        scale_in_forbidden=True,
        automatic_retry_forbidden=True,
        fee_buffer_usdc=Decimal("1"),
        max_new_orders=1,
        max_new_positions=1,
        config_digest=config_digest,
    )


@dataclass(frozen=True)
class CanaryCapitalGuardMarginEvidenceV1:
    avail_eq_usdc: str | None
    imr_rate: str | None
    imr_source_class: str | None = None
    pretrade_decision_id: str | None = None
    expected_pretrade_decision_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "avail_eq_usdc": self.avail_eq_usdc,
            "imr_rate": self.imr_rate,
            "imr_source_class": self.imr_source_class,
            "pretrade_decision_id": self.pretrade_decision_id,
            "expected_pretrade_decision_id": self.expected_pretrade_decision_id,
        }


@dataclass(frozen=True)
class CanaryCapitalGuardExposureEvidenceV1:
    open_order_count: int
    open_position_count: int
    unknown_submit_active: bool
    recovery_state_clear: bool
    transport_retry_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "open_order_count": self.open_order_count,
            "open_position_count": self.open_position_count,
            "unknown_submit_active": self.unknown_submit_active,
            "recovery_state_clear": self.recovery_state_clear,
            "transport_retry_count": self.transport_retry_count,
        }


@dataclass
class CanaryCapitalGuardSessionV1:
    session_id: str
    account_scope: str
    instrument_id: str
    owner_go: str
    guard_config_digest: str
    entry_submit_count: int = 0
    unknown_submit_locked: bool = False
    consumed_plan_digests: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "account_scope": self.account_scope,
            "instrument_id": self.instrument_id,
            "owner_go": self.owner_go,
            "guard_config_digest": self.guard_config_digest,
            "entry_submit_count": self.entry_submit_count,
            "unknown_submit_locked": self.unknown_submit_locked,
            "consumed_plan_digests": list(self.consumed_plan_digests),
        }


_guard_session_var: ContextVar[CanaryCapitalGuardSessionV1 | None] = ContextVar(
    "canary_capital_guard_session_v1",
    default=None,
)


def bind_canary_capital_guard_session_v1(
    session: CanaryCapitalGuardSessionV1 | None,
) -> _CtxReset:
    return _guard_session_var.set(session)


def active_canary_capital_guard_session_v1() -> CanaryCapitalGuardSessionV1 | None:
    return _guard_session_var.get()


def compute_order_notional_usdc_v1(
    *,
    quantity: str,
    contract_value: str,
    reference_price: str,
) -> Decimal:
    qty = _require_positive_cap(quantity, field="quantity")
    ct = _require_positive_cap(contract_value, field="contract_value")
    px = _require_positive_cap(reference_price, field="reference_price")
    return qty * ct * px


def compute_conservative_initial_margin_usdc_v1(
    *,
    order_notional: Decimal,
    imr_rate: Decimal,
    fee_buffer_usdc: Decimal,
) -> Decimal:
    if imr_rate <= 0 or imr_rate > Decimal("1"):
        raise CanaryCapitalGuardError("IMR_RATE_OUT_OF_CONSERVATIVE_RANGE")
    if fee_buffer_usdc < 0:
        raise CanaryCapitalGuardError("FEE_BUFFER_NEGATIVE")
    return order_notional * imr_rate + fee_buffer_usdc


def extract_imr_from_instruments_payload_v1(
    *,
    instruments_payload: Mapping[str, Any],
    instrument_id: str,
) -> str | None:
    """Deprecated for guard authority — instruments.imr is not admissible IMR."""
    _ = (instruments_payload, instrument_id)
    return None


def bind_imr_from_public_position_tiers_payload_v1(
    *,
    position_tiers_payload: Mapping[str, Any],
    expected_inst_family: str,
) -> str:
    from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.cover_usdc_current_public_tier_mmr_productive_evidence_v1 import (
        extract_qty_one_mmr_from_public_position_tiers_payload_v1,
    )

    _mmr, imr, _tier, _min_sz, _max_sz, _family = (
        extract_qty_one_mmr_from_public_position_tiers_payload_v1(
            position_tiers_payload,
            expected_inst_family=expected_inst_family,
        )
    )
    return imr


def extract_avail_eq_usdc_from_balance_payload_v1(payload: Mapping[str, Any]) -> str | None:
    if str(payload.get("code") or "") != "0":
        return None
    data = payload.get("data")
    if not isinstance(data, list) or not data:
        return None
    details = data[0].get("details") if isinstance(data[0], Mapping) else None
    if not isinstance(details, list):
        return None
    for row in details:
        if not isinstance(row, Mapping):
            continue
        if str(row.get("ccy") or "").upper() != "USDC":
            continue
        avail = row.get("availEq")
        if avail is None or str(avail).strip() == "":
            return None
        return str(avail).strip()
    return None


def extract_leverage_from_leverage_payload_v1(
    *,
    leverage_payload: Mapping[str, Any],
    instrument_id: str,
) -> str | None:
    if str(leverage_payload.get("code") or "") != "0":
        return None
    data = leverage_payload.get("data")
    if not isinstance(data, list):
        return None
    for row in data:
        if not isinstance(row, Mapping):
            continue
        if str(row.get("instId") or "") != instrument_id and str(row.get("instFamily") or ""):
            pass
        lever = row.get("lever")
        if lever is not None and str(lever).strip():
            return str(lever).strip()
    if data and isinstance(data[0], Mapping):
        lever = data[0].get("lever")
        if lever is not None and str(lever).strip():
            return str(lever).strip()
    return None


def _assert_caps_present(config: CanaryCapitalGuardConfigV1, reasons: list[str]) -> None:
    for name, value in (
        ("max_single_order_notional", config.max_single_order_notional),
        ("max_incremental_initial_margin", config.max_incremental_initial_margin),
        ("max_aggregate_exposure", config.max_aggregate_exposure),
        ("max_leverage", config.max_leverage),
        ("max_session_capital_commitment", config.max_session_capital_commitment),
        ("fee_buffer_usdc", config.fee_buffer_usdc),
    ):
        if value is None:
            reasons.append(f"MISSING_NUMERIC_CAP:{name}")
    if config.max_open_positions is None:
        reasons.append("MISSING_NUMERIC_CAP:max_open_positions")
    if config.max_submitted_orders is None:
        reasons.append("MISSING_NUMERIC_CAP:max_submitted_orders")


@dataclass(frozen=True)
class CanaryCapitalGuardEvaluationV1:
    guard_allowed: bool
    reasons: tuple[str, ...]
    requested_notional_usdc: str | None
    required_initial_margin_usdc: str | None
    observed_leverage: str | None
    plan_digest: str
    guard_config_digest: str
    session_id: str | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "GUARD_ALLOWED": self.guard_allowed,
            "REASONS": list(self.reasons),
            "requested_notional_usdc": self.requested_notional_usdc,
            "required_initial_margin_usdc": self.required_initial_margin_usdc,
            "observed_leverage": self.observed_leverage,
            "plan_digest": self.plan_digest,
            "guard_config_digest": self.guard_config_digest,
            "session_id": self.session_id,
            "contract_id": CONTRACT_ID,
        }


def evaluate_canary_capital_guard_entry_v1(
    *,
    plan: CanaryOrderPlanV1,
    guard_config: CanaryCapitalGuardConfigV1,
    margin_evidence: CanaryCapitalGuardMarginEvidenceV1,
    exposure_evidence: CanaryCapitalGuardExposureEvidenceV1,
    owner_go: str | None,
    account_scope: str,
    session: CanaryCapitalGuardSessionV1 | None,
    expected_config_digest: str | None = None,
    observed_leverage: str | None = None,
    durable_entry_state: str | None = None,
    required_owner_go: str | None = None,
    enforce_canary_operative_contract_quantity: bool = True,
) -> CanaryCapitalGuardEvaluationV1:
    reasons: list[str] = []
    plan_digest = compute_canary_plan_digest_v1(plan_payload=plan.to_dict())

    if not guard_config.live_canary_allowed:
        reasons.append("LIVE_CANARY_ALLOWED_FALSE")
    if not guard_config.owner_caps_ratified:
        reasons.append("OWNER_CAPS_UNRATIFIED")
    _assert_caps_present(guard_config, reasons)

    expected_digest = str(expected_config_digest or guard_config.config_digest).strip().lower()
    if guard_config.config_digest != expected_digest:
        reasons.append("GUARD_CONFIG_DIGEST_MISMATCH")
    if durable_entry_state is not None and durable_entry_state not in {
        "AVAILABLE",
        "",
    }:
        reasons.append(f"DURABLE_ENTRY_SLOT_UNAVAILABLE:{durable_entry_state}")

    go = str(owner_go or "").strip()
    expected_go = str(required_owner_go or OWNER_GO_EXECUTE).strip()
    if not go:
        reasons.append("OWNER_PERMIT_MISSING")
    elif go != expected_go:
        reasons.append(f"OWNER_GO_MISMATCH:{go}")

    if session is not None:
        if session.account_scope != account_scope:
            reasons.append("SESSION_ACCOUNT_SCOPE_MISMATCH")
        if session.instrument_id != plan.instrument_id:
            reasons.append("SESSION_INSTRUMENT_MISMATCH")
        if session.owner_go != go:
            reasons.append("SESSION_OWNER_GO_MISMATCH")
        if session.guard_config_digest != guard_config.config_digest:
            reasons.append("SESSION_GUARD_CONFIG_DIGEST_MISMATCH")
        if session.unknown_submit_locked:
            reasons.append("UNKNOWN_SUBMIT_SESSION_LOCKED")
        if plan_digest in session.consumed_plan_digests:
            reasons.append("DUPLICATE_PLAN_DIGEST")

    if guard_config.max_new_orders == 0:
        reasons.append("ENTRY_BLOCKED:MAX_NEW_ORDERS_ZERO")
    elif session is not None and session.entry_submit_count >= guard_config.max_new_orders:
        reasons.append("MAX_NEW_ORDERS_EXCEEDED")

    if guard_config.max_new_positions == 0:
        reasons.append("ENTRY_BLOCKED:MAX_NEW_POSITIONS_ZERO")
    elif exposure_evidence.open_position_count >= guard_config.max_new_positions:
        reasons.append("MAX_NEW_POSITIONS_EXCEEDED")

    if guard_config.automatic_retry_forbidden and exposure_evidence.transport_retry_count > 0:
        reasons.append("AUTOMATIC_RETRY_FORBIDDEN")

    if exposure_evidence.unknown_submit_active:
        reasons.append("UNKNOWN_SUBMIT_ACTIVE")
    if not exposure_evidence.recovery_state_clear:
        reasons.append("RECOVERY_STATE_UNCLEAR")

    if exposure_evidence.open_order_count > 0:
        reasons.append("OPEN_ORDER_PRESENT")
    if exposure_evidence.open_position_count > 0:
        reasons.append("OPEN_POSITION_PRESENT")
    max_pos = guard_config.max_open_positions
    if max_pos is not None and exposure_evidence.open_position_count > int(max_pos):
        reasons.append("MAX_OPEN_POSITIONS_EXCEEDED")

    if enforce_canary_operative_contract_quantity:
        operative = canary_venue_contract_count_v1()
        if guard_config.scale_in_forbidden and str(plan.quantity) != operative:
            reasons.append("SCALE_IN_FORBIDDEN")

    # Instrument metadata validation (fail-closed).
    try:
        qty = _dec(plan.quantity, field="quantity")
        min_sz = _dec(plan.min_sz, field="min_sz")
        lot = _dec(plan.lot_sz, field="lot_sz")
        if qty < min_sz:
            reasons.append("QUANTITY_BELOW_MIN_SZ")
        if lot > 0 and (qty % lot) != 0:
            reasons.append("QUANTITY_NOT_LOT_ALIGNED")
        _require_positive_cap(plan.ct_val, field="ct_val")
        _require_positive_cap(plan.limit_price, field="limit_price")
    except CanaryCapitalGuardError as exc:
        reasons.append(str(exc))

    requested_notional: Decimal | None = None
    required_margin: Decimal | None = None
    try:
        requested_notional = compute_order_notional_usdc_v1(
            quantity=plan.quantity,
            contract_value=plan.ct_val,
            reference_price=plan.limit_price,
        )
    except CanaryCapitalGuardError as exc:
        reasons.append(str(exc))

    if margin_evidence.imr_rate is None or str(margin_evidence.imr_rate).strip() == "":
        reasons.append("MISSING_IMR_EVIDENCE")
    elif margin_evidence.imr_source_class != IMR_SOURCE_PUBLIC_POSITION_TIERS_QTY_ONE:
        reasons.append("IMR_SOURCE_NOT_AUTHORITATIVE")
    if margin_evidence.avail_eq_usdc is None or str(margin_evidence.avail_eq_usdc).strip() == "":
        reasons.append("MISSING_AVAILABLE_MARGIN_EVIDENCE")
    expected_pt = str(margin_evidence.expected_pretrade_decision_id or "").strip()
    bound_pt = str(margin_evidence.pretrade_decision_id or "").strip()
    if expected_pt and bound_pt and expected_pt != bound_pt:
        reasons.append("STALE_MARGIN_EVIDENCE_PRETRADE_MISMATCH")
    if guard_config.fee_buffer_usdc is None:
        reasons.append("MISSING_FEE_BUFFER_CAP")

    lev_raw = observed_leverage
    if lev_raw is None or str(lev_raw).strip() == "":
        reasons.append("MISSING_LEVERAGE_EVIDENCE")
    else:
        try:
            lever = _require_positive_cap(lev_raw, field="leverage")
            if guard_config.max_leverage is not None and lever > guard_config.max_leverage:
                reasons.append("MAX_LEVERAGE_EXCEEDED")
        except CanaryCapitalGuardError as exc:
            reasons.append(str(exc))

    if (
        requested_notional is not None
        and margin_evidence.imr_rate is not None
        and guard_config.fee_buffer_usdc is not None
    ):
        try:
            imr = _require_positive_cap(margin_evidence.imr_rate, field="imr_rate")
            required_margin = compute_conservative_initial_margin_usdc_v1(
                order_notional=requested_notional,
                imr_rate=imr,
                fee_buffer_usdc=guard_config.fee_buffer_usdc,
            )
            if guard_config.max_single_order_notional is not None:
                if requested_notional > guard_config.max_single_order_notional:
                    reasons.append("MAX_SINGLE_ORDER_NOTIONAL_EXCEEDED")
            if guard_config.max_incremental_initial_margin is not None:
                if required_margin > guard_config.max_incremental_initial_margin:
                    reasons.append("MAX_INCREMENTAL_INITIAL_MARGIN_EXCEEDED")
            if guard_config.max_aggregate_exposure is not None:
                if requested_notional > guard_config.max_aggregate_exposure:
                    reasons.append("MAX_AGGREGATE_EXPOSURE_EXCEEDED")
            if guard_config.max_session_capital_commitment is not None:
                if requested_notional > guard_config.max_session_capital_commitment:
                    reasons.append("MAX_SESSION_CAPITAL_COMMITMENT_EXCEEDED")
            if margin_evidence.avail_eq_usdc is not None:
                avail = _dec(margin_evidence.avail_eq_usdc, field="avail_eq_usdc")
                if required_margin > avail:
                    reasons.append("REQUIRED_MARGIN_EXCEEDS_AVAIL_EQ")
        except CanaryCapitalGuardError as exc:
            reasons.append(str(exc))

    allowed = len(reasons) == 0
    return CanaryCapitalGuardEvaluationV1(
        guard_allowed=allowed,
        reasons=tuple(dict.fromkeys(reasons)),
        requested_notional_usdc=(
            None if requested_notional is None else format(requested_notional, "f")
        ),
        required_initial_margin_usdc=(
            None if required_margin is None else format(required_margin, "f")
        ),
        observed_leverage=lev_raw,
        plan_digest=plan_digest,
        guard_config_digest=guard_config.config_digest,
        session_id=None if session is None else session.session_id,
    )


def refuse_canary_capital_guard_entry_unless_pass_v1(
    evaluation: CanaryCapitalGuardEvaluationV1,
) -> None:
    if evaluation.guard_allowed:
        return
    joined = ",".join(evaluation.reasons) or "UNKNOWN"
    raise CanaryCapitalGuardError(f"CANARY_CAPITAL_GUARD_BLOCKED:{joined}")


def record_canary_capital_guard_entry_attempt_v1(
    *,
    session: CanaryCapitalGuardSessionV1,
    plan_digest: str,
    unknown_submit: bool = False,
) -> CanaryCapitalGuardSessionV1:
    consumed = list(session.consumed_plan_digests)
    if plan_digest not in consumed:
        consumed.append(plan_digest)
    return replace(
        session,
        entry_submit_count=session.entry_submit_count + 1,
        unknown_submit_locked=session.unknown_submit_locked or unknown_submit,
        consumed_plan_digests=consumed,
    )


@dataclass(frozen=True)
class CanaryCapitalGuardFlattenEvaluationV1:
    guard_allowed: bool
    reasons: tuple[str, ...]
    plan_digest: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "GUARD_ALLOWED": self.guard_allowed,
            "REASONS": list(self.reasons),
            "plan_digest": self.plan_digest,
            "flatten_mode": True,
            "contract_id": CONTRACT_ID,
        }


def evaluate_canary_capital_guard_flatten_v1(
    *,
    plan: CanaryFlattenOrderPlanV1,
    signed_pos: Decimal,
    reduce_only_confirmed: bool,
) -> CanaryCapitalGuardFlattenEvaluationV1:
    reasons: list[str] = []
    plan_digest = compute_canary_plan_digest_v1(plan_payload=plan.to_dict())
    if not reduce_only_confirmed:
        reasons.append("FLATTEN_REDUCE_ONLY_REQUIRED")
    try:
        flatten_qty = _require_positive_cap(plan.quantity, field="flatten_quantity")
        if flatten_qty > abs(signed_pos):
            reasons.append("FLATTEN_EXCEEDS_OBSERVED_POSITION")
        if signed_pos == 0:
            reasons.append("FLATTEN_NO_OPEN_POSITION")
    except CanaryCapitalGuardError as exc:
        reasons.append(str(exc))
    allowed = len(reasons) == 0
    return CanaryCapitalGuardFlattenEvaluationV1(
        guard_allowed=allowed,
        reasons=tuple(dict.fromkeys(reasons)),
        plan_digest=plan_digest,
    )


def refuse_canary_capital_guard_flatten_unless_pass_v1(
    evaluation: CanaryCapitalGuardFlattenEvaluationV1,
) -> None:
    if evaluation.guard_allowed:
        return
    joined = ",".join(evaluation.reasons) or "UNKNOWN"
    raise CanaryCapitalGuardError(f"CANARY_CAPITAL_GUARD_FLATTEN_BLOCKED:{joined}")


def build_default_guard_session_v1(
    *,
    session_id: str,
    account_scope: str = REUSED_BINDING_ACCOUNT_SCOPE,
    instrument_id: str,
    owner_go: str,
    guard_config: CanaryCapitalGuardConfigV1,
) -> CanaryCapitalGuardSessionV1:
    return CanaryCapitalGuardSessionV1(
        session_id=str(session_id),
        account_scope=str(account_scope),
        instrument_id=str(instrument_id),
        owner_go=str(owner_go),
        guard_config_digest=guard_config.config_digest,
    )


__all__ = [
    "CONTRACT_ID",
    "CanaryCapitalGuardConfigV1",
    "CanaryCapitalGuardError",
    "CanaryCapitalGuardEvaluationV1",
    "CanaryCapitalGuardExposureEvidenceV1",
    "CanaryCapitalGuardFlattenEvaluationV1",
    "CanaryCapitalGuardMarginEvidenceV1",
    "CanaryCapitalGuardSessionV1",
    "active_canary_capital_guard_session_v1",
    "IMR_SOURCE_PUBLIC_POSITION_TIERS_QTY_ONE",
    "bind_canary_capital_guard_session_v1",
    "bind_imr_from_public_position_tiers_payload_v1",
    "build_default_guard_session_v1",
    "compute_canary_plan_digest_v1",
    "compute_conservative_initial_margin_usdc_v1",
    "compute_order_notional_usdc_v1",
    "evaluate_canary_capital_guard_entry_v1",
    "evaluate_canary_capital_guard_flatten_v1",
    "extract_avail_eq_usdc_from_balance_payload_v1",
    "extract_imr_from_instruments_payload_v1",
    "extract_leverage_from_leverage_payload_v1",
    "load_canary_capital_guard_config_v1",
    "offline_proof_guard_config_v1",
    "parse_canary_capital_guard_config_v1",
    "parse_optional_finite_decimal_cap_v1",
    "record_canary_capital_guard_entry_attempt_v1",
    "refuse_canary_capital_guard_entry_unless_pass_v1",
    "refuse_canary_capital_guard_flatten_unless_pass_v1",
]
