"""BWP-7 vector corpus registry — discovery, validation, indexing (read-only)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.evaluation.golden_vectors.contracts.enums import VectorClass
from src.evaluation.golden_vectors.contracts.models import CorpusManifestV1, VectorManifestV1
from src.evaluation.golden_vectors.contracts.validation import (
    parse_corpus_manifest_v1,
    parse_vector_manifest_v1,
)
from src.evaluation.golden_vectors.corpus.digest_v1 import (
    corpus_identity_digest_hex,
    vector_identity_digest_hex,
)
from src.evaluation.golden_vectors.corpus.errors import GvefCorpusDriftError

BWP_ID = "BWP-7"
PRIMARY_FAILURE_CLASS = "CORPUS_DRIFT"
REPROOF_CLASS = "WHOLE_SYSTEM_REPROOF"
CANONICAL_CORPUS_ROOT = "config/evaluation/golden_vectors"


@dataclass(frozen=True)
class CorpusRegistryEntryV1:
    corpus_ref: str
    manifest: CorpusManifestV1
    vectors: tuple[VectorManifestV1, ...]
    vector_digests: tuple[tuple[str, str], ...]
    validation_digest: str


@dataclass(frozen=True)
class CorpusValidationResultV1:
    corpus_ref: str
    corpus_identity_digest: str
    vector_identity_digests: tuple[tuple[str, str], ...]
    registry_order: tuple[str, ...]


class VectorCorpusRegistryV1:
    """Deterministic corpus discovery/validation. AUTHORITY=NONE."""

    def __init__(self, *, corpus_root: Path) -> None:
        self._corpus_root = corpus_root.resolve()

    @classmethod
    def default(cls) -> VectorCorpusRegistryV1:
        root = Path(CANONICAL_CORPUS_ROOT)
        return cls(corpus_root=root)

    def discover_corpus_refs(self) -> tuple[str, ...]:
        refs: list[str] = []
        if not self._corpus_root.is_dir():
            return tuple()
        for child in sorted(self._corpus_root.iterdir(), key=lambda p: p.name):
            if child.is_dir() and (child / "corpus_manifest.json").is_file():
                refs.append(f"{CANONICAL_CORPUS_ROOT}/{child.name}")
        return tuple(refs)

    def load_entry(self, corpus_ref: str) -> CorpusRegistryEntryV1:
        root = self._resolve_ref(corpus_ref)
        manifest_path = root / "corpus_manifest.json"
        manifest = parse_corpus_manifest_v1(json.loads(manifest_path.read_text(encoding="utf-8")))
        vectors_dir = root / "vectors"
        if not vectors_dir.is_dir():
            raise GvefCorpusDriftError("missing vectors directory", field="vectors")

        on_disk: dict[str, Path] = {}
        for path in sorted(vectors_dir.glob("*.json"), key=lambda p: p.name):
            on_disk[path.stem] = path

        if len(manifest.vector_ids) != len(set(manifest.vector_ids)):
            raise GvefCorpusDriftError("duplicate vector_id in corpus manifest", field="vector_ids")

        vectors: list[VectorManifestV1] = []
        digests: dict[str, str] = {}
        for vector_id in manifest.vector_ids:
            path = on_disk.pop(vector_id, None)
            if path is None:
                raise GvefCorpusDriftError(
                    f"missing vector manifest for {vector_id}",
                    field="vector_ids",
                )
            vector = parse_vector_manifest_v1(json.loads(path.read_text(encoding="utf-8")))
            if vector.vector_id != vector_id:
                raise GvefCorpusDriftError(
                    f"vector_id mismatch: file {vector_id} != manifest {vector.vector_id}",
                    field="vector_id",
                )
            digest = vector_identity_digest_hex(vector)
            vectors.append(vector)
            digests[vector_id] = digest

        if on_disk:
            extra = ", ".join(sorted(on_disk))
            raise GvefCorpusDriftError(
                f"unexpected vectors not listed in manifest: {extra}",
                field="vector_ids",
            )

        identity = corpus_identity_digest_hex(manifest, vector_digests_by_id=digests)
        if manifest.corpus_digest != identity:
            raise GvefCorpusDriftError(
                "corpus_digest mismatch",
                field="corpus_digest",
            )

        digest_pairs = tuple((vid, digests[vid]) for vid in manifest.vector_ids)
        validation_digest = identity
        return CorpusRegistryEntryV1(
            corpus_ref=corpus_ref,
            manifest=manifest,
            vectors=tuple(vectors),
            vector_digests=digest_pairs,
            validation_digest=validation_digest,
        )

    def validate(self, corpus_ref: str) -> CorpusValidationResultV1:
        entry = self.load_entry(corpus_ref)
        return CorpusValidationResultV1(
            corpus_ref=entry.corpus_ref,
            corpus_identity_digest=entry.validation_digest,
            vector_identity_digests=entry.vector_digests,
            registry_order=tuple(v.vector_id for v in entry.vectors),
        )

    def validate_in_memory(
        self,
        *,
        manifest: CorpusManifestV1,
        vectors: dict[str, VectorManifestV1],
    ) -> CorpusValidationResultV1:
        """Validate bound snapshot (tests / run binding)."""
        if len(manifest.vector_ids) != len(set(manifest.vector_ids)):
            raise GvefCorpusDriftError("duplicate vector_id", field="vector_ids")
        digests: dict[str, str] = {}
        ordered: list[VectorManifestV1] = []
        for vector_id in manifest.vector_ids:
            vector = vectors.get(vector_id)
            if vector is None:
                raise GvefCorpusDriftError(f"missing vector {vector_id}", field="vector_ids")
            if vector.vector_id != vector_id:
                raise GvefCorpusDriftError("vector_id mismatch", field="vector_id")
            digests[vector_id] = vector_identity_digest_hex(vector)
            ordered.append(vector)
        extra = set(vectors) - set(manifest.vector_ids)
        if extra:
            raise GvefCorpusDriftError(
                f"unexpected vectors: {sorted(extra)}",
                field="vector_ids",
            )
        identity = corpus_identity_digest_hex(manifest, vector_digests_by_id=digests)
        if manifest.corpus_digest != identity:
            raise GvefCorpusDriftError("corpus_digest mismatch", field="corpus_digest")
        return CorpusValidationResultV1(
            corpus_ref="in_memory",
            corpus_identity_digest=identity,
            vector_identity_digests=tuple((v.vector_id, digests[v.vector_id]) for v in ordered),
            registry_order=tuple(v.vector_id for v in ordered),
        )

    def assert_vector_class_known(self, vector_class: str) -> None:
        try:
            VectorClass(vector_class)
        except ValueError as exc:
            raise GvefCorpusDriftError(
                f"unknown vector class: {vector_class}",
                field="vector_class",
            ) from exc

    def _resolve_ref(self, corpus_ref: str) -> Path:
        ref_path = Path(corpus_ref)
        if ref_path.is_absolute():
            root = ref_path
        else:
            root = (Path.cwd() / ref_path).resolve()
        if not root.is_dir():
            raise GvefCorpusDriftError(f"corpus root not found: {corpus_ref}", field="corpus_ref")
        return root


def load_json_fixture(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))
