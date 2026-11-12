"""Phase 2g (optional) — tree cover outside the USFS map, from the same aerial imagery.

Why this exists
---------------
The USFS / CAL FIRE 2022 canopy map (02d) stops at the 2020 Census urban-area
line. A growing city has housing past that line: in Bakersfield, 180 ranked
cells of new subdivisions on the edge. 02d fills those from the 2009-2020
canopy-height model, whose imagery can predate the houses themselves, and
which reads lower than the aerial map where both exist.

The USFS map was classified from the 2022 National Agriculture Imagery Program
(NAIP) aerial survey: 60 cm, red / green / blue / near-infrared, public. That
imagery does not stop at the urban-area line. This stage

  1. samples cells the USFS map covers, reads the NAIP pixels under them, and
     trains a per-pixel classifier with the USFS map as the label. Three kinds
     of cell are sampled, because the land past the urban-area line is not
     like the land inside it: "urban" (any fully covered cell, stratified by
     tree cover), "open land" (fully covered cells that ESA WorldCover calls
     mostly cropland, grassland, bare ground, shrub or woodland) and "edge"
     (cells the urban-area line cuts through, using only their assessed part);
  2. scores it on OTHER cells of each kind that it never saw (cell-level tree
     cover against the USFS figure), next to the height model on the same
     cells, and writes all of it to reports/canopy_naip_<slug>.json;
  3. REFUSES to write anything unless, on urban cells AND on open-land cells,
     it beats the height model on mean absolute error, and on urban cells
     matches or beats its rank correlation;
  4. otherwise fills every cell the USFS map does not assess (and partial
     cells below config.CANOPY_MIN_COVERAGE) with the modelled cover of the
     whole cell: canopy_source "naip-model", canopy_year = the imagery year,
     canopy_quality "modelled".

  5. completes the few cells the urban-area line cuts where the homes are on
     the far side of it. A partly assessed cell normally keeps the USFS figure
     for its assessed part, because that part is usually where its homes are
     and the rest is open ground. Where under half of the cell's in-city
     residential building weight lies in the assessed part (config key
     complete_partial_below, default 0.5), the USFS figure describes a sliver
     nobody lives on; there the whole-cell figure is the USFS canopy area plus
     the modelled canopy of the rest: canopy_source "usfs+naip-model",
     canopy_quality "completed", coverage_frac still the USFS share.
     `--complete-partials` runs this step alone on an already filled file.

A cell's cover is the mean predicted probability over its pixels, not a count
of thresholded pixels: averaging probabilities is the unbiased area estimate.

Open land is sampled on purpose. A first version trained on urban cells
alone scored well on urban cells (mean absolute error 1.0 point) and then,
past the line, read irrigated alfalfa and pasture as tree canopy: 65% "tree
cover" on a field of row crops. Aerial photos of the worst cells showed it.
The model is only as good as the ground it has seen, so the fields the USFS
map does cover are in the training set and are tested separately.

What it is not: a second USFS map. It is a model of that map, tested on that
map, and the report says how far off it is. Planting scenarios that need a
measured canopy baseline stay limited to full USFS cells (05).

Gated by CANOPY_NAIP in the city's config.py. Run after 02d and 04 (streets);
re-run after any re-run of 02d, which rewrites the canopy file.

    pip install scikit-learn      # not in requirements.txt, only this stage needs it
    COOLEQUITY_CITY=bakersfield python pipeline/02g_canopy_naip.py [--validate-only]
"""
import glob
import json
import os
import pickle
import sys

import numpy as np

import config as C

# A remote read that never returns would hang a whole run; GDAL waits forever by default.
for _k, _v in (("GDAL_HTTP_TIMEOUT", "45"), ("GDAL_HTTP_CONNECTTIMEOUT", "20"), ("GDAL_HTTP_MAX_RETRY", "3"),
               ("GDAL_HTTP_RETRY_DELAY", "2"), ("GDAL_DISABLE_READDIR_ON_OPEN", "EMPTY_DIR")):
    os.environ.setdefault(_k, _v)

SRC_DIR = C.CACHE / "canopy_src"
REPORT = C.REPORTS / f"canopy_naip_{C.SLUG}.json"
MODEL = C.CACHE / f"canopy_naip_model_{C.SLUG}.pkl"
PARTIAL = C.CACHE / f"canopy_naip_fill_{C.SLUG}.jsonl"   # cells already filled, so a broken run resumes
STAC = "https://planetarycomputer.microsoft.com/api/stac/v1"
PAD = 32                   # pixels read past the cell so the texture windows are full
ROW_HALF_WIDTH_M = 7.0     # as 02c / 02d
SEED = 20221108
FEATURES = ["red", "green", "blue", "nir", "ndvi", "bright", "ndvi_sd3", "nir_sd3",
            "ndvi_sd7", "nir_sd7", "ndvi_m7", "ndvi_m15", "bright_m15", "nir_sd15",
            "ndvi_m31", "ndvi_sd31", "nir_sd31", "ndvi_m61"]
OPEN_LAND = ("cropland", "grassland", "bare ground", "shrubland", "woodland")


def log(msg):
    print(msg, flush=True)


def features(img):
    """(4, h, w) uint8 NAIP -> (h, w, n) float32. Trees differ from lawn mainly in
    texture (rough crowns, self-shadow) and from shrubs in neighbourhood greenness;
    the widest windows (18 m, 37 m) are what tell a crown from the middle of a field."""
    from scipy.ndimage import uniform_filter
    r, g, b, n = (img[i].astype("float32") for i in range(4))
    ndvi = (n - r) / np.maximum(n + r, 1.0)
    bright = (r + g + b) / 3.0

    def sd(a, k):
        m = uniform_filter(a, k, mode="nearest")
        return np.sqrt(np.maximum(uniform_filter(a * a, k, mode="nearest") - m * m, 0.0))

    cols = [r, g, b, n, ndvi, bright, sd(ndvi, 3), sd(n, 3), sd(ndvi, 7), sd(n, 7),
            uniform_filter(ndvi, 7, mode="nearest"), uniform_filter(ndvi, 15, mode="nearest"),
            uniform_filter(bright, 15, mode="nearest"), sd(n, 15),
            uniform_filter(ndvi, 31, mode="nearest"), sd(ndvi, 31), sd(n, 31),
            uniform_filter(ndvi, 61, mode="nearest")]
    return np.stack(cols, axis=-1)


class Imagery:
    """NAIP quarter-quads for the study box, opened lazily and kept open."""

    def __init__(self, year):
        import planetary_computer as pc
        import pystac_client
        from shapely.geometry import box
        cat = pystac_client.Client.open(STAC)
        w, s, e, n = C.BBOX
        items = list(cat.search(collections=["naip"], bbox=(w - .02, s - .02, e + .02, n + .02),
                                datetime=f"{year}-01-01/{year}-12-31").items())
        if not items:
            raise SystemExit(f"02g: no NAIP {year} imagery over {C.CITY}")
        self.items = [(it.id, it.assets["image"].href.split("?")[0], int(it.properties.get("proj:epsg") or str(it.properties["proj:code"]).split(":")[-1]),
                       box(*it.properties["proj:bbox"]), it.datetime.date().isoformat()) for it in items]
        self.dates = sorted({d for *_, d in self.items})
        self.gsd = sorted({float(it.properties.get("gsd", 0)) for it in items})
        self.open = {}
        log(f"  NAIP {year}: {len(items)} quarter-quads, flown {self.dates[0]} to {self.dates[-1]}, {self.gsd} m")

    @staticmethod
    def sign(href):
        import planetary_computer as pc
        return pc.sign(href)

    def clone(self):
        """The same quads with no open rasters, for another thread."""
        other = object.__new__(Imagery)
        other.items, other.dates, other.gsd, other.open = self.items, self.dates, self.gsd, {}
        return other

    def read(self, geom_by_epsg):
        """Pixels under one cell from the first quad that contains it whole.
        Returns (img, transform, crs, cell geometry in that crs) or None."""
        import rasterio
        from rasterio.windows import from_bounds
        for iid, href, epsg, foot, _ in self.items:
            g = geom_by_epsg(epsg)
            if not foot.contains(g.buffer(PAD)):
                continue
            src = self.open.get(iid)
            if src is None:
                src = self.open[iid] = rasterio.open(self.sign(href))
            x0, y0, x1, y1 = g.bounds
            px = abs(src.res[0])
            win = from_bounds(x0 - PAD * px, y0 - PAD * px, x1 + PAD * px, y1 + PAD * px,
                              transform=src.transform).round_offsets().round_lengths()
            for attempt in range(4):
                try:
                    img = src.read(window=win)
                    break
                except Exception:                           # noqa: BLE001 - signed URL / network hiccup
                    if attempt == 3:
                        raise
                    import time
                    time.sleep(3)
                    src = self.open[iid] = rasterio.open(self.sign(href))   # a fresh token: they expire within the hour
            if img.shape[0] < 4:
                continue
            return img[:4], src.window_transform(win), src.crs, g
        return None


_STREETS = {}
_STREETS_LOCK = __import__("threading").Lock()


def cell_arrays(im, geom4326, label_src=None, boundary=None, streets=None):
    """Feature stack, in-cell mask, optional USFS label and street-corridor mask."""
    import geopandas as gpd
    from rasterio.features import rasterize
    cache = {}

    def to(epsg):
        if epsg not in cache:
            cache[epsg] = gpd.GeoSeries([geom4326], crs="EPSG:4326").to_crs(epsg).iloc[0]
        return cache[epsg]

    got = im.read(to)
    if got is None:
        return None
    img, tr, crs, g = got
    shape = img.shape[1:]
    mask = rasterize([(g, 1)], out_shape=shape, transform=tr, fill=0, dtype="uint8").astype(bool)
    out = {"X": features(img), "mask": mask, "px_m2": abs(tr.a * tr.e)}
    if label_src is not None:
        from rasterio.warp import Resampling, reproject
        lab = np.full(shape, 255, dtype="uint8")
        reproject(source=__import__("rasterio").band(label_src, 1), destination=lab, dst_transform=tr,
                  dst_crs=crs, dst_nodata=255, resampling=Resampling.nearest)
        out["label"] = lab
    if streets is not None:
        key = crs.to_string()
        if key not in _STREETS:                 # reproject the street file once per projection, not per cell
            with _STREETS_LOCK:
                if key not in _STREETS:
                    _STREETS[key] = streets.to_crs(crs)
        s = _STREETS[key]
        s = s.iloc[s.sindex.query(g, predicate="intersects")]
        out["row"] = (rasterize([(geom, 1) for geom in s.geometry.buffer(ROW_HALF_WIDTH_M)], out_shape=shape,
                                transform=tr, fill=0, dtype="uint8").astype(bool) & mask) if len(s) else np.zeros(shape, bool)
    return out


def stats(pred, truth):
    from scipy.stats import spearmanr
    pred, truth = np.asarray(pred, float), np.asarray(truth, float)
    return {"n": int(len(pred)), "bias": round(float((pred - truth).mean()), 2),
            "mae": round(float(np.abs(pred - truth).mean()), 2),
            "rmse": round(float(np.sqrt(((pred - truth) ** 2).mean())), 2),
            "pearson": round(float(np.corrcoef(pred, truth)[0, 1]), 3),
            "spearman": round(float(spearmanr(pred, truth)[0]), 3)}


class Workers:
    """Run a per-cell function on several threads. The work is network- and
    numpy-bound; each thread keeps its own open rasters, because a rasterio
    dataset must not be shared between threads."""

    def __init__(self, im, label_path, threads):
        import threading
        self.im, self.label_path, self.threads = im, label_path, threads
        self.local = threading.local()

    def ctx(self):
        import rasterio
        if not hasattr(self.local, "im"):
            self.local.im = self.im.clone()
            self.local.label = rasterio.open(self.label_path)
        return self.local.im, self.local.label

    def map(self, fn, items, what):
        from concurrent.futures import ThreadPoolExecutor
        out = []
        with ThreadPoolExecutor(self.threads) as pool:
            for k, r in enumerate(pool.map(fn, items)):
                out.append(r)
                if k and k % 100 == 0:
                    log(f"    {what}: {k}/{len(items)}")
        return out


def complete_partials(can, cfg, model, W, boundary, streets, year):
    """Step 5 of the module docstring. `can` is the canopy table indexed by h3; returns the h3 completed."""
    import geopandas as gpd
    import pandas as pd
    cut = float(cfg.get("complete_partial_below", 0.5))
    if not C.BUILDINGS_FILE.exists():
        log("  partly assessed cells: no buildings file, so none can be tested for where its homes are")
        return []
    hexes = gpd.read_file(C.GRID_FILE)[["h3", "geometry"]]
    part = hexes[hexes["h3"].isin(can.index[(can["canopy_source"] == "usfs-2022") & (can["canopy_quality"] == "partial")])]
    b = gpd.read_file(C.BUILDINGS_FILE)
    b["wt"] = b["w"] if "w" in b.columns else b["area_m2"]
    if C.BOUNDARY_FILE.exists():            # residents come from in-city buildings only (03)
        b = b[b.within(gpd.read_file(C.BOUNDARY_FILE).to_crs(b.crs).geometry.union_all())]
    hit = gpd.sjoin(b[["wt", "geometry"]], part, how="inner", predicate="within")
    hit["inside"] = hit.geometry.within(boundary)
    tot = hit.groupby("h3")["wt"].sum()
    ins = hit[hit["inside"]].groupby("h3")["wt"].sum().reindex(tot.index).fillna(0.0)
    share = (ins / tot)[tot > 0]
    todo = part[part["h3"].isin(share.index[share < cut])]
    log(f"  partly assessed cells: {len(part)}; {len(share)} hold in-city homes; "
        f"{len(todo)} have under {cut:.0%} of them in the assessed part and are completed")
    if todo.empty:
        return []
    area = todo.to_crs("EPSG:3310").geometry.area
    nf = len(FEATURES)

    def rest(item):
        ix, g4326 = item
        lim, _ = W.ctx()
        g = g4326.difference(boundary)
        a = None if g.is_empty else cell_arrays(lim, g, streets=streets)
        if a is None or not a["mask"].any():
            return ix, None
        X = a["X"].reshape(-1, nf)
        pct = float(model.predict_proba(X[a["mask"].ravel()])[:, 1].mean() * 100)
        row = a.get("row")
        rpx = int(row.sum()) if row is not None else 0
        rpct = float(model.predict_proba(X[row.ravel()])[:, 1].mean() * 100) if rpx else 0.0
        return ix, (pct, rpx * a["px_m2"], rpct)

    done = []
    for ix, got in W.map(rest, list(todo.geometry.items()), "partly assessed cells completed"):
        if got is None:
            continue
        pct, row_tot_m2, rpct = got
        h = todo.at[ix, "h3"]
        r = can.loc[h]
        unassessed = max(0.0, float(area[ix]) - float(r["assessed_m2"]))
        canopy_m2 = float(r["canopy_m2"]) + pct / 100 * unassessed
        # Street corridor: the USFS part as 02d measured it, plus the modelled rest.
        u_unshaded, u_pct = float(r["row_m2"]), float(r["row_canopy_pct"])
        u_tot = u_unshaded / (1 - u_pct / 100) if u_pct < 100 else u_unshaded
        m_unshaded = row_tot_m2 * (1 - rpct / 100)
        tot_row = u_tot + row_tot_m2
        can.loc[h, "canopy_m2"] = round(canopy_m2, 1)
        can.loc[h, "canopy_pct"] = round(canopy_m2 / float(area[ix]) * 100, 3)
        can.loc[h, "row_m2"] = round(u_unshaded + m_unshaded, 0)
        can.loc[h, "row_canopy_pct"] = round((1 - (u_unshaded + m_unshaded) / tot_row) * 100, 3) if tot_row > 0 else 0.0
        can.loc[h, "assessed_m2"] = round(float(area[ix]), 2)        # the whole cell is now described
        can.loc[h, ["canopy_source", "canopy_year", "canopy_quality"]] = ["usfs+naip-model", str(year), "completed"]
        done.append(h)
    return done


def main():
    import geopandas as gpd
    import pandas as pd
    cfg = getattr(C, "CANOPY_NAIP", None)
    if not cfg:
        log(f"Phase 2g — NAIP canopy | {C.CITY}: no CANOPY_NAIP in config.py, nothing to do")
        return
    try:
        from sklearn.ensemble import HistGradientBoostingClassifier
    except ImportError:
        raise SystemExit("02g needs scikit-learn (pip install scikit-learn)")
    year = int(cfg["year"])
    log(f"Phase 2g — tree cover from NAIP {year}, trained on the USFS {year} map | {C.CITY}")
    tifs = sorted(glob.glob(str(SRC_DIR / "**" / "*_canopy2022.tif"), recursive=True))
    shps = sorted(glob.glob(str(SRC_DIR / "**" / "*.shp"), recursive=True))
    if len(tifs) != 1 or len(shps) != 1:
        raise SystemExit(f"02g expects exactly one USFS raster and boundary in {SRC_DIR}, found {len(tifs)} and {len(shps)}")
    can = pd.read_csv(C.CANOPY_CSV)
    if "--complete-partials" in sys.argv:
        # Step 5 alone, on a file 02g has already filled, with the model that filled it.
        if not (MODEL.exists() and REPORT.exists() and json.loads(REPORT.read_text()).get("filled_cells")):
            raise SystemExit("02g --complete-partials needs the saved model and a report of a completed fill")
        with open(MODEL, "rb") as fh:
            model = pickle.load(fh)["model"]
        boundary = gpd.read_file(shps[0]).to_crs("EPSG:4326").geometry.union_all()
        streets = gpd.read_file(C.STREETS_FILE) if C.STREETS_FILE.exists() else None
        W = Workers(Imagery(year), tifs[0], int(cfg.get("threads", 6)))
        can = can.set_index("h3")
        for col in ("canopy_source", "canopy_year", "canopy_quality"):
            can[col] = can[col].astype(object)
        done = complete_partials(can, cfg, model, W, boundary, streets, year)
        can.reset_index().to_csv(C.CANOPY_CSV, index=False)
        report = json.loads(REPORT.read_text())
        report["completed_partials"] = int((can["canopy_source"] == "usfs+naip-model").sum())
        report["complete_partial_below"] = float(cfg.get("complete_partial_below", 0.5))
        REPORT.write_text(json.dumps(report, indent=1) + "\n")
        log(f"  completed {len(done)} partly assessed cells; wrote {C.CANOPY_CSV.relative_to(C.ROOT)}")
        return
    if can["canopy_source"].isin(["naip-model", "usfs+naip-model"]).any():
        raise SystemExit("02g: the canopy file already holds modelled cells; re-run 02d first")
    hexes = gpd.read_file(C.GRID_FILE)[["h3", "geometry"]].merge(can, on="h3")
    if C.WORLDCOVER_CSV.exists():
        hexes = hexes.merge(pd.read_csv(C.WORLDCOVER_CSV)[["h3", "land"]], on="h3", how="left")
    else:
        hexes["land"] = ""
    boundary = gpd.read_file(shps[0]).to_crs("EPSG:4326").geometry.union_all()
    streets = gpd.read_file(C.STREETS_FILE) if C.STREETS_FILE.exists() else None
    rng = np.random.default_rng(SEED)

    # ---------------------------------------------------------------- the three samples
    usfs = hexes["canopy_source"] == "usfs-2022"
    full = hexes[usfs & (hexes["coverage_frac"] >= 0.999)]
    dec = pd.qcut(full["canopy_pct"].rank(method="first"), 10, labels=False)
    n_tr, n_te = int(cfg.get("train_cells", 300)), int(cfg.get("test_cells", 300))
    pick = np.concatenate([rng.permutation(full.index[dec == d])[: (n_tr + n_te) // 10] for d in range(10)])
    pick = rng.permutation(pick)
    groups = {"urban": (list(pick[:n_tr]), list(pick[n_tr:n_tr + n_te]))}
    rest = full.drop(index=pick)
    op = list(rng.permutation(rest.index[rest["land"].isin(OPEN_LAND)]))
    groups["open_land"] = (op[: len(op) // 2], op[len(op) // 2:])
    edge = hexes[usfs & hexes["coverage_frac"].between(0.25, 0.99)]
    ed = list(rng.permutation(edge.index))
    groups["edge"] = (ed[: len(ed) // 2], ed[len(ed) // 2:])
    for name, (tr_ix, te_ix) in groups.items():
        log(f"  {name}: {len(tr_ix)} cells to train, {len(te_ix)} held out to test")
    if len(groups["open_land"][1]) < 30:
        raise SystemExit("02g: fewer than 30 open-land cells to test on; the model cannot be checked past the urban edge")
    # An edge cell is used only where the USFS map assessed it.
    geom = {ix: (hexes.geometry[ix].intersection(boundary) if name == "edge" else hexes.geometry[ix])
            for name, (a, b) in groups.items() for ix in a + b}
    kind = {ix: name for name, (a, b) in groups.items() for ix in a + b}

    im = Imagery(year)
    W = Workers(im, tifs[0], int(cfg.get("threads", 6)))
    nf = len(FEATURES)

    def train_pixels(ix):
        lim, lab_src = W.ctx()
        a = cell_arrays(lim, geom[ix], label_src=lab_src)
        if a is None:
            return None
        # The USFS raster stores canopy as 1 and everything else as nodata, so
        # inside assessed ground "not 1" IS the no-canopy class.
        idx = np.flatnonzero(a["mask"])
        r = np.random.default_rng(SEED + int(ix))
        idx = r.choice(idx, min(per_cell[kind[ix]], len(idx)), replace=False)
        return a["X"].reshape(-1, nf)[idx], (a["label"].ravel()[idx] == 1).astype("uint8")

    per_cell = {"urban": int(cfg.get("pixels_per_cell", 3000)), "open_land": 6000, "edge": 6000}
    train_all = [ix for a, _ in groups.values() for ix in a]
    if "--reuse-model" in sys.argv and MODEL.exists():
        # Same seed, same cells: only for re-running the fill after a validation run.
        with open(MODEL, "rb") as fh:
            saved = pickle.load(fh)
        if saved.get("features") != FEATURES or saved.get("train_cells") != len(train_all):
            raise SystemExit("02g: the saved model was trained with other features or cells; run without --reuse-model")
        model, n_px = saved["model"], saved["n"]
        log(f"  reusing the model trained on {n_px:,} pixels ({MODEL.name})")
    else:
        got = [g for g in W.map(train_pixels, train_all, "training cells read") if g is not None]
        X, y = np.concatenate([g[0] for g in got]), np.concatenate([g[1] for g in got])
        n_px = len(X)
        log(f"  training on {n_px:,} pixels from {len(got)} cells, {y.mean()*100:.1f}% canopy")
        model = HistGradientBoostingClassifier(max_iter=400, learning_rate=0.1, max_leaf_nodes=63,
                                               l2_regularization=1.0, random_state=SEED).fit(X, y)
        MODEL.parent.mkdir(exist_ok=True)
        with open(MODEL, "wb") as fh:
            pickle.dump({"model": model, "n": n_px, "features": FEATURES, "train_cells": len(train_all)}, fh)
        del X, y, got

    def proba(a, which="mask"):
        m = a[which]
        if not m.any():
            return float("nan"), 0
        p = model.predict_proba(a["X"].reshape(-1, nf)[m.ravel()])[:, 1]
        return float(p.mean() * 100), int(m.sum())

    # ---------------------------------------------------------------- held-out scores
    prior = None
    if "--reuse-model" in sys.argv and REPORT.exists():
        prior = json.loads(REPORT.read_text())
        if prior.get("train_pixels") != n_px or prior.get("features") != FEATURES:
            prior = None
    if prior is not None:
        report = prior
        report.pop("filled_cells", None)
        report.pop("cells_no_single_quad", None)
        log("  held-out scores from the saved validation of this model (not re-computed)")
    else:
        def score(ix):
            lim, lab_src = W.ctx()
            a = cell_arrays(lim, geom[ix], label_src=lab_src)
            if a is None:
                return None
            m = a["mask"]
            p = model.predict_proba(a["X"].reshape(-1, nf)[m.ravel()])[:, 1]
            lab = a["label"][m] == 1
            return ix, p.mean() * 100, lab.mean() * 100, ((p >= 0.5) == lab).mean()

        chm_path = C.CANOPY_CSV.with_name(C.CANOPY_CSV.stem + "_chm.csv")
        chm = pd.read_csv(chm_path).set_index("h3")["canopy_pct"] if chm_path.exists() else None
        report = {"city": C.CITY, "imagery": f"NAIP {year}", "flown": im.dates,
                  "label": "USFS / CAL FIRE 2022 urban tree canopy", "features": FEATURES,
                  "train_cells": {k: len(a) for k, (a, _) in groups.items()}, "train_pixels": int(n_px), "held_out": {}}
        ok = True
        for name, (tr_ix, te_ix) in groups.items():
            res = [r for r in W.map(score, te_ix, f"held-out {name} cells scored") if r is not None]
            used = [r[0] for r in res]
            pred, truth = np.array([r[1] for r in res]), np.array([r[2] for r in res])
            # The label as this stage reads it must be the figure 02d wrote for the
            # same cell; if not, the two stages disagree about the map.
            drift = float(np.abs(truth - hexes.loc[used, "canopy_pct"].to_numpy()).max())
            if drift > 0.5:
                raise SystemExit(f"02g: USFS cover re-read here differs from 02d's by up to {drift:.2f} points ({name}); refusing")
            g = {"naip_model": {**stats(pred, truth), "pixel_accuracy": round(float(np.mean([r[3] for r in res])), 4),
                                "label_vs_02d_max_abs_diff": round(drift, 3)}}
            line = f"    {name:<9} NAIP model bias {g['naip_model']['bias']:+.2f} MAE {g['naip_model']['mae']:.2f} rank r {g['naip_model']['spearman']:.3f}"
            # The height model describes whole cells, so it is compared only where
            # the USFS figure does too (not on edge cells' assessed parts).
            if chm is not None and name != "edge":
                h = chm.reindex(hexes.loc[used, "h3"]).to_numpy()
                have = ~np.isnan(h)
                g["height_model"] = stats(h[have], truth[have])
                th = chm.reindex(hexes.loc[tr_ix, "h3"]).to_numpy()
                tu = hexes.loc[tr_ix, "canopy_pct"].to_numpy()
                keep = ~np.isnan(th)
                slope, icpt = np.polyfit(th[keep], tu[keep], 1)
                g["height_model_rescaled"] = {**stats(icpt + slope * h[have], truth[have]),
                                              "intercept": round(float(icpt), 2), "slope": round(float(slope), 3)}
                best = min(g["height_model"]["mae"], g["height_model_rescaled"]["mae"])
                ok &= g["naip_model"]["mae"] < best
                if name == "urban":
                    ok &= g["naip_model"]["spearman"] >= max(g["height_model"]["spearman"], g["height_model_rescaled"]["spearman"]) - 0.005
                    ok &= g["naip_model"]["mae"] <= float(cfg.get("max_mae", 2.0))
                line += (f" | height model MAE {g['height_model']['mae']:.2f} (rescaled {g['height_model_rescaled']['mae']:.2f}) "
                         f"rank r {g['height_model']['spearman']:.3f}")
            ok &= abs(g["naip_model"]["bias"]) <= 1.0
            report["held_out"][name] = g
            log(line)
        report["accepted"] = bool(ok)
    C.REPORTS.mkdir(exist_ok=True)
    if not report["accepted"] or "--validate-only" in sys.argv:
        REPORT.write_text(json.dumps(report, indent=1) + "\n")
        log("  NOT writing modelled cells: " + ("--validate-only" if report["accepted"] else
            "the model does not beat the height model on held-out cells, or is biased by more than a point"))
        return

    # ---------------------------------------------------------------- fill
    thin = (hexes["canopy_quality"] == "partial") & (hexes["coverage_frac"].fillna(0) < C.CANOPY_MIN_COVERAGE)
    target = hexes[(hexes["canopy_source"] != "usfs-2022") | thin]
    log(f"  filling {len(target)} cells the USFS map does not assess ({int(thin.sum())} of them thin partials)")
    area = hexes.to_crs("EPSG:3310").geometry.area

    import threading
    lock = threading.Lock()
    stamp = f"{n_px}:{len(FEATURES)}"
    have = {}
    if PARTIAL.exists():
        for line in PARTIAL.read_text().splitlines():
            r = json.loads(line)
            if r["model"] == stamp:
                have[r["h3"]] = r["v"]
        if have:
            log(f"  resuming: {len(have)} cells already filled by this model in an earlier run")
        else:
            PARTIAL.unlink()

    def fill(item):
        ix, g4326 = item
        h = hexes.loc[ix, "h3"]
        if h in have:
            return ix, have[h]
        lim, _ = W.ctx()
        a = cell_arrays(lim, g4326, streets=streets)
        if a is None:
            return ix, None
        pct, _n = proba(a)
        rpct, rpx = proba(a, "row") if "row" in a else (float("nan"), 0)
        v = (pct, None if np.isnan(rpct) else rpct, rpx, a["px_m2"])
        with lock, open(PARTIAL, "a") as fh:
            fh.write(json.dumps({"h3": h, "model": stamp, "v": v}) + "\n")
        return ix, v

    results = W.map(fill, list(target.geometry.items()), "cells filled")
    can = can.set_index("h3")
    for col in ("canopy_source", "canopy_year", "canopy_quality"):
        can[col] = can[col].astype(object)
    done = missed = 0
    for ix, got in results:
        if got is None:
            missed += 1
            continue
        pct, rpct, rpx, px_m2 = got
        rpct = float("nan") if rpct is None else rpct
        h = hexes.loc[ix, "h3"]
        can.loc[h, "canopy_pct"] = round(pct, 3)
        can.loc[h, "canopy_m2"] = round(pct / 100 * area[ix], 1)
        can.loc[h, "row_canopy_pct"] = 0.0 if not rpx else round(rpct, 3)
        can.loc[h, "row_m2"] = 0.0 if not rpx else round(rpx * px_m2 * (1 - rpct / 100), 0)
        can.loc[h, "assessed_m2"] = round(float(area[ix]), 2)
        can.loc[h, "coverage_frac"] = 1.0
        can.loc[h, ["canopy_source", "canopy_year", "canopy_quality"]] = ["naip-model", str(year), "modelled"]
        done += 1
    completed = complete_partials(can, cfg, model, W, boundary, streets, year)
    report["completed_partials"] = len(completed)
    report["complete_partial_below"] = float(cfg.get("complete_partial_below", 0.5))
    can.reset_index().to_csv(C.CANOPY_CSV, index=False)
    PARTIAL.unlink(missing_ok=True)
    report["filled_cells"] = done
    report["cells_no_single_quad"] = missed
    REPORT.write_text(json.dumps(report, indent=1) + "\n")
    log(f"  filled {done} cells ({missed} not inside any single quarter-quad, left as they were)")
    log(f"  wrote {C.CANOPY_CSV.relative_to(C.ROOT)} and {REPORT.relative_to(C.ROOT)}")

    from sources import record
    u, o = report["held_out"]["urban"]["naip_model"], report["held_out"]["open_land"]["naip_model"]
    record("02g_canopy_naip", f"NAIP {year} aerial imagery (tree-cover model outside the USFS map)",
           "https://planetarycomputer.microsoft.com/dataset/naip", count=done,
           publisher="USDA Farm Service Agency, via Microsoft Planetary Computer",
           note=(f"Flown {im.dates[0]} to {im.dates[-1]}. Per-pixel model trained on the USFS map; on held-out cells against "
                 f"the USFS figure: urban cells (n={u['n']}) bias {u['bias']:+.2f} points, mean absolute error {u['mae']:.2f}, "
                 f"rank correlation {u['spearman']:.3f}; open-land cells (n={o['n']}) bias {o['bias']:+.2f}, mean absolute "
                 f"error {o['mae']:.2f}. Count is cells filled."))


if __name__ == "__main__":
    main()
