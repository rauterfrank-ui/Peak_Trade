"""Contract tests for canonical offline linear diagnostics promotion binding reconciliation v0."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

from src.governance.canonical_offline_linear_diagnostics_promotion_binding_completion_reconciliation_v0 import (
    AUTHORITATIVE_TRUTH,
    CLOSEOUT_SECTION_PREFIX,
    GO_TOKEN,
    PR5185_CLOSEOUT_DIR,
    PR5186_CLOSEOUT_DIR,
    PR5187_CLOSEOUT_DIR,
    PR_CHAIN,
    SCOPE,
    build_closeout_binding_map_v0,
    build_pr_chain_json_v0,
    deterministic_materialization_digest,
    reject_contradictory_pass_when_gate_false,
    reject_invalid_manifest_status,
    reject_missing_closeout_reference,
    validate_authoritative_registry_fields,
    validate_closeout_section_fields,
    validate_pr_chain_order,
    verify_source_derivation_manifest,
)
from src.governance.runbook_progress_registry_v1 import (
    duplicate_current_owner_fields,
    load_runbook_progress_registry_v1,
)
from src.research.linear_evidence.offline_productive_linear_diagnostics_promotion_economic_gate_consumer_binding_v0 import (
    BLOCKING_REASON_BLOCKED_SOURCE_DIAGNOSTICS_PRESENT,
    materialize_promotion_economic_gate_consumer_binding_v0,
)
from tests.ops.runbook_progress_registry_contract_helpers_v1 import (
    authoritative_field_value,
    read_registry,
)
from scripts.ops.primary_evidence_retention_v0 import verify_manifest_sha256
from src.research.linear_evidence.offline_productive_linear_diagnostics_support_bundle_v0 import (
    DEFAULT_SOURCE_BUNDLE_SPECS,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
MATERIALIZER = REPO_ROOT / (
    "scripts/ops/materialize_canonical_offline_linear_diagnostics_and_promotion_binding_"
    "completion_reconciliation_v0.py"
)


def _field_value(text: str, field: str) -> str:
    match = re.search(rf"\| `{re.escape(field)}` \| `([^`]*)` \|", text)
    assert match, f"missing registry field: {field}"
    return match.group(1)


def _closeout_section(text: str) -> str:
    start = text.index(CLOSEOUT_SECTION_PREFIX)
    end = text.index("\n---\n\n## PR #4629 Evidence-Drift", start)
    return text[start:end]


def _archive_available() -> bool:
    return all(
        path.is_dir() for path in (PR5185_CLOSEOUT_DIR, PR5186_CLOSEOUT_DIR, PR5187_CLOSEOUT_DIR)
    )


@pytest.fixture(scope="module")
def closeout_records():
    if not _archive_available():
        pytest.skip("PR5185-5187 closeout archives unavailable")
    records = build_closeout_binding_map_v0(verify_manifest_sha256)
    validate_pr_chain_order(records)
    return records


class TestAuthoritativeRegistryBinding:
    def test_pr5185_5186_5187_closeouts_registered(self) -> None:
        assert authoritative_field_value("PR5185_CLOSEOUT_REGISTERED") == "true"
        assert authoritative_field_value("PR5186_CLOSEOUT_REGISTERED") == "true"
        assert authoritative_field_value("PR5187_CLOSEOUT_REGISTERED") == "true"
        assert authoritative_field_value("PR5185_MERGE_CLOSEOUT_BOUND") == "true"
        assert authoritative_field_value("PR5186_MERGE_CLOSEOUT_BOUND") == "true"
        assert authoritative_field_value("PR5187_MERGE_CLOSEOUT_BOUND") == "true"

    def test_authoritative_truth_fields_bound(self) -> None:
        observed = validate_authoritative_registry_fields()
        assert observed == AUTHORITATIVE_TRUTH

    def test_step_29l2_complete_and_productively_bound(self) -> None:
        assert authoritative_field_value("STEP_29L_2_STATUS") == ("COMPLETE_AND_PRODUCTIVELY_BOUND")
        assert authoritative_field_value("LINEAR_DIAGNOSTIC_CLASS_COUNT") == "5"

    def test_step_29m_remains_fail_closed(self) -> None:
        assert authoritative_field_value("STEP_29M_STATUS") == "COMPLETE_FAIL_CLOSED"
        assert authoritative_field_value("STEP29M_FLEET_STATUS") == (
            "TERMINAL_FAIL_RESEARCH_GENERATION_CLOSED"
        )
        assert authoritative_field_value("ECONOMIC_VALIDITY_OFFLINE_GATE_PASS") == "false"

    def test_step_29n_productively_bound_promotion_blocked(self) -> None:
        assert authoritative_field_value("STEP_29N_STATUS") == ("COMPLETE_AND_PRODUCTIVELY_BOUND")
        assert authoritative_field_value("PROMOTION_ECONOMIC_GATE_STATUS") == "BLOCKED"
        assert authoritative_field_value("PROMOTION_BLOCKING_REASON") == (
            BLOCKING_REASON_BLOCKED_SOURCE_DIAGNOSTICS_PRESENT
        )

    def test_step_29r_blocked_runtime_rewire_inadmissible(self) -> None:
        assert authoritative_field_value("STEP_29R_STATUS") == "COMPLETE_FAIL_CLOSED"
        assert authoritative_field_value("RUNBOOK_STEP_29R_STATUS") == "BLOCKED"
        assert authoritative_field_value("RUNTIME_REWIRE_ADMISSIBLE") == "false"

    def test_policy_blocks_preserved(self) -> None:
        assert authoritative_field_value("UNCHANGED_RETRY_BLOCKED") == "true"
        assert authoritative_field_value("POLICY_RESCUE_ALLOWED") == "false"
        assert authoritative_field_value("NO_IMPLEMENTATION_GAP") == "true"
        assert authoritative_field_value("REMAINING_BLOCK_CLASS") == "POLICY_BLOCK_ONLY"

    def test_no_runtime_or_authority_effect(self) -> None:
        section = _closeout_section(read_registry())
        assert _field_value(section, "RUNTIME_EFFECT") == "NONE"
        assert _field_value(section, "AUTHORITY_EFFECT") == "NONE"


class TestCloseoutSection:
    def test_closeout_section_records_chain_without_evidence_mutation(self) -> None:
        section = _closeout_section(read_registry())
        validate_closeout_section_fields(read_registry())
        assert _field_value(section, "STATUS") == "COMPLETE"
        assert _field_value(section, "SCOPE_CLASSIFICATION") == SCOPE
        assert _field_value(section, "GO_TOKEN") == GO_TOKEN
        assert _field_value(section, "HISTORICAL_NEGATIVE_EVIDENCE_MUTATED") == "false"


class TestPrChainBinding:
    def test_pr_chain_order_and_merge_commits(self, closeout_records) -> None:
        chain = build_pr_chain_json_v0(closeout_records)
        assert [item["pr"] for item in chain["chain"]] == ["5185", "5186", "5187"]
        for expected, actual in zip(PR_CHAIN, chain["chain"]):
            assert actual["merge_commit"] == expected["merge_commit"]
            assert actual["manifest_verify_rc"] == 0

    def test_productive_promotion_consumer_remains_blocked(self, closeout_records) -> None:
        _, _, promotion_result = materialize_promotion_economic_gate_consumer_binding_v0(
            source_specs=DEFAULT_SOURCE_BUNDLE_SPECS,
            verify_fn=verify_manifest_sha256,
            repo_root=REPO_ROOT,
        )
        payload = promotion_result.to_dict()
        assert payload["promotion_economic_gate_status"] == "BLOCKED"
        assert BLOCKING_REASON_BLOCKED_SOURCE_DIAGNOSTICS_PRESENT in payload["blocking_reason"]
        assert payload["economic_evaluation_executed"] is False
        assert payload["promotion_pass_created"] is False


class TestDeterministicMaterialization:
    def test_repeated_digest_identical(self, closeout_records) -> None:
        payload = build_pr_chain_json_v0(closeout_records)
        assert deterministic_materialization_digest(
            payload
        ) == deterministic_materialization_digest(payload)

    def test_materializer_produces_manifest_verified_bundle(self, tmp_path: Path) -> None:
        if not _archive_available():
            pytest.skip("PR5185-5187 closeout archives unavailable")
        out_dir = tmp_path / "evidence"
        proc = subprocess.run(
            [sys.executable, str(MATERIALIZER), "--out", str(out_dir), "--skip-focused-tests"],
            cwd=str(REPO_ROOT),
            text=True,
            capture_output=True,
            env={"PYTHONPATH": f"{REPO_ROOT / 'src'}:{REPO_ROOT}"},
        )
        assert proc.returncode == 0, proc.stdout + proc.stderr
        ok, _msg = verify_manifest_sha256(out_dir)
        assert ok is True


class TestFailClosedGuards:
    def test_missing_closeout_reference_rejected(self) -> None:
        with pytest.raises(Exception):
            reject_missing_closeout_reference(None)

    def test_invalid_manifest_status_rejected(self) -> None:
        with pytest.raises(Exception):
            reject_invalid_manifest_status(1)

    def test_contradictory_pass_with_gate_false_rejected(self) -> None:
        with pytest.raises(Exception):
            reject_contradictory_pass_when_gate_false(False, "PASS")

    def test_source_derivation_manifest_verifies(self) -> None:
        if not _archive_available():
            pytest.skip("derivation/closeout archives unavailable")
        assert verify_source_derivation_manifest(verify_fn=verify_manifest_sha256) == 0


class TestRegistryResolverIntegrity:
    def test_no_duplicate_conflicting_authoritative_current_owners(self) -> None:
        registry = load_runbook_progress_registry_v1()
        ambiguous = duplicate_current_owner_fields(
            registry,
            fields=(
                "PROMOTION_ECONOMIC_GATE_STATUS",
                "ECONOMIC_VALIDITY_OFFLINE_GATE_PASS",
                "STEP_29L_2_STATUS",
                "NO_IMPLEMENTATION_GAP",
            ),
        )
        assert ambiguous == {}

    def test_closeout_binding_map_json_roundtrip(self, closeout_records) -> None:
        payload = build_pr_chain_json_v0(closeout_records)
        roundtrip = json.loads(json.dumps(payload, sort_keys=True))
        assert roundtrip == payload
