"""Bitcoin-/Futures-only drift guard for Final Research Fleet Class D artifacts v0."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Iterable

REPO_ROOT = Path(__file__).resolve().parents[2]
CLASS_D_CONFIG_PATHS = (
    REPO_ROOT / "config/research/final_research_fleet_class_d_versioned_binding_completion_v0.json",
    REPO_ROOT
    / "config/research/final_research_fleet_class_d_offline_economic_evaluation_scope_ratification_v0.json",
    REPO_ROOT / "config/research/final_research_fleet_class_d_operator_ratification_v0.json",
)

EVALUATION_NATIVE_INSTRUMENT_ID = "ETH-USDT-SWAP"
EXPECTED_PANEL_MEMBER_COUNT = 118
EXPECTED_COMPLETION_DIGEST = "0610afa34b347abde08768fb2fbfb30fd4bb19ae010f3b2042c67155fb6c0fc4"
HISTORICAL_BLOCKED_COMPLETION_DIGEST = (
    "161d834e5153df78a0013b6e55c4c8bd4788c775811e3678f025104a307d78f1"
)

FORBIDDEN_POSITIVE_TOKENS = (
    "BTC-USDT-SWAP",
    "BTC-USDT",
    "XBTUSD",
    "PF_XBT",
    "XBT-USDT-SWAP",
)
FORBIDDEN_POSITIVE_PATTERNS = (
    re.compile(r"\bBTC\b"),
    re.compile(r"\bXBT\b"),
    re.compile(r"\bBitcoin\b"),
)
ALLOWED_NEGATIVE_SUBSTRINGS = (
    "bitcoin_direction_allowed",
    "non_bitcoin",
    "non-Bitcoin",
    "BITCOIN_DIRECTION_ALLOWED=false",
    "POSITIVE_BITCOIN_BINDINGS_ALLOWED=false",
    "BITCOIN_DRIFT_GUARD",
    "historical_blocked_completion_digest",
    HISTORICAL_BLOCKED_COMPLETION_DIGEST,
)


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _iter_strings(node: Any, *, path: str = "$") -> Iterable[tuple[str, str]]:
    if isinstance(node, str):
        yield path, node
        return
    if isinstance(node, dict):
        for key, value in node.items():
            yield from _iter_strings(value, path=f"{path}.{key}")
        return
    if isinstance(node, list):
        for index, value in enumerate(node):
            yield from _iter_strings(value, path=f"{path}[{index}]")


def _is_allowed_negative_reference(value: str) -> bool:
    lowered = value.lower()
    if "bitcoin_direction_allowed" in lowered and "false" in lowered:
        return True
    if "non_bitcoin" in lowered or "non-bitcoin" in lowered:
        return True
    if HISTORICAL_BLOCKED_COMPLETION_DIGEST in value:
        return True
    if any(term in value for term in ALLOWED_NEGATIVE_SUBSTRINGS):
        return True
    return False


def _is_blocking_positive_reference(value: str) -> bool:
    if _is_allowed_negative_reference(value):
        return False
    if any(token in value for token in FORBIDDEN_POSITIVE_TOKENS):
        return True
    for pattern in FORBIDDEN_POSITIVE_PATTERNS:
        if pattern.search(value):
            return True
    if re.search(r"bitcoin", value, flags=re.IGNORECASE) and "non" not in value.lower():
        return True
    return False


def test_class_d_config_artifacts_exist() -> None:
    for path in CLASS_D_CONFIG_PATHS:
        assert path.is_file(), f"missing class d artifact: {path}"


def test_materialized_completion_digest_matches_ratified_scope() -> None:
    completion = _load_json(CLASS_D_CONFIG_PATHS[0])
    assert completion["completion_digest"] == EXPECTED_COMPLETION_DIGEST
    assert completion["completion_digest"] != HISTORICAL_BLOCKED_COMPLETION_DIGEST


def test_futures_only_and_bitcoin_guard_flags_on_all_artifacts() -> None:
    for path in CLASS_D_CONFIG_PATHS:
        payload = _load_json(path)
        assert payload["bitcoin_direction_allowed"] is False
        if "futures_only" in payload:
            assert payload["futures_only"] is True
        if "spot_allowed" in payload:
            assert payload["spot_allowed"] is False


def test_evaluation_instrument_is_eth_usdt_swap_only() -> None:
    completion = _load_json(CLASS_D_CONFIG_PATHS[0])
    assert completion["futures_only"] is True
    assert completion["spot_allowed"] is False
    assert completion["synthetic_spot_allowed"] is False

    for candidate in completion["candidates"]:
        instrument = candidate["instrument_binding"]
        assert instrument["evaluation_native_instrument_id"] == EVALUATION_NATIVE_INSTRUMENT_ID
        assert instrument["bitcoin_direction_allowed"] is False
        assert instrument["futures_only"] is True
        assert instrument["spot_allowed"] is False
        assert instrument["eligible_instrument_count"] == EXPECTED_PANEL_MEMBER_COUNT
        assert EVALUATION_NATIVE_INSTRUMENT_ID in instrument["eligible_native_instrument_ids"]

        adapter = candidate["dataset_binding"]["evaluation_price_data_adapter"]
        assert adapter["native_instrument_id"] == EVALUATION_NATIVE_INSTRUMENT_ID

    shared = completion["shared_bindings"]["instrument_binding"]
    assert shared["evaluation_native_instrument_id"] == EVALUATION_NATIVE_INSTRUMENT_ID
    assert shared["eligible_instrument_count"] == EXPECTED_PANEL_MEMBER_COUNT


def test_no_positive_bitcoin_bindings_in_materialized_class_d_artifacts() -> None:
    blocking_hits: list[str] = []
    for path in CLASS_D_CONFIG_PATHS:
        payload = _load_json(path)
        for json_path, value in _iter_strings(payload):
            if _is_blocking_positive_reference(value):
                blocking_hits.append(f"{path.relative_to(REPO_ROOT)}:{json_path}={value!r}")
    assert blocking_hits == [], "blocking positive bitcoin references:\n" + "\n".join(blocking_hits)


def test_positive_bitcoin_binding_fixture_fails_guard() -> None:
    bad = {
        "instrument_binding": {
            "evaluation_native_instrument_id": "BTC-USDT-SWAP",
            "bitcoin_direction_allowed": True,
        }
    }
    hits = [value for _, value in _iter_strings(bad) if _is_blocking_positive_reference(value)]
    assert hits, "fixture must represent a blocking positive bitcoin binding"
