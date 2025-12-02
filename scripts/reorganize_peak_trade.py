#!/usr/bin/env python3
"""
Reorganization script for Peak_Trade project structure.
Creates a clean directory structure and moves files to their designated locations.
"""

import argparse
import shutil
from pathlib import Path
from typing import List, Tuple


class ReorganizationReport:
    def __init__(self):
        self.moved: List[Tuple[str, str]] = []
        self.skipped: List[Tuple[str, str]] = []
        self.created_dirs: List[str] = []
        self.created_files: List[str] = []

    def add_moved(self, source: str, dest: str):
        self.moved.append((source, dest))

    def add_skipped(self, source: str, reason: str):
        self.skipped.append((source, reason))

    def add_created_dir(self, path: str):
        self.created_dirs.append(path)

    def add_created_file(self, path: str):
        self.created_files.append(path)

    def print_summary(self):
        print("\n" + "=" * 80)
        print("REORGANIZATION SUMMARY")
        print("=" * 80)

        if self.created_dirs:
            print(f"\n✓ Created {len(self.created_dirs)} directories:")
            for dir_path in self.created_dirs:
                print(f"  • {dir_path}")

        if self.moved:
            print(f"\n✓ Moved {len(self.moved)} files:")
            for source, dest in self.moved:
                print(f"  • {source} → {dest}")

        if self.created_files:
            print(f"\n✓ Created {len(self.created_files)} new files:")
            for file_path in self.created_files:
                print(f"  • {file_path}")

        if self.skipped:
            print(f"\n⚠ Skipped {len(self.skipped)} operations:")
            for source, reason in self.skipped:
                print(f"  • {source}: {reason}")

        print("\n" + "=" * 80)
        print("Reorganization complete!")
        print("=" * 80 + "\n")


def ensure_dir(path: Path, report: ReorganizationReport, dry_run: bool = False) -> None:
    """Create directory if it doesn't exist."""
    if not path.exists():
        if not dry_run:
            path.mkdir(parents=True, exist_ok=True)
        report.add_created_dir(str(path))


def move_file(source: Path, dest: Path, report: ReorganizationReport, dry_run: bool = False) -> None:
    """Move file from source to destination, with conflict handling."""
    if not source.exists():
        report.add_skipped(str(source), "source file does not exist")
        return

    if dest.exists():
        report.add_skipped(str(source), f"destination already exists: {dest}")
        return

    if not dry_run:
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(source), str(dest))

    report.add_moved(str(source), str(dest))


def move_dir(source: Path, dest: Path, report: ReorganizationReport, dry_run: bool = False) -> None:
    """Move directory from source to destination."""
    if not source.exists():
        report.add_skipped(str(source), "source directory does not exist")
        return

    if dest.exists():
        report.add_skipped(str(source), f"destination already exists: {dest}")
        return

    if not dry_run:
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(source), str(dest))

    report.add_moved(str(source), str(dest))


def create_file_if_missing(path: Path, content: str, report: ReorganizationReport, dry_run: bool = False) -> None:
    """Create a file with given content if it doesn't exist."""
    if path.exists():
        report.add_skipped(str(path), "file already exists")
        return

    if not dry_run:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    report.add_created_file(str(path))


def reorganize_peak_trade(project_root: Path, dry_run: bool = False) -> None:
    """Main reorganization function."""
    report = ReorganizationReport()

    if dry_run:
        print("\n*** DRY RUN MODE - No changes will be made ***\n")

    # Step 1: Create archive directory and move old content
    archive_dir = project_root / "archive"
    ensure_dir(archive_dir, report, dry_run)

    move_dir(project_root / "PeakTradeRepo", archive_dir / "PeakTradeRepo", report, dry_run)
    move_dir(project_root / "noch einordnen", archive_dir / "noch_einordnen", report, dry_run)
    move_file(project_root / "full_files_stand_02.12.2025", archive_dir / "full_files_stand_02.12.2025", report, dry_run)

    # Step 2: Create config directory and move config.toml
    config_dir = project_root / "config"
    ensure_dir(config_dir, report, dry_run)
    move_file(project_root / "config.toml", config_dir / "config.toml", report, dry_run)

    # Step 3: Create docs structure and move documentation files
    docs_dir = project_root / "docs"
    architecture_dir = docs_dir / "architecture"
    reports_dir = docs_dir / "reports"
    project_docs_dir = docs_dir / "project_docs"

    ensure_dir(docs_dir, report, dry_run)
    ensure_dir(architecture_dir, report, dry_run)
    ensure_dir(reports_dir, report, dry_run)
    ensure_dir(project_docs_dir, report, dry_run)

    # Move architecture files
    move_file(project_root / "architecture_diagram.png", architecture_dir / "architecture_diagram.png", report, dry_run)

    # Move report files
    move_file(project_root / "dashboard.html", reports_dir / "dashboard.html", report, dry_run)
    move_file(project_root / "peak_trade_documentation.pdf", reports_dir / "peak_trade_documentation.pdf", report, dry_run)
    move_file(project_root / "PeakTrade_enhanced.pdf", reports_dir / "PeakTrade_enhanced.pdf", report, dry_run)
    move_file(project_root / "peak_trade_documentation.html", reports_dir / "peak_trade_documentation.html", report, dry_run)

    # Step 4: Move and rename project markdown files
    move_file(project_root / "FINAL_SUMMARY.md", project_docs_dir / "FINAL_SUMMARY.md", report, dry_run)
    move_file(project_root / "CONFIG_SYSTEM.md", project_docs_dir / "CONFIG_SYSTEM.md", report, dry_run)
    move_file(project_root / "RISK_LIMITS_UPDATE.md", project_docs_dir / "RISK_LIMITS_UPDATE.md", report, dry_run)
    move_file(project_root / "NEXT_STEPS.md", project_docs_dir / "NEXT_STEPS.md", report, dry_run)
    move_file(project_root / "FILES_CHANGED.md", project_docs_dir / "FILES_CHANGED.md", report, dry_run)

    # Handle files with pattern matching for truncated names
    backtest_files = list(project_root.glob("BACKTEST_RI*GRATION.md"))
    if backtest_files:
        move_file(backtest_files[0], project_docs_dir / "BACKTEST_INTEGRATION.md", report, dry_run)
    else:
        move_file(project_root / "BACKTEST_INTEGRATION.md", project_docs_dir / "BACKTEST_INTEGRATION.md", report, dry_run)

    # Rename CLAUDE.MD to CLAUDE_NOTES.md
    move_file(project_root / "CLAUDE.MD", project_docs_dir / "CLAUDE_NOTES.md", report, dry_run)

    # Move Peak_Trade_Data_Layer_Doku.md if it exists
    move_file(project_root / "Peak_Trade_Data_Layer_Doku.md", project_docs_dir / "Peak_Trade_Data_Layer_Doku.md", report, dry_run)

    # Step 5: Create CHANGELOG.md and RISK_MANAGEMENT.md if they don't exist
    changelog_content = """# Changelog

This file consolidates changes and file status information.

## Sources
- Previously tracked in FILES_CHANGED.md
- Snapshot from full_files_stand_02.12.2025

## Changes
(To be filled in manually)
"""

    risk_management_content = """# Risk Management

Central documentation for risk management in Peak_Trade.

## Overview
(To be filled in manually)

## Risk Limits
(To be filled in manually)

## Related Documents
- RISK_LIMITS_UPDATE.md
"""

    create_file_if_missing(project_docs_dir / "CHANGELOG.md", changelog_content, report, dry_run)
    create_file_if_missing(project_docs_dir / "RISK_MANAGEMENT.md", risk_management_content, report, dry_run)

    # Step 6: Rename gitignore to .gitignore if needed
    if (project_root / "gitignore").exists():
        move_file(project_root / "gitignore", project_root / ".gitignore", report, dry_run)

    # Step 7: Move debug_signals.py to scripts
    scripts_dir = project_root / "scripts"
    ensure_dir(scripts_dir, report, dry_run)
    move_file(project_root / "debug_signals.py", scripts_dir / "debug_signals.py", report, dry_run)

    # Print summary
    report.print_summary()


def main():
    parser = argparse.ArgumentParser(
        description="Reorganize Peak_Trade project structure into a clean layout."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making actual changes"
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path(__file__).parent.parent,
        help="Path to the Peak_Trade project root (default: parent of scripts directory)"
    )

    args = parser.parse_args()

    project_root = args.project_root.resolve()

    if not project_root.exists():
        print(f"Error: Project root does not exist: {project_root}")
        return 1

    print(f"Project root: {project_root}")

    reorganize_peak_trade(project_root, args.dry_run)

    return 0


if __name__ == "__main__":
    exit(main())
