"""Phase 4e — SB 535 Disadvantaged Communities (CalEPA, 2026 designation) per hex.

California's SB 535 designation names the census tracts that receive priority
for Greenhouse Gas Reduction Fund money. The September 2026 designation (final)
qualifies a tract under any of four criteria: top 25% of CalEnviroScreen 5.0
overall scores, top 5% of CES 5.0 pollution burden, at least 25% overlap with a
2022 (CES 4.0) DAC tract, or land under the control of a federally recognized
tribe. Cities that commit a share of planting to disadvantaged communities
(Bakersfield: at least 80% of new trees) screen against this list, so the map
carries it as an input and a layer.

Per hex this writes
    dac         share of the hex's area inside a designated tract or tribal
                land, 0-1 (area overlap, as HOLC is majority-overlap in 04).
                1.0 means wholly designated; a boundary hex reads its share.
    dac_type    designation criterion of the tract covering most of the hex
                (CES 5.0 Top 25%, CES 5.0 Top 5% Pollution Burden,
                CES 4.0 Carry-Over DAC, Tribal), or empty where none.
    dac_tract   that tract's 11-digit GEOID, or empty.

Source: CalEPA ArcGIS feature service SB_535_Disadvantaged_Communities_2026
(layers 0 tracts, 1-3 tribal boundaries), queried for the study bbox and cached
as data/sb535_<slug>.geojson. Gated by SB535_URL in the city's config.py: no URL,
no layer, and 05 scores the term at zero. Run after 01; 05 merges the CSV.

    COOLEQUITY_CITY=bakersfield python pipeline/04f_sb535.py [--refresh]
"""
import json
import sys

import pandas as pd
import requests

import config as C

OUT_CSV = C.DATA / f"sb535_{C.SLUG}.csv"
CACHE = C.DATA / f"sb535_{C.SLUG}.geojson"
UA = {"User-Agent": "CoolEquity/0.1 (heat-equity planning screen)"}
TRACT_LAYER = 0
TRIBAL_LAYERS = (1, 2, 3)


def log(msg):
    print(msg, flush=True)


def fetch_layer(layer):
    """Every feature of one layer that intersects the bbox, paged past the
    service's maxRecordCount. With f=geojson ArcGIS reports exceededTransferLimit
    under the top-level `properties`, not beside `features`."""
    w, s, e, n = C.BBOX
    geom = json.dumps({"xmin": w, "ymin": s, "xmax": e, "ymax": n,
                       "spatialReference": {"wkid": 4326}})
    feats, offset = [], 0
    while True:
        r = requests.get(f"{C.SB535_URL}/{layer}/query", headers=UA, timeout=120, params={
            "where": "1=1", "geometry": geom, "geometryType": "esriGeometryEnvelope",
            "inSR": 4326, "spatialRel": "esriSpatialRelIntersects", "outFields": "*",
            "outSR": 4326, "f": "geojson", "resultOffset": offset})
        r.raise_for_status()
        gj = r.json()
        if "error" in gj:
            raise SystemExit(f"SB 535 service error on layer {layer}: {gj['error']}")
        page = gj.get("features", [])
        feats.extend(page)
        more = (gj.get("properties") or {}).get("exceededTransferLimit") or gj.get("exceededTransferLimit")
        if not more or not page:
            return feats
        offset += len(page)


def fetch():
    feats = []
    for f in fetch_layer(TRACT_LAYER):
        p = f["properties"]
        feats.append({"type": "Feature", "geometry": f["geometry"], "properties": {
            "dac_type": p.get("dac_type") or "designated",
            # The service stores the GEOID as a number, which drops California's leading 0.
            "dac_tract": str(int(p["tract"])).zfill(11) if p.get("tract") else "",
            "county": p.get("county"), "ces_pctile": p.get("CIscoreP"),
            "pollution_pctile": p.get("PollutionP")}})
    tribal = 0
    for layer in TRIBAL_LAYERS:
        for f in fetch_layer(layer):
            tribal += 1
            feats.append({"type": "Feature", "geometry": f["geometry"], "properties": {
                "dac_type": "Tribal", "dac_tract": "", "county": None,
                "ces_pctile": None, "pollution_pctile": None}})
    log(f"  fetched {len(feats) - tribal} designated tracts and {tribal} tribal areas in the bbox")
    return {"type": "FeatureCollection",
            "designation": "SB 535 Disadvantaged Communities, final designation September 2026 (CalEPA)",
            "source": C.SB535_URL, "features": feats}


def main():
    import geopandas as gpd
    refresh = "--refresh" in sys.argv
    log(f"Phase 4e — SB 535 disadvantaged communities | {C.CITY}")
    if not getattr(C, "SB535_URL", None):
        log("  skipped: SB535_URL is not set for this city (no layer, term scored at 0)")
        return
    if CACHE.exists() and not refresh:
        gj = json.loads(CACHE.read_text())
        log(f"  cached: {len(gj['features'])} polygons from {CACHE.relative_to(C.ROOT)}")
    else:
        gj = fetch()
        CACHE.write_text(json.dumps(gj))
        log(f"  wrote {CACHE.relative_to(C.ROOT)}")

    hexes = gpd.read_file(C.GRID_FILE).to_crs(C.RASTER_CRS)[["h3", "geometry"]]
    feats = [f for f in gj["features"] if f.get("geometry")]
    if len(feats) < len(gj["features"]):
        log(f"  {len(gj['features']) - len(feats)} features without geometry dropped")
    dac = gpd.GeoDataFrame.from_features(feats, crs="EPSG:4326")
    # make_valid can return a GeometryCollection; keep its polygonal parts rather
    # than losing the tract to the type filter below.
    from shapely import get_parts
    from shapely.ops import unary_union
    def polygonal(g):
        parts = [p for p in get_parts(g) if p.geom_type in ("Polygon", "MultiPolygon")]
        return unary_union(parts) if parts else None
    dac["geometry"] = dac.geometry.make_valid().map(polygonal)
    dac = dac[dac.geometry.notna() & ~dac.geometry.is_empty]
    # Also pad a cache written before the zfill above.
    dac["dac_tract"] = dac["dac_tract"].fillna("").astype(str).map(lambda t: t.zfill(11) if t else "")
    dac = dac[dac.geometry.geom_type.isin(("Polygon", "MultiPolygon"))].to_crs(C.RASTER_CRS)

    inter = gpd.overlay(hexes, dac[["dac_type", "dac_tract", "geometry"]],
                        how="intersection", keep_geom_type=True)
    inter["a"] = inter.geometry.area
    # Designations can stack (a carry-over tract under tribal land); the share is
    # of the union, so it never exceeds 1.
    union = inter.dissolve(by="h3").geometry.area
    area = hexes.set_index("h3").geometry.area
    share = (union / area).clip(upper=1.0)
    top = (inter.groupby(["h3", "dac_type", "dac_tract"], as_index=False)["a"].sum()
           .sort_values("a").drop_duplicates("h3", keep="last").set_index("h3"))

    out = pd.DataFrame({"h3": hexes["h3"].values})
    out["dac"] = out["h3"].map(share).fillna(0.0).round(3)
    out["dac_type"] = out["h3"].map(top["dac_type"]).where(out["dac"] > 0, "")
    out["dac_tract"] = out["h3"].map(top["dac_tract"]).where(out["dac"] > 0, "")
    out.to_csv(OUT_CSV, index=False)

    n_in = int((out["dac"] >= 0.5).sum())
    log(f"  {n_in}/{len(out)} hexes mostly inside a designated community; "
        f"{int((out['dac'] > 0).sum())} touch one; "
        f"types {out.loc[out['dac'] > 0, 'dac_type'].value_counts().to_dict()}")
    log(f"  wrote {OUT_CSV.relative_to(C.ROOT)}")


if __name__ == "__main__":
    main()
