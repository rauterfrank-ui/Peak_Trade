# AI & Workflow Ideas

Hier sammeln wir Ideen für **AI-Assistenten, Agenten, Prompt-Bibliothek, Automatisierung von Runbooks & Reports**.

| ID          | Titel                                | Tier | Score | Status   | Kurzbeschreibung                                     |
| ----------- | ------------------------------------ | ---- | ----- | -------- | ---------------------------------------------------- |
| IDEA-AI-002 | InfoStream v0 Intel-Pipeline         | T1   | 9     | **ACTIVE** | Meta-Layer für Automation-Learnings & Makro-Intel    |
| IDEA-AI-001 | AI-Agent für Runbook-Automatisierung | T3   | 6     | NEW      | Agent, der Runbooks & Checks automatisch anstößt.    |
| IDEA-AI-003 | InfoStream v1 Python-Modul           | T2   | 7     | BACKLOG  | `src/meta/infostream/` mit IntelEvent Dataclass      |
| IDEA-AI-004 | InfoStream v2 HTML-Dashboard         | T3   | 5     | BACKLOG  | Tailwind-Dashboard mit Filter & Export               |

## IDEA-AI-002: InfoStream v0 (ACTIVE)

**Status:** Implementiert (Dezember 2025)

Der InfoStream ist ein leichter Meta-Layer, der:
- Auswertungen aus verschiedenen Quellen sammelt (TestHealth, TriggerTraining, Makro/GeoRisk)
- Sie in standardisierte INFO_PACKETs umwandelt
- An einen KI-Datenauswertungsspezialisten weitergibt
- EVAL_PACKETs + LEARNING_SNIPPETs extrahiert

**Dokumentation:**
- [InfoStream README](../infostream/README.md)
- [KI-Prompts](../infostream/PROMPTS.md)
- [Templates](../infostream/TEMPLATES.md)
- [Learning-Log](INFOSTREAM_LEARNING_LOG.md)

**Hilfs-Script:**
```bash
python scripts/create_info_packet.py --interactive
```

---

*(Weitere Zeilen nach Bedarf hinzufügen.)*
