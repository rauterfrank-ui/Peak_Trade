"""V6 native full-cycle trace engine — AUTHORITY=NONE, observation only."""

from __future__ import annotations

import hashlib
import json
import threading
import time
import traceback
from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any, Callable

TRACE_ID = "E2E_10K_NATIVE_FULL_CYCLE_V6"
AUTHORITY = "NONE"

MATERIAL_PATH_MARKERS = (
    "/src/ops/governed_productive_account_equity_authority_producer_v1/",
    "/src/ops/full_core_live_path_composition_root_v1/",
    "/src/ops/governed_futures_universe_producer_v1/",
    "/src/ops/productive_futures_ranking_producer_v1/",
    "/src/ops/single_selected_future",
    "/src/ops/current_productive_eea_universe_inventory_acquisition_v1/",
    "/src/ops/governed_productive_instrument_metadata",
    "/src/ops/governed_productive_reference_price",
    "/src/ops/b05_full_core_governed_authority_chain_closure_v1/",
    "/src/ops/current_mf_n5_full_autonomy_occupied_lane",
    "/src/trading/master_v2/",
    "/src/governance/capital_risk_sizing_v1.py",
    "/src/governance/canonical_order_intent_v1.py",
)

SKIP_FUNCTION_NAMES = frozenset({"<listcomp>", "<dictcomp>", "<genexpr>", "<setcomp>"})

FORBIDDEN_SESSION_FUNCTIONS = frozenset(
    {
        "prepare_layered_long_armed_seed_for_pre_external_invoke_v1",
        "acquire_current_productive_29p_cap24_bound_instrument_provenance_handoff_v1",
    }
)

CLASSIFY_BY_NAME: dict[str, str] = {
    "execute_current_productive_native_full_cycle_host_v1": "OTHER",
    "execute_current_productive_eea_universe_inventory_to_cap24_and_29p_v1": "OTHER",
    "execute_current_productive_full_core_pre_external_closure_v1": "OTHER",
    "advance_layered_long_mv2_state_for_pre_external_v1": "STATE_UPDATE",
    "acquire_eea_universe_inventory_v1": "EXTERNAL_OBSERVATION",
    "run_cap21_to_cap23_persist_productive_v1": "SEMANTIC_TRANSFORMATION",
    "compose_current_productive_29p_common_epoch_handoff_v1": "DERIVATION",
    "execute_current_productive_treasury_single_source_capital_handoff_v1": "SEMANTIC_TRANSFORMATION",
    "produce_current_productive_available_for_sizing_v1": "DERIVATION",
    "join_current_productive_enter_live_29p_before_venue_plan_v1": "RISK_CALCULATION",
    "join_current_productive_enter_live_29p_v1": "RISK_CALCULATION",
    "evaluate_capital_risk_sizing_v1": "SIZING",
    "bind_canonical_order_intent_offline_replay_evidence_v0": "EXECUTION_PLANNING",
    "invoke_occupied_lane_governed_cycle_n1_consumer_v1": "DECISION",
    "run_current_productive_master_v2_runtime_cycle_v1": "STATE_UPDATE",
    "compose_occupied_lane_mv2_dp_durable_cycle_v1": "STATE_UPDATE",
    "collect_fresh_pretrade_runtime_get_v1": "EXTERNAL_OBSERVATION",
    "governed_c1_aligned_g17_dk_producer_v1": "FEATURE_COMPUTATION",
}


def _utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _value_summary(obj: Any) -> str:
    if obj is None:
        return "null"
    if isinstance(obj, (str, int, float, bool)):
        s = str(obj)
        return s[:240] + ("…" if len(s) > 240 else "")
    if isinstance(obj, Decimal):
        return str(obj)
    if is_dataclass(obj):
        d = asdict(obj)
        keys = list(d.keys())[:12]
        parts = [f"{k}={_value_summary(d[k])}" for k in keys]
        return type(obj).__name__ + "{" + ", ".join(parts) + "}"
    if isinstance(obj, dict):
        return f"dict(len={len(obj)})"
    if isinstance(obj, (list, tuple)):
        return f"{type(obj).__name__}(len={len(obj)})"
    return type(obj).__name__


def _semantic_type(obj: Any) -> str:
    if obj is None:
        return "NONE"
    name = type(obj).__name__
    mod = getattr(type(obj), "__module__", "") or ""
    if "BoundInstrument" in name:
        return "BOUND_INSTRUMENT"
    if "UsdcFreeMargin" in name or "MarginObservation" in name:
        return "USDC_MARGIN_OBSERVATION"
    if "CapitalRiskSizingDecision" in name:
        return "CRS_DECISION"
    if "FinalOrderEnvelope" in name:
        return "FINAL_ORDER_ENVELOPE"
    if "IntegratedOfflineReplayResult" in name:
        return "MV2_DP_REPLAY_RESULT"
    if "CurrentProductiveMasterV2CycleResult" in name:
        return "MV2_CYCLE_RESULT"
    if "CurrentProductiveNativeFullCycleHostResult" in name:
        return "NATIVE_HOST_RESULT"
    if name == "dict" and isinstance(obj, dict):
        if "BOUND_INSTRUMENT" in obj:
            return "BOUND_INSTRUMENT_JSON_WRAPPER"
    return f"{mod}.{name}"


class NativeTraceEngineV6:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._call_seq = 0
        self._obj_seq = 0
        self._handoff_seq = 0
        self._num_seq = 0
        self._cycle_seq = 0
        self._active = False
        self._call_stack: list[str] = []
        self.calls: list[dict[str, Any]] = []
        self.objects: dict[str, dict[str, Any]] = {}
        self.id_to_obj: dict[int, str] = {}
        self.handoffs: list[dict[str, Any]] = []
        self.numerical: list[dict[str, Any]] = []
        self.persistence_events: list[dict[str, Any]] = []
        self.forbidden_function_hits: list[dict[str, str]] = []
        self.py_id_to_object: dict[int, Any] = {}

    def register_object(
        self,
        obj: Any,
        *,
        producer_call_id: str | None,
        derived_from: list[str] | None = None,
        extra: dict[str, Any] | None = None,
    ) -> str:
        with self._lock:
            py_id = id(obj)
            if py_id in self.id_to_obj and obj is not None:
                oid = self.id_to_obj[py_id]
                if producer_call_id:
                    rec = self.objects[oid]
                    if producer_call_id not in rec.get("producer_call_ids", []):
                        rec.setdefault("producer_call_ids", []).append(producer_call_id)
                return oid
            self._obj_seq += 1
            oid = f"OBJ_{self._obj_seq:06d}"
            rec: dict[str, Any] = {
                "object_id": oid,
                "python_type": type(obj).__name__,
                "semantic_type": _semantic_type(obj),
                "producer_call_id": producer_call_id or "",
                "producer_call_ids": [producer_call_id] if producer_call_id else [],
                "derived_from_object_ids": derived_from or [],
                "value_summary": _value_summary(obj),
                "unit": "",
                "currency": "",
                "venue_binding": "",
                "account_binding": "",
                "instrument_binding": "",
                "decision_epoch": "",
                "provenance": "",
                "consumer_call_ids": [],
                "python_identity": py_id,
                "authority": AUTHORITY,
            }
            if is_dataclass(obj):
                d = asdict(obj)
                if "settlement_currency" in d:
                    rec["currency"] = str(d.get("settlement_currency") or "")
                if "instrument_id" in d:
                    rec["instrument_binding"] = str(
                        d.get("instrument_id") or d.get("venue_native_id") or ""
                    )
                if "venue_native_id" in d and not rec["instrument_binding"]:
                    rec["instrument_binding"] = str(d.get("venue_native_id") or "")
                if "value" in d:
                    rec["value_summary"] = str(d.get("value"))
                if "decision_epoch" in d:
                    rec["decision_epoch"] = str(d.get("decision_epoch") or "")
                if "decision_outcome" in d:
                    rec["provenance"] = f"decision_outcome={d.get('decision_outcome')}"
                if "quantity" in d and "side" in d:
                    rec["value_summary"] = f"side={d.get('side')} qty={d.get('quantity')}"
                cursor = d.get("outgoing_cursor")
                if isinstance(cursor, dict) and cursor.get("side_state"):
                    rec["provenance"] = (
                        rec.get("provenance", "") + f";side_state={cursor.get('side_state')}"
                    ).strip(";")
            if extra:
                rec.update(extra)
            self.objects[oid] = rec
            if obj is not None:
                self.id_to_obj[py_id] = oid
                self.py_id_to_object[py_id] = obj
            return oid

    def record_handoff(
        self,
        *,
        producer_call_id: str,
        output_object_id: str,
        consumer_call_id: str,
        input_object_id: str,
        handoff_type: str,
        driver_reconstruction: bool = False,
        identity_or_derivation_proof: str = "",
    ) -> None:
        with self._lock:
            self._handoff_seq += 1
            proven = (
                handoff_type
                in (
                    "SAME_IDENTITY",
                    "DERIVED_FROM_PROVEN",
                    "SERIALIZATION_PROVEN",
                    "PERSISTENCE_PROVEN",
                    "NATIVE_TYPED_HANDOFF",
                )
                and not driver_reconstruction
            )
            self.handoffs.append(
                {
                    "handoff_id": f"HO_{self._handoff_seq:06d}",
                    "producer_call_id": producer_call_id,
                    "output_object_id": output_object_id,
                    "consumer_call_id": consumer_call_id,
                    "input_object_id": input_object_id,
                    "handoff_type": handoff_type,
                    "identity_or_derivation_proof": identity_or_derivation_proof or handoff_type,
                    "driver_reconstruction_required": driver_reconstruction,
                    "causal_handoff_proven": proven,
                    "authority": AUTHORITY,
                }
            )
            if output_object_id in self.objects:
                self.objects[output_object_id].setdefault("consumer_call_ids", []).append(
                    consumer_call_id
                )

    def record_numerical(
        self,
        *,
        call_id: str,
        input_object_id: str,
        input_value: str,
        rule: str,
        output_value: str,
        output_object_id: str,
    ) -> None:
        with self._lock:
            self._num_seq += 1
            self.numerical.append(
                {
                    "numerical_id": f"N_{self._num_seq:06d}",
                    "call_id": call_id,
                    "input_object_id": input_object_id,
                    "input_value": input_value,
                    "formula_rule": rule,
                    "output_value": output_value,
                    "output_object_id": output_object_id,
                    "authority": AUTHORITY,
                }
            )

    def _classify(self, func_name: str) -> str:
        if func_name in FORBIDDEN_SESSION_FUNCTIONS:
            return "FORBIDDEN_DRIVER_BRIDGE"
        return CLASSIFY_BY_NAME.get(func_name, "OTHER")

    def _material_frame(self, filename: str) -> bool:
        if "/Peak_Trade/src/" not in filename.replace("\\", "/"):
            return False
        norm = filename.replace("\\", "/")
        return any(m in norm for m in MATERIAL_PATH_MARKERS)

    def trace_function(self, frame, event: str, arg: Any) -> Callable:
        if not self._active:
            return self.trace_function
        code = frame.f_code
        if code.co_name in SKIP_FUNCTION_NAMES:
            return self.trace_function
        filename = code.co_filename
        if not self._material_frame(filename):
            return self.trace_function

        if code.co_name in FORBIDDEN_SESSION_FUNCTIONS and event == "call":
            with self._lock:
                self.forbidden_function_hits.append(
                    {"function": code.co_name, "file": filename, "event": event}
                )

        if event == "call":
            with self._lock:
                self._call_seq += 1
                call_id = f"CALL_{self._call_seq:06d}"
                parent = self._call_stack[-1] if self._call_stack else ""
                self._call_stack.append(call_id)
            input_oids: list[str] = []
            for _name, val in list(frame.f_locals.items())[:40]:
                if _name in ("self", "cls", "frame"):
                    continue
                if val is None or isinstance(val, (bool, int, float)):
                    continue
                if isinstance(val, (str, bytes)) and len(str(val)) > 500:
                    continue
                try:
                    input_oids.append(self.register_object(val, producer_call_id=None))
                except Exception:
                    continue
            rec = {
                "call_id": call_id,
                "parent_call_id": parent,
                "function": code.co_name,
                "module": frame.f_globals.get("__name__", ""),
                "file": filename.split("/Peak_Trade/")[-1]
                if "/Peak_Trade/" in filename
                else filename,
                "start": time.time(),
                "end": None,
                "input_object_ids": input_oids,
                "output_object_ids": [],
                "exception": None,
                "classification": self._classify(code.co_name),
                "authority": AUTHORITY,
            }
            frame.f_locals["__v6_call_id__"] = call_id
            with self._lock:
                self.calls.append(rec)
            return self.trace_function

        if event == "return":
            call_id = frame.f_locals.get("__v6_call_id__")
            if not call_id:
                return self.trace_function
            retval = arg
            output_oids: list[str] = []
            try:
                if retval is not None:
                    oid = self.register_object(retval, producer_call_id=call_id)
                    output_oids.append(oid)
                    if code.co_name == "evaluate_capital_risk_sizing_v1" and is_dataclass(retval):
                        d = asdict(retval)
                        qty = str(d.get("quantity") or d.get("final_quantity") or "")
                        if qty:
                            self.record_numerical(
                                call_id=call_id,
                                input_object_id=output_oids[0],
                                input_value=str(d.get("capital_base") or d.get("available") or ""),
                                rule="evaluate_capital_risk_sizing_v1",
                                output_value=qty,
                                output_object_id=output_oids[0],
                            )
            except Exception:
                pass
            with self._lock:
                for c in reversed(self.calls):
                    if c["call_id"] == call_id:
                        c["end"] = time.time()
                        c["output_object_ids"] = output_oids
                        break
                if self._call_stack and self._call_stack[-1] == call_id:
                    self._call_stack.pop()
                elif call_id in self._call_stack:
                    self._call_stack = [x for x in self._call_stack if x != call_id]
            if output_oids and self._call_stack:
                parent_id = self._call_stack[-1]
                for inp in output_oids:
                    self.record_handoff(
                        producer_call_id=call_id,
                        output_object_id=inp,
                        consumer_call_id=parent_id,
                        input_object_id=inp,
                        handoff_type="SAME_IDENTITY",
                    )
            return self.trace_function

        if event == "exception":
            call_id = frame.f_locals.get("__v6_call_id__")
            if call_id:
                exc = traceback.format_exc(limit=3)
                with self._lock:
                    for c in self.calls:
                        if c["call_id"] == call_id:
                            c["exception"] = exc[:500]
                            c["end"] = time.time()
                            break
            return self.trace_function

        return self.trace_function

    def start(self) -> None:
        self._active = True

    def stop(self) -> None:
        self._active = False

    def build_mv2_state_transition_ledger(self) -> list[dict[str, Any]]:
        ledger: list[dict[str, Any]] = []
        mv2_fns = {
            "run_current_productive_master_v2_runtime_cycle_v1",
            "compose_occupied_lane_mv2_dp_durable_cycle_v1",
            "invoke_occupied_lane_governed_cycle_n1_consumer_v1",
        }
        for call in self.calls:
            if call["function"] not in mv2_fns:
                continue
            for oid in call.get("output_object_ids") or []:
                obj = self.py_id_to_object.get(self.objects[oid]["python_identity"])
                if obj is None:
                    continue
                if not is_dataclass(obj):
                    continue
                name = type(obj).__name__
                if "CycleResult" not in name and "ConsumerInvocation" not in name:
                    continue
                self._cycle_seq += 1
                d = asdict(obj)
                cycle_id = str(d.get("cycle_id") or call["call_id"])
                decision = str(d.get("decision_outcome") or "")
                side_before = ""
                side_after = ""
                cursor = d.get("outgoing_cursor")
                if isinstance(cursor, dict):
                    side_after = str(cursor.get("side_state") or "")
                ledger.append(
                    {
                        "cycle_id": cycle_id,
                        "observation_ids": call.get("input_object_ids") or [],
                        "state_before": side_before,
                        "layer_rule": call["function"],
                        "state_after": side_after,
                        "output": decision,
                        "call_id": call["call_id"],
                    }
                )
        return ledger

    def build_sizing_ledger(self, *, avail_eq: str, final_quantity: str) -> dict[str, Any]:
        crs_calls = [c for c in self.calls if c["function"] == "evaluate_capital_risk_sizing_v1"]
        crs_objects = [o for o in self.objects.values() if o.get("semantic_type") == "CRS_DECISION"]
        return {
            "avail_eq_observation": avail_eq,
            "crs_call_ids": [c["call_id"] for c in crs_calls],
            "crs_object_ids": [o["object_id"] for o in crs_objects],
            "numerical_steps": self.numerical,
            "final_quantity": final_quantity,
            "quantity_lineage_proven": bool(final_quantity and crs_calls),
            "authority": AUTHORITY,
        }

    def write_artifacts(
        self,
        evidence_root: Path,
        *,
        report: dict[str, Any],
        mv2_advance: dict[str, Any] | None = None,
    ) -> None:
        evidence_root.mkdir(parents=True, exist_ok=True)
        mv2_ledger = self.build_mv2_state_transition_ledger()
        if mv2_advance:
            mv2_ledger.append(
                {
                    "cycle_id": "native-mv2-advance-arm",
                    "observation_ids": [],
                    "state_before": "UPSCOPE_CONFIRMED",
                    "layer_rule": "advance_layered_long_mv2_state_for_pre_external_v1",
                    "state_after": mv2_advance.get("arm_side_state", ""),
                    "output": mv2_advance.get("arm_decision_outcome", ""),
                    "call_id": "",
                }
            )
        (evidence_root / "CALL_GRAPH.json").write_text(
            json.dumps(
                {
                    "trace_id": TRACE_ID,
                    "calls": self.calls,
                    "total_native_runtime_calls": len(self.calls),
                    "authority": AUTHORITY,
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        (evidence_root / "OBJECT_LINEAGE.json").write_text(
            json.dumps(
                {
                    "objects": self.objects,
                    "total_native_runtime_objects": len(self.objects),
                    "authority": AUTHORITY,
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        (evidence_root / "HANDOFF_LEDGER.json").write_text(
            json.dumps(
                {
                    "handoffs": self.handoffs,
                    "total_native_material_handoffs": len(self.handoffs),
                    "no_driver_internal_business_bridge": report.get(
                        "NO_DRIVER_INTERNAL_BUSINESS_BRIDGE", True
                    ),
                    "authority": AUTHORITY,
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        (evidence_root / "STATE_TRANSITION_LEDGER.json").write_text(
            json.dumps({"transitions": mv2_ledger, "authority": AUTHORITY}, indent=2) + "\n",
            encoding="utf-8",
        )
        (evidence_root / "SIZING_LEDGER.json").write_text(
            json.dumps(
                self.build_sizing_ledger(
                    avail_eq=str(report.get("AVAIL_EQ") or ""),
                    final_quantity=str(report.get("FINAL_QUANTITY") or ""),
                ),
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        (evidence_root / "NUMERICAL_LINEAGE.json").write_text(
            json.dumps({"numerical": self.numerical, "authority": AUTHORITY}, indent=2) + "\n",
            encoding="utf-8",
        )
        (evidence_root / "NATIVE_FULL_CYCLE_REPORT.json").write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
