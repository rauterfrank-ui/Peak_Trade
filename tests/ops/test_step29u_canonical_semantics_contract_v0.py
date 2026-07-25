"""Static contract: canonical STEP 29U semantics ratification (docs-only, unbound)."""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
RUNBOOK = (
    REPO_ROOT / "docs" / "governance" / "Peak_Trade_Kanonisches_Vollautonomie_Runbook_v4.4.12.md"
)
READINESS_CONTRACT = (
    REPO_ROOT / "docs" / "ops" / "runbooks" / "SHADOW_PREPARATION_READINESS_GATE_CONTRACT_V0.md"
)

STEP29U_HEADING = "## STEP 29U — Shadow"
STEP29V_HEADING = "## STEP 29V — Paper"


def _read(path: Path) -> str:
    assert path.is_file(), f"missing required document: {path}"
    return path.read_text(encoding="utf-8")


def _step29u_body() -> str:
    text = _read(RUNBOOK)
    assert STEP29U_HEADING in text, "missing STEP 29U heading"
    start = text.index(STEP29U_HEADING)
    end = text.index(STEP29V_HEADING, start)
    body = text[start:end]
    # Body must contain more than the bare heading line.
    assert len(body.strip().splitlines()) > 1, "STEP 29U body must not be empty"
    return body


def test_step29u_canonical_body_is_explicit_and_non_empty_v0() -> None:
    body = _step29u_body()
    assert "STEP29U_SEMANTICS_RATIFIED=true" in body
    assert "OFFLINE_COMPOSITION_BOUND_INTO_CANONICAL_SHADOW_NO_ORDER_NOT_ACTIVATED" in body


def test_step29u_declares_bound_implemented_not_activated_invariants_v0() -> None:
    body = _step29u_body()
    for marker in (
        "CANONICAL_STEP_29U_BOUND=true",
        "CANONICAL_SHADOW_MODE_EXISTS=true",
        "STEP_29U_IMPLEMENTED=true",
        "STEP_29U_ACTIVATED=false",
        "CANONICAL_STEP_29U_ABSENT=CLEARED_COMPOSITION_BOUND_ACTIVATION_STILL_UNAUTHORIZED",
    ):
        assert marker in body, marker


def test_step29u_declares_non_activating_and_separate_operator_go_v0() -> None:
    body = _step29u_body()
    assert "NON_ACTIVATING=true" in body
    assert "AUTHORITY_EFFECT=NONE" in body
    assert "SEPARATE_OPERATOR_GO_REQUIRED_FOR_STEP29U_IMPLEMENTATION=true" in body
    assert "SEPARATE_OPERATOR_GO_REQUIRED_FOR_ANY_ACTIVATION_STAGE=true" in body
    assert "STEP_29U_IMPLEMENTATION_AUTHORIZED_BY_THIS_RATIFICATION=false" in body


def test_step29u_lists_historical_surfaces_as_non_equivalent_v0() -> None:
    body = _step29u_body()
    assert "HISTORICAL_SHADOW_SURFACES_NON_EQUIVALENT_TO_STEP_29U=true" in body
    assert "READINESS_GATE_IS_NOT_STEP_29U=true" in body
    for token in (
        "ShadowOrderExecutor",
        "scripts/run_shadow_execution.py",
        "ShadowPaperSession",
        "scripts/run_shadow_paper_session.py",
        "Shadow-247",
        "ops.shadow_preparation_readiness_gate_v0",
    ):
        assert token in body, token


def test_step29u_preserves_open_dashboard_blocker_v0() -> None:
    body = _step29u_body()
    assert "MARKET_DASHBOARD_VISIBLE_INTRABAR_CONTINUITY=OPEN" in body
    assert "DASHBOARD_BLOCKER_STATE=OPEN" in body
    assert "DASHBOARD_BLOCKER_RESOLVED=false" in body
    assert "DASHBOARD_BLOCKER_WAIVED=false" in body
    assert "DASHBOARD_BLOCKER_RESOLVED=true" not in body
    assert "DASHBOARD_BLOCKER_WAIVED=true" not in body


def test_step29u_does_not_declare_activation_or_scheduler_runtime_v0() -> None:
    body = _step29u_body()
    forbidden = (
        "CANONICAL_SHADOW_SESSION_IMPLEMENTED=true",
        "CANONICAL_SHADOW_SCHEDULER_JOB_BOUND=true",
        "RUNTIME_ACTIVATION_AUTHORIZED=true",
        "SHADOW_ACTIVATION_AUTHORIZED=true",
        "STEP_29U_ACTIVATED=true",
    )
    for token in forbidden:
        assert token not in body, token


def test_step29u_preserves_economic_and_activation_locks_v0() -> None:
    body = _step29u_body()
    for marker in (
        "ECONOMIC_VALIDITY_OFFLINE_GATE_PASS=false",
        "SHADOW_PREPARATION_COMPLETE=false",
        "SHADOW_ACTIVATION_AUTHORIZED=false",
        "PAPER_ACTIVATION_AUTHORIZED=false",
        "TESTNET_ACTIVATION_AUTHORIZED=false",
        "SCHEDULER_ACTIVATION_AUTHORIZED=false",
        "RUNTIME_ACTIVATION_AUTHORIZED=false",
        "LIVE_AUTHORIZED=false",
        "ORDERS=false",
        "RUNTIME_BRIDGE_STATE=BOUND_NOT_ACTIVATED",
    ):
        assert marker in body, marker


def test_readiness_contract_remains_authority_free_and_observes_binding_v0() -> None:
    text = _read(READINESS_CONTRACT)
    assert "AUTHORITY_EFFECT=NONE" in text
    assert "NOT_STEP_29U_IMPLEMENTATION=true" in text
    assert "CANONICAL_STEP_29U_BOUND=true" in text
    assert "CANONICAL_SHADOW_MODE_EXISTS=true" in text
    assert "READINESS_PRODUCER_CANNOT_BIND_STEP_29U=true" in text
    assert "READINESS_PRODUCER_CANNOT_IMPLEMENT_STEP_29U=true" in text
    assert "READINESS_PRODUCER_CANNOT_ACTIVATE_STEP_29U=true" in text
    assert "Peak_Trade_Kanonisches_Vollautonomie_Runbook_v4.4.12.md" in text, (
        "readiness contract must cross-link canonical STEP 29U owner"
    )
    assert STEP29U_HEADING in text
