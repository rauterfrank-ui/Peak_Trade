"""WP-FS-B1 post-merge canonical persist invariants. Docs/governance only. No runtime."""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
MASTER_RUNBOOK = REPO_ROOT / "docs" / "runbooks" / "canonical" / "PEAK_TRADE_MASTER_RUNBOOK.md"
MAP_OF_TRUTH = REPO_ROOT / "docs" / "governance" / "PEAK_TRADE_MAP_OF_TRUTH.md"
CENSUS_META = REPO_ROOT / "docs" / "system_atlas" / "census" / "census_meta.yaml"

WP_FS_B1_HEADING = (
    "### 11.13.5 Parallel-track WP-FS-B1 canonical persist and Atlas navigation census rebind"
)
PRIOR_DDO_HEADING = (
    "### 11.13.5 Parallel-track canonical DDO offline contract-foundation persist"
    " and Atlas navigation census rebind"
)
Z2DA_HEADING = "### 11.13.5.Z2DA Post-Z2CZ position-creation / autonomy semantic rebind persist"
LADDER_HEADING = "## 11.14 Live order and economic evidence ladder"
OWNER_GO = "PEAK_TRADE_OWNER_GO_WP_FS_B1_CANONICAL_PERSIST_AND_ATLAS_NAVIGATION_REBIND_V1"
WP_FS_B1_GIT_MERGE_SHA = "14e8a58f32dcb6b521be6b2559b388bf27360194"
HISTORICAL_EVIDENCE_SHA = "615de3b307132b73a60df33fd3bedfac811c8cce"
PRIOR_CENSUS_SHA = "46d2c1734746d6d1332de0dfb03840d3bd8c31b1"
LIVE_EARLIEST = (
    "NO_AUTHORIZED_REACHABLE_PRODUCER_OF_NONZERO_VENUE_POSITION_REQUIRED_BY_PREREQUISITE_08"
)


def _read(path: Path) -> str:
    assert path.is_file(), f"missing canonical path: {path}"
    return path.read_text(encoding="utf-8")


def _wp_fs_b1_section(text: str) -> str:
    start = text.find(WP_FS_B1_HEADING)
    assert start >= 0, "missing WP-FS-B1 persist heading"
    end = text.find(LADDER_HEADING, start)
    assert end > start, "missing §11.14 boundary after WP-FS-B1 persist"
    return text[start:end]


def test_wp_fs_b1_heading_is_unique_and_follows_parallel_ddo_persist() -> None:
    text = _read(MASTER_RUNBOOK)
    assert text.count(WP_FS_B1_HEADING) == 1
    z2da = text.find(Z2DA_HEADING)
    prior = text.find(PRIOR_DDO_HEADING)
    persist = text.find(WP_FS_B1_HEADING)
    ladder = text.find(LADDER_HEADING)
    assert 0 <= z2da < prior < persist < ladder


def test_wp_fs_b1_docs_bind_already_merged_observation_only_fact() -> None:
    section = _wp_fs_b1_section(_read(MASTER_RUNBOOK))
    required = (
        "AUTHORIZED_SCOPE=A_PARALLEL_TRACK_WP_FS_B1_CANONICAL_PERSIST_AND_ATLAS_NAVIGATION_CENSUS_REBIND_ONLY",
        f"OWNER_GO={OWNER_GO}",
        "OWNER_GO_STATUS=CONSUMED",
        f"CURRENT_ORIGIN_MAIN_SHA={WP_FS_B1_GIT_MERGE_SHA}",
        f"CURRENT_REPO_SHA={WP_FS_B1_GIT_MERGE_SHA}",
        f"WP_FS_B1_GIT_MERGE_SHA={WP_FS_B1_GIT_MERGE_SHA}",
        f"HISTORICAL_EVIDENCE_SHA={HISTORICAL_EVIDENCE_SHA}",
        "CURRENT_REPO_SHA_NE_HISTORICAL_EVIDENCE_SHA=true",
        "WP_FS_B1_GIT_MERGED_BEFORE_THIS_PERSIST=true",
        "WP_FS_B1_IMPLEMENTED_BY_THIS_PERSIST=false",
        "WP_FS_B1_PURPOSE=DDO_OBSERVATION_HOST_DECORATOR_COMPLETION",
        "WP_FS_B1_CAPTURE_CLASS=OBSERVATION_ONLY",
        "WP_FS_B1_PRODUCER_RESULT_SEMANTICS_CHANGED=false",
        "WP_FS_B1_EXTERNAL_EFFECT=NONE",
        "LAST_MERGED_PR=6215",
        "CURRENT_CANONICAL_SECTION=11.13.5.Z2DA",
        "CURRENT_CANONICAL_SECTION_REPLACED=false",
        "CANONICAL_LIVE_NEXT_POINTER_CHANGED=false",
        f"CANONICAL_LIVE_EARLIEST_UNRESOLVED_DEPENDENCY={LIVE_EARLIEST}",
        "WP_FA_01_THROUGH_WP_FA_07_OFFLINE_DDO_CONTRACT_FOUNDATION=CLOSED",
        "WP_FA_08_CANONICAL_DEFINITION_FOUND=false",
        "WP_FA_08_DEFINED_BY_THIS_PERSIST=false",
        "WP_FA_08_AUTHORIZED=false",
        "WP_FA_08_IMPLEMENTED_BY_THIS_PERSIST=false",
        "WP_FA_SERIES_SUCCESSOR_INVENTED=false",
        "THIS_GO_AUTHORIZES_WP_FA_08=false",
        "SUPERVISOR_PRODUCTIVE_HOST_WIRING=false",
        "SUPERVISOR_HOST_ACTIVATION_AUTHORIZED=false",
        "AUTONOMY_SUPERVISOR_RUNTIME_REACHABILITY=false",
        "EXECUTION_PERMISSION_AUTHORIZED=false",
        "VENUE_EXECUTION_AUTHORIZED=false",
        "LEARNING_PRODUCTIVE_AUTHORITY=NONE",
        "PROMOTION_AUTHORITY_ACTIVATION=false",
        "PRODUCTIVE_DEPLOYMENT_ALLOWED=false",
        "PRODUCTIVE_ROLLBACK_ALLOWED=false",
        "LIVE_AUTHORIZED=false",
        "TESTNET_AUTHORIZED=false",
        "CANARY_AUTHORIZED=false",
        "ORDERS_ALLOWED=false",
        "ATLAS_AUTHORITY=NONE",
        "ATLAS_ROLE=NAVIGATION_INDEX_ONLY",
        "ATLAS_MUTATION=false",
        "LANDSCAPE_AUTHORITY=NONE",
        "LANDSCAPE_ROLE=READ_ONLY_VISUAL_CONSUMER",
        "LANDSCAPE_MUTATION=false",
        "NO_MAP_OF_TRUTH_MUTATION=true",
        "MERGE_AUTHORIZED_BY_THIS_PERSIST=false",
        "NEXT_IMPLEMENTATION_AUTHORIZED=false",
        "RUNTIME_AUTHORIZATION_EFFECT=NONE",
        "GET_EXECUTED_THIS_PERSIST=false",
        "POST_EXECUTED=false",
        "FLATTEN_EXECUTED=false",
    )
    for token in required:
        assert token in section, token


def test_wp_fs_b1_docs_forbid_activation_and_wp_fa_08_definition() -> None:
    section = _wp_fs_b1_section(_read(MASTER_RUNBOOK))
    forbidden = (
        "\nLIVE_AUTHORIZED=true\n",
        "\nCLASS_D_CONSUMED=true\n",
        "\nZ2AP_CONSUMED=true\n",
        "\nEXECUTION_READY=true\n",
        "\nPOST_EXECUTED=true\n",
        "\nFLATTEN_EXECUTED=true\n",
        "\nWP_FA_08_AUTHORIZED=true\n",
        "\nWP_FA_08_DEFINED_BY_THIS_PERSIST=true\n",
        "\nWP_FA_08_CANONICAL_DEFINITION_FOUND=true\n",
        "\nTHIS_GO_AUTHORIZES_WP_FA_08=true\n",
        "\nSUPERVISOR_HOST_ACTIVATION_AUTHORIZED=true\n",
        "\nAUTONOMY_SUPERVISOR_RUNTIME_REACHABILITY=true\n",
        "\nEXECUTION_PERMISSION_AUTHORIZED=true\n",
        "\nVENUE_EXECUTION_AUTHORIZED=true\n",
        "\nPRODUCTIVE_DEPLOYMENT_ALLOWED=true\n",
        "\nCURRENT_CANONICAL_SECTION_REPLACED=true\n",
        "\nATLAS_MUTATION=true\n",
        "\nLANDSCAPE_MUTATION=true\n",
        "\nMERGE_AUTHORIZED_BY_THIS_PERSIST=true\n",
        "WP_FA_08_EXACT_SCOPE=",
        "WORKPACKAGE_ID=WP_FA_08",
    )
    for token in forbidden:
        assert token not in section, token


def test_map_of_truth_has_no_wp_fs_b1_semantic_entry() -> None:
    text = _read(MAP_OF_TRUTH)
    assert "DOCUMENT_ROLE=NAVIGATION_ONLY_NO_SEMANTICS" in text
    assert "WP-FS-B1" not in text
    assert "WP_FS_B1" not in text
    assert "Z2DA" not in text


def test_atlas_census_distinguishes_current_repo_sha_from_historical_evidence_sha() -> None:
    meta = _read(CENSUS_META)
    assert f"origin_main_sha: {WP_FS_B1_GIT_MERGE_SHA}" in meta
    assert f"navigation_rebind_sha: {WP_FS_B1_GIT_MERGE_SHA}" in meta
    assert f"domain_census_payloads_bound_sha: {HISTORICAL_EVIDENCE_SHA}" in meta
    assert "domain_census_payloads_fresh_exhaustive_recensus: false" in meta
    assert WP_FS_B1_GIT_MERGE_SHA != HISTORICAL_EVIDENCE_SHA
    assert f"origin_main_sha: {PRIOR_CENSUS_SHA}" not in meta
    assert f"domain_census_payloads_bound_sha: {WP_FS_B1_GIT_MERGE_SHA}" not in meta
