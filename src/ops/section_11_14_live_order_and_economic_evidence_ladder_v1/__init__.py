"""§11.14 live order and economic evidence-ladder surface.

LIVE_EXECUTION_CODE_EXISTS, LIVE_EXECUTION_PATH_REACHABLE,
LIVE_PRIVATE_READ_ONLY_PROVEN, LIVE_ORDER_PLAN_OBSERVED,
LIVE_SUBMIT_ACK_OBSERVED, LIVE_FILL_OBSERVED, LIVE_FEE_OBSERVED,
LIVE_POSITION_RECONCILED, and LIVE_ACCOUNTING_RECONSTRUCTED are bound
true. Unique productive capture owner, lifecycle hook, and unique
productive caller remain structurally bound. COMPLETE_CAPTURE_SEAM=PROVEN
remains the predecessor offline contract.
CONTEMPORANEOUS_CAPTURE_RUNTIME_SURFACE=PROVEN remains the predecessor
runtime-surface proof. Isolation from live execution remains false.
CONTEMPORANEOUS_PRE_RESTART_CAPTURE_OBSERVATION=NOT_EXECUTED.
CONTEMPORANEOUS_PRODUCTIVE_CAPTURE_EXECUTED remains false.
LIVE_FILL_READINESS remains false. LIVE_FILL_EXECUTION_AUTHORIZED remains
false. CURRENT_RUNTIME_EXECUTION_AUTHORIZED remains false.
LIVE_RESTART_RECONSTRUCTED remains false. Host-crash durability remains
unproven. This GO performs no GET, no POST, no restart execution, no
productive contemporaneous capture, and no order mutation. Atlas has no
authority.
"""
