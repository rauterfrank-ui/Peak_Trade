#!/usr/bin/env python3
"""Review Testnet bounded observation evidence without running anything.

Taxonomy cross-reference (review-input-only): indexed in
``docs/ops/specs/RUNTIME_LANE_TAXONOMY_AUTHORITY_LEVELS_CONTRACT_V0.md`` §10
(bounded observation evidence review scripts).

Non-authorizing offline review only. Does not execute bounded observation adapters.
Does not grant Live/broker/exchange approval. Does not override scheduler, preflight,
or operator approval boundaries.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.ops.primary_evidence_retention_v0 import (
    BOUNDED_TESTNET_DURABLE_RUN_REQUIRED_REL_PATHS,
    validate_durable_primary_evidence_root,
)

PASS = "PASS"
REVIEW_REQUIRED = "REVIEW_REQUIRED"
REVIEW_REQUIRED_EXIT = 1
USAGE_EXIT = 2

SCHEMA_VERSION = "review_testnet_bounded_observation_evidence.v0"
WRAPPER_EVIDENCE_DIR = "wrapper_evidence"
BOUNDED_TESTNET_MD = "TESTNET_BOUNDED_OBSERVATION.md"
STEPS_JSONL = "steps.jsonl"
MANIFEST_JSON = "manifest.json"
EXPECTED_MANIFEST_SCHEMA = "testnet_bounded_dry_run.v0"
PROOF_CONTRACT_DOC = "docs/ops/specs/FUTURES_TESTNET_DRY_RUN_PROOF_CONTRACT_V0.md"
SAFETY_STRINGS = (
    "TESTNET_SANDBOX_ONLY",
    "NO_PRODUCTION_FALLBACK",
    "NO_LIVE_ORDER_SUBMISSION",
)
FORBIDDEN_GATE_CLAIMS = (
    "BLOCKER_CLEARANCE_GRANTED=true",
    "TESTNET_READY=true",
    "TESTNET_AUTHORIZED=true",
    "PREFLIGHT_BLOCKED=false",
    "LIVE_ALLOWED=true",
    "GLB_014_CLEARED=true",
    "GLB_015_CLEARED=true",
)


def _consume_argv(argv: list[str] | None) -> list[str]:
    if argv is None:
        return sys.argv[1:]
    if argv and not argv[0].startswith("-"):
        return list(argv[1:])
    return list(argv)


def _load_json(path: Path) -> tuple[Any | None, str | None]:
    try:
        return json.loads(path.read_text(encoding="utf-8")), None
    except (OSError, json.JSONDecodeError) as exc:
        return None, f"{path.name} is not valid JSON: {exc}"


def _text_contains_any(text: str, needles: tuple[str, ...]) -> bool:
    return any(needle in text for needle in needles)


def _resolve_wrapper_evidence_root(staging_root: Path) -> Path:
    nested = staging_root / WRAPPER_EVIDENCE_DIR
    if nested.is_dir():
        return nested
    return staging_root


def review_evidence(
    staging_root: Path,
    *,
    durable_run_root: Path | None = None,
) -> dict[str, Any]:
    issues: list[str] = []
    checks: dict[str, bool] = {}

    evidence_root = _resolve_wrapper_evidence_root(staging_root)
    checks["evidence_root_exists"] = evidence_root.is_dir()
    if not checks["evidence_root_exists"]:
        issues.append(f"evidence root missing: {evidence_root}")

    markdown = evidence_root / BOUNDED_TESTNET_MD
    checks["markdown_present"] = markdown.is_file()
    if not checks["markdown_present"]:
        issues.append(f"missing {BOUNDED_TESTNET_MD}")
    else:
        md_text = markdown.read_text(encoding="utf-8", errors="replace")
        checks["markdown_has_safety_strings"] = _text_contains_any(md_text, SAFETY_STRINGS)
        if not checks["markdown_has_safety_strings"]:
            issues.append(f"{BOUNDED_TESTNET_MD} missing safety boundary strings")
        checks["markdown_no_gate_claims"] = not _text_contains_any(md_text, FORBIDDEN_GATE_CLAIMS)
        if not checks["markdown_no_gate_claims"]:
            issues.append(f"{BOUNDED_TESTNET_MD} must not claim gate clearance")
        checks["proof_contract_refs_present"] = PROOF_CONTRACT_DOC in md_text
        if not checks["proof_contract_refs_present"]:
            issues.append(f"{BOUNDED_TESTNET_MD} must reference {PROOF_CONTRACT_DOC}")

    steps = evidence_root / STEPS_JSONL
    checks["steps_present"] = steps.is_file()
    if not checks["steps_present"]:
        issues.append(f"missing {STEPS_JSONL}")
    elif not steps.read_text(encoding="utf-8", errors="replace").strip():
        checks["steps_non_empty"] = False
        issues.append(f"{STEPS_JSONL} is empty")
    else:
        checks["steps_non_empty"] = True

    manifest_path = evidence_root / MANIFEST_JSON
    checks["manifest_present"] = manifest_path.is_file()
    manifest_payload: Any | None = None
    if not checks["manifest_present"]:
        issues.append(f"missing {MANIFEST_JSON}")
    else:
        manifest_payload, manifest_err = _load_json(manifest_path)
        checks["manifest_valid_json"] = manifest_err is None
        if manifest_err:
            issues.append(manifest_err)
        elif isinstance(manifest_payload, dict):
            schema = manifest_payload.get("schema")
            checks["manifest_schema_match"] = schema == EXPECTED_MANIFEST_SCHEMA
            if not checks["manifest_schema_match"]:
                issues.append(
                    f"{MANIFEST_JSON} schema must be {EXPECTED_MANIFEST_SCHEMA!r}, got {schema!r}"
                )
            manifest_blob = json.dumps(manifest_payload, sort_keys=True)
            checks["manifest_has_safety_strings"] = _text_contains_any(
                manifest_blob, SAFETY_STRINGS
            )
            if not checks["manifest_has_safety_strings"]:
                issues.append(f"{MANIFEST_JSON} missing safety boundary strings")
            checks["manifest_has_network_boundary_fields"] = (
                manifest_payload.get("broker_connected") is False
                and manifest_payload.get("production_fallback") is False
            )
            if not checks["manifest_has_network_boundary_fields"]:
                issues.append(
                    f"{MANIFEST_JSON} must declare broker_connected=false and production_fallback=false"
                )
            checks["proof_contract_refs_present"] = checks.get(
                "proof_contract_refs_present", False
            ) or (manifest_payload.get("proof_contract_doc") == PROOF_CONTRACT_DOC)
            if not checks["proof_contract_refs_present"]:
                issues.append(f"missing proof contract reference to {PROOF_CONTRACT_DOC}")
        else:
            checks["manifest_schema_match"] = False
            issues.append(f"{MANIFEST_JSON} must be a JSON object")

    logs_dir = staging_root / "logs"
    stdout_log = logs_dir / "wrapper_stdout.log"
    stderr_log = logs_dir / "wrapper_stderr.log"
    checks["stdout_log_present"] = stdout_log.is_file()
    checks["stderr_log_present"] = stderr_log.is_file()
    if not checks["stdout_log_present"]:
        issues.append("missing logs/wrapper_stdout.log")
    if not checks["stderr_log_present"]:
        issues.append("missing logs/wrapper_stderr.log")

    verdict = PASS if not issues else REVIEW_REQUIRED
    result: dict[str, Any] = {
        "verdict": verdict,
        "schema_version": SCHEMA_VERSION,
        "staging_root": str(staging_root.resolve()),
        "evidence_root": str(evidence_root.resolve()),
        "checks": checks,
        "issues": issues,
        "non_authorizing": True,
    }

    if durable_run_root is not None:
        durable_root = durable_run_root.resolve()
        ok, msg, durable_detail = validate_durable_primary_evidence_root(
            durable_root,
            required_rel_paths=BOUNDED_TESTNET_DURABLE_RUN_REQUIRED_REL_PATHS,
        )
        result["durable_run_root"] = str(durable_root)
        result["durable_checks"] = durable_detail.get("checks", {})
        durable_issues = list(durable_detail.get("issues", []))
        if not ok and msg and msg not in durable_issues:
            durable_issues.insert(0, msg)
        if durable_issues:
            result["issues"] = list(result.get("issues", [])) + durable_issues
            result["checks"]["durable_primary_evidence_valid"] = False
            result["verdict"] = REVIEW_REQUIRED
        else:
            result["checks"]["durable_primary_evidence_valid"] = True

    return result


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Review Testnet bounded observation evidence. "
            "Non-authorizing; does not claim readiness or gate clearance."
        )
    )
    parser.add_argument("--staging-root", type=Path, required=True)
    parser.add_argument(
        "--durable-run-root",
        type=Path,
        default=None,
        help=(
            "Optional durable primary evidence run root outside /tmp (Preflight §2a.1). "
            "Default off; staging-only review when omitted."
        ),
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Optional path to write REVIEW_RESULT.json",
    )
    parser.add_argument("--json", action="store_true", help="Emit review JSON to stdout.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    try:
        args = parser.parse_args(_consume_argv(argv))
    except SystemExit as exc:
        if exc.code in (0, None):
            raise
        return USAGE_EXIT

    staging_root = args.staging_root.expanduser().resolve()
    if not staging_root.is_dir():
        print(f"staging root must exist: {staging_root}", file=sys.stderr)
        return USAGE_EXIT

    durable_run_root: Path | None = None
    if args.durable_run_root is not None:
        durable_run_root = args.durable_run_root.expanduser().resolve()
        if not durable_run_root.is_dir():
            print(f"durable run root must exist: {durable_run_root}", file=sys.stderr)
            return USAGE_EXIT

    result = review_evidence(staging_root, durable_run_root=durable_run_root)
    payload = json.dumps(result, indent=2, sort_keys=True)
    if args.out is not None:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(payload + "\n", encoding="utf-8")
    if args.json or args.out is None:
        print(payload)
    return 0 if result["verdict"] == PASS else REVIEW_REQUIRED_EXIT


if __name__ == "__main__":
    raise SystemExit(main())
