"""Marker tests for Scope-Init min/max_scope_band semantic class Owner persist."""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CONTRACT = REPO_ROOT / "docs/ops/specs/SCOPE_INIT_MIN_MAX_SEMANTIC_CLASS_OWNER_DECISION_V1.md"
RUNBOOK = REPO_ROOT / "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md"


def _contract_text() -> str:
    return CONTRACT.read_text(encoding="utf-8")


def _runbook_text() -> str:
    return RUNBOOK.read_text(encoding="utf-8")


def test_contract_file_exists() -> None:
    assert CONTRACT.is_file()


def test_unit_class_and_roles_persisted() -> None:
    text = _contract_text()
    assert "SCOPE_INIT_MIN_MAX_UNIT_CLASS=PRICE_DISTANCE_BOUNDS" in text
    assert "MIN_SCOPE_BAND_ROLE=LOWER_BOUND" in text
    assert "MAX_SCOPE_BAND_ROLE=UPPER_BOUND" in text
    assert "BOUNDED_QUANTITY=INITIAL_VOLATILITY_DISTANCE" in text
    assert "DIMENSIONAL_DOMAIN=SAME_PRICE_DISTANCE_DOMAIN_AS_VOL_TIMES_REFERENCE_PRICE" in text
    assert "MIN_MAX_SAME_CLASS=true" in text
    assert "OWNER=CanonicalScopeInitializationPolicyV1" in text
    assert "OWNER_SURFACE=_default_policies" in text
    assert "MIN_SCOPE_BAND_OWNER=NOT_CAP63" in text


def test_numeric_calibration_and_literals_remain_open_and_unchanged() -> None:
    text = _contract_text()
    assert "NUMERIC_CALIBRATION_ADJUDICATED=false" in text
    assert "CURRENT_50_500_CHANGED=false" in text
    assert "CURRENT_50_500_COMMENSURABILITY=UNADJUDICATED" in text
    assert "INSTRUMENT_NORMALIZATION_AUTHORIZED=false" in text
    assert "THRESHOLD_OR_DISTANCE_MUTATION_AUTHORIZED=false" in text
    assert "SCOPE_INITIALIZATION_FORMULA_CHANGED=false" in text
    assert "min_scope_band=50.0" in text
    assert "max_scope_band=500.0" in text
    assert "PRICE_DISTANCE_BOUNDS_IMPLIES_MAGNITUDE=false" in text
    assert "VOL_TIMES_PRICE_REQUIRES_MIN_MAX_TO_SCALE=false" in text


def test_cap63_and_cap65_remain_separate_and_unbound() -> None:
    text = _contract_text()
    assert "CAP63_AUTHORITY_CHANGED=false" in text
    assert "CAP65_AUTHORITY_CHANGED=false" in text
    assert "CAP63_OWNER_MERGE_AUTHORIZED=false" in text
    assert "CAP65_OWNER_MERGE_AUTHORIZED=false" in text
    assert "DERIVE_V1_BIND_AUTHORIZED=false" in text
    assert "DERIVATION_RUNTIME_BIND_AUTHORIZED=false" in text
    assert "ATOMIC_RETIRE_BIND_AUTHORIZED=false" in text
    assert "OQ_C1_BOUND=false" in text
    assert "OQ_C2_BOUND=false" in text
    assert "SECTION_9_2_9_METADATA_TRACK=ORTHOGONAL" in text
    assert "CAP65_PROFIT_PROTECTION_OWNER=SEPARATE" in text


def test_reachability_not_repaired_and_next_dependency_is_numeric_policy() -> None:
    text = _contract_text()
    assert "REACHABILITY_REPAIR_AUTHORIZED=false" in text
    assert (
        "NEXT_UNRESOLVED_DEPENDENCY=OWNER_DECISION_SCOPE_INIT_PRICE_DISTANCE_BOUND_NUMERIC_POLICY"
        in text
    )
    assert "EXACT_NEXT_OWNER_GO_TOKEN=NOT_MINTED" in text
    assert "NUMERIC_POLICY_QUESTION_ANSWERED=false" in text
    assert "IMPLEMENTATION_READY=false" in text
    assert "initial_volatility_distance≈0.0025" in text


def test_runbook_persist_matches_contract_markers() -> None:
    text = _runbook_text()
    assert (
        "### 9.2.10 Canonical Scope Initialization min/max_scope_band semantic class Owner decision"
        in text
    )
    assert (
        "OWNER_GO=OWNER_GO_BOUNDED_SCOPE_INIT_MIN_MAX_SEMANTIC_CLASS_DECISION_DOCS_ONLY_V1" in text
    )
    assert "SCOPE_INIT_MIN_MAX_UNIT_CLASS=PRICE_DISTANCE_BOUNDS" in text
    assert "MIN_SCOPE_BAND_ROLE=LOWER_BOUND" in text
    assert "MAX_SCOPE_BAND_ROLE=UPPER_BOUND" in text
    assert "MIN_SCOPE_BAND_OWNER=NOT_CAP63" in text
    assert "NUMERIC_CALIBRATION_ADJUDICATED=false" in text
    assert "CURRENT_50_500_CHANGED=false" in text
    assert (
        "NEXT_UNRESOLVED_DEPENDENCY=OWNER_DECISION_SCOPE_INIT_PRICE_DISTANCE_BOUND_NUMERIC_POLICY"
        in text
    )
    assert "CAP63_AUTHORITY_CHANGED=false" in text
    assert "CAP65_AUTHORITY_CHANGED=false" in text
