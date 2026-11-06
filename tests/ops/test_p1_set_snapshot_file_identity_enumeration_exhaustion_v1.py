"""P1_SET snapshot file-identity enumeration exhaustion.

Docs/persistence contract checks only. Does not authorize Live, Testnet,
Canary, flatten execute, credentials, or canonical mutation. Does not
create a domain or relation ontology.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PERSISTENCE = REPO_ROOT / "docs" / "forensics" / "persistence"
P1_INVENTORY = PERSISTENCE / "inventories" / "P1_REPO_FORENSIC_TREES_FILE_INVENTORY_V1.json"
P1_CONTRACT = PERSISTENCE / "inventories" / "P1_REPO_FORENSIC_TREES_FILE_INVENTORY_V1.contract.json"
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
FOUR_TREES = ("docs/forensic", "docs/forensics", "forensic", "forensics")


def _load_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def test_p1_set_exhaustion_criterion_is_source_bound() -> None:
    obs = _load_json(P1_EXH)
    sets = _load_json(SET_REGISTER)
    p1 = next(item for item in sets["sets"] if item["set_id"] == "P1_SET")
    assert obs["P1_SET_EXHAUSTION_POLICY"] == "SNAPSHOT_FILE_IDENTITY_ENUMERATION_EXHAUSTION_V1"
    assert obs["SEMANTIC_SCOPE"] == "P1_SET_BOUND_SNAPSHOT_ONLY"
    assert obs["NAMED_DOMAIN_ID"] == "P1_SET"
    assert obs["TEMPORAL_ROLE"] == "snapshot"
    assert obs["LAYER_IDENTITY"] == "origin/main"
    assert p1["exhaustion_criterion"] == "SNAPSHOT_FILE_IDENTITY_ENUMERATION_EXHAUSTION_V1"
    assert sets["P1_SET_SNAPSHOT_EXHAUSTION_CRITERION_BOUND"] is True
    l2 = L2.read_text(encoding="utf-8")
    assert "| A-OBS-P1-EXH |" in l2
    assert "| FB-P3D-15 |" in l2
    assert "| FB-P3D-16 |" in l2


def test_p1_set_e1_through_e10_and_member_count() -> None:
    inv = _load_json(P1_INVENTORY)
    contract = _load_json(P1_CONTRACT)
    sets = _load_json(SET_REGISTER)
    obs = _load_json(P1_EXH)
    recs = inv["records"]
    p1 = next(item for item in sets["sets"] if item["set_id"] == "P1_SET")
    tree_counts = Counter(item["tree"] for item in recs)
    summary = {key: value["file_count"] for key, value in inv["trees_summary"].items()}
    paths = [item["path"] for item in recs]
    shas = [item["sha256"] for item in recs]
    persistence_members = [
        item
        for item in recs
        if "docs/forensics/persistence" in (item.get("path") or "")
        or str(item.get("rel", "")).startswith("persistence/")
    ]
    assert set(tree_counts) == set(FOUR_TREES)
    assert tree_counts["docs/forensic"] == 4
    assert tree_counts["docs/forensics"] == 5
    assert tree_counts["forensic"] == 46
    assert tree_counts["forensics"] == 74
    assert sum(summary.values()) == 129
    assert inv["file_count"] == 129
    assert len(recs) == 129
    assert len(set(paths)) == 129
    assert len(set((item["tree"], item["rel"]) for item in recs)) == 129
    assert p1["member_count"] == 129
    assert contract["inventory_record_count"] == 129
    assert len(persistence_members) == 0
    assert all(isinstance(path, str) and path for path in paths)
    assert all(isinstance(sha, str) and len(sha) == 64 for sha in shas)
    assert len(set(shas)) == 125
    assert obs["exhaustion_evidence"]["UNIQUE_SHA256_COUNT"] == 125
    assert obs["e_conditions"] == {f"E{i}": "PASS" for i in range(1, 11)}
    assert obs["P1_SNAPSHOT_EXHAUSTION_IS_NOT_LIVE_EXHAUSTION"] is True
    assert obs["LIVE_GROWTH_INCLUDED_IN_P1"] is False
    assert obs["DISCOVERY_STOP_USED_AS_EXHAUSTION"] is False
    assert obs["SOURCE_IDENTITY_COLLAPSE_PERFORMED"] is False
    assert obs["CENSUS_48_USED_IN_DOMAIN_FORMULA"] is False


def test_p1_snapshot_sha256_integrity_against_committed_blobs() -> None:
    inv = _load_json(P1_INVENTORY)
    match = 0
    for item in inv["records"]:
        git_path = f"{item['tree']}/{item['rel']}"
        blob = (REPO_ROOT / git_path).read_bytes()
        assert hashlib.sha256(blob).hexdigest() == item["sha256"]
        match += 1
    assert match == 129


def test_p1_per_domain_closed_universe_is_not_global() -> None:
    obs = _load_json(P1_EXH)
    sets = _load_json(SET_REGISTER)
    fsc = _load_json(FSC_POLICY)
    l4 = L4.read_text(encoding="utf-8")
    p1 = next(item for item in sets["sets"] if item["set_id"] == "P1_SET")
    assert obs["verdict"]["PER_DOMAIN_PROOF_VERDICT"] == (
        "PER_DOMAIN_COMPLETENESS_AND_EXHAUSTION_PROVEN"
    )
    assert obs["verdict"]["PER_DOMAIN_CLOSED_UNIVERSE_PROVEN"] is True
    assert obs["verdict"]["PER_DOMAIN_CLOSED_UNIVERSE_DOMAIN"] == "P1_SET"
    assert obs["verdict"]["GLOBAL_CLOSED_UNIVERSE_PROVEN"] is False
    assert obs["verdict"]["GLOBAL_SOURCE_UNIVERSE_EXHAUSTED"] is False
    assert obs["verdict"]["LIVE_SOURCE_UNIVERSE_EXHAUSTED"] is False
    assert p1["closed_universe_proven"] is True
    assert p1["closed_universe_scope"] == "P1_SET_bound_snapshot_only"
    assert sets["THIS_REGISTER_IS_NOT_A_CLOSED_UNIVERSE"] is True
    assert sets["GLOBAL_CLOSED_UNIVERSE_PROVEN"] is False
    assert fsc["closed_universe_status"]["CLOSED_UNIVERSE_PROVEN"] is False
    assert fsc["closed_universe_status"]["SOURCE_UNIVERSE_EXHAUSTED"] is False
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
