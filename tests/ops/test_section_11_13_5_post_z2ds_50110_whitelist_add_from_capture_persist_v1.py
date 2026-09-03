"""Post-Z2DS captured-50110 whitelist-add persist invariants."""

from __future__ import annotations

import json
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
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.evidence_v1 import (
    verify_manifest_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_execute_authority_v1 import (
    FORBIDDEN_FLATTEN_EXECUTE_OWNER_GOS,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
MASTER_RUNBOOK = REPO_ROOT / "docs" / "runbooks" / "canonical" / "PEAK_TRADE_MASTER_RUNBOOK.md"
MAP_OF_TRUTH = REPO_ROOT / "docs" / "governance" / "PEAK_TRADE_MAP_OF_TRUTH.md"
ATLAS_CATALOG = REPO_ROOT / "docs" / "system_atlas" / "entities" / "catalog.yaml"
ATLAS_AUTHORITY = REPO_ROOT / "docs" / "system_atlas" / "ATLAS_AUTHORITY_AND_USAGE.md"
SPEC = REPO_ROOT / "docs/ops/specs/POST_Z2DS_CAPTURED_50110_EGRESS_IP_WHITELIST_MINIMUM_ADD_V1.md"
EVIDENCE_PACK = (
    REPO_ROOT
    / "evidence"
    / "ops"
    / "section_11_13_5_post_z2ds_50110_whitelist_add_from_capture_v1"
    / "20260903T175654Z"
)
SOURCE_PACK = (
    REPO_ROOT
    / "evidence"
    / "ops"
    / "section_11_13_5_post_z2ds_private_get_current_50110_egress_capture_v1"
    / "20260903T171133Z"
)

CAPTURE_HEADING = "### 11.13.5 Post-Z2DS one-shot private GET current 50110 egress capture persist"
WHITELIST_HEADING = "### 11.13.5 Post-Z2DS captured-50110 egress IP whitelist minimum add persist"
LADDER_HEADING = "## 11.14 Live order and economic evidence ladder"
OWNER_GO = "PEAK_TRADE_OWNER_GO_OKX_EEA_EXTERNAL_IP_WHITELIST_ADD_FROM_CAPTURED_50110_EVIDENCE_20260903T171133Z_V1"
SUPERSEDED_GO = (
    "PEAK_TRADE_OWNER_GO_OKX_EEA_EXTERNAL_IP_WHITELIST_MINIMUM_ADD_CURRENT_50110_EGRESS_V1"
)
SECRETREF = "secretref://vault/peak-trade/live-canary-minimum-exposure/okx"
VAULT_KEY_SHA256 = "36c6b5691f1b0dd20ec0627ce234a97c4d69a3aaba8887ed5bca216bc4fd23c7"
AUTHORIZED_IP = "176.5.200.177"
WHITELIST_PRE_STATE = "84.140.105.223,2.161.34.181,84.141.69.36"
WHITELIST_POST_STATE = "84.140.105.223,2.161.34.181,84.141.69.36,176.5.200.177"
NEXT_BOUNDARY = "SEPARATE_OWNER_GO_REQUIRED_BEFORE_ANY_PRIVATE_GET_OR_P08_OR_FUNDING_OR_EXECUTION"


def _read(path: Path) -> str:
    assert path.is_file(), f"missing canonical path: {path}"
    return path.read_text(encoding="utf-8")


def _section(text: str) -> str:
    start = text.find(WHITELIST_HEADING)
    assert start >= 0, "missing captured-50110 whitelist-add heading"
    end = text.find(LADDER_HEADING, start)
    assert end > start, "missing §11.14 boundary after whitelist-add persist"
    return text[start:end]


def test_whitelist_heading_is_unique_and_follows_capture() -> None:
    text = _read(MASTER_RUNBOOK)
    assert text.count(WHITELIST_HEADING) == 1
    assert (
        0 <= text.find(CAPTURE_HEADING) < text.find(WHITELIST_HEADING) < text.find(LADDER_HEADING)
    )


def test_capture_text_was_not_rewritten() -> None:
    text = _read(MASTER_RUNBOOK)
    start = text.find(CAPTURE_HEADING)
    end = text.find(WHITELIST_HEADING, start)
    section = text[start:end]
    assert "THIS_SLICE=11.13.5.POST_Z2DS_50110_EGRESS_CAPTURE" in section
    assert "WHITELIST_MUTATION_PERFORMED=false" in section
    assert OWNER_GO not in section


def test_whitelist_docs_bind_minimum_add_without_get_or_p08() -> None:
    section = _section(_read(MASTER_RUNBOOK))
    required = (
        "AUTHORIZED_SCOPE=A_POST_Z2DS_CAPTURED_50110_EGRESS_IP_WHITELIST_MINIMUM_ADD_ONLY",
        f"OWNER_GO={OWNER_GO}",
        "OWNER_GO_STATUS=CONSUMED",
        f"SUPERSEDED_GO={SUPERSEDED_GO}",
        "SUPERSEDED_GO_STATUS=SUPERSEDED_NOT_EXECUTED",
        "SUPERSEDED_GO_EXECUTED_SEPARATELY=false",
        "CURRENT_ORIGIN_MAIN_SHA=36e8d281d91c0423a22da3bfded5c6be803b17b5",
        "THIS_SLICE=11.13.5.POST_Z2DS_50110_WHITELIST_ADD_FROM_CAPTURE",
        "PREDECESSOR_SLICE=11.13.5.POST_Z2DS_50110_EGRESS_CAPTURE",
        "LAST_CANONICALLY_CLOSED_STEP=SECTION_11_13_5_POST_Z2DS_50110_WHITELIST_ADD_FROM_CAPTURE",
        "MUTATION_MODE=MINIMUM_ADD_ONLY",
        f"AUTHORIZED_IP={AUTHORIZED_IP}",
        f"WHITELIST_PRE_STATE={WHITELIST_PRE_STATE}",
        f"WHITELIST_POST_STATE={WHITELIST_POST_STATE}",
        "EXISTING_WHITELIST_IPS_PRESERVED=true",
        "UNEXPECTED_WHITELIST_IP_ADDED=false",
        "WHITELIST_MUTATION_PERFORMED=true",
        "WHITELIST_MUTATION_CONFIRMED=true",
        "PRIVATE_GET_PERFORMED=false",
        "PUBLIC_GET_PERFORMED=false",
        "POST_PERFORMED=false",
        "PREREQUISITE_08_CLOSED=false",
        "RUNTIME_50110_CLEARANCE=NOT_TESTED",
        "PRIVATE_API_AUTH_SUCCESS=UNPROVEN",
        "TARGET_UI_KEY_NAME=PeakTrade-Live-Canary-MinExp",
        f"TARGET_VAULT_KEY_SHA256={VAULT_KEY_SHA256}",
        "READ_PERMISSION=true",
        "TRADE_PERMISSION=true",
        "WITHDRAW_PERMISSION=false",
        "API_PERMISSION_CHANGED=false",
        "SECRETREF_CHANGED=false",
        "API_KEY_ROTATED=false",
        "NEW_RUNTIME_CONSUMER_CREATED=false",
        "MERGE_AUTHORIZED_BY_THIS_PERSIST=false",
        f"NEXT_AUTHORITY_BOUNDARY={NEXT_BOUNDARY}",
        (
            "EVIDENCE_PACK=evidence/ops/section_11_13_5_post_z2ds_50110_"
            "whitelist_add_from_capture_v1/20260903T175654Z"
        ),
        (
            "CAPTURE_SOURCE_PACK=evidence/ops/section_11_13_5_post_z2ds_private_get_"
            "current_50110_egress_capture_v1/20260903T171133Z"
        ),
        "ATLAS_AUTHORITY=NONE",
        "AUTHORIZED_IP_IS_STATIC_EGRESS_ARCHITECTURE=false",
    )
    for token in required:
        assert token in section, token


def test_whitelist_docs_forbid_overclaim() -> None:
    section = _section(_read(MASTER_RUNBOOK))
    forbidden = (
        "\nLIVE_AUTHORIZED=true\n",
        "\nCANARY_AUTHORIZED=true\n",
        "\nSUBMIT_UNLOCKED=true\n",
        "\nPREREQUISITE_08_CLOSED=true\n",
        "\nPRIVATE_GET_PERFORMED=true\n",
        "\nPUBLIC_GET_PERFORMED=true\n",
        "\nPOST_PERFORMED=true\n",
        "\nRUNTIME_50110_CLEARANCE=true\n",
        "\nRUNTIME_50110_CLEARANCE=TESTED\n",
        "\nPRIVATE_API_AUTH_SUCCESS=true\n",
        "\nAPI_PERMISSION_CHANGED=true\n",
        "\nWITHDRAW_PERMISSION=true\n",
        "\nAPI_KEY_ROTATED=true\n",
        "\nUNEXPECTED_WHITELIST_IP_ADDED=true\n",
        "\nOTHER_API_KEY_CHANGED=true\n",
        "\nMERGE_AUTHORIZED_BY_THIS_PERSIST=true\n",
        "\nNEW_RUNTIME_CONSUMER_CREATED=true\n",
        "\nATLAS_AUTHORITY=CANONICAL\n",
        "\nAUTHORIZED_IP_IS_STATIC_EGRESS_ARCHITECTURE=true\n",
        "\nSUPERSEDED_GO_EXECUTED_SEPARATELY=true\n",
    )
    for token in forbidden:
        assert token not in section, token
    assert "api_secret" not in section.lower()
    assert "passphrase" not in section.lower()
    assert "ok-access-" not in section.lower()


def test_map_of_truth_has_no_whitelist_add_semantic_entry() -> None:
    text = _read(MAP_OF_TRUTH)
    assert "DOCUMENT_ROLE=NAVIGATION_ONLY_NO_SEMANTICS" in text
    assert "POST_Z2DS_50110_WHITELIST_ADD_FROM_CAPTURE" not in text
    assert OWNER_GO not in text


def test_standing_flags_and_flatten_denylist() -> None:
    assert LIVE_AUTHORIZED is False
    assert TESTNET_AUTHORIZED is False
    assert LIVE_ENABLED is False
    assert LIVE_ARMED is False
    assert SUBMIT_UNLOCKED is False
    assert REQUIRED_SECRETREF_URI == SECRETREF
    assert REQUIRED_CREDENTIAL_CLASS == "LIVE_CANARY_MINIMUM_EXPOSURE_TRADE_API_KEY"
    assert OWNER_GO in FORBIDDEN_FLATTEN_EXECUTE_OWNER_GOS
    assert SUPERSEDED_GO in FORBIDDEN_FLATTEN_EXECUTE_OWNER_GOS


def test_atlas_whitelist_add_is_navigation_only() -> None:
    catalog = _read(ATLAS_CATALOG)
    authority = _read(ATLAS_AUTHORITY)
    assert "ATLAS_AUTHORITY=NONE" in authority
    assert "id: PHASE:post_z2ds_50110_whitelist_add_from_capture" in catalog
    assert "kind: RUNTIME_COMPONENT:post_z2ds_50110_whitelist_add" not in catalog


def test_evidence_packs_and_source_binding() -> None:
    assert EVIDENCE_PACK.is_dir()
    assert SOURCE_PACK.is_dir()
    verified = verify_manifest_v1(EVIDENCE_PACK)
    assert int(verified.get("MANIFEST_VERIFY_RC", 1)) == 0
    source_verified = verify_manifest_v1(SOURCE_PACK)
    assert int(source_verified.get("MANIFEST_VERIFY_RC", 1)) == 0
    claims = json.loads((EVIDENCE_PACK / "claims.json").read_text(encoding="utf-8"))
    assert claims["OWNER_GO"] == OWNER_GO
    assert claims["SECRET_VALUES_INCLUDED"] is False
    assert claims["WHITELIST_POST_STATE"] == WHITELIST_POST_STATE
    summary = json.loads((EVIDENCE_PACK / "SUMMARY.json").read_text(encoding="utf-8"))
    assert summary["AUTHORIZED_IP"] == AUTHORIZED_IP
    assert summary["WHITELIST_MUTATION_CONFIRMED"] is True
    assert summary["PRIVATE_GET_PERFORMED"] is False
    snapshot = json.loads(
        (EVIDENCE_PACK / "MANAGEMENT_PLANE.sanitized.json").read_text(encoding="utf-8")
    )
    assert snapshot["TARGET_UI_KEY_NAME"] == "PeakTrade-Live-Canary-MinExp"
    assert snapshot["WHITELIST_POST_STATE"] == WHITELIST_POST_STATE
    lowered = json.dumps(snapshot).lower()
    assert "api_secret" not in lowered
    assert "passphrase" not in lowered
    assert "ok-access-" not in lowered
    source_summary = json.loads((SOURCE_PACK / "SUMMARY.json").read_text(encoding="utf-8"))
    assert source_summary["OKX_REPORTED_EGRESS_IPV4"] == AUTHORIZED_IP
    assert source_summary["HTTP_STATUS"] == 401
    assert source_summary["OKX_CODE"] == "50110"


def test_spec_exists() -> None:
    assert SPEC.is_file()
    text = _read(SPEC)
    assert "WHITELIST_MUTATION_PERFORMED=true" in text
    assert AUTHORIZED_IP in text
    assert "RUNTIME_50110_CLEARANCE=NOT_TESTED" in text
