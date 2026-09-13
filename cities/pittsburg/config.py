"""Pittsburg and Bay Point — pipeline settings. Loaded by pipeline/config.py.

Only what differs from the shared settings lives here.

The study area is the city of Pittsburg plus the unincorporated Bay Point CDP
next to it, on the east side of Contra Costa County. It was chosen from the
county build: at the county's recommended weights Pittsburg holds 10 of the
county's 100 highest-need areas and Bay Point 5, and the two are one contiguous
built-up area sharing the same delta-edge climate. A city-scale grid (res 9,
0.1 km2) resolves that where the county grid (0.74 km2) cannot.
"""

# ---------------------------------------------------------------- geography
CITY = "Pittsburg & Bay Point"
SLUG = "pittsburg"              # must match this folder's name

# west, south, east, north: bounds of the union of the two TIGERweb place
# polygons (Pittsburg city, GEOID 0657456, layer 4; Bay Point CDP, GEOID
# 0604415, layer 5 of Places_CouSub_ConCity_SubMCD), read off the geometry. The
# union itself is committed as data/boundary_pittsburg.geojson and clips the
# grid in 01.
BBOX = (-122.0066, 37.9830, -121.8332, 38.0561)

# Res 9 (~0.1 km2, ~370 m across), as in the other city-scale builds.
H3_RES = 9

# ---------------------------------------------------------------- scoring
# HEAT IS NOT SCORED here, as in the county build this area was cut from, and
# the reason is a measurement made on this build's own cells, not a preference.
# Among residential cells with summer surface temperature above 35 C (570 of
# 739, i.e. the built-up area, marsh and water set aside) position (lon, lat)
# still explains 28% of the variance in surface temperature, against 39%
# county-wide and 11% in West Contra Costa: the north-south gradient from the
# Suisun shoreline into the hills is most of the heat signal. And heat does not
# track missing shade here: LST correlates +0.23 with aerial canopy among those
# cells (the newer hillside subdivisions are both hotter and greener than the
# older flat neighbourhoods near the shore). Scoring heat would therefore
# reward distance from the water, not lack of trees. Heat stays measured,
# displayed and movable, at weight 0, and the county's weights apply.
#
# A/C is scored: Census LACE 2023 runs 69-96% of homes across the area, so the
# input carries real signal (unlike Bakersfield and San Ramon).
WEIGHTS = {
    "heat":     0.00,   # heat_n — built, viewable, NOT scored (see above)
    "green":    0.55,   # (1 - canopy_n)
    "ac":       0.25,   # (1 - ac_access_n)
    "age65":    0.20,   # age65_n
}

# ---------------------------------------------------------------- census (US)
COUNTY_FIPS = "013"          # Contra Costa County
COUNTY_POP_RANGE = (0.9e6, 1.4e6)

# 01 reads the committed boundary file first (data/boundary_pittsburg.geojson).
# This URL is the network fallback: Pittsburg city alone, so a rebuild without
# the file still clips to land in the right place rather than to the county.
CLIP_URL = ("https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/"
            "Places_CouSub_ConCity_SubMCD/MapServer/4/query?"
            "where=GEOID%3D%270657456%27&outFields=GEOID,NAME&"
            "returnGeometry=true&outSR=4326&f=geojson")

HOLC_URL = None              # Mapping Inequality has no 1930s map of Pittsburg

# ---------------------------------------------------------------- buildings
# Block groups along the shoreline and the city line run past the bbox.
BUILDINGS_MARGIN_DEG = 0.09

# ---------------------------------------------------------------- cooling sources
# Inside Contra Costa County, so the county EHSD directory and its corrections
# apply. The two libraries the county lists as lacking A/C are in West County,
# not here; the set is kept so the county rule is applied uniformly.
COOLING_SOURCE_URL = 'https://ehsd.org/wp-content/uploads/2026/07/Senior_Cooling-Centers-Tips_July-2026.docx'
NO_AC_LIBRARIES = frozenset({'Kensington Branch Library', 'El Cerrito Branch Contra Costa County Library'})
