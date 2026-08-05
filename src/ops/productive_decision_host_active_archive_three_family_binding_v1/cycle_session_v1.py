"""Bounded productive host session: Cap-7.2-enabled run_bridge_cycle_v1 + family export."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence

from src.ops.productive_decision_host_active_archive_three_family_binding_v1.archive_binding_v1 import (
    bind_active_archive_v1,
    resolve_selected_instrument_from_archive_v1,
)
from src.ops.productive_decision_host_active_archive_three_family_binding_v1.authorization_v1 import (
    ProductiveHostAuthorizationError,
    prove_network_and_order_boundary_v1,
    require_owner_go_v1,
    require_repository_sha_match_v1,
    resolve_git_head_sha_v1,
)
from src.ops.productive_decision_host_active_archive_three_family_binding_v1.constants_v1 import (
    CAPABILITY_ID,
    CYCLE_TRACE_FILENAME,
    DEFAULT_MIN_CYCLE_INTERVAL_SECONDS,
    DEFAULT_SMOKE_BACKOFF_SECONDS,
    DEFAULT_SMOKE_MAX_CYCLES,
    HARD_STOP_DOUBLE_PLAY_CANONICAL_INPUT_CONTRACT_MISMATCH,
    LONG_RUNNING_PHASE_9_2_PROVEN,
    OWNER,
    PACKAGE_MARKER,
    PRODUCTIVE_HOST_SYMBOL,
    RUNTIME_MODE,
    SCHEMA_VERSION,
)
from src.ops.productive_decision_host_active_archive_three_family_binding_v1.family_export_adapter_v1 import (
    export_families_after_runtime_commit_v1,
)
from src.ops.productive_decision_host_active_archive_three_family_binding_v1.models_v1 import (
    CycleCommitTraceV1,
    SessionContractV1,
    SmokeSessionResultV1,
)
from src.ops.productive_decision_host_active_archive_three_family_binding_v1.state_root_layout_v1 import (
    ProductiveHostSingleWriterV1,
    materialize_state_root_layout_v1,
    write_session_contract_v1,
)
from src.ops.single_future_stateful_no_order_runtime_activation_v1.constants_v1 import (
    CONFIG_RELATIVE_PATH,
)
from src.ops.single_future_stateful_no_order_runtime_activation_v1.host_binding_v1 import (
    HostActivationBindingV1,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1.decision_economics_cycle_bridge_v1 import (
    BridgeSessionStateV1,
    run_bridge_cycle_v1,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1.constants_v1 import (
    LIVE_AUTHORIZED,
    ORDERS_AUTHORIZED,
    PAPER_EXECUTION_AUTHORIZED,
    TESTNET_AUTHORIZED,
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _append_cycle_trace(evidence_root: Path, trace: CycleCommitTraceV1) -> None:
    path = Path(evidence_root) / CYCLE_TRACE_FILENAME
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(trace.to_dict(), sort_keys=True) + "\n")


def build_session_contract_v1(
    *,
    repository_sha: str,
    expected_repository_sha: str,
    runtime_session_id: str,
    instrument_id: str,
    instrument_source: str,
    archive_root: str,
    config_digest: str,
    owner_go: bool,
    activation_enabled: bool,
    network_session_allowed: bool,
) -> SessionContractV1:
    return SessionContractV1(
        capability_id=CAPABILITY_ID,
        schema_version=SCHEMA_VERSION,
        owner=OWNER,
        package_marker=PACKAGE_MARKER,
        runtime_mode=RUNTIME_MODE,
        repository_sha=repository_sha,
        expected_repository_sha=expected_repository_sha,
        config_digest=config_digest,
        runtime_session_id=runtime_session_id,
        instrument_id=instrument_id,
        instrument_source=instrument_source,
        archive_root=archive_root,
        owner_go=owner_go,
        activation_enabled=activation_enabled,
        public_md_only=True,
        orders_authorized=bool(ORDERS_AUTHORIZED),
        live_authorized=bool(LIVE_AUTHORIZED),
        testnet_authorized=bool(TESTNET_AUTHORIZED),
        paper_exchange_orders=bool(PAPER_EXECUTION_AUTHORIZED),
        exchange_credential_use=False,
        real_capital_movement=False,
        network_session_allowed=bool(network_session_allowed),
        long_running_phase_9_2_proven=LONG_RUNNING_PHASE_9_2_PROVEN,
        hard_stop_double_play_canonical_input_contract_mismatch=(
            HARD_STOP_DOUBLE_PLAY_CANONICAL_INPUT_CONTRACT_MISMATCH
        ),
    )


def run_productive_host_smoke_session_v1(
    *,
    owner_go: bool,
    expected_repository_sha: str,
    archive_root: str | Path | None,
    runtime_root: str | Path,
    runtime_session_id: str,
    mid_prices: Sequence[float],
    expected_instrument: str | None = "SATS-USDT-SWAP",
    enable_activation: bool = True,
    require_selection_binding: bool = False,
    min_cycle_interval_seconds: float = DEFAULT_MIN_CYCLE_INTERVAL_SECONDS,
    max_cycles: int = DEFAULT_SMOKE_MAX_CYCLES,
    network_session_allowed: bool = False,
    start_ts_unix: float = 1_700_000_000.0,
    repo_root: Path | None = None,
) -> SmokeSessionResultV1:
    """Owner-authorized bounded smoke: host cycles + three-family export binding.

    Uses analytical mid ticks (no private APIs). ``network_session_allowed`` is
    recorded on the contract; this smoke does not open Public-MD sockets unless
    a future Owner-GO extends the observation adapter separately.
    """
    root = Path(repo_root) if repo_root is not None else _repo_root()
    errors: list[str] = []
    notes: list[str] = [
        f"PRODUCTIVE_HOST_SYMBOL={PRODUCTIVE_HOST_SYMBOL}",
        "SMOKE_USES_ANALYTICAL_MIDS_NOT_PHASE_9_2",
        "DOUBLE_PLAY_HARD_STOP_WITHOUT_DECISION_TYPED_INPUTS",
        "BLOCKED_CANONICAL_INPUT_AUTHORITY_ABSENT",
        "TRANSITION_DECISION_PASSTHROUGH_WIRED",
        "EXPORT_REPLAY_INTERMEDIATE_FROM_HOST_STATE",
    ]

    try:
        require_owner_go_v1(owner_go=owner_go)
        actual_sha = resolve_git_head_sha_v1(root)
        require_repository_sha_match_v1(
            actual_sha=actual_sha,
            expected_sha=expected_repository_sha,
        )
        boundary = prove_network_and_order_boundary_v1(repo_root=root)
        archive = bind_active_archive_v1(archive_root=archive_root)
        instrument_id, instrument_source = resolve_selected_instrument_from_archive_v1(
            archive_root=archive.archive_root,
            expected_symbol=expected_instrument,
        )
        # Runtime roots must not collapse into archive authority.
        runtime_binding = materialize_state_root_layout_v1(runtime_root=runtime_root)
        if Path(runtime_binding.runtime_root).resolve() == Path(archive.archive_root).resolve():
            raise ProductiveHostAuthorizationError(
                "RUNTIME_ROOT_EQUALS_ARCHIVE_ROOT",
                "decision state roots must be separate from dashboard archive",
            )

        activation_config = root / CONFIG_RELATIVE_PATH
        config_digest = ""
        if activation_config.is_file():
            raw = json.loads(activation_config.read_text(encoding="utf-8"))
            config_digest = str(raw.get("config_digest") or "")

        contract = build_session_contract_v1(
            repository_sha=actual_sha,
            expected_repository_sha=expected_repository_sha,
            runtime_session_id=runtime_session_id,
            instrument_id=instrument_id,
            instrument_source=instrument_source,
            archive_root=archive.archive_root,
            config_digest=config_digest,
            owner_go=True,
            activation_enabled=bool(enable_activation),
            network_session_allowed=bool(network_session_allowed),
        )
        write_session_contract_v1(
            evidence_root=Path(runtime_binding.evidence_session_root),
            payload=contract.to_dict(),
        )

        writer = ProductiveHostSingleWriterV1(
            lock_path=Path(runtime_binding.writer_lock_path),
            session_id=runtime_session_id,
        )
        writer.acquire()
        try:
            state = BridgeSessionStateV1(
                instrument_id=instrument_id,
                require_selection_binding=bool(require_selection_binding),
            )
            state.confirmation_state_root = runtime_binding.confirmation_state_root
            state.dynamic_scope_state_root = runtime_binding.dynamic_scope_state_root
            state.accounting_state_root = runtime_binding.accounting_state_root
            state.activation_state_root = runtime_binding.activation_state_root
            state.activation_config_path = str(activation_config)
            state.activation_binding = HostActivationBindingV1(enabled=bool(enable_activation))
            if not state.activation_binding.enabled:
                raise ProductiveHostAuthorizationError(
                    "ACTIVATION_BINDING_MUST_BE_ENABLED",
                    "HostActivationBindingV1.enabled must be true",
                )

            result = SmokeSessionResultV1(
                ok=False,
                host_started=True,
                archive_bound=True,
                session=contract.to_dict(),
                state_roots=runtime_binding.to_dict(),
                archive_binding=archive.to_dict(),
                order_path_reachable=boundary.order_submit_reachable,
                credential_path_reachable=boundary.credential_path_reachable,
                notes=tuple(notes),
            )

            committed = 0
            last_ds = None
            last_cd = None
            last_dp = None
            mids = list(mid_prices)[: int(max_cycles)]
            if not mids:
                raise ProductiveHostAuthorizationError("SMOKE_MIDS_REQUIRED")

            for i, mid in enumerate(mids):
                if i > 0 and min_cycle_interval_seconds > 0:
                    time.sleep(float(min_cycle_interval_seconds))
                result.cycles_attempted += 1
                event_ts = float(start_ts_unix) + float(i)
                cycle_id = f"{runtime_session_id}:cycle:{i}"
                try:
                    cycle = run_bridge_cycle_v1(
                        state,
                        mid_price=float(mid),
                        event_ts_unix=event_ts,
                        session_id=runtime_session_id,
                        repository_sha=actual_sha,
                        confirmation_state_root=Path(runtime_binding.confirmation_state_root),
                        dynamic_scope_state_root=Path(runtime_binding.dynamic_scope_state_root),
                        accounting_state_root_override=Path(runtime_binding.accounting_state_root),
                        activation_state_root=Path(runtime_binding.activation_state_root),
                        activation_config_path=activation_config,
                        direct_instrument_override=(
                            None if require_selection_binding else instrument_id
                        ),
                        persist_confirmation=True,
                        persist_dynamic_scope=True,
                    )
                except Exception as exc:  # noqa: BLE001
                    errors.append(f"cycle_{i}:{type(exc).__name__}:{exc}")
                    time.sleep(float(DEFAULT_SMOKE_BACKOFF_SECONDS))
                    continue

                if not cycle.ok:
                    errors.append(f"cycle_{i}_not_ok:{','.join(cycle.blockers)}")
                    continue

                evidence_payload = getattr(state, "last_canonical_decision_evidence", None)
                ds_commit = state.last_dynamic_scope_commit or {}
                ds_persisted = bool(ds_commit.get("persisted"))
                decision_id = ""
                if isinstance(evidence_payload, Mapping):
                    decision_id = str(evidence_payload.get("decision_id") or "")

                families = export_families_after_runtime_commit_v1(
                    state_roots=runtime_binding,
                    archive=archive,
                    cycle_id=cycle_id,
                    cycle_index=int(cycle.cycle_index),
                    dynamic_scope_persisted=ds_persisted,
                    evidence_payload=(
                        dict(evidence_payload) if isinstance(evidence_payload, Mapping) else None
                    ),
                    replay_intermediate=getattr(state, "last_replay_intermediate", None),
                )
                last_ds = families.get("dynamic_scope")
                last_cd = families.get("canonical_decision")
                last_dp = families.get("double_play")

                trace = CycleCommitTraceV1(
                    cycle_id=cycle_id,
                    cycle_index=int(cycle.cycle_index),
                    instrument_id=instrument_id,
                    repository_sha=actual_sha,
                    config_digest=config_digest,
                    runtime_session_id=runtime_session_id,
                    mid_price=float(mid),
                    event_ts_unix=event_ts,
                    decision_outcome=str(cycle.decision_outcome),
                    decision_id=decision_id,
                    dynamic_scope_advanced=bool(ds_commit.get("scope_advanced")),
                    dynamic_scope_persisted=ds_persisted,
                    canonical_decision_persisted=bool(evidence_payload),
                    runtime_commit_ok=True,
                    families={k: v.to_dict() for k, v in families.items()},
                    blockers=tuple(str(x) for x in cycle.blockers),
                )
                _append_cycle_trace(Path(runtime_binding.evidence_session_root), trace)
                committed += 1
                result.canonical_cycle_committed = True
                result.public_md_cycle_observed = bool(network_session_allowed)
                # Analytical mids still count as observation cycles for smoke.
                notes.append(f"committed:{cycle_id}:outcome={cycle.decision_outcome}")

            result.cycles_committed = committed
            result.dynamic_scope = last_ds
            result.canonical_decision = last_cd
            result.double_play = last_dp
            result.notes = tuple(notes)
            result.errors = tuple(errors)
            result.ok = committed > 0 and not any(
                e.startswith("OWNER_") or "BOUNDARY" in e for e in errors
            )
            return result
        finally:
            writer.release()
    except ProductiveHostAuthorizationError as exc:
        return SmokeSessionResultV1(
            ok=False,
            errors=(str(exc),),
            notes=tuple(notes),
            hard_stop_double_play=HARD_STOP_DOUBLE_PLAY_CANONICAL_INPUT_CONTRACT_MISMATCH,
        )
    except Exception as exc:  # noqa: BLE001
        return SmokeSessionResultV1(
            ok=False,
            errors=(f"{type(exc).__name__}:{exc}",),
            notes=tuple(notes),
            hard_stop_double_play=HARD_STOP_DOUBLE_PLAY_CANONICAL_INPUT_CONTRACT_MISMATCH,
        )
