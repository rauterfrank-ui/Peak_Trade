"""§11.13.5.Z2DJ persist invariants for the OKX EEA IP-whitelist reconcile."""

from __future__ import annotations

from pathlib import Path

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    LIVE_ARMED,
    LIVE_AUTHORIZED,
    LIVE_ENABLED,
    REQUIRED_CREDENTIAL_CLASS,
    REQUIRED_SECRETREF_URI,
    SUBMIT_UNLOCKED,
    TESTNET_AUTHORIZED,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
MASTER_RUNBOOK = REPO_ROOT / "docs" / "runbooks" / "canonical" / "PEAK_TRADE_MASTER_RUNBOOK.md"
MAP_OF_TRUTH = REPO_ROOT / "docs" / "governance" / "PEAK_TRADE_MAP_OF_TRUTH.md"
ATLAS_CATALOG = REPO_ROOT / "docs" / "system_atlas" / "entities" / "catalog.yaml"
ATLAS_AUTHORITY = REPO_ROOT / "docs" / "system_atlas" / "ATLAS_AUTHORITY_AND_USAGE.md"

Z2DI_HEADING = "### 11.13.5.Z2DI Post-Z2DH dual-401 whitelist-block census SSOT persist"
Z2DJ_HEADING = "### 11.13.5.Z2DJ OKX EEA API-key IP whitelist management-plane reconcile"
Z2DK_HEADING = "### 11.13.5.Z2DK GET redirect fail-closed on existing canary urllib transport"
Z2DL_HEADING = "### 11.13.5.Z2DL Post-remediation single private authenticated GET"
LADDER_HEADING = "## 11.14 Live order and economic evidence ladder"
OWNER_GO = "PEAK_TRADE_OWNER_GO_Z2DJ_OKX_API_KEY_IP_WHITELIST_RECONCILE_V1"
Z2DI_OWNER_GO = "PEAK_TRADE_OWNER_GO_Z2DI_POST_Z2DH_DUAL_401_WHITELIST_BLOCK_CENSUS_SSOT_PERSIST_V1"
BASELINE_SHA = "14b55ba6d50df55ab49f2a18b8be062152f88eb5"
NEXT_BOUNDARY = "SEPARATE_OWNER_GO_REQUIRED_FOR_POST_WHITELIST_SINGLE_PRIVATE_AUTHENTICATED_GET"
SECRETREF = "secretref://vault/peak-trade/live-canary-minimum-exposure/okx"
VAULT_KEY_SHA256 = "36c6b5691f1b0dd20ec0627ce234a97c4d69a3aaba8887ed5bca216bc4fd23c7"
TARGET_EGRESS = "84.141.69.36"
WHITELIST_PRE_STATE = "84.140.105.223,2.161.34.181"
WHITELIST_POST_STATE = "84.140.105.223,2.161.34.181,84.141.69.36"


def _read(path: Path) -> str:
    assert path.is_file(), f"missing canonical path: {path}"
    return path.read_text(encoding="utf-8")


def _z2dj_section(text: str) -> str:
    start = text.find(Z2DJ_HEADING)
    assert start >= 0, "missing §11.13.5.Z2DJ heading"
    end = text.find(Z2DK_HEADING, start)
    assert end > start, "missing §11.13.5.Z2DK boundary after Z2DJ"
    return text[start:end]


def _z2di_section(text: str) -> str:
    start = text.find(Z2DI_HEADING)
    assert start >= 0, "missing §11.13.5.Z2DI heading"
    end = text.find(Z2DJ_HEADING, start)
    assert end > start, "missing §11.13.5.Z2DJ boundary after Z2DI"
    return text[start:end]


def test_z2dj_heading_is_unique_and_follows_z2di() -> None:
    text = _read(MASTER_RUNBOOK)
    assert text.count(Z2DJ_HEADING) == 1
    assert (
        0
        <= text.find(Z2DI_HEADING)
        < text.find(Z2DJ_HEADING)
        < text.find(Z2DK_HEADING)
        < text.find(Z2DL_HEADING)
        < text.find(LADDER_HEADING)
    )


def test_z2di_text_was_not_rewritten() -> None:
    section = _z2di_section(_read(MASTER_RUNBOOK))
    assert "THIS_SLICE=11.13.5.Z2DI" in section
    assert f"OWNER_GO={Z2DI_OWNER_GO}" in section
    assert "LAST_CANONICALLY_CLOSED_STEP=SECTION_11_13_5_Z2DI" in section
    assert "WHITELIST_MUTATION_PERFORMED=false" in section
    assert "WHITELIST_MUTATION_ALLOWED=false" in section
    assert "11.13.5.Z2DJ" not in section
    assert OWNER_GO not in section
    assert "11.13.5.Z2DK" not in section


def test_z2dj_docs_bind_management_plane_whitelist_without_get_or_activation() -> None:
    section = _z2dj_section(_read(MASTER_RUNBOOK))
    required = (
        "AUTHORIZED_SCOPE=A_Z2DJ_OKX_EEA_API_KEY_IP_WHITELIST_MANAGEMENT_PLANE_RECONCILE_ONLY",
        "Z2DJ_SCOPE=OKX_EEA_API_KEY_IP_WHITELIST_MANAGEMENT_PLANE_RECONCILIATION_ONLY",
        f"OWNER_GO={OWNER_GO}",
        "OWNER_GO_STATUS=CONSUMED",
        f"CURRENT_ORIGIN_MAIN_SHA={BASELINE_SHA}",
        f"Z2DI_SQUASH_SHA={BASELINE_SHA}",
        "LAST_MERGED_PR=6221",
        "PREDECESSOR_SLICE=11.13.5.Z2DI",
        "THIS_SLICE=11.13.5.Z2DJ",
        "LAST_CANONICALLY_CLOSED_STEP=SECTION_11_13_5_Z2DJ",
        f"TARGET_SECRETREF={SECRETREF}",
        "TARGET_CREDENTIAL_CLASS=LIVE_CANARY_MINIMUM_EXPOSURE_TRADE_API_KEY",
        "TARGET_UI_KEY_NAME=PeakTrade-Live-Canary-MinExp",
        f"TARGET_VAULT_KEY_SHA256={VAULT_KEY_SHA256}",
        f"WHITELIST_PRE_STATE={WHITELIST_PRE_STATE}",
        f"WHITELIST_POST_STATE={WHITELIST_POST_STATE}",
        f"TARGET_EGRESS={TARGET_EGRESS}",
        "EXISTING_WHITELIST_IPS_PRESERVED=true",
        "UNEXPECTED_WHITELIST_IP_ADDED=false",
        "OTHER_API_KEY_CHANGED=false",
        "WHITELIST_MUTATION_CONFIRMED=true",
        "WHITELIST_MUTATION_PERFORMED=true",
        "READ_PERMISSION_UNCHANGED=true",
        "TRADE_PERMISSION_UNCHANGED=true",
        "WITHDRAW_PERMISSION_UNCHANGED=true",
        "READ_PERMISSION=true",
        "TRADE_PERMISSION=true",
        "WITHDRAW_PERMISSION=false",
        "SECRETREF_CHANGED=false",
        "CREDENTIAL_CHANGED=false",
        "API_KEY_ROTATED=false",
        "EGRESS_ARCHITECTURE_CHANGED=false",
        "PRIVATE_GET_PERFORMED=false",
        "FUNDING_GET_PERFORMED=false",
        "POSITIONS_GET_PERFORMED=false",
        "GET_COUNT=0",
        "GET_EXECUTED_THIS_PERSIST=false",
        "POST_EXECUTED=false",
        "PRIVATE_API_AUTH_SUCCESS=UNPROVEN",
        "POST_AUTH_VIABILITY=UNPROVEN",
        "RUNTIME_50110_CLEARANCE=NOT_TESTED",
        "FUNDING_BALANCE_GET_SUCCESS_AFTER_WHITELIST=UNPROVEN",
        "FUNDING_BALANCE_GET_SUCCESS=false",
        "BALANCES_OBSERVED=false",
        "PREREQUISITE_08_CLOSED=false",
        "CLASS_D_CONSUMED=false",
        "Z2AP_CONSUMED=false",
        "EXECUTION_READY=false",
        "CANONICAL_LIVE_NEXT_POINTER_CHANGED=false",
        "LIVE_TRACK_CANONICAL_NEXT_POINTER_UNCHANGED=true",
        "THIS_GO_DOES_NOT_REPLACE_LIVE_TRACK_POINTER=true",
        "P3_INDEPENDENT_PARALLEL_TRACKS_POLICY=true",
        "LIVE_AUTHORIZED=false",
        "TESTNET_AUTHORIZED=false",
        "CANARY_AUTHORIZED=false",
        "SUBMIT_UNLOCKED=false",
        "Z2DJ_RUNTIME_CONSUMER_CREATED=false",
        "Z2DI_TEXT_REWRITTEN=false",
        "Z2DH_TEXT_REWRITTEN=false",
        "Z2DG_TEXT_REWRITTEN=false",
        "Z2DG_EVIDENCE_REWRITTEN=false",
        "Z2DH_EVIDENCE_REWRITTEN=false",
        "CORE_SEMANTICS_CHANGED=false",
        "NO_MAP_OF_TRUTH_MUTATION=true",
        "ATLAS_AUTHORITY=NONE",
        "ATLAS_ROLE=NAVIGATION_INDEX_ONLY",
        "ATLAS_MUTATION=false",
        "ATLAS_SEMANTIC_AUTHORITY_CREATED=false",
        "LANDSCAPE_AUTHORITY=NONE",
        "MERGE_AUTHORIZED_BY_THIS_PERSIST=false",
        "Z2DJ_DOES_NOT_CLAIM_PRIVATE_API_AUTH_SUCCESS=true",
        "Z2DJ_DOES_NOT_CLAIM_RUNTIME_50110_CLEARANCE=true",
        "Z2DJ_DOES_NOT_CLAIM_FUNDING_BALANCE_GET_SUCCESS=true",
        "Z2DJ_ADJUDICATES_MANAGEMENT_PLANE_WHITELIST_ONLY=true",
        f"NEXT_AUTHORITY_BOUNDARY={NEXT_BOUNDARY}",
    )
    for token in required:
        assert token in section, token
    assert "84.140.105.223" in section
    assert "2.161.34.181" in section
    assert TARGET_EGRESS in section


def test_z2dj_docs_forbid_activation_get_and_overclaim() -> None:
    section = _z2dj_section(_read(MASTER_RUNBOOK))
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
        "\nPRIVATE_GET_PERFORMED=true\n",
        "\nFUNDING_GET_PERFORMED=true\n",
        "\nPOSITIONS_GET_PERFORMED=true\n",
        "\nPRIVATE_API_AUTH_SUCCESS=true\n",
        "\nRUNTIME_50110_CLEARANCE=true\n",
        "\nRUNTIME_50110_CLEARANCE=TESTED\n",
        "\nSECRETREF_CHANGED=true\n",
        "\nCREDENTIAL_CHANGED=true\n",
        "\nAPI_KEY_ROTATED=true\n",
        "\nAPI_PERMISSION_CHANGED=true\n",
        "\nWITHDRAW_PERMISSION=true\n",
        "\nEGRESS_ARCHITECTURE_CHANGED=true\n",
        "\nUNEXPECTED_WHITELIST_IP_ADDED=true\n",
        "\nOTHER_API_KEY_CHANGED=true\n",
        "\nZ2DJ_RUNTIME_CONSUMER_CREATED=true\n",
        "\nMERGE_AUTHORIZED_BY_THIS_PERSIST=true\n",
        "\nZ2DI_TEXT_REWRITTEN=true\n",
        "\nCANONICAL_LIVE_NEXT_POINTER_CHANGED=true\n",
        "\nTHIS_GO_DOES_NOT_REPLACE_LIVE_TRACK_POINTER=false\n",
        "\nATLAS_AUTHORITY=CANONICAL\n",
        "\nLANDSCAPE_AUTHORITY=SSOT\n",
    )
    for token in forbidden:
        assert token not in section, token
    assert "50110 now cleared" not in section.lower()
    assert "private api auth success" not in section.lower()
    assert "RETRY_ALLOWED=true" not in section
    assert "THIS_GO_AUTHORIZES_GET=true" not in section
    assert "THIS_GO_AUTHORIZES_POST=true" not in section
    assert "EXECUTE_AUTHORIZED=true" not in section
    assert "api_secret" not in section.lower()
    assert "passphrase" not in section.lower()
    assert "ok-access-" not in section.lower()


def test_map_of_truth_has_no_z2dj_semantic_entry() -> None:
    text = _read(MAP_OF_TRUTH)
    assert "DOCUMENT_ROLE=NAVIGATION_ONLY_NO_SEMANTICS" in text
    assert "Z2DJ" not in text
    assert "11.13.5.Z2DJ" not in text


def test_standing_live_flags_and_secretref_identity_remain_unchanged() -> None:
    assert LIVE_AUTHORIZED is False
    assert TESTNET_AUTHORIZED is False
    assert LIVE_ENABLED is False
    assert LIVE_ARMED is False
    assert SUBMIT_UNLOCKED is False
    assert REQUIRED_SECRETREF_URI == SECRETREF
    assert REQUIRED_CREDENTIAL_CLASS == "LIVE_CANARY_MINIMUM_EXPOSURE_TRADE_API_KEY"


def test_atlas_z2dj_remains_navigation_only() -> None:
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
    assert "tests/ops/test_section_11_13_5_z2dj_persist_v1.py" in block
    assert "Additive §11.13.5.Z2DJ SSOT persist" in block
    assert "kind: RUNTIME_COMPONENT:z2dj" not in catalog
    assert "RUNTIME_COMPONENT:z2dj_" not in catalog
