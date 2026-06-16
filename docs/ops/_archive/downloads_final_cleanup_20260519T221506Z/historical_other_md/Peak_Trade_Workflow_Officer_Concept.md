# Peak_Trade Workflow Officer – Konzept v0

## 1. Ziel

Der Workflow Officer ist eine deterministische Orchestrierungs- und Entscheidungsschicht für lokale und CI-nahe Arbeitsabläufe in Peak_Trade.

Er soll **nicht** die Sandbox, GitHub oder das Host-System „reparieren“. Stattdessen soll er:
- den aktuellen Arbeitskontext zuverlässig prüfen,
- bekannte Fehlerklassen erkennen,
- bestehende Checks/Gates/Preflights orchestrieren,
- sichere nächste Schritte und Fallbacks empfehlen,
- einen einheitlichen Audit-Trail erzeugen.

Der Workflow Officer ist damit ein **Safety-/Preflight-/Triage-Layer** über bereits vorhandenen Bausteinen.

---

## 2. Nicht-Ziele

Der Workflow Officer soll in v0 ausdrücklich **nicht**:
- Plattformrechte erweitern oder Sandbox-Restriktionen umgehen,
- GitHub-/TLS-/Netzwerkprobleme „wegzaubern",
- Live-/Paper-/Shadow-Daten mutieren,
- autonome Codeänderungen ausführen,
- finale Autorität für riskante Ausführungen übernehmen,
- bestehende Guardrails duplizieren.

Er ist ein **Koordinator**, kein Ersatz für bestehende Policies oder Gates.

---

## 3. Warum der Officer sinnvoll ist

Peak_Trade enthält bereits viele geeignete Bausteine:
- Doctor / Preflight
- Policy / Gates
- Failure Triage
- Fallback-Muster
- Evidence / Registry
- GitHub-/TLS-Helfer
- Dry-Run-/Sandbox-Muster

Aktuell sind diese Bausteine jedoch verteilt. Der Workflow Officer bündelt sie in:
- einem kanonischen Einstiegspunkt,
- einem gemeinsamen Report-Format,
- einer standardisierten Failure-Taxonomy,
- einer klaren Entscheidungslogik.

---

## 4. Bereits vorhandene Bausteine im Repo

### 4.1 Doctor / Basisdiagnose
- `src&#47;ops&#47;doctor.py`
- `scripts&#47;ops&#47;ops_doctor.sh`
- `scripts&#47;ops&#47;demo_ops_doctor.sh`
- `scripts&#47;ops&#47;test_ops_doctor_minimal.sh`
- `scripts&#47;ops&#47;generate_ops_doctor_dashboard.sh`

### 4.2 Preflight
- `scripts&#47;ops&#47;docker_desktop_preflight_readonly.sh`
- `scripts&#47;ops&#47;run_live_pilot_preflight.sh`
- `scripts&#47;ops&#47;mcp_smoke_preflight.sh`
- `scripts&#47;run_live_beta_drill.py`

### 4.3 Policy / Gates
- `scripts&#47;ops&#47;validate_docs_token_policy.py`
- `scripts&#47;ci&#47;guard_no_tracked_reports.sh`
- `scripts&#47;ci&#47;check_docs_diff_guard_section.py`
- `scripts&#47;ci&#47;docs_diff_guard.sh` <!-- pt:ref-target-ignore -->
- `scripts&#47;ci&#47;scheduled_guardrails.sh`
- `scripts&#47;ci&#47;stability_gate.py`
- `scripts&#47;ops&#47;registry_alerts_gate.py`
- `scripts&#47;execution&#47;recon_audit_gate.sh`
- `scripts&#47;live&#47;verify_live_gates.py`
- `scripts&#47;live&#47;verify_shadow_mode.py`
- Health-/Meta-Gates unter `scripts&#47;ops&#47;p71_*`, `p79_*`, `p95_*`

### 4.4 Failure Triage / Analyse
- `scripts&#47;audit&#47;check_error_taxonomy_adoption.py`
- `scripts&#47;ops&#47;analyze_failures.sh`
- `scripts&#47;ops&#47;closeout_failures_summary_and_runbook.sh`
- `scripts&#47;ops&#47;pr_trigger_triage_v1.sh`
- `scripts&#47;ops&#47;stash_triage.sh`
- `scripts&#47;ops&#47;docs_graph_triage.py`
- `scripts&#47;governance&#47;keep_review_triage.py`
- `src&#47;core&#47;resilience&#47;*`

### 4.5 Evidence / Registry / JSONL
- `scripts&#47;aiops&#47;generate_evidence_pack.py`
- `scripts&#47;aiops&#47;validate_evidence_pack.py`
- `scripts&#47;ops&#47;update_evidence_index.py` <!-- pt:ref-target-ignore -->
- `scripts&#47;ops&#47;validate_evidence_index.py`
- `scripts&#47;ops&#47;append_done_registry.py`
- `scripts&#47;wave6&#47;write_evidence_registry_hook.py`
- `src&#47;ops&#47;p39&#47;registry_cli_v1.py`

### 4.6 GitHub / TLS / Closeout
- `scripts&#47;ops&#47;gh_tls_wrap.sh` <!-- pt:ref-target-ignore -->
- `scripts&#47;ops&#47;gh_tls_diag_fix.sh`
- `scripts&#47;ops&#47;tls_fix_gh_orchestrator.sh` <!-- pt:ref-target-ignore -->
- `scripts&#47;governance&#47;safe_delete_merged_branches.sh`
- `scripts&#47;governance&#47;post_merge_closeout.sh`

### 4.7 Readiness / Status / Health
- `scripts&#47;check_live_readiness.py`
- `scripts&#47;live_operator_status.py`
- `scripts&#47;health_dashboard.py`
- `scripts&#47;telemetry_health_check.py`
- `scripts&#47;telemetry_health_snapshot.py`
- `scripts&#47;ci&#47;live_readiness_scorecard.py`
- `scripts&#47;ci&#47;shadow_testnet_readiness_scorecard.py`

---

## 5. Zielbild

Der Workflow Officer wird ein zentraler, sicherer Einstiegspunkt wie:

```bash
python3 -m src.ops.workflow_officer --profile docs_only_pr --json
```

oder:

```bash
bash scripts/ops/workflow_officer.sh --profile ops_local_env
```

Er nutzt vorhandene Prüfer und Gates als Unterbausteine und liefert:
- ein einheitliches Urteil,
- strukturierte Fehlerklassen,
- Empfehlungen,
- sichere Fallbacks,
- einen konsistenten Audit-Trail.

---

## 6. Architektur

### 6.1 Schichten

#### A. Collector Layer
Sammelt Rohinformationen aus:
- Git / Repo-Status
- vorhandenen Doctor-/Preflight-Skripten
- Health-/Readiness-Checks
- Policy-Gates
- GitHub-/TLS-Helfern
- lokalen Laufzeit-/Registry-/Evidence-Dateien

#### B. Classification Layer
Ordnet Ergebnisse einer einheitlichen Failure-Taxonomy zu.

#### C. Policy Layer
Bewertet den Kontext gegen definierte Regeln:
- docs-only
- read-only
- protected paths
- no paper/shadow mutation
- live blocked unless explicitly allowed

#### D. Advice Layer
Leitet aus Status + Policy die nächste sichere Aktion ab.

#### E. Evidence Layer
Schreibt einheitliche Reports nach `out&#47;ops&#47;workflow_officer&#47;...`.

---

## 7. Kanonische Betriebsmodi

### 7.1 `audit`
Nur lesen, prüfen, klassifizieren, reporten.

### 7.2 `preflight`
Zusätzlich workflow-spezifische Prüfgruppen bündeln.

### 7.3 `advise`
Keine Mutation, aber Empfehlung für:
- nächsten sicheren Schritt,
- passenden Fallback,
- relevante Runbooks / Scripts.

### 7.4 Später optional
- `validate`
- `enforce`
- `execute`

Diese Modi sollten **nicht** Teil von v0 sein.

---

## 8. Profile für v0

### 8.1 `docs_only_pr`
Ziel:
- Docs-Policy,
- Reference-Targets,
- Repo-Status,
- Branch-Kontext,
- sichere PR-/Closeout-Fähigkeit.

### 8.2 `ops_local_env`
Ziel:
- lokales Dev-/Ops-Setup,
- Docker-Preflight,
- gh/TLS-Verfügbarkeit,
- observability entrypoints,
- lokale Pfad-/Permission-Prüfung.

### 8.3 `live_pilot_preflight`
Ziel:
- bestehende Live-Pilot-Preflight-Bausteine bündeln,
- Gates / Readiness / Health / Status zusammenfassen,
- keine Live-Mutation.

---

## 9. Check-Gruppen

### 9.1 Repo
- Git root
- branch name
- clean/dirty status
- protected path drift
- tracked/untracked critical artifacts

### 9.2 Docs Policy
- token policy
- reference targets
- docs diff guard
- tracked reports guard

### 9.3 Local Environment
- Python / uv / config presence
- required files
- shell/runtime assumptions
- write permissions on allowed output roots

### 9.4 GitHub / Network / TLS
- `gh` executable present
- auth usable
- TLS wrapper needed
- network reachable / not reachable

### 9.5 Docker / Observability
- docker available
- compose files present
- local ports expected vs occupied
- known observability scripts present

### 9.6 Live / Risk / Health
- live readiness
- shadow/testnet readiness
- kill switch health
- telemetry health
- operator status

### 9.7 Evidence / Registry
- evidence index structure
- registry structure
- expected manifests/index files
- done tokens / report shape

---

## 10. Failure-Taxonomy v0

Jeder Check soll auf eine standardisierte Klasse abbilden.

### 10.1 Beispielklassen
- `OK`
- `WARN_LEGACY_REFERENCE`
- `WARN_OPTIONAL_MISSING`
- `SANDBOX_PERMISSION`
- `HEADLESS_UI_LIMIT`
- `NETWORK_UNAVAILABLE`
- `GH_AUTH`
- `GH_TLS`
- `REPO_DIRTY`
- `BRANCH_MISMATCH`
- `DOCS_POLICY_FAIL`
- `REFERENCE_TARGET_MISSING`
- `DOCKER_UNAVAILABLE`
- `PORT_CONFLICT`
- `LIVE_GATE_BLOCKED`
- `HEALTH_CHECK_FAIL`
- `EVIDENCE_STATE_MISMATCH`
- `UNKNOWN_FAILURE`

### 10.2 Bewertungslogik
Jeder Check liefert mindestens:
- `status`: `ok` / `warn` / `fail`
- `failure_class`
- `summary`
- `evidence`
- `recommended_action`
- `safe_fallback`

---

## 11. Report-Format

### 11.1 Ausgabeorte
Vorschlag:

```text
out/ops/workflow_officer/<ts>/report.json
out/ops/workflow_officer/<ts>/report.md
out/ops/workflow_officer/<ts>/events.jsonl
```

### 11.2 Minimales JSON-Schema

```json
{
  "profile": "docs_only_pr",
  "mode": "audit",
  "timestamp_utc": "2026-03-23T12:00:00Z",
  "repo": {
    "branch": "main",
    "clean": true
  },
  "summary": {
    "status": "warn",
    "ok": 12,
    "warn": 2,
    "fail": 0
  },
  "checks": [
    {
      "id": "repo.git_status",
      "status": "ok",
      "failure_class": "OK",
      "summary": "Working tree clean",
      "evidence": {}
    },
    {
      "id": "gh.tls",
      "status": "warn",
      "failure_class": "GH_TLS",
      "summary": "Use gh_tls_wrap.sh",
      "recommended_action": "Run scripts/ops/gh_tls_wrap.sh", <!-- pt:ref-target-ignore -->
      "safe_fallback": "Avoid direct gh mutation; prepare local patch only" <!-- pt:ref-target-ignore -->
    }
  ]
}
```

---

## 12. Entscheidungslogik

### 12.1 Grundprinzip
- read-only by default
- deny-by-default für riskante Operationen
- explizite Profile statt impliziter Heuristik
- vorhandene Guardrails behalten Priorität

### 12.2 Beispiel
Wenn `docs_only_pr` aktiv ist:
- niemals Paper-/Shadow-/Live-Daten anfassen
- niemals `out&#47;ops` mutieren, außer klar definierte Officer-Reports
- Policy-Failures blocken Empfehlung zur PR-Erstellung
- Sandbox/TLS-Probleme führen zu Fallback-Empfehlung statt zu erzwungenen Writes

---

## 13. Fallback-Modell

Der Officer soll keine „unscharfen“ Workarounds erfinden, sondern bekannte Fallbacks ausgeben.

### 13.1 Beispiele
- `GH_TLS` → `scripts&#47;ops&#47;gh_tls_wrap.sh` <!-- pt:ref-target-ignore -->
- `NETWORK_UNAVAILABLE` → nur lokale Patch-/Diff-Vorbereitung
- `HEADLESS_UI_LIMIT` → keine Browser-/open-Kommandos, stattdessen URL ausgeben
- `SANDBOX_PERMISSION` → nur read-only Analyse, kein erzwungener Write
- `DOCS_POLICY_FAIL` → konkret betroffene Tokens/Pfade + empfohlene Korrektur

---

## 14. Integration mit bestehenden Bausteinen

### 14.1 Wiederverwenden, nicht duplizieren
Der Officer soll bevorzugt Adapter um bestehende Bausteine bauen.

Beispiele:
- `src.ops.doctor` direkt einbinden
- Shell-Preflights als subprocess ausführen
- Gate-Ergebnisse als standardisierte Check-Resultate normalisieren
- JSONL-/Registry-Bausteine für Audit-Trail wiederverwenden

### 14.2 Adapter-Idee
V0 kann simpel sein:
- Python-Klasse `SubprocessCheckAdapter`
- Exit-Code + stdout/stderr → normalisierte Check-Response

---

## 15. MVP-Schnitt

### 15.1 V0 Umfang
**Ein neuer Einstieg plus drei Profile:**
- `docs_only_pr`
- `ops_local_env`
- `live_pilot_preflight`

**Mit diesen Kernbausteinen:**
- `src&#47;ops&#47;doctor.py`
- Docs-Policy / Reference-Targets
- Docker Desktop Preflight
- gh/TLS-Helfer
- `check_live_readiness.py`
- `live_operator_status.py`
- Evidence-/Registry-Grundchecks

### 15.2 V0 Ausgabe
- JSON-Report
- Markdown-Zusammenfassung
- Exit-Code

---

## 16. Empfohlene Exit-Codes

- `0` = alles ok
- `1` = warn only
- `2` = policy/gate fail
- `3` = environment/sandbox/network blocker
- `4` = unexpected internal failure

---

## 17. Sicherheitsregeln

### 17.1 Muss-Regeln
- standardmäßig read-only
- keine Mutation an Paper-/Shadow-/Evidence-Daten
- keine Änderungen an Live-Gates
- keine automatische GitHub-Mutation in v0
- keine automatische Docker-Mutation in v0
- nur definierte Officer-Reports unter `out&#47;ops&#47;workflow_officer&#47;`

### 17.2 Audit-Trail
Jede Entscheidung muss erklärbar sein:
- welcher Check lief,
- welches Ergebnis kam zurück,
- welche Failure-Klasse wurde gesetzt,
- welche Empfehlung wurde abgeleitet.

---

## 18. Spätere Ausbaustufen

### V1
- mehr Profile
- bessere Adapter
- verdichtete Scorecards
- trendfähige JSONL-Historie

### V2
- Recovery Playbook Router
- automatische Gruppierung ähnlicher Fehlerbilder
- optionales HTML-Dashboard

### V3 optional
- assistive KI-Schicht zur Erklärung/Priorisierung
- **nicht** als Autorität, sondern nur als Begründungs-/Routing-Layer

---

## 19. Klare Empfehlung

Den Officer **zuerst deterministisch** bauen.

Nicht starten mit:
- autonomer KI-Steuerung,
- Auto-Fixern,
- Systemeingriffen,
- Write-heavy Orchestrierung.

Sondern mit:
- einheitlichem Einstieg,
- klarer Failure-Taxonomy,
- wiederverwendeten Checks,
- stabilem Report-Format,
- read-only Safety-by-default.

---

## 20. Konkreter nächster Schritt

Als nächste Phase sinnvoll:

1. **Design-Spec im Repo anlegen**
   - z. B. `docs&#47;ops&#47;WORKFLOW_OFFICER_V0_SPEC.md` <!-- pt:ref-target-ignore -->

2. **Mapping-Tabelle bauen**
   - bestehender Check/Gate/Script → Officer-Check-ID

3. **JSON-Schema festlegen**
   - für `report.json`

4. **Minimalen Python-Entrypoint bauen**
   - nur `audit`
   - nur `docs_only_pr`
   - nur read-only

5. **Tests für Failure-Klassen**
   - besonders `DOCS_POLICY_FAIL`, `SANDBOX_PERMISSION`, `GH_TLS`, `REPO_DIRTY`
