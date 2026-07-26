"""SECRET_SCANNING_AND_PUSH_PROTECTION_GOVERNANCE_V1 — regression contracts.

Synthetic fixtures only. Never assert by printing usable credentials.
"""

from __future__ import annotations

import contextlib
import json
import re
import subprocess
from io import StringIO
from pathlib import Path

import pytest

import scripts.ci.check_tracked_credential_hygiene_policy_v1 as policy_gate
import scripts.security.secret_hygiene_redaction_v1 as redaction


REPO_ROOT = Path(__file__).resolve().parents[2]
ALLOWLIST = REPO_ROOT / "docs" / "ops" / "specs" / "tracked_credential_like_allowlist_v1.json"
GOV_SPEC = (
    REPO_ROOT / "docs" / "ops" / "specs" / "SECRET_SCANNING_AND_PUSH_PROTECTION_GOVERNANCE_V1.md"
)
SECURITY_NOTES = REPO_ROOT / "SECURITY_NOTES.md"
LINT_GATE = REPO_ROOT / ".github" / "workflows" / "lint_gate.yml"
SCANNER = REPO_ROOT / "scripts" / "ci" / "check_tracked_credential_hygiene_policy_v1.py"
REDACTION_OWNER = REPO_ROOT / "scripts" / "security" / "secret_hygiene_redaction_v1.py"

SYN_API_KEY = "sk-SYNTHETICGOVFAKEOPENAISTYLEKEY0000001"
SYN_AWS_KEY = "AKIAFAKESYNTHGOV0001"
SYN_JWT = (
    "eyJhbGciOiJSYNTHETICGOVIn0.eyJzdWIiOiJzeW50aGV0aWMtZ292LWZha2UifQ."
    "SYNTHETICFAKESIGNATUREVALUEGOV0001"
)
SYN_PEM = "-----BEGIN PRIVATE KEY-----"
SYN_URL = "https://synth_gov_user:synth_gov_pass_NOT_REAL@example.test/v1"
SYN_AUTH = "Authorization: Bearer synth-gov-bearer-token-NOT-REAL-0001"
SYN_HIGH = 'api_key = "Ab9xQ2mK7pL4nR8sT1uV0wY3zC6dF5gH"'  # synthetic high-entropy assignment
ORDINARY = "mark_price = 101.25\nstatus = ok\nreason = NO_SIGNAL\n"


def test_governance_spec_and_owners_exist() -> None:
    assert GOV_SPEC.is_file()
    assert SCANNER.is_file()
    assert REDACTION_OWNER.is_file()
    assert ALLOWLIST.is_file()
    text = GOV_SPEC.read_text(encoding="utf-8")
    assert "HISTORY_SCAN_STATUS=MANUAL_BOUNDED" in text or "MANUAL_BOUNDED" in text
    assert "scripts/security/secret_hygiene_redaction_v1.py" in text
    assert policy_gate.HISTORY_SCAN_STATUS == "MANUAL_BOUNDED"
    assert policy_gate.CAPABILITY_ID == "SECRET_SCANNING_AND_PUSH_PROTECTION_GOVERNANCE_V1"


def test_single_scanner_and_redaction_owner() -> None:
    assert REDACTION_OWNER.is_file()
    scanner_hits = subprocess.check_output(
        ["git", "-C", str(REPO_ROOT), "ls-files", "--", "scripts/ci/*credential*"],
        text=True,
    ).splitlines()
    assert scanner_hits == ["scripts/ci/check_tracked_credential_hygiene_policy_v1.py"]
    redaction_hits = []
    needle = re.compile(r'CONTRACT_ID\s*=\s*"secret_hygiene_redaction_v1"')
    for rel in subprocess.check_output(
        ["git", "-C", str(REPO_ROOT), "ls-files", "-z", "--", "*.py"],
        text=False,
    ).split(b"\0"):
        if not rel:
            continue
        path = REPO_ROOT / rel.decode("utf-8")
        try:
            body = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        if needle.search(body):
            redaction_hits.append(rel.decode("utf-8"))
    assert redaction_hits == ["scripts/security/secret_hygiene_redaction_v1.py"]


def test_synthetic_secret_fixtures_detected_and_never_printed() -> None:
    allow = json.loads(ALLOWLIST.read_text(encoding="utf-8"))
    probe = "\n".join(
        [
            f"token={SYN_API_KEY}",
            f"aws={SYN_AWS_KEY}",
            f"jwt={SYN_JWT}",
            SYN_PEM,
            SYN_URL,
            SYN_AUTH,
            SYN_HIGH,
        ]
    )
    findings = policy_gate.scan_text("unallowlisted_gov_probe.txt", probe, allow)
    classes = {f.pattern_class for f in findings}
    assert "OPENAI_STYLE_KEY" in classes
    assert "AWS_ACCESS_KEY_ID" in classes
    assert "JWT_LIKE" in classes
    assert "PEM_PRIVATE_KEY" in classes
    assert "URL_USERINFO_CREDENTIAL" in classes
    assert "AUTHORIZATION_HEADER_OR_ASSIGNMENT" in classes
    assert "HIGH_ENTROPY_CREDENTIAL_ASSIGNMENT" in classes
    for finding in findings:
        assert finding.secret_value_exposed is False
        dumped = repr(finding)
        assert SYN_API_KEY not in dumped
        assert SYN_AWS_KEY not in dumped
        assert "synth_gov_pass_NOT_REAL" not in dumped


def test_scanner_output_uses_canonical_redaction_and_hides_raw() -> None:
    assert "secret_hygiene_redaction_v1" in SCANNER.read_text(encoding="utf-8")
    raw = f"boom Authorization: Bearer {SYN_API_KEY}"
    safe = policy_gate._safe_display(raw)
    assert SYN_API_KEY not in safe
    assert redaction.REDACTION_MARKER in safe or "REDACTED" in safe


def test_allowlisted_exact_entry_passes_near_match_fails() -> None:
    allow = policy_gate._load_allowlist()
    # Exact allowlisted path+class from repo allowlist should suppress.
    path = "tests/ci/test_credential_hygiene_redaction_unification_v1.py"
    suppressed = policy_gate.scan_text(path, f"x={SYN_API_KEY}\n", allow)
    assert not any(f.pattern_class == "OPENAI_STYLE_KEY" for f in suppressed)
    # Near-match different path must fail.
    near = policy_gate.scan_text(
        "tests/ci/near_match_not_allowlisted.py",
        f"x={SYN_API_KEY}\n",
        allow,
    )
    assert any(f.pattern_class == "OPENAI_STYLE_KEY" for f in near)


def test_expired_and_malformed_allowlist_fail_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    bad = {
        "schema_version": "tracked_credential_like_allowlist_v1",
        "entries": [
            {
                "path": "tests/ci/x.py",
                "pattern_class": "OPENAI_STYLE_KEY",
                "bounded": True,
                "owner": "security-hygiene",
                "expires_on": "2000-01-01",
                "reason": "Synthetic expired entry for fail-closed test.",
            }
        ],
    }
    path = tmp_path / "allow.json"
    path.write_text(json.dumps(bad), encoding="utf-8")
    monkeypatch.setattr(policy_gate, "ALLOWLIST_PATH", path)
    with pytest.raises(ValueError, match="expired"):
        policy_gate._load_allowlist()

    wild = {
        "schema_version": "tracked_credential_like_allowlist_v1",
        "entries": [
            {
                "path": "tests/**/*.py",
                "pattern_class": "OPENAI_STYLE_KEY",
                "bounded": True,
                "owner": "security-hygiene",
                "review_by": "2099-01-01",
                "reason": "Synthetic wildcard must fail closed.",
            }
        ],
    }
    path.write_text(json.dumps(wild), encoding="utf-8")
    with pytest.raises(ValueError, match="wildcard|exact"):
        policy_gate._load_allowlist()

    disabled = {
        "schema_version": "tracked_credential_like_allowlist_v1",
        "entries": [
            {
                "path": "tests/ci/x.py",
                "pattern_class": "OPENAI_STYLE_KEY",
                "bounded": True,
                "owner": "security-hygiene",
                "review_by": "2099-01-01",
                "global_disable": True,
                "reason": "Synthetic global disable must fail closed.",
            }
        ],
    }
    path.write_text(json.dumps(disabled), encoding="utf-8")
    with pytest.raises(ValueError, match="global"):
        policy_gate._load_allowlist()


def test_ordinary_source_text_no_uncontrolled_false_positives() -> None:
    allow = policy_gate._load_allowlist()
    findings = policy_gate.scan_text("ordinary_module.py", ORDINARY, allow)
    assert findings == []


def test_tracked_repo_gate_green_and_deterministic() -> None:
    first = policy_gate.scan_repo()
    second = policy_gate.scan_repo()
    assert first == []
    assert second == []
    assert first == second


def test_cli_json_deterministic_no_network_no_raw_secret() -> None:
    buf1 = StringIO()
    buf2 = StringIO()
    with contextlib.redirect_stdout(buf1):
        rc1 = policy_gate.main(["--json"])
    with contextlib.redirect_stdout(buf2):
        rc2 = policy_gate.main(["--json"])
    assert rc1 == 0 and rc2 == 0
    assert buf1.getvalue() == buf2.getvalue()
    payload = json.loads(buf1.getvalue())
    assert payload["findings_count"] == 0
    assert payload["secret_value_exposed"] is False
    assert payload["network_required"] is False
    assert payload["history_scan_status"] == "MANUAL_BOUNDED"
    assert payload["tracked_tree_scan_enforced"] is True
    dumped = json.dumps(payload)
    assert SYN_API_KEY not in dumped
    assert SYN_AWS_KEY not in dumped
    # Documented skip prefixes are reported (not silent).
    assert payload["documented_skip_prefixes"]


def test_manual_history_mode_truthful_status() -> None:
    buf = StringIO()
    with contextlib.redirect_stdout(buf):
        rc = policy_gate.main(["--manual-history", "--history-max-commits", "5", "--json"])
    assert rc in (0, 1)
    payload = json.loads(buf.getvalue())
    assert payload["mode"] == "manual_history_bounded"
    assert payload["history_scan_status"] == "MANUAL_BOUNDED"
    assert payload["tracked_tree_scan_enforced"] is False
    assert payload["secret_value_exposed"] is False


def test_lint_gate_wires_scanner_without_write_or_pr_target() -> None:
    text = LINT_GATE.read_text(encoding="utf-8")
    assert "check_tracked_credential_hygiene_policy_v1.py" in text
    assert "Tracked secret-like policy gate" in text
    assert re.search(r"^permissions\s*:", text, re.MULTILINE)
    assert "write-all" not in text.lower()
    assert "pull_request_target" not in text
    # No permissions: write expansions in this workflow.
    for line in text.splitlines():
        if re.search(r":\s*write\b", line) and not line.strip().startswith("#"):
            pytest.fail(f"unexpected write permission in lint_gate.yml: {line}")


def test_security_notes_and_allowlist_schema() -> None:
    notes = SECURITY_NOTES.read_text(encoding="utf-8")
    assert "SECRET_SCANNING_AND_PUSH_PROTECTION_GOVERNANCE_V1" in notes
    allow = policy_gate._load_allowlist()
    assert allow["schema_version"] == "tracked_credential_like_allowlist_v1"
    for entry in allow["entries"]:  # type: ignore[union-attr]
        assert entry["bounded"] is True
        assert entry["owner"]
        assert entry.get("expires_on") or entry.get("review_by")
