"""BWP-7 corpus test fixtures (synthetic mechanism vectors)."""

from __future__ import annotations

from copy import deepcopy

from src.evaluation.golden_vectors.contracts.models import CorpusManifestV1, VectorManifestV1
from src.evaluation.golden_vectors.contracts.validation import (
    parse_corpus_manifest_v1,
    parse_domain_evaluation_context_v1,
    parse_vector_manifest_v1,
)
from src.evaluation.golden_vectors.corpus.digest_v1 import (
    corpus_identity_digest_hex,
    vector_identity_digest_hex,
)
from src.evaluation.golden_vectors.corpus.registry_v1 import CANONICAL_CORPUS_ROOT

FIXTURE_CORPUS_REF = f"{CANONICAL_CORPUS_ROOT}/fixture_corpus_v1"
_SHA = "a" * 64


def vector_ptp() -> dict:
    return {
        "vector_id": "vec-gvef-ptp-mechanism-001",
        "vector_class": "GoldenHappy",
        "schema_version": "1.0.0",
        "population_selector": {
            "selector_id": "mechanism_ptp_v1",
            "binding_digest": _SHA,
        },
        "invariant_ids": ["ptp.pre_external_terminal"],
        "expected_dispositions": ["OBSERVE_ONLY"],
        "provenance": {
            "source": "TEST_ONLY_SYNTHETIC",
            "ref": "tests/evaluation/golden_vectors/corpus_fixtures_v1.py",
        },
    }


def vector_ru() -> dict:
    return {
        "vector_id": "vec-gvef-ru-mechanism-001",
        "vector_class": "GoldenNeutral",
        "schema_version": "1.0.0",
        "population_selector": {
            "selector_id": "mechanism_ru_v1",
            "binding_digest": _SHA,
        },
        "invariant_ids": ["ru.not_selection"],
        "provenance": {
            "source": "TEST_ONLY_SYNTHETIC",
            "ref": "tests/evaluation/golden_vectors/corpus_fixtures_v1.py",
        },
    }


def build_corpus_manifest_dict() -> dict:
    vectors = [
        parse_vector_manifest_v1(vector_ptp()),
        parse_vector_manifest_v1(vector_ru()),
    ]
    vector_ids = [v.vector_id for v in vectors]
    digests = {v.vector_id: vector_identity_digest_hex(v) for v in vectors}
    manifest_stub = CorpusManifestV1(
        corpus_version="1.0.0",
        corpus_digest=_SHA,
        vector_ids=vector_ids,
        metric_schema_version="1.0.0",
        seed_set=[42],
        provenance={"source": "TEST_ONLY_SYNTHETIC", "ref": FIXTURE_CORPUS_REF},
    )
    digest = corpus_identity_digest_hex(manifest_stub, vector_digests_by_id=digests)
    return {
        "corpus_version": "1.0.0",
        "corpus_digest": digest,
        "vector_ids": vector_ids,
        "metric_schema_version": "1.0.0",
        "seed_set": [42],
        "provenance": {"source": "TEST_ONLY_SYNTHETIC", "ref": FIXTURE_CORPUS_REF},
    }


def parsed_fixture_corpus() -> CorpusManifestV1:
    return parse_corpus_manifest_v1(build_corpus_manifest_dict())


def parsed_fixture_vectors() -> dict[str, VectorManifestV1]:
    return {
        "vec-gvef-ptp-mechanism-001": parse_vector_manifest_v1(vector_ptp()),
        "vec-gvef-ru-mechanism-001": parse_vector_manifest_v1(vector_ru()),
    }


def corpus_bound_context(*, domain_evaluator_id: str = "productive_trading_path_evaluator_v1"):
    from tests.evaluation.golden_vectors.runner_fixtures_v1 import domain_context

    ctx = deepcopy(domain_context())
    ctx["run_manifest"]["corpus_manifest_ref"] = FIXTURE_CORPUS_REF
    ctx["run_manifest"]["domain_evaluator_id"] = domain_evaluator_id
    manifest = build_corpus_manifest_dict()
    ctx["corpus_identity"] = manifest
    return parse_domain_evaluation_context_v1(ctx)


def canonical_vector_payloads_for_order_test() -> list[dict]:
    return [vector_ptp(), vector_ru()]
