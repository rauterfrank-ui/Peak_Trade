"""Materialize Phase 9.2 public-MD smoke session preflight evidence offline."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict

from src.ops.phase_9_2_public_md_session_preflight_v1.authorization_path_v1 import (
    prove_authorization_and_confirm_token_path_v1,
)
from src.ops.phase_9_2_public_md_session_preflight_v1.constants_v1 import (
    AUTH_PATH_FILENAME,
    CAPABILITY_ID,
    CLAIM_MATRIX_FILENAME,
    CONFIG_RELATIVE_PATH,
    EVIDENCE_DIRNAME,
    EVIDENCE_FILENAME,
    EVIDENCE_SUBDIR,
    FAILURE_INJECTION_FILENAME,
    MANIFEST_FILENAME,
    NETWORK_PROOF_FILENAME,
    PACING_PROOF_FILENAME,
    PARITY_PROOF_FILENAME,
    PREREQUISITE_MATRIX_FILENAME,
    READINESS_FILENAME,
    RESTART_PROOF_FILENAME,
    RESULT_FILENAME,
    SESSION_LADDER,
    SESSION_LADDER_FILENAME,
    SMOKE_CONTRACT_FILENAME,
    TASK_ID,
    repo_root_v1,
)
from src.ops.phase_9_2_public_md_session_preflight_v1.failure_injection_v1 import (
    run_failure_injections_v1,
)
from src.ops.phase_9_2_public_md_session_preflight_v1.models_v1 import (
    PreflightClaimsV1,
    PreflightEvidenceV1,
)
from src.ops.phase_9_2_public_md_session_preflight_v1.network_boundary_v1 import (
    prove_phase92_network_and_execution_boundary_v1,
)
from src.ops.phase_9_2_public_md_session_preflight_v1.pacing_safety_v1 import (
    prove_pacing_and_staleness_safety_v1,
)
from src.ops.phase_9_2_public_md_session_preflight_v1.parity_v1 import prove_phase92_parity_v1
from src.ops.phase_9_2_public_md_session_preflight_v1.prerequisites_v1 import (
    prove_phase92_prerequisites_v1,
)
from src.ops.phase_9_2_public_md_session_preflight_v1.restart_evidence_v1 import (
    prove_state_restart_evidence_preflight_v1,
)
from src.ops.phase_9_2_public_md_session_preflight_v1.smoke_session_contract_v1 import (
    build_smoke_session_contract_v1,
    validate_smoke_session_contract_v1,
)


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _write_json(path: Path, payload: Dict[str, Any]) -> str:
    text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return _sha256_bytes(text.encode("utf-8"))


def _write_manifest(dir_path: Path, digests: Dict[str, str]) -> None:
    lines = [f"{digest}  {name}" for name, digest in sorted(digests.items())]
    (dir_path / MANIFEST_FILENAME).write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_preflight_evidence_v1(
    *,
    repository_sha: str,
    repo_root: Path | None = None,
    materialize: bool = True,
) -> PreflightEvidenceV1:
    root = Path(repo_root) if repo_root is not None else repo_root_v1()
    gaps: list[str] = []

    prerequisites = prove_phase92_prerequisites_v1(repository_sha=repository_sha, repo_root=root)
    if not prerequisites.get("ok"):
        gaps.extend(list(prerequisites.get("gaps") or ["PREREQUISITES_FAILED"]))

    contract = build_smoke_session_contract_v1(repository_sha=repository_sha, repo_root=root)
    contract_gaps = validate_smoke_session_contract_v1(contract)
    if contract_gaps:
        gaps.extend(contract_gaps)

    network = prove_phase92_network_and_execution_boundary_v1()
    if not network.get("ok"):
        gaps.append("NETWORK_OR_EXECUTION_BOUNDARY_FAILED")

    pacing = prove_pacing_and_staleness_safety_v1(contract=contract)
    if not pacing.get("ok"):
        gaps.append("PACING_OR_STALENESS_FAILED")

    auth_path = prove_authorization_and_confirm_token_path_v1(repo_root=root)
    if not auth_path.get("ok"):
        gaps.append("AUTHORIZATION_PATH_FAILED")

    restart = prove_state_restart_evidence_preflight_v1(contract=contract, repo_root=root)
    if not restart.get("ok"):
        gaps.append("STATE_RESTART_EVIDENCE_FAILED")

    parity = prove_phase92_parity_v1()
    if not parity.get("ok"):
        gaps.append("PARITY_FAILED")

    failures = run_failure_injections_v1(contract=contract)
    if not failures.get("ok"):
        gaps.append("FAILURE_INJECTION_FAILED")

    session_ladder = {
        "ok": True,
        "SESSION_LADDER_DEFINED": True,
        "ladder": list(SESSION_LADDER),
        "current_allowed_step": "SMOKE_SESSION",
        "note": "Only smoke-session preparation is authorized by this preflight task.",
    }

    ready = not gaps
    claims = PreflightClaimsV1(
        PHASE_9_1_CLOSED=bool(prerequisites.get("PHASE_9_1_CLOSED")),
        STRATEGY_REGISTRY_CLOSED=bool(prerequisites.get("STRATEGY_REGISTRY_CLOSED")),
        PHASE_9_2_PREREQUISITES_PROVEN=bool(prerequisites.get("PHASE_9_2_PREREQUISITES_PROVEN")),
        FULL_CANONICAL_STATEFUL_RUNTIME_ACTIVE=bool(
            prerequisites.get("FULL_CANONICAL_STATEFUL_RUNTIME_ACTIVE")
        ),
        SIMULATED_EXECUTION_ACTIVE=bool(prerequisites.get("SIMULATED_EXECUTION_ACTIVE")),
        RECONCILIATION_BEFORE_ALPHA=bool(restart.get("RECONCILIATION_BEFORE_ALPHA")),
        PUBLIC_MD_ONLY_BOUNDARY_PROVEN=bool(network.get("PUBLIC_MD_ONLY_BOUNDARY_PROVEN")),
        GET_ONLY_PROVEN=bool(network.get("GET_ONLY_PROVEN")),
        PRIVATE_ENDPOINT_REACHABLE=bool(network.get("PRIVATE_ENDPOINT_REACHABLE")),
        AUTH_HEADER_PRESENT=bool(network.get("AUTH_HEADER_PRESENT")),
        REAL_EXECUTION_ADAPTER_CONSTRUCTED=bool(network.get("REAL_EXECUTION_ADAPTER_CONSTRUCTED")),
        EXCHANGE_ORDER_SUBMIT_REACHABLE=bool(network.get("EXCHANGE_ORDER_SUBMIT_REACHABLE")),
        EXCHANGE_CREDENTIAL_ACCESS_REACHABLE=bool(
            network.get("EXCHANGE_CREDENTIAL_ACCESS_REACHABLE")
        ),
        PAPER_EXCHANGE_EXECUTION_REACHABLE=bool(network.get("PAPER_EXCHANGE_EXECUTION_REACHABLE")),
        LIVE_PATH_REACHABLE=bool(network.get("LIVE_PATH_REACHABLE")),
        TESTNET_PATH_REACHABLE=bool(network.get("TESTNET_PATH_REACHABLE")),
        NO_ZERO_INTERVAL_REQUEST_BURST=bool(pacing.get("NO_ZERO_INTERVAL_REQUEST_BURST")),
        EXPLICIT_PACING_BUDGET=bool(pacing.get("EXPLICIT_PACING_BUDGET")),
        BOUNDED_RETRY=bool(pacing.get("BOUNDED_RETRY")),
        BOUNDED_BACKOFF=bool(pacing.get("BOUNDED_BACKOFF")),
        HTTP_429_CLASSIFIED=bool(pacing.get("HTTP_429_CLASSIFIED")),
        STALENESS_GATE_PROVEN=bool(pacing.get("STALENESS_GATE_PROVEN")),
        CONFIRMATION_SESSION_ID_STABLE=bool(restart.get("CONFIRMATION_SESSION_ID_STABLE")),
        RUNTIME_SESSION_ID_STABLE=bool(restart.get("RUNTIME_SESSION_ID_STABLE")),
        DECISION_STATE_PERSISTENCE_PROVEN=bool(restart.get("DECISION_STATE_PERSISTENCE_PROVEN")),
        RESTART_SEMANTICS_PROVEN=bool(restart.get("RESTART_SEMANTICS_PROVEN")),
        NO_DUPLICATE_CONFIRMATION_ADVANCE=bool(restart.get("NO_DUPLICATE_CONFIRMATION_ADVANCE")),
        NO_DUPLICATE_FILL=bool(restart.get("NO_DUPLICATE_FILL")),
        EVIDENCE_RECOVERY_IDEMPOTENT=bool(restart.get("EVIDENCE_RECOVERY_IDEMPOTENT")),
        SESSION_LADDER_DEFINED=True,
        SMOKE_SESSION_CONTRACT_CREATED=not bool(contract_gaps),
        SESSION_PREREGISTRATION_READY=ready and not bool(contract_gaps),
        AUTHORIZATION_PATH_IDENTIFIED=bool(auth_path.get("AUTHORIZATION_PATH_IDENTIFIED")),
        CONFIRM_TOKEN_CANONICAL_PATH_IDENTIFIED=bool(
            auth_path.get("CONFIRM_TOKEN_CANONICAL_PATH_IDENTIFIED")
        ),
        CONFIRM_TOKEN_PLAINTEXT_EXPOSED=bool(auth_path.get("CONFIRM_TOKEN_PLAINTEXT_EXPOSED")),
        CORE_LOGIC_CHANGED=bool(parity.get("CORE_LOGIC_CHANGED")),
        GOLDEN_VECTOR_PARITY_PASS=bool(parity.get("GOLDEN_VECTOR_PARITY_PASS")),
        CALL_ORDER_PARITY_PROVEN=bool(parity.get("CALL_ORDER_PARITY_PROVEN")),
        INPUT_OUTPUT_PARITY_PROVEN=bool(parity.get("INPUT_OUTPUT_PARITY_PROVEN")),
        STATE_TRANSITION_PARITY_PROVEN=bool(parity.get("STATE_TRANSITION_PARITY_PROVEN")),
        DECISION_REASON_PARITY_PROVEN=bool(parity.get("DECISION_REASON_PARITY_PROVEN")),
        RISK_PARITY_PROVEN=bool(parity.get("RISK_PARITY_PROVEN")),
        SAFETY_PARITY_PROVEN=bool(parity.get("SAFETY_PARITY_PROVEN")),
        EXIT_PRECEDENCE_PARITY_PROVEN=bool(parity.get("EXIT_PRECEDENCE_PARITY_PROVEN")),
        PHASE_9_2_SMOKE_SESSION_PREFLIGHT_READY=ready,
    )

    evidence = PreflightEvidenceV1(
        ok=ready,
        capability_id=CAPABILITY_ID,
        task_id=TASK_ID,
        repository_sha=repository_sha,
        smoke_contract_digest=contract.smoke_contract_digest,
        activation_config_digest=contract.activation_config_digest,
        claims=claims.to_dict(),
        gaps=gaps,
    )

    if materialize:
        out_dir = root / "docs" / "evidence" / EVIDENCE_DIRNAME / EVIDENCE_SUBDIR
        digests: Dict[str, str] = {}
        digests[SMOKE_CONTRACT_FILENAME] = _write_json(
            out_dir / SMOKE_CONTRACT_FILENAME, contract.to_dict()
        )
        digests[SESSION_LADDER_FILENAME] = _write_json(
            out_dir / SESSION_LADDER_FILENAME, session_ladder
        )
        digests[PREREQUISITE_MATRIX_FILENAME] = _write_json(
            out_dir / PREREQUISITE_MATRIX_FILENAME, prerequisites
        )
        digests[NETWORK_PROOF_FILENAME] = _write_json(out_dir / NETWORK_PROOF_FILENAME, network)
        digests[PACING_PROOF_FILENAME] = _write_json(out_dir / PACING_PROOF_FILENAME, pacing)
        digests[AUTH_PATH_FILENAME] = _write_json(out_dir / AUTH_PATH_FILENAME, auth_path)
        digests[RESTART_PROOF_FILENAME] = _write_json(out_dir / RESTART_PROOF_FILENAME, restart)
        digests[PARITY_PROOF_FILENAME] = _write_json(out_dir / PARITY_PROOF_FILENAME, parity)
        digests[FAILURE_INJECTION_FILENAME] = _write_json(
            out_dir / FAILURE_INJECTION_FILENAME, failures
        )
        digests[CLAIM_MATRIX_FILENAME] = _write_json(
            out_dir / CLAIM_MATRIX_FILENAME, claims.to_dict()
        )
        readiness = {
            "ok": ready,
            "PHASE_9_2_SMOKE_SESSION_PREFLIGHT_READY": ready,
            "gaps": gaps,
            "smoke_session_id": contract.session_id,
            "smoke_contract_digest": contract.smoke_contract_digest,
            "repository_sha": repository_sha,
            "network_session_authorized": False,
            "authorization_issuance_authorized": False,
            "authorization_consumption_authorized": False,
            "runtime_start_authorized": False,
            "next_safe_step": (
                "Separate Owner-GO for authorization issuance + smoke session execution "
                "with NETWORK_SESSION_ALLOWED=true and AUTHORIZATION_ISSUANCE_ALLOWED=true; "
                "do not start network or consume authorization from this preflight."
            ),
        }
        digests[READINESS_FILENAME] = _write_json(out_dir / READINESS_FILENAME, readiness)
        result = {
            "ok": ready,
            "capability_id": CAPABILITY_ID,
            "task_id": TASK_ID,
            "PHASE_9_2_SMOKE_SESSION_PREFLIGHT_READY": ready,
            "smoke_contract_digest": contract.smoke_contract_digest,
            "activation_config_digest": contract.activation_config_digest,
            "repository_sha": repository_sha,
            "claims": claims.to_dict(),
            "gaps": gaps,
        }
        digests[RESULT_FILENAME] = _write_json(out_dir / RESULT_FILENAME, result)
        evidence_payload = evidence.to_dict()
        digests[EVIDENCE_FILENAME] = _write_json(out_dir / EVIDENCE_FILENAME, evidence_payload)
        evidence.evidence_digest = digests[EVIDENCE_FILENAME]
        # Rewrite evidence with digest filled.
        digests[EVIDENCE_FILENAME] = _write_json(out_dir / EVIDENCE_FILENAME, evidence.to_dict())
        _write_manifest(out_dir, digests)

        # Canonical config mirror (preregistration draft for later Owner-GO).
        config_path = root / CONFIG_RELATIVE_PATH
        _write_json(config_path, contract.to_dict())

        summary = {
            "ok": ready,
            "capability_id": CAPABILITY_ID,
            "task_id": TASK_ID,
            "PHASE_9_2_SMOKE_SESSION_PREFLIGHT_READY": ready,
            "repository_sha": repository_sha,
            "smoke_contract_digest": contract.smoke_contract_digest,
            "evidence_digest": evidence.evidence_digest,
        }
        _write_json(root / "docs" / "evidence" / EVIDENCE_DIRNAME / "SUMMARY.json", summary)
        # Top-level manifest points at preflight artifacts.
        top_manifest = {
            SMOKE_CONTRACT_FILENAME: digests[SMOKE_CONTRACT_FILENAME],
            RESULT_FILENAME: digests[RESULT_FILENAME],
            EVIDENCE_FILENAME: digests[EVIDENCE_FILENAME],
            READINESS_FILENAME: digests[READINESS_FILENAME],
        }
        _write_manifest(
            root / "docs" / "evidence" / EVIDENCE_DIRNAME,
            {f"preflight/{k}": v for k, v in top_manifest.items()},
        )

    return evidence
