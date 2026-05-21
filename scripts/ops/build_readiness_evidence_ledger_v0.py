#!/usr/bin/env python3
"""Build an offline readiness/evidence ledger from a runtime evidence archive root.

Taxonomy cross-reference (review-input-only): indexed in
``docs/ops/specs/RUNTIME_LANE_TAXONOMY_AUTHORITY_LEVELS_CONTRACT_V0.md`` §10
(readiness aggregate and bounded observation retention adapters).

Default shadow/testnet run IDs use the bounded observation evidence family
(``shadow_bounded_observation_*``, ``testnet_bounded_observation_*``) as
review-input-only archive inputs — ledger PASS does not authorize adapter
``--execute``, Stage-3 escalation, or runtime start.

Non-authorizing: review-input-only; does not start runtime, read secrets, or grant
Live/Testnet/broker/exchange approval or trading authorization. Does not override
scheduler boundary guards, preflight BLOCKED, or operator-explicit approval.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA = "peak_trade.readiness_evidence_ledger.v0"

DEFAULT_PAPER_RUN_ID = "paper_only_120min_20260520T171443Z"
DEFAULT_SHADOW_RUN_ID = "shadow_bounded_observation_20260520T214522Z"
DEFAULT_TESTNET_RUN_ID = "testnet_bounded_observation_20260520T232014Z"

VERDICT_PASS_BLOCKED_SAFE = "READINESS_EVIDENCE_LEDGER_PASS_BLOCKED_SAFE"
VERDICT_REVIEW_REQUIRED = "READINESS_EVIDENCE_LEDGER_REVIEW_REQUIRED"
VERDICT_FAIL_CLOSED = "READINESS_EVIDENCE_LEDGER_FAIL_CLOSED"

BLOCKER_HOLD = "HOLD_NO_PAPER_RUN_NOT_CLEARED"
BLOCKER_GLB_014 = "GLB_014_NOT_CLEARED"
BLOCKER_GLB_015 = "GLB_015_NOT_CLEARED"
BLOCKER_PREFLIGHT = "PREFLIGHT_BLOCKED"
BLOCKER_LIVE = "LIVE_NOT_AUTHORIZED"
BLOCKER_BROKER = "BROKER_EXCHANGE_NOT_AUTHORIZED"

PLANNING_SURFACE_MARKERS: tuple[tuple[str, str], ...] = (
    ("named_go_no_go_authority_selection_record", "named_go_no_go_authority"),
    ("explicit_go_no_go_decision_template", "explicit_go_no_go_template"),
    ("production_secret_storage_mechanism_evaluation", "production_secret_storage_evaluation"),
    ("live_production_authority_boundary", "live_production_authority_boundary"),
    ("preflight_status_refresh_with_hold_decision_context", "preflight_status_refresh"),
    ("hold_operator_global_clearance_decision_record", "hold_operator_global_clearance"),
    ("glb014_015_operator_clearance_decision_record", "glb_operator_clearance"),
)

UNSAFE_TRUE_KEYS: frozenset[str] = frozenset(
    key.upper()
    for key in (
        "secret_values_included",
        "live_allowed",
        "broker_exchange_allowed",
        "go_decision_granted",
        "hold_no_paper_run_cleared",
        "glb_014_cleared",
        "glb_015_cleared",
    )
)

UNSAFE_KEY_TO_CODE: dict[str, str] = {
    "SECRET_VALUES_INCLUDED": "UNSAFE_SECRET_VALUES_INCLUDED",
    "LIVE_ALLOWED": "UNSAFE_LIVE_ALLOWED",
    "BROKER_EXCHANGE_ALLOWED": "UNSAFE_BROKER_EXCHANGE_ALLOWED",
    "GO_DECISION_GRANTED": "UNSAFE_GO_DECISION_GRANTED",
    "HOLD_NO_PAPER_RUN_CLEARED": "UNSAFE_HOLD_CLEARED",
    "GLB_014_CLEARED": "UNSAFE_GLB_CLEARED",
    "GLB_015_CLEARED": "UNSAFE_GLB_CLEARED",
}

MACHINE_LINE_RE = re.compile(r"^([A-Z0-9_]+)=(true|false)\s*$")

GOVERNANCE_KEYS = (
    "go_decision_granted",
    "no_go_decision_granted",
    "hold_no_paper_run_cleared",
    "glb_014_cleared",
    "glb_015_cleared",
    "preflight_ready",
    "live_allowed",
    "broker_exchange_allowed",
    "secret_values_included",
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
class BuildContext:
    archive_root: Path
    paper_run_id: str
    shadow_run_id: str
    testnet_run_id: str
    fixed_generated_at_utc: str | None = None
    issues: list[Issue] = field(default_factory=list)

    def add_issue(self, code: str, message: str, path: Path | None = None) -> None:
        rel = None
        if path is not None:
            try:
                rel = str(path.relative_to(self.archive_root))
            except ValueError:
                rel = str(path)
        self.issues.append(Issue(code=code, message=message, path=rel))


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_manifest_directory(root: Path, ctx: BuildContext, label: str) -> bool:
    manifest_path = root / "MANIFEST.sha256"
    if not root.is_dir():
        ctx.add_issue("MISSING_RUN_DIR", f"{label} run directory missing", root)
        return False
    if not manifest_path.is_file():
        ctx.add_issue("MISSING_MANIFEST", f"{label} MANIFEST.sha256 missing", manifest_path)
        return False

    ok = True
    for line_no, raw in enumerate(manifest_path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split(None, 1)
        if len(parts) != 2:
            ctx.add_issue(
                "MANIFEST_ENTRY_MISSING",
                f"{label} MANIFEST line {line_no} invalid",
                manifest_path,
            )
            ok = False
            continue
        expected_hash, rel_path = parts
        target = root / rel_path
        if not target.is_file():
            ctx.add_issue(
                "MANIFEST_ENTRY_MISSING",
                f"{label} manifest entry missing file: {rel_path}",
                target,
            )
            ok = False
            continue
        actual_hash = _sha256_file(target)
        if actual_hash != expected_hash:
            ctx.add_issue(
                "MANIFEST_HASH_MISMATCH",
                f"{label} hash mismatch for {rel_path}",
                target,
            )
            ok = False
    return ok


def _load_review_verdict(review_path: Path) -> tuple[str | None, str | None]:
    if not review_path.is_file():
        return None, "missing"
    try:
        payload = json.loads(review_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return None, f"invalid JSON: {exc}"
    verdict = payload.get("verdict")
    if not isinstance(verdict, str):
        return None, "verdict missing or not string"
    return verdict, None


def verify_review(
    run_dir: Path,
    ctx: BuildContext,
    label: str,
    *,
    required: bool,
) -> bool:
    review_path = run_dir / "review" / "REVIEW_RESULT.json"
    verdict, err = _load_review_verdict(review_path)
    if err == "missing":
        if required:
            ctx.add_issue(
                "MISSING_REVIEW_JSON",
                f"{label} review/REVIEW_RESULT.json missing",
                review_path,
            )
            return False
        return True
    if err is not None:
        ctx.add_issue(
            "MISSING_REVIEW_JSON",
            f"{label} review invalid: {err}",
            review_path,
        )
        return False
    if verdict != "PASS":
        ctx.add_issue(
            "REVIEW_VERDICT_NOT_PASS",
            f"{label} review verdict must be PASS, got {verdict!r}",
            review_path,
        )
        return False
    return True


def _find_planning_dirs(planning_root: Path, marker: str) -> list[Path]:
    if not planning_root.is_dir():
        return []
    return sorted(
        [p for p in planning_root.iterdir() if p.is_dir() and marker in p.name],
        key=lambda p: p.name,
    )


def _iter_machine_lines(text: str) -> list[tuple[str, bool]]:
    out: list[tuple[str, bool]] = []
    for raw in text.splitlines():
        match = MACHINE_LINE_RE.match(raw.strip())
        if not match:
            continue
        out.append((match.group(1), match.group(2) == "true"))
    return out


def _parse_machine_line(text: str, key: str) -> bool | None:
    machine_key = key.upper()
    values = [value for name, value in _iter_machine_lines(text) if name == machine_key]
    if not values:
        return None
    return values[-1]


def _scan_planning_texts(planning_root: Path) -> str:
    if not planning_root.is_dir():
        return ""
    chunks: list[str] = []
    for path in sorted(planning_root.rglob("*")):
        if not path.is_file():
            continue
        if path.suffix.lower() not in {".md", ".json", ".log"}:
            continue
        if path.name in {"MANIFEST.sha256", "MANIFEST_VERIFY.log"}:
            continue
        try:
            chunks.append(path.read_text(encoding="utf-8", errors="replace"))
        except OSError:
            continue
    return "\n".join(chunks)


def scan_unsafe_planning(planning_root: Path, ctx: BuildContext) -> None:
    if not planning_root.is_dir():
        return
    for path in sorted(planning_root.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in {".md", ".json", ".log"}:
            continue
        if path.name in {"MANIFEST.sha256", "MANIFEST_VERIFY.log"}:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for key, value in _iter_machine_lines(text):
            if value and key in UNSAFE_TRUE_KEYS:
                code = UNSAFE_KEY_TO_CODE.get(key, "UNSAFE_PLANNING_MARKER")
                ctx.add_issue(
                    code,
                    f"unsafe planning machine line {key}=true",
                    path,
                )


def verify_planning_surfaces(planning_root: Path, ctx: BuildContext) -> dict[str, bool]:
    present: dict[str, bool] = {}
    for marker, key in PLANNING_SURFACE_MARKERS:
        dirs = _find_planning_dirs(planning_root, marker)
        if not dirs:
            ctx.add_issue(
                "MISSING_PLANNING_SURFACE",
                f"planning surface missing for marker {marker!r}",
                planning_root / marker,
            )
            present[key] = False
            continue
        verified = False
        for directory in dirs:
            if verify_manifest_directory(directory, ctx, f"planning:{marker}"):
                verified = True
                break
        if not verified:
            ctx.add_issue(
                "PLANNING_MANIFEST_INVALID",
                f"planning surface {marker!r} has no valid MANIFEST",
                dirs[-1],
            )
        present[key] = verified
    return present


def derive_governance(planning_root: Path) -> dict[str, bool]:
    blob = _scan_planning_texts(planning_root)
    governance: dict[str, bool] = {}
    for key in GOVERNANCE_KEYS:
        machine_key = key.upper()
        parsed = _parse_machine_line(blob, machine_key)
        governance[key] = parsed if parsed is not None else False

    if _parse_machine_line(blob, "NAMED_GO_NO_GO_AUTHORITY_SELECTED") is True:
        governance.setdefault("_named_selected", True)
    else:
        governance.setdefault("_named_selected", False)

    governance["governance_blocked"] = (
        governance["go_decision_granted"] is False
        and governance["live_allowed"] is False
        and governance["broker_exchange_allowed"] is False
        and (
            governance["hold_no_paper_run_cleared"] is False
            or governance["glb_014_cleared"] is False
            or governance["glb_015_cleared"] is False
            or governance["preflight_ready"] is False
        )
    )
    return governance


def derive_blockers(governance: dict[str, bool]) -> list[str]:
    blockers: list[str] = []
    if not governance.get("hold_no_paper_run_cleared", False):
        blockers.append(BLOCKER_HOLD)
    if not governance.get("glb_014_cleared", False):
        blockers.append(BLOCKER_GLB_014)
    if not governance.get("glb_015_cleared", False):
        blockers.append(BLOCKER_GLB_015)
    if not governance.get("preflight_ready", False):
        blockers.append(BLOCKER_PREFLIGHT)
    if not governance.get("live_allowed", False):
        blockers.append(BLOCKER_LIVE)
    if not governance.get("broker_exchange_allowed", False):
        blockers.append(BLOCKER_BROKER)
    return sorted(set(blockers))


def derive_verdict(ctx: BuildContext) -> str:
    codes = {issue.code for issue in ctx.issues}
    if any(code.startswith("UNSAFE_") for code in codes):
        return VERDICT_FAIL_CLOSED
    if "REVIEW_VERDICT_NOT_PASS" in codes:
        return VERDICT_FAIL_CLOSED
    review_required_codes = {
        "MISSING_ARCHIVE_ROOT",
        "MISSING_RUN_DIR",
        "MISSING_MANIFEST",
        "MANIFEST_ENTRY_MISSING",
        "MANIFEST_HASH_MISMATCH",
        "MISSING_REVIEW_JSON",
        "MISSING_PLANNING_SURFACE",
        "PLANNING_MANIFEST_INVALID",
    }
    if codes & review_required_codes:
        return VERDICT_REVIEW_REQUIRED
    return VERDICT_PASS_BLOCKED_SAFE


def build_ledger(ctx: BuildContext) -> dict[str, Any]:
    archive_root = ctx.archive_root
    if not archive_root.is_dir():
        ctx.add_issue("MISSING_ARCHIVE_ROOT", "archive root does not exist", archive_root)

    paper_dir = archive_root / "runs" / "paper" / ctx.paper_run_id
    shadow_dir = archive_root / "runs" / "shadow" / ctx.shadow_run_id
    testnet_dir = archive_root / "runs" / "testnet" / ctx.testnet_run_id
    planning_root = archive_root / "planning"

    paper_manifest_ok = verify_manifest_directory(paper_dir, ctx, "paper")
    shadow_manifest_ok = verify_manifest_directory(shadow_dir, ctx, "shadow")
    shadow_review_ok = verify_review(shadow_dir, ctx, "shadow", required=True)
    testnet_manifest_ok = verify_manifest_directory(testnet_dir, ctx, "testnet")
    testnet_review_ok = verify_review(testnet_dir, ctx, "testnet", required=True)

    paper_ok = paper_manifest_ok
    shadow_ok = shadow_manifest_ok and shadow_review_ok
    testnet_ok = testnet_manifest_ok and testnet_review_ok

    scan_unsafe_planning(planning_root, ctx)
    planning_present = verify_planning_surfaces(planning_root, ctx)
    governance = derive_governance(planning_root)

    named_selected = planning_present.get("named_go_no_go_authority", False)
    if named_selected:
        parsed_named = _parse_machine_line(
            _scan_planning_texts(planning_root), "NAMED_GO_NO_GO_AUTHORITY_SELECTED"
        )
        if parsed_named is False:
            named_selected = False

    planning_chain_present = all(planning_present.values())

    generated_at = ctx.fixed_generated_at_utc or os.environ.get("PEAK_TRADE_FIXED_GENERATED_AT_UTC")
    if not generated_at:
        generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    blockers = derive_blockers(governance)
    verdict = derive_verdict(ctx)

    return {
        "schema": SCHEMA,
        "generated_at_utc": generated_at,
        "archive_root": str(archive_root.resolve()),
        "evidence": {
            "paper_run_id": ctx.paper_run_id,
            "shadow_run_id": ctx.shadow_run_id,
            "testnet_run_id": ctx.testnet_run_id,
            "paper_primary_evidence_verified": paper_ok,
            "shadow_primary_evidence_verified": shadow_ok,
            "testnet_primary_evidence_verified": testnet_ok,
            "triple_lane_primary_evidence": paper_ok and shadow_ok and testnet_ok,
        },
        "planning": {
            "planning_chain_present": planning_chain_present,
            "named_go_no_go_authority_selected": bool(named_selected),
            "explicit_go_no_go_template_present": planning_present.get(
                "explicit_go_no_go_template", False
            ),
            "production_secret_storage_evaluation_present": planning_present.get(
                "production_secret_storage_evaluation", False
            ),
        },
        "governance": {
            "go_decision_granted": governance["go_decision_granted"],
            "no_go_decision_granted": governance["no_go_decision_granted"],
            "hold_no_paper_run_cleared": governance["hold_no_paper_run_cleared"],
            "glb_014_cleared": governance["glb_014_cleared"],
            "glb_015_cleared": governance["glb_015_cleared"],
            "preflight_ready": governance["preflight_ready"],
            "live_allowed": governance["live_allowed"],
            "broker_exchange_allowed": governance["broker_exchange_allowed"],
            "secret_values_included": governance["secret_values_included"],
            "governance_blocked": governance["governance_blocked"],
        },
        "blockers": blockers,
        "verdict": verdict,
        "issues": [issue.as_dict() for issue in ctx.issues],
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive-root", type=Path, required=True)
    parser.add_argument("--paper-run-id", default=DEFAULT_PAPER_RUN_ID)
    parser.add_argument("--shadow-run-id", default=DEFAULT_SHADOW_RUN_ID)
    parser.add_argument("--testnet-run-id", default=DEFAULT_TESTNET_RUN_ID)
    parser.add_argument("--fixed-generated-at-utc")
    parser.add_argument("--json", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    ctx = BuildContext(
        archive_root=args.archive_root.expanduser().resolve(),
        paper_run_id=args.paper_run_id,
        shadow_run_id=args.shadow_run_id,
        testnet_run_id=args.testnet_run_id,
        fixed_generated_at_utc=args.fixed_generated_at_utc,
    )
    ledger = build_ledger(ctx)
    if args.json:
        print(json.dumps(ledger, indent=2, sort_keys=False))
    else:
        print(f"verdict={ledger['verdict']}")
        print(f"triple_lane={ledger['evidence']['triple_lane_primary_evidence']}")
        print(f"issues={len(ledger['issues'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
