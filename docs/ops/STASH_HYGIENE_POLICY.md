# Stash Hygiene Policy

Ziel: Stashes **kurzlebig** halten und "stille" Repo-Verschmutzung vermeiden.

## Grundsätze
1. **Analyse vor Delete**  
   - Niemals "blind" droppen. Erst `git stash show --stat` + `--name-only` prüfen.
2. **Keyword-basiert statt index-basiert**  
   - Indizes shiften nach jedem Drop. Daher immer per Keyword identifizieren:
     - `git stash list | grep -i <keyword>`
     - dann `git stash drop stash@{N}` nur mit *soeben* identifiziertem Ref.
3. **Export-before-delete für wichtige Diffs**  
   - Wenn ein Stash als Referenz nützlich ist: Patch exportieren, dokumentieren, dann Stash droppen.
   - Referenzablage: `docs/ops/stash_refs/`
4. **Recovery-Branch nur wenn nötig**  
   - Für konfliktträchtige Stashes: `git checkout -b wip/recover-... main` + `git stash apply`.
   - Danach entweder PR oder Branch verwerfen.

## Minimal-Triage-Checkliste
- `git stash show --stat stash@{N}`
- `git stash show --name-only stash@{N}`
- `git stash show -p stash@{N} | sed -n '1,120p'` (Patch-Head)

## Best-Practice Hooks (verhindern "Trailing Newlines"-Stashes)
- pre-commit Hooks:
  - `trailing-whitespace`
  - `end-of-file-fixer`

## Beispiel-Workflow: Keyword-based Drop

```bash
# 1. Stash identifizieren
KW="my-feature"
REF="$(git stash list | grep -i "$KW" | head -n1 | sed -E 's/^(stash@\{[0-9]+\}).*$/\1/')"

# 2. Prüfen
git stash show --stat "$REF"

# 3. Optional: Export
git diff "${REF}^1" "${REF}" -- path/to/important/file.py > export.patch

# 4. Drop
git stash drop "$REF"
```

## Referenzen
- Session-Report: `docs/ops/STASH_TRIAGE_SESSION_20251223-051920.md`
- Export-Beispiel: `docs/ops/stash_refs/knowledge_db_strategy_vault_ref_*.md`
