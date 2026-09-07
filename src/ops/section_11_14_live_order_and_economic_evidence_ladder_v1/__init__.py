"""§11.14 live order and economic evidence-ladder surface.

LIVE_EXECUTION_CODE_EXISTS, LIVE_EXECUTION_PATH_REACHABLE,
LIVE_PRIVATE_READ_ONLY_PROVEN, LIVE_ORDER_PLAN_OBSERVED,
LIVE_SUBMIT_ACK_OBSERVED, LIVE_FILL_OBSERVED, LIVE_FEE_OBSERVED,
LIVE_POSITION_RECONCILED, and LIVE_ACCOUNTING_RECONSTRUCTED are bound
true. The restart reader and reconstruction consumer are bound to the
minted durable handoff owner. Contemporaneous pre-restart observability
is CLOSED_REFUTED: no authorized non-live runtime surface joins the
writer, and repo-root read-back is MISSING_HANDOFF.
COMPLETE_CAPTURE_SEAM remains UNPROVEN. LIVE_RESTART_RECONSTRUCTED
remains false. Host-crash durability remains unproven. Exact-single live
POST remains consumed. This GO performs no GET, no POST, no restart
execution, no productive handoff write, and no order mutation. Atlas has
no authority.
"""
