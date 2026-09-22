"""PATH_B durable-UNKNOWN U05 embedding-identity pin tests.

No GET. No POST. No INCLUDE or EXCLUDE. No Path C. Witness branch closed.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    LIVE_ARMED,
    LIVE_ENABLED,
    MS2_AUTHORIZED,
    WIRE_SEND_PERMITTED,
)
from src.ops.full_core_live_path_composition_root_v1.live_admission_gap_dag_v1 import (
    EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.named_remaining_unknown_kind_set_evidence_persist_contract_v1 import (
    DECISION_REMAIN_UNKNOWN,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.package_1_s6_mapping_classification_v1 import (
    verify_manifest_sha256_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.u05_durable_unknown_embedding_identity_pin_v1 import (
    BLOCKER_ID,
    CANONICAL_PACK_RELPATH,
    NEXT_OWNER_GO,
    NEXT_PRODUCTIVE_NODE,
    OWNER_GO,
    SELECTED_PATH,
    U05DurableUnknownEmbeddingIdentityPinError,
    execute_u05_durable_unknown_embedding_identity_pin_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
SOURCE_PATH = (
    "src/ops/governed_productive_account_equity_authority_producer_v1/"
    "u05_durable_unknown_embedding_identity_pin_v1.py"
)
SPEC_PATH = REPO_ROOT / "docs/ops/specs/FULL_CORE_U05_DURABLE_UNKNOWN_EMBEDDING_IDENTITY_PIN_V1.md"
MOT_PATH = REPO_ROOT / "docs/governance/PEAK_TRADE_MAP_OF_TRUTH.md"
ATLAS_PATH = REPO_ROOT / "docs/system_atlas/entities/catalog.yaml"
RUNBOOK = REPO_ROOT / "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md"
CANONICAL_PACK = REPO_ROOT / CANONICAL_PACK_RELPATH
CE_HEADING = "11.2.1.CE FULL_CORE_U05_DURABLE_UNKNOWN_EMBEDDING_IDENTITY_PIN"
EXPECTED_SHA = "d3dbac35af5c9cfc3bc1a4087aeecc66950c58c6"


def test_standing_pins_remain_fail_closed() -> None:
    assert LIVE_ENABLED is True
    assert LIVE_ARMED is True
    assert WIRE_SEND_PERMITTED is True
    assert MS2_AUTHORIZED is False
    assert EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY == (
        "CURRENT_PRODUCTIVE_29P_RISK_CAPITAL_SURFACE_BOUND_VALUE_REQUIRES_FRESH_TRUSTED_GET"
    )


def test_wrong_owner_go_fail_closed(tmp_path: Path) -> None:
    with pytest.raises(U05DurableUnknownEmbeddingIdentityPinError, match="OWNER_GO_MISMATCH"):
        execute_u05_durable_unknown_embedding_identity_pin_v1(
            owner_go="WRONG",
            origin_main_sha=EXPECTED_SHA,
            evidence_root=tmp_path / "pack",
        )


def test_path_a_is_not_this_slice(tmp_path: Path) -> None:
    with pytest.raises(
        U05DurableUnknownEmbeddingIdentityPinError, match="SELECTED_PATH_NOT_PATH_B"
    ):
        execute_u05_durable_unknown_embedding_identity_pin_v1(
            owner_go=OWNER_GO,
            origin_main_sha=EXPECTED_SHA,
            evidence_root=tmp_path / "pack",
            selected_path="PATH_A",
        )


def test_execute_pins_durable_unknown_without_get(tmp_path: Path) -> None:
    store = tmp_path / "pack"
    result = execute_u05_durable_unknown_embedding_identity_pin_v1(
        owner_go=OWNER_GO,
        origin_main_sha=EXPECTED_SHA,
        evidence_root=store,
    )
    claims = json.loads((store / "claims.json").read_text(encoding="utf-8"))
    tree = json.loads((store / "downstream_dependency_tree_v1.json").read_text(encoding="utf-8"))
    assert result.selected_path == SELECTED_PATH
    assert result.non_algebraic_embedding_identity == "DURABLE_UNKNOWN"
    assert result.u05_decision_after == DECISION_REMAIN_UNKNOWN
    assert result.further_u05_witness_acquisition == "STOPPED"
    assert result.witness_branch_closed == "true"
    assert result.authorized_get_count == "0"
    assert result.actual_get_count == "0"
    assert result.post_count == "0"
    assert claims["NON_ALGEBRAIC_EMBEDDING_IDENTITY"] == "DURABLE_UNKNOWN"
    assert claims["U05_DECISION_AFTER"] == DECISION_REMAIN_UNKNOWN
    assert claims["PATH_C_CLOSEOUT"] == "false"
    assert claims["INTEREST_ACCRUED_GET_COUNT_REMAINS"] == "1"
    assert claims["NEXT_PRODUCTIVE_NODE"] == NEXT_PRODUCTIVE_NODE
    assert claims["NEXT_OWNER_GO_REQUIRED"] == NEXT_OWNER_GO
    assert "INCLUDE" not in claims["U05_DECISION_AFTER"]
    assert "EXCLUDE" not in claims["U05_DECISION_AFTER"]
    assert tree["next_productive_classification"] == "REQUIRES_NEW_AUTHORITY"
    assert verify_manifest_sha256_v1(store_root=store) == 0


def test_source_does_not_get_or_post() -> None:
    source = (REPO_ROOT / SOURCE_PATH).read_text(encoding="utf-8")
    assert "urllib" not in source
    assert "requests" not in source
    assert "GET_ENDPOINTS_PRIVATE" not in source
    assert "/api/v5/" not in source
    assert "max_retries" not in source


def test_canonical_pack_sealed() -> None:
    claims = json.loads((CANONICAL_PACK / "claims.json").read_text(encoding="utf-8"))
    assert claims["OWNER_GO"] == OWNER_GO
    assert claims["SELECTED_PATH"] == "PATH_B"
    assert claims["NON_ALGEBRAIC_EMBEDDING_IDENTITY"] == "DURABLE_UNKNOWN"
    assert claims["U05_DECISION_AFTER"] == DECISION_REMAIN_UNKNOWN
    assert claims["FURTHER_U05_EMBEDDING_WITNESS_ACQUISITION"] == "STOPPED"
    assert claims["WITNESS_BRANCH_CLOSED"] == "true"
    assert claims["PATH_C_CLOSEOUT"] == "false"
    assert claims["ACTUAL_GET_COUNT"] == "0"
    assert claims["POST_COUNT"] == "0"
    assert claims["BLOCKER_ID"] == BLOCKER_ID
    assert verify_manifest_sha256_v1(store_root=CANONICAL_PACK) == 0


def test_runbook_ce_persists_path_b() -> None:
    spec = SPEC_PATH.read_text(encoding="utf-8")
    mot = MOT_PATH.read_text(encoding="utf-8")
    atlas = ATLAS_PATH.read_text(encoding="utf-8")
    runbook = RUNBOOK.read_text(encoding="utf-8")
    start = runbook.index(CE_HEADING)
    ce_section = runbook[start : runbook.index("## 11.3 Autonomy state model", start)]
    assert OWNER_GO in ce_section
    assert "THIS_SLICE=11.2.1.CE.FULL_CORE_U05_DURABLE_UNKNOWN_EMBEDDING_IDENTITY_PIN" in ce_section
    assert "SELECTED_PATH=PATH_B" in ce_section
    assert "NON_ALGEBRAIC_EMBEDDING_IDENTITY=DURABLE_UNKNOWN" in ce_section
    assert "U05_DECISION_AFTER=REMAIN_UNKNOWN" in ce_section
    assert "FURTHER_U05_EMBEDDING_WITNESS_ACQUISITION=STOPPED" in ce_section
    assert "WITNESS_BRANCH_CLOSED=true" in ce_section
    assert "PATH_C_CLOSEOUT=false" in ce_section
    assert "ACTUAL_GET_COUNT=0" in ce_section
    assert "INTEREST_ACCRUED_GET_COUNT_REMAINS=1" in ce_section
    assert "U06_DECISION_UNCHANGED=REMAIN_UNKNOWN" in ce_section
    assert BLOCKER_ID in ce_section
    assert NEXT_OWNER_GO in ce_section
    assert "CURRENT_CANONICAL_SECTION=11.2.1.CE" in ce_section
    assert "DOCS_TOKEN_FULL_CORE_U05_DURABLE_UNKNOWN_EMBEDDING_IDENTITY_PIN_V1" in spec
    assert "FULL_CORE_U05_DURABLE_UNKNOWN_EMBEDDING_IDENTITY_PIN_V1.md" in mot
    assert CE_HEADING in mot
    assert "11.2.1.CE" in atlas
    assert "u05_durable_unknown_embedding_identity_pin_v1.py" in atlas
    assert "ATLAS_AUTHORITY=NONE" in atlas
