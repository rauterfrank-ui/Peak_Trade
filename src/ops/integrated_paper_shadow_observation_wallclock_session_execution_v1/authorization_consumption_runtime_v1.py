"""Wallclock authorization consumption — V1 quarantined; productive path is v2 gatekeeper."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional, Set

from src.ops.canonical_wallclock_authorization_consumption_authority_and_mandatory_bindings_v1.constants_v1 import (
    AUTHORIZATION_SCHEMA_REJECTED_LEGACY,
)
from src.ops.canonical_wallclock_authorization_consumption_authority_and_mandatory_bindings_v1.wallclock_v2_gatekeeper_v1 import (
    consume_authorization_for_wallclock_start_via_v2_gatekeeper_v1,
)
from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.wallclock_evidence_v1 import (
    WallclockEvidenceWriterV1,
)
from src.ops.paper_shadow_observation_operator_go_session_preregistration_v1.authorization_artifact_v1 import (
    AuthorizationArtifactV1,
)
from src.ops.paper_shadow_observation_operator_go_session_preregistration_v1.operator_go_contract_v1 import (
    OperatorGoContractV1,
)
from src.ops.paper_shadow_observation_operator_go_session_preregistration_v1.preregistration_contract_v1 import (
    SessionPreregistrationContractV1,
)


class AuthorizationConsumptionError(RuntimeError):
    """Fail-closed consumption error."""


@dataclass
class AuthorizationConsumptionResultV1:
    ok: bool
    blockers: list[str] = field(default_factory=list)
    consumed_artifact: Optional[AuthorizationArtifactV1] = None
    confirm_token_fingerprint: str = ""
    consumption_record: dict[str, Any] = field(default_factory=dict)
    transport_open_allowed: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "blockers": list(self.blockers),
            "confirm_token_fingerprint": self.confirm_token_fingerprint,
            "consumption_record": dict(self.consumption_record),
            "transport_open_allowed": self.transport_open_allowed,
            "consumed_artifact": None,
            "session_started": False,
        }


def consume_authorization_for_wallclock_start_v1(
    *,
    prereg: SessionPreregistrationContractV1,
    go: OperatorGoContractV1,
    artifact: AuthorizationArtifactV1 | None = None,
    confirm_token: str,
    evidence_writer: WallclockEvidenceWriterV1,
    artifact_path: Path,
    now_unix: float,
    expected_repository_sha: str,
    fingerprint_ledger_path: Path,
    known_session_ids: Optional[Set[str]] = None,
) -> AuthorizationConsumptionResultV1:
    """Compatibility wrapper: AuthorizationArtifactV1 is never productively consumable.

    Productive wallclock consumption must use authorization_artifact_v2 via the
    canonical gatekeeper. Passing a V1 artifact object is rejected with
    AUTHORIZATION_SCHEMA_REJECTED_LEGACY and zero session side effects.
    """
    if artifact is not None:
        return AuthorizationConsumptionResultV1(
            ok=False,
            blockers=[AUTHORIZATION_SCHEMA_REJECTED_LEGACY],
            transport_open_allowed=False,
            consumption_record={
                "classification": "LEGACY_PRODUCTIVE_AUTHORITY_RETIRED",
                "consumable": False,
                "session_start_reachable": False,
            },
        )

    result = consume_authorization_for_wallclock_start_via_v2_gatekeeper_v1(
        prereg=prereg,
        go=go,
        confirm_token=confirm_token,
        evidence_writer=evidence_writer,
        artifact_path=artifact_path,
        now_unix=now_unix,
        expected_repository_sha=expected_repository_sha,
        fingerprint_ledger_path=fingerprint_ledger_path,
        known_session_ids=known_session_ids,
    )
    return AuthorizationConsumptionResultV1(
        ok=result.ok,
        blockers=list(result.blockers),
        confirm_token_fingerprint=result.confirm_token_fingerprint,
        transport_open_allowed=result.transport_open_allowed,
        consumption_record={
            "consumption_id": result.consumption_id,
            "canonical_schema": "authorization_artifact_v2",
            "session_started": False,
        },
    )
