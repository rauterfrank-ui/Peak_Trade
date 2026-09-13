"""D5 checkpoint-observation acquisition and checkpoint reference binding."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.ops.capability_11_1_execution_domain_and_order_lifecycle_contracts_v1.execution_ports_v1 import (
    ExecutionPortConstructionForbiddenError,
    construct_live_execution_port_v1,
)
from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    ACCOUNT_EQUITY_AUTHORITY_OWNER,
    BOUND_ACCOUNT_CONCRETE_UID_OBSERVED,
    BOUND_ACCOUNT_IDENTITY_PROVEN,
    C01_C16_REJECTION_STILL_BINDING,
    C17_CREATED,
    C17_CREATION_FROZEN_UNTIL_D1_D9_PROVEN,
    CHECKPOINT_CAN_MINT_EQUITY,
    CHECKPOINT_OBSERVATION_ACQUISITION_CREATED,
    CHECKPOINT_OBSERVATION_ACQUISITION_SCHEMA_PRESENT,
    CHECKPOINT_OBSERVATION_NETWORK_GET_AUTHORIZED,
    CHECKPOINT_OBSERVATION_PROVEN,
    CHECKPOINT_OBSERVATION_RUNTIME_INSTANCE_PRESENT,
    EARLIEST_OPTION_D_DEPENDENCY,
    EVENT_ACQUISITION_CREATED,
    GOVERNED_PRODUCER_CREATED,
    LIVE_ARMED,
    LIVE_ENABLED,
    MAPPING_PROVEN,
    RAW_EQ_SOURCE_AUTHORITY,
    RECONSTRUCTION_ENGINE_CREATED,
    RESTART_PROVEN,
    SOURCE_SELECTED,
    WIRE_SEND_PERMITTED,
)
from src.ops.full_core_live_path_composition_root_v1.live_admission_gap_dag_v1 import (
    EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY,
    live_admission_gap_dag_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.bound_account_identity_contract_v1 import (
    BoundAccountIdentityContractV1,
    build_bound_account_identity_contract_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.checkpoint_observation_acquisition_contract_v1 import (
    FRESHNESS_EVIDENCE_STATUS,
    CheckpointObservationAcquisitionContractError,
    acquire_checkpoint_observation_v1,
    bind_checkpoint_observation_to_checkpoint_v1,
    compute_checkpoint_observation_digest_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.constants_v1 import (
    C01_C16_NOT_ELEVATED,
    C01_C16_REVIVAL_ALLOWED,
    OWNER,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.equity_stock_checkpoint_contract_v1 import (
    EQUITY_MINT_STATUS_NOT_MINTED,
    build_equity_stock_checkpoint_contract_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.source_candidate_v1 import (
    C01_C16_IDS,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
RUNBOOK = REPO_ROOT / "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md"
SPEC_PATH = REPO_ROOT / "docs/ops/specs/FULL_CORE_D5_CHECKPOINT_OBSERVATION_ACQUISITION_V1.md"
AS_HEADING = "11.2.1.AS FULL_CORE_D4_BOUND_ACCOUNT_IDENTITY_CONTRACT"
AT_HEADING = "11.2.1.AT FULL_CORE_D5_CHECKPOINT_OBSERVATION_ACQUISITION"
_DIGEST = "a" * 64
_DIGEST_B = "b" * 64
_ISO = "2026-09-13T08:26:00Z"
_NEW_CONTRACT_FILES = (
    "src/ops/governed_productive_account_equity_authority_producer_v1/"
    "checkpoint_observation_acquisition_contract_v1.py",
    "src/ops/governed_productive_account_equity_authority_producer_v1/"
    "equity_stock_checkpoint_contract_v1.py",
    "src/ops/governed_productive_account_equity_authority_producer_v1/"
    "bound_account_identity_contract_v1.py",
)
_FORBIDDEN_ENGINE_MARKERS = (
    "reconstruct_equity_stock_from_events",
    "acquire_equity_events",
    "requests.",
    "httpx.",
    "urllib.request",
)


def _identity(*, identity_id: str, account: str) -> BoundAccountIdentityContractV1:
    return build_bound_account_identity_contract_v1(
        identity_id=identity_id,
        bound_account_identity=account,
        bound_venue_identity="SYNTHETIC_VENUE_OKX",
        bound_td_mode="cross",
        settlement_currency="USDC",
    )


def _identity_kwargs(identity: BoundAccountIdentityContractV1) -> dict[str, str]:
    return {
        "bound_account_identity_ref": identity.identity_id,
        "bound_account_identity_digest": identity.identity_digest,
        "expected_bound_account_identity_ref": identity.identity_id,
        "expected_bound_account_identity_digest": identity.identity_digest,
    }


def _checkpoint(identity: BoundAccountIdentityContractV1):
    return build_equity_stock_checkpoint_contract_v1(
        checkpoint_id="CKPT_OBSERVATION_A",
        schema_digest=_DIGEST,
        input_set_digest=_DIGEST_B,
        checkpoint_version="v1",
        bound_account_identity_ref=identity.identity_id,
        bound_account_identity_digest=identity.identity_digest,
    )


def _acquire(identity: BoundAccountIdentityContractV1, **overrides: str):
    fields = {
        "observation_id": "CKPT_OBS_A",
        "source_observation_id": "SRC_OBS_A",
        "observed_at_as_of": _ISO,
        "acquired_at": _ISO,
        "component_completeness": "COMPLETE",
        "freshness_policy_status": FRESHNESS_EVIDENCE_STATUS,
        **_identity_kwargs(identity),
    }
    fields.update(overrides)
    return acquire_checkpoint_observation_v1(**fields)


def _at_section() -> str:
    runbook = RUNBOOK.read_text(encoding="utf-8")
    at_start = runbook.index(AT_HEADING)
    return runbook[at_start : runbook.index("## 11.3 Autonomy state model", at_start)]


def test_d4_prerequisite_and_exact_identity_match() -> None:
    identity = _identity(identity_id="SYNTHETIC_ACCOUNT_A", account="SYNTHETIC_ACCOUNT_A")
    result = _acquire(identity)
    checkpoint = _checkpoint(identity)
    binding = bind_checkpoint_observation_to_checkpoint_v1(
        binding_id="BIND_OBS_A",
        checkpoint=checkpoint,
        acquisition=result,
    )
    assert BOUND_ACCOUNT_IDENTITY_PROVEN is True
    assert result.bound_account_identity_ref == identity.identity_id
    assert result.bound_account_identity_digest == identity.identity_digest
    assert result.source_observation_id == "SRC_OBS_A"
    assert result.acquired_at == _ISO
    assert result.observed_at_as_of == _ISO
    assert result.authority_owner == ACCOUNT_EQUITY_AUTHORITY_OWNER
    assert result.authority_effect == "NONE"
    assert binding.checkpoint_id == checkpoint.checkpoint_id
    assert binding.checkpoint_observation_ref == result.observation_id
    assert binding.checkpoint_observation_digest == result.provenance_digest
    assert binding.checkpoint_provenance_digest == checkpoint.provenance_digest
    assert binding.equity_mint_status == EQUITY_MINT_STATUS_NOT_MINTED


def test_cross_account_mismatch_fail_closed() -> None:
    identity_a = _identity(identity_id="SYNTHETIC_ACCOUNT_A", account="SYNTHETIC_ACCOUNT_A")
    identity_b = _identity(identity_id="SYNTHETIC_ACCOUNT_B", account="SYNTHETIC_ACCOUNT_B")
    with pytest.raises(CheckpointObservationAcquisitionContractError) as mismatch:
        acquire_checkpoint_observation_v1(
            observation_id="CKPT_OBS_MIX",
            source_observation_id="SRC_OBS_MIX",
            expected_bound_account_identity_ref=identity_a.identity_id,
            expected_bound_account_identity_digest=identity_a.identity_digest,
            bound_account_identity_ref=identity_b.identity_id,
            bound_account_identity_digest=identity_b.identity_digest,
            observed_at_as_of=_ISO,
            acquired_at=_ISO,
            component_completeness="COMPLETE",
            freshness_policy_status=FRESHNESS_EVIDENCE_STATUS,
        )
    assert "CHECKPOINT_OBSERVATION_IDENTITY_MISMATCH_CROSS_ACCOUNT" in str(mismatch.value)
    result_b = _acquire(identity_b)
    with pytest.raises(CheckpointObservationAcquisitionContractError) as bind_err:
        bind_checkpoint_observation_to_checkpoint_v1(
            binding_id="BIND_MIX",
            checkpoint=_checkpoint(identity_a),
            acquisition=result_b,
        )
    assert "CHECKPOINT_OBSERVATION_IDENTITY_MISMATCH_CROSS_ACCOUNT" in str(bind_err.value)


def test_missing_unknown_stale_partial_observation_fail_closed() -> None:
    identity = _identity(identity_id="SYNTHETIC_ACCOUNT_A", account="SYNTHETIC_ACCOUNT_A")
    with pytest.raises(CheckpointObservationAcquisitionContractError):
        _acquire(identity, observation_id="")
    with pytest.raises(CheckpointObservationAcquisitionContractError) as unknown_err:
        _acquire(identity, observation_id="UNKNOWN")
    assert "UNKNOWN_FAIL_CLOSED" in str(unknown_err.value)
    with pytest.raises(CheckpointObservationAcquisitionContractError) as stale_err:
        _acquire(identity, freshness_policy_status="STALE")
    assert "STALE_FAIL_CLOSED" in str(stale_err.value)
    with pytest.raises(CheckpointObservationAcquisitionContractError) as partial_err:
        _acquire(identity, component_completeness="PARTIAL")
    assert "PARTIAL_FAIL_CLOSED" in str(partial_err.value)
    with pytest.raises(CheckpointObservationAcquisitionContractError):
        _acquire(identity, observed_at_as_of="MISSING")
    with pytest.raises(CheckpointObservationAcquisitionContractError):
        _acquire(identity, acquired_at="")


def test_provenance_reference_digest_integrity() -> None:
    identity = _identity(identity_id="SYNTHETIC_ACCOUNT_A", account="SYNTHETIC_ACCOUNT_A")
    result = _acquire(identity)
    again = _acquire(identity)
    assert result.provenance_digest == again.provenance_digest
    payload = {
        "observation_id": result.observation_id,
        "source_observation_id": result.source_observation_id,
        "observation_semantic_class": result.observation_semantic_class,
        "authority_owner": result.authority_owner,
        "bound_account_identity_ref": result.bound_account_identity_ref,
        "bound_account_identity_digest": result.bound_account_identity_digest,
        "observed_at_as_of": result.observed_at_as_of,
        "acquired_at": result.acquired_at,
        "component_completeness": result.component_completeness,
        "freshness_policy_status": result.freshness_policy_status,
        "observation_vs_authority_class": result.observation_vs_authority_class,
        "network_method": result.network_method,
        "claimed_equity_stock_value": result.claimed_equity_stock_value,
        "reconstructed_equity_created": result.reconstructed_equity_created,
        "event_stream_acquisition_created": result.event_stream_acquisition_created,
        "eq_reconciliation_executed": result.eq_reconciliation_executed,
        "raw_eq_source_authority": result.raw_eq_source_authority,
        "source_selected": result.source_selected,
        "mapping_proven": result.mapping_proven,
        "c17_created": result.c17_created,
        "authority_effect": result.authority_effect,
    }
    assert result.provenance_digest == compute_checkpoint_observation_digest_v1(payload)
    other = _acquire(identity, source_observation_id="SRC_OBS_B")
    assert other.provenance_digest != result.provenance_digest
    binding = bind_checkpoint_observation_to_checkpoint_v1(
        binding_id="BIND_OBS_A",
        checkpoint=_checkpoint(identity),
        acquisition=result,
    )
    assert binding.checkpoint_observation_digest == result.provenance_digest
    assert binding.bound_account_identity_digest == identity.identity_digest


def test_checkpoint_cannot_mint_or_reconstruct_equity() -> None:
    identity = _identity(identity_id="SYNTHETIC_ACCOUNT_A", account="SYNTHETIC_ACCOUNT_A")
    with pytest.raises(CheckpointObservationAcquisitionContractError) as mint_err:
        _acquire(identity, claimed_equity_stock_value="12.50")
    assert "CHECKPOINT_OBSERVATION_CANNOT_MINT_EQUITY" in str(mint_err.value)
    with pytest.raises(CheckpointObservationAcquisitionContractError):
        _acquire(identity, claimed_equity_stock_value="reconstructed_equity")
    result = _acquire(identity)
    checkpoint = _checkpoint(identity)
    binding = bind_checkpoint_observation_to_checkpoint_v1(
        binding_id="BIND_OBS_A",
        checkpoint=checkpoint,
        acquisition=result,
    )
    assert CHECKPOINT_CAN_MINT_EQUITY is False
    assert checkpoint.claimed_equity_stock_value == "ABSENT"
    assert checkpoint.equity_mint_status == EQUITY_MINT_STATUS_NOT_MINTED
    assert result.reconstructed_equity_created == "false"
    assert binding.reconstructed_equity_created == "false"


def test_no_event_stream_fresh_eq_or_network_get() -> None:
    identity = _identity(identity_id="SYNTHETIC_ACCOUNT_A", account="SYNTHETIC_ACCOUNT_A")
    with pytest.raises(CheckpointObservationAcquisitionContractError) as get_err:
        _acquire(identity, network_method="GET")
    assert "NETWORK_METHOD_FORBIDDEN:GET" in str(get_err.value)
    with pytest.raises(CheckpointObservationAcquisitionContractError) as post_err:
        _acquire(identity, network_method="POST")
    assert "NETWORK_METHOD_FORBIDDEN:POST" in str(post_err.value)
    with pytest.raises(CheckpointObservationAcquisitionContractError) as event_err:
        _acquire(identity, source_observation_id="classified_event_stream")
    assert "EVENT_STREAM_ACQUISITION_FORBIDDEN" in str(event_err.value)
    result = _acquire(identity)
    assert result.event_stream_acquisition_created == "false"
    assert result.eq_reconciliation_executed == "false"
    assert result.network_method == "NONE"
    assert result.raw_eq_source_authority == "false"
    assert result.source_selected == "false"
    assert result.mapping_proven == "false"
    assert result.c17_created == "false"


def test_existing_owner_pins_and_non_regression() -> None:
    dag = live_admission_gap_dag_v1()
    assert OWNER == "ops.governed_productive_account_equity_authority_producer_v1"
    assert ACCOUNT_EQUITY_AUTHORITY_OWNER == OWNER
    assert CHECKPOINT_OBSERVATION_ACQUISITION_SCHEMA_PRESENT is True
    assert CHECKPOINT_OBSERVATION_ACQUISITION_CREATED is True
    assert CHECKPOINT_OBSERVATION_PROVEN is True
    assert CHECKPOINT_OBSERVATION_RUNTIME_INSTANCE_PRESENT is False
    assert CHECKPOINT_OBSERVATION_NETWORK_GET_AUTHORIZED is False
    assert BOUND_ACCOUNT_CONCRETE_UID_OBSERVED is False
    assert C01_C16_REJECTION_STILL_BINDING is True
    assert C01_C16_REVIVAL_ALLOWED is False
    assert C01_C16_NOT_ELEVATED is True
    assert len(C01_C16_IDS) == 16
    assert C17_CREATED is False
    assert C17_CREATION_FROZEN_UNTIL_D1_D9_PROVEN is True
    assert SOURCE_SELECTED is False
    assert MAPPING_PROVEN is False
    assert GOVERNED_PRODUCER_CREATED is False
    assert EVENT_ACQUISITION_CREATED is False
    assert RECONSTRUCTION_ENGINE_CREATED is False
    assert RESTART_PROVEN is False
    assert RAW_EQ_SOURCE_AUTHORITY is False
    assert LIVE_ENABLED is False
    assert LIVE_ARMED is False
    assert WIRE_SEND_PERMITTED is False
    assert dag["CHECKPOINT_OBSERVATION_ACQUISITION_CREATED"] is True
    assert dag["CHECKPOINT_OBSERVATION_PROVEN"] is True
    assert dag["CHECKPOINT_OBSERVATION_NETWORK_GET_AUTHORIZED"] is False
    assert dag["EVENT_ACQUISITION_CREATED"] is False
    assert dag["EARLIEST_OPTION_D_DEPENDENCY"] == (
        "D6_COMPLETE_CLASSIFIED_EVENT_STREAM_ACQUISITION"
    )
    assert EARLIEST_OPTION_D_DEPENDENCY == "D6_COMPLETE_CLASSIFIED_EVENT_STREAM_ACQUISITION"
    assert EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY == (
        "NO_CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING"
    )
    with pytest.raises(ExecutionPortConstructionForbiddenError):
        construct_live_execution_port_v1()
    for relative in _NEW_CONTRACT_FILES:
        text = (REPO_ROOT / relative).read_text(encoding="utf-8")
        lowered = text.lower()
        for marker in _FORBIDDEN_ENGINE_MARKERS:
            assert marker not in lowered
        assert "def reconstruct_equity_stock" not in text
        assert "def acquire_events" not in text


def test_runbook_at_consumes_owner_go_without_rewriting_as_or_protected_surfaces() -> None:
    runbook = RUNBOOK.read_text(encoding="utf-8")
    spec = SPEC_PATH.read_text(encoding="utf-8")
    at_section = _at_section()
    as_start = runbook.index(AS_HEADING)
    as_section = runbook[as_start : runbook.index(AT_HEADING, as_start)]
    assert "THIS_SLICE=11.2.1.AS" in as_section
    assert "THIS_SLICE=11.2.1.AT" not in as_section
    assert "EARLIEST_OPTION_D_DEPENDENCY=D5_CHECKPOINT_OBSERVATION_ACQUISITION" in as_section
    assert (
        "OWNER_GO=OWNER_GO_OPTION_D_D5_CHECKPOINT_OBSERVATION_ACQUISITION_WORKPACKAGE_V1"
        in at_section
    )
    assert "OWNER_GO_STATUS=CONSUMED" in at_section
    assert "THIS_SLICE=11.2.1.AT.FULL_CORE_D5_CHECKPOINT_OBSERVATION_ACQUISITION" in at_section
    assert "CHECKPOINT_OBSERVATION_ACQUISITION_CREATED=true" in at_section
    assert "CHECKPOINT_OBSERVATION_PROVEN=true" in at_section
    assert "CHECKPOINT_OBSERVATION_RUNTIME_INSTANCE_PRESENT=false" in at_section
    assert "CHECKPOINT_OBSERVATION_NETWORK_GET_AUTHORIZED=false" in at_section
    assert "NETWORK_GET_PERFORMED=false" in at_section
    assert "NETWORK_POST_PERFORMED=false" in at_section
    assert "NEW_TRANSPORT_CREATED=false" in at_section
    assert (
        "D5_CHECKPOINT_OBSERVATION_ACQUISITION="
        "TYPED_ACQUISITION_CONTRACT_PRESENT_AND_CHECKPOINT_BOUND" in at_section
    )
    assert (
        "EARLIEST_OPTION_D_DEPENDENCY=D6_COMPLETE_CLASSIFIED_EVENT_STREAM_ACQUISITION" in at_section
    )
    assert "CHECKPOINT_CAN_MINT_EQUITY=false" in at_section
    assert "RECONSTRUCTED_EQUITY_CREATED=false" in at_section
    assert "EVENT_STREAM_ACQUISITION_CREATED=false" in at_section
    assert "EQ_RECONCILIATION_EXECUTED=false" in at_section
    assert "RAW_EQ_SOURCE_AUTHORITY=false" in at_section
    assert "SOURCE_SELECTED=false" in at_section
    assert "MAPPING_PROVEN=false" in at_section
    assert "C17_CREATED=false" in at_section
    assert "EVENT_ACQUISITION_CREATED=false" in at_section
    assert "RECONSTRUCTION_ENGINE_CREATED=false" in at_section
    assert "EXISTING_AUTHORITY_OWNER_UNCHANGED=true" in at_section
    assert (
        "ACCOUNT_EQUITY_AUTHORITY_OWNER="
        "ops.governed_productive_account_equity_authority_producer_v1" in at_section
    )
    assert "LIVE_ENABLED=false" in at_section
    assert "LIVE_ARMED=false" in at_section
    assert "WIRE_SEND_PERMITTED=false" in at_section
    assert "MASTER_V2_UNCHANGED=true" in at_section
    assert "DOUBLE_PLAY_UNCHANGED=true" in at_section
    assert "BULL_BEAR_STATE_SWITCH_UNCHANGED=true" in at_section
    assert "TOP20_RANKING_UNIVERSE_UNCHANGED=true" in at_section
    assert "SELF_LEARNING_UNCHANGED=true" in at_section
    assert "FULL_CORE_AUTONOMY_UNCHANGED=true" in at_section
    assert "PROTECTED_SURFACES_UNCHANGED=true" in at_section
    assert "CORE_LOGIC_CHANGE=false" in at_section
    assert "CONSTRUCT_LIVE_EXECUTION_PORT_V1=FORBIDDEN_IN_CAP_11_1" in at_section
    assert "DOCS_TOKEN_FULL_CORE_D5_CHECKPOINT_OBSERVATION_ACQUISITION_V1" in spec
    assert "D5_CHECKPOINT_OBSERVATION_ACQUISITION=NOT_BUILT" in as_section
    assert "C17_CREATED=false" in as_section
