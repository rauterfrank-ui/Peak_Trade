"""Shared fixtures for tests/ops (PRE_EXTERNAL process-state isolation)."""

from __future__ import annotations

import pytest

from tests.ops._current_productive_pre_external_shared_process_state_v1 import (
    reset_current_productive_pre_external_shared_test_process_state_v1,
)
from tests.ops._current_productive_pre_external_test_process_isolation_v1 import (
    establish_current_productive_pre_external_test_process_isolation_v1,
)


def _needs_current_productive_pre_external_process_isolation_v1(nodeid: str) -> bool:
    needles = (
        "pre_external",
        "gap_true_01",
        "order_independence",
        "one_shot_enter_e2e",
        "e2e_runtime_handoff",
    )
    return any(needle in nodeid for needle in needles)


@pytest.fixture(autouse=True)
def _current_productive_pre_external_process_isolation_v1(
    request: pytest.FixtureRequest,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    """Per-test isolated F1/M9 canonical ledger resolution + G17/F1 test caches."""
    if not _needs_current_productive_pre_external_process_isolation_v1(request.node.nodeid):
        yield
        return

    f1_root = tmp_path / "f1-m9-canonical-isolation"
    establish_current_productive_pre_external_test_process_isolation_v1(
        monkeypatch=monkeypatch,
        f1_root=f1_root,
        reseed_workspace_f1_m9=False,
    )

    yield

    reset_current_productive_pre_external_shared_test_process_state_v1()
