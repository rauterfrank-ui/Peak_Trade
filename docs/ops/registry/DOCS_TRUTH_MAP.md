# DOCS_TRUTH_MAP — Zweck (Slice A)

**Status:** Slice A — maschinenlesbares Mapping + lokaler Drift-Check  
**Konfiguration:** `config/ops/docs_truth_map.yaml`  
**Skript:** `scripts/ops/check_docs_drift_guard.py`

## Zweck

Einige **sensible Code- und Dokumentationspfade** (Execution, Orders, Environment, zentrale Governance-/Limitations-Docs) sollen nicht **still** von den **kanonischen Beschreibungen** im Repo abdriften.

Dieses Mapping verknüpft **Bereiche** (Triggers) mit **Canonical-Docs** (mindestens eine Datei aus der Liste muss bei einer Änderung im Bereich mitgeändert werden — im selben Diff gegenüber dem gewählten Basis-Ref, z. B. `origin&#47;main`).

## Wie das Mapping funktioniert

1. Regeln stehen in `config/ops/docs_truth_map.yaml` (`rules[]`).
2. Jede Regel hat `sensitive` (Pfade) und `required_docs` (Pfadliste).
3. Das Skript ermittelt geänderte Dateien via `git diff <base>...HEAD` und prüft pro Regel:  
   **Wenn** mindestens ein `sensitive`-Pfad geändert wurde **und** **keine** der `required_docs` geändert wurde → **Fehler** (Exit 1).

Pfad-Matching:

- Endet ein Eintrag in `sensitive` mit `/`, gelten alle Repo-relativen Pfade **unter** diesem Präfix.
- Sonst exakter Pfad.

## Was das nicht leistet

- **Kein** Beweis, dass die Doku inhaltlich korrekt ist — nur dass **bewusst** mindestens eine referenzierte Canonical-Datei mitaktualisiert wurde.
- **Keine** semantische Prüfung, kein LLM.
- **Kein** Ersatz für Review, Governance oder Operator-Urteil.

## Betrieb

```bash
python3 scripts/ops/check_docs_drift_guard.py --base origin/main
```

Vor dem ersten Lauf: `git fetch origin` sinnvoll, damit `origin&#47;main` existiert.

## Operator: `orders-layer` und Canonical-Doku (Lesson PR #2242)

Kurzablauf, wenn **`src/orders/`** (Prefix-Regel) geändert wird:

1. **Regel `orders-layer`:** Im **selben Diff** wie der Code mindestens **eine** der drei Canonical-Dateien anfassen:  
   `docs/GOVERNANCE_AND_SAFETY_OVERVIEW.md`, `docs/PEAK_TRADE_V1_KNOWN_LIMITATIONS.md`, `docs/ops/runbooks/CANARY_LIVE_ENTRY_CRITERIA.md` (siehe `config/ops/docs_truth_map.yaml`).
2. **Kaskade:** Wird **`docs/PEAK_TRADE_V1_KNOWN_LIMITATIONS.md`** geändert, greift zusätzlich **`known-limitations-canonical`** → **`docs/ops/registry/DOCS_TRUTH_MAP.md`** (diese Datei) muss im **selben Diff** einen kurzen Nachweis bekommen (z. B. eine Zeile unter „Änderungsnachweis“).
3. **Vor Push lokal:** `python3 scripts/ops/check_docs_drift_guard.py --base origin/main`; bei Docs-Änderungen sinnvoll: `bash scripts/ops/pt_docs_gates_snapshot.sh --changed`.

**Referenzfall (PR #2242, `src/orders/exchange.py`):** Als kleinster **orders-layer**-Nachzug reichte **eine** ergänzende Referenzzeile in `docs/PEAK_TRADE_V1_KNOWN_LIMITATIONS.md` (die anderen beiden Canonical-Docs wären alternativ möglich gewesen).

**Hinweis:** Der Check vergleicht `git diff <base>...HEAD` — Stub-Änderungen nur an Code ohne Canonical-Doc lösen den Gate in CI ab.

## Operator: `truth-branch-protection-canonical`

Wenn **`docs/ops/registry/TRUTH_BRANCH_PROTECTION.md`** geändert wird, muss im **selben Diff** **`docs/ops/registry/DOCS_TRUTH_MAP.md`** (diese Datei) einen kurzen Eintrag unter „Änderungsnachweis“ erhalten — damit bleibt die Registry-Landkarte mit der Branch-Protection-Referenz im Einklang (siehe Regel `truth-branch-protection-canonical` in `config/ops/docs_truth_map.yaml`).

## Änderungsnachweis (Slice A)
- 2026-04-09 — LB-EXE-001 Phase 2 updated `docs/PEAK_TRADE_V1_KNOWN_LIMITATIONS.md` to record deny-by-default guard hardening around `src/execution/networked/transport_gate_v1.py` and related networked guard tests; no live approval or outbound execution unlock implied.

- 2026-04-09 — LB-EXE-001 Phase 1 updated `docs/PEAK_TRADE_V1_KNOWN_LIMITATIONS.md` to record deny-by-default guard hardening in `src/execution/networked/entry_contract_v1.py`, `src/execution/networked/transport_gate_v1.py`, and `src/execution/networked/canary_live_gate_v1.py`; no live approval or outbound execution unlock implied.

- 2026-04-09 — LB-OPE-001 Phase 1 updated `docs/PEAK_TRADE_V1_KNOWN_LIMITATIONS.md` to record the mock-only Finish-C3 hardening in `src/execution/live/safety.py` and `src/execution/live/reconcile.py`; no live approval or execution unlock implied.

- 2026-04-09 — LB-OPE-001 Phase 2 updated `docs/PEAK_TRADE_V1_KNOWN_LIMITATIONS.md` for cancel-race reconcile reporting and non-finite qty invariants in the same Finish-C3 mock modules; no live approval implied.

- 2026-04-08 — LB-EXE-001: `transport_gate_v1.py` populates `TransportDecisionV1.canary_live_gate_v1` (audit field; still deny outbound); `PEAK_TRADE_V1_KNOWN_LIMITATIONS.md`; paired with `known-limitations-canonical`.
- 2026-04-08 — LB-EXE-001 minimal code slice: `canary_live_gate_v1.py` + `PEAK_TRADE_V1_KNOWN_LIMITATIONS.md` — explicit gate decision API; v1 denies outbound; `PT_CANARY_SCOPE_REF` is evidence pointer only; paired with `known-limitations-canonical`.
- 2026-04-09 — LB-APR-001 docs wave: `CANARY_LIVE_ENTRY_CRITERIA.md` — § Freigabe-Artefakt (LB-APR-001): externes Ticket/Owner/Risk/Sign-off-Nachweisschema; explizit kein Live-Unlock durch Repo/Docs allein; `GOVERNANCE_AND_SAFETY_OVERVIEW.md` Querverweis; paired with `canary-live-entry-canonical` + `governance-overview-canonical`.
- 2026-04-09 — GAP-004 docs-only: `docs/ops/templates/CANARY_LIVE_MANIFEST_TEMPLATE.md` added; `CANARY_LIVE_ENTRY_CRITERIA.md`, `EVIDENCE_INDEX.md`, `GOVERNANCE_AND_SAFETY_OVERVIEW.md` cross-referenced; template is not live approval; paired with governance-overview-canonical.
- 2026-04-08 — Finish-C3 reconcile/safety mock slice updated `docs/PEAK_TRADE_V1_KNOWN_LIMITATIONS.md` to clarify that `src/execution/live/reconcile.py` and `src/execution/live/safety.py` are bounded mock/testability steps and do not imply live approval or exchange enablement.
- 2026-04-08 — GAP-001 docs-only clarification touched `docs/GOVERNANCE_AND_SAFETY_OVERVIEW.md`, `docs/SAFETY_POLICY_TESTNET_AND_LIVE.md`, and `docs/ops/roadmap/FINISH_PLAN.md`; truth-map updated to record canonical alignment only, not live approval.


- 2026-04-05 — `config/ops/docs_truth_map.yaml`: Regel `truth-branch-protection-canonical` ergänzt; Operator-Abschnitt „truth-branch-protection-canonical“ in dieser Datei.
- 2026-04-04 — `docs/PEAK_TRADE_V1_KNOWN_LIMITATIONS.md`: Referenz auf `LiveOrderExecutor`-Stub in `src/orders/exchange.py` ergänzt (Abgleich orders-layer / known-limitations-canonical).
- 2026-04-04 — Abschnitt „Operator: orders-layer … (PR #2242)“ ergänzt (Playbook für Drift-Guard); Referenzfall PEAK_TRADE als minimaler Nachzug präzisiert.
