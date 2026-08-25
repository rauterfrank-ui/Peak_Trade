"""Bound-source Layer-1 tiling reconstruction oracle.

This proves structural reconstruction against the bound Source bytes.
It does not claim that the retained dataset independently contains the
Source. Dataset-only reconstruction remains false.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any, Sequence

from scripts.ops.forensic_structure_schema_v1.constants import (
    EXPECTED_SOURCE_BYTES,
    EXPECTED_SOURCE_SHA256,
)
from scripts.ops.forensic_structure_schema_v1.exceptions import (
    TransformationContractViolation,
)


@dataclass(frozen=True)
class ReconstructionReport:
    passed: bool
    reconstructed_source_sha256: str
    expected_source_sha256: str
    reconstructed_bytes: int
    expected_source_bytes: int
    layer1_count: int
    gaps: int
    overlaps: int
    invalid_ranges: int
    duplicate_sequences: int
    missing_sequences: int
    hash_mismatches: int
    length_mismatch: bool
    reconstructed_byte_mismatch: bool
    sha_match: bool
    reconstruction_uses_bound_source: bool
    dataset_only_reconstruction_claim: bool
    violation_rule: str
    detail: str

    def to_canonical(self) -> dict[str, Any]:
        return {
            "role": "BOUND_SOURCE_LAYER1_TILING_RECONSTRUCTION_ORACLE",
            "authority": "NONE",
            "status": "PASS" if self.passed else "FAIL",
            "passed": self.passed,
            "reconstructed_source_sha256": self.reconstructed_source_sha256,
            "expected_source_sha256": self.expected_source_sha256,
            "sha_match": self.sha_match,
            "reconstructed_bytes": self.reconstructed_bytes,
            "expected_source_bytes": self.expected_source_bytes,
            "layer1_count": self.layer1_count,
            "gaps": self.gaps,
            "overlaps": self.overlaps,
            "invalid_ranges": self.invalid_ranges,
            "duplicate_sequences": self.duplicate_sequences,
            "missing_sequences": self.missing_sequences,
            "hash_mismatches": self.hash_mismatches,
            "length_mismatch": self.length_mismatch,
            "reconstructed_byte_mismatch": self.reconstructed_byte_mismatch,
            "reconstruction_uses_bound_source": self.reconstruction_uses_bound_source,
            "dataset_only_reconstruction_claim": self.dataset_only_reconstruction_claim,
            "retained_dataset_contains_source_bytes": False,
            "violation_rule": self.violation_rule,
            "detail": self.detail,
        }


def _sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _span_fields(span: Any) -> tuple[str, int, int, int, str]:
    return (
        str(span.occurrence_id),
        int(span.source_sequence),
        int(span.byte_start),
        int(span.byte_end),
        str(span.content_hash_sha256),
    )


def evaluate_layer1_reconstruction(
    *,
    source_bytes: bytes,
    spans: Sequence[Any],
    expected_source_sha256: str = EXPECTED_SOURCE_SHA256,
    expected_source_bytes: int = EXPECTED_SOURCE_BYTES,
    reconstruction_uses_bound_source: bool,
) -> ReconstructionReport:
    """Evaluate tiling. Source bytes are the materialization authority."""
    gaps = 0
    overlaps = 0
    invalid_ranges = 0
    hash_mismatches = 0
    detail = "ok"
    rule = ""
    n = len(spans)
    sequences = [int(span.source_sequence) for span in spans]
    sequence_set = set(sequences)
    duplicate_sequences = n - len(sequence_set)
    expected_sequences = set(range(1, n + 1))
    missing_sequences = len(expected_sequences.difference(sequence_set))

    if duplicate_sequences:
        rule = "LAYER1_DUPLICATE_SEQUENCE"
        detail = f"duplicate source_sequence count={duplicate_sequences}"
    elif missing_sequences:
        rule = "LAYER1_MISSING_SEQUENCE"
        detail = f"missing source_sequence count={missing_sequences}"

    ordered = sorted(spans, key=lambda span: int(span.source_sequence))
    reconstructed = bytearray()
    prev_end = 0
    if not rule:
        for index, span in enumerate(ordered):
            _occ, seq, start, end, expected_hash = _span_fields(span)
            if seq != index + 1 and not rule:
                rule = "LAYER1_MISSING_SEQUENCE"
                detail = f"source_sequence hole at ordered index {index}: {seq}"
            if start < 0 or end < start or end > len(source_bytes):
                invalid_ranges += 1
                if not rule:
                    rule = "LAYER1_INVALID_RANGE"
                    detail = f"invalid range [{start},{end}) on {_occ}"
            if index == 0:
                if start != 0 and not rule:
                    rule = "LAYER1_GAP"
                    detail = f"coverage does not start at 0: start={start}"
                    gaps += 1
            else:
                if prev_end < start:
                    gaps += 1
                    if not rule:
                        rule = "LAYER1_GAP"
                        detail = f"gap between {prev_end} and {start}"
                elif prev_end > start:
                    overlaps += 1
                    if not rule:
                        rule = "LAYER1_OVERLAP"
                        detail = f"overlap between {prev_end} and {start}"
            slice_bytes = source_bytes[start:end]
            observed_hash = _sha256_hex(slice_bytes)
            if observed_hash != expected_hash:
                hash_mismatches += 1
                if not rule:
                    rule = "LAYER1_SPAN_HASH_MISMATCH"
                    detail = f"span hash mismatch on {_occ}"
            reconstructed.extend(slice_bytes)
            prev_end = end
        if ordered and prev_end != expected_source_bytes and not rule:
            rule = "LAYER1_LENGTH_MISMATCH"
            detail = f"terminal byte {prev_end} != {expected_source_bytes}"

    reconstructed_bytes_obj = bytes(reconstructed)
    reconstructed_len = len(reconstructed_bytes_obj)
    length_mismatch = reconstructed_len != expected_source_bytes
    if length_mismatch and not rule:
        rule = "LAYER1_LENGTH_MISMATCH"
        detail = f"reconstructed length {reconstructed_len} != {expected_source_bytes}"
    byte_mismatch = reconstructed_bytes_obj != source_bytes
    if byte_mismatch and not rule:
        rule = "LAYER1_RECONSTRUCTED_BYTE_MISMATCH"
        detail = "concat(source[start:end]) != source_bytes"
    reconstructed_sha = _sha256_hex(reconstructed_bytes_obj)
    sha_match = reconstructed_sha == expected_source_sha256
    if not sha_match and not rule:
        rule = "LAYER1_RECONSTRUCTED_SHA_MISMATCH"
        detail = f"reconstructed sha {reconstructed_sha} != {expected_source_sha256}"

    passed = (
        not rule
        and gaps == 0
        and overlaps == 0
        and invalid_ranges == 0
        and duplicate_sequences == 0
        and missing_sequences == 0
        and hash_mismatches == 0
        and not length_mismatch
        and not byte_mismatch
        and sha_match
        and reconstructed_len == len(source_bytes) == expected_source_bytes
    )
    return ReconstructionReport(
        passed=passed,
        reconstructed_source_sha256=reconstructed_sha,
        expected_source_sha256=expected_source_sha256,
        reconstructed_bytes=reconstructed_len,
        expected_source_bytes=expected_source_bytes,
        layer1_count=n,
        gaps=gaps,
        overlaps=overlaps,
        invalid_ranges=invalid_ranges,
        duplicate_sequences=duplicate_sequences,
        missing_sequences=missing_sequences,
        hash_mismatches=hash_mismatches,
        length_mismatch=length_mismatch,
        reconstructed_byte_mismatch=byte_mismatch,
        sha_match=sha_match,
        reconstruction_uses_bound_source=reconstruction_uses_bound_source,
        dataset_only_reconstruction_claim=False,
        violation_rule=rule,
        detail=detail,
    )


def assert_layer1_reconstruction(
    *,
    source_bytes: bytes,
    spans: Sequence[Any],
    expected_source_sha256: str = EXPECTED_SOURCE_SHA256,
    expected_source_bytes: int = EXPECTED_SOURCE_BYTES,
    reconstruction_uses_bound_source: bool,
) -> ReconstructionReport:
    report = evaluate_layer1_reconstruction(
        source_bytes=source_bytes,
        spans=spans,
        expected_source_sha256=expected_source_sha256,
        expected_source_bytes=expected_source_bytes,
        reconstruction_uses_bound_source=reconstruction_uses_bound_source,
    )
    if not report.passed:
        raise TransformationContractViolation(
            report.violation_rule or "LAYER1_RECONSTRUCTION_FAILURE",
            report.detail,
        )
    return report
