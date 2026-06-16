#!/usr/bin/env python3
"""Compose readiness ledger, preflight status, and mirror into one gate snapshot.

Taxonomy cross-reference (review-input-only): indexed in
``docs/ops/specs/RUNTIME_LANE_TAXONOMY_AUTHORITY_LEVELS_CONTRACT_V0.md`` §10.

Non-authorizing offline convenience CLI. Review-input-only; does not start runtime or
grant approval, gate clearance, Live/Testnet/broker/exchange permission, or trading
authorization. Does not override scheduler boundary guards, preflight BLOCKED, or
operator-explicit approval.

Optional ``--include-registry`` attaches a summary-only Generic Evidence Run Registry
v1 subsection. That subsection is non-authorizing and must not be interpreted as gate
clearance.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA = "peak_trade.readiness_gate_snapshot.v0"

VERDICT_PASS_BLOCKED_SAFE = "READINESS_GATE_SNAPSHOT_PASS_BLOCKED_SAFE"
VERDICT_REVIEW_REQUIRED = "READINESS_GATE_SNAPSHOT_REVIEW_REQUIRED"
VERDICT_FAIL_CLOSED = "READINESS_GATE_SNAPSHOT_FAIL_CLOSED"

LEDGER_PASS = "READINESS_EVIDENCE_LEDGER_PASS_BLOCKED_SAFE"
MIRROR_PASS = "READINESS_LEDGER_PREFLIGHT_MIRROR_PASS_BLOCKED_SAFE"

REGISTRY_PASS = "GENERIC_EVIDENCE_RUN_REGISTRY_PASS_BLOCKED_SAFE"
REGISTRY_REVIEW = "GENERIC_EVIDENCE_RUN_REGISTRY_REVIEW_REQUIRED"
REGISTRY_FAIL = "GENERIC_EVIDENCE_RUN_REGISTRY_FAIL_CLOSED"


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _ensure_repo_imports() -> None:
    root = str(_repo_root())
    if root not in sys.path:
        sys.path.insert(0, root)


def _summarize_ledger(full: dict[str, Any]) -> dict[str, Any]:
    evidence = full.get("evidence") if isinstance(full.get("evidence"), dict) else {}
    planning = full.get("planning") if isinstance(full.get("planning"), dict) else {}
    governance = full.get("governance") if isinstance(full.get("governance"), dict) else {}
    return {
        "verdict": full.get("verdict"),
        "triple_lane_primary_evidence": evidence.get("triple_lane_primary_evidence"),
        "planning_chain_present": planning.get("planning_chain_present"),
        "governance_blocked": governance.get("governance_blocked"),
        "live_allowed": governance.get("live_allowed"),
        "broker_exchange_allowed": governance.get("broker_exchange_allowed"),
        "secret_values_included": governance.get("secret_values_included"),
        "go_decision_granted": governance.get("go_decision_granted"),
        "hold_no_paper_run_cleared": governance.get("hold_no_paper_run_cleared"),
        "glb_014_cleared": governance.get("glb_014_cleared"),
        "glb_015_cleared": governance.get("glb_015_cleared"),
        "preflight_ready": governance.get("preflight_ready"),
        "blockers": full.get("blockers") if isinstance(full.get("blockers"), list) else [],
        "issues_count": len(full.get("issues") or []),
    }


def _summarize_preflight(full: dict[str, Any]) -> dict[str, Any]:
    hold = full.get("hold_context_v0") if isinstance(full.get("hold_context_v0"), dict) else {}
    dry = (
        full.get("dry_activation_readiness")
        if isinstance(full.get("dry_activation_readiness"), dict)
        else {}
    )
    return {
        "status": full.get("status"),
        "dry_activation_readiness_ready": dry.get("ready"),
        "hold_current_state": hold.get("current_state"),
        "go_live_next_step": hold.get("go_live_next_step"),
        "live_authorized": full.get("live_authorized"),
        "testnet_authorized": full.get("testnet_authorized"),
        "activation_authorized": full.get("activation_authorized"),
        "blockers": full.get("blockers") if isinstance(full.get("blockers"), list) else [],
    }


def _summarize_mirror(full: dict[str, Any]) -> dict[str, Any]:
    mirror = full.get("mirror") if isinstance(full.get("mirror"), dict) else {}
    return {
        "verdict": full.get("verdict"),
        "mirror_check_pass": mirror.get("mirror_check_pass"),
        "ledger_pass_blocked_safe": mirror.get("ledger_pass_blocked_safe"),
        "preflight_blocked": mirror.get("preflight_blocked"),
        "authorization_flags_false": mirror.get("authorization_flags_false"),
        "governance_blocked_consistent": mirror.get("governance_blocked_consistent"),
        "issues_count": len(full.get("issues") or []),
    }


def _derive_governance(
    ledger_full: dict[str, Any],
    preflight_full: dict[str, Any],
) -> dict[str, Any]:
    ledger_gov = (
        ledger_full.get("governance") if isinstance(ledger_full.get("governance"), dict) else {}
    )
    return {
        "governance_blocked": ledger_gov.get("governance_blocked"),
        "live_allowed": ledger_gov.get("live_allowed"),
        "broker_exchange_allowed": ledger_gov.get("broker_exchange_allowed"),
        "secret_values_included": ledger_gov.get("secret_values_included"),
        "go_decision_granted": ledger_gov.get("go_decision_granted"),
        "hold_no_paper_run_cleared": ledger_gov.get("hold_no_paper_run_cleared"),
        "glb_014_cleared": ledger_gov.get("glb_014_cleared"),
        "glb_015_cleared": ledger_gov.get("glb_015_cleared"),
        "preflight_ready": ledger_gov.get("preflight_ready"),
        "preflight_status": preflight_full.get("status"),
    }


def _collect_issues(
    ledger_full: dict[str, Any],
    mirror_full: dict[str, Any],
    extra: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    for item in ledger_full.get("issues") or []:
        if isinstance(item, dict):
            issues.append({"source": "ledger", **item})
    for item in mirror_full.get("issues") or []:
        if isinstance(item, dict):
            issues.append({"source": "mirror", **item})
    issues.extend(extra)
    return issues


def _derive_blockers(ledger_full: dict[str, Any], mirror_full: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    ledger_blockers = ledger_full.get("blockers")
    if isinstance(ledger_blockers, list):
        blockers.extend(str(x) for x in ledger_blockers)
    mirror_blockers = mirror_full.get("blockers")
    if isinstance(mirror_blockers, list):
        blockers.extend(str(x) for x in mirror_blockers)
    return sorted(set(blockers))


def derive_gate_verdict(
    ledger_full: dict[str, Any],
    preflight_full: dict[str, Any],
    mirror_full: dict[str, Any],
    issues: list[dict[str, Any]],
) -> str:
    ledger_verdict = ledger_full.get("verdict")
    mirror_verdict = mirror_full.get("verdict")
    governance = (
        ledger_full.get("governance") if isinstance(ledger_full.get("governance"), dict) else {}
    )

    if ledger_verdict == "READINESS_EVIDENCE_LEDGER_FAIL_CLOSED":
        return VERDICT_FAIL_CLOSED
    if mirror_verdict == "READINESS_LEDGER_PREFLIGHT_MIRROR_FAIL_CLOSED":
        return VERDICT_FAIL_CLOSED
    if governance.get("live_allowed") is True:
        return VERDICT_FAIL_CLOSED
    if governance.get("broker_exchange_allowed") is True:
        return VERDICT_FAIL_CLOSED
    if governance.get("secret_values_included") is True:
        return VERDICT_FAIL_CLOSED
    if governance.get("go_decision_granted") is True:
        return VERDICT_FAIL_CLOSED
    if governance.get("hold_no_paper_run_cleared") is True:
        return VERDICT_FAIL_CLOSED
    if governance.get("glb_014_cleared") is True or governance.get("glb_015_cleared") is True:
        return VERDICT_FAIL_CLOSED
    if preflight_full.get("status") in {"READY", "APPROVED", "GO", "LIVE", "AUTHORIZED", "CLEARED"}:
        return VERDICT_FAIL_CLOSED
    if (
        preflight_full.get("live_authorized") is True
        or preflight_full.get("testnet_authorized") is True
    ):
        return VERDICT_FAIL_CLOSED

    if ledger_verdict == "READINESS_EVIDENCE_LEDGER_REVIEW_REQUIRED":
        return VERDICT_REVIEW_REQUIRED
    if mirror_verdict == "READINESS_LEDGER_PREFLIGHT_MIRROR_REVIEW_REQUIRED":
        return VERDICT_REVIEW_REQUIRED
    if issues:
        return VERDICT_REVIEW_REQUIRED

    if (
        ledger_verdict == LEDGER_PASS
        and mirror_verdict == MIRROR_PASS
        and preflight_full.get("status") == "BLOCKED"
        and governance.get("governance_blocked") is True
        and governance.get("live_allowed") is False
        and governance.get("broker_exchange_allowed") is False
        and governance.get("secret_values_included") is False
    ):
        return VERDICT_PASS_BLOCKED_SAFE
    return VERDICT_REVIEW_REQUIRED


def _summarize_registry(full: dict[str, Any]) -> dict[str, Any]:
    summaries = full.get("summaries") if isinstance(full.get("summaries"), dict) else {}
    blockers = full.get("blockers") if isinstance(full.get("blockers"), list) else []
    return {
        "included": True,
        "non_authorizing": True,
        "schema": full.get("schema"),
        "verdict": full.get("verdict"),
        "total_runs": summaries.get("total_runs"),
        "verified_runs": summaries.get("verified_runs"),
        "runs_by_lane": summaries.get("runs_by_lane"),
        "scheduler_boundary_gap_acknowledged": summaries.get("scheduler_boundary_gap_acknowledged"),
        "live_authority_present": summaries.get("live_authority_present"),
        "broker_exchange_authority_present": summaries.get("broker_exchange_authority_present"),
        "issues_count": len(full.get("issues") or []),
        "blockers": blockers,
    }


def _registry_build_failed_section() -> dict[str, Any]:
    return {
        "included": False,
        "non_authorizing": True,
    }


def _registry_unsafe_for_gate(full: dict[str, Any]) -> bool:
    summaries = full.get("summaries") if isinstance(full.get("summaries"), dict) else {}
    authority = full.get("authority") if isinstance(full.get("authority"), dict) else {}
    if summaries.get("live_authority_present") is True:
        return True
    if summaries.get("broker_exchange_authority_present") is True:
        return True
    if authority.get("live_allowed") is True:
        return True
    if authority.get("broker_exchange_allowed") is True:
        return True
    if authority.get("secret_values_included") is True:
        return True
    return False


def _apply_registry_verdict_escalation(
    gate_verdict: str,
    registry_full: dict[str, Any] | None,
    *,
    build_failed: bool,
) -> str:
    if build_failed:
        if gate_verdict == VERDICT_FAIL_CLOSED:
            return gate_verdict
        return VERDICT_REVIEW_REQUIRED

    if registry_full is None:
        return gate_verdict

    if _registry_unsafe_for_gate(registry_full):
        return VERDICT_FAIL_CLOSED

    reg_verdict = registry_full.get("verdict")
    if reg_verdict == REGISTRY_FAIL:
        return VERDICT_FAIL_CLOSED
    if reg_verdict == REGISTRY_REVIEW and gate_verdict == VERDICT_PASS_BLOCKED_SAFE:
        return VERDICT_REVIEW_REQUIRED

    return gate_verdict


def build_readiness_gate_snapshot(
    archive_root: Path,
    *,
    repo_root: Path | None = None,
    fixed_generated_at_utc: str | None = None,
    include_registry: bool = False,
) -> dict[str, Any]:
    _ensure_repo_imports()
    from scripts.ops.build_readiness_evidence_ledger_v0 import (
        DEFAULT_PAPER_RUN_ID,
        DEFAULT_SHADOW_RUN_ID,
        DEFAULT_TESTNET_RUN_ID,
        BuildContext,
        build_ledger,
    )
    from scripts.ops.report_paper_shadow_247_preflight_status import (
        build_paper_shadow_247_preflight_status,
    )
    from scripts.ops.report_readiness_ledger_preflight_mirror_v0 import (
        build_mirror_from_payloads,
    )

    root = (repo_root or _repo_root()).resolve()
    archive = archive_root.expanduser().resolve()

    ledger_ctx = BuildContext(
        archive_root=archive,
        paper_run_id=DEFAULT_PAPER_RUN_ID,
        shadow_run_id=DEFAULT_SHADOW_RUN_ID,
        testnet_run_id=DEFAULT_TESTNET_RUN_ID,
    )
    ledger_full = build_ledger(ledger_ctx)
    preflight_full = build_paper_shadow_247_preflight_status(repo_root=root)
    mirror_full = build_mirror_from_payloads(
        ledger_full,
        preflight_full,
        fixed_generated_at_utc=fixed_generated_at_utc,
    )

    extra_issues: list[dict[str, Any]] = []
    issues = _collect_issues(ledger_full, mirror_full, extra_issues)
    governance = _derive_governance(ledger_full, preflight_full)
    verdict = derive_gate_verdict(ledger_full, preflight_full, mirror_full, issues)

    registry_section: dict[str, Any] | None = None
    if include_registry:
        try:
            from scripts.ops.build_generic_evidence_run_registry_v1 import (
                BuildContext as RegistryBuildContext,
                build_registry,
            )

            registry_ctx = RegistryBuildContext(
                archive_root=archive,
                repo_root=root,
                fixed_generated_at_utc=fixed_generated_at_utc,
            )
            registry_full = build_registry(registry_ctx)
            registry_section = _summarize_registry(registry_full)
            if _registry_unsafe_for_gate(registry_full):
                issues.append(
                    {
                        "source": "registry",
                        "code": "REGISTRY_SECTION_UNSAFE_AUTHORITY_SIGNAL",
                        "message": "registry summary reported unsafe authority signal",
                    }
                )
            elif registry_full.get("verdict") == REGISTRY_REVIEW:
                issues.append(
                    {
                        "source": "registry",
                        "code": "REGISTRY_SECTION_REVIEW_REQUIRED",
                        "message": "registry verdict requires review",
                    }
                )
            elif registry_full.get("verdict") == REGISTRY_FAIL:
                issues.append(
                    {
                        "source": "registry",
                        "code": "REGISTRY_SECTION_FAIL_CLOSED",
                        "message": "registry verdict is fail closed",
                    }
                )
            verdict = _apply_registry_verdict_escalation(
                verdict,
                registry_full,
                build_failed=False,
            )
        except Exception as exc:
            registry_section = _registry_build_failed_section()
            issues.append(
                {
                    "source": "registry",
                    "code": "REGISTRY_SECTION_BUILD_FAILED",
                    "message": str(exc),
                }
            )
            verdict = _apply_registry_verdict_escalation(
                verdict,
                None,
                build_failed=True,
            )

    generated_at = fixed_generated_at_utc or os.environ.get("PEAK_TRADE_FIXED_GENERATED_AT_UTC")
    if not generated_at:
        generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    payload: dict[str, Any] = {
        "schema": SCHEMA,
        "generated_at_utc": generated_at,
        "archive_root": str(archive),
        "ledger": _summarize_ledger(ledger_full),
        "preflight": _summarize_preflight(preflight_full),
        "mirror": _summarize_mirror(mirror_full),
        "governance": governance,
        "blockers": _derive_blockers(ledger_full, mirror_full),
        "verdict": verdict,
        "issues": issues,
    }
    if include_registry and registry_section is not None:
        payload["registry"] = registry_section
    return payload


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive-root", type=Path, required=True)
    parser.add_argument("--repo-root", type=Path)
    parser.add_argument("--fixed-generated-at-utc")
    parser.add_argument("--include-registry", action="store_true")
    parser.add_argument("--json", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    payload = build_readiness_gate_snapshot(
        args.archive_root,
        repo_root=args.repo_root,
        fixed_generated_at_utc=args.fixed_generated_at_utc,
        include_registry=args.include_registry,
    )
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=False))
    else:
        print(f"verdict={payload['verdict']}")
        print(f"issues={len(payload['issues'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
