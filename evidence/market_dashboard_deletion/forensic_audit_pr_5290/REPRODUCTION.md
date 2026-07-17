# Market Dashboard deletion — forensic reproduction (PR #5290)

## Identity

- BASE=`987e020378d1767fbd6fb1f0914d475f9a485f51`
- HEAD=`PENDING_COMMIT`

## Counts

```bash
LC_ALL=C git diff --name-status -M 987e020378d1767fbd6fb1f0914d475f9a485f51 HEAD | wc -l
LC_ALL=C git diff --name-status -M 987e020378d1767fbd6fb1f0914d475f9a485f51 HEAD | cut -f1 | sort | uniq -c
```

## Final diff digest (excludes evidence/market_dashboard_deletion/**)

```bash
LC_ALL=C git -c core.quotepath=false diff --binary --full-index --no-ext-diff \
  987e020378d1767fbd6fb1f0914d475f9a485f51 HEAD -- . ':(exclude)evidence/market_dashboard_deletion/**' \
  | shasum -a 256
```

## Manifest digest

```bash
shasum -a 256 evidence/market_dashboard_deletion/manifest.sha256
# must match evidence/market_dashboard_deletion/manifest_file.sha256
```

## Verify

```bash
uv run python scripts/ops/verify_market_dashboard_deletion_evidence_v1.py \
  --base 987e020378d1767fbd6fb1f0914d475f9a485f51 --head HEAD
```
