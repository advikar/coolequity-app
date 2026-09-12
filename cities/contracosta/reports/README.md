# September 7, 2026 rebuild evidence

- `rebuild_summary.json`: browser-equivalent before/after ranks, source counts and nine weight stress cases.
- `rebuild_cell_changes.csv`: stable cell ID, previous/current rank, score, population and A/C. Positive rank_change means higher priority after the rebuild. Previous score is the older exported score; comparisons of rank use browser arithmetic.
- `source_manifest.json`: public source endpoints, vintage, coverage rule and SHA-256 hashes of the new inputs/output.

Regenerate after a future build with `.venv/bin/python pipeline/06_audit_rebuild.py --baseline PATH`.
PATH must contain the actual preceding `contracosta.geojson`; retain it before replacing data.
The current comparison uses the pre-rebuild workspace snapshot. Weight stress tests vary canopy
share (35/55/75%) and the allocation of the remainder between A/C and age; they do not quantify
ACS uncertainty, optimize city policy or prove local predictive validity.

Validation: `.venv/bin/python -m unittest discover -s tests -p 'test_*.py'` and
`node tests/ui-contract.cjs`. Cache refresh and rebuilding instructions remain in the pipeline.
No city branch other than Contra Costa was changed. This is a local, unpublished build.
