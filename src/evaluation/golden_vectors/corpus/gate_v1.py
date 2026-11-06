"""Generic corpus integrity gate (orchestration boundary only)."""

from __future__ import annotations

from typing import Protocol

from src.evaluation.golden_vectors.contracts.models import DomainEvaluationContextV1, RunManifestV1
from src.evaluation.golden_vectors.corpus.errors import GvefCorpusDriftError
from src.evaluation.golden_vectors.corpus.registry_v1 import VectorCorpusRegistryV1


class CorpusIntegrityGateV1(Protocol):
    def evaluate_bound_corpus(
        self,
        *,
        run: RunManifestV1,
        context: DomainEvaluationContextV1,
    ) -> None:
        """Raise GvefCorpusDriftError on drift; return silently on success."""


class PassThroughCorpusIntegrityGateV1:
    """Default: no corpus root binding (legacy runner fixtures)."""

    def evaluate_bound_corpus(
        self,
        *,
        run: RunManifestV1,
        context: DomainEvaluationContextV1,
    ) -> None:
        _ = (run, context)


class VectorCorpusIntegrityGateV1:
    """Validate run manifest ref + frozen context corpus identity."""

    def __init__(self, *, registry: VectorCorpusRegistryV1) -> None:
        self._registry = registry
        self._bound_identity: str | None = None
        self._bound_ref: str | None = None

    def evaluate_bound_corpus(
        self,
        *,
        run: RunManifestV1,
        context: DomainEvaluationContextV1,
    ) -> None:
        ref = run.corpus_manifest_ref
        if ref != context.corpus_identity.provenance.ref:
            raise GvefCorpusDriftError(
                "run corpus_manifest_ref does not match bound corpus provenance.ref",
                field="corpus_manifest_ref",
            )
        entry = self._registry.load_entry(ref)
        if entry.manifest.model_dump(mode="json") != context.corpus_identity.model_dump(
            mode="json"
        ):
            raise GvefCorpusDriftError(
                "bound corpus_identity differs from registry manifest",
                field="corpus_identity",
            )
        identity = entry.validation_digest
        if self._bound_identity is None:
            self._bound_ref = ref
            self._bound_identity = identity
        elif self._bound_identity != identity or self._bound_ref != ref:
            raise GvefCorpusDriftError(
                "run attempted corpus switch after binding",
                field="corpus_manifest_ref",
            )
