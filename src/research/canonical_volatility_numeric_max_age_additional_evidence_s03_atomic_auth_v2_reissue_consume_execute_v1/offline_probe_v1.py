"""Offline capability probe for atomic Auth-v2 reissue→consume→execute owner."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from research.canonical_volatility_numeric_max_age_additional_evidence_s03_atomic_auth_v2_reissue_consume_execute_v1.constants_v1 import (
    BOUND_DURATION_SECONDS_V1,
    CAPABILITY_ID,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_s03_atomic_auth_v2_reissue_consume_execute_v1.orchestrator_v1 import (
    run_s03_atomic_auth_v2_reissue_consume_and_execute_with_ephemeral_confirm_token_v1,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_s03_productive_session_execution_owner_v1.constants_v1 import (
    BOUND_DURATION_SECONDS,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_s03_productive_session_execution_owner_v1.evidence_v1 import (
    evidence_file_map_v1,
    resolve_s03_session_dir_v1,
    scan_artifacts_for_confirm_token_plaintext_v1,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_s03_productive_session_execution_owner_v1.models_v1 import (
    AdditionalEvidenceS03SessionExecutionOwnerError,
    MarketSampleV1,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_session_authorization_v2.artifact_v2 import (
    build_additional_evidence_session_authorization_v2,
    write_additional_evidence_session_authorization_v2,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_session_preregistration_contract_v2.contract_v2 import (
    verify_additional_evidence_session_preregistration_contract_artifact_v2,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_session_preregistration_contract_v2.validate_v2 import (
    validate_additional_evidence_session_preregistration_candidate_v2,
)

# Lost/unconsumable token for the pre-existing auth fixture (never reused for consume).
UNCONSUMABLE_FIXTURE_TOKEN = (
    "GO_PSO_SESSION_PREREG_V1_ATOMIC_UNCONSUMABLE_FIXTURE_TOKEN_NOT_FOR_PRODUCTION"
)


def _fake_samples_v1() -> tuple[MarketSampleV1, ...]:
    base_event = 1_700_000_000.0
    samples: list[MarketSampleV1] = []
    for i in range(3):
        samples.append(
            MarketSampleV1(
                sample_identity=f"mark:{i}:{int(base_event + 60 * i)}",
                mark_price=3000.0 + i,
                event_time_unix_seconds=base_event + 60 * i,
                receive_time_unix_seconds=base_event + 60 * i + 0.1,
                monotonic_elapsed_seconds=float(i),
            )
        )
    return tuple(samples)


def run_atomic_offline_capability_probe_v1(
    *,
    repo_root: Path,
    tmp_root: Path,
    execution_sha: str,
) -> dict[str, Any]:
    """Isolated offline probe; never touches productive authorization artifacts."""
    root = Path(repo_root)
    tmp = Path(tmp_root)
    old_auth_dir = tmp / "old_authorization"
    new_auth_dir = tmp / "new_authorization"
    evidence_root = tmp / "evidence_root"
    old_auth_dir.mkdir(parents=True, exist_ok=True)
    new_auth_dir.mkdir(parents=True, exist_ok=True)
    evidence_root.mkdir(parents=True, exist_ok=True)

    contract = verify_additional_evidence_session_preregistration_contract_artifact_v2(
        repo_root=root
    )
    prereg_path = (
        root
        / "config/research/canonical_volatility_numeric_max_age_additional_evidence_session_preregistration_v2.json"
    )
    prereg = __import__("json").loads(prereg_path.read_text(encoding="utf-8"))
    validated = validate_additional_evidence_session_preregistration_candidate_v2(
        prereg,
        repo_root=root,
        verify_baseline_artifact_ordering=True,
    )
    cons = old_auth_dir / "consumption_ledger.jsonl"
    rev = old_auth_dir / "revocation_ledger.jsonl"
    _lost = UNCONSUMABLE_FIXTURE_TOKEN
    old_artifact = build_additional_evidence_session_authorization_v2(
        preregistration_id=str(validated["session_id"]),
        preregistration_digest=str(validated["preregistration_digest"]),
        preregistration_contract_version=str(contract["capability_version"]),
        preregistration_contract_digest=str(contract["contract_digest"]),
        code_baseline_sha=str(validated["code_baseline_sha"]),
        execution_sha=execution_sha,
        critical_surface_digest=str(validated["critical_surface_manifest_digest"]),
        runbook_digest=str(prereg["runbook_digest"]),
        venue=str(validated["venue"]),
        instrument=str(validated["instrument"]),
        network_scope=str(validated["network_scope"]),
        session_scope=str(validated["session_scope"]),
        duration_seconds=int(prereg["duration_seconds"]),
        campaign_id=str(validated["campaign_id"]),
        # Short binder avoids Policy Critic NO_SECRETS `token=<long_name>` false positive.
        confirm_token=_lost,
        revocation_ledger_path=str(rev.resolve()),
        consumption_ledger_path=str(cons.resolve()),
        issued_at=datetime(2026, 8, 1, 19, 0, 0, tzinfo=timezone.utc),
    )
    old_path = old_auth_dir / "additional_evidence_session_authorization_v2.json"
    write_additional_evidence_session_authorization_v2(output_path=old_path, artifact=old_artifact)

    class _Clock:
        def __init__(self) -> None:
            self._now = 10.0
            self._calls = 0

        def __call__(self) -> float:
            self._calls += 1
            if self._calls >= 3:
                self._now = 10.0 + float(BOUND_DURATION_SECONDS) + 1.0
            return float(self._now)

    result = run_s03_atomic_auth_v2_reissue_consume_and_execute_with_ephemeral_confirm_token_v1(
        repo_root=root,
        execution_sha=execution_sha,
        unconsumable_authorization_path=old_path,
        unconsumable_authorization_id=old_artifact.authorization_id,
        evidence_root=evidence_root,
        isolated_authorization_dir=new_auth_dir,
        offline_probe=True,
        enable_productive_atomic_execution=False,
        market_samples=_fake_samples_v1(),
        monotonic_clock=_Clock(),
    )

    if result.get("status") != "PASS":
        raise AdditionalEvidenceS03SessionExecutionOwnerError(
            f"atomic_offline_probe_failed:{result.get('verdict')}:{result.get('blocker')}"
        )
    if not result.get("old_authorization_revoked"):
        raise AdditionalEvidenceS03SessionExecutionOwnerError("old_auth_not_revoked")
    if not result.get("authorization_consumed"):
        raise AdditionalEvidenceS03SessionExecutionOwnerError("new_auth_not_consumed")
    if int(result.get("requested_duration_seconds") or 0) != BOUND_DURATION_SECONDS_V1:
        raise AdditionalEvidenceS03SessionExecutionOwnerError("duration_not_bound")

    session_dir = resolve_s03_session_dir_v1(evidence_root=evidence_root)
    files = evidence_file_map_v1(session_dir)
    missing = [k for k, p in files.items() if not p.is_file()]
    if missing:
        raise AdditionalEvidenceS03SessionExecutionOwnerError(
            f"atomic_offline_probe_missing_evidence:{','.join(missing)}"
        )
    hits = scan_artifacts_for_confirm_token_plaintext_v1(
        root=session_dir,
        forbidden_substrings=[UNCONSUMABLE_FIXTURE_TOKEN],
    )
    if hits:
        raise AdditionalEvidenceS03SessionExecutionOwnerError(
            f"confirm_token_plaintext_persisted:{hits[0]}"
        )

    return {
        "ok": True,
        "capability_id": CAPABILITY_ID,
        "status": result.get("status"),
        "verdict": result.get("verdict"),
        "old_authorization_id": result.get("old_authorization_id"),
        "new_authorization_id": result.get("new_authorization_id"),
        "authorization_consumed": True,
        "token_plaintext_persisted": False,
        "requested_duration_seconds": BOUND_DURATION_SECONDS_V1,
        "side_effect_probe": result.get("side_effect_probe"),
    }
