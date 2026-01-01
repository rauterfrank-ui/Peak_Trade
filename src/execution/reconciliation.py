"""
Reconciliation Engine (WP0D - Phase 0 Recon/Ledger Bridge)

Minimal reconciliation logic for detecting position/order divergences.

Phase 0: Paper/Shadow mode - no real exchange data.
- Internal snapshot: PositionLedger, OrderLedger
- External snapshot: Mocked/stubbed (no real exchange API)
- Matching rules: Deterministic (order_id, symbol, timestamp)
- Severity: INFO/WARN/FAIL

Future: Phase 1+ integration with exchange API.
"""

from typing import List, Dict, Optional
from datetime import datetime
from decimal import Decimal
from dataclasses import dataclass
import uuid

from src.execution.contracts import ReconDiff, ReconSummary, OrderState
from src.execution.position_ledger import PositionLedger, Position
from src.execution.order_ledger import OrderLedger


@dataclass
class ExternalSnapshot:
    """
    External state snapshot (mocked in Phase 0).

    Represents exchange-reported state for reconciliation.
    In Phase 0 (paper/shadow), this is conceptual/mocked.
    In Phase 1+, populated from exchange API.
    """

    timestamp: datetime
    positions: Dict[str, Decimal]  # symbol -> quantity
    open_orders: List[Dict]  # List of open order dicts
    fills: List[Dict]  # List of fill dicts
    cash_balance: Optional[Decimal] = None


class ReconciliationEngine:
    """
    Reconciliation engine for detecting divergences.

    Phase 0: Minimal logic with mocked external data.

    Features:
    - Compare internal vs external positions
    - Detect quantity mismatches
    - Generate ReconDiff with severity (INFO/WARN/FAIL)
    """

    def __init__(
        self,
        position_ledger: PositionLedger,
        order_ledger: OrderLedger,
    ):
        """
        Initialize reconciliation engine.

        Args:
            position_ledger: Internal position ledger
            order_ledger: Internal order ledger
        """
        self.position_ledger = position_ledger
        self.order_ledger = order_ledger

        # Tolerance thresholds (from WP0D spec)
        self.quantity_tolerance_pct = Decimal("0.001")  # 0.1%
        self.quantity_tolerance_abs = Decimal("0.01")  # 0.01 units
        self.price_tolerance_pct = Decimal("0.005")  # 0.5%

    def reconcile(
        self,
        external_snapshot: Optional[ExternalSnapshot] = None,
        as_of_time: Optional[datetime] = None,
    ) -> List[ReconDiff]:
        """
        Perform reconciliation between internal and external state.

        Args:
            external_snapshot: External state (mocked in Phase 0)
            as_of_time: Reconciliation time (defaults to now)

        Returns:
            List of ReconDiff representing divergences
        """
        as_of_time = as_of_time or datetime.utcnow()
        diffs: List[ReconDiff] = []

        # Phase 0: If no external snapshot, create empty/mocked one
        if external_snapshot is None:
            external_snapshot = self._create_mock_external_snapshot(as_of_time)

        # Reconcile positions
        position_diffs = self._reconcile_positions(external_snapshot, as_of_time)
        diffs.extend(position_diffs)

        # Reconcile cash (if available)
        if external_snapshot.cash_balance is not None:
            cash_diff = self._reconcile_cash(external_snapshot, as_of_time)
            if cash_diff:
                diffs.append(cash_diff)

        return diffs

    def _create_mock_external_snapshot(self, timestamp: datetime) -> ExternalSnapshot:
        """
        Create a mock external snapshot (Phase 0 placeholder).

        In Phase 0, external snapshot mirrors internal state (no divergence).
        In Phase 1+, this would fetch from exchange API.

        Args:
            timestamp: Snapshot timestamp

        Returns:
            Mock external snapshot
        """
        # Mirror internal positions (no divergence in Phase 0 by default)
        positions = {}
        for position in self.position_ledger.get_all_positions():
            positions[position.symbol] = position.quantity

        return ExternalSnapshot(
            timestamp=timestamp,
            positions=positions,
            open_orders=[],
            fills=[],
            cash_balance=self.position_ledger.get_cash_balance(),
        )

    def _reconcile_positions(
        self,
        external_snapshot: ExternalSnapshot,
        as_of_time: datetime,
    ) -> List[ReconDiff]:
        """
        Reconcile internal positions vs external positions.

        Args:
            external_snapshot: External state
            as_of_time: Reconciliation time

        Returns:
            List of position-related ReconDiff
        """
        diffs: List[ReconDiff] = []

        # Get internal positions
        internal_positions = {pos.symbol: pos for pos in self.position_ledger.get_all_positions()}

        # Check for mismatches
        all_symbols = set(internal_positions.keys()) | set(external_snapshot.positions.keys())

        for symbol in all_symbols:
            internal_qty = internal_positions.get(symbol, Position(symbol=symbol)).quantity
            external_qty = external_snapshot.positions.get(symbol, Decimal("0"))

            delta = abs(internal_qty - external_qty)

            # Calculate tolerance
            tolerance = max(
                self.quantity_tolerance_abs, abs(external_qty) * self.quantity_tolerance_pct
            )

            if delta > tolerance:
                # Determine severity
                severity = self._determine_position_severity(delta, external_qty)

                diff = ReconDiff(
                    diff_id=f"pos_diff_{symbol}_{as_of_time.isoformat()}",
                    timestamp=as_of_time,
                    client_order_id="",  # Position-level, no specific order
                    exchange_order_id=None,
                    local_state=None,
                    exchange_state=None,
                    severity=severity,
                    diff_type="POSITION",
                    description=f"Position mismatch for {symbol}: internal={internal_qty}, external={external_qty}, delta={delta}",
                    details={
                        "symbol": symbol,
                        "internal_quantity": str(internal_qty),
                        "external_quantity": str(external_qty),
                        "delta": str(delta),
                        "tolerance": str(tolerance),
                    },
                )

                diffs.append(diff)

        return diffs

    def _reconcile_cash(
        self,
        external_snapshot: ExternalSnapshot,
        as_of_time: datetime,
    ) -> Optional[ReconDiff]:
        """
        Reconcile internal cash vs external cash.

        Args:
            external_snapshot: External state
            as_of_time: Reconciliation time

        Returns:
            ReconDiff if cash mismatch, None otherwise
        """
        internal_cash = self.position_ledger.get_cash_balance()
        external_cash = external_snapshot.cash_balance

        if external_cash is None:
            return None

        delta = abs(internal_cash - external_cash)

        # Cash tolerance: 0.5% or 1.0 EUR
        tolerance = max(Decimal("1.0"), abs(external_cash) * Decimal("0.005"))

        if delta > tolerance:
            # Cash mismatch is always FAIL
            return ReconDiff(
                diff_id=f"cash_diff_{as_of_time.isoformat()}",
                timestamp=as_of_time,
                client_order_id="",
                exchange_order_id=None,
                local_state=None,
                exchange_state=None,
                severity="FAIL",
                diff_type="CASH",
                description=f"Cash mismatch: internal={internal_cash}, external={external_cash}, delta={delta}",
                details={
                    "internal_cash": str(internal_cash),
                    "external_cash": str(external_cash),
                    "delta": str(delta),
                    "tolerance": str(tolerance),
                },
            )

        return None

    def _determine_position_severity(
        self,
        delta: Decimal,
        external_qty: Decimal,
    ) -> str:
        """
        Determine severity for position mismatch.

        Severity taxonomy (from WP0D spec):
        - INFO: <0.1%
        - WARN: 0.1%-1%
        - FAIL: >1%

        Args:
            delta: Absolute quantity difference
            external_qty: External quantity (for percentage calc)

        Returns:
            Severity string (INFO/WARN/FAIL)
        """
        if external_qty == 0:
            # If external is zero, any internal position is a mismatch
            return "FAIL" if delta > Decimal("0.01") else "WARN"

        pct_drift = (delta / abs(external_qty)) * Decimal("100")

        if pct_drift < Decimal("0.1"):
            return "INFO"
        elif pct_drift < Decimal("1.0"):
            return "WARN"
        else:
            return "FAIL"

    def create_summary(
        self,
        diffs: List[ReconDiff],
        session_id: str = "",
        strategy_id: str = "",
        top_n: int = 10,
    ) -> ReconSummary:
        """
        Create structured reconciliation summary.

        Design (WP0D Observability):
        - Aggregate counts by severity and diff_type
        - Select top-N diffs (deterministic ordering)
        - Flag critical/fail conditions

        Args:
            diffs: List of ReconDiff
            session_id: Session identifier
            strategy_id: Strategy identifier
            top_n: Number of top diffs to include

        Returns:
            ReconSummary with aggregated statistics
        """
        # Count by severity
        counts_by_severity: Dict[str, int] = {}
        for diff in diffs:
            counts_by_severity[diff.severity] = counts_by_severity.get(diff.severity, 0) + 1

        # Count by type
        counts_by_type: Dict[str, int] = {}
        for diff in diffs:
            counts_by_type[diff.diff_type] = counts_by_type.get(diff.diff_type, 0) + 1

        # Determine max severity (CRITICAL > FAIL > ERROR > WARN > INFO)
        severity_order = ["CRITICAL", "FAIL", "ERROR", "WARN", "INFO"]
        max_severity = "INFO"
        for sev in severity_order:
            if counts_by_severity.get(sev, 0) > 0:
                max_severity = sev
                break

        # Sort diffs deterministically: severity (desc), timestamp (asc), diff_id (asc)
        severity_rank = {s: i for i, s in enumerate(severity_order)}
        sorted_diffs = sorted(
            diffs,
            key=lambda d: (severity_rank.get(d.severity, 99), d.timestamp, d.diff_id),
        )

        # Select top-N
        top_diffs = sorted_diffs[:top_n]

        return ReconSummary(
            run_id=str(uuid.uuid4()),
            timestamp=datetime.utcnow(),
            session_id=session_id,
            strategy_id=strategy_id,
            total_diffs=len(diffs),
            counts_by_severity=counts_by_severity,
            counts_by_type=counts_by_type,
            top_diffs=top_diffs,
            has_critical=counts_by_severity.get("CRITICAL", 0) > 0,
            has_fail=counts_by_severity.get("FAIL", 0) > 0,
            max_severity=max_severity,
        )

    def export_reconciliation_report(
        self,
        diffs: List[ReconDiff],
        as_of_time: datetime,
    ) -> Dict:
        """
        Export reconciliation report as dict (for JSON serialization).

        Args:
            diffs: List of ReconDiff
            as_of_time: Reconciliation time

        Returns:
            Dict with report summary
        """
        severity_counts = {
            "INFO": sum(1 for d in diffs if d.severity == "INFO"),
            "WARN": sum(1 for d in diffs if d.severity == "WARN"),
            "FAIL": sum(1 for d in diffs if d.severity == "FAIL"),
        }

        return {
            "as_of_time": as_of_time.isoformat(),
            "total_diffs": len(diffs),
            "severity_counts": severity_counts,
            "diffs": [d.to_dict() for d in diffs],
        }
