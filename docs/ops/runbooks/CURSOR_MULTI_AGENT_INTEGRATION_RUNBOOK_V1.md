# Peak_Trade Runbook: Cursor Multi-Agent Integration (V1)

Stand: 2026-01-05  
Scope: Engineering-Workflow & Agent-Governance.  
Out of scope: Jede Form von autonomer Live-Execution oder Governance-Unlock.

---

## 0) Zielbild (was „fertig integriert" bedeutet)

Wir nutzen Cursor Multi-Agents als **lokalen, auditierbaren Delivery-Booster**:

- **Multi-Agents (bis zu 8 parallel)** auf derselben Aufgabe (Best-of-N) ODER gesplittet auf Teilaufgaben (Task-Split), ohne File-Konflikte dank isolierter **Git-Worktrees**.
- **Standardisierte Agent-Governance** über versionierte Cursor **Rules** und **Slash-Commands** im Repo.
- **Reproduzierbarkeit**: Jeder Agent-Run liefert
  - "Changed files"
  - "Tests executed"
  - "Verification note"
  - optional "Trace/Run ID"
- **Evals als Gate (P0 lokal, P1 CI)** via promptfoo (Eval + Red Team).
- Optional: **Observability/Tracing** (Langfuse) für Agent-Runs, nicht für Trading-Runtime.

---

## 1) Safety & Governance (nicht verhandelbar)

### 1.1 Prime Directive
1) **Keine autonome Live-Execution.**  
2) **Keine Umgehung von Governance-Locks / Risk-Gates / Safety-Gates.**  
3) Änderungen an `src/execution/**`, `src/governance/**`, `src/risk/**`, Live-Track/Live-Runner nur mit **expliziter manueller Freigabe** und **erweiterter Testsuite**.

### 1.2 Secrets & Prompt-Injection
- Keine Tokens/Keys in Repo, Chat, Rules, Commands.
- Externes Material (Web-Snippets, Issues, Logs) immer als **untrusted input** behandeln.
- Agent darf nie "export secrets" / "print env" / "upload files" ausführen.

### 1.3 Terminal-Sandbox
Cursor 2.0 auf macOS führt Agent-Shell-Commands standardmäßig in einer **Sandbox** aus (Workspace R/W, kein Internet). Das ist erwünscht.

---

## 2) Voraussetzungen

### 2.1 Tooling (Operator)
- Cursor ≥ 2.0 (Multi-Agents / Worktrees / Sandbox).
- Git (worktree support).
- Python venv für Peak_Trade (wie im Repo standard).
- Node.js für promptfoo-Runs (lokal/CI), siehe promptfoo prerequisites.

### 2.2 Repo-Artefakte (in diesem Runbook angelegt)
- `.cursor/rules/*.mdc` (Project Rules)
- `.cursor/commands/*.md` (Slash-Commands)
- `evals/aiops/**` (promptfoo configs)
- `docs/ai/**` (AI-RFC/Runbooks)

---

## 3) Multi-Agent Betriebsmodi (wann welchen nutzen)

### Modus A — Best-of-N (gleiche Aufgabe, mehrere Modelle)
Use when:
- Architekturentscheidungen
- Refactor-Strategien
- "Find the cleanest fix"

Wie es funktioniert:
- Jeder Agent läuft in isoliertem Worktree, du vergleichst Ergebnisse und klickst "Apply All" auf die beste Lösung.

### Modus B — Task-Split (jeder Agent macht eine Teilaufgabe)
Use when:
- klar separierbare Workstreams (Tests / Docs / Code / Evals / Refactor)
- große Changesets, aber mit klaren Interfaces

Bewährtes Muster:
- Cursor Multi-Agents geben standardmäßig **allen denselben Prompt**; daher koordinieren wir über `.agent-id` und eine Task-Matrix: Agent liest `.agent-id`, führt nur „seine" Task aus.

---

## 4) Repo-Integration: Rules + Commands + Evals (P0)

### 4.1 Branch & Sauberkeit
Wir integrieren die Toolchain wie eine normale Peak_Trade Phase:
- Feature-Branch, kleine Commits, Merge-Log.

#### Terminal Pre-Flight (robust)
> Hinweis: Wenn du in einer Continuation festhängst (`>`, `dquote>`, heredoc>): **Ctrl-C**.

```bash
# PRE-FLIGHT (robust)
cd /Users/frnkhrz/Peak_Trade

pwd
git rev-parse --show-toplevel
git status -sb

# Start branch
git switch -c feat/aiops-cursor-multiagent-v1
```

### 4.2 Verzeichnisstruktur anlegen

```bash
mkdir -p .cursor/rules .cursor/commands evals/aiops/tests/testcases docs/ai
```

### 4.3 Dateien (siehe Repo)

**Rules:**
- `.cursor/rules/peak-trade-governance.mdc` — Prime Directive, High-Risk Paths
- `.cursor/rules/delivery-contract.mdc` — Workflow, Completion Block

**Commands:**
- `.cursor/commands/pt-preflight.md` — Repo Pre-Flight Check
- `.cursor/commands/pt-plan.md` — Structured Planning
- `.cursor/commands/pt-split.md` — Parallel Agent Coordination
- `.cursor/commands/pt-verify.md` — Verification Checklist
- `.cursor/commands/pt-merge-log.md` — Merge-Log Draft Generator
- `.cursor/commands/pt-eval.md` — Promptfoo Eval Runner

**Evals:**
- `evals/aiops/promptfooconfig.yaml` — Main Config
- `evals/aiops/tests/testcases/docs_link_fixer.yaml` — Path Restriction Test
- `evals/aiops/tests/testcases/ci_failure_triage.yaml` — Secret Leakage Test
- `evals/aiops/README.md` — Promptfoo How-To

---

## 5) Workflow-Beispiele

### Beispiel 1: Best-of-N (Refactor-Strategie)
```
Operator: "Refactor src/portfolio/rebalancer.py for better testability."
- Cursor startet 3 Agents (Claude, GPT-4, Gemini)
- Jeder Agent arbeitet in isoliertem Worktree
- Operator vergleicht Ergebnisse und wählt beste Lösung
```

### Beispiel 2: Task-Split (große Feature-Implementierung)
```
Operator: "Implement Portfolio VaR monitoring with tests and docs."
- Agent 1 (.agent-id = 1): Implement core logic in src/risk/var_monitor.py
- Agent 2 (.agent-id = 2): Write tests in tests/test_var_monitor.py
- Agent 3 (.agent-id = 3): Write docs in docs/risk/VAR_MONITORING.md
- Agent 4 (.agent-id = 4): Add CLI integration
```

---

## 6) Evals als Quality Gate (P0 lokal)

**Vor jedem PR:**
```bash
# Run evals
npx promptfoo@latest eval -c evals/aiops/promptfooconfig.yaml --fail-on-error

# Run red-team
npx promptfoo@latest redteam run
```

**Erwartung:**
- Alle Assertions müssen bestehen (path restrictions, no secrets, output contracts)
- Red-Team Tests müssen Prompt-Injection Attacks abwehren

---

## 7) Observability (optional, P1)

**Langfuse Integration (falls gewünscht):**
- Trace Agent-Runs (nicht Trading-Runtime!)
- Metrics: Latency, Token-Usage, Success-Rate
- Red-Team Attack Detection

---

## 8) Operator Checklist

**Vor Agent-Run:**
- [ ] `/pt-preflight` ausführen (Repo clean, richtiger Branch)
- [ ] `/pt-plan` für strukturiertes Planning

**Nach Agent-Run:**
- [ ] `/pt-verify` für Verification Checklist
- [ ] `/pt-eval` für promptfoo Evals
- [ ] `/pt-merge-log` für PR-Vorbereitung

**Bei HIGH-RISK Changes:**
- [ ] Explizite manuelle Review
- [ ] Erweiterte Testsuite
- [ ] Governance-Team informieren

---

## 9) Troubleshooting

**Problem: Agent schlägt High-Risk Änderungen vor**
- Lösung: Agent sollte mit "RISK: HIGH. Requires explicit operator approval." starten. Falls nicht, Rule `.cursor/rules/peak-trade-governance.mdc` prüfen.

**Problem: Agent versucht Secrets zu printen**
- Lösung: Sofort stoppen, Red-Team Eval ausführen, Issue melden.

**Problem: Worktree-Konflikt bei Task-Split**
- Lösung: `.agent-id` prüfen, Task-Matrix überprüfen, ggf. Agents neu starten.

---

## 10) References

- Cursor Multi-Agents: https://cursor.com/changelog/2-0
- Promptfoo CI/CD: https://www.promptfoo.dev/docs/integrations/ci-cd/
- Langfuse Observability: https://langfuse.com/docs/observability/get-started
- Cursor Rules Format: https://forum.cursor.com/t/cursor-rules-files-format-arent-clear/51419
- Cursor Commands: https://cursor.com/changelog/1-6
- Task-Split Pattern: https://forum.cursor.com/t/cursor-2-0-split-tasks-using-parallel-agents-automatically-in-one-chat-how-to-setup-worktree-json/140218

---

**Status: P0 Complete (2026-01-05)**  
**Next: P1 — CI Integration, Extended Eval Suite, Langfuse Tracing**
