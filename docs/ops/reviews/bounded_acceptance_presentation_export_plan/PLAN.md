# BOUNDED ACCEPTANCE PRESENTATION EXPORT PLAN

## Purpose
Define how bounded acceptance slides should be packaged and exported from the repo source.

## Source of Truth
Primary source:
- `docs&#47;ops&#47;slides&#47;BOUNDED_ACCEPTANCE_SLIDES_V2.md`

Older source retained for history / iteration:
- `docs&#47;ops&#47;slides&#47;BOUNDED_ACCEPTANCE_SLIDES_V1.md`

## Recommended Packaging Model
- keep Marp Markdown in git as the source of truth
- treat exported presentation files as derivative artifacts
- avoid making PDF / HTML the editing source

## Export Targets
Recommended export targets when needed:
- PDF for review / sharing
- HTML for lightweight presentation preview

## Versioning Recommendation
Version in git:
- Marp Markdown source
- supporting handoff / review docs

Do not version by default:
- generated PDF exports
- generated HTML exports

Rationale:
- source remains diffable and reviewable
- exports are reproducible from source
- avoids binary churn in the repo

## Suggested Export Location
If exports are produced for a review event, prefer a non-source location such as:
- `out&#47;ops&#47;slides&#47;`
or another clearly generated-artifact path

Do not treat generated exports as canonical source documents.

## When To Export
Export only when one of these is true:
- an internal review meeting needs a presentation artifact
- a PDF is specifically requested
- HTML preview is needed outside the repo editing flow

## Naming Convention
Suggested pattern:
- `bounded_acceptance_slides_v2.pdf`
- `bounded_acceptance_slides_v2.html`

If event-specific:
- `bounded_acceptance_slides_v2_<yyyymmdd>.pdf`

## Review / Release Position
Current recommendation:
- keep the repo on Marp source only for now
- export on demand
- do not add export automation until there is a concrete recurring need

## Future Option
If repeated exports become common:
- add a lightweight export runbook
- optionally add a local helper script
- still keep the Marp Markdown as source of truth

## Bottom Line
Bounded acceptance slides should remain source-first in git, with PDF / HTML treated as generated delivery artifacts created only when needed.
