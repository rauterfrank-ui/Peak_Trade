## Execution Watch v0.3 fixtures

Diese Fixtures werden von `tests/live/test_execution_watch_api_v0_2.py` genutzt, um
deterministische v0.3-Semantik zu prüfen:

- **empty**: effektiv leeres JSONL (nur Whitespace-Zeile)
- **malformed**: genau eine ungültige JSONL-Zeile zwischen validen Events (read_errors==1)
- **tail**: Run mit mehreren Events für `since_cursor`/Tail-Mode
