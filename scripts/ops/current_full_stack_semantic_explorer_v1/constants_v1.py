"""Explorer limits and closed vocabularies. AUTHORITY=NONE."""

from __future__ import annotations

from typing import Final

SCHEMA_ID: Final = "current_full_stack_semantic_explorer_run.v1"
TOOL_AUTHORITY: Final = "NONE"
EXTERNAL_EFFECTS_PERFORMED: Final = 0

EVIDENCE_CLASSES: Final = frozenset({"STATIC", "CONTRACT", "RUNTIME_OBSERVED"})
STATUSES: Final = frozenset({"PROVEN", "UNPROVEN"})
SLICE_STATUSES: Final = frozenset({"PASS", "FAIL", "INCOMPLETE"})

AUTHORITY_FIELDS: Final = {
    "authority": "AUTHORITY",
    "decision_authority": "DECISION_AUTHORITY",
    "execution_authority": "EXECUTION_AUTHORITY",
    "safety_authority": "SAFETY_AUTHORITY",
}
AUTHORITY_PREDICATES: Final = frozenset(AUTHORITY_FIELDS.values())

PERSIST_CALLS: Final = frozenset(
    {
        "open",
        "dump",
        "dumps",
        "write_text",
        "write_bytes",
        "execute",
        "executemany",
        "to_csv",
        "to_parquet",
    }
)
EXTERNAL_ROOTS: Final = frozenset({"requests", "httpx", "socket", "urllib"})
EXTERNAL_ATTRS: Final = frozenset(
    {"get", "post", "put", "delete", "request", "urlopen", "create_connection"}
)

MAX_BLOB_BYTES: Final = 262144
