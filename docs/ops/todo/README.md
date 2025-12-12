# TODO-Board – Nutzung

## Zweck

Dieses Board ist die zentrale Aufgabenliste für Peak_Trade.

**Single Source of Truth:** `PEAK_TRADE_TODO_BOARD.md`

---

## Workflow (kurz)

1. **Neue Idee** → INBOX
2. **Wöchentlich (Fr):** INBOX triagieren → NEXT
3. **Daily:** max 3 Items in NOW (WIP-Limit)
4. **Blocker** immer mit Grund + Entblocker notieren

---

## ID-Format

Jedes TODO-Item hat eine eindeutige ID: `PT-TODO-XXXXXX`

**Beispiel:**
```markdown
- [ ] [PT-TODO-000003] (tag: r_and_d) RSI-Varianten-Sweep implementieren
```

---

## GitHub Issues (optional)

Wenn du GitHub Issues nutzt:

1. **Titel** enthält die ID in eckigen Klammern:
   ```
   [PT-TODO-000021] TODO→GitHub-Issue Sync testen
   ```

2. **Duplikate finden:**
   ```bash
   gh issue list --search "[PT-TODO-000021]"
   ```

3. **Issue-URL** kann direkt neben dem Item stehen:
   ```markdown
   - [ ] [PT-TODO-000021] (tag: ops) Sync testen
     Issue: https://github.com/USER/REPO/issues/42
   ```

---

## Desktop-Zugang (macOS)

### Variante 1: Finder Alias (einfach)

1. Rechtsklick auf `PEAK_TRADE_TODO_BOARD.md`
2. "Alias erstellen"
3. Alias auf Schreibtisch ziehen

### Variante 2: Symlink (Terminal)

**Für Frank (aktueller Pfad):**
```bash
ln -s "/Users/frnkhrz/Peak_Trade/docs/ops/todo/PEAK_TRADE_TODO_BOARD.md" \
  "$HOME/Desktop/Peak_Trade_TODO.md"
```

**Allgemein:**
```bash
ln -s "/ABSOLUTER/PFAD/ZUM/REPO/docs/ops/todo/PEAK_TRADE_TODO_BOARD.md" \
  "$HOME/Desktop/Peak_Trade_TODO.md"
```

**Symlink entfernen:**
```bash
rm "$HOME/Desktop/Peak_Trade_TODO.md"
```

---

## Status-Werte

| Status | Bedeutung |
|--------|-----------|
| INBOX | Sammelbecken, noch nicht triagiert |
| NEXT | Als nächstes geplant |
| NOW | Aktiv in Arbeit (WIP-Limit: max 3) |
| BLOCKED | Blockiert, Grund + Entblocker angeben |
| DONE | Abgeschlossen, mit Datum |

---

## Tags (Beispiele)

`ops`, `ci`, `governance`, `live`, `execution`, `r_and_d`, `docs`, `dashboard`, `cleanup`

**Frei erweiterbar** – nutze Tags, die für dich Sinn machen.

---

## Weekly Rollup (5 Min, Freitags)

Kurze Reflexion am Ende der Woche:

1. **Anzahl neue INBOX:** Wie viele Tasks kamen dazu?
2. **Anzahl DONE:** Was wurde abgeschlossen?
3. **Top-Blocker:** Was blockiert aktuell?
4. **Entscheidung:** WIP-Limit anpassen? Scope schneiden?

**Beispiel:**
```markdown
**KW 50 (2025-12-12):**
- Anzahl neue INBOX: 7
- Anzahl DONE: 7
- Top-Blocker: Vol-Regime-Filter Design
- Entscheidung: WIP-Limit beibehalten (3), Fokus auf R&D-Items
```

---

## DONE Items archivieren

**Regel:** DONE bleibt 14 Tage im Board, danach optional in Archive verschieben.

**Archive-Ordner:** `docs/ops/todo/archive/`

**Archiv-Datei:** z.B. `archive/DONE_2025_KW48.md`

**Beispiel:**
```bash
# Erstelle Archiv-Datei
touch docs/ops/todo/archive/DONE_2025_KW50.md

# Kopiere DONE-Items dorthin
# ... (manuell oder per Script)
```

---

## Grey-Track (Zukünftige Tasks)

Langfristige Tasks sind im Board in `<details>` collapsed:

```markdown
<details>
<summary>Mittelfristig (48 Sessions) - Click to expand</summary>

- [ ] [PT-TODO-100] (tag: r_and_d) Monte-Carlo-Robustness
- [ ] [PT-TODO-101] (tag: r_and_d) Korrelations-Matrix-Plot

</details>
```

**Vorteil:** Übersichtlichkeit, ohne langfristige Planung zu verlieren.

---

## Best Practices

1. **WIP-Limit einhalten:** Max 3 Items in NOW
2. **Blocker sofort notieren:** Grund + Entblocker
3. **DONE mit Datum:** Für Geschwindigkeits-Tracking
4. **Wöchentlich triagieren:** INBOX → NEXT
5. **Archive regelmäßig:** Alte DONE-Items auslagern

---

**Erstellt:** 2025-12-12
**Maintainer:** Frank
