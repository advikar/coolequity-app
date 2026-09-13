# CoolEquity

**Where would new street trees help residents most?** A planning screen that scores every
neighborhood area of a city on surface heat, tree cover, population, age, home air conditioning
and the walk to a cool place, then sizes a street-planting scenario. Exploratory, not a field
survey; every number carries its source and limits in each city's in-app guide.

**Live:** <https://advikar.github.io/coolequity-app/>

| City | Map | Areas ranked | Residents | Tree cover | A/C | Heat weight |
|---|---|---|---|---|---|---|
| Contra Costa County | [contracosta/app/](https://advikar.github.io/coolequity-app/contracosta/app/) | 2,697 | 1.16M | USFS/CAL FIRE 2022 aerial; greenness stand-in on 131 areas (aerial assessment under 10%); 2009–2020 height model on 1330 | Census LACE 2023, scored | 0 |
| Bakersfield | [bakersfield/app/](https://advikar.github.io/coolequity-app/bakersfield/app/) | 3,767 | 410k | USFS/CAL FIRE 2022 aerial | LACE 2023, not scored (96.5–100% everywhere) | 0.45 |
| San Ramon | [sanramon/app/](https://advikar.github.io/coolequity-app/sanramon/app/) | 419 | 85k | USFS/CAL FIRE 2022 aerial | LACE 2023, not scored | 0.45 |
| West Contra Costa | [westcc/app/](https://advikar.github.io/coolequity-app/westcc/app/) | 982 | 272k | USFS/CAL FIRE 2022 aerial | LACE 2023, scored | 0.35 |
| Pittsburg & Bay Point | [pittsburg/app/](https://advikar.github.io/coolequity-app/pittsburg/app/) | 570 | 90k | USFS/CAL FIRE 2022 aerial; greenness stand-in on 16 areas; 2009–2020 height model on 52 | LACE 2023, scored | 0 (shown, not scored: tracks distance from the shore) |

All four share one app, one pipeline and one method: ACS 2020–2024 population and age
allocated into H3 areas, Landsat 8/9 surface temperature, walking time routed on the
OpenStreetMap pedestrian network, planting scenarios conditional on mapped street capacity,
a data & methods guide, the county cooling directory and reproducible scenario export.

This repository replaces the per-city branches of
[advikar/coolequity](https://github.com/advikar/coolequity), which stays as it was (including
the legacy Los Angeles build on its `master` branch, not carried over here).

## Layout

```
app/                 the map page, shared by every city
  index.html           map, ranking, scenarios, export (reads city.js for its settings)
  cities.js            the list of cities, for the city switchers
  guide.css, guide.js  styling and behaviour of the guide pages
  vendor/              MapLibre and both typefaces, so nothing loads from a CDN
cities/<slug>/       everything that differs by city
  config.py            pipeline settings: bbox, grid resolution, weights, census county, …
  city.js              map settings: the same weights, presets, wording
  guide.html           data & methods guide (city-specific sources and numbers)
  cooling.html         the county's published cooling directory
  data/                pipeline inputs and outputs; the map reads three of these
  reports/             rebuild audit output (pipeline/06_audit_rebuild.py)
  STATUS.md, README.md history of that city's build, carried over from its branch
pipeline/            the data pipeline, shared; the city is chosen by COOLEQUITY_CITY
site/index.html      the chooser page at the site root
scripts/
  build_site.py        assembles dist/ exactly as GitHub Pages serves it
  test.sh              every check, for every city
tests/               map contract (Node) and data contracts (Python)
docs/archive/        project brief, spec, reviews and the pitch deck, kept for reference
```

The weights exist twice on purpose, once in `config.py` for the pipeline and once in `city.js`
for the browser, each beside the reasoning for it. `tests/ui-contract.cjs` fails if they
disagree, and checks that the browser's live ranking reproduces the pipeline's rank for every
residential area of every city.

## Run it

```bash
python3 scripts/build_site.py --serve     # then open http://localhost:8000/
```

The build copies files and generates nothing, so what you run is what deploys. The app works
with no network: without internet you lose only the CARTO street basemap, and the map falls
back to a flat background with the outline drawn in (rehearse with `?flat=1`).

URL switches on a city map: `?go=1` skips the landing screen; `?data=<name>` swaps the hex file
and implies `?go=1`.

## Test

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
scripts/test.sh                  # all cities; or: scripts/test.sh bakersfield
```

## Deploy

Push to `main`. [The workflow](.github/workflows/pages.yml) runs `scripts/test.sh` for every
city and publishes `dist/` to GitHub Pages only if every check passes. There is no deploy
script and no `gh-pages` branch. Pages caches for about 10 minutes, so hard-refresh.

## Rebuild a city's data

Only needed when changing the pipeline or refreshing sources; the committed outputs are
complete.

```bash
echo "CENSUS_API_KEY=..." > .env && chmod 600 .env    # api.census.gov/data/key_signup.html
export COOLEQUITY_CITY=bakersfield
.venv/bin/python pipeline/01_make_grid.py
.venv/bin/python pipeline/02_satellite.py              # --cached: use the committed rasters
.venv/bin/python pipeline/02b_buildings.py             # --refresh: re-pull footprints
.venv/bin/python pipeline/02c_canopy.py
.venv/bin/python pipeline/02d_canopy_usfs.py
.venv/bin/python pipeline/02e_worldcover.py
.venv/bin/python pipeline/03_census.py
.venv/bin/python pipeline/04_overlays.py               # --refresh: force a live Overpass pull
.venv/bin/python pipeline/04b_routed_access.py
.venv/bin/python pipeline/04c_designated_cooling.py    # county cooling list -> map points (Nominatim)
.venv/bin/python pipeline/05_score.py
.venv/bin/python pipeline/05b_stability.py            # rank bands: census margins + weight jitter, 300 draws
.venv/bin/python pipeline/06_audit_rebuild.py --baseline <dir with the previous outputs>
```

Two inputs are downloaded by hand and are not in the repository:

- **Census LACE 2023** (A/C prevalence by tract): put `LACE_23_Tract.csv` at
  `cities/<slug>/data/_cache/ac_src/LACE_23_Tract.csv`. `03_census.py` stops if it is missing;
  set `COOLEQUITY_ALLOW_INCOME_MODEL=1` to knowingly fall back to the income model instead.
- **USFS/CAL FIRE 2022 canopy** rasters: see the docstring of `02d_canopy_usfs.py` for the
  download and where to place the zips.

Each step's docstring states its inputs, outputs and fallbacks. `03_census.py` decides for
itself whether the OSM building mask is complete and unbiased enough to place residents with,
and says loudly which mode it used: it refuses on Contra Costa County and accepts on San Ramon.

Two settings keep a rebuild reproducible against the committed data rather than making every
city identical: San Ramon sets `SCENE_CAP_PER_TILE = False` (its composites were made with the
older global scene cap) and `DASY_MAX_INCOME_BIAS = 3.0` (evidence in its `config.py`).

## Add a city

1. Copy a similar city's folder under `cities/`, rename it to the new slug, and set every value
   in its `config.py` (the loader refuses to run if a required one is missing or `SLUG` does not
   match the folder).
2. Run the pipeline with `COOLEQUITY_CITY=<slug>`.
3. Set `city.js` to the same weights, and rewrite `guide.html` and `cooling.html` for the city.
4. Add the city to `app/cities.js`, its card to `site/index.html`, and its expected counts to
   `EXPECT` in `tests/ui-contract.cjs` and the directory table in `tests/test_data_pipeline.py`.
5. `scripts/test.sh`, then push.

## Limits

An independent student project, not a city or county product, and not reviewed by any city or
county. Scores are relative within one city; they are not health-risk probabilities or
cross-city rankings. Tree counts and costs are planning assumptions, not quotes. Mapped cooling
locations are not verified as open or air-conditioned; call before visiting.
