#!/usr/bin/env python3
"""U2b: persist governed snapshot loader run record (offline, confirm-token gated).

Writes durable loader persist bundle under archive root only.
Not readmodel write, dashboard wiring, truth-GO, or trading.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Optional, Sequence

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from src.webui.workflow_dashboard_readmodel_v1.futures_producer_packet_real_metadata_source_v1 import (
    LOADER_PERSIST_CONFIRM_TOKEN,
    FuturesProducerPacketRealMetadataSourceError,
    persist_governed_snapshot_loader_run_v1,
)


def _die(msg: str, code: int = 2) -> None:
    print(msg, file=sys.stderr)
    raise SystemExit(code)


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Persist U2b governed snapshot loader run record (no readmodel/dashboard/truth)."
    )
    parser.add_argument("--candidate-bundle", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--archive-root", type=Path, required=True)
    parser.add_argument("--persist-bundle-id", type=str, default=None)
    parser.add_argument(
        "--confirm-token",
        required=True,
        help=f"Must be exactly {LOADER_PERSIST_CONFIRM_TOKEN!r}.",
    )
    ns = parser.parse_args(argv)
    try:
        summary = persist_governed_snapshot_loader_run_v1(
            confirm_token=ns.confirm_token,
            candidate_bundle_path=ns.candidate_bundle,
            output_dir=ns.output_dir,
            archive_root=ns.archive_root,
            persist_bundle_id=ns.persist_bundle_id,
        )
    except FuturesProducerPacketRealMetadataSourceError as exc:
        _die(f"ERR: {exc}", 1)
    except SystemExit as exc:
        return int(exc.code) if isinstance(exc.code, int) else 2
    print(f"LOADER_PERSIST_EXECUTED=true")
    print(f"OUTPUT_DIR={summary['output_dir']}")
    print(f"MANIFEST_VERIFY_RC={summary['manifest_verify_rc']}")
    print(f"PACKET_COUNT={summary['completeness_summary']['packet_count']}")
    print(
        "CANDIDATE_VALIDATION_COMPLETE_COUNT="
        f"{summary['completeness_summary']['candidate_validation_complete_count']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
