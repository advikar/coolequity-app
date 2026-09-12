"""Phase 4b — routed pedestrian walk time to the nearest cooling site.

Why this replaces the straight-line estimate (DATA_QUALITY.md W-1)
-----------------------------------------------------------------
04's `access_time` is a circuity-adjusted straight line: crow-fly distance to the
nearest cooling site × C.CIRCUITY (1.273, the grid-Manhattan ratio) ÷ walk speed.
Its documented failure mode is that a hex one freeway, creek or ridgeline away from
a site reads "close" — the straight line ignores barriers, and a fixed circuity
factor cannot know that suburban San Ramon's winding cul-de-sacs are far more
circuitous than a grid.

This module routes on the real OSM **pedestrian network** instead:

  * `osmnx` builds the walk graph for the study bbox (a freeway with no sidewalk is
    simply not in it, so it cannot be crossed; a footbridge over a creek is);
  * one multi-source Dijkstra from every cooling site gives each graph node its
    true network distance to the nearest site (fast — one pass for the whole grid);
  * door-to-door: the point→graph-node snap distance is added at BOTH ends (hex
    centroid and cooling site), and the result is floored at the straight-line
    distance (you cannot walk less than crow-fly), which removes snapping artefacts.

It is computed ONCE, offline, and written into overlays_<slug>.csv, so nothing
routes at demo time. The downloaded graph is cached to
data/_cache/walkgraph_<slug>.graphml so a rerun needs no network.

Validation before trusting it (per DATA_QUALITY.md follow-up 3): the log reports
the largest-connected-component share (should be ~1.0), the routed/crow-fly ratio
distribution (must be ≥1.0 everywhere), and the count of hexes that fell back to
the straight line. Any hex the pedestrian network cannot reach keeps the
straight-line estimate and is marked access_src="straightline".

Two defects found in the September 2026 build (a Bakersfield cell 1.1 km from a
site read 254 min; Contra Costa had 157 cells over 3x the straight line):

  * osmnx's default filter drops every way tagged access=private, i.e. all the
    streets inside gated and private subdivisions. A populated hex with no network
    inside it then snapped 500 m to a farm track that reached town by a 26 km loop.
    Residents can walk out of their own subdivision, so those streets are kept
    (WALK_ACCESS_FILTER) and the graph is re-downloaded to a *_v2 cache.
  * Snapping a point to its single nearest node picks a pocket path over a street
    a few metres further away. Each hex centroid and each site is now joined to
    its SNAP_K nearest nodes and the best door-to-door total wins.

What is still implausibly far (routed > DETOUR_RATIO x crow-fly AND more than
DETOUR_EXTRA_M beyond it) is flagged access_quality="detour-review". If such a
cell is also more than SNAP_MAX_M from any network node, or the network it joins
is a fragment (fewer than POCKET_MIN_NODES nodes within POCKET_RADIUS_M of its
node — Bakersfield's far-west cells sit in a 12-node pocket of farm tracks 150 m
away), the walking network does not really reach it: the routed figure is a
property of the nearest track, not of the cell, so the cell keeps the
straight-line estimate and says access_src="straightline". A flagged cell that IS on the network keeps its routed value —
that is a real barrier, and the flag tells the reader to check it.

Run:  ../.venv/bin/python 04b_routed_access.py   (after 04 has written overlays)
"""
import sys
import numpy as np

import config as C
from cooling_sources import eligible_discovery_sites

MARGIN_DEG = 0.02           # pull the graph a little past the bbox so edge hexes
                            # can route to a just-outside site and border routes
                            # are not artificially truncated
# No blanket access filter. osmnx's default drops access=private (every street in
# a gated subdivision); a naive access!=no drops pedestrian-only paths tagged
# access=no + foot=yes. The walk filter's own foot!~no rule is the one that
# matters for a pedestrian, so that is the only access rule applied.
WALK_ACCESS_FILTER = ''
SNAP_K = 8                  # candidate network nodes per point; best total wins
DETOUR_RATIO = 3.0          # flag routed > 3x crow-fly ...
DETOUR_EXTRA_M = 1500       # ... and more than 1.5 km beyond it
SNAP_MAX_M = 500            # flagged AND further than this from the network: off-network
POCKET_RADIUS_M = 2000      # flagged AND fewer than POCKET_MIN_NODES nodes within this
POCKET_MIN_NODES = 40       # walking distance of the cell's node: a fragment, not a network
GRAPH_CACHE = C.CACHE / f"walkgraph_{C.SLUG}_v2.graphml"


def log(msg):
    print(msg, flush=True)


def build_graph():
    import osmnx as ox
    if GRAPH_CACHE.exists():
        log(f"  walk graph: loading cache {GRAPH_CACHE.name}")
        return ox.load_graphml(GRAPH_CACHE)
    w, s, e, n = C.BBOX
    ox.settings.default_access = WALK_ACCESS_FILTER
    log(f"  walk graph: downloading OSM pedestrian network for bbox+{MARGIN_DEG}° "
        f"(~{(e-w)*88:.0f}×{(n-s)*111:.0f} km) — this is the slow step")
    G = ox.graph_from_bbox(bbox=(w - MARGIN_DEG, s - MARGIN_DEG,
                                 e + MARGIN_DEG, n + MARGIN_DEG),
                           network_type="walk")
    ox.save_graphml(G, GRAPH_CACHE)
    log(f"  walk graph: cached to {GRAPH_CACHE.relative_to(C.ROOT)}")
    return G


def detour_mask(routed_m, crow_m):
    """Routed distance implausibly far above the straight line: a real barrier or
    a map gap. NaN (unreachable) is never flagged here; it is handled as such."""
    routed_m = np.asarray(routed_m, dtype=float); crow_m = np.asarray(crow_m, dtype=float)
    return ~np.isnan(routed_m) & (routed_m > np.maximum(DETOUR_RATIO * crow_m, crow_m + DETOUR_EXTRA_M))


def finalize_access(routed_m, crow_m, snap_m, detour, pocket=None):
    """Decide per hex which estimate ships and how it is labelled.

    Returns (access_src, final_m, access_quality):
      * unreachable, or detour-flagged AND off-network (snap > SNAP_MAX_M, or the
        cell's node sits in a network fragment — `pocket`):
        straight line x circuity, access_src="straightline";
      * otherwise the routed value, access_src="routed";
      * access_quality: "detour-review" wherever flagged, else "approach-review"
        for a snap over 100 m, else "network-estimate".
    """
    routed_m = np.asarray(routed_m, dtype=float); crow_m = np.asarray(crow_m, dtype=float)
    snap_m = np.asarray(snap_m, dtype=float); detour = np.asarray(detour, dtype=bool)
    straight_m = crow_m * C.CIRCUITY
    unreach = np.isnan(routed_m)
    pocket = np.zeros_like(detour) if pocket is None else np.asarray(pocket, dtype=bool)
    offnet = detour & ((snap_m > SNAP_MAX_M) | pocket)
    src = np.where(unreach | offnet, "straightline", "routed")
    final_m = np.where(src == "straightline", straight_m, routed_m)
    # Compared as the rounded metres the CSV carries, so the flag and the number
    # a reader sees can never disagree at the boundary.
    quality = np.where(detour, "detour-review",
              np.where(np.round(snap_m, 0) > 100, "approach-review", "network-estimate"))
    return src, final_m, quality


def routed_meters(grid, centers_gj):
    """Door-to-door network metres from each hex centroid to the nearest cooling
    site. Returns (routed_m, crow_m, stats dict). routed_m is NaN where the network
    cannot reach the hex (caller falls back to the straight line)."""
    import geopandas as gpd
    import networkx as nx
    import osmnx as ox
    from shapely.geometry import shape
    from scipy.spatial import cKDTree

    cen = grid.to_crs(C.RASTER_CRS).geometry.centroid
    cpts = [shape(f["geometry"]) for f in centers_gj["features"]]
    cpt = gpd.GeoSeries(cpts, crs="EPSG:4326").to_crs(C.RASTER_CRS)

    G = build_graph()
    G = ox.project_graph(G, to_crs=C.RASTER_CRS)
    Gu = ox.convert.to_undirected(G)

    comps = sorted((len(c) for c in nx.connected_components(Gu)), reverse=True)
    lcc = comps[0] / Gu.number_of_nodes() if Gu.number_of_nodes() else 0
    log(f"  graph: {Gu.number_of_nodes()} nodes, {Gu.number_of_edges()} edges, "
        f"largest component {lcc:.3f} of nodes")

    # Candidate nodes: the SNAP_K nearest to each point, not just the nearest.
    # The nearest node can sit on an isolated footpath while a real street is a
    # few metres further; taking the best (snap + network) total over several
    # candidates removes that artefact without any hand-tuned threshold.
    node_ids = np.array(list(Gu.nodes), dtype=object)
    node_xy = np.column_stack([[Gu.nodes[n]["x"] for n in node_ids],
                               [Gu.nodes[n]["y"] for n in node_ids]])
    ntree = cKDTree(node_xy)
    k = min(SNAP_K, len(node_ids))
    c_d, c_i = ntree.query(np.column_stack([cpt.x.values, cpt.y.values]), k=k)
    h_d, h_i = ntree.query(np.column_stack([cen.x.values, cen.y.values]), k=k)
    c_d, c_i, h_d, h_i = (np.atleast_2d(a) for a in (c_d, c_i, h_d, h_i))

    # Virtual super-source joined to each site's candidate nodes with edge weight
    # = that straight-line snap, so a single Dijkstra returns, for every node, the
    # minimum over sites of (site_snap + network_distance). Gu is a MultiGraph, so
    # two sites snapping to one node just add parallel edges — Dijkstra takes the
    # smaller, which is exactly what we want; no manual dedup needed.
    SRC = "__cooling_src__"
    Gu.add_node(SRC)
    for drow, irow in zip(c_d, c_i):
        for sd, ni in zip(drow, irow):
            Gu.add_edge(SRC, node_ids[ni], length=float(sd))
    dist = nx.single_source_dijkstra_path_length(Gu, SRC, weight="length")

    # Per hex: best door-to-door total over its candidates; remember which snap
    # produced it so access_snap_m describes the connection actually used.
    routed_m = np.full(len(cen), np.nan)
    hx_snap = h_d[:, 0].astype(float).copy()          # nearest, for the unreachable
    best_node = h_i[:, 0].copy()
    for r in range(len(cen)):
        tot = np.array([dist.get(node_ids[ni], np.nan) + sd
                        for sd, ni in zip(h_d[r], h_i[r])], dtype=float)
        if np.isfinite(tot).any():
            j = int(np.nanargmin(tot))
            routed_m[r] = tot[j]
            hx_snap[r] = float(h_d[r][j])
            best_node[r] = h_i[r][j]

    tree = cKDTree(np.column_stack([cpt.x.values, cpt.y.values]))
    crow_m, _ = tree.query(np.column_stack([cen.x.values, cen.y.values]))
    # physical floor: a walk cannot be shorter than the straight line
    routed_m = np.where(np.isnan(routed_m), np.nan, np.maximum(routed_m, crow_m))

    ok = ~np.isnan(routed_m)
    ratio = routed_m[ok] / np.maximum(crow_m[ok], 1.0)
    detour = detour_mask(routed_m, crow_m)
    # Only flagged hexes need the fragment test: how much network is within
    # walking reach of the node the hex was joined to?
    pocket = np.zeros(len(cen), dtype=bool)
    for r in np.flatnonzero(detour):
        n_reach = len(nx.single_source_dijkstra_path_length(
            Gu, node_ids[best_node[r]], weight="length", cutoff=POCKET_RADIUS_M))
        pocket[r] = n_reach < POCKET_MIN_NODES
    stats = dict(lcc=lcc, reachable=int(ok.sum()), total=int(len(ok)),
                 ratio_med=float(np.median(ratio)) if ok.any() else float("nan"),
                 ratio_min=float(ratio.min()) if ok.any() else float("nan"),
                 ratio_p90=float(np.percentile(ratio, 90)) if ok.any() else float("nan"),
                 ratio_max=float(ratio.max()) if ok.any() else float("nan"),
                 detour=int(detour.sum()), detour_mask=detour, pocket_mask=pocket,
                 snap_p95=float(np.percentile(hx_snap, 95)),
                 hex_snap_m=np.asarray(hx_snap,dtype=float).tolist())
    return routed_m, crow_m, stats


def main():
    import geopandas as gpd
    import pandas as pd
    import json

    log(f"Phase 4b — routed walk time | {C.CITY}")
    if not C.OVERLAYS_CSV.exists():
        raise SystemExit(f"\nNo {C.OVERLAYS_CSV.name}; run 04 first.")
    if not C.CENTERS_FILE.exists():
        raise SystemExit(f"\nNo {C.CENTERS_FILE.name}; run 04 first.")

    grid = gpd.read_file(C.GRID_FILE)[["h3", "geometry"]]
    centers = eligible_discovery_sites(json.loads(C.CENTERS_FILE.read_text()))
    log(f"  {len(grid)} hexes, {len(centers['features'])} cooling sites")

    routed_m, crow_m, st = routed_meters(grid, centers)
    log(f"  connectivity {st['lcc']:.3f} | reachable {st['reachable']}/{st['total']} "
        f"| routed/crow-fly ratio med {st['ratio_med']:.2f} min {st['ratio_min']:.2f} "
        f"p90 {st['ratio_p90']:.2f} max {st['ratio_max']:.2f} | hex snap p95 {st['snap_p95']:.0f} m "
        f"| detour-review {st['detour']}")
    if st["ratio_min"] < 0.999:
        raise SystemExit("  ABORT: routed < crow-fly somewhere — snapping bug, not shipping.")
    if st["lcc"] < 0.90:
        log("  !! WARNING: walk graph is fragmented (largest component < 90%); "
            "many hexes will fall back to the straight line. Review before shipping.")

    # Fall back to the straight-line estimate where the network cannot reach the
    # site, or does not reach the cell (detour-flagged AND off-network).
    snap = np.asarray(st["hex_snap_m"], dtype=float)
    src, final_m, quality = finalize_access(routed_m, crow_m, snap, st["detour_mask"], st["pocket_mask"])
    unreach = np.isnan(routed_m)
    offnet = (src == "straightline") & ~unreach
    km = final_m / 1000.0
    mins = km / C.WALK_SPEED_KMH * 60.0
    if unreach.any():
        log(f"  {int(unreach.sum())} hex(es) unreachable on foot — kept the straight-line estimate")
    if offnet.any():
        log(f"  {int(offnet.sum())} hex(es) detour-flagged and off-network (>{SNAP_MAX_M} m snap, or a "
            f"fragment of <{POCKET_MIN_NODES} nodes within {POCKET_RADIUS_M} m) — straight-line estimate, flagged detour-review")
    kept = int((st["detour_mask"] & ~offnet).sum())
    if kept:
        log(f"  {kept} hex(es) detour-flagged on the network — routed value kept, flagged detour-review")

    ov = pd.read_csv(C.OVERLAYS_CSV)
    order = pd.Series(np.arange(len(grid)), index=grid["h3"].values)
    idx = ov["h3"].map(order)                    # align by h3, not row order
    ov["access_min"] = np.round(mins[idx.values], 1)
    ov["access_km"] = np.round(km[idx.values], 2)
    ov["access_src"] = src[idx.values]
    ov["access_snap_m"] = np.round(np.asarray(st["hex_snap_m"])[idx.values], 0)
    # Review flags, not a safe/unsafe route classification. Short snaps also need
    # pedestrian validation; long straight approaches deserve explicit disclosure,
    # and a route far longer than the straight line says "barrier or map gap".
    ov["access_quality"] = quality[idx.values]
    ov.to_csv(C.OVERLAYS_CSV, index=False)
    log(f"  access: median {np.median(mins):.1f} min, max {np.max(mins):.1f} min "
        f"(routed). wrote {C.OVERLAYS_CSV.relative_to(C.ROOT)}")
    log("  re-run 05_score.py to propagate into the geojson.")


if __name__ == "__main__":
    main()
