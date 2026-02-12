# PeakTrade — Brenner × Level-Up Roadmap (Evidence-first) — 2026-02-11

Dieses Dokument kombiniert die **Level-Up Roadmap (Evidence-first)** mit einem **Brenner-Runbook** (burn-down / operator-first):  
**jede rote/gelbe Fähigkeit wird in einen kleinen, testbaren Contract zerlegt** und per **Evidence-Artefakten** abgeschlossen.

---

## 0) Ausgangslage (Scorecard → Fokus-Hebel)

Aus der Roadmap: Größter Rückstand ist **Backtesting + Data/Ingest + Execution** (14 Features → 13× Red).  
Ziel: **Level 3 production-grade Kernpfad**, ohne Scope-Creep.  
(Quelle: `PEAKTRADE_LEVELUP_ROADMAP_EVIDENCE_FIRST_20260211.md`)

---

## 1) Brenner-Prinzip (wie wir “Greens” schnell erzeugen)

### 1.1 Work-Unit = „Contract Slice“
Für jedes Yellow/Red Feature wird **genau eine Slice** abgearbeitet:

1) **Contract (≈10–20 Zeilen)**  
   Was wird garantiert? Was blockt? Welche Inputs/Outputs?  
2) **Tests (3–8)**  
   Beweisen den Contract, inkl. Edge Cases.  
3) **Docs (kurz, operator-tauglich)**  
   Minimaler Abschnitt + „Was tun wenn…“  
4) **Evidence Bundle (out&#47;ops)**  
   Hashes + Pointer + 1-Line-Crawler-Summary.

> Ergebnis: Ein Slice ist “Green”, sobald Tests + Contract + Evidence vorhanden sind.

### 1.2 Definition of Done (global)
- Tests grün (CI + lokale Smoke soweit möglich)
- Contract-Text vorhanden (docs oder in-code docstring)
- Evidence: `out&#47;ops&#47;<task>_*` mit `SHA256SUMS.txt` + `*.bundle.tgz` + `*_CRAWLER_SUMMARY_1LINE.txt`
- Live bleibt **default-blocked** (enabled/armed/token gating), keine Bypass-Pfade.

---

## 2) Brenner-Board (2 Sprints, high impact)

### Sprint 1 — Live-Kernpfad “Green”
Ziel: „Live ist sicher gated, execution ist korrekt, state ist reconcilebar.“

#### S1-R3: Live execution gated (kritisch)
**DoD**
- Tests:
  - ohne `enabled && armed && confirm_token` → **keine Order**
  - mit korrektem Status → Order **erlaubt**
  - Safe-Mode: nur reduce-only / no-new-orders (klar definiert)
- Contract: „Live Gating Contract“ (10–20 Zeilen)
- Evidence: slice-evidence + 1-line summary

**Artefakt-Targets (typisch)**
- `src/live/safety.py`
- `src/execution/pipeline.py`
- Tests: `tests&#47;live&#47;test_gating_contract.py` (neu)

#### S1-R4: Retries + Idempotency (kritisch)
**DoD**
- Tests:
  - transient error → retry nach policy
  - idempotency-key verhindert Doppelorder
  - fake broker simuliert timeout&#47;retry → **genau 1** Order
- Contract: „Idempotency Contract“ (key formation + guarantees)
- Evidence + 1-line summary

**Artefakt-Targets**
- `src/execution/retry_policy.py`
- `src/execution/broker/fake_broker.py`
- Tests: `tests&#47;execution&#47;test_idempotency_retry.py` (neu)

#### S1-R5: Reconciliation (kritisch)
**DoD**
- Tests:
  - drift lokal vs exchange erkannt
  - recon erzeugt repair plan (refresh/cancel/safe mode)
  - drift → neues Trading blockiert bis sauber (oder safe mode)
- Contract: „Exchange is Source of Truth“ (6–10 bullets)
- Evidence + 1-line summary

**Artefakt-Targets**
- `src/execution/reconciliation.py`
- `src/ops/recon/reconcile.py`
- Tests: `tests&#47;execution&#47;test_reconcile_drift.py` (neu)

#### S1-R1: Confirmation token (Governance-Kern)
**DoD**
- Tests:
  - token required (ohne token: block)
  - token one-time / expiry / scoped (je nach Design)
  - token wird im audit-log erfasst
- Contract: „Promotion to Live“ (Shadow→Testnet→Live inkl Token-Step)
- Evidence + 1-line summary

**Artefakt-Targets**
- `src/core/environment.py`
- `src/live/safety.py`
- `src/live/drills.py`
- Tests: `tests&#47;live&#47;test_confirm_token.py` (neu)

---

### Sprint 2 — Risk-Härtung + Data-Quality Gate (Hands-off)
Ziel: Kein Trading bei kaputten Daten + harte Verlustgrenzen.

#### S2-R2: Max Drawdown (Risk-Kern)
**DoD**
- Tests:
  - DD korrekt (peak-to-trough)
  - trigger → safe mode / stop
  - edge cases: new peaks, reset windows, no-data
- Contract: „Risk Limits: MaxDD + MaxLoss/day“
- Evidence + 1-line summary

**Artefakt-Targets**
- `src/live/risk_limits.py`
- `src/live/live_gates.py`
- `src/backtest/stats.py`
- Tests: `tests&#47;live&#47;test_maxdd_gate.py` (neu)

#### S2-DQ: Data Freshness / Gap Detection als Hard Gate (kritisch)
**DoD**
- Tests:
  - stale feed → trading block
  - gap detection → block oder degrade-mode (explizit)
- Alert + Runbook:
  - alert `stale_data`
  - runbook „Was tun bei stale_data?“ (3–6 Schritte)
- Evidence + 1-line summary

**Artefakt-Targets**
- `src/data/shadow/live_quality_checks.py`
- `src/data/feeds/live_feed.py`
- Tests: `tests&#47;data&#47;test_freshness_gap_gate.py` (neu)
- Docs: `docs&#47;ops&#47;runbooks&#47;stale_data.md` (neu/kurz)

---

---

## 2.1 Sprint 3 — Strategy “Double-Play” (Bull/Bear + Switch-Gate) + Dynamic Leverage (cap 50×)

Ziel: Regime-Switching **LONG / SHORT / FLAT** mit zwei Specialist-Modellen (bull/bear) und einem **Meta-Controller** (Switch-Gate).
Leverage wird **elegant dynamisch** (vol-/stop-basiert) bestimmt, aber durch **MAX_LEVERAGE_CAP = 50×** hart begrenzt.

> Wichtig: Das sind **keine neuen Architektur-Layer**. Es sind Bausteine im **Strategy Layer** + eine **Sizing-Policy** im **Risk Layer**.
> Execution/Governance bleiben unverändert (nur “eingeklinkt”).

### S3-S1: Signal Specialists (Bull/Bear) + Contract (kritisch, deterministisch startbar)
**DoD**
- Contract (10–20 Zeilen): “Bull/Bear Specialist Contract”
  - Inputs: FeatureFrame (strictly causal), timestamp, instrument
  - Output: `p_up` / `p_down` ∈ [0,1] + optional `confidence`
  - Determinismus: feste Seeds / versionierte Config
- Tests:
  - Output-Bounds (0..1), NaN-Handling, empty-window behavior
  - Repro: gleicher Input → identischer Output (seed/config)
- Evidence: slice-evidence + 1-line summary

**Artefakt-Targets**
- `src&#47;strategy&#47;models&#47;bull.py` (neu)
- `src&#47;strategy&#47;models&#47;bear.py` (neu)
- Tests: `tests&#47;strategy&#47;test_specialists_contract.py` (neu)

### S3-S2: Switch-Gate (Hysterese + MinHold + Cooldown + Sideways-Band) (kritisch)
**DoD**
- Contract: “Switch-Gate Contract”
  - Inputs: `p_up`, `p_down`, prior_state, counters
  - Output: `state ∈ {LONG, SHORT, FLAT}`, `desired_dir ∈ {-1,0,+1}`, `reason_codes`
  - Hysterese: separate enter/exit thresholds
  - Anti-churn: `min_hold_bars`, `cooldown_bars`, optional `confirm_n_bars`
- Tests (mind. 8):
  - LONG→SHORT nur wenn Margin/Threshold erfüllt **und** cooldown/minhold erlaubt
  - Sideways-Band: `abs(p_up - p_down) < band` → FLAT
  - No-flip on noise: Hysterese schützt gegen Ping-Pong
  - Deterministisch: gleiche Inputs + counters → gleicher State
- Evidence + 1-line summary

**Artefakt-Targets**
- `src&#47;strategy&#47;meta&#47;switch_gate.py` (neu)
- Tests: `tests&#47;strategy&#47;test_switch_gate_hysteresis.py` (neu)

### S3-R1: Risk Sizing “Elegant Leverage” (Vol-/Stop-basiert, capped bei 50×) (kritisch)
**Zielbild**
- **Kein fixes 20×**. Leverage ist ein Ergebnis von Risk-Sizing.
- Sizing nutzt (a) Risk-Budget, (b) Stop-Distanz / Volatilität, (c) Regime/Chop-Filter.
- Harte Schranken:
  - `MAX_LEVERAGE_CAP = 50.0`
  - zusätzlich: `max_notional`, `max_position_pct_equity`, `max_daily_loss`, `maxDD` (bestehende Gates)

**DoD**
- Contract: “Dynamic Leverage Sizing Contract”
  - Inputs: equity, price, stop_distance (oder realized_vol proxy), desired_dir, risk_budget
  - Output: `target_notional`, `target_leverage`, clamped to cap
  - Fail-closed: bei fehlenden Inputs → `target=0` (FLAT) oder reduce-only (explizit)
- Tests:
  - Leverage niemals > 50× (hard clamp)
  - Vol steigt → leverage sinkt (monoton)
  - Stop-Distanz kleiner → leverage sinkt oder size sinkt (je nach Formel; monotone safety)
  - After switch: optional “switch_penalty” reduziert leverage für N Bars
- Evidence + 1-line summary

**Artefakt-Targets**
- `src&#47;risk&#47;sizing&#47;dynamic_leverage.py` (neu)
- `src&#47;risk&#47;sizing&#47;__init__.py` (export)
- Tests: `tests&#47;risk&#47;test_dynamic_leverage_cap50.py` (neu)

### S3-I: Integration-Policy “double_play” (Strategy→Risk→Execution) (kritisch)
**DoD**
- End-to-end Contract:
  - Specialists → Switch-Gate → Risk Sizing → Execution intent
  - Execution bleibt **default-blocked** (enabled/armed/token) wie in Sprint 1
- Tests:
  - deterministischer positions intent (bei fixen inputs)
  - churn guard: Switch + sizing penalty reduziert “flip damage”
- Evidence + 1-line summary

**Artefakt-Targets**
- `src&#47;strategy&#47;policies&#47;double_play.py` (neu)
- Tests: `tests&#47;integration&#47;test_double_play_policy_smoke.py` (neu)
- Docs: kurzer Abschnitt `docs&#47;ops&#47;runbooks&#47;double_play.md` (neu/kurz, operator-first)

---


## 3) Brenner-Workflow pro Slice (Copy/Paste)

> Ziel: minimaler, wiederholbarer Loop wie eure P7–P18 Closeouts, aber inhaltlich.

### 3.1 Kickoff (Branch + Work-Start)
- `git checkout main && git pull --ff-only origin main`
- `git checkout -b feat/<slice-slug>`
- `out&#47;ops&#47;work_start_<ts>/WORK_START.txt` + sha256

### 3.2 Implement (Contract → Tests → Docs)
- **Contract** zuerst schreiben (10–20 Zeilen)
- Tests schreiben, die Contract klar beweisen
- Docs/Runbook ergänzen (operator-first)

### 3.3 Gate (lokal + CI)
- `python3 -m pytest -q <tests>`
- `ruff format --check ...` / `ruff check ...` (falls im PATH; sonst CI)
- `gh pr checks <PR>` ohne watch (Evidence-Snapshot)

### 3.4 Evidence Bundle (out&#47;ops only)
Mindestinhalt:
- `HEAD.txt`, `STATUS.txt`, `LOG5.txt`, `PR_VIEW.json`, `PR_CHECKS.txt`
- `LOCAL_DIFFSTAT.txt`, `LOCAL_NAME_ONLY.txt`
- `SHA256SUMS.txt`
- `*_CRAWLER_SUMMARY_1LINE.txt`
- `*.bundle.tgz` + sha256

### 3.5 Merge + Closeout
- Auto-merge aktivieren (`--auto`) oder manuell
- Post-merge closeout:
  - main sync
  - evidence + tarball + crawler line
  - branch cleanup
  - baseline „ready-for-next-work“ bestätigen

---

## 4) Acceptance Criteria (global, damit “Level 3” zählt)

### Governance/Safety
- Live gating + confirm token: tests beweisen *no order without gates*
- Audit/registry: evidence bundles reproducible, crawler lines vorhanden

### Execution correctness
- Retry policy + idempotency: *exactly-once order semantics* im Fake Broker belegbar
- Reconciliation: drift detection + repair plan + trading block/safe mode

### Strategy (Double-Play)
- Specialists (bull/bear) + Switch-Gate: deterministisch, anti-churn (Hysterese + MinHold + Cooldown) per Tests bewiesen
- Integration: policy erzeugt LONG/SHORT/FLAT intents; Sideways-Band → flat; Switch-Reason-Codes im Audit-Log

### Data quality
- Stale/gaps: *hard gate* + alert + runbook

### Risk hard caps
- MaxDD + daily loss: *hard gate* + tests + contract
- Dynamic leverage sizing: leverage **hard-capped at 50×** + monotonic safety tests (vol/stop) + fail-closed behavior

---

## 5) Reihenfolge-Empfehlung (Brenner-Priorität)

1) **S1-R3 Live gating** (Katastrophenprävention)  
2) **S1-R4 Idempotency** (Doppelorders verhindern)  
3) **S1-R5 Reconcile** (State-Vertrauen)  
4) **S1-R1 Confirm token** (Operator-Sicherheitsbarriere)  
5) **S2-DQ Freshness/Gaps** (keine Daten = kein Trading)  
6) **S2-R2 MaxDD** (harte Verlustbegrenzung)

---

## 6) Checkliste für den nächsten Schritt (ab P19)

Wenn ihr das „Skeleton-Pn“ Pattern beibehalten wollt, dann:
- P19 (oder P20) **nicht** als weiteres Skeleton, sondern als **S1-R3 Slice**: Live gating Contract + Tests.
- Danach PR, Gate, Merge, Closeout – wie gewohnt.

---

## 7) Anhang: Kurzform “Biggest Hink”
1) Execution correctness: gating + idempotency + reconciliation  
2) Data quality: stale/gaps → trading stop  
3) Risk hard caps: max loss/day + maxDD  
4) Ops evidence: wenige harte alerts + runbooks + replay/hashing coverage

---

## Attachment: Cursor MR Runbook (Missing Features / Open Points)

## Cursor Multi-Agent Runbook — Offene Features in Peak_Trade (Einstieg → Endpunkt)

**Quelle:** [docs/FEHLENDE_FEATURES_PEAK_TRADE.md](../FEHLENDE_FEATURES_PEAK_TRADE.md) (Stand 2026-02-10, letzter Repo-Abgleich 2026-02-10)  
**Runbook-Version:** 2026-02-10T12:00:00+01:00 (Europe/Berlin)  
**Ziel:** Für die **noch offenen** Punkte ein **logisches, sequentielles** Abarbeitungs-Runbook, das in **Cursor Multi-Agent Chats** (bash-only) ausführbar ist, mit klaren **Einstiegs-/Endpunkten**, Artefakt-Pfaden und Evidence.

#### Stand / Fortschritt (wird bei Abarbeitung aktualisiert)

| Block | Slug | Status | Anmerkung |
|-------|------|--------|-----------|
| A | sweep-pipeline-cli | ✅ erledigt | `scripts/run_sweep_pipeline.py` mit --run/--report/--promote, Artefakte unter `out&#47;research&#47;<sweep_id>&#47;` (2026-02-11) |
| B | heatmap-template-2x2 | ✅ erledigt | `create_standard_2x2_heatmap()` in `src/reporting/sweep_visualization.py`, 2 params × 2 metrics, Tests (2026-02-11) |
| C | vol-regime-universal-wrapper | offen | |
| D | corr-matrix-param-metric | offen | |
| E | rolling-window-stability | offen | |
| F | sweep-comparison-tool | offen | |
| G | metrics-ulcer-recovery | ✅ erledigt | Ulcer Index + Recovery Factor in `src/backtest/stats.py`, Engine + `compute_backtest_stats`, Sweep-Defaults, Tests (2026-02-11) |
| H | nightly-sweep-automation | offen | |
| I | feature-importance-wrapper | offen | |
| J | feature-engine-skeleton | offen | |

**Nächster logischer Schritt:** Block C (Vol-Regime Universal Wrapper).

---

### 0) Konventionen (wichtig für Reproduzierbarkeit)

**Arbeitsweise pro Feature-Block:**
- Neuer Branch pro Block: `feat&#47;<slug>`
- Jede MA-Session schreibt:
  - `out&#47;ops&#47;cursor_ma&#47;<slug>&#47;MANIFEST.json`
  - `out&#47;ops&#47;cursor_ma&#47;<slug>&#47;JOURNAL.ndjson`
  - `out&#47;ops&#47;cursor_ma&#47;<slug>&#47;EVIDENCE.md`
- Finaler Abschluss pro Block:
  - Tests/Lint: mindestens `ruff format --check` + relevante `pytest -q`
  - Commit mit eindeutigem Scope
  - PR optional (wenn du die Repo-Policy so fährst)

**Bash-only:** Alle Schritte unten sind als copy/paste Befehlsfolgen geschrieben.

---

### 1) Einstiegspunkt (einmal pro Arbeitssession)

```bash
set -euo pipefail

## Repo-Root (anpassen falls nötig)
cd "$(git rev-parse --show-toplevel)"

git status -sb
git fetch origin --prune
git checkout main
git pull --ff-only origin main

## Arbeitsordner für diese Session
export MA_TS="2026-02-10T12:00:00+01:00"
export MA_ROOT="out&#47;ops&#47;cursor_ma/session_${MA_TS//:/-}"
mkdir -p "$MA_ROOT"

## Snapshot
git rev-parse HEAD | tee "$MA_ROOT/HEAD.txt"
git status -sb | tee "$MA_ROOT/STATUS.txt"
```

**Endpunkt dieses Abschnitts:** `main` ist sauber und synchron; Session-Ordner mit HEAD/STATUS existiert.

---

### 2) Offene Punkte → Logische Abarbeitungsreihenfolge

Aus [docs/FEHLENDE_FEATURES_PEAK_TRADE.md](../FEHLENDE_FEATURES_PEAK_TRADE.md) sind offen (Schwerpunkte):
- Research/Strategy (5.1): Pipeline-CLI, Heatmap-Template, Vol-Regime Wrapper, Corr-Matrix, Rolling Stability, Sweep-Comparison, zusätzliche Metriken, Regime-adaptive Strategien, Nightly Sweeps, interaktive Dashboards, Feature-Importance Wrapper
- Feature-Engine/Meta-Labeling: `src/features/` Placeholder, Triple-Barrier Labels / Feature Extraction TODO
- Real-Time/Streaming, Live-Execution, Multi-Exchange, Web-Dashboard (Auth/WebSocket), Risk Auto-Liquidation, API-Doku, Skalierung, etc.
- Tech-Debt / Stubs: Kill-Switch, PagerDuty, Adapter Protocol Placeholder, R&D Strategien TODO

**Pragmatische Reihenfolge (Dependency-first):**
1. **Research Tooling Core** (unified sweep pipeline + standard heatmap template + metrics add-ons)  
2. **Strategy Wrappers** (vol-regime universal wrapper + regime-adaptive switching)  
3. **Comparisons & Robustness** (rolling stability + sweep comparison + correlation plots)  
4. **Automation** (nightly sweeps + alerts, ohne Live-Trading)  
5. **Feature-Importance Wrapper** (SHAP/Permutation: vereinheitlichen, reports)  
6. **Feature-Engine Skeleton** (`src/features/` echte Pipeline + meta-labeling TODOs)  
7. Danach: Streaming/Live/Multi-Exchange/Web-Auth (größerer Scope, separate Runbooks sinnvoll)

Die folgenden Abschnitte liefern **konkrete Cursor-MA Blöcke** für 1–6.

---

### 3) Block A — Unified Pipeline CLI (`run_sweep_pipeline.py`)

#### Einstieg
- Ziel: Ein einziges CLI, das `--run&#47;--report&#47;--promote` orchestriert und Artefakte standardisiert ablegt.
- Endzustand: CLI vorhanden + Tests/Smoke + Doku-Update.

```bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

export SLUG="sweep-pipeline-cli"
git checkout -b "feat/${SLUG}"

mkdir -p "out&#47;ops&#47;cursor_ma/${SLUG}"

## Cursor Multi-Agent: Planner → Implementer → Critic
## (Command Palette in Cursor): "Cursor: Multi Agent Orchestration"
## Input: Ziel + Constraints (bash-only, safety-first, reproducible)
```

**MA Prompt (copy/paste in Cursor MA):**
```text
[GOAL]
Implement a unified sweep pipeline CLI: scripts/run_sweep_pipeline.py (or src/cli/run_sweep_pipeline.py if that's the convention)
with subcommands or flags:
  --run (execute sweep), --report (generate plots/reports), --promote (move "best" configs into registry/presets)
Write artifacts to out&#47;research&#47;<sweep_id>&#47;...
Ensure idempotency: rerun does not corrupt outputs; new run_id each time unless explicitly provided.

[CONSTRAINTS]
- No live trading; research-only
- Must integrate with existing sweep runners + reporting modules (stats, sweep_visualization, portfolio_builder)
- Provide at least one smoke test + minimal unit tests
- Add logging + clear exit codes
- Update docs where appropriate

[OUTPUTS]
- new CLI file
- tests
- docs snippet
- evidence: paths and sample run
```

#### Lokal: Smoke + Evidence + Commit
```bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

## Lint/Test (anpassen je nach Repo-Targets)
ruff format --check src tests scripts || true
pytest -q || true

## Minimal Smoke (CLI vorhanden):
python3 scripts/run_sweep_pipeline.py --help 2>&1 | tee "out&#47;ops&#47;cursor_ma/${SLUG}/smoke_help.txt" || true

## Evidence
git diff | tee "out&#47;ops&#47;cursor_ma/${SLUG}/DIFF.patch"

## Commit
git add -A
git commit -m "research: add unified sweep pipeline CLI" || true
```

#### Endpunkt
- Branch enthält CLI + Tests/Doku.
- Evidence liegt unter `out&#47;ops&#47;cursor_ma&#47;sweep-pipeline-cli&#47;`.

---

### 4) Block B — Standard Heatmap Template (2 params × 2 metrics)

#### Einstieg
- Ziel: Generisches Template, nicht nur Drawdown; mindestens zwei Metriken (z.B. Sharpe + MaxDD) und zwei Parameter-Achsen.
- Endzustand: API in `src/reporting/sweep_visualization.py` (oder passender Ort) + Tests + example output.

```bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

export SLUG="heatmap-template-2x2"
git checkout -b "feat/${SLUG}"
mkdir -p "out&#47;ops&#47;cursor_ma/${SLUG}"
```

**MA Prompt:**
```text
[GOAL]
Add a standard heatmap template that supports:
- x_param, y_param
- metric_a, metric_b
- output: two heatmaps (metric_a and metric_b) with consistent labeling
- handles missing grid points gracefully

[CONSTRAINTS]
- Reuse existing drawdown heatmap utilities if present
- Deterministic output file names
- Add a small test that builds a tiny synthetic sweep dataframe

[OUTPUTS]
- API function + docstring
- test
- example call in research CLI or docs
```

**Lokal:**
```bash
ruff format --check src tests scripts || true
pytest -q || true
git add -A
git commit -m "reporting: add standard 2x2 heatmap template" || true
```

**Endpunkt:** 2×Heatmap Template ist verfügbar, tests grün.

**Beispiel (nach Implementierung):**
```python
from pathlib import Path
from src.reporting.sweep_visualization import create_standard_2x2_heatmap

paths = create_standard_2x2_heatmap(
    df=sweep_df,
    x_param="fast_period",
    y_param="slow_period",
    metric_a="sharpe_ratio",
    metric_b="max_drawdown",
    sweep_name="ma_sweep",
    output_dir=Path("out&#47;research/run_01/report"),
)
## -> paths["metric_a"], paths["metric_b"] (PNG-Pfade)
```

---

### 5) Block C — Vol-Regime Universal Wrapper (für alle Strategien)

#### Einstieg
- Ziel: Eine dekorator-/wrapper-basierte Lösung, die jede Strategie optional mit Regime-Filter (z.B. only trade in specific vol regimes) versieht.
- Endzustand: Wrapper im `src/strategies/` oder `src&#47;core&#47;strategy_wrappers.py` + tests.

```bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

export SLUG="vol-regime-universal-wrapper"
git checkout -b "feat/${SLUG}"
mkdir -p "out&#47;ops&#47;cursor_ma/${SLUG}"
```

**MA Prompt:**
```text
[GOAL]
Implement a universal vol-regime wrapper that can wrap any Strategy instance:
- takes regime labels series + allowed regimes
- masks signals/positions outside allowed regimes
- works in backtest and sweeps
- minimal config surface (yaml/json friendly)

[CONSTRAINTS]
- Do not break existing Strategy interface
- Add unit tests for signal masking + edge cases (NaN regimes)
- Ensure audit/logging indicates regime gating was applied

[OUTPUTS]
- wrapper module
- tests
- docs snippet in strategy docs
```

**Endpunkt:** Wrapper existiert, ist per Config nutzbar.

---

### 6) Block D — Correlation Matrix Plot (Parameter–Metrik)

#### Einstieg
- Ziel: Plot/Report, der Korrelationen zwischen Parametern (numeric) und Zielmetriken zeigt (Spearman/Pearson).
- Endzustand: Funktion + CLI hook + Test.

```bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

export SLUG="corr-matrix-param-metric"
git checkout -b "feat/${SLUG}"
mkdir -p "out&#47;ops&#47;cursor_ma/${SLUG}"
```

**MA Prompt:**
```text
[GOAL]
Add a correlation matrix report:
- inputs: sweep results dataframe with params + metrics
- computes correlation (Spearman default) between numeric params and selected metrics
- outputs: heatmap plot + csv table
- integrates into report step of unified sweep pipeline

[CONSTRAINTS]
- Deterministic ordering of columns
- Gracefully skip non-numeric params
- Unit test for correlation computation on synthetic data
```

**Endpunkt:** Report ist Bestandteil des `--report`-Steps.

---

### 7) Block E — Rolling-Window Stability (Top-Params über 6-Monats Fenster)

#### Einstieg
- Ziel: Stability-Analyse: Parameter-Rankings je Window; z.B. top-k Frequenz oder Kendall tau zwischen Fenstern.
- Endzustand: Funktion + Report + Test.

```bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

export SLUG="rolling-window-stability"
git checkout -b "feat/${SLUG}"
mkdir -p "out&#47;ops&#47;cursor_ma/${SLUG}"
```

**MA Prompt:**
```text
[GOAL]
Implement rolling-window stability analysis for sweeps:
- windows: e.g. 6 months (configurable)
- for each window: run same sweep or evaluate same param grid on that window
- compute stability metrics: top-k overlap, kendall tau, rank volatility
- output: table + plot

[CONSTRAINTS]
- Must be runnable offline; deterministic
- If full recomputation is too heavy, allow "evaluate existing trade logs" if available
- Provide at least one fast unit test and one smoke example
```

**Endpunkt:** Stability report exists and is callable via pipeline `--report`.

---

### 8) Block F — Sweep Comparison Tool

#### Einstieg
- Ziel: Zwei Sweeps vergleichen: best configs, distribution shifts, winner/loser per metric.
- Endzustand: CLI subcommand + report.

```bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

export SLUG="sweep-comparison-tool"
git checkout -b "feat/${SLUG}"
mkdir -p "out&#47;ops&#47;cursor_ma/${SLUG}"
```

**MA Prompt:**
```text
[GOAL]
Add a sweep comparison tool:
- compare two sweep runs by run_id/path
- outputs: side-by-side summary, deltas for top-N configs, histogram/ECDF for key metrics
- writes a single markdown report and plots

[CONSTRAINTS]
- pure research tooling; no live execution hooks
- deterministic output path structure
- add a unit test for summary/delta logic
```

**Endpunkt:** Comparison tool can be called from CLI.

---

### 9) Block G — Additional Metrics (Ulcer Index, Recovery Factor)

#### Einstieg
- Ziel: Ergänzung der Stats-Engine + Sweep outputs.
- Endzustand: `src/backtest/stats.py` erweitert + tests.

```bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

export SLUG="metrics-ulcer-recovery"
git checkout -b "feat/${SLUG}"
mkdir -p "out&#47;ops&#47;cursor_ma/${SLUG}"
```

**MA Prompt:**
```text
[GOAL]
Add Ulcer Index and Recovery Factor metrics:
- integrate into backtest stats and sweep reporting
- ensure they appear in CSV/JSON outputs

[CONSTRAINTS]
- definitions documented in docstring (no external links required)
- test metrics on small synthetic equity curves
```

**Endpunkt:** Metrics appear in reports and are unit-tested.

---

### 10) Block H — Nightly Sweep Automation (Cron/Scheduler + Alerts)

#### Einstieg
- Ziel: Offline/CI automation, die nightly sweeps ausführt und Ergebnisse ablegt + optional notify (stub ok).
- Endzustand: GitHub Actions workflow oder lokaler scheduler wrapper (abhängig von Policy).

```bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

export SLUG="nightly-sweep-automation"
git checkout -b "feat/${SLUG}"
mkdir -p "out&#47;ops&#47;cursor_ma/${SLUG}"
```

**MA Prompt:**
```text
[GOAL]
Add nightly sweep automation:
- a workflow (GitHub Actions) or local cron-friendly script
- runs unified sweep pipeline with a configured set
- uploads/stores artifacts
- emits a compact summary (markdown)

[CONSTRAINTS]
- no secrets required
- notifications can be stubbed (print summary); avoid PagerDuty unless already implemented
- respect existing CI gates and repo conventions
```

**Endpunkt:** automation definition exists and is documented.

---

### 11) Block I — Feature-Importance Wrapper (SHAP/Permutation)

#### Einstieg
- Ziel: „Universal“ wrapper/report, der vorhandene SHAP/Permutation-Logik standardisiert abrufbar macht.
- Endzustand: CLI `--feature-importance` + report artifacts.

```bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

export SLUG="feature-importance-wrapper"
git checkout -b "feat/${SLUG}"
mkdir -p "out&#47;ops&#47;cursor_ma/${SLUG}"
```

**MA Prompt:**
```text
[GOAL]
Implement a standard feature-importance report wrapper:
- supports permutation importance as baseline
- optional SHAP if dependency available (guarded import)
- outputs: csv table + plot + markdown summary
- integrates with research pipeline report step

[CONSTRAINTS]
- no hard dependency on heavy libs; SHAP optional
- deterministic output
- unit tests for permutation importance on synthetic model
```

**Endpunkt:** Unified feature importance report exists.

---

### 12) Block J — Feature-Engine Skeleton + Meta-Labeling TODOs (`src/features/`)

#### Einstieg
- Ziel: `src/features/` wird echte Pipeline (compute features, store feature matrix, versioned schema).
- Zudem: `compute_triple_barrier_labels` + `_extract_features` nicht mehr Placeholder.
- Endzustand: Minimal viable feature-engine that plugs into research.

```bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

export SLUG="feature-engine-skeleton"
git checkout -b "feat/${SLUG}"
mkdir -p "out&#47;ops&#47;cursor_ma/${SLUG}"
```

**MA Prompt:**
```text
[GOAL]
Turn src/features/ from placeholder into a minimal feature engine:
- feature schema/versioning (simple: dataclass + version string)
- compute feature matrix from OHLCV (returns, vol, rolling stats, regime features)
- store outputs deterministically (parquet/csv) under out&#47;features/<run_id>/
- implement compute_triple_barrier_labels (no placeholders)
- implement _extract_features with a minimal meaningful set

[CONSTRAINTS]
- do not require exotic deps; use pandas/numpy
- keep interfaces narrow; testable functions
- add unit tests for label generation and feature extraction
- no live execution hooks
```

**Endpunkt:** Placeholder removed; features + labels are real, tested, and documented.

---

### 13) Global Endpunkt (für jeden Block)

```bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

## Final sanity
git status -sb
ruff format --check src tests scripts || true
pytest -q || true

## Evidence snapshot (always)
export SLUG="<set_this>"
mkdir -p "out&#47;ops&#47;cursor_ma/${SLUG}"
git rev-parse HEAD | tee "out&#47;ops&#47;cursor_ma/${SLUG}/HEAD.txt"
git log -1 --oneline | tee "out&#47;ops&#47;cursor_ma/${SLUG}/LOG1.txt"
```

Optional PR:
```bash
## If gh works in your environment:
## gh pr create --fill
## gh pr view --web
```

---

### 14) Quick Index — Welche Blöcke sind „must-have“ vs. „nice-to-have“

**Must-have (macht den Research-Track „rund“):**
- Block A (Pipeline CLI)
- Block B (Heatmap Template)
- Block C (Vol-Regime Wrapper)
- Block D (Corr Matrix)
- Block G (Ulcer/Recovery metrics)

**Nice-to-have / Iterativ:**
- Block E/F (Stability/Comparison)
- Block H (Nightly)
- Block I (Feature-Importance Wrapper)
- Block J (Feature-Engine + Meta-Labeling)

---

### 15) Datei-Output / Crawler-Hinweis

Diese Datei ist **crawler-eindeutig** benannt und enthält im Titel die Scope-Keywords:
- `CURSOR_MA_RUNBOOK`
- `FEHLENDE_FEATURES`
- `OPEN_POINTS`
- Datum

---

### Closeout — Block G Evidence (metrics-ulcer-recovery)

**Date:** 2026-02-10

#### Evidence files
- Present: DIFF.patch, STATUS.txt, HEAD.txt, LOG1.txt
- DIFF.patch: 0 bytes (working tree clean)

#### Verify commands actually executed
- ruff format --check: **NOT executed** (ruff not in PATH; use `python3 -m ruff` on macOS)
- pytest: executed as `python3 -m pytest tests/backtest/test_stats_ulcer_recovery.py -q` → **8 passed**

#### Cross-check
- LOG1 = `5e279236 reporting: add standard 2x2 heatmap template`
- Ulcer/Recovery changes are also in commit `5e279236` (git log -S ulcer / -S recovery_factor → same commit)
- Interpretation: Branch `feat/metrics-ulcer-recovery` forked after Block-G changes already existed → no additional diff/commit on this branch.

#### New evidence artifacts
- `out&#47;ops&#47;cursor_ma&#47;metrics-ulcer-recovery&#47;EVIDENCE_SUMMARY.md`
- `out&#47;ops&#47;cursor_ma&#47;metrics-ulcer-recovery&#47;EVIDENCE_SHA256.txt` (macOS `shasum -a 256`)

#### If a dedicated Block-G commit is required
- Option A: branch from parent commit before `5e279236`, stage only Block-G files/hunks, commit.
- Option B: keep as-is (no-op branch), confirm main contains Block-G, then delete branch.

#### Portable verify helper — hash flags fix

- Problem: `portable_verify.sh` hashed every pytest arg; flags like `-q` caused hash failures.
- Fix: hash only existing file paths; ignore args starting with `-` and non-existent paths.
- Behavior:
  - If no files are passed (or only flags): prints `[hash] no files to hash (pass file paths as args; flags are ignored)` and exits 0.
  - If files are passed: hashes via `sha256sum` when available, else `shasum -a 256` per file (macOS).
- Commit: 50a2dd4a ops: make portable_verify hash only existing files (ignore flags)

Evidence: `out&#47;ops&#47;cursor_ma&#47;metrics-ulcer-recovery&#47;closeout_meta2&#47;` (STATUS.txt, LOG1.txt, DIFF_CACHED.patch, SHA256.txt)

#### Closeout — normalize_validator_report_cli (PYTHONPATH-free) green
- Fix commit: 604a53fb (scripts/aiops/normalize_validator_report.py)
- Evidence: out&#47;ops&#47;portable_verify_failures&#47;fix_normalize_validator_report_cli&#47;
