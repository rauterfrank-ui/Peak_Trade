#!/usr/bin/env bash
#
# test_get_github_token.sh - Unit tests für get_github_token.sh
#
# Dieser Test validiert die Token-Präfix-Erkennung OHNE echte Token-Werte zu verwenden.
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET_SCRIPT="$SCRIPT_DIR/get_github_token.sh"

if [[ ! -f "$TARGET_SCRIPT" ]]; then
  echo "❌ Skript nicht gefunden: $TARGET_SCRIPT"
  exit 1
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Testing: get_github_token.sh"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Test Helper Functions
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

PASSED=0
FAILED=0

assert_accepts() {
  local test_token="$1"
  local description="$2"

  # Env var setzen und Skript im --check Mode laufen lassen
  set +e  # Temporär set -e deaktivieren
  GITHUB_TOKEN="$test_token" bash "$TARGET_SCRIPT" --check 2>/dev/null
  local result=$?
  set -e  # set -e wieder aktivieren

  if [[ $result -eq 0 ]]; then
    echo "✅ PASS: $description"
    PASSED=$((PASSED + 1))
  else
    echo "❌ FAIL: $description"
    echo "   Token wurde abgelehnt: ${test_token:0:20}..."
    FAILED=$((FAILED + 1))
  fi
}

assert_rejects() {
  local test_token="$1"
  local description="$2"

  # Sollte fehlschlagen
  set +e  # Temporär set -e deaktivieren
  GITHUB_TOKEN="$test_token" bash "$TARGET_SCRIPT" --check 2>/dev/null
  local result=$?
  set -e  # set -e wieder aktivieren

  if [[ $result -eq 0 ]]; then
    echo "❌ FAIL: $description"
    echo "   Token wurde fälschlicherweise akzeptiert: ${test_token:0:20}..."
    FAILED=$((FAILED + 1))
  else
    echo "✅ PASS: $description"
    PASSED=$((PASSED + 1))
  fi
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Test Cases
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

echo "Test 1: Gültige Token-Formate"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Classic PAT (ghp_)
assert_accepts "ghp_1234567890abcdefghijklmnopqrstuvwxyz12345" \
  "Classic PAT (ghp_)"

# Fine-grained PAT (github_pat_)
assert_accepts "github_pat_1234567890abcdefghijklmnopqrstuvwxyz12345678" \
  "Fine-grained PAT (github_pat_)"

# OAuth token (gho_) - NEU!
assert_accepts "gho_1234567890abcdefghijklmnopqrstuvwxyz12345" \
  "OAuth token (gho_)"

# Mit unterschiedlichen Längen (alle über Minimum)
assert_accepts "ghp_123456789012345678901234567890" \
  "Classic PAT (Minimallänge)"

assert_accepts "gho_1234567890123456789012345678901234567890" \
  "OAuth token (lange Version)"

echo

echo "Test 2: Ungültige Token-Formate"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Zu kurz
assert_rejects "ghp_short" \
  "Zu kurzes Token (< 24 Zeichen)"

assert_rejects "gho_xyz" \
  "OAuth token zu kurz"

# Falsches Präfix
assert_rejects "xxx_1234567890abcdefghijklmnopqrstuvwxyz12345" \
  "Ungültiges Präfix (xxx_)"

assert_rejects "token_1234567890abcdefghijklmnopqrstuvwxyz12345" \
  "Ungültiges Präfix (token_)"

# Kein Präfix
assert_rejects "1234567890abcdefghijklmnopqrstuvwxyz12345" \
  "Kein Präfix"

# Leerstring
assert_rejects "" \
  "Leerstring"

# Nur Whitespace
assert_rejects "   " \
  "Nur Whitespace"

echo

echo "Test 3: Whitespace-Handling"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Token mit trailing newline (typisch bei pbpaste)
assert_accepts "ghp_1234567890abcdefghijklmnopqrstuvwxyz12345
" \
  "Token mit Newline am Ende"

# Token mit leading/trailing Spaces
assert_accepts "  ghp_1234567890abcdefghijklmnopqrstuvwxyz12345  " \
  "Token mit Spaces"

# Token mit Tabs
assert_accepts "	ghp_1234567890abcdefghijklmnopqrstuvwxyz12345	" \
  "Token mit Tabs"

echo

echo "Test 4: Debug-Modus (keine echten Token ausgeben)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Test, dass --debug niemals den vollen Token ausgibt
TEST_TOKEN="ghp_1234567890abcdefghijklmnopqrstuvwxyz12345"
OUTPUT=$(GITHUB_TOKEN="$TEST_TOKEN" bash "$TARGET_SCRIPT" --debug 2>&1 || true)

# Prüfe, dass der volle Token NICHT im Output erscheint
if echo "$OUTPUT" | grep -q "$TEST_TOKEN"; then
  echo "❌ FAIL: --debug Modus gibt vollen Token aus (SECURITY ISSUE!)"
  ((FAILED++))
else
  echo "✅ PASS: --debug Modus gibt vollen Token NICHT aus"
  ((PASSED++))
fi

# Prüfe, dass Präfix und Länge vorhanden sind
if echo "$OUTPUT" | grep -q "ghp_"; then
  echo "✅ PASS: --debug Modus zeigt Präfix"
  ((PASSED++))
else
  echo "❌ FAIL: --debug Modus zeigt kein Präfix"
  ((FAILED++))
fi

if echo "$OUTPUT" | grep -q "chars"; then
  echo "✅ PASS: --debug Modus zeigt Länge"
  ((PASSED++))
else
  echo "❌ FAIL: --debug Modus zeigt keine Länge"
  ((FAILED++))
fi

echo

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Summary
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Test Summary"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Passed: $PASSED"
echo "Failed: $FAILED"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [[ $FAILED -gt 0 ]]; then
  echo "❌ Tests FAILED"
  exit 1
else
  echo "✅ All tests PASSED"
  exit 0
fi
