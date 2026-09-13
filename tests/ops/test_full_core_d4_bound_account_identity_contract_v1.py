"""D4 bound account-identity contract and reference-only binding."""

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
    BOUND_ACCOUNT_IDENTITY_CONTRACT_SCHEMA_PRESENT,
    BOUND_ACCOUNT_IDENTITY_FROM_CREDENTIAL_FORBIDDEN,
    BOUND_ACCOUNT_IDENTITY_FROM_ENV_FORBIDDEN,
    BOUND_ACCOUNT_IDENTITY_IMPLICIT_DEFAULT_FORBIDDEN,
    BOUND_ACCOUNT_IDENTITY_PROVEN,
    BOUND_ACCOUNT_IDENTITY_RUNTIME_INSTANCE_PRESENT,
    C01_C16_REJECTION_STILL_BINDING,
    C17_CREATED,
    C17_CREATION_FROZEN_UNTIL_D1_D9_PROVEN,
    EARLIEST_OPTION_D_DEPENDENCY,
    EVENT_ACQUISITION_CREATED,
    GOVERNED_PRODUCER_CREATED,
    LIVE_ARMED,
    LIVE_ENABLED,
    MAPPING_PROVEN,
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
    FORBIDDEN_PROVENANCE_CLASSES,
    NOT_D4_IDENTITY_MEMBERS,
    RATIFIED_IDENTITY_MEMBERS,
    BoundAccountIdentityContractError,
    BoundAccountIdentityContractV1,
    assert_same_bound_account_identity_v1,
    build_bound_account_identity_contract_v1,
    require_bound_account_identity_ref_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.constants_v1 import (
    C01_C16_NOT_ELEVATED,
    C01_C16_REVIVAL_ALLOWED,
    OWNER,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.equity_affecting_event_taxonomy_contract_v1 import (
    CLASSIFICATION_STATUS_UNKNOWN,
    build_equity_affecting_event_taxonomy_record_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.equity_stock_checkpoint_contract_v1 import (
    BOUND_ACCOUNT_IDENTITY_STATUS_BOUND_BY_REFERENCE,
    build_equity_stock_checkpoint_contract_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.fresh_eq_reconciliation_target_contract_v1 import (
    build_fresh_eq_reconciliation_target_contract_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.source_candidate_v1 import (
    C01_C16_IDS,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
RUNBOOK = REPO_ROOT / "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md"
SPEC_PATH = REPO_ROOT / "docs/ops/specs/FULL_CORE_D4_BOUND_ACCOUNT_IDENTITY_CONTRACT_V1.md"
AR_HEADING = (
    "11.2.1.AR FULL_CORE_OPTION_D_SSOT_CHECKPOINT_EVENT_TAXONOMY_"
    "AND_EQ_RECONCILIATION_TARGET_CONTRACTS"
)
AS_HEADING = "11.2.1.AS FULL_CORE_D4_BOUND_ACCOUNT_IDENTITY_CONTRACT"
_DIGEST = "a" * 64
_DIGEST_B = "b" * 64
_NEW_CONTRACT_FILES = (
    "src/ops/governed_productive_account_equity_authority_producer_v1/"
    "bound_account_identity_contract_v1.py",
    "src/ops/governed_productive_account_equity_authority_producer_v1/"
    "equity_stock_checkpoint_contract_v1.py",
    "src/ops/governed_productive_account_equity_authority_producer_v1/"
    "equity_affecting_event_taxonomy_contract_v1.py",
    "src/ops/governed_productive_account_equity_authority_producer_v1/"
    "fresh_eq_reconciliation_target_contract_v1.py",
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
    }


def _as_section() -> str:
    runbook = RUNBOOK.read_text(encoding="utf-8")
    as_start = runbook.index(AS_HEADING)
    return runbook[as_start : runbook.index("## 11.3 Autonomy state model", as_start)]


def test_d4_members_are_explicit_and_digest_is_deterministic() -> None:
    identity = _identity(identity_id="SYNTHETIC_ACCOUNT_A", account="SYNTHETIC_ACCOUNT_A")
    again = _identity(identity_id="SYNTHETIC_ACCOUNT_A", account="SYNTHETIC_ACCOUNT_A")
    assert RATIFIED_IDENTITY_MEMBERS == (
        "bound_account_identity",
        "bound_venue_identity",
        "bound_td_mode",
        "settlement_currency",
    )
    assert "expected_instrument_id" in NOT_D4_IDENTITY_MEMBERS
    assert "instId" in NOT_D4_IDENTITY_MEMBERS
    assert "rest_host" in NOT_D4_IDENTITY_MEMBERS
    assert "account_mode" in NOT_D4_IDENTITY_MEMBERS
    assert identity.identity_kind == "GOVERNED_ACCOUNT_DOMAIN_IDENTITY"
    assert identity.identity_provenance_class == "EXPLICIT_TYPED_BINDING"
    assert identity.authority_owner == ACCOUNT_EQUITY_AUTHORITY_OWNER
    assert identity.authority_effect == "NONE"
    assert identity.identity_digest == again.identity_digest
    assert (
        identity.identity_digest
        != _identity(
            identity_id="SYNTHETIC_ACCOUNT_B", account="SYNTHETIC_ACCOUNT_B"
        ).identity_digest
    )


def test_env_credential_implicit_unknown_and_missing_identity_fail_closed() -> None:
    with pytest.raises(BoundAccountIdentityContractError) as env_err:
        build_bound_account_identity_contract_v1(
            identity_id="SYNTHETIC_ACCOUNT_A",
            bound_account_identity="os.environ:ACCT",
            bound_venue_identity="SYNTHETIC_VENUE_OKX",
            bound_td_mode="cross",
            settlement_currency="USDC",
        )
    assert "BOUND_ACCOUNT_IDENTITY_IMPLICIT_OR_CREDENTIAL_TOKEN" in str(env_err.value)
    with pytest.raises(BoundAccountIdentityContractError) as cred_err:
        build_bound_account_identity_contract_v1(
            identity_id="SYNTHETIC_ACCOUNT_A",
            bound_account_identity="acct-uid-demo",
            bound_venue_identity="SYNTHETIC_VENUE_OKX",
            bound_td_mode="cross",
            settlement_currency="USDC",
        )
    assert "BOUND_ACCOUNT_IDENTITY_IMPLICIT_OR_CREDENTIAL_TOKEN" in str(cred_err.value)
    with pytest.raises(BoundAccountIdentityContractError) as unknown_err:
        build_bound_account_identity_contract_v1(
            identity_id="SYNTHETIC_ACCOUNT_A",
            bound_account_identity="UNKNOWN",
            bound_venue_identity="SYNTHETIC_VENUE_OKX",
            bound_td_mode="cross",
            settlement_currency="USDC",
        )
    assert "BOUND_ACCOUNT_IDENTITY_UNKNOWN_OR_MISSING" in str(unknown_err.value)
    with pytest.raises(BoundAccountIdentityContractError):
        build_bound_account_identity_contract_v1(
            identity_id="SYNTHETIC_ACCOUNT_A",
            bound_account_identity="",
            bound_venue_identity="SYNTHETIC_VENUE_OKX",
            bound_td_mode="cross",
            settlement_currency="USDC",
        )
    for provenance in FORBIDDEN_PROVENANCE_CLASSES:
        with pytest.raises(BoundAccountIdentityContractError):
            build_bound_account_identity_contract_v1(
                identity_id="SYNTHETIC_ACCOUNT_A",
                bound_account_identity="SYNTHETIC_ACCOUNT_A",
                bound_venue_identity="SYNTHETIC_VENUE_OKX",
                bound_td_mode="cross",
                settlement_currency="USDC",
                identity_provenance_class=provenance,
            )
    with pytest.raises(BoundAccountIdentityContractError):
        require_bound_account_identity_ref_v1(
            bound_account_identity_ref=None,
            bound_account_identity_digest=_DIGEST,
        )
    with pytest.raises(BoundAccountIdentityContractError):
        require_bound_account_identity_ref_v1(
            bound_account_identity_ref="UNKNOWN",
            bound_account_identity_digest=_DIGEST,
        )


def test_checkpoint_event_and_eq_bind_identity_by_reference_only() -> None:
    identity = _identity(identity_id="SYNTHETIC_ACCOUNT_A", account="SYNTHETIC_ACCOUNT_A")
    kwargs = _identity_kwargs(identity)
    checkpoint = build_equity_stock_checkpoint_contract_v1(
        checkpoint_id="CKPT_IDENTITY_A",
        schema_digest=_DIGEST,
        input_set_digest=_DIGEST_B,
        checkpoint_version="v1",
        **kwargs,
    )
    event = build_equity_affecting_event_taxonomy_record_v1(
        event_record_id="EVT_IDENTITY_A",
        classification_status=CLASSIFICATION_STATUS_UNKNOWN,
        event_semantic_class=CLASSIFICATION_STATUS_UNKNOWN,
        ordering_key="1",
        event_digest=_DIGEST,
        mapped_numeric_effect="FORBIDDEN_NOT_ZERO",
        **kwargs,
    )
    target = build_fresh_eq_reconciliation_target_contract_v1(
        reconciliation_record_id="EQ_IDENTITY_A",
        reconstructed_equity_fact_id="RECON_FACT_A",
        reconstructed_equity_provenance_digest=_DIGEST,
        reconstructed_equity_value_state="PRESENT",
        reconstructed_equity_value="12.50",
        venue_eq_fact_id="VENUE_EQ_FACT_A",
        venue_eq_provenance_digest=_DIGEST_B,
        venue_eq_value_state="PRESENT",
        venue_eq_value="12.50",
        **kwargs,
    )
    assert checkpoint.bound_account_identity_ref == identity.identity_id
    assert checkpoint.bound_account_identity_digest == identity.identity_digest
    assert (
        checkpoint.bound_account_identity_status == BOUND_ACCOUNT_IDENTITY_STATUS_BOUND_BY_REFERENCE
    )
    assert not hasattr(checkpoint, "bound_account_identity")
    assert event.bound_account_identity_ref == identity.identity_id
    assert target.bound_account_identity_ref == identity.identity_id
    assert_same_bound_account_identity_v1(
        left_ref=checkpoint.bound_account_identity_ref,
        left_digest=checkpoint.bound_account_identity_digest,
        right_ref=event.bound_account_identity_ref,
        right_digest=event.bound_account_identity_digest,
    )
    assert_same_bound_account_identity_v1(
        left_ref=event.bound_account_identity_ref,
        left_digest=event.bound_account_identity_digest,
        right_ref=target.bound_account_identity_ref,
        right_digest=target.bound_account_identity_digest,
    )


def test_cross_account_mix_and_missing_identity_fail_closed() -> None:
    identity_a = _identity(identity_id="SYNTHETIC_ACCOUNT_A", account="SYNTHETIC_ACCOUNT_A")
    identity_b = _identity(identity_id="SYNTHETIC_ACCOUNT_B", account="SYNTHETIC_ACCOUNT_B")
    checkpoint = build_equity_stock_checkpoint_contract_v1(
        checkpoint_id="CKPT_IDENTITY_A",
        schema_digest=_DIGEST,
        input_set_digest=_DIGEST_B,
        checkpoint_version="v1",
        **_identity_kwargs(identity_a),
    )
    event = build_equity_affecting_event_taxonomy_record_v1(
        event_record_id="EVT_IDENTITY_B",
        classification_status=CLASSIFICATION_STATUS_UNKNOWN,
        event_semantic_class=CLASSIFICATION_STATUS_UNKNOWN,
        ordering_key="1",
        event_digest=_DIGEST,
        mapped_numeric_effect="FORBIDDEN_NOT_ZERO",
        **_identity_kwargs(identity_b),
    )
    with pytest.raises(BoundAccountIdentityContractError) as mix_err:
        assert_same_bound_account_identity_v1(
            left_ref=checkpoint.bound_account_identity_ref,
            left_digest=checkpoint.bound_account_identity_digest,
            right_ref=event.bound_account_identity_ref,
            right_digest=event.bound_account_identity_digest,
        )
    assert "BOUND_ACCOUNT_IDENTITY_MISMATCH_CROSS_ACCOUNT" in str(mix_err.value)
    with pytest.raises(BoundAccountIdentityContractError):
        build_equity_stock_checkpoint_contract_v1(
            checkpoint_id="CKPT_MISSING",
            schema_digest=_DIGEST,
            input_set_digest=_DIGEST_B,
            checkpoint_version="v1",
            bound_account_identity_ref=None,
            bound_account_identity_digest=_DIGEST,
        )
    with pytest.raises(BoundAccountIdentityContractError):
        build_equity_affecting_event_taxonomy_record_v1(
            event_record_id="EVT_MISSING",
            classification_status=CLASSIFICATION_STATUS_UNKNOWN,
            event_semantic_class=CLASSIFICATION_STATUS_UNKNOWN,
            ordering_key="1",
            event_digest=_DIGEST,
            mapped_numeric_effect="FORBIDDEN_NOT_ZERO",
            bound_account_identity_ref="UNKNOWN",
            bound_account_identity_digest=_DIGEST,
        )
    with pytest.raises(BoundAccountIdentityContractError):
        build_fresh_eq_reconciliation_target_contract_v1(
            reconciliation_record_id="EQ_MISSING",
            reconstructed_equity_fact_id="RECON_FACT_A",
            reconstructed_equity_provenance_digest=_DIGEST,
            reconstructed_equity_value_state="PRESENT",
            reconstructed_equity_value="12.50",
            venue_eq_fact_id="VENUE_EQ_FACT_A",
            venue_eq_provenance_digest=_DIGEST_B,
            venue_eq_value_state="PRESENT",
            venue_eq_value="12.50",
            bound_account_identity_ref="",
            bound_account_identity_digest=_DIGEST,
        )


def test_c01_c16_remain_fenced_and_no_source_or_engine() -> None:
    dag = live_admission_gap_dag_v1()
    assert BOUND_ACCOUNT_IDENTITY_PROVEN is True
    assert BOUND_ACCOUNT_IDENTITY_CONTRACT_SCHEMA_PRESENT is True
    assert BOUND_ACCOUNT_IDENTITY_RUNTIME_INSTANCE_PRESENT is False
    assert BOUND_ACCOUNT_CONCRETE_UID_OBSERVED is False
    assert BOUND_ACCOUNT_IDENTITY_FROM_ENV_FORBIDDEN is True
    assert BOUND_ACCOUNT_IDENTITY_FROM_CREDENTIAL_FORBIDDEN is True
    assert BOUND_ACCOUNT_IDENTITY_IMPLICIT_DEFAULT_FORBIDDEN is True
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
    assert LIVE_ENABLED is False
    assert LIVE_ARMED is False
    assert WIRE_SEND_PERMITTED is False
    assert dag["BOUND_ACCOUNT_IDENTITY_PROVEN"] is True
    assert dag["BOUND_ACCOUNT_CONCRETE_UID_OBSERVED"] is False
    assert dag["EARLIEST_OPTION_D_DEPENDENCY"] == "D5_CHECKPOINT_OBSERVATION_ACQUISITION"
    assert EARLIEST_OPTION_D_DEPENDENCY == "D5_CHECKPOINT_OBSERVATION_ACQUISITION"
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


def test_existing_owner_unchanged() -> None:
    assert OWNER == "ops.governed_productive_account_equity_authority_producer_v1"
    assert ACCOUNT_EQUITY_AUTHORITY_OWNER == OWNER
    identity = _identity(identity_id="SYNTHETIC_ACCOUNT_A", account="SYNTHETIC_ACCOUNT_A")
    assert identity.authority_owner == OWNER


def test_runbook_as_consumes_owner_go_without_rewriting_ar_or_protected_surfaces() -> None:
    runbook = RUNBOOK.read_text(encoding="utf-8")
    spec = SPEC_PATH.read_text(encoding="utf-8")
    as_section = _as_section()
    ar_start = runbook.index(AR_HEADING)
    ar_section = runbook[ar_start : runbook.index(AS_HEADING, ar_start)]
    assert "THIS_SLICE=11.2.1.AR" in ar_section
    assert "THIS_SLICE=11.2.1.AS" not in ar_section
    assert "EARLIEST_OPTION_D_DEPENDENCY=D4_BOUND_ACCOUNT_IDENTITY" in ar_section
    assert "OWNER_GO=D4_BOUND_ACCOUNT_IDENTITY_WORKPACKAGE_V1" in as_section
    assert "OWNER_GO_STATUS=CONSUMED" in as_section
    assert "THIS_SLICE=11.2.1.AS.FULL_CORE_D4_BOUND_ACCOUNT_IDENTITY_CONTRACT" in as_section
    assert "BOUND_ACCOUNT_IDENTITY_PROVEN=true" in as_section
    assert "BOUND_ACCOUNT_IDENTITY_CONTRACT_SCHEMA_PRESENT=true" in as_section
    assert "BOUND_ACCOUNT_IDENTITY_RUNTIME_INSTANCE_PRESENT=false" in as_section
    assert "BOUND_ACCOUNT_CONCRETE_UID_OBSERVED=false" in as_section
    assert "BOUND_ACCOUNT_IDENTITY_FROM_ENV_FORBIDDEN=true" in as_section
    assert "BOUND_ACCOUNT_IDENTITY_FROM_CREDENTIAL_FORBIDDEN=true" in as_section
    assert "BOUND_ACCOUNT_IDENTITY_IMPLICIT_DEFAULT_FORBIDDEN=true" in as_section
    assert "D4_BOUND_ACCOUNT_IDENTITY=CONTRACT_PRESENT_AND_REFERENCE_BOUND" in as_section
    assert "EARLIEST_OPTION_D_DEPENDENCY=D5_CHECKPOINT_OBSERVATION_ACQUISITION" in as_section
    assert "SOURCE_SELECTED=false" in as_section
    assert "MAPPING_PROVEN=false" in as_section
    assert "C17_CREATED=false" in as_section
    assert "EVENT_ACQUISITION_CREATED=false" in as_section
    assert "RECONSTRUCTION_ENGINE_CREATED=false" in as_section
    assert "EXISTING_AUTHORITY_OWNER_UNCHANGED=true" in as_section
    assert (
        "ACCOUNT_EQUITY_AUTHORITY_OWNER="
        "ops.governed_productive_account_equity_authority_producer_v1" in as_section
    )
    assert "LIVE_ENABLED=false" in as_section
    assert "LIVE_ARMED=false" in as_section
    assert "WIRE_SEND_PERMITTED=false" in as_section
    assert "MASTER_V2_UNCHANGED=true" in as_section
    assert "DOUBLE_PLAY_UNCHANGED=true" in as_section
    assert "BULL_BEAR_STATE_SWITCH_UNCHANGED=true" in as_section
    assert "TOP20_RANKING_UNIVERSE_UNCHANGED=true" in as_section
    assert "SELF_LEARNING_UNCHANGED=true" in as_section
    assert "FULL_CORE_AUTONOMY_UNCHANGED=true" in as_section
    assert "PROTECTED_SURFACES_UNCHANGED=true" in as_section
    assert "CORE_LOGIC_CHANGE=false" in as_section
    assert "CONSTRUCT_LIVE_EXECUTION_PORT_V1=FORBIDDEN_IN_CAP_11_1" in as_section
    assert "DOCS_TOKEN_FULL_CORE_D4_BOUND_ACCOUNT_IDENTITY_CONTRACT_V1" in spec
    assert "THIS_SLICE=11.2.1.AR" in ar_section
    assert "C17_CREATED=false" in ar_section
