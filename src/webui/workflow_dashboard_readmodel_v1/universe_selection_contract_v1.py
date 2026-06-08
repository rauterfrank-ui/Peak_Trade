"""Schema contract and validation for universe_selection_readmodel.v1 (Slice 1 — no runtime I/O)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

SCHEMA_NAME = "universe_selection_readmodel.v1"
SCHEMA_VERSION = 1
STORAGE_RELATIVE_PATH = "readmodels/universe_selection_readmodel.v1.json"

ALLOWED_SOURCE_STAGES = frozenset({"paper", "shadow", "testnet"})
FORBIDDEN_SOURCE_STAGES = frozenset({"live"})

MISSING_TRUTH_UNIVERSE = "UNIVERSE_SOURCE_NOT_PERSISTED"
MISSING_TRUTH_RANKING = "TOP20_RANKING_NOT_PERSISTED"
MISSING_TRUTH_SELECTED = "SELECTED_FUTURE_NOT_PERSISTED"
MISSING_TRUTH_FUTURE_DETAIL = "FUTURE_DETAIL_NOT_AVAILABLE"
MISSING_TRUTH_PNL = "NOT_PERSISTED"

ALLOWED_MISSING_TRUTH_STATUSES = frozenset(
    {
        "PERSISTED",
        "NOT_PERSISTED",
        "UNKNOWN",
        MISSING_TRUTH_UNIVERSE,
        MISSING_TRUTH_RANKING,
        MISSING_TRUTH_SELECTED,
        MISSING_TRUTH_FUTURE_DETAIL,
        MISSING_TRUTH_PNL,
        "AVAILABLE",
        "NOT_AVAILABLE",
    }
)

FORBIDDEN_ROW_FIELDS = frozenset(
    {
        "order_id",
        "side",
        "quantity",
        "leverage",
        "approval",
        "approved",
        "live_authorized",
        "strategy_activation",
    }
)

FORBIDDEN_SELECTED_SYMBOLS = frozenset(
    {
        "BTC/USD",
        "BTCUSD",
        "BTC-USD",
    }
)

FORBIDDEN_TRUTH_SOURCE_KINDS = frozenset(
    {
        "market_surface_dummy",
        "get_market_dummy",
        "btc_usd_dummy_default",
    }
)

MAX_UNIVERSE_ROWS = 60
MAX_RANKING_ROWS = 20


class UniverseSelectionContractError(ValueError):
    """Raised when a universe selection contract payload is invalid."""


@dataclass(frozen=True)
class UniverseSelectionRowV1:
    row_id: str
    symbol: str
    rank: int
    exchange: str | None = None
    display_score: float | None = None
    notes: str | None = None


@dataclass(frozen=True)
class SelectedFutureV1:
    row_id: str
    symbol: str
    rank: int
    truth_status: str
    selection_reason: str | None = None
    notes: str | None = None


@dataclass(frozen=True)
class MissingTruthBlockV1:
    universe: str
    ranking: str
    selected_future: str
    future_detail: str
    orders_fills_pnl: str


@dataclass(frozen=True)
class UniverseSelectionContractV1:
    schema_name: str
    schema_version: int
    generated_at: str
    source_run_id: str
    source_stage: str
    universe: tuple[UniverseSelectionRowV1, ...]
    ranking: tuple[UniverseSelectionRowV1, ...]
    selected_future: SelectedFutureV1 | None
    market_snapshot: dict[str, Any]
    evidence: dict[str, Any]
    missing_truth: MissingTruthBlockV1
    non_authorizing: bool
    fixture_marked: bool


def _as_mapping(value: Any, *, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise UniverseSelectionContractError(f"{field} must be an object")
    return value


def _as_string(value: Any, *, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise UniverseSelectionContractError(f"{field} must be a non-empty string")
    return value.strip()


def _as_int(value: Any, *, field: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise UniverseSelectionContractError(f"{field} must be an integer")
    return value


def _as_bool(value: Any, *, field: str) -> bool:
    if not isinstance(value, bool):
        raise UniverseSelectionContractError(f"{field} must be a boolean")
    return value


def _normalize_row(row: Any, *, field: str) -> UniverseSelectionRowV1:
    row_map = _as_mapping(row, field=field)
    forbidden = sorted(FORBIDDEN_ROW_FIELDS.intersection(row_map))
    if forbidden:
        raise UniverseSelectionContractError(
            f"{field} contains forbidden fields: {', '.join(forbidden)}"
        )
    symbol = _as_string(row_map.get("symbol"), field=f"{field}.symbol")
    normalized = UniverseSelectionRowV1(
        row_id=_as_string(row_map.get("row_id"), field=f"{field}.row_id"),
        symbol=symbol,
        rank=_as_int(row_map.get("rank"), field=f"{field}.rank"),
        exchange=row_map.get("exchange") if row_map.get("exchange") is None else _as_string(
            row_map.get("exchange"), field=f"{field}.exchange"
        ),
        display_score=(
            float(row_map["display_score"])
            if "display_score" in row_map and row_map["display_score"] is not None
            else None
        ),
        notes=row_map.get("notes") if row_map.get("notes") is None else _as_string(
            row_map.get("notes"), field=f"{field}.notes"
        ),
    )
    return normalized


def _normalize_rows(value: Any, *, field: str, max_rows: int) -> tuple[UniverseSelectionRowV1, ...]:
    if not isinstance(value, list):
        raise UniverseSelectionContractError(f"{field} must be a list")
    if len(value) > max_rows:
        raise UniverseSelectionContractError(f"{field} exceeds max rows ({max_rows})")
    return tuple(_normalize_row(row, field=f"{field}[{index}]") for index, row in enumerate(value))


def _normalize_missing_truth(value: Any) -> MissingTruthBlockV1:
    block = _as_mapping(value, field="missing_truth")
    fields = {
        "universe": _as_string(block.get("universe"), field="missing_truth.universe"),
        "ranking": _as_string(block.get("ranking"), field="missing_truth.ranking"),
        "selected_future": _as_string(
            block.get("selected_future"), field="missing_truth.selected_future"
        ),
        "future_detail": _as_string(block.get("future_detail"), field="missing_truth.future_detail"),
        "orders_fills_pnl": _as_string(
            block.get("orders_fills_pnl"), field="missing_truth.orders_fills_pnl"
        ),
    }
    for name, status in fields.items():
        if status not in ALLOWED_MISSING_TRUTH_STATUSES:
            raise UniverseSelectionContractError(
                f"missing_truth.{name} has unsupported status: {status}"
            )
    return MissingTruthBlockV1(**fields)


def _normalize_selected_future(value: Any) -> SelectedFutureV1 | None:
    if value is None:
        return None
    block = _as_mapping(value, field="selected_future")
    truth_status = _as_string(block.get("truth_status"), field="selected_future.truth_status")
    if truth_status == "NOT_PERSISTED":
        return None
    symbol = _as_string(block.get("symbol"), field="selected_future.symbol")
    _reject_btc_dummy_selected_truth(
        symbol=symbol,
        source_kind=block.get("source_kind"),
        field="selected_future",
    )
    forbidden = sorted(FORBIDDEN_ROW_FIELDS.intersection(block))
    if forbidden:
        raise UniverseSelectionContractError(
            f"selected_future contains forbidden fields: {', '.join(forbidden)}"
        )
    return SelectedFutureV1(
        row_id=_as_string(block.get("row_id"), field="selected_future.row_id"),
        symbol=symbol,
        rank=_as_int(block.get("rank"), field="selected_future.rank"),
        truth_status=truth_status,
        selection_reason=(
            None
            if block.get("selection_reason") is None
            else _as_string(block.get("selection_reason"), field="selected_future.selection_reason")
        ),
        notes=(
            None
            if block.get("notes") is None
            else _as_string(block.get("notes"), field="selected_future.notes")
        ),
    )


def _reject_btc_dummy_selected_truth(
    *,
    symbol: str,
    source_kind: Any,
    field: str,
) -> None:
    normalized = symbol.upper().replace("-", "").replace("/", "")
    if symbol in FORBIDDEN_SELECTED_SYMBOLS or normalized == "BTCUSD":
        raise UniverseSelectionContractError(
            f"{field}.symbol forbidden as paper/future/runtime truth: {symbol}"
        )
    if isinstance(source_kind, str) and source_kind in FORBIDDEN_TRUTH_SOURCE_KINDS:
        raise UniverseSelectionContractError(
            f"{field}.source_kind forbidden: {source_kind}"
        )


def _validate_missing_truth_consistency(
    contract: UniverseSelectionContractV1,
) -> None:
    mt = contract.missing_truth
    if contract.universe and mt.universe in (MISSING_TRUTH_UNIVERSE, "NOT_PERSISTED"):
        raise UniverseSelectionContractError(
            "universe rows present but missing_truth.universe is NOT_PERSISTED"
        )
    if not contract.universe and mt.universe == "PERSISTED":
        raise UniverseSelectionContractError(
            "missing_truth.universe is PERSISTED but universe is empty"
        )
    if contract.ranking and mt.ranking in (MISSING_TRUTH_RANKING, "NOT_PERSISTED"):
        raise UniverseSelectionContractError(
            "ranking rows present but missing_truth.ranking is NOT_PERSISTED"
        )
    if not contract.ranking and mt.ranking == "PERSISTED":
        raise UniverseSelectionContractError(
            "missing_truth.ranking is PERSISTED but ranking is empty"
        )
    if contract.selected_future and mt.selected_future in (MISSING_TRUTH_SELECTED, "NOT_PERSISTED"):
        raise UniverseSelectionContractError(
            "selected_future present but missing_truth.selected_future is NOT_PERSISTED"
        )
    if contract.selected_future is None and mt.selected_future == "PERSISTED":
        raise UniverseSelectionContractError(
            "missing_truth.selected_future is PERSISTED but selected_future is absent"
        )


def validate_universe_selection_payload(payload: dict[str, Any]) -> UniverseSelectionContractV1:
    """Validate a universe_selection_readmodel.v1 JSON object (no filesystem access)."""
    schema_name = _as_string(payload.get("schema_name"), field="schema_name")
    if schema_name != SCHEMA_NAME:
        raise UniverseSelectionContractError(f"schema_name must be {SCHEMA_NAME}")

    schema_version = payload.get("schema_version")
    if schema_version != SCHEMA_VERSION:
        raise UniverseSelectionContractError(f"schema_version must be {SCHEMA_VERSION}")

    source_stage = _as_string(payload.get("source_stage"), field="source_stage").lower()
    if source_stage in FORBIDDEN_SOURCE_STAGES:
        raise UniverseSelectionContractError(f"source_stage forbidden: {source_stage}")
    if source_stage not in ALLOWED_SOURCE_STAGES:
        raise UniverseSelectionContractError(f"source_stage unsupported: {source_stage}")

    non_authorizing = _as_bool(payload.get("non_authorizing"), field="non_authorizing")
    if not non_authorizing:
        raise UniverseSelectionContractError("non_authorizing must be true")

    universe = _normalize_rows(payload.get("universe"), field="universe", max_rows=MAX_UNIVERSE_ROWS)
    ranking = _normalize_rows(payload.get("ranking"), field="ranking", max_rows=MAX_RANKING_ROWS)
    selected_future = _normalize_selected_future(payload.get("selected_future"))
    market_snapshot = _as_mapping(payload.get("market_snapshot"), field="market_snapshot")
    evidence = _as_mapping(payload.get("evidence"), field="evidence")
    missing_truth = _normalize_missing_truth(payload.get("missing_truth"))

    contract = UniverseSelectionContractV1(
        schema_name=schema_name,
        schema_version=schema_version,
        generated_at=_as_string(payload.get("generated_at"), field="generated_at"),
        source_run_id=_as_string(payload.get("source_run_id"), field="source_run_id"),
        source_stage=source_stage,
        universe=universe,
        ranking=ranking,
        selected_future=selected_future,
        market_snapshot=market_snapshot,
        evidence=evidence,
        missing_truth=missing_truth,
        non_authorizing=non_authorizing,
        fixture_marked=bool(payload.get("fixture_marked", False)),
    )
    _validate_missing_truth_consistency(contract)
    return contract


def load_universe_selection_contract(path: str | Path) -> UniverseSelectionContractV1:
    """Load and validate universe_selection_readmodel.v1.json from a fixture or archive path."""
    payload_path = Path(path)
    if payload_path.is_dir():
        payload_path = payload_path / "universe_selection_readmodel.v1.json"
    try:
        raw = payload_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise UniverseSelectionContractError(f"cannot read contract file: {payload_path}") from exc
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise UniverseSelectionContractError("contract json_decode_error") from exc
    if not isinstance(payload, dict):
        raise UniverseSelectionContractError("contract root must be an object")
    return validate_universe_selection_payload(payload)


def contract_to_json_dict(contract: UniverseSelectionContractV1) -> dict[str, Any]:
    """Serialize a validated contract back to JSON-compatible dict."""
    selected: dict[str, Any] | None
    if contract.selected_future is None:
        selected = {"truth_status": "NOT_PERSISTED"}
    else:
        sf = contract.selected_future
        selected = {
            "row_id": sf.row_id,
            "symbol": sf.symbol,
            "rank": sf.rank,
            "truth_status": sf.truth_status,
            "selection_reason": sf.selection_reason,
            "notes": sf.notes,
        }

    def _rows(rows: tuple[UniverseSelectionRowV1, ...]) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        for row in rows:
            item: dict[str, Any] = {
                "row_id": row.row_id,
                "symbol": row.symbol,
                "rank": row.rank,
            }
            if row.exchange is not None:
                item["exchange"] = row.exchange
            if row.display_score is not None:
                item["display_score"] = row.display_score
            if row.notes is not None:
                item["notes"] = row.notes
            out.append(item)
        return out

    mt = contract.missing_truth
    return {
        "schema_name": contract.schema_name,
        "schema_version": contract.schema_version,
        "generated_at": contract.generated_at,
        "source_run_id": contract.source_run_id,
        "source_stage": contract.source_stage,
        "non_authorizing": contract.non_authorizing,
        "fixture_marked": contract.fixture_marked,
        "universe": _rows(contract.universe),
        "ranking": _rows(contract.ranking),
        "selected_future": selected,
        "market_snapshot": contract.market_snapshot,
        "evidence": contract.evidence,
        "missing_truth": {
            "universe": mt.universe,
            "ranking": mt.ranking,
            "selected_future": mt.selected_future,
            "future_detail": mt.future_detail,
            "orders_fills_pnl": mt.orders_fills_pnl,
        },
    }
