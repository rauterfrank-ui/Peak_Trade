---
docs_token: DOCS_TOKEN_CURRENT_OFFLINE_PARITY_EXPLICIT_FINANCIAL_CONTEXT_V1
authority: NONE
runtime_authorization_effect: NONE
---

# Expliziter Finanzkontext im aktuellen Offline-Paritätsvergleich

Aktuelle Ausgangsbasis ist 65fdc5075b3adda49e12c83f21276d0ec96dd50d.
Der dortige [Zahlenbeleg](../evidence/CURRENT_SURVIVAL_NUMERIC_ADMISSION_2026_11_08.md)
hält drei fehlgeschlagene Paritätsprüfungen fest. Dieser Anschluss repariert die
betroffene aktuelle Übergabe. Vorhandene Prüfungen und ihre PASS-Erwartungen
werden weder entfernt noch abgeschwächt.

## Belegte Ursache

Die Financial-Fixture des [Paritätsharness](../../../src/trading/master_v2/integrated_vs_scenario_replay_full_system_parity_harness_v0.py)
rief den heutigen Mengenadapter ohne dessen ausdrücklich erforderlichen
Kapitalkontext auf. Dieser lieferte korrekt CAPITAL_RISK_CONTEXT_UNRESOLVED und
keine Mengenbindung. Zusätzlich leitete die Fixture selected_side durch
Stringersetzung aus einem SideState-Namen ab. Aus dem heutigen Armed-Neutral-
Namen entsteht dabei kein gültiges long/short.

Der andere Vergleichszweig verwendete zudem den impliziten isolierten
Szenario-Finanzkontext. Dieser passt nicht zum Preis 100 des ausgewählten Ticks.
Ein BOUND_OFFLINE-Label kann selbst bei blockierter Mengenrechnung vorkommen;
der bisherige reine Labelvergleich ist daher kein ausreichender Vergleich eines
positiven Mengen-/Intentpfads.

## Explizite Übergabe an die Originalowner

Die vorhandenen Szenarioadapter für
[Mengenrechnung](../../../src/trading/master_v2/capital_risk_sizing_offline_replay_binding_adapter_v0.py)
und [Order-Intent](../../../src/trading/master_v2/canonical_order_intent_offline_replay_binding_adapter_v0.py)
nehmen jetzt optional den bereits existierenden vollständigen
CanonicalCoreRuntimeCapitalContextV0 entgegen. Diese Form benötigt keinen neuen
Finanz-Datentyp und keine zweite Mengenformel. Der übergebene Körper erreicht
unverändert die bisherigen Originalbinder.

Explizites None bedeutet fehlender Kontext und führt zur bisherigen gesperrten
Originalantwort. Ein falscher Typ oder ein gleichzeitig abweichend übergebener
Referenzpreis wird abgewiesen. Für diese explizite Form werden keine isolierten
Kontoliterale nachgeladen. Der getrennte Sentinel für ältere Aufrufer, die das
neue Argument vollständig auslassen, erhält nur deren bestehende isolierte
Fixture-API. Das ist keine Migration oder Freigabe eines produktiven Aufrufers.

Der [Szenarioreplay](../../../src/trading/master_v2/offline_double_play_scenario_replay_v0.py)
kann für denselben Zweck capital_contexts_by_tick erhalten. Ein leeres Mapping
oder eine fehlende Tickadresse bedeutet in diesem expliziten Modus None. Beide
Adapter erhalten denselben tatsächlichen Tickkontext. Ein leerer Eintrag wird
nicht mit dem älteren ausgelassenen Argument verwechselt.

Die heutigen Financial-Fixtures entnehmen dem Replay nur ihren tatsächlichen
Entry-Policyausgang. Dazu läuft dieser Zweig ausdrücklich mit leerem Finanzmapping;
ältere implizite finanzielle Tickausgänge werden nicht als aktuelle Inputs
übernommen. LONG/SHORT stammt aus ENTER_LONG/ENTER_SHORT. Fehlt der angeforderte
Entry oder bezeichnet der Fixture-State keine unterstützte Armed-Seite, entsteht
keine finanzielle Vergleichsbindung.

## Deklarierte synthetische Rechendaten

Die beiden Standard-Financial-Fixtures tragen einen ausdrücklich im Harness
deklarierten Testkontext: Referenzpreis 100, Schutzstop 98, Testequity 1000,
Scope- und Tradegrenze jeweils 120, Gesamtgrenze 240 und verbleibendes
Tagesverlustbudget 6. Es sind neu deklarierte synthetische Rechendaten; sie
stammen weder aus einem Konto noch aus einer früheren Kontosicherung und werden
nicht in die Betriebskonfiguration geschrieben.

Der vorhandene neutrale lineare Instrumentadapter verwendet Kontraktmultiplikator
eins und Losgröße 0,01. In diesem synthetischen Beispiel teilen Preis und
Kapitalfelder denselben Rechennumeraire. Ein FX-/Währungsfluss eines wirklichen
Kontos wird damit nicht belegt. Der Originalowner berechnet 1,20 native Einheiten
und Notional 120. Wird die explizite Scopegrenze auf 80 gesetzt, verbrauchen
Original-Sizing und der nachfolgende Original-Intent tatsächlich 0,80 Einheiten.
Dieser Gegenversuch prüft den numerischen Verbrauch der Inputfelder.

Vor dem Bindungsaufruf müssen der exakte Kontexttyp, OFFLINE_ALGEBRA,
Instrumentidentität und Referenzpreis des ausgewählten tatsächlichen Ticks passen.
Stop, Kapital und Mengenbedingungen werden weiterhin vom Originalowner bewertet.
Die deklarierte Fixture ist weder ein Account-State-Producer noch produktive
Risikopolicy oder wirtschaftliche Survival-Herleitung.

## Vergleich und nachgewiesene Grenze

Beide Vergleichszweige übergeben denselben expliziten Kontext an ihre bestehenden
direkten beziehungsweise Szenarioadapter. Der Vergleich verlangt jetzt zusätzlich
den gleichen Entscheidungs-Ausgang, Mengenstatus sowie Mengen-, Risiko- und
Intentreferenzen. Der positive Finanzpfad benötigt einen zulässigen Mengenstatus
und vorhandene Referenzen; gleiche BOUND_OFFLINE-Labels reichen nicht.

Die [neuen Fälle](../../../tests/trading/master_v2/test_surface_p_explicit_financial_context_v1.py)
prüfen unter anderem fehlende/fremde Kontexte, falsche Referenzpreise, nicht
unterstützte Modi, erschöpftes Kapital, fehlenden Stop, Referenzabweichungen trotz
gleicher Label und fehlende Tickkontexte ohne Rückfall auf isolierte Kontowerte.
Die bestehenden drei fehlgeschlagenen Prüfungen bleiben unverändert enthalten.

Der mehrtaktige Standarddatensatz liefert keinen SHORT-Entry. Diese Abwesenheit
bleibt ausdrücklich gesperrt. Die SHORT-Adapterfälle verwenden einen gesondert
durch die heutige kanonische Composition-/Entry-Policy berechneten SHORT-Ausgang
als synthetischen Gegenversuch; sie belegen keinen natürlich erreichten
SHORT-Zyklus des Standarddatensatzes.

Ein bestandener Surface-P-Fixturevergleich ist ein Offline-Adapterbefund.
Backtest- und Runtime-Referenzlanes sowie die übrigen Fixturepfade behalten ihre
bisherigen Rollen. Daraus folgen keine neue vollständige kanonische Hostkette,
empirische Wirtschaftlichkeit, aktuelle Account-/Zeit-/Inputadmission oder
produktive numerische Risikozulassung. Der integrierte Replayowner, dessen feste
Survivalinputs, die finanzielle Risikoformel, produktive Gates und reale Zustände
werden durch diese Reparatur nicht geändert. Runtime bleibt BOUND_NOT_ACTIVATED;
Ausführungs- und Adaptereligibility bleiben false und Authority NONE.

## Manifestabhängige positive und negative Prüfungen

Der erweiterte Ownerlauf erfasste außerdem sieben positive Tests, die ein
bestimmtes datiertes Archivmanifest als vorhanden und verifiziert voraussetzten.
Das Manifest fehlt im heutigen Bestand; der unveränderte Manifestowner liefert
daher korrekt einen fehlenden Nachweis und false für die finalen Erfolgsflags.
Diese Tests erhalten jetzt eine ausdrücklich temporäre aktuelle Testquelle:
ein synthetischer Record bindet die tatsächlichen aktuellen Adapterquellen,
sein echtes SHA-256-Manifest wird mit dem vorhandenen Dateiverifier geprüft.
Der Rückgabecode des Verifiers wird nicht gemockt.

Nur die jeweiligen positiven Tests verwenden dieses per Test zurückgesetzte
Verzeichnis. Ihre bisherigen positiven Assertions bleiben erhalten; zwei
Testnamen benennen jetzt die ausdrücklich eingesetzte Fixture statt einer
angeblich vorhandenen globalen Standardquelle. Zusätzliche negative Fälle
belegen die Sperre bei fehlendem Verzeichnis und bei tatsächlich nachträglich
verändertem Record. Ein grüner Renderer-/Flagtest unter diesen Inputs bedeutet
keine globale Quelle oder freigegebene Systemkette. Das produktive/defaultmäßige
Manifestziel und der Manifest-/Flagowner werden nicht geändert, alte Belege
nicht restauriert und keine Erfolgsflags direkt gesetzt.

Der [Prüfbeleg](../evidence/CURRENT_OFFLINE_PARITY_EXPLICIT_FINANCIAL_CONTEXT_2026_11_08.md)
bindet die konkreten aktuellen Quellen und den gemeinsamen Ownerlauf.
