"""
Risk Layer Integration Adapter
================================

Minimal integration layer for BacktestEngine and Risk Managers.

This is an OPT-IN adapter - existing code continues to work without changes.

Usage:
    >>> from src.core.peak_config import load_config
    >>> from src.risk_layer.integration import RiskLayerAdapter
    >>>
    >>> cfg = load_config()
    >>> adapter = RiskLayerAdapter(cfg)
    >>>
    >>> # Check if trading is allowed
    >>> if adapter.check_trading_allowed():
    ...     # Execute trade
    ...     pass
"""

from __future__ import annotations

import logging
from typing import Optional

logger = logging.getLogger(__name__)


class RiskLayerAdapter:
    """
    Adapter für Integration von Risk Layer Features.

    Provides minimal wiring between Risk Layer components and
    existing BacktestEngine/RiskManagers.

    Features:
    - Kill Switch integration
    - Optional VaR/Attribution integration
    - Opt-in design (no breaking changes)
    """

    def __init__(self, config):
        """
        Initialize adapter with config.

        Args:
            config: PeakConfig instance or dict
        """
        self.config = config
        self._kill_switch: Optional[object] = None

        # Lazy initialization based on config
        self._init_components()

    def _init_components(self):
        """Initialize Risk Layer components based on config."""
        # Kill Switch (optional)
        kill_switch_enabled = self._get_config("risk_layer_v1.kill_switch.enabled", False)

        if kill_switch_enabled:
            try:
                from src.risk_layer.kill_switch import KillSwitch

                kill_switch_config = self._get_config("risk_layer_v1.kill_switch", {})
                self._kill_switch = KillSwitch(kill_switch_config)
                logger.info("Kill Switch initialized via RiskLayerAdapter")
            except Exception as e:
                logger.warning(f"Failed to initialize Kill Switch: {e}")

    def _get_config(self, path: str, default=None):
        """
        Get config value with dot-notation support.

        Args:
            path: Config path (e.g. "risk_layer_v1.var.window")
            default: Default value if not found

        Returns:
            Config value or default
        """
        # Support both PeakConfig and plain dict
        if hasattr(self.config, "get"):
            return self.config.get(path, default)
        elif isinstance(self.config, dict):
            # Plain dict: navigate manually
            keys = path.split(".")
            node = self.config
            for key in keys:
                if isinstance(node, dict) and key in node:
                    node = node[key]
                else:
                    return default
            return node
        else:
            return default

    def check_trading_allowed(self) -> bool:
        """
        Prüft ob Trading erlaubt ist (Kill Switch Check).

        Returns:
            True wenn Trading erlaubt, False wenn blockiert
        """
        if self._kill_switch is None:
            return True  # Kein Kill Switch = Trading erlaubt

        return not self._kill_switch.check_and_block()

    @property
    def kill_switch(self):
        """Gibt Kill Switch Instanz zurück (oder None)."""
        return self._kill_switch


def create_risk_layer_adapter(config=None):
    """
    Factory function für RiskLayerAdapter.

    Args:
        config: Optional PeakConfig, lädt default wenn None

    Returns:
        RiskLayerAdapter instance
    """
    if config is None:
        from src.core.peak_config import load_config

        config = load_config()

    return RiskLayerAdapter(config)
