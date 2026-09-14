# HANDOFF

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
  In a browser, each city on https://advikar.github.io/coolequity-app/ was loaded next to the
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
