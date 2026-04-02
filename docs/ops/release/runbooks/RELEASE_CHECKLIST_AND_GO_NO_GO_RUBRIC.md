# Release checklist & Go/No-Go rubric (Finish Level C)

> **Zweck:** Ein **einziger** Review-Bogen für einen Release-Kandidaten — **Go** nur, wenn alle **kritischen** Punkte erfüllt sind.  
> **NO‑LIVE:** Dieses Dokument **aktiviert** nichts; es dient Planung, Review und **Evidence**. Live-Schritte nur nach separater Governance-Freigabe.

---

## 1. Release-Metadaten (ausfüllen)

| Feld | Wert |
|------|------|
| Release-Kandidat (Tag/Branch/PR) | |
| Datum (UTC) | |
| Owner / Reviewer | |
| Risiko-Note (kurz) | |

---

## 2. Go/No-Go-Rubric (Finish Level C — Auszug)

**Legende:** **P0** = No-Go wenn nicht erfüllt · **P1** = Go mit dokumentiertem Risiko / Follow-up

| # | Kategorie | Check (kurz) | Stufe | Go, wenn … | No-Go, wenn … |
|---|-----------|----------------|-------|------------|---------------|
| 1 | Governance / Evidence | Docs-Gates (Token Policy, Reference Targets, Diff Guard) reproduzierbar | P0 | `pt_docs_gates_snapshot.sh --changed` (o. ä.) **PASS**; Pfade nur auf existente Ziele | Gates dauerhaft rot ohne Plan |
| 2 | Safety | Safety Policy & Kill-Switch-Posture verstanden; keine „stillen“ Live-Pfade | P0 | Verweise auf aktuelle Policy-/KS-Doku; **kein** Widerspruch zu NO‑LIVE-Default | Unklare Freigabe-Grenzen oder fehlende KS-Referenz |
| 3 | Ops / Runbooks | Start/Stop, Incident, Rollback sind auffindbar (Frontdoor → Runbooks) | P1 | [Workflow Frontdoor](../../../WORKFLOW_FRONTDOOR.md) → Live-Ops-Pack verlinkt; Runbooks konsistent mit Kandidat | Kritische Runbooks fehlen oder sind veraltet |
| 4 | Observability | Status-/Health-Reports erzeugbar (Snapshot) | P1 | Report-Pfad dokumentiert (z. B. [Live Status Reports](../../../LIVE_STATUS_REPORTS.md)); kein Muss für Produktions-Betrieb **in diesem Repo-Kontext** | Keine Nachvollziehbarkeit des Zustands |
| 5 | Broker / Testnet (wenn Scope) | Paper/Testnet gemäß DoD; keine Live-Orders ohne Freigabe | P0 | Nachweis nur **paper/testnet/snapshot** wie in [Finish Plan Level C](../../roadmap/FINISH_PLAN.md#finish-level-c-level-c-v10-broker-live-ops-governed) | Live-Execution ohne explizite Freigabe / Evidence |

**Entscheidung:** ☐ **Go** · ☐ **No-Go** — Begründung (max. 5 Sätze):

---

## 3. Evidence-Vorlage (copy-paste)

```text
Release-Kandidat: <tag|branch|PR>
Datum (UTC): <ISO8601>
Go/No-Go: <Go|No-Go>

Docs gates: <PASS/FAIL + Kommando>
Safety/Kill-Switch: <kurz + Links>
Ops/Runbooks: <kurz + Links>
Observability (Snapshot): <Report-Pfad oder „n/a“>
Broker/Testnet: <PASS/FAIL + Kommando/Pfad>

Risk note: <1–3 Sätze>
```

---

## 4. Operator verify (Finish Plan PR 8)

Kurzablauf vor einem **Merge als Release-Kandidat** oder vor einem **formalen Go/No-Go-Review** (weiterhin **NO‑LIVE**-Default in diesem Repo; keine Aktivierung von Live-Trading).

1. **Docs-Gates (changed scope)** — lokal oder in CI-Äquivalent:

```bash
bash scripts/ops/pt_docs_gates_snapshot.sh --changed
```

Erwartung: alle drei Gates **PASS** (Token Policy, Reference Targets, Diff Guard).

2. **Rubric §2** — Tabelle für den Kandidaten ausfüllen; **Entscheidung** und Begründung setzen.

3. **Evidence** — Block aus **§3** in Merge-Beschreibung, Operator-Log oder kurze Notiz im Repo unterhalb von `docs/` einfügen (genauer Pfad/Artefakt vom Team festgelegt; nicht zwingend committen).

4. **Truth-Gates auf `main` (optional, wenn PR den Truth-Workflow berührt):** `python3 scripts/ops/ensure_truth_branch_protection.py --check` — siehe [`TRUTH_BRANCH_PROTECTION.md`](../../registry/TRUTH_BRANCH_PROTECTION.md).

---

## Verwandte Dokumente

- [Finish Plan (PR 8)](../../roadmap/FINISH_PLAN.md#pr-8-release-checklist-gono-go-rubric-docs-only)
- [Governance & Safety Overview](../../../GOVERNANCE_AND_SAFETY_OVERVIEW.md)
- [Safety Policy Testnet & Live](../../../SAFETY_POLICY_TESTNET_AND_LIVE.md)
- [Finish Level C — DoD (Auszug)](../../roadmap/FINISH_PLAN.md#finish-level-c-level-c-v10-broker-live-ops-governed)
