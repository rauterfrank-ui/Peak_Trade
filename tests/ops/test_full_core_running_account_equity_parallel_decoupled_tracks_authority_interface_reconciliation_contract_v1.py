"""Parallel-decoupled tracks Authority/Interface/Reconciliation contract tests.

Docs/contract-only. No mapping mint. No sizing mint. No runtime mutation.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    MAPPING_PROVEN,
    OBSERVATION_IS_NOT_AUTHORITY as ROOT_OBSERVATION_IS_NOT_AUTHORITY,
)
from src.ops.full_core_live_path_composition_root_v1.live_admission_gap_dag_v1 import (
    EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.constants_v1 import (
    CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING,
    CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_SOURCE_STATUS,
    GOVERNED_PRODUCER_CREATED,
    LEGACY_RECONSTRUCTION_REQUIRED_FOR_LIVE,
    MAPPED_TO_RUNNING_ACCOUNT_EQUITY_AVAILABLE_FOR_SIZING,
    RECONCILIATION_CONTRACT_CREATED,
    SOURCE_SELECTED,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.running_account_equity_parallel_decoupled_tracks_authority_interface_reconciliation_contract_v1 import (
    ACCOUNT_EQUITY_AUTHORITY_CHAIN_CLOSED,
    ACCOUNT_EQUITY_AUTHORITY_OWNER,
    AUTHORITY_MODEL,
    DIMENSION_ID,
    NEXT_OWNER_GO_REQUIRED,
    NEXT_UNRESOLVED_DEPENDENCY,
    OWNER_DECISION_1,
    OWNER_GO,
    PARALLEL_DECOUPLED_TRACKS_AUTHORITY_INTERFACE_RECONCILIATION_CONTRACT_CREATED,
    ParallelDecoupledTracksAuthorityInterfaceReconciliationContractError,
    RECONCILIATION_MAY_NOT_MINT_AUTHORITY_BY_AGREEMENT,
    SOURCE_TO_SEMANTIC_MAPPING_AUTHORIZED_BY_THIS_WP,
    SIZING_MINT_AUTHORIZED_BY_THIS_WP,
    build_running_account_equity_parallel_decoupled_tracks_authority_interface_reconciliation_contract_v1,
    reject_authority_mint_by_reconciliation_agreement_v1,
    reject_silent_track_substitution_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
RUNBOOK = REPO_ROOT / "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md"
SPEC = (
    REPO_ROOT
    / "docs/ops/specs"
    / "FULL_CORE_RUNNING_ACCOUNT_EQUITY_PARALLEL_DECOUPLED_TRACKS_AUTHORITY_INTERFACE_RECONCILIATION_CONTRACT_V1.md"
)
MOT = REPO_ROOT / "docs/governance/PEAK_TRADE_MAP_OF_TRUTH.md"


def test_contract_builds_and_preserves_pins() -> None:
    contract = build_running_account_equity_parallel_decoupled_tracks_authority_interface_reconciliation_contract_v1(
        contract_id="PARALLEL_DECOUPLED_TRACKS_FIXTURE_001",
    )
    assert contract.owner_decision_1 == "C"
    assert contract.authority_model == AUTHORITY_MODEL == "PARALLEL_DECOUPLED_TRACKS"
    assert contract.dimension_id == DIMENSION_ID
    assert contract.owner_go == OWNER_GO
    assert contract.parallel_decoupled_tracks_contract_created is True
    assert PARALLEL_DECOUPLED_TRACKS_AUTHORITY_INTERFACE_RECONCILIATION_CONTRACT_CREATED is True
    assert contract.option_d_reconstruction_reconciliation_contract_created is False
    assert RECONCILIATION_CONTRACT_CREATED is False
    assert contract.account_equity_authority_owner == "UNRESOLVED"
    assert ACCOUNT_EQUITY_AUTHORITY_OWNER == "UNRESOLVED"
    assert contract.account_equity_authority_chain_closed is False
    assert ACCOUNT_EQUITY_AUTHORITY_CHAIN_CLOSED is False
    assert contract.canonically_valid_account_equity_source_mapping is True
    assert CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING is True
    assert contract.source_selected is True
    assert SOURCE_SELECTED is True
    assert contract.legacy_reconstruction_required_for_live is False
    assert LEGACY_RECONSTRUCTION_REQUIRED_FOR_LIVE is False
    assert contract.mapping_proven is True
    assert MAPPING_PROVEN is True
    assert contract.mapped_to_running_account_equity_available_for_sizing is True
    assert MAPPED_TO_RUNNING_ACCOUNT_EQUITY_AVAILABLE_FOR_SIZING is True
    assert contract.governed_producer_created is False
    assert GOVERNED_PRODUCER_CREATED is False
    assert contract.source_to_semantic_mapping_authorized_by_this_wp is False
    assert SOURCE_TO_SEMANTIC_MAPPING_AUTHORIZED_BY_THIS_WP is False
    assert contract.sizing_mint_authorized_by_this_wp is False
    assert SIZING_MINT_AUTHORIZED_BY_THIS_WP is False
    assert contract.reconciliation_may_not_mint_authority_by_agreement is True
    assert RECONCILIATION_MAY_NOT_MINT_AUTHORITY_BY_AGREEMENT is True
    assert contract.observation_is_not_authority is True
    assert ROOT_OBSERVATION_IS_NOT_AUTHORITY is True
    assert contract.next_unresolved_dependency == NEXT_UNRESOLVED_DEPENDENCY
    assert EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY == (
        "CURRENT_PRODUCTIVE_29P_RISK_CAPITAL_SURFACE_BOUND_VALUE_REQUIRES_FRESH_TRUSTED_GET"
    )
    assert contract.next_owner_go_required == NEXT_OWNER_GO_REQUIRED


def test_reject_silent_substitution_and_agreement_mint() -> None:
    with pytest.raises(
        ParallelDecoupledTracksAuthorityInterfaceReconciliationContractError,
        match="SILENT_EQUIVALENCE_OR_SUBSTITUTION_FORBIDDEN",
    ):
        reject_silent_track_substitution_v1(
            claimed_equivalence={
                "left": "availEq",
                "right": "RUNNING_ACCOUNT_EQUITY_AVAILABLE_FOR_SIZING",
            }
        )
    with pytest.raises(
        ParallelDecoupledTracksAuthorityInterfaceReconciliationContractError,
        match="SILENT_EQUIVALENCE_OR_SUBSTITUTION_FORBIDDEN",
    ):
        reject_silent_track_substitution_v1(
            claimed_equivalence={"left": "eq", "right": "reconstructed_equity"}
        )
    reject_authority_mint_by_reconciliation_agreement_v1(agreement=False)
    with pytest.raises(
        ParallelDecoupledTracksAuthorityInterfaceReconciliationContractError,
        match="RECONCILIATION_MAY_NOT_MINT_AUTHORITY_BY_AGREEMENT",
    ):
        reject_authority_mint_by_reconciliation_agreement_v1(agreement=True)


def test_runbook_spec_and_mot_persist() -> None:
    runbook = RUNBOOK.read_text(encoding="utf-8")
    spec = SPEC.read_text(encoding="utf-8")
    mot = MOT.read_text(encoding="utf-8")

    assert OWNER_GO in runbook
    assert "OWNER_DECISION_1=C" in runbook
    assert "AUTHORITY_MODEL=PARALLEL_DECOUPLED_TRACKS" in runbook
    assert (
        "PARALLEL_DECOUPLED_TRACKS_AUTHORITY_INTERFACE_RECONCILIATION_CONTRACT_CREATED=true"
        in runbook
    )
    assert "RECONCILIATION_CONTRACT_CREATED=false" in runbook
    assert "ACCOUNT_EQUITY_AUTHORITY_OWNER=UNRESOLVED" in runbook
    assert "CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING=false" in runbook
    assert (
        "OWNER_GO_RATIFY_SOURCE_TO_SEMANTIC_MAPPING_AND_BIND_AVAILABLE_FOR_SIZING_"
        "PRODUCER_UNDER_PARALLEL_DECOUPLED_TRACKS_V1"
    ) in runbook
    assert "CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING=true" in runbook
    assert "LEGACY_RECONSTRUCTION_REQUIRED_FOR_LIVE=false" in runbook
    assert "SOURCE_TO_SEMANTIC_MAPPING_AUTHORIZED_BY_THIS_WP=false" in runbook
    assert "SIZING_MINT_AUTHORIZED_BY_THIS_WP=false" in runbook
    assert "QUARANTINE_OR_PR_6714_USED_AS_AUTHORITY=false" in runbook
    assert "CORE_MV2_DP_CHANGED=false" in runbook
    assert "N5_UNAUTHORIZED=true" in runbook
    assert NEXT_OWNER_GO_REQUIRED in runbook
    assert (
        "DOCS_TOKEN_FULL_CORE_RUNNING_ACCOUNT_EQUITY_PARALLEL_DECOUPLED_TRACKS_"
        "AUTHORITY_INTERFACE_RECONCILIATION_CONTRACT_V1"
    ) in spec
    assert "OWNER_DECISION_1=C" in spec
    assert "AUTHORITY_MODEL=PARALLEL_DECOUPLED_TRACKS" in spec
    assert (
        "FULL_CORE_RUNNING_ACCOUNT_EQUITY_PARALLEL_DECOUPLED_TRACKS_"
        "AUTHORITY_INTERFACE_RECONCILIATION_CONTRACT_V1.md"
    ) in mot
    assert (
        "RUNNING_ACCOUNT_EQUITY_PARALLEL_DECOUPLED_TRACKS_CONTRACT_ROLE=NAVIGATION_POINTER_ONLY"
    ) in mot
