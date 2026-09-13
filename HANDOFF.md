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
