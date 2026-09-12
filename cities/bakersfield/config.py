"""Bakersfield — pipeline settings. Loaded by pipeline/config.py.

Only what differs from the shared settings lives here.
"""

# ---------------------------------------------------------------- geography
CITY = "Bakersfield"
SLUG = "bakersfield"            # must match this folder's name

# west, south, east, north: the bounding box of the incorporated city (TIGERweb
# place GEOID 0603526). The place polygon clips the grid in 01.
BBOX = (-119.2653, 35.1940, -118.7727, 35.4480)

# Res 9 (~0.1 km2, ~370 m across), as in San Ramon: city scale, so heat and
# canopy resolve per hex while census fields are interpolated downward.
H3_RES = 9

# ---------------------------------------------------------------- scoring
# Bakersfield scores all four inputs — the only build that does — and both of
# the reasons the other cities dropped one are absent here.
#
# HEAT counts. Contra Costa had to zero it because that county runs from the
# Richmond shoreline to the Delta and 38.8% of its surface-temperature variance
# was explained by position alone; comparing Richmond's 41 C to Antioch's 52 C
# on one scale was comparing climates. Bakersfield is one flat valley floor
# ~30 km across with no marine gradient, so within-city normalisation compares
# like with like. Measured range: 33.2-58.1 C, median 49.8 C.
#
# A/C ACCESS counts. San Ramon had to zero it because its block-group median
# incomes ran $100,906-$250,001. Kern's run $14,159-$250,001, with 42% of block
# groups under $60k. Note the Census LACE estimate is nearly uniform here
# (96.5-100% of occupied homes across ranked cells), so it carries little
# ranking signal; the "Canopy only" preset shows the answer without it.
WEIGHTS = {
    "heat":     0.35,   # heat_n
    "green":    0.25,   # (1 - canopy_n)
    "ac":       0.25,   # (1 - ac_access_n)
    "age65":    0.15,   # age65_n
}

# ---------------------------------------------------------------- census (US)
COUNTY_FIPS = "029"          # Kern County
COUNTY_POP_RANGE = (0.8e6, 1.1e6)

CLIP_URL = ("https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/"
            "Places_CouSub_ConCity_SubMCD/MapServer/4/query?"
            "where=GEOID%3D%270603526%27&outFields=GEOID,NAME&"
            "returnGeometry=true&outSR=4326&f=geojson")

HOLC_URL = None              # no digitised HOLC map for Bakersfield

# ---------------------------------------------------------------- buildings
# How far outside BBOX 02b pulls buildings. The bbox is the incorporated city,
# so keep San Ramon's generous margin. (No building file is committed for this
# build, so 03 uses area weighting.)
BUILDINGS_MARGIN_DEG = 0.09

# ---------------------------------------------------------------- cooling sources
# No documented exclusions yet: the Kern County cooling-center page lists
# county-run and independent centers but does not identify mapped discovery
# sites (libraries, pools, community centres) that lack A/C.
COOLING_SOURCE_URL = 'https://www.kerncounty.com/government/aging-adult-services/services/cooling-centers'
NO_AC_LIBRARIES = frozenset()
