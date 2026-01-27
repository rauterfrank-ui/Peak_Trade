# Peak_Trade — Projekt-Summary v2 (Gliederung / Redaktionsplan)

**Ziel:** Diese Gliederung macht die bestehende Datei `docs/PEAK_TRADE_PROJECT_SUMMARY_CURRENT_2026-01-27.md` zu einer *arbeitsfähigen* **Start-/Gate-/Governance-Landkarte** (statt nur „Ist-Stand-Text“).

**Hinweis zur Token-Policy:** Inline-Pfade in Prosa bitte ggf. mit `&#47;` escapen (z.B. `docs&#47;ops&#47;...`). In Code-Fences sind normale Pfade/Commands OK.

---

## Inhaltsverzeichnis (v2)

0. **Purpose & Audience**
1. **Quick Links (One-Page)**
2. **Start Here (by persona)**
3. **System Map (Mermaid)**
4. **Repo & Governance Context**
5. **Architecture (High-Level)**
6. **Codebase Map (`src/` Domains)**
7. **Config Map (Single Source of Truth)**
8. **Safety & Risk: Non‑Negotiables**
9. **CI & Gates Index (Matrix)**
10. **Change Impact Map (Path → Gate/Owner/Approval)**
11. **Ops Center: Runbooks, Evidence, Incident**
12. **Outputs & Artefacts (Where results land)**
13. **Happy Paths (golden workflows)**
14. **Toolchain Standard & Common Pitfalls**
15. **Stability / Readiness Matrix**
16. **Known Gaps (documented only) & Next Steps (governance‑safe)**
A. **Glossary & Conventions**
B. **FAQ / Troubleshooting (Top 10)**

---

## 0) Purpose & Audience (neu, P0)

**One‑liner purpose:** *Repo‑Einstieg + Orientierung + CI/Gates‑Landkarte + Governance/Safety‑Vertrag + Output‑Pfadkarte.*

**Audience / Jump links**
- **Developer:** Setup, Module, Tests/Lint, CI‑Repro → §2.1, §6, §9, §14
- **Operator/Ops:** Runbooks, Docs Gates, Evidence, Incident → §2.2, §11, §9, §12
- **Research:** Backtest/Sweeps/Reporting/Data → §2.3, §5–§6, §13, §12
- **Audit/Compliance (intern):** Governance‑Invarianten, Approval‑Pflichten, Evidence‑Flow → §4, §8–§10, §12

**Non‑Goals**
- Kein vollständiges Runbook (dafür: Runbooks-Index).
- Keine Spekulation in „Known Gaps“: nur belegbare Items (Docs/TODOs/Runbooks/Issues).

*Bestehender Inhalt, der hierher wandert:* Teile aus „1) Kurzbeschreibung“.

---

## 1) Quick Links (One‑Page) (neu, P0)

**Frontdoors**
- `README.md`
- `docs/PEAK_TRADE_OVERVIEW.md`
- `docs/ARCHITECTURE_OVERVIEW.md`
- `WORKFLOW_FRONTDOOR.md` (falls vorhanden)
- Ops Hub / Runbooks Index (link)

**Key run flows**
- Backtest suite / reporting quickstart (link)
- Docs Gates snapshot script (link)
- Evidence Index / Merge logs (link)

*Quelle:* Streu‑Links aus §1/§9/§10 zusammenziehen.

---

## 2) Start Here (by persona) (neu, P0)

### 2.1 Developer Start
- Setup: python3, env tool (uv/pip), optional docker
- “Edit → test → format → docs gates snapshot → PR” (5‑Step)
- Top commands (code fences):
  - `uv run pytest -q`
  - `ruff format` / `ruff check`
  - docs gates snapshot script (falls vorhanden)

### 2.2 Operator Start
- “Verify → evidence → index → merge log” (5‑Step)
- Wo ist Ops‑Center / wichtigste Runbooks
- CI Health: required checks vs signal checks
- Evidence Packs: wo, wann, wieso

### 2.3 Research Start
- Data pipeline entry points
- Backtests / sweeps / robustness
- Reporting generator (single & compare)
- Repro/Determinism notes

### 2.4 Audit/Compliance Start (optional)
- Non‑negotiables checklist
- Approval required actions
- Evidence artifacts & retention

---

## 3) System Map (Mermaid) (neu, P1)

> **Mermaid block** (ein Diagramm, maximal 2). Vorschlag:

```mermaid
flowchart LR
  A[Data Ingest] --> B[Strategies]
  B --> C[Signals & Sizing]
  C --> D[Risk Layer]
  D --> E[Backtest / Research]
  D --> F[Execution (Shadow/Paper/Testnet)]
  E --> G[Reporting]
  F --> G
  G --> H[Evidence / Docs / Merge Logs]

  subgraph Gates[Governance & Gates]
    X1[CI Required Checks]
    X2[Docs Integrity Gates]
    X3[Policy / Critic Gate]
    X4[Evidence Pack Gate]
  end

  X1 -.-> H
  X2 -.-> H
  X3 -.-> F
  X4 -.-> H
```

---

## 4) Repo & Governance Context (ausbauen, P0)

- Remote/Ownership: Repo, Branch protection, CODEOWNERS
- Governance‑Philosophie: **fail‑closed**, Defense‑in‑Depth, NO‑LIVE default
- „Was ist verboten?“ (Secrethygiene, direkte live toggles ohne gates)

*Basis:* bestehende §2 („GitHub/Repo-Umfeld“) + §6 („Risk & Safety“).

---

## 5) Architecture (High-Level) (bestehend, leicht straffen)

- 6–10 bullets: Subsysteme + Verantwortlichkeiten
- Link‑Hub zu tieferen Architekturdocs

*Basis:* bestehende §3.

---

## 6) Codebase Map (`src/` Domains) (bestehend + klarer)

- Tabelle: Domain | Responsibility | Key modules | Primary consumers | Tests?
- Fokus: „womit fange ich an“ statt vollständigem Listing

*Basis:* bestehende §4.

---

## 7) Config Map (Single Source of Truth) (P1)

**Ziel:** „Welche config wofür?“ + „SSoT pro Flow“.

- Tabelle: Config | Purpose | Used by | Safety critical? | Typical edits | Approval required?
- Klarstellen, ob `config.toml` vs `config/config.toml` unterschiedliche Rollen haben
- Profile/Environments (wenn vorhanden): paper/shadow/testnet/… (nur belegbar)

*Basis:* bestehende §5.

---

## 8) Safety & Risk: Non‑Negotiables (neu/ausbauen, P0)

### 8.1 Non‑Negotiables (checkable)
- NO‑LIVE default (locked)
- Fail‑closed (policy critic / gates)
- No secrets in repo
- SoD (Operator vs automation)
- Determinism expectations (wo relevant)

### 8.2 Operator Approval Required (nur belegbar)
- Liste kritischer Pfade (Execution/Risk/Governance/Live‑adjacent)
- Referenz: gate/workflow/runbook, das es enforced

*Basis:* bestehende §6, aber als Checkliste.

---

## 9) CI & Gates Index (Matrix) (neu, P0)

**Tabelle (Pflichtspalten):**
| Gate/Workflow | Required? | Trigger | Docs‑only Verhalten | Fail‑Semantik | Lokale Repro‑Commands |
|---|---:|---|---|---|---|

**Initiale Zeilen (aus aktuellem Stand)**
- `ci.yml` (Tests/Contract)
- `docs_reference_targets_gate.yml`
- `docs_token_policy_gate.yml`
- `policy_critic_gate.yml`
- `evidence_pack_gate.yml`
- `mcp_smoke_preflight.yml` (Signal)

> Jede Zeile: genau sagen „was bricht“ und „wie reproduziere ich lokal“.

*Basis:* bestehende §8 („Auszug“) → in Matrix umformen.

---

## 10) Change Impact Map (neu, P1)

Kurze Tabelle: **Pfad/Domain → welche Gates/Owners/Approval werden relevant?**

Beispiele (nur wenn belegbar):
- Änderungen unter `docs/` → Docs Integrity Gates
- Änderungen unter `src/execution/` → Policy Critic strict + extra review
- Änderungen unter config risk/killswitch → approval required

---

## 11) Ops Center: Runbooks, Evidence, Incident (bestehend + strukturieren)

- Runbooks Index + „wie finde ich das richtige Runbook?“
- Evidence: IDs, Index, Packs
- Incident: escalation primitives / oncall (nur belegbar)

*Basis:* bestehende §9.

---

## 12) Outputs & Artefacts (neu, P1)

**Ziel:** „Wo liegen Ergebnisse?“ + „committed vs gitignored“.

- Reports (HTML/JSON) — default output paths
- Evidence packs — committed location
- Logs / smoke outputs — gitignored location
- Flow: Run → Artefacts → Validate → Evidence Index → Merge Log

---

## 13) Happy Paths (bestehend, aber persona‑zentriert)

- Developer happy path
- Operator happy path
- Research happy path

*Basis:* bestehende §10, aber nach Persona splitten.

---

## 14) Toolchain Standard & Common Pitfalls (P1)

- python3, uv/pip, ruff, pre-commit, pytest
- docker compose optional (mlflow, prom/grafana)
- „häufige Fallen“ (python alias, missing extras, macOS issues)

*Basis:* bestehende §7 + §11.

---

## 15) Stability / Readiness Matrix (neu, P2)

Tabelle:
| Area | Readiness | Tests present | Runbook present | Evidence flow | Notes |
|---|---|---:|---:|---:|---|

Bereiche: Backtest, Data, Risk, Execution pipeline, WebUI, Observability, AI autonomy.

---

## 16) Known Gaps & Next Steps (neu, P2)

**Regel:** nur *documented only*.
- „Known gaps“: Link auf Quelle (doc/TODO/runbook)
- „Next steps“: kurz, governance‑safe, priorisiert

---

## A) Glossary & Conventions (neu, P1)

- Evidence IDs (EV_*), Evidence Packs
- Merge logs (PR_###_MERGE_LOG.md)
- Runbooks / frontdoors
- Gates: required vs signal
- „watch-only“ / „no-live“ Begriffe

---

## B) FAQ / Troubleshooting (neu, P1)

Top 10:
- Docs token policy failure (wie fix)
- Docs reference targets failure
- ruff format/check failures
- pytest env issues
- docker ports/prometheus/grafana datasource mismatch
- policy critic gate interpretation
- evidence pack gate expectations

---

## Migrationshinweise (wo existierende Sections hin sollen)

- **Aktuelle §1 Kurzbeschreibung** → split in §0 Purpose & §1 Quick Links
- **Aktuelle §2 Repo-Umfeld** → §4 Repo & Governance
- **Aktuelle §3/§4** → §5/§6 (nur straffen)
- **Aktuelle §5** → §7 Config Map
- **Aktuelle §6** → §8 Non‑Negotiables
- **Aktuelle §7/§11** → §14 Toolchain & Pitfalls
- **Aktuelle §8** → §9 CI & Gates Matrix
- **Aktuelle §9** → §11 Ops Center
- **Aktuelle §10** → §13 Happy Paths
- **Aktuelle §12** → verteilt in §16 + ggf. §15

---

## Akzeptanzkriterien (Definition of Done)

- Oben steht Purpose + Persona‑Jump‑Links.
- Start‑Here enthält pro Persona: 5–10 präzise bullets + 3–6 Commands (code fences).
- CI/Gates Matrix deckt alle zentralen Workflows ab und hat **lokale Repro‑Commands**.
- Non‑Negotables sind als **checkbare** Liste formuliert und (wo möglich) referenzieren Enforcer (workflow/script/runbook).
- Outputs & Artefacts erklären **wo** Ergebnisse landen und was committed ist.
- Ein Mermaid Diagramm macht die Seite in <60s scannbar.
