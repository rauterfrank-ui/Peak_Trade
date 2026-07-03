"""Contract tests for final_research_fleet_v0_fleet_ratification_v0."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.research.final_research_fleet_offline_economic_evaluation_scope_ratification_v0 import (
    ECONOMIC_EVALUATION_AUTHORIZED,
    ECONOMIC_EVALUATION_SCOPE_RATIFIED,
    FINAL_RESEARCH_FLEET_BINDING_READY,
    NEW_CANDIDATES_RATIFIED,
    materialize_final_research_fleet_offline_economic_evaluation_scope_ratification_v0,
)
from src.research.final_research_fleet_v0_fleet_ratification_v0 import (
    CONFIG_REL_PATH,
    NEXT_CANONICAL_STEP,
    ValidationVerdict,
    materialize_final_research_fleet_v0_fleet_ratification_v0,
    validate_final_research_fleet_v0_fleet_ratification_v0,
)
from src.research.final_research_fleet_versioned_binding_completion_v0 import (
    materialize_final_research_fleet_versioned_binding_completion_v0,
)
from tests.research.test_final_research_fleet_versioned_binding_completion_v0 import (
    _build_production_result,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
_SOURCE_REF = "okx_public_instruments_swap:test"
_SOURCE_DIGEST = "c" * 64


@pytest.fixture(scope="module")
def canonical_completion():
    production, panel_series = _build_production_result()
    return materialize_final_research_fleet_versioned_binding_completion_v0(
        repo_root=REPO_ROOT,
        production_manifest=production.manifest,
        production_envelope=production.envelope,
        panel_series=panel_series,
        source_registration_ref=_SOURCE_REF,
        source_registration_digest=_SOURCE_DIGEST,
    )


@pytest.fixture(scope="module")
def canonical_scope(canonical_completion):
    return materialize_final_research_fleet_offline_economic_evaluation_scope_ratification_v0(
        repo_root=REPO_ROOT,
        fleet_binding_completion=canonical_completion,
    )


@pytest.fixture(scope="module")
def canonical_fleet_record(canonical_completion):
    return materialize_final_research_fleet_v0_fleet_ratification_v0(
        repo_root=REPO_ROOT,
        fleet_binding_completion=canonical_completion,
    )


def test_fleet_record_has_three_candidates(canonical_fleet_record: dict) -> None:
    assert len(canonical_fleet_record["candidate_ratification_records"]) == 3


def test_fleet_record_governance_flags(canonical_fleet_record: dict) -> None:
    assert canonical_fleet_record["final_research_fleet_binding_ready"] is True
    assert canonical_fleet_record["new_candidates_ratified"] is True
    assert canonical_fleet_record["economic_evaluation_scope_ratified"] is True
    assert canonical_fleet_record["economic_evaluation_authorized"] is False
    assert canonical_fleet_record["next_canonical_step"] == NEXT_CANONICAL_STEP
    assert FINAL_RESEARCH_FLEET_BINDING_READY is True
    assert NEW_CANDIDATES_RATIFIED is True
    assert ECONOMIC_EVALUATION_SCOPE_RATIFIED is True
    assert ECONOMIC_EVALUATION_AUTHORIZED is False


def test_validate_accepts_canonical_fleet_record(
    canonical_fleet_record: dict,
    canonical_completion: dict,
    canonical_scope: dict,
) -> None:
    result = validate_final_research_fleet_v0_fleet_ratification_v0(
        canonical_fleet_record,
        fleet_binding_completion=canonical_completion,
        scope_ratification=canonical_scope,
    )
    assert result.verdict == ValidationVerdict.ACCEPTED
    assert result.valid is True


def test_committed_fleet_config_exists_when_present() -> None:
    config_path = REPO_ROOT / CONFIG_REL_PATH
    if config_path.is_file():
        import json

        payload = json.loads(config_path.read_text(encoding="utf-8"))
        assert payload["economic_evaluation_authorized"] is False
        assert payload["new_candidates_ratified"] is True
