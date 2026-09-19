"""Contract tests for WP_DDO_OUTCOME_TO_PROMOTION_PRODUCTIVE_BINDING_NORMATIVE_V1."""

from __future__ import annotations

import ast
import json
from pathlib import Path

from src.learning.deterministic_decision_outcome_v0.authority_v0 import (
    LEARNING_PRODUCTIVE_AUTHORITY,
    PROMOTION_AUTHORITY_ACTIVATION,
    PROMOTION_AUTHORITY_EFFECT,
)
from src.learning.deterministic_decision_outcome_v0.promotion_controller_v0 import (
    PROMOTION_ELIGIBILITY_DRY_RUN,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
DECISION_PATH = (
    REPO_ROOT / "config/governance/ddo_outcome_to_promotion_productive_binding_decision_v1.json"
)
NORMATIVE_SPEC = (
    REPO_ROOT / "docs/ops/specs/DDO_OUTCOME_TO_PROMOTION_PRODUCTIVE_BINDING_NORMATIVE_V1.md"
)
PROMOTION_CONTROLLER = (
    REPO_ROOT / "src/learning/deterministic_decision_outcome_v0/promotion_controller_v0.py"
)


def test_normative_spec_and_decision_record_present() -> None:
    assert NORMATIVE_SPEC.is_file()
    assert DECISION_PATH.is_file()
    text = NORMATIVE_SPEC.read_text(encoding="utf-8")
    assert "DOCS_TOKEN_DDO_OUTCOME_TO_PROMOTION_PRODUCTIVE_BINDING_NORMATIVE_V1" in text
    assert text.lstrip().startswith("---")
    assert "ADJUDICATION=NO_N_BARS_TO_PROMOTION_BINDING" in text
    assert "OBSERVATION_NOT_PROMOTION=true" in text
    assert "OUTCOME_RECORD_EQ_VALIDATION_EVIDENCE_PACK=FORBIDDEN_ASSUMPTION" in text


def test_machine_readable_adjudication_c_and_guards() -> None:
    decision = json.loads(DECISION_PATH.read_text(encoding="utf-8"))
    assert decision["owner_adjudication_bound"] is True
    assert decision["adjudication"] == "NO_N_BARS_TO_PROMOTION_BINDING"
    assert decision["adjudication_code"] == "C"
    assert decision["governed_binding_required"] is False
    assert decision["separate_outcome_eligibility_path_required"] is False
    assert decision["implementation_authorized"] is False
    assert decision["productive_promotion_join_authorized"] is False
    guards = decision["capture_and_runtime_guards"]
    assert guards["promotion_authority_activation"] is False
    assert guards["promotion_authority_effect"] == "NONE"
    assert guards["external_effect_authorized"] is False
    assert decision["canonical_outcome_to_promotion_mapping"] == "ABSENT_FORBIDDEN_TO_ASSUME"


def test_runtime_authority_markers_unchanged_and_controller_input_contract() -> None:
    assert PROMOTION_AUTHORITY_ACTIVATION is False
    assert PROMOTION_AUTHORITY_EFFECT == "NONE"
    assert LEARNING_PRODUCTIVE_AUTHORITY == "NONE"
    assert PROMOTION_ELIGIBILITY_DRY_RUN is True
    source = PROMOTION_CONTROLLER.read_text(encoding="utf-8")
    assert "outcome_record" not in source
    tree = ast.parse(source)
    fn = next(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name == "evaluate_promotion_eligibility_v0"
    )
    arg_names = [a.arg for a in fn.args.kwonlyargs]
    assert "policy" in arg_names
    assert "candidate" in arg_names
    assert "evidence_pack" in arg_names
    assert "outcome_record" not in arg_names
