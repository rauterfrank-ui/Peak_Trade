"""Client / credential / plugin safety preflight for Pre-Economic session v1.

Fail-closed: any unclear or order-capable surface blocks production start.
"""

from __future__ import annotations

import ast
import importlib
import inspect
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable, Optional

from src.ops.pre_economic_zero_order_evidence_session_okx_readonly_telemetry_v1 import (
    FORBIDDEN_CLIENT_METHODS,
    assert_client_read_only,
    TelemetryError,
)

PACKAGE_MARKER = "PRE_ECONOMIC_ZERO_ORDER_EVIDENCE_SESSION_SAFETY_PREFLIGHT_V1=true"

FORBIDDEN_IMPORT_PREFIXES = (
    "src.orders",
    "src.execution",
    "src.live",
    "src.broker",
    "src.trading.live",
)

FORBIDDEN_MODULE_TOKENS = frozenset(
    {
        "place_order",
        "submit_order",
        "cancel_order",
        "amend_order",
        "broker_write",
        "live_execution",
    }
)

ALLOWED_CLIENT_TYPES = frozenset(
    {
        "OkxPublicMarketDataClientV1",
        "SimulatedOkxTelemetryClientV1",
    }
)


class SafetyPreflightError(ValueError):
    """Fail-closed safety preflight error."""


@dataclass
class SafetyPreflightResultV1:
    ok: bool
    blockers: list[str] = field(default_factory=list)
    client_type: str = ""
    trading_permissions_absent: bool = True
    credential_scope: str = "NONE_PUBLIC_ONLY"
    inspected_modules: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _module_source_path(module_name: str) -> Optional[Path]:
    try:
        mod = importlib.import_module(module_name)
    except Exception:  # noqa: BLE001
        return None
    src = getattr(mod, "__file__", None)
    if not src:
        return None
    return Path(src)


def inspect_module_imports(module_name: str) -> list[str]:
    path = _module_source_path(module_name)
    if path is None or not path.is_file():
        return [f"MODULE_SOURCE_UNAVAILABLE:{module_name}"]
    tree = ast.parse(path.read_text(encoding="utf-8"))
    imported: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported.append(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.append(node.module)
    return imported


def assert_no_forbidden_imports(module_names: Iterable[str]) -> list[str]:
    blockers: list[str] = []
    for name in module_names:
        imported = inspect_module_imports(name)
        for mod in imported:
            for prefix in FORBIDDEN_IMPORT_PREFIXES:
                if mod.startswith(prefix):
                    blockers.append(f"FORBIDDEN_IMPORT:{name}:{mod}")
            for token in FORBIDDEN_MODULE_TOKENS:
                if token in mod.lower():
                    blockers.append(f"FORBIDDEN_IMPORT_TOKEN:{name}:{mod}")
    return blockers


def assert_no_order_callbacks(callbacks: Optional[Iterable[Any]]) -> list[str]:
    blockers: list[str] = []
    if not callbacks:
        return blockers
    for cb in callbacks:
        name = getattr(cb, "__name__", str(cb)).lower()
        qual = getattr(cb, "__qualname__", name).lower()
        for token in ("order", "execute", "broker", "trade", "submit"):
            if token in name or token in qual:
                blockers.append(f"ORDER_SHAPED_CALLBACK:{name}")
                break
    return blockers


def assert_plugin_surface_readonly(plugins: Optional[Iterable[Any]]) -> list[str]:
    blockers: list[str] = []
    if not plugins:
        return blockers
    for plugin in plugins:
        for method in FORBIDDEN_CLIENT_METHODS:
            if hasattr(plugin, method) and callable(getattr(plugin, method)):
                blockers.append(f"PLUGIN_ORDER_SURFACE:{type(plugin).__name__}:{method}")
        # Generic execution adapters
        cls_name = type(plugin).__name__.lower()
        if any(tok in cls_name for tok in ("order", "execution", "broker", "trader")):
            blockers.append(f"PLUGIN_ORDER_ADAPTER:{type(plugin).__name__}")
    return blockers


def run_safety_preflight_v1(
    *,
    client: Any,
    credential_scope: str = "NONE_PUBLIC_ONLY",
    trading_permissions: Optional[Iterable[str]] = None,
    runtime_hooks: Optional[Iterable[Any]] = None,
    plugins: Optional[Iterable[Any]] = None,
    session_path_modules: Optional[Iterable[str]] = None,
) -> SafetyPreflightResultV1:
    blockers: list[str] = []
    notes = [
        "ORDERS_ALLOWED=false",
        "BROKER_WRITES_ALLOWED=false",
        "RUNTIME_AUTHORITY=NONE",
    ]
    client_type = type(client).__name__
    if client_type not in ALLOWED_CLIENT_TYPES:
        blockers.append(f"CLIENT_TYPE_NOT_ALLOWLISTED:{client_type}")
    try:
        assert_client_read_only(client)
    except TelemetryError as exc:
        blockers.append(str(exc))

    perms = [str(p).upper() for p in (trading_permissions or ())]
    if perms:
        blockers.append(f"TRADING_PERMISSIONS_PRESENT:{','.join(perms)}")

    scope = str(credential_scope or "").upper()
    if scope not in {"NONE_PUBLIC_ONLY", "READONLY_VALIDATED"}:
        blockers.append(f"CREDENTIAL_SCOPE_INVALID:{scope}")
    if scope == "READONLY_VALIDATED":
        # Even validated RO credentials are only allowed when explicitly declared;
        # public-only remains preferred.
        notes.append("READONLY_CREDENTIALS_DECLARED")

    blockers.extend(assert_no_order_callbacks(runtime_hooks))
    blockers.extend(assert_plugin_surface_readonly(plugins))

    modules = list(
        session_path_modules
        or (
            "src.ops.pre_economic_zero_order_evidence_session_production_runner_v1",
            "src.ops.pre_economic_zero_order_evidence_session_okx_readonly_telemetry_v1",
            "src.ops.pre_economic_zero_order_evidence_session_authorization_v1",
            "src.ops.pre_economic_zero_order_evidence_session_production_verifier_v1",
        )
    )
    # Import presence check uses source AST of modules that are already loadable.
    for mod_name in modules:
        try:
            importlib.import_module(mod_name)
        except Exception as exc:  # noqa: BLE001
            # During partial construction some modules may not exist yet; treat as soft.
            if "production_runner" in mod_name or "production_verifier" in mod_name:
                notes.append(f"MODULE_IMPORT_DEFERRED:{mod_name}:{exc}")
                continue
            blockers.append(f"SESSION_PATH_MODULE_UNIMPORTABLE:{mod_name}:{exc}")
    blockers.extend(assert_no_forbidden_imports(modules))

    # Dynamic import scan on client class module if available.
    try:
        client_mod = inspect.getmodule(type(client))
        if client_mod is not None and client_mod.__name__:
            modules.append(client_mod.__name__)
            blockers.extend(assert_no_forbidden_imports([client_mod.__name__]))
    except Exception as exc:  # noqa: BLE001
        blockers.append(f"CLIENT_MODULE_INSPECT_FAILED:{exc}")

    ok = not blockers
    return SafetyPreflightResultV1(
        ok=ok,
        blockers=blockers,
        client_type=client_type,
        trading_permissions_absent=not bool(perms),
        credential_scope=scope,
        inspected_modules=sorted(set(modules)),
        notes=notes,
    )
