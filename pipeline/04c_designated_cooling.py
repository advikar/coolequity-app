"""Phase 4c — county-designated cooling locations as map points.

Reads the city's published cooling directory (cities/<slug>/data/
cooling_directory_<slug>.json, transcribed from the county's own list) and
writes designated_<slug>.geojson: one point per location the county lists,
geocoded from its street address with OpenStreetMap Nominatim.

These are the county's designated sites, distinct from the OpenStreetMap
discovery inventory in centers_<slug>.geojson that drives the walking-time
layer. Nothing here asserts open-now status, hours or eligibility; the
directory's own service note and phone numbers travel with each point.

    COOLEQUITY_CITY=bakersfield python pipeline/04c_designated_cooling.py

Study area: the county's list covers the whole county, but a city map should
only draw the sites its residents can reach. A located site is kept as a map
point when it falls inside the study-area boundary (01's clip polygon) padded by
NEAR_M; the rest are written under `outside_study_area` in the file's top-level
properties, with their coordinates, so nothing is dropped silently and the
cooling.html directory can still list them.

Geocoding: address first; if that fails, the parenthetical is dropped, then the
facility name with the city is tried. `geocode_quality` records which matched
('address', 'name') or 'street' when Nominatim only resolved the road. Locations
it could not place are listed under `unlocated` in the file's top-level
properties, never silently dropped. Nominatim usage policy: one request per
second, identified user agent, results cached in data/_cache/geocode_<slug>.json.
"""
import json
import re
import sys
import time
import urllib.parse
import urllib.request

import config as C

DIRECTORY = C.DATA / f"cooling_directory_{C.SLUG}.json"
OUT = C.DATA / f"designated_{C.SLUG}.geojson"
CACHE = C.CACHE / f"geocode_{C.SLUG}.json"
UA = "CoolEquity (student project; github.com/advikar/coolequity-app)"
NEAR_M = 1500   # a site this far outside the boundary still serves residents on the edge


def study_area():
    """Boundary polygon padded by NEAR_M, in WGS84, or None when 01 has not run."""
    if not C.BOUNDARY_FILE.exists():
        return None
    from shapely.geometry import shape
    from shapely.ops import unary_union
    geom = unary_union([shape(f["geometry"]) for f in json.loads(C.BOUNDARY_FILE.read_text())["features"]])
    return geom.buffer(NEAR_M / 110_540.0)   # degrees: ~NEAR_M north-south, a little less east-west


def nominatim(q):
    url = "https://nominatim.openstreetmap.org/search?" + urllib.parse.urlencode(
        {"q": q, "format": "json", "limit": 1, "countrycodes": "us"})
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        hits = json.load(urllib.request.urlopen(req, timeout=20))
    except Exception as e:  # network or 4xx: treat as no hit, caller records it
        print(f"    nominatim error for {q!r}: {e}", file=sys.stderr)
        hits = []
    time.sleep(1.1)
    return hits[0] if hits else None


def geocode(item, default_city, cache):
    city = item.get("city") or default_city
    addr = item["address"]
    tries = [("address", f"{addr}, {city}, California")]
    stripped = re.sub(r"\s*\(.*?\)", "", addr).strip()
    if stripped != addr:
        tries.append(("address", f"{stripped}, {city}, California"))
    tries.append(("name", f"{item['name']}, {city}, California"))
    for how, q in tries:
        if q in cache:
            hit = cache[q]
        else:
            hit = nominatim(q)
            cache[q] = hit
        if hit:
            quality = how
            if how == "address" and hit.get("type") in ("primary", "secondary", "tertiary", "residential", "road"):
                quality = "street"   # only the road matched; the point is on the road, not the door
            return float(hit["lat"]), float(hit["lon"]), quality, hit.get("display_name", "")
    return None, None, "none", ""


def main():
    print(f"Phase 4c — designated cooling locations | {C.CITY}")
    doc = json.loads(DIRECTORY.read_text())
    items = next(v for v in doc.values() if isinstance(v, list) and v and isinstance(v[0], dict) and "name" in v[0])
    meta = {k: v for k, v in doc.items() if not isinstance(v, list)}
    cache = json.loads(CACHE.read_text()) if CACHE.exists() else {}
    area = study_area()
    if area is None:
        print("  WARNING: no boundary file; every located site is kept", file=sys.stderr)
    feats, unlocated, outside = [], [], []
    for it in items:
        lat, lon, quality, matched = geocode(it, C.CITY, cache)
        rec = {k: it.get(k) for k in ("id", "name", "address", "city", "phone", "opening_hours", "eligibility", "designation", "note")}
        rec["geocode_quality"] = quality
        rec["geocode_match"] = matched
        if lat is None:
            unlocated.append(rec)
            print(f"  NOT LOCATED: {it['name']} — {it['address']}, {it.get('city') or C.CITY}")
            continue
        feat = {"type": "Feature", "geometry": {"type": "Point", "coordinates": [lon, lat]}, "properties": rec}
        if area is not None:
            from shapely.geometry import Point
            if not area.contains(Point(lon, lat)):
                outside.append(feat)
                print(f"  outside  {it['name'][:40]:40s} {it.get('city') or ''}")
                continue
        feats.append(feat)
        print(f"  {quality:8s} {it['name'][:40]:40s} {matched[:70]}")
    CACHE.parent.mkdir(exist_ok=True)
    CACHE.write_text(json.dumps(cache, indent=1))
    out = {"type": "FeatureCollection",
           "properties": {**meta, "geocoder": "OpenStreetMap Nominatim, address match",
                          "geocoded": time.strftime("%Y-%m-%d"), "unlocated": unlocated,
                          "study_area_pad_m": NEAR_M, "outside_study_area": outside},
           "features": feats}
    OUT.write_text(json.dumps(out, indent=1))
    print(f"  wrote {OUT.relative_to(C.ROOT)}: {len(feats)} in study area, "
          f"{len(outside)} elsewhere in the county (listed, not drawn), {len(unlocated)} not located")


if __name__ == "__main__":
    main()
