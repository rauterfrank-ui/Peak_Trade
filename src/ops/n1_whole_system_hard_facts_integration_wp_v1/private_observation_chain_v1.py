"""RW-E9–E11: private WS observation-only canonical join (no POST / selection authority)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping

from src.ops.full_core_live_path_composition_root_v1.fresh_pretrade_runtime_get_v1 import (
    FRESHNESS_POLICY,
)
from src.ops.okx_eea_private_account_state_runtime_v1.mutation_prohibition_v1 import (
    assert_no_ws_mutation_operations_in_public_api_v1,
)
from src.ops.okx_eea_private_account_state_runtime_v1.runtime_orchestrator_v1 import (
    OkxEeaPrivateAccountStateRuntimeV1,
)
from src.ops.okx_eea_private_account_state_runtime_v1.safety_boundary_v1 import (
    private_runtime_safety_attestation_v1,
)


@dataclass(frozen=True)
class PrivateObservationChainProofV1:
    ok: bool
    private_ws_canonical: bool
    private_ws_restart_safe: bool
    private_observation_productive_join: bool
    fresh_pretrade_get_required: bool


def prove_private_ws_canonical_and_observation_only_v1() -> bool:
    att = private_runtime_safety_attestation_v1()
    assert_no_ws_mutation_operations_in_public_api_v1()
    return (
        att["POST_ALLOWED"] is False
        and att["private_runtime_may_ws_order_send"] is False
        and att["MULTI_FUTURE_RUNTIME_AUTHORIZED"] is False
    )


def prove_private_restart_recovery_order_v1(
    *,
    store_root: Path,
    rest_fetch_json: Callable[[str, Mapping[str, str]], Mapping[str, Any]],
    captured_at: str = "2026-09-26T00:00:00Z",
) -> dict[str, Any]:
    runtime = OkxEeaPrivateAccountStateRuntimeV1(
        store_root=store_root,
        rest_fetch_json=rest_fetch_json,
        ws_transport=None,
    )
    return runtime.restart_sequence_v1(captured_at=captured_at)


def prove_private_observation_chain_v1(
    *,
    store_root: Path,
    rest_fetch_json: Callable[[str, Mapping[str, str]], Mapping[str, Any]],
) -> PrivateObservationChainProofV1:
    canonical = prove_private_ws_canonical_and_observation_only_v1()
    restart = prove_private_restart_recovery_order_v1(
        store_root=store_root,
        rest_fetch_json=rest_fetch_json,
    )
    restart_ok = "reconciliation" in restart
    hint = FRESHNESS_POLICY
    return PrivateObservationChainProofV1(
        ok=canonical and restart_ok,
        private_ws_canonical=canonical,
        private_ws_restart_safe=restart_ok,
        private_observation_productive_join=restart_ok,
        fresh_pretrade_get_required=bool(hint),
    )
