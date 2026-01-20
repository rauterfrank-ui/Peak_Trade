# WIP Stash Archives (Remote)

Diese Branches sind Archiv-Snapshots aus ehemals lokalen `git stash` Einträgen.
Ziel: Nichts verlieren, aber lokale Stash-Queue leer halten.

## Archives (2025-12-27)

- `origin&#47;wip&#47;stash-archive-20251227_010316_0` — Merge log workflow
- `origin&#47;wip&#47;stash-archive-20251227_010341_1` — Old merge log WIP 1
- `origin&#47;wip&#47;stash-archive-20251227_010344_2` — Whitespace fixes + DRIFT_GUARD
- `origin&#47;wip&#47;stash-archive-20251227_010347_3` — Ops center changes

## Policy

Archiv-Branches sind **read-only**. Wenn etwas daraus gebraucht wird:

1. Neuen Feature/Fix-Branch von `main` erstellen
2. Benötigte Commits cherry-picken oder Inhalte übernehmen
3. Danach Archiv-Branch optional löschen

## Warum Archive statt lokale Stashes?

**Problem mit lokalen Stashes:**
- Wachsen unbegrenzt (6+ Stashes sind üblich)
- Werden nie aufgeräumt
- Keine Beschreibung außer kurzer Message
- Keine CI/Backup

**Vorteile von Remote Archive Branches:**
- ✅ Sicher auf Remote gespeichert
- ✅ Mit vollständiger Commit-Message dokumentiert
- ✅ CI-validiert (Pre-commit hooks laufen)
- ✅ Einfach zu inspizieren: `git log origin&#47;wip&#47;stash-archive-*`
- ✅ Lokale Stash-Queue bleibt leer und übersichtlich

## Workflow: Stash archivieren

```bash
set -euo pipefail
cd ~/Peak_Trade

git checkout main
test -z "$(git status --porcelain)" || { echo "Working tree not clean"; exit 1; }

# Stash archivieren
STASH="stash@{0}"
BR="wip/stash-archive-$(date +%Y%m%d_%H%M%S)_0"

git stash branch "$BR" "$STASH"

if test -n "$(git status --porcelain)"; then
  git add -A
  git commit -m "wip: archive $STASH"
fi

git push -u origin "$BR"
git checkout main
```

## Workflow: Inhalte aus Archiv nutzen

```bash
# 1. Neuen Branch von main erstellen
git checkout main
git checkout -b feature/my-feature

# 2. Commit(s) aus Archiv cherry-picken
git cherry-pick <commit-hash-from-archive>

# 3. (Optional) Archiv-Branch löschen wenn nicht mehr benötigt
git push origin --delete wip/stash-archive-20251227_010316_0
```

## Inspizieren von Archiven

```bash
# Liste aller Archive
git branch -r | grep wip/stash-archive

# Log eines spezifischen Archives
git log origin/wip/stash-archive-20251227_010316_0

# Diff anschauen
git diff origin/main...origin/wip/stash-archive-20251227_010316_0
```

## Aufräumen (optional)

Wenn Archive nicht mehr benötigt werden:

```bash
# Einzelnes Archiv löschen
git push origin --delete wip/stash-archive-20251227_010316_0

# Alle Archive eines Datums löschen
git branch -r | grep "wip/stash-archive-20251227" | \
  sed 's/origin\///' | xargs -I {} git push origin --delete {}
```

---

**Best Practice:** Archive regelmäßig reviewen (z.B. monatlich) und nicht mehr benötigte Branches löschen.
