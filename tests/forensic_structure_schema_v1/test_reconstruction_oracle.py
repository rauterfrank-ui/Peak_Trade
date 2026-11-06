"""Layer-1 tiling reconstruction oracle tests. Bound Source is byte authority."""

from __future__ import annotations

import hashlib
from dataclasses import replace

import pytest

from scripts.ops.forensic_structure_schema_v1.bound_inputs import (
    bound_inputs_available,
    run_bound_transformer,
)
from scripts.ops.forensic_structure_schema_v1.constants import (
    EXPECTED_SOURCE_BYTES,
    EXPECTED_SOURCE_SHA256,
)
from scripts.ops.forensic_structure_schema_v1.exceptions import (
    TransformationContractViolation,
)
from scripts.ops.forensic_structure_schema_v1.models import Layer1Occurrence
from scripts.ops.forensic_structure_schema_v1.reconstruction import (
    assert_layer1_reconstruction,
    evaluate_layer1_reconstruction,
)


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _span(source: bytes, seq: int, start: int, end: int) -> Layer1Occurrence:
    return Layer1Occurrence(
        occurrence_id=f"occ-{seq}",
        source_sequence=seq,
        byte_start=start,
        byte_end=end,
        line_start=seq,
        line_end=seq,
        content_hash_sha256=_sha(source[start:end]),
        mechanical_type="NARRATIVE_OR_OTHER",
    )


def test_synthetic_tiling_reconstructs_exact_bytes() -> None:
    source = b"abcdef"
    spans = [_span(source, 1, 0, 2), _span(source, 2, 2, 6)]
    report = assert_layer1_reconstruction(
        source_bytes=source,
        spans=spans,
        expected_source_sha256=_sha(source),
        expected_source_bytes=len(source),
        reconstruction_uses_bound_source=False,
    )
    assert report.passed is True
    assert report.gaps == 0
    assert report.overlaps == 0
    assert report.hash_mismatches == 0
    assert report.dataset_only_reconstruction_claim is False
    assert report.sha_match is True


def test_rejects_gap() -> None:
    source = b"abcdef"
    spans = [_span(source, 1, 0, 2), _span(source, 2, 3, 6)]
    with pytest.raises(TransformationContractViolation) as exc:
        assert_layer1_reconstruction(
            source_bytes=source,
            spans=spans,
            expected_source_sha256=_sha(source),
            expected_source_bytes=len(source),
            reconstruction_uses_bound_source=False,
        )
    assert exc.value.rule == "LAYER1_GAP"


def test_rejects_overlap() -> None:
    source = b"abcdef"
    spans = [_span(source, 1, 0, 3), _span(source, 2, 2, 6)]
    with pytest.raises(TransformationContractViolation) as exc:
        assert_layer1_reconstruction(
            source_bytes=source,
            spans=spans,
            expected_source_sha256=_sha(source),
            expected_source_bytes=len(source),
            reconstruction_uses_bound_source=False,
        )
    assert exc.value.rule == "LAYER1_OVERLAP"


def test_rejects_span_hash_mismatch() -> None:
    source = b"abcdef"
    bad = replace(_span(source, 1, 0, 3), content_hash_sha256="0" * 64)
    spans = [bad, _span(source, 2, 3, 6)]
    with pytest.raises(TransformationContractViolation) as exc:
        assert_layer1_reconstruction(
            source_bytes=source,
            spans=spans,
            expected_source_sha256=_sha(source),
            expected_source_bytes=len(source),
            reconstruction_uses_bound_source=False,
        )
    assert exc.value.rule == "LAYER1_SPAN_HASH_MISMATCH"


def test_rejects_wrong_source_sequence_order() -> None:
    source = b"AB"
    swapped = [
        _span(source, 1, 1, 2),
        _span(source, 2, 0, 1),
    ]
    with pytest.raises(TransformationContractViolation) as exc:
        assert_layer1_reconstruction(
            source_bytes=source,
            spans=swapped,
            expected_source_sha256=_sha(source),
            expected_source_bytes=len(source),
            reconstruction_uses_bound_source=False,
        )
    assert exc.value.rule in {
        "LAYER1_GAP",
        "LAYER1_RECONSTRUCTED_BYTE_MISMATCH",
        "LAYER1_RECONSTRUCTED_SHA_MISMATCH",
    }


def test_rejects_wrong_terminal_byte_count() -> None:
    source = b"abcdef"
    spans = [_span(source, 1, 0, 2), _span(source, 2, 2, 5)]
    with pytest.raises(TransformationContractViolation) as exc:
        assert_layer1_reconstruction(
            source_bytes=source,
            spans=spans,
            expected_source_sha256=_sha(source),
            expected_source_bytes=len(source),
            reconstruction_uses_bound_source=False,
        )
    assert exc.value.rule in {"LAYER1_LENGTH_MISMATCH", "LAYER1_GAP"}


def test_rejects_duplicate_and_missing_sequence() -> None:
    source = b"ab"
    dup = [_span(source, 1, 0, 1), replace(_span(source, 2, 1, 2), source_sequence=1)]
    missing = [_span(source, 1, 0, 1), replace(_span(source, 2, 1, 2), source_sequence=3)]
    with pytest.raises(TransformationContractViolation) as exc:
        assert_layer1_reconstruction(
            source_bytes=source,
            spans=dup,
            expected_source_sha256=_sha(source),
            expected_source_bytes=len(source),
            reconstruction_uses_bound_source=False,
        )
    assert exc.value.rule == "LAYER1_DUPLICATE_SEQUENCE"
    with pytest.raises(TransformationContractViolation) as exc:
        assert_layer1_reconstruction(
            source_bytes=source,
            spans=missing,
            expected_source_sha256=_sha(source),
            expected_source_bytes=len(source),
            reconstruction_uses_bound_source=False,
        )
    assert exc.value.rule == "LAYER1_MISSING_SEQUENCE"


@pytest.mark.skipif(not bound_inputs_available(), reason="bound forensic inputs absent")
def test_bound_corpus_layer1_reconstructs_source() -> None:
    result = run_bound_transformer()
    report = assert_layer1_reconstruction(
        source_bytes=result.state.source_bytes,
        spans=result.state.layer1_ordered,
        reconstruction_uses_bound_source=True,
    )
    assert report.passed is True
    assert report.reconstruction_uses_bound_source is True
    assert report.dataset_only_reconstruction_claim is False
    assert report.gaps == 0
    assert report.overlaps == 0
    assert report.hash_mismatches == 0
    assert report.reconstructed_source_sha256 == EXPECTED_SOURCE_SHA256
    assert report.reconstructed_bytes == EXPECTED_SOURCE_BYTES
    assert result.state.reconstruction_report is not None
    assert result.state.reconstruction_report["sha_match"] is True
    evaluated = evaluate_layer1_reconstruction(
        source_bytes=result.state.source_bytes,
        spans=result.state.layer1_ordered,
        reconstruction_uses_bound_source=True,
    )
    assert evaluated.passed is True
