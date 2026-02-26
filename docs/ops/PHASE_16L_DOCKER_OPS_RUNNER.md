# Phase 16L: Docker Ops Runner Implementation

**Status:** ✅ Implemented  
**Date:** 2025-12-20  
**Scope:** Reproducible Stage1 Monitoring in Docker

---

## Motivation

Stage1 Monitoring (Daily Snapshot + Weekly Trend Reports) bisher nur host-native ausführbar.
Für CI/CD, Reproducibility und Isolation benötigt: Docker-Runner mit sauberem Volume-Handling.

**Goals:**
- Reports sauber per Volume nach Host schreiben
- Pfad-Handling robust: Default unverändert, aber per ENV/Flag übersteuerbar
- Keine Breaking Changes

---

## Implementation

### 1. Report Path Utilities

**New Module:** `src/utils/report_paths.py`

**Functions:**
- `get_repo_root()` - Finds repo root via pyproject.toml/uv.lock/.git
- `get_reports_root(default_rel="reports")` - Respects ENV `PEAK_REPORTS_DIR`
- `ensure_dir(p)` - mkdir -p equivalent

**Priority:**
1. CLI flag `--reports-root` (highest)
2. ENV `PEAK_REPORTS_DIR`
3. Default `reports&#47;` relative to repo root

### 2. Stage1 Scripts Enhanced

**Modified Scripts:**
- `scripts/obs/stage1_daily_snapshot.py`
- `scripts/obs/stage1_trend_report.py`

**Changes:**
- Added `--reports-root` optional flag
- Import `get_reports_root()` and `ensure_dir()`
- Backwards compatible: Default behavior unchanged

**Example:**
```bash
# Default (unchanged)
python3 scripts/obs/stage1_daily_snapshot.py

# ENV override
PEAK_REPORTS_DIR=/custom python3 scripts/obs/stage1_daily_snapshot.py

# CLI override (highest priority)
python3 scripts/obs/stage1_daily_snapshot.py --reports-root /custom
```

### 3. Docker Infrastructure

**New Files:**
- `docker/obs/Dockerfile` - Python 3.11-slim, uv install, frozen deps
- `docker/obs/entrypoint.sh` - Command dispatcher (stage1-snapshot, stage1-trends)
- `docker-compose.obs.yml` - Compose config with volume mount

**Image:**
- Base: `python:3.11-slim`
- Dependencies: Installed via `uv` from frozen `uv.lock`
- Default ENV: `PEAK_REPORTS_DIR=&#47;reports`
- Volume: `.&#47;reports:&#47;reports`

**Commands:**
```bash
# Build
docker compose -f docker-compose.obs.yml build

# Run snapshot
docker compose -f docker-compose.obs.yml run --rm peaktrade-ops stage1-snapshot

# Run trends with custom days
docker compose -f docker-compose.obs.yml run --rm peaktrade-ops stage1-trends --days 21

# Help
docker compose -f docker-compose.obs.yml run --rm peaktrade-ops --help
```

### 4. Convenience Scripts

**New Scripts:**
- `scripts/obs/run_stage1_snapshot_docker.sh`
- `scripts/obs/run_stage1_trends_docker.sh`

**Behavior:**
1. Build image (cached if no changes)
2. Run container with `.&#47;reports:&#47;reports` mount
3. Print output location

**Example:**
```bash
./scripts/obs/run_stage1_snapshot_docker.sh
# ✅ Reports written to: /Users/frnkhrz/Peak_Trade/reports/obs/stage1/
```

---

## Testing Strategy

### Unit Tests

**Test File:** `tests/test_report_paths.py`

**Coverage:**
- Default behavior (no ENV)
- ENV relative path
- ENV absolute path
- `ensure_dir()` creates directories

### Integration Testing

```bash
# Host execution (default)
python3 scripts/obs/stage1_daily_snapshot.py

# Docker execution
./scripts/obs/run_stage1_snapshot_docker.sh

# Verify output exists in same location
ls -lh reports/obs/stage1/
```

---

## Backwards Compatibility

### Guaranteed Unchanged Defaults

1. **No ENV, no flags:** Reports go to `./reports/obs/stage1/` (same as before)
2. **Existing flags:** `--repo`, `--out-dir`, `--days` all work unchanged
3. **Custom `--out-dir`:** Still works exactly as before

### New Capabilities (Additive)

1. **ENV `PEAK_REPORTS_DIR`:** Override default reports root
2. **CLI `--reports-root`:** Explicit override (highest priority)
3. **Docker runner:** Isolated, reproducible execution

---

## Output Structure

```
reports/obs/stage1/
├── 2025-12-20_snapshot.md      # Daily snapshot (markdown)
├── 2025-12-20_summary.json     # Daily snapshot (JSON, Phase 16K)
└── stage1_trend.json           # Weekly trend (JSON, Phase 16K)
```

**Both host and Docker produce identical output structure.**

---

## Use Cases

### 1. Local Development (Default)

```bash
python3 scripts/obs/stage1_daily_snapshot.py
# Output: reports/obs/stage1/2025-12-20_snapshot.md
```

### 2. CI/CD (Reproducible)

```bash
docker compose -f docker-compose.obs.yml run --rm peaktrade-ops stage1-snapshot
# Output: reports/obs/stage1/2025-12-20_snapshot.md (via volume mount)
```

### 3. Custom Reports Location

```bash
PEAK_REPORTS_DIR=/var/peak/reports ./scripts/obs/run_stage1_snapshot_docker.sh
# Output: /var/peak/reports/obs/stage1/2025-12-20_snapshot.md
```

### 4. GitHub Actions Integration

```yaml
- name: Run Stage1 Snapshot
  run: |
    docker compose -f docker-compose.obs.yml run --rm peaktrade-ops stage1-snapshot

- name: Upload Reports
  uses: actions/upload-artifact@v3
  with:
    name: stage1-reports
    path: reports/obs/stage1/
```

---

## Dependencies

**Runtime:**
- Python 3.11 (Docker image)
- `uv` for dependency management
- All Python deps from `pyproject.toml` (frozen via `uv.lock`)

**Build:**
- Docker (or Podman with Docker compat)
- docker-compose (or `docker compose` plugin)

---

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| **Breaking existing workflows** | Extensive backwards compat testing; defaults unchanged |
| **Volume mount issues (permissions)** | Docker runs as root, writes to host volume work by default |
| **ENV pollution on host** | Docker isolation; host execution unchanged |
| **Dependency drift (host vs Docker)** | Docker uses frozen `uv.lock`; host can use same |
| **Path resolution edge cases** | Unit tests cover relative/absolute paths |

---

## Future Work

### Phase 16M (Hypothetical)

- Stage2/Stage3 monitoring in Docker
- Scheduled Docker runs via cron/GitHub Actions
- Multi-arch Docker builds (arm64 support)

### Phase 16N (Hypothetical)

- Docker registry push (private/public)
- Kubernetes Job specs for Stage1 monitoring

---

## Verification Checklist

- [x] Unit tests pass (`tests/test_report_paths.py`)
- [x] Linter clean (`ruff check src tests scripts`)
- [x] Host execution unchanged (default behavior)
- [x] Docker execution produces identical output
- [x] ENV override works (host + Docker)
- [x] CLI flag override works (host + Docker)
- [x] Documentation updated (`docs/ops/README.md`)
- [x] Convenience scripts executable

---

## References

- **Issue/PR:** (to be filled when merged)
- **Related Phases:**
  - Phase 16K: Stage1 JSON output
  - Phase 16L: Docker Ops Runner (this document)
- **Related Docs:**
  - `docs/ops/README.md` - Operations Guide
  - `ADR_0001_Peak_Tool_Stack.md` - Tool stack decisions


## Canonical recovery note
Siehe: `docs/ops/DOCKER_RECOVERY_CANONICAL_STATE.md`

Kanonische Docker-/Prometheus-Pfade:
- `docker/compose.yml`
- `docker/docker-compose.obs.yml`
- `.local/prometheus/prometheus.docker.yml`
- `scripts/docker/run_l3_no_net.sh`

Historische Verweise auf entfernte `docs/webui/observability/DOCKER_COMPOSE_*.yml` sind Legacy.
