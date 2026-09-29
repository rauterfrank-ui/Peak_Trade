"""Fail-closed fresh-root isolation for Actual-Venue-POST pre-live path.

RUNTIME_AUTHORIZATION_EFFECT=PRE_LIVE_ISOLATION_VALIDATION_ONLY
"""

from __future__ import annotations

from pathlib import Path

HISTORICAL_LOCAL_POST_STORE_MARKER = "first_real_okx_europe_venue_post"
DEFAULT_CAP24_REL = Path("runtime/current_productive/cap24_selection_state")


class PreLiveFreshRuntimeRootIsolationError(RuntimeError):
    """Fresh-root isolation violation."""


def _resolve_under_repo(path: Path, repo_root: Path) -> Path:
    candidate = path if path.is_absolute() else (repo_root / path)
    return candidate.resolve()


def validate_post_durable_store_root_isolation_v1(
    *,
    store_root: Path | str,
    repo_root: Path | None = None,
) -> dict[str, str | bool]:
    """Reject historical consumed POST stores and implicit discovery roots."""

    root = Path(store_root)
    repo = repo_root or Path(__file__).resolve().parents[3]
    resolved = _resolve_under_repo(root, repo)
    under_repo = resolved.is_relative_to(repo.resolve())
    rel = str(resolved.relative_to(repo.resolve())) if under_repo else str(resolved)
    reasons: list[str] = []
    normalized = rel.replace("\\", "/")
    if HISTORICAL_LOCAL_POST_STORE_MARKER in normalized:
        reasons.append("HISTORICAL_FIRST_REAL_OKX_POST_STORE_FORBIDDEN")
    if under_repo and not normalized.startswith("runtime/"):
        reasons.append("POST_STORE_MUST_LIVE_UNDER_RUNTIME_NAMESPACE")
    return {
        "OK": not reasons,
        "RESOLVED_PATH": rel,
        "REASON_CODES": ",".join(reasons) if reasons else "",
    }


def validate_productivity_root_isolation_v1(
    *,
    productivity_root: Path | str,
    repo_root: Path | None = None,
    explicit_binding_required: bool = True,
) -> dict[str, str | bool]:
    root = Path(productivity_root)
    repo = repo_root or Path(__file__).resolve().parents[3]
    resolved = _resolve_under_repo(root, repo)
    rel = (
        str(resolved.relative_to(repo.resolve()))
        if resolved.is_relative_to(repo.resolve())
        else str(resolved)
    )
    default_resolved = _resolve_under_repo(DEFAULT_CAP24_REL, repo)
    reasons: list[str] = []
    if resolved == default_resolved and explicit_binding_required:
        reasons.append("DEFAULT_CAP24_ROOT_REQUIRES_EXPLICIT_PRE_LIVE_BINDING")
    if HISTORICAL_LOCAL_POST_STORE_MARKER in rel.replace("\\", "/"):
        reasons.append("HISTORICAL_POST_STORE_PATH_FORBIDDEN")
    return {
        "OK": not reasons,
        "RESOLVED_PATH": rel,
        "REASON_CODES": ",".join(reasons) if reasons else "",
    }


def assert_post_durable_store_root_isolation_v1(
    *,
    store_root: Path | str,
    repo_root: Path | None = None,
) -> None:
    probe = validate_post_durable_store_root_isolation_v1(
        store_root=store_root,
        repo_root=repo_root,
    )
    if probe["OK"] is not True:
        raise PreLiveFreshRuntimeRootIsolationError(
            str(probe.get("REASON_CODES") or "ISOLATION_FAIL")
        )


__all__ = [
    "DEFAULT_CAP24_REL",
    "HISTORICAL_LOCAL_POST_STORE_MARKER",
    "PreLiveFreshRuntimeRootIsolationError",
    "assert_post_durable_store_root_isolation_v1",
    "validate_post_durable_store_root_isolation_v1",
    "validate_productivity_root_isolation_v1",
]
