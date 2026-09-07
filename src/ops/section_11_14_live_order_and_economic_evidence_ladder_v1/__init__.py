"""§11.14 live order and economic evidence-ladder surface.

LIVE_EXECUTION_CODE_EXISTS, LIVE_EXECUTION_PATH_REACHABLE,
LIVE_PRIVATE_READ_ONLY_PROVEN, LIVE_ORDER_PLAN_OBSERVED,
LIVE_SUBMIT_ACK_OBSERVED, LIVE_FILL_OBSERVED, LIVE_FEE_OBSERVED,
LIVE_POSITION_RECONCILED, and LIVE_ACCOUNTING_RECONSTRUCTED are bound
true. CASE_B refuted unique existing owner/hook facts. This slice creates
exactly one productive capture owner and exactly one lifecycle hook,
structurally bound on the unauthorized LIVE_ORDER path, fail-closed.
CURRENT_RUNTIME_EXECUTION_AUTHORIZED remains false. COMPLETE_CAPTURE_SEAM
remains UNPROVEN. LIVE_RESTART_RECONSTRUCTED remains false. Host-crash
durability remains unproven. This GO performs no GET, no POST, no restart
execution, no productive handoff write, and no order mutation. Atlas has
no authority.
"""
