# PL_TF_002 Read-Only Endpoint Contract Remediation — Adversarial Contract Review V1

```text
WORK_PACKAGE_ID=PL_TF_002_READ_ONLY_ENDPOINT_CONTRACT_REMEDIATION_V1
BASELINE_ORIGIN_MAIN_SHA=ff7ece37fb56e8d6ea7a1ca3a03737c341f17c5e
TRADING_LOGIC_CHANGED=false
PRODUCTION_AUTHORIZATION_WIDENED=false
POST_ALLOWED=false
EXTERNAL_EFFECT_AUTHORIZED=false
```

## Finding reviewed

Test `test_transport_post_and_treasury_forbidden` asserted PL-TF-002 policy on
`FullCoreProductiveReadOnlyGetTransportV1` directly. Session policy lives in
`_assert_get_only_surface_v1`; transport retains GET exact-order lookup for
reconciliation-only consumers.

## Adversarial checks

| Check | Result |
| --- | --- |
| PL-TF-002 still excludes `/api/v5/trade/order` | PASS (`FORBIDDEN_MUTATION_ENDPOINTS`) |
| F1 allowlist unchanged | PASS (fresh pretrade paths only) |
| Transport POST prohibition | PASS (`FORBIDDEN_METHODS`) |
| Treasury/cancel hard-block on transport | PASS (`FORBIDDEN_ENDPOINTS`) |
| Recon exact lookup confined to transport + separate WP | PASS (no PL-TF-002 allowlist widen) |
| Trading logic touched | PASS (none) |
| Standing safety pins | PASS (unchanged) |

## Verdict

`CONTRACT_REMEDIATION_SAFE` — test/spec alignment only; strictest session policy preserved.
