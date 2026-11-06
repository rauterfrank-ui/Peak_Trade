#!/usr/bin/env python3
"""Fetch bound-period historical OKX PT1H futures sources for cross-sectional v0.

Read-only public GET to OKX v5 allowlist. No auth, no orders, no runtime effect.
Operator GO: GO_BOUNDED_CROSS_SECTIONAL_RELATIVE_STRENGTH_V0_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_V2
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

CONFIRM_TOKEN = (
    "GO_BOUNDED_CROSS_SECTIONAL_RELATIVE_STRENGTH_V0_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_V2"
)

BOUND_WARMUP_START_UTC = "2024-05-25T00:00:00Z"
BOUND_PERIOD_END_UTC = "2024-06-01T01:00:00Z"
ACQUISITION_SOURCE = "okx_public_rest_history_candles_v5"
BAR_GRANULARITY = "PT1H"


def _load_materialize_okx_module() -> Any:
    script = _REPO_ROOT / "scripts/ops/materialize_okx_production_lifecycle_and_pt1h_panel_v1.py"
    spec = importlib.util.spec_from_file_location("materialize_okx_pt1h_panel_v1", script)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def _utc_to_ms(value: str) -> int:
    dt = datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    return int(dt.timestamp() * 1000)


def _die(msg: str, code: int = 2) -> None:
    print(msg, file=sys.stderr)
    raise SystemExit(code)


def run_historical_fetch(
    *,
    confirm: str,
    target_staging_root: Path,
    durable_evidence_root: Path,
    period_start_utc: str = BOUND_WARMUP_START_UTC,
    period_end_utc: str = BOUND_PERIOD_END_UTC,
    timeout_seconds: float = 15.0,
    max_response_bytes: int = 50_000_000,
    fetcher: Callable[..., tuple[int, bytes, dict[str, str]]] | None = None,
) -> dict[str, Any]:
    if confirm != CONFIRM_TOKEN:
        _die(f"ERR: confirm_go_token_required:{CONFIRM_TOKEN}")
    if target_staging_root.exists():
        _die(f"ERR: target_staging_root_exists:{target_staging_root}")

    okx_mod = _load_materialize_okx_module()._load_okx_ingest_module()
    mat_mod = _load_materialize_okx_module()
    fetcher = fetcher or okx_mod.okx_public_fetch_v1
    ts_slug = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    tmp_root = target_staging_root.parent / f".tmp_historical_{ts_slug}"
    raw_dir = tmp_root / "raw"
    lifecycle_dir = tmp_root / "lifecycle"
    panel_dir = tmp_root / "panel"
    reports_dir = tmp_root / "reports"
    for path in (raw_dir, lifecycle_dir, panel_dir, reports_dir):
        path.mkdir(parents=True, exist_ok=True)

    retrieval_ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    source_snapshot_ref = (
        f"okx_public_historical_pt1h:{period_start_utc}:{period_end_utc}:{ts_slug}"
    )
    start_ms = _utc_to_ms(period_start_utc)
    end_ms = _utc_to_ms(period_end_utc)

    rate_limiter = okx_mod.RateLimiter()
    instruments = mat_mod.fetch_all_swap_instruments(
        okx_mod,
        fetcher=fetcher,
        rate_limiter=rate_limiter,
        timeout_seconds=timeout_seconds,
        max_response_bytes=max_response_bytes,
        raw_dir=raw_dir,
    )

    from src.research.okx_production_instrument_lifecycle_source_v1 import (
        MIN_ELIGIBLE_INSTRUMENT_COUNT,
        SOURCE_ID,
        build_okx_lifecycle_source_snapshot_v1,
        build_lifecycle_source_observations_v1,
    )
    from src.research.pit_futures_instrument_lifecycle_registry_persistence_v1 import (
        OverwritePolicy,
        write_registry_snapshot_v1,
    )
    from src.research.pit_futures_instrument_lifecycle_registry_v1 import (
        assemble_registry_snapshot_v1,
        format_registry_reference_v1,
    )
    from src.research.pit_futures_instrument_lifecycle_registry_validator_v1 import (
        ValidationVerdict,
    )
    from src.research.pit_futures_universe_manifest_v1 import compute_sha256_digest
    from src.research.pit_okx_pt1h_panel_ohlcv_dataset_v1 import (
        InstrumentPanelSeriesV1,
        compute_series_digest,
        filter_panel_series_to_full_bound_calendar_coverage_v1,
        validate_panel_series_v1,
    )
    from src.research.instrument_id_canonicalization_v1 import (
        InstrumentIdCanonicalizationInputV1,
        canonicalize_instrument_id_v1,
    )

    lifecycle_snapshot_input = build_okx_lifecycle_source_snapshot_v1(
        instruments,
        retrieval_timestamp_utc=retrieval_ts,
        source_snapshot_ref=source_snapshot_ref,
    )
    if len(lifecycle_snapshot_input.eligible_instruments) < MIN_ELIGIBLE_INSTRUMENT_COUNT:
        _die(
            "ERR: FAIL_CLOSED_INSUFFICIENT_ELIGIBLE_INSTRUMENTS:"
            f"{len(lifecycle_snapshot_input.eligible_instruments)}"
        )

    config_digest = compute_sha256_digest(
        {
            "acquisition_source": ACQUISITION_SOURCE,
            "bar_granularity": BAR_GRANULARITY,
            "period_start_utc": period_start_utc,
            "period_end_utc": period_end_utc,
            "source_snapshot_ref": source_snapshot_ref,
        }
    )
    observations = build_lifecycle_source_observations_v1(lifecycle_snapshot_input)
    assembly = assemble_registry_snapshot_v1(
        observations,
        generated_at=retrieval_ts,
        venue_scope=("okx",),
        config_digest=config_digest,
        implementation_digest=config_digest,
        registered_sources=frozenset({SOURCE_ID}),
        approved_snapshot_digests=frozenset({lifecycle_snapshot_input.raw_snapshot_digest}),
    )
    if not assembly.success or assembly.snapshot is None:
        _die(f"ERR: lifecycle_registry_assembly_failed:{assembly.error_codes}")

    validation = __import__(
        "src.research.pit_futures_instrument_lifecycle_registry_validator_v1",
        fromlist=["validate_pit_futures_instrument_lifecycle_registry_snapshot_v1"],
    ).validate_pit_futures_instrument_lifecycle_registry_snapshot_v1(assembly.snapshot)
    if validation.verdict is not ValidationVerdict.ACCEPTED:
        _die(f"ERR: lifecycle_registry_validation_failed:{validation.error_codes}")

    persist_result = write_registry_snapshot_v1(
        assembly.snapshot,
        root_dir=lifecycle_dir,
        relative_path="registry_snapshot_v1.json",
        overwrite_policy=OverwritePolicy.FAIL_IF_EXISTS,
    )
    if not persist_result.success:
        _die(f"ERR: lifecycle_registry_persist_failed:{persist_result.error_codes}")

    registry_ref = format_registry_reference_v1(
        artifact_id="okx_production_lifecycle_v1",
        registry_snapshot_digest=assembly.snapshot.registry_snapshot_digest,
    )
    (lifecycle_dir / "REGISTRY_REFERENCE.txt").write_text(registry_ref + "\n", encoding="utf-8")
    (lifecycle_dir / "SOURCE_REGISTRATION.json").write_text(
        json.dumps(
            {
                "production_lifecycle_source_id": SOURCE_ID,
                "registered": True,
                "source_snapshot_ref": source_snapshot_ref,
                "source_snapshot_digest": lifecycle_snapshot_input.raw_snapshot_digest,
                "acquisition_source": ACQUISITION_SOURCE,
                "period_start_utc": period_start_utc,
                "period_end_utc": period_end_utc,
                "retrieval_timestamp_utc": retrieval_ts,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    panel_series: list[InstrumentPanelSeriesV1] = []
    provenance_entries: list[dict[str, Any]] = []
    for metadata in lifecycle_snapshot_input.eligible_instruments:
        canon = canonicalize_instrument_id_v1(
            InstrumentIdCanonicalizationInputV1(
                venue_id="okx",
                market_type="futures",
                contract_type="linear_perpetual",
                base_asset=metadata.base_asset,
                quote_asset="USDT",
                settlement_asset="USDT",
                venue_symbol=metadata.inst_id,
            )
        )
        if not canon.success or canon.instrument_id is None:
            continue
        rows = mat_mod.fetch_pt1h_candles_for_instrument(
            okx_mod,
            inst_id=metadata.inst_id,
            fetcher=fetcher,
            rate_limiter=rate_limiter,
            timeout_seconds=timeout_seconds,
            max_response_bytes=max_response_bytes,
            raw_dir=raw_dir,
            start_ms=start_ms,
            end_ms=end_ms,
        )
        if not rows:
            continue
        bars = mat_mod.normalize_candles_to_panel_bars(canon.instrument_id, rows)
        bound_bars = tuple(
            bar
            for bar in bars
            if period_start_utc <= bar.timestamp_utc <= period_end_utc and bar.is_final
        )
        if not bound_bars:
            continue
        series = InstrumentPanelSeriesV1(
            instrument_id=canon.instrument_id,
            native_instrument_id=metadata.inst_id,
            bars=bound_bars,
            series_digest=compute_series_digest(
                InstrumentPanelSeriesV1(
                    instrument_id=canon.instrument_id,
                    native_instrument_id=metadata.inst_id,
                    bars=bound_bars,
                    series_digest="0" * 64,
                )
            ),
        )
        panel_series.append(series)
        provenance_entries.append(
            {
                "instrument_id": canon.instrument_id,
                "native_instrument_id": metadata.inst_id,
                "row_count_bound": len(bound_bars),
                "first_timestamp_utc": bound_bars[0].timestamp_utc,
                "last_timestamp_utc": bound_bars[-1].timestamp_utc,
            }
        )

    membership_filter = filter_panel_series_to_full_bound_calendar_coverage_v1(
        tuple(panel_series),
        period_start_utc=period_start_utc,
        period_end_utc=period_end_utc,
    )
    panel_series = list(membership_filter.selected)
    (reports_dir / "PANEL_MEMBERSHIP_FILTER.json").write_text(
        json.dumps(
            {
                "period_start_utc": period_start_utc,
                "period_end_utc": period_end_utc,
                "candidate_count": len(provenance_entries),
                "selected_count": len(panel_series),
                "excluded_empty_count": membership_filter.excluded_empty_count,
                "excluded_partial_count": membership_filter.excluded_partial_count,
                "filter_policy": "full_bound_panel_calendar_coverage_exact_timestamps",
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    if len(panel_series) < MIN_ELIGIBLE_INSTRUMENT_COUNT:
        _die(
            "ERR: FAIL_CLOSED_INSUFFICIENT_COMMON_HISTORY:"
            f"{len(panel_series)}:"
            f"excluded_partial={membership_filter.excluded_partial_count}:"
            f"excluded_empty={membership_filter.excluded_empty_count}"
        )

    panel_validation = validate_panel_series_v1(
        tuple(panel_series),
        min_instruments=MIN_ELIGIBLE_INSTRUMENT_COUNT,
        generation_cutoff_utc=retrieval_ts,
    )
    if not panel_validation.valid:
        _die(f"ERR: panel_validation_failed:{panel_validation.error_codes}")

    normalized_rows = []
    for series in panel_series:
        for bar in series.bars:
            normalized_rows.append(asdict(bar))
    (panel_dir / "normalized_panel_bars.json").write_text(
        json.dumps(normalized_rows, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (reports_dir / "SOURCE_PROVENANCE.json").write_text(
        json.dumps(
            {
                "acquisition_source": ACQUISITION_SOURCE,
                "period_start_utc": period_start_utc,
                "period_end_utc": period_end_utc,
                "retrieval_timestamp_utc": retrieval_ts,
                "entries": provenance_entries,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    (reports_dir / "PERIOD_BINDING.json").write_text(
        json.dumps(
            {
                "bound_warmup_start_utc": period_start_utc,
                "bound_period_end_utc": period_end_utc,
                "bar_granularity": BAR_GRANULARITY,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    target_staging_root.parent.mkdir(parents=True, exist_ok=True)
    tmp_root.rename(target_staging_root)

    evidence_dir = (
        durable_evidence_root
        / "implementation"
        / f"bounded_cross_sectional_historical_pt1h_source_fetch_v0_{ts_slug}"
    )
    evidence_dir.mkdir(parents=True, exist_ok=False)
    (evidence_dir / "FETCH_RESULT.json").write_text(
        json.dumps(
            {
                "verdict": "HISTORICAL_SOURCE_FETCH_COMPLETE",
                "target_staging_root": str(target_staging_root),
                "period_start_utc": period_start_utc,
                "period_end_utc": period_end_utc,
                "instrument_count": len(panel_series),
                "source_snapshot_ref": source_snapshot_ref,
                "source_snapshot_digest": lifecycle_snapshot_input.raw_snapshot_digest,
                "provenance_entry_count": len(provenance_entries),
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    from scripts.ops import primary_evidence_retention_v0 as retention

    rc, verify_msg = retention.finalize_durable_bundle_manifest(evidence_dir)
    return {
        "verdict": "HISTORICAL_SOURCE_FETCH_COMPLETE",
        "target_staging_root": str(target_staging_root),
        "period_start_utc": period_start_utc,
        "period_end_utc": period_end_utc,
        "instrument_count": len(panel_series),
        "source_snapshot_digest": lifecycle_snapshot_input.raw_snapshot_digest,
        "durable_evidence_path": str(evidence_dir),
        "manifest_verify_rc": rc,
        "manifest_verify_msg": verify_msg,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--confirm", required=True)
    parser.add_argument("--target-staging-root", type=Path, required=True)
    parser.add_argument("--durable-evidence-root", type=Path, required=True)
    parser.add_argument("--period-start-utc", default=BOUND_WARMUP_START_UTC)
    parser.add_argument("--period-end-utc", default=BOUND_PERIOD_END_UTC)
    args = parser.parse_args()
    result = run_historical_fetch(
        confirm=args.confirm,
        target_staging_root=args.target_staging_root,
        durable_evidence_root=args.durable_evidence_root,
        period_start_utc=args.period_start_utc,
        period_end_utc=args.period_end_utc,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
