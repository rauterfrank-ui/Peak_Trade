"""Negative non-regression guards for removed legacy Market Dashboard / market_surface.

Canonical status: REMOVED_WITH_NEGATIVE_NON_REGRESSION_GUARDS.

Legacy market_surface is fully removed and is not an architectural component.
These tests exist solely to prevent reintroduction. They do not define, register,
or authorize any tombstone route, module, presenter, template, source, slot,
fallback, compatibility path, authority, producer, read model, or runtime path.

Filename retained for historical guard-reference stability only.
"""

from __future__ import annotations

import importlib
import re
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.webui.app import create_app

REPO = Path(__file__).resolve().parents[2]
APP_PATH = REPO / "src" / "webui" / "app.py"
BASE_HTML = REPO / "templates" / "peak_trade_dashboard" / "base.html"
REMOVAL_NOTICE = REPO / "docs" / "webui" / "MARKET_DASHBOARD_REMOVED.md"
SHELL_ROUTER = REPO / "src" / "webui" / "market_dashboard_landscape_shell_router_v2.py"
LANDSCAPE_RUNBOOK = (
    REPO
    / "docs"
    / "ops"
    / "market_dashboard"
    / "PEAK_TRADE_MARKET_DASHBOARD_LANDSCAPE_MASTER_RUNBOOK_V2.md"
)

# Historical alias kept so older call sites / greps remain accurate.
TOMBSTONE = REMOVAL_NOTICE

DELETED_PACKAGES = (
    "src.webui.market_surface",
    "src.webui.market_dashboard_product_surface_v1",
    "src.webui.market_dashboard_readmodels_v1",
    "src.webui.market_futures_ohlcv_readmodel_v0",
    "src.webui.market_ranking_funnel_readmodel_v0",
    "src.webui.market_visual_operator_surface_v1",
    "src.webui.market_depth_api_v0",
    "src.webui.futures_read_only_market_dashboard_runtime_v0",
)

DELETED_TEMPLATES = (
    "market_dashboard_product_v1.html",
    "market_v0.html",
)

CANONICAL_REMOVAL_STATEMENT = (
    "Legacy market_surface is fully removed and is not an architectural component."
)

FORBIDDEN_ACTIVE_CLASSIFICATIONS = (
    "TOMBSTONED",
    "DEPRECATED",
    "COMPATIBILITY",
    "FALLBACK",
    "REACTIVATABLE",
    "REACTIVATION",
)

# Productive / canonical architecture surfaces that must not classify legacy
# market_surface as an active, deprecated, compatibility, fallback, or
# reactivatable component.
ARCHITECTURE_SCAN_ROOTS = (
    REPO / "src" / "webui",
    REPO / "config" / "governance",
    REPO / "docs" / "ops" / "market_dashboard",
    REPO / "docs" / "webui",
)

ARCHITECTURE_SCAN_GLOBS = ("*.py", "*.json", "*.md")


@pytest.fixture()
def client() -> TestClient:
    return TestClient(create_app())


def test_landscape_market_route_returns_200(client: TestClient) -> None:
    response = client.get("/market")
    assert response.status_code == 200
    assert 'data-market-landscape-v2="true"' in response.text
    assert response.history == []


def test_market_aliases_return_404(client: TestClient) -> None:
    for path in (
        "/market/double-play",
        "/market/futures",
        "/api/market/ohlcv",
        "/api/market/depth",
    ):
        response = client.get(path)
        assert response.status_code == 404, path
        assert response.history == []


def test_no_legacy_market_router_registration() -> None:
    text = APP_PATH.read_text(encoding="utf-8")
    assert "create_market_router" not in text
    assert "market_surface" not in text
    assert "market_dashboard_landscape_shell_router_v2" in text
    router = SHELL_ROUTER.read_text(encoding="utf-8")
    assert '@router.get("/market"' in router
    assert "@router.post" not in router


def test_deleted_packages_not_importable() -> None:
    for mod in DELETED_PACKAGES:
        with pytest.raises(ModuleNotFoundError):
            importlib.import_module(mod)


def test_deleted_templates_absent() -> None:
    tmpl_dir = REPO / "templates" / "peak_trade_dashboard"
    for name in DELETED_TEMPLATES:
        assert not (tmpl_dir / name).exists()
    assert not (REPO / "static" / "css" / "market_dashboard_product_v1.css").exists()
    assert (tmpl_dir / "market_landscape_v2.html").is_file()


def test_no_legacy_nav_resurrect_aliases() -> None:
    html = BASE_HTML.read_text(encoding="utf-8")
    # Global chrome may later link Landscape; must not resurrect legacy APIs.
    assert "/api/market/ohlcv" not in html
    hub = REPO / "templates" / "peak_trade_dashboard" / "observability_hub.html"
    hub_text = hub.read_text(encoding="utf-8")
    assert "/api/market/ohlcv" not in hub_text


def test_no_reset_shell_or_legacy_product_surface_markers(client: TestClient) -> None:
    html = client.get("/market").text.lower()
    assert "architecture reset in progress" not in html
    assert "data-market-architecture-reset-shell-v1" not in html
    assert "data-market-dashboard-product-surface-v1" not in html
    assert "data-market-landscape-v2" in html


def test_removal_notice_doc_present() -> None:
    assert REMOVAL_NOTICE.is_file()
    text = REMOVAL_NOTICE.read_text(encoding="utf-8")
    assert "intentionally" in text.lower()
    # Docs token policy requires illustrative path encoding (GET &#47;market).
    assert "GET &#47;market" in text
    assert "GET /market" not in text
    assert "Landscape V2" in text or "landscape v2" in text.lower()
    assert "REMOVED_WITH_NEGATIVE_NON_REGRESSION_GUARDS" in text
    assert CANONICAL_REMOVAL_STATEMENT in text
    assert "No tombstone route" in text
    assert "not an architectural component" in text.lower()


def test_tombstone_doc_present() -> None:
    """Historical name retained; asserts the removal notice remains present."""
    test_removal_notice_doc_present()


def test_no_legacy_dashboard_product_tests_or_fixtures_remain() -> None:
    assert not (REPO / "tests" / "fixtures" / "market_futures_ohlcv_readmodel_v0").exists()
    assert not (REPO / "tests" / "fixtures" / "market_ranking_funnel_readmodel_v0").exists()
    remaining = sorted((REPO / "tests" / "webui").glob("test_market_dashboard_*.py"))
    assert remaining == [REPO / "tests" / "webui" / "test_market_dashboard_tombstone_v1.py"]


def test_legacy_market_surface_not_classified_as_active_or_reactivatable_surface() -> None:
    """Prove absence of active/tombstone/compatibility classification only."""
    assert LANDSCAPE_RUNBOOK.is_file()
    runbook = LANDSCAPE_RUNBOOK.read_text(encoding="utf-8")
    assert "LEGACY_MARKET_SURFACE_STATUS=REMOVED_WITH_NEGATIVE_NON_REGRESSION_GUARDS" in runbook
    assert "LEGACY_MARKET_SURFACE_IS_ARCHITECTURAL_COMPONENT=false" in runbook
    assert "ACTIVE_TOMBSTONE_SURFACE=false" in runbook
    assert "LEGACY_PRODUCT_TOMBSTONE=" not in runbook

    # Forbidden: classify market_surface itself as a live/compat/fallback surface.
    # Allowed: deny-lists and explicit REMOVED / not-an-architectural-component wording.
    classification_near_market_surface = re.compile(
        r"(?is)market_surface.{0,120}("
        + "|".join(FORBIDDEN_ACTIVE_CLASSIFICATIONS)
        + r")|("
        + "|".join(FORBIDDEN_ACTIVE_CLASSIFICATIONS)
        + r").{0,120}market_surface"
    )
    allowed_context = re.compile(
        r"(?is)(REMOVED_WITH_NEGATIVE_NON_REGRESSION_GUARDS|"
        r"not an architectural component|"
        r"forbidden|"
        r"rejected|"
        r"REASON_MARKET_SURFACE_NOT_OBSERVABILITY_TRUTH|"
        r"Dummy truth|"
        r"no tombstone)"
    )

    violations: list[str] = []
    for root in ARCHITECTURE_SCAN_ROOTS:
        if not root.exists():
            continue
        for pattern in ARCHITECTURE_SCAN_GLOBS:
            for path in root.rglob(pattern):
                if path.name == "MARKET_DASHBOARD_REMOVED.md":
                    # Canonical removal notice may mention "tombstone" only to deny it.
                    continue
                if path.name == Path(__file__).name:
                    continue
                text = path.read_text(encoding="utf-8")
                if "market_surface" not in text:
                    continue
                for match in classification_near_market_surface.finditer(text):
                    window = text[max(0, match.start() - 160) : match.end() + 160]
                    if allowed_context.search(window):
                        continue
                    # Deny-list / rejection fixtures are negative controls.
                    if any(
                        token in window
                        for token in (
                            "FORBIDDEN",
                            "forbidden",
                            "rejected",
                            "reject",
                            "not_importable",
                            "DELETED_PACKAGES",
                            '"market_surface"',
                            "'market_surface'",
                        )
                    ):
                        continue
                    violations.append(f"{path.relative_to(REPO)}: {match.group(0)!r}")

    assert violations == [], (
        "legacy market_surface reclassified as active/compat surface:\n" + "\n".join(violations)
    )


def test_no_productive_market_surface_module_or_template_exists() -> None:
    assert not (REPO / "src" / "webui" / "market_surface.py").exists()
    assert not (REPO / "src" / "webui" / "market_surface").exists()
    assert not (REPO / "docs" / "webui" / "MARKET_SURFACE_V0.md").exists()
