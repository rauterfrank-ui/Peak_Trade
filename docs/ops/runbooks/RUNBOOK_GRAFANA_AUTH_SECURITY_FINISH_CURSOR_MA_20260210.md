# RUNBOOK_GRAFANA_AUTH_SECURITY_FINISH_CURSOR_MA_20260210

> Scope: Grafana Login (kein `admin/admin` mehr als Repo-Default) + Security-Baseline (Ports localhost-only, Remote-Access-Policy) + Verify-Skripte/Docs/Tests konsistent.
>
> Execution mode: Cursor Multi Agent Orchestrator (Bash-only).  
> Repo: Peak_Trade  
> Safety: Keine Secrets committen. Lokale `.env` nur untracked. Tokens bevorzugt für MCP/Cursor.

---

## Phase 0 — Preconditions (Read-only)

```bash
cd /Users/frnkhrz/Peak_Trade

git status -sb
git fetch origin --prune
git pull --ff-only origin main

# Optional: tags holen (nur wenn nötig)
git fetch origin --tags --prune

# Quick inventory of grafana-related compose + scripts + docs
ls -la DOCKER_COMPOSE_GRAFANA_ONLY.yml || true
ls -la docs/webui/observability/DOCKER_COMPOSE_*.yml || true

rg -n --hidden --glob '!**/.git/**' \
  'GF_SECURITY_ADMIN_(USER|PASSWORD)|GF_AUTH_ANONYMOUS|GF_USERS_ALLOW_SIGN_UP|admin:admin|admin/admin|GRAFANA_AUTH\=\"\$\{GRAFANA_AUTH:-admin:admin\}\"|GRAFANA_AUTH:-admin:admin' \
  DOCKER_COMPOSE_GRAFANA_ONLY.yml docs/webui/observability scripts/obs tests/obs docs -S
```

**Exit criteria:** Working tree clean, `rg` shows all relevant occurrences (Compose, scripts, docs, tests).

---

## Phase 1 — Create Work Branch (No code changes yet)

```bash
cd /Users/frnkhrz/Peak_Trade

git checkout -b feat/obs-grafana-auth-security
git status -sb
```

---

## Phase 2 — Decide Standard Policy (Fail-fast + Local `.env`)

**Policy (repo):**
- Compose must **not** hardcode `GF_SECURITY_ADMIN_PASSWORD`.
- Compose must require a password via env: `${GF_SECURITY_ADMIN_PASSWORD:?set}` (standardized on `GF_SECURITY_ADMIN_PASSWORD`).
- All local stacks must bind ports to `127.0.0.1` (Grafana + Prometheus + exporters).
- Docs: show `.env` + exports patterns; no secrets in git.
- Verify scripts: no default `admin:admin`; require `GRAFANA_AUTH` or `GRAFANA_TOKEN`.

---

## Phase 3 — Compose: Remove Hardcoded admin/admin + Require Env + Localhost Ports

### 3.1 Edit Root Compose: `DOCKER_COMPOSE_GRAFANA_ONLY.yml`

```bash
cd /Users/frnkhrz/Peak_Trade
cursor DOCKER_COMPOSE_GRAFANA_ONLY.yml
```

**Apply these rules:**
- `GF_SECURITY_ADMIN_USER: "${GF_SECURITY_ADMIN_USER:-admin}"`
- `GF_SECURITY_ADMIN_PASSWORD: "${GF_SECURITY_ADMIN_PASSWORD:?set GF_SECURITY_ADMIN_PASSWORD}"`
- Add:
  - `GF_USERS_ALLOW_SIGN_UP: "false"`
  - `GF_AUTH_ANONYMOUS_ENABLED: "false"`
- Ports:
  - `"127.0.0.1:3000:3000"`

### 3.2 Edit Docs Compose: `docs/webui/observability/DOCKER_COMPOSE_GRAFANA_ONLY.yml`

```bash
cd /Users/frnkhrz/Peak_Trade
cursor docs/webui/observability/DOCKER_COMPOSE_GRAFANA_ONLY.yml
```

Apply the same rules as 3.1.

### 3.3 Edit Prom+Grafana Compose: `docs/webui/observability/DOCKER_COMPOSE_PROM_GRAFANA.yml`

```bash
cd /Users/frnkhrz/Peak_Trade
cursor docs/webui/observability/DOCKER_COMPOSE_PROM_GRAFANA.yml
```

Apply:
- Remove hardcoded `GF_SECURITY_ADMIN_PASSWORD=admin`
- Require env (correct YAML style)
- Bind published ports to `127.0.0.1`:
  - Grafana 3000
  - Prometheus-local ports (9092/9093/9094/9095) if published
  - Any exporter ports (9109/9110) if published

### 3.4 Sanity grep after edits

```bash
cd /Users/frnkhrz/Peak_Trade

rg -n 'GF_SECURITY_ADMIN_PASSWORD\s*:\s*["'\'']admin["'\'']|GF_SECURITY_ADMIN_PASSWORD=admin|admin/admin|admin:admin' \
  DOCKER_COMPOSE_GRAFANA_ONLY.yml docs/webui/observability/DOCKER_COMPOSE_*.yml -S || true

rg -n '127\.0\.0\.1:3000:3000|127\.0\.0\.1:9092|127\.0\.0\.1:9093|127\.0\.0\.1:9094|127\.0\.0\.1:9095|127\.0\.0\.1:9109|127\.0\.0\.1:9110' \
  DOCKER_COMPOSE_GRAFANA_ONLY.yml docs/webui/observability/DOCKER_COMPOSE_*.yml -S || true
```

**Exit criteria:** No hardcoded admin password remains in Compose; ports are localhost-only where published.

---

## Phase 4 — Local Secrets: Add a Local `.env` Pattern (Untracked)

```bash
cd /Users/frnkhrz/Peak_Trade

PASS="$(openssl rand -base64 24 | tr -d '\n')"
cat > .env <<EOF
# Local-only. DO NOT COMMIT.
GF_SECURITY_ADMIN_USER=admin
GF_SECURITY_ADMIN_PASSWORD=${PASS}

# Verify scripts expect GRAFANA_AUTH in user:pass format (legacy) or token.
GRAFANA_AUTH=admin:${PASS}
EOF

printf "\n.env\n" >> .git/info/exclude
git status -sb
```

---

## Phase 5 — Verify Scripts: Remove Default admin:admin, Require Explicit Auth

```bash
cd /Users/frnkhrz/Peak_Trade
rg -n 'GRAFANA_AUTH\=\"\$\{GRAFANA_AUTH:-admin:admin\}\"|GRAFANA_AUTH\=\$\{GRAFANA_AUTH:-admin:admin\}|admin:admin' scripts/obs -S
```

Edit each hit (in Cursor) and:
- remove any `:-admin:admin` default
- require `GRAFANA_TOKEN` (preferred) or `GRAFANA_AUTH=user:pass`

Fail-fast snippet (paste near top of script):
```bash
if [[ -z "${GRAFANA_TOKEN:-}" ]]; then
  if [[ -z "${GRAFANA_AUTH:-}" && -n "${GF_SECURITY_ADMIN_USER:-}" && -n "${GF_SECURITY_ADMIN_PASSWORD:-}" ]]; then
    GRAFANA_AUTH="${GF_SECURITY_ADMIN_USER}:${GF_SECURITY_ADMIN_PASSWORD}"
  fi
fi

if [[ -z "${GRAFANA_TOKEN:-}" && -z "${GRAFANA_AUTH:-}" ]]; then
  echo "ERROR: Grafana auth missing. Set GRAFANA_TOKEN (preferred) or GRAFANA_AUTH=user:pass." >&2
  exit 2
fi
```

Post-edit:
```bash
cd /Users/frnkhrz/Peak_Trade
rg -n 'admin:admin|admin/admin|GRAFANA_AUTH:-admin:admin' scripts/obs -S || true
```

---

## Phase 6 — Docs: Remove admin/admin + Add Override Instructions

```bash
cd /Users/frnkhrz/Peak_Trade

rg -n 'admin:admin|admin/admin' docs/webui/observability docs/ops/runbooks docs/observability -S
```

Edit each hit:
- replace "admin/admin" with "use `.env` / exports"
- add a Credentials section in `docs/webui/observability/README.md`
- troubleshooting: 401 → auth vars; if correct but still 401 → volume drift; reset is destructive (dev-only)

---

## Phase 7 — Tests: Remove admin:admin Assumptions

```bash
cd /Users/frnkhrz/Peak_Trade
rg -n 'admin:admin|GRAFANA_AUTH' tests/obs -S
```

Edit test hits:
- remove reliance on `admin:admin` default
- set env explicitly for each test scenario

Run:
```bash
cd /Users/frnkhrz/Peak_Trade
pytest -q tests/obs -ra
```

---

## Phase 8 — Local Stack Validation (Dev-only)

```bash
cd /Users/frnkhrz/Peak_Trade

docker compose -f DOCKER_COMPOSE_GRAFANA_ONLY.yml up -d
docker ps --format 'table {{.Names}}\t{{.Ports}}' | rg -n 'grafana|3000' || true

export GRAFANA_AUTH="$(rg -n '^GRAFANA_AUTH=' .env | sed -E 's/^GRAFANA_AUTH=//')"
./scripts/obs/grafana_local_verify.sh
./scripts/obs/grafana_verify_v2.sh

docker compose -f DOCKER_COMPOSE_GRAFANA_ONLY.yml down
```

If 401 and you accept destructive reset:
```bash
cd /Users/frnkhrz/Peak_Trade
./scripts/obs/grafana_local_down.sh || true
docker compose -f DOCKER_COMPOSE_GRAFANA_ONLY.yml down -v || true
docker compose -f DOCKER_COMPOSE_GRAFANA_ONLY.yml up -d
export GRAFANA_AUTH="$(rg -n '^GRAFANA_AUTH=' .env | sed -E 's/^GRAFANA_AUTH=//')"
./scripts/obs/grafana_local_verify.sh
docker compose -f DOCKER_COMPOSE_GRAFANA_ONLY.yml down
```

---

## Phase 9 — Lint/Test Gates

```bash
cd /Users/frnkhrz/Peak_Trade

ruff format --check src tests scripts || true
ruff check src tests scripts || true
pytest -q -ra
```

---

## Phase 10 — Commit + PR

```bash
cd /Users/frnkhrz/Peak_Trade

git add -A
git diff --cached --stat

git commit -m "obs(grafana): require env creds, remove admin/admin defaults; localhost-only ports; align verify+docs+tests"

git push -u origin feat/obs-grafana-auth-security

# If gh works:
gh pr create --fill --base main --head feat/obs-grafana-auth-security
```

---

## Phase 11 — Post-Merge Closeout

```bash
cd /Users/frnkhrz/Peak_Trade

git checkout main
git fetch origin --prune
git pull --ff-only origin main

git branch -d feat/obs-grafana-auth-security
git push origin --delete feat/obs-grafana-auth-security || true

git status -sb
```

---

## Finish Criteria Checklist

```bash
cd /Users/frnkhrz/Peak_Trade

rg -n 'admin:admin|admin/admin|GF_SECURITY_ADMIN_PASSWORD\s*:\s*["'\'']admin["'\'']|GF_SECURITY_ADMIN_PASSWORD=admin' \
  DOCKER_COMPOSE_GRAFANA_ONLY.yml docs/webui/observability scripts/obs docs tests -S || true

docker ps --format 'table {{.Names}}\t{{.Ports}}' | rg -n '3000|9092|9093|9094|9095|9109|9110' || true

pytest -q -ra
```
