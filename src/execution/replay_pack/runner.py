from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Tuple

from src.execution.beta_bridge.schema import normalize_beta_exec_v1_event, sort_key_beta_exec_v1
from src.execution.ledger.engine import LedgerEngine
from src.execution.ledger.quantization import parse_symbol

from .contract import ContractViolationError
from .loader import load_replay_pack
from .validator import validate_replay_pack


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


def replay_bundle(bundle_path: str | Path, *, check_outputs: bool = False) -> int:
    """
    Deterministically replay a bundle.

    Exit codes:
      0: pass
      2: contract/validation failure
      3: replay mismatch (expected outputs)
    """
    try:
        validate_replay_pack(bundle_path)
    except ContractViolationError:
        return 2
    except Exception:
        return 2

    bundle = load_replay_pack(bundle_path)
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
            return 3

    if expected_positions is not None:
        # Expected positions are persisted as JSON-safe strings.
        if expected_positions != result.positions:
            return 3

    return 0
