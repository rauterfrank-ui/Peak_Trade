"""DE/DD execution-ladder merge-stable baseline and contract separation tests."""

from __future__ import annotations

import inspect

import pytest

from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    EXTERNAL_EFFECT_AUTHORIZED,
    PRODUCTIVE_WIRE_SEND_REACHABLE,
    current_productive_first_real_blocker_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_29p_chain_baseline_contract_v1 import (
    PROTECTED_CURRENT_PRODUCTIVE_29P_CHAIN_SURFACE_PATHS,
    RUNTIME_INTEGRITY_CONTRACT_VERSION,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_execution_admission_remainder_v1 import (
    CurrentProductiveExecutionAdmissionRemainderError,
    execute_current_productive_execution_admission_remainder_v1,
    OWNER_GO as DD_OWNER_GO,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_cap72_host_join_to_live_execution_port_v1 import (
    CurrentProductiveCap72HostJoinToLiveExecutionPortError,
    execute_current_productive_cap72_host_join_to_live_execution_port_v1,
    OWNER_GO as DF_OWNER_GO,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_live_execution_port_construction_v1 import (
    CurrentProductiveLiveExecutionPortConstructionError,
    execute_current_productive_live_execution_port_construction_v1,
    OWNER_GO as DE_OWNER_GO,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_29p_chain_baseline_contract_v1 import (
    default_current_productive_29p_integrity_backend_v1,
)
from tests.ops._current_productive_29p_chain_integrity_test_helpers_v1 import (
    MockCurrentProductive29PIntegrityBackendV1,
    TRUSTED_TEST_ORIGIN_MAIN_SHA,
)
from tests.ops.test_full_core_current_productive_29p_common_epoch_handoff_v1 import (
    CountingInjectedFreshGetTransportV1,
    _bound,
    _identity_payloads,
)

_INTEGRITY = MockCurrentProductive29PIntegrityBackendV1()


def test_de_dd_modules_on_protected_chain_surface() -> None:
    paths = PROTECTED_CURRENT_PRODUCTIVE_29P_CHAIN_SURFACE_PATHS
    assert any("execution_admission_remainder_v1.py" in p for p in paths)
    assert any("live_execution_port_construction_v1.py" in p for p in paths)
    assert any("cap72_host_join_to_live_execution_port_v1.py" in p for p in paths)
    assert any(
        "fresh_runtime_cycle_to_exact_envelope_bound_single_use_post_boundary_v1.py" in p
        for p in paths
    )
    assert any("execute_network_read_credential_loader_v1.py" in p for p in paths)


def test_de_does_not_import_cap72_host_join() -> None:
    from src.ops.governed_productive_account_equity_authority_producer_v1 import (
        current_productive_live_execution_port_construction_v1 as de_mod,
    )

    source = inspect.getsource(de_mod)
    assert "join_cap72_host_to_live_execution_port_v1" not in source


def test_dd_execution_identity_drift_fail_closed(tmp_path) -> None:
    drift_backend = MockCurrentProductive29PIntegrityBackendV1(drift="diff")
    with pytest.raises(
        CurrentProductiveExecutionAdmissionRemainderError,
        match="PROTECTED_CHAIN_SURFACE_DRIFT",
    ):
        execute_current_productive_execution_admission_remainder_v1(
            owner_go=DD_OWNER_GO,
            origin_main_sha=TRUSTED_TEST_ORIGIN_MAIN_SHA,
            evidence_root=tmp_path / "dd",
            execution_integrity_backend=drift_backend,
        )


def test_de_execution_identity_mismatch_fail_closed(tmp_path) -> None:
    with pytest.raises(
        CurrentProductiveLiveExecutionPortConstructionError,
        match="ORIGIN_MAIN_SHA_MISMATCH",
    ):
        execute_current_productive_live_execution_port_construction_v1(
            owner_go=DE_OWNER_GO,
            origin_main_sha="b" * 40,
            evidence_root=tmp_path / "de",
            execution_integrity_backend=_INTEGRITY,
        )


def test_ei_boundary_follows_current_first_real_blocker() -> None:
    from dataclasses import replace

    from src.ops.governed_productive_account_equity_authority_producer_v1 import (
        current_productive_29p_common_epoch_handoff_v1 as ei_mod,
    )
    from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_29p_common_epoch_handoff_v1 import (
        compose_current_productive_29p_common_epoch_handoff_v1,
    )

    transport = CountingInjectedFreshGetTransportV1(
        payloads=_identity_payloads(instrument_id="0G-USDT-SWAP")
    )
    handoff = compose_current_productive_29p_common_epoch_handoff_v1(
        decision_epoch="2026-09-22T08:00:00Z",
        bound_instrument=_bound(),
        fresh_get_transport=transport,
        inst_type="SWAP",
    )
    productive_handoff = replace(
        handoff,
        lab_trusted=True,
        instrument_bound=True,
        eligibility=object(),
        observation=object(),
        produced=True,
        evaluator_29p=True,
    )
    blocker, cls = ei_mod._first_blocker_from_handoff_v1(
        handoff=productive_handoff,
        productive_contact=True,
    )
    assert blocker == current_productive_first_real_blocker_v1()
    assert blocker != "LIVE_EXECUTION_PORT_CONSTRUCTION_REMAINS_FORBIDDEN"
    assert cls == "E"


def test_wire_reachability_not_external_effect() -> None:
    assert PRODUCTIVE_WIRE_SEND_REACHABLE is True
    assert EXTERNAL_EFFECT_AUTHORIZED is False


def test_runtime_integrity_contract_version_present_in_specs() -> None:
    assert RUNTIME_INTEGRITY_CONTRACT_VERSION == "current_productive_29p_chain_runtime_integrity.v1"


def test_dd_de_df_runtime_proof_with_trusted_integrity_backend(tmp_path) -> None:
    backend = default_current_productive_29p_integrity_backend_v1()
    origin_main_sha = backend.resolve_origin_main_sha_v1()
    trusted = MockCurrentProductive29PIntegrityBackendV1(
        origin_main=origin_main_sha,
        head=origin_main_sha,
    )
    dd = execute_current_productive_execution_admission_remainder_v1(
        owner_go=DD_OWNER_GO,
        origin_main_sha=origin_main_sha,
        evidence_root=tmp_path / "dd",
        execution_integrity_backend=trusted,
    )
    assert dd.post_count == "0"
    de = execute_current_productive_live_execution_port_construction_v1(
        owner_go=DE_OWNER_GO,
        origin_main_sha=origin_main_sha,
        evidence_root=tmp_path / "de",
        execution_integrity_backend=trusted,
    )
    assert de.port_constructed == "true"
    assert de.port_construction_side_effect_free == "true"
    assert de.post_count == "0"
    df = execute_current_productive_cap72_host_join_to_live_execution_port_v1(
        owner_go=DF_OWNER_GO,
        origin_main_sha=origin_main_sha,
        evidence_root=tmp_path / "df",
        execution_integrity_backend=trusted,
    )
    assert df.host_joined == "true"
    assert df.host_join_side_effect_free == "true"
    assert df.post_count == "0"
    assert df.first_real_blocker == (
        "OWNER_GO_REQUIRED_FOR_ACTUAL_VENUE_POST_WITH_FRESH_ENVELOPE_BOUND_SINGLE_USE_PERMIT"
    )


def test_df_execution_identity_drift_fail_closed(tmp_path) -> None:
    drift_backend = MockCurrentProductive29PIntegrityBackendV1(drift="diff")
    with pytest.raises(
        CurrentProductiveCap72HostJoinToLiveExecutionPortError,
        match="PROTECTED_CHAIN_SURFACE_DRIFT",
    ):
        execute_current_productive_cap72_host_join_to_live_execution_port_v1(
            owner_go=DF_OWNER_GO,
            origin_main_sha=TRUSTED_TEST_ORIGIN_MAIN_SHA,
            evidence_root=tmp_path / "df",
            execution_integrity_backend=drift_backend,
        )
