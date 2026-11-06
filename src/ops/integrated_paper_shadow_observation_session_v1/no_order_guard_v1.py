"""No-order / no-broker-write technical enforcement for IPSO v1."""

from __future__ import annotations

import ast
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Mapping, Optional, Sequence

from src.ops.integrated_paper_shadow_observation_session_v1.constants_v1 import (
    FORBIDDEN_IMPORT_PREFIXES,
    ORDERS_ALLOWED,
    BROKER_WRITES_ALLOWED,
)

NO_ORDER_GUARD_ID = "ops.integrated_paper_shadow_observation_no_order_guard_v1"

_FORBIDDEN_CALL_NAMES = frozenset(
    {
        "place_order",
        "submit_order",
        "cancel_order",
        "amend_order",
        "broker_write",
        "create_order",
        "send_order",
    }
)


class NoOrderGuardError(ValueError):
    """Fail-closed no-order guard error."""


@dataclass
class NoOrderAttestationV1:
    ok: bool
    orders_allowed: bool = False
    broker_writes_allowed: bool = False
    orders_attempted: int = 0
    orders_submitted: int = 0
    broker_writes_performed: int = 0
    blockers: list[str] = field(default_factory=list)
    scanned_modules: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "orders_allowed": self.orders_allowed,
            "broker_writes_allowed": self.broker_writes_allowed,
            "orders_attempted": self.orders_attempted,
            "orders_submitted": self.orders_submitted,
            "broker_writes_performed": self.broker_writes_performed,
            "blockers": list(self.blockers),
            "scanned_modules": list(self.scanned_modules),
            "guard_id": NO_ORDER_GUARD_ID,
        }


def assert_observation_request_no_order_v1(
    *,
    mode: str,
    orders_enabled: bool = False,
    broker_writes_enabled: bool = False,
    live_enabled: bool = False,
    testnet_enabled: bool = False,
    network_enabled: bool = False,
    credentials_enabled: bool = False,
) -> tuple[str, ...]:
    blockers: list[str] = []
    if str(mode).strip().lower() != "observation":
        blockers.append("MODE_MUST_BE_OBSERVATION")
    if orders_enabled or ORDERS_ALLOWED:
        blockers.append("ORDERS_FORBIDDEN")
    if broker_writes_enabled or BROKER_WRITES_ALLOWED:
        blockers.append("BROKER_WRITES_FORBIDDEN")
    if live_enabled:
        blockers.append("LIVE_FORBIDDEN")
    if testnet_enabled:
        blockers.append("TESTNET_FORBIDDEN")
    if network_enabled:
        blockers.append("NETWORK_FORBIDDEN")
    if credentials_enabled:
        blockers.append("CREDENTIALS_FORBIDDEN")
    return tuple(blockers)


def scan_module_source_for_forbidden_surfaces_v1(
    source: str,
    *,
    module_name: str = "<module>",
) -> list[str]:
    blockers: list[str] = []
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        return [f"SOURCE_PARSE_FAILED:{module_name}:{exc}"]
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                name = alias.name
                for prefix in FORBIDDEN_IMPORT_PREFIXES:
                    if name == prefix or name.startswith(prefix + "."):
                        blockers.append(f"FORBIDDEN_IMPORT:{module_name}:{name}")
        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            for prefix in FORBIDDEN_IMPORT_PREFIXES:
                if mod == prefix or mod.startswith(prefix + "."):
                    blockers.append(f"FORBIDDEN_IMPORT_FROM:{module_name}:{mod}")
        elif isinstance(node, ast.Call):
            func = node.func
            name = None
            if isinstance(func, ast.Name):
                name = func.id
            elif isinstance(func, ast.Attribute):
                name = func.attr
            if name in _FORBIDDEN_CALL_NAMES:
                blockers.append(f"FORBIDDEN_CALL:{module_name}:{name}")
    return blockers


def attest_capability_sources_no_order_v1(
    *,
    repo_root: Path,
    relative_paths: Sequence[str],
    orders_attempted: int = 0,
    orders_submitted: int = 0,
    broker_writes_performed: int = 0,
) -> NoOrderAttestationV1:
    blockers: list[str] = []
    scanned: list[str] = []
    root = repo_root.resolve()
    for rel in relative_paths:
        path = (root / rel).resolve()
        try:
            path.relative_to(root)
        except ValueError:
            blockers.append(f"PATH_OUTSIDE_REPO:{rel}")
            continue
        if not path.is_file():
            blockers.append(f"SOURCE_MISSING:{rel}")
            continue
        scanned.append(rel)
        blockers.extend(
            scan_module_source_for_forbidden_surfaces_v1(
                path.read_text(encoding="utf-8"),
                module_name=rel,
            )
        )
    if orders_attempted or orders_submitted or broker_writes_performed:
        blockers.append("ORDER_OR_BROKER_WRITE_COUNTER_NONZERO")
    ok = not blockers
    return NoOrderAttestationV1(
        ok=ok,
        orders_allowed=False,
        broker_writes_allowed=False,
        orders_attempted=orders_attempted,
        orders_submitted=orders_submitted,
        broker_writes_performed=broker_writes_performed,
        blockers=blockers,
        scanned_modules=scanned,
    )


def reject_broker_write_attempt_v1(action: str) -> None:
    raise NoOrderGuardError(f"BROKER_WRITE_REJECTED:{action}")


def reject_order_attempt_v1(action: str) -> None:
    raise NoOrderGuardError(f"ORDER_REJECTED:{action}")
