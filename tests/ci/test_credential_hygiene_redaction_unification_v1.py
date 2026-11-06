"""SECRET_HYGIENE_AND_REDACTION_UNIFICATION_V1 — regression contracts.

Synthetic fixtures only. Never assert by printing secret values into
diagnostics beyond pytest failure diffs on already-synthetic strings.
"""

from __future__ import annotations

import io
import json
import logging
import re
from dataclasses import dataclass
from pathlib import Path

import pytest

import scripts.ci.check_tracked_credential_hygiene_policy_v1 as policy_gate
import scripts.security.secret_hygiene_redaction_v1 as redaction


REPO_ROOT = Path(__file__).resolve().parents[2]
OWNER_MODULE = REPO_ROOT / "scripts" / "security" / "secret_hygiene_redaction_v1.py"
SPEC_DOC = REPO_ROOT / "docs" / "ops" / "specs" / "SECRET_HYGIENE_AND_REDACTION_UNIFICATION_V1.md"
SECURITY_NOTES = REPO_ROOT / "SECURITY_NOTES.md"
ALLOWLIST = REPO_ROOT / "docs" / "ops" / "specs" / "tracked_credential_like_allowlist_v1.json"

# Unmistakably fake synthetic values (fixtures only).
SYN_API_KEY = "sk-SYNTHETICFAKEOPENAISTYLEKEY0000001"
SYN_AWS_KEY = "AKIAFAKESYNTH0000001"
SYN_JWT = "eyJhbGciOiJSYNTHETICIn0.eyJzdWIiOiJzeW50aGV0aWMtZmFrZSJ9.SYNTHETICFAKESIGNATUREVALUE0001"
SYN_PASSWORD = "synth-password-NOT-REAL-0001"
SYN_BEARER = "synth-bearer-token-NOT-REAL-0001"
SYN_COOKIE = "session=synth-cookie-NOT-REAL-0001"
SYN_PEM_BODY = (
    "-----BEGIN PRIVATE KEY-----\nSYNTHETIC_PEM_BODY_NOT_A_REAL_KEY_0001\n-----END PRIVATE KEY-----"
)
SYN_URL = (
    "https://synth_user:synth_pass_NOT_REAL@example.test/v1/orders?api_key=synth-query-NOT-REAL"
)


def test_owner_identity_and_marker() -> None:
    identity = redaction.owner_identity()
    assert identity["contract_id"] == "secret_hygiene_redaction_v1"
    assert identity["capability_id"] == "SECRET_HYGIENE_AND_REDACTION_UNIFICATION_V1"
    assert identity["redaction_marker"] == "[REDACTED]"
    assert redaction.REDACTION_MARKER == "[REDACTED]"
    assert OWNER_MODULE.is_file()
    assert SPEC_DOC.is_file()


def test_architecture_owner_uniqueness() -> None:
    """Exactly one module may declare the canonical contract id."""
    import subprocess

    hits: list[str] = []
    needle = re.compile(r'CONTRACT_ID\s*=\s*"secret_hygiene_redaction_v1"')
    tracked = subprocess.check_output(
        ["git", "-C", str(REPO_ROOT), "ls-files", "-z", "--", "*.py"],
        text=False,
    ).split(b"\0")
    untracked = subprocess.check_output(
        [
            "git",
            "-C",
            str(REPO_ROOT),
            "ls-files",
            "-z",
            "--others",
            "--exclude-standard",
            "--",
            "*.py",
        ],
        text=False,
    ).split(b"\0")
    rels = []
    for raw in tracked + untracked:
        if not raw:
            continue
        rels.append(raw.decode("utf-8"))
    for rel in sorted(set(rels)):
        path = REPO_ROOT / rel
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        if needle.search(text):
            hits.append(rel)
    assert hits == ["scripts/security/secret_hygiene_redaction_v1.py"]


def test_sensitive_field_names_redacted() -> None:
    payload = {
        "api_key": SYN_API_KEY,
        "password": SYN_PASSWORD,
        "authorization": f"Bearer {SYN_BEARER}",
        "cookie": SYN_COOKIE,
        "client_secret": "synth-client-secret-NOT-REAL",
        "refresh_token": "synth-refresh-NOT-REAL",
        "ok": "safe-value",
        "count": 3,
        "empty_secret": "",
        "null_token": None,
    }
    out = redaction.redact_structured(payload)
    assert out["api_key"] == redaction.REDACTION_MARKER
    assert out["password"] == redaction.REDACTION_MARKER
    assert out["authorization"] == redaction.REDACTION_MARKER
    assert out["cookie"] == redaction.REDACTION_MARKER
    assert out["client_secret"] == redaction.REDACTION_MARKER
    assert out["refresh_token"] == redaction.REDACTION_MARKER
    assert out["ok"] == "safe-value"
    assert out["count"] == 3
    assert out["empty_secret"] == ""
    assert out["null_token"] is None
    redaction.assert_no_raw_secret(out, SYN_API_KEY)
    redaction.assert_no_raw_secret(out, SYN_PASSWORD)
    redaction.assert_no_raw_secret(out, SYN_BEARER)


def test_embedded_token_formats_redacted() -> None:
    raw = f"call with Bearer {SYN_BEARER} and key {SYN_API_KEY} aws={SYN_AWS_KEY} jwt={SYN_JWT}"
    out = redaction.redact_string(raw)
    assert "Bearer [REDACTED]" in out
    assert SYN_BEARER not in out
    assert SYN_API_KEY not in out
    assert SYN_AWS_KEY not in out
    assert SYN_JWT not in out
    assert redaction.REDACTION_MARKER in out


def test_headers_and_cookies_redacted() -> None:
    headers = {
        "Authorization": f"Bearer {SYN_BEARER}",
        "Cookie": SYN_COOKIE,
        "X-Api-Key": SYN_API_KEY,
        "Content-Type": "application/json",
        "X-Request-Id": "req-safe-001",
    }
    out = redaction.redact_headers(headers)
    assert out["Authorization"] == redaction.REDACTION_MARKER
    assert out["Cookie"] == redaction.REDACTION_MARKER
    assert out["X-Api-Key"] == redaction.REDACTION_MARKER
    assert out["Content-Type"] == "application/json"
    assert out["X-Request-Id"] == "req-safe-001"
    redaction.assert_no_raw_secret(out, SYN_BEARER)
    redaction.assert_no_raw_secret(out, SYN_COOKIE)
    redaction.assert_no_raw_secret(out, SYN_API_KEY)


def test_credential_bearing_url_redacted_preserves_host_path() -> None:
    out = redaction.redact_string(SYN_URL)
    assert "example.test" in out
    assert "/v1/orders" in out
    assert "synth_user" not in out
    assert "synth_pass_NOT_REAL" not in out
    assert "synth-query-NOT-REAL" not in out
    assert "api_key=[REDACTED]" in out
    assert "REDACTED:REDACTED@" in out


def test_nested_structures_and_dataclass() -> None:
    @dataclass(frozen=True)
    class Row:
        instrument: str
        api_key: str
        note: str

    payload = {
        "rows": [
            {"token": SYN_BEARER, "symbol": "BTC-USD"},
            ("keep", f"password={SYN_PASSWORD}"),
        ],
        "meta": Row(
            instrument="ETH-USD",
            api_key=SYN_API_KEY,
            note=f"Bearer {SYN_BEARER}",
        ),
        "flags": (True, False, None),
    }
    out = redaction.redact_structured(payload)
    assert out["rows"][0]["token"] == redaction.REDACTION_MARKER
    assert out["rows"][0]["symbol"] == "BTC-USD"
    assert out["rows"][1][0] == "keep"
    assert out["rows"][1][1] == f"password={redaction.REDACTION_MARKER}"
    assert SYN_PASSWORD not in out["rows"][1][1]
    assert out["meta"]["instrument"] == "ETH-USD"
    assert out["meta"]["api_key"] == redaction.REDACTION_MARKER
    assert SYN_BEARER not in out["meta"]["note"]
    assert out["flags"] == (True, False, None)
    redaction.assert_no_raw_secret(out, SYN_API_KEY)
    redaction.assert_no_raw_secret(out, SYN_PASSWORD)


def test_redaction_idempotent_and_never_returns_original() -> None:
    raw = f"Authorization: Bearer {SYN_BEARER}; key={SYN_API_KEY}"
    once = redaction.redact_string(raw)
    twice = redaction.redact_string(once)
    assert once == twice
    assert once != raw
    assert SYN_BEARER not in once
    assert SYN_API_KEY not in once


def test_does_not_fabricate_business_data() -> None:
    payload = {"pnl": 12.5, "status": "ok", "api_key": SYN_API_KEY}
    out = redaction.redact_structured(payload)
    assert out["pnl"] == 12.5
    assert out["status"] == "ok"
    assert out["api_key"] == redaction.REDACTION_MARKER
    # Marker is not a plausible fabricated pnl/status substitute.
    assert out["api_key"] != SYN_API_KEY
    assert out["api_key"] != ""
    assert out["api_key"] != "ok"


def test_safe_ordinary_values_unchanged() -> None:
    payload = {
        "instrument_id": "BTC-USD-SWAP",
        "reason_codes": ["NO_SIGNAL", "WARMUP"],
        "mark_price": 101.25,
        "summary": "all clear",
    }
    assert redaction.redact_structured(payload) == payload
    assert redaction.redact_string("hello world") == "hello world"


def test_logging_boundary_filter_redacts() -> None:
    logger = logging.getLogger("peak_trade.secret_hygiene.test")
    logger.handlers.clear()
    logger.filters.clear()
    logger.setLevel(logging.INFO)
    logger.propagate = False
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(handler)
    redaction.install_logging_redaction_filter(logger)

    logger.info("auth Bearer %s key=%s", SYN_BEARER, SYN_API_KEY)
    text = stream.getvalue()
    assert SYN_BEARER not in text
    assert SYN_API_KEY not in text
    assert redaction.REDACTION_MARKER in text
    assert redaction.redact_for_logging(f"cookie={SYN_COOKIE}")
    redaction.assert_no_raw_secret(redaction.redact_for_logging(f"cookie={SYN_COOKIE}"), SYN_COOKIE)


def test_diagnostics_and_evidence_and_webui_boundaries() -> None:
    diag = {
        "error_category": "AUTH_REJECTED",
        "source_class": "ExchangeClient",
        "authorization": f"Bearer {SYN_BEARER}",
        "detail": f"url={SYN_URL}",
    }
    for fn in (
        redaction.redact_for_diagnostics,
        redaction.redact_for_evidence_export,
        redaction.redact_for_webui_payload,
    ):
        out = fn(diag)
        assert out["error_category"] == "AUTH_REJECTED"
        assert out["source_class"] == "ExchangeClient"
        assert out["authorization"] == redaction.REDACTION_MARKER
        redaction.assert_no_raw_secret(out, SYN_BEARER)
        redaction.assert_no_raw_secret(out, "synth_pass_NOT_REAL")


def test_exception_and_pem_and_fail_closed_unsupported() -> None:
    exc = RuntimeError(f"upstream Authorization: Bearer {SYN_BEARER}")
    rendered = redaction.redact_exception(exc)
    assert rendered.startswith("RuntimeError:")
    assert SYN_BEARER not in rendered

    pem_out = redaction.redact_string(f"keymaterial:\n{SYN_PEM_BODY}")
    assert "BEGIN PRIVATE KEY" not in pem_out
    assert "SYNTHETIC_PEM_BODY" not in pem_out

    class Weird:
        def __repr__(self) -> str:
            return f"Weird(api_key={SYN_API_KEY})"

    unsupported = redaction.redact_structured({"x": Weird()})
    assert unsupported["x"] == redaction.UNSUPPORTED_PAYLOAD_MARKER
    redaction.assert_no_raw_secret(unsupported, SYN_API_KEY)


def test_tracked_secret_policy_gate_pass_on_repo() -> None:
    findings = policy_gate.scan_repo()
    # Never include matched values in assertions beyond class/path.
    assert findings == []
    assert ALLOWLIST.is_file()
    allow = json.loads(ALLOWLIST.read_text(encoding="utf-8"))
    assert allow["schema_version"] == "tracked_credential_like_allowlist_v1"
    assert isinstance(allow["entries"], list)
    for entry in allow["entries"]:
        assert entry.get("bounded") is True
        reason = str(entry.get("reason") or "").lower()
        assert any(
            token in reason
            for token in (
                "synthetic",
                "placeholder",
                "fixture",
                "pattern definition",
                "documentation",
            )
        )


def test_tracked_secret_policy_gate_rejects_new_secret_like(tmp_path: Path) -> None:
    allow = json.loads(ALLOWLIST.read_text(encoding="utf-8"))
    findings = policy_gate.scan_text(
        "unallowlisted_synthetic_probe.txt",
        f"token={SYN_API_KEY}\n",
        allow,
    )
    assert any(f.pattern_class == "OPENAI_STYLE_KEY" for f in findings)
    for finding in findings:
        # Path/class only — never compare against embedding the secret into messages.
        assert finding.path == "unallowlisted_synthetic_probe.txt"
        assert (
            finding.secret_value_exposed is False
            if hasattr(finding, "secret_value_exposed")
            else True
        )
    rc = policy_gate.main(["--paths-file", str(tmp_path / "missing_paths.txt")])
    assert rc != 0


def test_policy_gate_cli_pass_json() -> None:
    # Full repo scan via API already covered; CLI JSON must not include secret values.
    # Use empty path list file to exercise CLI without re-scanning whole repo twice if desired.
    # Here we invoke scan summary shape via main with --json on default repo.
    import contextlib
    from io import StringIO

    buf = StringIO()
    with contextlib.redirect_stdout(buf):
        rc = policy_gate.main(["--json"])
    assert rc == 0
    payload = json.loads(buf.getvalue())
    assert payload["findings_count"] == 0
    assert payload["secret_value_exposed"] is False
    dumped = json.dumps(payload)
    assert SYN_API_KEY not in dumped
    assert SYN_AWS_KEY not in dumped


def test_security_notes_point_to_canonical_owner() -> None:
    text = SECURITY_NOTES.read_text(encoding="utf-8")
    assert "SECRET_HYGIENE_AND_REDACTION_UNIFICATION_V1" in text
    assert "scripts/security/secret_hygiene_redaction_v1.py" in text
    assert (
        "tracked_secret_like_policy" in text
        or "check_tracked_credential_hygiene_policy_v1.py" in text
    )


def test_legacy_evidence_pack_is_not_second_contract_owner() -> None:
    """Legacy local redactor may exist but must not declare the canonical contract id."""
    path = REPO_ROOT / "src" / "ai_orchestration" / "evidence_pack_generator.py"
    text = path.read_text(encoding="utf-8")
    # Avoid embedding the exact assignment form (uniqueness scanner needle).
    assert "secret_hygiene_redaction_v1" not in text
    assert "def _redact_content" in text  # known legacy incomplete consumer
