"""Actual-venue Enter POST BWP tests — fakes only. No productive eea.okx.com default."""

from __future__ import annotations

import json
import socket
from pathlib import Path
from typing import Any

import pytest

from src.ops.full_core_live_path_composition_root_v1.checkout_independent_credential_concrete_backend_item_identity_v1 import (
    KEYCHAIN_ACCOUNT_ID,
    KEYCHAIN_SERVICE_ID,
)
from src.ops.full_core_live_path_composition_root_v1.checkout_independent_credential_os_native_store_acquisition_v1 import (
    FullCoreCheckoutIndependentOsNativeStoreAcquisitionError,
)
from src.ops.full_core_live_path_composition_root_v1.checkout_independent_credential_os_native_store_item_class_and_value_encoding_v1 import (
    KEYCHAIN_ITEM_CLASS,
)
from src.ops.full_core_live_path_composition_root_v1.final_order_envelope_v1 import (
    bind_final_order_envelope_from_venue_plan_v1,
)
from src.ops.full_core_live_path_composition_root_v1.models_v1 import VenuePlanCandidateV1
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_actual_venue_post_with_fresh_envelope_bound_single_use_permit_v1 import (
    EXPECTED_BASELINE_ORIGIN_MAIN_SHA,
    OWNER_GO,
    CurrentProductiveActualVenuePostError,
    execute_current_productive_actual_venue_post_with_fresh_envelope_bound_single_use_permit_v1,
    prove_pre_live_actual_venue_post_readiness_v1,
)
from src.governance.current_productive_actual_venue_post_admission_policy_v1 import (
    validate_actual_venue_post_admission_policy_v1,
)
from src.governance.governed_current_productive_actual_venue_post_admission_closure_v1 import (
    prove_governed_current_productive_actual_venue_post_admission_v1,
)

FAKE_OPAQUE = json.dumps(
    {"apiKey": "ak-test", "secretKey": "sk-test", "passphrase": "pp-test"},
    separators=(",", ":"),
).encode("utf-8")


class _FakeKeychainBackend:
    def copy_matching_generic_password_value_data_v1(
        self,
        *,
        service: str,
        account: str,
        item_class: str,
    ) -> bytes:
        assert service == KEYCHAIN_SERVICE_ID
        assert account == KEYCHAIN_ACCOUNT_ID
        assert item_class == KEYCHAIN_ITEM_CLASS
        return bytes(FAKE_OPAQUE)


class _TimeoutOpener:
    def open(self, req: Any, timeout: float = 0) -> Any:
        del req, timeout
        raise TimeoutError("bounded-test-timeout")


@pytest.fixture(autouse=True)
def _forbid_real_sockets(monkeypatch: pytest.MonkeyPatch) -> None:
    def _boom(*_args: Any, **_kwargs: Any) -> None:
        raise AssertionError("NETWORK_FORBIDDEN")

    monkeypatch.setattr(socket, "create_connection", _boom)
    monkeypatch.setattr(socket.socket, "connect", _boom)


def _envelope():
    plan = VenuePlanCandidateV1(
        instrument_id="okx_eea:linear_perpetual:0G:USDT:USDT:0g-usdt-swap",
        side="buy",
        quantity="1",
        order_type="market",
        td_mode="cross",
        reduce_only=False,
        clordid="pt-fc-enter-post-bwp-v1",
        venue_native_payload={
            "instId": "0G-USDT-SWAP",
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
        creation_epoch="2026-09-27T00:00:00Z",
    )


def test_policy_record_valid() -> None:
    root = Path(__file__).resolve().parents[2]
    result = validate_actual_venue_post_admission_policy_v1(repo_root=root)
    assert result.policy_valid is True
    assert result.baseline_origin_main_sha == EXPECTED_BASELINE_ORIGIN_MAIN_SHA
    assert prove_governed_current_productive_actual_venue_post_admission_v1(repo_root=root)


def test_pre_live_proof_without_owner_go_consume(tmp_path: Path) -> None:
    envelope = _envelope()
    backend = _FakeKeychainBackend()
    proof = prove_pre_live_actual_venue_post_readiness_v1(
        owner_go=OWNER_GO,
        baseline_origin_main_sha=EXPECTED_BASELINE_ORIGIN_MAIN_SHA,
        envelope=envelope,
        store_root=tmp_path,
        k1_backend=backend,
    )
    assert proof["OWNER_GO_CONSUMED"] == "false"
    assert proof["PRE_LIVE_PROOF_COMPLETE"] == "true"
    assert proof["SECRET_DISCLOSED"] == "false"


def test_execute_unknown_outcome_single_attempt_no_retry(tmp_path: Path) -> None:
    envelope = _envelope()
    backend = _FakeKeychainBackend()
    result = (
        execute_current_productive_actual_venue_post_with_fresh_envelope_bound_single_use_permit_v1(
            owner_go=OWNER_GO,
            baseline_origin_main_sha=EXPECTED_BASELINE_ORIGIN_MAIN_SHA,
            envelope=envelope,
            store_root=tmp_path,
            evidence_root=tmp_path / "evidence",
            perform_real_venue_post=True,
            k1_backend=backend,
            opener_factory=lambda: _TimeoutOpener(),
        )
    )
    assert result.post_outcome == "UNKNOWN_EXTERNAL_EFFECT_POSSIBLE"
    assert result.real_venue_post_attempted == "true"
    assert result.second_post_performed == "false"
    assert result.replay_attempt_blocked == "true"
    go_consume = json.loads(
        (
            tmp_path / "full_core_current_productive_actual_venue_post_owner_go_consume_v1.json"
        ).read_text()
    )
    assert go_consume["consumed"] is True
    permit_consume = json.loads(
        (tmp_path / "full_core_external_effect_permit_consume_v1.json").read_text()
    )
    assert permit_consume["durable_state"] == "SENT_INITIATED"
    assert "sk-test" not in json.dumps(permit_consume)


def test_owner_go_mismatch_fail_closed(tmp_path: Path) -> None:
    with pytest.raises(CurrentProductiveActualVenuePostError, match="OWNER_GO_MISMATCH"):
        prove_pre_live_actual_venue_post_readiness_v1(
            owner_go="WRONG",
            baseline_origin_main_sha=EXPECTED_BASELINE_ORIGIN_MAIN_SHA,
            envelope=_envelope(),
            store_root=tmp_path,
            k1_backend=_FakeKeychainBackend(),
        )


def test_stale_parent_baseline_sha_mismatch_fail_closed(tmp_path: Path) -> None:
    stale_parent = "04345330c0898ccf2682c88fd58c32f102a8001d"
    assert stale_parent != EXPECTED_BASELINE_ORIGIN_MAIN_SHA
    with pytest.raises(CurrentProductiveActualVenuePostError, match="BASELINE_SHA_MISMATCH"):
        prove_pre_live_actual_venue_post_readiness_v1(
            owner_go=OWNER_GO,
            baseline_origin_main_sha=stale_parent,
            envelope=_envelope(),
            store_root=tmp_path,
            k1_backend=_FakeKeychainBackend(),
        )
