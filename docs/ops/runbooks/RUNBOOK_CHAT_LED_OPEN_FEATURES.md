# Runbook — Chat-geführte Offene-Features-/Gap-Erkennung (Peak_Trade)

> **Zweck:** Du startest **eine Chat-Session** mit klarem Ziel — der Assistent **führt** Recherche und Triage im Repo aus und liefert **Aufgaben als Arbeitspakete** zurück (kein „Kommando-Sammelsurium“ für dich).  
> **Scope:** NO-LIVE; keine Secrets; Evidence-first wenn etwas behauptet wird.

---

## 1. Wo Themen im **Repo** sichtbar sind

- Ein Thema muss **nicht** als fester String in Code oder Docs vorkommen. Wenn es **nirgends** im Repo (oder auf GitHub als Issue/PR) verankert ist, ist es **noch nicht** priorisiert — es kann später über Gap-Sessions oder neue PRs/Issues eingeordnet werden.
- **Sichtbare Anker:** `docs/ops/roadmap/CURRENT_FOCUS.md`, `docs/ops/roadmap/FINISH_PLAN.md`, offene **GitHub-Issues/PRs**, sowie konkrete Pfade unter `src/` und `docs/`. Es gibt **keine** einzelne zentrale Datei für „alles“; Themen werden **verteilt** über diese Stellen (oder bewusst neue Docs unter `docs/ops/`).

---

## 2. Was „alles implementiert“ hier **nicht** automatisch heißt

- Der **Finish Plan** und **CURRENT_FOCUS** beschreiben einen **abgeschlossenen Roadmap-Strang** (u. a. PR 6–8 + Follow-ups) — **nicht** jede historische Idee oder jeden experimentellen Branch.
- **Offene Arbeit** zeigt sich typischerweise als: `TODO`/`FIXME` im **`src/`**-Code, **absichtliche** `NotImplementedError` (Research-Stubs), **dokumentierte** Lücken („planned“, „optional“, „Phase …“), oder **fehlende Tests** für einen Pfad.

---

## 3. Kanonische Einstiege (vor jeder Gap-Session)

| Rolle | Pfad |
|--------|------|
| Wo stehen wir operativ | `docs/ops/roadmap/CURRENT_FOCUS.md` |
| Roadmap + DoD + PR-Slices | `docs/ops/roadmap/FINISH_PLAN.md` |
| Navigation Runbooks / Ops | `docs/WORKFLOW_FRONTDOOR.md` |
| Session-Bootstrap (Copy-Paste) | `docs/ops/runbooks/PEAK_TRADE_CHAT_CONTINUITY_BOOTSTRAP.md` |

---

## 4. Ablauf pro Chat-Session (Assistent-geführt)

**Du gibst:** 1–3 Sätze Ziel (z. B. „Learning Loop Lücken“, „Infostream Härten“, „Kill-Switch Adapter Follow-up“).

**Der Assistent macht (ohne dass du Shell-Wände einfügen musst):**

1. **Scope fixieren** — nur `src/` / nur `docs/ops/` / nur ein Modul; NO-LIVE beachten.  
2. **Signale sammeln** — gezielt nach `TODO`/`FIXME` im gewählten Bereich, plus Doku-Querverweise.  
3. **Klassifizieren** — *absichtlicher Stub (Research)* vs. *echte Lücke* vs. *Tech-Debt*.  
4. **Priorisieren** — Risiko, Nutzen, Abhängigkeiten, ob Tests existieren.  
5. **Lieferobjekt** — Tabelle **Backlog** + **ein** empfohlener nächster PR-/Docs-Slice + ggf. Evidence-Pfad.

**Optional (nur wenn nötig):** ein kurzer Verifikationsblock (Docs-Gates, gezielter pytest) — nicht als Standard für jede Frage.

---

## 5. Snapshot — repräsentative offene Signals (nicht vollständig)

> **Hinweis:** Das ist **kein** vollständiger Repo-Scan, sondern eine **Stichprobe** aus Code/Docs, die typische **„noch offen / später / Stub“**-Muster zeigt. Der Assistent soll sie bei einer echten Session **aktualisieren und verfeinern**.

| Kategorie | Signal (Kurz) | Beispiel-Ort / Hinweis |
|-----------|----------------|-------------------------|
| Learning / Promotion | Bridge & Emitter „TODO“, Automation optional | `docs/LEARNING_PROMOTION_LOOP_V1_ARCHITECTURE.md`, Release-Notes Learning Loop |
| Infostream / KI | Robustere Parser, Konfiguration Modell/API | `src/meta/infostream/evaluator.py` |
| Evidence / Orchestration | Migrationskette Evidence-Packs | `src/ai_orchestration/evidence_pack_schema.py` |
| Live / Safety | Platzhalter-Snapshots „wire“ | `src/live/safety.py` (Kommentar TODO wire) |
| Risk / Kill-Switch | Legacy-Adapter entfernt (Slice 3); optional weitere Doku | `TODO_KILL_SWITCH_ADAPTER_MIGRATION.md` |
| Backtest / Engine | Tracker-Integration „not yet“ (Test beschreibt Deferral) | `tests/backtest/test_engine_tracking.py` |
| Research-Stubs | Absichtlich `NotImplementedError` (Research-Phase) | u. a. `src/strategies/bouchaud/`, `src/strategies/gatheral_cont/` |
| ML / Meta-Labeling | Unvollständige Implementierung / Platzhalter | `src/research/ml/meta/meta_labeling.py` |
| Scripts | Konfig extrahieren (Symbol) | `scripts/run_backtest.py` (TODO-Kommentar) |
| Ops / Navigation | Chat-led ↔ Stufe J (geordnete Stub-Liste) verlinkt | PR #2182 — [Verwandte Dokumente](#verwandte-dokumente) · [RUNBOOK_UNIMPLEMENTED_FEATURES_ORDERED.md](./RUNBOOK_UNIMPLEMENTED_FEATURES_ORDERED.md) |

**Interpretation:** Viele Einträge sind **keine** „vergessenen Produktfeatures“, sondern **bewusste** Stufen (Research, NO-LIVE, Phase-X). Der Wert der Liste ist **Transparenz** und **Priorisierung**, nicht Schuldzuweisung.

---

## 6. Was du in den Chat schreiben kannst (kurze Vorlage)

```text
Ziel: Offene Features / Gaps im Bereich [THEMA] identifizieren und priorisieren.
Kanonisch: CURRENT_FOCUS + FINISH_PLAN + WORKFLOW_FRONTDOOR.
Bitte: Assistent-geführte Triage in src/… (und passende docs), Ergebnis als Tabelle + 1 empfohlener nächster Slice.
Constraints: NO-LIVE, keine Secrets, Evidence wenn Behauptungen über „fertig“.
```

---

## 7. Anhang — nur wenn du technisch verifizieren willst

Changed-scope Docs-Gates (nach Doc-Edits):

```bash
bash scripts/ops/pt_docs_gates_snapshot.sh --changed
```

---

## Verwandte Dokumente

- [Current focus](../roadmap/CURRENT_FOCUS.md)  
- [Finish Plan](../roadmap/FINISH_PLAN.md)  
- [Workflow Frontdoor](../../WORKFLOW_FRONTDOOR.md)  
- [Chat continuity bootstrap](./PEAK_TRADE_CHAT_CONTINUITY_BOOTSTRAP.md)
- [Unimplemented features (ordered)](./RUNBOOK_UNIMPLEMENTED_FEATURES_ORDERED.md) — u. a. **Stufe J** (Forward-Pipeline-Stub, Scripts/Demos); ergänzt diese Chat-Triage um priorisierte Repo-Anker (**kein** Ersatz für Gap-Sessions).
