#!/usr/bin/env python3
"""Run MV2 zero-trade per-bar decision-outcome diagnostic v1 (offline observability).

Operator GO: GO_MV2_ZERO_TRADE_PER_BAR_DECISION_OUTCOME_DIAGNOSTIC_V1
No economic reevaluation, no strategy/decision/sizing/runtime mutation.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))
if str(_REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT / "src"))
if str(_REPO_ROOT / "src" / "trading") not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT / "src" / "trading"))

from scripts.ops.primary_evidence_retention_v0 import (  # noqa: E402
    verify_manifest_sha256,
    write_manifest_sha256,
)
from src.backtest.admissible_versioned_futures_dataset_v1 import (  # noqa: E402
    DatasetProfileBindingV1,
    DatasetProfileV1,
    ExecutionCostBindingV1,
    L1ObservationStatusV1,
)
from src.backtest.mv2_research_wiring_v1 import (  # noqa: E402
    MV2_REQUIRED_INSTRUMENT_ID,
    run_mv2_research_backtest_wiring_v1,
)
from src.research.final_research_fleet_v0_versioned_binding_manifest_contract_v0 import (  # noqa: E402
    CANONICAL_INSTRUMENT_ID,
)
from src.research.mv2_zero_trade_per_bar_decision_outcome_diagnostic_v1 import (  # noqa: E402
    DIAGNOSTIC_ID,
    GO_TOKEN,
    EntryBarDiagnosticRecordV1,
    aggregate_entry_bar_diagnostics_v1,
    build_observational_snapshot_from_replay_v1,
    classify_entry_bar_snapshot_v1,
    is_strategy_entry_raw_signal_v1,
    render_audit_markdown_v1,
    stable_digest_v1,
)
from src.strategies.bollinger import BollingerBandsStrategy  # noqa: E402

CONFIRM_GO = GO_TOKEN
DEFAULT_CONFIG = (
    _REPO_ROOT / "config/research/mv2_zero_trade_per_bar_decision_outcome_diagnostic_v1.json"
)
DEFAULT_ARCHIVE_ROOT = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z"
)
OUTPUT_PREFIX = "mv2_zero_trade_per_bar_decision_outcome_diagnostic_v1"


def _utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _die(message: str, code: int = 2) -> None:
    print(message, file=sys.stderr)
    raise SystemExit(code)


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"not_object:{path}")
    return payload


def _count_entry_bars(bars: pd.DataFrame, *, strategy_params: dict[str, Any]) -> int:
    strategy = BollingerBandsStrategy(
        bb_period=int(strategy_params.get("bb_period", 20)),
        bb_std=float(strategy_params.get("bb_std", 2.0)),
        entry_threshold=float(strategy_params.get("entry_threshold", 0.95)),
        exit_threshold=float(strategy_params.get("exit_threshold", 0.5)),
    )
    signals = strategy.generate_signals(bars)
    return int((signals == 1).sum())


def _diagnose_member(
    *,
    bars: pd.DataFrame,
    cfg: dict[str, Any],
    panel_member_instrument_id: str,
    profile_binding: DatasetProfileBindingV1,
) -> tuple[list[EntryBarDiagnosticRecordV1], int]:
    expected_entries = _count_entry_bars(
        bars,
        strategy_params=dict(cfg.get("economic_evaluation_v1", {}).get("strategy_params", {})),
    )
    collected: list[EntryBarDiagnosticRecordV1] = []

    def _hook(**kwargs: Any) -> None:
        raw = int(kwargs["raw_strategy_signal"])
        if not is_strategy_entry_raw_signal_v1(raw):
            return
        snapshot = build_observational_snapshot_from_replay_v1(
            trading_epoch=int(kwargs["trading_epoch"]),
            bar_timestamp=str(kwargs["bar_timestamp"]),
            instrument_id=str(kwargs["instrument_id"]),
            panel_member_instrument_id=str(kwargs["panel_member_instrument_id"]),
            raw_strategy_signal=raw,
            warmup_status=str(kwargs["warmup_status"]),
            warmup_skipped=bool(kwargs["warmup_skipped"]),
            context_id=str(kwargs["context_id"]),
            context_input_digest=str(kwargs["context_input_digest"]),
            agreement_material=kwargs.get("agreement_material"),
            intermediate=kwargs.get("intermediate"),
            decision_outcome=kwargs.get("decision_outcome"),
            evidence_reason_codes=tuple(kwargs.get("evidence_reason_codes") or ()),
            mapped_position_signal=int(kwargs["mapped_position_signal"]),
            price_path=kwargs.get("price_path"),
            regime_id=kwargs.get("regime_id"),
            eligible_strategy_count=kwargs.get("eligible_strategy_count"),
            regime_wildcard_matched=kwargs.get("regime_wildcard_matched"),
            fail_reasons=tuple(kwargs.get("fail_reasons") or ()),
            replay_input_built=bool(kwargs["replay_input_built"]),
            decision_authority_reached=bool(kwargs["decision_authority_reached"]),
        )
        collected.append(classify_entry_bar_snapshot_v1(snapshot))

    run_mv2_research_backtest_wiring_v1(
        bars,
        strategy_id=str(cfg["economic_evaluation_v1"]["strategy_id"]),
        cfg=cfg,
        instrument_id=CANONICAL_INSTRUMENT_ID,
        profile_binding=profile_binding,
        observational_bar_hook=_hook,
        observational_panel_member_instrument_id=panel_member_instrument_id,
    )
    if len(collected) != expected_entries:
        raise ValueError(
            "entry_bar_hook_reconciliation_failed:"
            f"panel_member={panel_member_instrument_id}:"
            f"expected={expected_entries}:collected={len(collected)}"
        )
    return collected, expected_entries


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=CONFIRM_GO)
    parser.add_argument("--go-token", required=True)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--archive-root", type=Path, default=DEFAULT_ARCHIVE_ROOT)
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--eval-only", action="store_true")
    parser.add_argument("--max-panel-members", type=int, default=None)
    args = parser.parse_args(argv)

    if args.go_token != CONFIRM_GO:
        _die(f"go_token_mismatch:expected={CONFIRM_GO}")

    config = _load_json(args.config)
    source_evidence = Path(str(config["source_durable_evidence_dir"]))
    if not source_evidence.is_dir():
        _die(f"source_evidence_missing:{source_evidence}")

    runtime_cfg_path = source_evidence / "runtime_evaluation_config.json"
    cfg = _load_json(runtime_cfg_path)
    binding_path = _REPO_ROOT / str(config["binding_ref"])
    binding = _load_json(binding_path)

    scratch = source_evidence / "scratch"
    member_dirs = sorted(
        path for path in scratch.iterdir() if path.is_dir() and path.name.startswith("okx_")
    )
    if not member_dirs:
        _die(f"no_panel_member_scratch:{scratch}")

    # Deterministic panel member order from binding when available.
    panel_ids: list[str] = []
    instrument_binding = binding.get("binding", {}).get("instrument_binding", {})
    eligible = instrument_binding.get("eligible_instrument_ids")
    if isinstance(eligible, list) and eligible:
        panel_ids = [str(item) for item in eligible]
    else:
        panel_ids = [
            path.name.replace("okx_linear_perpetual_", "okx:linear_perpetual:")
            .replace("_USDT_USDT_perp", ":USDT:USDT:perp")
            .replace("_", ":", 2)
            for path in member_dirs
        ]
        # Fallback mapping for scratch naming okx_linear_perpetual_SYMBOL_USDT_USDT_perp
        repaired: list[str] = []
        for path in member_dirs:
            # okx_linear_perpetual_1INCH_USDT_USDT_perp -> okx:linear_perpetual:1INCH:USDT:USDT:perp
            parts = path.name.split("_")
            # ['okx','linear','perpetual', SYMBOL..., 'USDT','USDT','perp']
            if len(parts) < 7:
                continue
            symbol = "_".join(parts[3:-3])
            repaired.append(f"okx:linear_perpetual:{symbol}:USDT:USDT:perp")
        if repaired:
            panel_ids = repaired

    eval_instrument_id = str(
        config.get("evaluation_instrument_id")
        or panel_ids[0]
        or "okx:linear_perpetual:1INCH:USDT:USDT:perp"
    )
    if args.max_panel_members is not None:
        panel_ids = panel_ids[: max(0, int(args.max_panel_members))]
    if args.eval_only:
        panel_ids = [eval_instrument_id]

    profile_binding = DatasetProfileBindingV1(
        dataset_profile=DatasetProfileV1.ECONOMIC_RESEARCH_V1,
        execution_cost_binding=ExecutionCostBindingV1(
            spread_model_version="research_conservative_bps_v1",
            execution_price_observation_source="MODELLED_NOT_OBSERVED",
            conservative_half_spread_bps=5.0,
        ),
        l1_observation_status=L1ObservationStatusV1.EXECUTION_MODEL_BOUND_NOT_OBSERVED,
    )

    stamp = _utc_stamp()
    out_dir = args.output_dir or (args.archive_root / "research" / f"{OUTPUT_PREFIX}_{stamp}")
    out_dir.mkdir(parents=True, exist_ok=True)

    eval_records: list[EntryBarDiagnosticRecordV1] = []
    panel_records: list[EntryBarDiagnosticRecordV1] = []
    per_member_expected: dict[str, int] = {}

    for member_id in panel_ids:
        member_dir = scratch / member_id.replace(":", "_")
        bars_path = member_dir / "bars.parquet"
        if not bars_path.is_file():
            # also try datasets path used by candidate run
            alt = scratch / "datasets" / member_id.replace(":", "_") / "bars.parquet"
            if alt.is_file():
                bars_path = alt
            else:
                _die(f"bars_missing:{member_id}:{bars_path}")
        bars = pd.read_parquet(bars_path)
        records, expected = _diagnose_member(
            bars=bars,
            cfg=cfg,
            panel_member_instrument_id=member_id,
            profile_binding=profile_binding,
        )
        per_member_expected[member_id] = expected
        panel_records.extend(records)
        if member_id == eval_instrument_id:
            eval_records = list(records)
        print(
            json.dumps(
                {
                    "member": member_id,
                    "entry_bars": expected,
                    "classified": len(records),
                },
                sort_keys=True,
            ),
            flush=True,
        )

    if not eval_records and eval_instrument_id in per_member_expected:
        # Eval instrument may be absent from truncated panel; re-run dedicated.
        member_dir = scratch / eval_instrument_id.replace(":", "_")
        bars = pd.read_parquet(member_dir / "bars.parquet")
        eval_records, _ = _diagnose_member(
            bars=bars,
            cfg=cfg,
            panel_member_instrument_id=eval_instrument_id,
            profile_binding=profile_binding,
        )

    eval_aggregate = aggregate_entry_bar_diagnostics_v1(
        eval_records,
        expected_entry_count=per_member_expected.get(eval_instrument_id, len(eval_records)),
    )
    panel_aggregate = aggregate_entry_bar_diagnostics_v1(
        panel_records,
        expected_entry_count=sum(per_member_expected.get(mid, 0) for mid in panel_ids),
    )

    provenance = {
        "base_sha": str(config.get("base_sha", "")),
        "binding_id": str(binding.get("binding_id") or binding.get("artifact_kind") or ""),
        "binding_ref": str(config["binding_ref"]),
        "binding_digest": str(config.get("binding_digest", "")),
        "source_durable_evidence_dir": str(source_evidence),
        "runtime_evaluation_config": str(runtime_cfg_path),
        "canonical_wiring_instrument_id": MV2_REQUIRED_INSTRUMENT_ID,
        "evaluation_instrument_id": eval_instrument_id,
        "panel_member_count": len(panel_ids),
        "go_token": CONFIRM_GO,
        "diagnostic_id": DIAGNOSTIC_ID,
        "created_at_utc": stamp,
    }
    provenance["provenance_digest"] = stable_digest_v1(provenance)

    detail_path = out_dir / "entry_bar_decision_outcomes.jsonl"
    with detail_path.open("w", encoding="utf-8") as handle:
        for record in panel_records:
            handle.write(json.dumps(record.to_dict(), sort_keys=True) + "\n")

    aggregate_payload = {
        "eval_instrument": eval_aggregate.to_dict(),
        "panel": panel_aggregate.to_dict(),
        "per_member_expected_entry_counts": dict(sorted(per_member_expected.items())),
        "provenance": provenance,
    }
    # Drop bulky nested records from aggregate JSON (detail lives in JSONL).
    aggregate_payload["eval_instrument"].pop("records", None)
    aggregate_payload["panel"].pop("records", None)
    (out_dir / "entry_bar_decision_outcome_aggregate.json").write_text(
        json.dumps(aggregate_payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (out_dir / "AUDIT.md").write_text(
        render_audit_markdown_v1(
            eval_aggregate=eval_aggregate,
            panel_aggregate=panel_aggregate,
            provenance=provenance,
        ),
        encoding="utf-8",
    )
    (out_dir / "provenance.json").write_text(
        json.dumps(provenance, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (out_dir / "config_snapshot.json").write_text(
        json.dumps(config, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    write_manifest_sha256(out_dir)
    ok, message = verify_manifest_sha256(out_dir)
    (out_dir / "MANIFEST_VERIFY.log").write_text(
        f"verify_ok={ok}\nmessage={message}\nMANIFEST_VERIFY_RC={0 if ok else 1}\n",
        encoding="utf-8",
    )
    if not ok:
        _die(f"manifest_verify_failed:{message}")

    print(
        json.dumps(
            {
                "ok": True,
                "output_dir": str(out_dir),
                "eval_entry_bars": eval_aggregate.entry_bar_count,
                "panel_entry_bars": panel_aggregate.entry_bar_count,
                "dominant_first_failed_stage": panel_aggregate.dominant_first_failed_stage,
                "price_path_suspicion_status": panel_aggregate.price_path_suspicion_status,
                "regime_id_suspicion_status": panel_aggregate.regime_id_suspicion_status,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
