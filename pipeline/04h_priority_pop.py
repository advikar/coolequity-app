"""Phase 4h — California Climate Investments priority populations (CARB) per hex.

State climate money (the Greenhouse Gas Reduction Fund, which pays for CAL FIRE's
urban forestry grants among others) has to reach "priority populations": the
SB 535 disadvantaged communities, plus the low-income communities and households
AB 1550 added. A planting program that reports against grant terms needs both,
and SB 535 alone (04f) misses the low-income tracts.

CARB publishes the areas as one layer, Priority Populations 5.0, in effect for
projects selected on or after September 18, 2026 (CalEnviroScreen 5.0, the final
2026 SB 535 designation, and AB 1550 low-income tracts: median household income
at or below 80% of the statewide median or the state's county low-income limit).
Each polygon carries one of these designations, and this stage keeps them as
CARB words them:

    Disadvantaged community                        SB 535, not low-income
    Disadvantaged and low-income community         both
    Low-income community                           AB 1550 tract
    Low-income community within 1/2 mile of a      AB 1550 tract, inside the
      disadvantaged community                      half-mile buffer

"Not a priority population area" polygons (including the half-mile buffer where
the tract is not low-income) are not counted. Low-income HOUSEHOLDS qualify
anywhere in the state; that is a property of a household, not of a place, and
no map can show it.

Per hex this writes
    pp        share of the hex's area inside a priority population area, 0-1
    pp_type   the designation covering most of the hex, or empty

It is a display and reporting field. It carries no weight and changes no score.

Gated by PRIORITY_POP_URL in the city's config.py. Run after 01; 05 merges the CSV.

    COOLEQUITY_CITY=bakersfield python pipeline/04h_priority_pop.py [--refresh]
"""
import json
import sys

import pandas as pd
import requests

import config as C

OUT_CSV = C.PRIORITY_POP_CSV
CACHE = C.DATA / f"priority_pop_{C.SLUG}.geojson"
UA = {"User-Agent": "CoolEquity/0.1 (heat-equity planning screen)"}

D, L, N = "Disadvantaged community", "Low-income community", "within ½ mile of a disadvantaged community"


def label(detail):
    """CARB's designation_detail codes ('ces dac, lic', 'neighbor, lic', 'not pp'...)
    to one of the four designations, or None where the area is not one."""
    parts = {p.strip().replace("_", " ") for p in (detail or "").lower().split(",")}
    dac = bool(parts & {"ces dac", "tribal dac"})
    lic = "lic" in parts
    if dac:
        return "Disadvantaged and low-income community" if lic else D
    if lic:
        return f"{L} {N}" if "neighbor" in parts else L
    return None


def log(msg):
    print(msg, flush=True)


def fetch():
    w, s, e, n = C.BBOX
    geom = json.dumps({"xmin": w, "ymin": s, "xmax": e, "ymax": n, "spatialReference": {"wkid": 4326}})
    feats, offset = [], 0
    while True:
        r = requests.get(f"{C.PRIORITY_POP_URL}/query", headers=UA, timeout=180, params={
            "where": "1=1", "geometry": geom, "geometryType": "esriGeometryEnvelope", "inSR": 4326,
            "spatialRel": "esriSpatialRelIntersects", "outFields": "designation,designation_detail,tract,geography",
            "outSR": 4326, "f": "geojson", "resultOffset": offset, "orderByFields": "objectid"})
        r.raise_for_status()
        gj = r.json()
        if "error" in gj:
            raise SystemExit(f"04h: service error: {gj['error']}")
        page = gj.get("features", [])
        feats.extend(page)
        more = (gj.get("properties") or {}).get("exceededTransferLimit") or gj.get("exceededTransferLimit")
        if not more or not page:
            break
        offset += len(page)
    out, unknown = [], set()
    for f in feats:
        p = f["properties"]
        lab = label(p.get("designation_detail"))
        if lab is None and "not pp" not in (p.get("designation_detail") or "").lower():
            unknown.add(p.get("designation_detail"))
        if lab and f.get("geometry"):
            t = p.get("tract")
            out.append({"type": "Feature", "geometry": f["geometry"], "properties": {
                "pp_type": lab, "tract": str(int(t)).zfill(11) if t not in (None, "") else "",
                "geography": p.get("geography")}})
    if unknown:
        raise SystemExit(f"04h: designation codes this stage does not know: {sorted(map(str, unknown))}")
    log(f"  fetched {len(feats)} polygons in the bbox, {len(out)} of them priority population areas")
    return {"type": "FeatureCollection",
            "designation": "California Climate Investments Priority Populations 5.0 (CARB), in effect September 18, 2026",
            "source": C.PRIORITY_POP_URL, "features": out}


def main():
    import geopandas as gpd
    log(f"Phase 4h — priority populations | {C.CITY}")
    if not getattr(C, "PRIORITY_POP_URL", None):
        log("  skipped: PRIORITY_POP_URL is not set for this city")
        return
    fresh = not CACHE.exists() or "--refresh" in sys.argv
    if fresh:
        gj = fetch()
        CACHE.write_text(json.dumps(gj))
    else:
        gj = json.loads(CACHE.read_text())
        log(f"  cached: {len(gj['features'])} polygons from {CACHE.relative_to(C.ROOT)}")

    from shapely import get_parts
    from shapely.ops import unary_union

    def polygonal(g):
        parts = [p for p in get_parts(g) if p.geom_type in ("Polygon", "MultiPolygon")]
        return unary_union(parts) if parts else None

    hexes = gpd.read_file(C.GRID_FILE).to_crs(C.RASTER_CRS)[["h3", "geometry"]]
    out = pd.DataFrame({"h3": hexes["h3"].values, "pp": 0.0, "pp_type": ""})
    if gj["features"]:
        pp = gpd.GeoDataFrame.from_features(gj["features"], crs="EPSG:4326")
        pp["geometry"] = pp.geometry.make_valid().map(polygonal)
        pp = pp[pp.geometry.notna() & ~pp.geometry.is_empty].to_crs(C.RASTER_CRS)
        inter = gpd.overlay(hexes, pp[["pp_type", "geometry"]], how="intersection", keep_geom_type=True)
        inter["a"] = inter.geometry.area
        area = hexes.set_index("h3").geometry.area
        share = (inter.dissolve(by="h3").geometry.area / area).clip(upper=1.0)
        top = (inter.groupby(["h3", "pp_type"], as_index=False)["a"].sum()
               .sort_values("a").drop_duplicates("h3", keep="last").set_index("h3"))
        out["pp"] = out["h3"].map(share).fillna(0.0).round(3)
        out["pp_type"] = out["h3"].map(top["pp_type"]).where(out["pp"] > 0, "").fillna("")
    out.to_csv(OUT_CSV, index=False)
    log(f"  {int((out['pp'] >= 0.5).sum())}/{len(out)} hexes mostly inside a priority population area; "
        f"types {out.loc[out['pp'] >= 0.5, 'pp_type'].value_counts().to_dict()}")
    log(f"  wrote {OUT_CSV.relative_to(C.ROOT)}")
    if fresh:
        from sources import record
        record("04h_priority_pop", "Priority populations (California Climate Investments)", C.PRIORITY_POP_URL,
               path=CACHE, count=len(gj["features"]), publisher="California Air Resources Board",
               note="Priority Populations 5.0, in effect for projects selected on or after September 18, 2026. "
                    "Areas only; low-income households qualify anywhere and are not mapped.")


if __name__ == "__main__":
    main()
