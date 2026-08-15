"""Read-only preflight for a later OWNER_GO_SHADOW_EXECUTE. Never starts a session."""

from __future__ import annotations

from types import MappingProxyType
from typing import Any, Mapping

from src.ops.canonical_i17_productive_shadow_contract_readiness_v1.constants_v1 import (
    CANONICAL_SHADOW_CONTRACT_OWNER,
    CANONICAL_SHADOW_EVIDENCE_OWNER,
    CANONICAL_SHADOW_IDENTITY_BINDING,
    CANONICAL_SHADOW_PROMOTION_CONSUMER,
    CANONICAL_SHADOW_RUNNER_OWNER,
    LIVE_AUTHORIZED,
    PRODUCTIVE_SHADOW_EXECUTED,
    REQUIRED_OWNER_RELPATHS,
    TESTNET_AUTHORIZED,
)
from src.ops.canonical_i17_productive_shadow_contract_readiness_v1.contract_v1 import (
    build_evidence_pack_contract_v1,
)
from src.ops.canonical_i17_productive_shadow_contract_readiness_v1.lineage_v1 import repo_root
from src.ops.canonical_i17_productive_shadow_contract_readiness_v1.models_v1 import (
    I17ShadowContractReadinessError,
    ShadowReadinessInputV1,
    TerminalState,
)


def _reject(message: str) -> None:
    raise I17ShadowContractReadinessError(message)


def assert_canonical_owners_present_v1(root=None) -> None:
    base = root or repo_root()
    missing = [rel for rel in REQUIRED_OWNER_RELPATHS if not (base / rel).is_file()]
    if missing:
        _reject(f"canonical_owner_missing:{missing}")


def run_shadow_readiness_preflight_v1(
    inp: ShadowReadinessInputV1, *, root=None
) -> Mapping[str, Any]:
    if inp.execute or PRODUCTIVE_SHADOW_EXECUTED:
        _reject("productive_shadow_execute_forbidden_this_pass")
    if inp.network_enabled:
        _reject("network_session_forbidden_this_pass")
    if inp.orders_enabled:
        _reject("order_submit_path_forbidden")
    if inp.live_enabled or LIVE_AUTHORIZED:
        _reject("live_authorized_forbidden")
    if inp.testnet_enabled or TESTNET_AUTHORIZED:
        _reject("testnet_authorized_forbidden")
    if inp.canary_enabled:
        _reject("canary_forbidden")
    if inp.promotion_authority or inp.auto_promote:
        _reject("promotion_authority_forbidden")
    assert_canonical_owners_present_v1(root)
    pack = build_evidence_pack_contract_v1(inp)
    claims = {
        "ok": True,
        "canonical_owners_resolved": True,
        "canonical_shadow_contract_owner": CANONICAL_SHADOW_CONTRACT_OWNER,
        "canonical_shadow_runner_owner": CANONICAL_SHADOW_RUNNER_OWNER,
        "canonical_shadow_evidence_owner": CANONICAL_SHADOW_EVIDENCE_OWNER,
        "canonical_shadow_identity_binding": CANONICAL_SHADOW_IDENTITY_BINDING,
        "canonical_shadow_promotion_consumer": CANONICAL_SHADOW_PROMOTION_CONSUMER,
        "evidence_pack": dict(pack),
        "network_capable_path_present_but_not_executed": True,
        "order_capable_path_reachable_from_r4": False,
        "order_effect": "NONE",
        "productive_shadow_executed": False,
        "productive_shadow_evidence_proven": False,
        "promotion_eligible": False,
        "promotion_eligible_is_grant": False,
        "terminal_state": TerminalState.BLOCKED_PENDING_SHADOW_EXECUTE_GO.value,
        "owner_go_shadow_execute_required": True,
    }
    return MappingProxyType(claims)
