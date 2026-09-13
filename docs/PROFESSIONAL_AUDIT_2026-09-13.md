# CoolEquity professional-readiness audit

> **Status tracker (kept current as work lands).** The audit below was written by a second
> reviewer on September 13, 2026 against the live site and the *old* `advikar/coolequity`
> checkout. The tracker records what has since been fixed in this repository. Last update:
> September 13, 2026 (second pass).
>
> | Item | Status | Where |
> |---|---|---|
> | Scenario files do not restore custom costs | **Fixed** | `loadScenario` restores `planting_assumptions.cost_per_tree_usd` |
> | Shared links are not an exact scenario | **Fixed (copy narrowed)** | Export hint now says a link carries priorities, layer and selection only; file is the exact-view mechanism |
> | Greenness labelled/exported as trees | **Fixed** | List row reads "greenness"; export has `greenness_index_0_100`, `tree_cover_pct` empty for NDVI cells; "Trees < 10%" filter ignores NDVI cells |
> | "Plantable" label exceeds evidence | **Fixed** | Filter reads "Has street capacity"; CSV column is `mapped_street_m`, described as theoretical capacity |
> | Guide duplication (two Export sections) | **Fixed** | Contra Costa and San Ramon guides |
> | Reset is incomplete | **Fixed** | `resetMap` clears filters, sort, direction, cost per tree |
> | Ranked-row button nesting (a11y) | **Fixed** | Row is a plain container; the name is the open control (role=button, keyboard), the star is a sibling button |
> | CSV formula-prefix escaping | **Fixed** | Text cells starting with = + - @ tab are prefixed with an apostrophe |
> | Celsius default claim | **Not reproduced** | Default is imperial in code and on the live site |
> | Afternoon vs late-morning wording | **Fixed** (was live, now late morning) | App copy and all three guides |
> | Need is not marginal benefit (positioning) | Owner's call | Headline kept by decision; wording may be softened |
> | Mixed canopy sources / reliability flag at point of use | **Fixed for thin coverage; pooling remains** | Detail panel tags tree cover with source, year and assessed share. Cells whose aerial assessment covered under 10% (`CANOPY_MIN_COVERAGE`) now score on the satellite stand-in: 121 Contra Costa, 63 Bakersfield, 20 San Ramon cells; top-25 unchanged in every city. Legacy height-model cells and full/partial aerial cells are still pooled in one input |
> | Uncertainty / rank stability bands | Open | Larger modelling work |
> | Cooling discovery vs verified relief | **Fixed** | County-designated cooling locations are a separate amber layer with their own toggle and popup (address, phone, "call before visiting"), geocoded by `04c_designated_cooling.py`; the OpenStreetMap dots are labelled as discovery sites. One Kern site (Frazier Park) could not be geocoded and is listed as unlocated in the file |
> | Planting outputs: low/base/high cost, survival | Open | |
> | Chooser + intro friction, three-column squeeze, mobile legend | **Partly fixed** | Legend starts collapsed under 700px unless the viewer opened it. Chooser/intro and desktop layout unchanged |
> | Generated cell names look too precise | **Fixed** | Detail subtitle shows the stable area id; name tooltip says it is generated from nearby places, not a boundary |
> | Consolidate duplicated city apps | **Already done** before the audit (this repo) |
> | Canopy recovery: four public CHM tiles reachable; Discovery Bay USFS package missing | Open, first data task | See addendum below |
>
> Fixed earlier the same day, from a separate audit: session weights leaking between cities,
> opening an area marking the session unsaved, A/C driver copy, dead legend caption and
> Simple-mode code, two unescaped popup fields, Bakersfield A/C weight 0.25 to 0, LACE silent
> fallback, hackathon residue, minimum 11px type, landing-page jargon.

Audited September 13, 2026. Target: https://advikar.github.io/coolequity-app/.

## Verdict

Strong student/portfolio work and a credible exploratory prototype. Not yet a professionally validated municipal investment tool. Presentation is ahead of evidentiary certainty and reproducibility. It can support a conversation about where to investigate; it cannot yet establish where planting will produce the greatest benefit, what is actually plantable, or reliable project budgets.

Subjective readiness ratings: visual identity 8/10; desktop usability 7/10; analytical transparency 7/10; decision-grade accuracy 4/10; operational planning usefulness 5/10. These are reviewer judgments, not measured benchmarks.

## Scope and verification

- Opened the live chooser and all three city maps. Inspected default priorities and statistics in each city; performed deeper county interaction, data and implementation review.
- Checked county selection, alternate-priority reranking, searching, proxy-data display and the live guide. Older residents moved Rossmoor to first place and introduced six new top-25 areas.
- Inspected the actual deployed HTML for all three maps, the county guide, and all three deployed GeoJSON datasets. The county GeoJSON matches this checkout byte for byte; the deployed HTML differs. Local findings must not automatically be described as live defects.
- Verified San Ramon at 390 × 844 CSS pixels: no document horizontal overflow, but substantial map occlusion by controls and the expanded legend. This is a responsive spot check, not a full mobile or accessibility certification.
- No county console warnings/errors were captured during the sampled session.
- Local UI-contract suite passed, including 11,436 scenario cases, scoring/rank parity and export contracts. Eight Python tests passed. These validate implementation consistency, not external accuracy, and do not certify all deployed branches.
- Independently reproduced the deployed scenario import's failure to restore unit cost by executing its extracted loadScenario function with minimal stubs. A file specifying $1,200/tree returned success with the same-data message while COST_TREE remained $500.
- No product files or city branches were changed. Existing user documentation edits were preserved. This audit did not rerun raw imagery processing, verify facilities in person, inspect every route, certify security/accessibility, or fully exercise downloaded PDFs and file-upload round trips in each city.

## What is already good

The serif identity, map palette, consistent panels and light theme look intentional. The product has a clear policy question rather than a generic map landing page. Presets, visible explanations, ranks, shortlist controls and exports form a plausible professional workflow. The implementation distinguishes map coloring from reranking, surface from air temperature, and relative scores from measured risk. Source metadata, data fingerprints, locally bundled assets and tests are meaningful foundations. The guides contain unusually candid limitations for a student project.

The strongest existing use is preparing a shortlist for field investigation and explaining how chosen priorities affect it. Preserve that focus.

## Release defects and misleading contracts

### High: scenario files do not restore custom costs

The deployed county exportHeader saves planting_assumptions.cost_per_tree_usd. loadScenario restores weights, population weight, shares and selection but never restores that assumption. It nevertheless reports successful loading and matching data. A scenario saved at $1,200/tree can reopen at $500/tree. CSV headers also omit the planting-assumption object, while exported notes still hard-code $500.

Fix: version and round-trip every assumption; reject unsupported assumptions or explicitly warn. Repeat all material assumptions in CSV columns. Acceptance: a fresh page reproduces tree count, canopy gain and cost from a custom-cost file exactly, with matching data and model versions.

### High: shared links are not an exact scenario

The live county share function includes only rounded weights, population weight, layer and selected cell. It omits planting shares, unit cost, shortlist, filters, sort, map extent and data fingerprint. applyHash explicitly declines access/HOLC layer restoration. The interface says a copied link reopens the exact view including planting shares. That promise is false.

Fix: define a versioned scenario/view schema shared by links and files, or narrow the promise to what actually survives. Avoid rounding weights if exact rank reproducibility is promised.

### High: greenness is still labeled/exported as trees

County cell 310, The Willows At Bethel Island N 16, displayed “60/100 trees” in the ranked row. It has no canopy assessment. The detail distinguishes greenness, and the tree layer mutes proxy cells, but the row keeps the label “trees.” The export writes p.green into tree_cover_pct even for NDVI records. The guide explains the overload; that does not make it a safe quantitative column for downstream averages or joins.

Fix: separate canopy_pct and greenness_index; canopy must be null when unknown. Make row labels, sort and the Trees <10% filter source-aware. Do not treat lack of evidence as low canopy.

### Medium: plantability labels exceed evidence

The “Plantable” filter checks scenario availability, which reflects mapped street length and cell area. The CSV names that length plantable_street_m and calls it available for planting. No ownership, utilities, planting strip, existing-tree or site survey establishes that availability.

Fix: rename to “Mapped street capacity” or “Scenario available.” Reserve plantable for assessed sites. Keep theoretical capacity and verified capacity as separate fields.

### Medium: guide duplication

The deployed county guide contains two Export & reload a scenario sections. IDs export, export-area and export-fields each occur twice. This makes anchor targeting ambiguous and invites inconsistent maintenance.

Fix: remove the duplicate and enforce unique IDs and working internal anchors in release checks.

### Medium: reset is incomplete in deployed county code

resetMap clears search, shares, selection and some map controls but does not reset RANK_FILTERS, RANK_SORT, RANK_DIR or COST_TREE. Its “original settings” promise is broader than its implementation.

Fix: define the default state once, explicitly decide whether shortlist is preserved, and test reset after every editable control has changed.

### Accessibility and input hardening follow-ups

Live ranked rows expose a button role containing a separate star button. This deserves keyboard/screen-reader verification and a sibling-control structure. Small controls and dense 11–12px supporting text make sustained reading harder. CSV escaping handles separators and quotes but does not neutralize spreadsheet-formula prefixes in external names; harden it before accepting arbitrary imported/community data. No exploit was demonstrated in the current dataset.

## Data evidence

Counts below were calculated from the deployed datasets, restricted to ranked residential cells.

| City | Ranked cells | Full aerial coverage | Partial aerial coverage | Legacy, coverage unknown | No canopy/NDVI proxy | Straight-line walking fallback |
|---|---:|---:|---:|---:|---:|---:|
| Contra Costa | 2,697 | 788 | 542 | 936 | 431 | 21 |
| Bakersfield | 3,788 | 1,960 | 349 | 1,479 | 0 | 45 |
| San Ramon | 419 | 356 | 61 | 2 | 0 | 0 |

“Full” is a coverage category, not percent accuracy. In Contra Costa, 121 residential cells have an aerial source covering less than 10% of the cell. The default top 25 all use the aerial source; that is reassuring but is not an independent validation of their ordinal ranking.

Sources: [county data](https://advikar.github.io/coolequity-app/contracosta/data/contracosta.geojson), [Bakersfield data](https://advikar.github.io/coolequity-app/bakersfield/data/bakersfield.geojson), [San Ramon data](https://advikar.github.io/coolequity-app/sanramon/data/sanramon.geojson).

### Need is not marginal benefit

The central headline asks where new trees would help most. The score combines selected indicators of need; it does not estimate site-specific marginal benefits of actual projects. High need, physical feasibility and expected benefit per dollar are distinct questions. A high-ranked hex can be a poor immediate planting project, and an unranked employment area can still have substantial daytime exposure.

Position the current product as “Where should we investigate shade investment first?” Add feasibility and benefit comparison as separately validated stages. Do not add a budget optimizer on top of unverified capacity and costs and call its result optimal.

### Mixed canopy sources distort comparability

Pooling assessed-land percentages, unknown-coverage legacy estimates and greenness proxies into one normalized input makes scores comparable numerically without establishing comparable measurement. The detailed caveats are good, but ranking rows still look equally authoritative.

Show source, year, assessed fraction and a concise reliability flag beside each selected metric. Offer a verified-coverage-only comparison and disclose excluded residents. Do not simply discard low-coverage communities: map missing evidence as a priority for data collection. Assess rank sensitivity to source choice and partial coverage.

### Fine cells do not imply fine demographic knowledge

County population is allocated from larger census areas. The guide says ACS margins of error are retained in source data but are not propagated into score uncertainty. Adjacent hexes can inherit the same uncertain information; treating their rank difference as meaningful is unjustified.

Publish robust priority bands, rank ranges or top-tier stability under plausible input and weight variation. Model spatial-allocation uncertainty as well as sampling uncertainty, preserving correlations between cells derived from the same census geography. The Census Bureau explicitly advises considering margins of error in comparisons: [ACS statistical testing](https://www.census.gov/programs-surveys/acs/guidance/statistical-testing-tool.html).

### Cooling discovery is not verified relief

The county introduction says 486 “places to cool off,” but these are mapped discovery sites, not 486 verified accessible cooling facilities. The official directory is a separate reference. County data flags 2,238 residential cells for approach review and 34 for detour review; 21 use straight-line fallback. A >100m approach flag is not proof of a bad route, but it means the displayed minutes are not verified door-to-door access.

Separate confirmed cooling services from possible sites, display destination identity and route quality, and retain last-verified date, entrances, public access, fees, A/C and hours. Do not infer public pass-through rights from inclusion of private streets in the routing graph. The public-facing product should not imply emergency or open-now reliability.

### Planting outputs need time, survival and local cost

For the top county area, the 25% scenario showed 513 trees, +2.7 canopy percentage points and $256,500. The arithmetic is coherent; site capacity and outcomes are not established. Uniform spacing and crown size do not account for utilities, existing crowns, soil, species, establishment water, mortality or maintenance. An exact dollar total visually feels more certain than the assumptions warrant.

Add low/base/high locally justified costs, establishment and lifecycle costs, a stated maturity horizon, species/crown ranges and survival. Prefer feasible shade added along important pedestrian destinations as a primary benefit. Keep air cooling secondary and explicitly conditional. Field evidence shows survival can materially reduce realized benefits: [Forest Service Sacramento monitoring](https://research.fs.usda.gov/treesearch/48956).

### Improve heat evidence without inventing precision

The guide correctly distinguishes summer satellite surface temperature from air temperature and live conditions. The deployed sort text says late morning; the local checkout's afternoon wording is a local-only drift issue, not a current live bug.

For a stronger analytical release, retain per-cell valid-observation counts, scene dates, thermal quality flags and temporal variability. Validate spatial patterns against independent observations where possible. Excluding heat from county defaults avoids one comparability problem but does not prove hotter inland climates are irrelevant to need. Consider within-climate comparisons and separate heat-exposure evidence. USGS documents surface-temperature retrieval inputs and limitations: [Landsat surface temperature](https://www.usgs.gov/landsat-missions/landsat-collection-2-surface-temperature).

## Usability and professional workflow

- The chooser followed by another large city intro adds friction. Make the city card open the map; preserve a compact optional introduction.
- The desktop three-column view squeezes the map and makes users scroll separate panels. Reduce the visible controls to choose priorities, shortlist, compare, and export; keep diagnostic detail expandable.
- At 390 × 844, San Ramon's expanded legend covers much of the lower map, while the top panel and map controls use much of the remaining space. Start mobile with a compact legend and a clear Map/List switch; open details in a deliberate drawer.
- Generated names such as “Coventry Place Apartments W 12” and “The Willows At Bethel Island N 16” resemble geography more precise than it is. Show stable cell ID, municipality and nearby cross streets, and explain generated labels. Add address/street lookup if supported by an appropriate geocoder.
- Add side-by-side comparison of 3–5 areas, municipal/district boundaries and filtering, assignment/status/field notes, and an evidence-complete briefing output. These reduce real analyst work more than more decorative layers.
- Keep U.S. users' likely unit expectations in mind: a fresh session starts with Celsius even though the root highlights Fahrenheit.

## Recommended sequence

1. **Release integrity:** fix cost import, scenario links, CSV semantics, duplicate IDs and reset; make uncertainty and discovery status visible at the point of use. Test the deployed build, not only a potentially different local branch.
2. **One-city validation:** select a bounded pilot; manually audit a stratified sample across ranks and data-quality categories; have an urban forester and GIS analyst review sites, assumptions and systematic errors. Publish findings and acceptance thresholds before claiming decision readiness.
3. **Decision workflow:** compare candidates, filter jurisdiction, record field verification, and export a reproducible packet with uncertainty, assumptions and evidence dates.
4. **Stronger models:** consistent canopy measurement, population-allocation validation, rank stability, verified service routing, realistic planting growth/cost/survival.
5. **Maintainability:** consolidate duplicated city applications into a shared UI with city configuration; make current documentation authoritative and move superseded notes into history. Require per-city deployment smoke tests, round-trip tests and unique-anchor checks.

Professional readiness would mean a planner can understand the evidence, reproduce a colleague's scenario, identify what needs checking, and take a candidate through field verification without being misled by its precision. Another visual redesign alone will not get the product there.

## Addendum: verified local screening sources

Researched September 13, 2026. These are proposed integrations, not changes to the deployed product. Existence of a source or field is not evidence that its coverage, freshness or completeness meets the product's needs.

| Place / source | Verified evidence | Recommended screening or product change | Qualification |
|---|---|---|---|
| San Ramon tree inventory | Official point service exposes species, diameter, crown, condition, utility, planting-strip and irrigation fields; a three-record query succeeded. | Overlay existing inventoried trees and recorded constraints; use species and measured attributes where populated to inform scenarios. | Service description references February 2017. All three sampled records had ActualCrown=0, TreeCondition=N/A and blank AcceptedDate. Audit units, missing-value conventions, positional outliers and update dates before use. Absence of a point does not prove absence of a tree. |
| San Ramon maintenance jurisdiction | City describes maintaining over 400 acres of landscaping across public rights-of-way, medians and special assessment zones. LLAD_Zone services appear in its GIS directory. | Show maintenance jurisdiction and separate city-deliverable candidates from projects needing private participation. | An assessment district is not a parcel ownership or planting-permission layer. |
| Contra Costa Our Tree Plan | Official program plans urban canopy assessment, soil/species work for two climate zones, maintenance financing and monitoring for unincorporated areas within the Urban Limit Line. | Add incorporated/unincorporated and Urban Limit Line filters; seek published assessment outputs and local validation; distinguish climate-specific planting assumptions. | The program page describes planned work, not a finished replacement raster. Do not apply unincorporated-county program scope to all incorporated cities. |
| Contra Costa adopted climate plan | Discusses canopy, impervious cover, heat islands and nighttime heat retention, including affected parts of East and West County. | Add impervious-cover context and compare heat within comparable climate areas; retain a separate exposure view. | This supports examining these factors; it does not validate particular numerical weights or local cooling coefficients. |
| Bakersfield/Kern designated cooling services | Official 2026 schedule names East Bakersfield Veterans Building and The Mission at Kern County, seasonal dates, county temperature activation rules and facility exceptions. | Separate designated services from discovery sites. Record activation conditions, season, facility-specific hours and timestamped daily status; expose 211 transportation assistance. | County valley threshold is forecast >=105°F and usual hours are 1–8 p.m.; The Mission has different rules/hours. Threshold satisfaction is not confirmation of opening. Resolve conflicting addresses/hours before routing to an entrance. |
| Bakersfield property inventory | Official polygon service has APN, class, acreage, status, zoning and formerly-owned fields. | Intersect candidates with property inventory, inspect ownership/status and exclude disposed assets where appropriate. | Service presence is not proof every polygon is currently city owned. Validate field meanings, dates, right-of-way limits and actual site feasibility. |

Sources:

- [San Ramon tree layer](https://gis.sanramon.ca.gov/server/rest/services/Fieldwork/Trees/FeatureServer/0) and [service description](https://gis.sanramon.ca.gov/server/rest/services/Fieldwork/Trees/FeatureServer).
- [San Ramon landscaping responsibilities](https://www.ci.san-ramon.ca.us/our_city/departments_and_divisions/public_works/landscaping_and_trees) and [Public Services GIS directory](https://gis.sanramon.ca.gov/server/rest/services/Public_Services).
- [Contra Costa Our Tree Plan](https://www.contracosta.ca.gov/10541/Our-Tree-Plan) and [adopted 2024 climate plan](https://www.contracosta.ca.gov/DocumentCenter/View/84967).
- [Kern County 2026 schedule](https://www.kerncounty.com/Home/Components/News/News/3855/34810) and [cooling-center service / transportation](https://www.kerncounty.com/government/aging-adult-services/services/cooling-centers).
- [Bakersfield property inventory layer](https://gis.bakersfieldcity.us/webmaps/rest/services/General/PropertyManagement/MapServer/0).

Suggested order: designated cooling-service screening; San Ramon inventory quality assessment; jurisdiction/property overlays; locally supported species, soil and scenario assumptions. No verified local evidence found in this research establishes $500/tree, 40 m² per crown or the uniform air-cooling coefficient as appropriate across all three locations.

## Addendum: are the canopy gaps unavoidable or paywalled?

### Correct interpretation of the earlier audit

“No canopy” in the audit table means **no canopy-specific value in the shipped dataset**, not no trees, no imagery anywhere, or data withheld behind a paywall. The 431 proxy-only residential cells are all in Contra Costa. Bakersfield and San Ramon have no proxy-only residential cells in the audited release, but have partial aerial coverage and legacy-source issues. Full aerial coverage is also not a guarantee of classification accuracy.

There are three distinct problems:

1. **Source footprint:** the USFS/CAL FIRE product is an urban-area assessment, not wall-to-wall county land cover. Rural fringes and hexagons crossing its boundary can legitimately be unassessed or partial.
2. **Incomplete acquisition or processing:** the local aerial cache contains four named assessment regions; the official catalog contains additional packages, including Discovery Bay. The legacy height pipeline catches any tile-open exception and continues, so a failed request can be exported as unavailable data. No retained run log establishes the original cause for every gap.
3. **Insufficient provenance:** the legacy CSV does not preserve valid assessed extent. Even where a value exists, its coverage cannot be certified from that value alone. This is a pipeline/provenance deficit, not proof that the upstream raster lacks coverage.

The official USFS source is public-domain/CC0 and offers 0.6 m 2022 aerial-derived canopy. It explicitly limits analysis to Census urban areas and notes that downloadable data can exist for places no longer classified as urban under the newer boundary definition. A package labeled California-wide must not be interpreted as wall-to-wall rural coverage. [USFS California Urban Canopy Data](https://www.fs.usda.gov/r05/state-tribal-forestry/california-urban-canopy-data).

### Direct checks of the existing public height source

The local missing-cell geometry was grouped by centroid into the same quadkey regions used by pipeline/02c_canopy.py. All 431 proxy-only residential cell centroids fall into four regions:

| Legacy source tile | Proxy-only cell centroids | Public file check |
|---|---:|---|
| 02301021233 | 174 | HTTP 200 |
| 02301021320 | 121 | HTTP 200 |
| 02301021302 | 71 | HTTP 200 |
| 02301021322 | 65 | HTTP 200 |

All four files were accessible without credentials. Small 32 × 32 pixel windows were read around three missing-cell centroids in each region. Files report uint16 values, CENTIMETERS and no explicit nodata value. Eleven windows were uniformly 2 cm. One window, in cell 1193 (Clayton Palms Community S 18), ranged from 24 to 1,415 cm, including clearly nonconstant modeled vegetation heights despite the app currently using NDVI for that cell.

**Finding:** at least some relevant canopy-height information is publicly accessible where the app currently has no canopy value. The four files' existence does not prove that all 431 full cells have useful observations. With no nodata flag, a raster library reporting every pixel valid is insufficient evidence; uniform near-zero values need review against source footprints and imagery. These checks establish a recovery opportunity, not a validated repaired canopy percentage or proof of the historical failure cause.

Public file pattern checked: `https://dataforgood-fb-data.s3.amazonaws.com/forests/v1/California/alsgedi_ca_v5_float/chm/{tile}.tif`. The [AWS Open Data registry](https://registry.opendata.aws/dataforgood-fb-forests/) identifies the public California source and CC-BY-4.0 license. This is a modeled height product, not direct lidar measurement.

### Additional aerial package worth checking first

The official catalog lists **Discovery Bay**, but no Discovery Bay raster is present in this checkout's aerial cache. Among residential cells whose generated names contain “Discovery Bay,” 69 are proxy-only and four use legacy canopy. These names are not official boundaries: a full geometry intersection with the package footprint is required before estimating how many cells it would repair. This is a specific missing-acquisition lead, not a paywall finding. Do not claim all 69 are covered until that intersection and valid-pixel assessment are complete.

### Better data options and their actual tradeoffs

| Option | Access | Potential benefit | What remains to establish |
|---|---|---|---|
| Complete the 2022 USFS/CAL FIRE package set | Public, CC0 | Consistent aerial canopy for covered urban areas; first acquisition to investigate for Discovery Bay. | Match all intersecting package footprints, source masks and cell geometry. Remaining rural land will not automatically be covered. |
| Rebuild the existing California WRI/Meta height fallback correctly | Public, CC-BY-4.0 | Recover missing usable source data; preserve observed extent and stop swallowing download failures. | Confirm source footprints, units, zero/fill meaning and local classification performance. Height thresholding is not identical to aerial tree-crown classification. |
| WRI/Meta global 1 m height product | Public, CC-BY-4.0 | An alternative to benchmark where the older regional source is missing or unsuitable. | WRI documents imagery from 2009–2020 despite dataset creation in 2024; it is not a 2024 tree survey. Its reference canopy uses >=3 m while this pipeline uses >=2 m. Harmonize definitions and compare local errors. |
| 2022 USGS Contra Costa lidar | Free public point clouds | Detailed 3D observations could improve canopy height and validate candidates within the acquisition footprint. | Metadata covers about 163 square miles, not the entire county. Intersect actual tile footprints with gaps. Derive canopy from above-ground returns plus building/vegetation separation; a bare-earth DEM alone cannot supply canopy. |
| NAIP aerial imagery plus canopy classification or manual interpretation | Public imagery | Broad raw-imagery route for gaps; leaf-on imagery supports tree/lawn separation with a suitable model and validation. | Raw imagery is not a ready-made canopy map. Determine actual local acquisition dates, classify, and measure omission/commission error on a held-out local sample. |
| Commercial EarthDefine Tree Map / commissioned urban canopy assessment | Commercial; free samples advertised | Potentially more recent, consistent fine-resolution coverage and custom delivery. | Vendor advertises 60 cm and on-demand production from latest NAIP. Obtain actual local image dates, footprint, accuracy evidence, license and quote. Marketing accuracy is not accuracy for these cells. No local price or guaranteed superiority was verified. |
| National 30 m tree canopy | Public | Coarse regional comparison or fallback sensitivity analysis. | Too coarse for individual crowns and street planting decisions; do not assume it improves on 0.6 m urban classification. |

Sources and qualifications:

- [WRI baseline methods](https://coolcities.wri.org/data-and-methods/tree_cover_baseline): documents 1 m modeled extent, a 3 m height threshold, source imagery dates and limitations. Release year and observation year must be distinct in the UI.
- [2022 USGS Contra Costa lidar metadata](https://www.fisheries.noaa.gov/inport/item/69121): 485 tiles, spring 2022 acquisition, approximately 163 square miles, free access. Exact coverage of the missing cells remains unverified. Its [USGS project report](https://rockyweb.usgs.gov/vdelivery/Datasets/Staged/Elevation/metadata/CA_ContraCosta_B22/USGS_CA_ContraCosta_B22_Project_Report.pdf) lists ground/unclassified and other classes rather than a ready-made tree-canopy class; elevation accuracy is not canopy-classification accuracy.
- [USGS NAIP imagery service](https://imagery.nationalmap.gov/arcgis/rest/services/USGSNAIPPlus/ImageServer) and [USDA imagery catalog](https://catalog.data.gov/dataset/national-agriculture-imagery-program-naip-imagery): imagery is an input to a new assessment, not proof of canopy at a particular location. Use the provider catalog to establish local acquisition dates.
- [EarthDefine Tree Map](https://www.earthdefine.com/treemap/): commercial product candidate, not an independently validated recommendation to purchase.
- [Forest Service national tree canopy](https://data.fs.usda.gov/geodata/rastergateway/treecanopycover/): regional benchmarking option.

The search also found [2018 Southern California lidar metadata](https://www.fisheries.noaa.gov/inport/item/58709) mentioning portions of Kern County. That is insufficient to claim coverage of Bakersfield or its legacy-source cells; verify acquisition polygons before prioritizing this route. San Ramon's city inventory is useful validation/context, but point locations cannot replace a complete canopy-extent raster.

### Recommended recovery and validation work

1. Build a per-cell coverage manifest from the actual source footprints and valid pixels: source, observation date, downloaded tile, checksum, successfully read fraction and failure reason. Export missing, unassessed and observed zero as different states.
2. Acquire and intersect the missing urban assessment packages, starting with Discovery Bay. Recompute only after assessing overlap, resolution and nodata conventions.
3. Reprocess the four accessible legacy source tiles with recorded coverage, retries and explicit failures. Spot-check suspicious constant windows against aerial imagery; do not equate an absent nodata mask with observations.
4. Benchmark remaining gaps using available NAIP and, where footprints overlap, lidar. Compare newer commercial samples only if open-data recovery still fails the required quality level.
5. Validate urban fringe, agricultural/orchard, sparse-tree and dense-tree samples separately. Report canopy error and rank changes, including the top-25 overlap. Do not harmonize incompatible sources merely by placing them in a percent column.

**Conclusion:** the current gaps are not established as a paywall problem. There are verified public recovery opportunities and stronger raw-data options. The substantial work is acquisition completeness, provenance, classification and local validation. It would be premature either to buy data or to promise every gap can be filled accurately from the files checked so far.
