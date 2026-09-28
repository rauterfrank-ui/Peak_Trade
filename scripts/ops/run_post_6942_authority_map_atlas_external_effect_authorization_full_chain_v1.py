"""Post-6942 Map/Atlas EXTERNAL_EFFECT_AUTHORIZATION full-chain forensic (no POST)."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

_RUN_TS = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
PACK = (
    REPO / "evidence/ops/post_6942_external_effect_authorization_full_chain_forensic_v1" / _RUN_TS
)
E2E_RUN_ID = f"eeaf6942-{_RUN_TS}-{uuid.uuid4().hex[:12]}"

from src.governance.post_6942_external_effect_authorization_full_chain_forensic_v1 import (  # noqa: E402
    ATLAS_CENSUS_REL,
    MAP_SOURCE_REL,
    WORKPACKAGE_ID,
    build_full_chain_forensic_report_v1,
)


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _origin_sha() -> str:
    return subprocess.check_output(["git", "rev-parse", "origin/main"], cwd=REPO, text=True).strip()


def _run_treasury_e2e() -> dict:
    proc = subprocess.run(
        [
            str(REPO / "scripts" / "pt"),
            "scripts/ops/run_whole_system_causal_closure_from_synthetic_treasury_zero_e2e_v1.py",
        ],
        cwd=REPO,
        check=False,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"treasury E2E failed rc={proc.returncode}\n{proc.stderr[-2000:]}")
    root = REPO / "evidence/ops/whole_system_causal_closure_from_synthetic_treasury_zero_v1"
    packs = sorted(p for p in root.iterdir() if p.is_dir())
    if not packs:
        raise RuntimeError("no treasury E2E evidence pack found")
    final_path = packs[-1] / "FINAL_REPORT.json"
    return json.loads(final_path.read_text(encoding="utf-8"))


def main() -> int:
    PACK.mkdir(parents=True, exist_ok=True)
    baseline = _origin_sha()
    treasury = _run_treasury_e2e()
    report = build_full_chain_forensic_report_v1(
        repo_root=REPO,
        baseline_sha=baseline,
        treasury_report=treasury,
        map_sha256=_sha256_file(REPO / MAP_SOURCE_REL),
        atlas_sha256=_sha256_file(REPO / ATLAS_CENSUS_REL),
        e2e_run_id=E2E_RUN_ID,
        evidence_root=str(PACK.relative_to(REPO)),
    )
    (PACK / "FINAL_REPORT.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    (PACK / "TREASURY_E2E_FINAL_REPORT.json").write_text(
        json.dumps(treasury, indent=2) + "\n", encoding="utf-8"
    )
    (PACK / "LINEAGE.json").write_text(
        json.dumps(
            {
                "wp": WORKPACKAGE_ID,
                "baseline_sha": baseline,
                "treasury_evidence": treasury.get("EVIDENCE_ROOT"),
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
                "WP": WORKPACKAGE_ID,
                "FIXPOINT_REACHED": report.get("FIXPOINT_REACHED"),
                "FIRST_IRREVERSIBLE_OPERATION": report.get("FIRST_IRREVERSIBLE_OPERATION"),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
