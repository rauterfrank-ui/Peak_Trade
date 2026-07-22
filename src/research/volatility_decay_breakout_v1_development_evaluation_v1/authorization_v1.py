"""Authorization decision for VDB v1 development evaluation.

Fail-closed: token match alone is insufficient; measurement-contract, program, and
entry-point-binding flags must also authorize development evaluation. Development
evaluation is authorized on HEAD; panel execution remains a separate operator GO.

Corrective measurement reevaluation is a distinct authorization path that preserves
development_run_count / runner_start_count at 1 and uses a separate corrective
counter / evidence directory.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from src.research.volatility_decay_breakout_v1_development_evaluation_v1.constants_v1 import (
    CORRECTIVE_AUTHORIZE_TOKEN,
    CORRECTIVE_MEASUREMENT_REEVALUATION_LIMIT,
    ENTRY_POINT_BINDING_REL_PATH,
    HYPOTHESIS_ID,
    MEASUREMENT_CONTRACT_REL_PATH,
    MEASUREMENT_REPAIR_MERGE_COMMIT,
    PORTFOLIO_AGGREGATION_ID,
    PROGRAM_REL_PATH,
)
from src.research.volatility_decay_breakout_v1_development_evaluation_v1.guards_v1 import (
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


@dataclass(frozen=True)
class CorrectiveAuthorizationDecisionV1:
    authorized: bool
    authorize_token_valid: bool
    contract_corrective_authorized: bool
    program_corrective_authorized: bool
    binding_corrective_authorized: bool
    development_counters_preserved: bool
    measurement_repair_commit_bound: bool
    portfolio_aggregation_bound: bool
    reason_codes: tuple[str, ...]

    def require_authorized(self) -> None:
        if not self.authorized:
            raise GuardError(
                "CORRECTIVE_REEVALUATION_UNAUTHORIZED:"
                + ",".join(self.reason_codes or ("UNKNOWN",))
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


def resolve_corrective_measurement_reevaluation_authorization_v1(
    repo_root: Path,
    *,
    authorize_token: str,
) -> CorrectiveAuthorizationDecisionV1:
    """Authorize exactly one corrective measurement reevaluation (fail-closed)."""
    reasons: list[str] = []
    token_ok = authorize_token == CORRECTIVE_AUTHORIZE_TOKEN
    if not token_ok:
        reasons.append("CORRECTIVE_AUTHORIZE_TOKEN_MISMATCH")

    contract = _load(repo_root, MEASUREMENT_CONTRACT_REL_PATH)
    program = _load(repo_root, PROGRAM_REL_PATH)
    binding = _load(repo_root, ENTRY_POINT_BINDING_REL_PATH)

    contract_auth = contract.get("corrective_measurement_reevaluation_authorized") is True
    program_auth = program.get("corrective_measurement_reevaluation_authorized") is True
    binding_auth = binding.get("corrective_measurement_reevaluation_authorized") is True
    if not contract_auth:
        reasons.append("CONTRACT_CORRECTIVE_REEVALUATION_AUTHORIZED_FALSE")
    if not program_auth:
        reasons.append("PROGRAM_CORRECTIVE_REEVALUATION_AUTHORIZED_FALSE")
    if not binding_auth:
        reasons.append("BINDING_CORRECTIVE_REEVALUATION_AUTHORIZED_FALSE")

    dev_run = int(contract.get("development_run_count", -1))
    runner_start = int(contract.get("runner_start_count", -1))
    program_dev = int(program.get("development_run_count", -1))
    program_runner = int(program.get("runner_start_count", -1))
    binding_dev = int(binding.get("development_run_count", -1))
    binding_runner = int(binding.get("runner_start_count", -1))
    development_ok = (
        dev_run == 1
        and runner_start == 1
        and program_dev == 1
        and program_runner == 1
        and binding_dev == 1
        and binding_runner == 1
    )
    if not development_ok:
        reasons.append("DEVELOPMENT_COUNTERS_NOT_PRESERVED_AT_ONE")

    corrective_count = int(contract.get("corrective_measurement_reevaluation_count", -1))
    corrective_limit = int(
        contract.get(
            "corrective_measurement_reevaluation_limit",
            CORRECTIVE_MEASUREMENT_REEVALUATION_LIMIT,
        )
    )
    if corrective_limit != CORRECTIVE_MEASUREMENT_REEVALUATION_LIMIT:
        reasons.append("CORRECTIVE_REEVALUATION_LIMIT_DRIFT")
    if corrective_count >= CORRECTIVE_MEASUREMENT_REEVALUATION_LIMIT:
        reasons.append("CORRECTIVE_REEVALUATION_LIMIT_EXHAUSTED")
    if corrective_count < 0:
        reasons.append("CORRECTIVE_REEVALUATION_COUNT_MISSING")

    repair_ok = (
        str(contract.get("measurement_repair_merge_commit") or "")
        == MEASUREMENT_REPAIR_MERGE_COMMIT
        and str(program.get("measurement_repair_merge_commit") or "")
        == MEASUREMENT_REPAIR_MERGE_COMMIT
        and str(binding.get("measurement_repair_merge_commit") or "")
        == MEASUREMENT_REPAIR_MERGE_COMMIT
    )
    if not repair_ok:
        reasons.append("MEASUREMENT_REPAIR_MERGE_COMMIT_MISMATCH")

    portfolio = contract.get("portfolio") or {}
    portfolio_ok = (
        str(portfolio.get("portfolio_aggregation_id") or "") == PORTFOLIO_AGGREGATION_ID
        and str(binding.get("portfolio_aggregation_id") or "") == PORTFOLIO_AGGREGATION_ID
        and str(program.get("portfolio_aggregation_id") or PORTFOLIO_AGGREGATION_ID)
        == PORTFOLIO_AGGREGATION_ID
    )
    if not portfolio_ok:
        reasons.append("PORTFOLIO_AGGREGATION_ID_MISMATCH")

    if contract.get("holdout_authorized") is True:
        reasons.append("HOLDOUT_AUTHORIZED_TRUE")
    if (contract.get("runtime_policy") or {}).get("live_authorized") is True:
        reasons.append("LIVE_AUTHORIZED_TRUE")

    authorized = (
        token_ok
        and contract_auth
        and program_auth
        and binding_auth
        and development_ok
        and repair_ok
        and portfolio_ok
        and corrective_count < CORRECTIVE_MEASUREMENT_REEVALUATION_LIMIT
        and corrective_limit == CORRECTIVE_MEASUREMENT_REEVALUATION_LIMIT
        and not any(code.startswith("HOLDOUT_") or code.startswith("LIVE_") for code in reasons)
    )
    if authorized:
        reasons = ()
    return CorrectiveAuthorizationDecisionV1(
        authorized=authorized,
        authorize_token_valid=token_ok,
        contract_corrective_authorized=contract_auth,
        program_corrective_authorized=program_auth,
        binding_corrective_authorized=binding_auth,
        development_counters_preserved=development_ok,
        measurement_repair_commit_bound=repair_ok,
        portfolio_aggregation_bound=portfolio_ok,
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
