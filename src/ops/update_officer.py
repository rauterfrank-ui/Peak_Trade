from __future__ import annotations

import argparse
import copy
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from src.ops.truth_officer_integration import build_unified_truth_status
from src.ops.update_officer_markdown import render_update_officer_summary
from src.ops.update_officer_profiles import (
    PROFILES,
    surface_category,
    surface_finding_description,
)
from src.ops.update_officer_schema import validate_notifier_payload, validate_report_payload

UTC = timezone.utc

PRIORITY_RANK: dict[str, int] = {"p0": 0, "p1": 1, "p2": 2, "p3": 3}
RANK_TO_PRIORITY: tuple[str, ...] = ("p0", "p1", "p2", "p3")

NOTIFIER_PAYLOAD_BASENAME = "notifier_payload.json"

_TOPIC_REVIEW_PATHS: dict[str, list[str]] = {
    "python_dependencies": ["pyproject.toml"],
    "ci_integrations": [".github/workflows"],
}

# tomllib is stdlib from 3.11; fall back to tomli for 3.9/3.10
try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib  # type: ignore[no-redef]


def _utc_ts() -> str:
    return datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")


def _safe_mkdir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _write_text(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def _normalize_pkg_name(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower().strip()


def _extract_name_and_spec(entry: str) -> tuple[str, str]:
    """Split 'package>=1.0' into ('package', '>=1.0')."""
    m = re.match(r"^([A-Za-z0-9_.\-]+)(.*)", entry.strip())
    if not m:
        return entry.strip(), ""
    return _normalize_pkg_name(m.group(1)), m.group(2).strip()


def _classify_package(
    pkg_name: str,
    spec: str,
    safe_packages: set[str],
    blocked_packages: set[str],
) -> tuple[str, str]:
    norm = _normalize_pkg_name(pkg_name)
    if norm in blocked_packages:
        return "blocked", f"{norm} is runtime/execution-adjacent"
    if norm in safe_packages:
        return "safe_review", f"{norm} is recognized dev tooling"
    if not spec or spec == "*":
        return "manual_review", f"{norm} has no version pin"
    return "manual_review", f"{norm} is not in known dev-tooling bucket"


def recommend_priority_action(classification: str, surface: str) -> tuple[str, str]:
    """Deterministic operator-facing recommendation; never implies auto-fix."""
    if classification == "blocked":
        if surface == "pyproject.toml":
            return (
                "p0",
                "Remove or replace runtime-adjacent dev dependency before proceeding.",
            )
        return (
            "p1",
            "Resolve blocked CI or supply-chain finding before merge.",
        )
    if classification == "manual_review":
        if surface == "github_actions":
            return (
                "p1",
                "Pin or verify GitHub Actions references before relying on this workflow.",
            )
        return (
            "p2",
            "Review unpinned or unrecognized dev dependency before the next tooling bump.",
        )
    return ("p3", "No immediate action; include in routine dev-tooling hygiene.")


def enrich_findings(profile: str, findings: list[dict[str, Any]]) -> None:
    for f in findings:
        surf = str(f["surface"])
        f.setdefault("notes", [])
        f["category"] = surface_category(profile, surf)
        f["description"] = surface_finding_description(profile, surf, str(f["item_name"]))
        prio, action = recommend_priority_action(str(f["classification"]), surf)
        f["recommended_priority"] = prio
        f["recommended_action"] = action


def _classify_action_ref(ref: str) -> tuple[str, str]:
    if "@" not in ref:
        return "manual_review", "action ref has no version pin"
    _action, version = ref.rsplit("@", 1)
    if re.match(r"^v?\d", version):
        return "safe_review", f"pinned at {version}"
    if re.match(r"^[0-9a-f]{7,40}$", version):
        return "safe_review", f"pinned to commit SHA {version[:12]}"
    return "manual_review", f"non-standard version ref: {version}"


# ---------------------------------------------------------------------------
# Surface scanners
# ---------------------------------------------------------------------------


def scan_pyproject(repo_root: Path, profile_cfg: dict[str, object]) -> list[dict[str, Any]]:
    pyproject_path = repo_root / "pyproject.toml"
    if not pyproject_path.exists():
        return []

    with pyproject_path.open("rb") as fh:
        data = tomllib.load(fh)

    safe_packages: set[str] = set(profile_cfg.get("safe_packages") or set())  # type: ignore[arg-type]
    blocked_packages: set[str] = set(profile_cfg.get("blocked_packages") or set())  # type: ignore[arg-type]

    findings: list[dict[str, Any]] = []

    # [project.optional-dependencies].dev
    opt_deps = data.get("project", {}).get("optional-dependencies", {})
    for entry in opt_deps.get("dev", []):
        raw = entry.split(";")[0].strip()
        pkg, spec = _extract_name_and_spec(raw)
        if not pkg:
            continue
        classification, reason = _classify_package(pkg, spec, safe_packages, blocked_packages)
        findings.append(
            {
                "surface": "pyproject.toml",
                "item_name": pkg,
                "current_spec": spec or "(unpinned)",
                "classification": classification,
                "reason": reason,
                "notes": [],
            }
        )

    # [dependency-groups].dev
    dep_groups = data.get("dependency-groups", {})
    for entry in dep_groups.get("dev", []):
        if not isinstance(entry, str):
            continue
        raw = entry.split(";")[0].strip()
        pkg, spec = _extract_name_and_spec(raw)
        if not pkg:
            continue
        already = {f["item_name"] for f in findings}
        if pkg in already:
            continue
        classification, reason = _classify_package(pkg, spec, safe_packages, blocked_packages)
        findings.append(
            {
                "surface": "pyproject.toml",
                "item_name": pkg,
                "current_spec": spec or "(unpinned)",
                "classification": classification,
                "reason": reason,
                "notes": ["from [dependency-groups].dev"],
            }
        )

    return findings


def scan_github_actions(repo_root: Path) -> list[dict[str, Any]]:
    workflows_dir = repo_root / ".github" / "workflows"
    if not workflows_dir.is_dir():
        return []

    findings: list[dict[str, Any]] = []
    seen: set[str] = set()

    for yml_path in sorted(workflows_dir.glob("*.yml")):
        try:
            text = yml_path.read_text(encoding="utf-8")
        except OSError:
            continue
        for line in text.splitlines():
            stripped = line.strip()
            if not stripped.startswith("uses:") and "uses:" not in stripped:
                continue
            m = re.search(r"uses:\s*([^\s#]+)", stripped)
            if not m:
                continue
            ref = m.group(1).strip("\"'")
            if "/" not in ref:
                continue
            if ref in seen:
                continue
            seen.add(ref)
            classification, reason = _classify_action_ref(ref)
            findings.append(
                {
                    "surface": "github_actions",
                    "item_name": ref,
                    "current_spec": ref.split("@")[-1] if "@" in ref else "(no pin)",
                    "classification": classification,
                    "reason": reason,
                    "notes": [],
                }
            )

    return findings


# ---------------------------------------------------------------------------
# Report assembly
# ---------------------------------------------------------------------------


def build_recommended_update_queue(findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Deterministic topic buckets = finding `category`; stable sort for notifier use."""
    by_topic: dict[str, list[dict[str, Any]]] = {}
    for f in findings:
        tid = str(f.get("category", "unknown"))
        by_topic.setdefault(tid, []).append(f)

    rows: list[dict[str, Any]] = []
    for topic_id, bucket in by_topic.items():
        pranks = [PRIORITY_RANK.get(str(x.get("recommended_priority", "p3")), 3) for x in bucket]
        worst = min(pranks)
        worst_p = RANK_TO_PRIORITY[worst]
        bc = sum(1 for x in bucket if x["classification"] == "blocked")
        mc = sum(1 for x in bucket if x["classification"] == "manual_review")
        sc = sum(1 for x in bucket if x["classification"] == "safe_review")
        fc = len(bucket)
        headline = (
            f"{fc} finding(s); worst_priority={worst_p}; "
            f"blocked={bc}; manual_review={mc}; safe_review={sc}"
        )
        rows.append(
            {
                "topic_id": topic_id,
                "worst_priority": worst_p,
                "finding_count": fc,
                "blocked_count": bc,
                "manual_review_count": mc,
                "safe_review_count": sc,
                "headline": headline,
                "_sort_worst": worst,
                "_sort_neg_fc": -fc,
            }
        )

    rows.sort(key=lambda r: (r["_sort_worst"], r["_sort_neg_fc"], r["topic_id"]))
    out: list[dict[str, Any]] = []
    for i, r in enumerate(rows, start=1):
        out.append(
            {
                "topic_id": r["topic_id"],
                "rank": i,
                "worst_priority": r["worst_priority"],
                "finding_count": r["finding_count"],
                "blocked_count": r["blocked_count"],
                "manual_review_count": r["manual_review_count"],
                "safe_review_count": r["safe_review_count"],
                "headline": r["headline"],
            }
        )
    return out


def _worst_priority_rank(findings: list[dict[str, Any]]) -> int | None:
    if not findings:
        return None
    return min(PRIORITY_RANK.get(str(f.get("recommended_priority", "p3")), 3) for f in findings)


def build_notifier_payload(
    officer_version: str,
    generated_at: str,
    next_recommended_topic: str,
    top_priority_reason: str,
    recommended_update_queue: list[dict[str, Any]],
    findings: list[dict[str, Any]],
) -> dict[str, Any]:
    """Deterministic machine-readable contract for external notifiers (no transport)."""
    worst_rank = _worst_priority_rank(findings)
    if worst_rank is None:
        severity = "info"
    else:
        worst_p = RANK_TO_PRIORITY[worst_rank]
        severity = {"p0": "critical", "p1": "high", "p2": "medium", "p3": "low"}[worst_p]

    if not findings:
        reminder_class = "none"
    elif any(f["classification"] == "blocked" for f in findings):
        reminder_class = "blocked"
    elif any(f["classification"] == "manual_review" for f in findings):
        reminder_class = "manual_review"
    else:
        reminder_class = "hygiene"

    review_paths = sorted(_TOPIC_REVIEW_PATHS.get(next_recommended_topic, []))

    if not recommended_update_queue:
        next_action = "No update topics queued; no notifier next action required."
    else:
        next_action = (
            f"Focus manual review on update topic `{next_recommended_topic}` first. "
            f"Context: {top_priority_reason}"
        )

    requires_manual = bool(findings) and (
        severity in ("critical", "high")
        or any(f["classification"] in ("blocked", "manual_review") for f in findings)
    )

    qcopy: list[dict[str, Any]] = copy.deepcopy(recommended_update_queue)

    return {
        "officer_version": officer_version,
        "generated_at": generated_at,
        "next_recommended_topic": next_recommended_topic,
        "top_priority_reason": top_priority_reason,
        "recommended_update_queue": qcopy,
        "recommended_next_action": next_action,
        "recommended_review_paths": review_paths,
        "severity": severity,
        "reminder_class": reminder_class,
        "requires_manual_review": requires_manual,
    }


def next_recommended_topic_and_reason(queue: list[dict[str, Any]]) -> tuple[str, str]:
    if not queue:
        return (
            "none",
            "No findings; no deterministic update topic to prioritize.",
        )
    top = queue[0]
    reason = (
        f"Topic `{top['topic_id']}` ranks first in the deterministic queue: "
        f"worst per-finding priority is `{top['worst_priority']}` across "
        f"{top['finding_count']} finding(s) (blocked={top['blocked_count']})."
    )
    return str(top["topic_id"]), reason


def build_summary(findings: list[dict[str, Any]]) -> dict[str, Any]:
    counts: dict[str, Any] = {
        "total_findings": len(findings),
        "safe_review": 0,
        "manual_review": 0,
        "blocked": 0,
        "priority_counts": {"p0": 0, "p1": 0, "p2": 0, "p3": 0},
        "category_counts": {},
    }
    for f in findings:
        cls = f["classification"]
        if cls in ("safe_review", "manual_review", "blocked"):
            counts[cls] += 1
        pr = f.get("recommended_priority", "")
        if pr in counts["priority_counts"]:
            counts["priority_counts"][pr] += 1  # type: ignore[index]
        cat = f.get("category", "unknown")
        cc: dict[str, int] = counts["category_counts"]  # type: ignore[assignment]
        cc[cat] = cc.get(cat, 0) + 1
    return counts


def emit_events(events_path: Path, findings: list[dict[str, Any]]) -> None:
    with events_path.open("w", encoding="utf-8") as fh:
        for f in findings:
            fh.write(
                json.dumps(
                    {
                        "type": "update_officer_finding",
                        "surface": f["surface"],
                        "item_name": f["item_name"],
                        "classification": f["classification"],
                        "recommended_priority": f.get("recommended_priority"),
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )


def emit_manifest(manifest_path: Path, output_dir: Path) -> None:
    files = []
    for p in sorted(output_dir.iterdir()):
        if p.is_file():
            files.append({"path": str(p), "size_bytes": p.stat().st_size})
    manifest_path.write_text(
        json.dumps({"files": files}, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def run(
    profile: str,
    output_root: str,
    repo_root: Path | None = None,
) -> int:
    repo_root = repo_root or Path.cwd()
    started_at = datetime.now(UTC).isoformat()
    run_dir = repo_root / output_root / _utc_ts()
    _safe_mkdir(run_dir)

    profile_cfg = PROFILES[profile]
    findings: list[dict[str, Any]] = []

    surfaces = profile_cfg.get("surfaces", [])
    if "pyproject.toml" in surfaces:  # type: ignore[operator]
        findings.extend(scan_pyproject(repo_root, profile_cfg))
    if "github_actions" in surfaces:  # type: ignore[operator]
        findings.extend(scan_github_actions(repo_root))

    enrich_findings(profile, findings)
    findings.sort(
        key=lambda f: (
            f["recommended_priority"],
            f["classification"],
            f["surface"],
            f["item_name"],
        )
    )

    emit_events(run_dir / "events.jsonl", findings)

    summary = build_summary(findings)
    summary["unified_truth_status"] = build_unified_truth_status(repo_root)
    success = summary["blocked"] == 0
    recommended_update_queue = build_recommended_update_queue(findings)
    next_recommended_topic, top_priority_reason = next_recommended_topic_and_reason(
        recommended_update_queue
    )
    finished_at = datetime.now(UTC).isoformat()
    officer_version = "v3-min"

    notifier_payload = build_notifier_payload(
        officer_version=officer_version,
        generated_at=finished_at,
        next_recommended_topic=next_recommended_topic,
        top_priority_reason=top_priority_reason,
        recommended_update_queue=recommended_update_queue,
        findings=findings,
    )
    validate_notifier_payload(notifier_payload)
    _write_text(
        run_dir / NOTIFIER_PAYLOAD_BASENAME,
        json.dumps(notifier_payload, indent=2, ensure_ascii=False) + "\n",
    )

    report_payload: dict[str, Any] = {
        "officer_version": officer_version,
        "profile": profile,
        "started_at": started_at,
        "finished_at": finished_at,
        "output_dir": str(run_dir),
        "repo_root": str(repo_root),
        "success": success,
        "findings": findings,
        "summary": summary,
        "next_recommended_topic": next_recommended_topic,
        "top_priority_reason": top_priority_reason,
        "recommended_update_queue": recommended_update_queue,
        "notifier_payload_path": NOTIFIER_PAYLOAD_BASENAME,
    }

    validate_report_payload(report_payload)

    _write_text(
        run_dir / "report.json",
        json.dumps(report_payload, indent=2, ensure_ascii=False) + "\n",
    )
    _write_text(
        run_dir / "summary.md",
        render_update_officer_summary(report_payload),
    )

    emit_manifest(run_dir / "manifest.json", run_dir)

    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Peak_Trade Update Officer v3")
    parser.add_argument(
        "--profile",
        choices=sorted(PROFILES.keys()),
        default="dev_tooling_review",
    )
    parser.add_argument("--output-root", default="out/ops/update_officer")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    return run(profile=args.profile, output_root=args.output_root)


if __name__ == "__main__":
    raise SystemExit(main())
