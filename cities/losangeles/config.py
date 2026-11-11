"""Los Angeles — pipeline settings. Loaded by pipeline/config.py.

Only what differs from the shared settings lives here.

The study area is the incorporated City of Los Angeles (TIGERweb place GEOID
0644000), not the basin: the legacy hackathon build on the old repository's
`master` branch drew a bounding box over the whole basin at res 8 with 2023
census and one summer of imagery. This build replaces it with the city limit,
the city-scale grid the other city builds use, and the sources below.
"""

# ---------------------------------------------------------------- geography
CITY = "Los Angeles"
SLUG = "losangeles"             # must match this folder's name

# west, south, east, north: the bounding box of the incorporated city, read off
# the TIGERweb place polygon (committed as data/boundary_losangeles.geojson,
# which clips the grid in 01). The box necessarily also covers Burbank,
# Glendale, Beverly Hills, West Hollywood, Culver City, Santa Monica, San
# Fernando, Inglewood, Torrance, Carson and other cities the limit wraps
# around; none of their land is in the grid.
BBOX = (-118.6682, 33.7037, -118.1553, 34.3373)

# Res 9 (~0.1 km2, ~370 m across), as in every other city-scale build: heat and
# canopy resolve per hex while census fields are interpolated downward. The
# city is 1,219 km2 of land, so this is by far the largest grid in the project.
H3_RES = 9

# Hex names come from OpenStreetMap place nodes only (neighbourhoods and
# suburbs: Sylmar, Koreatown, San Pedro). The shared default also names cells
# after named residential-landuse polygons, which suits a town of subdivisions;
# here those polygons are mostly single apartment complexes, and with them on
# a square mile of Sylmar came out as "Olive View Gardens NE 4".
NAME_FROM_LANDUSE = False

# Hexes are named for the neighbourhood they lie in: the Los Angeles Times
# "Mapping L.A." neighbourhood boundaries (114 inside the city), as published
# on the City of Los Angeles GeoHub. They are a newspaper's reader-reviewed
# map, not a legal boundary, and the city has no official neighbourhood
# layer that covers all of it (certified Neighborhood Councils leave gaps);
# these are the names residents and city departments use. A name locates a
# cell; nothing is scored or summed by neighbourhood.
NAME_AREAS = dict(
    service=("https://services5.arcgis.com/7nsPwEMP38bSkCjy/arcgis/rest/services/"
             "LA_Times_Neighborhoods/FeatureServer/0"),
    name_field="name",
    what="Los Angeles Times Mapping L.A. neighbourhood boundaries (City of Los Angeles GeoHub)",
)

# Los Angeles sits in UTM zone 11; the shared default is zone 10 (Contra Costa).
RASTER_CRS = "EPSG:32611"

# ---------------------------------------------------------------- satellite
# Summers 2024-2026, the shared window. For Los Angeles the newer window is not
# only fresher but necessary: the January 2025 Palisades fire burned through
# Pacific Palisades inside the city limit, and a 2022-2024 composite would show
# that ground as it was before the fire.

# ---------------------------------------------------------------- scoring
# HEAT IS SCORED, on the same test that decided the other builds. Normalising
# within the study area assumes one climate, and Los Angeles runs from the
# beach to the San Fernando Valley, so the question had to be measured rather
# than assumed. Across the 9,021 residential cells of this build, position
# (a linear fit on longitude and latitude) explains 8.8% of the variance in
# summer surface temperature (22.6-51.3 C, median 44.6), against 6% in West
# Contra Costa and 8% in Bakersfield, where heat is scored, and 14% in the
# county build, where it is not (same test, summers 2024-2026). The clearer
# separator is the next figure: surface temperature correlates -0.66 with
# aerial tree cover (-0.73 after removing the position trend), the strongest
# of any build (county -0.20, Pittsburg +0.23, both unscored), so a hotter
# cell here is mostly a barer cell, which is the signal a shade-planting screen
# wants. The coast-to-Valley gradient is real (Westside developed cells average
# about 41 C, Valley cells about 46 C) but it is a minor share of the spread.
#
# A/C IS SCORED: Census LACE 2023 runs 44-100% of occupied homes across ranked
# cells (median 94%, 2nd percentile 52%), the widest spread of any build, and
# it is uncorrelated with surface heat (r = 0.00), so it adds information
# rather than repeating the heat term. Low A/C is a coastal and older-housing
# pattern; heat keeps those cells from outranking hotter ones on A/C alone.
#
# The mix is West Contra Costa's, the build with the closest measured profile.
#
# SB 535 DISADVANTAGED COMMUNITIES ships at 0 in the recommended mix and leads
# the "Disadvantaged communities" preset (city.js), as in Bakersfield: a
# designation is a funding-eligibility screen, not a measurement of heat or
# shade. 4,614 of 11,893 cells are at least half inside a designated tract.
WEIGHTS = {
    "heat":     0.35,   # heat_n
    "green":    0.35,   # (1 - canopy_n)
    "ac":       0.15,   # (1 - ac_access_n)
    "age65":    0.15,   # age65_n
    "dac":      0.00,   # dac (share of the hex in an SB 535 tract) — preset only
}

# ---------------------------------------------------------------- census (US)
COUNTY_FIPS = "037"          # Los Angeles County
COUNTY_POP_RANGE = (9.0e6, 10.5e6)

CLIP_URL = ("https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/"
            "Places_CouSub_ConCity_SubMCD/MapServer/4/query?"
            "where=GEOID%3D%270644000%27&outFields=GEOID,NAME&"
            "returnGeometry=true&outSR=4326&f=geojson")

# Mapping Inequality (University of Richmond): the 1939 HOLC "residential
# security" map of Los Angeles. The only build in the project with one.
HOLC_URL = ("https://dsl.richmond.edu/panorama/redlining/static/"
            "citiesData/CALosAngeles1939/geojson.json")

# CalEPA SB 535 Disadvantaged Communities, final designation September 2026
# (CalEnviroScreen 5.0). 04f caches the tracts in the bbox.
SB535_URL = ("https://services1.arcgis.com/PCHfdHz4GlDNAhBb/ArcGIS/rest/services/"
             "SB_535_Disadvantaged_Communities_2026/FeatureServer")

# ---------------------------------------------------------------- buildings
# Block groups on the city line run into the neighbouring cities; the bbox
# already contains most of them, so a small margin is enough.
BUILDINGS_MARGIN_DEG = 0.02

# The OpenStreetMap building mask passes the dasymetric check on coverage (0.58
# mapped buildings per ACS housing unit over the block groups touching the
# city). 3.0 here, not the shared 2.0, on evidence (2026-11-11, ACS 2024 block
# groups wholly inside the city, n = 2,404): the count-based check reads 2.7x
# because the lowest-income quartile is apartment housing, not because it is
# unmapped. Median housing units per mapped building by income quartile:
# 3.04 / 1.69 / 1.34 / 1.01; share of units in one-unit structures: 20% / 43% /
# 53% / 88%. Restricted to the 443 block groups where at least 90% of units are
# one-unit structures, coverage is 1.14 / 1.26 / 1.27 / 1.16 buildings per unit,
# flat across income, and only 2 of 2,675 in-city block groups with housing
# have no mapped building. Los Angeles footprints are Los Angeles County's own
# building outlines imported into OpenStreetMap (2.9 million buildings in the
# extract carry a county building id), which is why the mask is even. A COUNT
# per unit is the wrong completeness metric for multifamily housing (the same
# finding as San Ramon); the weights themselves are footprint area.
DASY_MAX_INCOME_BIAS = 3.0

# ---------------------------------------------------------------- cooling sources
# Los Angeles County's own cooling center list (County Office of Emergency
# Management, "Operational Area Authoritative Cooling Center List", August
# 2026). It names no mapped discovery site as lacking A/C, so there are no
# exclusions; the county states each listed site has working air conditioning.
COOLING_SOURCE_URL = 'https://ready.lacounty.gov/heat/'
NO_AC_LIBRARIES = frozenset()

# ---------------------------------------------------------------- wards / districts
# The city's own GIS service (Bureau of Engineering, GIS Mapping Division).
# Boundaries are the 2021 redistricting map, Ordinance 187279, effective
# December 10, 2021. Member names are whatever the service says on the day 04e
# runs; the district number is the stable label.
WARDS = dict(
    service="https://maps.lacity.org/lahub/rest/services/Boundaries/MapServer/13",
    fields=dict(id="District", name="District_Name", member="NAME", url="NLA_URL"),
    label="District {n}", outside="City-line areas (center outside the limit)",
    what="Council districts", publisher="City of Los Angeles, Bureau of Engineering (GIS Mapping Division)",
    adopted="2021 redistricting, Ordinance 187279, effective December 10, 2021",
)

# ---------------------------------------------------------------- fire perimeters
# CAL FIRE FRAP historical fire perimeters. The tree-cover map is 2022 aerial
# imagery and the residents are ACS 2020-2024, so any fire from 2023 on is
# newer than both. Two reach the city: Palisades (January 2025, 56 km2 inside
# the limit, including most of Pacific Palisades) and Hurst (January 2025,
# 1.1 km2 of hillside above Sylmar). 04g flags the cells; nothing is rescored.
FIRE_PERIMETERS = dict(
    service=("https://services1.arcgis.com/jUJYIo9tSA7EHvfZ/arcgis/rest/services/"
             "California_Historic_Fire_Perimeters/FeatureServer/0"),
    since_year=2023, min_km2=0.05,
    publisher="CAL FIRE, Fire and Resource Assessment Program (FRAP)",
)

# ---------------------------------------------------------------- tree cover
# 02d (USFS / CAL FIRE 2022 aerial canopy, the Los Angeles--Long Beach--Anaheim
# urban-area package) assesses 8,978 of the 9,021 residential cells. 02c, the
# 2009-2020 height model the other builds use for their rural fringe, is not
# run here: it would fill 73 mountain-edge cells (43 unassessed, 30 assessed on
# under 10% of their area) with older imagery of unknown coverage. Those cells
# show the satellite greenness stand-in, labelled as such.
