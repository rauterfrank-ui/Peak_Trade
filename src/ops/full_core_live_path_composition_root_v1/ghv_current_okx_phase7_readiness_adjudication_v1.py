"""Evidence-bound Phase-7 readiness adjudication for GHV OKX productive GET validation.

Offline reproof via frozen pytest owners. Adversarial review via static manifest +
review document (no runner self-attestation). FAIL_CLOSED by default.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from src.meta.learning_loop.contract_safety_v1 import compute_content_sha256, is_valid_sha256_hex

_GIT_SHA_HEX_RE = __import__("re").compile(r"^[0-9a-f]{40}$")

PHASE7_ADJUDICATION_CONTRACT_ID = "GHV_CURRENT_OKX_PHASE7_READINESS_ADJUDICATION_V1"
WORK_PACKAGE_ID = "GHV_CURRENT_OKX_PRODUCTIVE_GET_ACTIVATION_READINESS_V1"

PHASE7_OFFLINE_REPROOF_TEST_OWNERS_V1: tuple[str, ...] = (
    "tests/ops/test_full_core_exchange_reconciliation_v1.py",
    "tests/ops/test_full_core_exchange_reconciliation_okx_read_only_provider_v1.py",
    "tests/ops/test_full_core_post_submit_exchange_reconciliation_lifecycle_join_v1.py",
    "tests/ops/test_full_core_governed_cycle_host_post_submit_lifecycle_wiring_v1.py",
    "tests/ops/test_full_core_post_completed_hook_evidence_durability_v1.py",
    "tests/ops/test_full_core_s5_recovery_observation_v1.py",
    "tests/ops/test_full_core_orchestrated_post_submit_lifecycle_reconciliation_v1.py",
    "tests/ops/test_ghv_current_okx_productive_read_only_reconciliation_get_validation_v1.py",
)

PHASE7_ADVERSARIAL_REVIEW_MANIFEST_RELPATH = (
    "config/governance/ghv_current_okx_productive_get_activation_readiness_v1/"
    "phase7_adversarial_contract_review_v1.json"
)

PHASE7_REQUIRED_REVIEW_CONTRACT_PATHS_V1: frozenset[str] = frozenset(
    {
        PHASE7_ADVERSARIAL_REVIEW_MANIFEST_RELPATH,
        "docs/ops/specs/GHV_CURRENT_EXCHANGE_RECONCILIATION_INTEGRATION_V1.md",
        "scripts/ops/run_ghv_current_okx_productive_read_only_reconciliation_get_validation_v1.py",
        "src/ops/full_core_live_path_composition_root_v1/full_core_orchestrated_post_submit_lifecycle_reconciliation_v1.py",
        "src/ops/full_core_live_path_composition_root_v1/ghv_current_okx_phase7_readiness_adjudication_v1.py",
        "src/ops/full_core_live_path_composition_root_v1/ghv_current_okx_productive_read_only_reconciliation_get_validation_v1.py",
    }
)

MANIFEST_PROVENANCE_EXCLUDED_KEYS_V1: frozenset[str] = frozenset(
    {
        "review_evidence_sha256",
        "reviewed_contract_paths_sha256",
    }
)

_MANIFEST_PROVENANCE_BODY_SHA256_RE = re.compile(
    r"MANIFEST_PROVENANCE_BODY_SHA256=([0-9a-f]{64})",
    re.IGNORECASE,
)

PHASE7_PYTEST_TIMEOUT_SECONDS = 900.0


class Phase7ReadinessAdjudicationError(RuntimeError):
    """Fail-closed Phase-7 readiness violation."""


@dataclass(frozen=True)
class Phase7ReadinessAdjudicationV1:
    offline_reproof: str
    adversarial_review: str
    offline_reproof_detail: str
    adversarial_review_detail: str
    origin_main_sha: str
    git_head_sha: str
    offline_reproof_test_owners: tuple[str, ...]

    def offline_reproof_pass(self) -> bool:
        return self.offline_reproof == "PASS"

    def adversarial_review_pass(self) -> bool:
        return self.adversarial_review == "PASS"


def _normalize_sha(text: str) -> str:
    return str(text or "").strip().lower()


def _is_valid_git_commit_sha_v1(value: str) -> bool:
    return bool(_GIT_SHA_HEX_RE.match(_normalize_sha(value)))


def resolve_git_origin_main_sha_v1(*, repo_root: Path) -> str:
    try:
        proc = subprocess.run(
            ["git", "rev-parse", "origin/main"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=True,
            timeout=30,
        )
    except (subprocess.SubprocessError, OSError) as exc:
        raise Phase7ReadinessAdjudicationError("ORIGIN_MAIN_GIT_RESOLVE_FAILED") from exc
    sha = _normalize_sha(proc.stdout)
    if not _is_valid_git_commit_sha_v1(sha):
        raise Phase7ReadinessAdjudicationError("ORIGIN_MAIN_SHA_INVALID")
    return sha


def resolve_git_head_sha_v1(*, repo_root: Path) -> str:
    try:
        proc = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=True,
            timeout=30,
        )
    except (subprocess.SubprocessError, OSError) as exc:
        raise Phase7ReadinessAdjudicationError("HEAD_GIT_RESOLVE_FAILED") from exc
    sha = _normalize_sha(proc.stdout)
    if not _is_valid_git_commit_sha_v1(sha):
        raise Phase7ReadinessAdjudicationError("HEAD_SHA_INVALID")
    return sha


def verify_current_baseline_checkout_v1(
    *,
    repo_root: Path,
    declared_origin_main_sha: str,
) -> tuple[str, str]:
    """Declared SHA must match origin/main and HEAD (no drift during proof)."""

    declared = _normalize_sha(declared_origin_main_sha)
    if not _is_valid_git_commit_sha_v1(declared):
        raise Phase7ReadinessAdjudicationError("DECLARED_ORIGIN_MAIN_SHA_INVALID")
    actual_origin = resolve_git_origin_main_sha_v1(repo_root=repo_root)
    head = resolve_git_head_sha_v1(repo_root=repo_root)
    if actual_origin != declared:
        raise Phase7ReadinessAdjudicationError("ORIGIN_MAIN_SHA_DRIFT")
    if head != declared:
        raise Phase7ReadinessAdjudicationError("HEAD_NOT_AT_DECLARED_ORIGIN_MAIN")
    return actual_origin, head


def sha256_file_v1(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git_is_ancestor_commit_v1(
    *,
    repo_root: Path,
    ancestor_sha: str,
    descendant_sha: str,
) -> bool:
    ancestor = _normalize_sha(ancestor_sha)
    descendant = _normalize_sha(descendant_sha)
    if not _is_valid_git_commit_sha_v1(ancestor) or not _is_valid_git_commit_sha_v1(descendant):
        return False
    try:
        proc = subprocess.run(
            ["git", "merge-base", "--is-ancestor", ancestor, descendant],
            cwd=repo_root,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
    except (subprocess.SubprocessError, OSError):
        return False
    return proc.returncode == 0


def compute_manifest_provenance_body_sha256_v1(manifest: Mapping[str, Any]) -> str:
    """Hash manifest metadata excluding cross-linked review doc digest (trust anchor field)."""

    body = {k: v for k, v in manifest.items() if k not in MANIFEST_PROVENANCE_EXCLUDED_KEYS_V1}
    return compute_content_sha256(body)


def parse_manifest_provenance_anchor_from_review_doc_v1(review_text: str) -> str | None:
    match = _MANIFEST_PROVENANCE_BODY_SHA256_RE.search(review_text)
    if not match:
        return None
    return _normalize_sha(match.group(1))


def compute_reviewed_contract_paths_sha256_v1(
    repo_root: Path,
    relative_paths: tuple[str, ...],
) -> str:
    lines: list[str] = []
    for rel in sorted(relative_paths):
        path = repo_root / rel
        if not path.is_file():
            raise Phase7ReadinessAdjudicationError(f"REVIEWED_CONTRACT_MISSING:{rel}")
        if rel == PHASE7_ADVERSARIAL_REVIEW_MANIFEST_RELPATH:
            manifest = _load_json_object_v1(path)
            digest = compute_manifest_provenance_body_sha256_v1(manifest)
            lines.append(f"{rel}:{digest}")
        else:
            lines.append(f"{rel}:{sha256_file_v1(path)}")
    return hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest()


def _load_json_object_v1(path: Path) -> Mapping[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise Phase7ReadinessAdjudicationError("ADVERSARIAL_MANIFEST_UNREADABLE") from exc
    if not isinstance(payload, Mapping):
        raise Phase7ReadinessAdjudicationError("ADVERSARIAL_MANIFEST_NOT_OBJECT")
    return payload


def adjudicate_phase7_adversarial_contract_review_v1(
    *,
    repo_root: Path,
    declared_origin_main_sha: str,
) -> tuple[str, str]:
    manifest_path = repo_root / PHASE7_ADVERSARIAL_REVIEW_MANIFEST_RELPATH
    if not manifest_path.is_file():
        return "FAIL", "MANIFEST_MISSING"

    manifest = _load_json_object_v1(manifest_path)
    if (
        str(manifest.get("schema_version") or "")
        != "ghv_current_okx_phase7_adversarial_contract_review_v1"
    ):
        return "FAIL", "MANIFEST_SCHEMA_VERSION"
    if str(manifest.get("work_package") or "") != WORK_PACKAGE_ID:
        return "FAIL", "MANIFEST_WORK_PACKAGE"
    if str(manifest.get("review_scope") or "") != "PHASE_7_TO_PHASE_8_ENTRY_BOUNDARY":
        return "FAIL", "MANIFEST_REVIEW_SCOPE"
    review_baseline = _normalize_sha(str(manifest.get("review_baseline_origin_main_sha") or ""))
    if not review_baseline:
        review_baseline = _normalize_sha(str(manifest.get("baseline_origin_main_sha") or ""))
    if not _is_valid_git_commit_sha_v1(review_baseline):
        return "FAIL", "REVIEW_BASELINE_SHA_INVALID"
    declared = _normalize_sha(declared_origin_main_sha)
    if not git_is_ancestor_commit_v1(
        repo_root=repo_root,
        ancestor_sha=review_baseline,
        descendant_sha=declared,
    ):
        return "FAIL", "REVIEW_BASELINE_NOT_ANCESTOR_OF_CURRENT_ORIGIN_MAIN"
    if manifest.get("runner_self_attestation_forbidden") is not True:
        return "FAIL", "RUNNER_SELF_ATTESTATION_NOT_FORBIDDEN"
    if str(manifest.get("adversarial_review_verdict") or "") != "PASS":
        return "FAIL", "ADVERSARIAL_VERDICT_NOT_PASS"
    open_defects = manifest.get("open_defects")
    if not isinstance(open_defects, list) or open_defects:
        return "FAIL", "OPEN_DEFECTS_PRESENT"

    raw_paths = manifest.get("reviewed_contract_paths")
    if not isinstance(raw_paths, list) or not raw_paths:
        return "FAIL", "REVIEWED_CONTRACT_PATHS_MISSING"
    rel_paths = tuple(str(p) for p in raw_paths)
    if not PHASE7_REQUIRED_REVIEW_CONTRACT_PATHS_V1.issubset(set(rel_paths)):
        return "FAIL", "REVIEW_SCOPE_INCOMPLETE"
    expected_paths_hash = str(manifest.get("reviewed_contract_paths_sha256") or "").lower()
    if not is_valid_sha256_hex(expected_paths_hash):
        return "FAIL", "REVIEWED_CONTRACT_PATHS_HASH_INVALID"
    try:
        actual_paths_hash = compute_reviewed_contract_paths_sha256_v1(repo_root, rel_paths)
    except Phase7ReadinessAdjudicationError as exc:
        return "FAIL", str(exc)
    if actual_paths_hash != expected_paths_hash:
        return "FAIL", "REVIEWED_CONTRACT_STALE_OR_TAMPERED"

    review_doc_rel = str(manifest.get("review_evidence_relpath") or "")
    if not review_doc_rel:
        return "FAIL", "REVIEW_EVIDENCE_RELPATH_MISSING"
    review_doc_path = repo_root / review_doc_rel
    if not review_doc_path.is_file():
        return "FAIL", "REVIEW_EVIDENCE_MISSING"
    expected_doc_hash = str(manifest.get("review_evidence_sha256") or "").lower()
    if not is_valid_sha256_hex(expected_doc_hash):
        return "FAIL", "REVIEW_EVIDENCE_HASH_INVALID"
    actual_doc_hash = sha256_file_v1(review_doc_path)
    if actual_doc_hash != expected_doc_hash:
        return "FAIL", "REVIEW_EVIDENCE_STALE_OR_TAMPERED"

    review_text = review_doc_path.read_text(encoding="utf-8")
    anchored_provenance = parse_manifest_provenance_anchor_from_review_doc_v1(review_text)
    if not anchored_provenance or not is_valid_sha256_hex(anchored_provenance):
        return "FAIL", "MANIFEST_PROVENANCE_ANCHOR_MISSING_IN_REVIEW_DOC"
    actual_provenance = compute_manifest_provenance_body_sha256_v1(manifest)
    if actual_provenance != anchored_provenance:
        return "FAIL", "MANIFEST_PROVENANCE_BODY_MISMATCH_REVIEW_ANCHOR"

    forbidden = manifest.get("forbidden_runtime_generated_evidence_paths")
    if isinstance(forbidden, list):
        for rel in forbidden:
            if (repo_root / str(rel)).exists():
                return "FAIL", f"FORBIDDEN_RUNTIME_EVIDENCE_PRESENT:{rel}"

    return "PASS", f"MANIFEST_OK:{manifest_path.name}"


def execute_phase7_offline_reproof_pytest_v1(*, repo_root: Path) -> tuple[str, str]:
    missing = [
        rel for rel in PHASE7_OFFLINE_REPROOF_TEST_OWNERS_V1 if not (repo_root / rel).is_file()
    ]
    if missing:
        return "FAIL", f"MISSING_TEST_OWNER:{missing[0]}"

    pt = repo_root / "scripts" / "pt"
    if not pt.is_file():
        return "FAIL", "CANONICAL_PT_LAUNCHER_MISSING"

    cmd = [str(pt), "-m", "pytest", "-q", *PHASE7_OFFLINE_REPROOF_TEST_OWNERS_V1]
    try:
        proc = subprocess.run(
            cmd,
            cwd=repo_root,
            capture_output=True,
            text=True,
            timeout=PHASE7_PYTEST_TIMEOUT_SECONDS,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return "FAIL", "PYTEST_TIMEOUT"
    except (subprocess.SubprocessError, OSError) as exc:
        return "FAIL", f"PYTEST_SUBPROCESS_ERROR:{exc}"

    if proc.returncode != 0:
        tail = (proc.stdout or "")[-500:] + (proc.stderr or "")[-500:]
        return "FAIL", f"PYTEST_EXIT_{proc.returncode}:{tail.strip()[:200]}"
    return "PASS", f"PYTEST_OK:owners={len(PHASE7_OFFLINE_REPROOF_TEST_OWNERS_V1)}"


def adjudicate_ghv_current_okx_phase7_readiness_v1(
    *,
    repo_root: Path,
    declared_origin_main_sha: str,
) -> Phase7ReadinessAdjudicationV1:
    try:
        origin_sha, head_sha = verify_current_baseline_checkout_v1(
            repo_root=repo_root,
            declared_origin_main_sha=declared_origin_main_sha,
        )
    except Phase7ReadinessAdjudicationError as exc:
        return Phase7ReadinessAdjudicationV1(
            offline_reproof="FAIL",
            adversarial_review="FAIL",
            offline_reproof_detail=str(exc),
            adversarial_review_detail="BASELINE_CHECK_FAILED",
            origin_main_sha=_normalize_sha(declared_origin_main_sha),
            git_head_sha="",
            offline_reproof_test_owners=PHASE7_OFFLINE_REPROOF_TEST_OWNERS_V1,
        )

    offline_status, offline_detail = execute_phase7_offline_reproof_pytest_v1(repo_root=repo_root)
    adv_status, adv_detail = adjudicate_phase7_adversarial_contract_review_v1(
        repo_root=repo_root,
        declared_origin_main_sha=origin_sha,
    )

    return Phase7ReadinessAdjudicationV1(
        offline_reproof=offline_status,
        adversarial_review=adv_status,
        offline_reproof_detail=offline_detail,
        adversarial_review_detail=adv_detail,
        origin_main_sha=origin_sha,
        git_head_sha=head_sha,
        offline_reproof_test_owners=PHASE7_OFFLINE_REPROOF_TEST_OWNERS_V1,
    )


def phase7_readiness_manifest_digest_v1(manifest: Mapping[str, Any]) -> str:
    body = {k: v for k, v in manifest.items() if k != "integrity"}
    return compute_content_sha256(body)


__all__ = [
    "PHASE7_ADVERSARIAL_REVIEW_MANIFEST_RELPATH",
    "PHASE7_OFFLINE_REPROOF_TEST_OWNERS_V1",
    "PHASE7_ADJUDICATION_CONTRACT_ID",
    "Phase7ReadinessAdjudicationError",
    "Phase7ReadinessAdjudicationV1",
    "WORK_PACKAGE_ID",
    "adjudicate_ghv_current_okx_phase7_readiness_v1",
    "adjudicate_phase7_adversarial_contract_review_v1",
    "compute_manifest_provenance_body_sha256_v1",
    "compute_reviewed_contract_paths_sha256_v1",
    "execute_phase7_offline_reproof_pytest_v1",
    "git_is_ancestor_commit_v1",
    "parse_manifest_provenance_anchor_from_review_doc_v1",
    "resolve_git_origin_main_sha_v1",
    "verify_current_baseline_checkout_v1",
]
