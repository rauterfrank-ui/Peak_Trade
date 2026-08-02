"""Prove Phase 9.2 prerequisites from productive Cap 7.2 / Phase 9.1 artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.ops.phase_9_2_public_md_session_preflight_v1.constants_v1 import (
    ACTIVATION_CAPABILITY_ID,
    PREDECESSOR_CAPABILITY_ID,
    repo_root_v1,
)
from src.ops.single_future_stateful_no_order_runtime_activation_v1.config_v1 import (
    load_activation_config_v1,
)
from src.ops.single_future_stateful_no_order_runtime_activation_v1.preconditions_v1 import (
    prove_preconditions_v1,
)


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def prove_phase91_closed_v1(*, repo_root: Path | None = None) -> dict[str, Any]:
    root = Path(repo_root) if repo_root is not None else repo_root_v1()
    result_path = (
        root
        / "docs/evidence/capability_phase_9_1_strategy_registry_closure_v1"
        / "productive_binding"
        / "phase_9_1_strategy_registry_closure_result_v1.json"
    )
    summary_path = (
        root / "docs/evidence/capability_phase_9_1_strategy_registry_closure_v1" / "SUMMARY.json"
    )
    if not result_path.is_file() or not summary_path.is_file():
        return {
            "ok": False,
            "PHASE_9_1_CLOSED": False,
            "STRATEGY_REGISTRY_CLOSED": False,
            "gap": "missing_phase_9_1_evidence",
        }
    result = _read_json(result_path)
    summary = _read_json(summary_path)
    closed = bool(result.get("STRATEGY_REGISTRY_CLOSED")) and bool(result.get("ok"))
    claims = dict(result.get("claims") or {})
    return {
        "ok": closed and bool(summary.get("ok")),
        "PHASE_9_1_CLOSED": closed,
        "STRATEGY_REGISTRY_CLOSED": closed,
        "capability_id": result.get("capability_id"),
        "expected_capability_id": PREDECESSOR_CAPABILITY_ID,
        "LEGACY_PARALLEL_AUTHORITY_ABSENT": bool(claims.get("LEGACY_PARALLEL_AUTHORITY_ABSENT")),
        "result_path": str(result_path.relative_to(root)),
    }


def prove_cap72_activation_v1(*, repo_root: Path | None = None) -> dict[str, Any]:
    root = Path(repo_root) if repo_root is not None else repo_root_v1()
    status_path = (
        root
        / "docs/evidence/capability_7_2_single_future_stateful_no_order_runtime_activation_v1"
        / "productive_binding"
        / "activation_status_v1.json"
    )
    result_path = (
        root
        / "docs/evidence/capability_7_2_single_future_stateful_no_order_runtime_activation_v1"
        / "productive_binding"
        / "single_future_stateful_no_order_runtime_activation_result_v1.json"
    )
    summary_path = (
        root
        / "docs/evidence/capability_7_2_single_future_stateful_no_order_runtime_activation_v1"
        / "SUMMARY.json"
    )
    if not status_path.is_file() or not result_path.is_file():
        return {
            "ok": False,
            "FULL_CANONICAL_STATEFUL_RUNTIME_ACTIVE": False,
            "SIMULATED_EXECUTION_ACTIVE": False,
            "gap": "missing_cap72_evidence",
        }
    status = _read_json(status_path)
    result = _read_json(result_path)
    summary = _read_json(summary_path) if summary_path.is_file() else {}
    activation_cfg = load_activation_config_v1(
        config_path=root
        / "config/runtime/single_future_stateful_no_order_runtime_activation_v1.json"
    )
    active = (
        bool(status.get("FULL_CANONICAL_STATEFUL_RUNTIME_ACTIVE"))
        and bool(result.get("FULL_CANONICAL_STATEFUL_RUNTIME_ACTIVE"))
        and bool(activation_cfg.full_canonical_stateful_runtime_active)
    )
    sim = (
        bool(status.get("SIMULATED_EXECUTION_ACTIVE"))
        and bool(result.get("SIMULATED_EXECUTION_ACTIVE"))
        and bool(activation_cfg.simulated_execution_active)
    )
    return {
        "ok": active and sim and bool(result.get("ok", True)) and bool(summary.get("ok", True)),
        "FULL_CANONICAL_STATEFUL_RUNTIME_ACTIVE": active,
        "SIMULATED_EXECUTION_ACTIVE": sim,
        "PUBLIC_MD_RUNTIME_CAPABLE": bool(status.get("PUBLIC_MD_RUNTIME_CAPABLE")),
        "PUBLIC_MD_NETWORK_SESSION_OBSERVED": bool(
            status.get("PUBLIC_MD_NETWORK_SESSION_OBSERVED")
        ),
        "activation_status": status.get("status"),
        "activation_config_digest": activation_cfg.config_digest,
        "capability_id": result.get("capability_id"),
        "expected_capability_id": ACTIVATION_CAPABILITY_ID,
        "instrument_id": status.get("instrument_id"),
        "runtime_mode": status.get("runtime_mode"),
        "NETWORK_SESSION_STARTED": bool(status.get("NETWORK_SESSION_STARTED")),
        "activation_contract_owner": "ops.single_future_stateful_no_order_runtime_activation_v1",
    }


def prove_phase92_prerequisites_v1(
    *,
    repository_sha: str,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    root = Path(repo_root) if repo_root is not None else repo_root_v1()
    phase91 = prove_phase91_closed_v1(repo_root=root)
    cap72 = prove_cap72_activation_v1(repo_root=root)
    pre = prove_preconditions_v1(repository_sha=repository_sha)
    matrix = dict(pre.get("matrix") or {})

    required_true = {
        "C1_PRODUCTIVELY_BOUND": bool(matrix.get("C1_PRODUCTIVELY_BOUND")),
        "C2_PRODUCTIVELY_BOUND": bool(matrix.get("C2_PRODUCTIVELY_BOUND")),
        "C3_PRODUCTIVELY_BOUND": bool(matrix.get("C3_PRODUCTIVELY_BOUND")),
        "CONFIRMATION_STATE_PERSISTED": bool(matrix.get("CONFIRMATION_STATE_PERSISTED")),
        "CONFIRMATION_SESSION_ID_STABLE": bool(matrix.get("CONFIRMATION_SESSION_ID_STABLE")),
        "DYNAMIC_SCOPE_STATE_PERSISTED": bool(matrix.get("DYNAMIC_SCOPE_STATE_PERSISTED")),
        "DECISION_PATH_RESTART_PROVEN": bool(matrix.get("DECISION_PATH_RESTART_PROVEN")),
        "EXIT_POLICY_PRODUCERS_BOUND": bool(matrix.get("EXIT_POLICY_PRODUCERS_BOUND")),
        "ENTRY_END_TO_END_EVIDENCE_PROVEN": bool(matrix.get("ENTRY_END_TO_END_EVIDENCE_PROVEN")),
        "EXIT_END_TO_END_EVIDENCE_PROVEN": bool(matrix.get("EXIT_END_TO_END_EVIDENCE_PROVEN")),
        "NONZERO_FEE_EVIDENCE_PROVEN": bool(matrix.get("NONZERO_FEE_EVIDENCE_PROVEN")),
        "NONZERO_SLIPPAGE_EVIDENCE_PROVEN": bool(matrix.get("NONZERO_SLIPPAGE_EVIDENCE_PROVEN")),
        "RECONCILIATION_BEFORE_ALPHA": bool(matrix.get("RECONCILIATION_BEFORE_ALPHA")),
        "CONFIG_TRUTH_ALIGNED": bool(matrix.get("CONFIG_TRUTH_ALIGNED")),
        "EVIDENCE_VERIFIER_PASS": bool(matrix.get("EVIDENCE_VERIFIER_PASS")),
        "LEGACY_PARALLEL_AUTHORITY_ABSENT": bool(matrix.get("LEGACY_PARALLEL_AUTHORITY_ABSENT"))
        and bool(phase91.get("LEGACY_PARALLEL_AUTHORITY_ABSENT")),
    }
    gaps = [k for k, v in required_true.items() if not v]
    if not phase91.get("ok"):
        gaps.append("PHASE_9_1_NOT_CLOSED")
    if not cap72.get("ok"):
        gaps.append("CAP72_ACTIVATION_NOT_PROVEN")
    if not bool(pre.get("ok")):
        gaps.append("CAP72_PRECONDITION_MATRIX_NOT_OK")
    if bool(cap72.get("NETWORK_SESSION_STARTED")):
        gaps.append("NETWORK_SESSION_ALREADY_STARTED")
    if bool(cap72.get("PUBLIC_MD_NETWORK_SESSION_OBSERVED")):
        gaps.append("PUBLIC_MD_NETWORK_SESSION_ALREADY_OBSERVED")

    ok = not gaps
    return {
        "ok": ok,
        "gaps": gaps,
        "PHASE_9_1_CLOSED": bool(phase91.get("PHASE_9_1_CLOSED")),
        "STRATEGY_REGISTRY_CLOSED": bool(phase91.get("STRATEGY_REGISTRY_CLOSED")),
        "FULL_CANONICAL_STATEFUL_RUNTIME_ACTIVE": bool(
            cap72.get("FULL_CANONICAL_STATEFUL_RUNTIME_ACTIVE")
        ),
        "SIMULATED_EXECUTION_ACTIVE": bool(cap72.get("SIMULATED_EXECUTION_ACTIVE")),
        "activation_contract": cap72,
        "phase91": phase91,
        "cap72_precondition_matrix": pre,
        "required_true": required_true,
        "PHASE_9_2_PREREQUISITES_PROVEN": ok,
    }
