"""CURRENT-WP-04: standing admission refresh + endgame done gate."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.ops.current_wp03_live_scoped_observation_golden_convergence_v1.convergence_proof_v1 import (
    prove_wp03_golden_convergence_v1,
)
from src.ops.current_wp04_standing_pre_external_admission_endgame_done_gate_v1.ci_snapshot_v1 import (
    load_ci_admission_snapshot_v1,
)
from src.ops.current_wp04_standing_pre_external_admission_endgame_done_gate_v1.constants_v1 import (
    BLUEPRINT_DEFINITION_SOURCE,
    REQUIRED_CI_CONFIG_RELATIVE,
)
from src.ops.current_wp04_standing_pre_external_admission_endgame_done_gate_v1.evidence_v1 import (
    write_current_wp04_closure_evidence_v1,
)
from src.ops.current_wp04_standing_pre_external_admission_endgame_done_gate_v1.package_proof_v1 import (
    prove_current_wp04_package_v1,
    write_standing_pre_external_autonomy_admission_evidence_v1,
)
from src.ops.current_wp04_standing_pre_external_admission_endgame_done_gate_v1.standing_autonomy_record_v1 import (
    StandingPreExternalAutonomyRecordV1,
    write_standing_pre_external_autonomy_record_v1,
)
from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    EXTERNAL_EFFECT_AUTHORIZED,
    POST_ALLOWED,
    REAL_VENUE_POST_ALLOWED,
)
from src.ops.governed_futures_universe_producer_v1.constants_v1 import (
    SNAPSHOT_FILENAME as UNIVERSE_SNAPSHOT_FILENAME,
)
from src.ops.hard_facts_system_closure_v1.authority_proof_v1 import (
    prove_hard_facts_authority_invariants_v1,
)
from src.ops.n1_whole_system_hard_facts_integration_wp_v1.backlog_matrix_v1 import (
    close_row_v1,
    initial_backlog_rows_v1,
    summarize_backlog_v1,
)
from src.ops.n1_whole_system_hard_facts_integration_wp_v1.constants_v1 import BACKLOG_TOTAL
from src.ops.n1_whole_system_hard_facts_integration_wp_v1.public_real_md_cap22_n1_chain_v1 import (
    prove_public_real_md_to_cap22_n1_chain_v1,
)
from tests.ops._wp03_supervisor_golden_harness_v1 import (
    run_hold_supervisor_v1,
    run_natural_long_supervisor_v1,
    run_natural_short_supervisor_v1,
    run_two_epoch_supervisor_v1,
)
from tests.ops.test_current_mf_n5_boundary_occupied_lane_cap24_n1_bind_join_v1 import (
    _five_rows,
    _held_writer,
    _persist_universe_and_ranking,
)
from tests.ops.test_n1_standing_pre_external_runtime_supervisor_v1 import (
    OWNER_GO_BASELINE_SHA,
    REPO,
)
from tests.ops._productive_economic_md_inject_helpers_v1 import (
    injected_economic_md_source_for_venue_native_ids_v1,
)

REQUIREMENT_ADJUDICATION = {
    "EDG-034": "STILL_REQUIRED→standing admission refresh with WP-03 scoped semantics",
    "EDG-042": "STILL_REQUIRED→CI admission snapshot at WP-04",
    "BLK-10": "CLOSED_CURRENT→via WP-03",
    "BLK-11": "CLOSED_CURRENT→via WP-03",
    "§12_DONE_GATE": "STILL_REQUIRED→mechanical gate + CI snapshot",
    "PRE_EXTERNAL_AUTONOMY_ADMISSION": "PARTIAL_CURRENT→#6983 inject; WP-04 runtime rebind",
}


def _public_chain_proof_v1(tmp_path: Path):
    tmp_path.mkdir(parents=True, exist_ok=True)
    chain = _persist_universe_and_ranking(tmp_path, _five_rows())
    writer = _held_writer(tmp_path / "topo")
    md = injected_economic_md_source_for_venue_native_ids_v1(["ETH-USDT-SWAP"])
    universe = json.loads(
        (chain["universe_root"] / UNIVERSE_SNAPSHOT_FILENAME).read_text(encoding="utf-8")
    )
    public_proof, _ = prove_public_real_md_to_cap22_n1_chain_v1(
        universe_snapshot=universe,
        public_md_source=md,
        productive_ranking_snapshot=chain["ranking"],
        membership_store_root=tmp_path / "mca",
        topology_state_root_base=tmp_path / "topo",
        lane_assignment_writer=writer,
    )
    return public_proof


def _wp03_proof_v1(tmp_path: Path):
    return prove_wp03_golden_convergence_v1(
        long_result=run_natural_long_supervisor_v1(tmp_path / "long"),
        short_result=run_natural_short_supervisor_v1(tmp_path / "short"),
        hold_result=run_hold_supervisor_v1(tmp_path / "hold"),
        two_epoch_result=run_two_epoch_supervisor_v1(tmp_path / "two_epoch"),
    )


def test_safety_pins_and_authority_boundary_unchanged() -> None:
    assert POST_ALLOWED is False
    assert EXTERNAL_EFFECT_AUTHORIZED is False
    assert REAL_VENUE_POST_ALLOWED is False
    assert prove_hard_facts_authority_invariants_v1().ok is True


def test_ci_admission_snapshot_structural() -> None:
    snap = load_ci_admission_snapshot_v1(
        repo_root=REPO,
        config_relative=REQUIRED_CI_CONFIG_RELATIVE,
    )
    assert snap.recorded is True
    assert len(snap.effective_required_contexts) >= 10
    assert snap.all_required_ci_green_at_admission is False


def test_wp04_standing_admission_and_mechanical_done_gate(tmp_path: Path) -> None:
    wp03 = _wp03_proof_v1(tmp_path)
    assert wp03.ok is True
    public_proof = _public_chain_proof_v1(tmp_path / "pub_chain")
    rows = initial_backlog_rows_v1()
    for row_id in rows:
        close_row_v1(
            rows,
            backlog_id=row_id,
            changed_files=(
                "src/ops/current_wp04_standing_pre_external_admission_endgame_done_gate_v1/",
            ),
            tests=(
                "tests/ops/test_current_wp04_standing_pre_external_admission_endgame_done_gate_v1.py",
            ),
            notes="CURRENT-WP-04 standing admission",
        )
    summary = summarize_backlog_v1(rows)
    assert summary["BACKLOG_CLOSED"] == BACKLOG_TOTAL
    pkg = prove_current_wp04_package_v1(
        repo_root=REPO,
        public_chain=public_proof,
        public_store_root=tmp_path / "pub_store",
        private_store_root=tmp_path / "priv_store",
        wp03=wp03,
        reference_supervisor_run=run_two_epoch_supervisor_v1(tmp_path / "ref_supervisor"),
        tested_code_sha=OWNER_GO_BASELINE_SHA,
        backlog_matrix=summary,
    )
    assert pkg.admission.ok is True
    assert pkg.admission.post_count == 0
    assert pkg.done_gate.mechanical_ok is True
    assert pkg.done_gate.ok is False
    assert pkg.done_gate.ALL_REQUIRED_CI_GREEN is False
    assert pkg.ok is True


def test_fail_closed_admission_rejects_missing_wp03(tmp_path: Path) -> None:
    wp03 = _wp03_proof_v1(tmp_path)
    public_proof = _public_chain_proof_v1(tmp_path / "pub_chain")
    from dataclasses import replace

    broken = replace(wp03, ok=False)
    rows = summarize_backlog_v1(initial_backlog_rows_v1())
    pkg = prove_current_wp04_package_v1(
        repo_root=REPO,
        public_chain=public_proof,
        public_store_root=tmp_path / "pub_store",
        private_store_root=tmp_path / "priv_store",
        wp03=broken,
        reference_supervisor_run=run_two_epoch_supervisor_v1(tmp_path / "ref"),
        tested_code_sha=OWNER_GO_BASELINE_SHA,
        backlog_matrix=rows,
    )
    assert pkg.ok is False
    assert pkg.done_gate.mechanical_ok is False


def test_standing_autonomy_record_no_post_activation(tmp_path: Path) -> None:
    record = StandingPreExternalAutonomyRecordV1.from_admission_flags_v1(
        tested_code_sha=OWNER_GO_BASELINE_SHA,
        mechanical_gate_ok=True,
        post_allowed=False,
        external_effect_authorized=False,
        real_venue_post_allowed=False,
    )
    path = write_standing_pre_external_autonomy_record_v1(out_dir=tmp_path, record=record)
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["continuous_run_authorized_pin_flipped"] is False
    assert payload["standing_runtime_admitted"] is True


def test_write_closure_and_admission_evidence_shapes(tmp_path: Path) -> None:
    wp03 = _wp03_proof_v1(tmp_path)
    public_proof = _public_chain_proof_v1(tmp_path / "pub_chain")
    summary = summarize_backlog_v1(initial_backlog_rows_v1())
    pkg = prove_current_wp04_package_v1(
        repo_root=REPO,
        public_chain=public_proof,
        public_store_root=tmp_path / "pub_store",
        private_store_root=tmp_path / "priv_store",
        wp03=wp03,
        reference_supervisor_run=run_two_epoch_supervisor_v1(tmp_path / "ref"),
        tested_code_sha=OWNER_GO_BASELINE_SHA,
        backlog_matrix=summary,
    )
    adm_path = write_standing_pre_external_autonomy_admission_evidence_v1(
        repo_root=tmp_path,
        payload=pkg.admission_payload,
    )
    assert "STANDING_PRE_EXTERNAL_AUTONOMY_ADMISSION_V1" in adm_path.name
    closure = write_current_wp04_closure_evidence_v1(
        repo_root=tmp_path,
        baseline_sha=OWNER_GO_BASELINE_SHA,
        tested_code_sha=OWNER_GO_BASELINE_SHA,
        admission=pkg.admission,
        done_gate=pkg.done_gate,
        requirement_adjudication={
            "source": BLUEPRINT_DEFINITION_SOURCE,
            "adjudication": REQUIREMENT_ADJUDICATION,
        },
        changed_files=(
            "src/ops/current_wp04_standing_pre_external_admission_endgame_done_gate_v1/",
        ),
        tests_executed=(
            "tests/ops/test_current_wp04_standing_pre_external_admission_endgame_done_gate_v1.py",
        ),
        residuals=("ALL_REQUIRED_CI_GREEN deferred to GitHub required checks on PR",),
    )
    text = closure.read_text(encoding="utf-8")
    assert "WP05_NOT_STARTED" in text
    assert "MECHANICAL_ENDGAME_GATE_OK" in text


def test_wp03_wp02_wp01_regression_import_smoke() -> None:
    from tests.ops import test_current_wp03_live_scoped_observation_golden_convergence_v1 as wp03
    from tests.ops import test_current_wp02_default_productive_universe_handoff_v1 as wp02
    from tests.ops import test_n1_standing_pre_external_runtime_supervisor_v1 as wp01

    assert wp03.test_safety_pins_unchanged is not None
    assert wp02.test_synthetic_ranking_rejected is not None
    assert wp01.test_authority_boundary_and_pins is not None
