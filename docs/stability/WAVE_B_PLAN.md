# Stability – Wave B Plan

## Goal
Härten der Robustheit rund um Cache/Artefakte, Reproducibility-Metadaten und Error-UX, ohne neue schwere Dependencies.

## Deliverables
1) Atomic Cache Writes (temp -> rename), optional lock
2) Cache Manifest/Index (run_id -> files + hashes + schema versions)
3) Unified Error Taxonomy (Domain Exceptions)
4) Reproducibility Metadata: config hash, code sha, env snapshot
5) CI Smoke: fast E2E test (seconds), deterministic

## Tasks (proposed)
- [ ] cache: implement atomic write helper (tempfile + os.replace)
- [ ] cache: add manifest.json (or .toml) per run_id
- [ ] errors: define exceptions (e.g. DataContractError, CacheCorruptError, ConfigError)
- [ ] tracking: ensure run metadata always includes (git_sha, config_hash, python, platform)
- [ ] tests: add deterministic E2E smoke test for cache roundtrip + contracts
- [ ] docs: update stability runbook / overview

## Acceptance
- Deterministic reproduction on same inputs
- Corruption/partial writes are detected & surfaced cleanly
- Smoke test runs < 10s locally and in CI
