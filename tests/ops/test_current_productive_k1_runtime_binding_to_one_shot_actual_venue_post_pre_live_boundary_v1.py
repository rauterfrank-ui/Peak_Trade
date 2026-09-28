"""K1 runtime binding → one-shot POST pre-live boundary (fake Keychain only)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.ops.full_core_live_path_composition_root_v1.checkout_independent_credential_concrete_backend_item_identity_v1 import (
    KEYCHAIN_ACCOUNT_ID,
    KEYCHAIN_SERVICE_ID,
)
from src.ops.full_core_live_path_composition_root_v1.checkout_independent_credential_os_native_store_item_class_and_value_encoding_v1 import (
    KEYCHAIN_ITEM_CLASS,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_k1_runtime_binding_to_one_shot_actual_venue_post_pre_live_boundary_v1 import (
    EXPECTED_BASELINE_ORIGIN_MAIN_SHA,
    K1RuntimeBindingOneShotPostPreLiveBoundaryError,
    K1_OPAQUE_SIGNING_OWNER_GO,
    POST_OWNER_GO,
    attempt_k1_runtime_binding_to_one_shot_actual_venue_post_pre_live_boundary_v1,
    resolve_macos_security_framework_k1_lookup_backend_v1,
)
from src.ops.full_core_live_path_composition_root_v1.final_order_envelope_v1 import (
    bind_final_order_envelope_from_venue_plan_v1,
)
from src.ops.full_core_live_path_composition_root_v1.models_v1 import VenuePlanCandidateV1
from src.governance.current_productive_k1_pre_post_productive_chain_v1 import (
    STATUS_CHAIN_STOPPED_POST_ADMISSION,
)
from src.governance.current_productive_real_venue_post_admission_v1 import NEXT_OWNER_GO

REPO_ROOT = Path(__file__).resolve().parents[2]
FAKE_K1_OPAQUE = json.dumps(
    {"apiKey": "ak-test", "secretKey": "sk-test", "passphrase": "pp-test"},
    separators=(",", ":"),
).encode("utf-8")


class FakeOsNativeStoreLookupBackendV1:
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
        return bytes(FAKE_K1_OPAQUE)


def _sample_envelope():
    plan = VenuePlanCandidateV1(
        instrument_id="okx_eea:linear_perpetual:BTC:USDT:USDT:btc-usdt-swap",
        side="buy",
        quantity="1",
        order_type="market",
        td_mode="cross",
        reduce_only=False,
        clordid="k1-runtime-bind-clord",
        venue_native_payload={
            "instId": "BTC-USDT-SWAP",
            "ordType": "market",
            "side": "buy",
            "sz": "1",
            "tdMode": "cross",
        },
        quantity_source="TEST_FIXTURE_NOT_LIVE_ENVELOPE",
        side_source="TEST_FIXTURE_NOT_LIVE_ENVELOPE",
        instrument_source="TEST_FIXTURE",
        path_kind="FULL_CORE_CURRENT_PRODUCTIVE",
    )
    return bind_final_order_envelope_from_venue_plan_v1(
        plan,
        admission_ref="TEST_ADMISSION_REF",
        provenance_ref="TEST_PROVENANCE_REF",
        creation_epoch="2026-09-27T00:00:00Z",
    )


def test_baseline_pin_unchanged() -> None:
    assert EXPECTED_BASELINE_ORIGIN_MAIN_SHA == "1e859eaa79f48308cf7037656c6465191ed9993b"


def test_k1_runtime_binding_pre_live_boundary_fake_keychain(tmp_path: Path) -> None:
    backend = FakeOsNativeStoreLookupBackendV1()
    envelope = _sample_envelope()
    result = attempt_k1_runtime_binding_to_one_shot_actual_venue_post_pre_live_boundary_v1(
        k1_owner_go=K1_OPAQUE_SIGNING_OWNER_GO,
        post_owner_go=POST_OWNER_GO,
        baseline_origin_main_sha=EXPECTED_BASELINE_ORIGIN_MAIN_SHA,
        envelope=envelope,
        store_root=tmp_path,
        k1_backend=backend,
        repo_root=REPO_ROOT,
    )
    assert result.k1_chain_status == STATUS_CHAIN_STOPPED_POST_ADMISSION
    assert result.pre_live_proof_complete == "true"
    assert result.permit_consumed_durable == "false"
    assert result.real_venue_post_attempted == "false"
    assert result.next_true_blocker == NEXT_OWNER_GO
    public = json.dumps(result.to_public_dict_v1())
    assert "sk-test" not in public


def test_k1_owner_go_mismatch_fail_closed(tmp_path: Path) -> None:
    backend = FakeOsNativeStoreLookupBackendV1()
    with pytest.raises(K1RuntimeBindingOneShotPostPreLiveBoundaryError, match="K1_OWNER_GO"):
        attempt_k1_runtime_binding_to_one_shot_actual_venue_post_pre_live_boundary_v1(
            k1_owner_go="WRONG",
            post_owner_go=POST_OWNER_GO,
            baseline_origin_main_sha=EXPECTED_BASELINE_ORIGIN_MAIN_SHA,
            envelope=_sample_envelope(),
            store_root=tmp_path,
            k1_backend=backend,
            repo_root=REPO_ROOT,
        )


def test_resolve_macos_backend_requires_canonical_k1_go() -> None:
    with pytest.raises(K1RuntimeBindingOneShotPostPreLiveBoundaryError):
        resolve_macos_security_framework_k1_lookup_backend_v1(k1_owner_go="WRONG")
    backend = resolve_macos_security_framework_k1_lookup_backend_v1(
        k1_owner_go=K1_OPAQUE_SIGNING_OWNER_GO
    )
    assert backend is not None
