"""Pfadkonventionen und Stamp-Auflösung (nur unter `bundle_root`, Appendix A.3)."""

from __future__ import annotations

from pathlib import Path

from .types import PaperShadowPathPolicyV0


def validate_stamp_token(stamp: str) -> bool:
    if not stamp or stamp in (".", ".."):
        return False
    if "/" in stamp or "\\" in stamp:
        return False
    return True


def path_is_under_root(bundle_root: Path, candidate: Path) -> bool:
    try:
        candidate.resolve().relative_to(bundle_root.resolve())
        return True
    except ValueError:
        return False


def resolve_stamp(
    bundle_root: Path,
    policy: PaperShadowPathPolicyV0 | None,
) -> tuple[str | None, tuple[str, ...]]:
    if policy is not None and policy.stamp:
        if not validate_stamp_token(policy.stamp):
            return None, ("invalid_stamp_token",)
        return policy.stamp, ()

    prj = bundle_root / "prj_smoke"
    if not prj.is_dir():
        return None, ("prj_smoke_missing_or_not_directory",)

    children = sorted(p for p in prj.iterdir() if p.is_dir())
    if len(children) == 0:
        return None, ("prj_smoke_stamp_missing",)
    if len(children) > 1:
        return None, ("prj_smoke_stamp_ambiguous",)

    name = children[0].name
    if not validate_stamp_token(name):
        return None, ("invalid_stamp_token",)
    return name, ()


def evidence_pack_dir(bundle_root: Path, stamp: str) -> Path:
    return bundle_root / "evidence_packs" / f"pack_prj_smoke_{stamp}"


def prj_smoke_run_dir(bundle_root: Path, stamp: str) -> Path:
    return bundle_root / "prj_smoke" / stamp
