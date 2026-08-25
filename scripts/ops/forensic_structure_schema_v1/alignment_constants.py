"""Bound constants for the additive binding-candidate alignment index.

Derived / non-authoritative only. Does not close residuals, bind occurrences,
adjudicate parentage, currentness, supersession, or winners.
"""

from __future__ import annotations

from scripts.ops.forensic_structure_schema_v1.constants import (
    EXPECTED_SIDECAR_SHA256,
    EXPECTED_SOURCE_SHA256,
)
from scripts.ops.forensic_structure_schema_v1.disposition_constants import (
    CROSS_RESIDUAL_PREREQUISITES,
    MUST_REMAIN_OPEN_RESIDUAL_IDS,
)

ALIGNMENT_LAYER_ID = "FORENSIC_STRUCTURE_SCHEMA_V1_BINDING_CANDIDATE_ALIGNMENT_INDEX_V1"
ALIGNMENT_TRANSFORMATION_VERSION = "1.0.0"
ALIGNMENT_GENERATOR_ID = (
    "FORENSIC_STRUCTURE_SCHEMA_V1_BINDING_CANDIDATE_ALIGNMENT_INDEX_GENERATOR_1.0.0"
)
ALIGNMENT_OUTPUT_ROLE = "DERIVED_NAVIGATION_OR_ANALYSIS_ONLY"
ALIGNMENT_AUTHORITY = "NONE"
REPO_ALIGNMENT_RELPATH = (
    "forensics/derived/FORENSIC_STRUCTURE_SCHEMA_V1_BINDING_CANDIDATE_ALIGNMENT_INDEX_V1"
)
EXTERNAL_ALIGNMENT_DATASET_DIR = (
    "/Users/frnkhrz/Documents/Peak_Trade/forensics/derived/"
    "FORENSIC_STRUCTURE_SCHEMA_V1_BINDING_CANDIDATE_ALIGNMENT_INDEX_V1"
)

BOUND_SOURCE_SHA256 = EXPECTED_SOURCE_SHA256
BOUND_SIDECAR_SHA256 = EXPECTED_SIDECAR_SHA256

EXPECTED_T4_RECORD_COUNT = 7175
EXPECTED_LAYER3_RELATION_COUNT = 122
EXPECTED_ENDPOINT_RECORD_COUNT = 244
EXPECTED_VIEW_COUNT = 12
EXPECTED_T4_CONTAINS_COUNT = 2613
EXPECTED_T4_LAYER3_MAPPED_PRESENT_COUNT = 87
EXPECTED_T4_LAYER3_MAPPED_NULL_COUNT = 7088
EXPECTED_OCCURRENCE_BINDING_PROVEN_COUNT = 0
EXPECTED_PROVEN_PARENTAGE_COUNT = 0
EXPECTED_WINNER_SELECTED_COUNT = 0

EXPECTED_A_L_DATASET_SHA256 = "2e489aeeb906acb05a53571ced0ecea54e0f877a70847d577c567ed5e790d575"
EXPECTED_RELATION_ENVELOPES_SHA256 = (
    "93a346fd77b11776ba352ce2f3bd7251a347e911de0a0f916e0cc840f8debb16"
)
EXPECTED_DATASET_CATALOG_SHA256 = "110cbe25d7df42d7cc20130ed2f17b6800bc52bb9a54f70be8bb2c89fa4b4bcd"
EXPECTED_DISPOSITION_LAYER_SHA256 = (
    "dd5de1ddbe4711065681162fded9d49b0b3fc2d9aca5c9762bd462827238b408"
)

A_L_CATALOG_RELPATH = "forensics/derived/FORENSIC_STRUCTURE_SCHEMA_V1_TRANSFORMATION_V1"
DISPOSITION_RELPATH = "forensics/derived/FORENSIC_STRUCTURE_SCHEMA_V1_BINDING_DISPOSITION_V1"

ALIGNMENT_SHARD_ORDER = (
    "t4_overlay_records.json",
    "layer3_relation_records.json",
    "endpoint_binding_candidate_records.json",
    "view_records.json",
    "cross_residual_evidence_edges.json",
    "non_identity_records.json",
)

GIT_TRACKED_SHARDS = (
    "layer3_relation_records.json",
    "endpoint_binding_candidate_records.json",
    "view_records.json",
    "cross_residual_evidence_edges.json",
    "non_identity_records.json",
)
EXTERNAL_ONLY_SHARDS = ("t4_overlay_records.json",)

EPISTEMIC_CLASSES = (
    "FACT_FROM_SOURCE",
    "RAW_EVIDENCE",
    "STRUCTURAL_DERIVATION",
    "PRIOR_ADJUDICATION_REFERENCE",
    "EXPLICIT_TEXT_RELATION",
    "NAVIGATION_ONLY",
    "INTERPRETATION",
    "HYPOTHESIS",
    "UNKNOWN",
    "ABSENT",
    "NULL",
    "OPEN",
    "CONFLICTED",
    "REJECTED",
    "PROVEN",
    "POSSIBLE",
    "UNRESOLVED",
)

EVIDENCE_CLASSES = (
    "ENCODING",
    "ENDPOINT_COUPLING",
    "GUARD",
    "ENCODING_OR_GUARD",
    "CROSS_RESIDUAL_PREREQUISITE_REFERENCE",
    "OWNER_GO_REJECTED_CLOSE_ORDER",
    "POSSIBLE_ONLY",
)

EDGE_EPISTEMIC_STATES = ("proven", "possible", "rejected")

CANDIDATE_STATES = (
    "UNRESOLVED",
    "POSSIBLE",
    "NAVIGATION_ONLY",
    "DO_NOT_BIND",
    "UNBOUND_NO_SUPPORTED_BINDING",
)

PARENTS_FIELD_STATES = ("ABSENT", "NULL", "PRESENT")

NON_IDENTITY_STATEMENTS = (
    ("NI-001", "TSV_DIRECTIONALITY", "SIDECAR_DECLARED_RELATION_TYPE"),
    ("NI-002", "SIDECAR_DECLARED_RELATION_TYPE", "LAYER3_RELATION_TYPE"),
    ("NI-003", "T4_CONTAINS", "WRAPPER_CONTAINS"),
    ("NI-004", "T4_ROW_OCCURRENCE", "ENDPOINT_OCCURRENCE_IDENTITY"),
    ("NI-005", "TOKEN_OCCURRENCE_ID", "LAYER1_OCCURRENCE_ID"),
    ("NI-006", "REL_ALIAS", "SOURCE_OCCURRENCE"),
    ("NI-007", "SRC_ALIAS", "SOURCE_OCCURRENCE"),
    ("NI-008", "VIEW_PARENT_HINT", "PROVEN_PARENTAGE"),
    ("NI-009", "PREFIX_EPOCH_SUCCEEDS", "CURRENTNESS"),
    ("NI-010", "PREFIX_EPOCH_SUCCEEDS", "SUPERSESSION"),
    ("NI-011", "MECHANICAL_ORDER", "DEPENDENCY"),
    ("NI-012", "LATER_RECORD", "WINNER"),
    ("NI-013", "ABSENT", "FALSE"),
    ("NI-014", "ABSENT", "NO_PARENT"),
    ("NI-015", "UNKNOWN", "FALSE"),
    ("NI-016", "OPEN", "UNPROVEN"),
    ("NI-017", "OPEN", "CLOSED"),
)

PROVEN_CROSS_RESIDUAL_EDGES = (
    (
        "XRE-001",
        "WRAPPER_CONTAINS.to_id",
        "begin_occurrence_id",
        "DR-002",
        "ENCODING",
        "proven",
        "STRUCTURAL_OR_GUARD_EVIDENCE",
    ),
    (
        "XRE-002",
        "STRUCTURAL_ORDERED_BEFORE.endpoint_aliases",
        "SW-R-004",
        "SW-R-004",
        "ENDPOINT_COUPLING",
        "proven",
        "STRUCTURAL_OR_GUARD_EVIDENCE",
    ),
    (
        "XRE-003",
        "TOKEN_OCCURRENCE_ID",
        "LAYER1_OCCURRENCE_ID",
        "SW-R-008",
        "GUARD",
        "proven",
        "STRUCTURAL_OR_GUARD_EVIDENCE",
    ),
    (
        "XRE-004",
        "LINE",
        "JOIN_KEY",
        "DR-003",
        "GUARD",
        "proven",
        "STRUCTURAL_OR_GUARD_EVIDENCE",
    ),
    (
        "XRE-005",
        "ABSENT",
        "NULL_AND_UNKNOWN",
        "DR-006",
        "ENCODING_OR_GUARD",
        "proven",
        "STRUCTURAL_OR_GUARD_EVIDENCE",
    ),
    (
        "XRE-006",
        "H1_PARTITION",
        "PARENTAGE",
        "SW-R-005",
        "GUARD",
        "proven",
        "STRUCTURAL_OR_GUARD_EVIDENCE",
    ),
)

POSSIBLE_CROSS_RESIDUAL_EDGES = (
    (
        "XRE-007",
        "T3_HEADING_VS_REGION",
        "SW-R-015",
        "SW-R-015",
        "POSSIBLE_ONLY",
        "possible",
        "POSSIBLE_ONLY_FUTURE_PARENTAGE_ATTEMPT",
    ),
)

REJECTED_CLOSE_ORDER_EDGES = (
    (
        "XRE-008",
        "SW-R-002",
        "SW-R-004",
        "SW-R-002",
        "OWNER_GO_REJECTED_CLOSE_ORDER",
        "rejected",
        "CIRCULAR_CROSS_TABLE",
    ),
    (
        "XRE-009",
        "SW-R-005",
        "MANDATORY_CLOSE_GATE",
        "SW-R-005",
        "OWNER_GO_REJECTED_CLOSE_ORDER",
        "rejected",
        "MANDATORY_CLOSE_GATE",
    ),
    (
        "XRE-010",
        "SW-R-008",
        "MANDATORY_CLOSE_GATE",
        "SW-R-008",
        "OWNER_GO_REJECTED_CLOSE_ORDER",
        "rejected",
        "MANDATORY_CLOSE_GATE",
    ),
    (
        "XRE-011",
        "SW-R-015",
        "MANDATORY_CLOSE_GATE",
        "SW-R-015",
        "OWNER_GO_REJECTED_CLOSE_ORDER",
        "rejected",
        "MANDATORY_CLOSE_GATE",
    ),
    (
        "XRE-012",
        "DR-002",
        "MANDATORY_CLOSE_GATE",
        "DR-002",
        "OWNER_GO_REJECTED_CLOSE_ORDER",
        "rejected",
        "MANDATORY_CLOSE_GATE",
    ),
    (
        "XRE-013",
        "DR-003",
        "MANDATORY_CLOSE_GATE",
        "DR-003",
        "OWNER_GO_REJECTED_CLOSE_ORDER",
        "rejected",
        "MANDATORY_CLOSE_GATE",
    ),
    (
        "XRE-014",
        "DR-006",
        "MANDATORY_CLOSE_GATE",
        "DR-006",
        "OWNER_GO_REJECTED_CLOSE_ORDER",
        "rejected",
        "MANDATORY_CLOSE_GATE",
    ),
    (
        "XRE-015",
        "PR_6063_HISTORICAL_CO_OCCURRENCE",
        "CLOSE_ORDER",
        "SW-R-002",
        "OWNER_GO_REJECTED_CLOSE_ORDER",
        "rejected",
        "HISTORICAL_CO_OCCURRENCE",
    ),
    (
        "XRE-016",
        "T4_CONTAINS",
        "WRAPPER_CONTAINS",
        "SW-R-002",
        "OWNER_GO_REJECTED_CLOSE_ORDER",
        "rejected",
        "FORBIDDEN_IDENTITY",
    ),
    (
        "XRE-017",
        "PREFIX_EPOCH_SUCCEEDS",
        "CURRENTNESS",
        "SW-R-002",
        "OWNER_GO_REJECTED_CLOSE_ORDER",
        "rejected",
        "FORBIDDEN_IDENTITY",
    ),
    (
        "XRE-018",
        "VIEW_PARENTS",
        "CHILD_SRC",
        "SW-R-009",
        "OWNER_GO_REJECTED_CLOSE_ORDER",
        "rejected",
        "FORBIDDEN_IDENTITY",
    ),
)

ALIGNMENT_GUARD_NAMES = (
    "forbid_missing_binding_as_negative_fact",
    "forbid_cross_residual_close_order",
    "forbid_t4_declared_equals_tsv_globally_unverified",
    "forbid_candidate_as_proven_occurrence",
    "forbid_documentary_parent_as_proven_parentage",
    "forbid_mechanical_order_as_dependency",
    "forbid_epoch_order_as_currentness",
    "forbid_epoch_order_as_supersession",
    "forbid_later_record_as_winner",
    "forbid_open_residual_status_transition",
    "forbid_authority_promotion",
    "forbid_source_mutation",
    "forbid_sidecar_mutation",
    "forbid_retained_input_rewrite",
    "forbid_disposition_input_rewrite",
    "forbid_unknown_to_false_collapse",
    "forbid_absent_to_no_parent_collapse",
    "forbid_duplicate_evidence_collapse",
    "forbid_provenance_collapse",
)

HISTORICAL_LOCATOR_SUBSTRINGS = (
    "/Users/frnkhrz/Desktop/",
    "/Users/frnkhrz/Downloads/",
)

OPEN_CLUSTER_RESIDUAL_IDS = ("SW-R-002", "SW-R-004", "SW-R-009")
ALIGNMENT_MUST_REMAIN_OPEN = MUST_REMAIN_OPEN_RESIDUAL_IDS
ALIGNMENT_CROSS_RESIDUAL_PREREQUISITES = CROSS_RESIDUAL_PREREQUISITES
