"""Discover verified HEAD-bound correctness evidence for readiness consumers."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from src.ops.integrated_offline_replay_and_correctness_head_bound_v1.constants_v1 import (
    CONFIG_RELPATH,
)
from src.ops.integrated_offline_replay_and_correctness_head_bound_v1.proof_v1 import (
    default_canonical_evidence_dir_for_head_v1,
    resolve_repository_head_sha_v1,
)
from src.ops.integrated_offline_replay_and_correctness_head_bound_v1.verifier_v1 import (
    verify_integrated_offline_replay_and_correctness_head_bound_evidence_v1,
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


def discover_verified_head_bound_correctness_at_current_head_v1(
    *,
    repo_root: Path,
) -> tuple[bool, bool, bool, str]:
    """Return (offline_replay_pass, correctness_pass, full_chain_proxy, evidence_note)."""
    root = repo_root.resolve()
    try:
        head = resolve_repository_head_sha_v1(repo_root=root)
    except ValueError as exc:
        return False, False, False, f"head_resolution_failed:{exc}"

    cfg = _load_config(root)
    rel = str(cfg.get("canonical_evidence_relpath") or "").strip()
    if not rel:
        rel = default_canonical_evidence_dir_for_head_v1(head_sha=head)
    evidence_root = root / rel
    verification = verify_integrated_offline_replay_and_correctness_head_bound_evidence_v1(
        evidence_root=evidence_root,
        repo_root=root,
        require_current_head=True,
    )
    if not verification.verified:
        blockers = ",".join(verification.blockers[:5]) or "verify_fail_closed"
        return False, False, False, f"head_bound_verify_blocked:{blockers}"

    return (
        True,
        True,
        True,
        f"verified:{rel}",
    )
