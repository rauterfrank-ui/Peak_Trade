"""G004 — durable post-attempt exchange reconciliation disposition (fail-closed).

Binds adjudicated reconciliation outcome to the durable POST attempt store
(correlation + envelope identity). Does not authorize POST, GET, or capital release.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from src.ops.full_core_live_path_composition_root_v1.current_productive_execution_lifecycle_root_binding_v1 import (
    ExecutionLifecycleRootBindingError,
    assert_correlation_identity_matches_envelope_v1,
)
from src.ops.full_core_live_path_composition_root_v1.final_order_envelope_v1 import (
    FinalOrderEnvelopeV1,
    assert_envelope_unmodified_v1,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_capital_guard_atomic_one_shot_v1 import (
    FullCoreAuthorizationBindingV1,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_exchange_reconciliation_v1 import (
    FullCoreExchangeReconciliationDecisionV1,
    FullCoreExchangeReconciliationIdentityV1,
    LocalSubmitOutcome,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_post_response_to_ack_mapper_v1 import (
    FullCorePostSubmitJoinResultV1,
)

CONTRACT_ID = "V2_G004_PERSISTED_RECONCILIATION_DISPOSITION_V1"
DISPOSITION_FILENAME = "full_core_post_attempt_exchange_reconciliation_disposition_v1.json"
PERSISTENCE_OWNER = (
    "ops.full_core_live_path_composition_root_v1."
    "current_productive_persisted_reconciliation_disposition_v1"
)
_SECRET_TOKENS = ("secret", "passphrase", "api_key", "apikey", "private_key")


class PersistedReconciliationDispositionError(RuntimeError):
    """Fail-closed persisted reconciliation disposition violation."""


def _utc_now_iso_v1() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def _canonical_json(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _assert_no_secrets(payload: Mapping[str, Any]) -> None:
    blob = _canonical_json(payload).lower()
    for token in _SECRET_TOKENS:
        if token in blob:
            raise PersistedReconciliationDispositionError(f"SECRET_TOKEN_PRESENT:{token}")


def disposition_path_v1(*, store_root: Path | str) -> Path:
    return Path(store_root) / DISPOSITION_FILENAME


def attempt_digest_v1(
    *,
    submit_attempt_id: str,
    envelope_digest: str,
) -> str:
    material = _canonical_json(
        {
            "submit_attempt_id": str(submit_attempt_id or "").strip(),
            "envelope_digest": str(envelope_digest or "").strip(),
        }
    )
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def _semantic_disposition_digest_v1(record: Mapping[str, Any]) -> str:
    material = {
        "reconciliation_outcome": record.get("reconciliation_outcome"),
        "local_submit_outcome": record.get("local_submit_outcome"),
        "identity_digest": record.get("identity_digest"),
        "reconciliation_complete": record.get("reconciliation_complete"),
        "recommended_atomic_state": record.get("recommended_atomic_state"),
        "typed_post_submit_outcome": record.get("typed_post_submit_outcome"),
    }
    return hashlib.sha256(_canonical_json(material).encode("utf-8")).hexdigest()


def build_reconciliation_disposition_record_v1(
    *,
    envelope: FinalOrderEnvelopeV1,
    binding: FullCoreAuthorizationBindingV1,
    identity: FullCoreExchangeReconciliationIdentityV1,
    decision: FullCoreExchangeReconciliationDecisionV1,
    local_submit_outcome: LocalSubmitOutcome,
    post_submit_join: FullCorePostSubmitJoinResultV1,
    submit_attempt_id: str,
    lane_id: str,
) -> dict[str, Any]:
    assert_envelope_unmodified_v1(envelope)
    digest = attempt_digest_v1(
        submit_attempt_id=submit_attempt_id,
        envelope_digest=envelope.envelope_digest,
    )
    return {
        "contract_id": CONTRACT_ID,
        "persistence_owner": PERSISTENCE_OWNER,
        "lane_id": str(lane_id or "").strip(),
        "account_scope": binding.account_scope,
        "execution_environment": binding.environment,
        "instrument_id": binding.instrument_id,
        "native_id": binding.native_id,
        "clordid": envelope.client_order_id,
        "envelope_id": envelope.envelope_id,
        "envelope_digest": envelope.envelope_digest,
        "submit_attempt_id": str(submit_attempt_id or "").strip(),
        "attempt_digest": digest,
        "venue_ord_id": str(post_submit_join.venue_order_id or "").strip() or None,
        "identity_digest": identity.identity_digest(),
        "local_submit_outcome": local_submit_outcome.value,
        "typed_post_submit_outcome": post_submit_join.typed_outcome,
        "reconciliation_outcome": decision.outcome,
        "reconciliation_complete": decision.reconciliation_complete,
        "recommended_atomic_state": decision.recommended_atomic_state,
        "ack_is_not_fill": True,
        "persistence_failure_is_not_exchange_rejection": True,
        "persisted_at_utc": _utc_now_iso_v1(),
    }


def load_persisted_reconciliation_disposition_v1(
    *,
    store_root: Path | str,
) -> dict[str, Any] | None:
    path = disposition_path_v1(store_root=store_root)
    if not path.is_file():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise PersistedReconciliationDispositionError("DISPOSITION_MALFORMED")
    return payload


def _load_enter_post_lifecycle_correlation_v1(*, store_root: Path | str) -> dict[str, Any] | None:
    from src.ops.full_core_live_path_composition_root_v1.current_productive_mandatory_new_risk_enter_post_admission_v1 import (
        load_enter_post_lifecycle_correlation_v1,
    )

    return load_enter_post_lifecycle_correlation_v1(store_root=store_root)


def _assert_authorization_binding_matches_envelope_and_correlation_v1(
    *,
    binding: FullCoreAuthorizationBindingV1,
    envelope: FinalOrderEnvelopeV1,
    correlation: Mapping[str, Any],
) -> None:
    """Binding must match envelope and durable correlation (fail-closed)."""
    assert_envelope_unmodified_v1(envelope)
    env_clord = str(envelope.client_order_id or "").strip()
    bind_clord = str(binding.clordid or "").strip()
    if not env_clord or not bind_clord:
        raise PersistedReconciliationDispositionError("CLORDID_REQUIRED")
    if bind_clord != env_clord:
        raise PersistedReconciliationDispositionError("BINDING_CLORDID_ENVELOPE_MISMATCH")
    corr_clord = str(correlation.get("clordid") or "").strip()
    if corr_clord and corr_clord != env_clord:
        raise PersistedReconciliationDispositionError("CORRELATION_CLORDID_ENVELOPE_MISMATCH")
    env_digest = str(envelope.envelope_digest or "").strip()
    bind_digest = str(binding.envelope_digest or "").strip()
    if not env_digest or not bind_digest:
        raise PersistedReconciliationDispositionError("ENVELOPE_DIGEST_REQUIRED")
    if bind_digest != env_digest:
        raise PersistedReconciliationDispositionError("BINDING_ENVELOPE_DIGEST_MISMATCH")
    corr_digest = str(correlation.get("envelope_digest") or "").strip()
    if corr_digest and corr_digest != env_digest:
        raise PersistedReconciliationDispositionError("CORRELATION_ENVELOPE_DIGEST_MISMATCH")


def _assert_reconciliation_identity_matches_attempt_v1(
    *,
    identity: FullCoreExchangeReconciliationIdentityV1,
    envelope: FinalOrderEnvelopeV1,
    submit_attempt_id: str,
    post_submit_join: FullCorePostSubmitJoinResultV1,
) -> None:
    """Reconciliation identity must align with POST attempt (not a parallel order key)."""
    env_clord = str(envelope.client_order_id or "").strip()
    if str(identity.clordid or "").strip() != env_clord:
        raise PersistedReconciliationDispositionError("IDENTITY_CLORDID_ENVELOPE_MISMATCH")
    if str(identity.envelope_digest or "").strip() != str(envelope.envelope_digest or "").strip():
        raise PersistedReconciliationDispositionError("IDENTITY_ENVELOPE_DIGEST_MISMATCH")
    if str(identity.submit_attempt_id or "").strip() != str(submit_attempt_id or "").strip():
        raise PersistedReconciliationDispositionError("IDENTITY_SUBMIT_ATTEMPT_MISMATCH")
    join_clord = str(post_submit_join.client_order_id or "").strip()
    if join_clord and join_clord != env_clord:
        raise PersistedReconciliationDispositionError("POST_JOIN_CLORDID_ENVELOPE_MISMATCH")
    venue_ord = str(post_submit_join.venue_order_id or "").strip()
    if venue_ord and str(identity.exchange_ord_id or "").strip() not in {"", venue_ord}:
        raise PersistedReconciliationDispositionError("IDENTITY_VENUE_ORD_ID_MISMATCH")


def _assert_correlation_binds_attempt_v1(
    *,
    store_root: Path | str,
    envelope: FinalOrderEnvelopeV1,
    submit_attempt_id: str,
) -> dict[str, Any]:
    correlation = _load_enter_post_lifecycle_correlation_v1(store_root=store_root)
    if correlation is None:
        raise PersistedReconciliationDispositionError("MISSING_LIFECYCLE_CORRELATION")
    try:
        assert_correlation_identity_matches_envelope_v1(
            correlation=correlation,
            envelope=envelope,
        )
    except ExecutionLifecycleRootBindingError as exc:
        raise PersistedReconciliationDispositionError(str(exc)) from exc
    corr_attempt = str(correlation.get("submit_attempt_id") or "").strip()
    if corr_attempt != str(submit_attempt_id or "").strip():
        raise PersistedReconciliationDispositionError("SUBMIT_ATTEMPT_ID_CORRELATION_MISMATCH")
    return correlation


def persist_post_attempt_reconciliation_disposition_v1(
    *,
    store_root: Path | str,
    envelope: FinalOrderEnvelopeV1,
    binding: FullCoreAuthorizationBindingV1,
    identity: FullCoreExchangeReconciliationIdentityV1,
    decision: FullCoreExchangeReconciliationDecisionV1,
    local_submit_outcome: LocalSubmitOutcome,
    post_submit_join: FullCorePostSubmitJoinResultV1,
    submit_attempt_id: str,
    lane_id: str | None = None,
) -> dict[str, Any]:
    """Atomically persist reconciliation disposition for one POST attempt store."""

    correlation = _assert_correlation_binds_attempt_v1(
        store_root=store_root,
        envelope=envelope,
        submit_attempt_id=submit_attempt_id,
    )
    lane = str(lane_id or correlation.get("account_scope") or binding.account_scope).strip()
    if not lane:
        raise PersistedReconciliationDispositionError("LANE_ID_REQUIRED")
    if (
        str(binding.account_scope or "").strip()
        != str(correlation.get("account_scope") or "").strip()
    ):
        raise PersistedReconciliationDispositionError("ACCOUNT_SCOPE_CORRELATION_MISMATCH")
    if str(binding.native_id or "").strip() != str(correlation.get("native_id") or "").strip():
        raise PersistedReconciliationDispositionError("NATIVE_ID_CORRELATION_MISMATCH")
    _assert_authorization_binding_matches_envelope_and_correlation_v1(
        binding=binding,
        envelope=envelope,
        correlation=correlation,
    )
    _assert_reconciliation_identity_matches_attempt_v1(
        identity=identity,
        envelope=envelope,
        submit_attempt_id=submit_attempt_id,
        post_submit_join=post_submit_join,
    )

    record = build_reconciliation_disposition_record_v1(
        envelope=envelope,
        binding=binding,
        identity=identity,
        decision=decision,
        local_submit_outcome=local_submit_outcome,
        post_submit_join=post_submit_join,
        submit_attempt_id=submit_attempt_id,
        lane_id=lane,
    )
    _assert_no_secrets(record)
    semantic = _semantic_disposition_digest_v1(record)

    root = Path(store_root)
    root.mkdir(parents=True, exist_ok=True)
    path = disposition_path_v1(store_root=root)
    existing = load_persisted_reconciliation_disposition_v1(store_root=root)
    if existing is not None:
        if _semantic_disposition_digest_v1(existing) == semantic:
            return existing
        raise PersistedReconciliationDispositionError("CONFLICTING_RECONCILIATION_DISPOSITION")

    record["semantic_disposition_digest"] = semantic
    tmp = path.with_suffix(path.suffix + ".tmp")
    try:
        tmp.write_text(json.dumps(record, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        os.replace(tmp, path)
    except OSError as exc:
        if tmp.is_file():
            tmp.unlink(missing_ok=True)
        raise PersistedReconciliationDispositionError("PERSISTENCE_FAILURE") from exc
    loaded = load_persisted_reconciliation_disposition_v1(store_root=root)
    if loaded is None:
        raise PersistedReconciliationDispositionError("PERSISTENCE_VERIFY_FAILED")
    return loaded


def lookup_post_attempt_reconciliation_disposition_v1(
    *,
    store_root: Path | str,
    envelope: FinalOrderEnvelopeV1,
    binding: FullCoreAuthorizationBindingV1,
    submit_attempt_id: str,
    lane_id: str,
) -> dict[str, Any]:
    """Restart-safe lookup with fail-closed identity binding checks."""

    record = load_persisted_reconciliation_disposition_v1(store_root=store_root)
    if record is None:
        raise PersistedReconciliationDispositionError("DISPOSITION_NOT_FOUND")
    _assert_correlation_binds_attempt_v1(
        store_root=store_root,
        envelope=envelope,
        submit_attempt_id=submit_attempt_id,
    )
    if str(record.get("lane_id") or "") != str(lane_id or "").strip():
        raise PersistedReconciliationDispositionError("WRONG_LANE")
    if str(record.get("account_scope") or "") != str(binding.account_scope or "").strip():
        raise PersistedReconciliationDispositionError("WRONG_ACCOUNT")
    if str(record.get("native_id") or "") != str(binding.native_id or "").strip():
        raise PersistedReconciliationDispositionError("WRONG_INSTRUMENT")
    env_clord = str(envelope.client_order_id or "").strip()
    if str(record.get("clordid") or "").strip() != env_clord:
        raise PersistedReconciliationDispositionError("WRONG_CLORDID")
    if str(binding.clordid or "").strip() != env_clord:
        raise PersistedReconciliationDispositionError("BINDING_CLORDID_ENVELOPE_MISMATCH")
    if (
        str(record.get("envelope_digest") or "").strip()
        != str(envelope.envelope_digest or "").strip()
    ):
        raise PersistedReconciliationDispositionError("WRONG_ENVELOPE_DIGEST")
    if str(record.get("envelope_id") or "") != str(envelope.envelope_id or "").strip():
        raise PersistedReconciliationDispositionError("WRONG_ENVELOPE_ID")
    expected_digest = attempt_digest_v1(
        submit_attempt_id=submit_attempt_id,
        envelope_digest=envelope.envelope_digest,
    )
    if str(record.get("attempt_digest") or "") != expected_digest:
        raise PersistedReconciliationDispositionError("WRONG_ATTEMPT_DIGEST")
    return record


__all__ = [
    "CONTRACT_ID",
    "DISPOSITION_FILENAME",
    "PERSISTENCE_OWNER",
    "PersistedReconciliationDispositionError",
    "attempt_digest_v1",
    "build_reconciliation_disposition_record_v1",
    "disposition_path_v1",
    "load_persisted_reconciliation_disposition_v1",
    "lookup_post_attempt_reconciliation_disposition_v1",
    "persist_post_attempt_reconciliation_disposition_v1",
]
