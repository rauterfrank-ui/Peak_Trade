"""
Risk Runtime (WP0B)

Main orchestrator for runtime risk evaluation.
"""

from typing import List, Optional
from datetime import datetime

from src.execution.contracts import Order, Fill, LedgerEntry
from src.execution.risk_runtime.decisions import (
    RiskDirective,
    RiskDecision,
    allow_directive,
    halt_directive,
)
from src.execution.risk_runtime.context import (
    RiskContextSnapshot,
    build_context_snapshot,
)
from src.execution.risk_runtime.policies import RiskPolicy


# ============================================================================
# Risk Runtime
# ============================================================================


class RiskRuntime:
    """
    Runtime risk evaluator with pluggable policies.

    Design:
    - Takes list of RiskPolicy implementations
    - Evaluates all policies in sequence
    - Short-circuits on HALT or REJECT (configurable)
    - Writes all decisions to audit log (append-only)
    - Idempotent (same inputs → same decisions)

    Features:
    - Pre-order evaluation (before submission)
    - Pre-fill evaluation (before applying fill)
    - Post-fill evaluation (after applying fill)
    - Audit trail for all decisions
    """

    def __init__(
        self,
        policies: List[RiskPolicy],
        audit_log=None,  # Type: AuditLog (avoid import)
        short_circuit_on_reject: bool = True,
    ):
        """
        Initialize risk runtime.

        Args:
            policies: List of risk policies to evaluate
            audit_log: Optional audit log for decisions
            short_circuit_on_reject: Stop evaluation on first REJECT
        """
        self.policies = policies
        self.audit_log = audit_log
        self.short_circuit_on_reject = short_circuit_on_reject

        # Statistics
        self._evaluations_count = 0
        self._rejections_count = 0
        self._modifications_count = 0

    def evaluate_pre_order(
        self,
        order: Order,
        order_ledger=None,
        position_ledger=None,
    ) -> RiskDirective:
        """
        Evaluate order before submission.

        Args:
            order: Order to evaluate
            order_ledger: Optional OrderLedger instance
            position_ledger: Optional PositionLedger instance

        Returns:
            RiskDirective with final decision
        """
        # Build context snapshot
        snapshot = build_context_snapshot(
            order=order,
            order_ledger=order_ledger,
            position_ledger=position_ledger,
        )

        # Evaluate all policies
        final_directive = self._evaluate_policies(snapshot, event_type="PRE_ORDER")

        # Log decision
        self._log_decision(order=order, directive=final_directive, event_type="PRE_ORDER")

        return final_directive

    def evaluate_pre_fill(
        self,
        fill: Fill,
        order_ledger=None,
        position_ledger=None,
    ) -> RiskDirective:
        """
        Evaluate fill before applying to position ledger.

        Args:
            fill: Fill to evaluate
            order_ledger: Optional OrderLedger instance
            position_ledger: Optional PositionLedger instance

        Returns:
            RiskDirective with final decision
        """
        # Build context snapshot
        snapshot = build_context_snapshot(
            fill=fill,
            order_ledger=order_ledger,
            position_ledger=position_ledger,
        )

        # Evaluate all policies
        final_directive = self._evaluate_policies(snapshot, event_type="PRE_FILL")

        # Log decision
        self._log_decision(fill=fill, directive=final_directive, event_type="PRE_FILL")

        return final_directive

    def evaluate_post_fill(
        self,
        fill: Fill,
        order_ledger=None,
        position_ledger=None,
    ) -> RiskDirective:
        """
        Evaluate after fill has been applied (monitoring/alerting).

        Args:
            fill: Fill that was applied
            order_ledger: Optional OrderLedger instance
            position_ledger: Optional PositionLedger instance

        Returns:
            RiskDirective with final decision
        """
        # Build context snapshot
        snapshot = build_context_snapshot(
            fill=fill,
            order_ledger=order_ledger,
            position_ledger=position_ledger,
        )

        # Evaluate all policies
        final_directive = self._evaluate_policies(snapshot, event_type="POST_FILL")

        # Log decision
        self._log_decision(fill=fill, directive=final_directive, event_type="POST_FILL")

        return final_directive

    def _evaluate_policies(
        self,
        snapshot: RiskContextSnapshot,
        event_type: str,
    ) -> RiskDirective:
        """
        Evaluate all policies against snapshot.

        Logic:
        - Evaluate policies in order
        - HALT → short-circuit immediately
        - REJECT → short-circuit (if configured)
        - MODIFY → use modified order for subsequent policies
        - Collect all directives for audit

        Args:
            snapshot: Current system state
            event_type: Event type for logging

        Returns:
            Final RiskDirective
        """
        self._evaluations_count += 1

        # If no policies, default to ALLOW
        if not self.policies:
            return allow_directive(reason="No policies configured")

        # Evaluate each policy
        directives: List[RiskDirective] = []

        for policy in self.policies:
            directive = policy.evaluate(snapshot)
            directives.append(directive)

            # Short-circuit on HALT
            if directive.decision == RiskDecision.HALT:
                self._rejections_count += 1
                return halt_directive(
                    reason=f"Policy {policy.name}: {directive.reason}",
                    policy=policy.name,
                    short_circuit="HALT",
                )

            # Short-circuit on REJECT (if configured)
            if directive.decision == RiskDecision.REJECT and self.short_circuit_on_reject:
                self._rejections_count += 1
                return directive

            # Handle MODIFY
            if directive.decision == RiskDecision.MODIFY and directive.modified_order:
                self._modifications_count += 1
                # Update snapshot with modified order
                snapshot.order = directive.modified_order

        # Aggregate decisions
        # If any REJECT (and not short-circuited), reject
        rejects = [d for d in directives if d.decision == RiskDecision.REJECT]
        if rejects:
            self._rejections_count += 1
            return rejects[0]  # Return first rejection

        # If any MODIFY, return modified order
        modifies = [d for d in directives if d.decision == RiskDecision.MODIFY]
        if modifies:
            return modifies[-1]  # Return last modification

        # All ALLOW
        return allow_directive(
            reason=f"All {len(self.policies)} policies passed",
            policies_count=str(len(self.policies)),
        )

    def _log_decision(
        self,
        directive: RiskDirective,
        event_type: str,
        order: Optional[Order] = None,
        fill: Optional[Fill] = None,
    ) -> None:
        """
        Log risk decision to audit log.

        Args:
            directive: Risk directive to log
            event_type: Event type (PRE_ORDER, PRE_FILL, POST_FILL)
            order: Optional order
            fill: Optional fill
        """
        if not self.audit_log:
            return

        # Create ledger entry
        client_order_id = ""
        if order:
            client_order_id = order.client_order_id
        elif fill:
            client_order_id = fill.client_order_id

        entry = LedgerEntry(
            entry_id=f"risk_{event_type.lower()}_{datetime.utcnow().timestamp()}",
            event_type=f"RISK_{event_type}",
            client_order_id=client_order_id,
            details=directive.to_dict(),
        )

        self.audit_log.append(entry)

    def get_statistics(self) -> dict:
        """Get runtime statistics"""
        return {
            "evaluations_count": self._evaluations_count,
            "rejections_count": self._rejections_count,
            "modifications_count": self._modifications_count,
            "policies_count": len(self.policies),
        }
