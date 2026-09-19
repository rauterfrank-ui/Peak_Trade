"""Offline macOS Keychain item-class and value-encoding contract tests.

No Keychain access. No vault files. No network. No V5 join. No payload schema.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from src.ops.full_core_live_path_composition_root_v1.checkout_independent_credential_capability_v1 import (
    REAL_BACKEND_ACCESS_FAIL_CLOSED_CODE,
    FullCoreCheckoutIndependentCredentialCapabilityError,
    FullCoreCheckoutIndependentCredentialCapabilityV1,
    bind_offline_contract_capability_v1,
    prove_capability_cannot_mutate_standing_gates_v1,
    resolve_checkout_independent_credential_capability_v1,
)
from src.ops.full_core_live_path_composition_root_v1.checkout_independent_credential_concrete_backend_item_identity_v1 import (
    KEYCHAIN_ACCOUNT_ID,
    KEYCHAIN_SERVICE_ID,
    PROVIDER_REF_IDENTIFIER,
    SOURCE_REF_URI,
)
from src.ops.full_core_live_path_composition_root_v1.checkout_independent_credential_fail_closed_os_native_store_adapter_v1 import (
    FullCoreCheckoutIndependentFailClosedOsNativeStoreAdapterError,
    FullCoreCheckoutIndependentFailClosedOsNativeStoreAdapterV1,
    prove_fail_closed_adapter_bound_v1,
)
from src.ops.full_core_live_path_composition_root_v1.checkout_independent_credential_os_native_store_item_class_and_value_encoding_v1 import (
    EPHEMERAL_MATERIAL_PATH_IMPLEMENTED,
    KEYCHAIN_ITEM_CLASS,
    KEYCHAIN_ITEM_CLASS_OS_CONSTANT_NAME,
    KEYCHAIN_VALUE_DATA_REPRESENTATION,
    KEYCHAIN_VALUE_ENCODING,
    MATERIAL_LOADED_TRUE_REACHABLE,
    PAYLOAD_SCHEMA_BOUND,
    PRODUCTIVE_PROVIDER_ACTIVE,
    REAL_KEYCHAIN_ACCESS_AUTHORIZED,
    REAL_KEYCHAIN_ACCESS_IMPLEMENTED,
    V5_JOINED,
    V5_USES_NEW_PROVIDER,
    assert_keychain_item_class_v1,
    assert_keychain_value_encoding_v1,
    prove_item_class_and_value_encoding_bound_v1,
    prove_item_class_encoding_authority_non_interference_v1,
    refuse_mint_from_item_class_bind_v1,
    refuse_real_keychain_access_from_item_class_bind_v1,
    resolve_bound_keychain_item_class_and_value_encoding_v1,
)
from src.ops.full_core_live_path_composition_root_v1.checkout_independent_credential_source_backend_kind_v1 import (
    PRODUCTIVE_TARGET_BACKEND,
    SOURCE_BACKEND_CLASS,
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
    / "checkout_independent_credential_os_native_store_item_class_and_value_encoding_v1.py"
)
ADAPTER_PATH = (
    REPO_ROOT
    / "src/ops/full_core_live_path_composition_root_v1"
    / "checkout_independent_credential_fail_closed_os_native_store_adapter_v1.py"
)
RESOLVE_MODULE_PATH = (
    REPO_ROOT
    / "src/ops/full_core_live_path_composition_root_v1"
    / "checkout_independent_credential_capability_v1.py"
)
RUNBOOK = REPO_ROOT / "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md"
OWNER_URI = "fullcore-cred://provider-ref/okx-eea-productive"
UNKNOWN_URI = "fullcore-cred://provider-ref/unknown-identifier"
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
    "SecItemUpdate",
    "SecItemDelete",
)


def test_owner_item_class_and_encoding_remain_exact() -> None:
    proof = prove_item_class_and_value_encoding_bound_v1()
    assert proof["KEYCHAIN_ITEM_CLASS"] == "generic-password"
    assert proof["KEYCHAIN_ITEM_CLASS_OS_CONSTANT_NAME"] == "kSecClassGenericPassword"
    assert proof["KEYCHAIN_VALUE_ENCODING"] == "utf-8"
    assert proof["KEYCHAIN_VALUE_DATA_REPRESENTATION"] == "BYTES"
    assert proof["PAYLOAD_SCHEMA_BOUND"] == "false"
    assert KEYCHAIN_ITEM_CLASS == "generic-password"
    assert KEYCHAIN_ITEM_CLASS_OS_CONSTANT_NAME == "kSecClassGenericPassword"
    assert KEYCHAIN_VALUE_ENCODING == "utf-8"
    assert KEYCHAIN_VALUE_DATA_REPRESENTATION == "BYTES"
    assert KEYCHAIN_SERVICE_ID == "peak-trade.full-core.venue-credentials"
    assert KEYCHAIN_ACCOUNT_ID == "okx-eea.productive"
    assert PROVIDER_REF_IDENTIFIER == "okx-eea-productive"
    assert SOURCE_REF_URI == OWNER_URI
    assert PAYLOAD_SCHEMA_BOUND is False
    bound = resolve_bound_keychain_item_class_and_value_encoding_v1(OWNER_URI)
    assert bound.keychain_item_class == "generic-password"
    assert bound.keychain_value_encoding == "utf-8"
    assert bound.keychain_service_id == KEYCHAIN_SERVICE_ID
    assert bound.keychain_account_id == KEYCHAIN_ACCOUNT_ID
    assert bound.payload_schema_bound == "false"
    assert bound.real_keychain_accessed == "false"
    assert bound.credential_material_loaded == "false"


def test_forbidden_item_class_and_encoding_fail_closed() -> None:
    with pytest.raises(
        FullCoreCheckoutIndependentCredentialCapabilityError,
        match="KEYCHAIN_ITEM_CLASS_FORBIDDEN",
    ):
        assert_keychain_item_class_v1("internet-password")
    with pytest.raises(
        FullCoreCheckoutIndependentCredentialCapabilityError,
        match="KEYCHAIN_ITEM_CLASS_FORBIDDEN",
    ):
        assert_keychain_item_class_v1("certificate")
    with pytest.raises(
        FullCoreCheckoutIndependentCredentialCapabilityError,
        match="KEYCHAIN_ITEM_CLASS_DRIFT",
    ):
        assert_keychain_item_class_v1("application-password")
    with pytest.raises(
        FullCoreCheckoutIndependentCredentialCapabilityError,
        match="KEYCHAIN_ITEM_CLASS_NORMALIZATION_FORBIDDEN",
    ):
        assert_keychain_item_class_v1("Generic-Password")
    with pytest.raises(
        FullCoreCheckoutIndependentCredentialCapabilityError,
        match="KEYCHAIN_VALUE_ENCODING_FORBIDDEN",
    ):
        assert_keychain_value_encoding_v1("latin-1")
    with pytest.raises(
        FullCoreCheckoutIndependentCredentialCapabilityError,
        match="KEYCHAIN_VALUE_ENCODING_DRIFT",
    ):
        assert_keychain_value_encoding_v1("utf8")
    with pytest.raises(
        FullCoreCheckoutIndependentCredentialCapabilityError,
        match="KEYCHAIN_VALUE_ENCODING_NORMALIZATION_FORBIDDEN",
    ):
        assert_keychain_value_encoding_v1("UTF-8")


def test_unknown_identifier_still_fail_closed_before_backend() -> None:
    with pytest.raises(
        FullCoreCheckoutIndependentCredentialCapabilityError,
        match="KEYCHAIN_IDENTITY_UNKNOWN_IDENTIFIER",
    ):
        resolve_bound_keychain_item_class_and_value_encoding_v1(UNKNOWN_URI)


def test_payload_schema_remains_unbound() -> None:
    proof = prove_item_class_and_value_encoding_bound_v1()
    assert proof["PAYLOAD_SCHEMA_BOUND"] == "false"
    assert proof["CANARY_VAULT_FIELDS_BOUND_AS_KEYCHAIN_SSOT"] == "false"
    for field in ("api_key", "api_secret", "passphrase"):
        assert field not in proof
        assert field not in proof.values()
    source = MODULE_PATH.read_text(encoding="utf-8")
    assert "PAYLOAD_SCHEMA_BOUND = False" in source
    assert "This is not a payload schema" in source or "not a payload schema" in source.lower()


def test_no_material_load_and_flags_remain_false() -> None:
    capability = bind_offline_contract_capability_v1(source_ref=OWNER_URI)
    assert capability.material_loaded is False
    assert MATERIAL_LOADED_TRUE_REACHABLE is False
    assert EPHEMERAL_MATERIAL_PATH_IMPLEMENTED is False
    assert REAL_KEYCHAIN_ACCESS_IMPLEMENTED is False
    assert REAL_KEYCHAIN_ACCESS_AUTHORIZED is False
    assert PRODUCTIVE_PROVIDER_ACTIVE is False
    assert V5_USES_NEW_PROVIDER is False
    assert V5_JOINED is False
    with pytest.raises(
        FullCoreCheckoutIndependentCredentialCapabilityError,
        match="CREDENTIAL_MATERIAL_LOADED_FORBIDDEN",
    ):
        FullCoreCheckoutIndependentCredentialCapabilityV1(
            capability_id="eb-material-forbidden",
            source_ref=bind_offline_contract_capability_v1(source_ref=OWNER_URI).source_ref,
            credential_class="FULL_CORE_VENUE_AUTH_CLASS",
            environment="LIVE",
            bound=True,
            released=False,
            material_loaded=True,
            can_authenticate_private_get=False,
            can_sign=False,
        )
    with pytest.raises(
        FullCoreCheckoutIndependentCredentialCapabilityError,
        match="REAL_KEYCHAIN_ACCESS_FORBIDDEN",
    ):
        refuse_real_keychain_access_from_item_class_bind_v1()


def test_ea_adapter_still_terminates_at_real_backend_access() -> None:
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
    proof = prove_fail_closed_adapter_bound_v1()
    assert proof["CANONICAL_EB_ITEM_CLASS_CONSUMED"] == "true"
    assert proof["KEYCHAIN_ITEM_CLASS"] == "generic-password"
    assert proof["KEYCHAIN_VALUE_ENCODING"] == "utf-8"
    assert proof["REAL_BACKEND_ACCESS_FAIL_CLOSED_CODE"] == REAL_BACKEND_ACCESS_FAIL_CLOSED_CODE
    with pytest.raises(
        FullCoreCheckoutIndependentCredentialCapabilityError,
        match="PROVIDER_UNAVAILABLE",
    ):
        resolve_checkout_independent_credential_capability_v1(source_ref=OWNER_URI)


def test_no_forbidden_backend_imports_or_calls() -> None:
    for path in (MODULE_PATH, ADAPTER_PATH, RESOLVE_MODULE_PATH):
        source = path.read_text(encoding="utf-8")
        for forbidden in _FORBIDDEN_IMPORTS:
            assert forbidden not in source


def test_v5_host_absent_and_does_not_join_eb() -> None:
    assert not V5_HOST.is_file()
    assert V5_JOINED is False
    assert V5_USES_NEW_PROVIDER is False
    k1_cycle = (
        REPO_ROOT
        / "src/ops/full_core_live_path_composition_root_v1"
        / "current_productive_governed_cycle_orchestrator_v1.py"
    )
    assert "default_vault_path_v1" not in k1_cycle.read_text(encoding="utf-8")


def test_authority_non_interference_regression() -> None:
    bound = resolve_bound_keychain_item_class_and_value_encoding_v1(OWNER_URI)
    before = prove_capability_cannot_mutate_standing_gates_v1()
    proof = prove_item_class_encoding_authority_non_interference_v1(bound)
    assert proof["AUTHORITY_NON_INTERFERENCE_PROVEN"] == "true"
    assert proof["CREDENTIAL_POSSESSION_IMPLIES_SELECTION_AUTHORITY"] == "false"
    assert proof["CREDENTIAL_POSSESSION_IMPLIES_TRADING_DECISION_AUTHORITY"] == "false"
    assert proof["CREDENTIAL_POSSESSION_IMPLIES_RISK_AUTHORITY"] == "false"
    assert proof["CREDENTIAL_POSSESSION_IMPLIES_ADMISSION_AUTHORITY"] == "false"
    assert proof["CREDENTIAL_POSSESSION_IMPLIES_EXTERNAL_EFFECT_AUTHORITY"] == "false"
    assert proof["CREDENTIAL_POSSESSION_IMPLIES_POST_AUTHORITY"] == "false"
    assert proof["CREDENTIAL_POSSESSION_IMPLIES_SEND_AUTHORITY"] == "false"
    assert proof["GET_AUTH_IMPLIES_SEND_AUTHORITY"] == "false"
    assert proof["SIGNING_IMPLIES_SEND_AUTHORITY"] == "false"
    after = prove_capability_cannot_mutate_standing_gates_v1()
    assert before == after
    assert int(MAX_POSITIONS_EFFECTIVE) == 1
    assert SOURCE_BACKEND_CLASS == "OS_NATIVE_SECRET_STORE"
    assert PRODUCTIVE_TARGET_BACKEND == "MACOS_KEYCHAIN"
    with pytest.raises(
        FullCoreCheckoutIndependentCredentialCapabilityError,
        match="CREDENTIAL_CAPABILITY_CANNOT_MINT_PERMIT",
    ):
        refuse_mint_from_item_class_bind_v1(bound)


def test_runbook_eb_persist_and_ea_bounds() -> None:
    eb = (
        REPO_ROOT
        / "src/ops/full_core_live_path_composition_root_v1"
        / "checkout_independent_credential_os_native_store_item_class_and_value_encoding_v1.py"
    ).read_text(encoding="utf-8")
    assert "11.2.1.EB.FULL_CORE_MACOS_KEYCHAIN_ITEM_CLASS_AND_VALUE_ENCODING" in eb
    assert 'KEYCHAIN_ITEM_CLASS = "generic-password"' in eb
    assert "KEYCHAIN_VALUE_ENCODING" in eb
    assert "V5_USES_NEW_PROVIDER = False" in eb
    assert "REAL_KEYCHAIN_ACCESS_IMPLEMENTED = False" in eb
    assert "REAL_KEYCHAIN_ACCESS_AUTHORIZED = False" in eb
    ea = (
        REPO_ROOT
        / "src/ops/full_core_live_path_composition_root_v1"
        / "checkout_independent_credential_fail_closed_os_native_store_adapter_v1.py"
    ).read_text(encoding="utf-8")
    assert "OFFLINE_ADAPTER_IMPLEMENTED = True" in ea
    assert "REAL_BACKEND_ACCESS_FAIL_CLOSED_CODE" in ea
