"""Constants for simple run evidence retention v1 (navigation only; no runtime authority)."""

from __future__ import annotations

SCHEMA_SIMPLE_RUN_EVIDENCE_INDEX_ENTRY_V1 = "peak_trade.simple_run_evidence_index_entry.v1"

RUN_CLASS_PAPER = "paper"
RUN_CLASS_SHADOW = "shadow"
RUN_CLASS_TESTNET = "testnet"
RUN_CLASS_CANARY = "canary"

ARCHIVE_RUN_CLASSES = (
    RUN_CLASS_PAPER,
    RUN_CLASS_SHADOW,
    RUN_CLASS_TESTNET,
)

RETENTION_STANDARD = "STANDARD"
RETENTION_KEEP = "KEEP"
RETENTION_CANARY = "CANARY"
RETENTION_FORENSIC = "FORENSIC"

VALID_RETENTION_CLASSES = frozenset(
    {
        RETENTION_STANDARD,
        RETENTION_KEEP,
        RETENTION_CANARY,
        RETENTION_FORENSIC,
    }
)

RUN_STATUS_RUNNING = "RUNNING"
RUN_STATUS_COMPLETE = "COMPLETE"
RUN_STATUS_INCOMPLETE = "INCOMPLETE"
RUN_STATUS_FAILED = "FAILED"
RUN_STATUS_ABORTED = "ABORTED"

# Incomplete runs must not surface as COMPLETE (contract tests).
TERMINAL_STATUSES = frozenset(
    {
        RUN_STATUS_COMPLETE,
        RUN_STATUS_FAILED,
        RUN_STATUS_ABORTED,
    }
)

# Legacy archive contract (other systems); NOT used as owner-storage fallback.
ENV_DATA_ARCHIVE_ROOT = "PEAK_TRADE_DATA_ARCHIVE_ROOT"

# Owner navigation / durable owner-layer writes (simple_run_evidence_retention_v1 only).
ENV_OWNER_RUN_EVIDENCE_ROOT = "PEAK_TRADE_OWNER_RUN_EVIDENCE_ROOT"
OWNER_HOME_DIR_NAME = "Peak_Trade_Run_Evidence"
OWNER_RUNS_DIRNAME = "runs"
OWNER_INDEX_DIRNAME = "index"
OWNER_INDEX_FILENAME = "runs.jsonl"

RETENTION_SIDECAR_FILENAME = "RETENTION.json"

# Repo evidence/ops capability roots treated as canary-class evidence (do not degrade).
CANARY_EVIDENCE_CAPABILITY_PREFIXES = (
    "section_11_13_5_",
    "section_11_13_pre_canary_",
    "combined_ghv_whole_cycle_canary_",
)

CANARY_EVIDENCE_CAPABILITY_EXACT = frozenset(
    {
        "combined_ghv_whole_cycle_canary_measurement_v1",
    }
)

GENERIC_EVIDENCE_RUN_REGISTRY_OWNER = "scripts/ops/build_generic_evidence_run_registry_v1.py"
PRIMARY_EVIDENCE_RETENTION_OWNER = "scripts/ops/primary_evidence_retention_v0.py"
