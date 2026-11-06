"""Static contract tests for GitHub workflows avoiding pull_request_target.

Parses workflow YAML files as UTF-8 text only. Never dispatches workflows,
never calls GitHub APIs, never executes scripts, and never touches runtime,
scheduler, daemon, testnet/live, broker/exchange, or order-submission paths.
"""

from __future__ import annotations

import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
WORKFLOW_ROOT = REPO_ROOT / ".github" / "workflows"
CHECKOUT_USES_PATTERN = re.compile(r"uses:\s*actions/checkout@v(\d+)\b")
FORBIDDEN_CHECKOUT_VERSIONS = frozenset({"3", "4"})
REQUIRED_CHECKOUT_VERSION = "5"
TIMEOUT_MINUTES_PATTERN = re.compile(r"^\s*timeout-minutes:\s*(\d+)\s*$", re.MULTILINE)
PEAK_TRADE_CI_ABSOLUTE_HARD_TIMEOUT_MINUTES = 25
FORBIDDEN_EXPLICIT_TIMEOUT_MINUTES = frozenset({40})


def _workflow_files() -> list[Path]:
    return sorted(
        path
        for pattern in ("*.yml", "*.yaml")
        for path in WORKFLOW_ROOT.glob(pattern)
        if path.is_file()
    )


def _workflow_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_workflows_no_pull_request_target_contract_has_workflows_to_check() -> None:
    workflows = _workflow_files()

    assert WORKFLOW_ROOT.exists()
    assert workflows


def test_workflows_no_pull_request_target_contract_module_avoids_execution_hooks() -> None:
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
    assert not found, f"static workflow contract must not import execution/network hooks: {found}"


def test_workflows_no_pull_request_target_contract_forbids_event() -> None:
    """No workflow may use the high-risk pull_request_target event."""
    offenders: list[str] = []

    event_pattern = re.compile(r"^\s*pull_request_target\s*:", re.MULTILINE)

    for workflow in _workflow_files():
        text = _workflow_text(workflow)
        if event_pattern.search(text):
            offenders.append(workflow.relative_to(REPO_ROOT).as_posix())

    assert not offenders, f"pull_request_target is forbidden in workflows: {offenders}"


def test_workflows_no_pull_request_target_contract_retains_static_local_scope() -> None:
    test_text = Path(__file__).read_text(encoding="utf-8")

    # Built dynamically so this guard does not match its own string table.
    forbidden_fragments = [
        "".join(("subprocess", ".")),
        "".join(("os", ".system")),
        "".join(("runpy", ".")),
        "".join(("importlib", ".import_module")),
        "".join(("requests", ".")),
        "".join(("httpx", ".")),
        "".join(("urllib", ".")),
        "".join(("socket", ".")),
        " ".join(("gh", "workflow", "run")),
        " ".join(("gh", "api")),
    ]

    found = [fragment for fragment in forbidden_fragments if fragment in test_text]
    assert not found, f"contract must remain static/local-only: {found}"


def test_workflows_no_pull_request_target_contract_covers_all_workflow_files() -> None:
    workflows = _workflow_files()
    workflow_names = {path.name for path in workflows}

    assert len(workflows) >= 1
    assert any(name.endswith(".yml") or name.endswith(".yaml") for name in workflow_names)


def _checkout_uses_by_workflow() -> dict[str, list[str]]:
    by_workflow: dict[str, list[str]] = {}
    for workflow in _workflow_files():
        matches = CHECKOUT_USES_PATTERN.findall(_workflow_text(workflow))
        if matches:
            by_workflow[workflow.relative_to(REPO_ROOT).as_posix()] = matches
    return by_workflow


def test_workflows_checkout_pin_uniform_v5_contract_forbids_legacy_versions() -> None:
    offenders: list[str] = []

    for workflow_path, versions in _checkout_uses_by_workflow().items():
        legacy = sorted({version for version in versions if version in FORBIDDEN_CHECKOUT_VERSIONS})
        if legacy:
            offenders.append(f"{workflow_path}: actions/checkout@v{', v'.join(legacy)}")

    assert not offenders, f"legacy checkout pins are forbidden: {offenders}"


def test_workflows_checkout_pin_uniform_v5_contract_requires_explicit_v5() -> None:
    offenders: list[str] = []

    for workflow_path, versions in _checkout_uses_by_workflow().items():
        non_v5 = sorted({version for version in versions if version != REQUIRED_CHECKOUT_VERSION})
        if non_v5:
            offenders.append(f"{workflow_path}: actions/checkout@v{', v'.join(non_v5)}")

    assert not offenders, f"checkout pins must use actions/checkout@v5: {offenders}"


def _explicit_timeout_minutes_by_workflow() -> dict[str, list[int]]:
    by_workflow: dict[str, list[int]] = {}
    for workflow in _workflow_files():
        values = [int(match) for match in TIMEOUT_MINUTES_PATTERN.findall(_workflow_text(workflow))]
        if values:
            by_workflow[workflow.relative_to(REPO_ROOT).as_posix()] = values
    return by_workflow


def test_workflows_absolute_hard_timeout_contract_caps_explicit_job_timeouts() -> None:
    offenders: list[str] = []

    for workflow_path, values in _explicit_timeout_minutes_by_workflow().items():
        for value in values:
            if value > PEAK_TRADE_CI_ABSOLUTE_HARD_TIMEOUT_MINUTES:
                offenders.append(f"{workflow_path}: timeout-minutes={value}")

    assert not offenders, (
        "explicit workflow job timeouts must be <= "
        f"{PEAK_TRADE_CI_ABSOLUTE_HARD_TIMEOUT_MINUTES} minutes: {offenders}"
    )


def test_workflows_absolute_hard_timeout_contract_forbids_legacy_40_minute_values() -> None:
    offenders: list[str] = []

    for workflow_path, values in _explicit_timeout_minutes_by_workflow().items():
        for value in values:
            if value in FORBIDDEN_EXPLICIT_TIMEOUT_MINUTES:
                offenders.append(f"{workflow_path}: timeout-minutes={value}")

    assert not offenders, f"legacy 40-minute workflow timeouts are forbidden: {offenders}"
