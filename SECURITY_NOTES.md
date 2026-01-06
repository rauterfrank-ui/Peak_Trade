# Security Notes - Dependencies

## Python Version Compatibility & Known Vulnerabilities

### Overview

This project supports Python 3.9, 3.10, and 3.11. Some security vulnerabilities exist in older package versions required for Python <3.10 support, but these vulnerabilities are **not present** in the CI/production environment which uses Python 3.11.

### Status (as of 2026-01-06)

#### ✅ Resolved
- **aiohttp** (3.13.2 → 3.13.3): All 8 vulnerabilities fixed across all Python versions

#### ⚠️ Known Limitations (Python 3.9 only)

##### 1. filelock 3.19.1
- **Vulnerability**: GHSA-w853-jp5j-5j7f
- **Fix Available**: 3.20.1 (requires Python >=3.10)
- **Impact**: Low - filelock is used for temporary file locking in development tools
- **Mitigation**: Production/CI uses Python 3.11 with filelock 3.20.1

##### 2. mlflow 3.1.4
- **Vulnerability**: GHSA-wf7f-8fxf-xfxc
- **Fix Available**: 3.8.1 (requires Python >=3.10)
- **Impact**: Medium - affects experiment tracking functionality
- **Mitigation**: Production/CI uses Python 3.11 with mlflow 3.8.1

### Recommendations

#### For Production/CI
- ✅ Continue using Python 3.11 (current configuration)
- ✅ No action required - all vulnerabilities are resolved

#### For Local Development (Python 3.9 users)
- Consider upgrading to Python 3.10+ to benefit from security fixes
- If Python 3.9 is required, be aware of the above limitations
- Contact the maintainers if you have concerns about these vulnerabilities

### Audit Policy

The CI audit workflow (`pip-audit`) runs on Python 3.11 and will:
- ✅ **PASS** - No vulnerabilities detected in Python 3.11 environment
- ⚠️ Note: `pip-audit` may report vulnerabilities when scanning `requirements.txt` with Python <3.10 constraints, but these do not affect the production environment

### Future Actions

- Monitor for Python 3.9 security fixes for filelock and mlflow
- Consider dropping Python 3.9 support in future major version if vulnerabilities remain unpatched

---

**Last Updated**: 2026-01-06  
**Audit Tool**: pip-audit 2.9.0
