from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from src.ops.update_officer_markdown import render_update_officer_summary
from src.ops.update_officer_profiles import PROFILES
from src.ops.update_officer_schema import validate_report_payload

UTC = timezone.utc

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


def build_summary(findings: list[dict[str, Any]]) -> dict[str, int]:
    counts = {"total_findings": len(findings), "safe_review": 0, "manual_review": 0, "blocked": 0}
    for f in findings:
        cls = f["classification"]
        if cls in counts:
            counts[cls] += 1
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

    findings.sort(key=lambda f: (f["classification"], f["surface"], f["item_name"]))

    emit_events(run_dir / "events.jsonl", findings)

    summary = build_summary(findings)
    success = summary["blocked"] == 0

    report_payload: dict[str, Any] = {
        "officer_version": "v0-min",
        "profile": profile,
        "started_at": started_at,
        "finished_at": datetime.now(UTC).isoformat(),
        "output_dir": str(run_dir),
        "repo_root": str(repo_root),
        "success": success,
        "findings": findings,
        "summary": summary,
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
    parser = argparse.ArgumentParser(description="Peak_Trade Update Officer v0")
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
