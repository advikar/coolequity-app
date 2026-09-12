> **History.** This is the `STATUS.md` of the `contra-costa` branch of [advikar/coolequity](https://github.com/advikar/coolequity/tree/contra-costa), carried over unchanged when the cities were combined into this repository (September 12, 2026). Paths, branch names, run and deploy instructions in it refer to that repository; the top-level README.md is current.

# CoolEquity — build status & handoff

## September 8, 2026 — delivery plan and portable model handoff

Added `DELIVERY_PLAN.md` with Claude-heavy ownership, dependency-ordered work through
publication, separate explorer/operational acceptance, and provider-switch instructions.
`HANDOFF.md` records the active next packet and recovery context. Planning only on
`contra-costa`; no product/data behavior or other city branch changed, no tests rerun,
and no deployment performed. Existing implementation changes remain in the workspace.
Inspection found `deploy.sh` omits the new cooling-directory JSON and archives committed
branches rather than local edits; repair and assembled-site verification are release work.

## Session 2026-09-06d — routed walk time + F-bar UI fix (DEPLOYED)

- **Routed pedestrian walk time replaces the straight-line estimate** (DATA_QUALITY
  W-1) on SR/CC/Bakersfield. New `pipeline/04b_routed_access.py`: builds the OSM
  walk graph with osmnx, runs ONE multi-source Dijkstra from all cooling sites,
  writes door-to-door `access_min`/`access_km` into `overlays_<slug>.csv`, then
  re-run 05. Door-to-door = network distance + the point→graph-node snap at BOTH
  ends, floored at the straight-line distance (so snapping can never make a walk
  shorter than crow-fly). Graph cached to `data/_cache/walkgraph_<slug>.graphml`
  (gitignored, ~1–266 MB); computed once offline, nothing routes at demo time.
- **Validated before shipping** (the reason it was staged): each city's walk graph
  is a SINGLE connected component (lcc=1.000), every hex reachable, routed/crow-fly
  ratio ≥ ~1.0 everywhere. Ratios reflect real geography — SR 1.67 (winding
  cul-de-sacs), CC 1.60, Bakersfield 1.42 (flat grid). The old ×1.273 circuity was
  systematically optimistic; barrier cases (a site across the freeway) now read true.
- **`access` is unweighted in every city's score, so score/rank are unchanged**
  (verified: max |score change| = 0, max |rank change| = 0 on all three). Only the
  displayed walk time, the ROI panel and the "No relief nearby" preset change.
  App copy updated from "estimated, not routed" to routed-on-OSM everywhere.
- Honest note: for the big-bbox cities the all-hex median walk is high (CC res 61
  min, Bakersfield res 68 min) — that is county sprawl + sparse OSM cooling-site
  coverage (Bakersfield has only 39 mapped sites), present in the straight-line
  method too; the priority hexes read 5–22 min. Routing makes the far ones more
  honest, not artefactual.
- **LA (master) NOT routed** — its ~3,400 km² basin bbox is a millions-of-nodes
  walk graph and tens of minutes of Overpass; deliberately out of scope, same as
  its canopy/WorldCover deferral.
- **UI fix (all four cities incl. LA):** the panel header (`.brandtop`) overflowed
  the fixed 366px panel by ~37px and clipped the **°F·mi units toggle**. Now the row
  wraps and the units control sits right-aligned on its own line — verified
  in-browser (units right edge 345 < panel 366). Pure CSS.
- `.gitignore` now excludes the osmnx HTTP cache (`cache/`, `pipeline/cache/`).
  Committed on all relevant branches, pushed to origin, published via `./deploy.sh`.

## Session 2026-09-06c — empty-hex land labels → ESA WorldCover (DEPLOYED)

- **The undeveloped ("empty") hexes now carry an authoritative land-cover label
  from ESA WorldCover 2021 v200** (10 m, Sentinel, CC-BY 4.0, via Planetary
  Computer), replacing the old lst/veg/canopy heuristic. New
  `pipeline/02e_worldcover.py` (single windowed read per WorldCover tile → majority
  class per hex → `worldcover_<slug>.csv`); `05_score.py` merges it and applies the
  label to empty hexes only, keeping `classify_land()` as an offline fallback.
- **Descriptive label only — scoring/ranking untouched.** Verified on all three:
  max |score change| = 0, max |rank change| = 0. Empty hexes are not scored, so
  this cannot move a ranking or a headline number. Live on SR/CC/Bakersfield;
  **LA left as-is** (still NDVI + old binary drop) per the standing instruction.
- **Why it's better, concretely:** the heuristic was right on water but lumped
  everything non-water as "bare / hillside." WorldCover corrects — CC: 12 hexes →
  Delta cropland (4) / grassland (7) / wetland (1); SR: 76 → golden grassland (80
  after reclass) / woodland (4), not bare; BK (San Joaquin Valley, where it matters
  most): the undifferentiated bare/hillside splits into cropland (42) / grassland
  (90) / genuinely bare ground (31) / woodland (9). Two BK empty hexes read
  "developed" — WorldCover sees paving OSM has no footprint for; left as an honest
  disclosure (muted, unranked).
- App: empty-hex detail now states "Land cover here is <X> (ESA WorldCover 2021,
  10 m)" instead of "inferred from satellite (likely …)"; footer credits WorldCover.
- Also fixed a **latent crash in 05's top-10 summary print** (`:d`/`:,d` format on
  the now-float rank/pop columns), exposed by the first full 05 re-run since the
  three-class model landed. Output format unchanged.
- **node --check passed on all three apps before deploy** (non-negotiable rule 2).
- Committed on all three source branches, then published with `./deploy.sh`.

## Session 2026-09-06b — full-coverage map + two shipped-bug fixes (DEPLOYED)

- **No more mystery holes. Every hex in the study area is now shown**, in three
  classes (`place` property): `res` (residents — scored/ranked), `activity`
  (developed but unpopulated — commercial/industrial, shown with real canopy/heat,
  greyed on Priority, NOT ranked), `empty` (undeveloped — shown muted, with a
  best-effort `land` label: open water / woodland / open land / bare hillside,
  inferred from the satellite layers). Classifier is buildings-aware (`02b`
  footprints), not street-only, so malls/schools/business parks are caught. The
  study-area boundary outline is now drawn ALWAYS. Live on SR/CC/Bakersfield.
  **LA left as-is** (still NDVI + old binary drop) per instruction.
- **Two of my own earlier edits had shipped BROKEN apps** — an unescaped
  apostrophe ("San Ramon's") killed the SR app JS, and a missing `}` killed the LA
  app JS. Both were blank/dead live until caught here. Fixed. **`node --check` on
  every app's inline script is now mandatory before deploy** (a data/parity check
  is not enough — the front end must be syntax-checked too).
- **UHI: decided AGAINST integrating.** The CalEPA index models 2006 & 2013, and
  sitting it beside the 2022–24 Landsat + 2022 aerial canopy would undercut the
  "current and accurate" credibility and confuse which heat reading is
  authoritative. Left documented-but-not-built in DATA_QUALITY.md.

## Session 2026-09-06 — canopy + A/C data upgrades (DEPLOYED)

Two headline accuracy fixes from the review shipped and are **live**:

- **Canopy → USFS/CAL FIRE 2022 aerial (0.6 m NAIP)** for **Bakersfield, San Ramon,
  Contra Costa** via new `pipeline/02d_canopy_usfs.py` (EPSG:3310 equal-area,
  per-hex windowed reads, urban-boundary denominator; CHM fallback for rural
  fringe outside census urban areas). Replaces the 2009–2020 Meta/WRI height
  model that read ~35% low. **San Ramon's real canopy is 17.7% over the average
  resident (was a false ~11%) — it is slightly ABOVE the CA urban average, so its
  brief was reframed from "thin canopy" to "uneven canopy."** **LA is still on
  NDVI** — its `master` pipeline predates the canopy contract; swap recipe is in
  `DATA_QUALITY.md` follow-up 1.
- **A/C → measured US Census LACE 2023 (tract)** for **all four cities** via a
  LACE join in `03_census.py` (income model kept only as a per-tract fallback;
  new `ac_src` column). Breaks the income-circularity in CC and LA (where A/C is
  scored). Bakersfield A/C is ~99% uniform (correctly stops skewing its ranking).

Source rasters/CSVs live in `data/_cache/` (gitignored): `canopy_src/` (USFS zips
per urban area) and `ac_src/LACE_23_Tract.csv`. `05_score.py` now stores `ac` at
2dp (measured A/C's clip range is narrow, so 1dp broke live-score parity).
All four re-verified: live-score parity < 0.1, ranks stable; populations intact.

**Non-negotiables that held:** checked every ranking/quartile claim against the
built geojson — corrected "all 25 top CC hexes poorest quartile" → 23/25, and SR's
"6 of 10 blocks east of Dougherty Rd" → 0 of 10 (thinnest are apartment complexes
central/west). `FINDINGS_CONTRACOSTA.md` + SR `BRIEF.md` + all app copy + the root
chooser updated and redeployed via `./deploy.sh`.

**Staged (recipes in `DATA_QUALITY.md`):** LA canopy swap, CalEPA UHI air-temp
layer (data downloaded to `/tmp/uhi`), routed walk time (deliberately not shipped —
can't guarantee accuracy at scale here; straight-line estimate stays labelled).

`DATA_QUALITY.md` (new, contra-costa branch) is the full caveat audit with fixes.

## Session 2026-09-05b — UI overhaul + accuracy review

**UI (done, deployed):** every app now has a real four-city switcher on the
landing screen (replaces the search-over-20-fake-cities combobox, which never
navigated) and an "All cities" link in the map header → the site chooser.
Bakersfield's San Ramon leaks fixed (panel description, HOLC note). Nav path is
derived by stripping each city's own suffix off the URL (`SITE_ROOT`), verified
live = `/coolequity/`. Applied via scratchpad `patch_ui.py` for consistency.

**Accuracy review — findings:**
1. **Non-robust min-max normalisation — FIXED & deployed (all four cities).**
   `05_score.py` now normalises each scoring input against a ONE-SIDED p2/p98
   clip, written into the geojson as `norm`; the app reads it into `svals` (used
   only for scoring, clamped [0,1]; colour ramps keep raw `vals`). One-sided on
   purpose: clip only the least-need tail (a single leafy/empty-cool block stops
   setting the scale) and never blunt the hottest/oldest/barest blocks — a
   two-sided clip flattened Rossmoor's 84%-elderly and broke Protect-seniors.
   Protective inputs (green, ac) + population clip the HIGH tail; heat/age clip
   the LOW tail. lst/green stored at 2dp so live parity holds (<0.13 all cities,
   top-10 exact). New top-3s: CC State Court Park/Nystrom Village/Atchison
   Village; SR Mosaic Park/Valencia S/Carmelita S; Bak Bakersfield S 5/S 3/
   Coventry; LA Skid Row/Little Armenia/Huntington Park. SR brief re-derived;
   CC seniors + LA Holmby-Hills preset copy re-checked live. Patchers in
   scratchpad: patch_score.py, patch_svals.py. Population is still skew-limited
   at the bulk (clip helps the top; rank/log would be the stronger fix if wanted).
2. **`row_m2` (02c) computed in EPSG:3857**, so it's mercator-area, inflated
   ~1.5× at 37°N. NOT user-facing (app/brief use `street_m`, real UTM metres) —
   latent bad column only. `canopy_pct`/`canopy_m2` are correct (ratio cancels;
   area from `h3.cell_area`).
3. **CHM canopy vintage 2009–2020** vs 2023 heat/census — stale in fast-growth
   areas (Dougherty Valley, new Bakersfield tracts). Disclosed in the brief's
   sources; not yet on the app footers.
4. **A/C = f(income) is 25% of CC's score** → the priority ranking is not
   income-independent (circularity). Headline equity stat is clean (raw canopy),
   and no copy claims "priority tracks income" — keep it that way.
5. Minor: "blocks/census blocks" for H3 hexes; LST is Landsat ~10:30 daytime,
   not afternoon (ROI "afternoon cooling" is WRI air-temp, a different quantity).

## Session 2026-09-05 — measured canopy live on all four cities

The site now serves **four** cities: LA `/app/` (still NDVI), San Ramon
`/sanramon/`, Contra Costa `/contracosta/` and Bakersfield `/bakersfield/`.
Deployed and verified over the wire (all 9 URLs 200, right content at each).

Done this session:
- **contra-costa**: committed the measured-canopy rescore (02c_canopy.py +
  05_score.py `veg`/`canopy_m2`/`row_*`); app copy corrected (canopy median 12.6%,
  63% of residents under 15%, income gap 8.9% vs 21.6% popwt, corr(heat,canopy)
  county −0.24).
- **four-city chooser** in `site/index.html` + `deploy.sh` (both live on the
  contra-costa branch — deploy from there).
- **san-ramon BRIEF.md** fully recomputed on measured canopy (median 10.1% ≈ 11%
  over the typical resident; the old −0.80 was corr with NDVI vegetation, canopy
  is −0.64; top-10 regenerated; Capella now rank 13). App lede/footer/captions
  fixed too.
- **bakersfield** app footer said "Contra Costa County" (copy-paste leak) and its
  veg caption carried San Ramon's correlations — both corrected (Bakersfield
  canopy~heat is only −0.24; irrigation, r=−0.82, carries the cooling).

**Outstanding (flagged, not done):**
1. `README.md` / `DEMO.md` on **san-ramon** still carry NDVI-era numbers
   (−0.80, 20.9%, 21%, the flat income quartile table). Not deployed, but redo
   before showing anyone.
2. `FINDINGS_CONTRACOSTA.md` §1 equity table and §5 headline numbers are still
   NDVI-era (median 19.7%, 32%/370k under 15%, top-25 12.0%, 36,928 trees/$18.5M).
   The app is corrected; this source doc is not.
3. The **bakersfield branch carries a stale copy of the San Ramon BRIEF.md** —
   wrong-branch leftover; give Bakersfield its own brief or delete it.
4. **Analytical note for review:** on measured canopy, in the dry-summer cities
   canopy's *partial* corr with heat (controlling for total NDVI greenness) is
   weak — San Ramon −0.21, Bakersfield −0.05 — i.e. irrigation/total vegetation
   carries most of the measured cooling. Raw canopy~heat is still negative
   (SR −0.64, Bak −0.24). This supports REDTEAM objection 1 and bounds how hard
   "trees cool" can be stated. Contra Costa's within-zone (detrended) heat~canopy
   is −0.44, *stronger* than the NDVI −0.15 that justified heat=0 — worth
   revisiting whether heat deserves some weight in the CC score (not changed).

> ## Branch: `san-ramon`
>
> This branch retargets the whole engine at **San Ramon, California** — 419 populated hexes
> at H3 res 9, 85,569 residents, all data freshly built. `master` (Los Angeles)
> is untouched: every data artefact here is suffixed `_sanramon`, so the two
> cities' files coexist instead of overwriting each other.
>
> **Everything below this box was written for the LA build.** The fixed-bug list
> still applies — it is about the front end, which is shared — but the numbers,
> the demo beats and the HOLC/redlining material are LA's. See README.md and
> DEMO.md on this branch for San Ramon's.
>
> ### What was actually built (all verified in the browser)
>
> | | |
> |---|---|
> | Hexes | 419 populated (122 with no housing dropped), res 9, ~0.11 km² each |
> | Coverage | the incorporated city, clipped to TIGERweb place GEOID 0668378 |
> | Population | **85,569** against a true ACS place total of **85,734** — 0.19% |
> | Hexes | 419 populated of 541 (122 with no housing, correctly dropped) |
> | Surface temp | 39.2–51.1 °C, median 45.8 |
> | Canopy proxy | 5.3–40.8%, median 20.9 |
> | Aged 65+ | 0–47.6%, median 11.8 (smoothed) |
> | Cooling sites | 25 — 12 community centres, 5 pools, 5 senior/shelter, 3 libraries |
> | Walk to relief | 0–46 min, median 14 |
> | corr(LST, canopy) | **−0.800**, −0.808 detrended (LA was −0.61) |
> | corr(income, priority) | **−0.02** — no income gradient; see Phase 10 |
> | #1 hex | Valencia S — 46.9 °C, 12.9% canopy, 925 people, 8.6% aged 65+ |
>
> ### Phase 10 — the population was wrong, and so was the headline

Two independent problems, found by checking rather than by reasoning. Both are
fixed; the second is a lesson about this project's failure mode.

**1. Area weighting manufactured residents.** `03_census.py` split each block
group's population across hexes by AREA. At LA's res 8 (0.82 km²) that is a fair
areal-interpolation assumption. At San Ramon's res 9 (0.11 km²) it is not: **57
of 540 hexes held ≥50 "residents" each while containing zero residential
buildings** — 5,850 people, 6.9% of the city, placed on golf courses, ridgelines
and the Bishop Ranch office park. One empty hex ranked **#10**. Population is a
multiplier in the score, so those hexes were promoted, and a planner sent to look
at one would find a hillside.

Fixed with dasymetric refinement — new `pipeline/02b_buildings.py` pulls OSM
residential footprints and `03_census.py` splits block groups by residential
**floor area** instead of ground area. Three subtleties, each of which produced a
visibly wrong total before it was right:

  - the **denominator** must be the whole block group including the part outside
    the grid, or partly-covered block groups assign all their residents to their
    in-city half (this gave 108,178 people);
  - the **numerator** must be clipped to the city limits, because hexes are kept
    if they *intersect* the boundary and so overhang into Danville and Dublin
    (unclipped: 92,395; clipped both ends wrongly: 96,801);
  - the buildings query must run **wider than the bbox** (`MARGIN_DEG = 0.09`),
    because 17 of the 61 block groups touching San Ramon extend past it and their
    missing houses shrink the denominator (this was most of a 2.7% overcount).

Result: **85,569 vs a true ACS place total of 85,734 — 0.19%.** Zero hexes now
have population without housing. The ACS reconciliation check in `03_census.py`
is what caught every one of these; keep it.

**2. The headline finding was false.** The branch claimed heat inequity in San
Ramon "tracks housing type — apartment complexes like Fairway Village and Amador
Lakes." Tested against 26,346 OSM building footprints: `corr(priority,
multi-family floor share) = +0.08`, and the median top-10 hex is **0%**
multi-family. The claim came from hex **names** — "Fairway Village Apartments SE"
is named for the nearest landmark and contains 4% apartment floor area. The
follow-up hypothesis (newer subdivisions) also failed: ACS B25035 median year
built gives `r = +0.02`.

What is actually true, and now what the app says:

  - `corr(LST, canopy) = −0.80`, **−0.808 after removing a quadratic spatial
    trend** — a real shade effect, stronger than LA's −0.61;
  - `corr(income, priority) = −0.02`. Canopy by income quartile: 21.5 / 22.6 /
    21.7 / 20.4%. **There is no heat-equity gradient in San Ramon.** The app is
    reframed as canopy targeting and says so on the landing screen;
  - geography carries what is left: 8 of the top 10 hexes are in Dougherty
    Valley (east of Dougherty Rd), 19.8% vs 22.6% canopy, t = −4.8.

**This is the third claim of this shape to ship wrong** (after the LA A/C swap
and Holmby Hills). The pattern is always the same: a plausible story written from
names or intuition, never tested. **Any claim about what the ranking "tracks"
must be a measured correlation before it goes in copy.**

### The City has already asked for this — CAP Measure CS-1

San Ramon's Draft Climate Action Plan (10 April 2025, prepared by Rincon Consultants;
Planning Services contact listed as Ryan Driscoll, Associate Planner) contains **Measure
CS-1**, whose actions map almost exactly onto what this branch does:

  - **CS-1b** — conduct a Tree Canopy assessment "including identifying areas with below
    average canopy coverage"; set "a goal of having no significant difference in canopy
    coverage between census blocks in the community".
  - **CS-1c** — prioritise planting "in areas with populations most at risk to extreme heat
    impacts (e.g., older adults …)".
  - **CS-1d** — a Tree Trust for "selected communities with below average tree canopy
    coverage", plus USDA / California ReLeaf / Urban and Community Forestry grant applications.
  - **CS-1e** — publish "an interactive map showing the results of the tree canopy assessment
    along with areas identified for new tree canopy".

`BRIEF.md` now leads with this rather than pitching cold. **The honesty limit matters here:**
CS-1b asks for a canopy assessment *and a tree inventory*, and this delivers neither — it is a
satellite vegetation proxy, which is exactly what REDTEAM objection 1 is about. The brief says
"first pass, to scope or cross-check yours", never "this satisfies CS-1b". Do not let that
slide.

### Deployed — two cities, one site

Live at **<https://advikar.github.io/coolequity/>**: a chooser at the root, Los
Angeles at `/app/`, San Ramon at `/sanramon/app/`.

GitHub Pages serves exactly one branch, so it now serves **`gh-pages`, which is a
build, not a source branch** — assembled from `master` and `san-ramon` by
`./deploy.sh`. Consequences worth knowing:

  - **Pushing to `master` or `san-ramon` no longer updates the site.** Run
    `./deploy.sh` after any change you want published.
  - **Never edit `gh-pages` by hand**; the next deploy force-pushes over it.
  - **LA keeps the exact paths it had** when Pages pointed at `master`, so any
    link already shared still resolves. Do not move `/app/`.
  - Only the three data files each app fetches are copied. The pipeline's
    rasters, the 16 MB building footprints and every CSV stay out of the site.
  - The root chooser lives at `site/index.html` in the source tree, not in
    `gh-pages`, so it is version-controlled like everything else.

Verified over the wire after deploy: all nine URLs 200, the right city at each
path, the deployed San Ramon `index.html` byte-identical to the branch, and
`sanramon.geojson` arriving intact — 419 hexes, 85,569 residents, `street_m`
present.

### Phase 11 — audit, robustness, and the two documents for the City

Ran the outstanding audit steps rather than assuming they would pass.

**Top-12 hex audit — passes, with one flag.** Every top-12 hex has full raster coverage
(120–125 valid pixels), surface-temperature σ of 0.6–1.4 °C and a 90th-minus-median spread
under 2.8 °C, so **no ranking rests on a single hot pixel**. All have 43–188 real buildings
and 493–1,985 m of street frontage; parking and commercial coverage is ≤1.6%. Every one has a
*negative* vegetation anomaly against its neighbours (−1.0 to −11.8 pp), which is the expected
signature of a real canopy gap.

**⚠ Capella (#10) is flagged, not trusted.** +3.82 °C against its neighbour ring (citywide
95th percentile of |anomaly| is 1.87 °C), −11.8 pp vegetation, and 6.0 residents per mapped
building against a city median of 3.7. Needs ground-truth at 37.78122, −121.92628 before it is
presented to anyone.

**Resolution robustness — passes, and improves.** Rebuilt at res 8 (81 populated cells):
`corr(LST, canopy) = −0.837` against res 9's −0.800. The aggregate finding is not a
resolution artifact. But individual rankings are resolution-sensitive — of the 17 res-8 parents
holding the res-9 top 25, 11 are in the res-8 top quartile. **Present the list as a screen,
not as a precise ranking.**

**Irrigation confound — partly ruled out, and this is the weakest link.** Removing all mapped
parks, turf, golf and woodland moves `corr(LST, canopy)` from −0.800 to −0.799. But those
features are only ~6% of the city; most greenness here is private yard, unmapped in OSM, so
the test could not reach it. In a summer-dry climate NDVI separates *irrigated* from
*unirrigated* at least as sharply as *shaded* from *unshaded*. **A real canopy layer is the
one thing that would settle it** — see `REDTEAM.md` objection 1.

**Health validation data — does not exist at this geography.** California publishes
heat-illness ED rates at **county** level (Tracking California). ZIP-level records sit inside
HCAI behind a Limited Data Request. CalHeatScore scores every ZIP 0–4 but publishes only the
forecast, not the underlying historical rates. **No San Ramon-specific figure was found, and
county numbers must not be quoted as San Ramon's.**

**Two new documents.** `BRIEF.md` is the one-page analysis for the City's Sustainability
Division — headline, ten thinnest blocks, sources, three limitations, and a single ask (cross-
check against the City's own tree inventory). `REDTEAM.md` is the strongest case against our
own finding, ranked by severity. Both carry the Capella flag. Every figure in BRIEF.md was
generated from `data/sanramon.geojson` rather than typed; the claim that "five of the top 25"
exceed their frontage was written from intuition, checked, and corrected to nine.

### Four things that did NOT transfer from LA, and would fail quietly
>
> 1. **One summer is one Landsat scene here**, not twenty. `SUMMER_YEARS` is now
>    `(2022, 2023, 2024)` and `02_satellite.py` searches each summer separately
>    and concatenates — 9 Landsat, 11 Sentinel-2, same 20% cloud filter. **Never
>    replace this with a single continuous date range**: it would silently pull
>    January scenes into a "summer" thermal median.
> 2. **A/C access is weighted 0**, and this is the most important decision on the
>    branch. It is modelled from income percentile *within the city*; San Ramon's
>    block-group medians are $101,645–$250,001, so that transform would invent a
>    35–95% spread across a uniformly wealthy town and hand it 25% of the score.
>    Built and viewable, scored at zero. Weights are 45/33/22 (LA's 35/25/15
>    renormalised). Do not "fix" this by restoring 25%.
> 3. **No HOLC layer, by history not by bug.** San Ramon was farmland in 1935 and
>    incorporated in 1983. `HOLC_URL = None`, and the app hides the toggle when
>    no hex carries a grade (`syncHolcAvailable()`) and explains why.
> 4. **Hex names needed a new source.** Five OSM place nodes for 540 hexes gave
>    "Windemere NE 19". Now names come from the 90 named residential subdivision
>    polygons a hex falls *inside* (`NAME_FROM_LANDUSE`), nearest non-park anchor
>    otherwise. Parks are excluded from the proximity pass — 49 of them in 52 km²
>    otherwise win everywhere and produce "Piccadilly Square Park E 5".
>
> ### Two front-end bugs found and fixed while doing this
>
> - **`[hidden]` loses to any class rule that sets `display`.** `.toggle` sets
>   `display:flex`, so marking the HOLC toggle hidden did nothing and it stayed
>   on screen. Restated at class specificity: `.toggle[hidden],.hint[hidden]`.
> - **The population stat assumed millions.** `(pop/1e6).toFixed(1)+'M'` rendered
>   85,569 as "0.1M". Now switches units at a million.
>
> ### Resume here
>
> Pipeline is fully run and committed; `python3 -m http.server 8000` then
> `/app/` opens San Ramon. Not yet done: this branch is **not deployed** (Pages
> serves `master`), and the 60s screen capture is still unrecorded.

Resume point for a fresh session. Spec lives in `SPEC.md` (in-repo since Phase 6;
Section 10 of it is superseded by `DEMO.md`).

## Run it

```bash
cd coolequity
python3 -m http.server 8000       # then open http://localhost:8000/app/
```

Pipeline (venv already built at `.venv`), run from `pipeline/`:

```bash
../.venv/bin/python 01_make_grid.py
../.venv/bin/python 02_satellite.py      # --cached to skip the network
../.venv/bin/python 03_census.py
../.venv/bin/python 04_overlays.py       # --refresh to re-pull OSM/HOLC
../.venv/bin/python 05_score.py
```

Note the two flags are opposites on purpose. 02 goes live by default and
`--cached` forces the cache; 04 uses the cache by default and `--refresh` forces
live, because Overpass rate-limits and re-pulling 645 amenities on every tweak
is how you get 504'd an hour before the demo.

## Where we are

| Phase | State | Output |
|---|---|---|
| 0 Front end decoupled | done | `app/index.html` fetches `data/la.geojson` |
| 1 H3 grid | done | `data/grid.geojson` — 3486 res-8 hexes, 0.82 km² each |
| 2 Satellite LST + NDVI | done | `data/satellite.csv`, `data/{lst,ndvi}.tif` |
| 3 ACS census | done | `data/census.csv`, `data/acs.csv` |
| 4 Overlays | done | `data/overlays.csv`, `centers.geojson`, `holc_la.geojson`, `places.geojson` |
| 5 Score + rank | done | `data/la.geojson` — 3008 scored hexes, **app now on real data** |
| 6 Polish + demo | done bar the video | `README.md`, `DEMO.md`, `app/vendor/` |
| 7 Front-end rebuild | done | landing screen, live weights, ramp inversion, units |

Verified in the browser at 1440×860: priority, redlining and cooling-access
layers all render and the legend matches the map; ROI panel produces sane
numbers on the #1 hex. Re-verified after the Phase 6 edits, on both the CARTO
and the flat basemap paths — `?flat=1` shows **zero** off-host requests.

**The only thing left on the whole build is the 60s screen capture**, which is a
manual step; instructions are at the bottom of `DEMO.md`.

## Bugs already fixed — do not reintroduce

1. **`LAYERS['holc']` missing** → `setLayer('holc')` threw, redlining toggle dead.
2. **`#detail` had no `position`** → flowed as a third grid cell, halved the map.
3. **`AREA_M2` hardcoded to 5.16 km²** (a res-7 value). Real hexes are 0.82 km²;
   ROI overstated trees and cost by 6.3×. Now reads per-hex `area_m2`.
4. **UI init gated on `map.on('load')`** → blank screen on a slow CDN. Panel now
   renders from data first.
5. **Basemap fallback keyed on `map.on('load')`** — `load` waits on the first
   render, so a backgrounded tab (rAF suspended) is indistinguishable from a dead
   CDN, and the fallback tore down a working map. Now probes the style URL directly.
   **Never key a fallback on `load`.**
6. **Sentinel-2 BOA offset** — baseline ≥04.00 carries `BOA_ADD_OFFSET = -1000`
   that Planetary Computer does not pre-apply. It does *not* cancel in a ratio.
   Without it NDVI maxed at 0.50 instead of 0.79.
7. **NDVI clamp** — spec's 0.20–0.80 floored 40.5% of hexes at 0% green.
   Now 0.05–0.65 (physical endpoints, must stay absolute — canopy % feeds ROI).
8. **Overpass `out center tags`** — the `tags` verbosity prints ids and tags and
   **drops coordinates**, including on plain nodes. Every element parsed fine and
   then had nowhere to go, so the place-name query silently returned zero
   features. Use `out center`. `check_coords()` now hard-fails instead of
   silently dropping.
9. **Data layers added on `map.on('load')`** — bug 5 one level deeper, and the
   lesson had not been carried across. Measured: a tab opened in the background
   reports `document.hidden=true`, `map.loaded()=false` *forever*, and presents a
   blank map when you switch to it. `isStyleLoaded()` never settles either.
   Sources and layers are now **baked into the style object before the map is
   constructed**, so no event is involved at all.
10. **`fitBounds` padding larger than the container** → throws
    `Invalid LngLat object: (Infinity, NaN)`. Thrown inside `boot()`'s promise
    chain it took down the whole map and reported it as "could not load
    la.geojson", sending you to debug the wrong layer. `fitData()` clamps padding
    and defers on a zero-sized container; the catch handler now distinguishes
    "data failed" from "map failed".
11. **MapLibre loaded from unpkg** — the risk register's whole answer to "venue
    Wi-Fi dies" is *"app + all data are static/local"*, and a `<script src=unpkg>`
    quietly made that false. With no network `maplibregl` is undefined and the map
    never gets as far as the basemap fallback that was built for exactly this.
    Now vendored at `app/vendor/` (v4.7.1, BSD-3; its CSS inlines every icon as a
    `data:` URI, so nothing else leaks out). **Audit the whole page for off-host
    requests, not just the ones you wrote a fallback for.**
12. **`setLayer` gated on `map.getLayer('fill')`** — `getLayer()` returns
    undefined until the style parses, so a layer toggled during the basemap fetch
    updated the legend, chip and caption while the map kept the old ramp. **The
    legend silently lying about the map is the worst failure mode here.**
    `paintFill()` retries on `styledata`. **Generalised in Phase 7 to
    `styleOp()`** — the centre filter and the selection ring were both still
    behind `if(map.getLayer(id))`, i.e. the same bug in two more places. Route
    every style mutation through `styleOp`, and never through `getLayer`.
13. **`rgbOf()` digit-scraped its argument** — it only ever worked on `ramp()`'s
    `rgb(r,g,b)` output. Fed a raw `#rrggbb` from the ramp arrays it failed
    *plausibly*: `#b30000` → `rgb(NaN)`, `#5c3a17` → `[5,3,17]` → a grey that
    looked like a design choice, so every weight swatch and slider thumb was
    silently grey. Branch on the leading `#`. **A colour helper that accepts two
    notations has to test both.**
14. **Mercator y in radians against longitude in degrees** (intro backdrop) —
    the raw log-tangent is 57.3× too small, so LA drew as a 60 px horizontal
    smear rather than a city. Multiply by `180/π`. Any hand-rolled projection
    needs both axes in the same units.

## Phase 7 — the front-end rebuild

Driven by "it doesn't feel hackathon-winning": the map worked but the model was
invisible, the colours argued the opposite of the thesis, and there was no way
in other than being dropped on a map.

- **Ramps inverted, basemap lit.** One rule, stated in the legend under the bar
  with an arrow at the correct end: *deeper = more need*. The two protective
  inputs (canopy, A/C) ramp deep→pale so the arrow flips rather than the meaning.
  This forced CARTO **positron** — over dark-matter the deep end is the least
  visible ink on screen. The two changes only work together. `?flat=1`'s flat
  background is now light to match.
- **The four weights are live sliders.** Not a rebuild of the model — the same
  model. Verified in-page against the committed `la.geojson` at the shipped
  weights: **max 0.156 points, mean 0.039, pipeline ranks #1–#6 exact.** The
  residual is the geojson storing lst/green/ac at 1 dp. The pipeline's `score`
  and `rank` properties are never overwritten, so Reset is exact.
- The map repaints from a **MapLibre expression** that recomputes the score over
  the raw properties. Not `setData` — that re-serialises 1.4 MB per frame of a
  drag.
- **The legend caption for Priority is generated from the weights in force**, so
  the "keep config.py and the legend copy in sync" hazard below is retired for
  that layer. It is now impossible for the caption to quote 35% while the slider
  says 60%.
- Detail panel shows the **score arithmetic term by term** — measured value,
  position on the city's 0–1 scale, × weight, = points, then the population
  multiplier.
- **Cooling sites are classified** by the `kind` already in `centers.geojson`
  (library 212, community centre 200, pool 133, senior/shelter 100), each with a
  colour, a count read *from the file*, a plain-English definition and its own
  filter. Clicking one names it.
- **Landing screen** with a city picker. Only LA is built and the UI says so —
  the other cities are labelled *pipeline-ready* and show the actual build steps.
  A dropdown that appeared to load Delhi would be the worst thing in this repo.
  Backdrop is the real hex layer drawn to a canvas from the same geometry.
  `?go=1` (and any `?data=`) skips straight to the map.
- **Metric/imperial switch**, display-layer only. `fTemp` and `fTempD` are
  separate on purpose: a *drop* of 0.36 °C is 0.65 °F, not 32.65 °F.
- **Inter + Instrument Serif vendored** at `app/vendor/*.woff2` (latin subsets,
  63 KB, both OFL 1.1). Not a Google Fonts `<link>` — see fixed bug 11.

## Open issues / decisions taken

- **`corr(LST, green)` — RESOLVED, and it is negative.** The +0.091 across all
  3486 hexes was entirely the 478 uninhabited ones (ocean reads 18.4 °C with zero
  vegetation). Across the 3008 populated hexes **r = −0.606**, and it holds
  inside every longitude band (−0.35 to −0.69), so it is not LA's coastal
  gradient. Partial correlation after removing a quadratic lon/lat trend is
  **−0.577**. The "shade cools" narrative is safe to say out loud.
- **478 uninhabited hexes — DROPPED** (`config.MIN_POP`). Justified above: they
  invert the headline correlation and stretch the heat ramp over a range no
  inhabited hex occupies. The map now has honest holes over the bay, Griffith
  Park and the Sepulveda Basin.
- **`pct65` degenerate shares — FIXED** by empirical-Bayes shrinkage toward the
  citywide rate with a 100-person pseudo-count (`config.AGE65_SHRINK_POP`). Raw
  max was 100% (a 4-person hex); smoothed max is 47.4%, median 15.2%. A
  5,000-person hex keeps 98% of its own weight. Without it the Age-65 ramp was
  set by a 4-person artefact and went flat.
- **Hex names — DONE, from OSM place nodes**, not a US neighborhood file, so the
  same code names hexes in Lagos or Delhi. 308 place nodes → nearest-node join,
  with a compass suffix to keep the ranked list unique ("Westlake S",
  "Koreatown SE"). 1450 of 3008 need a numeric suffix too, but those are
  low-density mountain hexes that rank last; the dense core reads well.
- **Walk time is a circuity-adjusted straight line, not a route.** `CIRCUITY =
  1.273` = 4/π, the exact expected Manhattan-to-Euclidean ratio over uniform
  bearings — the penalty for a perfect street grid, which is close to what LA is.
  A real osmnx walk graph over this 3,400 km² bbox is millions of nodes and tens
  of minutes of Overpass download; that does not belong on a demo's critical
  path. **Say "estimated walking minutes", never imply it is routed.**
- Population totals 6.48M vs the county's 9.85M — expected, the bbox covers the
  LA basin, not Antelope Valley. Visible as a hard straight edge on the east side
  of the hex layer around El Monte / Whittier. Not a bug; know it before a judge
  points at it.

## Phase 6 — what was done

1. **The two false claims in spec Section 10 are corrected**, in the spec itself
   (with a "superseded, rehearse from DEMO.md" banner) and in the new `DEMO.md`,
   which is now the rehearsal doc. The real table:

   | HOLC | hexes | mean LST | mean green | mean walk | mean score |
   |---|---|---|---|---|---|
   | A | 136 | 38.7 °C | 26.0% | 20.3 min | 24.4 |
   | B | 200 | 42.7 °C | 18.5% | 14.3 min | 38.4 |
   | C | 450 | 45.1 °C | 12.2% | 13.2 min | 52.0 |
   | D | 260 | 45.4 °C |  9.4% | 12.2 min | 54.1 |

   A→D gap is **+6.7 °C**, not ~10. And D areas are **closer** to relief
   (12.2 vs 20.3 min), not twice as far — dense inner-city blocks have libraries;
   A-graded areas are leafy low-density suburbs. Reframed in `DEMO.md` as
   "redlining shows up here as heat and missing canopy, not as distance."
2. **Real ROI numbers are in the closing beat** (hex #1, Westlake S): canopy
   3% → 15%, −0.36 °C, 15,759 residents, 1,797 aged 65+, ~2,470 trees over
   0.82 km², ≈ $1.2M, $78/resident. Re-verified against the live app, not just
   recomputed from the geojson.
3. **The repo now genuinely runs with no network** — see fixed bug 11. Confirmed
   by counting off-host requests in the page: 0 on `?flat=1`, and on the normal
   path the only ones are CARTO's own basemap assets. `data/_cache/` stays
   gitignored; it is pipeline scratch, nothing the app reads.
4. **`README.md` written** — run instructions, pipeline order, score and ROI
   formulas, provenance, and an explicit "what's estimated" section.

## Phase 8 — presets, city search, and two bugs the UI was telling on itself

1. **Landing screen names the product** and the city chips became a type-to-search
   combobox over 20 cities. `have` on a `CITIES` entry is still the only thing
   that decides whether the CTA opens a dataset, so the list can grow without
   ever implying data exists. Enter/Escape inside the field are stopped from
   bubbling to the global handler that launches the map.
2. **Weights lead with six presets**; the four sliders and the normalisation
   explainer moved behind an "Adjust the weights yourself" disclosure.
3. **Fixed: "changing the weights changes nothing."** Not a wiring bug — the
   weights are renormalised to 100%, so dragging one input to the old slider
   ceiling of 60 landed near 40% once the other three rescaled. Enough to swap
   two adjacent hexes, not enough to look like an effect. Presets set all four at
   once; the ceiling also went 60 → 100. Verified: *Protect seniors* moves
   Westlake S #1 → #5 and Holmby Hills ~2,100th → 27th.
4. **Fixed: ROI "residents cooled" looked dead.** It printed the hex's whole
   population regardless of the slider, including at the minimum where cost is
   $0 and cooling is 0.00 °C. Now 0 until there is planting to price. Beat 4's
   numbers at 15% are unchanged ($1.2M, $78/resident, −0.36 °C, 2,470 trees).
5. **Caught in review:** the *Protect seniors* preset copy first claimed it makes
   Holmby Hills #1. It is #27 there; #1 needs a pure 100% age weighting. Copy,
   README and DEMO.md all now state the true figures. Any claim of this shape
   must be re-checked against `LIVE.rank` before it ships — the model moved.

## Phase 9 — legibility, provenance, and a fifth weight

1. **Every ramp's pale end now starts darker than the basemap.** They were
   lighter than `#eceff3`, so a low hex read as a hole rather than as a hexagon
   — worst on Population, where most of the basin disappeared. Priority's low
   third is still deliberately quiet (that is bug-12 era design, keep it); it is
   just no longer invisible. The legend bar is generated from the same arrays via
   `rampStops()`, so it cannot disagree — verified: legend stop 0 and
   `colorFor('pop', min)` are both `rgb(219,228,238)`.
2. **ROI provenance on screen** (`#roi-src`): WRI for the cooling coefficient,
   40 m² per crown, and $500/tree explicitly labelled a *planning assumption*,
   not a quote. Never let the dollar figure ship unsourced again.
3. **Copy**: "incl. aged 65+" → "of them aged 65+"; cooling-site descriptions
   rewritten flat (they were writing punchlines).
4. **Home button** in the panel header. It *reloads* rather than re-inserting the
   overlay — the intro is built once from HEX/CENTERS during `boot()`, and a
   second construction path is a second thing to keep correct. Keeps `?flat=1`,
   drops `?go`/`?data`.
5. **Landing screen names tree canopy** as the lever, plus a
   population-weighted "canopy over the average resident" stat (12% in LA).
   Footer carries a unit-aware scale note read off `area_m2` (0.82 km²).
6. **Fifth weight, `access`, shipped at 0.** `config.py` weights four things and
   the parity claim against `la.geojson` depends on reproducing exactly those
   four — a non-zero default would make "Pipeline default" a lie. `normW()` and
   `matchPreset()` now fold over `W_INPUTS`, so a sixth input is one array entry.
   `W_INPUTS` entries take an optional `show` formatter (minutes are not %).
7. **Caught in review, again:** the new *No relief nearby* preset's copy claimed
   it pulls the answer outward to the far blocks. False — top-50 mean walk time
   moves only 8.8 → 9.1 min and the top ten is unchanged, because the population
   multiplier keeps the dense core in front. True figure: 722 of 3,008 hexes move
   >100 places, all mid-list. **That is two of two such claims wrong on first
   write. Verify against `LIVE.rank` before any of them ships.**
8. The legend now states that the score is a *ranking within this city*, not an
   absolute hazard level, and points at the Surface temperature layer for
   absolute values. That is the honest answer to "if the whole city were
   freezing, everything should be low priority".

Verified in-browser at each step: console clean (the two `layer 'fill' does not
exist` errors seen during testing were from an injected test script — stack
frames read `<anonymous>`, not `index.html`), Westlake S ROI unchanged at 15%
($1.2M · $78/resident · −0.36 °C · 2,470 trees · 15,759 residents · 1,797 aged
65+), ROI zeroes correctly at the hex's own canopy, breakdown renders
"Far from relief | 8 min | 0.03 × 0.00 | 0.000".

9. **Landing card no longer clips its own title.** `#intro` centred with
   `align-items:center` + `overflow:hidden`, which clips a too-tall card at BOTH
   ends — and the end that matters is the top, so the wordmark disappeared the
   moment the card grew past the viewport (979px against a 720px window). Now
   `margin:auto` on `.intro-card` with `overflow-y:auto` on `#intro`: centred
   when it fits, scrollable from its own top when it does not. Plus a
   short-window ladder at 860/740/640px that tightens type and spacing so it
   fits without scrolling on a laptop. **If you add copy to the landing screen,
   re-measure `.wordmark`'s `getBoundingClientRect().top` afterwards** — it must
   be positive. This is the second time the title went missing this way.
10. **Cooling relief sites is now a disclosure**, same pattern as the weights
    panel: count in the header, `Show the four categories` beneath it, detail
    collapsed. The summary line reports hidden categories (`all on` / `1 hidden`)
    because collapsed it is the only thing saying what is filtered.
11. Landing stat labels are deliberately short (`neighborhoods`, `residents`,
    `hottest block`, `avg. canopy`, `cooling sites`) so all five fit one row at
    760px. A fifth stat orphaned onto a second line reads as a bug.

README.md and DEMO.md are updated for Phases 8 and 9: seven presets, the fifth
weight at zero, the cost-provenance answer, the "your scale is relative"
objection, the ramp darkening, and the home button.

### Deployed

Live at <https://advikar.github.io/coolequity/> (Pages, `master`, root path).
Verified after the first build: the deployed `app/index.html` is byte-identical
to the local file, `data/la.geojson` serves as 1.39 MB `application/geo+json`,
and the vendored MapLibre and the root redirect both return 200. Publishing is
just a `git push` now — there is no build step to forget.

**Still open:** the 60s screen capture (steps at the bottom of DEMO.md) is still
unrecorded — it is the fallback if the laptop dies and someone else presents.
Ranks #1 and #2 both display `100` in the list because scores round to 0 dp
(100.0 and 99.5); cosmetic, untouched.

### Phase 7 browser verification — all clear

Everything in Phase 7 has now been checked in a real browser: console clean,
layer toggles confirmed to repaint the map via `queryRenderedFeatures` and not
just the legend, live model checked against `la.geojson`, units checked
including the temperature *delta*. The two items that had landed after the
previous browser pass were closed on the pass after that:

1. **The intro canvas backdrop is a city, not a band.** The `180/π` fix for
   fixed bug 14 renders correctly. Measured off the canvas pixels rather than
   eyeballed, because the smear it replaced was only ~60px tall and a thumbnail
   would not have settled it: ink spans 99.9% of canvas height and 85% of its
   width, and the left edge of the ink marches from x=0.16 at the top to x=0.69
   at the bottom — that diagonal is the LA coastline running NW→SE. A regression
   would flatten `vertFrac` toward zero. Re-measure with:

   ```js
   (()=>{const c=document.getElementById('intro-canvas'),g=c.getContext('2d');
     const d=g.getImageData(0,0,c.width,c.height).data;
     let minY=1e9,maxY=-1;
     for(let y=0;y<c.height;y+=2)for(let x=0;x<c.width;x+=2)
       if(d[(y*c.width+x)*4+3]>8){if(y<minY)minY=y;if(y>maxY)maxY=y;}
     return {vertFrac:+((maxY-minY)/c.height).toFixed(3)};})()   // expect ~0.999
   ```

2. **`?flat=1` makes zero off-host requests** — confirmed in the Network tab, not
   just statically audited. Every request is `localhost:8000`, a `data:` URI, or
   the MapLibre worker `blob:`. The flat path also *draws*: hexes plus the county
   outline, no basemap. That property is the whole answer to "what if the venue
   Wi-Fi dies", so re-check it in the Network tab after any change that touches
   `basemapStyle()` or adds an asset.

**A blank map screenshot during this pass was fixed bug 9 again, not a
regression.** The Browser pane backgrounds its tabs, `document.hidden` goes
true, rAF is suspended and the WebGL framebuffer is never repainted before
capture — while `queryRenderedFeatures({layers:['fill']})` returned 3,084. Trust
that query over a screenshot; front the tab (click into it) before believing a
blank frame.

Revert path if any of Phase 7 is unwanted: `git checkout pre-redesign -- app/`
(tag `pre-redesign` is the last pre-rebuild commit).

### Still open

- **Record the 60s screen capture.** Manual; steps at the bottom of `DEMO.md`.
  It covers the failure vendoring doesn't: this laptop dying and someone else
  having to present.
- Stretch goals in spec Section 11 (city selector, budget optimizer, CSV export)
  are untouched and remain optional.

## Contract between pipeline and front end

Hex properties the app reads. Renaming any of these breaks the UI:

```
id  name  lst  green  pop  pct65  ac  holc  access_min  access_km  score  rank  area_m2
```

`holc` is legitimately `null` outside the 1939 map (1962 of 3008 hexes) — the
fill expression's `match` default handles it.

Score weights live in `pipeline/config.py` and are mirrored in the app's
`DEFAULT_W` / `DEFAULT_POPW`. **Those two must stay in sync** — that is the whole
basis of the "reproduces the pipeline" claim, and the check is one line in the
console:

```js
HEX.features.reduce((m,f)=>Math.max(m,Math.abs(sc(f.properties)-f.properties.score)),0)
// expect < 0.2 with the sliders at their defaults
```

The legend *copy* no longer needs syncing: it is generated from the weights in
force.

## Notes

- `.env` holds `CENSUS_API_KEY`, gitignored, mode 600, never committed.
- Satellite path is Planetary Computer (anonymous). No Earth Engine account needed.
- Overpass mirrors are tried in order with backoff; `overpass.kumi.systems` leads
  because the main instance throttles hardest.
- `?data=<name>` on the app URL swaps the hex file (e.g. `?data=grid`). Implies
  `?go=1`.
- `?go=1` opens straight onto the map, skipping the landing screen. Use it for
  rehearsal and for the recorded walkthrough.
- `?flat=1` forces the flat basemap, so the no-network look is rehearsable
  without actually killing the Wi-Fi. The county outline is drawn only on that
  path — over CARTO's streets it is clutter, over nothing it is the only thing
  telling you the holes over the bay are holes.
- The app needs ~700px of width before the map column is usable; below that the
  366px panel eats the grid. Fine for a projector, worth knowing on a laptop.
- Nothing off-host except CARTO's basemap: MapLibre, both typefaces and all data
  are local. Re-audit with `?flat=1` after any front-end change — that path must
  stay at **zero** external requests.


## September 7, 2026 — Contra Costa UI and evidence guide

Implemented the user's review in the contra-costa working tree: persistent help, a dedicated
17-topic searchable Data & methods page, contextual links, collapsed score decomposition,
street-capacity planting scenarios, removal of irrelevant redlining content, keyboard ranked
rows, mobile layout and accurate model/estimate labels. See `UI_REVIEW.md` for candid review,
`FEATURES.md` for the current UI contract and `DATA_QUALITY.md` for accuracy corrections.
Validation: `node tests/ui-contract.cjs`; desktop and mobile browser checks. No source-data
rerun, no ranking weight change, no public deployment in this pass. Deployment script reads
committed city branches; do not run it expecting to include uncommitted guide files.


## September 7, 2026 — benefits-led guide and deeper source audit

Rewrote guide around city uses and method-choice rationale, compacted essential notes, made
info rings smaller, added all-residential-area search/pagination, semantic facility filters,
startup storage protection, safe HTML names and failure recovery. Source audit found 430
residential NDVI fallbacks and 866 inconsistent canopy-area rows. Added green_src export and
source-aware labels/scenario guards; preserved all prior data values/ranks. Retired mixed-source
canopy headline pending recheck. `PRODUCT_READINESS.md` records research and proposed upgrades.
Analytical rebuilds, latest ACS integration, local assumptions and public deployment remain pending.

## September 7, 2026 — first analytical rebuild completed

Contra Costa only: canopy rasters rebuilt and atomic fallback fixed (866 area inconsistencies
to zero); coverage/source flags and 99% aerial scenario gate; ACS 2024/native MOEs and housing
LACE weighting; matched live/export ordinal ranks; separate public greenness index; secondary
air cooling display. 2,697 ranked areas, 24/25 top-25 overlap. Five pipeline tests and 11,436
scenario cases pass; all residential ranks reproduce in browser scorer. Reports and manifest
in reports/. Official facilities, local planting validation, uncertainty propagation and public
deployment remain pending.

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

### Verification complete — September 8, 2026

Contra Costa branch: seven Python tests, 11,436 scenario checks, JavaScript/guide contract checks, and git whitespace checks passed. Browser checks covered a partial-canopy scenario and the searchable county directory; final directory styling was visually verified. FEATURES.md and DATA_QUALITY.md reflect the current behavior. Work is uncommitted and unpublished; the remaining production-readiness work listed above is still open.
