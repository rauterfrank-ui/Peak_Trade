#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))
sys.path.insert(0, str(REPO_ROOT))

from research.linear_evidence.drift import RollingLinearDriftInputV1, fit_rolling_linear_drift


def _fixture_records() -> list[RollingLinearDriftInputV1]:
    records: list[RollingLinearDriftInputV1] = []
    for index in range(1, 19):
        hour = index - 1
        decision_time = f"2026-01-01T{hour:02d}:00:00Z"
        feature_time = decision_time
        signal = float(index)
        if index <= 9:
            target = 0.5 * signal + 0.1
        else:
            target = 2.5 * signal - 1.0
        records.append(
            RollingLinearDriftInputV1(
                instrument_id="PF_ETHUSD",
                decision_time=decision_time,
                feature_availability_time=feature_time,
                target=target,
                features={"signal": signal, "aux": float(index % 3)},
            )
        )
    return records


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    evidence = fit_rolling_linear_drift(_fixture_records(), window_size=6, min_samples=4)
    report = evidence.to_dict()
    report.update(
        {
            "offline_only": True,
            "system_economic_evidence_admissible": False,
            "runtime_rewire_admissible": False,
            "promotion_pass_authority": False,
        }
    )

    report_path = out / "rolling_linear_drift_evidence_v1.json"
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(f"STATUS={evidence.status}")
    print("AUTHORITY_EFFECT=NONE")
    print("RUNTIME_EFFECT=NONE")
    print(f"DRIFT_SCORE={evidence.drift_score}")
    print(f"REASON_CODES={','.join(evidence.reason_codes) or 'NONE'}")
    print(f"REPORT={report_path}")
    return (
        0
        if evidence.status
        in {
            "DIAGNOSTIC_ONLY",
            "ROBUSTNESS_FAILED",
            "RANK_DEFICIENT_BLOCKED",
            "INSUFFICIENT_DATA",
        }
        else 1
    )


if __name__ == "__main__":
    raise SystemExit(main())
