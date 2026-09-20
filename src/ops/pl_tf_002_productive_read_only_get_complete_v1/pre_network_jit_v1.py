"""Pre-network JIT proof for PL-TF-002. No venue GET unless execute_network on capture."""

from __future__ import annotations

from typing import Any, Mapping

from src.ops.full_core_live_path_composition_root_v1.checkout_independent_credential_os_native_store_acquisition_v1 import (
    REAL_KEYCHAIN_ACCESS_AUTHORIZED,
)
from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    EXTERNAL_EFFECT_AUTHORIZED,
    POST_ALLOWED,
    REAL_VENUE_POST_ALLOWED,
)
from src.ops.pl_tf_002_productive_read_only_get_complete_v1.constants_v1 import (
    AUTHORIZED_NETWORK_HOST,
    PRODUCTIVE_TRANSPORT_CLASS,
    SESSION_OWNER_GO,
)
from src.ops.pl_tf_002_productive_read_only_session_executor_v1.constants_v1 import (
    METHOD_ALLOWLIST,
)
from src.ops.pl_tf_002_productive_read_only_session_executor_v1.session_executor_v1 import (
    build_pl_tf_002_read_only_get_session_preflight_v1,
    prove_pl_tf_002_session_does_not_authorize_post_v1,
)


def build_pl_tf_002_pre_network_jit_proof_v1(
    *,
    session_owner_go: str,
    origin_main_sha: str,
    integrity_backend: object | None = None,
) -> dict[str, Any]:
    """Non-secret JIT envelope immediately before bounded productive GET capture."""

    pre = build_pl_tf_002_read_only_get_session_preflight_v1(
        owner_go=session_owner_go,
        origin_main_sha=origin_main_sha,
        integrity_backend=integrity_backend,  # type: ignore[arg-type]
    )
    post_proof = prove_pl_tf_002_session_does_not_authorize_post_v1()
    return {
        "K1_ACQUISITION": "NOT_EXECUTED_IN_JIT",
        "K1_PARSE": "NOT_EXECUTED_IN_JIT",
        "K1_BINDING": "NOT_EXECUTED_IN_JIT",
        "PRODUCTIVE_K1_MATERIAL_PRESENT": "UNKNOWN_UNTIL_SESSION_OPEN",
        "HOST": AUTHORIZED_NETWORK_HOST,
        "TRANSPORT": PRODUCTIVE_TRANSPORT_CLASS,
        "METHOD_ALLOWLIST": list(METHOD_ALLOWLIST),
        "POST": False,
        "ORDER": False,
        "TRADING": False,
        "TREASURY_MUTATION": False,
        "WITHDRAWAL": False,
        "TRANSFER": False,
        "NETWORK_EXECUTION_AUTHORIZED": False,
        "SESSION_OWNER_GO_REQUIRED": SESSION_OWNER_GO,
        "SESSION_OWNER_GO_ACCEPTED": session_owner_go == SESSION_OWNER_GO,
        "PREFLIGHT": pre.to_dict(),
        "POST_STANDING_PROOF": post_proof,
        "REAL_KEYCHAIN_ACCESS_AUTHORIZED_STANDING": REAL_KEYCHAIN_ACCESS_AUTHORIZED is False,
        "EXTERNAL_EFFECT_AUTHORIZED_STANDING": EXTERNAL_EFFECT_AUTHORIZED is False,
        "POST_ALLOWED_STANDING": POST_ALLOWED is False,
        "REAL_VENUE_POST_ALLOWED_STANDING": REAL_VENUE_POST_ALLOWED is False,
    }


def merge_session_k1_jit_facts_v1(
    jit: Mapping[str, Any],
    *,
    credential_acquired: bool,
    k1_handle_bound: bool,
) -> dict[str, Any]:
    out = dict(jit)
    out["K1_ACQUISITION"] = "PASS" if credential_acquired else "FAIL_CLOSED"
    out["K1_PARSE"] = "PASS" if credential_acquired else "FAIL_CLOSED"
    out["K1_BINDING"] = "PASS" if k1_handle_bound else "FAIL_CLOSED"
    out["PRODUCTIVE_K1_MATERIAL_PRESENT"] = credential_acquired is True
    return out
