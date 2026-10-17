"""Adversarial offline matrix for B5 (kill switch), B5-RR (risk reduction), B6 (global replay).

Fake/mock transport only. Real sockets are forbidden. Every test asserts the exact
fake-POST count; any unexpected increase fails the test.
"""

from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import time
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest

from src.ops.full_core_live_path_composition_root_v1 import (
    current_productive_global_venue_effect_authority_ledger_v1 as ledger_mod,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_global_venue_effect_authority_ledger_v1 import (
    ACCOUNT_SCOPE_K1,
    CLASS_CLAIMED_ORPHAN,
    CLASS_CLAIMED_PROVEN_NOT_SENT,
    DETAIL_PROVEN_NOT_SENT,
    ENVIRONMENT_LIVE_EEA,
    KIND_CLIENT_ORDER_ID,
    KIND_OWNER_AUTHORIZATION,
    RISK_CLASS_NEW_RISK,
    STATE_ABORTED_BEFORE_TRANSPORT,
    STATE_CLAIMED,
    STATE_RECONCILED,
    STATE_SENT_INITIATED,
    STATE_UNKNOWN_OUTCOME,
    GlobalVenueEffectAuthorityLedgerV1,
    GlobalVenueEffectIdentityV1,
    GlobalVenueEffectLedgerError,
    GlobalVenueEffectReplayDeniedError,
    resolve_canonical_global_ledger_root_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_one_shot_fresh_envelope_permit_mint_durable_consume_and_post_join_v1 import (
    CurrentProductiveOneShotFreshEnvelopeJoinError,
    OneShotJoinProbeV1,
    attempt_current_productive_one_shot_fresh_envelope_permit_mint_durable_consume_and_post_join_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_post_path_kill_switch_gate_v1 import (
    DENY_ACTIVE_NOT_CANONICAL_WRITER,
    DENY_BLOCKED,
    DENY_ENV_OVERRIDE_REJECTED,
    DENY_EVIDENCE_STALE,
    DENY_SECONDARY_SIGNAL,
    PostPathKillSwitchDecisionV1,
    evaluate_post_path_kill_switch_v1,
    read_post_path_kill_switch_evidence_v1,
    resolve_post_path_kill_switch_state_path_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_risk_reduction_venue_proof_v1 import (
    RiskReductionNotProvenError,
    prove_risk_reduction_from_venue_evidence_v1,
)
from src.ops.full_core_live_path_composition_root_v1.external_effect_permit_durable_consume_v1 import (
    load_external_effect_durable_consume_v1,
)
from src.ops.full_core_live_path_composition_root_v1.external_effect_permit_v1 import (
    FullCoreExternalEffectPermitError,
    issue_external_effect_permit_v1,
)
from src.ops.full_core_live_path_composition_root_v1.final_order_envelope_v1 import (
    bind_final_order_envelope_from_venue_plan_v1,
)
from src.ops.full_core_live_path_composition_root_v1.models_v1 import VenuePlanCandidateV1
from tests.ops._current_productive_post_hard_crash_harness_v1 import (
    CrashPointV1,
    expected_crash_exit_v1,
    harness_global_ledger_v1,
    spawn_hard_crash_child_v1,
)
from tests.ops._pilot_guard_enter_post_test_helpers_v1 import (
    bind_authorized_exact_object_flatten_envelope_for_tests_v1,
    establish_new_risk_one_shot_admission_seal_for_tests_v1,
)
from tests.ops._post_path_safety_fixtures_v1 import (
    KILL_SWITCH_ENV,
    TEST_BASELINE_SHA,
    activate_isolated_kill_switch_state_v1,
    claim_for_join_v1,
    isolate_kill_switch_state_root_v1,
    isolated_global_ledger_v1,
    kill_switch_evidence_from_state_v1,
    risk_reduction_proof_for_envelope_v1,
    rr_venue_payloads_v1,
    write_kill_switch_state_v1,
)
from tests.ops.test_current_productive_one_shot_fresh_envelope_permit_mint_durable_consume_and_post_join_v1 import (
    POST_OWNER_GO,
    _FakeKeychainBackend,
    _new_risk_envelope,
    _persist_post_go,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
OTHER_BASELINE_SHA = "cd" * 20


@pytest.fixture(autouse=True)
def _forbid_real_sockets(monkeypatch: pytest.MonkeyPatch) -> None:
    def _boom(*_args: Any, **_kwargs: Any) -> None:
        raise AssertionError("NETWORK_FORBIDDEN")

    monkeypatch.setattr(socket, "create_connection", _boom)
    monkeypatch.setattr(socket.socket, "connect", _boom)


class _CountingTimeoutOpener:
    """Fake venue socket: every ``open`` is one fake POST; outcome is unknown (timeout)."""

    def __init__(self) -> None:
        self.requests: list[Any] = []

    def open(self, req: Any, timeout: float = 0) -> Any:
        del timeout
        self.requests.append(req)
        raise TimeoutError("bounded-test-timeout")


def _ks(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, state: str = "ACTIVE") -> Path:
    return activate_isolated_kill_switch_state_v1(monkeypatch, tmp_path, state=state)


def _flatten_envelope(clordid: str = "pt-b5-flatten-v1") -> Any:
    return bind_authorized_exact_object_flatten_envelope_for_tests_v1(clordid=clordid)


def _long_short_close_long_envelope() -> Any:
    plan = VenuePlanCandidateV1(
        instrument_id="okx_eea:linear_perpetual:0G:USDT:USDT:0g-usdt-swap",
        side="sell",
        quantity="1",
        order_type="limit",
        td_mode="cross",
        reduce_only=True,
        clordid="pt-b5rr-long-short-v1",
        venue_native_payload={"px": "10.0", "posSide": "long"},
        quantity_source="TEST_FIXTURE_NOT_LIVE_ENVELOPE",
        side_source="TEST_FIXTURE_NOT_LIVE_ENVELOPE",
        instrument_source="DH_CAP24_BOUND_INSTRUMENT_ID",
        path_kind="FULL_CORE_CURRENT_PRODUCTIVE",
    )
    return bind_final_order_envelope_from_venue_plan_v1(
        plan,
        admission_ref="TEST_ADMISSION_REF",
        provenance_ref="TEST_PROVENANCE_REF",
        creation_epoch="2026-10-17T00:00:00Z",
    )


def _join(
    *,
    store_root: Path,
    envelope: Any,
    ledger: GlobalVenueEffectAuthorityLedgerV1,
    opener: _CountingTimeoutOpener,
    probe: OneShotJoinProbeV1 | None = None,
    claim: Any = None,
    risk_reduction_proof: Any = None,
    backend: Any = None,
    baseline: str = TEST_BASELINE_SHA,
) -> Any:
    _persist_post_go(store_root)
    if envelope.reduce_only is not True:
        establish_new_risk_one_shot_admission_seal_for_tests_v1(
            store_root=store_root, envelope=envelope
        )
    use_claim = (
        claim
        if claim is not None
        else claim_for_join_v1(ledger, envelope, baseline_origin_main_sha=baseline)
    )
    return attempt_current_productive_one_shot_fresh_envelope_permit_mint_durable_consume_and_post_join_v1(
        envelope=envelope,
        post_owner_go=POST_OWNER_GO,
        store_root=store_root,
        k1_backend=backend if backend is not None else _FakeKeychainBackend(),
        opener_factory=lambda: opener,
        probe=probe if probe is not None else OneShotJoinProbeV1(),
        global_authority_ledger=ledger,
        global_claim=use_claim,
        risk_reduction_proof=risk_reduction_proof,
    )


def _identity(
    *,
    permit_id: str = "eep-test-1",
    envelope_digest: str = "a" * 64,
    client_order_id: str = "pt-b6-cl-1",
    baseline: str = TEST_BASELINE_SHA,
    risk_class: str = RISK_CLASS_NEW_RISK,
) -> GlobalVenueEffectIdentityV1:
    return GlobalVenueEffectIdentityV1(
        owner_go_token=POST_OWNER_GO,
        account_scope=ACCOUNT_SCOPE_K1,
        environment=ENVIRONMENT_LIVE_EEA,
        permit_id=permit_id,
        envelope_id=f"env-{permit_id}",
        envelope_digest=envelope_digest,
        client_order_id=client_order_id,
        risk_class=risk_class,
        baseline_origin_main_sha=baseline,
    )


# --------------------------------------------------------------------------- B5

_WRITER_ACTIVE = "WRITER:ACTIVE"
_WRITER_KILLED = "WRITER:KILLED"


@pytest.mark.parametrize(
    "raw,expect_admit",
    [
        (_WRITER_ACTIVE, True),
        (_WRITER_KILLED, False),
        (json.dumps({"state": "ACTIVE"}), False),
        (json.dumps({"state": "ACTIVE", "version": "1.0", "saved_at": "not-a-time"}), False),
        (json.dumps({"state": "KILLED"}), False),
        (json.dumps({"state": "RECOVERING"}), False),
        (json.dumps({"state": "DISABLED"}), False),
        (None, False),
        ("{not json", False),
        (json.dumps({"state": "ACTIVE", "status": "KILLED"}), False),
        (json.dumps({"state": "ACTIVE", "kill_switch": True}), False),
        (json.dumps({"state": "BOGUS"}), False),
    ],
    ids=[
        "writer_active",
        "writer_killed",
        "historical_active_without_writer_schema",
        "active_with_invalid_saved_at",
        "killed",
        "recovering",
        "disabled",
        "missing",
        "unreadable",
        "contradictory_alias",
        "contradictory_flag",
        "unknown_state",
    ],
)
def test_b5_join_kill_switch_state_matrix_new_risk(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, raw: str | None, expect_admit: bool
) -> None:
    state_path = isolate_kill_switch_state_root_v1(monkeypatch, tmp_path / "ks")
    if raw in (_WRITER_ACTIVE, _WRITER_KILLED):
        write_kill_switch_state_v1(state_path, state=raw.split(":", 1)[1])
    elif raw is not None:
        write_kill_switch_state_v1(state_path, raw=raw)
    opener = _CountingTimeoutOpener()
    probe = OneShotJoinProbeV1()
    ledger = isolated_global_ledger_v1(tmp_path)
    if expect_admit:
        join = _join(
            store_root=tmp_path / "store",
            envelope=_new_risk_envelope(),
            ledger=ledger,
            opener=opener,
            probe=probe,
        )
        assert join.unknown_outcome is True
        assert len(opener.requests) == 1
        return
    with pytest.raises(
        CurrentProductiveOneShotFreshEnvelopeJoinError, match="^KILL_SWITCH_GATE_DENIED:"
    ):
        _join(
            store_root=tmp_path / "store",
            envelope=_new_risk_envelope(),
            ledger=ledger,
            opener=opener,
            probe=probe,
        )
    assert opener.requests == []
    assert "KILL_SWITCH_ADMITTED_PRE_MINT" not in probe.events
    assert probe.permit_minted is False
    assert probe.http_post_attempts == 0
    assert (
        load_external_effect_durable_consume_v1(store_root=tmp_path / "store")["durable_consumed"]
        is not True
    )


def test_b5_kill_switch_flips_between_permit_and_transport_blocks_post(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    state_path = _ks(monkeypatch, tmp_path, "ACTIVE")

    class _FlipOnK1Backend(_FakeKeychainBackend):
        def copy_matching_generic_password_value_data_v1(self, **kwargs: Any) -> bytes:
            write_kill_switch_state_v1(state_path, state="KILLED")
            return super().copy_matching_generic_password_value_data_v1(**kwargs)

    opener = _CountingTimeoutOpener()
    probe = OneShotJoinProbeV1()
    ledger = isolated_global_ledger_v1(tmp_path)
    claim = claim_for_join_v1(ledger, _new_risk_envelope())
    with pytest.raises(
        CurrentProductiveOneShotFreshEnvelopeJoinError, match="PRE_SEND_GATE_DENIED"
    ):
        _join(
            store_root=tmp_path / "store",
            envelope=_new_risk_envelope(),
            ledger=ledger,
            opener=opener,
            probe=probe,
            claim=claim,
            backend=_FlipOnK1Backend(),
        )
    assert opener.requests == []
    assert probe.http_post_attempts == 0
    assert "KILL_SWITCH_ADMITTED_PRE_MINT" in probe.events
    assert "DURABLE_ABORTED_BEFORE_TRANSPORT" in probe.events
    assert probe.events[-1] == f"GLOBAL_CLAIM_SETTLED:{STATE_ABORTED_BEFORE_TRANSPORT}"
    assert ledger.load_claim_v1(claim.claim_id)["state"] == STATE_ABORTED_BEFORE_TRANSPORT
    record = load_external_effect_durable_consume_v1(store_root=tmp_path / "store")["record"]
    assert record["durable_state"] == STATE_ABORTED_BEFORE_TRANSPORT
    assert record["retry_allowed"] is False
    write_kill_switch_state_v1(state_path, state="ACTIVE")
    with pytest.raises(GlobalVenueEffectReplayDeniedError):
        claim_for_join_v1(ledger, _new_risk_envelope())
    assert opener.requests == []


def test_b5_missing_pre_send_gate_wiring_blocks_socket(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from src.ops.full_core_live_path_composition_root_v1 import (
        full_core_productive_http_post_transport_v1 as http_mod,
    )

    _ks(monkeypatch, tmp_path)
    original_init = http_mod.FullCoreProductiveHttpTradeOrderTransportV1.__init__

    def _init_without_gate(self: Any, **kwargs: Any) -> None:
        kwargs["pre_send_safety_gate"] = None
        original_init(self, **kwargs)

    monkeypatch.setattr(
        http_mod.FullCoreProductiveHttpTradeOrderTransportV1, "__init__", _init_without_gate
    )
    opener = _CountingTimeoutOpener()
    with pytest.raises(
        CurrentProductiveOneShotFreshEnvelopeJoinError, match="PRE_SEND_SAFETY_GATE_REQUIRED"
    ):
        _join(
            store_root=tmp_path / "store",
            envelope=_new_risk_envelope(),
            ledger=isolated_global_ledger_v1(tmp_path),
            opener=opener,
        )
    assert opener.requests == []


def test_b5_state_path_independent_of_cwd_and_cwd_file_only_denies(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv(KILL_SWITCH_ENV, raising=False)
    monkeypatch.delenv("PEAKTRADE_KILL_SWITCH_STATE_PATH", raising=False)
    canonical_before = resolve_post_path_kill_switch_state_path_v1()
    elsewhere = tmp_path / "elsewhere"
    write_kill_switch_state_v1(elsewhere / "data" / "kill_switch" / "state.json", state="KILLED")
    monkeypatch.chdir(elsewhere)
    assert resolve_post_path_kill_switch_state_path_v1() == canonical_before
    assert canonical_before.is_absolute()
    assert str(canonical_before).startswith(str(REPO_ROOT))

    active = _ks(monkeypatch, tmp_path / "primary", "ACTIVE")
    evidence = read_post_path_kill_switch_evidence_v1()
    assert evidence.state_path == str(active)
    assert str((elsewhere / "data" / "kill_switch" / "state.json").resolve()) in (
        evidence.secondary_deny_paths
    )
    admission = evaluate_post_path_kill_switch_v1(
        evidence=evidence, envelope=_new_risk_envelope(), risk_reduction_proof=None
    )
    assert admission.decision is PostPathKillSwitchDecisionV1.DENY
    assert admission.reason_codes in (
        (DENY_SECONDARY_SIGNAL,),
        ("KILL_SWITCH_EVIDENCE_NOT_TRUSTED:CONTRADICTORY_BLOCKED",),
    )

    write_kill_switch_state_v1(elsewhere / "data" / "kill_switch" / "state.json", state="ACTIVE")
    active.unlink()
    missing = read_post_path_kill_switch_evidence_v1()
    assert missing.evidence_status == "MISSING"
    admission = evaluate_post_path_kill_switch_v1(
        evidence=missing, envelope=_new_risk_envelope(), risk_reduction_proof=None
    )
    assert admission.decision is PostPathKillSwitchDecisionV1.DENY


def test_b5_restart_reads_durable_killed_state_in_fresh_process_and_other_cwd(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    state_path = _ks(monkeypatch, tmp_path, "KILLED")
    other_cwd = tmp_path / "other_cwd"
    other_cwd.mkdir()
    code = (
        "import sys; from pathlib import Path; sys.path.insert(0, sys.argv[1]);"
        "from src.ops.gates import risk_gate;"
        "risk_gate._KILL_SWITCH_STATE_ROOT = Path(sys.argv[2]);"
        "from src.ops.full_core_live_path_composition_root_v1."
        "current_productive_post_path_kill_switch_gate_v1 import "
        "read_post_path_kill_switch_evidence_v1 as r;"
        "e = r(); print(e.evidence_status, e.state_name, e.blocked, e.state_path)"
    )
    env = {
        k: v
        for k, v in os.environ.items()
        if k not in {KILL_SWITCH_ENV, "PEAKTRADE_KILL_SWITCH_STATE_PATH", "PYTEST_CURRENT_TEST"}
    }
    completed = subprocess.run(
        [sys.executable, "-c", code, str(REPO_ROOT), str(state_path.parents[2])],
        cwd=str(other_cwd),
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    assert completed.stdout.split() == ["TRUSTED_PRESENT", "KILLED", "True", str(state_path)]


def test_b5_stale_or_forged_kill_switch_evidence_denied(tmp_path: Path) -> None:
    envelope = _new_risk_envelope()
    evidence = kill_switch_evidence_from_state_v1(tmp_path, state="ACTIVE")
    stale = evaluate_post_path_kill_switch_v1(
        evidence=evidence,
        envelope=envelope,
        risk_reduction_proof=None,
        now_epoch_s=evidence.read_at_epoch_s + 60.0,
    )
    assert stale.decision is PostPathKillSwitchDecisionV1.DENY
    assert DENY_EVIDENCE_STALE in stale.reason_codes
    forged = replace(evidence, contract_id="FORGED")
    with pytest.raises(FullCoreExternalEffectPermitError, match="KILL_SWITCH_EVIDENCE_NOT_TRUSTED"):
        issue_external_effect_permit_v1(
            envelope,
            authority_ref=POST_OWNER_GO,
            kill_switch_evidence=forged,
            risk_reduction_proof=None,
        )
    with pytest.raises(FullCoreExternalEffectPermitError, match="KILL_SWITCH_EVIDENCE_TYPE"):
        issue_external_effect_permit_v1(
            envelope,
            authority_ref=POST_OWNER_GO,
            kill_switch_evidence={"evidence_status": "TRUSTED_PRESENT"},  # type: ignore[arg-type]
            risk_reduction_proof=None,
        )


def test_b5_forged_trusted_permit_evidence_cannot_override_durable_killed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _ks(monkeypatch, tmp_path, "KILLED")
    opener = _CountingTimeoutOpener()
    probe = OneShotJoinProbeV1()
    with pytest.raises(CurrentProductiveOneShotFreshEnvelopeJoinError, match=DENY_BLOCKED):
        _join(
            store_root=tmp_path / "store",
            envelope=_new_risk_envelope(),
            ledger=isolated_global_ledger_v1(tmp_path),
            opener=opener,
            probe=probe,
        )
    assert probe.permit_minted is False
    assert opener.requests == []


def test_b5_required_parameters_cannot_be_omitted(tmp_path: Path) -> None:
    envelope = _new_risk_envelope()
    with pytest.raises(TypeError):
        issue_external_effect_permit_v1(envelope, authority_ref=POST_OWNER_GO)  # type: ignore[call-arg]
    with pytest.raises(TypeError):
        attempt_current_productive_one_shot_fresh_envelope_permit_mint_durable_consume_and_post_join_v1(  # type: ignore[call-arg]
            envelope=envelope,
            post_owner_go=POST_OWNER_GO,
            store_root=tmp_path,
        )
    with pytest.raises(CurrentProductiveOneShotFreshEnvelopeJoinError, match="LEDGER_REQUIRED"):
        _persist_post_go(tmp_path)
        establish_new_risk_one_shot_admission_seal_for_tests_v1(
            store_root=tmp_path, envelope=envelope
        )
        attempt_current_productive_one_shot_fresh_envelope_permit_mint_durable_consume_and_post_join_v1(
            envelope=envelope,
            post_owner_go=POST_OWNER_GO,
            store_root=tmp_path,
            k1_backend=_FakeKeychainBackend(),
            opener_factory=lambda: _CountingTimeoutOpener(),
            global_authority_ledger=None,  # type: ignore[arg-type]
            global_claim=None,  # type: ignore[arg-type]
        )


# ------------------------------------------------------------------------ B5-RR


def _prove(envelope: Any, **kw: Any) -> Any:
    config, positions, pending = rr_venue_payloads_v1(envelope, **kw)
    return prove_risk_reduction_from_venue_evidence_v1(
        envelope=envelope,
        config_payload=config,
        positions_payload=positions,
        pending_orders_payload=pending,
        observed_at_epoch_s=time.time(),
    )


@pytest.mark.parametrize(
    "kwargs,reason",
    [
        ({"pos": "0"}, "NO_OPEN_POSITION"),
        ({"pos": "-1"}, "ORDER_SIDE_DOES_NOT_REDUCE_POSITION"),
        ({"pos": "0.5"}, "ORDER_QTY_EXCEEDS_POSITION"),
        ({"pos_mode": "long_short_mode", "pos": "1", "pos_side": "long"}, "POS_SIDE_REQUIRED"),
        ({"pos_mode": "portfolio_mode"}, "POSITION_MODE_UNSUPPORTED"),
        ({"pos_side": "long"}, "POS_SIDE_CONTRADICTS_NET_MODE"),
        (
            {"pending_rows": [{"instId": "x", "clOrdId": "other"}]},
            "PENDING_ORDER_INSTRUMENT_IDENTITY_AMBIGUOUS",
        ),
        ({"uid": ""}, "ACCOUNT_SCOPE_UNPROVEN"),
    ],
    ids=[
        "no_position",
        "wrong_direction",
        "qty_exceeds_position",
        "wrong_pos_mode",
        "unsupported_pos_mode",
        "contradictory_pos_side",
        "foreign_pending_order",
        "account_unproven",
    ],
)
def test_b5rr_net_mode_counter_evidence_not_proven(kwargs: dict[str, Any], reason: str) -> None:
    with pytest.raises(RiskReductionNotProvenError, match=reason):
        _prove(_flatten_envelope(), **kwargs)


def test_b5rr_concurrent_open_order_on_instrument_not_proven() -> None:
    envelope = _flatten_envelope()
    with pytest.raises(RiskReductionNotProvenError, match="CONFLICTING_OPEN_ORDERS"):
        _prove(
            envelope,
            pending_rows=[{"instId": envelope.instrument_id, "clOrdId": "resting-1"}],
        )


def test_b5rr_long_short_mode_semantics() -> None:
    envelope = _long_short_close_long_envelope()
    proof = _prove(envelope, pos_mode="long_short_mode", pos="1", pos_side="long")
    assert proof.pos_mode == "long_short_mode"
    assert proof.position_side == "long"
    with pytest.raises(RiskReductionNotProvenError, match="NO_OPEN_POSITION_FOR_POS_SIDE"):
        _prove(envelope, pos_mode="long_short_mode", pos="1", pos_side="short")
    with pytest.raises(RiskReductionNotProvenError, match="HEDGED_POSITION_REDUCTION_NOT_PROVEN"):
        _prove(
            envelope,
            pos_mode="long_short_mode",
            pos="1",
            pos_side="long",
            extra_position_rows=[
                {
                    "instId": envelope.instrument_id,
                    "pos": "1",
                    "posSide": "short",
                    "mgnMode": envelope.td_mode,
                }
            ],
        )
    with pytest.raises(RiskReductionNotProvenError, match="POS_SIDE_CONTRADICTS_NET_MODE"):
        _prove(envelope, pos_mode="net_mode", pos="1", pos_side="net")


def test_b5rr_reduce_only_label_without_proof_never_posts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _ks(monkeypatch, tmp_path)
    opener = _CountingTimeoutOpener()
    probe = OneShotJoinProbeV1()
    with pytest.raises(
        CurrentProductiveOneShotFreshEnvelopeJoinError, match="RISK_REDUCTION_NOT_PROVEN"
    ):
        _join(
            store_root=tmp_path / "store",
            envelope=_flatten_envelope(),
            ledger=isolated_global_ledger_v1(tmp_path),
            opener=opener,
            probe=probe,
            risk_reduction_proof=None,
        )
    assert probe.permit_minted is False
    assert opener.requests == []


def test_b5rr_stale_foreign_or_tampered_proof_never_posts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _ks(monkeypatch, tmp_path)
    envelope = _flatten_envelope()
    stale = risk_reduction_proof_for_envelope_v1(envelope, observed_at_epoch_s=time.time() - 120)
    foreign = risk_reduction_proof_for_envelope_v1(_flatten_envelope(clordid="pt-b5rr-other"))
    tampered = replace(risk_reduction_proof_for_envelope_v1(envelope), position_qty_abs="1000")
    opener = _CountingTimeoutOpener()
    for index, (proof, reason) in enumerate(
        (
            (stale, "VENUE_EVIDENCE_STALE"),
            (foreign, "PROOF_ENVELOPE_ID_MISMATCH"),
            (tampered, "PROOF_DIGEST_MISMATCH"),
        )
    ):
        with pytest.raises(CurrentProductiveOneShotFreshEnvelopeJoinError, match=reason):
            _join(
                store_root=tmp_path / f"store{index}",
                envelope=envelope,
                ledger=isolated_global_ledger_v1(tmp_path / f"ledger{index}"),
                opener=opener,
                risk_reduction_proof=proof,
            )
    assert opener.requests == []


@pytest.mark.parametrize("state", ["KILLED", "RECOVERING"])
def test_b5rr_proven_reduction_admitted_under_blocking_kill_switch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, state: str
) -> None:
    _ks(monkeypatch, tmp_path, state)
    envelope = _flatten_envelope()
    opener = _CountingTimeoutOpener()
    probe = OneShotJoinProbeV1()
    ledger = isolated_global_ledger_v1(tmp_path)
    join = _join(
        store_root=tmp_path / "store",
        envelope=envelope,
        ledger=ledger,
        opener=opener,
        probe=probe,
        risk_reduction_proof=risk_reduction_proof_for_envelope_v1(envelope),
    )
    assert join.unknown_outcome is True
    assert len(opener.requests) == 1
    new_risk_opener = _CountingTimeoutOpener()
    with pytest.raises(CurrentProductiveOneShotFreshEnvelopeJoinError, match=DENY_BLOCKED):
        _join(
            store_root=tmp_path / "store_new_risk",
            envelope=_new_risk_envelope(),
            ledger=isolated_global_ledger_v1(tmp_path / "ledger_new_risk"),
            opener=new_risk_opener,
        )
    assert new_risk_opener.requests == []


def test_b5rr_proof_ages_out_between_mint_and_transport(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from src.ops.full_core_live_path_composition_root_v1 import (
        current_productive_risk_reduction_venue_proof_v1 as rr_mod,
    )

    _ks(monkeypatch, tmp_path, "KILLED")
    envelope = _flatten_envelope()
    proof = risk_reduction_proof_for_envelope_v1(envelope)
    real_time = time.time

    class _AgingBackend(_FakeKeychainBackend):
        def copy_matching_generic_password_value_data_v1(self, **kwargs: Any) -> bytes:
            monkeypatch.setattr(rr_mod.time, "time", lambda: real_time() + 600.0)
            return super().copy_matching_generic_password_value_data_v1(**kwargs)

    opener = _CountingTimeoutOpener()
    with pytest.raises(
        CurrentProductiveOneShotFreshEnvelopeJoinError, match="PRE_SEND_GATE_DENIED"
    ):
        _join(
            store_root=tmp_path / "store",
            envelope=envelope,
            ledger=isolated_global_ledger_v1(tmp_path),
            opener=opener,
            risk_reduction_proof=proof,
            backend=_AgingBackend(),
        )
    assert opener.requests == []


# --------------------------------------------------------------------------- B6


def test_b6_two_store_roots_identical_envelope_single_fake_post(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _ks(monkeypatch, tmp_path)
    ledger = isolated_global_ledger_v1(tmp_path)
    opener = _CountingTimeoutOpener()
    _join(
        store_root=tmp_path / "root_a", envelope=_new_risk_envelope(), ledger=ledger, opener=opener
    )
    assert len(opener.requests) == 1
    with pytest.raises(GlobalVenueEffectReplayDeniedError, match="GLOBAL_REPLAY_DENIED"):
        _join(
            store_root=tmp_path / "root_b",
            envelope=_new_risk_envelope(),
            ledger=GlobalVenueEffectAuthorityLedgerV1(root=ledger.namespace.parents[2]),
            opener=opener,
        )
    assert len(opener.requests) == 1
    assert not (tmp_path / "root_b" / "full_core_external_effect_permit_consume_v1.json").exists()


def test_b6_two_store_roots_identical_owner_go_different_envelope_denied(tmp_path: Path) -> None:
    ledger = isolated_global_ledger_v1(tmp_path)
    ledger.claim_v1(_identity())
    with pytest.raises(
        GlobalVenueEffectReplayDeniedError, match=f"GLOBAL_REPLAY_DENIED:{KIND_OWNER_AUTHORIZATION}"
    ):
        ledger.claim_v1(
            _identity(
                permit_id="eep-test-2", envelope_digest="b" * 64, client_order_id="pt-b6-cl-2"
            )
        )


def test_b6_identical_clordid_with_changed_envelope_denied(tmp_path: Path) -> None:
    ledger = isolated_global_ledger_v1(tmp_path)
    ledger.claim_v1(_identity())
    with pytest.raises(
        GlobalVenueEffectReplayDeniedError, match=f"GLOBAL_REPLAY_DENIED:{KIND_CLIENT_ORDER_ID}"
    ):
        ledger.claim_v1(
            _identity(permit_id="eep-test-2", envelope_digest="b" * 64, baseline=OTHER_BASELINE_SHA)
        )


_PARALLEL_CLAIM_CODE = r"""
import sys, time
from pathlib import Path
sys.path.insert(0, sys.argv[1])
from src.ops.full_core_live_path_composition_root_v1.current_productive_global_venue_effect_authority_ledger_v1 import (
    ACCOUNT_SCOPE_K1, ENVIRONMENT_LIVE_EEA, GlobalVenueEffectAuthorityLedgerV1,
    GlobalVenueEffectIdentityV1, GlobalVenueEffectLedgerError,
)
root, barrier, index, distinct = Path(sys.argv[2]), Path(sys.argv[3]), sys.argv[4], sys.argv[5] == "1"
suffix = index if distinct else "same"
identity = GlobalVenueEffectIdentityV1(
    owner_go_token="OWNER_GO_PARALLEL_TEST",
    account_scope=ACCOUNT_SCOPE_K1,
    environment=ENVIRONMENT_LIVE_EEA,
    permit_id="eep-par-" + suffix,
    envelope_id="env-par-" + suffix,
    envelope_digest=(("%064x" % (int(index) + 1)) if distinct else "e" * 64),
    client_order_id="pt-par-" + suffix,
    risk_class="NEW_RISK_ENTER",
    baseline_origin_main_sha=(("%040x" % (int(index) + 1)) if distinct else "ab" * 20),
)
ledger = GlobalVenueEffectAuthorityLedgerV1(root=root)
deadline = time.time() + 30
while not barrier.exists() and time.time() < deadline:
    time.sleep(0.001)
try:
    ledger.claim_v1(identity)
    print("CLAIMED", flush=True)
except GlobalVenueEffectLedgerError as exc:
    print("DENIED:" + str(exc), flush=True)
sys.stdin.read()
"""


@pytest.mark.parametrize("distinct", [False, True], ids=["same_identity", "distinct_new_risk"])
def test_b6_parallel_processes_exactly_one_claim(tmp_path: Path, distinct: bool) -> None:
    root = tmp_path / "parallel_ledger"
    barrier = tmp_path / "barrier"
    procs = [
        subprocess.Popen(
            [
                sys.executable,
                "-c",
                _PARALLEL_CLAIM_CODE,
                str(REPO_ROOT),
                str(root),
                str(barrier),
                str(index),
                "1" if distinct else "0",
            ],
            cwd=str(tmp_path),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        for index in range(8)
    ]
    time.sleep(1.5)
    barrier.write_text("go", encoding="utf-8")
    # Claimers stay alive until all have answered: a dead claimer's unsent
    # CLAIMED record is proven unsent and may legitimately be settled.
    outputs = [proc.stdout.readline().strip() for proc in procs]
    for proc in procs:
        _, err = proc.communicate(input="", timeout=60)
        assert proc.returncode == 0, err
    assert outputs.count("CLAIMED") == 1, outputs
    denied = [o for o in outputs if o != "CLAIMED"]
    expected = (
        "DENIED:GLOBAL_UNRESOLVED_VENUE_EFFECT_BLOCKS_NEW_RISK"
        if distinct
        else "DENIED:GLOBAL_REPLAY_DENIED:"
    )
    assert all(o.startswith(expected) for o in denied), outputs
    ledger = GlobalVenueEffectAuthorityLedgerV1(root=root)
    assert len(ledger.unresolved_claims_v1()) == 1


def test_b6_crash_after_consume_and_post_restart_other_root_replay_denied(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _ks(monkeypatch, tmp_path)
    store = tmp_path / "store"
    child = spawn_hard_crash_child_v1(store_root=store, crash_point=CrashPointV1.C9)
    assert child.exit_code == expected_crash_exit_v1(CrashPointV1.C9), child.stderr
    ledger = harness_global_ledger_v1(store)
    unresolved = ledger.unresolved_claims_v1()
    assert [c["state"] for c in unresolved] == [STATE_SENT_INITIATED]
    restarted = harness_global_ledger_v1(store)
    opener = _CountingTimeoutOpener()
    with pytest.raises(GlobalVenueEffectReplayDeniedError):
        _join(
            store_root=tmp_path / "fresh_root_after_restart",
            envelope=_new_risk_envelope(),
            ledger=restarted,
            opener=opener,
        )
    with pytest.raises(GlobalVenueEffectLedgerError, match="BLOCKS_NEW_RISK"):
        restarted.claim_v1(_identity(baseline=OTHER_BASELINE_SHA, client_order_id="pt-b6-new"))
    assert opener.requests == []


def test_b6_crash_orphan_same_boot_owner_gone_is_proven_unsent_and_settled(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _ks(monkeypatch, tmp_path)
    store = tmp_path / "store"
    child = spawn_hard_crash_child_v1(store_root=store, crash_point=CrashPointV1.C4)
    assert child.exit_code == expected_crash_exit_v1(CrashPointV1.C4), child.stderr
    ledger = harness_global_ledger_v1(store)
    [orphan] = ledger.unresolved_claims_v1()
    claim_id = orphan["claim_id"]
    [view] = ledger.classify_unresolved_claims_v1()
    assert view["classification"] == CLASS_CLAIMED_PROVEN_NOT_SENT
    assert view["safe_to_retry"] is False
    with pytest.raises(GlobalVenueEffectLedgerError, match="REQUIRES_LIVE_ATTEMPT"):
        ledger.abandon_unsent_claim_v1(claim_id, reason="OPERATOR_MANUAL_ABANDON")
    envelope = _new_risk_envelope()
    not_found_identity, empty_snapshot = _recon_identity_and_snapshot(envelope, order_rows=[])
    halted = ledger.reconcile_unresolved_claim_v1(
        claim_id, reconciliation_identity=not_found_identity, snapshot=empty_snapshot
    )
    assert halted.reconciliation_complete is False
    assert ledger.load_claim_v1(claim_id)["state"] == STATE_CLAIMED

    new_claim = ledger.claim_v1(
        _identity(baseline=OTHER_BASELINE_SHA, client_order_id="pt-b6-after-crash")
    )
    assert new_claim.state == STATE_CLAIMED
    settled = ledger.load_claim_v1(claim_id)
    assert settled["state"] == STATE_ABORTED_BEFORE_TRANSPORT
    assert settled["history"][-1]["detail"] == DETAIL_PROVEN_NOT_SENT
    assert [h["state"] for h in settled["history"]] == [
        STATE_CLAIMED,
        STATE_ABORTED_BEFORE_TRANSPORT,
    ]
    with pytest.raises(GlobalVenueEffectReplayDeniedError):
        claim_for_join_v1(ledger, envelope)
    assert [c["claim_id"] for c in ledger.unresolved_claims_v1()] == [new_claim.claim_id]


def test_b6_crash_orphan_unprovable_boot_session_not_released_by_manual_abandon_only_by_g004(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _ks(monkeypatch, tmp_path)
    store = tmp_path / "store"
    child = spawn_hard_crash_child_v1(store_root=store, crash_point=CrashPointV1.C4)
    assert child.exit_code == expected_crash_exit_v1(CrashPointV1.C4), child.stderr
    monkeypatch.setattr(ledger_mod, "_boot_session_identity_v1", lambda: "f" * 64)
    ledger = harness_global_ledger_v1(store)
    unresolved = ledger.unresolved_claims_v1()
    assert [c["state"] for c in unresolved] == [STATE_CLAIMED]
    claim_id = unresolved[0]["claim_id"]
    assert load_external_effect_durable_consume_v1(store_root=store)["durable_consumed"] is not True
    new_identity = _identity(baseline=OTHER_BASELINE_SHA, client_order_id="pt-b6-after-crash")
    with pytest.raises(GlobalVenueEffectLedgerError, match="BLOCKS_NEW_RISK"):
        ledger.claim_v1(new_identity)

    [view] = ledger.classify_unresolved_claims_v1()
    assert view["classification"] == CLASS_CLAIMED_ORPHAN
    assert view["held_by_this_live_attempt"] is False
    assert view["safe_to_retry"] is False
    assert ledger.load_claim_v1(claim_id)["state"] == STATE_CLAIMED

    with pytest.raises(GlobalVenueEffectLedgerError, match="REQUIRES_LIVE_ATTEMPT"):
        ledger.abandon_unsent_claim_v1(claim_id, reason="OPERATOR_MANUAL_ABANDON")
    with pytest.raises(GlobalVenueEffectLedgerError, match="INVALID_TRANSITION"):
        ledger.mark_outcome_v1(claim_id, outcome_state=STATE_ABORTED_BEFORE_TRANSPORT)
    with pytest.raises(GlobalVenueEffectLedgerError, match="REQUIRES_LIVE_ATTEMPT"):
        ledger.mark_sent_initiated_v1(
            claim_id,
            permit_id=unresolved[0]["identity"]["permit_id"],
            envelope_digest=unresolved[0]["identity"]["envelope_digest"],
        )
    assert ledger.load_claim_v1(claim_id)["state"] == STATE_CLAIMED

    envelope = _new_risk_envelope()
    not_found_identity, empty_snapshot = _recon_identity_and_snapshot(envelope, order_rows=[])
    halted = ledger.reconcile_unresolved_claim_v1(
        claim_id, reconciliation_identity=not_found_identity, snapshot=empty_snapshot
    )
    assert halted.reconciliation_complete is False
    assert ledger.load_claim_v1(claim_id)["state"] == STATE_CLAIMED
    with pytest.raises(GlobalVenueEffectLedgerError, match="BLOCKS_NEW_RISK"):
        ledger.claim_v1(new_identity)

    canceled = {
        "clOrdId": envelope.client_order_id,
        "ordId": "ord-orphan-1",
        "instId": envelope.instrument_id,
        "state": "canceled",
        "sz": envelope.quantity,
        "accFillSz": "0",
        "sCode": "0",
    }
    identity, snapshot = _recon_identity_and_snapshot(
        envelope, order_rows=[canceled], bucket="order_history"
    )
    decision = ledger.reconcile_unresolved_claim_v1(
        claim_id, reconciliation_identity=identity, snapshot=snapshot
    )
    assert decision.reconciliation_complete is True
    assert decision.execution_authority_effect == "NONE"
    assert ledger.load_claim_v1(claim_id)["state"] == STATE_RECONCILED
    with pytest.raises(GlobalVenueEffectReplayDeniedError):
        claim_for_join_v1(ledger, envelope)
    assert ledger.claim_v1(new_identity).state == STATE_CLAIMED


def test_b6_timeout_unknown_is_not_safe_to_retry(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _ks(monkeypatch, tmp_path)
    ledger = isolated_global_ledger_v1(tmp_path)
    opener = _CountingTimeoutOpener()
    claim = claim_for_join_v1(ledger, _new_risk_envelope())
    join = _join(
        store_root=tmp_path / "store",
        envelope=_new_risk_envelope(),
        ledger=ledger,
        opener=opener,
        claim=claim,
    )
    assert join.unknown_outcome is True
    assert ledger.load_claim_v1(claim.claim_id)["state"] == STATE_UNKNOWN_OUTCOME
    assert ledger.load_claim_v1(claim.claim_id)["retry_allowed"] is False
    with pytest.raises(GlobalVenueEffectLedgerError, match="INVALID_TRANSITION"):
        ledger.mark_sent_initiated_v1(
            claim.claim_id,
            permit_id=claim.identity.permit_id,
            envelope_digest=claim.identity.envelope_digest,
        )
    with pytest.raises(GlobalVenueEffectLedgerError, match="ABANDON_AFTER_SEND_FORBIDDEN"):
        ledger.abandon_unsent_claim_v1(claim.claim_id, reason="must not hide unknown")
    with pytest.raises(GlobalVenueEffectLedgerError, match="INVALID_TRANSITION"):
        ledger.mark_outcome_v1(claim.claim_id, outcome_state=STATE_ABORTED_BEFORE_TRANSPORT)
    with pytest.raises(GlobalVenueEffectReplayDeniedError):
        claim_for_join_v1(ledger, _new_risk_envelope())
    with pytest.raises(GlobalVenueEffectLedgerError, match="BLOCKS_NEW_RISK"):
        ledger.claim_v1(_identity(baseline=OTHER_BASELINE_SHA, client_order_id="pt-b6-next"))
    assert len(opener.requests) == 1


def _recon_identity_and_snapshot(
    envelope: Any,
    *,
    order_rows: list[dict[str, Any]],
    bucket: str = "pending_orders",
) -> Any:
    from src.ops.full_core_live_path_composition_root_v1.full_core_capital_guard_atomic_one_shot_v1 import (
        FullCoreAuthorizationBindingV1,
    )
    from src.ops.full_core_live_path_composition_root_v1.full_core_exchange_reconciliation_integration_v1 import (
        identity_from_full_core_binding_v1,
    )
    from src.ops.full_core_live_path_composition_root_v1.full_core_exchange_reconciliation_offline_provider_v1 import (
        OfflineExchangeFixtureV1,
        build_offline_exchange_reconciliation_snapshot_v1,
    )

    binding = FullCoreAuthorizationBindingV1(
        owner_go=POST_OWNER_GO,
        origin_main_sha=TEST_BASELINE_SHA,
        account_scope="acct-recon-test",
        environment="LIVE",
        execution_mode="OFFLINE_STUB",
        canonical_decision_id="dec-recon-test",
        instrument_id=envelope.instrument_id,
        native_id=envelope.instrument_id,
        selected_direction="ENTER_LONG",
        order_side=envelope.side,
        final_quantity=envelope.quantity,
        order_type=envelope.order_type,
        order_price=envelope.price or "",
        venue_plan_digest="vp-digest",
        envelope_digest=envelope.envelope_digest,
        guard_config_digest="gc-digest",
        session_id="sess-recon-test",
        clordid=envelope.client_order_id,
    )
    identity = identity_from_full_core_binding_v1(
        binding,
        decision_outcome="ENTER",
        venue_plan_identity="vp-1",
        envelope_identity=envelope.envelope_id,
        submit_attempt_id="submit-1",
        local_durable_state_version="v1",
    )
    snapshot = build_offline_exchange_reconciliation_snapshot_v1(
        identity=identity,
        fixture=OfflineExchangeFixtureV1(**{bucket: {"data": order_rows}}),
    )
    return identity, snapshot


def test_b6_unknown_outcome_reconciled_via_g004_keeps_authority_consumed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _ks(monkeypatch, tmp_path)
    ledger = isolated_global_ledger_v1(tmp_path)
    envelope = _new_risk_envelope()
    claim = claim_for_join_v1(ledger, envelope)
    opener = _CountingTimeoutOpener()
    _join(
        store_root=tmp_path / "store",
        envelope=envelope,
        ledger=ledger,
        opener=opener,
        claim=claim,
    )
    assert ledger.load_claim_v1(claim.claim_id)["state"] == STATE_UNKNOWN_OUTCOME

    not_found_identity, empty_snapshot = _recon_identity_and_snapshot(envelope, order_rows=[])
    halted = ledger.reconcile_unresolved_claim_v1(
        claim.claim_id, reconciliation_identity=not_found_identity, snapshot=empty_snapshot
    )
    assert halted.reconciliation_complete is False
    assert ledger.load_claim_v1(claim.claim_id)["state"] == STATE_UNKNOWN_OUTCOME

    row = {
        "clOrdId": envelope.client_order_id,
        "ordId": "ord-recon-1",
        "instId": envelope.instrument_id,
        "state": "live",
        "sz": envelope.quantity,
        "accFillSz": "0",
        "sCode": "0",
    }
    open_identity, open_snapshot = _recon_identity_and_snapshot(envelope, order_rows=[row])
    still_open = ledger.reconcile_unresolved_claim_v1(
        claim.claim_id, reconciliation_identity=open_identity, snapshot=open_snapshot
    )
    assert still_open.outcome == "CONFIRMED_OPEN"
    assert still_open.reconciliation_complete is False
    assert ledger.load_claim_v1(claim.claim_id)["state"] == STATE_UNKNOWN_OUTCOME

    canceled = dict(row, state="canceled")
    identity, snapshot = _recon_identity_and_snapshot(
        envelope, order_rows=[canceled], bucket="order_history"
    )
    wrong = replace(identity, clordid="pt-not-this-order")
    with pytest.raises(GlobalVenueEffectLedgerError, match="GLOBAL_RECON_CLORDID_MISMATCH"):
        ledger.reconcile_unresolved_claim_v1(
            claim.claim_id, reconciliation_identity=wrong, snapshot=snapshot
        )
    decision = ledger.reconcile_unresolved_claim_v1(
        claim.claim_id, reconciliation_identity=identity, snapshot=snapshot
    )
    assert decision.reconciliation_complete is True
    assert decision.execution_authority_effect == "NONE"
    assert ledger.load_claim_v1(claim.claim_id)["state"] == STATE_RECONCILED
    assert ledger.unresolved_claims_v1() == []
    with pytest.raises(GlobalVenueEffectReplayDeniedError):
        claim_for_join_v1(ledger, envelope)
    assert (
        ledger.claim_v1(
            _identity(baseline=OTHER_BASELINE_SHA, client_order_id="pt-b6-after-recon")
        ).state
        == STATE_CLAIMED
    )
    assert len(opener.requests) == 1


def test_b6_global_replay_blocks_before_second_capital_reservation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_actual_venue_post_with_fresh_envelope_bound_single_use_permit_v1 import (
        EXPECTED_BASELINE_ORIGIN_MAIN_SHA,
        OWNER_GO,
        CurrentProductiveActualVenuePostError,
        execute_current_productive_actual_venue_post_with_fresh_envelope_bound_single_use_permit_v1,
    )
    from tests.ops._current_productive_29p_chain_integrity_test_helpers_v1 import (
        MockCurrentProductive29PIntegrityBackendV1,
    )
    from tests.ops._pilot_guard_enter_post_test_helpers_v1 import (
        PilotGuardReadTransport,
        mandatory_new_risk_execute_kwargs,
    )

    _ks(monkeypatch, tmp_path)
    ledger = isolated_global_ledger_v1(tmp_path)
    opener = _CountingTimeoutOpener()

    def _execute(store_root: Path) -> Any:
        kwargs = mandatory_new_risk_execute_kwargs(store_root)
        return (
            execute_current_productive_actual_venue_post_with_fresh_envelope_bound_single_use_permit_v1(
                owner_go=OWNER_GO,
                baseline_origin_main_sha=EXPECTED_BASELINE_ORIGIN_MAIN_SHA,
                envelope=_new_risk_envelope(),
                store_root=store_root,
                evidence_root=store_root / "evidence",
                perform_real_venue_post=True,
                k1_backend=_FakeKeychainBackend(),
                opener_factory=lambda: opener,
                global_authority_ledger=ledger,
                read_only_get_transport=PilotGuardReadTransport(avail_eq="10000"),
                execution_integrity_backend=MockCurrentProductive29PIntegrityBackendV1(
                    origin_main=EXPECTED_BASELINE_ORIGIN_MAIN_SHA,
                    head=EXPECTED_BASELINE_ORIGIN_MAIN_SHA,
                    drift="",
                ),
                **kwargs,
            ),
            kwargs,
        )

    first, _ = _execute(tmp_path / "root_a")
    assert len(opener.requests) == 1
    summary = json.loads((Path(first.evidence_root) / "SUMMARY.json").read_text(encoding="utf-8"))
    assert summary["GLOBAL_AUTHORITY_CLAIM_STATE"] == STATE_UNKNOWN_OUTCOME
    assert summary["GLOBAL_AUTHORITY_REPLAY_BLOCKED"] == "true"
    assert summary["STORE_ROOT_REPLAY_BLOCKED"] == "true"
    second_root = tmp_path / "root_b"
    second_kwargs = mandatory_new_risk_execute_kwargs(second_root)
    with pytest.raises(CurrentProductiveActualVenuePostError, match="GLOBAL_REPLAY_DENIED"):
        _execute(second_root)
    assert len(opener.requests) == 1
    atomic_dir = Path(second_kwargs["pilot_atomic_state_dir"])
    reservations = list(atomic_dir.glob("*.state.json")) if atomic_dir.is_dir() else []
    assert reservations == []
    assert not (second_root / "full_core_external_effect_permit_consume_v1.json").exists()


def test_b6_canonical_root_refused_under_test_and_namespace_isolated(tmp_path: Path) -> None:
    with pytest.raises(GlobalVenueEffectLedgerError, match="FORBIDDEN_UNDER_TEST"):
        resolve_canonical_global_ledger_root_v1()
    with pytest.raises(GlobalVenueEffectLedgerError, match="FORBIDDEN_UNDER_TEST"):
        GlobalVenueEffectAuthorityLedgerV1()
    live = GlobalVenueEffectAuthorityLedgerV1(root=tmp_path)
    other_account = GlobalVenueEffectAuthorityLedgerV1(root=tmp_path, account_scope="K1:other")
    assert live.namespace != other_account.namespace
    with pytest.raises(GlobalVenueEffectLedgerError, match="ACCOUNT_SCOPE_MISMATCH"):
        other_account.claim_v1(_identity())
    live.claim_v1(_identity())
    assert other_account.unresolved_claims_v1() == []
    assert len(live.unresolved_claims_v1()) == 1
    with pytest.raises(GlobalVenueEffectLedgerError, match="BASELINE_SHA_INVALID"):
        live.claim_v1(_identity(baseline="", client_order_id="pt-b6-nosha"))
