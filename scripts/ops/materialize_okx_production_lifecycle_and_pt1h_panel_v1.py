#!/usr/bin/env python3
"""Materialize OKX production lifecycle source and PT1H multi-instrument panel v1.

Public GET allowlist only. No auth, no orders, no runtime effect.
Operator GO: GO_BOUNDED_OKX_PRODUCTION_LIFECYCLE_SOURCE_REGISTRATION_AND_PT1H_PANEL_OHLCV_INGEST_V0
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from dataclasses import asdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

CONFIRM_TOKEN = (
    "GO_BOUNDED_OKX_PRODUCTION_LIFECYCLE_SOURCE_REGISTRATION_AND_PT1H_PANEL_OHLCV_INGEST_V0"
)
DEFAULT_STAGING_WINDOW_DAYS = 14
MIN_ELIGIBLE_INSTRUMENTS = 5

from src.research.okx_production_instrument_lifecycle_source_v1 import (  # noqa: E402
    MIN_ELIGIBLE_INSTRUMENT_COUNT,
    OkxLifecycleSourceErrorCode,
    SOURCE_ID,
    UNIVERSE_POLICY_ID,
    UNIVERSE_POLICY_VERSION,
    build_lifecycle_source_observations_v1,
    build_okx_lifecycle_source_snapshot_v1,
    compute_raw_instruments_snapshot_digest,
)
from src.research.pit_futures_instrument_lifecycle_registry_persistence_v1 import (  # noqa: E402
    OverwritePolicy,
    write_registry_snapshot_v1,
)
from src.research.pit_futures_instrument_lifecycle_registry_v1 import (  # noqa: E402
    assemble_registry_snapshot_v1,
    format_registry_reference_v1,
    registry_snapshot_to_dict,
)
from src.research.pit_futures_instrument_lifecycle_registry_validator_v1 import (  # noqa: E402
    ValidationVerdict,
    validate_pit_futures_instrument_lifecycle_registry_snapshot_v1,
)
from src.research.pit_futures_universe_manifest_v1 import compute_sha256_digest  # noqa: E402
from src.research.pit_okx_pt1h_panel_ohlcv_dataset_v1 import (  # noqa: E402
    BAR_GRANULARITY,
    OKX_BAR_PARAM,
    PANEL_ID,
    InstrumentPanelSeriesV1,
    PanelBarV1,
    build_panel_dataset_manifest_v1,
    compute_implementation_digest,
    compute_series_digest,
    panel_manifest_to_dict,
    validate_panel_series_v1,
)


def _load_okx_ingest_module() -> Any:
    script = (
        _REPO_ROOT
        / "scripts/ops/ingest_okx_futures_public_market_data_canonical_dataset_staging_v1.py"
    )
    spec = importlib.util.spec_from_file_location(
        "ingest_okx_futures_public_market_data_canonical_dataset_staging_v1", script
    )
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def _utc_now_z() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _ms_to_rfc3339_utc(ms: int) -> str:
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _die(msg: str, code: int = 2) -> None:
    print(msg, file=sys.stderr)
    raise SystemExit(code)


def fetch_all_swap_instruments(
    okx_mod: Any,
    *,
    fetcher: Callable[..., tuple[int, bytes, dict[str, str]]],
    rate_limiter: Any,
    timeout_seconds: float,
    max_response_bytes: int,
    raw_dir: Path,
) -> list[dict[str, Any]]:
    params = {"instType": "SWAP"}
    url = okx_mod._build_url("/api/v5/public/instruments", params)
    req_at = _utc_now_z()
    status, body, _ = okx_mod.fetch_with_retry(
        url,
        timeout_seconds=timeout_seconds,
        max_response_bytes=max_response_bytes,
        rate_limiter=rate_limiter,
        fetcher=fetcher,
    )
    resp_at = _utc_now_z()
    digest = okx_mod._sha256_bytes(body)
    raw_path = raw_dir / f"instruments_all_swap_{digest[:16]}.json"
    raw_path.write_bytes(body)
    payload = okx_mod._parse_okx_json(body)
    okx_code = str(payload.get("code", ""))
    data = payload.get("data") or []
    if status < 200 or status >= 300 or okx_code != "0" or not isinstance(data, list):
        _die(f"ERR: instruments_fetch_failed:http_{status}:code_{okx_code}")
    return [dict(item) for item in data if isinstance(item, Mapping)]


def fetch_pt1h_candles_for_instrument(
    okx_mod: Any,
    *,
    inst_id: str,
    fetcher: Callable[..., tuple[int, bytes, dict[str, str]]],
    rate_limiter: Any,
    timeout_seconds: float,
    max_response_bytes: int,
    raw_dir: Path,
    start_ms: int,
    end_ms: int,
) -> list[list[Any]]:
    request_log: list[Any] = []
    return okx_mod.paginate_candles(
        path="/api/v5/market/history-candles",
        params_base={"instId": inst_id, "bar": OKX_BAR_PARAM},
        fetcher=fetcher,
        rate_limiter=rate_limiter,
        timeout_seconds=timeout_seconds,
        max_response_bytes=max_response_bytes,
        raw_dir=raw_dir,
        request_log=request_log,
        start_ms=start_ms,
        end_ms=end_ms,
        series_name=f"ohlcv_{inst_id.replace('-', '_').lower()}",
    )


def normalize_candles_to_panel_bars(
    instrument_id: str,
    rows: Sequence[Sequence[Any]],
) -> tuple[PanelBarV1, ...]:
    bars: list[PanelBarV1] = []
    for row in rows:
        ts = _ms_to_rfc3339_utc(int(str(row[0])))
        is_final = str(row[8]) == "1" if len(row) >= 9 else str(row[5]) == "1"
        bars.append(
            PanelBarV1(
                instrument_id=instrument_id,
                timestamp_utc=ts,
                open=str(row[1]),
                high=str(row[2]),
                low=str(row[3]),
                close=str(row[4]),
                volume=str(row[5]),
                is_final=is_final,
            )
        )
    return tuple(bars)


def compute_common_period_bounds(
    series_list: Sequence[InstrumentPanelSeriesV1],
) -> tuple[str, str]:
    if not series_list:
        _die("ERR: no_panel_series")
    common_starts = [series.bars[0].timestamp_utc for series in series_list if series.bars]
    common_ends = [series.bars[-1].timestamp_utc for series in series_list if series.bars]
    if not common_starts or not common_ends:
        _die("ERR: empty_panel_series")
    return max(common_starts), min(common_ends)


def align_series_to_common_period(
    series_list: Sequence[InstrumentPanelSeriesV1],
    *,
    period_start_utc: str,
    period_end_utc: str,
) -> tuple[InstrumentPanelSeriesV1, ...]:
    aligned: list[InstrumentPanelSeriesV1] = []
    for series in series_list:
        bars = tuple(
            bar for bar in series.bars if period_start_utc <= bar.timestamp_utc <= period_end_utc
        )
        aligned.append(
            InstrumentPanelSeriesV1(
                instrument_id=series.instrument_id,
                native_instrument_id=series.native_instrument_id,
                bars=bars,
                series_digest=compute_series_digest(
                    InstrumentPanelSeriesV1(
                        instrument_id=series.instrument_id,
                        native_instrument_id=series.native_instrument_id,
                        bars=bars,
                        series_digest="0" * 64,
                    )
                ),
            )
        )
    return tuple(aligned)


def run_materialization(
    *,
    confirm: str,
    target_staging_root: Path,
    durable_evidence_root: Path,
    staging_window_days: int = DEFAULT_STAGING_WINDOW_DAYS,
    timeout_seconds: float = 15.0,
    max_response_bytes: int = 50_000_000,
    fetcher: Callable[..., tuple[int, bytes, dict[str, str]]] | None = None,
    skip_network: bool = False,
) -> dict[str, Any]:
    if confirm != CONFIRM_TOKEN:
        _die("ERR: confirm token required")
    if target_staging_root.exists():
        _die(f"ERR: target_staging_root_exists:{target_staging_root}")

    okx_mod = _load_okx_ingest_module()
    fetcher = fetcher or okx_mod.okx_public_fetch_v1
    ts_slug = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    tmp_root = target_staging_root.parent / f".tmp_{ts_slug}"
    raw_dir = tmp_root / "raw"
    lifecycle_dir = tmp_root / "lifecycle"
    panel_dir = tmp_root / "panel"
    reports_dir = tmp_root / "reports"
    for path in (raw_dir, lifecycle_dir, panel_dir, reports_dir):
        path.mkdir(parents=True, exist_ok=True)

    retrieval_ts = _utc_now_z()
    source_snapshot_ref = f"okx_public_instruments_swap:{ts_slug}"

    if skip_network:
        _die("ERR: skip_network_not_supported_for_production_materialization")

    rate_limiter = okx_mod.RateLimiter()
    instruments = fetch_all_swap_instruments(
        okx_mod,
        fetcher=fetcher,
        rate_limiter=rate_limiter,
        timeout_seconds=timeout_seconds,
        max_response_bytes=max_response_bytes,
        raw_dir=raw_dir,
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
            "bar_granularity": BAR_GRANULARITY,
            "min_eligible_instruments": MIN_ELIGIBLE_INSTRUMENT_COUNT,
            "source_id": SOURCE_ID,
            "staging_window_days": staging_window_days,
            "universe_policy_id": UNIVERSE_POLICY_ID,
            "universe_policy_version": UNIVERSE_POLICY_VERSION,
        }
    )
    implementation_digest = compute_implementation_digest()
    observations = build_lifecycle_source_observations_v1(lifecycle_snapshot_input)
    assembly = assemble_registry_snapshot_v1(
        observations,
        generated_at=retrieval_ts,
        venue_scope=("okx",),
        config_digest=config_digest,
        implementation_digest=implementation_digest,
        registered_sources=frozenset({SOURCE_ID}),
        approved_snapshot_digests=frozenset({lifecycle_snapshot_input.raw_snapshot_digest}),
    )
    if not assembly.success or assembly.snapshot is None:
        _die(f"ERR: lifecycle_registry_assembly_failed:{assembly.error_codes}")

    validation = validate_pit_futures_instrument_lifecycle_registry_snapshot_v1(assembly.snapshot)
    if validation.verdict is not ValidationVerdict.ACCEPTED:
        _die(f"ERR: lifecycle_registry_validation_failed:{validation.error_codes}")

    registry_path = lifecycle_dir / "registry_snapshot_v1.json"
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
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    end_dt = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0) - timedelta(
        hours=1
    )
    start_dt = end_dt - timedelta(days=staging_window_days)
    start_ms = int(start_dt.timestamp() * 1000)
    end_ms = int(end_dt.timestamp() * 1000)

    panel_series: list[InstrumentPanelSeriesV1] = []
    eligible_members: list[dict[str, str]] = []
    for metadata in lifecycle_snapshot_input.eligible_instruments:
        from src.research.instrument_id_canonicalization_v1 import (
            InstrumentIdCanonicalizationInputV1,
            canonicalize_instrument_id_v1,
        )

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
        rows = fetch_pt1h_candles_for_instrument(
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
        bars = normalize_candles_to_panel_bars(canon.instrument_id, rows)
        series = InstrumentPanelSeriesV1(
            instrument_id=canon.instrument_id,
            native_instrument_id=metadata.inst_id,
            bars=bars,
            series_digest=compute_series_digest(
                InstrumentPanelSeriesV1(
                    instrument_id=canon.instrument_id,
                    native_instrument_id=metadata.inst_id,
                    bars=bars,
                    series_digest="0" * 64,
                )
            ),
        )
        panel_series.append(series)
        eligible_members.append(
            {
                "instrument_id": canon.instrument_id,
                "native_instrument_id": metadata.inst_id,
                "list_time_utc": metadata.list_time_utc,
            }
        )

    if len(panel_series) < MIN_ELIGIBLE_INSTRUMENT_COUNT:
        _die(f"ERR: FAIL_CLOSED_INSUFFICIENT_PANEL_MEMBERS:{len(panel_series)}")

    period_start, period_end = compute_common_period_bounds(panel_series)
    aligned_series = align_series_to_common_period(
        panel_series, period_start_utc=period_start, period_end_utc=period_end
    )
    panel_validation = validate_panel_series_v1(
        aligned_series,
        min_instruments=MIN_ELIGIBLE_INSTRUMENT_COUNT,
        generation_cutoff_utc=retrieval_ts,
    )
    if not panel_validation.valid:
        _die(f"ERR: panel_validation_failed:{panel_validation.error_codes}")

    source_provenance_digest = compute_sha256_digest(
        {
            "acquisition_method": "okx_public_rest_api_v5",
            "bar_param": OKX_BAR_PARAM,
            "raw_instruments_digest": lifecycle_snapshot_input.raw_snapshot_digest,
            "source_id": SOURCE_ID,
        }
    )
    panel_manifest = build_panel_dataset_manifest_v1(
        series_list=aligned_series,
        lifecycle_registry_ref=registry_ref,
        lifecycle_registry_digest=assembly.snapshot.registry_snapshot_digest,
        period_start_utc=period_start,
        period_end_utc=period_end,
        config_digest=config_digest,
        source_provenance_digest=source_provenance_digest,
    )
    (panel_dir / "panel_dataset_manifest.json").write_text(
        json.dumps(panel_manifest_to_dict(panel_manifest), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    normalized_rows = []
    for series in aligned_series:
        for bar in series.bars:
            normalized_rows.append(asdict(bar))
    (panel_dir / "normalized_panel_bars.json").write_text(
        json.dumps(normalized_rows, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (panel_dir / "INSTRUMENT_MEMBERSHIP.json").write_text(
        json.dumps(
            {
                "eligible_instrument_count": len(eligible_members),
                "eligible_instruments": sorted(
                    eligible_members, key=lambda item: item["instrument_id"]
                ),
                "universe_policy_id": UNIVERSE_POLICY_ID,
                "universe_policy_version": UNIVERSE_POLICY_VERSION,
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
                "evaluation_period_binding": "pit_cross_sectional_panel_common_coverage_period.v1",
                "period_start_utc": period_start,
                "period_end_utc": period_end,
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
        / "planning"
        / f"bounded_okx_production_lifecycle_source_registration_and_pt1h_panel_ohlcv_ingest_v0_{ts_slug}"
    )
    evidence_dir.mkdir(parents=True, exist_ok=True)
    for rel in (
        "lifecycle/registry_snapshot_v1.json",
        "lifecycle/REGISTRY_REFERENCE.txt",
        "lifecycle/SOURCE_REGISTRATION.json",
        "panel/panel_dataset_manifest.json",
        "panel/INSTRUMENT_MEMBERSHIP.json",
        "reports/PERIOD_BINDING.json",
    ):
        src = target_staging_root / rel
        if src.is_file():
            dst = evidence_dir / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_bytes(src.read_bytes())

    from scripts.ops import primary_evidence_retention_v0 as retention

    rc, verify_msg = retention.finalize_durable_bundle_manifest(evidence_dir)

    result = {
        "verdict": "OKX_PRODUCTION_LIFECYCLE_AND_PT1H_PANEL_MATERIALIZATION_COMPLETE",
        "production_lifecycle_source_id": SOURCE_ID,
        "production_lifecycle_source_bound": True,
        "lifecycle_registry_snapshot_materialized": True,
        "lifecycle_registry_ref": registry_ref,
        "lifecycle_data_digest": assembly.snapshot.registry_snapshot_digest,
        "eligible_instrument_count": len(eligible_members),
        "eligible_instruments": [item["instrument_id"] for item in eligible_members],
        "panel_dataset_manifest_materialized": True,
        "panel_dataset_ref": (
            f"pit_okx_pt1h_panel_ohlcv_dataset_v1:{PANEL_ID}:sha256:{panel_manifest.manifest_digest}"
        ),
        "panel_data_digest": panel_manifest.normalized_panel_digest,
        "panel_period_start": period_start,
        "panel_period_end": period_end,
        "bar_granularity": BAR_GRANULARITY,
        "target_staging_root": str(target_staging_root),
        "durable_evidence_path": str(evidence_dir),
        "manifest_verify_rc": rc,
        "manifest_verify_msg": verify_msg,
        "panel_validation": {
            "duplicate_check": panel_validation.duplicate_check,
            "gap_check": panel_validation.gap_check,
            "out_of_order_check": panel_validation.out_of_order_check,
            "future_leakage_check": panel_validation.future_leakage_check,
        },
        "registry_snapshot": registry_snapshot_to_dict(assembly.snapshot),
    }
    (evidence_dir / "MATERIALIZATION_RESULT.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    retention.finalize_durable_bundle_manifest(evidence_dir)
    _emit_machine_lines(result)
    return result


def _emit_machine_lines(result: Mapping[str, Any]) -> None:
    for key in (
        "verdict",
        "production_lifecycle_source_id",
        "production_lifecycle_source_bound",
        "lifecycle_registry_snapshot_materialized",
        "eligible_instrument_count",
        "panel_dataset_manifest_materialized",
        "panel_dataset_ref",
        "panel_data_digest",
        "lifecycle_data_digest",
        "bar_granularity",
        "panel_period_start",
        "panel_period_end",
        "manifest_verify_rc",
    ):
        print(f"{key.upper()}={result.get(key)}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Materialize OKX production lifecycle source and PT1H panel v1."
    )
    parser.add_argument("--confirm-go-token", required=True, choices=[CONFIRM_TOKEN])
    parser.add_argument("--target-staging-root", type=Path, required=True)
    parser.add_argument("--durable-evidence-root", type=Path, required=True)
    parser.add_argument("--staging-window-days", type=int, default=DEFAULT_STAGING_WINDOW_DAYS)
    parser.add_argument("--timeout-seconds", type=float, default=15.0)
    parser.add_argument("--max-response-bytes", type=int, default=50_000_000)
    ns = parser.parse_args(argv)
    run_materialization(
        confirm=ns.confirm_go_token,
        target_staging_root=ns.target_staging_root,
        durable_evidence_root=ns.durable_evidence_root,
        staging_window_days=ns.staging_window_days,
        timeout_seconds=ns.timeout_seconds,
        max_response_bytes=ns.max_response_bytes,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
