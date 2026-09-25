#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

REPORT_DIR="${REPORT_DIR:-reports/rl_v0_1}"
mkdir -p "$REPORT_DIR"

LOG_FILE="$REPORT_DIR/validate_rl_v0_1.log"
JSON_FILE="$REPORT_DIR/validate_rl_v0_1.json"

utc_now() { date -u +"%Y-%m-%dT%H:%M:%SZ"; }

echo "[INFO] RL v0.1 validation started at $(utc_now)" | tee "$LOG_FILE"
echo "[INFO] Repo root: $ROOT_DIR" | tee -a "$LOG_FILE"
python -V | tee -a "$LOG_FILE" || true

# Required smoke test must exist (it is also run earlier in CI as Fast Lane)
if [[ ! -f "tests/test_rl_v0_1_smoke.py" ]]; then
  echo "[ERROR] Missing tests/test_rl_v0_1_smoke.py — cannot validate RL v0.1 contract." | tee -a "$LOG_FILE"
  cat > "$JSON_FILE" <<EOF
{"status":"failure","reason":"missing_smoke_test","ts":"$(utc_now)","log":"$LOG_FILE"}
EOF
  exit 1
fi

# SB3 is optional in v0.1: if missing -> PASS (exit 0)
if ! python - <<'PY' >/dev/null 2>&1
import importlib.util
raise SystemExit(0 if importlib.util.find_spec("stable_baselines3") else 1)
PY
then
  echo "[INFO] stable-baselines3 not installed; skipping RL v0.1 contract validation (v0.1 spec => PASS)." | tee -a "$LOG_FILE"
  cat > "$JSON_FILE" <<EOF
{"status":"skipped","reason":"stable_baselines3_not_installed","ts":"$(utc_now)","log":"$LOG_FILE"}
EOF
  exit 0
fi

echo "[INFO] stable-baselines3 detected; running RL v0.1 contract checks." | tee -a "$LOG_FILE"

# Run the smoke test (contract minimum)
set +e
pytest -q tests/test_rl_v0_1_smoke.py 2>&1 | tee -a "$LOG_FILE"
SMOKE_RC=${PIPESTATUS[0]}
set -e

# Optionally run additional RL v0.1 contract tests if they exist
EXTRA_RC=0
if compgen -G "tests/test_rl_v0_1_*contract*.py" > /dev/null; then
  echo "[INFO] Found additional contract tests: tests/test_rl_v0_1_*contract*.py" | tee -a "$LOG_FILE"
  set +e
  pytest -q tests/test_rl_v0_1_*contract*.py 2>&1 | tee -a "$LOG_FILE"
  EXTRA_RC=${PIPESTATUS[0]}
  set -e
else
  echo "[INFO] No additional contract tests found (tests/test_rl_v0_1_*contract*.py)." | tee -a "$LOG_FILE"
fi

RC=$(( SMOKE_RC != 0 || EXTRA_RC != 0 ))
if [[ "$RC" -ne 0 ]]; then
  echo "[ERROR] RL v0.1 validation FAILED (smoke_rc=$SMOKE_RC extra_rc=$EXTRA_RC)" | tee -a "$LOG_FILE"
  cat > "$JSON_FILE" <<EOF
{"status":"failure","reason":"pytest_failed","smoke_rc":$SMOKE_RC,"extra_rc":$EXTRA_RC,"ts":"$(utc_now)","log":"$LOG_FILE"}
EOF
  exit 1
fi

echo "[INFO] RL v0.1 validation PASSED" | tee -a "$LOG_FILE"
cat > "$JSON_FILE" <<EOF
{"status":"passed","ts":"$(utc_now)","log":"$LOG_FILE"}
EOF
exit 0
