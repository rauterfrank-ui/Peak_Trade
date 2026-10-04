"""GVEF BWP-0D protected semantic digest layer."""

from src.evaluation.golden_vectors.digest.comparator_v1 import ProtectedSemanticComparatorV1
from src.evaluation.golden_vectors.digest.errors import GvefProtectedDigestDriftError
from src.evaluation.golden_vectors.digest.protected_semantic_digest_layer_v1 import (
    BWP_ID,
    COMPONENT_ID,
    EXCLUDED_VOLATILE_FIELDS,
    ProtectedDigestComparisonReportV1,
    UNEXPECTED_REPROOF_CLASS,
    compare_protected_semantic_digests,
    enforce_ranking_universe_selection_separation,
    protected_semantic_digests_aggregate_hex,
    raise_if_fail_closed,
    reproof_class_for_verdict,
    resolve_reproof_class,
    semantic_payload_digest_hex,
)

__all__ = [
    "BWP_ID",
    "COMPONENT_ID",
    "EXCLUDED_VOLATILE_FIELDS",
    "GvefProtectedDigestDriftError",
    "ProtectedDigestComparisonReportV1",
    "ProtectedSemanticComparatorV1",
    "UNEXPECTED_REPROOF_CLASS",
    "compare_protected_semantic_digests",
    "enforce_ranking_universe_selection_separation",
    "protected_semantic_digests_aggregate_hex",
    "raise_if_fail_closed",
    "reproof_class_for_verdict",
    "resolve_reproof_class",
    "semantic_payload_digest_hex",
]
