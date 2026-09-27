"""CURRENT productive Enter one-shot E2E runtime handoff (prepare only).

Chains Cap-2.4 provenance → Full-Core PRE_EXTERNAL closure → fresh
FINAL_ORDER_ENVELOPE.json → optional K1 pre-live boundary proof → governed
POST CLI handoff. Does not consume POST Owner-GO durably. Does not POST.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from src.ops.full_core_live_path_composition_root_v1.checkout_independent_credential_os_native_store_acquisition_v1 import (
    OsNativeStoreLookupBackendV1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_k1_runtime_binding_to_one_shot_actual_venue_post_pre_live_boundary_v1 import (
    EXPECTED_BASELINE_ORIGIN_MAIN_SHA as POST_PATH_BOUND_BASELINE_SHA,
    K1_OPAQUE_SIGNING_OWNER_GO,
    POST_OWNER_GO,
    attempt_k1_runtime_binding_to_one_shot_actual_venue_post_pre_live_boundary_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_actual_venue_post_owner_go_durable_consume_v1 import (
    load_durable_post_owner_go_consume_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_governed_cycle_orchestrator_v1 import (
    DISPOSITION_PRE_EXTERNAL_EFFECT,
)
from src.ops.full_core_live_path_composition_root_v1.final_order_envelope_v1 import (
    FinalOrderEnvelopeV1,
    assert_envelope_unmodified_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_fresh_executable_enter_final_order_envelope_runtime_reach_to_one_shot_post_join_boundary_v1 import (
    resolve_fresh_executable_enter_final_order_envelope_from_pre_external_closure_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_29p_cap24_bound_instrument_provenance_handoff_v1 import (
    CurrentProductive29PCap24ProvenanceHandoffError,
    acquire_current_productive_29p_cap24_bound_instrument_provenance_handoff_v1,
    default_current_productive_cap24_runtime_state_root_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_29p_chain_baseline_contract_v1 import (
    CurrentProductive29PRuntimeIntegrityBackendV1,
    GitCurrentProductive29PRuntimeIntegrityBackendV1,
    assert_current_productive_29p_execution_identity_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_actual_venue_post_with_fresh_envelope_bound_single_use_permit_v1 import (
    prove_pre_live_actual_venue_post_readiness_from_pre_external_closure_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_fresh_cap23_cap24_decision_and_one_shot_real_post_readiness_v1 import (
    _assert_no_secrets,
    _persist_json,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_full_core_pre_external_closure_v1 import (
    OWNER_GO as PRE_EXTERNAL_OWNER_GO,
    CurrentProductiveFullCorePreExternalClosureError,
    CurrentProductiveFullCorePreExternalClosureResultV1,
    execute_current_productive_full_core_pre_external_closure_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.d4_d5_genesis_runtime_orchestrator_v1 import (
    persist_manifest_sha256_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.package_1_s6_mapping_classification_v1 import (
    verify_manifest_sha256_v1,
)
from src.ops.single_selected_future_runtime_binding_v1.models_v1 import BoundInstrumentV1

OWNER_GO = "OWNER_GO_CURRENT_PRODUCTIVE_ONE_SHOT_ENTER_E2E_RUNTIME_HANDOFF_V1"
THIS_SLICE = "11.2.1.DP.FULL_CORE_CURRENT_PRODUCTIVE_ONE_SHOT_ENTER_E2E_RUNTIME_HANDOFF_V1"
HANDOFF_FILENAME = "ONE_SHOT_ENTER_E2E_RUNTIME_HANDOFF.json"
ENVELOPE_FILENAME = "FINAL_ORDER_ENVELOPE.json"
FALSE_TOKEN = "false"
TRUE_TOKEN = "true"
_REPO_ROOT = Path(__file__).resolve().parents[3]


class CurrentProductiveOneShotEnterE2ERuntimeHandoffError(RuntimeError):
    """Fail-closed one-shot Enter E2E prepare violation."""


@dataclass(frozen=True)
class CurrentProductiveOneShotEnterE2ERuntimeHandoffResultV1:
    handoff_store_root: str
    closure_store_root: str
    post_durable_store_root: str
    envelope_json_path: str
    origin_main_sha: str
    post_path_bound_baseline_sha: str
    pre_external_owner_go: str
    post_owner_go: str
    k1_owner_go: str
    terminal_disposition: str
    envelope_id: str
    envelope_digest: str
    pre_live_proof_complete: str
    k1_pre_live_attempted: str
    e2e_runtime_ready: str
    final_operator_command: str
    final_pre_live_command: str
    manifest_verify_rc: int


def _utc_now_iso_v1() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _resolve_origin_main_sha_v1(
    *,
    declared: str | None,
    integrity_backend: CurrentProductive29PRuntimeIntegrityBackendV1 | None,
) -> str:
    backend = integrity_backend or GitCurrentProductive29PRuntimeIntegrityBackendV1(
        repo_root=_REPO_ROOT
    )
    live = backend.resolve_origin_main_sha_v1().strip().lower()
    if declared:
        decl = str(declared).strip().lower()
        if decl != live:
            raise CurrentProductiveOneShotEnterE2ERuntimeHandoffError(
                "ORIGIN_MAIN_SHA_MISMATCH_WITH_LIVE"
            )
        return decl
    return live


def _assert_post_store_fresh_v1(store_root: Path) -> None:
    durable = load_durable_post_owner_go_consume_v1(store_root=store_root)
    if durable.get("consumed") is True:
        raise CurrentProductiveOneShotEnterE2ERuntimeHandoffError(
            "POST_DURABLE_STORE_ALREADY_CONSUMED"
        )
    ext_path = store_root / "external_effect_durable_consume_v1.json"
    if ext_path.is_file():
        payload = json.loads(ext_path.read_text(encoding="utf-8"))
        if isinstance(payload, dict) and payload.get("consumed") is True:
            raise CurrentProductiveOneShotEnterE2ERuntimeHandoffError(
                "EXTERNAL_EFFECT_DURABLE_STORE_ALREADY_CONSUMED"
            )


def _build_final_post_command_v1(
    *,
    post_store_root: Path,
    envelope_json: Path,
    k1_backend_flag: str,
) -> str:
    script = (
        "./scripts/pt scripts/ops/"
        "run_current_productive_actual_venue_post_with_fresh_envelope_bound_single_use_permit_v1.py"
    )
    return (
        f"{script} "
        f"--store-root {post_store_root} "
        f"--envelope-json {envelope_json} "
        f"--k1-backend {k1_backend_flag} "
        f"--confirm-real-venue-post"
    )


def _build_pre_live_command_v1(
    *,
    post_store_root: Path,
    envelope_json: Path,
    k1_backend_flag: str,
) -> str:
    script = (
        "./scripts/pt scripts/ops/"
        "run_current_productive_actual_venue_post_with_fresh_envelope_bound_single_use_permit_v1.py"
    )
    return (
        f"{script} "
        f"--store-root {post_store_root} "
        f"--envelope-json {envelope_json} "
        f"--k1-backend {k1_backend_flag} "
        f"--pre-live-only"
    )


def prepare_current_productive_one_shot_enter_e2e_runtime_handoff_v1(
    *,
    owner_go: str,
    pre_external_owner_go: str,
    post_owner_go: str,
    k1_owner_go: str,
    productivity_root: Path | None,
    lane_state_root: Path,
    post_durable_store_root: Path,
    origin_main_sha: str | None = None,
    binding_epoch: str | None = None,
    execute_network: bool = False,
    vault_file: Path | str | None = None,
    evidence_root: Path | None = None,
    prove_k1_pre_live: bool = False,
    use_macos_k1: bool = False,
    k1_backend: OsNativeStoreLookupBackendV1 | None = None,
    bound_instrument_override: BoundInstrumentV1 | None = None,
    execution_integrity_backend: CurrentProductive29PRuntimeIntegrityBackendV1 | None = None,
    fresh_get_transport: object | None = None,
    candles_payload: Mapping[str, Any] | None = None,
    market_kwargs: Mapping[str, Any] | None = None,
    g17_typed_vol_producers: Mapping[str, object] | None = None,
) -> CurrentProductiveOneShotEnterE2ERuntimeHandoffResultV1:
    """Prepare governed Enter one-shot through PRE_EXTERNAL + handoff (no POST)."""

    if str(owner_go or "") != OWNER_GO:
        raise CurrentProductiveOneShotEnterE2ERuntimeHandoffError("HANDOFF_OWNER_GO_MISMATCH")
    if str(pre_external_owner_go or "") not in (
        PRE_EXTERNAL_OWNER_GO,
        f"OWNER_GO_{PRE_EXTERNAL_OWNER_GO}",
    ):
        raise CurrentProductiveOneShotEnterE2ERuntimeHandoffError("PRE_EXTERNAL_OWNER_GO_MISMATCH")
    if str(post_owner_go or "") != POST_OWNER_GO:
        raise CurrentProductiveOneShotEnterE2ERuntimeHandoffError("POST_OWNER_GO_MISMATCH")
    if str(k1_owner_go or "") != K1_OPAQUE_SIGNING_OWNER_GO:
        raise CurrentProductiveOneShotEnterE2ERuntimeHandoffError("K1_OWNER_GO_MISMATCH")

    repo_sha = _resolve_origin_main_sha_v1(
        declared=origin_main_sha,
        integrity_backend=execution_integrity_backend,
    )
    assert_current_productive_29p_execution_identity_v1(
        declared_origin_main_sha=repo_sha,
        integrity_backend=execution_integrity_backend,
    )

    post_root = Path(post_durable_store_root)
    post_root.mkdir(parents=True, exist_ok=True)
    _assert_post_store_fresh_v1(post_root)

    epoch = str(binding_epoch or _utc_now_iso_v1())
    cap24_prod_root = productivity_root
    if cap24_prod_root is None:
        cap24_prod_root = default_current_productive_cap24_runtime_state_root_v1()

    bound = bound_instrument_override
    if bound is None:
        prod_root = cap24_prod_root
        try:
            handoff = acquire_current_productive_29p_cap24_bound_instrument_provenance_handoff_v1(
                productivity_root=prod_root,
                repository_sha=repo_sha,
                binding_epoch=epoch,
            )
        except CurrentProductive29PCap24ProvenanceHandoffError as exc:
            raise CurrentProductiveOneShotEnterE2ERuntimeHandoffError(str(exc)) from exc
        bound = handoff.bound_instrument

    lane_root = Path(lane_state_root)
    if not lane_root.is_dir():
        raise CurrentProductiveOneShotEnterE2ERuntimeHandoffError("LANE_STATE_ROOT_MISSING")

    try:
        closure: CurrentProductiveFullCorePreExternalClosureResultV1 = (
            execute_current_productive_full_core_pre_external_closure_v1(
                owner_go=pre_external_owner_go,
                origin_main_sha=repo_sha,
                bound_instrument=bound,
                lane_state_root=lane_root,
                fresh_get_transport=fresh_get_transport,
                execute_network=execute_network,
                vault_file=vault_file,
                evidence_root=evidence_root,
                candles_payload=candles_payload,
                market_kwargs=market_kwargs,
                g17_typed_vol_producers=g17_typed_vol_producers,
                execution_integrity_backend=execution_integrity_backend,
                cap24_productivity_root=cap24_prod_root,
            )
        )
    except CurrentProductiveFullCorePreExternalClosureError as exc:
        raise CurrentProductiveOneShotEnterE2ERuntimeHandoffError(str(exc)) from exc

    if str(closure.terminal_disposition or "") != DISPOSITION_PRE_EXTERNAL_EFFECT:
        blocker = str(closure.earliest_remaining_blocker or "PRE_EXTERNAL_NOT_REACHED")
        raise CurrentProductiveOneShotEnterE2ERuntimeHandoffError(blocker)

    envelope = resolve_fresh_executable_enter_final_order_envelope_from_pre_external_closure_v1(
        closure
    )
    assert_envelope_unmodified_v1(envelope)

    closure_store = Path(closure.store_root)
    envelope_path = closure_store / ENVELOPE_FILENAME
    if not envelope_path.is_file():
        raise CurrentProductiveOneShotEnterE2ERuntimeHandoffError(
            "FINAL_ORDER_ENVELOPE_JSON_MISSING"
        )

    k1_flag = "macos" if (prove_k1_pre_live or use_macos_k1) else "none"
    pre_live_ok = FALSE_TOKEN
    k1_attempted = FALSE_TOKEN
    if prove_k1_pre_live:
        k1_attempted = TRUE_TOKEN
        if use_macos_k1 and k1_backend is None:
            from src.ops.full_core_live_path_composition_root_v1.current_productive_k1_runtime_binding_to_one_shot_actual_venue_post_pre_live_boundary_v1 import (
                resolve_macos_security_framework_k1_lookup_backend_v1,
            )

            k1_backend = resolve_macos_security_framework_k1_lookup_backend_v1(
                k1_owner_go=k1_owner_go
            )
        if k1_backend is None:
            raise CurrentProductiveOneShotEnterE2ERuntimeHandoffError(
                "K1_BACKEND_REQUIRED_FOR_PRE_LIVE_PROOF"
            )
        k1_result = attempt_k1_runtime_binding_to_one_shot_actual_venue_post_pre_live_boundary_v1(
            k1_owner_go=k1_owner_go,
            post_owner_go=post_owner_go,
            baseline_origin_main_sha=POST_PATH_BOUND_BASELINE_SHA,
            envelope=envelope,
            store_root=post_root,
            k1_backend=k1_backend,
            use_macos_security_framework=False,
            repo_root=_REPO_ROOT,
        )
        pre_live_ok = k1_result.pre_live_proof_complete
    else:
        pre = prove_pre_live_actual_venue_post_readiness_from_pre_external_closure_v1(
            owner_go=post_owner_go,
            baseline_origin_main_sha=POST_PATH_BOUND_BASELINE_SHA,
            closure=closure,
            store_root=post_root,
            k1_backend=None,
        )
        pre_live_ok = str(pre.get("PRE_LIVE_PROOF_COMPLETE") or FALSE_TOKEN)

    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    handoff_store = (
        Path(evidence_root)
        if evidence_root is not None
        else _REPO_ROOT
        / "evidence"
        / "ops"
        / "full_core_current_productive_one_shot_enter_e2e_runtime_handoff_v1"
        / run_id
    )
    handoff_store.mkdir(parents=True, exist_ok=True)

    final_post_cmd = _build_final_post_command_v1(
        post_store_root=post_root,
        envelope_json=envelope_path,
        k1_backend_flag="macos",
    )
    final_pre_live_cmd = _build_pre_live_command_v1(
        post_store_root=post_root,
        envelope_json=envelope_path,
        k1_backend_flag="macos",
    )

    e2e_ready = TRUE_TOKEN
    if prove_k1_pre_live and pre_live_ok != TRUE_TOKEN:
        e2e_ready = FALSE_TOKEN

    claims: dict[str, Any] = {
        "DOCUMENT_CLASS": THIS_SLICE,
        "OWNER_GO": OWNER_GO,
        "ORIGIN_MAIN_SHA": repo_sha,
        "POST_PATH_BOUND_BASELINE_SHA": POST_PATH_BOUND_BASELINE_SHA,
        "PRE_EXTERNAL_OWNER_GO": pre_external_owner_go,
        "POST_OWNER_GO": post_owner_go,
        "K1_OWNER_GO": k1_owner_go,
        "CLOSURE_STORE_ROOT": str(closure_store),
        "POST_DURABLE_STORE_ROOT": str(post_root),
        "ENVELOPE_JSON_PATH": str(envelope_path),
        "ENVELOPE_ID": envelope.envelope_id,
        "ENVELOPE_DIGEST": envelope.envelope_digest,
        "TERMINAL_DISPOSITION": closure.terminal_disposition,
        "PRE_LIVE_PROOF_COMPLETE": pre_live_ok,
        "K1_PRE_LIVE_ATTEMPTED": k1_attempted,
        "E2E_RUNTIME_READY": e2e_ready,
        "REAL_VENUE_POST_ATTEMPTED": FALSE_TOKEN,
        "REAL_VENUE_POST_PERFORMED": FALSE_TOKEN,
        "PERMIT_CONSUMED_DURABLE": FALSE_TOKEN,
        "FINAL_OPERATOR_COMMAND": final_post_cmd,
        "FINAL_PRE_LIVE_COMMAND": final_pre_live_cmd,
    }
    _assert_no_secrets(claims)
    _persist_json(path=handoff_store / HANDOFF_FILENAME, payload=claims)
    persist_manifest_sha256_v1(store_root=handoff_store)
    manifest_rc = verify_manifest_sha256_v1(store_root=handoff_store)

    return CurrentProductiveOneShotEnterE2ERuntimeHandoffResultV1(
        handoff_store_root=str(handoff_store),
        closure_store_root=str(closure_store),
        post_durable_store_root=str(post_root),
        envelope_json_path=str(envelope_path),
        origin_main_sha=repo_sha,
        post_path_bound_baseline_sha=POST_PATH_BOUND_BASELINE_SHA,
        pre_external_owner_go=pre_external_owner_go,
        post_owner_go=post_owner_go,
        k1_owner_go=k1_owner_go,
        terminal_disposition=str(closure.terminal_disposition),
        envelope_id=envelope.envelope_id,
        envelope_digest=envelope.envelope_digest,
        pre_live_proof_complete=pre_live_ok,
        k1_pre_live_attempted=k1_attempted,
        e2e_runtime_ready=e2e_ready,
        final_operator_command=final_post_cmd,
        final_pre_live_command=final_pre_live_cmd,
        manifest_verify_rc=manifest_rc,
    )


__all__ = [
    "HANDOFF_FILENAME",
    "OWNER_GO",
    "POST_PATH_BOUND_BASELINE_SHA",
    "THIS_SLICE",
    "CurrentProductiveOneShotEnterE2ERuntimeHandoffError",
    "CurrentProductiveOneShotEnterE2ERuntimeHandoffResultV1",
    "prepare_current_productive_one_shot_enter_e2e_runtime_handoff_v1",
]
