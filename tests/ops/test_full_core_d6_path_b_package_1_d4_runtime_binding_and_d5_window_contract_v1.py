"""D6 PATH_B PACKAGE_1 D4 runtime binding and D5 window-binding contract."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.ops.capability_11_1_execution_domain_and_order_lifecycle_contracts_v1.execution_ports_v1 import (
    ExecutionPortConstructionForbiddenError,
    construct_live_execution_port_v1,
)
from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    BOUND_ACCOUNT_CONCRETE_UID_OBSERVED,
    BOUND_ACCOUNT_IDENTITY_RUNTIME_INSTANCE_PRESENT,
    CHECKPOINT_OBSERVATION_RUNTIME_INSTANCE_PRESENT,
    D4_CONCRETE_UID_CORROBORATED,
    D4_RUNTIME_BINDING_CONTRACT_PRESENT,
    D5_WINDOW_BINDING_CONTRACT_PRESENT,
    D5_WINDOW_END_EQUALS_OBSERVED_AT_AS_OF_RELATION_AUTHORITY_PRESENT,
    EXECUTION_READY,
    LIVE_ARMED,
    LIVE_ENABLED,
    OBSERVATION_EXECUTED,
    OBSERVATION_EXECUTION_AUTHORIZED,
    OBSERVATION_NETWORK_GET_AUTHORIZED,
    OBSERVATION_S0_RUNTIME_PAYLOADS_PRESENT,
    OBSERVATION_S0_STRUCTURAL_BLOCKERS_CLEARED,
    WIRE_SEND_PERMITTED,
)
from src.ops.full_core_live_path_composition_root_v1.live_admission_gap_dag_v1 import (
    live_admission_gap_dag_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.bound_account_identity_contract_v1 import (
    PROVENANCE_EXPLICIT_TYPED_BINDING,
    build_bound_account_identity_contract_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.bound_account_identity_runtime_binding_v1 import (
    CONCRETE_UID_CORROBORATED_TOKEN,
    BoundAccountIdentityRuntimeBindingError,
    build_bound_account_identity_runtime_binding_v1,
    inspect_bound_account_identity_runtime_binding_status_v1,
    load_bound_account_identity_runtime_binding_v1,
    persist_bound_account_identity_runtime_binding_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.checkpoint_observation_acquisition_contract_v1 import (
    FRESHNESS_EVIDENCE_STATUS,
    acquire_checkpoint_observation_v1,
    bind_checkpoint_observation_to_checkpoint_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.checkpoint_observation_window_binding_contract_v1 import (
    AS_OF_RELATION_UNPROVEN,
    BINDING_CLASS_EXPLICIT,
    CheckpointObservationWindowBindingContractError,
    bind_checkpoint_observation_window_v1,
    inspect_checkpoint_observation_window_binding_status_v1,
    persist_checkpoint_observation_window_binding_v1,
    reject_implicit_now_or_lookback_window_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.constants_v1 import (
    C01_REHABILITATION_FORBIDDEN,
    D6_FULLY_CLOSED,
    D7_AUTHORIZED,
    KIND_SET_RESOLVED,
    MS2_AUTHORIZED,
    OWNER,
    PACKAGE_1_PERSISTED,
    PATH_B_PREAUTHORIZATION_READY,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.equity_stock_checkpoint_contract_v1 import (
    build_equity_stock_checkpoint_contract_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.package_1_observation_s0_runtime_binding_gate_v1 import (
    S0_BLOCKED,
    Package1ObservationS0RuntimeBindingGateError,
    assert_package_1_observation_s0_runtime_payloads_present_v1,
    inspect_package_1_observation_s0_runtime_binding_gate_v1,
    reject_package_1_observation_execution_without_runtime_payloads_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.path_b_class_c_package_1_trading_account_observation_rules_contract_v1 import (
    corroborate_d4_identity_from_account_config_observation_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
RUNBOOK = REPO_ROOT / "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md"
SPEC_PATH = (
    REPO_ROOT
    / "docs/ops/specs/FULL_CORE_D6_PATH_B_PACKAGE_1_D4_RUNTIME_BINDING_AND_D5_WINDOW_CONTRACT_V1.md"
)
AZ_HEADING = "11.2.1.AZ FULL_CORE_D6_PATH_B_CLASS_C_PACKAGE_1_TRADING_ACCOUNT_OBSERVATION_RULES"
BA_HEADING = "11.2.1.BA FULL_CORE_D6_PATH_B_PACKAGE_1_D4_RUNTIME_BINDING_AND_D5_WINDOW_CONTRACT"
_ISO = "2026-09-13T08:26:00Z"
_ISO_START = "2026-09-13T08:00:00Z"
_ISO_END = "2026-09-13T09:00:00Z"
_DIGEST = "a" * 64
_DIGEST_B = "b" * 64
_NEW_CONTRACT_FILES = (
    "src/ops/governed_productive_account_equity_authority_producer_v1/"
    "bound_account_identity_runtime_binding_v1.py",
    "src/ops/governed_productive_account_equity_authority_producer_v1/"
    "checkpoint_observation_window_binding_contract_v1.py",
    "src/ops/governed_productive_account_equity_authority_producer_v1/"
    "package_1_observation_s0_runtime_binding_gate_v1.py",
)
_FORBIDDEN_ENGINE_MARKERS = (
    "reconstruct_equity_stock_from_events",
    "acquire_equity_events",
    "requests.",
    "httpx.",
    "urllib.request",
)
_FORBIDDEN_AUTHORITY_FLAGS = (
    "ATLAS_AUTHORITY_UPLIFTED",
    "KIND_SET_RESOLVED",
    "MS2_AUTHORIZED",
    "C01_REHABILITATED",
    "D7_AUTHORIZED",
    "LIVE_AUTHORIZED",
    "CANARY_AUTHORIZED",
)


def _identity_kwargs():
    identity = build_bound_account_identity_contract_v1(
        identity_id="SYNTHETIC_ACCOUNT_A",
        bound_account_identity="SYNTHETIC_ACCOUNT_A",
        bound_venue_identity="SYNTHETIC_VENUE_OKX",
        bound_td_mode="cross",
        settlement_currency="USDC",
    )
    return identity, {
        "bound_account_identity_ref": identity.identity_id,
        "bound_account_identity_digest": identity.identity_digest,
        "expected_bound_account_identity_ref": identity.identity_id,
        "expected_bound_account_identity_digest": identity.identity_digest,
    }


def _d5_pair():
    identity, identity_kwargs = _identity_kwargs()
    acquisition = acquire_checkpoint_observation_v1(
        observation_id="CKPT_OBS_A",
        source_observation_id="SRC_OBS_A",
        observed_at_as_of=_ISO,
        acquired_at=_ISO,
        component_completeness="COMPLETE",
        freshness_policy_status=FRESHNESS_EVIDENCE_STATUS,
        **identity_kwargs,
    )
    checkpoint = build_equity_stock_checkpoint_contract_v1(
        checkpoint_id="CKPT_OBSERVATION_A",
        schema_digest=_DIGEST,
        input_set_digest=_DIGEST_B,
        checkpoint_version="v1",
        bound_account_identity_ref=identity.identity_id,
        bound_account_identity_digest=identity.identity_digest,
    )
    checkpoint_binding = bind_checkpoint_observation_to_checkpoint_v1(
        binding_id="BIND_OBS_A",
        checkpoint=checkpoint,
        acquisition=acquisition,
    )
    return acquisition, checkpoint_binding


def _ba_section() -> str:
    runbook = RUNBOOK.read_text(encoding="utf-8")
    ba_start = runbook.index(BA_HEADING)
    return runbook[ba_start : runbook.index("## 11.3 Autonomy state model", ba_start)]


def test_valid_d4_explicit_typed_binding_is_digest_stable(tmp_path: Path) -> None:
    first = persist_bound_account_identity_runtime_binding_v1(
        store_root=tmp_path,
        identity_id="SYNTHETIC_ACCOUNT_A",
        bound_account_identity="SYNTHETIC_ACCOUNT_A",
        bound_venue_identity="SYNTHETIC_VENUE_OKX",
        bound_td_mode="cross",
        settlement_currency="USDC",
        identity_provenance_class=PROVENANCE_EXPLICIT_TYPED_BINDING,
    )
    loaded = load_bound_account_identity_runtime_binding_v1(store_root=tmp_path)
    again = build_bound_account_identity_runtime_binding_v1(
        identity_id="SYNTHETIC_ACCOUNT_A",
        bound_account_identity="SYNTHETIC_ACCOUNT_A",
        bound_venue_identity="SYNTHETIC_VENUE_OKX",
        bound_td_mode="cross",
        settlement_currency="USDC",
    )
    assert first.identity_provenance_class == PROVENANCE_EXPLICIT_TYPED_BINDING
    assert first.contract_status == "CONTRACT_PROVEN"
    assert first.runtime_instance_present == "true"
    assert first.concrete_uid_corroborated == CONCRETE_UID_CORROBORATED_TOKEN
    assert loaded.instance_digest == first.instance_digest
    assert again.instance_digest == first.instance_digest
    assert loaded.identity_digest == first.identity_digest


def test_d4_rejects_env_default_credential_and_implicit_provenance() -> None:
    with pytest.raises(BoundAccountIdentityRuntimeBindingError) as env_err:
        build_bound_account_identity_runtime_binding_v1(
            identity_id="SYNTHETIC_ACCOUNT_A",
            bound_account_identity="os.environ:ACCT",
            bound_venue_identity="SYNTHETIC_VENUE_OKX",
            bound_td_mode="cross",
            settlement_currency="USDC",
        )
    assert "IMPLICIT_OR_CREDENTIAL_TOKEN" in str(env_err.value)
    with pytest.raises(BoundAccountIdentityRuntimeBindingError) as cred_err:
        build_bound_account_identity_runtime_binding_v1(
            identity_id="SYNTHETIC_ACCOUNT_A",
            bound_account_identity="SYNTHETIC_ACCOUNT_A",
            bound_venue_identity="SYNTHETIC_VENUE_OKX",
            bound_td_mode="cross",
            settlement_currency="USDC",
            identity_provenance_class="CREDENTIAL",
        )
    assert "D4_RUNTIME_PROVENANCE_FORBIDDEN:CREDENTIAL" in str(cred_err.value)
    with pytest.raises(BoundAccountIdentityRuntimeBindingError) as default_err:
        build_bound_account_identity_runtime_binding_v1(
            identity_id="SYNTHETIC_ACCOUNT_A",
            bound_account_identity="SYNTHETIC_ACCOUNT_A",
            bound_venue_identity="SYNTHETIC_VENUE_OKX",
            bound_td_mode="cross",
            settlement_currency="USDC",
            identity_provenance_class="IMPLICIT_DEFAULT",
        )
    assert "D4_RUNTIME_PROVENANCE_FORBIDDEN:IMPLICIT_DEFAULT" in str(default_err.value)
    with pytest.raises(BoundAccountIdentityRuntimeBindingError):
        build_bound_account_identity_runtime_binding_v1(
            identity_id="SYNTHETIC_ACCOUNT_A",
            bound_account_identity="acct-uid-demo",
            bound_venue_identity="SYNTHETIC_VENUE_OKX",
            bound_td_mode="cross",
            settlement_currency="USDC",
        )


def test_d4_runtime_instance_is_not_uid_corroboration(tmp_path: Path) -> None:
    persist_bound_account_identity_runtime_binding_v1(
        store_root=tmp_path,
        identity_id="SYNTHETIC_ACCOUNT_A",
        bound_account_identity="SYNTHETIC_ACCOUNT_A",
        bound_venue_identity="SYNTHETIC_VENUE_OKX",
        bound_td_mode="cross",
        settlement_currency="USDC",
    )
    status = inspect_bound_account_identity_runtime_binding_status_v1(store_root=tmp_path)
    empty = inspect_bound_account_identity_runtime_binding_status_v1(store_root=None)
    assert status.runtime_instance_present == "true"
    assert status.artifact_present == "true"
    assert status.concrete_uid_corroborated == "false"
    assert empty.runtime_instance_present == "false"
    assert empty.contract_status == "CONTRACT_PROVEN"
    assert BOUND_ACCOUNT_IDENTITY_RUNTIME_INSTANCE_PRESENT is False
    assert D4_CONCRETE_UID_CORROBORATED is False
    assert BOUND_ACCOUNT_CONCRETE_UID_OBSERVED is False
    corroborated = corroborate_d4_identity_from_account_config_observation_v1(
        bound_account_identity="SYNTHETIC_ACCOUNT_A",
        bound_settlement_currency="USDC",
        observed_uid="SYNTHETIC_ACCOUNT_A",
        observed_main_uid="SYNTHETIC_MAIN_A",
        observed_settle_ccy="USDC",
        observed_account_mode="cross",
        identity_provenance_class=PROVENANCE_EXPLICIT_TYPED_BINDING,
    )
    assert corroborated == "D4_RUNTIME_EVIDENCE_CORROBORATED_IDENTITY_NOT_MINTED"
    reloaded = load_bound_account_identity_runtime_binding_v1(store_root=tmp_path)
    assert reloaded.concrete_uid_corroborated == "false"


def test_valid_explicit_d5_window_and_rejects_missing_invalid_and_implicit(
    tmp_path: Path,
) -> None:
    acquisition, checkpoint_binding = _d5_pair()
    window = bind_checkpoint_observation_window_v1(
        binding_id="WIN_A",
        checkpoint_id=checkpoint_binding.checkpoint_id,
        acquisition=acquisition,
        checkpoint_binding=checkpoint_binding,
        checkpoint_window_start=_ISO_START,
        checkpoint_window_end=_ISO_END,
    )
    persist_checkpoint_observation_window_binding_v1(store_root=tmp_path, binding=window)
    again = bind_checkpoint_observation_window_v1(
        binding_id="WIN_A",
        checkpoint_id=checkpoint_binding.checkpoint_id,
        acquisition=acquisition,
        checkpoint_binding=checkpoint_binding,
        checkpoint_window_start=_ISO_START,
        checkpoint_window_end=_ISO_END,
    )
    status = inspect_checkpoint_observation_window_binding_status_v1(store_root=tmp_path)
    assert window.binding_class == BINDING_CLASS_EXPLICIT
    assert window.observed_at_as_of_relation_class == AS_OF_RELATION_UNPROVEN
    assert window.event_completeness_from_window == "false"
    assert window.checkpoint_window_start == _ISO_START
    assert window.checkpoint_window_end == _ISO_END
    assert window.provenance_digest == again.provenance_digest
    assert status.artifact_present == "true"
    assert D5_WINDOW_END_EQUALS_OBSERVED_AT_AS_OF_RELATION_AUTHORITY_PRESENT is False
    with pytest.raises(CheckpointObservationWindowBindingContractError) as missing_start:
        bind_checkpoint_observation_window_v1(
            binding_id="WIN_B",
            checkpoint_id=checkpoint_binding.checkpoint_id,
            acquisition=acquisition,
            checkpoint_binding=checkpoint_binding,
            checkpoint_window_start="",
            checkpoint_window_end=_ISO_END,
        )
    assert "D5_WINDOW_FIELD_MISSING:checkpoint_window_start" in str(missing_start.value)
    with pytest.raises(CheckpointObservationWindowBindingContractError) as missing_end:
        bind_checkpoint_observation_window_v1(
            binding_id="WIN_C",
            checkpoint_id=checkpoint_binding.checkpoint_id,
            acquisition=acquisition,
            checkpoint_binding=checkpoint_binding,
            checkpoint_window_start=_ISO_START,
            checkpoint_window_end=None,
        )
    assert "D5_WINDOW_FIELD_MISSING:checkpoint_window_end" in str(missing_end.value)
    with pytest.raises(CheckpointObservationWindowBindingContractError) as invalid_range:
        bind_checkpoint_observation_window_v1(
            binding_id="WIN_D",
            checkpoint_id=checkpoint_binding.checkpoint_id,
            acquisition=acquisition,
            checkpoint_binding=checkpoint_binding,
            checkpoint_window_start=_ISO_END,
            checkpoint_window_end=_ISO_START,
        )
    assert "D5_WINDOW_RANGE_INVALID" in str(invalid_range.value)
    with pytest.raises(CheckpointObservationWindowBindingContractError) as now_err:
        bind_checkpoint_observation_window_v1(
            binding_id="WIN_E",
            checkpoint_id=checkpoint_binding.checkpoint_id,
            acquisition=acquisition,
            checkpoint_binding=checkpoint_binding,
            checkpoint_window_start=_ISO_START,
            checkpoint_window_end=_ISO_END,
            window_derivation_class="IMPLICIT_NOW",
        )
    assert "D5_WINDOW_IMPLICIT_NOW_OR_LOOKBACK_FORBIDDEN:IMPLICIT_NOW" in str(now_err.value)
    with pytest.raises(CheckpointObservationWindowBindingContractError) as lookback_err:
        reject_implicit_now_or_lookback_window_v1(window_derivation_class="LOOKBACK")
    assert "D5_WINDOW_IMPLICIT_NOW_OR_LOOKBACK_FORBIDDEN:LOOKBACK" in str(lookback_err.value)
    with pytest.raises(CheckpointObservationWindowBindingContractError) as equal_claim:
        bind_checkpoint_observation_window_v1(
            binding_id="WIN_F",
            checkpoint_id=checkpoint_binding.checkpoint_id,
            acquisition=acquisition,
            checkpoint_binding=checkpoint_binding,
            checkpoint_window_start=_ISO_START,
            checkpoint_window_end=_ISO_END,
            observed_at_as_of_relation_class="WINDOW_END_EQUALS_OBSERVED_AT_AS_OF",
        )
    assert "D5_WINDOW_AS_OF_RELATION_AUTHORITY_ABSENT" in str(equal_claim.value)
    with pytest.raises(CheckpointObservationWindowBindingContractError) as completeness:
        bind_checkpoint_observation_window_v1(
            binding_id="WIN_G",
            checkpoint_id=checkpoint_binding.checkpoint_id,
            acquisition=acquisition,
            checkpoint_binding=checkpoint_binding,
            checkpoint_window_start=_ISO_START,
            checkpoint_window_end=_ISO_END,
            event_completeness_from_window="true",
        )
    assert "D5_WINDOW_CANNOT_PROVE_EVENT_COMPLETENESS" in str(completeness.value)


def test_observation_remains_blocked_without_persisted_runtime_payloads(
    tmp_path: Path,
) -> None:
    empty = inspect_package_1_observation_s0_runtime_binding_gate_v1(store_root=None)
    assert empty.observation_s0_runtime_payloads_present == "false"
    assert empty.observation_executed == "false"
    assert empty.observation_execution_ready == "false"
    assert empty.gate_status == S0_BLOCKED
    with pytest.raises(Package1ObservationS0RuntimeBindingGateError) as blocked:
        assert_package_1_observation_s0_runtime_payloads_present_v1(store_root=None)
    assert S0_BLOCKED in str(blocked.value)
    persist_bound_account_identity_runtime_binding_v1(
        store_root=tmp_path,
        identity_id="SYNTHETIC_ACCOUNT_A",
        bound_account_identity="SYNTHETIC_ACCOUNT_A",
        bound_venue_identity="SYNTHETIC_VENUE_OKX",
        bound_td_mode="cross",
        settlement_currency="USDC",
    )
    with pytest.raises(Package1ObservationS0RuntimeBindingGateError):
        reject_package_1_observation_execution_without_runtime_payloads_v1(store_root=tmp_path)
    acquisition, checkpoint_binding = _d5_pair()
    window = bind_checkpoint_observation_window_v1(
        binding_id="WIN_S0",
        checkpoint_id=checkpoint_binding.checkpoint_id,
        acquisition=acquisition,
        checkpoint_binding=checkpoint_binding,
        checkpoint_window_start=_ISO_START,
        checkpoint_window_end=_ISO_END,
    )
    persist_checkpoint_observation_window_binding_v1(store_root=tmp_path, binding=window)
    assert_package_1_observation_s0_runtime_payloads_present_v1(store_root=tmp_path)
    with pytest.raises(Package1ObservationS0RuntimeBindingGateError) as exec_err:
        reject_package_1_observation_execution_without_runtime_payloads_v1(store_root=tmp_path)
    assert "OBSERVATION_EXECUTION_UNAUTHORIZED" in str(exec_err.value)
    assert OBSERVATION_S0_RUNTIME_PAYLOADS_PRESENT is False
    assert OBSERVATION_EXECUTED is False
    assert OBSERVATION_EXECUTION_AUTHORIZED is False
    assert OBSERVATION_NETWORK_GET_AUTHORIZED is False
    assert EXECUTION_READY is False


def test_no_network_side_effect_and_package_1_authority_non_regression() -> None:
    dag = live_admission_gap_dag_v1()
    assert D4_RUNTIME_BINDING_CONTRACT_PRESENT is True
    assert D5_WINDOW_BINDING_CONTRACT_PRESENT is True
    assert OBSERVATION_S0_STRUCTURAL_BLOCKERS_CLEARED is True
    assert BOUND_ACCOUNT_IDENTITY_RUNTIME_INSTANCE_PRESENT is False
    assert CHECKPOINT_OBSERVATION_RUNTIME_INSTANCE_PRESENT is False
    assert dag["D4_RUNTIME_BINDING_CONTRACT_PRESENT"] is True
    assert dag["D4_CONCRETE_UID_CORROBORATED"] is False
    assert dag["D5_WINDOW_BINDING_CONTRACT_PRESENT"] is True
    assert dag["OBSERVATION_S0_RUNTIME_PAYLOADS_PRESENT"] is False
    assert dag["KIND_SET_RESOLVED"] is False
    assert dag["MS2_AUTHORIZED"] is False
    assert dag["D6_FULLY_CLOSED"] is False
    assert dag["D7_AUTHORIZED"] is False
    assert PACKAGE_1_PERSISTED is True
    assert PATH_B_PREAUTHORIZATION_READY is True
    assert KIND_SET_RESOLVED is False
    assert MS2_AUTHORIZED is False
    assert D6_FULLY_CLOSED is False
    assert D7_AUTHORIZED is False
    assert C01_REHABILITATION_FORBIDDEN is True
    assert LIVE_ENABLED is False
    assert LIVE_ARMED is False
    assert WIRE_SEND_PERMITTED is False
    assert OWNER == "ops.governed_productive_account_equity_authority_producer_v1"
    with pytest.raises(ExecutionPortConstructionForbiddenError):
        construct_live_execution_port_v1()
    for rel in _NEW_CONTRACT_FILES:
        text = (REPO_ROOT / rel).read_text(encoding="utf-8")
        lowered = text.lower()
        for marker in _FORBIDDEN_ENGINE_MARKERS:
            assert marker not in lowered
        for flag in _FORBIDDEN_AUTHORITY_FLAGS:
            assert f"{flag}=true" not in text


def test_runbook_ba_persists_binding_contracts_without_real_values_or_get() -> None:
    spec = SPEC_PATH.read_text(encoding="utf-8")
    ba_section = _ba_section()
    az_section_start = RUNBOOK.read_text(encoding="utf-8").index(AZ_HEADING)
    az_section = RUNBOOK.read_text(encoding="utf-8")[
        az_section_start : RUNBOOK.read_text(encoding="utf-8").index(BA_HEADING, az_section_start)
    ]
    assert "THIS_SLICE=11.2.1.AZ" in az_section
    assert "THIS_SLICE=11.2.1.BA" not in az_section
    assert (
        "OWNER_GO=OWNER_GO_D6_PATH_B_PACKAGE_1_D4_RUNTIME_BINDING_AND_D5_WINDOW_CONTRACT_IMPLEMENTATION_V1"
        in ba_section
    )
    assert (
        "THIS_SLICE=11.2.1.BA.FULL_CORE_D6_PATH_B_PACKAGE_1_D4_RUNTIME_BINDING_AND_D5_WINDOW_CONTRACT"
        in ba_section
    )
    assert "D4_RUNTIME_BINDING_CONTRACT_PRESENT=true" in ba_section
    assert "BOUND_ACCOUNT_IDENTITY_RUNTIME_INSTANCE_PRESENT=false" in ba_section
    assert "D4_CONCRETE_UID_CORROBORATED=false" in ba_section
    assert "D5_WINDOW_BINDING_CONTRACT_PRESENT=true" in ba_section
    assert "CHECKPOINT_OBSERVATION_WINDOW_RUNTIME_INSTANCE_PRESENT=false" in ba_section
    assert "OBSERVATION_S0_RUNTIME_PAYLOADS_PRESENT=false" in ba_section
    assert "OBSERVATION_EXECUTED=false" in ba_section
    assert "NETWORK_GET_PERFORMED=false" in ba_section
    assert "NETWORK_POST_PERFORMED=false" in ba_section
    assert "KIND_SET_RESOLVED=false" in ba_section
    assert "MS2_AUTHORIZED=false" in ba_section
    assert "D7_AUTHORIZED=false" in ba_section
    assert "LIVE_ENABLED=false" in ba_section
    assert "MASTER_V2_UNCHANGED=true" in ba_section
    assert "DOUBLE_PLAY_UNCHANGED=true" in ba_section
    assert (
        "DOCS_TOKEN_FULL_CORE_D6_PATH_B_PACKAGE_1_D4_RUNTIME_BINDING_AND_D5_WINDOW_CONTRACT_V1"
        in spec
    )
    mot = (REPO_ROOT / "docs/governance/PEAK_TRADE_MAP_OF_TRUTH.md").read_text(encoding="utf-8")
    assert "FULL_CORE_D6_PATH_B_PACKAGE_1_D4_RUNTIME_BINDING_AND_D5_WINDOW_CONTRACT_V1.md" in mot
    assert (
        "§11.2.1.BA FULL_CORE_D6_PATH_B_PACKAGE_1_D4_RUNTIME_BINDING_AND_D5_WINDOW_CONTRACT" in mot
    )
