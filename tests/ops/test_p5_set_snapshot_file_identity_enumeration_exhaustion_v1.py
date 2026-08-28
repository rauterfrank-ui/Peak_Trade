"""P5_SET snapshot file-identity enumeration exhaustion.

Docs/persistence contract checks only. Does not authorize Live, Testnet,
Canary, flatten execute, credentials, or canonical mutation. Does not
create a domain or relation ontology. Does not walk the live P5 tree.
"""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PERSISTENCE = REPO_ROOT / "docs" / "forensics" / "persistence"
P5_INVENTORY = (
    PERSISTENCE / "inventories" / "P5_DOCUMENTS_PEAK_TRADE_FORENSICS_FILE_INVENTORY_V1.json"
)
XFACTS = PERSISTENCE / "inventories" / "CROSS_CORPUS_RELATION_FACTS_V1.json"
P5_EXH = (
    PERSISTENCE
    / "inventories"
    / "P5_SET_SNAPSHOT_FILE_IDENTITY_ENUMERATION_EXHAUSTION_OBSERVATION_V1.json"
)
P1_EXH = (
    PERSISTENCE
    / "inventories"
    / "P1_SET_SNAPSHOT_FILE_IDENTITY_ENUMERATION_EXHAUSTION_OBSERVATION_V1.json"
)
SET_REGISTER = PERSISTENCE / "registries" / "P6_5189_SET_AND_UNIVERSE_REGISTER_V1.json"
L2 = PERSISTENCE / "registries" / "INFORMATION_OBJECT_REFERENCE_REGISTRY_V1.md"
L4 = PERSISTENCE / "registries" / "CURRENT_STATE_PROJECTION_V1.md"
FSC_POLICY = (
    PERSISTENCE
    / "inventories"
    / "P6_FEDERATED_SCOPED_COMPLETENESS_POLICY_OWNER_DECISION_OBSERVATION_V1.json"
)


def _load_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def test_p5_set_exhaustion_criterion_is_source_bound_and_not_p1_policy() -> None:
    obs = _load_json(P5_EXH)
    p1 = _load_json(P1_EXH)
    sets = _load_json(SET_REGISTER)
    p5 = next(item for item in sets["sets"] if item["set_id"] == "P5_SET")
    p1_set = next(item for item in sets["sets"] if item["set_id"] == "P1_SET")
    assert obs["P5_SET_EXHAUSTION_POLICY"] == "P5_SNAPSHOT_FILE_IDENTITY_ENUMERATION_EXHAUSTION_V1"
    assert obs["SEMANTIC_SCOPE"] == "P5_SET_BOUND_SNAPSHOT_ONLY"
    assert obs["NAMED_DOMAIN_ID"] == "P5_SET"
    assert obs["TEMPORAL_ROLE"] == "snapshot"
    assert obs["LAYER_IDENTITY"] == "origin/main"
    assert obs["P1_EXHAUSTION_POLICY_AUTOMATICALLY_REUSED_FOR_P5"] is False
    assert p1["P1_SET_EXHAUSTION_POLICY"] == "SNAPSHOT_FILE_IDENTITY_ENUMERATION_EXHAUSTION_V1"
    assert p1["P1_SET_EXHAUSTION_POLICY"] != obs["P5_SET_EXHAUSTION_POLICY"]
    assert p5["exhaustion_criterion"] == "P5_SNAPSHOT_FILE_IDENTITY_ENUMERATION_EXHAUSTION_V1"
    assert p1_set["exhaustion_criterion"] == "SNAPSHOT_FILE_IDENTITY_ENUMERATION_EXHAUSTION_V1"
    assert p1_set["closed_universe_proven"] is True
    assert sets["P5_SET_SNAPSHOT_EXHAUSTION_CRITERION_BOUND"] is True
    assert sets["P1_SET_SNAPSHOT_EXHAUSTION_CRITERION_BOUND"] is True
    l2 = L2.read_text(encoding="utf-8")
    assert "| A-OBS-P5-EXH |" in l2
    assert "| FB-P3D-17 |" in l2
    assert "| FB-P3D-18 |" in l2


def test_p5_set_e1_through_e15_and_uncollapsed_counts() -> None:
    inv = _load_json(P5_INVENTORY)
    xfacts = _load_json(XFACTS)
    sets = _load_json(SET_REGISTER)
    obs = _load_json(P5_EXH)
    recs = inv["records"]
    p5 = next(item for item in sets["sets"] if item["set_id"] == "P5_SET")
    p5x = xfacts["P5_DOCUMENTS_PEAK_TRADE_FORENSICS_VS_REPO"]
    paths = [item["path"] for item in recs]
    rels = [item["rel"] for item in recs]
    shas = [item["sha256"] for item in recs]
    p5_only_locs = sum(len(item["p5_locators"]) for item in p5x["p5_only_by_sha"])
    bi_p5_locs = sum(len(item["p5_locators"]) for item in p5x["byte_identical"])
    assert inv["file_count"] == 44
    assert len(recs) == 44
    assert len(set(paths)) == 44
    assert len(set(rels)) == 44
    assert p5["member_count"] == 44
    assert inv["P5_ONLY_FILE_LOCATOR_COUNT"] == 28
    assert inv["P5_ONLY_UNIQUE_SHA_COUNT"] == 27
    assert p5x["P5_ONLY_FILE_LOCATOR_COUNT"] == 28
    assert p5x["P5_ONLY_UNIQUE_SHA_COUNT"] == 27
    assert len(p5x["p5_only_by_sha"]) == 27
    assert p5_only_locs == 28
    assert p5x["byte_identical_sha_count"] == 15
    assert len(p5x["byte_identical"]) == 15
    assert bi_p5_locs == 16
    assert p5_only_locs + bi_p5_locs == 44
    assert len(set(shas)) == 42
    assert 44 != 28
    assert 44 != 27
    assert 28 != 27
    assert inv["ASSIGNED_AS_P2_OWNER_NAMED_PEAK_TRADE_FORENSIK"] is False
    assert all(isinstance(path, str) and path for path in paths)
    assert all(isinstance(rel, str) and rel for rel in rels)
    assert all(isinstance(sha, str) and len(sha) == 64 for sha in shas)
    assert all(item.get("is_symlink") is False for item in recs)
    assert obs["exhaustion_evidence"]["FULL_P5_UNIQUE_SHA256_COUNT"] == 42
    assert obs["exhaustion_evidence"]["P5_P1_BYTE_IDENTICAL_PAIR_COUNT"] == 15
    assert obs["exhaustion_evidence"]["P5_P1_BYTE_IDENTICAL_P5_LOCATOR_COUNT"] == 16
    assert obs["e_conditions"] == {f"E{i}": "PASS" for i in range(1, 16)}
    assert obs["COUNT_44_27_28_COLLAPSED"] is False
    assert obs["P5_ONLY_28_PROMOTED_TO_FULL_P5_COUNT"] is False
    assert obs["P5_SNAPSHOT_EXHAUSTION_IS_NOT_LIVE_EXHAUSTION"] is True
    assert obs["LIVE_GROWTH_INCLUDED_IN_P5"] is False
    assert obs["DISCOVERY_STOP_USED_AS_EXHAUSTION"] is False
    assert obs["SOURCE_IDENTITY_COLLAPSE_PERFORMED"] is False
    assert obs["CENSUS_48_USED_IN_DOMAIN_FORMULA"] is False
    assert obs["P1_MEMBERSHIP_CHANGED"] is False
    assert obs["P6_STATE_CHANGED"] is False


def test_p5_per_domain_closed_universe_is_not_global_or_live() -> None:
    obs = _load_json(P5_EXH)
    sets = _load_json(SET_REGISTER)
    fsc = _load_json(FSC_POLICY)
    l4 = L4.read_text(encoding="utf-8")
    p5 = next(item for item in sets["sets"] if item["set_id"] == "P5_SET")
    p1 = next(item for item in sets["sets"] if item["set_id"] == "P1_SET")
    p6_5189 = next(item for item in sets["sets"] if item["set_id"] == "P6_HISTORICAL_5189_TOKEN")
    relevant_174 = next(item for item in sets["sets"] if item["set_id"] == "P6_RELEVANT_174_SET")
    assert obs["verdict"]["PER_DOMAIN_PROOF_VERDICT"] == (
        "PER_DOMAIN_COMPLETENESS_AND_EXHAUSTION_PROVEN"
    )
    assert obs["verdict"]["PER_DOMAIN_CLOSED_UNIVERSE_PROVEN"] is True
    assert obs["verdict"]["PER_DOMAIN_CLOSED_UNIVERSE_DOMAIN"] == "P5_SET"
    assert obs["verdict"]["GLOBAL_CLOSED_UNIVERSE_PROVEN"] is False
    assert obs["verdict"]["GLOBAL_SOURCE_UNIVERSE_EXHAUSTED"] is False
    assert obs["verdict"]["LIVE_SOURCE_UNIVERSE_EXHAUSTED"] is False
    assert p5["closed_universe_proven"] is True
    assert p5["closed_universe_scope"] == "P5_SET_bound_snapshot_only"
    assert p1["closed_universe_proven"] is True
    assert p6_5189["closed_universe_proven"] is False
    assert relevant_174["member_count"] == 174
    assert sets["THIS_REGISTER_IS_NOT_A_CLOSED_UNIVERSE"] is True
    assert sets["GLOBAL_CLOSED_UNIVERSE_PROVEN"] is False
    assert fsc["closed_universe_status"]["CLOSED_UNIVERSE_PROVEN"] is False
    assert fsc["closed_universe_status"]["SOURCE_UNIVERSE_EXHAUSTED"] is False
    assert "P5_SET_PER_DOMAIN_CLOSED_UNIVERSE_PROVEN=true" in l4
    assert "P1_SET_PER_DOMAIN_CLOSED_UNIVERSE_PROVEN=true" in l4
    assert "GLOBAL_CLOSED_UNIVERSE_PROVEN=false" in l4
    assert "CLOSED_UNIVERSE_PROVEN=false" in l4
    assert all(value == "PASS" for value in obs["pdc"].values())
    assert obs["pdc"]["PDC_10"] == "PASS"
    assert obs["pdc"]["PDC_11"] == "PASS"
    assert obs["HISTORICAL_OBSERVATION_REWRITE_COUNT"] == 0
    assert obs["MEMBERSHIP_LIST_REWRITE_COUNT"] == 0
    assert obs["NEW_DOMAIN_ONTOLOGY_CREATED"] is False
    assert obs["NEW_RELATION_TYPE_CREATED"] is False
    assert obs["CURRENT_TREE_USED_TO_REWRITE_P5_SNAPSHOT"] is False
