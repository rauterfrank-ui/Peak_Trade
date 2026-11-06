"""Tests for GHV regression corpus provenance contract."""

from __future__ import annotations

from src.ops.ghv_regression_corpus_provenance_v1 import (
    GHV_E2E_EXPECTED_FLIGHT_COUNT,
    LAB_FULL_CYCLE_LINES,
    LAB_SMOKE_CYCLE_LINES,
    canonical_ghv_corpus_catalog_v1,
    classify_corpus_line_count_v1,
)


def test_catalog_has_three_distinct_corpus_identities() -> None:
    catalog = canonical_ghv_corpus_catalog_v1()
    ids = {c.corpus_id for c in catalog}
    assert len(ids) == 3
    assert "GHV_E2E_PRODUCTIVE_PRESERVATION_REPROOF" in ids


def test_smoke_line_count_not_equal_to_e2e_or_full_lab() -> None:
    assert LAB_SMOKE_CYCLE_LINES != LAB_FULL_CYCLE_LINES
    assert LAB_SMOKE_CYCLE_LINES != 10202
    assert GHV_E2E_EXPECTED_FLIGHT_COUNT == 425


def test_classifier_rejects_ambiguous_unknown_count() -> None:
    assert classify_corpus_line_count_v1(line_count=1) == "UNKNOWN_LINE_COUNT"
