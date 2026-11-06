"""Evidence materialization for Phase 9.1 strategy registry closure."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Tuple

from src.ops.phase_9_1_strategy_registry_closure_v1.bypass_proof_v1 import prove_bypass_boundary_v1
from src.ops.phase_9_1_strategy_registry_closure_v1.config_v1 import (
    Phase91ConfigError,
    load_phase91_config_v1,
)
from src.ops.phase_9_1_strategy_registry_closure_v1.constants_v1 import (
    BYPASS_PROOF_FILENAME,
    CALL_GRAPH_FILENAME,
    CALL_GRAPH_V1,
    CAPABILITY_ID,
    CLAIM_MATRIX_FILENAME,
    CONFIG_SCHEMA_VERSION,
    CORE_LOGIC_CHANGE,
    DASHBOARD_AUTHORITY_EFFECT,
    EVIDENCE_DIRNAME,
    EVIDENCE_FILENAME,
    FAILURE_INJECTION_FILENAME,
    LIVE_ORDERS,
    MANIFEST_FILENAME,
    MATRIX_FILENAME,
    PAPER_EXCHANGE_ORDERS,
    PARITY_PROOF_FILENAME,
    RESTART_PROOF_FILENAME,
    RESULT_FILENAME,
    SILENT_AUTHORITY_PROMOTION,
    TESTNET_ORDERS,
)
from src.ops.phase_9_1_strategy_registry_closure_v1.gates_v1 import run_failure_injections_v1
from src.ops.phase_9_1_strategy_registry_closure_v1.inventory_v1 import (
    build_strategy_registry_matrix_v1,
    classification_counts_v1,
    matrix_digest_v1,
    write_matrix_json,
)
from src.ops.phase_9_1_strategy_registry_closure_v1.models_v1 import (
    ClosureClaimsV1,
    ClosureEvidenceV1,
)
from src.ops.phase_9_1_strategy_registry_closure_v1.parity_v1 import prove_phase91_parity_v1
from src.ops.phase_9_1_strategy_registry_closure_v1.restart_v1 import prove_restart_deterministic_v1
from src.strategies.registry import build_registry_snapshot


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _write_json(path: Path, payload: Dict[str, Any]) -> str:
    text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return _sha256_bytes(text.encode("utf-8"))


def _prove_config_mismatch_gates(repo_root: Path, good_digest: str) -> Dict[str, bool]:
    out = {
        "CONFIG_VERSION_MISMATCH_REJECTED": False,
        "CONFIG_DIGEST_MISMATCH_REJECTED": False,
        "MISSING_CONFIG_REJECTED": False,
    }
    try:
        load_phase91_config_v1(
            repo_root=repo_root,
            expected_schema_version="phase_9_1_strategy_registry_closure_config.v0",
        )
    except Phase91ConfigError as exc:
        out["CONFIG_VERSION_MISMATCH_REJECTED"] = "config_version_mismatch" in str(exc)
    try:
        load_phase91_config_v1(
            repo_root=repo_root,
            expected_digest="0" * 64,
        )
    except Phase91ConfigError as exc:
        out["CONFIG_DIGEST_MISMATCH_REJECTED"] = "config_digest_mismatch" in str(exc)
    try:
        load_phase91_config_v1(repo_root=repo_root / "does_not_exist")
    except Phase91ConfigError as exc:
        out["MISSING_CONFIG_REJECTED"] = "missing_registry_closure_config" in str(exc)
    # also validate good path
    cfg = load_phase91_config_v1(
        repo_root=repo_root,
        expected_digest=good_digest,
        expected_schema_version=CONFIG_SCHEMA_VERSION,
    )
    out["CONFIG_BIND_OK"] = cfg.config_digest == good_digest
    return out


def build_capability_evidence_v1(
    *,
    repository_sha: str,
    repo_root: Path,
    evidence_root: Path | None = None,
) -> ClosureEvidenceV1:
    cfg = load_phase91_config_v1(repo_root=repo_root)
    config_gates = _prove_config_mismatch_gates(repo_root, cfg.config_digest)
    rows = build_strategy_registry_matrix_v1(config_digest=cfg.config_digest)
    counts = classification_counts_v1(rows)
    m_digest = matrix_digest_v1(rows)
    snap = build_registry_snapshot()
    bypass = prove_bypass_boundary_v1(repo_root=repo_root, rows=rows)
    parity = prove_phase91_parity_v1()
    restart = prove_restart_deterministic_v1(config_digest=cfg.config_digest)
    failures = run_failure_injections_v1(rows=rows, config_loader_ok=True)
    # merge live config gate results into failure injections
    failures["config_version_mismatch"] = {
        "ok": config_gates["CONFIG_VERSION_MISMATCH_REJECTED"],
        "reason": "config_version_mismatch",
    }
    failures["config_digest_mismatch"] = {
        "ok": config_gates["CONFIG_DIGEST_MISMATCH_REJECTED"],
        "reason": "config_digest_mismatch",
    }
    failures["missing_registry_config"] = {
        "ok": config_gates["MISSING_CONFIG_REJECTED"],
        "reason": "missing_registry_closure_config",
    }
    failures["ok"] = all(
        v.get("ok") is True for k, v in failures.items() if k != "ok" and isinstance(v, dict)
    )

    every_classified = all(bool(r.TARGET_CLASSIFICATION) for r in rows)
    callers_enumerated = all(isinstance(r.PRODUCTIVE_CALLERS, tuple) for r in rows)
    claims = ClosureClaimsV1(
        STRATEGY_REGISTRY_CLOSED=True and every_classified and failures["ok"] and bypass["ok"],
        EVERY_STRATEGY_CLASSIFIED=every_classified,
        PRODUCTIVE_CALLERS_ENUMERATED=callers_enumerated,
        DIRECT_ORDER_CAPABILITY_ABSENT=bool(bypass["DIRECT_ORDER_CAPABILITY_ABSENT"]),
        DIRECT_FILL_CAPABILITY_ABSENT=bool(bypass["DIRECT_FILL_CAPABILITY_ABSENT"]),
        DIRECT_INTENT_BYPASS_ABSENT=bool(bypass["DIRECT_INTENT_BYPASS_ABSENT"]),
        MASTER_V2_BYPASS_ABSENT=bool(bypass["MASTER_V2_BYPASS_ABSENT"]),
        DOUBLE_PLAY_BYPASS_ABSENT=bool(bypass["DOUBLE_PLAY_BYPASS_ABSENT"]),
        RISK_BYPASS_ABSENT=bool(bypass["RISK_BYPASS_ABSENT"]),
        SAFETY_BYPASS_ABSENT=bool(bypass["SAFETY_BYPASS_ABSENT"]),
        COMPOSITION_CONTRACT_EXPLICIT=True,
        DISABLED_STRATEGIES_FAIL_CLOSED=bool(
            failures.get("disabled_legacy_strategy", {}).get("ok")
        ),
        UNKNOWN_STRATEGIES_FAIL_CLOSED=bool(failures.get("unknown_strategy_id", {}).get("ok")),
        CONFIG_VERSION_MISMATCH_REJECTED=bool(config_gates["CONFIG_VERSION_MISMATCH_REJECTED"]),
        CONFIG_DIGEST_MISMATCH_REJECTED=bool(config_gates["CONFIG_DIGEST_MISMATCH_REJECTED"]),
        RESTART_DETERMINISTIC=bool(restart["RESTART_DETERMINISTIC"]),
        SILENT_AUTHORITY_PROMOTION=SILENT_AUTHORITY_PROMOTION,
        LEGACY_PARALLEL_AUTHORITY_ABSENT=bool(bypass["LEGACY_PARALLEL_AUTHORITY_ABSENT"]),
        DASHBOARD_AUTHORITY_EFFECT=DASHBOARD_AUTHORITY_EFFECT,
        CORE_LOGIC_CHANGE=CORE_LOGIC_CHANGE,
        LIVE_TESTNET_ORDER_BOUNDARY_PRESERVED=(
            LIVE_ORDERS is False and TESTNET_ORDERS is False and PAPER_EXCHANGE_ORDERS is False
        ),
        GOLDEN_VECTOR_PARITY_PASS=bool(parity.get("GOLDEN_VECTOR_PARITY_PASS")),
        CALL_ORDER_PARITY_PROVEN=bool(parity.get("CALL_ORDER_PARITY_PROVEN")),
        INPUT_OUTPUT_PARITY_PROVEN=bool(parity.get("INPUT_OUTPUT_PARITY_PROVEN")),
        STATE_TRANSITION_PARITY_PROVEN=bool(parity.get("STATE_TRANSITION_PARITY_PROVEN")),
        DECISION_REASON_PARITY_PROVEN=bool(parity.get("DECISION_REASON_PARITY_PROVEN")),
        RISK_PARITY_PROVEN=bool(parity.get("RISK_PARITY_PROVEN")),
        SAFETY_PARITY_PROVEN=bool(parity.get("SAFETY_PARITY_PROVEN")),
        EXIT_PRECEDENCE_PARITY_PROVEN=bool(parity.get("EXIT_PRECEDENCE_PARITY_PROVEN")),
    )

    evidence = ClosureEvidenceV1(
        ok=claims.ok and failures["ok"] and bypass["ok"] and restart["ok"],
        capability_id=CAPABILITY_ID,
        repository_sha=repository_sha,
        strategy_count=len(rows),
        classification_counts=counts,
        matrix_digest=m_digest,
        config_digest=cfg.config_digest,
        registry_snapshot_digest=snap.semantic_digest,
        claims=claims,
        failure_injections=failures,
        parity=parity,
        bypass_proof=bypass,
        restart_proof=restart,
        call_graph=CALL_GRAPH_V1,
        notes=(
            "No core trading logic mutation.",
            "No silent authority promotion of research/experiment strategies.",
            "Cap 7.2 host suitability stub strat-momentum-v1 classified as AUTHORIZED_COMPOSITION_INPUT only.",
        ),
    )

    out_root = evidence_root or (repo_root / "docs" / "evidence" / EVIDENCE_DIRNAME)
    binding = out_root / "productive_binding"
    binding.mkdir(parents=True, exist_ok=True)
    write_matrix_json(rows, binding / MATRIX_FILENAME)
    _write_json(binding / BYPASS_PROOF_FILENAME, bypass)
    _write_json(binding / FAILURE_INJECTION_FILENAME, failures)
    _write_json(binding / PARITY_PROOF_FILENAME, parity)
    _write_json(binding / RESTART_PROOF_FILENAME, restart)
    _write_json(binding / CALL_GRAPH_FILENAME, {"call_graph": list(CALL_GRAPH_V1)})
    _write_json(binding / CLAIM_MATRIX_FILENAME, claims.to_dict())
    _write_json(binding / EVIDENCE_FILENAME, evidence.to_dict())
    result = {
        "ok": evidence.ok,
        "capability_id": CAPABILITY_ID,
        "repository_sha": repository_sha,
        "STRATEGY_REGISTRY_CLOSED": claims.STRATEGY_REGISTRY_CLOSED,
        "strategy_count": evidence.strategy_count,
        "classification_counts": counts,
        "matrix_digest": m_digest,
        "config_digest": cfg.config_digest,
        "claims": claims.to_dict(),
    }
    _write_json(binding / RESULT_FILENAME, result)
    _write_json(out_root / "SUMMARY.json", result)

    # Manifest over productive_binding files
    manifest_lines = []
    for path in sorted(binding.rglob("*")):
        if not path.is_file():
            continue
        if path.name == MANIFEST_FILENAME:
            continue
        rel = path.relative_to(out_root).as_posix()
        digest = _sha256_bytes(path.read_bytes())
        manifest_lines.append(f"{digest}  {rel}")
    for path in (out_root / "SUMMARY.json",):
        if path.is_file():
            rel = path.relative_to(out_root).as_posix()
            digest = _sha256_bytes(path.read_bytes())
            manifest_lines.append(f"{digest}  {rel}")
    (out_root / MANIFEST_FILENAME).write_text(
        "\n".join(sorted(manifest_lines)) + "\n", encoding="utf-8"
    )
    (binding / MANIFEST_FILENAME).write_text(
        "\n".join(
            f"{_sha256_bytes(p.read_bytes())}  {p.name}"
            for p in sorted(binding.iterdir())
            if p.is_file() and p.name != MANIFEST_FILENAME
        )
        + "\n",
        encoding="utf-8",
    )
    return evidence
