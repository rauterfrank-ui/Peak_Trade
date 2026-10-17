"""Content-bound Owner-GO pins for protected-surface diffs against ``origin/main``.

A protected path may differ from ``origin/main`` only when BOTH its exact
working-tree content sha256 AND its ``origin/main`` blob id equal a pin bound to
an Owner GO. Any other edit, any further new file, a deletion, or a moved
``origin/main`` base for that path is reported as unauthorized. Untracked files
under a protected path are included.
"""

from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path
from typing import Iterable, Mapping, Optional

REPO_ROOT = Path(__file__).resolve().parents[2]

AUTHORIZATION_B5_B6_V1_V2 = (
    "OWNER_GO=IMPLEMENT_B5_B5RR_B6_SECURITY_REMEDIATION_V1"
    "+OWNER_GO=IMPLEMENT_B5_B6_SECURITY_CLOSURE_V2"
    "+OWNER_GO=IMPLEMENT_B5_B6_FINAL_SECURITY_REVIEW_V3"
)
AUTHORIZATION_B6_LINUX_LEDGER_V5 = (
    AUTHORIZATION_B5_B6_V1_V2 + "+OWNER_GO=IMPLEMENT_B6_LINUX_LEDGER_ALLOWLIST_FIX_V5"
)
AUTHORIZATION_WP_B5_KILL_SWITCH_CLOSURE = (
    "OWNER_IMPLEMENTATION_GO=WP_B5_KILL_SWITCH_SAFETY_AND_RECOVERY_CLOSURE"
)
NEW_FILE_BASE_BLOB = None

# path -> (authorization, origin/main blob id or None for new file, content sha256)
AUTHORIZED_PROTECTED_SURFACE_CHANGES_V1: Mapping[str, tuple[str, Optional[str], str]] = {
    "src/ops/full_core_live_path_composition_root_v1/current_full_system_offline_e2e_integration_proof_v1.py": (
        AUTHORIZATION_B5_B6_V1_V2,
        "bc4bd326ab14b7aa2b74673e087958760794bf0c",
        "c4d18d780d16a573db7e453a2451ea46378cdd6e2d5a7ad6ed3ffe3437a1af3b",
    ),
    "src/ops/full_core_live_path_composition_root_v1/current_productive_actual_venue_post_owner_go_durable_consume_v1.py": (
        AUTHORIZATION_B5_B6_V1_V2,
        "a8bb51dae2af8b539d757f82e193da1349f98fc3",
        "2f6d0141e44b56802273e8d2fb9d3a23dbd8ed489f560196887000cf97701d64",
    ),
    "src/ops/full_core_live_path_composition_root_v1/current_productive_global_venue_effect_authority_ledger_v1.py": (
        AUTHORIZATION_B6_LINUX_LEDGER_V5,
        NEW_FILE_BASE_BLOB,
        "72f585cf1c37c00620a157d52ddf8ebbb545a889ccc960db9ee9414e412ab5b3",
    ),
    "src/ops/full_core_live_path_composition_root_v1/current_productive_one_shot_fresh_envelope_permit_mint_durable_consume_and_post_join_v1.py": (
        AUTHORIZATION_B5_B6_V1_V2,
        "dc2c2d32c13c0e6355af17195c632978ab08c534",
        "5b2f6237f733b35f50d3e37f0f9991645db0426c6d50b5a75bce1e6184574f9d",
    ),
    "src/ops/full_core_live_path_composition_root_v1/current_productive_post_path_kill_switch_gate_v1.py": (
        AUTHORIZATION_WP_B5_KILL_SWITCH_CLOSURE,
        "9fb2729bff6cf8f63d9ad04cf1be93d236e3f022",
        "f95a36596d081ca9ce0c72c25c7bb3ea30ab53c094db109da6d35ac42969f482",
    ),
    "src/ops/full_core_live_path_composition_root_v1/current_productive_risk_reduction_venue_proof_v1.py": (
        AUTHORIZATION_B5_B6_V1_V2,
        NEW_FILE_BASE_BLOB,
        "1a97dc6881b21d923362f3087ccdfdc423ef8a1083fcd764b5ca364c83f528b4",
    ),
    "src/ops/full_core_live_path_composition_root_v1/envelope_bound_external_effect_send_seam_v1.py": (
        AUTHORIZATION_B5_B6_V1_V2,
        "aee31be184f779b8dc0c550566e4aad87668fc77",
        "1026b1f6a4f00e28afe01b0838585d6bffe7d07b8fa66e2821bc89ec3ffa5679",
    ),
    "src/ops/full_core_live_path_composition_root_v1/external_effect_permit_durable_consume_v1.py": (
        AUTHORIZATION_B5_B6_V1_V2,
        "133ecfe3c5f54ffaafd1cc5f6b007506daef31d8",
        "b15271aa28c4c3b52a701b68c14295f1806acdf161e887bb1ff61aedc50abace",
    ),
    "src/ops/full_core_live_path_composition_root_v1/external_effect_permit_v1.py": (
        AUTHORIZATION_B5_B6_V1_V2,
        "6c93dcecbda2149e592b989ee40ac9042346a880",
        "142fc07da0923d6bc2058bae34782a390e2c45c27e3a2bd6c34d6e2c60af87a7",
    ),
    "src/ops/full_core_live_path_composition_root_v1/full_core_productive_http_post_transport_v1.py": (
        AUTHORIZATION_B5_B6_V1_V2,
        "e25bd22c93197d5c76ed5fee9b8c95d9f7a8e113",
        "1d26cdefd232c32fa3b3c0dd1ead2f95b782d12d1b912a7f206b02ea23336f5f",
    ),
}


def _git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=REPO_ROOT, check=True, capture_output=True, text=True
    ).stdout


def changed_protected_paths_v1(paths: Iterable[str]) -> list[str]:
    targets = list(paths)
    tracked = _git("diff", "--name-only", "origin/main", "--", *targets).split()
    untracked = _git("ls-files", "--others", "--exclude-standard", "--", *targets).split()
    return sorted(set(tracked) | set(untracked))


def _origin_main_blob_v1(path: str) -> Optional[str]:
    proc = subprocess.run(
        ["git", "rev-parse", "--verify", "--quiet", f"origin/main:{path}"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    return proc.stdout.strip() or None


def _content_sha256_v1(path: str) -> Optional[str]:
    target = REPO_ROOT / path
    if not target.is_file():
        return None
    return hashlib.sha256(target.read_bytes()).hexdigest()


def unauthorized_protected_changes_v1(paths: Iterable[str]) -> list[str]:
    out: list[str] = []
    for rel in changed_protected_paths_v1(paths):
        pin = AUTHORIZED_PROTECTED_SURFACE_CHANGES_V1.get(rel)
        if pin is None:
            out.append(f"{rel}:NOT_PINNED")
            continue
        _authorization, base_blob, content_sha = pin
        if _origin_main_blob_v1(rel) != base_blob:
            out.append(f"{rel}:ORIGIN_MAIN_BASE_MOVED")
        elif _content_sha256_v1(rel) != content_sha:
            out.append(f"{rel}:CONTENT_NOT_PINNED")
    return out
