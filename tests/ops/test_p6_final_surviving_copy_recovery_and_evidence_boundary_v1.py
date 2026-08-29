"""P6 final surviving-copy recovery and evidence-boundary persist.

Docs/persistence contract checks only. Does not authorize Live, Testnet,
Canary, flatten execute, credentials, or canonical mutation. Does not
create a domain, exclusion, layer, temporal, or gate ontology.
"""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PERSISTENCE = REPO_ROOT / "docs" / "forensics" / "persistence"
OBS = (
    PERSISTENCE
    / "inventories"
    / "P6_5189_FINAL_SURVIVING_COPY_RECOVERY_AND_EVIDENCE_BOUNDARY_OBSERVATION_V1.json"
)
PRIOR = (
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

CENSUS_SHA = "caa85fb2447af1d22c7752e9cacaecf60d058c2b0265ca44f50c14471b42ef0a"
REVIEW_SHA = "267bc03ca823c112d6fc2ecc77227ef1f9c9d2c96ea3ae4cf845437284c6b565"
M4_SHA = "7efc7e124b43267f12f4ecf4dea05a4c420223ed7be37a78294af4f761bc03ce"
REVIEW_SCRIPT_SHA = "9ba8e3c340186a66a6a71e544859f901a6adeacdd01e89aec386f4ac62a9b51e"
RESIDUAL_SCRIPT_SHA = "4e30648e2ee309acabf4b419c56692f752d221e15bd2d9401e710127f9af00e7"
FORBIDDEN_GLOBAL_CLAIMS = (
    "PREIMAGE_DOES_NOT_EXIST",
    "PREIMAGE_NEVER_EXISTED",
    "PREIMAGE_DOES_NOT_EXIST_ANYWHERE",
    "GLOBAL_IRRECOVERABLE",
    "GLOBAL_SOURCE_UNIVERSE_EXHAUSTED",
)


def _load_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def test_authority_none_and_no_ontology_escalation() -> None:
    obs = _load_json(OBS)
    assert obs["AUTHORITY"] == "NONE"
    assert obs["TARGET_AUTHORITY"] == "NONE"
    assert obs["FORENSIC_PERSISTENCE_AUTHORITY"] == "NONE"
    assert obs["CANONICAL"] is False
    assert obs["NEW_AUTHORITY_CREATED"] is False
    assert obs["NEW_DOMAIN_ONTOLOGY_CREATED"] is False
    assert obs["AUTHORITY_ESCALATION_PRESENT"] is False
    assert obs["GAP_CLOSED"] is False
    assert obs["P6_CLOSED"] is False
    assert obs["CU_PROVEN"] is False
    assert obs["GLOBAL_CLOSED_UNIVERSE_PROVEN"] is False


def test_census_producer_command_identity_and_serialization() -> None:
    obs = _load_json(OBS)
    prod = obs["producer_provenance"]
    census = prod["census_hash_original_producer"]
    assert prod["CAA85FB2_PRODUCER"] == "d234_L24_find_sed_sort_shasum"
    assert "find" in census["command_verbatim"]
    assert "sed" in census["command_verbatim"]
    assert "sort" in census["command_verbatim"]
    assert "shasum -a 256" in census["command_verbatim"]
    assert census["list_flow"] == "stdin_to_shasum"
    assert census["full_list_written_to_file"] is False
    assert census["full_list_printed_to_stdout"] is False
    assert census["attested_sha256"] == CENSUS_SHA
    assert census["attested_census_count"] == 5189
    assert prod["CAA85FB2_PREIMAGE_MATERIALIZED_BY_PRODUCER"] is False
    recompute = prod["census_hash_recompute_producer"]
    assert recompute["script_content_sha256"] == REVIEW_SCRIPT_SHA
    assert recompute["MATCHES_ATTESTED_RAW_EXECUTION_SCRIPT_SHA"] is True
    assert "hashlib.sha256" in recompute["locator_sha_verbatim"]
    residual = prod["residual_script"]
    assert residual["script_content_sha256_after_strreplace"] == RESIDUAL_SCRIPT_SHA


def test_review_tsv_and_producer_non_materialization_scope() -> None:
    obs = _load_json(OBS)
    prod = obs["producer_provenance"]
    tsv = prod["review_tsv_267bc03c_producer"]
    assert tsv["attested_sha256"] == REVIEW_SHA
    assert tsv["stdout_prints_tsv_blob"] is False
    assert tsv["open_write_of_preimage"] is False
    assert prod["267BC03C_PREIMAGE_MATERIALIZED_BY_PRODUCER"] is False
    assert prod["HISTORICAL_PRODUCER_MATERIALIZED_PERSISTED_PREIMAGE"] is False
    assert prod["HISTORICAL_PRODUCER_MATERIALIZED_PERSISTED_PREIMAGE_SCOPE"] == (
        "FOR_THE_RECOVERED_CENSUS_AND_REVIEW_PRODUCERS"
    )
    assert prod["NO_PERSISTED_PREIMAGE_CREATED_BY_THIS_PRODUCER"] is True
    assert obs["PRODUCER_NON_MATERIALIZATION_IS_NOT_GLOBAL_NONEXISTENCE"] is True
    assert obs["TOOL_RESULT_HASH_OUTPUT_IS_NOT_LOCATOR_LIST_PREIMAGE"] is True


def test_bounded_recovery_wording_and_no_global_irrecoverability() -> None:
    obs = _load_json(OBS)
    text = json.dumps(obs)
    for token in FORBIDDEN_GLOBAL_CLAIMS:
        assert f'"{token}": true' not in text
    assert obs["PREIMAGE_DOES_NOT_EXIST_NOT_CLAIMED"] is True
    assert obs["PREIMAGE_NEVER_EXISTED_NOT_CLAIMED"] is True
    assert obs["PREIMAGE_DOES_NOT_EXIST_ANYWHERE_NOT_CLAIMED"] is True
    assert obs["GLOBAL_IRRECOVERABLE_NOT_CLAIMED"] is True
    assert obs["GLOBAL_SOURCE_UNIVERSE_EXHAUSTED_NOT_CLAIMED"] is True
    assert (
        obs["HISTORICAL_P6_5189_PREIMAGE_NOT_RECOVERED_ON_DECLARED_AND_EXAMINED_RECOVERY_SURFACES"]
        is True
    )
    assert obs["EXACT_PREIMAGE_RECOVERED"] is False
    assert obs["CANDIDATE_COUNT"] == 0
    assert obs["P6_CENSUS_PREIMAGE_RECOVERY_STATUS"] == "NOT_RECOVERED"
    assert (
        obs["P6_HISTORICAL_RECOVERY_PATH_FROM_CURRENTLY_IDENTIFIED_LOCAL_EVIDENCE"] == "EXHAUSTED"
    )
    assert obs["NO_FURTHER_EVIDENCE_BACKED_LOCAL_RECOVERY_SURFACE_IDENTIFIED"] is True
    assert obs["GENERIC_SEARCH_AGAIN_NOT_RECOMMENDED"] is True
    assert obs["EXHAUSTED_DOES_NOT_MEAN_P6_CU_PROVEN"] is True
    assert obs["EXHAUSTED_DOES_NOT_MEAN_GLOBAL_CU_PROVEN"] is True
    assert obs["MISSING_BACKUP_ACCESS_IS_NOT_NEGATIVE_RECOVERY_RESULT"] is True
    assert obs["surface_results"]["APFS_SNAPSHOT_STATUS"] == (
        "OS_UPDATE_SNAPSHOT_PRESENT_NOT_MOUNTED_CONTENT_NOT_EXAMINED_DUE_TO_ACCESS_BOUNDARY"
    )
    assert obs["surface_results"]["P2_LOCATION_UNRESOLVED"] is True
    assert obs["p2_resolution_this_pass"]["ALTERNATIVE_DIRECTORY_ASSIGNED"] is False
    assert obs["LIVE_CENSUS_RECOMPUTE_PERFORMED"] is False
    assert obs["CURRENT_LIVE_JSONL_IS_NOT_HISTORICAL_5189"] is True


def test_p6_remains_unbound_and_1067_is_not_5189() -> None:
    obs = _load_json(OBS)
    prior = _load_json(PRIOR)
    assert obs["HISTORICAL_P6_SOURCE_SET_BOUND_STATUS"] == "UNBOUND"
    assert obs["P6_5189_SNAPSHOT_BINDING_VALID"] is False
    assert obs["1067_LOCATOR_ENUMERATION_IS_NOT_5189_CENSUS_PREIMAGE"] is True
    assert obs["M4_1067_SHA256"] == M4_SHA
    assert obs["P6_RELATIVE_LOCATOR_LIST_SHA256"] == CENSUS_SHA
    assert M4_SHA != CENSUS_SHA
    assert prior["hash_non_equality"]["HASH_EQUAL"] is False
    assert (
        obs[
            "THIS_FILE_DOES_NOT_REWRITE_P6_5189_PREIMAGE_RECOVERY_NEGATIVE_FINDINGS_AND_1067_LOCATOR_BINDING_OBSERVATION"
        ]
        is True
    )


def test_5011_remains_aggregate_only_and_uncollapsed_counts() -> None:
    obs = _load_json(OBS)
    assert obs["5011_REMAINS_AGGREGATE_ONLY"] is True
    assert obs["5011_EXACT_MEMBER_LIST_RECOVERED"] is False
    assert obs["COUNT_5185_EQUALS_5189"] is False
    assert obs["COUNT_5189_EQUALS_5190"] is False
    assert obs["COUNT_174_EQUALS_169"] is False
    assert obs["COUNT_1067_EQUALS_5011"] is False
    assert obs["COUNT_3946_EQUALS_3951"] is False
    assert 5185 != 5189 != 5190
    assert 174 != 169
    assert 1067 != 5011
    assert 3946 != 3951


def test_p1_p5_non_regression_and_source_set_exhausted_flags_remain_false() -> None:
    obs = _load_json(OBS)
    sets = _load_json(SET_REGISTER)
    loc = _load_json(LOCALIZATION)
    p1 = next(item for item in sets["sets"] if item["set_id"] == "P1_SET")
    p5 = next(item for item in sets["sets"] if item["set_id"] == "P5_SET")
    t5189 = next(item for item in sets["sets"] if item["set_id"] == "P6_HISTORICAL_5189_TOKEN")
    s5011 = next(item for item in sets["sets"] if item["set_id"] == "5011_SOURCE_SET")
    l2 = L2.read_text(encoding="utf-8")
    l4 = L4.read_text(encoding="utf-8")
    base = BASE.read_text(encoding="utf-8")
    assert p1["closed_universe_proven"] is True
    assert p5["closed_universe_proven"] is True
    assert t5189["closed_universe_proven"] is False
    assert s5011["closed_universe_proven"] is False
    assert sets["GLOBAL_CLOSED_UNIVERSE_PROVEN"] is False
    assert loc["HISTORICAL_P6_SOURCE_SET_BOUND"] is False
    assert loc["localization_verdict"]["P6_5189_SNAPSHOT_BINDING_VALID"] is False
    assert obs["P1_MEMBERSHIP_CHANGED"] is False
    assert obs["P1_CLOSURE_CHANGED"] is False
    assert obs["P5_MEMBERSHIP_CHANGED"] is False
    assert obs["P5_CLOSURE_CHANGED"] is False
    assert obs["P6_STATE_CHANGED"] is False
    assert obs["P6_DISCOVERY_5185_SOURCE_SET_EXHAUSTED"] is False
    assert obs["P6_HISTORICAL_5189_TOKEN_SOURCE_SET_EXHAUSTED"] is False
    assert obs["P6_LIVE_5190_SOURCE_SET_EXHAUSTED"] is False
    assert obs["5011_SOURCE_SET_EXHAUSTED"] is False
    assert obs["CENSUS_48_OPERATIONALIZED"] is False
    assert obs["SEARCH_SURFACE_EXHAUSTION_IS_NOT_SOURCE_SET_EXHAUSTION"] is True
    assert "| A-OBS-P6-SURVIVING-COPY-BOUNDARY |" in l2
    assert "| FB-P3D-20 |" in l2
    assert "A-OBS-P6-SURVIVING-COPY-BOUNDARY" in l4
    assert "GLOBAL_CLOSED_UNIVERSE_PROVEN=false" in l4
    assert "P6_5189_FINAL_SURVIVING_COPY_RECOVERY_AND_EVIDENCE_BOUNDARY_OBSERVATION_V1.json" in base
    assert obs["maintenance_contract"]["SET_CONTRACT_UPDATE_REQUIRED"] is False
    assert obs["maintenance_contract"]["L0_UPDATE_REQUIRED"] is False
    assert obs["THIS_FILE_DOES_NOT_MUTATE_P6_5189_SET_AND_UNIVERSE_REGISTER"] is True
