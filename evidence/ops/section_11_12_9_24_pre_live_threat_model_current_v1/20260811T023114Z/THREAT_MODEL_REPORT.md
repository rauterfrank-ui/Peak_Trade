# §11.12.9.24 Pre-Live Threat Model Current

- Owner-GO: `OWNER_GO_PRE_LIVE_SECURITY_PACKAGE_THREAT_MODEL_CURRENT`
- Origin/main SHA: `4431f810752bb1c42d94d24a2dcc24127a98fdcb`
- Run ID: `20260811T023114Z`
- Package verdict: **PASS** (`THREAT_MODEL_CURRENT=true`)
- Pre-Live gate: **NOT_PASSED** (remaining §18.2 packages unmet)
- Earliest unresolved after this package: `SECRETS_REVIEW`
- Threat catalog: 24 threats; required topic coverage PASS
- Currentness checks: 10/10 PASS
- Static currentness/control probes: ALL_PASS
- Critical/High findings in this package: 0 / 0
- Live authorized: false
- Section 11.13 started: false
- No Live/Testnet orders; no credentials accessed; no venue network writes

## Scope

Evidence-bound Pre-Live acceptance threat model against Cybersecurity Runbook
V2.1 §4 / §18.2 criterion `THREAT_MODEL_CURRENT` on current `origin/main`,
including Phase-11 / Testnet / Pre-Live architecture, trust boundaries, and
residual risks. Reuses venue-scoped `THREAT_MODEL_DELTA` artifacts and
§11.12.9.23 architecture review as inputs.

Does **not** execute secrets review, dependency audit, SBOM, static analysis,
regression, penetration, leakage, authority-replay, recovery-security,
isolation, arming, or findings-register packages. Does **not** set
`PRE_LIVE_CYBERSECURITY_GATE=PASS`.

## Trust boundaries modeled

1. Operator ↔ Control Plane
2. Control Plane ↔ Execution Plane
3. Execution Plane ↔ Exchange/Venue
4. Runtime/Operator Persistence Boundary
5. CI/CD / GitHub Boundary
6. Evidence / Audit Boundary
7. Notion Consumer/Mirror Boundary (non-SSOT)

## Assets (summary)

- Durable authorization / Owner-GO surface
- Confirm-token / enabled / armed / dry-run gates
- SecretRef credential path and Demo credential class
- OKX EEA Demo XPerp venue/host/instrument binding
- Order POST / campaign write surface
- Kill-switch / emergency control
- Sealed evidence manifests
- Repository SSOT vs Notion mirror

## Actors (summary)

- External internet attacker
- Supply-chain / CI attacker
- Compromised credentials
- Insider / malicious or accidental operator
- Venue anomaly / stale-forged responses
- Dependency / Action compromise

## Currentness

`CURRENTNESS_CHECK.json` verifies the model reflects:

- Bound SHA `4431f810752bb1c42d94d24a2dcc24127a98fdcb`
- Active binding: OKX EEA Demo / `https://eea.okx.com` / `BTC-USD_UM_XPERP-310328` / xperp
- `LIVE_AUTHORIZED=false`, `SECTION_11_13_STARTED=false`, gate `NOT_PASSED`
- `TESTNET_LIFECYCLE_PROVEN=true`, `LONG_RUNNING_TESTNET_PROVEN=true`
- `CYBERSECURITY_ARCHITECTURE_REVIEW=PASS`
- No invented PASS for remaining §18.2 packages

## Residual risks (do not block THREAT_MODEL_CURRENT)

1. `SECRETS_REVIEW` outstanding (next Owner-GO).
2. `DEPENDENCY_AUDIT` / `SBOM_PRESENT` / `STATIC_SECURITY_ANALYSIS` outstanding.
3. Adversarial packages (`PENETRATION_PROGRAM`, `AUTHORITY_REPLAY_TEST`,
   `CREDENTIAL_LEAKAGE_TEST`, `RECOVERY_SECURITY_TEST`) outstanding.
4. Governed Pre-Live findings register not yet sealed (`CRITICAL_FINDINGS_OPEN` /
   `HIGH_FINDINGS_OPEN` remain OPEN fail-closed for gate accounting).
5. `LIVE_*` isolation/arming proofs remain separate packages.
6. Notion mirror lag is an accepted residual until post-merge sync.

## Distinctions

```text
THREAT_MODEL_CURRENT != PRE_LIVE_CYBERSECURITY_GATE_PASS
THREAT_MODEL_CURRENT != LIVE_AUTHORIZED
THREAT_MODEL_CURRENT != SECTION_11_13_STARTED
THREAT_MODEL_CURRENT != SECRETS_REVIEW
VENUE_THREAT_MODEL_DELTA != THREAT_MODEL_CURRENT
ARCHITECTURE_REVIEW_PASS != THREAT_MODEL_CURRENT
```
