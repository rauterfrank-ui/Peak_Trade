"""Offline E2E proofs for FULL_CORE_PRE_POST_CAPITAL_GUARD_JOIN_V1."""

from __future__ import annotations

import multiprocessing as mp
import tempfile
from dataclasses import replace
from decimal import Decimal
from pathlib import Path

import pytest

from src.ops.full_core_live_path_composition_root_v1.current_full_core_capital_guard_v1 import (
    OWNER_GO_FULL_CORE_PRE_POST,
    offline_proof_full_core_guard_config_v1,
    ratified_offline_full_core_guard_config_v1,
)
from src.ops.full_core_live_path_composition_root_v1.final_order_envelope_v1 import (
    build_final_order_envelope_v1,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_capital_guard_atomic_one_shot_v1 import (
    FullCoreAuthorizationBindingV1,
    FullCoreAtomicOneShotError,
    assert_full_core_entry_authorization_available_v1,
    full_core_atomic_reserve_owner_go_authorization_v1,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_capital_guard_reconciliation_stub_v1 import (
    OUTCOME_HALTED_UNRESOLVED,
    OUTCOME_ORDER_NOT_FOUND,
    OUTCOME_PARTIAL_FILL,
    FullCoreReconciliationEvidenceV1,
    adjudicate_full_core_entry_recovery_stub_v1,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_pre_post_capital_guard_join_v1 import (
    FullCoreCapitalGuardJoinMode,
    FullCorePrePostCapitalGuardJoinBindingV1,
    resolve_full_core_capital_guard_join_mode_v1,
    run_full_core_pre_post_capital_guard_join_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_governed_cycle_orchestrator_v1 import (
    DISPOSITION_PRE_EXTERNAL_EFFECT,
)
from src.ops.full_core_live_path_composition_root_v1.ghv_full_core_capital_guard_observability_v1 import (
    STAGE_CAPITAL_GUARD_DECISION,
    STAGE_PRE_EXTERNAL_REACHED,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    OWNER_GO_EXECUTE,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.current_live_canary_capital_guard_v1 import (
    CanaryCapitalGuardExposureEvidenceV1,
    CanaryCapitalGuardMarginEvidenceV1,
    IMR_SOURCE_PUBLIC_POSITION_TIERS_QTY_ONE,
)

NATIVE = "0G-USDT-SWAP"
INST = NATIVE


def _envelope(*, side: str = "buy", qty: str = "1", price: str = "10") -> object:
    cl = "ptfullcoretest00001"
    return build_final_order_envelope_v1(
        instrument_id=INST,
        side=side,
        order_type="limit",
        quantity=qty,
        quantity_unit="CONTRACTS",
        td_mode="cross",
        reduce_only=False,
        client_order_id=cl,
        path_kind="ENTER",
        venue_plan_clordid=cl,
        quantity_source="FIXTURE",
        side_source="FIXTURE",
        instrument_source="FIXTURE",
        admission_ref="adm-1",
        provenance_ref="prov-1",
        creation_epoch="1700000000",
        price=price,
    )


def _binding(
    envelope,
    *,
    direction: str = "ENTER_LONG",
    side: str = "buy",
    qty: str = "1",
    price: str = "10",
    pre_external: bool = True,
    owner_go: str = OWNER_GO_FULL_CORE_PRE_POST,
    decision_id: str = "dec-1",
    venue_digest: str = "venue-digest-1",
    account: str = "acct-full-core-1",
    env: str = "OFFLINE_STUB",
    cfg_digest: str | None = None,
) -> FullCorePrePostCapitalGuardJoinBindingV1:
    cfg_digest = cfg_digest or ratified_offline_full_core_guard_config_v1().config_digest
    return FullCorePrePostCapitalGuardJoinBindingV1(
        canonical_decision_id=decision_id,
        native_id=NATIVE,
        instrument_id=INST,
        selected_direction=direction,
        order_side=side,
        final_quantity=qty,
        order_type="limit",
        order_price=price,
        venue_plan_digest=venue_digest,
        envelope_digest=envelope.envelope_digest,
        account_identity=account,
        environment=env,
        execution_mode="OFFLINE_STUB",
        owner_go=owner_go,
        origin_main_sha="38d607a43aa38683cb21158aa96703866fb0a2ac",
        guard_config_digest=cfg_digest,
        clordid=envelope.client_order_id,
        pre_external_reached=pre_external,
        terminal_disposition=DISPOSITION_PRE_EXTERNAL_EFFECT if pre_external else "HOLD",
        ct_val="1",
        min_sz="1",
        lot_sz="1",
    )


def _clean_margin(**kw: object) -> CanaryCapitalGuardMarginEvidenceV1:
    base = dict(
        avail_eq_usdc="10000",
        imr_rate="0.05",
        imr_source_class=IMR_SOURCE_PUBLIC_POSITION_TIERS_QTY_ONE,
        pretrade_decision_id="dec-1",
        expected_pretrade_decision_id="dec-1",
    )
    base.update(kw)
    return CanaryCapitalGuardMarginEvidenceV1(**base)  # type: ignore[arg-type]


def _clean_exposure(**kw: object) -> CanaryCapitalGuardExposureEvidenceV1:
    base = dict(
        open_order_count=0,
        open_position_count=0,
        unknown_submit_active=False,
        recovery_state_clear=True,
        transport_retry_count=0,
    )
    base.update(kw)
    return CanaryCapitalGuardExposureEvidenceV1(**base)  # type: ignore[arg-type]


def _run_join(**kwargs: object):
    binding = kwargs.get("binding")
    account_scope = getattr(binding, "account_identity", "acct-full-core-1")
    env_scope = getattr(binding, "environment", "OFFLINE_STUB")
    defaults = dict(
        join_mode=FullCoreCapitalGuardJoinMode.OFFLINE_STUB,
        guard_config=ratified_offline_full_core_guard_config_v1(),
        margin_evidence=_clean_margin(),
        exposure_evidence=_clean_exposure(),
        observed_leverage="5",
        account_evidence_scope=kwargs.pop("account_evidence_scope", account_scope),
        authoritative_environment=kwargs.pop("authoritative_environment", env_scope),
        authoritative_venue_plan_digest=kwargs.pop(
            "authoritative_venue_plan_digest",
            getattr(binding, "venue_plan_digest", "venue-digest-1"),
        ),
        atomic_state_dir=kwargs.pop("atomic_state_dir", None),
    )
    if defaults["atomic_state_dir"] is None:
        defaults["atomic_state_dir"] = Path(tempfile.mkdtemp(prefix="fc-cap-guard-"))
    defaults.update(kwargs)
    return run_full_core_pre_post_capital_guard_join_v1(**defaults)  # type: ignore[arg-type]


def test_default_join_mode_disabled() -> None:
    assert (
        resolve_full_core_capital_guard_join_mode_v1(explicit_mode=None)
        is FullCoreCapitalGuardJoinMode.DISABLED
    )
    env = _envelope()
    res = _run_join(
        binding=_binding(env),
        envelope=env,
        join_mode=FullCoreCapitalGuardJoinMode.DISABLED,
    )
    assert res.guard_allowed is None
    assert res.post_count == 0


@pytest.mark.parametrize(
    "explicit",
    [
        FullCoreCapitalGuardJoinMode.LIVE_POST,
        "LIVE_POST",
        "live_post",
    ],
)
def test_live_post_explicit_mode_always_resolves_disabled(explicit: object) -> None:
    assert (
        resolve_full_core_capital_guard_join_mode_v1(explicit_mode=explicit)
        is FullCoreCapitalGuardJoinMode.DISABLED
    )


def test_live_post_join_mode_never_executes_guard_or_reservation(tmp_path: Path) -> None:
    env = _envelope()
    state_dir = tmp_path / "atomic-live-post-block"
    state_dir.mkdir()
    for explicit in (FullCoreCapitalGuardJoinMode.LIVE_POST, "LIVE_POST"):
        res = _run_join(
            binding=_binding(env),
            envelope=env,
            join_mode=explicit,
            atomic_state_dir=state_dir,
        )
        assert res.join_mode == FullCoreCapitalGuardJoinMode.DISABLED.value
        assert res.guard_allowed is None
        assert res.guard_blocked is False
        assert res.post_count == 0
        assert res.reservation_created is False
        assert list(state_dir.glob("*.state.json")) == []


def test_live_post_env_var_resolves_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    from src.ops.full_core_live_path_composition_root_v1.full_core_pre_post_capital_guard_join_v1 import (
        JOIN_ENV_VAR,
    )

    monkeypatch.setenv(JOIN_ENV_VAR, "LIVE_POST")
    assert (
        resolve_full_core_capital_guard_join_mode_v1(explicit_mode=None)
        is FullCoreCapitalGuardJoinMode.DISABLED
    )


def test_guard_pass_does_not_imply_post_authority(tmp_path: Path) -> None:
    """OFFLINE_STUB may allow guard evaluation; POST_COUNT remains zero."""
    env = _envelope()
    res = _run_join(
        binding=_binding(env),
        envelope=env,
        atomic_state_dir=tmp_path / "atomic-pass-no-post",
    )
    assert res.guard_allowed is True
    assert res.post_count == 0


def test_natural_enter_long_allow_stub() -> None:
    env = _envelope(side="buy")
    res = _run_join(binding=_binding(env, direction="ENTER_LONG"), envelope=env)
    assert res.guard_allowed is True
    assert res.guard_blocked is False
    assert res.post_count == 0
    assert res.reservation_created is True


def test_natural_enter_short_allow_stub() -> None:
    env = _envelope(side="sell")
    b = _binding(env, direction="ENTER_SHORT", side="sell")
    res = _run_join(binding=b, envelope=env)
    assert res.guard_allowed is True


def test_no_action_skipped_by_missing_pre_external_binding() -> None:
    env = _envelope()
    b = _binding(env, pre_external=False)
    res = _run_join(binding=b, envelope=env)
    assert res.guard_blocked is True
    assert "PRE_EXTERNAL_NOT_REACHED" in res.reasons


def test_wrong_decision_identity_blocked_via_stale_margin() -> None:
    env = _envelope()
    res = _run_join(
        binding=_binding(env, decision_id="dec-other"),
        envelope=env,
        margin_evidence=_clean_margin(
            pretrade_decision_id="dec-1",
            expected_pretrade_decision_id="dec-other",
        ),
    )
    assert res.guard_blocked is True
    assert "STALE_MARGIN_EVIDENCE_PRETRADE_MISMATCH" in res.reasons


@pytest.mark.parametrize(
    "mutator,reason_fragment",
    [
        (lambda b, e: replace(b, instrument_id="OTHER-USDT-SWAP"), "INSTRUMENT"),
        (lambda b, e: replace(b, order_side="sell"), "ORDER_SIDE"),
        (lambda b, e: replace(b, final_quantity="2"), "QUANTITY"),
        (lambda b, e: replace(b, venue_plan_digest="wrong"), "VENUE_PLAN"),
        (lambda b, e: replace(b, envelope_digest="wrong"), "ENVELOPE_DIGEST"),
        (lambda b, e: replace(b, account_identity="other"), "ACCOUNT"),
        (lambda b, e: replace(b, environment="LIVE"), "LIVE"),
    ],
)
def test_binding_mismatch_blocks(mutator, reason_fragment) -> None:
    env = _envelope()
    base = _binding(env)
    b = mutator(base, env)
    res = _run_join(
        binding=b,
        envelope=env,
        account_evidence_scope=base.account_identity,
        authoritative_environment=base.environment,
        authoritative_venue_plan_digest=base.venue_plan_digest,
    )
    assert res.guard_blocked is True
    if reason_fragment:
        assert any(reason_fragment in r for r in res.reasons)


def test_canary_owner_go_forbidden() -> None:
    env = _envelope()
    res = _run_join(binding=_binding(env, owner_go=OWNER_GO_EXECUTE), envelope=env)
    assert "CANARY_OWNER_GO_FORBIDDEN" in res.reasons


def test_missing_ratified_caps_block() -> None:
    env = _envelope()
    cfg = offline_proof_full_core_guard_config_v1()
    res = _run_join(
        binding=_binding(env, cfg_digest=cfg.config_digest),
        envelope=env,
        guard_config=cfg,
    )
    assert res.guard_blocked is True
    assert any("UNRATIFIED" in r for r in res.reasons)


def test_zero_new_orders_cap_blocks() -> None:
    env = _envelope()
    cfg = replace(ratified_offline_full_core_guard_config_v1(), max_new_orders=0)
    res = _run_join(
        binding=_binding(env, cfg_digest=cfg.config_digest),
        envelope=env,
        guard_config=cfg,
    )
    assert any("MAX_NEW_ORDERS_ZERO" in r for r in res.reasons)


def test_excess_notional_blocks() -> None:
    env = _envelope(price="1000", qty="10")
    cfg = replace(
        ratified_offline_full_core_guard_config_v1(),
        max_single_order_notional=Decimal("100"),
    )
    res = _run_join(
        binding=_binding(env, price="1000", qty="10", cfg_digest=cfg.config_digest),
        envelope=env,
        guard_config=cfg,
    )
    assert any("NOTIONAL" in r for r in res.reasons)


def test_missing_imr_blocks() -> None:
    env = _envelope()
    res = _run_join(
        binding=_binding(env),
        envelope=env,
        margin_evidence=_clean_margin(imr_rate=None),
    )
    assert "MISSING_IMR_EVIDENCE" in res.reasons


def test_pending_unknown_order_blocks() -> None:
    env = _envelope()
    res = _run_join(
        binding=_binding(env),
        envelope=env,
        exposure_evidence=_clean_exposure(unknown_submit_active=True),
    )
    assert "UNKNOWN_SUBMIT_ACTIVE" in res.reasons


def test_owner_go_replay_blocks_second_reservation(tmp_path: Path) -> None:
    env = _envelope()
    state_dir = tmp_path / "atomic"
    b = _binding(env)
    first = _run_join(binding=b, envelope=env, atomic_state_dir=state_dir)
    assert first.reservation_created is True
    second = _run_join(binding=b, envelope=env, atomic_state_dir=state_dir)
    assert second.guard_blocked is True


def _reserve_worker(state_dir: str, binding_dict: dict[str, str]) -> None:
    allowed = {f.name for f in FullCoreAuthorizationBindingV1.__dataclass_fields__.values()}
    binding = FullCoreAuthorizationBindingV1(
        **{k: v for k, v in binding_dict.items() if k in allowed}
    )
    full_core_atomic_reserve_owner_go_authorization_v1(
        state_dir=Path(state_dir),
        binding=binding,
    )


def test_concurrent_duplicate_join_at_most_one_reservation(tmp_path: Path) -> None:
    env = _envelope()
    b = _binding(env)
    auth = FullCoreAuthorizationBindingV1(
        owner_go=b.owner_go,
        origin_main_sha=b.origin_main_sha,
        account_scope=b.account_identity,
        environment=b.environment,
        execution_mode=b.execution_mode,
        canonical_decision_id=b.canonical_decision_id,
        instrument_id=b.instrument_id,
        native_id=b.native_id,
        selected_direction=b.selected_direction,
        order_side=b.order_side,
        final_quantity=b.final_quantity,
        order_type=b.order_type,
        order_price=b.order_price,
        venue_plan_digest=b.venue_plan_digest,
        envelope_digest=b.envelope_digest,
        guard_config_digest=b.guard_config_digest,
        session_id="sess-mp",
        clordid=b.clordid,
    )
    state_dir = tmp_path / "mp"
    state_dir.mkdir()
    binding_dict = auth.to_dict()
    procs = [
        mp.Process(target=_reserve_worker, args=(str(state_dir), binding_dict)) for _ in range(4)
    ]
    for p in procs:
        p.start()
    for p in procs:
        p.join(timeout=30)
    rows = list(state_dir.glob("*.state.json"))
    assert len(rows) == 1


def test_crash_at_submit_boundary_unknown(tmp_path: Path) -> None:
    env = _envelope()
    res = _run_join(
        binding=_binding(env),
        envelope=env,
        atomic_state_dir=tmp_path / "atomic",
        simulate_submit_boundary_crash=True,
    )
    assert "SUBMIT_BOUNDARY_UNKNOWN_HALTED" in res.reasons
    assert res.post_count == 0


def test_partial_fill_reconciliation_stub() -> None:
    adj = adjudicate_full_core_entry_recovery_stub_v1(
        evidence=FullCoreReconciliationEvidenceV1(
            account_scope="a",
            environment="OFFLINE_STUB",
            instrument_id=INST,
            clordid="c1",
            evidence_fresh=True,
            reconciliation_complete=False,
            order_exists=True,
            order_state="partially_filled",
            partial_fill_qty="0.5",
            position_exposure=None,
            pending_unknown_submission=False,
        ),
        stub_orders={"data": [{"clOrdId": "c1", "state": "partially_filled", "accFillSz": "0.5"}]},
    )
    assert adj.outcome == OUTCOME_PARTIAL_FILL


def test_order_not_found_unresolved() -> None:
    adj = adjudicate_full_core_entry_recovery_stub_v1(
        evidence=FullCoreReconciliationEvidenceV1(
            account_scope="a",
            environment="OFFLINE_STUB",
            instrument_id=INST,
            clordid="missing",
            evidence_fresh=True,
            reconciliation_complete=False,
            order_exists=False,
            order_state=None,
            partial_fill_qty=None,
            position_exposure=None,
            pending_unknown_submission=False,
        ),
    )
    assert adj.outcome == OUTCOME_ORDER_NOT_FOUND
    assert adj.reconciliation_complete is False


def test_ghv_truthful_trace_stages() -> None:
    env = _envelope()
    res = _run_join(binding=_binding(env), envelope=env)
    stages = [r.get("stage") for r in res.ghv_bundle.get("ghv_full_core_capital_guard_stages", [])]
    assert STAGE_PRE_EXTERNAL_REACHED in stages
    assert STAGE_CAPITAL_GUARD_DECISION in stages


def test_observe_only_no_reservation(tmp_path: Path) -> None:
    env = _envelope()
    res = _run_join(
        binding=_binding(env),
        envelope=env,
        join_mode=FullCoreCapitalGuardJoinMode.OBSERVE_ONLY,
        atomic_state_dir=tmp_path / "atomic",
    )
    assert res.guard_allowed is True
    assert res.reservation_created is False


def test_atomic_payload_change_blocks_replay(tmp_path: Path) -> None:
    env = _envelope()
    state_dir = tmp_path / "atomic"
    b1 = _binding(env, qty="1")
    _run_join(binding=b1, envelope=env, atomic_state_dir=state_dir)
    env2 = _envelope(qty="2")
    b2 = _binding(env2, qty="2")
    with pytest.raises(FullCoreAtomicOneShotError):
        auth = FullCoreAuthorizationBindingV1(
            owner_go=b2.owner_go,
            origin_main_sha=b2.origin_main_sha,
            account_scope=b2.account_identity,
            environment=b2.environment,
            execution_mode=b2.execution_mode,
            canonical_decision_id=b2.canonical_decision_id,
            instrument_id=b2.instrument_id,
            native_id=b2.native_id,
            selected_direction=b2.selected_direction,
            order_side=b2.order_side,
            final_quantity=b2.final_quantity,
            order_type=b2.order_type,
            order_price=b2.order_price,
            venue_plan_digest=b2.venue_plan_digest,
            envelope_digest=b2.envelope_digest,
            guard_config_digest=b2.guard_config_digest,
            session_id="sess-2",
            clordid=b2.clordid,
        )
        assert_full_core_entry_authorization_available_v1(state_dir=state_dir, binding=auth)
