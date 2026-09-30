"""N=1 standing PRE_EXTERNAL runtime supervisor — constants (no runtime authorization)."""

from __future__ import annotations

WORK_PACKAGE_ID = "n1_standing_pre_external_runtime_supervisor_v1"
EVIDENCE_ROOT_RELATIVE = "evidence/ops/n1_standing_pre_external_runtime_supervisor_v1"

TRANSPORT_SCOPE_OFFLINE_INJECT = "offline_inject_no_live_network"
TRANSPORT_SCOPE_SCOPED_READONLY_GET = "scoped_readonly_get_when_owner_go_consumed"

PRETRADE_DECISION_ID_SUPERVISOR_TICK = (
    "N1_STANDING_PRE_EXTERNAL_RUNTIME_SUPERVISOR_V1_PRETRADE_REFRESH"
)

SUPERVISOR_ZERO_ECONOMIC_AUTHORITY = True
