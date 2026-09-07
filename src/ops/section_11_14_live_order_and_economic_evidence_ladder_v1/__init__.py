"""§11.14 live order and economic evidence-ladder surface.

LIVE_EXECUTION_CODE_EXISTS, LIVE_EXECUTION_PATH_REACHABLE,
LIVE_PRIVATE_READ_ONLY_PROVEN, LIVE_ORDER_PLAN_OBSERVED,
LIVE_SUBMIT_ACK_OBSERVED, LIVE_FILL_OBSERVED, LIVE_FEE_OBSERVED,
LIVE_POSITION_RECONCILED, and LIVE_ACCOUNTING_RECONSTRUCTED are bound
true. The restart reader and reconstruction consumer are bound to the
minted durable handoff owner. COMPLETE_CAPTURE_SEAM remains UNPROVEN
because contemporaneous provenance is only contract-proven, not
empirically observed. LIVE_RESTART_RECONSTRUCTED remains false.
Host-crash durability remains unproven. Exact-single live POST remains
consumed. This GO performs no GET, no POST, no restart execution, and
no order mutation. Atlas has no authority.
"""
