#!/usr/bin/env bash
set -euo pipefail

JSON=0
for arg in "$@"; do
  case "$arg" in
    --json) JSON=1 ;;
    -h|--help)
      cat <<'TXT'
check_claude_code_ready.sh

Read-only Preflight für Claude Code:

  * Ist 'claude' im PATH?
  * Welche auth.json Kandidaten existieren?
  * macOS Hinweis: Keychain reset als letzter Schritt

Usage:
  scripts/check_claude_code_ready.sh
  scripts/check_claude_code_ready.sh --json
TXT
      exit 0
      ;;
    *) echo "Unknown arg: $arg" >&2; exit 2 ;;
  esac
done

has_claude=0
claude_path=""
if command -v claude >/dev/null 2>&1; then
  has_claude=1
  claude_path="$(command -v claude)"
fi

# Kandidatenpfade (wie im reset-script)
candidates=(
  "$HOME/.config/claude/auth.json"
  "$HOME/.config/claude-code/auth.json"
  "$HOME/.config/anthropic/claude/auth.json"
  "$HOME/Library/Application Support/Claude Code/auth.json"
  "$HOME/Library/Application Support/Claude/auth.json"
  "$HOME/Library/Application Support/Anthropic/Claude Code/auth.json"
  "$HOME/Library/Application Support/Anthropic/Claude/auth.json"
)

found=()
for f in "${candidates[@]}"; do
  [[ -f "$f" ]] && found+=("$f")
done

platform="$(uname -s)"

if [[ "$JSON" -eq 1 ]]; then
  # minimal JSON output (ohne jq)
  printf '{'
  printf '"has_claude":%s,' "$has_claude"
  printf '"claude_path":"%s",' "${claude_path//\"/\\\"}"
  printf '"platform":"%s",' "${platform//\"/\\\"}"
  printf '"auth_files":['
  for i in "${!found[@]}"; do
    p="${found[$i]//\"/\\\"}"
    printf '"%s"' "$p"
    [[ "$i" -lt $((${#found[@]}-1)) ]] && printf ','
  done
  printf ']'
  printf '}\n'
  exit 0
fi

echo "== Claude Code Preflight =="
if [[ "$has_claude" -eq 1 ]]; then
  echo "✅ claude im PATH: $claude_path"
else
  echo "❌ claude NICHT im PATH"
  echo "   → Installiere Claude Code (danach erneut prüfen)."
fi

echo
echo "Auth-Dateien (auth.json) gefunden:"
if [[ "${#found[@]}" -eq 0 ]]; then
  echo "  (keine gefunden – ok, je nach Setup)"
else
  for f in "${found[@]}"; do
    echo "  - $f"
  done
fi

echo
echo "Hinweise:"
echo "  - /login /logout /permissions funktionieren NUR in einer Claude Code Session."
if [[ "$platform" == "Darwin" ]]; then
  echo "  - macOS: Wenn 401 bleibt → Keychain 'Claude'/'Anthropic' Einträge entfernen (letzter Schritt)."
fi

# exit code:
#   0 = ok (claude found)
#   2 = missing claude
[[ "$has_claude" -eq 1 ]] && exit 0 || exit 2
