"""WP_B05_BYPASS_FATE_IMPLEMENTATION_CONTRACT_V1 — semantics + completion rules (governance only)."""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
IMPLEMENTATION_JSON = (
    REPO_ROOT / "config" / "governance" / "risk_sizing_bypass_fate_implementation_contract_v1.json"
)
IMPLEMENTATION_DOC = (
    REPO_ROOT / "docs" / "governance" / "RISK_SIZING_BYPASS_FATE_IMPLEMENTATION_CONTRACT_V1.md"
)
ADJUDICATION_JSON = (
    REPO_ROOT / "config" / "governance" / "risk_sizing_bypass_fate_operator_adjudication_v1.json"
)
VOCABULARY_JSON = (
    REPO_ROOT
    / "config"
    / "governance"
    / "risk_sizing_bypass_fate_vocabulary_and_decision_authority_freeze_v1.json"
)
INVENTORY_JSON = REPO_ROOT / "config" / "governance" / "risk_sizing_owner_inventory_ssot_v1.json"

EXPECTED_BYPASS_IDS = (
    "BYPASS_CLASSIC_BACKTEST_DEFAULT",
    "BYPASS_CORE_POSITION_SIZER",
    "BYPASS_EXECUTION_EXECUTE_FROM_SIGNALS",
    "BYPASS_LIVE_SHADOW_POSITION_FRACTION",
    "BYPASS_OFFLINE_EVAL_SIZING_CONTRACT",
)

EXPECTED_FATES = {
    "BYPASS_CLASSIC_BACKTEST_DEFAULT": "GOVERNANCE_EXCLUDE_FROM_SYSTEM_EVIDENCE",
    "BYPASS_CORE_POSITION_SIZER": "KEEP_PARALLEL_NON_CANONICAL",
    "BYPASS_EXECUTION_EXECUTE_FROM_SIGNALS": "KEEP_PARALLEL_NON_CANONICAL",
    "BYPASS_LIVE_SHADOW_POSITION_FRACTION": "GOVERNANCE_EXCLUDE_FROM_SYSTEM_EVIDENCE",
    "BYPASS_OFFLINE_EVAL_SIZING_CONTRACT": "RESEARCH_OR_OFFLINE_SCOPE_ONLY",
}


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_implementation_contract_semantics_slice_boundaries() -> None:
    payload = _load(IMPLEMENTATION_JSON)
    markers = payload["markers"]
    assert payload["workpackage_id"] == "WP_B05_BYPASS_FATE_IMPLEMENTATION_CONTRACT_V1"
    assert markers["FATE_IMPLEMENTATION_SEMANTICS_DEFINED"] is True
    assert markers["FATE_IMPLEMENTATION_EXECUTED"] is True
    assert markers["PER_BYPASS_FATE_IMPLEMENTATION_EXECUTED_COUNT"] == 5
    assert markers["S1_KEEP_PARALLEL_FATE_IMPLEMENTATION_EXECUTED"] is True
    assert markers["S2_GOVERNANCE_EXCLUDE_FATE_IMPLEMENTATION_EXECUTED"] is True
    assert markers["S3_RESEARCH_OR_OFFLINE_SCOPE_FATE_IMPLEMENTATION_EXECUTED"] is True
    assert markers["B05_FATE_PHASE_STATUS"] == "CLOSED"
    assert markers["RUNTIME_MUTATION_EXECUTED"] is False
    assert markers["RUNTIME_REWIRE_EXECUTED"] is False
    assert markers["BYPASS_PATH_COUNT"] == 5
    assert markers["CONVERSION_READY"] is False
    assert markers["C2_INPUT_AUTHORITIES"] == "UNRESOLVED"
    assert markers["CANONICAL_RISK_SIZING_OWNER"] == "UNRESOLVED"
    assert markers["AUTHORITY_EFFECT"] == "NONE"
    assert markers["RUNTIME_EFFECT"] == "NONE"
    assert payload["decision_authority"]["this_slice_executes_fate_implementation"] is False
    assert (
        payload["global_completion_rule"]["fate_implementation_executed_marker"][
            "this_contract_slice_may_set_true"
        ]
        is False
    )


def test_all_five_bypasses_bound_to_adjudicated_fates_with_requirements() -> None:
    payload = _load(IMPLEMENTATION_JSON)
    adjudication = _load(ADJUDICATION_JSON)
    summary = adjudication["operator_fate_summary_sorted"]
    implementations = payload["bypass_fate_implementations"]
    assert set(implementations.keys()) == set(EXPECTED_BYPASS_IDS)
    assert summary == EXPECTED_FATES
    for bid in EXPECTED_BYPASS_IDS:
        row = implementations[bid]
        assert row["stable_id"] == bid
        assert row["operator_fate_adjudication"] == summary[bid]
        assert row["fate_implementation_executed"] is True
        assert row["completion_evidence_satisfied"] is True
        assert row["minimum_implementation_requirements_verified"] is True
        assert row["fate_implementation_status"] == "COMPLETE"
        assert row["minimum_implementation_requirements"]
        assert row["completion_evidence"]
        assert row["forbidden_implicit_effects"]
        assert row["evidence_provenance_effect"]
        fate_semantics_key = row["fate_token_implementation_semantics_ref"]
        fate_sem = payload["fate_token_implementation_semantics"][fate_semantics_key]
        assert row["runtime_mutation_required"] == fate_sem["runtime_mutation_required"]
        assert row["separate_runtime_go_required"] == fate_sem["separate_runtime_go_required"]


def test_fate_token_semantics_align_with_vocabulary_runtime_go_pins() -> None:
    payload = _load(IMPLEMENTATION_JSON)
    vocabulary = _load(VOCABULARY_JSON)
    fate_sem = vocabulary["fate_token_semantics"]
    impl_sem = payload["fate_token_implementation_semantics"]
    for fate_semantics_key in (
        "KEEP_PARALLEL_NON_CANONICAL",
        "GOVERNANCE_EXCLUDE_FROM_SYSTEM_EVIDENCE",
        "RESEARCH_OR_OFFLINE_SCOPE_ONLY",
    ):
        assert impl_sem[fate_semantics_key]["runtime_mutation_required"] is False
        vocab_go = fate_sem[fate_semantics_key]["later_implementation_requires_separate_runtime_go"]
        if fate_semantics_key == "KEEP_PARALLEL_NON_CANONICAL":
            assert impl_sem[fate_semantics_key]["separate_runtime_go_required"] is False
            assert vocab_go is False
        else:
            assert impl_sem[fate_semantics_key]["separate_runtime_go_required"] is True
            assert vocab_go is True


def test_inventory_and_adjudication_cross_pins() -> None:
    implementation = _load(IMPLEMENTATION_JSON)
    adjudication = _load(ADJUDICATION_JSON)
    inventory = _load(INVENTORY_JSON)
    assert adjudication["markers"]["FATE_IMPLEMENTATION_EXECUTED"] is True
    assert inventory["markers"]["OPERATOR_FATE_ADJUDICATION_EXECUTED"] is True
    impl_block = inventory["operator_fate_implementation_v1"]
    assert impl_block["fate_implementation_executed"] is True
    assert impl_block["per_bypass_implementation_executed_count"] == 5
    assert impl_block["fate_implementation_semantics_defined"] is True
    assert impl_block["contract_ref"] == (
        "config/governance/risk_sizing_bypass_fate_implementation_contract_v1.json"
    )
    inventored = {b["id"]: b["operator_fate_adjudication"] for b in inventory["bypass_paths"]}
    assert inventored == adjudication["operator_fate_summary_sorted"]
    related = implementation["related_but_separate_contracts"]
    assert related["risk_sizing_bypass_fate_operator_adjudication_v1"] == (
        "ADJUDICATED_FATES_AUTHORITY_UNCHANGED"
    )


def test_implementation_doc_markers_present() -> None:
    text = IMPLEMENTATION_DOC.read_text(encoding="utf-8")
    for marker in (
        "RISK_SIZING_BYPASS_FATE_IMPLEMENTATION_CONTRACT_V1=true",
        "FATE_IMPLEMENTATION_SEMANTICS_DEFINED=true",
        "FATE_IMPLEMENTATION_EXECUTED=true",
        "RUNTIME_EFFECT=NONE",
        "CONVERSION_READY=false",
    ):
        assert marker in text


def test_productive_src_does_not_import_implementation_contract() -> None:
    needle = "risk_sizing_bypass_fate_implementation_contract_v1"
    hits: list[str] = []
    for path in (REPO_ROOT / "src").rglob("*.py"):
        if needle in path.read_text(encoding="utf-8"):
            hits.append(str(path.relative_to(REPO_ROOT)))
    assert hits == []


def test_global_completion_rule_is_machine_checkable_conjunction() -> None:
    payload = _load(IMPLEMENTATION_JSON)
    rule = payload["global_completion_rule"]["fate_implementation_executed_marker"]
    assert rule["allowed_true_only_when_all"]
    assert len(rule["allowed_true_only_when_all"]) >= 5
    per = payload["global_completion_rule"]["per_bypass_completion_rule"]
    assert per["this_contract_slice_may_set_per_bypass_true"] is False
