"""Contra Costa County — pipeline settings. Loaded by pipeline/config.py.

Only what differs from the shared settings lives here.
"""

# ---------------------------------------------------------------- geography
CITY = "Contra Costa County"
SLUG = "contracosta"            # must match this folder's name

# west, south, east, north. Derived from the county's own block groups' bounds,
# so every block group is inside it by construction. The county polygon clips the
# grid in 01.
BBOX = (-122.4301, 37.7185, -121.5342, 38.0999)

# Res 8 (~0.74 km2 per hex): a county is ~2,000 km2, so res 8 already gives
# ~2,900 cells, in line with how many block groups the census resolves here.
H3_RES = 8

# ---------------------------------------------------------------- scoring
# HEAT IS BUILT BUT NOT SCORED HERE. That is the opposite of the other builds
# and it is the most important decision for this county, so the reasoning is
# written out rather than assumed.
#
# The score normalises each input min-max WITHIN the study area. That works when
# the study area is one climate, which a city is and a county this shape is not.
# Contra Costa runs from the Richmond shoreline to the Delta: mean summer LST is
# 36.8 C in the west and 43.1 C in the east, and 38.8% of ALL variance in surface
# temperature is explained by longitude and latitude alone. Normalising across
# that ranks Richmond's 41 C against Antioch's 52 C as though a resident of each
# experiences them the same way.
#
# The consequence is measurable. In San Ramon corr(LST, canopy) = -0.800, and
# -0.808 after detrending: shade demonstrably cools. Here it is -0.120, -0.149
# detrended, and by longitude band it swings from +0.381 to -0.092. There is no
# consistent shade effect to score at this scale. Weighting it 35% would have
# put the heaviest weight in the model on the input carrying the least signal.
#
# So heat keeps its layer, its legend and its per-hex numbers -- all measured,
# all real -- and carries zero weight, exactly as A/C access does in San Ramon.
# What remains is a canopy-deficit model: where is tree cover thinnest, weighted
# by how many people live under it and how vulnerable they are.
#
# A/C access IS scored here. Contra Costa's 674 block groups with income run
# $18,071 to $250,001, p10 $69,526, median $128,142, p90 $240,586 -- a real
# gradient. A/C is now the Census LACE 2023 estimate (see app/index.html notes);
# the income model survives only as a per-tract fallback.
#
# NOTE ON CIRCULARITY: measured A/C prevalence still correlates with income, so
# the canopy-equity finding is computed on RAW MEASURED CANOPY against income,
# with no score involved. Keep it that way.
WEIGHTS = {
    "heat":     0.00,   # built, viewable, NOT scored — see above
    "green":    0.55,   # (1 - greenness_n)   the model's centre of gravity
    "ac":       0.25,   # (1 - ac_access_n)
    "age65":    0.20,   # age65_n
}

# ---------------------------------------------------------------- census (US)
COUNTY_FIPS = "013"          # Contra Costa County
# Sanity band for the county-wide ACS total, checked at the end of 03 (~1.16M).
COUNTY_POP_RANGE = (0.9e6, 1.4e6)

# County polygon, not a place polygon. GEOID 06013 is Contra Costa County.
CLIP_URL = ("https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/"
            "State_County/MapServer/13/query?"
            "where=GEOID%3D%2706013%27&outFields=GEOID,NAME&"
            "returnGeometry=true&outSR=4326&f=geojson")

# No HOLC map covers Contra Costa in any useful way. Checked against Mapping
# Inequality directly rather than assumed: the East Bay 1937 survey is an
# Oakland/Berkeley map, and only 8 of its 120 polygons touch this county — all
# graded A, B or C, with NO D grades at all. Turning the layer on would draw a
# sliver over El Cerrito and imply a redlining story the data cannot support.
HOLC_URL = None

# ---------------------------------------------------------------- buildings
# How far outside BBOX 02b pulls buildings. 03 divides a block group's residents
# by that block group's TOTAL housing, so a block group straddling the bbox edge
# needs its outside houses counted. Here BBOX comes from the county's own block
# groups, so the margin only has to cover geometry slop. (The county's building
# mask fails the dasymetric check anyway — see DASY_* in pipeline/config.py.)
BUILDINGS_MARGIN_DEG = 0.02

# ---------------------------------------------------------------- cooling sources
COOLING_SOURCE_URL = 'https://ehsd.org/wp-content/uploads/2026/07/Senior_Cooling-Centers-Tips_July-2026.docx'
# The June 2026 EHSD revision explicitly identifies these libraries as lacking A/C.
# Exact name + kind avoids excluding unrelated facilities in the same city.
NO_AC_LIBRARIES = frozenset({'Kensington Branch Library', 'El Cerrito Branch Contra Costa County Library'})
