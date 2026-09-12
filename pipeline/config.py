"""Shared pipeline settings, plus the settings of the city being built.

Every pipeline step reads from here. The city is chosen with the COOLEQUITY_CITY
environment variable, which names a folder under cities/:

    COOLEQUITY_CITY=bakersfield python pipeline/05_score.py

cities/<slug>/config.py holds everything that differs between cities (name,
bounding box, grid resolution, score weights, census county, clip polygon and
the local cooling-source corrections), each with the evidence for its value.
This file holds what every city shares; a city file may override any of it.
Adding a city means adding a folder, never forking this code.
"""
import importlib.util
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CITIES_DIR = ROOT / "cities"
CITY_IDS = sorted(p.name for p in CITIES_DIR.iterdir() if (p / "config.py").exists())

CITY_ID = os.environ.get("COOLEQUITY_CITY", "")
if CITY_ID not in CITY_IDS:
    raise SystemExit(
        f"Set COOLEQUITY_CITY to one of: {', '.join(CITY_IDS)} "
        f"(got {CITY_ID!r}). Example: COOLEQUITY_CITY=contracosta python pipeline/05_score.py")

COUNTRY = "USA"                 # gates the US-only layers (HOLC, ACS)

# ---------------------------------------------------------------- scoring
# WEIGHTS live in each city's config.py: the right mix is a property of that
# city's data (a county spanning two climates cannot score heat; a uniformly
# wealthy town cannot score A/C), so there is deliberately no shared default.
# app/index.html reads the same weights from cities/<slug>/city.js, and
# tests/ui-contract.cjs fails if the two disagree.
#
# priority = base_risk * (POP_FLOOR + POP_WEIGHT * population_n)
POP_FLOOR = 0.55
POP_WEIGHT = 0.45

# Hexes with no residents — open ocean, national forest — are dropped before
# scoring. They are not just clutter: sea surface reads 18.4 C against a 51.9 C
# urban max, so leaving them in stretches the heat normalisation over a range no
# inhabited hex occupies. They also invert the headline correlation — across all
# 3,486 hexes corr(LST, greenness) is +0.09, but across the 3,008 populated ones
# it is -0.61 (and -0.58 after removing a quadratic spatial trend, so it is a
# real shade effect and not LA's coastal gradient).
MIN_POP = 1.0

# Share-aged-65 is a ratio, so a hex holding 4 people can read 100% elderly.
# Shrink each hex's rate toward the citywide rate with a pseudo-count of this
# many people (empirical Bayes): a 4-person hex at 100% lands near the city
# mean, while a 5,000-person hex keeps 98% of its own weight. Without it the
# Age-65 layer's colour ramp is set by a 4-person artefact and goes flat.
AGE65_SHRINK_POP = 100.0

# ---------------------------------------------------------------- satellite
# Summer window — LST is only meaningful at peak heat.
#
# LA composited one summer because one summer was plenty: 20 Landsat scenes
# cleared the 20% cloud filter over the basin. Over San Ramon's much smaller
# footprint, summer 2023 yields exactly ONE — and a single scene is not a median,
# it is one afternoon, with whatever haze and whatever synoptic weather that day
# happened to bring.
#
# So the window is three summers rather than one, at the SAME strict cloud
# filter: 2022-2024 gives 35 Landsat and 60 Sentinel-2 scenes. Loosening the
# cloud threshold instead (11 scenes at <50%) would have bought quantity with
# quality, which is the wrong trade for a thermal median.
#
# These are summer months in each year, never a continuous 2022-2024 range —
# 02 searches each year separately and concatenates. A straight range would pull
# in January scenes and quietly turn "peak summer surface temperature" into an
# annual mean.
SUMMER_YEARS = (2022, 2023, 2024)
SUMMER_MMDD = ("06-01", "09-15")
MAX_CLOUD_PCT = 20

# Metric CRS for raster work. UTM 10N; every current build used it, including
# Bakersfield (which sits in 11N) — zonal means in any projected CRS avoid the
# lat/lon pixel anisotropy, so a city file only needs to override this for a
# study area far outside zone 10.
RASTER_CRS = "EPSG:32610"
# 30 m, not LA's 100 m: a res-9 hex is ~370 m across, so at 100 m it would hold
# only ~10 pixels and the zonal mean would be noise. 30 m is Landsat thermal's
# native grid and gives ~115 px/hex over an area this small.
RASTER_RES_M = 30
MAX_SCENES = 30             # cap per collection so a demo build stays bounded

# NDVI -> vegetation-cover-% proxy: clamp, then scale linearly to 0..CANOPY_MAX.
#
# Endpoints are physical, not percentile-based: NDVI ~0.05 is the bare-soil/paved
# threshold and ~0.65 is dense healthy canopy in this composite (observed p99 =
# 0.67). They must stay absolute because canopy % feeds the ROI tree count — a
# relative stretch would make a desert city look as green as a forest one.
#
# The spec's 0.20-0.80 was calibrated for wetter imagery: against LA's dry-summer
# median NDVI of 0.24 it floored 40% of hexes at exactly 0% green, flattening the
# layer and pinning the ROI slider. 0.05-0.65 gives a citywide median of ~14%,
# consistent with LA's published ~21% tree canopy for a dry-summer composite.
NDVI_CLAMP = (0.05, 0.65)
CANOPY_MAX_PCT = 45.0

# ---------------------------------------------------------------- census (US)
ACS_YEAR = 2024
STATE_FIPS = "06"
# COUNTY_FIPS, COUNTY_POP_RANGE and CLIP_URL are per city.

# A/C access is MODELED from an income percentile — there is no A/C census.
# It is only a per-tract fallback now; Census LACE 2023 is the primary source.
AC_PCT_MIN = 35.0
AC_PCT_MAX = 95.0

# ---------------------------------------------------------------- overlays (04)
# Mapping Inequality (Univ. of Richmond) digitised HOLC "residential security"
# maps. US-only — COUNTRY gates this layer off everywhere else. None turns the
# layer off end to end rather than colouring a city with somebody else's grades;
# none of the current cities has a usable HOLC map (see each city's config.py).
HOLC_URL = None
# A hex must be at least this covered by graded polygons before it inherits a
# grade. The 1939 map stops at the then-built-up city, so most of the San
# Fernando Valley is genuinely ungraded; without a floor, a hex that merely
# clips a boundary would be coloured as if it were redlined.
HOLC_MIN_COVER = 0.25

# Public Overpass instances, tried in order. The main one throttles hard on a
# demo day, so the mirror leads.
OVERPASS_MIRRORS = (
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass-api.de/api/interpreter",
    "https://overpass.private.coffee/api/interpreter",
)
# A demo reads the ranked list aloud, so hex names have to be names a resident
# would recognise. LA had enough OSM place nodes to do that on its own; San Ramon
# has FIVE for 541 hexes, which produces "Windemere NE 19" and tells nobody
# anything. It does, however, have 90 named residential subdivisions mapped as
# landuse polygons — Canyon Lakes, Gale Ranch, Bent Creek Estates — which are
# exactly the names people use. With this on, 04 also pulls those (and named
# parks, which anchor the non-residential hexes) and names a hex after the
# polygon it falls INSIDE, falling back to the nearest anchor.
#
# Off for LA, whose committed places.geojson is place nodes only and whose names
# are already good.
NAME_FROM_LANDUSE = True

OVERPASS_TIMEOUT_S = 180
OVERPASS_ROUNDS = 3          # passes over the mirror list before giving up
OVERPASS_BACKOFF_S = 45      # pause between passes — a 504 usually means us

# ---------------------------------------------------------------- intervention
# Front end mirrors these; keep them in sync with app/index.html.
TREE_CANOPY_M2 = 40      # ~40 m2 canopy per mature urban tree
COST_PER_TREE = 500      # planting + 3yr maintenance, USD
WALK_SPEED_KMH = 4.8     # walking pace for the access-time layer

# Straight-line distance under-states a walk, because nobody walks through
# buildings. 4/pi = 1.273 is the exact expected ratio of Manhattan to Euclidean
# distance over uniformly-distributed bearings — i.e. the penalty for a perfect
# street grid, which is very close to what most of LA is.
#
# This is the spec's documented fallback, and it is deliberately the primary
# method: a real osmnx walk graph over this 3,400 km2 bbox is millions of nodes
# and tens of minutes of Overpass download, which is not something to put on the
# critical path of a live demo. Say "circuity-adjusted straight line" out loud
# rather than implying it is routed.
CIRCUITY = 1.273

# --- when dasymetric placement is allowed at all -------------------------------
# Splitting a block group's residents by building floor area is only better than
# splitting by area if the building mask is COMPLETE and UNBIASED. OSM is neither,
# everywhere. Measured:
#
#   San Ramon         20,417 buildings / ~31k ACS housing units = 0.66 coverage
#                     -> USE IT (see cities/sanramon/config.py for its bias limit)
#   Contra Costa Co.  139,121 / 426,585 = 0.33 coverage, and coverage by income
#                     quartile runs 0.07 / 0.07 / 0.08 / 0.33 -- the richest
#                     quartile is mapped 4.7x better than the poorest  -> REFUSE
#
# The county case is the dangerous one and it is dangerous in a specific
# direction: population is a MULTIPLIER in the score, so concentrating residents
# into well-mapped areas would systematically demote poor neighbourhoods. An
# equity tool that under-ranks poverty because volunteers mapped Blackhawk more
# thoroughly than North Richmond is worse than useless.
#
# 03_census.py checks both numbers over the block groups touching the study area
# and falls back to area weighting if either fails. Do not raise these to force
# dasymetric on; fix the mask instead.
DASY_MIN_COVERAGE = 0.50     # mapped buildings per ACS housing unit, study-wide
DASY_MAX_INCOME_BIAS = 2.0   # richest-quartile coverage / poorest-quartile

# ---------------------------------------------------------------- satellite scenes
# 02 caps scenes PER SATELLITE TILE by default (see search() in 02_satellite.py):
# a global cap starved most of Contra Costa's tiles. A city file can set this
# False to reproduce a build made with the older global cap.
SCENE_CAP_PER_TILE = True

# ---------------------------------------------------------------- cooling sources
# Source-specific corrections to the OSM discovery inventory (cooling_sources.py).
COOLING_SOURCE_URL = None
NO_AC_LIBRARIES = frozenset()

# ---------------------------------------------------------------- the city
# Load cities/<slug>/config.py and let it set or override any UPPERCASE name.
_spec = importlib.util.spec_from_file_location(
    f"coolequity_city_{CITY_ID}", CITIES_DIR / CITY_ID / "config.py")
_city = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_city)
for _name in dir(_city):
    if _name.isupper():
        globals()[_name] = getattr(_city, _name)
for _required in ("CITY", "SLUG", "BBOX", "H3_RES", "WEIGHTS", "COUNTY_FIPS",
                  "COUNTY_POP_RANGE", "CLIP_URL", "BUILDINGS_MARGIN_DEG"):
    if _required not in globals():
        raise SystemExit(f"cities/{CITY_ID}/config.py must set {_required}")
if SLUG != CITY_ID:
    raise SystemExit(f"cities/{CITY_ID}/config.py sets SLUG={SLUG!r}; it must match the folder")

# ---------------------------------------------------------------- paths
CITY_DIR = CITIES_DIR / SLUG
DATA = CITY_DIR / "data"
REPORTS = CITY_DIR / "reports"
CACHE = DATA / "_cache"          # gitignored intermediates (big rasters)

# Every artefact still carries the city SLUG in its name, so a file copied out of
# its folder can never be mistaken for another city's.
GRID_FILE = DATA / f"grid_{SLUG}.geojson"        # 01 -> 02
OUT_FILE = DATA / f"{SLUG}.geojson"              # 05 -> the app
CENTERS_FILE = DATA / f"centers_{SLUG}.geojson"  # 04 -> the app
HOLC_FILE = DATA / f"holc_{SLUG}.geojson"        # 04 fallback (unused: HOLC_URL is None)
PLACES_FILE = DATA / f"places_{SLUG}.geojson"    # 04 fallback, committed (hex names)
BOUNDARY_FILE = DATA / f"boundary_{SLUG}.geojson"  # 01 clip polygon, committed
ACS_FILE = DATA / f"acs_{SLUG}.csv"              # 03 fallback, committed
# Residential building footprints, committed. 03 uses them to place people
# INSIDE a block group instead of smearing them evenly across its area.
BUILDINGS_FILE = DATA / f"buildings_{SLUG}.geojson"
# Plantable street centrelines, committed. 04 measures frontage per hex; the app
# turns that into how many street trees the city could actually put in.
STREETS_FILE = DATA / f"streets_{SLUG}.geojson"
# 02c -> 05: measured canopy, plantable right-of-way.
CANOPY_CSV = DATA / f"canopy_{SLUG}.csv"
# 02e -> 05: authoritative land cover (ESA WorldCover 2021, 10 m) for the
# undeveloped/empty hexes, replacing the lst/veg/canopy heuristic in classify_land.
WORLDCOVER_CSV = DATA / f"worldcover_{SLUG}.csv"

LST_TIF = DATA / f"lst_{SLUG}.tif"               # 02 composite cache, committed
NDVI_TIF = DATA / f"ndvi_{SLUG}.tif"             # 02 composite cache, committed
SAT_CSV = DATA / f"satellite_{SLUG}.csv"
CENSUS_CSV = DATA / f"census_{SLUG}.csv"
OVERLAYS_CSV = DATA / f"overlays_{SLUG}.csv"

DATA.mkdir(parents=True, exist_ok=True)
CACHE.mkdir(exist_ok=True)
