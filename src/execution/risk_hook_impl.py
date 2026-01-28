"""
Runtime Risk Hook Implementation (WP0B)

Adapter that implements RiskHook protocol using RiskRuntime.
"""

from typing import Optional, Dict, Any
from decimal import Decimal

from src.execution.contracts import Order, RiskResult, RiskDecision as ContractRiskDecision
from src.execution.risk_runtime import RiskRuntime
from src.execution.risk_runtime.decisions import RiskDecision as RuntimeRiskDecision


# ============================================================================
# Runtime Risk Hook (Adapter)
# ============================================================================


class RuntimeRiskHook:
    """
    Implementation of RiskHook protocol using RiskRuntime.

    Design:
    - Adapts RiskRuntime to RiskHook protocol
    - Converts between contract types (RiskResult) and runtime types (RiskDirective)
    - Delegates to RiskRuntime for evaluation
    - NO cyclic imports (only depends on contracts + risk_runtime)

    Usage:
        # Create runtime with policies
        runtime = RiskRuntime(policies=[MaxOpenOrdersPolicy(10)])

        # Wrap in adapter
        hook = RuntimeRiskHook(runtime, order_ledger, position_ledger)

        # Use with OrderStateMachine
        osm = OrderStateMachine(risk_hook=hook)
    """

    def __init__(
        self,
        runtime: RiskRuntime,
        order_ledger=None,  # Type: OrderLedger (avoid import)
        position_ledger=None,  # Type: PositionLedger (avoid import)
    ):
        """
        Initialize runtime risk hook.

        Args:
            runtime: RiskRuntime instance
            order_ledger: Optional OrderLedger instance
            position_ledger: Optional PositionLedger instance
        """
        self.runtime = runtime
        self.order_ledger = order_ledger
        self.position_ledger = position_ledger

    def evaluate_order(
        self,
        order: Order,
        context: Optional[Dict[str, Any]] = None,
    ) -> RiskResult:
        """
        Evaluate order using RiskRuntime.

        Args:
            order: Order to evaluate
            context: Optional context (ignored in Phase 0)

        Returns:
            RiskResult with decision (ALLOW/BLOCK/PAUSE)
        """
        # Evaluate using runtime
        directive = self.runtime.evaluate_pre_order(
            order=order,
            order_ledger=self.order_ledger,
            position_ledger=self.position_ledger,
        )

        # SLICE4 telemetry (watch/paper/shadow safe): bounded risk decision counters.
        try:
            from src.obs import strategy_risk_telemetry as _srt

            # Runtime decision mapping:
            # - ALLOW/MODIFY => allow
            # - REJECT/HALT  => block
            d = directive.decision
            if d == RuntimeRiskDecision.ALLOW or d == RuntimeRiskDecision.MODIFY:
                _srt.inc_risk_check(check="runtime_risk.evaluate_pre_order", result="allow", n=1)
            elif d == RuntimeRiskDecision.REJECT:
                _srt.inc_risk_check(check="runtime_risk.evaluate_pre_order", result="block", n=1)
                _srt.inc_risk_block(reason="runtime:reject", n=1)
            elif d == RuntimeRiskDecision.HALT:
                _srt.inc_risk_check(check="runtime_risk.evaluate_pre_order", result="block", n=1)
                _srt.inc_risk_block(reason="runtime:halt", n=1)
            else:
                _srt.inc_risk_check(check="runtime_risk.evaluate_pre_order", result="error", n=1)
                _srt.inc_risk_block(reason="runtime:unknown", n=1)
        except Exception:
            pass

        # Convert RuntimeRiskDecision to ContractRiskDecision
        contract_decision = self._convert_decision(directive.decision)

        # Build RiskResult
        return RiskResult(
            decision=contract_decision,
            reason=directive.reason,
            metadata=directive.tags,
        )

    def check_kill_switch(self) -> RiskResult:
        """
        Check if kill switch is active.

        Note: Phase 0 doesn't implement kill switch.
        Future work: add KillSwitchPolicy to runtime.

        Returns:
            RiskResult with ALLOW (kill switch inactive)
        """
        # Phase 0: No kill switch implementation
        return RiskResult(
            decision=ContractRiskDecision.ALLOW,
            reason="Kill switch not implemented in Phase 0",
            metadata={"phase": "0", "kill_switch": "not_implemented"},
        )

    def evaluate_position_change(
        self,
        symbol: str,
        quantity: Decimal,
        side: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> RiskResult:
        """
        Evaluate position change.

        Note: Phase 0 uses order-level evaluation.
        Future work: add position-level policies.

        Args:
            symbol: Trading symbol
            quantity: Position change quantity
            side: "BUY" or "SELL"
            context: Optional context

        Returns:
            RiskResult with decision
        """
        # Phase 0: Delegate to order evaluation
        # Create temporary order for evaluation
        from src.execution.contracts import OrderSide

        temp_order = Order(
            client_order_id="temp_position_change",
            symbol=symbol,
            side=OrderSide(side),
            quantity=quantity,
        )

        return self.evaluate_order(temp_order, context)

    def _convert_decision(self, runtime_decision: RuntimeRiskDecision) -> ContractRiskDecision:
        """
        Convert runtime decision to contract decision.

        Mapping:
        - ALLOW → ALLOW
        - REJECT → BLOCK
        - MODIFY → ALLOW (modified order handled by runtime)
        - HALT → PAUSE

        Args:
            runtime_decision: RuntimeRiskDecision

        Returns:
            ContractRiskDecision
        """
        if runtime_decision == RuntimeRiskDecision.ALLOW:
            return ContractRiskDecision.ALLOW
        elif runtime_decision == RuntimeRiskDecision.REJECT:
            return ContractRiskDecision.BLOCK
        elif runtime_decision == RuntimeRiskDecision.MODIFY:
            # MODIFY is handled internally by runtime
            # At RiskHook level, we return ALLOW (order was modified)
            return ContractRiskDecision.ALLOW
        elif runtime_decision == RuntimeRiskDecision.HALT:
            return ContractRiskDecision.PAUSE
        else:
            # Fallback: BLOCK on unknown decision
            return ContractRiskDecision.BLOCK


# ============================================================================
# Factory Functions
# ============================================================================


def create_runtime_risk_hook(
    policies,  # List[RiskPolicy]
    order_ledger=None,
    position_ledger=None,
    audit_log=None,
) -> RuntimeRiskHook:
    """
    Factory to create RuntimeRiskHook with RiskRuntime.

    Args:
        policies: List of RiskPolicy instances
        order_ledger: Optional OrderLedger instance
        position_ledger: Optional PositionLedger instance
        audit_log: Optional AuditLog instance

    Returns:
        RuntimeRiskHook instance
    """
    runtime = RiskRuntime(policies=policies, audit_log=audit_log)
    return RuntimeRiskHook(
        runtime=runtime,
        order_ledger=order_ledger,
        position_ledger=position_ledger,
    )
