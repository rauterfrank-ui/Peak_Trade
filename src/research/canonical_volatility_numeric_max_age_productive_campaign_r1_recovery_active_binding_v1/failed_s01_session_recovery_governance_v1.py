"""Machine-readable governance for CONSUMED + PARTIAL + NO_CARRIER + TERMINAL_FAIL S01.

Does not mutate evidence, authorize sessions, or rematerialize campaigns.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Optional

from research.canonical_volatility_numeric_max_age_campaign_authorization_v1.ledgers_v1 import (
    find_session_consumption_v1,
    load_consumption_records_v1,
    resolve_ledger_path_v1,
)
from research.canonical_volatility_numeric_max_age_productive_campaign_r1_recovery_active_binding_v1.constants_v1 import (
    TOMBSTONE_ABANDONED_CAMPAIGN_ID,
)
from research.canonical_volatility_numeric_max_age_productive_campaign_r1_recovery_active_binding_v1.models_v1 import (
    ActiveCampaignBindingV1,
    ProductiveCampaignR1RecoveryError,
)

SCHEMA_FAILED_S01_GOVERNANCE = (
    "canonical_volatility_numeric_max_age_productive_campaign_failed_s01_governance/v1"
)

FAILED_S01_TERMINAL_STATES: frozenset[str] = frozenset(
    {
        "FAIL_CLOSED_AFTER_CONSUMPTION",
        "FAIL_CLOSED_INTEGRITY",
        "FAIL_CLOSED_SESSION_02_ISOLATION",
    }
)

S01_RETRY_SAME_SESSION_FORBIDDEN = True
S02_START_AFTER_FAILED_S01_FORBIDDEN = True
REMAINING_AUTH_SLOT_IS_NOT_RECOVERY = True
FRESH_CAMPAIGN_REMATERIALIZATION_REQUIRED_FOR_SUCCESS_PATH = True
FAILED_EVIDENCE_IMMUTABLE_FORENSIC = True


@dataclass(frozen=True)
class FailedS01CampaignGovernanceV1:
    schema_version: str
    campaign_id: str
    session_01_id: str
    session_02_id: str
    failed_s01_closed: bool
    s01_consumed: bool
    s01_terminal_fail_closed: bool
    retained_estimate_carrier_present: bool
    s01_retry_same_session_forbidden: bool
    s02_start_forbidden: bool
    remaining_auth_slot_is_not_recovery: bool
    fresh_campaign_rematerialization_required: bool
    failed_evidence_immutable_forensic: bool
    disposition_reason_codes: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "campaign_id": self.campaign_id,
            "session_01_id": self.session_01_id,
            "session_02_id": self.session_02_id,
            "failed_s01_closed": self.failed_s01_closed,
            "s01_consumed": self.s01_consumed,
            "s01_terminal_fail_closed": self.s01_terminal_fail_closed,
            "retained_estimate_carrier_present": self.retained_estimate_carrier_present,
            "s01_retry_same_session_forbidden": self.s01_retry_same_session_forbidden,
            "s02_start_forbidden": self.s02_start_forbidden,
            "remaining_auth_slot_is_not_recovery": self.remaining_auth_slot_is_not_recovery,
            "fresh_campaign_rematerialization_required": (
                self.fresh_campaign_rematerialization_required
            ),
            "failed_evidence_immutable_forensic": self.failed_evidence_immutable_forensic,
            "disposition_reason_codes": list(self.disposition_reason_codes),
        }


def _load_session_manifest_terminal_state_v1(path: Path) -> Optional[str]:
    if not path.is_file() or path.stat().st_size <= 0:
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    if not isinstance(payload, Mapping):
        return None
    return str(payload.get("terminal_state") or "") or None


def evaluate_failed_s01_campaign_governance_v1(
    *,
    binding: ActiveCampaignBindingV1,
    evidence_root: Path,
    authorization_artifact_path: Optional[Path] = None,
    authorization_id: Optional[str] = None,
) -> FailedS01CampaignGovernanceV1:
    """Detect failed-S01 closed state from durable runtime evidence (read-only)."""
    if binding.campaign_id == TOMBSTONE_ABANDONED_CAMPAIGN_ID:
        raise ProductiveCampaignR1RecoveryError("tombstone_campaign_not_failed_s01_subject")

    root = Path(evidence_root)
    carrier_path = root / binding.retained_estimate_lifecycle_carrier_path
    carrier_present = carrier_path.is_file() and carrier_path.stat().st_size > 0

    s01_manifest = (
        root
        / "docs/evidence/canonical_volatility_max_age_productive_research_evidence_ledger_v1"
        / f"campaigns/{binding.campaign_id}/sessions/session_01_manifest.json"
    )
    terminal_state = _load_session_manifest_terminal_state_v1(s01_manifest)
    s01_terminal_fail = terminal_state in FAILED_S01_TERMINAL_STATES

    s01_consumed = False
    if authorization_artifact_path is not None and authorization_id:
        try:
            from research.canonical_volatility_numeric_max_age_campaign_authorization_v1.artifact_v1 import (
                load_campaign_authorization_artifact_v1,
            )

            artifact = load_campaign_authorization_artifact_v1(Path(authorization_artifact_path))
            cons_path = resolve_ledger_path_v1(
                evidence_root=root,
                relative_or_absolute=artifact.consumption_ledger_path,
            )
            records = load_consumption_records_v1(cons_path) if cons_path.exists() else []
            s01_consumed = (
                find_session_consumption_v1(
                    records,
                    authorization_id=str(authorization_id),
                    session_id=binding.session_01_id,
                )
                is not None
            )
        except Exception:
            s01_consumed = False

    failed_closed = bool(
        s01_consumed and s01_terminal_fail and not carrier_present and binding.campaign_id
    )
    reasons: list[str] = []
    if s01_consumed:
        reasons.append("S01_AUTHORIZATION_CONSUMED")
    if s01_terminal_fail:
        reasons.append("S01_TERMINAL_FAIL_CLOSED")
    if not carrier_present:
        reasons.append("RETAINED_ESTIMATE_CARRIER_ABSENT")
    if failed_closed:
        reasons.append("FAILED_S01_CAMPAIGN_CLOSED")

    return FailedS01CampaignGovernanceV1(
        schema_version=SCHEMA_FAILED_S01_GOVERNANCE,
        campaign_id=binding.campaign_id,
        session_01_id=binding.session_01_id,
        session_02_id=binding.session_02_id,
        failed_s01_closed=failed_closed,
        s01_consumed=s01_consumed,
        s01_terminal_fail_closed=s01_terminal_fail,
        retained_estimate_carrier_present=carrier_present,
        s01_retry_same_session_forbidden=S01_RETRY_SAME_SESSION_FORBIDDEN,
        s02_start_forbidden=S02_START_AFTER_FAILED_S01_FORBIDDEN,
        remaining_auth_slot_is_not_recovery=REMAINING_AUTH_SLOT_IS_NOT_RECOVERY,
        fresh_campaign_rematerialization_required=(
            FRESH_CAMPAIGN_REMATERIALIZATION_REQUIRED_FOR_SUCCESS_PATH if failed_closed else False
        ),
        failed_evidence_immutable_forensic=FAILED_EVIDENCE_IMMUTABLE_FORENSIC,
        disposition_reason_codes=tuple(reasons),
    )


def assert_session_start_allowed_under_failed_s01_governance_v1(
    *,
    session_id: str,
    governance: FailedS01CampaignGovernanceV1,
) -> None:
    """Fail-closed gate for preregistered runner preflight (no mutation)."""
    if not governance.failed_s01_closed:
        return
    sid = str(session_id or "").strip()
    if sid == governance.session_01_id and governance.s01_retry_same_session_forbidden:
        raise ProductiveCampaignR1RecoveryError("failed_s01_retry_same_session_forbidden")
    if sid == governance.session_02_id and governance.s02_start_forbidden:
        raise ProductiveCampaignR1RecoveryError("failed_s01_s02_start_forbidden")
    if sid in (governance.session_01_id, governance.session_02_id):
        raise ProductiveCampaignR1RecoveryError("failed_s01_campaign_session_start_forbidden")
