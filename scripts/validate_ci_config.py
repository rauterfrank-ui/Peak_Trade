#!/usr/bin/env python3
"""
Peak_Trade CI/CD Config Validator
==================================

Validiert GitHub Actions Workflow-Konfigurationen und TestHealth-Setup.

Usage:
    python scripts/validate_ci_config.py

Stand: Dezember 2024
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def validate_yaml_syntax(yaml_path: Path) -> tuple[bool, str]:
    """Validiert YAML-Syntax."""
    try:
        import yaml

        with open(yaml_path, "r") as f:
            yaml.safe_load(f)
        return True, f"✅ YAML-Syntax OK: {yaml_path.name}"
    except ImportError:
        return True, f"⚠️ PyYAML nicht installiert, Syntax-Check übersprungen"
    except yaml.YAMLError as e:
        return False, f"❌ YAML-Syntax-Fehler in {yaml_path.name}:\n{e}"
    except Exception as e:
        return False, f"❌ Fehler beim Lesen von {yaml_path.name}: {e}"


def validate_workflow_jobs(yaml_path: Path) -> tuple[bool, list[str]]:
    """Validiert Workflow-Jobs."""
    messages = []
    try:
        import yaml

        with open(yaml_path, "r") as f:
            config = yaml.safe_load(f)

        if "jobs" not in config:
            return False, ["❌ Keine 'jobs' in Workflow gefunden"]

        jobs = config["jobs"]
        job_names = list(jobs.keys())
        messages.append(f"✅ {len(jobs)} Jobs gefunden: {', '.join(job_names)}")

        # Check required jobs
        required_jobs = ["daily-health-check", "weekly-health-check", "manual-health-check"]
        for job in required_jobs:
            if job in jobs:
                messages.append(f"  ✅ Job '{job}' vorhanden")
            else:
                messages.append(f"  ⚠️ Job '{job}' fehlt (optional)")

        return True, messages
    except ImportError:
        return True, ["⚠️ PyYAML nicht installiert, Job-Validation übersprungen"]
    except Exception as e:
        return False, [f"❌ Fehler bei Job-Validation: {e}"]


def validate_test_health_config() -> tuple[bool, list[str]]:
    """Validiert TestHealth-Konfiguration."""
    messages = []

    # Check config file
    config_path = PROJECT_ROOT / "config" / "test_health_profiles.toml"
    if not config_path.exists():
        return False, ["❌ config/test_health_profiles.toml nicht gefunden"]
    messages.append(f"✅ Config gefunden: {config_path.relative_to(PROJECT_ROOT)}")

    # Check runner module
    runner_path = PROJECT_ROOT / "src" / "ops" / "test_health_runner.py"
    if not runner_path.exists():
        return False, ["❌ src/ops/test_health_runner.py nicht gefunden"]
    messages.append(f"✅ Runner gefunden: {runner_path.relative_to(PROJECT_ROOT)}")

    # Check CLI script
    cli_path = PROJECT_ROOT / "scripts" / "run_test_health_profile.py"
    if not cli_path.exists():
        return False, ["❌ scripts/run_test_health_profile.py nicht gefunden"]
    messages.append(f"✅ CLI gefunden: {cli_path.relative_to(PROJECT_ROOT)}")

    # Check history module
    history_path = PROJECT_ROOT / "src" / "ops" / "test_health_history.py"
    if history_path.exists():
        messages.append(f"✅ History-Modul gefunden: {history_path.relative_to(PROJECT_ROOT)}")
    else:
        messages.append(f"⚠️ History-Modul nicht gefunden (optional)")

    return True, messages


def validate_profile_definitions() -> tuple[bool, list[str]]:
    """Validiert Profil-Definitionen in TOML."""
    messages = []

    try:
        # Try tomllib (Python 3.11+) or tomli
        try:
            import tomllib
        except ImportError:
            import tomli as tomllib

        config_path = PROJECT_ROOT / "config" / "test_health_profiles.toml"
        with open(config_path, "rb") as f:
            config = tomllib.load(f)

        if "profiles" not in config:
            return False, ["❌ Keine 'profiles' in Config gefunden"]

        profiles = config["profiles"]
        profile_names = list(profiles.keys())
        messages.append(f"✅ {len(profiles)} Profile gefunden: {', '.join(profile_names)}")

        # Check required profiles
        required_profiles = ["daily_quick", "weekly_core"]
        for profile in required_profiles:
            if profile in profiles:
                checks = profiles[profile].get("checks", [])
                messages.append(f"  ✅ Profil '{profile}': {len(checks)} Checks")
            else:
                messages.append(f"  ⚠️ Profil '{profile}' fehlt (empfohlen)")

        # Check optional profiles
        optional_profiles = ["full_suite", "r_and_d_experimental", "demo_simple"]
        for profile in optional_profiles:
            if profile in profiles:
                checks = profiles[profile].get("checks", [])
                messages.append(f"  ✅ Profil '{profile}': {len(checks)} Checks (optional)")

        return True, messages

    except ImportError:
        return True, ["⚠️ tomllib/tomli nicht installiert, Profil-Validation übersprungen"]
    except Exception as e:
        return False, [f"❌ Fehler bei Profil-Validation: {e}"]


def validate_github_actions_structure() -> tuple[bool, list[str]]:
    """Validiert GitHub Actions Verzeichnis-Struktur."""
    messages = []

    # Check .github directory
    github_dir = PROJECT_ROOT / ".github"
    if not github_dir.exists():
        return False, ["❌ .github/ Verzeichnis nicht gefunden"]
    messages.append(f"✅ .github/ gefunden")

    # Check workflows directory
    workflows_dir = github_dir / "workflows"
    if not workflows_dir.exists():
        return False, ["❌ .github/workflows/ nicht gefunden"]
    messages.append(f"✅ .github/workflows/ gefunden")

    # Check test_health.yml
    test_health_yml = workflows_dir / "test_health.yml"
    if not test_health_yml.exists():
        return False, ["❌ .github/workflows/test_health.yml nicht gefunden"]
    messages.append(f"✅ test_health.yml gefunden")

    # List all workflows
    workflows = list(workflows_dir.glob("*.yml")) + list(workflows_dir.glob("*.yaml"))
    messages.append(
        f"✅ {len(workflows)} Workflow(s) gesamt: {', '.join(w.name for w in workflows)}"
    )

    return True, messages


def main() -> int:
    """Hauptfunktion."""
    print("=" * 70)
    print("🔍 Peak_Trade CI/CD Config Validator")
    print("=" * 70)
    print()

    all_passed = True

    # 1. GitHub Actions Structure
    print("📁 GitHub Actions Struktur")
    print("-" * 70)
    passed, messages = validate_github_actions_structure()
    for msg in messages:
        print(msg)
    if not passed:
        all_passed = False
    print()

    # 2. YAML Syntax
    print("📝 YAML-Syntax Validation")
    print("-" * 70)
    test_health_yml = PROJECT_ROOT / ".github" / "workflows" / "test_health.yml"
    if test_health_yml.exists():
        passed, msg = validate_yaml_syntax(test_health_yml)
        print(msg)
        if not passed:
            all_passed = False
    else:
        print("⚠️ test_health.yml nicht gefunden, YAML-Check übersprungen")
    print()

    # 3. Workflow Jobs
    print("🔧 Workflow Jobs Validation")
    print("-" * 70)
    if test_health_yml.exists():
        passed, messages = validate_workflow_jobs(test_health_yml)
        for msg in messages:
            print(msg)
        if not passed:
            all_passed = False
    else:
        print("⚠️ test_health.yml nicht gefunden, Job-Check übersprungen")
    print()

    # 4. TestHealth Config
    print("⚙️ TestHealth Config Validation")
    print("-" * 70)
    passed, messages = validate_test_health_config()
    for msg in messages:
        print(msg)
    if not passed:
        all_passed = False
    print()

    # 5. Profile Definitions
    print("📊 Profile Definitions Validation")
    print("-" * 70)
    passed, messages = validate_profile_definitions()
    for msg in messages:
        print(msg)
    if not passed:
        all_passed = False
    print()

    # Summary
    print("=" * 70)
    if all_passed:
        print("✅ Alle Validierungen erfolgreich!")
        print()
        print("🚀 Nächste Schritte:")
        print("   1. git add .github/workflows/test_health.yml")
        print("   2. git commit -m 'ci: add test health automation workflow'")
        print("   3. git push origin main")
        print("   4. Teste Manual Run in GitHub Actions UI")
        return 0
    else:
        print("❌ Einige Validierungen fehlgeschlagen!")
        print()
        print("Bitte behebe die Fehler und führe das Script erneut aus.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
