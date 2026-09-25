"""Peak_Trade System Atlas constants. ATLAS_AUTHORITY=NONE."""

from __future__ import annotations

ATLAS_AUTHORITY = "NONE"
ATLAS_ROLE = "EVIDENCE_BOUND_SYSTEM_TOPOLOGY_AND_NAVIGATION"
PACKAGE_MARKER = "SYSTEM_ATLAS_V1=true"
SCHEMA_VERSION = "system_atlas.v1"
GENERATOR_MODULE = "scripts/ops/generate_system_atlas_v1.py"
ATLAS_RELATIVE_ROOT = "docs/system_atlas"
GENERATED_MARKER = "GENERATED/DO_NOT_EDIT"
RECONCILIATION_AUTHORITY = "NONE"
RECONCILIATION_ROLE = "GOVERNANCE_AND_EVIDENCE_NOT_RUNTIME"
RECONCILIATION_RELATIVE_ROOT = "docs/system_atlas/reconciliation"
RECONCILIATION_SCHEMA_VERSION = "peak_trade.reconciliation_governance.v1"

EPISTEMIC_CLASSES = frozenset(
    {
        "CANONICAL_AUTHORITY",
        "FORENSIC_RAW",
        "ADJUDICATED",
        "HISTORICAL",
        "NAVIGATION_ONLY",
        "INTERPRETATION",
        "HYPOTHESIS",
        "OPEN",
        "CONTRADICTED",
    }
)

ENTITY_KINDS = frozenset(
    {
        "SYSTEM",
        "SUBSYSTEM",
        "GENERATION",
        "FUNCTIONAL_CORE",
        "FAMILY",
        "CHILD",
        "SSOT_CHILD",
        "MMR",
        "CAPABILITY",
        "POLICY",
        "OWNER_DECISION",
        "INVARIANT",
        "CONTRACT",
        "DATA_CONTRACT",
        "RUNTIME_COMPONENT",
        "RUNNER",
        "HOST",
        "ADAPTER",
        "TRANSPORT",
        "OBSERVER",
        "SELECTOR",
        "UNIVERSE",
        "BINDER",
        "GATE",
        "GUARD",
        "PERMIT",
        "RECEIPT",
        "EVIDENCE_ARTIFACT",
        "CONFIG",
        "SCHEMA",
        "MODEL",
        "STATE_FIELD",
        "REGISTRY",
        "EXPERIMENT",
        "STRATEGY",
        "PORTFOLIO",
        "RISK_COMPONENT",
        "EXECUTION_COMPONENT",
        "VENUE",
        "VENUE_ENDPOINT",
        "VENUE_FIELD",
        "VENUE_ACCOUNT_SETTING",
        "VENUE_PRODUCT_TYPE",
        "AUTH_PRIMITIVE",
        "TEST",
        "SCRIPT",
        "RUNBOOK",
        "FORENSIC_REFERENCE",
        "NAVIGATION_INDEX",
        "OKX_FEATURE",
        "OKX_RESPONSE_SHAPE",
        "OKX_HOST",
        "TERM",
        "DOD",
        "ACRONYM",
        "SCHEMA",
        "PREDICATE",
        "OBLIGATION",
        "MANIFEST",
        "CENSUS",
        "PHASE",
        "LINEAGE_VALUE",
    }
)

STRUCTURAL_RELATION_TYPES = frozenset(
    {
        "CONTAINS",
        "HAS_FUNCTIONAL_CORE",
        "HAS_FAMILY",
        "HAS_CHILD",
        "HAS_SSOT_CHILD",
        "HAS_MMR",
        "HAS_DOD",
        "USES_SCHEMA",
        "DEFINES_SHAPE_OF",
        "HAS_CAPABILITY",
        "IMPLEMENTS",
        "SATISFIES",
        "GOVERNED_BY",
        "SUPERSEDES",
        "RESTORES",
        "DERIVED_FROM",
        "REFERENCE_OF",
        "NAVIGATES_TO",
        "DEPENDS_ON",
        "REQUIRES",
        "OPTIONALLY_USES",
        "CONFIGURED_BY",
        "TESTED_BY",
        "INTRODUCED_BY",
        "MODIFIED_BY",
        "SUPERSEDED_BY",
        "RESTORED_BY",
    }
)

RUNTIME_RELATION_TYPES = frozenset(
    {
        "CALLS",
        "CONSUMES",
        "PRODUCES",
        "BINDS",
        "READS",
        "WRITES",
        "VALIDATES",
        "SELECTS",
        "FILTERS",
        "NORMALIZES",
        "REJECTS",
        "OBSERVES",
        "SERIALIZES",
        "DESERIALIZES",
        "SIGNS",
        "SENDS",
        "RECEIVES",
        "PERSISTS",
        "LOADS",
        "EMITS",
        "GATES",
        "AUTHORIZES",
        "DENIES",
        "READS_BACK",
        "COMPARES",
        "DERIVES",
        "INJECTS",
        "FETCHES",
        "TRANSFORMS",
        "RANKS",
        "RECONCILES",
    }
)

AUTHORITY_RELATION_TYPES = frozenset(
    {
        "BINDS",
        "GOVERNS",
        "CLAIMS_TO_IMPLEMENT",
        "EXERCISES",
        "SUPPORTS",
        "RESOLVES",
        "NAVIGATES_TO",
        "DOCUMENTS",
        "DOES_NOT_AUTHORIZE",
    }
)

GRAPHS = frozenset({"structural", "runtime", "authority_evidence"})

CANONICAL_AUTHORITY_PATH_PREFIXES = (
    "docs/runbooks/canonical/",
    "docs/ops/specs/MASTER_V2_CAPABILITY_",
)

ATLAS_PATH_PREFIXES = ("docs/system_atlas/",)

GENERATED_VIEW_NAMES = (
    "SYSTEM_ATLAS.md",
    "STRUCTURAL_GRAPH.md",
    "RUNTIME_GRAPH.md",
    "AUTHORITY_GRAPH.md",
    "OKX_INTEGRATION_MAP.md",
    "OKX_FEATURE_MATRIX.md",
    "OKX_CHRONOLOGY.md",
    "MASTER_V2_DOUBLE_PLAY_MAP.md",
    "FAMILY_CHILD_MMR_MAP.md",
    "FULL_DEPENDENCY_GRAPH.md",
    "DATA_LINEAGE_MAP.md",
    "CONFIGURATION_WIRING.md",
    "ENTRYPOINT_RUNTIME_TRACES.md",
    "ORPHAN_AND_WIRING_GAPS.md",
    "SAFETY_GOVERNANCE_MAP.md",
    "DATA_CONTRACT_MAP.md",
    "PROVENANCE_TIMELINE.md",
    "BUILD_GUIDANCE.md",
    "CONTRADICTION_REGISTER.md",
    "PROJECT_TERMINOLOGY.md",
    "ACRONYM_REGISTER.md",
    "DOD_MAP.md",
    "SCHEMA_MAP.md",
    "TERMINOLOGY_COLLISIONS.md",
    "COVERAGE_REPORT.md",
    "ATLAS_CHANGE_IMPACT.md",
)

CURRENT_STATUS_VALUES = frozenset(
    {
        "CURRENT_CANONICAL",
        "CURRENT_NONCANONICAL",
        "HISTORICAL_ONLY",
        "SUPERSEDED",
        "REMOVED",
        "REJECTED",
        "EXPERIMENTAL",
        "FORENSIC_REFERENCE_ONLY",
        "OPEN",
        "PARTIALLY_RESTORED",
        "RESTORATION_TARGET",
        "CURRENT_IMPLEMENTATION_WITHOUT_PROVEN_CANONICAL_SUPPORT",
        "STILL_CURRENT_AND_CANONICALLY_SUPPORTED",
    }
)
