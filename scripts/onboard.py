#!/usr/bin/env python3
"""
Interactive onboarding script for new developers.

Sets up:
- Python environment
- Dependencies
- Pre-commit hooks
- Configuration files
- IDE settings
"""

import subprocess
import sys
from pathlib import Path
import platform
import json


def print_header(text: str):
    """Print section header."""
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}\n")


def run(cmd: str, description: str, check: bool = True):
    """Run command with description."""
    print(f"⚙️  {description}...")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if check and result.returncode != 0:
        print(f"❌ Failed: {result.stderr}")
        if "--dry-run" not in sys.argv:
            sys.exit(1)
    print(f"✅ Done")
    return result


def main():
    """Run onboarding process."""
    dry_run = "--dry-run" in sys.argv

    print_header("Welcome to Peak Trade! 🚀")
    print("This script will set up your development environment.")

    if dry_run:
        print("⚠️  DRY RUN MODE - No changes will be made\n")

    # Detect system
    system = platform.system()
    is_apple_silicon = system == "Darwin" and platform.machine() == "arm64"

    if is_apple_silicon:
        print("✅ Detected Apple Silicon (M2/M3)")
    else:
        print(f"✅ Detected {system} {platform.machine()}")

    # 1. Python environment
    print_header("Step 1: Python Environment")
    result = subprocess.run(
        ["python", "--version"], capture_output=True, text=True
    )
    python_version = result.stdout.strip()
    print(f"Python version: {python_version}")

    if not dry_run and input("\nCreate virtual environment? (y/n): ").lower() == "y":
        run("python -m venv venv", "Creating virtual environment")
        activate_cmd = (
            "source venv/bin/activate" if system != "Windows" else "venv\\Scripts\\activate"
        )
        print(f"\n💡 Activate with: {activate_cmd}")

    # 2. Install dependencies
    print_header("Step 2: Dependencies")
    if not dry_run:
        run("python -m pip install --upgrade pip", "Upgrading pip")
        run("pip install -r requirements.txt", "Installing Peak Trade dependencies")
        run(
            "pip install pytest pytest-cov ruff mypy bandit",
            "Installing development tools",
        )

    # 3. Pre-commit hooks
    print_header("Step 3: Pre-commit Hooks")
    if not dry_run:
        # Check if pre-commit is installed
        result = subprocess.run(
            ["pre-commit", "--version"], capture_output=True, text=True
        )
        if result.returncode != 0:
            run("pip install pre-commit", "Installing pre-commit")

        run("pre-commit install", "Installing pre-commit hooks")
        run(
            "pre-commit install --hook-type commit-msg",
            "Installing commit-msg hook",
            check=False,
        )

    # 4. Configuration
    print_header("Step 4: Configuration")
    config_file = Path("config.toml")
    if not config_file.exists() and not dry_run:
        example_file = Path("config.toml.example")
        if example_file.exists():
            run("cp config.toml.example config.toml", "Creating config.toml")
            print("💡 Edit config.toml to customize settings")
        else:
            print("ℹ️  config.toml already exists")

    # 5. IDE setup
    print_header("Step 5: IDE Setup")
    if not dry_run and input("\nConfigure VSCode? (y/n): ").lower() == "y":
        vscode_dir = Path(".vscode")
        vscode_dir.mkdir(exist_ok=True)

        settings = {
            "python.linting.enabled": True,
            "python.linting.ruffEnabled": True,
            "python.formatting.provider": "none",
            "[python]": {"editor.defaultFormatter": "charliermarsh.ruff"},
            "editor.formatOnSave": True,
            "editor.codeActionsOnSave": {"source.organizeImports": "explicit"},
            "python.testing.pytestEnabled": True,
            "python.testing.unittestEnabled": False,
        }

        settings_file = vscode_dir / "settings.json"
        with open(settings_file, "w") as f:
            json.dump(settings, f, indent=2)

        print("✅ VSCode settings configured")

    # 6. Verify installation
    print_header("Step 6: Verification")
    if not dry_run:
        print("Running basic tests...")
        result = run(
            "pytest tests/test_basics.py -v",
            "Running test suite",
            check=False,
        )
        if result.returncode == 0:
            print("✅ All tests passed")
        else:
            print("⚠️  Some tests failed - this may be expected for new setups")

    # Done!
    print_header("Setup Complete! 🎉")
    print("You're ready to start developing!\n")
    print("Next steps:")
    print("  1. Activate virtual environment:")
    activate_cmd = (
        "source venv/bin/activate" if system != "Windows" else "venv\\Scripts\\activate"
    )
    print(f"     {activate_cmd}")
    print("  2. Read the documentation: docs/")
    print("  3. Run tests: pytest tests/")
    print("  4. Try code review: python scripts/code_review.py")
    print("\n📚 Documentation: https://rauterfrank-ui.github.io/Peak_Trade")
    print("🐛 Issues: https://github.com/rauterfrank-ui/Peak_Trade/issues")
    print("\nHappy coding! 💻")


if __name__ == "__main__":
    main()
