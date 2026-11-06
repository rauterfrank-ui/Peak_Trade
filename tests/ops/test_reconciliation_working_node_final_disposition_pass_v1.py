"""WORKING_NODE_FINAL_DISPOSITION_PASS_V1 contracts. Additive. RCN census frozen."""

from __future__ import annotations

from pathlib import Path

import yaml

from scripts.ops.system_atlas_v1.reconciliation_v1 import (
    load_reconciliation_v1,
    validate_reconciliation_v1,
)
from scripts.ops.system_atlas_v1.working_node_final_disposition_pass_v1_records import (
    BOUND_SHA,
    EXPECTED_ACCEPTED,
    EXPECTED_ADAPT,
    EXPECTED_CHANGED,
    EXPECTED_COUNT,
    EXPECTED_COVERED,
    EXPECTED_HVBI,
    EXPECTED_REJECT,
    EXPECTED_RETAIN,
    EXPECTED_SAFETY_CRITICAL,
    IDENTITY_UNIVERSE,
    OWNER_GO,
    OWNER_TO_TAXONOMY,
    OVERRIDE_CHANGE_REASONS,
    PASS_ID,
    working_node_final_disposition_records,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
RECON = REPO_ROOT / "docs" / "system_atlas" / "reconciliation"
PASS_ROOT = RECON / "working_nodes"
FROZEN_DIRS = (
    "understand",
    "evaluate",
    "adjudicate",
    "evidence_resolution",
    "reevaluate",
)


def _status() -> dict:
    return yaml.safe_load((PASS_ROOT / "pass_v1_status.yaml").read_text(encoding="utf-8"))


def _index() -> dict:
    return yaml.safe_load((PASS_ROOT / "index.yaml").read_text(encoding="utf-8"))


def test_status_invariants() -> None:
    status = _status()
    assert status["pass_id"] == PASS_ID
    assert status["owner_go"] == OWNER_GO
    assert status["bound_against_sha"] == BOUND_SHA
    assert status["identity_universe"] == IDENTITY_UNIVERSE
    assert status["atlas_authority"] == "NONE"
    assert status["reconciliation_authority"] == "NONE"
    assert int(status["working_node_record_count"]) == EXPECTED_COUNT
    assert int(status["retain_as_is_count"]) == EXPECTED_RETAIN
    assert int(status["adapt_and_reintegrate_count"]) == EXPECTED_ADAPT
    assert int(status["capability_already_covered_count"]) == EXPECTED_COVERED
    assert int(status["historically_valid_but_incompatible_count"]) == EXPECTED_HVBI
    assert int(status["reject_for_current_system_count"]) == EXPECTED_REJECT
    assert int(status["proposal_accepted_count"]) == EXPECTED_ACCEPTED
    assert int(status["proposal_changed_count"]) == EXPECTED_CHANGED
    assert int(status["safety_critical_count"]) == EXPECTED_SAFETY_CRITICAL
    assert int(status["remaining_open_record_count"]) == 0
    assert int(status["rcn_ledger_record_count_unchanged"]) == 53
    assert status["rcn_ledger_mutated"] is False
    assert status["rcn_census_reopened"] is False
    assert status["reintegration_performed"] is False
    assert status["runtime_mutation_performed"] is False
    assert status["implementation_authorized"] is False
    assert status["integrate_or_disposition_execution_authorized"] is False
    assert status["final_dispositions_authorized"] is True
    assert status["integrate_or_disposition_started"] is False


def test_index_and_records_match_generated() -> None:
    index = _index()
    generated = working_node_final_disposition_records(repo_root=REPO_ROOT)
    assert int(index["row_count"]) == EXPECTED_COUNT
    assert len(index["rows"]) == EXPECTED_COUNT
    assert len(generated) == EXPECTED_COUNT
    files = sorted(p.name for p in (PASS_ROOT / "records").glob("WN-*.yaml"))
    assert len(files) == EXPECTED_COUNT
    index_ids = [row["working_node_id"] for row in index["rows"]]
    gen_ids = [row["working_node_id"] for row in generated]
    assert index_ids == gen_ids
    assert len(set(index_ids)) == EXPECTED_COUNT
    for row, expected in zip(index["rows"], generated, strict=True):
        path = PASS_ROOT / "records" / f"{row['working_node_id']}.yaml"
        persisted = yaml.safe_load(path.read_text(encoding="utf-8"))
        assert persisted["working_node_id"] == expected["working_node_id"]
        assert persisted["final_disposition"] == expected["final_disposition"]
        assert (
            persisted["final_disposition_owner_label"] == expected["final_disposition_owner_label"]
        )
        assert persisted["proposed_disposition"] == expected["proposed_disposition"]
        assert persisted["proposal_accepted"] is expected["proposal_accepted"]
        assert persisted["lifecycle_state"] == "DISPOSITION_DECIDED"
        assert persisted["implementation_authorized"] is False
        assert persisted["reintegration_performed"] is False
        owner_label = persisted["final_disposition_owner_label"]
        assert persisted["final_disposition"] == OWNER_TO_TAXONOMY[owner_label]


def test_four_owner_overrides() -> None:
    expected = {
        "WN-CORE-BACKUP-RECOVERY": "ADAPT_AND_REINTEGRATE",
        "WN-HIST-INFRA-BACKUP": "HISTORICALLY_VALID_BUT_INCOMPATIBLE",
        "WN-HIST-INFRA-MONITORING": "CAPABILITY_ALREADY_COVERED",
        "WN-HIST-REGIME-SEQUENCER": "CAPABILITY_ALREADY_COVERED",
    }
    for wn, disposition in expected.items():
        rec = yaml.safe_load((PASS_ROOT / "records" / f"{wn}.yaml").read_text(encoding="utf-8"))
        assert rec["proposal_accepted"] is False
        assert rec["final_disposition"] == disposition
        assert rec["change_reason"] == OVERRIDE_CHANGE_REASONS[wn]
        assert rec["lifecycle_state"] == "DISPOSITION_DECIDED"


def test_reject_has_positive_reason_and_is_not_deletion() -> None:
    rec = yaml.safe_load(
        (PASS_ROOT / "records" / "WN-EXECUTION-SIMPLE.yaml").read_text(encoding="utf-8")
    )
    assert rec["final_disposition"] == "REJECT_FOR_CURRENT_SYSTEM"
    assert rec["rejection_is_not_based_on_age_or_absence"] is True
    assert str(rec["positive_reason"]).strip()
    assert rec["lifecycle_state"] == "DISPOSITION_DECIDED"


def test_adapt_records_carry_boundaries_without_implementation() -> None:
    adapt_ids = [
        "WN-SRC-AUTONOMOUS",
        "WN-SRC-PORTFOLIO",
        "WN-LIVE-GATES",
        "WN-SRC-GOVERNANCE-PROMOTION",
        "WN-SRC-META-LEARNING-LOOP",
        "WN-LIVE-TESTNET-ORCH",
        "WN-SRC-SCHEDULER",
        "WN-SRC-REGIME",
        "WN-HIST-INFRA-HEALTH",
        "WN-HIST-INFRA-RESILIENCE",
        "WN-HIST-WEBUI-VISUAL-OPS",
        "WN-CORE-BACKUP-RECOVERY",
    ]
    for wn in adapt_ids:
        rec = yaml.safe_load((PASS_ROOT / "records" / f"{wn}.yaml").read_text(encoding="utf-8"))
        assert rec["final_disposition"] == "ADAPT_AND_REINTEGRATE"
        assert rec["implementation_authorized"] is False
        assert str(rec["preserve_capability"]).strip()
        assert str(rec["do_not_restore_or_preserve"]).strip()
        assert str(rec["target_current_architectural_home"]).strip()
        assert str(rec["adaptation_boundary"]).strip()


def test_rcn_ledger_and_frozen_snapshots_untouched() -> None:
    payload = load_reconciliation_v1(repo_root=REPO_ROOT)
    assert validate_reconciliation_v1(payload) == []
    ledger = payload["records"]["ledger.yaml"]
    assert int(ledger["ledger_record_count"]) == 53
    records = ledger["records"]
    assert len(records) == 53
    ids = {str((rec.get("identity") or {}).get("reconciliation_id") or "") for rec in records}
    assert ids == {f"RCN-{n:06d}" for n in range(1, 54)}
    for name in FROZEN_DIRS:
        assert (RECON / name).is_dir()
    schema = yaml.safe_load((RECON / "schema.yaml").read_text(encoding="utf-8"))
    assert schema["working_node_final_disposition_is_not_rcn_census"] is True
    assert schema["working_node_final_disposition_implementation_authorized"] is False
    gov = yaml.safe_load((RECON / "GOVERNANCE_V1.yaml").read_text(encoding="utf-8"))
    wn_pass = gov["working_node_final_disposition_pass"]
    assert wn_pass["does_not_mutate_rcn_ledger"] is True
    assert wn_pass["implementation_authorized"] is False
    assert wn_pass["is_not_fifth_sequence_step"] is True
