"""Check formatting while retaining exact byte guards on frozen sources.

Every exception must match both the frozen Git object and the current file.
Exceptions cannot admit edits or extend the protected path set.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[2]
MANIFEST = "scripts/ci/ruff_frozen_format_exceptions_v1.json"
MODEL = "docs/system_atlas/source/current-model.json"
PROTECTED = frozenset(
    {
        "src/research/multi_future_ghv_counterfactual_distance_lab_v1/counterfactual_replay_v1.py",
        "src/research/multi_future_ghv_counterfactual_distance_lab_v1/distance_geometry_v1.py",
        "src/research/multi_future_ghv_counterfactual_distance_lab_v1/runner_v1.py",
        "src/research/multi_future_ghv_counterfactual_distance_lab_v1/stage1_v1.py",
        "src/research/multi_future_ghv_counterfactual_distance_lab_v1/stage2_v1.py",
        "src/research/multi_future_ghv_counterfactual_distance_lab_v2/aggregate_v2.py",
        "src/research/multi_future_ghv_counterfactual_distance_lab_v2/cycle_observation_v2.py",
        "src/research/multi_future_ghv_counterfactual_distance_lab_v2/replay_input_v2.py",
        "src/research/multi_future_ghv_counterfactual_distance_lab_v2/runner_v2.py",
        "src/research/multi_future_ghv_counterfactual_distance_lab_v2/safety_v2.py",
        "src/research/multi_future_ghv_counterfactual_distance_lab_v2/stage2_runner_v2.py",
        "src/research/multi_future_ghv_counterfactual_distance_lab_v3/aggregate_v3.py",
        "src/research/multi_future_ghv_counterfactual_distance_lab_v3/proof_gates_v3.py",
        "src/research/multi_future_ghv_counterfactual_distance_lab_v3/replay_state_v3.py",
        "src/research/multi_future_ghv_counterfactual_distance_lab_v3/runner_v3.py",
        "src/research/multi_future_ghv_counterfactual_distance_lab_v3/stage2_runner_v3.py",
        "src/research/multi_future_ghv_counterfactual_distance_lab_v3/state_carrier_v3.py",
        "tests/research/test_btc_common_research_admission_v1.py",
        "tests/research/test_multi_future_ghv_counterfactual_distance_lab_v2.py",
        "tests/research/test_pit_futures_instrument_lifecycle_registry_v1.py",
        "tests/trading/master_v2/test_deterministic_scope_event_generator_v1.py",
        "src/governance/pre_live_fresh_state_and_slice_baseline_convergence_v1.py",
        "src/ops/full_core_live_path_composition_root_v1/current_productive_g17_typed_vol_cmc_bind_v1.py",
        "src/trading/master_v2/canonical_core_runtime_integration_bridge_v0.py",
        "src/trading/master_v2/canonical_scope_initialization_v1.py",
        "src/trading/master_v2/deterministic_scope_event_generator_v1.py",
        "src/trading/master_v2/directional_assessment_v1.py",
        "src/trading/master_v2/double_play_composition_matrix_v1.py",
        "src/trading/master_v2/double_play_entry_exit_policy_v0.py",
        "src/trading/master_v2/double_play_futures_input.py",
        "src/trading/master_v2/integrated_offline_trading_logic_replay_v1.py",
    }
)


def _git(root: Path, *args: str) -> bytes:
    return subprocess.check_output(["git", *args], cwd=root)


def frozen_exceptions(root: Path) -> list[str]:
    manifest = json.loads((root / MANIFEST).read_bytes())
    model = json.loads((root / MODEL).read_bytes())
    if (
        manifest.get("schema") != "peaktrade.ruff_frozen_format_exceptions.v1"
        or manifest.get("authority") != "NONE"
        or manifest.get("runtime_authorization_effect") != "NONE"
        or manifest.get("source_commit") != model["source_commit"]
        or manifest.get("source_tag") != model["source_tag"]
        or _git(root, "rev-parse", model["source_tag"] + "^{commit}").decode().strip()
        != model["source_commit"]
    ):
        raise ValueError("FROZEN_FORMAT_SOURCE_BINDING_INVALID")
    rows = manifest["files"]
    if len(rows) != len(PROTECTED) or {row["path"] for row in rows} != PROTECTED:
        raise ValueError("FROZEN_FORMAT_SCOPE_INVALID")
    for row in rows:
        rel = row["path"]
        path = root / rel
        original = _git(root, "show", model["source_commit"] + ":" + rel)
        if (
            path.is_symlink()
            or not path.is_file()
            or not row.get("reason")
            or hashlib.sha256(original).hexdigest() != row["sha256"]
            or path.read_bytes() != original
        ):
            raise ValueError("FROZEN_FORMAT_SOURCE_CHANGED:" + rel)
    return sorted(PROTECTED)


def check_format(root: Path, ruff: str) -> int:
    exceptions = frozen_exceptions(root)
    print(f"FROZEN_FORMAT_BYTES_VERIFIED={len(exceptions)}", flush=True)
    return subprocess.run(
        [
            ruff,
            "format",
            "--check",
            "--force-exclude",
            "--exclude",
            ",".join(exceptions),
            "src/",
            "tests/",
            "scripts/",
        ],
        cwd=root,
        check=False,
    ).returncode


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    parser.add_argument("--ruff", default="ruff")
    args = parser.parse_args()
    try:
        return check_format(args.repo_root.resolve(), args.ruff)
    except (ValueError, KeyError, OSError, subprocess.CalledProcessError) as exc:
        print(f"FROZEN_FORMAT_CHECK_FAILED:{exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
