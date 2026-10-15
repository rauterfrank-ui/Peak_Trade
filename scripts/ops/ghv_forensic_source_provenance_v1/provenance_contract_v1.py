"""FORENSIC_SOURCE_PROVENANCE_CONTRACT (R1-A)."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

CLEAN_DIRTY_FINGERPRINT_PREFIX = "e3b0c44298fc1c14"
SCHEMA_VERSION = "forensic_source_provenance.v1"


class SourceDirtyStatus(str, Enum):
    CLEAN = "CLEAN"
    DIRTY = "DIRTY"
    UNKNOWN = "UNKNOWN"


class SourceValidationMode(str, Enum):
    STRICT_CURRENT = "STRICT_CURRENT"
    NAVIGATION_ONLY = "NAVIGATION_ONLY"
    UNKNOWN = "UNKNOWN"


class SourceProvenanceKind(str, Enum):
    PINNED_GIT_TREE = "PINNED_GIT_TREE"
    ISOLATED_CHECKOUT = "ISOLATED_CHECKOUT"
    SNAPSHOT_BINDING = "SNAPSHOT_BINDING"
    UNKNOWN = "UNKNOWN"


class TestExecutionClass(str, Enum):
    EXECUTED_PINNED_CURRENT = "EXECUTED_PINNED_CURRENT"
    EXECUTED_LOCAL_WIP = "EXECUTED_LOCAL_WIP"
    STATIC_TEST_INSPECTION = "STATIC_TEST_INSPECTION"
    GHV_MODEL_ONLY = "GHV_MODEL_ONLY"
    NOT_EXECUTED = "NOT_EXECUTED"
    UNKNOWN = "UNKNOWN"


def _git_rev_parse(repo_root: Path, ref: str) -> str | None:
    try:
        return subprocess.check_output(
            ["git", "-C", str(repo_root), "rev-parse", ref],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except subprocess.CalledProcessError:
        return None


def resolve_declared_current_sha(
    *,
    repo_root: Path,
    declared_current_sha: str | None,
) -> str | None:
    if declared_current_sha and declared_current_sha.strip():
        full = _git_rev_parse(repo_root, declared_current_sha.strip())
        return full or declared_current_sha.strip()
    return None


def classify_dirty_status(dirty_fingerprint: str | None) -> SourceDirtyStatus:
    if not dirty_fingerprint or dirty_fingerprint == "unknown":
        return SourceDirtyStatus.UNKNOWN
    if dirty_fingerprint.startswith(CLEAN_DIRTY_FINGERPRINT_PREFIX):
        return SourceDirtyStatus.CLEAN
    return SourceDirtyStatus.DIRTY


def infer_source_provenance_kind(
    *,
    repo_root: Path,
    declared_current_sha: str | None,
    actual_source_sha: str | None,
    source_dirty_status: SourceDirtyStatus,
    snapshot_binding_verified: bool,
) -> SourceProvenanceKind:
    if snapshot_binding_verified:
        return SourceProvenanceKind.SNAPSHOT_BINDING
    if not declared_current_sha or not actual_source_sha:
        return SourceProvenanceKind.UNKNOWN
    if declared_current_sha != actual_source_sha:
        return SourceProvenanceKind.UNKNOWN
    if source_dirty_status == SourceDirtyStatus.CLEAN:
        resolved = str(repo_root.resolve())
        if "/tmp/" in resolved or ".worktrees/" in resolved:
            return SourceProvenanceKind.ISOLATED_CHECKOUT
        return SourceProvenanceKind.PINNED_GIT_TREE
    return SourceProvenanceKind.UNKNOWN


def classify_test_execution(
    *,
    test_execution_sha: str | None,
    declared_current_sha: str | None,
    actual_source_sha: str | None,
    source_dirty_status: SourceDirtyStatus,
    invoked_via_pytest: bool,
) -> TestExecutionClass:
    if not test_execution_sha:
        if invoked_via_pytest:
            return TestExecutionClass.STATIC_TEST_INSPECTION
        return TestExecutionClass.NOT_EXECUTED
    if declared_current_sha and test_execution_sha == declared_current_sha:
        if (
            source_dirty_status == SourceDirtyStatus.CLEAN
            and actual_source_sha == declared_current_sha
        ):
            return TestExecutionClass.EXECUTED_PINNED_CURRENT
        return TestExecutionClass.EXECUTED_LOCAL_WIP
    if actual_source_sha and test_execution_sha == actual_source_sha:
        return TestExecutionClass.EXECUTED_LOCAL_WIP
    return TestExecutionClass.UNKNOWN


@dataclass(frozen=True)
class ForensicSourceProvenanceRecordV1:
    schema_version: str
    declared_current_sha: str | None
    actual_source_sha: str | None
    ghv_source_sha: str | None
    test_execution_sha: str | None
    snapshot_id: str | None
    source_provenance: str
    proof_eligibility: bool
    source_tree_identity: str | None
    source_dirty_status: str
    source_validation_mode: str
    proof_eligibility_reasons: tuple[str, ...]
    test_execution_class: str
    source_repository_path: str | None
    current_graph_verified: bool | None
    snapshot_binding_verified: bool | None
    source_validation_pass_reported: bool | None
    source_validation_pass_composed_field: bool | None
    runtime_correlation_proven: bool
    global_causal_closure_proven: bool
    global_non_interference_proven: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "DECLARED_CURRENT_SHA": self.declared_current_sha or "UNKNOWN",
            "ACTUAL_SOURCE_SHA": self.actual_source_sha or "UNKNOWN",
            "GHV_SOURCE_SHA": self.ghv_source_sha or "UNKNOWN",
            "TEST_EXECUTION_SHA": self.test_execution_sha or "UNKNOWN",
            "SNAPSHOT_ID": self.snapshot_id or "UNKNOWN",
            "SOURCE_PROVENANCE": self.source_provenance,
            "PROOF_ELIGIBILITY": self.proof_eligibility,
            "SOURCE_TREE_IDENTITY": self.source_tree_identity or "UNKNOWN",
            "SOURCE_DIRTY_STATUS": self.source_dirty_status,
            "SOURCE_VALIDATION_MODE": self.source_validation_mode,
            "PROOF_ELIGIBILITY_REASONS": list(self.proof_eligibility_reasons),
            "TEST_EXECUTION_CLASS": self.test_execution_class,
            "SOURCE_REPOSITORY_PATH": self.source_repository_path or "UNKNOWN",
            "CURRENT_GRAPH_VERIFIED": self.current_graph_verified,
            "SNAPSHOT_BINDING_VERIFIED": self.snapshot_binding_verified,
            "SOURCE_VALIDATION_PASS_REPORTED": self.source_validation_pass_reported,
            "SOURCE_VALIDATION_PASS_COMPOSED_FIELD": self.source_validation_pass_composed_field,
            "RUNTIME_CORRELATION_PROVEN": self.runtime_correlation_proven,
            "GLOBAL_CAUSAL_CLOSURE_PROVEN": self.global_causal_closure_proven,
            "GLOBAL_NON_INTERFERENCE_PROVEN": self.global_non_interference_proven,
        }
