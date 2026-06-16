Du bist Cursor Multi-Agent Orchestrator im Peak_Trade Repo.

Git-Kontext:
- Arbeite auf main.
- Arbeitsmodus: strikt read-only.
- Keine Branch-Erstellung.
- Keine Dateiänderungen im Repo.
- Keine Commits.
- Keine Tests/Runner/Daemons starten.
- Keine Paper-Testdaten, State, Artifacts, Live/Testnet, Exchange, Provider oder Secrets berühren.

Ziel:
Erstelle eine Master-V2-kompatible Autonomy Roadmap für Peak_Trade.

Langfristiges Ziel:
Peak_Trade soll langfristig ein voll autonomer, selbst verbessernder Trading-Stack werden, der Trades automatisch setzen kann. Diese Autonomie darf aber nur staged, auditierbar, fail-closed und Master-V2-kompatibel entstehen.

Untersuche repo-weit:
- Was existiert aktuell?
- Was fehlt für 24/7 Paper?
- Was fehlt für autonomes Shadow?
- Was fehlt für Testnet?
- Was fehlt für erste begrenzte Live-Autonomie?
- Welche Gates, Owner, Evidence, Reports, Readmodels, KillSwitch-/Risk-Flächen und Operator-Entscheidungen sind dafür nötig?
- Welche bestehenden Flächen müssen wiederverwendet werden?
- Welche neuen parallelen Flächen wären verboten?
- Was ist HOLD/Approval-only?

Wichtig:
Diese Analyse ist keine Freigabe für Live/Testnet/Execution. Sie soll die technische Stufenleiter zur späteren Autonomie beschreiben.

Bindende Regeln:
1. Reuse before new.
2. Rewire before parallel rebuild.
3. Integration over duplication.
4. Keine neuen readiness/evidence/report/index/handoff surfaces ohne eindeutigen kanonischen Owner.
5. Keine parallelen Evidence-/Readiness-/Report-/Registry-/Handoff-Flächen.
6. Keine Live/Testnet-Aktion.
7. Kein Master V2 / Double Play Runtime-Umbau.
8. Kein Scope/Capital Runtime-Umbau.
9. Keine Risk/KillSwitch-Änderung.
10. Keine Execution/Live Gate-Änderung.
11. Keine PaperExecutionEngine/Futures-Wiring.
12. Keine Shadow/Paper Runner Futures-Wiring.
13. Keine Exchange-/Provider-Integration.
14. Keine Paper-Testdaten stören.
15. Kein src/execution/** Slice empfehlen ohne bewusste Scope-Entscheidung und Docs-Drift-Bundle.
16. Snapshot DTO v0 bleibt HOLD / explicit approval only.
17. Keine 24/7-Daemon-Surface erfinden, wenn sie repo-seitig nicht kanonisch existiert.

Input-Kontext, falls vorhanden:
- /tmp/peak_trade_env_master_v2_linkage_repo_wide_review_20260502T180526Z/ENV_MASTER_V2_LINKAGE_REPO_WIDE_REVIEW.md
- /tmp/peak_trade_env_master_v2_owner_decision_pack_20260502T180717Z/ENV_MASTER_V2_OWNER_DECISION_PACK.md
- /tmp/peak_trade_repo_wide_current_system_overview_20260502T165147Z/PEAK_TRADE_REPO_WIDE_CURRENT_SYSTEM_OVERVIEW.md
- /tmp/peak_trade_final_session_handoff_20260502T174613Z/FINAL_SESSION_HANDOFF.md
- /tmp/peak_trade_operator_owner_roster_working_copy_20260502T181002Z/OPERATOR_OWNER_ROSTER_WORKING_COPY.md

Aufgaben:

1. Git-State
   - Branch, HEAD, upstream, working tree.
   - Letzte relevante Commits.

2. Existing System Inventory
   Repo-weit inventarisieren:
   - Master V2 Specs
   - Double Play / Bull-Bear / State-Switch / Scope-Capital
   - Risk / KillSwitch / Stop Signals
   - Execution Gates / Confirm Token / enabled / armed / dry-run
   - PaperExecutionEngine / Paper/Shadow Runner
   - Class-A Spot/Paper scheduled probes
   - Offline Suites
   - WebUI / Readmodels / Dashboard
   - Evidence / Readiness / Registry / Truth Map / Handoff
   - Futures Accounting / Snapshot DTO / F1/F2 / Class-A Futures
   - Strategy / Learning Loop / Backtest / Walk-Forward / Stress / Christoffersen
   - Env / Vars / Secrets / Scheduled controls

3. Autonomy Stage Ladder
   Entwirf eine technische Stufenleiter:
   - Stage 0: Research / Backtest only
   - Stage 1: Shadow advisory
   - Stage 2: 24/7 Paper observation
   - Stage 3: Paper autonomous candidate loop
   - Stage 4: Testnet autonomous bounded loop
   - Stage 5: Gated Live pilot
   - Stage 6: Bounded autonomous Live
   - Stage 7: Self-improving autonomy with hard gates

   Für jede Stage:
   - Ziel
   - bestehende Repo-Flächen
   - fehlende Bausteine
   - benötigte Evidence
   - benötigte Tests
   - benötigte Ops/Runbook/Owner-Klärung
   - erlaubte Autorität
   - verbotene Autorität
   - Promotion-Kriterien
   - STOP/KillSwitch Kriterien
   - Reuse-Pfad statt neuer Surface

4. Authority Chain
   Lege dar:
   - Signal != Trade
   - Strategy != Authority
   - AI != Authority
   - Dashboard != Freigabe
   - Paper != Live
   - Testnet != Live
   - Master V2 / Double Play / Risk / KillSwitch / Execution Gates sind Kontrollkette
   - Learning Loop darf Kandidaten verbessern, aber keine Gates umgehen

5. Current State Placement
   Ordne den aktuellen Repo-Stand einer oder mehreren Stages zu.
   Sage explizit:
   - Was ist schon da?
   - Was ist nur docs/spec/tests?
   - Was ist pure/offline?
   - Was ist read-only/reporting?
   - Was ist nicht gewired?
   - Was ist nicht live/testnet?
   - Was ist approval-only?

6. Gap Register
   Erstelle Gap-Register:
   - P0 Authority/Safety blockers
   - P1 Required tests/contracts
   - P2 Docs/owner/discoverability
   - P3 ergonomics/refactor
   - HOLD/Approval-only

   Muss mindestens bewerten:
   - canonical 24/7 Paper surface fehlt/nicht bestätigt
   - Env/Owner/Vars partially assigned but canonical surface unresolved
   - Snapshot DTO v0 HOLD
   - PaperExecutionEngine/Futures wiring HOLD
   - Master V2 runtime no-touch
   - Risk/KillSwitch/Live Gates no-touch
   - Evidence/Readiness duplicate-risk
   - Strategy/Learning Loop evidence requirements

7. Best Next Moves
   Entwickle 5 bis 7 mögliche nächste Moves:
   - read-only autonomy roadmap consolidation
   - docs-only autonomy ladder in bestehender Master V2 Doc, falls Owner klar
   - tests-only Paper/Shadow non-authority contract
   - read-only 24/7 Paper owner-resolution
   - bounded pure-model Snapshot DTO v0 nur Approval-only
   - strategy/learning-loop evidence inventory
   - CI/offline-suite autonomy gate inventory

   Für jeden:
   - Nutzen
   - Risiko
   - Type
   - betroffene Dateien
   - No-Touch-Grenzen
   - Reuse Owner
   - warum jetzt / warum später

8. Recommended Best Next Step
   Gib genau eine Empfehlung.
   Die Empfehlung darf keine Implementierung ausführen.
   Bevorzuge einen Schritt, der das langfristige Autonomie-Ziel voranbringt, ohne Authority/Risk/Gate-Grenzen zu verletzen.

9. Operator Decision
   Formuliere, was der Operator entscheiden muss, bevor ein nächster Slice gestartet wird:
   - Welche Stage als nächstes?
   - Nur Roadmap/Docs?
   - Tests-only?
   - Paper/Shadow owner-resolution?
   - Approval für Snapshot DTO?
   - STOP/HOLD?

10. Exact Next Prompt If Approved
   Gib einen konkreten Prompt-Plan für den empfohlenen nächsten Schritt.
   Nicht ausführen.

Output:
Schreibe Langbericht nach:
$BASE/MASTER_V2_AUTONOMY_ROADMAP_READONLY.md

Schreibe Kurzfassung nach:
$BASE/MASTER_V2_AUTONOMY_ROADMAP_SHORT.md

Struktur Langbericht:
1. Executive Summary
2. Git State
3. Existing System Inventory
4. Autonomy Stage Ladder
5. Authority Chain
6. Current State Placement
7. Gap Register
8. Best Next Moves
9. Recommended Best Next Step
10. Operator Decision Required
11. Exact Next Prompt If Approved
12. STOP Conditions
13. Copy-Paste Handoff

Wichtig:
- Claims mit konkreten Pfaden belegen.
- Keine Implementierung.
- Keine neuen parallelen Surfaces.
- Wenn eine Doc-Ergänzung empfohlen wird, nur bestehende kanonische Master-V2/Ops-Flächen verwenden.
