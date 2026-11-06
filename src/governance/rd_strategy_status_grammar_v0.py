"""R&D strategy status grammar v0 — docs/governance classification SSOT.

Canonical owner for DRIFT_B02_RD_STRATEGY_STATUS_GRAMMAR_V0.

This module normalizes and validates R&D *documentation* status tokens
(``stub`` | ``research-only`` | ``missing``). It does **not** change strategy
signal logic, promotion, live authorization, Master V2, Double Play, risk,
sizing, or dashboard behavior.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Mapping

CONTRACT_ID = "RD_STRATEGY_STATUS_GRAMMAR_V0"
CONTRACT_VERSION = "v0"
PACKAGE_MARKER = "RD_STRATEGY_STATUS_GRAMMAR_V0=true"

CANONICAL_STATUSES: frozenset[str] = frozenset({"stub", "research-only", "missing"})

DEFAULT_CONTRACT_RELPATH = "docs/features/rd_strategy_status_grammar_v0.json"

_REPO_ROOT = Path(__file__).resolve().parents[2]


class RdStrategyStatusGrammarError(ValueError):
    """Fail-closed error for invalid or ambiguous R&D status tokens."""


def default_contract_path(repo_root: Path | None = None) -> Path:
    root = _REPO_ROOT if repo_root is None else Path(repo_root)
    return root / DEFAULT_CONTRACT_RELPATH


def _fold_token(raw: str) -> str:
    """Fold separators so alias keys compare stably."""
    return " ".join(raw.strip().lower().replace("_", " ").replace("-", " ").split())


def load_rd_strategy_status_grammar_v0(
    contract_path: str | Path | None = None,
) -> dict[str, Any]:
    """Load the machine-readable grammar contract (single SSOT file)."""
    path = Path(contract_path) if contract_path else default_contract_path()
    if not path.is_file():
        raise RdStrategyStatusGrammarError(
            f"RD_STRATEGY_STATUS_CONTRACT_MISSING: {path} (fail-closed)."
        )
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RdStrategyStatusGrammarError(
            "RD_STRATEGY_STATUS_CONTRACT_TYPE: root must be object (fail-closed)."
        )
    if payload.get("contract_id") != CONTRACT_ID:
        raise RdStrategyStatusGrammarError(
            "RD_STRATEGY_STATUS_CONTRACT_ID_MISMATCH: "
            f"expected {CONTRACT_ID}, got {payload.get('contract_id')!r} (fail-closed)."
        )
    statuses = payload.get("canonical_statuses")
    if set(statuses or []) != set(CANONICAL_STATUSES):
        raise RdStrategyStatusGrammarError(
            "RD_STRATEGY_STATUS_CONTRACT_STATUSES_DRIFT: "
            f"contract statuses {statuses!r} != {sorted(CANONICAL_STATUSES)} (fail-closed)."
        )
    return payload


# Cache by resolved path string for determinism in repeated test imports.
@lru_cache(maxsize=8)
def _load_cached(contract_path_resolved: str) -> dict[str, Any]:
    return load_rd_strategy_status_grammar_v0(contract_path_resolved)


def get_rd_strategy_status_grammar_v0(
    contract_path: str | Path | None = None,
) -> dict[str, Any]:
    path = Path(contract_path) if contract_path else default_contract_path()
    return _load_cached(str(path.resolve()))


def normalize_rd_strategy_status_v0(
    raw: Any,
    *,
    contract: Mapping[str, Any] | None = None,
) -> str:
    """Normalize a status token to a canonical grammar value.

    Legacy aliases are applied only at this boundary. Ambiguous tokens
    (``TODO``, ``NotImplementedError``, …) fail closed. Empty/whitespace
    and non-str values fail closed.
    """
    if raw is None:
        raise RdStrategyStatusGrammarError(
            "RD_STRATEGY_STATUS_EMPTY: status token is None (fail-closed)."
        )
    if not isinstance(raw, str):
        raise RdStrategyStatusGrammarError(
            f"RD_STRATEGY_STATUS_TYPE: expected str, got {type(raw).__name__} (fail-closed)."
        )
    if not raw.strip():
        raise RdStrategyStatusGrammarError(
            "RD_STRATEGY_STATUS_EMPTY: status token is empty/whitespace (fail-closed)."
        )

    payload = contract if contract is not None else get_rd_strategy_status_grammar_v0()
    aliases: Mapping[str, Any] = payload.get("legacy_aliases") or {}
    rejected = {_fold_token(tok) for tok in (payload.get("ambiguous_rejected_tokens") or [])}

    folded = _fold_token(raw)
    if folded in rejected:
        raise RdStrategyStatusGrammarError(
            f"RD_STRATEGY_STATUS_AMBIGUOUS: {raw!r} is ambiguous and must not be "
            "used as an R&D status (fail-closed)."
        )

    # Direct canonical hit (preserve hyphenated research-only).
    direct = raw.strip().lower()
    if direct in CANONICAL_STATUSES:
        return direct

    # Alias table keys may be hyphenated or spaced; fold both sides.
    folded_aliases = {_fold_token(str(k)): str(v) for k, v in aliases.items()}
    if folded in folded_aliases:
        canonical = folded_aliases[folded]
        if canonical not in CANONICAL_STATUSES:
            raise RdStrategyStatusGrammarError(
                f"RD_STRATEGY_STATUS_ALIAS_TARGET_INVALID: alias {raw!r} maps to "
                f"{canonical!r} which is not canonical (fail-closed)."
            )
        return canonical

    raise RdStrategyStatusGrammarError(
        f"RD_STRATEGY_STATUS_UNKNOWN: {raw!r} is not a canonical status or "
        "known legacy alias (fail-closed)."
    )


def list_canonical_rd_strategy_statuses_v0() -> tuple[str, ...]:
    """Deterministic ordered canonical status set."""
    return tuple(sorted(CANONICAL_STATUSES))


def iter_rd_strategy_status_rows_v0(
    *,
    contract: Mapping[str, Any] | None = None,
) -> tuple[dict[str, Any], ...]:
    """Return strategy classification rows with normalized status."""
    payload = contract if contract is not None else get_rd_strategy_status_grammar_v0()
    rows = payload.get("strategies")
    if not isinstance(rows, list) or not rows:
        raise RdStrategyStatusGrammarError(
            "RD_STRATEGY_STATUS_ROWS_MISSING: strategies[] required (fail-closed)."
        )
    out: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict):
            raise RdStrategyStatusGrammarError(
                "RD_STRATEGY_STATUS_ROW_TYPE: each strategies[] entry must be object."
            )
        status = normalize_rd_strategy_status_v0(row.get("status"), contract=payload)
        item = dict(row)
        item["status"] = status
        out.append(item)
    return tuple(out)


def serialize_rd_strategy_status_inventory_v0(
    *,
    contract: Mapping[str, Any] | None = None,
) -> str:
    """Deterministic JSON serialization of normalized strategy inventory."""
    rows = [
        {
            "strategy_id": r["strategy_id"],
            "status": r["status"],
            "module_path": r["module_path"],
            "registry_key": r["registry_key"],
        }
        for r in iter_rd_strategy_status_rows_v0(contract=contract)
    ]
    rows_sorted = sorted(rows, key=lambda x: str(x["strategy_id"]))
    return json.dumps(rows_sorted, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def assert_fehlende_features_consumes_grammar_v0(
    fehlende_text: str,
    *,
    contract: Mapping[str, Any] | None = None,
) -> None:
    """Consumer parity: canonical FEHLENDE catalog must embed grammar markers."""
    payload = contract if contract is not None else get_rd_strategy_status_grammar_v0()
    if "rd_strategy_status_grammar_v0" not in fehlende_text:
        raise RdStrategyStatusGrammarError(
            "RD_STRATEGY_STATUS_CONSUMER_DRIFT: FEHLENDE_FEATURES must reference "
            "rd_strategy_status_grammar_v0 (fail-closed)."
        )
    for status in CANONICAL_STATUSES:
        # Table must mention each canonical token at least once.
        if status not in fehlende_text:
            raise RdStrategyStatusGrammarError(
                f"RD_STRATEGY_STATUS_CONSUMER_MISSING_TOKEN: {status!r} absent from "
                "FEHLENDE_FEATURES (fail-closed)."
            )
    for row in iter_rd_strategy_status_rows_v0(contract=payload):
        sid = str(row["strategy_id"])
        status = str(row["status"])
        # Require strategy display or id near its status in the catalog table.
        if sid not in fehlende_text and str(row.get("display_name", "")) not in fehlende_text:
            raise RdStrategyStatusGrammarError(
                f"RD_STRATEGY_STATUS_CONSUMER_ROW_MISSING: {sid} not present in "
                "FEHLENDE_FEATURES (fail-closed)."
            )
        # Reject residual blanket drift phrases for these strategies.
    banned = (
        "TODO/NotImplementedError (z. B. Ehlers",
        "gibt Nullen zurück",
        "gibt leeres DataFrame zurück",
    )
    for phrase in banned:
        if phrase in fehlende_text:
            raise RdStrategyStatusGrammarError(
                f"RD_STRATEGY_STATUS_CONSUMER_STALE_DRIFT: banned phrase {phrase!r} "
                "still present in FEHLENDE_FEATURES (fail-closed)."
            )


def clear_rd_strategy_status_grammar_cache_v0() -> None:
    """Test helper: clear lru cache."""
    _load_cached.cache_clear()
