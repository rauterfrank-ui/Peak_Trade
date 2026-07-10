#!/usr/bin/env python3
"""Materialize bound open-interest panel dataset for cross_sectional_open_interest_delta_rank/v0.

Uses OKX public rubik open-interest-history endpoint with bounded pagination.
Fail-closed when required 2024 window is not covered by venue retention.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.ops.ingest_okx_futures_public_market_data_canonical_dataset_staging_v1 import (  # noqa: E402
    RateLimiter,
)
from src.research.cross_sectional_open_interest_delta_rank_v0_bound_panel_dataset_materialization_v0 import (  # noqa: E402
    BoundOpenInterestPanelMaterializationResultV0,
    MaterializationTerminalStatus,
    build_dataset_contract_v0,
    materialize_open_interest_panel_from_observations_v0,
)
from src.research.okx_historical_open_interest_public_fetch_v0 import (  # noqa: E402
    CONFIRM_GO,
    OpenInterestFetchBudgetGuardV0,
    assess_open_interest_horizon_v0,
    compute_open_interest_bounded_window_v0,
    paginate_bounded_open_interest_v0,
)

DEFAULT_OHLCV_STAGING_ROOT = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "datasets/admissible_futures/"
    "pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_research_v1/extended_chronological_v1"
)
DEFAULT_OI_STAGING_ROOT = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "datasets/admissible_futures/"
    "pit_okx_linear_usdt_non_bitcoin_open_interest_panel/v0"
)


def _die(msg: str, code: int = 2) -> None:
    print(msg, file=sys.stderr)
    raise SystemExit(code)


def _stable_digest(payload: Any) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _build_url(path: str, params: dict[str, str]) -> str:
    query = "&".join(f"{k}={v}" for k, v in sorted(params.items()))
    return f"https://www.okx.com{path}?{query}"


def _parse_json(body: bytes) -> dict[str, Any]:
    return json.loads(body.decode())


def _fetch_with_retry(
    url: str, *, fetcher: Any, **_kwargs: Any
) -> tuple[int, bytes, dict[str, str]]:
    return fetcher(url)


def run_bounded_open_interest_fetch_and_materialization_v0(
    *,
    confirm: str,
    ohlcv_staging_root: Path,
    oi_staging_root: Path,
    skip_fetch: bool = False,
    probe_only: bool = False,
) -> dict[str, Any]:
    if confirm != CONFIRM_GO:
        _die(f"ERR: confirm_go_token_required:{CONFIRM_GO}")

    ohlcv_staging_root = ohlcv_staging_root.resolve()
    oi_staging_root = oi_staging_root.resolve()
    if not ohlcv_staging_root.is_dir():
        _die(f"ERR: missing_ohlcv_staging_root:{ohlcv_staging_root}")

    from dataclasses import dataclass

    @dataclass(frozen=True)
    class _PanelMemberV0:
        instrument_id: str
        native_instrument_id: str

    manifest_path = ohlcv_staging_root / "panel" / "panel_dataset_manifest.json"
    if not manifest_path.is_file():
        _die(f"ERR: missing_panel_manifest:{manifest_path}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    instrument_ids = [str(x) for x in manifest.get("instrument_ids", [])]
    native_ids = [str(x) for x in manifest.get("native_instrument_ids", [])]
    if not instrument_ids or len(instrument_ids) != len(native_ids):
        _die("ERR: invalid_panel_manifest_member_lists")
    panel_series = [
        _PanelMemberV0(instrument_id=i, native_instrument_id=n)
        for i, n in zip(instrument_ids, native_ids)
    ]

    window = compute_open_interest_bounded_window_v0()
    probe_series = panel_series[0]
    observations_by_native: dict[str, list[Any]] = {}
    source_inventory: list[dict[str, Any]] = []

    if not skip_fetch:
        import scripts.ops.ingest_okx_futures_public_market_data_canonical_dataset_staging_v1 as ingest

        raw_dir = oi_staging_root / "raw" / "open_interest_history"
        raw_dir.mkdir(parents=True, exist_ok=True)
        budget = OpenInterestFetchBudgetGuardV0(
            max_instruments=1 if probe_only else len(panel_series),
            max_pages_per_instrument=500,
            max_total_requests=5000,
            max_total_raw_bytes=500_000_000,
            max_runtime_seconds=900,
        )
        targets = [probe_series] if probe_only else list(panel_series)
        for series in targets:
            obs, fail_reason = paginate_bounded_open_interest_v0(
                instrument_id=series.instrument_id,
                native_instrument_id=series.native_instrument_id,
                window=window,
                fetcher=ingest.okx_public_fetch_v1,
                rate_limiter=RateLimiter(),
                fetch_with_retry=ingest.fetch_with_retry,
                build_url=_build_url,
                parse_json=_parse_json,
                raw_dir=raw_dir / series.native_instrument_id,
                budget=budget,
            )
            observations_by_native[series.native_instrument_id] = obs
            source_inventory.append(
                {
                    "instrument_id": series.instrument_id,
                    "native_instrument_id": series.native_instrument_id,
                    "observation_count": len(obs),
                    "fail_reason": fail_reason,
                }
            )
            budget.instruments_completed += 1
            budget.current_instrument_pages = 0

    probe_obs = observations_by_native.get(probe_series.native_instrument_id, [])
    source_digest = _stable_digest(source_inventory or {"probe_observation_count": len(probe_obs)})
    horizon = assess_open_interest_horizon_v0(
        probe_obs,
        window=window,
        probe_instrument_id=probe_series.instrument_id,
    )

    oi_staging_root.mkdir(parents=True, exist_ok=True)
    result: BoundOpenInterestPanelMaterializationResultV0 = (
        materialize_open_interest_panel_from_observations_v0(
            staging_root=ohlcv_staging_root,
            observations_by_native=observations_by_native,
            horizon_assessment=horizon,
            source_data_digest=source_digest,
        )
    )

    return {
        "verdict": result.status.value,
        "dataset_id": result.dataset_id,
        "panel_data_digest": result.panel_data_digest,
        "bound_data_digest": result.bound_data_digest,
        "universe_digest": result.universe_digest,
        "source_data_digest": result.source_data_digest,
        "instrument_count": result.instrument_count,
        "row_count_total": result.row_count_total,
        "horizon_assessment": result.horizon_assessment,
        "reason_codes": list(result.reason_codes),
        "source_inventory": source_inventory,
        "dataset_contract": build_dataset_contract_v0(),
        "skip_fetch": skip_fetch,
        "probe_only": probe_only,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--confirm", required=True)
    parser.add_argument("--ohlcv-staging-root", type=Path, default=DEFAULT_OHLCV_STAGING_ROOT)
    parser.add_argument("--oi-staging-root", type=Path, default=DEFAULT_OI_STAGING_ROOT)
    parser.add_argument("--skip-fetch", action="store_true")
    parser.add_argument("--probe-only", action="store_true")
    args = parser.parse_args()
    result = run_bounded_open_interest_fetch_and_materialization_v0(
        confirm=args.confirm,
        ohlcv_staging_root=args.ohlcv_staging_root,
        oi_staging_root=args.oi_staging_root,
        skip_fetch=args.skip_fetch,
        probe_only=args.probe_only,
    )
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
