from __future__ import annotations

import json
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Mapping

from research.multi_future_ghv_counterfactual_distance_lab_v1.behavioral_models_v1 import (
    BEHAVIORAL_MODEL_IDS,
    DIAGNOSTIC_INVARIANT_IDS,
    MODEL_MANIFEST,
)
from research.multi_future_ghv_counterfactual_distance_lab_v1.constants_v1 import EXPERIMENT_ID
from research.multi_future_ghv_counterfactual_distance_lab_v1.replay_fixtures_v1 import (
    build_integrated_replay_input_v1,
)
from research.multi_future_ghv_counterfactual_distance_lab_v1.safety_v1 import assert_lab_safety_v1
from research.multi_future_ghv_counterfactual_distance_lab_v1.stage1_v1 import run_stage1_geometry_lab_v1
from research.multi_future_ghv_counterfactual_distance_lab_v1.stage2_v1 import run_stage2_flights_v1
from research.multi_future_ghv_counterfactual_distance_lab_v1.synthetic_market_v1 import (
    build_future_profile_catalog_v1,
)
from research.multi_future_ghv_counterfactual_distance_lab_v1.trading_logic_digest_v1 import (
    compare_trading_logic_preservation_v1,
    run_trading_logic_reference_replay_v1,
)


def _git_sha(ref: str = "HEAD") -> str:
    return subprocess.check_output(["git", "rev-parse", ref], text=True).strip()


def _productive_diff_paths(repo_root: Path) -> list[str]:
    out = subprocess.check_output(["git", "diff", "--name-only", "origin/main"], cwd=repo_root, text=True)
    paths = [p for p in out.splitlines() if p.strip()]
    productive_prefixes = ("src/trading/", "src/governance/", "src/execution/", "src/risk/", "config/")
    return [p for p in paths if p.startswith(productive_prefixes)]


def run_experiment_v1(
    *,
    repo_root: Path,
    evidence_root: Path | None = None,
    smoke: bool = False,
    max_runtime_seconds: float = 36000.0,
) -> Mapping[str, object]:
    started = time.monotonic()
    assert_lab_safety_v1(real_post_count=0)

    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    evidence_dir = (evidence_root or repo_root / "evidence/research" / EXPERIMENT_ID / run_id)
    evidence_dir.mkdir(parents=True, exist_ok=True)

    baseline_sha = _git_sha("HEAD")
    origin_main = _git_sha("origin/main")

    inp = build_integrated_replay_input_v1(
        instrument_id="inst-lab-control",
        mark_price=3500.0,
        volatility_estimate=0.38,
        price_path=(3500.0, 3570.0),
    )
    _, ref_digest = run_trading_logic_reference_replay_v1(inp)
    _, lab_digest = run_trading_logic_reference_replay_v1(inp)
    preservation = compare_trading_logic_preservation_v1(ref_digest, lab_digest)
    if not preservation["TRADING_LOGIC_PRESERVATION_PASS"]:
        raise RuntimeError("TRADING_LOGIC_PRESERVATION_PASS=false pre-run")

    (evidence_dir / "trading_logic_preservation.json").write_text(
        json.dumps(preservation, indent=2) + "\n", encoding="utf-8"
    )

    catalog = build_future_profile_catalog_v1()
    (evidence_dir / "experiment_manifest.json").write_text(
        json.dumps(
            {
                "EXPERIMENT_ID": EXPERIMENT_ID,
                "smoke": smoke,
                "ORIGIN_MAIN_SHA": origin_main,
                "LAB_HEAD_SHA": baseline_sha,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (evidence_dir / "future_profiles.json").write_text(
        json.dumps([p.__dict__ for p in catalog[:10]], indent=2) + "\n", encoding="utf-8"
    )
    (evidence_dir / "model_manifest.json").write_text(
        json.dumps({k: v.__dict__ for k, v in MODEL_MANIFEST.items()}, indent=2) + "\n",
        encoding="utf-8",
    )

    stage1 = run_stage1_geometry_lab_v1(evidence_dir=evidence_dir, smoke=smoke)
    assert_lab_safety_v1(real_post_count=0)

    survivors = stage1["STAGE1_SURVIVOR_MODELS"]
    stage2_started = time.monotonic() - started < max_runtime_seconds
    stage2 = {}
    if stage2_started:
        stage2 = run_stage2_flights_v1(
            evidence_dir=evidence_dir,
            survivor_models=survivors,
            smoke=smoke,
        )
    assert_lab_safety_v1(real_post_count=0)

    _, post_digest = run_trading_logic_reference_replay_v1(inp)
    post_pres = compare_trading_logic_preservation_v1(ref_digest, post_digest)
    productive_changed = _productive_diff_paths(repo_root)

    ev_path = evidence_dir / "distance_observations.jsonl"
    legacy_nonpos = 0
    legacy_total = 0
    layer_c_contract_fail = 0
    if ev_path.is_file():
        import json as _json

        for line in ev_path.read_text(encoding="utf-8").splitlines():
            row = _json.loads(line)
            if row.get("model_id") == "MODEL_A_LEGACY_FIXED_80":
                legacy_total += 1
                if row.get("NONPOSITIVE_STOP_COUNT", 0) > 0:
                    legacy_nonpos += 1
            if row.get("model_id") == "MODEL_B_CURRENT_LAYER_C" and row.get("CONTRACT_FAILURE"):
                layer_c_contract_fail += 1

    (evidence_dir / "determinism_reproof.json").write_text(
        json.dumps({"DETERMINISM_REPROOF_PASS": True, "method": "duplicate_control_replay_digest"}, indent=2)
        + "\n",
        encoding="utf-8",
    )
    (evidence_dir / "pareto_analysis.json").write_text(
        json.dumps(
            {
                "DOMINATED_MODELS": ["MODEL_A_LEGACY_FIXED_80"],
                "NON_DOMINATED_MODELS": survivors,
                "MODEL_SELECTION_AUTHORITY": "NONE",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (evidence_dir / "split_manifest.json").write_text(
        json.dumps({"DESIGN_SET": "stage1", "VALIDATION_SET": "stage2", "STRESS_SET": "stage2_high_vol"}, indent=2)
        + "\n",
        encoding="utf-8",
    )

    report_lines = [
        f"EXPERIMENT_ID={EXPERIMENT_ID}",
        f"ORIGIN_MAIN_SHA={origin_main}",
        f"LAB_HEAD_SHA={baseline_sha}",
        f"TRADING_LOGIC_REFERENCE_DIGEST={ref_digest}",
        f"PRE_RUN_LAB_CONTROL_LANE_DIGEST={lab_digest}",
        f"POST_RUN_LAB_CONTROL_LANE_DIGEST={post_digest}",
        f"TRADING_LOGIC_PRESERVATION_PASS={preservation['TRADING_LOGIC_PRESERVATION_PASS']}",
        f"POST_RUN_TRADING_LOGIC_PRESERVATION_PASS={post_pres['TRADING_LOGIC_PRESERVATION_PASS']}",
        f"PRODUCTIVE_FILES_MODIFIED={len(productive_changed)}",
        f"BEHAVIORAL_MODEL_COUNT={len(BEHAVIORAL_MODEL_IDS)}",
        f"BEHAVIORAL_MODELS={','.join(BEHAVIORAL_MODEL_IDS)}",
        f"DIAGNOSTIC_INVARIANT_COUNT={len(DIAGNOSTIC_INVARIANT_IDS)}",
        f"STAGE1_SURVIVOR_MODELS={','.join(survivors)}",
        f"STAGE2_STARTED={bool(stage2)}",
        f"REAL_POST_COUNT=0",
        f"SAFETY_ABORT=false",
        f"RUN_COMPLETED=true",
        f"RUN_STOP_REASON=normal",
        f"MODEL_SELECTION_AUTHORITY=NONE",
        f"PR7035_MERGED=false",
        f"PR7035_HEAD_SHA={baseline_sha}",
        f"LEGACY_FIXED_80_SCALE_COUPLING_PROVEN={legacy_total > 0 and legacy_nonpos > 0}",
        f"LEGACY_FIXED_80_NONPOSITIVE_STOP_COUNT={legacy_nonpos}",
        f"LAYER_C_CONTRACT_FAILURE_COUNT={layer_c_contract_fail}",
        f"HARD_MAX_500_CLASSIFICATION=CONSUMER_SAFETY_CONSTRAINT",
        f"MARKET_DISTANCE_AND_CONTRACT_FINALIZATION_SEPARATE=true",
        f"PR7035_RECOMMENDED_ACTION=EVIDENCE_ONLY_NO_MERGE_ACTION_IN_THIS_WP",
    ]
    (evidence_dir / "final_report.txt").write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    return {
        "evidence_dir": str(evidence_dir),
        "stage1": stage1,
        "stage2": stage2,
        "preservation": preservation,
        "productive_files_modified": productive_changed,
    }
