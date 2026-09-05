"""STEP-29P capital/risk admissibility to pre-construction. No POST. No wire."""

from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path

import pytest

from src.governance import capital_risk_sizing_v1 as sizing
from src.ops.full_core_live_path_composition_root_v1.capital_admission_v1 import (
    evaluate_capital_admission_v1,
    live_venue_capital_may_bind_step_29p_v1,
)
from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    FORBIDDEN_IMPORT_TOKENS,
    LIVE_ARMED,
    LIVE_ENABLED,
    RISK_ADMISSIBLE_DOES_NOT_IMPLY_LIVE_ARMED,
    RISK_ADMISSIBLE_DOES_NOT_IMPLY_LIVE_ENABLED,
    RISK_ADMISSIBLE_DOES_NOT_IMPLY_PORT_CONSTRUCTION,
    RISK_ADMISSIBLE_DOES_NOT_IMPLY_WIRE_SEND,
    STEP_29P_CAPITAL_RISK_ADMISSIBILITY_IMPLEMENTED,
    WIRE_SEND_PERMITTED,
)
from src.ops.full_core_live_path_composition_root_v1.execution_admission_contract_v1 import (
    ADMISSION_CONTEXT_LIVE,
    CAPITAL_AUTHORITY_OBSERVED_NOT_RISK_ADMISSIBLE,
    CAPITAL_AUTHORITY_RISK_ADMISSIBLE,
    CAPITAL_RISK_MODE_LIVE_ACCOUNT_BOUND,
    CapitalAdmissionStatusV1,
    DurableKillSwitchEvidenceStatusV1,
    FreshPretradeGetStatusV1,
    LiveAccountBoundStatusV1,
    OwnerOneShotPermitStatusV1,
    PRETRADE_SOURCE_FRESH_GET,
    PretradeFreshnessStatusV1,
    evaluate_execution_admission_v1,
)
from src.ops.full_core_live_path_composition_root_v1.live_admission_gap_dag_v1 import (
    EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY,
    FRESH_EXTERNAL_EVIDENCE_REQUIRED_FOR_NEXT_SLICE,
    MAX_SAFE_REPO_INTERNAL_NEXT_SLICE,
    gap_node_v1,
)
from src.ops.full_core_live_path_composition_root_v1.live_execution_port_construction_admission_v1 import (
    evaluate_live_execution_port_construction_admission_v1,
    prove_live_execution_port_not_constructible_v1,
)
from src.ops.full_core_live_path_composition_root_v1.overclaim_guards_v1 import (
    prove_package_does_not_import_wire_surfaces_v1,
)
from src.ops.full_core_live_path_composition_root_v1.step_29p_capital_risk_admissibility_v1 import (
    RISK_EQUITY_DIMENSION,
    Step29PCapitalRiskAdmissibilityClaimV1,
    evaluate_step_29p_capital_risk_admissibility_v1,
    persist_class_fields_v1,
)
from src.ops.full_core_live_path_composition_root_v1.treasury_interference_proof_v1 import (
    prove_treasury_interference_absent_v1,
)
from src.ops.full_core_step_29p_fresh_venue_evidence_v1.constants_v1 import (
    AUTHORIZED_HOST,
    BOUND_INSTRUMENT_ID,
    EMPTY_DATA_IS_ZERO,
    EXPECTED_ORIGIN_MAIN_SHA,
    OWNER_GO,
    USER_AGENT_STEP_29P_FRESH_GET,
)
from src.ops.full_core_step_29p_fresh_venue_evidence_v1.execute_v1 import (
    execute_step_29p_fresh_venue_evidence_gets_v1,
)
from src.ops.full_core_step_29p_fresh_venue_evidence_v1.requirement_matrix_v1 import (
    FRESH_EVIDENCE_REQUIREMENT_MATRIX,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.http_client_v1 import (
    RecordingFakeCanaryTransportV1,
)
from src.risk_layer.kill_switch.persistence import StatePersistence
from src.risk_layer.kill_switch.state import KillSwitchState
from tests.governance.test_capital_risk_sizing_v1 import _evaluate_chain
from tests.ops.test_full_core_execution_admission_contract_v1 import _live_inputs
from tests.ops.test_full_core_live_account_bound_and_remaining_closeout_v1 import (
    _TEST_INST,
    _TEST_UID,
    _bind_state_path,
    _bound_transport,
    _identity_payloads,
)
from tests.ops.test_full_core_live_enabled_standing_admission_seam_v1 import (
    _all_modelable_live_gates_true,
)
from tests.ops.test_full_core_live_path_composition_root_v1 import _run
from tests.ops.test_full_core_pre_live_capital_admission_contract_v1 import _claim
from tests.trading.master_v2.test_integrated_offline_trading_logic_replay_v1 import (
    _INSTRUMENT,
)
from tests.trading.master_v2.test_master_v2_integrated_replay_safety_before_intent_restore_contract_v1 import (
    _confirmed_replay_input,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
RUNBOOK = REPO_ROOT / "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md"
SPEC_PATH = (
    REPO_ROOT / "docs/ops/specs/FULL_CORE_STEP_29P_RISK_ADMISSIBILITY_PRE_CONSTRUCTION_V1.md"
)


def _okx(data: object) -> bytes:
    return json.dumps({"code": "0", "msg": "", "data": data}).encode("utf-8")


def _capital(**overrides):
    payload = {
        "claim": _claim(),
        "expected_account_identity": _TEST_UID,
        "expected_instrument_id": _TEST_INST,
        "admission_context": ADMISSION_CONTEXT_LIVE,
    }
    payload.update(overrides)
    return evaluate_capital_admission_v1(**payload)


def _complete_claim(**overrides) -> Step29PCapitalRiskAdmissibilityClaimV1:
    payload = {
        "fresh_pretrade_get_status": FreshPretradeGetStatusV1.TRUSTED_PRESENT.value,
        "live_account_bound_status": LiveAccountBoundStatusV1.TRUSTED_PRESENT.value,
        "expected_instrument_id": _TEST_INST,
        "observed_instrument_id": _TEST_INST,
        "expected_currency": "USDC",
        "observed_currency": "USDC",
        "equity_dimension": RISK_EQUITY_DIMENSION,
        "typed_account_equity_raw": "10000",
        "typed_account_equity_source_field": "injected_running_account_equity",
        "fresh_evidence_fetched": True,
        "fresh_evidence_validated": True,
    }
    payload.update(overrides)
    return Step29PCapitalRiskAdmissibilityClaimV1(**payload)


def test_flags_and_dag_next_pointer() -> None:
    assert STEP_29P_CAPITAL_RISK_ADMISSIBILITY_IMPLEMENTED is True
    assert LIVE_ENABLED is False
    assert LIVE_ARMED is False
    assert WIRE_SEND_PERMITTED is False
    assert RISK_ADMISSIBLE_DOES_NOT_IMPLY_LIVE_ENABLED is True
    assert RISK_ADMISSIBLE_DOES_NOT_IMPLY_LIVE_ARMED is True
    assert RISK_ADMISSIBLE_DOES_NOT_IMPLY_WIRE_SEND is True
    assert RISK_ADMISSIBLE_DOES_NOT_IMPLY_PORT_CONSTRUCTION is True
    assert EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY == "STEP_29P_EQUITY_DIMENSION_BINDING_MISSING"
    assert MAX_SAFE_REPO_INTERNAL_NEXT_SLICE == (
        "NO_FURTHER_REPO_INTERNAL_SLICE_PRE_CONSTRUCTION_BOUNDARY_REACHED"
    )
    assert FRESH_EXTERNAL_EVIDENCE_REQUIRED_FOR_NEXT_SLICE is False
    node = gap_node_v1("STEP_29P_CAPITAL_RISK_ADMISSIBILITY")
    assert node.implementation_status == "JOINED_TYPED_EVIDENCE_FAIL_CLOSED"
    assert node.wiring_authorized is True
    assert node.standing_live_gates_would_change is False
    port = gap_node_v1("LiveExecutionPort")
    assert port.implementation_status == "CONSTRUCTION_FORBIDDEN"
    assert "STEP_29P_CAPITAL_RISK_ADMISSIBILITY" in port.dependencies


def test_stale_missing_wrong_instrument_wrong_currency_denied() -> None:
    capital = _capital()
    stale = evaluate_step_29p_capital_risk_admissibility_v1(
        capital=capital,
        claim=_complete_claim(fresh_pretrade_get_status=FreshPretradeGetStatusV1.STALE.value),
    )
    assert stale.risk_admissible is False
    assert "FRESH_EVIDENCE_GET_NOT_TRUSTED" in stale.reason_codes
    missing = evaluate_step_29p_capital_risk_admissibility_v1(capital=capital, claim=None)
    assert missing.risk_admissible is False
    assert "FRESH_EVIDENCE_MISSING" in missing.reason_codes
    wrong_inst = evaluate_step_29p_capital_risk_admissibility_v1(
        capital=capital,
        claim=_complete_claim(observed_instrument_id="BTC-USD_UM_XPERP-310404"),
    )
    assert wrong_inst.risk_admissible is False
    assert "STEP_29P_WRONG_INSTRUMENT" in wrong_inst.reason_codes
    wrong_ccy = evaluate_step_29p_capital_risk_admissibility_v1(
        capital=capital, claim=_complete_claim(observed_currency="USDT")
    )
    assert wrong_ccy.risk_admissible is False
    assert "STEP_29P_WRONG_CURRENCY" in wrong_ccy.reason_codes


def test_forbidden_okx_equity_field_cannot_bind() -> None:
    capital = _capital()
    result = evaluate_step_29p_capital_risk_admissibility_v1(
        capital=capital,
        claim=_complete_claim(typed_account_equity_source_field="details.availEq"),
    )
    assert result.risk_admissible is False
    assert "CAPITAL_ADMISSION_OPTIMISTIC_FIELD_FALLBACK" in result.reason_codes
    assert result.equity_dimension_bound is False


def test_incomplete_conjunction_false_complete_conjunction_true() -> None:
    capital = _capital()
    incomplete = evaluate_step_29p_capital_risk_admissibility_v1(
        capital=capital, claim=_complete_claim(equity_dimension="")
    )
    assert incomplete.risk_admissible is False
    assert "STEP_29P_EQUITY_DIMENSION_UNBOUND" in incomplete.reason_codes
    complete = evaluate_step_29p_capital_risk_admissibility_v1(
        capital=capital, claim=_complete_claim()
    )
    assert complete.risk_admissible is True
    assert complete.live_enabled is False
    assert complete.live_armed is False
    assert complete.wire_send_permitted is False
    assert complete.standing_gates_satisfied is False
    assert complete.port_constructed is False
    persist = persist_class_fields_v1(complete)
    assert persist["STEP_29P_RISK_ADMISSIBLE"] is True
    assert persist["STANDING_GATES_SATISFIED"] is False
    assert persist["PORT_CONSTRUCTED"] is False
    assert persist["WIRE_SEND_EXECUTED"] is False
    chain = _evaluate_chain(account_equity=Decimal("10000"))
    assert chain.outcome is sizing.CapitalRiskSizingOutcome.PASS
    assert chain.final_quantity > 0
    assert live_venue_capital_may_bind_step_29p_v1(capital, admissibility=complete) is True


def test_no_hidden_unconditional_true_bypass() -> None:
    capital = _capital()
    result = evaluate_step_29p_capital_risk_admissibility_v1(capital=capital, claim=None)
    assert result.risk_admissible is False
    assert "LIVE_VENUE_CAPITAL_NOT_ADMITTED_TO_STEP_29P" in result.reason_codes


def test_venue_failure_classifications(tmp_path: Path) -> None:
    transport = RecordingFakeCanaryTransportV1(
        status_code=401,
        body=b'{"code":"50110","msg":"IP not in whitelist","data":[]}',
    )
    result = execute_step_29p_fresh_venue_evidence_gets_v1(
        owner_go=OWNER_GO,
        origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
        evidence_root=tmp_path,
        transport=transport,
    )
    assert result["summary"]["STEP_29P_RISK_ADMISSIBLE"] is False
    assert result["MUTATING_NETWORK_CALL_OCCURRED"] is False
    assert result["NETWORK_GET_TO_OKX_OCCURRED"] is False
    nonzero = RecordingFakeCanaryTransportV1(
        status_code=200, body=b'{"code":"1","msg":"fail","data":[]}'
    )
    denied = execute_step_29p_fresh_venue_evidence_gets_v1(
        owner_go=OWNER_GO,
        origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
        evidence_root=tmp_path / "nonzero",
        transport=nonzero,
    )
    assert denied["summary"]["STEP_29P_RISK_ADMISSIBLE"] is False
    malformed = RecordingFakeCanaryTransportV1(status_code=200, body=b"not-json")
    bad = execute_step_29p_fresh_venue_evidence_gets_v1(
        owner_go=OWNER_GO,
        origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
        evidence_root=tmp_path / "malformed",
        transport=malformed,
    )
    assert bad["summary"]["STEP_29P_RISK_ADMISSIBLE"] is False


def test_empty_positions_is_not_zero(tmp_path: Path) -> None:
    transport = RecordingFakeCanaryTransportV1(
        status_code=200,
        body=_okx([]),
        bodies_by_endpoint={
            "/api/v5/account/positions": _okx([]),
            "/api/v5/public/instruments": _okx(
                [{"instId": BOUND_INSTRUMENT_ID, "state": "live", "ctVal": "1"}]
            ),
            "/api/v5/public/price-limit": _okx(
                [{"instId": BOUND_INSTRUMENT_ID, "buyLmt": "2", "sellLmt": "1"}]
            ),
            "/api/v5/market/ticker": _okx([{"instId": BOUND_INSTRUMENT_ID, "last": "1.23"}]),
            "/api/v5/account/max-size": _okx([{"instId": BOUND_INSTRUMENT_ID, "availBuy": "1"}]),
            "/api/v5/account/leverage-info": _okx(
                [{"instId": BOUND_INSTRUMENT_ID, "lever": "3", "mgnMode": "cross"}]
            ),
            "/api/v5/account/config": _okx([{"uid": "1", "acctLv": "2", "posMode": "net_mode"}]),
            "/api/v5/account/balance": _okx([{"details": [{"ccy": "USDC", "availEq": "10"}]}]),
        },
    )
    result = execute_step_29p_fresh_venue_evidence_gets_v1(
        owner_go=OWNER_GO,
        origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
        evidence_root=tmp_path,
        transport=transport,
    )
    positions = [
        item for item in result["snapshot"]["REQUESTS"] if item["FETCH_GROUP"] == "positions"
    ][0]
    assert positions["NORMALIZED"]["ROW_STATUS"] == "NOT_OBSERVED"
    assert positions["NORMALIZED"]["EMPTY_DATA_IS_ZERO"] is False
    assert EMPTY_DATA_IS_ZERO is False
    assert result["summary"]["STEP_29P_RISK_ADMISSIBLE"] is False
    balance = [item for item in result["snapshot"]["REQUESTS"] if item["FETCH_GROUP"] == "balance"][
        0
    ]
    assert balance["NORMALIZED"]["MAPPED_TO_STEP_29P_ACCOUNT_EQUITY"] is False


def test_gate_independence_when_risk_admissible() -> None:
    capital = _capital()
    complete = evaluate_step_29p_capital_risk_admissibility_v1(
        capital=capital, claim=_complete_claim()
    )
    assert complete.risk_admissible is True
    decision = evaluate_execution_admission_v1(
        _all_modelable_live_gates_true(step_29p_risk_admissible=True)
    )
    assert decision.admitted is False
    assert "LIVE_VENUE_CAPITAL_NOT_ADMITTED_TO_STEP_29P" not in decision.reason_codes
    assert LIVE_ENABLED is False
    assert LIVE_ARMED is False
    assert WIRE_SEND_PERMITTED is False
    construction = evaluate_live_execution_port_construction_admission_v1(
        admission=decision,
        live_enabled=True,
        live_armed=True,
        wire_send_permitted=True,
        attempt_with_credentials=False,
        attempt_network_session=False,
    )
    assert construction.constructible is False
    assert construction.constructed is False
    proof = prove_live_execution_port_not_constructible_v1()
    assert proof["constructed"] is False


def test_forged_risk_admissible_without_29p_contract_denied() -> None:
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
            live_account_bound_status=LiveAccountBoundStatusV1.TRUSTED_PRESENT.value,
            capital_admission_status=CapitalAdmissionStatusV1.TRUSTED_PRESENT.value,
            capital_authority_class=CAPITAL_AUTHORITY_RISK_ADMISSIBLE,
            step_29p_risk_admissible=False,
            live_enabled=False,
            live_armed=False,
            wire_send_permitted=False,
        )
    )
    assert decision.admitted is False
    assert "FORGED_RISK_ADMISSIBLE_WITHOUT_29P_CONTRACT" in decision.reason_codes
    assert "CAPITAL_ADMISSION_RISK_ADMISSIBLE_POLICY_FROZEN" not in decision.reason_codes


def test_treasury_interference_proof_pass() -> None:
    proof = prove_treasury_interference_absent_v1()
    assert proof["ok"] is True
    assert proof["TREASURY_INTERFERENCE_PROOF"] == "PASS"
    assert proof["TREASURY_HAS_PRODUCTIVE_CALL_GRAPH_REACHABILITY"] is False
    assert proof["TREASURY_IS_IN_CURRENT_LIVE_ADMISSION_DAG"] is False
    assert proof["TREASURY_CAN_OVERRIDE_STEP_29P_RISK_ADMISSION"] is False
    assert proof["TREASURY_CAN_OVERRIDE_WIRE_SEND_PERMISSION"] is False
    assert proof["TREASURY_CAN_CONSTRUCT_LIVE_EXECUTION_PORT"] is False
    assert proof["TREASURY_CAN_MOVE_FUNDS_FROM_CURRENT_FULL_CORE_PATH"] is False
    assert proof["TREASURY_MUTATION_AUTHORIZED"] is False
    from src.ops.treasury_phase_1_offline_contracts_v1.constants_v1 import (
        TREASURY_MUTATION_REACHABLE_FROM_TRADING,
        TREASURY_PHASE_1_CAN_MINT_RISK_ADMISSIBLE_CAPITAL,
        TREASURY_PHASE_1_CAN_MOVE_FUNDS,
        TREASURY_PHASE_2_STATUS,
    )

    assert TREASURY_MUTATION_REACHABLE_FROM_TRADING is False
    assert TREASURY_PHASE_1_CAN_MINT_RISK_ADMISSIBLE_CAPITAL is False
    assert TREASURY_PHASE_1_CAN_MOVE_FUNDS is False
    assert TREASURY_PHASE_2_STATUS == "NOT_STARTED"


def test_full_core_package_still_forbids_canary_http_import() -> None:
    proof = prove_package_does_not_import_wire_surfaces_v1()
    assert proof["ok"] is True
    assert "LiveCanaryHttpClientV1" in FORBIDDEN_IMPORT_TOKENS
    assert USER_AGENT_STEP_29P_FRESH_GET != ""
    assert AUTHORIZED_HOST == "eea.okx.com"


def test_zero_submit_wire_port_on_full_core_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = _bind_state_path(tmp_path, monkeypatch)
    StatePersistence(str(path)).save(KillSwitchState.ACTIVE)
    result, _ = _run(
        monkeypatch,
        _confirmed_replay_input(side="LONG"),
        mode="LIVE",
        fresh_pretrade_get_transport=_bound_transport(
            payloads=_identity_payloads(instrument_id=_INSTRUMENT)
        ),
        expected_account_identity=_TEST_UID,
        capital_admission_claim=_claim(instrument_id=_INSTRUMENT),
        step_29p_risk_claim=_complete_claim(
            expected_instrument_id=_INSTRUMENT,
            observed_instrument_id=_INSTRUMENT,
        ),
        attempt_wire_send=True,
        attempt_construct_live_port=True,
    )
    assert result.boundary is not None
    assert result.boundary.halt_before_wire is True
    assert result.wire_send_occurred is False
    assert result.boundary.live_execution_port_constructed is False
    assert result.boundary.admission is not None
    assert result.boundary.admission.admitted is False


def test_requirement_matrix_covers_required_gets_and_unresolved_equity() -> None:
    ids = {str(row["REQUIREMENT"]) for row in FRESH_EVIDENCE_REQUIREMENT_MATRIX}
    assert "AVAILABLE_MARGIN" in ids
    assert "MARGIN_MODE" in ids
    assert "TICKER_LAST_FOR_MAX_SIZE_QUERY_PX" in ids
    assert RISK_EQUITY_DIMENSION in ids
    equity = [
        row
        for row in FRESH_EVIDENCE_REQUIREMENT_MATRIX
        if row["REQUIREMENT"] == RISK_EQUITY_DIMENSION
    ][0]
    assert equity["ENDPOINT"] == "NONE_CANONICAL_VENUE_MAPPING"


def test_runbook_and_spec_bind_without_construction_lift() -> None:
    runbook = RUNBOOK.read_text(encoding="utf-8")
    spec = SPEC_PATH.read_text(encoding="utf-8")
    start = runbook.index("11.2.1.Q FULL_CORE_STEP_29P_RISK_ADMISSIBILITY_PRE_CONSTRUCTION")
    section = runbook[start : runbook.index("## 11.3 Autonomy state model", start)]
    assert "STEP_29P_CAPITAL_RISK_ADMISSIBILITY_IMPLEMENTED=true" in section
    assert "STEP_29P_RISK_ADMISSIBLE=false" in section
    assert "CONSTRUCT_LIVE_EXECUTION_PORT_V1=FORBIDDEN_IN_CAP_11_1" in section
    assert "CAP_11_1_CONSTRUCTION_POLICY_LIFT_AUTHORIZED=false" in section
    assert "CAP_7_2_HOST_JOIN_TO_LIVE_EXECUTION_PORT_AUTHORIZED=false" in section
    assert "LIVE_ENABLED=false" in section
    assert "LIVE_ARMED=false" in section
    assert "WIRE_SEND_PERMITTED=false" in section
    assert "FRESH_EVIDENCE_FETCHED" in section
    assert "PORT_CONSTRUCTED" in section
    assert "docs_token:" in spec
    assert "DOCS_TOKEN_FULL_CORE_STEP_29P_RISK_ADMISSIBILITY_PRE_CONSTRUCTION_V1" in spec
    assert CAPITAL_AUTHORITY_OBSERVED_NOT_RISK_ADMISSIBLE == "OBSERVED_NOT_RISK_ADMISSIBLE"
