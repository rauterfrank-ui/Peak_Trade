"""Architecture guards for Landscape V3 fresh build."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.webui.app import create_app
from src.webui.market_dashboard_landscape_v3.constants_v1 import V3_SNAPSHOT_API_ROUTE
from src.webui.market_dashboard_landscape_v3.safety_v1 import (
    FORBIDDEN_IMPORT_PREFIXES,
    FORBIDDEN_SUBSTRINGS,
    V3_JS,
    V3_PKG,
    V3_ROUTER,
    V3_TEMPLATE,
)

REPO = Path(__file__).resolve().parents[2]


def _iter_py(root: Path) -> list[Path]:
    return sorted(p for p in root.rglob("*.py") if p.is_file())


def _imports(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    mods: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            mods.extend(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            mods.append(node.module)
    return mods


def test_v3_package_no_forbidden_imports() -> None:
    hits: list[str] = []
    for path in _iter_py(V3_PKG) + [V3_ROUTER]:
        for mod in _imports(path):
            for prefix in FORBIDDEN_IMPORT_PREFIXES:
                if mod == prefix or mod.startswith(prefix + "."):
                    hits.append(f"{path.relative_to(REPO)}:{mod}")
    assert hits == []


def test_v3_assets_do_not_reference_v2_or_global_okx() -> None:
    for path in (V3_TEMPLATE, V3_JS):
        text = path.read_text(encoding="utf-8")
        for token in FORBIDDEN_SUBSTRINGS:
            if token in ("market_dashboard_landscape_v2", "www.okx.com"):
                assert token not in text, path.name


def test_v3_routes_are_get_and_ws_only() -> None:
    client = TestClient(create_app())
    for method, path in (
        ("POST", "/market/v3"),
        ("POST", "/api/market/v3/snapshot"),
        ("PUT", "/market/v3"),
    ):
        resp = client.request(method, path)
        assert resp.status_code in {405, 404, 422}


def test_snapshot_declares_no_authority() -> None:
    snap = TestClient(create_app()).get(V3_SNAPSHOT_API_ROUTE).json()
    assert snap["authority"] == "NONE"
    assert snap["selection_authority"] == "NONE"
    assert snap["execution_authority"] == "NONE"
    assert snap["diagnostics"]["direct_browser_okx"] is False


def test_upstream_rejects_global_rest_host() -> None:
    from src.ops.peak_trade_public_market_data_runtime_v1.rest_recovery_v1 import (
        PublicRestRecoveryError,
        assert_eea_rest_host_v1,
    )

    with pytest.raises(PublicRestRecoveryError):
        assert_eea_rest_host_v1("www.okx.com")
