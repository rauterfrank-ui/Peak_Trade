# Peak_Trade – Docker (local)

Local MLflow tracking server for development and experimentation.

## Quick Start

### Prerequisites
- Docker & Docker Compose installed
- Port 5001 available (or customize via `docker/.env`)

### Start MLflow
```bash
make mlflow-up
# Or directly:
# docker compose -f docker/compose.yml up -d --build
```

### Access UI
http://localhost:5001

### Stop MLflow
```bash
make mlflow-down
# Or directly:
# docker compose -f docker/compose.yml down
```

### Full Reset (deletes all data)
```bash
make mlflow-reset
# Or directly:
# docker compose -f docker/compose.yml down -v
```

## Configuration

Edit `docker/.env` to customize (auto-created from `.env.example`):

```bash
# Port for MLflow UI (default: 5001)
MLFLOW_PORT=5001
```

**Note:** Port 5000 is often occupied by macOS AirPlay Receiver. Using 5001 avoids conflicts.

## Persistence

### What Persists Between Restarts
- **Experiments & Runs:** Stored in `mlruns/` volume
- **Artifacts:** Stored in `mlartifacts/` volume
- **Configuration:** `docker/.env` (gitignored, safe to customize locally)

### What Gets Deleted
- `make mlflow-down`: Stops container, **keeps data**
- `make mlflow-reset`: **Destroys volumes** (all experiments/artifacts lost)

Use `mlflow-reset` when you want a clean slate or to free disk space.

## Expected Warnings (Non-Critical)

When starting MLflow, you may see:

```
The "MLFLOW_BACKEND_STORE_URI" variable is not set. Defaulting to a blank string.
The "MLFLOW_DEFAULT_ARTIFACT_ROOT" variable is not set. Defaulting to a blank string.
```

**This is expected and safe.** MLflow defaults to file-based local storage (suitable for development). These warnings can be ignored unless you're configuring an external database backend.

## Troubleshooting

### Port Already in Use

**Symptoms:**
```
Error: bind: address already in use
```

**Solutions:**
1. Check if port 5001 is occupied:
   ```bash
   lsof -i :5001
   ```

2. Kill conflicting process or change port in `docker/.env`:
   ```bash
   MLFLOW_PORT=5002
   ```

3. On macOS, disable AirPlay Receiver if using port 5000:
   - System Preferences → Sharing → AirPlay Receiver (turn off)

### UI Not Reachable

**Checklist:**
- [ ] Container running? `docker ps | grep mlflow`
- [ ] Logs show errors? `make mlflow-logs`
- [ ] Port correct? Check `docker/.env` for `MLFLOW_PORT`
- [ ] Firewall blocking? Temporarily disable or allow port 5001

### Docker Not Found

**Error:**
```
docker: command not found
```

**Solution:** Install Docker Desktop:
- macOS: https://docs.docker.com/desktop/install/mac-install/
- Linux: https://docs.docker.com/engine/install/

### Container Crashes on Startup

**Steps:**
1. Check logs: `make mlflow-logs`
2. Try full reset: `make mlflow-reset && make mlflow-up`
3. Verify disk space: `df -h`

## Make Targets

| Command | Description |
|---------|-------------|
| `make mlflow-up` | Build & start MLflow container |
| `make mlflow-down` | Stop container (keeps data) |
| `make mlflow-logs` | Follow container logs (Ctrl+C to exit) |
| `make mlflow-reset` | **Destructive:** Remove container + volumes |
| `make mlflow-smoke` | Smoke test: log test run to verify setup |

## Notes

- **Dev/Local only:** Not production-ready (no external DB, no S3 artifacts)
- **No CI integration:** MLflow runs locally only (not in automated tests)
- **Data safety:** Volumes persist between restarts unless you use `mlflow-reset`
