"""§11.14 live order and economic evidence-ladder surface.

LIVE_EXECUTION_CODE_EXISTS, LIVE_EXECUTION_PATH_REACHABLE,
LIVE_PRIVATE_READ_ONLY_PROVEN, LIVE_ORDER_PLAN_OBSERVED,
LIVE_SUBMIT_ACK_OBSERVED, LIVE_FILL_OBSERVED, LIVE_FEE_OBSERVED,
LIVE_POSITION_RECONCILED, and LIVE_ACCOUNTING_RECONSTRUCTED are bound
true. LIVE_RESTART_RECONSTRUCTED remains false because the restart
reader remains unbound and COMPLETE_CAPTURE_SEAM remains UNPROVEN.
The S05 producer, first durable pre-restart handoff owner, and writer
are implemented; host-crash durability is unproven. Exact-single live
POST remains consumed. This GO performs no GET, no POST, no restart
execution, and no order mutation. Atlas has no authority.
"""
