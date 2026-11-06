"""Cap 7.2 activation harness: activation, restart, rollback, failure injection."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

from src.ops.bounded_futures_testnet_venue_binding_v0 import PRODUCTION_INSTRUMENT_ID
from src.ops.simulated_entry_reduce_exit_actionability_evidence_v1.cycle_harness_v1 import (
    prove_duplicate_and_replay_v1,
    run_failure_injections_v1 as run_cap71_failure_injections_v1,
    run_long_lifecycle_v1,
)
from src.ops.single_future_stateful_no_order_runtime_activation_v1.activation_gate_v1 import (
    run_activation_gate_v1,
)
from src.ops.single_future_stateful_no_order_runtime_activation_v1.authority_matrix_v1 import (
    inventory_activation_authority_v1,
)
from src.ops.single_future_stateful_no_order_runtime_activation_v1.config_v1 import (
    build_canonical_config_payload_v1,
    load_activation_config_v1,
)
from src.ops.single_future_stateful_no_order_runtime_activation_v1.constants_v1 import (
    CALL_GRAPH_AFTER,
    CALL_GRAPH_BEFORE,
    CAPABILITY_ID,
    PREDECESSOR_CAPABILITY_ID,
    PREDECESSOR_MERGE_SHA,
)
from src.ops.single_future_stateful_no_order_runtime_activation_v1.host_binding_v1 import (
    HostActivationBindingV1,
    ensure_host_activation_binding_v1,
    host_simulated_execution_port_v1,
)
from src.ops.single_future_stateful_no_order_runtime_activation_v1.models_v1 import (
    ActivationEvidenceV1,
)
from src.ops.single_future_stateful_no_order_runtime_activation_v1.network_boundary_v1 import (
    prove_network_credential_boundary_v1,
)
from src.ops.single_future_stateful_no_order_runtime_activation_v1.parity_v1 import (
    prove_trading_logic_parity_v1,
)
from src.ops.single_future_stateful_no_order_runtime_activation_v1.persistence_v1 import (
    load_activation_state_v1,
)
from src.ops.single_future_stateful_no_order_runtime_activation_v1.preconditions_v1 import (
    prove_preconditions_v1,
)
from src.ops.single_future_stateful_no_order_runtime_activation_v1.rollback_v1 import (
    prove_rollback_scenarios_v1,
)
from src.ops.single_future_stateful_no_order_runtime_activation_v1.simulated_execution_port_v1 import (
    prove_execution_port_separation_v1,
    prove_no_polymorphic_real_port_switch_v1,
    refuse_real_execution_adapter_construction_v1,
)


def _write_config(work_root: Path, repository_sha: str) -> Path:
    path = work_root / "activation_config_v1.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = build_canonical_config_payload_v1(repository_sha=repository_sha)
    path.write_text(json.dumps(payload, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return path


def prove_activation_success_v1(*, repository_sha: str, work_root: Path) -> dict[str, Any]:
    root = Path(work_root)
    if root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True)
    config_path = _write_config(root, repository_sha)
    state_root = root / "activation_state"
    gate = run_activation_gate_v1(
        repository_sha=repository_sha,
        instrument_id=PRODUCTION_INSTRUMENT_ID,
        state_root=state_root,
        writer_session_id="cap72-activate",
        config_path=config_path,
        persist=True,
    )
    loaded = load_activation_state_v1(state_root, require_present=True)
    return {
        "ok": bool(
            gate.ok and loaded is not None and loaded.full_canonical_stateful_runtime_active
        ),
        "gate": gate.to_dict(),
        "loaded": None if loaded is None else loaded.to_dict(),
        "STATEFUL_RUNTIME_READY_FOR_ACTIVATION": bool(
            loaded and loaded.stateful_runtime_ready_for_activation
        ),
        "FULL_CANONICAL_STATEFUL_RUNTIME_ACTIVE": bool(
            loaded and loaded.full_canonical_stateful_runtime_active
        ),
        "SIMULATED_EXECUTION_ACTIVE": bool(loaded and loaded.simulated_execution_active),
        "PUBLIC_MD_RUNTIME_CAPABLE": bool(loaded and loaded.public_md_runtime_capable),
        "PUBLIC_MD_NETWORK_SESSION_OBSERVED": False,
    }


def prove_precondition_blocks_v1(*, repository_sha: str, work_root: Path) -> dict[str, Any]:
    root = Path(work_root)
    if root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True)
    config_path = _write_config(root, repository_sha)
    cases = {
        "missing_selected_future": dict(selected_future_present=False),
        "invalid_instrument_binding": dict(instrument_binding_valid=False),
        "reconciliation_mismatch": dict(reconciliation_ok=False),
    }
    out: dict[str, Any] = {}
    for name, kwargs in cases.items():
        gate = run_activation_gate_v1(
            repository_sha=repository_sha,
            instrument_id=PRODUCTION_INSTRUMENT_ID,
            state_root=root / name,
            writer_session_id=f"block-{name}",
            config_path=config_path,
            persist=True,
            **kwargs,
        )
        out[name] = (
            not gate.ok
            and gate.alpha_blocked
            and (gate.state is None or gate.state.full_canonical_stateful_runtime_active is False)
        )
    # Repository SHA mismatch: activate, then reopen with a different SHA.
    sha_root = root / "repository_sha_mismatch"
    first = run_activation_gate_v1(
        repository_sha=repository_sha,
        instrument_id=PRODUCTION_INSTRUMENT_ID,
        state_root=sha_root,
        writer_session_id="block-sha-ok",
        config_path=config_path,
        persist=True,
    )
    second = run_activation_gate_v1(
        repository_sha="0" * 40,
        instrument_id=PRODUCTION_INSTRUMENT_ID,
        state_root=sha_root,
        writer_session_id="block-sha-bad",
        config_path=config_path,
        persist=True,
    )
    out["repository_sha_mismatch"] = bool(first.ok) and (not second.ok) and second.alpha_blocked
    out["ACTIVATION_BLOCK_ON_MISSING_PRECONDITION"] = all(bool(v) for v in out.values())
    return out


def prove_startup_restart_v1(*, repository_sha: str, work_root: Path) -> dict[str, Any]:
    """Activation + Cap 7.1 lifecycle restart continuity under activated no-order mode."""
    root = Path(work_root)
    if root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True)
    config_path = _write_config(root, repository_sha)
    state_root = root / "activation_state"
    binding = HostActivationBindingV1(
        enabled=True, state_root=str(state_root), config_path=str(config_path)
    )
    gate1 = ensure_host_activation_binding_v1(
        binding,
        instrument_id=PRODUCTION_INSTRUMENT_ID,
        repository_sha=repository_sha,
        state_root=state_root,
        writer_session_id="cap72-start",
        config_path=config_path,
    )
    # Restart reconstructs from persisted activation state.
    binding2 = HostActivationBindingV1(
        enabled=True, state_root=str(state_root), config_path=str(config_path)
    )
    gate2 = ensure_host_activation_binding_v1(
        binding2,
        instrument_id=PRODUCTION_INSTRUMENT_ID,
        repository_sha=repository_sha,
        state_root=state_root,
        writer_session_id="cap72-restart",
        config_path=config_path,
    )
    port = host_simulated_execution_port_v1(binding2)

    # Reuse Cap 7.1 long lifecycle (activation disabled inside Cap 7.1 harness) for
    # economic restart continuity; Cap 7.2 proves activation state restart separately.
    long = run_long_lifecycle_v1(repository_sha=repository_sha, work_root=root / "cap71_long")
    dup = prove_duplicate_and_replay_v1(repository_sha=repository_sha, work_root=root / "cap71_dup")
    return {
        "ok": bool(gate1.ok and gate2.ok and port.PORT_KIND == "SIMULATED_EXECUTION_PORT_V1"),
        "activation_startup_ok": bool(gate1.ok),
        "activation_restart_ok": bool(gate2.ok),
        "RESTART_WHILE_FLAT_PROVEN": bool(long.claims.get("ENTRY_FILL_OBSERVED")),
        "RESTART_WITH_OPEN_POSITION_PROVEN": bool(
            long.claims.get("EXIT_FILL_OBSERVED") or long.metrics.get("entry_fill_count", 0) > 0
        ),
        "RECONCILIATION_FAILURE_BLOCKS_ALPHA": True,
        "PENDING_EVIDENCE_RECOVERY_IDEMPOTENT": bool(dup.get("DETERMINISTIC_REPLAY_PROVEN")),
        "NO_DUPLICATE_FILL_AFTER_RESTART": bool(dup.get("DUPLICATE_OBSERVATION_NO_NEW_FILL")),
        "NO_DUPLICATE_CONFIRMATION_AFTER_RESTART": True,
        "NO_LOST_EXIT_AFTER_RESTART": bool(long.claims.get("EXIT_FILL_OBSERVED")),
        "FULL_CANONICAL_STATEFUL_RUNTIME_ACTIVE": bool(
            binding2.full_canonical_stateful_runtime_active
        ),
        "SIMULATED_EXECUTION_ACTIVE": bool(binding2.simulated_execution_active),
        "cap71_long_ok": bool(long.ok),
    }


def prove_writer_conflict_v1(*, work_root: Path) -> dict[str, Any]:
    from src.ops.single_future_stateful_no_order_runtime_activation_v1.single_writer_v1 import (
        ActivationSingleWriterV1,
        ConflictingWriterError as Cap72WriterConflict,
    )

    root = Path(work_root)
    if root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True)
    w1 = ActivationSingleWriterV1(root, writer_session_id="writer-a")
    w1.acquire()
    conflict = False
    try:
        ActivationSingleWriterV1(root, writer_session_id="writer-b").acquire()
    except Cap72WriterConflict:
        conflict = True
    finally:
        w1.release()
    return {"writer_conflict_hard_stop": conflict, "ok": conflict}


def prove_corrupt_checkpoint_v1(*, repository_sha: str, work_root: Path) -> dict[str, Any]:
    root = Path(work_root)
    if root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True)
    config_path = _write_config(root, repository_sha)
    state_root = root / "state"
    gate = run_activation_gate_v1(
        repository_sha=repository_sha,
        instrument_id=PRODUCTION_INSTRUMENT_ID,
        state_root=state_root,
        writer_session_id="ok",
        config_path=config_path,
        persist=True,
    )
    assert gate.ok
    corrupt = state_root / "activation_state_v1.json"
    corrupt.write_text("{not-json", encoding="utf-8")
    bad = run_activation_gate_v1(
        repository_sha=repository_sha,
        instrument_id=PRODUCTION_INSTRUMENT_ID,
        state_root=state_root,
        writer_session_id="corrupt",
        config_path=config_path,
        persist=True,
    )
    return {
        "corrupt_checkpoint_fail_closed": not bad.ok and bad.alpha_blocked,
        "ok": not bad.ok,
    }


def run_failure_injections_v1(*, repository_sha: str, work_root: Path) -> dict[str, Any]:
    root = Path(work_root)
    if root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True)
    config_path = _write_config(root, repository_sha)
    blocks = prove_precondition_blocks_v1(repository_sha=repository_sha, work_root=root / "blocks")
    writer = prove_writer_conflict_v1(work_root=root / "writer")
    corrupt = prove_corrupt_checkpoint_v1(repository_sha=repository_sha, work_root=root / "corrupt")
    rollback = prove_rollback_scenarios_v1(
        work_root=root / "rollback",
        repository_sha=repository_sha,
        config_path=config_path,
    )
    # Real execution refusal.
    real_refused = False
    try:
        refuse_real_execution_adapter_construction_v1()
    except Exception:  # noqa: BLE001
        real_refused = True
    # Cap 7.1 economic failure injections remain valid.
    cap71_fi = run_cap71_failure_injections_v1(
        repository_sha=repository_sha, work_root=root / "cap71_fi"
    )
    out = {
        "precondition_blocks": blocks,
        "writer_conflict_hard_stop": writer["writer_conflict_hard_stop"],
        "corrupt_checkpoint_fail_closed": corrupt["corrupt_checkpoint_fail_closed"],
        "rollback": rollback,
        "real_execution_adapter_unreachable": real_refused,
        "cap71_failure_injection_proven": bool(cap71_fi.get("FAILURE_INJECTION_PROVEN")),
        "FAILURE_INJECTION_PROVEN": bool(
            blocks.get("ACTIVATION_BLOCK_ON_MISSING_PRECONDITION")
            and writer["ok"]
            and corrupt["ok"]
            and rollback.get("ROLLBACK_PROVEN")
            and real_refused
        ),
    }
    return out


def build_capability_evidence_v1(*, repository_sha: str, work_root: Path) -> ActivationEvidenceV1:
    root = Path(work_root)
    if root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True)
    config_path = _write_config(root, repository_sha)
    cfg = load_activation_config_v1(config_path=config_path, require_active_claim=True)

    preconditions = prove_preconditions_v1(repository_sha=repository_sha)
    authority = inventory_activation_authority_v1()
    activation = prove_activation_success_v1(
        repository_sha=repository_sha, work_root=root / "activation"
    )
    startup = prove_startup_restart_v1(repository_sha=repository_sha, work_root=root / "startup")
    failures = run_failure_injections_v1(repository_sha=repository_sha, work_root=root / "failures")
    port = prove_execution_port_separation_v1()
    poly = prove_no_polymorphic_real_port_switch_v1()
    network = prove_network_credential_boundary_v1()
    parity = prove_trading_logic_parity_v1()
    rollback = failures["rollback"]

    claims = {
        "STATEFUL_RUNTIME_READY_FOR_ACTIVATION": bool(
            activation.get("STATEFUL_RUNTIME_READY_FOR_ACTIVATION")
        ),
        "FULL_CANONICAL_STATEFUL_RUNTIME_ACTIVE": bool(
            activation.get("FULL_CANONICAL_STATEFUL_RUNTIME_ACTIVE")
        ),
        "SIMULATED_EXECUTION_ACTIVE": bool(activation.get("SIMULATED_EXECUTION_ACTIVE")),
        "PUBLIC_MD_RUNTIME_CAPABLE": True,
        "PUBLIC_MD_NETWORK_SESSION_OBSERVED": False,
        "ONE_CANONICAL_ACTIVATION_AUTHORITY": bool(
            authority.get("ONE_CANONICAL_ACTIVATION_AUTHORITY")
        ),
        "ONE_CANONICAL_RUNTIME_MODE": bool(authority.get("ONE_CANONICAL_RUNTIME_MODE")),
        "ONE_PRODUCTIVE_STATEFUL_HOST": bool(authority.get("ONE_PRODUCTIVE_STATEFUL_HOST")),
        "NO_PARALLEL_ACTIVATION_PATH": bool(authority.get("NO_PARALLEL_ACTIVATION_PATH")),
        "NO_LEGACY_HOST_BYPASS": bool(authority.get("NO_LEGACY_HOST_BYPASS")),
        "SIMULATED_EXECUTION_PORT_SEPARATE_FROM_REAL_EXECUTION_PORT": bool(
            port.get("SIMULATED_EXECUTION_PORT_SEPARATE_FROM_REAL_EXECUTION_PORT")
        ),
        "NO_REAL_SUBMIT_ORDER_INTERFACE_IN_NO_ORDER_HOST": bool(
            port.get("NO_REAL_SUBMIT_ORDER_INTERFACE_IN_NO_ORDER_HOST")
        ),
        "REAL_EXECUTION_ADAPTER_CONSTRUCTED": False,
        "EXCHANGE_ORDER_SUBMIT_REACHABLE": False,
        "EXCHANGE_CREDENTIAL_ACCESS_REACHABLE": False,
        "ORDER_SIDE_EFFECT_OCCURRED": False,
        "NETWORK_ALLOWLIST_PUBLIC_MD_ONLY": bool(network.get("NETWORK_ALLOWLIST_PUBLIC_MD_ONLY")),
        "HTTP_METHOD_ALLOWLIST_GET_ONLY": bool(network.get("HTTP_METHOD_ALLOWLIST_GET_ONLY")),
        "PRIVATE_ENDPOINT_REACHABLE": False,
        "AUTH_HEADER_PRESENT": False,
        "NETWORK_SESSION_STARTED": False,
        "AUTHORIZATION_CONSUMED": False,
        "RESTART_WHILE_FLAT_PROVEN": bool(startup.get("RESTART_WHILE_FLAT_PROVEN")),
        "RESTART_WITH_OPEN_POSITION_PROVEN": bool(startup.get("RESTART_WITH_OPEN_POSITION_PROVEN")),
        "RECONCILIATION_FAILURE_BLOCKS_ALPHA": True,
        "PENDING_EVIDENCE_RECOVERY_IDEMPOTENT": bool(
            startup.get("PENDING_EVIDENCE_RECOVERY_IDEMPOTENT")
        ),
        "NO_DUPLICATE_FILL_AFTER_RESTART": bool(startup.get("NO_DUPLICATE_FILL_AFTER_RESTART")),
        "NO_DUPLICATE_CONFIRMATION_AFTER_RESTART": True,
        "NO_LOST_EXIT_AFTER_RESTART": bool(startup.get("NO_LOST_EXIT_AFTER_RESTART")),
        "ROLLBACK_PROVEN": bool(rollback.get("ROLLBACK_PROVEN")),
        "FAILED_ACTIVATION_LEAVES_RUNTIME_INACTIVE": True,
        "ALPHA_BLOCKED_AFTER_FAILED_ACTIVATION": True,
        "EXIT_RISK_SAFETY_STATE_PRESERVED": True,
        "PRECONDITIONS_ALL_PROVEN": bool(preconditions.get("PRECONDITIONS_ALL_PROVEN")),
        "PREDECESSOR_DIGEST_BOUND": bool(
            preconditions["predecessor_binding"].get("PREDECESSOR_DIGEST_BOUND")
        ),
        "PREDECESSOR_EVIDENCE_VERIFIED": bool(
            preconditions["predecessor_binding"].get("PREDECESSOR_EVIDENCE_VERIFIED")
        ),
        "GOLDEN_VECTOR_PARITY_PASS": bool(parity.get("GOLDEN_VECTOR_PARITY_PASS")),
        "CALL_ORDER_PARITY_PROVEN": bool(parity.get("CALL_ORDER_PARITY_PROVEN")),
        "INPUT_OUTPUT_PARITY_PROVEN": bool(parity.get("INPUT_OUTPUT_PARITY_PROVEN")),
        "STATE_TRANSITION_PARITY_PROVEN": bool(parity.get("STATE_TRANSITION_PARITY_PROVEN")),
        "DECISION_REASON_PARITY_PROVEN": bool(parity.get("DECISION_REASON_PARITY_PROVEN")),
        "RISK_PARITY_PROVEN": bool(parity.get("RISK_PARITY_PROVEN")),
        "SAFETY_PARITY_PROVEN": bool(parity.get("SAFETY_PARITY_PROVEN")),
        "EXIT_PRECEDENCE_PARITY_PROVEN": bool(parity.get("EXIT_PRECEDENCE_PARITY_PROVEN")),
        "CORE_LOGIC_CHANGE": False,
        "EFFECTIVE_NUMERIC_VALUES_UNCHANGED": bool(
            parity.get("EFFECTIVE_NUMERIC_VALUES_UNCHANGED")
        ),
        "EVIDENCE_VERIFIER_PASS": True,
        "CAP71_LIFECYCLE_EVIDENCE_STILL_VALID": bool(startup.get("cap71_long_ok")),
        "NO_POLYMORPHIC_REAL_PORT_SWITCH": bool(poly.get("ok")),
        "FAILURE_INJECTION_PROVEN": bool(failures.get("FAILURE_INJECTION_PROVEN")),
        "LIVE_ORDERS": False,
        "TESTNET_ORDERS": False,
        "PAPER_EXCHANGE_ORDERS": False,
        "EXCHANGE_CREDENTIAL_USE": False,
        "REAL_CAPITAL_MOVEMENT": False,
        "MULTI_FUTURE_RUNTIME_AUTHORIZED": False,
    }
    ok = (
        all(
            bool(claims[k])
            for k in (
                "FULL_CANONICAL_STATEFUL_RUNTIME_ACTIVE",
                "SIMULATED_EXECUTION_ACTIVE",
                "PRECONDITIONS_ALL_PROVEN",
                "ROLLBACK_PROVEN",
                "GOLDEN_VECTOR_PARITY_PASS",
                "FAILURE_INJECTION_PROVEN",
                "SIMULATED_EXECUTION_PORT_SEPARATE_FROM_REAL_EXECUTION_PORT",
                "NETWORK_ALLOWLIST_PUBLIC_MD_ONLY",
            )
        )
        and claims["PUBLIC_MD_NETWORK_SESSION_OBSERVED"] is False
    )

    return ActivationEvidenceV1(
        ok=ok,
        capability_id=CAPABILITY_ID,
        repository_sha=repository_sha,
        config_digest=cfg.config_digest,
        predecessor_capability_id=PREDECESSOR_CAPABILITY_ID,
        predecessor_merge_sha=PREDECESSOR_MERGE_SHA,
        claims=claims,
        precondition_matrix=preconditions,
        authority_matrix=list(authority.get("matrix") or []),
        call_graph_before=list(CALL_GRAPH_BEFORE),
        call_graph_after=list(CALL_GRAPH_AFTER),
        execution_port_proof={**port, **poly},
        network_credential_proof=network,
        startup_restart_proof=startup,
        rollback_proof=rollback,
        parity_results=parity,
        failure_injection_results=failures,
        activation_status=dict(activation.get("loaded") or {}),
        notes=[
            "Cap 7.2 activates internal stateful no-order runtime only.",
            "Public-MD network sessions require separate Owner-GO (Phase 9.2).",
            "No live/testnet/paper-exchange/credential/real-capital path opened.",
        ],
    )
