# Queue am effizientesten durchziehen

**Zweck:** Regeln für PR-Größe, Merge-Reihenfolge und Definition of Done, damit die Queue zügig und konsistent abgearbeitet werden kann.

---

## Regeln

### PR-Größe

- **200–500 LOC netto** pro PR
- **Maximal 1–2 Themen** pro PR

### Merge-Reihenfolge

1. **Docs/Contracts zuerst** → PR-01  
2. **Enforcement** → PR-02, PR-10  
3. **Providers/Telemetry** → PR-03, PR-04, PR-05  
4. **Data correctness** → PR-06, PR-07, PR-08, PR-09  

### Definition of Done pro PR

- **Grüne Tests** (CI grün)
- **Ein „Expected Artifacts“-Beispiel** in `docs/` oder `reports/fixtures/`

---

## PR-Queue (Platzhalter für konkrete PRs)

| PR   | Thema / Schwerpunkt      | Reihenfolge | Erwartete Pfade / Themen |
|------|--------------------------|-------------|---------------------------|
| PR-01 | Docs/Contracts           | 1           | Verträge, SSoT-Docs, erwartete Artefakte |
| PR-02 | Enforcement              | 2           | Validierung, Guards       |
| PR-10 | Enforcement (weitere)    | 2           | wie PR-02                 |
| PR-03 | Providers                | 3           | Adapter, Datenquellen     |
| PR-04 | Telemetry (Teil 1)      | 3           | Metriken, Logging         |
| PR-05 | Telemetry (Teil 2)      | 3           | Evals, Exporter           |
| PR-06 | Data correctness (1)   | 4           | Schema, Validierung       |
| PR-07 | Data correctness (2)   | 4           | Fixtures, Contracts       |
| PR-08 | Data correctness (3)   | 4           | Report-Compare, Index     |
| PR-09 | Data correctness (4)   | 4           | Regression, Golden       |

*(Inhalt von PR-01…PR-10 kann je nach Backlog angepasst werden.)*

### PR-Queue (DoD & Evidence)

| PR | Thema | Scope | DoD | Evidence |
|---|---|---|---|---|
| PR-01 | Status-Matrix + Evidence-Schema v1 + GATES-Overview konsolidieren | docs/ops + docs/ops/evidence | ✅ markdown konsistent, ✅ Claims nutzen status enums, ✅ Evidence pack example vorhanden | docs/ops/evidence/packs/PR-01/EV-2026-02-PR01-000.json |

---

## Relevante Repo-Pfade (für konkrete Patches)

Damit pro PR konkrete Commit-Patches (Diff-Style: neue Files, Signaturen, Testnamen) formuliert werden können, hier die relevanten Verzeichnisse und Dateitypen.

### Docs / Contracts (PR-01)

- `docs/ops/` – Ops-Docs, Runbooks, Merge-Logs, Gates
- `docs/ai/`, `docs/execution/`, `docs/risk/`, `docs/governance/` – fachliche Verträge
- `docs/webui/observability/` – Observability-Contracts
- `.cursor/rules/`, `.github/` – Projekt- und CI-Contracts
- Typische Artefakte: `docs/ops/evidence/`, `docs/ops/EVIDENCE_SCHEMA.md`, `docs/ops/GATES_*.md`

### Enforcement (PR-02, PR-10)

- `scripts/ops/` – Validatoren, Guards (z. B. `validate_workflow_dispatch_guards.py`, `check_merge_log_hygiene.py`, `validate_docs_token_policy.py`)
- `scripts/ci/` – CI-Validierung (`validate_required_checks_hygiene.py`, `guard_no_tracked_reports.sh`)
- `.github/workflows/` – Workflows als Enforcement (Gates)
- `src/governance/`, `src/live/safety.py`, `src/data/safety/` – Runtime-Enforcement

### Providers / Telemetry (PR-03, PR-04, PR-05)

- `src/data/providers/`, `src/data/feeds/` – Datenprovider
- `src/obs/` – Observability, OTel, metricsd (`src/obs/otel.py`, `src/obs/metricsd.py`)
- `scripts/obs/` – Exporter, Stage1, Grafana/Prometheus
- `src/notifications/`, `src/infra/escalation/` – Alerts, Eskalation
- `config/telemetry_alerting.toml`, `config/model_registry.toml` – Telemetrie-Config

### Data correctness (PR-06, PR-07, PR-08, PR-09)

- `src/risk/validation/` – VaR report_compare, report_index
- `tests/risk/validation/`, `tests/fixtures/var_suite_reports/` – VaR-Fixtures
- `src/execution/replay_pack/`, `src/ai_orchestration/` – Replay, Evidence Pack, Critic-Schema
- `tests/fixtures/evidence_packs/`, `tests/fixtures/transcripts/` – erwartete Artefakte
- `scripts/risk/var_suite_*.py`, `scripts/aiops/` – Report-Tools
- `reports/` – nur über Artifacts/fixtures; typisch `reports/fixtures/` oder Beispiele unter `docs/`/`tests/fixtures/`

### Expected Artifacts / Fixtures (DoD)

- `docs/ops/evidence/` – Evidence-Beispiele
- `tests/fixtures/` – JSON/Parquet/JSONL für Tests
- `reports/fixtures/` – falls genutzt; sonst Beispiele in `docs/` (z. B. `docs/ops/.../example_*.json`)

---

## Nächster Schritt: konkrete Patches

- **Repo ist lokal verfügbar:** `/Users/frnkhrz/Peak_Trade` (bzw. Projektroot).
- Wenn du pro PR konkrete **Commit-Patches (Diff-Style)** willst: entweder
  - **PR-Thema konkretisieren** (z. B. „PR-01 = nur docs/ops/GATES_OVERVIEW.md + EVIDENCE_SCHEMA Anpassung“), dann können neue Files, geänderte Signaturen und Testnamen 1:1 vorgeschlagen werden, oder
  - **Dateiliste pro PR** angeben (z. B. „PR-03: scripts/obs/ai_live_exporter.py, config/...“), dann können Diffs dazu formuliert werden.

Dieses Doc kannst du als Referenz nutzen, wenn du (oder jemand anderes) die Patches formuliert.
