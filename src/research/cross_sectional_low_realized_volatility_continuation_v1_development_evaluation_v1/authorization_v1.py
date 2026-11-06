"""Authorization decision for CSLRVC v1 development evaluation.

Fail-closed: token match alone is insufficient; measurement-contract, program, and
entry-point-binding flags must also authorize development evaluation. Exactly one
bounded DEVELOPMENT evaluation may consume the run slot under operator GO.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from src.research.cross_sectional_low_realized_volatility_continuation_v1_development_evaluation_v1.constants_v1 import (
    ENTRY_POINT_BINDING_REL_PATH,
    HYPOTHESIS_ID,
    MEASUREMENT_CONTRACT_REL_PATH,
    PROGRAM_REL_PATH,
)
from src.research.cross_sectional_low_realized_volatility_continuation_v1_development_evaluation_v1.guards_v1 import (
    GuardError,
)


@dataclass(frozen=True)
class AuthorizationDecisionV1:
    authorized: bool
    authorize_token_valid: bool
    repo_development_evaluation_authorized: bool
    program_development_evaluation_authorized: bool
    entry_point_binding_authorized: bool
    reason_codes: tuple[str, ...]

    def require_authorized(self) -> None:
        if not self.authorized:
            raise GuardError(
                "EVALUATION_UNAUTHORIZED:" + ",".join(self.reason_codes or ("UNKNOWN",))
            )


def _load(repo_root: Path, rel: str) -> dict[str, Any]:
    path = repo_root / rel
    if not path.is_file():
        raise GuardError(f"AUTH_AUTHORITY_FILE_MISSING:{rel}")
    return json.loads(path.read_text(encoding="utf-8"))


def resolve_authorization_decision_v1(
    repo_root: Path,
    *,
    authorize_token: str,
) -> AuthorizationDecisionV1:
    """Machine-checkable authorization. Token and all three repo surfaces required."""
    reasons: list[str] = []
    token_ok = authorize_token == HYPOTHESIS_ID
    if not token_ok:
        reasons.append("AUTHORIZE_TOKEN_MISMATCH")

    contract = _load(repo_root, MEASUREMENT_CONTRACT_REL_PATH)
    program = _load(repo_root, PROGRAM_REL_PATH)
    binding = _load(repo_root, ENTRY_POINT_BINDING_REL_PATH)

    contract_auth = contract.get("development_evaluation_authorized") is True
    program_auth = program.get("development_evaluation_authorized") is True
    binding_auth = binding.get("development_evaluation_authorized") is True

    if not contract_auth:
        reasons.append("CONTRACT_DEVELOPMENT_EVALUATION_AUTHORIZED_FALSE")
    if not program_auth:
        reasons.append("PROGRAM_DEVELOPMENT_EVALUATION_AUTHORIZED_FALSE")
    if not binding_auth:
        reasons.append("ENTRY_POINT_BINDING_DEVELOPMENT_EVALUATION_AUTHORIZED_FALSE")

    if contract.get("holdout_authorized") is True:
        reasons.append("HOLDOUT_AUTHORIZED_TRUE")
    if (contract.get("runtime_policy") or {}).get("live_authorized") is True:
        reasons.append("LIVE_AUTHORIZED_TRUE")

    authorized = (
        token_ok
        and contract_auth
        and program_auth
        and binding_auth
        and not any(code.startswith("HOLDOUT_") or code.startswith("LIVE_") for code in reasons)
    )
    if authorized:
        reasons = ()
    return AuthorizationDecisionV1(
        authorized=authorized,
        authorize_token_valid=token_ok,
        repo_development_evaluation_authorized=contract_auth,
        program_development_evaluation_authorized=program_auth,
        entry_point_binding_authorized=binding_auth,
        reason_codes=tuple(reasons),
    )


def authorization_decision_from_mapping(payload: Mapping[str, Any]) -> AuthorizationDecisionV1:
    return AuthorizationDecisionV1(
        authorized=bool(payload.get("authorized")),
        authorize_token_valid=bool(payload.get("authorize_token_valid", True)),
        repo_development_evaluation_authorized=bool(
            payload.get("repo_development_evaluation_authorized", False)
        ),
        program_development_evaluation_authorized=bool(
            payload.get("program_development_evaluation_authorized", False)
        ),
        entry_point_binding_authorized=bool(payload.get("entry_point_binding_authorized", False)),
        reason_codes=tuple(payload.get("reason_codes") or ()),
    )
