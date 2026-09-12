"""Phase 2d — measured tree canopy from the USFS / CAL FIRE 2022 product.

Reads the USFS/CAL FIRE 2022 urban-area classification and its matching
assessment boundaries. Canopy percentage uses assessed ground, not unassessed
land. Legacy height-map fallback values are retained with explicit provenance;
their coverage is unknown and they do not enable planting scenarios.

Outputs canopy_pct, canopy_m2, row_m2, row_canopy_pct plus canopy_source,
canopy_year, assessed_m2, coverage_frac and canopy_quality. ROW fields describe
a buffered street corridor, not verified public ownership or plantability.
"""
import glob
import sys

import numpy as np

import config as C

CANOPY_VALUE = 1          # USFS raster: 1 = canopy, 255 = nodata
CANOPY_MIN_HT_M = None    # not a height product; kept only so logs read the same
ROW_HALF_WIDTH_M = 7.0    # plantable strip half-width, matches 02c
STRIPE_ROWS = 2048        # window height; bounds memory on a county-size raster
SRC_DIR = C.CACHE / "canopy_src"


def log(msg):
    print(msg, flush=True)


def main():
    import geopandas as gpd
    import pandas as pd
    import rasterio
    from rasterio.windows import Window
    from rasterio.features import rasterize

    log(f"Phase 2d — canopy (USFS/CAL FIRE 2022) | {C.CITY}")
    tifs = sorted(glob.glob(str(SRC_DIR / "**" / "*_canopy2022.tif"), recursive=True))
    shps = glob.glob(str(SRC_DIR / "**" / "*.shp"), recursive=True)
    if not tifs:
        raise SystemExit(
            f"\nNo USFS canopy rasters in {SRC_DIR}.\n"
            f"Download this city's urban-area zip(s) from the USFS California Urban\n"
            f"Canopy page and unzip the *_canopy2022.tif + boundary *.shp into that\n"
            f"folder. See the module docstring.")

    hexes = gpd.read_file(C.GRID_FILE)[["h3", "geometry"]]
    cell_area = hexes.to_crs("EPSG:3310").geometry.area.to_numpy()
    seen_boundary = None
    n = len(hexes)
    px_tot = np.zeros(n)   # pixels of each hex that fall on assessed land
    px_can = np.zeros(n)   # of those, canopy
    row_tot = np.zeros(n)  # right-of-way pixels on assessed land
    row_can = np.zeros(n)  # of those, already shaded

    streets = None
    if C.STREETS_FILE.exists():
        streets = gpd.read_file(C.STREETS_FILE)
    else:
        log(f"  !! no {C.STREETS_FILE.name}; row_m2 will be 0. Run 04 first for it.")

    import os
    from rasterio.windows import from_bounds
    pix_area_m2 = None
    for tif in tifs:
        stem = tif[:-len("_canopy2022.tif")]
        # boundary shp for this urban area — beside the raster, or anywhere under
        # SRC_DIR (the USFS zips keep rasters in urbancanopy2022/ and boundaries
        # in a sibling urbanboundary/). Match by urban-area name.
        cand = glob.glob(os.path.join(os.path.dirname(tif), "*.shp")) or shps
        if not cand:
            raise SystemExit(f"  no urban-boundary .shp found for {os.path.basename(tif)}")
        bnd_path = _match_boundary(stem, cand)

        with rasterio.open(tif) as src:
            crs = src.crs
            if crs.to_epsg() != 3310:
                raise ValueError("Canopy area requires the source EPSG:3310 grid")
            if pix_area_m2 is not None and not np.isclose(pix_area_m2, abs(src.res[0] * src.res[1])):
                raise ValueError("Mixed source pixel areas are not supported")
            if pix_area_m2 is None:
                pix_area_m2 = float(src.res[0] * src.res[1])   # 3310 => exact ground m²
            bnd_union = gpd.read_file(bnd_path).to_crs(crs).geometry.union_all()
            # Never count overlapping assessments twice; deterministic file order.
            from shapely.geometry import box
            bnd_union = bnd_union.intersection(box(*src.bounds))
            if seen_boundary is not None:
                bnd_union = bnd_union.difference(seen_boundary)
            seen_boundary = bnd_union if seen_boundary is None else seen_boundary.union(bnd_union)
            hx = hexes.to_crs(crs)
            # Denominator geometry: each hex clipped to the assessed urban boundary,
            # so a hex overhanging into unassessed (rural) land does not count that
            # overhang as "no canopy" — only assessed pixels are the denominator.
            clipped = hx.geometry.intersection(bnd_union)
            row_geom = None
            if streets is not None:
                row_geom = (streets.to_crs(crs).geometry.buffer(ROW_HALF_WIDTH_M)
                            .union_all().intersection(bnd_union))
            rminx, rminy, rmaxx, rmaxy = src.bounds
            done = 0
            # Per-hex windowed read: each hex is ~0.1–0.8 km² (300k–2M px), so we
            # read only its own bounding box (the .ovr overviews make this cheap)
            # rather than striping the whole 2-billion-pixel raster. Scales to a
            # county by iterating more hexes, not by reading more per hex.
            for i, g in enumerate(clipped):
                if g.is_empty:
                    continue
                gx0, gy0, gx1, gy1 = g.bounds
                if gx1 <= rminx or gx0 >= rmaxx or gy1 <= rminy or gy0 >= rmaxy:
                    continue
                win = from_bounds(max(gx0, rminx), max(gy0, rminy),
                                  min(gx1, rmaxx), min(gy1, rmaxy),
                                  transform=src.transform)
                win = win.round_offsets().round_lengths()
                if win.width < 1 or win.height < 1:
                    continue
                arr = src.read(1, window=win)
                tr = src.window_transform(win)
                mask = rasterize([(g, 1)], out_shape=arr.shape, transform=tr,
                                 fill=0, dtype="uint8").astype(bool)
                canopy = (arr == CANOPY_VALUE) & mask
                px_tot[i] += int(mask.sum())
                px_can[i] += int(canopy.sum())
                if row_geom is not None and not row_geom.is_empty and g.intersects(row_geom):
                    rg = g.intersection(row_geom)
                    if not rg.is_empty:
                        rmask = rasterize([(rg, 1)], out_shape=arr.shape, transform=tr,
                                          fill=0, dtype="uint8").astype(bool)
                        row_tot[i] += int(rmask.sum())
                        row_can[i] += int((rmask & (arr == CANOPY_VALUE)).sum())
                done += 1
            log(f"  {os.path.basename(tif)}: assessed {done} hexes")

    out = pd.DataFrame({"h3": hexes["h3"]})
    with np.errstate(invalid="ignore", divide="ignore"):
        out["canopy_pct"] = np.where(px_tot > 0, px_can / px_tot * 100, np.nan)
        out["row_canopy_pct"] = np.where(row_tot > 0, row_can / row_tot * 100, 0.0)
    out["canopy_m2"] = (px_can * pix_area_m2).round(2)   # 2 dp: a single 0.36 m² pixel must not round to 0
    out["row_m2"] = ((row_tot - row_can) * pix_area_m2).clip(min=0).round(0)

    out["assessed_m2"] = (px_tot * pix_area_m2).round(2)
    out["coverage_frac"] = out["assessed_m2"] / cell_area
    if (out["coverage_frac"] > 1.002).any():
        raise ValueError("Assessed canopy area exceeds cell area")
    out["coverage_frac"] = out["coverage_frac"].clip(0, 1)
    out["canopy_source"] = np.where(px_tot > 0, "usfs-2022", "none")
    out["canopy_year"] = np.where(px_tot > 0, "2022", "")
    out["canopy_quality"] = np.where(px_tot > 0,
        np.where(out["coverage_frac"] >= .99, "full", "partial"), "unassessed")
    chm_path = C.CANOPY_CSV.with_name(C.CANOPY_CSV.stem + "_chm.csv")
    if chm_path.exists():
        out, filled = fill_legacy_canopy(out, pd.read_csv(chm_path))
        log(f"  filled {filled} cells from legacy CHM; coverage remains unknown")

    ok = out["canopy_pct"].notna()
    log(f"  canopy_pct: {out.loc[ok,'canopy_pct'].min():.1f}–"
        f"{out.loc[ok,'canopy_pct'].max():.1f}% (median "
        f"{out.loc[ok,'canopy_pct'].median():.1f}%, {ok.sum()}/{n} hexes assessed)")
    # population-weighted canopy sanity line — this is what the city will quote
    log(f"  canopy area: {out.canopy_m2.sum()/1e6:.2f} km² | "
        f"unshaded ROW: {out.row_m2.sum()/1e6:.2f} km²")
    out.to_csv(C.CANOPY_CSV, index=False)
    log(f"  wrote {C.CANOPY_CSV.relative_to(C.ROOT)}")


def fill_legacy_canopy(out, chm):
    """Freeze one aligned missing mask before filling any dependent fields."""
    out = out.set_index("h3").copy()
    chm = chm.set_index("h3").reindex(out.index)
    use = out["canopy_pct"].isna() & chm["canopy_pct"].notna()
    for col in ["canopy_pct", "row_canopy_pct", "canopy_m2", "row_m2"]:
        out.loc[use, col] = chm.loc[use, col] if col in chm else np.nan
    out.loc[use, "canopy_source"] = "chm-legacy"
    out.loc[use, "canopy_year"] = "2009-2020"
    out.loc[use, "canopy_quality"] = "coverage-unknown"
    out.loc[use, ["assessed_m2", "coverage_frac"]] = np.nan
    return out.reset_index(), int(use.sum())


def _match_boundary(stem, cands):
    """Require an exact urban-area filename match; never guess by prefix."""
    from pathlib import Path
    matches = [c for c in cands if Path(c).stem.lower() == Path(stem).name.lower()]
    if len(matches) != 1:
        raise ValueError(f"Expected one matching boundary for {Path(stem).name}")
    return matches[0]


if __name__ == "__main__":
    main()
