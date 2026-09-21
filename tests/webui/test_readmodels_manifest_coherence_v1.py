"""Manifest coherence after presentation materializer writes (Phase V recovery)."""

from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

import pytest

from scripts.ops.primary_evidence_retention_v0 import verify_manifest_sha256, write_manifest_sha256
from src.webui.market_dashboard_landscape_producer_binding_v2 import bind_market_universe_slots
from src.webui.workflow_dashboard_readmodel_v1.dynamic_scope_presentation_projection_materializer_v1 import (
    materialize_dynamic_scope_presentation_projection_v1,
)
from src.webui.workflow_dashboard_readmodel_v1.universe_selection_reader_v1 import (
    try_load_universe_selection_for_dashboard,
)
from tests.webui.test_dynamic_scope_presentation_projection_materializer_v1 import (
    _durable_state,
    _write_source_state,
)
from tests.webui.test_market_landscape_dashboard_v2_okx_ohlcv_continuous_refresh_v0 import (
    _write_universe,
)


def _write_universe_fixture(archive: Path) -> None:
    _write_universe(archive)
    _write_source_state(archive, _durable_state())
    write_manifest_sha256(archive / "readmodels")


def test_materializer_write_keeps_manifest_and_universe_bind_available(
    tmp_path: Path,
) -> None:
    archive = tmp_path / "archive"
    _write_universe_fixture(archive)
    readmodels = archive / "readmodels"

    before_ok, _ = verify_manifest_sha256(readmodels)
    assert before_ok is True
    slots_before = bind_market_universe_slots(
        generated_at=datetime.now(timezone.utc),
        archive_root=archive,
    )
    assert slots_before["universe_ranking"].availability.value == "AVAILABLE"

    result = materialize_dynamic_scope_presentation_projection_v1(
        archive_root=archive,
        generated_at="2026-09-21T14:38:22Z",
    )
    assert result.written is True

    after_ok, after_msg = verify_manifest_sha256(readmodels)
    assert after_ok is True, after_msg

    slice_after = try_load_universe_selection_for_dashboard(archive)
    assert slice_after.loaded is True
    assert not slice_after.load_errors

    slots_after = bind_market_universe_slots(
        generated_at=datetime.now(timezone.utc),
        archive_root=archive,
    )
    assert slots_after["universe_ranking"].availability.value == "AVAILABLE"
    assert slots_after["market_instrument"].instrument_id is not None


def test_corrupt_manifest_stays_invalid_without_bypass(tmp_path: Path) -> None:
    archive = tmp_path / "archive"
    _write_universe_fixture(archive)
    readmodels = archive / "readmodels"
    universe_path = readmodels / "universe_selection_readmodel.v1.json"
    universe_path.write_bytes(universe_path.read_bytes() + b" ")

    ok, msg = verify_manifest_sha256(readmodels)
    assert ok is False
    assert "checksum mismatch" in msg

    sl = try_load_universe_selection_for_dashboard(archive)
    assert sl.loaded is False
    assert sl.load_errors == ("MANIFEST_VERIFY_FAILED",)

    slots = bind_market_universe_slots(
        generated_at=datetime.now(timezone.utc),
        archive_root=archive,
    )
    assert slots["universe_ranking"].availability.value == "INVALID"
