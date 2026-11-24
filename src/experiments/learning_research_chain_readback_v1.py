"""Read existing DDO/OPT/Meta/GVEF handoffs without creating scientific truth.

All record, numerical, corpus and domain validation stays with its original
owner. This reader binds their retained identities across a completed campaign
job. It neither re-executes historical research nor authenticates venue sources.
"""

from pathlib import Path

from src.evaluation.golden_vectors.integration.bounded_required_domain_fanout_v1 import (
    validate_domain_receipt_v1,
)
from src.evaluation.golden_vectors.integration.domain_result_binding_v1 import (
    DomainRequirementV1,
    binding_digest_v1,
)
from src.evaluation.golden_vectors.integration.evaluation_receipt_v1 import (
    EvaluationReceiptArchiveV1,
    assess_economic_quality_v1,
)
from src.experiments.canonical_native_research_session_v1 import NativeResearchExecutionArchiveV1
from src.experiments.canonical_advanced_search_v1 import canonical_record_payload_v1
from src.experiments.canonical_meta_learning_v1 import MetaLearningPolicyV1
from src.experiments.canonical_optimization_universe_learning_input_v1 import (
    CanonicalOptimizationUniverseLearningInputRequestV1,
    validate_canonical_optimization_universe_learning_input_v1,
)
from src.experiments.canonical_research_prepared_execution_v1 import digest_v1, read_v1
from src.experiments.canonical_research_result_to_meta_input_v1 import (
    build_meta_learning_from_research_results_v1,
)
from src.learning.deterministic_decision_outcome_v0.learning_evidence_record_v1 import (
    validate_learning_evidence_record_v1,
)
from src.learning.deterministic_decision_outcome_v0.meta_learning_evidence_v1 import (
    UNIVERSE_CLASS_SELF_LEARNING,
)


def _require(condition, edge):
    if not condition:
        raise ValueError("LEARNING_RESEARCH_CHAIN_MISMATCH:" + edge)


def read_learning_research_chain_v1(root: Path, learning_digest: str, completed=None) -> dict:
    """Bind retained receipts; a mechanical PASS never becomes economic acceptance."""
    workspace = EvaluationReceiptArchiveV1(root)
    # safe_path rejects non-relative components; the evidence owner checks the
    # complete learning digest below, including its original canonical schema.
    if completed is None:
        completed = read_v1(workspace.safe_path_v1(Path("completed") / (learning_digest + ".json")))
    job = read_v1(workspace.safe_path_v1(Path("jobs") / (learning_digest + ".json")))
    run = workspace.safe_path_v1(Path("offline-ddo-research") / learning_digest)
    bound, result = (read_v1(run / name) for name in ("request.json", "result.json"))
    evidence = validate_learning_evidence_record_v1(bound["learning_evidence"])
    request = bound["request"]
    _require(
        evidence["content_hash"]
        == request["learning_evidence_digest"]
        == result["learning_evidence_digest"]
        == completed["learning_digest"]
        == learning_digest,
        "DDO_TO_RESEARCH_IDENTITY",
    )
    admission = validate_canonical_optimization_universe_learning_input_v1(
        CanonicalOptimizationUniverseLearningInputRequestV1(learning_evidence=evidence)
    )
    _require(dict(admission) == bound["optimization_admission"], "SL_TO_OPT_ADMISSION")
    _require(
        result["request_digest"] == digest_v1(bound)
        and result["optimization_admission_digest"] == admission["result_digest"]
        and completed["result_digest"] == digest_v1(result),
        "REQUEST_AND_RESULT",
    )
    _require(
        completed["source"] == job["source"]
        and completed["input_digest"] == job["input_digest"]
        and completed["status"] == result["status"]
        and bound["identity"]["fields"]["git_sha"] == job["code_sha"]
        and bound["authority"] == result["authority"] == completed["authority"] == "NONE",
        "CAMPAIGN_SOURCE_AND_AUTHORITY",
    )
    _require(
        completed["instrument_id"]
        == request["instrument_id"]
        == evidence["outcome_evidence_provenance"]["instrument_id"]
        and completed["strategy_id"] == request["strategy_id"]
        and completed["strategy_version"] == request["strategy_version"],
        "INSTRUMENT_AND_STRATEGY",
    )
    follow_up = result.get("follow_up") or {}
    first_measured = result["first_artifact_id"] is not None
    pair_measured = result["next_artifact_id"] is not None
    evaluation = result.get("evaluation")
    _require(
        (result.get("campaign_meta_feedback") is not None) == bool(job["meta_digests"])
        and (result.get("meta_feedback") is not None) == first_measured
        and (result["next_search"] is not None) == first_measured
        and (first_measured or not pair_measured)
        and (evaluation is not None) == pair_measured
        and bool(follow_up) == (pair_measured and "follow_up_times" in bound),
        "REQUIRED_HANDOFF_MISSING",
    )
    if evaluation is None:
        _require(
            result["status"]
            == ("NEXT_SEARCH_EXHAUSTED" if first_measured else "FIRST_SEARCH_EXHAUSTED"),
            "SEARCH_EXHAUSTION_STATUS",
        )
    else:
        _require(
            result["status"]
            == (
                "MECHANISM_PASS"
                if evaluation["mechanism_status"] == "PASS"
                else "MECHANISM_BLOCKED"
            ),
            "GVEF_TO_CAMPAIGN_STATUS",
        )
    expected = [
        value
        for value in (
            result["first_artifact_id"],
            result["next_artifact_id"],
            follow_up.get("artifact_id"),
        )
        if value is not None
    ]
    _require(completed["artifacts"] == expected, "MEASURED_ARTIFACT_ORDER")
    archive = NativeResearchExecutionArchiveV1(run / "native-archive")
    measurements = []
    units = {}
    searches = [
        value
        for value in (
            result["first_search"] if result["first_artifact_id"] else None,
            result["next_search"] if result["next_artifact_id"] else None,
            follow_up.get("search") if follow_up.get("artifact_id") else None,
        )
        if value is not None
    ]
    _require(len(searches) == len(expected), "SEARCH_MEASUREMENT_COUNT")
    for key in expected:
        executed, measured = archive._read_packet(key)
        loop = executed.next_meta_input.research_loop_record
        _require(
            canonical_record_payload_v1(executed.next_meta_input.search_record)
            == searches[len(measurements)],
            "SEARCH_TO_ACTUAL_MEASUREMENT",
        )
        _require(
            measured["instrument_id"] == request["instrument_id"]
            and measured["strategy_id"] == request["strategy_id"]
            and measured["strategy_version"] == request["strategy_version"]
            and measured["source_hashes"]["dataset_sha256"] == request["dataset_sha256"]
            and loop["experiment_record"]["experiment_identity"]["parent_lineage"][
                "parent_lineage_ref"
            ]
            == "ddo-learning-evidence:sha256:" + learning_digest,
            "OPT_MEASUREMENT_TO_ORIGINAL_DDO",
        )
        measurements.append(
            {
                "artifact_id": key,
                "experiment_id": measured["experiment_id"],
                "research_loop_status": loop["overall_status"],
                "parameters": dict(measured["parameters"]),
            }
        )
        units[measured["experiment_id"]] = executed.next_meta_input
    for prior in job["history"]:
        if prior["learning_digest"] not in job["meta_digests"]:
            continue
        prior_run = workspace.safe_path_v1(Path("offline-ddo-research") / prior["learning_digest"])
        _require(
            digest_v1(read_v1(prior_run / "result.json")) == prior["result_digest"], "META_HISTORY"
        )
        prior_archive = NativeResearchExecutionArchiveV1(prior_run / "native-archive")
        for key in prior["artifacts"]:
            unit = prior_archive.get(key).next_meta_input
            if job.get("gap_returns"):
                from src.experiments.campaign_reality_gap_return_v1 import with_returns_v1

                unit = with_returns_v1(unit, root, job["gap_returns"])
            units[unit.research_loop_record["selected_experiment_id"]] = unit
    feedbacks = (
        (result.get("campaign_meta_feedback"), result["first_search"]),
        (result.get("meta_feedback"), result.get("next_search")),
        (follow_up.get("meta_feedback"), follow_up.get("search")),
    )
    meta_bindings = []
    for feedback, search in feedbacks:
        if feedback is None:
            continue
        binding = feedback["meta_input_binding"]
        meta = binding["meta_learning_record"]
        source_units = [units[row["experiment_id"]] for row in binding["source_bindings"]]
        actual = build_meta_learning_from_research_results_v1(
            source_units,
            created_at=meta["created_at"],
            policy=MetaLearningPolicyV1(**meta["evaluation_policy"]),
        )
        _require(canonical_record_payload_v1(actual) == binding, "MEASURED_RESULTS_TO_META")
        _require(feedback["next_search_record"] == search, "META_TO_ACTUAL_SEARCH")
        _require(
            search["input_lineage"]["meta_learning_identity"]
            == (meta["meta_learning_identity"] if meta["research_proposals"] else None),
            "META_IDENTITY_CONSUMED_BY_SEARCH",
        )
        meta_bindings.append(
            {
                "meta_learning_identity": meta["meta_learning_identity"],
                "experiment_ids": [row["experiment_id"] for row in binding["source_bindings"]],
                "research_proposal_ids": [row["proposal_id"] for row in meta["research_proposals"]],
            }
        )
    if evaluation is not None:
        _require(len(expected) >= 2, "GVEF_REQUIRES_TWO_ORIGINAL_MEASUREMENTS")
        receipts = EvaluationReceiptArchiveV1(run / "gvef/evidence")
        system = receipts.get_v1("system", evaluation["receipt_id"])
        _require(
            system["plan_id"] == binding_digest_v1("plan.v1", system["plan"])
            and system["plan"]["source_tree_digest"] == bound["source_tree_digest"]
            and system["mechanism_status"] == evaluation["mechanism_status"]
            and system["economic_quality"] == assess_economic_quality_v1(system["economic_request"])
            and system["economic_quality"]["status"] == evaluation["economic_status"]
            and system["productive_apply_authorized"] is False
            and system["full_system_accepted"] is False,
            "GVEF_PLAN_AND_CLAIM_SCOPE",
        )
        requirements = [DomainRequirementV1(**row) for row in system["plan"]["required"]]
        _require(
            set(system["domains"]) == {row.domain for row in requirements}, "GVEF_REQUIRED_DOMAINS"
        )
        for row in requirements:
            row.validate_v1()
            ref = system["domains"][row.domain]
            if ref["receipt_id"] is not None:
                checked = validate_domain_receipt_v1(
                    receipts, ref["receipt_id"], requirement=row, plan_id=system["plan_id"]
                )
                _require(checked["status"] == ref["status"], "GVEF_DOMAIN_STATUS")
            else:
                _require(ref["status"] == "MISSING_REQUIRED_DOMAIN", "GVEF_MISSING_DOMAIN")
        statuses = {row["status"] for row in system["domains"].values()}
        _require(
            system["mechanism_status"]
            == (
                "BLOCKED"
                if "BLOCKED" in statuses
                else "INCOMPLETE"
                if "MISSING_REQUIRED_DOMAIN" in statuses
                else "PASS"
            ),
            "GVEF_SYSTEM_VERDICT",
        )
        (requirement,) = (
            DomainRequirementV1(**row)
            for row in system["plan"]["required"]
            if row["domain"] == "self_learning"
        )
        reference = system["domains"]["self_learning"]
        _require(reference["receipt_id"] == evaluation["domain_receipt_id"], "GVEF_DOMAIN")
        domain = validate_domain_receipt_v1(
            receipts, reference["receipt_id"], requirement=requirement, plan_id=system["plan_id"]
        )
        _require(
            [row["original_artifact_id"] for row in domain["numeric_evidence"]] == expected[:2],
            "GVEF_NUMERIC_PAIR",
        )
        if follow_up:
            decision = follow_up["decision"]
            saved = read_v1(run / "follow-up-decisions" / (evaluation["receipt_id"] + ".json"))
            _require(
                decision == saved
                and decision["evaluation"] == evaluation
                and decision["authority"] == "NONE"
                and decision["request_digest"] == result["request_digest"]
                and list(decision["prior_artifact_ids"]) == expected[:2]
                and decision["action"]
                == ("SEARCH_ONCE" if evaluation["mechanism_status"] == "PASS" else "HOLD"),
                "GVEF_RECEIPT_TO_FOLLOW_UP",
            )
            if decision["action"] == "SEARCH_ONCE":
                _require(
                    follow_up.get("meta_feedback") is not None
                    and follow_up.get("search") is not None
                    and follow_up["status"]
                    == ("MEASURED" if follow_up.get("artifact_id") else "SEARCH_EXHAUSTED"),
                    "FOLLOW_UP_TO_MEASUREMENT",
                )
            else:
                _require(
                    follow_up["status"] == "HELD_BY_EVALUATION"
                    and not any(
                        follow_up.get(key) is not None
                        for key in ("artifact_id", "meta_feedback", "search")
                    ),
                    "HELD_FOLLOW_UP",
                )
    provenance = evidence["outcome_evidence_provenance"]
    return {
        "schema_version": "learning_research_causal_chain_readback.v1",
        "authority": "NONE",
        "learning_digest": learning_digest,
        "source": completed["source"],
        "decision_event_ref": evidence["decision_event_ref"],
        "outcome_semantic_class": provenance["outcome_semantic_class"],
        "outcome_scalar_kind": evidence["outcome_scalar_kind"],
        "evaluation_horizon": evidence["evaluation_horizon"],
        "meta_learning_universe": UNIVERSE_CLASS_SELF_LEARNING,
        "measurements": measurements,
        "meta_bindings": meta_bindings,
        "evaluation": evaluation,
        "follow_up_status": follow_up.get("status"),
        "status": result["status"],
        "source_authentication_performed": False,
        "economic_acceptance_inferred": False,
        "productive_apply_authorized": False,
    }
