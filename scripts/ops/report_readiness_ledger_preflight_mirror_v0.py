#!/usr/bin/env python3
"""Compare Readiness Evidence Ledger v0 JSON with Preflight status JSON.

Taxonomy cross-reference (review-input-only): indexed in
``docs/ops/specs/RUNTIME_LANE_TAXONOMY_AUTHORITY_LEVELS_CONTRACT_V0.md`` §10.

Non-authorizing mirror check only. Review-input-only; does not start runtime or grant
approval, gate clearance, Live/Testnet/broker/exchange permission, or trading
authorization. Does not override scheduler boundary guards, preflight BLOCKED, or
operator-explicit approval.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA = "peak_trade.readiness_ledger_preflight_mirror.v0"

LEDGER_VERDICT_PASS_BLOCKED_SAFE = "READINESS_EVIDENCE_LEDGER_PASS_BLOCKED_SAFE"

VERDICT_PASS_BLOCKED_SAFE = "READINESS_LEDGER_PREFLIGHT_MIRROR_PASS_BLOCKED_SAFE"
VERDICT_REVIEW_REQUIRED = "READINESS_LEDGER_PREFLIGHT_MIRROR_REVIEW_REQUIRED"
VERDICT_FAIL_CLOSED = "READINESS_LEDGER_PREFLIGHT_MIRROR_FAIL_CLOSED"

PREFLIGHT_BLOCKED_STATUSES = frozenset({"BLOCKED"})
PREFLIGHT_UNSAFE_STATUSES = frozenset(
    {
        "READY",
        "APPROVED",
        "GO",
        "LIVE",
        "AUTHORIZED",
        "CLEARED",
    }
)

PREFLIGHT_AUTH_FLAGS = (
    "activation_authorized",
    "shadow_runtime_authorized",
    "scheduler_execution_authorized",
    "testnet_authorized",
    "live_authorized",
    "broker_authorized",
    "exchange_authorized",
    "daemon_activation_authorized",
    "order_submission_authorized",
    "paper_runtime_authorized",
)


@dataclass
class Issue:
    code: str
    message: str
    path: str | None = None

    def as_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {"code": self.code, "message": self.message}
        if self.path is not None:
            out["path"] = self.path
        return out


@dataclass
class MirrorContext:
    ledger_path: Path | None
    preflight_path: Path | None
    fixed_generated_at_utc: str | None = None
    issues: list[Issue] = field(default_factory=list)

    def add_issue(self, code: str, message: str, path: str | None = None) -> None:
        self.issues.append(Issue(code=code, message=message, path=path))


def _load_json(path: Path | None, ctx: MirrorContext, *, label: str) -> dict[str, Any] | None:
    if path is None:
        code = "MISSING_LEDGER_JSON" if label == "ledger" else "MISSING_PREFLIGHT_JSON"
        ctx.add_issue(code, f"{label} path not provided")
        return None
    if not path.is_file():
        code = "MISSING_LEDGER_JSON" if label == "ledger" else "MISSING_PREFLIGHT_JSON"
        ctx.add_issue(code, f"{label} JSON file missing: {path}", str(path))
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        code = "INVALID_LEDGER_JSON" if label == "ledger" else "INVALID_PREFLIGHT_JSON"
        ctx.add_issue(code, f"{label} JSON invalid: {exc}", str(path))
        return None
    if not isinstance(payload, dict):
        code = "INVALID_LEDGER_JSON" if label == "ledger" else "INVALID_PREFLIGHT_JSON"
        ctx.add_issue(code, f"{label} JSON root must be object", str(path))
        return None
    return payload


def _bool(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    return None


def _extract_preflight_auth_flags(preflight: dict[str, Any]) -> dict[str, bool | None]:
    flags: dict[str, bool | None] = {key: None for key in PREFLIGHT_AUTH_FLAGS}

    def _merge(source: dict[str, Any]) -> None:
        for key in PREFLIGHT_AUTH_FLAGS:
            if key not in source:
                continue
            value = _bool(source.get(key))
            if value is True:
                flags[key] = True
            elif value is False and flags[key] is not True:
                flags[key] = False

    _merge(preflight)
    hold = preflight.get("hold_context_v0")
    if isinstance(hold, dict):
        progression = hold.get("progression_authorization")
        if isinstance(progression, dict):
            _merge(progression)
    return flags


def _check_ledger(ledger: dict[str, Any] | None, ctx: MirrorContext) -> dict[str, Any]:
    summary: dict[str, Any] = {
        "verdict": None,
        "triple_lane_primary_evidence": None,
        "planning_chain_present": None,
        "governance_blocked": None,
        "live_allowed": None,
        "broker_exchange_allowed": None,
        "secret_values_included": None,
        "preflight_ready": None,
        "hold_no_paper_run_cleared": None,
        "glb_014_cleared": None,
        "glb_015_cleared": None,
        "blockers": [],
    }
    if ledger is None:
        return summary

    summary["verdict"] = ledger.get("verdict")
    evidence = ledger.get("evidence") if isinstance(ledger.get("evidence"), dict) else {}
    planning = ledger.get("planning") if isinstance(ledger.get("planning"), dict) else {}
    governance = ledger.get("governance") if isinstance(ledger.get("governance"), dict) else {}
    blockers = ledger.get("blockers")
    summary["blockers"] = blockers if isinstance(blockers, list) else []

    summary["triple_lane_primary_evidence"] = _bool(evidence.get("triple_lane_primary_evidence"))
    summary["planning_chain_present"] = _bool(planning.get("planning_chain_present"))
    summary["governance_blocked"] = _bool(governance.get("governance_blocked"))
    summary["live_allowed"] = _bool(governance.get("live_allowed"))
    summary["broker_exchange_allowed"] = _bool(governance.get("broker_exchange_allowed"))
    summary["secret_values_included"] = _bool(governance.get("secret_values_included"))
    summary["preflight_ready"] = _bool(governance.get("preflight_ready"))
    summary["hold_no_paper_run_cleared"] = _bool(governance.get("hold_no_paper_run_cleared"))
    summary["glb_014_cleared"] = _bool(governance.get("glb_014_cleared"))
    summary["glb_015_cleared"] = _bool(governance.get("glb_015_cleared"))

    if summary["verdict"] != LEDGER_VERDICT_PASS_BLOCKED_SAFE:
        ctx.add_issue(
            "LEDGER_VERDICT_NOT_PASS_BLOCKED_SAFE",
            f"ledger verdict must be {LEDGER_VERDICT_PASS_BLOCKED_SAFE}, got {summary['verdict']!r}",
        )
    if summary["triple_lane_primary_evidence"] is not True:
        ctx.add_issue(
            "LEDGER_TRIPLE_EVIDENCE_FALSE", "ledger triple_lane_primary_evidence must be true"
        )
    if summary["planning_chain_present"] is not True:
        ctx.add_issue("LEDGER_PLANNING_CHAIN_FALSE", "ledger planning_chain_present must be true")
    if summary["governance_blocked"] is not True:
        ctx.add_issue("LEDGER_GOVERNANCE_NOT_BLOCKED", "ledger governance_blocked must be true")
    if summary["live_allowed"] is True:
        ctx.add_issue("LEDGER_LIVE_ALLOWED_TRUE", "ledger live_allowed must be false")
    if summary["broker_exchange_allowed"] is True:
        ctx.add_issue("LEDGER_BROKER_ALLOWED_TRUE", "ledger broker_exchange_allowed must be false")
    if summary["secret_values_included"] is True:
        ctx.add_issue(
            "LEDGER_SECRET_VALUES_INCLUDED_TRUE", "ledger secret_values_included must be false"
        )

    return summary


def _check_preflight(preflight: dict[str, Any] | None, ctx: MirrorContext) -> dict[str, Any]:
    summary: dict[str, Any] = {
        "status": None,
        "dry_activation_readiness_ready": None,
        "hold_current_state": None,
        "go_live_next_step": None,
        "authorization_flags": {},
    }
    if preflight is None:
        return summary

    status = preflight.get("status")
    summary["status"] = status if isinstance(status, str) else None

    dry = preflight.get("dry_activation_readiness")
    if isinstance(dry, dict) and "ready" in dry:
        summary["dry_activation_readiness_ready"] = _bool(dry.get("ready"))

    hold = preflight.get("hold_context_v0")
    if isinstance(hold, dict):
        current_state = hold.get("current_state")
        summary["hold_current_state"] = current_state if isinstance(current_state, str) else None
        go_live = hold.get("go_live_next_step")
        summary["go_live_next_step"] = go_live if isinstance(go_live, str) else None

    auth_flags = _extract_preflight_auth_flags(preflight)
    summary["authorization_flags"] = auth_flags

    if summary["status"] is None:
        ctx.add_issue("PREFLIGHT_STATUS_NOT_BLOCKED", "preflight status missing")
    elif summary["status"] in PREFLIGHT_UNSAFE_STATUSES:
        ctx.add_issue(
            "PREFLIGHT_STATUS_NOT_BLOCKED",
            f"preflight status must be BLOCKED, got {summary['status']!r}",
        )
    elif summary["status"] not in PREFLIGHT_BLOCKED_STATUSES:
        ctx.add_issue(
            "PREFLIGHT_STATUS_NOT_BLOCKED",
            f"preflight status unexpected: {summary['status']!r}",
        )

    if summary["dry_activation_readiness_ready"] is True:
        ctx.add_issue(
            "PREFLIGHT_READY_TRUE", "preflight dry_activation_readiness.ready must be false"
        )

    if (
        summary["hold_current_state"] is not None
        and summary["hold_current_state"] != "HOLD_NO_PAPER_RUN"
    ):
        ctx.add_issue(
            "HOLD_CONTEXT_NOT_HOLD_NO_PAPER_RUN",
            f"hold_context_v0.current_state must be HOLD_NO_PAPER_RUN, got {summary['hold_current_state']!r}",
        )

    go_live = summary.get("go_live_next_step")
    if isinstance(go_live, str) and go_live.lower() not in {"blocked", "hold", "none", "stop"}:
        ctx.add_issue(
            "PREFLIGHT_GO_LIVE_NEXT_STEP_NOT_BLOCKED",
            f"go_live_next_step must be blocked, got {go_live!r}",
        )

    for key, value in auth_flags.items():
        if value is True:
            ctx.add_issue(
                "PREFLIGHT_AUTHORIZATION_FLAG_TRUE",
                f"preflight authorization flag {key} must be false",
            )

    return summary


def _build_mirror_checks(
    ledger_summary: dict[str, Any], preflight_summary: dict[str, Any]
) -> dict[str, bool]:
    auth_flags = preflight_summary.get("authorization_flags") or {}
    authorization_flags_false = not any(value is True for value in auth_flags.values())

    preflight_blocked = preflight_summary.get("status") == "BLOCKED"
    ledger_pass = ledger_summary.get("verdict") == LEDGER_VERDICT_PASS_BLOCKED_SAFE

    return {
        "ledger_pass_blocked_safe": ledger_pass,
        "preflight_blocked": preflight_blocked,
        "authorization_flags_false": authorization_flags_false,
        "governance_blocked_consistent": ledger_summary.get("governance_blocked") is True
        and preflight_blocked,
        "live_not_allowed_consistent": ledger_summary.get("live_allowed") is False
        and auth_flags.get("live_authorized") is not True,
        "secret_safe_consistent": ledger_summary.get("secret_values_included") is False,
        "hold_glb_not_cleared_consistent": ledger_summary.get("hold_no_paper_run_cleared") is False
        and ledger_summary.get("glb_014_cleared") is False
        and ledger_summary.get("glb_015_cleared") is False,
        "mirror_check_pass": False,
    }


def derive_verdict(ctx: MirrorContext) -> str:
    codes = {issue.code for issue in ctx.issues}
    fail_codes = {
        "LEDGER_LIVE_ALLOWED_TRUE",
        "LEDGER_BROKER_ALLOWED_TRUE",
        "LEDGER_SECRET_VALUES_INCLUDED_TRUE",
        "LEDGER_GOVERNANCE_NOT_BLOCKED",
        "PREFLIGHT_STATUS_NOT_BLOCKED",
        "PREFLIGHT_READY_TRUE",
        "PREFLIGHT_AUTHORIZATION_FLAG_TRUE",
        "PREFLIGHT_GO_LIVE_NEXT_STEP_NOT_BLOCKED",
    }
    if codes & fail_codes:
        return VERDICT_FAIL_CLOSED
    if "LEDGER_VERDICT_NOT_PASS_BLOCKED_SAFE" in codes and not (
        codes & {"LEDGER_LIVE_ALLOWED_TRUE", "LEDGER_SECRET_VALUES_INCLUDED_TRUE"}
    ):
        return VERDICT_REVIEW_REQUIRED
    review_codes = {
        "MISSING_LEDGER_JSON",
        "MISSING_PREFLIGHT_JSON",
        "INVALID_LEDGER_JSON",
        "INVALID_PREFLIGHT_JSON",
        "LEDGER_VERDICT_NOT_PASS_BLOCKED_SAFE",
        "LEDGER_TRIPLE_EVIDENCE_FALSE",
        "LEDGER_PLANNING_CHAIN_FALSE",
        "HOLD_CONTEXT_NOT_HOLD_NO_PAPER_RUN",
    }
    if codes & review_codes:
        return VERDICT_REVIEW_REQUIRED
    return VERDICT_PASS_BLOCKED_SAFE


def derive_blockers(ledger_summary: dict[str, Any], preflight_summary: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    ledger_blockers = ledger_summary.get("blockers")
    if isinstance(ledger_blockers, list):
        blockers.extend(str(item) for item in ledger_blockers)
    if preflight_summary.get("status") == "BLOCKED":
        blockers.append("PREFLIGHT_BLOCKED")
    return sorted(set(blockers))


def build_mirror(ctx: MirrorContext) -> dict[str, Any]:
    ledger = _load_json(ctx.ledger_path, ctx, label="ledger")
    preflight = _load_json(ctx.preflight_path, ctx, label="preflight")
    return build_mirror_from_payloads(
        ledger,
        preflight,
        ctx=ctx,
        fixed_generated_at_utc=ctx.fixed_generated_at_utc,
    )


def build_mirror_from_payloads(
    ledger: dict[str, Any] | None,
    preflight: dict[str, Any] | None,
    *,
    ctx: MirrorContext | None = None,
    fixed_generated_at_utc: str | None = None,
) -> dict[str, Any]:
    mirror_ctx = ctx or MirrorContext(
        ledger_path=None,
        preflight_path=None,
        fixed_generated_at_utc=fixed_generated_at_utc,
    )
    if ledger is None:
        mirror_ctx.add_issue("MISSING_LEDGER_JSON", "ledger payload missing")
    if preflight is None:
        mirror_ctx.add_issue("MISSING_PREFLIGHT_JSON", "preflight payload missing")

    ledger_summary = _check_ledger(ledger, mirror_ctx)
    preflight_summary = _check_preflight(preflight, mirror_ctx)
    mirror = _build_mirror_checks(ledger_summary, preflight_summary)

    verdict = derive_verdict(mirror_ctx)
    mirror["mirror_check_pass"] = verdict == VERDICT_PASS_BLOCKED_SAFE

    generated_at = mirror_ctx.fixed_generated_at_utc or os.environ.get(
        "PEAK_TRADE_FIXED_GENERATED_AT_UTC"
    )
    if not generated_at:
        generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    return {
        "schema": SCHEMA,
        "generated_at_utc": generated_at,
        "ledger": ledger_summary,
        "preflight": preflight_summary,
        "mirror": mirror,
        "blockers": derive_blockers(ledger_summary, preflight_summary),
        "verdict": verdict,
        "issues": [issue.as_dict() for issue in mirror_ctx.issues],
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ledger-json", type=Path, required=True)
    parser.add_argument("--preflight-json", type=Path, required=True)
    parser.add_argument("--fixed-generated-at-utc")
    parser.add_argument("--json", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    ctx = MirrorContext(
        ledger_path=args.ledger_json.expanduser().resolve(),
        preflight_path=args.preflight_json.expanduser().resolve(),
        fixed_generated_at_utc=args.fixed_generated_at_utc,
    )
    payload = build_mirror(ctx)
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=False))
    else:
        print(f"verdict={payload['verdict']}")
        print(f"issues={len(payload['issues'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
