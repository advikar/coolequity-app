"""Phase 4d — which city or unincorporated community each cell is in.

A planner reads the map by jurisdiction before anything else: "show me my
city". Generated cell names (nearest mapped place plus a compass suffix) do not
answer that, and the audit asked for a stable municipality per cell alongside
the cell id. This step fetches Census TIGERweb place polygons for the study
bbox and assigns every cell the place that contains its centroid:

    incorporated city (layer 4)  ->  city = "Richmond",   city_kind = "city"
    census-designated place (5)  ->  city = "Bay Point",  city_kind = "cdp"
    neither                      ->  city = "Unincorporated", city_kind = "none"

Cities win over CDPs where both contain the point (they should not overlap,
but TIGERweb edges are not perfectly clean). Centroid assignment means a cell
on a city line is attributed to one side; the cell is 0.04–0.3 sq mi, so that
is the precision of the label and the guide says so.

    COOLEQUITY_CITY=contracosta python pipeline/04d_jurisdiction.py

Writes:  data/jurisdiction_<slug>.csv           h3, city, city_kind, city_geoid
         data/jurisdictions_<slug>.geojson      the place outlines actually used,
                                                for the map's boundary layer
Network: TIGERweb (public, no key); the raw response is cached in
         data/_cache/tigerweb_places_<slug>.json.
"""
import json
import sys
import time
import urllib.parse
import urllib.request

import config as C

BASE = ("https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/"
        "Places_CouSub_ConCity_SubMCD/MapServer/{layer}/query?")
LAYERS = {4: "city", 5: "cdp"}
CACHE = C.CACHE / f"tigerweb_places_{C.SLUG}.json"
OUT_CSV = C.DATA / f"jurisdiction_{C.SLUG}.csv"
OUT_GJ = C.DATA / f"jurisdictions_{C.SLUG}.geojson"
COORD_DP = 5


def fetch(layer):
    w, s, e, n = C.BBOX
    q = urllib.parse.urlencode({
        "geometry": f"{w},{s},{e},{n}", "geometryType": "esriGeometryEnvelope", "inSR": "4326",
        "spatialRel": "esriSpatialRelIntersects", "where": f"STATE='{C.STATE_FIPS}'",
        "outFields": "GEOID,BASENAME,NAME", "returnGeometry": "true", "outSR": "4326", "f": "geojson"})
    req = urllib.request.Request(BASE.format(layer=layer) + q, headers={"User-Agent": "CoolEquity (student project)"})
    for attempt in range(3):
        try:
            return json.load(urllib.request.urlopen(req, timeout=120))
        except Exception as ex:  # TIGERweb drops connections now and then; try again, then fail loudly
            print(f"    layer {layer} attempt {attempt + 1} failed: {ex}", file=sys.stderr)
            time.sleep(5)
    raise SystemExit(f"04d: TIGERweb layer {layer} unavailable; refusing to write a partial jurisdiction file")


def rounded(coords):
    if isinstance(coords[0], (int, float)):
        return [round(coords[0], COORD_DP), round(coords[1], COORD_DP)]
    return [rounded(c) for c in coords]


def main():
    import pandas as pd
    from shapely.geometry import shape
    from shapely.strtree import STRtree
    print(f"Phase 4d — jurisdiction | {C.CITY}")
    if CACHE.exists():
        raw = json.loads(CACHE.read_text())
        print(f"  places: cached {CACHE.name}")
    else:
        raw = {str(layer): fetch(layer) for layer in LAYERS}
        CACHE.parent.mkdir(exist_ok=True)
        CACHE.write_text(json.dumps(raw))
        print("  places: fetched TIGERweb layers 4 (cities) and 5 (CDPs)")
    places = []
    for layer, kind in LAYERS.items():
        for f in raw[str(layer)].get("features", []):
            places.append({"name": f["properties"]["BASENAME"], "kind": kind,
                           "geoid": f["properties"]["GEOID"], "geom": shape(f["geometry"]), "feature": f})
    print(f"  {sum(p['kind']=='city' for p in places)} cities and {sum(p['kind']=='cdp' for p in places)} CDPs touch the bbox")

    grid = json.loads(C.GRID_FILE.read_text())
    geoms = [p["geom"] for p in places]
    tree = STRtree(geoms)
    rows, used = [], set()
    for f in grid["features"]:
        pt = shape(f["geometry"]).centroid
        hits = [places[i] for i in tree.query(pt) if geoms[i].contains(pt)]
        hits.sort(key=lambda p: 0 if p["kind"] == "city" else 1)
        if hits:
            p = hits[0]
            used.add(id(p))
            rows.append({"h3": f["properties"]["h3"], "city": p["name"], "city_kind": p["kind"], "city_geoid": p["geoid"]})
        else:
            rows.append({"h3": f["properties"]["h3"], "city": "Unincorporated", "city_kind": "none", "city_geoid": None})
    df = pd.DataFrame(rows)
    df.to_csv(OUT_CSV, index=False)
    counts = df["city"].value_counts()
    print(f"  assigned: {len(counts)} jurisdictions; top: " + ", ".join(f"{k} {v}" for k, v in counts.head(8).items()))
    feats = []
    for p in places:
        if id(p) not in used:
            continue
        g = p["feature"]["geometry"]
        feats.append({"type": "Feature",
                      "properties": {"name": p["name"], "kind": p["kind"], "geoid": p["geoid"]},
                      "geometry": {"type": g["type"], "coordinates": rounded(g["coordinates"])}})
    OUT_GJ.write_text(json.dumps({"type": "FeatureCollection",
                                  "properties": {"source": "Census TIGERweb Places_CouSub_ConCity_SubMCD layers 4 and 5",
                                                 "fetched": time.strftime("%Y-%m-%d"),
                                                 "assignment": "cell centroid within polygon; cities before CDPs"},
                                  "features": feats}))
    print(f"  wrote {OUT_CSV.relative_to(C.ROOT)} and {OUT_GJ.relative_to(C.ROOT)} "
          f"({len(feats)} outlines, {OUT_GJ.stat().st_size/1e6:.1f} MB)")


if __name__ == "__main__":
    main()
