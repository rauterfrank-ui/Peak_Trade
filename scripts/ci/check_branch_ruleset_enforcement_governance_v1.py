#!/usr/bin/env python3
"""BRANCH_RULESET_ENFORCEMENT_GOVERNANCE_V1 — fail-closed ruleset verifier.

Read-only. Consumes sanitized API evidence JSON and/or fetches via ``gh api``.
Never prints credentials, Authorization headers, or tokens.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

CAPABILITY_ID = "BRANCH_RULESET_ENFORCEMENT_GOVERNANCE_V1"
CONTRACT_SCHEMA = "branch_ruleset_enforcement_contract_v1"
EVIDENCE_SCHEMA = "branch_ruleset_enforcement_api_evidence_v1"

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONTRACT = REPO_ROOT / "config" / "ci" / "branch_ruleset_enforcement_contract_v1.json"
DEFAULT_REQUIRED = REPO_ROOT / "config" / "ci" / "required_status_checks.json"
DEFAULT_EVIDENCE = (
    REPO_ROOT / "docs" / "ops" / "specs" / "branch_ruleset_enforcement_api_evidence_after_v1.json"
)

FORBIDDEN_OUTPUT_NEEDLES = (
    "authorization:",
    "bearer ",
    "ghp_",
    "gho_",
    "ghu_",
    "ghs_",
    "github_pat_",
)


class VerificationError(RuntimeError):
    """Fail-closed verification failure."""


def _die_on_credential_leak(text: str) -> None:
    lowered = text.lower()
    for needle in FORBIDDEN_OUTPUT_NEEDLES:
        if needle in lowered:
            raise VerificationError(
                "REFUSING_OUTPUT: credential-like material detected in verifier I/O; fail-closed"
            )


def _load_json(path: Path) -> dict[str, Any]:
    raw = path.read_text(encoding="utf-8")
    _die_on_credential_leak(raw)
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise VerificationError(f"JSON root must be object: {path}")
    return data


def load_contract(path: Path = DEFAULT_CONTRACT) -> dict[str, Any]:
    data = _load_json(path)
    if data.get("schema_version") != CONTRACT_SCHEMA:
        raise VerificationError(
            f"unexpected contract schema_version: {data.get('schema_version')!r}"
        )
    if data.get("capability_id") != CAPABILITY_ID:
        raise VerificationError(f"unexpected capability_id: {data.get('capability_id')!r}")
    return data


def load_required_contexts(path: Path = DEFAULT_REQUIRED) -> list[str]:
    data = _load_json(path)
    required = data.get("required_contexts")
    ignored = set(data.get("ignored_contexts") or [])
    if not isinstance(required, list) or not required:
        raise VerificationError("required_contexts missing/empty; fail-closed")
    out = sorted(
        {str(x).strip() for x in required if str(x).strip()} - {str(i).strip() for i in ignored}
    )
    if not out:
        raise VerificationError("effective required contexts empty; fail-closed")
    return out


def sanitize_ruleset_payload(raw: dict[str, Any]) -> dict[str, Any]:
    """Normalize a ruleset API object into evidence-safe fields only."""
    return {
        "id": raw.get("id"),
        "name": raw.get("name"),
        "target": raw.get("target"),
        "enforcement": raw.get("enforcement"),
        "conditions": raw.get("conditions") or {},
        "rules": raw.get("rules") or [],
        "bypass_actors": raw.get("bypass_actors") or [],
        "current_user_can_bypass": raw.get("current_user_can_bypass"),
    }


def sanitize_repo_payload(raw: dict[str, Any]) -> dict[str, Any]:
    sec = raw.get("security_and_analysis") or {}
    return {
        "default_branch": raw.get("default_branch"),
        "allow_squash_merge": raw.get("allow_squash_merge"),
        "allow_merge_commit": raw.get("allow_merge_commit"),
        "allow_rebase_merge": raw.get("allow_rebase_merge"),
        "allow_auto_merge": raw.get("allow_auto_merge"),
        "delete_branch_on_merge": raw.get("delete_branch_on_merge"),
        "visibility": raw.get("visibility"),
        "secret_scanning": ((sec.get("secret_scanning") or {}).get("status")),
        "secret_scanning_push_protection": (
            (sec.get("secret_scanning_push_protection") or {}).get("status")
        ),
    }


def sanitize_classic_protection(raw: dict[str, Any]) -> dict[str, Any]:
    rsc = raw.get("required_status_checks") or {}
    rev = raw.get("required_pull_request_reviews") or {}
    return {
        "required_status_checks": {
            "strict": rsc.get("strict"),
            "contexts": sorted(str(c) for c in (rsc.get("contexts") or []) if c),
        },
        "required_pull_request_reviews": {
            "dismiss_stale_reviews": rev.get("dismiss_stale_reviews"),
            "require_code_owner_reviews": rev.get("require_code_owner_reviews"),
            "require_last_push_approval": rev.get("require_last_push_approval"),
            "required_approving_review_count": rev.get("required_approving_review_count"),
        },
        "enforce_admins": (raw.get("enforce_admins") or {}).get("enabled"),
        "required_linear_history": (raw.get("required_linear_history") or {}).get("enabled"),
        "allow_force_pushes": (raw.get("allow_force_pushes") or {}).get("enabled"),
        "allow_deletions": (raw.get("allow_deletions") or {}).get("enabled"),
        "required_conversation_resolution": (
            (raw.get("required_conversation_resolution") or {}).get("enabled")
        ),
    }


def _gh_api_json(path: str) -> dict[str, Any] | list[Any]:
    proc = subprocess.run(
        ["gh", "api", "-H", "Accept: application/vnd.github+json", path],
        capture_output=True,
        text=True,
        check=False,
    )
    combined = (proc.stdout or "") + "\n" + (proc.stderr or "")
    _die_on_credential_leak(combined)
    if proc.returncode != 0:
        # Never echo raw stderr (may contain URLs with tokens in misconfigured envs).
        raise VerificationError(f"gh api failed for {path!r} (rc={proc.returncode})")
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise VerificationError(f"malformed gh api JSON for {path!r}") from exc


def fetch_evidence(
    *,
    owner: str = "rauterfrank-ui",
    repo: str = "Peak_Trade",
    ruleset_id: int = 11192468,
    branch: str = "main",
) -> dict[str, Any]:
    base = f"repos/{owner}/{repo}"
    repo_raw = _gh_api_json(base)
    rulesets_raw = _gh_api_json(f"{base}/rulesets")
    ruleset_raw = _gh_api_json(f"{base}/rulesets/{ruleset_id}")
    try:
        bp_raw = _gh_api_json(f"{base}/branches/{branch}/protection")
        classic = sanitize_classic_protection(bp_raw if isinstance(bp_raw, dict) else {})
    except VerificationError:
        classic = {"_absent": True}

    if not isinstance(repo_raw, dict) or not isinstance(ruleset_raw, dict):
        raise VerificationError("unexpected API payload types; fail-closed")
    if not isinstance(rulesets_raw, list):
        raise VerificationError("rulesets list missing; fail-closed")

    return {
        "schema_version": EVIDENCE_SCHEMA,
        "phase": "live_fetch",
        "repository": sanitize_repo_payload(repo_raw),
        "rulesets_summary": [
            {
                "id": x.get("id"),
                "name": x.get("name"),
                "enforcement": x.get("enforcement"),
                "target": x.get("target"),
            }
            for x in rulesets_raw
            if isinstance(x, dict)
        ],
        "ruleset": sanitize_ruleset_payload(ruleset_raw),
        "classic_branch_protection_main": classic,
    }


def _rule_by_type(rules: list[Any], rule_type: str) -> dict[str, Any] | None:
    matches = [r for r in rules if isinstance(r, dict) and r.get("type") == rule_type]
    if len(matches) > 1:
        raise VerificationError(f"duplicate rule type {rule_type!r}; fail-closed")
    return matches[0] if matches else None


def _contexts_from_required_status_rule(rule: dict[str, Any]) -> list[str]:
    params = rule.get("parameters") or {}
    if not isinstance(params, dict):
        raise VerificationError("required_status_checks parameters malformed")
    checks = params.get("required_status_checks") or []
    if not isinstance(checks, list) or not checks:
        raise VerificationError("required_status_checks list empty/malformed")
    names: list[str] = []
    for item in checks:
        if not isinstance(item, dict):
            raise VerificationError("required status check entry malformed")
        ctx = item.get("context")
        if not ctx or not str(ctx).strip():
            raise VerificationError("required status check missing context")
        names.append(str(ctx).strip())
    # Detect duplicates / renamed ambiguity
    if len(names) != len(set(names)):
        raise VerificationError("duplicate required check contexts in ruleset; fail-closed")
    return sorted(names)


def _is_broad_bypass_actor(actor: Any) -> bool:
    if not isinstance(actor, dict):
        return True
    # Any bypass actor is treated as broad unless contract allowlists it explicitly.
    # Empty allowlist => any actor is broad/forbidden.
    return True


def evaluate_evidence(
    evidence: dict[str, Any],
    contract: dict[str, Any],
    required_contexts: list[str],
) -> dict[str, Any]:
    if evidence.get("schema_version") != EVIDENCE_SCHEMA:
        raise VerificationError(
            f"unexpected evidence schema_version: {evidence.get('schema_version')!r}"
        )

    repo = evidence.get("repository") or {}
    ruleset = evidence.get("ruleset") or {}
    if not isinstance(repo, dict) or not isinstance(ruleset, dict):
        raise VerificationError("evidence repository/ruleset missing; fail-closed")

    rs_cfg = contract["ruleset"]
    findings: list[str] = []

    default_branch = repo.get("default_branch")
    canonical = contract.get("canonical_protected_branch")
    target_branch_match = default_branch == canonical

    enforcement = ruleset.get("enforcement")
    if enforcement in (None, "", "disabled", "evaluate"):
        findings.append(f"enforcement_not_active:{enforcement!r}")
    elif enforcement != rs_cfg["expected_enforcement"]:
        findings.append(f"enforcement_mismatch:{enforcement!r}")

    if ruleset.get("name") != rs_cfg["expected_name"]:
        findings.append(f"ruleset_name_mismatch:{ruleset.get('name')!r}")
    if ruleset.get("id") != rs_cfg["expected_id"]:
        findings.append(f"ruleset_id_mismatch:{ruleset.get('id')!r}")
    if ruleset.get("target") != rs_cfg["expected_target"]:
        findings.append(f"ruleset_target_mismatch:{ruleset.get('target')!r}")

    conditions = ruleset.get("conditions") or {}
    ref_name = (conditions.get("ref_name") or {}) if isinstance(conditions, dict) else {}
    include = list(ref_name.get("include") or [])
    expected_include = list(contract.get("canonical_ref_include") or [])
    if sorted(include) != sorted(expected_include):
        findings.append(f"target_ref_include_mismatch:{include!r}")
        target_branch_match = False

    rules = ruleset.get("rules") or []
    if not isinstance(rules, list) or not rules:
        findings.append("rules_absent")
        rules = []

    present_types = sorted(
        {str(r.get("type")) for r in rules if isinstance(r, dict) and r.get("type")}
    )
    for needed in rs_cfg["required_rule_types"]:
        if needed not in present_types:
            findings.append(f"missing_rule_type:{needed}")

    deletion = _rule_by_type(rules, "deletion")
    nff = _rule_by_type(rules, "non_fast_forward")
    force_push_allowed = nff is None  # absence of non_fast_forward => force push possible
    branch_deletion_allowed = deletion is None
    if force_push_allowed:
        findings.append("force_push_allowed")
    if branch_deletion_allowed:
        findings.append("branch_deletion_allowed")

    pr_rule = _rule_by_type(rules, "pull_request")
    pr_params: dict[str, Any] = {}
    if pr_rule is None:
        findings.append("pull_request_rule_absent")
        pull_request_required = False
    else:
        pull_request_required = True
        pr_params = pr_rule.get("parameters") or {}
        if not isinstance(pr_params, dict):
            findings.append("pull_request_parameters_malformed")
            pr_params = {}
        expected_pr = rs_cfg["pull_request"]
        for key, expected in expected_pr.items():
            actual = pr_params.get(key)
            if isinstance(expected, list) and isinstance(actual, list):
                if sorted(expected) != sorted(actual):
                    findings.append(f"pull_request_param_mismatch:{key}:{actual!r}!={expected!r}")
            elif actual != expected:
                findings.append(f"pull_request_param_mismatch:{key}:{actual!r}!={expected!r}")

    rsc_rule = _rule_by_type(rules, "required_status_checks")
    check_set_match = False
    require_up_to_date = False
    live_checks: list[str] = []
    if rsc_rule is None:
        findings.append("required_status_checks_rule_absent")
    else:
        params = rsc_rule.get("parameters") or {}
        if not isinstance(params, dict):
            findings.append("required_status_checks_parameters_malformed")
        else:
            require_up_to_date = bool(params.get("strict_required_status_checks_policy"))
            if require_up_to_date != bool(
                rs_cfg["required_status_checks"]["strict_required_status_checks_policy"]
            ):
                findings.append("strict_required_status_checks_policy_mismatch")
            try:
                live_checks = _contexts_from_required_status_rule(rsc_rule)
            except VerificationError as exc:
                findings.append(str(exc))
                live_checks = []
            if live_checks == sorted(required_contexts):
                check_set_match = True
            else:
                missing = sorted(set(required_contexts) - set(live_checks))
                extra = sorted(set(live_checks) - set(required_contexts))
                if missing:
                    findings.append(f"missing_required_checks:{missing}")
                if extra:
                    findings.append(f"unexpected_required_checks:{extra}")

    bypass_actors = ruleset.get("bypass_actors") or []
    if not isinstance(bypass_actors, list):
        findings.append("bypass_actors_malformed")
        bypass_actors = ["_malformed"]
    allowed = list(rs_cfg.get("bypass_actors_allowed") or [])
    broad = []
    for actor in bypass_actors:
        # Serialize actor identity without tokens.
        if allowed and actor in allowed:
            continue
        if _is_broad_bypass_actor(actor):
            broad.append(actor)
    broad_count = len(broad)
    if broad_count:
        findings.append(f"broad_bypass_actors:{broad_count}")

    enforcement_status = (
        "ENFORCED"
        if enforcement == "active" and not findings and target_branch_match and check_set_match
        else ("NOT_ENFORCED" if enforcement in ("disabled", "evaluate", None, "") else "UNKNOWN")
    )
    # If active but findings remain, still NOT_ENFORCED for fail-closed posture.
    if enforcement == "active" and findings:
        enforcement_status = "NOT_ENFORCED"

    result = {
        "capability_id": CAPABILITY_ID,
        "RULESET_ENFORCEMENT_STATUS": enforcement_status,
        "TARGET_BRANCH_MATCH": bool(target_branch_match),
        "PULL_REQUEST_REQUIRED": bool(pull_request_required),
        "REQUIRED_APPROVAL_COUNT": pr_params.get("required_approving_review_count"),
        "STALE_APPROVAL_DISMISSAL": pr_params.get("dismiss_stale_reviews_on_push"),
        "LATEST_PUSH_APPROVAL_REQUIRED": pr_params.get("require_last_push_approval"),
        "CONVERSATION_RESOLUTION_REQUIRED": pr_params.get("required_review_thread_resolution"),
        "REQUIRED_CHECK_SET_MATCH": bool(check_set_match),
        "REQUIRED_CHECKS": live_checks,
        "REQUIRE_UP_TO_DATE": bool(require_up_to_date),
        "FORCE_PUSH_ALLOWED": bool(force_push_allowed),
        "BRANCH_DELETION_ALLOWED": bool(branch_deletion_allowed),
        "BROAD_BYPASS_ACTOR_COUNT": broad_count,
        "BYPASS_ACTORS": bypass_actors,
        "findings": findings,
        "ok": not findings
        and enforcement_status == "ENFORCED"
        and target_branch_match
        and check_set_match,
        "network_required": False,
        "secret_value_exposed": False,
    }
    return result


def render_human(result: dict[str, Any]) -> str:
    lines = [
        f"CAPABILITY_ID={result['capability_id']}",
        f"RULESET_ENFORCEMENT_STATUS={result['RULESET_ENFORCEMENT_STATUS']}",
        f"TARGET_BRANCH_MATCH={result['TARGET_BRANCH_MATCH']}",
        f"PULL_REQUEST_REQUIRED={result['PULL_REQUEST_REQUIRED']}",
        f"REQUIRED_APPROVAL_COUNT={result['REQUIRED_APPROVAL_COUNT']}",
        f"STALE_APPROVAL_DISMISSAL={result['STALE_APPROVAL_DISMISSAL']}",
        f"LATEST_PUSH_APPROVAL_REQUIRED={result['LATEST_PUSH_APPROVAL_REQUIRED']}",
        f"CONVERSATION_RESOLUTION_REQUIRED={result['CONVERSATION_RESOLUTION_REQUIRED']}",
        f"REQUIRED_CHECK_SET_MATCH={result['REQUIRED_CHECK_SET_MATCH']}",
        f"REQUIRE_UP_TO_DATE={result['REQUIRE_UP_TO_DATE']}",
        f"FORCE_PUSH_ALLOWED={result['FORCE_PUSH_ALLOWED']}",
        f"BRANCH_DELETION_ALLOWED={result['BRANCH_DELETION_ALLOWED']}",
        f"BROAD_BYPASS_ACTOR_COUNT={result['BROAD_BYPASS_ACTOR_COUNT']}",
        f"ok={result['ok']}",
    ]
    if result["findings"]:
        lines.append("findings=")
        for item in result["findings"]:
            lines.append(f"  - {item}")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--required-config", type=Path, default=DEFAULT_REQUIRED)
    parser.add_argument(
        "--evidence-json",
        type=Path,
        default=None,
        help="Sanitized evidence JSON (offline). Default: committed after-evidence.",
    )
    parser.add_argument(
        "--fetch",
        action="store_true",
        help="Fetch live sanitized evidence via gh api (operator/network).",
    )
    parser.add_argument("--json", action="store_true", help="Emit machine JSON on stdout.")
    args = parser.parse_args(argv)
    as_json = bool(args.json)

    try:
        contract = load_contract(args.contract)
        required = load_required_contexts(args.required_config)
        if args.fetch:
            evidence = fetch_evidence(
                ruleset_id=int(contract["ruleset"]["expected_id"]),
                branch=str(contract["canonical_protected_branch"]),
            )
            evidence["network_required"] = True
        else:
            evidence_path = args.evidence_json or DEFAULT_EVIDENCE
            evidence = _load_json(evidence_path)
            evidence["network_required"] = False
        result = evaluate_evidence(evidence, contract, required)
        result["network_required"] = bool(evidence.get("network_required"))
    except (OSError, json.JSONDecodeError, VerificationError, TypeError, KeyError) as exc:
        err = {
            "capability_id": CAPABILITY_ID,
            "ok": False,
            "RULESET_ENFORCEMENT_STATUS": "UNKNOWN",
            "error": str(exc),
            "secret_value_exposed": False,
            "network_required": bool(args.fetch),
        }
        out = json.dumps(err, sort_keys=True, indent=2) + "\n" if as_json else f"FAIL: {exc}\n"
        _die_on_credential_leak(out)
        sys.stdout.write(out)
        return 2

    if as_json:
        payload = json.dumps(result, sort_keys=True, indent=2) + "\n"
        _die_on_credential_leak(payload)
        sys.stdout.write(payload)
    else:
        human = render_human(result)
        _die_on_credential_leak(human)
        sys.stdout.write(human)
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
