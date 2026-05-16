# Bounded no-order Shadow adapter plan builder (v0).
# Pure, deterministic, side-effect free. Not a runtime entrypoint.

from __future__ import annotations

from dataclasses import dataclass

from src.shadow_no_order_proof.adapter_contract_v0 import (
    ADAPTER_KIND,
    BOUNDED_SHADOW_ADAPTER_PROOF_V0,
)

_NOT_EXECUTABLE_DECLARATION = (
    "This plan is declarative metadata only; it is not an executable command or runtime entrypoint."
)
_NOT_APPROVED_DECLARATION = "No trading, testnet, live, shadow mode, scheduler, runtime, or order path is approved by this plan."

_DEFAULT_FORBIDDEN_ACTIONS: tuple[str, ...] = (
    "call_mixed_risk_shadow_execution_entry_script",
    "call_mixed_risk_testnet_orchestrator_entry_script",
    "wrap_or_import_mixed_risk_shadow_runtime_candidates",
    "intent_order_flow_submit",
    "intent_order_flow_place",
    "intent_order_flow_cancel",
    "intent_order_flow_create",
    "intent_order_flow_send",
    "broker_connect",
    "exchange_connect",
    "open_runtime",
    "open_scheduler",
    "start_testnet_session",
    "start_live_session",
    "enable_shadow_mode",
    "read_api_credentials",
)


@dataclass(frozen=True)
class BoundedShadowAdapterPlan:
    """Declarative adapter plan — metadata only, not an execution authority."""

    adapter_kind: str
    source: str
    proof_version: str
    allowed_actions: tuple[str, ...]
    forbidden_actions: tuple[str, ...]
    evidence_required: bool
    proven_shadow_no_order_entrypoint_found: bool
    executable_command_created: bool
    not_executable_declaration: str
    not_approved_declaration: str
    shadow_mode_allowed: bool
    order_submission_allowed: bool
    broker_allowed: bool
    exchange_allowed: bool
    runtime_allowed: bool
    scheduler_allowed: bool
    live_allowed: bool
    testnet_allowed: bool
    paper_allowed: bool


def build_bounded_shadow_adapter_plan_v0(
    *, source: str = "bounded_adapter_build_v0"
) -> BoundedShadowAdapterPlan:
    """Return a frozen plan describing a bounded no-order adapter boundary (no I/O, no orchestration)."""

    return BoundedShadowAdapterPlan(
        adapter_kind=ADAPTER_KIND,
        source=source,
        proof_version=f"{BOUNDED_SHADOW_ADAPTER_PROOF_V0}_impl_v0",
        allowed_actions=(),
        forbidden_actions=_DEFAULT_FORBIDDEN_ACTIONS,
        evidence_required=True,
        proven_shadow_no_order_entrypoint_found=False,
        executable_command_created=False,
        not_executable_declaration=_NOT_EXECUTABLE_DECLARATION,
        not_approved_declaration=_NOT_APPROVED_DECLARATION,
        shadow_mode_allowed=False,
        order_submission_allowed=False,
        broker_allowed=False,
        exchange_allowed=False,
        runtime_allowed=False,
        scheduler_allowed=False,
        live_allowed=False,
        testnet_allowed=False,
        paper_allowed=False,
    )
