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
# like with like. Re-measured November 11, 2026 on the 1,987 cells ranked once
# residents were placed by building (summers 2024-2026): 35.1-57.1 C, median
# 49.1 C; position explains 16% of the variance and surface temperature
# correlates -0.66 with tree cover. (On the 3,767 cells ranked under the old
# even spread, half of them without housing, those read 8% and -0.33.)
#
# A/C ACCESS ships at 0. The Census LACE 2023 estimate is nearly uniform here
# (96.5-100% of occupied homes across ranked cells, median 99.8%). Min-max
# scaling would stretch that 3.5-point modelled spread to a full 0-1 term, so a
# non-zero weight would score model noise, not a housing difference. The input
# stays measured, displayed and movable; the "Homes without A/C" preset shows it.
#
# SB 535 DISADVANTAGED COMMUNITIES ships at 0 in the recommended mix and is the
# lead term of the "Disadvantaged communities" preset (city.js). The city's
# planting program commits at least 80% of new trees to SB 535-designated
# tracts (CalEPA, final designation September 2026), so the designation is an
# input and a layer here. It is a policy screen, not a measurement: a 0/1 share
# of the hex inside a designated tract, not a continuous need gradient. Keeping
# it out of the recommended mix keeps the shipped ranking a physical and
# demographic need ranking; the preset answers "where, within the commitment".
WEIGHTS = {
    "heat":     0.45,   # heat_n
    "green":    0.35,   # (1 - canopy_n)
    "ac":       0.00,   # (1 - ac_access_n) — nearly uniform, see above
    "age65":    0.20,   # age65_n
    "dac":      0.00,   # dac (share of the hex in an SB 535 tract) — preset only
}

# ---------------------------------------------------------------- census (US)
COUNTY_FIPS = "029"          # Kern County
COUNTY_POP_RANGE = (0.8e6, 1.1e6)

CLIP_URL = ("https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/"
            "Places_CouSub_ConCity_SubMCD/MapServer/4/query?"
            "where=GEOID%3D%270603526%27&outFields=GEOID,NAME&"
            "returnGeometry=true&outSR=4326&f=geojson")

HOLC_URL = None              # no digitised HOLC map for Bakersfield

# CalEPA SB 535 Disadvantaged Communities, final designation September 2026
# (CalEnviroScreen 5.0). 04f caches the tracts in the bbox as
# data/sb535_bakersfield.geojson: 92 Kern tracts, none tribal.
SB535_URL = ("https://services1.arcgis.com/PCHfdHz4GlDNAhBb/ArcGIS/rest/services/"
             "SB_535_Disadvantaged_Communities_2026/FeatureServer")

# Footprint area alone cannot see storeys or household size. Each footprint is
# weighted by its 2020 Census block's residents (shared within the block by
# footprint area), with homes built since 2020 credited at their block group's
# residents per unit. See block_weights() in 02b.
BLOCK_WEIGHTS = dict(
    service="https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/Tracts_Blocks/MapServer/2",
    fields=dict(pop="POP100", units="HU100", geoid="GEOID"), main_m2=80.0,
)

# California Climate Investments Priority Populations 5.0 (CARB), in effect for
# projects selected on or after September 18, 2026: the SB 535 tracts above plus
# the AB 1550 low-income communities. Display and reporting only, never scored.
PRIORITY_POP_URL = ("https://gis.carb.arb.ca.gov/hosting/rest/services/Hosted/"
                    "PriorityPopulations5/FeatureServer/0")

# ---------------------------------------------------------------- buildings
# The City of Bakersfield's own footprint layer ("Building General Structure
# Existing Site", maintained by the city's GIS office from its aerial surveys,
# last edited July 2026), not OpenStreetMap, which has mapped too little of the
# city to place residents with. 228,012 footprints over the metropolitan
# general-plan area, each with a use type. Measured November 11, 2026 against
# ACS 2020-2024 housing units over the 344 block groups touching the city:
# 0.95 residential footprints per housing unit, and by income quartile of the
# block group 0.84 / 0.93 / 0.97 / 1.17 (richest/poorest 1.4x, inside the 2.0x
# guard; the low end is apartment block groups, where one building holds many
# homes). 03 re-checks both numbers on every run.
#
# Residential = use type RESIDENTIAL. "MULTIPLE" is multi-tenant commercial
# (its second type field reads Commercial / General / Industrial) and is left
# out. 22,989 footprints carry no type, 17,075 of them digitised from the 2026
# aerial: new construction not yet typed. Those count when their centre lies in
# a residential designation of the Metropolitan Bakersfield General Plan land
# use layer, so new subdivisions are not dropped.
#
# The margin only has to reach the far side of block groups that straddle the
# city limit; the layer ends at the general-plan boundary in any case.
BUILDINGS_MARGIN_DEG = 0.09
BUILDINGS_SOURCE = dict(
    service="https://gis.bakersfieldcity.us/webmaps/rest/services/General/Buildings/MapServer/0",
    publisher="City of Bakersfield GIS Office",
    type_field="FAC_TYPE_1", residential=("RESIDENTIAL",),
    untyped_landuse=dict(
        service="https://gis.bakersfieldcity.us/webmaps/rest/services/General/LandUse/MapServer/6",
        field="LANDUSE",
        residential=("LR", "LMR", "LMR/LR", "HMR", "HR", "SR", "SR/LR", "RR", "ER", "UER",
                     "WM-LR", "WM-LMR", "WM-HMR", "WM-HR")),
    note="City footprint layer, last edited July 2026; land use is the Metropolitan Bakersfield General Plan layer.",
)

# ---------------------------------------------------------------- cooling sources
# No documented exclusions yet: the Kern County cooling-center page lists
# county-run and independent centers but does not identify mapped discovery
# sites (libraries, pools, community centres) that lack A/C.
COOLING_SOURCE_URL = 'https://www.kerncounty.com/government/aging-adult-services/services/cooling-centers'
NO_AC_LIBRARIES = frozenset()

# ---------------------------------------------------------------- wards / districts
# The city's own GIS service. Boundaries are the 2022 redistricting map (council
# map 5B, the "Unity Map"), first used for the November 2022 election. Member
# names are whatever the service says on the day 04e runs; the ward number is
# the stable label.
WARDS = dict(
    service="https://gis.bakersfieldcity.us/webmaps/rest/services/General/Boundary/MapServer/5",
    fields=dict(id="WARD_ID", name="FEAT_NAME", member="MEMBER", url="LINK"),
    label="Ward {n}", outside="Unincorporated (Kern County)",
    what="Council wards", publisher="City of Bakersfield GIS Office",
    adopted="2022 redistricting, council map 5B (Unity Map)",
)

# ---------------------------------------------------------------- area names
# OpenStreetMap has few place nodes here, so nearest-place naming gave hundreds
# of cells names like "Village at Lakeside E 21". The city's street centreline
# layer carries names and a road class; 04i names every cell by its cross
# streets, the way locations are given in Bakersfield.
NAME_STREETS = dict(
    service="https://gis.bakersfieldcity.us/webmaps/rest/services/General/Transportation/MapServer/4",
    publisher="City of Bakersfield GIS Office",
    fields=dict(prefix="PREFIX", name="NAME", type="TYPE", suffix="SUFFIX", cls="CLASS"),
    major=("ARTERIAL", "HIGHWAY", "EXPRESSWAY"),
    collector=("COLLECTOR", "LOCAL-COLLECTOR", "CITY-COLLECTOR"),
    skip=("RAMP", "FREEWAY", "FUTURE", "DIRT"),
)

# ---------------------------------------------------------------- places people go
# The city's program (Recreation and Parks; $500,000 for fiscal 2026-27, 80% of
# planting in underserved areas, wards with the least canopy first) plants in
# city parks, along city streetscapes and the Kern River Parkway, and its
# Central City corridor project is about downtown walkability. Those are places,
# not homes, and the resident ranking cannot see a hex without homes. 04j counts
# schools, bus stops and public parks per hex from the city's own layers so the
# app can list them by hot ground and missing shade. Never scored.
_GIS = "https://gis.bakersfieldcity.us/webmaps/rest/services/General"
PLACES = dict(
    schools=dict(service=f"{_GIS}/Education/MapServer/0", properties=f"{_GIS}/Education/MapServer/2", name="NAME", type="TYPE", status="STATUS",
                 closed=("CLOSED",), skip_types=("JUVENILE HALL", "ADULT"),
                 publisher="City of Bakersfield GIS Office",
                 note="School Facilities layer; open schools only. The layer's own verification dates are from 2018, so a school opened since may be missing."),
    bus_stops=dict(service=f"{_GIS}/Transportation/MapServer/1", name="Name",
                   publisher="Golden Empire Transit, via City of Bakersfield GIS Office",
                   note="GET Bus Stops layer, last edited June 2026."),
    parks=dict(service=f"{_GIS}/ParksAndRecreation/MapServer/1", name="NAME", type="TYPE", owner="AGENCY_ID",
               status="PARK_STATUS", types=("Park", "Dog Park", "Rec Facility", "Community Center", "Preserve"),
               private=("PRIVATE", "PARK STOCKDALE CIVIC ASSOCIATION"), city_owner="CITY OF BAKERSFIELD",
               publisher="City of Bakersfield GIS Office",
               note="Park and Recreation layer: active public parks (city, county, North of the River district, state). Golf courses, the fairgrounds and private parks are left out."),
)

# ---------------------------------------------------------------- tree cover past the USFS map
# The USFS / CAL FIRE 2022 map stops at the 2020 Census urban-area line; the
# city's newest subdivisions lie past it. 02g models tree cover there from the
# same June 2022 NAIP aerial survey the USFS map was classified from, trained
# on cells the USFS map covers and tested on others of three kinds: urban,
# open land (fields, pasture, bare ground, orchards) and cells the line cuts.
# It writes nothing unless it beats the old canopy-height model on held-out
# urban AND open-land cells. Measured November 11, 2026 (mean absolute error
# in percentage points of tree cover, model / height model): urban 0.92 / 1.75,
# open land 0.62 / 3.24, edge 1.18; bias within 0.12 on all three.
# reports/canopy_naip_bakersfield.json holds the figures.
#
# complete_partial_below: a cell the urban line cuts keeps the USFS figure for
# its assessed part unless under this share of its in-city homes (weighted by
# residents) is in that part; then the model fills the rest and the figure is
# for the whole cell. 23 ranked cells on November 11, 2026. Completing all 217
# partly assessed cells was compared and rejected (the owner's decision): it
# moved 97 cells by 100+ ranks, mostly cells whose homes were already measured.
CANOPY_NAIP = dict(year=2022, train_cells=300, test_cells=300, max_mae=2.0, complete_partial_below=0.5)
