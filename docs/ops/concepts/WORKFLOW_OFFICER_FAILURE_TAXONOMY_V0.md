# Workflow Officer Failure Taxonomy v0

**Scope:** Workflow-Officer-Kontext nur. Getrennt von Runtime/Paper/Shadow/Evidence-Fehlern.

---

## 1. Failure Classes

| Klasse | ID | Beschreibung | Bestehender Handler |
|--------|-----|--------------|----------------------|
| **SANDBOX_PERMISSION** | `F001` | launchctl/Operation not permitted, sandboxed CI | Kein Handler; dokumentiert in `docs/analysis/p96/README.md` |
| **TLS_GITHUB** | `F002` | gh CLI TLS/Netzwerkfehler | `gh_tls_wrap.sh`, `gh_tls_diag_fix.sh`, `tls_fix_gh_orchestrator.sh` |
| **GIT_STATE** | `F003` | Dirty repo, falscher Branch, merge conflicts | `validate_git_state.sh`, Doctor `repo.git_status` |
| **DOCS_POLICY** | `F004` | Docs-Token-Policy, Reference-Targets, Links | `validate_docs_token_policy.py`, `verify_docs_reference_targets.sh` |
| **DOCKER** | `F005` | Docker nicht lauffähig, VM-Problem | `docker_desktop_preflight_readonly.sh` |
| **LIVE_GATES** | `F006` | Live-Mode-Gates (enable_live_trading, live_mode_armed, etc.) | `verify_live_gates.py`, `live_operator_status.py` |
| **EVIDENCE_STATE** | `F007` | Evidence-Index inkonsistent, Pack-Validierung fehlgeschlagen | `validate_evidence_index.py`, `validate_evidence_pack.py` |
| **REPO_DEPS** | `F008` | uv.lock fehlt, requirements drift | Doctor `deps.uv_lock`, `deps.requirements_sync` |
| **CI_FILES** | `F009` | CI-Workflows/Required-Checks inkonsistent | Doctor `ci.files`, `validate_required_checks_hygiene.py` |
| **CONFIG** | `F010` | config.toml/pyproject fehlt oder invalide | Doctor `config.files`, `config.pyproject` |

---

## 2. Trennung von anderen Taxonomien

| Domain | Workflow Officer | Nicht hier |
|--------|------------------|-------------|
| **Sandbox/Permission** | F001 (nur Klassifikation) | Keine Remediation |
| **TLS/GitHub** | F002 | Kein gh-Bypass |
| **Docs Policy** | F004 | Keine Auto-Fix von Token-Violations |
| **Docker** | F005 | Kein Docker-Start |
| **Live Gates** | F006 | Nur Read-Only-Status, keine Gate-Änderung |
| **Evidence State** | F007 | Nur Validierung, keine Evidence-Mutation |
| **Runtime/Paper/Shadow** | — | Keine Berührung |

---

## 3. Zuordnung Triage-Helfer

| Failure Class | Triage-Helfer | Ort |
|---------------|---------------|-----|
| F001 | (dokumentiert) | `docs/analysis/p96/README.md` |
| F002 | gh_tls_diag_fix | `scripts/ops/gh_tls_diag_fix.sh` |
| F003 | validate_git_state | `scripts/ci/validate_git_state.sh` |
| F004 | validate_docs_token_policy | `scripts/ops/validate_docs_token_policy.py` |
| F005 | docker_desktop_preflight_readonly | `scripts/ops/docker_desktop_preflight_readonly.sh` |
| F006 | verify_live_gates | `scripts/live/verify_live_gates.py` |
| F007 | validate_evidence_index | `scripts/ops/validate_evidence_index.py` |
| F008 | Doctor deps.* | `src/ops/doctor.py` |
| F009 | Doctor ci.files | `src/ops/doctor.py` |
| F010 | Doctor config.* | `src/ops/doctor.py` |

---

## 4. Keine Erweiterung der Code-Fehler-Taxonomie

Die bestehende `check_error_taxonomy_adoption.py` (raise Exception, except Exception) betrifft **Source-Code-Qualität**, nicht Workflow-Officer-Failures. Es gibt keine Vermischung.
