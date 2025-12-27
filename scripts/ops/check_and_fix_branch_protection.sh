#!/usr/bin/env bash
# scripts/ops/check_and_fix_branch_protection.sh
#
# Überprüft und härtet GitHub Branch Protection Rules für main/master
# Stellt sicher, dass PRs mit FAILURE nicht gemerged werden können
#
# Usage:
#   bash scripts/ops/check_and_fix_branch_protection.sh [check|fix|status]
#
# Modes:
#   check  - Nur überprüfen, keine Änderungen (default)
#   fix    - Branch Protection Rules setzen/härten
#   status - Detaillierter Status-Report

set -euo pipefail

ORG="${GITHUB_ORG:-rauterfrank-ui}"
REPO="${GITHUB_REPO:-Peak_Trade}"
BRANCH="${GITHUB_BRANCH:-main}"
MODE="${1:-check}"

# Farben für Output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Required Status Checks
REQUIRED_CHECKS=(
  "audit"
  "tests (3.9)"
  "tests (3.10)"
  "tests (3.11)"
  "Policy Critic Review"
)

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║     Branch Protection Check & Fix                           ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo
echo "Repository: ${ORG}/${REPO}"
echo "Branch:     ${BRANCH}"
echo "Mode:       ${MODE}"
echo

# Dependency check
if ! command -v gh >/dev/null 2>&1; then
  echo -e "${RED}✗ ERROR: gh CLI not found${NC}"
  echo "Install: brew install gh"
  exit 1
fi

if ! command -v jq >/dev/null 2>&1; then
  echo -e "${RED}✗ ERROR: jq not found${NC}"
  echo "Install: brew install jq"
  exit 1
fi

# Auth check
if ! gh auth status -h github.com >/dev/null 2>&1; then
  echo -e "${RED}✗ ERROR: Not authenticated with GitHub${NC}"
  echo "Run: gh auth login -h github.com"
  exit 1
fi

echo -e "${GREEN}✓ Dependencies OK${NC}"
echo

# ─────────────────────────────────────────────────────────────────────
# Funktion: Aktuelle Branch Protection abrufen
# ─────────────────────────────────────────────────────────────────────
fetch_protection() {
  gh api "repos/${ORG}/${REPO}/branches/${BRANCH}/protection" 2>/dev/null || echo "{}"
}

# ─────────────────────────────────────────────────────────────────────
# Funktion: Status analysieren
# ─────────────────────────────────────────────────────────────────────
check_status() {
  local protection
  protection="$(fetch_protection)"

  echo "═══════════════════════════════════════════════════════════════"
  echo "  BRANCH PROTECTION STATUS"
  echo "═══════════════════════════════════════════════════════════════"
  echo

  # Check ob Protection überhaupt existiert
  if [[ "$protection" == "{}" ]] || [[ "$(jq -r '.message // ""' <<<"$protection")" == "Branch not protected" ]]; then
    echo -e "${RED}✗ KRITISCH: Branch ist NICHT geschützt!${NC}"
    echo
    echo "  Das bedeutet:"
    echo "  • PRs können ohne Status Checks gemerged werden"
    echo "  • Admins können direkt in main pushen"
    echo "  • Keine Enforcement von CI-Qualitätsgates"
    echo
    return 1
  fi

  # Required Status Checks
  local has_required_checks
  has_required_checks="$(jq -r '.required_status_checks != null' <<<"$protection")"

  if [[ "$has_required_checks" == "true" ]]; then
    echo -e "${GREEN}✓ Required Status Checks: AKTIVIERT${NC}"
    
    local strict
    strict="$(jq -r '.required_status_checks.strict' <<<"$protection")"
    if [[ "$strict" == "true" ]]; then
      echo -e "${GREEN}  ✓ Strict Mode: Branch muss up-to-date sein${NC}"
    else
      echo -e "${YELLOW}  ⚠ Strict Mode: DEAKTIVIERT (Risiko!)${NC}"
    fi

    echo
    echo "  Erforderliche Checks:"
    local configured_checks
    configured_checks="$(jq -r '.required_status_checks.contexts[]' <<<"$protection" 2>/dev/null || true)"
    
    if [[ -z "$configured_checks" ]]; then
      echo -e "    ${RED}✗ Keine Checks konfiguriert!${NC}"
    else
      while IFS= read -r check; do
        echo "    - $check"
      done <<<"$configured_checks"

      # Prüfe ob alle erforderlichen Checks vorhanden sind
      local missing_checks=()
      for required in "${REQUIRED_CHECKS[@]}"; do
        if ! grep -qF "$required" <<<"$configured_checks"; then
          missing_checks+=("$required")
        fi
      done

      if [[ ${#missing_checks[@]} -gt 0 ]]; then
        echo
        echo -e "  ${YELLOW}⚠ FEHLENDE Checks:${NC}"
        for missing in "${missing_checks[@]}"; do
          echo -e "    ${YELLOW}✗ $missing${NC}"
        done
      else
        echo
        echo -e "  ${GREEN}✓ Alle erforderlichen Checks konfiguriert${NC}"
      fi
    fi
  else
    echo -e "${RED}✗ Required Status Checks: NICHT AKTIVIERT${NC}"
    echo "  → PRs können ohne CI-Checks gemerged werden!"
  fi

  echo

  # Admin Enforcement
  local enforce_admins
  enforce_admins="$(jq -r '.enforce_admins.enabled // false' <<<"$protection")"
  
  if [[ "$enforce_admins" == "true" ]]; then
    echo -e "${GREEN}✓ Admin Enforcement: AKTIVIERT${NC}"
    echo "  → Admins können Branch Protection nicht umgehen"
  else
    echo -e "${RED}✗ Admin Enforcement: DEAKTIVIERT${NC}"
    echo "  → Admins können Branch Protection umgehen!"
    echo "  → Dies erklärt warum PRs mit FAILURE gemerged werden konnten"
  fi

  echo

  # Required Pull Request Reviews
  local require_reviews
  require_reviews="$(jq -r '.required_pull_request_reviews != null' <<<"$protection")"

  if [[ "$require_reviews" == "true" ]]; then
    local required_approvals
    required_approvals="$(jq -r '.required_pull_request_reviews.required_approving_review_count' <<<"$protection")"
    echo -e "${GREEN}✓ Required Reviews: AKTIVIERT (${required_approvals} approval(s))${NC}"
  else
    echo -e "${YELLOW}⚠ Required Reviews: NICHT AKTIVIERT${NC}"
  fi

  echo
  echo "═══════════════════════════════════════════════════════════════"
  echo

  # Gesamtbewertung
  if [[ "$has_required_checks" == "true" ]] && [[ "$enforce_admins" == "true" ]]; then
    echo -e "${GREEN}✓ BEWERTUNG: Branch Protection ist konfiguriert${NC}"
    if [[ ${#missing_checks[@]:-0} -gt 0 ]]; then
      echo -e "${YELLOW}  ⚠ Aber: Einige Checks fehlen${NC}"
      return 1
    fi
    return 0
  else
    echo -e "${RED}✗ BEWERTUNG: Branch Protection ist UNZUREICHEND${NC}"
    echo
    echo "  Empfohlene Aktion: bash $0 fix"
    return 1
  fi
}

# ─────────────────────────────────────────────────────────────────────
# Funktion: Branch Protection härten
# ─────────────────────────────────────────────────────────────────────
fix_protection() {
  echo "═══════════════════════════════════════════════════════════════"
  echo "  BRANCH PROTECTION WIRD GESETZT"
  echo "═══════════════════════════════════════════════════════════════"
  echo

  echo -e "${BLUE}Hinweis: Dies erfordert Admin-Rechte auf dem Repository${NC}"
  echo
  echo "Die folgenden Einstellungen werden aktiviert:"
  echo "  • Required Status Checks (strict mode)"
  echo "  • Enforce für Admins"
  echo "  • Erforderliche Checks:"
  for check in "${REQUIRED_CHECKS[@]}"; do
    echo "    - $check"
  done
  echo

  read -p "Fortfahren? (y/N) " -n 1 -r
  echo
  if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Abgebrochen."
    exit 0
  fi

  echo
  echo "Setze Branch Protection..."

  # JSON für required_status_checks bauen
  local checks_json
  checks_json="$(jq -n --argjson checks "$(printf '%s\n' "${REQUIRED_CHECKS[@]}" | jq -R . | jq -s .)" \
    '{strict: true, contexts: $checks}')"

  # API Call
  if gh api "repos/${ORG}/${REPO}/branches/${BRANCH}/protection" \
    --method PUT \
    --field required_status_checks="$checks_json" \
    --field enforce_admins=true \
    --field required_pull_request_reviews='{"required_approving_review_count":1}' \
    --field restrictions=null \
    >/dev/null 2>&1; then
    
    echo -e "${GREEN}✓ Branch Protection erfolgreich gesetzt${NC}"
    echo
    echo "Verifiziere..."
    sleep 2
    check_status
  else
    echo -e "${RED}✗ FEHLER beim Setzen der Branch Protection${NC}"
    echo
    echo "Mögliche Ursachen:"
    echo "  • Keine Admin-Rechte auf dem Repository"
    echo "  • GitHub API Rate Limit erreicht"
    echo "  • Netzwerkproblem"
    echo
    echo "Manuelle Konfiguration über GitHub Web UI:"
    echo "  https://github.com/${ORG}/${REPO}/settings/branches"
    exit 1
  fi
}

# ─────────────────────────────────────────────────────────────────────
# Main Logic
# ─────────────────────────────────────────────────────────────────────
case "$MODE" in
  check|status)
    if check_status; then
      exit 0
    else
      exit 1
    fi
    ;;
  fix)
    fix_protection
    ;;
  *)
    echo -e "${RED}✗ Ungültiger Mode: $MODE${NC}"
    echo
    echo "Usage: $0 [check|fix|status]"
    echo
    echo "  check  - Überprüfe Branch Protection (default)"
    echo "  fix    - Setze/härte Branch Protection Rules"
    echo "  status - Detaillierter Status-Report (alias für check)"
    exit 1
    ;;
esac

