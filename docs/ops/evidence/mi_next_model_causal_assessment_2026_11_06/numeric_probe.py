"""Bounded existing-function probes; no MI trainer or runtime integration."""

from pathlib import Path
import ast
import json

import numpy as np

from src.research.linear_evidence.feature_matrix import build_feature_matrix_binding
from src.research.linear_evidence.fitters import fit_ols_lstsq
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.mi_offline_durable_evidence_store_v1 import (
    MiOfflineDurableEvidenceStoreV1,
)
from src.ops.peak_trade_economic_ranking_runtime_v1.score_construction_v1 import (
    build_balanced_movement_scores_v1,
)

REPO = Path(__file__).resolve().parents[4]
PACK = Path(__file__).resolve().parent


def probe():
    fits = {}
    for name, slope, heldout_delta in [
        ("base", 2.0, 0.0),
        ("training_changed", 3.0, 0.0),
        ("heldout_only_changed", 2.0, 100.0),
    ]:
        rows = [
            {
                "decision_time": f"2026-01-01T{i:02d}:00:00Z",
                "x": float(i),
                "y": 1.0 + slope * i + (heldout_delta if i >= 6 else 0.0),
            }
            for i in range(8)
        ]
        x, y, binding = build_feature_matrix_binding(rows, feature_names=("x",), target_name="y")
        fitted = fit_ols_lstsq(x, y, binding)
        coefficients = dict(fitted.coefficients)
        fits[name] = {
            "coefficients": coefficients,
            "analysis_calculated_value_at_x8": coefficients["intercept"] + 8.0 * coefficients["x"],
            "rmse_over_all_supplied_rows": fitted.diagnostics.rmse,
            "status": fitted.status,
            "runtime_effect": fitted.runtime_effect,
            "cost_policy_output": fitted.cost_policy_output,
        }
    assert np.isclose(fits["base"]["analysis_calculated_value_at_x8"], 17.0)
    assert np.isclose(fits["training_changed"]["analysis_calculated_value_at_x8"], 25.0)
    assert np.isclose(fits["heldout_only_changed"]["analysis_calculated_value_at_x8"], 17.0)

    original = REPO / "docs/ops/evidence/independent_market_observation_v1_2026_11_06"
    witness = json.loads((original / "example/witness.json").read_text())
    store = MiOfflineDurableEvidenceStoreV1(original / "example/store")
    records = store.list_records()
    assert len(records) == 1
    record = store.get_by_forecast_evidence_id(records[0]["forecast_evidence_id"])
    assert record is not None
    calibration = dict(record["calibration_evidence"]["calibration_result"])
    assert calibration == witness["calibration_result"]
    bridge = (
        REPO
        / "src/learning/market_intelligence_forecast_calibration_offline_stack_v1/mi_to_learning_evidence_bridge_v1.py"
    )
    body_keys = []
    for node in ast.walk(ast.parse(bridge.read_text())):
        if (
            isinstance(node, ast.Assign)
            and any(isinstance(t, ast.Name) and t.id == "body" for t in node.targets)
            and isinstance(node.value, ast.Dict)
        ):
            body_keys.append(
                sorted(
                    k.value
                    for k in node.value.keys
                    if isinstance(k, ast.Constant) and isinstance(k.value, str)
                )
            )
    assert body_keys and all("calibration_result" not in keys for keys in body_keys)

    ranking = {}
    for name, scale in [("movement_sample", 1.0), ("uniformly_quieter_sample", 0.000001)]:
        scores = build_balanced_movement_scores_v1(
            identities={"a": "A", "b": "B"},
            volatility_raw_by_id={"a": 0.02 * scale, "b": 0.01 * scale},
            amplitude_raw_by_id={"a": 0.2 * scale, "b": 0.1 * scale},
        )
        ranking[name] = [
            {
                "id": s.canonical_instrument_id,
                "volatility": s.volatility_raw,
                "amplitude": s.amplitude_raw,
                "score": s.balanced_movement_score,
            }
            for s in scores
        ]
    assert [(r["id"], r["score"]) for r in ranking["movement_sample"]] == [
        (r["id"], r["score"]) for r in ranking["uniformly_quieter_sample"]
    ]
    return {
        "scope": "existing pure OLS fit, existing native store cold read, projection AST and relative rank seam only",
        "ols_synthetic_controls": fits,
        "native_calibration_cold_read": calibration,
        "learning_projection_body_keys": body_keys,
        "relative_ranking_controls": ranking,
        "mi_training_or_inference_implemented": False,
        "new_model_artifact_persisted": False,
        "natural_quality_or_dp_improvement_proven": False,
    }


if __name__ == "__main__":
    print(json.dumps(probe(), ensure_ascii=False, indent=2))
