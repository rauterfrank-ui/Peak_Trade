"""Cap 11.1–11.9 dependency retention + Cap 11.10 ownership matrix."""

from __future__ import annotations

from typing import Any

from src.ops.capability_11_10_live_bounded_single_future_continuity_v1.constants_v1 import (
    CAPABILITY_11_9_LIVE_CANARY_ORDER_EXECUTION_RETAINED,
    CAPABILITY_11_9_MINIMUM_EXPOSURE_RETAINED,
    CAPABILITY_11_9_NO_NETWORK_SESSION_RETAINED,
    CAPABILITY_11_9_NO_ORDER_SUBMIT_RETAINED,
    CAPABILITY_11_9_NO_PROVEN_CLAIMS_RETAINED,
    CAPABILITY_11_9_NOT_ACTIVATED_RETAINED,
    LIVE_BOUNDED_EVIDENCE_LADDER_OWNER,
    LIVE_BOUNDED_ORDER_LIFECYCLE_CONTINUITY_OWNER,
    LIVE_BOUNDED_SINGLE_FUTURE_CONTINUITY_OWNER,
    OWNER,
    PREDECESSOR_CAPABILITY_ID_11_1,
    PREDECESSOR_CAPABILITY_ID_11_2,
    PREDECESSOR_CAPABILITY_ID_11_3,
    PREDECESSOR_CAPABILITY_ID_11_4,
    PREDECESSOR_CAPABILITY_ID_11_5,
    PREDECESSOR_CAPABILITY_ID_11_6,
    PREDECESSOR_CAPABILITY_ID_11_7,
    PREDECESSOR_CAPABILITY_ID_11_8,
    PREDECESSOR_CAPABILITY_ID_11_9,
)
from src.ops.capability_11_9_live_canary_order_execution_v1.dependency_and_ownership_v1 import (
    prove_capability_11_1_dependency_retained_v1 as _prove_11_1,
)
from src.ops.capability_11_9_live_canary_order_execution_v1.dependency_and_ownership_v1 import (
    prove_capability_11_2_dependency_retained_v1 as _prove_11_2,
)
from src.ops.capability_11_9_live_canary_order_execution_v1.dependency_and_ownership_v1 import (
    prove_capability_11_3_dependency_retained_v1 as _prove_11_3,
)
from src.ops.capability_11_9_live_canary_order_execution_v1.dependency_and_ownership_v1 import (
    prove_capability_11_4_dependency_retained_v1 as _prove_11_4,
)
from src.ops.capability_11_9_live_canary_order_execution_v1.dependency_and_ownership_v1 import (
    prove_capability_11_5_dependency_retained_v1 as _prove_11_5,
)
from src.ops.capability_11_9_live_canary_order_execution_v1.dependency_and_ownership_v1 import (
    prove_capability_11_6_dependency_retained_v1 as _prove_11_6,
)
from src.ops.capability_11_9_live_canary_order_execution_v1.dependency_and_ownership_v1 import (
    prove_capability_11_7_dependency_retained_v1 as _prove_11_7,
)
from src.ops.capability_11_9_live_canary_order_execution_v1.dependency_and_ownership_v1 import (
    prove_capability_11_8_dependency_retained_v1 as _prove_11_8,
)
from src.ops.capability_11_9_live_canary_order_execution_v1.verifier_v1 import (
    verify_capability_11_9_v1,
)


STATE_OWNERSHIP_MATRIX_V1: tuple[dict[str, str], ...] = (
    {
        "field": "live_bounded_single_future_continuity",
        "classification": "EVIDENCE_ONLY_STATE",
        "owner": LIVE_BOUNDED_SINGLE_FUTURE_CONTINUITY_OWNER,
        "mutable_by_adapter": "false",
    },
    {
        "field": "live_bounded_order_lifecycle_continuity",
        "classification": "EVIDENCE_ONLY_STATE",
        "owner": LIVE_BOUNDED_ORDER_LIFECYCLE_CONTINUITY_OWNER,
        "mutable_by_adapter": "false",
    },
    {
        "field": "live_bounded_evidence_ladder",
        "classification": "EVIDENCE_ONLY_STATE",
        "owner": LIVE_BOUNDED_EVIDENCE_LADDER_OWNER,
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
    result = _prove_11_7()
    result["PREDECESSOR_CAPABILITY_ID"] = PREDECESSOR_CAPABILITY_ID_11_7
    return result


def prove_capability_11_8_dependency_retained_v1() -> dict[str, Any]:
    result = _prove_11_8()
    result["PREDECESSOR_CAPABILITY_ID"] = PREDECESSOR_CAPABILITY_ID_11_8
    return result


def prove_capability_11_9_dependency_retained_v1() -> dict[str, Any]:
    result = verify_capability_11_9_v1()
    claims = result.get("claims") or {}
    ok = all(
        [
            result.get("ok") is True,
            result.get("VERIFIER_RESULT") == "PASS",
            claims.get("CORE_LOGIC_CHANGE") is False,
            claims.get("ACTIVATION_STATE") == "not_activated",
            claims.get("TESTNET_AUTHORIZED") is False,
            claims.get("LIVE_AUTHORIZED") is False,
            claims.get("CAPABILITY_11_9_STARTED") is True,
            claims.get("CAPABILITY_11_9_LIVE_CANARY_ORDER_EXECUTION_STARTED") is True,
            claims.get("LIVE_CANARY_EXECUTION_ACTIVATED") is False,
            claims.get("LIVE_CANARY_MINIMUM_EXPOSURE_ACTIVATED") is False,
            claims.get("LIVE_CANARY_ORDER_EXECUTION_ACTIVATED") is False,
            claims.get("LIVE_SUBMIT_ACK_OBSERVED") is False,
            claims.get("PRIVATE_NETWORK_SESSION_STARTED") is False,
            claims.get("NETWORK_SESSION_STARTED") is False,
            claims.get("LIVE_ORDER_SUBMIT_PERFORMED_IN_CAPABILITY_11_9") is False,
            claims.get("CREDENTIAL_LOAD_PERFORMED_IN_CAPABILITY_11_9") is False,
            claims.get("EXCHANGE_CREDENTIAL_ACCESS_REACHABLE") is False,
            # Cap 11.9 package itself still refuses Cap 11.10 activation from within 11.9.
            claims.get("CAPABILITY_11_10_STARTED") is False,
            claims.get("CAPABILITY_11_1_DEPENDENCY_SATISFIED") is True,
            claims.get("CAPABILITY_11_2_DEPENDENCY_SATISFIED") is True,
            claims.get("CAPABILITY_11_3_DEPENDENCY_SATISFIED") is True,
            claims.get("CAPABILITY_11_4_DEPENDENCY_SATISFIED") is True,
            claims.get("CAPABILITY_11_5_DEPENDENCY_SATISFIED") is True,
            claims.get("CAPABILITY_11_6_DEPENDENCY_SATISFIED") is True,
            claims.get("CAPABILITY_11_7_DEPENDENCY_SATISFIED") is True,
            claims.get("CAPABILITY_11_8_DEPENDENCY_SATISFIED") is True,
            CAPABILITY_11_9_LIVE_CANARY_ORDER_EXECUTION_RETAINED is True,
            CAPABILITY_11_9_MINIMUM_EXPOSURE_RETAINED is True,
            CAPABILITY_11_9_NOT_ACTIVATED_RETAINED is True,
            CAPABILITY_11_9_NO_ORDER_SUBMIT_RETAINED is True,
            CAPABILITY_11_9_NO_NETWORK_SESSION_RETAINED is True,
            CAPABILITY_11_9_NO_PROVEN_CLAIMS_RETAINED is True,
        ]
    )
    return {
        "ok": ok,
        "PREDECESSOR_CAPABILITY_ID": PREDECESSOR_CAPABILITY_ID_11_9,
        "CAPABILITY_11_9_DEPENDENCY_SATISFIED": ok,
        "CAPABILITY_11_9_VERIFIER_RESULT": result.get("VERIFIER_RESULT"),
        "CAPABILITY_11_9_LIVE_CANARY_ORDER_EXECUTION_RETAINED": (
            CAPABILITY_11_9_LIVE_CANARY_ORDER_EXECUTION_RETAINED
        ),
        "CAPABILITY_11_9_MINIMUM_EXPOSURE_RETAINED": CAPABILITY_11_9_MINIMUM_EXPOSURE_RETAINED,
        "CAPABILITY_11_9_NOT_ACTIVATED_RETAINED": CAPABILITY_11_9_NOT_ACTIVATED_RETAINED,
        "CAPABILITY_11_9_NO_ORDER_SUBMIT_RETAINED": CAPABILITY_11_9_NO_ORDER_SUBMIT_RETAINED,
        "CAPABILITY_11_9_NO_NETWORK_SESSION_RETAINED": (
            CAPABILITY_11_9_NO_NETWORK_SESSION_RETAINED
        ),
        "CAPABILITY_11_9_NO_PROVEN_CLAIMS_RETAINED": CAPABILITY_11_9_NO_PROVEN_CLAIMS_RETAINED,
    }


def prove_state_ownership_matrix_v1() -> dict[str, Any]:
    owners = {row["field"]: row["owner"] for row in STATE_OWNERSHIP_MATRIX_V1}
    ok = all(
        [
            owners.get("live_bounded_single_future_continuity")
            == LIVE_BOUNDED_SINGLE_FUTURE_CONTINUITY_OWNER,
            owners.get("live_bounded_order_lifecycle_continuity")
            == LIVE_BOUNDED_ORDER_LIFECYCLE_CONTINUITY_OWNER,
            owners.get("live_bounded_evidence_ladder") == LIVE_BOUNDED_EVIDENCE_LADDER_OWNER,
            owners.get("plaintext_credentials") == "none",
            all(row["mutable_by_adapter"] == "false" for row in STATE_OWNERSHIP_MATRIX_V1),
        ]
    )
    return {
        "ok": ok,
        "owner": OWNER,
        "matrix": list(STATE_OWNERSHIP_MATRIX_V1),
        "LIVE_BOUNDED_SINGLE_FUTURE_CONTINUITY_OWNER": LIVE_BOUNDED_SINGLE_FUTURE_CONTINUITY_OWNER,
        "LIVE_BOUNDED_ORDER_LIFECYCLE_CONTINUITY_OWNER": (
            LIVE_BOUNDED_ORDER_LIFECYCLE_CONTINUITY_OWNER
        ),
        "LIVE_BOUNDED_EVIDENCE_LADDER_OWNER": LIVE_BOUNDED_EVIDENCE_LADDER_OWNER,
    }
