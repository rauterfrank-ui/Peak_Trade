"""External archive root contract — fail-closed writes outside git."""

from __future__ import annotations

import os
from pathlib import Path

from src.research.longer_chronological_pit_acquisition_v1 import ENV_ARCHIVE_ROOT

# Semantic subtrees under PEAK_TRADE_DATA_ARCHIVE_ROOT. Machine root stays external.
FORENSICS_DOCUMENTS_PEAK_TRADE_REL = "forensics/documents_peak_trade"
RUNTIME_EVIDENCE_20260520_REL = "runtime_evidence/20260520T161443Z"
_UNSET_SENTINEL = Path("/__peak_trade_data_archive_root_unset__")


class ArchiveRootError(ValueError):
    """Raised when archive root is missing or unsafe."""


def _repo_root() -> Path:
    # src/research/<pkg>/archive_root.py → parents[3] = repo root
    return Path(__file__).resolve().parents[3]


def resolve_archive_root(
    *,
    explicit: str | Path | None = None,
    env: dict[str, str] | None = None,
    require_for_write: bool = True,
) -> Path | None:
    """Resolve external archive root.

    Returns None when not set and ``require_for_write`` is False (read-only/plan).
    Raises ArchiveRootError when required for write or when path is unsafe.
    """
    env_map = env if env is not None else os.environ
    raw = ""
    if explicit is not None:
        raw = str(explicit).strip()
    else:
        raw = str(env_map.get(ENV_ARCHIVE_ROOT, "") or "").strip()

    if not raw:
        if require_for_write:
            raise ArchiveRootError(
                f"MISSING_{ENV_ARCHIVE_ROOT}: writes require an external archive root"
            )
        return None

    root = Path(raw).expanduser().resolve()
    validate_archive_root(root)
    return root


def validate_archive_root(root: Path) -> None:
    """Reject repo-relative, filesystem root, and home-directory roots."""
    if not root.is_absolute():
        raise ArchiveRootError("ARCHIVE_ROOT_NOT_ABSOLUTE")

    # Bare filesystem root
    if root == Path(root.anchor):
        raise ArchiveRootError("ARCHIVE_ROOT_IS_FILESYSTEM_ROOT")

    home = Path.home().resolve()
    if root == home:
        raise ArchiveRootError("ARCHIVE_ROOT_IS_HOME_DIRECTORY")

    repo = _repo_root().resolve()
    try:
        root.relative_to(repo)
    except ValueError:
        pass
    else:
        # equal to repo root or nested under it
        raise ArchiveRootError("ARCHIVE_ROOT_INSIDE_GIT_REPO")


def archive_layout(root: Path) -> dict[str, Path]:
    """Canonical subdirectories under the external archive root."""
    base = root / "longer_chronological_pit" / "chrono_3y_v1"
    return {
        "base": base,
        "raw": base / "raw",
        "normalized": base / "normalized",
        "manifests": base / "manifests",
        "quarantine": base / "quarantine",
        "state": base / "state",
        "logs": base / "logs",
    }


def located_forensics_documents_peak_trade(
    *,
    explicit: str | Path | None = None,
    env: dict[str, str] | None = None,
    require_for_write: bool = False,
) -> Path:
    """Resolve D01 forensic subtree. Unset env => non-Documents sentinel path."""
    root = resolve_archive_root(explicit=explicit, env=env, require_for_write=require_for_write)
    if root is None:
        return _UNSET_SENTINEL / FORENSICS_DOCUMENTS_PEAK_TRADE_REL
    return root / FORENSICS_DOCUMENTS_PEAK_TRADE_REL


def located_runtime_evidence_20260520(
    *,
    explicit: str | Path | None = None,
    env: dict[str, str] | None = None,
    require_for_write: bool = False,
) -> Path:
    """Resolve D03 runtime-evidence subtree. Unset env => non-Documents sentinel path."""
    root = resolve_archive_root(explicit=explicit, env=env, require_for_write=require_for_write)
    if root is None:
        return _UNSET_SENTINEL / RUNTIME_EVIDENCE_20260520_REL
    return root / RUNTIME_EVIDENCE_20260520_REL


def expand_data_archive_locator(value: str) -> str:
    """Join DATA_ARCHIVE_ROOT-relative locators. Leave unrelated strings unchanged."""
    if not isinstance(value, str) or not value:
        return value
    for rel in (RUNTIME_EVIDENCE_20260520_REL, FORENSICS_DOCUMENTS_PEAK_TRADE_REL):
        if value == rel or value.startswith(rel + "/"):
            root = resolve_archive_root(require_for_write=False)
            if root is None:
                return str(_UNSET_SENTINEL / value)
            return str(root / value)
    return value


def expand_locators_in_obj(obj: object) -> object:
    """Recursively expand archive-relative strings in JSON-like objects."""
    if isinstance(obj, str):
        return expand_data_archive_locator(obj)
    if isinstance(obj, list):
        return [expand_locators_in_obj(item) for item in obj]
    if isinstance(obj, dict):
        return {key: expand_locators_in_obj(val) for key, val in obj.items()}
    return obj


def archive_relative_locator(path: Path | str) -> str:
    """Return DATA_ARCHIVE_ROOT-relative locator when ``path`` is under a known root."""
    candidate = Path(path)
    bases: list[Path] = [_UNSET_SENTINEL]
    resolved_root = resolve_archive_root(require_for_write=False)
    if resolved_root is not None:
        bases.insert(0, resolved_root)
    for base in bases:
        try:
            return candidate.relative_to(base).as_posix()
        except ValueError:
            continue
    return str(candidate)


def join_runtime_evidence_relpath(root: Path, relpath: str, *, error_code: str) -> Path:
    """Join ``relpath`` under the D03 subtree of ``root``."""
    rel = Path(relpath)
    if rel.is_absolute() or ".." in rel.parts:
        raise ArchiveRootError(error_code)
    return assert_path_under_archive(root / RUNTIME_EVIDENCE_20260520_REL / rel, root)


def assert_path_under_archive(path: Path, root: Path) -> Path:
    resolved = path.expanduser().resolve()
    try:
        resolved.relative_to(root.resolve())
    except ValueError as exc:
        raise ArchiveRootError("PATH_OUTSIDE_ARCHIVE_ROOT") from exc
    # Refuse if somehow also under git repo
    repo = _repo_root().resolve()
    try:
        resolved.relative_to(repo)
        raise ArchiveRootError("PATH_RESOLVES_INTO_GIT_REPO")
    except ValueError:
        pass
    return resolved
