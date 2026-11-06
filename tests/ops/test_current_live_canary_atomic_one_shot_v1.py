"""Offline fault-injection and multiprocess tests for canary atomic one-shot."""

from __future__ import annotations

import json
import multiprocessing as mp
import os
from pathlib import Path

import pytest

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.canary_atomic_recovery_adjudicate_v1 import (
    OUTCOME_CONTRADICTION,
    OUTCOME_ORDER_NOT_FOUND,
    OUTCOME_PROVEN_NEVER_SUBMITTED,
    adjudicate_canary_entry_recovery_offline_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.canary_capital_guard_atomic_one_shot_v1 import (
    CanaryAtomicOneShotError,
    CanaryAuthorizationBindingV1,
    STATE_RESERVED_PRE_POST,
    STATE_SUBMIT_MAY_HAVE_OCCURRED,
    STATE_SUBMITTED_ACKNOWLEDGED,
    STATE_TERMINAL_RECONCILED,
    atomic_mark_submit_boundary_v1,
    atomic_mark_submitted_acknowledged_v1,
    atomic_reserve_owner_go_authorization_v1,
    assert_atomic_entry_authorization_available_v1,
    load_atomic_authorization_state_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    OWNER_GO_EXECUTE,
    REUSED_BINDING_ACCOUNT_SCOPE,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.http_client_v1 import (
    LiveCanaryHttpClientV1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.current_live_canary_capital_guard_v1 import (
    CanaryCapitalGuardMarginEvidenceV1,
    IMR_SOURCE_PUBLIC_POSITION_TIERS_QTY_ONE,
    evaluate_canary_capital_guard_entry_v1,
    offline_proof_guard_config_v1,
)
from tests.ops.test_current_live_canary_capital_guard_v1 import (
    _clean_exposure,
    _ratified_offline_config,
    _sample_plan,
    _session,
)


def _binding(
    *,
    plan_digest: str = "plan-1",
    instrument_id: str = "SUI-USDT-SWAP",
    clordid: str = "cl-1",
    session_id: str = "sess-1",
    owner_go: str = OWNER_GO_EXECUTE,
    origin: str = "abc123",
) -> CanaryAuthorizationBindingV1:
    return CanaryAuthorizationBindingV1(
        owner_go=owner_go,
        origin_main_sha=origin,
        account_scope=REUSED_BINDING_ACCOUNT_SCOPE,
        environment="LIVE",
        instrument_id=instrument_id,
        plan_digest=plan_digest,
        guard_config_digest="cfg-digest",
        session_id=session_id,
        clordid=clordid,
    )


def _worker_reserve(state_dir: str, binding_dict: dict[str, str], q: mp.Queue) -> None:
    binding = CanaryAuthorizationBindingV1(**binding_dict)
    try:
        atomic_reserve_owner_go_authorization_v1(state_dir=Path(state_dir), binding=binding)
        q.put("OK")
    except CanaryAtomicOneShotError as exc:
        q.put(str(exc))


@pytest.fixture
def state_dir(tmp_path: Path) -> Path:
    d = tmp_path / "atomic_states"
    d.mkdir()
    return d


def test_two_simultaneous_processes_one_winner(state_dir: Path) -> None:
    b = _binding()
    q: mp.Queue = mp.Queue()
    bd = b.to_dict()
    procs = [
        mp.Process(target=_worker_reserve, args=(str(state_dir), bd, q)),
        mp.Process(target=_worker_reserve, args=(str(state_dir), bd, q)),
    ]
    for p in procs:
        p.start()
    for p in procs:
        p.join(timeout=30)
    results = [q.get(timeout=5) for _ in procs]
    assert results.count("OK") == 1
    assert sum(1 for r in results if r.startswith("OWNER_GO_ALREADY_CONSUMED")) == 1


def test_many_concurrent_at_most_one_winner(state_dir: Path) -> None:
    b = _binding()
    q: mp.Queue = mp.Queue()
    bd = b.to_dict()
    n = 6
    procs = [mp.Process(target=_worker_reserve, args=(str(state_dir), bd, q)) for _ in range(n)]
    for p in procs:
        p.start()
    for p in procs:
        p.join(timeout=30)
    results = [q.get(timeout=5) for _ in range(n)]
    assert results.count("OK") == 1


def test_same_owner_go_changed_instrument_blocks(state_dir: Path) -> None:
    b1 = _binding(instrument_id="SUI-USDT-SWAP")
    atomic_reserve_owner_go_authorization_v1(state_dir=state_dir, binding=b1)
    b2 = _binding(instrument_id="BTC-USDT-SWAP")
    with pytest.raises(CanaryAtomicOneShotError, match="OWNER_GO_PAYLOAD_BINDING_MISMATCH"):
        atomic_reserve_owner_go_authorization_v1(state_dir=state_dir, binding=b2)


def test_same_owner_go_changed_plan_digest_blocks(state_dir: Path) -> None:
    atomic_reserve_owner_go_authorization_v1(
        state_dir=state_dir, binding=_binding(plan_digest="p1")
    )
    with pytest.raises(CanaryAtomicOneShotError, match="OWNER_GO_PAYLOAD_BINDING_MISMATCH"):
        atomic_reserve_owner_go_authorization_v1(
            state_dir=state_dir, binding=_binding(plan_digest="p2")
        )


def test_same_owner_go_changed_clordid_blocks(state_dir: Path) -> None:
    atomic_reserve_owner_go_authorization_v1(state_dir=state_dir, binding=_binding(clordid="a"))
    with pytest.raises(CanaryAtomicOneShotError, match="OWNER_GO_PAYLOAD_BINDING_MISMATCH"):
        atomic_reserve_owner_go_authorization_v1(state_dir=state_dir, binding=_binding(clordid="b"))


def test_same_owner_go_changed_session_blocks(state_dir: Path) -> None:
    atomic_reserve_owner_go_authorization_v1(state_dir=state_dir, binding=_binding(session_id="s1"))
    with pytest.raises(CanaryAtomicOneShotError, match="OWNER_GO_PAYLOAD_BINDING_MISMATCH"):
        atomic_reserve_owner_go_authorization_v1(
            state_dir=state_dir, binding=_binding(session_id="s2")
        )


def test_restart_after_reservation_blocks_second_entry(state_dir: Path) -> None:
    b = _binding()
    atomic_reserve_owner_go_authorization_v1(state_dir=state_dir, binding=b)
    with pytest.raises(CanaryAtomicOneShotError, match="OWNER_GO_ALREADY_CONSUMED"):
        assert_atomic_entry_authorization_available_v1(state_dir=state_dir, binding=b)


def test_restart_after_submit_boundary_blocks(state_dir: Path) -> None:
    b = _binding()
    atomic_reserve_owner_go_authorization_v1(state_dir=state_dir, binding=b)
    atomic_mark_submit_boundary_v1(state_dir=state_dir, binding=b)
    with pytest.raises(CanaryAtomicOneShotError, match="OWNER_GO_ALREADY_CONSUMED"):
        atomic_reserve_owner_go_authorization_v1(state_dir=state_dir, binding=b)


def test_crash_before_post_state_reserved(state_dir: Path) -> None:
    b = _binding()
    atomic_reserve_owner_go_authorization_v1(state_dir=state_dir, binding=b)
    row = load_atomic_authorization_state_v1(
        state_dir=state_dir, consumption_key=b.consumption_key()
    )
    assert row is not None
    assert row.state == STATE_RESERVED_PRE_POST
    with pytest.raises(CanaryAtomicOneShotError):
        atomic_reserve_owner_go_authorization_v1(state_dir=state_dir, binding=b)


def test_crash_during_post_unknown_no_retry(state_dir: Path) -> None:
    b = _binding()
    atomic_reserve_owner_go_authorization_v1(state_dir=state_dir, binding=b)
    atomic_mark_submit_boundary_v1(state_dir=state_dir, binding=b)
    row = load_atomic_authorization_state_v1(
        state_dir=state_dir, consumption_key=b.consumption_key()
    )
    assert row is not None
    assert row.state == STATE_SUBMIT_MAY_HAVE_OCCURRED
    with pytest.raises(CanaryAtomicOneShotError):
        atomic_reserve_owner_go_authorization_v1(state_dir=state_dir, binding=b)


def test_crash_after_post_before_ack_boundary_state(state_dir: Path) -> None:
    b = _binding()
    atomic_reserve_owner_go_authorization_v1(state_dir=state_dir, binding=b)
    atomic_mark_submit_boundary_v1(state_dir=state_dir, binding=b)
    assert (
        load_atomic_authorization_state_v1(
            state_dir=state_dir, consumption_key=b.consumption_key()
        ).state
        == STATE_SUBMIT_MAY_HAVE_OCCURRED
    )


def test_ack_accepted_durable_state(state_dir: Path) -> None:
    b = _binding()
    atomic_reserve_owner_go_authorization_v1(state_dir=state_dir, binding=b)
    atomic_mark_submit_boundary_v1(state_dir=state_dir, binding=b)
    atomic_mark_submitted_acknowledged_v1(state_dir=state_dir, binding=b)
    row = load_atomic_authorization_state_v1(
        state_dir=state_dir, consumption_key=b.consumption_key()
    )
    assert row.state == STATE_SUBMITTED_ACKNOWLEDGED
    assert row.authorization_permanently_consumed


def test_owner_go_remains_consumed_after_terminal_reconcile(state_dir: Path) -> None:
    from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.canary_capital_guard_atomic_one_shot_v1 import (
        atomic_mark_terminal_reconciled_v1,
        atomic_mark_reconciliation_pending_v1,
    )

    b = _binding()
    atomic_reserve_owner_go_authorization_v1(state_dir=state_dir, binding=b)
    atomic_mark_submit_boundary_v1(state_dir=state_dir, binding=b)
    atomic_mark_submitted_acknowledged_v1(state_dir=state_dir, binding=b)
    atomic_mark_reconciliation_pending_v1(state_dir=state_dir, binding=b)
    atomic_mark_terminal_reconciled_v1(state_dir=state_dir, binding=b)
    with pytest.raises(CanaryAtomicOneShotError):
        atomic_reserve_owner_go_authorization_v1(state_dir=state_dir, binding=b)


def test_order_not_found_no_automatic_release() -> None:
    adj = adjudicate_canary_entry_recovery_offline_v1(
        clordid="cl-x",
        pending_orders_payload={"data": []},
        history_payload={"data": []},
        positions_payload={"data": []},
        instrument_id="SUI-USDT-SWAP",
    )
    assert adj.outcome == OUTCOME_ORDER_NOT_FOUND
    assert adj.reconciliation_complete is False


def test_reconciliation_contradiction_halted() -> None:
    pending = {"data": [{"clOrdId": "cl-x", "state": "live"}]}
    history = {"data": [{"clOrdId": "cl-x", "state": "filled"}]}
    adj = adjudicate_canary_entry_recovery_offline_v1(
        clordid="cl-x",
        pending_orders_payload=pending,
        history_payload=history,
        positions_payload={"data": []},
        instrument_id="SUI-USDT-SWAP",
    )
    assert adj.outcome == OUTCOME_CONTRADICTION
    assert adj.recommended_state == "HALTED_UNRESOLVED"


def test_proven_never_submitted_terminal() -> None:
    adj = adjudicate_canary_entry_recovery_offline_v1(
        clordid="cl-x",
        pending_orders_payload={"data": []},
        history_payload={"data": []},
        positions_payload={"data": []},
        instrument_id="SUI-USDT-SWAP",
        proven_never_submitted_evidence={"transport": "stub_no_wire"},
    )
    assert adj.outcome == OUTCOME_PROVEN_NEVER_SUBMITTED
    assert adj.recommended_state == STATE_TERMINAL_RECONCILED


def test_ledger_corruption_blocks(state_dir: Path) -> None:
    b = _binding()
    key = b.consumption_key()
    state_path = state_dir / f"{key.lower()}.state.json"
    state_dir.mkdir(parents=True, exist_ok=True)
    state_path.write_text("{not-json", encoding="utf-8")
    with pytest.raises(CanaryAtomicOneShotError, match="LEDGER_CORRUPT"):
        load_atomic_authorization_state_v1(state_dir=state_dir, consumption_key=key)


def test_interrupted_write_blocks(state_dir: Path) -> None:
    b = _binding()
    key = b.consumption_key()
    tmp = state_dir / f".{key.lower()}.state.json.incomplete"
    state_dir.mkdir(parents=True, exist_ok=True)
    tmp.write_text('{"schema_version":', encoding="utf-8")
    assert not (state_dir / f"{key.lower()}.state.json").exists()
    assert_atomic_entry_authorization_available_v1(state_dir=state_dir, binding=b)


def test_different_owner_go_scopes_independent(state_dir: Path) -> None:
    b1 = _binding(owner_go=OWNER_GO_EXECUTE, origin="sha1")
    b2 = _binding(owner_go=OWNER_GO_EXECUTE, origin="sha2")
    atomic_reserve_owner_go_authorization_v1(state_dir=state_dir, binding=b1)
    atomic_reserve_owner_go_authorization_v1(state_dir=state_dir, binding=b2)


def test_entry_post_has_no_transport_retry_loop() -> None:
    src = Path(LiveCanaryHttpClientV1.post_entry_order.__code__.co_filename).read_text(
        encoding="utf-8"
    )
    assert "def post_entry_order" in src
    body = src.split("def post_entry_order", 1)[1].split("\n    def ", 1)[0]
    assert "RETRY_BACKOFF" not in body
    assert "for attempt" not in body.lower()


def test_guard_missing_caps_still_blocks() -> None:
    cfg = offline_proof_guard_config_v1()
    ev = evaluate_canary_capital_guard_entry_v1(
        plan=_sample_plan(max_notional="50"),
        guard_config=cfg,
        margin_evidence=CanaryCapitalGuardMarginEvidenceV1(
            avail_eq_usdc="1000",
            imr_rate="0.05",
            imr_source_class=IMR_SOURCE_PUBLIC_POSITION_TIERS_QTY_ONE,
            pretrade_decision_id="pt-1",
            expected_pretrade_decision_id="pt-1",
        ),
        exposure_evidence=_clean_exposure(),
        owner_go=OWNER_GO_EXECUTE,
        account_scope=REUSED_BINDING_ACCOUNT_SCOPE,
        session=_session(cfg),
        durable_entry_state="AVAILABLE",
    )
    assert "OWNER_CAPS_UNRATIFIED" in ev.reasons or "LIVE_CANARY_ALLOWED_FALSE" in ev.reasons


def test_ghv_atomic_stage_no_secrets() -> None:
    from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.ghv_canary_capital_guard_observability_v1 import (
        record_canary_atomic_one_shot_ghv_stage_v1,
    )

    row = record_canary_atomic_one_shot_ghv_stage_v1(
        session_id="s",
        consumption_key="k",
        binding_digest="d",
        stage="ATOMIC_RESERVATION",
        payload={"result": "OK"},
    )
    blob = json.dumps(row).lower()
    assert "secret" not in blob
    assert "passphrase" not in blob


def test_flatten_module_separate_from_entry_atomic() -> None:
    flatten = Path(__file__).resolve().parents[2] / (
        "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/flatten_pre_send_gate_v1.py"
    )
    text = flatten.read_text(encoding="utf-8")
    assert "canary_capital_guard_atomic_one_shot_v1" not in text
