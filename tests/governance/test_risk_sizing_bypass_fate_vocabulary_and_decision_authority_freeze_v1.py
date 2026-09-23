"""Static contract: Bypass fate vocabulary + decision authority freeze v1.

Docs/config/tests-only. Pins allowed operator_fate_adjudication tokens and
SCOPED_OPERATOR_GO decision authority without assigning per-BYPASS fates or
changing runtime semantics.
"""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CONTRACT_JSON = (
    REPO_ROOT
    / "config"
    / "governance"
    / "risk_sizing_bypass_fate_vocabulary_and_decision_authority_freeze_v1.json"
)
CONTRACT_DOC = (
    REPO_ROOT
    / "docs"
    / "governance"
    / "RISK_SIZING_BYPASS_FATE_VOCABULARY_AND_DECISION_AUTHORITY_FREEZE_V1.md"
)
OWNER_INVENTORY_JSON = (
    REPO_ROOT / "config" / "governance" / "risk_sizing_owner_inventory_ssot_v1.json"
)

EXPECTED_ALLOWED_TOKENS = (
    "CONFLICTING",
    "GOVERNANCE_EXCLUDE_FROM_SYSTEM_EVIDENCE",
    "INTEND_REBIND_TO_CRS",
    "KEEP_PARALLEL_NON_CANONICAL",
    "RESEARCH_OR_OFFLINE_SCOPE_ONLY",
    "UNKNOWN",
)

EXPECTED_BYPASS_IDS = (
    "BYPASS_CLASSIC_BACKTEST_DEFAULT",
    "BYPASS_CORE_POSITION_SIZER",
    "BYPASS_EXECUTION_EXECUTE_FROM_SIGNALS",
    "BYPASS_LIVE_SHADOW_POSITION_FRACTION",
    "BYPASS_OFFLINE_EVAL_SIZING_CONTRACT",
)

FOREIGN_TOKENS = (
    "DEPRECATE_LEGACY_PATH",
    "DEPRECATED_QUARANTINED",
)

REQUIRED_DOC_MARKERS = (
    "RISK_SIZING_BYPASS_FATE_VOCABULARY_AND_DECISION_AUTHORITY_FREEZE_V1=true",
    "INVENTORY_ONLY=true",
    "AUTHORITY_EFFECT=NONE",
    "RUNTIME_EFFECT=NONE",
    "PER_BYPASS_FATE_ADJUDICATION_EXECUTED=false",
    "PER_BYPASS_FATE_ASSIGNMENT_AUTHORIZED_BY_THIS_SLICE=false",
    "UNKNOWN_FATE_COUNT=5",
    "BYPASS_PATH_COUNT=5",
    "BYPASS_SET_CHANGED=false",
    "CONSOLIDATION_STATUS=NOT_STARTED",
    "CONVERSION_READY=false",
    "NEXT_PRODUCTIVE_CONVERSION_SLICE_AUTHORIZED=false",
    "C2_INPUT_AUTHORITIES=UNRESOLVED",
    "NO_RUNTIME_REWIRE=true",
    "NO_SIZING_MATH_CHANGE=true",
    "NO_CRS_SCOPE_EXPANSION=true",
    "NO_REPO_WIDE_OWNER_PROMOTION=true",
    "NO_FOREIGN_TOKEN_NORMALIZATION=true",
    "DEPRECATE_LEGACY_PATH_IS_NOT_OPERATOR_FATE=true",
    "DEPRECATED_QUARANTINED_IS_NOT_OPERATOR_FATE=true",
    "SINGULAR_REPO_WIDE_OWNER_REQUIRED=false",
    "MV2_INTENT_BOUND_QUANTITY_ALGEBRA_OWNER=src.governance.capital_risk_sizing_v1",
    "MV2_INTENT_BOUND_QUANTITY_ALGEBRA_OWNER_SCOPE=mv2_governance_intent_bound",
    "CANONICAL_RISK_SIZING_OWNER=UNRESOLVED",
    "DECISION_AUTHORITY=SCOPED_OPERATOR_GO",
    "DECISION_AUTHORITY_HOLDER=Peak_Trade_Operator",
    "LIVE_AUTHORIZED=false",
    "ORDERS_ENABLED=false",
    "PRODUCTIVE_RUNTIME_SEMANTICS_CHANGED=false",
)

REQUIRED_SEMANTIC_FIELDS = (
    "normative_meaning",
    "required_evidence_for_assignment",
    "forbidden_interpretations",
    "runtime_effect_of_this_freeze",
    "relation_to_crs_mv2_scope",
    "later_implementation_requires_separate_runtime_go",
    "later_assignment_requires_scoped_operator_go",
)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _load_contract() -> dict:
    return json.loads(_read(CONTRACT_JSON))


def _load_inventory() -> dict:
    return json.loads(_read(OWNER_INVENTORY_JSON))


def _validate_fate_assignment(
    *,
    fate_id: str,
    evidence_present: bool,
    scoped_operator_go_present: bool,
    allowed_tokens: set[str],
    foreign_tokens: set[str],
    required_evidence_by_token: dict[str, list],
) -> str:
    """Fail-closed validator for later adjudication (contract-bound, no runtime).

    Parameter is named fate_id (not token=...) so Policy Critic NO_SECRETS
    length heuristics do not false-positive on public fate vocabulary literals.
    """
    if fate_id in foreign_tokens:
        return "REJECT_FOREIGN_TOKEN"
    if fate_id not in allowed_tokens:
        return "REJECT_UNKNOWN_TOKEN"
    if fate_id == "UNKNOWN":
        return "ACCEPT_UNKNOWN_FAIL_CLOSED"
    if not scoped_operator_go_present:
        return "REJECT_MISSING_DECISION_AUTHORITY"
    required = required_evidence_by_token.get(fate_id) or []
    if required and not evidence_present:
        return "REJECT_MISSING_REQUIRED_EVIDENCE"
    return "ACCEPT"


def test_contract_doc_markers_present() -> None:
    text = _read(CONTRACT_DOC)
    for marker in REQUIRED_DOC_MARKERS:
        assert marker in text, f"missing doc marker: {marker}"
    assert "PER_BYPASS_FATE_ADJUDICATION_EXECUTED=true" not in text
    assert "CONVERSION_READY=true" not in text
    assert "BYPASS_SET_CHANGED=true" not in text
    assert "PRODUCTIVE_RUNTIME_SEMANTICS_CHANGED=true" not in text


def test_allowed_fate_tokens_exactly_pinned() -> None:
    payload = _load_contract()
    tokens = payload["allowed_operator_fate_tokens_sorted"]
    assert tokens == list(EXPECTED_ALLOWED_TOKENS)
    assert tokens == sorted(tokens)
    assert set(tokens) == set(EXPECTED_ALLOWED_TOKENS)
    semantics = payload["fate_token_semantics"]
    assert set(semantics.keys()) == set(EXPECTED_ALLOWED_TOKENS)
    for token in EXPECTED_ALLOWED_TOKENS:
        row = semantics[token]
        for field in REQUIRED_SEMANTIC_FIELDS:
            assert field in row, f"{token} missing {field}"
        assert row["runtime_effect_of_this_freeze"] == "NONE"


def test_unknown_remains_fail_closed_and_admissible() -> None:
    payload = _load_contract()
    assert "UNKNOWN" in payload["allowed_operator_fate_tokens_sorted"]
    unknown = payload["fate_token_semantics"]["UNKNOWN"]
    assert unknown["runtime_effect_of_this_freeze"] == "NONE"
    assert payload["markers"]["UNKNOWN_FATE_COUNT"] == 5
    assert (
        payload["later_per_bypass_adjudication_fail_closed_rules"][
            "missing_or_conflicting_evidence_must_remain_unknown_or_conflicting"
        ]
        == "FAIL_CLOSED"
    )
    result = _validate_fate_assignment(
        fate_id="UNKNOWN",
        evidence_present=False,
        scoped_operator_go_present=False,
        allowed_tokens=set(EXPECTED_ALLOWED_TOKENS),
        foreign_tokens=set(FOREIGN_TOKENS),
        required_evidence_by_token={
            k: v["required_evidence_for_assignment"]
            for k, v in payload["fate_token_semantics"].items()
        },
    )
    assert result == "ACCEPT_UNKNOWN_FAIL_CLOSED"


def test_unknown_tokens_and_foreign_tokens_rejected() -> None:
    payload = _load_contract()
    allowed = set(payload["allowed_operator_fate_tokens_sorted"])
    foreign = {row["token"] for row in payload["foreign_tokens_explicitly_not_operator_fate"]}
    assert foreign == set(FOREIGN_TOKENS)
    required = {
        k: v["required_evidence_for_assignment"] for k, v in payload["fate_token_semantics"].items()
    }
    assert (
        _validate_fate_assignment(
            fate_id="DEPRECATE_LEGACY_PATH",
            evidence_present=True,
            scoped_operator_go_present=True,
            allowed_tokens=allowed,
            foreign_tokens=foreign,
            required_evidence_by_token=required,
        )
        == "REJECT_FOREIGN_TOKEN"
    )
    assert (
        _validate_fate_assignment(
            fate_id="DEPRECATED_QUARANTINED",
            evidence_present=True,
            scoped_operator_go_present=True,
            allowed_tokens=allowed,
            foreign_tokens=foreign,
            required_evidence_by_token=required,
        )
        == "REJECT_FOREIGN_TOKEN"
    )
    assert (
        _validate_fate_assignment(
            fate_id="NOT_A_REAL_FATE",
            evidence_present=True,
            scoped_operator_go_present=True,
            allowed_tokens=allowed,
            foreign_tokens=foreign,
            required_evidence_by_token=required,
        )
        == "REJECT_UNKNOWN_TOKEN"
    )


def test_assignment_without_authority_or_evidence_rejected() -> None:
    payload = _load_contract()
    allowed = set(payload["allowed_operator_fate_tokens_sorted"])
    foreign = {row["token"] for row in payload["foreign_tokens_explicitly_not_operator_fate"]}
    required = {
        k: v["required_evidence_for_assignment"] for k, v in payload["fate_token_semantics"].items()
    }
    assert (
        _validate_fate_assignment(
            fate_id="KEEP_PARALLEL_NON_CANONICAL",
            evidence_present=True,
            scoped_operator_go_present=False,
            allowed_tokens=allowed,
            foreign_tokens=foreign,
            required_evidence_by_token=required,
        )
        == "REJECT_MISSING_DECISION_AUTHORITY"
    )
    assert (
        _validate_fate_assignment(
            fate_id="INTEND_REBIND_TO_CRS",
            evidence_present=False,
            scoped_operator_go_present=True,
            allowed_tokens=allowed,
            foreign_tokens=foreign,
            required_evidence_by_token=required,
        )
        == "REJECT_MISSING_REQUIRED_EVIDENCE"
    )
    assert (
        _validate_fate_assignment(
            fate_id="KEEP_PARALLEL_NON_CANONICAL",
            evidence_present=True,
            scoped_operator_go_present=True,
            allowed_tokens=allowed,
            foreign_tokens=foreign,
            required_evidence_by_token=required,
        )
        == "ACCEPT"
    )


def test_decision_authority_is_scoped_operator_go() -> None:
    payload = _load_contract()
    auth = payload["decision_authority"]
    assert auth["decision_authority_class"] == "SCOPED_OPERATOR_GO"
    assert auth["decision_authority_holder"] == "Peak_Trade_Operator"
    assert (
        auth["decision_authority_gate"]
        == "EXPLICIT_SCOPED_OPERATOR_GO_FOR_WP_B05_BYPASS_FATE_OPERATOR_ADJUDICATION_V1"
    )
    assert auth["authority_effect_of_this_freeze"] == "NONE"
    assert auth["may_assign_per_bypass_fate_in_this_slice"] is False
    for forbidden in (
        "src.governance.capital_risk_sizing_v1",
        "CURRENT_SYSTEM_INTERACTION_AUTHORITY_MAP_V1",
        "CODE_OWNERSHIP",
        "REACHABILITY",
        "CHAT_MEMORY",
        "FILENAME_OR_AGE_HEURISTIC",
    ):
        assert forbidden in auth["decision_authority_not"]
    for ref in auth["evidence_refs"]:
        assert (REPO_ROOT / ref).is_file(), f"missing authority evidence: {ref}"


def test_all_five_current_fates_remain_unknown() -> None:
    payload = _load_contract()
    pins = payload["current_bypass_fate_pins"]
    assert set(pins.keys()) == set(EXPECTED_BYPASS_IDS)
    assert all(v == "UNKNOWN" for v in pins.values())
    assert payload["markers"]["UNKNOWN_FATE_COUNT"] == 5
    assert payload["markers"]["BYPASS_PATH_COUNT"] == 5
    assert payload["markers"]["BYPASS_SET_CHANGED"] is False
    assert payload["markers"]["PER_BYPASS_FATE_ADJUDICATION_EXECUTED"] is False

    inventory = _load_inventory()
    inventored = {b["id"]: b["operator_fate_adjudication"] for b in inventory["bypass_paths"]}
    assert set(inventored.keys()) == set(EXPECTED_BYPASS_IDS)
    assert all(v == "UNKNOWN" for v in inventored.values())
    assert inventored == pins


def test_no_runtime_semantics_claimed_and_boundary_pins_hold() -> None:
    payload = _load_contract()
    markers = payload["markers"]
    assert markers["AUTHORITY_EFFECT"] == "NONE"
    assert markers["RUNTIME_EFFECT"] == "NONE"
    assert markers["CONVERSION_READY"] is False
    assert markers["NEXT_PRODUCTIVE_CONVERSION_SLICE_AUTHORIZED"] is False
    assert markers["CONSOLIDATION_STATUS"] == "NOT_STARTED"
    assert markers["C2_INPUT_AUTHORITIES"] == "UNRESOLVED"
    assert markers["NO_RUNTIME_REWIRE"] is True
    assert markers["NO_SIZING_MATH_CHANGE"] is True
    assert markers["NO_CRS_SCOPE_EXPANSION"] is True
    assert markers["NO_REPO_WIDE_OWNER_PROMOTION"] is True
    assert markers["CANONICAL_RISK_SIZING_OWNER"] == "UNRESOLVED"
    assert (
        markers["MV2_INTENT_BOUND_QUANTITY_ALGEBRA_OWNER"]
        == "src.governance.capital_risk_sizing_v1"
    )
    assert markers["MV2_INTENT_BOUND_QUANTITY_ALGEBRA_OWNER_SCOPE"] == "mv2_governance_intent_bound"
    assert markers["LIVE_AUTHORIZED"] is False
    assert markers["ORDERS_ENABLED"] is False

    related = payload["related_but_separate_contracts"]
    assert (
        related["risk_sizing_owner_inventory_ssot_v1"]
        == "COMPLETE_SEPARATE_UNCHANGED_FATES_REMAIN_UNKNOWN"
    )
    assert (
        related["risk_sizing_authority_decision_contract_freeze_v1"]
        == "COMPLETE_SEPARATE_UNCHANGED_C2_UNRESOLVED"
    )


def test_inventory_points_at_freeze_without_fate_mutation() -> None:
    inventory = _load_inventory()
    markers = inventory["markers"]
    assert markers.get("FATE_VOCABULARY_SOURCE") == (
        "config/governance/risk_sizing_bypass_fate_vocabulary_and_decision_authority_freeze_v1.json"
    )
    assert markers.get("OPERATOR_FATE_ADJUDICATION_EXECUTED") is False
    related = inventory["risk_sizing_owner_and_bypass_surface_contract"][
        "related_but_separate_contracts"
    ]
    assert (
        related["risk_sizing_bypass_fate_vocabulary_and_decision_authority_freeze_v1"]
        == "COMPLETE_SEPARATE_VOCABULARY_AND_DECISION_AUTHORITY_ONLY_FATES_REMAIN_UNKNOWN"
    )
    for bypass in inventory["bypass_paths"]:
        assert bypass["operator_fate_adjudication"] == "UNKNOWN"


def test_productive_src_does_not_import_freeze_contract() -> None:
    needles = (
        "risk_sizing_bypass_fate_vocabulary_and_decision_authority_freeze",
        "bypass_fate_vocabulary_and_decision_authority_freeze_v1",
    )
    hits: list[str] = []
    for path in (REPO_ROOT / "src").rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        if any(n in text for n in needles):
            hits.append(str(path.relative_to(REPO_ROOT)))
    assert hits == []
