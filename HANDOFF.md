# HANDOFF

## Checkpoint — November 11, 2026 (Claude), evening: Bakersfield residents by building, modelled tree cover past the USFS map, priority populations, ward one-pagers

Task (owner: advikar): the five Bakersfield recommendations from the afternoon. Committed and pushed to `main` on the owner's instruction. Bakersfield's ranking
changes substantially; anything handed to city staff from the earlier build quotes old ranks.

1. **Residents placed by building (done, tested).** `02b_buildings.py` reads an agency footprint
   layer where a city sets `BUILDINGS_SOURCE` (Bakersfield: the city's own layer, 228,012
   footprints, last edited July 2026; typed RESIDENTIAL, plus untyped footprints in a residential
   general-plan designation). Where a city sets `BLOCK_WEIGHTS`, each footprint is weighted by
   its 2020 Census block's residents (shared within the block by footprint area), with homes
   built since 2020 credited at their block group's residents per unit; 03 splits by that weight.
   OpenStreetMap is no longer used for Bakersfield's buildings.
   - Guard (03, every run): 0.95 footprints per ACS housing unit; income quartiles 0.84 / 0.93 /
     0.97 / 1.17 (1.4x, limit 2.0x). City total 410,680 vs ACS place 411,986.
   - Ranked areas 3,767 -> 1,987: 1,789 cells that held residents only by even spreading have no
     housing. Against the previous build: Spearman 0.70 on cells ranked in both, top-25 overlap
     7, top-100 overlap 50. None of the old top 25 lost its ranking; 3 of the old top 100 did.
   - Check against 2020 block counts interpolated to cells: even spread r 0.86 (MAE 45 per
     cell); footprint area alone r 0.93 (30), the independent test; block-weighted r 0.94 (26),
     expected since it uses those counts. Largest mobile-home park cell: 583 by footprint area,
     305 counted in 2020, 312 block-weighted. Mobile-home parks are in the layer (2,999
     footprints in MH zoning).
   - `buildings_bakersfield.geojson` (36 MB) is gitignored like the other large masks; rebuild
     with `02b_buildings.py --refresh`.
2. **Tree cover past the USFS map (done, tested).** The USFS raster has no data outside the 2020
   urban-area line (checked on the downloaded package: only nodata there), so "neighbouring
   packages" was a dead end. New optional stage `02g_canopy_naip.py` (`CANOPY_NAIP` in config;
   needs `pip install scikit-learn`, installed outside the venv for this run) trains a per-pixel
   classifier on NAIP 2022 with the USFS map as label and fills cells the USFS map does not
   assess, only if it beats the height model on held-out cells.
   - Held-out, against the USFS figure (bias / MAE / rank r): urban -0.12 / 0.92 / 0.963
     (height model MAE 1.75, 1.51 rescaled, rank r 0.924); open land -0.01 / 0.62 / 0.974
     (height model 3.24, 0.861); edge +0.08 / 1.18 / 0.963.
   - **A first version was wrong and was caught by looking at the photos:** trained on urban
     cells only (urban MAE 1.03), it read irrigated alfalfa and pasture as canopy (65% on a crop
     field). A WorldCover cropland mask did not fix it (pasture is "grassland" there). The stage
     now trains and tests on open-land and edge cells the USFS map covers. Residual: thin false
     strips along some field edges, up to ~15 points in all-farmland cells (few or no residents).
     Orchards count as canopy, as in the USFS map.
   - 1,758 cells filled (213 ranked); threaded fill reproduced exactly by a single-threaded
     re-run on 14 cells. For the 87 modelled ranked cells with 50+ residents: mean 3.7% vs 3.6%
     under the height model, 5 differ by more than 5 points. No ranked cell uses the greenness
     stand-in or the height model any longer.
   - The fill hung once on a dead connection at 1,500 cells; the stage now sets GDAL HTTP
     timeouts, re-signs URLs on retry and checkpoints to `_cache/canopy_naip_fill_<slug>.jsonl`.
   - **Partly assessed cells (decided by the owner after a comparison).** 217 ranked cells are
     cut by the USFS boundary and report the assessed part only. Completing all of them with
     the model was run as a comparison (data restored afterwards): top 25 unchanged, 97 of the
     top 100 kept, but the 217 moved a median of 74 ranks and 97 of them 100 or more, mostly
     cells whose homes are all in the assessed part and whose remainder is empty land. Adopted
     instead: complete a cell only where under half of its in-city homes, weighted by
     residents, are in the assessed part (`complete_partial_below=0.5`; `--complete-partials`
     runs the step alone). 23 ranked cells, all inside the city limits (newer housing past the
     2020 urban line): `canopy_source` `usfs+naip-model`, `canopy_quality` `completed`,
     `coverage_frac` still the USFS share, never a planting baseline. A first count over all
     footprints gave 20; the pipeline rule counts in-city homes by resident weight, which adds
     three edge cells. Effect: the 23 moved a median of 190 ranks (15 up, 7 down; Moores Creed
     Dr & Wind Wolfs Ln 1,146 to 217); every other cell moved 7 ranks at most; top 25
     unchanged, 99 of the top 100 kept; none of the 23 entered the top 199.
3. **Priority populations (done, tested).** `04h_priority_pop.py` (`PRIORITY_POP_URL`): CARB
   Priority Populations 5.0, in effect September 18, 2026. Per cell `pp` (share) and `pp_type`;
   written by 05 only where the CSV exists (other builds' data files are untouched). Layer,
   detail row, export columns, briefing source line, guide topic `#pp` (short "not built" topic
   in the other five guides, as for `#fire`). Never scored. 1,759 of 4,054 cells at least half
   inside; every cell's share >= its SB 535 share (asserted in the page test). 38% of residents
   in SB 535 communities, 51% in priority population areas.
4. **Street-tree inventory (not possible; nothing built).** The city's GIS services list no tree
   or planting-site layer, and public reporting says the city has no inventory: the Council
   declined an inventory contract and staff are reconsidering how to do one. Nothing to load.
   The request has to go to the urban forestry contact.
5. **Ward one-page summaries (done, tested).** `openWardSheets()` in `app/index.html`, button
   under the ward table in every build with wards or districts: one Letter page each (residents,
   top-100 count, need and tree cover vs the study area, heat, 65+, SB 535 and priority
   population shares, an SVG map of the ward's cells, top ten areas, starred-area trees, cost and
   SB 535 share). With a ward chosen in the list filter, that ward only.

7. **Places people go (done, tested).** Research first: the city's
   tree program is run by Recreation and Parks ($500,000 for fiscal 2026-27, 80% of planting in
   underserved areas, wards with least canopy first, Wards 1 and 7 named), plants in city parks,
   city streetscapes and the Kern River Parkway, and the Central City corridor project is about
   downtown walkability (news coverage; council packets were not readable from here). Those are
   places, not homes, and the ranking cannot see an area with no residents.
   - `04j_places.py` (`PLACES`): open schools, GET bus stops and public parks from the city's
     layers. Each place is measured on its own ground: tree cover inside the park, on the school
     property polygon (120 m around the point where there is none), within 30 m of a stop, on the
     USFS 60 cm raster; heat from the Landsat composite over the same ground. 1,007 places inside
     the city limits (772 stops, 148 schools, 87 parks); 970 measured on the aerial map itself,
     37 past its edge take the surrounding cell's figure and say so. Median tree cover: stops
     5.5%, schools 6.2%, parks 16.6%. Writes `people_places_<slug>.geojson` (served to the app)
     and per-cell counts (`schools`, `bus_stops`, `park`...), optional fields in 05.
   - A first version ranked whole cells that held a place; its top entries were bare desert
     beside a soccer park, so it was replaced by per-place measurement before anything shipped.
   - App: "Places people go" section (list, kind / city-park / SB 535 / ward filters, dots on
     the map, CSV), a "Here:" note in the detail panel, a line on each ward page. Index = half
     heat, half missing tree cover on the ranking's scales; no residents, no weights.
   - Not verified: the dots drawn on the map (the preview pane was hidden; the layer and its
     data were checked through the map's API only).
   - **Audit of the places method, November 12 (after the owner asked for one).** Changed: the
     two kerbs of a bus stop (same name within 80 m) are one place, 772 stops -> 645 locations,
     so the list no longer repeats a stop; places past the USFS map are read on their own
     ground by the 02g model (32 of 35; 3 parks keep the cell figure) instead of taking the
     cell's value; bus stops carry a second reading at 15 m. Checked: all 77 directly measured
     parks and all 507 single stops recomputed by canopy area / place area agree within 0.2
     points; heat for 15 parks within 0.6 C. Radius sensitivity (15 / 30 / 50 m medians 5.0 /
     5.9 / 6.3%; rank r 0.86 between 15 and 30 m; 56 of the barest 100 shared) is stated in the
     guide; the list ranks on 30 m and shows 15 m beside it. Total now 880 places.
   - Map view reworked after the owner found the dots frustrating: the 50 hottest and barest of
     the current list are numbered markers (number = list position; circle stop, square
     school, green ring park), linked to the rows both ways with a hover card; "Show all" adds
     the rest as small dots; hexagons fade while it is on.
   - Clicking a place only opened the surrounding cell and showed nothing of the place (owner's
     report, reproduced). Now any clicked place gets a labelled pin and a dashed outline of the
     ground that was measured (`people_places_outlines_<slug>.geojson`, fetched on first use),
     the camera goes to it clear of the detail panel, and the markers turn on. Seen working for
     a park and a bus stop at 1300 px wide; not checked on a phone-width screen, where the
     detail panel covers the map.
   - November 12: the owner saw the top school read 0% while the basemap shows trees. Checked on
     the June 2022 NAIP photo: Crescent Elementary was under construction, saplings only; the
     model's 0.1% is right for that day and the basemap is newer. Every row, pin and card now
     states the photo date (`tree_as_of` in the places file); the 35 places past the 2020 urban
     line are tagged "newer site"; a "Hide newer sites" filter drops them; the ward page's top
     three leaves them out. Not solved: new places inside the 2020 urban area are not dated.
9. **Tree spacing is editable (done, tested; all builds).** `TREE_SPACING_M` was a constant
   10; it is now an input beside the cost (4-30 m, default 10, feet shown). `setSpacing()`
   recomputes street room, its thirds, scenarios, costs and the ward table; exports already
   carried `tree_spacing_m` and loading a scenario now restores it. The ranking does not use
   spacing. Not changed: `wards_summary_<slug>.csv` (pipeline) still states capacity at 10 m.
   Bakersfield's code ratio (1 tree per 30 ft or per 20 ft of frontage depending on the
   edition found) is quoted in its guide as unconfirmed.
10. **Check planting locations (done, tested; all builds with SB 535).** The owner shared a
   briefing for a city presentation: the map could not show, tree by tree, that 80% of a
   planting is in SB 535 tracts (cells on a tract edge are partly designated; a cell's ward is
   its centre's). New section in the app: paste coordinates or open a CSV; each point is tested
   against the cached CalEPA tract outlines (`sb535_<slug>.geojson`, now shipped with the
   site) and the ward polygons, in the browser, nothing uploaded. Returns DAC yes/no, tract,
   criterion, ward and member, priority-population designation where built, a flag within 15 m
   of a tract edge, the share of the list inside a DAC, dots on the map and a CSV. Tested in
   `tests/ui-contract.cjs` at every cell centre wholly inside or outside a tract (about 20,000
   across five builds) and for ward agreement; all agree. The briefing's Bakersfield figures
   were re-derived from the data and hold (38% of residents and 34% of city land in a DAC;
   Wards 1 and 2 99%, Ward 7 27%, Ward 5 0%; 70 of the top 100 mostly in a DAC). Landing page
   and README counts corrected (Bakersfield 1,987; 15,676 areas in all; 79 stand-in areas).
   Top-ranked area (Commonwealth Ave & Withernsea Ln) checked on the June 2022 photo: a
   finished recent subdivision with saplings only, so its 0% is right for that date.
8. **Guide.** Bakersfield's guide opens with "How this map works, in plain words" (including
   "Why are so many areas gray?"), has "In plain words" paragraphs on Population and Tree
   canopy, and a "Places people go" topic; the other five guides have a short one. The priority
   legend now says gray means no residents.

Other changes: heat evidence re-measured on the new ranked set (position 16%, LST vs tree cover
r = -0.66; config.py note); stability re-run (199 top-tier of 1,987, median band 279, 51% of the
top tier stay in at least 80% of draws); wards summary re-run; `tests/ui-contract.cjs` EXPECT
bakersfield res 1987 / ndvi 0; new tests for priority populations and modelled canopy; README
stage list; all six guides' column keys regenerated.

- **Tests run:** `scripts/test.sh`, all six cities, passed (after the last edit to `app/index.html`).
  In the local build: Bakersfield map, priority populations layer, detail row and export
  column, modelled-canopy label, briefing source lines, ward pages (7), single-ward page; Los
  Angeles district pages (15); no console errors. **Not verified:** the ward pages as printed
  on paper or PDF, phone layout, Firefox/Safari.
6. **Area names by cross streets (done, tested; owner asked for it the same evening).**
   `04i_street_names.py` (`NAME_STREETS`): the city's street centreline layer (26,680 segments,
   names and road class). Each cell is named by the intersection inside it, arterials and
   collectors preferred, then nearest the centre ("Ming Ave & Stine Rd"); a cell with none is
   named by direction from the nearest ("N of Akers Rd & Planz Rd", with miles past a quarter
   mile). New optional property `near`: the nearest intersection of two through streets as a
   phrase ("0.4 mi N of Ming Ave & Stine Rd"), shown under the name in the detail panel, in the
   ward pages and the briefing's shortlist blocks, matched by search, exported as
   `nearest_major_intersection`. 05 replaces 04's names where `names_<slug>.csv` exists;
   `city.js` sets `nameKind:'streets'`. An intersection needs three segment ends of two
   differently named streets, so a name change (Coffee Rd / Gosford Rd) is not one.
   - 2,164 of 4,054 cells (1,804 of 1,987 ranked) hold an intersection; all names unique (26
     far-out empty cells carry a "(2)"). Against the city's separate intersection layer: 1,782 of
     the 1,804 ranked inside-named cells have that same intersection inside them.
   - Bakersfield only. The other five builds keep nearest-place names (Los Angeles: published
     neighbourhood polygons); doing the same for them needs a street layer with names per city.
   - The ward page was re-laid out to stay on one sheet with the extra column (map beside the
     facts; the street-room column gives way to the intersection where a build has one).
     Measured on screen for all seven wards; not printed.
   - Ranks, scores and every other field are unchanged by the renaming; shortlists and field
     notes are keyed by cell number, so they carry over.

## Checkpoint — November 11, 2026 (Claude), later: all builds on summers 2024–2026; SB 535 in three more; app audit fixes

Owner: advikar. Committed and pushed to `main` on the owner's instruction after a final pass
(below). This entry supersedes the "five earlier builds were
not rebuilt" line in the checkpoint below.

- **Satellite window.** `SUMMER_YEARS` is now (2024, 2025, 2026) in `pipeline/config.py` for
  every city (checked first: each city has at least as many Landsat scenes under the cloud
  filter as in 2022–2024). 02 re-run live for the five earlier cities (Landsat scenes: county
  96, Bakersfield 104, San Ramon 11, West CC 37, Pittsburg 41), then 05, 04e `--cached`, 05b.
  Against the previous commit, nothing but surface temperature, greenness and what follows
  from them changed (population, age, A/C, tree cover, streets, walking time, names, wards and
  place classes identical cell by cell; Bakersfield's 60 greenness stand-in cells re-read).
  - Contra Costa, Pittsburg: heat weight 0, **no rank moved**.
  - West Contra Costa: old/new LST r = 0.984; Spearman 0.997; top-25 overlap 24/25; top tier 94/98.
  - Bakersfield: LST r = 0.921; Spearman 0.974; top-25 22/25; top tier 359/377; median move 96 ranks.
  - San Ramon: LST r = 0.875 (11 scenes; mean −3.3 °C); Spearman 0.956; top-25 19/25; top tier 32/42.
  Anything already handed to city staff from Bakersfield, San Ramon or West CC quotes the old ranks.
- **Heat evidence re-measured** (ranked cells, linear fit on lon/lat; LST vs tree cover r):
  LA 8.8% / −0.66; San Ramon 13.5% / −0.56; West CC 6.0% / −0.35; Bakersfield 8.2% / −0.33;
  county 14.1% / −0.20; Pittsburg 15.7% / +0.23. The 38.8%, 28% and 11.1% quoted in older
  configs came from earlier builds and other cell subsets and do not reproduce; configs now
  carry dated re-measurement notes and the guides quote the new figures. **For the owner:** the
  position share no longer separates scored from unscored builds (San Ramon 13.5% scored,
  county 14.1% not); the tree-cover correlation does. No weight was changed.
- **SB 535** added as input (weight 0), layer and "Disadvantaged communities" preset to
  Contra Costa (408 cells at least half designated), West CC (480) and Pittsburg (475).
  San Ramon has no designated tract and stays without it. County preset is dac 50 / green 40 /
  ac 5 / age 5 because the contract test requires the top 50 under the preset to be designated.
  Recommended ranks unchanged by it.
- **App audit** (independent read of `app/`, `site/`, `scripts/build_site.py`; findings and
  fixes itemised in `cities/contracosta/FEATURES.md`). Fixed: briefing crashed with the HOLC
  layer on; CSV dropped `walk_method` and `share_inside_study_area`; heat and population legend
  captions; false unsaved-changes prompt after loading a scenario; "driven most by" naming
  inputs that are not high; guide search and sub-anchor links; fire note in briefing and
  compare table; CSV byte-order mark; list scrolling during slider drags; start-screen keys;
  stand-in sort and label; district wording; one-entry Show menu hidden; reset restores county
  dots; two unescaped strings; column-key values; `build_site.py --out` guard; ward-summary CSV
  line endings. **Not fixed, left for the owner:** `aria-pressed` on the Units and Basemap
  toggles, a label on the field-check textarea, keyboard access to ward-table rows, planting
  shares not restored after a reload, HOLC grade not shown in the detail panel, and throttling
  slider redraws on Los Angeles if dragging feels slow.
- **Final pass before the push.** A range check on every data file found two Contra Costa
  cells (Canyon S, Canyon SW) with calibrated tree cover of 103.9% and 100.8%, present since
  the September lidar calibration: the fitted aerial line runs past 100 at the dense end. 05
  now caps calibrated and lidar-substituted cover at 100; both cells read 100%, no rank moved.
  All six maps, guides, cooling pages and data files answer 200 in the local build, every
  preset applies without error, and each map draws.
- **Tests run:** `scripts/test.sh`, all six cities, passed. In the local build: county SB 535
  layer and preset, Los Angeles briefing with the HOLC layer on, corrected captions, hidden
  Show menu, CSV columns; no console errors. Not verified: the printed briefing's appearance,
  phone layout, Firefox/Safari.

## Checkpoint — November 11, 2026 (Claude): Los Angeles build, with a source-vintage audit

Task: add the City of Los Angeles as a sixth study area, after checking every data source for a
newer vintage. Owner: advikar. Committed with the entry above.

- **Source audit (all checked November 11, 2026).** Still the newest release, kept: ACS
  2020–2024 5-year (the 2025 endpoint returns 404; due December 2026), Census LACE 2023 (only
  vintage), USFS/CAL FIRE canopy 2022 (page updated March 2026, no later map), ESA WorldCover
  2021 v200, SB 535 2026 designation. **Outdated: the satellite window.** `SUMMER_YEARS`
  defaults to 2022–2024; summers 2025 and 2026 are in the archive. Los Angeles overrides it to
  2024–2026. **The five earlier builds were not rebuilt** and still carry 2022–2024: moving
  them changes every heat value and re-ranks the three that score heat, which is the owner's call.
- **Build.** `cities/losangeles/`: city limit (TIGERweb 0644000), res 9, UTM 11N; 11,893 cells,
  9,021 ranked, 3,856,571 residents (ACS place total 3,857,263). Landsat: 35 scenes (15/13/7 for
  2024/25/26). Canopy: USFS 2022 on 8,948 ranked cells, greenness stand-in on 73, no height
  model (02c not run, reasons in config.py). Population is dasymetric; `DASY_MAX_INCOME_BIAS =
  3.0` with the evidence in config.py (the 2.7x count-per-unit reading is apartment housing;
  one-unit block groups read 1.1–1.3 buildings per unit in every income quartile). Weights
  0.35/0.35/0.15/0.15 on measured evidence (position explains 8.8% of LST variance over ranked
  cells; LST vs canopy r = −0.66; LACE 44–100%). HOLC 1939 on 3,621 cells. SB 535 on 4,614
  cells (preset only). 15 council districts from the city's GIS service; each holds 244k–271k
  residents, which is what equal-population districts should hold. 153 county cooling sites
  from the county's own map layer (August 2026), 94 drawn. Fire flag: 129 ranked cells mostly
  inside the Palisades or Hurst perimeters; best rank among flagged cells is 4,172.
- **OpenStreetMap came from a local extract**, not Overpass: both mirrors timed out and the
  main instance answered "at capacity". `pipeline/00_osm_extract.py` (new, optional, needs
  `pip install osmium`; installed outside the venv for this run) read Geofabrik's
  `socal-261110.osm.pbf` and wrote buildings (1,667,445 footprints, 284 MB, gitignored),
  streets (24.6 MB, committed like every city's), place nodes and the walk graph (575,806
  nodes). The cool-place inventory (669 sites) is the one Overpass pull that succeeded.
  Names: place nodes alone mislabelled whole districts, so `NAME_AREAS` adds the 114 Mapping
  L.A. neighbourhood polygons from the City GeoHub.
- **Shared code touched:** `app/index.html` (fire note, tag, popover, export fields),
  `pipeline/{02b_buildings,04_overlays,04c_designated_cooling,05_score,config}.py`, new
  `pipeline/{00_osm_extract,04g_fire}.py`, `tests/*`, `scripts/sync_guide_facts.py`, every
  guide (`#fire` topic, regenerated column key), `app/cities.js`, `site/index.html`,
  `README.md`, `.gitignore`. Itemised in `cities/contracosta/FEATURES.md`.
- **Tests run:** `scripts/test.sh`, all six cities, passed (map contract incl. rank parity for
  all 9,021 Los Angeles cells, data contracts, guide facts and column keys, clean build).
  Verified in the local build (`scripts/build_site.py --serve`, port 8010): map loads with no
  console errors, live rescore of 11,893 cells takes about 12 ms, Priority and HOLC layers, the
  fire note and row tag on Pacific Palisades, 15 district outlines loaded, guide and cooling
  pages render. **Not verified:** a phone session, the printed briefing, exports opened in a
  spreadsheet, GitHub Pages serving a 13.7 MB data file (it gzips; untested live), and
  `06_audit_rebuild.py` (no baseline; `reports/` holds only the stability file).
- **Left to the owner:** commit and push (CI deploys on push to main); whether to rebuild the
  other five cities on summers 2024–2026; whether to rename the Los Angeles guide's and
  chooser's wording. `cities/losangeles/` has no STATUS.md or README.md history file.

## Checkpoint — November 2, 2026 (Claude): SB 535 disadvantaged communities (Bakersfield)

Task: Bakersfield's urban forestry contact asked for CalEPA's SB 535 Disadvantaged Communities
2026 designation as a layer and priority component (the city plants ≥80% of new trees in
designated tracts) for a City Council slide. Owner: advikar. Files: `pipeline/04f_sb535.py` (new),
`pipeline/config.py`, `pipeline/05_score.py`, `pipeline/05b_stability.py`, `app/index.html`,
`cities/bakersfield/{config.py,city.js,guide.html,data/sb535_bakersfield.{geojson,csv},data/bakersfield.geojson,reports/stability_bakersfield.json}`,
`cities/*/guide.html` (dac topic + column key), `tests/ui-contract.cjs`, `README.md`.

- **Data.** `04f_sb535.py` queries the CalEPA feature service
  `SB_535_Disadvantaged_Communities_2026` (tracts + three tribal layers) for the bbox and
  writes per cell `dac` (share of area inside a designated polygon, 0–1), `dac_type`
  (criterion) and `dac_tract`. Bakersfield: 92 Kern tracts in the box (68 CES 5.0 top 25%,
  24 CES 4.0 carry-over, no tribal land); 1,494 of 4,054 cells ≥50% designated, 1,320 of the
  3,767 ranked cells, holding 40% of residents; 67 of the top 100 ranked areas are inside.
  Gated by `SB535_URL` in the city config (None elsewhere → term 0, no layer).
- **Scoring.** New term `W["dac"] * dac` on a fixed 0–1 scale (no percentile clip) in 05,
  05b and the browser (`rescore`, `liveScoreExpr`, drivers, briefing). Recommended mix keeps
  `dac` at 0, so **no rank, score or stability band changed** (checked cell by cell against
  the previous file). New preset **"Disadvantaged communities"**: dac 35 / heat 30 / green 30 /
  age 5, population default. `W_INPUTS` adds the slider only where `city.js` declares
  `weights.dac`; old scenario files without the key load with it at 0 (`optional`).
- **UI.** "SB 535 community" map layer (purple ramp, hidden where no cell carries a share),
  detail and briefing metric rows, caption/driver text, export columns
  `sb535_dac_share_pct`, `sb535_dac_criterion`, `sb535_dac_tract`, `weight_sb535_community`;
  guide topic `#dac` in every city (the other four say the build does not carry it).
  `dataVersion` → `20261102-sb535`.
- **Tests run:** `scripts/test.sh` (all five cities) passed, including new contract assertions
  (dac keys in config.py ⇔ city.js ⇔ `SB535_URL`; share in 0–1 with a criterion iff > 0).
- **Audit (November 3, independent review + data recompute).** Fixed: tract GEOIDs lost
  California's leading 0 (now 11 digits); the ArcGIS `exceededTransferLimit` flag was read
  from the wrong place so a >2,000-tract bbox would have truncated silently (04e now pages);
  null geometries / GeometryCollections from `make_valid` are handled; a pre-change share
  link with five `w=` values reads the SB 535 weight as 0 instead of being ignored;
  `#layer=dac` on a build without the layer falls back to Priority; the briefing source table
  and `metadata.stability.held_fixed` name the designation; guides say "the weights in force"
  rather than "five weights" and non-Bakersfield column keys omit `weight_sb535_community`.
  New contract cases: dac-weighted browser score equals an independent recompute and the
  top 50 under the preset are designated; a five-weight scenario file loads with dac = 0.
  Data verified: per-cell shares match an EPSG:3310 recompute within 0.0005; centroid-in-tract
  agrees with share ≥ 0.5 for all 1,494 cells; 92 of Kern's 122 designated tracts fall in the
  bbox; service last edited September 2026. `reports/stability_bakersfield.json` is unchanged.
- **Not done / decisions left to the owner:** the recommended mix is unchanged; the city's
  email asks for DAC + canopy + heat to lead, which the preset does. Making it the default
  would re-rank the city and re-run 05b. Not committed or pushed.
## Checkpoint — October 13, 2026 (Claude): basemap tone per theme, shorter disclaimer

- Street basemap (CARTO Positron) ground is toned to the chrome's map grey and water a
  shade deeper in the **dark** theme only (`toneBasemap`/`retoneMap` in app/index.html);
  the light theme keeps Positron's own near-white ground. Switching theme re-tones the
  live map. Done on the style's own layers, not an overlay (a veil washed out roads
  and imagery).
- Disclaimer on every page shortened to "Independent student project. Not a city or
  county product." (app, guide and cooling pages, all cities). README prose and the
  guide "field note" sentences were left as they were.

## Checkpoint — October 13, 2026 (Claude): ward and city-limit cartography

Files: `app/index.html`, `scripts/build_site.py`. Ward and district borders redrawn to
professional standard: a soft white casing under a thin desaturated dashed line (the pure
black ring is now only the selection); one label per ward in tracked uppercase at the largest
part's centre, with collision avoidance; a legend key with the member date while the toggle is
on; the basemap's own county and state lines rest while ours show; a solid city outline (from
04d jurisdictions, now served as an optional data file) whenever one city is chosen in "Show";
hovering the border highlights the ward and shows member, residents, mean need and top-100
count; clicking the border limits the list. Tests: `scripts/test.sh` all cities. Verified in
the local build on Bakersfield (wards) and Contra Costa (districts + Richmond outline).
Also: the study-area limit (the pipeline's clip polygon, the real city or county line with
county islands as holes) is now drawn above the hexagons as a solid slate line on a white
casing instead of a faint grey under them, with a "city limit" / "county line" / "study area"
legend key worded by `CE_CITY.scope`. The hexagon edge stays quiet. Verified on Bakersfield.
Second pass after review: the limit is lighter and thinner (slate `#55657a`, 1.3–2.2 px on a
soft casing), and a light veil (`outside` fill, 50% off-white) covers everything beyond the
limit, including county islands, so the colour stops at the line and the edge reads as
continuous where whole hexagons straddle it. Outside cells stay readable and clickable.
Third pass: the basemap's road lines sit above the choropleth by design, so the limit was
cut by every white road casing crossing it; the limit (casing + line) is now moved above the
last basemap line layer, still below place labels, so it draws continuously over roads.
Correction: the outside veil also faded the street map and the satellite imagery beyond the
limit. Removed; instead the hexagons that lie mostly outside the limit (inside_frac < 0.5)
are painted at 45% of the fill opacity, so the basemap keeps its full contrast everywhere.

## Checkpoint — October 13, 2026 (Claude): UI and feature audit

Task: exercise every option on every city and report. Owner: advikar. Files: `app/index.html`
(one fix), `docs/UI_AUDIT_2026-10-13.md`.

- **Done:** scripted walk of presets, sliders, nine layers, every filter and sort, search, paging,
  rows, detail, scenario inputs, field checks, every export, briefing build, share link, scenario
  reload, reset, units, theme, panel, legend, basemap, popovers, aria basics, on all five cities;
  phone layout, chooser, guide, cooling page; link and anchor crawl of the built site. No
  functional defects. Fixed: the optional ward fetch no longer logs a 404 where a city has no
  district source. Findings and suggested improvements in `docs/UI_AUDIT_2026-10-13.md`.
- **Tests run:** `scripts/test.sh` (all five cities).
- **Left for later:** phone detail header wrapping; need-versus-room scatter; off-street band.

## Checkpoint — October 12, 2026 (Claude): street room layer and row labels

Task: show feasibility beside need (reviewer feedback). Owner: advikar. Files: `app/index.html`,
`cities/*/guide.html`.

- **Done:** `roomOf(p)` = tree spots the mapped street centrelines inside the boundary hold at
  10 m on both sides (the scenario's own ceiling), stamped onto every feature at load.
  "Street room" map layer (deeper = less room, keeping the deeper-means-more-need rule), a
  fourth mini-column on every row (none / little / some / plenty, city-relative thirds of ranked
  areas with any mapped street), a detail metric with the count, `street_room_tree_spots` and
  `street_room_band` in exports (column key regenerated), a Room column in the briefing's top-25
  table, a `#room` guide topic and popover.
- **Tests run:** `scripts/test.sh` (all five cities). Verified in the local build on Bakersfield.
- **Left for later:** a need-versus-room scatter in the briefing; city right-of-way, utility and
  sidewalk layers to replace the OSM upper bound.

## Checkpoint — October 12, 2026 (Claude): ward/district roll-up, provenance, licence

Task: bring the ward work from the `one-repo` branch of `advikar/coolequity` into this
repository. Owner: advikar. Files: `pipeline/04e_wards.py`, `pipeline/sources.py`,
`pipeline/config.py`, `pipeline/05_score.py`, `cities/{bakersfield,contracosta,sanramon}/config.py`
and `city.js`, `app/index.html`, `cities/*/guide.html`, `scripts/build_site.py`,
`tests/test_data_pipeline.py`, `LICENSE`, `PRIVACY.md`, `README.md`.

- **Done:** `04e_wards.py` (04c was taken by designated cooling) fetches each configured city's
  ward or district layer from its own GIS service, assigns every grid hexagon by centre, writes
  `wards_<slug>.{geojson,csv}` and `wards_summary_<slug>.csv`, stamps `ward_id`/`ward_name` onto
  the scored output and records the fetch in `data/SOURCES.md`; `05_score.py` merges the CSV on
  rebuilds. App: "By ward/district" section with the roll-up table (residents, mean need under
  the current mix, areas in the top 100, starred trees and cost), map outline toggle with labels,
  ward filter, row tags, ward on the detail header, `ward_id`/`ward_name` in exports (column key
  regenerated), a By-ward page in the briefing; `districtUnit` and `wardsOutsideLabel` in
  `city.js` drive the wording. Guides gained a `#wards` topic. `build_site.py` serves the ward
  file when present. `LICENSE` (MIT + CC BY 4.0, Advika Richhariya) and `PRIVACY.md` added.
- **Tests run:** `scripts/test.sh` (all five cities) passed after the port: map contract, column
  key and guide facts in sync, pipeline contracts (incl. the new `WardRollup` check), clean site
  build. Verified in the local build on Bakersfield: section, filter, outlines, exports.
- **Not verified:** printed briefing pagination with the extra page; a phone session.
- **Left for later:** sources for West Contra Costa (several cities) and Pittsburg; calling
  `sources.record()` from the satellite, census and OSM stages so `SOURCES.md` is complete.

## Checkpoint — September 21, 2026 (Claude): outreach-readiness audit fixes

Task: apply the release-integrity findings of `reports/OUTREACH_READINESS_AUDIT_2026-09-21.md`
(kept in the old `coolequity` checkout) to the deployed app. Owner: advikar. Files: `app/index.html`,
`site/index.html`, `cities/*/city.js`, `cities/*/guide.html`, `tests/ui-contract.cjs`,
`cities/contracosta/FEATURES.md`. Next checkpoint: `scripts/test.sh` green, then push.

- **Done (see the September 21 entry in `cities/contracosta/FEATURES.md` for the full list):**
  unique CSV headers with `study_area_slug` and the planting assumptions on every row;
  greenness stand-ins export on the displayed 0–100 index; scenario files restore field checks
  (file wins only when local is empty or older; kept records are counted in the message) and
  the shortlist; cost scope (`COST_SCOPES`/`costScope()`) travels through detail, exports and
  briefing; briefing sources counted from the data and `CE_CITY.popAllocation`; model text
  states the real clipping bounds and the bounded population factor; share links keep slider
  precision, honor `access`/`holc` and carry a data fingerprint with a stale-link toast;
  `fitData()` reserves panel width only while the panel is open; guide/chooser copy drift fixed;
  `dataVersion` `20260909-walk` → `20260913-stability`; chooser About / feedback / privacy section.
- **Tests run:** `scripts/test.sh` (all five cities) passed, including new contract assertions
  for unique CSV headers, the greenness scale and the field-check/shortlist round trip. Verified
  in the local build (`scripts/build_site.py --serve`) on Bakersfield: `toCsv()` headers unique,
  proxy cell "Southland R.V. Park SW 2" exports 13 as displayed, `#layer=access&d=deadbeef`
  opened the access layer and showed the stale-data toast, Base $2,000 changed the detail
  sentence to establishment-care scope, `loadScenario()` restored a field note and a shortlist.
  Not verified: printed briefing pagination, a real phone session, screen-reader pass.
- **Left for later:** free-text custom cost scope; serializing layer/filter/sort; a non-GitHub
  contact address (none exists in the repo to publish); mobile and accessibility passes.
- Pushed by the owner as `efacd64`; CI test/deploy/smoke passed; live site checked.
- Follow-up sweep: guides no longer describe the removed Simple/Explore modes; Pittsburg guide
  links to its own data and config instead of West County's. `scripts/test.sh` re-run.
- GoatCounter wired into `scripts/build_site.py`: reads `site/goatcounter.txt`, injects the
  tag before the first `</head>` of the chooser and each city's app, guide and cooling page, and
  a visible sentence into the chooser's privacy note. File is committed empty; the owner signs
  up at goatcounter.com, writes the code, pushes. Verified: 16 pages tagged with a test code,
  none without.

## Checkpoint — September 13, 2026 (Claude): West Contra Costa build, county canopy recovery

- **New city `westcc` (West Contra Costa).** Study area = union of 16 TIGERweb place polygons
  (Richmond, San Pablo, El Cerrito, Pinole, Hercules + 11 CDPs), committed as
  `boundary_westcc.geojson`; res 9; 2,651 hexes, 982 ranked, 271,620 residents. Chosen from the
  county build (these places hold 60 of the county's top 100). Full pipeline run 01→05 plus 04c.
  Dasymetric check passed (0.63 coverage). 975 ranked cells on USFS 2022 aerial, 7 height model,
  8 stand-in. A/C: 981 LACE, 1 income-model (suppressed tract; the data contract now allows
  ≤0.5% of such cells). No HOLC map exists for Richmond, CA (the 1937 Oakland map touches only
  0.1 km² of Kensington).
- **Heat is scored in westcc (0.35/0.35/0.15/0.15)** on evidence recorded in its config.py:
  position explains 11.1% of LST variance here vs 38.8% county-wide, and LST vs greenness
  r = −0.64.
- **County canopy recovery.** Discovery Bay USFS package added (37 cells, 10,140 residents to
  aerial). `02c_canopy.py` now records per-cell tile coverage and flat fraction, writes a tile
  log and stops on tile failure; the rebuilt legacy file read all 24 tiles, so every county
  cell has a canopy value (400 formerly unassessed cells now carry 2009–2020 height-model
  values, tagged). `CANOPY_MIN_COVERAGE = 0.10`: aerial assessments covering under 10% of a
  cell fall back to the stand-in (131 county cells).
- **Not yet done for westcc:** `06_audit_rebuild.py` (no baseline), `reports/` folder is
  empty, `cooling.html`/`guide.html` are the county pages with numbers and scope rewritten
  rather than written fresh. Buildings file (42 MB) is gitignored like the county's.

## Checkpoint — September 13, 2026 (Claude): audit fixes before sharing with city staff

- **Map page.** Opening an area no longer marks the session unsaved (only a moved planting
  slider does; `userShares`). A/C driver copy now reads "homes without A/C (N% lack it)". The
  legend caption element existed only in code; it is now in the DOM. Dead Simple/Explore mode
  code removed. Hover and centers popups escape `land`/`kind` from the data files. Landsat
  wording is "late morning", not "afternoon" (also in every guide's sort glossary). Share-link
  hash rejects NaN/all-zero weights; `SITE_ROOT` tolerates an explicit `index.html`. Minimum
  type size in the panel is 11px. Hackathon-era comments and the hard-coded LA map centre are gone.
- **Start screens.** `CE_CITY.introNote` renders under the Explore button; Contra Costa uses
  it to say heat is shown but not scored. The chooser page no longer says "reference build" /
  "current build" / "severity case".
- **Bakersfield A/C weight 0.25 → 0** (heat 0.45, canopy 0.35, age 0.20): LACE runs 96.5–100%
  across ranked cells, so the old term scored model noise. `05_score.py` re-run; ranks moved
  a lot (top-25 overlap with the previous build 4/25, median |rank move| 230). Guide, README
  and city.js updated. Not yet audited with `06_audit_rebuild.py`.
- **Pipeline.** `03_census.py` now stops when the LACE CSV is missing unless
  `COOLEQUITY_ALLOW_INCOME_MODEL=1`; README lists the two hand-downloaded inputs.
- **Audit round 2 (same day).** Scenario files round-trip cost per tree; the export hint says
  what a copied link actually carries; greenness stand-ins read "greenness" in the list, export
  as `greenness_index_0_100` with `tree_cover_pct` empty, and are excluded from the "Trees < 10%"
  filter; the duplicate "Export & reload" guide article in Contra Costa and San Ramon is removed;
  Reset map also clears filters, sort direction and the cost per tree. Pushed.
- `scripts/test.sh` passes for all three cities.

## Checkpoint — September 12, 2026 (Claude): city switching no longer carries weights over

- Fix (c28a40b): app/index.html saves the per-tab state under `ce-session-<slug>` instead of one
  shared `ce-session`. Theme, units, mode, legend and folds stay shared (localStorage); the
  shortlist was already per city. tests/ui-contract.cjs now fails if sessionStorage is used
  through anything but a city-scoped SESSION_KEY.
- Tests: `scripts/test.sh` passed locally and in CI. The first deploy job sat queued with no
  runner for ~40 min (no approvals pending, GitHub status operational); cancelled and re-ran,
  attempt 2 passed test + deploy.
- Verified on the live site in one tab: Contra Costa with "Heat only" → city switcher to
  Bakersfield opens Bakersfield's recommended mix (35/25/25/15, "Recommended mix" selected) →
  switcher back to Contra Costa restores "Heat only". No console errors. Old `ce-session`
  entries from the old site are ignored.

## Checkpoint — September 12, 2026 (Claude): repository created from the three city branches

- **What this is.** A fresh repository (`advikar/coolequity-app`, branch `main`, one initial
  commit) combining the `contra-costa`, `san-ramon` and `bakersfield` branches of
  `advikar/coolequity` into one codebase. Sources: contra-costa `cc013b8`, san-ramon `872a314`,
  bakersfield `8219aad` (each equal to its origin branch on September 12). The old repository
  and its live site are unchanged; Los Angeles (`master`) was deliberately not carried over.
- **How the cities were merged.**
  - Shared code (`app/`, `pipeline/`, `tests/`) comes from contra-costa. City differences moved
    into `cities/<slug>/config.py` (pipeline) and `cities/<slug>/city.js` (map page), both
    generated from that city's branch. Every UPPERCASE pipeline setting was compared against
    each branch's own `pipeline/config.py`: zero differences for all three cities.
  - Pipeline code differed in two places. `03_census.py` takes San Ramon's version (the
    dasymetric check is judged over the study area's block groups with all pulled buildings);
    it cannot change Contra Costa (the county is the study area and its mask is refused anyway)
    or Bakersfield (no buildings file, so the check never runs). `02_satellite.py` keeps the
    per-tile scene cap, with `SCENE_CAP_PER_TILE = False` on San Ramon to reproduce its
    committed composites.
  - Map page: one behavioural difference was unified. The A/C layer now greys out cells whose
    `ac_src` is `income-model` (the San Ramon/Bakersfield rule); Contra Costa's old rule greyed
    anything not `lace`, which is identical on its data (only `lace` and `income-model` occur).
  - Guide and cooling pages stay per city (their text and numbers are city-specific). GitHub
    links in them were rewritten to this repository. San Ramon's and Bakersfield's guides linked
    a `DATA_QUALITY.md` their branches never had; those links now go to Contra Costa's audit.
  - Data: only each city's own `*_<slug>` files from its own branch. The 82 MB
    `buildings_contracosta.geojson` committed on the san-ramon and bakersfield branches was left
    out (gitignored on contra-costa, not an input to any result).
  - Docs: each branch's `STATUS.md` and `README.md` are in `cities/<slug>/` as history;
    Contra Costa's `FEATURES.md`, `DATA_QUALITY.md`, `FINDINGS_CONTRACOSTA.md` (now
    `FINDINGS.md`) with it. Brief, spec, reviews, delivery plan and deck are in `docs/archive/`.
    The old contra-costa checkout had uncommitted Codex notes in DATA_QUALITY/FEATURES/STATUS/
    HANDOFF (a Sept 8 "live release verified" paragraph and older handoff checkpoints); those
    were not copied.
  - Deploy: GitHub Actions (`.github/workflows/pages.yml`) replaces `deploy.sh` and the
    `gh-pages` branch.
- **Tests run before the initial commit.** `scripts/test.sh` — `node tests/ui-contract.cjs`
  PASS for contracosta, bakersfield and sanramon (all 5 groups each, including browser/export
  rank parity for every residential cell with that city's weights); Python data contracts
  8/8 OK per city; `scripts/build_site.py` builds 3 cities, 48 files.
- **Deployed and verified (September 12, 2026).** First Actions run passed (test + deploy).
  In a browser, each city on https://coolequity.org/ was loaded next to the
  same city on the old site (https://advikar.github.io/coolequity/, built from the same three
  commits) with session storage cleared: identical page text (apart from Los Angeles leaving
  the city switchers), identical rank and score for every residential area at the default
  weights, identical default weights, presets, input notes, layer titles/captions, data and
  cooling-site URLs; every live rank equals the pipeline's `rank`. The only code-level
  difference is the A/C grey-out rule above (equivalent on Contra Costa's data). Chooser,
  guide and cooling pages, data files, fonts, city.js and cities.js return 200; city
  switchers resolve to /coolequity-app/<slug>/app/.
- **Pre-existing bug found (also on the old site):** one shared sessionStorage key carried a
  city's weights into the next city. Fixed in the checkpoint above.

## Checkpoint — September 13, 2026: designated cooling layer clipped to study area

- `04c_designated_cooling.py` keeps a located site only if it is inside the study-area
  boundary padded by 1.5 km; the rest go under `outside_study_area` in the GeoJSON's
  top-level properties (with coordinates, so nothing is dropped silently). Result: county 17
  drawn; West Contra Costa 3 drawn / 14 listed; San Ramon 1 / 16; Bakersfield 1 / 8 (+1 not
  located: Frazier Park). The map toggle text reports both counts.
- `tests/test_data_pipeline.py` now checks that drawn designated points fall inside the
  city's BBOX and that drawn + outside + unlocated equals the directory's site count.
- West Contra Costa guide said walking estimates use "486 discovery sites" (county number);
  corrected to 39.

## Checkpoint — September 13, 2026: Pittsburg & Bay Point build; water/wetland rule in area weighting

- **New city `pittsburg`.** Study area = union of TIGERweb Pittsburg city (0657456) and Bay
  Point CDP (0604415), committed as `boundary_pittsburg.geojson`; res 9; 755 hexes, 570
  ranked, 89,581 residents. 518 ranked cells on USFS 2022 aerial (Antioch + Concord packages
  copied into its cache), 52 height model, 16 stand-in. A/C: all LACE, 69–96%.
- **Heat is NOT scored (county weights 0/0.55/0.25/0.20).** Measured on this build: among
  residential cells above 35 °C, lon/lat explain 28% of LST variance (county 39%, West CC
  11%) and LST correlates +0.25 with aerial canopy (hillside subdivisions are hotter and
  greener). Recorded in config.py, city.js and the guide's Surface heat topic. The first
  draft of this build scored heat at 0.35; do not reintroduce that without new evidence.
- **Area-weighting fallback now excludes water/wetland** (`UNINHABITABLE_LAND` in
  03_census.py, from 02e WorldCover's dominant class). Triggered by 3,796 residents on
  Pittsburg's shoreline marsh. Bakersfield re-run (needed LACE copied into its cache):
  351 residents moved, ranked 3,788 → 3,767, top 25 unchanged; guide, README, chooser and
  test counts updated.
- **Pittsburg caveats:** OSM building mask covers 8% of housing so dasymetric placement was
  refused (area weighting, said in the guide); only 8 OSM cool places exist (same as the
  county build finds), so walking times are long (median 43 min) and read as a map-coverage
  caveat; 2 county-listed sites are in the area; no HOLC map; Overpass needed three mirrors
  for streets. `06_audit_rebuild.py` not run (no baseline); `reports/` empty; guide and
  cooling pages are rewritten West CC copies.

## Checkpoint — September 13, 2026: chooser/panel friction; survival in planting scenarios

- Chooser cards and the in-map city switch open the map directly (`?go=1`); the start screen
  stays for direct links and the home button. `CE_CITY.introNote` also renders under the
  panel lead (`#pnote`). "Color the map by", "Places to cool off", "Export & share" start
  folded (`FOLD_CLOSED_DEFAULT`; a viewer's own toggle is remembered).
- Planting scenarios: `SURVIVAL` (default 70%, `#survival` input). `scenarioFor` returns
  `trees` (planted, carries cost) and `trees_surviving` (carries canopy gain, cooling,
  `new_crown_m2`, `future_canopy_pct`). Scenario files carry
  `planting_assumptions.survival_share_pct`; files without it load at 100% so they reproduce
  what they showed. Test contexts seed `SURVIVAL:70`. Every guide's Planting and Cost topics
  describe it, citing Ko, Lee, McPherson & Roman 2015 (42.4% alive at 22 years).

## Checkpoint — September 13, 2026: rank-stability bands (05b)

- `pipeline/05b_stability.py` runs after 05 and rewrites `<slug>.geojson` in place with
  `rank_lo`, `rank_hi`, `rank_top_share` per residential cell and `metadata.stability`;
  summary in `cities/<slug>/reports/stability_<slug>.json`. Inputs: acs_<slug>.csv MOEs,
  `_cache/bg_2024_06.zip` (copied into every city cache), `_cache/ac_src/LACE_23_Tract.csv`
  (AC_PM). Seeded (20260913), 300 draws, ~2 s per city. Re-run it after any 05 re-run or
  the bands go stale (the ui-contract test only checks shape, not freshness).
- App: `#d-band` under the rank line, `stability` popover, export columns
  `rank_recommended_mix_p05/p95`, `top_tier_share`; guide anchor `#stability` inside the
  Score topic of every city.

## Checkpoint — September 13, 2026: jurisdiction per cell; phone view switch

- `pipeline/04d_jurisdiction.py` (new, before 05): TIGERweb places layers 4/5 for the bbox,
  cell centroid in polygon, cities before CDPs; writes `jurisdiction_<slug>.csv` and
  `jurisdictions_<slug>.geojson` (outlines, not yet drawn by the app). 05 merges `city` and
  `city_kind` into the contract. All five cities re-run through 05 and 05b (ranks unchanged).
- App: `#rank-city` "Show" menu (`RANK_CITY`, session-only, cleared by Reset map) filters the
  list and fades other cells via `applyCityMask()`; the detail rank line and hover show the
  city; export column `city_or_community`. Phone-only `#mview` List/Both/Map segment
  (`ce-mview` in localStorage) toggles `#app.mv-list` / `#app.mv-map`.

## Checkpoint — September 13, 2026: field checks; post-deploy smoke test

- Field checks: `NOTES` map, localStorage `ce-fieldcheck-<slug>`, `#d-field` box (status
  select + note), `fieldTag()` in rows, `field_status/field_note/field_note_updated` in
  `cellRecord`, briefing shortlist section, `fieldcheck` popover and guide anchor. Reset map
  does not clear them (work product). Test contexts stub `noteOf` and `FC_LABEL`.
- `.github/workflows/pages.yml` gained a `smoke` job after `deploy` (curls every city's five
  URLs on the live site with retries; fails the run if any is not 200).

## Checkpoint — September 13, 2026: shortlist compare; American spelling

- `#sl-compare` toggles `SL_COMPARE` (localStorage `ce-slview`); `compareTable(items)` renders
  up to six starred areas as columns; column headers open the area. Briefing top-25 table has
  City and Likely rank columns; shortlist headings carry band, city, id.
- User-facing copy converted to American spelling (color, center, program, meters, normalized,
  labeled, gray). OSM tag value `community_centre` and the CDP name "Contra Costa Centre"
  are untouched on purpose.

## Checkpoint — September 13, 2026: study-area topics in the West CC and Pittsburg guides

- New first topic `#area` ("About this study area") and rewritten `#findings` in both guides,
  with numbers taken from the current data and `reports/stability_<slug>.json`. If a build
  is re-scored, refresh those numbers by hand (they are prose, not generated). Method topics
  intentionally match the county guide word for word.


## Checkpoint, September 13, 2026 (evening, eleventh pass)

- Cost per tree now has Low/Base/High presets ($500 / $2,000 / $3,500) with sources on hover and in every guide's cost topic; `markCostPreset()` keeps the chips in step with the input, reset and scenario load. Default unchanged at $500 (low band).
- `docs/EVIDENCE_COST_CANOPY_2026-09-13.md` records the cost sources, per-source canopy accuracy from the literature, and a specified but unrun `02f_canopy_validate.py` against CDFW ds3206 (lidar canopy cover, Contra Costa; 160 MB zip, needs owner approval to download).
- Outreach plan §3.1 has 18 ready-to-send email drafts, one per contact, each naming a top area from that contact's map.
- Later the same evening: 02f run against CDFW ds3206 for the four Contra Costa builds; 05 harmonises sources (height model → aerial line; stand-in → lidar canopy) when `data/canopy_lidar_<slug>.csv` and the validation report exist. Re-scored and 05b re-run for contracosta, westcc, pittsburg, sanramon. ui-contract EXPECT ndvi counts now 5/1/0/0. The 160 MB gdb lives outside the repo (scratchpad); re-download from CDFW to re-run 02f. Keep 02f before 05 in any rebuild, else 05 falls back to pooled sources and the EXPECT counts fail.


## Checkpoint, September 21, 2026 (re-audit fixes, done)

Task: apply `../coolequity/reports/REVIEW_READINESS_REAUDIT_2026-09-21.md`. All ten findings were
re-verified against source and live before editing. Order: (1) `site/goatcounter.txt` back to
`coolequity` (the account now exists; `YOUR-CODE` was committed literally and failed CI);
(2) 05b started from the already-smoothed `pct65` and smoothed again — now starts from the raw
census share and smooths once; all five builds re-run; (3) save protection compares a signature
(weights, shares, cost, survival) against the last saved/loaded state; (4) light-theme contrast
for `.why` and field-check pills; (5) Tab loop in both modals; (6) guide column keys generated
from `FIELD_KEY` by `scripts/sync_column_key.py` + contract test; (7) compare-table band label;
(9) briefing lede lists active inputs, page count no longer promised; (10) analytics tag skipped
under `?flat=1`, privacy sentence made precise. Left for later: UI rearrangement and renames
(finding 8 and the wording table), physical-phone and print-PDF passes.

Done and tested (`scripts/test.sh`, all cities; browser: contrast, Tab loop, cost-only warning, `?flat=1` off-host check). See `cities/contracosta/FEATURES.md` for the itemised list. To re-run sensitivity after any re-score: `COOLEQUITY_CITY=<slug> .venv/bin/python pipeline/05b_stability.py`, then paste the median band / top-tier share from `reports/stability_<slug>.json` into that guide's `#stability` topic (prose, not generated). Column keys: `python3 scripts/sync_column_key.py` after any `FIELD_KEY` edit.

## Checkpoint, September 22, 2026 (re-audit finding 8 + wording, minimal, done)

Phones default to List (a saved choice still wins); "What matters most" starts folded so the ranked
areas sit above the fold on a laptop (its head still says which mix is in force; a saved fold state
wins); labels that misdescribed what they do renamed: "Trees only" → "Fewest trees", "Full aerial
tree data" → "Aerial coverage ≥99%", "Briefing report (PDF)" → "Printable briefing", "Ranking (CSV)"
→ "All ranked areas (CSV)", mix bar "People" → "Population". Guides follow. Headline, walk labels
and "Recommended mix" kept on purpose.

## Checkpoint, September 24, 2026 (chooser as a blended start screen; badge width, done)

Chooser: hero in the style of the city start screens (hex canvas backdrop, wordmark, eyebrow,
the chooser's headline, a Study-area select top right that fills the stat row and the Explore
button), then the five cards, note, about, contact, privacy, footer as before. List/shortlist
rank badge fits three digits.

## Checkpoint, September 24, 2026 (evening): panel resize, guide city switch, chooser hero (done)

Map panel: drag grip on its edge (min 366px, the width the controls were designed for; max
720px or what leaves 420px of map), a collapse button that hides it and a floating "Show panel"
button that brings it back; both remembered per browser (`ce-panelw`, `ce-pcol`). Guide: a
city select in the header (from cities.js), goes to the same page in the other build. Chooser:
hero full-bleed like the city start screens, bigger hexes in the map palette, select in the
viewport corner; the five cards are gone, the Explore button opens a study-area menu until one
is chosen.
