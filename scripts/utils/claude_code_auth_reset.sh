#!/usr/bin/env bash
set -euo pipefail

usage() {
cat <<'TXT'
Claude Code Auth Reset Helper (macOS/Linux)

Usage:
  scripts/claude_code_auth_reset.sh            # zeigt Schritte + Kandidatenpfade
  scripts/claude_code_auth_reset.sh --purge    # löscht auth.json (falls gefunden)
  scripts/claude_code_auth_reset.sh --open     # startet danach 'claude'

Flow (in Claude Code Session):
  /permissions
  /logout
  (Claude Code schließen)
  neu starten: claude
  /login

Hinweis:
  * /login, /logout, /permissions laufen NUR innerhalb einer aktiven Claude Code Session.
  * Falls 401 bleibt: macOS Keychain Einträge zu Claude/Anthropic entfernen (manuell).
TXT
}

OPEN=0
PURGE=0

if [ $# -eq 0 ]; then
  # No arguments - run default behavior
  :
else
  for arg in "$@"; do
    case "$arg" in
      --open) OPEN=1 ;;
      --purge) PURGE=1 ;;
      -h|--help) usage; exit 0 ;;
      *) echo "Unknown arg: $arg"; usage; exit 2 ;;
    esac
  done
fi

echo "== Claude Code Auth Troubleshooting =="

if ! command -v claude >/dev/null 2>&1; then
  echo "❌ 'claude' ist nicht im PATH."
  echo "   Installiere Claude Code, dann erneut versuchen."
  exit 1
fi

echo "✅ claude gefunden: $(command -v claude)"
echo

# Kandidaten für auth.json (variieren je nach Version/Installationsweg)
CANDIDATES=(
  "$HOME/.config/claude/auth.json"
  "$HOME/.config/claude-code/auth.json"
  "$HOME/.config/anthropic/claude/auth.json"
  "$HOME/Library/Application Support/Claude Code/auth.json"
  "$HOME/Library/Application Support/Claude/auth.json"
  "$HOME/Library/Application Support/Anthropic/Claude Code/auth.json"
  "$HOME/Library/Application Support/Anthropic/Claude/auth.json"
)

FOUND=()
for f in "${CANDIDATES[@]}"; do
  if [ -f "$f" ]; then
    FOUND+=("$f")
  fi
done

echo "Auth-Datei Kandidaten (existierende):"
if [ "${#FOUND[@]}" -eq 0 ]; then
  echo "  (keine gefunden – ok, je nach Setup)"
else
  for f in "${FOUND[@]}"; do
    echo "  - $f"
  done
fi
echo

if [ "$PURGE" -eq 1 ]; then
  if [ "${#FOUND[@]}" -eq 0 ]; then
    echo "ℹ️  --purge: keine auth.json gefunden → nichts zu löschen."
  else
    echo "⚠️  --purge: lösche auth.json Dateien..."
    for f in "${FOUND[@]}"; do
      rm -f "$f"
      echo "  deleted: $f"
    done
    echo "✅ auth.json gelöscht."
  fi
  echo
fi

cat <<'TXT'
Nächste Schritte (wichtig, genau so):

1. Claude Code starten:
   claude

2. In der Claude Code Session:
   /permissions
   /logout

3. Claude Code komplett schließen.

4. Claude Code neu starten:
   claude

5. In der neuen Session:
   /login

Wenn danach immer noch OAuth 401:
  * macOS: Schlüsselbundverwaltung öffnen → nach "Claude" / "Anthropic" suchen → Einträge entfernen
    (danach claude neu starten und /login erneut)

TXT

if [ "$OPEN" -eq 1 ]; then
  echo "== Starte claude =="
  exec claude
fi
