# Section 11.12.9.26 Pre-Live DEPENDENCY_AUDIT Report

```text
OWNER_GO=OWNER_GO_DEPENDENCY_AUDIT
RUN_ID=20260811T031527Z
ORIGIN_MAIN_SHA=95d043048d8538f934fcba469a728bd25da4f7de
DEPENDENCY_AUDIT_RESULT=FAIL
DEPENDENCY_AUDIT_PROVEN=false
PRE_LIVE_CYBERSECURITY_GATE=NOT_PASSED
```

## Scope

Productive, evidence-bound dependency / supply-chain audit against Cybersecurity Runbook V2.1 section 8 / 18.2 on origin/main `95d043048d8538f934fcba469a728bd25da4f7de`.

## Reuse-before-new

Reused existing owners: `uv.lock` + `requirements.txt` (uv export --locked), `.github/workflows/audit.yml` pip-audit path, `scripts/ops/run_full_audit.sh`, prior sealed SECRETS_REVIEW / Threat Model / Architecture Review packages. No duplicate parallel audit owner invented.

## Results summary

| Metric | Value |
|---|---|
| Deduped vulnerability findings | 20 |
| Critical | 0 |
| High | 6 |
| Medium | 11 |
| Low | 3 |
| Blocking (High/Critical open with fix) | 6 |
| Package requirements | 15/17 PASS; 2 FAIL |
| GHA uses SHA-pinned | 231/260 |
| Docker digest-pinned | 0/3 |
| Dependabot alerts | disabled |
| Node manifests tracked | 0 |

## Blocking findings (package PASS prevented)

- **msgpack@1.1.2** `GHSA-6v7p-g79w-8964` severity=HIGH scope=RUNTIME_OR_OPTIONAL_TRANSITIVE fix_versions=['1.2.1'] — DoS via crafted msgpack; HIGH severity upstream.
- **pyarrow@22.0.0** `GHSA-rgxp-2hwp-jwgg` severity=HIGH scope=RUNTIME_DIRECT fix_versions=['23.0.1'] — Runtime direct dep; HIGH; crafted IPC/data paths.
- **starlette@0.50.0** `GHSA-82w8-qh3p-5jfq` severity=HIGH scope=OPTIONAL_WEB_EXTRA fix_versions=['1.3.1'] — Optional web/FastAPI stack; HIGH vulns present if web surface enabled.
- **starlette@0.50.0** `GHSA-wqp7-x3pw-xc5r` severity=HIGH scope=OPTIONAL_WEB_EXTRA fix_versions=['1.1.0'] — Optional web/FastAPI stack; HIGH vulns present if web surface enabled.
- **urllib3@2.6.3** `GHSA-mf9v-mfxr-j63j` severity=HIGH scope=RUNTIME_DIRECT fix_versions=['2.7.0'] — Runtime direct constrained dep; HIGH streaming/header issues with fix in 2.7.0.
- **urllib3@2.6.3** `GHSA-qccp-gfcp-xxvc` severity=HIGH scope=RUNTIME_DIRECT fix_versions=['2.7.0'] — Runtime direct constrained dep; HIGH streaming/header issues with fix in 2.7.0.

## Process / control findings (non-blocking for HIGH rule)

See `proofs&#47;PROCESS_CONTROL_FINDINGS.json` (Dependabot disabled, requirements hash absence, Docker tag-only bases, residual floating GHA tags).

## Explicit non-claims

- `DEPENDENCY_AUDIT_PROVEN=false`
- No automatic dependency upgrades
- No trading-logic changes
- No SBOM package execution (`SBOM_PRESENT` remains separate)
- No section 11.13 / Live / Testnet / order authorization
- Gate remains `NOT_PASSED`

## Next Owner step

`OWNER_GO_REQUIRED_SEPARATE_FOR_PRE_LIVE_SECURITY_PACKAGE_DEPENDENCY_AUDIT_REMEDIATION_OR_RERUN_AFTER_HIGH_FINDING_CLOSURE`

Hard stop after this package. Separate Owner-GO required for remediation and/or re-audit.

