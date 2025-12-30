# Execution Simple (Legacy)

**Location:** `src/execution_simple/`  
**Purpose:** Simplified execution for legacy/backtest code  
**Status:** Legacy (use `src/execution/` for new code)

---

## Purpose

This module provides **simplified execution** for:
- Legacy backtest code
- Quick prototyping
- Educational examples

**Do NOT use for:**
- ❌ Live trading (use `src/execution/` instead)
- ❌ Production code (use `src/execution/` instead)

---

## Relationship to `src/execution/`

See: `src/execution/README.md`

**Use `src/execution/` instead of this module for all new code.**

---

## Migration

If you have code using `src/execution_simple/`, consider migrating to `src/execution/` for:
- Better state management
- Retry policies
- Audit trail
- Production readiness

---

## Revision History

| Date | Version | Changes |
|------|---------|---------|
| 2025-12-30 | 1.0 | Initial README for FND-0003 remediation |
