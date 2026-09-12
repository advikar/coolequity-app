# HANDOFF

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
- **Open, pre-existing (also on the old site):** the tab's saved state uses the sessionStorage
  key `ce-session` for every city, so switching city in the same tab carries the previous
  city's weights and layer into the next one (shown as "Your own mix"). Scoping the key by
  `CITY_SLUG` in app/index.html would fix it; not changed in the migration.
