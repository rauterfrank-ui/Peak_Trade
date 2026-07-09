#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))
sys.path.insert(0, str(REPO_ROOT))

from research.linear_evidence.factor_exposure import FactorExposureInputV1, fit_factor_exposure


def _fixture_records():
    return [
        FactorExposureInputV1(
            "PF_ETHUSD",
            1,
            0.010,
            {"market_beta": 0.10, "liquidity_beta": 0.05, "volatility_beta": 0.20},
        ),
        FactorExposureInputV1(
            "PF_ETHUSD",
            2,
            0.012,
            {"market_beta": 0.11, "liquidity_beta": 0.04, "volatility_beta": 0.19},
        ),
        FactorExposureInputV1(
            "PF_ETHUSD",
            3,
            0.009,
            {"market_beta": 0.09, "liquidity_beta": 0.06, "volatility_beta": 0.21},
        ),
        FactorExposureInputV1(
            "PF_SOLUSD",
            4,
            -0.004,
            {"market_beta": -0.02, "liquidity_beta": 0.03, "volatility_beta": 0.25},
        ),
        FactorExposureInputV1(
            "PF_SOLUSD",
            5,
            -0.006,
            {"market_beta": -0.03, "liquidity_beta": 0.02, "volatility_beta": 0.26},
        ),
        FactorExposureInputV1(
            "PF_SOLUSD",
            6,
            0.003,
            {"market_beta": 0.04, "liquidity_beta": 0.08, "volatility_beta": 0.18},
        ),
        FactorExposureInputV1(
            "PF_AVAXUSD",
            7,
            0.007,
            {"market_beta": 0.08, "liquidity_beta": 0.07, "volatility_beta": 0.17},
        ),
        FactorExposureInputV1(
            "PF_AVAXUSD",
            8,
            0.006,
            {"market_beta": 0.07, "liquidity_beta": 0.07, "volatility_beta": 0.16},
        ),
        FactorExposureInputV1(
            "PF_DOTUSD",
            9,
            -0.002,
            {"market_beta": 0.01, "liquidity_beta": 0.01, "volatility_beta": 0.22},
        ),
        FactorExposureInputV1(
            "PF_DOTUSD",
            10,
            0.001,
            {"market_beta": 0.03, "liquidity_beta": 0.02, "volatility_beta": 0.20},
        ),
    ]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    evidence = fit_factor_exposure(_fixture_records())
    report = evidence.to_dict()
    report.update(
        {
            "offline_only": True,
            "system_economic_evidence_admissible": False,
            "runtime_rewire_admissible": False,
            "promotion_pass_authority": False,
        }
    )

    (out / "factor_exposure_evidence_v1.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n"
    )
    print(f"STATUS={evidence.status}")
    print("AUTHORITY_EFFECT=NONE")
    print("RUNTIME_EFFECT=NONE")
    print(f"REPORT={out / 'factor_exposure_evidence_v1.json'}")
    return (
        0
        if evidence.status in {"DIAGNOSTIC_ONLY", "ROBUSTNESS_FAILED", "RANK_DEFICIENT_BLOCKED"}
        else 1
    )


if __name__ == "__main__":
    raise SystemExit(main())
