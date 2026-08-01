"""Atomic per-session single-use consumption with consume-before-side-effects."""

from __future__ import annotations

import fcntl
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Optional, Sequence

from research.canonical_volatility_numeric_max_age_campaign_authorization_v1.artifact_v1 import (
    load_campaign_authorization_artifact_v1,
    verify_campaign_authorization_artifact_v1,
)
from research.canonical_volatility_numeric_max_age_campaign_authorization_v1.constants_v1 import (
    AUTHORIZATION_MAXIMUM_TOTAL_CONSUMPTIONS,
    BOUND_CAMPAIGN_ID,
    BOUND_PREREGISTRATION_DIGEST,
    BOUND_SESSION_IDS,
)
from research.canonical_volatility_numeric_max_age_campaign_authorization_v1.expiry_v1 import (
    assert_clock_within_authorization_window_v1,
    format_aware_utc_datetime_v1,
)
from research.canonical_volatility_numeric_max_age_campaign_authorization_v1.ledgers_v1 import (
    append_consumption_record_v1,
    assert_not_revoked_v1,
    find_session_consumption_v1,
    load_consumption_records_v1,
    parse_consumption_record_v1,
    resolve_ledger_path_v1,
)
from research.canonical_volatility_numeric_max_age_campaign_authorization_v1.models_v1 import (
    CampaignAuthorizationArtifactV1,
    CampaignAuthorizationError,
    RuntimeReleaseV1,
)

Clock = Callable[[], datetime]


class _ExclusiveLedgerLockV1:
    def __init__(self, lock_path: Path) -> None:
        self.lock_path = Path(lock_path)
        self.fd: Optional[int] = None

    def acquire(self) -> None:
        try:
            self.lock_path.parent.mkdir(parents=True, exist_ok=True)
            self.fd = os.open(str(self.lock_path), os.O_CREAT | os.O_RDWR, 0o644)
            fcntl.flock(self.fd, fcntl.LOCK_EX)
        except OSError as exc:
            raise CampaignAuthorizationError(f"lock_persist_error:{exc}") from exc

    def release(self) -> None:
        if self.fd is None:
            return
        try:
            fcntl.flock(self.fd, fcntl.LOCK_UN)
        except OSError:
            pass
        try:
            os.close(self.fd)
        except OSError:
            pass
        self.fd = None


def consume_campaign_authorization_session_v1(
    *,
    authorization_artifact_path: Path,
    session_id: str,
    evidence_root: Path,
    expected_repository_sha: Optional[str] = None,
    expected_campaign_id: str = BOUND_CAMPAIGN_ID,
    expected_session_ids: tuple[str, ...] = BOUND_SESSION_IDS,
    expected_preregistration_digest: str = BOUND_PREREGISTRATION_DIGEST,
    now: Optional[datetime] = None,
    clock: Optional[Clock] = None,
    side_effect_probe: Optional[list[str]] = None,
) -> RuntimeReleaseV1:
    """Consume one authorized session under exclusive lock.

    Steps 1–8 must complete before any runtime / evidence / network release.
    Temporary files have no authority. Authority is the final append-only record.
    """
    probe = side_effect_probe if side_effect_probe is not None else []

    # 1) Load artifact
    artifact = load_campaign_authorization_artifact_v1(Path(authorization_artifact_path))
    # 2–3) Digest + full bindings
    artifact = verify_campaign_authorization_artifact_v1(
        artifact,
        expected_repository_sha=expected_repository_sha or artifact.repository_sha,
        expected_campaign_id=expected_campaign_id,
        expected_session_ids=expected_session_ids,
        expected_preregistration_digest=expected_preregistration_digest,
    )
    # 4) Expiry / earliest_start
    current = assert_clock_within_authorization_window_v1(
        issued_at=artifact.issued_at,
        earliest_start=artifact.earliest_start,
        expires_at=artifact.expires_at,
        now=now,
        clock=clock,
    )

    revocation_path = resolve_ledger_path_v1(
        evidence_root=evidence_root,
        relative_or_absolute=artifact.revocation_ledger_path,
    )
    consumption_path = resolve_ledger_path_v1(
        evidence_root=evidence_root,
        relative_or_absolute=artifact.consumption_ledger_path,
    )
    lock_path = consumption_path.with_suffix(consumption_path.suffix + ".lock")

    # 5) Revocation (pre-lock fail-closed; rechecked under lock)
    assert_not_revoked_v1(
        revocation_ledger_path=revocation_path,
        authorization_id=artifact.authorization_id,
        authorization_digest=artifact.artifact_digest,
    )

    # 6) Session membership
    sid = str(session_id or "").strip()
    if sid not in artifact.session_ids:
        raise CampaignAuthorizationError("unknown_session_id")

    lock = _ExclusiveLedgerLockV1(lock_path)
    lock.acquire()
    try:
        assert_not_revoked_v1(
            revocation_ledger_path=revocation_path,
            authorization_id=artifact.authorization_id,
            authorization_digest=artifact.artifact_digest,
        )
        records = load_consumption_records_v1(consumption_path)
        if find_session_consumption_v1(
            records,
            authorization_id=artifact.authorization_id,
            session_id=sid,
        ):
            raise CampaignAuthorizationError("session_already_consumed")
        auth_records = [r for r in records if r["authorization_id"] == artifact.authorization_id]
        if len(auth_records) >= AUTHORIZATION_MAXIMUM_TOTAL_CONSUMPTIONS:
            raise CampaignAuthorizationError("maximum_total_consumptions_exceeded")

        consumption_index = len(auth_records) + 1
        # 7) Atomic append-only consumption record
        probe.append("CONSUMPTION_PERSIST_BEGIN")
        written = append_consumption_record_v1(
            consumption_ledger_path=consumption_path,
            authorization_id=artifact.authorization_id,
            authorization_digest=artifact.artifact_digest,
            session_id=sid,
            repository_sha=artifact.repository_sha,
            campaign_id=artifact.campaign_id,
            consumption_index=consumption_index,
            consumed_at=current,
        )
        # 8) Re-read and verify persisted authority
        reread = load_consumption_records_v1(consumption_path)
        found = find_session_consumption_v1(
            reread,
            authorization_id=artifact.authorization_id,
            session_id=sid,
        )
        if found is None:
            raise CampaignAuthorizationError("consumption_persist_verify_failed")
        verified = parse_consumption_record_v1(found)
        if verified["consumption_record_digest"] != written["consumption_record_digest"]:
            raise CampaignAuthorizationError("consumption_persist_verify_failed")
        probe.append("CONSUMPTION_PERSIST_VERIFIED")

        release = RuntimeReleaseV1(
            authorization_id=artifact.authorization_id,
            authorization_digest=artifact.artifact_digest,
            campaign_id=artifact.campaign_id,
            session_id=sid,
            repository_sha=artifact.repository_sha,
            consumption_record_digest=verified["consumption_record_digest"],
            consumption_index=int(verified["consumption_index"]),
            released_at=format_aware_utc_datetime_v1(current),
        )
        probe.append("RUNTIME_RELEASE_RETURNED")
        return release
    finally:
        lock.release()


def revoke_campaign_authorization_v1(
    *,
    authorization_artifact_path: Path,
    evidence_root: Path,
    reason: str,
    operator_reference: str,
    revoked_at: Optional[datetime] = None,
    clock: Optional[Clock] = None,
) -> dict[str, Any]:
    from research.canonical_volatility_numeric_max_age_campaign_authorization_v1.ledgers_v1 import (
        append_revocation_record_v1,
    )

    artifact = verify_campaign_authorization_artifact_v1(
        load_campaign_authorization_artifact_v1(Path(authorization_artifact_path))
    )
    when = revoked_at
    if when is None:
        if clock is None:
            from datetime import timezone

            when = datetime.now(timezone.utc)
        else:
            when = clock()
    revocation_path = resolve_ledger_path_v1(
        evidence_root=evidence_root,
        relative_or_absolute=artifact.revocation_ledger_path,
    )
    consumption_path = resolve_ledger_path_v1(
        evidence_root=evidence_root,
        relative_or_absolute=artifact.consumption_ledger_path,
    )
    lock = _ExclusiveLedgerLockV1(consumption_path.with_suffix(consumption_path.suffix + ".lock"))
    lock.acquire()
    try:
        return append_revocation_record_v1(
            revocation_ledger_path=revocation_path,
            authorization_id=artifact.authorization_id,
            authorization_digest=artifact.artifact_digest,
            reason=reason,
            operator_reference=operator_reference,
            revoked_at=when,
        )
    finally:
        lock.release()


def load_verified_runtime_release_for_session_v1(
    *,
    authorization_artifact_path: Path,
    session_id: str,
    evidence_root: Path,
    expected_repository_sha: Optional[str] = None,
    expected_campaign_id: Optional[str] = BOUND_CAMPAIGN_ID,
    expected_session_ids: Optional[tuple[str, ...]] = BOUND_SESSION_IDS,
    expected_preregistration_digest: Optional[str] = BOUND_PREREGISTRATION_DIGEST,
) -> RuntimeReleaseV1:
    """Gate helper: require an already-persisted atomic consumption for the session."""
    artifact = verify_campaign_authorization_artifact_v1(
        load_campaign_authorization_artifact_v1(Path(authorization_artifact_path)),
        expected_repository_sha=expected_repository_sha,
        expected_campaign_id=expected_campaign_id,
        expected_session_ids=expected_session_ids,
        expected_preregistration_digest=expected_preregistration_digest,
    )
    revocation_path = resolve_ledger_path_v1(
        evidence_root=evidence_root,
        relative_or_absolute=artifact.revocation_ledger_path,
    )
    consumption_path = resolve_ledger_path_v1(
        evidence_root=evidence_root,
        relative_or_absolute=artifact.consumption_ledger_path,
    )
    assert_not_revoked_v1(
        revocation_ledger_path=revocation_path,
        authorization_id=artifact.authorization_id,
        authorization_digest=artifact.artifact_digest,
    )
    sid = str(session_id or "").strip()
    if sid not in artifact.session_ids:
        raise CampaignAuthorizationError("unknown_session_id")
    records = load_consumption_records_v1(consumption_path)
    found = find_session_consumption_v1(
        records,
        authorization_id=artifact.authorization_id,
        session_id=sid,
    )
    if found is None:
        raise CampaignAuthorizationError("authorization_not_consumed_for_session")
    verified = parse_consumption_record_v1(found)
    if verified["repository_sha"] != artifact.repository_sha:
        raise CampaignAuthorizationError("consumption_repository_sha_mismatch")
    if verified["campaign_id"] != artifact.campaign_id:
        raise CampaignAuthorizationError("consumption_campaign_id_mismatch")
    return RuntimeReleaseV1(
        authorization_id=artifact.authorization_id,
        authorization_digest=artifact.artifact_digest,
        campaign_id=artifact.campaign_id,
        session_id=sid,
        repository_sha=artifact.repository_sha,
        consumption_record_digest=verified["consumption_record_digest"],
        consumption_index=int(verified["consumption_index"]),
        released_at=str(verified["consumed_at"]),
    )


def assert_no_foreign_side_effects_before_release_v1(
    *,
    evidence_root: Path,
    artifact: CampaignAuthorizationArtifactV1,
    probe: Sequence[str],
) -> None:
    """Ensure productive ledger/join/quarantine were not touched pre-release."""
    productive = resolve_ledger_path_v1(
        evidence_root=evidence_root, relative_or_absolute=artifact.durable_ledger_path
    )
    join = resolve_ledger_path_v1(
        evidence_root=evidence_root, relative_or_absolute=artifact.join_path
    )
    quarantine = resolve_ledger_path_v1(
        evidence_root=evidence_root, relative_or_absolute=artifact.quarantine_path
    )
    for path in (productive, join, quarantine):
        if path.exists():
            raise CampaignAuthorizationError(f"side_effect_before_consumption:{path.name}")
    if "RUNTIME_RELEASE_RETURNED" in list(probe) and "CONSUMPTION_PERSIST_VERIFIED" not in list(
        probe
    ):
        raise CampaignAuthorizationError("runtime_release_before_persist_verify")
