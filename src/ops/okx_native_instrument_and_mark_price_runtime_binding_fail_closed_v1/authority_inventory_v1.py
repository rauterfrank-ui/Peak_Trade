"""Repository-wide authority inventory for instrument/mark-price binding."""

from __future__ import annotations

import ast
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from src.ops.okx_native_instrument_and_mark_price_runtime_binding_fail_closed_v1.constants_v1 import (
    CAPABILITY_ID,
    MARK_PRICE_ENDPOINT,
    VENUE_MAPPING_AUTHORITY,
)

WALLCLOCK_TRANSPORT = (
    "src/ops/integrated_paper_shadow_observation_wallclock_session_execution_v1/"
    "eea_public_md_transport_v1.py"
)
WALLCLOCK_RUNTIME = (
    "src/ops/integrated_paper_shadow_observation_wallclock_session_execution_v1/"
    "session_runtime_v1.py"
)
VENUE_BINDING = "src/ops/bounded_futures_testnet_venue_binding_v0.py"
MAPPING_MODULE = (
    "src/ops/okx_native_instrument_and_mark_price_runtime_binding_fail_closed_v1/"
    "venue_instrument_mapping_v1.py"
)
HARDENING_PRICE = (
    "src/ops/wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_"
    "hardening_v2/market_data_price_basis_v2.py"
)
HARDENING_CONSTANTS = (
    "src/ops/wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_"
    "hardening_v2/constants_v2.py"
)


@dataclass
class AuthorityInventoryResultV1:
    ok: bool
    blockers: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    capability: str = CAPABILITY_ID
    canonical_instrument_authority_count: int = 0
    venue_mapping_authority_count: int = 0
    second_instrument_mapping_authority_present: bool = True
    direct_canonical_id_to_okx_transport_path_present: bool = True
    ticker_markpx_assumption_present: bool = True
    deterministic_schema_failure_reconnectable: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _read(repo_root: Path, rel: str) -> str:
    return (repo_root / rel).read_text(encoding="utf-8")


def _fetch_ticker_uses_canonical_default(src: str) -> bool:
    tree = ast.parse(src)
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == "EeaPublicMdTransportV1":
            for item in node.body:
                if isinstance(item, ast.FunctionDef) and item.name == "fetch_ticker":
                    for arg in item.args.args:
                        if arg.arg == "instrument_id":
                            return True
                    for default in item.args.defaults:
                        if isinstance(default, ast.Name) and default.id == (
                            "CANONICAL_INSTRUMENT_ID"
                        ):
                            return True
                    # keyword-only defaults
                    for default in item.args.kw_defaults:
                        if default is None:
                            continue
                        if isinstance(default, ast.Name) and default.id == (
                            "CANONICAL_INSTRUMENT_ID"
                        ):
                            return True
    return False


def verify_okx_native_instrument_mark_price_authority_inventory_v1(
    *,
    repo_root: Path,
) -> AuthorityInventoryResultV1:
    blockers: list[str] = []
    notes: list[str] = []

    mapping_src = _read(repo_root, MAPPING_MODULE)
    venue_src = _read(repo_root, VENUE_BINDING)
    transport_src = _read(repo_root, WALLCLOCK_TRANSPORT)
    runtime_src = _read(repo_root, WALLCLOCK_RUNTIME)
    hardening_const = _read(repo_root, HARDENING_CONSTANTS)

    # Single venue mapping authority: mapping module must call venue binding.
    uses_venue_binding = "default_okx_europe_xperp_production_binding" in mapping_src
    if not uses_venue_binding:
        blockers.append("VENUE_MAPPING_AUTHORITY_NOT_BOUND")
    # No second registry inventing ETH-USDT-SWAP in this capability package.
    pkg = repo_root / "src/ops/okx_native_instrument_and_mark_price_runtime_binding_fail_closed_v1"
    second = False
    for path in pkg.glob("*.py"):
        text = path.read_text(encoding="utf-8")
        if "ETH-USDT-SWAP" in text and path.name != "authority_inventory_v1.py":
            second = True
            blockers.append(f"SECOND_MAPPING_HARDCODE:{path.name}")
    if "PRODUCTION_INSTRUMENT_ID" not in venue_src:
        blockers.append("VENUE_BINDING_MISSING_PRODUCTION_INSTRUMENT")

    direct = _fetch_ticker_uses_canonical_default(transport_src)
    if direct:
        blockers.append("DIRECT_CANONICAL_ID_TO_OKX_TRANSPORT_PATH_PRESENT")
    if "venue_instrument_id" not in transport_src:
        blockers.append("TRANSPORT_MISSING_VENUE_INSTRUMENT_ID")
    if "fetch_mark_price" not in transport_src:
        blockers.append("TRANSPORT_MISSING_FETCH_MARK_PRICE")
    if MARK_PRICE_ENDPOINT not in transport_src and "mark-price" not in transport_src:
        blockers.append("TRANSPORT_MARK_PRICE_PATH_MISSING")

    ticker_markpx = (
        'REQUIRED_TICKER_PRICE_FIELD = "markPx"' in hardening_const
        or "REQUIRED_TICKER_PRICE_FIELD = 'markPx'" in hardening_const
    )
    if ticker_markpx:
        blockers.append("TICKER_MARKPX_ASSUMPTION_PRESENT")

    # Runtime must classify deterministic schema failures as non-reconnectable.
    if "classify_transport_message_v1" not in runtime_src:
        blockers.append("RUNTIME_MISSING_ERROR_CLASSIFICATION")
    if "MarketDataBindingErrorV1" not in runtime_src:
        blockers.append("RUNTIME_MISSING_BINDING_ERROR_HANDLING")
    reconnectable_bug = (
        "REQUIRED_PRICE_FIELD_MISSING" in runtime_src
        and "reconnect_attempts +=" in runtime_src
        and "classify_transport_message_v1" not in runtime_src
    )
    if reconnectable_bug:
        blockers.append("DETERMINISTIC_SCHEMA_FAILURE_RECONNECTABLE")

    notes.extend(
        [
            f"VENUE_MAPPING_AUTHORITY={VENUE_MAPPING_AUTHORITY}",
            "CANONICAL_INSTRUMENT_AUTHORITY=venue_binding_production_instrument",
            "MARK_PRICE_FROM_PUBLIC_MARK_PRICE_ENDPOINT",
        ]
    )

    return AuthorityInventoryResultV1(
        ok=not blockers,
        blockers=sorted(set(blockers)),
        notes=notes,
        canonical_instrument_authority_count=1 if uses_venue_binding else 0,
        venue_mapping_authority_count=1 if uses_venue_binding and not second else 0,
        second_instrument_mapping_authority_present=second,
        direct_canonical_id_to_okx_transport_path_present=direct,
        ticker_markpx_assumption_present=ticker_markpx,
        deterministic_schema_failure_reconnectable=reconnectable_bug,
    )
