---
docs_token: DOCS_TOKEN_CURRENT_OPEN_SLOT_COST_RESERVE_RENEWAL_V1
authority: DEVELOPMENT_DELTA_ONLY
runtime_authorization_effect: NONE
---

# Abgerechnetes Funding und Erneuerung offener Kostenreserven

Ausgang ist der lokale Commit `3ef1d467b38b5841801098e98eb1241591632f35`.
Dieser Anschluss gehört ausschließlich zu BWP1. Die neue ausdrücklich gewählte
[Testpolicy V8](BOUNDED_MULTISLOT_TEST_ENTRY_BUDGET_V8.json) verwendet
`entry_budget_policy.v9`. Vorherige Policies und die operative Finanzkonfiguration
werden nicht umgestellt. Notional und native Positionsmenge werden nicht erhöht.

## Fachliche Quellen und kausale Kette

Die Obsidian-Fachhinweise S01/S11/S12, ACCOUNTING/BUDGET/TREASURY, die Ports
P08/P09/P11/P12 und die Trennung von Kapital, Accounting und Lernergebnis wurden
mit den folgenden Originalownern abgeglichen. Die S-Adressen sind analytische
Sichten und keine neuen Runtime-Layer. Ein Port beschreibt keine automatische
Zustellung und überträgt keine fremde Schreibautorität.

1. Die originale Reservation und ihre unveränderte Sizingbindung liefern Account,
   Slot, Instrument, native Menge und die bisher gehaltene Fundingperiode.
2. Der originale Accountingkernel führt signierte Zahlungen, Event-IDs, Währung,
   Instrument, Ereigniszeit und tatsächliche Reihenfolge. Der unveränderte
   Episodenadapter archiviert und verifiziert diese Rechnung einschließlich
   Openingfill und Restposition.
3. Der neue typisierte `OpenSlotCostRenewalContextV1` bindet eine explizite
   Zuordnung der Originalzahlungen zu den abgelösten Perioden, übergebene frische
   öffentliche Historien-GETs, den originalen verfügbaren Kapitaloutput und eine
   exakte vorherige Revision desselben Budgetstores.
4. Frische kontobezogene Gebühren, Instrumentmetadaten, ausführbare Schließtiefe,
   Mark, eigener FX-Bezug und nächste Fundinggrenzen bewerten die native
   Restmenge. LONG schließt über Bids/SELL, SHORT über Asks/BUY. Das bestehende
   Preismodell und die gegenwärtigen Ratengrenzen bleiben Planungsevidence.
5. Unter dem Lock des Originalbudgetowners werden die bisherigen Holds aller
   Slots gegen das frische Originalkapital und die verbleibende Testverlustzulage
   geprüft. Derselbe bestehende SQLite-Commit speichert Kapitalbezug, neue
   Close-/Fundingholds, Quellen und den Schutzbefund gemeinsam.
6. Budgetsumme, ursprünglicher Commitment-Readback, frühe Reservation einschließlich
   Replay und später Entryreader verbrauchen die tatsächlich erneuerten Holds.
   Der bestehende N1-/S7-Pfad verbraucht weiterhin nur seinen originalen
   slotbezogenen Safety-Auftrag. Ungeklärte gemeinsame Verpflichtungen sperren
   neue Entries; sie geben fremde Slots weder frei noch schließen sie diese.
7. Cold-Read rekonstruiert jede Erneuerung aus Accountingarchiv, vorheriger
   Originalrevision, Kapital- und Kostenquellen. Fehlende oder nur neu gehashte
   Summen reichen nicht. Admission erfordert anschließend die originale Recovery.

## Periodenabdeckung und Geldsemantik

Die am 9. November 2026 erneut gelesene
[OKX-Primärdokumentation](https://www.okx.com/docs-v5/en/#public-data-rest-api-get-funding-rate-history)
beschreibt `before` als neuer und `after` als älter als den angegebenen
Fundingzeitpunkt, jeweils exklusiv. Der Adapter verlangt explizite Range-GETs
von der bisher reservierten Periode bis vor die neue kommende Periode mit
`limit=400`. Volle Seiten verlangen eine weitere ältere Seite; erst eine
ausgeschöpfte Seite mit weniger als 400 Records beendet die Abdeckung.
Unvollständige, doppelte, falsch geordnete oder fremde Perioden bleiben gesperrt.
Die Historie enthält die tatsächliche öffentliche Rate; diese wird niemals in
eine angeblich beobachtete Accountzahlung umgerechnet. Eine feste
Achtstundenperiode wird nicht vorausgesetzt.

Für diesen begrenzten internen Accountingpfad gilt eine ausdrückliche einzelne
Originalbuchung je abzurechnendem Zeitpunkt. Die Zuordnung muss Event-ID,
signierten Originalbetrag, Währung, Instrument und Ereigniszeit exakt erhalten;
die Ereigniszeit muss dem belegten Fundingzeitpunkt entsprechen. Fehlende
Buchungen sind kein Nullbetrag. Ein ausdrücklich gebuchter Nullbetrag ist
zulässig. Zusätzliche unzugeordnete Zahlungen im Abrechnungsbereich sperren den
Übergang. Andere Buchungszeitkonventionen oder aufgeteilte Abrechnungen benötigen
einen weiteren Originalquellenvertrag und werden hier nicht still interpretiert.
Auch eine veränderte ursprüngliche Terminprognose ohne passenden
Abrechnungsbeleg erhält keine automatische Ablösung.

Gebuchte Zahlungen stecken bereits im ursprünglichen markbewerteten
Accounting-Nettoergebnis. Sie werden nicht nochmals als Verlust abgezogen.
Nach belegtem Übergang bleiben nur zukünftige Funding-/Closeverpflichtungen in
dieser Vorsorge. Das ursprüngliche Openingfee-Hold und Notional bleiben unter
ihren vorhandenen Releasebedingungen. Verlustzulage, verfügbare Margin und
Notionalobergrenze bleiben getrennte Geldgrößen. Die Testverlustzulage wird
weder bei Funding, Rotation, Tageswechsel noch Neustart automatisch aufgefüllt.

## Fehler, Wiederaufnahme und Grenzen

Fehlende Zuordnung, Daten oder frisches Kapital erhalten die bisherigen Holds.
Öffentliches `settled`, Zeitablauf und die Treasury-Kontorolle Funding ersetzen
keine Zahlung. Ist eine neue Periode bekannt, bleibt bei ungeklärter alter
Abrechnung auch deren zusätzliche Vorsorge in der konservativen Schutzrechnung.
Belegte Verlusterschöpfung und der bereits gebundene Close bleiben wirksam.
Belegte unzureichende Kapital- oder Verlustdeckung erreicht den vorhandenen
kontrollierten Exit des Zielslots. Das ist keine zusätzliche Prozentschwelle.

Eine gültige Neubewertung innerhalb derselben kommenden Periode kann deren
Kostenholds mit frischem Kapital ebenfalls erneuern. Andere Slots werden bei
jeder Transaktion erneut mitgerechnet. Exakte Decimal-Addition im neuen
Holdpfad verhindert unterschiedliche Summen allein durch Additionsreihenfolge.
Eine inzwischen fortgeschrittene Budgetrevision darf nicht überschrieben werden.
Nach unklarer Commitbestätigung wird der Writer gesperrt; erst Cold-Read zeigt,
ob die alte oder neue Transaktion dauerhaft vorliegt. Reines Replay schreibt
keine zweite Erneuerung. Ein begonnener Close wird durch billigere neue Quellen
nicht aufgehoben.

Das historische N1-Beobachtungslabel `OBSERVED_PROTECTION_ONLY` allein belegt
keine Erneuerung. Maßgeblich sind der rekonstruierbare Erneuerungsreceipt und
der gemeinsam gespeicherte tatsächliche Holdstand beim Budgetowner.

Die [verbundenen Prüfungen](../../../tests/ops/test_open_slot_cost_reserve_renewal_v1.py)
verwenden ursprüngliche N1-/S7-, Accounting-, Budget- und Recoveryconsumer.
Der [Prüfbeleg](../evidence/CURRENT_OPEN_SLOT_COST_RESERVE_RENEWAL_V1_2026-11-09.json)
bindet den endgültig geprüften Quellstand und den genauen Umfang.

Dies ist ein expliziter interner Simulationsanschluss, keine authentifizierte
private Venue-Abrechnung und kein neuer Collector oder Netzwerkport. Frische
Kosten sind keine garantierten zukünftigen Fills oder Kostenobergrenzen.
Die bisherige Startup-, Positions-, Kapital- und Cursor-Recovery sowie die vier
zugelassenen Funding-Episode-Adapter bleiben erhalten. Physischer Stromausfall,
unbegrenzter autonomer Dauerbetrieb, vollständige Margin-/Liquidationszulassung
und der gesamte Wirtschaftsrahmen sind damit nicht abgenommen. BWP1 bleibt
IN_BEARBEITUNG; BWP2 bis BWP5 werden nicht erweitert. Freeze-Tags bleiben erhalten.

Quellen: [Originalbudgetowner](../../../src/ops/portfolio_capital_reservation_budget_v1/contract_v1.py),
[Erneuerungsadapter](../../../src/ops/portfolio_capital_reservation_budget_v1/open_slot_cost_renewal_v1.py),
[ursprüngliche Schutzrechnung](CURRENT_OPEN_SLOT_CURRENT_COST_PROTECTION_V1.md),
[Funding-Episodenvertrag](CURRENT_ORDERED_FUNDING_EPISODE_DEVELOPMENT_ADMISSION_V1.md).
