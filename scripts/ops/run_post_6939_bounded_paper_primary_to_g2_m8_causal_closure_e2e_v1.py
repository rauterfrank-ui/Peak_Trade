"""Post-6939 bounded PAPER primary evidence → G2 → M4–M8 causal closure orchestrator v1."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

WP = "POST_6939_BOUNDED_PAPER_PRIMARY_G2_M8_CAUSAL_CLOSURE_V1"
APPROVAL = (
    REPO
    / "config/governance/post_6939_bounded_paper_primary_g2_closure_v1/owner_go_bounded_paper_approval_v1.md"
)
PACK = REPO / "evidence/ops/post_6939_bounded_paper_primary_g2_closure_v1"
RUN_TS = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _origin() -> str:
    return subprocess.check_output(["git", "rev-parse", "origin/main"], cwd=REPO, text=True).strip()


def continue_g2_from_primary_root(primary_root: Path, *, projection_inputs: dict) -> dict:
    from src.governance.governed_authority_map_atlas_guided_whole_system_g2_primary_causal_e2e_v1 import (
        classify_primary_archive_root_v1,
        PrimaryArchiveClassificationV1,
        run_g2_m8_continuation_evidence_v1,
    )
    from src.governance.governed_runtime_primary_to_offline_observation_projection_v1 import (
        GovernedRuntimePrimaryProjectionRequestV1,
        RuntimePrimarySourceModeV1,
    )

    report = classify_primary_archive_root_v1(primary_root, repo_root=REPO)
    if (
        report.classification is not PrimaryArchiveClassificationV1.OBSERVED_BOUNDED_RUNTIME
        or not report.projection_admit_ok
        or report.source_execution_mode != RuntimePrimarySourceModeV1.PAPER.value
    ):
        raise ValueError("PAPER_OBSERVED_PRIMARY_ARCHIVE_REQUIRED")
    req = GovernedRuntimePrimaryProjectionRequestV1(
        source_mode=RuntimePrimarySourceModeV1.PAPER,
        primary_evidence_root=primary_root,
        **projection_inputs,
    )
    g2 = run_g2_m8_continuation_evidence_v1(
        req,
        classification="OBSERVED_BOUNDED_RUNTIME_PRIMARY_ARCHIVE",
    )
    return {"classification": report.__dict__, "g2_m8": g2.__dict__}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("primary_root", nargs="?", type=Path)
    parser.add_argument(
        "--projection-request",
        type=Path,
        help="JSON identity and hypothesis fields for the G2 projection request",
    )
    args = parser.parse_args()
    if (args.primary_root is None) != (args.projection_request is None):
        parser.error("primary_root and --projection-request must be supplied together")
    out: dict = {
        "WP": WP,
        "BASELINE_SHA": _origin(),
        "APPROVAL_RECORD": str(APPROVAL),
        "E2E_RUN_ID": f"post6939-paper-{RUN_TS}-{uuid.uuid4().hex[:8]}",
    }
    if args.primary_root is not None:
        try:
            projection_inputs = json.loads(args.projection_request.read_bytes())
            if not isinstance(projection_inputs, dict):
                raise ValueError("PAPER_PROJECTION_REQUEST_OBJECT_REQUIRED")
            out["G2_CONTINUATION"] = continue_g2_from_primary_root(
                args.primary_root.resolve(), projection_inputs=projection_inputs
            )
        except (TypeError, ValueError, OSError) as exc:
            parser.error(str(exc))
    else:
        out["NOTE"] = "Pass the durable PAPER archive path and --projection-request after closeout."
    dest = PACK / RUN_TS
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "ORCHESTRATOR.json").write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
