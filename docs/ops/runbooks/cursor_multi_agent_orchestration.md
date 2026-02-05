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

### Exit
- Nur PRs mit grüner CI gemerged; Runbook-Änderungen durch Docs-Gate abgesichert.

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
