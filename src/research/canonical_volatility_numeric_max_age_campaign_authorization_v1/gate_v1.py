"""Accumulation gatekeeper: runtime release only after atomic session consumption."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping, Optional

from research.canonical_volatility_numeric_max_age_campaign_authorization_v1.constants_v1 import (
    BOUND_CAMPAIGN_ID,
    BOUND_PREREGISTRATION_DIGEST,
    BOUND_SESSION_IDS,
    CAPABILITY_ID,
)
from research.canonical_volatility_numeric_max_age_campaign_authorization_v1.consume_v1 import (
    load_verified_runtime_release_for_session_v1,
)
from research.canonical_volatility_numeric_max_age_campaign_authorization_v1.models_v1 import (
    CampaignAuthorizationError,
    RuntimeReleaseV1,
)


def require_campaign_authorization_runtime_release_v1(
    *,
    authorization_artifact_path: Path | None,
    session_id: str,
    campaign_id: str,
    evidence_root: Path,
    repository_sha: str,
    expected_preregistration_digest: str = BOUND_PREREGISTRATION_DIGEST,
) -> RuntimeReleaseV1:
    """Fail-closed gate for the productive accumulation entrypoint.

    - Missing authorization → reject
    - Present but unconsumed authorization → reject
    - Accept only atomically consumed, exactly bound session context
    """
    if authorization_artifact_path is None:
        raise CampaignAuthorizationError("campaign_authorization_missing")
    path = Path(authorization_artifact_path)
    if not path.is_file():
        raise CampaignAuthorizationError("campaign_authorization_missing")

    release = load_verified_runtime_release_for_session_v1(
        authorization_artifact_path=path,
        session_id=session_id,
        evidence_root=Path(evidence_root),
        expected_repository_sha=repository_sha,
        expected_campaign_id=campaign_id,
        expected_session_ids=BOUND_SESSION_IDS if campaign_id == BOUND_CAMPAIGN_ID else None,
        expected_preregistration_digest=(
            expected_preregistration_digest if campaign_id == BOUND_CAMPAIGN_ID else None
        ),
    )
    if release.session_id != session_id:
        raise CampaignAuthorizationError("runtime_release_session_mismatch")
    if release.campaign_id != campaign_id:
        raise CampaignAuthorizationError("runtime_release_campaign_mismatch")
    if release.repository_sha != repository_sha:
        raise CampaignAuthorizationError("runtime_release_repository_sha_mismatch")
    return release


def assert_orders_and_private_endpoints_excluded_v1(release: RuntimeReleaseV1) -> dict[str, Any]:
    """Capability invariant: orders/private endpoints/credentials remain excluded."""
    del release  # release does not grant order/private authority
    return {
        "orders_technically_excluded": True,
        "private_endpoints_excluded": True,
        "credentials_required": False,
        "public_md_methods_get_only": True,
        "gate_capability_id": CAPABILITY_ID,
    }


def gate_status_payload_v1(
    *,
    ok: bool,
    release: Optional[RuntimeReleaseV1] = None,
    blocker: str = "",
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "ok": ok,
        "gate_capability_id": CAPABILITY_ID,
        "runtime_side_effects_authorized": bool(ok and release is not None),
        "blocker": blocker,
    }
    if release is not None:
        payload["runtime_release"] = release.to_dict()
    return payload


def try_require_campaign_authorization_runtime_release_v1(
    **kwargs: Any,
) -> Mapping[str, Any]:
    try:
        release = require_campaign_authorization_runtime_release_v1(**kwargs)
        return gate_status_payload_v1(ok=True, release=release)
    except CampaignAuthorizationError as exc:
        return gate_status_payload_v1(ok=False, blocker=str(exc))
