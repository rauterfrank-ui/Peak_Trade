"""Reason / failure codes for Cap 7.1 actionability evidence."""

from __future__ import annotations

from enum import Enum


class ActionabilityFailureCodeV1(str, Enum):
    CORRUPT_CHECKPOINT = "CORRUPT_CHECKPOINT"
    CONFIG_DIGEST_MISMATCH = "CONFIG_DIGEST_MISMATCH"
    WRITER_CONFLICT = "WRITER_CONFLICT"
    EVIDENCE_MATERIALIZATION_FAILED = "EVIDENCE_MATERIALIZATION_FAILED"
    FORCED_INJECTION_REJECTED = "FORCED_INJECTION_REJECTED"
