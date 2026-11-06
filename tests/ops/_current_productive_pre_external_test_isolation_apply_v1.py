"""Apply per-test F1/M9 + Master-V2 isolation (delegates to authoritative establish)."""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.ops._current_productive_pre_external_test_process_isolation_v1 import (
    establish_current_productive_pre_external_test_process_isolation_v1,
)


def apply_current_productive_pre_external_f1_m9_test_isolation_v1(
    *,
    monkeypatch: pytest.MonkeyPatch,
    f1_root: Path,
) -> None:
    establish_current_productive_pre_external_test_process_isolation_v1(
        monkeypatch=monkeypatch,
        f1_root=f1_root,
        reseed_workspace_f1_m9=False,
    )


__all__ = ["apply_current_productive_pre_external_f1_m9_test_isolation_v1"]
