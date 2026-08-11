# §11.12.9.29 Pre-Live SBOM_PRESENT package

## Verdict

`SBOM_PRESENT=true` / `SBOM_PRESENT_PROVEN=true` bound on `origin/main` `1b61cd94af98439e55e12d7bb839e44852027a06`.

`PRE_LIVE_CYBERSECURITY_GATE=NOT_PASSED` (unchanged).

## Proof method

Reuse-before-new canonical SBOM export owner from `scripts/ops/run_full_audit.sh`:

```text
uv export --format cyclonedx1.5 --output-file proofs/sbom.cyclonedx1.5.json
```

Structural validation: `bomFormat=CycloneDX`, `specVersion=1.5`, non-empty components, SHA256-bound artifact.

## Artifact summary

| Field | Value |
|---|---|
| RUN_ID | `20260811T042745Z` |
| ORIGIN_MAIN_SHA | `1b61cd94af98439e55e12d7bb839e44852027a06` |
| SBOM_SHA256 | `5707f7636d756f64dd2bdc2812094ac7c2b3af114902c1bb2b9b8ab088f0c8c8` |
| SBOM_BYTES | `20650` |
| component_count | `67` |
| dependency_node_count | `68` |
| EXPORT_RC | `0` |
| STRUCTURAL_VALID | `true` |

## Explicit non-claims

- Not `PRE_LIVE_CYBERSECURITY_GATE=PASS`
- Not Live / Testnet / order / credential authorization
- Not Cap / §11.13 started
- Not `STATIC_SECURITY_ANALYSIS` (next separate Owner-GO)
- Not penetration / regression / credential-leakage / authority-replay / recovery packages
- No trading-logic mutation
- `DEPENDENCY_AUDIT=PASS` remains prior binding; SBOM ≠ dependency audit

## Next step

```text
CANONICAL_NEXT_STEP=OWNER_GO_REQUIRED_SEPARATE_FOR_PRE_LIVE_SECURITY_PACKAGE_STATIC_SECURITY_ANALYSIS
HARD_STOP_AFTER_THIS_PACKAGE=true
```
