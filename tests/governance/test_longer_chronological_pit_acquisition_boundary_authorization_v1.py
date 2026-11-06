"""Boundary authorization for longer chronological PIT acquisition scaffold v1."""

from __future__ import annotations

from pathlib import Path

from src.governance.economic_diagnostic_optimization_boundary_v0 import (
    build_boundary_report,
    load_technical_wiring_authorization,
    validate_technical_wiring_authorization,
)

REPO_ROOT = Path(__file__).resolve().parents[2]

AUTHORIZED_PIT_ACQUISITION_FIXTURE = [
    "src/research/longer_chronological_pit_acquisition_v1/__init__.py",
    "src/research/longer_chronological_pit_acquisition_v1/history_depth_probe.py",
    "src/research/longer_chronological_pit_acquisition_v1/sealed_lifecycle_v1.py",
    "src/research/longer_chronological_pit_acquisition_v1/public_lifecycle_acquisition_v1.py",
    "src/research/longer_chronological_pit_acquisition_v1/cli.py",
    "tests/research/test_longer_chronological_pit_acquisition_scaffold_v1.py",
    "tests/research/test_longer_chronological_pit_okx_history_depth_probe_v1.py",
    "tests/research/test_longer_chronological_pit_sealed_lifecycle_acquisition_v1.py",
    "config/research/longer_chronological_pit_acquisition_chrono_3y_v1.json",
    "config/research/longer_chronological_pit_sealed_lifecycle_long_panel_v1.json",
    "config/governance/economic_diagnostic_optimization_boundary_canonical_owner_map_v0.json",
    "config/governance/technical_canonical_wiring_authorization_v1.json",
]


def test_authorized_pit_acquisition_scaffold_paths_are_admissible() -> None:
    report = build_boundary_report(
        AUTHORIZED_PIT_ACQUISITION_FIXTURE,
        repo_root=REPO_ROOT,
    )
    assert report.admissible is True
    assert report.fail_closed is False
    assert report.impact_unknown is False
    assert "LONGER_CHRONOLOGICAL_PIT_PUBLIC_HISTORY_ACQUISITION_SCAFFOLD_AND_DEPTH_PROBE_V1" in (
        report.allowed_surface_classification
    )
    assert report.master_v2_changed is False
    assert report.double_play_changed is False
    assert report.risk_sizing_changed is False
    assert report.promotion_runtime_authority_changed is False


def test_neighboring_unauthorized_research_mutation_remains_fail_closed() -> None:
    report = build_boundary_report(
        [
            "src/research/longer_chronological_pit_acquisition_v1/cli.py",
            "src/research/some_unregistered_neighbor_module_v0.py",
        ],
        repo_root=REPO_ROOT,
    )
    assert report.admissible is False
    assert report.fail_closed is True
    assert report.impact_unknown is True
    assert "IMPACT_UNKNOWN_MUTATION_BLOCKED" in report.reason_codes


def test_technical_wiring_auth_lists_exact_pit_acquisition_files() -> None:
    auth = load_technical_wiring_authorization(REPO_ROOT)
    assert auth is not None
    valid, reasons = validate_technical_wiring_authorization(auth)
    assert valid is True
    assert reasons == ()
    allowed = set(auth["allowed_paths"])
    assert "src/research/longer_chronological_pit_acquisition_v1/history_depth_probe.py" in allowed
    assert "src/research/longer_chronological_pit_acquisition_v1/sealed_lifecycle_v1.py" in allowed
    assert "tests/research/test_longer_chronological_pit_okx_history_depth_probe_v1.py" in allowed
    assert (
        "tests/research/test_longer_chronological_pit_sealed_lifecycle_acquisition_v1.py" in allowed
    )
    assert "config/research/longer_chronological_pit_sealed_lifecycle_long_panel_v1.json" in allowed
    assert (
        "TECHNICAL_LONGER_CHRONOLOGICAL_PIT_PUBLIC_HISTORY_ACQUISITION_WIRING"
        in auth["allowed_surface_classes"]
    )
    # No broad directory grant
    assert "src/research/" not in allowed
    assert "src/trading/master_v2/" not in allowed
