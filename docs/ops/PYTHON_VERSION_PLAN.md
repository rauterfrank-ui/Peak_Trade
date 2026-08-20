# Python Version Upgrade Plan

```text
DOCUMENT_STATUS=HISTORICAL_SUPERSEDED
SUPERSEDED_BY=docs/runtime/PEAK_TRADE_PYTHON_RUNTIME_CONTRACT_V1.md
CURRENT_PROJECT_FLOOR=requires-python >=3.10 (pyproject.toml)
CURRENT_SUPPORTED_LOCAL_RUNTIME=.venv/bin/python via scripts/pt
PYTHON_39_SUPPORTED=false
```

This planning note is **historical**. It must not be read as current runtime
guidance. The project floor is `requires-python = ">=3.10"`. Python 3.9 is not a
supported Peak_Trade runtime. Use `./scripts/pt`, not PATH `python3`.

**Status:** SUPERSEDED (kept for history)
**Historical snapshot in this note:** Python 3.9.6 as then-current local CLT
**Current target:** repository `.venv` CPython 3.11.x


---

## Why Upgrade?

### Security Risk
- Python 3.9 reaches End-of-Life in **October 2025**
- After EOL: No security patches, no bug fixes
- Dependencies may drop 3.9 support (NumPy, Pandas already recommend 3.10+)

### Performance Benefits
- 3.11: ~10-60% faster execution (CPython optimizations)
- 3.12: Further performance improvements, better error messages
- Better async/await performance (relevant for live trading)

### Feature Benefits
- Better type hints (ParamSpec, TypeVarTuple)
- Improved error messages and tracebacks
- `tomllib` built-in (currently using external toml package)
- Pattern matching (`match`/`case` statements)

---

## Recommended Target: Python 3.11

**Rationale:**
- 3.11 is mature (released Oct 2022, well-tested)
- Major performance improvements
- Wide dependency compatibility
- 3.12 is newer but some packages may lag

**Alternative:** Python 3.12 if all dependencies support it by upgrade time.

---

## Upgrade Steps

### Phase 1: Preparation (This PR - Documentation Only)
- [x] Document current state and plan
- [ ] Audit `requirements.txt` for version constraints
- [ ] Check CI matrix (GitHub Actions)

### Phase 2: Local Testing (Separate PR)
1. Install Python 3.11 locally:
   ```bash
   # macOS
   brew install python@3.11

   # Or use pyenv
   pyenv install 3.11.7
   pyenv local 3.11.7
   ```

2. Create fresh venv and install deps:
   ```bash
   python3 -m venv .venv311
   source .venv311/bin/activate
   pip install -r requirements.txt
   ```

3. Run full test suite:
   ```bash
   python3 -m pytest -q
   make todo-board-check
   ```

4. Run audit:
   ```bash
   make audit
   ```

### Phase 3: CI Update (Separate PR)
1. Update `.github&#47;workflows&#47;*.yml`:
   ```yaml
   strategy:
     matrix:
       python-version: ['3.11']  # or ['3.11', '3.12'] for matrix
   ```

2. Update `pyproject.toml` (if exists):
   ```toml
   [project]
   requires-python = ">=3.11"
   ```

3. Update `requirements.txt` header comment (if any)

### Phase 4: Production Rollout
1. Update local dev environment
2. Verify all scripts work
3. Update any deployment configs
4. Remove 3.9 from CI matrix

---

## Rollback Plan

If issues arise after upgrade:

1. **Immediate:** Switch back to 3.9 venv
   ```bash
   deactivate
   source .venv/bin/activate  # Original 3.9 venv
   ```

2. **CI:** Revert workflow changes
   ```bash
   git revert <commit-sha>
   ```

3. **Dependencies:** Pin problematic packages to 3.9-compatible versions

---

## Dependency Compatibility Check

Before upgrading, verify these key dependencies:
- `numpy` - Check minimum Python version
- `pandas` - Check minimum Python version
- `pydantic` - Usually well-maintained
- `ccxt` - Exchange library
- `pytest` - Testing framework

Command to check:
```bash
pip index versions <package> --python-version 3.11
```

---

## Timeline Recommendation

| Phase | Target Date | Notes |
|-------|-------------|-------|
| Preparation | Now | This document |
| Local Testing | Q1 2025 | Before 3.9 EOL |
| CI Update | Q1 2025 | After local validation |
| Full Rollout | Q2 2025 | Before Oct 2025 EOL |

---

## References

- [Python 3.9 EOL Schedule](https://devguide.python.org/versions/)
- [Python 3.11 Release Notes](https://docs.python.org/3/whatsnew/3.11.html)
- [Python 3.12 Release Notes](https://docs.python.org/3/whatsnew/3.12.html)

---

*This document is for planning purposes. Implementation requires explicit approval and separate PR.*
