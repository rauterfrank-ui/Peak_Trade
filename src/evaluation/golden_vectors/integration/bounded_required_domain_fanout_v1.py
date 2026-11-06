"""Execute concrete existing domain runners for an explicit, non-authorizing plan.

WHOLE_SYSTEM tags never substitute for actual calls or requirement coverage.
"""

from __future__ import annotations
from dataclasses import asdict, dataclass, replace
import hashlib
import inspect
import json
from pathlib import Path

from src.evaluation.golden_vectors.contracts.models import (
    EvidenceBundleV1,
    DomainEvaluationContextV1,
    DomainEvaluationResultV1,
    DecisionDeltaManifestV1,
    ProvenanceRecordV1,
    contract_digest_hex,
)
from src.evaluation.golden_vectors.contracts.enums import ExternalPromotionStatus
from src.evaluation.golden_vectors.constraints.pre_constraint_gate_v1 import (
    ConstraintMatrixPreGateV1,
)
from src.evaluation.golden_vectors.constraints.post_constraint_gate_v1 import (
    ConstraintMatrixPostGateV1,
)
from src.evaluation.golden_vectors.corpus.gate_v1 import VectorCorpusIntegrityGateV1
from src.evaluation.golden_vectors.digest.comparator_v1 import ProtectedSemanticComparatorV1
from src.evaluation.golden_vectors.evaluators.ranking_universe_v1 import RankingUniverseEvaluatorV1
from src.evaluation.golden_vectors.evaluators.productive_trading_path_v1 import (
    ProductiveTradingPathEvaluatorV1,
)
from src.evaluation.golden_vectors.evaluators.self_learning_v1 import SelfLearningEvaluatorV1
from src.evaluation.golden_vectors.evaluators.optimization_universe_v1 import (
    OptimizationUniverseEvaluatorV1,
)
from src.evaluation.golden_vectors.evaluators.market_intelligence_v1 import (
    MarketIntelligenceEvaluatorV1,
)
from src.evaluation.golden_vectors.registry.evidence_registry_v1 import GvefEvidenceRegistryV1
from src.evaluation.golden_vectors.runner.generic_runner_v1 import (
    GenericRunnerV1,
    GvefRunRequestV1,
    GvefRunnerDependenciesV1,
)
from src.evaluation.golden_vectors.promotion.promotion_evidence_adapter_v1 import (
    evidence_bundle_semantic_digest,
    PassThroughPromotionEvidenceAdapterV1,
)
from .domain_result_binding_v1 import (
    EvaluationBindingError,
    EvaluationPlanV1,
    DomainRequirementV1,
    CONTRACTS,
    binding_digest_v1,
    exact_bytes_v1,
    require_result_coverage_v1,
    source_tree_digest_v1,
)
from .evaluation_receipt_v1 import (
    EvaluationReceiptArchiveV1,
    validate_numeric_packet_v1,
    assess_economic_quality_v1,
    evaluation_receipt_binding_v1,
)

EVALUATORS = {
    "ranking_universe": RankingUniverseEvaluatorV1,
    "productive_trading_path": ProductiveTradingPathEvaluatorV1,
    "self_learning": SelfLearningEvaluatorV1,
    "optimization_universe": OptimizationUniverseEvaluatorV1,
    "market_intelligence": MarketIntelligenceEvaluatorV1,
}


@dataclass(frozen=True)
class BoundContextReplayV1:
    def replay(self, *, run, context):
        if run != context.run_manifest:
            raise EvaluationBindingError("REPLAY_CONTEXT_RUN_MISMATCH")
        return type(context.replay_trace).model_validate(
            context.replay_trace.model_dump(mode="json", by_alias=True)
        )


@dataclass(frozen=True)
class BoundDeltaBuilderV1:
    def build(self, *, comparator_delta):
        return DecisionDeltaManifestV1.model_validate(
            comparator_delta.model_dump(mode="json", by_alias=True)
        )


@dataclass(frozen=True)
class BoundContextEvidenceBuilderV1:
    context: DomainEvaluationContextV1

    def build(
        self,
        *,
        run,
        delta,
        protected_digests,
        boundary_results,
        post_gate_pass,
        domain_evaluation_result=None,
    ):
        c = self.context
        if run != c.run_manifest or domain_evaluation_result is None:
            raise EvaluationBindingError("RESULT_BOUND_EVIDENCE_REQUIRED")
        bundle = EvidenceBundleV1(
            run_id=run.run_id,
            experiment_id=run.experiment_id,
            baseline_sha=run.baseline_sha,
            candidate_sha=run.candidate_sha,
            constraint_matrix_version=run.constraint_matrix_version,
            constraint_matrix_digest=run.constraint_matrix_digest,
            vector_corpus_version=c.corpus_identity.corpus_version,
            vector_corpus_digest=c.corpus_identity.corpus_digest,
            protected_semantic_digests=protected_digests,
            config_digest=c.config_identity.config_digest,
            config_provenance=ProvenanceRecordV1(
                source="EXPLICIT_BOUND_CONTEXT", ref=c.config_identity.config_path
            ),
            data_manifest=c.data_identity,
            data_provenance=ProvenanceRecordV1(
                source="EXPLICIT_BOUND_CONTEXT", ref=c.data_identity.data_manifest_id
            ),
            seed_set=c.seed_identity.seeds,
            metric_schema_version=c.corpus_identity.metric_schema_version,
            invariant_results=domain_evaluation_result.invariants,
            authority_boundary_results=[
                *boundary_results,
                *domain_evaluation_result.boundary_results,
            ],
            decision_delta_manifest=delta,
            evidence_digest="0" * 64,
            promotion_status=ExternalPromotionStatus.EXTERNAL_UNSET,
            post_constraint_gate_pass=post_gate_pass,
            fan_out_evaluation_class=run.fan_out_evaluation_class,
        )
        return bundle.model_copy(
            update={"evidence_digest": evidence_bundle_semantic_digest(bundle)}
        )


@dataclass(frozen=True)
class DomainExecutionInputV1:
    context: DomainEvaluationContextV1
    dependencies: GvefRunnerDependenciesV1
    numeric_evidence: tuple[dict, ...] = ()


def dependency_binding_v1(deps):
    result = {}
    for role in (
        "pre_gate",
        "post_gate",
        "replay_adapter",
        "evaluator",
        "comparator",
        "delta_builder",
        "evidence_builder",
        "registry",
        "corpus_gate",
        "promotion_adapter",
    ):
        component = getattr(deps, role)
        cls = type(component)
        try:
            path = Path(inspect.getfile(cls))
            source_sha = hashlib.sha256(path.read_bytes()).hexdigest()
        except (TypeError, OSError):
            source_sha = None
        result[role] = {
            "class": cls.__module__ + "." + cls.__qualname__,
            "source_sha256": source_sha,
        }
        if role == "comparator":
            result[role]["expected_changed_domains"] = (
                sorted(x.value for x in component.expected_changed_domains)
                if hasattr(component, "expected_changed_domains")
                else None
            )
        if role in {"pre_gate", "post_gate"}:
            result[role]["repo_root"] = (
                str(component.repo_root.resolve())
                if getattr(component, "repo_root", None)
                else None
            )
        if role == "evaluator":
            result[role]["evaluator_id"] = getattr(component, "evaluator_id", None)
            result[role]["schema_version"] = getattr(component, "schema_version", None)

    return result


def requirement_for_input_v1(domain, vector_id, entry):
    return DomainRequirementV1(
        domain,
        CONTRACTS[domain][0],
        vector_id,
        contract_digest_hex(entry.context),
        binding_digest_v1("dependencies.v1", dependency_binding_v1(entry.dependencies)),
        binding_digest_v1("numeric_refs.v1", list(entry.numeric_evidence)),
    )


def _validate_input(requirement, entry):
    c = entry.context
    d = entry.dependencies
    expected = {
        "evaluator": EVALUATORS[requirement.domain],
        "pre_gate": ConstraintMatrixPreGateV1,
        "post_gate": ConstraintMatrixPostGateV1,
        "corpus_gate": VectorCorpusIntegrityGateV1,
        "replay_adapter": BoundContextReplayV1,
        "comparator": ProtectedSemanticComparatorV1,
        "delta_builder": BoundDeltaBuilderV1,
        "evidence_builder": BoundContextEvidenceBuilderV1,
        "registry": GvefEvidenceRegistryV1,
        "promotion_adapter": PassThroughPromotionEvidenceAdapterV1,
    }
    if any(type(getattr(d, k)) is not v for k, v in expected.items()):
        raise EvaluationBindingError("REQUIRED_CONCRETE_DEPENDENCY_NOT_EXECUTED_BY_PROFILE")
    if c.run_manifest.domain_evaluator_id.value != d.evaluator.evaluator_id:
        raise EvaluationBindingError("DOMAIN_EVALUATOR_IDENTITY_MISMATCH")
    if (
        binding_digest_v1("numeric_refs.v1", list(entry.numeric_evidence))
        != requirement.numeric_evidence_digest
    ):
        raise EvaluationBindingError("NUMERIC_REFERENCE_PLAN_BINDING_MISMATCH")
    if requirement.domain == "self_learning" and not entry.numeric_evidence:
        raise EvaluationBindingError("ACTUAL_NUMERIC_RESEARCH_PACKET_REQUIRED")
    if (
        contract_digest_hex(c) != requirement.context_digest
        or binding_digest_v1("dependencies.v1", dependency_binding_v1(d))
        != requirement.dependency_digest
    ):
        raise EvaluationBindingError("DOMAIN_CONTEXT_OR_IMPLEMENTATION_DRIFT")
    if contract_digest_hex(d.evidence_builder.context) != requirement.context_digest:
        raise EvaluationBindingError("EVIDENCE_BUILDER_CONTEXT_MISMATCH")
    corpus = d.corpus_gate._registry.load_entry(c.run_manifest.corpus_manifest_ref)
    if len(corpus.vectors) != 1 or corpus.vectors[0].vector_id != requirement.vector_id:
        raise EvaluationBindingError("ONE_EXPLICIT_EXECUTED_VECTOR_REQUIRED")
    vector = corpus.vectors[0]
    if (
        vector.population_selector.selector_id != "E5_EXPLICIT_REPLAY_SNAPSHOT_V1"
        or vector.population_selector.binding_digest != contract_digest_hex(c.replay_trace)
        or set(CONTRACTS[requirement.domain][1]) != set(vector.invariant_ids)
        or vector.expected_dispositions != ["DECLARED_REPLAY_CONTRACTS_ONLY"]
    ):
        raise EvaluationBindingError("CORPUS_POPULATION_OR_REQUIREMENT_UNBOUND")
    if (
        c.seed_identity.seeds != c.corpus_identity.seed_set
        or c.run_manifest.seed_set_digest != c.seed_identity.seed_set_digest
    ):
        raise EvaluationBindingError("CORPUS_SEED_CONTEXT_MISMATCH")
    d.corpus_gate.evaluate_bound_corpus(run=c.run_manifest, context=c)
    return {
        "manifest": corpus.manifest.model_dump(mode="json", by_alias=True),
        "vectors": {v.vector_id: v.model_dump(mode="json", by_alias=True) for v in corpus.vectors},
    }


def require_numeric_context_binding_v1(domain, context, refs, archive):
    """Validity of two independent records is not proof of their actual join."""
    entries = context.replay_trace.entries
    if domain == "self_learning":
        if not refs or any(r["owner"] != "NativeResearchExecutionArchiveV1" for r in refs):
            raise EvaluationBindingError("SL_ORIGINAL_NUMERIC_OWNER_REQUIRED")
        expected = [
            json.loads(archive.numeric_bytes_v1(r["original_bytes_sha256"]))["gvef_reference"]
            for r in refs
        ]
        actual = [e.get("learning_artifact") for e in entries if e.get("kind") == "self_learning"]
        if (
            not actual
            or any(a not in expected for a in actual)
            or any(e not in actual for e in expected)
        ):
            raise EvaluationBindingError("SL_NUMERIC_PACKET_REPLAY_JOIN_MISMATCH")
    if domain == "market_intelligence":
        if not refs or any(r["owner"] != "MiOfflineDurableEvidenceStoreV1" for r in refs):
            raise EvaluationBindingError("MI_ORIGINAL_NUMERIC_OWNER_REQUIRED")
        actual = [
            e.get("mi_context_bundle", {}).get("measured_calibration_artifact")
            for e in entries
            if e.get("kind") == "market_intelligence"
        ]
        if not actual or any(a not in refs for a in actual) or any(r not in actual for r in refs):
            raise EvaluationBindingError("MI_NUMERIC_PACKET_REPLAY_JOIN_MISMATCH")


class _ObservedEvaluator:
    def __init__(self, original):
        self.original = original
        self.calls = []

    def _evaluate(self, kind, **kwargs):
        result = getattr(self.original, "evaluate_" + kind)(**kwargs)
        self.calls.append({"kind": kind, "result": result.model_dump(mode="json", by_alias=True)})
        return result

    def evaluate_baseline(self, **kwargs):
        return self._evaluate("baseline", **kwargs)

    def evaluate_candidate(self, **kwargs):
        return self._evaluate("candidate", **kwargs)

    def protected_digests_baseline(self, **kwargs):
        return self.original.protected_digests_baseline(**kwargs)

    def protected_digests_candidate(self, **kwargs):
        return self.original.protected_digests_candidate(**kwargs)

    def failure_fan_out(self, failure):
        return self.original.failure_fan_out(failure)


def _record_payload(record):
    value = {}
    for name, value0 in vars(record).items():
        if hasattr(value0, "model_dump"):
            value[name] = value0.model_dump(mode="json", by_alias=True)
        elif hasattr(value0, "value"):
            value[name] = value0.value
        elif name == "state_history":
            value[name] = [s.value for s in value0]
        else:
            value[name] = value0
    return value


def validate_domain_receipt_v1(archive, receipt_id, *, requirement, plan_id):
    body = archive.get_v1("domain", receipt_id)
    if (
        body["schema_version"] != "domain_result_binding.v1"
        or body["plan_id"] != plan_id
        or body["requirement"] != json.loads(exact_bytes_v1(asdict(requirement)))
    ):
        raise EvaluationBindingError("DOMAIN_RECEIPT_IDENTITY_MISMATCH")
    if body.get("evaluation_receipt") != evaluation_receipt_binding_v1(body):
        raise EvaluationBindingError("ADDITIVE_RESULT_OR_BUNDLE_BINDING_CHANGED")
    if body["status"] not in {"PASS", "BLOCKED"}:
        raise EvaluationBindingError("INVALID_DOMAIN_RECEIPT_STATUS")
    if body["status"] != "PASS":
        return body
    if (
        binding_digest_v1("numeric_refs.v1", body["numeric_evidence"])
        != requirement.numeric_evidence_digest
    ):
        raise EvaluationBindingError("NUMERIC_REFERENCE_PLAN_BINDING_MISMATCH")
    c = DomainEvaluationContextV1.model_validate(body["context"])
    r = body["record"]
    from src.evaluation.golden_vectors.corpus.registry_v1 import VectorCorpusRegistryV1
    from src.evaluation.golden_vectors.contracts.models import CorpusManifestV1, VectorManifestV1

    snapshot = body["corpus_snapshot"]
    manifest = CorpusManifestV1.model_validate(snapshot["manifest"])
    vectors = {k: VectorManifestV1.model_validate(v) for k, v in snapshot["vectors"].items()}
    VectorCorpusRegistryV1(corpus_root=archive.root).validate_in_memory(
        manifest=manifest, vectors=vectors
    )
    if (
        manifest != c.corpus_identity
        or len(vectors) != 1
        or requirement.vector_id not in vectors
        or vectors[requirement.vector_id].population_selector.binding_digest
        != contract_digest_hex(c.replay_trace)
    ):
        raise EvaluationBindingError("ARCHIVED_CORPUS_OR_REPLAY_BINDING_MISMATCH")
    if (
        contract_digest_hex(c) != requirement.context_digest
        or binding_digest_v1("dependencies.v1", body["dependency_binding"])
        != requirement.dependency_digest
    ):
        raise EvaluationBindingError("ARCHIVED_DOMAIN_CONTEXT_MISMATCH")
    if [x["kind"] for x in body["calls"]] != ["baseline", "candidate", "baseline", "candidate"]:
        raise EvaluationBindingError("ACTUAL_REPEAT_CALLS_MISSING")
    if (
        body["calls"][0]["result"] != body["calls"][2]["result"]
        or body["calls"][1]["result"] != body["calls"][3]["result"]
    ):
        raise EvaluationBindingError("FULL_BASELINE_OR_CANDIDATE_REPEAT_CHANGED")
    if (
        r["baseline_result"] != body["calls"][0]["result"]
        or r["candidate_result"] != body["calls"][1]["result"]
    ):
        raise EvaluationBindingError("FULL_RESULT_CALL_BINDING_MISMATCH")
    for name in ("baseline_result", "candidate_result"):
        require_result_coverage_v1(requirement, r[name])
    bundle = EvidenceBundleV1.model_validate(r["evidence_bundle"])
    if (
        evidence_bundle_semantic_digest(bundle) != bundle.evidence_digest
        or r["state"] != "REGISTERED"
        or r["failure_classification"] is not None
    ):
        raise EvaluationBindingError("LEGACY_BUNDLE_OR_REGISTRATION_INVALID")
    if (
        bundle.run_id != c.run_manifest.run_id
        or bundle.config_digest != c.config_identity.config_digest
        or bundle.vector_corpus_digest != c.corpus_identity.corpus_digest
        or bundle.invariant_results
        != DomainEvaluationResultV1.model_validate(r["candidate_result"]).invariants
    ):
        raise EvaluationBindingError("BUNDLE_RESULT_OR_CONTEXT_BINDING_MISMATCH")
    for ref in body["numeric_evidence"]:
        validate_numeric_packet_v1(archive, ref)
    require_numeric_context_binding_v1(requirement.domain, c, body["numeric_evidence"], archive)
    return body


def run_required_domain_fanout_v1(
    *,
    plan: EvaluationPlanV1,
    inputs: dict[str, DomainExecutionInputV1],
    archive: EvaluationReceiptArchiveV1,
    economic_request: dict,
):
    plan.validate_v1()
    snapshot = plan.to_dict_v1()
    plan_id = binding_digest_v1("plan.v1", snapshot)
    if set(inputs) - {r.domain for r in plan.required}:
        raise EvaluationBindingError("UNPLANNED_DOMAIN_INPUT")
    with archive.lease_v1():
        archive.publish_v1(Path("plans") / (plan_id + ".json"), snapshot)
        results = {}
        for requirement in plan.required:
            domain = requirement.domain
            index = archive.root / "plans" / plan_id / (domain + ".json")
            if index.exists():
                if index.is_symlink():
                    raise EvaluationBindingError("RECEIPT_SYMLINK_FORBIDDEN")
                key = json.loads(index.read_bytes())["receipt_id"]
                body = validate_domain_receipt_v1(
                    archive, key, requirement=requirement, plan_id=plan_id
                )
                results[domain] = {"status": body["status"], "receipt_id": key}
                continue
            if domain not in inputs:
                results[domain] = {"status": "MISSING_REQUIRED_DOMAIN", "receipt_id": None}
                continue
            entry = inputs[domain]
            observed = None
            corpus_snapshot = None
            record = None
            reason = None
            try:
                corpus_snapshot = _validate_input(requirement, entry)
                for ref in entry.numeric_evidence:
                    validate_numeric_packet_v1(archive, ref)
                require_numeric_context_binding_v1(
                    domain, entry.context, entry.numeric_evidence, archive
                )
                observed = _ObservedEvaluator(entry.dependencies.evaluator)
                record = GenericRunnerV1().execute(
                    GvefRunRequestV1(entry.context), replace(entry.dependencies, evaluator=observed)
                )
                if record.state.value != "REGISTERED":
                    raise EvaluationBindingError(
                        "DOMAIN_RUN_FAILED:" + str(record.failure_classification)
                    )
                for result in (record.baseline_result, record.candidate_result):
                    require_result_coverage_v1(
                        requirement, result.model_dump(mode="json", by_alias=True)
                    )
                stored = entry.dependencies.registry.get(record.run_manifest.run_id)
                if stored is None or stored != record.evidence_bundle:
                    raise EvaluationBindingError("ORIGINAL_REGISTRY_READBACK_MISMATCH")
                if _validate_input(requirement, entry) != corpus_snapshot:
                    raise EvaluationBindingError("CORPUS_CHANGED_DURING_DOMAIN_EVALUATION")
            except Exception as exc:
                reason = type(exc).__name__ + ":" + str(exc)
            body = {
                "schema_version": "domain_result_binding.v1",
                "plan_id": plan_id,
                "requirement": json.loads(exact_bytes_v1(asdict(requirement))),
                "status": "PASS" if reason is None else "BLOCKED",
                "reason": reason,
                "context": entry.context.model_dump(mode="json", by_alias=True),
                "dependency_binding": dependency_binding_v1(entry.dependencies),
                "record": _record_payload(record) if record else None,
                "calls": observed.calls if observed else [],
                "numeric_evidence": list(entry.numeric_evidence),
                "corpus_snapshot": corpus_snapshot,
            }
            body["evaluation_receipt"] = evaluation_receipt_binding_v1(body)
            key = archive.append_v1("domain", body)
            validate_domain_receipt_v1(archive, key, requirement=requirement, plan_id=plan_id)
            archive.publish_v1(Path("plans") / plan_id / (domain + ".json"), {"receipt_id": key})
            results[domain] = {"status": body["status"], "receipt_id": key}
            if plan.to_dict_v1() != snapshot or source_tree_digest_v1() != plan.source_tree_digest:
                raise EvaluationBindingError("PLAN_OR_SOURCE_CHANGED_DURING_EVALUATION")
        statuses = {v["status"] for v in results.values()}
        status = (
            "BLOCKED"
            if "BLOCKED" in statuses
            else "INCOMPLETE"
            if "MISSING_REQUIRED_DOMAIN" in statuses
            else "PASS"
        )
        system = {
            "schema_version": "system_evaluation_receipt.v1",
            "plan": snapshot,
            "plan_id": plan_id,
            "mechanism_status": status,
            "domains": results,
            "not_required": snapshot["not_required"],
            "claim_scope": plan.claim_scope,
            "economic_request": economic_request,
            "economic_quality": assess_economic_quality_v1(economic_request),
            "full_system_accepted": False,
            "productive_apply_authorized": False,
            "source_authenticated": False,
        }
        key = archive.append_v1("system", system)
        return key, read_system_evaluation_v1(archive, key, expected_plan=plan)


def read_system_evaluation_v1(archive, receipt_id, *, expected_plan):
    expected_plan.validate_v1()
    body = archive.get_v1("system", receipt_id)
    if (
        body["schema_version"] != "system_evaluation_receipt.v1"
        or body["plan"] != expected_plan.to_dict_v1()
        or body["plan_id"] != binding_digest_v1("plan.v1", body["plan"])
    ):
        raise EvaluationBindingError("SYSTEM_EVALUATION_PLAN_MISMATCH")
    if (
        body["claim_scope"] != expected_plan.claim_scope
        or body["not_required"] != body["plan"]["not_required"]
    ):
        raise EvaluationBindingError("SYSTEM_CLAIM_OR_IMPACT_SCOPE_CHANGED")
    if set(body["domains"]) != {r.domain for r in expected_plan.required}:
        raise EvaluationBindingError("SYSTEM_REQUIRED_DOMAIN_MISSING")
    for req in expected_plan.required:
        ref = body["domains"][req.domain]
        if ref["receipt_id"] is not None:
            domain = validate_domain_receipt_v1(
                archive, ref["receipt_id"], requirement=req, plan_id=body["plan_id"]
            )
            if domain["status"] != ref["status"]:
                raise EvaluationBindingError("SYSTEM_DOMAIN_STATUS_MISMATCH")
        elif ref["status"] != "MISSING_REQUIRED_DOMAIN":
            raise EvaluationBindingError("MISSING_REQUIRED_DOMAIN_FALSE_PASS")
    statuses = {v["status"] for v in body["domains"].values()}
    expected = (
        "BLOCKED"
        if "BLOCKED" in statuses
        else "INCOMPLETE"
        if "MISSING_REQUIRED_DOMAIN" in statuses
        else "PASS"
    )
    if body["mechanism_status"] != expected or body[
        "economic_quality"
    ] != assess_economic_quality_v1(body["economic_request"]):
        raise EvaluationBindingError("FALSE_SYSTEM_OR_ECONOMIC_PASS")
    if (
        body["full_system_accepted"] is not False
        or body["productive_apply_authorized"] is not False
        or body["source_authenticated"] is not False
    ):
        raise EvaluationBindingError("EVALUATION_AUTHORITY_OR_AUTHENTICATION_CLAIM_FORBIDDEN")
    return body
