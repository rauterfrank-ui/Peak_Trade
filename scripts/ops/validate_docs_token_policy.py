#!/usr/bin/env python3
"""
Docs Token Policy Gate - Enforce encoding policy for illustrative paths in Markdown.

This script scans Markdown files for inline-code tokens containing '/' and enforces
the policy that illustrative (non-existent) paths must use &#47; encoding to prevent
docs-reference-targets-gate false positives.

Exit codes:
  0 - All checks passed
  1 - Violations found
  2 - Script error
"""

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Dict, Set, Optional
from enum import Enum


class TokenType(Enum):
    """Classification of inline-code tokens containing '/'."""

    REAL_REPO_TARGET = "REAL_REPO_TARGET"  # Exists in repo
    ILLUSTRATIVE = "ILLUSTRATIVE"  # Looks like path but doesn't exist
    COMMAND = "COMMAND"  # Shell command
    URL = "URL"  # HTTP/HTTPS URL
    LOCAL_PATH = "LOCAL_PATH"  # Absolute or relative with ../ ./
    BRANCH_NAME = "BRANCH_NAME"  # Git branch name pattern
    ENCODED = "ENCODED"  # Already uses &#47; encoding
    OTHER = "OTHER"  # Doesn't match known patterns


@dataclass
class TokenViolation:
    """A violation of the docs token policy."""

    file: str
    line: int
    token: str
    token_type: str
    message: str
    fix_suggestion: str


@dataclass
class ScanResult:
    """Result of scanning a file."""

    file: str
    total_tokens: int
    violations: List[TokenViolation]
    passed: bool


class DocsTokenPolicyValidator:
    """Validates inline-code tokens in Markdown files."""

    # Regex to find inline-code tokens (single backticks only)
    INLINE_CODE_PATTERN = re.compile(r"`([^`\n]+?)`")

    # Patterns for classification
    URL_PATTERN = re.compile(r"^https?://")
    ENCODED_PATTERN = re.compile(r"&#47;")
    COMMAND_PREFIXES = (
        "python ",
        "python3 ",
        "python3.11 ",
        "python3.10 ",
        "python3.9 ",
        "git ",
        "gh ",
        "uv ",
        "make ",
        "bash ",
        "sh ",
        "cd ",
        "ls ",
        "cat ",
        "grep ",
        "rg ",
        "find ",
        "sed ",
        "awk ",
        "./run_",
        "docker ",
        "npm ",
        "yarn ",
        "pip ",
    )
    LOCAL_PATH_PATTERN = re.compile(r"^(\.\./|\.\/|~/|/[A-Za-z_/])")
    BRANCH_NAME_PATTERN = re.compile(r"^[A-Za-z0-9._-]+/[A-Za-z0-9._-]+$")

    # Known git branch prefixes
    KNOWN_BRANCH_PREFIXES = {
        "feature",
        "feat",
        "fix",
        "bugfix",
        "hotfix",
        "release",
        "docs",
        "ci",
        "chore",
        "refactor",
        "test",
        "tests",
        "build",
        "perf",
        "ops",
    }

    # File extensions that suggest repo paths
    REPO_PATH_EXTENSIONS = (
        ".py",
        ".toml",
        ".yml",
        ".yaml",
        ".md",
        ".txt",
        ".json",
        ".sh",
        ".sql",
        ".js",
        ".ts",
        ".tsx",
        ".jsx",
        ".css",
        ".html",
        ".xml",
        ".csv",
        ".log",
    )

    def __init__(self, repo_root: Path, allowlist_path: Optional[Path] = None):
        self.repo_root = repo_root
        self.allowlist = self._load_allowlist(allowlist_path)

    def _load_allowlist(self, allowlist_path: Optional[Path]) -> Set[str]:
        """Load allowlist of tokens to skip."""
        if not allowlist_path or not allowlist_path.exists():
            return set()

        allowlist = set()
        with open(allowlist_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    allowlist.add(line)
        return allowlist

    def _is_real_repo_target(self, token: str) -> bool:
        """Check if token corresponds to a real file in the repo."""
        # Strip common prefixes
        path_candidate = token
        for prefix in self.COMMAND_PREFIXES:
            if token.startswith(prefix):
                parts = token.split()
                if len(parts) > 1:
                    path_candidate = parts[1]
                    break

        # Check if it exists
        candidate_path = self.repo_root / path_candidate
        return candidate_path.exists()

    def _classify_token(self, token: str) -> TokenType:
        """Classify a token containing '/'."""
        token_lower = token.lower()

        # Already encoded?
        if self.ENCODED_PATTERN.search(token):
            return TokenType.ENCODED

        # URL?
        if self.URL_PATTERN.search(token):
            return TokenType.URL

        # Command?
        if any(token.startswith(prefix) for prefix in self.COMMAND_PREFIXES):
            return TokenType.COMMAND

        # Local path pattern?
        if self.LOCAL_PATH_PATTERN.match(token):
            return TokenType.LOCAL_PATH

        # Branch name pattern?
        if self.BRANCH_NAME_PATTERN.match(token) and not any(
            token.endswith(ext) for ext in self.REPO_PATH_EXTENSIONS
        ):
            # Check if first segment is a known branch prefix
            first_segment = token.split("/")[0].lower()
            if first_segment in self.KNOWN_BRANCH_PREFIXES:
                return TokenType.BRANCH_NAME

        # Check if it's a real repo target
        if self._is_real_repo_target(token):
            return TokenType.REAL_REPO_TARGET

        # Looks like a path with extension?
        if any(token.endswith(ext) for ext in self.REPO_PATH_EXTENSIONS) or "/" in token:
            return TokenType.ILLUSTRATIVE

        return TokenType.OTHER

    def _should_require_encoding(self, token: str, token_type: TokenType) -> bool:
        """Determine if a token should require &#47; encoding."""
        # Skip if in allowlist
        if token in self.allowlist:
            return False

        # Only enforce on ILLUSTRATIVE type
        # BRANCH_NAME is allowed (no encoding required)
        if token_type == TokenType.ILLUSTRATIVE:
            return True

        return False

    def scan_file(self, file_path: Path) -> ScanResult:
        """Scan a single Markdown file for token policy violations."""
        violations = []

        try:
            content = file_path.read_text(encoding="utf-8")
        except Exception as e:
            return ScanResult(
                file=str(file_path.relative_to(self.repo_root)),
                total_tokens=0,
                violations=[
                    TokenViolation(
                        file=str(file_path.relative_to(self.repo_root)),
                        line=0,
                        token="",
                        token_type="ERROR",
                        message=f"Failed to read file: {e}",
                        fix_suggestion="",
                    )
                ],
                passed=False,
            )

        lines = content.split("\n")
        total_tokens = 0
        in_code_block = False

        for line_num, line in enumerate(lines, 1):
            # Track fenced code blocks (ignore content inside)
            if line.strip().startswith("```"):
                in_code_block = not in_code_block
                continue

            if in_code_block:
                continue

            # Find all inline-code tokens
            for match in self.INLINE_CODE_PATTERN.finditer(line):
                token = match.group(1)

                # Only check tokens containing '/'
                if "/" not in token:
                    continue

                total_tokens += 1
                token_type = self._classify_token(token)

                if self._should_require_encoding(token, token_type):
                    encoded_token = token.replace("/", "&#47;")
                    violations.append(
                        TokenViolation(
                            file=str(file_path.relative_to(self.repo_root)),
                            line=line_num,
                            token=token,
                            token_type=token_type.value,
                            message=f"Illustrative path token must use &#47; encoding",
                            fix_suggestion=f"Replace `{token}` with `{encoded_token}`",
                        )
                    )

        return ScanResult(
            file=str(file_path.relative_to(self.repo_root)),
            total_tokens=total_tokens,
            violations=violations,
            passed=len(violations) == 0,
        )

    def get_changed_markdown_files(self, base_ref: str = "origin/main") -> List[Path]:
        """Get list of changed Markdown files in current branch."""
        try:
            # Get merge base
            merge_base = subprocess.check_output(
                ["git", "merge-base", "HEAD", base_ref], cwd=self.repo_root, text=True
            ).strip()

            # Get changed files
            changed_files = (
                subprocess.check_output(
                    ["git", "diff", "--name-only", "--diff-filter=d", merge_base, "HEAD"],
                    cwd=self.repo_root,
                    text=True,
                )
                .strip()
                .split("\n")
            )

            # Filter for .md files
            md_files = [
                self.repo_root / f
                for f in changed_files
                if f and f.endswith(".md") and (self.repo_root / f).exists()
            ]

            return md_files
        except subprocess.CalledProcessError as e:
            print(f"Error detecting changed files: {e}", file=sys.stderr)
            return []

    def get_all_markdown_files(self) -> List[Path]:
        """
        Get all Markdown files in the repository.

        Hardening note:
        Prefer git-tracked files to avoid scanning virtualenvs, worktrees, and other
        untracked/ignored directories that may exist in the workspace.
        """
        try:
            out = subprocess.check_output(
                ["git", "ls-files", "*.md"], cwd=self.repo_root, text=True
            ).strip()
        except subprocess.CalledProcessError:
            out = ""

        if out:
            return [self.repo_root / p for p in out.splitlines() if p.strip()]

        # Fallback (should be rare): filesystem walk
        return list(self.repo_root.rglob("*.md"))

    def get_tracked_markdown_files(self, pathspec: str) -> List[Path]:
        """Get git-tracked Markdown files matching a pathspec (e.g. 'docs/**/*.md')."""
        try:
            out = subprocess.check_output(
                ["git", "ls-files", pathspec], cwd=self.repo_root, text=True
            ).strip()
        except subprocess.CalledProcessError:
            out = ""
        if not out:
            return []
        return [self.repo_root / p for p in out.splitlines() if p.strip()]


def main():
    parser = argparse.ArgumentParser(
        description="Validate docs token policy for inline-code tokens in Markdown files.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Check changed files (default)
  %(prog)s

  # Check all Markdown files
  %(prog)s --all

  # Check changed files against specific base
  %(prog)s --base origin/develop

  # Output JSON report
  %(prog)s --json report.json
""",
    )

    parser.add_argument(
        "--changed",
        action="store_true",
        default=False,
        help="Check only changed .md files (default if no other mode specified)",
    )

    parser.add_argument("--all", action="store_true", help="Check all .md files in repository")
    parser.add_argument(
        "--tracked-docs",
        action="store_true",
        help="Check git-tracked Markdown files under docs/ only (docs/**.md)",
    )

    parser.add_argument(
        "--base", default="origin/main", help="Base ref for change detection (default: origin/main)"
    )

    parser.add_argument("--json", metavar="FILE", help="Write JSON report to file")

    parser.add_argument(
        "--allowlist",
        type=Path,
        help="Path to allowlist file (default: scripts/ops/docs_token_policy_allowlist.txt)",
    )

    args = parser.parse_args()

    # Find repo root
    try:
        repo_root = Path(
            subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip()
        )
    except subprocess.CalledProcessError:
        print("Error: Not in a git repository", file=sys.stderr)
        return 2

    # Default allowlist path
    if not args.allowlist:
        args.allowlist = repo_root / "scripts" / "ops" / "docs_token_policy_allowlist.txt"

    # Initialize validator
    validator = DocsTokenPolicyValidator(repo_root, args.allowlist)

    # Determine which files to check
    if args.tracked_docs:
        files_to_check = validator.get_tracked_markdown_files("docs/**/*.md")
        mode = "tracked docs files (docs/**/*.md)"
    elif args.all:
        files_to_check = validator.get_all_markdown_files()
        mode = "all files"
    else:
        # Default to --changed mode
        files_to_check = validator.get_changed_markdown_files(args.base)
        mode = f"changed files (base: {args.base})"

    if not files_to_check:
        print(f"✅ No Markdown files to check ({mode})")
        return 0

    print(f"🔍 Scanning {len(files_to_check)} Markdown file(s) ({mode})...")
    print()

    # Scan all files
    results = []
    total_violations = 0

    for file_path in sorted(files_to_check):
        result = validator.scan_file(file_path)
        results.append(result)

        if not result.passed:
            total_violations += len(result.violations)

    # Print results
    files_with_violations = [r for r in results if not r.passed]

    if files_with_violations:
        print(f"❌ Found {total_violations} violation(s) in {len(files_with_violations)} file(s):")
        print()

        for result in files_with_violations:
            print(f"📄 {result.file}")
            for v in result.violations:
                print(f"  Line {v.line}: `{v.token}` ({v.token_type})")
                print(f"    → {v.message}")
                print(f"    💡 {v.fix_suggestion}")
            print()
    else:
        print(f"✅ All checks passed! ({len(results)} files scanned)")

    # Write JSON report if requested
    if args.json:
        report = {
            "mode": mode,
            "files_scanned": len(results),
            "files_with_violations": len(files_with_violations),
            "total_violations": total_violations,
            "results": [
                {
                    "file": r.file,
                    "total_tokens": r.total_tokens,
                    "passed": r.passed,
                    "violations": [asdict(v) for v in r.violations],
                }
                for r in results
            ],
        }

        json_path = Path(args.json)
        json_path.write_text(json.dumps(report, indent=2))
        print(f"📊 JSON report written to: {json_path}")

    # Exit with appropriate code
    return 0 if total_violations == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
