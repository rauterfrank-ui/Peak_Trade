"""CANARY_SUBMIT_AUTHORIZATION contract docs-only persistence v1.

No live trading. No POST. No GET. No productive src mutation.
This test is a documentation guard, not a second semantic SSOT.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
MASTER_RUNBOOK = REPO_ROOT / "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md"
MAP_OF_TRUTH = REPO_ROOT / "docs/governance/PEAK_TRADE_MAP_OF_TRUTH.md"
SPEC_PATH = REPO_ROOT / "docs/ops/specs/PEAK_TRADE_CANARY_SUBMIT_AUTHORIZATION_CONTRACT_V1.md"
PRIOR_VENUE = REPO_ROOT / (
    "docs/ops/specs/PEAK_TRADE_VENUE_PRETRADE_LIMIT_GATES_FORENSIC_BINDING_AND_CLOSURE_V1.md"
)
OWNER_GO = "PEAK_TRADE_CANARY_SUBMIT_AUTHORIZATION_CONTRACT_DOCS_ONLY_PERSISTENCE_V1"
BOUND_SHA = "f868f6b519611fbfd1ff189293f5a40aafc7a26c"
CONSTANTS_1135 = (
    REPO_ROOT / "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/constants_v1.py"
)
CONSTANTS_1132 = REPO_ROOT / "src/ops/section_11_13_2_live_private_read_only_v1/constants_v1.py"


def _section_5_3(text: str) -> str:
    start = text.index("## 5.3 Canonical productive no-order call graph")
    end = text.index("## 5.4 Closed or materially established baseline capabilities")
    return text[start:end]


def test_docs_and_master_pointer() -> None:
    spec = SPEC_PATH.read_text(encoding="utf-8")
    prior = PRIOR_VENUE.read_text(encoding="utf-8")
    section = _section_5_3(MASTER_RUNBOOK.read_text(encoding="utf-8"))
    mot = MAP_OF_TRUTH.read_text(encoding="utf-8")
    assert SPEC_PATH.is_file()
    assert f"OWNER_GO_THIS_SLICE={OWNER_GO}" in spec
    assert f"BOUND_ORIGIN_MAIN_SHA={BOUND_SHA}" in spec
    assert "DOCUMENT_CLASS=SUBORDINATE_GOVERNANCE_CONTRACT" in spec
    assert "CANARY_SUBMIT_AUTHORIZATION_CONTRACT_BOUND=true" in spec
    assert "CANARY_SUBMIT_AUTHORIZATION_AUTHORIZED=false" in spec
    assert "CANARY_SUBMIT_AUTHORIZATION_SATISFIED=false" in spec
    assert "CANARY_SUBMIT_AUTHORIZATION_IS_SINGLE_BOOLEAN=false" in spec
    assert "CANARY_SUBMIT_AUTHORIZATION_EQUALS_SUBMIT_ALLOWED=false" in spec
    assert "CANARY_SUBMIT_AUTHORIZATION_EQUALS_CANARY_AUTHORIZED=false" in spec
    assert "CANARY_SUBMIT_AUTHORIZATION_EQUALS_ACTUAL_SUBMIT=false" in spec
    assert "INCLUDED_LAYERS=L1,L2,L3,L4" in spec
    assert "EXCLUDED_LAYERS=L0,L5,L6,L7" in spec
    assert "STATE_COLLAPSE_FORBIDDEN=true" in spec
    assert "CANARY_AUTHORIZED_ROLE=SEPARATE_STANDING_GOVERNANCE_STATE_NOT_MEMBER" in spec
    assert "CANARY_AUTHORIZED_REQUIRED_FOR_SCOPED_SUBMIT=false" in spec
    assert "CANARY_AUTHORIZED_MAY_REMAIN_FALSE_DURING_SCOPED_CANARY=true" in spec
    assert (
        "LIVE_CANARY_MINIMUM_EXPOSURE_AUTHORIZED_ROLE=SCOPED_OPERATIVE_AUTHORITY_INPUT_L1" in spec
    )
    assert "COVER_USDC_MEMBERSHIP=EXCLUDED_FROM_THIS_NAMED_SURFACE" in spec
    assert "COVER_USDC_HISTORICAL_ROLE_PRESERVED=true" in spec
    assert "COVER_USDC_STATUS=UNINSTANTIATED" in spec
    assert "LIVE_FLATTEN_PROVABILITY_MEMBERSHIP=EXCLUDED_FROM_THIS_NAMED_SURFACE" in spec
    assert "LIVE_FLATTEN_PROVABILITY_EXECUTION_SAFETY_ROLE_PRESERVED=true" in spec
    assert "LIVE_FLATTEN_PROVABILITY_RECOVERY_AND_PROVEN_STATE_ROLE_PRESERVED=true" in spec
    assert "Z2AA_SAFETY_FINDING_NOT_DELETED_BY_POINTER_SUCCESSION=true" in spec
    assert "PLANE_A=AUTHORIZATION_GRANT" in spec
    assert "PLANE_G=RECONCILIATION_PROVEN_PROGRESSION" in spec
    assert "EARLIEST_UNRESOLVED_DEPENDENCY=MULTIPLE_INDEPENDENT_BLOCKERS" in spec
    assert "EARLIEST_UNRESOLVED_DEPENDENCY_PROVEN_ORDERING=false" in spec
    assert (
        "INDEPENDENT_BLOCKERS_INSIDE_SURFACE="
        "L1_SCOPED_AUTHORITY;L2_SESSION_ARMING;L4_FRESH_RUNTIME_PRE_SUBMIT_VALIDATION"
    ) in spec
    assert (
        "PARALLEL_PRESERVED_OUTSIDE_SURFACE="
        "COVER_USDC_FUNDING_AND_LOSS_BOUND;"
        "LIVE_FLATTEN_PROVABILITY_EXECUTION_SAFETY_AND_PROVEN_STATE"
    ) in spec
    assert "NEXT_DISTINCT_SURFACE=CANARY_SUBMIT_AUTHORIZATION" in spec
    assert "NEXT_DISTINCT_SURFACE_AUTHORIZED=false" in spec
    assert "IMPLEMENTATION_AUTHORIZED=false" in spec
    assert "EXECUTION_AUTHORIZED=false" in spec
    assert "NETWORK_GET_PERFORMED=false" in spec
    assert "NETWORK_POST_PERFORMED=false" in spec
    assert "TRADING_PERFORMED=false" in spec
    assert "LIVE_AUTHORIZED=false" in spec
    assert "TESTNET_AUTHORIZED=false" in spec
    assert "CANARY_AUTHORIZED=false" in spec
    assert "SUBMIT_UNLOCKED=false" in spec
    assert "CHANGED_RUNTIME_FILES=NONE" in spec
    assert "RUNTIME_MUTATION_PERFORMED=false" in spec
    assert "NAVIGATION_ONLY=MAP_OF_TRUTH" in spec
    assert "TESTS_ARE_GUARDS_NOT_SECOND_SSOT=true" in spec

    assert "CANARY_SUBMIT_AUTHORIZATION_CONTRACT_V1=true" in section
    assert "CANARY_SUBMIT_AUTHORIZATION_CONTRACT_BOUND=true" in section
    assert "CANARY_SUBMIT_AUTHORIZATION_AUTHORIZED=false" in section
    assert "CANARY_SUBMIT_AUTHORIZATION_SATISFIED=false" in section
    assert "CANARY_SUBMIT_AUTHORIZATION_EQUALS_SUBMIT_ALLOWED=false" in section
    assert "INCLUDED_LAYERS=L1,L2,L3,L4" in section
    assert "EXCLUDED_LAYERS=L0,L5,L6,L7" in section
    assert "STATE_COLLAPSE_FORBIDDEN=true" in section
    assert "COVER_USDC_MEMBERSHIP=EXCLUDED_FROM_THIS_NAMED_SURFACE" in section
    assert "LIVE_FLATTEN_PROVABILITY_MEMBERSHIP=EXCLUDED_FROM_THIS_NAMED_SURFACE" in section
    assert "Z2AA_SAFETY_FINDING_NOT_DELETED_BY_POINTER_SUCCESSION=true" in section
    assert "EARLIEST_UNRESOLVED_DEPENDENCY=MULTIPLE_INDEPENDENT_BLOCKERS" in section
    assert "NEXT_DISTINCT_SURFACE=CANARY_SUBMIT_AUTHORIZATION" in section
    assert "NEXT_DISTINCT_SURFACE_AUTHORIZED=false" in section
    assert "LIVE_AUTHORIZED=false" in section
    assert "TESTNET_AUTHORIZED=false" in section
    assert "CANARY_AUTHORIZED=false" in section
    assert "SUBMIT_UNLOCKED=false" in section
    assert "the surface is not authorized" in section

    assert "PEAK_TRADE_CANARY_SUBMIT_AUTHORIZATION_CONTRACT_V1" in mot
    assert "DOCUMENT_ROLE=NAVIGATION_ONLY_NO_SEMANTICS" in mot
    assert "THIS_DOCUMENT_DEFINES_NO_SEMANTICS=true" in mot
    assert "EARLIEST_UNRESOLVED_DEPENDENCY=MULTIPLE_INDEPENDENT_BLOCKERS" in mot
    assert (
        "EARLIEST_UNRESOLVED_SECTION_POINTER=SECTION_5_3_CANARY_SUBMIT_AUTHORIZATION_CONTRACT"
    ) in mot
    assert "§11.13.5.Z2AA |" in mot
    assert "EARLIEST_UNRESOLVED_DEPENDENCY=LIVE_FLATTEN_PROVABILITY" in mot
    assert "COVER_USDC_STATUS=UNINSTANTIATED" in mot
    assert "LIVE_AUTHORIZED=false" in mot
    assert "SUBMIT_UNLOCKED=false" in mot

    assert "EARLIEST_UNRESOLVED_DEPENDENCY=CANARY_SUBMIT_AUTHORIZATION" in prior
    assert "NEXT_DISTINCT_SURFACE=CANARY_SUBMIT_AUTHORIZATION" in prior


def test_standing_authorization_flags_remain_false() -> None:
    constants_1135 = CONSTANTS_1135.read_text(encoding="utf-8")
    constants_1132 = CONSTANTS_1132.read_text(encoding="utf-8")
    assert "LIVE_AUTHORIZED = False" in constants_1135
    assert "TESTNET_AUTHORIZED = False" in constants_1135
    assert "SUBMIT_UNLOCKED = False" in constants_1135
    assert "CANARY_AUTHORIZED = False" in constants_1132
    assert "LIVE_AUTHORIZED = True" not in constants_1135
    assert "TESTNET_AUTHORIZED = True" not in constants_1135
    assert "SUBMIT_UNLOCKED = True" not in constants_1135
    assert "CANARY_AUTHORIZED = True" not in constants_1132
