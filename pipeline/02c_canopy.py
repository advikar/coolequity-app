"""Phase 2c — measured tree canopy, tree counts, and plantable public space.

Why this replaces the NDVI proxy
--------------------------------
`green` used to be NDVI rescaled to a percentage. NDVI measures *photosynthesis*,
not trees, and in a summer-dry climate that is a decisive difference: an irrigated
lawn is bright green and shades nobody. Measured on San Ramon, the NDVI proxy put
canopy at 21.2% of the ground; two independent real canopy products put it at
9.5% (USFS NLCD) and 11.2% (Meta/WRI canopy height). It was overstating tree
cover by roughly a factor of two, and the excess was grass.

This module uses the Meta/WRI High-Resolution Canopy Height Map: 0.6 m pixels
over California, values in centimetres of vegetation height, free and anonymous
on S3 as cloud-optimised GeoTIFFs. Height is the right instrument, because a lawn
is 0.1 m tall and a tree is not. No classifier, no vegetation index, no seasonal
irrigation signal — just how far off the ground the vegetation is.

KNOWN BIAS, and it must stay on the screen
------------------------------------------
Validated against the one professional ground truth available: the City of
Fresno's UFMP reports 14.6% canopy from 2022 aerial imagery. Over the same city
boundary this product reads 9.1%, and NLCD reads 2.2%. So CHM is about 38% low
against a real aerial assessment, and NLCD is unusable for urban canopy (it is a
forest-cover product). CHM is the best free option and it is still biased low.

Consequence: this pipeline RANKS blocks; it does not certify absolute canopy.
Where CHM and NLCD are both available they agree on ranking (Spearman +0.84) but
share only 12 of their worst 25 blocks — so the ordering is broadly sound and the
exact top of the list is not. The app says this out loud.

What comes out
--------------
  canopy_pct      % of hex ground under vegetation >= CANOPY_MIN_HT_M
  canopy_m2       that as an area
  row_m2          UNSHADED plantable public right-of-way: street centrelines
                  buffered by ROW_HALF_WIDTH_M, minus what already has canopy
  row_canopy_pct  share of that right-of-way already shaded

WHY THERE IS NO TREE COUNT
--------------------------
An individual-tree count was attempted and abandoned, because this data cannot
support one honestly. Two standard methods were tested on San Ramon:

  connected components  764 objects over a 2.35 km2 sample -> 470 m2 each
  local maxima (4-8 m)  1,498-1,639 objects              -> 219-240 m2 each

A real suburban tree crown is 40-80 m2, about 7-10 m across. Both methods return
objects two to six times that size, because Meta's CHM is a smooth modelled
height surface rather than a crisp per-crown model like airborne LiDAR: touching
crowns never separate. Counting them would have produced a number that looks
authoritative and is wrong by a factor of two to five.

So this module reports canopy EXTENT, which the data measures well, and planting
CAPACITY on public land, which is geometry rather than detection. Both are
defensible. "How many trees are there" is not answerable from this source, and
the app must not pretend otherwise.
"""
import math
import sys

import numpy as np

import config as C

CHM_BASE = ("https://dataforgood-fb-data.s3.amazonaws.com/forests/v1/"
            "California/alsgedi_ca_v5_float/chm")
CHM_ZOOM = 11

# 2 m is the conventional floor for "tree canopy" in urban forestry (i-Tree and
# most UTC assessments). Below it you are counting shrubs and hedges.
CANOPY_MIN_HT_M = 2.0
# Half-width of plantable strip either side of a street centreline. 7 m covers a
# typical residential kerb-to-setback planting strip. Deliberately generous: this
# is an upper bound on public planting space, and it is labelled as one.
ROW_HALF_WIDTH_M = 7.0
# Read resolution. Native is ~0.6 m; 1.2 m still resolves a crown (a 6 m crown is
# 5 px across) and quarters the bytes pulled over HTTP. Decimation was tested and
# moves the canopy fraction by ~1 point, which is inside the product's own bias.
READ_M = 1.2
# Above this many hexes the study area is a county, not a city, and 1.2 m over
# the whole of it is billions of pixels. 2.4 m still puts ~130,000 samples in a
# res-8 hex, which is far more than the statistic needs.
BIG_AREA_HEXES = 1500
READ_M_BIG = 2.4


def log(msg):
    print(msg, flush=True)


def quadkey(lat, lon, z=CHM_ZOOM):
    s = math.sin(lat * math.pi / 180)
    x = int(((lon + 180) / 360) * (1 << z))
    y = int((0.5 - math.log((1 + s) / (1 - s)) / (4 * math.pi)) * (1 << z))
    return "".join(
        str((1 if x & (1 << (i - 1)) else 0) + (2 if y & (1 << (i - 1)) else 0))
        for i in range(z, 0, -1))


def tiles_for(bounds, step=0.02):
    lo_lon, lo_lat, hi_lon, hi_lat = bounds
    out, la = set(), lo_lat
    while la <= hi_lat + step:
        lon = lo_lon
        while lon <= hi_lon + step:
            out.add(quadkey(min(la, hi_lat), min(lon, hi_lon)))
            lon += step
        la += step
    return sorted(out)


def main():
    import os
    os.environ.update(dict(
        AWS_NO_SIGN_REQUEST="YES", GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR",
        CPL_VSIL_CURL_ALLOWED_EXTENSIONS=".tif",
        GDAL_HTTP_MAX_RETRY="5", GDAL_HTTP_RETRY_DELAY="3"))
    import geopandas as gpd
    import pandas as pd
    import rasterio
    from rasterio.windows import from_bounds
    from rasterio.transform import from_bounds as tfb
    from rasterio.features import geometry_mask, rasterize
    from scipy import ndimage  # noqa: F401
    from shapely.geometry import box

    log(f"Phase 2c — canopy | {C.CITY}")
    hexes = gpd.read_file(C.GRID_FILE)[["h3", "geometry"]]
    hx = hexes.to_crs("EPSG:3857")

    row_geom = None
    if not C.STREETS_FILE.exists():
        # Not fatal, but never silent: a missing streets file used to produce a
        # clean run reporting 0.00 km2 of plantable public land, which reads as a
        # finding rather than an absent input.
        log(f"  !! NO {C.STREETS_FILE.name} — right-of-way columns will be 0. "
            f"Run 04_overlays.py first if you want them.")
    if C.STREETS_FILE.exists():
        st = gpd.read_file(C.STREETS_FILE).to_crs("EPSG:3857")
        row_geom = st.geometry.buffer(ROW_HALF_WIDTH_M).union_all()
        log(f"  right-of-way: {len(st)} street segments buffered "
            f"{ROW_HALF_WIDTH_M:g} m -> {row_geom.area/1e6:.1f} km2 of public strip")

    tiles = tiles_for(hexes.to_crs(4326).total_bounds)
    log(f"  canopy height: {len(tiles)} CHM tile(s) cover this study area")

    n = len(hx)
    px_tot = np.zeros(n); px_can = np.zeros(n)
    row_tot = np.zeros(n); row_can = np.zeros(n)

    for ti, t in enumerate(tiles, 1):
        url = f"/vsicurl/{CHM_BASE}/{t}.tif"
        try:
            src = rasterio.open(url)
        except Exception as e:
            log(f"    tile {t}: unavailable ({type(e).__name__})")
            continue
        with src:
            b, tb = hx.total_bounds, src.bounds
            bb = (max(b[0], tb.left), max(b[1], tb.bottom),
                  min(b[2], tb.right), min(b[3], tb.top))
            if bb[2] <= bb[0] or bb[3] <= bb[1]:
                continue
            w = from_bounds(*bb, transform=src.transform)
            target_m = READ_M_BIG if len(hx) > BIG_AREA_HEXES else READ_M
            dec = max(1, int(round(target_m / src.res[0])))
            oh, ow = int(w.height // dec), int(w.width // dec)
            log(f"    tile {ti}/{len(tiles)} {t}: reading {ow}x{oh} px "
                f"(~{src.res[0]*dec:.1f} m)")
            arr = src.read(1, window=w, out_shape=(oh, ow), out_dtype="float32")
            tr = tfb(bb[0], bb[1], bb[2], bb[3], ow, oh)

        # uint16 centimetres -> metres. See the bucket readme; a max of 3814
        # would be 38 m of tree, which is right, or 3.8 km, which is not.
        h = arr / 100.0
        canopy = h >= CANOPY_MIN_HT_M
        px_m2 = ((bb[2] - bb[0]) / ow) * ((bb[3] - bb[1]) / oh)

        row_mask = None
        if row_geom is not None:
            row_mask = rasterize([(row_geom, 1)], out_shape=canopy.shape,
                                 transform=tr, fill=0, dtype="uint8").astype(bool)

        # One rasterise of hex INDEX per tile, then bincount — not one mask per
        # hex. The county has 2,695 hexes and 24 tiles; masking each hex against
        # each tile would be 64,680 passes over a 100-megapixel array, which does
        # not finish. This is the same arithmetic in two passes.
        idx = rasterize(
            ((g, i + 1) for i, g in enumerate(hx.geometry)),
            out_shape=canopy.shape, transform=tr, fill=0, dtype="int32")
        flat = idx.ravel()
        nb = len(hx) + 1
        px_tot += np.bincount(flat, minlength=nb)[1:]
        px_can += np.bincount(flat, weights=canopy.ravel(), minlength=nb)[1:]
        if row_mask is not None:
            rm = row_mask.ravel()
            row_tot += np.bincount(flat, weights=rm, minlength=nb)[1:]
            row_can += np.bincount(flat, weights=(rm & canopy.ravel()),
                                   minlength=nb)[1:]

    out = pd.DataFrame({"h3": hexes["h3"]})
    with np.errstate(invalid="ignore", divide="ignore"):
        out["canopy_pct"] = np.where(px_tot > 0, px_can / px_tot * 100, np.nan)
        out["row_canopy_pct"] = np.where(row_tot > 0, row_can / row_tot * 100, 0.0)
    px_m2_out = (READ_M_BIG if len(hx) > BIG_AREA_HEXES else READ_M) ** 2
    out["row_m2"] = (row_tot - row_can) * px_m2_out      # unshaded public strip
    out["row_m2"] = out["row_m2"].clip(lower=0).round(0)
    areas = gpd.read_file(C.GRID_FILE)[["h3", "area_m2"]]
    out = out.merge(areas, on="h3", how="left")
    out["canopy_m2"] = (out["canopy_pct"] / 100 * out["area_m2"]).round(0)
    out = out.drop(columns=["area_m2"])

    ok = out["canopy_pct"].notna()
    log(f"  canopy_pct: {out.loc[ok,'canopy_pct'].min():.1f}–"
        f"{out.loc[ok,'canopy_pct'].max():.1f}% (median "
        f"{out.loc[ok,'canopy_pct'].median():.1f}%)")
    log(f"  canopy area: {out.canopy_m2.sum()/1e6:.2f} km2 measured")
    log(f"  unshaded public right-of-way: {out.row_m2.sum()/1e6:.2f} km2")
    out.to_csv(C.CANOPY_CSV, index=False)
    log(f"  wrote {C.CANOPY_CSV.relative_to(C.ROOT)}")


if __name__ == "__main__":
    main()
