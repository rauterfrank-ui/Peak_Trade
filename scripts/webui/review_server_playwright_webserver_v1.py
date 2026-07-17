#!/usr/bin/env python3
"""Playwright webServer lifecycle for Peak Trade WebUI review harness.

Integrates with the repo-owned shell harness:
  ./scripts/webui/review_server.sh

Invariants:
  PLAYWRIGHT_WEBSERVER_REQUIRED=true
  PRIMARY_BROWSER=GOOGLE_CHROME
  PRIMARY_PLAYWRIGHT_CHANNEL=chrome
  REUSE_EXISTING_SERVER_ALLOWED=true
  CI_REUSE_EXISTING_SERVER=false
  LOCAL_REUSE_EXISTING_SERVER=true
  START_TIMEOUT_BOUNDED=true
  UVICORN_RELOAD=false
  LOCALHOST_ONLY=true

No second Playwright toolchain: reuses Python Playwright (channel=chrome)
from scripts/webui/_dashboard_chrome_playwright_harness_v1.py.
"""

from __future__ import annotations

import os
import socket
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.error import URLError
from urllib.request import urlopen

REPO_ROOT = Path(__file__).resolve().parents[2]
REVIEW_SERVER_SCRIPT = REPO_ROOT / "scripts" / "webui" / "review_server.sh"
PRIMARY_PLAYWRIGHT_CHANNEL = "chrome"
PRIMARY_BROWSER = "GOOGLE_CHROME"


def _env_truthy(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in {"1", "true", "yes", "on"}


def is_ci_environment() -> bool:
    return _env_truthy("CI") or _env_truthy("GITHUB_ACTIONS") or _env_truthy("PEAK_TRADE_CI")


def default_reuse_existing() -> bool:
    """CI never reuses a random local server; local may reuse healthy harness server."""
    if is_ci_environment():
        return False
    if "PEAK_TRADE_WEBUI_REUSE_EXISTING" in os.environ:
        return _env_truthy("PEAK_TRADE_WEBUI_REUSE_EXISTING")
    return True


def find_free_localhost_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def http_ok(url: str, *, timeout: float = 2.0) -> bool:
    try:
        with urlopen(url, timeout=timeout) as resp:  # noqa: S310 — localhost review only
            return int(getattr(resp, "status", 200)) == 200
    except (URLError, TimeoutError, OSError):
        return False


@dataclass
class WebServerHandle:
    base_url: str
    host: str
    port: int
    state_dir: Path
    managed: bool
    reused_existing: bool
    health_url: str
    review_url: str
    primary_browser: str = PRIMARY_BROWSER
    primary_playwright_channel: str = PRIMARY_PLAYWRIGHT_CHANNEL


class ReviewServerWebServer:
    """Start/stop Peak Trade review server for automated browser tests."""

    def __init__(
        self,
        *,
        host: str = "127.0.0.1",
        port: int | None = None,
        state_dir: Path | None = None,
        reuse_existing: bool | None = None,
        start_timeout_seconds: int | None = None,
        health_path: str = "/api/health",
        review_path: str = "/",
        repo_root: Path | None = None,
    ) -> None:
        if host not in {"127.0.0.1", "localhost", "::1"}:
            raise ValueError(f"LOCALHOST_ONLY violation: host={host!r}")
        self.repo_root = Path(repo_root or REPO_ROOT)
        self.host = host
        self.port = int(
            port if port is not None else os.environ.get("PEAK_TRADE_WEBUI_PORT", "8000")
        )
        self.state_dir = Path(
            state_dir
            if state_dir is not None
            else os.environ.get(
                "PEAK_TRADE_WEBUI_STATE_DIR",
                str(self.repo_root / ".run" / "webui_review_server"),
            )
        )
        self.reuse_existing = (
            default_reuse_existing() if reuse_existing is None else bool(reuse_existing)
        )
        self.start_timeout_seconds = int(
            start_timeout_seconds
            if start_timeout_seconds is not None
            else os.environ.get("PEAK_TRADE_WEBUI_START_TIMEOUT_SECONDS", "45")
        )
        self.health_path = health_path
        self.review_path = review_path
        self._handle: WebServerHandle | None = None
        self._started_by_us = False

    def _base_env(self) -> dict[str, str]:
        env = dict(os.environ)
        env.update(
            {
                "PEAK_TRADE_WEBUI_HOST": self.host,
                "PEAK_TRADE_WEBUI_PORT": str(self.port),
                "PEAK_TRADE_WEBUI_STATE_DIR": str(self.state_dir),
                "PEAK_TRADE_WEBUI_START_TIMEOUT_SECONDS": str(self.start_timeout_seconds),
                "PEAK_TRADE_WEBUI_HEALTH_PATH": self.health_path,
                "PEAK_TRADE_WEBUI_REVIEW_PATH": self.review_path,
                "LIVE_AUTHORIZED": "false",
                "ORDERS_ALLOWED": "false",
            }
        )
        return env

    def _run_harness(self, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
        script = self.repo_root / "scripts" / "webui" / "review_server.sh"
        if not script.is_file():
            raise FileNotFoundError(script)
        return subprocess.run(
            ["bash", str(script), *args],
            cwd=str(self.repo_root),
            env=self._base_env(),
            text=True,
            capture_output=True,
            check=check,
        )

    def _parse_kv(self, blob: str) -> dict[str, str]:
        out: dict[str, str] = {}
        for line in blob.splitlines():
            if "=" not in line:
                continue
            key, value = line.split("=", 1)
            out[key.strip()] = value.strip()
        return out

    def status(self) -> dict[str, str]:
        proc = self._run_harness("status", check=False)
        return self._parse_kv(proc.stdout + "\n" + proc.stderr)

    def start(self) -> WebServerHandle:
        base = f"http://{self.host}:{self.port}"
        health_url = f"{base}{self.health_path}"
        review_url = f"{base}{self.review_path}"
        st = self.status()
        if st.get("STATUS") == "RUNNING_HEALTHY" and self.reuse_existing:
            handle = WebServerHandle(
                base_url=base,
                host=self.host,
                port=self.port,
                state_dir=self.state_dir,
                managed=False,
                reused_existing=True,
                health_url=health_url,
                review_url=review_url,
            )
            self._handle = handle
            self._started_by_us = False
            return handle

        if st.get("STATUS") == "RUNNING_HEALTHY" and not self.reuse_existing:
            raise RuntimeError(
                "healthy review server already running but reuse_existing=false "
                "(CI_REUSE_EXISTING_SERVER=false)"
            )

        proc = self._run_harness("start", check=False)
        kv = self._parse_kv(proc.stdout + "\n" + proc.stderr)
        if proc.returncode != 0 or kv.get("STATUS") != "RUNNING_HEALTHY":
            raise RuntimeError(
                "review_server start failed: "
                f"rc={proc.returncode} status={kv.get('STATUS')} "
                f"stdout={proc.stdout[-2000:]!r} stderr={proc.stderr[-2000:]!r}"
            )

        deadline = time.time() + self.start_timeout_seconds
        while time.time() < deadline:
            if http_ok(health_url):
                break
            time.sleep(0.2)
        else:
            raise TimeoutError(f"bounded health wait failed for {health_url}")

        handle = WebServerHandle(
            base_url=base,
            host=self.host,
            port=self.port,
            state_dir=self.state_dir,
            managed=True,
            reused_existing=kv.get("ACTION") == "REUSED_EXISTING_HEALTHY",
            health_url=health_url,
            review_url=review_url,
        )
        self._handle = handle
        self._started_by_us = handle.managed and not handle.reused_existing
        return handle

    def stop(self) -> None:
        if not self._started_by_us:
            return
        proc = self._run_harness("stop", check=False)
        if proc.returncode != 0:
            raise RuntimeError(
                f"review_server stop failed: rc={proc.returncode} "
                f"stdout={proc.stdout[-1000:]!r} stderr={proc.stderr[-1000:]!r}"
            )
        self._started_by_us = False

    def __enter__(self) -> WebServerHandle:
        return self.start()

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        self.stop()


def launch_chrome_channel(playwright: Any, *, headless: bool = True) -> tuple[Any, dict[str, Any]]:
    """Launch Google Chrome via Playwright channel=chrome; Chromium fallback reported."""
    report: dict[str, Any] = {
        "PRIMARY_BROWSER": PRIMARY_BROWSER,
        "PRIMARY_PLAYWRIGHT_CHANNEL": PRIMARY_PLAYWRIGHT_CHANNEL,
        "BROWSER_ACTUAL": "NONE",
        "CHROMIUM_FALLBACK_USED": False,
        "REAL_CHROME_VERIFIED": False,
    }
    try:
        browser = playwright.chromium.launch(channel=PRIMARY_PLAYWRIGHT_CHANNEL, headless=headless)
        report["BROWSER_ACTUAL"] = "GOOGLE_CHROME"
        report["REAL_CHROME_VERIFIED"] = True
        return browser, report
    except Exception as exc:  # noqa: BLE001 — bounded diagnostic fallback
        browser = playwright.chromium.launch(headless=headless)
        report["BROWSER_ACTUAL"] = "PLAYWRIGHT_CHROMIUM"
        report["CHROMIUM_FALLBACK_USED"] = True
        report["REAL_CHROME_VERIFIED"] = False
        report["launch_error"] = f"{type(exc).__name__}: {exc}"
        return browser, report
