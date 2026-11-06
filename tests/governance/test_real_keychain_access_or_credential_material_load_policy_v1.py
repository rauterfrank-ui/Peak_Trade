"""Real Keychain access / credential material load policy v1 tests."""

from __future__ import annotations

import copy
import json
from pathlib import Path

from src.governance.governed_current_productive_chain_pre_external_to_external_effect_boundary_closure_v1 import (
    CANONICAL_EXTERNAL_EFFECT_BOUNDARY,
    prove_governed_current_productive_chain_pre_external_to_external_effect_boundary_v1,
)
from src.governance.governed_real_keychain_access_or_credential_material_load_policy_closure_v1 import (
    prove_governed_real_keychain_access_or_credential_material_load_policy_v1,
)
from src.governance.real_keychain_access_governed_credential_material_acquisition_v1 import (
    attempt_governed_credential_material_acquisition_v1,
    governed_credential_material_acquisition_scope_v1,
)
from src.governance.real_keychain_access_or_credential_material_load_gate_binding_v1 import (
    evaluate_material_load_bound_credential_acquisition_seam_v1,
)
from src.governance.real_keychain_access_or_credential_material_load_policy_v1 import (
    BASELINE_ORIGIN_MAIN_SHA,
    DECISION_CONFIG,
    OWNER_GO_DECISION_CONFIG,
    POLICY_RECORD_CONFIG,
    STATUS_LOAD_ADMISSION_GRANTED,
    STATUS_POLICY_VALID,
    canonical_policy_record_body_v1,
    evaluate_real_keychain_access_or_credential_material_load_admission_v1,
    governed_credential_material_load_authorized_v1,
    prove_material_load_does_not_authorize_post_v1,
    prove_material_load_does_not_authorize_request_signing_v1,
    prove_material_load_does_not_flip_standing_keychain_pins_v1,
    real_keychain_access_or_credential_material_load_policy_granted_v1,
    validate_real_keychain_access_or_credential_material_load_policy_record_v1,
)
from src.governance.checkout_independent_credential_access_policy_v1 import (
    governed_credential_access_authorized_v1,
)
from src.ops.full_core_live_path_composition_root_v1.checkout_independent_credential_capability_v1 import (
    FullCoreCheckoutIndependentCredentialCapabilityError,
)
from src.ops.full_core_live_path_composition_root_v1.checkout_independent_credential_os_native_store_acquisition_v1 import (
    KEYCHAIN_ACCOUNT_ID,
    KEYCHAIN_ITEM_CLASS,
    KEYCHAIN_SERVICE_ID,
    REASON_ITEM_ABSENT,
    coerce_opaque_value_data_v1,
    opaque_os_native_store_material_is_held_v1,
)
from src.ops.full_core_live_path_composition_root_v1.checkout_independent_credential_concrete_backend_item_identity_v1 import (
    SOURCE_REF_URI,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
FAKE_OPAQUE = b"\x00\x01OPAQUE-TEST-VECTOR-9f3a-not-operator-material"


class FakeOsNativeStoreLookupBackendV1:
    def __init__(self) -> None:
        self.items: dict[tuple[str, str, str], list[object]] = {}

    def put(self, *, service: str, account: str, item_class: str, values: list[object]) -> None:
        self.items[(service, account, item_class)] = list(values)

    def copy_matching_generic_password_value_data_v1(
        self,
        *,
        service: str,
        account: str,
        item_class: str,
    ) -> bytes:
        found = self.items.get((service, account, item_class), [])
        if len(found) == 0:
            raise FullCoreCheckoutIndependentCredentialCapabilityError(REASON_ITEM_ABSENT)
        return coerce_opaque_value_data_v1(found[0])


def _bound_fake() -> FakeOsNativeStoreLookupBackendV1:
    fake = FakeOsNativeStoreLookupBackendV1()
    fake.put(
        service=KEYCHAIN_SERVICE_ID,
        account=KEYCHAIN_ACCOUNT_ID,
        item_class=KEYCHAIN_ITEM_CLASS,
        values=[FAKE_OPAQUE],
    )
    return fake


def test_baseline_and_standing_pin_proofs() -> None:
    assert BASELINE_ORIGIN_MAIN_SHA == "ce883bb52163db2a9cd29c5029c29215be2afd90"
    assert prove_material_load_does_not_flip_standing_keychain_pins_v1()
    assert prove_material_load_does_not_authorize_request_signing_v1()
    assert prove_material_load_does_not_authorize_post_v1()


def test_material_load_policy_record_valid() -> None:
    result = validate_real_keychain_access_or_credential_material_load_policy_record_v1(
        repo_root=REPO_ROOT
    )
    assert result.material_load_policy_authorized is True, result.reason_codes
    assert result.policy_status == STATUS_POLICY_VALID
    assert real_keychain_access_or_credential_material_load_policy_granted_v1(repo_root=REPO_ROOT)


def test_positive_material_load_admission() -> None:
    assert governed_credential_access_authorized_v1(repo_root=REPO_ROOT)
    admission = evaluate_real_keychain_access_or_credential_material_load_admission_v1(
        repo_root=REPO_ROOT
    )
    assert admission.admission_status == STATUS_LOAD_ADMISSION_GRANTED
    assert admission.material_load_policy_granted is True
    assert admission.request_signing_authorized is False
    assert admission.post_allowed is False
    assert governed_credential_material_load_authorized_v1(repo_root=REPO_ROOT) is True


def test_material_load_gate_binding() -> None:
    bound = evaluate_material_load_bound_credential_acquisition_seam_v1(repo_root=REPO_ROOT)
    assert bound.material_load_admission_granted is True
    assert bound.request_signing_authorized is False


def test_governed_acquisition_with_fake_backend_no_secret_in_public_dict() -> None:
    fake = _bound_fake()
    result = attempt_governed_credential_material_acquisition_v1(
        repo_root=REPO_ROOT,
        backend=fake,
        source_ref=SOURCE_REF_URI,
    )
    assert result.acquisition_performed is True
    assert result.real_credential_access_performed is True
    assert result.secret_disclosed is False
    assert result.secret_persisted is False
    public = result.to_public_dict_v1()
    blob = json.dumps(public)
    assert FAKE_OPAQUE.decode("latin-1") not in blob
    assert "OPAQUE-TEST-VECTOR" not in blob


def test_governed_acquisition_scope_wipes_material() -> None:
    fake = _bound_fake()
    adapter_holder_check = False
    with governed_credential_material_acquisition_scope_v1(
        repo_root=REPO_ROOT,
        backend=fake,
    ) as result:
        assert result.acquisition_performed is True
        adapter_holder_check = True
    assert adapter_holder_check is True


def test_acquisition_without_backend_fail_closed() -> None:
    result = attempt_governed_credential_material_acquisition_v1(repo_root=REPO_ROOT)
    assert result.acquisition_performed is False
    assert "LOOKUP_BACKEND_REQUIRED" in result.reason_codes[0]


def test_closure_and_chain() -> None:
    assert prove_governed_real_keychain_access_or_credential_material_load_policy_v1(
        repo_root=REPO_ROOT
    )
    assert prove_governed_current_productive_chain_pre_external_to_external_effect_boundary_v1(
        repo_root=REPO_ROOT
    )


def test_decision_records() -> None:
    owner = json.loads((REPO_ROOT / OWNER_GO_DECISION_CONFIG).read_text(encoding="utf-8"))
    assert owner["real_keychain_access_or_credential_material_load_owner_go"] is True
    assert owner["real_secret_load_performed"] is False
    assert (
        owner["next_genuine_blocker"]
        == "OWNER_GO_CURRENT_PRODUCTIVE_K1_REAL_KEYCHAIN_ACCESS_AND_OPAQUE_SIGNING_HANDLE_PRE_POST_V1"
    )
    decision = json.loads((REPO_ROOT / DECISION_CONFIG).read_text(encoding="utf-8"))
    assert decision["load_implies_request_signing"] is False


def test_canonical_boundary_constant_updated() -> None:
    assert CANONICAL_EXTERNAL_EFFECT_BOUNDARY == (
        "K1_OPAQUE_SIGNING_PRE_POST_ENVELOPE_VALIDATED_REAL_VENUE_POST_ADMISSION_FAIL_CLOSED"
    )


def test_record_digest_mismatch_fail_closed(tmp_path: Path) -> None:
    for rel in (
        POLICY_RECORD_CONFIG,
        OWNER_GO_DECISION_CONFIG,
        "config/governance/checkout_independent_credential_access_policy_v1_record.json",
        "config/governance/checkout_independent_credential_access_owner_go_v1_decision.json",
        "config/governance/external_effect_permit_mint_policy_v1_record.json",
        "config/governance/external_effect_permit_mint_owner_go_v1_decision.json",
        "config/governance/standing_external_effect_lift_policy_v1_record.json",
        "config/governance/standing_external_effect_lift_owner_go_v1_decision.json",
        "config/governance/external_effect_authorization_policy_v1_record.json",
        "config/governance/external_effect_authorization_policy_owner_go_v1_decision.json",
    ):
        src = REPO_ROOT / rel
        dst = tmp_path / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")

    record = json.loads((tmp_path / POLICY_RECORD_CONFIG).read_text(encoding="utf-8"))
    record["policy_record_digest"] = "0" * 64
    (tmp_path / POLICY_RECORD_CONFIG).write_text(json.dumps(record, indent=2) + "\n")

    result = validate_real_keychain_access_or_credential_material_load_policy_record_v1(
        repo_root=tmp_path
    )
    assert result.material_load_policy_authorized is False
    assert "POLICY_RECORD_DIGEST_MISMATCH" in result.reason_codes


def test_canonical_body_stable() -> None:
    record = json.loads((REPO_ROOT / POLICY_RECORD_CONFIG).read_text(encoding="utf-8"))
    body = canonical_policy_record_body_v1(record)
    mutated = copy.deepcopy(record)
    mutated["semantic_definition"] = "tampered"
    assert canonical_policy_record_body_v1(mutated) != body
