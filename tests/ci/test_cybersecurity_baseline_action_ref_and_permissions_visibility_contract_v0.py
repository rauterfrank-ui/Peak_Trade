"""Cybersecurity baseline: immutable Action SHA pins + top-level permissions.

Parses workflow YAML files as UTF-8 text only. Never dispatches workflows,
never calls GitHub APIs, never executes scripts, and never touches runtime,
scheduler, daemon, paper/shadow/testnet/live, broker/exchange, or order paths.

Fail-closed (CYBER_CI_SUPPLY_CHAIN_HARDENING_V1):
- every external `uses:` must be pinned to a full 40-hex commit SHA
- floating mutable refs (`@main` / `@master` / `@latest` / `@head`) are forbidden
- semantic / major-only tags without SHA are forbidden for external Actions
- local `./` actions and `docker://` refs are classified separately (not SHA-rewritten)
- every active workflow declares an explicit top-level `permissions:` mapping
- `permissions: write-all` is forbidden
- empty / malformed top-level permissions fail closed
"""

from __future__ import annotations

import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
WORKFLOW_ROOT = REPO_ROOT / ".github" / "workflows"
SECURITY_NOTES = REPO_ROOT / "SECURITY_NOTES.md"
CI_GHA_AUDIT_INDEX = (
    REPO_ROOT / "docs" / "ops" / "CI_GITHUB_ACTIONS_PERMISSIONS_SECRETS_ARTIFACTS_AUDIT_INDEX_V0.md"
)

USES_REF_RX = re.compile(r"^\s*uses:\s*([^\s#]+)", re.MULTILINE)
FLOATING_REF_RX = re.compile(r"@(?:main|master|latest|head)\s*$", re.IGNORECASE)
SHA_PIN_RX = re.compile(r"@[0-9a-f]{40}$", re.IGNORECASE)
TOP_LEVEL_PERMISSIONS_RX = re.compile(r"^permissions\s*:", re.MULTILINE)
WRITE_ALL_RX = re.compile(r"^permissions\s*:\s*write-all\s*$", re.MULTILINE | re.IGNORECASE)
PULL_REQUEST_TARGET_RX = re.compile(r"^\s*pull_request_target\s*:", re.MULTILINE)

# After CYBER_CI_SUPPLY_CHAIN_HARDENING_V1 every workflow must declare top-level permissions.
KNOWN_WORKFLOWS_MISSING_TOP_LEVEL_PERMISSIONS: frozenset[str] = frozenset()


def _workflow_files() -> list[Path]:
    return sorted(
        path
        for pattern in ("*.yml", "*.yaml")
        for path in WORKFLOW_ROOT.glob(pattern)
        if path.is_file()
    )


def _workflow_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _uses_refs(text: str) -> list[str]:
    return [m.group(1).strip() for m in USES_REF_RX.finditer(text)]


def _classify_uses_ref(ref: str) -> str:
    if ref.startswith("./"):
        return "LOCAL_ACTION"
    if ref.startswith("docker://"):
        return "DOCKER_ACTION"
    if ref.startswith("."):
        return "REUSABLE_LOCAL_WORKFLOW"
    if "/" not in ref:
        return "UNKNOWN"
    if "/.github/workflows/" in ref or ref.endswith((".yml", ".yaml")):
        # owner/repo/.github/workflows/x.yml@sha — still external reusable workflow
        return "REUSABLE_EXTERNAL_WORKFLOW"
    return "EXTERNAL_GITHUB_ACTION"


def _workflows_missing_top_level_permissions() -> set[str]:
    missing: set[str] = set()
    for path in _workflow_files():
        if not TOP_LEVEL_PERMISSIONS_RX.search(_workflow_text(path)):
            missing.add(path.name)
    return missing


def _top_level_permissions_malformed() -> list[str]:
    """Fail closed when a top-level permissions key has no mapping / empty body."""
    offenders: list[str] = []
    for path in _workflow_files():
        lines = _workflow_text(path).splitlines()
        for idx, line in enumerate(lines):
            if not re.match(r"^permissions\s*:", line):
                continue
            rhs = line.split(":", 1)[1].strip()
            if rhs in {"write-all", "WRITE-ALL"}:
                offenders.append(f"{path.name}: write-all")
                break
            if rhs == "{}":
                break
            if rhs:
                # inline mapping form e.g. permissions: contents: read — rare; accept if non-empty
                break
            # Look ahead for indented mapping entries
            has_body = False
            for nxt in lines[idx + 1 :]:
                if not nxt.strip():
                    break
                if re.match(r"^[A-Za-z0-9_-]", nxt):
                    break
                if re.match(r"^  [A-Za-z0-9_-]+\s*:", nxt) or nxt.strip() == "{}":
                    has_body = True
                    break
                if nxt.startswith("  #"):
                    continue
                break
            if not has_body:
                offenders.append(f"{path.name}: empty permissions mapping")
            break
    return offenders


def test_cybersecurity_baseline_contract_has_workflows_to_check() -> None:
    workflows = _workflow_files()
    assert WORKFLOW_ROOT.exists()
    assert workflows


def test_cybersecurity_baseline_contract_module_avoids_execution_hooks() -> None:
    test_text = Path(__file__).read_text(encoding="utf-8")
    import_lines = [
        line.strip()
        for line in test_text.splitlines()
        if line.strip().startswith(("import ", "from "))
    ]

    forbidden_import_prefixes = [
        "import os",
        "from os",
        "import subprocess",
        "from subprocess",
        "import runpy",
        "from runpy",
        "import importlib",
        "from importlib",
        "import requests",
        "from requests",
        "import httpx",
        "from httpx",
        "import urllib",
        "from urllib",
        "import socket",
        "from socket",
    ]

    found = [
        prefix
        for prefix in forbidden_import_prefixes
        if any(line.startswith(prefix) for line in import_lines)
    ]
    assert not found, f"static baseline contract must not import execution/network hooks: {found}"


def test_cybersecurity_baseline_external_actions_are_full_sha_pinned() -> None:
    floating: list[tuple[str, str]] = []
    unpinned_or_tag: list[tuple[str, str]] = []
    unknown: list[tuple[str, str]] = []
    sha_pins = 0
    external_total = 0

    for path in _workflow_files():
        for ref in _uses_refs(_workflow_text(path)):
            kind = _classify_uses_ref(ref)
            if kind in {"LOCAL_ACTION", "DOCKER_ACTION", "REUSABLE_LOCAL_WORKFLOW"}:
                continue
            if kind == "UNKNOWN":
                unknown.append((path.name, ref))
                continue
            external_total += 1
            if FLOATING_REF_RX.search(ref):
                floating.append((path.name, ref))
            if SHA_PIN_RX.search(ref):
                sha_pins += 1
            else:
                unpinned_or_tag.append((path.name, ref))

    assert not unknown, f"unclassified uses: refs are forbidden: {unknown}"
    assert not floating, f"floating mutable uses: refs are forbidden: {floating}"
    assert not unpinned_or_tag, (
        "external GitHub Actions must use full 40-hex commit SHA pins "
        f"(tag/branch refs forbidden): {unpinned_or_tag}"
    )
    assert external_total > 0
    assert sha_pins == external_total


def test_cybersecurity_baseline_every_workflow_has_top_level_permissions() -> None:
    actual = _workflows_missing_top_level_permissions()
    assert actual == set(KNOWN_WORKFLOWS_MISSING_TOP_LEVEL_PERMISSIONS), (
        f"every active workflow must declare top-level permissions:; missing={sorted(actual)}"
    )
    malformed = _top_level_permissions_malformed()
    assert not malformed, f"malformed top-level permissions blocks: {malformed}"


def test_cybersecurity_baseline_forbids_write_all_and_pull_request_target() -> None:
    write_all: list[str] = []
    prt: list[str] = []
    for path in _workflow_files():
        text = _workflow_text(path)
        if WRITE_ALL_RX.search(text):
            write_all.append(path.name)
        if PULL_REQUEST_TARGET_RX.search(text):
            prt.append(path.name)
    assert not write_all, f"permissions: write-all is forbidden: {write_all}"
    assert not prt, f"pull_request_target is forbidden: {prt}"


def test_cybersecurity_baseline_docs_anchors_present() -> None:
    notes = SECURITY_NOTES.read_text(encoding="utf-8")
    index = CI_GHA_AUDIT_INDEX.read_text(encoding="utf-8")

    assert "PEAK_TRADE_CYBERSECURITY_BASELINE_REFRESH_V1" in notes
    assert "CYBER_CI_SUPPLY_CHAIN_HARDENING_V1" in notes
    assert "RR-CB-001" in notes
    assert "Action pinning posture" in index
    assert "CYBER_CI_SUPPLY_CHAIN_HARDENING_V1" in index
    assert (
        "test_cybersecurity_baseline_action_ref_and_permissions_visibility_contract_v0.py" in index
    )
    assert "full-SHA-pinned" in notes or "full SHA-pinned" in notes or "40-hex" in notes
    assert "PEAK_TRADE_CYBERSECURITY_BASELINE_REFRESH_V1" in index
