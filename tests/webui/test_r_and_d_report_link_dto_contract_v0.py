"""In-memory contract for ``RnDReportLink`` DTO (v0).

No TestClient, router/HTTP execution, filesystem, subprocess, env, or network.

Prod definition lives in ``src.webui.r_and_d_api``.
"""

from __future__ import annotations

import pytest

pytest.importorskip("fastapi")

from src.webui.r_and_d_api import RnDReportLink


def _model_dump_public(model: object) -> dict:
    dump = getattr(model, "model_dump", None)
    if callable(dump):
        return dump(mode="python")
    legacy = getattr(model, "dict", None)
    if callable(legacy):
        return legacy()
    raise AssertionError("expected BaseModel-like model_dump()/dict()")


def _minimal() -> RnDReportLink:
    return RnDReportLink(
        type="markdown",
        label="Report",
        path="reports/x.md",
        url="/api/r_and_d/reports/x.md",
    )


def test_rnd_report_link_import_contract_v0() -> None:
    assert RnDReportLink.__name__ == "RnDReportLink"


def test_rnd_report_link_required_fields_and_default_exists_contract_v0() -> None:
    link = _minimal()
    assert link.type == "markdown"
    assert link.label == "Report"
    assert link.path == "reports/x.md"
    assert link.url == "/api/r_and_d/reports/x.md"
    assert link.exists is True


def test_rnd_report_link_override_exists_contract_v0() -> None:
    link = RnDReportLink(
        type="html",
        label="HTML view",
        path="out/index.html",
        url="/r_and_d/html/run_1/",
        exists=False,
    )
    assert link.exists is False


def test_rnd_report_link_model_fields_public_contract_v0() -> None:
    assert set(RnDReportLink.model_fields.keys()) == {
        "type",
        "label",
        "path",
        "url",
        "exists",
    }


def test_rnd_report_link_dump_shape_stable_contract_v0() -> None:
    link = _minimal()
    assert _model_dump_public(link) == {
        "type": "markdown",
        "label": "Report",
        "path": "reports/x.md",
        "url": "/api/r_and_d/reports/x.md",
        "exists": True,
    }
