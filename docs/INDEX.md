# Peak_Trade Documentation Index

> **Zweck:** Zentraler Einstieg in die Peak_Trade-Dokumentation  
> **Stand:** 2026-04-15  
> **Status:** canonical

---

## Einstieg

| Dokument | Zweck |
|----------|-------|
| [PEAK_TRADE_OVERVIEW.md](PEAK_TRADE_OVERVIEW.md) | Architektur & Schnelleinstieg |
| [KNOWLEDGE_BASE_INDEX.md](KNOWLEDGE_BASE_INDEX.md) | Vollständiger Dokumentations-Hub |

---

## Canonical Vocabulary / Authority / Provenance v0

- Canonical Spec (verbindlich): [docs/ops/specs/CANONICAL_VOCAB_AUTHORITY_PROVENANCE_V0.md](ops/specs/CANONICAL_VOCAB_AUTHORITY_PROVENANCE_V0.md)
- Normative Kurzregel: `Governance > Safety&#47;Kill-Switch > Risk&#47;Exposure Caps`; `Switch-Gate` und `AI Orchestrator` sind Control-Orchestration/advisory, aber keine finale Execution Authority.
- Claim-Disziplin: Claims nur in den Klassen `repo-evidenced`, `documented`, `unverified`, `not-claimed` formulieren (Abschnitt 6); `unverified` und `not-claimed` nicht als verifizierte Fakten ausgeben; `operator-stated` explizit markieren; keine impliziten E2E-/Runtime-Behauptungen.
- Master-V2 Readiness (canonical pair): [Readiness Ladder](ops/specs/MASTER_V2_FIRST_LIVE_ENABLEMENT_READINESS_LADDER.md) + [Readiness Read Model v1 (read-only interpretation)](ops/specs/MASTER_V2_FIRST_LIVE_ENABLEMENT_READINESS_READ_MODEL_V1.md)
- Master-V2 Gate-Status Report Surface v1 (docs-only reporting layer): [Gate-Status Report Surface / Summary Table v1](ops/specs/MASTER_V2_FIRST_LIVE_ENABLEMENT_GATE_STATUS_REPORT_SURFACE_V1.md)
- Authority Recovery (Navigations-&#47;Konsolidierungsindex, **non-authorizing**): [AUTHORITY_RECOVERY_CONSOLIDATION_INDEX_V0.md](ops/AUTHORITY_RECOVERY_CONSOLIDATION_INDEX_V0.md) — Review- und Re-Onboarding-Navigation zu **bereits gelandeten** Authority-Boundary-Dokumenten (P0-Bereiche u. a.); **weder** Gate **noch** Signoff, **weder** Evidence-Paket **noch** Live-, First-Live-, Master-V2- oder Double-Play-Freigabe; ersetzt **nicht** die kanonischen Verträge oberhalb.
- Bounded / Acceptance Authority Frontdoor (P0-D, Navigations-&#47;Read-Model-Frontdoor, **non-authorizing**): [BOUNDED_ACCEPTANCE_AUTHORITY_FRONTDOOR_INDEX_V0.md](ops/BOUNDED_ACCEPTANCE_AUTHORITY_FRONTDOOR_INDEX_V0.md) — read-only Einstiegs- und **Inventar-**Karte zu **bounded/acceptance-** und First-Live-**nahen** Doku-**Oberflächen**; **weder** Gate **noch** Signoff, **weder** Evidence **noch** Live-, First-Live-, **bounded-live**-, Master-V2- oder Double-Play-Freigabe; **keine** zweite **Autoritäts-**Quelle; ersetzt **nicht** die maßgeblichen kanonischen Verträge und Specs oberhalb.

---

## Gruppierung

### Canonical / Current (autoritativ)
- [README](../README.md) — Projekt-Einstieg
- [PEAK_TRADE_OVERVIEW.md](PEAK_TRADE_OVERVIEW.md) — Architektur
- [KNOWLEDGE_BASE_INDEX.md](KNOWLEDGE_BASE_INDEX.md) — Hub
- [features/FEHLENDE_FEATURES_PEAK_TRADE.md](features/FEHLENDE_FEATURES_PEAK_TRADE.md) — Fehlende/geplante Features (canonical)
- [ai/CLAUDE_GUIDE.md](ai/CLAUDE_GUIDE.md) — Technische AI-Referenz
- [governance/README.md](governance/README.md) — Governance

### Operational (Runbooks, Ops)
- [ops/RUNBOOK_INDEX.md](ops/RUNBOOK_INDEX.md) — Runbook-Index (Ops-Runbooks, Workflows)
- [ops/runbooks/futures/FUTURES_TRADING_READINESS_RUNBOOK_V0.md](ops/runbooks/futures/FUTURES_TRADING_READINESS_RUNBOOK_V0.md) — Futures-/Perp-**Readiness** (Stufenplan, docs-only, non-authority)
- [ops/](ops/) — Ops-Docs, Merge-Logs
- [runbooks/](runbooks/) — Runbooks (docs&#47;runbooks&#47;; Ops-Runbooks siehe ops&#47;RUNBOOK_INDEX.md)

<!-- docs INDEX status navigation note -->
- `docs&#47;ops&#47;STATUS_MATRIX.md` — kompakte Status-Matrix und schneller Navigations-/Lookup-Einstieg.
- `docs&#47;ops&#47;STATUS_OVERVIEW_2026-02-19.md` — datierter Überblick mit narrativem Kontext und zeitgebundener Operator-Einordnung.

### Historical (Referenz)
- [audit/GOVERNANCE_DATAFLOW_REPORT.md](audit/GOVERNANCE_DATAFLOW_REPORT.md) — Historisch: Dataflow & Governance
- [audit/REPO_AUDIT_REPORT.md](audit/REPO_AUDIT_REPORT.md) — Historisch: Repo-Inventory & Feature-Matrix
- [ops/PR_*_MERGE_LOG.md](ops/) — Merge-Logs
- [ops/_archive/](ops/_archive/) — Archivierte Docs
## Cursor Rules / Agent Context

- `.cursor/rules/README.md` — lokaler Index der Cursor-Regeln im Repo
- `.cursor/rules/peak_trade_founder_operator_paper_stability_guard.mdc` — Founder/Operator-Regel für `paper_stability_guard`, read-only-inventory-first und one-topic-one-PR
