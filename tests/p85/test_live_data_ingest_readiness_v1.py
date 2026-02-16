"""P85 live data ingest readiness tests."""

from pathlib import Path
from unittest.mock import patch

import pytest

from src.ops.p85.run_live_data_ingest_readiness_v1 import (
    P85ContextV1,
    run_live_data_ingest_readiness_v1,
)


def test_p85_context() -> None:
    """P85ContextV1 has required fields."""
    ctx = P85ContextV1(mode="shadow", run_id="test", out_dir="/tmp/p85")
    assert ctx.mode == "shadow"
    assert ctx.run_id == "test"
    assert ctx.out_dir == "/tmp/p85"


def test_p85_live_only_paper_shadow(tmp_path: Path) -> None:
    """P85 rejects live/record mode."""
    ctx = P85ContextV1(mode="live", run_id="test", out_dir=str(tmp_path))
    with pytest.raises(PermissionError, match="only paper/shadow"):
        run_live_data_ingest_readiness_v1(ctx)


def test_p85_run_persists_result(tmp_path: Path) -> None:
    """P85 writes P85_RESULT.json to out_dir."""
    ctx = P85ContextV1(mode="shadow", run_id="test", out_dir=str(tmp_path))
    # Mock connectivity to avoid network in tests
    mock_response = b'{"error":[],"result":{"unixtime":1700000000,"rfc1123":"..."}}'

    with patch("urllib.request.urlopen") as mock_open:
        mock_resp = mock_open.return_value.__enter__.return_value
        mock_resp.read.return_value = mock_response
        mock_resp.status = 200

        report = run_live_data_ingest_readiness_v1(ctx)

    assert "overall_ok" in report
    assert "checks" in report
    result_path = tmp_path / "P85_RESULT.json"
    assert result_path.exists()
    loaded = __import__("json").loads(result_path.read_text())
    assert loaded["meta"]["p85_version"] == "v1"
    assert loaded["meta"]["run_id"] == "test"


def test_p85_connectivity_failure(tmp_path: Path) -> None:
    """P85 reports NOT_READY when connectivity fails."""
    ctx = P85ContextV1(mode="shadow", run_id="test", out_dir=str(tmp_path))

    with patch("urllib.request.urlopen") as mock_open:
        mock_open.side_effect = OSError("Connection refused")

        report = run_live_data_ingest_readiness_v1(ctx)

    assert report["overall_ok"] is False
    conn_check = next(c for c in report["checks"] if c["id"] == "connectivity")
    assert conn_check["ok"] is False
