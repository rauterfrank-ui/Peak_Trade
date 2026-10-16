"""Contract tests for presentation_materializer_import_guard_v1."""

from __future__ import annotations

import pytest

from tests.webui.presentation_materializer_import_guard_v1 import (
    assert_import_modules_allowed,
)


def test_import_guard_rejects_src_webui_module_path() -> None:
    with pytest.raises(AssertionError, match="forbidden webui import"):
        assert_import_modules_allowed(
            ["src.webui.workflow_dashboard_readmodel_v1.double_play_presentation_projection_v1"]
        )


def test_import_guard_rejects_webui_root_module_path() -> None:
    with pytest.raises(AssertionError, match="forbidden webui import"):
        assert_import_modules_allowed(["webui.app"])


def test_import_guard_allows_src_ops_workflow_archive_projections() -> None:
    assert_import_modules_allowed(
        [
            "src.ops.workflow_archive_readmodel_projections_v1.double_play_presentation_projection_v1",
            "src.ops.archive_sibling_export_contract_v1.manifest_finalize_v1",
        ],
        forbidden_roots=frozenset({"trading"}),
    )


def test_import_guard_rejects_trading_root() -> None:
    with pytest.raises(AssertionError, match="forbidden import root 'trading'"):
        assert_import_modules_allowed(
            ["trading.master_v2.foo"],
            forbidden_roots=frozenset({"trading"}),
        )
