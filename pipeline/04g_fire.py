"""Phase 4g — wildfire perimeters newer than the tree-cover and census inputs.

The tree-cover map is a 2022 aerial classification and the residents are the
2020-2024 American Community Survey. Where a wildfire has burned through a
neighbourhood since, both describe ground that no longer exists as measured:
the January 2025 Palisades fire destroyed thousands of homes inside the City of
Los Angeles, and a cell there still carries its 2022 tree cover and its
pre-fire residents. The map cannot correct those numbers, so it says which
cells they are.

Per hex this writes
    fire        share of the hex's area inside the perimeter of a fire that
                started in or after FIRE_PERIMETERS["since_year"], 0-1 (the
                union of all such perimeters, so overlaps never exceed 1)
    fire_name   the fire covering most of the hex, e.g. "Palisades"
    fire_year   its year

A perimeter is the outer line of the fire, not a map of what burned: unburned
islands and surviving houses and trees lie inside it. The flag means "inputs
here predate a fire; check before using them", nothing more. It carries no
weight and changes no score.

Source: CAL FIRE FRAP historical fire perimeters (ArcGIS feature service),
queried for the study bbox and cached as data/fire_<slug>.geojson. Gated by
FIRE_PERIMETERS in the city's config.py; no entry, no stage, and 05 writes a
zero share. Run after 01; 05 merges the CSV.

    COOLEQUITY_CITY=losangeles python pipeline/04g_fire.py [--refresh]
"""
import datetime
import json
import sys

import config as C

FIRE_FILE = C.DATA / f"fire_{C.SLUG}.geojson"
FIRE_CSV = C.FIRE_CSV
MIN_SHARE = 0.005        # below half a percent of a cell is a sliver of digitising


def log(msg):
    print(msg, flush=True)


def fetch(cfg):
    import requests
    w, s, e, n = C.BBOX
    feats, offset = [], 0
    while True:
        r = requests.get(cfg["service"].rstrip("/") + "/query", params={
            "where": f"YEAR_>={int(cfg['since_year'])}",
            "geometry": f"{w},{s},{e},{n}", "geometryType": "esriGeometryEnvelope", "inSR": 4326,
            "spatialRel": "esriSpatialRelIntersects",
            "outFields": "YEAR_,FIRE_NAME,AGENCY,INC_NUM,ALARM_DATE,CONT_DATE,GIS_ACRES",
            "outSR": 4326, "f": "geojson", "resultOffset": offset}, timeout=180)
        r.raise_for_status()
        g = r.json()
        if "error" in g:
            raise SystemExit(f"04g: service error: {g['error']}")
        feats += g.get("features", [])
        if not (g.get("exceededTransferLimit") or g.get("properties", {}).get("exceededTransferLimit")):
            break
        offset = len(feats)
    for f in feats:                       # epoch milliseconds -> ISO dates, in UTC as published
        for k in ("ALARM_DATE", "CONT_DATE"):
            v = f["properties"].get(k)
            f["properties"][k] = (datetime.datetime.fromtimestamp(v / 1000, datetime.timezone.utc).date().isoformat()
                                  if isinstance(v, (int, float)) else None)
    return {"type": "FeatureCollection", "features": feats}


def main():
    import geopandas as gpd
    import pandas as pd
    cfg = getattr(C, "FIRE_PERIMETERS", None)
    if not cfg:
        log(f"Phase 4g — fire perimeters | {C.CITY}: no FIRE_PERIMETERS in config.py, nothing to do")
        return
    log(f"Phase 4g — fire perimeters since {cfg['since_year']} | {C.CITY}")
    if FIRE_FILE.exists() and "--refresh" not in sys.argv:
        gj = json.loads(FIRE_FILE.read_text())
        log(f"  cached {FIRE_FILE.name} ({len(gj['features'])} perimeters) — --refresh to re-pull")
    else:
        gj = fetch(cfg)
        log(f"  fetched {len(gj['features'])} perimeters touching the bbox")

    hexes = gpd.read_file(C.GRID_FILE).to_crs(C.RASTER_CRS)[["h3", "geometry"]]
    out = pd.DataFrame({"h3": hexes["h3"].values, "fire": 0.0, "fire_name": "", "fire_year": ""})
    kept = []
    if gj["features"]:
        fires = gpd.GeoDataFrame.from_features(gj["features"], crs="EPSG:4326")
        fires["geometry"] = fires.geometry.make_valid()
        fires = fires[~fires.geometry.is_empty & fires.geometry.notna()]
        fires = fires[fires.geometry.geom_type.isin(("Polygon", "MultiPolygon"))].to_crs(C.RASTER_CRS)
        # Only fires that reach the study area itself, not merely its bounding box.
        if C.BOUNDARY_FILE.exists():
            study = gpd.read_file(C.BOUNDARY_FILE).to_crs(C.RASTER_CRS).geometry.union_all()
            fires = fires[fires.intersects(study)]
        fires = fires[fires.geometry.area >= float(cfg.get("min_km2", 0.0)) * 1e6].reset_index(drop=True)
        fires["label"] = fires["FIRE_NAME"].fillna("Unnamed").str.strip().str.title()
        if len(fires):
            area = hexes.set_index("h3").geometry.area
            union = fires.geometry.union_all()
            share = (hexes.set_index("h3").geometry.intersection(union).area / area).clip(0, 1)
            inter = gpd.overlay(hexes, fires[["label", "YEAR_", "geometry"]], how="intersection", keep_geom_type=True)
            inter["a"] = inter.geometry.area
            top = inter.sort_values("a").drop_duplicates("h3", keep="last").set_index("h3")
            hit = share[share >= MIN_SHARE].index
            out = out.set_index("h3")
            out.loc[hit, "fire"] = share.loc[hit].round(3)
            out.loc[hit, "fire_name"] = top["label"].reindex(hit).fillna("").values
            out.loc[hit, "fire_year"] = top["YEAR_"].reindex(hit).map(lambda v: "" if pd.isna(v) else str(int(v))).values
            out = out.reset_index()
            kept = json.loads(fires.drop(columns=["label"]).to_crs("EPSG:4326").to_json(drop_id=True))["features"]
    FIRE_FILE.write_text(json.dumps({"type": "FeatureCollection", "features": kept}))
    out.to_csv(FIRE_CSV, index=False)
    half = int((out["fire"] >= 0.5).sum())
    names = sorted({f"{r.fire_name} {r.fire_year}" for r in out[out["fire"] > 0].itertuples()})
    log(f"  {len(kept)} perimeters reach the study area ({', '.join(names) or 'none'}); "
        f"{half}/{len(out)} hexes mostly inside one, {int((out['fire'] > 0).sum())} touch one")
    log(f"  wrote {FIRE_FILE.relative_to(C.ROOT)} and {FIRE_CSV.relative_to(C.ROOT)}")

    from sources import record
    record("04g_fire", "Wildfire perimeters", cfg["service"], path=FIRE_FILE, count=len(kept),
           publisher=cfg.get("publisher", "CAL FIRE FRAP"),
           note=f"Perimeters of fires from {cfg['since_year']} on that reach the study area. "
                "A perimeter is the fire's outer line, not a map of what burned.")


if __name__ == "__main__":
    main()
