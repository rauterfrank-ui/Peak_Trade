# PR #152 MERGE LOG

- PR: #152
- Title: docs(dev): polish local MLflow docker quickstart
- Merged at (UTC): 2025-12-19T00:08:40Z
- Merge SHA (squash): a8c124f
- Branch: chore/mlflow-docker-polish (deleted)
- Base: main
- PR URL: https://github.com/rauterfrank-ui/Peak_Trade/pull/152

## TL;DR

- ✅ Documentation-only polish for local MLflow Docker setup (PR #150 follow-up)
- ✅ Added comprehensive troubleshooting guide
- ✅ Explained expected MLflow warnings (non-critical)
- ✅ Documented persistence behavior and port configuration

## CI Status

All checks passed:

- **tests (3.11):** ✅ PASS (3m34s)
- **audit:** ✅ PASS (1m51s)
- **strategy-smoke:** ✅ PASS (47s)
- **CI Health Gate:** ✅ PASS (44s)

## Scope

**Documentation-only changes.** No functional modifications to code, tests, or infrastructure.

This PR enhances the user experience for PR #150 (MLflow Docker setup) by adding:
- Clear troubleshooting guidance
- Port configuration best practices
- Explanation of expected warnings
- Persistence behavior documentation

## Changes Merged

Total: **1 file changed, 121 insertions(+), 7 deletions(-)**

### Modified Files

**`docker/README.md`** (+121 lines, -7 lines, net +114 lines)

Expanded from minimal quickstart to comprehensive documentation:

#### New Sections Added

1. **Quick Start Improvements**
   - Prerequisites (Docker, port availability)
   - `make` targets as primary interface (with raw `docker-compose` fallback)
   - Clear distinction: `mlflow-down` (keeps data) vs `mlflow-reset` (destroys data)

2. **Configuration**
   - How to customize `docker/.env`
   - **Port 5001 default** - explicitly documented to avoid macOS AirPlay Receiver conflict on port 5000
   - Instructions to change port if needed (edit `docker/.env`)

3. **Persistence**
   - What persists between restarts: `mlruns&#47;`, `mlartifacts&#47;` volumes, `.env`
   - What gets deleted: `mlflow-down` vs `mlflow-reset` behavior comparison
   - Clear warning about data loss with `make mlflow-reset`

4. **Expected Warnings (Non-Critical)**
   - Explains `MLFLOW_BACKEND_STORE_URI` / `MLFLOW_DEFAULT_ARTIFACT_ROOT` warnings
   - Confirms: file-based storage is **intentional** for local dev
   - Users can safely ignore these warnings

5. **Troubleshooting**
   - **Port conflicts:** Check `lsof -i :5001`, change port in `docker/.env`, disable macOS AirPlay
   - **UI not reachable:** Checklist (container status, logs, port, firewall)
   - **Docker not found:** Installation links for macOS/Linux
   - **Container crashes:** Diagnostic steps (logs, reset, disk space)

6. **Make Targets Reference**
   - Table format with all 5 MLflow targets
   - Clear **"Destructive"** label on `mlflow-reset`

7. **Notes**
   - Dev/local scope (not production-ready)
   - No CI integration
   - Data safety reminder

## Port Configuration Details

### Default: Port 5001

**Why not 5000?**
- macOS AirPlay Receiver often occupies port 5000
- Port 5001 avoids conflicts out-of-the-box

**How to change:**
```bash
# Edit docker/.env
MLFLOW_PORT=5002
```

### Troubleshooting Port Conflicts

1. Check if port occupied:
   ```bash
   lsof -i :5001
   ```

2. Change port in `docker/.env` or disable AirPlay:
   - System Preferences → Sharing → AirPlay Receiver (turn off)

## MLflow Warnings Explained

The README now documents that these warnings are **expected and safe**:

```
The "MLFLOW_BACKEND_STORE_URI" variable is not set. Defaulting to a blank string.
The "MLFLOW_DEFAULT_ARTIFACT_ROOT" variable is not set. Defaulting to a blank string.
```

**Reason:** MLflow defaults to file-based local storage when these env vars are unset. This is the intended behavior for local development. Users should ignore these warnings unless configuring an external database backend.

## Persistence Behavior

The README clarifies data persistence:

| Command | Container | Data (Volumes) |
|---------|-----------|----------------|
| `make mlflow-down` | Stops & removes | **Keeps** |
| `make mlflow-reset` | Stops & removes | **Destroys** |

**What persists:**
- Experiments & runs (`mlruns&#47;` volume)
- Artifacts (`mlartifacts&#47;` volume)
- Configuration (`docker/.env` - gitignored)

**Use `mlflow-reset` when:**
- You want a clean slate
- Freeing disk space

## Make Targets Documentation

The README includes a reference table:

| Command | Description |
|---------|-------------|
| `make mlflow-up` | Build & start MLflow container |
| `make mlflow-down` | Stop container (keeps data) |
| `make mlflow-logs` | Follow container logs (Ctrl+C to exit) |
| `make mlflow-reset` | **Destructive:** Remove container + volumes |
| `make mlflow-smoke` | Smoke test: log test run to verify setup |

## Benefits

This documentation polish provides:

1. **New user onboarding:** Clear prerequisites and quickstart
2. **Troubleshooting:** Self-service diagnostic guidance
3. **Port conflicts:** Proactive documentation (macOS AirPlay)
4. **Warning clarity:** Prevents confusion about expected MLflow warnings
5. **Data safety:** Clear warnings about destructive operations
6. **Best practices:** `make` targets as recommended interface

## Notes

### Scope
- **Docs-only:** No code, test, or infrastructure changes
- **Follow-up to PR #150:** Completes MLflow Docker setup with user documentation
- **Safe to merge:** Zero risk of breaking changes

### Testing
- Documentation verified for:
  - Markdown rendering
  - Valid links
  - Copy-pasteable commands

### No Breaking Changes
- Pure documentation additions
- No impact on existing functionality
- No test changes required

## Links

- **PR:** https://github.com/rauterfrank-ui/Peak_Trade/pull/152
- **Original PR (MLflow Docker):** https://github.com/rauterfrank-ui/Peak_Trade/pull/150
- **Updated Documentation:** `docker/README.md`
