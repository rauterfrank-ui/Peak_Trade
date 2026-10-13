"""Offline E2E: governed Cycle Host → capital guard → lifecycle orchestration."""

from __future__ import annotations

import multiprocessing as mp
import subprocess
import tempfile
from pathlib import Path

import pytest

from src.ops.full_core_live_path_composition_root_v1.current_productive_governed_cycle_orchestrator_v1 import (
    DISPOSITION_PRE_EXTERNAL_EFFECT,
    CurrentProductiveGovernedCycleResultV1,
)
from src.ops.full_core_live_path_composition_root_v1.final_order_envelope_v1 import (
    build_final_order_envelope_v1,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_capital_guard_atomic_one_shot_v1 import (
    STATE_HALTED_UNRESOLVED,
    load_full_core_atomic_authorization_state_v1,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_exchange_reconciliation_offline_provider_v1 import (
    OfflineExchangeFixtureV1,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_exchange_reconciliation_v1 import (
    OUTCOME_CONFIRMED_FILLED,
    OUTCOME_CONFIRMED_OPEN,
    OUTCOME_HALTED_UNRESOLVED,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_governed_cycle_host_post_submit_lifecycle_wiring_v1 import (
    CANONICAL_CYCLE_HOST_OWNER,
    CycleLifecycleWiringMode,
    CycleSubmitInjectionKind,
    FullCoreCycleLifecycleWiringError,
    FullCoreCycleLifecycleWiringOwnerGosV1,
    FullCoreCycleLifecycleWiringRequestV1,
    POST_SUBMIT_LIFECYCLE_ORCHESTRATION_OWNER,
    POST_COUNT,
    PRIVATE_GET_COUNT,
    REAL_ORDER_COUNT,
    bind_full_core_cycle_lifecycle_wiring_invocation_v1,
    maybe_record_full_core_governed_cycle_lifecycle_wiring_v1,
    reset_full_core_cycle_lifecycle_wiring_invocation_v1,
    resolve_cycle_lifecycle_wiring_mode_v1,
    run_full_core_governed_cycle_host_post_submit_lifecycle_wiring_v1,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_orchestrated_post_submit_lifecycle_reconciliation_v1 import (
    resolve_origin_main_sha_v1,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_post_submit_exchange_reconciliation_lifecycle_join_v1 import (
    NETWORK_REQUEST_COUNT,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_pre_post_capital_guard_binding_v1 import (
    FullCoreCapitalGuardHandoffContextV1,
    FullCoreCapitalGuardInstrumentMetadataV1,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_productive_http_post_transport_v1 import (
    FullCoreTradeOrderPostResultV1,
)
from src.ops.single_selected_future_runtime_binding_v1.models_v1 import BoundInstrumentV1
from tests.ops.test_full_core_exchange_reconciliation_v1 import CL, _binding, _order_row


def _origin_main() -> str:
    proc = subprocess.run(
        ["git", "rev-parse", "origin/main"],
        capture_output=True,
        text=True,
        check=True,
    )
    return str(proc.stdout or "").strip()


def _owner_gos(**kw: str) -> FullCoreCycleLifecycleWiringOwnerGosV1:
    base = {
        "governed_lifecycle_wiring_go": "GRANTED",
        "offline_implementation_go": "GRANTED",
        "private_get_go": "NOT_GRANTED",
    }
    base.update(kw)
    return FullCoreCycleLifecycleWiringOwnerGosV1(**base)  # type: ignore[arg-type]


def _envelope():
    return build_final_order_envelope_v1(
        instrument_id="0G-USDT-SWAP",
        side="buy",
        order_type="limit",
        quantity="1",
        quantity_unit="CONTRACTS",
        td_mode="cross",
        reduce_only=False,
        client_order_id=CL,
        path_kind="ENTER",
        venue_plan_clordid=CL,
        quantity_source="FIXTURE",
        side_source="FIXTURE",
        instrument_source="FIXTURE",
        admission_ref="adm-wiring",
        provenance_ref="prov-wiring",
        creation_epoch="1700000000",
        price="10",
    )


def _bound() -> BoundInstrumentV1:
    return BoundInstrumentV1(
        instrument_id="0G-USDT-SWAP",
        venue_native_id="0G-USDT-SWAP",
        ranking_snapshot_id="rank-wiring",
        ranking_integrity_digest="rank-digest-wiring",
        universe_snapshot_id="uni-wiring",
        selection_id="sel-wiring",
        selection_integrity_digest="sel-digest-wiring",
        selection_state="SELECTED",
    )


def _handoff(*, sha: str) -> FullCoreCapitalGuardHandoffContextV1:
    return FullCoreCapitalGuardHandoffContextV1(
        bound_instrument=_bound(),
        canonical_decision_id="dec-wiring-1",
        account_identity="acct-wiring-1",
        environment="OFFLINE_STUB",
        origin_main_sha=sha,
        instrument_metadata=FullCoreCapitalGuardInstrumentMetadataV1(
            ct_val="1",
            min_sz="1",
            lot_sz="1",
        ),
    )


def _cycle(*, envelope) -> CurrentProductiveGovernedCycleResultV1:
    return CurrentProductiveGovernedCycleResultV1(
        disposition=DISPOSITION_PRE_EXTERNAL_EFFECT,
        reason_code="PRE_EXTERNAL",
        terminal_class="PRE_EXTERNAL_EFFECT",
        cycle_go_status_after="CONSUMED",
        get_consumed=True,
        eg_consumed=True,
        occupancy_consumed=True,
        t2_consumed=True,
        get_consume_count=1,
        eg_dispatch_count=1,
        occupancy_disposition="CONSUMED",
        t2_consume_count=1,
        runtime_cycle_count=1,
        c1_used="fixture",
        occupancy_used="fixture",
        decision_result="EXECUTABLE_VENUE_PLAN_BOUND",
        decision_execution_eligible="true",
        master_v2_decision="enter_long",
        venue_plan_status="BOUND",
        envelope_created=True,
        envelope_identity=f"envelope_id={envelope.envelope_id}",
        permit_created=False,
        post_count=0,
        external_effect_count=0,
        cursor_floor_before=1.0,
        cursor_floor_after=1.0,
        cursor_persisted=False,
        first_genuine_blocker="POST_OWNER_GO",
        blocker_class="PRE_EXTERNAL_EFFECT",
        next_required_owner_decision="POST",
        lock_released="true",
        ledger_state="COMPLETED",
        transitions=("IDLE", "COMPLETED"),
        final_order_envelope=envelope,
    )


def _ack_post(ord_id: str = "ord-wiring-1") -> FullCoreTradeOrderPostResultV1:
    return FullCoreTradeOrderPostResultV1(
        post_attempted=True,
        venue_live_contact=False,
        method="POST",
        http_status=200,
        payload={
            "code": "0",
            "data": [{"clOrdId": CL, "ordId": ord_id, "sCode": "0"}],
        },
        unknown_outcome=False,
        transport_class="INJECTED_OFFLINE_WIRING",
        endpoint="/api/v5/trade/order",
    )


def _wiring_request(
    *,
    sha: str,
    submit_kind: CycleSubmitInjectionKind,
    fixture: OfflineExchangeFixtureV1 | None = None,
    state_dir: Path | None = None,
    post: FullCoreTradeOrderPostResultV1 | None = None,
    apply_durable: bool = False,
) -> FullCoreCycleLifecycleWiringRequestV1:
    return FullCoreCycleLifecycleWiringRequestV1(
        mode=CycleLifecycleWiringMode.OFFLINE_INJECTED,
        owner_gos=_owner_gos(),
        origin_main_sha=resolve_origin_main_sha_v1(declared=sha),
        submit_kind=submit_kind,
        offline_fixture=fixture or OfflineExchangeFixtureV1(),
        injected_post_result=post,
        atomic_state_dir=state_dir,
        apply_durable_atomic_state=apply_durable,
    )


def _order_row_join(*, state: str, ord_id: str = "ord-wiring-1", acc: str = "0") -> dict:
    row = _order_row(state=state, sz="1", acc=acc)
    row["ordId"] = ord_id
    return row


class TestSafetyPins:
    def test_standing_counts_zero(self) -> None:
        assert POST_COUNT == 0
        assert PRIVATE_GET_COUNT == 0
        assert NETWORK_REQUEST_COUNT == 0
        assert REAL_ORDER_COUNT == 0

    def test_default_wiring_mode_disabled(self) -> None:
        assert resolve_cycle_lifecycle_wiring_mode_v1() is CycleLifecycleWiringMode.DISABLED

    def test_cycle_host_owners_documented(self) -> None:
        assert "governed_cycle_orchestrator" in CANONICAL_CYCLE_HOST_OWNER
        assert "orchestrated_post_submit_lifecycle" in POST_SUBMIT_LIFECYCLE_ORCHESTRATION_OWNER


def test_pre_external_not_attempted_proven_never_submitted(tmp_path: Path) -> None:
    sha = _origin_main()
    env = _envelope()
    res = run_full_core_governed_cycle_host_post_submit_lifecycle_wiring_v1(
        cycle=_cycle(envelope=env),
        handoff=_handoff(sha=sha),
        request=_wiring_request(
            sha=sha,
            submit_kind=CycleSubmitInjectionKind.NOT_ATTEMPTED,
            state_dir=tmp_path,
        ),
    )
    assert res.lifecycle is not None
    assert res.lifecycle.local_submit_outcome.value == "NOT_SUBMITTED"
    assert res.ghv_forward_join == "PASS"
    assert res.ghv_reverse_join == "PASS"


def test_ack_open_offline_chain(tmp_path: Path) -> None:
    sha = _origin_main()
    env = _envelope()
    fixture = OfflineExchangeFixtureV1(pending_orders={"data": [_order_row_join(state="live")]})
    res = run_full_core_governed_cycle_host_post_submit_lifecycle_wiring_v1(
        cycle=_cycle(envelope=env),
        handoff=_handoff(sha=sha),
        request=_wiring_request(
            sha=sha,
            submit_kind=CycleSubmitInjectionKind.ACKNOWLEDGED,
            fixture=fixture,
            post=_ack_post(),
            state_dir=tmp_path,
        ),
    )
    assert res.lifecycle is not None
    assert res.lifecycle.reconciliation.decision.outcome == OUTCOME_CONFIRMED_OPEN


def test_unknown_timeout_halts_without_terminal_promotion(tmp_path: Path) -> None:
    sha = _origin_main()
    env = _envelope()
    binding = _binding()
    res = run_full_core_governed_cycle_host_post_submit_lifecycle_wiring_v1(
        cycle=_cycle(envelope=env),
        handoff=_handoff(sha=sha),
        request=_wiring_request(
            sha=sha,
            submit_kind=CycleSubmitInjectionKind.UNKNOWN_TIMEOUT,
            state_dir=tmp_path,
            apply_durable=True,
        ),
    )
    assert res.lifecycle is not None
    assert res.lifecycle.reconciliation.decision.outcome == OUTCOME_HALTED_UNRESOLVED
    assert res.ghv_forward_join == "PASS"
    assert res.ghv_reverse_join == "PASS"


def test_full_fill_durable_terminal(tmp_path: Path) -> None:
    sha = _origin_main()
    env = _envelope()
    fixture = OfflineExchangeFixtureV1(
        order_history={"data": [_order_row_join(state="filled", acc="1")]}
    )
    res = run_full_core_governed_cycle_host_post_submit_lifecycle_wiring_v1(
        cycle=_cycle(envelope=env),
        handoff=_handoff(sha=sha),
        request=_wiring_request(
            sha=sha,
            submit_kind=CycleSubmitInjectionKind.ACKNOWLEDGED,
            fixture=fixture,
            post=_ack_post(),
            state_dir=tmp_path,
            apply_durable=True,
        ),
    )
    assert res.lifecycle is not None
    assert res.lifecycle.reconciliation.decision.outcome == OUTCOME_CONFIRMED_FILLED


def test_duplicate_lifecycle_invocation_idempotent_outcome(tmp_path: Path) -> None:
    sha = _origin_main()
    env = _envelope()
    cycle = _cycle(envelope=env)
    handoff = _handoff(sha=sha)
    first = run_full_core_governed_cycle_host_post_submit_lifecycle_wiring_v1(
        cycle=cycle,
        handoff=handoff,
        request=_wiring_request(
            sha=sha,
            submit_kind=CycleSubmitInjectionKind.UNKNOWN_OUTCOME,
            state_dir=tmp_path / "first",
            apply_durable=True,
        ),
    )
    second = run_full_core_governed_cycle_host_post_submit_lifecycle_wiring_v1(
        cycle=cycle,
        handoff=handoff,
        request=_wiring_request(
            sha=sha,
            submit_kind=CycleSubmitInjectionKind.UNKNOWN_OUTCOME,
            state_dir=tmp_path / "second",
            apply_durable=True,
        ),
    )
    assert first.lifecycle is not None and second.lifecycle is not None
    assert (
        first.lifecycle.reconciliation.decision.outcome
        == second.lifecycle.reconciliation.decision.outcome
    )


def test_wiring_denied_without_owner_go() -> None:
    sha = _origin_main()
    env = _envelope()
    bad = FullCoreCycleLifecycleWiringRequestV1(
        mode=CycleLifecycleWiringMode.OFFLINE_INJECTED,
        owner_gos=FullCoreCycleLifecycleWiringOwnerGosV1(
            governed_lifecycle_wiring_go="DENIED",
            offline_implementation_go="GRANTED",
            private_get_go="NOT_GRANTED",
        ),
        origin_main_sha=resolve_origin_main_sha_v1(declared=sha),
        submit_kind=CycleSubmitInjectionKind.NOT_ATTEMPTED,
        offline_fixture=OfflineExchangeFixtureV1(),
    )
    with pytest.raises(FullCoreCycleLifecycleWiringError):
        run_full_core_governed_cycle_host_post_submit_lifecycle_wiring_v1(
            cycle=_cycle(envelope=env),
            handoff=_handoff(sha=sha),
            request=bad,
        )


def test_maybe_record_empty_without_context() -> None:
    assert (
        maybe_record_full_core_governed_cycle_lifecycle_wiring_v1(
            cycle=_cycle(envelope=_envelope()),
            handoff=_handoff(sha=_origin_main()),
        )
        == {}
    )


def test_cycle_host_hook_invokes_when_context_bound(tmp_path: Path) -> None:
    sha = _origin_main()
    env = _envelope()
    req = _wiring_request(
        sha=sha,
        submit_kind=CycleSubmitInjectionKind.NOT_ATTEMPTED,
        state_dir=tmp_path,
    )
    tokens = bind_full_core_cycle_lifecycle_wiring_invocation_v1(request=req)
    try:
        fields = maybe_record_full_core_governed_cycle_lifecycle_wiring_v1(
            cycle=_cycle(envelope=env),
            handoff=_handoff(sha=sha),
        )
    finally:
        reset_full_core_cycle_lifecycle_wiring_invocation_v1(tokens)
    assert fields.get("FULL_CORE_CYCLE_LIFECYCLE_WIRING") == "INVOKED"
    assert fields.get("FULL_CORE_CYCLE_LIFECYCLE_GHV_FORWARD") == "PASS"


class TestContextVarSafety:
    """PRE_PR_ADVERSARIAL_CONTRACT_REVIEW_V1 — ContextVar invocation boundary."""

    def test_no_context_no_side_effects(self) -> None:
        assert (
            maybe_record_full_core_governed_cycle_lifecycle_wiring_v1(
                cycle=_cycle(envelope=_envelope()),
                handoff=_handoff(sha=_origin_main()),
            )
            == {}
        )

    def test_disabled_mode_in_context_is_inert(self, tmp_path: Path) -> None:
        sha = _origin_main()
        req = FullCoreCycleLifecycleWiringRequestV1(
            mode=CycleLifecycleWiringMode.DISABLED,
            owner_gos=_owner_gos(),
            origin_main_sha=resolve_origin_main_sha_v1(declared=sha),
            submit_kind=CycleSubmitInjectionKind.NOT_ATTEMPTED,
            offline_fixture=OfflineExchangeFixtureV1(),
            atomic_state_dir=tmp_path,
        )
        tokens = bind_full_core_cycle_lifecycle_wiring_invocation_v1(request=req)
        try:
            assert (
                maybe_record_full_core_governed_cycle_lifecycle_wiring_v1(
                    cycle=_cycle(envelope=_envelope()),
                    handoff=_handoff(sha=sha),
                )
                == {}
            )
        finally:
            reset_full_core_cycle_lifecycle_wiring_invocation_v1(tokens)

    def test_reset_in_finally_clears_context(self, tmp_path: Path) -> None:
        sha = _origin_main()
        req = _wiring_request(
            sha=sha,
            submit_kind=CycleSubmitInjectionKind.NOT_ATTEMPTED,
            state_dir=tmp_path,
        )
        tokens = bind_full_core_cycle_lifecycle_wiring_invocation_v1(request=req)
        try:
            raise RuntimeError("simulated_cycle_failure")
        except RuntimeError:
            reset_full_core_cycle_lifecycle_wiring_invocation_v1(tokens)
        assert (
            maybe_record_full_core_governed_cycle_lifecycle_wiring_v1(
                cycle=_cycle(envelope=_envelope()),
                handoff=_handoff(sha=sha),
            )
            == {}
        )

    def test_nested_invocation_restores_outer(self, tmp_path: Path) -> None:
        sha = _origin_main()
        outer = _wiring_request(
            sha=sha,
            submit_kind=CycleSubmitInjectionKind.NOT_ATTEMPTED,
            state_dir=tmp_path / "outer",
        )
        inner = _wiring_request(
            sha=sha,
            submit_kind=CycleSubmitInjectionKind.NOT_ATTEMPTED,
            state_dir=tmp_path / "inner",
        )
        outer_tokens = bind_full_core_cycle_lifecycle_wiring_invocation_v1(request=outer)
        inner_tokens = bind_full_core_cycle_lifecycle_wiring_invocation_v1(request=inner)
        try:
            inner_fields = maybe_record_full_core_governed_cycle_lifecycle_wiring_v1(
                cycle=_cycle(envelope=_envelope()),
                handoff=_handoff(sha=sha),
            )
            assert inner_fields.get("FULL_CORE_CYCLE_LIFECYCLE_WIRING") == "INVOKED"
        finally:
            reset_full_core_cycle_lifecycle_wiring_invocation_v1(inner_tokens)
        outer_fields = maybe_record_full_core_governed_cycle_lifecycle_wiring_v1(
            cycle=_cycle(envelope=_envelope()),
            handoff=_handoff(sha=sha),
        )
        reset_full_core_cycle_lifecycle_wiring_invocation_v1(outer_tokens)
        assert outer_fields.get("FULL_CORE_CYCLE_LIFECYCLE_WIRING") == "INVOKED"

    def test_spawned_process_does_not_inherit_parent_invocation(self, tmp_path: Path) -> None:
        sha = _origin_main()
        req = _wiring_request(
            sha=sha,
            submit_kind=CycleSubmitInjectionKind.NOT_ATTEMPTED,
            state_dir=tmp_path,
        )
        tokens = bind_full_core_cycle_lifecycle_wiring_invocation_v1(request=req)
        ctx = mp.get_context("spawn")
        queue: mp.Queue = ctx.Queue()

        try:
            proc = ctx.Process(target=_spawn_child_maybe_record_probe, args=(queue, sha))
            proc.start()
            proc.join(timeout=30)
            assert proc.exitcode == 0
            assert queue.get(timeout=5) == {}
            parent = maybe_record_full_core_governed_cycle_lifecycle_wiring_v1(
                cycle=_cycle(envelope=_envelope()),
                handoff=_handoff(sha=sha),
            )
            assert parent.get("FULL_CORE_CYCLE_LIFECYCLE_WIRING") == "INVOKED"
        finally:
            reset_full_core_cycle_lifecycle_wiring_invocation_v1(tokens)


class TestAdversarialContractReview:
    """PRE_PR_ADVERSARIAL_CONTRACT_REVIEW_V1 — offline wiring invariants."""

    def test_missing_lifecycle_when_mode_disabled(self) -> None:
        sha = _origin_main()
        req = FullCoreCycleLifecycleWiringRequestV1(
            mode=CycleLifecycleWiringMode.DISABLED,
            owner_gos=_owner_gos(),
            origin_main_sha=resolve_origin_main_sha_v1(declared=sha),
            submit_kind=CycleSubmitInjectionKind.NOT_ATTEMPTED,
            offline_fixture=OfflineExchangeFixtureV1(),
        )
        with pytest.raises(FullCoreCycleLifecycleWiringError, match="DISABLED"):
            run_full_core_governed_cycle_host_post_submit_lifecycle_wiring_v1(
                cycle=_cycle(envelope=_envelope()),
                handoff=_handoff(sha=sha),
                request=req,
            )

    def test_hold_cycle_rejects_wiring(self) -> None:
        sha = _origin_main()
        env = _envelope()
        cycle = _cycle(envelope=env)
        cycle = CurrentProductiveGovernedCycleResultV1(
            **{**cycle.__dict__, "disposition": "HOLD", "terminal_class": "HOLD"}
        )
        with pytest.raises(FullCoreCycleLifecycleWiringError, match="PRE_EXTERNAL"):
            run_full_core_governed_cycle_host_post_submit_lifecycle_wiring_v1(
                cycle=cycle,
                handoff=_handoff(sha=sha),
                request=_wiring_request(
                    sha=sha,
                    submit_kind=CycleSubmitInjectionKind.NOT_ATTEMPTED,
                ),
            )

    def test_ack_requires_injected_post(self, tmp_path: Path) -> None:
        sha = _origin_main()
        req = _wiring_request(
            sha=sha,
            submit_kind=CycleSubmitInjectionKind.ACKNOWLEDGED,
            post=None,
            state_dir=tmp_path,
        )
        with pytest.raises(FullCoreCycleLifecycleWiringError, match="INJECTED_ACK"):
            run_full_core_governed_cycle_host_post_submit_lifecycle_wiring_v1(
                cycle=_cycle(envelope=_envelope()),
                handoff=_handoff(sha=sha),
                request=req,
            )


def test_restart_unknown_atomic_not_terminal_without_proof(tmp_path: Path) -> None:
    sha = _origin_main()
    res = run_full_core_governed_cycle_host_post_submit_lifecycle_wiring_v1(
        cycle=_cycle(envelope=_envelope()),
        handoff=_handoff(sha=sha),
        request=_wiring_request(
            sha=sha,
            submit_kind=CycleSubmitInjectionKind.UNKNOWN_OUTCOME,
            state_dir=tmp_path,
            apply_durable=True,
        ),
    )
    assert res.lifecycle is not None
    assert res.lifecycle.reconciliation.decision.outcome == OUTCOME_HALTED_UNRESOLVED
    assert res.lifecycle.reconciliation.atomic_state_after in {
        STATE_HALTED_UNRESOLVED,
        "RECONCILIATION_PENDING",
    }
    assert res.lifecycle.reconciliation.atomic_state_after != "TERMINAL_RECONCILED"


def _concurrent_worker(args: tuple[str, str, str]) -> str:
    state_dir, sha, suffix = args
    env = _envelope()
    req = _wiring_request(
        sha=sha,
        submit_kind=CycleSubmitInjectionKind.UNKNOWN_TIMEOUT,
        state_dir=Path(state_dir) / suffix,
        apply_durable=True,
    )
    res = run_full_core_governed_cycle_host_post_submit_lifecycle_wiring_v1(
        cycle=_cycle(envelope=env),
        handoff=_handoff(sha=sha),
        request=req,
    )
    assert res.lifecycle is not None
    return res.lifecycle.reconciliation.decision.outcome


def _spawn_child_maybe_record_probe(out_q: mp.Queue, origin_sha: str) -> None:
    out_q.put(
        maybe_record_full_core_governed_cycle_lifecycle_wiring_v1(
            cycle=_cycle(envelope=_envelope()),
            handoff=_handoff(sha=origin_sha),
        )
    )


def test_concurrent_lifecycle_invocation_fail_closed_or_consistent() -> None:
    sha = _origin_main()
    with tempfile.TemporaryDirectory() as tmp:
        ctx = mp.get_context("spawn")
        with ctx.Pool(2) as pool:
            outcomes = pool.map(
                _concurrent_worker,
                [(tmp, sha, "a"), (tmp, sha, "b")],
            )
        assert outcomes[0] == outcomes[1]
