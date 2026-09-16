"""Offline Full-Core checkout-independent credential capability contract V1.

No network. No vault files. No real credentials. No V5 join.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from src.ops.full_core_live_path_composition_root_v1.checkout_independent_credential_capability_v1 import (
    ALLOWED_SOURCE_KIND,
    AUTONOMOUS_EXECUTOR_FORBIDDEN_ACTIONS,
    CHECKOUT_INDEPENDENT_PRODUCTIVE_PROVIDER_ACTIVE,
    CREDENTIAL_POSSESSION_ALONE_GRANTS_NO_POST_AUTHORITY,
    CREDENTIAL_POSSESSION_GRANTS_NO_TRADING_AUTHORITY,
    EXECUTION_AUTONOMY_TRADING_DECISION_AUTHORITY,
    GET_AUTH_CAPABILITY_IMPLIES_POST_AUTHORITY,
    PRODUCTIVE_BACKEND_JOINED,
    REAL_BACKEND_ACCESS_FAIL_CLOSED_CODE,
    REQUIRED_CREDENTIAL_CLASS,
    REQUIRED_ENVIRONMENT,
    SIGNING_CAPABILITY_IMPLIES_SEND_AUTHORITY,
    V5_JOINED,
    FullCoreCheckoutIndependentCredentialCapabilityError,
    FullCoreCheckoutIndependentCredentialCapabilityV1,
    assert_checkout_independent_source_ref_v1,
    bind_offline_contract_capability_v1,
    prove_autonomous_executor_boundary_v1,
    prove_capability_cannot_mutate_standing_gates_v1,
    prove_capability_does_not_upgrade_standing_gates_v1,
    prove_capability_grants_no_trading_or_post_authority_v1,
    prove_capability_serialization_has_no_plaintext_v1,
    prove_repo_root_not_provider_authority_v1,
    prove_worktree_identity_not_required_v1,
    refuse_mint_external_effect_permit_from_credential_capability_v1,
    release_checkout_independent_credential_capability_v1,
    resolve_checkout_independent_credential_capability_v1,
)
from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    EXTERNAL_EFFECT_AUTHORIZED,
    LIVE_ARMED,
    LIVE_ENABLED,
    POST_ALLOWED,
    REAL_VENUE_POST_ALLOWED,
    SUBMISSION_AUTHORIZED,
    WIRE_SEND_PERMITTED,
)
from src.ops.full_core_live_path_composition_root_v1.gated_productive_wire_transport_v1 import (
    FullCoreSendCredentialHandleV1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.live_credential_ephemeral_v1 import (
    LiveCanaryEphemeralCredentialHandleV1,
    LiveCanaryVaultBackendPortV1,
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
CANARY_EPHEMERAL = (
    REPO_ROOT
    / "src/ops/section_11_13_5_live_canary_minimum_exposure_v1"
    / "live_credential_ephemeral_v1.py"
)
VALID_REF = "fullcore-cred://provider-ref/phase-a-offline-contract"


def _capability(**kwargs: object) -> FullCoreCheckoutIndependentCredentialCapabilityV1:
    return bind_offline_contract_capability_v1(source_ref=VALID_REF, **kwargs)


def test_provider_unavailable_fail_closed() -> None:
    with pytest.raises(
        FullCoreCheckoutIndependentCredentialCapabilityError, match="PROVIDER_UNAVAILABLE"
    ):
        resolve_checkout_independent_credential_capability_v1(
            source_ref=VALID_REF,
            provider=None,
        )


def test_malformed_provider_reference_fail_closed() -> None:
    for raw in (
        "",
        "file:///tmp/vault.json",
        "secretref://vault/x",
        "not-a-uri",
        "fullcore-cred://file/x",
    ):
        with pytest.raises(
            FullCoreCheckoutIndependentCredentialCapabilityError,
            match="MALFORMED_PROVIDER_REFERENCE|PROVIDER_REFERENCE_MISSING",
        ):
            assert_checkout_independent_source_ref_v1(raw)


def test_environment_mismatch_fail_closed() -> None:
    with pytest.raises(
        FullCoreCheckoutIndependentCredentialCapabilityError, match="ENVIRONMENT_MISMATCH"
    ):
        bind_offline_contract_capability_v1(source_ref=VALID_REF, environment="TESTNET")


def test_credential_class_mismatch_fail_closed() -> None:
    with pytest.raises(
        FullCoreCheckoutIndependentCredentialCapabilityError, match="CREDENTIAL_CLASS_MISMATCH"
    ):
        bind_offline_contract_capability_v1(
            source_ref=VALID_REF,
            credential_class="LIVE_CANARY_MINIMUM_EXPOSURE_TRADE_API_KEY",
        )


def test_checkout_worktree_identity_not_required() -> None:
    proof = prove_worktree_identity_not_required_v1(checkout_identity=None)
    assert proof["WORKTREE_IDENTITY_REQUIRED"] == "false"
    assert proof["GIT_WORKTREE_CREATION_IMPLIES_CREDENTIAL_DUPLICATION"] == "false"
    capability = _capability()
    assert capability.checkout_identity == ""


def test_repo_root_not_provider_authority() -> None:
    proof = prove_repo_root_not_provider_authority_v1(repo_root=None)
    assert proof["REPO_ROOT_IS_CREDENTIAL_AUTHORITY"] == "false"
    with pytest.raises(
        FullCoreCheckoutIndependentCredentialCapabilityError,
        match="CHECKOUT_IDENTITY_MUST_NOT_BE_CREDENTIAL_AUTHORITY",
    ):
        resolve_checkout_independent_credential_capability_v1(
            source_ref=VALID_REF,
            repo_root=str(REPO_ROOT),
        )


def test_serialization_contains_no_plaintext_credential_fields() -> None:
    capability = _capability()
    prove_capability_serialization_has_no_plaintext_v1(capability)
    payload = capability.to_dict()
    claims = capability.to_claims()
    log_safe = capability.to_log_safe()
    for blob in (payload, claims, log_safe):
        keys = {str(key).lower() for key in blob}
        assert "api_key" not in keys
        assert "api_secret" not in keys
        assert "passphrase" not in keys
        assert "secret" not in keys
    assert payload["material_loaded"] == "false"
    assert payload["plaintext_present"] == "false"


def test_capability_does_not_expose_trading_or_post_authority() -> None:
    capability = _capability()
    proof = prove_capability_grants_no_trading_or_post_authority_v1(capability)
    assert proof["SELECTION_AUTHORITY"] == "false"
    assert proof["TRADING_DECISION_AUTHORITY"] == "false"
    assert proof["RISK_AUTHORITY"] == "false"
    assert proof["ADMISSION_AUTHORITY"] == "false"
    assert proof["EXTERNAL_EFFECT_AUTHORITY"] == "false"
    assert proof["POST_AUTHORITY"] == "false"
    assert CREDENTIAL_POSSESSION_GRANTS_NO_TRADING_AUTHORITY is True
    assert CREDENTIAL_POSSESSION_ALONE_GRANTS_NO_POST_AUTHORITY is True
    assert EXECUTION_AUTONOMY_TRADING_DECISION_AUTHORITY is False


def test_capability_cannot_mint_external_effect_permit() -> None:
    capability = _capability()
    with pytest.raises(
        FullCoreCheckoutIndependentCredentialCapabilityError,
        match="CREDENTIAL_CAPABILITY_CANNOT_MINT_PERMIT",
    ):
        refuse_mint_external_effect_permit_from_credential_capability_v1(capability)


def test_capability_cannot_mutate_standing_gates() -> None:
    before = prove_capability_cannot_mutate_standing_gates_v1()
    capability = _capability()
    after = prove_capability_does_not_upgrade_standing_gates_v1(capability, before=before)
    assert after == before
    assert LIVE_ENABLED is True
    assert LIVE_ARMED is True
    assert WIRE_SEND_PERMITTED is True
    assert SUBMISSION_AUTHORIZED is True
    assert EXTERNAL_EFFECT_AUTHORIZED is False
    assert REAL_VENUE_POST_ALLOWED is False
    assert POST_ALLOWED is False
    assert after["EXTERNAL_EFFECT_AUTHORIZED"] == "false"
    assert after["POST_ALLOWED"] == "false"


def test_get_auth_capability_does_not_imply_post_authority() -> None:
    capability = _capability(can_authenticate_private_get=True, can_sign=True)
    assert capability.can_authenticate_private_get is True
    assert capability.post_authority is False
    assert GET_AUTH_CAPABILITY_IMPLIES_POST_AUTHORITY is False
    prove_capability_grants_no_trading_or_post_authority_v1(capability)


def test_signing_capability_does_not_imply_send_authority() -> None:
    capability = _capability(can_sign=True)
    assert capability.can_sign is True
    assert capability.send_authority is False
    assert SIGNING_CAPABILITY_IMPLIES_SEND_AUTHORITY is False


def test_v5_productive_runtime_source_unchanged() -> None:
    source = V5_HOST.read_text(encoding="utf-8")
    assert "default_vault_path_v1" in source
    assert "checkout_independent_credential_capability_v1" not in source
    assert "FullCoreCheckoutIndependentCredentialCapabilityV1" not in source
    assert V5_JOINED is False


def test_existing_default_file_vault_path_unchanged() -> None:
    path = default_vault_path_v1(repo_root=REPO_ROOT)
    assert path == REPO_ROOT / ".ops_local" / DEFAULT_VAULT_RELATIVE
    assert DEFAULT_VAULT_RELATIVE.endswith("secretref_vault.json")


def test_existing_canary_types_unchanged_and_not_full_core_authority() -> None:
    assert CANARY_EPHEMERAL.is_file()
    assert hasattr(LiveCanaryVaultBackendPortV1, "resolve_secretref_material_v1")
    handle = LiveCanaryEphemeralCredentialHandleV1(
        handle_id="offline-canary-handle",
        secret_reference="secretref://vault/peak-trade/live-canary-minimum-exposure/okx",
        material_digest="0" * 64,
        runtime_mode="LIVE",
        credential_class="LIVE_CANARY_MINIMUM_EXPOSURE_TRADE_API_KEY",
        bound=True,
    )
    send = FullCoreSendCredentialHandleV1(handle_id="full-core-send-handle", bound=True)
    capability = _capability()
    assert type(capability) is not type(handle)
    assert type(capability) is not type(send)
    assert not isinstance(capability, FullCoreSendCredentialHandleV1)


def test_max_positions_unchanged() -> None:
    assert int(MAX_POSITIONS_EFFECTIVE) == 1
    snapshot = prove_capability_cannot_mutate_standing_gates_v1()
    assert snapshot["MAX_POSITIONS_EFFECTIVE"] == "1"


def test_no_network_and_no_secret_files_required() -> None:
    module = (
        REPO_ROOT
        / "src/ops/full_core_live_path_composition_root_v1"
        / "checkout_independent_credential_capability_v1.py"
    ).read_text(encoding="utf-8")
    assert "import urllib" not in module
    assert "from urllib" not in module
    assert "import socket" not in module
    assert "import requests" not in module
    capability = _capability()
    assert capability.material_loaded is False
    assert PRODUCTIVE_BACKEND_JOINED is False
    assert CHECKOUT_INDEPENDENT_PRODUCTIVE_PROVIDER_ACTIVE is False


def test_productive_resolve_dispatches_then_remains_fail_closed() -> None:
    calls: list[object] = []

    class _RecordingBackend:
        def resolve_capability_v1(self, **kwargs: object) -> object:
            calls.append(kwargs)
            return bind_offline_contract_capability_v1(source_ref=VALID_REF)

        def release_capability_v1(self, capability: object) -> None:
            del capability

    with pytest.raises(
        FullCoreCheckoutIndependentCredentialCapabilityError,
        match=REAL_BACKEND_ACCESS_FAIL_CLOSED_CODE,
    ):
        resolve_checkout_independent_credential_capability_v1(
            source_ref=VALID_REF,
            provider=_RecordingBackend(),  # type: ignore[arg-type]
        )
    assert len(calls) == 1


def test_release_lifecycle_and_reuse_fail_closed() -> None:
    capability = _capability()
    released = release_checkout_independent_credential_capability_v1(capability)
    assert released.released is True
    assert released.bound is False
    with pytest.raises(
        FullCoreCheckoutIndependentCredentialCapabilityError, match="CAPABILITY_ALREADY_RELEASED"
    ):
        release_checkout_independent_credential_capability_v1(released)


def test_autonomous_executor_boundary() -> None:
    proof = prove_autonomous_executor_boundary_v1()
    assert proof["EXECUTION_AUTONOMY_TRADING_DECISION_AUTHORITY"] == "false"
    for action in (
        "CAP23_OVERRIDE",
        "MASTER_V2_DECISION_MINT",
        "PLAN_ONLY_TO_SUBMIT",
        "POST_FROM_CREDENTIAL_AVAILABILITY",
    ):
        assert action in AUTONOMOUS_EXECUTOR_FORBIDDEN_ACTIONS


def test_allowed_source_kind_is_backend_neutral() -> None:
    parsed = assert_checkout_independent_source_ref_v1(VALID_REF)
    assert parsed.kind == ALLOWED_SOURCE_KIND
    assert parsed.kind != "file"
    assert REQUIRED_ENVIRONMENT == "LIVE"
    assert REQUIRED_CREDENTIAL_CLASS == "FULL_CORE_VENUE_AUTH_CLASS"
