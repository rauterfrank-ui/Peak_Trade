"""DK execute_network credential join — EEA/CZ authority reuse and fail-closed contracts."""

from __future__ import annotations

from pathlib import Path
import pytest

from src.ops.full_core_live_path_composition_root_v1.gated_productive_wire_transport_v1 import (
    FullCoreSendCredentialHandleV1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_execute_network_credential_join_v1 import (
    CREDENTIAL_HANDLE_FAIL_CLOSED_STATUS,
    REQUIRED_CREDENTIAL_CLASS,
    REQUIRED_SECRETREF_URI,
    bind_productive_read_only_get_transport_for_execute_network_v1,
    productive_fail_closed_credential_unavailable_v1,
    release_productive_credential_handle_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_fresh_runtime_cycle_to_exact_envelope_bound_single_use_post_boundary_v1 import (
    OWNER_GO,
    execute_current_productive_fresh_runtime_cycle_to_exact_envelope_bound_v1,
)
from tests.ops._current_productive_29p_chain_integrity_test_helpers_v1 import (
    MockCurrentProductive29PIntegrityBackendV1,
    TRUSTED_TEST_ORIGIN_MAIN_SHA,
)
from tests.ops.test_full_core_current_productive_eea_universe_inventory_to_cap24_and_29p_v1 import (
    _eligible_transport,
)
from tests.ops.test_full_core_current_productive_fresh_runtime_cycle_to_exact_envelope_bound_single_use_post_boundary_v1 import (
    _fresh_get_transport,
)

_INTEGRITY = MockCurrentProductive29PIntegrityBackendV1()
_REPO = Path(__file__).resolve().parents[2]


def test_credential_constants_match_section_11_13_5_authority() -> None:
    assert REQUIRED_SECRETREF_URI.startswith("secretref://")
    assert "LIVE_CANARY" in REQUIRED_CREDENTIAL_CLASS


def test_default_stub_fail_closed_without_nameerror() -> None:
    with pytest.raises(RuntimeError, match=CREDENTIAL_HANDLE_FAIL_CLOSED_STATUS):
        productive_fail_closed_credential_unavailable_v1(repo_root=_REPO)


def test_bind_execute_network_missing_credentials_fail_closed() -> None:
    transport, status, handle = bind_productive_read_only_get_transport_for_execute_network_v1(
        execute_network=True,
        fresh_get_transport=None,
        vault_file=None,
        repo_root=_REPO,
    )
    assert transport is None
    assert handle is None
    assert status == CREDENTIAL_HANDLE_FAIL_CLOSED_STATUS


def test_bind_execute_network_false_not_reached() -> None:
    injected = _fresh_get_transport()
    transport, status, handle = bind_productive_read_only_get_transport_for_execute_network_v1(
        execute_network=False,
        fresh_get_transport=injected,
        vault_file=None,
        repo_root=_REPO,
    )
    assert transport is injected
    assert status == "NOT_REACHED"
    assert handle is None


def test_bind_execute_network_success_with_patched_loader(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[dict[str, object]] = []

    def _loader(*_a: object, **kwargs: object) -> FullCoreSendCredentialHandleV1:
        calls.append(dict(kwargs))
        if _a or "handle" in kwargs:
            return None  # type: ignore[return-value]
        return FullCoreSendCredentialHandleV1(handle_id="test-cred", bound=True)

    monkeypatch.setattr(
        "src.ops.governed_productive_account_equity_authority_producer_v1."
        "current_productive_execute_network_credential_join_v1."
        "productive_fail_closed_credential_unavailable_v1",
        _loader,
    )
    transport, status, handle = bind_productive_read_only_get_transport_for_execute_network_v1(
        execute_network=True,
        fresh_get_transport=None,
        vault_file="/tmp/test-vault.json",
        repo_root=_REPO,
    )
    assert status == ""
    assert transport is not None
    assert handle is not None
    secret_calls = [c for c in calls if "secret_reference" in c]
    assert len(secret_calls) == 1
    assert secret_calls[0]["secret_reference"] == REQUIRED_SECRETREF_URI
    assert secret_calls[0]["credential_class"] == REQUIRED_CREDENTIAL_CLASS
    release_productive_credential_handle_v1(handle)


def test_invalid_credential_class_fail_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    def _loader(**kwargs: object) -> object:
        if kwargs.get("credential_class") != REQUIRED_CREDENTIAL_CLASS:
            raise RuntimeError(CREDENTIAL_HANDLE_FAIL_CLOSED_STATUS)
        return FullCoreSendCredentialHandleV1(handle_id="test-cred", bound=True)

    monkeypatch.setattr(
        "src.ops.governed_productive_account_equity_authority_producer_v1."
        "current_productive_execute_network_credential_join_v1."
        "productive_fail_closed_credential_unavailable_v1",
        _loader,
    )
    transport, status, _handle = bind_productive_read_only_get_transport_for_execute_network_v1(
        execute_network=True,
        fresh_get_transport=None,
        vault_file="/tmp/test-vault.json",
        repo_root=_REPO,
    )
    assert transport is None
    assert status == CREDENTIAL_HANDLE_FAIL_CLOSED_STATUS


def test_dk_execute_network_no_nameerror_fail_closed(tmp_path: Path) -> None:
    result = execute_current_productive_fresh_runtime_cycle_to_exact_envelope_bound_v1(
        owner_go=OWNER_GO,
        origin_main_sha=TRUSTED_TEST_ORIGIN_MAIN_SHA,
        evidence_root=tmp_path / "store",
        acquisition_transport=_eligible_transport(),
        execute_network=True,
        producer_observed_at_unix=1_700_000_100.0,
        replay=None,
        execution_integrity_backend=_INTEGRITY,
    )
    assert result.first_real_blocker == (
        "FRESH_PRE_SUBMIT_EVIDENCE_FAIL_CLOSED:" + CREDENTIAL_HANDLE_FAIL_CLOSED_STATUS
    )
    assert result.post_count == "0"
    assert result.permit_created == "false"


def test_dk_execute_network_false_regression_unchanged(tmp_path: Path) -> None:
    result = execute_current_productive_fresh_runtime_cycle_to_exact_envelope_bound_v1(
        owner_go=OWNER_GO,
        origin_main_sha=TRUSTED_TEST_ORIGIN_MAIN_SHA,
        evidence_root=tmp_path / "store",
        acquisition_transport=_eligible_transport(),
        fresh_get_transport=_fresh_get_transport(),
        execute_network=False,
        producer_observed_at_unix=1_700_000_100.0,
        replay=None,
        execution_integrity_backend=_INTEGRITY,
    )
    assert result.master_v2_runtime_cycle_id != ""
    assert result.post_count == "0"
