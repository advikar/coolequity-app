"""Phase 4j (optional) — schools, bus stops and parks per hex: the places people go.

The ranking is about where people LIVE: a hex with no homes has no residents and
is not ranked. But people are out in the heat where they wait, walk and play,
and a city plants on land it controls: parks, streetscapes, civic frontages.
Bakersfield's program (Recreation and Parks) plants in city parks, along city
streetscapes and the Kern River Parkway, and its downtown corridor project is
about walkability, not housing. A map that only sees homes cannot point at a
bare bus stop on a commercial strip or a schoolyard with no shade.

Where a city publishes the layers (PLACES in its config.py), this stage counts,
per hex:

    schools       open schools whose point lies in the hex, and their names
    bus_stops     transit stops in the hex
    park          share of the hex's area inside a public park, 0-1, with the
                  park's name and whether the city itself owns it

and measures each place ITSELF, because the hex around a park can be bare
desert while the park is shaded, or the reverse:

    tree    tree cover, %: inside the park; inside the school's property (the
            city's school-property polygon, else 120 m around the point); within
            30 m of a bus stop, which is the shade a person waiting there gets.
            Counted on the USFS / CAL FIRE 2022 canopy raster (60 cm). Where
            that map does not cover at least 90% of the place, the place's own
            ground is read by the 02g model from the same 2022 aerial survey
            (tree_src "modelled"); only if that model is not on disk does the
            figure fall back to the surrounding hex's (tree_src "area").

Bus stops come in pairs, one each side of the street, under one name. Stops
sharing a name within 80 m of each other are one place, measured over both.
    heat    mean summer surface temperature over the same ground from the
            Landsat composite 02 wrote (30 m pixels, so a bus stop's figure is
            its block's, not the kerb's).

Writes people_places_<slug>.geojson, one point per place with those figures,
and people_places_<slug>.csv, the per-hex counts. Nothing here is scored. The
app lists the places by hot ground and missing tree cover alone.

    COOLEQUITY_CITY=bakersfield python pipeline/04j_places.py [--refresh]
"""
import json
import sys

import config as C

OUT_CSV = C.PLACES_CSV
OUT_PLACES = C.DATA / f"people_places_{C.SLUG}.geojson"
OUT_OUTLINES = C.DATA / f"people_places_outlines_{C.SLUG}.geojson"   # the ground each place was measured on
SCHOOL_RADIUS_M, STOP_RADIUS_M, HEAT_MIN_RADIUS_M = 120.0, 30.0, 45.0
STOP_PAIR_M = 80.0
STOP_NEAR_M = 15.0        # a second, tighter reading for bus stops: the shade right at the stop
MIN_ASSESSED = 0.90
CACHE = C.DATA / f"places_people_go_{C.SLUG}.geojson"
MAX_NAMES = 3


def log(msg):
    print(msg, flush=True)


ACRONYMS = {"JH", "HS", "MS", "ROP", "CSU", "CSUB", "KHSD", "BCSD", "PBVUSD", "NOR", "YMCA", "II", "III", "BHS"}


def title(s):
    """'WHITLEY (DOUGLAS S) ELEMENTARY' -> 'Whitley (Douglas S) Elementary'; known acronyms stay upper."""
    import re
    small = {"of", "and", "the", "at", "for", "de", "la", "del"}

    def one(m):
        w = m.group(0)
        if w.upper() in ACRONYMS:
            return w.upper()
        if w.lower() in small and m.start() > 0:
            return w.lower()
        if len(w) > 3 and w[:2].upper() == "MC":
            return "Mc" + w[2:3].upper() + w[3:].lower()
        return w[:1].upper() + w[1:].lower()
    return re.sub(r"[A-Za-z][A-Za-z']*", one, " ".join(str(s or "").split()))


def fetch(cfg):
    sys.path.insert(0, str(C.ROOT / "pipeline"))
    arc = __import__("02b_buildings").arcgis_all
    w, s, e, n = C.BBOX
    env = (w - .01, s - .01, e + .01, n + .01)
    feats = []
    sc = cfg.get("schools")
    if sc:
        closed = {v.upper() for v in sc.get("closed", ("CLOSED",))}
        skip = {v.upper() for v in sc.get("skip_types", ())}
        for f in arc(sc["service"], fields=",".join([sc["name"], sc["type"], sc["status"]]), envelope=env):
            p = f["properties"]
            if not f.get("geometry") or (p.get(sc["status"]) or "").strip().upper() in closed:
                continue
            if (p.get(sc["type"]) or "").strip().upper() in skip:
                continue
            feats.append({"type": "Feature", "geometry": f["geometry"],
                          "properties": {"kind": "school", "name": title(p.get(sc["name"])),
                                         "type": title(p.get(sc["type"]))}})
    if sc and sc.get("properties"):
        for f in arc(sc["properties"], fields="NAME", envelope=env):
            if f.get("geometry"):
                feats.append({"type": "Feature", "geometry": f["geometry"], "properties": {"kind": "school_property", "name": ""}})
    bs = cfg.get("bus_stops")
    if bs:
        for f in arc(bs["service"], fields=bs["name"], envelope=env):
            if f.get("geometry"):
                feats.append({"type": "Feature", "geometry": f["geometry"],
                              "properties": {"kind": "bus_stop", "name": " ".join(str(f["properties"].get(bs["name"]) or "").split())}})
    pk = cfg.get("parks")
    if pk:
        keep = {v.upper() for v in pk["types"]}
        private = {v.upper() for v in pk.get("private", ("PRIVATE",))}
        city = pk.get("city_owner", "").upper()
        for f in arc(pk["service"], fields=",".join([pk["name"], pk["type"], pk["owner"], pk["status"]]), envelope=env):
            p = f["properties"]
            owner = (p.get(pk["owner"]) or "").strip().upper()
            if (not f.get("geometry") or (p.get(pk["type"]) or "").strip().upper() not in keep
                    or owner in private or (p.get(pk["status"]) or "ACTIVE").strip().upper() != "ACTIVE"):
                continue
            feats.append({"type": "Feature", "geometry": f["geometry"],
                          "properties": {"kind": "park", "name": title(p.get(pk["name"])),
                                         "city_owned": bool(city) and owner == city}})
    return {"type": "FeatureCollection", "features": feats}


def main():
    import geopandas as gpd
    import pandas as pd
    cfg = getattr(C, "PLACES", None)
    if not cfg:
        log(f"Phase 4j — places people go | {C.CITY}: no PLACES in config.py, nothing to do")
        return
    log(f"Phase 4j — schools, bus stops and parks | {C.CITY}")
    fresh = not CACHE.exists() or "--refresh" in sys.argv
    if fresh:
        gj = fetch(cfg)
        CACHE.write_text(json.dumps(gj))
    else:
        gj = json.loads(CACHE.read_text())
    g = gpd.GeoDataFrame.from_features(gj["features"], crs="EPSG:4326").to_crs(C.RASTER_CRS)
    hexes = gpd.read_file(C.GRID_FILE).to_crs(C.RASTER_CRS)[["h3", "geometry"]]
    # Only what lies inside the study boundary: a school across the city line is not this city's frontage.
    if C.BOUNDARY_FILE.exists():
        study = gpd.read_file(C.BOUNDARY_FILE).to_crs(C.RASTER_CRS).geometry.union_all()
    else:
        study = hexes.geometry.union_all()
    out = pd.DataFrame({"h3": hexes.h3, "schools": 0, "school_names": "", "bus_stops": 0,
                        "park": 0.0, "park_name": "", "park_city": False}).set_index("h3")

    pts = g[g["kind"].isin(("school", "bus_stop")) & g.geometry.within(study)]
    hit = gpd.sjoin(pts, hexes, how="inner", predicate="within")
    sch = hit[hit["kind"] == "school"].drop_duplicates(["h3", "name"])
    out.loc[sch.groupby("h3").size().index, "schools"] = sch.groupby("h3").size().values
    names = sch.sort_values("name").groupby("h3")["name"].apply(
        lambda s: "; ".join(list(s)[:MAX_NAMES]) + (f"; +{len(s) - MAX_NAMES} more" if len(s) > MAX_NAMES else ""))
    out.loc[names.index, "school_names"] = names.values
    # A stop pair on opposite kerbs often shares a name; count the stops, not the names.
    bus = hit[hit["kind"] == "bus_stop"].groupby("h3").size()
    out.loc[bus.index, "bus_stops"] = bus.values

    parks = g[g["kind"] == "park"].copy()
    if len(parks):
        parks["geometry"] = parks.geometry.make_valid().intersection(study)
        parks = parks[~parks.geometry.is_empty]
        inter = gpd.overlay(hexes, parks[["name", "city_owned", "geometry"]], how="intersection", keep_geom_type=True)
        inter["a"] = inter.geometry.area
        share = (inter.dissolve(by="h3").geometry.area / hexes.set_index("h3").geometry.area).clip(upper=1.0)
        share = share[share >= 0.02]                       # a sliver of lawn at the hex edge is not a park in it
        top = inter.sort_values("a").drop_duplicates("h3", keep="last").set_index("h3")
        out.loc[share.index, "park"] = share.round(3).values
        out.loc[share.index, "park_name"] = top["name"].reindex(share.index).values
        out.loc[share.index, "park_city"] = top["city_owned"].reindex(share.index).astype(bool).values
    out.reset_index().to_csv(OUT_CSV, index=False)
    measure(g, hexes, study, cfg)
    kinds = g["kind"].value_counts().to_dict()
    any_place = (out.schools > 0) | (out.bus_stops > 0) | (out.park > 0)
    log(f"  fetched {kinds.get('school', 0)} open schools, {kinds.get('bus_stop', 0)} bus stops, {kinds.get('park', 0)} public parks in the box")
    log(f"  inside the study area: {int(out.schools.sum())} schools in {int((out.schools > 0).sum())} hexes, "
        f"{int(out.bus_stops.sum())} bus stops in {int((out.bus_stops > 0).sum())}, parks in {int((out.park > 0).sum())}; "
        f"{int(any_place.sum())}/{len(out)} hexes hold at least one")
    log(f"  wrote {OUT_CSV.relative_to(C.ROOT)}")
    if fresh:
        from sources import record
        for key, what in (("schools", "Schools"), ("bus_stops", "Bus stops"), ("parks", "Parks")):
            if cfg.get(key):
                k = {"schools": "school", "bus_stops": "bus_stop", "parks": "park"}[key]
                record("04j_places", f"{what} (places people go)", cfg[key]["service"], path=CACHE,
                       count=int(kinds.get(k, 0)), publisher=cfg[key].get("publisher"), note=cfg[key].get("note"))


def measure(g, hexes, study, cfg):
    """Tree cover and surface heat of each place itself -> people_places_<slug>.geojson."""
    import glob
    import geopandas as gpd
    import numpy as np
    import pandas as pd
    import rasterio
    from rasterio.features import geometry_mask
    from rasterio.windows import from_bounds

    props = g[g["kind"] == "school_property"]
    rows = []
    for kind in ("school", "bus_stop", "park"):
        sub = g[g["kind"] == kind]
        if kind == "park":
            sub = sub.copy()
            sub["geometry"] = sub.geometry.make_valid().intersection(study)
            # at least 2,000 m2 inside the study area: less is the corner of a park that lies in another jurisdiction
            sub = sub[~sub.geometry.is_empty & (sub.geometry.area >= 2000)]
            sub = sub.dissolve(by="name", as_index=False, aggfunc={"city_owned": "max", "kind": "first"})
        else:
            sub = sub[sub.geometry.within(study)]
            if kind == "school":
                sub = sub.drop_duplicates("name")
        for r in sub.itertuples():
            if kind == "park":
                foot, pt, how = r.geometry, r.geometry.representative_point(), "inside the park"
            elif kind == "school":
                inside = props[props.geometry.contains(r.geometry)] if len(props) else props
                pt = r.geometry
                if len(inside):
                    foot, how = inside.geometry.iloc[0].intersection(study), "on the school property"
                else:
                    foot, how = r.geometry.buffer(SCHOOL_RADIUS_M), f"within {SCHOOL_RADIUS_M:.0f} m of the school"
            else:
                continue                                    # bus stops are grouped below
            rows.append({"kind": kind, "name": r.name, "city_owned": bool(getattr(r, "city_owned", False)) if kind == "park" else None,
                         "foot": foot, "pt": pt, "how": how})
    # Bus stops: same name within STOP_PAIR_M = the two kerbs of one stop.
    stops = g[(g["kind"] == "bus_stop") & g.geometry.within(study)].reset_index(drop=True)
    seen = set()
    for i, r in stops.iterrows():
        if i in seen:
            continue
        near = stops[(stops["name"] == r["name"]) & (stops.geometry.distance(r.geometry) <= STOP_PAIR_M)]
        near = near[~near.index.isin(seen)]
        seen.update(near.index)
        pts_ = near.geometry.union_all()
        n = len(near)
        rows.append({"kind": "bus_stop", "name": r["name"], "city_owned": None, "stops": n, "near": pts_.buffer(STOP_NEAR_M),
                     "foot": pts_.buffer(STOP_RADIUS_M), "pt": pts_.centroid if n > 1 else r.geometry,
                     "how": f"within {STOP_RADIUS_M:.0f} m of the stop" + (f" (both sides, {n} stops)" if n > 1 else "")})
    P = gpd.GeoDataFrame(rows, geometry="foot", crs=C.RASTER_CRS)
    P["stops"] = P["stops"].fillna(1).astype(int) if "stops" in P else 1
    P["area_m2"] = P.geometry.area.round(0)

    # the hex each place's point is in: ward, designation and the fallback figures come from it
    pts = gpd.GeoDataFrame(P[["kind"]].copy(), geometry=list(P["pt"]), crs=C.RASTER_CRS)
    hit = gpd.sjoin(pts, hexes, how="left", predicate="within")
    P["h3"] = hit[~hit.index.duplicated()]["h3"].reindex(P.index).values
    can = pd.read_csv(C.CANOPY_CSV).set_index("h3")
    sat = pd.read_csv(C.SAT_CSV).set_index("h3")

    # tree cover on the USFS raster (EPSG:3310, 1 = canopy, everything else nodata)
    tifs = sorted(glob.glob(str(C.CACHE / "canopy_src" / "**" / "*_canopy2022.tif"), recursive=True))
    shps = sorted(glob.glob(str(C.CACHE / "canopy_src" / "**" / "*.shp"), recursive=True))
    if len(tifs) != 1 or len(shps) != 1:
        raise SystemExit("04j needs the USFS canopy raster and boundary in _cache/canopy_src (see 02d)")
    def cover(src, geom, bnd):
        inb = geom.intersection(bnd)
        if inb.is_empty or inb.area < MIN_ASSESSED * geom.area:
            return None
        win = from_bounds(*inb.bounds, transform=src.transform).round_offsets().round_lengths()
        if win.width < 1 or win.height < 1:
            return None
        arr = src.read(1, window=win)
        m = ~geometry_mask([inb], out_shape=arr.shape, transform=src.window_transform(win), invert=False)
        return float((arr[m] == 1).mean() * 100) if m.sum() >= 50 else None

    tree, src_lab, near = [], [], []
    with rasterio.open(tifs[0]) as src:
        bnd = gpd.read_file(shps[0]).to_crs(src.crs).geometry.union_all()
        feet = P.geometry.to_crs(src.crs)
        nears = gpd.GeoSeries([g_ if g_ is not None else None for g_ in P.get("near", [None] * len(P))], crs=C.RASTER_CRS).to_crs(src.crs) if "near" in P else [None] * len(P)
        for geom, h, ng in zip(feet, P["h3"], nears):
            val = cover(src, geom, bnd)
            nv = cover(src, ng, bnd) if ng is not None and not ng.is_empty else None
            near.append(None if nv is None else round(nv, 1))
            if val is None:
                v = can["canopy_pct"].get(h, np.nan) if isinstance(h, str) else np.nan
                tree.append(None if pd.isna(v) else round(float(v), 1))
                src_lab.append("area")
            else:
                tree.append(round(val, 1))
                src_lab.append("aerial")
    P["tree_near"] = near
    P["tree"], P["tree_src"] = tree, src_lab
    P = model_fill(P)

    heat = []
    with rasterio.open(C.LST_TIF) as src:
        feet = gpd.GeoSeries(list(P["pt"]), crs=C.RASTER_CRS).buffer(HEAT_MIN_RADIUS_M).union(P.geometry).to_crs(src.crs)
        for geom, h in zip(feet, P["h3"]):
            val = None
            win = from_bounds(*geom.bounds, transform=src.transform).round_offsets().round_lengths()
            if win.width >= 1 and win.height >= 1:
                arr = src.read(1, window=win, masked=True)
                m = ~geometry_mask([geom], out_shape=arr.shape, transform=src.window_transform(win), invert=False, all_touched=True)
                vals = arr[m].compressed() if hasattr(arr[m], "compressed") else arr[m]
                vals = vals[np.isfinite(vals)]
                if len(vals):
                    val = float(vals.mean())
            if val is None and isinstance(h, str):
                v = sat["lst_c"].get(h, np.nan)
                val = None if pd.isna(v) else float(v)
            heat.append(None if val is None else round(val, 2))
    P["heat"] = heat

    P = P[P["tree"].notna() & P["heat"].notna() & P["h3"].notna()]
    ll = gpd.GeoSeries(list(P["pt"]), crs=C.RASTER_CRS).to_crs("EPSG:4326")
    ids = dict(zip(gpd.read_file(C.GRID_FILE)["h3"], gpd.read_file(C.GRID_FILE)["id"]))
    feats = [{"type": "Feature", "geometry": {"type": "Point", "coordinates": [round(p.x, 6), round(p.y, 6)]},
              "properties": {"kind": r.kind, "name": r.name, "tree": r.tree, "tree_src": r.tree_src, "heat": r.heat,
                             "how": r.how, "area_m2": int(r.area_m2), "city_owned": r.city_owned,
                             "stops": int(r.stops) if r.kind == "bus_stop" else None,
                             "tree_near": None if pd.isna(r.tree_near) else float(r.tree_near), "cell": int(ids[r.h3])}}
             for p, r in zip(ll, P.itertuples())]
    OUT_PLACES.write_text(json.dumps({"type": "FeatureCollection", "features": feats}))
    # The measured ground itself, so the app can draw exactly what a figure describes: the park,
    # the school property, the 30 m circle(s) round a stop. `i` is the place's position above.
    shapes = P.geometry.simplify(1.5).to_crs("EPSG:4326")
    outl = [{"type": "Feature", "properties": {"i": i}, "geometry": json.loads(gpd.GeoSeries([g_]).set_precision(1e-6).to_json())["features"][0]["geometry"]}
            for i, g_ in enumerate(shapes)]
    OUT_OUTLINES.write_text(json.dumps({"type": "FeatureCollection", "features": outl}))
    log(f"  wrote {OUT_OUTLINES.relative_to(C.ROOT)} ({OUT_OUTLINES.stat().st_size / 1e6:.2f} MB)")
    by = P.groupby("kind").agg(n=("tree", "size"), tree=("tree", "median"), aerial=("tree_src", lambda s: int((s == "aerial").sum())))
    for k, r in by.iterrows():
        log(f"  {k}: {int(r.n)} measured, median tree cover {r.tree:.1f}%, {int(r.aerial)} from the aerial map directly")
    log(f"  wrote {OUT_PLACES.relative_to(C.ROOT)}")


def model_fill(P):
    """Places the USFS map does not cover: read their own ground with the 02g model, if it is on disk."""
    import pickle
    need = P.index[P["tree_src"] == "area"]
    try:
        naip = __import__("02g_canopy_naip")
        if not len(need) or not naip.MODEL.exists() or not getattr(C, "CANOPY_NAIP", None):
            return P
        with open(naip.MODEL, "rb") as fh:
            saved = pickle.load(fh)
        if saved.get("features") != naip.FEATURES:
            return P
    except Exception as e:                                   # noqa: BLE001 - scikit-learn absent, or no model
        log(f"  {len(need)} places past the USFS map keep the surrounding cell's figure ({type(e).__name__})")
        return P
    im = naip.Imagery(int(C.CANOPY_NAIP["year"]))
    feet = P.geometry.to_crs("EPSG:4326")
    nf, done = len(naip.FEATURES), 0
    for ix in need:
        a = naip.cell_arrays(im, feet[ix])
        if a is None or a["mask"].sum() < 50:
            continue
        p = saved["model"].predict_proba(a["X"].reshape(-1, nf)[a["mask"].ravel()])[:, 1]
        P.loc[ix, "tree"] = round(float(p.mean() * 100), 1)
        P.loc[ix, "tree_src"] = "modelled"
        done += 1
    log(f"  {done} of {len(need)} places past the USFS map read on their own ground by the 02g model")
    return P


if __name__ == "__main__":
    main()
