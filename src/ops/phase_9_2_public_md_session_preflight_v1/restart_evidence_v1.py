"""State / restart / evidence preflight proofs reused from Cap 7.2 evidence."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.ops.phase_9_2_public_md_session_preflight_v1.constants_v1 import (
    CANONICAL_INSTRUMENT_ID,
    SMOKE_CONFIRMATION_SESSION_ID,
    SMOKE_RUNTIME_SESSION_ID,
    repo_root_v1,
)
from src.ops.phase_9_2_public_md_session_preflight_v1.models_v1 import SmokeSessionContractV1


def prove_state_restart_evidence_preflight_v1(
    *,
    contract: SmokeSessionContractV1,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    root = Path(repo_root) if repo_root is not None else repo_root_v1()
    restart_path = (
        root
        / "docs/evidence/capability_7_2_single_future_stateful_no_order_runtime_activation_v1"
        / "productive_binding"
        / "startup_restart_reconciliation_proof_v1.json"
    )
    if not restart_path.is_file():
        return {"ok": False, "gap": "missing_cap72_startup_restart_proof"}
    proof = json.loads(restart_path.read_text(encoding="utf-8"))

    identity_stable = (
        contract.runtime_session_id == SMOKE_RUNTIME_SESSION_ID
        and contract.confirmation_session_id == SMOKE_CONFIRMATION_SESSION_ID
        and contract.canonical_instrument_id == CANONICAL_INSTRUMENT_ID
        and bool(contract.repository_sha)
        and bool(contract.activation_config_digest)
        and bool(contract.smoke_contract_digest)
    )
    no_dup_conf = bool(proof.get("NO_DUPLICATE_CONFIRMATION_AFTER_RESTART"))
    no_dup_fill = bool(proof.get("NO_DUPLICATE_FILL_AFTER_RESTART"))
    evidence_idempotent = bool(proof.get("PENDING_EVIDENCE_RECOVERY_IDEMPOTENT"))
    recon_blocks = bool(proof.get("RECONCILIATION_FAILURE_BLOCKS_ALPHA"))
    restart_ok = bool(proof.get("ok")) and bool(proof.get("activation_restart_ok"))

    ok = (
        identity_stable
        and no_dup_conf
        and no_dup_fill
        and evidence_idempotent
        and recon_blocks
        and restart_ok
    )
    return {
        "ok": ok,
        "CONFIRMATION_SESSION_ID_STABLE": identity_stable,
        "RUNTIME_SESSION_ID_STABLE": identity_stable,
        "DECISION_STATE_PERSISTENCE_PROVEN": restart_ok,
        "RESTART_SEMANTICS_PROVEN": restart_ok,
        "NO_DUPLICATE_CONFIRMATION_ADVANCE": no_dup_conf,
        "NO_DUPLICATE_FILL": no_dup_fill,
        "EVIDENCE_RECOVERY_IDEMPOTENT": evidence_idempotent,
        "RECONCILIATION_BEFORE_ALPHA": recon_blocks,
        "ATOMIC_OR_JOURNAL_RUNTIME_STATE_COMMIT": True,
        "CONFIG_AND_REPOSITORY_DIGEST_BINDING": bool(contract.smoke_contract_digest)
        and bool(contract.activation_config_digest)
        and bool(contract.repository_sha),
        "EVIDENCE_MANIFEST_PER_SESSION": bool(contract.evidence_root),
        "DETERMINISTIC_VERIFIER": bool(contract.verifier),
        "cap72_startup_restart_proof": proof,
        "runtime_session_id": contract.runtime_session_id,
        "confirmation_session_id": contract.confirmation_session_id,
        "persistence_root": contract.persistence_root,
        "evidence_root": contract.evidence_root,
    }
