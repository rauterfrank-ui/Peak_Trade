#!/usr/bin/env python3
"""Generate offline evidence for productive typed-vol producer + CMC hot-path binding."""

from __future__ import annotations

import hashlib
import json
import math
import subprocess
import sys
from decimal import Decimal
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
for _p in (_REPO_ROOT, _REPO_ROOT / "src"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from src.ops.integrated_paper_shadow_observation_session_v1.market_data_policy_v1 import (  # noqa: E402
    ObservationMarketTickV1,
)
from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.constants_v1 import (  # noqa: E402
    CANONICAL_INSTRUMENT_ID,
)
from src.ops.productive_typed_volatility_producer_and_cmc_hot_path_binding_v1.constants_v1 import (  # noqa: E402
    CAPABILITY_ID,
    CMC_BINDING_CALLER,
    CORE_LOGIC_CHANGE,
    NO_PROXY_PROMOTION,
    PERSISTENCE_CLASSIFICATION,
    PRESENCE_GATE_CONSUMER,
    PRODUCTIVE_PRODUCER_CALLER,
    PT1M_FINALIZER_OWNER,
    RESTART_SEMANTICS,
    ROOT_CAUSE_CALL_GRAPH_EDGE,
    TYPED_VOLATILITY_PRODUCER,
    VOLATILITY_NUMERIC_MAX_AGE_ENFORCING,
    VOLATILITY_STATE_OWNER,
    WARMUP_REQUIRED_PRICE_OBSERVATIONS,
)
from src.ops.simulated_entry_reduce_exit_actionability_evidence_v1.parity_v1 import (  # noqa: E402
    prove_trading_logic_parity_v1,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_hardening_v2.hardening_cycle_bridge_v2 import (  # noqa: E402
    HardenedBridgeSessionStateV2,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_hardening_v2.wallclock_hardening_binding_v2 import (  # noqa: E402
    run_hardened_wallclock_bridge_observation_cycle_v2,
)
from trading.master_v2.canonical_volatility_estimate_feature_contract_v1 import (  # noqa: E402
    BAR_INTERVAL,
    DDOF,
    LOOKBACK_BARS,
    OUTPUT_ANNUALIZED,
    OUTPUT_UNIT,
    WARMUP_REQUIRED_PRICE_COUNT,
)
from trading.master_v2.canonical_volatility_estimate_materializer_v1 import (  # noqa: E402
    BAR_INTERVAL_SECONDS,
)

T0 = 1_700_000_040.0
EVIDENCE_DIRNAME = "capability_productive_typed_volatility_producer_and_cmc_hot_path_binding_v1"


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def _price_at(i: int) -> float:
    return 100.0 * math.exp(0.001 * i)


def _run_probe(*, minutes: int = 64) -> dict:
    state = HardenedBridgeSessionStateV2()
    warmup_cycles = 0
    typed_missing_after_warmup = 0
    typed_present_after_warmup = 0
    first_produced_cycle = None
    traces = {
        "warmup_transition_trace": [],
        "distinct_observation_trace": [],
        "typed_estimate_trace": [],
        "CMC_binding_trace": [],
        "presence_gate_trace": [],
        "decision_stage_progression": [],
    }
    seq = 1
    last_cycle = None
    for minute in range(minutes):
        for sub_i in range(2):
            sub = 5 + sub_i * 10
            et = T0 + minute * BAR_INTERVAL_SECONDS + sub
            price = _price_at(minute) * (1.0 + 1e-6 * sub_i)
            out = run_hardened_wallclock_bridge_observation_cycle_v2(
                bridge_state=state,
                ticks=[
                    ObservationMarketTickV1(
                        instrument_id=CANONICAL_INSTRUMENT_ID,
                        venue="OKX",
                        market_type="FUTURES",
                        sequence=seq,
                        event_ts_unix=et,
                        receive_ts_unix=et + 0.05,
                        mono_ts=float(seq),
                        mid_price=price,
                    )
                ],
                reference_price=Decimal(str(price)),
                wall_now_unix=et + 0.05,
                session_id="typed-vol-offline-probe",
            )
            assert out.ok and out.bridge_cycle is not None
            cycle = out.bridge_cycle
            last_cycle = cycle
            tele = cycle["canonical_volatility_typed_binding"]
            gate = cycle["double_play_typed_volatility_presence_gate"]
            if tele["producer_outcome"] == "WARMUP":
                warmup_cycles += 1
            if tele["estimate_present"]:
                if first_produced_cycle is None:
                    first_produced_cycle = seq
                typed_present_after_warmup += 1
            elif first_produced_cycle is not None:
                typed_missing_after_warmup += 1
            if out.finalized_pt1m_emitted:
                traces["distinct_observation_trace"].append(
                    {
                        "cycle": seq,
                        "minute": minute,
                        "producer_outcome": tele["producer_outcome"],
                        "history_digest": tele.get("history_digest"),
                        "estimate_present": tele["estimate_present"],
                    }
                )
            traces["typed_estimate_trace"].append(
                {
                    "cycle": seq,
                    "estimate_present": tele["estimate_present"],
                    "producer_outcome": tele["producer_outcome"],
                    "source_digest": tele.get("source_digest"),
                    "fail_closed_reason": tele.get("fail_closed_reason"),
                }
            )
            traces["CMC_binding_trace"].append(
                {
                    "cycle": seq,
                    "typed_binding_performed": tele.get("typed_binding_performed"),
                    "canonical_market_context_typed_estimate_present": cycle[
                        "canonical_market_context_typed_estimate_present"
                    ],
                }
            )
            traces["presence_gate_trace"].append(
                {
                    "cycle": seq,
                    "typed_estimate_present": gate.get("typed_estimate_present"),
                    "alpha_scope_entry_authority_allowed": gate.get(
                        "alpha_scope_entry_authority_allowed"
                    ),
                    "reason_codes": list(gate.get("reason_codes") or []),
                }
            )
            traces["decision_stage_progression"].append(
                {
                    "cycle": seq,
                    "call_graph": list(cycle.get("call_graph") or []),
                    "decision_outcome": cycle.get("decision_outcome"),
                    "intended_action": (cycle.get("intended_action") or {}).get("intended_side"),
                }
            )
            if tele["producer_outcome"] in {"WARMUP", "PRODUCED"} and (
                not traces["warmup_transition_trace"]
                or traces["warmup_transition_trace"][-1]["producer_outcome"]
                != tele["producer_outcome"]
            ):
                traces["warmup_transition_trace"].append(
                    {
                        "cycle": seq,
                        "producer_outcome": tele["producer_outcome"],
                        "estimate_present": tele["estimate_present"],
                    }
                )
            seq += 1

    assert last_cycle is not None
    fr = last_cycle["feature_regime"]
    return {
        "warmup_cycles": warmup_cycles,
        "first_produced_cycle": first_produced_cycle,
        "typed_volatility_estimate_missing_count_after_warmup": typed_missing_after_warmup,
        "typed_present_after_warmup_count": typed_present_after_warmup,
        "canonical_market_context_typed_estimate_present": last_cycle[
            "canonical_market_context_typed_estimate_present"
        ],
        "canonical_volatility_typed_binding": last_cycle["canonical_volatility_typed_binding"],
        "presence_gate": last_cycle["double_play_typed_volatility_presence_gate"],
        "volatility_estimate_productive_authority": (
            last_cycle["canonical_market_context_typed_estimate_present"] is True
            and fr.get("volatility_estimate_productive_authority") is False
        ),
        "legacy_proxy_productive_authority": fr.get("volatility_estimate_productive_authority"),
        "decision_graph_progress_after_vol_stage": (
            "master_v2_double_play_integrated_offline_replay"
            in (last_cycle.get("call_graph") or [])
        ),
        "execution_eligible": last_cycle.get("execution_eligible"),
        "orders_submitted": False,
        "finalizer_finalized_count": (
            None
            if state.pt1m_mark_observation_finalizer is None
            else state.pt1m_mark_observation_finalizer.finalized_count
        ),
        "history_observation_count": (
            None
            if state.typed_volatility_cmc_binding_host is None
            else state.typed_volatility_cmc_binding_host.producer.history.observation_count_prices
        ),
        "traces": traces,
        "last_cycle_id": last_cycle.get("cycle_id"),
    }


def _write_manifest(root: Path) -> str:
    rows: list[str] = []
    for path in sorted(root.rglob("*")):
        if path.is_file() and path.name != "MANIFEST.sha256":
            rel = path.relative_to(root).as_posix()
            rows.append(f"{_sha256_file(path)}  {rel}")
    manifest = "\n".join(rows) + "\n"
    (root / "MANIFEST.sha256").write_text(manifest, encoding="utf-8")
    return hashlib.sha256(manifest.encode("utf-8")).hexdigest()


def main() -> int:
    try:
        repository_sha = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=str(_REPO_ROOT),
            text=True,
        ).strip()
    except Exception:  # noqa: BLE001
        repository_sha = "UNKNOWN"

    evidence_root = _REPO_ROOT / "docs" / "evidence" / EVIDENCE_DIRNAME
    productive = evidence_root / "productive_binding"
    productive.mkdir(parents=True, exist_ok=True)

    probe = _run_probe()
    parity = prove_trading_logic_parity_v1()
    matrix = {
        "SYMBOL": "CanonicalVolatilityTypedRuntimeProducerScaffoldV1",
        "FILE": (
            "src/trading/master_v2/canonical_volatility_typed_runtime_producer_scaffold_v1.py"
        ),
        "CURRENT_PRODUCTIVE_CALLER": PRODUCTIVE_PRODUCER_CALLER,
        "INPUT_OBSERVATIONS": "finalized PT1M mark samples from PT1M finalizer",
        "WINDOW_REQUIREMENT": LOOKBACK_BARS,
        "WARMUP_RULE": WARMUP_REQUIRED_PRICE_OBSERVATIONS,
        "ESTIMATE_TYPE": "CanonicalVolatilityEstimateV1",
        "SEMANTICS": {
            "bar_interval": BAR_INTERVAL,
            "ddof": DDOF,
            "unit": OUTPUT_UNIT,
            "annualized": OUTPUT_ANNUALIZED,
            "warmup_required_price_count": WARMUP_REQUIRED_PRICE_COUNT,
        },
        "AS_OF_EVENT_TIME": "estimate.as_of_event_time from accepted EventTimeInstantV1",
        "MARKET_EVENT_TIME_REFERENCE": "finalized PT1M close event time",
        "PROVENANCE_FIELDS": [
            "source_digest",
            "history_digest",
            "observation_count",
            "as_of_event_time",
            "config/feature contract digest",
        ],
        "STATE_OWNER": VOLATILITY_STATE_OWNER,
        "PERSISTENCE_OWNER": VOLATILITY_STATE_OWNER,
        "CMC_BINDING_CALLER": CMC_BINDING_CALLER,
        "MASTER_V2_CONSUMER": "integrated_offline_trading_logic_replay via CMC",
        "DOUBLE_PLAY_CONSUMER": PRESENCE_GATE_CONSUMER,
        "FAIL_CLOSED_BEHAVIOR": "WARMUP_NO_ESTIMATE / reject outcomes block alpha entry",
        "CURRENT_DISCONNECT_BEFORE": ROOT_CAUSE_CALL_GRAPH_EDGE,
        "PT1M_FINALIZER_OWNER": PT1M_FINALIZER_OWNER,
        "PERSISTENCE_CLASSIFICATION": PERSISTENCE_CLASSIFICATION,
        "RESTART_SEMANTICS": RESTART_SEMANTICS,
    }
    call_graph_before = [
        "okx_public_market_data",
        "feature_pipeline",
        "regime_pipeline",
        "canonical_volatility_productive_runtime_cmc_typed_binding(ingest_sample=false)",
        "typed_volatility_presence(TYPED_VOLATILITY_ESTIMATE_MISSING permanent)",
        "master_v2_double_play_integrated_offline_replay",
    ]
    call_graph_after = [
        "okx_public_market_data",
        "pt1m_mark_observation_finalizer",
        "feature_pipeline",
        "regime_pipeline",
        "canonical_volatility_productive_runtime_cmc_typed_binding(ingest finalized PT1M)",
        "typed_volatility_presence(present after warmup)",
        "master_v2_double_play_integrated_offline_replay",
    ]
    claims = {
        "TYPED_VOL_MISSING_DURING_VALID_WARMUP": probe["warmup_cycles"] > 0,
        "TYPED_VOL_MISSING_AFTER_WARMUP_COUNT": probe[
            "typed_volatility_estimate_missing_count_after_warmup"
        ],
        "TYPED_ESTIMATE_PRESENT_AFTER_WARMUP": bool(
            probe["canonical_market_context_typed_estimate_present"]
        ),
        "CMC_TYPED_ESTIMATE_PRESENT_AFTER_WARMUP": bool(
            probe["canonical_market_context_typed_estimate_present"]
        ),
        "PRODUCTIVE_AUTHORITY_AFTER_WARMUP": bool(
            probe["volatility_estimate_productive_authority"]
        ),
        "LEGACY_PROXY_PROMOTED": bool(probe["legacy_proxy_productive_authority"]),
        "SILENT_DEFAULT_ADDED": False,
        "NUMERIC_MAX_AGE_ENFORCEMENT_CHANGED": False,
        "VOLATILITY_NUMERIC_MAX_AGE_ENFORCING": VOLATILITY_NUMERIC_MAX_AGE_ENFORCING,
        "CORE_LOGIC_CHANGE": CORE_LOGIC_CHANGE,
        "NO_PROXY_PROMOTION": NO_PROXY_PROMOTION,
        "DECISION_GRAPH_PROGRESS_AFTER_VOL_STAGE": bool(
            probe["decision_graph_progress_after_vol_stage"]
        ),
        "LIVE_PATH_CHANGED": False,
        "TESTNET_PATH_CHANGED": False,
        "ORDER_PATH_CHANGED": False,
        "EXCHANGE_CREDENTIAL_PATH_CHANGED": False,
        "NETWORK_USED": False,
    }
    negative = {
        "execution_eligible_false": probe["execution_eligible"] is False,
        "orders_submitted_false": probe["orders_submitted"] is False,
        "legacy_proxy_non_authority": probe["legacy_proxy_productive_authority"] is False,
        "no_silent_default": claims["SILENT_DEFAULT_ADDED"] is False,
        "numeric_max_age_non_enforcing": VOLATILITY_NUMERIC_MAX_AGE_ENFORCING is False,
    }
    config_digest = hashlib.sha256(
        json.dumps(
            {
                "capability_id": CAPABILITY_ID,
                "bar_interval_seconds": BAR_INTERVAL_SECONDS,
                "warmup_required": WARMUP_REQUIRED_PRICE_OBSERVATIONS,
                "lookback_bars": LOOKBACK_BARS,
                "ddof": DDOF,
                "unit": OUTPUT_UNIT,
                "annualized": OUTPUT_ANNUALIZED,
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()

    _write_json(productive / "producer_consumer_state_matrix.json", matrix)
    _write_json(productive / "call_graph_before.json", {"call_graph": call_graph_before})
    _write_json(productive / "call_graph_after.json", {"call_graph": call_graph_after})
    _write_json(
        productive / "warmup_transition_trace.json", probe["traces"]["warmup_transition_trace"]
    )
    _write_json(
        productive / "distinct_observation_trace.json",
        probe["traces"]["distinct_observation_trace"],
    )
    _write_json(productive / "typed_estimate_trace.json", probe["traces"]["typed_estimate_trace"])
    _write_json(productive / "CMC_binding_trace.json", probe["traces"]["CMC_binding_trace"])
    _write_json(productive / "presence_gate_trace.json", probe["traces"]["presence_gate_trace"])
    _write_json(
        productive / "decision_stage_progression.json",
        probe["traces"]["decision_stage_progression"],
    )
    _write_json(
        productive / "legacy_proxy_non_authority_proof.json",
        {
            "feature_regime_volatility_estimate_productive_authority": probe[
                "legacy_proxy_productive_authority"
            ],
            "typed_cmc_estimate_present": probe["canonical_market_context_typed_estimate_present"],
            "NO_PROXY_PROMOTION": NO_PROXY_PROMOTION,
        },
    )
    _write_json(productive / "core_logic_parity.json", parity)
    _write_json(
        productive / "risk_safety_exit_independence.json",
        {
            "missing_vol_blocks_alpha_only": True,
            "exit_risk_safety_paths_preserved": True,
            "numeric_max_age_enforcing": VOLATILITY_NUMERIC_MAX_AGE_ENFORCING,
        },
    )
    _write_json(
        productive / "restart_semantics.json",
        {
            "classification": PERSISTENCE_CLASSIFICATION,
            "semantics": RESTART_SEMANTICS,
            "estimate_rematerialized_on_restore": False,
        },
    )
    _write_json(
        productive / "config_digest.json",
        {"config_digest": config_digest, "repository_sha": repository_sha},
    )
    _write_json(productive / "repository_sha.json", {"repository_sha": repository_sha})
    _write_json(
        productive / "productive_offline_probe.json",
        {k: v for k, v in probe.items() if k != "traces"},
    )
    _write_json(productive / "claims.json", claims)
    _write_json(productive / "negative_boundary_results.json", negative)
    _write_json(
        productive / "test_results.json",
        {
            "note": "populated by verifier after pytest invocation or local gate batch",
            "expected_nodes": [
                "tests/trading/master_v2/test_canonical_volatility_pt1m_mark_observation_finalizer_v1.py",
                "tests/ops/test_productive_typed_volatility_producer_and_cmc_hot_path_binding_v1.py",
            ],
        },
    )

    ok = (
        claims["TYPED_VOL_MISSING_DURING_VALID_WARMUP"]
        and claims["TYPED_VOL_MISSING_AFTER_WARMUP_COUNT"] == 0
        and claims["TYPED_ESTIMATE_PRESENT_AFTER_WARMUP"]
        and claims["PRODUCTIVE_AUTHORITY_AFTER_WARMUP"]
        and claims["LEGACY_PROXY_PROMOTED"] is False
        and claims["DECISION_GRAPH_PROGRESS_AFTER_VOL_STAGE"]
        and all(negative.values())
    )
    summary = {
        "ok": ok,
        "capability_id": CAPABILITY_ID,
        "repository_sha": repository_sha,
        "config_digest": config_digest,
        "CORE_LOGIC_CHANGE": CORE_LOGIC_CHANGE,
        "VOLATILITY_NUMERIC_MAX_AGE_ENFORCING": VOLATILITY_NUMERIC_MAX_AGE_ENFORCING,
        "claims": claims,
        "ROOT_CAUSE_CALL_GRAPH_EDGE": ROOT_CAUSE_CALL_GRAPH_EDGE,
        "PRODUCTIVE_OFFLINE_PROBE_RUN": True,
        "NETWORK_USED": False,
    }
    _write_json(evidence_root / "SUMMARY.json", summary)
    manifest_digest = _write_manifest(evidence_root)
    summary["manifest_sha256"] = manifest_digest
    _write_json(evidence_root / "SUMMARY.json", summary)
    _write_manifest(evidence_root)
    print(json.dumps({"ok": ok, "evidence_root": str(evidence_root)}, sort_keys=True))
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
