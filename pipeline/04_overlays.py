"""Phase 4 — the story overlays, plus the names the demo actually talks in.

Three things the score itself can't say:
  * HOLC redlining grade  — why the map looks the way it does (US-only)
  * cooling centers       — where relief already exists
  * walk time to relief   — the access gap, which is the intervention argument

...and one thing the demo can't do without: a human name per hex. H3 cells have
none, and "Hex 2417 is the hottest place in LA" persuades nobody. Names come from
OSM place nodes rather than a US neighborhood file, because OSM has them for
Lagos and Delhi too — same reason the grid is H3 and not census tracts.

Fallback chain, per layer:
  1. live fetch (Mapping Inequality / Overpass)  ->  cached to data/*.geojson
  2. the committed data/*.geojson                ->  fully offline
  3. HOLC/names degrade to null; centers hard-stop (the access layer needs them)

Writes data/overlays.csv: h3, name, holc, access_min, access_km.
"""
import json
import math
import sys
import time

import numpy as np
import pandas as pd
import requests

import config as C
from cooling_sources import eligible_discovery_sites

OUT_CSV = C.OVERLAYS_CSV
UA = {"User-Agent": "CoolEquity/0.1 (hackathon heat-equity mapper)"}

# south,west,north,east — Overpass's bbox order, not GeoJSON's.
OQL_BBOX = f"{C.BBOX[1]},{C.BBOX[0]},{C.BBOX[3]},{C.BBOX[2]}"

# What counts as somewhere you can go to escape the heat. Libraries and
# community/rec centers are what US cities actually designate; public pools and
# splash parks are the informal version. Deliberately excludes private pools,
# which LA has tens of thousands of and which help nobody without one.
CENTERS_OQL = f"""[out:json][timeout:{C.OVERPASS_TIMEOUT_S}];
(
  nwr["amenity"="library"]({OQL_BBOX});
  nwr["amenity"="community_centre"]({OQL_BBOX});
  nwr["amenity"="public_bath"]({OQL_BBOX});
  nwr["amenity"="social_facility"]["social_facility"="shelter"]({OQL_BBOX});
  nwr["amenity"="social_facility"]["social_facility:for"~"senior"]({OQL_BBOX});
  nwr["leisure"="swimming_pool"]["access"~"^(yes|public|permissive|customers)$"]({OQL_BBOX});
  nwr["leisure"="water_park"]({OQL_BBOX});
);
out center;"""

_PLACE_NODES = (
    f'  node["place"~"^(neighbourhood|suburb|quarter|borough|city|town|village)$"]'
    f'["name"]({OQL_BBOX});\n'
)
# Named subdivision and park polygons. `out geom` rather than `out center`,
# because the point of these is that a hex can fall INSIDE one — a centroid
# would put every hex in a long canyon subdivision nearer some other centroid.
_NAMED_AREAS = (
    f'  way["landuse"="residential"]["name"]({OQL_BBOX});\n'
    f'  way["leisure"="park"]["name"]({OQL_BBOX});\n'
)
PLACES_OQL = (
    f"[out:json][timeout:{C.OVERPASS_TIMEOUT_S}];\n(\n"
    + _PLACE_NODES
    + (_NAMED_AREAS if getattr(C, "NAME_FROM_LANDUSE", False) else "")
    + ");\nout geom;"
)

# NB: `out center`, never `out ... tags`. The `tags` verbosity prints ids and
# tags and *drops the coordinates*, including on plain nodes — which fails
# silently here, as every element parses fine and then has nowhere to be put.

OCTANTS = ("N", "NE", "E", "SE", "S", "SW", "W", "NW")


def log(msg):
    print(msg, flush=True)


# ------------------------------------------------------------------- fetching
def overpass(oql, label):
    """Run an Overpass query against the first mirror that answers.

    Public instances rate-limit and go down, and a 504 from one usually means
    you are the load — hence the pause between rounds rather than an immediate
    retry. A demo that depends on exactly one instance is a demo that fails at
    the venue.
    """
    last = None
    for attempt in range(C.OVERPASS_ROUNDS):
        if attempt:
            log(f"    {label}: all mirrors busy — backing off "
                f"{C.OVERPASS_BACKOFF_S}s")
            time.sleep(C.OVERPASS_BACKOFF_S)
        for url in C.OVERPASS_MIRRORS:
            host = url.split("/")[2]
            try:
                log(f"    {label}: querying {host}...")
                r = requests.post(url, data={"data": oql}, headers=UA,
                                  timeout=C.OVERPASS_TIMEOUT_S + 30)
                r.raise_for_status()
                return r.json()["elements"]
            except Exception as e:
                last = f"{type(e).__name__}: {e}"
                log(f"    {host} failed ({last})")
    raise RuntimeError(f"all Overpass mirrors failed — last: {last}")


def cached(path, build, label, refresh):
    """Committed copy first, else live fetch, else None. Never fatal here.

    Cache-first — the opposite of 02_satellite.py, on purpose. The STAC catalog
    does not care how often you ask; Overpass does, and re-pulling 645 amenities
    on every tweak of the scoring code is how you get rate-limited an hour
    before the demo. `--refresh` when you actually want new data.
    """
    if path.exists() and not refresh:
        gj = json.loads(path.read_text())
        log(f"  {label}: cached {path.name} ({len(gj['features'])} features) "
            f"— --refresh to re-pull")
        return gj
    try:
        gj = build()
        n = len(gj["features"])
        if n == 0:
            raise RuntimeError("query returned nothing")
        path.write_text(json.dumps(gj))
        log(f"  {label}: {n} live -> cached {path.name}")
        return gj
    except Exception as e:
        log(f"  {label}: live fetch failed ({type(e).__name__}: {e})")
        if path.exists():
            gj = json.loads(path.read_text())
            log(f"  {label}: using committed {path.name} "
                f"({len(gj['features'])} features)")
            return gj
        log(f"  {label}: NO CACHE at {path.name}")
        return None


def osm_point(el):
    """Node coords, or the `out center` centroid for a way/relation."""
    if "lat" in el:
        return el["lon"], el["lat"]
    ctr = el.get("center")
    return (ctr["lon"], ctr["lat"]) if ctr else None


# The four categories the front end knows how to draw, count and toggle. Kept
# here rather than implied, because the failure mode is silent: a site with a
# kind the app has never heard of still gets drawn on the map but is missing from
# every count, so the panel reads "487 of 488 shown" and nobody can find the one.
# That is exactly what happened -- kind_of() used to RETURN the fallthrough value
# "public_bath", a fifth category the app had no entry for. LA had none, so it
# never surfaced; Contra Costa has one.
KINDS = ("library", "community_centre", "pool", "shelter/senior")


def kind_of(tags):
    """Map OSM tags to one of KINDS, or None to drop the site.

    Every branch is explicit. Public baths fold into "pool" -- both are public
    water facilities and a category with a single member is UI noise, not
    information. Anything unmatched returns None and is dropped rather than
    quietly inventing a category.
    """
    amenity = tags.get("amenity")
    if amenity == "library":
        return "library"
    if amenity == "community_centre":
        return "community_centre"
    if amenity == "social_facility":
        return "shelter/senior"
    if amenity == "public_bath":
        return "pool"
    if tags.get("leisure") in ("swimming_pool", "water_park"):
        return "pool"
    return None


def check_coords(els, label):
    """Guard the `out center` contract — see the note by the queries above."""
    bad = sum(1 for e in els if osm_point(e) is None)
    if bad:
        raise RuntimeError(
            f"{label}: {bad}/{len(els)} elements came back without coordinates "
            "— the `out` mode dropped them"
        )
    return els


def fetch_centers():
    feats, seen, dropped = [], set(), []
    for el in check_coords(overpass(CENTERS_OQL, "cooling centers"), "centers"):
        pt = osm_point(el)
        # A pool inside a rec center is often mapped as both a node and a way;
        # round to ~10 m so the pair collapses to one marker.
        key = (round(pt[0], 4), round(pt[1], 4))
        if key in seen:
            continue
        seen.add(key)
        tags = el.get("tags", {})
        kind = kind_of(tags)
        if kind is None:
            # Dropped, not defaulted. See the note above KINDS.
            dropped.append(tags.get("name") or "unnamed")
            continue
        feats.append({
            "type": "Feature",
            "properties": {
                "kind": kind,
                "name": tags.get("name", "Unnamed cooling site"),
            },
            "geometry": {"type": "Point", "coordinates": [round(pt[0], 5),
                                                          round(pt[1], 5)]},
        })
    if dropped:
        log(f"    dropped {len(dropped)} site(s) matching no known category "
            f"(e.g. {dropped[0]}) — see KINDS in this file")
    return {"type": "FeatureCollection", "features": feats}


def fetch_places():
    """Place nodes, plus (optionally) named subdivision/park polygons.

    Mixed geometry on purpose: a node becomes a Point and is matched by
    proximity, a closed way becomes a Polygon and is matched by containment
    first. Ways that are not closed rings are dropped rather than guessed at.
    """
    feats, pts, polys = [], 0, 0
    for el in overpass(PLACES_OQL, "place names"):
        tags = el.get("tags", {})
        name = tags.get("name")
        if not name:
            continue
        geom = el.get("geometry")
        if el["type"] == "way" and geom and len(geom) >= 4:
            ring = [[round(p["lon"], 5), round(p["lat"], 5)] for p in geom]
            if ring[0] != ring[-1]:
                ring.append(ring[0])            # close it, or shapely refuses
            if len(ring) < 4:
                continue
            g = {"type": "Polygon", "coordinates": [ring]}
            polys += 1
        else:
            pt = osm_point(el)
            if pt is None:
                continue
            g = {"type": "Point", "coordinates": [round(pt[0], 5), round(pt[1], 5)]}
            pts += 1
        feats.append({"type": "Feature", "geometry": g, "properties": {
            "name": name,
            "place": tags.get("place", ""),
            "kind": "park" if tags.get("leisure") == "park" else
                    "subdivision" if tags.get("landuse") == "residential" else "place",
        }})
    log(f"    places: {pts} point anchors, {polys} named areas")
    return {"type": "FeatureCollection", "features": feats}


def fetch_holc():
    r = requests.get(C.HOLC_URL, headers=UA, timeout=90)
    r.raise_for_status()
    gj = r.json()
    # One LA polygon carries a null grade; an ungraded area is not a category.
    gj["features"] = [f for f in gj["features"]
                      if f.get("geometry") and f["properties"].get("grade")
                      in ("A", "B", "C", "D")]
    return gj


# -------------------------------------------------------------------- joins
def holc_grades(hexes, holc_gj):
    """Majority-overlap HOLC grade per hex, or null where the map didn't reach.

    Majority by *area*, not by centroid hit: a hex straddling a C/D boundary
    should read as whichever dominates, and centroid sampling would coin-flip it.
    """
    import geopandas as gpd
    holc = gpd.GeoDataFrame.from_features(holc_gj["features"], crs="EPSG:4326")
    # The 1930s scans digitise with self-intersections here and there; overlay
    # refuses to run on those.
    holc["geometry"] = holc.geometry.make_valid()
    holc = holc[holc.geometry.geom_type.isin(("Polygon", "MultiPolygon"))]
    holc = holc[["grade", "geometry"]].to_crs(C.RASTER_CRS)

    inter = gpd.overlay(hexes[["h3", "geometry"]], holc,
                        how="intersection", keep_geom_type=True)
    inter["a"] = inter.geometry.area
    by = inter.groupby(["h3", "grade"], as_index=False)["a"].sum()

    top = by.sort_values("a").drop_duplicates("h3", keep="last")
    cover = by.groupby("h3")["a"].sum()
    area = hexes.set_index("h3").geometry.area

    top = top.set_index("h3")
    frac = (cover / area).reindex(top.index)
    graded = top["grade"].where(frac >= C.HOLC_MIN_COVER)
    return graded.reindex(hexes["h3"].values).values


def access_time(hexes, centers_gj):
    """Walking minutes and km from each hex centroid to the nearest cooling site.

    Circuity-adjusted straight line (see C.CIRCUITY) — an estimate, not a route.
    """
    import geopandas as gpd
    from shapely.geometry import shape

    pts = gpd.GeoDataFrame(
        geometry=[shape(f["geometry"]) for f in centers_gj["features"]],
        crs="EPSG:4326",
    ).to_crs(C.RASTER_CRS)

    cent = gpd.GeoDataFrame({"h3": hexes["h3"].values},
                            geometry=hexes.geometry.centroid, crs=hexes.crs)
    near = gpd.sjoin_nearest(cent, pts, how="left", distance_col="m")
    # sjoin_nearest emits one row per tie; a hex equidistant from two centers
    # would otherwise duplicate downstream.
    near = near.drop_duplicates("h3").set_index("h3").reindex(hexes["h3"].values)

    km = near["m"].values / 1000.0 * C.CIRCUITY
    return km / C.WALK_SPEED_KMH * 60.0, km


def octant(dx, dy):
    ang = math.degrees(math.atan2(dx, dy)) % 360      # 0 = due north
    return OCTANTS[int((ang + 22.5) // 45) % 8]


def hex_names(hexes, places_gj):
    """Name each hex after the place it is in, or failing that the nearest one.

    Two passes, because the anchors are two different kinds of thing:

      1. CONTAINMENT. If the hex centroid falls inside a named area — a
         subdivision or a park — it takes that name. Where areas nest (a park
         inside a subdivision) the SMALLEST containing one wins, since that is
         the more specific answer.
      2. PROXIMITY. Anything left over takes the nearest anchor of any kind.
         This is the only pass LA ever used, because LA's anchors are all point
         nodes.

    Dozens of hexes still fall inside one name, so the closest hex to the
    anchor keeps the bare name and the rest get a compass suffix — "Gale Ranch"
    vs "Gale Ranch SE". The ranked list is read aloud in the demo; two identical
    rows would be worse than a slightly clumsy one.
    """
    import geopandas as gpd
    from shapely.geometry import shape

    pl = gpd.GeoDataFrame(
        {"pname": [f["properties"]["name"] for f in places_gj["features"]],
         "kind": [f["properties"].get("kind", "place")
                  for f in places_gj["features"]]},
        geometry=[shape(f["geometry"]) for f in places_gj["features"]],
        crs="EPSG:4326",
    ).to_crs(C.RASTER_CRS)

    cent = gpd.GeoDataFrame({"h3": hexes["h3"].values},
                            geometry=hexes.geometry.centroid, crs=hexes.crs)

    areas = pl[pl.geometry.geom_type.isin(("Polygon", "MultiPolygon"))].copy()
    assigned = {}
    if len(areas):
        areas["a"] = areas.geometry.area
        hit = gpd.sjoin(cent, areas[["pname", "kind", "a", "geometry"]],
                        how="inner", predicate="within")
        # Smallest containing area wins — the more specific answer.
        hit = hit.sort_values("a").drop_duplicates("h3", keep="first")
        assigned = dict(zip(hit["h3"], hit["pname"]))
        log(f"  names: {len(assigned)}/{len(cent)} hexes inside a named area")

    # Parks are excluded from the PROXIMITY pass, though not from containment.
    # There are 49 of them in 52 km2 and they are small, so on nearest-anchor
    # they beat the subdivisions almost everywhere and every third hex comes out
    # "<something> Park E 5". A hex sitting in a park may fairly be named for it;
    # a hex of houses near one should be named for the neighbourhood.
    left = cent[~cent["h3"].isin(assigned)]
    if len(left):
        prox = pl[pl["kind"] != "park"]
        if not len(prox):
            prox = pl
        near = gpd.sjoin_nearest(left, prox[["pname", "geometry"]],
                                 how="left", distance_col="m")
        near = near.drop_duplicates("h3")
        assigned.update(dict(zip(near["h3"], near["pname"])))
        log(f"  names: {len(left)} more by nearest "
            f"{'non-park ' if len(prox) < len(pl) else ''}anchor")

    # Compass suffixes, computed against the anchor the hex was matched to.
    anchor = pl.dissolve(by="pname").geometry.centroid
    rows = []
    for h3c, geom in zip(cent["h3"], cent.geometry):
        nm = assigned.get(h3c)
        if nm is None or nm not in anchor.index:
            rows.append((h3c, nm or "Unnamed", 0.0, "N"))
            continue
        a = anchor.loc[nm]
        rows.append((h3c, nm, geom.distance(a), octant(geom.x - a.x, geom.y - a.y)))
    df = pd.DataFrame(rows, columns=["h3", "pname", "m", "oct"])

    labels, used = {}, set()
    for pname, grp in df.sort_values("m").groupby("pname", sort=False):
        for i, (_, row) in enumerate(grp.iterrows()):
            base = pname if i == 0 else f"{pname} {row['oct']}"
            label, n = base, 2
            while label in used:                       # same octant twice over
                label, n = f"{base} {n}", n + 1
            used.add(label)
            labels[row["h3"]] = label

    return pd.Series(labels).reindex(hexes["h3"].values).values


# --------------------------------------------------------------------- main
# Streets the city can plant along. Residential and tertiary roads only:
# motorway and trunk are Caltrans/county right-of-way with no planting strip, and
# service ways are driveways and parking aisles. This is the closest thing in
# open data to "frontage San Ramon actually controls", and it is the difference
# between a map that says where trees should go and one a planner can act on --
# the top-ranked hexes are private subdivisions, so street frontage is where the
# city's own authority to plant actually lives.
STREETS_OQL = f"""[out:json][timeout:{C.OVERPASS_TIMEOUT_S}];
way["highway"~"^(residential|tertiary|unclassified|living_street|secondary)$"]\
({C.BBOX[1]},{C.BBOX[0]},{C.BBOX[3]},{C.BBOX[2]});
out geom;
"""


def street_frontage(hexes, refresh):
    """Metres of plantable street centreline inside each hex.

    Returns a Series indexed like `hexes`. Both sides of a street are plantable,
    so capacity is 2 x length / spacing -- that doubling happens in the app,
    where the spacing assumption is visible, not buried here.
    """
    import geopandas as gpd
    from shapely.geometry import LineString

    def build():
        return {"type": "FeatureCollection", "features": [
            {"type": "Feature",
             "properties": {"hw": e["tags"].get("highway", "")},
             "geometry": {"type": "LineString",
                          "coordinates": [[round(p["lon"], 5), round(p["lat"], 5)]
                                          for p in e["geometry"]]}}
            for e in overpass(STREETS_OQL, "streets")
            if len(e.get("geometry") or []) >= 2]}

    gj = cached(C.STREETS_FILE, build, "streets", refresh)
    if gj is None:
        # Non-fatal, like every other overlay here: the score does not depend on
        # frontage, so a failed Overpass pull costs the planner column and
        # nothing else.
        log("  streets: unavailable — frontage column will be 0")
        return hexes["h3"].map({}).fillna(0.0)

    st = gpd.GeoDataFrame.from_features(gj["features"], crs="EPSG:4326").to_crs(C.RASTER_CRS)
    hx = hexes.to_crs(C.RASTER_CRS)[["h3", "geometry"]]
    inter = gpd.overlay(
        gpd.GeoDataFrame(geometry=st.geometry, crs=C.RASTER_CRS).assign(k=1),
        hx, how="intersection", keep_geom_type=False)
    inter = inter[inter.geometry.geom_type.isin(["LineString", "MultiLineString"])]
    m = inter.assign(m=inter.geometry.length).groupby("h3")["m"].sum()
    return hexes["h3"].map(m).fillna(0.0)


def main():
    import geopandas as gpd
    refresh = "--refresh" in sys.argv
    log(f"Phase 4 — overlays | {C.CITY}{' | --refresh' if refresh else ''}")
    hexes = gpd.read_file(C.GRID_FILE).to_crs(C.RASTER_CRS)
    log(f"  grid: {len(hexes)} hexes")

    centers = cached(C.CENTERS_FILE, fetch_centers, "centers", refresh)
    if centers:
        centers = eligible_discovery_sites(centers)
        C.CENTERS_FILE.write_text(json.dumps(centers))
    places = cached(C.PLACES_FILE, fetch_places, "places", refresh)
    # Gated on the URL as well as the country: San Ramon is in the USA and still
    # has no HOLC map, because HOLC surveyed built-up cities in 1935-40 and San
    # Ramon was farmland. No URL means no layer, rather than borrowed grades.
    holc = (cached(C.HOLC_FILE, fetch_holc, "HOLC", refresh)
            if C.COUNTRY == "USA" and C.HOLC_URL else None)

    if not centers or not centers["features"]:
        raise SystemExit(
            f"\nNo cooling centers and no cache at {C.CENTERS_FILE}.\n"
            "The access-gap layer is the intervention argument — refusing to "
            "invent one."
        )

    out = pd.DataFrame({"h3": hexes["h3"].values})

    out["name"] = (hex_names(hexes, places) if places else
                   [f"Hex {i}" for i in range(len(hexes))])
    if not places:
        log("  names: no place data — falling back to 'Hex N'")

    if holc:
        out["holc"] = holc_grades(hexes, holc)
        got = out["holc"].notna().sum()
        share = out["holc"].value_counts().to_dict()
        log(f"  HOLC: {got}/{len(out)} hexes graded {share}")
    else:
        out["holc"] = None
        why = ("no HOLC map exists for this city" if C.COUNTRY == "USA"
               else f"COUNTRY={C.COUNTRY} — US-only layer")
        log(f"  HOLC: skipped ({why})")

    mins, km = access_time(hexes, centers)
    out["access_min"] = np.round(mins, 1)
    out["access_km"] = np.round(km, 2)

    fr = street_frontage(hexes, refresh)
    out["street_m"] = np.round(fr, 0)
    log(f"  streets: {fr.sum()/1000:,.0f} km of plantable frontage, "
        f"median {fr.median():,.0f} m per hex, "
        f"{int((fr == 0).sum())} hexes with none")

    out.to_csv(OUT_CSV, index=False)
    log(f"  centers: {len(centers['features'])} sites")
    log(f"  access:  {out.access_min.min():.0f}–{out.access_min.max():.0f} min "
        f"(median {out.access_min.median():.0f}), circuity {C.CIRCUITY}")
    log(f"  names:   {out.name.nunique()} distinct, e.g. "
        f"{', '.join(out.name.head(3))}")
    log(f"  wrote {OUT_CSV.relative_to(C.ROOT)}")

    # Every hex is within ~1 km of somewhere in a city this dense; a citywide
    # median over an hour means the center list came back nearly empty.
    if out.access_min.median() > 60:
        log("  WARNING: median walk time looks implausible — check centers",
            file=sys.stderr)


if __name__ == "__main__":
    main()
