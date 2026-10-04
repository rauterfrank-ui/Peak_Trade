"""Validate run-specific Owner-GO binding without consuming or persisting authorization."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.ops.canonical_shadow_runtime_enablement_v1.constants_v1 import (
    SHADOW_ACTIVATION_OPERATOR_GO,
    SHADOW_OBSERVATION_OPERATOR_GO,
)
from src.ops.paper_shadow_bounded_orchestrator_v1.run_contract_v1 import (
    PaperShadowRunContractV1,
    RunContractError,
)


@dataclass(frozen=True)
class OwnerGoValidationResultV1:
    ok: bool
    owner_go_present: bool
    owner_go_consumed: bool
    blockers: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "OWNER_GO_PRESENT": self.owner_go_present,
            "OWNER_GO_CONSUMED": self.owner_go_consumed,
            "blockers": list(self.blockers),
            "OWNER_GO_VALIDATOR_READY": True,
        }


def validate_owner_go_authorization_v1(
    *,
    contract: PaperShadowRunContractV1,
    authorization_path: Path | None = None,
    observation_token: str | None = None,
    activation_token: str | None = None,
    consume: bool = False,
) -> OwnerGoValidationResultV1:
    """Fail-closed binding check. ``consume=True`` is for tests only (in-memory flag)."""
    if consume:
        raise RunContractError("OWNER_GO_CONSUMPTION_FORBIDDEN_IN_VALIDATOR")

    blockers: list[str] = []
    obs = str(observation_token or "").strip()
    act = str(activation_token or "").strip()

    if authorization_path is not None:
        ap = Path(authorization_path).resolve()
        if not ap.is_file():
            blockers.append("AUTHORIZATION_FILE_MISSING")
        else:
            payload = json.loads(ap.read_text(encoding="utf-8"))
            bound = payload.get("BOUND_TO") or payload.get("bound_to") or {}
            if str(bound.get("RUN_ID") or "") != contract.run_id:
                blockers.append("RUN_ID_MISMATCH")
            if str(bound.get("FIXPOINT_SHA") or "") != contract.fixpoint_sha:
                blockers.append("FIXPOINT_SHA_MISMATCH")
            if str(bound.get("SETTINGS_DIGEST") or "") != contract.settings_digest:
                blockers.append("SETTINGS_DIGEST_MISMATCH")
            if int(bound.get("RUN_DURATION_SECONDS") or -1) != contract.run_duration_seconds:
                blockers.append("RUN_DURATION_MISMATCH")
            for key, expected in (
                ("MAX_OBSERVATION_COUNT", contract.max_observation_count),
                ("MAX_CYCLE_COUNT", contract.max_cycle_count),
                ("MAX_SIMULATED_EXECUTION_COUNT", contract.max_simulated_execution_count),
            ):
                if int(bound.get(key) or -1) != expected:
                    blockers.append(f"{key}_MISMATCH")
            if str(bound.get("EXECUTION_SINK") or "") != contract.execution_sink:
                blockers.append("EXECUTION_SINK_MISMATCH")
            obs = obs or str(
                payload.get("OBSERVATION_TOKEN") or payload.get("observation_token") or ""
            )
            act = act or str(
                payload.get("ACTIVATION_TOKEN") or payload.get("activation_token") or ""
            )

    present = bool(obs or act or authorization_path)
    if present:
        if obs != SHADOW_OBSERVATION_OPERATOR_GO:
            blockers.append("OBSERVATION_TOKEN_MISMATCH")
        if act != SHADOW_ACTIVATION_OPERATOR_GO:
            blockers.append("ACTIVATION_TOKEN_MISMATCH")
    else:
        blockers.append("OWNER_GO_NOT_PRESENT")

    return OwnerGoValidationResultV1(
        ok=not blockers,
        owner_go_present=present and not blockers,
        owner_go_consumed=False,
        blockers=tuple(blockers),
    )
