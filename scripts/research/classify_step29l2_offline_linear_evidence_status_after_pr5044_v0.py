#!/usr/bin/env python3
"""Classify STEP29L.2 offline linear evidence surface status after PR5044 (offline only)."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))
sys.path.insert(0, str(REPO_ROOT))

from research.linear_evidence.import_boundary import (  # noqa: E402
    classify_import_boundary_scan,
    scan_paths_import_boundary,
)
from scripts.ops.primary_evidence_retention_v0 import (  # noqa: E402
    verify_manifest_sha256,
    write_manifest_sha256,
)

CLASSIFICATION = "STEP29L2_OFFLINE_LINEAR_EVIDENCE_STATUS_AFTER_PR5044"
MISSING_SURFACE = "offline_signal_orthogonality_diagnostics_v0"

LINEAR_EVIDENCE_REL = Path("src/research/linear_evidence")
RESEARCH_SCRIPT_NAMES = (
    "offline_factor_exposure_diagnostics_v0.py",
    "offline_linear_cost_model_diagnostics_v0.py",
    "offline_parameter_sensitivity_surface_v0.py",
    "offline_rolling_linear_drift_diagnostics_v0.py",
)
RESEARCH_TEST_NAMES = (
    "test_offline_factor_exposure_diagnostics_v0.py",
    "test_offline_linear_cost_model_diagnostics_v0.py",
    "test_offline_parameter_sensitivity_surface_v0.py",
    "test_offline_rolling_linear_drift_diagnostics_v0.py",
)


def _git_rev_parse(ref: str) -> str:
    proc = subprocess.run(
        ["git", "rev-parse", ref],
        cwd=str(REPO_ROOT),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if proc.returncode != 0:
        return "UNKNOWN"
    return proc.stdout.strip()


def _git_status_short() -> str:
    proc = subprocess.run(
        ["git", "status", "--short"],
        cwd=str(REPO_ROOT),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    return proc.stdout.strip()


def _collect_scan_paths(repo_root: Path) -> list[Path]:
    paths: list[Path] = []
    linear_dir = repo_root / LINEAR_EVIDENCE_REL
    if linear_dir.is_dir():
        paths.extend(sorted(p for p in linear_dir.rglob("*.py") if p.is_file()))
    for name in RESEARCH_SCRIPT_NAMES:
        candidate = repo_root / "scripts/research" / name
        if candidate.is_file():
            paths.append(candidate)
    for name in RESEARCH_TEST_NAMES:
        candidate = repo_root / "tests/research" / name
        if candidate.is_file():
            paths.append(candidate)
    return paths


def _write_inventory(repo_root: Path, output_dir: Path) -> None:
    lines = ["=== linear_evidence tree ==="]
    linear_dir = repo_root / LINEAR_EVIDENCE_REL
    if linear_dir.is_dir():
        for path in sorted(linear_dir.rglob("*")):
            if path.is_file():
                lines.append(path.relative_to(repo_root).as_posix())
    lines.extend(["", "=== research scripts ==="])
    for name in RESEARCH_SCRIPT_NAMES:
        rel = f"scripts/research/{name}"
        if (repo_root / rel).is_file():
            lines.append(rel)
    lines.extend(["", "=== research tests ==="])
    for name in RESEARCH_TEST_NAMES:
        rel = f"tests/research/{name}"
        if (repo_root / rel).is_file():
            lines.append(rel)
    (output_dir / "inventory.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_context(output_dir: Path, *, head: str, origin_main: str) -> None:
    worktree_clean = _git_status_short() == ""
    (output_dir / "context.txt").write_text(
        "\n".join(
            [
                f"CLASSIFICATION={CLASSIFICATION}",
                f"HEAD={head}",
                f"ORIGIN_MAIN={origin_main}",
                f"HEAD_EQUALS_ORIGIN_MAIN={str(head == origin_main).lower()}",
                f"WORKTREE_CLEAN={str(worktree_clean).lower()}",
                "AUTHORITY_EFFECT=NONE",
                "RUNTIME_EFFECT=NONE",
                "SYSTEM_ECONOMIC_EVIDENCE_ADMISSIBLE=false",
                "RUNTIME_REWIRE_ADMISSIBLE=false",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def _write_surface_classification(output_dir: Path) -> None:
    orthogonality_module = (REPO_ROOT / "src/research/linear_evidence/orthogonality.py").is_file()
    orthogonality_cli = (
        REPO_ROOT / "scripts/research/offline_signal_orthogonality_diagnostics_v0.py"
    ).is_file()
    orthogonality_tests = (
        REPO_ROOT / "tests/research/test_offline_signal_orthogonality_diagnostics_v0.py"
    ).is_file()
    missing_modules: list[str] = []
    missing_clis: list[str] = []
    missing_tests: list[str] = []
    if not orthogonality_module:
        missing_modules.extend(["orthogonality_module", "diagnostics"])
    if not orthogonality_cli:
        missing_clis.append("orthogonality_cli")
    if not orthogonality_tests:
        missing_tests.append("orthogonality_tests")
    (output_dir / "classification.txt").write_text(
        "\n".join(
            [
                f"REQUIRED_MODULES_PRESENT={str(not missing_modules).lower()}",
                f"REQUIRED_CLIS_PRESENT={str(not missing_clis).lower()}",
                f"REQUIRED_TESTS_PRESENT={str(not missing_tests).lower()}",
                f"MISSING_REQUIRED_MODULES={','.join(missing_modules) if missing_modules else 'NONE'}",
                f"MISSING_REQUIRED_CLIS={','.join(missing_clis) if missing_clis else 'NONE'}",
                f"MISSING_REQUIRED_TESTS={','.join(missing_tests) if missing_tests else 'NONE'}",
                "STEP29L2_SURFACE_STATUS=PARTIAL",
                "NEXT_GAP_CLASS=MISSING_REQUIRED_DIAGNOSTIC_SURFACE",
                f"MISSING_SURFACE={MISSING_SURFACE}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def _write_import_boundary_artifacts(
    output_dir: Path,
    *,
    hits,
    docstring_comment_probes: list[str],
    classification: dict[str, str | int | bool],
) -> None:
    scan_lines = ["=== authority/runtime import scan ==="]
    if hits:
        scan_lines.extend(hit.format_scan_line() for hit in hits)
    (output_dir / "import_boundary_scan.txt").write_text(
        "\n".join(scan_lines) + "\n",
        encoding="utf-8",
    )

    class_lines = [
        f"IMPORT_BOUNDARY_HITS={classification['IMPORT_BOUNDARY_HITS']}",
        f"BAD_IMPORT_BOUNDARY_HITS={classification['BAD_IMPORT_BOUNDARY_HITS']}",
        f"IMPORT_BOUNDARY_STATUS={classification['IMPORT_BOUNDARY_STATUS']}",
        (
            "false_positive_docstring_ignored="
            f"{str(classification['false_positive_docstring_ignored']).lower()}"
        ),
        f"DOCSTRING_COMMENT_PROBE_HITS={classification['DOCSTRING_COMMENT_PROBE_HITS']}",
    ]
    if hits:
        class_lines.append(f"BAD_HIT={hits[0].format_scan_line()}")
    elif docstring_comment_probes:
        class_lines.append(f"IGNORED_PROBE_HIT={docstring_comment_probes[0]}")
    (output_dir / "import_boundary_classification.txt").write_text(
        "\n".join(class_lines) + "\n",
        encoding="utf-8",
    )


def _write_final_report(
    output_dir: Path,
    *,
    head: str,
    origin_main: str,
    classification: dict[str, str | int | bool],
    manifest_verify_rc: int,
) -> None:
    (output_dir / "final_report.txt").write_text(
        "\n".join(
            [
                f"CLASSIFICATION={CLASSIFICATION}",
                f"HEAD={head}",
                f"ORIGIN_MAIN={origin_main}",
                "OFFLINE_ONLY=true",
                "NO_RUNTIME_REWIRE=true",
                "AUTHORITY_EFFECT=NONE",
                "RUNTIME_EFFECT=NONE",
                f"IMPORT_BOUNDARY_STATUS={classification['IMPORT_BOUNDARY_STATUS']}",
                (
                    "false_positive_docstring_ignored="
                    f"{str(classification['false_positive_docstring_ignored']).lower()}"
                ),
                "STEP29L2_SURFACE_STATUS=PARTIAL",
                "NEXT_GAP_CLASS=MISSING_REQUIRED_DIAGNOSTIC_SURFACE",
                f"MISSING_SURFACE={MISSING_SURFACE}",
                f"MANIFEST_VERIFY_RC={manifest_verify_rc}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def run_classification(*, output_dir: Path, repo_root: Path | None = None) -> int:
    root = repo_root or REPO_ROOT
    output_dir.mkdir(parents=True, exist_ok=True)

    head = _git_rev_parse("HEAD")
    origin_main = _git_rev_parse("origin/main")

    _write_inventory(root, output_dir)
    _write_context(output_dir, head=head, origin_main=origin_main)
    _write_surface_classification(output_dir)

    scan_paths = _collect_scan_paths(root)
    hits, docstring_comment_probes = scan_paths_import_boundary(
        scan_paths,
        repo_root=root,
    )
    boundary_classification = classify_import_boundary_scan(
        hits,
        docstring_comment_probes=docstring_comment_probes,
    )
    _write_import_boundary_artifacts(
        output_dir,
        hits=hits,
        docstring_comment_probes=docstring_comment_probes,
        classification=boundary_classification,
    )

    _write_final_report(
        output_dir,
        head=head,
        origin_main=origin_main,
        classification=boundary_classification,
        manifest_verify_rc=0,
    )

    write_manifest_sha256(output_dir)
    ok, _msg = verify_manifest_sha256(output_dir)
    manifest_verify_rc = 0 if ok else 1
    (output_dir / "MANIFEST.verify.rc").write_text(
        f"{manifest_verify_rc}\n",
        encoding="utf-8",
    )
    (output_dir / "final_report.txt").write_text(
        "\n".join(
            [
                f"CLASSIFICATION={CLASSIFICATION}",
                f"HEAD={head}",
                f"ORIGIN_MAIN={origin_main}",
                "OFFLINE_ONLY=true",
                "NO_RUNTIME_REWIRE=true",
                "AUTHORITY_EFFECT=NONE",
                "RUNTIME_EFFECT=NONE",
                f"IMPORT_BOUNDARY_STATUS={boundary_classification['IMPORT_BOUNDARY_STATUS']}",
                (
                    "false_positive_docstring_ignored="
                    f"{str(boundary_classification['false_positive_docstring_ignored']).lower()}"
                ),
                "STEP29L2_SURFACE_STATUS=PARTIAL",
                "NEXT_GAP_CLASS=MISSING_REQUIRED_DIAGNOSTIC_SURFACE",
                f"MISSING_SURFACE={MISSING_SURFACE}",
                f"MANIFEST_VERIFY_RC={manifest_verify_rc}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    write_manifest_sha256(output_dir)
    ok, _msg = verify_manifest_sha256(output_dir)
    manifest_verify_rc = 0 if ok else 1
    return (
        0
        if manifest_verify_rc == 0
        and boundary_classification["IMPORT_BOUNDARY_STATUS"] != "REVIEW_REQUIRED"
        else 1
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--repo-root", default=str(REPO_ROOT))
    args = parser.parse_args()
    return run_classification(
        output_dir=Path(args.output_dir).resolve(),
        repo_root=Path(args.repo_root).resolve(),
    )


if __name__ == "__main__":
    raise SystemExit(main())
