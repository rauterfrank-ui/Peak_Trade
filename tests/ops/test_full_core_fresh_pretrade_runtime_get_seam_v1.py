"""Fresh Pretrade Runtime GET seam for Full-Core admission. No venue GET."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    FRESH_PRETRADE_RUNTIME_GET_IMPLEMENTED,
    LIVE_ARMED,
    LIVE_ENABLED,
    OWNER_ONE_SHOT_PERMIT_TOKEN,
    WIRE_SEND_PERMITTED,
)
from src.ops.full_core_live_path_composition_root_v1.execution_admission_contract_v1 import (
    ADMISSION_CONTEXT_LIVE,
    ADMISSION_CONTEXT_OFFLINE_FULL_CORE_PROOF,
    CAPITAL_RISK_MODE_LIVE_ACCOUNT_BOUND,
    CAPITAL_RISK_MODE_OFFLINE_ALGEBRA,
    DurableKillSwitchEvidenceStatusV1,
    FreshPretradeGetStatusV1,
    OwnerOneShotPermitStatusV1,
    PRETRADE_SOURCE_FRESH_GET,
    PRETRADE_SOURCE_FROZEN_OFFLINE,
    PretradeFreshnessStatusV1,
    evaluate_execution_admission_v1,
)
from src.ops.full_core_live_path_composition_root_v1.fresh_pretrade_runtime_get_v1 import (
    ENDPOINT_ACCOUNT_BALANCE,
    ENDPOINT_ACCOUNT_CONFIG,
    ENDPOINT_ACCOUNT_LEVERAGE_INFO,
    ENDPOINT_ACCOUNT_MAX_SIZE,
    ENDPOINT_ACCOUNT_POSITIONS,
    ENDPOINT_PUBLIC_INSTRUMENTS,
    ENDPOINT_PUBLIC_PRICE_LIMIT,
    JOIN_SEAM_ID,
    PRIVATE_GET_PATHS,
    PUBLIC_GET_PATHS,
    REQUIRED_GET_ITEM_SPECS,
    TRANSPORT_CLASS_INJECTED_TEST_DOUBLE,
    FreshPretradeGetTransportResultV1,
    collect_fresh_pretrade_runtime_get_v1,
    join_fresh_pretrade_runtime_get_into_admission_inputs_v1,
)
from src.ops.full_core_live_path_composition_root_v1.live_admission_gap_dag_v1 import (
    EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY,
    FRESH_EXTERNAL_EVIDENCE_REQUIRED_FOR_NEXT_SLICE,
    gap_node_v1,
)
from src.risk_layer.kill_switch.persistence import StatePersistence
from src.risk_layer.kill_switch.state import KillSwitchState
from tests.ops.test_full_core_execution_admission_contract_v1 import _live_inputs
from tests.ops.test_full_core_live_path_composition_root_v1 import _run
from tests.trading.master_v2.test_master_v2_integrated_replay_safety_before_intent_restore_contract_v1 import (
    _confirmed_replay_input,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
RUNBOOK = REPO_ROOT / "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md"
SPEC_PATH = REPO_ROOT / "docs/ops/specs/FULL_CORE_FRESH_PRETRADE_RUNTIME_GET_SEAM_V1.md"

_OK_PAYLOAD = {"code": "0", "data": [{"row": "1"}]}
_REQUIRED_PATHS = (
    ENDPOINT_PUBLIC_INSTRUMENTS,
    ENDPOINT_PUBLIC_PRICE_LIMIT,
    ENDPOINT_ACCOUNT_MAX_SIZE,
    ENDPOINT_ACCOUNT_LEVERAGE_INFO,
    ENDPOINT_ACCOUNT_CONFIG,
    ENDPOINT_ACCOUNT_POSITIONS,
    ENDPOINT_ACCOUNT_BALANCE,
)


class InjectedFreshGetTransportV1:
    def __init__(
        self,
        *,
        payloads=None,
        missing_paths=(),
        historical_reuse=False,
        venue_live_contact=False,
        transport_class=TRANSPORT_CLASS_INJECTED_TEST_DOUBLE,
        http_status=200,
        status_by_path=None,
        auth_header_sent=None,
        method="GET",
        payload_override=None,
        error_class="",
    ):
        self.payloads = payloads or {}
        self.missing_paths = set(missing_paths)
        self.historical_reuse = historical_reuse
        self.venue_live_contact = venue_live_contact
        self.transport_class = transport_class
        self.http_status = http_status
        self.status_by_path = status_by_path or {}
        self.auth_header_sent = auth_header_sent
        self.method = method
        self.payload_override = payload_override
        self.error_class = error_class

    def get(self, *, endpoint, auth_required, pretrade_decision_id):
        path = str(endpoint or "").split("?", 1)[0]
        if path in self.missing_paths:
            return FreshPretradeGetTransportResultV1(
                get_performed=False,
                method="GET",
                endpoint=endpoint,
                http_status=0,
                payload=None,
                auth_header_sent=False,
                transport_class=self.transport_class,
                venue_live_contact=False,
                historical_reuse=False,
                error_class="NOT_PERFORMED",
            )
        auth_sent = self.auth_header_sent
        if auth_sent is None:
            auth_sent = bool(auth_required)
        payload = self.payload_override
        if payload is None:
            payload = self.payloads.get(path, _OK_PAYLOAD)
        return FreshPretradeGetTransportResultV1(
            get_performed=True,
            method=self.method,
            endpoint=endpoint,
            http_status=int(self.status_by_path.get(path, self.http_status)),
            payload=payload,
            auth_header_sent=auth_sent,
            transport_class=self.transport_class,
            venue_live_contact=self.venue_live_contact,
            historical_reuse=self.historical_reuse,
            error_class=self.error_class,
        )


def _bind_state_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    path = tmp_path / "kill_switch_state.json"
    monkeypatch.setenv("PEAK_KILL_SWITCH_STATE_PATH", str(path))
    monkeypatch.delenv("PEAKTRADE_KILL_SWITCH_STATE_PATH", raising=False)
    monkeypatch.delenv("PEAK_KILL_SWITCH", raising=False)
    return path


def _collect(**overrides):
    payload = {
        "pretrade_decision_id": "decision-1",
        "instrument_id": "SUI-USD_UM_XPERP-310404",
        "td_mode": "cross",
        "limit_px": "1.23",
        "transport": InjectedFreshGetTransportV1(),
        "require_collection": True,
    }
    payload.update(overrides)
    return collect_fresh_pretrade_runtime_get_v1(**payload)


def _join_live(*, transport, owner_go=OWNER_ONE_SHOT_PERMIT_TOKEN, **kwargs):
    payload = {
        "plan_identity": "plan-1",
        "venue_plan_identity": "venue-1",
        "instrument_identity_ok": True,
        "pretrade_admissible": True,
        "pretrade_source_kind": PRETRADE_SOURCE_FROZEN_OFFLINE,
        "pretrade_freshness_status": PretradeFreshnessStatusV1.FROZEN_OFFLINE.value,
        "capital_risk_mode": CAPITAL_RISK_MODE_OFFLINE_ALGEBRA,
        "owner_go": owner_go,
        "admission_context": ADMISSION_CONTEXT_LIVE,
        "provenance_refs": (),
        "transport": transport,
        "pretrade_decision_id": "decision-1",
        "instrument_id": "SUI-USD_UM_XPERP-310404",
        "td_mode": "cross",
        "limit_px": "1.23",
    }
    payload.update(kwargs)
    return join_fresh_pretrade_runtime_get_into_admission_inputs_v1(**payload)


def test_flag_and_standing_gates_remain_false() -> None:
    assert FRESH_PRETRADE_RUNTIME_GET_IMPLEMENTED is True
    assert LIVE_ENABLED is False
    assert LIVE_ARMED is False
    assert WIRE_SEND_PERMITTED is False
    assert EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY == "LIVE_ENABLED"
    assert FRESH_EXTERNAL_EVIDENCE_REQUIRED_FOR_NEXT_SLICE is False
    node = gap_node_v1("FRESH_GET_PER_PRETRADE_DECISION")
    assert node.implementation_status == "JOINED_TYPED_EVIDENCE_FAIL_CLOSED"
    assert node.wiring_authorized is True
    assert node.standing_live_gates_would_change is False
    auth = gap_node_v1("PRIVATE_AUTH_PREFLIGHT")
    assert auth.implementation_status == "PRIVATE_GET_AUTH_REQUIRED_FAIL_CLOSED"
    assert auth.wiring_authorized is True
    assert PUBLIC_GET_PATHS == {
        ENDPOINT_PUBLIC_INSTRUMENTS,
        ENDPOINT_PUBLIC_PRICE_LIMIT,
    }
    assert PRIVATE_GET_PATHS == {
        ENDPOINT_ACCOUNT_MAX_SIZE,
        ENDPOINT_ACCOUNT_LEVERAGE_INFO,
        ENDPOINT_ACCOUNT_CONFIG,
        ENDPOINT_ACCOUNT_POSITIONS,
        ENDPOINT_ACCOUNT_BALANCE,
    }
    assert {spec.item_id for spec in REQUIRED_GET_ITEM_SPECS} == {
        "INSTRUMENT_STATE",
        "MAX_SIZE",
        "PRICE_BAND",
        "MAX_AVAILABLE",
        "LEVERAGE",
        "POS_MODE",
        "ACCOUNT_MODE",
        "MARGIN_MODE",
        "AVAILABLE_MARGIN",
    }


def test_all_required_get_evidence_valid_fresh_component_pass() -> None:
    evidence = _collect()
    assert evidence.evidence_status == FreshPretradeGetStatusV1.TRUSTED_PRESENT.value
    assert evidence.pretrade_source_kind == PRETRADE_SOURCE_FRESH_GET
    assert evidence.pretrade_freshness_status == PretradeFreshnessStatusV1.LIVE_FRESH.value
    assert evidence.venue_live_contact is False
    assert evidence.live_enabled is False
    assert evidence.wire_send_permitted is False
    assert evidence.post_attempted is False
    assert len(evidence.items) == len(REQUIRED_GET_ITEM_SPECS)
    assert all(
        item.evidence_status == FreshPretradeGetStatusV1.TRUSTED_PRESENT.value
        for item in evidence.items
    )


def test_missing_required_evidence_deny() -> None:
    evidence = _collect(transport=None)
    assert evidence.evidence_status == FreshPretradeGetStatusV1.MISSING.value
    assert evidence.pretrade_freshness_status == PretradeFreshnessStatusV1.MISSING.value


def test_malformed_payload_deny() -> None:
    evidence = _collect(transport=InjectedFreshGetTransportV1(payload_override={"code": "0"}))
    assert evidence.evidence_status == FreshPretradeGetStatusV1.MALFORMED.value
    truthy = _collect(transport=InjectedFreshGetTransportV1(payload_override={"ok": True}))
    assert truthy.evidence_status == FreshPretradeGetStatusV1.MALFORMED.value
    numeric = _collect(
        transport=InjectedFreshGetTransportV1(payload_override={"code": 0, "data": [1]})
    )
    assert numeric.evidence_status == FreshPretradeGetStatusV1.MALFORMED.value


def test_stale_historical_reuse_deny() -> None:
    evidence = _collect(transport=InjectedFreshGetTransportV1(historical_reuse=True))
    assert evidence.evidence_status == FreshPretradeGetStatusV1.STALE.value
    assert "FRESH_PRETRADE_GET_FIXTURE_REPLAY_NOT_PRODUCTIVE" in evidence.reason_codes


def test_one_required_get_missing_among_otherwise_valid_set_deny() -> None:
    evidence = _collect(
        transport=InjectedFreshGetTransportV1(missing_paths={ENDPOINT_ACCOUNT_BALANCE})
    )
    assert evidence.evidence_status == FreshPretradeGetStatusV1.MISSING.value
    missing_item = next(item for item in evidence.items if item.item_id == "AVAILABLE_MARGIN")
    assert missing_item.evidence_status == FreshPretradeGetStatusV1.MISSING.value
    others = [item for item in evidence.items if item.item_id != "AVAILABLE_MARGIN"]
    assert all(
        item.evidence_status == FreshPretradeGetStatusV1.TRUSTED_PRESENT.value for item in others
    )


def test_auth_failure_on_private_get_deny() -> None:
    evidence = _collect(
        transport=InjectedFreshGetTransportV1(
            status_by_path={ENDPOINT_ACCOUNT_CONFIG: 401},
            error_class="AUTH_ERROR",
        )
    )
    assert evidence.evidence_status == FreshPretradeGetStatusV1.AUTH_FAILURE.value
    no_header = _collect(transport=InjectedFreshGetTransportV1(auth_header_sent=False))
    assert no_header.evidence_status == FreshPretradeGetStatusV1.AUTH_FAILURE.value


def test_public_get_failure_deny() -> None:
    evidence = _collect(
        transport=InjectedFreshGetTransportV1(status_by_path={ENDPOINT_PUBLIC_PRICE_LIMIT: 500})
    )
    assert evidence.evidence_status == FreshPretradeGetStatusV1.PUBLIC_FAILURE.value


def test_fixture_replay_cannot_impersonate_productive_fresh_evidence() -> None:
    evidence = _collect(pretrade_decision_id="HISTORICAL_Z2V_PACK")
    assert evidence.evidence_status == FreshPretradeGetStatusV1.STALE.value
    claimed = _collect(transport=InjectedFreshGetTransportV1(venue_live_contact=True))
    assert claimed.evidence_status == FreshPretradeGetStatusV1.CONTRADICTORY.value
    productive = _collect(transport=InjectedFreshGetTransportV1(transport_class="PRODUCTIVE_VENUE"))
    assert productive.evidence_status == FreshPretradeGetStatusV1.CONTRADICTORY.value


def test_duplicate_ambiguous_payload_is_grouped_once() -> None:
    evidence = _collect()
    instrument_items = [
        item for item in evidence.items if item.endpoint_path == ENDPOINT_PUBLIC_INSTRUMENTS
    ]
    assert len(instrument_items) == 2
    assert {item.item_id for item in instrument_items} == {"INSTRUMENT_STATE", "MAX_SIZE"}


def test_post_method_is_forbidden() -> None:
    evidence = _collect(transport=InjectedFreshGetTransportV1(method="POST"))
    assert evidence.evidence_status == FreshPretradeGetStatusV1.CONTRADICTORY.value
    assert evidence.post_attempted is True
    assert "FRESH_PRETRADE_GET_POST_FORBIDDEN" in evidence.reason_codes


def test_offline_collection_not_required_keeps_frozen_source() -> None:
    evidence = _collect(require_collection=False, transport=None)
    assert evidence.evidence_status == FreshPretradeGetStatusV1.NOT_REQUIRED_OFFLINE.value
    assert evidence.pretrade_source_kind == PRETRADE_SOURCE_FROZEN_OFFLINE
    assert evidence.get_performed is False


def test_valid_fresh_get_join_does_not_admit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = _bind_state_path(tmp_path, monkeypatch)
    StatePersistence(str(path)).save(KillSwitchState.ACTIVE)
    inputs = _join_live(transport=InjectedFreshGetTransportV1(), state_path=str(path))
    assert inputs.fresh_pretrade_get_status == FreshPretradeGetStatusV1.TRUSTED_PRESENT.value
    assert inputs.pretrade_source_kind == PRETRADE_SOURCE_FRESH_GET
    assert inputs.pretrade_freshness_status == PretradeFreshnessStatusV1.LIVE_FRESH.value
    assert inputs.live_enabled is False
    assert inputs.live_armed is False
    assert inputs.wire_send_permitted is False
    decision = evaluate_execution_admission_v1(inputs)
    assert decision.admitted is False
    assert "FRESH_PRETRADE_GET_MISSING" not in decision.reason_codes
    assert "FRESH_PRETRADE_GET_NOT_IMPLEMENTED" not in decision.reason_codes
    assert "LIVE_ENABLED_FALSE" in decision.reason_codes
    assert "WIRE_SEND_NOT_PERMITTED" in decision.reason_codes
    assert "LIVE_ARMED_FALSE" in decision.reason_codes


def test_owner_permit_absent_overall_deny(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    path = _bind_state_path(tmp_path, monkeypatch)
    StatePersistence(str(path)).save(KillSwitchState.ACTIVE)
    inputs = _join_live(
        transport=InjectedFreshGetTransportV1(),
        owner_go=None,
        state_path=str(path),
    )
    decision = evaluate_execution_admission_v1(inputs)
    assert decision.admitted is False
    assert "OWNER_ONE_SHOT_PERMIT_MISSING" in decision.reason_codes
    assert "MISSING_OWNER_AUTHORIZATION" in decision.reason_codes


def test_filegate_deny_overall_deny(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    path = _bind_state_path(tmp_path, monkeypatch)
    StatePersistence(str(path)).save(KillSwitchState.KILLED)
    inputs = _join_live(transport=InjectedFreshGetTransportV1(), state_path=str(path))
    assert inputs.durable_kill_switch_blocked is True
    decision = evaluate_execution_admission_v1(inputs)
    assert decision.admitted is False
    assert "DURABLE_FILEGATE_BLOCKS_TRADING" in decision.reason_codes


def test_standing_gates_false_overall_deny_even_with_trusted_get() -> None:
    decision = evaluate_execution_admission_v1(
        _live_inputs(
            pretrade_source_kind=PRETRADE_SOURCE_FRESH_GET,
            pretrade_freshness_status=PretradeFreshnessStatusV1.LIVE_FRESH.value,
            capital_risk_mode=CAPITAL_RISK_MODE_LIVE_ACCOUNT_BOUND,
            durable_kill_switch_evidence_status=(
                DurableKillSwitchEvidenceStatusV1.TRUSTED_PRESENT.value
            ),
            durable_kill_switch_blocked=False,
            owner_authorization_present=True,
            owner_one_shot_permit_status=OwnerOneShotPermitStatusV1.TRUSTED_PRESENT.value,
            fresh_pretrade_get_status=FreshPretradeGetStatusV1.TRUSTED_PRESENT.value,
            live_enabled=False,
            live_armed=False,
            wire_send_permitted=False,
        )
    )
    assert decision.admitted is False
    assert "LIVE_ENABLED_FALSE" in decision.reason_codes
    assert "LIVE_ARMED_FALSE" in decision.reason_codes
    assert "WIRE_SEND_NOT_PERMITTED" in decision.reason_codes
    assert "FRESH_PRETRADE_GET_NOT_IMPLEMENTED" not in decision.reason_codes


def test_fresh_get_success_alone_cannot_admit() -> None:
    decision = evaluate_execution_admission_v1(
        _live_inputs(
            pretrade_source_kind=PRETRADE_SOURCE_FRESH_GET,
            pretrade_freshness_status=PretradeFreshnessStatusV1.LIVE_FRESH.value,
            fresh_pretrade_get_status=FreshPretradeGetStatusV1.TRUSTED_PRESENT.value,
        )
    )
    assert decision.admitted is False
    assert "LIVE_ENABLED_FALSE" in decision.reason_codes


def test_fresh_get_cannot_override_other_gates(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = _bind_state_path(tmp_path, monkeypatch)
    StatePersistence(str(path)).save(KillSwitchState.KILLED)
    inputs = _join_live(transport=InjectedFreshGetTransportV1(), state_path=str(path))
    decision = evaluate_execution_admission_v1(inputs)
    assert decision.admitted is False
    assert inputs.fresh_pretrade_get_status == FreshPretradeGetStatusV1.TRUSTED_PRESENT.value
    assert "DURABLE_FILEGATE_BLOCKS_TRADING" in decision.reason_codes
    assert inputs.live_enabled is False
    assert LIVE_ENABLED is False


def test_live_path_with_injected_get_still_halts_before_wire_and_does_not_post(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = _bind_state_path(tmp_path, monkeypatch)
    StatePersistence(str(path)).save(KillSwitchState.ACTIVE)
    result, _ = _run(
        monkeypatch,
        _confirmed_replay_input(side="LONG"),
        mode="LIVE",
        fresh_pretrade_get_transport=InjectedFreshGetTransportV1(),
    )
    assert result.boundary is not None
    assert result.boundary.halt_before_wire is True
    assert result.boundary.admission is not None
    assert result.boundary.admission.admitted is False
    assert result.wire_send_occurred is False
    assert result.boundary.canary_http_invoked is False
    assert "HARD_STOP_BEFORE_WIRE" in result.reason_codes
    assert "FRESH_PRETRADE_GET_NOT_IMPLEMENTED" not in result.reason_codes
    assert "LIVE_ENABLED_FALSE" in result.reason_codes
    assert JOIN_SEAM_ID
    assert result.boundary.live_execution_port_constructed is False


def test_live_path_without_transport_denies_missing_get(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    result, _ = _run(
        monkeypatch,
        _confirmed_replay_input(side="LONG"),
        mode="LIVE",
    )
    assert result.boundary is not None
    assert result.boundary.admission is not None
    assert result.boundary.admission.admitted is False
    assert "FRESH_PRETRADE_GET_MISSING" in result.reason_codes
    assert result.wire_send_occurred is False


def test_runbook_and_spec_bind_fresh_get_without_live_arming() -> None:
    runbook = RUNBOOK.read_text(encoding="utf-8")
    spec = SPEC_PATH.read_text(encoding="utf-8")
    start = runbook.index("11.2.1.L FULL_CORE_FRESH_PRETRADE_RUNTIME_GET_SEAM")
    section = runbook[start : runbook.index("## 11.3 Autonomy state model", start)]
    assert "FRESH_PRETRADE_RUNTIME_GET_IMPLEMENTED=true" in section
    assert "LIVE_ENABLED=false" in section
    assert "LIVE_ARMED=false" in section
    assert "WIRE_SEND_PERMITTED=false" in section
    assert "POST_PERFORMED=false" in section
    assert "FULL_CORE_SYSTEM_E2E_PROVEN=false" in section
    assert "CURRENT_LIVE_CORE_PATH_PROVEN=false" in section
    assert "FRESH_GET_ALONE_CAN_ADMIT=false" in section
    assert "FRESH_GET_CAN_OVERRIDE_OTHER_GATES=false" in section
    assert "EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY=LIVE_ACCOUNT_BOUND_IMPLEMENTED" in section
    assert "docs_token:" in spec
    assert "DOCS_TOKEN_FULL_CORE_FRESH_PRETRADE_RUNTIME_GET_SEAM_V1" in spec
    prior = runbook[runbook.index("11.2.1.K FULL_CORE_OWNER_ONE_SHOT_TYPED_PERMIT_SEAM") : start]
    assert "OWNER_ONE_SHOT_TYPED_LIVE_EXECUTION_PERMIT_IMPLEMENTED=true" in prior
    assert (
        "EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY=FRESH_PRETRADE_RUNTIME_GET_IMPLEMENTED" in prior
    )
