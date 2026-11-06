# E2: Position, Kapital, Risiko und Wiederaufnahme im expliziten Offlinepfad

Stand 2026-11-05; lokale uncommittete Ergänzung auf
`1814ca5b24d1d3ab537683e340b3ab045ea51e62`. Dieser Vertrag ergänzt
[E1](BOUNDED_OFFLINE_STAGE_E1_ACCEPTANCE_V1.md). Er ersetzt weder originale
finanzielle Owner noch Scope-, Auswahl-, Ausführungs- oder Betriebsautorität.

## Gewählte Konstruktion und historische Varianten

Die ursprünglichen Positions-, Accounting-, Exit- und Budgetowner bleiben erhalten.
E2 verbindet ihre expliziten lokalen Ports und ergänzt restriktive Risiko- und
Übergabenachweise. Vollständige Systemausführung mit Outcome/Lernrückweg und
unabhängiger wirtschaftlicher Bewertung folgt den verbleibenden Etappen.

Die bereits rekonstruierte Risikoplanung FG01–FG09/T01–T17 ist Ausgangspunkt:
`risk-functional-reconnection-spec-v1&#47;functional_reconnection_plan.json` im lokalen
Kartierungsbestand vom 2026-11-04. Ihre historischen Library-/Consumerdossiers
bleiben Quellen ihrer damaligen Revision; heutige Wirkung wird an tatsächlichen
Consumern geprüft. Relevante vorhandene Implementierungen sind `src/risk/var.py`,
`portfolio_var.py`, `stress.py`, der originale Sizingowner und die dauerhaften
Portfolio-/Executionowner. Keine alten fail-open Gates werden reaktiviert.

Die gewählte Modellvariante ist historische VaR auf explizit projizierten,
vorzeichenbehafteten Futures-Expositionen. Die vorhandene Portfolio-Library mit
Summe-gleich-eins-Gewichten würde diese Expositionen verändern und wird dafür
nicht verwendet. Stattdessen konsumiert die originale Einzelserien-VaR die
tatsächliche gewichtete Portfoliorenditeserie. Linke Tailwahrscheinlichkeit und
Confidence werden gemeinsam explizit verlangt und müssen sich zu eins ergänzen.
Ein Minutenreturn wird nicht durch einen als Tage bezeichneten Parameter skaliert.

Für Stress bleiben die originalen Szenariotransformationen maßgeblich. Der
mean-erhaltende VolSpike kann nur mit einem dafür geeigneten Tail-/Worst-Loss-Maß
verwendet werden. VolSpike plus Mean-Loss wird abgelehnt. Asset-Shocks wirken vor
der Projektion auf die vorzeichenbehaftete Position; ein negativer Asset-Shock
wird daher nicht als negativer Portfolio-Return einer Shortposition ausgegeben.
Andere nicht implementierte Szenarien/Instrumentarten werden nicht still ersetzt.

Die historische Adverse-vor-TimeExit-Regel wird nicht umgedreht. Eine zusätzliche
Reduktionsquote oder harte Ausführungsfrist ist nicht historisch hinreichend belegt
und wird nicht erfunden. `REDUCE_RISK_RULE_REQUIRED` bleibt eine konkrete Sperre
für einen noch nicht fachlich bemessenen REDUCE. Der bestehende TimeExit-Anker und
seine Pendingidentität bleiben erhalten. Das ist keine Behauptung, jede solche
Verpflichtung werde ohne weitere fachliche Mengenregel bereits ausgeführt.

## Daten-, Einheiten- und Zeitsnapshot

`src/risk/decision_bound_model_adapters_v1.py` definiert unveränderliche typisierte
Offlineinputs. Account/Umgebung, Decision/Cycle, Lane, kanonisches/native Instrument
und Instrumentepoch sind gebunden. Der Input bezeichnet vollständige bekannte
Positionen und explizite Abdeckung bereits gefüllter Reservierungen. Originale
aktive Holds werden aus dem Budgetowner gelesen, nicht aus einem zweiten Ledger.

Die Exposition besteht aus beobachteter Position plus ungefülltem Rest eines
originalen Holds. Ein gefüllter Anteil darf nur anhand der passenden originalen
Execution-Reconciliation und ihrer exakten Mengenabdeckung abgezogen werden.
Unbekannte Submitzustände, fehlende Sizingbindung oder widersprüchliche Abdeckung
erlauben keine neue Risikoadmission. Weder Budgetrest noch Marge wird als
Portfoliogewicht oder als tatsächliche Position ausgegeben.

Linearer Kontraktmultiplikator, native Kontraktmenge, Quote-/Settlementwährung,
Quote-zu-Kapital-Umrechnung und deren Quellen-/Zeitbezug sind explizit. Inverse
Kontrakte werden abgewiesen. Der Riskdenominator heißt ausdrücklich ACCOUNT_EQUITY
und hat eine eigene Quelle. Der originale Available-for-Sizing-Producer bleibt
daneben alleiniger Budgeteingang. Gleiche Zahlen machen die Bedeutungen nicht
gleich. Am tatsächlichen 29P-Join stimmt der Risk-Positionsinput mit dem originalen
Host-Portfolio-Readback einschließlich dessen Digest und Zeiten überein.

Returns müssen endlich, geordnet, synchron und pro Instrument lückenlos sein.
Sampleperiode und Haltehorizont sind explizit; der Horizont ist ein ganzzahliges
Vielfaches. Vollständige nicht überlappende Assetfenster werden geometrisch
zusammengefasst und anschließend mit statischer, signierter As-of-Exposition
projiziert. Es gibt weder implizites Rebalancing noch eine versteckte
Quadratwurzel-Skalierung oder Zero-Correlation-Annahme. Event, KnownAt, As-of,
Altersgrenzen und Captureversatz werden vor Modellverwendung geprüft.

Liquidität verwendet echte deklarierte Preis-/Kontraktmengenlevels, separat
gebundenes ADV-Quote-Notional und dessen Fenster/Zeit. Spread wird über den Mid in
Bps berechnet, Slippage über den mengenabhängigen Bookwalk gegen den besten
ausführbaren Preis. Depthband und ADV-Teilnahme bleiben getrennte Prüfungen.
Die gewählte Market-/Limitpolicy heißt IMMEDIATE_EXECUTION_ONLY: Ein nicht sofort
ausführbares Limit erhält keinen behaupteten Fill oder Kapazitätspass. Quotes
allein sind weiterhin keine Depth/ADV/Slippagequelle. Fehlende, nichtfinite,
fremde oder veraltete Pflichtwerte führen zu einer konkreten Exception und
FAIL_CLOSED am Reservierungsconsumer; sie erzeugen keinen erfolgreichen
Modellrecord mit Risiko null. Berechenbare Grenzverletzungen tragen BLOCK.

Alle numerischen Policies müssen als EXPLICIT_OFFLINE_TEST_POLICY samt Quelle
vorliegen. Testwerte sind keine Ratifikation produktiver Confidence, Limits,
Horizon-, Depth- oder ADV-Policies und keine authentischen Marktbeobachtungen.

## Tatsächliche Sizing-, Reserve- und Envelopebindung

Der bestehende `admit_sized_slot_reservation_v1` erhält optional den typisierten
`restrictive_risk`-Input. Der explizite 29P-Pfad erlaubt ihn nur mit bereits
vorhandenem, offenem Host/Recoverycontext und injizierten Offlineports. Er schafft
keinen privaten Transport, um das Profil zu prüfen. Originale Double-Play-
Entscheidung und Equity-/Monetary-Normalization-Producer werden nicht ersetzt.

Nach ursprünglicher Kapitaladmission wird ein Readback unter dem originalen
Budgetlock eingefroren. Sein Digest bindet aktuelle Observation, Account,
Lane-/Instrumentgenerationen, originale Holds/Executionlinks und den dauerhaften
Storehead. Eine positive explizite Mengenobergrenze geht als zusätzliche Schranke
in den originalen Sizingowner; Null wird vorher verweigert. Genau die von diesem
Owner endgültig bemessene Menge wird numerisch gegen alle gewählten Modelle
geprüft. Es wird keine Monotonie eines Hedge-Risikos vorausgesetzt und keine
Envelope nachträglich auf einen vermeintlich sicheren Wert umgeschrieben.

Vor dem Einfügen des Holds prüft derselbe Budgetlock den Snapshotdigest erneut.
Ein Beobachtungs-/Hold-/Generationswechsel führt zum Abbruch ohne neue Reservierung.
Der Caller darf erst mit einem neuen expliziten Snapshot und innerhalb seiner
ursprünglichen Bounds neu bewerten; es gibt keine automatische Endlossuche.

`ReservationSizingBindingV1` speichert die erfolgreiche exakte Riskbindung als
versioniertes v2-Objekt im bestehenden atomaren Budgetcheckpoint. Historische
v1-Bindungen behalten ihre Darstellung und Holds. Alte Holds erhalten nicht durch
einen neuen Caller eine nachträgliche Riskzertifizierung. Alte Leser brauchen
keine v2-Daten zu akzeptieren; es gibt keine stille Migration oder Downgrade.

Bei Wiederholung bleiben ursprüngliche Sizingmenge und Riskinput erhalten.
Fehlender/geänderter Riskcontext blockiert; ein frischer Timestamp kann einen alten
Record nicht als neue Entscheidung zulassen. Der originale Executionlink prüft
die unveränderte Envelope gegen die gespeicherte Riskmenge, Instrument, Side,
Ordertyp und Preisbindung. Nur dieser verbundene Pfad ist hier belegt; ein
Legacycaller ohne die expliziten Ports erhält keine pauschale Zertifizierung.

## Entryquelle, Teilfüllung, Flat und neue Episode

Der neue `risk_bound_simulated_entry_v1`-Adapter verbindet eine bereits angewendete
explizite simulierte Openingfüllung mit originalem Hold, Riskbinding und exakt
gebundener Envelope. Er führt keinen Fill aus. Fillidentität, Instrument, Side,
Menge, Kontraktgröße, Quote, Tick-/Mindestmenge und ursprüngliche Eventzeit werden
geprüft. Ein separater unveränderlicher Herkunftsrecord wird vor der originalen
Exitadoption aufbewahrt. Fehlende oder auch konsistent neu gehashte fremde Records
werden beim spezifischen Restore nicht akzeptiert. Die originale Accountingengine
prüft weiter die vollständige Quelle und berechnet Durchschnitt, Menge und PnL.

Eine konkrete Lücke ist geschlossen: N1 prüft die beobachtete Restmenge jetzt
auch gegen die initiale simulierte Accountingquelle, nicht erst nach einem
Progressupdate. Abweichung scheitert vor der Governed-Cycle-Autorisation.

Der verbundene Long-/Short-Test führt zwei echte N1-/Completionzyklen aus:
ursprüngliche Close-Envelope über 0,4, deklarierte simulierte Teilfüllung über 0,1,
Sourceupdate, Sessionneustart, dieselbe Pendingverpflichtung und neue originale
Close-Envelope über den Rest 0,3. Erst vollständige Accounting-Flatquelle und
explizite originale Positions-/Pending-/Portfolio-Prüfung versiegeln die Episode.
Die erste Governed-Evidenz bleibt bytegleich. Die getrennte Nachfolgeepisode
übernimmt weder die alte Pendingidentität noch alte Cursorroots.

Die Teilfüllung ist ein expliziter Simulationsport für eine bestehende Full-Close-
Envelope, keine erfundene prozentuale Adverse-REDUCE-Regel. Eine getrennt beobachtete
Nachfolgefüllung ist kein automatisch neu zugelassener Entry. Lokales Flat löst
weder Kapital noch Slot, Algo-Custody oder Outcomeverpflichtungen pauschal auf.
Die originalen Treasury-/Close-Reconciliation-Tests prüfen gesondert den
identitätsgebundenen Release/Refresh und die Hold-Erhaltung bei Teilclose.

## Übergaben, Crash und Readiness

`OfflineHandoffJournalV1` besitzt nur unveränderliche technische Übergabenachweise.
Bei gewähltem `handoff_journal` schreibt der originale Risk-Reservepfad PREPARED
vor dem finanziellen Insert; ACK folgt erst auf den dauerhaften Originalcommit
und dessen Readback. Fehler nach Commit sperren den aktuellen Handle. Ein neuer
Prozess liest genau diesen ursprünglichen Hold und kann nur dessen ACK ergänzen.
Ein Replay mit noch fehlendem ACK blockiert. Es entstehen keine neuen Holds,
Rückrechnungen, Rollbacks oder selbständigen Release-/Resendaktionen.

Für Exitstate/Marker/Manifest wird jeder einzelne Swap geprüft. Vollständig
geschriebener Originalzustand ist verifizierbar; gemischte Generationen bleiben
erhalten und recoverypflichtig. Dieser Coordinator repariert keine Bytes nach
Vermutung. Die originalen Submitbarrieren bleiben unverändert: insbesondere
erlaubt ein fehlender zweiter Marker nach erster Barriere keinen erneuten Send.
Die Prüfungen verwenden ausschließlich injizierte, nicht vernetzende Transporte.

`project_offline_session_readiness_v1` bindet tatsächlichen Prozess/PID,
Session-/Manifestidentität, Heartbeat, originale Quell-/Konfigurations-/Ownerchecks
und Restbounds. `run_readiness_checked_offline_cycle_v1` konsumiert die Projektion
vor N1. Ein guter Prozessstatus ist kein Fach- oder Venue-Pass. Die Projektion
unterscheidet New-Entry-Kapitalbedarf von bestehendem Positionmanagement:
Recoverypflichtiges Entrykapital erteilt kein Entryrecht, wird aber auch nicht
zu einer neu erfundenen Kapitalvoraussetzung für Schutzreduzierung/Exit.
Der belegte occupied-Sessionpfad erlaubt überhaupt keinen neuen Entry.

Der dauerhafte manifestgebundene Stoprecord verhindert neue Sessionzyklen vor
Versuchsverbrauch und bleibt bei Wiederöffnung wirksam. Bestehende Versuche,
Holds und Originalledgers bleiben erhalten. Read-only-Inspektion bleibt möglich.
Ein bereits laufender synchroner Call wird dadurch nicht hart unterbrochen.
Es wird weder ein Supervisorprozess installiert noch eine hängende Fremdoperation
automatisch neu gestartet. Kooperative lokale Locks sind keine globale
Transaktion über beliebige Legacycaller oder ein Power-Loss-Beweis.

## Abnahmereichweite

E2 ist für diese expliziten lokalen Offlineports mit konservativen Sperren
abgenommen. Die zwölf zugeordneten Kriterien AC11–AC20, AC36 und AC37 und alle
Risiko-T01–T17 sind im neuen Abschlussreport mit konkreten Consumerwitnesses
zugeordnet. Zusammenhängende Teilpfade und Originalregression sind getrennt von
einer erst in E6 beanspruchbaren kompletten Verbundepisode beschrieben.

Offen bleiben produktive Policy-Ratifikation und Quellenauthentizität, eine
gesondert zu bestimmende Adverse-Reduktionsregel, gegebenenfalls zusätzliche
TimeExit-Frist, natürliche Fill-/Outcome-/Lernqualität und die verbleibenden
Etappen. Scopeformeln/-parameter, finale Schutz-/Permitgrenzen, Originalledgers
und der originale finanzielle Rechenkern bleiben geschützt. Es entsteht keine
Live-, Testnet-, Credential-, Order-, Kapitalbewegungs- oder Veröffentlichungsfreigabe.

[Aktuelle E2-Evidence](../evidence/BOUNDED_OFFLINE_STAGE_E2_ACCEPTANCE_2026_11_05.md).
