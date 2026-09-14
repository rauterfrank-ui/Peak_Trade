"""Live-critical-path next-blocker bounded workpackage.

Consumes sealed BL remaining-unknown consumption. Historical F12/F13/U05
and F16-F18 remain UNKNOWN. Live KIND_SET is a NEW_CANONICAL_DEFINITION
and stays empty. No GET. GATE_A and GATE_B are not executed.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    KIND_SET_RESOLVED,
    LIVE_ARMED,
    LIVE_ENABLED,
    MS2_AUTHORIZED,
    RAW_EQ_SOURCE_AUTHORITY,
    WIRE_SEND_PERMITTED,
)
from src.ops.full_core_live_path_composition_root_v1.live_admission_gap_dag_v1 import (
    EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.bj_remaining_unknown_kind_semantics_v1 import (
    DECISION_EXCLUDE,
    DECISION_INCLUDE,
    FACT_F12,
    FACT_IDS,
    KIND_SET_EMPTY,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.bk_bj_semantics_consumption_v1 import (
    CANONICAL_PACK_RELPATH as CANONICAL_BL_PACK_RELPATH,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.f12_f13_kind_set_remaining_unknown_pin_and_reopen_gate_v1 import (
    GATE_A_ID,
    GATE_B_ID,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.live_critical_path_next_blocker_bounded_wp1 import (
    CLASS_ALREADY_CLOSED,
    CLASS_DOWNSTREAM,
    CLASS_HISTORICAL,
    CLASS_LIVE_CRITICAL,
    EARLIEST_LIVE_CRITICAL_PATH_BLOCKER,
    EXPECTED_ORIGIN_MAIN_SHA,
    LIVE_CRITICAL_KIND_SET_IDENTITY,
    NEXT_OWNER_GO_REQUIRED,
    OWNER_GO,
    CANONICAL_PACK_RELPATH,
    LiveCriticalPathNextBlockerError,
    build_live_critical_kind_set_boundary_v1,
    build_live_critical_path_item_adjudications_v1,
    execute_live_critical_path_next_blocker_bounded_wp1,
    reject_claimed_live_critical_path_authority_mutation_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.named_remaining_unknown_kind_set_evidence_persist_contract_v1 import (
    DECISION_REMAIN_UNKNOWN,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.package_1_s6_mapping_classification_v1 import (
    verify_manifest_sha256_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
RUNBOOK = REPO_ROOT / "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md"
SPEC_PATH = REPO_ROOT / "docs/ops/specs/FULL_CORE_LIVE_CRITICAL_PATH_NEXT_BLOCKER_BOUNDED_WP1.md"
MOT_PATH = REPO_ROOT / "docs/governance/PEAK_TRADE_MAP_OF_TRUTH.md"
ATLAS_PATH = REPO_ROOT / "docs/system_atlas/entities/catalog.yaml"
BL_HEADING = "11.2.1.BL FULL_CORE_D6_BK_BOUNDED_IMPLEMENTATION"
BM_HEADING = "11.2.1.BM FULL_CORE_LIVE_CRITICAL_PATH_NEXT_BLOCKER"
SEALED_BL = REPO_ROOT / CANONICAL_BL_PACK_RELPATH
CANONICAL_PACK = REPO_ROOT / CANONICAL_PACK_RELPATH
_AS_OF = "2026-09-14T09:00:00Z"


def _bm_section() -> str:
    runbook = RUNBOOK.read_text(encoding="utf-8")
    start = runbook.index(BM_HEADING)
    return runbook[
        start : runbook.index(
            "11.2.1.BN FULL_CORE_LIVE_EQUITY_STOCK_KIND_SET_NEW_CANONICAL_DEFINITION", start
        )
    ]


def _run(tmp_path: Path):
    return execute_live_critical_path_next_blocker_bounded_wp1(
        owner_go=OWNER_GO,
        origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
        sealed_bl_pack=SEALED_BL,
        evidence_root=tmp_path / "live_critical",
        persist_as_of=_AS_OF,
    )


def test_sealed_bl_manifest_verifies() -> None:
    assert verify_manifest_sha256_v1(store_root=SEALED_BL) == 0


def test_owner_go_and_sha_mismatch_fail_closed(tmp_path: Path) -> None:
    with pytest.raises(LiveCriticalPathNextBlockerError, match="OWNER_GO_MISMATCH"):
        execute_live_critical_path_next_blocker_bounded_wp1(
            owner_go="WRONG",
            origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
            sealed_bl_pack=SEALED_BL,
            evidence_root=tmp_path / "live_critical",
            persist_as_of=_AS_OF,
        )
    with pytest.raises(LiveCriticalPathNextBlockerError, match="ORIGIN_MAIN_SHA_MISMATCH"):
        execute_live_critical_path_next_blocker_bounded_wp1(
            owner_go=OWNER_GO,
            origin_main_sha="0" * 40,
            sealed_bl_pack=SEALED_BL,
            evidence_root=tmp_path / "live_critical",
            persist_as_of=_AS_OF,
        )


def test_missing_bl_claims_fail_closes(tmp_path: Path) -> None:
    pack = tmp_path / "empty_pack"
    pack.mkdir()
    lineage = pack / "LINEAGE.json"
    lineage.write_text("{}\n", encoding="utf-8")
    digest = hashlib.sha256(lineage.read_bytes()).hexdigest()
    (pack / "MANIFEST.sha256").write_text(f"{digest}  LINEAGE.json\n", encoding="utf-8")
    with pytest.raises(LiveCriticalPathNextBlockerError, match="BL_CLAIMS_MISSING"):
        execute_live_critical_path_next_blocker_bounded_wp1(
            owner_go=OWNER_GO,
            origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
            sealed_bl_pack=pack,
            evidence_root=tmp_path / "live_critical",
            persist_as_of=_AS_OF,
        )


def test_malformed_bl_claims_fail_closes(tmp_path: Path) -> None:
    pack = tmp_path / "malformed_pack"
    pack.mkdir()
    claims = pack / "claims.json"
    claims.write_text("{not-json\n", encoding="utf-8")
    digest = hashlib.sha256(claims.read_bytes()).hexdigest()
    (pack / "MANIFEST.sha256").write_text(f"{digest}  claims.json\n", encoding="utf-8")
    with pytest.raises(LiveCriticalPathNextBlockerError, match="BL_CLAIMS_MALFORMED"):
        execute_live_critical_path_next_blocker_bounded_wp1(
            owner_go=OWNER_GO,
            origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
            sealed_bl_pack=pack,
            evidence_root=tmp_path / "live_critical",
            persist_as_of=_AS_OF,
        )


@pytest.mark.parametrize(
    "claimed_proof",
    [
        DECISION_INCLUDE,
        DECISION_EXCLUDE,
        "EXECUTE_GATE_A",
        "EXECUTE_GATE_B",
        "INVENT_LIVE_SOURCE_KIND",
        "RECONSTRUCT_HISTORICAL_UNKNOWN",
        "PROMOTE_HISTORICAL_UNKNOWN_TO_LIVE_KIND",
    ],
)
def test_forbidden_authority_mutations_fail_closed(claimed_proof: str) -> None:
    with pytest.raises(LiveCriticalPathNextBlockerError, match="LIVE_CRITICAL_PATH_CANNOT_"):
        reject_claimed_live_critical_path_authority_mutation_v1(
            claimed_proof=claimed_proof,
            fact_id=FACT_F12,
        )


def test_historical_facts_are_not_live_kind_set_members() -> None:
    items = {item.item_id: item for item in build_live_critical_path_item_adjudications_v1()}
    for fact_id in FACT_IDS:
        record = items[fact_id]
        assert record.classification == CLASS_HISTORICAL
        assert record.reconstruct_historical_unknown == "false"
        assert record.live_kind_set_member == "false"
    assert items[GATE_A_ID].classification == CLASS_DOWNSTREAM
    assert items[GATE_B_ID].classification == CLASS_DOWNSTREAM
    assert items["D6_BK_BL_SEMANTICS_CONSUMPTION"].classification == CLASS_ALREADY_CLOSED
    live = items[EARLIEST_LIVE_CRITICAL_PATH_BLOCKER]
    assert live.classification == CLASS_LIVE_CRITICAL


def test_live_kind_set_boundary_is_new_canonical_and_empty() -> None:
    boundary = build_live_critical_kind_set_boundary_v1()
    assert boundary.definition_class == "NEW_CANONICAL_DEFINITION"
    assert boundary.definition_id == LIVE_CRITICAL_KIND_SET_IDENTITY
    assert boundary.live_critical_kind_set == KIND_SET_EMPTY
    assert boundary.live_critical_kind_set_resolved == "false"
    assert boundary.historical_unknown_on_critical_path == "false"
    assert boundary.kinds_invented_this_go == "false"
    assert boundary.ratified_live_source_kinds == "NONE"


def test_sealed_bl_consumption_keeps_historical_unknown_and_empty_live_kind_set(
    tmp_path: Path,
) -> None:
    result = _run(tmp_path)
    assert result.historical_unknown_on_critical_path == "false"
    assert result.live_critical_kind_set == KIND_SET_EMPTY
    assert result.live_critical_kind_set_resolved == "false"
    assert result.earliest_live_critical_path_blocker == EARLIEST_LIVE_CRITICAL_PATH_BLOCKER
    assert result.next_owner_go_required == NEXT_OWNER_GO_REQUIRED
    assert result.venue_get_count == "0"
    assert result.venue_post_count == "0"
    assert result.gate_a_executed == "false"
    assert result.gate_b_executed == "false"
    assert result.kinds_invented_this_go == "false"
    assert result.d6_fully_closed == "false"
    assert result.d7_authorized == "false"
    assert result.ms2_authorized == "false"
    assert KIND_SET_RESOLVED is False
    assert MS2_AUTHORIZED is False
    assert RAW_EQ_SOURCE_AUTHORITY is False
    assert LIVE_ENABLED is False
    assert LIVE_ARMED is False
    assert WIRE_SEND_PERMITTED is False
    assert EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY == (
        "NO_CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING"
    )
    store = Path(result.store_root)
    assert verify_manifest_sha256_v1(store_root=store) == 0
    claims = json.loads((store / "claims.json").read_text(encoding="utf-8"))
    assert claims["BL_CONTRACT_REUSED"] == "true"
    assert claims["MASTER_V2_UNCHANGED"] == "true"
    assert claims["F12_DECISION"] == DECISION_REMAIN_UNKNOWN
    assert claims["HISTORICAL_UNKNOWN_ON_CRITICAL_PATH"] == "false"
    adjudication = json.loads((store / "adjudication_v1.json").read_text(encoding="utf-8"))
    assert adjudication[FACT_F12]["classification"] == CLASS_HISTORICAL
    assert (
        adjudication[EARLIEST_LIVE_CRITICAL_PATH_BLOCKER]["classification"] == CLASS_LIVE_CRITICAL
    )


def test_canonical_pack_matches_executor_and_manifest() -> None:
    assert verify_manifest_sha256_v1(store_root=CANONICAL_PACK) == 0
    expected: dict[str, str] = {}
    for line in (CANONICAL_PACK / "MANIFEST.sha256").read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        digest, name = line.split("  ", 1)
        expected[name] = digest
    actual = {
        path.name
        for path in CANONICAL_PACK.iterdir()
        if path.is_file() and path.name != "MANIFEST.sha256"
    }
    assert set(expected) == actual
    for name, digest in expected.items():
        assert hashlib.sha256((CANONICAL_PACK / name).read_bytes()).hexdigest() == digest
    claims = json.loads((CANONICAL_PACK / "claims.json").read_text(encoding="utf-8"))
    assert claims["LIVE_CRITICAL_KIND_SET"] == KIND_SET_EMPTY
    assert claims["HISTORICAL_UNKNOWN_ON_CRITICAL_PATH"] == "false"
    assert claims["VENUE_GET_COUNT"] == "0"
    assert claims["VENUE_POST_COUNT"] == "0"
    assert claims["KINDS_INVENTED_THIS_GO"] == "false"
    assert claims["EARLIEST_LIVE_CRITICAL_PATH_BLOCKER"] == EARLIEST_LIVE_CRITICAL_PATH_BLOCKER


def test_runbook_bm_and_navigation_persist() -> None:
    spec = SPEC_PATH.read_text(encoding="utf-8")
    mot = MOT_PATH.read_text(encoding="utf-8")
    atlas = ATLAS_PATH.read_text(encoding="utf-8")
    runbook = RUNBOOK.read_text(encoding="utf-8")
    assert BL_HEADING in runbook
    bm_section = _bm_section()
    assert OWNER_GO in bm_section
    assert "THIS_SLICE=11.2.1.BM.FULL_CORE_LIVE_CRITICAL_PATH_NEXT_BLOCKER" in bm_section
    assert "HISTORICAL_UNKNOWN_ON_CRITICAL_PATH=false" in bm_section
    assert "LIVE_CRITICAL_KIND_SET=EMPTY_FAIL_CLOSED" in bm_section
    assert "LIVE_CRITICAL_KIND_SET_RESOLVED=false" in bm_section
    assert "KINDS_INVENTED_THIS_GO=false" in bm_section
    assert "GATE_A_EXECUTED=false" in bm_section
    assert "VENUE_GET_COUNT=0" in bm_section
    assert "D6_FULLY_CLOSED=false" in bm_section
    assert "BL_CONTRACT_REUSED=true" in bm_section
    assert EARLIEST_LIVE_CRITICAL_PATH_BLOCKER in bm_section
    assert "DOCS_TOKEN_FULL_CORE_LIVE_CRITICAL_PATH_NEXT_BLOCKER_BOUNDED_WP1" in spec
    assert "FULL_CORE_LIVE_CRITICAL_PATH_NEXT_BLOCKER_BOUNDED_WP1.md" in mot
    assert "11.2.1.BM FULL_CORE_LIVE_CRITICAL_PATH_NEXT_BLOCKER" in mot
    assert "ATLAS_AUTHORITY=NONE" in atlas
    assert "11.2.1.BM" in atlas
    assert "live_critical_path_next_blocker_bounded_wp1.py" in atlas
