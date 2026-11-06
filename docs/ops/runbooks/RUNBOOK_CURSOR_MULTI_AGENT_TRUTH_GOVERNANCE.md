# RUNBOOK — Cursor Multi-Agent Orchestrator für Truth / Docs / Drift Governance

Stand: 2026-04-01  
Status: aktiv nutzbares Ops-Runbook  
Scope: Repo-Truth-Claims, Docs-Drift-Guard, Canonical-Docs-Nachzug, PR-Disziplin  
Nicht im Scope: semantischer Vollbeweis für das gesamte Repo, Live-Trading-Freigabe, GitHub-Workflow-Umbau außerhalb dieses Runbooks

---

## 1. Zweck

Dieses Runbook beschreibt, wie der Cursor Multi-Agent Orchestrator Änderungen so führt, dass:

- sensible Repo-Bereiche nicht stillschweigend an Canonical-Docs vorbeilaufen
- definierte Repo-Truth-Claims maschinenprüfbar bleiben
- Docs-Drift systematisch erkannt und aktiv nachgezogen wird
- Workflow Officer und Update Officer auf demselben Truth-Unterbau arbeiten

Dieses Runbook ist kein allgemeiner Wahrheitsbeweis für das gesamte Repo.  
Es operationalisiert einen prüfbaren Wahrheitsstatus für definierte Claims und sensible Bereiche.

---

## 2. Zielbild

Unter einem gemeinsamen Dach arbeiten vier Ebenen zusammen:

1. **Truth Map**
   - Zuordnung: sensibler Bereich → Canonical Docs

2. **Repo Truth Claims**
   - maschinenlesbare, prüfbare Claims
   - Status: `PASS`, `FAIL`, `UNKNOWN`

3. **Docs Drift Guard**
   - prüft bei sensiblen Änderungen, ob zugehörige Canonical Docs mitgezogen wurden

4. **Officer-Sicht**
   - Workflow Officer: nächste Schritte, offene Truth-Lücken
   - Update Officer: Drift, veraltete Aussagen, Claim-Abweichungen

---

## 3. Relevante Dateien

### Truth / Guard / Claims

- `config/ops/docs_truth_map.yaml`
- `config/ops/repo_truth_claims.yaml`
- `scripts/ops/check_docs_drift_guard.py`
- `scripts/ops/check_repo_truth_claims.py`

### Unified Truth Core

- `src/ops/truth/models.py`
- `src/ops/truth/loaders.py`
- `src/ops/truth/evaluator.py`
- `src/ops/truth/git_refs.py`
- `src/ops/truth/__init__.py`

### Doku

- `docs/ops/registry/DOCS_TRUTH_MAP.md`
- `docs/ops/registry/REPO_TRUTH_CLAIMS.md`
- `docs/ops/registry/TRUTH_CORE.md`

### Typische High-Level-Docs für kritische Änderungen

- `docs/GOVERNANCE_AND_SAFETY_OVERVIEW.md`
- `docs/PEAK_TRADE_V1_KNOWN_LIMITATIONS.md`
- `docs/ops/runbooks/CANARY_LIVE_ENTRY_CRITERIA.md`

---

## 4. Wann dieses Runbook benutzt wird

Dieses Runbook ist zu verwenden, wenn ein PR mindestens eine der folgenden Klassen berührt:

- `src/execution/` (Präfix; Drift-Guard-Logik wie in Truth Map)
- `src/orders/`
- `src/core/environment.py`
- Governance-/Safety-High-Level-Doku
- bounded-pilot-/live-entry-bezogene Runbooks oder Specs
- J1-/Forward-Pipeline-Docs, wenn Datenpfade, UTC-/as_of-Verträge oder Loader-Verhalten geändert werden
- Learning-/Promotion-Truth- oder Drift-Schicht

---

## 5. Multi-Agent-Rollen

### Agent A — Scope / Sensitive Area Triage

Aufgabe:

- identifiziert, ob die Änderung in einen sensitiven Bereich fällt
- liest `docs_truth_map.yaml`
- bestimmt erwartete Canonical Docs

Output:

- Liste betroffener Bereiche
- Liste betroffener Canonical Docs
- Entscheidung: Drift-Guard relevant ja/nein

### Agent B — Claim Impact

Aufgabe:

- prüft, ob bestehende Claims betroffen sind
- ergänzt neue Claims, wenn neue Capability / neue Governance-Aussage hinzukommt
- markiert unklare Stellen als `UNKNOWN`, wenn noch keine maschinenprüfbare Definition vorliegt

Output:

- Claims: unverändert / angepasst / neu erforderlich

### Agent C — Docs Sync

Aufgabe:

- zieht Canonical Docs nach
- schärft Sprache auf Default vs. Ausnahme vs. bounded Scope
- entfernt pauschale Altaussagen, wenn sie nicht mehr vollständig stimmen

Output:

- konkrete Doku-Änderungen
- konsistente Canonical-Formulierung

### Agent D — Guard / Check Execution

Aufgabe:

- führt lokale Checks aus
- bewertet die Statuswerte `PASS`, `FAIL`, `UNKNOWN` (siehe `TruthStatus` in `src/ops/truth/models.py`)
- bricht Merge-Vorbereitung ab, wenn Drift oder Claim-Fails offen bleiben

Output:

- prüfbarer Status für PR-Freigabe

### Agent E — Officer Feed

Aufgabe:

- formuliert knapp, was Workflow Officer / Update Officer später sehen müssen
- aktualisiert bei Bedarf Runbook-/Registry-/Focus-Doku

Output:

- Truth-/Drift-relevante Kurz-Zusammenfassung für den nächsten Operator-Schritt

---

## 6. Standardablauf pro PR

### Phase 1 — Scope feststellen

1. Geänderte Dateien sichten.
2. Prüfen, ob sensitive Bereiche betroffen sind.
3. Canonical Docs aus `docs_truth_map.yaml` ableiten.

### Phase 2 — Claim-Relevanz prüfen

1. Prüfen, ob bestehende Claims berührt werden.
2. Falls neue Capability eingeführt wird:
   - neuen Claim ergänzen, oder
   - bewusst als noch nicht formalisiert dokumentieren

### Phase 3 — Docs nachziehen

1. Nur lokale Doku im PR-Scope ändern.
2. High-Level-Docs nur dort anfassen, wo die Aussage wirklich betroffen ist.
3. Keine Marketing-Sprache; immer:
   - Default
   - Ausnahme
   - Grenzen
   - Gating

### Phase 4 — Checks lokal ausführen

Pflicht bei Truth-/Docs-/Governance-Änderungen:

```bash
python3 scripts/ops/check_docs_drift_guard.py --base origin/main
python3 scripts/ops/check_repo_truth_claims.py
python3 scripts/ops/validate_docs_token_policy.py --base origin/main
./scripts/ops/verify_docs_reference_targets.sh --changed --base origin/main
```

**Erwartung:** alle Kommandos beenden mit Exit `0`.  
Bei Drift-Guard Exit `1`: mindestens eine erwartete Canonical-Doku fehlt im Diff — nachziehen oder Truth Map bewusst anpassen (mit Review).  
Bei Token-Policy oder Reference-Targets Exit `1`: Inline-Code-Pfade und Backticks gemäß Gates korrigieren (siehe bestehende Operator-Runbooks unter „Docs Gates & Policies“).

Vor den Checks: `git fetch origin` sinnvoll, damit die Basis-Ref (z. B. `origin&#47;main`) existiert.

### Phase 5 — PR-Evidence

- Truth Map / Claims / Registry-Änderungen sind im PR nachvollziehbar committet.
- Optional: Agent E Kurzblock im PR-Body (betroffene Bereiche, erledigte Checks).
- **CI (GitHub):** Pull Requests laufen die Jobs **`docs-drift-guard`** und **`repo-truth-claims`** (Workflow `.github/workflows/truth_gates_pr.yml`). Repo-Admins können diese Namen unter Branch Protection als **Required** setzen, sobald die Checks auf dem Ziel-Branch sichtbar sind.

---

## 7. Exit-Codes (Kurzreferenz)

| Werkzeug | `0` | `1` | `2` |
| --- | --- | --- | --- |
| Docs Drift Guard | OK | Drift | Git/Konfiguration |
| Repo Truth Claims | alle PASS | mindestens ein FAIL | UNKNOWN / Konfiguration |
| Token Policy / Reference Targets | OK | Verstöße | (Skriptfehler) |

---

## 8. Siehe auch

- `docs/ops/registry/TRUTH_CORE.md` — gemeinsame Truth-Schicht (`ops.truth`)
- `docs/ops/runbooks/README.md` — Index der Operator-Runbooks (Docs Gates)
