"""
ExecutionPipeline plan-only boundary v0.

Structural validation against ExecutionPipeline input contracts without adapter
instantiation, network access, or submission side effects.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

from src.execution_pipeline.contracts import ExecutionError, ExecutionPlan

PLAN_ONLY_BOUNDARY_VERSION = "v0"
PLAN_ONLY_BOUNDARY_OWNER = "src.execution_pipeline.plan_only_boundary_v0"
PACKAGE_MARKER = "EXECUTION_PIPELINE_PLAN_ONLY_BOUNDARY_V0=true"

REASON_PASS = "PASS"
REASON_ZERO_ORDER_SUBMISSION_BLOCKED = "ZERO_ORDER_SUBMISSION_BLOCKED"
REASON_EXECUTION_ELIGIBILITY_DENIED = "EXECUTION_ELIGIBILITY_DENIED"
REASON_INVALID_PLAN = "INVALID_PLAN"
REASON_PLAN_ONLY_REQUIRED = "PLAN_ONLY_REQUIRED"


@dataclass(frozen=True)
class ExecutionPipelinePlanOnlyBoundaryResultV0:
    boundary_pass: bool
    submission_blocked: bool
    execution_eligible: bool
    adapter_invoked: bool
    fail_reasons: Tuple[str, ...]
    reason_codes: Tuple[str, ...]
    validation_error: Optional[ExecutionError] = None
    order_plan_count: int = 0


def _validate_plan_structure(plan: ExecutionPlan) -> Optional[ExecutionError]:
    """Mirror ExecutionPipeline structural validation without side effects."""
    if plan.orders is None:
        return ExecutionError(error_code="invalid_plan", message="orders_missing")
    if len(plan.orders) == 0:
        return ExecutionError(error_code="invalid_plan", message="orders_empty")
    for order in plan.orders:
        if not order.order_id:
            return ExecutionError(error_code="invalid_order", message="order_id_missing")
        if not order.symbol:
            return ExecutionError(
                error_code="invalid_order",
                message="symbol_missing",
                details={"order_id": order.order_id},
            )
        if order.side not in ("buy", "sell"):
            return ExecutionError(
                error_code="invalid_order",
                message="side_invalid",
                details={"order_id": order.order_id, "side": order.side},
            )
        if order.quantity <= 0:
            return ExecutionError(
                error_code="invalid_order",
                message="quantity_invalid",
                details={"order_id": order.order_id, "quantity": order.quantity},
            )
    return None


def validate_execution_plan_only_boundary_v0(
    plan: ExecutionPlan,
    *,
    plan_only: bool = True,
    submission_blocked: bool = True,
    execution_eligible: bool = False,
) -> ExecutionPipelinePlanOnlyBoundaryResultV0:
    """Validate plan shape at the pipeline boundary; always block submission."""

    reasons: list[str] = []
    if not plan_only:
        reasons.append(REASON_PLAN_ONLY_REQUIRED)
    if execution_eligible:
        reasons.append(REASON_EXECUTION_ELIGIBILITY_DENIED)
    if not submission_blocked:
        reasons.append(REASON_ZERO_ORDER_SUBMISSION_BLOCKED)

    validation_error = _validate_plan_structure(plan)
    if validation_error is not None:
        reasons.append(REASON_INVALID_PLAN)
        return ExecutionPipelinePlanOnlyBoundaryResultV0(
            boundary_pass=False,
            submission_blocked=True,
            execution_eligible=False,
            adapter_invoked=False,
            fail_reasons=tuple(dict.fromkeys(reasons)),
            reason_codes=tuple(dict.fromkeys(reasons)),
            validation_error=validation_error,
            order_plan_count=len(plan.orders or []),
        )

    reasons.append(REASON_ZERO_ORDER_SUBMISSION_BLOCKED)
    return ExecutionPipelinePlanOnlyBoundaryResultV0(
        boundary_pass=not any(
            code in reasons
            for code in (REASON_PLAN_ONLY_REQUIRED, REASON_EXECUTION_ELIGIBILITY_DENIED)
        ),
        submission_blocked=True,
        execution_eligible=False,
        adapter_invoked=False,
        fail_reasons=tuple(
            code
            for code in dict.fromkeys(reasons)
            if code not in (REASON_PASS, REASON_ZERO_ORDER_SUBMISSION_BLOCKED)
        ),
        reason_codes=(REASON_PASS, REASON_ZERO_ORDER_SUBMISSION_BLOCKED),
        validation_error=None,
        order_plan_count=len(plan.orders),
    )
