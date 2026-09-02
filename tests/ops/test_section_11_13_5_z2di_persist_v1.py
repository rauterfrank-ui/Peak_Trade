"""§11.13.5.Z2DI persist invariants for the Post-Z2DH dual-401 census SSOT."""

from __future__ import annotations

import json
from pathlib import Path

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    LIVE_ARMED,
    LIVE_AUTHORIZED,
    LIVE_ENABLED,
    SUBMIT_UNLOCKED,
    TESTNET_AUTHORIZED,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.evidence_v1 import (
    verify_manifest_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
MASTER_RUNBOOK = REPO_ROOT / "docs" / "runbooks" / "canonical" / "PEAK_TRADE_MASTER_RUNBOOK.md"
MAP_OF_TRUTH = REPO_ROOT / "docs" / "governance" / "PEAK_TRADE_MAP_OF_TRUTH.md"
ATLAS_CATALOG = REPO_ROOT / "docs" / "system_atlas" / "entities" / "catalog.yaml"
ATLAS_AUTHORITY = REPO_ROOT / "docs" / "system_atlas" / "ATLAS_AUTHORITY_AND_USAGE.md"
Z2DG_EVIDENCE_PACK = (
    REPO_ROOT
    / "evidence"
    / "ops"
    / "section_11_13_5_z2dg_single_actual_read_only_funding_balance_get_v1"
    / "20260902T134821Z"
)
Z2DH_EVIDENCE_PACK = (
    REPO_ROOT
    / "evidence"
    / "ops"
    / "section_11_13_5_z2dh_single_actual_read_only_funding_balance_get_v1"
    / "20260902T143840Z"
)

Z2DH_HEADING = "### 11.13.5.Z2DH Single actual read-only Funding Account balance GET"
Z2DI_HEADING = "### 11.13.5.Z2DI Post-Z2DH dual-401 whitelist-block census SSOT persist"
Z2DJ_HEADING = "### 11.13.5.Z2DJ OKX EEA API-key IP whitelist management-plane reconcile"
Z2DK_HEADING = "### 11.13.5.Z2DK GET redirect fail-closed on existing canary urllib transport"
Z2DL_HEADING = "### 11.13.5.Z2DL Post-remediation single private authenticated GET"
LADDER_HEADING = "## 11.14 Live order and economic evidence ladder"
OWNER_GO = "PEAK_TRADE_OWNER_GO_Z2DI_POST_Z2DH_DUAL_401_WHITELIST_BLOCK_CENSUS_SSOT_PERSIST_V1"
BASELINE_SHA = "52d144bff3214c000fcdd3b5cac40f2b568a891d"
Z2DH_PARENT_SHA = "79bb087a8531714b1fdb8d65d4077bc31068b67b"
BOUND_BODY_SHA256 = "4a8bfe0808942b74465e052a2ab6e8440d9a477be4abfdf42611ace7e3684730"
NEXT_BOUNDARY = (
    "SEPARATE_OWNER_GO_REQUIRED_BEFORE_ANY_FURTHER_PRIVATE_GET_OR_"
    "IP_WHITELIST_MUTATION_OR_CREDENTIAL_EGRESS_CHANGE"
)


def _read(path: Path) -> str:
    assert path.is_file(), f"missing canonical path: {path}"
    return path.read_text(encoding="utf-8")


def _z2di_section(text: str) -> str:
    start = text.find(Z2DI_HEADING)
    assert start >= 0, "missing §11.13.5.Z2DI heading"
    end = text.find(Z2DJ_HEADING, start)
    assert end > start, "missing §11.13.5.Z2DJ boundary after Z2DI"
    return text[start:end]


def _z2dh_section(text: str) -> str:
    start = text.find(Z2DH_HEADING)
    assert start >= 0, "missing §11.13.5.Z2DH heading"
    end = text.find(Z2DI_HEADING, start)
    assert end > start, "missing §11.13.5.Z2DI boundary after Z2DH"
    return text[start:end]


def _snapshot(pack: Path) -> dict[str, object]:
    return json.loads((pack / "GET_SNAPSHOT.sanitized.json").read_text(encoding="utf-8"))


def test_z2di_heading_is_unique_and_follows_z2dh() -> None:
    text = _read(MASTER_RUNBOOK)
    assert text.count(Z2DI_HEADING) == 1
    assert (
        0
        <= text.find(Z2DH_HEADING)
        < text.find(Z2DI_HEADING)
        < text.find(Z2DJ_HEADING)
        < text.find(Z2DK_HEADING)
        < text.find(Z2DL_HEADING)
        < text.find(LADDER_HEADING)
    )


def test_z2dh_text_was_not_rewritten() -> None:
    section = _z2dh_section(_read(MASTER_RUNBOOK))
    assert "THIS_SLICE=11.13.5.Z2DH" in section
    assert "FUNDING_BALANCE_GET_EXECUTED=true" in section
    assert "LAST_CANONICALLY_CLOSED_STEP=SECTION_11_13_5_Z2DH" in section
    assert "HTTP_STATUS=401" in section
    assert "VENUE_CODE=50110" in section
    assert "11.13.5.Z2DI" not in section
    assert OWNER_GO not in section
    assert "11.13.5.Z2DJ" not in section


def test_z2di_text_excludes_z2dj_tokens() -> None:
    section = _z2di_section(_read(MASTER_RUNBOOK))
    assert "11.13.5.Z2DJ" not in section
    assert "PEAK_TRADE_OWNER_GO_Z2DJ_OKX_API_KEY_IP_WHITELIST_RECONCILE_V1" not in section
    assert "WHITELIST_MUTATION_CONFIRMED=true" not in section


def test_z2di_docs_bind_census_without_get_or_activation() -> None:
    section = _z2di_section(_read(MASTER_RUNBOOK))
    required = (
        "AUTHORIZED_SCOPE=A_Z2DI_ADDITIVE_DOCS_TESTS_ATLAS_NAVIGATION_PERSIST_ONLY",
        "Z2DI_SCOPE=POST_Z2DH_LOCAL_CENSUS_SSOT_PERSIST_ONLY",
        f"OWNER_GO={OWNER_GO}",
        "OWNER_GO_STATUS=CONSUMED",
        f"CURRENT_ORIGIN_MAIN_SHA={BASELINE_SHA}",
        f"Z2DH_SQUASH_SHA={BASELINE_SHA}",
        f"Z2DH_PARENT_SHA={Z2DH_PARENT_SHA}",
        "LAST_MERGED_PR=6220",
        "PREDECESSOR_SLICE=11.13.5.Z2DH",
        "THIS_SLICE=11.13.5.Z2DI",
        "LAST_CANONICALLY_CLOSED_STEP=SECTION_11_13_5_Z2DI",
        f"Z2DG_BODY_SHA256={BOUND_BODY_SHA256}",
        f"Z2DH_BODY_SHA256={BOUND_BODY_SHA256}",
        "DUAL_401_BODY_SHA256_IDENTITY=true",
        "DUAL_401_IDENTITY_MEANS_IDENTICAL_OBSERVED_RESPONSE_BODY_HASH_ONLY=true",
        "DUAL_401_IDENTITY_DOES_NOT_PROVE_OTHER_ENDPOINTS=true",
        "DUAL_401_IDENTITY_DOES_NOT_PROVE_TIME_STABILITY=true",
        "DUAL_401_IDENTITY_DOES_NOT_PROVE_CREDENTIAL_STABILITY=true",
        "FUNDING_BALANCE_GET_SUCCESS=false",
        "BALANCES_OBSERVED=false",
        "POST_AUTH_VIABILITY=UNPROVEN",
        "PREREQUISITE_08_CLOSED=false",
        "CLASS_D_CONSUMED=false",
        "Z2AP_CONSUMED=false",
        "EXECUTION_READY=false",
        "CANONICAL_LIVE_NEXT_POINTER_CHANGED=false",
        "LIVE_TRACK_CANONICAL_NEXT_POINTER_UNCHANGED=true",
        "THIS_GO_DOES_NOT_REPLACE_LIVE_TRACK_POINTER=true",
        "P3_INDEPENDENT_PARALLEL_TRACKS_POLICY=true",
        "EARLIEST_Z2DH_STRAND_EXTERNAL_DEPENDENCY=API_KEY_IP_WHITELIST_BLOCK_OKX_50110",
        "EARLIEST_Z2DH_STRAND_EXTERNAL_DEPENDENCY_AUTHORITY_CLASS=G_EXTERNAL_IP_WHITELIST_MUTATION",
        "POSITIONS_GET_EXECUTED_THIS_PERSIST=false",
        "POSITIONS_GET_50110_PROVEN=false",
        "SHARED_AUTHENTICATED_PRIVATE_GET_50110_BLOCKER=HYPOTHESIS_NOT_PROVEN",
        "WHITELIST_SUCCESS_CLAIMED=false",
        "GET_COUNT=0",
        "GET_EXECUTED_THIS_PERSIST=false",
        "THIRD_FUNDING_GET_AUTHORIZED=false",
        "POST_EXECUTED=false",
        "TRANSFER_EXECUTED=false",
        "CAPITAL_MOVEMENT_AUTHORIZED=false",
        "LIVE_AUTHORIZED=false",
        "TESTNET_AUTHORIZED=false",
        "CANARY_AUTHORIZED=false",
        "SUBMIT_UNLOCKED=false",
        "WHITELIST_MUTATION_ALLOWED=false",
        "WHITELIST_MUTATION_PERFORMED=false",
        "SECRETREF_CHANGE_AUTHORIZED=false",
        "CREDENTIAL_MUTATION_AUTHORIZED=false",
        "EGRESS_CHANGE_AUTHORIZED=false",
        "Z2DH_RUNTIME_CONSUMER_CREATED=false",
        "Z2DI_RUNTIME_CONSUMER_CREATED=false",
        "NO_CONSUMER_GAP_REPAIRED=false",
        "Z2DH_TEXT_REWRITTEN=false",
        "Z2DG_TEXT_REWRITTEN=false",
        "Z2DG_EVIDENCE_REWRITTEN=false",
        "Z2DH_EVIDENCE_REWRITTEN=false",
        "NEW_VENUE_EVIDENCE_CREATED=false",
        "NO_MAP_OF_TRUTH_MUTATION=true",
        "ATLAS_AUTHORITY=NONE",
        "ATLAS_ROLE=NAVIGATION_INDEX_ONLY",
        "ATLAS_MUTATION=false",
        "ATLAS_SEMANTIC_AUTHORITY_CREATED=false",
        "ATLAS_RUNTIME_CONSUMER_CREATED=false",
        "LANDSCAPE_AUTHORITY=NONE",
        "MERGE_AUTHORIZED_BY_THIS_PERSIST=false",
        "Z2DI_DOES_NOT_CLAIM_POSITIONS_GET_50110=true",
        "Z2DI_ADJUDICATES_Z2DH_FUNDING_BALANCE_SUBSTRAND_ONLY=true",
        f"NEXT_AUTHORITY_BOUNDARY={NEXT_BOUNDARY}",
    )
    for token in required:
        assert token in section, token


def test_z2di_docs_forbid_activation_retry_and_overclaim() -> None:
    section = _z2di_section(_read(MASTER_RUNBOOK))
    forbidden = (
        "\nLIVE_AUTHORIZED=true\n",
        "\nTESTNET_AUTHORIZED=true\n",
        "\nCANARY_AUTHORIZED=true\n",
        "\nORDERS_ALLOWED=true\n",
        "\nSUBMIT_UNLOCKED=true\n",
        "\nPOST_EXECUTED=true\n",
        "\nTRANSFER_EXECUTED=true\n",
        "\nFUNDING_BALANCE_GET_SUCCESS=true\n",
        "\nBALANCES_OBSERVED=true\n",
        "\nPREREQUISITE_08_CLOSED=true\n",
        "\nCLASS_D_CONSUMED=true\n",
        "\nZ2AP_CONSUMED=true\n",
        "\nEXECUTION_READY=true\n",
        "\nCAPITAL_MOVEMENT_AUTHORIZED=true\n",
        "\nGET_EXECUTED_THIS_PERSIST=true\n",
        "\nTHIRD_FUNDING_GET_AUTHORIZED=true\n",
        "\nWHITELIST_MUTATION_ALLOWED=true\n",
        "\nWHITELIST_MUTATION_PERFORMED=true\n",
        "\nWHITELIST_SUCCESS_CLAIMED=true\n",
        "\nPOSITIONS_GET_50110_PROVEN=true\n",
        "\nSECRETREF_CHANGE_AUTHORIZED=true\n",
        "\nCREDENTIAL_MUTATION_AUTHORIZED=true\n",
        "\nEGRESS_CHANGE_AUTHORIZED=true\n",
        "\nZ2DH_RUNTIME_CONSUMER_CREATED=true\n",
        "\nNO_CONSUMER_GAP_REPAIRED=true\n",
        "\nMERGE_AUTHORIZED_BY_THIS_PERSIST=true\n",
        "\nZ2DH_TEXT_REWRITTEN=true\n",
        "\nCANONICAL_LIVE_NEXT_POINTER_CHANGED=true\n",
        "\nTHIS_GO_DOES_NOT_REPLACE_LIVE_TRACK_POINTER=false\n",
        "\nATLAS_AUTHORITY=CANONICAL\n",
        "\nLANDSCAPE_AUTHORITY=SSOT\n",
    )
    for token in forbidden:
        assert token not in section, token
    assert "also returns 50110" not in section.lower()
    assert "positions GET likewise" not in section
    assert "whitelist success" not in section.lower()
    assert "RETRY_ALLOWED=true" not in section
    assert "THIS_GO_AUTHORIZES_GET=true" not in section
    assert "THIS_GO_AUTHORIZES_POST=true" not in section
    assert "THIS_GO_AUTHORIZES_TRANSFER=true" not in section
    assert "EXECUTE_AUTHORIZED=true" not in section


def test_map_of_truth_has_no_z2di_semantic_entry() -> None:
    text = _read(MAP_OF_TRUTH)
    assert "DOCUMENT_ROLE=NAVIGATION_ONLY_NO_SEMANTICS" in text
    assert "Z2DI" not in text
    assert "11.13.5.Z2DI" not in text
    assert "DUAL_401" not in text


def test_existing_evidence_packs_bind_identical_body_sha256() -> None:
    z2dg = _snapshot(Z2DG_EVIDENCE_PACK)
    z2dh = _snapshot(Z2DH_EVIDENCE_PACK)
    assert z2dg["BODY_SHA256"] == BOUND_BODY_SHA256
    assert z2dh["BODY_SHA256"] == BOUND_BODY_SHA256
    assert z2dg["BODY_SHA256"] == z2dh["BODY_SHA256"]
    assert z2dg["AUTHORIZED_ENDPOINT"] == "GET /api/v5/asset/balances"
    assert z2dh["AUTHORIZED_ENDPOINT"] == "GET /api/v5/asset/balances"
    assert int(verify_manifest_v1(Z2DG_EVIDENCE_PACK)["MANIFEST_VERIFY_RC"]) == 0
    assert int(verify_manifest_v1(Z2DH_EVIDENCE_PACK)["MANIFEST_VERIFY_RC"]) == 0
    z2dg_summary = json.loads((Z2DG_EVIDENCE_PACK / "SUMMARY.json").read_text(encoding="utf-8"))
    z2dh_summary = json.loads((Z2DH_EVIDENCE_PACK / "SUMMARY.json").read_text(encoding="utf-8"))
    assert z2dg_summary["HTTP_STATUS"] == 401
    assert z2dh_summary["HTTP_STATUS"] == 401
    z2dg_snap_text = _read(Z2DG_EVIDENCE_PACK / "GET_SNAPSHOT.sanitized.json")
    z2dh_snap_text = _read(Z2DH_EVIDENCE_PACK / "GET_SNAPSHOT.sanitized.json")
    assert '"VENUE_CODE": "50110"' in z2dg_snap_text
    assert '"VENUE_CODE": "50110"' in z2dh_snap_text
    z2dg_claims = _read(Z2DG_EVIDENCE_PACK / "claims.json")
    z2dh_claims = _read(Z2DH_EVIDENCE_PACK / "claims.json")
    assert '"PREREQUISITE_08_CLOSED": false' in z2dg_claims
    assert '"PREREQUISITE_08_CLOSED": false' in z2dh_claims
    assert '"POST_ALLOWED": false' in z2dg_claims
    assert '"POST_ALLOWED": false' in z2dh_claims
    assert '"TRANSFER_ALLOWED": false' in z2dg_claims
    assert '"TRANSFER_ALLOWED": false' in z2dh_claims
    assert '"RETRY_ALLOWED": false' in z2dh_claims
    assert '"WHITELIST_MUTATION_ALLOWED": false' in z2dh_claims


def test_standing_live_flags_remain_false() -> None:
    assert LIVE_AUTHORIZED is False
    assert TESTNET_AUTHORIZED is False
    assert LIVE_ENABLED is False
    assert LIVE_ARMED is False
    assert SUBMIT_UNLOCKED is False


def test_atlas_z2dh_entry_remains_navigation_only() -> None:
    catalog = _read(ATLAS_CATALOG)
    authority = _read(ATLAS_AUTHORITY)
    assert "ATLAS_AUTHORITY=NONE" in authority
    assert "id: RUNTIME_COMPONENT:z2dh_single_actual_read_only_funding_balance_get_v1" in catalog
    start = catalog.find(
        "id: RUNTIME_COMPONENT:z2dh_single_actual_read_only_funding_balance_get_v1"
    )
    end = catalog.find("\n  - id:", start + 1)
    block = catalog[start:] if end < 0 else catalog[start:end]
    assert "current_canonical: false" in block
    assert "ATLAS_AUTHORITY=NONE" in block
    assert "No runtime consumer" in block
    assert "kind: RUNTIME_COMPONENT:z2di" not in catalog
    assert "RUNTIME_COMPONENT:z2di_" not in catalog
