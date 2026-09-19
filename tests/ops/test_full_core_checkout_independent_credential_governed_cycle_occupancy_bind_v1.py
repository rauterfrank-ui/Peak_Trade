"""Governed-cycle occupancy-adjacent K1 credential bind contracts.

No operator Keychain access. No GET. No POST. No V5/K2 credential reuse.
"""

from __future__ import annotations

import inspect
from pathlib import Path
from types import SimpleNamespace

import pytest

from src.ops.full_core_live_path_composition_root_v1.checkout_independent_credential_capability_v1 import (
    REAL_BACKEND_ACCESS_FAIL_CLOSED_CODE,
    REQUIRED_CREDENTIAL_CLASS,
    FullCoreCheckoutIndependentCredentialCapabilityError,
    prove_capability_cannot_mutate_standing_gates_v1,
)
from src.ops.full_core_live_path_composition_root_v1.checkout_independent_credential_concrete_backend_item_identity_v1 import (
    SOURCE_REF_URI,
)
from src.ops.full_core_live_path_composition_root_v1.checkout_independent_credential_fail_closed_os_native_store_adapter_v1 import (
    REAL_KEYCHAIN_ACCESS_AUTHORIZED as EA_REAL_KEYCHAIN_ACCESS_AUTHORIZED,
    REAL_KEYCHAIN_ACCESS_IMPLEMENTED as EA_REAL_KEYCHAIN_ACCESS_IMPLEMENTED,
    FullCoreCheckoutIndependentFailClosedOsNativeStoreAdapterV1,
)
from src.ops.full_core_live_path_composition_root_v1.checkout_independent_credential_governed_cycle_occupancy_bind_v1 import (
    CONSUMER_ROLE,
    JOIN_EXECUTION_AUTHORITY,
    JOIN_RANKING_AUTHORITY,
    JOIN_SEAM_ID,
    JOIN_SELECTION_AUTHORITY,
    JOIN_SEMANTICS,
    JOIN_TRADING_AUTHORITY,
    MAY_EXECUTE_NETWORK,
    MAY_MINT_PERMIT,
    MAY_PERFORM_GET,
    MAY_POST,
    OWNER_GO,
    PRODUCTIVE_CONSUMER_JOINED,
    PRODUCTIVE_PROVIDER_ACTIVE,
    REAL_KEYCHAIN_ACCESS_AUTHORIZED,
    REAL_KEYCHAIN_ACCESS_IMPLEMENTED,
    SEAM_LOCATION,
    SEND_HANDLE_JOINED,
    V5_JOINED,
    bind_k1_credential_capability_for_governed_cycle_occupancy_v1,
)
from src.ops.full_core_live_path_composition_root_v1.checkout_independent_credential_os_native_store_acquisition_v1 import (
    REAL_KEYCHAIN_ACCESS_AUTHORIZED as K1_REAL_KEYCHAIN_ACCESS_AUTHORIZED,
    REAL_KEYCHAIN_ACCESS_IMPLEMENTED as K1_REAL_KEYCHAIN_ACCESS_IMPLEMENTED,
)
from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    EXTERNAL_EFFECT_AUTHORIZED,
    POST_ALLOWED,
    REAL_VENUE_POST_ALLOWED,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_governed_cycle_orchestrator_v1 import (
    DISPOSITION_HOLD,
    DISPOSITION_PRE_EXTERNAL_EFFECT,
    run_current_productive_governed_cycle_v1,
)
from src.ops.full_core_live_path_composition_root_v1.gated_productive_wire_transport_v1 import (
    FullCoreSendCredentialHandleV1,
)
from src.ops.single_selected_future_runtime_binding_v1.constants_v1 import (
    MAX_POSITIONS_EFFECTIVE,
)
from tests.ops.test_full_core_current_productive_governed_cycle_orchestrator_v1 import (
    _auth,
    _candles,
    _eg_stub,
    _occupancy_absent,
    _occupancy_present,
    _run,
    _t2_enter,
    _t2_hold,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
BIND_PATH = (
    REPO_ROOT
    / "src/ops/full_core_live_path_composition_root_v1"
    / "checkout_independent_credential_governed_cycle_occupancy_bind_v1.py"
)
CYCLE_PATH = (
    REPO_ROOT
    / "src/ops/full_core_live_path_composition_root_v1"
    / "current_productive_governed_cycle_orchestrator_v1.py"
)
N5_DIR = REPO_ROOT / "src/ops/current_mf_n5_full_autonomy_runtime_n5_completion_v1"
N1_DIR = (
    REPO_ROOT
    / "src/ops/current_mf_n5_full_autonomy_occupied_lane_governed_cycle_n1_consumer_join_v1"
)
PROTECTED_ALGORITHM_FILES = (
    "src/ops/single_selected_future_policy_v1/selection_v1.py",
    "src/ops/single_selected_future_policy_v1/policy_v1.py",
    "src/trading/master_v2/double_play_state.py",
    "src/trading/master_v2/double_play_entry_exit_policy_v0.py",
)
K2_MARKERS = (
    "secretref",
    "SecretRef",
    "file_vault",
    "FILE_VAULT",
    "vault.json",
    "live_credential_ephemeral_v1",
    "hmac",
    "HMAC",
)
NETWORK_MARKERS = (
    "import urllib",
    "from urllib",
    "import socket",
    "import requests",
    "import http.client",
    "from http",
    "SecItemCopyMatching",
    "import ctypes",
    "from ctypes",
)


def _package_source(directory: Path) -> str:
    return "\n".join(path.read_text(encoding="utf-8") for path in sorted(directory.glob("*.py")))


def test_bind_reuses_existing_provider_port_and_stays_fail_closed() -> None:
    before = prove_capability_cannot_mutate_standing_gates_v1()
    proof = bind_k1_credential_capability_for_governed_cycle_occupancy_v1()
    after = prove_capability_cannot_mutate_standing_gates_v1()
    assert before == after
    assert proof.disposition == "FAIL_CLOSED_BOUND"
    assert proof.provider_port_reused == "true"
    assert proof.source_ref_uri == SOURCE_REF_URI
    assert proof.credential_class == REQUIRED_CREDENTIAL_CLASS
    assert proof.resolve_fail_closed == "true"
    assert proof.resolve_fail_closed_code == REAL_BACKEND_ACCESS_FAIL_CLOSED_CODE
    assert proof.material_loaded == "false"
    assert proof.real_keychain_access_authorized == "false"
    assert proof.real_keychain_access_implemented == "false"
    assert proof.productive_provider_active == "false"
    assert proof.v5_joined == "false"
    assert proof.send_handle_joined == "false"
    assert proof.permit_created == "false"
    assert proof.post_count == "0"
    assert proof.perform_get == "false"
    assert proof.execute_network == "false"
    assert "api_key" not in proof.to_dict().values()
    assert REAL_KEYCHAIN_ACCESS_AUTHORIZED is False
    assert REAL_KEYCHAIN_ACCESS_IMPLEMENTED is False
    assert K1_REAL_KEYCHAIN_ACCESS_AUTHORIZED is False
    assert K1_REAL_KEYCHAIN_ACCESS_IMPLEMENTED is False
    assert EA_REAL_KEYCHAIN_ACCESS_AUTHORIZED is False
    assert EA_REAL_KEYCHAIN_ACCESS_IMPLEMENTED is False
    assert PRODUCTIVE_CONSUMER_JOINED is True
    assert PRODUCTIVE_PROVIDER_ACTIVE is False
    assert V5_JOINED is False
    assert SEND_HANDLE_JOINED is False
    assert MAY_PERFORM_GET is False
    assert MAY_EXECUTE_NETWORK is False
    assert MAY_MINT_PERMIT is False
    assert MAY_POST is False
    assert JOIN_TRADING_AUTHORITY is False
    assert JOIN_RANKING_AUTHORITY is False
    assert JOIN_SELECTION_AUTHORITY is False
    assert JOIN_EXECUTION_AUTHORITY is False
    assert CONSUMER_ROLE == "GOVERNED_CYCLE_OCCUPANCY_ADJACENT_K1_CAPABILITY_BIND"
    assert SEAM_LOCATION == "GOVERNED_CYCLE_AFTER_EG_BEFORE_OCCUPANCY_CLASSIFY"
    assert JOIN_SEMANTICS == "FAIL_CLOSED_AUTHORITY_NEUTRAL_K1_CAPABILITY_BIND"
    assert JOIN_SEAM_ID == "CURRENT_PRODUCTIVE_GOVERNED_CYCLE_K1_CREDENTIAL_BIND_SEAM_V1"
    assert OWNER_GO == "OWNER_GO_K1_GOVERNED_CYCLE_CREDENTIAL_BIND_JOIN_V1"
    assert EXTERNAL_EFFECT_AUTHORIZED is False
    assert POST_ALLOWED is False
    assert REAL_VENUE_POST_ALLOWED is False
    assert int(MAX_POSITIONS_EFFECTIVE) == 1


def test_capability_is_not_send_handle_and_cannot_mint_permit() -> None:
    proof = bind_k1_credential_capability_for_governed_cycle_occupancy_v1()
    send = FullCoreSendCredentialHandleV1(handle_id="full-core-send-handle", bound=True)
    assert type(proof) is not type(send)
    assert not isinstance(proof, FullCoreSendCredentialHandleV1)
    assert not isinstance(send, type(proof))
    adapter = FullCoreCheckoutIndependentFailClosedOsNativeStoreAdapterV1()
    assert not isinstance(adapter, FullCoreSendCredentialHandleV1)
    with pytest.raises(
        FullCoreCheckoutIndependentCredentialCapabilityError,
        match="CREDENTIAL_CAPABILITY_CANNOT_MINT_PERMIT",
    ):
        from src.ops.full_core_live_path_composition_root_v1.checkout_independent_credential_capability_v1 import (
            refuse_mint_external_effect_permit_from_credential_capability_v1,
        )

        refuse_mint_external_effect_permit_from_credential_capability_v1()


def test_bind_source_has_no_k2_network_or_os_lookup() -> None:
    source = BIND_PATH.read_text(encoding="utf-8")
    for marker in K2_MARKERS + NETWORK_MARKERS:
        assert marker not in source
    assert "FullCoreSendCredentialHandleV1" not in source
    assert "acquire_opaque_os_native_store_material_v1" not in source
    assert "run_opaque_os_native_store_acquisition_v1" not in source
    assert "bind_fail_closed_os_native_store_adapter_v1" in source
    assert "resolve_checkout_independent_credential_capability_v1" in source


def test_n5_and_n1_remain_without_credential_surface() -> None:
    n5_source = _package_source(N5_DIR)
    n1_source = _package_source(N1_DIR)
    for source in (n5_source, n1_source):
        assert "checkout_independent_credential_governed_cycle_occupancy_bind_v1" not in source
        assert "bind_k1_credential_capability_for_governed_cycle_occupancy_v1" not in source
        assert "checkout_independent_credential_os_native_store_acquisition_v1" not in source
        assert "FullCoreSendCredentialHandleV1" not in source
        assert "live_credential_ephemeral_v1" not in source
    n5_constants = (N5_DIR / "constants_v1.py").read_text(encoding="utf-8")
    assert "MAY_PERFORM_GET = False" in n5_constants
    assert "MAY_POST = False" in n5_constants
    assert "MAY_MINT_PERMIT = False" in n5_constants
    assert "JOIN_TRADING_AUTHORITY = False" in n5_constants
    n1_constants = (N1_DIR / "constants_v1.py").read_text(encoding="utf-8")
    assert "EG_V5_USED = False" in n1_constants
    assert "JOIN_TRADING_AUTHORITY = False" in n1_constants
    assert "JOIN_EXECUTION_AUTHORITY = False" in n1_constants


def test_cycle_source_order_is_eg_then_k1_bind_then_occupancy_then_t2() -> None:
    source = CYCLE_PATH.read_text(encoding="utf-8")
    eg_idx = source.find("eg_dispatch_count = int(eg_result.dispatch_count)")
    bind_idx = source.find("bind_k1_credential_capability_for_governed_cycle_occupancy_v1()")
    occupancy_idx = source.find("occupancy_facts = _classify_occupancy_v1(")
    t2_idx = source.find("t2_result = t2_dispatch(")
    assert eg_idx != -1
    assert bind_idx != -1
    assert occupancy_idx != -1
    assert t2_idx != -1
    assert eg_idx < bind_idx < occupancy_idx < t2_idx
    assert "execute_network is True or perform_get is True" in source
    assert "REASON_NETWORK_NOT_AUTHORIZED" in source


def test_cycle_runtime_order_and_fail_closed_bind_does_not_block(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import src.ops.full_core_live_path_composition_root_v1.current_productive_governed_cycle_orchestrator_v1 as cycle_mod

    order: list[str] = []
    original_bind = cycle_mod.bind_k1_credential_capability_for_governed_cycle_occupancy_v1
    original_classify = cycle_mod._classify_occupancy_v1

    def _eg(**kwargs: object) -> SimpleNamespace:
        order.append("eg")
        return _eg_stub(**kwargs)

    def _bind(**kwargs: object) -> object:
        order.append("credential-bind")
        return original_bind(**kwargs)

    def _classify(**kwargs: object) -> object:
        order.append("occupancy")
        return original_classify(**kwargs)

    def _t2(**kwargs: object) -> SimpleNamespace:
        order.append("t2")
        return _t2_hold(**kwargs)

    monkeypatch.setattr(
        cycle_mod, "bind_k1_credential_capability_for_governed_cycle_occupancy_v1", _bind
    )
    monkeypatch.setattr(cycle_mod, "_classify_occupancy_v1", _classify)
    result = _run(tmp_path, eg_cycle_dispatch=_eg, t2_cycle_dispatch=_t2)
    assert result.disposition == DISPOSITION_HOLD
    assert order == ["eg", "credential-bind", "occupancy", "t2"]
    assert result.post_count == 0
    assert result.permit_created is False
    assert result.external_effect_count == 0
    ledger = (tmp_path / "evidence" / "governed_cycle_orchestrator_ledger_v1.json").read_text(
        encoding="utf-8"
    )
    assert "FAIL_CLOSED_BOUND" in ledger
    assert '"K1_MATERIAL_LOADED": "false"' in ledger
    assert '"K1_SEND_HANDLE_JOINED": "false"' in ledger
    assert '"K1_V5_JOINED": "false"' in ledger
    assert '"K1_PERMIT_CREATED": "false"' in ledger
    assert '"K1_POST_COUNT": "0"' in ledger


def test_freshness_failure_does_not_bind_k1(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import src.ops.full_core_live_path_composition_root_v1.current_productive_governed_cycle_orchestrator_v1 as cycle_mod

    calls = {"n": 0}
    original_bind = cycle_mod.bind_k1_credential_capability_for_governed_cycle_occupancy_v1

    def _bind(**kwargs: object) -> object:
        calls["n"] += 1
        return original_bind(**kwargs)

    monkeypatch.setattr(
        cycle_mod, "bind_k1_credential_capability_for_governed_cycle_occupancy_v1", _bind
    )
    result = _run(tmp_path, candles_payload=_candles(last_ts_ms=int(1789664700.0 * 1000)))
    assert result.eg_consumed is False
    assert result.occupancy_consumed is False
    assert result.t2_consumed is False
    assert calls["n"] == 0


def test_occupancy_failure_still_binds_k1_before_classify(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import src.ops.full_core_live_path_composition_root_v1.current_productive_governed_cycle_orchestrator_v1 as cycle_mod

    order: list[str] = []
    original_bind = cycle_mod.bind_k1_credential_capability_for_governed_cycle_occupancy_v1
    original_classify = cycle_mod._classify_occupancy_v1

    def _bind(**kwargs: object) -> object:
        order.append("credential-bind")
        return original_bind(**kwargs)

    def _classify(**kwargs: object) -> object:
        order.append("occupancy")
        return original_classify(**kwargs)

    monkeypatch.setattr(
        cycle_mod, "bind_k1_credential_capability_for_governed_cycle_occupancy_v1", _bind
    )
    monkeypatch.setattr(cycle_mod, "_classify_occupancy_v1", _classify)
    result = _run(tmp_path, occupancy_payloads=_occupancy_present())
    assert result.terminal_class == "OCCUPANCY_FAILURE"
    assert result.t2_consumed is False
    assert order == ["credential-bind", "occupancy"]
    assert result.post_count == 0
    assert result.permit_created is False


def test_pre_external_effect_still_reached_without_get_or_post(tmp_path: Path) -> None:
    result = _run(tmp_path, t2_cycle_dispatch=_t2_enter)
    assert result.disposition == DISPOSITION_PRE_EXTERNAL_EFFECT
    assert result.t2_consumed is True
    assert result.post_count == 0
    assert result.permit_created is False
    assert result.external_effect_count == 0
    with pytest.raises(
        Exception,
        match="NETWORK_NOT_AUTHORIZED_THIS_SLICE",
    ):
        run_current_productive_governed_cycle_v1(
            authorization=_auth(),
            origin_main_sha="f9bbd1d8c77a571b9c3f8cd238bacf21f200877d",
            cursor_store_root=tmp_path / "cursor",
            lock_root=tmp_path / "lock",
            evidence_root=tmp_path / "evidence-get",
            candles_payload=_candles(last_ts_ms=int(1789664760.0 * 1000)),
            occupancy_payloads=_occupancy_absent(),
            execute_network=False,
            perform_get=True,
            eg_cycle_dispatch=_eg_stub,
            t2_cycle_dispatch=_t2_hold,
        )


def test_protected_trading_owners_and_v5_host_absent() -> None:
    for path in PROTECTED_ALGORITHM_FILES:
        assert (REPO_ROOT / path).is_file()
    v5_host = (
        REPO_ROOT
        / "src/ops/governed_productive_account_equity_authority_producer_v1"
        / "current_productive_one_runtime_cycle_after_new_finalized_1m_c1_observation_v5.py"
    )
    assert not v5_host.is_file()
    cycle_source = CYCLE_PATH.read_text(encoding="utf-8")
    assert "live_credential_ephemeral_v1" not in cycle_source
    assert "default_vault_path_v1" not in cycle_source
    assert inspect.isfunction(bind_k1_credential_capability_for_governed_cycle_occupancy_v1)
