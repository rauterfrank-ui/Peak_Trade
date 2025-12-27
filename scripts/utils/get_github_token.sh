#!/usr/bin/env bash
#
# get_github_token.sh - Sicher GitHub-Token aus verschiedenen Quellen abrufen
#
# Dieses Skript liest GitHub-Token aus verschiedenen Quellen und validiert deren Format.
# Es akzeptiert sowohl Personal Access Tokens (PATs) als auch OAuth Tokens.
#
# Token-Quellen (in dieser Reihenfolge):
#   1. GITHUB_TOKEN environment variable
#   2. GH_TOKEN environment variable
#   3. macOS clipboard (pbpaste)
#   4. gh CLI (gh auth token) als Fallback
#
# Akzeptierte Token-Formate:
#   - ghp_*         (Classic PAT)
#   - github_pat_*  (Fine-grained PAT)
#   - gho_*         (OAuth token)
#
# Usage:
#   scripts/utils/get_github_token.sh              # Token ausgeben (zu stdout)
#   scripts/utils/get_github_token.sh --check      # Nur validieren, nichts ausgeben
#   scripts/utils/get_github_token.sh --debug      # Debug-Info (nur Präfix + Länge)
#
# Exit codes:
#   0 - Gültiges Token gefunden
#   1 - Kein Token gefunden oder ungültiges Format
#   2 - Ungültige Argumente
#
# Sicherheit:
#   - Token-Werte werden NIE geloggt oder ausgegeben (außer im Erfolgsfall zu stdout)
#   - Im --debug Modus wird nur Präfix (erste 4 Zeichen) + Länge angezeigt
#
set -euo pipefail

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Configuration
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

MODE="output"  # output, check, debug

usage() {
  cat <<'EOF'
get_github_token.sh - GitHub-Token sicher abrufen und validieren

Token-Quellen (Priorität):
  1. GITHUB_TOKEN Umgebungsvariable
  2. GH_TOKEN Umgebungsvariable
  3. macOS Clipboard (pbpaste)
  4. gh CLI (gh auth token)

Akzeptierte Token-Formate:
  - ghp_*         (Classic PAT)
  - github_pat_*  (Fine-grained PAT)
  - gho_*         (OAuth token, z.B. von GitHub CLI)

Usage:
  scripts/utils/get_github_token.sh              # Token ausgeben
  scripts/utils/get_github_token.sh --check      # Nur validieren
  scripts/utils/get_github_token.sh --debug      # Debug-Info
  scripts/utils/get_github_token.sh --help       # Diese Hilfe

Exit codes:
  0 - Gültiges Token gefunden
  1 - Kein Token gefunden oder ungültiges Format
  2 - Ungültige Argumente

Sicherheit:
  Token-Werte werden NIEMALS geloggt. Im --debug Modus werden nur
  Präfix (erste 4 Zeichen) und Länge angezeigt.

Beispiele:
  # Token in Variable speichern
  TOKEN=$(scripts/utils/get_github_token.sh)

  # Nur prüfen, ob ein gültiges Token verfügbar ist
  if scripts/utils/get_github_token.sh --check; then
    echo "Token verfügbar"
  fi

  # Debug-Info anzeigen (sicher)
  scripts/utils/get_github_token.sh --debug
EOF
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Argument Parsing
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

for arg in "$@"; do
  case "$arg" in
    --check)
      MODE="check"
      ;;
    --debug)
      MODE="debug"
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "❌ Unbekanntes Argument: $arg" >&2
      echo "Verwende --help für Hilfe." >&2
      exit 2
      ;;
  esac
done

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Token Validation
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Validiert Token-Format
# Akzeptiert: ghp_*, github_pat_*, gho_*
# Returns: 0 wenn gültig, 1 wenn ungültig
validate_token() {
  local token="$1"

  # Leerstring
  if [[ -z "$token" ]]; then
    return 1
  fi

  # Check für akzeptierte Präfixe
  if [[ "$token" =~ ^(ghp_|github_pat_|gho_) ]]; then
    # Minimale Länge prüfen (Präfix + mindestens 20 Zeichen)
    if [[ ${#token} -ge 24 ]]; then
      return 0
    fi
  fi

  return 1
}

# Gibt sicheren Debug-String zurück (nur Präfix + Länge)
get_safe_token_info() {
  local token="$1"
  local prefix="${token:0:4}"
  local length="${#token}"
  echo "${prefix}...*** (${length} chars)"
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Token Retrieval
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

TOKEN=""
SOURCE=""

# Versuche 1: GITHUB_TOKEN Umgebungsvariable
if [[ -n "${GITHUB_TOKEN:-}" ]]; then
  candidate="${GITHUB_TOKEN}"
  # Whitespace/Newlines entfernen
  candidate=$(echo "$candidate" | tr -d '[:space:]')

  if validate_token "$candidate"; then
    TOKEN="$candidate"
    SOURCE="GITHUB_TOKEN env var"
    [[ "$MODE" == "debug" ]] && echo "✅ Token gefunden: $SOURCE" >&2
    [[ "$MODE" == "debug" ]] && echo "   Format: $(get_safe_token_info "$TOKEN")" >&2
  fi
fi

# Versuche 2: GH_TOKEN Umgebungsvariable
if [[ -z "$TOKEN" ]] && [[ -n "${GH_TOKEN:-}" ]]; then
  candidate="${GH_TOKEN}"
  candidate=$(echo "$candidate" | tr -d '[:space:]')

  if validate_token "$candidate"; then
    TOKEN="$candidate"
    SOURCE="GH_TOKEN env var"
    [[ "$MODE" == "debug" ]] && echo "✅ Token gefunden: $SOURCE" >&2
    [[ "$MODE" == "debug" ]] && echo "   Format: $(get_safe_token_info "$TOKEN")" >&2
  fi
fi

# Versuche 3: macOS Clipboard (pbpaste)
if [[ -z "$TOKEN" ]] && command -v pbpaste &>/dev/null; then
  if candidate=$(pbpaste 2>/dev/null); then
    candidate=$(echo "$candidate" | tr -d '[:space:]')

    if validate_token "$candidate"; then
      TOKEN="$candidate"
      SOURCE="macOS clipboard"
      [[ "$MODE" == "debug" ]] && echo "✅ Token gefunden: $SOURCE" >&2
      [[ "$MODE" == "debug" ]] && echo "   Format: $(get_safe_token_info "$TOKEN")" >&2
    elif [[ "$MODE" == "debug" ]]; then
      if [[ -n "$candidate" ]]; then
        echo "⚠️  Clipboard enthält Text, aber kein gültiges GitHub-Token" >&2
        echo "   Erwartet: ghp_*, github_pat_*, oder gho_* Präfix" >&2
        if [[ ${#candidate} -ge 4 ]]; then
          echo "   Gefunden: ${candidate:0:4}... (${#candidate} chars)" >&2
        fi
      fi
    fi
  fi
fi

# Versuche 4: gh CLI (Fallback)
if [[ -z "$TOKEN" ]] && command -v gh &>/dev/null; then
  if gh auth status &>/dev/null; then
    if candidate=$(gh auth token 2>/dev/null); then
      candidate=$(echo "$candidate" | tr -d '[:space:]')

      if validate_token "$candidate"; then
        TOKEN="$candidate"
        SOURCE="gh CLI (gh auth token)"
        [[ "$MODE" == "debug" ]] && echo "✅ Token gefunden: $SOURCE" >&2
        [[ "$MODE" == "debug" ]] && echo "   Format: $(get_safe_token_info "$TOKEN")" >&2
      fi
    fi
  elif [[ "$MODE" == "debug" ]]; then
    echo "⚠️  gh CLI verfügbar, aber nicht authentifiziert" >&2
    echo "   Tipp: Führe 'gh auth login' aus" >&2
  fi
fi

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Output
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

if [[ -z "$TOKEN" ]]; then
  if [[ "$MODE" == "debug" ]]; then
    echo "" >&2
    echo "❌ Kein gültiges GitHub-Token gefunden" >&2
    echo "" >&2
    echo "Versuchte Quellen:" >&2
    echo "  1. GITHUB_TOKEN env var" >&2
    echo "  2. GH_TOKEN env var" >&2
    [[ "$(uname -s)" == "Darwin" ]] && echo "  3. macOS Clipboard (pbpaste)" >&2
    command -v gh &>/dev/null && echo "  4. gh CLI (gh auth token)" >&2
    echo "" >&2
    echo "Akzeptierte Token-Formate:" >&2
    echo "  - ghp_*         (Classic PAT)" >&2
    echo "  - github_pat_*  (Fine-grained PAT)" >&2
    echo "  - gho_*         (OAuth token)" >&2
    echo "" >&2
    echo "Lösungen:" >&2
    echo "  • Export GITHUB_TOKEN: export GITHUB_TOKEN='ghp_...'" >&2
    echo "  • Kopiere Token ins Clipboard" >&2
    echo "  • Authentifiziere gh CLI: gh auth login" >&2
  elif [[ "$MODE" != "check" ]]; then
    echo "❌ Kein gültiges GitHub-Token gefunden" >&2
  fi
  exit 1
fi

# Token gefunden und gültig
case "$MODE" in
  output)
    # Token zu stdout ausgeben
    echo "$TOKEN"
    ;;
  check)
    # Erfolg, nichts ausgeben
    exit 0
    ;;
  debug)
    echo "" >&2
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" >&2
    echo "GitHub Token Validation - Success" >&2
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" >&2
    echo "Quelle:  $SOURCE" >&2
    echo "Format:  $(get_safe_token_info "$TOKEN")" >&2

    # Bestimme Token-Typ
    if [[ "$TOKEN" =~ ^ghp_ ]]; then
      echo "Typ:     Classic Personal Access Token (PAT)" >&2
    elif [[ "$TOKEN" =~ ^github_pat_ ]]; then
      echo "Typ:     Fine-grained Personal Access Token" >&2
    elif [[ "$TOKEN" =~ ^gho_ ]]; then
      echo "Typ:     OAuth Token (z.B. von gh CLI)" >&2
    fi

    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" >&2
    echo "" >&2
    echo "✅ Token ist valide und einsatzbereit" >&2
    ;;
esac

exit 0
