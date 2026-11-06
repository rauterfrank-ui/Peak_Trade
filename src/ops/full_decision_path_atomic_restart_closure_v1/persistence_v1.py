"""Versioned multi-record transaction with commit marker, replay, pending evidence."""

from __future__ import annotations

import json
import os
import shutil
import tempfile
import uuid
from pathlib import Path
from typing import Any, Callable, Mapping, Optional

from src.ops.decision_config_ownership_and_consumer_closure_v1.models_v1 import (
    DecisionConfigBindingStateV1,
)
from src.ops.decision_config_ownership_and_consumer_closure_v1.persistence_v1 import (
    persist_decision_config_state_atomic_v1,
)
from src.ops.full_decision_path_atomic_restart_closure_v1.constants_v1 import (
    COMMIT_MARKER_FILENAME,
    JOURNAL_FILENAME,
    MANIFEST_FILENAME,
    MEMBER_ACCOUNTING,
    MEMBER_CONFIRMATION,
    MEMBER_DECISION_CONFIG,
    MEMBER_DYNAMIC_SCOPE,
    PENDING_EVIDENCE_FILENAME,
    STAGING_DIRNAME_PREFIX,
    STATE_VERSION,
    TRANSACTION_INDEX_FILENAME,
)
from src.ops.full_decision_path_atomic_restart_closure_v1.models_v1 import (
    DecisionPathCommitMarkerV1,
    DecisionPathWalJournalV1,
    MemberRootRefV1,
    PendingEvidenceCursorV1,
    canonical_digest_v1,
    sha256_hex,
)
from src.ops.full_decision_path_atomic_restart_closure_v1.reason_codes_v1 import (
    DecisionPathAtomicFailureCodeV1,
)
from src.ops.full_decision_path_atomic_restart_closure_v1.single_writer_v1 import (
    DecisionPathAtomicSingleWriterV1,
)
from src.ops.productive_futures_accounting_runtime_binding_v1.accounting_engine_v1 import (
    ProductiveFuturesAccountingSessionV1,
)
from src.ops.productive_futures_accounting_runtime_binding_v1.persistence_v1 import (
    persist_accounting_bundle_atomic_v1,
)
from src.ops.productive_futures_accounting_runtime_binding_v1.single_writer_v1 import (
    ProductiveFuturesAccountingSingleWriterV1,
)
from src.ops.stateful_confirmation_and_c1_productive_binding_v1.models_v1 import (
    CanonicalConfirmationStateV1,
)
from src.ops.stateful_confirmation_and_c1_productive_binding_v1.persistence_v1 import (
    persist_confirmation_state_atomic_v1,
)
from src.ops.stateful_confirmation_and_c1_productive_binding_v1.single_writer_v1 import (
    ConfirmationStateSingleWriterV1,
)
from src.ops.dynamic_scope_persistence_binding_v1.models_v1 import (
    CanonicalDynamicScopeStateV1,
)
from src.ops.dynamic_scope_persistence_binding_v1.persistence_v1 import (
    persist_dynamic_scope_state_atomic_v1,
)
from src.ops.dynamic_scope_persistence_binding_v1.single_writer_v1 import (
    DynamicScopeStateSingleWriterV1,
)


class DecisionPathAtomicPersistenceError(RuntimeError):
    def __init__(self, code: DecisionPathAtomicFailureCodeV1, detail: str = "") -> None:
        self.code = code
        super().__init__(f"{code.value}:{detail}" if detail else code.value)


def _atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=path.name + ".", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(text)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp_name, path)
    finally:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)


def write_manifest(root: Path, relative_files: tuple[str, ...]) -> str:
    lines: list[str] = []
    for rel in sorted(relative_files):
        digest = sha256_hex((root / rel).read_bytes())
        lines.append(f"{digest}  {rel}")
    body = "\n".join(lines) + "\n"
    _atomic_write_text(root / MANIFEST_FILENAME, body)
    return sha256_hex(body)


def verify_manifest(root: Path) -> dict[str, Any]:
    manifest = Path(root) / MANIFEST_FILENAME
    if not manifest.is_file():
        raise DecisionPathAtomicPersistenceError(
            DecisionPathAtomicFailureCodeV1.MANIFEST_VERIFY_FAILED,
            "MANIFEST_MISSING",
        )
    errors: list[str] = []
    for line in manifest.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        digest, rel = line.split(None, 1)
        path = Path(root) / rel
        if not path.is_file():
            errors.append(f"MISSING:{rel}")
            continue
        actual = sha256_hex(path.read_bytes())
        if actual != digest:
            errors.append(f"DIGEST_MISMATCH:{rel}")
    if errors:
        raise DecisionPathAtomicPersistenceError(
            DecisionPathAtomicFailureCodeV1.MANIFEST_VERIFY_FAILED,
            ";".join(errors),
        )
    return {"ok": True, "manifest_path": str(manifest)}


def journal_path(root: Path) -> Path:
    return Path(root) / JOURNAL_FILENAME


def commit_marker_path(root: Path) -> Path:
    return Path(root) / COMMIT_MARKER_FILENAME


def pending_evidence_path(root: Path) -> Path:
    return Path(root) / PENDING_EVIDENCE_FILENAME


def prior_commit_exists(root: Path) -> bool:
    return commit_marker_path(root).is_file()


def load_commit_marker_v1(root: Path) -> Optional[DecisionPathCommitMarkerV1]:
    path = commit_marker_path(root)
    if not path.is_file():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        marker = DecisionPathCommitMarkerV1.from_dict(payload)
    except Exception as exc:  # noqa: BLE001
        raise DecisionPathAtomicPersistenceError(
            DecisionPathAtomicFailureCodeV1.COMMIT_MARKER_CORRUPT,
            str(exc),
        ) from exc
    if marker.state_version != STATE_VERSION:
        raise DecisionPathAtomicPersistenceError(
            DecisionPathAtomicFailureCodeV1.STATE_VERSION_MISMATCH,
            marker.state_version,
        )
    return marker


def load_pending_evidence_cursor_v1(root: Path) -> Optional[PendingEvidenceCursorV1]:
    path = pending_evidence_path(root)
    if not path.is_file():
        return None
    try:
        return PendingEvidenceCursorV1.from_dict(json.loads(path.read_text(encoding="utf-8")))
    except Exception as exc:  # noqa: BLE001
        raise DecisionPathAtomicPersistenceError(
            DecisionPathAtomicFailureCodeV1.CHECKPOINT_CORRUPT,
            f"PENDING_EVIDENCE:{exc}",
        ) from exc


def discard_incomplete_journal_v1(root: Path) -> dict[str, Any]:
    """Crash before commit marker: journal is non-authoritative; discard safely."""
    jpath = journal_path(root)
    discarded = False
    if jpath.is_file():
        jpath.unlink()
        discarded = True
    staging_dirs = list(Path(root).glob(f"{STAGING_DIRNAME_PREFIX}*"))
    for staging in staging_dirs:
        shutil.rmtree(staging, ignore_errors=True)
    return {"ok": True, "journal_discarded": discarded, "stagings_removed": len(staging_dirs)}


def recover_decision_path_atomic_v1(
    *,
    coordinator_root: Path,
    expected_repository_sha: str | None = None,
    expected_config_digest: str | None = None,
) -> dict[str, Any]:
    """
    Recovery:
    - journal without marker → discard (incomplete txn)
    - marker present → authoritative; verify digests/bindings
    - pending evidence → leave for idempotent drain (does not roll back runtime)
    """
    root = Path(coordinator_root)
    root.mkdir(parents=True, exist_ok=True)
    marker = load_commit_marker_v1(root)
    if marker is None:
        discarded = discard_incomplete_journal_v1(root)
        return {
            "ok": True,
            "recovered": False,
            "reason": "NO_PRIOR_COMMIT",
            "discarded": discarded,
            "pending_evidence": None,
        }
    if expected_repository_sha is not None and marker.repository_sha != expected_repository_sha:
        raise DecisionPathAtomicPersistenceError(
            DecisionPathAtomicFailureCodeV1.REPOSITORY_SHA_MISMATCH,
            f"{marker.repository_sha}!={expected_repository_sha}",
        )
    if expected_config_digest is not None and marker.config_digest != expected_config_digest:
        raise DecisionPathAtomicPersistenceError(
            DecisionPathAtomicFailureCodeV1.CONFIG_DIGEST_MISMATCH,
            f"{marker.config_digest}!={expected_config_digest}",
        )
    # Incomplete journal after marker is stale prepare — discard.
    discarded = discard_incomplete_journal_v1(root)
    pending = load_pending_evidence_cursor_v1(root)
    return {
        "ok": True,
        "recovered": True,
        "commit_identity": marker.commit_identity,
        "commit_sequence": marker.commit_sequence,
        "member_digests": dict(marker.member_digests),
        "config_digest": marker.config_digest,
        "repository_sha": marker.repository_sha,
        "observation_epoch": marker.observation_epoch,
        "portfolio_digest": marker.portfolio_digest,
        "evidence_status": marker.evidence_status,
        "pending_evidence": None if pending is None else pending.to_dict(),
        "discarded": discarded,
    }


def materialize_evidence_idempotent_v1(
    *,
    coordinator_root: Path,
    evidence_payload: Mapping[str, Any],
    fail: bool = False,
) -> dict[str, Any]:
    """Materialize evidence after runtime commit; failures leave recoverable pending cursor."""
    root = Path(coordinator_root)
    marker = load_commit_marker_v1(root)
    if marker is None:
        raise DecisionPathAtomicPersistenceError(
            DecisionPathAtomicFailureCodeV1.COMMIT_MARKER_MISSING,
            "EVIDENCE_REQUIRES_RUNTIME_COMMIT",
        )
    cursor = load_pending_evidence_cursor_v1(root)
    if cursor is None:
        cursor = PendingEvidenceCursorV1(
            state_version=STATE_VERSION,
            commit_identity=marker.commit_identity,
            commit_sequence=marker.commit_sequence,
            idempotency_key=marker.idempotency_key,
            evidence_path=str(root / "cycle_evidence_v1.json"),
            attempts=0,
            status="PENDING",
        )
    if cursor.status == "MATERIALIZED" and cursor.materialized_digest:
        return {
            "ok": True,
            "idempotent_replay": True,
            "materialized_digest": cursor.materialized_digest,
            "attempts": cursor.attempts,
        }
    cursor.attempts += 1
    if fail:
        cursor.last_error = "INJECTED_EVIDENCE_MATERIALIZATION_FAILURE"
        cursor.status = "PENDING"
        _atomic_write_text(
            pending_evidence_path(root),
            json.dumps(cursor.to_dict(), sort_keys=True, indent=2) + "\n",
        )
        marker.evidence_status = "PENDING"
        _atomic_write_text(
            commit_marker_path(root),
            json.dumps(marker.to_dict(), sort_keys=True, indent=2) + "\n",
        )
        write_manifest(
            root,
            tuple(
                name
                for name in (
                    COMMIT_MARKER_FILENAME,
                    PENDING_EVIDENCE_FILENAME,
                    TRANSACTION_INDEX_FILENAME,
                )
                if (root / name).is_file()
            ),
        )
        return {
            "ok": False,
            "pending": True,
            "attempts": cursor.attempts,
            "error": cursor.last_error,
            "runtime_commit_retained": True,
        }
    body = json.dumps(dict(evidence_payload), sort_keys=True, indent=2) + "\n"
    evidence_file = Path(cursor.evidence_path)
    _atomic_write_text(evidence_file, body)
    digest = sha256_hex(body)
    cursor.status = "MATERIALIZED"
    cursor.materialized_digest = digest
    cursor.last_error = ""
    _atomic_write_text(
        pending_evidence_path(root),
        json.dumps(cursor.to_dict(), sort_keys=True, indent=2) + "\n",
    )
    marker.evidence_status = "MATERIALIZED"
    _atomic_write_text(
        commit_marker_path(root),
        json.dumps(marker.to_dict(), sort_keys=True, indent=2) + "\n",
    )
    write_manifest(
        root,
        (
            COMMIT_MARKER_FILENAME,
            PENDING_EVIDENCE_FILENAME,
            TRANSACTION_INDEX_FILENAME,
        ),
    )
    return {
        "ok": True,
        "idempotent_replay": False,
        "materialized_digest": digest,
        "attempts": cursor.attempts,
    }


def commit_decision_path_atomic_transaction_v1(
    *,
    coordinator_root: Path,
    writer: DecisionPathAtomicSingleWriterV1,
    confirmation_state: CanonicalConfirmationStateV1,
    confirmation_state_root: Path,
    dynamic_scope_state: CanonicalDynamicScopeStateV1 | None,
    dynamic_scope_state_root: Path | None,
    decision_config_state: DecisionConfigBindingStateV1 | None,
    decision_config_state_root: Path | None,
    accounting_session: ProductiveFuturesAccountingSessionV1 | None,
    accounting_state_root: Path | None,
    repository_sha: str,
    config_digest: str,
    instrument_id: str,
    observation_epoch: int,
    fill_idempotency_key: str = "",
    persist_scope: bool = True,
    persist_accounting: bool = True,
    persist_config: bool = True,
    evidence_payload: Mapping[str, Any] | None = None,
    evidence_fail: bool = False,
    interrupt_before_state_write: bool = False,
    interrupt_during_state_write: bool = False,
    interrupt_after_state_before_marker: bool = False,
    interrupt_after_runtime_before_evidence: bool = False,
    interrupt_after_fill_before_portfolio: bool = False,
    interrupt_after_portfolio_before_evidence_cursor: bool = False,
) -> dict[str, Any]:
    """
    Transaction boundary:
      PREPARE(journal) → member writes (existing owners) → COMMIT_MARKER
      → PENDING_EVIDENCE_CURSOR → evidence materialization (non-rollback on failure)
    """
    writer.assert_held()
    root = Path(coordinator_root)
    root.mkdir(parents=True, exist_ok=True)

    prior = load_commit_marker_v1(root)
    if prior is not None and fill_idempotency_key:
        # Duplicate economic / decision replay after commit: no second advance.
        if fill_idempotency_key in {
            prior.fill_idempotency_key,
            prior.idempotency_key,
            prior.commit_identity,
        }:
            return {
                "ok": True,
                "duplicate_replay": True,
                "commit_identity": prior.commit_identity,
                "commit_sequence": prior.commit_sequence,
                "member_digests": dict(prior.member_digests),
                "evidence_status": prior.evidence_status,
            }

    commit_sequence = 1 if prior is None else int(prior.commit_sequence) + 1
    transaction_id = sha256_hex(f"{instrument_id}:{commit_sequence}:{uuid.uuid4().hex}")
    idempotency_key = sha256_hex(
        f"{instrument_id}:{observation_epoch}:{confirmation_state.confirmation_session_id}:"
        f"{fill_idempotency_key}:{commit_sequence}"
    )
    if prior is not None and prior.idempotency_key == idempotency_key:
        return {
            "ok": True,
            "duplicate_replay": True,
            "commit_identity": prior.commit_identity,
            "commit_sequence": prior.commit_sequence,
            "member_digests": dict(prior.member_digests),
            "evidence_status": prior.evidence_status,
        }

    if interrupt_before_state_write:
        raise DecisionPathAtomicPersistenceError(
            DecisionPathAtomicFailureCodeV1.PERSISTENCE_INTERRUPTION,
            "INJECTED_INTERRUPT_BEFORE_STATE_WRITE",
        )

    conf_digest = confirmation_state.state_digest()
    scope_digest = dynamic_scope_state.state_digest() if dynamic_scope_state is not None else ""
    cfg_digest = decision_config_state.state_digest() if decision_config_state is not None else ""
    portfolio_digest = (
        accounting_session.portfolio_state().digest() if accounting_session is not None else ""
    )
    members = [
        MemberRootRefV1(
            member_id=MEMBER_CONFIRMATION,
            state_root=str(confirmation_state_root),
            owner="ops.stateful_confirmation_and_c1_productive_binding_v1",
            state_digest=conf_digest,
        )
    ]
    if dynamic_scope_state is not None and dynamic_scope_state_root is not None:
        members.append(
            MemberRootRefV1(
                member_id=MEMBER_DYNAMIC_SCOPE,
                state_root=str(dynamic_scope_state_root),
                owner="ops.dynamic_scope_persistence_binding_v1",
                state_digest=scope_digest,
            )
        )
    if decision_config_state is not None and decision_config_state_root is not None:
        members.append(
            MemberRootRefV1(
                member_id=MEMBER_DECISION_CONFIG,
                state_root=str(decision_config_state_root),
                owner="ops.decision_config_ownership_and_consumer_closure_v1",
                state_digest=cfg_digest,
            )
        )
    if accounting_session is not None and accounting_state_root is not None:
        members.append(
            MemberRootRefV1(
                member_id=MEMBER_ACCOUNTING,
                state_root=str(accounting_state_root),
                owner="ops.productive_futures_accounting_runtime_binding_v1",
                state_digest=portfolio_digest,
            )
        )

    journal = DecisionPathWalJournalV1(
        state_version=STATE_VERSION,
        transaction_id=transaction_id,
        idempotency_key=idempotency_key,
        commit_sequence=commit_sequence,
        repository_sha=repository_sha,
        config_digest=config_digest,
        instrument_id=instrument_id,
        confirmation_session_id=confirmation_state.confirmation_session_id,
        scope_session_id=(
            dynamic_scope_state.scope_session_id if dynamic_scope_state is not None else ""
        ),
        members=members,
        confirmation_payload=confirmation_state.to_dict(),
        dynamic_scope_payload=(
            dynamic_scope_state.to_dict() if dynamic_scope_state is not None else {}
        ),
        decision_config_payload=(
            decision_config_state.to_dict() if decision_config_state is not None else {}
        ),
        accounting_payload=(
            accounting_session.to_durable_dict() if accounting_session is not None else {}
        ),
        portfolio_digest=portfolio_digest,
        fill_idempotency_key=fill_idempotency_key,
        observation_epoch=int(observation_epoch),
        phase="PREPARED",
        previous_commit_identity="" if prior is None else prior.commit_identity,
    )
    _atomic_write_text(
        journal_path(root),
        json.dumps(journal.to_dict(), sort_keys=True, indent=2) + "\n",
    )

    if interrupt_during_state_write:
        raise DecisionPathAtomicPersistenceError(
            DecisionPathAtomicFailureCodeV1.PERSISTENCE_INTERRUPTION,
            "INJECTED_INTERRUPT_DURING_STATE_WRITE",
        )

    member_digests: dict[str, str] = {}
    conf_out: dict[str, Any] = {}
    scope_out: dict[str, Any] = {}
    acct_out: dict[str, Any] = {}
    cfg_out: dict[str, Any] = {}
    staging_tx = root / f"{STAGING_DIRNAME_PREFIX}{transaction_id}"
    if staging_tx.exists():
        shutil.rmtree(staging_tx, ignore_errors=True)
    staging_tx.mkdir(parents=True, exist_ok=False)
    staged_promotions: list[tuple[Path, Path]] = []

    try:
        # Stage member writes under coordinator first (no live mixed roots until marker).
        if (
            persist_accounting
            and accounting_session is not None
            and accounting_state_root is not None
        ):
            if interrupt_after_fill_before_portfolio:
                raise DecisionPathAtomicPersistenceError(
                    DecisionPathAtomicFailureCodeV1.PERSISTENCE_INTERRUPTION,
                    "INJECTED_INTERRUPT_AFTER_FILL_BEFORE_PORTFOLIO",
                )
            staged_acct = staging_tx / MEMBER_ACCOUNTING
            acct_writer = ProductiveFuturesAccountingSingleWriterV1(
                state_root=staged_acct,
                session_id=writer.session_id,
            )
            acct_writer.acquire()
            try:
                acct_out = persist_accounting_bundle_atomic_v1(
                    state_root=staged_acct,
                    session=accounting_session,
                    writer=acct_writer,
                )
                member_digests[MEMBER_ACCOUNTING] = str(
                    acct_out.get("portfolio_state_digest") or portfolio_digest
                )
            finally:
                acct_writer.release()
            staged_promotions.append((staged_acct, Path(accounting_state_root)))

        staged_conf = staging_tx / MEMBER_CONFIRMATION
        conf_writer = ConfirmationStateSingleWriterV1(
            state_root=staged_conf,
            session_id=writer.session_id,
            instrument_id=instrument_id,
        )
        conf_writer.acquire()
        try:
            conf_out = persist_confirmation_state_atomic_v1(
                state_root=staged_conf,
                state=confirmation_state,
                writer=conf_writer,
            )
            committed_conf: CanonicalConfirmationStateV1 = conf_out["state"]
            member_digests[MEMBER_CONFIRMATION] = committed_conf.state_digest()
        finally:
            conf_writer.release()
        staged_promotions.append((staged_conf, Path(confirmation_state_root)))

        if (
            persist_scope
            and dynamic_scope_state is not None
            and dynamic_scope_state_root is not None
        ):
            staged_scope = staging_tx / MEMBER_DYNAMIC_SCOPE
            scope_writer = DynamicScopeStateSingleWriterV1(
                state_root=staged_scope,
                session_id=writer.session_id,
                instrument_id=instrument_id,
            )
            scope_writer.acquire()
            try:
                scope_out = persist_dynamic_scope_state_atomic_v1(
                    state_root=staged_scope,
                    state=dynamic_scope_state,
                    writer=scope_writer,
                )
                committed_scope: CanonicalDynamicScopeStateV1 = scope_out["state"]
                member_digests[MEMBER_DYNAMIC_SCOPE] = committed_scope.state_digest()
            finally:
                scope_writer.release()
            staged_promotions.append((staged_scope, Path(dynamic_scope_state_root)))

        if (
            persist_config
            and decision_config_state is not None
            and decision_config_state_root is not None
        ):
            staged_cfg = staging_tx / MEMBER_DECISION_CONFIG
            cfg_payload = dict(decision_config_state.to_dict())
            cfg_payload["commit_sequence"] = int(decision_config_state.commit_sequence) + 1
            cfg_state = DecisionConfigBindingStateV1.from_dict(cfg_payload)
            cfg_out_state = persist_decision_config_state_atomic_v1(
                cfg_state, state_root=staged_cfg
            )
            cfg_out = {"state_digest": cfg_out_state.state_digest()}
            member_digests[MEMBER_DECISION_CONFIG] = cfg_out_state.state_digest()
            staged_promotions.append((staged_cfg, Path(decision_config_state_root)))

        if interrupt_after_state_before_marker:
            raise DecisionPathAtomicPersistenceError(
                DecisionPathAtomicFailureCodeV1.PERSISTENCE_INTERRUPTION,
                "INJECTED_INTERRUPT_AFTER_STATE_BEFORE_MARKER",
            )

        commit_identity = sha256_hex(
            f"{transaction_id}:{idempotency_key}:{canonical_digest_v1(member_digests)}"
        )
        marker = DecisionPathCommitMarkerV1(
            state_version=STATE_VERSION,
            commit_identity=commit_identity,
            commit_sequence=commit_sequence,
            transaction_id=transaction_id,
            idempotency_key=idempotency_key,
            repository_sha=repository_sha,
            config_digest=config_digest,
            instrument_id=instrument_id,
            member_digests=member_digests,
            confirmation_session_id=confirmation_state.confirmation_session_id,
            scope_session_id=(
                dynamic_scope_state.scope_session_id if dynamic_scope_state is not None else ""
            ),
            observation_epoch=int(observation_epoch),
            portfolio_digest=member_digests.get(MEMBER_ACCOUNTING, portfolio_digest),
            fill_idempotency_key=fill_idempotency_key,
            previous_commit_identity="" if prior is None else prior.commit_identity,
            evidence_status="PENDING",
        )
        index = {
            "commit_identity": commit_identity,
            "commit_sequence": commit_sequence,
            "transaction_id": transaction_id,
            "member_digests": member_digests,
            "journal_digest": journal.journal_digest(),
        }
        _atomic_write_text(
            staging_tx / TRANSACTION_INDEX_FILENAME,
            json.dumps(index, sort_keys=True, indent=2) + "\n",
        )
        _atomic_write_text(
            staging_tx / COMMIT_MARKER_FILENAME,
            json.dumps(marker.to_dict(), sort_keys=True, indent=2) + "\n",
        )

        # Promote staged member roots then coordinator marker (runtime commit boundary).
        for staged_root, live_root in staged_promotions:
            live_root.mkdir(parents=True, exist_ok=True)
            for child in staged_root.iterdir():
                if child.name.endswith(".lock"):
                    continue
                dst = live_root / child.name
                if child.is_file():
                    os.replace(child, dst)
        os.replace(staging_tx / COMMIT_MARKER_FILENAME, commit_marker_path(root))
        os.replace(staging_tx / TRANSACTION_INDEX_FILENAME, root / TRANSACTION_INDEX_FILENAME)
        if journal_path(root).is_file():
            journal_path(root).unlink()

        if interrupt_after_portfolio_before_evidence_cursor and MEMBER_ACCOUNTING in member_digests:
            raise DecisionPathAtomicPersistenceError(
                DecisionPathAtomicFailureCodeV1.PERSISTENCE_INTERRUPTION,
                "INJECTED_INTERRUPT_AFTER_PORTFOLIO_BEFORE_EVIDENCE_CURSOR",
            )

        pending = PendingEvidenceCursorV1(
            state_version=STATE_VERSION,
            commit_identity=commit_identity,
            commit_sequence=commit_sequence,
            idempotency_key=idempotency_key,
            evidence_path=str(root / "cycle_evidence_v1.json"),
            attempts=0,
            status="PENDING",
        )
        _atomic_write_text(
            pending_evidence_path(root),
            json.dumps(pending.to_dict(), sort_keys=True, indent=2) + "\n",
        )
        write_manifest(
            root,
            (COMMIT_MARKER_FILENAME, PENDING_EVIDENCE_FILENAME, TRANSACTION_INDEX_FILENAME),
        )
        verify_manifest(root)

        if interrupt_after_runtime_before_evidence:
            raise DecisionPathAtomicPersistenceError(
                DecisionPathAtomicFailureCodeV1.PERSISTENCE_INTERRUPTION,
                "INJECTED_INTERRUPT_AFTER_RUNTIME_BEFORE_EVIDENCE",
            )

        evidence_result: dict[str, Any] = {"ok": True, "skipped": True}
        if evidence_payload is not None:
            evidence_result = materialize_evidence_idempotent_v1(
                coordinator_root=root,
                evidence_payload=evidence_payload,
                fail=evidence_fail,
            )

        return {
            "ok": True,
            "duplicate_replay": False,
            "commit_identity": commit_identity,
            "commit_sequence": commit_sequence,
            "transaction_id": transaction_id,
            "idempotency_key": idempotency_key,
            "member_digests": member_digests,
            "confirmation": {
                "commit_identity": conf_out.get("commit_identity"),
                "commit_sequence": conf_out.get("commit_sequence"),
                "state_digest": member_digests.get(MEMBER_CONFIRMATION),
            },
            "dynamic_scope": {
                "commit_identity": scope_out.get("commit_identity"),
                "commit_sequence": scope_out.get("commit_sequence"),
                "state_digest": member_digests.get(MEMBER_DYNAMIC_SCOPE),
            },
            "accounting": acct_out,
            "decision_config": cfg_out,
            "evidence": evidence_result,
            "runtime_commit_retained_on_evidence_failure": True,
        }
    except Exception:
        # Incomplete staging never becomes live authority.
        shutil.rmtree(staging_tx, ignore_errors=True)
        raise
    finally:
        if staging_tx.exists():
            shutil.rmtree(staging_tx, ignore_errors=True)


def assert_member_digests_consistent_v1(
    marker: DecisionPathCommitMarkerV1,
    *,
    confirmation_digest: str | None = None,
    scope_digest: str | None = None,
    portfolio_digest: str | None = None,
) -> None:
    if confirmation_digest is not None:
        expected = marker.member_digests.get(MEMBER_CONFIRMATION)
        if expected and expected != confirmation_digest:
            raise DecisionPathAtomicPersistenceError(
                DecisionPathAtomicFailureCodeV1.MIXED_STATE_ROOT_COMMIT,
                f"confirmation:{confirmation_digest}!={expected}",
            )
    if scope_digest is not None:
        expected = marker.member_digests.get(MEMBER_DYNAMIC_SCOPE)
        if expected and expected != scope_digest:
            raise DecisionPathAtomicPersistenceError(
                DecisionPathAtomicFailureCodeV1.MIXED_STATE_ROOT_COMMIT,
                f"scope:{scope_digest}!={expected}",
            )
    if portfolio_digest is not None:
        expected = marker.member_digests.get(MEMBER_ACCOUNTING) or marker.portfolio_digest
        if expected and expected != portfolio_digest:
            raise DecisionPathAtomicPersistenceError(
                DecisionPathAtomicFailureCodeV1.MEMBER_DIGEST_MISMATCH,
                f"portfolio:{portfolio_digest}!={expected}",
            )
