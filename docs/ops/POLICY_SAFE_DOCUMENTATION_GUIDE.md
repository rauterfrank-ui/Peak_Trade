# Policy-Safe Documentation Guide

**Purpose:** Best practices for writing documentation that avoids Policy Critic false positives

**Audience:** Docs authors, Technical Writers, Engineers writing READMEs/Runbooks

**Status:** Active (v1.0)

**Last Updated:** 2025-12-31

---

## Quick Reference

**Problem:** Documentation containing literal examples of sensitive flags or patterns triggers Policy Critic blocks.

**Solution:** Use generic descriptions, pseudocode markers, or placeholder patterns instead of literal values.

---

## Policy-Safe Configuration Examples

### Quick Reference: Allowed vs. Disallowed Patterns

| Pattern Type | ❌ DISALLOWED (triggers Policy Critic) | ✅ ALLOWED (policy-safe) |
|--------------|---------------------------------------|--------------------------|
| **Live Trading Flag** | `enable_live_trading = true` | `enable_live_trading = false` (default)<br>`enable_live_trading = <BLOCKED>` (governance gate) |
| **Armed State** | `live_mode_armed = True`<br>`armed = true` | `live_mode_armed = false` (default)<br>`armed = <REQUIRES_APPROVAL>` |
| **Execution Mode** | `mode = "live"` with enabled flags | `mode = "paper"`<br>`mode = "shadow"`<br>`execution_mode = "LIVE_BLOCKED"` |
| **Narrative Language** | "turn on live", "enable live mode", "unlock live" | "manual sign-off required", "go/no-go decision", "governance approval gate" |
| **Config Examples** | Showing literal true values for sensitive flags | Use `false`, `<BLOCKED>`, `<PLACEHOLDER>`, or `{value}` |

### Standard Policy-Safe Config Snippets

**✅ Safe Config Example (Paper/Shadow):**
```toml
[environment]
mode = "paper"  # Safe default
enable_live_trading = false  # Governance gate (blocked by default)
```

**✅ Safe Config Example (Live-Blocked Design):**
```toml
[environment]
mode = "live"  # Design only
enable_live_trading = false  # Default: BLOCKED (requires governance sign-off)
live_mode_armed = false  # Gate 2: BLOCKED
execution_mode = "LIVE_BLOCKED"  # Explicit governance block
```

**❌ Unsafe Config Example (DO NOT USE in docs):**
```toml
# This will trigger Policy Critic:
enable_live_trading = true  # ⚠️ VIOLATION
live_mode_armed = True  # ⚠️ VIOLATION
```

---

## Documentation-Safe Patterns

### ✅ Safe Patterns (Use These)

1. **Generic Descriptions**
   - ❌ BAD: `enable_live_trading=true`
   - ✅ GOOD: "set the live trading flag to enabled"
   - ✅ GOOD: "live trading enablement (not shown here for safety)"

2. **Placeholder Syntax**
   - ❌ BAD: `LIVE_MODE=true`
   - ✅ GOOD: `LIVE_MODE=<value>`
   - ✅ GOOD: `LIVE_MODE={true|false}`

3. **Pseudocode Markers**
   - ❌ BAD: `live_mode = true`
   - ✅ GOOD: `live_mode = PLACEHOLDER_VALUE`
   - ✅ GOOD: `live_mode = (controlled by governance)`

4. **Redacted Examples**
   - ❌ BAD: Showing actual flag values in policy rule examples
   - ✅ GOOD: "Policy Critic scans for live enablement patterns"
   - ✅ GOOD: "Certain configuration flags require governance approval"

5. **Neutral Configuration References**
   - ❌ BAD: `armed=true`, `enable_live=true`
   - ✅ GOOD: "armed state flag", "live enablement configuration"
   - ✅ GOOD: "execution mode selector (SIM/PAPER/LIVE)"

6. **Credential Handling**
   - ❌ BAD: `API_KEY=sk_live_abc123`, `SECRET=xxx`
   - ✅ GOOD: `API_KEY=<your-api-key>`
   - ✅ GOOD: `SECRET=(stored in secrets manager)`

7. **Inline Comments for Context**
   - ❌ BAD: Literal sensitive strings without context
   - ✅ GOOD: Add comment: `# Example only - not for production use`
   - ✅ GOOD: Add comment: `# Placeholder - actual value controlled by governance`

8. **Documentation of Policy Rules**
   - ❌ BAD: Listing literal trigger patterns as examples
   - ✅ GOOD: Describe the rule intent without showing triggers
   - ✅ GOOD: Reference patterns as "certain sensitive keywords" or "specific flags"

9. **Code Blocks in Docs**
   - ❌ BAD: Executable code with live flags set to true
   - ✅ GOOD: Code blocks with placeholder values or commented-out sensitive lines
   - ✅ GOOD: Pseudocode showing structure, not actual values

10. **Risk/Live Path Documentation**
    - ❌ BAD: Step-by-step instructions showing how to enable live mode
    - ✅ GOOD: "Live enablement requires governance approval (see WP1A governance workflow)"
    - ✅ GOOD: "Live mode activation is blocked in Phase 0 by default"

11. **Test/Example Outputs**
    - ❌ BAD: Showing test outputs with `enabled: true` for sensitive features
    - ✅ GOOD: Redact or replace sensitive values in output examples
    - ✅ GOOD: Use `enabled: <redacted>` or `enabled: (controlled)`

12. **Migration/Upgrade Guides**
    - ❌ BAD: "Change `live_mode` from false to true"
    - ✅ GOOD: "Update execution mode configuration (requires governance review)"
    - ✅ GOOD: "See governance workflow for live mode enablement process"

---

## Policy Critic Trigger Patterns (Common)

**Important:** These are patterns that Policy Critic actively scans for. **DO NOT use these literally in docs.**

### High-Risk Patterns (BLOCK Severity)

- `enable_live_trading` with `true`
- `LIVE_MODE` with `true`
- `armed` with `true`
- API key patterns with `live` or `prod` prefixes
- Credential strings with actual values

**Safe Alternative:** Describe these patterns generically:
- "Certain live enablement flags"
- "Production-level configuration options"
- "Governance-controlled activation settings"

### Medium-Risk Patterns (WARN Severity)

- Modifications to `src/execution/`, `src/risk/`, `src/live/` (when combined with config changes)
- Changes to risk limits without justification
- Governance workflow bypasses

**Safe Alternative:**
- Document the *process* for making such changes, not the literal flags
- Reference governance workflows by name, not by showing how to bypass them

---

## When to Use Policy Exemptions

**Rare cases** where literal patterns are necessary (e.g., documenting the Policy Critic rules themselves):

### Option 1: Exemption Comment (if supported)

```markdown
<!-- policy-exempt: documentation-of-rules -->
This rule scans for `enable_live_trading=true` patterns.
<!-- /policy-exempt -->
```

### Option 2: Separate Security-Reviewed Document

- Store sensitive configuration examples in a governance-reviewed location
- Reference the document by path, don't inline the examples

### Option 3: Admin-Only Documentation

- Place highly sensitive docs in a restricted directory
- Ensure only operators with governance approval can access

---

## Examples from Real PRs

### ❌ BAD: PR #462 (Initial)

**Problem:** WP0D Completion Report contained literal trigger strings in a "Policy Compliance" section:

```markdown
- No "enable_live_trading=true" examples in code or docs
- No "live_mode=true" examples
```

**Result:** Policy Critic BLOCK with `NO_LIVE_UNLOCK` violations

### ✅ GOOD: PR #462 (Fixed)

**Solution:** Replaced with generic descriptions:

```markdown
- No live enablement triggers in code or docs
- No live mode activation examples
```

**Result:** Policy Critic ✅ green

---

## Integration with Other Guides

This guide complements:

- [`MERGE_LOGS_STYLE_GUIDE.md`](MERGE_LOGS_STYLE_GUIDE.md) — Safe formatting for merge logs
- [`POLICY_CRITIC_TRIAGE_RUNBOOK.md`](POLICY_CRITIC_TRIAGE_RUNBOOK.md) — Handling false positives
- [`DOCS_REFERENCE_TARGETS_GATE_STYLE_GUIDE.md`](DOCS_REFERENCE_TARGETS_GATE_STYLE_GUIDE.md) — Link hygiene

---

## Verification Commands

Before committing documentation changes:

```bash
# Check for common trigger patterns (local scan)
grep -r "enable_live_trading.*true" docs/ || echo "Clean"
grep -r "LIVE_MODE.*true" docs/ || echo "Clean"
grep -r "armed.*true" docs/ || echo "Clean"

# Check for literal API keys (basic pattern)
grep -rE "(sk_live|pk_live|api.*key.*=.*[a-zA-Z0-9]{20,})" docs/ || echo "Clean"

# Policy Critic will run in CI, but local checks catch most issues early
```

---

## Lessons Learned (WP0D Integration)

From **PR #462** (2025-12-31):

1. **Documentation of policy rules triggers the rules themselves**
   - Documenting "what not to do" by showing literal examples causes false positives
   - Use generic descriptions instead

2. **Completion reports are scanned like code**
   - Policy Critic scans all files in the PR, including completion reports
   - Apply the same safety standards to docs as to code

3. **Fix is simple but requires awareness**
   - Replacing literal strings with generic terms takes seconds
   - Preventing the issue upfront saves CI time and re-review cycles

---

## Quick Checklist for Docs Authors

Before submitting a docs PR:

- [ ] No literal `enable_live_trading=true` patterns
- [ ] No literal `LIVE_MODE=true` patterns
- [ ] No literal `armed=true` patterns
- [ ] No actual API keys or credentials (use placeholders)
- [ ] Configuration examples use `<placeholder>` or `{value}` syntax
- [ ] Policy rule documentation uses generic descriptions
- [ ] Code blocks with sensitive flags are commented or use pseudocode
- [ ] Live enablement processes reference governance workflows, not literal steps

---

## Contact & Updates

**Maintainer:** Peak_Trade Ops Team

**Updates:** This guide is living documentation. Update it when new trigger patterns are discovered or when Policy Critic rules change.

**Related PRs:**
- PR #462 (2025-12-31) — Initial policy-safe patterns established from WP0D blockers

---

**Last Reviewed:** 2025-12-31
**Next Review:** Upon next Policy Critic rule change or major false-positive incident
