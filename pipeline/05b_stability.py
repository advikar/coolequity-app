"""Phase 5b — rank stability under plausible input and weight variation.

The ranking in <slug>.geojson is a single point estimate. This step re-draws
the inputs that carry published uncertainty and records, per ranked cell, the
range of ranks it takes across those draws. It adds three properties to each
residential feature of the city's GeoJSON (nothing else in the file changes):

    rank_lo         5th-percentile rank across draws (a better rank than usual)
    rank_hi         95th-percentile rank across draws (a worse rank than usual)
    rank_top_share  share of draws in which the cell lands in the top tier
                    (the best 10% of ranked cells)

What is varied, per draw
  * Population and residents 65+ per block group: normal draws inside the ACS
    90% margin of error (sigma = MOE / 1.645), floored at zero. A cell inherits
    the draw of the block groups it overlaps, weighted by overlap area, so
    neighbouring cells cut from the same block group move together, as the
    audit asked (sampling error is correlated across cells, not independent).
  * A/C prevalence per tract: same treatment with the LACE 2023 margin (AC_PM).
  * Weights: each non-zero recommended weight gets uniform noise of ±0.10 and
    the set is renormalised; a weight the city set to zero stays zero, because
    that is a decision, not an uncertainty. The population multiplier's slope
    moves ±0.10 around the shipped value.
What is not varied
  * Surface temperature and tree cover. Their error is measurement error with
    no published per-cell margin, and it is described by source and coverage in
    the cell's properties instead. Walking time carries no weight.
  * The allocation of residents within a block group (area or building
    weighting). That is a modelling choice, not a sampled quantity; the guide's
    Population topic states which one the build uses.

Scoring per draw repeats 05_score.py exactly (shrunk age share, p2/p98 clips
recomputed on the drawn residential cells, population multiplier), imported
from that module so the two cannot drift apart.

    COOLEQUITY_CITY=westcc python pipeline/05b_stability.py [--draws 300]

Reads:  data/<slug>.geojson, data/grid_<slug>.geojson, data/census_<slug>.csv (raw pct65),
        data/acs_<slug>.csv, _cache/bg_<year>_06.zip, _cache/ac_src/LACE_23_Tract.csv
Writes: data/<slug>.geojson (in place, three properties added, metadata.stability)
        reports/stability_<slug>.json
"""
import importlib.util
import json
import sys
import time

import numpy as np
import pandas as pd

import config as C

_spec = importlib.util.spec_from_file_location("score05", C.ROOT / "pipeline" / "05_score.py")
S = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(S)

DRAWS = int(sys.argv[sys.argv.index("--draws") + 1]) if "--draws" in sys.argv else 300
SEED = 20260913
WEIGHT_JITTER = 0.10      # uniform, absolute, per non-zero weight
POP_SLOPE_JITTER = 0.10   # uniform, absolute, on POP_WEIGHT
TOP_TIER = 0.10           # best 10% of ranked cells
Z90 = 1.645               # ACS and LACE publish 90% margins

BG_ZIP = C.CACHE / f"bg_{C.ACS_YEAR}_{C.STATE_FIPS}.zip"
LACE = C.CACHE / "ac_src" / "LACE_23_Tract.csv"
REPORT = C.CITY_DIR / "reports" / f"stability_{C.SLUG}.json"


def log(m):
    print(m, flush=True)


def overlap_shares():
    """hex -> [(GEOID, share)] by overlap area, from the grid and the BG shapes."""
    import geopandas as gpd
    from shapely.geometry import shape
    grid = json.loads(C.GRID_FILE.read_text())
    hexes = gpd.GeoDataFrame(
        {"id": [f["properties"]["id"] for f in grid["features"]]},
        geometry=[shape(f["geometry"]) for f in grid["features"]], crs="EPSG:4326").to_crs(C.RASTER_CRS)
    bgs = gpd.read_file(f"zip://{BG_ZIP}")
    bgs = bgs[bgs["COUNTYFP"] == C.COUNTY_FIPS][["GEOID", "geometry"]].to_crs(C.RASTER_CRS)
    inter = gpd.overlay(hexes, bgs, how="intersection", keep_geom_type=True)
    inter["a"] = inter.geometry.area
    tot = inter.groupby("id")["a"].transform("sum")
    inter["share"] = inter["a"] / tot
    return inter[["id", "GEOID", "share"]]


def main():
    log(f"Phase 5b — rank stability | {C.CITY} | {DRAWS} draws")
    doc = json.loads(C.OUT_FILE.read_text())
    props = pd.DataFrame([f["properties"] for f in doc["features"]])
    res = props["place"].eq("res").values
    nres = int(res.sum())
    top_n = max(1, int(np.ceil(TOP_TIER * nres)))
    log(f"  {nres} ranked cells; top tier = best {top_n}")

    # --- block-group and tract uncertainty, mapped onto cells by overlap share
    acs = pd.read_csv(C.ACS_FILE, dtype={"GEOID": str}).set_index("GEOID")
    lace = pd.read_csv(LACE, dtype={"STATE": str, "COUNTY": str, "TRACT": str})
    lace["tract"] = lace["STATE"] + lace["COUNTY"] + lace["TRACT"]
    lace = lace.set_index("tract")
    for col in ("AC_PE", "AC_PM"):
        lace[col] = pd.to_numeric(lace[col], errors="coerce")
    sh = overlap_shares()
    sh = sh[sh["GEOID"].isin(acs.index)]
    sh["tract"] = sh["GEOID"].str[:11]
    bg_ids = sorted(sh["GEOID"].unique())
    tr_ids = sorted(sh["tract"].unique())
    bg_pos = {g: i for i, g in enumerate(bg_ids)}
    tr_pos = {t: i for i, t in enumerate(tr_ids)}
    id_pos = {int(i): k for k, i in enumerate(props["id"])}
    # Sparse share matrices: cells x block groups, cells x tracts.
    Mbg = np.zeros((len(props), len(bg_ids)))
    Mtr = np.zeros((len(props), len(tr_ids)))
    for r in sh.itertuples(index=False):
        k = id_pos.get(int(r.id))
        if k is None:
            continue
        Mbg[k, bg_pos[r.GEOID]] += r.share
        Mtr[k, tr_pos[r.tract]] += r.share
    rows = Mbg.sum(axis=1, keepdims=True)
    Mbg = np.divide(Mbg, rows, out=np.zeros_like(Mbg), where=rows > 0)
    rows = Mtr.sum(axis=1, keepdims=True)
    Mtr = np.divide(Mtr, rows, out=np.zeros_like(Mtr), where=rows > 0)
    covered = (Mbg.sum(axis=1) > 0)
    log(f"  overlap: {len(bg_ids)} block groups, {len(tr_ids)} tracts; "
        f"{int((res & ~covered).sum())} ranked cells without an overlap (kept at their point estimate)")

    pop_e = acs.loc[bg_ids, "pop"].to_numpy(float)
    pop_m = acs.loc[bg_ids, "pop_moe"].to_numpy(float)
    p65_e = acs.loc[bg_ids, "pop65"].to_numpy(float)
    p65_m = acs.loc[bg_ids, "pop65_moe"].to_numpy(float)
    ac_e = lace.reindex(tr_ids)["AC_PE"].to_numpy(float)
    ac_m = lace.reindex(tr_ids)["AC_PM"].to_numpy(float)
    pop_m = np.nan_to_num(pop_m, nan=0.0); p65_m = np.nan_to_num(p65_m, nan=0.0)
    ac_ok = np.isfinite(ac_e) & np.isfinite(ac_m) & (ac_e > 0)
    log(f"  median relative MOE: population {np.nanmedian(pop_m/np.where(pop_e>0,pop_e,np.nan))*100:.0f}%, "
        f"residents 65+ {np.nanmedian(p65_m/np.where(p65_e>0,p65_e,np.nan))*100:.0f}%, "
        f"A/C {np.nanmedian(ac_m[ac_ok]/ac_e[ac_ok])*100:.0f}% of the estimate")

    base_pop = props["pop"].to_numpy(float)
    # The published pct65 is already smoothed by 05 (shrink_age65). Start each
    # draw from the RAW census share so the draw is smoothed exactly once, as
    # the point model is; smoothing the smoothed value again pulled small-
    # population cells further toward the citywide rate than 05 ever does.
    grid_props = pd.DataFrame([f["properties"] for f in json.loads(C.GRID_FILE.read_text())["features"]])[["id", "h3"]]
    raw = grid_props.merge(pd.read_csv(C.CENSUS_CSV)[["h3", "pct65"]], on="h3", how="left").set_index("id")["pct65"]
    base_p65 = raw.reindex(props["id"].astype(int)).fillna(0.0).to_numpy(float)   # raw share, %
    chk = S.shrink_age65(pd.Series(base_pop), pd.Series(base_p65)).round(1).to_numpy()
    pub = props["pct65"].to_numpy(float)
    bad = np.abs(chk - pub) > 0.15
    if bad.any():
        raise SystemExit(f"raw pct65 smoothed once does not reproduce the published share for {int(bad.sum())} cells "
                         f"(max gap {np.nanmax(np.abs(chk - pub)):.2f}); rebuild 05 first")
    log(f"  age share: raw census share smoothed once reproduces the published pct65 (max gap {np.nanmax(np.abs(chk-pub)):.2f})")
    base_ac = props["ac"].to_numpy(float)
    lst = props["lst"].to_numpy(float)
    green = props["green"].to_numpy(float)
    W0 = dict(C.WEIGHTS)
    wsum = sum(W0.values())
    rng = np.random.default_rng(SEED)
    ranks = np.full((DRAWS, len(props)), np.nan)

    for d in range(DRAWS):
        # block-group / tract ratio draws, folded onto cells by overlap share
        fpop = np.where(pop_e > 0, np.maximum(0.0, rng.normal(pop_e, pop_m / Z90)) / np.where(pop_e > 0, pop_e, 1), 1.0)
        f65 = np.where(p65_e > 0, np.maximum(0.0, rng.normal(p65_e, p65_m / Z90)) / np.where(p65_e > 0, p65_e, 1), 1.0)
        fac = np.where(ac_ok, np.clip(rng.normal(np.where(ac_ok, ac_e, 50), np.where(ac_ok, ac_m, 0) / Z90), 0, 100) / np.where(ac_ok, ac_e, 1), 1.0)
        cpop = Mbg @ fpop; c65 = Mbg @ f65; cac = Mtr @ fac
        cpop = np.where(covered, cpop, 1.0); c65 = np.where(covered, c65, 1.0); cac = np.where(covered, cac, 1.0)
        pop = base_pop * cpop
        # residents 65+ scale with their own draw; the share is that over the population draw
        pct65 = np.where(pop > 0, base_p65 * c65 / np.where(cpop > 0, cpop, 1), 0.0)
        ac = np.clip(base_ac * cac, 0, 100)
        # weights: jitter the non-zero ones, renormalise to the shipped total
        W = {k: (max(0.0, v + rng.uniform(-WEIGHT_JITTER, WEIGHT_JITTER)) if v > 0 else 0.0) for k, v in W0.items()}
        s = sum(W.values()); W = {k: v * wsum / s for k, v in W.items()}
        slope = float(np.clip(C.POP_WEIGHT + rng.uniform(-POP_SLOPE_JITTER, POP_SLOPE_JITTER), 0.05, 0.95))
        floor = 1.0 - slope
        # score exactly as 05 does, on the drawn residential cells
        pct65_s = S.shrink_age65(pd.Series(pop), pd.Series(pct65)).to_numpy()
        R = pd.DataFrame({"lst": lst, "green": green, "ac": ac, "p65": pct65_s, "pop": pop})[res]
        b = {"lst": S.clip_bounds(R["lst"], False), "green": S.clip_bounds(R["green"], True),
             "ac": S.clip_bounds(R["ac"], True), "p65": S.clip_bounds(R["p65"], False), "pop": S.clip_bounds(R["pop"], True)}
        n = {k: S.clip_minmax(R[k], b[k]).to_numpy() for k in b}
        risk = W["heat"] * n["lst"] + W["green"] * (1 - n["green"]) + W["ac"] * (1 - n["ac"]) + W["age65"] * n["p65"]
        pr = risk * (floor + slope * n["pop"])
        ranks[d, res] = pd.Series(pr).rank(method="first", ascending=False).to_numpy()

    lo = np.nanpercentile(ranks, 5, axis=0)
    hi = np.nanpercentile(ranks, 95, axis=0)
    top = np.nanmean(ranks <= top_n, axis=0)
    point = props["rank"].to_numpy(float)
    width = hi - lo
    # write back
    by_id = {}
    for k, pid in enumerate(props["id"]):
        if res[k]:
            by_id[int(pid)] = (int(round(lo[k])), int(round(hi[k])), round(float(top[k]), 3))
    for f in doc["features"]:
        p = f["properties"]
        v = by_id.get(int(p["id"]))
        p["rank_lo"], p["rank_hi"], p["rank_top_share"] = v if v else (None, None, None)
    doc.setdefault("metadata", {})["stability"] = {
        "draws": DRAWS, "seed": SEED, "top_tier_n": top_n, "rank_percentiles": [5, 95],
        "varied": "ACS block-group population and residents 65+ within 90% MOE (overlap-weighted, correlated across cells); "
                  "LACE tract A/C within 90% MOE; non-zero weights ±0.10 renormalised; population slope ±0.10",
        "held_fixed": "surface temperature, tree cover, walking time, within-block-group allocation",
        "age_share": "raw census share re-drawn, then shrink_age65 once (as 05)",
        "computed": time.strftime("%Y-%m-%d"),
    }
    C.OUT_FILE.write_text(json.dumps(doc))
    rw = width[res]
    summary = {
        "city": C.CITY, "draws": DRAWS, "ranked": nres, "top_tier_n": top_n,
        "median_band_width": float(np.median(rw)), "p90_band_width": float(np.percentile(rw, 90)),
        "share_band_within_10pct_of_list": float(np.mean(rw <= 0.10 * nres)),
        "point_top_tier_always_top_tier": float(np.mean(top[res & (point <= top_n)] >= 0.95)),
        "point_top_tier_usually_top_tier": float(np.mean(top[res & (point <= top_n)] >= 0.80)),
        "top25_point": [{"id": int(props["id"][k]), "name": props["name"][k], "rank": int(point[k]),
                         "rank_lo": int(round(lo[k])), "rank_hi": int(round(hi[k])), "top_share": round(float(top[k]), 3)}
                        for k in np.argsort(np.where(res, point, np.inf))[:25]],
    }
    REPORT.parent.mkdir(exist_ok=True)
    REPORT.write_text(json.dumps(summary, indent=1))
    log(f"  band width (p95 - p5): median {summary['median_band_width']:.0f} ranks, p90 {summary['p90_band_width']:.0f}; "
        f"{summary['share_band_within_10pct_of_list']*100:.0f}% of cells within 10% of the list")
    log(f"  of the {top_n} point-estimate top-tier cells, {summary['point_top_tier_always_top_tier']*100:.0f}% stay top-tier in >=95% of draws, "
        f"{summary['point_top_tier_usually_top_tier']*100:.0f}% in >=80%")
    for t in summary["top25_point"][:10]:
        log(f"    #{t['rank']:<3d} {t['name'][:34]:<34s} band {t['rank_lo']}–{t['rank_hi']}  top-tier {t['top_share']*100:.0f}%")
    log(f"  wrote {C.OUT_FILE.relative_to(C.ROOT)} (+rank_lo, rank_hi, rank_top_share) and {REPORT.relative_to(C.ROOT)}")


if __name__ == "__main__":
    main()
