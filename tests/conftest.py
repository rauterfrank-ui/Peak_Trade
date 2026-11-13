"""Autouse bypass for legacy runtime entrypoint tests (Slice D).

Historical runtime/session tests may construct legacy entrypoints only when
``PT_LEGACY_RUNTIME_ENTRYPOINT_TEST_ONLY=1``. Slice D contract tests opt out.
"""

from __future__ import annotations

from importlib.util import find_spec
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

# The pure historical suites require the packages retired in PR #6579.
# Mixed test modules keep their current contracts in collection.
collect_ignore = []
if find_spec("src.autonomous") is None:
    collect_ignore.extend(
        [
            "test_autonomous_decision_engine.py",
            "test_autonomous_monitors.py",
            "test_autonomous_workflow_engine.py",
        ]
    )
if find_spec("src.trigger_training") is None:
    collect_ignore.append("trigger_training")


@pytest.fixture(autouse=True)
def _legacy_runtime_entrypoint_test_only_bypass(request: pytest.FixtureRequest, monkeypatch):
    node_path = str(request.node.fspath)
    if _SLICE_D_TEST_MODULE in node_path:
        return
    monkeypatch.setenv("PT_LEGACY_RUNTIME_ENTRYPOINT_TEST_ONLY", "1")
