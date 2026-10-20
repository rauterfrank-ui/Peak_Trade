"""Guardian domain scope manifest constants. AUTHORITY=NONE."""

from __future__ import annotations

from typing import Final

SCHEMA_ID: Final = "GUARDIAN_DOMAIN_SCOPE_MANIFEST_V1"
SCHEMA_VERSION: Final = 1

STATUS_MANIFEST_RECORDED: Final = "MANIFEST_RECORDED"
STATUS_INVALID_MANIFEST: Final = "INVALID_MANIFEST"
STATUS_BINDER_RESULT_REJECTED: Final = "BINDER_RESULT_REJECTED"

MANIFEST_FIELDS: Final = (
    "manifest_id",
    "declared_commit_sha",
    "declared_tree_sha",
    "provenance",
    "scope",
    "tool_slots",
)

TOOL_SLOT_NAMES: Final = (
    "DOMAIN_GHV",
    "DOMAIN_CURRENT_CAUSAL_GRAPH",
    "DOMAIN_GHOSV",
)

TOOL_SLOT_STATUSES: Final = frozenset(
    {
        "ABSENT",
        "PRESENT_UNBOUND",
        "PRESENT_PIN_MISMATCH",
    }
)

FORBIDDEN_CLAIM_KEYS: Final = frozenset(
    {
        "authority",
        "trading_authority",
        "safety_authority",
        "execution_authority",
        "guardian_identity",
        "guardian_ratified",
        "guardian_ratification",
        "current_proven",
        "coverage_proof",
    }
)

FORBIDDEN_OUTPUT_KEYS: Final = frozenset(
    {
        "overall_pass",
        "guardian_pass",
        "universe_pass",
        "live_authorized",
    }
)
