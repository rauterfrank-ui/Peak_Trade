from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, Mapping, MutableMapping, Sequence

from research.multi_future_ghv_counterfactual_distance_lab_v1.behavioral_models_v1 import (
    BEHAVIORAL_MODEL_IDS,
    diagnostic_cmc_vs_hysteresis_band_v1,
)
from research.multi_future_ghv_counterfactual_distance_lab_v1.constants_v1 import (
    EXPERIMENT_ID,
    PRICE_SCALES_P0,
    REGIME_IDS,
    STAGE1_SEED_COUNT,
    TARGET_STAGE1_CASES,
    VOLATILITY_LEVELS,
)
from research.multi_future_ghv_counterfactual_distance_lab_v1.contract_profiles_v1 import (
    synthetic_contract_profile_v1,
)
from research.multi_future_ghv_counterfactual_distance_lab_v1.distance_geometry_v1 import (
    evaluate_distance_geometry_v1,
)
from research.multi_future_ghv_counterfactual_distance_lab_v1.synthetic_market_v1 import (
    build_future_profile_catalog_v1,
    iter_stage1_case_ids,
    sigma_for_profile,
)


def _select_profiles_for_target(full_catalog, target_cases: int) -> Sequence:
    other = (
        len(BEHAVIORAL_MODEL_IDS)
        * len(PRICE_SCALES_P0)
        * len(VOLATILITY_LEVELS)
        * len(REGIME_IDS)
        * STAGE1_SEED_COUNT
        * 2
    )
    need = max(1, min(len(full_catalog), target_cases // other))
    return full_catalog[:need]


def run_stage1_geometry_lab_v1(
    *,
    evidence_dir: Path,
    smoke: bool = False,
) -> Mapping[str, object]:
    catalog = build_future_profile_catalog_v1()
    target = 200 if smoke else TARGET_STAGE1_CASES
    profiles = catalog[:2] if smoke else _select_profiles_for_target(catalog, target)
    seeds = (0,) if smoke else tuple(range(STAGE1_SEED_COUNT))
    price_scales = (1.0, 100.0) if smoke else PRICE_SCALES_P0
    vols = ("MEDIUM",) if smoke else VOLATILITY_LEVELS
    regimes = ("R01", "R02") if smoke else REGIME_IDS
    models = BEHAVIORAL_MODEL_IDS if not smoke else BEHAVIORAL_MODEL_IDS[:2]

    case_iter = iter_stage1_case_ids(
        models=models,
        price_scales=price_scales,
        vol_levels=vols,
        regimes=regimes,
        seeds=seeds,
        profiles=profiles,
    )

    distance_path = evidence_dir / "distance_observations.jsonl"
    failure_path = evidence_dir / "failure_reasons.jsonl"
    diag_path = evidence_dir / "diagnostic_invariants.json"
    diagnostics: list[dict[str, object]] = []
    model_fail_counts: MutableMapping[str, int] = {m: 0 for m in BEHAVIORAL_MODEL_IDS}
    model_case_counts: MutableMapping[str, int] = {m: 0 for m in BEHAVIORAL_MODEL_IDS}
    completed = 0

    profile_by_id = {p.future_profile_id: p for p in profiles}

    with distance_path.open("w", encoding="utf-8") as dist_f, failure_path.open(
        "w", encoding="utf-8"
    ) as fail_f:
        for case in case_iter:
            profile = profile_by_id[str(case["future_profile_id"])]
            p0 = float(case["price_scale"])
            vol_level = str(case["vol_level"])
            sigma = sigma_for_profile(
                vol_level=vol_level,
                profile=profile,
                mode=str(case["market_mode"]),
            )
            mark = p0
            contract = synthetic_contract_profile_v1(
                future_profile_id=profile.future_profile_id,
                p0=p0,
            )
            model_id = str(case["model_id"])
            geom = evaluate_distance_geometry_v1(
                model_id=model_id,
                mark_price=mark,
                volatility_estimate=sigma,
                contract=contract,
            )
            row = {
                "EXPERIMENT_ID": EXPERIMENT_ID,
                **case,
                **geom,
                "contract_profile_id": contract.profile_id,
            }
            dist_f.write(json.dumps(row, sort_keys=True) + "\n")
            model_case_counts[model_id] = model_case_counts.get(model_id, 0) + 1
            if geom.get("GENERALIZATION_FAILURE"):
                model_fail_counts[model_id] = model_fail_counts.get(model_id, 0) + 1
                fail_f.write(json.dumps(row, sort_keys=True) + "\n")
            if completed < 500:
                band = sigma * mark
                diagnostics.append(
                    diagnostic_cmc_vs_hysteresis_band_v1(
                        mark_price=mark,
                        volatility_estimate=sigma,
                        hysteresis_band=band,
                    )
                )
            completed += 1

    survivors: list[str] = []
    for m in BEHAVIORAL_MODEL_IDS:
        total = model_case_counts.get(m, 0)
        if total <= 0:
            continue
        fail_rate = model_fail_counts.get(m, 0) / total
        if m == "MODEL_A_LEGACY_FIXED_80":
            continue
        if fail_rate >= 0.05:
            continue
        survivors.append(m)
    if not survivors:
        survivors = ["MODEL_B_CURRENT_LAYER_C"]

    diag_path.write_text(
        json.dumps({"diagnostics_sample": diagnostics, "count": len(diagnostics)}, indent=2)
        + "\n",
        encoding="utf-8",
    )
    summary = {
        "STAGE1_COMPLETED_FLIGHTS": completed,
        "STAGE1_PLANNED_FLIGHTS": completed,
        "STAGE1_GENERALIZATION_FAILURES": sum(model_fail_counts.values()),
        "STAGE1_SURVIVOR_MODELS": survivors,
        "profile_count": len(profiles),
    }
    (evidence_dir / "stage1_summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    return summary
