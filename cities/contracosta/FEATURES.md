> Carried over from the `contra-costa` branch of [advikar/coolequity](https://github.com/advikar/coolequity/tree/contra-costa) on September 12, 2026. File paths in it refer to that branch (e.g. `data/` is now `cities/contracosta/data/`, `app/guide.html` is now `cities/contracosta/guide.html`).

# CoolEquity — every feature, its data source, and its limitations

## Update — September 21, 2026: outreach-readiness audit fixes (shared app, all builds)

Findings 1–6 and the sharing/layout items of `OUTREACH_READINESS_AUDIT_2026-09-21.md`
(kept in the old `coolequity` checkout under `reports/`).

- **CSV exports** now have unique headers: the build slug is `study_area_slug` and the cell's
  city stays `city_or_community` (both were `city` before, and the slug was lost). Every row
  also carries `cost_per_tree_usd`, `cost_scope`, `survival_share_pct`, `tree_spacing_m`,
  `crown_m2_per_tree` and `cooling_c_per_10_canopy_points`, so a colleague can reproduce the
  scenario without inferring settings from rounded results. The contract test checks all of it.
- **Greenness stand-ins** export `greenness_index_0_100` on the 0–100 index the app displays
  (the stored value is on a 0–45 scale; Bakersfield's 62 proxy cells exported the raw value).
- **Scenario files restore field checks** (status, note, time) and, for ranked-list files, the
  shortlist. Conflict policy, stated in the load message: a file record replaces a local one only
  when this browser has none for the area or the file's is newer; otherwise the local record is
  kept and counted. "Exact view" wording is gone; copy names what a file and a link carry.
- **Cost scope travels with the price.** `COST_SCOPES` records what each preset covers
  (Low $500 planting only; Base $2,000 with establishment care; High $3,500 three-year program;
  a typed figure is labelled as the user's own). The detail note, export notes, JSON
  `planting_assumptions.cost_scope`, CSV and briefing all read it; the hard-coded "planting only
  at $500" sentence is gone.
- **Briefing** source table now counts tree-cover sources from the data (`canopySourcesLabel`)
  and reads the population method from `CE_CITY.popAllocation` (area in the county, Bakersfield
  and Pittsburg; dasymetric in San Ramon and West County). The model description states the
  per-input clipping bounds from the data file and the bounded population factor. Proxy cells are
  labelled greenness, not tree cover. Likely-rank bands are labelled as recommended-mix
  sensitivity ranges, not confidence intervals; the "noise" sentence is replaced in the
  popover, briefing and all five guides.
- **Share links** carry raw slider positions to two decimals (rounded normalized weights could
  change ranks), honor the `access` and `holc` overlays, and carry an 8-character data
  fingerprint; a link made on an earlier data release shows a warning toast.
- **Map fit** reserves room for the detail panel only while it is open and on the side it
  opens on, instead of 360 px on the right always.
- **Copy:** county guide cell counts corrected to 2,697 / 7 / 155; the "margins not yet
  propagated" and "survival is not modeled" sentences replaced in every guide; chooser
  describes the height-model and lidar sources, gives San Ramon's heat/greenness correlation as
  −0.67 (Pearson over all 419 ranked cells, previously −0.60), carries a release date of
  September 21, 2026 and an About / feedback / privacy section. `dataVersion` for the three
  builds still tagged `20260909-walk` is now `20260913-stability`, matching the data's
  stability computation date.
- **Own sweep after the audit (same day):** all five guides still described the removed
  Simple/Explore modes in the "Layers, units, basemaps & session state" topic; rewritten for the
  single panel. The Pittsburg guide's data download and "Default weights" links pointed at West
  County's files; now Pittsburg's. Live builds load with no console errors; a 375 px viewport
  shows no horizontal overflow.
- **Not done here:** a free-text custom cost scope, serializing layer/filter/sort state,
  a mobile or accessibility pass, a non-GitHub contact address.

## Current update — conditional scenarios and official cooling sources

September 7, 2026; Contra Costa branch only. This supersedes the earlier 99%-coverage
scenario gate. Coverage is the fraction assessed, **not a percentage accuracy score**.

- Conditional tree counts, cost, added canopy and illustrative air cooling now require
  mapped street capacity and valid area: **1,832 residential cells**. The former blanket
  exclusion was unnecessarily restrictive for scoping. None of these outputs certify
  plantability or budget accuracy; 10m spacing, 40m² new crown and $500/tree remain assumptions.
- `canopy_baseline_ok` retains the >=99% aerial-coverage check only for displaying a
  whole-cell current-to-future canopy total (788 residential cells). Partial or unknown
  coverage displays added canopy but omits a future total. Known aerial canopy area bounds
  the maximum possible new area without extending partial coverage over unassessed land.
- UI replaces “pts” with **percentage-point canopy gain**. Guide example: 10% → 15% is
  +5 percentage points. Added crowns and cooling require feasible, non-overlapping new cover.
- Cooling is explicitly **summer air cooling**, not surface-temperature change. A surface
  response formula has not been added: cross-sectional tree/urban LST differences are not
  a validated marginal intervention response for Contra Costa. Surface shading benefits are
  explained without inventing a local degree reduction. Source: Schwaab et al. (2021),
  https://pmc.ncbi.nlm.nih.gov/articles/PMC8611034/.
- Added searchable **county-listed cooling directory**, 17 locations with addresses and
  phone links. Source: EHSD bulletin, June 2026 revision, served at the July 2026 URL and
  checked September 7. No open-now status, coordinates, hours or unrestricted eligibility
  are invented. The source asks visitors to call before going.
- The same bulletin identifies El Cerrito and Kensington libraries as lacking A/C. Both
  are excluded by exact name/kind from the discovery inventory (488 → 486); walking
  estimates rebuilt against the remaining discovery sites. The official directory is a
  distinct reference, not the denominator of the walking layer.
- Routing now projects cells before finding centroids, exports the cell-to-network straight
  connection length, and flags connections >100m for approach review. The flag is an
  operational review trigger, not assurance that shorter approaches are safe or accessible.
- Failed optional-site loads now show a status message and retain access to official contacts.

Remaining: official-site coordinates/entrances, hours and eligibility verification; routing
against that service set; local species/growth/survival and cost validation; uncertainty
propagation and full surface-model development. No public deployment has occurred.


## Current release — data rebuild and public exploration, September 7, 2026

Supersedes the historical UI-only pass below. **Contra Costa branch only; local, unpublished.**

- Explore now separates **Tree canopy** and **Vegetation greenness**. All grid cells can display
  environmental layers; Priority alone mutes uninhabited land. Greenness is an index, not cover
  percent. No public lawn/plantable-ROW layer is inferred from incompatible measurements.
- Planting layout leads with **trees, canopy gain, indicative cost**. Air cooling is secondary,
  rounded to a tenth of a degree (or <0.1), tied to clear-sky summer conditions in the guide.
  Surface heat stays an existing-condition layer. No financial return is calculated.
- Scenarios require >=99% USFS aerial coverage, with clear unavailable states for partial,
  legacy height-map and NDVI cells. 788 residential cells currently qualify; the capacity
  slider still selects 0–100% of theoretical mapped street capacity.
- Updated ACS 2024 demographics and housing-weighted LACE produce 2,697 residential ranks.
  Source, coverage and vintage accompany exports. Score export and live UI agree exactly on
  ordinal ranks; displayed scores agree to rounding. Default top 25 overlap is 24/25.
- Source/method guide, owner review and data audit reflect the rebuild. Coverage guards do not
  imply field-verified sites; local costs, species/growth/survival, verified facilities, uncertainty
  propagation and scenario sharing remain subsequent work.


## Latest: pitch and source-audit revision — September 7, 2026

This supersedes the earlier UI-pass section where behavior differs.

- Guide: **Use it to** describes city workflows; **Why this approach** explains choices;
  **Source & calculation details** is expandable; **Planning note** contains only concise,
  decision-relevant qualifications. References include CAL FIRE, Census, CDC, USGS and JRC.
- Info rings are visually 16px with 24px clickable targets. Guide search indexes actual
  article text, including rationale and source names; technical disclosures have independent
  expand states. No claim that project weights/assumptions are externally optimal.
- Area search and 25-row pagination cover every ranked residential cell; facility filters
  use native buttons. Startup storage access is guarded; map/data failures show recovery
  actions; third-party names are HTML-escaped.
- **Canopy provenance correction:** 430 of 2,695 ranked cells use NDVI vegetation, not canopy.
  `green_src=ndvi|canopy` is exported by `05_score.py` and added to existing GeoJSON without
  changing any prior data value, rank or geometry. Proxy cells are labeled and their planting
  scenarios are unavailable (dashes rather than zero estimates). Canopy-backed combines aerial
  and CHM sources; this flag does not certify full coverage or aerial-only provenance.
- Landing pitch is now action-focused. Earlier canopy-equity headline is held for revalidation.

See `PRODUCT_READINESS.md` for source-by-source upgrade proposals and release acceptance
criteria. Current implementation is a planning tool under validation, not a certification of
enterprise/government readiness. Other city branches are unchanged.


## Current Contra Costa UI contract — September 7, 2026

This section and the revised rows below describe the current working-tree UI. Other city
branches have not received this UI pass. The user-facing reference is `app/guide.html`:
17 searchable, category-filtered topics with native disclosures, source links, formulas,
limitations and direct anchors. Metric info links open that guide in a reusable separate
tab, preserving the map. `app/guide.css` and `app/guide.js` are bundled static assets.

- Persistent **How to use** reopens the coach; **Data & methods** is always in the header.
- Default workspace copy is shortened; **Why this score?** is collapsed on selection.
- **Planting scenario** replaces “Intervention ROI”: choose 0–100% of theoretical mapped
  street capacity (25% initial). Capacity = floor(street_m × 2 / 10); trees = round(capacity
  × share / 100), capped at floor(remaining canopy area / 40). Gain = trees × 40 / area × 100
  percentage points. Cost = trees × $500; illustrative air cooling = gain / 10 × 0.3 °C.
- The calculator does not establish financial ROI, confirmed beneficiaries, public ownership
  or site feasibility. It preserves per-cell choices through unit/weight changes within the
  current page session. No street data disables the slider and explains unknown capacity.
- Redlining control and historical heading hide when no cells have grades. Cooling access
  stays available separately. Category filters affect markers only, not precomputed walks.
- Ranked rows are native keyboard buttons; selection focuses Close, which restores focus
  on dismissal. Hidden intro/detail content is inert. The mobile drawer makes covered map
  and panel content inert. Focus styles and narrow-screen layouts are included.
- Count labels distinguish 2,695 ranked residential cells from 2,859 total cells.
- A/C is **Census modeled prevalence**, not direct measurement. Legacy CSV `measured`
  labels mean LACE-backed; all residential cells here have that source.

Validation: `node tests/ui-contract.cjs` checks JS syntax, guide anchors, cell/HOLC counts
and 11,436 scenario cases. Browser checks cover desktop, 390px mobile, help reopening,
keyboard selection, unit preservation, guide deep links/search, and the flat basemap.
No pipeline inputs or ranking weights changed. Public deployment is a separate step;
`deploy.sh` archives committed branches, so uncommitted UI files are not published by it.


A complete reference for what the map does, where each number comes from, and what
it can and cannot be trusted to say. Written for a city team. Read this next to
`DATA_QUALITY.md` (the prioritised caveat audit) — this file is the inventory,
that one is the fix list.

**Cities live:** Los Angeles `/app/`, San Ramon `/sanramon/app/`, Contra Costa
County `/contracosta/app/`, Bakersfield `/bakersfield/app/`, chooser at the root.
Where a row says "SR/CC/Bak" it means all cities *except* LA, which runs an older
pipeline (see the LA notes at the end).

---

## 1. Map layers (the "Map layer" buttons)

| Layer | What it shows | Source | Key limitations |
|---|---|---|---|
| **Priority** (composite) | Where to cool first: a 0–100 score per residential hex | Computed: `base = w_heat·heat + w_green·(1−canopy) + w_ac·(1−ac) + w_age·age65`, then `× (0.55 + 0.45·pop)`, min-max→0–100 | **Relative within one city, not an absolute hazard** and not comparable between cities. Weights are chosen, not calibrated to a health outcome (none exists at this geography). Recomputed live from the sliders. |
| **Surface heat** | Summer daytime land-surface temperature | **Landsat 8/9** thermal (ST_B10), median of summers 2022–24, via Microsoft Planetary Computer | **Surface ≠ air temperature.** Landsat crosses ~10:30–11:30 local — **mid-morning, not the afternoon peak.** **Weighted 0 in CC & SR** (absolute temp there mostly tracks distance from the Bay, not need). |
| **Tree canopy** | % of ground under tree canopy | **USFS/CAL FIRE 2022** aerial canopy (0.6 m NAIP) for SR/CC/Bak; rural fringe outside the urban-area boundary falls back to the Meta/WRI CHM. **LA: still Sentinel-2 NDVI proxy.** | Canopy **extent, not a tree count/inventory** (CS-1b's inventory still needs LiDAR/ground). 2022 vintage. Fringe hexes mix two sources. LA overstates (NDVI counts lawn). |
| **Lawn / non-tree vegetation** (`veg`) | Photosynthesising ground that is *not* tree canopy | **Sentinel-2** NDVI, summer medians 2022–24 | An NDVI proxy — counts irrigated lawn, crops, shrub. Useful as "green but unshaded = cheap place to plant," not as canopy. |
| **Population exposed** | Residents per hex | **US Census ACS 2023 5-year**, block groups apportioned into hexes | Interpolated, not counted. Dasymetric (by building floor area) where OSM coverage is good (SR); **area-weighted in CC** (OSM maps its rich block groups 4.7× better, so building-weighting would demote poor areas). Block groups are ~3.6–9× a hex. |
| **Age 65+** | Share of residents 65+ | ACS 2023, empirical-Bayes shrunk toward the citywide rate | Smoothed (a 4-person hex can't read 100% elderly) and interpolated; not block-precise. |
| **A/C access** | % of occupied homes with air conditioning | **US Census LACE 2023** (Local A/C Estimates), tract level — *modeled Census estimates*, replacing the old local income-rank proxy | Tract-level (coarser than a hex). **Counts any A/C including evaporative ("swamp") coolers**, which protect far less in extreme heat — flagged on the Bakersfield layer. Income-model fallback only where a tract is suppressed (`ac_src` records which). |
| **Walk to cooling relief** | Est. walking minutes to the nearest cooling site | CC: OSM pedestrian-network distance plus endpoint snap distances, at 4.8 km/h; sites from **OpenStreetMap** | CC current overlay marks every cell routed; centroid/snap links and OSM completeness remain limitations. LA retains straight-line estimates. OSM cooling sites aren't verified as *designated, open, air-conditioned* cooling centres. Labelled "est." |
| **Redlining (HOLC)** | 1930s HOLC grades A–D | **Univ. of Richmond, Mapping Inequality** | Control hides where no hex is graded. CC also hides the historical heading; no coverage does not establish an absence of historic discrimination. Historical context, not current condition. |

## 2. The three land classes (every hex is now shown — `place` property)

| Class | Meaning | How decided | Shown as |
|---|---|---|---|
| **res** | Has residents | ACS population ≥ 1 | Scored & ranked (colour ramp) |
| **activity** | Developed, ~no residents (commercial/industrial/institutional) | ≥120 m street frontage **OR** ≥3 buildings **OR** (≥40 m road AND ≥1 building), from OSM streets + 02b footprints | Real canopy/heat on those layers; **grey on Priority; not ranked** |
| **empty** | Undeveloped | none of the above | **Muted fill + border**, with a best-effort `land` label |

**`land` labels for empty hexes** (open water / woodland / open land / bare hillside) are inferred from the satellite layers (cool+unvegetated → water, high canopy → woodland, etc.). **Validated against ESA WorldCover 10 m: 92% agreement on Contra Costa**, remaining 12/156 are minor (bare-vs-open-land). Labelled "likely" in the UI. *Upgrade path: pull ESA WorldCover / NLCD directly for authoritative labels — mechanism proven, see the handoff.*

## 3. Interactive functions

| Function | What it does | Source / basis | Limitations |
|---|---|---|---|
| **Weight sliders + presets** | Re-score & re-rank live as you change what counts | Same formula as the pipeline, recomputed in-browser; parity with the pipeline < 0.1 pts | Live score stored at 1–2 dp; residents-only (activity/empty excluded from ranking). |
| **Planting scenario** (Contra Costa detail panel) | Trees, indicative cost, canopy gain and illustrative cooling for a share of mapped street capacity | WRI *Cooling Potential of Urban Trees* (+10% canopy ≈ −0.3 °C ambient air temp); **$500/tree** and **40 m²/crown** are *planning assumptions*; street-frontage capacity at 10 m spacing both sides | Cost is order-of-magnitude, not a bid. Cooling coefficient is a generalised literature value applied uniformly (air-temp, vs surface-temp heat layer). Capacity ignores driveways/utilities. |
| **City switcher / "All cities"** | Move between the four deployed cities / the chooser | Static links under the Pages root | Replaced the old fake 20-city search. Only the four built cities are real. |
| **Metric / imperial toggle** | °C·km ↔ °F·mi | Display only | Temperature *deltas* convert as differences, not absolutes. |
| **Detail panel** | Per-hex score breakdown + all metrics + ROI | The hex's own properties | Activity/empty hexes show canopy/heat + a "not ranked" note instead of a score. |
| **Hover tooltip** | Name, priority, heat, canopy, walk time | Live values | Trusts the live score over the frozen property. |
| **Home / flat basemap (`?flat=1`)** | Reset to the city intro / render with zero off-host requests | Local vendored MapLibre + fonts; CARTO positron basemap otherwise | Flat path draws the boundary + hexes only (venue-Wi-Fi fallback). |
| **Cooling-site categories** | Filter libraries / community centres / pools / senior sites | `kind` in `centers_<city>.geojson` (OSM) | See walk-time caveats. |

## 4. Backend / pipeline (per city, `pipeline/`)

| Step | Produces | Source | Notes |
|---|---|---|---|
| `01_make_grid` | H3 grid | H3 (res 8 for LA/CC ≈ 0.77 km²; res 9 for SR/Bak ≈ 0.11 km²) | Hex ≠ census block. Areas geodesic (correct). |
| `02_satellite` | LST, NDVI rasters/CSV | Landsat 8/9 + Sentinel-2, Planetary Computer | Per-summer search (never a continuous range). Sentinel BOA offset applied. Per-tile scene budget (a county-scale bug fixed). |
| `02b_buildings` | Residential footprints | OpenStreetMap | Coverage varies; drives the dasymetric guard. |
| `02d_canopy_usfs` | Measured canopy | USFS/CAL FIRE 2022 (EPSG:3310 equal-area, per-hex windowed reads, urban-boundary denominator) | Fixes the old web-Mercator area bug + nodata handling. CHM fallback for fringe. |
| `03_census` | pop, age, income, A/C | ACS 2023 + **LACE 2023** join | Dasymetric-safety guard (refuses building-weighting when OSM is incomplete/biased). |
| `04_overlays` | cooling sites, walk time, street_m, names, HOLC | OpenStreetMap + Mapping Inequality | Overpass rate-limited; walk time is circuity-adjusted straight line. |
| `05_score` | the app's geojson | fuses all of the above | One-sided p2/p98 clip so outliers don't set the scale; three-class `place`; `norm` written for exact app parity. |
| `deploy.sh` | assembles `gh-pages` from all four branches | — | **Pushing a source branch does NOT update the site — run `./deploy.sh`.** Now: always `node --check` each app first. |

## 5. Los Angeles — what's different (deliberately not modernised this round)

LA runs the original, older pipeline: **canopy is still the Sentinel-2 NDVI proxy** (overstates cover), CSV filenames are unslugged, and `05_score` predates the measured-canopy contract, so LA is **not** on the three-class land model (it still drops unpopulated hexes). LA *did* get Census LACE A/C estimates. The recipe to bring LA up to parity (USFS canopy + three-class) is in `DATA_QUALITY.md` follow-up 1.

## 6. Known-broken-then-fixed (for the record)

Two of this session's own edits shipped syntax errors that made the **SR and LA apps blank/dead live** (an unescaped apostrophe; a missing brace) before they were caught and fixed. `node --check` on every app is now part of deploy. If an app ever renders blank, syntax-check its inline `<script>` first.

### Validation — September 8, 2026

Contra Costa branch only: seven Python tests and 11,436 scenario checks passed, including partial-baseline behavior and capacity bounds. Browser checks confirmed the conditional scenario and searchable 17-location county directory; the final directory layout was visually inspected. Changes remain local and unpublished.


### Re-audit fixes — September 21, 2026 (evening)

From `../coolequity/reports/REVIEW_READINESS_REAUDIT_2026-09-21.md`; every finding re-verified before editing.

- **Release.** `site/goatcounter.txt` is `coolequity` again (a literal `YOUR-CODE` had been committed and failed the build). The build stamps `<meta name="ce-release">` with `CE_RELEASE` (CI passes the commit) and the smoke job now fails unless the live chooser carries that commit, so an older release answering 200 no longer passes.
- **Rank sensitivity.** `05b_stability.py` started from the published, already-smoothed age share and smoothed it again. It now reads the raw census share, re-draws it, and smooths once, exactly as 05 does; it aborts if the once-smoothed raw share does not reproduce the published `pct65`. All five builds re-run (bands, top-tier shares, `reports/stability_*.json`, guide numbers); `dataVersion` is `20260921-stability` everywhere. Point ranks unchanged.
- **Save protection.** `isDirty()` compares a signature (weights, population weight, planting shares the user moved or a file supplied, cost, survival) against the state last saved to or loaded from a file, or the defaults. Cost-only and survival-only edits now warn; a saved or freshly loaded scenario does not; opening an area does not. Reset returns to a clean state. Contract test covers each case.
- **Accessibility.** Light theme: `.explain .why` uses `--why` (#8a4b00, 6.4:1 on the card; was 1.6:1) and field-status pills get dark ink. Both modals keep Tab and Shift+Tab inside, Escape closes, and focus returns to the control that opened them (Reset map or Home).
- **Export docs.** `scripts/sync_column_key.py` regenerates every guide's Column key from `FIELD_KEY`; `scripts/test.sh` fails if a guide is stale. `tree_cover_source_type` now says canopy covers aerial, calibrated height-model and lidar paths.
- **Compare table** labels the band "Likely rank (rec. mix)" like the briefing table.
- **Briefing** lede names the inputs that actually carry weight (and those at zero); the toolbar no longer promises a fixed page count.
- **Analytics** tag is added by a guard that skips `?flat=1`, so the offline rehearsal makes no off-host request; the chooser's privacy sentence now says what GoatCounter records and links its policy.

Left for later: the layout rearrangement and renames in finding 8 and the wording table (they touch presets, tests and every guide), a physical-phone pass, and a printed-PDF pass with 0/1/6 shortlisted areas.
