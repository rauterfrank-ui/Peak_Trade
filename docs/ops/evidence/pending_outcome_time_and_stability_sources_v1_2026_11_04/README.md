# Cross-Session-Zeitbezug und unterschiedliche Stabilitätsverträge

## Vorhandenen Zwischenpfad nachverfolgt

Die Datenübergabe hat einen vorhandenen Natural-Enter-Cross-Session-Pfad. Original: 06.10.2026, Commit 29d4ccd52; Aufrufer ist der PRE_EXTERNAL-Launcher. Die Runtime-Titel und historische COMPLETE-Labels sind dabei keine End-to-End-Nachweise. Es wurde kein echter Launcher, Netzwerkzugang oder Beobachtungslauf gestartet.

Ein enger Replayfehler ist behoben: Der Reader addierte zu einem bereits gespeicherten Empfangszeitpunkt erneut eine Sekunde. Jetzt wird der gespeicherte Wert unverändert übernommen. Fehlt er, wird kein Ersatz aus Eventzeit plus Verzögerung erzeugt; der bestehende Reader kann diesen Eintrag nicht normalisieren. Alte Events werden nicht umgeschrieben. 26 Tests bestehen, darunter drei neue Fälle, die vorher scheiterten: gebrochene Sekunden, fehlender Empfangszeitpunkt und echter Event-Ledger→Bar-Replay in einem temporären Fixture-Verzeichnis.

## Weitere Nachweisgrenzen bewusst getrennt

Der kontrollierte bestehende Fixture-Pfad kann CLOSED erreichen, obwohl das letzte Mess-Bar-Ende noch 2.400 Sekunden nach der letzten gelieferten Beobachtung liegt. Der Source-Wrapper kombiniert einen aktuellen Markpreis mit der neuesten Candle-Öffnungszeit; ein kontrollierter abweichender Markzeitpunkt von 1.800 Sekunden wird nicht als Markzeit weitergegeben. Der Resolver übergibt beim Horizon-Capture außerdem den Decision-Zeitpunkt als producer_observed_at. Eine ausdrückliche TEST_FIXTURE-Kette erzeugt im temporären Ledger einen eingebetteten OBSERVED_PRODUCTIVE_PRE_EXTERNAL-Label. Diese Beobachtungen sind keine verifizierten natürlichen Ergebnisdaten und kein Nachweis tatsächlicher Verunreinigung des geschützten Ledgers. Dessen Hash bleibt unverändert.

Die neu erhaltenen Mess-/Informationsset-Artefakte liegen am Runtime-Ergebnis vor; der Closure-Store hält in diesem gelesenen Pfad Referenzen und keine neue vollständige Messartefaktablage fest. Das ist eine weitere gesonderte Persistenzgrenze.

Die übrigen Zeit-/Quell-/Klassifikationspunkte erfordern einen zusammenhängenden Abgleich von tatsächlichem Markereignis, Empfang, Bar-Finalisierung, Auswertungsgrenze und Quellbindung. Eine neue Ergebnisklasse oder ein zeitlich rückversetzter Ersatzwert wird hier nicht erfunden. Die vom Owner zurückgestellten echten Quellen-/Aktualitätsnachweise bleiben offen. Der Replayfix allein schließt sie nicht.

## Stabilität ist nicht durch denselben Namen verbunden

Sechs heutige Pfade wurden nach Wertart, Formel bzw. Consumerrolle abgeglichen. Meta und Portfolio erwarten numerische Inputs; der Max-Age-Runner liefert unter demselben Namen ein Ablehnungsobjekt. Die Robustness-Suite prüft gelieferte Sharpe-Punkte/Vorzeichenwechsel/Nachbarverschlechterung. Die lineare Diagnostik berechnet tatsächlich Zahlen, darunter Richtungskonsistenz und Response-Varianz, auf einer anders gebundenen Kosten-/Surrogatfläche. Research-Validity bindet Referenzen, Digests und Status. Weder ein boolesches PASS noch der zufällig zur 0,5-Schwelle passende binäre Richtungswert wird stillschweigend zum originalen Meta-Stabilitätsmaß.

[Quellenrollen](stability_source_roles.json) halten die noch fehlende fachliche Identität fest. Das ist keine globale Aussage, es gebe nirgends eine Formel oder einen Adapter. Aktuelle Symbole einschließlich ignorierter Pfade und gezielte datierte Index-Treffer wurden zur Navigation verwendet; nicht alle historischen Chats oder externen Quellen wurden neu gelesen. Weiterarbeit an unabhängigen Kanten bleibt möglich.

[Kontrollierte Zeitprobe](temporal_source_probe.json), [ausführbarer isolierter Probequelltext](temporal_source_probe.py.txt), [Quellen und Prüfungen](receipt.json), [Blueprint Abschnitte 46/47](../../blueprints/PEAKTRADE_SYSTEM_RECONFIGURATION_BLUEPRINT_2026_11_03.md).
