"""Current-SUI L4 fail-closed MAX_AVAILABLE zero end-state bind v1.

Docs/evidence-only persistence. No live trading. No POST. No GET.
No productive src mutation. Tests are guards, not a second semantic SSOT.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
MASTER_RUNBOOK = REPO_ROOT / "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md"
MAP_OF_TRUTH = REPO_ROOT / "docs/governance/PEAK_TRADE_MAP_OF_TRUTH.md"
SPEC_PATH = REPO_ROOT / (
    "docs/ops/specs/"
    "PEAK_TRADE_BIND_CURRENT_SUI_L4_FAIL_CLOSED_MAX_AVAILABLE_ZERO_END_STATE_NO_REPAIR_V1.md"
)
PRIOR_CANARY = REPO_ROOT / "docs/ops/specs/PEAK_TRADE_CANARY_SUBMIT_AUTHORIZATION_CONTRACT_V1.md"
PRIOR_MAX_AVAILABLE = REPO_ROOT / (
    "docs/ops/specs/PEAK_TRADE_MAX_AVAILABLE_OWNER_POLICY_ADJUDICATION_AND_CLOSURE_V1.md"
)
EVIDENCE_PACK = REPO_ROOT / (
    "evidence/ops/post_reconsolidation_current_sui_l4_pre_submit_no_wire_v1/20260831T170944Z"
)
CLAIMS = EVIDENCE_PACK / "CLAIMS.json"
MAX_AVAILABLE = EVIDENCE_PACK / "GET_MAX_AVAILABLE.sanitized.json"
MAX_SIZE = EVIDENCE_PACK / "GET_MAX_SIZE.sanitized.json"
MANIFEST = EVIDENCE_PACK / "MANIFEST.sha256"
OWNER_GO = "PEAK_TRADE_BIND_CURRENT_SUI_L4_FAIL_CLOSED_MAX_AVAILABLE_ZERO_END_STATE_NO_REPAIR_V1"
BOUND_SHA = "b6bcdfbd62205d3be9ca30105735132ac9e7aaec"
CONSTANTS_1135 = (
    REPO_ROOT / "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/constants_v1.py"
)
VENUE_COUNT = (
    REPO_ROOT / "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/venue_contract_count_v1.py"
)
ORDER_PLAN = REPO_ROOT / "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/order_plan_v1.py"


def _section_5_3(text: str) -> str:
    start = text.index("## 5.3 Canonical productive no-order call graph")
    end = text.index("## 5.4 Closed or materially established baseline capabilities")
    return text[start:end]


def test_docs_and_master_pointer() -> None:
    spec = SPEC_PATH.read_text(encoding="utf-8")
    prior_canary = PRIOR_CANARY.read_text(encoding="utf-8")
    prior_max = PRIOR_MAX_AVAILABLE.read_text(encoding="utf-8")
    section = _section_5_3(MASTER_RUNBOOK.read_text(encoding="utf-8"))
    mot = MAP_OF_TRUTH.read_text(encoding="utf-8")
    assert SPEC_PATH.is_file()
    assert f"OWNER_GO_THIS_SLICE={OWNER_GO}" in spec
    assert f"BOUND_ORIGIN_MAIN_SHA={BOUND_SHA}" in spec
    assert "DOCUMENT_CLASS=SUBORDINATE_GOVERNANCE_CONTRACT" in spec
    assert "CURRENT_SUI_L4_STATE=FAIL_CLOSED_AT_MAX_AVAILABLE" in spec
    assert "TARGET_INSTRUMENT_ID=SUI-USD_UM_XPERP-310404" in spec
    assert "CURRENT_MAX_AVAILABLE_MAXBUY=0" in spec
    assert "CURRENT_MAX_AVAILABLE_MAXSELL=0" in spec
    assert "CURRENT_MINIMUM_OPERATIVE_CONTRACT_QTY=1" in spec
    assert "CURRENT_MINIMUM_OPERATIVE_CONTRACT_QTY_SOURCE=SUI_OPERATIVE_ORDER_SZ" in spec
    assert "MINSZ_IS_NOT_QUANTITY_SOURCE=true" in spec
    assert (
        "CURRENT_MAX_AVAILABLE_GATE_RESULT=FAIL_CLOSED:VENUE_CONTRACT_COUNT_EXCEEDS_MAXBUY" in spec
    )
    assert "ROOT_CAUSE_OF_MAX_AVAILABLE_ZERO=UNPROVEN" in spec
    assert "FUNDING_CAUSALITY_PROVEN=false" in spec
    assert "COVER_USDC_CAUSALITY_PROVEN=false" in spec
    assert "AVAILABLE_MARGIN_CAUSALITY_PROVEN=false" in spec
    assert "CURRENT_SUI_FRESH_PRETRADE_INPUTS_PROVEN=true" in spec
    assert "CURRENT_SUI_PRETRADE_CONSUMPTION_PROVEN=false" in spec
    assert "CURRENT_SUI_ORDER_PLAN_PROVEN=false" in spec
    assert "CURRENT_SUI_PRE_SUBMIT_PAYLOAD_PROVEN=false" in spec
    assert "CURRENT_SUI_CANARY_L4_PRE_SUBMIT_NO_WIRE_PROVEN=false" in spec
    assert "CURRENT_ORDER_PLAN_CONSTRUCTED=false" in spec
    assert "CURRENT_PRE_SUBMIT_PAYLOAD_CONSTRUCTED=false" in spec
    assert "POST_ATTEMPTED=false" in spec
    assert "WIRE_SEND_ATTEMPTED=false" in spec
    assert "PRODUCTIVE_TRANSPORT_INVOKED=false" in spec
    assert "NO_REPAIR_AUTHORIZED=true" in spec
    assert "NO_FUNDING_MUTATION_AUTHORIZED=true" in spec
    assert "NO_COVER_USDC_INSTANTIATION_AUTHORIZED=true" in spec
    assert "NO_EXECUTION_AUTHORIZED=true" in spec
    assert "MAXBUY_ZERO_IS_NOT_PROVEN_FUNDING_PROBLEM=true" in spec
    assert "MAX_AVAILABLE_IS_NOT_AVAILABLE_MARGIN=true" in spec
    assert "ACCOUNT_MAX_SIZE_IS_NOT_ACCOUNT_MAX_AVAIL_SIZE=true" in spec
    assert "OPERATIVE_QTY_ONE_IS_NOT_MINSZ_AS_QUANTITY_SOURCE=true" in spec
    assert "HISTORICAL_BTC_EVIDENCE_IS_NOT_CURRENT_SUI_EVIDENCE=true" in spec
    assert "COVER_USDC_STATUS=UNINSTANTIATED" in spec
    assert "AVAILABLE_MARGIN_REACHED_IN_CURRENT_RUN=false" in spec
    assert "CANARY_SUBMIT_AUTHORIZATION_STATUS=UNAUTHORIZED_UNSATISFIED" in spec
    assert "CANARY_SUBMIT_AUTHORIZATION_REMAINS_NEXT_DISTINCT_UNAUTHORIZED_SURFACE=true" in spec
    assert "NEXT_DISTINCT_SURFACE=NONE_STOP_NO_REPAIR" in spec
    assert "CHANGED_RUNTIME_FILES=NONE" in spec
    assert "RUNTIME_MUTATION_PERFORMED=false" in spec
    assert "TESTS_ARE_GUARDS_NOT_SECOND_SSOT=true" in spec
    assert "PERSISTED_PACK_IS_NOT_CANONICAL_AUTHORITY=true" in spec

    assert "BIND_CURRENT_SUI_L4_FAIL_CLOSED_MAX_AVAILABLE_ZERO_END_STATE_NO_REPAIR_V1=true" in (
        section
    )
    assert "CURRENT_SUI_L4_STATE=FAIL_CLOSED_AT_MAX_AVAILABLE" in section
    assert "ROOT_CAUSE_OF_MAX_AVAILABLE_ZERO=UNPROVEN" in section
    assert "FUNDING_CAUSALITY_PROVEN=false" in section
    assert "COVER_USDC_CAUSALITY_PROVEN=false" in section
    assert "AVAILABLE_MARGIN_CAUSALITY_PROVEN=false" in section
    assert "NO_REPAIR_AUTHORIZED=true" in section
    assert "NEXT_DISTINCT_SURFACE=NONE_STOP_NO_REPAIR" in section
    assert "CANARY_SUBMIT_AUTHORIZATION_REMAINS_NEXT_DISTINCT_UNAUTHORIZED_SURFACE=true" in (
        section
    )
    assert "LIVE_AUTHORIZED=false" in section
    assert "CANARY_AUTHORIZED=false" in section
    assert "CHANGED_RUNTIME_FILES=NONE" in section

    assert (
        "PEAK_TRADE_BIND_CURRENT_SUI_L4_FAIL_CLOSED_MAX_AVAILABLE_ZERO_END_STATE_NO_REPAIR_V1"
        in (mot)
    )
    assert "DOCUMENT_ROLE=NAVIGATION_ONLY_NO_SEMANTICS" in mot
    assert "THIS_DOCUMENT_DEFINES_NO_SEMANTICS=true" in mot
    assert "CURRENT_SUI_L4_STATE=FAIL_CLOSED_AT_MAX_AVAILABLE" in mot
    assert "ROOT_CAUSE_OF_MAX_AVAILABLE_ZERO=UNPROVEN" in mot
    assert "FUNDING_CAUSALITY_PROVEN=false" in mot
    assert "COVER_USDC_CAUSALITY_PROVEN=false" in mot
    assert "NO_REPAIR_AUTHORIZED=true" in mot
    assert "EARLIEST_UNRESOLVED_DEPENDENCY=MULTIPLE_INDEPENDENT_BLOCKERS" in mot
    assert (
        "EARLIEST_UNRESOLVED_SECTION_POINTER=SECTION_5_3_CANARY_SUBMIT_AUTHORIZATION_CONTRACT"
    ) in mot
    assert "CANARY_SUBMIT_AUTHORIZATION_STATUS=UNAUTHORIZED_UNSATISFIED" in mot
    assert "COVER_USDC_STATUS=UNINSTANTIATED" in mot

    assert "CANARY_SUBMIT_AUTHORIZATION_AUTHORIZED=false" in prior_canary
    assert "PREVIOUS_BINDING_DISPOSITION=SUPERSEDED_BY_OWNER_ADJUDICATION" in prior_max
    assert "MAX_AVAILABLE_ENDPOINT=/api/v5/account/max-size" in prior_max


def test_forensic_pack_referenced_not_authority() -> None:
    claims = CLAIMS.read_text(encoding="utf-8")
    max_available = MAX_AVAILABLE.read_text(encoding="utf-8")
    max_size = MAX_SIZE.read_text(encoding="utf-8")
    spec = SPEC_PATH.read_text(encoding="utf-8")
    assert EVIDENCE_PACK.is_dir()
    assert MANIFEST.is_file()
    assert '"maxBuy": "0"' in max_available
    assert '"maxSell": "0"' in max_available
    assert '"minSz": "1"' in max_size
    assert '"ORDER_PLAN_CONSTRUCTED": false' in claims
    assert '"PRE_SUBMIT_PAYLOAD_CONSTRUCTED": false' in claims
    assert '"CLIENT_POST_COUNT": 0' in claims
    assert '"WIRE_SEND_ATTEMPTED": false' in claims
    assert '"PRODUCTIVE_TRANSPORT_INVOKED": false' in claims
    assert '"OWNER_GO_EXECUTE_USED": false' in claims
    assert "MAX_AVAILABLE_GATE:VENUE_CONTRACT_COUNT_EXCEEDS_MAXBUY" in claims
    assert "PERSISTED_PACK_IS_NOT_CANONICAL_AUTHORITY=true" in spec
    assert "PERSISTED_PACK_IS_NOT_OPERATIVE_CACHE=true" in spec


def test_standing_authorization_and_quantity_source_unmutated() -> None:
    constants = CONSTANTS_1135.read_text(encoding="utf-8")
    venue_count = VENUE_COUNT.read_text(encoding="utf-8")
    order_plan = ORDER_PLAN.read_text(encoding="utf-8")
    assert "LIVE_AUTHORIZED = False" in constants
    assert "TESTNET_AUTHORIZED = False" in constants
    assert "SUBMIT_UNLOCKED = False" in constants
    assert "LIVE_AUTHORIZED = True" not in constants
    assert 'SUI_OPERATIVE_ORDER_SZ = "1"' in venue_count
    assert "FORBIDDEN_UPGRADE_MINSZ_1_TO_OPERATIVE_QTY_1 = True" in venue_count
    start = order_plan.index("def build_minimum_valid_canary_order_plan_v1(")
    end = order_plan.index("def build_minimum_valid_canary_flatten_order_plan_v1(")
    builder = order_plan[start:end]
    assert "apply_fresh_max_available_pretrade_gate_v1" in builder
    assert "apply_fresh_available_margin_pretrade_gate_v1" in builder
    idx_max_available = builder.index("apply_fresh_max_available_pretrade_gate_v1")
    idx_available_margin = builder.index("apply_fresh_available_margin_pretrade_gate_v1")
    idx_payload = builder.index("build_venue_native_order_body_v1")
    assert idx_max_available < idx_available_margin < idx_payload
