"""Cap 6.3 MODEL_C cross-instrument validation (pre-metadata scope).

Consumes Cap 2.3 selection + Cap 2.2 ranking candidate context.
Does not rewire selection, bind MODEL_C, or consume the metadata gate.
"""

from __future__ import annotations

import ast
import hashlib
import inspect
import json
from pathlib import Path
from typing import Any

from src.ops.derive_scope_event_distances_v1.derive_v1 import derive_scope_event_distances_v1
from src.ops.derive_scope_event_distances_v1.golden_vectors_v1 import GOLDEN_VALID_VECTORS_V1

REPO_ROOT = Path(__file__).resolve().parents[2]
CONTRACT = REPO_ROOT / "docs/ops/specs/CAP63_DYNAMIC_DERIVATION_CROSS_INSTRUMENT_VALIDATION_V1.md"
PROTOCOL = (
    REPO_ROOT / "docs/ops/specs/CAP63_DYNAMIC_DERIVATION_CROSS_INSTRUMENT_VALIDATION_PROTOCOL_V1.md"
)
RANKING_SNAPSHOT = (
    REPO_ROOT
    / "docs/evidence/capability_2_2_productive_futures_ranking_producer_v1"
    / "productive_ranking"
    / "productive_futures_ranking_snapshot_v1.json"
)
SELECTION_SNAPSHOT = (
    REPO_ROOT
    / "docs/evidence/capability_2_3_single_selected_future_policy_v1"
    / "productive_selection"
    / "single_selected_future_selection_v1.json"
)
CAP62_GATE_RESULTS = (
    REPO_ROOT
    / "docs/evidence/capability_6_2_dynamic_scope_persistence_binding_v1"
    / "productive_binding"
    / "dynamic_scope_gate_results_v1.json"
)
EVIDENCE_DIR = REPO_ROOT / "evidence/ops/cap63_dynamic_derivation_cross_instrument_validation_v1"
INPUTS_PATH = EVIDENCE_DIR / "INPUTS.json"
RESULTS_PATH = EVIDENCE_DIR / "RESULTS.json"
SUMMARY_PATH = EVIDENCE_DIR / "SUMMARY.json"
MANIFEST_PATH = EVIDENCE_DIR / "MANIFEST.sha256"
DERIVE_SOURCE = REPO_ROOT / "src/ops/derive_scope_event_distances_v1/derive_v1.py"
PACKAGE_ROOT = REPO_ROOT / "src/ops/derive_scope_event_distances_v1"

PRODUCTIVE_CONSUMER_ROOTS: tuple[str, ...] = (
    "src/trading",
    "src/live",
    "src/execution",
    "src/execution_simple",
    "src/ops/decision_config_ownership_and_consumer_closure_v1",
    "src/ops/dynamic_scope_persistence_binding_v1",
    "src/ops/exit_policy_producer_binding_v1",
)
_FORBIDDEN_MODULE_PREFIXES: tuple[str, ...] = (
    "src.ops.derive_scope_event_distances_v1",
    "ops.derive_scope_event_distances_v1",
)

EXPECTED_ORIGIN_MAIN = "26b62aae2965bf146818a40e951513f9be05c5df"
BAND_SAMPLE_CLASS = "FORMULA_VALID_BAND_NOT_PER_INSTRUMENT_PRODUCTIVE_SNAPSHOT"


def _independent_formula(band: float) -> tuple[float, float, float]:
    up_distance = band
    adverse_exit_distance = band * (80.0 / 200.0)
    reversal_distance = band * (120.0 / 200.0)
    return up_distance, adverse_exit_distance, reversal_distance


def _load_json(path: Path) -> dict[str, Any]:
    loaded = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(loaded, dict)
    return loaded


def _canonical_json(payload: object) -> str:
    return json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True) + "\n"


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _iter_python_files(root: Path) -> tuple[Path, ...]:
    return tuple(sorted(path for path in root.rglob("*.py") if "__pycache__" not in path.parts))


def _imported_modules(path: Path) -> tuple[str, ...]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    names: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            names.append(node.module)
    return tuple(names)


def _is_forbidden_import(module: str) -> bool:
    return any(
        module == prefix or module.startswith(f"{prefix}.") for prefix in _FORBIDDEN_MODULE_PREFIXES
    )


def _productive_callgraph_hits() -> list[str]:
    hits: list[str] = []
    for root in PRODUCTIVE_CONSUMER_ROOTS:
        for path in _iter_python_files(REPO_ROOT / root):
            for module in _imported_modules(path):
                if _is_forbidden_import(module):
                    hits.append(f"{path.relative_to(REPO_ROOT)}:{module}")
    return hits


def _selectable_instruments() -> list[dict[str, Any]]:
    ranking = _load_json(RANKING_SNAPSHOT)
    ranked = ranking["ranked_candidates"]
    assert isinstance(ranked, list)
    instruments: list[dict[str, Any]] = []
    for row in ranked:
        assert isinstance(row, dict)
        if row.get("eligibility_status") != "ELIGIBLE":
            continue
        instrument_id = row["canonical_instrument_id"]
        venue_native_id = row["venue_native_id"]
        rank = row["rank"]
        assert isinstance(instrument_id, str)
        assert isinstance(venue_native_id, str)
        assert isinstance(rank, int)
        instruments.append(
            {
                "canonical_instrument_id": instrument_id,
                "venue_native_id": venue_native_id,
                "rank": rank,
                "eligibility_status": "ELIGIBLE",
            }
        )
    return instruments


def _cap62_band_exemplar() -> dict[str, Any]:
    payload = _load_json(CAP62_GATE_RESULTS)
    scope = payload["restart_results"]["loaded_runtime_scope"]
    assert isinstance(scope, dict)
    band = scope["current_hysteresis_band"]
    instrument_id = payload["gate_flags"]["instrument_id"]
    assert type(band) is float
    assert isinstance(instrument_id, str)
    return {
        "evidence_path": str(CAP62_GATE_RESULTS.relative_to(REPO_ROOT)),
        "instrument_id": instrument_id,
        "current_hysteresis_band": band,
        "in_cap23_selectable_set": False,
        "used_as_productive_sample_for_cap23_instrument": False,
        "class": "BAND_FIELD_OWNER_EXEMPLAR_NOT_UNIVERSE_MEMBER",
        "epistemic_class": "FORENSIC_RAW_EVIDENCE",
    }


def build_inputs_v1() -> dict[str, Any]:
    instruments = _selectable_instruments()
    selection = _load_json(SELECTION_SNAPSHOT)
    selected_id = selection["instrument_id"]
    assert isinstance(selected_id, str)
    selectable_ids = {row["canonical_instrument_id"] for row in instruments}
    assert selected_id in selectable_ids
    ranking = _load_json(RANKING_SNAPSHOT)
    return {
        "EXPECTED_ORIGIN_MAIN": EXPECTED_ORIGIN_MAIN,
        "OWNER_GO": "OWNER_GO_BOUNDED_CAP63_DYNAMIC_DERIVATION_CROSS_INSTRUMENT_VALIDATION_V1",
        "PRE_METADATA_SCOPE": True,
        "SELECTION_OWNER": "CAPABILITY_2_3_SINGLE_SELECTED_FUTURE_POLICY_V1",
        "SELECTION_OWNER_SPEC": (
            "docs/ops/specs/MASTER_V2_CAPABILITY_2_3_SINGLE_SELECTED_FUTURE_POLICY_V1.md"
        ),
        "SELECTION_MODE": "SINGLE_SELECTED_FUTURE",
        "MAX_POSITIONS": 1,
        "MULTI_FUTURE_RUNTIME_AUTHORIZED": False,
        "THIS_VALIDATION_DEFINES_NO_INSTRUMENT_LIST": True,
        "VALIDATION_UNIVERSE_SOURCE": (
            "CAP22_EVIDENCE_RANKED_ELIGIBLE_CANDIDATES_AS_CAP23_SELECTABLE_CONTEXT"
        ),
        "VALIDATION_UNIVERSE_PATH": str(RANKING_SNAPSHOT.relative_to(REPO_ROOT)),
        "CAP22_EVIDENCE_RANKING_SNAPSHOT_ID": ranking["ranking_snapshot_id"],
        "CAP23_HISTORICAL_SELECTION_PATH": str(SELECTION_SNAPSHOT.relative_to(REPO_ROOT)),
        "CAP23_HISTORICAL_SELECTION_ID": selection["selection_id"],
        "CAP23_HISTORICAL_SELECTION_INSTRUMENT_ID": selected_id,
        "CAP23_HISTORICAL_SELECTION_RANKING_SNAPSHOT_ID": selection["ranking_snapshot_id"],
        "SNAPSHOT_IDENTITY_JOIN": "NOT_PROVEN_IDENTICAL",
        "SNAPSHOT_IDENTITY_JOIN_EPISTEMIC_CLASS": "OPEN_OR_CONTRADICTORY",
        "BAND_FIELD_OWNER": (
            "trading.master_v2.double_play_state.RuntimeScopeState.current_hysteresis_band"
        ),
        "BAND_PRODUCER": "trading.master_v2.double_play_state.update_dynamic_boundaries",
        "OBSERVED_PER_INSTRUMENT_RUNTIME_SCOPE_STATE_BAND": "ABSENT_ON_ORIGIN_MAIN",
        "BAND_SAMPLE_CLASS": BAND_SAMPLE_CLASS,
        "BAND_SAMPLE_OWNER": "src/ops/derive_scope_event_distances_v1/golden_vectors_v1.py",
        "GOLDEN_VECTORS_ARE_FORMULA_VECTORS_NOT_INSTRUMENT_UNIVERSE": True,
        "SYNTHETIC_BAND_SET_AS_PRODUCTIVE_AUTHORITY": False,
        "CAP62_BAND_EXEMPLAR": _cap62_band_exemplar(),
        "FORMULA": {
            "up_distance": "current_hysteresis_band",
            "adverse_exit_distance": "up_distance * (80.0 / 200.0)",
            "reversal_distance": "up_distance * (120.0 / 200.0)",
        },
        "EXCLUSIONS": {
            "TICK_ALIGNMENT": "NOT_IN_SCOPE",
            "LOT_ALIGNMENT": "NOT_IN_SCOPE",
            "CTVAL_ALIGNMENT": "NOT_IN_SCOPE",
            "PRICE_SCALE_ALIGNMENT": "NOT_IN_SCOPE",
            "VENUE_EXECUTABILITY": "NOT_IN_SCOPE",
            "GENERATOR_HARD_MAX_POLICY": "NOT_IN_SCOPE_HERE",
            "METADATA_GATE_CONSUMED": False,
            "MODEL_C_RUNTIME_BIND_AUTHORIZED": False,
        },
        "selectable_instruments": instruments,
    }


def build_results_v1(inputs: dict[str, Any]) -> dict[str, Any]:
    signature = inspect.signature(derive_scope_event_distances_v1)
    parameter_names = list(signature.parameters)
    derive_source = DERIVE_SOURCE.read_text(encoding="utf-8")
    samples: list[dict[str, Any]] = []
    oq_c1_failures: list[str] = []
    oq_c2_failures: list[str] = []
    geometry_failures: list[str] = []
    fallback_failures: list[str] = []
    for instrument in inputs["selectable_instruments"]:
        assert isinstance(instrument, dict)
        for vector in GOLDEN_VALID_VECTORS_V1:
            band = vector.current_hysteresis_band
            result = derive_scope_event_distances_v1(band)
            expected = _independent_formula(band)
            oq_c1 = result.ok is True and result.up_distance == band == expected[0]
            oq_c2 = (
                result.ok is True
                and result.adverse_exit_distance == expected[1]
                and result.reversal_distance == expected[2]
                and result.up_distance is not None
                and result.adverse_exit_distance == result.up_distance * (80.0 / 200.0)
                and result.reversal_distance == result.up_distance * (120.0 / 200.0)
            )
            geometry = (
                result.ok is True
                and result.adverse_exit_distance is not None
                and result.reversal_distance is not None
                and result.up_distance is not None
                and result.adverse_exit_distance > 0.0
                and result.reversal_distance > 0.0
                and result.adverse_exit_distance <= result.reversal_distance
                and result.adverse_exit_distance < result.up_distance
            )
            fallback = False
            if band != 200.0 and result.ok is True:
                fallback = (
                    result.up_distance == 200.0
                    or result.adverse_exit_distance == 80.0
                    or result.reversal_distance == 120.0
                )
            sample_id = f"{instrument['venue_native_id']}:{vector.note}:{band}"
            if not oq_c1:
                oq_c1_failures.append(sample_id)
            if not oq_c2:
                oq_c2_failures.append(sample_id)
            if not geometry:
                geometry_failures.append(sample_id)
            if fallback:
                fallback_failures.append(sample_id)
            samples.append(
                {
                    "sample_id": sample_id,
                    "canonical_instrument_id": instrument["canonical_instrument_id"],
                    "venue_native_id": instrument["venue_native_id"],
                    "rank": instrument["rank"],
                    "band_sample_note": vector.note,
                    "band_sample_class": BAND_SAMPLE_CLASS,
                    "current_hysteresis_band": band,
                    "ok": result.ok,
                    "up_distance": result.up_distance,
                    "adverse_exit_distance": result.adverse_exit_distance,
                    "reversal_distance": result.reversal_distance,
                    "failure_reason": result.failure_reason,
                    "oq_c1_pass": oq_c1,
                    "oq_c2_pass": oq_c2,
                    "nested_geometry_pass": geometry,
                    "instrument_id_consumed": False,
                    "unauthorized_floor_or_clamp_or_cap63_fallback": fallback,
                }
            )
    callgraph_hits = _productive_callgraph_hits()
    oq_c1_pass = oq_c1_failures == []
    oq_c2_pass = oq_c2_failures == []
    geometry_pass = geometry_failures == []
    no_fallback = fallback_failures == []
    unbound = callgraph_hits == []
    no_instrument_id = parameter_names == ["current_hysteresis_band"] and (
        "instrument_id" not in derive_source
    )
    validation_pass = (
        oq_c1_pass and oq_c2_pass and geometry_pass and no_fallback and unbound and no_instrument_id
    )
    return {
        "EXPECTED_ORIGIN_MAIN": EXPECTED_ORIGIN_MAIN,
        "function_parameter_names": parameter_names,
        "derive_source_contains_instrument_id": "instrument_id" in derive_source,
        "PRODUCTIVE_CALLGRAPH_REACHABLE": not unbound,
        "productive_callgraph_hits": callgraph_hits,
        "sample_count": len(samples),
        "instrument_count": len(inputs["selectable_instruments"]),
        "valid_band_sample_count": len(GOLDEN_VALID_VECTORS_V1),
        "OQ_C1_PASS": oq_c1_pass,
        "OQ_C2_PASS": oq_c2_pass,
        "NESTED_GEOMETRY_PASS": geometry_pass,
        "UNAUTHORIZED_FLOOR_OR_CLAMP": not no_fallback,
        "FORMULA_UNCHANGED": True,
        "RATIOS_UNCHANGED": True,
        "oq_c1_failures": oq_c1_failures,
        "oq_c2_failures": oq_c2_failures,
        "geometry_failures": geometry_failures,
        "fallback_failures": fallback_failures,
        "VALIDATION_PASS": validation_pass,
        "samples": samples,
    }


def build_summary_v1(inputs: dict[str, Any], results: dict[str, Any]) -> dict[str, Any]:
    validation_pass = bool(results["VALIDATION_PASS"])
    return {
        "OWNER_GO": "OWNER_GO_BOUNDED_CAP63_DYNAMIC_DERIVATION_CROSS_INSTRUMENT_VALIDATION_V1",
        "OWNER_GO_STATUS": "CONSUMED" if validation_pass else "NOT_CONSUMED_VALIDATION_FAILED",
        "EXPECTED_ORIGIN_MAIN": EXPECTED_ORIGIN_MAIN,
        "EVIDENCE_AUTHORITY_EFFECT": "NONE",
        "EVIDENCE_IS_NOT_TRADING_AUTHORITY": True,
        "CROSS_INSTRUMENT_VALIDATION_PERFORMED": True,
        "VALIDATION_PROTOCOL_CONFORMANT": validation_pass,
        "VALIDATION_UNIVERSE_FROM_EXISTING_AUTHORITY": True,
        "BAND_PROVENANCE_VALID": True,
        "OQ_C1_PASS": results["OQ_C1_PASS"],
        "OQ_C2_PASS": results["OQ_C2_PASS"],
        "FORMULA_UNCHANGED": True,
        "RATIOS_UNCHANGED": True,
        "UNAUTHORIZED_FLOOR_OR_CLAMP": results["UNAUTHORIZED_FLOOR_OR_CLAMP"],
        "METADATA_GATE_CONSUMED": False,
        "TICK_LOT_CTVAL_PRICE_SCALE_METADATA_AUTHORITY": "AUTHORITY_MISSING",
        "MODEL_C_BOUND": False,
        "MODEL_C_RUNTIME_BIND_AUTHORIZED": False,
        "PRODUCTIVE_SWITCH_PATH_CHANGED": False,
        "PRODUCTIVE_CALLGRAPH_REACHABLE": results["PRODUCTIVE_CALLGRAPH_REACHABLE"],
        "OD2_ARMED_RESIDUAL": "OPEN_NO_MUTATION",
        "OD2_LAST_STEP": "KEEP_BOUND_DESTINATION_PREFIX",
        "CORE_LOGIC_CHANGE": False,
        "CURRENT_CANONICAL_MODEL": "MODEL_B",
        "EFFECTIVE_NUMERIC_VALUES_UNCHANGED": True,
        "instrument_count": results["instrument_count"],
        "sample_count": results["sample_count"],
        "OBSERVED_PER_INSTRUMENT_RUNTIME_SCOPE_STATE_BAND": inputs[
            "OBSERVED_PER_INSTRUMENT_RUNTIME_SCOPE_STATE_BAND"
        ],
        "BAND_SAMPLE_CLASS": BAND_SAMPLE_CLASS,
        "SYNTHETIC_BAND_SET_AS_PRODUCTIVE_AUTHORITY": False,
        "SNAPSHOT_IDENTITY_JOIN": inputs["SNAPSHOT_IDENTITY_JOIN"],
        "VALIDATION_PASS": validation_pass,
    }


def persist_evidence() -> dict[str, Any]:
    inputs = build_inputs_v1()
    results = build_results_v1(inputs)
    summary = build_summary_v1(inputs, results)
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    INPUTS_PATH.write_text(_canonical_json(inputs), encoding="utf-8")
    RESULTS_PATH.write_text(_canonical_json(results), encoding="utf-8")
    SUMMARY_PATH.write_text(_canonical_json(summary), encoding="utf-8")
    manifest_lines = []
    for name in ("INPUTS.json", "RESULTS.json", "SUMMARY.json"):
        digest = _sha256_text((EVIDENCE_DIR / name).read_text(encoding="utf-8"))
        manifest_lines.append(f"{digest}  {name}")
    MANIFEST_PATH.write_text("\n".join(manifest_lines) + "\n", encoding="utf-8")
    return summary


def test_protocol_file_remains_historical_protocol_owner() -> None:
    text = PROTOCOL.read_text(encoding="utf-8")
    assert "CROSS_INSTRUMENT_VALIDATION_PROTOCOL_OWNER=PERSISTED" in text
    assert "CROSS_INSTRUMENT_VALIDATION_PERFORMED=false" in text
    assert "THIS_PROTOCOL_DEFINES_NO_INSTRUMENT_LIST=true" in text


def test_universe_is_consumed_cap22_ranked_eligible_candidates() -> None:
    inputs = build_inputs_v1()
    instruments = inputs["selectable_instruments"]
    assert isinstance(instruments, list)
    assert len(instruments) == 20
    ranks = [row["rank"] for row in instruments]
    assert ranks == list(range(1, 21))
    assert inputs["CAP23_HISTORICAL_SELECTION_INSTRUMENT_ID"] == (
        "okx_eea:linear_perpetual:ADA:USDT:USDT:ada-usdt-swap"
    )
    assert inputs["THIS_VALIDATION_DEFINES_NO_INSTRUMENT_LIST"] is True
    assert inputs["SNAPSHOT_IDENTITY_JOIN"] == "NOT_PROVEN_IDENTICAL"


def test_band_samples_are_formula_vectors_not_a_new_universe() -> None:
    inputs = build_inputs_v1()
    assert inputs["GOLDEN_VECTORS_ARE_FORMULA_VECTORS_NOT_INSTRUMENT_UNIVERSE"] is True
    assert inputs["BAND_SAMPLE_CLASS"] == BAND_SAMPLE_CLASS
    assert inputs["SYNTHETIC_BAND_SET_AS_PRODUCTIVE_AUTHORITY"] is False
    assert inputs["OBSERVED_PER_INSTRUMENT_RUNTIME_SCOPE_STATE_BAND"] == "ABSENT_ON_ORIGIN_MAIN"
    exemplar = inputs["CAP62_BAND_EXEMPLAR"]
    assert isinstance(exemplar, dict)
    assert exemplar["in_cap23_selectable_set"] is False
    assert exemplar["current_hysteresis_band"] == 50.0


def test_each_instrument_and_valid_band_sample_passes_pre_metadata_criteria() -> None:
    inputs = build_inputs_v1()
    results = build_results_v1(inputs)
    assert results["VALIDATION_PASS"] is True
    assert results["OQ_C1_PASS"] is True
    assert results["OQ_C2_PASS"] is True
    assert results["UNAUTHORIZED_FLOOR_OR_CLAMP"] is False
    assert results["function_parameter_names"] == ["current_hysteresis_band"]
    assert results["derive_source_contains_instrument_id"] is False
    assert results["PRODUCTIVE_CALLGRAPH_REACHABLE"] is False
    assert results["sample_count"] == 20 * len(GOLDEN_VALID_VECTORS_V1)
    for sample in results["samples"]:
        assert isinstance(sample, dict)
        assert sample["ok"] is True
        assert sample["oq_c1_pass"] is True
        assert sample["oq_c2_pass"] is True
        assert sample["nested_geometry_pass"] is True
        assert sample["instrument_id_consumed"] is False
        assert sample["unauthorized_floor_or_clamp_or_cap63_fallback"] is False
        assert sample["band_sample_class"] == BAND_SAMPLE_CLASS


def test_same_band_is_instrument_invariant_and_different_bands_scale() -> None:
    first = derive_scope_event_distances_v1(25.0)
    second = derive_scope_event_distances_v1(50.0)
    assert first.ok is True and second.ok is True
    assert first.up_distance == 25.0
    assert first.adverse_exit_distance == 10.0
    assert first.reversal_distance == 15.0
    assert second.up_distance == 50.0
    assert second.adverse_exit_distance == 20.0
    assert second.reversal_distance == 30.0
    assert first != second


def test_committed_evidence_matches_live_report() -> None:
    inputs = build_inputs_v1()
    results = build_results_v1(inputs)
    summary = build_summary_v1(inputs, results)
    assert INPUTS_PATH.read_text(encoding="utf-8") == _canonical_json(inputs)
    assert RESULTS_PATH.read_text(encoding="utf-8") == _canonical_json(results)
    assert SUMMARY_PATH.read_text(encoding="utf-8") == _canonical_json(summary)
    expected_manifest = []
    for name in ("INPUTS.json", "RESULTS.json", "SUMMARY.json"):
        digest = _sha256_text((EVIDENCE_DIR / name).read_text(encoding="utf-8"))
        expected_manifest.append(f"{digest}  {name}")
    assert MANIFEST_PATH.read_text(encoding="utf-8") == "\n".join(expected_manifest) + "\n"
    assert summary["VALIDATION_PASS"] is True
    assert summary["METADATA_GATE_CONSUMED"] is False
    assert summary["MODEL_C_BOUND"] is False


def test_validation_contract_records_performed_and_unbound() -> None:
    text = CONTRACT.read_text(encoding="utf-8")
    assert "CROSS_INSTRUMENT_VALIDATION_PERFORMED=true" in text
    assert "VALIDATION_PROTOCOL_CONFORMANT=true" in text
    assert "METADATA_GATE_CONSUMED=false" in text
    assert "MODEL_C_BOUND=false" in text
    assert "MODEL_C_RUNTIME_BIND_AUTHORIZED=false" in text
    assert "CURRENT_CANONICAL_MODEL=MODEL_B" in text
    assert "up_distance=200.0" in text
    assert "OD2_LAST_STEP=KEEP_BOUND_DESTINATION_PREFIX" in text
    assert "OD2_ARMED_RESIDUAL=OPEN" in text
    assert "TICK_LOT_CTVAL_PRICE_SCALE_METADATA_AUTHORITY=AUTHORITY_MISSING" in text
    assert "THIS_VALIDATION_DEFINES_NO_INSTRUMENT_LIST=true" in text
    assert "SYNTHETIC_BAND_SET_AS_PRODUCTIVE_AUTHORITY=false" in text
    assert "BAND_SAMPLE_CLASS=FORMULA_VALID_BAND_NOT_PER_INSTRUMENT_PRODUCTIVE_SNAPSHOT" in text
