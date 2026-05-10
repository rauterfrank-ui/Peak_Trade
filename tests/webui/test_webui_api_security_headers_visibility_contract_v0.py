"""Static visibility contract for WebUI/API security-header surfaces.

Parses `src/webui` Python files as UTF-8 text only. Never starts an ASGI HTTP
server process, never constructs Starlette/FastAPI test clients, never invokes
routes, never touches runtime state, and never changes WebUI behavior.

This contract freezes the current WebUI route/header inventory as an
owner-review surface. It does not require source changes and does not treat
routes without local header markers as a hard failure without owner decision.
"""

from __future__ import annotations

import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
WEBUI_ROOT = REPO_ROOT / "src" / "webui"

ROUTE_DECORATOR_RX = re.compile(
    r"^\s*@(?:app|router)\.(?:get|post|put|delete|patch)\(",
    re.MULTILINE,
)

SECURITY_HEADER_RX = re.compile(
    r"Cache-Control|no-store|no-cache|"
    r"X-Content-Type-Options|Content-Security-Policy|"
    r"Referrer-Policy|X-Frame-Options",
    re.IGNORECASE,
)

KNOWN_WEBUI_ROUTE_FILES_WITH_LOCAL_SECURITY_HEADER_MARKERS = frozenset(
    {
        "src/webui/app.py",
        "src/webui/double_play_dashboard_display_json_route_v0.py",
        "src/webui/execution_watch_api_v0.py",
        "src/webui/market_depth_api_v0.py",
    }
)

KNOWN_WEBUI_ROUTE_FILES_WITHOUT_LOCAL_SECURITY_HEADER_MARKERS = frozenset(
    {
        "src/webui/execution_watch_api_v0_2.py",
        "src/webui/health_endpoint.py",
        "src/webui/knowledge_api.py",
        "src/webui/market_surface.py",
        "src/webui/ops_ci_health_router.py",
        "src/webui/ops_stage1_router.py",
        "src/webui/ops_workflows_router.py",
        "src/webui/paper_shadow_summary_api_v0.py",
        "src/webui/r_and_d_api.py",
    }
)


def _webui_python_files() -> list[Path]:
    return sorted(path for path in WEBUI_ROOT.rglob("*.py") if path.is_file())


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _rel(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


def _has_route_decorator(path: Path) -> bool:
    return bool(ROUTE_DECORATOR_RX.search(_text(path)))


def _has_local_security_header_marker(path: Path) -> bool:
    return bool(SECURITY_HEADER_RX.search(_text(path)))


def _route_files_by_header_visibility() -> tuple[set[str], set[str]]:
    with_headers: set[str] = set()
    without_headers: set[str] = set()

    for path in _webui_python_files():
        if not _has_route_decorator(path):
            continue

        if _has_local_security_header_marker(path):
            with_headers.add(_rel(path))
        else:
            without_headers.add(_rel(path))

    return with_headers, without_headers


def test_webui_api_security_headers_visibility_contract_has_webui_files_to_check() -> None:
    files = _webui_python_files()

    assert WEBUI_ROOT.exists()
    assert files


def test_webui_api_security_headers_visibility_contract_module_avoids_runtime_hooks() -> None:
    test_text = Path(__file__).read_text(encoding="utf-8")
    import_lines = [
        line.strip()
        for line in test_text.splitlines()
        if line.strip().startswith(("import ", "from "))
    ]

    forbidden_import_prefixes = [
        "import os",
        "from os",
        "import subprocess",
        "from subprocess",
        "import runpy",
        "from runpy",
        "import importlib",
        "from importlib",
        "import requests",
        "from requests",
        "import httpx",
        "from httpx",
        "import urllib",
        "from urllib",
        "import socket",
        "from socket",
        "from fastapi.testclient",
        "import fastapi",
        "from starlette.testclient",
    ]

    found = [
        prefix
        for prefix in forbidden_import_prefixes
        if any(line.startswith(prefix) for line in import_lines)
    ]
    assert not found, f"static WebUI contract must not import runtime/network hooks: {found}"


def test_webui_api_security_headers_visibility_contract_classifies_current_sets() -> None:
    with_headers, without_headers = _route_files_by_header_visibility()

    assert frozenset(with_headers) == KNOWN_WEBUI_ROUTE_FILES_WITH_LOCAL_SECURITY_HEADER_MARKERS
    assert (
        frozenset(without_headers) == KNOWN_WEBUI_ROUTE_FILES_WITHOUT_LOCAL_SECURITY_HEADER_MARKERS
    )


def test_webui_api_security_headers_visibility_contract_known_sets_stay_documentary() -> None:
    """Known sets are owner-review surfaces, not WebUI behavior-change mandates."""
    assert len(KNOWN_WEBUI_ROUTE_FILES_WITH_LOCAL_SECURITY_HEADER_MARKERS) == 4
    assert len(KNOWN_WEBUI_ROUTE_FILES_WITHOUT_LOCAL_SECURITY_HEADER_MARKERS) == 9


def test_webui_api_security_headers_visibility_contract_requires_route_decorators_for_known_sets() -> (
    None
):
    all_known = (
        KNOWN_WEBUI_ROUTE_FILES_WITH_LOCAL_SECURITY_HEADER_MARKERS
        | KNOWN_WEBUI_ROUTE_FILES_WITHOUT_LOCAL_SECURITY_HEADER_MARKERS
    )

    missing_route_decorators = [
        rel_path for rel_path in sorted(all_known) if not _has_route_decorator(REPO_ROOT / rel_path)
    ]

    assert not missing_route_decorators, (
        f"known WebUI route files lost route-decorator visibility: {missing_route_decorators}"
    )


def test_webui_api_security_headers_visibility_contract_requires_header_markers_for_with_header_set() -> (
    None
):
    missing_header_markers = [
        rel_path
        for rel_path in sorted(KNOWN_WEBUI_ROUTE_FILES_WITH_LOCAL_SECURITY_HEADER_MARKERS)
        if not _has_local_security_header_marker(REPO_ROOT / rel_path)
    ]

    assert not missing_header_markers, (
        f"known WebUI header-covered files lost local header markers: {missing_header_markers}"
    )


def test_webui_api_security_headers_visibility_contract_retains_static_local_scope() -> None:
    test_text = Path(__file__).read_text(encoding="utf-8")

    forbidden_fragments = [
        "".join(("TestClient", "(")),
        "".join(("uvi", "corn")),
        "".join(("subprocess", ".")),
        "".join(("os", ".system")),
        "".join(("runpy", ".")),
        "".join(("importlib", ".import_module")),
        "".join(("requests", ".")),
        "".join(("httpx", ".")),
        "".join(("urllib", ".")),
        "".join(("socket", ".")),
    ]

    found = [fragment for fragment in forbidden_fragments if fragment in test_text]
    assert not found, f"contract must remain static/local-only: {found}"
