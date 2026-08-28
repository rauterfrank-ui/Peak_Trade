"""Federated scoped completeness policy invariants.

Docs/persistence contract checks only. Does not authorize Live, Testnet,
Canary, flatten execute, credentials, or canonical mutation. Does not
create a domain or relation ontology.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Mapping

REPO_ROOT = Path(__file__).resolve().parents[2]
PERSISTENCE = REPO_ROOT / "docs" / "forensics" / "persistence"
SCOPING = PERSISTENCE / "FORENSIC_COMPLETENESS_SCOPING_CONTRACT_V1.md"
OWNER_DECISION = (
    PERSISTENCE
    / "inventories"
    / "P6_FEDERATED_SCOPED_COMPLETENESS_POLICY_OWNER_DECISION_OBSERVATION_V1.json"
)
L0 = PERSISTENCE / "registries" / "FEDERATED_SOURCE_SURFACE_REGISTRY_V1.md"
L2 = PERSISTENCE / "registries" / "INFORMATION_OBJECT_REFERENCE_REGISTRY_V1.md"
L4 = PERSISTENCE / "registries" / "CURRENT_STATE_PROJECTION_V1.md"
SET_REGISTER = PERSISTENCE / "registries" / "P6_5189_SET_AND_UNIVERSE_REGISTER_V1.json"
ENTRYPOINT = PERSISTENCE / "FEDERATED_ENTRYPOINT_MAINTENANCE_CONTRACT_V1.md"
P1_CONTRACT = PERSISTENCE / "inventories" / "P1_REPO_FORENSIC_TREES_FILE_INVENTORY_V1.contract.json"
CROSS_FACTS = PERSISTENCE / "inventories" / "CROSS_CORPUS_RELATION_FACTS_V1.json"
HISTORICAL_OBS = (
    PERSISTENCE / "inventories" / "P6_Z2CL_OD_01_08_RECONSTRUCTION_DELTA_OBSERVATION_V1.json",
    PERSISTENCE
    / "inventories"
    / "P6_Z2CL_COMPLETENESS_PRECONDITION_AND_CLOSED_UNIVERSE_EXCLUSION_GAP_OBSERVATION_V1.json",
    PERSISTENCE
    / "inventories"
    / "P6_Z2CL_SCHEMA_NEGATIVE_CAPABILITY_AND_CENSUS_LINEAGE_OBSERVATION_V1.json",
    PERSISTENCE
    / "inventories"
    / "P6_Z2CL_IDENTITY_AND_HEADER_GAP_ADJUDICATION_OBSERVATION_V1.json",
)
ALLOWED_DOMAIN_KEYS = frozenset({"set_id", "SOURCE_SURFACE_ID", "INFORMATION_OBJECT_ID"})
ALLOWED_TEMPORAL_ROLES = frozenset({"snapshot", "live_instant", "historical_token", "current"})
ALLOWED_LAYER_IDENTITIES = frozenset(
    {
        "LAYER_1",
        "LAYER_2",
        "LAYER_3",
        "origin/main",
        "local_committed_HEAD",
        "dirty_operator_worktree",
    }
)
DIRTY_LAYERS = frozenset({"LAYER_3", "dirty_operator_worktree"})


def _read(path: Path) -> str:
    assert path.is_file(), f"missing persistence path: {path}"
    return path.read_text(encoding="utf-8")


def _load_json(path: Path) -> Any:
    return json.loads(_read(path))


def evaluate_completeness_claim(claim: Mapping[str, Any]) -> str:
    """Test-local well-formedness check from FORENSIC_COMPLETENESS_SCOPING_CONTRACT_V1.

    Missing named domain, temporal role, or layer identity is fail-closed.
    This helper is not a new ontology and does not close any universe.
    """

    named_domain_id = claim.get("named_domain_id")
    named_domain_key = claim.get("named_domain_key")
    temporal_role = claim.get("temporal_role")
    layer_identity = claim.get("layer_identity")
    if not named_domain_id or named_domain_key not in ALLOWED_DOMAIN_KEYS:
        return "FAIL_CLOSED"
    if temporal_role not in ALLOWED_TEMPORAL_ROLES:
        return "FAIL_CLOSED"
    if layer_identity not in ALLOWED_LAYER_IDENTITIES:
        return "FAIL_CLOSED"
    claimed_origin_main = bool(claim.get("supports_origin_main_completeness"))
    if claimed_origin_main and layer_identity in DIRTY_LAYERS:
        return "FAIL_CLOSED"
    return "WELL_FORMED"


def apply_stop_result(result: Mapping[str, Any]) -> dict[str, Any]:
    """Stop/no-hit without exhaustion evidence must not prove closed universe."""

    closed = bool(result.get("closed_universe_proven"))
    exhausted = bool(result.get("source_universe_exhausted"))
    stop = bool(result.get("stop"))
    no_hit = bool(result.get("no_hit"))
    exhaustion_criterion = result.get("exhaustion_criterion")
    exhaustion_evidence = result.get("exhaustion_evidence")
    if stop or no_hit:
        if not (exhaustion_criterion and exhaustion_evidence):
            closed = False
            exhausted = False
    return {
        "closed_universe_proven": closed,
        "source_universe_exhausted": exhausted,
    }


def test_completeness_claim_without_named_domain_fails() -> None:
    assert (
        evaluate_completeness_claim(
            {
                "temporal_role": "snapshot",
                "layer_identity": "LAYER_1",
            }
        )
        == "FAIL_CLOSED"
    )
    assert (
        evaluate_completeness_claim(
            {
                "named_domain_id": "SET-P1-REPO-FORENSIC-TREES",
                "named_domain_key": "set_id",
                "temporal_role": "snapshot",
                "layer_identity": "LAYER_1",
            }
        )
        == "WELL_FORMED"
    )
    contract = _read(SCOPING)
    assert "NO_NAMED_DOMAIN_ID=FAIL_CLOSED" in contract
    assert "GLOBAL_FORENSIC_CLOSED_WORLD=false" in contract
    assert (
        "COMPLETENESS_CLAIM_REQUIRED_FIELDS=named_domain_id,temporal_role,layer_identity"
        in contract
    )


def test_l0_known_sources_are_not_global_census() -> None:
    l0 = _read(L0)
    assert "L0_IS_REQUIRED_START_SET=true" in l0
    assert "L0_IS_GLOBAL_CENSUS=false" in l0
    assert "L0_IS_SOURCE_UNIVERSE_EXHAUSTION_PROOF=false" in l0
    assert "GLOBAL_SOURCE_UNIVERSE_EXHAUSTION_PROVEN=false" in l0
    assert "UNLISTED_SOURCE_IS_NOT_AUTOMATICALLY_ABSENT=true" in l0
    ss_ids = re.findall(r"^\| (SS-\d+) \|", l0, flags=re.MULTILINE)
    assert ss_ids == [f"SS-{i:02d}" for i in range(1, 15)]
    assert "SS-10_REMAINS_UNRESOLVED=true" in l0
    assert "SS-10_CONVERTED_TO_EMPTY_OR_ABSENT=false" in l0


def test_byte_identical_pairs_keep_dual_source_identity() -> None:
    facts = _load_json(CROSS_FACTS)
    pairs = facts["P5_DOCUMENTS_PEAK_TRADE_FORENSICS_VS_REPO"]["byte_identical"]
    assert len(pairs) == 15
    for pair in pairs:
        assert pair["relation"] == "BYTE_IDENTICAL"
        assert pair["SOURCE_IDENTITY_MERGED"] is False
        assert pair["p5_locators"]
        assert pair["repo_locators"]
        assert pair["p5_locators"] != pair["repo_locators"]
    contract = _read(SCOPING)
    assert "BYTE_IDENTICAL_DOES_NOT_MERGE_SOURCE_IDENTITY=true" in contract
    assert "REPO_EXTERNAL_UNION_CENSUS_DOMAIN=false" in contract
    assert "CROSS_CORPUS_P5_REPO_BYTE_IDENTICAL_SHA_RECORDS=15" in contract


def test_count_5185_not_equal_5189_not_equal_5190() -> None:
    contract = _read(SCOPING)
    l0 = _read(L0)
    l4 = _read(L4)
    sets = _load_json(SET_REGISTER)
    assert "5185_EQUALS_5189=false" in contract
    assert "5189_EQUALS_5190=false" in contract
    assert "5185_EQUALS_5190=false" in contract
    assert "5185_EQUALS_5189_EQUALS_5190=false" in l0
    assert "5185≠5189≠5190" in l4
    assert sets["COUNT_VALUES_NORMALIZED"] is False
    assert sets["COUNTS_5185_5189_5190_REMAIN_UNCOLLAPSED"] is True
    assert sets["COUNT_PER_NAMED_DOMAIN"] is True
    assert sets["GLOBAL_NORMALIZED_COUNT"] is False


def test_count_16_not_equal_22_not_equal_23() -> None:
    l4 = _read(L4)
    contract = _read(SCOPING)
    assert "PROJECTED_SUBJECT_COUNT=16" in l4
    assert "DEDICATED_L2_IO_HEADING_COUNT_AFTER_THIS_MAINTENANCE=22" in l4
    assert "SUBJECT_ID_HEADING_COUNT_INCLUDING_live_GFU_census_FACET=23" in l4
    assert "COUNT_16_NOT_COLLAPSED_ONTO_22_OR_23=true" in l4
    assert "PROJECTED_SUBJECT_COUNT_16_EQUALS_L2_IO_HEADING_COUNT_22=false" in contract
    assert "L2_IO_HEADING_COUNT_22_EQUALS_SUBJECT_ID_HEADING_COUNT_23=false" in contract
    assert "PROJECTED_SUBJECT_COUNT_16_EQUALS_SUBJECT_ID_HEADING_COUNT_23=false" in contract


def test_p1_129_is_not_live_census() -> None:
    p1 = _load_json(P1_CONTRACT)
    contract = _read(SCOPING)
    assert p1["inventory_record_count"] == 129
    assert p1["counts_are_live_census"] is False
    assert "P1_MEMBER_COUNT=129" in contract
    assert "P1_COUNT_IS_DISCOVERY_SNAPSHOT_NOT_LIVE_TREE_CENSUS=true" in contract
    assert "SNAPSHOT_COMPLETENESS_IS_NOT_LIVE_EXHAUSTION=true" in contract


def test_dirty_worktree_cannot_support_origin_main_completeness() -> None:
    contract = _read(SCOPING)
    assert "DIRTY_WORKTREE_IS_OWN_LAYER=true" in contract
    assert "DIRTY_WORKTREE_IS_NOT_ORIGIN_MAIN=true" in contract
    assert (
        "UNBOUND_DIRTY_FILES_ARE_NOT_MEMBERS_OF_ORIGIN_MAIN_COMPLETENESS_DOMAINS=true" in contract
    )
    assert (
        evaluate_completeness_claim(
            {
                "named_domain_id": "SS-03",
                "named_domain_key": "SOURCE_SURFACE_ID",
                "temporal_role": "current",
                "layer_identity": "LAYER_3",
                "supports_origin_main_completeness": True,
            }
        )
        == "FAIL_CLOSED"
    )
    l4 = _read(L4)
    assert "DIRTY_WORKTREE_PROMOTED_TO_ORIGIN_MAIN" not in l4


def test_stop_without_exhaustion_evidence_cannot_prove_closed_universe() -> None:
    contract = _read(SCOPING)
    decision = _load_json(OWNER_DECISION)
    sets = _load_json(SET_REGISTER)
    applied = apply_stop_result(
        {
            "stop": True,
            "closed_universe_proven": True,
            "source_universe_exhausted": True,
        }
    )
    assert applied["closed_universe_proven"] is False
    assert applied["source_universe_exhausted"] is False
    assert "STOP_IS_NOT_EXHAUSTION=true" in contract
    assert "POLICY_ALONE_MUST_NOT_SET_CLOSED_UNIVERSE_PROVEN=true" in contract
    assert "POLICY_ALONE_MUST_NOT_SET_SOURCE_UNIVERSE_EXHAUSTED=true" in contract
    assert decision["closed_universe_status"]["CLOSED_UNIVERSE_PROVEN"] is False
    assert decision["closed_universe_status"]["SOURCE_UNIVERSE_EXHAUSTED"] is False
    assert all(item["closed_universe_proven"] is False for item in sets["sets"])
    assert sets["POLICY_ALONE_MUST_NOT_SET_CLOSED_UNIVERSE_PROVEN"] is True
    entrypoint = _read(ENTRYPOINT)
    assert "POLICY_ALONE_MUST_NOT_SET_CLOSED_UNIVERSE_PROVEN=true" in entrypoint


def test_no_hit_is_not_exhaustion() -> None:
    applied = apply_stop_result(
        {
            "no_hit": True,
            "closed_universe_proven": True,
            "source_universe_exhausted": True,
        }
    )
    assert applied["closed_universe_proven"] is False
    assert applied["source_universe_exhausted"] is False
    assert "NO_HIT_IS_NOT_EXHAUSTION=true" in _read(SCOPING)


def test_p2_unknown_is_not_empty_or_absent() -> None:
    facts = _load_json(CROSS_FACTS)
    p2 = facts["P2_OWNER_NAMED_PEAK_TRADE_FORENSIK"]
    l2 = _read(L2)
    contract = _read(SCOPING)
    l0 = _read(L0)
    assert p2["status"] == "NOT_UNIQUELY_RESOLVED"
    assert p2["P2_FILE_COUNT"] == "UNKNOWN"
    assert p2["P2_EMPTY_INFERRED_FROM_UNRESOLVED_PATH"] is False
    assert "CURRENT_KNOWN_STATUS=NOT_UNIQUELY_RESOLVED; content UNKNOWN" in l2
    assert "P2_UNRESOLVED_IS_NOT_P2_EMPTY=true" in contract
    assert "P2_EMPTY_INFERRED_FROM_UNRESOLVED_PATH=false" in contract
    assert "P2_CORPUS_ABSENT=false" in contract
    assert "P2_UNRESOLVED_IS_NOT_P2_EMPTY=true" in l0
    assert "SS-10_CONVERTED_TO_EMPTY_OR_ABSENT=false" in l0


def test_scoped_exclusions_are_not_closed_universe_exclusions() -> None:
    precondition = _load_json(HISTORICAL_OBS[1])
    contract = _read(SCOPING)
    gaps = precondition["cp_03_no_closed_universe_exclusion_contract"]
    assert gaps["CLOSED_UNIVERSE_EXCLUSIONS_COUNT"] == 0
    assert gaps["EXPLICIT_SCOPED_EXCLUSIONS_ARE_NOT_CLOSED_UNIVERSE_EXCLUSIONS"] is True
    assert "EXPLICIT_SCOPED_EXCLUSIONS_ARE_NOT_CLOSED_UNIVERSE_EXCLUSIONS=true" in contract
    l4 = _read(L4)
    assert "CLOSED_UNIVERSE_EXCLUSIONS_CONTRACT_FOUND=false" in l4


def test_historical_literal_48_is_not_operative_member_count() -> None:
    contract = _read(SCOPING)
    decision = _load_json(OWNER_DECISION)
    reconstruction = _load_json(HISTORICAL_OBS[0])
    schema_nc = _load_json(HISTORICAL_OBS[2])
    assert "AUDIT_DECLARED_UNIVERSE_CENSUS_COUNT=48" in contract
    assert "CENSUS_48_STATUS=UNRESOLVED_HISTORICAL_ASSERTION" in contract
    assert "CENSUS_48_OPERATIONAL_COUNT=false" in contract
    assert "CENSUS_48_FORMULA_INVENTED=false" in contract
    assert "CENSUS_48_COUNT_FORMULA=UNPROVEN" in contract
    census = decision["census_48_treatment"]
    assert census["AUDIT_DECLARED_UNIVERSE_CENSUS_COUNT"] == 48
    assert census["CENSUS_48_STATUS"] == "UNRESOLVED_HISTORICAL_ASSERTION"
    assert census["CENSUS_48_FORMULA_INVENTED"] is False
    assert census["CENSUS_48_OPERATIONAL_COUNT"] is False
    assert census["CENSUS_48_OPERATIONALIZED"] is False
    assert census["CENSUS_48_COUNT_FORMULA"] == "UNPROVEN"
    assert reconstruction["count_hard_block_preserved_open"]["SOURCE_BOUND_LINEAGE_FOR_48"] == (
        "UNPROVEN"
    )
    assert schema_nc["count_hard_block_preserved_open"]["AUDIT_DECLARED_UNIVERSE_CENSUS_COUNT"] == (
        48
    )
    changed = "\n".join(
        [
            _read(SCOPING),
            json.dumps(decision, sort_keys=True),
            _read(L0),
            _read(L2),
            _read(L4),
            json.dumps(_load_json(SET_REGISTER), sort_keys=True),
            _read(ENTRYPOINT),
        ]
    )
    assert re.search(r"member_count\s*[:=]\s*48\b", changed) is None
    assert re.search(r"(?<![A-Z_0-9])48\s*=\s*[0-9+\-]", changed) is None


def test_temporal_role_required_on_new_completeness_claims() -> None:
    assert (
        evaluate_completeness_claim(
            {
                "named_domain_id": "IO-P6GRAPH",
                "named_domain_key": "INFORMATION_OBJECT_ID",
                "layer_identity": "LAYER_1",
            }
        )
        == "FAIL_CLOSED"
    )
    contract = _read(SCOPING)
    entrypoint = _read(ENTRYPOINT)
    assert "TEMPORAL_ROLE_ALLOWED=snapshot|live_instant|historical_token|current" in contract
    assert "COMPLETENESS_CLAIM_REQUIRES_TEMPORAL_ROLE=true" in entrypoint
    assert "SNAPSHOT_COMPLETENESS_IS_NOT_LIVE_EXHAUSTION=true" in contract


def test_owner_decision_bundle_is_source_bound_and_does_not_rewrite_history() -> None:
    decision = _load_json(OWNER_DECISION)
    selected = decision["owner_selected_decisions"]
    assert selected["OD_01_SELECTED"] == "A_SCOPED_OPEN_WORLD_DEFAULT"
    assert selected["OD_02_SELECTED"] == "A_L0_IS_REQUIRED_START_SET_NOT_CENSUS"
    assert selected["OD_03_SELECTED"] == "A_NO_UNION_CENSUS_DOMAIN"
    assert selected["OD_04_SELECTED"] == "A_COUNT_PER_NAMED_DOMAIN"
    assert selected["OD_05_SELECTED"] == "A_EXPLICIT_TEMPORAL_ROLE_REQUIRED"
    assert selected["OD_06_SELECTED"] == "A_LAYER_3_FAIL_CLOSED_NOT_IN_ORIGIN_MAIN_DOMAINS"
    assert selected["OD_07_SELECTED"] == "A_STOP_IS_NOT_EXHAUSTION"
    assert selected["OD_08_SELECTED"] == "A_PRESERVE_48_AS_UNRESOLVED_HISTORICAL_ASSERTION"
    assert decision["OWNER_DECISION_COUNT"] == 8
    assert decision["OWNER_DECISION_BY_AGENT"] is False
    assert decision["bound_origin_main_sha"] == ("f6d69aba628030bc9f250df50d43f676c55aac54")
    assert decision["NEW_RELATION_TYPE_CREATED"] is False
    assert decision["federated_relation"]["TYPE"] == "INPUT_TO"
    assert decision["federated_relation"]["TYPE_REUSED"] is True
    reconstruction = _load_json(HISTORICAL_OBS[0])
    assert "owner_selected_decisions" not in reconstruction
    assert "OD_01_SELECTED" not in json.dumps(reconstruction)
    l2 = _read(L2)
    assert "| FB-P3D-14 |" in l2
    assert "INPUT_TO | A-OBS-FSC-POLICY" in l2
    assert "OWNER_DECISIONS_ANSWERED=0" in l2
    assert "A-OBS-FSC-POLICY_IS_NOT_IO-SWR002=true" in l2


def test_policy_does_not_claim_closed_universe() -> None:
    contract = _read(SCOPING)
    decision = _load_json(OWNER_DECISION)
    l4 = _read(L4)
    assert "CURRENTLY_PROVEN_CLOSED_UNIVERSE=false" in contract
    assert "GLOBAL_CLOSED_UNIVERSE_INTENDED=false" in contract
    assert "POLICY_ENABLES_FUTURE_PER_DOMAIN_CLOSED_UNIVERSE_PROOF=true" in contract
    status = decision["closed_universe_status"]
    assert status["CURRENTLY_PROVEN_CLOSED_UNIVERSE"] is False
    assert status["GLOBAL_CLOSED_UNIVERSE_INTENDED"] is False
    assert status["POLICY_ENABLES_FUTURE_PER_DOMAIN_CLOSED_UNIVERSE_PROOF"] is True
    assert "CLOSED_UNIVERSE_PROVEN=false" in l4
    assert re.search(r"(?<![A-Z_])CLOSED_UNIVERSE_PROVEN=true", contract) is None
    assert re.search(r"(?<![A-Z_])SOURCE_UNIVERSE_EXHAUSTED=true", contract) is None
