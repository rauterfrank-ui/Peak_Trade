"""Scoped causal-graph adapter constants. AUTHORITY=NONE."""

from __future__ import annotations

from typing import Final

SCHEMA_ID: Final = "SCOPED_CAUSAL_GRAPH_ADAPTER_V1"
SCHEMA_VERSION: Final = 1
STATUS_MISSING_CURRENT_EVIDENCE: Final = "MISSING_CURRENT_EVIDENCE"
PROVENANCE_MANIFEST_NAME: Final = "scoped_graph_provenance_manifest.v1.json"
SOURCE_SYSTEM: Final = "CURRENT_SYSTEM_CENSUS"
GRAPH_MODE: Final = "STRICT_CURRENT"
