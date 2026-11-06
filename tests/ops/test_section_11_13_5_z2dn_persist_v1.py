"""§11.13.5.Z2DN persist invariants. Docs/governance plus offline policy rebind."""

from __future__ import annotations

from pathlib import Path

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    LIVE_ARMED,
    LIVE_AUTHORIZED,
    LIVE_ENABLED,
    SUBMIT_UNLOCKED,
    TESTNET_AUTHORIZED,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_execute_authority_v1 import (
    FORBIDDEN_FLATTEN_EXECUTE_OWNER_GOS,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.post_z2cz_position_creation_autonomy_semantic_rebind_v1 import (
    POSITION_MUST_BE_CREATED_BY_PEAK_TRADE as Z2DA_POSITION_MUST_BE_CREATED_BY_PEAK_TRADE,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.prerequisite_08_position_source_policy_rebind_v1 import (
    OWNER_GO as POLICY_OWNER_GO,
    OWNER_POLICY_DECISION,
    POSITION_MUST_BE_CREATED_BY_PEAK_TRADE,
    POSITION_SOURCE_POLICY,
    PREREQUISITE_08_CLOSED,
    THIS_SLICE,
    WORKPACKAGE_ID,
    Z2DA_TEXT_REWRITTEN,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
MASTER_RUNBOOK = REPO_ROOT / "docs" / "runbooks" / "canonical" / "PEAK_TRADE_MASTER_RUNBOOK.md"
MAP_OF_TRUTH = REPO_ROOT / "docs" / "governance" / "PEAK_TRADE_MAP_OF_TRUTH.md"
ATLAS_CATALOG = REPO_ROOT / "docs" / "system_atlas" / "entities" / "catalog.yaml"
ATLAS_AUTHORITY = REPO_ROOT / "docs" / "system_atlas" / "ATLAS_AUTHORITY_AND_USAGE.md"

Z2DA_HEADING = "### 11.13.5.Z2DA Post-Z2CZ position-creation / autonomy semantic rebind persist"
Z2DM_HEADING = "### 11.13.5.Z2DM Canonical offline position-creation path wiring persist"
Z2DN_HEADING = "### 11.13.5.Z2DN Prerequisite-08 position-source policy rebind persist"
Z2DO_HEADING = "### 11.13.5.Z2DO Route-C offline gated productive submit composition persist"
LADDER_HEADING = "## 11.14 Live order and economic evidence ladder"
OWNER_GO = "PEAK_TRADE_OWNER_GO_PREREQUISITE_08_POSITION_SOURCE_POLICY_PERSIST_IMPLEMENT_PR_V1"
BASELINE_SHA = "7ba9e9f87dc004f399dcc26a5b444435e94132f4"
NEXT_BOUNDARY = (
    "SEPARATE_OWNER_GO_REQUIRED_BEFORE_ANY_VENUE_WIRE_OR_GET_OR_POST_"
    "OR_POSITION_CREATION_OR_FLATTEN_OR_LIVE_OR_CANARY"
)


def _read(path: Path) -> str:
    assert path.is_file(), f"missing canonical path: {path}"
    return path.read_text(encoding="utf-8")


def _z2dn_section(text: str) -> str:
    start = text.find(Z2DN_HEADING)
    assert start >= 0, "missing §11.13.5.Z2DN heading"
    end = text.find(Z2DO_HEADING, start)
    if end < 0:
        end = text.find(LADDER_HEADING, start)
    assert end > start, "missing §11.13.5.Z2DO or §11.14 boundary after Z2DN"
    return text[start:end]


def _z2da_own_section(text: str) -> str:
    start = text.find(Z2DA_HEADING)
    assert start >= 0, "missing §11.13.5.Z2DA heading"
    end = text.find("### 11.13.5.", start + len(Z2DA_HEADING))
    assert end > start, "missing successor heading after Z2DA"
    return text[start:end]


def test_z2dn_heading_is_unique_and_follows_z2dm() -> None:
    text = _read(MASTER_RUNBOOK)
    assert text.count(Z2DN_HEADING) == 1
    assert (
        0
        <= text.find(Z2DM_HEADING)
        < text.find(Z2DN_HEADING)
        < text.find(Z2DO_HEADING)
        < text.find(LADDER_HEADING)
    )


def test_z2da_historical_unproven_left_open_is_preserved() -> None:
    z2da = _z2da_own_section(_read(MASTER_RUNBOOK))
    assert "POSITION_MUST_BE_CREATED_BY_PEAK_TRADE=UNPROVEN_LEFT_OPEN" in z2da
    assert "\nPOSITION_MUST_BE_CREATED_BY_PEAK_TRADE=false\n" not in z2da
    assert Z2DA_POSITION_MUST_BE_CREATED_BY_PEAK_TRADE == "UNPROVEN_LEFT_OPEN"
    assert Z2DA_TEXT_REWRITTEN is False


def test_z2dn_docs_bind_source_policy_without_create_or_08_close() -> None:
    section = _z2dn_section(_read(MASTER_RUNBOOK))
    required = (
        "AUTHORIZED_SCOPE=A_Z2DN_PREREQUISITE_08_POSITION_SOURCE_POLICY_REBIND_ONLY",
        f"OWNER_GO={OWNER_GO}",
        "OWNER_GO_STATUS=CONSUMED",
        f"OWNER_POLICY_DECISION={OWNER_POLICY_DECISION}",
        f"CURRENT_ORIGIN_MAIN_SHA={BASELINE_SHA}",
        "EXPECTED_ORIGIN_MAIN_SHA_MATCH=true",
        "PREDECESSOR_SLICE=11.13.5.Z2DM",
        f"THIS_SLICE={THIS_SLICE}",
        "LAST_CANONICALLY_CLOSED_STEP=SECTION_11_13_5_Z2DN",
        "CURRENT_CANONICAL_SECTION=11.13.5.Z2DN",
        "Z2DA_TEXT_REWRITTEN=false",
        "Z2DM_TEXT_REWRITTEN=false",
        f"WORKPACKAGE_ID={WORKPACKAGE_ID}",
        "SUPERSESSION_RELATION=Z2DN_RESOLVES_Z2DA_POSITION_MUST_BE_CREATED_BY_PEAK_TRADE_UNPROVEN_LEFT_OPEN_WITHOUT_REWRITING_Z2DA",
        "Z2DA_FIELD_HISTORICAL_VALUE=UNPROVEN_LEFT_OPEN",
        f"POSITION_SOURCE_POLICY={POSITION_SOURCE_POLICY}",
        "POSITION_MUST_BE_CREATED_BY_PEAK_TRADE=false",
        "SOURCE_PROVENANCE_REQUIRED_FOR_PREREQUISITE_08=false",
        "EXTERNAL_OR_PREEXISTING_POSITION_MAY_SATISFY_PREREQUISITE_08_IF_CANONICAL_NONZERO_OBSERVATION_IS_PROVEN=true",
        "PEAK_TRADE_CREATED_POSITION_MAY_SATISFY_PREREQUISITE_08_IF_CANONICAL_NONZERO_OBSERVATION_IS_PROVEN=true",
        "EXTERNAL_POSITION_ALLOWED=false",
        "PREREQUISITE_08_REMAINS_OBSERVATION_PROOF_GATE=true",
        "PREREQUISITE_08_CREATES_POSITION=false",
        "POSITION_SOURCE_IDENTITY_IS_NOT_PART_OF_PREREQUISITE_08_PROPOSITION=true",
        "PREREQUISITE_08_GRANTS_POSITION_CREATION_AUTHORITY=false",
        "PREREQUISITE_08_GRANTS_LIVE_AUTHORITY=false",
        "PREREQUISITE_08_GRANTS_CANARY_AUTHORITY=false",
        "DOWNSTREAM_RECONCILIATION_POLICY_CHANGED=false",
        "CLASSIFIER_SOURCE_PROVENANCE_INJECTED=false",
        "PREREQUISITE_08_CLOSED=false",
        "PRODUCTIVE_NONZERO_PROOF_CREATED_BY_THIS_PERSIST=false",
        "POSITION_CREATION_CURRENTLY_AUTHORIZED=false",
        "GET_EXECUTED_THIS_PERSIST=false",
        "POSITIONS_GET_PERFORMED=false",
        "POST_EXECUTED=false",
        "LIVE_AUTHORIZED=false",
        "CANARY_AUTHORIZED=false",
        "SUBMIT_UNLOCKED=false",
        "NEXT_IDENTICAL_GET_INFORMATION_VALUE=LOW_EXPECTED_INFORMATION_GAIN",
        "CANONICAL_LIVE_EARLIEST_UNRESOLVED_DEPENDENCY=EXECUTION_PREREQUISITE_08_TARGET_POSITION_NONZERO_PROVEN",
        "Z2DA_EARLIEST_REAL_UNRESOLVED_DEPENDENCY_HISTORICAL="
        "NO_AUTHORIZED_REACHABLE_PRODUCER_OF_NONZERO_VENUE_POSITION_REQUIRED_BY_PREREQUISITE_08",
        f"NEXT_AUTHORITY_BOUNDARY={NEXT_BOUNDARY}",
        "MERGE_AUTHORIZED_BY_THIS_PERSIST=false",
        "NO_MAP_OF_TRUTH_MUTATION=true",
        "ATLAS_MUTATION=false",
        "ATLAS_IMPACT=UPDATED",
    )
    for token in required:
        assert token in section, token


def test_z2dn_docs_forbid_overclaim() -> None:
    section = _z2dn_section(_read(MASTER_RUNBOOK))
    forbidden = (
        "\nLIVE_AUTHORIZED=true\n",
        "\nCANARY_AUTHORIZED=true\n",
        "\nSUBMIT_UNLOCKED=true\n",
        "\nPREREQUISITE_08_CLOSED=true\n",
        "\nEXTERNAL_POSITION_ALLOWED=true\n",
        "\nPOSITION_CREATION_CURRENTLY_AUTHORIZED=true\n",
        "\nPREREQUISITE_08_CREATES_POSITION=true\n",
        "\nGET_EXECUTED_THIS_PERSIST=true\n",
        "\nPOST_EXECUTED=true\n",
        "\nPOSITION_MUST_BE_CREATED_BY_PEAK_TRADE=true\n",
        "\nSOURCE_PROVENANCE_REQUIRED_FOR_PREREQUISITE_08=true\n",
        "\nZ2DA_TEXT_REWRITTEN=true\n",
        "\nMERGE_AUTHORIZED_BY_THIS_PERSIST=true\n",
        "\nCLASSIFIER_SOURCE_PROVENANCE_INJECTED=true\n",
        "\nPRODUCTIVE_NONZERO_PROOF_CREATED_BY_THIS_PERSIST=true\n",
        "\nATLAS_AUTHORITY=CANONICAL\n",
        "\nLANDSCAPE_AUTHORITY=SSOT\n",
    )
    for token in forbidden:
        assert token not in section, token
    assert "api_secret" not in section.lower()
    assert "passphrase" not in section.lower()


def test_map_of_truth_has_no_z2dn_semantic_entry() -> None:
    text = _read(MAP_OF_TRUTH)
    assert "DOCUMENT_ROLE=NAVIGATION_ONLY_NO_SEMANTICS" in text
    assert "Z2DN" not in text
    assert "11.13.5.Z2DN" not in text


def test_code_claims_remain_fail_closed() -> None:
    assert POLICY_OWNER_GO == OWNER_GO
    assert THIS_SLICE == "11.13.5.Z2DN"
    assert POSITION_SOURCE_POLICY == ("SOURCE_IRRELEVANT_TO_PREREQUISITE_08_IF_NONZERO_PROVEN")
    assert POSITION_MUST_BE_CREATED_BY_PEAK_TRADE is False
    assert PREREQUISITE_08_CLOSED is False
    assert OWNER_GO in FORBIDDEN_FLATTEN_EXECUTE_OWNER_GOS
    assert LIVE_AUTHORIZED is False
    assert TESTNET_AUTHORIZED is False
    assert LIVE_ENABLED is False
    assert LIVE_ARMED is False
    assert SUBMIT_UNLOCKED is False


def test_atlas_z2dn_is_navigation_only() -> None:
    catalog = _read(ATLAS_CATALOG)
    authority = _read(ATLAS_AUTHORITY)
    assert "ATLAS_AUTHORITY=NONE" in authority
    marker = "id: RUNTIME_COMPONENT:prerequisite_08_position_source_policy_rebind_v1"
    assert marker in catalog
    start = catalog.find(marker)
    end = catalog.find("\n  - id:", start + 1)
    block = catalog[start:] if end < 0 else catalog[start:end]
    assert "current_canonical: false" in block
    assert "ATLAS_AUTHORITY=NONE" in block
    assert "prerequisite_08_position_source_policy_rebind_v1.py" in block
    assert "id: PHASE:z2dn" in catalog
