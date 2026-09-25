# Bulk Proven Repository Decommission Grant v1

status: ACTIVE
owner: Peak_Trade
purpose: Fail-closed bulk bind of a pre-proven removal set to a fixed base SHA for repository convergence cuts only.
docs_token: DOCS_TOKEN_BULK_PROVEN_REPOSITORY_DECOMMISSION_GRANT_V1

```text
PARALLEL_SSOT_CREATED=false
RUNTIME_EFFECT=NONE
AUTHORITY_EFFECT=NONE
GRANT_KIND=BULK_PROVEN_REPOSITORY_DECOMMISSION_V1
TOKEN_ALONE_IS_INSUFFICIENT=true
```

Machine state: `config/governance/bulk_proven_repository_decommission_authorization_v1.json`

Distinct from `SEMANTICS_NEUTRAL_DECOMMISSION_ONLY` exact-file grants. Does not replace or weaken them.

Evidence SHA-256 canonicalization: sorted paths, UTF-8, each path followed by `\n`, chained via `hashlib.sha256().update()`.
