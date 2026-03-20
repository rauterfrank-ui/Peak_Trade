# BOUNDED ACCEPTANCE EXPORT RUNBOOK

## Purpose
Runbook for exporting bounded acceptance slides from Marp Markdown source into on-demand PDF or HTML artifacts.

## Source of Truth
Primary source:
- `docs/ops/slides/BOUNDED_ACCEPTANCE_SLIDES_V2.md`

Do not edit generated PDF or HTML as the canonical source.

## Output Position
Preferred generated-artifact location:
- `out/ops/slides/`

Suggested output names:
- `bounded_acceptance_slides_v2.pdf`
- `bounded_acceptance_slides_v2.html`

## Preconditions
- repo on `main` or intended review branch
- working tree understood before export
- Marp source reviewed before export
- exports treated as generated artifacts, not repo source

## Prerequisites
- Node.js and `npx` available
- Marp CLI: `npx @marp-team/marp-cli` (no global install required)

## Export Commands

### PDF
```bash
cd ~/Peak_Trade
mkdir -p out/ops/slides
npx @marp-team/marp-cli docs/ops/slides/BOUNDED_ACCEPTANCE_SLIDES_V2.md --pdf --no-stdin -o out/ops/slides/bounded_acceptance_slides_v2.pdf
```

### HTML
```bash
cd ~/Peak_Trade
mkdir -p out/ops/slides
npx @marp-team/marp-cli docs/ops/slides/BOUNDED_ACCEPTANCE_SLIDES_V2.md --html --no-stdin -o out/ops/slides/bounded_acceptance_slides_v2.html
```

### Event-Specific Naming
If a dated artifact is needed:
```bash
npx @marp-team/marp-cli docs/ops/slides/BOUNDED_ACCEPTANCE_SLIDES_V2.md --pdf --no-stdin -o out/ops/slides/bounded_acceptance_slides_v2_$(date +%Y%m%d).pdf
```

## When To Export
Export only when:
- an internal review meeting needs a presentation artifact
- a PDF is specifically requested
- HTML preview is needed outside the repo editing flow

## References
- export plan:
  `docs/ops/reviews/bounded_acceptance_presentation_export_plan/PLAN.md`
- slides source:
  `docs/ops/slides/BOUNDED_ACCEPTANCE_SLIDES_V2.md`

## Bottom Line
Exports are reproducible from Marp source. Do not version generated PDF/HTML in git by default.
