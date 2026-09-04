"""§11.14 live order and economic evidence-ladder surface.

LIVE_EXECUTION_CODE_EXISTS, LIVE_EXECUTION_PATH_REACHABLE,
LIVE_PRIVATE_READ_ONLY_PROVEN, LIVE_ORDER_PLAN_OBSERVED,
LIVE_SUBMIT_ACK_OBSERVED, LIVE_FILL_OBSERVED, LIVE_FEE_OBSERVED,
LIVE_POSITION_RECONCILED, and LIVE_ACCOUNTING_RECONSTRUCTED are bound
true. LIVE_RESTART_RECONSTRUCTED remains false because a durable Live
pre-restart handoff is absent after an exhaustive offline census.
Exact-single live POST remains consumed. This GO performs no GET, no POST,
no restart execution, and no order mutation. Atlas has no authority.
"""
