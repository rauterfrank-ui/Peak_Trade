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
   - Für konfliktträchtige Stashes: `git checkout -b wip&#47;recover-... main` + `git stash apply`.
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

## Automation (Ops Helper)

Das Tool `scripts/ops/stash_triage.sh` automatisiert die Stash-Triage mit Safe-by-Default-Design.

### Verwendung

```bash
# 1. Alle Stashes auflisten (default)
scripts/ops/stash_triage.sh --list

# 2. Alle Stashes exportieren (ohne Drop)
scripts/ops/stash_triage.sh --export-all

# 3. Gefilterte Stashes exportieren
scripts/ops/stash_triage.sh --export-all --filter "my-feature"

# 4. Export + Drop (mit expliziter Bestätigung)
scripts/ops/stash_triage.sh --export-all --drop-after-export --confirm-drop

# 5. Custom Export-Verzeichnis
scripts/ops/stash_triage.sh --export-all --export-dir /tmp/my_stashes
```

### Features

- ✅ **Safe-by-Default:** Kein Drop ohne `--drop-after-export` + `--confirm-drop`
- ✅ **Keyword-Filter:** `--filter <substring>` für selektiven Export
- ✅ **Strukturierter Export:** Patch + Metadata pro Stash
- ✅ **Session Report:** Tabelle aller exportierten Stashes
- ✅ **Robuste UX:** Exit 0 wenn keine Stashes, Exit 2 bei Drop ohne Confirm

### Export-Format

Jeder Stash wird als zwei Dateien exportiert:

```
docs/ops/stash_refs/
├── stash_ref_20251223-120000_0.patch    # git stash show -p
├── stash_ref_20251223-120000_0.md       # Ref, Message, Diffstat, Files
├── stash_ref_20251223-120000_1.patch
└── stash_ref_20251223-120000_1.md
```

### Session Report Beispiel

```markdown
# Stash Triage Session Report

- Date: 2025-12-23 12:00:00
- Filter: none
- Export Dir: docs/ops/stash_refs
- Drop After Export: yes ✅

## Exported Stashes

| Ref | Message | Patch | Metadata | Dropped |
|-----|---------|-------|----------|---------|
| stash@{0} | WIP: feature-x | stash_ref_..._0.patch | stash_ref_..._0.md | yes ✅ |
```

### Sicherheitsmechanismen

**Warum Safe-by-Default?**

1. **Kein versehentliches Löschen:** `--drop-after-export` alleine reicht nicht
2. **Explizite Bestätigung:** `--confirm-drop` zwingt bewusste Entscheidung
3. **Exit 2 bei unsicherer Nutzung:** Verhindert unbeabsichtigten Drop
4. **Export-before-Delete:** Patch + Metadata immer vorhanden vor Drop

**Beispiel: Unsichere Nutzung (wird verweigert)**

```bash
# ❌ FEHLER: Exit 2
scripts/ops/stash_triage.sh --export-all --drop-after-export

# Ausgabe:
# ❌ 🛑 --drop-after-export requires --confirm-drop (safety check) – exit 2
```

## Referenzen
- Session-Report: `docs/ops/STASH_TRIAGE_SESSION_20251223-051920.md`
- Export-Beispiel: `docs/ops/stash_refs/knowledge_db_strategy_vault_ref_*.md`
- Automation Tool: `scripts/ops/stash_triage.sh`
