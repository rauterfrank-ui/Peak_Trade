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
    EXPECTED_GENESIS_AS_OF,
    EXPECTED_GENESIS_ID,
    EXPECTED_ORIGIN_MAIN_SHA,
    OWNER_GO,
    TD_MODE_RESOLUTION_OWNER_GO,
    UID_RECAPTURE_OWNER_GO,
    build_d4_d5_genesis_rebaseline_contract_v1,
    persist_d4_d5_genesis_rebaseline_contract_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.d4_d5_genesis_runtime_orchestrator_v1 import (
    D4D5GenesisRuntimeOrchestratorError,
    continue_d4_d5_genesis_with_fresh_account_config_uid_v1,
    continue_d4_d5_genesis_with_fresh_position_mgn_mode_v1,
    execute_d4_d5_genesis_runtime_orchestrator_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.d4_genesis_fresh_position_mgn_mode_bootstrap_v1 import (
    D4GenesisFreshPositionMgnModeBootstrapError,
    resolve_fresh_position_mgn_mode_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.d4_genesis_fresh_account_config_bootstrap_v1 import (
    FRESH_ACCOUNT_CONFIG_UID_ABSENT,
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
BC_HEADING = "11.2.1.BC FULL_CORE_D6_PATH_B_CLASS_C_PACKAGE_1_OBSERVATION_EXECUTION"
_GENESIS_AS_OF = "2026-09-13T16:50:00Z"
_SYNTHETIC_UID = "900199001990019900"
_SUCCESS_BODY = (
    b'{"code":"0","msg":"","data":[{"uid":"900199001990019900","acctLv":"2",'
    b'"posMode":"net_mode","tdMode":"cross"}]}'
)
_UID_ONLY_BODY = (
    b'{"code":"0","msg":"","data":[{"uid":"900199001990019900","acctLv":"2",'
    b'"posMode":"net_mode","mainUid":"900199001990019901"}]}'
)
_NO_UID_BODY = b'{"code":"0","msg":"","data":[{"acctLv":"2","posMode":"net_mode","mainUid":"1"}]}'
_NO_TD_BODY = (
    b'{"code":"0","msg":"","data":[{"uid":"900199001990019900","acctLv":"2","posMode":"net_mode"}]}'
)
_BOUND_INST = "SUI-USD_UM_XPERP-310404"
_POSITION_CROSS_BODY = (
    b'{"code":"0","msg":"","data":[{"instId":"SUI-USD_UM_XPERP-310404","instType":"FUTURES",'
    b'"mgnMode":"cross","pos":"1","uid":"900199001990019900"}]}'
)
_POSITION_EMPTY_BODY = b'{"code":"0","msg":"","data":[]}'
_POSITION_NO_UID_BODY = (
    b'{"code":"0","msg":"","data":[{"instId":"SUI-USD_UM_XPERP-310404","instType":"FUTURES",'
    b'"mgnMode":"cross","pos":"1"}]}'
)


def _bb_section() -> str:
    runbook = RUNBOOK.read_text(encoding="utf-8")
    start = runbook.index(BB_HEADING)
    return runbook[start : runbook.index(BC_HEADING, start)]


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
    assert "BOUND_TD_MODE_RESOLVED=true" in bb_section
    assert "FRESH_MGN_MODE_OBSERVED=cross" in bb_section
    assert "FRESH_UID_PRESENT=true" in bb_section
    assert "D4_BOUND_ACCOUNT_IDENTITY_SOURCE=FRESH_AUTHENTICATED_ACCOUNT_CONFIG_UID" in bb_section
    assert "BOUND_ACCOUNT_IDENTITY_RESOLVED=true" in bb_section
    assert "D4_RUNTIME_INSTANCE_PRESENT=true" in bb_section
    assert "D5_RUNTIME_INSTANCE_PRESENT=true" in bb_section
    assert "OBSERVATION_S0_PREREQUISITES_SATISFIED=true" in bb_section
    assert (
        "UID_RECAPTURE_OWNER_GO=OWNER_GO_D6_PATH_B_BOUND_ACCOUNT_IDENTITY_FRESH_CONFIG_UID_RECAPTURE_V1"
        in bb_section
    )
    assert "KIND_SET_RESOLVED=false" in bb_section
    assert "MS2_AUTHORIZED=false" in bb_section
    assert "D7_AUTHORIZED=false" in bb_section
    assert "LIVE_ENABLED=false" in bb_section
    assert "MASTER_V2_UNCHANGED=true" in bb_section
    assert "DOCS_TOKEN_FULL_CORE_D6_PATH_B_D4_D5_GENESIS_REBASELINE_V1" in spec
    mot = (REPO_ROOT / "docs/governance/PEAK_TRADE_MAP_OF_TRUTH.md").read_text(encoding="utf-8")
    assert "FULL_CORE_D6_PATH_B_D4_D5_GENESIS_REBASELINE_V1.md" in mot
    assert "§11.2.1.BB FULL_CORE_D6_PATH_B_D4_D5_GENESIS_REBASELINE" in mot


def _persist_bound_genesis_contract(tmp_path: Path) -> None:
    contract = build_d4_d5_genesis_rebaseline_contract_v1(
        genesis_id=EXPECTED_GENESIS_ID,
        genesis_as_of=EXPECTED_GENESIS_AS_OF,
        owner_go=OWNER_GO,
        bound_origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
        continue_owner_go=CONTINUE_OWNER_GO,
    )
    persist_d4_d5_genesis_rebaseline_contract_v1(store_root=tmp_path, contract=contract)


def _persist_bound_genesis_pack_with_td_mode(tmp_path: Path) -> None:
    _persist_bound_genesis_contract(tmp_path)
    (tmp_path / "d4_genesis_position_mgn_mode_observed_facts_v1.json").write_text(
        (
            '{"bound_td_mode":"cross","bound_td_mode_derivation":'
            '"OKX_FUTURES_SWAP_MGN_MODE_TO_TD_MODE_IDENTITY_MAPPING",'
            '"bound_td_mode_source":"FRESH_AUTHENTICATED_POSITION_MGN_MODE",'
            '"fresh_mgn_mode_observed":"cross","http_status":"200",'
            '"network_get_count":"1","network_post_count":"0","observed_uid":""}\n'
        ),
        encoding="utf-8",
    )
    (tmp_path / "claims.json").write_text(
        (
            '{"ACCOUNT_CONFIG_GET_PERFORMED":"true","ADDITIONAL_READ_ONLY_GETS":"1",'
            '"BOUND_TD_MODE_RESOLVED":"true","D4_BOUND_TD_MODE_SOURCE":'
            '"FRESH_AUTHENTICATED_POSITION_MGN_MODE",'
            '"D4_GENESIS_FIELD_FAIL_CLOSED":'
            '"bound_account_identity:ABSENT_FROM_GENESIS_EVIDENCE_PACK",'
            '"D4_RUNTIME_INSTANCE_PRESENT":"false","D5_RUNTIME_INSTANCE_PRESENT":"false",'
            '"FRESH_MGN_MODE_OBSERVED":"cross","GENESIS_AS_OF":'
            f'"{EXPECTED_GENESIS_AS_OF}","GENESIS_ID":"{EXPECTED_GENESIS_ID}",'
            '"HISTORICAL_COMPLETENESS_CLAIMED":"false",'
            '"HISTORICAL_CONTINUITY_CLAIMED":"false",'
            '"LEGACY_D4_D5_RUNTIME_CHAIN":"NOT_RECONSTRUCTED",'
            '"NETWORK_POST_PERFORMED":"false",'
            '"OBSERVATION_S0_PREREQUISITES_SATISFIED":"false",'
            '"POINT_WINDOW_DOES_NOT_ASSERT_ZERO_PRIOR_EVENTS":"true",'
            '"POSITIONS_GET_PERFORMED":"true","PRE_GENESIS_DATA_IMPORTED":"false"}\n'
        ),
        encoding="utf-8",
    )


def test_fresh_position_mgn_mode_cross_maps_to_td_mode() -> None:
    mode, count, _names, uid = resolve_fresh_position_mgn_mode_v1(
        payload={
            "code": "0",
            "data": [
                {
                    "instId": _BOUND_INST,
                    "mgnMode": "cross",
                    "pos": "1",
                    "uid": _SYNTHETIC_UID,
                }
            ],
        },
        bound_instrument_id=_BOUND_INST,
    )
    assert mode == "cross"
    assert count == 1
    assert uid == _SYNTHETIC_UID


def test_fresh_position_empty_or_conflict_fail_closes() -> None:
    with pytest.raises(D4GenesisFreshPositionMgnModeBootstrapError) as empty_err:
        resolve_fresh_position_mgn_mode_v1(
            payload={"code": "0", "data": []}, bound_instrument_id=_BOUND_INST
        )
    assert "POSITIONS_EMPTY" in str(empty_err.value)
    with pytest.raises(D4GenesisFreshPositionMgnModeBootstrapError) as conflict_err:
        resolve_fresh_position_mgn_mode_v1(
            payload={
                "code": "0",
                "data": [
                    {"instId": _BOUND_INST, "mgnMode": "cross"},
                    {"instId": _BOUND_INST, "mgnMode": "isolated"},
                ],
            },
            bound_instrument_id=_BOUND_INST,
        )
    assert "CONFLICTING_MGN_MODE" in str(conflict_err.value)


def test_continue_genesis_persists_d4_d5_from_fresh_mgn_mode(tmp_path: Path) -> None:
    _persist_bound_genesis_contract(tmp_path)
    transport = RecordingFakeCanaryTransportV1(body=_POSITION_CROSS_BODY)
    result = continue_d4_d5_genesis_with_fresh_position_mgn_mode_v1(
        store_root=tmp_path,
        owner_go=TD_MODE_RESOLUTION_OWNER_GO,
        transport=transport,
    )
    assert result.genesis_id == EXPECTED_GENESIS_ID
    assert result.genesis_as_of == EXPECTED_GENESIS_AS_OF
    assert result.additional_read_only_gets == "1"
    assert result.network_post_performed == "false"
    assert result.d4_bound_td_mode == "cross"
    assert result.d4_bound_account_identity == _SYNTHETIC_UID
    assert result.d4_runtime_instance_persisted == "true"
    assert result.d5_runtime_instance_persisted == "true"
    assert result.d5_window_start == EXPECTED_GENESIS_AS_OF
    assert result.d5_window_end == EXPECTED_GENESIS_AS_OF
    assert result.d4_binding.identity_provenance_class == PROVENANCE_GENESIS_FRESH_TYPED_BINDING
    assert_package_1_observation_s0_runtime_payloads_present_v1(store_root=tmp_path)
    assert [call.method for call in transport.calls] == ["GET"]
    assert all("/account/positions" in call.endpoint for call in transport.calls)
    assert not any(call.method == "POST" for call in transport.calls)


def test_continue_genesis_empty_positions_fail_closes(tmp_path: Path) -> None:
    _persist_bound_genesis_contract(tmp_path)
    transport = RecordingFakeCanaryTransportV1(body=_POSITION_EMPTY_BODY)
    with pytest.raises(D4D5GenesisRuntimeOrchestratorError) as err:
        continue_d4_d5_genesis_with_fresh_position_mgn_mode_v1(
            store_root=tmp_path,
            owner_go=TD_MODE_RESOLUTION_OWNER_GO,
            transport=transport,
        )
    assert "POSITIONS_EMPTY" in str(err.value)
    assert not (tmp_path / "d4_bound_account_identity_runtime_instance_v1.json").exists()
    assert not (tmp_path / "d5_checkpoint_observation_window_binding_v1.json").exists()
    assert not any(call.method == "POST" for call in transport.calls)


def test_continue_genesis_missing_uid_fail_closes_after_mgn_mode(tmp_path: Path) -> None:
    _persist_bound_genesis_contract(tmp_path)
    transport = RecordingFakeCanaryTransportV1(body=_POSITION_NO_UID_BODY)
    with pytest.raises(D4D5GenesisRuntimeOrchestratorError) as err:
        continue_d4_d5_genesis_with_fresh_position_mgn_mode_v1(
            store_root=tmp_path,
            owner_go=TD_MODE_RESOLUTION_OWNER_GO,
            transport=transport,
        )
    assert "D4_BOUND_ACCOUNT_IDENTITY_ABSENT_FROM_GENESIS_EVIDENCE_PACK" in str(err.value)
    facts = (tmp_path / "d4_genesis_position_mgn_mode_observed_facts_v1.json").read_text(
        encoding="utf-8"
    )
    assert '"fresh_mgn_mode_observed":"cross"' in facts
    assert not (tmp_path / "d4_bound_account_identity_runtime_instance_v1.json").exists()
    assert not any(call.method == "POST" for call in transport.calls)


def test_uid_recapture_persists_d4_d5_from_fresh_account_config_uid(tmp_path: Path) -> None:
    _persist_bound_genesis_pack_with_td_mode(tmp_path)
    transport = RecordingFakeCanaryTransportV1(body=_UID_ONLY_BODY)
    result = continue_d4_d5_genesis_with_fresh_account_config_uid_v1(
        store_root=tmp_path,
        owner_go=UID_RECAPTURE_OWNER_GO,
        transport=transport,
    )
    assert result.genesis_id == EXPECTED_GENESIS_ID
    assert result.genesis_as_of == EXPECTED_GENESIS_AS_OF
    assert result.account_config_get_performed == "true"
    assert result.network_post_performed == "false"
    assert result.d4_bound_account_identity == _SYNTHETIC_UID
    assert result.d4_bound_venue_identity == "OKX"
    assert result.d4_bound_td_mode == "cross"
    assert result.d4_settlement_currency == "USDC"
    assert result.d4_runtime_instance_persisted == "true"
    assert result.d5_runtime_instance_persisted == "true"
    assert result.d5_window_start == EXPECTED_GENESIS_AS_OF
    assert result.d5_window_end == EXPECTED_GENESIS_AS_OF
    assert result.observation_s0_prerequisites_satisfied == "true"
    facts = (tmp_path / "d4_genesis_account_config_observed_facts_v1.json").read_text(
        encoding="utf-8"
    )
    assert '"observed_uid":"900199001990019900"' in facts
    assert '"observed_main_uid":"900199001990019901"' in facts
    claims = (tmp_path / "claims.json").read_text(encoding="utf-8")
    assert '"BOUND_ACCOUNT_IDENTITY_RESOLVED":"true"' in claims
    assert '"D4_BOUND_ACCOUNT_IDENTITY_SOURCE":"FRESH_AUTHENTICATED_ACCOUNT_CONFIG_UID"' in claims
    assert_package_1_observation_s0_runtime_payloads_present_v1(store_root=tmp_path)
    assert [call.method for call in transport.calls] == ["GET"]
    assert all("/account/config" in call.endpoint for call in transport.calls)
    assert not any("/account/positions" in call.endpoint for call in transport.calls)
    assert not any(call.method == "POST" for call in transport.calls)


def test_uid_recapture_ignores_account_config_td_mode(tmp_path: Path) -> None:
    _persist_bound_genesis_pack_with_td_mode(tmp_path)
    transport = RecordingFakeCanaryTransportV1(body=_SUCCESS_BODY)
    result = continue_d4_d5_genesis_with_fresh_account_config_uid_v1(
        store_root=tmp_path,
        owner_go=UID_RECAPTURE_OWNER_GO,
        transport=transport,
    )
    assert result.d4_bound_td_mode == "cross"
    facts = (tmp_path / "d4_genesis_account_config_observed_facts_v1.json").read_text(
        encoding="utf-8"
    )
    assert '"bound_td_mode_source":"FRESH_AUTHENTICATED_POSITION_MGN_MODE"' in facts


def test_uid_recapture_absent_uid_fail_closes(tmp_path: Path) -> None:
    _persist_bound_genesis_pack_with_td_mode(tmp_path)
    transport = RecordingFakeCanaryTransportV1(body=_NO_UID_BODY)
    with pytest.raises(D4D5GenesisRuntimeOrchestratorError) as err:
        continue_d4_d5_genesis_with_fresh_account_config_uid_v1(
            store_root=tmp_path,
            owner_go=UID_RECAPTURE_OWNER_GO,
            transport=transport,
        )
    assert FRESH_ACCOUNT_CONFIG_UID_ABSENT in str(err.value)
    assert not (tmp_path / "d4_bound_account_identity_runtime_instance_v1.json").exists()
    assert not (tmp_path / "d5_checkpoint_observation_window_binding_v1.json").exists()
    claims = (tmp_path / "claims.json").read_text(encoding="utf-8")
    assert f'"D4_GENESIS_FIELD_FAIL_CLOSED":"{FRESH_ACCOUNT_CONFIG_UID_ABSENT}"' in claims
    assert not any(call.method == "POST" for call in transport.calls)
