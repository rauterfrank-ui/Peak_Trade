# Master-V2: Konsolidierungs- und Integrationsanalyse (read-only)

**Stand (lokal geprüft):** `main` = `a80748b5` — **enthält kein** `src&#47;trading&#47;master_v2&#47;`.
**Befund:** Sämtliche genannten Feature-Branch-Tipps sind **jeweils genau 1 Commit** mit **direktem Eltern-Commit = `a80748b5` (main)**. Es gibt **keine** lineare Aneinanderkettung dieser Arbeit als Git-Historie: die Branches sind **Geschwister-Kommits**, kein `feat-A → feat-B → feat-C`‑Ketten-Graph.

---

## 1. Executive Summary

- Die **16 älteren „Contract-“Branches** (universe … fixture-factory) fügen jeweils **isoliert** wenige Dateien hinzu (Beispiel: `feat&#47;master-v2-universe-selection-contract-v1` nur 3 Pfade unter `src&#47;trading&#47;`), während die **6 neueren Slices** (scenario-matrix … dry-smoke) jeweils eine **kompakte, aber inhaltlich überlappende** `src&#47;trading&#47;master_v2&#47;`-Gesamtkopie in einem Commit tragen. None dieser „Contract-“-Tipps ist **Vorfahre** des Scenario-Matrix-Tipps `8171d19` — es wurde **kein** „Merge der vorherigen Slices in Git-Abstammung“ vollzogen.
- Eine **naive serielle Fast-Forward-/Merge-Reihenfolge** aller 22 Branches würde **keine sinnvolle** Historie abarbeiten, sondern auf **add/add- und `__init__`-Konflikten** auf derselben leeren `main`‑Basis treffen, weil mehrere Tipps **dieselbe Verzeichnisstruktur** unabhängig voneinander erzeugen.
- **Empfehlung:** Einen **einzigen kanonischen Baum** auf `main` legen, idealerweise den **jüngsten, umfassendsten Tipp** `feat&#47;master-v2-dry-smoke-adapter-v1` (`fb903289`) als **Soll-Zustand** — verified: gegenüber `10f4f2a5` (local-debug-cli) nur **+2 Dateien** (`scripts&#47;dev&#47;master_v2_dry_smoke_v1.py`, `test_dry_smoke_dev_script_v1.py`); `src&#47;trading&#47;master_v2` ist gegenüber `8171d19` um **4 zusätzliche Module** erweitert (u. a. `local_evaluator_*`, `input_adapter_v1`, `local_debug_cli_v1`). <!-- pt:ref-target-ignore -->

## 2. Empfohlene Integrationsstrategie

| Option | Kurz | Eignung |
|--------|------|---------|
| **A. Ein canonical „Bootstrap“-PR (empfohlen)** | Eine Branch-Basis, die exakt dem Stand von **`fb903289`** (oder nach Rebase auf aktuellstem `origin&#47;main` aufgebaut) entspricht; **eine** Squash- oder Merge-Commit-PR. | Geringe Konfliktrisiken; klare Soll-Quelle. |
| **B. Serielle Merges aller 22** | nacheinander Merges | **Nicht** empfohlen: künstliche add/add, hoher Aufwand, kein echter kumulativer Graph. |
| **C. Cherry-picks** | einzeln Dateien aus älteren Branches | Nur sinnvoll für **Content**, der in `fb903289` fehlt (Audit nötig); alte 1-Datei-Contract-Branches sind fachlich oft durch **gebündelte** `decision_packet_v1` obsolet. |

**Kombination, die in der Praxis passt:** `fb903289` (oder daraus rebased) **als einzige** Quelle für `src&#47;trading&#47;master_v2&#47;` + `tests&#47;trading&#47;master_v2&#47;` + `scripts&#47;dev&#47;master_v2_dry_smoke_v1.py`; alte 21 Tipps bestenfalls **Referenz** (`git show branch:path`) statt weitere Merges.

## 3. Top 5 Konflikt- / Redundanzrisiken

1. **`src&#47;trading&#47;master_v2&#47;__init__.py`**: In jedem kumulativen Slice erweitert — bei mehrfachem **Merge** paralleler Tipps: hohe Wahrscheinlichkeit doppelter oder widersprüchlicher `__all__`‑Einträge.
2. **Gesamter Ordner `src&#47;trading&#47;master_v2&#47;*`:** Mehrere Tipps fügen **denselben Satz** Basis-Dateien (decision_packet, snapshot, …) **unabhängig** hinzu — **add/add** auf identischen Pfaden, nicht „Patch auf vorherigem Stand“ in Git-Abstammung.
3. **`tests&#47;trading&#47;master_v2&#47;*`:** Wiederholt in jedem Voll-Shop-Slice; gleiches Konfliktmuster, Metadaten-Only-Diffs erschweren 3-Wege-Merges.
4. **`src&#47;trading&#47;__init__.py` (falls vorhanden / Namespace):** Wenn in älteren Branches getoucht, zusätzliches Kollisionsfeld (hier: Contract-Tipp `4dd1` enthält minimales `trading`‑`__init__` — in gebündelter Form evtl. obsolet/anders). <!-- pt:ref-target-ignore -->
5. **Semantische Zwillings-Historie:** Inhaltlich identische Kette kann mit **unterschiedlichen Blob-IDs** in parallelen Commits vorkommen — manuelle Synthese „ein Soll-Tree“ ist klarer als viele Merges.

## 4. Gruppenbildung & Übernahmeart

### Gruppe G1 — Alte 16 „Contract-“Branches (4dd1 … cbb20162)
- **Ziel-Dateien:** pro Branch typisch 1–3 spezifische Dateien, z. B. `universe_selection_v1.py`, weitere Körner (nicht identisch benannt zum gebündelten Paket).
- **Merge-Reihenfolge:** an Git-Historie **nicht** gekoppelt; alle auf **dasselbe** `main`‑Vorfahren-Base.
- **Empfehlung:** **Nicht** nacheinander in `main` mergen. Stattdessen: **Referenz-Review** (existiert fachlich Einzigartiges, das in `decision_packet_v1` + Fixtures **nicht** abgebildet ist?). Standardfall: Inhalt ist im gebündelten V2-Baum **konsolidiert** → **kein** Cherry-Pick nötig.

### Gruppe G2 — „Kumulative“ Slices (8171, 61cd, c0fe, 7f7e, 10f4, fb903)
- **Tatsache:** Sibling-Commits, Merge-Basis jeweils `a80748b5` (bzw. aktuelles `main`‑Pendant).
- **Ziel-Dateien:** voll `src&#47;trading&#47;master_v2&#47;`; Tests; ab `7f7e` Adapter; ab `10f4` Debug-CLI; ab `fb903` + `scripts&#47;dev&#47;…dry_smoke…`. <!-- pt:ref-target-ignore -->
- **Empfehlung:** **Nur `fb903289`** (nach Rebase auf `origin&#47;main`) integrieren. Untereinander: **keine** Merges nötig — inhaltlich ist `10f4` ⊃ inhaltlich `8171`+Erweiterungen (für `src&#47;trading` geprüft: Delta `8171..10f4` = +5 geänderte/hinzugefügte Module unter `master_v2`); `fb903` = `10f4` + Smoke-Adapter. <!-- pt:ref-target-ignore -->

## 5. Branches besser als Referenz (nicht direkt in Folge mergen)

- Sämtliche **16** alten 1-Commit-Contract-Branches, sofern der gebündelte Baum fachlich vollständig.
- `feat&#47;master-v2-scenario-matrix-v1` … `feat&#47;master-v2-local-debug-cli-v1` (aufsteigend bis 10f4) — jeweils **oberhalb abgedeckt** von `fb903`, falls File-Set ⊆ `fb903` (für `src&#47;trading` verifiziert: `fb903` superset `8171` fürs Modul-Set + Scripts). <!-- pt:ref-target-ignore -->
- **Ausnahme:** Wenn in einem alten Körner-Commit noch **einzelne** inhaltliche Zeilen-Features fehlen, gezieltes **Cherry-Pick einzelner Datei-Blobs** oder manuell vergleichen — nicht serieller Merge des ganzen Branch.

## 6. Ein klarer nächster Konsolidierungsschritt (eine Strategie)

1. **`main` / `origin&#47;main` frisch** (einmal lokal, nicht Teil dieser read-only Doku: pull).
2. **Neue Integrations-Branch** z. B. `consolidation&#47;master-v2-into-main` von **`origin&#47;main`**.
3. Inhalt anbinden: **ausschließlich** den Arbeitsbaum des Tipps **`fb903289`**, ideal **per**:
   - `git checkout fb903289 -- src&#47;trading&#47;master_v2 tests&#47;trading&#47;master_v2 scripts&#47;dev&#47;master_v2_dry_smoke_v1.py` (nach genauer Pfad-Liste), **oder**
   - `git merge -s ours` eines leeren und dann Inhalt ersetzen — was im Team leichter ist: oft **eine** klare `git read-tree` / Checkout des relevanten Bäume.
4. Anschließend: **`uv run` Ruff/Tests** wie im letzten Commit der Slice; **eine** PR / ein **Squash**-Commit-Message, das die Tatsache „Konsolidierung aus mehreren parallelen M2-Branches, kanonische Quelle `fb903`“ dokumentiert.
5. Alte 22 **Feature-Branches** nach Merge: **schließen** / Tag als historisch, **keine** weiteren nachträglichen Merges derselben Dateien.

---

## 7. Cursor-Multi-Agent-Umsetzungsbrief (nächster praktischer Schritt)

**Ziel (ein Arbeitsgang):** `origin&#47;main` um **genau** den Master-V2-Kanon erweitern, der in **`feat&#47;master-v2-dry-smoke-adapter-v1` @ `fb903289`** sichtbar ist, ohne 21 weitere Merges.

**Constraints:** Keine Logik-Änderung; nur Konsolidierung/Import des Trees; Ruff+Pytest grün; ein Commit-PR; Dokumentation in PR-Body: *„Kanonische Quelle: fb903289; frühere parallele Branches 4dd1… cbb/8171/61cd/… dienen als Referenz, nicht seriell gemergt“*.

**Schritte für den Agenten:**
1. `git fetch origin && git checkout -b consolidation&#47;master-v2-into-main origin&#47;main`
2. Prüffliste Dateien: `git ls-tree -r --name-only fb903289` für `src&#47;trading&#47;master_v2&#47;`, `tests&#47;trading&#47;master_v2&#47;`, `scripts&#47;dev&#47;master_v2_dry_smoke_v1.py` (und ggf. weitere ausschließlich in `fb903` getrackte Pfade)
3. `git checkout fb903289 -- <diese Pfade>` (keine Blind-Copy des ganzen Repos)
4. Optional: Differenz-Review `git diff origin&#47;main --` auf Konflikte mit anderem `src&#47;trading` (falls in Zukunft doch was existiert) <!-- pt:ref-target-ignore -->
5. `uv run ruff check&#47;format …`, `uv run pytest tests&#47;trading&#47;master_v2&#47; -q` (bzw. breiter, wenn CI es verlangt)
6. Ein Commit, PR-Titel/Body wie oben, **fertig**.

---

*Erstellt: read-only; keine Repo-Mutation, keine Merges ausgeführt.*
