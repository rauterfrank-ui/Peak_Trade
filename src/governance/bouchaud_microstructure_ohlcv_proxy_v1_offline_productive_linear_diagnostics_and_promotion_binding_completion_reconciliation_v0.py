"""Governance closeout binding for PR #5189–#5193 Bouchaud linear diagnostics consumer chain v0.

Narrow adapter over manifest-verified merge closeouts. Offline, deterministic,
non-authorizing — binds PR5189–5193 without mutating economic evidence, promotion
semantics, or the runbook progress registry.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from src.research.bouchaud_microstructure_ohlcv_proxy_v1_offline_productive_linear_diagnostics_execution_and_support_evidence_v0 import (
    CANONICAL_FEATURE_DIGEST,
)
from src.research.linear_evidence.offline_productive_linear_diagnostics_promotion_economic_gate_consumer_binding_v0 import (
    BLOCKING_REASON_BLOCKED_SOURCE_DIAGNOSTICS_PRESENT,
)

SCOPE = (
    "BOUCHAUD_MICROSTRUCTURE_OHLCV_PROXY_V1_OFFLINE_PRODUCTIVE_LINEAR_DIAGNOSTICS_"
    "AND_PROMOTION_BINDING_COMPLETION_RECONCILIATION_V0"
)
GO_TOKEN = (
    "GO_BOUCHAUD_MICROSTRUCTURE_OHLCV_PROXY_V1_OFFLINE_PRODUCTIVE_LINEAR_DIAGNOSTICS_"
    "AND_PROMOTION_BINDING_COMPLETION_RECONCILIATION_V0"
)
RECONCILIATION_OWNER = (
    "src.governance."
    "bouchaud_microstructure_ohlcv_proxy_v1_offline_productive_linear_diagnostics_"
    "and_promotion_binding_completion_reconciliation_v0"
)

ARCHIVE_ROOT = Path("/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z")
DERIVATION_EVIDENCE_DIR = (
    ARCHIVE_ROOT
    / "research"
    / "pr5193_merge_closeout_bouchaud_offline_productive_linear_diagnostics_"
    "promotion_economic_gate_consumer_binding_v0_20260715T013242Z"
)

RESEARCH_GENERATION_PREPARATION_OWNER = (
    "src/research/bouchaud_microstructure_ohlcv_proxy_v1_research_generation_preparation_v0.py"
)
FEATURE_MATRIX_BINDING_OWNER = (
    "src/research/"
    "bouchaud_microstructure_ohlcv_proxy_v1_offline_productive_linear_diagnostics_"
    "feature_matrix_binding_v0.py"
)
EXECUTION_SUPPORT_EVIDENCE_OWNER = (
    "src/research/"
    "bouchaud_microstructure_ohlcv_proxy_v1_offline_productive_linear_diagnostics_"
    "execution_and_support_evidence_v0.py"
)
ECONOMIC_EVIDENCE_CONSUMER_OWNER = (
    "scripts/ops/"
    "materialize_bouchaud_microstructure_ohlcv_proxy_v1_offline_productive_linear_diagnostics_"
    "economic_evidence_consumer_binding_v0.py"
)
PROMOTION_GATE_CONSUMER_OWNER = (
    "scripts/ops/"
    "materialize_bouchaud_microstructure_ohlcv_proxy_v1_offline_productive_linear_diagnostics_"
    "promotion_economic_gate_consumer_binding_v0.py"
)

PR5189_CLOSEOUT_DIR = (
    ARCHIVE_ROOT
    / "research"
    / "pr5189_merge_closeout_bouchaud_microstructure_ohlcv_proxy_v1_research_generation_"
    "preparation_v0_20260715T002136Z"
)
PR5190_CLOSEOUT_DIR = (
    ARCHIVE_ROOT
    / "research"
    / "pr5190_merge_closeout_bouchaud_microstructure_ohlcv_proxy_v1_offline_productive_linear_"
    "diagnostics_feature_matrix_binding_v0_20260715T003858Z"
)
PR5190_IMPLEMENTATION_DIR = (
    ARCHIVE_ROOT
    / "research"
    / "bouchaud_microstructure_ohlcv_proxy_v1_offline_productive_linear_diagnostics_"
    "feature_matrix_binding_v0_20260715T002940Z"
)
PR5190_CLOSEOUT_MANIFEST_LOG_DRIFT = True
PR5191_CLOSEOUT_DIR = (
    ARCHIVE_ROOT
    / "research"
    / "pr5191_merge_closeout_bouchaud_microstructure_ohlcv_proxy_v1_offline_productive_linear_"
    "diagnostics_execution_and_support_evidence_v0_20260715T005450Z"
)
PR5192_CLOSEOUT_DIR = (
    ARCHIVE_ROOT
    / "research"
    / "pr5192_merge_closeout_bouchaud_offline_productive_linear_diagnostics_"
    "economic_evidence_consumer_binding_v0_20260715T011845Z"
)
PR5193_CLOSEOUT_DIR = (
    ARCHIVE_ROOT
    / "research"
    / "pr5193_merge_closeout_bouchaud_offline_productive_linear_diagnostics_"
    "promotion_economic_gate_consumer_binding_v0_20260715T013242Z"
)

PR5191_IMPLEMENTATION_DIR = (
    ARCHIVE_ROOT
    / "research"
    / "bouchaud_microstructure_ohlcv_proxy_v1_offline_productive_linear_diagnostics_"
    "execution_and_support_evidence_v0_20260715T004424Z"
)
PR5192_IMPLEMENTATION_DIR = (
    ARCHIVE_ROOT
    / "research"
    / "bouchaud_microstructure_ohlcv_proxy_v1_offline_productive_linear_diagnostics_"
    "economic_evidence_consumer_binding_v0_20260715T011845Z"
)

PR_CHAIN: tuple[dict[str, str], ...] = (
    {
        "pr": "5189",
        "scope": "BOUCHAUD_MICROSTRUCTURE_OHLCV_PROXY_V1_RESEARCH_GENERATION_PREPARATION_V0",
        "merge_commit": "9065e8eb8824937db2033c1c4b54419c10630afa",
        "closeout_dir": str(PR5189_CLOSEOUT_DIR),
        "consumer_owner": RESEARCH_GENERATION_PREPARATION_OWNER,
    },
    {
        "pr": "5190",
        "scope": (
            "BOUCHAUD_MICROSTRUCTURE_OHLCV_PROXY_V1_OFFLINE_PRODUCTIVE_LINEAR_"
            "DIAGNOSTICS_FEATURE_MATRIX_BINDING_V0"
        ),
        "merge_commit": "eaa03ec54cbc3ae36decfa8bb2332701aa0e4059",
        "closeout_dir": str(PR5190_CLOSEOUT_DIR),
        "fallback_implementation_dir": str(PR5190_IMPLEMENTATION_DIR),
        "known_closeout_manifest_log_drift": "true",
        "consumer_owner": FEATURE_MATRIX_BINDING_OWNER,
    },
    {
        "pr": "5191",
        "scope": (
            "BOUCHAUD_MICROSTRUCTURE_OHLCV_PROXY_V1_OFFLINE_PRODUCTIVE_LINEAR_"
            "DIAGNOSTICS_EXECUTION_AND_SUPPORT_EVIDENCE_V0"
        ),
        "merge_commit": "6bc9fcd3a7ed44b7ce04f9607805839ca306da1c",
        "closeout_dir": str(PR5191_CLOSEOUT_DIR),
        "consumer_owner": EXECUTION_SUPPORT_EVIDENCE_OWNER,
    },
    {
        "pr": "5192",
        "scope": (
            "BOUCHAUD_OFFLINE_PRODUCTIVE_LINEAR_DIAGNOSTICS_ECONOMIC_EVIDENCE_CONSUMER_BINDING_V0"
        ),
        "merge_commit": "ce2a73cd370a715d6add4338c7ef0c9c869ef20b",
        "closeout_dir": str(PR5192_CLOSEOUT_DIR),
        "consumer_owner": ECONOMIC_EVIDENCE_CONSUMER_OWNER,
    },
    {
        "pr": "5193",
        "scope": "BOUCHAUD_PROMOTION_ECONOMIC_GATE_CONSUMER_BINDING_V0",
        "merge_commit": "f28c0358da38f6a4e6df2740157f24f682227e24",
        "closeout_dir": str(PR5193_CLOSEOUT_DIR),
        "consumer_owner": PROMOTION_GATE_CONSUMER_OWNER,
    },
)

AUTHORITATIVE_TRUTH: dict[str, str] = {
    "BOUCHAUD_RESEARCH_GENERATION_PREPARATION_BOUND": "true",
    "BOUCHAUD_FEATURE_MATRIX_BINDING_BOUND": "true",
    "BOUCHAUD_EXECUTION_SUPPORT_EVIDENCE_BOUND": "true",
    "BOUCHAUD_ECONOMIC_EVIDENCE_CONSUMER_BOUND": "true",
    "BOUCHAUD_PROMOTION_GATE_CONSUMER_BOUND": "true",
    "BOUCHAUD_LINEAR_DIAGNOSTICS_CONSUMER_CHAIN_TERMINAL": "true",
    "PR5189_MERGE_CLOSEOUT_BOUND": "true",
    "PR5190_MERGE_CLOSEOUT_BOUND": "true",
    "PR5191_MERGE_CLOSEOUT_BOUND": "true",
    "PR5192_MERGE_CLOSEOUT_BOUND": "true",
    "PR5193_MERGE_CLOSEOUT_BOUND": "true",
    "FEATURE_DIGEST": CANONICAL_FEATURE_DIGEST,
    "NO_IMPLEMENTATION_GAP": "true",
    "REMAINING_BLOCK_CLASS": "POLICY_BLOCK_ONLY",
    "PROMOTION_ECONOMIC_GATE_STATUS": "BLOCKED",
    "PROMOTION_BLOCKING_REASON": BLOCKING_REASON_BLOCKED_SOURCE_DIAGNOSTICS_PRESENT,
    "ECONOMIC_VALIDITY_OFFLINE_GATE_PASS": "false",
    "UNCHANGED_RETRY_BLOCKED": "true",
    "POLICY_RESCUE_ALLOWED": "false",
    "HISTORICAL_NEGATIVE_EVIDENCE_MUTATED": "false",
}


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
    evidence_binding_dir: Path
    closeout_manifest_log_drift: bool = False

    def to_dict(self) -> dict[str, Any]:
        payload = {
            "pr": self.pr,
            "scope": self.scope,
            "merge_commit": self.merge_commit,
            "closeout_dir": str(self.closeout_dir),
            "evidence_binding_dir": str(self.evidence_binding_dir),
            "consumer_owner": self.consumer_owner,
            "manifest_verify_rc": self.manifest_verify_rc,
            "runtime_effect": "NONE",
            "authority_effect": "NONE",
            "completion_status": "COMPLETE",
        }
        if self.closeout_manifest_log_drift:
            payload["closeout_manifest_log_drift"] = True
            payload["closeout_manifest_log_drift_note"] = (
                "PR5190 closeout MANIFEST_VERIFY.log self-referential drift; "
                "implementation bundle used as SSOT binding reference"
            )
        return payload


def verify_closeout_manifest(closeout_dir: Path, verify_fn: Callable[[Path], Any]) -> int:
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
    verify_fn: Callable[[Path], Any] | None = None,
) -> int:
    if verify_fn is None:
        from scripts.ops.primary_evidence_retention_v0 import verify_manifest_sha256

        verify_fn = verify_manifest_sha256
    return verify_closeout_manifest(derivation_dir, verify_fn)


def _resolve_evidence_binding_dir(item: Mapping[str, str]) -> Path:
    fallback = item.get("fallback_implementation_dir")
    if fallback:
        return Path(fallback)
    return Path(item["closeout_dir"])


def build_closeout_binding_map_v0(
    verify_fn: Callable[[Path], Any],
) -> tuple[CloseoutBindingRecordV0, ...]:
    records: list[CloseoutBindingRecordV0] = []
    for item in PR_CHAIN:
        closeout_dir = Path(item["closeout_dir"])
        evidence_binding_dir = _resolve_evidence_binding_dir(item)
        known_log_drift = item.get("known_closeout_manifest_log_drift") == "true"
        try:
            rc = verify_closeout_manifest(closeout_dir, verify_fn)
        except ReconciliationBindingError:
            if not known_log_drift:
                raise
            rc = verify_closeout_manifest(evidence_binding_dir, verify_fn)
        records.append(
            CloseoutBindingRecordV0(
                pr=item["pr"],
                scope=item["scope"],
                merge_commit=item["merge_commit"],
                closeout_dir=closeout_dir,
                consumer_owner=item["consumer_owner"],
                manifest_verify_rc=rc,
                evidence_binding_dir=evidence_binding_dir,
                closeout_manifest_log_drift=known_log_drift,
            )
        )
    return tuple(records)


def build_pr_chain_json_v0(records: Sequence[CloseoutBindingRecordV0]) -> dict[str, Any]:
    return {
        "schema_version": "pr5189_5193_bouchaud_chain.v0",
        "terminal_pr": "5193",
        "terminal_merge_commit": PR_CHAIN[-1]["merge_commit"],
        "feature_digest": CANONICAL_FEATURE_DIGEST,
        "chain": [record.to_dict() for record in records],
    }


def validate_pr_chain_order(records: Sequence[CloseoutBindingRecordV0]) -> None:
    if len(records) != 5:
        raise ReconciliationBindingError(f"expected 5 PR closeout records, got {len(records)}")
    pr_numbers = [record.pr for record in records]
    if pr_numbers != ["5189", "5190", "5191", "5192", "5193"]:
        raise ReconciliationBindingError(f"invalid PR chain order: {pr_numbers}")


def validate_authoritative_truth_fields(
    *,
    promotion_economic_gate_status: str,
    blocking_reason: str,
    feature_digest: str,
) -> dict[str, str]:
    if promotion_economic_gate_status != AUTHORITATIVE_TRUTH["PROMOTION_ECONOMIC_GATE_STATUS"]:
        raise ReconciliationBindingError(
            "promotion gate status mismatch: "
            f"expected={AUTHORITATIVE_TRUTH['PROMOTION_ECONOMIC_GATE_STATUS']!r} "
            f"actual={promotion_economic_gate_status!r}"
        )
    if BLOCKING_REASON_BLOCKED_SOURCE_DIAGNOSTICS_PRESENT not in blocking_reason:
        raise ReconciliationBindingError(
            f"blocking reason missing expected token: {blocking_reason!r}"
        )
    if feature_digest != CANONICAL_FEATURE_DIGEST:
        raise ReconciliationBindingError(
            f"feature digest mismatch: expected={CANONICAL_FEATURE_DIGEST!r} actual={feature_digest!r}"
        )
    return dict(AUTHORITATIVE_TRUTH)


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
        "reconciliation_owner": RECONCILIATION_OWNER,
        "research_generation_preparation_owner": RESEARCH_GENERATION_PREPARATION_OWNER,
        "feature_matrix_binding_owner": FEATURE_MATRIX_BINDING_OWNER,
        "execution_support_evidence_owner": EXECUTION_SUPPORT_EVIDENCE_OWNER,
        "economic_evidence_consumer_owner": ECONOMIC_EVIDENCE_CONSUMER_OWNER,
        "promotion_gate_consumer_owner": PROMOTION_GATE_CONSUMER_OWNER,
        "generic_promotion_gate_consumer_owner": (
            "src/research/linear_evidence/"
            "offline_productive_linear_diagnostics_promotion_economic_gate_consumer_binding_v0.py"
        ),
        "contract_test_owner": (
            "tests/ops/"
            "test_bouchaud_microstructure_ohlcv_proxy_v1_offline_productive_linear_diagnostics_"
            "and_promotion_binding_completion_reconciliation_v0_contract.py"
        ),
    }


def build_reuse_decision_v0() -> dict[str, str]:
    return {
        "decision": "REUSE_WITH_NARROW_ADAPTER",
        "reuse_source_pattern": "PR5188",
        "reconciliation_adapter": "NEW_NARROW_ADAPTER_JUSTIFIED",
        "runbook_mutation": "FORBIDDEN_BY_OPERATOR_SCOPE",
        "rationale": (
            "PR5189-5193 Bouchaud consumer chain complete; only manifest-verified closeout "
            "binding reconciliation missing without parallel promotion SSOT"
        ),
    }


__all__ = [
    "AUTHORITATIVE_TRUTH",
    "CloseoutBindingRecordV0",
    "DERIVATION_EVIDENCE_DIR",
    "GO_TOKEN",
    "PR5190_IMPLEMENTATION_DIR",
    "PR5190_CLOSEOUT_MANIFEST_LOG_DRIFT",
    "PR5191_IMPLEMENTATION_DIR",
    "PR5192_IMPLEMENTATION_DIR",
    "PR_CHAIN",
    "RECONCILIATION_OWNER",
    "ReconciliationBindingError",
    "SCOPE",
    "build_closeout_binding_map_v0",
    "build_owner_inventory_v0",
    "build_pr_chain_json_v0",
    "build_reuse_decision_v0",
    "deterministic_materialization_digest",
    "reject_contradictory_pass_when_gate_false",
    "reject_invalid_manifest_status",
    "reject_missing_closeout_reference",
    "validate_authoritative_truth_fields",
    "validate_pr_chain_order",
    "verify_closeout_manifest",
    "verify_source_derivation_manifest",
]
