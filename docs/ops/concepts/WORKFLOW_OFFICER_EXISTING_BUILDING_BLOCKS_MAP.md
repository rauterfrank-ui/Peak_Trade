# Workflow Officer — Existing Building Blocks Map

**Kategorien:** reuse-as-is | wrap | later | do-not-touch

---

## Reuse-as-is (direkt aufrufen)

| Baustein | Ort | Kategorie |
|----------|-----|-----------|
| Ops Doctor (Python) | `src/ops/doctor.py` | reuse-as-is |
| Ops Doctor (Shell) | `scripts/ops/ops_doctor.sh` | reuse-as-is |
| Docker Preflight (read-only) | `scripts/ops/docker_desktop_preflight_readonly.sh` | reuse-as-is |
| Docs Token Policy | `scripts/ops/validate_docs_token_policy.py` | reuse-as-is |
| Live Pilot Preflight | `scripts/ops/run_live_pilot_preflight.sh` | reuse-as-is |
| MCP Preflight | `scripts/ops/mcp_smoke_preflight.sh` | reuse-as-is |
| Live Gates Verify | `scripts/live/verify_live_gates.py` | reuse-as-is |
| Git State | `scripts/ci/validate_git_state.sh` | reuse-as-is |
| Markdown Links | `scripts/ops/check_markdown_links.py` | reuse-as-is |
| Docs Reference Targets | `scripts/ops/verify_docs_reference_targets.sh` | reuse-as-is |
| Evidence Index | `scripts/ops/validate_evidence_index.py` | reuse-as-is |

---

## Wrap (Orchestrator ruft auf, aggregiert Output)

| Baustein | Ort | Wrap-Notiz |
|----------|-----|------------|
| Doctor | `src/ops/doctor.py` | JSON-Output parsen, in Report-Schema einbetten |
| Preflight-Scripts | diverse | stdout/stderr erfassen, Exit-Code mappen |
| Stability Gate | `scripts/ci/stability_gate.py` | Optional für Profile; braucht Input-Pfade |
| Registry Alerts Gate | `scripts/ops/registry_alerts_gate.py` | Optional; Kontextabhängig |

---

## Later (v1+, nicht v0)

| Baustein | Ort | Grund |
|----------|-----|-------|
| PR Trigger Triage | `scripts/ops/pr_trigger_triage_v1.sh` | Braucht gh/CI-Kontext; v0 nur lokal |
| Docs Graph Triage | `scripts/ops/docs_graph_triage.py` | Erweiterte Docs-Analyse |
| Stash Triage | `scripts/ops/stash_triage.sh` | Git-Stash-spezifisch |
| Closeout-Scripts | diverse p*_closeout | PR/Closeout-Workflows; nicht v0-Scope |
| gh_tls_wrap / diag | `scripts&#47;ops&#47;gh_tls_*.sh` | Nur wenn gh-Checks in Profil; später |

---

## Do-not-touch (produktiv, keine Änderung)

| Baustein | Ort | Grund |
|----------|-----|-------|
| Doctor Implementierung | `src/ops/doctor.py` | P0, CODEOWNERS |
| CI Workflows | `.github/workflows/` | Keine Änderung durch Workflow Officer |
| Evidence Pack Produktion | `scripts/aiops/generate_evidence_pack.py` | Keine Vermischung |
| Paper/Shadow Runner | diverse | Kein Kontakt |
| Kill Switch / Live Safety | `src/risk_layer/`, `src/live/` | Keine Änderung |

---

## Profil → Bausteine

| Profil | Bausteine |
|--------|-----------|
| **default** | `src.ops.doctor` (run_all_checks) |
| **docs_only_pr** | `validate_docs_token_policy.py`, `check_markdown_links.py`, `verify_docs_reference_targets.sh` |
| **ops_local_env** | `src.ops.doctor`, `docker_desktop_preflight_readonly.sh` |
| **live_pilot_preflight** | `run_live_pilot_preflight.sh` (oder Sub-Checks: pull_prbi, pull_prbg, ops_status) |
