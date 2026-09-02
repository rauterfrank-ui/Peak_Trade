"""§11.13.5.Z2DK persist invariants for GET redirect fail-closed transport remediation."""

from __future__ import annotations

import inspect
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
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.http_client_v1 import (
    CanaryPostRedirectFailClosedHandler,
    LiveCanaryHttpClientV1,
    UrllibLiveCanaryTransportV1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.okx_live_canary_signer_v1 import (
    build_okx_live_canary_auth_headers_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
MASTER_RUNBOOK = REPO_ROOT / "docs" / "runbooks" / "canonical" / "PEAK_TRADE_MASTER_RUNBOOK.md"
MAP_OF_TRUTH = REPO_ROOT / "docs" / "governance" / "PEAK_TRADE_MAP_OF_TRUTH.md"
ATLAS_CATALOG = REPO_ROOT / "docs" / "system_atlas" / "entities" / "catalog.yaml"
ATLAS_AUTHORITY = REPO_ROOT / "docs" / "system_atlas" / "ATLAS_AUTHORITY_AND_USAGE.md"
HTTP_CLIENT = (
    REPO_ROOT
    / "src"
    / "ops"
    / "section_11_13_5_live_canary_minimum_exposure_v1"
    / "http_client_v1.py"
)

Z2DJ_HEADING = "### 11.13.5.Z2DJ OKX EEA API-key IP whitelist management-plane reconcile"
Z2DK_HEADING = "### 11.13.5.Z2DK GET redirect fail-closed on existing canary urllib transport"
Z2DL_HEADING = "### 11.13.5.Z2DL Post-remediation single private authenticated GET"
LADDER_HEADING = "## 11.14 Live order and economic evidence ladder"
OWNER_GO = "PEAK_TRADE_OWNER_GO_Z2DK_GET_REDIRECT_FAILCLOSED_TRANSPORT_REMEDIATION_V1"
Z2DJ_OWNER_GO = "PEAK_TRADE_OWNER_GO_Z2DJ_OKX_API_KEY_IP_WHITELIST_RECONCILE_V1"
Z2DK_WIRE_GO = "PEAK_TRADE_OWNER_GO_Z2DK_POST_WHITELIST_SINGLE_PRIVATE_AUTH_GET_V1"
BASELINE_SHA = "cd070c4c16c31f4e40bdeb315cf909f62b441e1c"
NEXT_BOUNDARY = "SEPARATE_OWNER_GO_REQUIRED_FOR_POST_REMEDIATION_SINGLE_PRIVATE_AUTHENTICATED_GET"
SECRETREF = "secretref://vault/peak-trade/live-canary-minimum-exposure/okx"


def _read(path: Path) -> str:
    assert path.is_file(), f"missing canonical path: {path}"
    return path.read_text(encoding="utf-8")


def _z2dk_section(text: str) -> str:
    start = text.find(Z2DK_HEADING)
    assert start >= 0, "missing §11.13.5.Z2DK heading"
    end = text.find(Z2DL_HEADING, start)
    assert end > start, "missing §11.13.5.Z2DL boundary after Z2DK"
    return text[start:end]


def _z2dj_section(text: str) -> str:
    start = text.find(Z2DJ_HEADING)
    assert start >= 0, "missing §11.13.5.Z2DJ heading"
    end = text.find(Z2DK_HEADING, start)
    assert end > start, "missing §11.13.5.Z2DK boundary after Z2DJ"
    return text[start:end]


def test_z2dk_heading_is_unique_and_follows_z2dj() -> None:
    text = _read(MASTER_RUNBOOK)
    assert text.count(Z2DK_HEADING) == 1
    assert (
        0
        <= text.find(Z2DJ_HEADING)
        < text.find(Z2DK_HEADING)
        < text.find(Z2DL_HEADING)
        < text.find(LADDER_HEADING)
    )


def test_z2dj_text_was_not_rewritten() -> None:
    section = _z2dj_section(_read(MASTER_RUNBOOK))
    assert "THIS_SLICE=11.13.5.Z2DJ" in section
    assert f"OWNER_GO={Z2DJ_OWNER_GO}" in section
    assert "LAST_CANONICALLY_CLOSED_STEP=SECTION_11_13_5_Z2DJ" in section
    assert "WHITELIST_MUTATION_PERFORMED=true" in section
    assert "PRIVATE_GET_PERFORMED=false" in section
    assert "11.13.5.Z2DK" not in section
    assert OWNER_GO not in section
    assert "11.13.5.Z2DL" not in section


def test_z2dk_docs_bind_transport_remediation_without_get_or_activation() -> None:
    section = _z2dk_section(_read(MASTER_RUNBOOK))
    required = (
        "AUTHORIZED_SCOPE=A_Z2DK_GET_REDIRECT_FAILCLOSED_TRANSPORT_REMEDIATION_ONLY",
        "Z2DK_SCOPE=EXISTING_CANARY_GET_TRANSPORT_REDIRECT_FAILCLOSED_ONLY",
        f"OWNER_GO={OWNER_GO}",
        "OWNER_GO_STATUS=CONSUMED",
        f"Z2DK_WIRE_GO={Z2DK_WIRE_GO}",
        "Z2DK_WIRE_GO_STATUS=STILL_NOT_CONSUMED",
        "Z2DK_WIRE_GO_CONSUMED=false",
        f"CURRENT_ORIGIN_MAIN_SHA={BASELINE_SHA}",
        f"Z2DJ_SQUASH_SHA={BASELINE_SHA}",
        "LAST_MERGED_PR=6222",
        "PREDECESSOR_SLICE=11.13.5.Z2DJ",
        "THIS_SLICE=11.13.5.Z2DK",
        "LAST_CANONICALLY_CLOSED_STEP=SECTION_11_13_5_Z2DK",
        "AFFECTED_OWNER=UrllibLiveCanaryTransportV1",
        "REUSED_REDIRECT_HANDLER=CanaryPostRedirectFailClosedHandler",
        "NEW_TRANSPORT_CLASS_CREATED=false",
        "NEW_AUTH_SIGNING_IMPLEMENTATION=false",
        "AUTH_SIGNING_OWNER_CHANGED=false",
        "SECRETREF_CHANGED=false",
        "GET_REDIRECT_AUTO_FOLLOW_BEFORE=true",
        "GET_REDIRECT_AUTO_FOLLOW_AFTER=false",
        "GET_REDIRECT_AUTO_FOLLOW=false",
        "GET_REDIRECT_FAILCLOSED=true",
        "POST_REDIRECT_FAILCLOSED=true",
        "MAX_HTTP_EXCHANGES_PER_SEND=1",
        "HIDDEN_RETRY_PRESENT=false",
        "FALLBACK_REQUEST_PRESENT=false",
        "POST_BEHAVIOR_REGRESSION=false",
        "POST_REACHABLE_FROM_GET_EXECUTE_PATH=false",
        "ORDER_REACHABLE=false",
        "EXECUTION_REACHABLE=false",
        "LIVE_ARMING_REACHABLE=false",
        "PRIVATE_GET_PERFORMED=false",
        "FUNDING_GET_PERFORMED=false",
        "POSITIONS_GET_PERFORMED=false",
        "GET_COUNT=0",
        "GET_EXECUTED_THIS_PERSIST=false",
        "POST_EXECUTED=false",
        "PRIVATE_API_AUTH_SUCCESS=UNPROVEN",
        "RUNTIME_50110_CLEARANCE=NOT_TESTED",
        "PREREQUISITE_08_CLOSED=false",
        "CLASS_D_CONSUMED=false",
        "Z2AP_CONSUMED=false",
        "EXECUTION_READY=false",
        "CANONICAL_LIVE_NEXT_POINTER_CHANGED=false",
        "LIVE_AUTHORIZED=false",
        "TESTNET_AUTHORIZED=false",
        "CANARY_AUTHORIZED=false",
        "SUBMIT_UNLOCKED=false",
        "Z2DK_RUNTIME_CONSUMER_CREATED=false",
        "Z2DJ_TEXT_REWRITTEN=false",
        "Z2DH_TEXT_REWRITTEN=false",
        "Z2DG_EVIDENCE_REWRITTEN=false",
        "Z2DH_EVIDENCE_REWRITTEN=false",
        "WHITELIST_MUTATION_PERFORMED=false",
        "NO_MAP_OF_TRUTH_MUTATION=true",
        "ATLAS_AUTHORITY=NONE",
        "ATLAS_ROLE=NAVIGATION_INDEX_ONLY",
        "MERGE_AUTHORIZED_BY_THIS_PERSIST=false",
        "Z2DK_DOES_NOT_CLAIM_PRIVATE_API_AUTH_SUCCESS=true",
        "Z2DK_ADJUDICATES_GET_REDIRECT_FAILCLOSED_ONLY=true",
        f"NEXT_AUTHORITY_BOUNDARY={NEXT_BOUNDARY}",
    )
    for token in required:
        assert token in section, token
    assert "11.13.5.Z2DL" not in section
    assert "PEAK_TRADE_OWNER_GO_Z2DL_POST_REMEDIATION_SINGLE_PRIVATE_AUTH_GET_V1" not in section


def test_z2dk_docs_forbid_activation_get_and_overclaim() -> None:
    section = _z2dk_section(_read(MASTER_RUNBOOK))
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
        "\nGET_EXECUTED_THIS_PERSIST=true\n",
        "\nPRIVATE_GET_PERFORMED=true\n",
        "\nFUNDING_GET_PERFORMED=true\n",
        "\nPOSITIONS_GET_PERFORMED=true\n",
        "\nPRIVATE_API_AUTH_SUCCESS=true\n",
        "\nRUNTIME_50110_CLEARANCE=true\n",
        "\nZ2DK_WIRE_GO_CONSUMED=true\n",
        "\nZ2DK_WIRE_GO_STATUS=CONSUMED\n",
        "\nGET_REDIRECT_AUTO_FOLLOW=true\n",
        "\nNEW_TRANSPORT_CLASS_CREATED=true\n",
        "\nAUTH_SIGNING_OWNER_CHANGED=true\n",
        "\nSECRETREF_CHANGED=true\n",
        "\nWHITELIST_MUTATION_PERFORMED=true\n",
        "\nZ2DK_RUNTIME_CONSUMER_CREATED=true\n",
        "\nMERGE_AUTHORIZED_BY_THIS_PERSIST=true\n",
        "\nZ2DJ_TEXT_REWRITTEN=true\n",
        "\nCANONICAL_LIVE_NEXT_POINTER_CHANGED=true\n",
        "\nATLAS_AUTHORITY=CANONICAL\n",
        "\nLANDSCAPE_AUTHORITY=SSOT\n",
    )
    for token in forbidden:
        assert token not in section, token
    assert "private api auth success" not in section.lower()
    assert "RETRY_ALLOWED=true" not in section
    assert "THIS_GO_AUTHORIZES_GET=true" not in section
    assert "THIS_GO_AUTHORIZES_POST=true" not in section
    assert "api_secret" not in section.lower()
    assert "passphrase" not in section.lower()
    assert "ok-access-" not in section.lower()


def test_map_of_truth_has_no_z2dk_semantic_entry() -> None:
    text = _read(MAP_OF_TRUTH)
    assert "DOCUMENT_ROLE=NAVIGATION_ONLY_NO_SEMANTICS" in text
    assert "Z2DK" not in text
    assert "11.13.5.Z2DK" not in text


def test_standing_live_flags_and_secretref_identity_remain_unchanged() -> None:
    assert LIVE_AUTHORIZED is False
    assert TESTNET_AUTHORIZED is False
    assert LIVE_ENABLED is False
    assert LIVE_ARMED is False
    assert SUBMIT_UNLOCKED is False
    assert REQUIRED_SECRETREF_URI == SECRETREF
    assert REQUIRED_CREDENTIAL_CLASS == "LIVE_CANARY_MINIMUM_EXPOSURE_TRADE_API_KEY"


def test_existing_owners_reused_without_new_transport_or_signer() -> None:
    assert UrllibLiveCanaryTransportV1.__name__ == "UrllibLiveCanaryTransportV1"
    handler_src = inspect.getsource(CanaryPostRedirectFailClosedHandler._block_post_or_follow)
    assert '{"GET", "POST"}' in handler_src or "{'GET', 'POST'}" in handler_src
    send_src = inspect.getsource(UrllibLiveCanaryTransportV1.send)
    assert "urlopen" not in send_src
    assert "CanaryPostRedirectFailClosedHandler" in send_src
    assert "build_opener" in send_src
    get_src = inspect.getsource(LiveCanaryHttpClientV1.get)
    assert "self.post(" not in get_src
    assert "post_entry_order" not in get_src
    signer_src = inspect.getsource(build_okx_live_canary_auth_headers_v1)
    assert "def build_okx_live_canary_auth_headers_v1" in signer_src
    http_text = _read(HTTP_CLIENT)
    assert (
        "from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener"
        in (http_text)
    )
    assert "urlopen" not in http_text


def test_atlas_z2dk_remains_navigation_only() -> None:
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
    assert "Additive §11.13.5.Z2DK SSOT persist" in block
    assert "tests/ops/test_section_11_13_5_z2dk_persist_v1.py" in block
    assert "http_client_v1.py" in block
    assert "kind: RUNTIME_COMPONENT:z2dk" not in catalog
    assert "RUNTIME_COMPONENT:z2dk_" not in catalog
