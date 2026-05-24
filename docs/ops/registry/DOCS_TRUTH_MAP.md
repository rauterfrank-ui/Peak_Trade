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

## Canonical: LevelUp v0 — additive Manifest-/IO-/CLI-Oberfläche

Kanonische **Ops-/Spec-Oberfläche** (Auffindbarkeit, Claim-Grenzen; **keine** neue Governance-/Risk-/Safety-Autorität): [`docs/ops/specs/LEVELUP_V0_CANONICAL_SURFACE.md`](../specs/LEVELUP_V0_CANONICAL_SURFACE.md).  
**Drift-Guard-Kopplung (Slice A):** Regel `levelup-v0-layer` in `config/ops/docs_truth_map.yaml` — `sensitive` → Präfix `src/levelup/`, `required_docs` → `docs/ops/specs/LEVELUP_V0_CANONICAL_SURFACE.md` (gleiches Muster wie z. B. `forward-run-manifest-helper`).

## Operator: `levelup-v0-layer`

Wenn **`src/levelup/`** (Prefix-Regel) geändert wird, muss im **selben Diff** mindestens **`docs/ops/specs/LEVELUP_V0_CANONICAL_SURFACE.md`** mitaktualisiert werden (siehe Regel `levelup-v0-layer` in `config/ops/docs_truth_map.yaml`).

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
- 2026-05-24 — `scripts/ops/scheduler_start_boundary_guard_v0.py` + `scripts/ops/paper_shadow_247_scheduler_hold_runtime_binding_v0.py` + `scripts/ops/run_paper_only_bounded_observation_adapter_v0.py` — **scheduler_hold_runtime_binding_v0 RUN_ID-scoped env bridge** (optional `PEAK_TRADE_SCHEDULER_HOLD_RUNTIME_OUTROOT` + `PEAK_TRADE_SCHEDULER_HOLD_RUNTIME_RUN_ID`; validates full OUTROOT chain + adapter approval + canonical combined command; default HOLD_NO_PAPER_RUN unchanged; reporter default unchanged; `dry_activation_readiness.ready=false` unchanged); Scheduler Boundary Hard-Block Contract §10; **code + tests**; **kein** global HOLD clear / Testnet / Live unlock.
- 2026-05-24 — `scripts/ops/report_paper_shadow_247_preflight_status.py` + `scripts/ops/paper_shadow_247_execution_prep_readiness_v0.py` — **execution_prep_readiness_v0 optional binding v0** (requires `governance_outroot_clearance_v0.valid=true` and `activation_authorization_v0.valid=true`; separate non-authorizing evidence field; default BLOCKED + conservative `hold_context_v0` unchanged; top-level auth flags unchanged; `dry_activation_readiness.ready=false` unchanged); Preflight contract § Execution prep readiness evidence; **code + tests**; **kein** Runtime-/Live-/Gate-Unlock.
- 2026-05-24 — `scripts/ops/report_paper_shadow_247_preflight_status.py` + `scripts/ops/paper_shadow_247_activation_authorization_v0.py` — **activation_authorization_v0 optional binding v0** (requires `governance_outroot_clearance_v0.valid=true`; separate non-authorizing evidence field; default BLOCKED + conservative `hold_context_v0` unchanged; top-level auth flags unchanged; `dry_activation_readiness.ready=false` unchanged); Preflight contract § Activation authorization evidence; **code + tests**; **kein** Runtime-/Live-/Gate-Unlock.
- 2026-05-24 — `scripts/ops/report_paper_shadow_247_preflight_status.py` + `scripts/ops/paper_shadow_247_governance_outroot_clearance_v0.py` — **governance_outroot_clearance_v0 optional binding v0** (paired `--durable-run-outroot` + `--expected-run-id`; separate non-authorizing evidence field; default BLOCKED + conservative `hold_context_v0` unchanged; `dry_activation_readiness.ready=false` unchanged); Preflight contract § Governance OUTROOT clearance evidence; **code + tests**; **kein** Runtime-/Live-/Gate-Unlock.
- 2026-05-24 — `docs/ops/CI_AUDIT_KNOWN_ISSUES.md` — **Cybersecurity Visibility Chain successor archive pointer v0** (Source artifacts: durable repo-static successor JSONL pointer; **not** lossless-equivalent; does **not** restore missing 20260508 JSONL; does **not** claim R-001/R-002/R-007 mapping; manifest `MANIFEST_VERIFY_RC=0`; candidate rows `162`; **non-authorizing**); **docs-only**; **kein** Runtime-/Live-/Broker-/Workflow-Unlock.
- 2026-05-23 — `docs/ops/CI_AUDIT_KNOWN_ISSUES.md` — **Cybersecurity Visibility Chain owner inventory v0** (anchor + R-001–R-007 status; R-003–R-006 retained-risk test-owner pointers; static visibility contract module index; **non-authorizing**); **docs-only**; **kein** Runtime-/Live-/Broker-/Workflow-Unlock.
- 2026-05-23 — `tests/ci/test_workflow_secrets_reference_visibility_contract_v0.py` — **Cybersecurity Visibility Chain registry crosslink tests v0** (static crosslinks to CI audit anchor + DOCS_TRUTH_MAP registry pointers + R-003–R-006 mappings; R-001/R-002/R-007 pending documented; **non-authorizing**); **static contract tests only**; **kein** Runtime-/Live-/Gate-Unlock.
- 2026-05-22 — `scripts/ops/p91_audit_snapshot_runner_v1.sh` + taxonomy §7i — **P91 post-stop wrapper hint sync v0** (non-executing hint block mirroring P101/P93; references `run_online_readiness_post_stop_pack_v0.sh`; no auto-execute wrapper/pack/P79 ARCHIVE_ROOT verify; no launchctl change); Preflight §2a cross-ref; **shell hints + static contract tests**; **kein** Runtime-/Live-/Gate-Unlock.
- 2026-05-22 — `docs/ops/runbooks/PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V0.md` — **hold_context_v0 conservative projection clarification** (`hold_context_v0` live reporter projection; archive operator records + U3 scoped exceptions traceability-only; do not clear HOLD/Preflight BLOCKED; PASS_BLOCKED_SAFE does not clear HOLD); cross-ref §2a.1 U3 + GLB-015 §6.5; **docs + static contract tests**; Preflight **BLOCKED** unverändert; **kein** Runtime-/Live-/Gate-Unlock.
- 2026-05-22 — `docs/ops/runbooks/PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V0.md` — **§2a.1 scoped preflight exception (U3 pattern) v0** (evidence-only bounded adapter execute under BLOCKED preflight; archive operator record + Stage-3 approval chain + §2a.1 hard gate; cross-ref GLB-015 §6.5; non-generalizable; no automatic 24h/72h rerun); **docs + static contract tests**; Preflight **BLOCKED** unverändert; **kein** Runtime-/Live-/Gate-Unlock.
- 2026-05-22 — `docs/ops/specs/MASTER_V2_GO_LIVE_BLOCKER_REGISTER_V0.md` — **§6.5 GLB-015 clarification** (readiness ledger/gate snapshot PASS_BLOCKED_SAFE + triple-lane evidence are review-input/completeness only; do not clear Preflight/HOLD or grant runtime); cross-ref Preflight §2a.1; **docs + static contract tests**; **kein** Runtime-/Live-/Gate-Unlock.
- 2026-05-22 — `docs/ops/runbooks/PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V0.md` — **§2a.1 Future-run primary evidence hard gate v0** (`FUTURE_RUNS_REQUIRE_DURABLE_ARCHIVE_ROOT`, `TMP_ONLY_EVIDENCE_INVALID`, manifest/closeout required; reuse `primary_evidence_retention_v0.py`); taxonomy §2 index + scheduler boundary §7c cross-ref; **docs + static contract tests**; Preflight **BLOCKED** unverändert; **kein** Runtime-/Live-/Testnet-/Scheduler-Unlock.
- 2026-05-23 — `docs/ops/runbooks/PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V0.md` — **§2a.1 mandatory durable closeout wiring v0** (`DURABLE_PRIMARY_EVIDENCE_MANDATORY_CLOSEOUT_WIRING_V0=true`; future bounded Shadow/Testnet closeout must wire `--durable-run-root` after archive verify; flag remains opt-in/default off; **non-authorizing**); **docs + static contract tests**; Preflight **BLOCKED** unverändert; **kein** Adapter-Execute-/Runtime-/Gate-Unlock.
- 2026-05-23 — `scripts/ops/review_shadow_bounded_observation_evidence_v0.py` + `review_testnet_bounded_observation_evidence_v0.py` + `primary_evidence_retention_v0.py` — **bounded review optional `--durable-run-root` v0** (default off; calls shared `validate_durable_primary_evidence_root()`; Preflight §2a anchor; **non-authorizing**); Preflight **BLOCKED** unverändert; **kein** Wrapper-/Adapter-/Scheduler-/Runtime-Unlock.
- 2026-05-23 — `tests/ops/test_run_primary_evidence_retention_hard_gate_v0.py` — **PR #3633 preflight §2a.1 mandatory wiring crosslink tests v0** (static crosslinks to mandatory closeout wiring token + DOCS_TRUTH_MAP; **non-authorizing**); **static contract tests only**; Preflight **BLOCKED** unverändert; **kein** Adapter-Execute-/Runtime-/Gate-Unlock.
- 2026-05-23 — `tests/ci/test_workflows_no_pull_request_target_contract_v0.py` — **PR #3634 checkout v5 uniform static CI contract v0** (uniform checkout v5 workflow pin + static contract tests; **non-authorizing**); **CI + tests only**; **kein** Runtime-/Live-/Gate-Unlock.
- 2026-05-23 — `tests/ops/test_run_primary_evidence_retention_hard_gate_v0.py` — **PR #3635 preflight §2a.1 bounded adapter crosslink tests v0** (static crosslinks to Shadow/Testnet adapter + review closeout; §2a.1 mandatory wiring anchor; **non-authorizing**); **static contract tests only**; Preflight **BLOCKED** unverändert; **kein** Adapter-Execute-/Runtime-/Gate-Unlock.
- 2026-05-23 — `tests/ops/test_primary_evidence_retention_invariant_contract_v0.py` — **PR #3636 primary evidence invariant mandatory wiring crosslink tests v0** (static crosslinks §2a invariant owner to mandatory closeout wiring + bounded review `--durable-run-root`; **non-authorizing**); **static contract tests only**; Preflight **BLOCKED** unverändert; **kein** Runtime-/Live-/Gate-Unlock.
- 2026-05-23 — `tests/ops/test_preflight_scoped_exception_contract_u3_v0.py` — **PR #3638 U3 scoped-exception mandatory wiring hard-gate chain crosslink tests v0** (static crosslinks U3 owner to mandatory token + hard-gate + invariant owners; **non-authorizing**); **static contract tests only**; Preflight **BLOCKED** unverändert; **kein** Runtime-/Live-/Gate-Unlock.
- 2026-05-23 — `tests/ops/test_bounded_observation_review_durable_primary_evidence_contract_v0.py` + `test_primary_evidence_retention_invariant_contract_v0.py` — **PR #3639 bounded-review and primary evidence invariant reciprocal crosslink tests v0** (bidirectional static crosslinks §2a.1 mandatory wiring chain; **non-authorizing**); **static contract tests only**; Preflight **BLOCKED** unverändert; **kein** Adapter-Execute-/Runtime-/Gate-Unlock.
- 2026-05-23 — `tests/ops/test_scheduler_completion_primary_evidence_closeout_v0.py` — **PR #3641 scheduler-completion mandatory wiring crosslink tests v0** (static crosslinks scheduler-completion closeout owner to Preflight §2a.1 mandatory token + hard-gate + invariant + bounded-review owners; **non-authorizing**); **static contract tests only**; Preflight **BLOCKED** unverändert; **kein** Adapter-Execute-/Runtime-/Gate-Unlock.
- 2026-05-23 — `tests/ops/test_primary_evidence_retention_invariant_contract_v0.py` — **PR #3642 primary evidence invariant scheduler-completion reciprocal crosslink tests v0** (bidirectional static crosslinks invariant owner ↔ scheduler-completion closeout owner; **non-authorizing**); **static contract tests only**; Preflight **BLOCKED** unverändert; **kein** Runtime-/Scheduler-Unlock.
- 2026-05-23 — `tests/ops/test_preflight_scoped_exception_contract_u3_v0.py` + `test_bounded_observation_review_durable_primary_evidence_contract_v0.py` — **PR #3643 U3 and bounded-review reciprocal crosslink tests v0** (bidirectional static crosslinks U3 scoped-exception owner ↔ bounded-review durable primary evidence owner; **non-authorizing**); **static contract tests only**; Preflight **BLOCKED** unverändert; **kein** Adapter-Execute-/Runtime-/Gate-Unlock.
- 2026-05-21 — `docs/ops/specs/SCHEDULER_BOUNDARY_HARD_BLOCK_CONTRACT_V0.md` — **Scheduler Boundary Hard-Block Contract v0** (shared `scheduler_start_boundary_guard_v0` preflight guard for `run_scheduler.py` non-dry-run and P67 CLI `main()`; P67/P72 library opt-in `scheduler_boundary_enforce` §7b; dry-run remains planning-only for canonical launcher); cross-link from taxonomy §7; **kein** Scheduler-Daemon-Start, **kein** Live/Testnet/Broker-Unlock.
- 2026-05-22 — `docs/ops/specs/RUNTIME_LANE_TAXONOMY_AUTHORITY_LEVELS_CONTRACT_V0.md` — **Runtime Lane Taxonomy + Authority Levels Contract v0** (normative lane IDs, authority levels, forbidden cross-lane promotions; Generic Evidence Registry v1 **implemented** baseline; scheduler launcher + P67 CLI hard-block markers; opt-in scheduler completion + supervisor offline pack closeout markers §7a–§7c; P79 archive manifest gate markers §7d; P101 post-stop operator hint markers §7e; post-stop pack wrapper markers §7f; P93 post-stop wrapper hint markers §7g; F5 read-only market dashboard markers §7h; readiness ledger/mirror/gate snapshot markers §10; bounded observation adapter markers §10; bounded observation review script markers §10; **autonomy stage authority crosswalk §12** stages 0–7 → max authority / AI cap / evidence owner / operator gate / forbidden promotions); **docs-only / non-authorizing**; cross-link from `PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V0.md` §3/§7 and `MASTER_V2_GO_LIVE_ROADMAP_V0.md` §3.1; **kein** Runtime-/Live-/Testnet-/Scheduler-Unlock; §2a/§2b retention owner bleibt Preflight-Contract.
- 2026-05-21 — `docs/ops/runbooks/PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V0.md` — §2a cross-reference to post-stop pack wrapper (`run_online_readiness_post_stop_pack_v0.sh`; operator-invoked; delegates to pack; optional `--p79-archive-verify`); P101/P93 hints reference wrapper; in-process auto-pack deferred; **docs-only / non-authorizing**; Preflight **BLOCKED** unverändert; **kein** Runtime-/Live-/Testnet-/Scheduler-Unlock.
- 2026-05-21 — `docs/ops/runbooks/PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V0.md` — §2a cross-reference to P101 post-stop operator hints (`p101_stop_playbook_v1.sh`; non-executing; pack + P79 `ARCHIVE_ROOT` operator-explicit); **docs-only / non-authorizing**; Preflight **BLOCKED** unverändert; **kein** Runtime-/Live-/Testnet-/Scheduler-Unlock.
- 2026-05-19 — `docs/ops/runbooks/PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V0.md` — Navigationssatz (**24h bounded Shadow dry-run candidate** documentary evidence → **[SHADOW_247_GOVERNANCE_CHARTER_V0.md](../runbooks/SHADOW_247_GOVERNANCE_CHARTER_V0.md)** *Status and scope*): **nicht-authorisierend**, Preflight **`BLOCKED`** unverändert; **docs-only / discovery**.
- 2026-05-19 — `docs/ops/runbooks/SHADOW_247_GOVERNANCE_CHARTER_V0.md` — Additiver Absatz **„24h bounded Shadow dry-run candidate — evidence semantics“**: dokumentarische `/tmp`-Evidence eines erfolgreichen **24h candidate tier**-Laufs ersetzt **Preflight BLOCKED / not_ready** nicht; **keine** Testnet-/Live-/Broker-/Order-Freigabe; Repo bleibt kanonisch; **docs-only / non-authorizing**.
- 2026-05-18 — `docs/ops/runbooks/SHADOW_247_GOVERNANCE_CHARTER_V0.md` — Shadow-247 **Governance Charter v0** (activation ladder, operator/stop/evidence **planning**; **non-authorizing**; `not_ready` / STOP_IDLE); Querverweis aus `PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V0.md` + `RUNBOOK_INDEX.md`; **kein** Live-/Testnet-/Daemon-/Run-Unlock; **kein** Ersatz für Preflight-Contract oder TOMLs.
- `docs/ops/runbooks/CANARY_LIVE_ENTRY_CRITERIA.md` → PR #3494 (Canary readiness crosslinks slice): pointer-only Verlinkung auf bestehende Readiness-/Bounded-Pilot-Runbooks; kein neuer Readiness-/Evidence-Surface, kein Live-Unlock, keine LB-APR-Abkürzung, NO-LIVE-Default unverändert.

- 2026-05-02 — `docs&#47;ops&#47;specs&#47;MASTER_V2_GO_LIVE_ROADMAP_V0.md` — Informative **`### 3.1 Autonomy stage crosswalk (informative only)`** (planning vocabulary vs §4–§10; distributed recurring verification; **kein** neuer **`24&#47;7 Paper-Test-Daemon`**); **docs-only / non-authorizing**; **keine** Live-&#47;Testnet-&#47;Execution-Freigabe; Gates &#47; KillSwitch &#47; Risk dominieren weiterhin.

- 2026-05-02 — `docs&#47;ops&#47;README.md` — Discoverability-Zeilen zu PR **#3237** (Double Play WebUI **read-only** Route-Contract ↔ Pure-Stack **Display-Map**) und PR **#3238** (Observability Readmodel **Contract-Tests**); **display/read-only** bzw. **tests-only**; **keine** Live-/Operational-Freigabe; **kein** Gate-Ersatz und **keine** Abweichung von Master V2 &#47; Risk &#47; Kill-Switch &#47; Execution-Gates.

- 2026-04-30 — `src&#47;execution&#47;paper&#47;futures_accounting.py`: **`FuturesPaperAccountingSnapshotV0`** + `build_futures_paper_accounting_snapshot_v0` (rein/offline, ohne WP1B&#47;Runner&#47;Provider); begleitend `docs&#47;ops&#47;specs&#47;MASTER_V2_FUTURES_CLASS_A_CAPABILITY_CONTRACT_V0.md` §7.3, `docs&#47;PEAK_TRADE_V1_KNOWN_LIMITATIONS.md`, `tests&#47;execution&#47;paper&#47;test_futures_accounting_snapshot_dto_v0.py`; **keine** Live-&#47;Testnet-Freigabe; **RUNTIME_NOT_WIRED**.

- 2026-04-29 — `src&#47;execution&#47;paper&#47;futures_accounting.py` (Pure-Model v0) mit begleitenden Verweisen in `docs&#47;GOVERNANCE_AND_SAFETY_OVERVIEW.md` und `docs&#47;PEAK_TRADE_V1_KNOWN_LIMITATIONS.md` — offline/deterministisch, ohne Runner/Exchange; **keine** Live-/Testnet-Freigabe, **kein** Futures-Class-A-Abschluss; erfüllt **governance-overview-canonical** / **known-limitations-canonical** Kaskade.

- 2026-04-25 — `docs&#47;GOVERNANCE_AND_SAFETY_OVERVIEW.md` — Abschnitt „Execution and risk-layer README authority boundary“ (Spiegel zu `src&#47;execution&#47;README.md` / `src&#47;risk_layer&#47;README.md`; P0-C Epoch-/Autoritätsgrenze; **keine** Live-Freigabe); paired with `governance-overview-canonical`.

- 2026-04-20 — `scripts&#47;report_live_sessions.py` — read-only `--bounded-pilot-readiness-summary` (Readiness + Operator-Preflight-Packet + Registry-Fokus; keine Autorisierung); Runbook `RUNBOOK_BOUNDED_PILOT_LIVE_ENTRY.md` §4; **keine** Live-Freigabe.

- 2026-04-20 — `scripts&#47;report_live_sessions.py` — read-only `--bounded-pilot-closeout-status-summary` (Registry-Terminalstatus im neuesten JSON pro `session_id` + Pointer; ohne Readiness-/Packet-Lauf); Runbook `RUNBOOK_BOUNDED_PILOT_LIVE_ENTRY.md` §4; **keine** Live-Freigabe.

- 2026-04-20 — `scripts&#47;report_live_sessions.py` — read-only `--bounded-pilot-operator-overview` (Readiness + Preflight-Packet + Session-Fokus + Closeout in einem Aufruf); Runbook `RUNBOOK_BOUNDED_PILOT_LIVE_ENTRY.md` §4; **keine** Live-Freigabe.

- 2026-04-20 — `scripts&#47;report_live_sessions.py` — read-only `--bounded-pilot-gate-index` (Gate-/Enablement-Index aus bestehenden Signalen + Overview-Kontext); Runbook `RUNBOOK_BOUNDED_PILOT_LIVE_ENTRY.md` §4; **keine** Live-Freigabe.

- 2026-04-20 — `scripts&#47;report_live_sessions.py` — read-only `--bounded-pilot-first-live-frontdoor` (Overview + Gate-Index + kanonische CLI-Hinweise für Subansichten); Runbook `RUNBOOK_BOUNDED_PILOT_LIVE_ENTRY.md` §4; **keine** Live-Freigabe.

- 2026-04-20 — `scripts&#47;report_live_sessions.py` — read-only `--bounded-pilot-lifecycle-consistency` (Registry-Fokus + Closeout-/Pointer-Konsistenz-Read-Model; ohne Readiness-/Packet-Lauf); Runbook `RUNBOOK_BOUNDED_PILOT_LIVE_ENTRY.md` §4; **keine** Live-Freigabe.

- 2026-04-20 — `scripts&#47;report_live_sessions.py` — read-only `--open-sessions` (Registry `status=started`, optional `mode=bounded_pilot` / `--latest-bounded-pilot-open`); Runbook `RUNBOOK_BOUNDED_PILOT_LIVE_ENTRY.md` §4; **keine** Live-Freigabe.

- 2026-04-20 — `scripts&#47;report_live_sessions.py` — read-only `--evidence-pointers` (Registry-JSON + session-scoped `out&#47;ops&#47;execution_events&#47;sessions&#47;...&#47;execution_events.jsonl`); Runbook `RUNBOOK_BOUNDED_PILOT_LIVE_ENTRY.md` §4; **keine** Live-Freigabe.

- 2026-04-20 — `docs&#47;ops&#47;runbooks&#47;RUNBOOK_BOUNDED_PILOT_LIVE_ENTRY.md` — `run_bounded_pilot_session.py --no-invoke` nutzt dasselbe Operator-Preflight-Packet wie der Invoke-Pfad (Gate-only Parität); Ist-Zustand-Tabelle / Phase A.4; **keine** Live-Freigabe.

- 2026-04-20 — `docs&#47;ops&#47;runbooks&#47;RUNBOOK_BOUNDED_PILOT_LIVE_ENTRY.md` — Phase D.3: direkter `run_execution_session.py --mode bounded_pilot` (non-dry-run) führt dasselbe Operator-Preflight-Packet nach Handoff-Env aus (Defense-in-Depth); **keine** Live-Freigabe.

- 2026-04-20 — `docs&#47;ops&#47;runbooks&#47;RUNBOOK_BOUNDED_PILOT_LIVE_ENTRY.md` — Phase B: kanonischer Preflight `check_bounded_pilot_readiness.py`; Entry-Wrapper `run_bounded_pilot_session.py` baut vor Runner-Handoff zusätzlich das read-only Operator-Preflight-Packet (`bounded_pilot_operator_preflight_packet.py`); Ist-Zustand-Tabelle / Phase D; **keine** Live-Freigabe; **keine** neue Gate-Theorie.

- 2026-04-20 — `docs&#47;ops&#47;reviews&#47;incident_stop_kill_switch_consistency_review&#47;REVIEW.md` — Companion: read-only `scripts&#47;ops&#47;snapshot_operator_stop_signals.py` (PT_* / incident_stop artifact / kill_switch JSON, Divergenz-Hinweise); **keine** Runtime-Vereinheitlichung; **keine** Live-Freigabe.

- 2026-04-20 — `docs&#47;ops&#47;specs&#47;BOUNDED_REAL_MONEY_PILOT_ENTRY_CONTRACT.md` — Verweis auf kanonischen Preflight `scripts&#47;ops&#47;check_bounded_pilot_readiness.py` (Primary docs / scripts); **read-only**; **keine** Live-Freigabe.

- 2026-04-20 — `docs&#47;ops&#47;runbooks&#47;CANARY_LIVE_ENTRY_CRITERIA.md` — Bounded-Pilot fail-closed Handoff (`PT_BOUNDED_PILOT_INVOKED_FROM_GATE`, `PT_LIVE_CONFIRM_TOKEN`), Abgrenzung `--dry-run` ohne Gate-Env, Go/No-Go-Konsistenz `TRADE_READY` vs. `dry_run`; Companion zu `src/execution/live_session.py` / `src/core/environment.py` (Drift-Regeln `execution-layer`, `core-environment`); **keine** zusätzliche Live-Freigabe.

- 2026-04-18 — `docs&#47;ops&#47;registry&#47;TRUTH_BRANCH_PROTECTION.md` auf Single-Writer-Contract präzisiert (`ensure_truth_branch_protection.py --apply` fail-closed blockiert; kanonischer Writer `scripts&#47;ops&#47;reconcile_required_checks_branch_protection.py --apply`); dieser Eintrag dokumentiert den verpflichtenden Companion-Nachzug gemäß `truth-branch-protection-canonical`.

- 2026-04-16: `docs&#47;ops&#47;specs&#47;LEVELUP_V0_CANONICAL_SURFACE.md` neu — kanonische Ops-/Spec-Oberfläche für LevelUp v0 (Manifest-/IO-/CLI; keine neue Autorität); Querverweise in `docs&#47;KNOWLEDGE_BASE_INDEX.md`, `docs&#47;ops&#47;README.md`, `docs&#47;ops&#47;RUNBOOK_INDEX.md`; Truth-Map-Abschnitt „Canonical: LevelUp v0“; zunächst ohne `docs_truth_map.yaml`-Regel; keine Runtime-/E2E-Ausweitung.

- 2026-04-16: `config&#47;ops&#47;docs_truth_map.yaml` — Regel `levelup-v0-layer` (`src&#47;levelup&#47;` → `docs&#47;ops&#47;specs&#47;LEVELUP_V0_CANONICAL_SURFACE.md`); Truth-Map-Abschnitt „Canonical: LevelUp v0“ + Operator-Stub `levelup-v0-layer` aligned; Drift-Guard wie `forward-run-manifest-helper`; keine neue Autorität.

- 2026-04-16: `docs&#47;GOVERNANCE_AND_SAFETY_OVERVIEW.md` — second-wave canonical hub anchors (PR #2664, docs-only); Truth-Map-Pflege; paired with `governance-overview-canonical`; keine Live-Freigabe.

- 2026-04-13: Top-Level-Key **`safety_state`** im Ops-Cockpit-Payload — `src&#47;ops&#47;safety_state.py` (`build_safety_state`); Projektion aus bestehenden `safety_posture_observation`, `incident_safety_observation`, `incident_state`; Contract/Operator-Summary/Coverage-Matrix angepasst; Tests `tests&#47;ops&#47;test_safety_state.py`, `tests&#47;ops&#47;test_ops_cockpit_payload_top_level_contract.py`, `tests&#47;webui&#47;test_ops_cockpit.py`; **keine** Gate-Abschwächung, **keine** Freigabe-Semantik.

- 2026-04-13: Operator-Summary-HTML — **`safety_state`** als read-only Block **Safety state (vNext projection)** in `src&#47;webui&#47;ops_cockpit.py` (`_render_operator_summary_surface`, `id=operator-summary-safety-state-projection`); Doku `OPS_COCKPIT_OPERATOR_SUMMARY_SURFACE.md`, `OPS_COCKPIT_VNEXT_REQUIRED_VIEWS_COVERAGE.md` (RV1); Test-Anker in `tests&#47;webui&#47;test_ops_cockpit.py`; **keine** neue Autorität, **keine** Freigabe-Semantik.

- 2026-04-13: Operator-Summary-HTML — **`balance_semantics_state`** als read-only Block **Balance semantics (observation)** in `src&#47;webui&#47;ops_cockpit.py` (`_render_operator_summary_surface`, `id=operator-summary-balance-semantics`; dieselben drei Felder wie Hauptseiten-Card); Doku `OPS_COCKPIT_OPERATOR_SUMMARY_SURFACE.md`, `OPS_COCKPIT_VNEXT_REQUIRED_VIEWS_COVERAGE.md` (§ Supplementary); Test-Anker in `tests&#47;webui&#47;test_ops_cockpit.py`; **keine** Exchange-/Reconciliation-Ansprüche, **keine** neue Payload-Logik.

- 2026-04-13: Operator-Summary-HTML — **`phase83_eligibility_snapshot`** als read-only Block **Phase 83 — Strategy eligibility (observation)** in `src&#47;webui&#47;ops_cockpit.py` (`_render_operator_summary_surface`, `id=operator-summary-phase83-eligibility`; kompakte Kennzahlen wie Hauptseiten-Card); Doku `OPS_COCKPIT_OPERATOR_SUMMARY_SURFACE.md`, `OPS_COCKPIT_VNEXT_REQUIRED_VIEWS_COVERAGE.md` (§ Supplementary), `OPS_COCKPIT_PAYLOAD_READ_MODEL_CONTRACT.md`; Test-Anker in `tests&#47;webui&#47;test_ops_cockpit.py`; **keine** Live-Freigabe, **keine** neue Eligibility-Logik.

- 2026-04-13: Operator-Summary-HTML — **`workflow_officer_state`** als read-only Block **Operator workflow (observation)** in `src&#47;webui&#47;ops_cockpit.py` (`_render_operator_summary_surface`, `id=operator-summary-workflow-officer`; kompakte Kennzahlen, keine Officer-Ausführung); Doku `OPS_COCKPIT_OPERATOR_SUMMARY_SURFACE.md`, `OPS_COCKPIT_VNEXT_REQUIRED_VIEWS_COVERAGE.md` (§ Supplementary), `OPS_COCKPIT_PAYLOAD_READ_MODEL_CONTRACT.md`; Test-Anker in `tests&#47;webui&#47;test_ops_cockpit.py`; **kein** Go-Signal, **kein** Ersatz für `policy_go_no_go_observation`.

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
