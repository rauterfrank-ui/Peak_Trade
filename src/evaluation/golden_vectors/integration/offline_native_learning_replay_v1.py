"""Evaluate two retained native research artifacts with the scoped GVEF SL evaluator."""

from __future__ import annotations

import json
from pathlib import Path
from uuid import UUID

from src.evaluation.golden_vectors.constraints.matrix_loader_v1 import (
    load_canonical_constraint_matrix_v1,
)
from src.evaluation.golden_vectors.constraints.post_constraint_gate_v1 import (
    ConstraintMatrixPostGateV1,
)
from src.evaluation.golden_vectors.constraints.pre_constraint_gate_v1 import (
    ConstraintMatrixPreGateV1,
)
from src.evaluation.golden_vectors.contracts.models import (
    CorpusManifestV1,
    DomainEvaluationContextV1,
    RunManifestV1,
    VectorManifestV1,
    contract_digest_hex,
)
from src.evaluation.golden_vectors.contracts.primitives import ReplayTraceV1
from src.evaluation.golden_vectors.contracts.serialization import sha256_hex
from src.evaluation.golden_vectors.corpus.digest_v1 import (
    corpus_identity_digest_hex,
    vector_identity_digest_hex,
)
from src.evaluation.golden_vectors.corpus.gate_v1 import VectorCorpusIntegrityGateV1
from src.evaluation.golden_vectors.corpus.registry_v1 import VectorCorpusRegistryV1
from src.evaluation.golden_vectors.digest.comparator_v1 import ProtectedSemanticComparatorV1
from src.evaluation.golden_vectors.integration.bounded_required_domain_fanout_v1 import (
    EVALUATORS,
    BoundContextEvidenceBuilderV1,
    BoundContextReplayV1,
    BoundDeltaBuilderV1,
    DomainExecutionInputV1,
    read_system_evaluation_v1,
    requirement_for_input_v1,
    run_required_domain_fanout_v1,
)
from src.evaluation.golden_vectors.integration.domain_result_binding_v1 import (
    CONTRACTS,
    DomainExclusionV1,
    EvaluationPlanV1,
)
from src.evaluation.golden_vectors.integration.evaluation_receipt_v1 import (
    EvaluationReceiptArchiveV1,
    retain_native_research_packet_v1,
)
from src.evaluation.golden_vectors.promotion.promotion_evidence_adapter_v1 import (
    PassThroughPromotionEvidenceAdapterV1,
)
from src.evaluation.golden_vectors.registry.evidence_registry_v1 import GvefEvidenceRegistryV1
from src.evaluation.golden_vectors.runner.generic_runner_v1 import GvefRunnerDependenciesV1
from src.experiments.canonical_research_prepared_execution_v1 import digest_v1

_DOMAIN = "self_learning"
_EDGE = "NativeResearch->SelfLearningEvaluation"
_VECTOR = "offline-ddo-native-learning-replay-v1"


def _corpus(workspace, trace, seed, evidence_class, binding_digest):
    folder = Path("corpus") / _DOMAIN
    corpus_dir = workspace.safe_path_v1(folder)
    provenance = {"source": evidence_class, "ref": binding_digest}
    vector = VectorManifestV1(
        vector_id=_VECTOR,
        vector_class="GoldenHappy",
        schema_version="1.0.0",
        population_selector={
            "selector_id": "E5_EXPLICIT_REPLAY_SNAPSHOT_V1",
            "binding_digest": contract_digest_hex(trace),
        },
        invariant_ids=list(CONTRACTS[_DOMAIN][1]),
        expected_dispositions=["DECLARED_REPLAY_CONTRACTS_ONLY"],
        provenance=provenance,
    )
    manifest = CorpusManifestV1(
        corpus_version="1.0.0",
        corpus_digest="0" * 64,
        vector_ids=[_VECTOR],
        metric_schema_version="1.0.0",
        seed_set=[seed],
        provenance={"source": evidence_class, "ref": str(corpus_dir)},
    )
    manifest = manifest.model_copy(
        update={
            "corpus_digest": corpus_identity_digest_hex(
                manifest, vector_digests_by_id={_VECTOR: vector_identity_digest_hex(vector)}
            )
        }
    )
    workspace.publish_v1(
        folder / "vectors" / (_VECTOR + ".json"), vector.model_dump(mode="json", by_alias=True)
    )
    workspace.publish_v1(
        folder / "corpus_manifest.json", manifest.model_dump(mode="json", by_alias=True)
    )
    return corpus_dir, manifest


def evaluate_offline_native_learning_replay_v1(
    directory, *, archive, first_id, next_id, bound, seed, created_at, protected
):
    """Use the first result as the replay reference and the next as the candidate.

    The replay proves the numeric-packet join and local evaluator invariants.
    Economic qualification and productive authority require independent owners.
    """
    workspace = EvaluationReceiptArchiveV1(directory)
    evidence = EvaluationReceiptArchiveV1(workspace.safe_path_v1("evidence"))
    refs = tuple(
        retain_native_research_packet_v1(evidence, owner_root=archive.root, artifact_id=artifact_id)
        for artifact_id in (first_id, next_id)
    )
    entries = [
        {
            "kind": _DOMAIN,
            "label": label,
            "learning_artifact": json.loads(
                evidence.numeric_bytes_v1(ref["original_bytes_sha256"])
            )["gvef_reference"],
        }
        for label, ref in zip(("baseline", "candidate"), refs)
    ]
    trace = ReplayTraceV1(
        trace_schema_version="1.0.0", trace_digest=sha256_hex({"entries": entries}), entries=entries
    )
    binding_digest = digest_v1(bound)
    request = bound["request"]
    corpus_dir, corpus = _corpus(
        workspace, trace, seed, request["evidence_source_class"], binding_digest
    )
    matrix = load_canonical_constraint_matrix_v1()
    evaluator = EVALUATORS[_DOMAIN]()
    sha = bound["identity"]["fields"]["git_sha"]
    seed_digest = sha256_hex({"seeds": [seed]})
    run_id = str(
        UUID(
            hex=sha256_hex({"request": binding_digest, "artifacts": [first_id, next_id]})[:32],
            version=4,
        )
    )
    run = RunManifestV1(
        run_id=run_id,
        experiment_id=refs[1]["experiment_id"],
        baseline_sha=sha,
        candidate_sha=sha,
        domain_evaluator_id=evaluator.evaluator_id,
        corpus_manifest_ref=str(corpus_dir),
        constraint_matrix_version=matrix.matrix_version,
        constraint_matrix_digest=matrix.matrix_digest,
        seed_set_digest=seed_digest,
        fan_out_evaluation_class="LOCAL_EVALUATION",
        created_at_utc=created_at,
    )
    context = DomainEvaluationContextV1(
        run_manifest=run,
        baseline_identity={"artifact_ref": refs[0]["original_locator"], "digest": first_id},
        candidate_identity={"artifact_ref": refs[1]["original_locator"], "digest": next_id},
        corpus_identity=corpus,
        config_identity={
            "config_path": f"offline-research:{binding_digest}",
            "config_digest": request["config_sha256"],
        },
        data_identity={
            "data_manifest_id": f"offline-research:{binding_digest}",
            "data_digest": request["dataset_sha256"],
        },
        seed_identity={"seeds": [seed], "seed_set_digest": seed_digest},
        constraint_identity=matrix,
        protected_digest_baseline=protected,
        replay_trace=trace,
    )
    dependencies = GvefRunnerDependenciesV1(
        pre_gate=ConstraintMatrixPreGateV1(),
        post_gate=ConstraintMatrixPostGateV1(),
        replay_adapter=BoundContextReplayV1(),
        evaluator=evaluator,
        comparator=ProtectedSemanticComparatorV1(),
        delta_builder=BoundDeltaBuilderV1(),
        evidence_builder=BoundContextEvidenceBuilderV1(context),
        registry=GvefEvidenceRegistryV1(),
        corpus_gate=VectorCorpusIntegrityGateV1(
            registry=VectorCorpusRegistryV1(corpus_root=corpus_dir.parent)
        ),
        promotion_adapter=PassThroughPromotionEvidenceAdapterV1(),
    )
    entry = DomainExecutionInputV1(context, dependencies, refs)
    plan = EvaluationPlanV1(
        f"offline-ddo-research:{binding_digest}",
        bound["source_tree_digest"],
        (_EDGE,),
        (requirement_for_input_v1(_DOMAIN, _VECTOR, entry),),
        tuple(
            DomainExclusionV1(
                domain, "Scope is native artifact binding in the local SL evaluator.", (_EDGE,)
            )
            for domain in CONTRACTS
            if domain != _DOMAIN
        ),
    )
    key, _ = run_required_domain_fanout_v1(
        plan=plan, inputs={_DOMAIN: entry}, archive=evidence, economic_request={}
    )
    receipt = read_system_evaluation_v1(evidence, key, expected_plan=plan)
    return {
        "receipt_id": key,
        "mechanism_status": receipt["mechanism_status"],
        "economic_status": receipt["economic_quality"]["status"],
        "domain_receipt_id": receipt["domains"][_DOMAIN]["receipt_id"],
    }
