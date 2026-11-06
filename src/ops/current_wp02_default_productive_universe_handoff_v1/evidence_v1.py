"""Machine-readable WP-02 closure evidence."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from src.ops.current_wp02_default_productive_universe_handoff_v1.constants_v1 import (
    EVIDENCE_ROOT_RELATIVE,
    WORK_PACKAGE_ID,
)
from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    EXTERNAL_EFFECT_AUTHORIZED,
    POST_ALLOWED,
    REAL_VENUE_POST_ALLOWED,
)
from src.ops.hard_facts_system_closure_v1.authority_proof_v1 import (
    prove_hard_facts_authority_invariants_v1,
)


def _utc_stamp_v1() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def write_current_wp02_closure_evidence_v1(
    *,
    repo_root: Path,
    baseline_sha: str,
    tested_code_sha: str,
    chain_flags: Mapping[str, Any],
    ranking_observations: int,
    post_count: int = 0,
) -> Path:
    proof = prove_hard_facts_authority_invariants_v1()
    stamp = _utc_stamp_v1()
    out_dir = repo_root / EVIDENCE_ROOT_RELATIVE / stamp
    out_dir.mkdir(parents=True, exist_ok=True)
    payload: dict[str, Any] = {
        "artifact_kind": "CURRENT_WP02_CLOSURE_V1",
        "work_package_id": WORK_PACKAGE_ID,
        "utc_timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "BASELINE_SHA": baseline_sha,
        "TESTED_CODE_SHA": tested_code_sha,
        "cap21_refresh_invoked": bool(chain_flags.get("cap21_refresh_invoked")),
        "economic_md_source_canonical": bool(chain_flags.get("economic_md_source_canonical")),
        "real_b05_built": bool(chain_flags.get("real_b05_built")),
        "cap22_productive_real_assertion": bool(chain_flags.get("cap22_productive_real_assertion")),
        "external_ranking_inject_required": False,
        "hard_facts_handoff_invoked": bool(chain_flags.get("hard_facts_handoff_invoked")),
        "external_membership_inject_required": False,
        "membership_persisted": bool(chain_flags.get("membership_persisted")),
        "topology_persisted": bool(chain_flags.get("topology_persisted")),
        "ranking_observations": int(ranking_observations),
        "restart_mca_restored": bool(chain_flags.get("restart_mca_restored")),
        "synthetic_b05_rejected": bool(chain_flags.get("synthetic_b05_rejected")),
        "open_position_replacement_blocked": bool(
            chain_flags.get("open_position_replacement_blocked")
        ),
        "POST_COUNT": int(post_count),
        "POST_ALLOWED": POST_ALLOWED is True,
        "EXTERNAL_EFFECT_AUTHORIZED": EXTERNAL_EFFECT_AUTHORIZED is True,
        "REAL_VENUE_POST_ALLOWED": REAL_VENUE_POST_ALLOWED is True,
        "authority_invariants_ok": proof.ok is True,
        "ok": bool(chain_flags.get("ok")),
    }
    path = out_dir / "CURRENT_WP02_CLOSURE_V1.json"
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path
