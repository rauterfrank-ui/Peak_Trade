# Etappe E1: abgegrenztes Offlineprofil v1

Stand: 2026-11-05. Lokale Implementierung auf HEAD
`1814ca5b24d1d3ab537683e340b3ab045ea51e62` mit uncommitteten Ergänzungen.
Dieser Vertrag ergänzt den bisherigen E1-Arbeitsstand. Historische Verträge und
Evidenz bleiben datierte Nachweise ihrer damaligen Reichweite.

## Zweck und gewählte Komposition

E1 verbindet begrenzte Offlinefortsetzung, Datenzulassung und bestehende N5-
Completion. Einstieg ist `open_e1_offline_session_v1` in
`src/ops/bounded_peaktrade_system_composition_v1/profile_v1.py` als expliziter
Contextmanager mit Modus `create` oder `recover`. Der Einstieg verlangt das
Manifest v2, den Digest aller fünf Datenzwecke und verpflichtende Hostcompletion.
Ein dünner Legacyaufruf zählt nicht als dieses Profil.

Das Sessionprofil übernimmt eine bereits eröffnete simulierte Positionsepisode.
MaxPos bleibt eins. Zwei tatsächliche N1-Auswertungen mit originalem Core,
Exit-/Cursorowner und Hostcompletion sind über Schließen/Wiederöffnen der Session
belegt, jeweils für Long und Short. Die vorhandene Accountingmenge von 0,4
Kontrakten bleibt bestehen: erzeugte Close-Envelopes werden nicht ausgeführt.
Vollständiger Positions-, Kapital-, Risiko- und Fill-Lifecycle gehört zu E2.

Daneben führt der architektonische N5-Harness fünf Instrumente aus einem
gemeinsamen, lesenden Public-Fact-Gateway über Economic MD, originale numerische
B05-Merkmalsproduktion, Cap22, Cap23/24 und N5 zur originalen Completion.
Die fünf getrennten Laneroots bedeuten weder fünf Positionen noch eine produktive
N>1-Zulassung. Der Harness ersetzt explizit Datenbeschaffung, Venueports und
Versuchsinputs durch lokale Fixtures. Er aktiviert keinen produktiven Rangpfad.

## Instanzen, Autorisation und Wiederaufnahme

Session, Account/Umgebung, Instrumentgeneration, Episode, Quellrecord, Implementierung,
Konfiguration, Zeitbereich und Versuchslimit sind manifestgebunden. Vor jedem
N1-Versuch wird der Verbrauch dauerhaft geschrieben. Der typisierte
`OfflineGovernedAttemptV1` validiert diesen exakten RUNNING-Record und bindet nur
die Evidenz des einzelnen Versuchs unterhalb des ursprünglichen Evidenzroots.
Originale Exit-, Cursor- und Shared-Lock-Roots bleiben gleich. Der bestehende
Governed-Cycle-Owner bleibt unverändert einmalig pro Evidenzroot.

Verbrauchte Originalledgers werden weder gelöscht noch als neue Autorisation
umgedeutet. Wiederholung, fremder Account, Namespace, Clock oder Charged-Record
scheitern. Neustart erneuert keine Versuche. Unterbrechung einschließlich Fehler
zwischen N1-Ergebnis und Completion führt zu RECOVERY_REQUIRED; Wiederöffnung
startet keine automatische Fachauswertung. Alte Manifest-/Codegenerationen werden
nicht still migriert. Die technischen Ressourcensperren sind kooperativ und keine
globale Transaktion über sämtliche Legacycaller.

Der bestehende Portfolioowner wird im N5-/Hostpfad unverändert weitergegeben;
Recoverykontext erreicht T2 und 29P. Separate Originalhostkontrollen belegen
Hold-Erhaltung und Accountbindung nach Neustart. Das gewählte belegte
Managementprofil benötigt keinen neuen Entry-Hold und erzeugt keinen Ersatzowner.
Die vollständige kapitalwirksame Verbundepisode bleibt E2.

Completion erhält bereits vorliegende Readiness und Consumerresultate. Sie führt
keinen zweiten Core-/N1-Cycle aus. Ein Completionfehler nach N1-Verbrauch ist kein
Grund, denselben Versuch erneut auszuführen.

## Datenbedeutung an den Consumern

Die Datenpolicy ist pro Zweck und exaktem Consumer explizit: kanonisches
Instrument, Factkind/Channel-Paare, Event-/Capturealter je Kind, maximaler
Captureversatz, Korrekturzulassung und Finalität je Kind. Es werden keine
produktiven numerischen Defaults ratifiziert. Der Profildigest bindet außerdem
Store, Preisbasis, Volumeneinheit und Intervall. Der bewegliche As-of-Zeitpunkt
bleibt innerhalb der ursprünglichen Sessionbounds.

Die fünf tatsächlichen Eingangsconsumer sind:

- RANKING: originaler `PublicRuntimeEconomicMdPublicSourceV1`, originale
  61 zusammenhängende finale PT1M-Markpreise, originale B03/B05-Berechnung und
  Cap22-Validierung. Sigma ist die Populationsstreuung der 60 Logreturns pro Bar;
  sie wird nicht annualisiert. Ein neu gehashter Datensatz mit annualisierter
  Einheit wird vom originalen Rankingconsumer abgelehnt.
- TRADING: zugelassene finale PT1M-OHLCV-Daten mit mindestens 100 Bars werden
  unverändert in den originalen C1-Extractor und den tatsächlichen N1/Corepfad
  gegeben. Preisbasis und Volumeneinheit müssen dem gebundenen Profil entsprechen.
  Nicht verfügbare zusätzliche Volumenwährungen bleiben leer.
- RESEARCH: zugelassene Closes gehen in dieselbe originale Returnberechnung wie
  der Parquetloader. Das gewählte Intervall ist Teil der Profilidentität.
  Dies belegt den Dateneingang, noch keinen vollständigen Researchlauf.
- OUTCOME: nur der originale finale PT1H-O4-Fact mit kanonischem Bar-Envelope
  erreicht den originalen Snapshotbuilder. Gewöhnliche frische OHLCV-Daten werden
  nicht zur autoritativen Outcomequelle erklärt. Das ist kein kompletter
  Decision-Job-Messung-Lernrückweg; dieser folgt in E3.
- LIQUIDITY: originale Quotezahlen erreichen den gebundenen Dateninput. Bid/Ask
  beweisen keine Depth, ADV oder Slippage. Bei diesen Pflichtgrößen lautet das
  Ergebnis CANNOT_EVALUATE mit fehlenden Werten und `risk_admitted=False`.
  Numerische Risikomodelle und Mengenadmission folgen in E2.

Der Sourcechecker liest digestgeprüfte Originalfacts. Spätere Event-, Capture-
oder Effective-Versionen sind historisch nicht verfügbar. Fehlende Uhrzeiten
werden nicht ersetzt. Captureversatz vergleicht die jeweils neuesten Köpfe pro
Factkind, nicht sämtliche Capturezeiten eines historischen Fensters. Jeder
historische Record unterliegt trotzdem seinen eigenen Alters-/Qualitätsgrenzen.

Kerzenöffnung, tatsächlicher Kerzenschluss, Erfassung und Entscheidungszeit sind
verschiedene Größen. Ein Finalized-Flag überstimmt keinen zukünftigen Schluss.
Das gebundene Offline-As-of wird bis zur tatsächlichen Core-`decision_time`
transportiert; `market_event_time` und Scope-Samplezeit bleiben Originalgrößen.
Die vorhandene DDO-Observationtime bezeichnet weiterhin Markteventzeit. Sie ist
kein automatischer Knowledge-Clock-/Outcomehorizontnachweis; diese Bindung bleibt
Teil von E3 und der natürliche Exportblocker bleibt wirksam.

Identische numerische Wiederbeobachtungen derselben Bar erzeugen eine Stichprobe.
Abweichende OHLCV-Werte brauchen eine strikt spätere Capturezeit, ein explizites
Corrected-Flag und die gebundene Korrekturpolicy. Gleichzeitige widersprüchliche
Revisionen, Lücken, falsche Einheiten und alternative Preisbasis scheitern.
Es gibt keinen Forward-Fill oder Ersatzwert aus fehlenden Daten.

## Auswahl, Laneidentität und optionale Residency

Die bestehenden Auswahl-/Topologieowner bleiben maßgeblich. Ein Rangtausch
fortgesetzter Instrumente ändert ihre wiederhergestellte Laneidentität nicht.
Fremde Snapshot-/Universe-/Digestbindung und beschädigte Checkpoints blockieren
statt neu zu bootstrappen. Vorhandene Residencytests prüfen zusätzlich
Snapshotidempotenz, Admissionidentität und Restartverhalten.

Im gewählten E1-Profil ist Residency nicht aktiviert. Mehrere optionale
Residencyframes sind NOT_SELECTED; es wird kein aggregiertes Laufzeitergebnis
aus einem letzten Frame behauptet. Die grünen Enginekontrollen ersetzen keine
spätere Abnahme einer tatsächlich aktivierten Mehrframekomposition.

## Konfiguration und Aussagegrenzen

Der zusätzliche Konfigurationsrecord bindet den frisch geladenen originalen
Configdigest, tatsächliche importierte Core-/Aliasoperanden und originale
Exitkonstanten. Abweichende oder fehlende Records und alte importierte Aliase
blockieren. Ein isolierter Kindprozess lädt ein temporäres TOML mit abweichenden
Confirmationepochs vor dem Coreimport und belegt die tatsächliche Wirkung.
Ein anschließendes Getter-Cacheclear aktualisiert keinen alten Corealias.
Scopeabstände und die Projektkonfiguration bleiben dabei unverändert.

E1 ist ausschließlich für dieses explizite lokale Offlineprofil abgenommen.
Die Abnahme verbindet mehrere belegte Teilpfade; sie ist kein einzelner
vollständiger Fünf-Positions-/Kapital-/Outcome-Lernlauf. Historische Ursprünge und
vollständige heutige Systemsemantik werden dadurch nicht pauschal zertifiziert.
Die genaue Zuordnung der elf E1-Abnahmekriterien, Testreceipts, Dateihashes und
offenen Folgearbeiten steht im neuen Abschlussreport. Es entsteht keine Live-,
Testnet-, Credential-, Netzwerk-, Order-, Kapital- oder Veröffentlichungsfreigabe.

Nachweis: [E1-Abschlussevidence](../evidence/BOUNDED_OFFLINE_STAGE_E1_ACCEPTANCE_2026_11_05.md).
