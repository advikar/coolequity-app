# Sources fetched for Bakersfield

Written by the pipeline, one line per fetched input: where it came from, when, how
many records, and a fingerprint of the committed file. Do not edit by hand; rerun the
stage instead. Hashes are the first 12 hex digits of the file's SHA-256.

| Stage | What | Publisher | Retrieved | Records | File | Hash |
|---|---|---|---|---|---|---|
| `02b_buildings` | [2020 Census blocks (residents and housing units, for building weights)](https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/Tracts_Blocks/MapServer/2) | US Census Bureau, TIGERweb | 2026-11-11 | 8870 |  | `` |
| `02b_buildings` | [Residential building footprints](https://gis.bakersfieldcity.us/webmaps/rest/services/General/Buildings/MapServer/0) | City of Bakersfield GIS Office | 2026-11-11 | 192093 | `buildings_bakersfield.geojson` | `ea6205598fad` |
| `02g_canopy_naip` | [NAIP 2022 aerial imagery (tree-cover model outside the USFS map)](https://planetarycomputer.microsoft.com/dataset/naip) | USDA Farm Service Agency, via Microsoft Planetary Computer | 2026-11-11 | 1758 |  | `` |
| `04e_wards` | [Council wards](https://gis.bakersfieldcity.us/webmaps/rest/services/General/Boundary/MapServer/5) | City of Bakersfield GIS Office | 2026-10-12 | 7 | `wards_bakersfield.geojson` | `cfa05a18572a` |
| `04h_priority_pop` | [Priority populations (California Climate Investments)](https://gis.carb.arb.ca.gov/hosting/rest/services/Hosted/PriorityPopulations5/FeatureServer/0) | California Air Resources Board | 2026-11-11 | 119 | `priority_pop_bakersfield.geojson` | `783e9e2eff9f` |
| `04i_street_names` | [Street centrelines (area names by cross streets)](https://gis.bakersfieldcity.us/webmaps/rest/services/General/Transportation/MapServer/4) | City of Bakersfield GIS Office | 2026-11-11 | 26680 | `street_names_bakersfield.geojson` | `18e17ee19baa` |
| `04j_places` | [Bus stops (places people go)](https://gis.bakersfieldcity.us/webmaps/rest/services/General/Transportation/MapServer/1) | Golden Empire Transit, via City of Bakersfield GIS Office | 2026-11-11 | 1055 | `places_people_go_bakersfield.geojson` | `a19154317011` |
| `04j_places` | [Parks (places people go)](https://gis.bakersfieldcity.us/webmaps/rest/services/General/ParksAndRecreation/MapServer/1) | City of Bakersfield GIS Office | 2026-11-11 | 113 | `places_people_go_bakersfield.geojson` | `a19154317011` |
| `04j_places` | [Schools (places people go)](https://gis.bakersfieldcity.us/webmaps/rest/services/General/Education/MapServer/0) | City of Bakersfield GIS Office | 2026-11-11 | 218 | `places_people_go_bakersfield.geojson` | `a19154317011` |

## Notes

- **2020 Census blocks (residents and housing units, for building weights)**: 2020 Census block counts (P.L. 94-171). Each residential footprint is weighted by its block's 2020 residents, shared by footprint area; 15,239 homes built since 2020 (main footprints beyond the block's 2020 housing units) are credited at their block group's residents per unit.
- **Residential building footprints**: 187,929 footprints typed RESIDENTIAL plus 14,222 untyped footprints lying in a residential land-use designation, before the size filter. City footprint layer, last edited July 2026; land use is the Metropolitan Bakersfield General Plan layer.
- **NAIP 2022 aerial imagery (tree-cover model outside the USFS map)**: Flown 2022-06-07 to 2022-06-08. Per-pixel model trained on the USFS map; on held-out cells against the USFS figure: urban cells (n=300) bias -0.12 points, mean absolute error 0.92, rank correlation 0.963; open-land cells (n=101) bias -0.01, mean absolute error 0.62. Count is cells filled.
- **Council wards**: 2022 redistricting, council map 5B (Unity Map). Member names as fetched; the ward number is the stable label.
- **Priority populations (California Climate Investments)**: Priority Populations 5.0, in effect for projects selected on or after September 18, 2026. Areas only; low-income households qualify anywhere and are not mapped.
- **Street centrelines (area names by cross streets)**: Names and road class only; used to name each area by its cross streets, not for routing or street length.
- **Bus stops (places people go)**: GET Bus Stops layer, last edited June 2026.
- **Parks (places people go)**: Park and Recreation layer: active public parks (city, county, North of the River district, state). Golf courses, the fairgrounds and private parks are left out.
- **Schools (places people go)**: School Facilities layer; open schools only. The layer's own verification dates are from 2018, so a school opened since may be missing.
