"""Contract: STEP 29U binding/implementation inventory v0 (docs-only, non-activating)."""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
INVENTORY = (
    REPO_ROOT
    / "docs"
    / "ops"
    / "runbooks"
    / "STEP_29U_CANONICAL_BINDING_AND_IMPLEMENTATION_INVENTORY_V0.md"
)
RUNBOOK = (
    REPO_ROOT / "docs" / "governance" / "Peak_Trade_Kanonisches_Vollautonomie_Runbook_v4.4.12.md"
)
READINESS_CONTRACT = (
    REPO_ROOT / "docs" / "ops" / "runbooks" / "SHADOW_PREPARATION_READINESS_GATE_CONTRACT_V0.md"
)
CURRENT_FOCUS = REPO_ROOT / "docs" / "ops" / "roadmap" / "CURRENT_FOCUS.md"
SOAK_README = (
    REPO_ROOT
    / "evidence"
    / "ops"
    / "okx_futures_shadow_no_order"
    / "2026-07-25_postmerge_600s_soak"
    / "README.md"
)

STEP29U_HEADING = "## STEP 29U — Shadow"
REQUIRED_STATES = (
    "SEMANTICALLY_DEFINED",
    "INVENTORIED",
    "BINDING_SPEC_RATIFIED",
    "IMPLEMENTED_OFFLINE",
    "VERIFIED_OFFLINE",
    "ACTIVATION_ELIGIBLE",
    "ACTIVATED",
)
REQUIRED_COMPONENTS = (
    "canonical_mode_identity",
    "lifecycle_owner",
    "session_state_machine",
    "canonical_decision_consumption",
    "risk_consumption",
    "execution_no_order_boundary",
    "reconciliation",
    "evidence_provenance",
    "failure_classification",
    "scheduler_runtime_boundary",
    "operator_go_boundary",
)


def _read(path: Path) -> str:
    assert path.is_file(), f"missing required document: {path}"
    return path.read_text(encoding="utf-8")


def test_inventory_document_exists_and_declares_non_activating_pass_split_v0() -> None:
    text = _read(INVENTORY)
    assert "STEP_29U_BINDING_IMPLEMENTATION_INVENTORY_V0=true" in text
    assert "STEP_29U_INVENTORY_PASS=true" in text
    assert "STEP_29U_BINDING_SPEC_PASS=true" in text
    assert "STEP_29U_IMPLEMENTATION_PASS=true" in text
    assert "STEP_29U_ACTIVATION_PASS=false" in text
    assert "AUTHORITY_EFFECT=NONE" in text
    assert "NON_ACTIVATING=true" in text
    assert "SECOND_TRUTH_INTRODUCED=false" in text


def test_inventory_keeps_canonical_absence_open_and_unbound_v0() -> None:
    text = _read(INVENTORY)
    assert "CANONICAL_STEP_29U_ABSENT=OPEN_INTENTIONAL_ACTIVATION_PREREQUISITE" in text
    assert "ABSENCE_MEANS_ACTIVATION_BINDING_ABSENT=true" in text
    assert "STEP_29U_IMPLEMENTED=true" in text
    assert "STEP_29U_BOUND_OFFLINE=true" in text
    assert "STEP_29U_VERIFIED_OFFLINE=true" in text
    assert "STEP_29U_ACTIVATED=false" in text
    assert "CANONICAL_STEP_29U_BOUND=false" in text
    for line in text.splitlines():
        stripped = line.strip()
        assert stripped != "STEP_29U_ACTIVATED=true"
        assert stripped != "CANONICAL_STEP_29U_BOUND=true"


def test_inventory_does_not_collapse_state_model_v0() -> None:
    text = _read(INVENTORY)
    for state in REQUIRED_STATES:
        assert state in text, state
    assert "STEP_29U_STATE_AFTER_THIS_SLICE=VERIFIED_OFFLINE" in text
    assert "STEP_29U_STATE_IMPLIES_ABSENCE_CLEARED=false" in text


def test_inventory_classifies_required_components_v0() -> None:
    text = _read(INVENTORY)
    for component in REQUIRED_COMPONENTS:
        assert f"`{component}`" in text or component in text, component
    for token in (
        "EXISTING_CANONICAL_REUSABLE",
        "EXISTING_NON_AUTHORITY_REUSABLE",
        "PRESENT_BUT_UNBOUND",
        "MISSING",
        "FUTURE_ONLY",
        "FORBIDDEN_FOR_STEP_29U",
    ):
        assert token in text, token


def test_inventory_defers_semantics_ssot_to_runbook_v0() -> None:
    text = _read(INVENTORY)
    assert "STEP_29U_SEMANTICS_SSOT=runbook.STEP_29U" in text
    assert "INVENTORY_CONTRACT_IS_NOT_SEMANTICS_SSOT=true" in text
    assert "Peak_Trade_Kanonisches_Vollautonomie_Runbook_v4.4.12.md" in text
    assert STEP29U_HEADING in _read(RUNBOOK)
    assert "READINESS_PRODUCER_CANNOT_BIND_STEP_29U=true" in text
    assert "READINESS_PRODUCER_CANNOT_IMPLEMENT_STEP_29U=true" in text
    assert "READINESS_PRODUCER_CANNOT_ACTIVATE_STEP_29U=true" in text


def test_inventory_forbids_soak_as_step29u_closure_v0() -> None:
    text = _read(INVENTORY)
    assert "SOAK_DOES_NOT_CLEAR_CANONICAL_STEP_29U_ABSENT=true" in text
    assert "SOAK_DOES_NOT_PROVE_STEP_29U_IMPLEMENTED=true" in text
    assert "FORBIDDEN_IF_SOAK_PROVEN_IMPLIES_STEP29U_PASS=true" in text
    assert "PROVEN_POST_MERGE_600S_SOAK" in _read(SOAK_README)
    assert "CANONICAL_STEP_29U_ABSENT" in _read(SOAK_README)


def test_inventory_forbids_readiness_as_binding_authority_v0() -> None:
    text = _read(INVENTORY)
    assert "FORBIDDEN_IF_READINESS_PROJECTION_CLAIMS_STEP29U_BINDING_AUTHORITY=true" in text
    assert "READINESS_GATE_IS_NOT_STEP_29U=true" in text
    readiness = _read(READINESS_CONTRACT)
    assert "READINESS_PRODUCER_CANNOT_BIND_STEP_29U=true" in readiness
    assert "NOT_STEP_29U_IMPLEMENTATION=true" in readiness


def test_inventory_forbids_collapsing_implementation_and_activation_v0() -> None:
    text = _read(INVENTORY)
    assert "FORBIDDEN_IF_INVENTORY_PASS_COLLAPSED_INTO_ACTIVATION_PASS=true" in text
    assert "FORBIDDEN_IF_OFFLINE_IMPLEMENTED_IMPLIES_ACTIVATED=true" in text
    assert "ALLOWED_OFFLINE_IMPLEMENTED_WHILE_ACTIVATION_ABSENT_OPEN=true" in text
    assert "STEP_29U_ACTIVATION_PASS=false" in text
    assert "STEP_29U_IMPLEMENTATION_DOES_NOT_AUTHORIZE_ACTIVATION=true" in text
    assert "SEPARATE_OPERATOR_GO_REQUIRED=true" in text


def test_inventory_records_external_blocker_policy_without_dashboard_silent_conversion_v0() -> None:
    text = _read(INVENTORY)
    assert "ECONOMIC_VALIDITY_RELATION=PROMOTION_AND_ACTIVATION_SEQUENCING_PREREQUISITE" in text
    assert (
        "MARKET_DASHBOARD_INTRABAR_RELATION="
        "INDEPENDENT_WORKSTREAM_AND_ACTIVATION_SEQUENCING_GATE" in text
    )
    assert "MARKET_DASHBOARD_VISIBLE_INTRABAR_CONTINUITY=OPEN" in text
    assert "RUNTIME_BRIDGE_RELATION=HARD_ACTIVATION_PREREQUISITE" in text
    assert "SCHEDULER_RELATION=HARD_ACTIVATION_PREREQUISITE" in text
    assert "NETWORK_RUNTIME_RELATION=HARD_PROHIBITION_UNTIL_EXPLICIT_GO" in text
    assert "OPERATOR_GO_RELATION=HARD_ACTIVATION_PREREQUISITE" in text


def test_inventory_defines_implemented_offline_capability_and_next_activation_gate_v0() -> None:
    text = _read(INVENTORY)
    assert "IMPLEMENTED_CAPABILITY=STEP_29U_OFFLINE_CAPABILITY_V0" in text
    assert "STEP_29U_LIFECYCLE_OWNER=ops.step_29u_offline_capability_v0" in text
    assert "STEP_29U_OPERATOR_COMMAND=" in text
    assert (
        "NEXT_AUTHORIZED_SLICE=STEP_29U_ACTIVATION_ELIGIBILITY_INVENTORY_ONLY_AFTER_SEPARATE_OPERATOR_GO"
        in text
    )
    assert "SEPARATE_OPERATOR_GO_REQUIRED=true" in text


def test_current_focus_and_readiness_point_to_inventory_without_claiming_activation_v0() -> None:
    focus = _read(CURRENT_FOCUS)
    readiness = _read(READINESS_CONTRACT)
    assert "STEP_29U_CANONICAL_BINDING_AND_IMPLEMENTATION_INVENTORY_V0.md" in focus
    assert "STEP_29U_CANONICAL_BINDING_AND_IMPLEMENTATION_INVENTORY_V0.md" in readiness
    assert "CANONICAL_STEP_29U_ABSENT" in focus
    assert "OPEN_INTENTIONAL_ACTIVATION_PREREQUISITE" in focus
    assert "STEP_29U_IMPLEMENTED=true" in focus
    assert "STEP_29U_ACTIVATED=false" in focus
    assert "STEP_29U_ACTIVATED=true" not in focus
    assert "ops.step_29u_offline_capability_v0" in focus
