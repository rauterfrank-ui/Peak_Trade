---
stand: "2026-11-05"
autoritaet: "NONE"
rolle: "Quellgebundene Rekonstruktion; vorhandene Ausführungsbelege begrenzt"
---

# Historisches Schichtenmodell aus dem originalen Toolauftrag

## Was konkret erhalten ist

Chat 962dd5c9-7680-4c10-b896-5554b595b8fe, JSONL-Zeile 94, enthält einen Shell-Toolauftrag mit einem eingebetteten Pythonprogramm. Darin stehen die vollständigen Literallisten layers und planes. Der wjson-Aufruf für 03_iu_layer_model_v1.json setzt daraus das Modell zusammen. Der vorherige Untersuchungseintrag82 datiert den Auftrag auf den 7.Oktober2026. Zeile 96 enthält die spätere Fertigmeldung; sie ist kein zusätzlicher unabhängiger Ausführungsbeweis.

Die Auslesung verwendet ast.literal_eval für reine Zuweisungen und einen ausschließlich auf Name/Constant/List/Tuple/Dict begrenzten Resolver für diesen Payload. Keine historische Shell, kein exec/eval, kein Originalskript, keine darin genannten Betriebsaktionen. Der unveränderte Schreibauftrag und die extrahierten Werte liegen als lesbare Belege im aktuellen Vault.

## Präziser Wiederherstellungsstatus

**Rekonstruiert:** historisch niedergeschriebener Dateninhalt von vierzehn Schichten, acht Planes sowie weiteren Literallisten für Roots, States, Config, Dispatch und Rückverbindungen. **Nicht wiederhergestellt:** unabhängig nachgewiesene Originaldateibytes auf dem damaligen Dateisystem. Kein früherer Originaldateihash liegt für den Vergleich vor. Kein Toolergebnis wird aus dem Toolauftrag erfunden.

Die später erhaltene 14-Schichten-Projektion an 110ae358 wurde als Gitblob geprüft. Layernamen und Owner sind mit dem Kandidaten abgleichbar. Übereinstimmung stärkt die Zuordnung; sie macht zwei abgeleitete Register nicht zu zwei unabhängigen Laufzeitbeobachtungen.

## Alte Fehlstellen präzisieren

„Nicht im lokal erreichbaren Git gefunden“ und „Datei an geprüften Orten fehlt“ bleiben zulässige Aussagen. „Inhalt nicht mehr rekonstruierbar“ wäre jetzt zu stark. Die gezielte Suche in beiden lokalen Checkouts und bekannten M2-Backupwurzeln fand die genaue fehlende Datei nicht. Nicht alle Unterordner, Chats, Recoverydaten oder ungeöffnete GHV-Quellen wurden vollständig erfasst; kein globaler Nichtexistenzbeweis.

Die Primärspur ist selbst ein analytisches Dossier vom Oktober. Sie beweist nicht, dass diese vierzehn Ebenen die allererste fachliche Konstruktion im April waren. Dafür bleiben das ältere Manifest und die damals vorhandenen Funktionsmodelle maßgebliche getrennte Quellen.

[Originaler Toolauftrag als Text](</Users/frnkhrz/Desktop/PEAK_TRADE_SYSTEM_AKTUELL/.belege/Systemindex/iu-historischer-schreibauftrag.txt>) · [Inerte Literalauslesung mit Provenienz](</Users/frnkhrz/Desktop/PEAK_TRADE_SYSTEM_AKTUELL/.belege/Systemindex/iu-historische-toolinput-rekonstruktion.json>).

[Zur IU-Übersicht](../vault_exact/00%20Systemindex/Intelligentes%20Universum/Intelligentes%20Universum%20rekonstruiert.md.json)
