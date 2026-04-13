# DOCS_TRUTH_MAP — Zweck (Slice A)

**Status:** Slice A — maschinenlesbares Mapping + lokaler Drift-Check  
**Konfiguration:** `config/ops/docs_truth_map.yaml`  
**Skript:** `scripts/ops/check_docs_drift_guard.py`

## Zweck

Einige **sensible Code- und Dokumentationspfade** (Execution, Orders, Environment, zentrale Governance-/Limitations-Docs) sollen nicht **still** von den **kanonischen Beschreibungen** im Repo abdriften.

Dieses Mapping verknüpft **Bereiche** (Triggers) mit **Canonical-Docs** (mindestens eine Datei aus der Liste muss bei einer Änderung im Bereich mitgeändert werden — im selben Diff gegenüber dem gewählten Basis-Ref, z. B. `origin&#47;main`).

## Canonical: LB-APR-001 — externes Freigabe-Artefakt (Vorlage)

Kanonische **Arbeitsvorlage** für das **externe** Ticket/Formular (LB-APR-001): [`docs/ops/templates/LB_APR_001_EXTERNAL_APPROVAL_ARTIFACT_TEMPLATE.md`](../templates/LB_APR_001_EXTERNAL_APPROVAL_ARTIFACT_TEMPLATE.md).  
Sie strukturiert nur die **organisatorische** Freigabe-Hülle; **Repo-Merge**, Doku und diese Vorlage **begründen keinen** technischen Canary-/Live-Unlock und **keine** `live-approved`-Eigenschaft im Sinne des Runbooks.

**Sprach-Mapping (externes Feld „Account Type“):** [`docs/ops/LB_APR_001_ACCOUNT_TYPE_FIELD_MAPPING.md`](../LB_APR_001_ACCOUNT_TYPE_FIELD_MAPPING.md) — Abgrenzung zur LB-APR-„Kontotyp“-Zeile und zu internen Laufzeit-/Phasenbegriffen; **Draft-/Approval-Hilfe**; **kein** technischer Unlock; **keine** implizite Live-Freigabe.

**Sprach-Mapping (externes Feld „Strategy Version“):** [`docs/ops/LB_APR_001_STRATEGY_VERSION_FIELD_MAPPING.md`](../LB_APR_001_STRATEGY_VERSION_FIELD_MAPPING.md) — Registry-Schlüssel vs. Laufzeit-ID vs. Git/Artefakt vs. KI-/Model-Registry; **Draft-/Approval-Hilfe**; **kein** technischer Unlock; **keine** implizite Live-Freigabe.

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

- 2026-04-13: Top-Level-Key **`safety_state`** im Ops-Cockpit-Payload — `src&#47;ops&#47;safety_state.py` (`build_safety_state`); Projektion aus bestehenden `safety_posture_observation`, `incident_safety_observation`, `incident_state`; Contract/Operator-Summary/Coverage-Matrix angepasst; Tests `tests&#47;ops&#47;test_safety_state.py`, `tests&#47;ops&#47;test_ops_cockpit_payload_top_level_contract.py`, `tests&#47;webui&#47;test_ops_cockpit.py`; **keine** Gate-Abschwächung, **keine** Freigabe-Semantik.

- 2026-04-13: `docs&#47;ops&#47;specs&#47;OPS_COCKPIT_VNEXT_REQUIRED_VIEWS_COVERAGE.md` — RV7-Zeile und **Notes** ergänzt: repo-belegte Traceability für `stale_state.order` &#47; `get_live_runs_order_staleness` (`src&#47;live&#47;order_staleness_reader.py`), Test-Anker `test_stale_state_order_*` in `tests&#47;webui&#47;test_ops_cockpit.py`; Wortlaut aligned zu [`OPS_COCKPIT_OPERATOR_SUMMARY_SURFACE.md`](../specs/OPS_COCKPIT_OPERATOR_SUMMARY_SURFACE.md); Merge mit **§ Supplementary Cockpit surfaces** (Traceability für `phase83_eligibility_snapshot`, `workflow_officer_state`, `update_officer_ui`, `balance_semantics_state` **außerhalb** Required Views §1–7; Querverweise in `OPS_COCKPIT_OPERATOR_SUMMARY_SURFACE.md` und `OPS_COCKPIT_PAYLOAD_READ_MODEL_CONTRACT.md` wo zutreffend); `docs&#47;DASHBOARD_COMPLETION_MASTER_CHECKLIST.md` — Runbook **Branch 6** (docs-only Matrix + Checklisten-Sync) als erledigt markiert; **keine** Produktfreigabe; reine Doku, keine `src&#47;`-Änderung.

- 2026-04-13: `docs&#47;ops&#47;specs&#47;OPS_COCKPIT_VNEXT_REQUIRED_VIEWS_COVERAGE.md` neu — vNext Required Views §1–7 ↔ Ops Cockpit Payload &#47; Operator-Summary-Surface &#47; Test-Anker (Traceability, keine Vollständigkeits-Freigabe); `docs&#47;DASHBOARD_COMPLETION_MASTER_CHECKLIST.md` OPS-Spur auf Ist-Stand Phasen A–E + Branch-Folge 1–6; Querverweise in vNext-Spec, vNext-Plan, Phase-E-Runbook; reine Doku, keine `src&#47;`-Änderung.

- 2026-04-13: `docs&#47;ops&#47;runbooks&#47;RUNBOOK_OPS_SUITE_PHASE_E_GOVERNANCE_REVIEW.md` neu — Phase E Governance Review (Ops Cockpit Interpretation vs. Autorität, Traceability zu Payload-Contract, Operator-Summary-Surface, Truth-Map, Tests); `RUNBOOK_OPS_SUITE_DASHBOARD_VNEXT_PLAN.md`, `OPS_COCKPIT_OPERATOR_SUMMARY_SURFACE.md`, `OPS_COCKPIT_PAYLOAD_READ_MODEL_CONTRACT.md` und `OPS_SUITE_OPERATOR_STATE_REAL_SIGNAL_REVIEW.md` (Supersession-Hinweis) angepasst; keine Produkt-Autoritätsänderung.

- 2026-04-13: `docs&#47;ops&#47;specs&#47;OPS_COCKPIT_PAYLOAD_READ_MODEL_CONTRACT.md` ergänzt — kanonischer Top-Level-Read-Model-Contract für `build_ops_cockpit_payload` (Key-Ebene, observation-only; keine Live-Freigabe); Querverweis-Pflege über [`OPS_COCKPIT_OPERATOR_SUMMARY_SURFACE.md`](../specs/OPS_COCKPIT_OPERATOR_SUMMARY_SURFACE.md) und Runbook Phase B.

- 2026-04-12: `docs&#47;GOVERNANCE_AND_SAFETY_OVERVIEW.md` ergänzt um den Hinweis, dass `bounded_pilot_mode` aus `[environment]` via `get_environment_from_config` gelesen wird und im Ops Cockpit nur als Konfigurationsbeobachtung innerhalb von `system_state` zu verstehen ist, nicht als Broker-/Exchange-Garantie.
- 2026-04-10 — Solo-Betriebsmodell: `docs/GOVERNANCE_AND_SAFETY_OVERVIEW.md` — Owner-led Governance (kein unabhängiges Risk-Gate; Review-/Approval-Felder nur bei realer Erfüllung); Pointer in diesem Abschnitt.

- 2026-04-10 — LB-APR-001: `docs/ops/LB_APR_001_STRATEGY_VERSION_FIELD_MAPPING.md` ergänzt (externes „Strategy Version“ vs. `strategy_registry_key` / `active_strategy_id` / Git / Artefakt / KI-Registry; Draft-/Approval-Hilfe; kein technischer Unlock; keine Live-Freigabe impliziert); Pointer in diesem Abschnitt.

- 2026-04-10 — LB-APR-001: `docs/ops/LB_APR_001_ACCOUNT_TYPE_FIELD_MAPPING.md` ergänzt (externes „Account Type“ vs. interne Kontexte; Draft-/Approval-Hilfe; kein technischer Unlock; keine Live-Freigabe impliziert); Pointer in diesem Abschnitt.

- 2026-04-10 — PR #2477–#2479: sichtbare Dashboard-v1.2-Strings in `templates/peak_trade_dashboard/base.html` (`<title>`), `templates/peak_trade_dashboard/index.html` (Session-Explorer-Fußzeile), `templates/peak_trade_dashboard/r_and_d_experiments.html` (R&D-Hub-Unterzeile); `tests/test_r_and_d_api.py` angepasst (#2479); reine Template-/Test-Kohärenz; keine Routing-/Laufzeit-Änderung; kein technischer Unlock.

- 2026-04-10 — PR #2481–#2482: `tests/test_r_and_d_api.py` — R&D-Hub-HTML-Testklasse `TestRAndDExperimentsPageV11` → `TestRAndDExperimentsPageV12` und Klassen-Docstring (#2481); Methoden-Docstrings in `TestRAndDExperimentsPageV12` auf v1.2 (#2482); reine Test-/Naming-Hygiene; keine Produktionscode-Änderung; kein technischer Unlock.

- 2026-04-10 — PR #2484–#2486: #2484 — `templates/peak_trade_dashboard/index.html` Dev-/HTML-Kommentare auf v1.2 ausgerichtet (Ergänzung zu den sichtbaren v1.2-Strings aus #2477–#2479; keine Laufzeit- oder Routing-Änderung); #2485 — `README.md` Root-Pointer auf diese Truth-Map; #2486 — `docs/ops/README.md` Truth-Map-Pointer für Ops-Index-Discoverability; reine Template-/Docs-Discoverability; kein technischer Unlock.

- 2026-04-10 — PR #2488: `docs/CLI_CHEATSHEET.md` — Truth-Map-Pointer im Block „Neu bei Peak_Trade?“ (CLI-Discoverability); reine Docs-Änderung; kein technischer Unlock.

- 2026-04-10 — PR #2490: `docs/LIVE_OPERATIONAL_RUNBOOKS.md` — Truth-Map-Pointer im Kopfbereich nach „Live-Ops Pack“ (Runbook-Discoverability); reine Docs-Änderung; kein technischer Unlock.

- 2026-04-11 — PR #2492: `docs/GETTING_STARTED.md` — Truth-Map-Pointer nach der Intro-Liste (Onboarding-Discoverability); reine Docs-Änderung; kein technischer Unlock.

- 2026-04-09 — LB-APR-001: `DOCS_TRUTH_MAP.md` ergänzt um kanonischen Auffindbarkeits-Hinweis auf `docs/ops/templates/LB_APR_001_EXTERNAL_APPROVAL_ARTIFACT_TEMPLATE.md` (externe Freigabe-Hülle / Arbeitshilfe; kein technischer Unlock; keine Live-Freigabe impliziert).

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
