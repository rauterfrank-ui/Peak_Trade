# Pending-Creation: fehlenden Entscheidungskontext ausdrücklich abweisen

Basis: 6a0e11e61ade0b83a5ee38cdc67835e9a2db1af4

Der weitere normale Datenflussabgleich zeigt eine unabhängige offene Kontextbindung: Der Launcher startet Entscheidungstimestamp und Referenzpreis mit null. Zeit wird aus dem ausgewählten S5-Record übernommen; Preis dagegen aus dem letzten gefundenen ENTER der optionalen GHV-Trace-Datei, ohne Abgleich dieses Trace-Records mit der ausgewählten DPO-/Zyklusidentität. Ohne Trace bleibt null erhalten. Dies ist statisch belegt, kein neu beobachteter natürlicher Fehlabschluss.

Die neue strikte Storeprüfung wies solche Werte bereits zurück, ließ den Fehler aber bis zum Speicherversuch laufen. Jetzt prüft die Pending-Creation gültige positive endliche Zeit und Preis vor jedem Zugriff/Schreibversuch. Fehlender oder ungültiger Kontext liefert PENDING_DECISION_CONTEXT_UNBOUND, created=false, skipped=true. Kein Null-Ersatz, keine aus einem fremden Zyklus entliehene Zahl, keine neue Zeit-/Entry-Regel und kein künstlicher Outcome. Ein bereits gültiger Kontext läuft unverändert durch. Die Aufnahmeprüfung beweist noch nicht die korrekte Herkunft einer positiven gelieferten Zahl.

Semantische Abgrenzung: Der allgemeine DDO-DecisionEvent-Typ darf nicht allein als genauer Double-Play-Entry-Typ gelesen werden. Die existierende Projektion hält den exakten Producer-outcome in der DPO; Enter wird im allgemeinen Typ nicht durch eine neue Enum-Erweiterung nachgebildet. Deshalb wurde aus einer NO_ENTRY-/UNKNOWN-Bezeichnung allein kein neuer verbindender Adapter konstruiert. Konkrete DPO, Eltern-Decision, S5-Zyklus, Instrument, Preis- und Zeitquelle müssen gemeinsam weiter gebunden werden.

Prüfung: zwölf neue Fälle scheiterten vor der Korrektur, 55 Fälle im anschließenden Scope bestanden, darunter alle zwölf neuen sowie vorhandene gültige Creation-/Closure-/Messartefaktfälle. Keine redundante Wiederholung der vollständigen vorigen Scopes. Ruff/Format geprüft. Ursprüngliches Lernledger unverändert; keine Netzwerk-/Konto-/Dienst-/Handelsaktion.

Weiter offen: tatsächlicher kanonischer Preislieferant im normalen Lauf ohne optionalen Forensic-Trace; genaue Zyklus-/DPO-/Episodebindung und mehrdeutige alte Korrelationspfade. Nicht voreilig einen gleichnamigen Trace oder fremden Mark als passende Quelle übernehmen. Unabhängige Meta-, MI-, G2- und Optimierungsfragen bleiben erhalten. Gesamtsystem noch nicht abgeschlossen.

[Quellbindungen](receipt.json), [Vorher](before.xml), [55 bestandene Fälle](after.xml).
