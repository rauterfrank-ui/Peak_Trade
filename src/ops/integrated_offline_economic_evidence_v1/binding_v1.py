"""Config binding for integrated offline economic evidence v1."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


def _load_config(repo_root: Path) -> dict[str, Any]:
    path = repo_root / "config/ops/integrated_offline_economic_evidence_v1.toml"
    if not path.is_file():
        return {}
    try:
        import tomllib
    except ModuleNotFoundError:  # pragma: no cover
        import tomli as tomllib  # type: ignore[no-redef]
    return tomllib.loads(path.read_text(encoding="utf-8"))


def resolve_configured_integrated_offline_economic_evidence_relpath_v1(
    *,
    repo_root: Path,
) -> str:
    cfg = _load_config(repo_root)
    rel = str(cfg.get("canonical_evidence_relpath") or "").strip()
    return rel


def config_digest_sha256_v1(*, repo_root: Path) -> str:
    path = repo_root / "config/ops/integrated_offline_economic_evidence_v1.toml"
    if not path.is_file():
        return ""
    import hashlib

    return hashlib.sha256(path.read_bytes()).hexdigest()


@dataclass(frozen=True)
class VerificationBindingContextV1:
    expected_implementation_surface_digest_sha256: str
    expected_config_digest_sha256: str


def resolve_verification_binding_context_v1(
    *,
    repo_root: Path,
    expected_implementation_surface_digest_sha256: str | None = None,
    expected_config_digest_sha256: str | None = None,
) -> tuple[VerificationBindingContextV1 | None, list[str]]:
    """Authoritative expected binding digests for reference verification (fail-closed)."""
    blockers: list[str] = []
    impl = (
        str(expected_implementation_surface_digest_sha256 or "").strip()
        if expected_implementation_surface_digest_sha256 is not None
        else ""
    )
    cfg = (
        str(expected_config_digest_sha256 or "").strip()
        if expected_config_digest_sha256 is not None
        else ""
    )
    if not impl:
        from src.ops.integrated_offline_replay_and_correctness_head_bound_v1.binding_v1 import (
            compute_implementation_surface_digest_sha256_v1,
        )

        impl = compute_implementation_surface_digest_sha256_v1(repo_root=repo_root)
    if not cfg:
        cfg = config_digest_sha256_v1(repo_root=repo_root)
    if not impl:
        blockers.append("EXPECTED_IMPLEMENTATION_SURFACE_DIGEST_MISSING")
    if not cfg:
        blockers.append("EXPECTED_CONFIG_DIGEST_MISSING")
    if blockers:
        return None, blockers
    return VerificationBindingContextV1(
        expected_implementation_surface_digest_sha256=impl,
        expected_config_digest_sha256=cfg,
    ), blockers
