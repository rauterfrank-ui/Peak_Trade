"""Regression proofs for post-first-real-attempt safety closure WP."""

from __future__ import annotations

import json
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
    execute_current_productive_actual_venue_post_with_fresh_envelope_bound_single_use_permit_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_unknown_post_attempt_read_only_reconciliation_v1 import (
    STILL_UNKNOWN,
    reconcile_unknown_post_attempt_read_only_v1,
)
from tests.ops.test_current_productive_actual_venue_post_with_fresh_envelope_bound_single_use_permit_v1 import (
    _FakeKeychainBackend,
    _TimeoutOpener,
    _envelope,
)


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


def test_baseline_pin_is_post_6930_merge_currency() -> None:
    assert EXPECTED_BASELINE_ORIGIN_MAIN_SHA == "cf3aa15f098827a9e60de8eb84e5bdd9eb54cca2"


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
            read_only_get_transport=_TrustedReadTransport(),
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


def test_exact_order_lookup_path_allowed_on_read_transport() -> None:
    assert READ_ONLY_EXACT_ORDER_LOOKUP_PATH == "/api/v5/trade/order"
