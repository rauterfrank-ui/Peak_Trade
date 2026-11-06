"""Consume merged Step-7 productive campaign path as explicit dependency edge."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from src.ops.phase_9_2_step_7_governed_productive_real_tty_campaign_execution_v1.constants_v1 import (
    MODE_GOVERNED_MULTI_SESSION_CAMPAIGN,
    PATH_ENTRYPOINT_PATH,
    PATH_IMPLEMENTATION_CAPABILITY_ID,
)
from src.ops.phase_9_2_step_7_productive_campaign_execution_path_v1.constants_v1 import (
    PRODUCTIVE_NETWORK_SESSION_EXECUTION_AUTHORIZED as PATH_PRODUCTIVE_AUTHORIZED,
)
from src.ops.phase_9_2_step_7_productive_campaign_execution_path_v1.constants_v1 import (
    STEP7_BINDING_ONLY_PRESERVED as PATH_BINDING_PRESERVED,
)
from src.ops.phase_9_2_step_7_productive_campaign_execution_path_v1.constants_v1 import (
    STEP7_PRODUCTIVE_CAMPAIGN_EXECUTION_PATH_PRESENT as PATH_PRESENT,
)
from src.ops.phase_9_2_step_7_productive_campaign_execution_path_v1.productive_campaign_executor_v1 import (
    evaluate_productive_campaign_execution_gate_v1,
    prove_productive_campaign_execution_path_v1,
)


def consume_productive_campaign_path_dependency_v1(
    *,
    expected_repository_sha: str,
    expected_config_digest: str,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    """Require productive campaign path present; never reinterpret Binding/Path as start owner."""
    blockers: list[str] = []
    if not PATH_PRESENT:
        blockers.append("PRODUCTIVE_PATH_ABSENT")
    if PATH_PRODUCTIVE_AUTHORIZED:
        blockers.append("PATH_PERMANENT_PRODUCTIVE_AUTHORIZED_MUST_REMAIN_FALSE")
    if not PATH_BINDING_PRESERVED:
        blockers.append("BINDING_ONLY_PRESERVATION_BROKEN")

    proof = prove_productive_campaign_execution_path_v1(
        expected_repository_sha=expected_repository_sha,
        expected_config_digest=expected_config_digest,
        repo_root=repo_root,
    )
    if not proof.ok:
        blockers.append("PRODUCTIVE_PATH_PROOF_FAILED")
        blockers.extend(list(proof.blockers or []))
    if proof.network_session_started:
        blockers.append("PATH_PROOF_MUST_NOT_START_NETWORK")

    entry = Path(PATH_ENTRYPOINT_PATH)
    if repo_root is not None:
        entry = Path(repo_root) / PATH_ENTRYPOINT_PATH
    if repo_root is not None and not entry.is_file():
        blockers.append("PATH_ENTRYPOINT_MISSING")

    return {
        "ok": not blockers,
        "blockers": sorted(set(blockers)),
        "path_capability_id": PATH_IMPLEMENTATION_CAPABILITY_ID,
        "path_present": bool(PATH_PRESENT and proof.ok),
        "path_proof_ok": bool(proof.ok),
        "path_network_session_started": bool(proof.network_session_started),
        "path_structural_may_start_under_full_go": bool(
            (proof.claims or {}).get("STRUCTURAL_MAY_START_UNDER_FULL_GO")
        ),
        "consumes_productive_path": True,
        "notes": [
            "CAMPAIGN_OWNER_CONSUMES_PATH_DEPENDENCY_EDGE=true",
            "PATH_IMPLEMENTATION_REMAINS_NON_STARTING=true",
            "BINDING_ONLY_NOT_USED_AS_CAMPAIGN_OWNER=true",
        ],
    }


def prove_path_alone_cannot_start_campaign_v1(
    *,
    owner_go: bool = True,
    operator_authorization_explicit: bool = True,
    network_session_go: bool = True,
    stdin_isatty: bool = True,
    planned_session_count: int = 2,
) -> dict[str, Any]:
    """Path implementation forbids real side effects even under full ephemeral GO."""
    gate = evaluate_productive_campaign_execution_gate_v1(
        mode=MODE_GOVERNED_MULTI_SESSION_CAMPAIGN,
        owner_go=owner_go,
        operator_authorization_explicit=operator_authorization_explicit,
        network_session_go=network_session_go,
        public_md_only=True,
        authorization_valid=True,
        confirm_token_valid=True,
        planned_session_count=planned_session_count,
        stdin_isatty=stdin_isatty,
        allow_real_network_side_effects=True,
    )
    forbidden = "REAL_NETWORK_SIDE_EFFECTS_FORBIDDEN_IN_THIS_IMPLEMENTATION_CAPABILITY" in (
        gate.get("blockers") or []
    )
    may_start = bool(gate.get("campaign_may_start") or gate.get("network_session_may_start"))
    return {
        "ok": forbidden and not may_start,
        "path_may_start_with_request_real_network": may_start,
        "path_side_effects_forbidden": forbidden,
        "blockers": list(gate.get("blockers") or []),
        "notes": [
            "PRODUCTIVE_PATH_ALONE_CANNOT_START_CAMPAIGN=true",
            "REAL_TTY_CAMPAIGN_OWNER_REQUIRED_FOR_INVOKE=true",
        ],
    }
