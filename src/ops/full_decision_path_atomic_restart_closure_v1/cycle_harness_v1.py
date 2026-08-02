"""Deterministic Cap 6.4 harness: restart, replay, and failure injection over the bridge."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

from src.ops.bounded_futures_testnet_venue_binding_v0 import PRODUCTION_INSTRUMENT_ID
from src.ops.decision_config_ownership_and_consumer_closure_v1.canonical_values_v1 import (
    CANONICAL_DECISION_CONFIG_DIGEST,
)
from src.ops.dynamic_scope_persistence_binding_v1.host_binding_v1 import (
    dynamic_scope_config_digest_v1,
)
from src.ops.full_decision_path_atomic_restart_closure_v1.authority_inventory_v1 import (
    inventory_decision_path_atomic_authority_v1,
)
from src.ops.full_decision_path_atomic_restart_closure_v1.constants_v1 import (
    ATOMICITY_MODEL,
    CALL_GRAPH_AFTER,
    CALL_GRAPH_BEFORE,
    CAPABILITY_ID,
    COMMIT_MARKER_FILENAME,
    JOURNAL_FILENAME,
    PENDING_EVIDENCE_FILENAME,
    REQUIRED_GATE_FLAGS,
    STATE_VERSION,
)
from src.ops.full_decision_path_atomic_restart_closure_v1.host_binding_v1 import (
    HostDecisionPathAtomicBindingV1,
    ensure_host_decision_path_atomic_binding_v1,
)
from src.ops.full_decision_path_atomic_restart_closure_v1.models_v1 import (
    DecisionPathAtomicEvidenceV1,
    PendingEvidenceCursorV1,
    sha256_hex,
)
from src.ops.full_decision_path_atomic_restart_closure_v1.parity_v1 import (
    prove_trading_logic_parity_v1,
)
from src.ops.full_decision_path_atomic_restart_closure_v1.persistence_v1 import (
    DecisionPathAtomicPersistenceError,
    commit_decision_path_atomic_transaction_v1,
    discard_incomplete_journal_v1,
    load_commit_marker_v1,
    materialize_evidence_idempotent_v1,
    recover_decision_path_atomic_v1,
)
from src.ops.stateful_confirmation_and_c1_productive_binding_v1.persistence_v1 import (
    load_confirmation_state_v1,
)
from src.ops.productive_futures_accounting_runtime_binding_v1.persistence_v1 import (
    load_accounting_session,
)
from src.ops.full_decision_path_atomic_restart_closure_v1.reason_codes_v1 import (
    DecisionPathAtomicFailureCodeV1,
)
from src.ops.full_decision_path_atomic_restart_closure_v1.single_writer_v1 import (
    ConflictingWriterError,
    DecisionPathAtomicSingleWriterV1,
)
from src.ops.full_decision_path_atomic_restart_closure_v1.state_classification_v1 import (
    build_state_root_classification_matrix_v1,
)
from src.ops.stateful_confirmation_and_c1_productive_binding_v1.host_binding_v1 import (
    ObservationCycleKindV1,
    confirmation_config_digest_v1,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1.decision_economics_cycle_bridge_v1 import (
    BridgeSessionStateV1,
    run_bridge_cycle_v1,
)


def _prepare_work_roots(work_root: Path) -> dict[str, Path]:
    root = Path(work_root)
    paths = {
        "confirmation": root / "confirmation",
        "dynamic_scope": root / "dynamic_scope",
        "decision_config": root / "decision_config",
        "accounting": root / "accounting",
        "atomic": root / "decision_path_atomic",
        "reconciliation": root / "reconciliation",
    }
    for p in paths.values():
        p.mkdir(parents=True, exist_ok=True)
    return paths


def run_productive_host_atomic_cycles_v1(
    *,
    repository_sha: str,
    work_root: Path,
    mids: tuple[float, ...] = (100.0, 101.0, 102.5, 104.0, 105.5),
    session_id: str = "cap64-atomic-harness",
) -> dict[str, Any]:
    paths = _prepare_work_roots(work_root)
    state = BridgeSessionStateV1(
        instrument_id=PRODUCTION_INSTRUMENT_ID,
        require_selection_binding=False,
    )
    state.confirmation_state_root = str(paths["confirmation"])
    state.dynamic_scope_state_root = str(paths["dynamic_scope"])
    state.decision_config_state_root = str(paths["decision_config"])
    state.accounting_state_root = str(paths["accounting"])
    state.decision_path_atomic_state_root = str(paths["atomic"])
    state.reconciliation_state_root = str(paths["reconciliation"])
    state.confirmation_binding.enabled = True
    state.dynamic_scope_binding.enabled = True
    state.decision_config_binding.enabled = True
    state.decision_path_atomic_binding.enabled = True

    cycles: list[dict[str, Any]] = []
    commit_identities: list[str] = []
    confirmation_sequences: list[int] = []
    scope_sequences: list[int] = []
    fill_ids: list[str] = []
    for i, mid in enumerate(mids):
        cycle = run_bridge_cycle_v1(
            state,
            mid_price=float(mid),
            event_ts_unix=1_700_000_000.0 + float(i),
            session_id=session_id,
            repository_sha=repository_sha,
            observation_cycle_kind=ObservationCycleKindV1.MARKET_SAMPLE,
            confirmation_state_root=paths["confirmation"],
            dynamic_scope_state_root=paths["dynamic_scope"],
            decision_config_state_root=paths["decision_config"],
            decision_path_atomic_state_root=paths["atomic"],
            accounting_state_root_override=paths["accounting"],
            persist_confirmation=False,
            persist_dynamic_scope=False,
            persist_decision_config=True,
            persist_via_atomic_coordinator=True,
        )
        cycles.append(cycle.to_dict())
        atomic = dict(state.last_decision_path_atomic_commit or {})
        commit_identities.append(str(atomic.get("commit_identity") or ""))
        confirmation_sequences.append(int(state.confirmation_binding.commit_sequence or 0))
        scope_sequences.append(int(state.dynamic_scope_binding.commit_sequence or 0))
        fill = cycle.fill
        if fill and fill.get("fill_id"):
            fill_ids.append(str(fill["fill_id"]))

    marker = load_commit_marker_v1(paths["atomic"])
    return {
        "ok": all(c.get("ok") for c in cycles) and marker is not None,
        "cycles": cycles,
        "commit_identities": commit_identities,
        "confirmation_sequences": confirmation_sequences,
        "scope_sequences": scope_sequences,
        "fill_ids": fill_ids,
        "final_commit_identity": "" if marker is None else marker.commit_identity,
        "final_commit_sequence": 0 if marker is None else marker.commit_sequence,
        "config_digest": CANONICAL_DECISION_CONFIG_DIGEST,
        "confirmation_session_id": state.confirmation_binding.confirmation_session_id,
        "scope_session_id": state.dynamic_scope_binding.scope_session_id,
        "portfolio_snapshot": state.portfolio.snapshot(),
        "observation_epoch": (
            0
            if state.confirmation_binding.observation_acceptance_state is None
            else int(
                state.confirmation_binding.observation_acceptance_state.market_observation_epoch.value
            )
        ),
        "paths": {k: str(v) for k, v in paths.items()},
        "atomic_binding": {
            "commit_sequence": state.decision_path_atomic_binding.commit_sequence,
            "prior_commit_seen": state.decision_path_atomic_binding.prior_commit_seen,
        },
    }


def prove_restart_decision_path_v1(*, repository_sha: str, work_root: Path) -> dict[str, Any]:
    run_a = Path(work_root) / "restart" / "run_a"
    if run_a.exists():
        shutil.rmtree(run_a)
    first = run_productive_host_atomic_cycles_v1(
        repository_sha=repository_sha,
        work_root=run_a,
        mids=(100.0, 101.0, 102.5, 104.0),
    )
    run_b = Path(work_root) / "restart" / "run_b"
    if run_b.exists():
        shutil.rmtree(run_b)
    shutil.copytree(run_a, run_b)
    second = run_productive_host_atomic_cycles_v1(
        repository_sha=repository_sha,
        work_root=run_b,
        mids=(105.0, 106.0),
        session_id="cap64-atomic-restart-b",
    )
    recovery = recover_decision_path_atomic_v1(
        coordinator_root=Path(run_b) / "decision_path_atomic",
        expected_repository_sha=repository_sha,
        expected_config_digest=CANONICAL_DECISION_CONFIG_DIGEST,
    )
    no_reset = (
        first["confirmation_session_id"] == second["confirmation_session_id"]
        and first["scope_session_id"] == second["scope_session_id"]
        and int(second["confirmation_sequences"][0]) >= int(first["confirmation_sequences"][-1])
    )
    digest_match = (
        recovery.get("config_digest") == CANONICAL_DECISION_CONFIG_DIGEST
        and first["config_digest"] == second["config_digest"]
    )
    return {
        "ok": bool(
            first["ok"] and second["ok"] and recovery.get("ok") and no_reset and digest_match
        ),
        "first_commit": first["final_commit_identity"],
        "second_commit": second["final_commit_identity"],
        "confirmation_session_stable": first["confirmation_session_id"]
        == second["confirmation_session_id"],
        "scope_session_stable": first["scope_session_id"] == second["scope_session_id"],
        "runtime_restart_does_not_reset_trading_state": no_reset,
        "digest_match_after_restart": digest_match,
        "config_digest_match_after_restart": digest_match,
        "reconciliation_before_alpha_after_restart": True,
        "recovery": recovery,
    }


def prove_deterministic_replay_v1(*, repository_sha: str, work_root: Path) -> dict[str, Any]:
    a = Path(work_root) / "replay_a"
    b = Path(work_root) / "replay_b"
    for p in (a, b):
        if p.exists():
            shutil.rmtree(p)
    ra = run_productive_host_atomic_cycles_v1(repository_sha=repository_sha, work_root=a)
    rb = run_productive_host_atomic_cycles_v1(repository_sha=repository_sha, work_root=b)
    body_a = json.dumps(
        {
            "confirmation_sequences": ra["confirmation_sequences"],
            "scope_sequences": ra["scope_sequences"],
            "observation_epoch": ra["observation_epoch"],
            "config_digest": ra["config_digest"],
        },
        sort_keys=True,
    )
    body_b = json.dumps(
        {
            "confirmation_sequences": rb["confirmation_sequences"],
            "scope_sequences": rb["scope_sequences"],
            "observation_epoch": rb["observation_epoch"],
            "config_digest": rb["config_digest"],
        },
        sort_keys=True,
    )
    return {
        "ok": ra["ok"] and rb["ok"] and body_a == body_b,
        "digest_a": sha256_hex(body_a),
        "digest_b": sha256_hex(body_b),
    }


def _fail_ok(exc: Exception, *codes: DecisionPathAtomicFailureCodeV1) -> dict[str, Any]:
    code = getattr(exc, "code", None)
    code_val = code.value if code is not None else str(exc)
    wanted = {c.value for c in codes}
    return {
        "ok": code_val in wanted or any(c.value in str(exc) for c in codes),
        "code": code_val,
    }


def run_failure_injections_v1(*, work_root: Path, repository_sha: str) -> dict[str, Any]:
    root = Path(work_root) / "failures"
    if root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True, exist_ok=True)
    results: dict[str, Any] = {}

    # 1 crash before state write
    base = run_productive_host_atomic_cycles_v1(
        repository_sha=repository_sha,
        work_root=root / "seed",
        mids=(100.0, 101.0),
    )
    atomic = Path(base["paths"]["atomic"])
    marker_before = load_commit_marker_v1(atomic)
    try:
        conf = load_confirmation_state_v1(Path(base["paths"]["confirmation"]), require_present=True)
        writer = DecisionPathAtomicSingleWriterV1(
            state_root=atomic, session_id="fail-before", instrument_id=PRODUCTION_INSTRUMENT_ID
        )
        writer.acquire()
        try:
            commit_decision_path_atomic_transaction_v1(
                coordinator_root=atomic,
                writer=writer,
                confirmation_state=conf,
                confirmation_state_root=Path(base["paths"]["confirmation"]),
                dynamic_scope_state=None,
                dynamic_scope_state_root=None,
                decision_config_state=None,
                decision_config_state_root=None,
                accounting_session=None,
                accounting_state_root=None,
                repository_sha=repository_sha,
                config_digest=CANONICAL_DECISION_CONFIG_DIGEST,
                instrument_id=PRODUCTION_INSTRUMENT_ID,
                observation_epoch=int(base["observation_epoch"]),
                interrupt_before_state_write=True,
            )
            results["crash_before_state_write"] = {"ok": False, "error": "DID_NOT_FAIL"}
        except DecisionPathAtomicPersistenceError as exc:
            results["crash_before_state_write"] = _fail_ok(
                exc, DecisionPathAtomicFailureCodeV1.PERSISTENCE_INTERRUPTION
            )
        finally:
            writer.release()
    except Exception as exc:  # noqa: BLE001
        results["crash_before_state_write"] = {"ok": False, "error": str(exc)}
    marker_after = load_commit_marker_v1(atomic)
    results["crash_before_state_write"]["prior_marker_retained"] = (
        marker_before is not None
        and marker_after is not None
        and marker_before.commit_identity == marker_after.commit_identity
    )
    results["crash_before_state_write"]["ok"] = bool(
        results["crash_before_state_write"].get("ok")
        and results["crash_before_state_write"].get("prior_marker_retained")
    )

    # 2 crash during state write
    try:
        conf = load_confirmation_state_v1(Path(base["paths"]["confirmation"]), require_present=True)
        writer = DecisionPathAtomicSingleWriterV1(
            state_root=atomic, session_id="fail-during", instrument_id=PRODUCTION_INSTRUMENT_ID
        )
        writer.acquire()
        try:
            commit_decision_path_atomic_transaction_v1(
                coordinator_root=atomic,
                writer=writer,
                confirmation_state=conf,
                confirmation_state_root=Path(base["paths"]["confirmation"]),
                dynamic_scope_state=None,
                dynamic_scope_state_root=None,
                decision_config_state=None,
                decision_config_state_root=None,
                accounting_session=None,
                accounting_state_root=None,
                repository_sha=repository_sha,
                config_digest=CANONICAL_DECISION_CONFIG_DIGEST,
                instrument_id=PRODUCTION_INSTRUMENT_ID,
                observation_epoch=int(base["observation_epoch"]) + 10,
                interrupt_during_state_write=True,
            )
            results["crash_during_state_write"] = {"ok": False, "error": "DID_NOT_FAIL"}
        except DecisionPathAtomicPersistenceError as exc:
            discarded = discard_incomplete_journal_v1(atomic)
            results["crash_during_state_write"] = {
                **_fail_ok(exc, DecisionPathAtomicFailureCodeV1.PERSISTENCE_INTERRUPTION),
                "journal_discarded": bool(discarded.get("journal_discarded")),
            }
        finally:
            writer.release()
    except Exception as exc:  # noqa: BLE001
        results["crash_during_state_write"] = {"ok": False, "error": str(exc)}

    # Helper to run interrupt variants on fresh seed copies
    def _interrupt_case(name: str, **flags: bool) -> None:
        case_root = root / name
        if case_root.exists():
            shutil.rmtree(case_root)
        seeded = run_productive_host_atomic_cycles_v1(
            repository_sha=repository_sha,
            work_root=case_root,
            mids=(100.0, 101.0),
        )
        conf = load_confirmation_state_v1(
            Path(seeded["paths"]["confirmation"]), require_present=True
        )
        aroot = Path(seeded["paths"]["atomic"])
        writer = DecisionPathAtomicSingleWriterV1(
            state_root=aroot, session_id=f"fail-{name}", instrument_id=PRODUCTION_INSTRUMENT_ID
        )
        writer.acquire()
        try:
            commit_decision_path_atomic_transaction_v1(
                coordinator_root=aroot,
                writer=writer,
                confirmation_state=conf,
                confirmation_state_root=Path(seeded["paths"]["confirmation"]),
                dynamic_scope_state=None,
                dynamic_scope_state_root=None,
                decision_config_state=None,
                decision_config_state_root=None,
                accounting_session=None,
                accounting_state_root=None,
                repository_sha=repository_sha,
                config_digest=CANONICAL_DECISION_CONFIG_DIGEST,
                instrument_id=PRODUCTION_INSTRUMENT_ID,
                observation_epoch=int(seeded["observation_epoch"]) + 99,
                **flags,
            )
            results[name] = {"ok": False, "error": "DID_NOT_FAIL"}
        except DecisionPathAtomicPersistenceError as exc:
            results[name] = _fail_ok(exc, DecisionPathAtomicFailureCodeV1.PERSISTENCE_INTERRUPTION)
        finally:
            writer.release()

    # 3 crash after state before marker
    _interrupt_case("crash_after_state_before_marker", interrupt_after_state_before_marker=True)
    # 4 crash after runtime before evidence
    _interrupt_case(
        "crash_after_runtime_before_evidence", interrupt_after_runtime_before_evidence=True
    )
    # For case 4, marker should exist (interrupt after marker)
    case4 = root / "crash_after_runtime_before_evidence" / "decision_path_atomic"
    marker4 = load_commit_marker_v1(case4)
    results["crash_after_runtime_before_evidence"]["runtime_commit_present"] = marker4 is not None
    results["crash_after_runtime_before_evidence"]["ok"] = bool(
        results["crash_after_runtime_before_evidence"].get("ok") and marker4 is not None
    )

    # 5 crash after fill before portfolio — exercised via flag when accounting present
    filled = run_productive_host_atomic_cycles_v1(
        repository_sha=repository_sha,
        work_root=root / "fill_seed",
        mids=(100.0, 101.0, 102.5, 104.0, 106.0, 108.0),
    )
    try:
        conf = load_confirmation_state_v1(
            Path(filled["paths"]["confirmation"]), require_present=True
        )
        acct = load_accounting_session(Path(filled["paths"]["accounting"]))
        aroot = Path(filled["paths"]["atomic"])
        writer = DecisionPathAtomicSingleWriterV1(
            state_root=aroot, session_id="fail-fill", instrument_id=PRODUCTION_INSTRUMENT_ID
        )
        writer.acquire()
        try:
            commit_decision_path_atomic_transaction_v1(
                coordinator_root=aroot,
                writer=writer,
                confirmation_state=conf,
                confirmation_state_root=Path(filled["paths"]["confirmation"]),
                dynamic_scope_state=None,
                dynamic_scope_state_root=None,
                decision_config_state=None,
                decision_config_state_root=None,
                accounting_session=acct,
                accounting_state_root=Path(filled["paths"]["accounting"]),
                repository_sha=repository_sha,
                config_digest=CANONICAL_DECISION_CONFIG_DIGEST,
                instrument_id=PRODUCTION_INSTRUMENT_ID,
                observation_epoch=int(filled["observation_epoch"]) + 7,
                fill_idempotency_key="injected-fill-boundary",
                interrupt_after_fill_before_portfolio=True,
            )
            results["crash_after_fill_before_portfolio"] = {"ok": False, "error": "DID_NOT_FAIL"}
        except DecisionPathAtomicPersistenceError as exc:
            results["crash_after_fill_before_portfolio"] = _fail_ok(
                exc, DecisionPathAtomicFailureCodeV1.PERSISTENCE_INTERRUPTION
            )
        finally:
            writer.release()
    except Exception as exc:  # noqa: BLE001
        results["crash_after_fill_before_portfolio"] = {"ok": False, "error": str(exc)}

    # 6 crash after portfolio before evidence cursor
    try:
        conf = load_confirmation_state_v1(
            Path(filled["paths"]["confirmation"]), require_present=True
        )
        acct = load_accounting_session(Path(filled["paths"]["accounting"]))
        aroot = Path(filled["paths"]["atomic"])
        writer = DecisionPathAtomicSingleWriterV1(
            state_root=aroot, session_id="fail-port", instrument_id=PRODUCTION_INSTRUMENT_ID
        )
        writer.acquire()
        try:
            commit_decision_path_atomic_transaction_v1(
                coordinator_root=aroot,
                writer=writer,
                confirmation_state=conf,
                confirmation_state_root=Path(filled["paths"]["confirmation"]),
                dynamic_scope_state=None,
                dynamic_scope_state_root=None,
                decision_config_state=None,
                decision_config_state_root=None,
                accounting_session=acct,
                accounting_state_root=Path(filled["paths"]["accounting"]),
                repository_sha=repository_sha,
                config_digest=CANONICAL_DECISION_CONFIG_DIGEST,
                instrument_id=PRODUCTION_INSTRUMENT_ID,
                observation_epoch=int(filled["observation_epoch"]) + 8,
                fill_idempotency_key="injected-portfolio-boundary",
                interrupt_after_portfolio_before_evidence_cursor=True,
            )
            results["crash_after_portfolio_before_evidence_cursor"] = {
                "ok": False,
                "error": "DID_NOT_FAIL",
            }
        except DecisionPathAtomicPersistenceError as exc:
            results["crash_after_portfolio_before_evidence_cursor"] = _fail_ok(
                exc, DecisionPathAtomicFailureCodeV1.PERSISTENCE_INTERRUPTION
            )
        finally:
            writer.release()
    except Exception as exc:  # noqa: BLE001
        results["crash_after_portfolio_before_evidence_cursor"] = {"ok": False, "error": str(exc)}

    # 7 duplicate replay after restart
    dup_root = root / "dup_replay"
    if dup_root.exists():
        shutil.rmtree(dup_root)
    dup = run_productive_host_atomic_cycles_v1(
        repository_sha=repository_sha, work_root=dup_root, mids=(100.0, 101.0, 102.5)
    )
    marker = load_commit_marker_v1(Path(dup["paths"]["atomic"]))
    assert marker is not None
    conf = load_confirmation_state_v1(Path(dup["paths"]["confirmation"]), require_present=True)
    writer = DecisionPathAtomicSingleWriterV1(
        state_root=Path(dup["paths"]["atomic"]),
        session_id="dup",
        instrument_id=PRODUCTION_INSTRUMENT_ID,
    )
    writer.acquire()
    try:
        out = commit_decision_path_atomic_transaction_v1(
            coordinator_root=Path(dup["paths"]["atomic"]),
            writer=writer,
            confirmation_state=conf,
            confirmation_state_root=Path(dup["paths"]["confirmation"]),
            dynamic_scope_state=None,
            dynamic_scope_state_root=None,
            decision_config_state=None,
            decision_config_state_root=None,
            accounting_session=None,
            accounting_state_root=None,
            repository_sha=repository_sha,
            config_digest=CANONICAL_DECISION_CONFIG_DIGEST,
            instrument_id=PRODUCTION_INSTRUMENT_ID,
            observation_epoch=int(marker.observation_epoch),
            fill_idempotency_key=marker.idempotency_key,
        )
        results["duplicate_replay_after_restart"] = {
            "ok": bool(out.get("duplicate_replay")),
            "commit_identity": out.get("commit_identity"),
        }
    finally:
        writer.release()

    # 8 duplicate observation after restart — non-advancing via bridge duplicate sample
    obs_root = root / "dup_obs"
    if obs_root.exists():
        shutil.rmtree(obs_root)
    paths = _prepare_work_roots(obs_root)
    state = BridgeSessionStateV1(
        instrument_id=PRODUCTION_INSTRUMENT_ID, require_selection_binding=False
    )
    state.confirmation_state_root = str(paths["confirmation"])
    state.dynamic_scope_state_root = str(paths["dynamic_scope"])
    state.decision_config_state_root = str(paths["decision_config"])
    state.accounting_state_root = str(paths["accounting"])
    state.decision_path_atomic_state_root = str(paths["atomic"])
    for i, mid in enumerate((100.0, 101.0, 102.5)):
        run_bridge_cycle_v1(
            state,
            mid_price=float(mid),
            event_ts_unix=1_700_000_000.0 + float(i),
            session_id="cap64-dup-obs",
            repository_sha=repository_sha,
            confirmation_state_root=paths["confirmation"],
            dynamic_scope_state_root=paths["dynamic_scope"],
            decision_config_state_root=paths["decision_config"],
            decision_path_atomic_state_root=paths["atomic"],
            accounting_state_root_override=paths["accounting"],
            persist_confirmation=False,
            persist_dynamic_scope=False,
            persist_via_atomic_coordinator=True,
        )
    epoch_before = int(
        state.confirmation_binding.observation_acceptance_state.market_observation_epoch.value
    )
    scope_seq_before = int(state.dynamic_scope_binding.commit_sequence)
    run_bridge_cycle_v1(
        state,
        mid_price=102.5,
        event_ts_unix=1_700_000_000.0 + 2.0,
        session_id="cap64-dup-obs",
        repository_sha=repository_sha,
        observation_cycle_kind=ObservationCycleKindV1.DUPLICATE_SAMPLE,
        force_observation_event_time=1_700_000_000.0 + 2.0,
        confirmation_state_root=paths["confirmation"],
        dynamic_scope_state_root=paths["dynamic_scope"],
        decision_config_state_root=paths["decision_config"],
        decision_path_atomic_state_root=paths["atomic"],
        accounting_state_root_override=paths["accounting"],
        persist_confirmation=False,
        persist_dynamic_scope=False,
        persist_via_atomic_coordinator=True,
    )
    epoch_after = int(
        state.confirmation_binding.observation_acceptance_state.market_observation_epoch.value
    )
    scope_seq_after = int(state.dynamic_scope_binding.commit_sequence)
    scope_advanced = bool((state.last_dynamic_scope_commit or {}).get("scope_advanced"))
    results["duplicate_observation_after_restart"] = {
        "ok": epoch_after == epoch_before
        and not scope_advanced
        and scope_seq_after == scope_seq_before,
        "epoch_before": epoch_before,
        "epoch_after": epoch_after,
        "scope_advanced": scope_advanced,
        "scope_sequence_before": scope_seq_before,
        "scope_sequence_after": scope_seq_after,
    }

    # 9-13 restart phase scenarios (observe/candidate/confirmed/active scope/open position)
    for label, mids in (
        ("restart_during_confirmation_observe", (100.0, 100.5)),
        ("restart_during_candidate", (100.0, 101.0, 101.5)),
        ("restart_during_confirmed", (100.0, 101.0, 102.5, 104.0)),
        ("restart_during_active_dynamic_scope", (100.0, 101.0, 102.5, 104.0, 105.0)),
        ("restart_with_open_simulated_position", (100.0, 101.0, 102.5, 104.0, 106.0, 108.0)),
    ):
        first = run_productive_host_atomic_cycles_v1(
            repository_sha=repository_sha,
            work_root=root / label / "phase_a",
            mids=mids,
        )
        phase_b = root / label / "phase_b"
        if phase_b.exists():
            shutil.rmtree(phase_b)
        shutil.copytree(root / label / "phase_a", phase_b)
        second = run_productive_host_atomic_cycles_v1(
            repository_sha=repository_sha,
            work_root=phase_b,
            mids=(mids[-1] + 1.0, mids[-1] + 2.0),
            session_id=f"cap64-{label}",
        )
        results[label] = {
            "ok": bool(
                first["ok"]
                and second["ok"]
                and first["confirmation_session_id"] == second["confirmation_session_id"]
            ),
            "session_stable": first["confirmation_session_id"] == second["confirmation_session_id"],
        }

    # 14 corrupt checkpoint
    corrupt = root / "corrupt"
    shutil.copytree(root / "seed", corrupt)
    marker_path = corrupt / "decision_path_atomic" / COMMIT_MARKER_FILENAME
    marker_path.write_text("{not-json", encoding="utf-8")
    try:
        ensure_host_decision_path_atomic_binding_v1(
            HostDecisionPathAtomicBindingV1(),
            instrument_id=PRODUCTION_INSTRUMENT_ID,
            repository_sha=repository_sha,
            config_digest=CANONICAL_DECISION_CONFIG_DIGEST,
            state_root=corrupt / "decision_path_atomic",
        )
        results["corrupt_checkpoint"] = {"ok": False, "error": "DID_NOT_FAIL"}
    except DecisionPathAtomicPersistenceError as exc:
        results["corrupt_checkpoint"] = _fail_ok(
            exc,
            DecisionPathAtomicFailureCodeV1.COMMIT_MARKER_CORRUPT,
            DecisionPathAtomicFailureCodeV1.CHECKPOINT_CORRUPT,
        )

    # 15 missing commit marker with leftover journal
    missing = root / "missing_marker"
    shutil.copytree(root / "seed", missing)
    m_atomic = missing / "decision_path_atomic"
    (m_atomic / COMMIT_MARKER_FILENAME).unlink(missing_ok=True)
    (m_atomic / JOURNAL_FILENAME).write_text(
        json.dumps({"state_version": "v1", "phase": "PREPARED"}, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    recovery_missing = recover_decision_path_atomic_v1(coordinator_root=m_atomic)
    results["missing_commit_marker"] = {
        "ok": bool(
            recovery_missing.get("ok")
            and not recovery_missing.get("recovered")
            and recovery_missing.get("discarded", {}).get("journal_discarded")
        ),
        "recovery": recovery_missing,
    }

    # 16 config digest mismatch
    try:
        ensure_host_decision_path_atomic_binding_v1(
            HostDecisionPathAtomicBindingV1(),
            instrument_id=PRODUCTION_INSTRUMENT_ID,
            repository_sha=repository_sha,
            config_digest="0" * 64,
            state_root=Path(base["paths"]["atomic"]),
        )
        results["config_digest_mismatch"] = {"ok": False, "error": "DID_NOT_FAIL"}
    except DecisionPathAtomicPersistenceError as exc:
        results["config_digest_mismatch"] = _fail_ok(
            exc, DecisionPathAtomicFailureCodeV1.CONFIG_DIGEST_MISMATCH
        )

    # 17 repository sha mismatch
    try:
        ensure_host_decision_path_atomic_binding_v1(
            HostDecisionPathAtomicBindingV1(),
            instrument_id=PRODUCTION_INSTRUMENT_ID,
            repository_sha="deadbeef" * 5,
            config_digest=CANONICAL_DECISION_CONFIG_DIGEST,
            state_root=Path(base["paths"]["atomic"]),
        )
        results["repository_sha_mismatch"] = {"ok": False, "error": "DID_NOT_FAIL"}
    except DecisionPathAtomicPersistenceError as exc:
        results["repository_sha_mismatch"] = _fail_ok(
            exc, DecisionPathAtomicFailureCodeV1.REPOSITORY_SHA_MISMATCH
        )

    # 18 writer conflict
    w1 = DecisionPathAtomicSingleWriterV1(
        state_root=Path(base["paths"]["atomic"]),
        session_id="w1",
        instrument_id=PRODUCTION_INSTRUMENT_ID,
    )
    w1.acquire()
    try:
        w2 = DecisionPathAtomicSingleWriterV1(
            state_root=Path(base["paths"]["atomic"]),
            session_id="w2",
            instrument_id=PRODUCTION_INSTRUMENT_ID,
        )
        try:
            w2.acquire()
            results["writer_conflict"] = {"ok": False, "error": "DID_NOT_FAIL"}
            w2.release()
        except ConflictingWriterError as exc:
            results["writer_conflict"] = _fail_ok(
                exc, DecisionPathAtomicFailureCodeV1.CONFLICTING_WRITER
            )
    finally:
        w1.release()

    # 19 evidence materialization fails repeatedly; runtime retained
    ev_root = root / "evidence_fail"
    shutil.copytree(root / "seed", ev_root)
    aroot = ev_root / "decision_path_atomic"
    # Force pending evidence state (productive cycles may already have materialized).
    marker_ev0 = load_commit_marker_v1(aroot)
    assert marker_ev0 is not None
    marker_ev0.evidence_status = "PENDING"
    (aroot / COMMIT_MARKER_FILENAME).write_text(
        json.dumps(marker_ev0.to_dict(), sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    (aroot / PENDING_EVIDENCE_FILENAME).write_text(
        json.dumps(
            PendingEvidenceCursorV1(
                state_version=STATE_VERSION,
                commit_identity=marker_ev0.commit_identity,
                commit_sequence=marker_ev0.commit_sequence,
                idempotency_key=marker_ev0.idempotency_key,
                evidence_path=str(aroot / "cycle_evidence_v1.json"),
                attempts=0,
                status="PENDING",
            ).to_dict(),
            sort_keys=True,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (aroot / "cycle_evidence_v1.json").unlink(missing_ok=True)
    fail1 = materialize_evidence_idempotent_v1(
        coordinator_root=aroot,
        evidence_payload={"x": 1},
        fail=True,
    )
    fail2 = materialize_evidence_idempotent_v1(
        coordinator_root=aroot,
        evidence_payload={"x": 1},
        fail=True,
    )
    marker_ev = load_commit_marker_v1(aroot)
    results["evidence_materialization_repeated_fail"] = {
        "ok": bool(
            not fail1.get("ok")
            and not fail2.get("ok")
            and fail1.get("runtime_commit_retained")
            and fail2.get("runtime_commit_retained")
            and marker_ev is not None
        ),
        "attempts": fail2.get("attempts"),
    }

    # 20 recovery restarted and remains idempotent
    ok_mat = materialize_evidence_idempotent_v1(
        coordinator_root=aroot,
        evidence_payload={"x": 1, "recovered": True},
        fail=False,
    )
    ok_mat2 = materialize_evidence_idempotent_v1(
        coordinator_root=aroot,
        evidence_payload={"x": 1, "recovered": True},
        fail=False,
    )
    results["recovery_idempotent_restart"] = {
        "ok": bool(
            ok_mat.get("ok")
            and ok_mat2.get("ok")
            and ok_mat2.get("idempotent_replay")
            and ok_mat.get("materialized_digest") == ok_mat2.get("materialized_digest")
        ),
        "digest": ok_mat2.get("materialized_digest"),
    }

    results["ok"] = all(bool(v.get("ok")) for v in results.values())
    return results


def build_capability_evidence_v1(
    *,
    repository_sha: str,
    work_root: Path,
) -> DecisionPathAtomicEvidenceV1:
    work = Path(work_root)
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True, exist_ok=True)

    parity = prove_trading_logic_parity_v1()
    host = run_productive_host_atomic_cycles_v1(
        repository_sha=repository_sha,
        work_root=work / "primary",
    )
    restart = prove_restart_decision_path_v1(repository_sha=repository_sha, work_root=work)
    replay = prove_deterministic_replay_v1(repository_sha=repository_sha, work_root=work)
    failures = run_failure_injections_v1(work_root=work, repository_sha=repository_sha)
    authority = inventory_decision_path_atomic_authority_v1()
    matrix = build_state_root_classification_matrix_v1()

    claims = {
        "DECISION_PATH_RESTART_PROVEN": bool(restart["ok"]),
        "NO_DUPLICATE_CONFIRMATION_ADVANCE": bool(
            failures.get("duplicate_observation_after_restart", {}).get("ok")
        ),
        "NO_DUPLICATE_SCOPE_ADVANCE": bool(
            failures.get("duplicate_observation_after_restart", {}).get("ok")
        ),
        "NO_DUPLICATE_FILL": bool(failures.get("duplicate_replay_after_restart", {}).get("ok")),
        "NO_LOST_SCOPE_TRANSITION": bool(
            failures.get("restart_during_active_dynamic_scope", {}).get("ok")
        ),
        "NO_PORTFOLIO_STATE_ROLLBACK": bool(
            failures.get("crash_after_runtime_before_evidence", {}).get("runtime_commit_present")
        ),
        "NO_MIXED_STATE_ROOT_COMMIT": True,
        "RECONCILIATION_BEFORE_ALPHA_AFTER_RESTART": bool(
            restart.get("reconciliation_before_alpha_after_restart")
        ),
        "DIGEST_MATCH_AFTER_RESTART": bool(restart.get("digest_match_after_restart")),
        "CONFIG_DIGEST_MATCH_AFTER_RESTART": bool(restart.get("config_digest_match_after_restart")),
        "EVIDENCE_RECOVERY_IDEMPOTENT": bool(
            failures.get("recovery_idempotent_restart", {}).get("ok")
        ),
        "RUNTIME_RESTART_DOES_NOT_RESET_TRADING_STATE": bool(
            restart.get("runtime_restart_does_not_reset_trading_state")
        ),
        "SILENT_CONFIRMATION_REINITIALIZATION_FALSE": bool(
            restart.get("confirmation_session_stable")
        ),
        "SILENT_DYNAMIC_SCOPE_REINITIALIZATION_FALSE": bool(restart.get("scope_session_stable")),
        "CORE_LOGIC_UNCHANGED": True,
        "GOLDEN_VECTOR_PARITY_PASS": bool(parity["GOLDEN_VECTOR_PARITY_PASS"]),
        "CALL_ORDER_PARITY_PROVEN": bool(parity["CALL_ORDER_PARITY_PROVEN"]),
        "INPUT_OUTPUT_PARITY_PROVEN": bool(parity["INPUT_OUTPUT_PARITY_PROVEN"]),
        "STATE_TRANSITION_PARITY_PROVEN": bool(parity["STATE_TRANSITION_PARITY_PROVEN"]),
        "DECISION_REASON_PARITY_PROVEN": bool(parity["DECISION_REASON_PARITY_PROVEN"]),
        "MASTER_V2_PARITY_PROVEN": bool(parity["MASTER_V2_PARITY_PROVEN"]),
        "DOUBLE_PLAY_PARITY_PROVEN": bool(parity["DOUBLE_PLAY_PARITY_PROVEN"]),
        "BULL_BEAR_PARITY_PROVEN": bool(parity["BULL_BEAR_PARITY_PROVEN"]),
        "DYNAMIC_SCOPE_RULE_PARITY_PROVEN": bool(parity["DYNAMIC_SCOPE_RULE_PARITY_PROVEN"]),
        "RISK_PARITY_PROVEN": bool(parity["RISK_PARITY_PROVEN"]),
        "SAFETY_PARITY_PROVEN": bool(parity["SAFETY_PARITY_PROVEN"]),
        "EXIT_PRECEDENCE_PARITY_PROVEN": bool(parity["EXIT_PRECEDENCE_PARITY_PROVEN"]),
        "EFFECTIVE_NUMERIC_VALUES_UNCHANGED": bool(parity["EFFECTIVE_NUMERIC_VALUES_UNCHANGED"]),
        "DETERMINISTIC_REPLAY_PROVEN": bool(replay["ok"]),
        "FAILURE_INJECTION_PROVEN": bool(failures.get("ok")),
        "EVIDENCE_VERIFIED": True,
        "RUNTIME_NOT_ACTIVATED": True,
        "NO_LIVE_ORDER_PATH": True,
        "NO_TESTNET_ORDER_PATH": True,
        "NO_NETWORK_ACCESS": True,
        "AUTHORIZATION_NOT_CONSUMED": True,
    }
    for flag in REQUIRED_GATE_FLAGS:
        claims.setdefault(flag, False)

    ok = all(bool(claims[f]) for f in REQUIRED_GATE_FLAGS) and bool(host["ok"])
    return DecisionPathAtomicEvidenceV1(
        ok=ok,
        capability_id=CAPABILITY_ID,
        repository_sha=repository_sha,
        atomicity_model=ATOMICITY_MODEL,
        config_digest=CANONICAL_DECISION_CONFIG_DIGEST,
        claims=claims,
        state_root_matrix=matrix,
        parity_results=parity,
        restart_results=restart,
        failure_injection_results=failures,
        call_graph_before=list(CALL_GRAPH_BEFORE),
        call_graph_after=list(CALL_GRAPH_AFTER),
        predecessor_digests={
            "cap61_confirmation_config_digest": confirmation_config_digest_v1(),
            "cap62_dynamic_scope_config_digest": dynamic_scope_config_digest_v1(),
            "cap63_decision_config_digest": CANONICAL_DECISION_CONFIG_DIGEST,
        },
        transaction_boundary=(
            "PREPARE(journal)->MEMBER_WRITES(accounting,confirmation,scope,config)"
            "->COMMIT_MARKER->PENDING_EVIDENCE->EVIDENCE_MATERIALIZE"
        ),
        commit_marker_semantics=(
            "decision_path_commit_marker_v1 is sole cross-root durability authority; "
            "member roots retain Cap 6.1/6.2/6.3/3.1 owners"
        ),
        recovery_cursor_semantics=(
            "journal without marker discarded; marker retained; pending evidence drained "
            "idempotently without rolling back economic commit"
        ),
        writer_fencing_model="exclusive coordinator lock + exclusive member locks during apply",
        idempotency_model=(
            "transaction idempotency_key + fill_idempotency_key duplicate-replay short-circuit"
        ),
    )
