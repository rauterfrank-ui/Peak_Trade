"""Workflow permission boundary visibility v1 (static inventory + low-risk guards).

Parses `.github/workflows/*.{yml,yaml}` as UTF-8 text only (regex/heuristic).
Never dispatches workflows, never calls external APIs, never executes ops scripts,
never touches runtime, scheduler, paper/testnet/live, broker/exchange, or orders.

Visibility-first: risky triggers/commands/id-token usage are recorded. Enforcement is
limited to: ``pull_request_target`` requires at least one ``permissions:`` key line,
and every scanned workflow path must stay under ``.github/workflows``.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
WORKFLOW_ROOT = REPO_ROOT / ".github" / "workflows"

_PULL_REQUEST_TARGET_RX = re.compile(r"(?m)^[\t ]*pull_request_target\s*:")
_WORKFLOW_DISPATCH_RX = re.compile(r"(?m)^[\t ]*workflow_dispatch\s*:")
_SCHEDULE_RX = re.compile(r"(?m)^[\t ]*schedule\s*:")
_PERMISSIONS_LINE_RX = re.compile(r"(?m)^[\t ]*permissions\s*:")
_ID_TOKEN_RX = re.compile(r"\bid-token\s*:", re.I)

_FILENAME_RELEASE_DEPLOY_PUBLISH_RX = re.compile(r"(release|deploy|publish|pypi)", re.I)

_RISK_MARKERS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("curl", re.compile(r"\bcurl\b", re.I)),
    ("wget", re.compile(r"\bwget\b", re.I)),
    ("ssh", re.compile(r"\bssh\b", re.I)),
    ("scp", re.compile(r"\bscp\b", re.I)),
    ("rsync", re.compile(r"\brsync\b", re.I)),
    ("docker_login", re.compile(r"\bdocker\s+login\b", re.I)),
    ("gh_release", re.compile(r"\bgh\s+release\b", re.I)),
    ("pypi", re.compile(r"\bpypi\b", re.I)),
    ("twine", re.compile(r"\btwine\b", re.I)),
    ("npm_publish", re.compile(r"\bnpm\s+publish\b", re.I)),
)


def _workflow_files() -> list[Path]:
    return sorted(
        path
        for pattern in ("*.yml", "*.yaml")
        for path in WORKFLOW_ROOT.glob(pattern)
        if path.is_file()
    )


def _workflow_record(rel_posix: str, text: str) -> dict[str, Any]:
    risky_cmds = [name for name, rx in _RISK_MARKERS if rx.search(text)]

    return {
        "path": rel_posix,
        "pull_request_target": bool(_PULL_REQUEST_TARGET_RX.search(text)),
        "workflow_dispatch": bool(_WORKFLOW_DISPATCH_RX.search(text)),
        "schedule": bool(_SCHEDULE_RX.search(text)),
        "permissions_line_present": bool(_PERMISSIONS_LINE_RX.search(text)),
        "id_token_marker_present": bool(_ID_TOKEN_RX.search(text)),
        "risky_command_markers": risky_cmds,
        "workflow_filename_release_like": bool(
            _FILENAME_RELEASE_DEPLOY_PUBLISH_RX.search(Path(rel_posix).name)
        ),
    }


def build_workflow_permission_inventory_v1() -> dict[str, Any]:
    """Deterministic repo-local workflow boundary snapshot."""
    workflows = _workflow_files()
    inventory: dict[str, dict[str, Any]] = {}

    for path in workflows:
        try:
            rel = path.relative_to(REPO_ROOT).as_posix()
        except ValueError as exc:
            raise AssertionError(f"workflow path escapes repo root: {path}") from exc

        if not rel.startswith(".github/workflows/"):
            raise AssertionError(f"workflow path outside .github/workflows: {rel}")

        text = path.read_text(encoding="utf-8")
        inventory[rel] = _workflow_record(rel, text)

    return {"workflow_root": ".github/workflows", "workflows": inventory}


def test_workflow_permission_boundary_visibility_v1_inventory_nonempty_and_paths_safe() -> None:
    inv = build_workflow_permission_inventory_v1()
    workflows = inv["workflows"]

    assert WORKFLOW_ROOT.exists(), ".github/workflows should exist for CI repos using workflows"
    assert workflows, "expected at least one workflow YAML file"

    for rel, row in sorted(workflows.items()):
        assert rel.startswith(".github/workflows/")
        assert row["path"] == rel


def test_workflow_permission_boundary_visibility_v1_pull_request_target_requires_permissions_line() -> (
    None
):
    """Low-risk guard: ``pull_request_target`` without explicit permissions is rejected."""
    inv = build_workflow_permission_inventory_v1()

    offenders: list[str] = []
    for rel, row in inv["workflows"].items():
        if row["pull_request_target"] and not row["permissions_line_present"]:
            offenders.append(rel)

    assert not offenders, (
        "workflows using pull_request_target must declare at least one "
        f"'permissions:' key line for reviewer visibility: {offenders}"
    )


def test_workflow_permission_boundary_visibility_v1_meta_avoids_execution_hooks() -> None:
    test_text = Path(__file__).read_text(encoding="utf-8")
    marker = "def test_workflow_permission_boundary_visibility_v1_meta_avoids_execution_hooks"
    start = test_text.find(marker)
    assert start != -1
    tail = test_text[start:]
    after = tail[len(marker) :]
    next_fn = re.search(r"\n^def test_", after, re.MULTILINE)
    chunk = tail[: len(marker) + next_fn.start()] if next_fn else tail

    forbidden = [
        "subprocess" + ".",
        "os" + ".system",
        "runpy" + ".",
        "importlib" + ".import_module",
        "requests" + ".",
        "httpx" + ".",
        "urllib" + ".",
        "socket" + ".",
        "".join(("gh ", "workflow")),
        "".join(("gh ", "api")),
        "".join(("curl", " ")),
        "".join(("wget", " ")),
    ]
    hits = [f for f in forbidden if f in chunk]
    assert not hits, f"visibility contract module chunk must stay execution-safe: {hits}"
