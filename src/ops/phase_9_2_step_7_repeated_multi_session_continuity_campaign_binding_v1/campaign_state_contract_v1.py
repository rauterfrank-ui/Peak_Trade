"""Campaign-state contract for repeated governed Step-7 sessions.

Each session remains individually authorized. This binding never enables a
permanent network flag and forbids authorization/confirm-token reuse.
Cross-session state continuity must be checked explicitly by the campaign
verifier (not assumed).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from src.ops.phase_9_2_step_7_repeated_multi_session_continuity_campaign_binding_v1.constants_v1 import (
    AUTHORIZATION_REUSE_FORBIDDEN,
    CAMPAIGN_ID,
    CAMPAIGN_STATE_CONTRACT_OWNER,
    CAMPAIGN_STATE_SCHEMA_VERSION,
    CONFIRM_TOKEN_REUSE_FORBIDDEN,
    MULTI_SESSION_REQUIREMENT_EXPRESSION,
    MULTI_SESSION_REQUIREMENT_OPERAND,
    MULTI_SESSION_REQUIREMENT_OPERATOR,
    NETWORK_SESSION_ALLOWED,
    NO_PERMANENT_UNSCOPED_ENABLE_FLAG,
    PHASE_9_2_SESSION_LADDER_COMPLETE,
    PHASE_9_2_STEP_7_STATUS,
    SESSION_LADDER_STEP,
    SESSION_SCOPE,
    TARGET_CAMPAIGN_CAPABILITY_ID,
    TARGET_SESSION_ID_PREFIX,
    repo_root_v1,
)
from src.ops.phase_9_2_step_7_repeated_multi_session_continuity_campaign_binding_v1.digest_v1 import (
    read_json_v1,
    sha256_canonical_v1,
)


class CampaignStateContractError(ValueError):
    """Invalid Step-7 campaign-state contract."""


def build_campaign_state_contract_v1(
    *,
    expected_repository_sha: str = "",
    expected_config_digest: str = "",
) -> dict[str, Any]:
    return {
        "schema_version": CAMPAIGN_STATE_SCHEMA_VERSION,
        "owner": CAMPAIGN_STATE_CONTRACT_OWNER,
        "capability_id": TARGET_CAMPAIGN_CAPABILITY_ID,
        "campaign_id": CAMPAIGN_ID,
        "session_ladder_step": SESSION_LADDER_STEP,
        "session_scope": SESSION_SCOPE,
        "session_id_prefix": TARGET_SESSION_ID_PREFIX,
        "multi_session_requirement": {
            "operator": MULTI_SESSION_REQUIREMENT_OPERATOR,
            "operand": MULTI_SESSION_REQUIREMENT_OPERAND,
            "expression": MULTI_SESSION_REQUIREMENT_EXPRESSION,
            "note": (
                "No invented governance minimum count. Campaign verifier "
                "requires strictly more than one governed session."
            ),
        },
        "per_session_authorization_required": True,
        "permanent_network_enable_forbidden": True,
        "no_permanent_unscoped_enable_flag": NO_PERMANENT_UNSCOPED_ENABLE_FLAG,
        "authorization_reuse_forbidden": AUTHORIZATION_REUSE_FORBIDDEN,
        "confirm_token_reuse_forbidden": CONFIRM_TOKEN_REUSE_FORBIDDEN,
        "cross_session_state_continuity_must_be_explicitly_checked": True,
        "network_session_allowed_by_binding": NETWORK_SESSION_ALLOWED,
        "phase_9_2_step_7_status": PHASE_9_2_STEP_7_STATUS,
        "phase_9_2_session_ladder_complete": PHASE_9_2_SESSION_LADDER_COMPLETE,
        "expected_repository_sha": str(expected_repository_sha or ""),
        "expected_config_digest": str(expected_config_digest or ""),
        "allowed_binding_transitions": [],
        "contract_digest": "",
    }


def validate_campaign_state_contract_v1(contract: Mapping[str, Any]) -> list[str]:
    blockers: list[str] = []
    if str(contract.get("schema_version") or "") != CAMPAIGN_STATE_SCHEMA_VERSION:
        blockers.append("CAMPAIGN_STATE_SCHEMA_MISMATCH")
    if str(contract.get("session_ladder_step") or "") != SESSION_LADDER_STEP:
        blockers.append("SESSION_LADDER_STEP_MISMATCH")
    if not bool(contract.get("per_session_authorization_required")):
        blockers.append("PER_SESSION_AUTHORIZATION_REQUIRED")
    if not bool(contract.get("permanent_network_enable_forbidden")):
        blockers.append("PERMANENT_NETWORK_ENABLE_MUST_BE_FORBIDDEN")
    if not bool(contract.get("authorization_reuse_forbidden")):
        blockers.append("AUTHORIZATION_REUSE_MUST_BE_FORBIDDEN")
    if not bool(contract.get("confirm_token_reuse_forbidden")):
        blockers.append("CONFIRM_TOKEN_REUSE_MUST_BE_FORBIDDEN")
    if not bool(contract.get("cross_session_state_continuity_must_be_explicitly_checked")):
        blockers.append("CROSS_SESSION_CONTINUITY_CHECK_REQUIRED")
    if bool(contract.get("network_session_allowed_by_binding")):
        blockers.append("NETWORK_SESSION_MUST_REMAIN_FORBIDDEN_IN_BINDING")
    if str(contract.get("phase_9_2_step_7_status") or "") != "OPEN":
        blockers.append("STEP7_STATUS_MUST_REMAIN_OPEN")
    if bool(contract.get("phase_9_2_session_ladder_complete")):
        blockers.append("SESSION_LADDER_MUST_REMAIN_INCOMPLETE")
    req = dict(contract.get("multi_session_requirement") or {})
    if str(req.get("operator") or "") != MULTI_SESSION_REQUIREMENT_OPERATOR:
        blockers.append("MULTI_SESSION_REQUIREMENT_OPERATOR_DRIFT")
    if int(req.get("operand") or -1) != MULTI_SESSION_REQUIREMENT_OPERAND:
        blockers.append("MULTI_SESSION_REQUIREMENT_OPERAND_DRIFT")
    if str(req.get("expression") or "") != MULTI_SESSION_REQUIREMENT_EXPRESSION:
        blockers.append("MULTI_SESSION_REQUIREMENT_EXPRESSION_DRIFT")
    return blockers


def seal_campaign_state_contract_v1(contract: Mapping[str, Any]) -> dict[str, Any]:
    out = dict(contract)
    out.pop("contract_digest", None)
    out["contract_digest"] = sha256_canonical_v1(out)
    return out


def load_campaign_contract_file_v1(*, repo_root: Path | None = None) -> dict[str, Any]:
    root = Path(repo_root) if repo_root is not None else repo_root_v1()
    path = root / (
        "config/ops/phase_9_2_public_md_multi_session_continuity_campaign_contract_v1.json"
    )
    if not path.is_file():
        raise CampaignStateContractError(f"CAMPAIGN_CONTRACT_MISSING:{path}")
    return read_json_v1(path)


def load_and_validate_campaign_state_contract_v1(
    *,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    contract = load_campaign_contract_file_v1(repo_root=repo_root)
    blockers = validate_campaign_state_contract_v1(contract)
    if blockers:
        raise CampaignStateContractError(";".join(blockers))
    return contract
