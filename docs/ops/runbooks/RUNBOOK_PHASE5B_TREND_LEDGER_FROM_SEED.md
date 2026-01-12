# Runbook: Phase 5B – Trend Ledger from Seed

**Phase:** 5B  
**Component:** Trend Ledger Consumer  
**Scope:** AIOps / Trend Analysis  
**Owner:** AI Orchestration Team

---

## Purpose

Phase 5B consumes **Phase 5A Trend Seeds** (generated from normalized validator reports) and produces a **canonical Trend Ledger snapshot** as a CI artifact.

**Key Properties:**
- **Deterministic:** Canonical JSON with stable ordering (sorted keys, stable lists)
- **Fail-closed:** Schema mismatch or missing fields → hard fail
- **CI-friendly:** Clear artifact names, minimal size, machine-readable
- **Operator-friendly:** Markdown summary included

---

## Architecture

### Input
- **Trend Seed JSON** (Phase 5A output)
  - Schema: v0.1.0
  - Source: Phase 4E normalized validator report
  - Contains: run metadata, conclusion, determinism info, counters

### Processing
- **Consumer Library:** `src/ai_orchestration/trends/trend_ledger.py`
  - Validates seed schema (fail-closed)
  - Extracts source metadata, counters, determinism info
  - Builds canonical ledger items (sorted by category/key)
  - Serializes to deterministic JSON (sorted keys, stable ordering)

### Output
- **Trend Ledger JSON** (canonical)
  - Schema: v0.1.0
  - Deterministic: byte-identical for same input
  - Structure: `{schema_version, generated_at, source_run, items[], counters}`
- **Markdown Summary** (operator-friendly)
  - Metadata, counters, items overview
- **Run Manifest** (CI tracking)
  - Phase, component, version, input/output hashes

---

## Usage

### CLI (Local)

```bash
# Basic usage
python scripts/aiops/generate_trend_ledger_from_seed.py \
  --input trend_seed.json \
  --output-json trend_ledger.json \
  --output-markdown trend_ledger.md

# With run manifest (CI mode)
python scripts/aiops/generate_trend_ledger_from_seed.py \
  --input trend_seed.json \
  --output-json trend_ledger.json \
  --output-markdown trend_ledger.md \
  --run-manifest manifest.json
```

**Exit Codes:**
- `0`: Success
- `1`: Error (schema mismatch, validation failure, IO error)
- `2`: Usage error (missing required arguments)

### CI Workflow

**Workflow:** `.github/workflows/aiops-trend-ledger-from-seed.yml`

**Trigger:** `workflow_run` on Phase 5A completion (success only, `main` branch only)

**Artifacts:**
- **Name:** `trend-ledger-<run_id>`
- **Contents:**
  - `trend_ledger.json` (canonical ledger)
  - `trend_ledger.md` (markdown summary)
  - `manifest.json` (run metadata)
- **Retention:** 30 days

**How to Access:**
1. Navigate to Phase 5A workflow run on GitHub Actions
2. Check "Workflow runs" for Phase 5B (triggered automatically)
3. Download artifact: `trend-ledger-<run_id>`

---

## Testing

### Unit Tests

```bash
# Run Phase 5B tests
pytest tests/ai_orchestration/test_trend_ledger_from_seed.py -v

# Run with coverage
pytest tests/ai_orchestration/test_trend_ledger_from_seed.py --cov=src.ai_orchestration.trends.trend_ledger
```

**Test Coverage:**
- Load trend seed from JSON
- Generate ledger from seed
- Canonical JSON serialization (determinism)
- Markdown summary rendering
- Schema validation (fail-closed)
- Error handling (missing fields, unsupported schema)

### Determinism Test

```bash
# Generate ledger twice from same seed, compare hashes
python scripts/aiops/generate_trend_ledger_from_seed.py \
  --input tests/fixtures/trend_seed.sample.json \
  --output-json /tmp/ledger1.json

python scripts/aiops/generate_trend_ledger_from_seed.py \
  --input tests/fixtures/trend_seed.sample.json \
  --output-json /tmp/ledger2.json

# Compare byte-for-byte
diff /tmp/ledger1.json /tmp/ledger2.json
# Should produce no output (files identical)

# Compare SHA-256 hashes
sha256sum /tmp/ledger1.json /tmp/ledger2.json
# Should produce identical hashes
```

---

## Schema

### Trend Ledger Schema (v0.1.0)

```json
{
  "schema_version": "0.1.0",
  "generated_at": "2026-01-11T12:00:00Z",
  "source_run": {
    "repo": "owner/repo",
    "workflow_name": "L4 Critic Replay Determinism",
    "run_id": "12345",
    "run_attempt": 1,
    "head_sha": "abc123",
    "ref": "refs/heads/main"
  },
  "items": [
    {
      "category": "validator_report",
      "key": "overall_status",
      "conclusion": "pass",
      "determinism_hash": "abc123",
      "is_deterministic": true,
      "report_id": "l4_critic_sample__..."
    }
  ],
  "counters": {
    "checks_total": 2,
    "checks_passed": 2,
    "checks_failed": 0,
    "policy_findings_total": 0,
    "items_total": 1
  }
}
```

**Key Fields:**
- `schema_version`: Ledger schema version (currently "0.1.0")
- `generated_at`: ISO-8601 UTC timestamp (from source seed)
- `source_run`: Original workflow run metadata
- `items`: Ledger items (sorted canonically by category, key)
- `counters`: Aggregated counters (checks, findings, items)

---

## Troubleshooting

### Error: "Trend seed not found"

**Cause:** Input file path is incorrect or file does not exist

**Fix:**
```bash
# Verify file exists
ls -lh trend_seed.json

# Use absolute path if relative path fails
python scripts/aiops/generate_trend_ledger_from_seed.py \
  --input /absolute/path/to/trend_seed.json \
  --output-json trend_ledger.json
```

### Error: "Unsupported schema_version"

**Cause:** Trend seed has unsupported schema version

**Fix:**
- Phase 5B supports Phase 5A seeds with schema v0.1.0
- Check seed schema version:
  ```bash
  jq '.schema_version' trend_seed.json
  ```
- Regenerate seed with Phase 5A consumer (v0.1.0+)

### Error: "Missing required field"

**Cause:** Trend seed is missing required fields (corrupt or incomplete)

**Fix:**
- Validate seed structure:
  ```bash
  jq 'keys' trend_seed.json
  # Should include: schema_version, source, normalized_report, generated_at
  ```
- Regenerate seed from normalized report using Phase 5A

### Error: "Missing or invalid 'source' field"

**Cause:** Seed is missing source metadata (repo, workflow_name, run_id, etc.)

**Fix:**
- Check source field:
  ```bash
  jq '.source' trend_seed.json
  ```
- Ensure Phase 5A consumer was invoked with all required metadata

---

## Monitoring

### Success Indicators
- ✅ CI workflow completes without errors
- ✅ Artifact `trend-ledger-<run_id>` uploaded successfully
- ✅ `trend_ledger.json` is valid JSON with schema v0.1.0
- ✅ Determinism test passes (repeated runs → identical hashes)

### Failure Indicators
- ❌ CI workflow fails with schema version error
- ❌ CI workflow fails with validation error (missing fields)
- ❌ Artifact upload fails or is incomplete
- ❌ Determinism test fails (different hashes for same input)

### Metrics (Future)
- Ledger generation time (target: <5s)
- Artifact size (target: <100KB per ledger)
- Schema version drift (alert on unsupported versions)

---

## Integration

### Upstream Dependencies
- **Phase 4E:** Normalized validator report (schema v1.0.0)
- **Phase 5A:** Trend seed consumer (schema v0.1.0)

### Downstream Consumers (Future)
- **Phase 5C:** Trend aggregation (multi-seed → time-series)
- **Phase 6:** Test health automation (trend-based alerting)
- **Phase 7:** Governance reporting (trend dashboards)

---

## References

- **Code:**
  - Consumer library: `src/ai_orchestration/trends/trend_ledger.py`
  - CLI: `scripts/aiops/generate_trend_ledger_from_seed.py`
  - Tests: `tests/ai_orchestration/test_trend_ledger_from_seed.py`
  - Fixtures: `tests/fixtures/trend_seed.sample.json`

- **CI:**
  - Workflow: `.github/workflows/aiops-trend-ledger-from-seed.yml`
  - Phase 5A workflow: `.github/workflows/aiops-trend-seed-from-normalized-report.yml`

- **Docs:**
  - Phase 5A runbook: `RUNBOOK_PHASE5A_NORMALIZED_REPORT_CONSUMER_TREND_SEED_CURSOR_MULTI_AGENT.md`
  - Phase 4E runbook: (see ops index)

---

## Change Log

| Version | Date       | Author | Changes                          |
|---------|------------|--------|----------------------------------|
| 0.1.0   | 2026-01-12 | AI Ops | Initial Phase 5B implementation  |

---

**Questions?** See ops index or Phase 5A runbook for context.
