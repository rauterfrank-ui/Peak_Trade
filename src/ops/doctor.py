#!/usr/bin/env python3
"""
Peak_Trade Ops Inspector - Doctor Mode
========================================

Führt umfassende Repository-Gesundheitschecks durch und liefert
einen strukturierten Statusbericht.

Usage:
    python -m src.ops.doctor
    python -m src.ops.doctor --json
    python -m src.ops.doctor --check repo.git_root --check deps.uv_lock
"""

import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional


@dataclass
class Check:
    """Ein einzelner Diagnose-Check."""

    id: str
    severity: Literal["fail", "warn", "info"]
    status: Literal["ok", "warn", "fail", "skip"] = "skip"
    message: str = ""
    fix_hint: str = ""
    evidence: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "severity": self.severity,
            "status": self.status,
            "message": self.message,
            "fix_hint": self.fix_hint,
            "evidence": self.evidence,
        }


class DoctorReport:
    """Container für alle Checks und deren Ergebnisse."""

    def __init__(self):
        self.checks: List[Check] = []
        self.timestamp = datetime.utcnow().isoformat() + "Z"

    def add_check(self, check: Check):
        self.checks.append(check)

    def summary(self) -> Dict[str, int]:
        """Zählt Status über alle Checks."""
        counts = {"ok": 0, "warn": 0, "fail": 0, "skip": 0}
        for check in self.checks:
            counts[check.status] += 1
        return counts

    def to_dict(self) -> Dict[str, Any]:
        summary = self.summary()
        return {
            "tool": "ops_inspector",
            "mode": "doctor",
            "timestamp": self.timestamp,
            "summary": {
                "ok": summary["ok"],
                "warn": summary["warn"],
                "fail": summary["fail"],
            },
            "checks": [c.to_dict() for c in self.checks],
        }

    def exit_code(self) -> int:
        """Exit Code basierend auf Checks."""
        summary = self.summary()
        if summary["fail"] > 0:
            return 1
        if summary["warn"] > 0:
            return 2
        return 0


class Doctor:
    """Hauptklasse für alle Diagnose-Checks."""

    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        self.report = DoctorReport()

    def run_all_checks(self) -> DoctorReport:
        """Führt alle verfügbaren Checks aus."""
        self.check_git_root()
        self.check_git_status()
        self.check_uv_lock()
        self.check_requirements_sync()
        self.check_pyproject_toml()
        self.check_config_files()
        self.check_docs_registry()
        self.check_test_infrastructure()
        self.check_ci_files()
        return self.report

    def run_specific_checks(self, check_ids: List[str]) -> DoctorReport:
        """Führt nur spezifische Checks aus."""
        check_map = {
            "repo.git_root": self.check_git_root,
            "repo.git_status": self.check_git_status,
            "deps.uv_lock": self.check_uv_lock,
            "deps.requirements_sync": self.check_requirements_sync,
            "config.pyproject": self.check_pyproject_toml,
            "config.files": self.check_config_files,
            "docs.registry": self.check_docs_registry,
            "tests.infrastructure": self.check_test_infrastructure,
            "ci.files": self.check_ci_files,
        }

        for check_id in check_ids:
            if check_id in check_map:
                check_map[check_id]()
            else:
                self.report.add_check(
                    Check(
                        id=check_id,
                        severity="warn",
                        status="skip",
                        message=f"Unknown check: {check_id}",
                    )
                )

        return self.report

    # ─────────────────────────────────────────────────────────────────────────────
    # CHECK IMPLEMENTATIONS
    # ─────────────────────────────────────────────────────────────────────────────

    def check_git_root(self):
        """Prüft ob wir in einem Git-Repo sind."""
        check = Check(
            id="repo.git_root",
            severity="fail",
        )

        git_dir = self.repo_root / ".git"
        if git_dir.exists():
            check.status = "ok"
            check.message = f"Git repository root found: {self.repo_root}"
            check.evidence.append(str(git_dir))
        else:
            check.status = "fail"
            check.message = "Not a git repository"
            check.fix_hint = "Run: git init"

        self.report.add_check(check)

    def check_git_status(self):
        """Prüft Git-Status (uncommitted changes, etc.)."""
        check = Check(
            id="repo.git_status",
            severity="warn",
        )

        try:
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=self.repo_root,
                capture_output=True,
                text=True,
                timeout=5,
            )

            if result.returncode != 0:
                check.status = "skip"
                check.message = "Git status check failed"
                check.evidence.append(result.stderr.strip())
            elif result.stdout.strip():
                # Uncommitted changes
                lines = result.stdout.strip().split("\n")
                check.status = "warn"
                check.message = f"Uncommitted changes: {len(lines)} files"
                check.evidence.extend(lines[:10])  # Erste 10 Files
                if len(lines) > 10:
                    check.evidence.append(f"... and {len(lines) - 10} more")
                check.fix_hint = "Commit or stash changes: git commit -m '...' or git stash"
            else:
                check.status = "ok"
                check.message = "Working directory clean"

        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            check.status = "skip"
            check.message = f"Git status check failed: {e}"

        self.report.add_check(check)

    def check_uv_lock(self):
        """Prüft ob uv.lock existiert und aktuell ist."""
        check = Check(
            id="deps.uv_lock",
            severity="fail",
        )

        uv_lock = self.repo_root / "uv.lock"
        pyproject = self.repo_root / "pyproject.toml"

        if not uv_lock.exists():
            check.status = "fail"
            check.message = "uv.lock not found"
            check.fix_hint = "Run: uv lock"
            self.report.add_check(check)
            return

        if not pyproject.exists():
            check.status = "warn"
            check.message = "pyproject.toml not found (cannot compare)"
            self.report.add_check(check)
            return

        # Vergleiche Zeitstempel
        lock_mtime = uv_lock.stat().st_mtime
        pyproject_mtime = pyproject.stat().st_mtime

        if lock_mtime < pyproject_mtime:
            check.status = "warn"
            check.message = "uv.lock older than pyproject.toml"
            check.fix_hint = "Run: uv lock"
            check.evidence.append(f"uv.lock: {datetime.fromtimestamp(lock_mtime)}")
            check.evidence.append(f"pyproject.toml: {datetime.fromtimestamp(pyproject_mtime)}")
        else:
            check.status = "ok"
            check.message = "uv.lock up to date"

        self.report.add_check(check)

    def check_requirements_sync(self):
        """Prüft ob requirements.txt mit uv.lock synchronisiert ist."""
        check = Check(
            id="deps.requirements_sync",
            severity="warn",
        )

        requirements = self.repo_root / "requirements.txt"
        uv_lock = self.repo_root / "uv.lock"

        if not requirements.exists():
            check.status = "skip"
            check.message = "requirements.txt not found (optional)"
            self.report.add_check(check)
            return

        if not uv_lock.exists():
            check.status = "skip"
            check.message = "uv.lock not found (cannot compare)"
            self.report.add_check(check)
            return

        # Verwende das vorhandene Shell-Script falls verfügbar
        sync_checker = self.repo_root / "scripts" / "ops" / "check_requirements_synced_with_uv.sh"
        if sync_checker.exists():
            try:
                result = subprocess.run(
                    ["bash", str(sync_checker)],
                    cwd=self.repo_root,
                    capture_output=True,
                    text=True,
                    timeout=10,
                )

                if result.returncode == 0:
                    check.status = "ok"
                    check.message = "requirements.txt in sync with uv.lock"
                else:
                    check.status = "warn"
                    check.message = "requirements.txt out of sync"
                    check.fix_hint = "Run: uv export --no-dev > requirements.txt"
                    check.evidence.append(result.stdout.strip())

            except (subprocess.TimeoutExpired, FileNotFoundError) as e:
                check.status = "skip"
                check.message = f"Sync check failed: {e}"
        else:
            # Fallback: Vergleiche Zeitstempel
            req_mtime = requirements.stat().st_mtime
            lock_mtime = uv_lock.stat().st_mtime

            if req_mtime < lock_mtime:
                check.status = "warn"
                check.message = "requirements.txt older than uv.lock"
                check.fix_hint = "Run: uv export --no-dev > requirements.txt"
            else:
                check.status = "ok"
                check.message = "requirements.txt appears up to date"

        self.report.add_check(check)

    def check_pyproject_toml(self):
        """Prüft pyproject.toml auf valide Syntax."""
        check = Check(
            id="config.pyproject",
            severity="fail",
        )

        pyproject = self.repo_root / "pyproject.toml"

        if not pyproject.exists():
            check.status = "fail"
            check.message = "pyproject.toml not found"
            check.fix_hint = "Create pyproject.toml"
            self.report.add_check(check)
            return

        try:
            import tomllib
        except ImportError:
            try:
                import tomli as tomllib  # Python < 3.11
            except ImportError:
                check.status = "skip"
                check.message = "TOML parser not available (install tomli)"
                self.report.add_check(check)
                return

        try:
            with open(pyproject, "rb") as f:
                data = tomllib.load(f)

            # Prüfe wichtige Felder
            if "project" not in data:
                check.status = "warn"
                check.message = "pyproject.toml missing [project] section"
                check.fix_hint = "Add [project] section with name and version"
            elif "name" not in data["project"]:
                check.status = "warn"
                check.message = "pyproject.toml missing project.name"
            else:
                check.status = "ok"
                check.message = f"pyproject.toml valid (project: {data['project']['name']})"

        except Exception as e:
            check.status = "fail"
            check.message = f"pyproject.toml parse error: {e}"
            check.fix_hint = "Fix TOML syntax errors"

        self.report.add_check(check)

    def check_config_files(self):
        """Prüft wichtige Config-Dateien im config/-Verzeichnis."""
        check = Check(
            id="config.files",
            severity="warn",
        )

        config_dir = self.repo_root / "config"

        if not config_dir.exists():
            check.status = "skip"
            check.message = "config/ directory not found"
            self.report.add_check(check)
            return

        # Erwartete wichtige Configs
        expected = ["default.toml", "config.toml"]
        missing = []
        found = []

        for cfg in expected:
            if (config_dir / cfg).exists():
                found.append(cfg)
            else:
                missing.append(cfg)

        if missing:
            check.status = "warn"
            check.message = f"Missing config files: {', '.join(missing)}"
            check.fix_hint = f"Create missing configs in config/"
            check.evidence.extend([f"✗ {m}" for m in missing])
            check.evidence.extend([f"✓ {f}" for f in found])
        else:
            check.status = "ok"
            check.message = f"All expected config files present ({len(found)})"
            check.evidence.extend([f"✓ {f}" for f in found])

        self.report.add_check(check)

    def check_docs_registry(self):
        """Prüft ob README_REGISTRY.md existiert und aktuell ist."""
        check = Check(
            id="docs.registry",
            severity="info",
        )

        registry = self.repo_root / "README_REGISTRY.md"

        if not registry.exists():
            check.status = "warn"
            check.message = "README_REGISTRY.md not found"
            check.fix_hint = "Create README_REGISTRY.md to document all README files"
            self.report.add_check(check)
            return

        try:
            content = registry.read_text()
            # Zähle referenzierte README-Files
            readme_refs = re.findall(r"\b\w+_README\.md\b", content)

            if len(readme_refs) > 0:
                check.status = "ok"
                check.message = f"README_REGISTRY.md found ({len(readme_refs)} docs referenced)"
                check.evidence.append(f"Referenced: {len(readme_refs)} docs")
            else:
                check.status = "warn"
                check.message = "README_REGISTRY.md exists but appears empty"

        except Exception as e:
            check.status = "skip"
            check.message = f"Could not read README_REGISTRY.md: {e}"

        self.report.add_check(check)

    def check_test_infrastructure(self):
        """Prüft Test-Infrastruktur (pytest.ini, tests/)."""
        check = Check(
            id="tests.infrastructure",
            severity="warn",
        )

        pytest_ini = self.repo_root / "pytest.ini"
        tests_dir = self.repo_root / "tests"

        issues = []
        evidence = []

        if not pytest_ini.exists():
            issues.append("pytest.ini not found")
        else:
            evidence.append("✓ pytest.ini")

        if not tests_dir.exists():
            issues.append("tests/ directory not found")
        elif not tests_dir.is_dir():
            issues.append("tests/ is not a directory")
        else:
            # Zähle Test-Files
            test_files = list(tests_dir.rglob("test_*.py"))
            evidence.append(f"✓ tests/ ({len(test_files)} test files)")

        if issues:
            check.status = "warn"
            check.message = f"Test infrastructure issues: {', '.join(issues)}"
            check.fix_hint = "Set up pytest: pip install pytest && touch pytest.ini"
            check.evidence.extend(issues)
        else:
            check.status = "ok"
            check.message = "Test infrastructure OK"
            check.evidence.extend(evidence)

        self.report.add_check(check)

    def check_ci_files(self):
        """Prüft CI/CD-Konfiguration."""
        check = Check(
            id="ci.files",
            severity="info",
        )

        ci_files = [
            ".github/workflows",
            "Makefile",
            "policy_packs/ci.yml",
        ]

        found = []
        missing = []

        for ci_path in ci_files:
            full_path = self.repo_root / ci_path
            if full_path.exists():
                found.append(ci_path)
            else:
                missing.append(ci_path)

        if found:
            check.status = "ok"
            check.message = f"CI/CD infrastructure present ({len(found)} components)"
            check.evidence.extend([f"✓ {f}" for f in found])
            if missing:
                check.evidence.extend([f"✗ {m}" for m in missing])
        else:
            check.status = "warn"
            check.message = "No CI/CD infrastructure found"
            check.fix_hint = "Consider adding CI/CD (GitHub Actions, Makefile, etc.)"

        self.report.add_check(check)


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────


def print_report_human(report: DoctorReport):
    """Gibt den Report in human-readable Format aus."""
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("🏥 Peak_Trade Ops Inspector – Doctor Mode")
    print(f"⏰ {report.timestamp}")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print()

    summary = report.summary()
    print("📊 Summary:")
    print(f"   ✅ OK:   {summary['ok']}")
    print(f"   ⚠️  WARN: {summary['warn']}")
    print(f"   ❌ FAIL: {summary['fail']}")
    print(f"   ⏭️  SKIP: {summary['skip']}")
    print()

    print("🔍 Checks:")
    print()

    for check in report.checks:
        # Status icon
        icon = {
            "ok": "✅",
            "warn": "⚠️ ",
            "fail": "❌",
            "skip": "⏭️ ",
        }[check.status]

        print(f"{icon} [{check.id}] {check.message}")

        if check.fix_hint:
            print(f"   💡 Fix: {check.fix_hint}")

        if check.evidence:
            for ev in check.evidence[:5]:  # Max 5 Evidence-Lines
                print(f"      {ev}")
            if len(check.evidence) > 5:
                print(f"      ... and {len(check.evidence) - 5} more")

        print()

    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    if summary["fail"] > 0:
        print("❌ Doctor found critical issues!")
        return 1
    elif summary["warn"] > 0:
        print("⚠️  Doctor found warnings")
        return 2
    else:
        print("🎉 All checks passed!")
        return 0


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Peak_Trade Ops Inspector – Doctor Mode",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--json",
        action="store_true",
        help="Output in JSON format",
    )

    parser.add_argument(
        "--check",
        action="append",
        dest="checks",
        help="Run specific check(s) only (can be repeated)",
    )

    parser.add_argument(
        "--repo-root",
        type=Path,
        default=None,
        help="Repository root (default: auto-detect)",
    )

    args = parser.parse_args()

    # Auto-detect repo root
    if args.repo_root:
        repo_root = args.repo_root.resolve()
    else:
        # Start from current dir and search upwards for .git
        current = Path.cwd()
        while current != current.parent:
            if (current / ".git").exists():
                repo_root = current
                break
            current = current.parent
        else:
            # Fallback: use current dir
            repo_root = Path.cwd()

    doctor = Doctor(repo_root)

    if args.checks:
        report = doctor.run_specific_checks(args.checks)
    else:
        report = doctor.run_all_checks()

    if args.json:
        print(json.dumps(report.to_dict(), indent=2))
        sys.exit(report.exit_code())
    else:
        exit_code = print_report_human(report)
        sys.exit(exit_code)


if __name__ == "__main__":
    main()
