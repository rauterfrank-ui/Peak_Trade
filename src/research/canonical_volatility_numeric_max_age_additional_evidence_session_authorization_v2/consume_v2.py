"""Single-use consumption and revocation for additional-evidence auth v2."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional, Sequence

from research.canonical_volatility_numeric_max_age_additional_evidence_session_authorization_v2.artifact_v2 import (
    load_additional_evidence_session_authorization_v2,
    verify_additional_evidence_session_authorization_v2,
    write_additional_evidence_session_authorization_v2,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_session_authorization_v2.confirm_token_v2 import (
    assert_confirm_token_matches_v2,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_session_authorization_v2.constants_v2 import (
    CONSUMPTION_STATE_CONSUMED,
    CONSUMPTION_STATE_REVOKED,
    FORBIDDEN_SIDE_EFFECT_BEFORE_CONSUME,
    REVOCATION_STATE_REVOKED,
    SIDE_EFFECT_AUTHORIZATION_CONSUMED,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_session_authorization_v2.ledgers_v2 import (
    append_consumption_record_v2,
    append_revocation_record_v2,
    assert_not_revoked_fail_closed_v2,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_session_authorization_v2.models_v2 import (
    AdditionalEvidenceSessionAuthorizationV2,
    AdditionalEvidenceSessionAuthorizationV2Error,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_session_authorization_v2.side_effect_order_v2 import (
    assert_consume_before_side_effects_v2,
)


def consume_additional_evidence_session_authorization_v2(
    *,
    repo_root: Path,
    authorization_path: Path,
    confirm_token: str,
    side_effect_probe: Sequence[str] | None = None,
    previously_seen_fingerprints: frozenset[str] | None = None,
) -> dict[str, Any]:
    """Atomically consume authorization before any session side effects."""
    root = Path(repo_root)
    probe = list(side_effect_probe or [])
    # Consumption itself is the first allowed durable side-effect marker.
    assert_consume_before_side_effects_v2(probe)

    artifact = load_additional_evidence_session_authorization_v2(Path(authorization_path))
    verified = verify_additional_evidence_session_authorization_v2(
        artifact,
        repo_root=root,
        require_unconsumed=True,
        require_unrevoked=True,
    )
    assert_not_revoked_fail_closed_v2(
        revocation_ledger_path=root / verified.revocation_ledger_path,
        authorization_id=verified.authorization_id,
    )
    assert_confirm_token_matches_v2(
        artifact_fingerprint=verified.confirm_token_fingerprint,
        artifact_digest=verified.confirm_token_digest,
        artifact_binding=verified.confirm_token_binding_sha256,
        confirm_token=confirm_token,
        authorization_id=verified.authorization_id,
        preregistration_id=verified.preregistration_id,
        preregistration_digest=verified.preregistration_digest,
        execution_sha=verified.execution_sha,
        previously_seen_fingerprints=previously_seen_fingerprints,
    )

    # Durable consumption ledger first.
    record = append_consumption_record_v2(
        consumption_ledger_path=root / verified.consumption_ledger_path,
        authorization_id=verified.authorization_id,
        authorization_digest=verified.authorization_digest,
        preregistration_id=verified.preregistration_id,
        session_id=verified.preregistration_id,
    )

    updated_payload = verified.to_dict()
    updated_payload["consumption_state"] = CONSUMPTION_STATE_CONSUMED
    # Recompute digest after state mutation.
    from research.canonical_volatility_numeric_max_age_additional_evidence_session_authorization_v2.artifact_v2 import (
        compute_authorization_digest_v2,
        parse_additional_evidence_session_authorization_v2,
    )

    updated_payload["authorization_digest"] = compute_authorization_digest_v2(updated_payload)
    updated = parse_additional_evidence_session_authorization_v2(updated_payload)
    write_additional_evidence_session_authorization_v2(
        output_path=Path(authorization_path), artifact=updated
    )

    probe_after = list(probe) + [SIDE_EFFECT_AUTHORIZATION_CONSUMED]
    assert_consume_before_side_effects_v2(probe_after)
    for forbidden in FORBIDDEN_SIDE_EFFECT_BEFORE_CONSUME:
        if forbidden in probe:
            raise AdditionalEvidenceSessionAuthorizationV2Error(
                f"side_effect_before_consume:{forbidden}"
            )

    return {
        "ok": True,
        "authorization_id": updated.authorization_id,
        "authorization_digest": updated.authorization_digest,
        "consumption_record": record,
        "consumption_state": updated.consumption_state,
        "side_effect_probe": probe_after,
    }


def revoke_additional_evidence_session_authorization_v2(
    *,
    repo_root: Path,
    authorization_path: Path,
    reason: str,
) -> dict[str, Any]:
    root = Path(repo_root)
    artifact = load_additional_evidence_session_authorization_v2(Path(authorization_path))
    record = append_revocation_record_v2(
        revocation_ledger_path=root / artifact.revocation_ledger_path,
        authorization_id=artifact.authorization_id,
        authorization_digest=artifact.authorization_digest,
        reason=reason,
    )
    payload = artifact.to_dict()
    payload["revocation_state"] = REVOCATION_STATE_REVOKED
    payload["consumption_state"] = CONSUMPTION_STATE_REVOKED
    from research.canonical_volatility_numeric_max_age_additional_evidence_session_authorization_v2.artifact_v2 import (
        compute_authorization_digest_v2,
        parse_additional_evidence_session_authorization_v2,
    )

    payload["authorization_digest"] = compute_authorization_digest_v2(payload)
    updated = parse_additional_evidence_session_authorization_v2(payload)
    write_additional_evidence_session_authorization_v2(
        output_path=Path(authorization_path), artifact=updated
    )
    return {
        "ok": True,
        "authorization_id": updated.authorization_id,
        "revocation_record": record,
        "revocation_state": updated.revocation_state,
    }
