# CoolEquity — Real Build Prompt & Technical Spec

> Hand this document to a coding assistant, or follow it yourself. It specifies a **real, working** heat-equity mapper for a live hackathon demo. It is deliberately time-boxed and includes fallbacks so no single data dependency can sink the demo.

---

## 0. Role & operating instructions (for the coding agent)

You are an experienced geospatial + full-stack engineer. Build the project described below end to end. Optimize for a **working demo in ~6 hours**, not completeness. Rules:

1. **Ship a working slice early.** Get the map rendering from a *sample* GeoJSON in the first hour, then replace it with real data. Never leave the app in a non-running state.
2. **Every data layer must have a fallback.** If a live API (Earth Engine, Overpass, Census) is slow or blocked, fall back to a pre-downloaded file committed to the repo. The demo must run offline if the venue Wi-Fi dies.
3. **Label modeled data as estimates in the UI.** A/C access and any wealth-proxy field are modeled, not measured. Never present them as ground truth.
4. **Keep the front end a single static file** (`app/index.html`) that loads a static `data/la.geojson`. No backend server at demo time.
5. **Commit working checkpoints** after each phase.

---

## 1. Product & demo goal

**Product:** CoolEquity ranks a city's neighborhoods by heat-vulnerability — fusing surface heat, tree canopy, population, elderly share, and cooling access — and recommends where cooling investment (trees, cooling centers) returns the most. The analysis engine runs on **globally-available satellite data**, demonstrated on **Los Angeles**.

**Definition of done (demo):**
- Dark, interactive map of LA on an **H3 hex grid** driven by **real** data.
- Toggleable layers: Priority score, Surface heat, Greenness, Population, Age 65+, A/C access (est.).
- **Story overlays:** HOLC redlining (US-only), cooling-access gap, cooling-center markers.
- **Intervention ROI calculator:** pick a hex, simulate canopy increase → estimated cooling, people protected, rough cost.
- A 60–90s demo narrative that ends on "here's exactly where to act first, and the return."

---

## 2. Architecture

Two decoupled stages:

```
[ Stage A: Python data pipeline ]  --produces-->  data/la.geojson (+ centers.geojson)
        (run once, offline)                              |
                                                         v
[ Stage B: static front end ]  index.html loads the GeoJSON, renders + interacts
        (MapLibre GL, single file, no server)
```

This split is the whole point: the engine is geography-agnostic (swap the bounding box + city name and it runs anywhere), while the demo is one polished city.

**Unit of analysis:** H3 hexagons (res 8 ≈ 0.7 km² for city detail; res 7 ≈ 5 km² if you need fewer cells for performance). Hexes, not admin boundaries, so it works in any country.

---

## 3. Tech stack

- **Python 3.11**: `h3`, `geopandas`, `rasterio`, `rasterstats`, `shapely`, `numpy`, `pandas`, `requests`, `osmnx`, `networkx`. Optional: `earthengine-api` (LST/NDVI), `census` (ACS).
- **Front end**: MapLibre GL JS 4.x + CARTO dark-matter basemap (no token). Vanilla JS, single HTML file. (Reuse the existing `coolequity_v2.html` — it already implements the UI, layers, ROI calculator, and toggles; you are swapping mock data for real.)
- **Repo**: git, with `data/` holding both live-pulled and fallback files.

---

## 4. Data sources (real, with global equivalents)

| Layer | LA demo source | How | Global equivalent | Fallback |
|---|---|---|---|---|
| **Land surface temp** | Landsat 8/9 C2 L2 `ST_B10`, summer median | Google Earth Engine `reduceRegions` over hexes, or download a GeoTIFF and `rasterstats` | MODIS MOD11A2 / Landsat (global) | Pre-exported `data/lst.tif` committed to repo |
| **Greenness / canopy** | Sentinel-2 NDVI, summer median | GEE NDVI → mean per hex | Sentinel-2 / ESA WorldCover (global) | Pre-exported `data/ndvi.tif` |
| **Population** | ACS block-group pop (US) OR WorldPop 100 m | Area-weighted sum into hexes | **WorldPop** (global, 100 m) | `data/worldpop_la.tif` |
| **Age 65+** | ACS `B01001` (US) | Census API → % 65+ per block group → hex | WorldPop age-structured grids | `data/acs_age.csv` |
| **A/C access (est.)** | Modeled: ACS median income → normalized proxy | Census API | Meta Relative Wealth Index (global) | inline in `acs.csv` |
| **HOLC redlining** | Mapping Inequality (Univ. Richmond) LA GeoJSON | Spatial join grade to hex by majority overlap | *US-only — leave null elsewhere* | `data/holc_la.geojson` (commit it) |
| **Cooling centers** | LA County/City open data OR OSM amenities | Overpass query: `library`, `community_centre`, `public` pools | OSM (global, sparser) | `data/centers.geojson` |
| **Roads (access time)** | OSM drive/walk network | `osmnx` graph → nearest-center travel time | OSM (global) | straight-line haversine × speed |

**Pragmatic recommendation:** for a 6-hour build, use **Google Earth Engine** for LST + NDVI (fastest way to real satellite values without wrangling scenes), **ACS** for pop/age/income (real, easy for a US city), **Mapping Inequality** for HOLC, and **OSM/Overpass** for cooling centers. Pre-download every one of these into `data/` as a fallback the moment you have it.

---

## 5. Repo structure

```
coolequity/
├─ data/
│  ├─ la_hexes.geojson        # final output consumed by the app
│  ├─ centers.geojson
│  ├─ holc_la.geojson         # fallback
│  ├─ lst.tif / ndvi.tif      # fallback rasters (if not using GEE live)
│  └─ acs.csv                 # fallback pop/age/income
├─ pipeline/
│  ├─ 01_make_grid.py         # H3 hexes over LA bbox
│  ├─ 02_satellite.py         # LST + NDVI per hex (GEE or raster)
│  ├─ 03_census.py            # pop, age65, income proxy per hex
│  ├─ 04_overlays.py          # HOLC join + cooling centers + access time
│  ├─ 05_score.py             # composite score + rank → writes la_hexes.geojson
│  └─ config.py               # bbox, city name, H3 res, weights
├─ app/
│  └─ index.html              # the front end (from coolequity_v2.html)
├─ requirements.txt
└─ README.md                  # run instructions + data provenance
```

---

## 6. Phased build plan (time-boxed)

**Phase 0 — Skeleton (30 min max).** Repo, `requirements.txt`, drop in `coolequity_v2.html` as `app/index.html` pointed at a *sample* GeoJSON. Confirm it renders. Commit.

**Phase 1 — Grid (30 min max).** `01_make_grid.py`: generate H3 hexes covering the LA bbox (`config.py`), output hex geometries with an `id`. Verify count is sane (res 8 → ~1–2k hexes; drop to res 7 if the browser lags).

**Phase 2 — Satellite (90 min max).** `02_satellite.py`: LST + NDVI per hex.
- *Primary:* GEE — summer median of Landsat ST_B10 (convert to °C) and Sentinel-2 NDVI; `reduceRegions(hexes, mean)`.
- *Fallback:* download one GeoTIFF each, `rasterstats.zonal_stats(hexes, tif, stats="mean")`.
- Convert NDVI → a canopy-% proxy (e.g., clamp/scale NDVI 0.2–0.8 → 0–45%). Commit outputs.

**Phase 3 — Census (60 min max).** `03_census.py`: pull ACS block-group population, age 65+, median income for LA County; area-weight into hexes; derive A/C-access proxy from income (normalize, label est.). Cache to `acs.csv`.

**Phase 4 — Overlays (75 min max).** `04_overlays.py`:
- HOLC: load Mapping Inequality LA GeoJSON, assign each hex the majority-overlap grade.
- Cooling centers: Overpass query (libraries, community centres, public pools) → `centers.geojson`.
- Access time: build an `osmnx` walk graph, compute minutes from each hex centroid to nearest center; **fallback** = haversine ÷ 4.8 km/h.

**Phase 5 — Score (30 min max).** `05_score.py`: normalize each field, compute composite (Section 7), rank, write `la_hexes.geojson`. Repoint the app at it. Commit.

**Phase 6 — Polish + demo (45 min max).** Sanity-check the map, tune opacity/labels, verify redlining and ROI read well, rehearse the narrative (Section 10). Record a 60s screen capture as an ultimate fallback.

---

## 7. Composite score (must match the front end)

For each hex, min–max normalize each input across the city, then:

```
base_risk = 0.35 * heat_n
          + 0.25 * (1 - greenness_n)
          + 0.25 * (1 - ac_access_n)
          + 0.15 * age65_n                 # per-capita vulnerability, 0..1

priority  = base_risk * (0.55 + 0.45 * population_n)   # weight by people exposed
score     = 100 * minmax(priority across hexes)         # 0..100
rank      = dense rank of score, descending
```

Expose the weights in `config.py` so they're tunable and defensible. **Normalize within the city** (44°C is normal in Phoenix, alarming in Seattle) — this is what makes the score portable.

---

## 8. Intervention ROI calculator (front-end formula)

Already implemented in `coolequity_v2.html`; keep these assumptions and cite them:

```
delta_canopy = target_pct - current_green_pct        # percentage points, >= 0
temp_drop_C  = (delta_canopy / 10) * 0.3             # WRI: +10% canopy ≈ −0.3°C air temp
seniors      = population * pct65 / 100
trees        = delta_canopy/100 * hex_area_m2 / 40   # ~40 m² canopy per mature urban tree
cost         = trees * 500                            # ~$500/tree planted + 3yr maintenance
cost_person  = cost / population
```

Label all outputs "estimated." Cite: WRI, *Cooling Potential of Urban Trees* (each +10% canopy ≈ −0.3 °C); global 806-city study (~1.5 °C midday LST reduction). Pull `hex_area_m2` from `h3.cell_area()` rather than a constant when wiring real data.

---

## 9. Risk register & mitigations

| Risk | Mitigation |
|---|---|
| GEE auth/quota delays | Pre-export LST/NDVI GeoTIFFs to `data/`; pipeline auto-uses them if GEE import/auth fails |
| Overpass/OSM timeout | Commit `centers.geojson`; `osmnx` access falls back to haversine travel time |
| Census API key/rate limit | Cache `acs.csv`; pipeline reads cache if API errors |
| Too many hexes → laggy map | Config flag to drop H3 res 8→7; simplify geometries with `shapely` |
| Venue Wi-Fi dies | App + all data are static/local; record a 60s demo video as final fallback |
| Judge asks "vs WRI Cool Cities Lab?" | Answer: same validated approach; our edge is the **ROI calculator** + **cooling-access gap** framing and running on any city from satellite data alone |

---

## 10. Demo script (60–90s)

> **Superseded — rehearse from `coolequity/DEMO.md`, not from here.** This script
> was written before the data existed and two of its numbers did not survive it:
> the A→D heat gap is **+6.7 °C**, not ~10 °C, and D-graded areas are **closer**
> to cooling centres than A-graded ones (12.2 min vs 20.3), not twice as far.
> Both are corrected below, with the underlying table in `DEMO.md`.

1. **Hook (10s):** "Heat is the deadliest weather hazard — ~489,000 deaths a year — and it hits the poorest, least-shaded blocks hardest. Cities have cooling budgets but no precise way to target them."
2. **Map (15s):** Open on the Priority layer. "Every hex in LA, scored on real satellite heat, tree canopy, population, age, and cooling access."
3. **Story (20s):** Toggle **Redlining**. "The hottest, least-shaded areas map onto 1930s redlining — D-graded areas run **6.7 °C hotter** than A-graded ones today, with a third of the tree canopy: 9% vs 26%." Toggle **cooling-access gap** and reframe honestly: the redlined core is *closer* to relief (12.2 min vs 20.3) because it is dense inner city with libraries — redlining shows up here as heat and missing shade, not as distance.
4. **Decision (25s):** Click the #1 hex (Westlake S) → **ROI calculator**. Drag canopy up. "Raising canopy here from 3% to 15% — about 2,470 trees — cools afternoons an estimated 0.36 °C for 15,759 residents, 1,797 of them over 65, for roughly \$1.2M, or \$78 a resident."
5. **Close (10s):** "The engine runs on global satellite data — point it at any city on Earth. This is where to plant the first tree."

---

## 11. Stretch goals (only if ahead of schedule)

- **City selector** — dropdown that swaps bbox + reruns; prove "works anywhere" with a Global South city (Delhi/Lagos) using WorldPop + Sentinel-2 only.
- **Cost-optimizer** — given a budget, greedily pick the set of hexes maximizing people-cooled per dollar.
- **Export** — "download priority list as CSV" button for a city official.

---

## 12. Setup commands

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt        # h3 geopandas rasterio rasterstats shapely numpy pandas requests osmnx networkx earthengine-api census
# optional live data:
earthengine authenticate               # for GEE LST/NDVI
export CENSUS_API_KEY=...               # https://api.census.gov/data/key_signup.html
python pipeline/01_make_grid.py && python pipeline/02_satellite.py && \
python pipeline/03_census.py && python pipeline/04_overlays.py && python pipeline/05_score.py
# serve the app:
python -m http.server -d app 8000      # open http://localhost:8000
```

**Provenance to cite in README:** USGS/NASA Landsat & Copernicus Sentinel-2; WorldPop; US Census ACS; University of Richmond *Mapping Inequality*; OpenStreetMap contributors; WRI (tree-cooling coefficients).
