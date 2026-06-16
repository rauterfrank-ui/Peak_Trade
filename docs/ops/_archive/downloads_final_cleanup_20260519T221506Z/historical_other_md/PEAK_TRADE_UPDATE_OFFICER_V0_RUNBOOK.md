# Peak_Trade — Update Officer v0 Runbook (Cursor Multi-Agent Orchestrator)

## Zweck

Dieses Runbook definiert einen **Update Officer v0** für Peak_Trade als **deterministischen, read-only, safety-first Update-Scout**. Ziel ist **nicht** autonomes Blind-Update, sondern ein kontrollierter Ablauf zum:

- Erkennen verfügbarer Updates
- Klassifizieren nach Risiko und Relevanz
- Erzeugen eines nachvollziehbaren Reports
- optionalen Erinnern / Review-Vorbereiten
- späteren Übergang zu einem strikt gegateten Auto-PR-Flow

Der v0-Scope ist bewusst konservativ: **keine direkte Mutation an `main`, keine stillen Änderungen, keine Berührung von Paper-/Shadow-/Evidence-Daten oder -Runs.**

---

## Leitplanken

### Harte Guardrails

- **Git-Kontext vor jedem Schritt explizit angeben**
- **Start immer auf `main` read-only**
- **keine Änderung an Paper-/Shadow-/Evidence-Daten oder laufenden Runs**
- **keine Live-/Runtime-Autorität**
- **kein autonomes Mergen**
- **kein direktes Updaten execution-naher Komponenten ohne separaten Policy-Entscheid**
- **alle Outputs unter eigenem Root**
- **Evidence/Audit-Trail first**
- **Reuse over invention**

### v0 ist ausdrücklich **nicht**

- kein autonomer Paket-Updater
- kein Hintergrund-Heiler
- kein „update everything"
- kein direkter Schreiber in produktive Configs, Locks, Requirements oder Dockerfiles
- kein System, das ohne menschliche Review mutiert

---

## Zielbild

Der Update Officer v0 ist das **Update-Gegenstück** zum Workflow Officer v0:

- **read-only**
- **profilgesteuert**
- **deterministisch**
- **report-orientiert**
- **ausbaubar**

Er beantwortet für definierte Oberflächen:

1. **Was ist updatebar?**
2. **Wie riskant ist das?**
3. **Ist es ein Kandidat für manuelle Review, Auto-PR oder Block?**
4. **Welche Verifikation wäre später notwendig?**

---

## Empfohlene Update-Kategorien

### A. Safe-Review-Kandidaten

Typisch niedriges Risiko, aber weiterhin review-pflichtig:

- Dev-Tooling: `ruff`, `pytest`, `mypy`, `black`-nahe Utilities
- rein dokumentationsnahe Tooling-Abhängigkeiten
- CI-Helfer ohne Produktionspfad
- lokale Dev-Only Utilities

### B. Manual-Review-Kandidaten

Höheres Risiko, aber grundsätzlich updatebar:

- `fastapi`, `uvicorn`, WebUI-nahe Dependencies
- MLflow-/Tracking-nahe Komponenten
- Build-/Packaging-Komponenten
- Test-Infrastruktur mit möglichem Seiteneffekt auf Artefakte

### C. Blocked / Governance-gated

Nicht durch Update Officer v0 mutierbar:

- execution-nahe Libraries
- Broker-/Exchange-Clients
- Risk-/Policy-/Safety-Kernpfade
- Evidence-/Manifest-/Schema-kritische Dependencies
- anything live-, shadow- oder paper-run relevant ohne separates Governance-Paket

---

## v0-Scope

### In Scope

- definierte Update-Flächen scannen
- verfügbare Updates sammeln
- Updates klassifizieren
- Report + JSONL + Markdown Summary erzeugen
- Ergebnis in Klassen ablegen:
  - `safe_review`
  - `manual_review`
  - `blocked`
  - `unknown`
- optionale Reminder-/Follow-up-Hinweise erzeugen

### Out of Scope

- direkte Dependency-Bumps
- Lockfile-Neuschreiben
- Docker-Image-Rebuilds
- Auto-PRs
- Auto-Merge
- Runtime-/Execution-Updates
- Mutation von Repo-Dateien im v0-Grundlauf

---

## Output-Root

Alle Outputs unter:

`out&#47;ops&#47;update_officer&#47;<ts>&#47;`

Empfohlene Dateien:

- `report.json`
- `events.jsonl`
- `summary.md`
- `manifest.json`
- `scan_inventory.json`
- `stdout.log`
- `stderr.log`

Wichtig:

- strikt getrennt von Paper-/Shadow-/Evidence-Produktionspfaden
- keine Vermischung mit bestehenden Evidence-Roots

---

## Empfohlene Profile

### `dev_tooling_review`

Zielt auf niedrigriskante Dev-/Lint-/Test-Abhängigkeiten.

### `web_stack_review`

Zielt auf WebUI-/API-nahe Pakete, aber nur read-only Bewertung.

### `ci_surface_review`

Zielt auf GitHub Actions, CI-Helfer, Workflow-Tooling.

### `full_update_inventory`

Reiner Inventurmodus ohne Änderungsabsicht.

---

## Empfohlene Modi

### `audit`

Nur Bestandsaufnahme + Klassifikation.

### `advise`

Audit plus konkrete Handlungs- und Review-Empfehlungen.

### `prepare`

Immer noch read-only, aber mit präziserem späteren Auto-PR-Plan je Kandidat.

---

## Zielarchitektur

### Kernmodule

- `src&#47;ops&#47;update_officer.py`
- `src&#47;ops&#47;update_officer_profiles.py`
- `src&#47;ops&#47;update_officer_schema.py`
- `src&#47;ops&#47;update_officer_markdown.py`

### Optional später

- `src&#47;webui&#47;update_officer_view.py` <!-- pt:ref-target-ignore -->
- `scripts&#47;ops&#47;run_update_officer.sh` <!-- pt:ref-target-ignore -->
- `tests&#47;ops&#47;test_update_officer.py`

### Datenfluss

1. Profile laden
2. definierte Scanner ausführen
3. Rohfunde normalisieren
4. Policy-/Risk-Klassifikation anwenden
5. Schema-validierten Report erzeugen
6. Markdown Summary rendern
7. optional Follow-up-Vorschläge ausgeben

---

## Normalisierte Report-Felder

### Pro Kandidat

- `surface`
- `package_or_target`
- `current_version`
- `latest_version`
- `update_kind`
  - `patch`
  - `minor`
  - `major`
  - `unknown`
- `risk_class`
  - `low`
  - `medium`
  - `high`
  - `blocked`
- `decision_class`
  - `safe_review`
  - `manual_review`
  - `blocked`
  - `unknown`
- `rationale`
- `recommended_next_action`
- `notes`

### Summary

- `total_candidates`
- `safe_review_count`
- `manual_review_count`
- `blocked_count`
- `unknown_count`
- `surface_counts`
- `update_kind_counts`
- `risk_class_counts`
- `decision_class_counts`

---

## Multi-Agent-Orchestrator-Rollen

### Agent 1 — Planner / Scope Officer

Verantwortung:

- Slice-Grenzen festziehen
- betroffene Oberflächen mappen
- Guardrails verifizieren
- keine Mutation

### Agent 2 — Repo Mapper

Verantwortung:

- bestehende Versionsquellen read-only finden
- z. B. `pyproject.toml`, `requirements*`, Dockerfiles, GitHub Workflows
- keine Änderungen

### Agent 3 — Policy Modeler

Verantwortung:

- Klassifikationslogik entwerfen
- Safe/Manual/Blocked-Matrix definieren
- execution-nahe Pfade explizit blocken

### Agent 4 — Implementer

Verantwortung:

- minimalen v0-Entrypoint bauen
- report/schema/markdown integrieren
- Outputs nur im dedizierten Root

### Agent 5 — Verifier

Verantwortung:

- Tests
- Ruff/Pytest
- Dry-run des Update Officer
- Validierung, dass keine produktiven Pfade berührt wurden

### Agent 6 — PR/Closeout Officer

Verantwortung:

- PR sauber formulieren
- Checks beobachten
- Post-Merge-Closeout
- finalen Handoff schreiben

---

## Reihenfolge der Umsetzung

## Phase 0 — Safety Freeze

Ziel:

- klarstellen, dass Update Officer v0 read-only ist
- Repo-/Daten-Guardrails dokumentieren

Exit-Kriterien:

- Scope akzeptiert
- keine Mutation von Paper-/Shadow-/Evidence-Daten vorgesehen

---

## Phase 1 — Read-only Repo Mapping

Ziel:

- vorhandene Update-Oberflächen im Repo ermitteln

Typische Fundorte:

- `pyproject.toml`
- `requirements*.txt`
- `constraints*.txt`
- Dockerfiles
- `.github&#47;workflows&#47;*.yml`
- Scripts mit Tool-Versionen

Ergebnis:

- `UPDATE_SURFACES_MAP.md` oder entsprechender Mapping-Abschnitt im Runbook

Exit-Kriterien:

- relevante Oberflächen gelistet
- blocked surfaces markiert

---

## Phase 2 — Policy / Risk Matrix

Ziel:

- definieren, welche Updates in welche Klasse fallen

Mindestmatrix:

| Surface | Beispiel | Risk | Decision |
|---|---|---:|---|
| Dev Tooling | ruff, pytest | low | safe_review |
| Web Stack | fastapi, uvicorn | medium | manual_review |
| CI Actions | action refs, helper tooling | medium | manual_review |
| Execution Clients | exchange/broker libs | high | blocked |
| Risk/Policy Core | safety-critical libs | high | blocked |

Exit-Kriterien:

- Klassifikation deterministisch beschrieben
- keine unklare Default-Autonomie

---

## Phase 3 — Minimal Entrypoint v0

Ziel:

- `src&#47;ops&#47;update_officer.py` als read-only CLI

Minimalfunktionen:

- `--mode`
- `--profile`
- `--output-root`
- scannt definierte Oberflächen
- erzeugt normalisierten Report

Exit-Kriterien:

- Lauf erzeugt `report.json`
- kein Repo-Mutationspfad

---

## Phase 4 — Schema Validation

Ziel:

- Report vor Finalisierung validieren

Exit-Kriterien:

- ungültiger Report führt deterministisch zu non-zero exit
- Enums/required fields abgesichert

---

## Phase 5 — Markdown Summary

Ziel:

- menschenlesbare Zusammenfassung erzeugen

Summary-Inhalt:

- Run-Metadaten
- Summary Counts
- Kandidaten-Tabelle
- empfohlene nächste Schritte
- blocked items separat sichtbar

Exit-Kriterien:

- `summary.md` wird geschrieben
- stabile Testabdeckung

---

## Phase 6 — Reminder / Review Hooks

Ziel:

- keine Autonomie, aber Review-Anstoß

Mögliche Varianten:

- Reminder-Text generieren
- „nächste Review empfohlen“ markieren
- später Automation/Reminder außerhalb des Repo-Flows

Exit-Kriterien:

- Reminder ist Output, keine Mutation

---

## Phase 7 — Optionaler v1-Vorbau für Auto-PR

Nicht Teil von v0, aber vorbereitbar:

- allowlistete surfaces
- branch-only mutation
- niemals `main` direkt
- PR + Tests + Audit Trail
- weiterhin kein Auto-Merge für kritische Flächen

---

## Acceptance-Kriterien für v0

Der Slice ist fertig, wenn:

- read-only Entrypoint existiert
- Profile existieren
- Klassifikation deterministic ist
- `report.json`, `events.jsonl`, `summary.md`, `manifest.json` geschrieben werden
- Schema-Validation aktiv ist
- Tests grün sind
- keine produktiven Datenpfade berührt werden

---

## Verbotene v0-Verhalten

Nicht erlauben:

- `pip install -U ...` im produktiven Repo-Kontext
- Lockfile-Rewrites ohne separaten Branch-Flow
- Dockerfile-Änderungen im Audit-Modus
- direkte Änderungen an GitHub Workflows im Audit-Modus
- selbstständiges Mergen
- selbstständiges Rebasen kritischer Update-PRs
- Upgrades execution-/broker-/policy-kritischer Libraries

---

## Konkreter v0-Einstiegsslice

Empfohlener erster Code-Slice:

1. `src&#47;ops&#47;update_officer.py`
2. `src&#47;ops&#47;update_officer_profiles.py`
3. `src&#47;ops&#47;update_officer_schema.py`
4. `src&#47;ops&#47;update_officer_markdown.py`
5. `tests&#47;ops&#47;test_update_officer.py`

MVP-Profil:

- `dev_tooling_review`

MVP-Oberflächen:

- Python-Dev-Tooling aus `pyproject.toml` / `requirements-dev` / vergleichbarer Quelle
- optional GitHub-Action-Versionen read-only inventarisieren

Warum dieser Slice zuerst:

- geringstes Risiko
- nützliches Ergebnis
- sauberer Audit-Trail
- gute Basis für späteres Auto-PR-Gating

---

## Empfohlener Branch-Plan

### Startkontext

- `GIT_CONTEXT=main`
- `BRANCH=main`
- `MODE=paper_stability_guard`

### Feature-Branch

- `feat&#47;update-officer-v0-min-slice`

### Spätere Folge-Slices

- `feat&#47;update-officer-v0-policy-matrix`
- `feat&#47;update-officer-v0-schema-validation`
- `feat&#47;update-officer-v0-markdown-summary`
- `feat&#47;update-officer-v0-reminder-hooks`

---

## Cursor Multi-Agent Orchestrator — empfohlener Ablauf

```bash
GIT_CONTEXT=main
BRANCH=main
MODE=paper_stability_guard
TOPIC=update_officer_v0_runbook_start

cd ~/Peak_Trade

git checkout main
git pull --ff-only origin main
git status --short --branch

git checkout -b feat/update-officer-v0-min-slice
```

```bash
GIT_CONTEXT=feature
BRANCH=feat/update-officer-v0-min-slice
MODE=paper_stability_guard
TOPIC=update_officer_v0_readonly_mapping

cd ~/Peak_Trade

python3 - <<'PY'
from pathlib import Path

candidates = [
    'pyproject.toml',
    'requirements.txt',
    'requirements-dev.txt',
    'constraints.txt',
    '.github/workflows',
]

for item in candidates:
    p = Path(item)
    print(f'{item}\tEXISTS={p.exists()}\tIS_DIR={p.is_dir()}\tIS_FILE={p.is_file()}')
PY
```

```bash
GIT_CONTEXT=feature
BRANCH=feat/update-officer-v0-min-slice
MODE=paper_stability_guard
TOPIC=update_officer_v0_impl_mvp

cd ~/Peak_Trade

mkdir -p src/ops tests/ops docs/ops/runbooks
```

```bash
GIT_CONTEXT=feature
BRANCH=feat/update-officer-v0-min-slice
MODE=paper_stability_guard
TOPIC=update_officer_v0_verify

cd ~/Peak_Trade

python3 -m pytest -q tests/ops/test_update_officer.py
python3 -m ruff check src/ops/update_officer.py src/ops/update_officer_profiles.py src/ops/update_officer_schema.py src/ops/update_officer_markdown.py tests/ops/test_update_officer.py
python3 src/ops/update_officer.py --mode audit --profile dev_tooling_review
```

```bash
GIT_CONTEXT=feature
BRANCH=feat/update-officer-v0-min-slice
MODE=paper_stability_guard
TOPIC=update_officer_v0_pr

cd ~/Peak_Trade

git add src/ops/update_officer.py src/ops/update_officer_profiles.py src/ops/update_officer_schema.py src/ops/update_officer_markdown.py tests/ops/test_update_officer.py docs/ops/runbooks

git commit -m "feat(ops): add update officer v0 minimal readonly scout"
git push -u origin feat/update-officer-v0-min-slice
```

---

## Spätere Autonomie — nur unter strikten Bedingungen

Ein späterer **Update Officer v1** darf erst kommen, wenn alle folgenden Punkte erfüllt sind:

- klare allowlist existiert
- blocked surfaces technisch ausgeschlossen sind
- branch-only mutation erzwungen ist
- vollständiger Verify-Plan existiert
- PR-Erzeugung reproduzierbar funktioniert
- kein Einfluss auf Paper-/Shadow-/Evidence-Läufe besteht
- Governance-Entscheid dokumentiert ist

Dann wäre denkbar:

- Auto-PR für Dev-Tooling-Patch-/Minor-Updates
- niemals Auto-Merge für kritische Kategorien
- niemals Direktänderung auf `main`

---

## Klare Empfehlung

Für Peak_Trade jetzt **nicht** mit autonomem Updaten starten.

Stattdessen:

1. **Update Officer v0** als read-only Scout
2. danach **v1 Auto-PR nur für allowlistete Low-Risk-Surfaces**
3. alles andere bleibt `manual_review` oder `blocked`

Das passt zu deinem bisherigen Sicherheitsmodell und unterläuft nicht die Paper-/Shadow-/Evidence-Guardrails.

---

## Guter nächster Prompt

`Nutze dieses Runbook und schneide für Peak_Trade einen minimalen Update-Officer-v0-Slice aus. Erst read-only die Update-Oberflächen mappen, dann einen kleinen Feature-Branch-Plan machen. Keine Mutation von Paper&#47;Shadow&#47;Evidence.`
