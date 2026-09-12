"""Phase 2 — land surface temperature and greenness per hex, from satellite.

Source: Microsoft Planetary Computer STAC (anonymous). Landsat C2-L2 thermal for
LST, Sentinel-2 L2A for NDVI, both summer-median so a single hot or cloudy day
can't drive the result.

Fallback chain, in order:
  1. STAC  ->  live scenes, and the composite is cached to data/*.tif
  2. data/lst.tif + data/ndvi.tif  ->  the cached composite, fully offline
  3. hard stop with an explanation (never silently fabricate a heat map)

Writes data/satellite.csv: h3, lst_c, green_pct.
"""
import sys
import warnings

import numpy as np
import pandas as pd
import rasterio
from rasterio.features import rasterize
from rasterio.transform import Affine

import config as C

warnings.filterwarnings("ignore", category=RuntimeWarning)   # all-NaN slice medians

STAC_URL = "https://planetarycomputer.microsoft.com/api/stac/v1"
LST_TIF = C.LST_TIF
NDVI_TIF = C.NDVI_TIF
OUT_CSV = C.SAT_CSV


# --------------------------------------------------------------------- helpers
def log(msg):
    print(msg, flush=True)


def read_grid():
    import geopandas as gpd
    gdf = gpd.read_file(C.GRID_FILE).to_crs(C.RASTER_CRS)
    log(f"  grid: {len(gdf)} hexes -> {C.RASTER_CRS}")
    return gdf


def write_tif(path, arr, transform):
    """Cache the composite so the next run — or a dead network — still works."""
    with rasterio.open(
        path, "w", driver="GTiff", height=arr.shape[0], width=arr.shape[1],
        count=1, dtype="float32", crs=C.RASTER_CRS, transform=transform,
        nodata=np.nan, compress="deflate",
    ) as dst:
        dst.write(arr.astype("float32"), 1)
    log(f"  cached {path.name} ({path.stat().st_size/1e6:.1f} MB)")


def read_tif(path):
    with rasterio.open(path) as src:
        return src.read(1).astype("float32"), src.transform


def zonal_mean(arr, transform, gdf):
    """Mean of `arr` per hex.

    Rasterise the hexes once and reduce with bincount rather than looping
    polygons — 3.5k separate zonal_stats windows is needlessly slow.
    """
    zones = rasterize(
        ((geom, i) for i, geom in enumerate(gdf.geometry, start=1)),
        out_shape=arr.shape, transform=transform, fill=0, dtype="int32",
    )
    ok = (zones > 0) & np.isfinite(arr)
    z, v = zones[ok], arr[ok]
    n = len(gdf) + 1
    total = np.bincount(z, weights=v, minlength=n)
    count = np.bincount(z, minlength=n)
    with np.errstate(invalid="ignore", divide="ignore"):
        mean = np.where(count > 0, total / np.maximum(count, 1), np.nan)
    covered = int((count[1:] > 0).sum())
    if covered < len(gdf):
        log(f"    note: {len(gdf)-covered} hexes had no valid pixels")
    return mean[1:]


# ------------------------------------------------------------------ STAC loads
def tile_key(item):
    """Which satellite tile a scene belongs to, for per-tile scene budgeting.

    Sentinel-2 is gridded by MGRS tile, Landsat by WRS-2 path/row. Falls back to
    a rounded bbox centroid so an unknown collection still gets grouped by
    location rather than collapsing into one bucket.
    """
    p = item.properties
    if "s2:mgrs_tile" in p:
        return f"mgrs:{p['s2:mgrs_tile']}"
    if "landsat:wrs_path" in p:
        return f"wrs:{p['landsat:wrs_path']}/{p.get('landsat:wrs_row')}"
    bb = item.bbox or [0, 0, 0, 0]
    return f"bbox:{round((bb[0] + bb[2]) / 2, 1)},{round((bb[1] + bb[3]) / 2, 1)}"


def search(catalog, collection, extra_query=None):
    """Scenes inside the summer window of EACH configured year.

    One search per year, then concatenate — never a single continuous range
    across years. A 2022-06-01/2024-09-15 range would happily return January
    2023, and a thermal median containing winter scenes is not a summer surface
    temperature. Costs two extra HTTP round trips and removes a whole class of
    silent wrongness.
    """
    q = {"eo:cloud_cover": {"lt": C.MAX_CLOUD_PCT}}
    if extra_query:
        q.update(extra_query)
    mm_lo, mm_hi = C.SUMMER_MMDD
    items, seen = [], set()
    for yr in C.SUMMER_YEARS:
        for it in catalog.search(
            collections=[collection], bbox=C.BBOX,
            datetime=f"{yr}-{mm_lo}/{yr}-{mm_hi}", query=q,
        ).items():
            if it.id not in seen:
                seen.add(it.id)
                items.append(it)
    # Least cloudy first, then cap PER TILE — not globally.
    #
    # A global sort-then-cap is fine for a city inside one satellite tile, and
    # quietly catastrophic for anything larger. Contra Costa spans several
    # Sentinel-2 MGRS tiles; taking the 30 least cloudy scenes county-wide took
    # them almost entirely from the clearest tile and left the rest with nothing,
    # so NDVI came back 37% valid with 1,723 of 2,859 hexes empty. The scenes
    # existed — they were sorted out of the running by a neighbouring tile that
    # happened to have clearer weather.
    #
    # Capping per tile keeps the runtime bound (the point of MAX_SCENES) while
    # guaranteeing every part of the study area gets its own best scenes.
    # SCENE_CAP_PER_TILE=False (San Ramon) reproduces the older global cap that
    # its committed composites were built with.
    items.sort(key=lambda i: i.properties.get("eo:cloud_cover", 100))
    by_tile = {}
    for it in items:
        by_tile.setdefault(tile_key(it) if C.SCENE_CAP_PER_TILE else "all", []).append(it)
    items = [it for group in by_tile.values() for it in group[: C.MAX_SCENES]]
    if items:
        cc = sorted(i.properties.get("eo:cloud_cover", 0) for i in items)
        log(f"  {collection}: {len(items)} scenes across {len(by_tile)} tiles "
            f"(cloud {cc[0]:.0f}–{cc[-1]:.0f}%, max {C.MAX_SCENES}/tile)")
    else:
        log(f"  {collection}: 0 scenes")
    return items


def load_stack(items, bands):
    import odc.geo.xr          # registers the .odc accessor used for the transform
    from odc.stac import load as odc_load
    ds = odc_load(
        items, bands=bands, bbox=C.BBOX, crs=C.RASTER_CRS,
        resolution=C.RASTER_RES_M, groupby="solar_day", chunks={},
    )
    return ds


def landsat_lst(catalog):
    items = search(catalog, "landsat-c2-l2",
                   {"platform": {"in": ["landsat-8", "landsat-9"]}})
    if not items:
        raise RuntimeError("no Landsat scenes matched")

    ds = load_stack(items, ["lwir11", "qa_pixel"]).compute()
    dn = ds["lwir11"].astype("float32").where(lambda a: a != 0)   # 0 = nodata

    # QA_PIXEL bits 1-4: dilated cloud, cirrus, cloud, cloud shadow. Clouds read
    # cold, so leaving them in would drag LST down exactly where it matters.
    qa = ds["qa_pixel"].astype("uint16")
    cloudy = ((qa >> 1) & 1) | ((qa >> 2) & 1) | ((qa >> 3) & 1) | ((qa >> 4) & 1)
    dn = dn.where(cloudy == 0)

    # odc-stac hands back raw DN; apply the collection's scale/offset -> Kelvin.
    # Guard in case a future version starts scaling for us.
    med = dn.median(dim="time", skipna=True)
    vals = med.values.astype("float32")
    if np.nanmedian(vals) > 1000:
        vals = vals * 0.00341802 + 149.0
    celsius = vals - 273.15

    finite = np.isfinite(celsius)
    log(f"  LST: {finite.mean()*100:.0f}% valid px, "
        f"{np.nanpercentile(celsius,2):.1f}–{np.nanpercentile(celsius,98):.1f} °C")
    if not (0 < np.nanmedian(celsius) < 70):
        raise RuntimeError(f"LST median {np.nanmedian(celsius):.1f} °C is implausible")

    transform = ds.odc.geobox.transform
    write_tif(LST_TIF, celsius, transform)
    return celsius, transform


def sentinel_ndvi(catalog):
    items = search(catalog, "sentinel-2-l2a")
    if not items:
        raise RuntimeError("no Sentinel-2 scenes matched")

    # Sentinel-2 processing baseline >= 04.00 carries BOA_ADD_OFFSET = -1000, and
    # Planetary Computer does not pre-apply it (no raster:bands, boa_offset_applied
    # unset). It does NOT cancel in a ratio: skipping it biases NDVI low across the
    # board — LA's median came out 0.12 instead of ~0.3, flattening the greenness
    # layer to zero for half the city.
    baselines = {float(i.properties.get("s2:processing_baseline", 0)) for i in items}
    if baselines and min(baselines) >= 4.0:
        offset = -1000.0
        log(f"  S2 baseline {min(baselines):.2f}–{max(baselines):.2f}: applying BOA offset {offset:+.0f}")
    else:
        offset = 0.0
        log(f"  S2 baselines mixed/old {sorted(baselines)}: no BOA offset applied")

    ds = load_stack(items, ["B04", "B08", "SCL"]).compute()
    red = ds["B04"].astype("float32") + offset
    nir = ds["B08"].astype("float32") + offset
    # Post-offset non-positives are noise/dark pixels, not surfaces.
    red = red.where(red > 0)
    nir = nir.where(nir > 0)

    # SCL: drop saturated/shadow/cloud/cirrus/snow, keep vegetation/soil/water.
    scl = ds["SCL"]
    bad = scl.isin([0, 1, 2, 3, 8, 9, 10, 11])
    red = red.where(~bad)
    nir = nir.where(~bad)

    with np.errstate(invalid="ignore", divide="ignore"):
        ndvi = (nir - red) / (nir + red)
    ndvi = ndvi.where(np.isfinite(ndvi)).clip(-1, 1)

    med = ndvi.median(dim="time", skipna=True).values.astype("float32")
    log(f"  NDVI: {np.isfinite(med).mean()*100:.0f}% valid px, "
        f"{np.nanpercentile(med,2):.2f}–{np.nanpercentile(med,98):.2f}")

    transform = ds.odc.geobox.transform
    write_tif(NDVI_TIF, med, transform)
    return med, transform


def ndvi_to_canopy(ndvi):
    """NDVI -> canopy-% proxy. Explicitly a proxy, not measured crown cover."""
    lo, hi = C.NDVI_CLAMP
    frac = np.clip((ndvi - lo) / (hi - lo), 0, 1)
    return frac * C.CANOPY_MAX_PCT


# ------------------------------------------------------------------------ main
def main():
    yrs = "/".join(str(y) for y in C.SUMMER_YEARS)
    log(f"Phase 2 — satellite | {C.CITY} | {C.SUMMER_MMDD[0]}..{C.SUMMER_MMDD[1]} of {yrs}")
    gdf = read_grid()

    # --cached skips the network entirely: recalibrating the NDVI mapping or
    # rehearsing the offline demo shouldn't re-pull 32 scenes.
    cached_only = "--cached" in sys.argv

    lst = ndvi = None
    try:
        if cached_only:
            raise RuntimeError("--cached requested")
        import planetary_computer
        import pystac_client
        cat = pystac_client.Client.open(STAC_URL, modifier=planetary_computer.sign_inplace)
        log("  source: Planetary Computer STAC (anonymous)")
        lst, lst_tf = landsat_lst(cat)
        ndvi, ndvi_tf = sentinel_ndvi(cat)
    except Exception as e:
        log("  source: cached rasters (--cached)" if cached_only
            else f"  STAC unavailable ({type(e).__name__}: {e})")
        if LST_TIF.exists() and NDVI_TIF.exists():
            log("  falling back to cached rasters")
            lst, lst_tf = read_tif(LST_TIF)
            ndvi, ndvi_tf = read_tif(NDVI_TIF)
        else:
            raise SystemExit(
                "\nNo satellite data and no cache.\n"
                f"Need network for {STAC_URL}, or commit {LST_TIF.name} and "
                f"{NDVI_TIF.name} to data/.\n"
                "Refusing to invent a heat map — the whole claim is that this is real."
            )

    log("  zonal stats...")
    lst_hex = zonal_mean(lst, lst_tf, gdf)
    ndvi_hex = zonal_mean(ndvi, ndvi_tf, gdf)
    green_hex = ndvi_to_canopy(ndvi_hex)

    out = pd.DataFrame({
        "h3": gdf["h3"].values,
        "lst_c": np.round(lst_hex, 2),
        "green_pct": np.round(green_hex, 2),
    })

    missing = int(out["lst_c"].isna().sum())
    if missing:
        log(f"  {missing} hexes missing LST — filling with city median")
        out["lst_c"] = out["lst_c"].fillna(out["lst_c"].median())
        out["green_pct"] = out["green_pct"].fillna(out["green_pct"].median())

    out.to_csv(OUT_CSV, index=False)
    log(f"  LST   {out.lst_c.min():.1f}–{out.lst_c.max():.1f} °C "
        f"(median {out.lst_c.median():.1f})")
    log(f"  green {out.green_pct.min():.1f}–{out.green_pct.max():.1f} % "
        f"(median {out.green_pct.median():.1f})")
    log(f"  wrote {OUT_CSV.relative_to(C.ROOT)}")


if __name__ == "__main__":
    main()
