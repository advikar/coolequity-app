> Carried over from the `contra-costa` branch of [advikar/coolequity](https://github.com/advikar/coolequity/tree/contra-costa) on September 12, 2026. File paths in it refer to that branch (e.g. `data/` is now `cities/contracosta/data/`, `app/guide.html` is now `cities/contracosta/guide.html`).

# CoolEquity — data-quality audit

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


## Current implementation — validated rebuild, September 7, 2026

This supersedes the source-audit and UI-only notes below. Those describe the pre-rebuild data.
Changed branch: **contra-costa only**. Local build; not publicly deployed.

- Re-ran all four locally available USFS/CAL FIRE rasters. **Canopy percentages are unchanged**.
  Frozen, H3-aligned fallback mask repairs all related columns; positive canopy with zero
  canopy area falls from **866 to 0**. Legacy CHM corridor areas remain unvalidated and must
  not be interpreted as verified public planting space.
- Sources across 2,859 cells: **1,334 USFS 2022**, **1,079 legacy CHM**, **446 no canopy**.
  Aerial extent: **789 cells >=99% assessed**, **545 partial**. CHM extent stays unknown;
  no coverage is invented from its percentage. Exact boundary matching, common equal-area
  CRS/pixel-area checks and overlap removal protect aggregation.
- Export adds source/year, assessed_m2, coverage_frac, canopy_quality and scenario_ok.
  Planting scenarios require USFS coverage >=99%: **788 residential cells enabled**.
  The 99% cutoff is an operational denominator tolerance (up to 1% unassessed), not source
  accuracy or site-feasibility certification. Partial and legacy cells remain browsable.
- Refreshed to **2020–2024 ACS five-year** and matching 2024 boundaries, 708 block groups.
  Cache includes vintage, occupied homes B25003_001E and published 90% margins of error.
  Missing required counts/vintage or unmatched block groups fail instead of silently becoming
  zero population. Per-cell uncertainty propagation and improved spatial allocation remain pending.
- LACE 2023 now weights **allocated occupied homes**, with explicit A/C numerator, housing
  denominator and coverage. Partial/suppressed coverage cannot masquerade as 0% A/C.
  All **2,697 residential cells** remain LACE-backed; nonresidential fallback records retain
  income-model flags. In a controlled 2023 run, population and age match exactly while A/C
  changes by up to **5.4 points**. No income-equity headline has been reinstated.
- Export and browser now rank the same published inputs with the same tie ordering. Previous
  dense ranks and pre-rounding inputs could disagree with the live list. Default top 25 overlap
  after rebuild: **24/25**; median absolute rank move **8**, maximum **393**.
- Greenness is publicly explorable as a **0–100 index**, not vegetation percent. The legacy
  0–45 `veg` scaling is mapped to 0–100 for display. Canopy layer never paints NDVI as canopy;
  missing canopy is gray. Raw NDVI is not recoverable outside the clamped endpoints.
- Cooling remains a secondary illustration. Primary reference: Krayenhoff et al. (2021),
  https://doi.org/10.1088/1748-9326/abdcf1: informal synthesis of higher-quality modeling
  studies, approximately 0.3°C per 10 canopy points for clear-sky summer afternoons.
  This is not observed Contra Costa cooling or a surface-temperature response model.

Validation: five pipeline regression tests; 11,436 scenario cases; all residential browser/export
rank and score agreement; stable IDs/geometries; source/area consistency. Nine weight stress
cases retain 19–24 of the default top 25; this is a diagnostic, not a confidence interval.
See `reports/rebuild_summary.json`, `reports/rebuild_cell_changes.csv`, `reports/source_manifest.json`.


## Latest source audit — critical corrections, September 7, 2026

**This section supersedes the earlier “Current UI accuracy corrections” where inconsistent.**
The earlier review missed the NDVI fallback and was too reassuring about canopy coverage.

- Joined grid IDs to current canopy/satellite CSVs and GeoJSON: **446 cells lack canopy_pct,
  including 430 residential cells**. All fallback `green` values match satellite `green_pct`;
  none is in the default top 25. Remaining residential cells: **2,265 canopy-backed**.
- Added `green_src` metadata to pipeline export and current file. Source-aware UI labels and
  disabled planting scenarios prevent those proxy values being presented as canopy baselines.
  Existing numerical fields, score/rank and geometry are unchanged (regression-checked).
- **866 positive-canopy records have zero canopy_m2 (860 residential).** Fallback loop in
  `02d_canopy_usfs.py` fills the percent before using percent-missingness for its other fields.
  Proposed repair: freeze missing mask; apply it to all matching columns; validate area and
  assessed coverage before rebuilding. No canopy raster reprocessing was performed this pass.
- Partial urban-boundary canopy denominators differ from whole-cell scenario areas. Export
  assessed area/coverage and constrain scenarios before treating these as locally validated.
- A/C input is modeled **occupied-housing-unit** prevalence, but the join uses people as
  weights. Propose occupied-unit weighting with reconciliation and source/uncertainty flags.
- ACS 2020–2024 five-year is available (January 29, 2026); current build remains 2023.
  Proposed update includes rank/coverage/MOE comparison. Fine 2020 census blocks are not
  automatically “exact” allocation truth: they are older and privacy-protected.
- Canopy-equity headlines derived from mixed canopy/NDVI need recomputation; the app landing
  no longer publishes the old ratio or below-15% count as pure canopy findings.
- $500/tree, 40m² crown, 10m spacing, chosen score weights and 100-person age smoothing remain
  project assumptions, not local calibration or externally endorsed constants.

Full evidence, source links, method alternatives and acceptance criteria: `PRODUCT_READINESS.md`.
UI notes stay short; substantive improvement proposals are kept in that owner-facing audit.


## Current UI accuracy corrections — September 7, 2026

**Read this before the historical issue tables below.** Those tables record earlier builds;
references to income-only A/C, unrouted county access and the previous canopy model are
historical unless explicitly retained here. This pass changes presentation and scenario
controls, not input data or score weights.

1. **LACE is modeled, not directly measured.** Verified against the Census LACE product
   page and `03_census.py`. The old CSV value `ac_src=measured` means LACE-backed. Joining
   residential GeoJSON IDs through the grid to census CSV confirms all 2,695 residential
   cells are LACE-backed; 140 of all 2,859 census rows use the income fallback. Corrected
   visible app labels and guide. Cell-level source flags still are not exported in GeoJSON.
2. **Right-of-way capacity is not verified feasibility.** OSM road length does not establish
   ownership or available tree positions. Replaced categorical “fits” and “needs private
   land” claims with theoretical-capacity language; absence means unknown opportunity.
3. **No confirmed beneficiary count or financial ROI.** Removed “residents cooled” and
   cost-per-beneficiary framing. Population is contextual. $500/tree and 40 m²/crown are
   explicit uncalibrated assumptions; overlapping crowns, survival and time are not modeled.
4. **Cooling is illustrative ambient-air cooling.** WRI summarizes ~0.3 °C per 10 percentage
   points of added canopy. No verified local afternoon prediction is available. Removed
   the previous implication of a locally measured effect and an afternoon guarantee.
   Source: https://www.wri.org/insights/urban-trees-cooling-potential
5. **Sites are potential relief, not verified centers.** Hours, access, fees and A/C remain
   unverified. All 2,859 current overlay rows say routed; endpoints use straight snap links
   and are not verified barrier-free door-to-door routes. Category filters do not reroute.
6. **Geographic denominator corrected:** 2,695 residential ranked cells; 8 activity and
   156 undeveloped cells; 2,859 total. Score breakdown now uses the residential denominator.
7. **Heat vintage corrected in layer caption:** summers 2022–2024, not summer 2023 alone.
8. **Verified current figures:** 1,161,570 residents; 577,342 in cells below 15% canopy.
   The guide attributes the 12.9% vs 27.0% income-quarter finding to the existing findings
   analysis and discloses ecological/median aggregation and geography limitations.

Remaining priorities for deployment as an operational planning product: complete per-cell
source/coverage metadata; ACS uncertainty; verified site inventory; municipal tree/ownership
and utility data; local costs; validated crown/maturity assumptions. No approximation here
is represented as “the most accurate” without comparative validation.

UI validation: `node tests/ui-contract.cjs` — 11,436 zero/quarter/half/full-share cases across
all cells, no nonfinite outputs, monotonic tree counts, capacity/canopy bounds and zero cost.
Desktop and narrow-screen browser checks are a targeted UI audit, not WCAG certification.


*Every approximation, caveat, and known error in the pipeline, with a concrete fix for each.*
Written to be read by a GIS analyst or a city sustainability team, not just the build. If a
figure from this tool is going into a grant application or a planting plan, read the item that
governs it first.

**How to read the priority column.** **P1** materially changes *which blocks rank where* or
*what the headline number is* — fix before the tool is used to allocate money. **P2** affects
accuracy at the margin or is a disclosed limitation with a real upgrade path. **P3** is latent,
cosmetic, or already honestly labelled.

The single most valuable change on this list is **C-1 (replace the canopy source)**. The
second is **AC-1 (replace the modelled A/C layer with measured data)**. Both are described in
full at the bottom, with sources.

---

## ✅ Status — September 2026: the two headline fixes shipped

Both P1 items are **done and deployed** (verified live at advikar.github.io/coolequity):

- **C-1/C-2/C-3 — canopy → USFS/CAL FIRE 2022 aerial (0.6 m NAIP), live for Bakersfield, San
  Ramon and Contra Costa.** New `pipeline/02d_canopy_usfs.py` reads the aerial rasters in
  **EPSG:3310 (equal-area)** with per-hex windowed reads and the urban-boundary polygon as the
  denominator — which also fixes **C-4 (Mercator area)** and **C-5 (nodata)** for free. Rural
  fringe outside the census urban areas falls back to the older CHM (still measured). This
  corrected San Ramon from a false ~11% (CHM read ~35% low) to a true **17.7%**, and sharpened
  Contra Costa's equity gradient. **LA is the one city still on NDVI — see follow-up 1.**
- **AC-1/AC-2 — A/C → measured US Census LACE (2023), live for all four cities.**
  `03_census.py` joins tract-level LACE prevalence population-weighted (income model kept only
  as a per-tract fallback; new `ac_src` column records which). In Contra Costa and LA, where
  A/C is scored, this **breaks the income-circularity trap** the earlier build carried.
- Quick fixes **C-4/C-5** landed with the canopy module. **D-2, W-3** remain open (low priority).
- **Map completeness (G-1/G-4) — done.** No hex in the study area is dropped any more. Three
  classes by a new `place` property: residential (scored/ranked), developed-but-unpopulated
  (commercial/industrial — shown with real canopy/heat, greyed on Priority, not ranked, caught
  by a buildings-aware classifier), and empty/undeveloped (shown muted + bordered, with a
  land cover label from **ESA WorldCover 2021** — see below).
  The study-area outline is now always drawn. Live on SR/CC/Bakersfield; LA still on the old
  binary drop (with its NDVI canopy) per instruction — folds in with follow-up 1.
- **Empty-hex land labels → ESA WorldCover 2021 (10 m) — done, live on SR/CC/Bakersfield.**
  The old `land` label was a lst/veg/canopy heuristic (water/woodland/open/bare); it was right
  on water but had no way to tell cropland from grassland from tidal wetland, and mislabelled
  both as "bare / hillside." New `pipeline/02e_worldcover.py` reads the authoritative, citable
  ESA WorldCover 2021 v200 map (Sentinel, CC-BY 4.0, Planetary Computer) as the majority class
  per hex; `05_score.py` applies it to empty hexes (heuristic kept only as a fallback).
  **Touches the descriptive label only — no scoring input, no ranking, no headline number
  (verified: max |score change| = 0, max |rank change| = 0 on all three).** Corrections: CC's
  12 "bare / hillside" hexes are Delta cropland/grass/wetland; SR's 76 are golden grassland, not
  bare; BK's undifferentiated bare/hillside separates into cropland, grassland, genuinely bare
  ground and woodland. The heuristic `classify_land()` stays as the offline fallback.
- **UHI (follow-up 2): decided AGAINST** — its 2006/2013 vintage would confuse the current heat
  reading. See the follow-up section.

- **Routed walk time (W-1) → done, live on SR/CC/Bakersfield.** The straight-line
  estimate is replaced by real routing on the OSM pedestrian network via new
  `pipeline/04b_routed_access.py` (osmnx graph + one multi-source Dijkstra from the
  cooling sites; door-to-door with endpoint snap distances, floored at crow-fly).
  Validated before shipping (the condition follow-up 3 set): each graph is a single
  connected component, all hexes reachable, routed/crow-fly ratio ≥ ~1.0 everywhere.
  `access` is unweighted in the score, so rankings are unchanged; only the displayed
  walk time and the access preset improve. LA stays on the straight line (its
  basin-scale graph is infeasible here — see follow-up 3). Details in STATUS.md.

**Staged, with recipes at the very bottom of this file:** follow-up 1 (LA canopy), follow-up 2
(CalEPA UHI air-temp layer — data downloaded, integration pending). Follow-up 3 (routed walk
time) is now DONE for SR/CC/Bakersfield (see above); it remained staged only for LA, whose
~3,400 km² bbox is a millions-of-nodes walk graph this environment can't build on a demo's
critical path.

---

## A. Canopy — the headline metric

| # | Issue | Impact | In-app now | Fix |
|---|---|---|---|---|
| **C-1** | **Vintage.** Canopy comes from the Meta/WRI Canopy Height Map, built from **2009–2020** Maxar imagery — up to 16 years old, and older than the 2022–24 heat and 2023 census it is scored against. | **P1.** Trees planted or lost since ~2015 are invisible. Worst in fast-changing areas: Dougherty Valley (San Ramon) and new Bakersfield subdivisions were built or matured after the imagery. A block can read "bare" because the canopy postdates the data. | Disclosed as "Meta/WRI canopy height," vintage not stated on the map. | **Replace with USFS/CAL FIRE 2022 California Urban Tree Canopy** (0.6 m, NAIP-derived, CC0). See §C-1 below. Biggest accuracy gain available. |
| **C-2** | **Systematic low bias.** The height model reads ~38 % below professional aerial assessment (9.1 % vs Fresno's published 14.6 % over the same boundary). | **P1** for absolute claims, **P2** for ranking. The tool ranks blocks correctly but its canopy % cannot be quoted as the real coverage. | Disclosed: "ranks blocks; does not certify absolute canopy." | The USFS 2022 product **is** the aerial-grade classification, so the bias largely disappears and canopy % becomes citable in absolute terms. Removes this caveat. |
| **C-3** | **Height threshold, not crown detection.** Anything ≥ 2 m of vegetation counts as canopy; a smooth modelled height surface merges touching crowns, so no honest per-tree count is possible. | **P2.** Tall hedges and shrubs count as canopy; deliberately no tree count (correct call). | Disclosed at length; no tree count shipped. | The USFS product is a canopy / no-canopy classification from imagery, not a 2 m height cut, so it is closer to what "canopy" should mean. Keep the no-tree-count discipline. |
| **C-4** | **Web-Mercator area distortion.** `02c_canopy.py` works in EPSG:3857; at 37–38° N a Mercator "metre" is ~1.25× a real metre, so Mercator **area** is inflated ~1.56×. This inflates the exported `row_m2` (plantable public right-of-way). | **P2 latent.** `canopy_pct` is a pixel *ratio* so it cancels — **unaffected**. `canopy_m2` uses the geodesic hex area — **unaffected**. Only `row_m2` is wrong, and the app's ROI panel uses real-metre `street_m` instead, so **no user-facing number is affected today**. But the exported column is ~1.5× too high. | Not surfaced. | Do the canopy zonal stats in `RASTER_CRS` (UTM 10N) like the rest of the pipeline, or scale `row_m2` by cos²(lat). One-file fix. |
| **C-5** | **NoData counted as "no canopy."** Every pixel in a hex goes into the denominator; nodata (tile edges, water) is treated as un-canopied, biasing canopy low where nodata is present. | **P3.** Small for inland CA cities; larger for coastal/edge hexes. | Not surfaced. | Mask the CHM nodata value before the ratio. |
| **C-6** | **Read decimation** to 1.2 m (cities) / 2.4 m (counties) from 0.6 m native. | **P3.** Tested to move canopy ~1 pt, inside the product's own bias. | Not surfaced. | None needed; note it. Moot after C-1. |

## B. Heat — land surface temperature

| # | Issue | Impact | In-app now | Fix |
|---|---|---|---|---|
| **H-1** | **Surface ≠ air temperature.** Landsat measures land-surface (skin) temperature; people experience air temperature, which is less extreme and less variable. | **P2.** A 51 °C surface reading is not a 51 °C air reading. | Layer is labelled "surface temperature." | Keep the label explicit. Air-temp modelling is possible but heavy; not worth it for a ranking tool. |
| **H-2** | **Overpass timing.** Landsat 8/9 cross at ~10:30–11:30 local — **mid-morning, not the afternoon peak.** The ROI text cites WRI's *afternoon* cooling coefficient. | **P2.** The heat layer and the ROI cooling claim are anchored to different times of day. | ROI says "afternoon"; heat layer does not state the time. | Relabel the heat layer "mid-morning surface temperature," and/or add an afternoon/evening source — **ECOSTRESS** (ISS, variable overpass incl. afternoon & night) is the standard complement. |
| **H-3** | **Summer median** over 2022–24, scenes < 20 % cloud, emissivity from the C2-L2 ST product. | **P3.** Sound method; the summer-per-year search (not a continuous range) is deliberate and correct. | Provenance shown. | None. Keep the per-summer search — a continuous date range would pull winter scenes into a "summer" median. |
| **H-4** | **Heat weighted 0** in Contra Costa and San Ramon (absolute temperature across a marine-to-inland county mostly tracks distance from the Bay, not local need). | **P2 by design.** A user may expect the hottest blocks to rank highest; they don't, because heat is unscored there. | Disclosed in the legend and the ROI "why cooling is claimed when heat isn't scored" note. | Defensible and documented. Leave as a user-adjustable weight. |

## C. A/C access

| # | Issue | Impact | In-app now | Fix |
|---|---|---|---|---|
| **AC-1** | **Modelled, not measured.** `ac_est = 35 % + 60 % × income-rank-percentile`. It is a relabelled income rank, nothing more. | **P1** where scored: **weighted 0.25 in Contra Costa** (moves the ranking), 0 in San Ramon. | Labelled "modelled / est." throughout. | **Replace with measured tract-level A/C prevalence.** See §AC-1 below. |
| **AC-2** | **Circularity.** Because `ac_est` *is* income and A/C is 25 % of the Contra Costa score, the ranking partly tracks income by construction. | **P1.** "Priority tracks income" must never be presented as an independent finding for CC. | Noted in `FINDINGS_CONTRACOSTA.md`; the landing-page income finding is computed on raw canopy, which is clean. | Real A/C data (AC-1) breaks the circularity and lets the income relationship be tested honestly. |

## D. Population, age, income (ACS)

| # | Issue | Impact | In-app now | Fix |
|---|---|---|---|---|
| **D-1** | **Apportionment.** ACS block groups (~3.6× a hex) are split into hexes by residential floor area (dasymetric where OSM buildings are complete) or by ground area (fallback). Demographics vary *smoothly*, not per block. | **P2.** Per-hex population/age/income are interpolations, not counts. The dasymetric guard (ACS reconciliation to 0.2 %) keeps totals honest, but a single hex's pop is an estimate. | Disclosed on the landing screen. | Use **2020 Census blocks** (decennial, exact counts, ~10× finer than block groups) as the dasymetric population target instead of area/floor. Removes most interpolation error for population. |
| **D-2** | **Averaging medians.** Hex income is a floor-/area-weighted **mean of block-group median incomes** — statistically improper (a weighted mean of medians is not a median). | **P3.** Small bias; income only feeds the A/C proxy, which AC-1 replaces anyway. | Not surfaced. | Assign each hex the median of the block group it mostly overlaps, rather than averaging across overlaps. |
| **D-3** | **ACS margins of error** are not propagated. Block-group income and age MOEs are large; suppressed values are handled but uncertainty is dropped. | **P3.** A ±estimate presented as a point value. | Not surfaced. | Carry the MOE columns; optionally grey out hexes whose driving estimate has a CV above a threshold. |
| **D-4** | **Age-65 empirical-Bayes shrinkage** (100-person pseudo-count) pulls small-hex rates toward the city mean. | **P3, by design.** Prevents a 4-person hex reading 100 % elderly; costs some real signal in small hexes. | Disclosed. | Sound. Leave as is. |

## E. Cooling access / walk time

| # | Issue | Impact | In-app now | Fix |
|---|---|---|---|---|
| **W-1** | ~~**Not routed.**~~ **FIXED (SR/CC/Bakersfield).** Was a straight line × 1.273 circuity ÷ 4.8 km/h, ignoring freeways, rivers, rail and walls. | **P2 → resolved** where routed; LA (master) still straight-line. | **Routed on the OSM pedestrian network** (osmnx + multi-source Dijkstra, `04b_routed_access.py`), door-to-door, barrier-aware. LA unchanged. | Done via osmnx rather than a standalone OSRM/Valhalla server (neither is available here); validated single-component + ratio ≥ crow-fly before shipping. |
| **W-2** | **Cooling sites from OSM tags.** Completeness varies, and an OSM "community centre" or "library" is **not** necessarily a designated, open, air-conditioned cooling centre during a heat event. | **P2.** The denominator of "relief nearby" may be wrong in both directions. | Sites are classified and counted from the file; designation is not claimed. | Use the **county/city official cooling-centre list** (and its hours) as the authoritative layer; keep OSM as a fallback. |
| **W-3** | **`access_min` filled with the median** for hexes with no reachable site — masks true isolation as "average." | **P3.** Under-flags genuinely stranded blocks. | Not surfaced. | Represent "no site within N minutes" explicitly rather than imputing the median. |

## F. Scoring / normalisation

| # | Issue | Impact | In-app now | Fix |
|---|---|---|---|---|
| **S-1** | **Relative, within-city.** Score is a 0–100 rank inside one city (now via one-sided p2/p98 clip). Not an absolute hazard level; **not comparable between cities.** | **P2 by design.** "#1 in Bakersfield" ≠ "#1 in San Ramon" on any absolute scale. | Disclosed in the legend. | Correct for the stated purpose. If cross-city comparison is ever needed, add an absolute index alongside the rank. |
| **S-2** | **Percentile choice.** The p2/p98 clip is a judgment call; endpoints are written into the geojson `norm` so the app reproduces the pipeline exactly, but 2/98 itself is not sacred. | **P2.** Reasonable and documented; a different percentile would reshuffle the mid-list slightly. | The clip is applied; endpoints shipped. | Sound. Revisit only with a calibration target (S-3). |
| **S-3** | **Weights are chosen, not calibrated.** 0.55 / 0.25 / 0.20 etc. are not fit to any heat-health outcome, because none exists at this geography (California publishes heat-ED rates only at **county** level). | **P2.** The weighting is defensible, not empirical. | Disclosed; the user can move every weight live. | If ZIP/tract heat-morbidity is ever obtained (HCAI Limited Data Request), calibrate weights against it. Until then, live sliders are the honest answer. |

## G. Geometry / mapping

| # | Issue | Impact | In-app now | Fix |
|---|---|---|---|---|
| **G-1** | **"Blocks" are H3 hexes, not census blocks.** CS-1b literally asks about "census blocks." Resolutions also differ by city (res 8 ≈ 0.77 km² for LA/CC; res 9 ≈ 0.11 km² for SR/Bakersfield), so hex "blocks" are not comparable across cities. | **P2.** A planner may expect census geography; the word "block" invites that. | Area/scale note in the footer. | Call them "cells / hexes," and/or offer a census-block-group or tract roll-up for anyone who needs to join to official geography. |
| **G-2** | **Hex names** come from OSM place/landuse polygons, else the nearest anchor with a compass suffix ("Valencia S"). A hex named for the nearest landmark may not *be* that development. | **P3.** Labels are approximate locators, not authoritative place names. | Compass suffixes signal approximation. | Fine; keep labelling them as locators. |
| **G-3** | **Basemap is CARTO positron** (external). `?flat=1` renders with no basemap and zero off-host requests. | **P3.** Disclosed; offline fallback exists and is tested. | Yes. | None. |
| **G-4** | **Boundary intersection overhang.** Hexes are kept if they *intersect* the city limit, so geometry overhangs into neighbours; population is clipped to the limit but the hex shape is not. | **P3.** Cosmetic edge effect; totals are correct. | Not surfaced. | Optionally clip display geometry to the boundary. |

## H. ROI / cost

| # | Issue | Impact | In-app now | Fix |
|---|---|---|---|---|
| **R-1** | **$500 / tree** planted incl. ~3 yr establishment — a planning assumption, not a bid. | **P3.** Order-of-magnitude only. | Explicitly labelled a planning assumption. | None; keep it labelled. |
| **R-2** | **WRI cooling coefficient** (+10 % canopy ≈ −0.3 °C afternoon air temp) applied uniformly to every block regardless of local climate/geometry, and it is an **air-temp** figure applied where heat is measured as **surface** temp. | **P2.** A generalised literature value, not a local measurement; and see H-2 on the time-of-day mismatch. | Sourced to WRI; the surface-vs-air distinction is spelled out in the ROI note. | Present as an order-of-magnitude planning figure (it is). If local calibration is ever available, use it. |
| **R-3** | **Frontage capacity** = both sides, 10 m spacing — ignores driveways, utilities, sight lines, existing trees. | **P3.** Explicitly an upper bound. | Disclosed. | None; labelled as an upper bound. |
| **R-4** | **40 m² / crown** to convert a canopy deficit into a tree count for the ROI. | **P3.** An assumption, but a capacity estimate (area ÷ crown), not a detection. | Sourced. | None. |

---

## §C-1 — Recent canopy data (the answer to "something this old raises flags")

**Yes, and it is free, recent, and better on every axis.**

**USFS Pacific Southwest / CAL FIRE — California Urban Tree Canopy (2022).**
- **0.6 m** resolution, derived from **2022 NAIP** aerial imagery with a deep-CNN classifier, produced with CAL FIRE, NOAA Office for Coastal Management and USFS State & Private Forestry.
- Covers **all US-Census urban areas in California** — includes Los Angeles, Bakersfield, and the Bay Area urban areas that contain San Ramon and central Contra Costa (Concord–Walnut Creek etc.).
- Ships **% canopy 2022, canopy acreage, % canopy 2018, and 2018→2022 change** — the change layer is exactly what CS-1b needs to show progress over time.
- **CC0 1.0 public domain.** Per-city and statewide GIS downloads via Box.
- Landing page: <https://www.fs.usda.gov/r05/state-private-tribal/california-urban-canopy-data>

Why it beats the current Meta/WRI CHM here: **2022 vs 2009–2020** imagery, a purpose-built **urban canopy classification** rather than a height proxy (kills the ~38 % low bias, C-2), and a **built-in change product**. Adopting it fixes C-1, C-2 and C-3 at once and lets us state absolute canopy percentages a city can defend.

Other options considered: **NLCD Tree Canopy Cover** (annual but 30 m and forest-oriented — reads ~2 % urban, unusable); **ETH Global Canopy Height 2020** (10 m, global, still a height proxy); **Meta 1 m global 2024** (same family as now — imagery still 2018–2020); commercial **EarthDefine CHM/TreeMap** (0.6 m, refreshed annually, but paid). For a California city the free USFS/CAL FIRE 2022 layer is the right default; a city with its own recent **LiDAR** (USGS 3DEP) can do better still for a definitive inventory.

Sources:
- USFS California Urban Canopy Data — <https://www.fs.usda.gov/r05/state-private-tribal/california-urban-canopy-data>
- "Sub-meter tree height mapping of California using aerial images and LiDAR-informed U-Net" — <https://www.sciencedirect.com/science/article/pii/S003442572400110X>
- EarthDefine CHM (commercial, annual) — <https://www.earthdefine.com/chm/>

## §AC-1 — Measured A/C access (the answer to "instead of estimating on income")

**Yes — real A/C data exists down to the census tract, and the definitive local source is the county assessor.**

Two practical replacements for the income proxy:

1. **County assessor "cooling type" parcel field — the authoritative local source.** Contra Costa, Los Angeles and Kern county assessors record heating/cooling system per parcel. A city deploying this tool *already owns* its assessor extract; joining the cooling field to parcels and aggregating to hexes gives measured A/C presence, not a model. Coverage is partial (not every record is populated), so pair it with #2 to fill gaps.

2. **Published tract-level A/C prevalence.** *A Comprehensive Dataset of Residential Air Conditioning Prevalence in the Continental United States* (Nature Scientific Data, 2025) classifies **central / other / evaporative / none** at **census-tract, ZIP and metro** resolution, built from ~103 M property records (Dewey/ZTRAX-type assessor data) with an XGBoost model. National coverage, so all four cities are included; join to hexes by tract.
   - <https://www.nature.com/articles/s41597-025-06104-3>

Caveats to keep even after switching: the tract dataset is itself **partly modelled** where assessor records are missing (in California only ~31 % of parcels had a recorded A/C type, so the rest is imputed), and evaporative coolers (common in Bakersfield) provide far less protection than refrigerated A/C — a "has cooling" flag should not be treated as "safe in a heat wave." But even a partly-modelled *measured* layer breaks the income circularity (AC-2) and is a real improvement over relabelling income.

Recommended approach: **assessor cooling field where available → tract prevalence to fill gaps → income only as a last-resort fallback, clearly labelled.** Also add an **evaporative-vs-refrigerated** distinction for the San Joaquin Valley cities.

Sources:
- Residential A/C prevalence dataset (Nature Sci Data 2025) — <https://www.nature.com/articles/s41597-025-06104-3>
- "Measuring A/C Access to Prepare Against Extreme Heat" (FAS) — <https://fas.org/publication/air-conditioning-data/>

---

## Recommended order of work

1. **C-1 / C-2 / C-3 — swap in USFS 2022 canopy.** Re-run `02c_canopy.py` against the new source for all four cities, re-score, re-derive `BRIEF.md`, redeploy. Changes every canopy number (for the better) and lets us drop the "ranks but doesn't certify" caveat.
2. **AC-1 / AC-2 — measured A/C.** Start with tract prevalence (fast, national); add assessor cooling fields per city where the city provides them.
3. **W-1 / W-2 — routed walk time on official cooling-centre locations.**
4. **D-1 — census-block dasymetric population.**
5. **C-4 / C-5 — canopy in UTM + nodata mask** (quick correctness fixes).

Items 1 and 2 change published figures, so they need a decision before they run — they are not silent refactors.

---

## Staged follow-ups — exact recipes

### Follow-up 1 — Los Angeles canopy → USFS 2022 aerial
LA is still on the Sentinel-2 NDVI proxy (which counts irrigated lawn as canopy and overstates
it). The other three cities are on USFS aerial; LA was deferred because `master`'s pipeline
predates the measured-canopy contract and swapping it safely is more than a data drop:

1. `curl -sL "https://usfs-public.box.com/shared/static/dbfv5dtrvm7zn7820ak2vssxczbwm43t.zip"`
   (Los Angeles--Long Beach--Anaheim, ~623 MB) → unzip into `data/_cache/canopy_src/`.
2. `master/pipeline/05_score.py` predates the canopy merge (it reads **unslugged** `census.csv`
   etc. and its CONTRACT lacks `canopy_m2/veg/row_m2`). Port the canopy-merge block from
   `san-ramon:pipeline/05_score.py` (the `if C.CANOPY_CSV.exists(): … green_pct = canopy_pct`
   stanza + the `canopy_m2/veg/row_m2/row_canopy` output rows), keeping master's file names.
   Add `CANOPY_CSV = DATA / "canopy_la.csv"` to `master/pipeline/config.py`.
3. `git checkout san-ramon -- pipeline/02d_canopy_usfs.py`; run `02d` then `05`.
4. Reframe the LA app copy: it frames `green` as NDVI "vegetation/greenery" throughout — the
   landing lede, the green-layer caption, the ROI. Rewrite to "measured canopy (USFS 2022)".
5. Verify live-score parity < 0.2 and redeploy.

### Follow-up 2 — CalEPA Urban Heat Island Index (air-temperature layer) — NOT RECOMMENDED
**Decision (Sep 2026): do not integrate.** The index models **2006 & 2013 only**. Placed next
to the 2022–24 Landsat surface temperature and 2022 aerial canopy this tool now uses, an
outdated layer would undercut the "current and accurate" credibility and confuse which heat
reading is authoritative — the opposite of what an official tool needs. Its one real advantage
(air-temp, confound-free urban increment) does not outweigh the vintage problem. Documented here
in case a refreshed version is ever published; the mechanics below still apply if so.

The data is already downloaded to `/tmp/uhi` (`Data_13-001/`, 496 per-city shapefiles). It is
census-tract **air** temperature (degree-hours/day, 2 m, urban-minus-upwind-rural), modelled
2006 & 2013 — the *urban heat increment*, which removes the distance-from-Bay confound.

1. Re-download if needed with a cookie jar (the CalEPA WordPress WAF redirect-loops otherwise):
   `curl -sL -c jar -b jar -A "Mozilla/5.0 …" -e "https://calepa.ca.gov/climate/urban-heat-island-index-for-california/" "https://calepa.ca.gov/wp-content/uploads/2020/06/Data_30-001_files_all.zip"`
2. Decode the per-city shapefile schema (the degree-hours field), union the tracts covering each
   study area, join to hexes area/pop-weighted → new `uhi` column written by `05_score.py`.
3. Add a display layer to each app (ramp + caption + toggle), labelled "air-temp UHI, CalEPA
   2006/2013". Optionally give it a non-zero weight in Contra Costa, where it is a defensible
   heat signal in a way absolute LST is not — but that re-opens the ranking, so make it a
   deliberate, verified change, not a default.

### Follow-up 3 — routed walk time (replace the circuity straight-line, W-1)
1. Run OSRM (foot profile) on a California OSM extract (Geofabrik NorCal + SoCal), or Valhalla.
2. For each hex centroid, request the walking duration to the nearest N cooling sites and take
   the minimum; write `access_min`/`access_km` in `04_overlays.py` from that instead of
   `dist × CIRCUITY ÷ speed`.
3. **Validate against a sample of hand-checked routes before shipping** — the whole reason this
   is staged is that an inaccurate route is worse than an honest estimate. Until it is
   validated, the app must keep labelling walk time "estimated, not routed."

### Validation — September 8, 2026

Current Contra Costa export supports 1,832 residential conditional scenarios; 788 residential cells qualify for displaying a canopy baseline and future total. Removing the two county-identified libraries without A/C and rebuilding access changed 21 cells’ walking estimates. Seven Python tests and 11,436 scenario checks passed. These checks verify implementation consistency, not field accuracy or planting feasibility. County source check date remains September 7, 2026.
