"""Canonical Integrated Paper-Shadow Observation cycle entrypoint v1.

Offline, observation-only. Uses caller-supplied market ticks and the simulated
portfolio economics model. Never contacts brokers, never starts wallclock
sessions, never grants authorization.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from decimal import Decimal
from typing import Any, Mapping, Optional, Sequence

from src.ops.bounded_futures_testnet_venue_binding_v0 import (
    PRODUCTION_INSTRUMENT_ID,
    VENUE_OKX_EUROPE,
    default_okx_europe_xperp_production_binding,
    evaluate_okx_europe_xperp_binding,
)
from src.ops.integrated_paper_shadow_observation_session_v1.constants_v1 import (
    AUTHORITY_EFFECT_NONE,
    CAPABILITY_ID,
    PACKAGE_MARKER,
    PRODUCER_FAMILY,
    REQUIRED_MODE,
    SCHEMA_VERSION,
)
from src.ops.integrated_paper_shadow_observation_session_v1.market_data_policy_v1 import (
    MarketDataPolicyParamsV1,
    ObservationMarketTickV1,
    evaluate_market_data_sequence_v1,
    validate_instrument_for_observation_v1,
)
from src.ops.integrated_paper_shadow_observation_session_v1.no_order_guard_v1 import (
    assert_observation_request_no_order_v1,
    reject_broker_write_attempt_v1,
    reject_order_attempt_v1,
)
from src.ops.integrated_paper_shadow_observation_session_v1.portfolio_economics_model_v1 import (
    PORTFOLIO_ECONOMICS_MODEL_ID,
    SimulatedPortfolioEconomicsModelV1,
)
from src.ops.okx_futures_shadow_no_order_entrypoint_v0 import (
    run_okx_futures_shadow_no_order_cycle_core_v0,
)

ENTRYPOINT_OWNER = "ops.integrated_paper_shadow_observation_session_entrypoint_v1"
CLI_RELPATH = "scripts/ops/run_integrated_paper_shadow_observation_session_contract_v1.py"


class ObservationEntrypointError(ValueError):
    """Fail-closed observation entrypoint error."""


@dataclass
class ObservationCycleResultV1:
    terminal_status: str
    capability_id: str
    package_marker: str
    schema_version: str
    entrypoint_owner: str
    mode: str
    venue: str
    instrument_id: str
    futures_only: bool
    btc_excluded: bool
    spot_excluded: bool
    decision_result: str
    direction: str
    reason_codes: tuple[str, ...]
    blockers: tuple[str, ...]
    risk_sizing_result: str
    safety_result: str
    portfolio_model_id: str
    portfolio_snapshot: dict[str, Any]
    economic_metrics: dict[str, Any]
    market_data_policy_ok: bool
    no_order_attestation_ok: bool
    orders_submitted: bool
    broker_writes_performed: bool
    credentials_used: bool
    network_used: bool
    wallclock_session_started: bool
    authority_effect: str
    paper_shadow_observation_authorized: bool
    notes: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["reason_codes"] = list(self.reason_codes)
        payload["blockers"] = list(self.blockers)
        payload["notes"] = list(self.notes)
        return payload


def _fail(
    *,
    blockers: tuple[str, ...],
    instrument_id: str = PRODUCTION_INSTRUMENT_ID,
    venue: str = VENUE_OKX_EUROPE,
    portfolio: SimulatedPortfolioEconomicsModelV1 | None = None,
) -> ObservationCycleResultV1:
    model = portfolio or SimulatedPortfolioEconomicsModelV1()
    return ObservationCycleResultV1(
        terminal_status="FAIL_CLOSED",
        capability_id=CAPABILITY_ID,
        package_marker=PACKAGE_MARKER,
        schema_version=SCHEMA_VERSION,
        entrypoint_owner=ENTRYPOINT_OWNER,
        mode=REQUIRED_MODE,
        venue=venue,
        instrument_id=instrument_id,
        futures_only=True,
        btc_excluded=True,
        spot_excluded=True,
        decision_result="NOT_EVALUATED",
        direction="NONE",
        reason_codes=blockers,
        blockers=blockers,
        risk_sizing_result="NOT_EVALUATED",
        safety_result="NOT_EVALUATED",
        portfolio_model_id=PORTFOLIO_ECONOMICS_MODEL_ID,
        portfolio_snapshot=dict(model.snapshot()),
        economic_metrics=model.economic_metrics().to_dict(),
        market_data_policy_ok=False,
        no_order_attestation_ok=False,
        orders_submitted=False,
        broker_writes_performed=False,
        credentials_used=False,
        network_used=False,
        wallclock_session_started=False,
        authority_effect=AUTHORITY_EFFECT_NONE,
        paper_shadow_observation_authorized=False,
        notes=("FAIL_CLOSED", "NO_AUTHORIZATION", "NO_WALLCLOCK"),
    )


def run_integrated_paper_shadow_observation_cycle_v1(
    *,
    mode: str,
    instrument_id: Optional[str] = None,
    ticks: Sequence[ObservationMarketTickV1] | None = None,
    reference_price: Decimal | None = None,
    intended_side: str = "HOLD",
    intended_quantity: Decimal = Decimal("0"),
    orders_enabled: bool = False,
    broker_writes_enabled: bool = False,
    live_enabled: bool = False,
    testnet_enabled: bool = False,
    network_enabled: bool = False,
    credentials_enabled: bool = False,
    attempt_order_submission: bool = False,
    attempt_broker_write: bool = False,
) -> ObservationCycleResultV1:
    """Run one offline observation cycle with simulated portfolio economics."""
    selected = (
        PRODUCTION_INSTRUMENT_ID
        if instrument_id is None or str(instrument_id).strip() == ""
        else str(instrument_id).strip()
    )
    blockers = list(
        assert_observation_request_no_order_v1(
            mode=mode,
            orders_enabled=orders_enabled,
            broker_writes_enabled=broker_writes_enabled,
            live_enabled=live_enabled,
            testnet_enabled=testnet_enabled,
            network_enabled=network_enabled,
            credentials_enabled=credentials_enabled,
        )
    )
    blockers.extend(
        validate_instrument_for_observation_v1(
            instrument_id=selected,
            params=MarketDataPolicyParamsV1(allowed_instruments=(PRODUCTION_INSTRUMENT_ID,)),
        )
    )
    if blockers:
        return _fail(blockers=tuple(blockers), instrument_id=selected)

    if attempt_order_submission:
        try:
            reject_order_attempt_v1("place_order")
        except Exception as exc:  # noqa: BLE001 - convert to fail-closed result
            return _fail(
                blockers=("ORDER_ATTEMPT_REJECTED", str(exc)),
                instrument_id=selected,
            )
    if attempt_broker_write:
        try:
            reject_broker_write_attempt_v1("broker_write")
        except Exception as exc:  # noqa: BLE001
            return _fail(
                blockers=("BROKER_WRITE_ATTEMPT_REJECTED", str(exc)),
                instrument_id=selected,
            )

    binding = default_okx_europe_xperp_production_binding()
    binding_eval = evaluate_okx_europe_xperp_binding(binding)
    if not binding_eval.get("venue_binding_pass"):
        return _fail(
            blockers=("CANONICAL_OKX_BINDING_FAILED",),
            instrument_id=selected,
        )

    price = reference_price if reference_price is not None else Decimal("3500")
    if price <= 0:
        return _fail(blockers=("INVALID_REFERENCE_PRICE",), instrument_id=selected)

    supplied_ticks = list(ticks or ())
    if not supplied_ticks:
        # Deterministic single offline tick (caller-supplied semantics; no network).
        supplied_ticks = [
            ObservationMarketTickV1(
                instrument_id=selected,
                venue="OKX",
                market_type="FUTURES",
                sequence=1,
                event_ts_unix=1_700_000_000.0,
                receive_ts_unix=1_700_000_000.1,
                mono_ts=100.0,
                mid_price=float(price),
                source="entrypoint_default_offline_tick",
            )
        ]
    md = evaluate_market_data_sequence_v1(
        supplied_ticks,
        params=MarketDataPolicyParamsV1(allowed_instruments=(PRODUCTION_INSTRUMENT_ID,)),
        wall_now_unix=supplied_ticks[-1].receive_ts_unix,
    )
    if not md.ok:
        return _fail(
            blockers=tuple(md.blockers) or ("MARKET_DATA_POLICY_FAIL",),
            instrument_id=selected,
        )

    # Reuse canonical Decision→Risk→Safety offline cycle (shadow mode core), then
    # map into observation portfolio simulation. Shadow core forbids order clients.
    core = run_okx_futures_shadow_no_order_cycle_core_v0(
        mode="shadow",
        instrument_id=selected,
        live_enabled=False,
        order_submission_enabled=False,
        testnet_order_submission_enabled=False,
        capital_change_enabled=False,
        scheduler_enabled=False,
        daemon_enabled=False,
        reference_price=price,
    )
    if core.terminal_status != "PASS":
        return _fail(
            blockers=tuple(core.blockers) or ("DECISION_PIPELINE_FAIL_CLOSED",),
            instrument_id=selected,
        )

    portfolio = SimulatedPortfolioEconomicsModelV1()
    # Observation economics: HOLD by default; optional intended action is simulated only.
    side = str(intended_side or "HOLD").upper()
    qty = Decimal(intended_quantity)
    if side in {"BUY", "SELL"} and qty <= 0:
        return _fail(blockers=("INTENDED_QUANTITY_REQUIRED",), instrument_id=selected)
    portfolio.apply_intended_action(
        instrument_id=selected,
        side=side,
        quantity=qty if side in {"BUY", "SELL"} else Decimal("0"),
        mark_price=price,
    )

    if core.real_order_submission or core.order_capable_client_instantiated:
        return _fail(
            blockers=("ORDER_SURFACE_REACHABLE_IN_CORE",),
            instrument_id=selected,
            portfolio=portfolio,
        )

    return ObservationCycleResultV1(
        terminal_status="PASS",
        capability_id=CAPABILITY_ID,
        package_marker=PACKAGE_MARKER,
        schema_version=SCHEMA_VERSION,
        entrypoint_owner=ENTRYPOINT_OWNER,
        mode=REQUIRED_MODE,
        venue=str(core.venue),
        instrument_id=selected,
        futures_only=True,
        btc_excluded=True,
        spot_excluded=True,
        decision_result=str(core.decision_result),
        direction=str(core.direction),
        reason_codes=tuple(core.reason_codes) + ("OBSERVATION_SIMULATED_PORTFOLIO",),
        blockers=(),
        risk_sizing_result=str(core.risk_sizing_result),
        safety_result=str(core.safety_result),
        portfolio_model_id=PORTFOLIO_ECONOMICS_MODEL_ID,
        portfolio_snapshot=dict(portfolio.snapshot()),
        economic_metrics=portfolio.economic_metrics().to_dict(),
        market_data_policy_ok=True,
        no_order_attestation_ok=True,
        orders_submitted=False,
        broker_writes_performed=False,
        credentials_used=False,
        network_used=False,
        wallclock_session_started=False,
        authority_effect=AUTHORITY_EFFECT_NONE,
        paper_shadow_observation_authorized=False,
        notes=(
            "OBSERVATION_ONLY",
            "SIMULATED_PORTFOLIO_ONLY",
            "NO_BROKER_WRITES",
            "NO_ORDERS",
            "NO_WALLCLOCK_SESSION",
            "NO_OPERATOR_GO",
            f"PRODUCER_FAMILY={PRODUCER_FAMILY}",
        ),
    )
