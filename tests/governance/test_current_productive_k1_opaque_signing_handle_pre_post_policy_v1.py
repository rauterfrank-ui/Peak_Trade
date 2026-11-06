"""K1 opaque signing handle PRE-POST policy v1 tests (fake Keychain only)."""

from __future__ import annotations

import json
from pathlib import Path

from src.governance.current_productive_k1_opaque_signing_handle_pre_post_policy_v1 import (
    BASELINE_ORIGIN_MAIN_SHA,
    OWNER_GO_TOKEN,
    STATUS_PRE_POST_ADMISSION_GRANTED,
    STATUS_POLICY_VALID,
    canonical_policy_record_body_v1,
    evaluate_k1_opaque_signing_handle_pre_post_admission_v1,
    governed_k1_opaque_signing_handle_pre_post_authorized_v1,
    k1_opaque_signing_handle_pre_post_policy_granted_v1,
    prove_k1_pre_post_does_not_authorize_post_v1,
    prove_k1_pre_post_does_not_flip_standing_keychain_pins_v1,
    validate_k1_opaque_signing_handle_pre_post_policy_record_v1,
)
from src.governance.current_productive_k1_opaque_signing_handle_pre_post_gate_binding_v1 import (
    evaluate_k1_pre_post_bound_opaque_signing_construction_seam_v1,
)
from src.governance.current_productive_k1_pre_post_productive_chain_v1 import (
    STATUS_CHAIN_STOPPED_POST_ADMISSION,
    attempt_governed_current_productive_k1_pre_post_productive_chain_v1,
)
from src.governance.current_productive_real_venue_post_admission_v1 import (
    BLOCKER_CLASS,
    NEXT_OWNER_GO,
)
from src.governance.governed_current_productive_chain_pre_external_to_external_effect_boundary_closure_v1 import (
    CANONICAL_EXTERNAL_EFFECT_BOUNDARY,
    prove_governed_current_productive_chain_pre_external_to_external_effect_boundary_v1,
)
from src.governance.governed_current_productive_k1_opaque_signing_handle_pre_post_policy_closure_v1 import (
    prove_governed_current_productive_k1_opaque_signing_handle_pre_post_policy_v1,
)
from src.governance.k1_opaque_signing_handle_governed_construction_v1 import (
    governed_k1_opaque_signing_handle_construction_scope_v1,
)
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
        clordid="k1-pre-post-test-clord",
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


def test_baseline_and_standing_pin_proofs() -> None:
    assert BASELINE_ORIGIN_MAIN_SHA == "4e31703f888fec81cca97f51376429088e022f3d"
    assert prove_k1_pre_post_does_not_flip_standing_keychain_pins_v1()
    assert prove_k1_pre_post_does_not_authorize_post_v1()


def test_k1_pre_post_policy_record_valid() -> None:
    result = validate_k1_opaque_signing_handle_pre_post_policy_record_v1(repo_root=REPO_ROOT)
    assert result.policy_status == STATUS_POLICY_VALID
    assert result.k1_pre_post_policy_authorized is True
    assert k1_opaque_signing_handle_pre_post_policy_granted_v1(repo_root=REPO_ROOT)
    assert governed_k1_opaque_signing_handle_pre_post_authorized_v1(repo_root=REPO_ROOT)


def test_admission_and_gate_binding() -> None:
    admission = evaluate_k1_opaque_signing_handle_pre_post_admission_v1(repo_root=REPO_ROOT)
    assert admission.admission_status == STATUS_PRE_POST_ADMISSION_GRANTED
    assert admission.request_signing_authorized is True
    assert admission.post_allowed is False
    bound = evaluate_k1_pre_post_bound_opaque_signing_construction_seam_v1(repo_root=REPO_ROOT)
    assert bound.k1_pre_post_admission_granted is True
    assert bound.request_signing_authorized is True


def test_governed_construction_and_productive_chain_stops_at_post_admission() -> None:
    backend = FakeOsNativeStoreLookupBackendV1()
    with governed_k1_opaque_signing_handle_construction_scope_v1(
        repo_root=REPO_ROOT,
        owner_go=OWNER_GO_TOKEN,
        backend=backend,
    ) as (construction, session):
        assert construction.construction_performed is True
        assert session is not None
        assert session.signing_handle.can_sign is True
        blob = json.dumps(construction.to_public_dict_v1())
        assert "sk-test" not in blob

    envelope = _sample_envelope()
    chain = attempt_governed_current_productive_k1_pre_post_productive_chain_v1(
        repo_root=REPO_ROOT,
        owner_go=OWNER_GO_TOKEN,
        envelope=envelope,
        k1_backend=backend,
        post_owner_go=None,
        one_shot_real_post=False,
    )
    assert chain.chain_status == STATUS_CHAIN_STOPPED_POST_ADMISSION
    assert chain.opaque_signing_handle_constructed is True
    assert chain.request_signing_performed is True
    assert chain.pre_post_envelope_constructed is True
    assert chain.pre_post_validated is True
    assert chain.permit_mint_performed is True
    assert chain.post_admission.post_admission_granted is False
    assert chain.blocker_class == BLOCKER_CLASS
    assert chain.next_owner_go == NEXT_OWNER_GO
    assert chain.secret_disclosed is False
    public = json.dumps(chain.to_public_dict_v1())
    assert "sk-test" not in public
    assert "ak-test" not in public


def test_closure_and_canonical_boundary() -> None:
    assert prove_governed_current_productive_k1_opaque_signing_handle_pre_post_policy_v1(
        repo_root=REPO_ROOT
    )
    assert prove_governed_current_productive_chain_pre_external_to_external_effect_boundary_v1(
        repo_root=REPO_ROOT
    )
    assert CANONICAL_EXTERNAL_EFFECT_BOUNDARY == (
        "K1_OPAQUE_SIGNING_PRE_POST_ENVELOPE_VALIDATED_REAL_VENUE_POST_ADMISSION_FAIL_CLOSED"
    )


def test_owner_go_mismatch_fail_closed() -> None:
    backend = FakeOsNativeStoreLookupBackendV1()
    with governed_k1_opaque_signing_handle_construction_scope_v1(
        repo_root=REPO_ROOT,
        owner_go="WRONG_GO",
        backend=backend,
    ) as (construction, session):
        assert construction.construction_performed is False
        assert session is None
        assert "OWNER_GO_MISMATCH" in construction.reason_codes


def test_policy_digest_stable() -> None:
    from src.governance.current_productive_k1_opaque_signing_handle_pre_post_policy_v1 import (
        POLICY_RECORD_CONFIG,
        load_k1_opaque_signing_handle_pre_post_policy_record_v1,
    )
    from src.meta.learning_loop.contract_safety_v1 import compute_content_sha256

    record = load_k1_opaque_signing_handle_pre_post_policy_record_v1(repo_root=REPO_ROOT)
    body = canonical_policy_record_body_v1(record)
    assert record["policy_record_digest"] == compute_content_sha256(body)
    assert (REPO_ROOT / POLICY_RECORD_CONFIG).is_file()
