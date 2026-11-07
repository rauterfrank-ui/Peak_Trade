---
docs_token: DOCS_TOKEN_SHARED_GET_RESOURCE_ENVELOPE_2026_11_07
authority: NONE
runtime_authorization_effect: NONE
---

# Geteiltes GET-Budget: tatsächliche Poll- und Pretradekosten

Basis ist 2ad95be4a8382d6d75a9855e124feb9e6b4f64fe nach PR 7186. Der
[JSON-Beleg](SHARED_GET_RESOURCE_ENVELOPE_2026_11_07.json) bindet Quellen,
ursprüngliche Gegenprobe, Testauswahl und genaue Grenzen. Dies setzt den
[Kapital-/Aufnahmefrischebeleg](CAPITAL_DECISION_ACQUISITION_FRESHNESS_2026_11_07.md)
mit einem getrennten Ressourcenvertrag fort.

## Ursprung und tatsächlicher Consumer

[PR 7004](https://github.com/rauterfrank-ui/Peak_Trade/pull/7004), Commit
59e9138b90e7e2c1073e7cf2b543422d0ecf783f vom 02.10.2026, berechnet den
Transportdeckel für zwei dynamische GETs pro S6-Poll: Candle und Mark.
Der damalige Index-GET in Commit 1a7235f20515aaa54b9dcb77ff0bc0f42e2df1a2
benutzt den allgemeinen Snapshotcache. Die ursprüngliche Budgetdatei ist
bytegleich mit der Budgetdatei unserer Basisrevision.

Der heutige Originalpoller fordert bei fehlendem idxPx dagegen einen dynamischen
Index-GET bei jedem Poll an. Damit kostet ein Poll zwei oder drei Requests.
Die Herkunft dieser zusätzlichen Frischeänderung innerhalb des späteren
Baselineübergangs wird hier nicht vollständig rekonstruiert; ihr aktueller
Aufruf und ihre Wirkung sind direkt geprüft. Die aktuelle Frische bleibt erhalten.

Zusätzlich benötigt jede neue Pretradeentscheidung seit PR 7186 die ursprünglichen
neun eindeutigen Fetchgruppen. Zwei Items derselben Gruppe teilen eine Antwort;
unterschiedliche Instrumentabfragen desselben Endpoints bleiben getrennte Reads.
Die Rechnung verbraucht deshalb das originale erforderliche GET-Set, keine
zusätzliche Endpointliste.

Der Productlauncher übergibt das Ergebnis dieser Budgetfunktion direkt als
max_request_count an den ursprünglichen GET-only-Transport. Derselbe Transport
bedient G17, gegebenenfalls Cold-Bootstrap, S6-Polls und die S5-Pretradeaufnahme.
Die Korrektur benötigt keinen neuen Transport oder neuen Runtimepfad.

## Rechnung und Wirkung

Bei autorisierter Zykluszahl C, S6-Dauer T und Warteintervall w bleibt die
ursprüngliche Pollobergrenze P = floor(T / w) + C + 8 erhalten.

Die Obergrenze zählt jetzt 1 G17-GET, 3 Cold-Bootstrap-GETs und 3 × P Poll-GETs.
Hinzu kommen C × erforderliche Pretrade-Fetchgruppen und die bestehende Reserve
von einem Versuch.
Bei derzeit neun Fetchgruppen ergeben sich für w = 5 Sekunden:

- C = 4, T = 180 Sekunden: P = 48; Requestdeckel 101 → **185**.
- C = 12, T = 900 Sekunden: P = 200; Requestdeckel 405 → **713**.

Poll-Retries verbrauchen bereits denselben Pollzähler. Teilweise fehlgeschlagene
Pretradeaufnahmen kosten höchstens das volle GET-Set des jeweiligen S5-Versuchs.
Die Reserve ist keine zusätzliche Retryfreigabe. Auch erfolglose HTTP-Versuche
belasten den unveränderten Transportzähler; der Deckel wird nicht zurückgesetzt.
Nicht endliche oder nicht positive Zeitwerte und ungültige Zykluszahlen können
keinen verwendbaren Requestdeckel erzeugen. Die bestehenden Owner prüfen ihre
eigenen fachlichen Hardcaps weiterhin selbst.

## Prüfung und Grenzen

Vor der Änderung scheitern beide Belastungsfälle am ursprünglichen Transport
mit MAX_REQUEST_COUNT_EXCEEDED, bereits während der Polls. Zwei weitere Fälle
bestätigen die tatsächlichen Pollkosten zwei beziehungsweise drei.

Nach der Korrektur bestehen **78** ausgewählte Owner-/Integrationsfälle. Die
Belastungsprobe benutzt Originalpoller, Original-Pretradecomposer und ursprünglichen
Transport mit lokalen Netzwerk-/Signierstubs und expliziter synthetischer Uhr.
Sie verbraucht Cold-Bootstrap, maximale Pollzahl, alle ursprünglichen Pretrade-
Fetchgruppen je Zyklus und einen fehlgeschlagenen HTTP-Versuch. Genau Versuch
185 beziehungsweise 713 ist der letzte zugelassene; der nächste bleibt gesperrt.
Das belegt Requestkosten und Fusewirkung, keinen vollständigen G17-/Core-/Hostlauf.

Einer vorhandenen HOLD-Testfixture fehlten die mittlerweile verlangten Envelope-
Felder. Derselbe Fehler tritt mit dem ursprünglichen Budgetcode der Basisrevision
auf. Die Fixture liefert jetzt ausdrücklich keinen Umschlag, keine Umschlagidentität
und envelope_created=false. Die ursprünglichen C1-/Sequenzierungs-/No-POST-
Prüfungen bleiben erhalten und prüfen zusätzlich diese leeren HOLD-Ausgänge.

**Zeitgrenze:** Die bestehende S6-Dauerkontrolle wird nach Rückkehr eines
Fremdcalls vor dem nächsten S5-Aufruf erneut geprüft. Im gezielten Gegenfall
endet ein nominell auf drei Sekunden begrenzter Lauf nach einem sechs Sekunden
dauernden simulierten Poll ohne S5-Aufruf. Das ist keine harte Unterbrechung
laufender Netzwerkoperationen. Diese Korrektur ändert weder Laufdauer, Timeout,
Warteintervall, Retryregeln, Frische-TTL noch die ursprünglichen Betriebsrechte.

Das Budget gilt für den benannten Productlauncher mit geteiltem Transport.
Die vorgelagerte Universeaufnahme hat einen eigenen Transport und gehört nicht
zu diesem gemeinsamen Zähler. Das Budget deckt keine zusätzliche
Standing-Supervisor-Preflightaufnahme, unabhängige
Private-REST-Reconciliation, vollständige Wiederherstellung oder echte Venue-
Ratelimits ab. Natürlicher Dauerbetrieb und ein harter Inflight-Deadlinevertrag
bleiben gesondert nachzuweisen. Die 24 älteren Fehler-/Setupfälle aus dem Beleg
zu PR 7186 wurden hier nicht erneut als Gesamtabnahme ausgeführt und bleiben offen.
Funding-/Margin-Herkunft und Netting sowie vollständiger Hostrestore bleiben
eigene Facharbeit. Keine Handelsaktivierung und kein Gesamtabschluss des Außenrings.
