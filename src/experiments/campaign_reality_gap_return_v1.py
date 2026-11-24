"""Append verified late I17 observations to campaign research memory."""

from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

from src.experiments.canonical_advanced_search_v1 import canonical_record_payload_v1 as plain
from src.experiments.canonical_failure_memory_store_v1 import CanonicalFailureMemoryStoreV1
from src.experiments.canonical_failure_memory_v1 import (
    CanonicalFailureMemoryRecordRequestV1,
    FAILURE_CLASS_TO_FAILED_GATE,
    build_canonical_failure_memory_record_v1,
)
from src.experiments.canonical_native_research_session_v1 import NativeResearchExecutionArchiveV1
from src.experiments.canonical_reality_gap_store_persist_v1 import CanonicalRealityGapStoreV1
from src.experiments import canonical_reality_gap_store_v1 as sl
from src.experiments.canonical_research_prepared_execution_v1 import digest_v1, publish_v1, read_v1
from src.evaluation.golden_vectors.integration.evaluation_receipt_v1 import (
    EvaluationReceiptArchiveV1,
)


def publish_gap_return_v1(state, plan, dimensions):
    workspace = EvaluationReceiptArchiveV1(state)
    digest = plan["learning_digest"]
    completed = read_v1(workspace.safe_path_v1(Path("completed") / (digest + ".json")))
    if completed["learning_digest"] != digest or dimensions["observed_plan_digest"] != digest_v1(
        plan
    ):
        raise ValueError("GAP_RETURN_PLAN_MISMATCH")
    archive = NativeResearchExecutionArchiveV1(
        workspace.safe_path_v1(Path("offline-ddo-research") / digest / "native-archive")
    )
    key = digest_v1(dimensions)
    base = workspace.safe_path_v1(Path("late-observations") / key)
    with workspace.lease_v1():
        publish_v1(base / "dimensions.json", dimensions)
        clock = base / "received.json"
        if not clock.exists():
            publish_v1(clock, {"at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")})
        stamp = read_v1(clock)["at"]
        if datetime.fromisoformat(stamp.replace("Z", "+00:00")) < datetime.fromisoformat(
            dimensions["source_data_known_at_utc"]
        ):
            raise ValueError("GAP_RETURN_FUTURE_OBSERVATION")
        rows = []
        for role, profile in plan["profiles"].items():
            obs = dimensions["profiles"][role]
            packet = obs["packet"]
            if packet != profile["packet"] or packet not in completed["artifacts"]:
                raise ValueError("GAP_RETURN_PACKET_MISMATCH")
            execution, measurement = archive._read_packet(packet)
            loop = execution.next_meta_input.research_loop_record
            memory = loop["experiment_record"]
            if (
                memory["completeness"] != "COMPLETE"
                or memory["experiment_id"] != profile["experiment_id"]
                or measurement["parameters"] != profile["parameters"]
            ):
                raise ValueError("GAP_RETURN_EXPERIMENT_MISMATCH")
            refs = [
                dict(
                    kind="EXPERIMENT_RECORD",
                    ref=memory["experiment_id"],
                    digest=memory["integrity"]["content_sha256"],
                ),
                dict(
                    kind=sl.ARTIFACT_KIND_STORE_RELATIVE_REF,
                    ref=f"late-observations/{key}/dimensions.json",
                    digest=key,
                ),
            ]
            gap = sl.build_canonical_reality_gap_record_v1(
                sl.CanonicalRealityGapRecordRequestV1(
                    experiment_identity=memory["experiment_identity"],
                    experiment_id=memory["experiment_id"],
                    observed_surface=dimensions["observed_surface"],
                    metric_definitions=dimensions["metric_definitions"],
                    threshold_policy_digest=dimensions["threshold_policy_digest"],
                    gap_dimensions=[sl.RealityGapDimensionV1(**v) for v in obs["gap_dimensions"]],
                    evidence_refs=refs,
                    created_at=stamp,
                )
            )
            gap = CanonicalRealityGapStoreV1(base / "gaps").append(gap)
            failure_id = None
            if gap["overall_disposition"] == sl.DISPOSITION_REJECTED_REALITY_GAP:
                failure = build_canonical_failure_memory_record_v1(
                    CanonicalFailureMemoryRecordRequestV1(
                        experiment_identity=memory["experiment_identity"],
                        experiment_id=memory["experiment_id"],
                        hypothesis_id=memory["hypothesis_id"],
                        failure_class=gap["overall_disposition"],
                        failed_gate=FAILURE_CLASS_TO_FAILED_GATE[gap["overall_disposition"]],
                        rejection_reason=gap["overall_disposition"],
                        regime=loop["robustness_evidence"]["regime"],
                        parameter_region=loop["robustness_evidence"]["parameter_region"],
                        cost_sensitivity={},
                        instability_indicators={},
                        evidence_refs=refs,
                        created_at=stamp,
                        robustness_policy_digest=loop["robustness_evidence"][
                            "robustness_policy_digest"
                        ],
                    )
                )
                failure_id = CanonicalFailureMemoryStoreV1(base / "failures").append(failure)[
                    "failure_record_id"
                ]
            rows.append(
                dict(
                    experiment_id=memory["experiment_id"],
                    gap=gap["reality_gap_record_id"],
                    failure=failure_id,
                )
            )
        publish_v1(base / "ready.json", dict(learning_digest=digest, received=stamp, records=rows))
    return key


def known_returns_v1(root, history, now):
    found = []
    for path in sorted((root / "late-observations").glob("*/ready.json")):
        receipt = read_v1(path)
        if (
            receipt["learning_digest"] in history
            and datetime.fromisoformat(receipt["received"].replace("Z", "+00:00")) <= now
        ):
            found.append(path.parent.name)
    return found


def with_returns_v1(unit, root, keys):
    gaps, failures = [], []
    for key in keys:
        if len(key) != 64 or any(c not in "0123456789abcdef" for c in key):
            raise ValueError("INVALID_RETURN_DIGEST")
        base = root / "late-observations" / key
        dimensions = read_v1(base / "dimensions.json")
        if digest_v1(dimensions) != key:
            raise ValueError("GAP_RETURN_SOURCE_CHANGED")
        for row in read_v1(base / "ready.json")["records"]:
            if row["experiment_id"] != unit.research_loop_record["selected_experiment_id"]:
                continue
            gap = plain(CanonicalRealityGapStoreV1(base / "gaps").get(row["gap"]))
            if gap["experiment_id"] != row["experiment_id"] or not any(
                ref["digest"] == key for ref in gap["evidence_refs"]
            ):
                raise ValueError("GAP_RETURN_WRONG_MEMORY")
            gaps.append(gap)
            if bool(row["failure"]) != (
                gap["overall_disposition"] == sl.DISPOSITION_REJECTED_REALITY_GAP
            ):
                raise ValueError("GAP_RETURN_FAILURE_MISMATCH")
            if row["failure"]:
                failure = plain(
                    CanonicalFailureMemoryStoreV1(base / "failures").get(row["failure"])
                )
                if failure["experiment_id"] != row["experiment_id"] or not any(
                    ref["digest"] == key for ref in failure["evidence_refs"]
                ):
                    raise ValueError("GAP_RETURN_WRONG_FAILURE")
                failures.append(failure)
    return replace(unit, late_gaps=tuple(gaps), late_failures=tuple(failures))


def route_cost_hypotheses_v1(workspace, completed, result, grids):
    """Keep the Meta cost investigation distinct from the strategy parameter search."""
    from src.experiments.f2_meta_cost_model_follow_up_v1 import (
        build_f2_meta_cost_model_follow_up_v1,
    )

    for feedback in (
        result.get("campaign_meta_feedback"),
        result.get("meta_feedback"),
        (result.get("follow_up") or {}).get("meta_feedback"),
    ):
        if not feedback:
            continue
        meta = feedback["meta_input_binding"]["meta_learning_record"]
        for proposal in meta["research_proposals"]:
            if proposal["target_kind"] != "cost_model" or proposal["kind"] != "INVESTIGATE":
                continue
            request = dict(
                learning_digest=completed["learning_digest"],
                instrument_id=completed["instrument_id"],
                meta_learning_identity=meta["meta_learning_identity"],
                proposal=proposal,
                authority="NONE",
            )
            folder = workspace.safe_path_v1(Path("cost-hypotheses") / digest_v1(request))
            publish_v1(folder / "request.json", request)
            grid = grids.get(proposal["target"])
            if grid is None:
                continue
            assessment = build_f2_meta_cost_model_follow_up_v1(
                meta_record=meta,
                expected_meta_identity=meta["meta_learning_identity"],
                proposal_id=proposal["proposal_id"],
                f2_result_path=grid.archive,
                expected_f2_execution_digest=grid.execution_digest,
            )
            if assessment["instrument_id"] != completed["instrument_id"]:
                raise ValueError("F2_COST_RETURN_INSTRUMENT_MISMATCH")
            publish_v1(folder / "assessment.json", assessment)
