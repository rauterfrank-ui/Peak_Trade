"""BRANCH_RULESET_ENFORCEMENT_GOVERNANCE_V1 — regression contracts.

Uses sanitized synthetic evidence only. Never asserts by printing credentials.
"""

from __future__ import annotations

import contextlib
import copy
import json
from io import StringIO
from pathlib import Path

import pytest

import scripts.ci.check_branch_ruleset_enforcement_governance_v1 as gate


REPO_ROOT = Path(__file__).resolve().parents[2]
CONTRACT = REPO_ROOT / "config" / "ci" / "branch_ruleset_enforcement_contract_v1.json"
REQUIRED = REPO_ROOT / "config" / "ci" / "required_status_checks.json"
SPEC = REPO_ROOT / "docs" / "ops" / "specs" / "BRANCH_RULESET_ENFORCEMENT_GOVERNANCE_V1.md"
EVIDENCE_AFTER = (
    REPO_ROOT / "docs" / "ops" / "specs" / "branch_ruleset_enforcement_api_evidence_after_v1.json"
)
EVIDENCE_BEFORE = (
    REPO_ROOT / "docs" / "ops" / "specs" / "branch_ruleset_enforcement_api_evidence_before_v1.json"
)
SECURITY_NOTES = REPO_ROOT / "SECURITY_NOTES.md"
LINT_GATE = REPO_ROOT / ".github" / "workflows" / "lint_gate.yml"
VERIFIER = REPO_ROOT / "scripts" / "ci" / "check_branch_ruleset_enforcement_governance_v1.py"
SECRET_SPEC = (
    REPO_ROOT / "docs" / "ops" / "specs" / "SECRET_SCANNING_AND_PUSH_PROTECTION_GOVERNANCE_V1.md"
)
REDACTION_OWNER = REPO_ROOT / "scripts" / "security" / "secret_hygiene_redaction_v1.py"
CRED_SCANNER = REPO_ROOT / "scripts" / "ci" / "check_tracked_credential_hygiene_policy_v1.py"


def _required_contexts() -> list[str]:
    return gate.load_required_contexts(REQUIRED)


def _passing_evidence() -> dict:
    contexts = _required_contexts()
    return {
        "schema_version": gate.EVIDENCE_SCHEMA,
        "phase": "synthetic_pass",
        "repository": {
            "default_branch": "main",
            "allow_squash_merge": True,
            "allow_merge_commit": True,
            "allow_rebase_merge": True,
            "allow_auto_merge": True,
            "delete_branch_on_merge": True,
            "visibility": "public",
            "secret_scanning": "enabled",
            "secret_scanning_push_protection": "enabled",
        },
        "rulesets_summary": [
            {
                "id": 11192468,
                "name": "peak_trade",
                "enforcement": "active",
                "target": "branch",
            }
        ],
        "ruleset": {
            "id": 11192468,
            "name": "peak_trade",
            "target": "branch",
            "enforcement": "active",
            "conditions": {"ref_name": {"include": ["refs/heads/main"], "exclude": []}},
            "rules": [
                {"type": "deletion"},
                {"type": "non_fast_forward"},
                {
                    "type": "pull_request",
                    "parameters": {
                        "required_approving_review_count": 0,
                        "dismiss_stale_reviews_on_push": True,
                        "require_code_owner_review": False,
                        "require_last_push_approval": True,
                        "required_review_thread_resolution": True,
                        "allowed_merge_methods": ["merge", "rebase", "squash"],
                    },
                },
                {
                    "type": "required_status_checks",
                    "parameters": {
                        "strict_required_status_checks_policy": True,
                        "required_status_checks": [{"context": c} for c in contexts],
                    },
                },
            ],
            "bypass_actors": [],
            "current_user_can_bypass": "never",
        },
        "classic_branch_protection_main": {"_synthetic": True},
    }


def test_owners_and_spec_exist() -> None:
    assert CONTRACT.is_file()
    assert SPEC.is_file()
    assert VERIFIER.is_file()
    assert EVIDENCE_AFTER.is_file()
    assert EVIDENCE_BEFORE.is_file()
    assert REDACTION_OWNER.is_file()
    assert CRED_SCANNER.is_file()
    text = SPEC.read_text(encoding="utf-8")
    assert "BRANCH_RULESET_ENFORCEMENT_GOVERNANCE_V1" in text
    assert "config/ci/required_status_checks.json" in text
    assert "SECRET_SCANNING_AND_PUSH_PROTECTION_GOVERNANCE_V1" in text
    assert "secret_hygiene_redaction_v1" in text
    assert gate.CAPABILITY_ID == "BRANCH_RULESET_ENFORCEMENT_GOVERNANCE_V1"


def test_no_duplicate_required_check_or_redaction_truth() -> None:
    notes = SECURITY_NOTES.read_text(encoding="utf-8")
    assert "BRANCH_RULESET_ENFORCEMENT_GOVERNANCE_V1" in notes
    assert "required_status_checks.json" in notes
    secret = SECRET_SPEC.read_text(encoding="utf-8")
    assert "ENFORCED" in secret or "active" in secret.lower()


def test_active_enforced_ruleset_passes() -> None:
    contract = gate.load_contract(CONTRACT)
    result = gate.evaluate_evidence(_passing_evidence(), contract, _required_contexts())
    assert result["ok"] is True
    assert result["RULESET_ENFORCEMENT_STATUS"] == "ENFORCED"
    assert result["REQUIRED_CHECK_SET_MATCH"] is True
    assert result["FORCE_PUSH_ALLOWED"] is False
    assert result["BRANCH_DELETION_ALLOWED"] is False
    assert result["BROAD_BYPASS_ACTOR_COUNT"] == 0


@pytest.mark.parametrize(
    ("mutator", "needle"),
    [
        (
            lambda e: e["ruleset"].__setitem__("enforcement", "evaluate"),
            "enforcement_not_active",
        ),
        (
            lambda e: e.__setitem__("ruleset", {}),
            "enforcement_not_active",
        ),
        (
            lambda e: e["ruleset"]["conditions"]["ref_name"].__setitem__(
                "include", ["refs/heads/develop"]
            ),
            "target_ref_include_mismatch",
        ),
        (
            lambda e: e["ruleset"]["rules"].__setitem__(
                3,
                {
                    "type": "required_status_checks",
                    "parameters": {
                        "strict_required_status_checks_policy": True,
                        "required_status_checks": [{"context": "Lint Gate"}],
                    },
                },
            ),
            "missing_required_checks",
        ),
        (
            lambda e: e["ruleset"]["rules"].__setitem__(
                3,
                {
                    "type": "required_status_checks",
                    "parameters": {
                        "strict_required_status_checks_policy": True,
                        "required_status_checks": [{"context": c} for c in _required_contexts()]
                        + [{"context": "Renamed Legacy Gate"}],
                    },
                },
            ),
            "unexpected_required_checks",
        ),
        (
            lambda e: e["ruleset"].__setitem__(
                "bypass_actors", [{"actor_id": 1, "actor_type": "OrganizationAdmin"}]
            ),
            "broad_bypass_actors",
        ),
        (
            lambda e: e["ruleset"].__setitem__(
                "rules", [r for r in e["ruleset"]["rules"] if r.get("type") != "non_fast_forward"]
            ),
            "force_push_allowed",
        ),
        (
            lambda e: e["ruleset"].__setitem__(
                "rules", [r for r in e["ruleset"]["rules"] if r.get("type") != "deletion"]
            ),
            "branch_deletion_allowed",
        ),
    ],
)
def test_fail_closed_mutations(mutator, needle: str) -> None:
    evidence = _passing_evidence()
    mutator(evidence)
    contract = gate.load_contract(CONTRACT)
    result = gate.evaluate_evidence(evidence, contract, _required_contexts())
    assert result["ok"] is False
    assert result["RULESET_ENFORCEMENT_STATUS"] != "ENFORCED"
    assert any(needle in f for f in result["findings"]), result["findings"]


def test_malformed_partial_evidence_fails() -> None:
    contract = gate.load_contract(CONTRACT)
    with pytest.raises(gate.VerificationError):
        gate.evaluate_evidence(
            {"schema_version": "wrong", "ruleset": {}},
            contract,
            _required_contexts(),
        )
    bad = _passing_evidence()
    bad["ruleset"]["rules"] = [
        {"type": "required_status_checks", "parameters": {"required_status_checks": "nope"}}
    ]
    result = gate.evaluate_evidence(bad, contract, _required_contexts())
    assert result["ok"] is False


def test_deterministic_normalized_output(tmp_path: Path) -> None:
    evidence = _passing_evidence()
    path = tmp_path / "ev.json"
    path.write_text(json.dumps(evidence, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    buf1 = StringIO()
    buf2 = StringIO()
    with contextlib.redirect_stdout(buf1):
        rc1 = gate.main(["--evidence-json", str(path), "--json"])
    with contextlib.redirect_stdout(buf2):
        rc2 = gate.main(["--evidence-json", str(path), "--json"])
    assert rc1 == 0 and rc2 == 0
    assert buf1.getvalue() == buf2.getvalue()
    payload = json.loads(buf1.getvalue())
    assert payload["secret_value_exposed"] is False
    assert payload["ok"] is True


def test_secret_redaction_safety_refuses_credential_like_evidence(tmp_path: Path) -> None:
    path = tmp_path / "leaky.json"
    path.write_text(
        json.dumps(
            {"schema_version": gate.EVIDENCE_SCHEMA, "token": "Authorization: Bearer ghp_SYNTH"}
        ),
        encoding="utf-8",
    )
    buf = StringIO()
    with contextlib.redirect_stdout(buf):
        rc = gate.main(["--evidence-json", str(path), "--json"])
    assert rc == 2
    out = buf.getvalue()
    assert "ghp_SYNTH" not in out
    assert "Bearer ghp" not in out


def test_committed_after_evidence_passes_offline_verifier() -> None:
    buf = StringIO()
    with contextlib.redirect_stdout(buf):
        rc = gate.main(["--json"])
    assert rc == 0, buf.getvalue()
    payload = json.loads(buf.getvalue())
    assert payload["RULESET_ENFORCEMENT_STATUS"] == "ENFORCED"
    assert payload["REQUIRED_CHECK_SET_MATCH"] is True
    assert payload["FORCE_PUSH_ALLOWED"] is False
    assert payload["BRANCH_DELETION_ALLOWED"] is False
    assert payload["BROAD_BYPASS_ACTOR_COUNT"] == 0
    assert payload["secret_value_exposed"] is False
    assert payload["network_required"] is False


def test_before_evidence_is_not_enforced() -> None:
    before = json.loads(EVIDENCE_BEFORE.read_text(encoding="utf-8"))
    contract = gate.load_contract(CONTRACT)
    # before evidence may lack full rules; evaluate should fail closed
    result = gate.evaluate_evidence(before, contract, _required_contexts())
    assert result["ok"] is False
    assert result["RULESET_ENFORCEMENT_STATUS"] != "ENFORCED"


def test_lint_gate_wires_verifier_without_privilege_expansion() -> None:
    text = LINT_GATE.read_text(encoding="utf-8")
    assert "check_branch_ruleset_enforcement_governance_v1.py" in text
    assert "pull_request_target" not in text
    # Top-level permissions remain read-only.
    assert "permissions:" in text
    assert "contents: read" in text
    assert "contents: write" not in text


def test_evaluate_only_and_absent_coverage_explicit() -> None:
    contract = gate.load_contract(CONTRACT)
    evaluate = _passing_evidence()
    evaluate["ruleset"]["enforcement"] = "evaluate"
    r1 = gate.evaluate_evidence(evaluate, contract, _required_contexts())
    assert r1["ok"] is False
    absent = copy.deepcopy(_passing_evidence())
    absent["ruleset"] = {
        "id": 999,
        "name": "missing",
        "target": "branch",
        "enforcement": "disabled",
        "conditions": {"ref_name": {"include": [], "exclude": []}},
        "rules": [],
        "bypass_actors": [],
    }
    r2 = gate.evaluate_evidence(absent, contract, _required_contexts())
    assert r2["ok"] is False
