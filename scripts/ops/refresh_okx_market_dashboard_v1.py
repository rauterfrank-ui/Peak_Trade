#!/usr/bin/env python3
"""Bounded operator refresh: OKX public metadata → intake → universe → OHLCV.

Read-only market-data path. No private API, orders, scheduler, or runtime activation.
"""

from __future__ import annotations

import argparse
import fcntl
import json
import sys
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence

_REPO_ROOT = Path(__file__).resolve().parents[2]
for _p in (_REPO_ROOT, _REPO_ROOT / "src"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from scripts.ops.okx_to_futures_producer_packet_governed_v1 import (
    CONFIRM_TOKEN as PRODUCER_CONFIRM,
)
from scripts.ops.okx_to_futures_producer_packet_governed_v1 import (
    build_okx_governed_bundle_v1,
)
from src.ops.okx_selected_instrument_ohlcv_readmodel_v1 import (
    materialize_selected_okx_ohlcv_readmodel_v1,
)
from src.webui.workflow_dashboard_archive_root_v1 import resolve_workflow_dashboard_archive_root
from src.webui.workflow_dashboard_readmodel_v1.futures_producer_packet_real_metadata_source_v1 import (
    FuturesProducerPacketRealMetadataSourceError,
    bundle_to_upstream_input,
    load_futures_producer_packet_governed,
)
from src.webui.workflow_dashboard_readmodel_v1.futures_universe_upstream_adapter_v1 import (
    map_futures_packets_to_universe_selection_readmodel,
)
from src.webui.workflow_dashboard_readmodel_v1.universe_selection_producer_v1 import (
    write_universe_selection_readmodel,
)

LOCK_NAME = ".okx_market_dashboard_refresh.lock"


def _die(msg: str, code: int = 2) -> None:
    print(msg, file=sys.stderr)
    raise SystemExit(code)


def refresh_okx_market_dashboard_v1(
    *,
    archive_root: Path | None,
    venue: str,
    market_type: str,
    settle_ccy: str,
    exclude_underlying: str,
    bar: str,
    verify_manifest: bool,
    materialize_readmodels: bool,
    dry_run: bool,
    environ: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    from src.ops.canonical_runtime_environment_contract_v1.builder_v1 import (
        CanonicalEnvironmentContractError,
    )
    from src.ops.canonical_runtime_environment_contract_v1.preflight_v1 import (
        assert_http_client_proxy_env_clean_v1,
    )

    try:
        assert_http_client_proxy_env_clean_v1(environ=environ)
    except CanonicalEnvironmentContractError as exc:
        _die(f"ERR: O1_PROXY_POLICY_FAILURE:{','.join(exc.blockers)}")

    if archive_root is not None:
        resolved_root = archive_root.expanduser().resolve()
    else:
        resolved = resolve_workflow_dashboard_archive_root(require_existing_directory=False)
        if resolved is None:
            _die("ERR: archive root unresolved")
        resolved_root = resolved.resolve()
    resolved_root.mkdir(parents=True, exist_ok=True)

    lock_path = resolved_root / LOCK_NAME
    lock_fh = lock_path.open("w", encoding="utf-8")
    try:
        fcntl.flock(lock_fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError as exc:
        lock_fh.close()
        raise SystemExit("ERR: refresh already in progress") from exc

    result: dict[str, Any] = {
        "command": "refresh-okx-market-dashboard",
        "archive_root": str(resolved_root),
        "venue": venue,
        "market_type": market_type,
        "settle_ccy": settle_ccy,
        "exclude_underlying": exclude_underlying,
        "bar": bar,
        "dry_run": dry_run,
        "authenticated_fetch": False,
        "orders": False,
        "runtime_activation": False,
        "status": "STARTED",
    }
    try:
        if dry_run:
            result["status"] = "DRY_RUN_OK"
            result["note"] = "dry-run only; no network fetch performed"
            print(json.dumps(result, indent=2))
            return result

        producer = build_okx_governed_bundle_v1(
            archive_root=resolved_root,
            venue=venue,
            market_type=market_type,
            settle_ccy=settle_ccy,
            exclude_underlying=exclude_underlying,
            confirm=PRODUCER_CONFIRM,
        )
        result["producer"] = {
            k: producer[k]
            for k in (
                "bundle_id",
                "bundle_dir",
                "governed_packet_path",
                "metadata_table_path",
                "manifest_verify_rc",
                "eligible_count",
                "selected_symbol",
                "selected_venue",
            )
            if k in producer
        }
        bundle_path = Path(producer["governed_packet_path"])
        if verify_manifest and int(producer.get("manifest_verify_rc", 1)) != 0:
            _die("ERR: MANIFEST_VERIFY_RC != 0")

        if not materialize_readmodels:
            result["status"] = "PRODUCER_ONLY_OK"
            print(json.dumps(result, indent=2))
            return result

        try:
            bundle = load_futures_producer_packet_governed(
                bundle_path,
                archive_root=resolved_root,
            )
            upstream_input = bundle_to_upstream_input(bundle)
        except FuturesProducerPacketRealMetadataSourceError as exc:
            _die(f"ERR: intake rejected: {exc}")

        adapted = map_futures_packets_to_universe_selection_readmodel(upstream_input)
        if adapted.status not in {"ok", "partial"}:
            _die(
                f"ERR: universe adapter status={adapted.status} reasons={adapted.rejection_reasons}"
            )

        write_result = write_universe_selection_readmodel(
            resolved_root,
            adapted.payload,
            dry_run=False,
        )
        if write_result.manifest_verify_rc != 0:
            _die("ERR: universe readmodel manifest verify failed")

        selected = adapted.payload.get("selected_future") or {}
        selected_symbol = str(selected.get("symbol") or "")
        if not selected_symbol:
            _die("ERR: selected instrument empty")
        selected_venue = "okx"
        for row in adapted.payload.get("universe") or []:
            if (
                isinstance(row, dict)
                and row.get("symbol") == selected_symbol
                and row.get("exchange")
            ):
                selected_venue = str(row["exchange"])
                break

        ohlcv = materialize_selected_okx_ohlcv_readmodel_v1(
            archive_root=resolved_root,
            selected_instrument=selected_symbol,
            selected_provider_instrument_id=selected_symbol,
            selected_venue=selected_venue,
            selection_bundle_id=str(producer["bundle_id"]),
            selection_path=Path(write_result.readmodel_path),
            bar=bar,
        )
        result.update(
            {
                "status": "OK",
                "intake_accepted": True,
                "universe_selection_path": write_result.readmodel_path,
                "selected_instrument": selected_symbol,
                "selected_venue": selected_venue,
                "ohlcv": ohlcv,
                "manifest_verify_rc": producer.get("manifest_verify_rc"),
            }
        )
        print(json.dumps(result, indent=2))
        return result
    finally:
        try:
            fcntl.flock(lock_fh.fileno(), fcntl.LOCK_UN)
        except Exception:  # noqa: BLE001
            pass
        lock_fh.close()


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Refresh OKX market-dashboard readmodels (public market data only)."
    )
    parser.add_argument("--archive-root", type=Path, default=None)
    parser.add_argument("--venue", default="okx")
    parser.add_argument("--market-type", default="swap")
    parser.add_argument("--settle-ccy", default="USDT")
    parser.add_argument("--exclude-underlying", default="BTC")
    parser.add_argument("--bar", default="PT1M")
    parser.add_argument("--verify-manifest", action="store_true", default=True)
    parser.add_argument("--no-verify-manifest", action="store_false", dest="verify_manifest")
    parser.add_argument("--materialize-readmodels", action="store_true", default=True)
    parser.add_argument(
        "--no-materialize-readmodels", action="store_false", dest="materialize_readmodels"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="No network fetch; print planned refresh envelope only.",
    )
    parser.add_argument(
        "command",
        nargs="?",
        default="refresh-okx-market-dashboard",
        choices=["refresh-okx-market-dashboard"],
    )
    ns = parser.parse_args(argv)
    try:
        refresh_okx_market_dashboard_v1(
            archive_root=ns.archive_root,
            venue=ns.venue,
            market_type=ns.market_type,
            settle_ccy=ns.settle_ccy,
            exclude_underlying=ns.exclude_underlying,
            bar=ns.bar,
            verify_manifest=ns.verify_manifest,
            materialize_readmodels=ns.materialize_readmodels,
            dry_run=ns.dry_run,
        )
    except SystemExit as exc:
        return int(exc.code) if isinstance(exc.code, int) else 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
