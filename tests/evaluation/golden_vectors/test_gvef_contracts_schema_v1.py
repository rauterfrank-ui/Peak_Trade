"""BWP-1 GVEF V1.5 contract schema tests."""

from __future__ import annotations

import ast
import importlib
from pathlib import Path

import pytest

from src.evaluation.golden_vectors.contracts import (
    EvidenceBundleLifecycleState,
    GvefSchemaError,
    SCHEMA_FAILURE,
    contract_canonical_bytes,
    contract_digest_hex,
    evidence_complete_not_implied_by_schema,
    parse_boundary_result_v1,
    parse_capital_risk_crs_sizing_evidence_bundle_v1,
    parse_constraint_matrix_v1,
    parse_corpus_manifest_v1,
    parse_decision_delta_manifest_v1,
    parse_domain_evaluation_context_v1,
    parse_domain_evaluation_result_v1,
    parse_evidence_bundle_v1,
    parse_invariant_result_v1,
    parse_metric_result_v1,
    parse_promotion_evidence_envelope_v1,
    parse_protected_digest_manifest_v1,
    parse_protected_semantic_digests_v1,
    parse_ranking_delta_manifest_v1,
    parse_ranking_universe_manifest_v1,
    parse_run_manifest_v1,
    parse_vector_manifest_v1,
    sha256_hex,
    validate_evidence_bundle_lifecycle_state,
)
from src.evaluation.golden_vectors.contracts.enums import GVEF_CONTRACTS_PACKAGE_VERSION

_SHA = "a" * 64
_SHA_B = "b" * 64
_GIT = "e1c884fcb6e105864073d049617bbed57811ecf9"
_TS = "2026-10-04T09:00:00Z"


def _provenance() -> dict:
    return {"source": "fixture", "ref": "tests/evaluation/golden_vectors"}


def _protected_digests(ru: str = _SHA, sel: str = _SHA_B) -> dict:
    entry = {"digest_hex": ru, "schema_version": "1.0.0"}
    entry_sel = {"digest_hex": sel, "schema_version": "1.0.0"}
    return {"ranking_universe": entry, "selection": entry_sel}


def _run_manifest() -> dict:
    return {
        "run_id": "550e8400-e29b-41d4-a716-446655440000",
        "experiment_id": "exp-gvef-bwp1",
        "baseline_sha": _GIT,
        "candidate_sha": _GIT,
        "domain_evaluator_id": "productive_trading_path_evaluator_v1",
        "corpus_manifest_ref": "corpus/fixture/v1",
        "constraint_matrix_version": "1.5.0",
        "constraint_matrix_digest": _SHA,
        "seed_set_digest": _SHA,
        "fan_out_evaluation_class": "LOCAL_EVALUATION",
        "created_at_utc": _TS,
    }


def _vector_manifest() -> dict:
    return {
        "vector_id": "vec-001",
        "vector_class": "GoldenHappy",
        "schema_version": "1.0.0",
        "population_selector": {"selector_id": "pop-a", "binding_digest": _SHA},
        "invariant_ids": ["inv.pre_external_terminal"],
        "provenance": _provenance(),
    }


def _corpus_manifest() -> dict:
    return {
        "corpus_version": "1.0.0",
        "corpus_digest": _SHA,
        "vector_ids": ["vec-001"],
        "metric_schema_version": "1.0.0",
        "seed_set": [42],
        "provenance": _provenance(),
    }


def _constraint_matrix() -> dict:
    return {
        "matrix_version": "1.5.0",
        "matrix_digest": _SHA,
        "baseline_sha": _GIT,
        "rows": [
            {
                "SIGNAL_EDGE": "RANKING_UNIVERSE->SELECTION",
                "DOMAIN": "RANKING_UNIVERSE",
                "PRODUCER": "Cap2.2 ranking context",
                "CONSUMER": "Cap2.3 SOLE_SELECTION_OWNER",
                "CONTRACT": "RANKING_UNIVERSE_TO_FULL_CORE_SSF_HANDOFF_CONTRACT_V1",
                "ALLOWED_DIRECTION": "handoff_to_cap23_only",
                "FORBIDDEN_DIRECTION": "gvef_to_selection_command",
                "AUTHORITY_OWNER": "Cap2.3 selection",
                "REQUIRED_CURRENT_VERDICT": "PROVEN_CURRENT",
                "PRODUCTIVE_REACHABILITY": "PROVEN_CURRENT",
                "FAILURE_ACTION": "AUTHORITY_FAILURE",
                "EVIDENCE_PROVENANCE": "handoff contract + tests",
            }
        ],
    }


def _domain_context() -> dict:
    return {
        "run_manifest": _run_manifest(),
        "baseline_identity": {"artifact_ref": "baseline", "digest": _SHA},
        "candidate_identity": {"artifact_ref": "candidate", "digest": _SHA_B},
        "corpus_identity": _corpus_manifest(),
        "config_identity": {"config_path": "config/fixture.json", "config_digest": _SHA},
        "data_identity": {"data_manifest_id": "data-1", "data_digest": _SHA},
        "seed_identity": {"seeds": [42], "seed_set_digest": _SHA},
        "constraint_identity": _constraint_matrix(),
        "protected_digest_baseline": _protected_digests(),
        "replay_trace": {
            "trace_schema_version": "1.0.0",
            "trace_digest": _SHA,
            "entries": [],
        },
    }


def _domain_result() -> dict:
    return {
        "domain": "productive_trading_path",
        "verdict": "PASS",
        "metrics": [{"metric_id": "m1", "value": 1}],
        "invariants": [{"invariant_id": "i1", "pass": True}],
        "boundary_results": [
            {
                "edge_id": "PTP->PRE_EXTERNAL",
                "pass": True,
                "producer": "full_core",
                "consumer": "PRE_EXTERNAL",
                "current_verdict": "PROVEN_CURRENT",
            }
        ],
        "evidence_refs": ["evidence/fixture"],
    }


def _evidence_bundle() -> dict:
    return {
        "run_id": "550e8400-e29b-41d4-a716-446655440000",
        "experiment_id": "exp-gvef-bwp1",
        "baseline_sha": _GIT,
        "candidate_sha": _GIT,
        "constraint_matrix_version": "1.5.0",
        "constraint_matrix_digest": _SHA,
        "vector_corpus_version": "1.0.0",
        "vector_corpus_digest": _SHA,
        "protected_semantic_digests": _protected_digests(),
        "config_digest": _SHA,
        "config_provenance": _provenance(),
        "data_manifest": {"data_manifest_id": "data-1", "data_digest": _SHA},
        "data_provenance": _provenance(),
        "seed_set": [42],
        "metric_schema_version": "1.0.0",
        "invariant_results": [{"invariant_id": "i1", "pass": True}],
        "authority_boundary_results": [
            {
                "edge_id": "GVEF->PRE_EXTERNAL",
                "pass": True,
                "producer": "gvef",
                "consumer": "PRE_EXTERNAL",
                "current_verdict": "PROVEN_CURRENT",
            }
        ],
        "decision_delta_manifest": {
            "deltas": [{"delta_id": "d1", "before": "a", "after": "b"}],
            "digest": _SHA,
        },
        "fan_out_evaluation_class": "LOCAL_EVALUATION",
        "evidence_digest": _SHA,
        "promotion_status": "EXTERNAL_UNSET",
        "post_constraint_gate_pass": False,
    }


CONTRACT_FIXTURES = [
    ("RunManifest", parse_run_manifest_v1, _run_manifest),
    ("VectorManifest", parse_vector_manifest_v1, _vector_manifest),
    ("CorpusManifest", parse_corpus_manifest_v1, _corpus_manifest),
    ("ConstraintMatrix", parse_constraint_matrix_v1, _constraint_matrix),
    ("DomainEvaluationContext", parse_domain_evaluation_context_v1, _domain_context),
    ("DomainEvaluationResult", parse_domain_evaluation_result_v1, _domain_result),
    ("MetricResult", parse_metric_result_v1, lambda: {"metric_id": "m", "value": 7}),
    ("InvariantResult", parse_invariant_result_v1, lambda: {"invariant_id": "i", "pass": True}),
    (
        "BoundaryResult",
        parse_boundary_result_v1,
        lambda: {
            "edge_id": "e1",
            "pass": True,
            "producer": "p",
            "consumer": "c",
            "current_verdict": "PROVEN_CURRENT",
        },
    ),
    (
        "ProtectedDigestManifest",
        parse_protected_digest_manifest_v1,
        lambda: {
            "domain": "ranking_universe",
            "digest_hex": _SHA,
            "schema_version": "1.0.0",
            "verdict": "DIGEST_EQUAL",
        },
    ),
    (
        "DecisionDeltaManifest",
        parse_decision_delta_manifest_v1,
        lambda: {"deltas": [], "digest": _SHA},
    ),
    (
        "RankingUniverseManifest",
        parse_ranking_universe_manifest_v1,
        lambda: {
            "membership": [{"instrument_id": "BTC-USD"}],
            "provenance": _provenance(),
        },
    ),
    (
        "RankingDeltaManifest",
        parse_ranking_delta_manifest_v1,
        lambda: {"digest": _SHA},
    ),
    (
        "CapitalRiskCrsSizingEvidenceBundle",
        parse_capital_risk_crs_sizing_evidence_bundle_v1,
        lambda: {"sizing_verdict": "PASS"},
    ),
    ("EvidenceBundle", parse_evidence_bundle_v1, _evidence_bundle),
    (
        "PromotionEvidenceEnvelope",
        parse_promotion_evidence_envelope_v1,
        lambda: {
            "evidence_bundle_ref": "runs/fixture",
            "evidence_digest": _SHA,
            "governance_handoff_timestamp": _TS,
            "post_constraint_gate_pass": True,
            "fan_out_evaluation_class": "LOCAL_EVALUATION",
        },
    ),
]


@pytest.mark.parametrize("name,parser,factory", CONTRACT_FIXTURES)
def test_contract_valid_fixture_parses(name: str, parser, factory) -> None:
    model = parser(factory())
    assert model is not None


def test_all_sixteen_contracts_listed() -> None:
    assert len(CONTRACT_FIXTURES) == 16


def test_missing_required_field_fail_closed() -> None:
    payload = _run_manifest()
    del payload["run_id"]
    with pytest.raises(GvefSchemaError):
        parse_run_manifest_v1(payload)


def test_unknown_enum_fail_closed() -> None:
    payload = _run_manifest()
    payload["fan_out_evaluation_class"] = "OTHER"
    with pytest.raises(GvefSchemaError):
        parse_run_manifest_v1(payload)


def test_extra_field_fail_closed() -> None:
    payload = _run_manifest()
    payload["unexpected"] = True
    with pytest.raises(GvefSchemaError):
        parse_run_manifest_v1(payload)


def test_illegal_null_required_fail_closed() -> None:
    payload = _run_manifest()
    payload["experiment_id"] = None
    with pytest.raises(GvefSchemaError):
        parse_run_manifest_v1(payload)


def test_permitted_optional_null_ranking_manifest() -> None:
    payload = _evidence_bundle()
    payload["ranking_universe_manifest"] = None
    model = parse_evidence_bundle_v1(payload)
    assert model.ranking_universe_manifest is None


def test_invalid_schema_version_vector_fail_closed() -> None:
    payload = _vector_manifest()
    payload["schema_version"] = "not-semver"
    with pytest.raises(GvefSchemaError):
        parse_vector_manifest_v1(payload)


def test_malformed_nested_contract_fail_closed() -> None:
    payload = _domain_context()
    payload["corpus_identity"] = {"corpus_version": "1.0.0"}
    with pytest.raises(GvefSchemaError):
        parse_domain_evaluation_context_v1(payload)


def test_canonical_serialization_deterministic() -> None:
    m1 = parse_run_manifest_v1(_run_manifest())
    m2 = parse_run_manifest_v1(_run_manifest())
    b1 = contract_canonical_bytes(m1)
    b2 = contract_canonical_bytes(m2)
    assert b1 == b2


def test_sha256_digest_deterministic() -> None:
    m = parse_corpus_manifest_v1(_corpus_manifest())
    d1 = contract_digest_hex(m)
    d2 = contract_digest_hex(m)
    assert d1 == d2
    assert d1 == sha256_hex(
        {
            "corpus_version": "1.0.0",
            "corpus_digest": _SHA,
            "vector_ids": ["vec-001"],
            "metric_schema_version": "1.0.0",
            "seed_set": [42],
            "provenance": _provenance(),
        }
    )


def test_ranking_universe_selection_digest_separation() -> None:
    payload = _evidence_bundle()
    payload["protected_semantic_digests"] = _protected_digests(ru=_SHA, sel=_SHA)
    with pytest.raises(GvefSchemaError):
        parse_evidence_bundle_v1(payload)


def test_protected_semantic_digests_distinct_domains() -> None:
    d = parse_protected_semantic_digests_v1(_protected_digests())
    assert d.ranking_universe.digest_hex != d.selection.digest_hex


def test_evidence_lifecycle_states_distinct() -> None:
    assert (
        EvidenceBundleLifecycleState.BUILT
        != EvidenceBundleLifecycleState.VALIDATED
        != EvidenceBundleLifecycleState.REGISTERED
    )
    assert validate_evidence_bundle_lifecycle_state("BUILT") == EvidenceBundleLifecycleState.BUILT
    with pytest.raises(GvefSchemaError):
        validate_evidence_bundle_lifecycle_state("REGISTERED_BY_DEFAULT")


def test_evidence_complete_not_implied() -> None:
    bundle = parse_evidence_bundle_v1(_evidence_bundle())
    assert bundle.post_constraint_gate_pass is False
    assert evidence_complete_not_implied_by_schema() is True


def test_promotion_envelope_requires_post_gate_pass() -> None:
    payload = {
        "evidence_bundle_ref": "runs/x",
        "evidence_digest": _SHA,
        "governance_handoff_timestamp": _TS,
        "post_constraint_gate_pass": False,
        "fan_out_evaluation_class": "LOCAL_EVALUATION",
    }
    with pytest.raises(GvefSchemaError):
        parse_promotion_evidence_envelope_v1(payload)


def test_metric_float_forbidden() -> None:
    with pytest.raises(GvefSchemaError):
        parse_metric_result_v1({"metric_id": "m", "value": 1.5})


def test_schema_failure_classification_constant() -> None:
    assert SCHEMA_FAILURE == "SCHEMA_FAILURE"


def test_package_version_constant() -> None:
    assert GVEF_CONTRACTS_PACKAGE_VERSION == "1.5.0"


FORBIDDEN_IMPORT_FRAGMENTS = (
    "full_core_live_path_composition_root_v1",
    "single_selected_future_policy_v1.persistence",
    "current_productive_cap24_selection_state_canonical_writer",
    "full_core_productive_http_post_transport",
    "checkout_independent_credential",
    "optimization_proposal_governance_ingress_v1",
    "governed_productive_configuration_apply_authority",
)


def test_forbidden_productive_imports_absent() -> None:
    root = Path("src/evaluation/golden_vectors/contracts")
    for path in root.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    for frag in FORBIDDEN_IMPORT_FRAGMENTS:
                        assert frag not in alias.name
            elif isinstance(node, ast.ImportFrom) and node.module:
                for frag in FORBIDDEN_IMPORT_FRAGMENTS:
                    assert frag not in node.module


def test_contracts_module_importable_without_productive_side_effects() -> None:
    mod = importlib.import_module("src.evaluation.golden_vectors.contracts")
    assert mod.GVEF_CONTRACTS_PACKAGE_VERSION == "1.5.0"
