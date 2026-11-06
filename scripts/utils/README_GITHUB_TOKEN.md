# GitHub Token Utility Scripts

Dieses Verzeichnis enthält Utility-Skripte für den sicheren Umgang mit GitHub-Token.

## get_github_token.sh

Sicheres Abrufen und Validieren von GitHub-Token aus verschiedenen Quellen.

### Features

- **Multi-Source Support**: Liest Token aus mehreren Quellen (Priorität):
  1. `GITHUB_TOKEN` Umgebungsvariable
  2. `GH_TOKEN` Umgebungsvariable
  3. macOS Clipboard (via `pbpaste`)
  4. GitHub CLI (via `gh auth token`)

- **Token-Format-Validierung**: Akzeptiert alle offiziellen GitHub-Token-Formate:
  - `ghp_*` - Classic Personal Access Token (PAT)
  - `github_pat_*` - Fine-grained Personal Access Token
  - `gho_*` - OAuth Token (z.B. von GitHub CLI)

- **Sicherheit First**:
  - Token-Werte werden **NIEMALS** geloggt oder ausgegeben (außer im Erfolgsfall zu stdout)
  - Debug-Modus zeigt nur Präfix (erste 4 Zeichen) + Länge
  - Whitespace/Newlines werden automatisch entfernt

- **Robustes Error-Handling**:
  - Klare Exit Codes
  - Hilfreiche Fehlermeldungen
  - Multiple Fallback-Optionen

### Usage

```bash
# Token abrufen (für Verwendung in Scripts)
TOKEN=$(scripts/utils/get_github_token.sh)
export GITHUB_TOKEN="$TOKEN"

# Nur validieren (prüfen ob Token verfügbar)
if scripts/utils/get_github_token.sh --check; then
  echo "✅ Token verfügbar"
else
  echo "❌ Kein gültiges Token"
fi

# Debug-Info anzeigen (SICHER - keine Token-Werte)
scripts/utils/get_github_token.sh --debug
```

### Examples

#### Token aus Environment Variable

```bash
export GITHUB_TOKEN="gho_xxxxxxxxxxxxxxxxxxxx"
scripts/utils/get_github_token.sh --check  # ✅ Success
```

#### Token aus Clipboard (macOS)

```bash
# 1. Kopiere Token ins Clipboard (z.B. aus GitHub Settings)
# 2. Führe Skript aus
scripts/utils/get_github_token.sh --debug
# ✅ Token gefunden: macOS clipboard
#    Format: gho_...*** (40 chars)
#    Typ:     OAuth Token (z.B. von gh CLI)
```

#### Token von gh CLI (Fallback)

```bash
gh auth login  # Einmalig
scripts/utils/get_github_token.sh --check  # ✅ Success via gh CLI
```

### Use Cases

#### In CI/CD Pipelines

```bash
#!/usr/bin/env bash
set -euo pipefail

# Token sicher abrufen
if ! TOKEN=$(scripts/utils/get_github_token.sh); then
  echo "❌ GitHub Token erforderlich"
  exit 1
fi

# Token verwenden (nicht loggen!)
gh api /user --header "Authorization: token $TOKEN"
```

#### In lokalen Scripts

```bash
#!/usr/bin/env bash

# Prüfe ob Token verfügbar
if ! scripts/utils/get_github_token.sh --check; then
  echo "⚠️  Kein GitHub Token verfügbar"
  echo "Optionen:"
  echo "  1. export GITHUB_TOKEN='...'"
  echo "  2. Token ins Clipboard kopieren"
  echo "  3. gh auth login"
  exit 1
fi

# Token ist verfügbar, Script kann fortfahren
echo "✅ GitHub Token OK"
```

### Exit Codes

| Code | Bedeutung |
|------|-----------|
| 0 | Gültiges Token gefunden |
| 1 | Kein Token gefunden oder ungültiges Format |
| 2 | Ungültige Argumente / Verwendungsfehler |

### Security Notes

⚠️ **WICHTIG**: Dieses Skript gibt Token-Werte NUR zu stdout aus (im Standard-Modus ohne Flags). In allen anderen Modi (--check, --debug) werden Token-Werte niemals ausgegeben.

✅ **Best Practices**:
- Verwende `--check` für Preflight-Checks
- Verwende `--debug` für Troubleshooting (safe)
- Speichere Token nie in Logs oder Dateien
- Verwende Environment Variables für Token in Scripts

## test_get_github_token.sh

Umfassende Test-Suite für `get_github_token.sh`.

### Usage

```bash
# Alle Tests ausführen
scripts/utils/test_get_github_token.sh

# Expected Output:
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Test Summary
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Passed: 18
# Failed: 0
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ✅ All tests PASSED
```

### Test Coverage

- ✅ Gültige Token-Formate (ghp_, github_pat_, gho_)
- ✅ Ungültige Token-Formate
- ✅ Whitespace-Handling (Newlines, Spaces, Tabs)
- ✅ Security: Debug-Modus gibt keine Token-Werte aus
- ✅ Minimale Längen-Validierung

### Integration in CI

```yaml
# .github/workflows/test.yml
- name: Test GitHub Token Script
  run: bash scripts/utils/test_get_github_token.sh
```

## Migration Guide

### Wenn du bisher PAT-only Validierung hattest

**Vorher:**

```bash
# Nur Classic PATs akzeptiert
if [[ ! "$TOKEN" =~ ^ghp_ ]]; then
  echo "❌ Nur Classic PATs erlaubt"
  exit 1
fi
```

**Nachher:**

```bash
# Alle Token-Typen akzeptiert
if ! TOKEN=$(scripts/utils/get_github_token.sh); then
  echo "❌ Kein gültiges Token"
  exit 1
fi
```

### Vorteile der Migration

- ✅ OAuth Tokens werden akzeptiert (kein PAT-Zwang mehr)
- ✅ Multiple Token-Quellen (Env, Clipboard, gh CLI)
- ✅ Automatisches Whitespace-Trimming
- ✅ Bessere Fehlermeldungen
- ✅ Sicherheits-First Design

## Changelog

### v1.0.0 (2025-12-27)

- ✨ Initiale Version mit Multi-Source Token Support
- ✨ OAuth Token Support (`gho_` Präfix)
- ✨ Classic PAT Support (`ghp_` Präfix)
- ✨ Fine-grained PAT Support (`github_pat_` Präfix)
- ✨ macOS Clipboard Integration
- ✨ GitHub CLI Integration (Fallback)
- ✅ Umfassende Test-Suite (18 Tests)
- 🔒 Sicherheits-Features (kein Token-Leaking)

## Related

- GitHub Token-Dokumentation: https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens
- GitHub CLI: https://cli.github.com/
