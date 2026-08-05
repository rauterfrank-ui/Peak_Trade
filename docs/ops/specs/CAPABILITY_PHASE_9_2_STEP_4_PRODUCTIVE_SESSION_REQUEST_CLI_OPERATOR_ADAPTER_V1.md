---
docs_token: DOCS_TOKEN_CAPABILITY_PHASE_9_2_STEP_4_PRODUCTIVE_SESSION_REQUEST_CLI_OPERATOR_ADAPTER_V1
status: active
scope: Phase 9.2 Step-4 CLI/operator adapter assembling canonical session_request from issuance artifacts; no network session
capability: PHASE_9_2_STEP_4_PRODUCTIVE_SESSION_REQUEST_CLI_OPERATOR_ADAPTER_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-08-05
---

# Capability — Phase 9.2 Step-4 Productive Session Request CLI Operator Adapter V1

## Forensic gap (after PR #5755)

Owner-session permit and runner-signature binding were closed, but the
productive CLI still omitted a signature-compatible `session_request`:

```text
REQUIRED_RUNNER_KWARGS=
  prereg, go, confirm_token, artifact_path,
  evidence_root, expected_repository_sha, fingerprint_ledger_path
CLI_DID_NOT_PASS_session_request=true
PRODUCTIVE_ENTRYPOINT_CLI_MISSING_SESSION_REQUEST_ADAPTER=true
```

## Closed by this capability

1. Canonical adapter
   `session_request_cli_adapter_v1.build_canonical_session_request_from_issuance_artifacts_v1`
   assembles the existing session_request Mapping from issuance artifacts.

2. CLI wires artifact paths:
   `--preregistration`, `--operator-go`, `--authorization-artifact`,
   `--confirm-token-file`, `--fingerprint-ledger`, optional matching
   `--evidence-root` / `--expected-repository-sha`.

3. Fail-closed validation before any activation consume:
   missing/stale paths, SHA mismatch, ledger/artifact binding mismatch,
   missing owner-session permit.

4. Controlled dry probe only:
   `network_session_allowed` must remain false under this capability.
   No auth/token consumption. No HTTP. No runner network side effect.

## Call graph

```text
Canonical issuance artifacts
→ Productive CLI argument resolution
→ canonical session_request adapter
→ canonical session_request validation
→ execute_productive_rate_limit_reconnect_session_activation_v1
→ existing canonical runner signature (kwargs bound)
→ controlled no-network dry-probe boundary
```

## Field source map

| session_request field | Source |
| --- | --- |
| `prereg` | issuance `preregistration.json` via `parse_preregistration_contract_v1` |
| `go` | issuance `operator_go.json` via `parse_operator_go_contract_v1` |
| `confirm_token` | canonical confirm-token file load (memory only; redacted in logs) |
| `artifact_path` | issuance authorization artifact path |
| `evidence_root` | `prereg.evidence_root` (CLI override must match) |
| `expected_repository_sha` | `prereg.expected_repository_sha` (CLI must match if set) |
| `fingerprint_ledger_path` | explicit operator `--fingerprint-ledger` |
| `use_real_network` | adapter constant `false` |

## Boundaries

```text
NETWORK_SESSION_ALLOWED=false
AUTHORIZATION_ISSUANCE=false
AUTHORIZATION_CONSUMPTION=false
CONFIRM_TOKEN_CONSUMPTION=false
CONFIRM_TOKEN_PLAINTEXT_EXPOSED=false
NO_PARALLEL_SESSION_REQUEST_MODEL=true
CORE_LOGIC_CHANGE=false
DASHBOARD_AUTHORITY_EFFECT=NONE
```

## Out of scope

- Starting a real Public-MD network session
- Minting authorization or confirm tokens
- Changing wallclock runner / transport / rate-limit policy
- Live / Testnet / credentials / orders / capital
- Dashboard / presentation / Notion / ruleset mutation
