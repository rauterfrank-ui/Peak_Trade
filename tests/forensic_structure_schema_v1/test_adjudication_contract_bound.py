"""Bound-input immutability checks for the adjudication contract."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from scripts.ops.forensic_structure_schema_v1.adjudication_constants import (
    BOUND_SIDECAR_SHA256,
    BOUND_SOURCE_SHA256,
    EXPECTED_T4_SHARD_SHA256,
)
from scripts.ops.forensic_structure_schema_v1.adjudication_persist import (
    persist_adjudication_contract,
)
from scripts.ops.forensic_structure_schema_v1.bound_inputs import (
    BOUND_SIDECAR,
    BOUND_SOURCE,
    bound_inputs_available,
)
from scripts.ops.forensic_structure_schema_v1.serialization import dumps_canonical_bytes


pytestmark = pytest.mark.skipif(not bound_inputs_available(), reason="bound forensic inputs absent")

EXTERNAL_T4 = Path(
    "/Users/frnkhrz/Documents/Peak_Trade/forensics/derived/"
    "FORENSIC_STRUCTURE_SCHEMA_V1_BINDING_CANDIDATE_ALIGNMENT_INDEX_V1/"
    "blobs/t4_overlay_records.json"
)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def test_bound_hashes_and_persist_do_not_mutate_source_or_sidecar(tmp_path: Path) -> None:
    before_src = _sha256_file(BOUND_SOURCE)
    before_sid = _sha256_file(BOUND_SIDECAR)
    assert before_src == BOUND_SOURCE_SHA256
    assert before_sid == BOUND_SIDECAR_SHA256
    if EXTERNAL_T4.is_file():
        assert _sha256_file(EXTERNAL_T4) == EXPECTED_T4_SHARD_SHA256
    first = persist_adjudication_contract(reports_dir=tmp_path / "run1")
    second = persist_adjudication_contract(reports_dir=tmp_path / "run2")
    assert dumps_canonical_bytes(first.contract.to_canonical()) == dumps_canonical_bytes(
        second.contract.to_canonical()
    )
    assert first.shard_sha256s == second.shard_sha256s
    assert _sha256_file(BOUND_SOURCE) == before_src
    assert _sha256_file(BOUND_SIDECAR) == before_sid
    assert first.immutability_report["source_mutated"] is False
    assert first.immutability_report["sidecar_mutated"] is False
