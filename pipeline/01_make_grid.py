"""Phase 1 — build the H3 hex grid that every later stage joins onto.

Hexes rather than admin boundaries: census tracts don't exist in most countries,
H3 does. This is what lets the same engine run on Lagos or Delhi unchanged.

Writes data/grid.geojson with: id, h3, area_m2, lat, lon.
"""
import json
import sys

import h3
import requests
from shapely.geometry import Polygon, shape

import config as C

# Clip polygon, from config so this file holds no city of its own. It mattered
# for LA because a raw basin bbox is ~20% Santa Monica Bay; it matters more for
# San Ramon, whose bbox corners sit in Danville, Dublin and open ranch land.
TIGERWEB = C.CLIP_URL
BOUNDARY_FILE = C.BOUNDARY_FILE


def load_boundary():
    """County polygon for land-clipping. Cached, then network, then None."""
    if BOUNDARY_FILE.exists():
        print(f"  boundary: cached {BOUNDARY_FILE.name}")
        return shape(json.loads(BOUNDARY_FILE.read_text())["features"][0]["geometry"])
    try:
        r = requests.get(TIGERWEB, timeout=30)
        r.raise_for_status()
        gj = r.json()
        if not gj.get("features"):
            raise ValueError("no features returned")
        BOUNDARY_FILE.write_text(json.dumps(gj))
        print(f"  boundary: fetched TIGERweb -> {BOUNDARY_FILE.name}")
        return shape(gj["features"][0]["geometry"])
    except Exception as e:
        # Non-fatal by design: an unclipped grid still demos, it just carries
        # some ocean hexes. Never let a network hiccup stop the pipeline.
        print(f"  boundary: UNAVAILABLE ({e}) — keeping full bbox grid", file=sys.stderr)
        return None


def cells_for_bbox(bbox, res):
    w, s, e, n = bbox
    # h3 v4 takes (lat, lng) pairs, counter-clockwise.
    ring = [(s, w), (s, e), (n, e), (n, w), (s, w)]
    return h3.h3shape_to_cells(h3.LatLngPoly(ring), res)


def cell_polygon(cell):
    # cell_to_boundary yields (lat, lng); GeoJSON wants (lng, lat).
    return Polygon([(lng, lat) for lat, lng in h3.cell_to_boundary(cell)])


def main():
    print(f"Phase 1 — H3 grid | {C.CITY} | res {C.H3_RES}")
    cells = cells_for_bbox(C.BBOX, C.H3_RES)
    print(f"  bbox cells: {len(cells)}")

    boundary = load_boundary()
    features = []
    for cell in sorted(cells):
        poly = cell_polygon(cell)
        if boundary is not None and not poly.intersects(boundary):
            continue
        lat, lon = h3.cell_to_latlng(cell)
        features.append({
            "type": "Feature",
            "properties": {
                "id": len(features),
                "h3": cell,
                # Real per-hex area — the ROI tree count and cost depend on it,
                # so it must not be a res-7 constant baked into the front end.
                "area_m2": round(h3.cell_area(cell, unit="m^2"), 1),
                "lat": round(lat, 6),
                "lon": round(lon, 6),
            },
            "geometry": json.loads(json.dumps(poly.__geo_interface__)),
        })

    if not features:
        raise SystemExit("No cells produced — check BBOX in config.py")

    C.GRID_FILE.write_text(json.dumps({"type": "FeatureCollection", "features": features}))
    areas = [f["properties"]["area_m2"] for f in features]
    print(f"  kept: {len(features)} hexes ({len(cells) - len(features)} dropped)")
    print(f"  area: ~{sum(areas)/len(areas)/1e6:.2f} km2/hex, "
          f"{sum(areas)/1e6:.0f} km2 total")
    print(f"  wrote {C.GRID_FILE.relative_to(C.ROOT)}")

    if len(features) > 3000:
        print(f"  NOTE: {len(features)} hexes may lag the browser — "
              f"consider H3_RES = {C.H3_RES - 1} in config.py", file=sys.stderr)


if __name__ == "__main__":
    main()
