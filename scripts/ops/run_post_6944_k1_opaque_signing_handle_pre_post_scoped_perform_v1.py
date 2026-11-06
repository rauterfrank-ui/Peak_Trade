"""Post-6944 scoped K1 PRE-POST perform orchestrator (no venue POST)."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

_RUN_TS = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
PACK = REPO / "evidence/ops/post_6944_k1_opaque_signing_handle_pre_post_scoped_perform_v1" / _RUN_TS
E2E_RUN_ID = f"k1pp6944-{_RUN_TS}-{uuid.uuid4().hex[:12]}"

from src.governance.post_6944_k1_opaque_signing_handle_pre_post_scoped_perform_v1 import (  # noqa: E402
    ATLAS_CENSUS_REL,
    MAP_SOURCE_REL,
    OWNER_GO_TOKEN,
    WORKPACKAGE_ID,
    build_k1_pre_post_perform_report_v1,
    perform_scoped_k1_pre_post_boundary_v1,
)


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _origin_sha() -> str:
    return subprocess.check_output(["git", "rev-parse", "origin/main"], cwd=REPO, text=True).strip()


def _run_post_6942_chain() -> dict:
    proc = subprocess.run(
        [
            str(REPO / "scripts" / "pt"),
            "scripts/ops/run_post_6942_authority_map_atlas_external_effect_authorization_full_chain_v1.py",
        ],
        cwd=REPO,
        check=False,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"post-6942 chain failed rc={proc.returncode}\n{proc.stderr[-2000:]}")
    root = REPO / "evidence/ops/post_6942_external_effect_authorization_full_chain_forensic_v1"
    packs = sorted(p for p in root.iterdir() if p.is_dir())
    if not packs:
        raise RuntimeError("no post-6942 evidence pack")
    return json.loads((packs[-1] / "FINAL_REPORT.json").read_text(encoding="utf-8"))


def _latest_post_6943_report() -> dict | None:
    root = REPO / "evidence/ops/post_6943_real_keychain_material_load_scoped_perform_v1"
    if not root.is_dir():
        return None
    packs = sorted(p for p in root.iterdir() if p.is_dir())
    if not packs:
        return None
    path = packs[-1] / "FINAL_REPORT.json"
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    token = os.environ.get("SCOPED_OWNER_GO_TOKEN", "").strip()
    if token != OWNER_GO_TOKEN:
        print(
            json.dumps(
                {
                    "ERROR": "SCOPED_OWNER_GO_TOKEN_ENV_REQUIRED",
                    "REQUIRED": OWNER_GO_TOKEN,
                },
                indent=2,
            )
        )
        return 2

    PACK.mkdir(parents=True, exist_ok=True)
    baseline = _origin_sha()
    chain_6942 = _run_post_6942_chain()
    chain_6943 = _latest_post_6943_report()
    perform = perform_scoped_k1_pre_post_boundary_v1(
        repo_root=REPO,
        owner_go_token=token,
        use_productive_macos_backend=True,
        backend=None,
    )
    report = build_k1_pre_post_perform_report_v1(
        repo_root=REPO,
        baseline_sha=baseline,
        owner_go_token=token,
        perform_payload=perform,
        chain_6942_report=chain_6942,
        material_load_6943_report=chain_6943,
        map_sha256=_sha256_file(REPO / MAP_SOURCE_REL),
        atlas_sha256=_sha256_file(REPO / ATLAS_CENSUS_REL),
        e2e_run_id=E2E_RUN_ID,
        evidence_root=str(PACK.relative_to(REPO)),
    )
    (PACK / "FINAL_REPORT.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    (PACK / "LINEAGE.json").write_text(
        json.dumps(
            {
                "wp": WORKPACKAGE_ID,
                "baseline_sha": baseline,
                "post_6942_evidence": chain_6942.get("EVIDENCE_ROOT"),
                "post_6943_evidence": (chain_6943 or {}).get("EVIDENCE_ROOT"),
                "e2e_run_id": E2E_RUN_ID,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "FINAL_REPORT": str(PACK / "FINAL_REPORT.json"),
                "K1_HANDLE_CREATED": report.get("K1_HANDLE_CREATED"),
                "SIGNING_PERFORMED": report.get("SIGNING_PERFORMED"),
                "FIXPOINT_REACHED": report.get("FIXPOINT_REACHED"),
                "FIRST_REAL_BLOCKER": report.get("FIRST_REAL_BLOCKER"),
            },
            indent=2,
        )
    )
    return 0 if report.get("FIXPOINT_REACHED") else 1


if __name__ == "__main__":
    raise SystemExit(main())
