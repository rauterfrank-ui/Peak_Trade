"""Governance closeout binding for PR #5185–#5187 linear diagnostics consumer chain v0.

Narrow adapter over the canonical progress registry owner. Offline, deterministic,
non-authorizing — binds manifest-verified merge closeouts without mutating economic
evidence or promotion semantics.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from src.governance.runbook_progress_registry_v1 import (
    CANONICAL_RUNBOOK_PROGRESS_REGISTRY_DOC,
    RUNBOOK_PROGRESS_REGISTRY_RESOLVER_OWNER,
    RunbookProgressRegistryError,
    RunbookProgressRegistryV1,
    load_runbook_progress_registry_v1,
)

SCOPE = "CANONICAL_OFFLINE_LINEAR_DIAGNOSTICS_AND_PROMOTION_BINDING_COMPLETION_RECONCILIATION_V0"
GO_TOKEN = (
    "GO_CANONICAL_OFFLINE_LINEAR_DIAGNOSTICS_AND_PROMOTION_BINDING_COMPLETION_RECONCILIATION_V0"
)
RECONCILIATION_OWNER = (
    "src.governance."
    "canonical_offline_linear_diagnostics_promotion_binding_completion_reconciliation_v0"
)
PROGRESS_REGISTRY_OWNER = CANONICAL_RUNBOOK_PROGRESS_REGISTRY_DOC
CLOSEOUT_SECTION_PREFIX = (
    "#### CANONICAL_OFFLINE_LINEAR_DIAGNOSTICS_AND_PROMOTION_BINDING_COMPLETION_RECONCILIATION_V0"
)

ARCHIVE_ROOT = Path("/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z")
DERIVATION_EVIDENCE_DIR = (
    ARCHIVE_ROOT
    / "research"
    / "derive_next_canonical_offline_scope_post_pr5187_read_only_v0_20260714T233810Z"
)

SUPPORT_BUNDLE_OWNER = (
    "src/research/linear_evidence/offline_productive_linear_diagnostics_support_bundle_v0.py"
)
ECONOMIC_EVIDENCE_CONSUMER_OWNER = (
    "src/research/linear_evidence/"
    "offline_productive_linear_diagnostics_economic_evidence_consumer_binding_v0.py"
)
PROMOTION_GATE_CONSUMER_OWNER = (
    "src/research/linear_evidence/"
    "offline_productive_linear_diagnostics_promotion_economic_gate_consumer_binding_v0.py"
)

PR5185_CLOSEOUT_DIR = (
    ARCHIVE_ROOT
    / "research"
    / "pr5185_merge_closeout_offline_productive_linear_diagnostics_support_bundle_v0_"
    "20260714T230433Z"
)
PR5186_CLOSEOUT_DIR = (
    ARCHIVE_ROOT
    / "research"
    / "pr5186_merge_closeout_offline_productive_linear_diagnostics_economic_evidence_consumer_binding_v0_"
    "20260714T231652Z"
)
PR5187_CLOSEOUT_DIR = (
    ARCHIVE_ROOT
    / "research"
    / "pr5187_merge_closeout_offline_productive_linear_diagnostics_promotion_economic_gate_consumer_binding_v0_"
    "20260714T233336Z"
)

PR_CHAIN: tuple[dict[str, str], ...] = (
    {
        "pr": "5185",
        "scope": "OFFLINE_PRODUCTIVE_LINEAR_DIAGNOSTICS_SUPPORT_BUNDLE_V0",
        "merge_commit": "175aca7872a89898dd3986e12749b0713efaea03",
        "closeout_dir": str(PR5185_CLOSEOUT_DIR),
        "consumer_owner": SUPPORT_BUNDLE_OWNER,
    },
    {
        "pr": "5186",
        "scope": "OFFLINE_PRODUCTIVE_LINEAR_DIAGNOSTICS_ECONOMIC_EVIDENCE_CONSUMER_BINDING_V0",
        "merge_commit": "299132bbd2af94f56f98c554798c8fdc48819651",
        "closeout_dir": str(PR5186_CLOSEOUT_DIR),
        "consumer_owner": ECONOMIC_EVIDENCE_CONSUMER_OWNER,
    },
    {
        "pr": "5187",
        "scope": "OFFLINE_PRODUCTIVE_LINEAR_DIAGNOSTICS_PROMOTION_ECONOMIC_GATE_CONSUMER_BINDING_V0",
        "merge_commit": "1d1f3ba85d02f35711ba632096e7aa2240f50d6e",
        "closeout_dir": str(PR5187_CLOSEOUT_DIR),
        "consumer_owner": PROMOTION_GATE_CONSUMER_OWNER,
    },
)

AUTHORITATIVE_TRUTH: dict[str, str] = {
    "STEP_29L_1_STATUS": "COMPLETE_AND_PRODUCTIVELY_BOUND",
    "FULL_CANONICAL_CHAIN_WIRED": "true",
    "BACKTEST_RUNTIME_DECISION_PARITY_PASS": "true",
    "STEP_29L_2_STATUS": "COMPLETE_AND_PRODUCTIVELY_BOUND",
    "LINEAR_DIAGNOSTIC_CLASS_COUNT": "5",
    "LINEAR_DIAGNOSTICS_SUPPORT_BUNDLE_BOUND": "true",
    "LINEAR_DIAGNOSTICS_ECONOMIC_EVIDENCE_CONSUMER_BOUND": "true",
    "LINEAR_DIAGNOSTICS_PROMOTION_GATE_CONSUMER_BOUND": "true",
    "STEP_29M_STATUS": "COMPLETE_FAIL_CLOSED",
    "STEP29M_FLEET_STATUS": "TERMINAL_FAIL_RESEARCH_GENERATION_CLOSED",
    "UNCHANGED_RETRY_BLOCKED": "true",
    "POLICY_RESCUE_ALLOWED": "false",
    "STEP_29N_STATUS": "COMPLETE_AND_PRODUCTIVELY_BOUND",
    "PROMOTION_ECONOMIC_GATE_BOUND": "true",
    "PROMOTION_ECONOMIC_GATE_STATUS": "BLOCKED",
    "PROMOTION_BLOCKING_REASON": "BLOCKED_SOURCE_DIAGNOSTICS_PRESENT",
    "STEP_29O_STATUS": "COMPLETE_AND_PRODUCTIVELY_BOUND",
    "STEP_29P_STATUS": "COMPLETE_AND_PRODUCTIVELY_BOUND",
    "STEP_29Q_STATUS": "COMPLETE_AND_PRODUCTIVELY_BOUND",
    "STEP_29R_STATUS": "COMPLETE_FAIL_CLOSED",
    "RUNBOOK_STEP_29R_STATUS": "BLOCKED",
    "RUNTIME_REWIRE_ADMISSIBLE": "false",
    "RUNTIME_REWIRE_BLOCKING_REASON": "ECONOMIC_VALIDITY_OFFLINE_GATE_PASS_FALSE",
    "PR5185_MERGE_CLOSEOUT_BOUND": "true",
    "PR5186_MERGE_CLOSEOUT_BOUND": "true",
    "PR5187_MERGE_CLOSEOUT_BOUND": "true",
    "LINEAR_DIAGNOSTICS_CONSUMER_CHAIN_TERMINAL": "true",
    "NO_IMPLEMENTATION_GAP": "true",
    "REMAINING_BLOCK_CLASS": "POLICY_BLOCK_ONLY",
    "ECONOMIC_VALIDITY_OFFLINE_GATE_PASS": "false",
}

FIELD_TABLE_ROW_RE = re.compile(r"\| `([^`]+)` \| `([^`]*)` \|")


class ReconciliationBindingError(ValueError):
    """Fail-closed reconciliation binding error."""


@dataclass(frozen=True)
class CloseoutBindingRecordV0:
    pr: str
    scope: str
    merge_commit: str
    closeout_dir: Path
    consumer_owner: str
    manifest_verify_rc: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "pr": self.pr,
            "scope": self.scope,
            "merge_commit": self.merge_commit,
            "closeout_dir": str(self.closeout_dir),
            "consumer_owner": self.consumer_owner,
            "manifest_verify_rc": self.manifest_verify_rc,
            "runtime_effect": "NONE",
            "authority_effect": "NONE",
            "completion_status": "COMPLETE",
        }


def default_progress_registry_path(repo_root: Path | None = None) -> Path:
    root = repo_root or Path(__file__).resolve().parents[2]
    return root / CANONICAL_RUNBOOK_PROGRESS_REGISTRY_DOC


def verify_closeout_manifest(closeout_dir: Path, verify_fn: Callable[[Path], int]) -> int:
    if not closeout_dir.is_dir():
        raise ReconciliationBindingError(f"missing closeout directory: {closeout_dir}")
    manifest = closeout_dir / "MANIFEST.sha256"
    if not manifest.is_file():
        raise ReconciliationBindingError(f"missing MANIFEST.sha256: {closeout_dir}")
    rc = verify_fn(closeout_dir)
    if isinstance(rc, tuple):
        ok, _msg = rc
        rc = 0 if ok else 1
    if rc != 0:
        raise ReconciliationBindingError(
            f"closeout manifest verification failed rc={rc}: {closeout_dir}"
        )
    return rc


def verify_source_derivation_manifest(
    derivation_dir: Path = DERIVATION_EVIDENCE_DIR,
    verify_fn: Callable[[Path], int] | None = None,
) -> int:
    if verify_fn is None:
        from scripts.ops.primary_evidence_retention_v0 import verify_manifest_sha256

        verify_fn = verify_manifest_sha256
    return verify_closeout_manifest(derivation_dir, verify_fn)


def build_closeout_binding_map_v0(
    verify_fn: Callable[[Path], int],
) -> tuple[CloseoutBindingRecordV0, ...]:
    records: list[CloseoutBindingRecordV0] = []
    for item in PR_CHAIN:
        closeout_dir = Path(item["closeout_dir"])
        rc = verify_closeout_manifest(closeout_dir, verify_fn)
        records.append(
            CloseoutBindingRecordV0(
                pr=item["pr"],
                scope=item["scope"],
                merge_commit=item["merge_commit"],
                closeout_dir=closeout_dir,
                consumer_owner=item["consumer_owner"],
                manifest_verify_rc=rc,
            )
        )
    return tuple(records)


def build_pr_chain_json_v0(records: Sequence[CloseoutBindingRecordV0]) -> dict[str, Any]:
    return {
        "schema_version": "pr5185_5187_chain.v0",
        "terminal_pr": "5187",
        "terminal_merge_commit": PR_CHAIN[-1]["merge_commit"],
        "diagnostic_class_count": 5,
        "chain": [record.to_dict() for record in records],
    }


def _section_field_value(text: str, section_prefix: str, field: str) -> str:
    start = text.index(section_prefix)
    end = text.find("\n#### ", start + 1)
    section = text[start:end] if end != -1 else text[start:]
    match = re.search(rf"\| `{re.escape(field)}` \| `([^`]*)` \|", section)
    if not match:
        raise ReconciliationBindingError(f"missing field {field} in section {section_prefix}")
    return match.group(1)


def validate_authoritative_registry_fields(
    registry: RunbookProgressRegistryV1 | None = None,
    *,
    repo_root: Path | None = None,
) -> dict[str, str]:
    parsed = registry or load_runbook_progress_registry_v1(
        default_progress_registry_path(repo_root)
    )
    observed: dict[str, str] = {}
    for field, expected in AUTHORITATIVE_TRUTH.items():
        try:
            actual = parsed.authoritative_value(field)
        except RunbookProgressRegistryError as exc:
            raise ReconciliationBindingError(
                f"missing authoritative registry field: {field}"
            ) from exc
        if actual != expected:
            raise ReconciliationBindingError(
                f"registry field mismatch for {field}: expected={expected!r} actual={actual!r}"
            )
        observed[field] = actual
    return observed


def validate_closeout_section_fields(registry_text: str) -> dict[str, str]:
    required = {
        "STATUS": "COMPLETE",
        "SCOPE_CLASSIFICATION": SCOPE,
        "GO_TOKEN": GO_TOKEN,
        "PR5185_MERGE_CLOSEOUT_BOUND": "true",
        "PR5186_MERGE_CLOSEOUT_BOUND": "true",
        "PR5187_MERGE_CLOSEOUT_BOUND": "true",
        "LINEAR_DIAGNOSTICS_CONSUMER_CHAIN_TERMINAL": "true",
        "NO_IMPLEMENTATION_GAP": "true",
        "REMAINING_BLOCK_CLASS": "POLICY_BLOCK_ONLY",
        "PROMOTION_ECONOMIC_GATE_STATUS": "BLOCKED",
        "PROMOTION_BLOCKING_REASON": "BLOCKED_SOURCE_DIAGNOSTICS_PRESENT",
        "ECONOMIC_VALIDITY_OFFLINE_GATE_PASS": "false",
        "HISTORICAL_NEGATIVE_EVIDENCE_MUTATED": "false",
        "POLICY_RESCUE_ALLOWED": "false",
        "UNCHANGED_RETRY_BLOCKED": "true",
        "RUNTIME_EFFECT": "NONE",
        "AUTHORITY_EFFECT": "NONE",
    }
    observed: dict[str, str] = {}
    for field, expected in required.items():
        actual = _section_field_value(registry_text, CLOSEOUT_SECTION_PREFIX, field)
        if actual != expected:
            raise ReconciliationBindingError(
                f"closeout section mismatch for {field}: expected={expected!r} actual={actual!r}"
            )
        observed[field] = actual
    return observed


def validate_pr_chain_order(records: Sequence[CloseoutBindingRecordV0]) -> None:
    if len(records) != 3:
        raise ReconciliationBindingError(f"expected 3 PR closeout records, got {len(records)}")
    pr_numbers = [record.pr for record in records]
    if pr_numbers != ["5185", "5186", "5187"]:
        raise ReconciliationBindingError(f"invalid PR chain order: {pr_numbers}")


def reject_contradictory_pass_when_gate_false(
    economic_validity_offline_gate_pass: bool,
    promotion_economic_gate_status: str,
) -> None:
    if not economic_validity_offline_gate_pass and promotion_economic_gate_status == "PASS":
        raise ReconciliationBindingError(
            "contradictory PASS promotion status with ECONOMIC_VALIDITY_OFFLINE_GATE_PASS=false"
        )


def reject_missing_closeout_reference(record: CloseoutBindingRecordV0 | None) -> None:
    if record is None:
        raise ReconciliationBindingError("missing PR closeout reference")


def reject_invalid_manifest_status(manifest_verify_rc: int) -> None:
    if manifest_verify_rc != 0:
        raise ReconciliationBindingError(f"invalid source manifest status rc={manifest_verify_rc}")


def deterministic_materialization_digest(payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def build_owner_inventory_v0() -> dict[str, Any]:
    return {
        "progress_registry_owner": PROGRESS_REGISTRY_OWNER,
        "progress_registry_resolver_owner": RUNBOOK_PROGRESS_REGISTRY_RESOLVER_OWNER,
        "reconciliation_owner": RECONCILIATION_OWNER,
        "support_bundle_owner": SUPPORT_BUNDLE_OWNER,
        "economic_evidence_consumer_owner": ECONOMIC_EVIDENCE_CONSUMER_OWNER,
        "promotion_gate_consumer_owner": PROMOTION_GATE_CONSUMER_OWNER,
        "contract_test_owner": (
            "tests/ops/"
            "test_canonical_offline_linear_diagnostics_and_promotion_binding_"
            "completion_reconciliation_v0_contract.py"
        ),
    }


def build_reuse_decision_v0() -> dict[str, str]:
    return {
        "decision": "REUSE_WITH_NARROW_ADAPTER",
        "progress_registry": "REUSE_AS_IS",
        "reconciliation_adapter": "NEW_NARROW_ADAPTER_JUSTIFIED",
        "parallel_registry_owner_forbidden": "true",
        "rationale": (
            "PR5185-5187 consumer chain complete; only progress registry closeout binding missing"
        ),
    }


__all__ = [
    "AUTHORITATIVE_TRUTH",
    "CLOSEOUT_SECTION_PREFIX",
    "CloseoutBindingRecordV0",
    "GO_TOKEN",
    "PR_CHAIN",
    "RECONCILIATION_OWNER",
    "ReconciliationBindingError",
    "SCOPE",
    "build_closeout_binding_map_v0",
    "build_owner_inventory_v0",
    "build_pr_chain_json_v0",
    "build_reuse_decision_v0",
    "default_progress_registry_path",
    "deterministic_materialization_digest",
    "reject_contradictory_pass_when_gate_false",
    "reject_invalid_manifest_status",
    "reject_missing_closeout_reference",
    "validate_authoritative_registry_fields",
    "validate_closeout_section_fields",
    "validate_pr_chain_order",
    "verify_closeout_manifest",
    "verify_source_derivation_manifest",
]
