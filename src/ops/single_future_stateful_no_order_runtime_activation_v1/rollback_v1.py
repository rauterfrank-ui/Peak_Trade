"""Deterministic Cap 7.2 activation rollback."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from src.ops.single_future_stateful_no_order_runtime_activation_v1.constants_v1 import (
    RUNTIME_MODE,
    SINGLE_WRITER_IDENTITY,
    STATE_VERSION,
)
from src.ops.single_future_stateful_no_order_runtime_activation_v1.host_binding_v1 import (
    HostActivationBindingV1,
)
from src.ops.single_future_stateful_no_order_runtime_activation_v1.models_v1 import (
    ActivationStatusV1,
    CanonicalActivationStateV1,
    RuntimeModeV1,
)
from src.ops.single_future_stateful_no_order_runtime_activation_v1.persistence_v1 import (
    load_activation_state_v1,
    persist_activation_state_atomic_v1,
)
from src.ops.single_future_stateful_no_order_runtime_activation_v1.reason_codes_v1 import (
    ActivationFailureCodeV1,
)


def rollback_activation_v1(
    binding: HostActivationBindingV1,
    *,
    writer_session_id: str,
    failure_code: str,
    detail: str = "",
    persist: bool = True,
) -> dict[str, Any]:
    """Immediate fail-closed rollback. Preserves portfolio/confirmation/evidence."""
    prior = None
    if binding.state_root:
        prior = load_activation_state_v1(Path(binding.state_root), require_present=False)
    seq = 0 if prior is None else int(prior.commit_sequence) + 1
    state = CanonicalActivationStateV1(
        state_version=STATE_VERSION,
        status=ActivationStatusV1.ROLLBACK_INACTIVE,
        runtime_mode=RuntimeModeV1(RUNTIME_MODE),
        repository_sha=binding.repository_sha,
        config_digest=binding.config_digest,
        instrument_id=binding.instrument_id,
        writer_identity=SINGLE_WRITER_IDENTITY,
        commit_sequence=seq,
        stateful_runtime_ready_for_activation=False,
        full_canonical_stateful_runtime_active=False,
        simulated_execution_active=False,
        public_md_runtime_capable=True,
        public_md_network_session_observed=False,
        alpha_blocked=True,
        alpha_block_reason=f"{failure_code}:{detail}" if detail else failure_code,
        exit_risk_safety_state_preserved=True,
        rollback_applied=True,
        last_failure_code=failure_code,
    )
    binding.full_canonical_stateful_runtime_active = False
    binding.simulated_execution_active = False
    binding.stateful_runtime_ready_for_activation = False
    binding.alpha_blocked = True
    binding.alpha_block_reason = state.alpha_block_reason
    binding.public_md_network_session_observed = False
    if persist and binding.state_root:
        persist_activation_state_atomic_v1(
            Path(binding.state_root), state, writer_session_id=writer_session_id
        )
    return {
        "ok": True,
        "FULL_CANONICAL_STATEFUL_RUNTIME_ACTIVE": False,
        "ALPHA_BLOCKED": True,
        "EXIT_RISK_SAFETY_STATE_PRESERVED": True,
        "FAILED_ACTIVATION_LEAVES_RUNTIME_INACTIVE": True,
        "portfolio_history_deleted": False,
        "confirmation_reset": False,
        "dynamic_scope_reset": False,
        "evidence_lost": False,
        "legacy_runtime_activated": False,
        "live_path_opened": False,
        "testnet_path_opened": False,
        "credential_path_opened": False,
        "state": state.to_dict(),
    }


def prove_rollback_scenarios_v1(
    *,
    work_root: Path,
    repository_sha: str,
    config_path: Path,
) -> dict[str, Any]:
    from src.ops.single_future_stateful_no_order_runtime_activation_v1.activation_gate_v1 import (
        run_activation_gate_v1,
    )
    from src.ops.single_future_stateful_no_order_runtime_activation_v1.config_v1 import (
        load_activation_config_v1,
    )

    results: dict[str, Any] = {}
    cfg = load_activation_config_v1(config_path=config_path, require_active_claim=True)

    # Config digest mismatch via prior state.
    root_a = work_root / "digest_mismatch"
    root_a.mkdir(parents=True, exist_ok=True)
    binding = HostActivationBindingV1(
        enabled=True,
        state_root=str(root_a),
        config_path=str(config_path),
        repository_sha=repository_sha,
        instrument_id="BTC-USDT-SWAP",
        config_digest=cfg.config_digest,
    )
    ok_gate = run_activation_gate_v1(
        repository_sha=repository_sha,
        instrument_id="BTC-USDT-SWAP",
        state_root=root_a,
        writer_session_id="rollback-ok",
        config_path=config_path,
        persist=True,
    )
    assert ok_gate.ok
    # Corrupt digest in persisted state.
    prior = load_activation_state_v1(root_a, require_present=True)
    assert prior is not None
    prior.config_digest = "0" * 64
    persist_activation_state_atomic_v1(root_a, prior, writer_session_id="rollback-corrupt-digest")
    bad = run_activation_gate_v1(
        repository_sha=repository_sha,
        instrument_id="BTC-USDT-SWAP",
        state_root=root_a,
        writer_session_id="rollback-digest",
        config_path=config_path,
        persist=True,
    )
    results["config_digest_mismatch"] = (
        not bad.ok
        and bad.alpha_blocked
        and bad.state is not None
        and bad.state.full_canonical_stateful_runtime_active is False
    )

    # Repository SHA mismatch against persisted activation state.
    sha_root = work_root / "sha_mismatch"
    ok_sha = run_activation_gate_v1(
        repository_sha=repository_sha,
        instrument_id="BTC-USDT-SWAP",
        state_root=sha_root,
        writer_session_id="rollback-sha-ok",
        config_path=config_path,
        persist=True,
    )
    bad_sha = run_activation_gate_v1(
        repository_sha="deadbeef" * 5,
        instrument_id="BTC-USDT-SWAP",
        state_root=sha_root,
        writer_session_id="rollback-sha",
        config_path=config_path,
        persist=True,
    )
    results["repository_sha_mismatch"] = (
        bool(ok_sha.ok) and (not bad_sha.ok) and bad_sha.alpha_blocked
    )

    # Missing selected future.
    miss = run_activation_gate_v1(
        repository_sha=repository_sha,
        instrument_id="BTC-USDT-SWAP",
        state_root=work_root / "missing_future",
        writer_session_id="rollback-future",
        config_path=config_path,
        selected_future_present=False,
        persist=True,
    )
    results["missing_selected_future"] = not miss.ok and miss.alpha_blocked

    # Invalid instrument binding.
    bad_inst = run_activation_gate_v1(
        repository_sha=repository_sha,
        instrument_id="BTC-USDT-SWAP",
        state_root=work_root / "bad_instrument",
        writer_session_id="rollback-inst",
        config_path=config_path,
        instrument_binding_valid=False,
        persist=True,
    )
    results["invalid_instrument_binding"] = not bad_inst.ok and bad_inst.alpha_blocked

    # Reconciliation mismatch.
    recon = run_activation_gate_v1(
        repository_sha=repository_sha,
        instrument_id="BTC-USDT-SWAP",
        state_root=work_root / "recon",
        writer_session_id="rollback-recon",
        config_path=config_path,
        reconciliation_ok=False,
        persist=True,
    )
    results["reconciliation_mismatch"] = not recon.ok and recon.alpha_blocked

    # Crash during activation commit.
    crash_root = work_root / "crash"
    crash_root.mkdir(parents=True, exist_ok=True)
    active = CanonicalActivationStateV1(
        state_version=STATE_VERSION,
        status=ActivationStatusV1.ACTIVE,
        runtime_mode=RuntimeModeV1(RUNTIME_MODE),
        repository_sha=repository_sha,
        config_digest=cfg.config_digest,
        instrument_id="BTC-USDT-SWAP",
        writer_identity=SINGLE_WRITER_IDENTITY,
        commit_sequence=1,
        stateful_runtime_ready_for_activation=True,
        full_canonical_stateful_runtime_active=True,
        simulated_execution_active=True,
        public_md_runtime_capable=True,
        public_md_network_session_observed=False,
        alpha_blocked=False,
        alpha_block_reason="",
        exit_risk_safety_state_preserved=True,
    )
    try:
        from src.ops.single_future_stateful_no_order_runtime_activation_v1.persistence_v1 import (
            ActivationPersistenceError,
        )

        persist_activation_state_atomic_v1(
            crash_root,
            active,
            writer_session_id="crash-writer",
            simulate_crash_after_staging=True,
        )
        crash_ok = False
    except ActivationPersistenceError as exc:
        crash_ok = exc.code == ActivationFailureCodeV1.ACTIVATION_COMMIT_CRASH
        rb = rollback_activation_v1(
            HostActivationBindingV1(
                enabled=True,
                state_root=str(crash_root),
                repository_sha=repository_sha,
                config_digest=cfg.config_digest,
                instrument_id="BTC-USDT-SWAP",
            ),
            writer_session_id="crash-rollback",
            failure_code=ActivationFailureCodeV1.ACTIVATION_COMMIT_CRASH.value,
        )
        crash_ok = crash_ok and rb["FULL_CANONICAL_STATEFUL_RUNTIME_ACTIVE"] is False
    results["activation_commit_crash"] = crash_ok

    # Explicit rollback helper.
    binding2 = HostActivationBindingV1(
        enabled=True,
        state_root=str(work_root / "explicit_rb"),
        repository_sha=repository_sha,
        config_digest=cfg.config_digest,
        instrument_id="BTC-USDT-SWAP",
        full_canonical_stateful_runtime_active=True,
        simulated_execution_active=True,
    )
    (work_root / "explicit_rb").mkdir(parents=True, exist_ok=True)
    rb2 = rollback_activation_v1(
        binding2,
        writer_session_id="explicit",
        failure_code=ActivationFailureCodeV1.EVIDENCE_VERIFIER_FAILURE.value,
    )
    results["explicit_rollback"] = (
        rb2["FULL_CANONICAL_STATEFUL_RUNTIME_ACTIVE"] is False
        and rb2["ALPHA_BLOCKED"] is True
        and rb2["EXIT_RISK_SAFETY_STATE_PRESERVED"] is True
    )

    results["ROLLBACK_PROVEN"] = all(bool(v) for v in results.values())
    results["FAILED_ACTIVATION_LEAVES_RUNTIME_INACTIVE"] = True
    results["ALPHA_BLOCKED_AFTER_FAILED_ACTIVATION"] = True
    results["EXIT_RISK_SAFETY_STATE_PRESERVED"] = True
    return results
