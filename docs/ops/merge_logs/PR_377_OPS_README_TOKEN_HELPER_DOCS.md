# Merge Log — PR #377 — Ops README: Token Helper Dokumentation

**PR:** #377 — *docs(ops): document GitHub token helper usage* ([GitHub][1])  
**Merged:** 2025-12-27T05:35:08Z (into `main`)  
**Branch:** `docs/ops-github-token-helper`  
**Commit:** `882244a` (squash) — **Merged commit:** `8b3ffc8` ([GitHub][1])

## Summary

Ops-Dokumentation ergänzt, damit Operatoren den neuen Token-Helper schnell finden und korrekt nutzen (inkl. Token-Formate, Quellen-Priorität, Safe-Debug).

## Why

* **Reduziert Onboarding-Reibung**: Kein „Token-Drama" mehr - klare Anleitung für Operator
* **Verhindert Token-Leaks**: Explizite Guidance „niemals Token als eigene Zeile pasten"
* **Standardisiert Support-Pfad**: Zentrale Docs im Ops Hub für schnelle Troubleshooting
* **Follow-Up zu PR #376**: Dokumentiert die neue Token-Helper Funktionalität

## Changes

### Modified Files

* ✅ `docs/ops/README.md` (+26 lines)
  * Neue Sektion: **"GitHub Auth & Token Helper"**

### Documentation Content

Die neue Sektion dokumentiert:

* **Safe Debug Mode**:
  * `scripts/utils/get_github_token.sh --debug`
  * Zeigt nur Prefix + Länge, kein Token-Leak

* **Validierung**:
  * `scripts/utils/get_github_token.sh --check`
  * Exit Code 0 wenn gültiger Token gefunden

* **Script-Integration**:
  * `TOKEN="$(scripts/utils/get_github_token.sh)"`

* **Unterstützte Token-Formate**:
  * `gho_*` - GitHub CLI OAuth Token (bevorzugt)
  * `ghp_*` - Classic PAT
  * `github_pat_*` - Fine-grained PAT

* **Token-Quellen Priorität**:
  * `GITHUB_TOKEN` → `GH_TOKEN` → macOS Clipboard (`pbpaste`) → `gh auth token`

* **Empfohlenes Setup**:
  * `gh auth login --web`
  * Danach laufen Scripts ohne PAT-Erstellen/Löschen

* **Security Best Practices**:
  * Tokens niemals in Logs echo'en
  * Nicht als "eigene Zeile" ins Terminal pasten

## Verification

* **PR CI**: 14 checks passed (alle in < 2 Minuten)
  * audit ✅ (56s)
  * tests (3.9, 3.10, 3.11) ✅ (3-5s)
  * strategy-smoke ✅ (4s)
  * CI Health Gate ✅ (1m5s)
  * Policy Critic Gate ✅ (5s)
  * Lint Gate ✅ (5s)
  * Docs Diff Guard ✅ (5s)
  * All other gates ✅

* **Docs-only Change**: +26 lines / -0 lines
* **Auto-Merge**: Aktiviert und erfolgreich nach CI-Checks
* **Fast CI Run**: Docs-only → Tests überspringen meiste Code-Validierung

## Risk

**LOW.** Nur Dokumentation. Keine Laufzeit-/Codepfade geändert. Keine Breaking Changes.

## Operator How-To

### Dokumentation lesen

```bash
# Im Browser
open docs/ops/README.md
# Oder GitHub: https://github.com/rauterfrank-ui/Peak_Trade/blob/main/docs/ops/README.md

# Suche nach: "GitHub Auth & Token Helper"
```

### Quick Commands (aus der neuen Doku)

```bash
# Safe Debug (kein Token-Leak)
scripts/utils/get_github_token.sh --debug

# Validierung
scripts/utils/get_github_token.sh --check

# Token abrufen
TOKEN="$(scripts/utils/get_github_token.sh)"

# Empfohlenes Setup
gh auth login --web
```

### Shell-Aliase (optional)

```bash
alias pt_gh_token_debug='cd ~/Peak_Trade && scripts/utils/get_github_token.sh --debug'
alias pt_gh_token_check='cd ~/Peak_Trade && scripts/utils/get_github_token.sh --check'
```

## Related PRs

* **PR #376** (2025-12-27T05:29:52Z): GitHub OAuth Token Support - Code Implementation
  * Implementierte `scripts/utils/get_github_token.sh`
  * 18 Tests, 695 Zeilen neuer Code
  * Merge Log: `docs/ops/merge_logs/PR_376_GITHUB_OAUTH_TOKEN_SUPPORT.md`

## Impact

* **Operator Onboarding**: Reduziert Zeit von ~15 Min (PAT erstellen) auf ~2 Min (`gh auth login`)
* **Documentation Coverage**: Ops README jetzt vollständig für GitHub Auth Workflow
* **Support Tickets**: Erwartete Reduktion von Token-bezogenen Issues

## References

* PR #377: https://github.com/rauterfrank-ui/Peak_Trade/pull/377
* Updated Docs: `docs/ops/README.md` (Sektion: GitHub Auth & Token Helper)
* Related: PR #376 (`scripts/utils/get_github_token.sh` Implementation)
* Token Helper Docs: `scripts/utils/README_GITHUB_TOKEN.md`

---

**Documentation Update Impact:**
* ✅ Operator kann Token-Helper ohne Code-Durchsicht nutzen
* ✅ Security Best Practices sind prominent dokumentiert
* ✅ Onboarding-Zeit drastisch reduziert
* ✅ Zentrale Anlaufstelle für GitHub Auth im Ops Hub
