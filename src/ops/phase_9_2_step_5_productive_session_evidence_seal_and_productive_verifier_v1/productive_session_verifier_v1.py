"""Productive-session verifier (AUTHORIZED_PRODUCTIVE_SESSION domain).

Distinct from the offline implementation verifier, which asserts
no-network / no-consume for implementation evidence.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Mapping

from src.ops.phase_9_2_step_5_governed_productive_real_network_prolonged_natural_market_session_execution_v1.contract_bindings_v1 import (
    load_execution_contract_bundle_v1,
)
from src.ops.phase_9_2_step_5_governed_productive_real_network_prolonged_natural_market_session_execution_v1.evidence_v1 import (
    claims_match_telemetry_v1,
    verify_session_manifest_v1,
)
from src.ops.phase_9_2_step_5_productive_session_evidence_seal_and_productive_verifier_v1.constants_v1 import (
    AUTH_LEDGER_RELATIVE,
    CONFIRM_TOKEN_PUBLIC_RELATIVE,
    EVENTS_RELATIVE,
    EXECUTOR_SUMMARY_RELATIVE,
    GRANT_PUBLIC_RELATIVE,
    LOCKS_DIR_RELATIVE,
    MIN_REQUEST_INTERVAL_SECONDS_REQUIRED,
    OFFLINE_IMPLEMENTATION_VERIFIER_OWNER,
    OFFLINE_VERIFIER_DOMAIN,
    OFFLINE_VERIFIER_EXPECTED_FALSE_FOR_PRODUCTIVE_SESSION,
    OPERATOR_PUBLIC_RESULT_NAME,
    PRODUCTIVE_SESSION_INVALIDATED_BY_OFFLINE_VERIFIER,
    PRODUCTIVE_VERIFIER_DOMAIN,
    PRODUCTIVE_VERIFIER_SCHEMA,
    PROGRESS_NAME,
    SESSION_CONTRACT_SECONDS_EXPECTED,
    TERMINAL_MANIFEST_RELATIVE,
    repo_root_v1,
)
from src.ops.phase_9_2_step_5_productive_session_evidence_seal_and_productive_verifier_v1.digest_v1 import (
    read_json_v1,
    sha256_file_bytes_v1,
)
from src.ops.single_future_stateful_no_order_runtime_activation_v1.config_v1 import (
    load_activation_config_v1,
)


def _add(blockers: list[str], ok: bool, code: str) -> None:
    if not ok:
        blockers.append(code)


def _load_optional_json(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    raw = json.loads(path.read_text(encoding="utf-8"))
    return raw if isinstance(raw, dict) else None


def _count_jsonl_lines(path: Path) -> int:
    if not path.is_file():
        return 0
    count = 0
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            count += 1
    return count


def _scan_plaintext_token_leak(session_root: Path) -> list[str]:
    """Detect plaintext confirm-token / secret artifacts without flagging public digests.

    Parameter names / boolean claim fields such as confirm_token_plaintext_exposed
    or confirm_token_plaintext=None are not treated as leaks.
    """
    hits: list[str] = []
    # Actual assigned plaintext value (quoted or long mint prefix), not kwarg=None.
    assigned_plaintext = re.compile(
        r"(?i)(?:confirm[_-]?token[_-]?plaintext|CONFIRM_TOKEN_PLAINTEXT)\s*[:=]\s*"
        r"(?:\"[^\"]{12,}\"|'[^\']{12,}'|PTCONFIRMv1_\S{8,})"
    )
    for path in sorted(session_root.rglob("*")):
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        name = path.name.lower()
        rel = str(path.relative_to(session_root))
        if name.endswith((".secret", ".token", ".tmp")) or name in {
            "confirm_token.txt",
            "confirm_token_plaintext.txt",
            "token_plaintext.txt",
        }:
            hits.append(f"TEMPORARY_SECRET_OR_TOKEN_ARTIFACT:{rel}")
        if "PTCONFIRMv1_" in text:
            hits.append(f"CONFIRM_TOKEN_PLAINTEXT_IN_EVIDENCE:{rel}")
        if assigned_plaintext.search(text):
            hits.append(f"CONFIRM_TOKEN_REGEX_HIT:{rel}")
    return sorted(set(hits))


def _locks_released(session_root: Path) -> bool:
    locks = session_root / LOCKS_DIR_RELATIVE
    if not locks.exists():
        return True
    if not locks.is_dir():
        return False
    return not any(locks.iterdir())


def verify_productive_session_evidence_v1(
    session_root: Path,
    *,
    expected_repository_sha: str,
    expected_config_digest: str | None = None,
    expected_session_contract_digest: str | None = None,
    expected_binding_config_digest: str | None = None,
    expected_public_md_request_count: int | None = None,
    expected_heartbeat_count: int | None = None,
    repo_root: Path | None = None,
    residual_process_found: bool = False,
) -> dict[str, Any]:
    """Verify an authorized productive Step-5 session evidence tree.

    Does not mutate session_root. Does not start network/runtime processes.
    """
    root = Path(repo_root) if repo_root is not None else repo_root_v1()
    session_root = Path(session_root)
    blockers: list[str] = []
    notes: list[str] = [
        f"OFFLINE_VERIFIER_DOMAIN={OFFLINE_VERIFIER_DOMAIN}",
        f"PRODUCTIVE_VERIFIER_DOMAIN={PRODUCTIVE_VERIFIER_DOMAIN}",
        f"OFFLINE_VERIFIER_EXPECTED_FALSE_FOR_PRODUCTIVE_SESSION="
        f"{OFFLINE_VERIFIER_EXPECTED_FALSE_FOR_PRODUCTIVE_SESSION}",
        f"PRODUCTIVE_SESSION_INVALIDATED_BY_OFFLINE_VERIFIER="
        f"{PRODUCTIVE_SESSION_INVALIDATED_BY_OFFLINE_VERIFIER}",
        f"OFFLINE_IMPLEMENTATION_VERIFIER_OWNER={OFFLINE_IMPLEMENTATION_VERIFIER_OWNER}",
    ]

    if not session_root.is_dir():
        return {
            "ok": False,
            "verified": False,
            "schema": PRODUCTIVE_VERIFIER_SCHEMA,
            "productive_verifier_domain": PRODUCTIVE_VERIFIER_DOMAIN,
            "blockers": ["SESSION_ROOT_MISSING"],
            "notes": notes,
        }

    public = _load_optional_json(session_root / OPERATOR_PUBLIC_RESULT_NAME)
    manifest = _load_optional_json(session_root / TERMINAL_MANIFEST_RELATIVE)
    progress = _load_optional_json(session_root / PROGRESS_NAME)
    executor = _load_optional_json(session_root / EXECUTOR_SUMMARY_RELATIVE)
    _add(blockers, public is not None, "OPERATOR_PUBLIC_RESULT_MISSING")
    _add(blockers, manifest is not None, "SESSION_TERMINAL_MANIFEST_MISSING")
    _add(blockers, progress is not None, "PROGRESS_MISSING")
    _add(blockers, (session_root / EVENTS_RELATIVE).is_file(), "SESSION_EVENTS_MISSING")
    _add(
        blockers,
        (session_root / CONFIRM_TOKEN_PUBLIC_RELATIVE).is_file(),
        "CONFIRM_TOKEN_PUBLIC_MISSING",
    )
    _add(blockers, (session_root / GRANT_PUBLIC_RELATIVE).is_file(), "GRANT_PUBLIC_MISSING")

    public = public or {}
    manifest = manifest or {}
    progress = progress or {}
    telemetry = dict(public.get("telemetry") or manifest.get("telemetry") or {})
    claims = dict(public.get("claims") or manifest.get("claims") or {})

    # Duration
    wallclock = float(public.get("wallclock_seconds") or 0.0)
    mono = float(
        telemetry.get("session_monotonic_wallclock_seconds")
        or claims.get("SESSION_MONOTONIC_WALLCLOCK_SECONDS")
        or 0.0
    )
    planned = int(
        public.get("planned_session_duration_seconds")
        or public.get("minimum_successful_wallclock_seconds")
        or SESSION_CONTRACT_SECONDS_EXPECTED
    )
    _add(
        blockers,
        planned == SESSION_CONTRACT_SECONDS_EXPECTED,
        "SESSION_CONTRACT_SECONDS_EXPECTED_MISMATCH",
    )
    duration_ok = wallclock >= float(SESSION_CONTRACT_SECONDS_EXPECTED) and mono >= float(
        SESSION_CONTRACT_SECONDS_EXPECTED
    )
    _add(blockers, duration_ok, "SESSION_WALLCLOCK_SECONDS_BELOW_MINIMUM")

    request_count = int(telemetry.get("request_count") or claims.get("REQUEST_COUNT") or 0)
    heartbeat_count = int(telemetry.get("heartbeat_count") or 0)
    min_interval = float(telemetry.get("min_observed_interval_seconds") or 0.0)
    zero_burst = bool(claims.get("ZERO_INTERVAL_BURST"))
    rate_limit_events = int(telemetry.get("http_429_count") or 0)
    retry_count = int(telemetry.get("retry_count") or 0)
    terminal_class = str(public.get("terminal_class") or manifest.get("terminal_class") or "")
    retry_budget_exceeded = terminal_class == "RATE_LIMIT_EXHAUSTED" or (
        terminal_class != "PASS" and retry_count > 0 and not public.get("ok")
    )

    _add(blockers, request_count > 0, "PUBLIC_MD_REQUEST_COUNT_NOT_POSITIVE")
    _add(blockers, heartbeat_count > 0, "HEARTBEAT_COUNT_NOT_POSITIVE")
    if expected_public_md_request_count is not None:
        _add(
            blockers,
            request_count == int(expected_public_md_request_count),
            "PUBLIC_MD_REQUEST_COUNT_MISMATCH",
        )
    if expected_heartbeat_count is not None:
        _add(
            blockers,
            heartbeat_count == int(expected_heartbeat_count),
            "HEARTBEAT_COUNT_MISMATCH",
        )
    _add(
        blockers,
        min_interval >= float(MIN_REQUEST_INTERVAL_SECONDS_REQUIRED),
        "MIN_REQUEST_INTERVAL_SECONDS_BELOW_MINIMUM",
    )
    _add(blockers, zero_burst is False, "ZERO_INTERVAL_BURST_DETECTED")
    _add(blockers, rate_limit_events == 0, "RATE_LIMIT_EVENTS_NONZERO")
    _add(blockers, retry_budget_exceeded is False, "RETRY_BUDGET_EXCEEDED")

    private = bool(
        telemetry.get("private_endpoint_access_occurred")
        or claims.get("PRIVATE_ENDPOINT_ACCESS_OCCURRED")
        or public.get("private_endpoint_reachable")
    )
    auth_header = bool(
        telemetry.get("auth_header_transmitted") or claims.get("AUTH_HEADER_TRANSMITTED")
    )
    credential = bool(
        telemetry.get("credential_access_occurred") or claims.get("CREDENTIAL_ACCESS_OCCURRED")
    )
    order_side = bool(
        telemetry.get("order_side_effect_occurred") or claims.get("ORDER_SIDE_EFFECT_OCCURRED")
    )
    public_endpoints_only = (not private) and bool(telemetry.get("network_session_started"))
    _add(blockers, public_endpoints_only, "PUBLIC_ENDPOINTS_ONLY_FALSE")
    _add(blockers, private is False, "PRIVATE_ENDPOINT_REACHABLE")
    _add(blockers, auth_header is False, "AUTH_HEADER_PRESENT")
    _add(blockers, credential is False, "CREDENTIAL_ACCESS_DETECTED")
    _add(blockers, order_side is False, "ORDER_SIDE_EFFECT_OCCURRED")

    auth_consumed = bool(
        public.get("authorization_consumed") or claims.get("AUTHORIZATION_CONSUMED")
    )
    ledger_count = _count_jsonl_lines(session_root / AUTH_LEDGER_RELATIVE)
    _add(blockers, auth_consumed is True, "AUTHORIZATION_NOT_CONSUMED")
    _add(blockers, ledger_count == 1, "AUTHORIZATION_CONSUMED_NOT_ONCE")

    token_exposed = bool(
        public.get("confirm_token_plaintext_exposed")
        or claims.get("CONFIRM_TOKEN_PLAINTEXT_EXPOSED")
    )
    token_persisted = bool(
        public.get("confirm_token_persisted") or claims.get("CONFIRM_TOKEN_PERSISTED")
    )
    token_in_argv = bool(public.get("confirm_token_process_argument"))
    leak_hits = _scan_plaintext_token_leak(session_root)
    token_in_logs = any(
        (":logs/" in h or h.endswith(".log") or "/logs/" in h)
        and ("CONFIRM_TOKEN" in h or "PTCONFIRM" in h)
        for h in leak_hits
    )
    token_in_evidence = any(
        h.startswith("CONFIRM_TOKEN_PLAINTEXT_IN_EVIDENCE:")
        or h.startswith("CONFIRM_TOKEN_REGEX_HIT:")
        for h in leak_hits
    )
    temp_secret = any(h.startswith("TEMPORARY_SECRET") for h in leak_hits)
    _add(blockers, token_exposed is False, "CONFIRM_TOKEN_PLAINTEXT_EXPOSED")
    _add(blockers, token_persisted is False, "CONFIRM_TOKEN_PERSISTED")
    _add(blockers, token_in_logs is False, "CONFIRM_TOKEN_IN_LOGS")
    _add(blockers, token_in_argv is False, "CONFIRM_TOKEN_IN_PROCESS_ARGUMENTS")
    _add(blockers, token_in_evidence is False, "CONFIRM_TOKEN_IN_EVIDENCE")
    _add(blockers, temp_secret is False, "TEMPORARY_SECRET_OR_TOKEN_ARTIFACT_FOUND")

    process_exited = (
        str(progress.get("phase") or "") == "completed"
        and bool(progress.get("ok"))
        and terminal_class == "PASS"
        and bool(public.get("ok"))
    )
    lock_released = _locks_released(session_root)
    _add(blockers, process_exited, "SESSION_PROCESS_NOT_EXITED")
    _add(blockers, residual_process_found is False, "RESIDUAL_PROCESS_FOUND")
    _add(blockers, lock_released, "SESSION_LOCK_NOT_RELEASED")

    # Digests
    cfg_expected = expected_config_digest
    contract_expected = expected_session_contract_digest
    binding_expected = expected_binding_config_digest
    if cfg_expected is None or contract_expected is None or binding_expected is None:
        bundle = load_execution_contract_bundle_v1(repo_root=root)
        cfg_live = str(
            load_activation_config_v1(
                config_path=root
                / "config/runtime/single_future_stateful_no_order_runtime_activation_v1.json"
            ).config_digest
        )
        if cfg_expected is None:
            cfg_expected = cfg_live
        if contract_expected is None:
            contract_expected = str(bundle["session_contract_digest"])
        if binding_expected is None:
            binding_expected = str(bundle["binding_config_digest"])

    repo_sha = str(public.get("actual_repository_sha") or manifest.get("repository_sha") or "")
    cfg_got = str(public.get("config_digest") or manifest.get("config_digest") or "")
    contract_got = str(
        public.get("session_contract_digest") or manifest.get("session_contract_digest") or ""
    )
    binding_got = str(
        public.get("binding_config_digest") or manifest.get("binding_config_digest") or ""
    )
    _add(
        blockers,
        repo_sha == str(expected_repository_sha),
        "REPOSITORY_SHA_MISMATCH",
    )
    _add(blockers, cfg_got == str(cfg_expected), "CONFIG_DIGEST_MISMATCH")
    _add(
        blockers,
        contract_got == str(contract_expected),
        "SESSION_CONTRACT_DIGEST_MISMATCH",
    )
    _add(blockers, binding_got == str(binding_expected), "BINDING_CONFIG_DIGEST_MISMATCH")

    required_manifest_keys = (
        "capability_id",
        "claims",
        "telemetry",
        "terminal_class",
        "repository_sha",
        "config_digest",
        "session_contract_digest",
        "binding_config_digest",
    )
    manifest_complete = all(k in manifest for k in required_manifest_keys)
    _add(blockers, manifest_complete, "SESSION_MANIFEST_INCOMPLETE")

    internal_ok = (
        bool(public.get("ok"))
        and terminal_class == "PASS"
        and int(claims.get("REQUEST_COUNT") or -1) == request_count
        and str(progress.get("terminal_class") or "") == terminal_class
    )
    _add(blockers, internal_ok, "SESSION_INTERNAL_CONSISTENCY_FAIL")

    claims_match = claims_match_telemetry_v1(claims=claims, telemetry=telemetry)
    _add(blockers, bool(claims_match.get("ok")), "CLAIMS_TELEMETRY_MISMATCH")
    if claims_match.get("blockers"):
        for b in claims_match["blockers"]:
            if b not in blockers:
                blockers.append(str(b))

    # Domain separation: offline verifier must remain False for productive claims
    offline = verify_session_manifest_v1(manifest)
    offline_false = offline.get("ok") is False
    _add(
        blockers,
        offline_false == OFFLINE_VERIFIER_EXPECTED_FALSE_FOR_PRODUCTIVE_SESSION,
        "OFFLINE_VERIFIER_DOMAIN_SEPARATION_DRIFT",
    )
    offline_blockers = list(offline.get("blockers") or [])
    for required in (
        "NETWORK_SESSION_MUST_REMAIN_FALSE_IN_IMPLEMENTATION_EVIDENCE",
        "AUTHORIZATION_MUST_NOT_BE_CONSUMED",
        "CONFIRM_TOKEN_MUST_NOT_BE_CONSUMED",
    ):
        _add(blockers, required in offline_blockers, f"OFFLINE_VERIFIER_MISSING_{required}")

    checks = {
        "SESSION_CONTRACT_SECONDS_EXPECTED": SESSION_CONTRACT_SECONDS_EXPECTED,
        "SESSION_WALLCLOCK_SECONDS_ACTUAL": wallclock,
        "SESSION_DURATION_REQUIREMENT_PASS": duration_ok,
        "PUBLIC_MD_REQUEST_COUNT": request_count,
        "HEARTBEAT_COUNT": heartbeat_count,
        "MIN_REQUEST_INTERVAL_SECONDS": min_interval,
        "ZERO_INTERVAL_BURST_DETECTED": zero_burst,
        "RATE_LIMIT_EVENTS": rate_limit_events,
        "RETRY_BUDGET_EXCEEDED": retry_budget_exceeded,
        "PUBLIC_ENDPOINTS_ONLY": public_endpoints_only,
        "PRIVATE_ENDPOINT_REACHABLE": private,
        "AUTH_HEADER_PRESENT": auth_header,
        "CREDENTIAL_ACCESS_DETECTED": credential,
        "ORDER_SIDE_EFFECT_OCCURRED": order_side,
        "AUTHORIZATION_CONSUMED_ONCE": auth_consumed and ledger_count == 1,
        "CONFIRM_TOKEN_PLAINTEXT_EXPOSED": token_exposed,
        "CONFIRM_TOKEN_PERSISTED": token_persisted,
        "CONFIRM_TOKEN_IN_LOGS": token_in_logs,
        "CONFIRM_TOKEN_IN_PROCESS_ARGUMENTS": token_in_argv,
        "CONFIRM_TOKEN_IN_EVIDENCE": token_in_evidence,
        "SESSION_PROCESS_EXITED": process_exited,
        "RESIDUAL_PROCESS_FOUND": residual_process_found,
        "SESSION_LOCK_RELEASED": lock_released,
        "TEMPORARY_SECRET_OR_TOKEN_ARTIFACT_FOUND": temp_secret,
        "REPOSITORY_SHA_MATCH": repo_sha == str(expected_repository_sha),
        "CONFIG_DIGEST_MATCH": cfg_got == str(cfg_expected),
        "SESSION_CONTRACT_DIGEST_MATCH": contract_got == str(contract_expected),
        "SESSION_MANIFEST_COMPLETE": manifest_complete,
        "SESSION_INTERNAL_CONSISTENCY_PASS": internal_ok,
        "CLAIMS_MATCH_TELEMETRY": bool(claims_match.get("ok")),
    }

    ok = not blockers
    return {
        "ok": ok,
        "verified": ok,
        "schema": PRODUCTIVE_VERIFIER_SCHEMA,
        "productive_verifier_domain": PRODUCTIVE_VERIFIER_DOMAIN,
        "offline_verifier_domain": OFFLINE_VERIFIER_DOMAIN,
        "offline_verifier_expected_false_for_productive_session": (
            OFFLINE_VERIFIER_EXPECTED_FALSE_FOR_PRODUCTIVE_SESSION
        ),
        "productive_session_invalidated_by_offline_verifier": (
            PRODUCTIVE_SESSION_INVALIDATED_BY_OFFLINE_VERIFIER
        ),
        "offline_verifier_result": offline,
        "blockers": blockers,
        "notes": notes,
        "checks": checks,
        "session_root": str(session_root),
        "repository_sha": repo_sha,
        "config_digest": cfg_got,
        "session_contract_digest": contract_got,
        "binding_config_digest": binding_got,
        "expected_repository_sha": str(expected_repository_sha),
        "expected_config_digest": str(cfg_expected),
        "expected_session_contract_digest": str(contract_expected),
        "expected_binding_config_digest": str(binding_expected),
        "VERIFIER_RESULT": "PASS" if ok else "FAIL",
        "raw_file_digests": {
            "operator_public_result_sha256": (
                sha256_file_bytes_v1(session_root / OPERATOR_PUBLIC_RESULT_NAME)
                if (session_root / OPERATOR_PUBLIC_RESULT_NAME).is_file()
                else ""
            ),
            "session_terminal_manifest_sha256": (
                sha256_file_bytes_v1(session_root / TERMINAL_MANIFEST_RELATIVE)
                if (session_root / TERMINAL_MANIFEST_RELATIVE).is_file()
                else ""
            ),
            "session_events_sha256": (
                sha256_file_bytes_v1(session_root / EVENTS_RELATIVE)
                if (session_root / EVENTS_RELATIVE).is_file()
                else ""
            ),
        },
        "executor_present": executor is not None,
    }


def assert_offline_verifier_semantics_unchanged_v1(
    *,
    implementation_manifest: Mapping[str, Any],
    productive_manifest: Mapping[str, Any],
) -> dict[str, Any]:
    """Regression: offline verifier PASS on implementation, FAIL on productive."""
    impl = verify_session_manifest_v1(implementation_manifest)
    prod = verify_session_manifest_v1(productive_manifest)
    blockers: list[str] = []
    if not impl.get("ok"):
        blockers.append("OFFLINE_VERIFIER_MUST_PASS_IMPLEMENTATION_EVIDENCE")
    if prod.get("ok"):
        blockers.append("OFFLINE_VERIFIER_MUST_FAIL_PRODUCTIVE_SESSION_EVIDENCE")
    for required in (
        "NETWORK_SESSION_MUST_REMAIN_FALSE_IN_IMPLEMENTATION_EVIDENCE",
        "AUTHORIZATION_MUST_NOT_BE_CONSUMED",
        "CONFIRM_TOKEN_MUST_NOT_BE_CONSUMED",
    ):
        if required not in list(prod.get("blockers") or []):
            blockers.append(f"OFFLINE_VERIFIER_SEMANTICS_DRIFT_MISSING_{required}")
    return {
        "ok": not blockers,
        "blockers": blockers,
        "implementation": impl,
        "productive": prod,
        "offline_verifier_semantics_changed": bool(blockers),
    }
