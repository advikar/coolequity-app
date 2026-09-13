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
# Bakersfield scores heat, canopy and age. A/C is present, movable, and ships
# at 0 for the same reason San Ramon zeroed it (see below).
#
# HEAT counts. Contra Costa had to zero it because that county runs from the
# Richmond shoreline to the Delta and 38.8% of its surface-temperature variance
# was explained by position alone; comparing Richmond's 41 C to Antioch's 52 C
# on one scale was comparing climates. Bakersfield is one flat valley floor
# ~30 km across with no marine gradient, so within-city normalisation compares
# like with like. Measured range: 33.2-58.1 C, median 49.8 C.
#
# A/C ACCESS ships at 0. The Census LACE 2023 estimate is nearly uniform here
# (96.5-100% of occupied homes across ranked cells, median 99.8%). Min-max
# scaling would stretch that 3.5-point modelled spread to a full 0-1 term, so a
# non-zero weight would score model noise, not a housing difference. The input
# stays measured, displayed and movable; the "Homes without A/C" preset shows it.
WEIGHTS = {
    "heat":     0.45,   # heat_n
    "green":    0.35,   # (1 - canopy_n)
    "ac":       0.00,   # (1 - ac_access_n) — nearly uniform, see above
    "age65":    0.20,   # age65_n
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
