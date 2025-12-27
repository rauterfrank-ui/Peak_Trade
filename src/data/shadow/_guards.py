"""
Shadow Pipeline Guards — Defense in Depth.

Verhindert versehentlichen Live-Mode über mehrere Ebenen:
1. Import Guard: prüft bei Module-Load
2. Runtime Guard: prüft zur Laufzeit gegen Config
3. Config Guard: prüft ob Pipeline enabled
"""

from __future__ import annotations

import os
from typing import Any


class ShadowPipelineDisabled(Exception):
    """Raised wenn Shadow Pipeline nicht enabled ist."""

    pass


class ShadowLiveForbidden(Exception):
    """Raised wenn Live-Mode aktiviert ist (VERBOTEN in Shadow)."""

    pass


def check_import_guard() -> None:
    """
    Import Guard: prüft ENV beim Modul-Load.

    Raises:
        ShadowLiveForbidden: Wenn PEAK_TRADE_LIVE_MODE gesetzt ist
    """
    live_mode_env = os.environ.get("PEAK_TRADE_LIVE_MODE", "").lower()
    if live_mode_env in ("1", "true", "yes"):
        raise ShadowLiveForbidden(
            "SHADOW PIPELINE ERROR: PEAK_TRADE_LIVE_MODE ist aktiv! "
            "Shadow-Modus darf NIEMALS im Live-Mode laufen."
        )


def check_runtime_guard(cfg: dict[str, Any]) -> None:
    """
    Runtime Guard: prüft Config zur Laufzeit.

    Args:
        cfg: Config-Dict (nested, z.B. {"live": {"enabled": false}})

    Raises:
        ShadowLiveForbidden: Wenn live.enabled=true
    """
    # Check ENV nochmal (double-check)
    check_import_guard()

    # Check Config: live.enabled
    live_enabled = cfg.get("live", {}).get("enabled", False)
    if live_enabled:
        raise ShadowLiveForbidden(
            "SHADOW PIPELINE ERROR: live.enabled=true in Config! "
            "Shadow-Modus darf NIEMALS im Live-Mode laufen."
        )


def check_config_guard(cfg: dict[str, Any]) -> None:
    """
    Config Guard: prüft ob Pipeline enabled ist.

    Args:
        cfg: Config-Dict

    Raises:
        ShadowPipelineDisabled: Wenn shadow.pipeline.enabled != true
    """
    pipeline_enabled = cfg.get("shadow", {}).get("pipeline", {}).get("enabled", False)
    if not pipeline_enabled:
        raise ShadowPipelineDisabled(
            "Shadow Pipeline ist disabled. Setze shadow.pipeline.enabled=true in Config."
        )
