"""Shadow observation authorization — mechanism vs consumed authorization (fail-closed)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.ops.canonical_shadow_runtime_enablement_v1.constants_v1 import (
    SHADOW_OBSERVATION_OPERATOR_GO,
)
from src.ops.integrated_paper_shadow_observation_session_v1.constants_v1 import (
    CONFIG_RELPATH,
    CONTRACT_DOC_RELPATH,
)

_MECHANISM_SOURCE_RELPATHS: tuple[str, ...] = (
    "src/ops/paper_shadow_observation_operator_go_session_preregistration_v1/operator_go_contract_v1.py",
    "src/ops/integrated_paper_shadow_observation_session_v1/readiness_producer_v1.py",
    CONFIG_RELPATH,
    CONTRACT_DOC_RELPATH,
)


@dataclass(frozen=True)
class ObservationAuthorizationEvaluationV1:
    observation_authorization_mechanism_ready: bool
    observation_authorized: bool
    mechanism_blockers: tuple[str, ...]
    authorization_blockers: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "OBSERVATION_AUTHORIZATION_MECHANISM_READY": self.observation_authorization_mechanism_ready,
            "OBSERVATION_AUTHORIZED": self.observation_authorized,
            "mechanism_blockers": list(self.mechanism_blockers),
            "authorization_blockers": list(self.authorization_blockers),
        }


def _repo_root(repo_root: Path | None) -> Path:
    return (repo_root or Path(__file__).resolve().parents[3]).resolve()


def evaluate_observation_authorization_mechanism_v1(
    *,
    repo_root: Path | None = None,
) -> tuple[bool, tuple[str, ...]]:
    """True when bounded observation GO can be adjudicated without code changes."""
    root = _repo_root(repo_root)
    blockers: list[str] = []
    for rel in _MECHANISM_SOURCE_RELPATHS:
        if not (root / rel).is_file():
            blockers.append(f"MECHANISM_SURFACE_MISSING:{rel}")
    return (not blockers, tuple(blockers))


def evaluate_observation_authorization_v1(
    *,
    operator_observation_go_token: str | None = None,
    repo_root: Path | None = None,
) -> ObservationAuthorizationEvaluationV1:
    """Classify mechanism readiness vs active observation authorization (never from static config)."""
    mechanism_ready, mechanism_blockers = evaluate_observation_authorization_mechanism_v1(
        repo_root=repo_root
    )
    token = str(operator_observation_go_token or "").strip()
    if not mechanism_ready:
        return ObservationAuthorizationEvaluationV1(
            observation_authorization_mechanism_ready=False,
            observation_authorized=False,
            mechanism_blockers=mechanism_blockers,
            authorization_blockers=("MECHANISM_NOT_READY",),
        )
    if token == SHADOW_OBSERVATION_OPERATOR_GO:
        return ObservationAuthorizationEvaluationV1(
            observation_authorization_mechanism_ready=True,
            observation_authorized=True,
            mechanism_blockers=(),
            authorization_blockers=(),
        )
    auth_blockers: tuple[str, ...]
    if token:
        auth_blockers = ("OBSERVATION_GO_TOKEN_MISMATCH",)
    else:
        auth_blockers = ("PAPER_SHADOW_OBSERVATION_NOT_AUTHORIZED",)
    return ObservationAuthorizationEvaluationV1(
        observation_authorization_mechanism_ready=True,
        observation_authorized=False,
        mechanism_blockers=(),
        authorization_blockers=auth_blockers,
    )


def resolve_observation_authorization_present_v1(
    *,
    observation_authorization_present: bool = False,
    operator_observation_go_token: str | None = None,
    repo_root: Path | None = None,
) -> bool:
    """Resolve explicit bool or scoped operator token into authorization-present flag."""
    if operator_observation_go_token is not None:
        return evaluate_observation_authorization_v1(
            operator_observation_go_token=operator_observation_go_token,
            repo_root=repo_root,
        ).observation_authorized
    return bool(observation_authorization_present)
