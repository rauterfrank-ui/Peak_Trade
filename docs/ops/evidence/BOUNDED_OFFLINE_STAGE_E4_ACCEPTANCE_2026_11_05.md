# E4 Abschluss: Forschung, Wiederaufnahme und gemessener Metarückweg

Stand: 2026-11-05. P11/P12/P14 und AC25–AC29/AC34 sind für den ausdrücklich
begrenzten lokalen Offline-Forschungspfad abgenommen. Die Gesamtabnahme bleibt offen.

**1.477 unterschiedliche Tests bestanden**, ohne Fehler oder Skips, in 245,71
Sekunden. Darin sind alle 904 E3-Prüffälle, die aktuellen Research-/Memory-/Meta-
Regressionen und die Golden-Vector-Prüfungen enthalten. 24 neue E4-Prüffälle
belegen Vorprüfung, Originalrequest-Recovery und die tatsächliche Folgemessung.
Die vollständige Population und Source-/Testbindungen liegen im Abschlussreport:
`/Users/frnkhrz/Desktop/PEAK_TRADE_SYSTEMPLAN/65 Gesamtsystementwurf/Etappe 4 Research Metarueckweg/Abschluss 2026-11-05.json`.

Der [Vertrag](../specs/BOUNDED_OFFLINE_STAGE_E4_RESEARCH_RECOVERY_V1.md) trennt
historischen Zweck, bestehende Owner, neue Handoff-Sicherung und offene Grenzen.

## Beobachtete Wirkung

- AC25: Vor dem Provider wird die tatsächliche Experimentidentität unter gemeinsamer
  Researchstep-Lease geprüft. Originale werden wiederverwendet oder fortgesetzt;
  Konflikte und Same-ID-Replikation sperren. Eine identische bestätigte Anfrage
  startet auch nach veränderter Failure-Memory keinen zweiten Kandidaten.
- AC26: Vor dem ersten Phase10-Memorywrite bleibt der vollständige validierte
  Originalrequest samt Messreceipt erhalten. Die Wiederaufnahme verwendet genau
  dessen CreatedAt, Zahlen und Ownerlocators. Tests beenden reale Prozesse nach
  Experiment-, Failure-, Gap-, Archive- und ACK-Writes; ein frischer Prozess setzt
  mit gesperrter Engine fort. Eine vor dem Preparedrecord verlorene Originalmessung
  bleibt ausdrücklich ungeklärt und blockiert.
- AC27: Aus nativ gemessenen Originaltrials erzeugt eine explizite strengere
  OOS-Bewertung drei relevante Overfit-Befunde für slow_window=50. Meta verändert
  die nächste Searchpriorität, und die gewählte 100er-Region wird tatsächlich
  durch vier Engine-Runs gemessen. Ohne diesen Befund wird 50 gemessen. Drei
  entsprechende Befunde zur unbeteiligten 75er-Region ändern die Wahl nicht.
  Die Target-Failure-Stores sind zuvor leer; direkte Failure-Filter erklären die
  Wirkung daher nicht. Vollständige numerische Archive, spätere identische Meta-
  Auswertung und ein tatsächlicher Original-Champion-/Challenger-Zahlenconsumer
  nach Reload sind dauerhaft erhalten.
- AC28/AC29: Die bereits implementierten vollständigen Candidate-/Baseline-
  Wiederholungsprüfungen, späte Mutationssperren und unabhängigen rehashenden
  Registry-Readbacks bestehen unverändert. Der neue Researchpfad verwendet
  weiter den ursprünglichen vollständigen Zahlen-/GVEF-Referenz-Archivvertrag.
- AC34: Die wirksame erwartete föderierte Optimizationversion sowie davon
  unabhängige tatsächliche M5-/Join-/Meta-Payloadprüfung bestehen unverändert.
  Dieser Evidencepfad wird nicht zu einer neuen nativen Searchmessung erklärt.

## Zahlen und Aussagegrenzen

Der gemessene Gesamtscore (nicht annualisierter Full-Engine-Equity-Sharpe) beträgt
für die 50er-Region **0,030562049388796947**, für die gewählte 100er-Region
**0,030229745317592854**. Der zweite Wert ist niedriger. Beide OOS-Scores sind
in diesem Beispiel gleich. Die Studie belegt folglich Auswahl-/Messwirkung und
Erhaltung der Numerik; sie belegt keine Verbesserung, Marktkausalität oder
wirtschaftliche Lernqualität. Der Eingriff verändert ausdrücklich eine
Research-Bewertungspolicy über gemessenen Splitzahlen, keine natürliche Marktlage.
Die vorab festgelegten unterschiedlichen Seeds werden nicht als unabhängige
Marktstichproben oder nachträgliche Konfliktumgehung ausgegeben.

Fehlende Robustheitsfähigkeiten, fehlende spätere Outcomes und Parameterstabilität,
Funding-/Quellenauthentizität und synthetischer Gapkontext bleiben ausdrücklich
begrenzt. Späteres Meta erhält seine Zahlen und liefert dieselbe Auswertung;
dadurch werden zuvor nicht berechenbare Assoziationen nicht berechenbar. Die
separate numerische Rangfolge wird mit dem vorhandenen Originalowner ausgeführt.
Kein Training, Championtausch oder produktiver Parameterapply ist enthalten.

Die Prepared-Handoffdateien sind keine zweite Experiment-Memory. Bestehende Owner
bleiben maßgeblich, Records werden nicht gelöscht oder rückwirkend ersetzt.
Die gemeinsame lokale Lease koordiniert diesen Sessionport, nicht sämtliche
standalone Altcaller oder verteilte Writer. Kein verteilter Commit-, Stromausfall-
oder Rollbackschutz wird behauptet. Archivierte Zeugen behalten ihre ursprünglichen
Pfade als Herkunft; ihre Kopie ist keine automatische Recovery-Migration.

Frühere E1–E3-Abnahmen, Ledger und Scopeformel/-parameter bleiben erhalten. Der
bereits in E3 separat reproduzierte Legacyfehler `future_native_contract_identity_unknown`
bleibt dokumentiert; es wird kein vollständig grüner Repository-Gesamttest behauptet.
E5 (Verbundbewertung) und E6 (systemweite Offlineabnahme) bleiben offen.
Keine Live-/Testnet-/Credential-/Order-/Kapitalbewegungs-/Service-/Veröffentlichungs-
oder Git-Commit-/Push-Aktion wurde ausgeführt.
