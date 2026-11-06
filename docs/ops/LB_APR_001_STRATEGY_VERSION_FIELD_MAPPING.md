# LB-APR-001 — Feld „Strategy Version“ (extern) ↔ interne Bezeichner

**Status:** Entwurf — **Draft-/Approval-Hilfe** für konsistente Befüllung externer Formulare.  
**Geltung:** Dieses Dokument **ändert keine** technische Semantik im Code, **keinen** technischen Unlock und **keine** Live-Freigabe. Es ordnet **Sprache** und **Kontexte** fürs Inventar und für Tickets ein.

---

## Zweck

- Ein **kanonischer, minimaler** Bezugsrahmen, damit das externe Pflichtfeld **„Strategy Version“** (englische Formularbezeichnung) **nicht** willkürlich mit internen Laufzeit-IDs, Git-Labels oder KI-/Model-Registry-Einträgen verwechselt wird.
- Orientierung für **approval-taugliche** Freitexte: welche **Kombination** aus stabilem Strategiebezeichner und **nachweisbarer** Code-/Artefakt-Referenz die stärkste Lesart bildet — **ohne** behauptete 1:1-Zwangsumsetzung in Produktcode.

## Nicht-Zweck

- **Kein** Ersatz für LB-APR-001-Sign-off, Owner-/Risk-Entscheid oder externes Ticket.
- **Keine** neue Aussage darüber, welche Strategie oder welche Version „freigegeben“ ist.
- **Kein** Ersatz für eine spätere formale „Trading-Strategie-Freigabeversion“-Policy (falls das Unternehmen eine eigene Nummerierung einführt).

---

## Externes Feld „Strategy Version“

- In **englischsprachigen** Freigabe-/GRC-Formularen taucht häufig **„Strategy Version“** (oder ähnlich) als Pflichtfeld auf.
- Solange **keine** vom Antragsteller und Risk gemeinsam fixierte **externe** Versionsnummer existiert, bleibt der Wert in Inventaren **TBD** — das ist **korrekt**, bis eine **kanonische externe Lesart** vereinbart ist.

**Lesart dieses Dokuments:** „Strategy Version“ bezieht sich auf die **beantragte und dokumentierte Trading-Strategie-Freigabe** im Sinne des Antrags — **nicht** auf beliebige technische IDs aus anderen Registries.

---

## Stärkste aktuelle Kandidatenstruktur (ohne neue Approval-Behauptung)

Aus **read-only** Inventar- und Abgleichspraxis (ohne Bindung an einen einzelnen Snapshot-Pfad):

1. **Primärbezeichner:** ein stabiler, in Konfiguration/Registry nachweisbarer Schlüssel — im Abgleich typischerweise **`strategy_registry_key`** (oder gleichwertig benannter Registry-Eintrag zur Strategie).
2. **Ergänzend (Pflicht zur Nachvollziehbarkeit):** mindestens **eine** der folgenden, explizit im Antrag/Ticket genannten Referenzen:
   - **Git-Revision** (z. B. Commit-SHA des freigegebenen Repo-Stands), und/oder
   - **Artefakt-Referenz** (z. B. Build-/Release-Label oder nachvollziehbares Dokument/Anhang, wie im Formular verlangt).

Damit bleibt die externe Zeile **überprüfbar** und von bloßen Laufzeit-Strings unterscheidbar.

---

## Verhältnis zu internen Begriffen (Überblick)

| Begriff | Rolle (kurz) | Verhältnis zu „Strategy Version“ (extern) |
|--------|--------------|-------------------------------------------|
| **`strategy_registry_key`** (o. ä.) | Stabiler Schlüssel der Strategie in der Strategie-Registry/Konfiguration | **Stärkster Kandidat** für den **Strategie**-Teil einer Freigabezeile — typischerweise **gepaart** mit Git-Revision und/oder Artefakt-Referenz. |
| **`active_strategy_id`** | Laufzeit: welche Strategie-ID aktiv geschaltet ist | **Konfigurations-/Laufzeitbezeichner**, **kein** approval-ready externes Versionslabel **allein**; Kombinationen wie `active_strategy_id@<git-sha>` sind **keine** saubere, alleinstehende **externe Freigabeversion**. |
| **Git-Revision** | Fixierter Repo-Stand | **Nachweis** für „welcher Code-Stand“ — **kein** Ersatz für eine semantische „Strategie-Version“ ohne klaren Strategiebezug im Antrag. |
| **Artefakt-Referenz** | Build-/Dokument-/Release-Pointer | **Nachweis** parallel zum Schlüssel — wie im jeweiligen Formular gefordert. |
| **KI-/Model-Registry-IDs** | Andere Domäne (Modell-/Inference-Lifecycle) | **Nicht** dasselbe wie **Trading-Strategie-Freigabeversionen** — **nicht** 1:1 ins Feld „Strategy Version“ übernehmen. |

---

## Was heute klar verwendbar ist

- **TBD** im externen Feld, solange keine vereinbarte externe Versionsform existiert — **absichtlich korrekt**.
- Sobald Antrag und Referenzen stehen: **benannter Registry-/Strategie-Schlüssel** **plus** **Git-Revision und/oder Artefakt-Referenz** als **strukturierte Freitext-Lesart** im Ticket — **ohne** implizite Live-Freigabe.

---

## Was bewusst nicht als externe Freigabeversion verwendet werden soll

- **`active_strategy_id@<git-sha>`** (oder ähnliche reine technische Zusammensetzungen) **allein** als „die“ Strategy Version — **zu wenig** semantisch für GRC, **kein** approval-ready Label ohne weitere Antragskontexte.
- **KI-/Model-Registry- oder Inference-IDs** — **falsche Ebene** (Modell-Lifecycle ≠ Trading-Strategie-Freigabe im LB-APR-Sinne).
- **Beliebige interne Kurzstrings** ohne Bezug zu Registry + nachweisbarem Stand — vermeiden; bei Unklarheit **TBD** oder explizite Klärung mit Owner/Risk.

---

## Querverweise

- [`LB_APR_001_EXTERNAL_APPROVAL_ARTIFACT_TEMPLATE.md`](templates/LB_APR_001_EXTERNAL_APPROVAL_ARTIFACT_TEMPLATE.md)
- [`DOCS_TRUTH_MAP.md`](registry/DOCS_TRUTH_MAP.md) — Auffindbarkeit LB-APR-001  
- Siehe auch: [`LB_APR_001_ACCOUNT_TYPE_FIELD_MAPPING.md`](LB_APR_001_ACCOUNT_TYPE_FIELD_MAPPING.md) (analoges Muster für ein anderes externes Pflichtfeld)
