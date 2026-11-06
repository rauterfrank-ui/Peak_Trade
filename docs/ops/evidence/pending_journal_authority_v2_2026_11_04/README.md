# Pending-Journal vor abgeleitetem Index

Basis: 2a9d6e95c4962be5ca6739a892712d62ce537f12

Das vorhandene Pending-Journal ist jetzt maßgeblicher Zustand. Zuvor schrieb persist_record den abgeleiteten Index vor dem Journal; Leser konnten dadurch verlorene Inputs übersehen oder aus einem fehlenden Index einen leeren Zustand ableiten. Jetzt prüft der Store vollständige JSONL-Rahmung, Schema, Record-/Eventidentität, Genesis, unveränderliche Metadaten, Fortschritt und Terminalübergänge. Fehlender Index wird nur im Speicher rekonstruiert; ein beschädigter Index wird beim Lesen nicht umgeschrieben. Fehlendes Journal bei vorhandenem Index bleibt gesperrt.

Der bestehende Store bleibt Owner. persist_record serialisiert kooperierende lokale Writer mit Kernel-flock und vergleicht unter diesem Lock den erwarteten Vorzustand. Erst erfolgreicher Journal-Append/Flush/fsync, dann abgeleitete Indexveröffentlichung. Fehlgeschlagener Index-Write lässt den bestätigbaren Journalstand erhalten; dieselbe Markbeobachtung wird beim Wiederholen nicht doppelt angehängt. Stale Writer können neuere Aufzeichnungen nicht überschreiben. Resolver-Replay nutzt nun denselben validierten Journalreader.

Prüfung: neun anfängliche neue Fälle scheiterten am Vorhercode. Final 79 PASS im verbundenen Scope, darunter 15 neue Storefälle. Ein Kindprozess wird nach fsync des echten Mark-Appends und vor Indexveröffentlichung mit SIGKILL beendet. Ein neuer kanonischer Python-Prozess rekonstruiert den Sample-Bar, erkennt Wiederholung und kann danach unter dem freigegebenen Kernel-Lock fortsetzen. Weitere Fälle: Indexverlust/-korruption, Append-/Indexfehler, torn/malformed Journal, fehlende Pflichtfelder, fremde Identität/Version, konkurrierender Writer und veralteter Vorzustand. Alle Wurzeln sind temporär.

Grenzen: lokale kooperierende Writer, kein verteilter Lock oder uneinheitliches Alt-/Neuversionen-Protokoll. Reader während eines unvollständigen Appends können fail-closed stoppen. Kein kryptografischer Herkunfts-/Rollbackbeweis, keine Garantie gegen vollständigen Zustandswurzelverlust, Hostkernel-/Stromausfall oder gemeinsamen Commit mit dem getrennten DDO-Ledger. Originale werden nicht automatisch repariert oder abgeschnitten. Vollständige dauerhafte Messartefakte bleiben separat offen. Die vorherigen 30 Downstream-PASS werden unverändert wiederverwendet, nicht erneut addiert oder ausgeführt. Kein echter Datenlauf, Credentialzugriff oder Betriebsstart.

[Quell-/Prüfbindungen](receipt.json), [Vorherfälle](before.xml), [finaler Scope](final_scope.xml).
