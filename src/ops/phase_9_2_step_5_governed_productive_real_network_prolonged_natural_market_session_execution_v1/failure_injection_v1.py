"""Offline failure-injection matrix for Step-5 governed execution (no network)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from src.ops.phase_9_2_step_5_governed_productive_real_network_prolonged_natural_market_session_execution_v1.constants_v1 import (
    CAPABILITY_ID,
    PLANNED_SESSION_DURATION_SECONDS,
    SESSION_SCOPE,
    TARGET_SESSION_ID,
)
from src.ops.phase_9_2_step_5_governed_productive_real_network_prolonged_natural_market_session_execution_v1.contract_bindings_v1 import (
    load_execution_contract_bundle_v1,
)
from src.ops.phase_9_2_step_5_governed_productive_real_network_prolonged_natural_market_session_execution_v1.digest_v1 import (
    sha256_canonical_v1,
)
from src.ops.phase_9_2_step_5_governed_productive_real_network_prolonged_natural_market_session_execution_v1.governed_session_execution_v1 import (
    execute_governed_step5_session_v1,
    request_real_network_offline_fail_closed_v1,
)
from src.ops.phase_9_2_step_5_governed_productive_real_network_prolonged_natural_market_session_execution_v1.hidden_pty_handoff_v1 import (
    fingerprint_only_v1,
)


def _token() -> str:
    return "PTCONFIRMv1_STEP5EXEC" + ("Z" * 20)


def run_step5_execution_failure_injection_v1(
    *,
    repository_sha: str,
    config_digest: str,
    persistence_root: Path,
    repo_root: Path | None = None,
    now_unix: float = 1_700_000_000.0,
) -> dict[str, Any]:
    persistence_root = Path(persistence_root)
    persistence_root.mkdir(parents=True, exist_ok=True)
    bundle = load_execution_contract_bundle_v1(repo_root=repo_root)
    token = _token()
    fp = fingerprint_only_v1(token)
    auth_id = "auth_step5_exec_fi_v1"
    auth_digest = sha256_canonical_v1({"authorization_id": auth_id, "sha": repository_sha})

    def _base(**overrides: Any) -> dict[str, Any]:
        kwargs: dict[str, Any] = {
            "expected_repository_sha": repository_sha,
            "expected_config_digest": config_digest,
            "expected_session_contract_digest": bundle["session_contract_digest"],
            "expected_binding_config_digest": bundle["binding_config_digest"],
            "authorization_id": auth_id,
            "authorization_digest": auth_digest,
            "confirm_token_binding_sha256": fp,
            "persistence_root": persistence_root / "base",
            "evidence_root": persistence_root / "evidence",
            "now_unix": now_unix,
            "authorization_expires_at": now_unix + 3600.0,
            "confirm_token_expires_at": now_unix + 3600.0,
            "confirm_token_plaintext": token,
            "authorization_capability_id": CAPABILITY_ID,
            "authorization_scope": SESSION_SCOPE,
            "authorization_session_id": TARGET_SESSION_ID,
            "repo_root": repo_root,
        }
        kwargs.update(overrides)
        result = execute_governed_step5_session_v1(**kwargs)
        return {
            "ok": result.ok,
            "blockers": list(result.blockers),
            "terminal_class": result.terminal_class,
            "network_session_started": result.network_session_started,
            "authorization_consumed": result.authorization_consumed,
            "confirm_token_consumed": result.confirm_token_consumed,
        }

    cases: dict[str, Any] = {}

    cases["network_without_authorization"] = _base(
        authorization_id="",
        authorization_digest="",
    )
    cases["wrong_sha"] = _base(
        expected_repository_sha=repository_sha,
        authorization_repository_sha="0" * 40,
    )
    # Force auth sha mismatch via authorization_repository path: use wrong expected sha
    # already covered; also wrong contract digest:
    cases["wrong_contract_digest"] = _base(
        expected_session_contract_digest="0" * 64,
    )
    cases["wrong_config_digest"] = _base(
        expected_binding_config_digest="0" * 64,
    )
    cases["wrong_scope"] = _base(authorization_scope="WRONG_SCOPE")
    cases["expired_authorization"] = _base(
        authorization_expires_at=now_unix - 10.0,
    )
    # reuse: pre-write ledger
    ledger = persistence_root / "reuse" / "step5_authorization_consumption_ledger_v1.jsonl"
    ledger.parent.mkdir(parents=True, exist_ok=True)
    ledger.write_text(
        json.dumps(
            {
                "authorization_id": auth_id,
                "authorization_digest": auth_digest,
                "session_id": TARGET_SESSION_ID,
                "consumed_at": now_unix - 1,
                "single_use": True,
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    cases["reused_authorization"] = _base(persistence_root=persistence_root / "reuse")
    cases["missing_confirm_token"] = _base(confirm_token_plaintext="")
    cases["wrong_confirm_token_digest"] = _base(confirm_token_binding_sha256="abad" * 16)
    cases["confirm_token_argv_rejected"] = _base(argv=["--confirm-token", "leak"])
    cases["confirm_token_env_rejected"] = _base(
        environ={"PEAK_TRADE_PSO_CONFIRM_TOKEN": "leak"},
    )
    req = request_real_network_offline_fail_closed_v1(
        expected_repository_sha=repository_sha,
        expected_config_digest=config_digest,
        repo_root=repo_root,
    )
    cases["request_real_network_fail_closed"] = {
        "ok": req.ok,
        "blockers": list(req.blockers),
        "terminal_class": req.terminal_class,
        "network_session_started": req.network_session_started,
    }

    expected_fail = {
        "network_without_authorization",
        "wrong_sha",
        "wrong_contract_digest",
        "wrong_config_digest",
        "wrong_scope",
        "expired_authorization",
        "reused_authorization",
        "missing_confirm_token",
        "wrong_confirm_token_digest",
        "confirm_token_argv_rejected",
        "confirm_token_env_rejected",
        "request_real_network_fail_closed",
    }
    ok = True
    for name in expected_fail:
        case = cases[name]
        if (
            case.get("ok")
            or case.get("network_session_started")
            or case.get("authorization_consumed")
        ):
            ok = False
            case["matrix_error"] = "EXPECTED_FAIL_CLOSED"
        # ensure no token plaintext leaked into blockers/notes serialization
        blob = json.dumps(case, sort_keys=True)
        if token in blob:
            ok = False
            case["matrix_error"] = "TOKEN_PLAINTEXT_LEAKED"

    return {
        "ok": ok,
        "cases": cases,
        "planned_session_duration_seconds": PLANNED_SESSION_DURATION_SECONDS,
        "network_session_started": False,
        "authorization_consumed": False,
        "confirm_token_consumed": False,
        "notes": ["FAILURE_INJECTION_OFFLINE_ONLY=true", "NO_FORCED_DECISION_OR_FILL=true"],
    }
