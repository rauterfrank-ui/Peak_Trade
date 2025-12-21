# PR #150 MERGE LOG

- PR: #150
- Title: feat(dev): add local MLflow via docker compose + make targets (#150)
- Merged at (UTC): 2025-12-18T23:50:42Z
- Merge SHA (squash): 1538a5f
- Branch: feat/dev-mlflow-docker (deleted)
- Base: main
- PR URL: https://github.com/rauterfrank-ui/Peak_Trade/pull/150

## TL;DR

- ✅ Local MLflow tracking server via Docker Compose (MLflow 2.15.1)
- ✅ 5 new Makefile targets for MLflow lifecycle management
- ✅ Port 5001 default (avoids macOS AirPlay conflict on 5000)
- ✅ Post-merge smoke test successful with real experiment tracking

## CI Status

All checks passed:

- **tests (3.11):** ✅ PASS (3m44s)
- **audit:** ✅ PASS (1m44s)
- **guard-reports-ignored:** ✅ PASS (4s)
- **CI Health Gate:** ✅ PASS (47s)

## Changes Merged

Total: **6 files changed, 81 insertions(+)**

### New Files

1. **`docker/.env.example`** (2 lines)
   - Template for environment configuration
   - Sets `MLFLOW_PORT=5001` (macOS-friendly default)

2. **`docker/README.md`** (19 lines)
   - Usage documentation for MLflow Docker setup
   - Quick reference for make targets

3. **`docker/compose.yml`** (25 lines)
   - Docker Compose configuration for MLflow service
   - Volume mounts for persistence (`mlruns/`, `mlartifacts/`)
   - Health check configuration

4. **`docker/mlflow/Dockerfile`** (12 lines)
   - Python 3.11-slim base image
   - MLflow 2.15.1 installation
   - Minimal dependencies (ca-certificates only)

### Modified Files

5. **`.gitignore`** (+1 line)
   - Added `docker/.env` to prevent committing local config

6. **`Makefile`** (+22 lines)
   - `mlflow-up`: Build and start MLflow container
   - `mlflow-down`: Stop and remove container + network
   - `mlflow-logs`: Follow container logs (Ctrl+C to exit)
   - `mlflow-reset`: Full cleanup (containers + volumes)
   - `mlflow-smoke`: Verify tracking with test experiment

## Quickstart: Local MLflow Docker

### Prerequisites
- Docker installed and running
- Make available

### Setup & Usage

```bash
# 1) Create local .env (if not exists)
cp docker/.env.example docker/.env

# 2) Start MLflow
make mlflow-up
# → UI available at http://localhost:5001

# 3) Verify with smoke test
make mlflow-smoke
# → Logs test run to experiment "peak_trade_local_docker"

# 4) View logs (optional)
make mlflow-logs
# → Press Ctrl+C to exit

# 5) Stop MLflow
make mlflow-down

# 6) Full reset (removes volumes!)
make mlflow-reset
```

### Make Targets

| Target | Description |
|--------|-------------|
| `mlflow-up` | Build image, start container, create network |
| `mlflow-down` | Stop and remove container, remove network |
| `mlflow-logs` | Follow container logs (blocking) |
| `mlflow-reset` | **Destructive**: Remove all containers + volumes |
| `mlflow-smoke` | Smoke test: log dummy run to verify tracking works |

## Post-Merge Verification

Verified on 2025-12-19T00:54 UTC (immediately after merge):

### Environment Setup
- ✅ `docker/.env` created from template
- ✅ Port configured: 5001 (macOS AirPlay conflict on 5000 avoided)

### MLflow Container Lifecycle
- ✅ Build: Successful (MLflow 2.15.1, Python 3.11-slim)
- ✅ Start: Container `peak-trade-mlflow` running
- ✅ Logs: gunicorn 22.0.0 with 4 workers listening on 0.0.0.0:5000 (internal)
- ✅ UI: Accessible at http://localhost:5001

### Smoke Test Results
- ✅ Test experiment created: `peak_trade_local_docker`
- ✅ Experiment ID: `300764868224531398`
- ✅ Test run logged successfully
- ✅ Run ID: `de5f7d3f3e674a99bf0f5483b532b613`
- ✅ Run viewable at: http://localhost:5001/#/experiments/300764868224531398/runs/de5f7d3f3e674a99bf0f5483b532b613

### Expected Warnings (Non-Critical)
The following warnings are expected and acceptable for local dev:

```
The "MLFLOW_BACKEND_STORE_URI" variable is not set. Defaulting to a blank string.
The "MLFLOW_DEFAULT_ARTIFACT_ROOT" variable is not set. Defaulting to a blank string.
```

**Reason:** MLflow defaults to file-based local storage when these env vars are unset. This is appropriate for local development and matches the design intent of the PR.

### Cleanup
- ✅ `make mlflow-down` executed successfully
- ✅ Container stopped and removed
- ✅ Network removed

## Notes & Considerations

### Scope
- **Dev/Local only:** This setup is for local development and experimentation
- **Not production-ready:** No external database backend, no artifact storage config
- **No CI integration yet:** MLflow not used in automated tests (future consideration)

### Requirements
- **Docker dependency:** Users must have Docker installed and running
- **Port availability:** Default 5001 must be free (customizable via `docker/.env`)

### Data Persistence
- **Volumes:** `mlruns/` and `mlartifacts/` persist between container restarts
- **Destructive reset:** `make mlflow-reset` **deletes all experiment data** (use with caution)

### Future Enhancements
Potential follow-ups (not in scope for this PR):
- PostgreSQL backend for metadata store
- S3/MinIO for artifact storage
- Integration with existing backtesting runners
- Optional MLflow tracking in CI (for performance regression detection)

## Breaking Changes

None. This PR is purely additive:
- No changes to existing code or tests
- No impact on CI/CD pipelines
- Opt-in feature (must explicitly run `make mlflow-up`)

## Links

- **PR:** https://github.com/rauterfrank-ui/Peak_Trade/pull/150
- **Documentation:** `docker/README.md`
- **Makefile targets:** `Makefile` (lines with `mlflow-*`)
