"""
Console Alert Sink - Phase 16I

Prints alerts to stdout (default sink for dry-run).
"""

import logging
import sys

from ..models import AlertEvent

logger = logging.getLogger(__name__)


class ConsoleAlertSink:
    """
    Console alert sink (stdout).

    Features:
    - Formatted output with severity emoji
    - Always succeeds (no external dependencies)
    - Ideal for dry-run mode
    """

    def __init__(self, color: bool = True):
        """
        Initialize console sink.

        Args:
            color: Use colored output (ANSI codes)
        """
        self.color = color

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
            logger.error(f"Console sink error: {e}", exc_info=True)
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
