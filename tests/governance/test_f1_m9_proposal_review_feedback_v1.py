import json
import subprocess
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict
from pathlib import Path

import pytest

from src.governance.f1_m9_proposal_review_feedback_v1 import (
    evaluate_and_store_f1_m9_proposal_review_feedback_v1,
    read_f1_m9_proposal_review_feedback_v1,
)
from src.governance.optimization_proposal_governance_ingress_v1 import (
    ADMISSION_ADMITTED,
    ADMISSION_DENIED,
    OptimizationProposalGovernanceAdmissionRequestV1,
    evaluate_optimization_proposal_governance_admission_v1,
)
from src.meta.learning_loop.contract_safety_v1 import (
    compute_content_sha256,
    deterministic_json_dumps,
)
from tests.governance.test_optimization_proposal_governance_ingress_v1 import _ingress_for_m9

REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize(
    ("max_age_seconds", "status", "reason"),
    [
        (300, ADMISSION_ADMITTED, "ADMITTED_FOR_GOVERNANCE_REVIEW_ONLY"),
        (999, ADMISSION_DENIED, "CANDIDATE_TARGET_OUT_OF_BOUNDS"),
    ],
)
def test_review_readback_preserves_original_decision(tmp_path, max_age_seconds, status, reason):
    ingress = _ingress_for_m9(tmp_path, parameter_config_delta={"max_age_seconds": max_age_seconds})
    root = tmp_path / "review"
    owner_result = evaluate_optimization_proposal_governance_admission_v1(
        OptimizationProposalGovernanceAdmissionRequestV1(ingress=ingress)
    )
    with ThreadPoolExecutor(max_workers=2) as workers:
        pending = [
            workers.submit(
                evaluate_and_store_f1_m9_proposal_review_feedback_v1,
                store_root=root,
                ingress=ingress,
            )
            for _ in range(2)
        ]
        first, second = (result.result() for result in pending)
    assert first == second
    assert first.admission_status == owner_result.admission_status == status
    assert first.reason_codes == owner_result.reason_codes == (reason,)
    assert first.ingress_digest == owner_result.ingress_digest
    assert first.proposal_identity_digest == ingress["optimization_provenance"]["identity_digest"]
    assert first.experiment_id == ingress["experiment_id"]
    assert first.candidate_ref == ingress["candidate_ref"]

    # Cold reader receives the original proposal through the normal readback API.
    source = """
import json
import sys
from dataclasses import asdict
from pathlib import Path
from src.governance.f1_m9_proposal_review_feedback_v1 import read_f1_m9_proposal_review_feedback_v1
receipt = read_f1_m9_proposal_review_feedback_v1(
    store_root=Path(sys.argv[1]), ingress=json.load(sys.stdin), review_policy_digest=sys.argv[2],
    expected_feedback_digest=sys.argv[3]
)
print(json.dumps(asdict(receipt), sort_keys=True))
"""
    completed = subprocess.run(
        [
            "./scripts/pt",
            "-c",
            source,
            str(root),
            first.review_policy_digest,
            first.feedback_digest,
        ],
        cwd=REPO_ROOT,
        input=deterministic_json_dumps(dict(ingress)),
        capture_output=True,
        check=True,
        text=True,
    )
    assert json.loads(completed.stdout.splitlines()[-1]) == json.loads(json.dumps(asdict(first)))
    [path] = root.glob("*/*.json")
    payload = json.loads(path.read_bytes())
    assert payload["authority"] == "NONE"
    assert (
        payload["optimization_evidence_content_hash"]
        == ingress["optimization_evidence_content_hash"]
    )
    assert list(path.parent.iterdir()) == [path]


def test_mismatched_proposal_and_modified_readback_fail_closed(tmp_path):
    ingress = _ingress_for_m9(tmp_path)
    root = tmp_path / "review"
    altered_ingress = dict(ingress, candidate_ref="different-candidate")
    with pytest.raises(ValueError, match="M9_REVIEW_INGRESS_DIGEST_MISMATCH"):
        evaluate_and_store_f1_m9_proposal_review_feedback_v1(
            store_root=root, ingress=altered_ingress
        )
    assert not root.exists()

    receipt = evaluate_and_store_f1_m9_proposal_review_feedback_v1(store_root=root, ingress=ingress)
    [path] = root.glob("*/*.json")
    payload = json.loads(path.read_bytes())
    payload["reason_codes"] = ["MODIFIED"]
    payload.pop("feedback_digest")
    payload["feedback_digest"] = compute_content_sha256(payload)
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="M9_REVIEW_FEEDBACK_DIGEST_MISMATCH"):
        read_f1_m9_proposal_review_feedback_v1(
            store_root=root,
            ingress=ingress,
            review_policy_digest=receipt.review_policy_digest,
            expected_feedback_digest=receipt.feedback_digest,
        )
    with pytest.raises(ValueError, match="M9_REVIEW_FEEDBACK_DIGEST_MISMATCH"):
        evaluate_and_store_f1_m9_proposal_review_feedback_v1(store_root=root, ingress=ingress)
    assert json.loads(path.read_bytes()) == payload
