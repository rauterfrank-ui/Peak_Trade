```text
AUTHORITY=NONE
PURPOSE=FORENSIC_HISTORICAL_REFERENCE
EXTRACTION_CLASS=MECHANICAL_READ_ONLY_REGEX_AND_FENCE_SCAN
INTERPRETATION_USED_AS_FACT=false
```

Re-run:

`./scripts/pt forensics/historical_reference/extraction/materialize_historical_reference_v1.py`

The generator is frozen with this package. Later corrections must add a new
content-addressed object and record supersession. Do not silently rewrite.
