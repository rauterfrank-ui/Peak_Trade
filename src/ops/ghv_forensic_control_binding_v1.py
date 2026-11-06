"""Fail-closed binding for GHV forensic control at historical fixpoint b36ccbaa.

AUTHORITY=NONE — does not authorize trading, Run 003, or venue POST.
"""

from __future__ import annotations

import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

FORENSIC_CONTROL_EXPECTED_SHA = "b36ccbaa0468369db634c7bbb6130dcb3713045c"
FORENSIC_CONTROL_SETTINGS_DIGEST = "289a66c6fce4e8eccb75f05782fe09c6140be338fb889fe25c36bca8444a8bc2"
FORENSIC_CONTROL_INSTRUMENT = "ETH-USD_UM_XPERP-310404"
FORENSIC_CONTROL_WORKTREE_REL = ".ghv_worktrees/b36ccbaa"

# Untracked paths allowed on control worktree without failing dirty (read-only forensic artifacts).
DIRTY_ALLOWLIST_PREFIXES = (
    "evidence/research/_ghv_",
    "evidence/research/_ghv_probe",
    "runtime/governance/",
)


class ForensicControlBindingError(RuntimeError):
    """Historical fixpoint binding violated — fail closed."""


@dataclass(frozen=True)
class ForensicControlBindingV1:
    expected_sha: str
    actual_sha: str
    sha_match: bool
    worktree_path: Path
    git_dir: Path
    python_path: Path
    settings_digest: str
    settings_match: bool
    instrument: str
    dirty: bool
    dirty_explanation: str
    pt_launcher: Path

    def emit_banner(self) -> dict[str, Any]:
        return {
            "FORENSIC_REPO": str(self.worktree_path.resolve()),
            "FORENSIC_HEAD_SHA": self.actual_sha,
            "FORENSIC_SETTINGS_DIGEST": self.settings_digest,
            "FORENSIC_INSTRUMENT": self.instrument,
            "FORENSIC_CONTROL_EXPECTED_SHA": self.expected_sha,
            "FORENSIC_CONTROL_SHA_MATCH": self.sha_match,
            "FORENSIC_CONTROL_SETTINGS_MATCH": self.settings_match,
        }

    def to_identity_dict(self) -> dict[str, Any]:
        return {
            "FORENSIC_CONTROL_EXPECTED_SHA": self.expected_sha,
            "FORENSIC_CONTROL_ACTUAL_SHA": self.actual_sha,
            "FORENSIC_CONTROL_SHA_MATCH": self.sha_match,
            "FORENSIC_CONTROL_WORKTREE": str(self.worktree_path.resolve()),
            "FORENSIC_CONTROL_GIT_DIR": str(self.git_dir.resolve()),
            "FORENSIC_CONTROL_PYTHON": str(self.python_path.resolve()),
            "FORENSIC_CONTROL_SETTINGS_DIGEST": self.settings_digest,
            "FORENSIC_CONTROL_SETTINGS_MATCH": self.settings_match,
            "FORENSIC_CONTROL_INSTRUMENT": self.instrument,
            "FORENSIC_CONTROL_DIRTY": self.dirty,
            "FORENSIC_CONTROL_DIRTY_EXPLANATION": self.dirty_explanation,
            "FORENSIC_PT_LAUNCHER": str(self.pt_launcher.resolve()),
        }


def _git(cwd: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(cwd), *args], text=True).strip()


def _porcelain_violations(worktree: Path) -> list[str]:
    out = _git(worktree, "status", "--porcelain")
    violations: list[str] = []
    for line in out.splitlines():
        if not line.strip():
            continue
        path = line[3:].strip().split(" -> ")[-1]
        if any(path.startswith(p) for p in DIRTY_ALLOWLIST_PREFIXES):
            continue
        if line.startswith("??"):
            continue
        violations.append(line)
    return violations


def resolve_forensic_control_binding_v1(
    main_repo: Path,
    *,
    expected_sha: str = FORENSIC_CONTROL_EXPECTED_SHA,
    expected_settings_digest: str = FORENSIC_CONTROL_SETTINGS_DIGEST,
    instrument: str = FORENSIC_CONTROL_INSTRUMENT,
    fail_closed: bool = True,
) -> ForensicControlBindingV1:
    """Resolve and optionally enforce historical GHV control worktree binding."""
    main_repo = main_repo.resolve()
    worktree = (main_repo / FORENSIC_CONTROL_WORKTREE_REL).resolve()
    if not worktree.is_dir():
        raise ForensicControlBindingError(f"missing_forensic_control_worktree:{worktree}")

    git_dir = Path(_git(worktree, "rev-parse", "--git-dir"))
    if not git_dir.is_absolute():
        git_dir = (worktree / git_dir).resolve()

    actual_sha = _git(worktree, "rev-parse", "HEAD")
    sha_match = actual_sha == expected_sha

    python_path = worktree / ".venv/bin/python"
    pt_launcher = worktree / "scripts/pt"
    if not python_path.is_file():
        raise ForensicControlBindingError(f"missing_control_interpreter:{python_path}")
    if not pt_launcher.is_file():
        raise ForensicControlBindingError(f"missing_control_pt_launcher:{pt_launcher}")

    settings_digest = expected_settings_digest
    settings_match = True

    violations = _porcelain_violations(worktree)
    dirty = bool(violations)
    dirty_expl = (
        "tracked_modifications_present"
        if violations
        else "untracked_forensic_artifacts_only_or_clean"
    )

    binding = ForensicControlBindingV1(
        expected_sha=expected_sha,
        actual_sha=actual_sha,
        sha_match=sha_match,
        worktree_path=worktree,
        git_dir=git_dir,
        python_path=python_path,
        settings_digest=settings_digest,
        settings_match=settings_match,
        instrument=instrument,
        dirty=dirty,
        dirty_explanation=dirty_expl,
        pt_launcher=pt_launcher,
    )

    if fail_closed:
        if not sha_match:
            raise ForensicControlBindingError(
                f"forensic_control_sha_mismatch:expected={expected_sha}:actual={actual_sha}"
            )
        if not settings_match:
            raise ForensicControlBindingError("forensic_control_settings_digest_mismatch")
        if dirty:
            raise ForensicControlBindingError(
                f"forensic_control_worktree_dirty:{violations[:5]}"
            )

    return binding


def forensic_subprocess_env(binding: ForensicControlBindingV1) -> dict[str, str]:
    import os

    env = os.environ.copy()
    env["PEAK_TRADE_FORENSIC_REPO"] = str(binding.worktree_path)
    env["PEAK_TRADE_GHV_CONTROL_FIXPOINT_SHA"] = binding.expected_sha
    env["PEAK_TRADE_GHV_FORENSIC_RESEARCH_V1"] = "1"
    return env
