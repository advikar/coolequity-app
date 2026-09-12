"""Phase 5 — fuse every layer into one priority score, and write the app's data.

    base_risk = 0.35*heat + 0.25*(1-green) + 0.25*(1-ac) + 0.15*age65
    priority  = base_risk * (0.55 + 0.45*population)
    score     = 100 * minmax(priority)

Every input is min-max normalised *within the city* before it enters the sum.
That is the portability argument: 44 C is an ordinary afternoon in Phoenix and an
emergency in Seattle, so an absolute threshold would rank cities, not
neighborhoods. Weights live in config.py — a judge will ask why 35%.

Reads grid.geojson + satellite.csv + census.csv + overlays.csv.
Writes data/la.geojson — the one file the front end loads.
"""
import json
import sys

import numpy as np
import pandas as pd

import config as C

# The front end reads exactly these. Renaming one breaks the UI silently —
# MapLibre just paints a hex the no-data colour and moves on.
CONTRACT = ["id", "name", "lst", "green", "pop", "pct65", "ac", "holc",
            "access_min", "access_km", "score", "rank", "area_m2", "street_m",
            "canopy_m2", "row_m2", "row_canopy", "veg", "place", "land", "green_src", "canopy_source", "canopy_year", "assessed_m2",
            "coverage_frac", "canopy_quality", "scenario_ok", "canopy_baseline_ok", "ac_src", "ac_coverage", "acs_year", "access_snap_m", "access_quality", "access_src"]

COORD_DP = 5      # ~1 m at this latitude; halves the file the browser downloads


def log(msg):
    print(msg, flush=True)


def minmax(s):
    lo, hi = s.min(), s.max()
    if not np.isfinite(lo) or hi == lo:
        return pd.Series(np.zeros(len(s)), index=s.index)
    return (s - lo) / (hi - lo)


# Percentile-clipped normalisation for the SCORING inputs. Plain min-max lets a
# single outlier set the scale: one 92%-canopy hex compresses the "missing
# canopy" term across every other block, and a handful of very crowded hexes pin
# ~98% of the population multiplier near its floor.
#
# The clip is ONE-SIDED, and on purpose. We only pull in the tail that represents
# the LEAST need — a single fully-canopied block, a single empty-cool one — so it
# stops setting the scale. We never touch the most-in-need tail, because the
# hottest, oldest and barest blocks are exactly what the tool exists to rank, and
# clipping them would blunt it (a two-sided clip flattened Rossmoor's 84%-elderly
# down to an ordinary block and broke the "Protect seniors" view). Population is
# a saturating multiplier — 2,500 people and 5,600 are both "a lot" — so it is
# clipped at the crowded end.
#
# Which end is benign is read off the score formula: protective inputs enter as
# (1-n) so their HIGH end is low-need; risk inputs enter as n so their LOW end is.
# Display values and colour ramps still use the raw range (this is score-only),
# and these endpoints are written into the geojson so the front end normalises
# against the identical bounds rather than recomputing percentiles a different way.
CLIP_LO_Q, CLIP_HI_Q = 2.0, 98.0


def clip_bounds(s, clip_high):
    """One-sided percentile clip. clip_high pulls the top tail in to p98 (the
    benign end for protective inputs and the saturating end for population);
    otherwise the bottom tail comes in to p2 and the true maximum is kept."""
    if clip_high:
        lo, hi = float(s.min()), float(np.percentile(s, CLIP_HI_Q))
    else:
        lo, hi = float(np.percentile(s, CLIP_LO_Q)), float(s.max())
    if not np.isfinite(lo) or hi <= lo:            # degenerate: fall back to range
        lo, hi = float(s.min()), float(s.max())
    return lo, hi


def clip_minmax(s, bounds):
    lo, hi = bounds
    if hi <= lo:
        return pd.Series(np.zeros(len(s)), index=s.index)
    return ((s - lo) / (hi - lo)).clip(0.0, 1.0)


def shrink_age65(pop, pct65):
    """Empirical-Bayes smoothing of the 65+ share toward the citywide rate."""
    pop65 = pop * pct65 / 100.0
    city = pop65.sum() / pop.sum()               # citywide rate, 0..1
    k = C.AGE65_SHRINK_POP
    return (pop65 + k * city) / (pop + k) * 100.0


def building_counts(h3_series):
    """Buildings per hex from the 02b footprints, by centroid. A hex with no
    residents but several buildings is developed, which street length can miss."""
    if not C.BUILDINGS_FILE.exists():
        return {}
    import geopandas as gpd
    b = gpd.read_file(C.BUILDINGS_FILE).to_crs(C.RASTER_CRS)
    b = b.set_geometry(b.geometry.centroid)
    grid = gpd.read_file(C.GRID_FILE).to_crs(C.RASTER_CRS)[["h3", "geometry"]]
    hit = gpd.sjoin(b[["geometry"]], grid, how="inner", predicate="within")
    return hit.groupby("h3").size().to_dict()


def classify_land(df):
    """Best-effort land-type label for EMPTY hexes from the satellite layers we
    already have: water reads cool+unvegetated, woodland high-canopy, open green
    ground high-NDVI/low-canopy, the rest bare/dry hillside. Approximate by design."""
    lst = df["lst_c"]
    veg = df["veg_pct"] if "veg_pct" in df.columns else df["green_pct"]
    can = (df["canopy_pct"] if "canopy_pct" in df.columns
           else pd.Series(0.0, index=df.index)).fillna(0)
    cool = lst.quantile(0.10)
    return np.where((lst <= cool) & (veg < 12), "open water",
           np.where(can > 25, "woodland",
           np.where(veg >= 35, "open land",
                    "bare / hillside")))


def round_coords(geom):
    return [[[round(x, COORD_DP), round(y, COORD_DP)] for x, y in ring]
            for ring in geom["coordinates"]]


def load():
    grid = json.loads(C.GRID_FILE.read_text())
    props = pd.DataFrame([f["properties"] for f in grid["features"]])

    df = props
    for path in (C.SAT_CSV, C.CENSUS_CSV, C.OVERLAYS_CSV):
        if not path.exists():
            raise SystemExit(
                f"\nMissing {path.relative_to(C.ROOT)}.\n"
                f"Run the pipeline in order: 01, 02, 03, 04, then 05."
            )
        df = df.merge(pd.read_csv(path), on="h3", how="left")

    df["green_src"] = "ndvi"

    # Preserve the satellite proxy separately and attach explicit canopy provenance.
    if C.CANOPY_CSV.exists():
        df = df.merge(pd.read_csv(C.CANOPY_CSV), on="h3", how="left")
        have = df["canopy_pct"].notna()
        df.loc[have, "green_src"] = "canopy"
        log(f"  canopy-source values for {int(have.sum())}/{len(df)} cells; NDVI elsewhere")
        df["veg_pct"] = df["green_pct"]
        df["green_pct"] = df["canopy_pct"].where(have, df["green_pct"])
    else:
        log("  canopy: no canopy CSV — using the NDVI proxy, which overstates "
            "tree cover roughly 2x. Run 02c_canopy.py.")

    # Authoritative land cover (ESA WorldCover 2021) for the empty-hex `land`
    # label. Merged under `wc_land` so it does not collide with the `land` column
    # main() builds; applied to empty hexes there, heuristic kept as a fallback.
    if C.WORLDCOVER_CSV.exists():
        wc = pd.read_csv(C.WORLDCOVER_CSV)[["h3", "land"]].rename(
            columns={"land": "wc_land"})
        df = df.merge(wc, on="h3", how="left")
        log(f"  land cover: ESA WorldCover 2021 for "
            f"{int(df['wc_land'].notna().sum())}/{len(df)} hexes")
    else:
        log("  land cover: no WorldCover CSV — empty hexes fall back to the "
            "lst/veg heuristic. Run 02e_worldcover.py for authoritative labels.")

    missing = df["lst_c"].isna().sum() + df["pop"].isna().sum()
    if missing:
        raise SystemExit(f"\n{missing} hexes missing inputs — rerun 02/03/04.")
    return grid, df


def main():
    log(f"Phase 5 — score | {C.CITY}")
    grid, df = load()
    log(f"  merged: {len(df)} hexes x {len(df.columns)} fields")

    # Three classes, and NOTHING is dropped — every hex stays on the map:
    #   res      — has residents: scored and ranked.
    #   activity — developed but unpopulated (street frontage OR buildings): a
    #              commercial/industrial block people use all day. Shown with real
    #              canopy/heat, greyed on Priority, not ranked by residential need.
    #   empty    — undeveloped: shown muted, with a best-effort land label.
    df["bldg_n"] = df["h3"].map(building_counts(df["h3"])).fillna(0).astype(int)
    street = (df["street_m"].fillna(0) if "street_m" in df.columns
              else pd.Series(0.0, index=df.index))
    developed = ((street >= 120.0) | (df["bldg_n"] >= 3)
                 | ((street >= 40.0) & (df["bldg_n"] >= 1)))
    df["place"] = np.where(df["pop"] >= C.MIN_POP, "res",
                           np.where(developed, "activity", "empty"))
    # Land label for empty hexes: authoritative ESA WorldCover 2021 where present,
    # the lst/veg heuristic only as a fallback for any hex WorldCover misses.
    df["land"] = classify_land(df)
    if "wc_land" in df.columns:
        df["land"] = df["wc_land"].where(df["wc_land"].notna(), df["land"])
    df.loc[df["place"] != "empty", "land"] = None
    nres, nact, nemp = [(df["place"] == v).sum() for v in ("res", "activity", "empty")]
    log(f"  {nres} residential (ranked) + {nact} developed-unpopulated (shown, not "
        f"ranked) + {nemp} empty (shown muted + labelled); all kept on the map")
    res = (df["place"] == "res").values

    df["pct65_s"] = shrink_age65(df["pop"], df["pct65"])
    log(f"  pct65: raw max {df.pct65.max():.1f}% -> smoothed "
        f"{df.pct65_s.max():.1f}% (median {df.pct65_s.median():.1f}%)")

    # p2/p98 endpoints per scoring input, computed once and reused by the app.
    # Keyed by the PROPERTY NAME the front end reads, so it can look them up.
    # clip_high=True on the protective inputs (green, ac) and on population; the
    # risk inputs (heat, age) keep their true maximum and clip the cool/young tail.
    # Bounds/normalisation computed on RESIDENTIAL hexes only, so a handful of
    # developed-unpopulated blocks never stretch the ramp or move a resident's rank.
    R = df.loc[res]
    bounds = {
        "lst":   clip_bounds(R["lst_c"],    clip_high=False),
        "green": clip_bounds(R["green_pct"], clip_high=True),
        "ac":    clip_bounds(R["ac_est"],    clip_high=True),
        "pct65": clip_bounds(R["pct65_s"],  clip_high=False),
        "pop":   clip_bounds(R["pop"],       clip_high=True),
    }
    log("  score inputs clipped to p2/p98: " + ", ".join(
        f"{k} {lo:.1f}–{hi:.1f}" for k, (lo, hi) in bounds.items()))
    n = pd.DataFrame({
        "heat":  clip_minmax(df["lst_c"], bounds["lst"]),
        "green": clip_minmax(df["green_pct"], bounds["green"]),
        "ac":    clip_minmax(df["ac_est"], bounds["ac"]),
        "age65": clip_minmax(df["pct65_s"], bounds["pct65"]),
        "pop":   clip_minmax(df["pop"], bounds["pop"]),
    })

    W = C.WEIGHTS
    base = (W["heat"] * n["heat"]
            + W["green"] * (1 - n["green"])
            + W["ac"] * (1 - n["ac"])
            + W["age65"] * n["age65"])
    priority = base * (C.POP_FLOOR + C.POP_WEIGHT * n["pop"])

    # Score and rank RESIDENTIAL hexes only; activity hexes get null score/rank
    # (they show canopy/heat but are not part of the resident-need ranking). Rank
    # the unrounded priority so rounding to 1dp does not manufacture ties.
    df["score"] = np.nan
    df["rank"] = np.nan
    pr = priority[res]
    df.loc[res, "score"] = (100 * minmax(pr)).values
    df.loc[res, "rank"] = pr.rank(method="first", ascending=False).values

    df["access_min"] = df["access_min"].fillna(df["access_min"].median())
    df["access_km"] = df["access_km"].fillna(df["access_km"].median())

    out = pd.DataFrame({
        "id":         df["id"].astype(int),
        "name":       df["name"].fillna("Unnamed"),
        "lst":        df["lst_c"].round(2),
        "green":      df["green_pct"].round(2),
        "green_src":  df["green_src"],
        "canopy_source": df.get("canopy_source", pd.Series("unknown", index=df.index)).fillna("unknown"),
        "canopy_year": df.get("canopy_year", pd.Series(None, index=df.index)),
        "assessed_m2": df.get("assessed_m2", pd.Series(np.nan, index=df.index)),
        "coverage_frac": df.get("coverage_frac", pd.Series(np.nan, index=df.index)),
        "canopy_quality": df.get("canopy_quality", pd.Series("unknown", index=df.index)),
        # 99% is an explicit operational coverage threshold, not a validation claim.
        "scenario_ok": (df["street_m"].fillna(0) > 0) & (df["area_m2"] > 0),
        "canopy_baseline_ok": ((df.get("canopy_source", pd.Series("", index=df.index)) == "usfs-2022") &
                        (df.get("coverage_frac", pd.Series(0., index=df.index)) >= .99)),
        "ac_src": df.get("ac_src", pd.Series("unknown", index=df.index)),
        "ac_coverage": df.get("ac_coverage", pd.Series(np.nan, index=df.index)),
        "acs_year": df.get("acs_year", pd.Series(C.ACS_YEAR, index=df.index)),
        # Legacy scaled NDVI proxy. Subtracting canopy does not identify non-tree cover.
        "veg":        (df["veg_pct"] if "veg_pct" in df.columns
                       else df["green_pct"]).round(1),
        "canopy_m2":  (df["canopy_m2"] if "canopy_m2" in df.columns
                       else df["green_pct"] / 100 * df["area_m2"]).round(0),
        # Plantable public ground: street right-of-way not already shaded. The
        # one figure here that describes what the CITY can do, as opposed to
        # what the block needs.
        "row_m2":     (df["row_m2"] if "row_m2" in df.columns
                       else pd.Series(0, index=df.index)).fillna(0).round(0),
        "row_canopy": (df["row_canopy_pct"] if "row_canopy_pct" in df.columns
                       else pd.Series(0.0, index=df.index)).fillna(0).round(1),
        "pop":        df["pop"].round(0).astype(int),
        "pct65":      df["pct65_s"].round(1),
        "ac":         df["ac_est"].round(2),
        "holc":       df["holc"],
        "access_min": df["access_min"].round(1),
        "access_km":  df["access_km"].round(2),
        "access_snap_m": df.get("access_snap_m", pd.Series(np.nan,index=df.index)),
        "access_quality": df.get("access_quality", pd.Series("unknown",index=df.index)),
        "access_src": df.get("access_src", pd.Series("unknown",index=df.index)),
        "score":      df["score"].round(1),
        "rank":       df["rank"],
        "place":      df["place"],
        "land":       df["land"],
        "area_m2":    df["area_m2"].round(0).astype(int),
        # Metres of city-plantable street centreline. Not scored — it answers
        # "can the city act here?", which is a different question from
        # "should it?", and mixing the two would let good access paper over
        # real need.
        "street_m":   df["street_m"].fillna(0).round(0).astype(int),
    })[CONTRACT]

    # Rank exactly the published values/endpoints used by the browser. This
    # avoids dense-rank ties and precision-dependent export/UI disagreement.
    norm = {k: [round(lo, 4), round(hi, 4)] for k, (lo, hi) in bounds.items()}
    published = {k: clip_minmax(out[k], b) for k, b in norm.items()}
    risk = (W["heat"] * published["lst"] + W["green"] * (1-published["green"])
            + W["ac"] * (1-published["ac"]) + W["age65"] * published["pct65"])
    pr = (risk * (C.POP_FLOOR + C.POP_WEIGHT * published["pop"]))[res]
    out.loc[res, "score"] = (100 * minmax(pr)).round(1).values
    out.loc[res, "rank"] = pr.rank(method="first", ascending=False).values

    by_id = {int(r["id"]): r for r in out.to_dict("records")}
    feats = []
    for f in grid["features"]:
        p = by_id.get(f["properties"]["id"])
        if p is None:
            continue
        # NaN is not JSON; holc is legitimately absent outside the 1939 map.
        p = {k: (None if isinstance(v, float) and np.isnan(v) else v)
             for k, v in p.items()}
        feats.append({"type": "Feature", "properties": p,
                      "geometry": {"type": "Polygon",
                                   "coordinates": round_coords(f["geometry"])}})

    # p2/p98 endpoints the front end must normalise against to reproduce this
    # ranking exactly. Keyed by the property each input is read from.
    norm = {k: [round(lo, 4), round(hi, 4)] for k, (lo, hi) in bounds.items()}
    C.OUT_FILE.write_text(json.dumps({"type": "FeatureCollection",
                                      "norm": norm, "metadata": {"schema_version": 3, "acs_year": C.ACS_YEAR,
                                      "lace_year": 2023, "canopy_baseline_min_coverage": 0.99}, "features": feats}))

    log(f"  score: {out.score.min():.1f}–{out.score.max():.1f} "
        f"(median {out.score.median():.1f})")
    log(f"  pop_n: median {n['pop'].median():.3f} — population multiplier spans "
        f"{C.POP_FLOOR:.2f}–{C.POP_FLOOR + C.POP_WEIGHT:.2f}")
    graded = out["holc"].notna().sum()
    log(f"  holc:  {graded}/{len(out)} graded")
    log(f"  wrote {C.OUT_FILE.relative_to(C.ROOT)} "
        f"({len(feats)} hexes, {C.OUT_FILE.stat().st_size/1e6:.1f} MB)")

    log("\n  Top 10 priority hexes")
    top = out.nsmallest(10, "rank")
    for _, r in top.iterrows():
        log(f"    #{int(r['rank']):<3d} {r['score']:5.1f}  {r['name'][:34]:<34s} "
            f"{r['lst']:.1f}C  {r['green']:4.1f}% green  "
            f"{int(r['pop']):6,d} people  {r['access_min']:5.1f} min  "
            f"HOLC {r['holc'] or '-'}")

    # The redlining claim in the demo script is a factual assertion about this
    # dataset. Check it here rather than discovering it is false on stage.
    if graded:
        g = out.dropna(subset=["holc"]).groupby("holc")
        log("\n  HOLC grade vs. today (the Section 10 story beat)")
        for grade, sub in g:
            log(f"    {grade}: {len(sub):4d} hexes  {sub.lst.mean():.1f}C  "
                f"{sub.green.mean():4.1f}% green  {sub.access_min.mean():5.1f} min  "
                f"score {sub.score.mean():.1f}")

    if out["rank"].min() != 1:
        log("  WARNING: no rank-1 hex — ranking is broken", file=sys.stderr)


if __name__ == "__main__":
    main()
