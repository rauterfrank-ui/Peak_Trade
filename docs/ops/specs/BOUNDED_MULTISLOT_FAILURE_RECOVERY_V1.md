# Ausfälle und Wiederaufnahme der begrenzten Mehrslotprobe

Stand: 09.11.2026. Ausführungswirkung: NONE.

Diese Prüfung baut auf dem [verbundenen Originalpfad](BOUNDED_MULTISLOT_CONNECTED_CYCLE_V1.md)
mit zwei beziehungsweise fünf tatsächlichen originalen Reservationen auf.
Alle Eingaben sind synthetisch; Netzwerksockets bleiben gesperrt.

## Reichweite der Fehler

- Ein instrumentbezogenes Ordermengenlimit null verhindert dessen finalen
  Entryplan. Andere Slots können ihren eigenen zulässigen Plan bilden; das
  freigewordene Slotbudget wird ihnen nicht zugeschlagen.
- Gemeinsame falsche Accountidentität, veraltete Accountbeobachtung oder
  ungelöste Pending-Orders sperren die ursprüngliche gemeinsame Admission.
  Holdbeträge, Ausführungslinks und ursprüngliche Corecursor bleiben erhalten.
- Eine unzugeordnete offene Position oder ungesunde gemeinsame Portfoliowahrheit
  schließt im expliziten begrenzten Testpfad denselben Originalbudgetowner vor
  dem Coreaufruf. Ein Fehler beim Leaseabbau überschreibt die originale Ursache
  nicht. Die vorhandenen Hold- und Wiederaufnahmeregeln bleiben zuständig.
- Ein Fehler im ursprünglichen S7/Corepfad entzieht die gemeinsame Admission.
  Bereits gehaltene Pläne aller fünf Slots können den geschlossenen Owner nicht
  als positive Submitzulassung verwenden. Neue Envelopes entstehen nicht.
  Ein weiter ausgewerteter Holdzyklus ist keine Handelsfreigabe.

## Wiederaufnahme und dauerhafte Bindung

Nach frischen ursprünglichen Accountbeobachtungen läuft dieselbe originale
Recovery mit dem tatsächlichen ursprünglichen kanonischen Kapitaloutput.
Sie behält alle Holdbeträge und Orderlinks. Ein Cold-Reopen übernimmt die
persistierte Testbudgetbindung und dieselben Verpflichtungen, beginnt aber mit
`recovery_required` und ohne Admission. Es gibt keinen Operator-Unlock und
keinen aus einem leeren Ersatzowner abgeleiteten Kapitalwert.

Ein gesonderter Prozess lädt denselben Originalstore und endet mit `os._exit`,
ohne seinen Writer ordentlich zu schließen. Ein weiterer frischer Prozess
erhält den Writerlock, liest dieselben Holds, Links und die Policy und bleibt
ebenfalls bis zur ursprünglichen Recovery gesperrt. Dies belegt den geprüften
Prozessabbruch nach dem Laden; es belegt keinen Stromausfall oder Abbruch mitten
in einer Datenbanktransaktion.

Fehlende und beschädigte SQLitezustände werden an den ursprünglichen
Recoverybedingungen abgewiesen. Der beschädigte Teststore wird nicht repariert
oder durch einen leeren Store ersetzt.

## Verbleibender Abschluss

Die [Prüfung](../../../tests/ops/test_bounded_multislot_failure_recovery_v1.py)
belegt diese konkreten Fälle. Eine echte Venueausführung, produktive N5-Rechte,
ein durchgängiger Mehrslot-Handelskreis nach bestätigten Closings und physischer
Stromausfall bleiben eigenständige Nachweise. Insbesondere bleibt die vollständige
Post-Close-/Rebindingkette derzeit N1-gebunden. Frank entscheidet ausdrücklich
über das Ende der Testphase; Tests erzeugen keinen automatischen Übergang.
