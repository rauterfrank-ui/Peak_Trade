#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────
# gh TLS x509 OSStatus -26276 (macOS) — minimal diagnose → smallest fix
# Purpose: Diagnose and fix gh/GitHub API TLS certificate errors on macOS.
#
# Modes:
#   - Default: run full diag + fix paths A/B/C
#   - Diag-only: PT_GH_TLS_DIAG_ONLY=1 ./gh_tls_diag_fix.sh
# ─────────────────────────────────────────────────────────────

set -euo pipefail

# 0) Locate repo root
if git rev-parse --show-toplevel >/dev/null 2>&1; then
  REPO_ROOT="$(git rev-parse --show-toplevel)"
else
  REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
fi
cd "${REPO_ROOT}"

# grep helper (portable: works without ripgrep)
_grep() {
  if command -v rg >/dev/null 2>&1; then
    rg "$@"
  else
    grep -E "$@"
  fi
}

# 1) capture evidence (no secrets)
mkdir -p out/ops/gh_tls
ts="$(date -u +%Y%m%dT%H%M%SZ)"
exec > >(tee "out/ops/gh_tls/gh_tls_diag_${ts}.log") 2>&1

echo "=== BASIC ==="
sw_vers
uname -a
which -a gh || true
gh --version || true
brew --version || true

echo "=== GH AUTH STATUS (no tokens printed) ==="
gh auth status || true

echo "=== GH API (expect failure if TLS broken) ==="
GITHUB_TOKEN= gh api -H 'Accept: application/vnd.github+json' rate_limit || true

echo "=== PR VIEW (your requested probe) ==="
gh pr view 1276 || true

echo "=== PROXY / SSL ENV ==="
env | _grep -i "https?_proxy|all_proxy|no_proxy|ssl|cert|cainfo|keychain|gh_" || true

echo "=== GIT PROXY / SSL CONFIG (read-only) ==="
git config --global -l 2>/dev/null | _grep -i "proxy|ssl|http\." || true
git config -l 2>/dev/null | _grep -i "proxy|ssl|http\." || true

echo "=== CURL (your probe; first ~120 lines for safety) ==="
( curl -Iv https://api.github.com 2>&1 || true ) | sed -n '1,120p'

echo "=== OPENSSL HANDSHAKE + CHAIN (helps detect SSL inspection) ==="
if command -v openssl >/dev/null 2>&1; then
  echo | openssl s_client -connect api.github.com:443 -servername api.github.com -showcerts 2>/dev/null \
    | sed -n '1,220p'
else
  echo "OPENSSL_MISSING"
fi

echo "=== macOS TRUSTD status (read-only) ==="
ps aux | _grep -n "trustd" || true

echo "=== DONE DIAG ==="

# ─────────────────────────────────────────────────────────────
# Fix paths (skip if diag-only)
# ─────────────────────────────────────────────────────────────
if [[ "${PT_GH_TLS_DIAG_ONLY:-0}" == "1" ]]; then
  echo "PT_GH_TLS_DIAG_ONLY=1: skipping fix paths. Re-run without it to apply fixes."
  exit 0
fi

# Fix path A: update/reinstall gh (safe, quick)
if command -v brew >/dev/null 2>&1; then
  echo "=== FIX A: brew upgrade/reinstall gh ==="
  brew update
  brew upgrade gh || true
  brew reinstall gh
  gh --version
fi

gh auth status || true
gh pr view 1276 || true
GITHUB_TOKEN= gh api rate_limit || true

# Fix path B: detect SSL inspection and install corp root CA (only if needed)
mkdir -p out/ops/gh_tls/certs
if command -v openssl >/dev/null 2>&1; then
  echo | openssl s_client -connect api.github.com:443 -servername api.github.com -showcerts 2>/dev/null \
    | awk '
      /BEGIN CERTIFICATE/ {i++}
      i>0 {print > ("out/ops/gh_tls/certs/chain_" i ".pem")}
    ' || true

  for f in out/ops/gh_tls/certs/chain_*.pem; do
    [[ -s "$f" ]] || continue
    echo "--- $f ---"
    openssl x509 -in "$f" -noout -subject -issuer -dates 2>/dev/null || true
  done
fi

ca_pem=""
for f in out/ops/gh_tls/certs/chain_*.pem; do
  [[ -s "$f" ]] && ca_pem="$f"
done

if [[ -n "${ca_pem:-}" ]] && [[ -s "${ca_pem:-}" ]]; then
  echo "=== CANDIDATE_CA_PEM: ${ca_pem} ==="
  openssl x509 -in "${ca_pem}" -noout -subject -issuer 2>/dev/null || true

  echo "=== Adding to System.keychain (requires sudo) ==="
  sudo security add-trusted-cert -d -r trustRoot -k /Library/Keychains/System.keychain "${ca_pem}" || true

  sudo killall -HUP trustd 2>/dev/null || true
fi

gh auth status || true
gh pr view 1276 || true
GITHUB_TOKEN= gh api rate_limit || true

# Fix path C: if proxy env is set, force NO_PROXY for GitHub endpoints (minimal)
echo "=== FIX C: NO_PROXY for GitHub ==="
export NO_PROXY="${NO_PROXY:-},github.com,api.github.com,uploads.github.com,raw.githubusercontent.com"
export no_proxy="${no_proxy:-},github.com,api.github.com,uploads.github.com,raw.githubusercontent.com"

gh pr view 1276 || true
GITHUB_TOKEN= gh api rate_limit || true

# Snapshot final state (for paste-back)
echo "=== FINAL SNAPSHOT ==="
gh --version || true
gh auth status || true
( curl -Iv https://api.github.com 2>&1 || true ) | sed -n '1,120p'
env | _grep -i "https?_proxy|all_proxy|no_proxy|ssl|cert|cainfo|keychain|gh_" || true
ls -la out/ops/gh_tls out/ops/gh_tls/certs 2>/dev/null || true
