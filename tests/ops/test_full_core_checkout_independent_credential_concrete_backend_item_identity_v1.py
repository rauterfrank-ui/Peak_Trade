"""Offline concrete macOS Keychain item-identity contract tests.

No Keychain access. No vault files. No network. No V5 join.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from src.ops.full_core_live_path_composition_root_v1.checkout_independent_credential_capability_v1 import (
    FullCoreCheckoutIndependentCredentialCapabilityError,
    assert_checkout_independent_source_ref_v1,
    prove_capability_cannot_mutate_standing_gates_v1,
)
from src.ops.full_core_live_path_composition_root_v1.checkout_independent_credential_concrete_backend_item_identity_v1 import (
    CONCRETE_BACKEND_ITEM_IDENTITY_BOUND,
    CONCRETE_KEYCHAIN_ACCOUNT_BOUND,
    CONCRETE_KEYCHAIN_SERVICE_BOUND,
    KEYCHAIN_ACCOUNT_ID,
    KEYCHAIN_SERVICE_ID,
    PRODUCTIVE_PROVIDER_ACTIVE,
    PROVIDER_REF_IDENTIFIER,
    PROVIDER_REF_IDENTIFIER_BOUND,
    PROVIDER_REF_TO_KEYCHAIN_IDENTITY_MAPPING_DEFINED,
    REAL_KEYCHAIN_ACCESS_AUTHORIZED,
    SOURCE_REF_URI,
    V5_JOINED,
    FullCoreCheckoutIndependentCredentialMacosKeychainItemIdentityError,
    prove_authority_non_interference_v1,
    prove_concrete_keychain_item_identity_bound_v1,
    prove_owner_identifier_values_exact_v1,
    prove_productive_backend_still_absent_from_identity_bind_v1,
    refuse_mint_from_keychain_identity_bind_v1,
    refuse_real_keychain_access_from_identity_bind_v1,
    resolve_bound_keychain_item_identity_v1,
)
from src.ops.full_core_live_path_composition_root_v1.checkout_independent_credential_source_backend_kind_v1 import (
    CONCRETE_BACKEND_ITEM_IDENTITY_BOUND as DY_CONCRETE_BACKEND_ITEM_IDENTITY_BOUND,
)
from src.ops.full_core_live_path_composition_root_v1.checkout_independent_credential_source_backend_kind_v1 import (
    CONCRETE_KEYCHAIN_ACCOUNT_BOUND as DY_CONCRETE_KEYCHAIN_ACCOUNT_BOUND,
)
from src.ops.full_core_live_path_composition_root_v1.checkout_independent_credential_source_backend_kind_v1 import (
    CONCRETE_KEYCHAIN_SERVICE_BOUND as DY_CONCRETE_KEYCHAIN_SERVICE_BOUND,
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
    / "checkout_independent_credential_concrete_backend_item_identity_v1.py"
)
DY_MODULE_PATH = (
    REPO_ROOT
    / "src/ops/full_core_live_path_composition_root_v1"
    / "checkout_independent_credential_source_backend_kind_v1.py"
)
RUNBOOK = REPO_ROOT / "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md"
OWNER_URI = "fullcore-cred://provider-ref/okx-eea-productive"
FIXTURE_URI = "fullcore-cred://provider-ref/phase-b-os-native-store"


def test_owner_identifier_values_remain_exact() -> None:
    proof = prove_owner_identifier_values_exact_v1()
    assert proof["OWNER_IDENTIFIER_VALUES_VALIDATED"] == "true"
    assert proof["VALUES_NORMALIZED"] == "false"
    assert proof["VALUES_INVENTED"] == "false"
    assert KEYCHAIN_SERVICE_ID == "peak-trade.full-core.venue-credentials"
    assert KEYCHAIN_ACCOUNT_ID == "okx-eea.productive"
    assert PROVIDER_REF_IDENTIFIER == "okx-eea-productive"
    assert SOURCE_REF_URI == OWNER_URI
    assert proof["KEYCHAIN_SERVICE_ID"] == KEYCHAIN_SERVICE_ID
    assert proof["KEYCHAIN_ACCOUNT_ID"] == KEYCHAIN_ACCOUNT_ID
    assert proof["PROVIDER_REF_IDENTIFIER"] == PROVIDER_REF_IDENTIFIER
    parsed = assert_checkout_independent_source_ref_v1(SOURCE_REF_URI)
    assert parsed.kind == "provider-ref"
    assert parsed.identifier == "okx-eea-productive"
    assert parsed.as_uri() == OWNER_URI


def test_concrete_identity_bound_without_rewriting_dy_constants() -> None:
    proof = prove_concrete_keychain_item_identity_bound_v1()
    assert proof["CONCRETE_KEYCHAIN_SERVICE_BOUND"] == "true"
    assert proof["CONCRETE_KEYCHAIN_ACCOUNT_BOUND"] == "true"
    assert proof["CONCRETE_BACKEND_ITEM_IDENTITY_BOUND"] == "true"
    assert proof["PROVIDER_REF_IDENTIFIER_BOUND"] == "true"
    assert proof["PROVIDER_REF_TO_KEYCHAIN_IDENTITY_MAPPING_DEFINED"] == "true"
    assert proof["SOURCE_REF_IS_IDENTIFIER_ONLY"] == "true"
    assert proof["SOURCE_REF_IS_KEYCHAIN_QUERY"] == "false"
    assert proof["REAL_KEYCHAIN_ACCESS_AUTHORIZED"] == "false"
    assert CONCRETE_KEYCHAIN_SERVICE_BOUND is True
    assert CONCRETE_KEYCHAIN_ACCOUNT_BOUND is True
    assert CONCRETE_BACKEND_ITEM_IDENTITY_BOUND is True
    assert PROVIDER_REF_IDENTIFIER_BOUND is True
    assert PROVIDER_REF_TO_KEYCHAIN_IDENTITY_MAPPING_DEFINED is True
    assert REAL_KEYCHAIN_ACCESS_AUTHORIZED is False
    assert PRODUCTIVE_PROVIDER_ACTIVE is False
    assert V5_JOINED is False
    assert DY_CONCRETE_KEYCHAIN_SERVICE_BOUND is False
    assert DY_CONCRETE_KEYCHAIN_ACCOUNT_BOUND is False
    assert DY_CONCRETE_BACKEND_ITEM_IDENTITY_BOUND is False


def test_provider_ref_maps_to_owner_keychain_identity() -> None:
    identity = resolve_bound_keychain_item_identity_v1(OWNER_URI)
    assert identity.provider_ref_identifier == "okx-eea-productive"
    assert identity.source_ref_kind == "provider-ref"
    assert identity.source_ref_uri == OWNER_URI
    assert identity.keychain_service_id == "peak-trade.full-core.venue-credentials"
    assert identity.keychain_account_id == "okx-eea.productive"
    assert identity.source_ref_is_identifier_only == "true"
    assert identity.source_ref_is_keychain_query == "false"
    assert identity.keychain_identity_implies_credential_possession == "false"
    assert identity.real_keychain_accessed == "false"
    assert identity.credential_material_loaded == "false"
    payload = identity.to_dict()
    for forbidden in (
        "selection_authority",
        "trading_decision_authority",
        "risk_authority",
        "admission_authority",
        "external_effect_authority",
        "post_authority",
        "send_authority",
        "side",
        "quantity",
        "api_key",
        "secret",
        "passphrase",
    ):
        assert forbidden not in payload


def test_unknown_and_fixture_identifiers_fail_closed() -> None:
    with pytest.raises(
        FullCoreCheckoutIndependentCredentialMacosKeychainItemIdentityError,
        match="KEYCHAIN_IDENTITY_UNKNOWN_IDENTIFIER",
    ):
        resolve_bound_keychain_item_identity_v1(FIXTURE_URI)
    with pytest.raises(
        FullCoreCheckoutIndependentCredentialMacosKeychainItemIdentityError,
        match="KEYCHAIN_IDENTITY_UNKNOWN_IDENTIFIER",
    ):
        resolve_bound_keychain_item_identity_v1(
            "fullcore-cred://provider-ref/okx-eea-productive-other"
        )
    with pytest.raises(
        FullCoreCheckoutIndependentCredentialCapabilityError,
        match="MALFORMED_PROVIDER_REFERENCE",
    ):
        resolve_bound_keychain_item_identity_v1("fullcore-cred://keychain/okx-eea-productive")


def test_no_normalization_of_owner_values() -> None:
    with pytest.raises(
        FullCoreCheckoutIndependentCredentialCapabilityError,
        match="MALFORMED_PROVIDER_REFERENCE",
    ):
        resolve_bound_keychain_item_identity_v1("fullcore-cred://provider-ref/okx-eea-productive/")
    with pytest.raises(
        FullCoreCheckoutIndependentCredentialCapabilityError,
        match="MALFORMED_PROVIDER_REFERENCE",
    ):
        resolve_bound_keychain_item_identity_v1("fullcore-cred://provider-ref/OKX-EEA-PRODUCTIVE")


def test_authority_non_interference() -> None:
    identity = resolve_bound_keychain_item_identity_v1(OWNER_URI)
    before = prove_capability_cannot_mutate_standing_gates_v1()
    proof = prove_authority_non_interference_v1(identity, standing_before=before)
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
    assert proof["SELECTION_AUTHORITY"] == "false"
    assert proof["TRADING_DECISION_AUTHORITY"] == "false"
    assert proof["POST_AUTHORITY"] == "false"
    assert proof["SEND_AUTHORITY"] == "false"
    assert proof["CAP23_REMAINS_SELECTION_AUTHORITY"] == "true"
    assert proof["MASTER_V2_DOUBLE_PLAY_REMAINS_TRADING_DECISION_AUTHORITY"] == "true"
    assert int(MAX_POSITIONS_EFFECTIVE) == 1
    with pytest.raises(
        FullCoreCheckoutIndependentCredentialCapabilityError,
        match="CREDENTIAL_CAPABILITY_CANNOT_MINT_PERMIT",
    ):
        refuse_mint_from_keychain_identity_bind_v1(identity)


def test_real_keychain_access_forbidden() -> None:
    with pytest.raises(
        FullCoreCheckoutIndependentCredentialMacosKeychainItemIdentityError,
        match="REAL_KEYCHAIN_ACCESS_FORBIDDEN",
    ):
        refuse_real_keychain_access_from_identity_bind_v1()


def test_productive_provider_and_v5_remain_unjoined() -> None:
    proof = prove_productive_backend_still_absent_from_identity_bind_v1()
    assert proof["PRODUCTIVE_BACKEND_JOINED"] == "false"
    assert proof["PRODUCTIVE_PROVIDER_ACTIVE"] == "false"
    assert proof["V5_JOINED"] == "false"
    source = V5_HOST.read_text(encoding="utf-8")
    assert "checkout_independent_credential_concrete_backend_item_identity_v1" not in source
    assert "checkout_independent_credential_capability_v1" not in source
    path = default_vault_path_v1(repo_root=REPO_ROOT)
    assert path == REPO_ROOT / ".ops_local" / DEFAULT_VAULT_RELATIVE


def test_module_has_no_keychain_or_network_imports() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    for forbidden in (
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
    ):
        assert forbidden not in source
    dy_source = DY_MODULE_PATH.read_text(encoding="utf-8")
    assert "CONCRETE_KEYCHAIN_SERVICE_BOUND = False" in dy_source
    assert "CONCRETE_KEYCHAIN_ACCOUNT_BOUND = False" in dy_source
    runbook = RUNBOOK.read_text(encoding="utf-8")
    dz = runbook.split("### 11.2.1.DZ ", 1)[1].split("### 11.2.1.EA ", 1)[0]
    assert "11.2.1.DZ.FULL_CORE_CONCRETE_MACOS_KEYCHAIN_ITEM_IDENTITY" in dz
    assert "KEYCHAIN_SERVICE_ID=peak-trade.full-core.venue-credentials" in dz
    assert "KEYCHAIN_ACCOUNT_ID=okx-eea.productive" in dz
    assert "PROVIDER_REF_IDENTIFIER=okx-eea-productive" in dz
    assert "CONCRETE_BACKEND_ITEM_IDENTITY_BOUND=true" in dz
    assert "PREVIOUS_V5_RUNTIME_GO_STATUS=DEFINED_NOT_CONSUMED" in dz
    assert "GO_CONSUMPTION_OPEN=true" in dz
    assert "REAL_KEYCHAIN_ACCESSED=false" in dz
    assert "AUTHORITY_NON_INTERFERENCE_PROVEN=true" in dz
    dy = runbook.split("### 11.2.1.DY ", 1)[1].split("### 11.2.1.DZ ", 1)[0]
    assert "CONCRETE_KEYCHAIN_SERVICE_BOUND=false" in dy
    assert "CONCRETE_KEYCHAIN_ACCOUNT_BOUND=false" in dy
    assert "CONCRETE_BACKEND_ITEM_IDENTITY_BOUND=false" in dy
