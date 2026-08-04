#!/usr/bin/env python3
"""Headed Playwright keepalive with a guaranteed close contract.

CAPABILITY_ID=WEBUI_PLAYWRIGHT_CHROME_CHANNEL_LIFECYCLE_CLOSE_V1

Uses managed_chrome_channel only (owns Playwright + opt-in SIGINT/SIGTERM close).
Does not touch review_server.sh::chrome_open / open -a "Google Chrome".
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_SCRIPTS_WEBUI = Path(__file__).resolve().parent
if str(_SCRIPTS_WEBUI) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_WEBUI))

from review_server_playwright_webserver_v1 import (  # noqa: E402
    PRIMARY_BROWSER,
    PRIMARY_PLAYWRIGHT_CHANNEL,
    managed_chrome_channel,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Open a headed Playwright chrome-channel session and keep it alive "
            "until SIGINT/SIGTERM, then close browser and Playwright."
        )
    )
    parser.add_argument(
        "url",
        help="Local review URL to open (e.g. http://127.0.0.1:8000/)",
    )
    parser.add_argument(
        "--goto-timeout-ms",
        type=int,
        default=60_000,
        help="page.goto timeout in milliseconds (default: 60000)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    with managed_chrome_channel(
        headless=False,
        install_termination_handlers=True,
    ) as handle:
        page = handle.browser.new_page()
        page.goto(args.url, wait_until="domcontentloaded", timeout=args.goto_timeout_ms)
        print(
            "HEADED_KEEPALIVE_READY="
            f"url={args.url} "
            f"browser={handle.report.get('BROWSER_ACTUAL')} "
            f"channel={PRIMARY_PLAYWRIGHT_CHANNEL} "
            f"primary={PRIMARY_BROWSER} "
            f"owns_playwright={handle.owns_playwright}",
            flush=True,
        )
        print("WAITING_FOR_SIGINT_OR_SIGTERM", flush=True)
        handle.wait_until_closed()
        print("HEADED_KEEPALIVE_CLOSED", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
