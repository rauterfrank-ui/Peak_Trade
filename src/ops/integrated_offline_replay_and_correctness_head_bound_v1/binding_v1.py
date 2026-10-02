"""Implementation-state binding for HEAD-bound correctness evidence v1.

Committed evidence must remain valid across follow-on evidence/governance/format
commits. Binding uses a stable proven source SHA plus a digest of bounded
implementation surfaces at verification time (not Git HEAD equality).
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from src.ops.integrated_offline_replay_and_correctness_head_bound_v1.constants_v1 import (
    CONFIG_RELPATH,
)

IMPLEMENTATION_SURFACE_RELPATHS: tuple[str, ...] = (
    "config/ops/integrated_offline_replay_and_correctness_head_bound_v1.toml",
    "src/ops/integrated_offline_replay_and_correctness_head_bound_v1/__init__.py",
    "src/ops/integrated_offline_replay_and_correctness_head_bound_v1/adjudication_v1.py",
    "src/ops/integrated_offline_replay_and_correctness_head_bound_v1/binding_v1.py",
    "src/ops/integrated_offline_replay_and_correctness_head_bound_v1/constants_v1.py",
    "src/ops/integrated_offline_replay_and_correctness_head_bound_v1/discovery_v1.py",
    "src/ops/integrated_offline_replay_and_correctness_head_bound_v1/economic_evidence_bundle_v1.py",
    "src/ops/integrated_offline_replay_and_correctness_head_bound_v1/proof_v1.py",
    "src/ops/integrated_offline_replay_and_correctness_head_bound_v1/verifier_v1.py",
    "src/ops/integrated_paper_shadow_observation_session_v1/readiness_producer_v1.py",
    "scripts/ops/run_integrated_offline_replay_correctness_and_paper_shadow_readiness_head_bound_v1.py",
)


def _load_config(repo_root: Path) -> dict[str, Any]:
    path = repo_root / CONFIG_RELPATH
    if not path.is_file():
        return {}
    try:
        import tomllib
    except ModuleNotFoundError:  # pragma: no cover
        import tomli as tomllib  # type: ignore[no-redef]
    return tomllib.loads(path.read_text(encoding="utf-8"))


def compute_implementation_surface_digest_sha256_v1(*, repo_root: Path) -> str:
    """Deterministic digest of bounded implementation/config surfaces."""
    root = repo_root.resolve()
    lines: list[str] = []
    for relpath in IMPLEMENTATION_SURFACE_RELPATHS:
        path = root / relpath
        if not path.is_file():
            lines.append(f"{relpath}\0MISSING")
            continue
        content_hash = hashlib.sha256(path.read_bytes()).hexdigest()
        lines.append(f"{relpath}\0{content_hash}")
    payload = "\n".join(lines).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def resolve_configured_correctness_evidence_relpath_v1(
    *,
    repo_root: Path,
    fallback_head_sha: str,
) -> str:
    cfg = _load_config(repo_root)
    rel = str(cfg.get("canonical_evidence_relpath") or "").strip()
    if rel:
        return rel
    return (
        f"evidence/ops/integrated_offline_replay_and_correctness_head_bound_v1/{fallback_head_sha}"
    )


def resolve_configured_economic_bundle_evidence_relpath_v1(
    *,
    repo_root: Path,
    fallback_head_sha: str,
) -> str:
    cfg = _load_config(repo_root)
    rel = str(cfg.get("economic_bundle_evidence_relpath") or "").strip()
    if rel:
        return rel
    return (
        "evidence/ops/integrated_paper_shadow_economic_evidence_bundle_head_bound_v1/"
        f"{fallback_head_sha}"
    )
