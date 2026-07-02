"""Autouse bypass for legacy runtime entrypoint tests (Slice D).

Historical runtime/session tests may construct legacy entrypoints only when
``PT_LEGACY_RUNTIME_ENTRYPOINT_TEST_ONLY=1``. Slice D contract tests opt out.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SRC_ROOT = _REPO_ROOT / "src"
if str(_SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(_SRC_ROOT))
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

_SLICE_D_TEST_MODULE = "test_canonical_core_runtime_integration_bridge_slice_d_v0"


@pytest.fixture(autouse=True)
def _legacy_runtime_entrypoint_test_only_bypass(request: pytest.FixtureRequest, monkeypatch):
    node_path = str(request.node.fspath)
    if _SLICE_D_TEST_MODULE in node_path:
        return
    monkeypatch.setenv("PT_LEGACY_RUNTIME_ENTRYPOINT_TEST_ONLY", "1")
