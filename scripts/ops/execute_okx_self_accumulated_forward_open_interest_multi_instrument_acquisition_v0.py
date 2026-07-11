#!/usr/bin/env python3
"""Execute bounded multi-instrument acquisition for self-accumulated forward OI archive v0.

Deterministic four-instrument expansion from canonical sufficiency universe binding,
bounded public OKX fetch via paginate_bounded_open_interest_v0, and append-only
observations.jsonl extension preserving ETH prefix and correction sidecars.
Operator GO: GO_CORE_SYSTEM_DEVELOPMENT_SELF_ACCUMULATED_OI_MULTI_INSTRUMENT_ACQUISITION_AND_ORCHESTRATION_V0
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
from src.research.okx_self_accumulated_forward_open_interest_multi_instrument_acquisition_and_orchestration_v0 import (  # noqa: E402
    CONFIRM_GO,
    AcquisitionTerminalStatus,
    build_orchestration_config_v0,
    execute_multi_instrument_acquisition_v0,
    result_to_report_dict_v0,
    select_additional_instruments_v0,
    validate_post_acquisition_v0,
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
        description="Bounded multi-instrument acquisition for self-accumulated OI archive v0."
    )
    parser.add_argument("--confirm-go-token", required=True)
    parser.add_argument("--target-archive", type=Path, default=DEFAULT_TARGET_ARCHIVE)
    parser.add_argument("--evidence-dir", type=Path, required=True)
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
    as_of_utc = collected_at_utc

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

    result = execute_multi_instrument_acquisition_v0(
        confirm=args.confirm_go_token,
        enabled=True,
        target_archive_path=target_archive,
        collected_at_utc=collected_at_utc,
        as_of_utc=as_of_utc,
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
    (evidence_dir / "acquisition_result.json").write_text(
        json.dumps(report, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    (evidence_dir / "orchestration_config.json").write_text(
        json.dumps(build_orchestration_config_v0(), sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )

    if args.validate_only:
        existing_ids = []
        from src.research.okx_self_accumulated_forward_open_interest_archive_v0 import (
            load_effective_archive_states_from_snapshot_v0,
        )

        states = load_effective_archive_states_from_snapshot_v0(target_archive)
        existing_ids = [state.instrument_id for state in states]
        selected = select_additional_instruments_v0(existing_ids)
        (evidence_dir / "selected_instruments.json").write_text(
            json.dumps(
                [
                    {
                        "instrument_id": item.instrument_id,
                        "native_instrument_id": item.native_instrument_id,
                    }
                    for item in selected
                ],
                sort_keys=True,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

    if result.status in {
        AcquisitionTerminalStatus.ACQUISITION_COMPLETE,
        AcquisitionTerminalStatus.VALIDATE_ONLY_PASS,
    }:
        validation = validate_post_acquisition_v0(
            target_archive_path=target_archive,
            prior_snapshot_dir=target_archive,
            as_of_utc=as_of_utc,
        )
        (evidence_dir / "effective_archive_validation.json").write_text(
            json.dumps(validation, sort_keys=True, indent=2) + "\n",
            encoding="utf-8",
        )

    print(json.dumps(report, sort_keys=True, indent=2))
    if result.status not in {
        AcquisitionTerminalStatus.ACQUISITION_COMPLETE,
        AcquisitionTerminalStatus.VALIDATE_ONLY_PASS,
    }:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
