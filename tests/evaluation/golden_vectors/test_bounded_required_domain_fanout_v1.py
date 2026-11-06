"""Actual five concrete evaluators; exact result/archive and economic claim gates."""

from dataclasses import replace
import json
from pathlib import Path
from uuid import uuid4

import pytest

from src.evaluation.golden_vectors.integration.domain_result_binding_v1 import (
    CONTRACTS,
    EvaluationBindingError,
    EvaluationPlanV1,
    DomainExclusionV1,
    source_tree_digest_v1,
)
from src.evaluation.golden_vectors.integration.bounded_required_domain_fanout_v1 import (
    EVALUATORS,
    BoundContextReplayV1,
    BoundDeltaBuilderV1,
    BoundContextEvidenceBuilderV1,
    DomainExecutionInputV1,
    requirement_for_input_v1,
    run_required_domain_fanout_v1,
    read_system_evaluation_v1,
)
from src.evaluation.golden_vectors.integration.evaluation_receipt_v1 import (
    EvaluationReceiptArchiveV1,
    retain_native_research_packet_v1,
    retain_mi_packet_v1,
    validate_numeric_packet_v1,
    assess_economic_quality_v1,
)
from src.evaluation.golden_vectors.constraints.pre_constraint_gate_v1 import (
    ConstraintMatrixPreGateV1,
)
from src.evaluation.golden_vectors.constraints.post_constraint_gate_v1 import (
    ConstraintMatrixPostGateV1,
)
from src.evaluation.golden_vectors.constraints.matrix_loader_v1 import (
    load_canonical_constraint_matrix_v1,
)
from src.evaluation.golden_vectors.corpus.registry_v1 import VectorCorpusRegistryV1
from src.evaluation.golden_vectors.corpus.gate_v1 import VectorCorpusIntegrityGateV1
from src.evaluation.golden_vectors.corpus.digest_v1 import (
    corpus_identity_digest_hex,
    vector_identity_digest_hex,
)
from src.evaluation.golden_vectors.contracts.models import (
    CorpusManifestV1,
    VectorManifestV1,
    DomainEvaluationContextV1,
    contract_digest_hex,
)
from src.evaluation.golden_vectors.contracts.enums import ProtectedDomain
from src.evaluation.golden_vectors.digest.comparator_v1 import ProtectedSemanticComparatorV1
from src.evaluation.golden_vectors.registry.evidence_registry_v1 import GvefEvidenceRegistryV1
from src.evaluation.golden_vectors.runner.generic_runner_v1 import GvefRunnerDependenciesV1
from src.evaluation.golden_vectors.promotion.promotion_evidence_adapter_v1 import (
    PassThroughPromotionEvidenceAdapterV1,
)
from tests.evaluation.golden_vectors.evaluator_fixtures_v1 import (
    ptp_context,
    ru_context,
    opt_context,
    sl_context,
    mi_context,
)

ROOT = Path(__file__).resolve().parents[3]


def _inputs(tmp_path):
    archive = EvaluationReceiptArchiveV1(tmp_path / "evidence")
    # Original complete measured owner packet, not a caller-made scalar.
    research = (
        ROOT
        / "docs/ops/evidence/durable_research_and_measured_mi_return_restoration_v1_2026_11_04/artifacts/research"
    )
    key = (research / "session_artifact_id.txt").read_text().strip()
    numeric = retain_native_research_packet_v1(
        archive, owner_root=research / "archive", artifact_id=key
    )
    from src.experiments.canonical_native_research_session_v1 import (
        NativeResearchExecutionArchiveV1,
    )
    from src.experiments.canonical_search_candidate_research_execution_v1 import (
        build_research_execution_gvef_reference_v1,
    )
    from src.experiments.canonical_advanced_search_v1 import canonical_record_payload_v1

    original = NativeResearchExecutionArchiveV1(research / "archive").get(key)
    artifact = canonical_record_payload_v1(
        build_research_execution_gvef_reference_v1(
            original, artifact_ref="execution.json"
        ).learning_artifact
    )
    from tests.learning.test_measured_return_calibration_v1 import _case
    from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.measured_return_calibration_v1 import (
        calibrate_explicit_measured_return_v1,
    )

    mi = calibrate_explicit_measured_return_v1(
        **_case(), durable_store_root=tmp_path / "mi-original-owner"
    )
    mi_numeric = retain_mi_packet_v1(
        archive,
        owner_root=tmp_path / "mi-original-owner",
        durable_evidence_id=mi["persistence"]["durable_evidence_id"],
    )
    contexts = {
        "ranking_universe": ru_context(baseline=["ETH-PERP"], candidate=["ETH-PERP"]),
        "productive_trading_path": ptp_context(),
        "self_learning": sl_context(),
        "optimization_universe": opt_context(),
        "market_intelligence": mi_context(),
    }
    inputs = {}
    requirements = []
    corpus_root = tmp_path / "corpus"
    matrix = load_canonical_constraint_matrix_v1()
    for domain, c in contexts.items():
        raw = c.model_dump(mode="json", by_alias=True)
        run_id = str(uuid4())
        raw["run_manifest"].update(
            run_id=run_id,
            domain_evaluator_id=EVALUATORS[domain]().evaluator_id,
            constraint_matrix_version=matrix.matrix_version,
            constraint_matrix_digest=matrix.matrix_digest,
        )
        raw["constraint_identity"] = matrix.model_dump(mode="json", by_alias=True)
        for row in raw["replay_trace"]["entries"]:
            if "run_id" in row:
                row["run_id"] = run_id
            if domain == "self_learning":
                row["learning_artifact"] = artifact
            if domain == "market_intelligence":
                row["mi_context_bundle"]["measured_calibration_artifact"] = mi_numeric
        c = DomainEvaluationContextV1.model_validate(raw)
        vector_id = "e5-" + domain
        vector = VectorManifestV1(
            vector_id=vector_id,
            vector_class="GoldenHappy",
            schema_version="1.0.0",
            population_selector={
                "selector_id": "E5_EXPLICIT_REPLAY_SNAPSHOT_V1",
                "binding_digest": contract_digest_hex(c.replay_trace),
            },
            invariant_ids=list(CONTRACTS[domain][1]),
            expected_dispositions=["DECLARED_REPLAY_CONTRACTS_ONLY"],
            provenance={
                "source": "TEST_ONLY_SYNTHETIC",
                "ref": "tests/evaluation/golden_vectors/test_bounded_required_domain_fanout_v1.py",
            },
        )
        ref = str((corpus_root / domain).resolve())
        manifest = CorpusManifestV1(
            corpus_version="1.0.0",
            corpus_digest="0" * 64,
            vector_ids=[vector_id],
            metric_schema_version="1.0.0",
            seed_set=[42],
            provenance={"source": "TEST_ONLY_SYNTHETIC", "ref": ref},
        )
        manifest = manifest.model_copy(
            update={
                "corpus_digest": corpus_identity_digest_hex(
                    manifest, vector_digests_by_id={vector_id: vector_identity_digest_hex(vector)}
                )
            }
        )
        folder = corpus_root / domain
        (folder / "vectors").mkdir(parents=True)
        (folder / "vectors" / (vector_id + ".json")).write_text(
            vector.model_dump_json(by_alias=True)
        )
        (folder / "corpus_manifest.json").write_text(manifest.model_dump_json(by_alias=True))
        raw = c.model_dump(mode="json", by_alias=True)
        raw["corpus_identity"] = manifest.model_dump(mode="json", by_alias=True)
        raw["run_manifest"]["corpus_manifest_ref"] = ref
        c = DomainEvaluationContextV1.model_validate(raw)
        deps = GvefRunnerDependenciesV1(
            pre_gate=ConstraintMatrixPreGateV1(),
            post_gate=ConstraintMatrixPostGateV1(),
            replay_adapter=BoundContextReplayV1(),
            evaluator=EVALUATORS[domain](),
            comparator=ProtectedSemanticComparatorV1(
                expected_changed_domains=frozenset({ProtectedDomain.RANKING_UNIVERSE})
                if domain == "ranking_universe"
                else frozenset()
            ),
            delta_builder=BoundDeltaBuilderV1(),
            evidence_builder=BoundContextEvidenceBuilderV1(c),
            registry=GvefEvidenceRegistryV1(),
            corpus_gate=VectorCorpusIntegrityGateV1(
                registry=VectorCorpusRegistryV1(corpus_root=corpus_root)
            ),
            promotion_adapter=PassThroughPromotionEvidenceAdapterV1(),
        )
        refs = (
            (numeric,)
            if domain == "self_learning"
            else (mi_numeric,)
            if domain == "market_intelligence"
            else ()
        )
        entry = DomainExecutionInputV1(c, deps, refs)
        inputs[domain] = entry
        requirements.append(requirement_for_input_v1(domain, vector_id, entry))
    plan = EvaluationPlanV1(
        "E5-explicit-five-domain-offline-replay",
        source_tree_digest_v1(),
        (
            "Research->SelfLearning",
            "MarketIntelligence->Evidence",
            "Ranking->Selection",
            "Core->PRE_EXTERNAL",
        ),
        tuple(requirements),
    )
    return plan, inputs, archive


def test_five_existing_evaluators_are_called_repeated_and_durably_read_back(tmp_path):
    plan, inputs, archive = _inputs(tmp_path)
    key, result = run_required_domain_fanout_v1(
        plan=plan,
        inputs=inputs,
        archive=archive,
        economic_request={"claim": "natural economic improvement"},
    )
    assert result["mechanism_status"] == "PASS", result
    assert result["economic_quality"]["status"] == "BLOCKED"
    for req in plan.required:
        body = archive.get_v1("domain", result["domains"][req.domain]["receipt_id"])
        assert [r["kind"] for r in body["calls"]] == [
            "baseline",
            "candidate",
            "baseline",
            "candidate",
        ]
        assert body["record"]["candidate_result"]["domain"] == req.domain
        assert (
            body["record"]["evidence_bundle"]["invariant_results"]
            == body["record"]["candidate_result"]["invariants"]
        )
        assert body["dependency_binding"]["evaluator"]["class"].endswith(
            EVALUATORS[req.domain].__name__
        )
    assert (
        read_system_evaluation_v1(EvaluationReceiptArchiveV1(archive.root), key, expected_plan=plan)
        == result
    )
    again, reloaded = run_required_domain_fanout_v1(
        plan=plan,
        inputs=inputs,
        archive=archive,
        economic_request={"claim": "natural economic improvement"},
    )
    assert again == key and reloaded == result
    sl = archive.get_v1("domain", result["domains"]["self_learning"]["receipt_id"])
    assert validate_numeric_packet_v1(archive, sl["numeric_evidence"][0])["engine_invocations"] == 4
    mi = archive.get_v1("domain", result["domains"]["market_intelligence"]["receipt_id"])
    assert validate_numeric_packet_v1(archive, mi["numeric_evidence"][0])["realized_return"] != 0


@pytest.mark.parametrize(
    "mode",
    [
        "missing",
        "pass_through",
        "fixture_builder",
        "wrong_evaluator",
        "wrong_corpus",
        "missing_numeric",
        "unknown_dependency",
    ],
)
def test_required_domain_absence_or_substitute_cannot_pass(tmp_path, mode):
    plan, inputs, archive = _inputs(tmp_path)
    domain = "self_learning"
    entry = inputs[domain]
    if mode == "missing":
        del inputs[domain]
    else:
        from src.evaluation.golden_vectors.runner.deterministic_stubs_v1 import (
            DeterministicEvidenceBuilderV1,
            DeterministicDomainEvaluatorV1,
        )
        from src.evaluation.golden_vectors.corpus.gate_v1 import PassThroughCorpusIntegrityGateV1

        if mode == "pass_through":
            entry.dependencies.corpus_gate = PassThroughCorpusIntegrityGateV1()
        if mode == "fixture_builder":
            entry.dependencies.evidence_builder = DeterministicEvidenceBuilderV1()
        if mode == "wrong_evaluator":
            entry.dependencies.evaluator = DeterministicDomainEvaluatorV1()
        if mode == "wrong_corpus":
            entry = replace(
                entry,
                context=entry.context.model_copy(
                    update={
                        "corpus_identity": entry.context.corpus_identity.model_copy(
                            update={"corpus_digest": "f" * 64}
                        )
                    }
                ),
            )
        if mode == "missing_numeric":
            entry = replace(entry, numeric_evidence=())
        if mode == "unknown_dependency":
            entry.dependencies.evaluator = object()
        inputs[domain] = entry
    _, r = run_required_domain_fanout_v1(
        plan=plan, inputs=inputs, archive=archive, economic_request={}
    )
    assert r["mechanism_status"] in {"INCOMPLETE", "BLOCKED"}
    assert r["domains"][domain]["status"] != "PASS"
    assert all(r["domains"][d]["status"] == "PASS" for d in inputs if d != domain)


def _legacy_digest(record):
    from src.evaluation.golden_vectors.runner.generic_runner_v1 import (
        GenericRunnerV1,
        GvefRunRecordV1,
    )
    from src.evaluation.golden_vectors.runner.states import RunnerState
    from src.evaluation.golden_vectors.contracts.models import (
        RunManifestV1,
        DecisionDeltaManifestV1,
        ProtectedSemanticDigestsV1,
        EvidenceBundleV1,
        DomainEvaluationResultV1,
    )

    r = GvefRunRecordV1(
        state=RunnerState(record["state"]),
        state_history=[RunnerState(s) for s in record["state_history"]],
        run_manifest=RunManifestV1.model_validate(record["run_manifest"]),
        baseline_result_digest=record["baseline_result_digest"],
        candidate_result=DomainEvaluationResultV1.model_validate(record["candidate_result"]),
        delta_manifest=DecisionDeltaManifestV1.model_validate(record["delta_manifest"]),
        protected_digests=ProtectedSemanticDigestsV1.model_validate(record["protected_digests"]),
        evidence_bundle=EvidenceBundleV1.model_validate(record["evidence_bundle"]),
    )
    return GenericRunnerV1()._protected_output_digest(r)


@pytest.mark.parametrize(
    "field", ["candidate_invariant", "candidate_metric", "candidate_semantics", "corpus", "calls"]
)
def test_additive_binding_detects_fields_outside_legacy_protected_digest(tmp_path, field):
    plan, inputs, archive = _inputs(tmp_path)
    key, system = run_required_domain_fanout_v1(
        plan=plan, inputs=inputs, archive=archive, economic_request={}
    )
    ref = system["domains"]["ranking_universe"]["receipt_id"]
    path = archive.root / "records/domain" / (ref + ".json")
    envelope = json.loads(path.read_bytes())
    b = envelope["body"]
    old = _legacy_digest(b["record"])
    assert old == b["record"]["protected_output_digest"]
    if field == "candidate_invariant":
        b["record"]["candidate_result"]["invariants"][0]["pass"] = False
    if field == "candidate_metric":
        b["record"]["candidate_result"]["metrics"][0]["value"] += 1
    if field == "candidate_semantics":
        b["record"]["candidate_result"]["semantic_digest_deltas"]["changed_uncovered_value"] = 42
    if field == "corpus":
        b["corpus_snapshot"]["vectors"][b["requirement"]["vector_id"]]["expected_dispositions"] = [
            "unproved"
        ]
    if field == "calls":
        b["calls"][1]["result"]["metrics"][0]["value"] += 1
    assert _legacy_digest(b["record"]) == old
    path.write_text(json.dumps(envelope))  # isolated evidence corruption, no repair
    with pytest.raises(EvaluationBindingError, match="DIGEST"):
        read_system_evaluation_v1(archive, key, expected_plan=plan)


@pytest.mark.parametrize("kind", ["native", "mi"])
def test_exact_original_numeric_bytes_are_checked_after_reload(tmp_path, kind):
    import base64

    plan, inputs, archive = _inputs(tmp_path)
    key, system = run_required_domain_fanout_v1(
        plan=plan, inputs=inputs, archive=archive, economic_request={}
    )
    d = "self_learning" if kind == "native" else "market_intelligence"
    body = archive.get_v1("domain", system["domains"][d]["receipt_id"])
    numeric = body["numeric_evidence"][0]
    path = archive.root / "numeric" / (numeric["original_bytes_sha256"] + ".json")
    saved = json.loads(path.read_text())
    data = json.loads(base64.b64decode(saved["base64"]))
    if kind == "native":
        data["measurement_receipt"]["runs"][0]["statistics"]["sharpe"]["value"] += 1
    else:
        data["calibration_evidence"]["calibration_result"]["realized_return"] += 1
    saved["base64"] = base64.b64encode(json.dumps(data).encode()).decode()
    path.write_text(json.dumps(saved))
    with pytest.raises(EvaluationBindingError, match="NUMERIC"):
        read_system_evaluation_v1(archive, key, expected_plan=plan)


def test_even_rehashed_receipt_must_satisfy_actual_requirement_fields(tmp_path):
    from src.evaluation.golden_vectors.integration.evaluation_receipt_v1 import (
        evaluation_receipt_binding_v1,
    )

    plan, inputs, archive = _inputs(tmp_path)
    key, system = run_required_domain_fanout_v1(
        plan=plan, inputs=inputs, archive=archive, economic_request={}
    )
    body = archive.get_v1("domain", system["domains"]["self_learning"]["receipt_id"])
    for i in (1, 3):
        body["calls"][i]["result"]["invariants"][0]["pass"] = False
    body["record"]["candidate_result"]["invariants"][0]["pass"] = False
    body["evaluation_receipt"] = evaluation_receipt_binding_v1(body)
    changed = archive.append_v1("domain", body)
    system["domains"]["self_learning"]["receipt_id"] = changed
    replacement = archive.append_v1("system", system)
    with pytest.raises(EvaluationBindingError, match="INVARIANT"):
        read_system_evaluation_v1(archive, replacement, expected_plan=plan)


def test_missing_domain_can_resume_without_reinvoking_completed_domains(tmp_path):
    plan, inputs, archive = _inputs(tmp_path)
    missing = dict(inputs)
    missing.pop("market_intelligence")
    _, incomplete = run_required_domain_fanout_v1(
        plan=plan, inputs=missing, archive=archive, economic_request={}
    )
    assert incomplete["mechanism_status"] == "INCOMPLETE"
    # A second registration would fail in these same original in-memory registries.
    # Only the missing original domain executes now.
    key, done = run_required_domain_fanout_v1(
        plan=plan, inputs=inputs, archive=archive, economic_request={}
    )
    assert done["mechanism_status"] == "PASS"
    for d in missing:
        assert done["domains"][d] == incomplete["domains"][d]
    assert read_system_evaluation_v1(archive, key, expected_plan=plan) == done


def test_not_required_needs_explicit_impact_and_cannot_hide_missing_domain(tmp_path):
    plan, inputs, archive = _inputs(tmp_path)
    removed = plan.required[-1]
    with pytest.raises(EvaluationBindingError, match="ALL_DOMAINS"):
        replace(plan, required=plan.required[:-1]).validate_v1()
    with pytest.raises(EvaluationBindingError, match="IMPACT"):
        replace(
            plan,
            required=plan.required[:-1],
            not_required=(DomainExclusionV1(removed.domain, "", ()),),
        ).validate_v1()
    scoped = replace(
        plan,
        change_id="declared narrower change",
        required=plan.required[:-1],
        not_required=(
            DomainExclusionV1(
                removed.domain,
                "This explicitly scoped change does not alter the MI context adapter.",
                ("MI context adapter->MI evaluator",),
            ),
        ),
    )
    chosen = {k: v for k, v in inputs.items() if k != removed.domain}
    _, result = run_required_domain_fanout_v1(
        plan=scoped, inputs=chosen, archive=archive, economic_request={}
    )
    assert result["mechanism_status"] == "PASS"
    assert result["not_required"][0]["impact_reason"]
    assert len(result["domains"]) == 4


@pytest.mark.parametrize(
    "supplied",
    [
        {},
        {
            "claim": "profitable",
            "costs": True,
            "funding": True,
            "independent_comparison": True,
            "independent_market_data": True,
            "horizon": True,
            "uncertainty": True,
            "target_metric": "pnl",
        },
    ],
)
def test_caller_flags_do_not_turn_mechanism_into_economic_quality(supplied):
    result = assess_economic_quality_v1(supplied)
    assert result["status"] == "BLOCKED"
    assert "ECONOMIC_QUALITY_CONTRACT_NOT_RATIFIED" in result["reasons"]
    assert (
        not result["profitability_established"]
        and not result["natural_learning_usefulness_established"]
    )


def test_registry_replay_and_corpus_numbers_remain_detached_from_archive_reader(tmp_path):
    plan, inputs, archive = _inputs(tmp_path)
    key, result = run_required_domain_fanout_v1(
        plan=plan, inputs=inputs, archive=archive, economic_request={}
    )
    result["domains"]["self_learning"]["status"] = "FAKE"
    original = read_system_evaluation_v1(archive, key, expected_plan=plan)
    assert original["domains"]["self_learning"]["status"] == "PASS"
    refs = archive.get_v1("domain", original["domains"]["self_learning"]["receipt_id"])
    refs["calls"][0]["result"]["metrics"][0]["value"] = "changed detached readback"
    assert read_system_evaluation_v1(archive, key, expected_plan=plan)["mechanism_status"] == "PASS"


def test_fresh_process_reads_archived_numbers_without_live_corpus_or_owner(tmp_path):
    import subprocess

    plan, inputs, archive = _inputs(tmp_path)
    key, result = run_required_domain_fanout_v1(
        plan=plan, inputs=inputs, archive=archive, economic_request={}
    )
    plan_path = tmp_path / "expected-plan.json"
    plan_path.write_text(json.dumps(plan.to_dict_v1()))
    (tmp_path / "corpus").rename(tmp_path / "retained-original-corpus")
    (tmp_path / "mi-original-owner").rename(tmp_path / "retained-original-mi-owner")
    code = """
import json,sys
from pathlib import Path
from src.evaluation.golden_vectors.integration.domain_result_binding_v1 import EvaluationPlanV1,DomainRequirementV1,DomainExclusionV1
from src.evaluation.golden_vectors.integration.evaluation_receipt_v1 import EvaluationReceiptArchiveV1,validate_numeric_packet_v1
from src.evaluation.golden_vectors.integration.bounded_required_domain_fanout_v1 import read_system_evaluation_v1,EVALUATORS
raw=json.loads(Path(sys.argv[2]).read_text());raw['required']=tuple(DomainRequirementV1(**r) for r in raw['required']);raw['not_required']=tuple(DomainExclusionV1(**r) for r in raw['not_required']);p=EvaluationPlanV1(**raw)
def forbidden(*a,**k):raise AssertionError('readback must not reevaluate')
for cls in EVALUATORS.values():cls.evaluate_baseline=forbidden;cls.evaluate_candidate=forbidden
archive=EvaluationReceiptArchiveV1(Path(sys.argv[1]));r=read_system_evaluation_v1(archive,sys.argv[3],expected_plan=p)
b=archive.get_v1('domain',r['domains']['market_intelligence']['receipt_id']);numeric=validate_numeric_packet_v1(archive,b['numeric_evidence'][0])
print('RESULT='+json.dumps({'status':r['mechanism_status'],'numeric':numeric}))
"""
    root = Path(__file__).resolve().parents[3]
    r = subprocess.run(
        [str(root / "scripts/pt"), "-c", code, str(archive.root), str(plan_path), key],
        cwd=root,
        text=True,
        capture_output=True,
    )
    assert r.returncode == 0, r.stdout + r.stderr
    decoded = json.loads(next(s[7:] for s in r.stdout.splitlines() if s.startswith("RESULT=")))
    assert decoded["status"] == "PASS" and decoded["numeric"]["realized_return"] > 0
    assert decoded["numeric"]["error"] != decoded["numeric"]["realized_return"]


def test_actual_failed_domain_cannot_be_hidden_by_whole_system_tag(tmp_path):
    plan, inputs, archive = _inputs(tmp_path)
    domain = "market_intelligence"
    e = inputs[domain]
    raw = e.context.model_dump(mode="json", by_alias=True)
    raw["run_manifest"]["fan_out_evaluation_class"] = "WHOLE_SYSTEM_REPROOF"
    raw["replay_trace"]["entries"][0]["venue_post"] = True
    # Create a new correctly bound corpus/plan for the forbidden input: neither
    # a digest mismatch nor a WHOLE_SYSTEM label substitutes for evaluator work.
    context = DomainEvaluationContextV1.model_validate(raw)
    folder = Path(context.run_manifest.corpus_manifest_ref)
    vector_path = next((folder / "vectors").glob("*.json"))
    v = VectorManifestV1.model_validate(json.loads(vector_path.read_text()))
    v = v.model_copy(
        update={
            "population_selector": v.population_selector.model_copy(
                update={"binding_digest": contract_digest_hex(context.replay_trace)}
            )
        }
    )
    manifest = context.corpus_identity
    manifest = manifest.model_copy(
        update={
            "corpus_digest": corpus_identity_digest_hex(
                manifest, vector_digests_by_id={v.vector_id: vector_identity_digest_hex(v)}
            )
        }
    )
    vector_path.write_text(v.model_dump_json(by_alias=True))
    (folder / "corpus_manifest.json").write_text(manifest.model_dump_json(by_alias=True))
    context = context.model_copy(update={"corpus_identity": manifest})
    e.dependencies.evidence_builder = BoundContextEvidenceBuilderV1(context)
    entry = replace(e, context=context)
    inputs[domain] = entry
    updated = requirement_for_input_v1(domain, v.vector_id, entry)
    plan = replace(
        plan, required=tuple(updated if r.domain == domain else r for r in plan.required)
    )
    _, result = run_required_domain_fanout_v1(
        plan=plan, inputs=inputs, archive=archive, economic_request={}
    )
    assert result["mechanism_status"] == "BLOCKED"
    blocked = archive.get_v1("domain", result["domains"][domain]["receipt_id"])
    assert len(blocked["calls"]) == 1 and blocked["calls"][0]["result"]["verdict"] == "FAIL"
    assert blocked["record"]["run_manifest"]["fan_out_evaluation_class"] == "WHOLE_SYSTEM_REPROOF"
    # Original evaluator failure routing remains distinct from the plan's actual
    # all-domain orchestration and its blocked aggregate.
    assert blocked["record"]["fan_out_evaluation_class"] == "LOCAL_EVALUATION"


def test_source_generation_and_comparator_policy_are_not_implicit(tmp_path):
    plan, inputs, archive = _inputs(tmp_path)
    with pytest.raises(EvaluationBindingError, match="SOURCE_GENERATION"):
        run_required_domain_fanout_v1(
            plan=replace(plan, source_tree_digest="0" * 64),
            inputs=inputs,
            archive=archive,
            economic_request={},
        )
    domain = "ranking_universe"
    inputs[domain].dependencies.comparator = ProtectedSemanticComparatorV1()
    _, result = run_required_domain_fanout_v1(
        plan=plan, inputs=inputs, archive=archive, economic_request={}
    )
    assert result["mechanism_status"] == "BLOCKED"
    assert (
        "IMPLEMENTATION_DRIFT"
        in archive.get_v1("domain", result["domains"][domain]["receipt_id"])["reason"]
    )


def test_system_claim_scope_cannot_be_promoted_by_rehashing(tmp_path):
    plan, inputs, archive = _inputs(tmp_path)
    key, result = run_required_domain_fanout_v1(
        plan=plan, inputs=inputs, archive=archive, economic_request={}
    )
    result["claim_scope"] = "ALL_NATURAL_ECONOMIC_DOMAIN_QUALITY"
    altered = archive.append_v1("system", result)
    with pytest.raises(EvaluationBindingError, match="CLAIM"):
        read_system_evaluation_v1(archive, altered, expected_plan=plan)


@pytest.mark.parametrize("domain", ["self_learning", "market_intelligence"])
def test_valid_but_unrelated_numeric_packet_cannot_certify_a_replay(tmp_path, domain):
    from src.evaluation.golden_vectors.integration.bounded_required_domain_fanout_v1 import (
        require_numeric_context_binding_v1,
    )

    plan, inputs, archive = _inputs(tmp_path)
    entry = inputs[domain]
    require_numeric_context_binding_v1(domain, entry.context, entry.numeric_evidence, archive)
    raw = entry.context.model_dump(mode="json", by_alias=True)
    for row in raw["replay_trace"]["entries"]:
        if domain == "self_learning":
            row["learning_artifact"]["payload_sha256"] = "0" * 64
        else:
            row["mi_context_bundle"]["measured_calibration_artifact"]["original_artifact_id"] = (
                "valid-but-unrelated-label"
            )
    foreign = DomainEvaluationContextV1.model_validate(raw)
    # The retained original packet itself is still fully valid and readable.
    validate_numeric_packet_v1(archive, entry.numeric_evidence[0])
    with pytest.raises(EvaluationBindingError, match="JOIN_MISMATCH"):
        require_numeric_context_binding_v1(domain, foreign, entry.numeric_evidence, archive)
