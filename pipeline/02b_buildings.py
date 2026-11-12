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

    if getattr(C, "BUILDINGS_SOURCE", None):
        return from_agency(C.BUILDINGS_SOURCE)

    sys.path.insert(0, str(C.ROOT / "pipeline"))
    overlays = __import__("04_overlays")

    log(f"Phase 2b — buildings | {C.CITY}")
    els = overlays.overpass(BUILDINGS_OQL, "buildings")

    rows = [r for r in (footprint(e.get("tags", {}).get("building", "yes"),
                                  [(p["lon"], p["lat"]) for p in (e.get("geometry") or [])])
                        for e in els) if r]
    write_buildings(rows)


# ---------------------------------------------------------------- agency footprints
# Where a city or county publishes its own building footprints with a use type,
# that layer replaces OpenStreetMap: it is digitised from the agency's aerial
# surveys to one standard across rich and poor neighbourhoods, which is the
# property the dasymetric guard in 03 exists to check. Set BUILDINGS_SOURCE in
# the city's config.py (see cities/bakersfield/config.py for the keys).
def arcgis_all(url, where="1=1", fields="*", envelope=None):
    """Every feature of an ArcGIS layer as GeoJSON features in EPSG:4326, fetched
    by object-id chunks so a server page limit cannot silently truncate it."""
    import time
    import requests
    q = {"where": where, "returnIdsOnly": "true", "f": "json"}
    if envelope:
        q.update(geometry=",".join(str(v) for v in envelope), geometryType="esriGeometryEnvelope",
                 inSR=4326, spatialRel="esriSpatialRelIntersects")
    r = requests.post(url.rstrip("/") + "/query", data=q, timeout=180)
    r.raise_for_status()
    meta = r.json()
    if "error" in meta:
        raise SystemExit(f"02b: {url}: {meta['error']}")
    ids = sorted(meta.get("objectIds") or [])
    oid = meta.get("objectIdFieldName", "OBJECTID")
    feats = []
    for i in range(0, len(ids), 500):
        chunk = ids[i:i + 500]
        for attempt in range(5):
            try:
                r = requests.post(url.rstrip("/") + "/query", data={
                    "objectIds": ",".join(str(v) for v in chunk), "outFields": fields,
                    "outSR": 4326, "f": "geojson", "geometryPrecision": 6}, timeout=180)
                r.raise_for_status()
                got = r.json()
                if "features" not in got:
                    raise ValueError(str(got)[:200])
                break
            except Exception as e:                       # noqa: BLE001 - retried, then fatal
                if attempt == 4:
                    raise SystemExit(f"02b: {url}: chunk at {oid} {chunk[0]} failed: {e}")
                time.sleep(5)
        if len(got["features"]) != len(chunk):
            raise SystemExit(f"02b: {url}: asked for {len(chunk)} features, got {len(got['features'])}")
        feats += got["features"]
        if (i // 500) % 50 == 0:
            log(f"    {len(feats):,} / {len(ids):,}")
    return feats


def from_agency(cfg):
    """Residential footprints from an agency layer.

    A footprint counts as residential when its use type says so. A footprint with
    NO use type (new construction the agency has digitised but not yet typed) is
    residential when its centre lies in a residential land-use designation; that
    is what keeps new subdivisions on the map. Every other type is left out.
    """
    import geopandas as gpd
    from sources import record
    log(f"Phase 2b — buildings | {C.CITY} | {cfg['publisher']}")
    w, s, e, n = C.BBOX
    env = (w - MARGIN_DEG, s - MARGIN_DEG, e + MARGIN_DEG, n + MARGIN_DEG)
    tf = cfg["type_field"]
    feats = arcgis_all(cfg["service"], fields=tf, envelope=env)
    b = gpd.GeoDataFrame.from_features(feats, crs="EPSG:4326")
    b = b[b.geometry.notna() & ~b.geometry.is_empty].copy()
    b["t"] = b[tf].fillna("").astype(str).str.strip().str.upper()
    res_types = {t.upper() for t in cfg["residential"]}
    tagged = b["t"].isin(res_types)
    untyped = b["t"] == ""
    log(f"  {len(b):,} footprints in the box: {int(tagged.sum()):,} typed residential, "
        f"{int(untyped.sum()):,} untyped, {int((~tagged & ~untyped).sum()):,} other uses (left out)")

    in_res = gpd.pd.Series(False, index=b.index)
    lu_cfg = cfg.get("untyped_landuse")
    if lu_cfg and untyped.any():
        lu = gpd.GeoDataFrame.from_features(
            arcgis_all(lu_cfg["service"], fields=lu_cfg["field"], envelope=env), crs="EPSG:4326")
        lu = lu[lu[lu_cfg["field"]].fillna("").str.strip().isin(set(lu_cfg["residential"]))]
        lu["geometry"] = lu.geometry.make_valid()
        cen = b.loc[untyped].to_crs(C.RASTER_CRS)
        cen = cen.set_geometry(cen.geometry.centroid)
        hit = gpd.sjoin(cen[["geometry"]], lu[["geometry"]].to_crs(C.RASTER_CRS), how="inner", predicate="within")
        in_res.loc[hit.index.unique()] = True
        log(f"  untyped footprints in a residential land-use designation: {int(in_res.sum()):,} kept, "
            f"{int(untyped.sum() - in_res.sum()):,} left out")

    keep = b[tagged | in_res].copy()
    # "residential" and "yes" are the tags 05 and the multi-family rule already know.
    keep["bt"] = ["residential" if t else "yes" for t in tagged[keep.index]]
    keep = keep.explode(index_parts=False)
    keep = keep[keep.geometry.geom_type == "Polygon"]
    keep["geometry"] = keep.geometry.make_valid()
    keep = keep[keep.geometry.geom_type == "Polygon"]
    write_buildings(keep[["bt", "geometry"]])
    n_out = len(json.loads(C.BUILDINGS_FILE.read_text())["features"])
    record("02b_buildings", "Residential building footprints", cfg["service"], path=C.BUILDINGS_FILE,
           count=n_out, publisher=cfg["publisher"],
           note=(f"{int(tagged.sum()):,} footprints typed {'/'.join(sorted(res_types))} plus {int(in_res.sum()):,} "
                 "untyped footprints lying in a residential land-use designation, before the size filter. "
                 + cfg.get("note", "")).strip())


# ---------------------------------------------------------------- block weights
# Footprint AREA is a proxy for where people live, and a biased one: storeys are
# not recorded, so a three-storey apartment block weighs what a one-storey house
# of the same footprint does, and household size is not in a footprint at all (a
# seniors' mobile-home park and a block of family houses weigh the same per m2).
# The 2020 Census counted both, block by block. Where a city sets BLOCK_WEIGHTS,
# each building's weight becomes its share (by footprint area) of its block's
# residents, so 03 splits a block group's ACS residents between its blocks the
# way the Census found them and between a block's buildings by footprint.
#
# Homes built since April 2020 are not in that count. A block with more main
# residential footprints than it had housing units in 2020 has grown by the
# difference, and each new home is credited with its block group's 2020
# residents per housing unit. A block of new houses on what was a field in 2020
# therefore still carries people.
def block_weights(gdf, cfg):
    """Add column `w` (2020 residents, plus growth, shared by footprint area)."""
    import geopandas as gpd
    import numpy as np
    from sources import record
    w, s, e, n = C.BBOX
    env = (w - MARGIN_DEG, s - MARGIN_DEG, e + MARGIN_DEG, n + MARGIN_DEG)
    f = cfg.get("fields", {})
    pop_f, hu_f, id_f = f.get("pop", "POP100"), f.get("units", "HU100"), f.get("geoid", "GEOID")
    feats = arcgis_all(cfg["service"], fields=f"{pop_f},{hu_f},{id_f}", envelope=env)
    blocks = gpd.GeoDataFrame.from_features(feats, crs="EPSG:4326").to_crs(C.RASTER_CRS)
    blocks = blocks.rename(columns={pop_f: "pop20", hu_f: "hu20", id_f: "block"})[["block", "pop20", "hu20", "geometry"]]
    blocks["geometry"] = blocks.geometry.make_valid()
    main_m2 = float(cfg.get("main_m2", 80.0))

    cen = gdf.copy()
    cen["geometry"] = cen.geometry.centroid
    hit = gpd.sjoin(cen[["area_m2", "geometry"]], blocks[["block", "geometry"]], how="left", predicate="within")
    hit = hit[~hit.index.duplicated()]
    gdf["block"] = hit["block"].reindex(gdf.index)
    per = gdf.groupby("block").agg(area=("area_m2", "sum"), n_main=("area_m2", lambda a: int((a >= main_m2).sum())))
    per = per.join(blocks.set_index("block")[["pop20", "hu20"]])
    per["bg"] = per.index.str[:12]
    bl = blocks.assign(bg=blocks["block"].str[:12])
    bg = bl[bl["hu20"] > 0].groupby("bg")[["pop20", "hu20"]].sum()
    county_ppu = float(bg["pop20"].sum() / bg["hu20"].sum())
    ppu = (bg["pop20"] / bg["hu20"]).clip(lower=1.0, upper=6.0)
    per["ppu"] = per["bg"].map(ppu).fillna(county_ppu)
    per["growth"] = (per["n_main"] - per["hu20"]).clip(lower=0)
    per["est"] = per["pop20"] + per["growth"] * per["ppu"]
    gdf["w"] = gdf["area_m2"] / gdf["block"].map(per["area"]) * gdf["block"].map(per["est"])
    lost = gdf["w"].isna()
    if lost.any():                      # a footprint outside every block: the typical weight per m2
        gdf.loc[lost, "w"] = gdf.loc[lost, "area_m2"] * float(np.nanmedian(gdf["w"] / gdf["area_m2"]))
    gdf["w"] = gdf["w"].round(3)
    with_homes = blocks[blocks["hu20"] > 0]
    no_fp = with_homes[~with_homes["block"].isin(per.index)]
    log(f"  block weights: {len(blocks):,} 2020 blocks in the box; {len(per):,} hold residential footprints "
        f"({int(per['pop20'].sum()):,} residents in 2020 + {int((per['growth'] * per['ppu']).sum()):,} credited to "
        f"{int(per['growth'].sum()):,} homes built since); {int(lost.sum())} footprints outside every block")
    log(f"  block weights: {len(no_fp):,} blocks with housing in 2020 hold no residential footprint "
        f"({int(no_fp['pop20'].sum()):,} residents, {no_fp['pop20'].sum() / max(1, blocks['pop20'].sum()):.1%} of the box); "
        f"their block groups' residents go to the footprints the block group does have")
    record("02b_buildings", "2020 Census blocks (residents and housing units, for building weights)", cfg["service"],
           count=len(blocks), publisher="US Census Bureau, TIGERweb",
           note=(f"2020 Census block counts (P.L. 94-171). Each residential footprint is weighted by its block's 2020 "
                 f"residents, shared by footprint area; {int(per['growth'].sum()):,} homes built since 2020 (main footprints "
                 f"beyond the block's 2020 housing units) are credited at their block group's residents per unit."))
    return gdf.drop(columns=["block"])


def footprint(bt, ring):
    """One residential footprint row from a building tag and its (lon, lat) ring,
    or None. Shared by the Overpass path above and 00_osm_extract.py."""
    from shapely.geometry import Polygon
    if len(ring) < 4 or bt not in RESIDENTIAL:
        return None
    if ring[0] != ring[-1]:
        ring = ring + [ring[0]]
    try:
        poly = Polygon(ring)
    except Exception:
        return None
    if not poly.is_valid:
        poly = poly.buffer(0)
    if poly.is_empty or poly.geom_type != "Polygon":
        return None
    return {"bt": bt, "geometry": poly}


def write_buildings(rows):
    import geopandas as gpd
    gdf = (rows if isinstance(rows, gpd.GeoDataFrame) else gpd.GeoDataFrame(rows, crs="EPSG:4326")).to_crs(C.RASTER_CRS)
    gdf["area_m2"] = gdf.geometry.area
    n_raw = len(gdf)
    gdf = gdf[(gdf.area_m2 >= MIN_RES_M2) & (gdf.area_m2 <= MAX_RES_M2)].copy()
    gdf["multifamily"] = ((gdf.area_m2 >= MULTIFAMILY_M2)
                          | (gdf.bt == "apartments"))
    cols = ["bt", "area_m2", "multifamily", "geometry"]
    if getattr(C, "BLOCK_WEIGHTS", None):
        gdf = block_weights(gdf, C.BLOCK_WEIGHTS)
        cols.insert(2, "w")

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
    out[cols].to_file(
        C.BUILDINGS_FILE, driver="GeoJSON", coordinate_precision=5)
    log(f"  wrote {C.BUILDINGS_FILE.relative_to(C.ROOT)} "
        f"({C.BUILDINGS_FILE.stat().st_size/1e6:.1f} MB, centroids + floor area)")


if __name__ == "__main__":
    main()
