"""Phase 4e — council wards (or supervisorial districts): fetch, assign, summarise.

Reads C.WARDS, a per-city entry pointing at an ArcGIS feature layer:

    WARDS = dict(service=".../MapServer/5",
                 fields=dict(id="WARD_ID", name="FEAT_NAME", member="MEMBER", url="LINK"),
                 label="Ward {n}", outside="Unincorporated (Kern County)",
                 adopted="2022 redistricting, council map 5B (Unity Map)",
                 publisher="City of Bakersfield GIS Office")

Writes:
  wards_<slug>.geojson          the boundaries, normalised (ward_id, ward_name, member, member_url)
  wards_<slug>.csv              h3, id, ward_id, ward_name for every grid hexagon (05 merges it)
  wards_summary_<slug>.csv      one row per ward: areas, residents, need, tree cover, street capacity
  sources.json / SOURCES.md     provenance line for the fetch
and, when <slug>.geojson already exists, patches ward_id/ward_name onto its features
so the app and the tests see the assignment without a full 05 rerun.

Flags:
  --cached             use the committed boundary file, no network
  --accept-boundaries  allow a fetch that CHANGES boundaries to overwrite the file.
                       Without it the new boundaries land in wards_<slug>.new.geojson
                       and the stage exits 2, because new lines change every ward
                       total in every report already handed out.

A city with no WARDS entry exits 0 and writes nothing.
"""
import csv
import hashlib
import json
import math
import sys

import config as C

try:
    from shapely.geometry import shape, Point
except ImportError:  # the light venv the tests use may lack it
    shape = Point = None


def log(msg):
    print(msg, flush=True)


# ------------------------------------------------------------------- fetch
def fetch_layer(service, fields):
    import requests
    feats, offset = [], 0
    while True:
        r = requests.get(f"{service}/query", params={
            "where": "1=1", "outFields": ",".join(v for v in fields.values() if v),
            "outSR": 4326, "f": "geojson", "resultOffset": offset}, timeout=120)
        r.raise_for_status()
        g = r.json()
        if "error" in g:
            raise SystemExit(f"service error: {g['error']}")
        feats += g.get("features", [])
        if not g.get("properties", {}).get("exceededTransferLimit") and not g.get("exceededTransferLimit"):
            break
        offset = len(feats)
    return feats


def _rnd(coords):
    if isinstance(coords[0], (int, float)):
        return [round(coords[0], 6), round(coords[1], 6)]
    return [_rnd(c) for c in coords]


def normalise(raw, cfg):
    f = cfg["fields"]
    label = cfg.get("label", "Ward {n}")
    out = []
    for ft in raw:
        p = ft["properties"]
        ident = str(p.get(f["id"], "")).strip()
        digits = "".join(ch for ch in ident if ch.isdigit())
        n = digits or ident
        out.append({"type": "Feature",
                    "properties": {"ward_id": n, "ward_name": label.format(n=n, raw=ident),
                                   "member": (p.get(f.get("member")) or "").strip() or None,
                                   "member_url": (p.get(f.get("url")) or "").strip() or None},
                    "geometry": {"type": ft["geometry"]["type"], "coordinates": _rnd(ft["geometry"]["coordinates"])}})
    out.sort(key=lambda x: (len(x["properties"]["ward_id"]), x["properties"]["ward_id"]))
    return out


def geometry_hash(feats):
    h = hashlib.sha256()
    for ft in feats:
        h.update(json.dumps(ft["geometry"], separators=(",", ":"), sort_keys=True).encode())
    return h.hexdigest()[:12]


# ------------------------------------------------------------------- assign
def assign(grid_feats, wards):
    """Hexagon centre in ward polygon. Centres come from the grid's lat/lon."""
    if shape is None:
        raise SystemExit("shapely is required for 04c (pip install shapely)")
    polys = [(w["properties"], shape(w["geometry"])) for w in wards]
    rows = []
    for f in grid_feats:
        p = f["properties"]
        pt = Point(p["lon"], p["lat"])
        hit = next((wp for wp, geom in polys if geom.contains(pt)), None)
        rows.append({"h3": p["h3"], "id": p["id"],
                     "ward_id": hit["ward_id"] if hit else "",
                     "ward_name": hit["ward_name"] if hit else ""})
    return rows


def summarise(assign_rows, wards, outside_label):
    """Per-ward totals from the scored output, if it exists."""
    if not C.OUT_FILE.exists():
        return None
    scored = json.loads(C.OUT_FILE.read_text())
    by_id = {r["id"]: r for r in assign_rows}
    acc = {}
    for ft in scored["features"]:
        p = ft["properties"]
        if p.get("place") != "res":
            continue
        a = by_id.get(p["id"], {})
        key = a.get("ward_id") or ""
        s = acc.setdefault(key, dict(areas=0, residents=0.0, residents_65plus=0.0, need_sum=0.0,
                                     top100=0, cover_pop=0.0, cover_w=0.0, heat_sum=0.0, street_m=0.0))
        s["areas"] += 1
        s["residents"] += p.get("pop") or 0
        s["residents_65plus"] += (p.get("pop") or 0) * (p.get("pct65") or 0) / 100
        s["need_sum"] += p.get("score") or 0
        s["top100"] += 1 if (p.get("rank") or 10**9) <= 100 else 0
        if p.get("green_src") == "canopy":
            s["cover_w"] += (p.get("green") or 0) * (p.get("pop") or 0); s["cover_pop"] += p.get("pop") or 0
        s["heat_sum"] += p.get("lst") or 0
        s["street_m"] += p.get("street_m") or 0
    members = {w["properties"]["ward_id"]: w["properties"] for w in wards}
    rows = []
    for key in sorted(acc, key=lambda k: (k == "", len(k), k)):
        s = acc[key]; m = members.get(key, {})
        rows.append({
            "ward_id": key, "ward_name": m.get("ward_name") or outside_label, "member": m.get("member") or "",
            "areas": s["areas"], "residents": round(s["residents"]), "residents_65plus": round(s["residents_65plus"]),
            "mean_need_0_100": round(s["need_sum"] / s["areas"], 1), "areas_in_top_100": s["top100"],
            "tree_cover_pct_pop_weighted": round(s["cover_w"] / s["cover_pop"], 1) if s["cover_pop"] else "",
            "mean_surface_heat_c": round(s["heat_sum"] / s["areas"], 1),
            "plantable_street_km": round(s["street_m"] / 1000, 1),
            "tree_positions_upper_bound": math.floor(s["street_m"] * 2 / getattr(C, "TREE_SPACING_M", 10)),
        })
    return rows


def patch_output(assign_rows):
    if not C.OUT_FILE.exists():
        return 0
    doc = json.loads(C.OUT_FILE.read_text())
    by_id = {r["id"]: r for r in assign_rows}
    n = 0
    for ft in doc["features"]:
        a = by_id.get(ft["properties"]["id"])
        if a is None:
            continue
        ft["properties"]["ward_id"] = a["ward_id"] or None
        ft["properties"]["ward_name"] = a["ward_name"] or None
        n += 1
    doc.setdefault("metadata", {})["wards"] = {"file": C.WARDS_FILE.name, "adopted": C.WARDS.get("adopted")}
    C.OUT_FILE.write_text(json.dumps(doc, separators=(",", ":")))
    return n


# ------------------------------------------------------------------- main
def main():
    cfg = getattr(C, "WARDS", None)
    log(f"Phase 4e — wards | {C.CITY}")
    if not cfg:
        log("  no WARDS entry in this city's config: nothing to do")
        return 0
    cached = "--cached" in sys.argv
    accept = "--accept-boundaries" in sys.argv
    existing = json.loads(C.WARDS_FILE.read_text()) if C.WARDS_FILE.exists() else None

    if cached:
        if not existing:
            raise SystemExit(f"--cached but {C.WARDS_FILE.name} is missing")
        wards = existing["features"]
        log(f"  boundaries: {len(wards)} from the committed file (--cached)")
    else:
        raw = fetch_layer(cfg["service"], cfg["fields"])
        wards = normalise(raw, cfg)
        log(f"  fetched {len(wards)} wards from {cfg['service']}")
        if existing:
            old, new = geometry_hash(existing["features"]), geometry_hash(wards)
            old_members = {w["properties"]["ward_id"]: w["properties"].get("member") for w in existing["features"]}
            for w in wards:
                pid = w["properties"]["ward_id"]
                if old_members.get(pid) != w["properties"].get("member"):
                    log(f"  member change: {w['properties']['ward_name']}: {old_members.get(pid)!r} -> {w['properties'].get('member')!r}")
            if old != new and not accept:
                alt = C.WARDS_FILE.with_suffix(".new.geojson")
                alt.write_text(json.dumps({"type": "FeatureCollection", "features": wards}, separators=(",", ":")))
                log(f"  BOUNDARIES CHANGED ({old} -> {new}). New lines change every ward total in every\n"
                    f"  report already handed out. Review {alt.name}; rerun with --accept-boundaries to adopt.")
                return 2
        doc = {"type": "FeatureCollection", "name": C.WARDS_FILE.stem,
               "source": cfg.get("publisher"), "source_url": cfg["service"],
               "retrieved": __import__("datetime").date.today().isoformat(),
               "boundaries_adopted": cfg.get("adopted"), "members_as_of": __import__("datetime").date.today().isoformat(),
               "crs_note": "WGS84 (EPSG:4326), reprojected by the server",
               "note": "Council members change at elections; boundaries change with redistricting. "
                       "Re-fetch with 04e_wards.py rather than editing by hand.",
               "features": wards}
        C.WARDS_FILE.write_text(json.dumps(doc, separators=(",", ":")))
        log(f"  wrote {C.WARDS_FILE.relative_to(C.ROOT)}")
        from sources import record
        record("04e_wards", cfg.get("what", "Council wards"), cfg["service"], path=C.WARDS_FILE,
               count=len(wards), publisher=cfg.get("publisher"),
               note=f"{cfg.get('adopted')}. Member names as fetched; the {cfg.get('label','Ward {n}').split(' ')[0].lower()} number is the stable label." if cfg.get("adopted") else None)

    grid = json.loads(C.GRID_FILE.read_text())["features"]
    rows = assign(grid, wards)
    with open(C.WARDS_CSV, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["h3", "id", "ward_id", "ward_name"]); w.writeheader(); w.writerows(rows)
    inside = sum(1 for r in rows if r["ward_id"])
    log(f"  assigned {inside}/{len(rows)} grid hexagons to a ward; wrote {C.WARDS_CSV.relative_to(C.ROOT)}")

    summary = summarise(rows, wards, cfg.get("outside", "Outside every ward"))
    if summary:
        with open(C.WARDS_SUMMARY_CSV, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(summary[0].keys())); w.writeheader(); w.writerows(summary)
        for r in summary:
            log(f"    {r['ward_name']:<28} {r['areas']:>5} areas {r['residents']:>9,} residents  need {r['mean_need_0_100']:>5}  top-100 {r['areas_in_top_100']:>3}")
        log(f"  wrote {C.WARDS_SUMMARY_CSV.relative_to(C.ROOT)}")
        n = patch_output(rows)
        log(f"  patched ward_id/ward_name onto {n} features in {C.OUT_FILE.name}")
    else:
        log("  no scored output yet: run 05_score.py, then rerun 04c --cached for the summary")
    return 0


if __name__ == "__main__":
    sys.exit(main())
