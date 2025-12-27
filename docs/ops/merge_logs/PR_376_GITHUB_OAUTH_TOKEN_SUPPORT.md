# Merge Log — PR #376 — GitHub OAuth Token Support (Token Helper)

**PR:** #376 — *fix(ops): accept gh OAuth tokens in clipboard token check* ([GitHub][1])  
**Merged:** 2025-12-27T05:29:52Z (into `main`)  
**Branch:** `feat/github-oauth-token-support`  
**Commit:** `bde5639` (squash) — **Merged commit:** `ca281d5` ([GitHub][1])

## Summary

Zentrales Utility für GitHub-Token-Abruf/Validierung eingeführt, das neben PATs nun auch **GitHub CLI OAuth Tokens (`gho_*`)** akzeptiert. Damit entfällt das PAT-Erstellen/Löschen im Operator-Workflow.

## Why

* **Operator-UX**: Kein PAT-Zwang mehr, wenn `gh auth` bereits eingerichtet ist
* **Security**: Token-Werte erscheinen nicht in Logs/Terminal (Debug zeigt nur Prefix + Länge)
* **Robustheit**: Multi-Source Token-Retrieval (Env → Clipboard → gh CLI)

## Changes

### New Files (695 lines)

* ✅ `scripts/utils/get_github_token.sh` (281 lines) - Token Retrieval & Validierung
* ✅ `scripts/utils/test_get_github_token.sh` (198 lines) - Test-Suite mit 18 Tests
* ✅ `scripts/utils/README_GITHUB_TOKEN.md` (216 lines) - Dokumentation & Beispiele

### Features

* **Multi-Source Token Retrieval** (Priorität):
  1. `GITHUB_TOKEN` Environment Variable
  2. `GH_TOKEN` Environment Variable
  3. macOS Clipboard (`pbpaste`)
  4. GitHub CLI (`gh auth token`)

* **Token Format Support**:
  * `gho_*` - OAuth Token (GitHub CLI) **← NEU**
  * `ghp_*` - Classic PAT
  * `github_pat_*` - Fine-grained PAT

* **Security Features**:
  * Token-Werte werden NIEMALS geloggt
  * Debug-Modus zeigt nur Prefix (4 chars) + Länge
  * Automatisches Whitespace/Newline-Trimming

## Verification

* **PR CI**: 14 checks passed ([GitHub][1])
  * audit ✅ (1m4s)
  * tests (3.9, 3.10, 3.11) ✅ (2m54s, 3m0s, 5m6s)
  * strategy-smoke ✅ (1m7s)
  * CI Health Gate ✅ (1m8s)
  * Policy Critic Gate ✅
  * Lint Gate ✅
  * Docs Diff Guard ✅
  * All other gates ✅

* **Test-Suite**: 18/18 Tests passed
  * Gültige Token-Formate (5 Tests)
  * Ungültige Token-Formate (7 Tests)
  * Whitespace-Handling (3 Tests)
  * Security (3 Tests - kein Token-Leak)

* **Live Verification**: OAuth Token (`gho_*`) erfolgreich von gh CLI abgerufen

## Risk

**LOW.** Neue Funktionalität ist in `scripts/utils/` gekapselt; keine Live-Execution / Trading-Logik betroffen. Pure Utility-Funktion ohne Breaking Changes.

## Operator How-To

### Setup (einmalig)

```bash
gh auth login --web
```

### Usage

```bash
# Safe Debug (kein Token-Leak)
scripts/utils/get_github_token.sh --debug

# Validierung (Exit Code 0 wenn OK)
scripts/utils/get_github_token.sh --check

# Nutzung in Scripts
TOKEN="$(scripts/utils/get_github_token.sh)"

# Tests ausführen
bash scripts/utils/test_get_github_token.sh

# Shell-Aliase (optional, für Convenience)
alias pt_gh_token_debug='cd ~/Peak_Trade && scripts/utils/get_github_token.sh --debug'
alias pt_gh_token_check='cd ~/Peak_Trade && scripts/utils/get_github_token.sh --check'
```

### Beispiel-Output (Debug Mode)

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
GitHub Token Validation - Success
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Quelle:  gh CLI (gh auth token)
Format:  gho_...*** (40 chars)
Typ:     OAuth Token (z.B. von gh CLI)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ Token ist valide und einsatzbereit
```

## Follow-Up

* PR #377 - Ops README Dokumentation Update (merged 2025-12-27T05:35:08Z)
  * Neue Sektion "GitHub Auth & Token Helper" in `docs/ops/README.md`

## References

* PR #376: https://github.com/rauterfrank-ui/Peak_Trade/pull/376
* Token Helper Docs: `scripts/utils/README_GITHUB_TOKEN.md`
* Ops README: `docs/ops/README.md` (GitHub Auth & Token Helper section)

---

**Benefits Summary:**
* ✅ Keine PAT-Erstellung/Löschung mehr nötig
* ✅ OAuth Tokens von gh CLI werden nativ unterstützt
* ✅ Security First (kein Token-Leaking)
* ✅ Multi-Source Fallback für Robustheit
* ✅ Umfassend getestet (18 Tests)
* ✅ Production-ready und dokumentiert
