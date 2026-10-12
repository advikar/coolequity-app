# Sources fetched for San Ramon

Written by the pipeline, one line per fetched input: where it came from, when, how
many records, and a fingerprint of the committed file. Do not edit by hand; rerun the
stage instead. Hashes are the first 12 hex digits of the file's SHA-256.

| Stage | What | Publisher | Retrieved | Records | File | Hash |
|---|---|---|---|---|---|---|
| `04e_wards` | [City council districts](https://gis.sanramon.ca.gov/server/rest/services/Infrastructure/City_Council_Districts/MapServer/0) | City of San Ramon GIS | 2026-10-12 | 4 | `wards_sanramon.geojson` | `ecc2392443fa` |

## Notes

- **City council districts**: 2022 redistricting after the 2020 census (by-district elections since November 2020). Member names as fetched; the district number is the stable label.
