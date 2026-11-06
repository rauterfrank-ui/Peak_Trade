---
title: "Wiederanlauf und Stromausfall"
stand: "2026-11-06"
rolle: "Quellgebundener Standabgleich ohne Betriebsautoritaet"
authoritaet: "NONE"
---

# Wiederanlauf und Stromausfall

Franks gewünschter Betriebsfall: Strom fällt aus, das System ist aus; nach erneutem Anschluss soll der Betrieb wieder aufgenommen werden. Dieser Wunsch bleibt als eigenständige Betriebskette sichtbar. Der Dokumentabgleich aktiviert keinen Dienst und ändert keine Recoverypolicy.

## Bedeutung der 50 und 100

Im konkret zurückverfolgten E6-Forschungsbeleg sind 50 und 100 Werte des langsamen MA-Strategiefensters slow_window. Der zweite 50er-Vorschlag wird als Duplikat verworfen; 100 wird neu gemessen. Das sind keine Spannungs-, Boot-, Retry- oder Recoveryparameter. Das E6-Paket enthält außerdem eigene Wiederanlaufbelege, die getrennt zu beurteilen sind. [[00 Systemindex/Intelligentes Universum/Verstaendnis nach Aussenkanten/09 Konkrete Werte bis zum Ursprung|Die vollständige Ursachenrekonstruktion]]

## Die benoetigten Betriebsebenen

Stromversorgung und Hardwarestart müssen nach Rückkehr der Versorgung tatsächlich wieder verfügbar sein. Darauf müssen Betriebssystem und zuständiger Dienst starten. Erst danach kann der richtige Host mit seinem ursprünglichen Profil, Store, Cursor, Budget und Datasetgeneration die Persistenz aufnehmen. Admission, Reconciliation und Safety müssen den verbliebenen Zustand prüfen, bevor ein erlaubter Fachschritt fortgesetzt wird. Diese Ebenen sind nicht durch ein einziges COMPLETE-Label ersetzt.

## Was die vorhandenen lokalen Tests zeigen

Die begrenzte E6-Komposition enthält sieben tatsächliche Prozessabbruchgrenzen sowie einen frischen Prozess, der originale Zahlen und Evaluation ohne erneuten Engineaufruf zurückliest. Das ist konkret stärker als bloße Dateiexistenz, bleibt aber ein kontrollierter Prozess-/Offlinebeleg.

Native Research-Recovery unterscheidet den originalen PREPARED-Zustand von einem davor unklar abgebrochenen Versuch: Ein sicher vorbereiteter Originalrequest kann ohne neue Engine fortgesetzt werden; unklarer Fortschritt vor PREPARED blockiert. Sessionbudget unterscheidet abgeschlossene, bereits belastete und unvollständige Versuche. Ein belasteter unfertiger Versuch darf nicht automatisch als neuer kostenfreier Versuch wiederholt werden. Automatisches Fortsetzen ist daher nicht in jedem Zustand die korrekte Reaktion.

## Was fuer den gewuenschten Stromfall noch fehlt

Eine tatsächlich geprüfte Kette Strom weg → persistente Medien konsistent → Versorgung zurück → Rechner bootet → Dienst startet → richtige ursprüngliche Generation aufgenommen → fachlich erlaubte Fortsetzung ist aus diesen Belegen nicht vollständig ableitbar. Hardware-/OS-Start und Dienstregistrierung wurden in diesem Abgleich nicht untersucht. Die vorhandenen Prozessabbrüche werden nicht rückwirkend zu physischen Stromausfalltests umbenannt.

## Quellen und vorhandene Owner

- [Research-Preflight-Recoverytests](/Users/frnkhrz/Peak_Trade/tests/experiments/test_research_preflight_recovery_v1.py)
- [Physische Prozessabbruchtests](/Users/frnkhrz/Peak_Trade/tests/ops/test_bounded_offline_owner_crash_points_v1.py)
- [Session- und Budgettests](/Users/frnkhrz/Peak_Trade/tests/ops/test_bounded_offline_episode_session_v1.py)
- [E6-Systemepisoden und frischer Readback](/Users/frnkhrz/Peak_Trade/tests/ops/test_bounded_peaktrade_system_episodes_v1.py)
- [E4-Recoveryvertrag](/Users/frnkhrz/Peak_Trade/docs/ops/specs/BOUNDED_OFFLINE_STAGE_E4_RESEARCH_RECOVERY_V1.md)
- [Sessionvertrag](/Users/frnkhrz/Peak_Trade/docs/ops/specs/BOUNDED_OFFLINE_EPISODE_SESSION_V1.md)

[[00 Systemindex/Semantik/S11|Betriebssemantik]] · [[00 Systemindex/Aussenbereiche/HOST|Hostzuständigkeit]] · [[00 Systemindex/Repoabgleich/Standabgleich mit dem Repository|Standabgleich und Aussagegrenzen]]

<!-- Vollständige Leserprojektion; Original: system:00 Systemindex/Betrieb/Wiederanlauf und Stromausfall.md; SHA256: c849495ad199f98d135320c972d984e4a64b03642a91e50b39347c190bbd9d0d. Native Wikilinks beziehen sich auf den ursprünglichen Vault. -->
