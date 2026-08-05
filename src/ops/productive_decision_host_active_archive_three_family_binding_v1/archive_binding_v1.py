"""Explicit archive binding and selection resolution (no latest-discovery)."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Mapping

from src.ops.productive_decision_host_active_archive_three_family_binding_v1.authorization_v1 import (
    ProductiveHostAuthorizationError,
)
from src.ops.productive_decision_host_active_archive_three_family_binding_v1.constants_v1 import (
    ARCHIVE_ROOT_ENV,
    CANONICAL_DECISION_SIBLING_RELATIVE,
    DOUBLE_PLAY_SIBLING_RELATIVE,
    DYNAMIC_SCOPE_SIBLING_RELATIVE,
)
from src.ops.productive_decision_host_active_archive_three_family_binding_v1.models_v1 import (
    ArchiveBindingV1,
)
from src.webui.workflow_dashboard_archive_root_v1 import (
    PRECEDENCE_DEFAULT,
    PRECEDENCE_DISCOVERED_GOVERNED_OKX,
    PRECEDENCE_ENV,
    PRECEDENCE_EXPLICIT,
    resolve_workflow_dashboard_archive_root,
)
from src.webui.workflow_dashboard_readmodel_v1.universe_selection_contract_v1 import (
    STORAGE_RELATIVE_PATH,
    UniverseSelectionContractError,
    load_universe_selection_contract,
)


def bind_active_archive_v1(
    *,
    archive_root: str | Path | None,
    environ: Mapping[str, str] | None = None,
    allow_resolver_fallback: bool = True,
) -> ArchiveBindingV1:
    """Bind the concrete archive root. Prefer explicit; optional canonical resolver.

    Discovery of 'latest' is forbidden. When ``archive_root`` is None and
    ``allow_resolver_fallback`` is True, the existing canonical resolver may
    resolve env → default → discovered governed OKX sibling and the resolved
    path is logged via the returned binding.
    """
    env = os.environ if environ is None else environ
    precedence = PRECEDENCE_EXPLICIT
    if archive_root is not None and str(archive_root).strip():
        root = Path(archive_root).expanduser().resolve()
        precedence = PRECEDENCE_EXPLICIT
    elif allow_resolver_fallback:
        # Use canonical resolver; record which precedence applied.
        explicit_env = env.get(ARCHIVE_ROOT_ENV)
        if explicit_env and str(explicit_env).strip():
            precedence = PRECEDENCE_ENV
        resolved = resolve_workflow_dashboard_archive_root(environ=env)
        if resolved is None:
            raise ProductiveHostAuthorizationError(
                "ARCHIVE_ROOT_UNRESOLVED",
                "canonical resolver returned None",
            )
        root = Path(resolved).expanduser().resolve()
        # Best-effort classify default vs discovered when env unset.
        if not (explicit_env and str(explicit_env).strip()):
            leaf = root.name
            if leaf.startswith("workflow_dashboard_v1_okx_"):
                precedence = PRECEDENCE_DISCOVERED_GOVERNED_OKX
            else:
                precedence = PRECEDENCE_DEFAULT
    else:
        raise ProductiveHostAuthorizationError(
            "ARCHIVE_ROOT_REQUIRED",
            "explicit archive_root required when allow_resolver_fallback=false",
        )

    if not root.is_dir():
        raise ProductiveHostAuthorizationError("ARCHIVE_ROOT_MISSING", str(root))
    readmodels = root / "readmodels"
    readmodels.mkdir(parents=True, exist_ok=True)
    writable = os.access(readmodels, os.W_OK)
    if not writable:
        raise ProductiveHostAuthorizationError("ARCHIVE_ROOT_NOT_WRITABLE", str(readmodels))

    return ArchiveBindingV1(
        archive_root=str(root),
        resolution_precedence=precedence,
        readmodels_dir=str(readmodels),
        dynamic_scope_sibling_path=str(root / DYNAMIC_SCOPE_SIBLING_RELATIVE),
        canonical_decision_sibling_path=str(root / CANONICAL_DECISION_SIBLING_RELATIVE),
        double_play_sibling_path=str(root / DOUBLE_PLAY_SIBLING_RELATIVE),
        writable=True,
    )


def resolve_selected_instrument_from_archive_v1(
    *,
    archive_root: str | Path,
    expected_symbol: str | None = None,
) -> tuple[str, str]:
    """Resolve selected instrument from archive universe selection authority.

    Returns (symbol, source_label). Never invents a productive hard-coded symbol.
    """
    root = Path(archive_root).expanduser().resolve()
    payload_path = root / STORAGE_RELATIVE_PATH
    try:
        contract = load_universe_selection_contract(payload_path)
    except UniverseSelectionContractError as exc:
        raise ProductiveHostAuthorizationError(
            "SELECTED_INSTRUMENT_LOAD_FAILED",
            str(exc),
        ) from exc
    if contract.selected_future is None or not str(contract.selected_future.symbol).strip():
        raise ProductiveHostAuthorizationError(
            "SELECTED_INSTRUMENT_MISSING",
            "universe_selection_readmodel.v1 has no selected_future.symbol",
        )
    symbol = str(contract.selected_future.symbol).strip()
    source = f"archive:{STORAGE_RELATIVE_PATH}:selected_future.symbol"
    if expected_symbol is not None and str(expected_symbol).strip():
        if symbol != str(expected_symbol).strip():
            raise ProductiveHostAuthorizationError(
                "SELECTED_INSTRUMENT_MISMATCH",
                f"archive={symbol}:expected={expected_symbol}",
            )
    return symbol, source
