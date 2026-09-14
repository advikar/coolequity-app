"""Phase 2f — validate the app's tree-cover input against an independent lidar map.

The audit's last open data item: the tree-cover column (`green`) pools three
sources — USFS/EarthDefine 2022 aerial canopy where census urban areas are
covered, the Meta/WRI canopy height model ("chm-legacy") elsewhere, and a
satellite greenness stand-in where neither covers 10% of a cell — on one
normalised scale, and nobody had checked whether those sources read the same
ground the same way. Field visits were the assumed fix. A better one exists for
every Contra Costa build: CDFW's 2025 fine-scale vegetation map of Alameda and
Contra Costa counties (BIOS ds3206, CC-BY) carries a lidar-derived canopy cover
for each of its 140,442 polygons, mapped at the same minimum mapping unit inside
the urban core as outside.

    ABS_COVER  = % of lidar returns above 15 ft (4.6 m), 2017–2022 lidar, per polygon

That is the reference here. It is NOT the same quantity as the app's input: the
app counts any tree crown (USFS) or vegetation over 2 m (height model), the lidar
figure counts returns above 4.6 m, so young street trees and tall shrubs are in
ours and not in theirs. Expect the app to read higher. What matters is whether
the offset is the SAME for every source class; if the height-model cells sit on a
different line from the aerial cells, pooling them was distorting the ranking and
the fitted lines say by how much.

    COOLEQUITY_CITY=westcc python pipeline/02f_canopy_validate.py \
        --gdb /path/to/ds3206.gdb

Writes reports/canopy_validation_<slug>.json: per source class and per context
(city, unincorporated, agricultural), n, bias, MAE, RMSE, Pearson, Spearman and
the fitted line app = a + b·lidar, plus the two fits 05 uses; and
data/canopy_lidar_<slug>.csv with the per-cell lidar figure. 05 then rescales
height-model cells onto the aerial line and replaces the greenness stand-in
with lidar canopy where the map covers ≥90% of the cell. Bakersfield is outside
the map (Kern County) and keeps the pooled input; its guide says so.
"""
import argparse
import json
import sys
import time

import numpy as np
import pandas as pd

import config as C

LIDAR_MIN_HT_FT = 15
AG_LIFEFORMS = ("Agricultur", "Orchard", "Vineyard", "Row Crop")
MIN_COVERAGE = 0.90          # a cell must be ≥90% covered by map polygons to be compared


def classify(p):
    src, q = p.get("green_src"), p.get("canopy_quality")
    if src == "ndvi":
        return "greenness stand-in"
    cs = p.get("canopy_source")
    if cs == "usfs-2022":
        return "aerial · full" if q == "full" else "aerial · partial"
    if cs == "chm-legacy":
        return "height model"
    return "other"


def metrics(a, l):
    a, l = np.asarray(a, float), np.asarray(l, float)
    n = len(a)
    if n < 8:
        return {"n": int(n)}
    d = a - l
    b, a0 = np.polyfit(l, a, 1)
    return {"n": int(n), "app_mean": round(float(a.mean()), 2), "lidar_mean": round(float(l.mean()), 2),
            "bias": round(float(d.mean()), 2), "mae": round(float(np.abs(d).mean()), 2),
            "rmse": round(float(np.sqrt((d ** 2).mean())), 2),
            "pearson": round(float(np.corrcoef(a, l)[0, 1]), 3),
            "spearman": round(float(pd.Series(a).rank().corr(pd.Series(l).rank())), 3),
            "fit_intercept": round(float(a0), 2), "fit_slope": round(float(b), 3)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gdb", required=True, help="path to ds3206.gdb (CDFW BIOS, Alameda & Contra Costa fine-scale vegetation)")
    args = ap.parse_args()
    import geopandas as gpd
    import pyogrio
    from shapely.geometry import box
    t0 = time.time()
    print(f"Phase 2f — canopy validation against lidar | {C.CITY}")

    grid = gpd.read_file(C.GRID_FILE)[["h3", "geometry"]].set_crs(4326, allow_override=True)
    scored = pd.DataFrame(gpd.read_file(C.DATA / f"{C.SLUG}.geojson").drop(columns="geometry"))
    scored = scored.merge(gpd.read_file(C.GRID_FILE)[["h3", "id"]], on="id", how="left")   # scored cells carry the numeric id; h3 lives on the grid
    keep = ["h3", "green", "green_src", "canopy_source", "canopy_quality", "rank", "city_kind", "land"]
    scored = scored[[k for k in keep if k in scored.columns]]

    w, s, e, n = C.BBOX
    bbox3310 = gpd.GeoSeries([box(w, s, e, n)], crs=4326).to_crs(3310).total_bounds
    veg = pyogrio.read_dataframe(args.gdb, layer="ds3206", bbox=tuple(bbox3310),
                                 columns=["ABS_COVER", "LIFEFORM", "SOURCE"], force_2d=True)
    print(f"  lidar map: {len(veg):,} polygons in bbox ({time.time()-t0:.0f}s)")
    veg = veg[veg["ABS_COVER"].notna()].copy()
    veg["ag"] = veg["LIFEFORM"].fillna("").str.contains("|".join(AG_LIFEFORMS), case=False)

    g = grid.to_crs(3310)
    g["hex_m2"] = g.geometry.area
    pairs = gpd.sjoin(g[["h3", "hex_m2", "geometry"]], veg, how="inner", predicate="intersects")
    vg = veg.geometry.values
    inter = gpd.GeoSeries(pairs.geometry.values, crs=3310).intersection(gpd.GeoSeries(vg[pairs["index_right"].values], crs=3310))
    pairs["a"] = inter.area.values
    pairs["ca"] = pairs["a"] * pairs["ABS_COVER"] / 100.0
    pairs["aga"] = pairs["a"] * pairs["ag"]
    per = pairs.groupby("h3").agg(hex_m2=("hex_m2", "first"), a=("a", "sum"), ca=("ca", "sum"), aga=("aga", "sum"))
    per["lidar_pct"] = 100 * per["ca"] / per["a"]
    per["coverage"] = per["a"] / per["hex_m2"]
    per["ag_frac"] = per["aga"] / per["a"]
    print(f"  {len(per):,} cells touched; {(per.coverage>=MIN_COVERAGE).sum():,} covered ≥{MIN_COVERAGE:.0%} ({time.time()-t0:.0f}s)")

    df = scored.merge(per[["lidar_pct", "coverage", "ag_frac"]], on="h3", how="inner")
    df = df[df["rank"].notna() & (df["coverage"] >= MIN_COVERAGE)].copy()
    df["cls"] = df.apply(classify, axis=1)
    df["ctx"] = np.where(df["ag_frac"] >= 0.3, "agricultural",
                np.where(df["city_kind"].isin(["city", "cdp"]), "city or CDP", "unincorporated"))
    out = {"city": C.CITY, "slug": C.SLUG, "run": time.strftime("%Y-%m-%d"),
           "reference": {"dataset": "CDFW BIOS ds3206, Alameda & Contra Costa fine-scale vegetation map (2025)",
                         "field": f"ABS_COVER: % lidar returns above {LIDAR_MIN_HT_FT} ft, 2017-2022 lidar, per polygon",
                         "aggregation": "area-weighted over the H3 cell; cells under 90% covered are dropped",
                         "note": "counts vegetation above 4.6 m only; the app counts any crown (USFS) or >2 m (height model), so the app should read higher"},
           "ranked_cells_compared": int(len(df)), "ranked_cells_total": int(scored["rank"].notna().sum()),
           "all": metrics(df["green"], df["lidar_pct"]),
           "by_source": {k: metrics(v["green"], v["lidar_pct"]) for k, v in df.groupby("cls")},
           "by_source_and_context": {f"{k[0]} | {k[1]}": metrics(v["green"], v["lidar_pct"]) for k, v in df.groupby(["cls", "ctx"])},
           "top25_by_source": df[df["rank"] <= 25]["cls"].value_counts().to_dict()}
    # residual by source after removing the common line: is any source on its own line?
    b, a0 = np.polyfit(df["lidar_pct"], df["green"], 1)
    df["resid"] = df["green"] - (a0 + b * df["lidar_pct"])
    out["residual_by_source_vs_common_fit"] = {k: {"n": int(len(v)), "mean_resid": round(float(v["resid"].mean()), 2),
                                                   "sd_resid": round(float(v["resid"].std()), 2)} for k, v in df.groupby("cls")}
    # Hand the per-cell lidar figure and the two fitted lines to 05, which uses them to
    # (a) put height-model cells on the aerial scale and (b) replace the greenness
    # stand-in with lidar canopy where the map covers the cell. See 05 load().
    aer, hm = out["by_source"].get("aerial · full", {}), out["by_source"].get("height model", {})
    out["calibration"] = {"aerial_full": {k: aer.get(k) for k in ("n", "spearman", "fit_intercept", "fit_slope")},
                          "height_model": {k: hm.get(k) for k in ("n", "spearman", "fit_intercept", "fit_slope")},
                          "min_n": 50, "min_spearman": 0.8, "use": "05_score.py: chm-legacy cells -> aerial scale via lidar; ndvi cells -> lidar canopy on the aerial scale"}
    per.reset_index()[["h3", "lidar_pct", "coverage"]].rename(columns={"coverage": "lidar_coverage"}).round(4).to_csv(C.DATA / f"canopy_lidar_{C.SLUG}.csv", index=False)
    rep = C.ROOT / "cities" / C.SLUG / "reports" / f"canopy_validation_{C.SLUG}.json"
    rep.parent.mkdir(exist_ok=True)
    rep.write_text(json.dumps(out, indent=1))
    print(f"  all: {out['all']}")
    for k, v in out["by_source"].items():
        print(f"  {k:22} {v}")
    for k, v in out["residual_by_source_vs_common_fit"].items():
        print(f"  resid {k:22} {v}")
    print(f"  top-25 by source: {out['top25_by_source']}")
    print(f"  wrote {rep.relative_to(C.ROOT)} ({time.time()-t0:.0f}s)")


if __name__ == "__main__":
    main()
