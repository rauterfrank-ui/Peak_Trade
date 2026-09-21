"""Bounded Economic Summary archive sibling exporter V1 — focused contract tests."""

from __future__ import annotations

import ast
import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from src.backtest import economic_viability_evidence_v1 as ev
from src.ops.economic_summary_archive_sibling_exporter_v1.constants_v1 import (
    CAPABILITY_ID,
    ERROR_BUNDLE_PATH_REQUIRED,
    ERROR_CROSS_SECTIONAL_SHAPE,
    ERROR_MANIFEST_OR_CONTRACT_FAIL,
    TARGET_RELATIVE_PATH,
)
from src.ops.economic_summary_archive_sibling_exporter_v1.exporter_v1 import (
    export_economic_summary_to_archive_sibling_from_explicit_bundle_v1,
)
from src.ops.economic_summary_archive_sibling_exporter_v1.explicit_bundle_source_v1 import (
    build_economic_summary_sibling_payload_from_explicit_bundle_v1,
)
from src.ops.productive_decision_host_active_archive_three_family_binding_v1.family_export_adapter_v1 import (
    export_families_after_runtime_commit_v1,
)
from src.ops.productive_decision_host_active_archive_three_family_binding_v1.models_v1 import (
    ArchiveBindingV1,
)
from src.ops.productive_decision_host_active_archive_three_family_binding_v1.state_root_layout_v1 import (
    materialize_state_root_layout_v1,
)
from src.webui.market_dashboard_landscape_producer_binding_v2 import (
    economic_viability_evidence_fields_from_v1,
)
from src.webui.workflow_dashboard_readmodel_v1.economic_summary_presentation_projection_materializer_v1 import (
    SOURCE_FIELDS_RELATIVE_PATH,
    materialize_economic_summary_presentation_projection_v1,
)
from src.webui.workflow_dashboard_readmodel_v1.economic_summary_presentation_projection_v1 import (
    try_load_economic_summary_presentation_projection_v1,
)
from tests.backtest.test_economic_viability_evidence_v1 import (
    _admissibility,
    _bars,
    _cfg,
)

EXPORTER_PKG = Path("src/ops/economic_summary_archive_sibling_exporter_v1")
PRODUCER_BINDING = Path("src/webui/market_dashboard_landscape_producer_binding_v2.py")
FORBIDDEN_IMPORT_PREFIXES = (
    "src.webui",
    "webui",
    "src.webui.",
)


def test_capability_id_is_stable() -> None:
    assert CAPABILITY_ID == "CAPABILITY_ECONOMIC_SUMMARY_ARCHIVE_SIBLING_EXPORTER_V1"


def test_exporter_module_has_no_top_level_webui_imports() -> None:
    tree = ast.parse((EXPORTER_PKG / "exporter_v1.py").read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert not any(alias.name.startswith(p) for p in FORBIDDEN_IMPORT_PREFIXES)
        if isinstance(node, ast.ImportFrom) and node.module:
            assert not any(node.module.startswith(p) for p in FORBIDDEN_IMPORT_PREFIXES)


def _persist_step29m_bundle(
    tmp_path: Path,
    *,
    suffix: str = "a",
    cfg=None,
) -> Path:
    bars = _bars()
    adm = _admissibility(bars)
    out = tmp_path / f"step29m_bundle_{suffix}"
    ev.build_and_persist_economic_viability_evidence_bundle_v1(
        out,
        bars=bars,
        data_admissibility=adm,
        strategy_id="ma_crossover",
        cfg=cfg if cfg is not None else _cfg(),
        input_provenance={"source": "synthetic_fixture", "bars_ref": "test::_bars"},
    )
    return out


def test_explicit_bundle_export_materialize_loader_and_field_mapping(tmp_path: Path) -> None:
    bundle = _persist_step29m_bundle(tmp_path)
    loaded = ev.load_economic_viability_evidence_bundle_v1(bundle)
    expected = economic_viability_evidence_fields_from_v1(
        loaded.evidence,
        generated_at=datetime(2026, 9, 21, 12, 0, 0, tzinfo=timezone.utc),
        source_reference=str(bundle),
    )
    for drop in ("generated_at", "source_reference"):
        expected.pop(drop, None)

    archive = tmp_path / "archive"
    out = export_economic_summary_to_archive_sibling_from_explicit_bundle_v1(
        archive_root=archive,
        economic_viability_evidence_bundle_path=bundle,
        source_label="test_explicit_bundle",
    )
    assert out.exported is True
    sibling_path = archive / SOURCE_FIELDS_RELATIVE_PATH
    assert sibling_path.is_file()
    sibling = json.loads(sibling_path.read_text(encoding="utf-8"))
    assert list(sibling.pop("reason_codes", [])) == list(expected.pop("reason_codes", []))
    assert sibling == expected

    ts_iso = "2026-09-21T12:00:00Z"
    mat = materialize_economic_summary_presentation_projection_v1(
        archive,
        generated_at=ts_iso,
        effective_at=ts_iso,
    )
    assert mat.written is True
    loaded_proj = try_load_economic_summary_presentation_projection_v1(archive)
    assert loaded_proj.loaded is True


def test_dashboard_autobind_after_explicit_bundle_export(tmp_path: Path) -> None:
    from src.webui.market_dashboard_landscape_producer_binding_v2 import bind_market_universe_slots
    from src.webui.market_dashboard_landscape_v2.availability import Availability

    bundle = _persist_step29m_bundle(tmp_path)
    archive = tmp_path / "archive"
    export_economic_summary_to_archive_sibling_from_explicit_bundle_v1(
        archive_root=archive,
        economic_viability_evidence_bundle_path=bundle,
    )
    ts_iso = "2026-09-21T12:00:00Z"
    ts = datetime(2026, 9, 21, 12, 0, 0, tzinfo=timezone.utc)
    materialize_economic_summary_presentation_projection_v1(
        archive,
        generated_at=ts_iso,
        effective_at=ts_iso,
    )
    slots = bind_market_universe_slots(archive_root=archive, generated_at=ts)
    eco_slot = slots["economic_summary"]
    assert eco_slot.availability in (Availability.AVAILABLE, Availability.STALE)
    assert eco_slot.economic_viability_status == "RESEARCH_ONLY"


def test_missing_bundle_path_fail_closed(tmp_path: Path) -> None:
    archive = tmp_path / "archive"
    out = export_economic_summary_to_archive_sibling_from_explicit_bundle_v1(
        archive_root=archive,
        economic_viability_evidence_bundle_path=None,
    )
    assert out.exported is False
    assert out.error_code == ERROR_BUNDLE_PATH_REQUIRED
    assert not (archive / TARGET_RELATIVE_PATH).exists()


def test_family_export_skips_without_explicit_bundle_reference(tmp_path: Path) -> None:
    state_roots = materialize_state_root_layout_v1(runtime_root=tmp_path / "runtime")
    archive_root = tmp_path / "archive"
    readmodels = archive_root / "readmodels"
    readmodels.mkdir(parents=True)
    archive = ArchiveBindingV1(
        archive_root=str(archive_root.resolve()),
        resolution_precedence="test",
        readmodels_dir=str(readmodels.resolve()),
        dynamic_scope_sibling_path=str((readmodels / "dynamic_scope_state_v1.json").resolve()),
        canonical_decision_sibling_path=str(
            (readmodels / "canonical_trading_decision_evidence.v1.json").resolve()
        ),
        double_play_sibling_path=str(
            (readmodels / "double_play_dashboard_display.v1.json").resolve()
        ),
        regime_bull_bear_switch_sibling_path=str(
            (readmodels / "regime_bull_bear_switch.v1.json").resolve()
        ),
        writable=True,
    )
    families = export_families_after_runtime_commit_v1(
        state_roots=state_roots,
        archive=archive,
        cycle_id="cycle-eco-0",
        cycle_index=0,
        dynamic_scope_persisted=False,
        evidence_payload=None,
        generated_at="2026-09-21T12:00:00Z",
        economic_viability_evidence_bundle_path=None,
    )
    eco = families["economic_summary"]
    assert eco.exported is False
    assert eco.exportable is False
    assert not (archive_root / SOURCE_FIELDS_RELATIVE_PATH).exists()


def test_invalid_manifest_fail_closed(tmp_path: Path) -> None:
    bundle = _persist_step29m_bundle(tmp_path)
    artifact = bundle / ev.ARTIFACT_FILENAME
    payload = json.loads(artifact.read_text(encoding="utf-8"))
    payload["manifest_digest"] = "0" * 64
    artifact.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")
    fields, errors = build_economic_summary_sibling_payload_from_explicit_bundle_v1(
        economic_viability_evidence_bundle_path=bundle,
    )
    assert fields is None
    assert ERROR_MANIFEST_OR_CONTRACT_FAIL in errors


def test_neighbor_bundle_not_discovered(tmp_path: Path) -> None:
    root = tmp_path / "bundles"
    root.mkdir()
    bundle_a = _persist_step29m_bundle(root, suffix="a", cfg=_cfg(fee_bps=10.0))
    bundle_b = _persist_step29m_bundle(root, suffix="b", cfg=_cfg(fee_bps=11.0))
    loaded_b = ev.load_economic_viability_evidence_bundle_v1(bundle_b)
    assert (
        loaded_b.evidence.manifest_digest
        != ev.load_economic_viability_evidence_bundle_v1(bundle_a).evidence.manifest_digest
    )

    archive = tmp_path / "archive"
    export_economic_summary_to_archive_sibling_from_explicit_bundle_v1(
        archive_root=archive,
        economic_viability_evidence_bundle_path=bundle_a,
    )
    sibling = json.loads((archive / SOURCE_FIELDS_RELATIVE_PATH).read_text(encoding="utf-8"))
    assert (
        sibling["manifest_digest"]
        == ev.load_economic_viability_evidence_bundle_v1(bundle_a).evidence.manifest_digest
    )
    assert sibling["manifest_digest"] != loaded_b.evidence.manifest_digest


def test_cross_sectional_shaped_artifact_rejected(tmp_path: Path) -> None:
    bundle = _persist_step29m_bundle(tmp_path, suffix="xs")
    artifact = bundle / ev.ARTIFACT_FILENAME
    cross = {
        "schema_version": "economic_viability_evidence_cross_sectional_v2",
        "strategy_id": "cross_sectional_relative_strength",
        "strategy_version": "v0",
        "net_return": 0.1,
    }
    artifact.write_text(json.dumps(cross), encoding="utf-8")
    fields, errors = build_economic_summary_sibling_payload_from_explicit_bundle_v1(
        economic_viability_evidence_bundle_path=bundle,
    )
    assert fields is None
    assert ERROR_CROSS_SECTIONAL_SHAPE in errors


def test_producer_binding_forbids_economic_discovery() -> None:
    text = PRODUCER_BINDING.read_text(encoding="utf-8")
    assert "Never discover/select EconomicViabilityEvidenceV1" in text
    assert "AUTHORITY_EFFECT=NONE" in text or "authority_effect" in text


def test_d4_4_witness_not_started_in_repo_tree() -> None:
    """Witness G: no D4.4 safety archive witness tree added by this capability slice."""
    assert not list(Path("docs/ops/market_dashboard").glob("d4_4_*"))
