"""Opaque macOS Keychain acquisition tests.

Uses fakes and OS-boundary substitution only. No operator Keychain material.
No vault files. No network. No V5/N5 join. No payload schema.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from src.ops.full_core_live_path_composition_root_v1.checkout_independent_credential_capability_v1 import (
    REAL_BACKEND_ACCESS_FAIL_CLOSED_CODE,
    FullCoreCheckoutIndependentCredentialCapabilityError,
    bind_offline_contract_capability_v1,
    prove_capability_cannot_mutate_standing_gates_v1,
    refuse_mint_external_effect_permit_from_credential_capability_v1,
    resolve_checkout_independent_credential_capability_v1,
)
from src.ops.full_core_live_path_composition_root_v1.checkout_independent_credential_fail_closed_os_native_store_adapter_v1 import (
    EPHEMERAL_MATERIAL_PATH_IMPLEMENTED,
    MATERIAL_LOADED_TRUE_REACHABLE,
    PRODUCTIVE_PROVIDER_ACTIVE,
    REAL_KEYCHAIN_ACCESS_AUTHORIZED as EA_REAL_KEYCHAIN_ACCESS_AUTHORIZED,
    REAL_KEYCHAIN_ACCESS_IMPLEMENTED as EA_REAL_KEYCHAIN_ACCESS_IMPLEMENTED,
    V5_JOINED,
    V5_USES_NEW_PROVIDER,
    FullCoreCheckoutIndependentFailClosedOsNativeStoreAdapterError,
    FullCoreCheckoutIndependentFailClosedOsNativeStoreAdapterV1,
)
from src.ops.full_core_live_path_composition_root_v1.checkout_independent_credential_os_native_store_acquisition_v1 import (
    K1_REAL_KEYCHAIN_ACQUISITION_IMPLEMENTED,
    KEYCHAIN_ACCOUNT_ID,
    KEYCHAIN_ITEM_CLASS,
    KEYCHAIN_SERVICE_ID,
    PAYLOAD_SCHEMA_INTRODUCED,
    REASON_BACKEND_REQUIRED,
    REASON_IDENTITY_MISMATCH,
    REASON_ITEM_ABSENT,
    REASON_ITEM_AMBIGUOUS,
    REASON_OS_NATIVE_STORE_ERROR,
    REASON_UNEXPECTED_REPRESENTATION,
    REASON_ACCESS_FORBIDDEN,
    REAL_KEYCHAIN_ACCESS_AUTHORIZED,
    REAL_KEYCHAIN_ACCESS_IMPLEMENTED,
    MacosSecurityFrameworkLookupBackendV1,
    coerce_opaque_value_data_v1,
    copy_matching_generic_password_payloads_v1,
    opaque_os_native_store_material_is_held_v1,
    public_surfaces_must_not_contain_opaque_material_v1,
    wipe_opaque_os_native_store_material_v1,
)
from src.ops.full_core_live_path_composition_root_v1.checkout_independent_credential_os_native_store_item_class_and_value_encoding_v1 import (
    REAL_KEYCHAIN_ACCESS_IMPLEMENTED as EB_REAL_KEYCHAIN_ACCESS_IMPLEMENTED,
)
from src.ops.full_core_live_path_composition_root_v1.checkout_independent_credential_source_backend_kind_v1 import (
    PRODUCTIVE_TARGET_BACKEND,
    REAL_KEYCHAIN_ACCESS_AUTHORIZED as DY_REAL_KEYCHAIN_ACCESS_AUTHORIZED,
    SOURCE_BACKEND_CLASS,
)
from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    EXTERNAL_EFFECT_AUTHORIZED,
    POST_ALLOWED,
    REAL_VENUE_POST_ALLOWED,
)
from src.ops.single_selected_future_runtime_binding_v1.constants_v1 import (
    MAX_POSITIONS_EFFECTIVE,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
OWNER_URI = "fullcore-cred://provider-ref/okx-eea-productive"
UNKNOWN_URI = "fullcore-cred://provider-ref/unknown-identifier"
FORBIDDEN_KIND_URI = "fullcore-cred://keychain/okx-eea-productive"
FAKE_OPAQUE = b"\x00\x01OPAQUE-TEST-VECTOR-9f3a-not-operator-material"
FAKE_OTHER = b"\x02\x03OPAQUE-OTHER-VECTOR-aa11"
ACQUISITION_PATH = (
    REPO_ROOT
    / "src/ops/full_core_live_path_composition_root_v1"
    / "checkout_independent_credential_os_native_store_acquisition_v1.py"
)
ADAPTER_PATH = (
    REPO_ROOT
    / "src/ops/full_core_live_path_composition_root_v1"
    / "checkout_independent_credential_fail_closed_os_native_store_adapter_v1.py"
)
DX_PATH = (
    REPO_ROOT
    / "src/ops/full_core_live_path_composition_root_v1"
    / "checkout_independent_credential_capability_v1.py"
)
DY_PATH = (
    REPO_ROOT
    / "src/ops/full_core_live_path_composition_root_v1"
    / "checkout_independent_credential_source_backend_kind_v1.py"
)
DZ_PATH = (
    REPO_ROOT
    / "src/ops/full_core_live_path_composition_root_v1"
    / "checkout_independent_credential_concrete_backend_item_identity_v1.py"
)
EB_PATH = (
    REPO_ROOT
    / "src/ops/full_core_live_path_composition_root_v1"
    / "checkout_independent_credential_os_native_store_item_class_and_value_encoding_v1.py"
)
N5_DIR = REPO_ROOT / "src/ops/current_mf_n5_full_autonomy_runtime_n5_completion_v1"
K2_MARKERS = (
    "secretref",
    "SecretRef",
    "file_vault",
    "FILE_VAULT",
    "vault.json",
    "live_credential_ephemeral_v1",
)
NETWORK_MARKERS = (
    "import urllib",
    "from urllib",
    "import socket",
    "import requests",
    "import http.client",
    "from http",
)
FALLBACK_MARKERS = (
    "os.environ",
    "getenv",
    "Path(",
    "open(",
    "vault",
    "keyring",
    "subprocess",
)


class FakeOsNativeStoreLookupBackendV1:
    def __init__(self) -> None:
        self.items: dict[tuple[str, str, str], list[object]] = {}
        self.os_error = False
        self.calls: list[tuple[str, str, str]] = []

    def put(self, *, service: str, account: str, item_class: str, values: list[object]) -> None:
        self.items[(service, account, item_class)] = list(values)

    def copy_matching_generic_password_value_data_v1(
        self,
        *,
        service: str,
        account: str,
        item_class: str,
    ) -> bytes:
        self.calls.append((service, account, item_class))
        if self.os_error:
            raise RuntimeError("synthetic-os-failure")
        found = self.items.get((service, account, item_class), [])
        if len(found) == 0:
            raise FullCoreCheckoutIndependentCredentialCapabilityError(REASON_ITEM_ABSENT)
        if len(found) > 1:
            raise FullCoreCheckoutIndependentCredentialCapabilityError(REASON_ITEM_AMBIGUOUS)
        return coerce_opaque_value_data_v1(found[0])


ACQ_MOD = (
    "src.ops.full_core_live_path_composition_root_v1."
    "checkout_independent_credential_os_native_store_acquisition_v1"
)


def _authorize(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(f"{ACQ_MOD}.REAL_KEYCHAIN_ACCESS_AUTHORIZED", True)


def _bound_fake() -> FakeOsNativeStoreLookupBackendV1:
    fake = FakeOsNativeStoreLookupBackendV1()
    fake.put(
        service=KEYCHAIN_SERVICE_ID,
        account=KEYCHAIN_ACCOUNT_ID,
        item_class=KEYCHAIN_ITEM_CLASS,
        values=[FAKE_OPAQUE],
    )
    return fake


def test_exact_identity_binding_acquires_opaque_bytes_inside_boundary() -> None:
    adapter = FullCoreCheckoutIndependentFailClosedOsNativeStoreAdapterV1()
    fake = _bound_fake()
    proof = adapter.acquire_opaque_os_native_store_material_v1(
        source_ref=OWNER_URI,
        backend=fake,
    )
    assert proof.acquired == "true"
    assert proof.source_ref_uri == OWNER_URI
    assert proof.keychain_service_id == "peak-trade.full-core.venue-credentials"
    assert proof.keychain_account_id == "okx-eea.productive"
    assert proof.keychain_item_class == "generic-password"
    assert proof.keychain_value_data_representation == "BYTES"
    assert proof.payload_schema_bound == "false"
    assert proof.material_emitted == "false"
    assert proof.utf8_payload_parsed == "false"
    assert fake.calls == [
        (
            "peak-trade.full-core.venue-credentials",
            "okx-eea.productive",
            "generic-password",
        )
    ]
    assert opaque_os_native_store_material_is_held_v1(id(adapter)) is True
    public_surfaces_must_not_contain_opaque_material_v1(
        proof,
        proof.to_dict(),
        adapter,
        adapter.__dict__,
        sentinel=FAKE_OPAQUE,
    )


def test_wrong_identity_rejected_without_lookup() -> None:
    adapter = FullCoreCheckoutIndependentFailClosedOsNativeStoreAdapterV1()
    fake = _bound_fake()
    with pytest.raises(
        FullCoreCheckoutIndependentCredentialCapabilityError,
        match="KEYCHAIN_IDENTITY_UNKNOWN_IDENTIFIER",
    ):
        adapter.acquire_opaque_os_native_store_material_v1(
            source_ref=UNKNOWN_URI,
            backend=fake,
        )
    with pytest.raises(
        FullCoreCheckoutIndependentCredentialCapabilityError,
        match="MALFORMED_PROVIDER_REFERENCE",
    ):
        adapter.acquire_opaque_os_native_store_material_v1(
            source_ref=FORBIDDEN_KIND_URI,
            backend=fake,
        )
    assert fake.calls == []
    assert opaque_os_native_store_material_is_held_v1(id(adapter)) is False


def test_missing_ambiguous_os_error_and_unexpected_representation_fail_closed() -> None:
    adapter = FullCoreCheckoutIndependentFailClosedOsNativeStoreAdapterV1()
    missing = FakeOsNativeStoreLookupBackendV1()
    with pytest.raises(
        FullCoreCheckoutIndependentCredentialCapabilityError,
        match=REASON_ITEM_ABSENT,
    ):
        adapter.acquire_opaque_os_native_store_material_v1(
            source_ref=OWNER_URI,
            backend=missing,
        )
    ambiguous = FakeOsNativeStoreLookupBackendV1()
    ambiguous.put(
        service=KEYCHAIN_SERVICE_ID,
        account=KEYCHAIN_ACCOUNT_ID,
        item_class=KEYCHAIN_ITEM_CLASS,
        values=[FAKE_OPAQUE, FAKE_OTHER],
    )
    with pytest.raises(
        FullCoreCheckoutIndependentCredentialCapabilityError,
        match=REASON_ITEM_AMBIGUOUS,
    ):
        adapter.acquire_opaque_os_native_store_material_v1(
            source_ref=OWNER_URI,
            backend=ambiguous,
        )
    unexpected = FakeOsNativeStoreLookupBackendV1()
    unexpected.put(
        service=KEYCHAIN_SERVICE_ID,
        account=KEYCHAIN_ACCOUNT_ID,
        item_class=KEYCHAIN_ITEM_CLASS,
        values=["not-bytes"],
    )
    with pytest.raises(
        FullCoreCheckoutIndependentCredentialCapabilityError,
        match=REASON_UNEXPECTED_REPRESENTATION,
    ):
        adapter.acquire_opaque_os_native_store_material_v1(
            source_ref=OWNER_URI,
            backend=unexpected,
        )
    os_err = FakeOsNativeStoreLookupBackendV1()
    os_err.os_error = True
    with pytest.raises(
        FullCoreCheckoutIndependentCredentialCapabilityError,
        match=REASON_OS_NATIVE_STORE_ERROR,
    ):
        adapter.acquire_opaque_os_native_store_material_v1(
            source_ref=OWNER_URI,
            backend=os_err,
        )
    assert opaque_os_native_store_material_is_held_v1(id(adapter)) is False


def test_non_callable_backend_and_identity_mismatch_on_unbound_query() -> None:
    class _MissingMethod:
        pass

    adapter = FullCoreCheckoutIndependentFailClosedOsNativeStoreAdapterV1()
    with pytest.raises(
        FullCoreCheckoutIndependentCredentialCapabilityError,
        match=REASON_BACKEND_REQUIRED,
    ):
        adapter.acquire_opaque_os_native_store_material_v1(
            source_ref=OWNER_URI,
            backend=_MissingMethod(),  # type: ignore[arg-type]
        )
    with pytest.raises(
        FullCoreCheckoutIndependentCredentialCapabilityError,
        match=REASON_IDENTITY_MISMATCH,
    ):
        MacosSecurityFrameworkLookupBackendV1().copy_matching_generic_password_value_data_v1(
            service="other.service",
            account=KEYCHAIN_ACCOUNT_ID,
            item_class=KEYCHAIN_ITEM_CLASS,
        )


def test_opaque_material_never_emitted_through_public_result_repr_or_error() -> None:
    adapter = FullCoreCheckoutIndependentFailClosedOsNativeStoreAdapterV1()
    fake = _bound_fake()
    proof = adapter.acquire_opaque_os_native_store_material_v1(
        source_ref=OWNER_URI,
        backend=fake,
    )
    leak_surfaces = [
        proof,
        proof.to_dict(),
        adapter,
        adapter.__dict__,
        repr(adapter),
        str(adapter),
    ]
    try:
        raise FullCoreCheckoutIndependentCredentialCapabilityError("KEYCHAIN_ITEM_ABSENT")
    except FullCoreCheckoutIndependentCredentialCapabilityError as exc:
        leak_surfaces.append(exc)
        leak_surfaces.append(str(exc))
        leak_surfaces.append(repr(exc))
    for surface in leak_surfaces:
        public_surfaces_must_not_contain_opaque_material_v1(surface, sentinel=FAKE_OPAQUE)
    capability = bind_offline_contract_capability_v1(source_ref=OWNER_URI)
    adapter.release_capability_v1(capability)
    assert opaque_os_native_store_material_is_held_v1(id(adapter)) is False
    public_surfaces_must_not_contain_opaque_material_v1(
        adapter,
        adapter.__dict__,
        sentinel=FAKE_OPAQUE,
    )


def test_no_fallback_source_and_no_k2_or_network_dependency() -> None:
    source = ACQUISITION_PATH.read_text(encoding="utf-8")
    for marker in K2_MARKERS + NETWORK_MARKERS + FALLBACK_MARKERS:
        assert marker not in source
    adapter_source = ADAPTER_PATH.read_text(encoding="utf-8")
    for marker in (
        "secretref",
        "FILE_VAULT",
        "import ctypes",
        "from ctypes",
        "SecItemCopyMatching",
    ):
        if marker in {"import ctypes", "from ctypes", "SecItemCopyMatching"}:
            assert marker not in adapter_source
        else:
            assert marker not in adapter_source
    assert "run_opaque_os_native_store_acquisition_v1" in adapter_source
    assert K1_REAL_KEYCHAIN_ACQUISITION_IMPLEMENTED is True
    assert REAL_KEYCHAIN_ACCESS_IMPLEMENTED is False
    assert REAL_KEYCHAIN_ACCESS_AUTHORIZED is False
    assert EA_REAL_KEYCHAIN_ACCESS_IMPLEMENTED is False
    assert EA_REAL_KEYCHAIN_ACCESS_AUTHORIZED is False
    assert DY_REAL_KEYCHAIN_ACCESS_AUTHORIZED is False
    assert EB_REAL_KEYCHAIN_ACCESS_IMPLEMENTED is False
    assert PAYLOAD_SCHEMA_INTRODUCED is False


def test_resolve_path_and_prior_dx_eb_semantics_remain_fail_closed() -> None:
    adapter = FullCoreCheckoutIndependentFailClosedOsNativeStoreAdapterV1()
    with pytest.raises(
        FullCoreCheckoutIndependentFailClosedOsNativeStoreAdapterError,
        match=REAL_BACKEND_ACCESS_FAIL_CLOSED_CODE,
    ):
        resolve_checkout_independent_credential_capability_v1(
            source_ref=OWNER_URI,
            provider=adapter,
        )
    assert adapter.resolve_dispatch_count == 1
    assert EA_REAL_KEYCHAIN_ACCESS_IMPLEMENTED is False
    assert EPHEMERAL_MATERIAL_PATH_IMPLEMENTED is False
    assert MATERIAL_LOADED_TRUE_REACHABLE is False
    assert PRODUCTIVE_PROVIDER_ACTIVE is False
    assert V5_JOINED is False
    assert V5_USES_NEW_PROVIDER is False
    assert SOURCE_BACKEND_CLASS == "OS_NATIVE_SECRET_STORE"
    assert PRODUCTIVE_TARGET_BACKEND == "MACOS_KEYCHAIN"
    dx_text = DX_PATH.read_text(encoding="utf-8")
    assert "REAL_BACKEND_ACCESS_NOT_IMPLEMENTED_AND_NOT_AUTHORIZED" in dx_text
    assert "CREDENTIAL_MATERIAL_LOADED_FORBIDDEN" in dx_text
    for path in (DY_PATH, DZ_PATH):
        assert "REAL_KEYCHAIN_ACCESS_AUTHORIZED = False" in path.read_text(encoding="utf-8")
    for path in (EB_PATH, ADAPTER_PATH):
        text = path.read_text(encoding="utf-8")
        assert "REAL_KEYCHAIN_ACCESS_IMPLEMENTED = False" in text
        assert "REAL_KEYCHAIN_ACCESS_AUTHORIZED = False" in text


def test_no_authority_escalation_or_n5_join() -> None:
    before = prove_capability_cannot_mutate_standing_gates_v1()
    adapter = FullCoreCheckoutIndependentFailClosedOsNativeStoreAdapterV1()
    proof = adapter.acquire_opaque_os_native_store_material_v1(
        source_ref=OWNER_URI,
        backend=_bound_fake(),
    )
    after = prove_capability_cannot_mutate_standing_gates_v1()
    assert before == after
    assert proof.real_keychain_access_authorized == "false"
    assert proof.productive_provider_active == "false"
    assert proof.v5_joined == "false"
    assert EXTERNAL_EFFECT_AUTHORIZED is False
    assert REAL_VENUE_POST_ALLOWED is False
    assert POST_ALLOWED is False
    assert int(MAX_POSITIONS_EFFECTIVE) == 1
    n5_source = "\n".join(path.read_text(encoding="utf-8") for path in N5_DIR.glob("*.py"))
    assert "checkout_independent_credential_os_native_store_acquisition_v1" not in n5_source
    assert "acquire_opaque_os_native_store_material_v1" not in n5_source


def test_real_backend_uses_substituted_os_boundary_only(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _authorize(monkeypatch)
    recorded: list[tuple[str, str, str]] = []

    def _absent(*, service: str, account: str, item_class: str) -> list[bytes]:
        recorded.append((service, account, item_class))
        return []

    monkeypatch.setattr(
        f"{ACQ_MOD}.copy_matching_generic_password_payloads_v1",
        _absent,
    )
    backend = MacosSecurityFrameworkLookupBackendV1()
    with pytest.raises(
        FullCoreCheckoutIndependentCredentialCapabilityError,
        match=REASON_ITEM_ABSENT,
    ):
        backend.copy_matching_generic_password_value_data_v1(
            service=KEYCHAIN_SERVICE_ID,
            account=KEYCHAIN_ACCOUNT_ID,
            item_class=KEYCHAIN_ITEM_CLASS,
        )

    def _ambiguous(*, service: str, account: str, item_class: str) -> list[bytes]:
        del service, account, item_class
        return [FAKE_OPAQUE, FAKE_OTHER]

    monkeypatch.setattr(
        f"{ACQ_MOD}.copy_matching_generic_password_payloads_v1",
        _ambiguous,
    )
    with pytest.raises(
        FullCoreCheckoutIndependentCredentialCapabilityError,
        match=REASON_ITEM_AMBIGUOUS,
    ):
        backend.copy_matching_generic_password_value_data_v1(
            service=KEYCHAIN_SERVICE_ID,
            account=KEYCHAIN_ACCOUNT_ID,
            item_class=KEYCHAIN_ITEM_CLASS,
        )
    assert recorded == [
        (
            "peak-trade.full-core.venue-credentials",
            "okx-eea.productive",
            "generic-password",
        )
    ]


def test_copy_matching_payloads_does_not_run_against_operator_keychain(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def _forbidden(*, service: str, account: str) -> list[bytes]:
        del service, account
        raise AssertionError("operator-keychain-must-not-be-reached")

    monkeypatch.setattr(
        f"{ACQ_MOD}._sec_item_copy_matching_generic_password_payloads_v1",
        _forbidden,
    )
    monkeypatch.setattr(f"{ACQ_MOD}.sys.platform", "darwin")
    with pytest.raises(
        FullCoreCheckoutIndependentCredentialCapabilityError,
        match=REASON_ACCESS_FORBIDDEN,
    ):
        copy_matching_generic_password_payloads_v1(
            service=KEYCHAIN_SERVICE_ID,
            account=KEYCHAIN_ACCOUNT_ID,
            item_class=KEYCHAIN_ITEM_CLASS,
        )
    wipe_opaque_os_native_store_material_v1(0)


def test_unauthorized_default_backend_is_macos_and_does_not_call_os(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    os_calls: list[tuple[str, str]] = []
    constructed: list[str] = []

    class _SpyBackend(MacosSecurityFrameworkLookupBackendV1):
        def __init__(self) -> None:
            constructed.append("macos")
            super().__init__()

    def _forbidden(*, service: str, account: str) -> list[bytes]:
        os_calls.append((service, account))
        raise AssertionError("operator-keychain-must-not-be-reached")

    monkeypatch.setattr(f"{ACQ_MOD}.MacosSecurityFrameworkLookupBackendV1", _SpyBackend)
    monkeypatch.setattr(
        f"{ACQ_MOD}._sec_item_copy_matching_generic_password_payloads_v1",
        _forbidden,
    )
    adapter = FullCoreCheckoutIndependentFailClosedOsNativeStoreAdapterV1()
    with pytest.raises(
        FullCoreCheckoutIndependentCredentialCapabilityError,
        match=REASON_ACCESS_FORBIDDEN,
    ):
        adapter.acquire_opaque_os_native_store_material_v1(
            source_ref=OWNER_URI,
            backend=None,
        )
    assert constructed == ["macos"]
    assert os_calls == []
    assert REAL_KEYCHAIN_ACCESS_AUTHORIZED is False
    assert opaque_os_native_store_material_is_held_v1(id(adapter)) is False


def test_authorized_default_backend_reaches_substituted_os_boundary(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _authorize(monkeypatch)
    recorded: list[tuple[str, str, str]] = []

    def _one(*, service: str, account: str, item_class: str) -> list[bytes]:
        recorded.append((service, account, item_class))
        return [FAKE_OPAQUE]

    monkeypatch.setattr(f"{ACQ_MOD}.copy_matching_generic_password_payloads_v1", _one)
    adapter = FullCoreCheckoutIndependentFailClosedOsNativeStoreAdapterV1()
    proof = adapter.acquire_opaque_os_native_store_material_v1(
        source_ref=OWNER_URI,
        backend=None,
    )
    assert proof.acquired == "true"
    assert proof.real_keychain_access_authorized == "true"
    assert proof.material_emitted == "false"
    assert recorded == [
        (
            "peak-trade.full-core.venue-credentials",
            "okx-eea.productive",
            "generic-password",
        )
    ]
    assert opaque_os_native_store_material_is_held_v1(id(adapter)) is True
    public_surfaces_must_not_contain_opaque_material_v1(
        proof,
        proof.to_dict(),
        adapter,
        adapter.__dict__,
        sentinel=FAKE_OPAQUE,
    )


def test_authorized_wrong_identity_fail_closed_without_os(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _authorize(monkeypatch)
    os_calls: list[tuple[str, str, str]] = []

    def _must_not_run(*, service: str, account: str, item_class: str) -> list[bytes]:
        os_calls.append((service, account, item_class))
        return [FAKE_OPAQUE]

    monkeypatch.setattr(
        f"{ACQ_MOD}.copy_matching_generic_password_payloads_v1",
        _must_not_run,
    )
    adapter = FullCoreCheckoutIndependentFailClosedOsNativeStoreAdapterV1()
    with pytest.raises(
        FullCoreCheckoutIndependentCredentialCapabilityError,
        match="KEYCHAIN_IDENTITY_UNKNOWN_IDENTIFIER",
    ):
        adapter.acquire_opaque_os_native_store_material_v1(
            source_ref=UNKNOWN_URI,
            backend=None,
        )
    with pytest.raises(
        FullCoreCheckoutIndependentCredentialCapabilityError,
        match="MALFORMED_PROVIDER_REFERENCE",
    ):
        adapter.acquire_opaque_os_native_store_material_v1(
            source_ref=FORBIDDEN_KIND_URI,
            backend=None,
        )
    assert os_calls == []


def test_default_wiring_does_not_authorize_or_lift_resolve(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = ACQUISITION_PATH.read_text(encoding="utf-8")
    assert "if backend is None:" in source
    assert "MacosSecurityFrameworkLookupBackendV1()" in source
    assert "REAL_KEYCHAIN_ACCESS_AUTHORIZED = False" in source
    assert REAL_KEYCHAIN_ACCESS_AUTHORIZED is False
    adapter = FullCoreCheckoutIndependentFailClosedOsNativeStoreAdapterV1()
    with pytest.raises(
        FullCoreCheckoutIndependentFailClosedOsNativeStoreAdapterError,
        match=REAL_BACKEND_ACCESS_FAIL_CLOSED_CODE,
    ):
        resolve_checkout_independent_credential_capability_v1(
            source_ref=OWNER_URI,
            provider=adapter,
        )
    _authorize(monkeypatch)
    with pytest.raises(
        FullCoreCheckoutIndependentFailClosedOsNativeStoreAdapterError,
        match=REAL_BACKEND_ACCESS_FAIL_CLOSED_CODE,
    ):
        resolve_checkout_independent_credential_capability_v1(
            source_ref=OWNER_URI,
            provider=adapter,
        )
    with pytest.raises(
        FullCoreCheckoutIndependentCredentialCapabilityError,
        match="CREDENTIAL_CAPABILITY_CANNOT_MINT_PERMIT",
    ):
        refuse_mint_external_effect_permit_from_credential_capability_v1()
    assert EXTERNAL_EFFECT_AUTHORIZED is False
    assert REAL_VENUE_POST_ALLOWED is False
    assert POST_ALLOWED is False
    assert REAL_KEYCHAIN_ACCESS_IMPLEMENTED is False
    assert PRODUCTIVE_PROVIDER_ACTIVE is False
    assert V5_JOINED is False


def test_authorized_direct_os_boundary_substitution_reaches_secitem_hook(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _authorize(monkeypatch)
    seen: list[tuple[str, str]] = []

    def _substituted(*, service: str, account: str) -> list[bytes]:
        seen.append((service, account))
        return [FAKE_OPAQUE]

    monkeypatch.setattr(
        f"{ACQ_MOD}._sec_item_copy_matching_generic_password_payloads_v1",
        _substituted,
    )
    monkeypatch.setattr(f"{ACQ_MOD}.sys.platform", "darwin")
    payloads = copy_matching_generic_password_payloads_v1(
        service=KEYCHAIN_SERVICE_ID,
        account=KEYCHAIN_ACCOUNT_ID,
        item_class=KEYCHAIN_ITEM_CLASS,
    )
    assert payloads == [FAKE_OPAQUE]
    assert seen == [("peak-trade.full-core.venue-credentials", "okx-eea.productive")]


def test_secitem_query_shape_uses_return_data_and_match_limit_one_only() -> None:
    source = ACQUISITION_PATH.read_text(encoding="utf-8")
    assert '_symbol(security, "kSecReturnAttributes")' not in source
    assert '_symbol(security, "kSecMatchLimitAll")' not in source
    assert '_symbol(security, "kSecMatchLimitOne")' in source
    assert '_symbol(security, "kSecReturnData")' in source


def test_secitem_malformed_empty_payload_fail_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _authorize(monkeypatch)

    def _empty(*, service: str, account: str) -> list[bytes]:
        del service, account
        return [b""]

    monkeypatch.setattr(
        f"{ACQ_MOD}._sec_item_copy_matching_generic_password_payloads_v1",
        _empty,
    )
    monkeypatch.setattr(f"{ACQ_MOD}.sys.platform", "darwin")
    backend = MacosSecurityFrameworkLookupBackendV1()
    with pytest.raises(
        FullCoreCheckoutIndependentCredentialCapabilityError,
        match=REASON_UNEXPECTED_REPRESENTATION,
    ):
        backend.copy_matching_generic_password_value_data_v1(
            service=KEYCHAIN_SERVICE_ID,
            account=KEYCHAIN_ACCOUNT_ID,
            item_class=KEYCHAIN_ITEM_CLASS,
        )
