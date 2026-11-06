# LB-APR-001 — Feld „Account Type“ (extern) ↔ interne Begriffe

**Status:** Entwurf — **Draft-/Approval-Hilfe** für konsistente Befüllung externer Formulare.  
**Geltung:** Dieses Dokument **ändert keine** technische Semantik im Code, **keinen** technischen Unlock und **keine** Live-Freigabe. Es ordnet **Sprache** und **Kontexte** fürs Inventar und für Tickets ein.

---

## Zweck

- Ein **kanonischer, minimale** Bezugsrahmen, damit das externe Pflichtfeld **„Account Type“** (englische Formularbezeichnung) **nicht** willkürlich mit internen Laufzeitbegriffen verwechselt wird.
- Klarstellung, welche internen Begriffe **parallel** existieren (Manifest, Runbooks, Execution-Modi) — **ohne** behauptete 1:1-Übersetzung in Produktcode.

## Nicht-Zweck

- **Kein** Ersatz für LB-APR-001-Sign-off, Owner-/Risk-Entscheid oder externes Ticket.
- **Keine** neue Aussage darüber, welche Konten oder Modi „freigegeben“ sind.
- **Keine** Zuordnung zu Secrets, API-Keys oder konkreten Exchange-API-Feldern (bleibt außerhalb dieser Scheibe).

---

## Externes Feld „Account Type“

- In **englischsprachigen** Freigabe-/GRC-Formularen taucht häufig **„Account Type“** als Pflichtfeld auf.
- In der **deutschsprachigen** LB-APR-001-Arbeitsvorlage entspricht dem inhaltlich der Eintrag **„Kontotyp“** (ein Wert, z. B. Spot vs. Margin/Futures) im Scope-Abschnitt — siehe [`LB_APR_001_EXTERNAL_APPROVAL_ARTIFACT_TEMPLATE.md`](templates/LB_APR_001_EXTERNAL_APPROVAL_ARTIFACT_TEMPLATE.md) § 3 und die Manifest-Tabelle in [`CANARY_LIVE_ENTRY_CRITERIA.md`](runbooks/CANARY_LIVE_ENTRY_CRITERIA.md) (Spalte „Kontotyp“).

**Lesart:** „Account Type“ / „Kontotyp“ bezieht sich hier auf die **vom Exchange/Produkt definierte Art des Handelskontos** (z. B. Spot), **nicht** auf interne Peak_Trade-Runner- oder Pipeline-Modus-Strings.

---

## Interne Begriffe / Kontexte (Überblick)

Die folgenden Begriffe beschreiben **unterschiedliche Ebenen** — sie sind **nicht** synonym mit „Account Type“:

| Kontext | Typische Bedeutung (kurz) |
|--------|---------------------------|
| **Execution-/Pipeline-Modus** (z. B. paper, shadow) | Simulierte oder nicht-outbound Ausführung; siehe z. B. Übersichten in [`PHASE_24_SHADOW_EXECUTION.md`](../PHASE_24_SHADOW_EXECUTION.md). |
| **Umgebung / Phase** (z. B. Research, Canary Live, NO-LIVE-Default) | Governance- und Phasenbegriffe im Runbook [`CANARY_LIVE_ENTRY_CRITERIA.md`](runbooks/CANARY_LIVE_ENTRY_CRITERIA.md). |
| **Manifest-Feld „Umgebung / Scope“** | Benannter Freigabe-Scope (z. B. Canary vs. anderer exakt benannter Scope) im LB-APR-001-Template — **parallel** zu Exchange/Kontotyp/Symbol, nicht Ersatz für „Kontotyp“. |

---

## Was heute klar zuordenbar ist

- **„Account Type“ / „Kontotyp“** im Sinne von LB-APR-001 ↔ **ein** vom Antrag klar benannter **Exchange-Produkt-/Kontotyp** (wie im Freigabe-Manifest und in der Vorlage gefordert).
- **Canary** ist im Freigabe-Template ein Eintrag unter **„Umgebung / Scope“** (siehe LB-APR-001 § 3) — das ist eine **Freigabe-Kategorie**, **kein** Ersatzwert für „Account Type“ und **kein** interner Modus-String.

---

## Was bewusst nicht 1:1 gemappt werden darf

- **Interne Modus-Strings** (z. B. `paper`, `shadow`) **nicht** als Wert in ein externes **„Account Type“**-Feld schreiben — falsche Ebene (Produktkonto vs. Laufzeitmodus).
- **„Canary“** **nicht** als Synonym für einen brokerseitigen Kontotyp verwenden; Canary bezeichnet hier die **beantragte Freigabe-Umgebung**, nicht die **Kontenart** beim Anbieter.
- **Keine** stillschweigende Gleichsetzung von **Testnet/Spot/Subaccount**-Labels aus Inventaren mit **internen** Gate-Namen — bei Unklarheit bleibt der externe Wert **TBD** bis zur Klärung durch Owner/Risk mit Bezug auf das konkrete Formular.

---

## Querverweise

- [`LB_APR_001_EXTERNAL_APPROVAL_ARTIFACT_TEMPLATE.md`](templates/LB_APR_001_EXTERNAL_APPROVAL_ARTIFACT_TEMPLATE.md)
- [`CANARY_LIVE_ENTRY_CRITERIA.md`](runbooks/CANARY_LIVE_ENTRY_CRITERIA.md)
- [`DOCS_TRUTH_MAP.md`](registry/DOCS_TRUTH_MAP.md) — Auffindbarkeit LB-APR-001
