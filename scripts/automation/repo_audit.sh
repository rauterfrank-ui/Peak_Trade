#!/usr/bin/env bash
set -euo pipefail

MODE="${1:-quick}"   # quick | full
TS="$(date +%Y-%m-%d_%H-%M-%S)"
ROOT="$(git rev-parse --show-toplevel)"
OUT_RAW="${ROOT}/reports/audit/${TS}"
OUT_DOC="${ROOT}/docs/audits/REPO_AUDIT_${TS}.md"

mkdir -p "${OUT_RAW}"

have() { command -v "$1" >/dev/null 2>&1; }

section() {
  echo
  echo "## $1"
}

run() {
  local name="$1"; shift
  echo "---- ${name} ----" | tee -a "${OUT_RAW}/_log.txt"
  ( "$@" ) > "${OUT_RAW}/${name}.txt" 2>&1 || echo "[FAILED] ${name}" >> "${OUT_RAW}/_log.txt"
}

echo "Peak_Trade Repo Audit @ ${TS}" > "${OUT_RAW}/_meta.txt"
echo "ROOT=${ROOT}" >> "${OUT_RAW}/_meta.txt"
git rev-parse HEAD >> "${OUT_RAW}/_meta.txt" 2>/dev/null || true

# --- Inventory
run "git_status" git status -sb
run "git_diffstat" bash -c 'git diff --stat || true'
run "git_ls_files_count" bash -c 'echo "tracked_files=$(git ls-files | wc -l | tr -d " ")"'
run "top_level_tree" bash -c 'ls -la'
run "tree_depth2" bash -c 'command -v tree >/dev/null && tree -L 2 -a -I ".git|.venv|__pycache__|.pytest_cache|.mypy_cache|node_modules|reports" || echo "tree not installed"'
run "largest_files" bash -c 'git ls-files -z | xargs -0 -I{} bash -c "wc -c \"{}\" 2>/dev/null | awk '\''{print \$1\" \"\$2}'\''" | sort -nr | head -n 50'
run "python_files" bash -c 'git ls-files "*.py" | wc -l | tr -d " "'

# --- Hygiene checks
run "crlf_check" bash -c 'git ls-files -z | xargs -0 file | grep -i "CRLF" || true'
run "tabs_check" bash -c 'git ls-files "*.py" "*.md" "*.toml" "*.yml" "*.yaml" 2>/dev/null | xargs -I{} bash -c "grep -nP \"\t\" \"{}\" 2>/dev/null | head -n 5 || true"'
run "todo_fixme" bash -c 'git grep -nE "TODO|FIXME|HACK" -- . ":!reports" || true'

# --- Python sanity
PYTHON_CMD=""
if have python; then
  PYTHON_CMD="python"
elif have python3; then
  PYTHON_CMD="python3"
fi

if [ -n "${PYTHON_CMD}" ]; then
  run "python_version" ${PYTHON_CMD} --version
  run "compileall_src" bash -c "${PYTHON_CMD} -m compileall -q src || true"
  run "pip_check" bash -c "${PYTHON_CMD} -m pip check || true"
else
  echo "python not found" > "${OUT_RAW}/python_version.txt"
fi

# --- Tests (quick vs full)
if [ -n "${PYTHON_CMD}" ]; then
  if [ "${MODE}" = "full" ]; then
    run "pytest" bash -c "${PYTHON_CMD} -m pytest -q || true"
  else
    run "pytest_smoke" bash -c "${PYTHON_CMD} -m pytest -q -k \"not slow\" || true"
  fi
fi

# --- Linters / Formatters / Typecheck (optional)
if have ruff; then
  run "ruff_check" ruff check .
  run "ruff_format_check" ruff format --check .
else
  echo "ruff not installed (skipped)" > "${OUT_RAW}/ruff_check.txt"
fi

if have black; then
  run "black_check" black --check .
else
  echo "black not installed (skipped)" > "${OUT_RAW}/black_check.txt"
fi

if have mypy; then
  run "mypy" mypy .
else
  echo "mypy not installed (skipped)" > "${OUT_RAW}/mypy.txt"
fi

# --- Security / deps (optional)
if have pip-audit; then
  run "pip_audit" pip-audit
else
  echo "pip-audit not installed (skipped)" > "${OUT_RAW}/pip_audit.txt"
fi

if have bandit; then
  run "bandit" bandit -r src -q
else
  echo "bandit not installed (skipped)" > "${OUT_RAW}/bandit.txt"
fi

if have gitleaks; then
  run "gitleaks" bash -c 'gitleaks detect --no-git --redact --source . || true'
else
  echo "gitleaks not installed (skipped)" > "${OUT_RAW}/gitleaks.txt"
fi

# --- Report (curated markdown)
{
  echo "# Repo Audit – ${TS}"
  echo
  echo "- Commit: \`$(git rev-parse --short HEAD 2>/dev/null || echo unknown)\`"
  echo "- Mode: \`${MODE}\`"
  echo
  echo "## Key Snapshots"
  echo
  echo "### git status"
  echo '```'
  sed -n '1,120p' "${OUT_RAW}/git_status.txt" 2>/dev/null || true
  echo '```'
  echo
  echo "### Largest tracked files (top 20)"
  echo '```'
  sed -n '1,20p' "${OUT_RAW}/largest_files.txt" 2>/dev/null || true
  echo '```'
  echo
  echo "### TODO/FIXME/HACK (first 80 lines)"
  echo '```'
  sed -n '1,80p' "${OUT_RAW}/todo_fixme.txt" 2>/dev/null || true
  echo '```'
  echo
  echo "## Tool Results (presence + exit summary)"
  echo
  for f in ruff_check black_check mypy pip_audit bandit gitleaks pytest pytest_smoke compileall_src; do
    if [ -f "${OUT_RAW}/${f}.txt" ]; then
      echo "### ${f}"
      echo '```'
      sed -n '1,120p' "${OUT_RAW}/${f}.txt"
      echo '```'
      echo
    fi
  done
  echo "## Raw artifacts"
  echo "- Raw outputs: \`reports/audit/${TS}/\` (nicht committen)"
} > "${OUT_DOC}"

echo "Wrote raw audit to: ${OUT_RAW}"
echo "Wrote curated audit report: ${OUT_DOC}"
