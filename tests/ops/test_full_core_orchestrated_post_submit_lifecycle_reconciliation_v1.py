"""Orchestrated post-submit lifecycle reconciliation join (offline)."""

from __future__ import annotations

import multiprocessing as mp
import subprocess
from pathlib import Path

import pytest

from src.ops.full_core_live_path_composition_root_v1.full_core_capital_guard_atomic_one_shot_v1 import (
    STATE_HALTED_UNRESOLVED,
    full_core_atomic_mark_submit_boundary_v1,
    full_core_atomic_reserve_owner_go_authorization_v1,
    load_full_core_atomic_authorization_state_v1,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_exchange_reconciliation_offline_provider_v1 import (
    OfflineExchangeFixtureV1,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_exchange_reconciliation_v1 import (
    OUTCOME_HALTED_UNRESOLVED,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_orchestrated_post_submit_lifecycle_reconciliation_v1 import (
    FullCoreOrchestratedLifecycleReconciliationError,
    LifecycleReconciliationOrchestrationMode,
    PostSubmitLifecycleReconciliationOrchestrationRequestV1,
    orchestrate_post_submit_lifecycle_reconciliation_v1,
    resolve_origin_main_sha_v1,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_post_response_to_ack_mapper_v1 import (
    join_full_core_post_result_to_lifecycle_v1,
)
from tests.ops.test_full_core_post_submit_exchange_reconciliation_lifecycle_join_v1 import (
    _ack_post_result,
    _join_kwargs,
)
from tests.ops.test_full_core_exchange_reconciliation_v1 import CL, _binding, _order_row


def _origin_main() -> str:
    proc = subprocess.run(
        ["git", "rev-parse", "origin/main"],
        capture_output=True,
        text=True,
        check=True,
    )
    return str(proc.stdout or "").strip()


def _orchestration_request(
    **overrides: object,
) -> PostSubmitLifecycleReconciliationOrchestrationRequestV1:
    base = {
        "mode": LifecycleReconciliationOrchestrationMode.OFFLINE_FIXTURE,
        "work_package_owner_go": "GRANTED",
        "private_get_go": "GRANTED_SCOPED_READ_ONLY",
        "offline_implementation_go": "GRANTED",
        "origin_main_sha": resolve_origin_main_sha_v1(declared=_origin_main()),
        "decision_outcome": "ENTER",
        "venue_plan_identity": "vp-orch",
        "envelope_identity": "env-orch",
        "submit_attempt_id": "submit-orch",
        "local_durable_state_version": "v1",
        "pretrade_decision_id": "pretrade-orch",
        "offline_fixture": OfflineExchangeFixtureV1(),
    }
    base.update(overrides)
    return PostSubmitLifecycleReconciliationOrchestrationRequestV1(**base)  # type: ignore[arg-type]


def test_orchestrator_offline_unknown_restart_recovery(tmp_path: Path) -> None:
    binding = _binding()
    full_core_atomic_reserve_owner_go_authorization_v1(state_dir=tmp_path, binding=binding)
    full_core_atomic_mark_submit_boundary_v1(state_dir=tmp_path, binding=binding)
    post_join = join_full_core_post_result_to_lifecycle_v1(
        result=None,
        sent_clordid=CL,
        transport_error="UNKNOWN_OUTCOME",
    )
    req = _orchestration_request(
        offline_fixture=OfflineExchangeFixtureV1(),
        state_dir=tmp_path,
        apply_durable_atomic_state=True,
    )
    first = orchestrate_post_submit_lifecycle_reconciliation_v1(
        post_submit_join=post_join,
        binding=binding,
        request=req,
    )
    second = orchestrate_post_submit_lifecycle_reconciliation_v1(
        post_submit_join=post_join,
        binding=binding,
        request=req,
    )
    assert first.reconciliation.decision.outcome == OUTCOME_HALTED_UNRESOLVED
    assert second.reconciliation.decision.outcome == first.reconciliation.decision.outcome
    loaded = load_full_core_atomic_authorization_state_v1(
        state_dir=tmp_path, consumption_key=binding.consumption_key()
    )
    assert loaded is not None
    assert loaded.state == STATE_HALTED_UNRESOLVED


def test_duplicate_lifecycle_invocation_idempotent_decision() -> None:
    post_join = join_full_core_post_result_to_lifecycle_v1(
        result=_ack_post_result(),
        sent_clordid=CL,
    )
    row = _order_row(state="live")
    row["ordId"] = "ord-join-1"
    req = _orchestration_request(
        offline_fixture=OfflineExchangeFixtureV1(pending_orders={"data": [row]}),
    )
    a = orchestrate_post_submit_lifecycle_reconciliation_v1(
        post_submit_join=post_join, binding=_binding(), request=req
    )
    b = orchestrate_post_submit_lifecycle_reconciliation_v1(
        post_submit_join=post_join, binding=_binding(), request=req
    )
    assert a.reconciliation.decision.outcome == b.reconciliation.decision.outcome
    assert a.ghv_forward_join == "PASS"
    assert b.ghv_reverse_join == "PASS"


def _worker(state_dir: str) -> None:
    binding = _binding()
    full_core_atomic_reserve_owner_go_authorization_v1(state_dir=Path(state_dir), binding=binding)
    post_join = join_full_core_post_result_to_lifecycle_v1(
        result=None, sent_clordid=CL, transport_error="TIMEOUT"
    )
    req = _orchestration_request(
        offline_fixture=OfflineExchangeFixtureV1(),
        state_dir=Path(state_dir),
        apply_durable_atomic_state=True,
    )
    orchestrate_post_submit_lifecycle_reconciliation_v1(
        post_submit_join=post_join,
        binding=binding,
        request=req,
    )


def test_concurrent_durable_apply_one_wins_fail_closed(tmp_path: Path) -> None:
    ctx = mp.get_context("spawn")
    workers = []
    for _ in range(2):
        p = ctx.Process(target=_worker, args=(str(tmp_path),))
        p.start()
        workers.append(p)
    codes = []
    for p in workers:
        p.join(timeout=30)
        codes.append(p.exitcode)
    assert any(code == 0 for code in codes)
    assert any(code != 0 for code in codes)


def test_owner_go_denied_without_private_get() -> None:
    post_join = join_full_core_post_result_to_lifecycle_v1(
        result=_ack_post_result(), sent_clordid=CL
    )
    req = _orchestration_request(private_get_go="DENIED")
    with pytest.raises(FullCoreOrchestratedLifecycleReconciliationError):
        orchestrate_post_submit_lifecycle_reconciliation_v1(
            post_submit_join=post_join,
            binding=_binding(),
            request=req,
        )


def test_productive_mode_rejects_durable_apply() -> None:
    post_join = join_full_core_post_result_to_lifecycle_v1(
        result=_ack_post_result(), sent_clordid=CL
    )

    class _Transport:
        transport_class = "FULL_CORE_PRODUCTIVE_READ_ONLY_GET_V1"

        def get(self, **kwargs: object) -> None:
            raise AssertionError("network forbidden in unit test")

    req = _orchestration_request(
        mode=LifecycleReconciliationOrchestrationMode.PRODUCTIVE_OKX_SCOPED_READ_ONLY,
        read_only_get_transport=_Transport(),  # type: ignore[arg-type]
        apply_durable_atomic_state=True,
        offline_fixture=None,
    )
    with pytest.raises(FullCoreOrchestratedLifecycleReconciliationError):
        orchestrate_post_submit_lifecycle_reconciliation_v1(
            post_submit_join=post_join,
            binding=_binding(),
            request=req,
        )
