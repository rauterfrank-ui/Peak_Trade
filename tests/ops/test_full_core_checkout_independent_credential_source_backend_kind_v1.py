"""Offline Option-4 source-backend-kind contract tests.

No Keychain access. No vault files. No network. No V5 join.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from src.ops.full_core_live_path_composition_root_v1.checkout_independent_credential_capability_v1 import (
    ALLOWED_SOURCE_KIND,
    FullCoreCheckoutIndependentCredentialCapabilityError,
    assert_checkout_independent_source_ref_v1,
    prove_capability_cannot_mutate_standing_gates_v1,
    prove_capability_does_not_upgrade_standing_gates_v1,
)
from src.ops.full_core_live_path_composition_root_v1.checkout_independent_credential_source_backend_kind_v1 import (
    CHECKOUT_INDEPENDENT_REQUIRED,
    CONCRETE_BACKEND_ITEM_IDENTITY_BOUND,
    PRODUCTIVE_PROVIDER_ACTIVE,
    PRODUCTIVE_TARGET_BACKEND,
    REAL_KEYCHAIN_ACCESS_AUTHORIZED,
    SOURCE_BACKEND_CLASS,
    SOURCE_LOCATION_BOUND,
    SOURCE_LOCATION_DERIVED_FROM_REPO_ROOT,
    SOURCE_LOCATION_IS_FILESYSTEM_PATH,
    SOURCE_REF_KIND,
    V5_JOINED,
    FullCoreCheckoutIndependentCredentialSourceBackendKindError,
    acquire_offline_ephemeral_capability_v1,
    current_lifetime_state_v1,
    fail_offline_ephemeral_capability_v1,
    prove_handle_release_is_not_backend_deletion_v1,
    prove_lifetime_contract_defined_v1,
    prove_owner_backend_choice_bound_v1,
    prove_productive_backend_still_absent_v1,
    prove_source_ref_identifier_only_semantics_v1,
    prove_zero_retention_semantics_v1,
    refuse_mint_from_source_backend_bind_v1,
    refuse_real_keychain_access_v1,
    release_offline_ephemeral_capability_v1,
    use_offline_ephemeral_capability_v1,
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
    / "checkout_independent_credential_source_backend_kind_v1.py"
)
RUNBOOK = REPO_ROOT / "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md"
VALID_REF = "fullcore-cred://provider-ref/phase-b-os-native-store"


def test_owner_backend_choice_bound() -> None:
    proof = prove_owner_backend_choice_bound_v1()
    assert proof["OWNER_BACKEND_CHOICE_BOUND"] == "true"
    assert SOURCE_BACKEND_CLASS == "OS_NATIVE_SECRET_STORE"
    assert PRODUCTIVE_TARGET_BACKEND == "MACOS_KEYCHAIN"
    assert SOURCE_REF_KIND == "provider-ref"
    assert SOURCE_REF_KIND == ALLOWED_SOURCE_KIND
    assert CHECKOUT_INDEPENDENT_REQUIRED is True
    assert SOURCE_LOCATION_BOUND is True
    assert SOURCE_LOCATION_IS_FILESYSTEM_PATH is False
    assert SOURCE_LOCATION_DERIVED_FROM_REPO_ROOT is False
    assert CONCRETE_BACKEND_ITEM_IDENTITY_BOUND is False
    assert REAL_KEYCHAIN_ACCESS_AUTHORIZED is False
    assert PRODUCTIVE_PROVIDER_ACTIVE is False
    assert V5_JOINED is False


def test_source_ref_remains_identifier_only_provider_ref() -> None:
    proof = prove_source_ref_identifier_only_semantics_v1(VALID_REF)
    assert proof["SOURCE_REF_KIND"] == "provider-ref"
    assert proof["SOURCE_REF_IS_IDENTIFIER_ONLY"] == "true"
    assert proof["SOURCE_REF_IS_FILESYSTEM_PATH"] == "false"
    assert proof["SOURCE_REF_IS_KEYCHAIN_QUERY"] == "false"
    parsed = assert_checkout_independent_source_ref_v1(VALID_REF)
    assert parsed.kind != "keychain"
    with pytest.raises(
        FullCoreCheckoutIndependentCredentialCapabilityError,
        match="MALFORMED_PROVIDER_REFERENCE",
    ):
        assert_checkout_independent_source_ref_v1("fullcore-cred://keychain/item")


def test_source_ref_rejects_checkout_identity_as_authority() -> None:
    with pytest.raises(
        FullCoreCheckoutIndependentCredentialCapabilityError,
        match="CHECKOUT_IDENTITY_MUST_NOT_BE_CREDENTIAL_AUTHORITY",
    ):
        prove_source_ref_identifier_only_semantics_v1("fullcore-cred://provider-ref/worktree-bound")


def test_acquire_use_release_failure_lifetime() -> None:
    lifetime = prove_lifetime_contract_defined_v1()
    assert lifetime["EPHEMERAL_LIFETIME_CONTRACT_DEFINED"] == "true"
    capability = acquire_offline_ephemeral_capability_v1(source_ref=VALID_REF)
    assert current_lifetime_state_v1(capability) == "ACQUIRED"
    assert capability.material_loaded is False
    used = use_offline_ephemeral_capability_v1(capability)
    assert used["state"] == "IN_USE"
    assert used["material_loaded"] == "false"
    assert used["use_loads_material"] == "false"
    assert used["use_performs_network"] == "false"
    assert used["POST_AUTHORITY"] == "false"
    assert current_lifetime_state_v1(capability) == "IN_USE"
    record = release_offline_ephemeral_capability_v1(capability)
    assert record.state == "RELEASED"
    assert record.handle_released == "true"
    assert record.backend_item_deleted == "false"
    prove_handle_release_is_not_backend_deletion_v1(record)
    with pytest.raises(
        FullCoreCheckoutIndependentCredentialSourceBackendKindError,
        match="CAPABILITY_ALREADY_RELEASED",
    ):
        use_offline_ephemeral_capability_v1(capability)
    with pytest.raises(
        FullCoreCheckoutIndependentCredentialSourceBackendKindError,
        match="CAPABILITY_ALREADY_RELEASED",
    ):
        release_offline_ephemeral_capability_v1(capability)


def test_failure_path_does_not_access_keychain() -> None:
    capability = acquire_offline_ephemeral_capability_v1(source_ref=VALID_REF)
    with pytest.raises(
        FullCoreCheckoutIndependentCredentialSourceBackendKindError,
        match="ENVIRONMENT_MISMATCH",
    ):
        fail_offline_ephemeral_capability_v1(capability, reason="ENVIRONMENT_MISMATCH")
    assert current_lifetime_state_v1(capability) == "FAILED"
    with pytest.raises(
        FullCoreCheckoutIndependentCredentialSourceBackendKindError,
        match="CAPABILITY_LIFETIME_FAILED",
    ):
        use_offline_ephemeral_capability_v1(capability)


def test_zero_retention_is_unloaded_handle_only() -> None:
    capability = acquire_offline_ephemeral_capability_v1(source_ref=VALID_REF)
    proof = prove_zero_retention_semantics_v1(capability)
    assert proof["ZERO_RETENTION_SEMANTICS_DEFINED"] == "true"
    assert proof["PLAINTEXT_WAS_LOADED"] == "false"
    assert proof["ZERO_RETENTION_OF_PLAINTEXT_IN_THIS_PROCESS"] == "true"
    assert proof["PROCESS_MEMORY_WIPE_PROVEN"] == "false"
    assert proof["BACKEND_ITEM_DELETED"] == "false"
    assert proof["HANDLE_RELEASE_EQUALS_BACKEND_DELETION"] == "false"
    record = release_offline_ephemeral_capability_v1(capability)
    released_proof = prove_zero_retention_semantics_v1(
        capability.__class__(
            capability_id=capability.capability_id,
            source_ref=capability.source_ref,
            credential_class=capability.credential_class,
            environment=capability.environment,
            bound=False,
            released=True,
            material_loaded=False,
            can_authenticate_private_get=False,
            can_sign=False,
        )
    )
    assert released_proof["BACKEND_ITEM_DELETED"] == "false"
    assert record.backend_item_deleted == "false"


def test_real_keychain_access_forbidden() -> None:
    with pytest.raises(
        FullCoreCheckoutIndependentCredentialSourceBackendKindError,
        match="REAL_KEYCHAIN_ACCESS_FORBIDDEN",
    ):
        refuse_real_keychain_access_v1()


def test_productive_provider_and_v5_remain_unjoined() -> None:
    proof = prove_productive_backend_still_absent_v1(source_ref=VALID_REF)
    assert proof["PRODUCTIVE_BACKEND_JOINED"] == "false"
    assert proof["PRODUCTIVE_PROVIDER_ACTIVE"] == "false"
    assert proof["V5_JOINED"] == "false"
    assert not V5_HOST.is_file()
    k1_cycle = (
        REPO_ROOT
        / "src/ops/full_core_live_path_composition_root_v1"
        / "current_productive_governed_cycle_orchestrator_v1.py"
    )
    assert "default_vault_path_v1" not in k1_cycle.read_text(encoding="utf-8")


def test_capability_still_cannot_mint_or_mutate_gates() -> None:
    before = prove_capability_cannot_mutate_standing_gates_v1()
    capability = acquire_offline_ephemeral_capability_v1(source_ref=VALID_REF)
    after = prove_capability_does_not_upgrade_standing_gates_v1(capability, before=before)
    assert after == before
    with pytest.raises(
        FullCoreCheckoutIndependentCredentialCapabilityError,
        match="CREDENTIAL_CAPABILITY_CANNOT_MINT_PERMIT",
    ):
        refuse_mint_from_source_backend_bind_v1(capability)
    assert int(MAX_POSITIONS_EFFECTIVE) == 1


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
    assert "CONCRETE_KEYCHAIN_SERVICE_BOUND = False" in source
    assert REAL_KEYCHAIN_ACCESS_AUTHORIZED is False
    assert V5_JOINED is False
