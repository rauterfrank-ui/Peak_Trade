# §11.12.9.30 Pre-Live STATIC_SECURITY_ANALYSIS package

## Verdict

`STATIC_SECURITY_ANALYSIS=FAIL` / `STATIC_SECURITY_ANALYSIS_PROVEN=false`

Bound on `origin/main` `1b61cd94af98439e55e12d7bb839e44852027a06`.

`PRE_LIVE_CYBERSECURITY_GATE=NOT_PASSED` (unchanged).

## Proof method

Reuse-before-new canonical SAST owner from `scripts/ops/run_audit.sh`:

```text
bandit -r src
```

Executed via `uvx bandit` (tooling ephemeral; no lockfile mutation). Semgrep remains default-off per `docs/ops/specs/SEMGREP_SAST_ADOPTION_CONCEPT_V0.md` and was **not** newly activated.

## Finding summary

| Severity | Count |
|---|---|
| CRITICAL | 0 |
| HIGH | 5 |
| MEDIUM | 51 |
| LOW | 2171 |
| TOTAL | 2227 |

`HIGH_FINDINGS_OPEN=5` / `CRITICAL_FINDINGS_OPEN=0`

### HIGH findings (blocking for package PASS)

- `B202` HIGH/HIGH: `src&#47;backtest&#47;p36&#47;tarball_v1.py` line 67 — tarfile.extractall used without any validation. Please check and discard dangerous members.
- `B324` HIGH/HIGH: `src&#47;experiments&#47;armstrong_elkaroui_combi_experiment.py` line 529 — Use of weak MD5 hash for security. Consider usedforsecurity=False
- `B324` HIGH/HIGH: `src&#47;experiments&#47;base.py` line 348 — Use of weak MD5 hash for security. Consider usedforsecurity=False
- `B324` HIGH/HIGH: `src&#47;experiments&#47;experiment_identity_manifest_v1.py` line 234 — Use of weak MD5 hash for security. Consider usedforsecurity=False
- `B602` HIGH/HIGH: `src&#47;ops&#47;test_health_runner.py` line 477 — subprocess call with shell=True identified, security issue.

### Suggested remediation (not authorized / not executed)

- `B202` @ `src&#47;backtest&#47;p36&#47;tarball_v1.py` line 67: Validate tar members before extractall (or use safe extract helpers); reject path traversal / absolute paths.
- `B324` @ `src&#47;experiments&#47;armstrong_elkaroui_combi_experiment.py` line 529: If MD5 is non-cryptographic (checksum/id), set usedforsecurity=False; otherwise use SHA-256+.
- `B324` @ `src&#47;experiments&#47;base.py` line 348: If MD5 is non-cryptographic (checksum/id), set usedforsecurity=False; otherwise use SHA-256+.
- `B324` @ `src&#47;experiments&#47;experiment_identity_manifest_v1.py` line 234: If MD5 is non-cryptographic (checksum/id), set usedforsecurity=False; otherwise use SHA-256+.
- `B602` @ `src&#47;ops&#47;test_health_runner.py` line 477: Replace shell=True with argv list subprocess and explicit executable path.

## Explicit non-claims

- Not `PRE_LIVE_CYBERSECURITY_GATE=PASS`
- Not Live / Testnet / order / credential authorization
- Not Cap / §11.13 started
- Not `SECURITY_REGRESSION` / penetration / credential-leakage packages
- No trading-logic mutation
- No auto-remediation of HIGH findings under this Owner-GO
- STATIC_SECURITY_ANALYSIS executed ≠ STATIC_SECURITY_ANALYSIS proven PASS

## Next step

```text
CANONICAL_NEXT_STEP=OWNER_GO_REQUIRED_SEPARATE_FOR_PRE_LIVE_SECURITY_PACKAGE_STATIC_SECURITY_ANALYSIS_REMEDIATION_OR_RERUN_AFTER_HIGH_FINDING_CLOSURE
HARD_STOP_AFTER_THIS_PACKAGE=true
SECURITY_REGRESSION_AUTHORIZED=false
```
