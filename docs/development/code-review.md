# Code Review Process

Peak Trade uses automated and manual code reviews to maintain code quality.

## Automated Code Review

### Pre-commit Hooks

Runs automatically on `git commit`:

```bash
# Install hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

**Checks**:
- ✅ Ruff linting
- ✅ Ruff formatting
- ✅ MyPy type checking
- ✅ Bandit security scan
- ✅ Trailing whitespace
- ✅ End-of-file fixer
- ✅ YAML/JSON/TOML validation

### Code Review Script

Comprehensive quality check:

```bash
python scripts/code_review.py
```

This runs:
1. **Ruff lint**: Fast Python linting
2. **Ruff format check**: Code formatting validation
3. **MyPy**: Type checking
4. **Bandit**: Security vulnerability scanning
5. **Test coverage**: Ensure adequate test coverage

Example output:

```
🔍 Ruff linting...
✅ Ruff linting passed

🔍 Ruff format check...
✅ Ruff format check passed

🔍 MyPy type checking...
✅ MyPy type checking passed

🔍 Bandit security scan...
✅ Bandit security scan passed

🔍 Test coverage...
✅ Test coverage passed

✅ All checks passed!
```

## CI/CD Review

### GitHub Actions

Every pull request triggers:
1. **Lint job**: Code quality checks
2. **Test job**: Full test suite (Python 3.9, 3.10, 3.11)
3. **Strategy smoke tests**: Validate all strategies

View results: GitHub PR → Checks tab

### Status Checks

Pull requests must pass:
- ✅ Lint checks
- ✅ All tests
- ✅ Strategy smoke tests

## Manual Code Review

### Review Checklist

**Code Quality**:
- [ ] Code follows style guidelines
- [ ] No unnecessary complexity
- [ ] Clear variable and function names
- [ ] Proper error handling
- [ ] No security vulnerabilities

**Testing**:
- [ ] New code has tests
- [ ] Tests are meaningful
- [ ] Edge cases covered
- [ ] No flaky tests

**Documentation**:
- [ ] Docstrings are clear
- [ ] Complex logic is commented
- [ ] User-facing changes documented
- [ ] Examples included where helpful

**Performance**:
- [ ] No obvious performance issues
- [ ] Efficient algorithms used
- [ ] No unnecessary loops or operations

**Compatibility**:
- [ ] Works across Python versions (3.9+)
- [ ] No breaking changes (or documented)
- [ ] Dependencies updated appropriately

### Review Comments

**Good feedback**:
```
✅ Consider using a list comprehension here for better performance:
   `results = [process(x) for x in items]`

✅ This function might raise ValueError if input is empty.
   Add input validation?

✅ Great test coverage! Consider adding an edge case test
   for when period=0
```

**Less helpful**:
```
❌ This is wrong.
❌ Bad code.
❌ You should know better.
```

## Common Issues

### Linting Failures

**Issue**: Ruff reports style violations

**Fix**:
```bash
# Auto-fix most issues
ruff check --fix .

# Format code
ruff format .
```

### Type Check Failures

**Issue**: MyPy reports type errors

**Fix**:
```python
# Add type hints
def process_data(data: pd.DataFrame) -> dict[str, float]:
    return {"mean": data.mean()}

# Use Optional for nullable values
from typing import Optional

def get_value(key: str) -> Optional[float]:
    return cache.get(key)
```

### Security Warnings

**Issue**: Bandit reports security concerns

**Fix**:
```python
# ❌ Don't use assert for validation
assert len(data) > 0, "Data is empty"

# ✅ Use proper exceptions
if len(data) == 0:
    raise ValueError("Data is empty")

# ❌ Don't use shell=True
subprocess.run(f"ls {user_input}", shell=True)

# ✅ Use list arguments
subprocess.run(["ls", user_input])
```

### Test Coverage Issues

**Issue**: Coverage below threshold

**Fix**:
```bash
# Check what's not covered
pytest tests/ --cov=src --cov-report=term-missing

# Add tests for uncovered code
pytest tests/ --cov=src --cov-report=html
# Open htmlcov/index.html to see details
```

## Best Practices

### Before Submitting PR

1. **Run local checks**:
   ```bash
   python scripts/code_review.py
   ```

2. **Run full test suite**:
   ```bash
   pytest tests/ -v
   ```

3. **Check coverage**:
   ```bash
   pytest tests/ --cov=src --cov-report=term-missing
   ```

4. **Review your own code**: Read your changes before submitting

### During Review

1. **Respond promptly** to feedback
2. **Ask questions** if feedback is unclear
3. **Make requested changes** or explain why not
4. **Mark conversations resolved** after addressing

### After Approval

1. **Squash commits** if needed
2. **Update branch** if behind main
3. **Verify CI passes** one final time

## Tools

### IDE Integration

**VSCode**:
```json
{
  "python.linting.ruffEnabled": true,
  "editor.formatOnSave": true,
  "[python]": {
    "editor.defaultFormatter": "charliermarsh.ruff"
  }
}
```

**PyCharm**:
- Settings → Tools → Ruff
- Enable "Ruff" plugin
- Configure file watcher for auto-formatting

### Command Line

```bash
# Quick checks
make lint
make typecheck
make test

# Full review
make check
```

## Getting Help

- **Questions**: Ask in PR comments
- **Style questions**: See [Contributing Guide](contributing.md)
- **Technical issues**: Open GitHub Discussion

## See Also

- [Contributing Guide](contributing.md)
- [CI/CD Pipeline](cicd.md)
- [Testing Guide](../guides/testing.md)
