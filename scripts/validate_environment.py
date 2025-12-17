#!/usr/bin/env python3
"""
Environment Validation Script for Peak Trade

Validates that the development environment is correctly configured:
- Python version
- Required packages installed
- Config files valid
- Directory structure correct
"""

import sys
from pathlib import Path
from typing import List, Tuple


def check_python_version() -> Tuple[bool, str]:
    """Check if Python version is compatible."""
    version = sys.version_info
    if version.major == 3 and version.minor >= 10:
        return True, f"✅ Python {version.major}.{version.minor}.{version.micro}"
    return False, f"❌ Python {version.major}.{version.minor}.{version.micro} (requires 3.10+)"


def check_package_installed(package_name: str) -> Tuple[bool, str]:
    """Check if a Python package is installed."""
    try:
        __import__(package_name)
        return True, f"✅ {package_name}"
    except ImportError:
        return False, f"❌ {package_name} (not installed)"


def check_file_exists(file_path: Path) -> Tuple[bool, str]:
    """Check if a file exists."""
    if file_path.exists():
        return True, f"✅ {file_path}"
    return False, f"❌ {file_path} (missing)"


def check_directory_exists(dir_path: Path) -> Tuple[bool, str]:
    """Check if a directory exists."""
    if dir_path.is_dir():
        return True, f"✅ {dir_path}/"
    return False, f"❌ {dir_path}/ (missing)"


def validate_config_toml() -> Tuple[bool, str]:
    """Validate config.toml exists and is parseable."""
    config_path = Path("config.toml")
    if not config_path.exists():
        return False, "❌ config.toml (missing)"

    try:
        # Try tomllib first (Python 3.11+)
        try:
            import tomllib
            with open(config_path, "rb") as f:
                config = tomllib.load(f)
        except (ImportError, AttributeError):
            # Fall back to toml library
            import toml
            with open(config_path, "r", encoding="utf-8") as f:
                config = toml.load(f)

        # Check for required sections
        required_sections = ["environment", "risk", "backtest"]
        missing = [s for s in required_sections if s not in config]

        if missing:
            return False, f"❌ config.toml (missing sections: {', '.join(missing)})"

        return True, "✅ config.toml (valid)"
    except Exception as e:
        return False, f"❌ config.toml (parse error: {e})"


def main():
    """Run all validation checks."""
    print("🔍 Peak Trade Environment Validation")
    print("=" * 60)
    print()

    checks: List[Tuple[str, Tuple[bool, str]]] = []

    # Python version check
    print("📦 Python Environment:")
    result = check_python_version()
    checks.append(("Python Version", result))
    print(f"  {result[1]}")

    # Core packages
    print()
    print("📚 Core Dependencies:")
    core_packages = ["numpy", "pandas", "pydantic", "toml", "ccxt"]
    for package in core_packages:
        result = check_package_installed(package)
        checks.append((f"Package: {package}", result))
        print(f"  {result[1]}")

    # Dev packages
    print()
    print("🛠️  Development Tools:")
    dev_packages = ["pytest", "ruff", "mypy", "bandit"]
    for package in dev_packages:
        result = check_package_installed(package)
        checks.append((f"Dev Package: {package}", result))
        print(f"  {result[1]}")

    # Config files
    print()
    print("⚙️  Configuration Files:")
    config_files = [
        Path("config.toml"),
        Path("pyproject.toml"),
        Path("pytest.ini"),
        Path("requirements.txt"),
    ]
    for file_path in config_files:
        result = check_file_exists(file_path)
        checks.append((f"File: {file_path}", result))
        print(f"  {result[1]}")

    # Validate config.toml content
    result = validate_config_toml()
    checks.append(("Config Validation", result))
    print(f"  {result[1]}")

    # Directory structure
    print()
    print("📁 Directory Structure:")
    required_dirs = [
        Path("src"),
        Path("src/core"),
        Path("tests"),
        Path("docs"),
        Path("scripts"),
    ]
    for dir_path in required_dirs:
        result = check_directory_exists(dir_path)
        checks.append((f"Directory: {dir_path}", result))
        print(f"  {result[1]}")

    # Apple Silicon detection (if on macOS)
    print()
    print("🍎 Platform Detection:")
    import platform
    system = platform.system()
    machine = platform.machine()
    print(f"  System: {system}")
    print(f"  Architecture: {machine}")
    if system == "Darwin" and machine == "arm64":
        print("  ✅ Apple Silicon (M2/M3) detected")
    elif system == "Darwin":
        print("  ⚠️  macOS detected but not Apple Silicon")
    else:
        print(f"  ℹ️  Running on {system}")

    # Summary
    print()
    print("=" * 60)
    passed = sum(1 for _, (success, _) in checks if success)
    total = len(checks)
    print(f"📊 Results: {passed}/{total} checks passed")
    print()

    if passed == total:
        print("✅ Environment validation successful!")
        print("   Your development environment is ready.")
        return 0
    else:
        print("⚠️  Some validation checks failed.")
        print("   Review the issues above and install missing dependencies.")
        print()
        print("💡 Quick fixes:")
        print("   - Install dev dependencies: pip install -r requirements-dev.txt")
        print("   - Run macOS setup: bash scripts/setup_macos.sh")
        return 1


if __name__ == "__main__":
    sys.exit(main())
