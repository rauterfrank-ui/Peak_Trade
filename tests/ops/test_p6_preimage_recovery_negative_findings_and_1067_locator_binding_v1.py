"""P6 historical preimage-recovery negative findings and M4_1067 locator replica.

Docs/persistence contract checks only. Does not authorize Live, Testnet,
Canary, flatten execute, credentials, or canonical mutation. Does not
create a domain, exclusion, layer, temporal, or gate ontology.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PERSISTENCE = REPO_ROOT / "docs" / "forensics" / "persistence"
OBS = (
    PERSISTENCE
    / "inventories"
    / "P6_5189_PREIMAGE_RECOVERY_NEGATIVE_FINDINGS_AND_1067_LOCATOR_BINDING_OBSERVATION_V1.json"
)
SET_REGISTER = PERSISTENCE / "registries" / "P6_5189_SET_AND_UNIVERSE_REGISTER_V1.json"
LOCALIZATION = (
    PERSISTENCE / "inventories" / "P6_5189_5011_SOURCE_SET_LOCALIZATION_OBSERVATION_V1.json"
)
L2 = PERSISTENCE / "registries" / "INFORMATION_OBJECT_REFERENCE_REGISTRY_V1.md"
L4 = PERSISTENCE / "registries" / "CURRENT_STATE_PROJECTION_V1.md"
BASE = PERSISTENCE / "PEAK_TRADE_INFORMATION_CORPUS_PERSISTENCE_BASE.md"

EXPECTED_1067_SHA = "7efc7e124b43267f12f4ecf4dea05a4c420223ed7be37a78294af4f761bc03ce"
CENSUS_SHA = "caa85fb2447af1d22c7752e9cacaecf60d058c2b0265ca44f50c14471b42ef0a"


def _load_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def test_1067_locator_replica_count_uniqueness_and_sha256() -> None:
    obs = _load_json(OBS)
    enum = obs["m4_1067_relative_locator_enumeration"]
    members = enum["members"]
    payload = ("\n".join(members) + "\n").encode("utf-8")
    reproduced = hashlib.sha256(payload).hexdigest()
    assert enum["MEMBER_COUNT"] == 1067
    assert enum["UNIQUE_MEMBER_COUNT"] == 1067
    assert len(members) == 1067
    assert len(set(members)) == 1067
    assert enum["SHA256"] == EXPECTED_1067_SHA
    assert reproduced == EXPECTED_1067_SHA
    assert enum["IDENTITY_TYPE"] == "relative_locator"
    assert enum["MEMBER_SEMANTIC"] == "relative_locator"
    assert enum["THIS_IS_NOT_SOURCE_UUID_ENUMERATION"] is True
    assert enum["THIS_IS_NOT_P6_DISCOVERY_5185_MEMBERSHIP"] is True
    assert enum["THIS_IS_NOT_P6_HISTORICAL_5189_MEMBERSHIP"] is True
    assert enum["THIS_IS_NOT_P6_LIVE_5190_MEMBERSHIP"] is True
    assert enum["THIS_IS_NOT_5011_NOT_RELEVANT_MEMBERSHIP"] is True
    assert enum["THIS_IS_NOT_CLOSED_UNIVERSE_PROOF"] is True
    assert enum["DEDUPLICATION_PERFORMED"] is False
    assert enum["SOURCE_UUID_CONVERSION_PERFORMED"] is False
    assert enum["NORMALIZATION_PERFORMED"] is False
    assert enum["LOCATOR_RENAME_PERFORMED"] is False
    assert all(isinstance(item, str) and item.endswith(".jsonl") for item in members)
    assert all("/" in item for item in members)


def test_1067_sha_is_not_p6_5189_census_preimage() -> None:
    obs = _load_json(OBS)
    finding = obs["hash_non_equality"]
    assert finding["1067_LOCATOR_LIST_SHA256"] == EXPECTED_1067_SHA
    assert finding["P6_RELATIVE_LOCATOR_LIST_SHA256"] == CENSUS_SHA
    assert finding["HASH_EQUAL"] is False
    assert finding["1067_LOCATOR_LIST_IS_P6_5189_CENSUS_PREIMAGE"] is False
    assert EXPECTED_1067_SHA != CENSUS_SHA
    assert finding["THIS_IS_IDENTITY_HASH_FINDING_NOT_GLOBAL_IRRECOVERABILITY"] is True


def test_timestamp_binding_limit_and_current_location_absence_are_bounded() -> None:
    obs = _load_json(OBS)
    ts = obs["timestamp_binding_limit"]
    cur = obs["current_location_observations"]
    ext = obs["external_forensic_md_bounded_negative_finding"]
    assert ts["STRING_PRESENT_IN_17B8D1BB"] is False
    assert ts["17B8D1BB_DIRECT_TIMESTAMP_BINDING_TO_5190_INSTANT"] is False
    assert ts["17B8D1BB_IS_NOT_HISTORICALLY_RELATED_TO_640021_NOT_INFERRED"] is True
    assert cur["ABSENT_AT_EXAMINED_LOCATOR_IS_NOT_ARTIFACT_NEVER_EXISTED"] is True
    assert cur["terminals_640021"]["status"] == "ABSENT_AT_EXAMINED_LOCATOR"
    assert cur["tmp_unresolved_semantic_review_script"]["status"] == "ABSENT_AT_EXAMINED_LOCATOR"
    assert cur["tmp_residual_1067_resolution_script"]["status"] == "ABSENT_AT_EXAMINED_LOCATOR"
    assert ext["caa85fb2_full_sha_pattern_status"] == "PATTERN_NOT_FOUND_ON_EXAMINED_EXTERNAL_FILE"
    assert ext["267bc03c_full_sha_pattern_status"] == "PATTERN_NOT_FOUND_ON_EXAMINED_EXTERNAL_FILE"
    assert ext["PREIMAGE_DOES_NOT_EXIST_NOT_CLAIMED"] is True


def test_recovery_outcomes_are_examined_surface_bounded_not_source_set_exhaustion() -> None:
    obs = _load_json(OBS)
    outcomes = obs["recovery_outcomes"]
    for key in (
        "P6_DISCOVERY_5185",
        "P6_HISTORICAL_5189_TOKEN",
        "P6_LIVE_5190",
        "5011_SOURCE_SET",
    ):
        assert outcomes[key]["PREIMAGE_STATUS"] == "PREIMAGE_NOT_FOUND_ON_EXAMINED_SURFACES"
        assert outcomes[key]["PREIMAGE_DOES_NOT_EXIST_NOT_CLAIMED"] is True
    assert obs["SEARCH_SURFACE_EXHAUSTION_IS_NOT_SOURCE_SET_EXHAUSTION"] is True
    assert obs["SOURCE_SET_EXHAUSTION_NOT_CLAIMED"] is True
    assert obs["PREIMAGE_DOES_NOT_EXIST_NOT_CLAIMED"] is True
    assert obs["GLOBAL_IRRECOVERABLE_NOT_CLAIMED"] is True
    assert (
        obs["SEARCH_SURFACE_EXHAUSTION_STATUS"] == "BOUNDED_EXAMINED_SURFACES_ONLY_NOT_SOURCE_SET"
    )
    assert obs["SOURCE_SET_EXHAUSTION_STATUS"] == "NOT_CLAIMED"
    assert obs["examined_surfaces"]
    assert obs["persisted_replica"]["ORIGINAL_SOURCE_EQUALS_PERSISTED_REPLICA"] is False
    assert obs["original_source"]["BYTE_IDENTICAL_COPIES_NOT_MERGED_AS_SOURCE_IDENTITY"] is True


def test_p1_p5_p6_non_regression_and_uncollapsed_counts() -> None:
    obs = _load_json(OBS)
    sets = _load_json(SET_REGISTER)
    loc = _load_json(LOCALIZATION)
    p1 = next(item for item in sets["sets"] if item["set_id"] == "P1_SET")
    p5 = next(item for item in sets["sets"] if item["set_id"] == "P5_SET")
    d5185 = next(item for item in sets["sets"] if item["set_id"] == "P6_DISCOVERY_5185")
    t5189 = next(item for item in sets["sets"] if item["set_id"] == "P6_HISTORICAL_5189_TOKEN")
    live = next(item for item in sets["sets"] if item["set_id"] == "P6_LIVE_5190")
    s174 = next(item for item in sets["sets"] if item["set_id"] == "P6_RELEVANT_174_SET")
    pack169 = next(item for item in sets["sets"] if item["set_id"] == "PACK_TRANSCRIPT_169")
    s5011 = next(item for item in sets["sets"] if item["set_id"] == "5011_SOURCE_SET")
    m4 = next(item for item in sets["sets"] if item["set_id"] == "M4_1067")
    drift = next(
        item for item in sets["sets"] if item["set_id"] == "COUNT_DRIFT_STAGE_VALUES_3946_3951"
    )
    l2 = L2.read_text(encoding="utf-8")
    l4 = L4.read_text(encoding="utf-8")
    base = BASE.read_text(encoding="utf-8")
    assert p1["member_count"] == 129
    assert p1["closed_universe_proven"] is True
    assert p5["member_count"] == 44
    assert p5["closed_universe_proven"] is True
    assert d5185["member_count"] == 5185
    assert t5189["member_count"] == 5189
    assert live["member_count"] == 5190
    assert s174["member_count"] == 174
    assert pack169["member_count"] == 169
    assert s5011["member_count"] == 5011
    assert m4["member_count"] == 1067
    assert d5185["closed_universe_proven"] is False
    assert t5189["closed_universe_proven"] is False
    assert live["closed_universe_proven"] is False
    assert s5011["closed_universe_proven"] is False
    assert m4["closed_universe_proven"] is False
    assert 5185 != 5189 != 5190
    assert 174 != 169
    assert 1067 != 5011
    assert drift["relations_to_other_sets"] == "3946_is_not_3951; neither_is_5011_enumeration"
    assert sets["SET_NODE_COUNT"] == 20
    assert sets["GLOBAL_CLOSED_UNIVERSE_PROVEN"] is False
    assert sets["GLOBAL_SOURCE_UNIVERSE_EXHAUSTED"] is False
    assert sets["LIVE_SOURCE_UNIVERSE_EXHAUSTED"] is False
    assert loc["HISTORICAL_P6_SOURCE_SET_BOUND"] is False
    assert loc["localization_verdict"]["P6_5189_SNAPSHOT_BINDING_VALID"] is False
    assert loc["intermediate_unresolved_1067"]["ids_not_copied_into_this_inventory"] is True
    assert obs["P6_5189_SNAPSHOT_BINDING_VALID"] is False
    assert obs["HISTORICAL_P6_SOURCE_SET_BOUND_STATUS"] == "UNBOUND"
    assert obs["P6_DISCOVERY_5185_SOURCE_SET_EXHAUSTED"] is False
    assert obs["P6_HISTORICAL_5189_TOKEN_SOURCE_SET_EXHAUSTED"] is False
    assert obs["P6_LIVE_5190_SOURCE_SET_EXHAUSTED"] is False
    assert obs["5011_SOURCE_SET_EXHAUSTED"] is False
    assert obs["GLOBAL_CLOSED_UNIVERSE_PROVEN"] is False
    assert obs["CENSUS_48_OPERATIONALIZED"] is False
    assert obs["P1_MEMBERSHIP_CHANGED"] is False
    assert obs["P1_CLOSURE_CHANGED"] is False
    assert obs["P5_MEMBERSHIP_CHANGED"] is False
    assert obs["P5_CLOSURE_CHANGED"] is False
    assert obs["P6_STATE_CHANGED"] is False
    assert obs["NEW_DOMAIN_ONTOLOGY_CREATED"] is False
    assert obs["AUTHORITY"] == "NONE"
    assert "| A-OBS-P6-PREIMAGE-1067 |" in l2
    assert "| FB-P3D-19 |" in l2
    assert "A-OBS-P6-PREIMAGE-1067" in l4
    assert "GLOBAL_CLOSED_UNIVERSE_PROVEN=false" in l4
    assert (
        "P6_5189_PREIMAGE_RECOVERY_NEGATIVE_FINDINGS_AND_1067_LOCATOR_BINDING_OBSERVATION_V1.json"
        in base
    )
    assert obs["maintenance_contract"]["SET_CONTRACT_UPDATE_REQUIRED"] is False
    assert obs["maintenance_contract"]["L0_UPDATE_REQUIRED"] is False
