"""Phase 4i (optional) — name each hex by its cross streets.

04 names a hex after the nearest mapped place. Where OpenStreetMap has few place
nodes that produces names nobody uses: in Bakersfield, hundreds of cells were
"Village at Lakeside E 21", the twenty-first cell east of one apartment complex.
City staff, council offices and residents locate things by cross streets, so
where a city publishes its street centrelines with names and a road class this
stage names every hex that way instead:

    name    the street intersection inside the hex ("Ming Ave & Stine Rd"),
            preferring the one made of the most major streets, then the one
            nearest the centre. A hex with no intersection inside it is named
            from the nearest one: "N of Akers Rd & Planz Rd", with the distance
            once it is more than a quarter mile ("0.6 mi NE of ...").
    near    the nearest intersection of two through streets (arterial, highway
            or collector, at least one of them arterial or highway), the way a
            location is given over the phone: "0.3 mi SW of Ming Ave & Stine Rd".
            Empty where the name already is that intersection.

Names are unique: two hexes cannot contain the same intersection, and a
direction-and-distance name that collides gets the distance, then a letter.

An intersection is a point where at least three segment ends of two or more
differently named streets meet. Two ends meeting is a street changing its name
(Coffee Rd becoming Gosford Rd), not a crossing, and neither is a street meeting
itself under another prefix (E Hosking Ave and Hosking Ave). Ramps, freeways (they cross other streets on
bridges), unbuilt and unnamed streets are left out.

Gated by NAME_STREETS in the city's config.py. Run after 01; 05 merges the CSV
and these names replace 04's.

    COOLEQUITY_CITY=bakersfield python pipeline/04i_street_names.py [--refresh]
"""
import json
import math
import sys
from collections import defaultdict

import config as C

OUT_CSV = C.NAMES_CSV
CACHE = C.DATA / f"street_names_{C.SLUG}.geojson"
SNAP_M = 1.5               # segment ends closer than this are one point
QUARTER_MILE_M = 402.0
DIRS = ("N", "NE", "E", "SE", "S", "SW", "W", "NW")
KEEP_UPPER = {"N", "S", "E", "W", "NE", "NW", "SE", "SW", "SR", "US", "CA", "II", "III"}


def log(msg):
    print(msg, flush=True)


def pretty(parts):
    """'S', 'H', 'ST', None -> 'S H St'; '24TH' -> '24th'; 'MCDONALD' -> 'McDonald'."""
    out = []
    tokens = " ".join(str(p).strip() for p in parts if p and str(p).strip()).split()
    # The city stores "MC KEE"; the street signs read "McKee".
    joined = []
    for token in tokens:
        if joined and joined[-1].upper() == "MC":
            joined[-1] = "MC" + token
        else:
            joined.append(token)
    # The city's name field sometimes already ends in the type ("VOYAGEURS DR" + "DR").
    while len(joined) > 2 and joined[-1].upper() == joined[-2].upper():
        joined.pop()
    for token in joined:
        t = token.upper()
        if t in KEEP_UPPER or len(t) == 1:
            out.append(t)
        elif any(ch.isdigit() for ch in t):
            out.append(t.lower())
        elif t.startswith("MC") and len(t) > 3:
            out.append("Mc" + t[2:].capitalize())
        else:
            out.append("-".join(w.capitalize() for w in t.split("-")))
    return " ".join(out)


def fetch(cfg):
    sys.path.insert(0, str(C.ROOT / "pipeline"))
    buildings = __import__("02b_buildings")
    f = cfg["fields"]
    w, s, e, n = C.BBOX
    m = 0.03
    feats = buildings.arcgis_all(cfg["service"], fields=",".join(v for v in f.values() if v),
                                 envelope=(w - m, s - m, e + m, n + m))
    out = []
    for ft in feats:
        p, g = ft["properties"], ft.get("geometry")
        if not g:
            continue
        name = pretty([p.get(f.get("prefix")), p.get(f["name"]), p.get(f.get("type")), p.get(f.get("suffix"))])
        out.append({"type": "Feature", "geometry": g,
                    "properties": {"street": name, "cls": (p.get(f["cls"]) or "").strip().upper()}})
    return {"type": "FeatureCollection", "source": cfg["service"], "features": out}


def compass(dx, dy):
    return DIRS[int(((math.degrees(math.atan2(dx, dy)) + 360 + 22.5) % 360) // 45)]


def offset_phrase(dx, dy):
    d = math.hypot(dx, dy)
    c = compass(dx, dy)
    return (f"{d / 1609.344:.1f} mi {c} of" if d > QUARTER_MILE_M else f"{c} of"), d


def main():
    import geopandas as gpd
    import numpy as np
    import pandas as pd
    from scipy.spatial import cKDTree
    from shapely.geometry import Point
    cfg = getattr(C, "NAME_STREETS", None)
    if not cfg:
        log(f"Phase 4i — street names | {C.CITY}: no NAME_STREETS in config.py, nothing to do")
        return
    log(f"Phase 4i — cross-street names | {C.CITY}")
    fresh = not CACHE.exists() or "--refresh" in sys.argv
    if fresh:
        gj = fetch(cfg)
        CACHE.write_text(json.dumps(gj))
        log(f"  fetched {len(gj['features']):,} street segments")
    else:
        gj = json.loads(CACHE.read_text())
        log(f"  cached: {len(gj['features']):,} street segments from {CACHE.relative_to(C.ROOT)}")

    rank = {}
    for c in cfg.get("major", ()):
        rank[c.upper()] = 0
    for c in cfg.get("collector", ()):
        rank[c.upper()] = 1
    skip = {c.upper() for c in cfg.get("skip", ())}
    st = gpd.GeoDataFrame.from_features(gj["features"], crs="EPSG:4326").to_crs(C.RASTER_CRS)
    st["street"] = st["street"].map(lambda v: pretty([v]))      # also tidies a cache written by an older rule
    st = st[st["street"].str.len().gt(0) & ~st["cls"].isin(skip) & st.geometry.notna()]
    st = st.explode(index_parts=False)
    st = st[st.geometry.geom_type == "LineString"]
    st["r"] = st["cls"].map(lambda c: rank.get(c, 3 if "PRIVATE" in c else 2))

    # Segment ends, snapped: a node carries every street that ends there and its best class.
    nodes, degree = defaultdict(dict), defaultdict(int)
    for geom, name, r in zip(st.geometry, st["street"], st["r"]):
        for x, y in (geom.coords[0], geom.coords[-1]):
            k = (round(x / SNAP_M), round(y / SNAP_M))
            degree[k] += 1
            if name not in nodes[k] or r < nodes[k][name][0]:
                nodes[k][name] = (r, x, y)

    def base(name):                     # "E Hosking Ave" and "Hosking Ave" are one street
        t = name.split()
        return " ".join(t[1:] if len(t) > 2 and t[0] in ("N", "S", "E", "W") else t)

    rows = []
    for k, streets in nodes.items():
        if degree[k] < 3:
            continue
        best, bases = [], set()
        for nm, v in sorted(streets.items(), key=lambda kv: (kv[1][0], kv[0])):
            if base(nm) not in bases:
                bases.add(base(nm))
                best.append((nm, v))
        if len(best) < 2:
            continue
        (a, (ra, x, y)), (b, (rb, _, _)) = best[:2]
        rows.append((x, y, f"{a} & {b}", ra, rb))
    ix = pd.DataFrame(rows, columns=["x", "y", "label", "ra", "rb"])
    ix["cost"] = ix["ra"] + ix["rb"]
    through = ix[(ix["ra"] == 0) & (ix["rb"] <= 1)].reset_index(drop=True)
    log(f"  {len(ix):,} intersections of named streets; {len(through):,} of two through streets")
    if len(ix) < 50 or len(through) < 5:
        raise SystemExit("04i: too few intersections; check NAME_STREETS field names and classes")

    hexes = gpd.read_file(C.GRID_FILE).to_crs(C.RASTER_CRS)[["h3", "geometry"]]
    pts = gpd.GeoDataFrame(ix, geometry=[Point(x, y) for x, y in zip(ix.x, ix.y)], crs=C.RASTER_CRS)
    hit = gpd.sjoin(pts, hexes, how="inner", predicate="within")
    cen = hexes.geometry.centroid
    cx, cy = dict(zip(hexes.h3, cen.x)), dict(zip(hexes.h3, cen.y))
    hit["d"] = np.hypot(hit.x - hit.h3.map(cx), hit.y - hit.h3.map(cy))
    hit = hit.sort_values(["cost", "d"])
    # Two streets can cross twice (a loop road). A hex takes its best intersection
    # whose label no better-placed hex has already taken, so labels stay unique
    # without numbering wherever the hex holds another intersection.
    taken, picks = set(), {}
    for h, grp in hit.groupby("h3", sort=False):
        picks[h] = grp
    order = sorted(picks, key=lambda h: (picks[h]["cost"].iloc[0], picks[h]["d"].iloc[0]))
    chosen = []
    for h in order:
        grp = picks[h]
        free = grp[~grp["label"].isin(taken)]
        row = (free if len(free) else grp).iloc[0]
        taken.add(row["label"])
        chosen.append(row)
    inside = pd.DataFrame(chosen).set_index("h3")

    tree_all, tree_thr = cKDTree(ix[["x", "y"]].to_numpy()), cKDTree(through[["x", "y"]].to_numpy())
    names, near, kind = {}, {}, {}
    for h in hexes.h3:
        x, y = cx[h], cy[h]
        if h in inside.index:
            names[h] = inside.at[h, "label"]
            kind[h] = "inside"
        else:
            _, j = tree_all.query([x, y])
            phrase, _d = offset_phrase(x - ix.at[j, "x"], y - ix.at[j, "y"])
            names[h] = f"{phrase} {ix.at[j, 'label']}"
            kind[h] = "nearest"
        _, j = tree_thr.query([x, y])
        t = through.loc[j]
        if h in inside.index and math.hypot(inside.at[h, "x"] - t.x, inside.at[h, "y"] - t.y) < 1.0:
            near[h] = ""                                   # the name already is that intersection
        else:
            inside_hex = hexes.geometry[hexes.h3 == h].iloc[0].contains(Point(t.x, t.y))
            phrase, d = offset_phrase(x - t.x, y - t.y)
            near[h] = t.label if inside_hex else f"{phrase} {t.label}"
        if near[h] == names[h]:
            near[h] = ""

    # Unique names. Collisions only arise among direction names; add the distance, then a letter.
    seen = defaultdict(list)
    for h, nm in names.items():
        seen[nm].append(h)
    fixed = 0
    for nm, hs in seen.items():
        if len(hs) < 2:
            continue
        for h in hs:
            if kind[h] != "nearest":
                continue
            _, j = tree_all.query([cx[h], cy[h]])
            dx, dy = cx[h] - ix.at[j, "x"], cy[h] - ix.at[j, "y"]
            names[h] = f"{math.hypot(dx, dy) / 1609.344:.2f} mi {compass(dx, dy)} of {ix.at[j, 'label']}"
            fixed += 1
    seen = defaultdict(list)
    for h, nm in names.items():
        seen[nm].append(h)
    for nm, hs in seen.items():
        if len(hs) > 1:
            for k, h in enumerate(sorted(hs)[1:], start=2):
                names[h] = f"{nm} ({k})"
                fixed += 1
    assert len(set(names.values())) == len(names), "names are not unique"

    out = pd.DataFrame({"h3": hexes.h3, "name": hexes.h3.map(names), "near": hexes.h3.map(near)})
    out.to_csv(OUT_CSV, index=False)
    n_in = sum(1 for v in kind.values() if v == "inside")
    log(f"  {n_in:,}/{len(out):,} hexes named by an intersection inside them, {len(out) - n_in:,} from the nearest one; "
        f"{fixed} names made unique")
    log(f"  wrote {OUT_CSV.relative_to(C.ROOT)}")
    if fresh:
        from sources import record
        record("04i_street_names", "Street centrelines (area names by cross streets)", cfg["service"], path=CACHE,
               count=len(gj["features"]), publisher=cfg.get("publisher"),
               note="Names and road class only; used to name each area by its cross streets, not for routing or street length.")


if __name__ == "__main__":
    main()
