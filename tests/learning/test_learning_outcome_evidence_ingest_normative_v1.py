"""Contract tests for LEARNING_OUTCOME_EVIDENCE_INGEST_AND_STATE_NORMATIVE_V1."""

from __future__ import annotations

import json
from pathlib import Path

from src.learning.deterministic_decision_outcome_v0.authority_v0 import (
    LEARNING_PRODUCTIVE_AUTHORITY,
    PROMOTION_AUTHORITY_ACTIVATION,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
DECISION_PATH = (
    REPO_ROOT / "config/governance/learning_outcome_evidence_ingest_and_state_decision_v1.json"
)
NORMATIVE_SPEC = (
    REPO_ROOT / "docs/ops/specs/LEARNING_OUTCOME_EVIDENCE_INGEST_AND_STATE_NORMATIVE_V1.md"
)


def test_normative_spec_and_decision_present() -> None:
    assert NORMATIVE_SPEC.is_file()
    assert DECISION_PATH.is_file()
    text = NORMATIVE_SPEC.read_text(encoding="utf-8")
    assert "DOCS_TOKEN_LEARNING_OUTCOME_EVIDENCE_INGEST_AND_STATE_NORMATIVE_V1" in text
    assert "ARCHITECTURE_CHOICE=A+C" in text
    assert "RATIFIED_UPDATE_SEMANTICS" in text
    assert "next_cycle_economic_score_label" in text


def test_machine_readable_guards() -> None:
    decision = json.loads(DECISION_PATH.read_text(encoding="utf-8"))
    assert decision["architecture_choice"] == "A+C"
    assert decision["learning_productive_authority"] == "NONE"
    assert decision["promotion_join_authorized"] is False
    assert decision["drift_auto_projection_authorized"] is False
    assert LEARNING_PRODUCTIVE_AUTHORITY == "NONE"
    assert PROMOTION_AUTHORITY_ACTIVATION is False
