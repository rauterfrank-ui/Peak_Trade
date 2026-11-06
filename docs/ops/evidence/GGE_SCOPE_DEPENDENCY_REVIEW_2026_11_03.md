# GGE, feste Scope-Grenzen und Lernabhängigkeiten — 03.11.2026

docs_token: DOCS_TOKEN_GGE_SCOPE_DEPENDENCY_REVIEW_2026_11_03

Status: begrenzte historische und statische Untersuchung mit ausführbarem Gegenbeispiel. Keine Runtimeänderung, keine Datenmigration, keine Aktivierung. Quellrevision: `94f2eebc26fe378a9beaea820b09e872605b1f3e`. Bindung der untersuchten Dateien: `binding_manifest.json` im gleichnamigen Evidence-Ordner.

## Ergebnis

Ein fester absoluter Scope ist für die GGE-Formel nicht erforderlich. Er kann aber nicht durch bloßes Löschen alter Zahlen verlässlich aus der heutigen Gesamtkette entfernt werden. Die instrumentrelative Initialisierung nutzt bereits GGE; ein nichtdelegierter Trailing-Pfad begrenzt kleine Werte weiterhin auf 1. Der P5-Vorschlag verwendet dagegen rohe GGE-Distanzen, wird aber nicht in jedem Zyklus/Startpfad angefordert. Ein einheitlicher vorhandener Konfigurationsschalter für beide Pfade ist nicht gefunden.

Franks Zielrichtung: eine Variante ohne feste wirtschaftliche Scope-Grenze untersuchen, in der GGE die Distanz liefert und Empfänger sie konsistent verwenden. Unbekannte Herkunft alter Lerndaten ist weder Beweis falscher Werte noch ein Grund, die alte Begrenzung dauerhaft zum Zielvertrag zu machen. Vor der Umstellung müssen Datenidentität und tatsächlich wirksame Consumer geklärt sein.

## Historische Konstruktion

- [PR 7036](https://github.com/rauterfrank-ui/Peak_Trade/pull/7036), Merge `a21362ab9236e28bc3512b8a02c84a0dda93c882`, 03.10.2026: produktive Initialisierung von absolutem Fenster 50/500 auf instrumentrelative Policy umgestellt. Das ist ein konkreter historischer Treffer zur geschilderten Future-übergreifenden Fehlinterpretation; keine nachträglich erfundene neue Formel.
- Ursprüngliches GGE-Arbeitspaket vom 06.10.2026: lokale Quellensammlung `gge-source-collection-2026-11-02&#47;sources&#47;gge-original-cursor-workpackage.txt` unter `/Users/frnkhrz/Documents/ChatGPT/PeakTrade Reconstruction`. Historischer Auftrag, keine neue Ausführungsanweisung. Gewünschter Owner: Markt-/Volatilitätsinformation → Basisdistanz; nicht die gesamte Double-Play-Zustandsmaschine.
- [PR 7064](https://github.com/rauterfrank-ui/Peak_Trade/pull/7064), Merge `dd4c23da1f3f519413fe8c9f04ddd0050ff3f026`, 06.10.2026: bestehende Formel Volatilität × Markpreis in GGE als gemeinsamen Owner gebündelt. Der ursprüngliche Commit `4e4711452fa2a3b6de86e6421a7e58ea2f25bd86` ersetzte auch im Trailing die Inline-Berechnung; das nachgeschaltete Clamping blieb bestehen.
- [PR 7090](https://github.com/rauterfrank-ui/Peak_Trade/pull/7090), Merge `f87032845fd21c0deb6aee0bddb553be9a43691f`, 12.10.2026: Skalenprüfung und GHV-/L10-Beobachtung, keine neue GGE-Formel. Historische PASS-Aussagen sind keine vollständige heutige Consumer-Prüfung.

## Konkreter aktueller Gegenfall

`integrated_offline_trading_logic_replay_v1._rules_for_cycle_v1` erzeugt instrumentrelativ eine Untergrenze 0; `_runtime_envelope_containing_scope_v1` setzt jedoch die statische Mindestdistanz 1. `double_play_state.clamp_band_width` kombiniert beide Grenzen und gibt bei widersprüchlichem Fenster sogar die Untergrenze zurück. LONG/SHORT-Trailing nutzt dieses Ergebnis.

Ausführbare Probe mit tatsächlicher Initialisierung, Replay-Hilfsfunktionen und Trailing-Funktion, synthetischen gültigen Marktdaten und Volatilität 0,02:

- Markpreis 0,02: GGE und Initialisierung 0,0004; LONG-/SHORT-Trailing 1.
- Markpreis 1: GGE und Initialisierung 0,02; LONG-/SHORT-Trailing 1.
- Markpreis 50.000: GGE, Initialisierung und Trailing 1.000; keine feste Obergrenze 500 in diesem instrumentrelativen Pfad.
- NEUTRAL behält den zuvor gesetzten Zustand; der Befund gilt nicht pauschal für alle Zustände.

Evidence: `current_scale_probe.json`. Das ist ein Gegenbeispiel innerhalb der realen Helper-Kette, kein vollständiger produktiver Zyklus und kein Test des delegierten P5-Pfads.

P5 `productive_cycle_bind_seam_v1` setzt den expliziten D_t-Vorschlag direkt auf die GGE-Distanz und protokolliert `global_usdt_clamp=none`. Der Wiring-Helper fordert den delegierten Pfad nur bei aktivem Bind, vorhandenem Store und bestehendem Scope-Carrier an. Bootstrap/fehlender Store bleibt im anderen Pfad. Ein bloßes Einschalten dieser Option ist daher kein vollständiger Ersatz; künstliche Scope-Carrier oder Metadaten würden den Beweis umgehen.

## Verfolgte Abhängigkeiten

1. **Scope-Zustand und Entscheidungen:** geclampte Distanz verändert Trailing-Grenzen; Scope-Ereignisse gelangen in die Double-Play-Auswertung. Statischer Consumer-Zusammenhang plus numerischer Helper-Gegenfall; konkrete spätere Orderwirkung hier nicht ausgeführt.
2. **Stops/Risikobemessung:** `current_productive_enter_live_29p_join_v1.resolve_current_productive_live_29p_adverse_exit_distance_v1` bezieht die adverse Distanz aus der aktuellen Layer-C-/GGE-Bindung; der Aufrufer verwendet sie zur Stopableitung. Zustandsbehaftetes Trailing und frisch abgeleitete Stopdistanz müssen bei der Umstellung gemeinsam geprüft werden. Nicht jede Zahl stammt aus dem alten Festfenster.
3. **Aufzeichnung:** `current_productive_master_v2_ddo_learning_capture_join_v1` übergibt `replay.intermediate.scope_event` an `record_productive_cycle_capture_v0`; dessen Seam `core.dynamic_scope` erzeugt DecisionEvents. Diese Aufzeichnung ist beobachtend und verändert die Entscheidung nicht.
4. **Herkunftslücke:** generisches Capture setzt `code_sha=UNKNOWN` und verwendet nur einen eventuell vorhandenen `config_digest`. Der Lern-Ingest-Namensraum wird aus Session und Account abgeleitet; eine Scope-Policy-Version ist dort nicht enthalten. Der Reducer prüft Referenzen, Zeit, Fingerprint und Outcome-Provenienzklasse, aber keine Gleichheit alter/neuer Scope-Konfiguration. Im Ingest-Aufruf werden Code-/Config-Defaults nicht überschrieben. Das ist eine konkrete fehlende Isolation an diesem Übergang, kein Beweis tatsächlich vermischter Trainingsläufe.
5. **Vorhandener Datenbestand:** ein gezielt gelesener lokaler Ledger enthält 742 Payloads, darunter 56 Scope-DecisionEvents und 3 Lernzustände. Alle 56 Scope-Ereignisse haben unbekannten Konfigurationshash; alle 3 Lernzustände unbekannten Code-SHA und Konfigurationshash. Die Lernzustände tragen die vorhandene Klasse `OBSERVED_PRODUCTIVE_PRE_EXTERNAL`; diese Klassifikation wurde hier nicht unabhängig zertifiziert. Bestandsaufnahme entpackt ausdrücklich die Ledger-Envelopes. Keine Kontokennungen oder vollständigen Payloads exportiert. Evidence: `capture_dependency_inventory.json` mit Quellhash.
6. **Forensische Rekonstruktion:** GHV-Scope-Traces speichern Raw-Distanz, effektives Band, Schwellen, Zustände, Instrument und Repository-SHA. Das ist ein brauchbarer Ansatz für eine spätere Rekonstruktion durch stabile Cycle-/Decision-IDs. Unterschiedliche Raw-/Effective-Werte allein beweisen wegen Zustand/Zeitbezug keinen Clamp. Eine vollständige Verknüpfung aller 3 Lernzustände zu genauen historischen Scope-Regeln ist noch offen.
7. **Optimierung/Forschung:** `canonical_optimization_universe_learning_input_v1` nimmt Learning-Evidence für Offline-Forschung an; es besitzt in diesem Vertrag keine produktive Config-/Such-/Promotionsautorität. Historische Multi-Future-Lab-Fixtures enthalten weiterhin 50/500 sowie 200/80/120 und kontrafaktische Hard-Max-Varianten. Das sind datierte Vergleichsmodelle, keine automatische heutige Runtimeautorität. Alte Experimente dürfen nicht still umetikettiert werden.

## Prüfergebnis und nächste konkrete Umstellung

79 bestehende Tests PASS: 67 GGE-/Raw-Scope-/Trailing-Tests und 12 Learning-Ingest-/Provenienztests. Die grünen Tests schließen das gezeigte Min-1-Gegenbeispiel nicht aus. JUnit-Dateien liegen im Evidence-Ordner. Kein neuer Nachweis für Profitabilität, Gesamtsemantik oder GitHub-CI.

Eine konsistente Variante ohne feste wirtschaftliche Scope-Grenze benötigt:

1. Einen explizit versionierten Vertrag für GGE-Einheiten, Volatilitätsbedeutung, Instrument-/Zeitbindung, tatsächlich verwendete Distanz und Initialisierung/Restart/Instrumentwechsel. Positive endliche Eingangswerte weiter validieren; fehlende oder ungültige Daten dürfen nicht durch eine erfundene Distanz ersetzt werden.
2. Dieselbe Distanzsemantik in Bootstrap, nichtdelegiertem Trailing und delegiertem L1–L10-Pfad; die Min-1-Hilfskette gezielt ersetzen statt nur 50/500-Textstellen löschen. Bestehende C3-/Bestätigungs-/Risikoregeln separat fachlich prüfen.
3. Scope-Policy-/Config-Identität an Decision, Outcome und Lernzustand durchreichen. Vorhandene unklare Bestände unverändert erhalten; ihre Übernahme anhand rekonstruierbarer Herkunft entscheiden. Für neue Daten eine explizite Versions-/Epochentrennung oder eine gleichwertig belegte Auswahlgrenze verwenden. Hier noch nicht implementiert.
4. Paired Replays mit kleinen/großen Preisen sowie Bootstrap, LONG, SHORT, NEUTRAL, Restore und Instrumentwechsel; Wirkung auf Events, Stopdistanz, Sizing, Outcome und Lernzuordnung verfolgen. Vergleiche müssen erwartete fachliche Änderungen von unbeabsichtigten Vertragsbrüchen unterscheiden.
5. Betroffene aktive Policies, Runbook-/Map-Quellen und Prüfungen gemeinsam umstellen; historische Originale unverändert lassen. Keine Aussage, dass alle Repo-Consumer schon vollständig erfasst sind.

Aktuelle Entscheidung: feste Grenzen nicht als notwendiges Ziel des neuen Systems übernehmen; Entfernung noch nicht vollzogen. Die vollständige Datenherkunfts-/Consumerprüfung und der anschließende konsistente Cutover bleiben offen. Externe Laufwerke wurden in diesem Schritt nicht erneut breit durchsucht, weil lokale Git-Revisionen, PRs und bereits rekonstruierte GGE-Originalquellen die konkrete historische Frage belegen.
