"""GHV regression corpus provenance contract — disambiguate lab JSONL vs E2E reproof."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

PACKAGE_MARKER = "GHV_REGRESSION_CORPUS_PROVENANCE_V1=true"

GHV_E2E_PRODUCTIVE_REPROOF_OWNER = (
    "evidence/research/full_core_golden_happy_vector_e2e_v1/run_full_core_ghv_e2e_v1.py"
)
GHV_E2E_EXPECTED_FLIGHT_COUNT = 425
GHV_E2E_EXPECTED_CYCLE_COUNT = 10202

LAB_CORPUS_PRODUCER = (
    "evidence/research/intelligent_universe_multi_future_ghv_dynamic_scope_lab_v1/run_lab_v1.py"
)
LAB_FULL_CYCLE_LINES = 9360
LAB_SMOKE_CYCLE_LINES = 384
LAB_CYCLES_PER_FLIGHT = 24
LAB_FULL_FLIGHT_COUNT = LAB_FULL_CYCLE_LINES // LAB_CYCLES_PER_FLIGHT
LAB_SMOKE_FLIGHT_COUNT = LAB_SMOKE_CYCLE_LINES // LAB_CYCLES_PER_FLIGHT

CANONICAL_ARTIFACT_NAME = "ghv_cycle_observations.jsonl"


@dataclass(frozen=True)
class GhvCorpusIdentityV1:
    corpus_id: str
    producer: str
    expected_line_count: int
    expected_flight_count: int
    semantic_role: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "corpus_id": self.corpus_id,
            "producer": self.producer,
            "artifact_name": CANONICAL_ARTIFACT_NAME,
            "expected_line_count": self.expected_line_count,
            "expected_flight_count": self.expected_flight_count,
            "semantic_role": self.semantic_role,
        }


def canonical_ghv_corpus_catalog_v1() -> tuple[GhvCorpusIdentityV1, ...]:
    return (
        GhvCorpusIdentityV1(
            corpus_id="GHV_E2E_PRODUCTIVE_PRESERVATION_REPROOF",
            producer=GHV_E2E_PRODUCTIVE_REPROOF_OWNER,
            expected_line_count=GHV_E2E_EXPECTED_CYCLE_COUNT,
            expected_flight_count=GHV_E2E_EXPECTED_FLIGHT_COUNT,
            semantic_role="post_gvef_preservation_metrics_authority",
        ),
        GhvCorpusIdentityV1(
            corpus_id="LAB_SCOPE_DYNAMIC_FULL",
            producer=LAB_CORPUS_PRODUCER,
            expected_line_count=LAB_FULL_CYCLE_LINES,
            expected_flight_count=LAB_FULL_FLIGHT_COUNT,
            semantic_role="research_scope_lab_generated_artifact",
        ),
        GhvCorpusIdentityV1(
            corpus_id="LAB_SCOPE_DYNAMIC_SMOKE",
            producer=LAB_CORPUS_PRODUCER,
            expected_line_count=LAB_SMOKE_CYCLE_LINES,
            expected_flight_count=LAB_SMOKE_FLIGHT_COUNT,
            semantic_role="research_smoke_subset_not_preservation_authority",
        ),
    )


def classify_corpus_line_count_v1(*, line_count: int) -> str:
    if line_count == GHV_E2E_EXPECTED_CYCLE_COUNT:
        return "MATCHES_E2E_CYCLE_COUNT"
    if line_count == LAB_FULL_CYCLE_LINES:
        return "MATCHES_LAB_FULL"
    if line_count == LAB_SMOKE_CYCLE_LINES:
        return "MATCHES_LAB_SMOKE_SUBSET"
    return "UNKNOWN_LINE_COUNT"
