"""Shared helpers for CURRENT productive POST hard-crash matrix (offline only)."""

from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
CHILD_RUNNER = REPO_ROOT / "tests/ops/_current_productive_post_hard_crash_child_runner_v1.py"

# Distinct exit codes so parent can prove the child reached the intended seam.
CRASH_EXIT: dict[str, int] = {
    "C1": 191,
    "C2": 192,
    "C3": 193,
    "C4": 194,
    "C6": 196,
    "C9": 199,
    "C9_HTTP200": 198,
    "C10": 200,
    "C11": 201,
    "C12": 212,
}

SUBPROCESS_TIMEOUT_SECONDS = 45

DURABLE_CONSUME_TMP_NAME = "full_core_external_effect_permit_consume_v1.json.tmp"


class RestartEvaluationReplayProbeError(RuntimeError):
    """Raised when restart evaluation skips or falsifies the same-envelope replay probe."""


class CrashPointV1(str, Enum):
    C1 = "C1"
    C2 = "C2"
    C3 = "C3"
    C4 = "C4"
    C6 = "C6"
    C9 = "C9"
    C9_HTTP200 = "C9_HTTP200"
    C10 = "C10"
    C11 = "C11"
    C12 = "C12"


@dataclass(frozen=True)
class CrashChildResultV1:
    crash_point: str
    exit_code: int
    stdout: str
    stderr: str
    timed_out: bool


@dataclass(frozen=True)
class RestartEvaluationV1:
    crash_point: str
    durable_consumed: bool
    durable_state: str | None
    correlation_present: bool
    guard_state: str | None
    second_admission_blocked: bool
    second_admission_reason: str
    mock_post_attempts_after_restart: int
    replay_attempt_executed: bool
    notes: tuple[str, ...]


class MockPostCountingOpenerV1:
    """Counts urllib open attempts for offline replay probes (never reaches network)."""

    def __init__(self) -> None:
        self.mock_post_open_attempts = 0

    def open(self, req: Any, timeout: float = 0) -> Any:
        del req, timeout
        self.mock_post_open_attempts += 1
        raise TimeoutError("hard-crash-replay-probe-timeout")


@dataclass(frozen=True)
class PermitSendSeamReplayProbeResultV1:
    mock_post_attempts: int
    rejection_reason: str
    owner_go_gate_reached: bool
    durable_permit_id: str
    durable_envelope_id: str


def assert_permit_send_seam_replay_proof_v1(
    result: PermitSendSeamReplayProbeResultV1,
    *,
    expect_durable_consumed_block: bool = True,
) -> None:
    if expect_durable_consumed_block:
        if result.rejection_reason not in {"CONSUMED_PERMIT", "REPLAYED_PERMIT"}:
            raise RestartEvaluationReplayProbeError(
                f"SEAM_REPLAY_REJECTION_UNEXPECTED:{result.rejection_reason}"
            )
        if result.mock_post_attempts != 0:
            raise RestartEvaluationReplayProbeError(
                f"SEAM_REPLAY_MOCK_POST_NONZERO:{result.mock_post_attempts}"
            )


def attempt_permit_send_seam_same_envelope_replay_v1(
    *,
    store_root: Path,
    envelope: Any,
) -> PermitSendSeamReplayProbeResultV1:
    """Invoke CURRENT envelope-bound send seam directly on a consumed durable store (offline)."""
    from src.ops.full_core_live_path_composition_root_v1.envelope_bound_external_effect_send_seam_v1 import (
        FullCoreEnvelopeBoundSendSeamError,
        attempt_envelope_bound_external_effect_send_v1,
    )
    from src.ops.full_core_live_path_composition_root_v1.execution_admission_contract_v1 import (
        DurableKillSwitchEvidenceStatusV1,
    )
    from src.ops.full_core_live_path_composition_root_v1.external_effect_permit_durable_consume_v1 import (
        DURABLE_STATE_SENT_INITIATED,
        load_external_effect_durable_consume_v1,
    )
    from src.ops.full_core_live_path_composition_root_v1.external_effect_permit_v1 import (
        issue_external_effect_permit_v1,
    )
    from src.ops.full_core_live_path_composition_root_v1.full_core_productive_http_post_transport_v1 import (
        FullCoreNonNetworkingTestPostTransportV1,
    )
    from src.ops.full_core_live_path_composition_root_v1.gated_productive_wire_transport_v1 import (
        FullCoreSendCredentialHandleV1,
    )
    from src.ops.full_core_live_path_composition_root_v1.submission_authorized_v1 import (
        STEP_29Q_PLAN_ONLY,
    )

    durable_before = load_external_effect_durable_consume_v1(store_root=store_root)
    record = durable_before.get("record") if isinstance(durable_before.get("record"), dict) else {}
    permit_id_before = str(record.get("permit_id") or "")
    envelope_id_before = str(record.get("envelope_id") or "")
    authority_ref = str(record.get("authority_ref") or "").strip()
    if not authority_ref:
        raise RestartEvaluationReplayProbeError("DURABLE_AUTHORITY_REF_MISSING")
    durable_state_before = str(record.get("durable_state") or "")
    if durable_before.get("durable_consumed") is not True:
        raise RestartEvaluationReplayProbeError("DURABLE_PERMIT_NOT_CONSUMED_FOR_SEAM_PROBE")
    if durable_state_before != DURABLE_STATE_SENT_INITIATED:
        raise RestartEvaluationReplayProbeError(
            f"DURABLE_STATE_UNEXPECTED:{durable_state_before or 'EMPTY'}"
        )

    transport = FullCoreNonNetworkingTestPostTransportV1()
    permit = issue_external_effect_permit_v1(
        envelope,
        authority_ref=authority_ref,
        kill_switch_blocked=False,
        durable_kill_switch_evidence_status=DurableKillSwitchEvidenceStatusV1.TRUSTED_PRESENT.value,
        filegate_denied=False,
        step_29q_status=STEP_29Q_PLAN_ONLY,
    )
    if permit.permit_id != permit_id_before:
        raise RestartEvaluationReplayProbeError("PERMIT_ID_DRIFT_VS_DURABLE_RECORD")
    if str(envelope.envelope_id) != envelope_id_before:
        raise RestartEvaluationReplayProbeError("ENVELOPE_ID_DRIFT_VS_DURABLE_RECORD")

    handle = FullCoreSendCredentialHandleV1(
        handle_id="hard-crash-permit-send-seam-replay-probe-v1",
        bound=True,
    )
    rejection = ""
    try:
        attempt_envelope_bound_external_effect_send_v1(
            envelope=envelope,
            permit=permit,
            store_root=store_root,
            transport=transport,
            handle=handle,
        )
        rejection = "UNEXPECTED_SUCCESS"
    except FullCoreEnvelopeBoundSendSeamError as exc:
        rejection = str(exc)

    durable_after = load_external_effect_durable_consume_v1(store_root=store_root)
    after_record = (
        durable_after.get("record") if isinstance(durable_after.get("record"), dict) else {}
    )
    if durable_after.get("durable_consumed") is not True:
        raise RestartEvaluationReplayProbeError("DURABLE_CONSUME_CLEARED_AFTER_SEAM_REPLAY")
    if str(after_record.get("permit_id") or "") != permit_id_before:
        raise RestartEvaluationReplayProbeError("DURABLE_PERMIT_ID_MUTATED")
    if str(after_record.get("durable_state") or "") != DURABLE_STATE_SENT_INITIATED:
        raise RestartEvaluationReplayProbeError("DURABLE_STATE_MUTATED")

    return PermitSendSeamReplayProbeResultV1(
        mock_post_attempts=int(transport.post_count),
        rejection_reason=rejection,
        owner_go_gate_reached=False,
        durable_permit_id=permit_id_before,
        durable_envelope_id=envelope_id_before,
    )


def _attempt_execute_path_same_envelope_replay_v1(
    *,
    store_root: Path,
    envelope: Any,
) -> tuple[int, bool]:
    """Re-drive full Enter-POST execute when durable consume is not yet present."""
    from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_actual_venue_post_with_fresh_envelope_bound_single_use_permit_v1 import (
        EXPECTED_BASELINE_ORIGIN_MAIN_SHA,
        OWNER_GO,
        execute_current_productive_actual_venue_post_with_fresh_envelope_bound_single_use_permit_v1,
    )
    from tests.ops._current_productive_29p_chain_integrity_test_helpers_v1 import (
        MockCurrentProductive29PIntegrityBackendV1,
    )
    from tests.ops._pilot_guard_enter_post_test_helpers_v1 import (
        PilotGuardReadTransport,
        mandatory_new_risk_execute_kwargs,
    )
    from tests.ops.test_current_productive_one_shot_fresh_envelope_permit_mint_durable_consume_and_post_join_v1 import (
        _FakeKeychainBackend,
        _persist_post_go,
    )

    counting_opener = MockPostCountingOpenerV1()
    kwargs = mandatory_new_risk_execute_kwargs(store_root)
    _persist_post_go(store_root)
    executed = False
    try:
        executed = True
        execute_current_productive_actual_venue_post_with_fresh_envelope_bound_single_use_permit_v1(
            owner_go=OWNER_GO,
            baseline_origin_main_sha=EXPECTED_BASELINE_ORIGIN_MAIN_SHA,
            envelope=envelope,
            store_root=store_root,
            evidence_root=store_root / "evidence",
            perform_real_venue_post=True,
            k1_backend=_FakeKeychainBackend(),
            opener_factory=lambda: counting_opener,
            read_only_get_transport=PilotGuardReadTransport(avail_eq="10000"),
            execution_integrity_backend=MockCurrentProductive29PIntegrityBackendV1(
                origin_main=EXPECTED_BASELINE_ORIGIN_MAIN_SHA,
                head=EXPECTED_BASELINE_ORIGIN_MAIN_SHA,
                drift="",
            ),
            **kwargs,
        )
    except Exception:
        pass
    return counting_opener.mock_post_open_attempts, executed


def _attempt_same_envelope_controlled_replay_v1(
    *,
    store_root: Path,
    envelope: Any,
) -> tuple[int, bool, str]:
    """Return (mock_post_count, executed, replay_channel)."""
    from src.ops.full_core_live_path_composition_root_v1.external_effect_permit_durable_consume_v1 import (
        load_external_effect_durable_consume_v1,
    )

    durable = load_external_effect_durable_consume_v1(store_root=store_root)
    if durable.get("durable_consumed") is True:
        seam = attempt_permit_send_seam_same_envelope_replay_v1(
            store_root=store_root,
            envelope=envelope,
        )
        assert_permit_send_seam_replay_proof_v1(seam)
        return seam.mock_post_attempts, True, f"PERMIT_SEND_SEAM:{seam.rejection_reason}"
    mock_posts, executed = _attempt_execute_path_same_envelope_replay_v1(
        store_root=store_root,
        envelope=envelope,
    )
    return mock_posts, executed, "EXECUTE_PATH"


def spawn_hard_crash_child_v1(
    *,
    store_root: Path,
    crash_point: CrashPointV1 | str,
    extra: dict[str, Any] | None = None,
) -> CrashChildResultV1:
    point = _crash_point_key(crash_point)
    payload = {"crash_point": point, "extra": dict(extra or {})}
    config_path = store_root / "hard_crash_child_config_v1.json"
    store_root.mkdir(parents=True, exist_ok=True)
    config_path.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")
    cmd = [
        sys.executable,
        str(CHILD_RUNNER),
        "--store-root",
        str(store_root),
        "--config",
        str(config_path),
    ]
    try:
        completed = subprocess.run(
            cmd,
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            timeout=SUBPROCESS_TIMEOUT_SECONDS,
            check=False,
        )
        return CrashChildResultV1(
            crash_point=point,
            exit_code=int(completed.returncode),
            stdout=completed.stdout or "",
            stderr=completed.stderr or "",
            timed_out=False,
        )
    except subprocess.TimeoutExpired as exc:
        return CrashChildResultV1(
            crash_point=point,
            exit_code=-9,
            stdout=(exc.stdout or "") if isinstance(exc.stdout, str) else "",
            stderr=(exc.stderr or "") if isinstance(exc.stderr, str) else "",
            timed_out=True,
        )


def _crash_point_key(crash_point: CrashPointV1 | str) -> str:
    if isinstance(crash_point, CrashPointV1):
        return crash_point.value
    return str(crash_point).strip()


def expected_crash_exit_v1(crash_point: CrashPointV1 | str) -> int:
    code = CRASH_EXIT.get(_crash_point_key(crash_point))
    if code is None:
        raise KeyError(f"unknown crash point: {crash_point}")
    return code


def _second_new_risk_envelope() -> Any:
    from src.ops.full_core_live_path_composition_root_v1.final_order_envelope_v1 import (
        bind_final_order_envelope_from_venue_plan_v1,
    )
    from src.ops.full_core_live_path_composition_root_v1.models_v1 import VenuePlanCandidateV1
    from tests.ops._pilot_guard_enter_post_test_helpers_v1 import PILOT_TEST_INST

    plan = VenuePlanCandidateV1(
        instrument_id="okx_eea:linear_perpetual:0G:USDT:USDT:0g-usdt-swap",
        side="buy",
        quantity="1",
        order_type="market",
        td_mode="cross",
        reduce_only=False,
        clordid="pt-hard-crash-second-entry-v1",
        venue_native_payload={
            "instId": PILOT_TEST_INST,
            "ordType": "market",
            "side": "buy",
            "sz": "1",
            "tdMode": "cross",
        },
        quantity_source="TEST_FIXTURE_NOT_LIVE_ENVELOPE",
        side_source="TEST_FIXTURE_NOT_LIVE_ENVELOPE",
        instrument_source="DH_CAP24_BOUND_INSTRUMENT_ID",
        path_kind="FULL_CORE_CURRENT_PRODUCTIVE",
    )
    return bind_final_order_envelope_from_venue_plan_v1(
        plan,
        admission_ref="TEST_ADMISSION_REF",
        provenance_ref="TEST_PROVENANCE_REF",
        creation_epoch="2026-10-14T00:00:02Z",
    )


def evaluate_restart_after_crash_v1(
    *,
    store_root: Path,
    crash_point: CrashPointV1 | str,
    first_envelope: Any | None = None,
    require_replay_probe: bool = True,
) -> RestartEvaluationV1:
    from src.ops.full_core_live_path_composition_root_v1.current_productive_mandatory_new_risk_enter_post_admission_v1 import (
        MandatoryNewRiskEnterPostAdmissionError,
        correlation_path_v1,
        load_enter_post_lifecycle_correlation_v1,
        prove_new_risk_enter_post_store_admission_clear_v1,
    )
    from src.ops.full_core_live_path_composition_root_v1.external_effect_permit_durable_consume_v1 import (
        DURABLE_STATE_SENT_INITIATED,
        load_external_effect_durable_consume_v1,
    )
    from src.ops.full_core_live_path_composition_root_v1.full_core_capital_guard_atomic_one_shot_v1 import (
        full_core_durable_entry_state_for_guard_v1,
    )
    from tests.ops._pilot_guard_enter_post_test_helpers_v1 import mandatory_new_risk_execute_kwargs
    from tests.ops.test_current_productive_one_shot_fresh_envelope_permit_mint_durable_consume_and_post_join_v1 import (
        _new_risk_envelope,
    )

    point = _crash_point_key(crash_point)
    env = first_envelope if first_envelope is not None else _new_risk_envelope()
    kwargs = mandatory_new_risk_execute_kwargs(store_root)
    atomic_dir = kwargs["pilot_atomic_state_dir"]
    durable = load_external_effect_durable_consume_v1(store_root=store_root)
    record = durable.get("record") if isinstance(durable.get("record"), dict) else {}
    durable_state = str(record.get("durable_state") or "") or None
    correlation = load_enter_post_lifecycle_correlation_v1(store_root=store_root)
    guard_state = None
    if correlation is not None:
        key = str(correlation.get("guard_consumption_key") or "")
        if key:
            guard_state = full_core_durable_entry_state_for_guard_v1(
                state_dir=atomic_dir,
                consumption_key=key,
            )
    if guard_state is None and atomic_dir.is_dir():
        for state_path in sorted(atomic_dir.glob("*.state.json")):
            try:
                payload = json.loads(state_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                continue
            if isinstance(payload, dict) and payload.get("state"):
                guard_state = str(payload["state"])
                break
    notes: list[str] = []
    if correlation_path_v1(store_root=store_root).is_file():
        notes.append("CORRELATION_FILE_PRESENT")
    tmp_consume = list(store_root.glob("full_core_external_effect_permit_consume_v1.json.tmp"))
    if tmp_consume:
        notes.append("DURABLE_CONSUME_TMP_PRESENT")

    second_blocked = False
    reason = ""
    try:
        prove_new_risk_enter_post_store_admission_clear_v1(
            store_root=store_root,
            envelope=_second_new_risk_envelope(),
            atomic_state_dir=atomic_dir,
        )
    except MandatoryNewRiskEnterPostAdmissionError as exc:
        second_blocked = True
        reason = str(exc)

    mock_posts, replay_executed, replay_channel = _attempt_same_envelope_controlled_replay_v1(
        store_root=store_root,
        envelope=env,
    )
    if require_replay_probe and not replay_executed:
        raise RestartEvaluationReplayProbeError("SAME_ENVELOPE_REPLAY_PROBE_NOT_EXECUTED")
    if mock_posts > 0:
        raise RestartEvaluationReplayProbeError(f"UNEXPECTED_MOCK_POST_AFTER_RESTART:{mock_posts}")
    notes.append("REPLAY_ATTEMPT_EXECUTED" if replay_executed else "REPLAY_ATTEMPT_SKIPPED")
    notes.append(f"REPLAY_CHANNEL={replay_channel}")

    return RestartEvaluationV1(
        crash_point=point,
        durable_consumed=bool(durable.get("durable_consumed")),
        durable_state=durable_state,
        correlation_present=correlation is not None,
        guard_state=guard_state,
        second_admission_blocked=second_blocked,
        second_admission_reason=reason,
        mock_post_attempts_after_restart=mock_posts,
        replay_attempt_executed=replay_executed,
        notes=tuple(notes),
    )


def build_okx_post_ack_body_v1(*, clordid: str, ord_id: str = "mock-venue-ord-1") -> bytes:
    payload = {
        "code": "0",
        "msg": "",
        "data": [
            {
                "sCode": "0",
                "sMsg": "",
                "ordId": ord_id,
                "clOrdId": clordid,
            }
        ],
    }
    return json.dumps(payload, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


class ValidOkxPostAckOpenerV1:
    """Minimal urllib opener returning HTTP 200 + OKX code=0/sCode=0 ACK shape."""

    def __init__(self, *, clordid: str, ord_id: str = "mock-venue-ord-1") -> None:
        self.clordid = clordid
        self.ord_id = ord_id
        self.requests: list[Any] = []

    def open(self, req: Any, timeout: float = 0) -> Any:
        del timeout
        import io
        from urllib.response import addinfourl

        self.requests.append(req)
        url = str(getattr(req, "full_url", "https://eea.okx.com/api/v5/trade/order"))
        body = build_okx_post_ack_body_v1(clordid=self.clordid, ord_id=self.ord_id)
        return addinfourl(io.BytesIO(body), {}, url, 200)


def write_parent_mock_exchange_acceptance_stub_v1(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "schema": "mock_exchange_acceptance_external_v1",
                "phase": "PARENT_PRE_CHILD",
                "authoritative_for_trading": False,
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def read_json_file_v1(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise AssertionError(f"JSON_NOT_OBJECT:{path}")
    return payload


def bootstrap_unknown_post_store_v1(tmp_path: Path) -> tuple[Path, Any]:
    """Run C9 timeout crash to leave SENT_INITIATED unknown POST store (offline)."""
    from tests.ops.test_current_productive_one_shot_fresh_envelope_permit_mint_durable_consume_and_post_join_v1 import (
        _new_risk_envelope,
    )

    store = tmp_path / "store"
    spawn_hard_crash_child_v1(store_root=store, crash_point=CrashPointV1.C9)
    env = _new_risk_envelope()
    restart = evaluate_restart_after_crash_v1(store_root=store, crash_point=CrashPointV1.C9)
    assert restart.durable_consumed is True
    assert restart.durable_state == "SENT_INITIATED"
    return store, env


def run_adversarial_reconciliation_v1(
    *,
    scenario: str,
    client_order_id: str,
    instrument_id: str,
) -> Any:
    from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_unknown_post_attempt_read_only_reconciliation_v1 import (
        reconcile_unknown_post_attempt_read_only_v1,
    )

    transport = AdversarialReconciliationReadTransportV1(
        scenario,
        clordid=client_order_id,
        inst=instrument_id,
    )
    return reconcile_unknown_post_attempt_read_only_v1(
        client_order_id=client_order_id,
        instrument_id=instrument_id,
        inst_type="SWAP",
        read_only_get_transport=transport,
        pretrade_decision_id="hard-crash-recon-adversarial",
    )


class AdversarialReconciliationReadTransportV1:
    """Scenario-keyed mock GET transport for reconcile_unknown_post_attempt_read_only_v1."""

    def __init__(self, scenario: str, *, clordid: str, inst: str) -> None:
        self.scenario = scenario
        self.clordid = clordid
        self.inst = inst
        self.request_count = 0

    def get(self, *, endpoint: str, auth_required: bool, pretrade_decision_id: str):
        del auth_required, pretrade_decision_id
        from src.ops.full_core_live_path_composition_root_v1.fresh_pretrade_runtime_get_v1 import (
            FreshPretradeGetTransportResultV1,
            TRANSPORT_CLASS_PRODUCTIVE_READ_ONLY_GET,
        )

        self.request_count += 1
        path = str(endpoint).split("?", 1)[0]

        if self.scenario == "GET_TECHNICAL_ERROR":
            return FreshPretradeGetTransportResultV1(
                get_performed=False,
                method="GET",
                endpoint=endpoint,
                http_status=0,
                payload=None,
                auth_header_sent=False,
                transport_class=TRANSPORT_CLASS_PRODUCTIVE_READ_ONLY_GET,
                venue_live_contact=False,
                historical_reuse=False,
                error_class="TRANSPORT_MISSING",
                data_safety_source_kind="REAL",
            )

        def _ok(payload: dict[str, Any]) -> FreshPretradeGetTransportResultV1:
            return FreshPretradeGetTransportResultV1(
                get_performed=True,
                method="GET",
                endpoint=endpoint,
                http_status=200,
                payload=payload,
                auth_header_sent=True,
                transport_class=TRANSPORT_CLASS_PRODUCTIVE_READ_ONLY_GET,
                venue_live_contact=True,
                historical_reuse=False,
                error_class="",
                data_safety_source_kind="REAL",
            )

        if self.scenario == "EMPTY_ORDER_RESPONSE":
            return _ok({"code": "0", "data": []})

        if self.scenario == "BUSINESS_NEGATIVE":
            if "orders-pending" in path or "orders-history" in path or "trade/order" in path:
                return _ok(
                    {
                        "code": "0",
                        "data": [
                            {
                                "clOrdId": self.clordid,
                                "instId": self.inst,
                                "ordId": "ord-rej-1",
                                "state": "canceled",
                                "sCode": "51008",
                                "sMsg": "Order failed",
                            }
                        ],
                    }
                )
            return _ok({"code": "0", "data": []})

        if self.scenario == "ORDER_WITHOUT_POSITION":
            if "orders-pending" in path:
                return _ok(
                    {
                        "code": "0",
                        "data": [
                            {
                                "clOrdId": self.clordid,
                                "instId": self.inst,
                                "ordId": "ord-live-1",
                                "state": "live",
                                "sCode": "0",
                            }
                        ],
                    }
                )
            if "positions" in path:
                return _ok({"code": "0", "data": []})
            return _ok({"code": "0", "data": []})

        if self.scenario == "CONTRADICTORY_EVIDENCE":
            if "orders-pending" in path:
                return _ok(
                    {
                        "code": "0",
                        "data": [
                            {
                                "clOrdId": self.clordid,
                                "instId": self.inst,
                                "ordId": "ord-a",
                                "state": "live",
                                "sCode": "0",
                            }
                        ],
                    }
                )
            if "trade/order" in path:
                return _ok(
                    {
                        "code": "0",
                        "data": [
                            {
                                "clOrdId": self.clordid,
                                "instId": self.inst,
                                "ordId": "ord-b",
                                "state": "canceled",
                                "sCode": "51008",
                            }
                        ],
                    }
                )
            return _ok({"code": "0", "data": []})

        if self.scenario == "POSITIVE_ORDER_EVIDENCE":
            if "orders-pending" in path or "trade/order" in path:
                return _ok(
                    {
                        "code": "0",
                        "data": [
                            {
                                "clOrdId": self.clordid,
                                "instId": self.inst,
                                "ordId": "ord-pos-1",
                                "state": "live",
                                "sCode": "0",
                            }
                        ],
                    }
                )
            return _ok({"code": "0", "data": []})

        raise AssertionError(f"UNKNOWN_RECON_SCENARIO:{self.scenario}")


def assert_second_new_risk_admission_blocked_v1(*, store_root: Path) -> str:
    restart = evaluate_restart_after_crash_v1(store_root=store_root, crash_point=CrashPointV1.C9)
    assert restart.second_admission_blocked is True
    return restart.second_admission_reason
