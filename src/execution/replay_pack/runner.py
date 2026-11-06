from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Tuple

from src.execution.beta_bridge.schema import normalize_beta_exec_v1_event, sort_key_beta_exec_v1
from src.execution.ledger.engine_legacy import LegacyLedgerEngine as LedgerEngine
from src.execution.ledger.quantization import parse_symbol

from .contract import ContractViolationError, HashMismatchError, ReplayMismatchError
from .loader import load_replay_pack
from .validator import validate_replay_pack
from .datarefs import (
    DataRefHashMismatchError,
    MissingRequiredDataRefError,
    ResolutionMode,
    enforce_resolution_mode,
    resolve_market_data_refs,
    parse_market_data_refs_document,
)


@dataclass(frozen=True)
class ReplayResult:
    fills: List[Dict[str, Any]]
    positions: Dict[str, Dict[str, str]]


def _compute_expected_positions_from_engine(eng: LedgerEngine) -> Dict[str, Dict[str, str]]:
    out: Dict[str, Dict[str, str]] = {}
    for sym in sorted(eng.state.positions.keys()):
        pos = eng.state.positions[sym]
        out[sym] = {
            "quantity": str(pos.quantity),
            "avg_cost": str(pos.avg_cost),
            "fees": str(pos.fees),
            "realized_pnl": str(pos.realized_pnl),
        }
    return out


def _replay_events(events: Iterable[Mapping[str, Any]]) -> ReplayResult:
    normalized = [normalize_beta_exec_v1_event(e) for e in events]
    normalized = sorted(normalized, key=sort_key_beta_exec_v1)

    first_symbol = str(normalized[0].get("symbol") or "")
    _, quote = parse_symbol(first_symbol)
    eng = LedgerEngine(quote_currency=quote)

    fills: List[Dict[str, Any]] = []
    for e in normalized:
        eng.apply(e)
        if str(e.get("event_type")) == "FILL":
            fills.append(dict(e))

    return ReplayResult(fills=fills, positions=_compute_expected_positions_from_engine(eng))


def replay_bundle(
    bundle_path: str | Path,
    *,
    check_outputs: bool = False,
    resolve_datarefs: Optional[ResolutionMode] = None,
    cache_root: Optional[str | Path] = None,
    datarefs_generated_at_utc: Optional[str] = None,
) -> int:
    """
    Deterministically replay a bundle.

    Exit codes:
      0: pass
      2: contract/schema violation
      3: hash mismatch
      4: replay mismatch (expected outputs)
      5: unexpected exception
      6: missing required dataref (strict)
    """
    try:
        validate_replay_pack(bundle_path)
    except HashMismatchError:
        return 3
    except ContractViolationError:
        return 2
    except Exception:
        return 5

    bundle = load_replay_pack(bundle_path)

    # Optional market data refs resolution (offline, deterministic).
    if resolve_datarefs is not None:
        cache_root_s = (
            str(cache_root)
            if cache_root is not None
            else str(os.environ.get("PEAK_TRADE_DATA_CACHE_ROOT") or "")
        )
        if not cache_root_s:
            return 2
        try:
            doc = bundle.market_data_refs()
            if doc is not None:
                refs = parse_market_data_refs_document(doc)  # validates
                generated_at = (
                    str(datarefs_generated_at_utc)
                    if datarefs_generated_at_utc is not None
                    else str(bundle.manifest.get("created_at_utc") or "")
                )
                report = resolve_market_data_refs(
                    bundle.root,
                    refs,
                    cache_root_s,
                    mode=resolve_datarefs,
                    bundle_id=str(bundle.manifest.get("bundle_id") or ""),
                    run_id=str(bundle.manifest.get("run_id") or ""),
                    generated_at_utc=generated_at,
                    run_id_for_report=str(bundle.manifest.get("run_id") or ""),
                )
                enforce_resolution_mode(mode=resolve_datarefs, refs=refs, report=report)
        except MissingRequiredDataRefError:
            return 6
        except DataRefHashMismatchError:
            return 3
        except ContractViolationError:
            return 2
        except Exception:
            return 5

    events = list(bundle.execution_events())
    if not events:
        return 2

    result = _replay_events(events)

    if not check_outputs:
        return 0

    expected_fills_iter = bundle.expected_fills()
    expected_positions = bundle.expected_positions()

    # If no expected outputs exist, treat as a successful replay.
    if expected_fills_iter is None and expected_positions is None:
        return 0

    if expected_fills_iter is not None:
        expected_fills = [normalize_beta_exec_v1_event(e) for e in expected_fills_iter]
        expected_fills = sorted(expected_fills, key=sort_key_beta_exec_v1)
        got_fills = [normalize_beta_exec_v1_event(e) for e in result.fills]
        got_fills = sorted(got_fills, key=sort_key_beta_exec_v1)
        if expected_fills != got_fills:
            raise ReplayMismatchError("fills mismatch vs outputs/expected_fills.jsonl")

    if expected_positions is not None:
        # Expected positions are persisted as JSON-safe strings.
        if expected_positions != result.positions:
            raise ReplayMismatchError("positions mismatch vs outputs/expected_positions.json")

    return 0


def replay_bundle_exit_code(bundle_path: str | Path, *, check_outputs: bool = False) -> int:
    """
    Wrapper that maps ReplayMismatchError to exit code 4.
    """
    try:
        return replay_bundle(bundle_path, check_outputs=check_outputs)
    except ReplayMismatchError:
        return 4
