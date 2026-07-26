# SECRET_HYGIENE_AND_REDACTION_UNIFICATION_V1

**Capability ID:** `SECRET_HYGIENE_AND_REDACTION_UNIFICATION_V1`  
**Mode:** Repository policy + pure redaction utility. **Non-authorizing.**  
**Does not:** rotate secrets, mutate GitHub security toggles, enable live/testnet/orders, rewrite history, or change Runtime/trading authority.

## Design decision

**Option B — ratify one narrowly scoped canonical redaction owner** because no repository-wide redaction SSOT existed.

| Role | Path |
|------|------|
| Canonical redaction owner | [`scripts/security/secret_hygiene_redaction_v1.py`](../../../scripts/security/secret_hygiene_redaction_v1.py) |
| Tracked secret-like policy gate | [`scripts/ci/check_tracked_credential_hygiene_policy_v1.py`](../../../scripts/ci/check_tracked_credential_hygiene_policy_v1.py) |
| Bounded allowlist | [`tracked_credential_like_allowlist_v1.json`](tracked_credential_like_allowlist_v1.json) |
| Regression contracts | [`tests/ci/test_credential_hygiene_redaction_unification_v1.py`](../../../tests/ci/test_credential_hygiene_redaction_unification_v1.py) |

`CONTRACT_ID = secret_hygiene_redaction_v1`. A second module defining the same contract id is forbidden.

## Redaction contract (fail-closed)

| Concern | Rule |
|---------|------|
| Marker | `[REDACTED]` (deterministic, unmistakable) |
| Null / empty | Preserved unchanged (no secret material) |
| Sensitive keys | Entire value replaced with marker (nested maps included) |
| Embedded strings | Bearer/Basic tokens, JWT-like, `sk-…`, `AKIA…`, PEM private key blocks, `key=value` assignments, URL userinfo |
| Headers | `authorization`, `cookie`, `set-cookie`, `x-api-key`, and key-name matches |
| URLs | Userinfo credentials replaced with bracketless `REDACTED:REDACTED@` (keeps host/path parseable; `[REDACTED]` would break `urlsplit` IPv6 parsing); sensitive query keys replaced with `[REDACTED]` |
| Nested dict/list/tuple/dataclass | Recursed with depth cap (`MAX_RECURSION_DEPTH`) |
| Unsupported objects | `[REDACTED:UNSUPPORTED_PAYLOAD]` — never raw `repr` passthrough |
| Idempotence | Re-redacting already redacted output is stable |
| Fabrication | Never invents replacement business data |

## Approved boundaries (adapters)

Call these helpers at the serialization/logging edge — do not mutate domain truth solely for display safety:

- `redact_for_logging` / `SecretRedactionLoggingFilter` / `install_logging_redaction_filter`
- `redact_for_diagnostics`
- `redact_for_evidence_export`
- `redact_for_webui_payload` (dashboard remains a pure read-only consumer, not a security authority)
- `redact_headers`, `redact_exception`, `redact_structured`

## Legacy / incomplete consumers (not second owners)

These remain domain-specific helpers and must not grow parallel policy:

- `src/ai_orchestration/evidence_pack_generator.py` (`_redact_content`) — incomplete local subset; new evidence export paths should call the canonical owner
- `src/ai_orchestration/model_client.py` (`redact_outbound_envelope`) — allowlist envelope, not general redaction
- `scripts/ops/run_shadow_bounded_observation_adapter_v0.py` (`_sanitize_command_for_transcript`) — command transcript scrub
- Private-readonly / order-capability `value_redacted` flags — evidence shape contracts, not string redaction

## Tracked secret-like policy

Gate scans tracked textual files for high-confidence classes (PEM private key headers, AWS access key ids, OpenAI-style keys, JWT-like triples, URL userinfo). Hits outside the bounded allowlist fail closed. Matched values are never printed.

## Residual risks

| ID | Risk | Notes |
|----|------|-------|
| RR-SH-001 | Not every historical call site is migrated | Legacy local helpers remain; new boundaries must use the owner |
| RR-SH-002 | Pattern detection is best-effort | High-entropy opaque secrets without known shape may evade string detectors; sensitive key names still catch structured fields |
| RR-SH-003 | External gitleaks job still optional | Repo gate covers high-confidence classes and is CI-enforced via Lint Gate under `SECRET_SCANNING_AND_PUSH_PROTECTION_GOVERNANCE_V1`; optional gitleaks remains complementary |
| RR-SH-004 | Generated artifacts outside git | Untracked local evidence may still need operators to run export through adapters |
| RR-SH-005 | Full Git history not CI-enforced | `HISTORY_SCAN_STATUS=MANUAL_BOUNDED` — see governance spec; do not claim complete history protection |

Governance overlay: [`SECRET_SCANNING_AND_PUSH_PROTECTION_GOVERNANCE_V1.md`](SECRET_SCANNING_AND_PUSH_PROTECTION_GOVERNANCE_V1.md).


## Explicit non-claims

This capability does not claim secret rotation, provider revocation, Git history purge, or Runtime/Live authorization changes.
