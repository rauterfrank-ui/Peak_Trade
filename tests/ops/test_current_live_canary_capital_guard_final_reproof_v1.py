"""Final offline reproof for CURRENT Live Canary Capital Guard (WP closure)."""

from __future__ import annotations

import inspect
import json
import multiprocessing as mp
import subprocess
from pathlib import Path

import pytest

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.canary_atomic_recovery_adjudicate_v1 import (
    OUTCOME_ORDER_NOT_FOUND,
    OUTCOME_ORDER_REJECTED,
    OUTCOME_PARTIAL_FILL,
    adjudicate_canary_entry_recovery_offline_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.canary_capital_guard_atomic_one_shot_v1 import (
    CanaryAtomicOneShotError,
    CanaryAuthorizationBindingV1,
    STATE_SUBMIT_MAY_HAVE_OCCURRED,
    atomic_mark_submit_boundary_v1,
    atomic_mark_unknown_submit_v1,
    atomic_reserve_owner_go_authorization_v1,
    assert_atomic_entry_authorization_available_v1,
    load_atomic_authorization_state_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.canary_capital_guard_durable_ledger_v1 import (
    record_durable_unknown_submit_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    ENDPOINT_SUBMIT,
    OWNER_GO_EXECUTE,
    POST_ENDPOINTS_GATED,
    REUSED_BINDING_ACCOUNT_SCOPE,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.ghv_canary_capital_guard_observability_v1 import (
    STAGE_CANARY_CAPITAL_GUARD_DECISION,
    build_canary_capital_guard_ghv_bundle_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.http_client_v1 import (
    LiveCanaryHttpClientV1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.submit_transport_v1 import (
    run_canary_submit_transport_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.current_live_canary_capital_guard_v1 import (
    evaluate_canary_capital_guard_entry_v1,
    evaluate_canary_capital_guard_flatten_v1,
)
from tests.ops.test_current_live_canary_capital_guard_v1 import (
    _clean_exposure,
    _clean_margin,
    _ratified_offline_config,
    _sample_plan,
    _session,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def _binding(**kwargs: str) -> CanaryAuthorizationBindingV1:
    base = {
        "owner_go": OWNER_GO_EXECUTE,
        "origin_main_sha": "abc123",
        "account_scope": REUSED_BINDING_ACCOUNT_SCOPE,
        "environment": "LIVE",
        "instrument_id": "SUI-USDT-SWAP",
        "plan_digest": "plan-1",
        "guard_config_digest": "cfg-digest",
        "session_id": "sess-1",
        "clordid": "cl-1",
    }
    base.update(kwargs)
    return CanaryAuthorizationBindingV1(**base)


def test_ack_rejected_after_post_attempt_recovery() -> None:
    adj = adjudicate_canary_entry_recovery_offline_v1(
        clordid="cl-rej",
        pending_orders_payload={"data": []},
        history_payload={
            "data": [{"clOrdId": "cl-rej", "state": "canceled", "sCode": "51008", "sMsg": "reject"}]
        },
        positions_payload={"data": []},
        instrument_id="SUI-USDT-SWAP",
    )
    assert adj.outcome == OUTCOME_ORDER_REJECTED
    assert adj.reconciliation_complete is True
    assert adj.exposure_retained is False


def test_partial_fill_retains_exchange_exposure() -> None:
    adj = adjudicate_canary_entry_recovery_offline_v1(
        clordid="cl-pf",
        pending_orders_payload={
            "data": [
                {
                    "clOrdId": "cl-pf",
                    "state": "partially_filled",
                    "accFillSz": "0.5",
                    "fillSz": "0.5",
                }
            ]
        },
        history_payload={"data": []},
        positions_payload={"data": []},
        instrument_id="SUI-USDT-SWAP",
    )
    assert adj.outcome == OUTCOME_PARTIAL_FILL
    assert adj.exposure_retained is True
    assert adj.reconciliation_complete is False


def test_crash_after_post_before_ack_boundary_state(tmp_path: Path) -> None:
    state_dir = tmp_path / "atomic"
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


def test_restart_after_unknown_submit_blocks_reentry(tmp_path: Path) -> None:
    state_dir = tmp_path / "atomic"
    ledger = tmp_path / "ledger.jsonl"
    b = _binding()
    atomic_reserve_owner_go_authorization_v1(state_dir=state_dir, binding=b)
    atomic_mark_submit_boundary_v1(state_dir=state_dir, binding=b)
    record_durable_unknown_submit_v1(
        ledger_path=ledger,
        scope_key=b.consumption_key(),
        plan_digest=b.plan_digest,
        binding=b,
        atomic_state_dir=state_dir,
    )
    with pytest.raises(CanaryAtomicOneShotError, match="OWNER_GO_ALREADY_CONSUMED"):
        assert_atomic_entry_authorization_available_v1(state_dir=state_dir, binding=b)


def test_reconciliation_contradiction_halted_unresolved() -> None:
    adj = adjudicate_canary_entry_recovery_offline_v1(
        clordid="cl-x",
        pending_orders_payload={"data": [{"clOrdId": "cl-x", "state": "live"}]},
        history_payload={"data": [{"clOrdId": "cl-x", "state": "filled"}]},
        positions_payload={"data": []},
        instrument_id="SUI-USDT-SWAP",
    )
    assert adj.recommended_state == "HALTED_UNRESOLVED"


def test_order_not_found_without_never_submitted_proof() -> None:
    adj = adjudicate_canary_entry_recovery_offline_v1(
        clordid="cl-missing",
        pending_orders_payload={"data": []},
        history_payload={"data": []},
        positions_payload={"data": []},
        instrument_id="SUI-USDT-SWAP",
    )
    assert adj.outcome == OUTCOME_ORDER_NOT_FOUND
    assert adj.evidence.get("note") == "ORDER_NOT_FOUND_NOT_PROVEN_NEVER_SUBMITTED"
    assert adj.reconciliation_complete is False


def test_permanent_owner_go_consumption_after_terminal_reconcile(tmp_path: Path) -> None:
    from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.canary_capital_guard_atomic_one_shot_v1 import (
        atomic_mark_reconciliation_pending_v1,
        atomic_mark_submitted_acknowledged_v1,
        atomic_mark_terminal_reconciled_v1,
    )

    state_dir = tmp_path / "atomic"
    b = _binding()
    atomic_reserve_owner_go_authorization_v1(state_dir=state_dir, binding=b)
    atomic_mark_submit_boundary_v1(state_dir=state_dir, binding=b)
    atomic_mark_submitted_acknowledged_v1(state_dir=state_dir, binding=b)
    atomic_mark_reconciliation_pending_v1(state_dir=state_dir, binding=b)
    atomic_mark_terminal_reconciled_v1(state_dir=state_dir, binding=b)
    row = load_atomic_authorization_state_v1(
        state_dir=state_dir, consumption_key=b.consumption_key()
    )
    assert row.authorization_permanently_consumed
    with pytest.raises(CanaryAtomicOneShotError):
        atomic_reserve_owner_go_authorization_v1(state_dir=state_dir, binding=b)


def _dup_submit_worker(state_dir: str, binding_dict: dict[str, str], q: mp.Queue) -> None:
    binding = CanaryAuthorizationBindingV1(**binding_dict)
    try:
        atomic_reserve_owner_go_authorization_v1(state_dir=Path(state_dir), binding=binding)
        atomic_mark_submit_boundary_v1(state_dir=Path(state_dir), binding=binding)
        q.put("SUBMIT_OK")
    except CanaryAtomicOneShotError as exc:
        q.put(str(exc))


def test_concurrent_duplicate_submit_at_most_one_boundary(tmp_path: Path) -> None:
    state_dir = tmp_path / "atomic"
    b = _binding()
    q: mp.Queue = mp.Queue()
    bd = b.to_dict()
    procs = [mp.Process(target=_dup_submit_worker, args=(str(state_dir), bd, q)) for _ in range(4)]
    for p in procs:
        p.start()
    for p in procs:
        p.join(timeout=30)
    results = [q.get(timeout=5) for _ in range(4)]
    assert results.count("SUBMIT_OK") == 1


def test_stale_lock_release_does_not_reset_consumption(tmp_path: Path) -> None:
    state_dir = tmp_path / "atomic"
    b = _binding()
    atomic_reserve_owner_go_authorization_v1(state_dir=state_dir, binding=b)
    lock_path = state_dir / f"{b.consumption_key().lower()}.lock"
    if lock_path.is_file():
        lock_path.unlink()
    with pytest.raises(CanaryAtomicOneShotError):
        atomic_reserve_owner_go_authorization_v1(state_dir=state_dir, binding=b)


def test_corrupt_durable_state_fails_closed(tmp_path: Path) -> None:
    state_dir = tmp_path / "atomic"
    b = _binding()
    key = b.consumption_key()
    state_dir.mkdir(parents=True, exist_ok=True)
    (state_dir / f"{key.lower()}.state.json").write_text("CORRUPT", encoding="utf-8")
    with pytest.raises(CanaryAtomicOneShotError):
        load_atomic_authorization_state_v1(state_dir=state_dir, consumption_key=key)


def test_emergency_flatten_separately_authorized() -> None:
    from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_pre_send_gate_v1 import (
        evaluate_flatten_pre_send_gate_v1,
    )

    flatten_src = inspect.getsource(evaluate_flatten_pre_send_gate_v1)
    assert "canary_capital_guard_atomic_one_shot_v1" not in flatten_src
    flatten_path = (
        REPO_ROOT
        / "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/flatten_pre_send_gate_v1.py"
    )
    assert "evaluate_canary_capital_guard_flatten_v1" in flatten_path.read_text(encoding="utf-8")
    assert evaluate_canary_capital_guard_flatten_v1 is not None


def test_current_pre_external_closure_post_count_zero(tmp_path: Path) -> None:
    """Reuse canonical WP2 offline harness in-process (GET-only; POST_COUNT=0)."""
    from tests.ops.test_full_core_current_productive_pre_external_closure_wp2_composition_v1 import (
        test_wp2_untrusted_29p_avail_zero_blocks_wp1_admissibility,
    )

    test_wp2_untrusted_29p_avail_zero_blocks_wp1_admissibility(tmp_path)


def test_current_pre_external_semantics_unchanged_no_canary_submit_in_productive_orchestrator() -> (
    None
):
    orch_path = (
        REPO_ROOT
        / "src/ops/full_core_live_path_composition_root_v1/current_productive_governed_cycle_orchestrator_v1.py"
    )
    text = orch_path.read_text(encoding="utf-8")
    assert "run_canary_submit_transport_v1" not in text
    diff = subprocess.run(
        [
            "git",
            "diff",
            "--name-only",
            "origin/main",
            "--",
            "src/ops/full_core_live_path_composition_root_v1/",
            "src/ops/governed_productive_account_equity_authority_producer_v1/current_productive_full_core_pre_external_closure_v1.py",
        ],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    assert diff.stdout.strip() == ""


def test_no_alternative_canary_entry_post_bypass() -> None:
    client_src = Path(LiveCanaryHttpClientV1.__module__.replace(".", "/") + ".py")
    client_src = (
        REPO_ROOT / "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/http_client_v1.py"
    )
    text = client_src.read_text(encoding="utf-8")
    assert ENDPOINT_SUBMIT in POST_ENDPOINTS_GATED or "POST_ENDPOINTS_GATED" in text
    transport_src = inspect.getsource(run_canary_submit_transport_v1)
    assert "post_entry_order" in transport_src
    assert "_evaluate_and_refuse_entry_capital_guard_v1" in transport_src
    assert "atomic_mark_submit_boundary_v1" in transport_src
    census = (
        REPO_ROOT
        / "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/remaining_execution_path_census_v1.py"
    ).read_text(encoding="utf-8")
    assert "submit_transport_v1" in census


def test_ghv_evidence_integrity_stages_and_no_authority() -> None:
    cfg = _ratified_offline_config()
    ev = evaluate_canary_capital_guard_entry_v1(
        plan=_sample_plan(max_notional="50"),
        guard_config=cfg,
        margin_evidence=_clean_margin(),
        exposure_evidence=_clean_exposure(),
        owner_go=OWNER_GO_EXECUTE,
        account_scope=REUSED_BINDING_ACCOUNT_SCOPE,
        session=_session(cfg),
        observed_leverage="5",
        durable_entry_state="AVAILABLE",
    )
    bundle = build_canary_capital_guard_ghv_bundle_v1(
        session_id="sess-final",
        guard_config=cfg.to_dict(),
        guard_input={"margin": "stub"},
        evaluation=ev,
    )
    assert bundle["ghv_authority"] == "NONE"
    stages = {row["stage"] for row in bundle["ghv_canary_capital_guard_stages"]}
    assert STAGE_CANARY_CAPITAL_GUARD_DECISION in stages
    assert "secret" not in json.dumps(bundle).lower()


def test_protected_cap24_ranking_files_unmodified_vs_main() -> None:
    protected = (
        "src/ops/governed_futures_universe_producer_v1/eligibility_v1.py",
        "src/ops/productive_futures_ranking_producer_v1/ranking_v1.py",
        "src/ops/single_selected_future_policy_v1/selection_v1.py",
    )
    diff = subprocess.run(
        ["git", "diff", "--name-only", "origin/main", "--", *protected],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    assert diff.stdout.strip() == ""
