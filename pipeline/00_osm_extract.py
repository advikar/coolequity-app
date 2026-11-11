"""Phase 0 (optional) — OpenStreetMap inputs from a downloaded extract, not Overpass.

Why this exists
---------------
02b, 04 and 04b fetch their OpenStreetMap inputs live from the public Overpass
instances: every building in the bbox, every plantable street, the place names
and the whole pedestrian network. For a town that is a few megabytes. For the
City of Los Angeles it is over a gigabyte of JSON in dozens of requests, on
servers that ask automated clients not to do that and, on the Los Angeles build
day, answered "at capacity" to all of them.

This stage reads the same data from a regional `.osm.pbf` extract on disk and
writes the files those three stages already treat as their caches, so they then
run exactly as they do for every other city, with no network:

    buildings_<slug>.geojson            02b's output (same residential rule, size
                                        filter and centroid file, via 02b's code)
    streets_<slug>.geojson              04's plantable street centrelines
    places_<slug>.geojson               04's place nodes and named areas (04's parser)
    _cache/walkgraph_<slug>_v2.graphml  04b's pedestrian graph (osmnx, same walk
                                        filter, truncation and simplification)

The tag rules are the Overpass queries of 02b, 04 and osmnx's "walk" network
type, applied locally; a way belongs to a bounding box when any of its nodes is
inside it, which is how Overpass selects ways. The one input this stage does
not produce is the cooling-site inventory (centers_<slug>.geojson): that query
is small, uses relations, and 04 fetches it as before.

One snapshot, one date: every OpenStreetMap-derived number in the build then
comes from the same extract, and sources.json records its name and hash.

    pip install osmium          # pyosmium; not in requirements.txt, only this stage needs it
    COOLEQUITY_CITY=losangeles python pipeline/00_osm_extract.py \\
        --pbf /path/to/socal-latest.osm.pbf [--skip-graph]

Extracts: https://download.geofabrik.de/ (the California sub-regions are a few
hundred megabytes each and are rebuilt daily).
"""
import argparse
import json
import re
import sys
from pathlib import Path

import config as C

sys.path.insert(0, str(C.ROOT / "pipeline"))
buildings02b = __import__("02b_buildings")
overlays = __import__("04_overlays")
routed = __import__("04b_routed_access")

PLACE_RE = re.compile(r"^(neighbourhood|suburb|quarter|borough|city|town|village)$")
STREET_RE = re.compile(r"^(residential|tertiary|unclassified|living_street|secondary)$")
# osmnx 2.x "walk" network filter, with the project's access rule (none: see
# WALK_ACCESS_FILTER in 04b). Overpass `!~` is an unanchored regex search and
# passes when the key is absent, so the same is done here.
WALK_HIGHWAY_NOT = re.compile(r"abandoned|bus_guideway|construction|cycleway|motor|no|planned|"
                              r"platform|proposed|raceway|razed|rest_area|services")
WALK_NOT = (("area", re.compile("yes")), ("foot", re.compile("no")), ("service", re.compile("private")),
            ("sidewalk", re.compile("separate")), ("sidewalk:both", re.compile("separate")),
            ("sidewalk:left", re.compile("separate")), ("sidewalk:right", re.compile("separate")))
GRAPH_BUFFER_M = 500      # osmnx downloads this far past the polygon before truncating


def log(msg):
    print(msg, flush=True)


def is_walk(tags):
    hw = tags.get("highway")
    if hw is None or WALK_HIGHWAY_NOT.search(hw):
        return False
    return not any(k in tags and rx.search(tags[k]) for k, rx in WALK_NOT)


def box(margin):
    w, s, e, n = C.BBOX
    return (w - margin, s - margin, e + margin, n + margin)


def touches(coords, b):
    w, s, e, n = b
    return any(w <= x <= e and s <= y <= n for x, y in coords)


def walk_polygons():
    """The polygon osmnx.graph_from_bbox would use, and its 500 m buffer."""
    from shapely.geometry import box as sbox
    from osmnx import projection
    poly = sbox(*box(routed.MARGIN_DEG))
    proj, crs = projection.project_geometry(poly)
    buff, _ = projection.project_geometry(proj.buffer(GRAPH_BUFFER_M), crs=crs, to_latlong=True)
    return poly, buff


def scan(pbf, want_graph):
    """One pass over the ways (node locations resolved by pyosmium), one over the
    tagged place nodes. Returns everything the writers below need."""
    import osmium
    from osmium import filter as of
    b_build, b_city = box(C.BUILDINGS_MARGIN_DEG), box(0.0)
    poly, buff = walk_polygons()
    b_walk = buff.bounds
    named_areas = getattr(C, "NAME_FROM_LANDUSE", False)

    rows, streets, place_els = [], [], []
    walk_ways, walk_nodes = [], {}
    n_build = 0
    fp = (osmium.FileProcessor(str(pbf)).with_locations()
          .with_filter(of.EntityFilter(osmium.osm.WAY))
          .with_filter(of.KeyFilter("building", "highway", "landuse", "leisure")))
    for i, w in enumerate(fp):
        tags = w.tags
        bt, hw = tags.get("building"), tags.get("highway")
        area = named_areas and "name" in tags and (
            tags.get("landuse") == "residential" or tags.get("leisure") == "park")
        if bt is None and hw is None and not area:
            continue
        try:
            coords = [(n.lon, n.lat) for n in w.nodes]
        except osmium.InvalidLocationError:
            continue                  # a node outside the extract: the way is not in this region
        if bt is not None and touches(coords, b_build):
            n_build += 1
            row = buildings02b.footprint(bt, coords)
            if row:
                rows.append(row)
        if hw is not None:
            if STREET_RE.match(hw) and touches(coords, b_city) and len(coords) >= 2:
                streets.append({"type": "Feature", "properties": {"hw": hw},
                                "geometry": {"type": "LineString",
                                             "coordinates": [[round(x, 5), round(y, 5)] for x, y in coords]}})
            if want_graph and touches(coords, b_walk):
                t = {tg.k: tg.v for tg in tags}
                if is_walk(t):
                    refs = [n.ref for n in w.nodes]
                    walk_ways.append({"type": "way", "id": w.id, "nodes": refs, "tags": t})
                    for r, (x, y) in zip(refs, coords):
                        walk_nodes[r] = (y, x)
        if area and touches(coords, b_city):
            place_els.append({"type": "way", "id": w.id, "tags": {tg.k: tg.v for tg in tags},
                              "geometry": [{"lon": x, "lat": y} for x, y in coords]})
        if i and i % 2_000_000 == 0:
            log(f"    {i:,} candidate ways read; {len(rows):,} residential footprints, "
                f"{len(streets):,} streets, {len(walk_ways):,} walkable ways")

    w0, s0, e0, n0 = b_city
    for n in (osmium.FileProcessor(str(pbf), osmium.osm.NODE)
              .with_filter(of.KeyFilter("place"))):
        tags = n.tags
        if "name" in tags and PLACE_RE.match(tags.get("place", "")) \
                and w0 <= n.location.lon <= e0 and s0 <= n.location.lat <= n0:
            place_els.append({"type": "node", "id": n.id, "lat": n.location.lat, "lon": n.location.lon,
                              "tags": {tg.k: tg.v for tg in tags}})
    log(f"  read: {n_build:,} buildings in the box ({len(rows):,} residential-tagged), "
        f"{len(streets):,} plantable streets, {len(place_els):,} name anchors, "
        f"{len(walk_ways):,} walkable ways on {len(walk_nodes):,} nodes")
    return rows, streets, place_els, walk_ways, walk_nodes, (poly, buff)


def build_graph(walk_ways, walk_nodes, polys):
    """osmnx.graph_from_polygon's own steps after the download, on local data."""
    import networkx as nx
    import osmnx as ox
    from osmnx import graph as oxg, simplification, stats, truncate
    poly, buff = polys
    elements = [{"type": "node", "id": i, "lat": la, "lon": lo} for i, (la, lo) in walk_nodes.items()]
    elements += walk_ways
    G_buff = oxg._create_graph([{"elements": elements}], bidirectional=True)
    del elements
    log(f"  walk graph: {len(G_buff):,} raw nodes before truncation and simplification")
    G_buff = truncate.truncate_graph_polygon(G_buff, buff, truncate_by_edge=False)
    G_buff = truncate.largest_component(G_buff, strongly=False)
    G_buff = simplification.simplify_graph(G_buff)
    G = truncate.truncate_graph_polygon(G_buff, poly, truncate_by_edge=False)
    G = truncate.largest_component(G, strongly=False)
    nx.set_node_attributes(G, values=stats.count_streets_per_node(G_buff, nodes=G.nodes), name="street_count")
    routed.GRAPH_CACHE.parent.mkdir(exist_ok=True)
    ox.save_graphml(G, routed.GRAPH_CACHE)
    log(f"  walk graph: {len(G):,} nodes, {len(G.edges):,} edges -> {routed.GRAPH_CACHE.relative_to(C.ROOT)}")
    return len(G)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pbf", type=Path, required=True, help="regional .osm.pbf extract covering the bbox")
    ap.add_argument("--url", default=None, help="where the extract was downloaded from, for sources.json")
    ap.add_argument("--skip-graph", action="store_true", help="do not rebuild the pedestrian graph")
    a = ap.parse_args()
    if not a.pbf.exists():
        raise SystemExit(f"no extract at {a.pbf}")
    log(f"Phase 0 — OpenStreetMap from a local extract | {C.CITY} | {a.pbf.name}")
    rows, streets, place_els, walk_ways, walk_nodes, polys = scan(a.pbf, not a.skip_graph)
    if not rows or not streets or not place_els:
        raise SystemExit("the extract returned no buildings, streets or places for this bbox; wrong region?")

    buildings02b.write_buildings(rows)
    del rows

    C.STREETS_FILE.write_text(json.dumps({"type": "FeatureCollection", "features": streets}))
    log(f"  wrote {C.STREETS_FILE.relative_to(C.ROOT)} ({C.STREETS_FILE.stat().st_size/1e6:.1f} MB)")

    # 04's own parser, fed the local elements instead of an Overpass response.
    live = overlays.overpass
    overlays.overpass = lambda oql, label: place_els
    try:
        places = overlays.fetch_places()
    finally:
        overlays.overpass = live
    C.PLACES_FILE.write_text(json.dumps(places))
    log(f"  wrote {C.PLACES_FILE.relative_to(C.ROOT)} ({len(places['features'])} features)")

    n_graph = None if a.skip_graph else build_graph(walk_ways, walk_nodes, polys)

    from sources import record, sha256_12
    url = a.url or "https://download.geofabrik.de/"
    note = (f"Extract {a.pbf.name} (SHA-256 {sha256_12(a.pbf)}…), read locally by 00_osm_extract.py with the tag "
            "rules of the Overpass queries in 02b and 04 and osmnx's walk filter. © OpenStreetMap contributors, ODbL.")
    record("00_osm_extract", "Residential building footprints (OpenStreetMap)", url, path=C.BUILDINGS_FILE,
           count=len(json.loads(C.BUILDINGS_FILE.read_text())["features"]),
           publisher="OpenStreetMap contributors, via Geofabrik", note=note)
    record("00_osm_extract", "Plantable street centrelines (OpenStreetMap)", url, path=C.STREETS_FILE,
           count=len(streets), publisher="OpenStreetMap contributors, via Geofabrik")
    record("00_osm_extract", "Place names and named areas (OpenStreetMap)", url, path=C.PLACES_FILE,
           count=len(places["features"]), publisher="OpenStreetMap contributors, via Geofabrik")
    if n_graph:
        record("00_osm_extract", "Pedestrian network (OpenStreetMap)", url, count=n_graph,
               publisher="OpenStreetMap contributors, via Geofabrik",
               note="Graph nodes after simplification; cached outside the repository (_cache/).")


if __name__ == "__main__":
    main()
