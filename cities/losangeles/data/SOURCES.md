# Sources fetched for Los Angeles

Written by the pipeline, one line per fetched input: where it came from, when, how
many records, and a fingerprint of the committed file. Do not edit by hand; rerun the
stage instead. Hashes are the first 12 hex digits of the file's SHA-256.

| Stage | What | Publisher | Retrieved | Records | File | Hash |
|---|---|---|---|---|---|---|
| `00_osm_extract` | [Pedestrian network (OpenStreetMap)](https://download.geofabrik.de/north-america/us/california/socal-261110.osm.pbf) | OpenStreetMap contributors, via Geofabrik | 2026-11-11 | 575806 |  | `` |
| `00_osm_extract` | [Place names and named areas (OpenStreetMap)](https://download.geofabrik.de/north-america/us/california/socal-261110.osm.pbf) | OpenStreetMap contributors, via Geofabrik | 2026-11-11 | 1776 | `places_losangeles.geojson` | `23707d55998f` |
| `00_osm_extract` | [Plantable street centrelines (OpenStreetMap)](https://download.geofabrik.de/north-america/us/california/socal-261110.osm.pbf) | OpenStreetMap contributors, via Geofabrik | 2026-11-11 | 85650 | `streets_losangeles.geojson` | `7fa0029a4aa0` |
| `00_osm_extract` | [Residential building footprints (OpenStreetMap)](https://download.geofabrik.de/north-america/us/california/socal-261110.osm.pbf) | OpenStreetMap contributors, via Geofabrik | 2026-11-11 | 1667445 | `buildings_losangeles.geojson` | `43396ff30de4` |
| `04_overlays` | [Neighbourhood names](https://services5.arcgis.com/7nsPwEMP38bSkCjy/arcgis/rest/services/LA_Times_Neighborhoods/FeatureServer/0) | Los Angeles Times Mapping L.A., published on the City of Los Angeles GeoHub | 2026-11-11 | 114 | `places_losangeles.geojson` | `23707d55998f` |
| `04e_wards` | [Council districts](https://maps.lacity.org/lahub/rest/services/Boundaries/MapServer/13) | City of Los Angeles, Bureau of Engineering (GIS Mapping Division) | 2026-11-11 | 15 | `wards_losangeles.geojson` | `343e1c060fa2` |
| `04g_fire` | [Wildfire perimeters](https://services1.arcgis.com/jUJYIo9tSA7EHvfZ/arcgis/rest/services/California_Historic_Fire_Perimeters/FeatureServer/0) | CAL FIRE, Fire and Resource Assessment Program (FRAP) | 2026-11-11 | 2 | `fire_losangeles.geojson` | `d17de04a802e` |

## Notes

- **Pedestrian network (OpenStreetMap)**: Graph nodes after simplification; cached outside the repository (_cache/).
- **Residential building footprints (OpenStreetMap)**: Extract socal-261110.osm.pbf (SHA-256 98bd541bca91…), read locally by 00_osm_extract.py with the tag rules of the Overpass queries in 02b and 04 and osmnx's walk filter. © OpenStreetMap contributors, ODbL.
- **Neighbourhood names**: Used to name cells by the neighbourhood containing their centre. Not a legal boundary; nothing is scored by neighbourhood.
- **Council districts**: 2021 redistricting, Ordinance 187279, effective December 10, 2021. Member names as fetched; the district number is the stable label.
- **Wildfire perimeters**: Perimeters of fires from 2023 on that reach the study area. A perimeter is the fire's outer line, not a map of what burned.
