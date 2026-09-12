"""Phase 2b — residential building footprints, for dasymetric population.

Why this exists
---------------
03_census.py used to split a block group's residents across hexes by AREA. At
H3 res 8 (LA, 0.82 km2) that is a reasonable assumption: a hex is big enough to
average over. At res 9 (San Ramon, 0.11 km2) it is not, and it manufactures
people. Measured on the first San Ramon build: 57 of 540 hexes held >=50
"residents" each while containing zero residential buildings -- 5,850 people,
6.9% of the city, placed on golf courses, ridgelines and the Bishop Ranch office
park. One of them ranked #10 in the city.

Those phantom residents are not harmless. Population is a multiplier in the
score, so an empty hex that inherits people from a populated block group gets
promoted up the priority list, and a planner sent to look at it finds a hillside.

The fix is dasymetric refinement: use building footprints as the mask that says
where people actually are, and split the block group by residential FLOOR AREA
rather than by ground area. This is standard practice in the areal-interpolation
literature, and here it is grounded in measured data -- OSM has 26,346 building
footprints inside the San Ramon bbox, which for a city of ~30k housing units is
effectively complete coverage.

Writes data/buildings_<slug>.geojson: one polygon per residential building, with
its footprint area and an is_multifamily flag. 03 consumes it; 05 uses the flag
to report what kind of housing a hex actually contains, rather than inferring it
from the name of the nearest landmark.
"""
import json
import sys

import config as C

# Residential only. A warehouse roof holds nobody, and including commercial
# floor area would pull residents toward the office park -- the exact error
# this script exists to remove.
RESIDENTIAL = {
    "detached", "house", "apartments", "terrace", "residential",
    "semidetached_house", "bungalow", "dormitory", "yes",
}
# "yes" is in the list because 9,533 of San Ramon's footprints are untyped and
# excluding them would delete a third of the city's housing. It is filtered by
# geometry instead: anything above MAX_RES_M2 is a big-box store or a school,
# not a home.
MAX_RES_M2 = 4000.0
MIN_RES_M2 = 30.0
# A detached house here is ~200-350 m2 of footprint. 600 m2 is comfortably
# above that and below a garden-apartment block, so it separates the two
# without needing a tag that most buildings do not carry.
MULTIFAMILY_M2 = 600.0

# Queried WIDER than the study bbox on purpose: 03 divides a block group's
# residents by that block group's TOTAL housing, so block groups straddling the
# edge need their outside houses counted or the denominator is short and every
# in-area hex sharing them is inflated. The margin is per-study-area and lives in
# config.BUILDINGS_MARGIN_DEG -- see the note there for why San Ramon needed
# 0.09 deg and a county-wide bbox needs far less.
MARGIN_DEG = C.BUILDINGS_MARGIN_DEG

BUILDINGS_OQL = f"""[out:json][timeout:{C.OVERPASS_TIMEOUT_S}];
way["building"]({C.BBOX[1]-MARGIN_DEG},{C.BBOX[0]-MARGIN_DEG},\
{C.BBOX[3]+MARGIN_DEG},{C.BBOX[2]+MARGIN_DEG});
out geom;
"""


def log(msg):
    print(msg, flush=True)


def main():
    refresh = "--refresh" in sys.argv
    if C.BUILDINGS_FILE.exists() and not refresh:
        gj = json.loads(C.BUILDINGS_FILE.read_text())
        log(f"Phase 2b — buildings | cached {C.BUILDINGS_FILE.name} "
            f"({len(gj['features'])} residential) — --refresh to re-pull")
        return

    import geopandas as gpd
    from shapely.geometry import Polygon

    sys.path.insert(0, str(C.ROOT / "pipeline"))
    overlays = __import__("04_overlays")

    log(f"Phase 2b — buildings | {C.CITY}")
    els = overlays.overpass(BUILDINGS_OQL, "buildings")

    rows = []
    for e in els:
        g = e.get("geometry")
        if not g or len(g) < 4:
            continue
        bt = e.get("tags", {}).get("building", "yes")
        if bt not in RESIDENTIAL:
            continue
        ring = [(p["lon"], p["lat"]) for p in g]
        if ring[0] != ring[-1]:
            ring.append(ring[0])
        try:
            poly = Polygon(ring)
        except Exception:
            continue
        if not poly.is_valid:
            poly = poly.buffer(0)
        if poly.is_empty or poly.geom_type != "Polygon":
            continue
        rows.append({"bt": bt, "geometry": poly})

    gdf = gpd.GeoDataFrame(rows, crs="EPSG:4326").to_crs(C.RASTER_CRS)
    gdf["area_m2"] = gdf.geometry.area
    n_raw = len(gdf)
    gdf = gdf[(gdf.area_m2 >= MIN_RES_M2) & (gdf.area_m2 <= MAX_RES_M2)].copy()
    gdf["multifamily"] = ((gdf.area_m2 >= MULTIFAMILY_M2)
                          | (gdf.bt == "apartments"))

    log(f"  {n_raw} residential-tagged -> {len(gdf)} after the "
        f"{MIN_RES_M2:.0f}-{MAX_RES_M2:.0f} m2 size filter")
    log(f"  {gdf.multifamily.sum()} flagged multi-family "
        f"(>={MULTIFAMILY_M2:.0f} m2 footprint or building=apartments)")
    log(f"  total residential floor plate: {gdf.area_m2.sum()/1e6:.2f} km2")

    # Stored as centroids, not polygons: the only thing downstream asks of a
    # building is "which hex is it in, and how much floor plate does it carry",
    # and a footprint is two orders of magnitude smaller than a hex, so the
    # centroid answers that exactly. Keeps the committed file at ~2 MB instead
    # of 12 MB of ring coordinates nothing reads.
    # Centroid in the PROJECTED crs, then reproject. Taking a centroid in
    # EPSG:4326 averages degrees, which is not the centre of anything.
    out = gdf.copy()
    out["geometry"] = out.geometry.centroid
    out["area_m2"] = out["area_m2"].round(1)
    out = out.to_crs("EPSG:4326")
    out[["bt", "area_m2", "multifamily", "geometry"]].to_file(
        C.BUILDINGS_FILE, driver="GeoJSON", coordinate_precision=5)
    log(f"  wrote {C.BUILDINGS_FILE.relative_to(C.ROOT)} "
        f"({C.BUILDINGS_FILE.stat().st_size/1e6:.1f} MB, centroids + floor area)")


if __name__ == "__main__":
    main()
