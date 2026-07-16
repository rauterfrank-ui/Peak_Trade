"""Active Browser Verification Policy: Chrome primary, Safari secondary."""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

pytestmark = pytest.mark.web

RUNBOOK = (
    project_root
    / "docs"
    / "product"
    / "Peak_Trade_Visual_Operator_Dashboard_Product_Runbook_v1.3.md"
)
HARNESS = project_root / "scripts" / "webui" / "market_dashboard_chrome_playwright_harness_v1.py"


def test_runbook_browser_policy_chrome_primary() -> None:
    text = RUNBOOK.read_text(encoding="utf-8")
    assert "# Browser Verification Policy" in text
    assert "PRIMARY_BROWSER=GOOGLE_CHROME" in text
    assert "PRIMARY_BROWSER_AUTOMATION=PLAYWRIGHT" in text
    assert "PRIMARY_PLAYWRIGHT_CHANNEL=chrome" in text
    assert "PRIMARY_BROWSER_SCREENSHOTS=CHROME" in text
    assert "PRIMARY_DOM_ASSERTIONS=CHROME" in text
    assert "PRIMARY_CONSOLE_ASSERTIONS=CHROME" in text
    assert "PRIMARY_NETWORK_ASSERTIONS=CHROME" in text
    assert "PRIMARY_INTERACTION_ASSERTIONS=CHROME" in text
    assert "CHROMIUM_FALLBACK_ALLOWED=true" in text
    assert "CHROMIUM_FALLBACK_MUST_BE_REPORTED=true" in text
    assert "PLAYWRIGHT_CHROMIUM_IS_NOT_REAL_CHROME=true" in text
    assert "WEBKIT_VERIFICATION=SECONDARY" in text
    assert "WEBKIT_IS_NOT_REAL_SAFARI=true" in text
    assert "REAL_SAFARI_VERIFICATION=SECONDARY" in text
    assert "SAFARI_REQUIRED_FOR_NORMAL_SLICE_MERGE=false" in text
    assert "SAFARI_FAILURE_BLOCKS_NORMAL_SLICE=false" in text
    assert "POST_SLICE_INTERACTIVE_OPEN=REAL_CHROME" in text
    # No active Safari-as-primary / Safari merge-blocker DoD
    assert "SAFARI_PASS=true" not in text
    assert "REAL_SAFARI_BASELINE=open_-a_Safari_manual" not in text
    assert re.search(r"(?m)^- desktop Safari$", text) is None
    assert "Safari Screenshots," not in text


def test_runbook_version_not_bumped_and_single_file() -> None:
    assert RUNBOOK.name == "Peak_Trade_Visual_Operator_Dashboard_Product_Runbook_v1.3.md"
    siblings = list(
        (project_root / "docs" / "product").glob(
            "Peak_Trade_Visual_Operator_Dashboard_Product_Runbook_v1.3*.md"
        )
    )
    assert siblings == [RUNBOOK]


def test_chrome_playwright_harness_module_exists_and_is_chrome_primary() -> None:
    assert HARNESS.is_file()
    text = HARNESS.read_text(encoding="utf-8")
    assert 'channel="chrome"' in text or "channel='chrome'" in text
    assert "PLAYWRIGHT_CHROMIUM" in text
    assert "REAL_CHROME_VERIFIED" in text
    assert "CHROMIUM_REPORTED_AS_REAL_CHROME" in text


def test_harness_launch_prefers_chrome_channel() -> None:
    pytest.importorskip("playwright")
    from playwright.sync_api import sync_playwright

    sys.path.insert(0, str(project_root / "scripts" / "webui"))
    from market_dashboard_chrome_playwright_harness_v1 import launch_browser

    with sync_playwright() as p:
        browser, report = launch_browser(p, headless=True)
        try:
            assert report.BROWSER_REQUESTED == "GOOGLE_CHROME"
            assert report.PLAYWRIGHT_CHANNEL == "chrome"
            if report.BROWSER_ACTUAL == "GOOGLE_CHROME":
                assert report.REAL_CHROME_VERIFIED is True
                assert report.CHROMIUM_FALLBACK_USED is False
                assert report.CHROMIUM_REPORTED_AS_REAL_CHROME is False
            else:
                assert report.BROWSER_ACTUAL == "PLAYWRIGHT_CHROMIUM"
                assert report.REAL_CHROME_VERIFIED is False
                assert report.CHROMIUM_FALLBACK_USED is True
                assert report.CHROMIUM_REPORTED_AS_REAL_CHROME is False
        finally:
            browser.close()
