---
docs_token: DOCS_TOKEN_SELF_LEARNING_NATIVE_RESUME_CONTRACT_V1
status: supplemental_source_review
runtime_authorization_effect: NONE
---

# Selbstlernende Forschung: Wiederanlauf und Experimentidentität

Diese ergänzende Quellenanalyse gilt für den eingefrorenen Commit
`732601aeacca7b87ff3df2e0373f180f8de50081`. Implementierung, Konfiguration und Scope bleiben
unverändert. Das [Master-Runbook](../../../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) bleibt maßgeblich.

## Drei unterschiedliche Fälle

Die native Session liest gespeicherte Failure- und Gap-Records vor der Suche. Der vorhandene
Test belegt im Quelltext eine konkrete Fallunterscheidung: Eine bekannte fehlerhafte Region
wird vor der nächsten Engine-Messung vermieden; bei erschöpften Regionen wird kein Versuch erzwungen.
Dieser Test wurde hier nicht neu ausgeführt.

Ein Archiv-Replay liest dagegen bereits gespeicherte numerische Ergebnisse. Der Archiv-Append
ist für identische Paketbytes idempotent. Daraus folgt keine allgemeine Idempotenz einer erneuten
vollständigen Session-Ausführung.

Wird dieselbe Experimentidentität erneut vorgeschlagen, erfolgt im nativen Provider zuerst die
Messung. Erst danach erreicht Phase10 den unveränderlichen Experiment-Memory-Store. Dessen
Datensatz enthält die Ausführungszeit, seine Experiment-ID wird aus der kanonischen Identität
abgeleitet. Bei gleicher ID und abweichendem Inhalt, etwa einer neuen Zeit, weist der Store
den Datensatz zurück. Dies ist eine bedingte Quellenkette, kein hier beobachteter Abbruch.

Der Searchrequest erhält keinen Bestand aller erfolgreichen Experiment-Memory-IDs. Die frühe
Vermeidung bekannter Fehler beweist deshalb für sich keine Vorab-Wiederverwendung erfolgreicher
Experimente. Ein Retest-Grund hebt die Identität und den Schutz gegen divergentes Überschreiben
nicht auf. Der betrachtete Resume-Test verwendet ausdrücklich eine andere Seed-Identität;
das ist ein anderer Fall als die erneute Ausführung derselben Identität.

## Bereits bekannte Persistenzgrenze erhalten

Die [bestehende Dokumentation](../durable_research_and_measured_mi_return_restoration_v1_2026_11_04/README.md)
nennt ausdrücklich: Vor einem späten Archivfehler können andere Ownerrecords bereits bestehen.
Das ist hier kein neuer Verlustfund. Originalrecords dürfen nicht als vermeintlicher Rollback
gelöscht werden. Ein solcher Schritt ist noch kein erfolgreich archivierter Sessionabschluss.

## Konkrete Ergänzung

Vor einer dauerhaften Forschungsschleife muss der tatsächliche Sessionconsumer zwischen
lesendem Replay, Wiederverwendung, begründeter neuer Experimentidentität und unvollständigem
vorigem Schritt unterscheiden. Die vorhandene Konfliktsperre bleibt erhalten. Es wird weder
eine neue Seed-Wahl zur Umgehung der Sperre noch ein automatischer Retest empfohlen.

Sechs definierte, noch nicht ausgeführte Kriterien sowie exakte Datei- und Ausschnitt-Hashes
stehen in [findings.json](findings.json). Die [Manifestdatei](manifest.json) bindet diesen Befund.
Keine Engine, kein Memory-Store und kein Archiv wurden dafür aufgerufen.
