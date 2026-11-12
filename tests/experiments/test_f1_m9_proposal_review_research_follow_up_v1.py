import json
import subprocess
from dataclasses import replace
from pathlib import Path

import pytest

from research.canonical_volatility_numeric_max_age_parameter_research_execution_v1.constants_v1 import (
    OPERATOR_BOUND_CANDIDATE_MAX_AGE_SECONDS,
)
from src.experiments import f1_m9_proposal_review_research_follow_up_v1 as follow_up
from src.governance.f1_m9_proposal_review_feedback_v1 import (
    evaluate_and_store_f1_m9_proposal_review_feedback_v1,
)
from src.meta.learning_loop.contract_safety_v1 import deterministic_json_dumps
from tests.governance.d27_native_baseline_fixtures_v1 import (
    build_fixture_native_baseline_evidence_v1,
)
from tests.governance.test_optimization_proposal_governance_ingress_v1 import _ingress_for_m9
from tests.research.test_canonical_volatility_numeric_max_age_parameter_research_execution_v1 import (
    _fixture_records,
)
from trading.master_v2.canonical_volatility_numeric_max_age_parameter_research_design_and_evidence_accumulation_contract_v1 import (
    append_max_age_research_evidence_ledger_record_v1,
)

ROOT = Path(__file__).resolve().parents[2]
RUNNER = "scripts/ops/run_canonical_volatility_numeric_max_age_parameter_research_execution_v1.py"
REPOSITORY_SHA = "a" * 40
CREATED_AT = "2026-11-12T09:00:00Z"


def _review(tmp_path, delta):
    ingress = _ingress_for_m9(tmp_path, parameter_config_delta=delta)
    store = tmp_path / "reviews"
    review = evaluate_and_store_f1_m9_proposal_review_feedback_v1(store_root=store, ingress=ingress)
    return follow_up.F1M9ProposalReviewResearchContextV1(
        review_store=store,
        original_ingress=ingress,
        review_policy_digest=review.review_policy_digest,
        review_feedback_digest=review.feedback_digest,
    )


def _run_cli(tmp_path, review, ledger, output):
    context_path = tmp_path / "review.json"
    context_path.write_text(
        deterministic_json_dumps(
            {
                "review_store": review.review_store.name,
                "original_ingress": dict(review.original_ingress),
                "review_policy_digest": review.review_policy_digest,
                "review_feedback_digest": review.review_feedback_digest,
            }
        ),
        encoding="utf-8",
    )
    baseline_path = tmp_path / "baseline.json"
    baseline_path.write_text(
        deterministic_json_dumps(build_fixture_native_baseline_evidence_v1()), encoding="utf-8"
    )
    result = subprocess.run(
        [
            "./scripts/pt",
            RUNNER,
            "--proposal-review-json",
            str(context_path),
            "--native-baseline-admission-json",
            str(baseline_path),
            "--ledger-path",
            str(ledger),
            "--output-root",
            str(output),
            "--repository-sha",
            REPOSITORY_SHA,
            "--created-at-utc",
            CREATED_AT,
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    return result


def _stdout_payload(result):
    assert "{" in result.stdout, result.stderr
    return json.loads(result.stdout[result.stdout.index("{") :])


def test_cold_governance_response_changes_the_normal_m9_cli_action(tmp_path):
    ledger = tmp_path / "m9.jsonl"
    for row in _fixture_records():
        append_max_age_research_evidence_ledger_record_v1(ledger_path=ledger, record=row.raw)
    original_ledger = ledger.read_bytes()

    admitted = _review(tmp_path, {"max_age_seconds": 300})
    denied = _review(tmp_path, {"max_age_seconds": 999})
    output = tmp_path / "follow-up"
    kept = _run_cli(tmp_path, admitted, ledger, output)
    assert kept.returncode == 0, kept.stderr
    assert _stdout_payload(kept)["action"] == "KEEP_ADMITTED_PROPOSAL"
    assert _stdout_payload(kept)["research"] is None
    assert not output.exists()

    launched = _run_cli(tmp_path, denied, ledger, output)
    assert launched.returncode == 0, launched.stderr
    response = _stdout_payload(launched)
    assert response["action"] == "RUN_REGISTERED_M9_RESEARCH"
    assert response["inputs"]["review_feedback_digest"] == denied.review_feedback_digest
    assert response["research"]["status"] == "PASS"
    assert response["research"]["final_holdout_executed"] is True
    assert json.loads((output / "candidate_domain.json").read_bytes())[
        "candidate_max_age_seconds"
    ] == list(OPERATOR_BOUND_CANDIDATE_MAX_AGE_SECONDS)
    assert (output / "input_research_ledger.jsonl").read_bytes() == original_ledger
    assert ledger.read_bytes() == original_ledger
    conclusion = json.loads((output / "research_conclusion.json").read_bytes())
    assert conclusion["execution_id"] == response["research"]["execution_id"]
    assert conclusion["numeric_threshold_selected"] is False
    assert conclusion["enforcement_applied"] is False

    replay = _run_cli(tmp_path, denied, ledger, output)
    assert replay.returncode == 0, replay.stderr
    assert _stdout_payload(replay) == response

    normal_output = tmp_path / "original-runner"
    normal = subprocess.run(
        [
            "./scripts/pt",
            RUNNER,
            "--native-baseline-admission-json",
            str(tmp_path / "baseline.json"),
            "--ledger-path",
            str(ledger),
            "--output-root",
            str(normal_output),
            "--repository-sha",
            REPOSITORY_SHA,
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert normal.returncode == 0, normal.stderr
    original = _stdout_payload(normal)
    assert original["status"] == response["research"]["status"]
    assert original["research_conclusion"] == response["research"]["research_conclusion"]
    assert original["final_holdout_executed"] is True

    with (output / "candidate_results.jsonl").open("ab") as stream:
        stream.write(b"\n")
    corrupted = _run_cli(tmp_path, denied, ledger, output)
    assert corrupted.returncode != 0
    assert "M9_REVIEW_RESEARCH_ARTIFACT_DIGEST_MISMATCH:candidate_results.jsonl" in corrupted.stderr


def test_other_denial_missing_evidence_and_policy_drift_do_not_start_research(
    tmp_path, monkeypatch
):
    denied = _review(tmp_path, {"max_age_seconds": 999})
    other = _review(tmp_path, {"fast": 10})
    output = tmp_path / "follow-up"
    kwargs = dict(
        repo_root=ROOT,
        native_baseline_evidence_v1={},
        ledger_path=None,
        output_root=output,
        repository_sha=None,
        created_at_utc=None,
    )
    run = follow_up.run_f1_m9_proposal_review_research_follow_up_v1
    assert run(context=denied, **kwargs)["action"] == "WAIT_FOR_M9_EVIDENCE"
    assert run(context=other, **kwargs)["action"] == "RESOLVE_ORIGINAL_REVIEW_REASONS"
    with pytest.raises(ValueError, match="M9_REVIEW_FEEDBACK_DIGEST_MISMATCH"):
        run(context=replace(denied, review_feedback_digest="b" * 64), **kwargs)
    monkeypatch.setattr(follow_up, "compute_m9_reproducibility_digest_v1", lambda: "b" * 64)
    assert run(context=denied, **kwargs)["action"] == "REVIEW_POLICY_CHANGED"
    assert not output.exists()


def test_insufficient_evidence_and_interrupted_output_stay_open(tmp_path):
    denied = _review(tmp_path, {"max_age_seconds": 999})
    ledger = tmp_path / "empty.jsonl"
    ledger.touch()
    output = tmp_path / "insufficient"
    blocked = _run_cli(tmp_path, denied, ledger, output)
    assert blocked.returncode == 2, blocked.stderr
    assert _stdout_payload(blocked)["research"]["status"] == "BLOCKED"
    assert _stdout_payload(blocked)["research"]["final_holdout_executed"] is False

    partial = tmp_path / "interrupted"
    partial.mkdir()
    candidate_domain = partial / "candidate_domain.json"
    candidate_domain.write_bytes(b"original partial artifact")
    interrupted = _run_cli(tmp_path, denied, ledger, partial)
    assert interrupted.returncode != 0
    assert "M9_REVIEW_RESEARCH_OUTPUT_INCOMPLETE" in interrupted.stderr
    assert candidate_domain.read_bytes() == b"original partial artifact"
