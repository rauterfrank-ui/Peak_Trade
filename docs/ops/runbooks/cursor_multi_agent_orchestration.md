# Runbook (Fortsetzung): Cursor Multi-Agent Orchestration — Peak_Trade

> **Ziel**: Stabiler, reproduzierbarer Cursor-MA-Betrieb (offline-first), mit klaren Phasen, Entry/Exit-Kriterien, Observability, Safety-Gates, Rollback.
> **Scope**: L0–L5 (Execution/L6 bleibt verboten).

---

## Phase 2 — Preflight: Host & Toolchain Verifikation

### Entry
- Repo ist sauber (`git status` clean).
- Docker Desktop läuft.

### Steps (Commands)
```bash
# Versions / Baselines
uname -a
sw_vers
python3 --version
git --version
docker version
docker compose version

# Disk / RAM grob
df -h
sysctl -n hw.memsize 2>/dev/null || true

# Ports, die wir typischerweise brauchen (anpassen falls ihr anders mapped):
# grafana:3000, prom:9090/9092/9094/9095, exporters:9109/9110/9111, web:8000
lsof -nP -iTCP -sTCP:LISTEN | egrep ':(3000|8000|9090|9092|9094|9095|9109|9110|9111)\b' || true
```

### Kandidaten (Pfade an euer Repo anpassen)
```bash
ls -la docs/ops 2>/dev/null || true
find . -maxdepth 4 -type f \( -name '*runner*.py' -o -name '*.toml' -o -name '*governance*' -o -name '*critic*' \) | sed 's|^\./||'
```

### Quick Sanity: TOML-Parse (tomllib, Py3.11+)
```bash
python3 - <<'PY'
import sys, pathlib
try:
    import tomllib
except Exception as e:
    print("tomllib not available:", e); sys.exit(0)
files = [p for p in pathlib.Path(".").rglob("*.toml")]
bad = 0
for p in files:
    try:
        tomllib.loads(p.read_bytes())
    except Exception as e:
        bad += 1
        print("BAD", p, e)
print("TOML files:", len(files), "bad:", bad)
sys.exit(1 if bad else 0)
PY
```

### Grep: L6 / Execution-Policy (nur Hinweis; sicherstellen, dass verboten bleibt)
```bash
rg -n "L6|execution.*forbid|LIVE.*block|armed|confirm token|dry[- ]run" -S . || true
```

### Compose-Projekte & Stack-Status
```bash
# Alle Compose-Projekte finden (üblich: docker-compose.yml / compose.yml)
find . -maxdepth 4 -type f \( -name 'docker-compose.yml' -o -name 'compose.yml' \) -print

# Falls ihr eine Start-Wrapper-Struktur habt:
ls -la scripts 2>/dev/null || true
find scripts -maxdepth 3 -type f -name '*.sh' -print 2>/dev/null || true

# Compose-Stacks-Status (alle Profile/Projekte die ihr nutzt)
docker compose ls

# Falls ihr bekannte Projekt-Dirs habt (Beispiele; anpassen):
for d in peaktrade-shadow-mvs peaktrade-ai-live-ops peaktrade-observability; do
  [ -d "$d" ] && (echo "== $d =="; (cd "$d" && docker compose ps)) || true
done

# Prom-Targets-Check (falls vorhanden)
[ -x scripts/ops/prom_targets_check.sh ] && ./scripts/ops/prom_targets_check.sh || true

# Grafana/Prom HTTP-Sanity (Ports anpassen)
curl -fsS http://localhost:3000/login >/dev/null && echo "grafana: OK" || echo "grafana: DOWN"
curl -fsS http://localhost:9090/-/ready  >/dev/null && echo "prom: OK"    || echo "prom: DOWN"
```

## Prometheus 9094/9095 nicht gebunden (AI-Live/Observability)

**Ursache „9094/9095 nicht gebunden“:** Wenn `peaktrade-obse` und `peaktrade-ai-live` (bzw. `peaktrade-observability` / `peaktrade-ai-live-ops`) **nicht** „Up“ sind, bindet Docker die Ports `9095:9090` und `9094:9090` nicht.

Diagnose + Start (in einem Schritt):

```bash
./scripts/obs/prom_9094_9095_up_and_verify.sh
```

Das Skript macht:
1) `docker compose ls` (Projektnamen erkennen)
2) `ps` + `logs --tail=200` für OBSE (9095) und AILIVE (9094)
3) `docker compose ... up -d` für beide
4) Port-Check via `lsof` (9094/9095) + `curl http:&#47;&#47;localhost:9094&#47;-&#47;ready` und `:9095&#47;-&#47;ready`

**Projekt-Erkennung:** Namen aus `docker compose ls` (enthält „observability“/„obse“ → OBSE; enthält „ai-live“ → AILIVE). Fallback: `peaktrade-observability` und `peaktrade-ai-live-ops`.

**Falls du mit eigenen `-f` Compose-Dateien startest:**

```bash
OBSE_COMPOSE="-f /pfad/zu/compose.obse.yml" \
AILIVE_COMPOSE="-f /pfad/zu/compose.ai-live.yml" \
./scripts/obs/prom_9094_9095_up_and_verify.sh
```

**Wenn 9094/9095 spinnen oder Prometheus „stuck“ ist:** OBSE + AILIVE sauber neu starten (ohne Volumes zu löschen). Entweder das Helper-Skript ausführen:

```bash
./scripts/obs/prom_9094_9095_restart.sh
```

Oder manuell: Projektnamen aus `docker compose ls` (OBSE = observability/obse, AILIVE = ai-live), dann `docker compose -p <OBSE> restart` bzw. `-p <AILIVE> restart`; reicht das nicht, `down` (ohne `-v`) und `up -d` für beide, danach Ports und `curl http:&#47;&#47;localhost:9094&#47;-&#47;ready` / `:9095&#47;-&#47;ready` prüfen. Bei FAIL: `logs --tail=200` für beide Stacks.

### Lokale Compose-Overrides (Ports 9094/9095) – ohne manuelles `-f`
Wenn `peaktrade-observability` / `peaktrade-ai-live-ops` nach einem `down` nicht mehr in `docker compose ls` auftauchen, nutzen die Helper-Skripte einen Fallback.

**Empfohlen:** Lege auf deinem Host lokale Overrides an (werden nicht versioniert):

- `.ops_local&#47;compose_overrides&#47;observability.prom.override.yml` → published Port `9095:9090`
- `.ops_local&#47;compose_overrides&#47;ai-live.prom.override.yml` → published Port `9094:9090`

Die Skripte wählen diese Overrides automatisch (ohne manuelle `OBSE_COMPOSE`/`AILIVE_COMPOSE`).

### Orchestrator lokalisieren & Smoke-Run
```bash
# Orchestrator / Runner / Gates (Beispiele; anpassen)
rg -n "Orchestrator|multi[- ]agent|agent.*matrix|L0|L1 Runner|L2 Runner|L4 Critic|Risk Gate" -S src scripts . || true

# Smoke-Run: Help / CLI
python3 -m src 2>/dev/null || true
python3 -c "import pkgutil; print('ok')" >/dev/null

# Falls Runner-Skripte existieren (Beispiele)
[ -f l1_runner.py ] && python3 l1_runner.py --help || true
[ -f l2_runner.py ] && python3 l2_runner.py --help || true

# Dry-Run / No-Network Env-Hardening (best-effort)
export PEAK_TRADE_MODE=research
export PEAK_TRADE_LIVE=0
export PEAK_TRADE_EXECUTION_FORBIDDEN=1
export PEAK_TRADE_DRY_RUN=1

# Minimaler "No-Op"-Lauf (nur wenn ein passender CLI existiert)
# python3 l1_runner.py --dry-run --config configs/L1_deep_research.toml
# python3 l2_runner.py --dry-run --config configs/L2_market_outlook.toml
```

### Tests, Lint & Minimal-Audit
```bash
# Tests
pytest -q || true

# Lint/Format (wenn vorhanden)
pre-commit run -a || true

# Minimal-Audit: keine Secrets im Repo
rg -n "OPENAI_API_KEY|API_KEY|SECRET|TOKEN" -S . || true
git status
```

### Exit / Teardown (Compose down, Cleanup, Repo-Reset)
```bash
# 1) Compose down (pro Projekt)
for d in peaktrade-shadow-mvs peaktrade-ai-live-ops peaktrade-observability; do
  [ -d "$d" ] && (cd "$d" && docker compose down --remove-orphans) || true
done

# 2) Hard stop: verbleibende Listener anzeigen
lsof -nP -iTCP -sTCP:LISTEN | egrep ':(3000|8000|9090|9092|9094|9095|9109|9110|9111)\b' || true

# 3) Docker-Cleanup (vorsichtig)
docker system df
# docker system prune -f   # nur wenn wirklich nötig

# 4) Repo-Reset (nur Working Tree)
git status
# git restore --staged .
# git restore .

# Optional: Änderungen committen
# git add docs/ops/runbooks/cursor_multi_agent_orchestration.md
# git commit -m "docs(runbook): continue cursor multi-agent orchestration phases 2-7"
```

---

## Phase 8 — Hardening & Scale-Out (Extension Points)

### Entry
- Phasen 2–6 stabil (Dry-Run grün, Observability grün).
- Keine LIVE-Flags/Execution bleibt blockiert.

### Steps (Commands)
```bash
# 1) Deterministic env snapshot
python3 -VV
pip --version || true
pip freeze | sort > /tmp/requirements.freeze.txt
sha256sum /tmp/requirements.freeze.txt 2>/dev/null || shasum -a 256 /tmp/requirements.freeze.txt

# 2) Repro config snapshot
git rev-parse HEAD
git status --porcelain
find . -maxdepth 5 -type f \( -name '*.toml' -o -name '*.yml' -o -name '*.yaml' -o -name '*.json' \) -print0 2>/dev/null | tar -czf /tmp/peaktrade_configs_snapshot.tgz --null -T -

# macOS/BSD tar fallback (no --null): NOTE: loses NUL-safety; prefer GNU tar for weird paths.
# find . -maxdepth 5 -type f \( -name '*.toml' -o -name '*.yml' -o -name '*.yaml' -o -name '*.json' \) -print 2>/dev/null | LC_ALL=C sort > /tmp/peaktrade_configs_files.list
# tar -czf /tmp/peaktrade_configs_snapshot.tgz -T /tmp/peaktrade_configs_files.list

# 3) Observability baseline
[ -x scripts/ops/prom_targets_check.sh ] && ./scripts/ops/prom_targets_check.sh || true
curl -fsS http://localhost:9090/api/v1/targets | head -c 2000 || true
```

---

## Phase 9 — Release Artifact Bundle (Portable Deliverable)

### Entry
- Runbook ist auf `main` gemerged und getaggt (z. B. `runbook-cursor-ma-v1`).
- Lokale Quarantäne ist aktiv (`.scratch&#47;` in `.gitignore`).
- Optionaler Worktree-Snapshot wurde extern gesichert (tgz + sha256).

### Steps (Commands)
```bash
# 1) Build a portable bundle (local-only; do NOT commit artifacts)
cd ~/Downloads
mkdir -p /tmp/release_bundle_cursor_ma_v1

cp -v \
  cursor_multi_agent_orchestration_runbook.zip \
  cursor_multi_agent_orchestration_runbook.zip.sha256 \
  grafana_ds_fix_worktree_snapshot.tgz \
  grafana_ds_fix_worktree_snapshot.tgz.sha256 \
  release_runbook_cursor_ma_v1.txt \
  release_runbook_cursor_ma_v1.txt.sha256 \
  scratch_manifest.txt \
  scratch_manifest.txt.sha256 \
  /tmp/release_bundle_cursor_ma_v1/

tar -czf /tmp/release_bundle_cursor_ma_v1.tgz -C /tmp release_bundle_cursor_ma_v1

# 2) Bundle checksum (path-agnostic)
cd /tmp
H="$(shasum -a 256 release_bundle_cursor_ma_v1.tgz | awk '{print $1}')"
printf "%s  %s\n" "$H" "release_bundle_cursor_ma_v1.tgz" > release_bundle_cursor_ma_v1.tgz.sha256
shasum -a 256 -c release_bundle_cursor_ma_v1.tgz.sha256

# 3) Optional: copy to Downloads for sharing
cp -v /tmp/release_bundle_cursor_ma_v1.tgz* ~/Downloads/
ls -la ~/Downloads/release_bundle_cursor_ma_v1.tgz*
```

### Evidence pack (repo metadata)

Minimales Evidence-Paket nur aus Repo-Metadaten (Commits, Tags, Status); intern teilbar, keine Source-Artefakte.

```bash
# 1) Record relevant commits + tags
git fetch origin --tags --prune
git log --oneline -n 20
git tag --list | rg 'runbook-cursor-ma' || true
git show runbook-cursor-ma-v1 --no-patch || true

# 2) Minimal evidence pack (repo metadata only; safe to share internally)
mkdir -p /tmp/evidence_pack_cursor_ma_v1
git rev-parse HEAD > /tmp/evidence_pack_cursor_ma_v1/HEAD.txt
git status -sb > /tmp/evidence_pack_cursor_ma_v1/status.txt
git log --oneline -n 50 > /tmp/evidence_pack_cursor_ma_v1/log_50.txt
git show --name-only --oneline 70745c8b > /tmp/evidence_pack_cursor_ma_v1/merge_runbook_1133.txt 2>/dev/null || true
git show --name-only --oneline 2aa7445b > /tmp/evidence_pack_cursor_ma_v1/merge_ignore_scratch_1134.txt 2>/dev/null || true

tar -czf /tmp/evidence_pack_cursor_ma_v1.tgz -C /tmp evidence_pack_cursor_ma_v1
H="$(shasum -a 256 /tmp/evidence_pack_cursor_ma_v1.tgz | awk '{print $1}')"
printf "%s  %s\n" "$H" "evidence_pack_cursor_ma_v1.tgz" > /tmp/evidence_pack_cursor_ma_v1.tgz.sha256
shasum -a 256 -c /tmp/evidence_pack_cursor_ma_v1.tgz.sha256

ls -la /tmp/evidence_pack_cursor_ma_v1.tgz /tmp/evidence_pack_cursor_ma_v1.tgz.sha256
```

### Verification (Consumer)

Nach Erhalt des Bundles (`release_bundle_cursor_ma_v1.tgz` + `.sha256`): Integrität prüfen, entpacken und enthaltene Artifakte verifizieren.

```bash
cd ~/Downloads

# 1) Verify bundle itself
shasum -a 256 -c release_bundle_cursor_ma_v1.tgz.sha256

# 2) Extract bundle
rm -rf /tmp/release_bundle_cursor_ma_v1_extract
mkdir -p /tmp/release_bundle_cursor_ma_v1_extract
tar -xzf release_bundle_cursor_ma_v1.tgz -C /tmp/release_bundle_cursor_ma_v1_extract

# 3) Verify included artifacts (all sha256 files are basename-only)
cd /tmp/release_bundle_cursor_ma_v1_extract/release_bundle_cursor_ma_v1
for f in *.sha256; do shasum -a 256 -c "$f"; done

# 4) Inspect contents
ls -la
unzip -l cursor_multi_agent_orchestration_runbook.zip
tar -tzf grafana_ds_fix_worktree_snapshot.tgz | head -n 30
```

### Rollback — Option 1: Revert squash-merge (preferred; auditable)

Rücknahme eines gemergten Commits per `git revert`; erzeugt einen neuen, nachvollziehbaren Commit. Commit-SHA von `origin&#47;main` verwenden (z. B. aus Evidence Pack oder `git log`).

```bash
# - pick the commit sha from origin&#47;main (examples)
#   - runbook merge: 70745c8b...
#   - ignore scratch: 2aa7445b...
git fetch origin --prune
git checkout -b revert/runbook-or-scratch
git revert <COMMIT_SHA_TO_REVERT>

git push -u origin revert/runbook-or-scratch
gh pr create \
  --base main \
  --head revert/runbook-or-scratch \
  --title "revert: <short reason>" \
  --body $'Reverts commit <COMMIT_SHA_TO_REVERT> due to <reason>.'

PR_NUM="$(gh pr view --json number -q .number)"
gh pr checks "$PR_NUM" --watch
# gh pr merge "$PR_NUM" --squash --delete-branch
```

### PR workflow (runbook phases 9–12)

Branch erstellen, PR gegen `main` öffnen (Branch-Protection), Checks abwarten, bei Grün squash-mergen, lokales `main` zurücksetzen.

```bash
# open PR (main protected)
git checkout -b docs/runbook-cursor-ma-phases-9-12
git push -u origin docs/runbook-cursor-ma-phases-9-12

gh pr create \
  --base main \
  --head docs/runbook-cursor-ma-phases-9-12 \
  --title "docs(runbook): add phases 9–12 (bundle, consumer verify, evidence, rollback)" \
  --body $'Extends cursor_multi_agent_orchestration.md with:\n- Phase 9: portable release bundle\n- Phase 10: consumer verification workflow\n- Phase 11: minimal repo-level evidence pack\n- Phase 12: rollback via revert PR\n\nArtifacts remain local-only (not committed).'

PR_NUM="$(gh pr view --json number -q .number)"
gh pr checks "$PR_NUM" --watch
# merge when green
gh pr merge "$PR_NUM" --squash --delete-branch

# resync
git checkout main
git fetch origin --prune
git reset --hard origin&#47;main
```

---

## Phase 13 — Maintenance: Drift Detection & Repro Baseline (Recurring)

### Entry
- `main` clean, stacks (falls genutzt) sind stabil.
- Ziel: frühzeitig Config/Env-Drift erkennen, ohne Live/Execution zu berühren.

### Steps (Commands)
```bash
# 1) Repo baseline snapshot (metadata-only)
git fetch origin --tags --prune
git rev-parse HEAD
git status -sb
git log --oneline -n 20

# 2) Dependency drift (best-effort; skip if no venv)
python3 -VV
pip --version || true
pip freeze | sort > /tmp/pip_freeze.sorted.txt
shasum -a 256 /tmp/pip_freeze.sorted.txt

# 3) Config drift (tracked config files)
git ls-files \
  | rg "\.(toml|ya?ml|json)$" \
  | sort > /tmp/tracked_configs.list

tar -czf /tmp/tracked_configs_snapshot.tgz -T /tmp/tracked_configs.list
shasum -a 256 /tmp/tracked_configs_snapshot.tgz

# 4) Prom/Grafana baseline (if running)
[ -x scripts/ops/prom_targets_check.sh ] && ./scripts/ops/prom_targets_check.sh || true
curl -fsS http://localhost:9090/-/ready >/dev/null && echo "prom: OK" || true
curl -fsS http://localhost:3000/login >/dev/null && echo "grafana: OK" || true
```

### Exit
- Snapshots/Checksums in `/tmp` (oder dokumentierter Ort) für spätere Vergleiche gesichert.
- Keine Änderung an Live/Execution.

---

## Phase 14 — Drift Review & Remediation

### Entry
- Phase-13-Baseline wurde mindestens einmal erstellt.
- Neuer Lauf (z. B. nach `git pull` oder Env-Änderung) durchgeführt; neue Snapshots in `/tmp` vorhanden.

### Steps (Commands)
```bash
# 1) Repo-Vergleich (Commit/Branch)
git fetch origin --tags --prune
git rev-parse HEAD
git log --oneline -n 5
# Diff gegen gespeicherte HEAD/status aus Phase 13 (manuell vergleichen oder diff /tmp/status_old.txt <(git status -sb))

# 2) Dependency-Vergleich (pip freeze)
# Vorher: Baselines aus Phase 13 archivieren (z. B. pip_freeze.sorted.txt → pip_freeze.baseline.txt)
pip freeze | sort > /tmp/pip_freeze.current.txt
diff -u /tmp/pip_freeze.baseline.txt /tmp/pip_freeze.current.txt || true

# 3) Config-Snapshot-Vergleich (Checksum oder tar diff)
# Baselines: tracked_configs_snapshot.tgz + .sha256 aus Phase 13 behalten
shasum -a 256 /tmp/tracked_configs_snapshot.tgz
# Bei Abweichung: tar -tzf /tmp/tracked_configs_snapshot.tgz | sort vs. Baseline-Listing

# 4) Entscheidung
# Kein Drift → nichts tun. Drift → Ursache klären (Intent vs. Versehen), ggf. PR für bewusste Änderung, Rollback/Revert bei Versehen.
```

### Exit
- Drift dokumentiert; bewusste Änderungen in PR/Commit, versehentliche rückgängig gemacht.

---

## Phase 15 — CI Docs-Gate Workflow

### Entry
- Runbook/Phasen auf `main`; Branch-Protection für `main` aktiv.
- Ziel: Docs- und Runbook-Änderungen müssen CI (Lint/Docs-Build) bestehen, bevor Merge.

### Steps (Commands)
```bash
# 1) Branch-Protection prüfen (GitHub; erforderliche Status-Checks)
gh api repos/:owner/:repo/branches/main/protection 2>/dev/null | jq '.required_status_checks.contexts' || true

# 2) Docs-relevante CI-Jobs (Beispiele; anpassen an eure Workflow-Namen)
gh workflow list
ls -la .github/workflows/*.yml 2>/dev/null | head -20

# 3) Lokaler Docs-Gate (vor Push): Lint + ggf. Docs-Build
pre-commit run --all-files || true
# Falls MkDocs/Quarto/Sphinx: mkdocs build / quarto render / sphinx-build (je nach Stack)
[ -f mkdocs.yml ] && mkdocs build --strict 2>/dev/null || true

# 4) PR erstellen; CI muss grün sein
git checkout -b docs/runbook-phase-13-16
git add docs/ops/runbooks/cursor_multi_agent_orchestration.md
git commit -m "docs(runbook): add phases 13–16 (maintenance, drift, CI docs-gate, incident playbook)"
git push -u origin docs/runbook-phase-13-16
gh pr create --base main --head docs/runbook-phase-13-16 \
  --title "docs(runbook): phases 13–16" \
  --body "Phase 13: drift detection & repro baseline. Phase 14: drift review. Phase 15: CI docs-gate. Phase 16: incident playbook."
gh pr checks --watch
# Nach Grün: gh pr merge --squash --delete-branch
```

### Token-Policy (Slash in Inline-Code) — lokal wie CI

Docs-Token-Policy lokal wie in CI prüfen; typische Verstöße: Pfade in Inline-Code mit `/` statt `&#47;`.

```bash
# 1) Reproduce locally exactly like CI
python3 scripts/ops/validate_docs_token_policy.py --base origin/main

# 2) Identify common inline-code violations (ILLUSTRATIVE)
# - Inline code with path-like tokens must use &#47; instead of /
rg -n "``[^`]*\/[^`]*``" docs -S || true

# 3) Typical fixes (edit intentionally)
# - `origin/main` -> `origin&#47;main`
# - `.scratch/`   -> `.scratch&#47;`

# confirm after fix
python3 scripts/ops/validate_docs_token_policy.py --base origin/main
```

### Exit
- Nur PRs mit grüner CI gemerged; Runbook-Änderungen durch Docs-Gate abgesichert.
- Token-Policy lokal bestanden (Slash in Inline-Code als `&#47;`).

---

## Phase 16 — Incident Playbook

### Entry
- Störung oder unerwartetes Verhalten (z. B. Agent-Lauf, Observability, Config, CI).

### Steps (Commands)

**1) Detection & Triage**
```bash
# Schnell-Check: Repo, Prozesse, Ports
git status -sb
git log --oneline -n 3
lsof -nP -iTCP -sTCP:LISTEN | egrep ':(3000|8000|9090|9092|9094|9095|9109|9110|9111)\b' || true

# Observability erreichbar?
curl -fsS http://localhost:9090/-/ready >/dev/null && echo "prom: OK" || echo "prom: DOWN"
curl -fsS http://localhost:3000/login >/dev/null && echo "grafana: OK" || echo "grafana: DOWN"

# Compose-Stacks
docker compose ls
[ -x scripts/ops/prom_targets_check.sh ] && ./scripts/ops/prom_targets_check.sh || true
```

**2) Mitigation (kein Live/Execution)**
```bash
# Stacks stoppen (nur wenn Ursache dort vermutet)
# for d in peaktrade-shadow-mvs peaktrade-ai-live-ops peaktrade-observability; do
#   [ -d "$d" ] && (cd "$d" && docker compose down --remove-orphans) || true
# done

# Repo-Reset (nur Working Tree; keine Force-Push ohne Absprache)
git status
# git restore --staged . && git restore .   # nur bei lokaler Versehen-Änderung

# Env sicher: Execution weiter blockiert
echo "PEAK_TRADE_EXECUTION_FORBIDDEN=${PEAK_TRADE_EXECUTION_FORBIDDEN:-not set}"
export PEAK_TRADE_MODE=research
export PEAK_TRADE_LIVE=0
export PEAK_TRADE_EXECUTION_FORBIDDEN=1
```

**3) Post-Mortem (nach Stabilisierung)**
- Kurz dokumentieren: Was? Wann? Welche Schritte? Rollback/ Fix?
- Optional: Eintrag in `docs/ops/runbooks/` oder Incident-Log; keine Secrets festhalten.

### Exit
- System stabil; keine Live-Execution ausgelöst; Post-Mortem bei Bedarf erstellt.

---

## Phase 17 — Release/Tagging Rules (Runbook Lifecycle)

### Entry
- Ein Runbook-Change ist gemerged (`main`), CI grün.
- Ziel: klare Versionierung + reproduzierbare Artefakte.

### Steps (Commands)
```bash
# 1) Tag naming convention
# - runbook-cursor-ma-v<N>  (annotated tag)
# - Tag message must reference PR(s)

git fetch origin --tags --prune
git rev-parse HEAD
git log --oneline -n 5

# create next tag (example)
# git tag -a runbook-cursor-ma-v4 -m "Runbook phases X–Y merged (#NNNN)"
# git push origin runbook-cursor-ma-v4

# verify remote tag exists
# git ls-remote --tags origin | rg 'runbook-cursor-ma-v4'
```

### Runbook-ZIP aus Tag erzeugen

Nach dem Tag: ZIP aus dem getaggten Stand erzeugen, Checksum ablegen, optional nach `~/Downloads` kopieren.

```bash
TAG="runbook-cursor-ma-v3"
OUT="/tmp/cursor_multi_agent_orchestration_runbook_${TAG}.zip"

git fetch origin --tags --prune
git archive --format=zip --output="$OUT" \
  "$TAG" docs/ops/runbooks/cursor_multi_agent_orchestration.md

cd /tmp
BASENAME="$(basename "$OUT")"
H="$(shasum -a 256 "$BASENAME" | awk '{print $1}')"
printf "%s  %s\n" "$H" "$BASENAME" > "${BASENAME}.sha256"
shasum -a 256 -c "${BASENAME}.sha256"

# optional: copy to Downloads
cp -v "$OUT" "${OUT}.sha256" ~/Downloads/
ls -la ~/Downloads/"$BASENAME"*
```

### PR workflow (runbook phases 17–20)

Preflight: Docs-Token-Policy lokal prüfen (fast fail). Branch, Commit, Push, PR, Checks, bei Grün Merge + Resync. Anschließend Anker prüfen.

```bash
# 0) local doc gate (fast fail)
python3 scripts/ops/validate_docs_token_policy.py --base origin/main

# 1) branch + commit
git status
git checkout -b docs/runbook-cursor-ma-phases-17-20

git add docs/ops/runbooks/cursor_multi_agent_orchestration.md
git diff --cached
git commit -m "docs(runbook): add phases 17–20 (tagging, artifacts, docs-gate, cleanup)"

# 2) push + PR
git push -u origin docs/runbook-cursor-ma-phases-17-20

gh pr create \
  --base main \
  --head docs/runbook-cursor-ma-phases-17-20 \
  --title "docs(runbook): add phases 17–20 (tagging, artifacts, docs-gate, cleanup)" \
  --body $'Extends cursor_multi_agent_orchestration.md with:\n- Phase 17: release/tagging rules\n- Phase 18: artifact naming + sha256 verification\n- Phase 19: docs-token-policy cheat sheet\n- Phase 20: quarterly cleanup\n\nIncludes PR workflow subsection (runbook phases 17–20).\n\nDocs-only; artifacts remain local-only.'

PR_NUM="$(gh pr view --json number -q .number)"
gh pr checks "$PR_NUM" --watch

# 3) merge when green + resync
gh pr merge "$PR_NUM" --squash --delete-branch

git checkout main
git fetch origin --prune
git reset --hard origin/main

# 4) verify anchors (pattern = actual Phase 17–20 headings on main)
rg -n "## Phase 17 — Release/Tagging Rules \(Runbook Lifecycle\)|## Phase 18 — Artifact Naming Convention|## Phase 19 — Docs-Gate Cheat Sheet|## Phase 20 — Quarterly Cleanup" \
  docs/ops/runbooks/cursor_multi_agent_orchestration.md
```

### Exit
- Annotated Tag auf `main` gepusht; Tag-Message referenziert PR(s); Reproduzierbarkeit gesichert.
- Optional: Runbook-ZIP + `.sha256` in `/tmp` (und ggf. `~/Downloads`) für Bundle (Phase 9) verfügbar.

---

## Phase 18 — Artifact Naming Convention

### Entry
- Phase 17 abgeschlossen (Tag z. B. `runbook-cursor-ma-v<N>` vorhanden).
- Ziel: einheitliche, versionierte Artefakt-Namen für Bundles und Evidence-Packs.

### Steps (Naming Rules)

| Artefakt-Typ | Muster | Beispiel |
|--------------|--------|----------|
| Runbook-ZIP | `cursor_multi_agent_orchestration_runbook.zip` | (ein pro Release; Version im Tag) |
| Release-Bundle (tgz) | `release_bundle_cursor_ma_v<N>.tgz` | `release_bundle_cursor_ma_v4.tgz` |
| Release-Bundle Checksum | `release_bundle_cursor_ma_v<N>.tgz.sha256` | |
| Evidence-Pack (tgz) | `evidence_pack_cursor_ma_v<N>.tgz` | `evidence_pack_cursor_ma_v4.tgz` |
| Evidence-Pack Checksum | `evidence_pack_cursor_ma_v<N>.tgz.sha256` | |
| Config-Snapshot | `peaktrade_configs_snapshot.tgz` / `tracked_configs_snapshot.tgz` | (optional mit Datum im Namen) |
| Worktree-Snapshot | `grafana_ds_fix_worktree_snapshot.tgz` (oder themenspezifisch) | |

```bash
# Beispiel: Artefakte für v4 benennen
V=4
cp release_bundle_cursor_ma_v1.tgz "release_bundle_cursor_ma_v${V}.tgz"
shasum -a 256 "release_bundle_cursor_ma_v${V}.tgz" | awk '{print $1, $2}' > "release_bundle_cursor_ma_v${V}.tgz.sha256"
```

### Exit
- Alle Release-Artefakte folgen dem Muster; Version `<N>` stimmt mit Tag `runbook-cursor-ma-v<N>` überein.

---

## Phase 19 — Docs-Gate Cheat Sheet

### Entry
- Branch-Protection für `main` aktiv; Docs-relevante CI-Workflows vorhanden.

### Steps (Quick Reference)

| Schritt | Befehl / Aktion |
|---------|------------------|
| Lokal vor Push | `pre-commit run --all-files`; ggf. `mkdocs build --strict` |
| Branch erstellen | `git checkout -b docs/runbook-<thema>` |
| PR öffnen | `gh pr create --base main --head docs/runbook-<thema> --title "..." --body "..."` |
| CI beobachten | `gh pr checks --watch` |
| Merge (nach Grün) | `gh pr merge <PR_NUM> --squash --delete-branch` |
| Resync main | `git checkout main && git fetch origin --prune && git reset --hard origin/main` |

**Typische Docs-Gate-Fehler**
- Lint/format: `pre-commit run -a` erneut ausführen, Änderungen committen.
- Docs-Build: `mkdocs build --strict` (oder Quarto/Sphinx) lokal prüfen; fehlende Referenzen/ broken links beheben.
- Token-Policy: `python3 scripts/ops/validate_docs_token_policy.py --base origin/main`; Inline-Code-Pfade mit `&#47;` statt `/` (z. B. `origin&#47;main`, `.scratch&#47;`).
- **docs-reference-targets-gate:** `./scripts&#47;ops&#47;verify_docs_reference_targets.sh --changed --base origin&#47;main`; referenzierte Repo-Pfade müssen existieren. False-Positives (illustrative Pfade): siehe `docs&#47;ops&#47;runbooks&#47;RUNBOOK_DOCS_REFERENCE_TARGETS_FALSE_POSITIVES.md`. <!-- pt:ref-target-ignore -->

**Token policy & reference targets (recommendations)**
1. **Token policy:** Inline-code illustrative slashes must use `&#47;` (e.g. `origin&#47;main`, `scripts&#47;ops&#47;...`).
2. **Reference targets:** Prose/table path-like tokens can be misread as repo paths and trigger docs-reference-targets-gate false positives.
- **Prefer fenced code blocks** for commands (not inline-code inside tables).
- If a table cell must contain path-like tokens, append `<!-- pt:ref-target-ignore -->` at end-of-line.

**Local gates**
```bash
python3 scripts/ops/validate_docs_token_policy.py --base origin/main
./scripts/ops/verify_docs_reference_targets.sh --changed --base origin/main || true
```

### Exit
- Cheat Sheet für schnelles Nachschlagen bei Runbook/Docs-PRs verfügbar.

---

## Phase 20 — Quarterly Cleanup

### Entry
- Laufendes Quartal endet; Runbook und Artefakte sind mehrfach genutzt worden.
- Ziel: veraltete lokale Artefakte, verwaiste Branches und veraltete Dokumentation bereinigen (ohne Live/Execution).

### Steps (Commands)
```bash
# 1) Verify repo clean
git status

# 2) Inspect scratch contents (ignored) + decide what to keep
du -sh .scratch 2>/dev/null || true
find .scratch -maxdepth 2 -type f -print 2>/dev/null | head -n 50

# 3) Archive scratch manifests (optional)
mkdir -p /tmp/scratch_archive
cp -v .scratch/manifests/*.txt* /tmp/scratch_archive/ 2>/dev/null || true
tar -czf /tmp/scratch_archive.tgz -C /tmp scratch_archive
shasum -a 256 /tmp/scratch_archive.tgz | tee /tmp/scratch_archive.tgz.sha256

# 4) Prune stale docker resources (careful; optional)
docker system df
# docker system prune -f

# 5) Remove old /tmp bundles (optional; manual selection)
ls -la /tmp | rg "cursor_multi_agent_orchestration_runbook|release_bundle_cursor_ma|evidence_pack_cursor_ma|incident_evidence_cursor_ma" || true

# 6) Alte Pip/Config-Snapshots in /tmp
ls -la /tmp/pip_freeze*.txt /tmp/tracked_configs*.tgz /tmp/peaktrade_configs*.tgz 2>/dev/null || true

# 7) Verwaiste lokale Branches (nur anzeigen; Löschen manuell)
git fetch origin --prune
git branch -vv | grep ': gone]' || true
# git branch -d <branch>   # nur nach Prüfung

# 8) Runbook-Dokumentation prüfen
# - Phasen 1–20 auf Aktualität (Links, Workflow-Namen, Beispiele)
# - Veraltete PR-Referenzen in Tag-Messages oder Evidence-Packs dokumentieren, nicht löschen

# 9) Optional: Tag-Liste für Audit
git tag --list 'runbook-cursor-ma-v*' | sort -V
```

### Exit
- Repo clean; .scratch inspiziert, ggf. Manifests archiviert; alte lokale Artefakte/Docker bereinigt; verwaiste Branches bereinigt; Runbook-Referenzen geprüft.

---

## Phase 21 — PR Hygiene (Docs-Only Changes)

### Entry
- Du änderst ausschließlich Docs/Runbooks.
- Ziel: kleine, reviewbare PRs, minimales CI-Risiko.

### Steps (Commands)
```bash
# 1) Ensure diff scope is docs-only
git status
git diff --name-only origin/main...HEAD | sort

# should be only under docs/
git diff --name-only origin/main...HEAD | rg -v '^docs/' && echo "ERROR: non-docs changes present" || echo "OK: docs-only"

# 2) Local gates (fast)
python3 scripts/ops/validate_docs_token_policy.py --base origin/main
pre-commit run -a || true  # optional
```

### Exit
- Nur Dateien unter `docs/` geändert; Token-Policy und Pre-Commit lokal bestanden; PR klein und fokussiert.

### PR workflow (runbook phases 21–24)

```bash
# PR workflow (main protected)

git checkout -b docs/runbook-cursor-ma-phases-21-24
git push -u origin docs/runbook-cursor-ma-phases-21-24

gh pr create \
  --base main \
  --head docs/runbook-cursor-ma-phases-21-24 \
  --title "docs(runbook): add phases 21–24 (PR hygiene, naming, CI triage, no-live)" \
  --body $'Extends cursor_multi_agent_orchestration.md with:\n- Phase 21: docs-only PR hygiene\n- Phase 22: branch/commit conventions\n- Phase 23: CI triage patterns\n- Phase 24: no-live enforcement checklist\n\nDocs-only; no runtime behavior changes.'

PR_NUM="$(gh pr view --json number -q .number)"
gh pr checks "$PR_NUM" --watch
# merge when green
gh pr merge "$PR_NUM" --squash --delete-branch

git checkout main
git fetch origin --prune
git reset --hard origin/main
```

---

## Phase 22 — Branch Naming Convention

### Entry
- Du erstellst einen Branch für Runbook/Docs- oder Ops-Änderungen.
- Ziel: einheitliche, maschinenlesbare Branch-Namen für schnelle Zuordnung und CI-Triage.

### Steps (Naming Rules)

**Branch naming (examples)**

| Kontext | Muster | Beispiele |
|---------|--------|-----------|
| Runbook Phasen | `docs&#47;runbook-<topic>-phases-<n>-<m>` | `docs&#47;runbook-cursor-ma-phases-21-24` |
| Runbook Fix | `docs&#47;runbook-<topic>-fix-<short>` | `docs&#47;runbook-cursor-ma-fix-token-policy` |
| Ops/Skripte | `ops&#47;<bereich>-<kurzbeschreibung>` | `ops&#47;validate-docs-token-policy`, `ops&#47;prom-targets-check` |
| Fix/Backport | `fix&#47;<issue-oder-thema>` oder `backport&#47;<pr>-to-main` | `fix&#47;docs-gate-slash`, `backport&#47;1234-to-main` |
| Revert | `revert&#47;<commit-oder-pr>` | `revert&#47;runbook-or-scratch` |

```bash
# Beispiele: Branch anlegen
git checkout -b docs/runbook-cursor-ma-phases-21-24
git checkout -b docs/runbook-cursor-ma-fix-token-policy
git checkout -b ops/ci-triage-patterns
```

**Commit message**

- Format: `docs(runbook): <imperative summary>`
- Beispiel: `docs(runbook): add phases 21–24 (PR hygiene, naming, CI triage, no-live)`

### Exit
- Branch-Name folgt dem Muster; Commit-Message im Format `docs(runbook): …`; CI und Reviewer können Scope sofort erkennen.

---

## Phase 23 — CI Triage Patterns

### Entry
- PR ist offen; CI läuft oder ist durchgelaufen.
- Ziel: typische CI-Fehler schnell einordnen und beheben (ohne Live/Execution).

### Steps (Quick Reference)

| CI-Fehler / Muster | Ursache (typisch) | Aktion |
|--------------------|--------------------|--------|
| Docs-Token-Policy fail | Slash in Inline-Code (z. B. `origin&#47;main`) | `validate_docs_token_policy.py` lokal; Inline-Code mit `&#47;` ersetzen |
| Lint/Format fail | Pre-Commit nicht lokal gelaufen oder andere Konfiguration | `pre-commit run -a`; Änderungen committen und pushen |
| Docs-Build fail | Broken links, fehlende Referenzen, fehlerhafte Syntax | `mkdocs build --strict` (oder Quarto/Sphinx) lokal; Links/Refs prüfen |
| Unrelated test fail | Flaky Test oder Änderung außerhalb des PR-Scopes | Prüfen ob PR nur `docs/` enthält; ggf. Test-Issue separat tracken, nicht in Docs-PR mischen |
| Branch out-of-date | `main` ist voraus | `git fetch origin && git rebase origin&#47;main` (oder Merge); Konflikte lösen |

```bash
# 1) CI-Status prüfen
gh pr checks --watch
gh pr view --json statusCheckRollup -q '.statusCheckRollup[] | "\(.name): \(.status)"'

# 2) Lokal gleiche Gates wie CI (Docs-PR)
python3 scripts/ops/validate_docs_token_policy.py --base origin/main
pre-commit run -a
# [ -f mkdocs.yml ] && mkdocs build --strict

# 3) Bei "branch out of date": Rebase
git fetch origin
git rebase origin/main
git push --force-with-lease
```

**PR status and run logs (by PR number)**

```bash
PR_NUM="<PR_NUMBER>"

# 1) Non-blocking status
gh pr view "$PR_NUM" --json number,state,mergeable,headRefName,baseRefName,url
gh pr checks "$PR_NUM" --required
gh pr checks "$PR_NUM"

# 2) Find latest run(s) for PR branch and pull logs for failing jobs
BR="$(gh pr view "$PR_NUM" --json headRefName -q .headRefName)"
gh run list --limit 20 --branch "$BR"
# If needed:
# RUN_ID="<databaseId>"
# gh run view "$RUN_ID" --log --log-failed

# 3) Typical docs-only failure handling
# - docs-token-policy-gate: run local validator + fix inline-code illustrative slashes via &#47;
# - audit: usually dependency/security scan; ensure no lockfile changes in docs-only PR
# - weekly_core: health gate; wait or re-run if allowed
```

**Required checks must be green (TLS fallback)**
```bash
PR_NUM="<PR_NUMBER>"

# Required checks must be green
gh pr checks "$PR_NUM" --required || true

# If gh TLS issues: use UI, but confirm required checks explicitly.
# Fallback verification: open PR and check "Required checks" section.
```

**TLS workaround options for gh (run on your local machine; pick one path)**

```bash
# 0) sanity: confirm gh can reach github
gh auth status
gh api https://api.github.com/rate_limit

# A) If corporate proxy / MITM: set proxy for gh + git (edit values)
# export HTTPS_PROXY="http://proxy.host:port"
# export HTTP_PROXY="http://proxy.host:port"
# export NO_PROXY="localhost,127.0.0.1,.local"
# gh api https://api.github.com/rate_limit

# B) If custom CA cert: point git/gh at the CA bundle (edit path)
# export SSL_CERT_FILE="$HOME/.certs/corp-ca.pem"
# git config --global http.sslCAInfo "$SSL_CERT_FILE"
# gh api https://api.github.com/rate_limit

# C) If only gh is failing, use GitHub UI for merge and use git for resync
# (checks + merge in browser)
open "https://github.com/rauterfrank-ui/Peak_Trade/pull/<PR_NUMBER>"

# After merge (either via gh or UI), resync main:
git checkout main
git fetch origin --prune
git reset --hard origin/main

# Verify anchors after merge:
rg -n "## Phase 21 — PR Hygiene|## Phase 22 — Branch Naming|## Phase 23 — CI Triage Patterns|## Phase 24 — No-Live Enforcement" \
  docs/ops/runbooks/cursor_multi_agent_orchestration.md
```
### Exit
- CI-Fehler einer Kategorie zugeordnet; Fix angewendet (Token-Policy, Lint, Docs-Build, Rebase); keine Live/Execution ausgelöst.

---

## Phase 24 — No-Live Enforcement

### Entry
- Jeder Lauf (lokal, CI, Agent) muss ohne Live-Trading/Execution bleiben.
- Ziel: klare Checks und Env-Setzung, damit versehentliches Live nie ausgelöst wird.

### Steps (Commands)

**1) Env-Checks (vor jedem Agent-/Runner-Lauf)**
```bash
# Erforderliche sichere Defaults / Blockierung
echo "PEAK_TRADE_MODE=${PEAK_TRADE_MODE:-not set}"
echo "PEAK_TRADE_LIVE=${PEAK_TRADE_LIVE:-not set}"
echo "PEAK_TRADE_EXECUTION_FORBIDDEN=${PEAK_TRADE_EXECUTION_FORBIDDEN:-not set}"
echo "PEAK_TRADE_DRY_RUN=${PEAK_TRADE_DRY_RUN:-not set}"

# Sollte sein: MODE=research, LIVE=0, EXECUTION_FORBIDDEN=1, DRY_RUN=1
export PEAK_TRADE_MODE=research
export PEAK_TRADE_LIVE=0
export PEAK_TRADE_EXECUTION_FORBIDDEN=1
export PEAK_TRADE_DRY_RUN=1
```

**2) Code-/Config-Scan (kein Live-Pfad aktiv)**
```bash
# Hinweis: Nur Hinweis; verbotene Muster dürfen in Runbook/Governance-Docs vorkommen (als Referenz).
rg -n "LIVE|live.*trade|execution.*allow|armed|confirm token|dry[- ]run" -S src scripts configs --glob '!*.md' || true

# Prüfen: Keine unabsichtliche Aktivierung in geänderten Dateien
git diff --name-only origin/main...HEAD | xargs -I {} rg -l "PEAK_TRADE_LIVE=1|EXECUTION_FORBIDDEN=0" {} 2>/dev/null && echo "RISK: possible live path" || echo "OK: no live env in diff"
```

**3) Confirm LIVE/Execution stays blocked (best-effort: env + grep)**
```bash
env | rg -n "PEAK_TRADE_LIVE|EXECUTION|ARMED|CONFIRM|DRY_RUN" -S || true
rg -n "L6|Execution.*forbid|LIVE.*block|confirm token|armed" -S src scripts docs || true
```

**4) Runbook commands (dry-run / non-destructive by default)**

- Alle in `docs&#47;runbooks` dokumentierten Befehle sollen dry-run bzw. nicht-destruktiv sein. <!-- pt:ref-target-ignore -->
- Bevorzuge `down` statt `rm -rf`; bevorzuge `curl … &#47;-&#47;ready`-Probes.
- `git reset --hard origin/main` nur explizit beim Reconcile nach Squash-Merge dokumentieren.

**5) Documenting execution-adjacent**

- Falls etwas execution-nah dokumentiert wird: explizit als verboten oder gated kennzeichnen (enabled/armed + confirm token).
- Aus default-Pfaden heraushalten (nicht in Standard-Runbook-Schritten ohne Warnung).

**6) Runbook/PR-Policy**

- Jeder PR, der `src/execution/`, `src/governance/`, `src/risk/` oder Broker/Exchange-Code ändert: explizite Review-Pflicht; keine autonome Merge-Entscheidung.
- Docs-Only-PRs (Phase 21): kein Live-Risiko; CI-Gates (Token-Policy, Lint, Docs-Build) reichen.

### Exit
- Env auf research/dry-run/forbidden gesetzt; keine Änderung aktiviert Live-Pfad; Runbook-Befehle non-destructive; Governance-Regeln eingehalten.

---

## Phase 25 — docs-reference-targets-gate (Deep Dive)

### Entry
- CI meldet `docs-reference-targets-gate` failure auf PR mit `.md`-Änderungen.

### Steps (Commands)
```bash
# Reproduce exactly like CI (only scans changed markdown)
./scripts&#47;ops&#47;verify_docs_reference_targets.sh --changed --base origin&#47;main

# If it fails: it prints "<file>:<line>: <token>" for missing targets.
# Investigate the printed line in the markdown (example):
#   cursor_multi_agent_orchestration.md:919: docs&#47;runbooks

# Open around that line (adjust range):
# sed -n '900,940p' docs&#47;ops&#47;runbooks&#47;cursor_multi_agent_orchestration.md

# Fix options:
# A) Correct the referenced path (preferred if it's a real repo path)
# B) If false positive: append ignore marker on the SAME line:
#    <!-- pt:ref-target-ignore -->
#
# Re-run gate:
./scripts&#47;ops&#47;verify_docs_reference_targets.sh --changed --base origin&#47;main
```

### Exit
- Gate lokal bestanden; alle gemeldeten Targets entweder existierender Pfad oder als False-Positive markiert (`<!-- pt:ref-target-ignore -->`).

---

## Phase 26 — False-Positive Playbook (docs-reference-targets)

### Entry
- Phase 25 zeigt „missing target“, der Pfad ist aber **illustrativ** (Beispiel, Platzhalter, geplanter Branch) und kein realer Repo-Pfad.

### Steps (Commands)

**1) Klassifizieren**
- **Echter Pfad (Typo/veraltet):** Pfad korrigieren oder Doc an echte Datei anpassen.
- **Illustrativ:** Siehe [RUNBOOK_DOCS_REFERENCE_TARGETS_FALSE_POSITIVES.md](RUNBOOK_DOCS_REFERENCE_TARGETS_FALSE_POSITIVES.md) (Diagnose, Fix A/B, Ignore-Marker).

**2) Optionen bei False Positive**
- **Fix A (bevorzugt):** Inline-Code-Pfad mit `&#47;` statt `/` (z. B. `docs&#47;runbooks`) — reduziert Parsing als Link-Target; Token-Policy-Gate prüft das.
- **Fix B:** Auf derselben Zeile am Zeilenende: `<!-- pt:ref-target-ignore -->` setzen (wenn Fix A nicht passt, z. B. in Tabellen oder Code-Blöcken).

**3) Nach Fix**
```bash
./scripts&#47;ops&#47;verify_docs_reference_targets.sh --changed --base origin&#47;main
```

### Exit
- Alle gemeldeten „missing targets“ entweder behoben (echter Pfad) oder als False-Positive neutralisiert (&#47; oder Ignore-Marker); Gate grün.

---

## Phase 27 — Auto-Merge Guidance

### Entry
- PR ist Docs-only oder low-risk; alle **required** CI-Checks grün oder im erwarteten Zustand.
- Ziel: Merge ohne manuelles Klicken nach Grün; einheitlich Squash + Branch löschen.

### Steps (Commands)

**1) Voraussetzungen prüfen**
- Branch-Protection: nur required Checks müssen grün sein.
- Kein Draft; keine offenen Review-Requests (falls Policy das verlangt).

**2) Auto-Merge aktivieren (Squash)**
```bash
PR_NUM="<PR-Nummer>"
gh pr merge "$PR_NUM" --squash --auto
# Prüfen:
gh pr view "$PR_NUM" --json autoMergeRequest --jq '.autoMergeRequest'
```

**3) Wann nicht Auto-Merge**
- PR ändert `src/execution/`, `src/governance/`, `src/risk/` oder Broker/Exchange-Code → explizite Review-Pflicht, kein Auto-Merge ohne Freigabe.
- Optional/nicht-required Checks hängen → Auto-Merge wartet nur auf required; bei Bedarf manuell mergen: `gh pr merge "$PR_NUM" --squash --delete-branch`.

**4) Nach Merge: Resync main**
```bash
git checkout main
git fetch origin --prune
git reset --hard origin/main
```

### Exit
- Auto-Merge aktiviert (wo zulässig); nach Merge main resynced; keine Live/Execution ausgelöst.

---

## Phase 28 — Gate Matrix (Quick Reference)

### Entry
- Schneller Überblick: welche Gates bei Docs/Runbook-PRs laufen, wie reproduzierbar, was bei Failure zu tun ist.

### Steps (Reference Table)

| Gate | Trigger | Lokal reproduzieren | Bei Failure |
|------|---------|--------------------|-------------|
| **docs-reference-targets-gate** | PR mit geänderten `.md` | `./scripts&#47;ops&#47;verify_docs_reference_targets.sh --changed --base origin&#47;main` | Phase 25 + 26: Pfad korrigieren oder False-Positive (&#47; / `<!-- pt:ref-target-ignore -->`) |
| **docs-token-policy-gate** | PR mit geänderten `.md` | `python3 scripts&#47;ops&#47;validate_docs_token_policy.py --base origin&#47;main` | Inline-Pfade mit `&#47;` statt `/` (z. B. `origin&#47;main`, `.scratch&#47;`) |
| **Lint / pre-commit** | Jeder Push | `pre-commit run --all-files` | `pre-commit run -a`, Fixes committen |
| **Docs-Build (MkDocs etc.)** | Wenn konfiguriert | `mkdocs build --strict` (o. ä.) | Broken links/Refs in Docs beheben |
| **No-Live / Execution** | Jeder Lauf (lokal/CI) | Env: `PEAK_TRADE_LIVE=0`, `PEAK_TRADE_EXECUTION_FORBIDDEN=1`; kein Code in execution/governance/risk ohne Review | Phase 24: Env + Grep-Checks; PR-Review bei execution-nah |

### Exit
- Gate Matrix als Nachschlagewerk genutzt; Failures der richtigen Phase zugeordnet und behoben.

---

## Phase 29 — Versioning Cadence (When to Cut vN Tags)

### Entry
- Runbook changes are merged to `main`, CI green.

### Steps (Commands)
```bash
# Tag when one of these is true:
# - a new Phase block is added
# - CI/gate procedure changes (token-policy, reference-targets, TLS workaround)
# - operator-facing incident/rollback process changes

git fetch origin --tags --prune
git log --oneline -n 20

# next tag (example)
# git tag -a runbook-cursor-ma-v5 -m "Runbook phases 29–32 merged (#NNNN)"
# git push origin runbook-cursor-ma-v5
```

### Exit
- Neuer Tag nur bei dokumentierten Triggern; Tag-Message referenziert PR(s).

---

## Phase 30 — Deprecation Policy (Runbook & Gates)

### Entry
- Eine Gate-Prozedur, ein Skript oder eine Runbook-Phase soll ersetzt oder eingestellt werden.
- Ziel: klare Ankündigung, Migration, kein stilles Entfernen.

### Steps (Commands)

**1) Soft deprecate first**
- Alte Prozedur/Befehl **behalten**, als **DEPRECATED** kennzeichnen und **Ersatz** (neue Phase/Befehl) direkt daneben dokumentieren.
- Cutoff-Datum oder Version-Tag angeben, z. B. „deprecated since runbook-cursor-ma-v4“.

**2) After one release cycle: remove deprecated block**
- Nach mindestens einem Runbook-Release (nächster Tag, z. B. `runbook-cursor-ma-vN+1`): deprecated Block aus dem Runbook entfernen oder durch kurzen Redirect zur neuen Phase ersetzen.

**3) References and gates stay clean**
- CI- und Workflow-Referenzen auf die neue Prozedur umstellen; Token-Policy und Reference-Targets nach Entfernen erneut laufen lassen.

**Quick search for deprecated markers**
```bash
rg -n "DEPRECATED|deprecated since runbook-cursor-ma" docs/ops/runbooks/cursor_multi_agent_orchestration.md
```

**Before removing a deprecated block: cross-references**
```bash
# Referenzen prüfen (Beispiele; anpassen)
rg -n "Phase NN — Deprecated Topic|script_deprecated" docs scripts --glob '*.md' || true
git grep -n "verify_docs_token_policy\|validate_docs_token_policy" -- '*.yml' '*.md' || true
```

### Exit
- Zuerst soft deprecate (alte Prozedur behalten, DEPRECATED + Ersatz + Tag); nach einem Release-Zyklus Block entfernen; Referenzen und Gates sauber.

---

## Phase 31 — Gate Regression Tests

### Entry
- CI-Gates (z. B. docs-token-policy, docs-reference-targets) sind definiert.
- Ziel: Änderungen an Gate-Skripten oder -Regeln nicht ohne Absicherung durchführen; Regressionen vermeiden.

### Steps (Commands)
```bash
# 1) Bestehende Gate-Skripte (Beispiele)
ls -la scripts&#47;ops&#47;validate_docs_token_policy.py scripts&#47;ops&#47;verify_docs_reference_targets.sh 2>/dev/null || true

# 2) Lokal gleiche Eingaben wie CI (geänderte .md gegen base)
git fetch origin --prune
python3 scripts&#47;ops&#47;validate_docs_token_policy.py --base origin&#47;main
./scripts&#47;ops&#47;verify_docs_reference_targets.sh --changed --base origin&#47;main

# 3) Bei Änderung eines Gate-Skripts: Regression prüfen
# - Vorher: Ergebnis auf bekanntem Stand (z.&#46;B. main) notieren
# - Nachher: gleicher Stand muss gleiches Ergebnis liefern (kein False-Negative)
# Optional: dedizierte Tests in evals&#47; oder tests&#47; für Gate-Logik

# 4) Evals/Testcases für Gates (falls vorhanden)
ls -la evals&#47;aiops&#47;testcases&#47;*.yaml 2>/dev/null || true
pytest tests&#47; -k "docs_token_policy or reference_targets" -q 2>/dev/null || true
```

### Exit
- Gate-Änderungen gegen bekannte Baseline geprüft; bei vorhandenen Evals/Tests grün.

---

## Phase 32 — Docs-Only CI Checklist

### Entry
- PR enthält nur Änderungen unter `docs&#47;` (Runbooks, Markdown, Konfig-Docs).
- Ziel: vor Push/Merge alle relevanten Gates lokal durchlaufen, um CI-Zeit und Rückläufer zu sparen.

### Steps (Checklist)

**Gates (1–3)**
```bash
# 1) token policy gate
python3 scripts/ops/validate_docs_token_policy.py --base origin/main

# 2) reference targets gate (changed markdown)
./scripts/ops/verify_docs_reference_targets.sh --changed --base origin/main || true

# 3) optional: full reference scan (slower)
./scripts/ops/verify_docs_reference_targets.sh --base origin/main
```

| Schritt | Befehl / Aktion |
|---------|------------------|
| Scope prüfen | `git diff --name-only origin&#47;main...HEAD \| rg -v '^docs/'` → leer |
| Token-Policy | `python3 scripts&#47;ops&#47;validate_docs_token_policy.py --base origin&#47;main` |
| Reference-Targets | `./scripts&#47;ops&#47;verify_docs_reference_targets.sh --changed --base origin&#47;main` <!-- pt:ref-target-ignore --> |
| Lint / Pre-Commit | `pre-commit run --all-files` |
| Docs-Build (falls vorhanden) | `mkdocs build --strict` oder Quarto/Sphinx |
| Kein Live-Pfad | Keine Änderungen in `src&#47;execution&#47;`, `src&#47;governance&#47;`, `src&#47;risk&#47;` |

```bash
# One-shot docs-only checklist (fast fail)
git fetch origin --prune
git diff --name-only origin/main...HEAD | rg -v '^docs/' && echo "FAIL: non-docs change" || true
python3 scripts/ops/validate_docs_token_policy.py --base origin/main
./scripts/ops/verify_docs_reference_targets.sh --changed --base origin/main
pre-commit run --all-files
# [ -f mkdocs.yml ] && mkdocs build --strict
```

### Exit
- Alle Punkte der Checkliste bestanden; PR kann gepusht werden; erwartet: Docs-Gates in CI grün.

---

## Phase 33 — PR Creation via GitHub UI (gh TLS Fallback)

### Entry
- `gh` fails with TLS verification errors (e.g., `tls: failed to verify certificate`).
- Branch is already pushed to `origin`.

### Steps (Commands)
```bash
BRANCH="<BRANCH_NAME>"

# Open compare view (create PR from branch)
# Replace <BRANCH_NAME> with your branch.
echo "https://github.com/rauterfrank-ui/Peak_Trade/compare/main...${BRANCH}?expand=1"

# Alternative direct PR creation URL:
echo "https://github.com/rauterfrank-ui/Peak_Trade/pull/new/${BRANCH}"

# In the UI:
# - Set Title/Body (copy from runbook PR workflow block)
# - Confirm "Required checks" section
# - Squash merge + delete branch (or enable auto-merge if allowed)
```

### Exit
- PR im UI erstellt; Required Checks bestätigt; Squash-Merge + Branch-Löschung wie im Runbook-Workflow.

---

## Phase 34 — Merge-Group Notes

### Entry
- Mehrere PRs sollen nacheinander oder als Gruppe gemerged werden (z. B. Runbook-Phasen-Batch).
- Ziel: klare Reihenfolge, Abhängigkeiten und Merge-Strategie dokumentieren.

### Steps (Commands)

**1) Merge-Reihenfolge festlegen**
- Abhängige PRs zuerst (z. B. Gate-Skript-Änderung vor Runbook-Phase, die darauf verweist).
- Docs-Only-PRs können parallel oder in beliebiger Reihenfolge, sofern keine Cross-Referenzen brechen.

**2) Branch-Protection & Required Checks**
- Nur mergen, wenn alle **required** Checks grün sind.
- Bei Merge-Group: jeden PR einzeln mergen; nach jedem Merge `main` resyncen, bevor der nächste Branch erstellt wird (falls Branch von `main` abzweigt).

**3) Notizen für Operator**
```bash
# Vor Merge-Group: Notizen anlegen (lokal, nicht committen)
# - Liste: PR-Nummern, Titel, Reihenfolge
# - Nach jedem Merge: gh pr view <N> --json state, mergedAt
# Resync nach jedem Merge:
git checkout main
git fetch origin --prune
git reset --hard origin/main
```

**4) Auto-Merge bei erlaubten PRs**
- Für Docs-Only/Low-Risk: `gh pr merge <PR_NUM> --squash --auto` (Phase 27); Merge-Group läuft dann nacheinander, sobald jeweils Checks grün sind.

**5) When merge queue is enabled**
- A PR can be green on `pull_request` but fail under `merge_group` due to integration effects (e.g. base moved, conflicts, or different env).
- Treat merge_group failures: rebase or merge `main` into branch, re-run local gates (Phase 32), push, retry.

**Quick sanity (before retry)**
```bash
git fetch origin --prune
git status -sb
```

### Exit
- Merge-Reihenfolge dokumentiert; jeder PR mit grünen Required Checks gemerged; main nach jedem Merge resynced.
- Bei Merge-Queue: merge_group-Failures durch Rebase/Merge von main, lokale Gates, erneuten Push beheben.

---

## Phase 35 — Docs-Gate Table Hardening

### Entry
- Gate-Matrix (Phase 28) und Docs-Gate-Checklisten sind in Gebrauch.
- Ziel: Tabelle und Referenzen konsistent halten; fehlende oder veraltete Einträge vermeiden.

### Steps (Commands)

**1) Gate-Liste gegen CI abgleichen**
```bash
# Welche Status-Checks verlangt main?
gh api repos/:owner/:repo/branches/main/protection 2>/dev/null | jq '.required_status_checks.contexts'

# Workflows, die Docs-Gates ausführen
gh workflow list
rg -l "validate_docs_token_policy|verify_docs_reference_targets" .github/workflows/
```

**2) Runbook-Tabellen prüfen**
- Phase 28 (Gate Matrix): jede Zeile = Gate, der in CI oder als Required Check vorkommt.
- Phase 19 (Docs-Gate Cheat Sheet): gleiche Gates mit Kurzbefehl und typischen Fehlern.
- Phase 32 (Docs-Only CI Checklist): gleiche Gates in Checklistenform.

**3) Einmalige Konsistenz-Checks**
```bash
# Erwähnte Skripte müssen existieren
[ -f scripts/ops/validate_docs_token_policy.py ] && echo "token-policy: OK" || echo "token-policy: MISSING"
[ -x scripts/ops/verify_docs_reference_targets.sh ] && echo "reference-targets: OK" || echo "reference-targets: MISSING"

# False-Positives-Doc referenziert (Phase 19/26)
[ -f docs/ops/runbooks/RUNBOOK_DOCS_REFERENCE_TARGETS_FALSE_POSITIVES.md ] && echo "false-positives doc: OK" || echo "false-positives doc: MISSING"
```

**4) Bei neuen Gates**
- Neue Zeile in Phase-28-Tabelle; Eintrag in Phase 19 und Phase 32; lokalen Reproduktionsbefehl dokumentieren.

### Exit
- Gate-Tabellen und Checklisten decken alle relevanten CI-Docs-Gates ab; Verweise auf Skripte und False-Positives-Doc korrekt.

---

## Phase 36 — Known False-Positives Catalog

### Entry
- `docs-reference-targets-gate` meldet fehlende Targets; einige davon sind bewusst illustrative Pfade (Phase 25/26).
- Ziel: zentrale Liste bekannter False-Positives für schnelle Zuordnung und einheitliche Behandlung.

### Steps (Commands)

**1) Katalog-Dokument**
- Siehe [RUNBOOK_DOCS_REFERENCE_TARGETS_FALSE_POSITIVES.md](RUNBOOK_DOCS_REFERENCE_TARGETS_FALSE_POSITIVES.md): Diagnose, Fix A/B (&#47; vs. `<!-- pt:ref-target-ignore -->`), Beispiele.

**Known false positives (examples)**  
- docs-reference-targets-gate misreads: table cells containing `./scripts&#47;ops&#47;...`; prose like `docs&#47;runbooks`. Fix: `<!-- pt:ref-target-ignore -->` (same line). <!-- pt:ref-target-ignore -->

**2) Bei neuem False-Positive**
- Zuerst klassifizieren: illustrativer Pfad (Beispiel, Platzhalter, Konvention) vs. echter Repo-Pfad (dann korrigieren).
- Illustrativ: Fix A (Inline-Code mit `&#47;`) oder Fix B (Ignore-Marker auf der Zeile); optional Eintrag im Katalog-Dokument mit Datei/Zeile/Muster.

**3) Katalog pflegen (optional)**
```bash
# Bestehende Ignore-Marker im Runbook
rg -n "pt:ref-target-ignore" docs/ops/runbooks/

# Gate nach Änderungen erneut ausführen
./scripts/ops/verify_docs_reference_targets.sh --changed --base origin/main
```

**4) Keine echten Pfade als False-Positive markieren**
- Nur illustrative/Platzhalter-Pfade mit Ignore-Marker oder &#47; versehen; echte Pfade müssen existieren oder angepasst werden.

### Exit
- Bekannte False-Positives im Katalog oder per Ignore-Marker/&#47; behandelt; Gate läuft grün; keine echten Pfadfehler als False-Positive abgelegt.

### PR workflow (runbook phases 33–36)

```bash
# PR workflow (main protected)

git checkout -b docs/runbook-cursor-ma-phases-33-36
git push -u origin docs/runbook-cursor-ma-phases-33-36

# If gh works:
gh pr create \
  --base main \
  --head docs/runbook-cursor-ma-phases-33-36 \
  --title "docs(runbook): add phases 33–36 (UI PR creation, merge_group, table hardening, catalog)" \
  --body $'Extends cursor_multi_agent_orchestration.md with:\n- Phase 33: PR creation via GitHub UI (gh TLS fallback)\n- Phase 34: merge_group notes\n- Phase 35: docs-gate table hardening\n- Phase 36: known false positives catalog\n\nDocs-only.'

# If gh TLS fails: create PR via UI using Phase 33 URLs.

PR_NUM="$(gh pr view --json number -q .number 2>/dev/null || true)"
[ -n "$PR_NUM" ] && gh pr checks "$PR_NUM" --watch
# merge when green (UI if needed)
# gh pr merge "$PR_NUM" --squash --delete-branch
# resync:
# git checkout main && git fetch origin --prune && git reset --hard origin/main
```

---

## Phase 37 — Merge Queue Failures (merge_group) Handling

### Entry
- PR was green on `pull_request` but fails under `merge_group` (merge queue run).

### Steps (Commands)
```bash
PR_NUM="<PR_NUMBER>"

# 1) Confirm required checks status (UI fallback if gh TLS broken)
gh pr checks "$PR_NUM" --required || true

# 2) Bring branch up to date with base (preferred: rebase; alternative: merge)
BR="$(gh pr view "$PR_NUM" --json headRefName -q .headRefName 2>/dev/null || true)"
git fetch origin --prune
[ -n "$BR" ] && git checkout "$BR"

# rebase onto latest main (keeps history clean)
git rebase origin/main
git push --force-with-lease

# 3) Re-run local docs gates (docs-only PR)
python3 scripts/ops/validate_docs_token_policy.py --base origin/main
./scripts/ops/verify_docs_reference_targets.sh --changed --base origin/main || true
```

### Exit
- Branch mit `main` abgeglichen; lokale Docs-Gates grün; Merge-Queue kann erneut laufen.

---

## Phase 38 — Re-Run Strategy (CI / merge_group)

### Entry
- Ein oder mehrere CI-Checks sind rot; Merge-Queue (`merge_group`) ist fehlgeschlagen oder PR-Checks hängen.
- Ziel: entscheiden, ob Re-Run ausreicht oder Rebase/ Fix nötig ist.

### Steps (Commands)

**0) Required checks before merge / evidence**
```bash
PR_NUM="<PR_NUMBER>"

# Prefer: do not merge until required checks are green.
gh pr checks "$PR_NUM" --required || true

# If a required check is flaky, re-run in UI (preferred) or via gh if available:
# gh run rerun <RUN_ID>

# Record evidence: link run + failing job for later triage.
```

**1) Re-Run vs. Rebase/Fix**
- **Nur Re-Run:** Flaky/transiente Fehler (Netzwerk, Timeout, externer Dienst); keine Code-/Config-Änderung nötig.
- **Rebase/Fix:** Branch out-of-date, Konflikte, Merge-Queue-Failure wegen Integration; Logs zeigen echten Fehler (Lint, Token-Policy, Reference-Targets). → Phase 37 (merge_group) bzw. Phase 23 (CI Triage).

**2) Re-Run auslösen**
```bash
PR_NUM="<PR_NUMBER>"
BR="$(gh pr view "$PR_NUM" --json headRefName -q .headRefName)"

# Letzte Runs für den PR-Branch
gh run list --limit 10 --branch "$BR"

# Bestimmten Run erneut ausführen (RUN_ID aus Liste)
# gh run rerun <RUN_ID> --failed
# oder alle Jobs des Runs:
# gh run rerun <RUN_ID>
```

**3) Nach Re-Run**
- Checks beobachten: `gh pr checks "$PR_NUM" --watch`.
- Bei erneutem Failure: Logs prüfen (`gh run view <RUN_ID> --log --log-failed`), dann Fix/Rebase (Phase 37/23).

**4) merge_group erneut anstoßen**
- Nach Rebase + Push (Phase 37): Merge-Queue läuft automatisch erneut. Kein separates „merge_group re-run“ nötig; Queue verarbeitet den aktualisierten Branch.

### Exit
- Re-Run nur bei vermutlich transienten Fehlern; bei echten Fehlern Rebase/Fix (Phase 37/23), dann erneuter Push.

---

## Phase 39 — PR Body Templates

### Entry
- Du öffnest einen PR für Runbook/Docs-Änderungen und willst einheitliche, vollständige PR-Bodies.
- Ziel: Required-Infos für Reviewer und Audit; Copy-Paste-fähige Vorlagen.

### Steps (Templates)

**Runbook-Phasen-Batch (Docs-Only)**
```markdown
Extends cursor_multi_agent_orchestration.md with:
- Phase XX: <short title>
- Phase YY: <short title>
(optional: - Phase ZZ: …)

Docs-only; no runtime behavior changes.
```

**Runbook-Phasen 37–40 (Beispiel)**
```markdown
Extends cursor_multi_agent_orchestration.md with:
- Phase 37: merge queue (merge_group) failure handling
- Phase 38: re-run strategy (CI / merge_group)
- Phase 39: PR body templates
- Phase 40: v5 tag procedure

Docs-only.
```

**Single-Phase / Fix**
```markdown
- Phase NN: <title> (or: Fix for <topic>)
- <one-line reason or scope>

Docs-only.
```

**Revert PR**
```markdown
Reverts commit <COMMIT_SHA> due to <reason>.

(Optional) Ref: Phase 12 rollback.
```

**Summary / Gates / Notes (optional block for PR body)**
```markdown
Summary
- <1–3 bullets of what changed>

Gates
- docs-token-policy-gate: <local result / not applicable>
- docs-reference-targets-gate: <local result / not applicable>

Notes
- Docs-only; no runtime behavior changes.
- If gh TLS issues: PR created via UI (Phase 33).
```

### Exit
- PR-Body enthält Scope und „Docs-only“ (oder Revert/Ref); Vorlagen für künftige Runbook-PRs nutzbar.

---

## Phase 40 — v5 Tag Procedure

### Entry
- Runbook-Änderungen inkl. Phasen 37–40 sind auf `main` gemerged; CI grün.
- Ziel: annotierten Tag `runbook-cursor-ma-v5` setzen, pushen und verifizieren.

### Steps (Commands)
```bash
# 1) Repo auf main, aktuell
git fetch origin --tags --prune
git checkout main
git pull --ff-only origin main
git rev-parse HEAD
git log --oneline -n 5

# 2) Tag erstellen (PR-Nummer in Message eintragen)
git tag -a runbook-cursor-ma-v5 -m "Runbook phases 37–40 merged (#<PR_NUM>): merge_group handling, re-run strategy, PR body templates, v5 tag procedure"
git push origin runbook-cursor-ma-v5

# 3) Verifizieren
git ls-remote --tags origin | grep runbook-cursor-ma-v5
git show runbook-cursor-ma-v5 --no-patch
```

**After merges**
```bash
# After merges:
git checkout main
git fetch origin --tags --prune
git status -sb
git rev-parse HEAD

# Create next tag (example v5)
# git tag -a runbook-cursor-ma-v5 -m "Runbook phases 33–40 merged (#NNNN...)"
# git push origin runbook-cursor-ma-v5

# Build zip from tag and checksum (pattern used in v1–v4)
# git archive --format=zip --output=/tmp/cursor_multi_agent_orchestration_runbook_v5.zip \
#   runbook-cursor-ma-v5 docs/ops/runbooks/cursor_multi_agent_orchestration.md
# cd /tmp
# H="$(shasum -a 256 cursor_multi_agent_orchestration_runbook_v5.zip | awk '{print $1}')"
# printf "%s  %s\n" "$H" "cursor_multi_agent_orchestration_runbook_v5.zip" > cursor_multi_agent_orchestration_runbook_v5.zip.sha256
# shasum -a 256 -c cursor_multi_agent_orchestration_runbook_v5.zip.sha256
```

**Optional: Runbook-ZIP aus v5**
```bash
TAG="runbook-cursor-ma-v5"
OUT="/tmp/cursor_multi_agent_orchestration_runbook_${TAG}.zip"
git archive --format=zip --output="$OUT" "$TAG" docs/ops/runbooks/cursor_multi_agent_orchestration.md
cd /tmp
H="$(shasum -a 256 "$(basename "$OUT")" | awk '{print $1}')"
printf "%s  %s\n" "$H" "$(basename "$OUT")" > "$(basename "$OUT").sha256"
shasum -a 256 -c "$(basename "$OUT").sha256"
```

### Exit
- Tag `runbook-cursor-ma-v5` auf `origin`; Tag-Message referenziert PR; optional Runbook-ZIP + Checksum in `/tmp`.

### Publish phases 37–40 (commit, push, PR)

```bash
# repo-root: publish phases 37–40 via PR (main protected) — commit first, then push + create PR (UI if gh TLS broken)

# 0) docs gates preflight
python3 scripts/ops/validate_docs_token_policy.py --base origin/main
./scripts/ops/verify_docs_reference_targets.sh --changed --base origin/main || true

# 1) branch + commit (required, since Phase 40 PR workflow assumes commit already exists)
git status
git checkout -b docs/runbook-cursor-ma-phases-37-40

git add docs/ops/runbooks/cursor_multi_agent_orchestration.md
git diff --cached
git commit -m "docs(runbook): add phases 37–40 (merge_group, rerun, PR template, v5 tag)"

# 2) push
git push -u origin docs/runbook-cursor-ma-phases-37-40

# 3) PR create (UI fallback if gh TLS broken)
gh pr create \
  --base main \
  --head docs/runbook-cursor-ma-phases-37-40 \
  --title "docs(runbook): add phases 37–40 (merge_group handling, rerun strategy, PR template, v5 tag)" \
  --body $'Extends cursor_multi_agent_orchestration.md with:\n- Phase 37: merge_group failure handling\n- Phase 38: rerun strategy + flaky checks\n- Phase 39: docs-only PR body template\n- Phase 40: next tag + zip procedure\n\nDocs-only.'

# if gh TLS fails, create PR via UI:
# echo "https://github.com/rauterfrank-ui/Peak_Trade/compare/main...docs/runbook-cursor-ma-phases-37-40?expand=1"

# 4) merge when green (UI if needed), then resync + verify anchors
# PR_NUM="<PR_NUMBER>"
# gh pr checks "$PR_NUM" --watch
# gh pr merge "$PR_NUM" --squash --delete-branch
# git checkout main && git fetch origin --prune && git reset --hard origin/main
# rg -n "## Phase 37 — Merge Queue Failures|## Phase 38 — Re-Run Strategy|## Phase 39 — PR Body Templates|## Phase 40 — v5 Tag Procedure" \
#   docs/ops/runbooks/cursor_multi_agent_orchestration.md
```

---

## Phase 41 — Docs PR Playbook (One Page)

### Entry
- You are about to push a docs-only PR (runbook edits).

### Steps (Commands)
```bash
# 0) branch
git status
git checkout -b docs/<topic>

# 1) local docs gates (CI parity)
python3 scripts/ops/validate_docs_token_policy.py --base origin/main
./scripts/ops/verify_docs_reference_targets.sh --changed --base origin/main || true

# 2) commit + push
git add docs/ops/runbooks/cursor_multi_agent_orchestration.md
git diff --cached
git commit -m "docs(runbook): <summary>"
git push -u origin docs/<topic>

# 3) PR creation (UI fallback if gh TLS broken)
echo "https://github.com/rauterfrank-ui/Peak_Trade/compare/main...docs/<topic>?expand=1"

# 4) merge readiness (UI: Required checks must be green; branch up to date)
# 5) squash-merge + delete branch
# 6) resync
git checkout main
git fetch origin --prune
git reset --hard origin/main
```

### Exit
- Docs-PR gemerged; lokales `main` mit `origin&#47;main` synchron.

---

## Phase 42 — Troubleshooting Decision Tree

### Entry
- CI/docs-Gate schlägt fehl oder Verhalten ist unklar (z. B. merge_group, reference-targets, Token-Policy).

### Decision Tree (Kurz)
1. **Fehlertyp?**
   - **reference-targets / broken anchors** → Phase 25 (Deep Dive), Phase 26 (False-Positive), Phase 36 (Catalog); ggf. `--changed --base origin&#47;main` erneut prüfen.
   - **Token-Policy / validate_docs_token_policy** → `scripts&#47;ops&#47;validate_docs_token_policy.py --base origin&#47;main` lokal; Ausgabe mit CI vergleichen.
   - **merge_group / Required checks** → Phase 37 (Merge Queue Failures), Phase 38 (Re-Run); ggf. Re-Run ohne Code-Change, dann erneut in Queue.
2. **Lokal grün, CI rot?**
   - Branch mit `main` abgleichen: `git fetch origin && git merge origin/main` oder Rebase; Push; erneut in Queue.
3. **Flaky Check?**
   - Phase 38: Re-Run-Strategie; bei wiederholtem Flake: Check/Job als flaky dokumentieren (Phase 36/Table).
4. **Unklar / Eskalation?**
   - Minimal Repro Bundle erstellen (Phase 43); Issue mit Bundle-Link + Schritte anlegen.

### Gate-specific quick fixes

1. **docs-token-policy-gate failing?**
   - **run:** `python3 scripts/ops/validate_docs_token_policy.py --base origin/main`
   - **fix:** illustrative slashes in inline-code to `&#47;` (do **NOT** change fenced bash blocks).

2. **docs-reference-targets-gate failing?**
   - **run:** `./scripts/ops/verify_docs_reference_targets.sh --changed --base origin/main`
   - **fix A:** correct real repo path.
   - **fix B:** false-positive → append `<!-- pt:ref-target-ignore -->` on the **same line**.
   - **see:** `docs/ops/runbooks/RUNBOOK_DOCS_REFERENCE_TARGETS_FALSE_POSITIVES.md`

3. **gh TLS broken?**
   - Create/merge PR in UI (Phase 33); resync via git (`git checkout main && git fetch origin --prune && git reset --hard origin/main`).

### Exit
- Fehler eingeordnet; nächster Schritt (Fix, Re-Run, oder Issue mit Repro) festgelegt.

---

## Phase 43 — Minimal Repro Bundle

### Entry
- Bug oder CI-Fehler soll reproduzierbar gemeldet werden (z. B. für Issue oder Eskalation).

### Steps (Commands)
```bash
# 1) Repo-Zustand eingrenzen (Branch + Commit)
git rev-parse HEAD
git status -sb
git log --oneline -n 3

# 2) Nur relevante Artefakte bündeln (keine Secrets, kein .env)
REPRO_DIR="/tmp/peaktrade_repro_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$REPRO_DIR"
git archive HEAD -- docs/ops/runbooks/cursor_multi_agent_orchestration.md \
  scripts/ops/validate_docs_token_policy.py \
  scripts/ops/verify_docs_reference_targets.sh 2>/dev/null | (cd "$REPRO_DIR" && tar x) || true
cp -R docs/ops scripts/ops "$REPRO_DIR"/ 2>/dev/null || true

# 3) Kontext-Infos in Datei
echo "Branch: $(git rev-parse --abbrev-ref HEAD)" > "$REPRO_DIR/repro_context.txt"
echo "Commit: $(git rev-parse HEAD)" >> "$REPRO_DIR/repro_context.txt"
echo "Date: $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$REPRO_DIR/repro_context.txt"

# 4) Archiv (optional)
zip -r "$REPRO_DIR.zip" "$REPRO_DIR"
echo "Bundle: $REPRO_DIR.zip"
```

### Exit
- Reproduzierbares Bundle (Pfad/ ZIP) ohne Secrets; Kontext (Branch, Commit, Datum) dokumentiert; für Issue/Support nutzbar.

---

## Phase 44 — v5 Release Cut (Checklist)

### Entry
- Alle geplanten Runbook- und Gate-Änderungen für v5 sind auf `main`; CI grün; Release-Cut soll erfolgen.

### Steps (Checklist)
1. **Pre-Cut**
   - `main` ist geschützt; letzter Merge (z. B. Phasen 41–44) durch Required checks.
   - Lokal: `git checkout main && git pull --ff-only origin main`.
2. **Tag setzen** (siehe Phase 40)
   - `git tag -a runbook-cursor-ma-v5 -m "Runbook phases 37–44 merged (#<PR_NUM>): ..."`
   - `git push origin runbook-cursor-ma-v5`
3. **Verifizieren**
   - `git ls-remote --tags origin | grep runbook-cursor-ma-v5`
   - Optional: Runbook-ZIP aus Tag (Phase 40, Optional-Block) + Checksum.
4. **Nach dem Cut**
   - Branch löschen (falls noch vorhanden); Release-Notes/Changelog aktualisieren falls vorgesehen.

### Exit
- Tag `runbook-cursor-ma-v5` auf `origin`; optional Runbook-ZIP + SHA256; Release-Cut abgeschlossen.

---

## Phase 45 — Release Bundle (vN) Packaging

### Entry
- A runbook tag `runbook-cursor-ma-vN` exists on `origin`.

### Steps (Commands)
```bash
TAG="runbook-cursor-ma-vN"
OUT_DIR="/tmp/release_bundle_${TAG}"
mkdir -p "$OUT_DIR"

# 1) Runbook zip from tag
git archive --format=zip --output="${OUT_DIR}/cursor_multi_agent_orchestration_runbook_${TAG}.zip" \
  "$TAG" docs/ops/runbooks/cursor_multi_agent_orchestration.md

# 2) SHA256 (basename-only)
cd "$OUT_DIR"
H="$(shasum -a 256 "cursor_multi_agent_orchestration_runbook_${TAG}.zip" | awk '{print $1}')"
printf "%s  %s\n" "$H" "cursor_multi_agent_orchestration_runbook_${TAG}.zip" > "cursor_multi_agent_orchestration_runbook_${TAG}.zip.sha256"
shasum -a 256 -c "cursor_multi_agent_orchestration_runbook_${TAG}.zip.sha256"

# 3) Optional: add related artifacts (snapshots/manifests) into same folder, each with basename-only .sha256
# Example:
# cp -v ~/Downloads/grafana_ds_fix_worktree_snapshot.tgz "$OUT_DIR/"
# shasum -a 256 grafana_ds_fix_worktree_snapshot.tgz | awk '{print $1 "  grafana_ds_fix_worktree_snapshot.tgz"}' > grafana_ds_fix_worktree_snapshot.tgz.sha256

# 4) Tar the bundle + checksum
cd /tmp
tar -czf "${OUT_DIR}.tgz" -C "$(dirname "$OUT_DIR")" "$(basename "$OUT_DIR")"
shasum -a 256 "${OUT_DIR}.tgz" | awk '{print $1 "  " FILENAME}' FILENAME="$(basename "${OUT_DIR}.tgz")" > "${OUT_DIR}.tgz.sha256"
shasum -a 256 -c "${OUT_DIR}.tgz.sha256"
```

### Exit
- Release-Bundle (tgz) + SHA256 in `/tmp`; Runbook-ZIP im Bundle mit basename-only Checksum; optional weitere Artefakte mit je .sha256.

---

## Phase 46 — Cross-Machine Verification

### Entry
- Release-Bundle (z. B. `release_bundle_runbook-cursor-ma-vN.tgz` + `.sha256`) wurde auf einer Maschine erstellt und liegt auf anderem Rechner oder geteiltem Speicher vor.
- Ziel: Integrität und Nutzbarkeit auf einer **anderen** Maschine prüfen (Consumer-/Ops-Sicht).

### Steps (Commands)
```bash
# 1) Bundle-Checksum prüfen (basename-only; gleicher Befehl wie Erzeuger)
cd /tmp
# Annahme: Bundle + .sha256 in aktuellem Verzeichnis (z. B. nach Download/Kopie)
shasum -a 256 -c release_bundle_runbook-cursor-ma-vN.tgz.sha256

# 2) Entpacken
rm -rf /tmp/release_bundle_runbook-cursor-ma-vN
mkdir -p /tmp/release_bundle_runbook-cursor-ma-vN
tar -xzf release_bundle_runbook-cursor-ma-vN.tgz -C /tmp

# 3) Enthaltene Artefakte verifizieren (alle .sha256 im Bundle sind basename-only)
cd /tmp/release_bundle_runbook-cursor-ma-vN
for f in *.sha256; do [ -f "$f" ] && shasum -a 256 -c "$f"; done

# 4) Sanity: Runbook-ZIP vorhanden und lesbar
unzip -l cursor_multi_agent_orchestration_runbook_runbook-cursor-ma-vN.zip | head -20

# 5) Optional: Runbook-Inhalt prüfen (z. B. Phasen-Überschrift)
unzip -p cursor_multi_agent_orchestration_runbook_runbook-cursor-ma-vN.zip \
  docs/ops/runbooks/cursor_multi_agent_orchestration.md | head -80
```

**Alternative: Verifikation in dediziertem Verzeichnis (SRC → DST)**

Bundle und Checksum in ein separates Verzeichnis kopieren, dort Tarball prüfen, entpacken und innere ZIP-Checksum verifizieren.

```bash
SRC="/tmp/release_bundle_runbook-cursor-ma-vN.tgz"
DST="/tmp/verify_release_bundle_vN"
mkdir -p "$DST"
cp -v "$SRC" "$SRC.sha256" "$DST/"
cd "$DST"

# Verify the tarball checksum
shasum -a 256 -c "$(basename "$SRC").sha256"

# Extract and verify inner zip checksum
tar -xzf "$(basename "$SRC")"
cd release_bundle_runbook-cursor-ma-vN
shasum -a 256 -c cursor_multi_agent_orchestration_runbook_runbook-cursor-ma-vN.zip.sha256
```

### Exit
- Bundle auf der Zielmaschine verifiziert; alle Checksums grün; Runbook-ZIP entpackbar und lesbar.

---

## Phase 47 — Retention Policy

### Entry
- Runbook-Releases (Tags, Bundles, Evidence-Packs) und lokale Artefakte sind im Einsatz.
- Ziel: klare Aufbewahrungsfristen und Bereinigung ohne Verlust von Audit-Pfaden.

### Steps (Policy)

**Aufbewahrung**

| Artefakt | Empfehlung | Aktion nach Frist |
|----------|------------|-------------------|
| Tags `runbook-cursor-ma-v*` | Dauerhaft auf `origin` | Nicht löschen; Audit-Referenz |
| Release-Bundle (tgz + .sha256) | Mind. 2 Releases oder 6 Monate | Optional archivieren; dann aus `/tmp` oder Downloads entfernen |
| Evidence-Pack (tgz + .sha256) | Wie Release-Bundle | Optional archivieren |
| Lokale `/tmp`-Bundles, pip_freeze, Config-Snapshots | Bis zum nächsten Release oder Quartal | Phase 20 (Quarterly Cleanup); manuell auswählen |
| Scratch-Archive, Manifests | Optional 1 Jahr | Archiv; dann Bereinigung |

**Befehle (Beispiele)**
```bash
# Bestehende Tags (nicht löschen)
git tag --list 'runbook-cursor-ma-v*' | sort -V

# Alte lokale Bundles identifizieren (manuell löschen)
ls -la /tmp/release_bundle_* ~/Downloads/release_bundle_* 2>/dev/null || true

# Quarterly Cleanup anwenden (Phase 20)
# - .scratch inspizieren, Manifests ggf. archivieren
# - verwaiste Branches, alte /tmp-Artefakte bereinigen
```

### Exit
- Retention-Regeln dokumentiert; Tags bleiben; lokale/archivierte Artefakte nach Policy bereinigt (Phase 20).

---

## Phase 48 — Rollback Procedure

### Entry
- Ein Release (Tag + ggf. Merge) soll zurückgenommen werden; z. B. fehlerhafte Runbook-Änderung oder Gate-Anpassung.
- Kein Live/Execution; nur Repo- und Artefakt-Ebene.

### Steps (Commands)

**1) Rollback der Runbook-Änderung (revert merge, bevorzugt)**

Commit-SHA des zu revertierenden Merges von `origin&#47;main` ermitteln (z. B. aus Evidence-Pack oder `git log`).

```bash
git fetch origin --prune
git log --oneline -n 20 origin/main

# Revert-Branch erstellen
git checkout -b revert/runbook-cursor-ma-vN origin/main
git revert <COMMIT_SHA_TO_REVERT> --no-edit

git push -u origin revert/runbook-cursor-ma-vN
# PR erstellen (Base: main, Head: revert/runbook-cursor-ma-vN)
# gh pr create --base main --head revert/runbook-cursor-ma-vN --title "revert: runbook <reason>" --body "Reverts <COMMIT_SHA>. Ref: Phase 48."
# Nach Merge: Tag für korrigierten Stand ggf. neu setzen (runbook-cursor-ma-vN+1 oder Patch).
```

**2) Tag nicht rückgängig machen; neuen Tag für korrigierten Stand**

- Alte Tags (`runbook-cursor-ma-vN`) **nicht** löschen (Audit).
- Nach Revert-Merge: neuen Tag setzen (z. B. `runbook-cursor-ma-vN+1` oder vN.1), siehe Phase 40/44.

**3) Rollback des Release-Bundles (Consumer)**

- Auf Consumer-Seite: vorherigen Release-Bundle (vN-1) verwenden; neuen Bundle (vN) nicht mehr nutzen.
- Kein automatisches Überschreiben von Bundles auf `origin`; Bundles sind lokal/Downloads.

**4) Schnell-Check nach Revert**

```bash
git checkout main
git pull --ff-only origin main
git log --oneline -n 5
# Prüfen: Revert-Commit ist auf main; Runbook-Inhalt entspricht erwartetem Stand.
```

### Exit
- Revert als Merge-Commit auf `main`; alter Tag unverändert; neuer Tag für korrigierten Stand; Consumer nutzen vorherigen Bundle bei Bedarf.
