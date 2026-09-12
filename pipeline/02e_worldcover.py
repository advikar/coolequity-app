"""Phase 2e — authoritative land cover per hex from ESA WorldCover 2021.

Why this exists
---------------
Every hex in the study area is shown, in three classes (see 05_score.py): `res`
(residents, ranked), `activity` (developed but unpopulated) and `empty`
(undeveloped). The empty hexes carry a `land` label so the map says *what* the
grey is — open water, cropland, woodland, marsh. Until now that label came from a
heuristic in 05 (`classify_land`): cool + low-veg => "open water", high canopy =>
"woodland", else "open land" / "bare / hillside". It is right on water but has no
way to tell cropland from grassland from tidal wetland, and in the
Sacramento–San Joaquin Delta it labelled cropland and marsh as "bare / hillside".

This module replaces that guess with a real, citable classification:

  **ESA WorldCover 2021 v200** — a global 10 m land-cover map from Sentinel-1/-2,
  CC-BY 4.0, served as cloud-optimised GeoTIFFs on the Microsoft Planetary
  Computer (collection `esa-worldcover`, asset `map`). Classes:

    10 tree, 20 shrub, 30 grass, 40 crop, 50 built, 60 bare, 70 snow/ice,
    80 water, 90 wetland, 95 mangrove, 100 moss/lichen.

It touches ONLY the descriptive `land` label on empty hexes — no scoring input,
no ranking, no headline number. 05 keeps the old heuristic as a fallback for any
hex WorldCover cannot cover (should be none in California).

Output
------
  data/worldcover_<slug>.csv : h3, land (readable label), land_frac (share of the
  hex's assessed pixels in the majority class — a confidence hint), wc_code (the
  raw WorldCover class of the majority).

Network: anonymous Planetary Computer, signed with planetary_computer.sign_inplace,
exactly like the Sentinel/Landsat path in 02. One windowed read per WorldCover
tile covering the bbox (each tile is 3 deg square), so a whole county is a couple
of reads, not one per hex.
"""
import numpy as np

import config as C

# WorldCover class code -> the label the app shows. Kept concise and in the house
# style ("open water" already shipped). Snow/mangrove/moss are here for
# completeness; none occur in the four California study areas.
WC_LABEL = {
    10: "woodland",     20: "shrubland",   30: "grassland",   40: "cropland",
    50: "developed",    60: "bare ground", 70: "snow / ice",  80: "open water",
    90: "wetland",      95: "mangrove",    100: "moss / lichen",
}


def log(msg):
    print(msg, flush=True)


def main():
    import geopandas as gpd
    import pandas as pd
    import planetary_computer as pc
    import pystac_client as psc
    import rasterio
    from rasterio.windows import from_bounds
    from rasterio.features import geometry_mask

    log(f"Phase 2e — land cover (ESA WorldCover 2021) | {C.CITY}")

    # WorldCover is in EPSG:4326; work the geometry in 4326 to match it.
    hexes = gpd.read_file(C.GRID_FILE)[["h3", "geometry"]].to_crs("EPSG:4326")
    n = len(hexes)
    geoms = list(hexes.geometry)
    minx = min(g.bounds[0] for g in geoms)
    miny = min(g.bounds[1] for g in geoms)
    maxx = max(g.bounds[2] for g in geoms)
    maxy = max(g.bounds[3] for g in geoms)
    pad = 0.01

    cat = psc.Client.open(
        "https://planetarycomputer.microsoft.com/api/stac/v1",
        modifier=pc.sign_inplace)
    items = list(cat.search(collections=["esa-worldcover"],
                            bbox=[minx, miny, maxx, maxy]).items())
    items = [it for it in items if "2021_v200" in it.id] or items
    if not items:
        raise SystemExit("\nNo ESA WorldCover tiles cover this bbox.")
    log(f"  tiles: {', '.join(it.id for it in items)}")

    # Accumulate per-hex class pixel counts across all covering tiles, so a hex on
    # a tile seam sums both halves. counts[i] is a dict {wc_code: n_px}.
    counts = [dict() for _ in range(n)]
    for it in items:
        href = it.assets["map"].href
        with rasterio.open(href) as src:
            win = from_bounds(max(minx - pad, src.bounds.left),
                              max(miny - pad, src.bounds.bottom),
                              min(maxx + pad, src.bounds.right),
                              min(maxy + pad, src.bounds.top),
                              src.transform).round_offsets().round_lengths()
            if win.width < 1 or win.height < 1:
                continue
            arr = src.read(1, window=win)
            tr = src.window_transform(win)
        H, W = arr.shape
        assessed = 0
        for i, g in enumerate(geoms):
            gx0, gy0, gx1, gy1 = g.bounds
            # Pixel window for this hex inside the array we already hold, so each
            # mask is built on ~tens–hundreds of px, not the whole county array.
            c0, r0 = ~tr * (gx0, gy1)      # upper-left px (x incr right, y decr down)
            c1, r1 = ~tr * (gx1, gy0)      # lower-right px
            c0, c1 = sorted((int(np.floor(c0)), int(np.ceil(c1))))
            r0, r1 = sorted((int(np.floor(r0)), int(np.ceil(r1))))
            c0, r0 = max(c0, 0), max(r0, 0)
            c1, r1 = min(c1, W), min(r1, H)
            if c1 <= c0 or r1 <= r0:
                continue
            sub = arr[r0:r1, c0:c1]
            subtr = rasterio.windows.transform(
                rasterio.windows.Window(c0, r0, c1 - c0, r1 - r0), tr)
            m = geometry_mask([g.__geo_interface__], out_shape=sub.shape,
                              transform=subtr, invert=True)
            v = sub[m]
            v = v[v != 0]                  # 0 = WorldCover nodata
            if v.size == 0:
                continue
            u, cnt = np.unique(v, return_counts=True)
            d = counts[i]
            for code, k in zip(u.tolist(), cnt.tolist()):
                d[code] = d.get(code, 0) + k
            assessed += 1
        log(f"  {it.id}: assessed {assessed} hexes")

    labels, fracs, codes = [], [], []
    for d in counts:
        if not d:
            labels.append(None); fracs.append(np.nan); codes.append(np.nan); continue
        tot = sum(d.values())
        code = max(d, key=d.get)
        labels.append(WC_LABEL.get(int(code), str(int(code))))
        fracs.append(round(d[code] / tot, 3))
        codes.append(int(code))

    out = pd.DataFrame({"h3": hexes["h3"], "land": labels,
                        "land_frac": fracs, "wc_code": codes})
    ok = out["land"].notna()
    dist = out.loc[ok, "land"].value_counts().to_dict()
    log(f"  land cover assessed for {int(ok.sum())}/{n} hexes")
    log(f"  distribution (all hexes): {dist}")
    out.to_csv(C.WORLDCOVER_CSV, index=False)
    log(f"  wrote {C.WORLDCOVER_CSV.relative_to(C.ROOT)}")


if __name__ == "__main__":
    main()
