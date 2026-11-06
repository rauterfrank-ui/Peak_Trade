"""Independent fail-closed Full-Core capital guard (CURRENT_FULL_CORE_CAPITAL_GUARD_V1).

Reuses numeric rule evaluation from CURRENT_LIVE_CANARY_CAPITAL_GUARD_V1 without
authorizing live POST. Does not resize quantities or alter strategy semantics.
RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, replace
from decimal import Decimal
from pathlib import Path
from typing import Any, Mapping

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    OWNER_GO_EXECUTE as CANARY_OWNER_GO_EXECUTE,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.current_live_canary_capital_guard_v1 import (
    CanaryCapitalGuardConfigV1,
    CanaryCapitalGuardError,
    CanaryCapitalGuardEvaluationV1,
    CanaryCapitalGuardExposureEvidenceV1,
    CanaryCapitalGuardMarginEvidenceV1,
    CanaryCapitalGuardSessionV1,
    compute_canary_plan_digest_v1,
    evaluate_canary_capital_guard_entry_v1,
    parse_canary_capital_guard_config_v1,
)

CONTRACT_ID = "CURRENT_FULL_CORE_CAPITAL_GUARD_V1"
SCHEMA_VERSION = "current_full_core_capital_guard.v1"
DEFAULT_CONFIG_REL_PATH = "config/ops/current_full_core_capital_guard_v1.json"

OWNER_GO_FULL_CORE_PRE_POST = "OWNER_GO_CURRENT_FULL_CORE_PRE_POST_CAPITAL_GUARD_JOIN_V1"

GUARD_AUTHORITY_EFFECT = "NONE"


class FullCoreCapitalGuardError(RuntimeError):
    """Fail-closed Full-Core capital guard violation."""


@dataclass(frozen=True)
class FullCoreCapitalGuardConfigV1:
    schema_version: str
    full_core_guard_join_enabled: bool
    owner_caps_ratified: bool
    currency: str
    max_single_order_notional: Decimal | None
    max_incremental_initial_margin: Decimal | None
    max_aggregate_exposure: Decimal | None
    max_leverage: Decimal | None
    max_open_positions: int | None
    max_submitted_orders: int | None
    max_session_capital_commitment: Decimal | None
    max_existing_exposure: Decimal | None
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
            "full_core_guard_join_enabled": self.full_core_guard_join_enabled,
            "owner_caps_ratified": self.owner_caps_ratified,
            "currency": self.currency,
            "max_single_order_notional": _fmt(self.max_single_order_notional),
            "max_incremental_initial_margin": _fmt(self.max_incremental_initial_margin),
            "max_aggregate_exposure": _fmt(self.max_aggregate_exposure),
            "max_leverage": _fmt(self.max_leverage),
            "max_open_positions": self.max_open_positions,
            "max_submitted_orders": self.max_submitted_orders,
            "max_session_capital_commitment": _fmt(self.max_session_capital_commitment),
            "max_existing_exposure": _fmt(self.max_existing_exposure),
            "scale_in_forbidden": self.scale_in_forbidden,
            "automatic_retry_forbidden": self.automatic_retry_forbidden,
            "fee_buffer_usdc": _fmt(self.fee_buffer_usdc),
            "max_new_orders": self.max_new_orders,
            "max_new_positions": self.max_new_positions,
            "config_digest": self.config_digest,
        }


def _as_canary_config(cfg: FullCoreCapitalGuardConfigV1) -> CanaryCapitalGuardConfigV1:
    return CanaryCapitalGuardConfigV1(
        schema_version="current_live_canary_capital_guard.v1",
        live_canary_allowed=cfg.full_core_guard_join_enabled,
        owner_caps_ratified=cfg.owner_caps_ratified,
        currency=cfg.currency,
        max_single_order_notional=cfg.max_single_order_notional,
        max_incremental_initial_margin=cfg.max_incremental_initial_margin,
        max_aggregate_exposure=cfg.max_aggregate_exposure,
        max_leverage=cfg.max_leverage,
        max_open_positions=cfg.max_open_positions,
        max_submitted_orders=cfg.max_submitted_orders,
        max_session_capital_commitment=cfg.max_session_capital_commitment,
        scale_in_forbidden=cfg.scale_in_forbidden,
        automatic_retry_forbidden=cfg.automatic_retry_forbidden,
        fee_buffer_usdc=cfg.fee_buffer_usdc,
        max_new_orders=cfg.max_new_orders,
        max_new_positions=cfg.max_new_positions,
        config_digest=cfg.config_digest,
    )


def load_full_core_capital_guard_config_v1(
    *,
    repo_root: Path | None = None,
    config_path: Path | None = None,
) -> FullCoreCapitalGuardConfigV1:
    root = repo_root or Path(__file__).resolve().parents[3]
    path = config_path or (root / DEFAULT_CONFIG_REL_PATH)
    raw_text = path.read_text(encoding="utf-8")
    payload = json.loads(raw_text)
    if not isinstance(payload, Mapping):
        raise FullCoreCapitalGuardError("GUARD_CONFIG_NOT_MAPPING")
    digest = hashlib.sha256(raw_text.encode("utf-8")).hexdigest()
    return parse_full_core_capital_guard_config_v1(payload, config_digest=digest)


def parse_full_core_capital_guard_config_v1(
    payload: Mapping[str, Any],
    *,
    config_digest: str,
) -> FullCoreCapitalGuardConfigV1:
    schema = str(payload.get("schema_version") or "").strip()
    if schema != SCHEMA_VERSION:
        raise FullCoreCapitalGuardError(f"GUARD_SCHEMA_MISMATCH:{schema or '<empty>'}")
    canary = parse_canary_capital_guard_config_v1(
        {
            **payload,
            "schema_version": "current_live_canary_capital_guard.v1",
            "live_canary_allowed": payload.get("full_core_guard_join_enabled"),
        },
        config_digest=config_digest,
    )
    max_existing = payload.get("max_existing_exposure")
    existing_dec: Decimal | None
    if max_existing is None:
        existing_dec = None
    else:
        existing_dec = Decimal(str(max_existing))
    return FullCoreCapitalGuardConfigV1(
        schema_version=schema,
        full_core_guard_join_enabled=bool(payload.get("full_core_guard_join_enabled")),
        owner_caps_ratified=canary.owner_caps_ratified,
        currency=canary.currency,
        max_single_order_notional=canary.max_single_order_notional,
        max_incremental_initial_margin=canary.max_incremental_initial_margin,
        max_aggregate_exposure=canary.max_aggregate_exposure,
        max_leverage=canary.max_leverage,
        max_open_positions=canary.max_open_positions,
        max_submitted_orders=canary.max_submitted_orders,
        max_session_capital_commitment=canary.max_session_capital_commitment,
        max_existing_exposure=existing_dec,
        scale_in_forbidden=canary.scale_in_forbidden,
        automatic_retry_forbidden=canary.automatic_retry_forbidden,
        fee_buffer_usdc=canary.fee_buffer_usdc,
        max_new_orders=canary.max_new_orders,
        max_new_positions=canary.max_new_positions,
        config_digest=canary.config_digest,
    )


def offline_proof_full_core_guard_config_v1(
    *, config_digest: str = "offline_proof_not_owner_ratified"
) -> FullCoreCapitalGuardConfigV1:
    return FullCoreCapitalGuardConfigV1(
        schema_version=SCHEMA_VERSION,
        full_core_guard_join_enabled=True,
        owner_caps_ratified=False,
        currency="USDC",
        max_single_order_notional=Decimal("1000"),
        max_incremental_initial_margin=Decimal("500"),
        max_aggregate_exposure=Decimal("1000"),
        max_leverage=Decimal("20"),
        max_open_positions=1,
        max_submitted_orders=1,
        max_session_capital_commitment=Decimal("1000"),
        max_existing_exposure=Decimal("500"),
        scale_in_forbidden=True,
        automatic_retry_forbidden=True,
        fee_buffer_usdc=Decimal("1"),
        max_new_orders=1,
        max_new_positions=1,
        config_digest=config_digest,
    )


@dataclass(frozen=True)
class FullCoreCapitalGuardOrderPlanV1:
    instrument_id: str
    native_id: str
    side: str
    order_type: str
    quantity: str
    limit_price: str
    min_sz: str
    lot_sz: str
    ct_val: str
    clordid: str

    def to_guard_plan_dict_v1(self) -> dict[str, Any]:
        return {
            "instrument_id": self.instrument_id,
            "side": self.side,
            "order_type": self.order_type,
            "quantity": self.quantity,
            "limit_price": self.limit_price,
            "min_sz": self.min_sz,
            "lot_sz": self.lot_sz,
            "ct_val": self.ct_val,
            "clordid": self.clordid,
        }


@dataclass(frozen=True)
class FullCoreCapitalGuardEvaluationV1:
    guard_allowed: bool
    reasons: tuple[str, ...]
    plan_digest: str
    guard_config_digest: str
    requested_notional_usdc: str | None
    required_initial_margin_usdc: str | None
    observed_leverage: str | None
    session_id: str | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "GUARD_ALLOWED": self.guard_allowed,
            "REASONS": list(self.reasons),
            "plan_digest": self.plan_digest,
            "guard_config_digest": self.guard_config_digest,
            "requested_notional_usdc": self.requested_notional_usdc,
            "required_initial_margin_usdc": self.required_initial_margin_usdc,
            "observed_leverage": self.observed_leverage,
            "session_id": self.session_id,
            "contract_id": CONTRACT_ID,
        }


def evaluate_full_core_capital_guard_entry_v1(
    *,
    plan: FullCoreCapitalGuardOrderPlanV1,
    guard_config: FullCoreCapitalGuardConfigV1,
    margin_evidence: CanaryCapitalGuardMarginEvidenceV1,
    exposure_evidence: CanaryCapitalGuardExposureEvidenceV1,
    owner_go: str | None,
    account_scope: str,
    session: CanaryCapitalGuardSessionV1 | None,
    observed_leverage: str | None = None,
    durable_entry_state: str | None = None,
    existing_exposure_notional_usdc: str | None = None,
) -> FullCoreCapitalGuardEvaluationV1:
    go = str(owner_go or "").strip()
    reasons_prefix: list[str] = []
    if go == CANARY_OWNER_GO_EXECUTE:
        reasons_prefix.append("CANARY_OWNER_GO_FORBIDDEN_FOR_FULL_CORE")
    if not guard_config.full_core_guard_join_enabled:
        reasons_prefix.append("FULL_CORE_GUARD_JOIN_DISABLED")
    if guard_config.max_existing_exposure is None:
        reasons_prefix.append("MISSING_NUMERIC_CAP:max_existing_exposure")

    from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.order_plan_v1 import (
        CanaryOrderPlanV1,
    )

    canary_plan = CanaryOrderPlanV1(
        instrument_id=plan.instrument_id,
        side=plan.side,
        order_type=plan.order_type,
        td_mode="cross",
        quantity=plan.quantity,
        quantity_domain="VENUE_CONTRACT_COUNT",
        quantity_unit="contracts",
        limit_price=plan.limit_price,
        min_sz=plan.min_sz,
        lot_sz=plan.lot_sz,
        tick_sz="0.0001",
        ct_val=plan.ct_val,
        ct_val_ccy="USDC",
        min_executable_notional="1",
        max_notional="999999",
        clordid=plan.clordid,
        venue_native_payload={"instId": plan.instrument_id, "sz": plan.quantity, "side": plan.side},
    )
    try:
        canary_eval = evaluate_canary_capital_guard_entry_v1(
            plan=canary_plan,
            guard_config=_as_canary_config(guard_config),
            margin_evidence=margin_evidence,
            exposure_evidence=exposure_evidence,
            owner_go=owner_go,
            account_scope=account_scope,
            session=session,
            observed_leverage=observed_leverage,
            durable_entry_state=durable_entry_state,
            required_owner_go=OWNER_GO_FULL_CORE_PRE_POST,
            enforce_canary_operative_contract_quantity=False,
        )
    except CanaryCapitalGuardError as exc:
        raise FullCoreCapitalGuardError(str(exc)) from exc

    reasons = list(reasons_prefix) + list(canary_eval.reasons)
    if (
        guard_config.max_existing_exposure is not None
        and existing_exposure_notional_usdc is not None
        and existing_exposure_notional_usdc.strip()
    ):
        try:
            existing = Decimal(str(existing_exposure_notional_usdc))
            cap = guard_config.max_existing_exposure
            if existing > cap:
                reasons.append("MAX_EXISTING_EXPOSURE_EXCEEDED")
            if canary_eval.requested_notional_usdc is not None:
                req = Decimal(str(canary_eval.requested_notional_usdc))
                if existing + req > guard_config.max_aggregate_exposure:
                    if guard_config.max_aggregate_exposure is not None:
                        reasons.append("AGGREGATE_EXPOSURE_WITH_EXISTING_EXCEEDED")
        except Exception:
            reasons.append("INVALID_EXISTING_EXPOSURE_EVIDENCE")

    reasons = tuple(dict.fromkeys(reasons))
    allowed = len(reasons) == 0
    return FullCoreCapitalGuardEvaluationV1(
        guard_allowed=allowed,
        reasons=reasons,
        plan_digest=canary_eval.plan_digest,
        guard_config_digest=canary_eval.guard_config_digest,
        requested_notional_usdc=canary_eval.requested_notional_usdc,
        required_initial_margin_usdc=canary_eval.required_initial_margin_usdc,
        observed_leverage=canary_eval.observed_leverage,
        session_id=canary_eval.session_id,
    )


def refuse_full_core_capital_guard_entry_unless_pass_v1(
    evaluation: FullCoreCapitalGuardEvaluationV1,
) -> None:
    if evaluation.guard_allowed:
        return
    joined = ",".join(evaluation.reasons) or "UNKNOWN"
    raise FullCoreCapitalGuardError(f"FULL_CORE_CAPITAL_GUARD_BLOCKED:{joined}")


def compute_full_core_guard_plan_digest_v1(*, plan_payload: Mapping[str, Any]) -> str:
    return compute_canary_plan_digest_v1(plan_payload=plan_payload)


def ratified_offline_full_core_guard_config_v1() -> FullCoreCapitalGuardConfigV1:
    return replace(offline_proof_full_core_guard_config_v1(), owner_caps_ratified=True)


def adapt_full_core_guard_config_to_canary_v1(
    cfg: FullCoreCapitalGuardConfigV1,
) -> CanaryCapitalGuardConfigV1:
    return _as_canary_config(cfg)


__all__ = [
    "CONTRACT_ID",
    "FullCoreCapitalGuardConfigV1",
    "FullCoreCapitalGuardError",
    "FullCoreCapitalGuardEvaluationV1",
    "FullCoreCapitalGuardOrderPlanV1",
    "OWNER_GO_FULL_CORE_PRE_POST",
    "adapt_full_core_guard_config_to_canary_v1",
    "compute_full_core_guard_plan_digest_v1",
    "evaluate_full_core_capital_guard_entry_v1",
    "load_full_core_capital_guard_config_v1",
    "offline_proof_full_core_guard_config_v1",
    "parse_full_core_capital_guard_config_v1",
    "ratified_offline_full_core_guard_config_v1",
    "refuse_full_core_capital_guard_entry_unless_pass_v1",
]
