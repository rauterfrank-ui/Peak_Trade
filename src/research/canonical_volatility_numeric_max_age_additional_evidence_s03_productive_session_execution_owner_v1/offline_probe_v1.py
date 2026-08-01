"""Fully offline capability probe for S03 execution owner (no production mutation)."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from research.canonical_volatility_numeric_max_age_additional_evidence_s03_productive_session_execution_owner_v1.constants_v1 import (
    BOUND_DURATION_SECONDS,
    BOUND_SESSION_ID,
    CAPABILITY_ID,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_s03_productive_session_execution_owner_v1.confirm_token_stdin_v1 import (
    sha256_fingerprint_plaintext_v1,
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
from research.canonical_volatility_numeric_max_age_additional_evidence_s03_productive_session_execution_owner_v1.orchestrator_v1 import (
    run_additional_evidence_s03_productive_session_v1,
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

OFFLINE_PROBE_TOKEN = "GO_S03_OFFLINE_PROBE_TOKEN_NOT_FOR_PRODUCTION_USE"


class _FakeMonotonicClock:
    def __init__(self, start: float = 1000.0) -> None:
        self._now = float(start)

    def __call__(self) -> float:
        return float(self._now)


def _build_fake_samples_v1() -> tuple[MarketSampleV1, ...]:
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
    samples.append(
        MarketSampleV1(
            sample_identity=samples[1].sample_identity,
            mark_price=samples[1].mark_price,
            event_time_unix_seconds=samples[1].event_time_unix_seconds,
            receive_time_unix_seconds=samples[1].receive_time_unix_seconds + 1.0,
            monotonic_elapsed_seconds=3.0,
        )
    )
    samples.append(
        MarketSampleV1(
            sample_identity=f"mark:ooo:{int(base_event - 60)}",
            mark_price=2999.0,
            event_time_unix_seconds=base_event - 60,
            receive_time_unix_seconds=base_event + 200,
            monotonic_elapsed_seconds=4.0,
        )
    )
    return tuple(samples)


def run_offline_capability_probe_v1(
    *,
    repo_root: Path,
    tmp_root: Path,
    execution_sha: str,
) -> dict[str, Any]:
    """Run isolated offline probe; never touches production auth/evidence artifacts."""
    root = Path(repo_root)
    tmp = Path(tmp_root)
    auth_dir = tmp / "authorization"
    auth_dir.mkdir(parents=True, exist_ok=True)
    evidence_root = tmp / "evidence_root"
    evidence_root.mkdir(parents=True, exist_ok=True)

    contract = verify_additional_evidence_session_preregistration_contract_artifact_v2(
        repo_root=root
    )
    prereg_path = (
        root
        / "config/research/canonical_volatility_numeric_max_age_additional_evidence_session_preregistration_v2.json"
    )
    prereg = json.loads(prereg_path.read_text(encoding="utf-8"))
    validated = validate_additional_evidence_session_preregistration_candidate_v2(
        prereg,
        repo_root=root,
        verify_baseline_artifact_ordering=True,
    )

    cons_path = auth_dir / "consumption_ledger.jsonl"
    rev_path = auth_dir / "revocation_ledger.jsonl"
    artifact = build_additional_evidence_session_authorization_v2(
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
        confirm_token=OFFLINE_PROBE_TOKEN,
        revocation_ledger_path=str(rev_path.resolve()),
        consumption_ledger_path=str(cons_path.resolve()),
        issued_at=datetime(2026, 8, 1, 19, 0, 0, tzinfo=timezone.utc),
    )
    auth_path = auth_dir / "additional_evidence_session_authorization_v2.json"
    write_additional_evidence_session_authorization_v2(output_path=auth_path, artifact=artifact)

    class _Clock:
        def __init__(self) -> None:
            self._now = 10.0
            self._calls = 0

        def __call__(self) -> float:
            self._calls += 1
            if self._calls >= 3:
                self._now = 10.0 + float(BOUND_DURATION_SECONDS) + 1.0
            return float(self._now)

    result = run_additional_evidence_s03_productive_session_v1(
        repo_root=root,
        authorization_path=auth_path,
        authorization_id=artifact.authorization_id,
        authorization_digest=artifact.authorization_digest,
        repository_sha=execution_sha,
        evidence_root=evidence_root,
        confirm_token=OFFLINE_PROBE_TOKEN,
        expected_confirm_token_fingerprint=sha256_fingerprint_plaintext_v1(OFFLINE_PROBE_TOKEN),
        monotonic_clock=_Clock(),
        market_samples=_build_fake_samples_v1(),
        offline_probe=True,
        enable_real_s03_session_execution=False,
        enable_real_public_md_network=False,
    )

    session_dir = resolve_s03_session_dir_v1(evidence_root=evidence_root)
    files = evidence_file_map_v1(session_dir)
    missing = [k for k, p in files.items() if not p.is_file()]
    if missing:
        raise AdditionalEvidenceS03SessionExecutionOwnerError(
            f"offline_probe_missing_evidence:{','.join(missing)}"
        )
    hits = scan_artifacts_for_confirm_token_plaintext_v1(
        root=session_dir,
        forbidden_substrings=[OFFLINE_PROBE_TOKEN],
    )
    if hits:
        raise AdditionalEvidenceS03SessionExecutionOwnerError(
            f"confirm_token_plaintext_persisted:{hits[0]}"
        )
    if result.get("status") != "PASS":
        raise AdditionalEvidenceS03SessionExecutionOwnerError(
            f"offline_probe_status:{result.get('status')}:{result.get('blocker')}"
        )
    events = list((result.get("side_effect_probe") or {}).get("events") or [])
    if "AUTHORIZATION_CONSUMED" not in events:
        raise AdditionalEvidenceS03SessionExecutionOwnerError("probe_missing_consume_event")
    if events.index("AUTHORIZATION_CONSUMED") > events.index("SESSION_LOCK"):
        raise AdditionalEvidenceS03SessionExecutionOwnerError("probe_lock_before_consume")
    if not cons_path.is_file() or not cons_path.read_text(encoding="utf-8").strip():
        raise AdditionalEvidenceS03SessionExecutionOwnerError("probe_consumption_missing")

    return {
        "ok": True,
        "capability_id": CAPABILITY_ID,
        "session_id": BOUND_SESSION_ID,
        "result": result,
        "evidence_files_present": sorted(files.keys()),
        "confirm_token_plaintext_persisted": False,
        "production_authorization_untouched": True,
        "real_network": False,
        "real_session": False,
    }
