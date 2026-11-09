---
docs_token: DOCS_TOKEN_CURRENT_SYSTEM_FIVE_BOUNDED_WORK_PACKAGES_V1
authority: NONE
runtime_authorization_effect: NONE
---

# Fünf begrenzte Arbeitspakete zum heutigen System

Auftrag vom 9. November 2026. Ausgangsrevision:
`304719c94030ff9aacdf2571e2ae56533f9e6a25` (PR 7205).
Dies ist ein Arbeits- und Abnahmeplan, kein neuer Runtimeowner.
Die Pakete werden zusammenhängend abgeschlossen; Unterpunkte sind keine
eigenständigen Fertigmeldungen oder automatisch neue PRs.

## Gemeinsame Abschlussregel

Ein Paket ist erst abgeschlossen, wenn seine fachlichen Definitionen,
Originalquellen, Transformationen, Persistenz-/Übergabestellen und tatsächlichen
Consumer am endgültigen Quellstand gemeinsam geprüft sind. Dazu gehören ein
positiver verbundener Ablauf, die relevanten negativen Fälle und die erforderliche
Wiederaufnahme. Ein Dokument, ein PASS-Label, eine Schnittstelle mit synthetischen
Zahlen oder allein eine technisch sichere Sperre erfüllt diese Regel nicht.

Jede Abnahmeanforderung erhält einen konkreten Nachweis. Fehlende fachliche
Entscheidungen und Quellen bleiben offen. Sie werden weder mit frei gewählten
Zahlen geschlossen noch still in ein späteres Paket verschoben. Neue Befunde
werden einem Paket zugeordnet; eine notwendige Umfangsänderung wird ausdrücklich
festgehalten. Paket 5 integriert die abgeschlossenen Einzelpakete und ersetzt
deren fehlende Fachabnahme nicht.

Die Testphase bleibt bei 25 USDC Notionalreservation je Slot, höchstens 125 USDC
bei fünf Slots und zusätzlicher tatsächlicher Kapitalzulassung. Ihr Ende
entscheidet Frank ausdrücklich. Zusätzlich gilt nur während dieser ausdrücklich
gewählten Testphase ein Verlustbudget von 25 USDC je Slot. Nach dessen Verbrauch
gibt es für diesen Slot keine neuen Entries und keine automatische Auffüllung.
Ein Instrumentwechsel, Neustart oder Tageswechsel beginnt kein neues Budget.
Diese Testregel wird nicht zur allgemeinen Regel des späteren kapitalabhängigen
Betriebs. Dessen Freigabe und finanzielle Policy werden getrennt festgelegt.
Entwicklung und Prüfung erzeugen keine
Live-/Testnet-, Order- oder Kapitalbewegungsfreigabe. Freeze-Tags bleiben erhalten.

## BWP 1 — Wirtschaftliche Wahrheit und Risiko

Status: IN_BEARBEITUNG. Kein Abschlussnachweis vorhanden.

Ziel: Die Handelslogik arbeitet innerhalb eines fachlich definierten,
quellengebundenen wirtschaftlichen und finanziellen Rahmens. Testkonstanten
werden nicht als belegte aktuelle Wirtschaftsinputs ausgegeben.

Umfang und Abnahmeanforderungen:

1. **BWP1-D1: Rolle festlegen.** Vorab geprüfter Handelsrahmen und etwaiger
   Gewinnforecast vor jedem Entry werden fachlich getrennt entschieden.
   24/7-Betrieb, Slot-/Instrumentepisode, einzelne Position und Fundingereignis
   sind getrennte Zeitbezüge. Rankingfrist und Scopeabstand werden nicht zum
   Forecast-, Funding- oder Risikohorizont umbenannt.
2. **BWP1-S1: Quellen und Semantik.** Für jede tatsächlich benötigte Größe sind
   Originalproducer, Bedeutung, Einheit, Währung, Instrument, Seite, Menge,
   Ereignis-/Kenntniszeit, Horizont und Zuständigkeit belegt. Dazu gehören Kosten,
   gegebenenfalls erwarteter Ertrag, Survivalmetriken und ihre Grenzen sowie
   Kapital-/Margin-/Verlustbudgets. Nicht benötigte Größen brauchen eine
   ausdrückliche fachliche Entscheidung; ein fehlender Wert wird nicht zu null.
3. **BWP1-A1: Arithmetik und Pfad.** Gebühren, Slippage, Funding, PnL,
   Kontraktmultiplikator, native Menge, Rundung und Kapitalbelastung stimmen
   mit den zuständigen Originalownern überein. LONG/SHORT, Verlustreihenfolge,
   wiederholte Wechsel und mehrere gleichzeitig belegte Slots sind abgedeckt.
   Eine gemessene Häufigkeit wird nicht zur behaupteten Erfolgswahrscheinlichkeit.
4. **BWP1-C1: Tatsächlicher Verbrauch.** Die zugelassenen Größen erreichen
   die ursprüngliche Entscheidung beziehungsweise finanzielle Mengenadmission.
   Änderung eines relevanten Inputs bewirkt die definierte Reaktion am echten
   Consumer; der Zustand erhält seine Quellen-/Policybindung bis zur Übergabe.
5. **BWP1-N1: Negative Wirkung.** Fehlende, alte, zukünftige, falsche,
   nichtendliche oder widersprüchliche Inputs und unzureichende Mittel sperren
   den betroffenen neuen Entry. Offene Positionen, risikoreduzierende Ausgänge,
   Originalholds und unbekannte Ausführung bleiben in ihrer Zuständigkeit.
6. **BWP1-R1: Wiederaufnahme und gemeinsame Prüfung.** Neustart und erneutes
   Lesen prüfen Quellen, Policy und vorhandene Verpflichtungen erneut.
   Ein Altplan oder früherer positiver Befund ersetzt keine aktuelle Zulassung.
   Verbundene positive und negative Prüfungen benutzen den endgültigen Quellstand.

Franks ausdrückliche Erhaltungsbedingung vom 9. November: Der vorhandene
Wiederanlauf mit gespeicherten Slot-/Instrumentbindungen, Positions-/Pending-
Abgleich und Kapitalverpflichtungen wird nicht durch Ranking oder eine neue
wirtschaftliche Prüfung ersetzt. Recovery liest die ursprünglichen Identitäten;
sie führt weder eine Neuauswahl noch eine automatische Holdfreigabe aus.
Eine neue Rankingmessung erreicht einen Instrumentwechsel nur über die
bestehenden getrennten Auswahl-, Flat- und Reconciliationbedingungen.

Aktueller Befund: Der native integrierte Replaybuilder setzt Kosten, Gross-Edge,
Vollständigkeit und vier Ratios fest. Der ursprüngliche Sizer und Budgetowner
haben echte angeschlossene Consumer, während der 29P-Contextbuilder Risiko- und
Tagesverlustdimensionen zunächst aus derselben Kapitalgröße setzt. Daraus folgt
kein gemessener Tagesverlustvertrag. Die vorhandene Shadow-Pfadquote ist
ausdrücklich vorläufig und kein positiver nativer Survivalproducer.

Fachliche Entscheidung BWP1-D1: Frank hat am 9. November den vorab geprüften
Handelsrahmen gewählt, ohne zusätzlichen Gewinnforecast als Pflichtfilter je
Entry. Die Gegenprüfung zur Instrumentrotation gehört ausdrücklich dazu:
Volatilität und Amplitude bestimmen die relative Rangfolge; die nativen festen
Gewinn-/Survivalinputs werden dort nicht konsumiert. Relativ bester Kandidat
und absolute Handelbarkeit gegenüber tatsächlichen Kosten bleiben getrennt.
Ein insgesamt bewegungsarmes Universum darf nicht allein wegen seiner weiterhin
vorhandenen relativen Rangfolge als kostentragfähig behauptet werden.

Die weiteren Anforderungen bleiben bis zum passenden verbundenen Nachweis offen.
Ein ausgeschriebener Vertrag allein schließt dieses Paket nicht.

Weitere ausdrückliche Präzisierung vom 9. November: Ein gewöhnlicher
Instrumentwechsel wird als einzelner fester Vorgang mit Slot, bisherigem
Instrument und Ersatzkandidat geführt. Die neu gewählte Wartefrist beträgt
1.800 Sekunden ab Vormerkung. Währenddessen wird genau dieses Paar erneut
verglichen; andere Kandidaten oder Rangänderungen anderer Slots verschieben
die Zuordnung nicht. Erholung hebt die Vormerkung auf. Anschließend bleiben
ursprünglicher Close-/Flat-/Kapitalpfad und die eigene GGE-/Dynamic-Scope-/
Double-Play-Kette samt zweifacher Richtungsbestätigung erforderlich. Die
[Rotationsfortschreibung](CURRENT_RESERVED_SLOT_ROTATION_V1.md) beschreibt den
zu prüfenden Anschluss. Dies ist weder eine maximale Positionsdauer noch ein
Funding- oder Gewinnforecasthorizont.

Entwicklungsfortschritt innerhalb dieses Pakets: Die Gegenprobe zum Stillstand
verbindet Original-Merkmalsrechnung, Cap22, Membershiprotation, Persistenz und
Cold-Read. Der dabei reproduzierte Default-ID-Konflikt bei neuen Merkmalen und
gleichem Universum wird am ursprünglichen Rankingproducer korrigiert. Eine
Neuberechnung derselben Quellen zählt weiterhin nicht als neue Beobachtung.
Die [Semantikprüfung](CURRENT_CONTINUOUS_DOUBLE_PLAY_ECONOMIC_SEMANTICS_V1.md)
hält Quoten, relative Rotation und absolute Kostenfrage getrennt.

Die bestehende simulierte Accountinghistorie wird um explizit geordnete,
beobachtete Fundingzahlungen bis zu Episode, Exit und Readback verbunden.
Funding ist dabei ein signierter Geldbetrag mit Ereigniszeit, kein Forecast
oder Prozentsatz. Ein Funding-only-Fortschritt benötigt keinen erfundenen Fill.
Diese begrenzten Änderungen schließen weder BWP1-S1/C1/R1 insgesamt noch die
produktive Kosten-/Margin-/Verlustbudgetherleitung ab. Der geprüfte Zwischenstand
ist in `d855ca546` committet. BWP1 bleibt offen; noch kein Paket-PR oder Merge.

Frank hat die [genau vier Fundingadapter betreffende Fortschreibung](CURRENT_ORDERED_FUNDING_EPISODE_DEVELOPMENT_ADMISSION_V1.md)
gesondert freigegeben, ausdrücklich mit Erhalt des Wiederanlaufs. Nur die
konkret geprüften Nachfolgedigests werden als vollständiges Entwicklungsbundle
zugelassen; der ursprüngliche Freeze und fremde Policyquellen bleiben geschützt.

Weitere Präzisierungen vom 9. November: Das Aufstocken einer noch offenen
Position wird in diesem Paket nicht eingeführt. Die 25 USDC sind eine obere
Grenze, keine Pflicht, bei jedem Entry die volle Summe einzusetzen. Der originale
Sizer kann aus tatsächlichen Kapital-/Risiko-/Mengenbedingungen kleinere Mengen
zulassen; eine frei gewählte Anfangstranche oder neue Ratchet-Prozentzahl wird
nicht ergänzt.

Die [Fortschreibung des Testbudgetanschlusses](BOUNDED_MULTISLOT_ENTRY_BUDGET_V1.md)
bindet die Verlustregel ausdrücklich an eine neue Testpolicy. Der Originalowner
behält die Geldquellen des Sizings und liest für einen abgeschlossenen
simulierten Zyklus die ursprünglichen Fill-/Fundingquellen erneut. Fehlende
wirtschaftliche Closequellen sperren die erneute finanzielle Entryzulassung,
auch wenn frisches Kontokapital zugelassen ist. Dies ersetzt weder die noch
offene Gebühren-/Slippage-/Fundingvorsorge vor einem Entry noch die vollständige
Margin- und Verlustfolgenabnahme von BWP1.

Der Zwischenstand `6459cc6b0` enthält die testbezogene Verlustfortschreibung und
die ursprünglichen Sizing-Geldquellen. Darauf folgt der in der
[Budgetfortschreibung](BOUNDED_MULTISLOT_ENTRY_BUDGET_V1.md) beschriebene
Source-Producer-Consumer-Anschluss für beobachtete Öffnungsgebühren und
Bookausführungskosten. Diese Beträge erreichen die unveränderte kanonische
Menge, die atomare Reservation, ihren dauerhaften Ausführungslink und den
späteren finanziellen Consumer. Zukünftige Closekosten, Fundingvorsorge und
vollständige Margin-/Liquidationsdeckung bleiben getrennt offen. Daraus wird
kein Paketabschluss und keine neue positive native Survivalquote abgeleitet.

Weitere Präzisierung: OKX-Demohandel ist für die Abnahme ausgeschlossen, da er
laut Frank nicht alle benötigten Instrumente abdeckt. Paper und Shadow müssen
das tatsächlich benötigte Originaluniversum mit nachgewiesener Datenabdeckung
prüfen. Frank verlangt außerdem die vorzeitige Berücksichtigung von
Schließkosten und bei tatsächlich verbrauchter Testverlustzulage den
kontrollierten Close der betroffenen offenen Position. Die
[Kosten-/Paper-/Shadow-Fortschreibung](CURRENT_BWP1_COST_PROVISION_AND_PAPER_SHADOW_V1.md)
trennt den vorhandenen Kostenanschluss von diesem noch nachzuweisenden
laufenden Positionsschutz und der offenen Funding-/Marginzulassung.

Der nachfolgende Entryanschluss bindet eine getrennte aktuelle Fundingquelle
an dieselbe ursprüngliche Mengen-/Kostenrechnung und atomare Reservation.
Die Vorsorge bis zur nächsten instrumentbezogenen Abrechnung wird im Readback,
der späten Budgetzulassung und beim gezielten Slotclose erhalten. Die laufende
Erneuerung offener Positionen und der kontrollierte Close bei tatsächlichem
Verbrauch bleiben davon getrennte offene Anforderungen. Die
[Paper-/Shadow-Semantikprüfung](CURRENT_PAPER_SHADOW_DATA_ROUTING_SEMANTICS_V1.md)
verwendet auf Franks Hinweis Obsidian als datierte Wissensquelle und hält
unterschiedliche Datenströme sowie öffentliche Raten und private Zahlungen
ausdrücklich auseinander. Dies ist kein Paketabschluss.

Der nächste begrenzte Anschluss ist der
[Verlustschutz offener Testslotpositionen](CURRENT_OPEN_TEST_SLOT_LOSS_PROTECTION_V1.md).
Die ursprüngliche simulierte Accountingepisode wird mit eigenem frischen Mark-
und gegebenenfalls FX-Bezug bewertet. Ein dauerhaft gespeicherter originaler
Budgetbefund erreicht den bestehenden Safety-Exit des genauen Zielslots, ohne
globale Killzustände, native Handelsformeln, fremde Holds oder die vorhandene
Startup-/Recoverykette zu ersetzen. S01, S11 und S12 aus den datierten Obsidian-
Wissensquellen wurden an den tatsächlichen Ownereingängen abgeglichen.
Die laufende Kosten-/Fundingvorsorgeerneuerung, vollständige Margin-/Liquidations-
zulassung und der gemeinsame Wirtschaftsrahmen bleiben offen.

Quellen: [fortgesetzter Handelskreis](CURRENT_CONTINUOUS_DOUBLE_PLAY_ECONOMIC_SEMANTICS_V1.md),
[heutige Risiko-/Mengenconsumer](CURRENT_N1_RISK_AND_QUANTITY_CONSUMPTION_V1.md),
[numerische Grenze](CURRENT_SURVIVAL_NUMERIC_ADMISSION_V1.md),
[native Survivalinputs](../../../src/trading/master_v2/integrated_offline_trading_logic_replay_v1.py),
[ursprüngliche Survivalrechnung](../../../src/trading/master_v2/survival_assessment_v1.py),
[ursprüngliche Kapitalcontext-Bindung](../../../src/ops/full_core_live_path_composition_root_v1/current_productive_mv2_capital_context_rebind_v1.py).

## BWP 2 — Senderecht, ungewisser Ausgang und Wiederaufnahme

Status: GEPLANT. Voraussetzung: fachliche Zulassung aus BWP 1.

Ziel: Nur der eindeutig gebundene und heute zugelassene Originalplan kann genau
einmal die gesondert erlaubte Versandgrenze erreichen.

Abschluss verlangt ein unabhängiges, exakt gebundenes Sendemandat; eindeutige
Owner-/Root-/Accountherkunft; nachvollziehbaren Permitverbrauch und Submitlink;
konservative Behandlung von MAY_HAVE_SENT/UNKNOWN; Originalreconciliation bis
zum bestätigten Ergebnis; und Wiederaufnahme ohne doppelten Versand oder
vorzeitige Holdfreigabe. Abbrüche vor, an und nach der Transportgrenze sind
gemeinsam mit den tatsächlichen frühen und späten Consumern geprüft.

Keine eigene Neuerfindung der Wirtschaftsrechnung aus BWP 1 und keine
Kontocustody-Vollständigkeitsbehauptung ohne BWP 3.

## BWP 3 — Vollständige Kontocustody und gemeinsame Ressourcen

Status: GEPLANT. Schnittstellen zu BWP 1 und BWP 2.

Ziel: Bekannte und fremde Positionen, offene Orders, unterstützte Algo-/Produkt-
quellen und deren Verpflichtungen werden vollständig im erklärten Accountscope
erfasst. Nicht unterstützte oder unklare Bestände geben keine Mittel frei.

Abschluss verlangt ein explizites unterstütztes Kontoinventar; Scope-/Seiten-/
Mengenzuordnung und Pendingabgleich an den Originalownern; sichere Behandlung
anderer Bots/Produkte; geteilte Session-/Request-/Concurrencygrenzen; und
verbundene Tests für Teilausfälle, Pagination, fehlende Quellen und Neustart.
Die tatsächlichen Kapital- und Versandconsumer berücksichtigen diesen Befund.

## BWP 4 — Verbundener autonomer Hostablauf

Status: GEPLANT. Voraussetzung: BWP 1 bis BWP 3 an ihren Übergaben abgenommen.

Ziel: Auswahl, Datenaufnahme, Coreentscheidung, finanzielle Admission,
gesondert erlaubter Versand, bestätigter Fill und fortgesetzter Slotkreis
werden durch den tatsächlichen Host mit eigener Persistenz fortgesetzt.

Abschluss verlangt KEEP/REPLACE und fortgesetzte LONG-/SHORT-Zyklen für alle
freigegebenen Slots; unveränderte Zuständigkeit anderer offener Slots; tatsächliche
Übergaben aus BWP 1 bis BWP 3; und getestete Wiederanläufe nach Prozess-/Hostfehlern.
Ein begrenzter simulierter Vorläufernachweis wird nicht als unbegrenzter
produktiver Dauerbetrieb ausgegeben. Der Umfang eines späteren Betriebsversuchs
und seine Freigabe bleiben ausdrücklich benannt.

## BWP 5 — Gemeinsame Endsystemabnahme

Status: GEPLANT. Voraussetzung: BWP 1 bis BWP 4 geschlossen.

Ziel: Ein einziger benannter Endstand trägt die vollständige Abnahmematrix.

Abschluss verlangt den gemeinsamen Quellen-/Policy-/Konfigurationsstand,
erfolgreiche relevante bestehende Verträge und verbundene Integrations-/
Ausfallprüfungen einschließlich der vereinbarten physischen Ausfallfälle.
Entscheidungsqualität, Ausführung, Sicherheit, wirtschaftliches Ergebnis und
Lern-/Optimierungswirkung werden getrennt nachgewiesen. Offene Collector-,
Account-, Daten- oder Recoveryverträge werden nicht durch neue Dokumenttests
ersetzt. Zulässige Restgrenzen bedürfen einer ausdrücklichen Entscheidung.

PR-/Merge- und Obsidian-Nachführung binden jeweils den tatsächlich geprüften
Stand. Eine eigene Betriebsfreigabe folgt auch aus diesem Abschlussbericht nicht.
