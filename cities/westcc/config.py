"""West Contra Costa — pipeline settings. Loaded by pipeline/config.py.

Only what differs from the shared settings lives here.

The study area is the west side of Contra Costa County: the cities of Richmond,
San Pablo, El Cerrito, Pinole and Hercules plus the unincorporated places between
and around them (North Richmond, El Sobrante, Rodeo, Crockett, Kensington, Tara
Hills, Montalvin Manor, Rollingwood, Bayview, East Richmond Heights, Port Costa).
It was chosen from the county build: at the county's recommended weights these
places hold 60 of the county's 100 highest-need areas, and Richmond alone has
92% of its residents in areas under 10% tree cover. A city-scale grid (res 9,
0.1 km2) resolves that where the county grid (0.74 km2) cannot.
"""

# ---------------------------------------------------------------- geography
CITY = "West Contra Costa"
SLUG = "westcc"                 # must match this folder's name

# west, south, east, north: bounds of the union of the 16 TIGERweb place
# polygons listed above (5 incorporated places from layer 4, 11 CDPs from layer
# 5 of Places_CouSub_ConCity_SubMCD), read off the geometry. The union itself is
# committed as data/boundary_westcc.geojson and clips the grid in 01.
BBOX = (-122.4415, 37.8837, -122.1789, 38.0733)

# Res 9 (~0.1 km2, ~370 m across), as in San Ramon and Bakersfield: heat and
# canopy resolve per hex; census fields interpolate downward from block groups.
H3_RES = 9

# ---------------------------------------------------------------- scoring
# HEAT IS SCORED here, unlike the county build this area was cut from, and the
# reason is a measurement, not a preference. County-wide, position (lon, lat)
# explains 38.8% of the variance in summer surface temperature: comparing the
# Richmond shoreline to Antioch is comparing climates. Inside West County the
# same regression explains 11.1% (1,494 land hexes, LST 27-49 C), and LST
# correlates -0.64 with satellite greenness: a hotter hex here is mostly a
# barer hex, which is the signal a shade-planting screen wants. Heat therefore
# carries the weight it does in the other city-scale builds.
#
# A/C is scored: Census LACE 2023 runs 46-82% of homes across this area, the
# widest spread of any build, so the input carries real signal.
WEIGHTS = {
    "heat":     0.35,   # heat_n
    "green":    0.35,   # (1 - canopy_n)
    "ac":       0.15,   # (1 - ac_access_n)
    "age65":    0.15,   # age65_n
}

# ---------------------------------------------------------------- census (US)
COUNTY_FIPS = "013"          # Contra Costa County
COUNTY_POP_RANGE = (0.9e6, 1.4e6)

# 01 reads the committed boundary file first (data/boundary_westcc.geojson, the
# union of the 16 places). This URL is the network fallback: Richmond city alone,
# which is the largest piece, so a rebuild without the file still clips to land
# in the right place rather than to the whole county.
CLIP_URL = ("https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/"
            "Places_CouSub_ConCity_SubMCD/MapServer/4/query?"
            "where=GEOID%3D%270660620%27&outFields=GEOID,NAME&"
            "returnGeometry=true&outSR=4326&f=geojson")

# Set below once the Mapping Inequality coverage of Richmond is confirmed.
HOLC_URL = None

# ---------------------------------------------------------------- buildings
# Block groups along the shoreline and the county line run past the bbox.
BUILDINGS_MARGIN_DEG = 0.09

# ---------------------------------------------------------------- cooling sources
# Inside Contra Costa County, so the county EHSD directory and its corrections
# apply. The two libraries the county lists as lacking A/C are both in this
# study area, which is exactly why the exclusion exists.
COOLING_SOURCE_URL = 'https://ehsd.org/wp-content/uploads/2026/07/Senior_Cooling-Centers-Tips_July-2026.docx'
NO_AC_LIBRARIES = frozenset({'Kensington Branch Library', 'El Cerrito Branch Contra Costa County Library'})
