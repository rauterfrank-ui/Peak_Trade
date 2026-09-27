"""Shared fixtures for tests/ops (PRE_EXTERNAL process-state isolation)."""

from __future__ import annotations

import pytest

from tests.ops._current_productive_pre_external_shared_process_state_v1 import (
    reseed_workspace_canonical_f1_m9_runtime_ledgers_v1,
    reset_current_productive_pre_external_shared_test_process_state_v1,
)
from tests.ops._current_productive_pre_external_test_isolation_apply_v1 import (
    apply_current_productive_pre_external_f1_m9_test_isolation_v1,
)


def _needs_current_productive_pre_external_process_isolation_v1(nodeid: str) -> bool:
    needles = (
        "pre_external",
        "gap_true_01",
        "order_independence",
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

    reset_current_productive_pre_external_shared_test_process_state_v1()
    reseed_workspace_canonical_f1_m9_runtime_ledgers_v1()
    f1_root = tmp_path / "f1-m9-canonical-isolation"
    f1_root.mkdir()
    apply_current_productive_pre_external_f1_m9_test_isolation_v1(
        monkeypatch=monkeypatch,
        f1_root=f1_root,
    )

    yield

    reset_current_productive_pre_external_shared_test_process_state_v1()
