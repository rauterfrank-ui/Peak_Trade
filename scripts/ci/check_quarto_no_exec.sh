#!/usr/bin/env bash
set -euo pipefail

# Welche .qmd Dateien sollen "no-exec" erzwingen?
# Fokus: Reports/Templates (da wollt ihr keine Execution in CI)
QMD_FILES=()
while IFS= read -r line; do
  QMD_FILES+=("$line")
done < <(git ls-files '*.qmd' | grep -E '^(templates/quarto/|reports/quarto/|reports/).+\.qmd$' || true)

if [ "${#QMD_FILES[@]}" -eq 0 ]; then
  echo "✅ No .qmd files in templates/quarto/ or reports/ – skipping no-exec guard."
  exit 0
fi

echo "🔎 Quarto no-exec guard: scanning ${#QMD_FILES[@]} file(s)..."

fail=0

for f in "${QMD_FILES[@]}"; do
  if [ ! -f "$f" ]; then
    continue
  fi

  # 1) Harte Regel: keine ausführbaren Python-Chunks
  if grep -nE '^```{python' "$f" >/dev/null; then
    echo "❌ EXECUTABLE PYTHON CHUNK FOUND in $f"
    grep -nE '^```{python' "$f" || true
    fail=1
  fi

  # 2) Harte Regel: YAML Frontmatter muss execute.enabled=false enthalten
  #    (wir prüfen nur innerhalb des ersten Frontmatter-Blocks --- ... ---)
  awk '
    BEGIN { in_fm=0; seen_open=0; in_exec=0; ok=0; }
    /^---[[:space:]]*$/ {
      if (seen_open==0) { in_fm=1; seen_open=1; next }
      if (in_fm==1) { in_fm=0; exit }  # Ende Frontmatter
    }
    in_fm==1 {
      if ($0 ~ /^execute:[[:space:]]*$/) { in_exec=1; next }
      if (in_exec==1 && $0 ~ /^[[:space:]]*enabled:[[:space:]]*false[[:space:]]*$/) { ok=1; next }
      # Wenn ein neuer top-level key beginnt, verlassen wir execute-block
      if (in_exec==1 && $0 ~ /^[A-Za-z0-9_-]+:[[:space:]]*.*$/) { in_exec=0 }
    }
    END { if (ok==1) exit 0; else exit 1 }
  ' "$f" >/dev/null 2>&1 || {
    echo "❌ MISSING 'execute: enabled: false' in YAML frontmatter: $f"
    fail=1
  }

done

if [ "$fail" -ne 0 ]; then
  echo ""
  echo "🛑 Quarto no-exec guard FAILED."
  echo "Fix: convert \`\`\`{python} -> \`\`\`python and ensure YAML includes:"
  echo "  execute:"
  echo "    enabled: false"
  exit 1
fi

echo "✅ Quarto no-exec guard PASSED."
