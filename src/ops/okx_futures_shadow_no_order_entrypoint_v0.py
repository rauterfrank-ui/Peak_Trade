"""Canonical OKX Futures Shadow no-order entrypoint v0.

Sole public entrypoint for the offline OKX Futures Shadow no-order path.
Invokes the Step-29U-bound composition after verifying canonical Step 29U
offline evidence. Core Decision→Risk→Execution→Reconciliation remains in
``run_okx_futures_shadow_no_order_cycle_core_v0`` (consumed by Step 29U).

No network, no credentials, no order-capable client, no scheduler/daemon,
no Paper fill simulator, no Live/Testnet order submission, no capital mutation.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any, Mapping, Optional

from src.ops.bounded_futures_testnet_venue_binding_v0 import (
    PRODUCTION_INSTRUMENT_ID,
    PRODUCTION_INSTRUMENT_TYPE,
    PRODUCTION_UNDERLYING,
    VENUE_OKX_EUROPE,
    default_okx_europe_xperp_production_binding,
    evaluate_okx_europe_xperp_binding,
)
from trading.master_v2.capital_risk_sizing_offline_replay_binding_adapter_v0 import (
    build_scenario_tick_decision_evidence_v0,
    evaluate_scenario_capital_risk_sizing_v0,
)
from trading.master_v2.canonical_order_intent_offline_replay_binding_adapter_v0 import (
    evaluate_scenario_canonical_order_intent_v0,
)
from trading.master_v2.double_play_entry_exit_policy_v0 import (
    DecisionOutcome,
    PositionState,
    ReconciliationState,
    SafetyMode,
)
from trading.master_v2.reconciliation_unknown_outcome_offline_replay_binding_adapter_v0 import (
    ReconciliationUnknownOutcomeOfflineReplayContextV0,
    evaluate_scenario_reconciliation_unknown_outcome_v0,
)
from trading.master_v2.safety_kernel_offline_replay_binding_adapter_v0 import (
    SafetyKernelOfflineReplayContextV0,
    evaluate_scenario_safety_kernel_v0,
)

PACKAGE_MARKER = "OKX_FUTURES_SHADOW_NO_ORDER_ENTRYPOINT_V0=true"
SCHEMA_ID = "ops.okx_futures_shadow_no_order_entrypoint_v0"
SCHEMA_VERSION = "v0"
ENTRYPOINT_OWNER = "ops.okx_futures_shadow_no_order_entrypoint_v0"
CLI_RELPATH = "scripts/ops/run_okx_futures_shadow_no_order_v0.py"

CANONICAL_OKX_INPUT_OWNER = "src.ops.bounded_futures_testnet_venue_binding_v0"
CANONICAL_INSTRUMENT_BINDING = PRODUCTION_INSTRUMENT_ID
CANONICAL_DECISION_OWNER = (
    "trading.master_v2.capital_risk_sizing_offline_replay_binding_adapter_v0."
    "build_scenario_tick_decision_evidence_v0"
)
CANONICAL_RISK_SIZING_OWNER = (
    "trading.master_v2.capital_risk_sizing_offline_replay_binding_adapter_v0"
)
CANONICAL_SAFETY_OWNER = "trading.master_v2.safety_kernel_offline_replay_binding_adapter_v0"
CANONICAL_EXECUTION_PROJECTION = (
    "trading.master_v2.canonical_order_intent_offline_replay_binding_adapter_v0"
)
CANONICAL_RECONCILIATION_OWNER = (
    "trading.master_v2.reconciliation_unknown_outcome_offline_replay_binding_adapter_v0"
)

REQUIRED_MODE = "shadow"
_BITCOIN_FRAGMENTS = frozenset({"BTC", "XBT", "BITCOIN"})
_SPOT_FRAGMENTS = frozenset({"SPOT", "/EUR", "/USD", "/USDT"})
_DEFAULT_REFERENCE_PRICE = Decimal("3500")
_CONFIG_DIGEST = "okx_futures_shadow_no_order_entrypoint_v0_config"
_IMPL_DIGEST = "okx_futures_shadow_no_order_entrypoint_v0_impl"


@dataclass(frozen=True)
class OkxFuturesShadowNoOrderCycleResultV0:
    terminal_status: str
    venue: str
    instrument: str
    market_classification: str
    futures_only: bool
    btc_excluded: bool
    spot_excluded: bool
    input_provenance: str
    decision_result: str
    direction: str
    reason_codes: tuple[str, ...]
    blockers: tuple[str, ...]
    risk_sizing_result: str
    safety_result: str
    execution_intent_result: str
    reconciliation_audit_result: str
    real_order_submission: bool
    order_capable_client_instantiated: bool
    exchange_order_submission: bool
    testnet_order_submission: bool
    live_activation: bool
    scheduler: bool
    background_process_left_running: bool
    step_29u_bound: bool = False
    step_29u_present: bool = False
    step_29u_evidence_verified: bool = False
    step_29u_capability_result: str = "NOT_BOUND"
    canonical_step_29u_absent: bool = True
    step_29u_binding_owner: str = "NONE"
    schema_id: str = SCHEMA_ID
    schema_version: str = SCHEMA_VERSION
    package_marker: str = PACKAGE_MARKER
    entrypoint_owner: str = ENTRYPOINT_OWNER
    cli_relpath: str = CLI_RELPATH


def _fail_result(
    *,
    blockers: tuple[str, ...],
    reason_codes: tuple[str, ...] = (),
    instrument: str = "",
    venue: str = VENUE_OKX_EUROPE,
) -> OkxFuturesShadowNoOrderCycleResultV0:
    return OkxFuturesShadowNoOrderCycleResultV0(
        terminal_status="FAIL_CLOSED",
        venue=venue,
        instrument=instrument or "NONE",
        market_classification="UNKNOWN",
        futures_only=False,
        btc_excluded=True,
        spot_excluded=True,
        input_provenance="none",
        decision_result="NOT_EVALUATED",
        direction="NONE",
        reason_codes=reason_codes or blockers,
        blockers=blockers,
        risk_sizing_result="NOT_EVALUATED",
        safety_result="NOT_EVALUATED",
        execution_intent_result="NOT_EVALUATED",
        reconciliation_audit_result="NOT_EVALUATED",
        real_order_submission=False,
        order_capable_client_instantiated=False,
        exchange_order_submission=False,
        testnet_order_submission=False,
        live_activation=False,
        scheduler=False,
        background_process_left_running=False,
    )


def _instrument_is_bitcoin(instrument_id: str) -> bool:
    upper = instrument_id.upper()
    return any(frag in upper for frag in _BITCOIN_FRAGMENTS)


def _instrument_is_spot(instrument_id: str) -> bool:
    upper = instrument_id.upper()
    if "XPERP" in upper or upper.endswith("-PERP") or "SWAP" in upper:
        return False
    return any(frag in upper for frag in _SPOT_FRAGMENTS) or upper.endswith("/EUR")


def validate_shadow_no_order_request_v0(
    *,
    mode: str,
    instrument_id: str,
    live_enabled: bool = False,
    order_submission_enabled: bool = False,
    testnet_order_submission_enabled: bool = False,
    capital_change_enabled: bool = False,
    scheduler_enabled: bool = False,
    daemon_enabled: bool = False,
) -> tuple[str, ...]:
    """Return fail-closed blockers; empty tuple means request may proceed."""
    blockers: list[str] = []
    if str(mode).strip().lower() != REQUIRED_MODE:
        blockers.append(f"mode_must_be_{REQUIRED_MODE}")
    if live_enabled:
        blockers.append("live_enabled_forbidden")
    if order_submission_enabled:
        blockers.append("order_submission_forbidden")
    if testnet_order_submission_enabled:
        blockers.append("testnet_order_submission_forbidden")
    if capital_change_enabled:
        blockers.append("capital_change_forbidden")
    if scheduler_enabled:
        blockers.append("scheduler_forbidden")
    if daemon_enabled:
        blockers.append("daemon_forbidden")
    inst = str(instrument_id or "").strip()
    if not inst:
        blockers.append("instrument_required")
        return tuple(blockers)
    if _instrument_is_bitcoin(inst):
        blockers.append("btc_instrument_forbidden")
    if _instrument_is_spot(inst):
        blockers.append("spot_instrument_forbidden")
    if inst != PRODUCTION_INSTRUMENT_ID:
        blockers.append("instrument_must_match_canonical_okx_europe_xperp_binding")
    return tuple(blockers)


def run_okx_futures_shadow_no_order_cycle_core_v0(
    *,
    mode: str,
    instrument_id: Optional[str] = None,
    live_enabled: bool = False,
    order_submission_enabled: bool = False,
    testnet_order_submission_enabled: bool = False,
    capital_change_enabled: bool = False,
    scheduler_enabled: bool = False,
    daemon_enabled: bool = False,
    reference_price: Decimal | None = None,
) -> OkxFuturesShadowNoOrderCycleResultV0:
    """Core Decision→Risk→Execution→Reconciliation cycle (no Step 29U binding)."""
    selected = (
        PRODUCTION_INSTRUMENT_ID
        if instrument_id is None or str(instrument_id).strip() == ""
        else str(instrument_id).strip()
    )
    blockers = validate_shadow_no_order_request_v0(
        mode=mode,
        instrument_id=selected,
        live_enabled=live_enabled,
        order_submission_enabled=order_submission_enabled,
        testnet_order_submission_enabled=testnet_order_submission_enabled,
        capital_change_enabled=capital_change_enabled,
        scheduler_enabled=scheduler_enabled,
        daemon_enabled=daemon_enabled,
    )
    if blockers:
        return _fail_result(blockers=blockers, instrument=selected)

    binding = default_okx_europe_xperp_production_binding()
    binding_eval = evaluate_okx_europe_xperp_binding(binding)
    if not binding_eval.get("venue_binding_pass"):
        fail_reasons = tuple(str(x) for x in binding_eval.get("fail_reasons", ()))
        return _fail_result(
            blockers=("canonical_okx_binding_failed", *fail_reasons),
            instrument=selected,
        )

    price = reference_price if reference_price is not None else _DEFAULT_REFERENCE_PRICE
    decision_outcome = DecisionOutcome.HOLD.value
    reason_codes = (
        "shadow_no_order_mode",
        "canonical_okx_futures_binding",
        "hold_no_submission",
    )
    evidence = build_scenario_tick_decision_evidence_v0(
        decision_id="okx-shadow-no-order-v0-001",
        replay_id="okx-shadow-no-order-v0-replay",
        instrument_id=selected,
        trading_epoch=0,
        composition_result_id="okx-shadow-no-order-composition",
        entry_exit_policy_ref="okx-shadow-no-order-entry-exit-policy",
        selected_side="neutral",
        decision_outcome=decision_outcome,
        reason_codes=reason_codes,
        decision_precedence_trace=("shadow_no_order_entrypoint_v0", "hold"),
        config_digest=_CONFIG_DIGEST,
        implementation_digest=_IMPL_DIGEST,
    )

    sizing = evaluate_scenario_capital_risk_sizing_v0(evidence, reference_price=price)
    intent = evaluate_scenario_canonical_order_intent_v0(
        sizing.evidence,
        sizing_decision=sizing.sizing_decision,
        reference_price=price,
    )
    safety = evaluate_scenario_safety_kernel_v0(
        intent.evidence,
        context=SafetyKernelOfflineReplayContextV0(
            safety_mode=SafetyMode.NORMAL,
            killswitch_blocked=False,
            safety_decision_allowed=True,
            reconciliation_state=ReconciliationState.RECONCILED,
            position_state=PositionState.FLAT_RECONCILED,
        ),
    )
    recon = evaluate_scenario_reconciliation_unknown_outcome_v0(
        safety.evidence,
        context=ReconciliationUnknownOutcomeOfflineReplayContextV0(
            position_state=PositionState.FLAT_RECONCILED,
            reconciliation_state=ReconciliationState.RECONCILED,
            venue_flat=True,
        ),
    )

    sizing_outcome = (
        sizing.sizing_decision.outcome.value
        if sizing.sizing_decision is not None
        else sizing.risk_sizing_effect
    )
    safety_codes = safety.boundary.reason_codes if safety.boundary is not None else ()
    recon_effect = recon.reconciliation_unknown_outcome_effect
    final_reasons = tuple(recon.evidence.reason_codes)

    return OkxFuturesShadowNoOrderCycleResultV0(
        terminal_status="PASS",
        venue=VENUE_OKX_EUROPE,
        instrument=selected,
        market_classification=PRODUCTION_INSTRUMENT_TYPE,
        futures_only=True,
        btc_excluded=PRODUCTION_UNDERLYING.upper() not in _BITCOIN_FRAGMENTS,
        spot_excluded=True,
        input_provenance=(
            f"{CANONICAL_OKX_INPUT_OWNER}:default_okx_europe_xperp_production_binding"
        ),
        decision_result=decision_outcome,
        direction="HOLD",
        reason_codes=final_reasons or reason_codes,
        blockers=(),
        risk_sizing_result=str(sizing_outcome),
        safety_result=(
            "PASS"
            if safety.binding_applied and not safety.boundary.hard_block_reasons
            else f"BOUND:{','.join(safety_codes) or 'none'}"
        ),
        execution_intent_result=(
            f"{intent.intent_outcome}:{intent.order_intent_effect}"
            if intent is not None
            else "NONE"
        ),
        reconciliation_audit_result=str(recon_effect),
        real_order_submission=False,
        order_capable_client_instantiated=False,
        exchange_order_submission=False,
        testnet_order_submission=False,
        live_activation=False,
        scheduler=False,
        background_process_left_running=False,
    )


def run_okx_futures_shadow_no_order_cycle_v0(
    *,
    mode: str,
    instrument_id: Optional[str] = None,
    live_enabled: bool = False,
    order_submission_enabled: bool = False,
    testnet_order_submission_enabled: bool = False,
    capital_change_enabled: bool = False,
    scheduler_enabled: bool = False,
    daemon_enabled: bool = False,
    reference_price: Decimal | None = None,
    repo_root: Path | None = None,
    evidence_dir: Path | None = None,
    source_git_sha: str | None = None,
) -> OkxFuturesShadowNoOrderCycleResultV0:
    """Sole public entrypoint: Step-29U-bound Shadow no-order cycle."""
    from src.ops.step_29u_canonical_shadow_binding_v0 import (
        run_step_29u_bound_okx_futures_shadow_no_order_cycle_v0,
    )

    return run_step_29u_bound_okx_futures_shadow_no_order_cycle_v0(
        mode=mode,
        instrument_id=instrument_id,
        repo_root=repo_root,
        evidence_dir=evidence_dir,
        source_git_sha=source_git_sha,
        live_enabled=live_enabled,
        order_submission_enabled=order_submission_enabled,
        testnet_order_submission_enabled=testnet_order_submission_enabled,
        capital_change_enabled=capital_change_enabled,
        scheduler_enabled=scheduler_enabled,
        daemon_enabled=daemon_enabled,
        reference_price=reference_price,
        cycle_core=run_okx_futures_shadow_no_order_cycle_core_v0,
    )


def serialize_okx_futures_shadow_no_order_cycle_result_v0(
    result: OkxFuturesShadowNoOrderCycleResultV0,
) -> dict[str, Any]:
    payload = asdict(result)
    payload["real_order_submission"] = False
    return payload


def result_to_machine_lines(result: OkxFuturesShadowNoOrderCycleResultV0) -> list[str]:
    data = serialize_okx_futures_shadow_no_order_cycle_result_v0(result)
    lines: list[str] = []
    for key, value in data.items():
        if isinstance(value, tuple):
            rendered = "[" + ",".join(str(v) for v in value) + "]"
        elif isinstance(value, bool):
            rendered = str(value).lower()
        else:
            rendered = str(value)
        lines.append(f"{key.upper()}={rendered}")
    return lines


def validate_request_mapping_v0(raw: Mapping[str, Any]) -> tuple[str, ...]:
    """Fail-closed helper for missing/invalid mapping inputs."""
    if not isinstance(raw, Mapping):
        return ("input_must_be_mapping",)
    mode = raw.get("mode")
    if mode is None or str(mode).strip() == "":
        return ("mode_required",)
    return validate_shadow_no_order_request_v0(
        mode=str(mode),
        instrument_id=str(raw.get("instrument_id") or PRODUCTION_INSTRUMENT_ID),
        live_enabled=bool(raw.get("live_enabled", False)),
        order_submission_enabled=bool(raw.get("order_submission_enabled", False)),
        testnet_order_submission_enabled=bool(raw.get("testnet_order_submission_enabled", False)),
        capital_change_enabled=bool(raw.get("capital_change_enabled", False)),
        scheduler_enabled=bool(raw.get("scheduler_enabled", False)),
        daemon_enabled=bool(raw.get("daemon_enabled", False)),
    )
