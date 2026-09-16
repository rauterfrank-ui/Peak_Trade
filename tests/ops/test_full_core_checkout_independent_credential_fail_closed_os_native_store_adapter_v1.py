"""Fail-closed OS-native-store adapter offline contract tests.

No Keychain access. No vault files. No network. No V5 join.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from src.ops.full_core_live_path_composition_root_v1.checkout_independent_credential_capability_v1 import (
    REAL_BACKEND_ACCESS_FAIL_CLOSED_CODE,
    FullCoreCheckoutIndependentCredentialCapabilityError,
    FullCoreCheckoutIndependentCredentialCapabilityV1,
    FullCoreCheckoutIndependentCredentialSourceRefV1,
    assert_checkout_independent_source_ref_v1,
    bind_offline_contract_capability_v1,
    prove_capability_cannot_mutate_standing_gates_v1,
    resolve_checkout_independent_credential_capability_v1,
)
from src.ops.full_core_live_path_composition_root_v1.checkout_independent_credential_concrete_backend_item_identity_v1 import (
    KEYCHAIN_ACCOUNT_ID,
    KEYCHAIN_SERVICE_ID,
    PROVIDER_REF_IDENTIFIER,
    SOURCE_REF_URI,
    resolve_bound_keychain_item_identity_v1,
)
from src.ops.full_core_live_path_composition_root_v1.checkout_independent_credential_fail_closed_os_native_store_adapter_v1 import (
    EPHEMERAL_MATERIAL_PATH_IMPLEMENTED,
    MATERIAL_LOADED_TRUE_REACHABLE,
    OFFLINE_ADAPTER_IMPLEMENTED,
    PRODUCTIVE_PROVIDER_ACTIVE,
    REAL_KEYCHAIN_ACCESS_AUTHORIZED as ADAPTER_REAL_KEYCHAIN_ACCESS_AUTHORIZED,
    REAL_KEYCHAIN_ACCESS_IMPLEMENTED,
    RESOLVE_DISPATCH_TO_ADAPTER_IMPLEMENTED,
    V5_JOINED,
    V5_USES_NEW_PROVIDER,
    FullCoreCheckoutIndependentFailClosedOsNativeStoreAdapterError,
    FullCoreCheckoutIndependentFailClosedOsNativeStoreAdapterV1,
    bind_fail_closed_os_native_store_adapter_v1,
    prove_adapter_authority_non_interference_v1,
    prove_fail_closed_adapter_bound_v1,
)
from src.ops.full_core_live_path_composition_root_v1.checkout_independent_credential_source_backend_kind_v1 import (
    PRODUCTIVE_TARGET_BACKEND,
    REAL_KEYCHAIN_ACCESS_AUTHORIZED,
    SOURCE_BACKEND_CLASS,
    refuse_real_keychain_access_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.credential_presence_v1 import (
    DEFAULT_VAULT_RELATIVE,
    default_vault_path_v1,
)
from src.ops.single_selected_future_runtime_binding_v1.constants_v1 import (
    MAX_POSITIONS_EFFECTIVE,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
V5_HOST = (
    REPO_ROOT
    / "src/ops/governed_productive_account_equity_authority_producer_v1"
    / "current_productive_one_runtime_cycle_after_new_finalized_1m_c1_observation_v5.py"
)
MODULE_PATH = (
    REPO_ROOT
    / "src/ops/full_core_live_path_composition_root_v1"
    / "checkout_independent_credential_fail_closed_os_native_store_adapter_v1.py"
)
RESOLVE_MODULE_PATH = (
    REPO_ROOT
    / "src/ops/full_core_live_path_composition_root_v1"
    / "checkout_independent_credential_capability_v1.py"
)
DX_MODULE_PATH = RESOLVE_MODULE_PATH
DY_MODULE_PATH = (
    REPO_ROOT
    / "src/ops/full_core_live_path_composition_root_v1"
    / "checkout_independent_credential_source_backend_kind_v1.py"
)
DZ_MODULE_PATH = (
    REPO_ROOT
    / "src/ops/full_core_live_path_composition_root_v1"
    / "checkout_independent_credential_concrete_backend_item_identity_v1.py"
)
EB_MODULE_PATH = (
    REPO_ROOT
    / "src/ops/full_core_live_path_composition_root_v1"
    / "checkout_independent_credential_os_native_store_item_class_and_value_encoding_v1.py"
)
RUNBOOK = REPO_ROOT / "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md"
OWNER_URI = "fullcore-cred://provider-ref/okx-eea-productive"
UNKNOWN_URI = "fullcore-cred://provider-ref/unknown-identifier"
FORBIDDEN_KIND_URI = "fullcore-cred://keychain/okx-eea-productive"
_FORBIDDEN_IMPORTS = (
    "import keyring",
    "from keyring",
    "import subprocess",
    "from subprocess",
    "import ctypes",
    "from ctypes",
    "import urllib",
    "from urllib",
    "import socket",
    "import requests",
    "security find-generic-password",
    "security add-generic-password",
    "Security.framework",
    "SecItemCopyMatching",
    "SecItemAdd",
)
_FORBIDDEN_AUTHORITY_ATTRS = (
    "selection_authority",
    "trading_decision_authority",
    "risk_authority",
    "admission_authority",
    "external_effect_authority",
    "post_authority",
    "send_authority",
    "side",
    "quantity",
    "submission_authority",
)


def test_canonical_provider_ref_maps_to_canonical_dz_identity() -> None:
    identity = resolve_bound_keychain_item_identity_v1(OWNER_URI)
    assert identity.provider_ref_identifier == PROVIDER_REF_IDENTIFIER
    assert identity.keychain_service_id == KEYCHAIN_SERVICE_ID
    assert identity.keychain_account_id == KEYCHAIN_ACCOUNT_ID
    assert identity.source_ref_uri == SOURCE_REF_URI
    proof = prove_fail_closed_adapter_bound_v1()
    assert proof["CANONICAL_DZ_IDENTITY_CONSUMED"] == "true"
    assert proof["KEYCHAIN_SERVICE_ID"] == "peak-trade.full-core.venue-credentials"
    assert proof["KEYCHAIN_ACCOUNT_ID"] == "okx-eea.productive"
    assert proof["PROVIDER_REF_IDENTIFIER"] == "okx-eea-productive"


def test_unknown_provider_ref_fail_closed() -> None:
    adapter = FullCoreCheckoutIndependentFailClosedOsNativeStoreAdapterV1()
    with pytest.raises(
        FullCoreCheckoutIndependentCredentialCapabilityError,
        match="KEYCHAIN_IDENTITY_UNKNOWN_IDENTIFIER",
    ):
        resolve_checkout_independent_credential_capability_v1(
            source_ref=UNKNOWN_URI,
            provider=adapter,
        )
    assert adapter.resolve_dispatch_count == 1


def test_forbidden_source_ref_kind_fail_closed() -> None:
    adapter = FullCoreCheckoutIndependentFailClosedOsNativeStoreAdapterV1()
    with pytest.raises(
        FullCoreCheckoutIndependentCredentialCapabilityError,
        match="MALFORMED_PROVIDER_REFERENCE",
    ):
        resolve_checkout_independent_credential_capability_v1(
            source_ref=FORBIDDEN_KIND_URI,
            provider=adapter,
        )
    assert adapter.resolve_dispatch_count == 0
    parsed = FullCoreCheckoutIndependentCredentialSourceRefV1(
        kind="keychain",
        identifier="okx-eea-productive",
    )
    with pytest.raises(
        FullCoreCheckoutIndependentCredentialCapabilityError,
        match="MALFORMED_PROVIDER_REFERENCE",
    ):
        adapter.resolve_capability_v1(
            source_ref=parsed,
            credential_class="FULL_CORE_VENUE_AUTH_CLASS",
            environment="LIVE",
        )


def test_adapter_constructs_without_keychain_secret_or_material() -> None:
    adapter = bind_fail_closed_os_native_store_adapter_v1()
    assert isinstance(adapter, FullCoreCheckoutIndependentFailClosedOsNativeStoreAdapterV1)
    assert adapter.resolve_dispatch_count == 0
    assert REAL_KEYCHAIN_ACCESS_IMPLEMENTED is False
    assert ADAPTER_REAL_KEYCHAIN_ACCESS_AUTHORIZED is False
    assert EPHEMERAL_MATERIAL_PATH_IMPLEMENTED is False
    source = MODULE_PATH.read_text(encoding="utf-8")
    for forbidden in _FORBIDDEN_IMPORTS:
        assert forbidden not in source


def test_resolve_dispatch_reaches_adapter_structurally() -> None:
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
    assert adapter.last_source_ref_uri == OWNER_URI
    assert RESOLVE_DISPATCH_TO_ADAPTER_IMPLEMENTED is True
    parsed = assert_checkout_independent_source_ref_v1(OWNER_URI)
    assert parsed.identifier == PROVIDER_REF_IDENTIFIER


def test_adapter_ends_before_real_backend_access() -> None:
    adapter = FullCoreCheckoutIndependentFailClosedOsNativeStoreAdapterV1()
    with pytest.raises(
        FullCoreCheckoutIndependentFailClosedOsNativeStoreAdapterError,
        match=REAL_BACKEND_ACCESS_FAIL_CLOSED_CODE,
    ):
        adapter.resolve_capability_v1(
            source_ref=assert_checkout_independent_source_ref_v1(OWNER_URI),
            credential_class="FULL_CORE_VENUE_AUTH_CLASS",
            environment="LIVE",
        )
    assert REAL_KEYCHAIN_ACCESS_IMPLEMENTED is False
    assert PRODUCTIVE_PROVIDER_ACTIVE is False
    with pytest.raises(
        FullCoreCheckoutIndependentCredentialCapabilityError,
        match="PROVIDER_UNAVAILABLE",
    ):
        resolve_checkout_independent_credential_capability_v1(source_ref=OWNER_URI)


def test_real_keychain_access_authorized_remains_false() -> None:
    assert REAL_KEYCHAIN_ACCESS_AUTHORIZED is False
    assert ADAPTER_REAL_KEYCHAIN_ACCESS_AUTHORIZED is False
    with pytest.raises(
        FullCoreCheckoutIndependentCredentialCapabilityError,
        match="REAL_KEYCHAIN_ACCESS_FORBIDDEN",
    ):
        refuse_real_keychain_access_v1()


def test_material_loaded_remains_false_and_true_unreachable() -> None:
    capability = bind_offline_contract_capability_v1(source_ref=OWNER_URI)
    assert capability.material_loaded is False
    assert MATERIAL_LOADED_TRUE_REACHABLE is False
    with pytest.raises(
        FullCoreCheckoutIndependentCredentialCapabilityError,
        match="CREDENTIAL_MATERIAL_LOADED_FORBIDDEN",
    ):
        FullCoreCheckoutIndependentCredentialCapabilityV1(
            capability_id="offline-material-forbidden",
            source_ref=assert_checkout_independent_source_ref_v1(OWNER_URI),
            credential_class="FULL_CORE_VENUE_AUTH_CLASS",
            environment="LIVE",
            bound=True,
            released=False,
            material_loaded=True,
            can_authenticate_private_get=False,
            can_sign=False,
        )


def test_v5_does_not_import_or_join_adapter() -> None:
    source = V5_HOST.read_text(encoding="utf-8")
    assert "checkout_independent_credential_fail_closed_os_native_store_adapter_v1" not in source
    assert "checkout_independent_credential_capability_v1" not in source
    assert "checkout_independent_credential_concrete_backend_item_identity_v1" not in source
    assert "checkout_independent_credential_source_backend_kind_v1" not in source
    assert (
        "checkout_independent_credential_os_native_store_item_class_and_value_encoding_v1"
        not in source
    )
    assert V5_JOINED is False
    assert V5_USES_NEW_PROVIDER is False
    path = default_vault_path_v1(repo_root=REPO_ROOT)
    assert path == REPO_ROOT / ".ops_local" / DEFAULT_VAULT_RELATIVE


def test_no_network_or_venue_imports() -> None:
    for path in (
        MODULE_PATH,
        RESOLVE_MODULE_PATH,
        DX_MODULE_PATH,
        DY_MODULE_PATH,
        DZ_MODULE_PATH,
        EB_MODULE_PATH,
    ):
        source = path.read_text(encoding="utf-8")
        for forbidden in _FORBIDDEN_IMPORTS:
            assert forbidden not in source


def test_authority_non_interference() -> None:
    adapter = FullCoreCheckoutIndependentFailClosedOsNativeStoreAdapterV1()
    before = prove_capability_cannot_mutate_standing_gates_v1()
    proof = prove_adapter_authority_non_interference_v1(adapter)
    assert proof["AUTHORITY_NON_INTERFERENCE_PROVEN"] == "true"
    assert proof["KEYCHAIN_IDENTITY_IMPLIES_CREDENTIAL_POSSESSION"] == "false"
    assert proof["CREDENTIAL_POSSESSION_IMPLIES_SELECTION_AUTHORITY"] == "false"
    assert proof["CREDENTIAL_POSSESSION_IMPLIES_TRADING_DECISION_AUTHORITY"] == "false"
    assert proof["CREDENTIAL_POSSESSION_IMPLIES_RISK_AUTHORITY"] == "false"
    assert proof["CREDENTIAL_POSSESSION_IMPLIES_ADMISSION_AUTHORITY"] == "false"
    assert proof["CREDENTIAL_POSSESSION_IMPLIES_EXTERNAL_EFFECT_AUTHORITY"] == "false"
    assert proof["CREDENTIAL_POSSESSION_IMPLIES_POST_AUTHORITY"] == "false"
    assert proof["CREDENTIAL_POSSESSION_IMPLIES_SEND_AUTHORITY"] == "false"
    assert proof["GET_AUTH_IMPLIES_SEND_AUTHORITY"] == "false"
    assert proof["SIGNING_IMPLIES_SEND_AUTHORITY"] == "false"
    assert proof["CAP23_REMAINS_SELECTION_AUTHORITY"] == "true"
    assert proof["MASTER_V2_DOUBLE_PLAY_REMAINS_TRADING_DECISION_AUTHORITY"] == "true"
    after = prove_capability_cannot_mutate_standing_gates_v1()
    assert before == after
    assert int(MAX_POSITIONS_EFFECTIVE) == 1
    for attr in _FORBIDDEN_AUTHORITY_ATTRS:
        assert not hasattr(adapter, attr)
        assert attr not in adapter.__dict__


def test_dx_dy_dz_semantics_remain() -> None:
    assert SOURCE_BACKEND_CLASS == "OS_NATIVE_SECRET_STORE"
    assert PRODUCTIVE_TARGET_BACKEND == "MACOS_KEYCHAIN"
    assert OFFLINE_ADAPTER_IMPLEMENTED is True
    identity = resolve_bound_keychain_item_identity_v1(OWNER_URI)
    assert identity.source_ref_is_keychain_query == "false"
    dy_source = DY_MODULE_PATH.read_text(encoding="utf-8")
    assert "CONCRETE_KEYCHAIN_SERVICE_BOUND = False" in dy_source
    assert "CONCRETE_KEYCHAIN_ACCOUNT_BOUND = False" in dy_source
    dx_source = DX_MODULE_PATH.read_text(encoding="utf-8")
    assert "provider.resolve_capability_v1" in dx_source or "resolve_fn(" in dx_source
    assert "PRODUCTIVE_BACKEND_ABSENT" in dx_source
    runbook = RUNBOOK.read_text(encoding="utf-8")
    ea = runbook.split("### 11.2.1.EA ", 1)[1].split("### 11.2.1.EB ", 1)[0]
    assert (
        "11.2.1.EA.FULL_CORE_CHECKOUT_INDEPENDENT_FAIL_CLOSED_MACOS_KEYCHAIN_PROVIDER_ADAPTER" in ea
    )
    assert "OFFLINE_ADAPTER_IMPLEMENTED=true" in ea
    assert "REAL_KEYCHAIN_ACCESS_IMPLEMENTED=false" in ea
    assert "REAL_KEYCHAIN_ACCESS_AUTHORIZED=false" in ea
    assert "PRODUCTIVE_PROVIDER_ACTIVE=false" in ea
    assert "V5_USES_NEW_PROVIDER=false" in ea
    assert "REAL_BACKEND_ACCESS_NOT_IMPLEMENTED_AND_NOT_AUTHORIZED" in ea
    assert "GO_CONSUMPTION_OPEN=true" in ea
    dz = runbook.split("### 11.2.1.DZ ", 1)[1].split("### 11.2.1.EA ", 1)[0]
    assert "CONCRETE_BACKEND_ITEM_IDENTITY_BOUND=true" in dz
    assert "GO_CONSUMPTION_OPEN=true" in dz


def test_process_local_release_is_not_backend_deletion() -> None:
    adapter = FullCoreCheckoutIndependentFailClosedOsNativeStoreAdapterV1()
    capability = bind_offline_contract_capability_v1(source_ref=OWNER_URI)
    adapter.release_capability_v1(capability)
    assert adapter.release_dispatch_count == 1
    assert capability.material_loaded is False
