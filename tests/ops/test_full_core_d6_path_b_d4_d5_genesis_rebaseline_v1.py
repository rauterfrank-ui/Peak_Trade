"""D6 PATH_B D4/D5 genesis rebaseline continue tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    D4_D5_GENESIS_REBASELINE_CONTRACT_PRESENT,
    EXECUTION_READY,
    HISTORICAL_COMPLETENESS_CLAIMED,
    HISTORICAL_CONTINUITY_CLAIMED,
    KIND_SET_RESOLVED,
    LIVE_ARMED,
    LIVE_ENABLED,
    MS2_AUTHORIZED,
    OBSERVATION_EXECUTED,
    OBSERVATION_EXECUTION_AUTHORIZED,
    OBSERVATION_NETWORK_GET_AUTHORIZED,
    WIRE_SEND_PERMITTED,
)
from src.ops.full_core_live_path_composition_root_v1.live_admission_gap_dag_v1 import (
    live_admission_gap_dag_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.bound_account_identity_contract_v1 import (
    PROVENANCE_GENESIS_FRESH_TYPED_BINDING,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.checkpoint_observation_window_binding_contract_v1 import (
    AS_OF_RELATION_GENESIS_EPOCH,
    BINDING_CLASS_GENESIS_EPOCH,
    WINDOW_DERIVATION_GENESIS_EPOCH,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.d4_d5_genesis_rebaseline_contract_v1 import (
    CONTINUE_OWNER_GO,
    EXPECTED_ORIGIN_MAIN_SHA,
    OWNER_GO,
    build_d4_d5_genesis_rebaseline_contract_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.d4_d5_genesis_runtime_orchestrator_v1 import (
    D4D5GenesisRuntimeOrchestratorError,
    execute_d4_d5_genesis_runtime_orchestrator_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.d4_genesis_fresh_account_config_bootstrap_v1 import (
    D4GenesisFreshAccountConfigBootstrapError,
    extract_observed_account_config_identity_facts_v1,
    resolve_genesis_d4_members_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.package_1_observation_s0_runtime_binding_gate_v1 import (
    assert_package_1_observation_s0_runtime_payloads_present_v1,
    reject_package_1_observation_execution_without_runtime_payloads_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.http_client_v1 import (
    RecordingFakeCanaryTransportV1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
RUNBOOK = REPO_ROOT / "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md"
SPEC_PATH = REPO_ROOT / "docs/ops/specs/FULL_CORE_D6_PATH_B_D4_D5_GENESIS_REBASELINE_V1.md"
BB_HEADING = "11.2.1.BB FULL_CORE_D6_PATH_B_D4_D5_GENESIS_REBASELINE"
_GENESIS_AS_OF = "2026-09-13T16:50:00Z"
_SYNTHETIC_UID = "900199001990019900"
_SUCCESS_BODY = (
    b'{"code":"0","msg":"","data":[{"uid":"900199001990019900","acctLv":"2",'
    b'"posMode":"net_mode","tdMode":"cross"}]}'
)
_NO_TD_BODY = (
    b'{"code":"0","msg":"","data":[{"uid":"900199001990019900","acctLv":"2","posMode":"net_mode"}]}'
)


def _bb_section() -> str:
    runbook = RUNBOOK.read_text(encoding="utf-8")
    start = runbook.index(BB_HEADING)
    return runbook[start : runbook.index("## 11.3 Autonomy state model", start)]


def test_genesis_contract_marks_legacy_chain_not_reconstructed() -> None:
    first = build_d4_d5_genesis_rebaseline_contract_v1(
        genesis_id="D4D5GENESISTEST0001",
        genesis_as_of=_GENESIS_AS_OF,
        owner_go=OWNER_GO,
        bound_origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
        continue_owner_go=CONTINUE_OWNER_GO,
    )
    again = build_d4_d5_genesis_rebaseline_contract_v1(
        genesis_id="D4D5GENESISTEST0001",
        genesis_as_of=_GENESIS_AS_OF,
        owner_go=OWNER_GO,
        bound_origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
        continue_owner_go=CONTINUE_OWNER_GO,
    )
    assert first.legacy_d4_d5_runtime_chain == "NOT_RECONSTRUCTED"
    assert first.historical_continuity_claimed == "false"
    assert first.historical_completeness_claimed == "false"
    assert first.pre_genesis_data_imported == "false"
    assert first.point_window_does_not_assert_zero_prior_events == "true"
    assert first.d4_genesis_bootstrap_source == "FRESH_AUTHENTICATED_ACCOUNT_CONFIG"
    assert first.provenance_digest == again.provenance_digest
    assert D4_D5_GENESIS_REBASELINE_CONTRACT_PRESENT is True
    assert HISTORICAL_CONTINUITY_CLAIMED is False
    assert HISTORICAL_COMPLETENESS_CLAIMED is False


def test_missing_td_mode_fail_closes_without_default() -> None:
    observed = extract_observed_account_config_identity_facts_v1(
        {"code": "0", "data": [{"uid": _SYNTHETIC_UID, "acctLv": "2"}]}
    )
    with pytest.raises(D4GenesisFreshAccountConfigBootstrapError) as err:
        resolve_genesis_d4_members_v1(observed=observed)
    assert "D4_GENESIS_FIELD_FAIL_CLOSED:bound_td_mode" in str(err.value)


def test_genesis_orchestrator_persists_d4_d5_and_s0_payloads(tmp_path: Path) -> None:
    transport = RecordingFakeCanaryTransportV1(body=_SUCCESS_BODY)
    result = execute_d4_d5_genesis_runtime_orchestrator_v1(
        store_root=tmp_path,
        genesis_as_of=_GENESIS_AS_OF,
        transport=transport,
    )
    assert result.account_config_get_performed == "true"
    assert result.additional_read_only_gets == "0"
    assert result.network_post_performed == "false"
    assert result.d4_bound_account_identity == _SYNTHETIC_UID
    assert result.d4_bound_venue_identity == "OKX"
    assert result.d4_bound_td_mode == "cross"
    assert result.d4_settlement_currency == "USDC"
    assert result.d4_runtime_instance_persisted == "true"
    assert result.d4_uid_corroborated == "true"
    assert result.d4_binding.identity_provenance_class == PROVENANCE_GENESIS_FRESH_TYPED_BINDING
    assert result.d5_window_start == _GENESIS_AS_OF
    assert result.d5_window_end == _GENESIS_AS_OF
    assert result.d5_window.observed_at_as_of == _GENESIS_AS_OF
    assert result.d5_window.binding_class == BINDING_CLASS_GENESIS_EPOCH
    assert result.d5_window.window_derivation_class == WINDOW_DERIVATION_GENESIS_EPOCH
    assert result.d5_window.observed_at_as_of_relation_class == AS_OF_RELATION_GENESIS_EPOCH
    assert result.d5_window.event_completeness_from_window == "false"
    assert result.historical_continuity_claimed == "false"
    assert result.historical_completeness_claimed == "false"
    assert result.pre_genesis_data_imported == "false"
    assert result.observation_s0_prerequisites_satisfied == "true"
    assert_package_1_observation_s0_runtime_payloads_present_v1(store_root=tmp_path)
    with pytest.raises(Exception) as exec_err:
        reject_package_1_observation_execution_without_runtime_payloads_v1(store_root=tmp_path)
    assert "OBSERVATION_EXECUTION_UNAUTHORIZED" in str(exec_err.value)
    assert [call.method for call in transport.calls] == ["GET"]
    assert all("/account/config" in call.endpoint for call in transport.calls)
    assert not any(call.method == "POST" for call in transport.calls)


def test_genesis_orchestrator_does_not_post_or_use_missing_td_mode(tmp_path: Path) -> None:
    transport = RecordingFakeCanaryTransportV1(body=_NO_TD_BODY)
    with pytest.raises(D4D5GenesisRuntimeOrchestratorError) as err:
        execute_d4_d5_genesis_runtime_orchestrator_v1(
            store_root=tmp_path,
            genesis_as_of=_GENESIS_AS_OF,
            transport=transport,
        )
    assert "D4_GENESIS_FIELD_FAIL_CLOSED:bound_td_mode" in str(err.value)
    assert not (tmp_path / "d4_bound_account_identity_runtime_instance_v1.json").exists()
    assert not (tmp_path / "d5_checkpoint_observation_window_binding_v1.json").exists()
    assert (tmp_path / "d4_d5_genesis_rebaseline_contract_v1.json").exists()
    claims = (tmp_path / "claims.json").read_text(encoding="utf-8")
    assert '"D4_RUNTIME_INSTANCE_PRESENT":"false"' in claims
    assert '"D4_GENESIS_FIELD_FAIL_CLOSED":"bound_td_mode"' in claims
    assert not any(call.method == "POST" for call in transport.calls)


def test_protected_surfaces_and_observation_execution_remain_closed() -> None:
    dag = live_admission_gap_dag_v1()
    assert dag["D4_D5_GENESIS_REBASELINE_CONTRACT_PRESENT"] is True
    assert dag["HISTORICAL_CONTINUITY_CLAIMED"] is False
    assert dag["HISTORICAL_COMPLETENESS_CLAIMED"] is False
    assert dag["KIND_SET_RESOLVED"] is False
    assert dag["MS2_AUTHORIZED"] is False
    assert KIND_SET_RESOLVED is False
    assert MS2_AUTHORIZED is False
    assert OBSERVATION_EXECUTED is False
    assert OBSERVATION_EXECUTION_AUTHORIZED is False
    assert OBSERVATION_NETWORK_GET_AUTHORIZED is False
    assert EXECUTION_READY is False
    assert LIVE_ENABLED is False
    assert LIVE_ARMED is False
    assert WIRE_SEND_PERMITTED is False


def test_runbook_bb_persists_genesis_without_historical_continuity() -> None:
    spec = SPEC_PATH.read_text(encoding="utf-8")
    bb_section = _bb_section()
    assert "OWNER_GO=OWNER_GO_D6_PATH_B_D4_D5_GENESIS_REBASELINE_CONTINUE_V1" in bb_section
    assert "THIS_SLICE=11.2.1.BB.FULL_CORE_D6_PATH_B_D4_D5_GENESIS_REBASELINE" in bb_section
    assert "LEGACY_D4_D5_RUNTIME_CHAIN=NOT_RECONSTRUCTED" in bb_section
    assert "HISTORICAL_CONTINUITY_CLAIMED=false" in bb_section
    assert "HISTORICAL_COMPLETENESS_CLAIMED=false" in bb_section
    assert "PRE_GENESIS_DATA_IMPORTED=false" in bb_section
    assert "D4_GENESIS_BOOTSTRAP_SOURCE=FRESH_AUTHENTICATED_ACCOUNT_CONFIG" in bb_section
    assert "POINT_WINDOW_DOES_NOT_ASSERT_ZERO_PRIOR_EVENTS=true" in bb_section
    assert "NETWORK_POST_PERFORMED=false" in bb_section
    assert "D4_GENESIS_FIELD_FAIL_CLOSED=bound_td_mode" in bb_section
    assert "D4_RUNTIME_INSTANCE_PRESENT=false" in bb_section
    assert "D5_RUNTIME_INSTANCE_PRESENT=false" in bb_section
    assert "KIND_SET_RESOLVED=false" in bb_section
    assert "MS2_AUTHORIZED=false" in bb_section
    assert "D7_AUTHORIZED=false" in bb_section
    assert "LIVE_ENABLED=false" in bb_section
    assert "MASTER_V2_UNCHANGED=true" in bb_section
    assert "DOCS_TOKEN_FULL_CORE_D6_PATH_B_D4_D5_GENESIS_REBASELINE_V1" in spec
    mot = (REPO_ROOT / "docs/governance/PEAK_TRADE_MAP_OF_TRUTH.md").read_text(encoding="utf-8")
    assert "FULL_CORE_D6_PATH_B_D4_D5_GENESIS_REBASELINE_V1.md" in mot
    assert "§11.2.1.BB FULL_CORE_D6_PATH_B_D4_D5_GENESIS_REBASELINE" in mot
