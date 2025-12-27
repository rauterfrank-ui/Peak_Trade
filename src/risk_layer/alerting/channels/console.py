"""
Console Notification Channel
=============================

Prints alerts to stdout - always enabled, no configuration required.
"""

import logging
import sys

from ..models import AlertEvent

logger = logging.getLogger(__name__)


class ConsoleChannel:
    """
    Console notification channel (stdout).

    Features:
    - Formatted output with severity emoji
    - Always enabled (no external dependencies)
    - Safe default for development
    """

    def __init__(self, color: bool = True):
        """
        Initialize console channel.

        Args:
            color: Use colored output (ANSI codes)
        """
        self.color = color

    @property
    def enabled(self) -> bool:
        """Console channel is always enabled."""
        return True

    def send(self, alert: AlertEvent) -> bool:
        """Send alert to console (stdout)."""
        try:
            output = alert.format_console()

            if self.color:
                output = self._colorize(output, alert.severity.value)

            print(output, file=sys.stdout)
            print("─" * 80, file=sys.stdout)

            return True

        except Exception as e:
            logger.error(f"Console channel error: {e}", exc_info=True)
            return False

    def _colorize(self, text: str, severity: str) -> str:
        """Add ANSI color codes based on severity."""
        color_codes = {
            "info": "\033[36m",  # Cyan
            "warn": "\033[33m",  # Yellow
            "critical": "\033[91m",  # Bright red
        }
        reset = "\033[0m"

        color = color_codes.get(severity, "")
        return f"{color}{text}{reset}"
