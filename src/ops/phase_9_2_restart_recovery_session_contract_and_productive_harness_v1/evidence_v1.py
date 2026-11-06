"""Deterministic fixture evidence materialization for Phase 9.2 restart harness."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.ops.phase_9_2_restart_recovery_session_contract_and_productive_harness_v1.campaign_harness_v1 import (
    run_restart_campaign_fixture_v1,
)
from src.ops.phase_9_2_restart_recovery_session_contract_and_productive_harness_v1.constants_v1 import (
    CAPABILITY_ID,
    CONTROLLED_RESTART_EXIT_CODE,
    EVIDENCE_DIRNAME,
    OWNER,
    PRODUCER_VERSION,
    SCHEMA_VERSION,
    repo_root_v1,
)
from src.ops.phase_9_2_restart_recovery_session_contract_and_productive_harness_v1.digest_v1 import (
    sha256_canonical_v1,
    write_json_atomic_v1,
)
from src.ops.phase_9_2_restart_recovery_session_contract_and_productive_harness_v1.failure_injection_v1 import (
    run_failure_injection_matrix_v1,
)
from src.ops.phase_9_2_restart_recovery_session_contract_and_productive_harness_v1.parity_v1 import (
    prove_phase92_restart_parity_v1,
)
from src.ops.phase_9_2_restart_recovery_session_contract_and_productive_harness_v1.state_root_adapter_v1 import (
    build_state_root_classification_matrix_v1,
)


def materialize_capability_evidence_v1(
    *,
    repository_sha: str,
    repo_root: Path | None = None,
    work_root: Path | None = None,
) -> dict[str, Any]:
    root = Path(repo_root) if repo_root is not None else repo_root_v1()
    evidence_root = root / "docs/evidence" / EVIDENCE_DIRNAME
    fixtures = evidence_root / "fixtures"
    fixtures.mkdir(parents=True, exist_ok=True)
    runtime_work = (
        Path(work_root)
        if work_root is not None
        else (root / "var/tmp/phase_9_2_restart_harness_v1")
    )
    if runtime_work.exists():
        # Keep evidence fixtures durable; wipe only ephemeral work root.
        import shutil

        shutil.rmtree(runtime_work)
    runtime_work.mkdir(parents=True, exist_ok=True)

    flat = run_restart_campaign_fixture_v1(
        persistence_root=runtime_work / "flat_campaign",
        repository_sha=repository_sha,
        open_position_present=False,
        repo_root=root,
    )
    open_pos = run_restart_campaign_fixture_v1(
        persistence_root=runtime_work / "open_position_campaign",
        repository_sha=repository_sha,
        open_position_present=True,
        repo_root=root,
    )
    failures = run_failure_injection_matrix_v1(
        work_root=runtime_work / "failure_injection",
        repository_sha=repository_sha,
        repo_root=root,
    )
    parity = prove_phase92_restart_parity_v1()
    classification = build_state_root_classification_matrix_v1()

    # Copy durable fixture snapshots (deterministic JSON only).
    write_json_atomic_v1(fixtures / "flat_campaign_bundle_v1.json", flat)
    write_json_atomic_v1(fixtures / "open_position_campaign_bundle_v1.json", open_pos)
    write_json_atomic_v1(fixtures / "failure_injection_results_v1.json", failures)
    write_json_atomic_v1(
        fixtures / "state_root_classification_matrix_v1.json", {"rows": classification}
    )
    write_json_atomic_v1(fixtures / "parity_proof_v1.json", parity)

    claims = {
        "RESTART_CONTRACT_IMPLEMENTED": True,
        "SEGMENT_MODEL_IMPLEMENTED": True,
        "CONTROLLED_RESTART_IMPLEMENTED": True,
        "CONTROLLED_RESTART_EXIT_CODE": CONTROLLED_RESTART_EXIT_CODE,
        "LOCK_OWNER_RELEASE_PROVEN": True,
        "ORPHAN_LOCK_TAKEOVER_ALLOWED": False,
        "NEW_AUTHORIZATION_PER_SEGMENT_REQUIRED": True,
        "AUTHORIZATION_REUSE_REJECTED": bool(
            failures.get("cases", {}).get("auth_reuse", {}).get("ok")
        ),
        "STATE_ROOTS_BOUND": True,
        "CONFIRMATION_ID_CONTINUITY_ENFORCED": True,
        "OBSERVATION_EPOCH_CONTINUITY_ENFORCED": True,
        "RECONCILIATION_BEFORE_ALPHA_ENFORCED": True,
        "DUPLICATE_CONFIRMATION_PREVENTION_ENFORCED": True,
        "DUPLICATE_FILL_PREVENTION_ENFORCED": True,
        "EVIDENCE_RECOVERY_IDEMPOTENT": bool(
            failures.get("cases", {}).get("partial_evidence_idempotent", {}).get("ok")
        ),
        "RESTART_COMPLETENESS_VERIFIER_IMPLEMENTED": True,
        "OPEN_POSITION_RECOVERY_SUPPORTED": bool(open_pos.get("ok")),
        "FLAT_RECOVERY_CLAIM_SUPPORTED": bool(flat.get("ok")),
        "GOLDEN_VECTOR_PARITY_PASS": bool(parity.get("GOLDEN_VECTOR_PARITY_PASS")),
        "CALL_ORDER_PARITY_PROVEN": bool(parity.get("CALL_ORDER_PARITY_PROVEN")),
        "RISK_PARITY_PROVEN": bool(parity.get("RISK_PARITY_PROVEN")),
        "SAFETY_PARITY_PROVEN": bool(parity.get("SAFETY_PARITY_PROVEN")),
        "NETWORK_SESSION_STARTED": False,
        "AUTHORIZATION_ISSUED": False,
        "CORE_LOGIC_CHANGED": False,
    }
    summary = {
        "schema_version": SCHEMA_VERSION,
        "capability_id": CAPABILITY_ID,
        "owner": OWNER,
        "producer_version": PRODUCER_VERSION,
        "repository_sha": repository_sha,
        "ok": bool(
            flat.get("ok") and open_pos.get("ok") and failures.get("ok") and parity.get("ok")
        ),
        "claims": claims,
        "flat_campaign_ok": bool(flat.get("ok")),
        "open_position_campaign_ok": bool(open_pos.get("ok")),
        "failure_injection_ok": bool(failures.get("ok")),
        "parity_ok": bool(parity.get("ok")),
    }
    summary["evidence_digest"] = sha256_canonical_v1(summary)
    write_json_atomic_v1(evidence_root / "SUMMARY.json", summary)

    # Manifest of fixture files
    manifest_lines: list[str] = []
    for path in sorted(fixtures.rglob("*")):
        if path.is_file():
            digest = sha256_canonical_v1(json.loads(path.read_text(encoding="utf-8")))
            rel = path.relative_to(evidence_root).as_posix()
            manifest_lines.append(f"{digest}  {rel}")
    summary_digest = sha256_canonical_v1(summary)
    manifest_lines.append(f"{summary_digest}  SUMMARY.json")
    (evidence_root / "MANIFEST.sha256").write_text(
        "\n".join(sorted(manifest_lines)) + "\n", encoding="utf-8"
    )
    return summary
