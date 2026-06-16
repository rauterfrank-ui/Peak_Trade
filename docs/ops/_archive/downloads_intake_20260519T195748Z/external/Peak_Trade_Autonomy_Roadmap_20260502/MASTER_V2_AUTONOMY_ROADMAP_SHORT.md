# Master V2 Autonomy Roadmap — Kurzfassung

**Stand:** `main` @ `a81492155e28`, Working Tree clean (2026-05-02 UTC).

## Kernbefunde

1. **Master V2:** **108** Specs unter `docs&#47;` (`MASTER_V2*.md`); **22** Module `src&#47;trading&#47;master_v2&#47;`; **16** Tests `tests&#47;trading&#47;master_v2&#47;`. Double Play Pure Stack und Dashboard-Anbindung sind **implementiert**; Live-Autorisierung bleibt **fail-closed** / nicht Dashboard-vergeben.

2. **24/7 Paper:** Keine repo-bestätigte **kanonische** „24/7 Paper-Daemon“-Fläche. Wiederkehrende Aktivität läuft über **verteilte** Workflows (`offline_suites.yml`, `class-a-shadow-paper-scheduled-probe-v1.yml`, Paper-Audits, scheduled PT-Smokes), optional **`scripts&#47;ops&#47;online_readiness_daemon_v1.sh`** + `docs&#47;analysis&#47;p77&#47;README.md`.

3. **Shadow/Paper/Testnet:** Viele YAMLs unter `.github&#47;workflows&#47;` (**73** Dateien); Testnet-/Pilot-Workflows **nicht** als Live-Promotion lesen. GH `vars`/`secrets`: Namen aus YAML nachweisbar, **Owner/Werte nicht repo-provable**.

4. **HOLD:** Snapshot DTO `FuturesPaperAccountingSnapshotV0` in `src&#47;execution&#47;paper&#47;futures_accounting.py` — **pure/offline**, **RUNTIME_NOT_WIRED** bis explizite Freigabe (`MASTER_V2_FUTURES_CLASS_A_CAPABILITY_CONTRACT_V0.md` §7). WP1B↔Futures Wiring ebenfalls HOLD.

5. **Externes Owner-Roster:** Namen **Frank Rauter** gesetzt; **Canonical Surface Clarification** weiterhin **TBD** → vor Repo-Doku zur Autonomie/Verification klären.

## Authority-Kette (ein Zeiler)

Signal ≠ Trade; Strategie/KI/Dashboard ≠ Freigabe; Paper ≠ Live; Testnet ≠ Live; Risk/KillSwitch/Gates dominieren; Learning nur **Kandidaten**, keine Gate-Umgehung (`MASTER_V2_LEARNING_AI_AUTONOMY_INVENTORY_V1.md`).

## Aktuelle Stage-Einordnung (grob)

| Bereich | Einordnung |
|---------|------------|
| Stage 0–1 | Stark durch Backtest/Strategien + Shadow/Paper Evidence abgedeckt |
| Stage 2 | Technisch fragmentiert möglich; **kanonisch/operatorisch offen** |
| Stage ≥3 | Blockiert durch Wiring-/Governance-HOLD und fehlende Verification-Kanonik |

## Gap-Highlights

- **P0:** Report/Dashboard vs echte Gate-Freigabe verwechseln; Scheduled CI als Readiness-Proxy.
- **P1:** WebUI gated POST-Pfade nicht überall zwingend abgesichert (laut System Overview).
- **P2:** Owner-Roster Canonical-Surface-Zeilen offen.
- **HOLD:** Master-V2-Runtime-, Risk-, KillSwitch-, Live-Gate-, Futures-Wiring-, Snapshot-Promotion ohne Approval **nicht**.

## Empfohlener nächster Schritt (einer)

Operator **schließt** die **Canonical Surface Clarification** im externen Roster und grenzt operative Planung auf **Stage ≤ 2** ein (**ohne** neue Daemon-Oberfläche zu definieren). **Keine** Repo-Mutation bis explizites STOP-Lifting; danach optional **ein** docs-only Crosswalk-Abschnitt in `docs&#47;ops&#47;specs&#47;MASTER_V2_GO_LIVE_ROADMAP_V0.md`.

## Operator muss entscheiden

Ziel-Stufe (kurzfristig ≤2 empfohlen), Repo-docs ja/nein nach Klärung, Tests-only nur bei nachgewiesener Lücke, Snapshot-DTO-Wiring ja/nein (Default **nein**), weiter **STOP/HOLD** für Implementierung bis Freigabe.

## Langversion & Prompt

Vollständige Stufenleiter, Gap-Register und Copy-Paste-Handoff: **`MASTER_V2_AUTONOMY_ROADMAP_READONLY.md`** im gleichen Verzeichnis wie diese Datei.

Orchestrierungs-Prompt-Vorlage: **`CURSOR_MASTER_V2_AUTONOMY_ROADMAP_READONLY_PROMPT.md`**.
