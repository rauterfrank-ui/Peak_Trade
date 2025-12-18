# Peak Trade Reporting Guide

## Overview

This guide covers reporting and documentation generation in the Peak Trade project.

## Available Reports

### Quarto Smoke Report

**Purpose**: Quick smoke test to verify Quarto rendering is working

**Template**: `templates/quarto/smoke.qmd`
**Output**: `reports/quarto/smoke.html`

**Usage**:
```bash
# Render smoke report
make report-smoke

# Render and open in browser (macOS)
make report-smoke-open
```

**Documentation**: See [REPORTING_SMOKE.md](REPORTING_SMOKE.md) for detailed information

**Output**: Self-contained HTML at `reports/quarto/smoke.html`

## Reporting Tools

### Quarto

**What is Quarto?**
- Modern scientific publishing system
- Combines code, narrative, and visualizations
- Supports Python, R, Julia, Observable JS
- Multiple output formats: HTML, PDF, Word, presentations

**Installation**:
```bash
# macOS
brew install quarto

# Verify
quarto --version
```

**Basic usage**:
```bash
# Render a .qmd file
quarto render path/to/report.qmd

# Render to specific format
quarto render report.qmd --to html
quarto render report.qmd --to pdf
```

**Documentation**: https://quarto.org/docs/guide/

### Python Dependencies

Reports typically require:
```bash
pip install numpy pandas matplotlib seaborn scikit-learn
```

Check individual report documentation for specific requirements.

## Report Structure

### Quarto Reports

**Templates**: `templates/quarto/`
**Outputs**: `reports/quarto/` (gitignored)

Structure:
```
templates/quarto/
├── smoke.qmd           # Smoke test template
└── *.qmd               # Future report templates

reports/quarto/         # Generated outputs (gitignored)
├── *.html              # HTML reports
└── *_files/            # Supporting files
```

### Scripts

Location: `scripts/dev/`

Structure:
```
scripts/dev/
├── report_smoke.sh     # Smoke report renderer
└── ...                 # Future report scripts
```

## CI/CD Integration

### GitHub Actions

Reports can be automatically generated in CI and uploaded as artifacts.

**Example workflow**: `.github/workflows/quarto_smoke.yml`

**Accessing CI artifacts**:
1. Navigate to Actions tab in GitHub
2. Click on workflow run
3. Scroll to "Artifacts" section
4. Download artifact ZIP
5. Extract and open HTML in browser

**Artifact retention**: 7 days (configurable in workflow YAML)

## Creating New Reports

### 1. Create Quarto Document

```bash
# Create new .qmd template
touch templates/quarto/my_report.qmd
```

### 2. Add Frontmatter

```yaml
---
title: "My Report Title"
author: "Peak Trade Team"
date: today
format:
  html:
    toc: true
    code-fold: false
    embed-resources: true
---
```

### 3. Add Content

Use markdown with code blocks:

````markdown
## Analysis Section

{python}
import pandas as pd
# Your analysis code
```
````

### 4. Create Render Script (optional)

```bash
#!/usr/bin/env bash
set -euo pipefail
quarto render templates/quarto/my_report.qmd --to html --output-dir reports/quarto
```

### 5. Add Makefile Target (optional)

```makefile
report-my-report:
	./scripts/dev/report_my_report.sh
```

### 6. Add CI Workflow (optional)

Copy and modify `.github/workflows/quarto_smoke.yml`

## Best Practices

### Self-Contained Reports

Always use `embed-resources: true` in Quarto frontmatter:
```yaml
format:
  html:
    embed-resources: true
```

This ensures HTML files include all images, CSS, and JS inline (no external dependencies).

### Reproducibility

- Pin package versions in requirements
- Document data sources and preprocessing
- Include environment information in reports
- Use relative paths from repo root

### Performance

- Keep smoke reports fast (< 1 minute)
- Use data sampling for large datasets in CI
- Cache expensive computations when possible
- Consider separate workflows for heavy reports

### Security

- Never commit sensitive data to reports
- Use `.gitignore` for generated outputs with data
- Sanitize any API keys or credentials
- Review reports before making repository public

## File Organization

### What to Commit

✅ Commit:
- `.qmd` source files
- Render scripts
- Documentation
- CI workflows

❌ Don't commit:
- Generated HTML/PDF outputs
- Large data files
- Temporary render artifacts
- `.quarto/` cache directory

See `.gitignore` for full list.

### What to Archive

Consider archiving (outside Git):
- Important generated reports with specific dates
- Reports for presentations or publications
- Large datasets used in reports

## Troubleshooting

### Quarto not found

```bash
# Install Quarto
brew install quarto  # macOS
# or download from https://quarto.org/docs/get-started/

# Verify
quarto --version
```

### Python package import errors

```bash
# Install missing packages
pip install package-name

# Or reinstall all requirements
pip install -r requirements.txt
```

### Render fails with "No such file"

- Check working directory (should be repo root)
- Verify file paths are relative to repo root
- Ensure all data files exist

### CI artifact not uploaded

- Check workflow logs for errors
- Verify file path matches workflow YAML
- Confirm file was actually generated
- Review `if-no-files-found` setting

## Related Documentation

- [Quarto Smoke Report Guide](REPORTING_SMOKE.md)
- [Quarto Official Docs](https://quarto.org/docs/guide/)
- [GitHub Actions Artifacts](https://docs.github.com/en/actions/using-workflows/storing-workflow-data-as-artifacts)

## Future Enhancements

Potential additions:
- Model training reports
- Experiment comparison reports
- Performance benchmark reports
- Data quality reports
- API documentation generation
- Automated report scheduling
