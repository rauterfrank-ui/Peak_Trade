"""Sole ACTIVE productive-campaign binding load/verify."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping, Optional

from research.canonical_volatility_numeric_max_age_productive_campaign_r1_recovery_active_binding_v1.constants_v1 import (
    ACTIVE_BINDING_REL_PATH,
    ACTIVE_BINDING_STATUS,
    CROSS_SHA_REUSE_ALLOWED,
    OWNER_POLICY,
    R1_PREREGISTRATION_REL_PATH,
    SCHEMA_ACTIVE_BINDING,
    SYNTHETIC_S01_ALLOWED,
)
from research.canonical_volatility_numeric_max_age_productive_campaign_r1_recovery_active_binding_v1.digest_v1 import (
    artifact_digest_v1,
)
from research.canonical_volatility_numeric_max_age_productive_campaign_r1_recovery_active_binding_v1.disposition_v1 import (
    assert_campaign_not_tombstone_v1,
    assert_session_not_tombstone_v1,
)
from research.canonical_volatility_numeric_max_age_productive_campaign_r1_recovery_active_binding_v1.identity_v1 import (
    derive_r1_campaign_identity_v1,
)
from research.canonical_volatility_numeric_max_age_productive_campaign_r1_recovery_active_binding_v1.models_v1 import (
    ActiveCampaignBindingV1,
    ProductiveCampaignR1RecoveryError,
    require_bool,
    require_mapping,
    require_str,
    require_str_tuple,
)
from research.canonical_volatility_numeric_max_age_productive_campaign_r1_recovery_active_binding_v1.preregistration_v1 import (
    build_r1_active_preregistration_payload_v1,
)


def build_active_campaign_binding_v1(
    *,
    repository_sha: str,
    preregistration_artifact_path: str = R1_PREREGISTRATION_REL_PATH,
    preregistration_digest: Optional[str] = None,
) -> ActiveCampaignBindingV1:
    identity = derive_r1_campaign_identity_v1(repository_sha=repository_sha)
    assert_campaign_not_tombstone_v1(identity["campaign_id"])
    assert_session_not_tombstone_v1(identity["session_01_id"])
    assert_session_not_tombstone_v1(identity["session_02_id"])
    if preregistration_digest is None:
        preg = build_r1_active_preregistration_payload_v1(repository_sha=repository_sha)
        preregistration_digest = str(preg["preregistration_digest"])
    provisional: dict[str, Any] = {
        "campaign_id": identity["campaign_id"],
        "early_estimate_producer_session_id": identity["session_01_id"],
        "evidence_write_authorized": False,
        "execution_authorized": False,
        "late_age_observation_session_id": identity["session_02_id"],
        "network_authorized": False,
        "owner_policy": OWNER_POLICY,
        "preregistration_artifact_path": str(preregistration_artifact_path),
        "preregistration_digest": str(preregistration_digest),
        "repository_sha": str(repository_sha).strip(),
        "schema_version": SCHEMA_ACTIVE_BINDING,
        "session_01_id": identity["session_01_id"],
        "session_02_id": identity["session_02_id"],
        "session_ids": [identity["session_01_id"], identity["session_02_id"]],
        "status": ACTIVE_BINDING_STATUS,
        "typed_volatility_persistence_path": identity["typed_volatility_persistence_path"],
        "retained_estimate_lifecycle_carrier_path": identity[
            "retained_estimate_lifecycle_carrier_path"
        ],
    }
    provisional["artifact_digest"] = artifact_digest_v1(provisional)
    return parse_active_campaign_binding_v1(provisional)


def parse_active_campaign_binding_v1(payload: Mapping[str, Any]) -> ActiveCampaignBindingV1:
    raw = require_mapping(payload, field="active_binding")
    required = {
        "schema_version",
        "status",
        "owner_policy",
        "repository_sha",
        "campaign_id",
        "session_ids",
        "session_01_id",
        "session_02_id",
        "preregistration_artifact_path",
        "preregistration_digest",
        "typed_volatility_persistence_path",
        "retained_estimate_lifecycle_carrier_path",
        "early_estimate_producer_session_id",
        "late_age_observation_session_id",
        "execution_authorized",
        "network_authorized",
        "evidence_write_authorized",
        "artifact_digest",
    }
    missing = sorted(required - set(raw.keys()))
    if missing:
        raise ProductiveCampaignR1RecoveryError("active_binding_field_missing:" + ",".join(missing))
    unknown = sorted(set(raw.keys()) - required)
    if unknown:
        raise ProductiveCampaignR1RecoveryError("active_binding_unknown_field:" + ",".join(unknown))

    session_ids = require_str_tuple(raw, "session_ids", count=2)
    session_01 = require_str(raw, "session_01_id")
    session_02 = require_str(raw, "session_02_id")
    if session_ids != (session_01, session_02):
        raise ProductiveCampaignR1RecoveryError("active_binding_session_tuple_mismatch")

    return ActiveCampaignBindingV1(
        schema_version=require_str(raw, "schema_version"),
        status=require_str(raw, "status"),
        owner_policy=require_str(raw, "owner_policy"),
        repository_sha=require_str(raw, "repository_sha"),
        campaign_id=require_str(raw, "campaign_id"),
        session_ids=session_ids,
        session_01_id=session_01,
        session_02_id=session_02,
        preregistration_artifact_path=require_str(raw, "preregistration_artifact_path"),
        preregistration_digest=require_str(raw, "preregistration_digest"),
        typed_volatility_persistence_path=require_str(raw, "typed_volatility_persistence_path"),
        retained_estimate_lifecycle_carrier_path=require_str(
            raw, "retained_estimate_lifecycle_carrier_path"
        ),
        early_estimate_producer_session_id=require_str(raw, "early_estimate_producer_session_id"),
        late_age_observation_session_id=require_str(raw, "late_age_observation_session_id"),
        execution_authorized=require_bool(raw, "execution_authorized", expected=False),
        network_authorized=require_bool(raw, "network_authorized", expected=False),
        evidence_write_authorized=require_bool(raw, "evidence_write_authorized", expected=False),
        artifact_digest=require_str(raw, "artifact_digest"),
    )


def verify_active_campaign_binding_v1(
    binding: ActiveCampaignBindingV1 | Mapping[str, Any],
    *,
    expected_repository_sha: Optional[str] = None,
) -> ActiveCampaignBindingV1:
    parsed = (
        binding
        if isinstance(binding, ActiveCampaignBindingV1)
        else parse_active_campaign_binding_v1(binding)
    )
    payload = parsed.to_dict()
    if parsed.artifact_digest != artifact_digest_v1(payload):
        raise ProductiveCampaignR1RecoveryError("active_binding_digest_mismatch")
    if parsed.schema_version != SCHEMA_ACTIVE_BINDING:
        raise ProductiveCampaignR1RecoveryError("active_binding_schema_mismatch")
    if parsed.status != ACTIVE_BINDING_STATUS:
        raise ProductiveCampaignR1RecoveryError("active_binding_status_mismatch")
    if parsed.owner_policy != OWNER_POLICY:
        raise ProductiveCampaignR1RecoveryError("active_binding_owner_policy_mismatch")
    assert_campaign_not_tombstone_v1(parsed.campaign_id)
    assert_session_not_tombstone_v1(parsed.session_01_id)
    assert_session_not_tombstone_v1(parsed.session_02_id)
    expected_identity = derive_r1_campaign_identity_v1(repository_sha=parsed.repository_sha)
    if parsed.campaign_id != expected_identity["campaign_id"]:
        raise ProductiveCampaignR1RecoveryError("active_binding_campaign_not_derived")
    if parsed.session_01_id != expected_identity["session_01_id"]:
        raise ProductiveCampaignR1RecoveryError("active_binding_session_01_not_derived")
    if parsed.session_02_id != expected_identity["session_02_id"]:
        raise ProductiveCampaignR1RecoveryError("active_binding_session_02_not_derived")
    if parsed.early_estimate_producer_session_id != parsed.session_01_id:
        raise ProductiveCampaignR1RecoveryError("active_binding_early_session_mismatch")
    if parsed.late_age_observation_session_id != parsed.session_02_id:
        raise ProductiveCampaignR1RecoveryError("active_binding_late_session_mismatch")
    if (
        parsed.typed_volatility_persistence_path
        != expected_identity["typed_volatility_persistence_path"]
    ):
        raise ProductiveCampaignR1RecoveryError("active_binding_persistence_path_mismatch")
    if (
        parsed.retained_estimate_lifecycle_carrier_path
        != expected_identity["retained_estimate_lifecycle_carrier_path"]
    ):
        raise ProductiveCampaignR1RecoveryError("active_binding_carrier_path_mismatch")
    if expected_repository_sha is not None and parsed.repository_sha != expected_repository_sha:
        raise ProductiveCampaignR1RecoveryError("active_binding_repository_sha_mismatch")
    if CROSS_SHA_REUSE_ALLOWED or SYNTHETIC_S01_ALLOWED:
        raise ProductiveCampaignR1RecoveryError("invariant_flags_corrupted")
    return parsed


def load_active_campaign_binding_v1(
    *,
    repo_root: Path,
    relative_path: str = ACTIVE_BINDING_REL_PATH,
    expected_repository_sha: Optional[str] = None,
) -> ActiveCampaignBindingV1:
    path = Path(repo_root) / relative_path
    if not path.is_file():
        raise ProductiveCampaignR1RecoveryError("active_binding_missing")
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ProductiveCampaignR1RecoveryError("active_binding_parse_error") from exc
    if isinstance(raw, list):
        raise ProductiveCampaignR1RecoveryError("multiple_active_bindings_forbidden")
    return verify_active_campaign_binding_v1(raw, expected_repository_sha=expected_repository_sha)


def assert_exactly_one_active_binding_file_v1(*, repo_root: Path) -> Path:
    """Fail closed if zero or multiple ACTIVE binding artifacts exist under governance."""
    gov = Path(repo_root) / "config" / "governance"
    if not gov.is_dir():
        raise ProductiveCampaignR1RecoveryError("active_binding_missing")
    matches: list[Path] = []
    for path in sorted(
        gov.glob("canonical_volatility_numeric_max_age_productive_campaign_active_binding*.json")
    ):
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            raise ProductiveCampaignR1RecoveryError("active_binding_parse_error") from None
        if isinstance(raw, Mapping) and str(raw.get("status") or "") == ACTIVE_BINDING_STATUS:
            matches.append(path)
    if not matches:
        raise ProductiveCampaignR1RecoveryError("active_binding_missing")
    if len(matches) != 1:
        raise ProductiveCampaignR1RecoveryError("multiple_active_bindings_forbidden")
    return matches[0]
