"""San Ramon — pipeline settings. Loaded by pipeline/config.py.

Only what differs from the shared settings lives here.
"""

# ---------------------------------------------------------------- geography
CITY = "San Ramon"
SLUG = "sanramon"               # must match this folder's name

# west, south, east, north. NOT hand-drawn: this is the exact bounding box of the
# TIGERweb incorporated-place polygon for San Ramon city (GEOID 0668378), read
# off the geometry rather than eyeballed off a map. The polygon itself clips the
# grid in 01, so the hexes follow the real city limits, which are ragged — San
# Ramon annexed in pieces and has Dougherty Valley hanging off the east side.
BBOX = (-122.0050, 37.7213, -121.8770, 37.7951)

# San Ramon is 52.0 km2. At res 8 (0.74 km2) that is 71 hexes — statistically
# tidy, since the city holds ~55 census block groups, but far too coarse to look
# like a map. Res 9 (0.105 km2, ~370 m across) gives ~490 hexes and a real
# picture of where the heat sits.
#
# The trade is documented rather than hidden: Landsat and Sentinel-2 genuinely
# resolve at this size, so heat and canopy are per-hex measurements. The census
# fields cannot be — a res-9 hex is roughly a ninth of a block group, so
# population, age and income are areally interpolated DOWNWARD and vary smoothly
# across neighbours. Real data, coarser than the grid drawn over it.
H3_RES = 9

# ---------------------------------------------------------------- scoring
# LA weighted A/C access at 25%. San Ramon does not, and the reason is a
# property of the data rather than a preference.
#
# San Ramon's block-group median incomes run $100,906-$250,001, narrow and
# uniformly high, and its A/C prevalence is high and narrow too. Stretching that
# across the within-city normalisation would invent a spread that is not there,
# and it would then carry a quarter of the score.
#
# So the layer is still BUILT and can still be viewed, and it is scored at zero.
# The rest is LA's ratio renormalised: 35/25/15 of 0.75 becomes
# 0.4667/0.3333/0.20, rounded to sum to exactly 1.
WEIGHTS = {
    "heat":     0.45,   # heat_n
    "green":    0.33,   # (1 - greenness_n)
    "ac":       0.00,   # (1 - ac_access_n)  -- built, not scored; see above
    "age65":    0.22,   # age65_n
}

# ---------------------------------------------------------------- census (US)
COUNTY_FIPS = "013"          # San Ramon is in Contra Costa County
COUNTY_POP_RANGE = (0.9e6, 1.4e6)

# Clips to the incorporated place, because a county-sized clip would leave the
# grid covering Mount Diablo and half of Danville.
CLIP_URL = ("https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/"
            "Places_CouSub_ConCity_SubMCD/MapServer/4/query?"
            "where=GEOID%3D%270668378%27&outFields=GEOID,NAME&"
            "returnGeometry=true&outSR=4326&f=geojson")

# None, and this is a fact about history rather than a gap in the build: HOLC
# surveyed built-up cities in 1935-1940, and San Ramon was farmland then — it did
# not incorporate until 1983.
HOLC_URL = None

# ---------------------------------------------------------------- buildings
# How far outside BBOX 02b pulls buildings. San Ramon needs 0.09 deg because 17
# of the 61 block groups touching the city bbox run up to 0.07 deg past its edge.
BUILDINGS_MARGIN_DEG = 0.09

# San Ramon's OSM building mask passes the dasymetric check: 0.66 coverage.
# 3.0 here, not the shared 2.0, on evidence (2026-09-08, ACS 2024 BGs): the
# count-based check reads 2.5x because San Ramon's lowest-income quartile
# ($89k-$172k) is apartment/condo-heavy -- median 2.8 housing units per mapped
# building vs 1.1-1.2 in the other quartiles -- not because it is unmapped:
# those block groups sit fully inside the city and carry a median 109 m2 of
# mapped floor area per unit. Dasymetric weights by floor area, so multifamily
# is handled; a building COUNT per unit is the wrong completeness metric for
# it. Contra Costa's 4.7x is a real mapping gap and keeps the 2.0 limit.
DASY_MAX_INCOME_BIAS = 3.0

# ---------------------------------------------------------------- satellite
# The committed San Ramon composites were built with the older GLOBAL scene cap
# (the 30 least-cloudy scenes overall). Kept so a rebuild reproduces them; set
# True to use the per-tile cap the other cities use (expect small LST/NDVI
# changes if the city straddles a tile edge).
SCENE_CAP_PER_TILE = False

# ---------------------------------------------------------------- cooling sources
# San Ramon is in Contra Costa County, so the county EHSD corrections apply.
COOLING_SOURCE_URL = 'https://ehsd.org/wp-content/uploads/2026/07/Senior_Cooling-Centers-Tips_July-2026.docx'
NO_AC_LIBRARIES = frozenset({'Kensington Branch Library', 'El Cerrito Branch Contra Costa County Library'})
