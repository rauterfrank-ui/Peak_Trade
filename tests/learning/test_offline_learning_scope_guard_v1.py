"""Common source/capital/config/metric scope precedes differing pool consumers."""

import pytest

from src.learning.deterministic_decision_outcome_v0.errors_v0 import DdoValidationError
from src.learning.deterministic_decision_outcome_v0.ledger_v0 import AppendOnlyDdoLedgerV0
from src.learning.deterministic_decision_outcome_v0.learning_scope_guard_v1 import (
    require_learning_scope_v1,
)
from src.learning.deterministic_decision_outcome_v0.outcome_evidence_provenance_v1 import (
    build_outcome_evidence_provenance_v1,
)
from src.learning.deterministic_decision_outcome_v0.optimization_provenance_eligibility_v1 import (
    evaluate_optimization_provenance_eligibility_v1,
)
from src.ops.full_core_live_path_composition_root_v1.natural_enter_cross_session_outcome_closure_v1.offline_v1 import (
    create_explicit_offline_pending_v1,
    advance_explicit_offline_pending_v1,
)
from tests.ops.test_explicit_offline_pending_learning_v1 import _case
import json


def _measured(tmp_path):
    args, t = _case(tmp_path)
    root = create_explicit_offline_pending_v1(**args)
    advance_explicit_offline_pending_v1(root=root, as_of_unix=t, source=args["source"])
    capsule = json.loads((root / "capsule_v1.json").read_text())
    outcome = dict(
        next(
            r
            for r in AppendOnlyDdoLedgerV0(root / "LANE_1/ddo_learning_capture_v1.jsonl").read_all()
            if r["schema_name"] == "outcome_record"
        )
    )
    return root, capsule, outcome


@pytest.mark.parametrize(
    "field,value",
    [
        ("outcome_semantic_class", "OBSERVED_PRODUCTIVE_PRE_EXTERNAL"),
        ("market_observation_source", "PUBLIC_MD"),
        ("external_capital_flow_class", "DEPOSIT"),
        ("code_sha", "other"),
        ("config_hash", "b" * 64),
        ("outcome_scalar_kind", "ABS_RETURN"),
        ("evaluation_horizon", "POSITION_LIFECYCLE"),
        ("evidence_pool_class", "REPLAY_HISTORICAL"),
        ("metric_version", "PNL_V1"),
        ("account_identity", ""),
    ],
)
def test_common_scope_rejects_cross_class_capital_metric_and_configuration(tmp_path, field, value):
    _root, c, outcome = _measured(tmp_path)
    require_learning_scope_v1(outcome=outcome, scope=c["scope"], target=c["target"])
    scope = {**c["scope"], field: value}
    with pytest.raises(DdoValidationError):
        require_learning_scope_v1(outcome=outcome, scope=scope, target=c["target"])


@pytest.mark.parametrize(
    "capital", ["DEPOSIT", "WITHDRAWAL", "INTERNAL_TRANSFER", "AMBIGUOUS", "UNKNOWN"]
)
def test_capital_cannot_be_admitted_by_changing_both_declarations(tmp_path, capital):
    root, c, outcome = _measured(tmp_path)
    raw = dict(outcome["outcome_evidence_provenance"])
    raw.pop("provenance_digest")
    raw["external_capital_flow_class"] = capital
    p = dict(build_outcome_evidence_provenance_v1(raw))
    outcome["outcome_evidence_provenance"] = p
    with pytest.raises(DdoValidationError):
        require_learning_scope_v1(
            outcome=outcome,
            scope={**c["scope"], "external_capital_flow_class": capital},
            target=c["target"],
        )
    if capital != "UNKNOWN":
        evidence = json.loads((root / "optimization_input_v1.json").read_text())["evidence"]
        evidence.update(
            outcome_evidence_provenance=p, outcome_evidence_provenance_digest=p["provenance_digest"]
        )
        result = evaluate_optimization_provenance_eligibility_v1(evidence)
        assert (
            not result.admitted
            and result.reason_code == "EXTERNAL_CAPITAL_FLOW_NOT_TRADING_OUTCOME"
        )
