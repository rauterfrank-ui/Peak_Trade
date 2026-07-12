#!/usr/bin/env python3
"""Execute historical panel depth extension for self-accumulated forward OI archive v0.

Bounded public OKX fetch for five-instrument panel, archive correction gap-insert,
and optional bound-panel rematerialization evidence. Operator GO required.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.ops.ingest_okx_futures_public_market_data_canonical_dataset_staging_v1 import (  # noqa: E402
    RateLimiter,
    fetch_with_retry,
    okx_public_fetch_v1,
)
from src.research.okx_self_accumulated_forward_open_interest_archive_v0 import (  # noqa: E402
    load_effective_archive_states_from_snapshot_v0,
)
from src.research.okx_self_accumulated_forward_open_interest_historical_panel_depth_extension_v0 import (  # noqa: E402
    CONFIRM_GO,
    HistoricalDepthExtensionTerminalStatus,
    build_extension_config_v0,
    compute_acquisition_window_v0,
    compute_common_panel_intersection_v0,
    execute_historical_panel_depth_extension_v0,
    result_to_report_dict_v0,
    validate_post_extension_v0,
)

DEFAULT_TARGET_ARCHIVE = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "datasets/okx_self_accumulated_forward_open_interest_archive_v0/production_snapshot"
)


def _die(msg: str, code: int = 2) -> None:
    print(msg, file=sys.stderr)
    raise SystemExit(code)


def _build_url(path: str, params: dict[str, str]) -> str:
    query = "&".join(f"{k}={v}" for k, v in sorted(params.items()))
    return f"https://www.okx.com{path}?{query}"


def _parse_json(body: bytes) -> dict:
    return json.loads(body.decode())


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Historical panel depth extension for self-accumulated OI archive v0."
    )
    parser.add_argument("--confirm-go-token", required=True)
    parser.add_argument("--target-archive", type=Path, default=DEFAULT_TARGET_ARCHIVE)
    parser.add_argument("--evidence-dir", type=Path, required=True)
    parser.add_argument("--collection-execution-id", required=True)
    parser.add_argument("--enabled", action="store_true")
    parser.add_argument("--execute-mutation", action="store_true")
    parser.add_argument("--validate-only", action="store_true")
    parser.add_argument(
        "--fixture-observations-dir",
        type=Path,
        default=None,
        help="Offline fixture directory keyed by native instrument id JSON files",
    )
    args = parser.parse_args(argv)

    if args.confirm_go_token != CONFIRM_GO:
        _die(f"OPERATOR_GO_MISMATCH expected={CONFIRM_GO}")

    if not args.enabled:
        _die("DEFAULT_OFF_ENABLED_FLAG_REQUIRED")

    if args.execute_mutation and args.validate_only:
        _die("EXECUTE_MUTATION_AND_VALIDATE_ONLY_MUTUALLY_EXCLUSIVE")

    target_archive = args.target_archive.resolve()
    if not target_archive.is_dir():
        _die(f"MISSING_TARGET_ARCHIVE:{target_archive}")

    evidence_dir = args.evidence_dir.resolve()
    evidence_dir.mkdir(parents=True, exist_ok=True)

    collected_at_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    evidence_ref = str(evidence_dir)

    states_before = load_effective_archive_states_from_snapshot_v0(target_archive)
    common_before = compute_common_panel_intersection_v0(states_before)
    if not common_before:
        _die("EMPTY_COMMON_PANEL_INTERSECTION")

    acquisition_window = compute_acquisition_window_v0(tail_end_venue_utc=common_before[-1])
    (evidence_dir / "acquisition_window.json").write_text(
        json.dumps(acquisition_window, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    (evidence_dir / "orchestration_config.json").write_text(
        json.dumps(build_extension_config_v0(), sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )

    fixture_observations_by_native = None
    if args.fixture_observations_dir is not None:
        from src.research.okx_historical_open_interest_public_fetch_v0 import (
            NormalizedOpenInterestObservationV0,
        )

        fixture_observations_by_native = {}
        for path in sorted(args.fixture_observations_dir.glob("*.json")):
            payload = json.loads(path.read_text(encoding="utf-8"))
            rows = payload.get("observations") or []
            fixture_observations_by_native[path.stem] = tuple(
                NormalizedOpenInterestObservationV0(**item) for item in rows
            )

    raw_dir = evidence_dir / "raw_fetch"
    raw_dir.mkdir(parents=True, exist_ok=True)

    result = execute_historical_panel_depth_extension_v0(
        confirm=args.confirm_go_token,
        enabled=True,
        target_archive_path=target_archive,
        collected_at_utc=collected_at_utc,
        collection_execution_id=args.collection_execution_id,
        evidence_ref=evidence_ref,
        fetcher=okx_public_fetch_v1 if args.fixture_observations_dir is None else None,
        rate_limiter=RateLimiter() if args.fixture_observations_dir is None else None,
        fetch_with_retry=fetch_with_retry if args.fixture_observations_dir is None else None,
        build_url=_build_url if args.fixture_observations_dir is None else None,
        parse_json=_parse_json if args.fixture_observations_dir is None else None,
        raw_dir=raw_dir,
        fixture_observations_by_native=fixture_observations_by_native,
        execute_mutation=args.execute_mutation and not args.validate_only,
        validate_only=args.validate_only,
    )

    report = result_to_report_dict_v0(result)
    (evidence_dir / "extension_result.json").write_text(
        json.dumps(report, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )

    if result.status in {
        HistoricalDepthExtensionTerminalStatus.EXTENSION_COMPLETE,
        HistoricalDepthExtensionTerminalStatus.VALIDATE_ONLY_PASS,
    }:
        validation = validate_post_extension_v0(target_archive_path=target_archive)
        (evidence_dir / "effective_archive_validation.json").write_text(
            json.dumps(validation, sort_keys=True, indent=2) + "\n",
            encoding="utf-8",
        )

    print(json.dumps(report, sort_keys=True, indent=2))
    if result.status not in {
        HistoricalDepthExtensionTerminalStatus.EXTENSION_COMPLETE,
        HistoricalDepthExtensionTerminalStatus.VALIDATE_ONLY_PASS,
    }:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
