# Workflow Notes Frontdoor

**Purpose:** Navigate workflow documentation and understand docs-reference-targets-gate compliance.

---

## 📚 Available Workflow Notes

### Historical Workflow Documentation
- **[PEAK_TRADE_WORKFLOW_NOTES_2025-12-03.md](PEAK_TRADE_WORKFLOW_NOTES_2025-12-03.md)**  
  Historical workflow notes from 2025-12-03 documenting:
  - Technical architecture snapshot
  - ChatGPT ↔ Claude Code workflow
  - Prompt engineering patterns
  - Planning for next development blocks

---

## 🔧 Docs-Reference-Targets-Gate Compliance

### Policy: Illustrative Path Encoding

**Why:** The `docs-reference-targets-gate` CI check verifies that all file paths mentioned in docs actually exist in the repository. This prevents broken references.

**Challenge:** Documentation often includes **illustrative example paths** that don't exist (e.g., `config/my_custom.toml`, `scripts/my_example.py`).

**Solution:** Use HTML entity encoding (`&#47;`) to neutralize illustrative paths:
- Replace `/` with `&#47;` in inline code spans (single backticks)
- This prevents the gate from treating illustrative examples as real file references
- Rendered output remains visually identical

### Examples

#### ✅ Real Repository Path (Keep As-Is)
```markdown
Real file: `src/strategies/ma_crossover.py`
```
**Why:** This file exists in repo → gate should track it

#### ✅ Illustrative Path (Neutralize)
```markdown
Example config: `config&#47;my_custom_backtest.toml`
```
**Why:** This is a hypothetical example → neutralize to avoid gate false positive

**Rendered:** Both display identically in GitHub/Quarto, but only real paths trigger the gate.

### When to Neutralize

**✅ Neutralize these:**
1. **Hypothetical examples** in tutorials
   - `config&#47;my_custom.toml`
   - `scripts&#47;my_example.py`
2. **Template paths** showing patterns
   - `data&#47;backups&#47;YYYY-MM-DD&#47;`
3. **Placeholder paths** in workflows
   - `logs&#47;session_12345&#47;`

**❌ Don't neutralize these:**
1. **Actual repository files**
   - `src/core/config.py`
   - `config.toml`
2. **URLs** (exempt from gate)
   - `https://example.com/path/to/file`
3. **Fenced code blocks** (usually safe)
   - Unless they contain standalone path references

### Quick Test
```bash
# Is this path in repo?
ls -la path/to/file

# If exists → Keep as-is (real path)
# If not exists → Neutralize with &#47; (illustrative)
```

---

## 🔍 Troubleshooting Gate Failures

### Symptom: CI Check "docs-reference-targets-gate" Fails

**Error message example:**
```
Missing targets: 3
  - /path/to/docs/file.md:42: config/my_example.toml
  - /path/to/docs/file.md:58: scripts/my_script.py
```

**Diagnosis:**
1. Check if paths are real or illustrative:
   ```bash
   ls -la config/my_example.toml  # Does it exist?
   ```

2. If illustrative → Neutralize:
   ```bash
   # Before:
   `config/my_example.toml`

   # After:
   `config&#47;my_example.toml`
   ```

**See also:** [RUNBOOK_DOCS_REFERENCE_TARGETS_FALSE_POSITIVES.md](../runbooks/RUNBOOK_DOCS_REFERENCE_TARGETS_FALSE_POSITIVES.md)

---

## 📖 Related Documentation

### Workflow & Operations
- [Ops Hub](../README.md) – Operations center
- [Documentation Frontdoor](../../README.md) – Main docs navigation
- [WORKFLOW_RUNBOOK_OVERVIEW](../../../WORKFLOW_RUNBOOK_OVERVIEW_2026-01-12.md) – Comprehensive workflow runbook

### Developer Workflows
- [DEVELOPER_WORKFLOW_GUIDE.md](../../DEVELOPER_WORKFLOW_GUIDE.md) – Developer workflows
- [DEV_WORKFLOW_SHORTCUTS.md](../../DEV_WORKFLOW_SHORTCUTS.md) – Productivity shortcuts

### Governance & Policy
- [DOCS_REFERENCE_TARGETS_GATE_STYLE_GUIDE.md](../DOCS_REFERENCE_TARGETS_GATE_STYLE_GUIDE.md) – Gate style guide (if exists)
- [DOCS_REFERENCE_TARGETS_IGNORE.txt](../DOCS_REFERENCE_TARGETS_IGNORE.txt) – Exemption list

---

## 🚀 Quick Start

**For workflow documentation authors:**
1. Read this frontdoor
2. Follow the illustrative path policy
3. Test locally: `./scripts/ops/verify_docs_reference_targets.sh --changed`
4. If gate fails → See troubleshooting section above

**For workflow document consumers:**
- Start with [PEAK_TRADE_WORKFLOW_NOTES_2025-12-03.md](PEAK_TRADE_WORKFLOW_NOTES_2025-12-03.md)
- Paths with `&#47;` are illustrative examples (rendered as `/`)
- Copy commands from rendered view (GitHub UI), not raw Markdown

---

**Last Updated:** 2026-01-13  
**Maintained By:** Peak_Trade Docs Team  
**Policy:** Minimal-invasive integration, KEEP EVERYTHING principle
