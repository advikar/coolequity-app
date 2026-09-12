# Owner review: what a city can buy, and what still needs work

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


## Implementation update — first analytical release completed

September 7, 2026, Contra Costa branch. The proposal below is retained as audit history;
this status takes precedence.

**Delivered:** canopy fallback repair and raster rebuild, explicit coverage/source/year,
partial/unknown-coverage scenario protection, ACS 2024 refresh with matching geometry and
native margins of error, occupied-home LACE weighting/coverage, reproducible scoring,
public greenness exploration, and subordinate air-cooling presentation.

**Evidence:** 866 inconsistent canopy-area rows repaired; canopy percentages unchanged.
1,334 aerial cells / 1,079 legacy height-map / 446 vegetation-only. 789 aerial cells meet the
99% operational coverage threshold, 788 of them residential. 2,697 ranked residential cells.
24/25 top priorities retained; median rank movement 8, largest 393. Controlled 2023 A/C
correction changes estimates by up to 5.4 percentage points, with population/age unchanged.
Report: `reports/rebuild_summary.json`; all-cell comparison: `reports/rebuild_cell_changes.csv`.

**Still unresolved:** unassessed rural/fringe canopy and unverified legacy CHM extent/ROW area;
local independent canopy accuracy checks; area-allocation validation and propagation of ACS
uncertainty; native-geography income analysis; official heat-site roster/service routing;
locally calibrated planting costs, species, growth and survival; reproducible user scenario
exports and deployment/operational acceptance. This release does not make those claims.

**Vegetation recommendation implemented:** public in Explore, with canopy separate from
scaled satellite greenness. Do not call the difference non-tree vegetation or render corridor
areas as public planting sites. Priority remains the main workflow.

**Temperature recommendation implemented:** air cooling is a secondary illustration; surface
temperature remains measured spatial context. The original coefficient traces to Krayenhoff
et al. (2021), an informal meta-analysis of numerical simulations for clear-sky summer
conditions, not a local field response. Surface and air effects are not interchangeable.
A later pedestrian-comfort model may better represent shade benefits, but requires additional
geometry, weather and validation; a stronger-looking surface-temperature number is not a fix.
Primary reference: https://doi.org/10.1088/1748-9326/abdcf1.

Next implementation priority: authoritative facility data and routing validation, followed by
configurable, evidence-backed planting assumptions and saved/exportable scenarios. City
arborist/procurement review remains an external acceptance step.


Reviewed September 7, 2026. Scope: Contra Costa application, its pipeline and committed
inputs, source documentation, and the revised guide. These are findings for the product
owner; this document is not part of the customer-facing guide.

**My judgment: the defensible product is a transparent tree-investment prioritization and
scenario tool. It is not yet a government production-grade planning system.** Good source
names do not validate our joins, assumptions, or outputs. Presentation now makes the use
case clearer; the data and operational gaps below determine whether a city can rely on it.

The previous review was too reassuring about canopy coverage. That is corrected here.
“Keep USFS canopy” is a recommendation about the source family, not approval of the current
county mosaic, fallback behavior or denominator choices.

## What I changed immediately

- Every guide topic leads with an actual city use case, then explains the source/method
  choice. Numeric detail is a disclosure. Decision-relevant notes are short, subordinate
  paragraphs, not warning panels. Unverified “better option” suggestions moved here.
- Smaller 16px visual info rings retain 24px link targets and keyboard focus styling.
- Search and pagination cover all 2,695 ranked residential cells, with keyboard selection.
  This is place-name/cell-ID search, not address geocoding or a complete unranked-cell table.
- Facility category filters are native buttons with pressed state. Protected local-storage
  access no longer prevents startup. Loading failures offer user-facing recovery instead of
  developer shell commands. Third-party place/site names are escaped before HTML insertion.
- Added `green_src` to the score export and current GeoJSON, without changing any prior
  numeric field, score, rank or geometry. All 446 missing-canopy cells (430 residential)
  use `ndvi`; the remaining cells use `canopy` (aerial or height-map source).
- Corrected proxy-cell metrics, list labels, hover and score explanation. Planting scenarios
  are disabled for those cells because an observed canopy baseline is unavailable.
- Retired the prior canopy-equity claim from the landing screen pending a canopy-only
  verification. The previous numbers remain documented as analysis history in the guide.

## Highest-priority findings and proposed changes

### 1. Canopy coverage and export consistency — must resolve before citing county canopy findings

**Verified from local inputs:** 446/2,859 rows in `canopy_contracosta.csv` have no canopy
percentage, including 430/2,695 residential cells. For every missing row, the shipped `green`
value matches `satellite_contracosta.csv`'s vegetation proxy. None is in the default top 25.
Thus the “all canopy” framing was false; source labels and scenario guards are now corrected.

Separately, 866 rows have positive canopy percentages but zero `canopy_m2`, including 860
residential cells. In `02d_canopy_usfs.py`, the fallback loop recomputes missingness after it
has already filled `canopy_pct`, preventing its matching area fields from being filled.
That is an implementation defect. The current UI calculator uses percentage, whole-cell
area and street length, not `canopy_m2`; exported area fields still need repair.

**Propose:** retain USFS/CAL FIRE 2022 urban canopy; freeze the pre-fill missing mask and
apply it consistently to every fallback column. Export assessed area, coverage fraction,
aerial/CHM/NDVI source, source year and quality state. Audit which urban areas are missing,
rebuild canopy, and verify a stratified sample against source rasters. Keep unassessed land
separate from “no trees.” Recheck county statistics and ranking stability before publishing.

The current canopy percentage is over assessed urban land, while the scenario applies it
to whole-cell area. Partial-coverage cells need a consistent scenario denominator or a
scenario exclusion. The new NDVI guard does not resolve this partial-coverage issue.

**Source assessment:** CAL FIRE's May 2025 director report confirms 2022, 60cm canopy for
2020 Census urban areas and 2018–2022 change data. The old USFS landing URL could not be
retrieved by the research tool; the CAL FIRE report independently verifies the product.
No verified countywide replacement was found that establishes greater accuracy for this
specific use. A tree inventory answers individual-tree/site questions; it is not automatically
a replacement for continuous canopy coverage. Do not buy/swap a new product on that premise.
[CAL FIRE report, page 3](https://cdnverify.bof.fire.ca.gov/media/xs2oiyts/full-8-may-2025-director-s-report.pdf#page=3)

### 2. Population, age and income — refresh and validate allocation

**Verified:** ACS 2023 remains configured. The 2020–2024 ACS five-year release became
available January 29, 2026, including block-group detailed tables. Recommend updating to
that release with a before/after reconciliation; newer is a freshness improvement, not a
proof of more accurate per-cell allocation.
[Census release](https://www.census.gov/programs-surveys/acs/news/data-releases/2024/release.html)

Area allocation is a defensible response to the project's observed OSM building-coverage
bias, but it spreads residents over uninhabited land. Propose testing a residential-land or
housing-unit allocation against area weighting, preserving block-group totals and checking
spatial error with local records. 2020 Census blocks are candidates for allocation weights,
not current exact household counts: they are older and privacy-protected. My earlier guide's
suggestion that finer census geography simply “improves” accuracy was too categorical.
[Census small-area privacy guidance](https://www2.census.gov/library/publications/decennial/2020/census-briefs/c2020br-03.pdf)

Carry ACS margins of error into a reliability analysis. The age-65+ factor has a sound
substantive rationale, but the 100-person smoothing strength has no identified local
calibration. Test rank sensitivity to it; never imply CDC endorses that constant.
[CDC age and heat](https://www.cdc.gov/heat-health/risk-factors/heat-and-older-adults-aged-65.html)

The code averages block-group median income using population weights. That is not a cell
median. Rebuild income-equity findings at their native geography or from defensible
household distributions; a simple “median of medians” replacement is not a statistical fix.

### 3. A/C — keep LACE, correct the denominator

LACE is a documented Census experimental model of occupied housing units with A/C.
It is appropriate as a tract-level home-cooling input. All current residential cells are
LACE-backed. There is no evidence here that an assessor extract is complete enough to be a
superior countywide replacement; propose checking it, not promising it.
[Census technical guide](https://www2.census.gov/programs-surveys/demo/technical-documentation/lace/2023-LACE-Quick-Guide.pdf)

**Code finding:** `03_census.py` averages tract A/C rates with allocated people as weights,
then the UI labels the result “% homes.” Propose occupied-housing-unit weighting, carrying
numerators/denominators and coverage through the join. Validate single-tract cells, mixed
tracts, zero-housing cases, suppressed tracts and whole-county reconciliation. Publish A/C
source and uncertainty flags. Do not silently change rankings during a copy-edit pass.

### 4. Facilities and walking — replace “potential” with verified service data

OSM libraries/pools/community facilities are a useful discovery inventory, not a verified
heat-service network. Contra Costa's official heat page provides a better starting authority
for designation, but I have not verified that it exposes a stable, complete machine-readable
feed or current opening schedules. Add an authoritative roster with hours, eligibility,
fees, accessibility, last verification time, owner and a process for updates; retain OSM as
supplemental potential sites. Recalculate access against the chosen eligible service set.
[County heat resources](https://www.contracosta.ca.gov/10174/Heat-Safety-Tips-Places-to-Cool)

All existing overlay rows are labeled routed. That alone is not validation: centroid-to-node
snap segments can cross barriers, and a single 4.8 km/h speed is not an accessible route
model. Validate actual routes, especially long snaps and disconnected components. Filters
currently change markers only; an operational service filter must recompute access or keep
the fixed denominator conspicuous. Routing alternatives alone do not fix a wrong site list.

### 5. Planting, cost and cooling — make local assumptions configurable and validated

10m spacing, 40m² crown and $500/tree are unsupported as universal or Contra Costa-specific
constants. They are useful transparent scenarios, not a defensible municipal budget.
Propose documented local low/base/high unit costs; species/crown, growth horizon and
survival assumptions; verified planting sites; and cost components for establishment,
irrigation, sidewalk work and ongoing care. Acceptance: a city arborist reviews the model
and a procurement contact checks costs against recent projects.

The i-Tree Planting tool supports species, initial size, project horizon and mortality. It is
a relevant comparison model, not a drop-in guaranteed upgrade. Its website currently warns
of halted traditional USFS funding, so evaluate maintenance/support before making it a
production dependency. It does not make our air-cooling formula locally validated.
[i-Tree Planting](https://planting.itreetools.org/)

WRI supports the broad ~0.3°C per 10-point canopy illustration. It does not justify a precise
per-cell local cooling forecast. Keep illustrative labeling until local calibration exists;
do not advertise avoided illness, confirmed beneficiaries or financial ROI without models
and evidence supporting those outcomes.
[WRI synthesis](https://www.wri.org/insights/urban-trees-cooling-potential)

### 6. Priority scoring — transparent preferences, then evidence of robustness

The current weights, clipping endpoints, population multiplier and heat exclusion are
project choices. No research source establishes our exact 55/25/20 formula as optimal.
The guide now says why it is interpretable without claiming external validation.

Propose automated sensitivity reports: top-25 overlap, rank shifts and driver changes under
weight ranges, alternative normalization, source exclusions and demographic uncertainty.
Ask city stakeholders to adopt the objective and defaults. Local heat detrending could be
benchmarked, but “removing climate” is not inherently correct for every policy objective.
[JRC sensitivity guidance](https://knowledge4policy.ec.europa.eu/composite-indicators/toolkit_en/navigation-page/10-step-guide_en/step-8-sensitivity-analysis_en)

## Remaining feature-by-feature review

| Feature | Keep / change | Production acceptance criterion |
|---|---|---|
| Landsat surface heat | Keep as spatial thermal context; refresh scene period and retain scene/quality metadata. | Document dates, cloud handling, coverage and sample comparison; never call it air temperature. TIRS is 100m native resampled to 30m, not independent 30m thermal detail. [USGS](https://www.usgs.gov/faqs/what-are-band-designations-landsat-satellites) |
| H3 grid | Keep stable IDs; validate boundary/denominator consistency. Offer census or administrative rollups for staff workflows. | Stable joins, geography provenance and consistent treatment of edge cells; validate aggregation before official area reporting. |
| Activity/empty classes | Keep context; these depend on estimated population and incomplete development mapping. | Field/sample checks and keyboard access to unranked cells; no “safe” interpretation of gray. |
| WorldCover | Keep broad land-context labels; no evidence that a newer/different source automatically improves this use. | Document year, dominant-class method and fallback; verify mixed-cell labels before treating them as land-use determinations. |
| Vegetation/export fields | Keep only with explicit definitions. NDVI is total vegetation proxy, not automatically “non-tree vegetation.” | Fix canopy/ROW area consistency; publish a field dictionary and sample values; validate differences before calling them lawn. |
| HOLC | Keep hidden where no grades. | Verified local coverage and historical-context wording; absence is not historical exoneration. |
| Place names | Useful locators, not official neighborhoods. New search improves access. | Add authoritative geocoding/admin-area search with clear geographic resolution and privacy review. |
| Map layers / units | Keep separate from score settings. | Explicit selected state; keyboard/touch tests; no scenario reset on unit changes. |
| Basemaps | Keep offline/plain fallback. | Verify service terms, attribution, request behavior and failure recovery for each deployment; validate mobile map geometry. |
| Coach / guide | Keep persistent contextual help. | Plain language tested with city users; source links monitored; source-version documentation maintained. |
| Search/list | Now all residential ranks are keyboard-accessible in pages of 25. | Add equivalent unranked geography browsing and usability testing; this is not WCAG certification. |
| Scenario persistence / export | Not delivered yet. | Save/share scenarios; versioned input/weight/assumption snapshots; accessible PDF/CSV or report export and deterministic reload. |
| Reliability / security | Startup and HTML-name handling improved; optional-site fetch still needs explicit failure reporting. | Input schema validation, visible partial-data failures, automated integration checks, deployment rollback, dependency/license inventory and security/accessibility review. |
| Government adoption | UI quality is necessary, not sufficient. | Assign data refresh/support owners; documented scope, service levels and accessibility assessment; pilot with real city workflows. Permissions/audit trails depend on whether multiuser editing is added. |

## Recommended sequence

1. Repair canopy coverage/area consistency and recheck all canopy-derived statements.
2. Refresh ACS; validate population and occupied-housing A/C allocation, then recompute
   rankings with before/after and uncertainty/sensitivity reports.
3. Establish official facility ownership and updates; validate routes against that service set.
4. Calibrate planting assumptions with a city partner and add reproducible scenario exports.
5. Run a pilot and accessibility/security/operational acceptance review before claiming
   enterprise/government production readiness.

These are proposed analytical upgrades, not claims that a data rebuild was completed.
This pass preserves existing values/ranks and adds source metadata and protective UI behavior.
