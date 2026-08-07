"""Cap 11.1–11.7 dependency retention + Cap 11.8 ownership matrix."""

from __future__ import annotations

from typing import Any

from src.ops.capability_11_7_live_private_readonly_and_shadow_reconciliation_v1.dependency_and_ownership_v1 import (
    prove_capability_11_1_dependency_retained_v1 as _prove_11_1,
)
from src.ops.capability_11_7_live_private_readonly_and_shadow_reconciliation_v1.dependency_and_ownership_v1 import (
    prove_capability_11_2_dependency_retained_v1 as _prove_11_2,
)
from src.ops.capability_11_7_live_private_readonly_and_shadow_reconciliation_v1.dependency_and_ownership_v1 import (
    prove_capability_11_3_dependency_retained_v1 as _prove_11_3,
)
from src.ops.capability_11_7_live_private_readonly_and_shadow_reconciliation_v1.dependency_and_ownership_v1 import (
    prove_capability_11_4_dependency_retained_v1 as _prove_11_4,
)
from src.ops.capability_11_7_live_private_readonly_and_shadow_reconciliation_v1.dependency_and_ownership_v1 import (
    prove_capability_11_5_dependency_retained_v1 as _prove_11_5,
)
from src.ops.capability_11_7_live_private_readonly_and_shadow_reconciliation_v1.dependency_and_ownership_v1 import (
    prove_capability_11_6_dependency_retained_v1 as _prove_11_6,
)
from src.ops.capability_11_7_live_private_readonly_and_shadow_reconciliation_v1.verifier_v1 import (
    verify_capability_11_7_v1,
)
from src.ops.capability_11_8_live_dry_run_order_plan_parity_v1.constants_v1 import (
    CAPABILITY_11_7_LIVE_PRIVATE_READONLY_RETAINED,
    CAPABILITY_11_7_NO_NETWORK_SESSION_RETAINED,
    CAPABILITY_11_7_NO_ORDER_SUBMIT_RETAINED,
    CAPABILITY_11_7_NO_PROVEN_CLAIMS_RETAINED,
    CAPABILITY_11_7_NOT_ACTIVATED_RETAINED,
    CAPABILITY_11_7_SHADOW_RECONCILIATION_RETAINED,
    LIVE_DRY_RUN_ORDER_PLAN_OWNER,
    LIVE_ORDER_PLAN_EVIDENCE_LADDER_OWNER,
    LIVE_ORDER_PLAN_PARITY_OWNER,
    OWNER,
    PREDECESSOR_CAPABILITY_ID_11_1,
    PREDECESSOR_CAPABILITY_ID_11_2,
    PREDECESSOR_CAPABILITY_ID_11_3,
    PREDECESSOR_CAPABILITY_ID_11_4,
    PREDECESSOR_CAPABILITY_ID_11_5,
    PREDECESSOR_CAPABILITY_ID_11_6,
    PREDECESSOR_CAPABILITY_ID_11_7,
)


STATE_OWNERSHIP_MATRIX_V1: tuple[dict[str, str], ...] = (
    {
        "field": "live_dry_run_order_plan",
        "classification": "EVIDENCE_ONLY_STATE",
        "owner": LIVE_DRY_RUN_ORDER_PLAN_OWNER,
        "mutable_by_adapter": "false",
    },
    {
        "field": "live_order_plan_parity",
        "classification": "EVIDENCE_ONLY_STATE",
        "owner": LIVE_ORDER_PLAN_PARITY_OWNER,
        "mutable_by_adapter": "false",
    },
    {
        "field": "live_order_plan_evidence_ladder",
        "classification": "EVIDENCE_ONLY_STATE",
        "owner": LIVE_ORDER_PLAN_EVIDENCE_LADDER_OWNER,
        "mutable_by_adapter": "false",
    },
    {
        "field": "plaintext_credentials",
        "classification": "FORBIDDEN_TO_PERSIST",
        "owner": "none",
        "mutable_by_adapter": "false",
    },
)


def prove_capability_11_1_dependency_retained_v1() -> dict[str, Any]:
    result = _prove_11_1()
    result["PREDECESSOR_CAPABILITY_ID"] = PREDECESSOR_CAPABILITY_ID_11_1
    return result


def prove_capability_11_2_dependency_retained_v1() -> dict[str, Any]:
    result = _prove_11_2()
    result["PREDECESSOR_CAPABILITY_ID"] = PREDECESSOR_CAPABILITY_ID_11_2
    return result


def prove_capability_11_3_dependency_retained_v1() -> dict[str, Any]:
    result = _prove_11_3()
    result["PREDECESSOR_CAPABILITY_ID"] = PREDECESSOR_CAPABILITY_ID_11_3
    return result


def prove_capability_11_4_dependency_retained_v1() -> dict[str, Any]:
    result = _prove_11_4()
    result["PREDECESSOR_CAPABILITY_ID"] = PREDECESSOR_CAPABILITY_ID_11_4
    return result


def prove_capability_11_5_dependency_retained_v1() -> dict[str, Any]:
    result = _prove_11_5()
    result["PREDECESSOR_CAPABILITY_ID"] = PREDECESSOR_CAPABILITY_ID_11_5
    return result


def prove_capability_11_6_dependency_retained_v1() -> dict[str, Any]:
    result = _prove_11_6()
    result["PREDECESSOR_CAPABILITY_ID"] = PREDECESSOR_CAPABILITY_ID_11_6
    return result


def prove_capability_11_7_dependency_retained_v1() -> dict[str, Any]:
    result = verify_capability_11_7_v1()
    claims = result.get("claims") or {}
    ok = all(
        [
            result.get("ok") is True,
            result.get("VERIFIER_RESULT") == "PASS",
            claims.get("CORE_LOGIC_CHANGE") is False,
            claims.get("ACTIVATION_STATE") == "not_activated",
            claims.get("TESTNET_AUTHORIZED") is False,
            claims.get("LIVE_AUTHORIZED") is False,
            claims.get("CAPABILITY_11_7_LIVE_PRIVATE_READONLY_STARTED") is True,
            claims.get("LIVE_PRIVATE_READONLY_ACTIVATED") is False,
            claims.get("LIVE_SHADOW_RECONCILIATION_ACTIVATED") is False,
            claims.get("LIVE_PRIVATE_READ_ONLY_PROVEN") is False,
            claims.get("PRIVATE_NETWORK_SESSION_STARTED") is False,
            claims.get("NETWORK_SESSION_STARTED") is False,
            claims.get("LIVE_ORDER_SUBMIT_PERFORMED_IN_CAPABILITY_11_7") is False,
            claims.get("CREDENTIAL_LOAD_PERFORMED_IN_CAPABILITY_11_7") is False,
            claims.get("EXCHANGE_CREDENTIAL_ACCESS_REACHABLE") is False,
            # Cap 11.7 package itself still refuses Cap 11.8 activation from within 11.7.
            claims.get("CAPABILITY_11_8_STARTED") is False,
            claims.get("CAPABILITY_11_1_DEPENDENCY_SATISFIED") is True,
            claims.get("CAPABILITY_11_2_DEPENDENCY_SATISFIED") is True,
            claims.get("CAPABILITY_11_3_DEPENDENCY_SATISFIED") is True,
            claims.get("CAPABILITY_11_4_DEPENDENCY_SATISFIED") is True,
            claims.get("CAPABILITY_11_5_DEPENDENCY_SATISFIED") is True,
            claims.get("CAPABILITY_11_6_DEPENDENCY_SATISFIED") is True,
            CAPABILITY_11_7_LIVE_PRIVATE_READONLY_RETAINED is True,
            CAPABILITY_11_7_SHADOW_RECONCILIATION_RETAINED is True,
            CAPABILITY_11_7_NOT_ACTIVATED_RETAINED is True,
            CAPABILITY_11_7_NO_ORDER_SUBMIT_RETAINED is True,
            CAPABILITY_11_7_NO_NETWORK_SESSION_RETAINED is True,
            CAPABILITY_11_7_NO_PROVEN_CLAIMS_RETAINED is True,
        ]
    )
    return {
        "ok": ok,
        "PREDECESSOR_CAPABILITY_ID": PREDECESSOR_CAPABILITY_ID_11_7,
        "CAPABILITY_11_7_DEPENDENCY_SATISFIED": ok,
        "CAPABILITY_11_7_VERIFIER_RESULT": result.get("VERIFIER_RESULT"),
        "CAPABILITY_11_7_LIVE_PRIVATE_READONLY_RETAINED": (
            CAPABILITY_11_7_LIVE_PRIVATE_READONLY_RETAINED
        ),
        "CAPABILITY_11_7_SHADOW_RECONCILIATION_RETAINED": (
            CAPABILITY_11_7_SHADOW_RECONCILIATION_RETAINED
        ),
        "CAPABILITY_11_7_NOT_ACTIVATED_RETAINED": CAPABILITY_11_7_NOT_ACTIVATED_RETAINED,
        "CAPABILITY_11_7_NO_ORDER_SUBMIT_RETAINED": CAPABILITY_11_7_NO_ORDER_SUBMIT_RETAINED,
        "CAPABILITY_11_7_NO_NETWORK_SESSION_RETAINED": (
            CAPABILITY_11_7_NO_NETWORK_SESSION_RETAINED
        ),
        "CAPABILITY_11_7_NO_PROVEN_CLAIMS_RETAINED": CAPABILITY_11_7_NO_PROVEN_CLAIMS_RETAINED,
    }


def prove_state_ownership_matrix_v1() -> dict[str, Any]:
    owners = {row["field"]: row["owner"] for row in STATE_OWNERSHIP_MATRIX_V1}
    ok = all(
        [
            owners.get("live_dry_run_order_plan") == LIVE_DRY_RUN_ORDER_PLAN_OWNER,
            owners.get("live_order_plan_parity") == LIVE_ORDER_PLAN_PARITY_OWNER,
            owners.get("live_order_plan_evidence_ladder") == LIVE_ORDER_PLAN_EVIDENCE_LADDER_OWNER,
            owners.get("plaintext_credentials") == "none",
            all(row["mutable_by_adapter"] == "false" for row in STATE_OWNERSHIP_MATRIX_V1),
        ]
    )
    return {
        "ok": ok,
        "owner": OWNER,
        "matrix": list(STATE_OWNERSHIP_MATRIX_V1),
        "LIVE_DRY_RUN_ORDER_PLAN_OWNER": LIVE_DRY_RUN_ORDER_PLAN_OWNER,
        "LIVE_ORDER_PLAN_PARITY_OWNER": LIVE_ORDER_PLAN_PARITY_OWNER,
        "LIVE_ORDER_PLAN_EVIDENCE_LADDER_OWNER": LIVE_ORDER_PLAN_EVIDENCE_LADDER_OWNER,
    }
