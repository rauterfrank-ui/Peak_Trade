"""Regression proofs for post-first-real-attempt safety closure WP."""

from __future__ import annotations

import contextlib
import json
import sys
from pathlib import Path
from typing import Any
from urllib.error import HTTPError
from urllib.request import OpenerDirector

import pytest

from src.ops.full_core_live_path_composition_root_v1.current_productive_actual_venue_post_baseline_v1 import (
    EXPECTED_BASELINE_ORIGIN_MAIN_SHA,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_actual_venue_post_immediate_pre_mutation_freshness_v1 import (
    prove_immediate_pre_mutation_freshness_for_actual_venue_post_v1,
)
from src.ops.full_core_live_path_composition_root_v1.execution_admission_contract_v1 import (
    FreshPretradeGetStatusV1,
)
from src.ops.full_core_live_path_composition_root_v1.final_order_envelope_v1 import (
    bind_final_order_envelope_from_venue_plan_v1,
)
from src.ops.full_core_live_path_composition_root_v1.fresh_pretrade_runtime_get_v1 import (
    FreshPretradeGetTransportResultV1,
    TRANSPORT_CLASS_PRODUCTIVE_READ_ONLY_GET,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_productive_http_post_outcome_v1 import (
    HTTP_RESPONSE_RECEIVED,
    TRANSPORT_FAILURE_BEFORE_RESPONSE,
    UNKNOWN_EXTERNAL_STATE,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_productive_http_post_transport_v1 import (
    FullCoreProductiveHttpTradeOrderTransportV1,
)
from src.ops.full_core_live_path_composition_root_v1.models_v1 import VenuePlanCandidateV1
from src.ops.full_core_live_path_composition_root_v1.productive_read_only_get_transport_v1 import (
    READ_ONLY_EXACT_ORDER_LOOKUP_PATH,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_actual_venue_post_with_fresh_envelope_bound_single_use_permit_v1 import (
    OWNER_GO,
    CurrentProductiveActualVenuePostError,
    execute_current_productive_actual_venue_post_with_fresh_envelope_bound_single_use_permit_v1 as _execute_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_unknown_post_attempt_read_only_reconciliation_v1 import (
    CONFIRMED_ACCEPTED_WORKING,
    CONFIRMED_REJECTED,
    STILL_UNKNOWN,
    UnknownPostAttemptReadOnlyReconciliationResultV1,
    reconcile_unknown_post_attempt_read_only_v1,
)
from tests.ops._current_productive_29p_chain_integrity_test_helpers_v1 import (
    MockCurrentProductive29PIntegrityBackendV1,
)
from tests.ops.test_current_productive_actual_venue_post_with_fresh_envelope_bound_single_use_permit_v1 import (
    _FakeKeychainBackend,
    _TimeoutOpener,
    _envelope,
)
from tests.ops._pilot_guard_enter_post_test_helpers_v1 import (
    PilotGuardReadTransport,
    mandatory_new_risk_execute_kwargs,
)


from tests.ops._post_path_safety_fixtures_v1 import (
    activate_isolated_kill_switch_state_v1,
    execute_with_isolated_global_ledger_v1,
)

execute_current_productive_actual_venue_post_with_fresh_envelope_bound_single_use_permit_v1 = (
    execute_with_isolated_global_ledger_v1(_execute_v1)
)


@pytest.fixture(autouse=True)
def _active_kill_switch_state(
    monkeypatch: pytest.MonkeyPatch, tmp_path_factory: pytest.TempPathFactory
) -> None:
    activate_isolated_kill_switch_state_v1(
        monkeypatch, tmp_path_factory.mktemp("kill_switch_active")
    )


def _clean_post_integrity() -> MockCurrentProductive29PIntegrityBackendV1:
    sha = EXPECTED_BASELINE_ORIGIN_MAIN_SHA
    return MockCurrentProductive29PIntegrityBackendV1(origin_main=sha, head=sha, drift="")


class _TrustedReadTransport:
    """Minimal productive read-only GET double returning TRUSTED_PRESENT shapes."""

    def __init__(self) -> None:
        self.request_count = 0

    def get(self, *, endpoint: str, auth_required: bool, pretrade_decision_id: str):
        del auth_required, pretrade_decision_id
        self.request_count += 1
        path = str(endpoint).split("?", 1)[0]
        if "instruments" in path or "price-limit" in path:
            payload = {
                "code": "0",
                "data": [{"instId": "0G-USDT-SWAP", "instType": "SWAP", "state": "live"}],
            }
        elif "positions" in path:
            payload = {"code": "0", "data": []}
        elif path == READ_ONLY_EXACT_ORDER_LOOKUP_PATH:
            payload = {"code": "0", "data": []}
        else:
            payload = {"code": "0", "data": [{"instId": "ADA-USDT-SWAP", "tdMode": "cross"}]}
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


class _MissingReadTransport:
    def get(self, *, endpoint: str, auth_required: bool, pretrade_decision_id: str):
        del endpoint, auth_required, pretrade_decision_id
        return FreshPretradeGetTransportResultV1(
            get_performed=False,
            method="GET",
            endpoint="",
            http_status=0,
            payload=None,
            auth_header_sent=False,
            transport_class=TRANSPORT_CLASS_PRODUCTIVE_READ_ONLY_GET,
            venue_live_contact=False,
            historical_reuse=False,
            error_class="TRANSPORT_MISSING",
        )


class _HttpErrorOpener:
    def open(self, req: Any, timeout: float = 0) -> Any:
        del timeout
        raise HTTPError(
            url=str(getattr(req, "full_url", "")),
            code=400,
            msg="bad request",
            hdrs=None,
            fp=__import__("io").BytesIO(
                b'{"code":"1","msg":"All operations failed","data":[{"sCode":"51008","sMsg":"Order failed"}]}'
            ),
        )


def test_baseline_pin_is_post_6946_recorded_rebind() -> None:
    assert EXPECTED_BASELINE_ORIGIN_MAIN_SHA == "fca07afa1fa74a94cdecde3876c9c30ad79ba828"


def test_direct_envelope_path_without_read_transport_blocks_post(tmp_path: Path) -> None:
    with pytest.raises(CurrentProductiveActualVenuePostError, match="PRE_MUTATION_READ_TRANSPORT"):
        execute_current_productive_actual_venue_post_with_fresh_envelope_bound_single_use_permit_v1(
            owner_go=OWNER_GO,
            baseline_origin_main_sha=EXPECTED_BASELINE_ORIGIN_MAIN_SHA,
            envelope=_envelope(),
            store_root=tmp_path,
            evidence_root=tmp_path / "ev",
            perform_real_venue_post=True,
            k1_backend=_FakeKeychainBackend(),
            read_only_get_transport=None,
            execution_integrity_backend=_clean_post_integrity(),
        )
    assert not (
        tmp_path / "full_core_current_productive_actual_venue_post_owner_go_consume_v1.json"
    ).is_file()


def test_unknown_position_freshness_fail_closed() -> None:
    envelope = _envelope()
    proof = prove_immediate_pre_mutation_freshness_for_actual_venue_post_v1(
        envelope=envelope,
        read_only_get_transport=_MissingReadTransport(),
        pretrade_decision_id="test-pre-mutation",
    )
    assert proof.all_required_pre_post_gates_pass is False
    assert proof.position_state_fresh is False


def test_timeout_preserves_transport_failure_without_retry(tmp_path: Path) -> None:
    result = (
        execute_current_productive_actual_venue_post_with_fresh_envelope_bound_single_use_permit_v1(
            owner_go=OWNER_GO,
            baseline_origin_main_sha=EXPECTED_BASELINE_ORIGIN_MAIN_SHA,
            envelope=_envelope(),
            store_root=tmp_path,
            evidence_root=tmp_path / "ev",
            perform_real_venue_post=True,
            k1_backend=_FakeKeychainBackend(),
            opener_factory=lambda: _TimeoutOpener(),
            read_only_get_transport=PilotGuardReadTransport(avail_eq="10000"),
            execution_integrity_backend=_clean_post_integrity(),
            **mandatory_new_risk_execute_kwargs(tmp_path),
        )
    )
    assert result.post_outcome == "UNKNOWN_EXTERNAL_EFFECT_POSSIBLE"
    assert result.second_post_performed == "false"
    assert result.real_venue_post_attempted == "true"


def test_http_error_retains_status_without_inventing_acceptance() -> None:
    from src.ops.full_core_live_path_composition_root_v1.full_core_post_response_to_ack_mapper_v1 import (
        classify_full_core_post_result_v1,
    )
    from src.ops.full_core_live_path_composition_root_v1.full_core_productive_http_post_transport_v1 import (
        FullCoreTradeOrderPostResultV1,
    )

    result = FullCoreTradeOrderPostResultV1(
        post_attempted=True,
        venue_live_contact=True,
        method="POST",
        endpoint="/api/v5/trade/order",
        http_status=400,
        payload={
            "code": "1",
            "msg": "All operations failed",
            "data": [{"sCode": "51008", "sMsg": "Order failed", "clOrdId": "c1"}],
        },
        transport_class="TEST",
        unknown_outcome=True,
        outcome_phase=HTTP_RESPONSE_RECEIVED,
    )
    classified = classify_full_core_post_result_v1(
        result=result,
        sent_clordid="c1",
        submit_count=1,
    )
    assert result.http_status == 400
    assert classified["classification"] in {"UNKNOWN", "REJECTED"}
    assert classified["classification"] != "ACKNOWLEDGED"


def test_reconciliation_empty_does_not_confirm_not_accepted() -> None:
    recon = reconcile_unknown_post_attempt_read_only_v1(
        client_order_id="pt-test-clordid",
        instrument_id="ADA-USDT-SWAP",
        inst_type="SWAP",
        read_only_get_transport=_TrustedReadTransport(),
        pretrade_decision_id="recon-test",
    )
    assert recon.reconciliation_result == STILL_UNKNOWN
    assert recon.order_found == "false"
    assert recon.technical_get_error_present == "false"
    assert recon.technical_get_error_classes == ()


def test_exact_order_lookup_path_allowed_on_read_transport() -> None:
    assert READ_ONLY_EXACT_ORDER_LOOKUP_PATH == "/api/v5/trade/order"


class _ScenarioOrderReconTransport:
    """Deterministic GET double for cross-surface reconciliation contract tests."""

    def __init__(self, scenario: str, *, cl: str, inst: str) -> None:
        self.scenario = scenario
        self.cl = cl
        self.inst = inst

    def get(self, *, endpoint: str, auth_required: bool, pretrade_decision_id: str):
        del auth_required, pretrade_decision_id
        path = str(endpoint).split("?", 1)[0]

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

        def _fail(error_class: str) -> FreshPretradeGetTransportResultV1:
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
                error_class=error_class,
                data_safety_source_kind="REAL",
            )

        if self.scenario == "CONTRADICTORY_PENDING_LIVE_EXACT_CANCELED":
            if "orders-pending" in path:
                return _ok(
                    {
                        "code": "0",
                        "data": [
                            {
                                "clOrdId": self.cl,
                                "instId": self.inst,
                                "ordId": "ord-a",
                                "state": "live",
                                "sCode": "0",
                            }
                        ],
                    }
                )
            if path == READ_ONLY_EXACT_ORDER_LOOKUP_PATH:
                return _ok(
                    {
                        "code": "0",
                        "data": [
                            {
                                "clOrdId": self.cl,
                                "instId": self.inst,
                                "ordId": "ord-b",
                                "state": "canceled",
                                "sCode": "51008",
                            }
                        ],
                    }
                )
            return _ok({"code": "0", "data": []})

        if self.scenario == "CONSISTENT_WORKING":
            if "orders-pending" in path or path == READ_ONLY_EXACT_ORDER_LOOKUP_PATH:
                return _ok(
                    {
                        "code": "0",
                        "data": [
                            {
                                "clOrdId": self.cl,
                                "instId": self.inst,
                                "ordId": "ord-live-1",
                                "state": "live",
                                "sCode": "0",
                            }
                        ],
                    }
                )
            return _ok({"code": "0", "data": []})

        if self.scenario == "CONSISTENT_REJECTED":
            if (
                "orders-pending" in path
                or "orders-history" in path
                or path == READ_ONLY_EXACT_ORDER_LOOKUP_PATH
            ):
                return _ok(
                    {
                        "code": "0",
                        "data": [
                            {
                                "clOrdId": self.cl,
                                "instId": self.inst,
                                "ordId": "ord-rej-1",
                                "state": "canceled",
                                "sCode": "51008",
                            }
                        ],
                    }
                )
            return _ok({"code": "0", "data": []})

        if self.scenario == "EMPTY_SUCCESS":
            return _ok({"code": "0", "data": []})

        if self.scenario == "ALL_TECHNICAL_ERROR":
            return _fail("TRANSPORT_MISSING")

        if self.scenario == "PARTIAL_TECHNICAL_WITH_PENDING_HIT":
            if "orders-pending" in path:
                return _ok(
                    {
                        "code": "0",
                        "data": [
                            {
                                "clOrdId": self.cl,
                                "instId": self.inst,
                                "ordId": "ord-live-2",
                                "state": "live",
                                "sCode": "0",
                            }
                        ],
                    }
                )
            if "orders-history" in path:
                return _fail("TIMEOUT")
            return _ok({"code": "0", "data": []})

        if self.scenario == "MISMATCHED_INST_ID":
            if "orders-pending" in path:
                return _ok(
                    {
                        "code": "0",
                        "data": [
                            {
                                "clOrdId": self.cl,
                                "instId": "OTHER-USDT-SWAP",
                                "ordId": "ord-x",
                                "state": "live",
                                "sCode": "0",
                            }
                        ],
                    }
                )
            return _ok({"code": "0", "data": []})

        if self.scenario == "ORDER_SURFACE_TIMEOUT_ONLY":
            if "orders-history" in path:
                return _fail("TIMEOUT")
            return _ok({"code": "0", "data": []})

        if self.scenario == "POSITIONS_FAIL_CONSISTENT_WORKING":
            if "account/positions" in path:
                return _fail("TRANSPORT_MISSING")
            if "orders-pending" in path or path == READ_ONLY_EXACT_ORDER_LOOKUP_PATH:
                return _ok(
                    {
                        "code": "0",
                        "data": [
                            {
                                "clOrdId": self.cl,
                                "instId": self.inst,
                                "ordId": "ord-live-pos-fail",
                                "state": "live",
                                "sCode": "0",
                            }
                        ],
                    }
                )
            return _ok({"code": "0", "data": []})

        if self.scenario == "MULTI_SURFACE_TECHNICAL_ERRORS":
            if "orders-history" in path:
                return _fail("TIMEOUT")
            if "account/positions" in path:
                return _fail("TRANSPORT_MISSING")
            return _ok({"code": "0", "data": []})

        raise AssertionError(f"UNKNOWN_SCENARIO:{self.scenario}")


def _recon_with_scenario(scenario: str) -> UnknownPostAttemptReadOnlyReconciliationResultV1:
    cl = "pt-scenario-clordid"
    inst = "ADA-USDT-SWAP"
    return reconcile_unknown_post_attempt_read_only_v1(
        client_order_id=cl,
        instrument_id=inst,
        inst_type="SWAP",
        read_only_get_transport=_ScenarioOrderReconTransport(scenario, cl=cl, inst=inst),
        pretrade_decision_id="contract-test",
    )


def test_q2_contradictory_pending_and_exact_lookup_stays_unknown() -> None:
    recon = _recon_with_scenario("CONTRADICTORY_PENDING_LIVE_EXACT_CANCELED")
    assert recon.reconciliation_result == STILL_UNKNOWN
    assert recon.external_effect_confirmed == "false"
    assert recon.reconciliation_result != CONFIRMED_ACCEPTED_WORKING


def test_q2_consistent_working_evidence_preserved() -> None:
    recon = _recon_with_scenario("CONSISTENT_WORKING")
    assert recon.reconciliation_result == CONFIRMED_ACCEPTED_WORKING
    assert recon.external_effect_confirmed == "true"


def test_q2_consistent_terminal_reject_preserved() -> None:
    recon = _recon_with_scenario("CONSISTENT_REJECTED")
    assert recon.reconciliation_result == CONFIRMED_REJECTED
    assert recon.external_effect_confirmed == "false"


def test_q3_empty_success_not_technical_error() -> None:
    recon = _recon_with_scenario("EMPTY_SUCCESS")
    assert recon.reconciliation_result == STILL_UNKNOWN
    assert recon.technical_get_error_present == "false"
    assert recon.technical_get_error_classes == ()


def test_q3_technical_get_error_flagged() -> None:
    recon = _recon_with_scenario("ALL_TECHNICAL_ERROR")
    assert recon.reconciliation_result == STILL_UNKNOWN
    assert recon.technical_get_error_present == "true"
    assert "TRANSPORT_MISSING" in recon.technical_get_error_classes


def test_q3_partial_technical_error_blocks_confirmation() -> None:
    recon = _recon_with_scenario("PARTIAL_TECHNICAL_WITH_PENDING_HIT")
    assert recon.reconciliation_result == STILL_UNKNOWN
    assert recon.external_effect_confirmed == "false"
    assert recon.technical_get_error_present == "true"
    assert "TIMEOUT" in recon.technical_get_error_classes


def test_q2_mismatched_inst_id_not_merged() -> None:
    recon = _recon_with_scenario("MISMATCHED_INST_ID")
    assert recon.order_found == "false"
    assert recon.reconciliation_result == STILL_UNKNOWN


def test_t1_all_gets_success_technical_error_fields_absent() -> None:
    recon = _recon_with_scenario("EMPTY_SUCCESS")
    assert recon.technical_get_error_present == "false"
    assert recon.technical_get_error_classes == ()


def test_t2_order_relevant_get_timeout_flags_error_conservative_recon() -> None:
    recon = _recon_with_scenario("ORDER_SURFACE_TIMEOUT_ONLY")
    assert recon.technical_get_error_present == "true"
    assert "TIMEOUT" in recon.technical_get_error_classes
    assert recon.reconciliation_result == STILL_UNKNOWN
    assert recon.external_effect_confirmed == "false"


def test_t3_positions_only_get_failure_flags_error_without_changing_order_adjudication() -> None:
    recon = _recon_with_scenario("POSITIONS_FAIL_CONSISTENT_WORKING")
    assert recon.technical_get_error_present == "true"
    assert "TRANSPORT_MISSING" in recon.technical_get_error_classes
    assert recon.reconciliation_result == CONFIRMED_ACCEPTED_WORKING
    assert recon.external_effect_confirmed == "true"


def test_t4_multiple_technical_errors_sorted_deterministically() -> None:
    recon = _recon_with_scenario("MULTI_SURFACE_TECHNICAL_ERRORS")
    assert recon.technical_get_error_present == "true"
    assert recon.technical_get_error_classes == ("TIMEOUT", "TRANSPORT_MISSING")


def test_t5_q2_conflict_tests_remain_pass() -> None:
    contradictory = _recon_with_scenario("CONTRADICTORY_PENDING_LIVE_EXACT_CANCELED")
    assert contradictory.reconciliation_result == STILL_UNKNOWN
    assert contradictory.external_effect_confirmed == "false"
    working = _recon_with_scenario("CONSISTENT_WORKING")
    assert working.reconciliation_result == CONFIRMED_ACCEPTED_WORKING


def test_cli_output_includes_structured_technical_error_fields(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    import scripts.ops.run_current_productive_unknown_post_attempt_read_only_reconciliation_v1 as cli_mod

    sample = UnknownPostAttemptReadOnlyReconciliationResultV1(
        client_order_id="cli-cl",
        read_only_requests_performed=5,
        order_found="false",
        venue_order_id="",
        order_state="",
        reconciliation_result=STILL_UNKNOWN,
        external_effect_confirmed="false",
        correlated_fill_count=0,
        exact_order_lookup_performed=True,
        surfaces_summary=("orders_pending:http=0:rows=0:err=TIMEOUT",),
        technical_get_error_present="true",
        technical_get_error_classes=("TIMEOUT",),
    )

    class _FakeSession:
        signing_handle = object()

    @contextlib.contextmanager
    def _fake_session(**_kwargs: Any):
        yield _FakeSession()

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run",
            "--client-order-id",
            "cli-cl",
            "--instrument-id",
            "ADA-USDT-SWAP",
        ],
    )

    from src.ops.full_core_live_path_composition_root_v1 import (
        current_productive_k1_opaque_signing_handle_from_macos_os_native_store_v1 as k1_mod,
    )
    from src.ops.full_core_live_path_composition_root_v1 import (
        current_productive_k1_runtime_binding_to_one_shot_actual_venue_post_pre_live_boundary_v1 as bind_mod,
    )
    from src.ops.full_core_live_path_composition_root_v1 import (
        productive_read_only_get_transport_v1 as transport_mod,
    )
    from src.ops.governed_productive_account_equity_authority_producer_v1 import (
        current_productive_unknown_post_attempt_read_only_reconciliation_v1 as recon_mod,
    )

    monkeypatch.setattr(
        k1_mod, "open_current_productive_k1_opaque_signing_handle_session_v1", _fake_session
    )
    monkeypatch.setattr(
        bind_mod, "resolve_macos_security_framework_k1_lookup_backend_v1", lambda **_k: object()
    )
    monkeypatch.setattr(
        transport_mod, "FullCoreProductiveReadOnlyGetTransportV1", lambda **_k: object()
    )
    monkeypatch.setattr(
        recon_mod, "reconcile_unknown_post_attempt_read_only_v1", lambda **_k: sample
    )

    assert cli_mod._main() == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["TECHNICAL_GET_ERROR_PRESENT"] == "true"
    assert payload["TECHNICAL_GET_ERROR_CLASSES"] == ["TIMEOUT"]
