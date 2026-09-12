> Carried over from the `contra-costa` branch of [advikar/coolequity](https://github.com/advikar/coolequity/tree/contra-costa) on September 12, 2026. File paths in it refer to that branch (e.g. `data/` is now `cities/contracosta/data/`, `app/guide.html` is now `cities/contracosta/guide.html`).

# Contra Costa County build — findings

## September 7 rebuild status

ACS 2024 and occupied-housing LACE corrections are implemented. The current build contains
2,697 ranked residential cells and source-specific canopy coverage. Prior income/canopy
headlines below remain historical: the mixed-source and median-income methodology has not
been revalidated. Use `reports/rebuild_summary.json` for current rebuild diagnostics.


> **September 7, 2026 source audit: historical results pending revalidation.**
> The existing county `green` field includes 430 residential NDVI-fallback cells. The canopy
> comparisons below were not all computed from canopy alone. Do not quote them as verified
> pure-canopy findings until the mosaic/source audit and recomputation are complete.
> The new app labels the source and has retired the old landing headline.
> See `PRODUCT_READINESS.md` and the latest section of `DATA_QUALITY.md`.


**Status: shipped as a CANOPY EQUITY map.** Heat is measured and viewable but carries zero
weight, for the reasons in §2. The scored model is missing canopy (55%), no A/C access (25%)
and age 65+ (20%), scaled by population.

Built 28 Aug 2026 from the same pipeline as San Ramon: H3 res 8, 2,695 populated hexes,
1,161,570 residents reconciling to the ACS county total of 1,161,458 (**0.01%**).

---

## 1. The equity gradient is real — this is what San Ramon could not show

> **Canopy is now the USFS/CAL FIRE 2022 aerial product (0.6 m NAIP), not the Meta/WRI
> height model.** Every figure below was recomputed on it. The gradient held and sharpened.

| Income quartile | Median income | Mean canopy | Population |
|---|---|---|---|
| Poorest 25% | $96,967 | **11.3%** | 465,010 |
| 2nd | $129,864 | 15.1% | 270,415 |
| 3rd | $164,629 | 24.3% | 198,864 |
| Richest 25% | $236,357 | **31.6%** | 208,480 |

- `corr(income, canopy) = **+0.419**` county-wide. San Ramon's was −0.037.
- Poorest vs richest quartile: a **20.3-point canopy gap, t = −21.0** (mean canopy); the
  poorest quarter of *residents* live under 12.9% canopy against the richest quarter's 27.0%.
- **23 of the 25 top-priority hexes fall in the poorest income quartile** (verified against
  the built geojson — it is no longer "all 25"). Top-25 median income $87,319 against a county
  median of ~$158,000.
- Top of the list is Richmond (Triangle Court, Easter Hill Village, Atchison Village) and
  Concord's Monument corridor — which is where anyone who knows the county would look.

**Caveat, and it is a real one:** detrending for a quadratic spatial surface drops
`corr(income, canopy)` from +0.419 to **+0.124**. A substantial part of the raw gap is
*where* rich and poor areas sit — the wooded Lamorinda hills versus the Richmond shoreline —
rather than differential investment in comparable terrain. **Quote +0.42 with the detrended
+0.12 beside it**, or the first hydrologist in the room will do it for you.

## 2. The heat finding does not reproduce, and that breaks the score

San Ramon: `corr(LST, canopy) = −0.604` (USFS aerial). Contra Costa: **−0.181** county-wide.
Either way, far weaker than a real shade signal and swinging sign by sub-region.

It is not hiding in a sub-region. Tested every way (the breakdown below predates the canopy
swap — Meta/WRI CHM — but the county-level conclusion is unchanged under USFS aerial):

| Area | n | LST~canopy | detrended |
|---|---|---|---|
| Whole county | 2,689 | −0.120 | −0.149 |
| West of −121.90 (urban core) | 1,448 | −0.018 | −0.200 |
| Richmond / El Cerrito only | 1,019 | **+0.043** | −0.130 |
| Central (Concord / Walnut Creek) | 723 | −0.084 | −0.326 |
| East (Antioch / Brentwood / Delta) | 518 | −0.090 | **+0.221** |

By longitude band it swings from **+0.381 to −0.092**. There is no consistent shade effect
at this scale.

**Why, most likely.** The county spans a marine-to-inland climate gradient — mean LST is
36.8 °C in the west and 43.1 °C in the east, and **38.8% of all LST variance is explained by
longitude and latitude alone**. Richmond is cool *and* bare; Brentwood is hot *and* irrigated
farmland. Absolute surface temperature across this county is mostly a map of distance from
the Bay. Resolution may contribute too — res 8 hexes (0.77 km²) mix houses, streets, parks and
parking — but LA managed −0.61 at res 8, so climate heterogeneity is the better explanation.

**Why this is not a footnote:** `WEIGHTS["heat"] = 0.35`. The single heaviest input in the
score is the one whose relationship to everything else has collapsed. Min-max normalising LST
across the whole county also means Richmond's 41 °C and Antioch's 52 °C are ranked on one
scale, as if a Richmond resident experiences 41 °C the way an Antioch resident experiences 41 °C.
They do not.

## 3. Dasymetric population placement was refused, automatically

The San Ramon method — placing residents by OSM building floor area — **must not be used
here**, and `03_census.py` now detects that itself rather than relying on someone noticing:

```
mask check: 139,121 mapped buildings vs 426,585 ACS housing units = 0.33 coverage
!! DASYMETRIC REFUSED: coverage 0.33 < 0.50 — the mask is a sample, not a census
!! falling back to AREA weighting
```

The completeness problem is bad; the bias is worse. OSM coverage by income quartile runs
**0.07 / 0.07 / 0.08 / 0.33** — volunteers have mapped the richest quartile **4.7× better**
than the poorest. Since population multiplies the priority score, weighting by that mask would
have moved residents out of poor neighbourhoods and demoted them. An equity tool that
under-ranks poverty because Blackhawk is better mapped than North Richmond is worse than no
tool. The guard and its thresholds are in `config.DASY_MIN_COVERAGE` /
`DASY_MAX_INCOME_BIAS`. **Do not raise them to force dasymetric back on — fix the mask.**

## 4. A bug this build found in the shared pipeline

`02_satellite.py` sorted candidate scenes by cloud cover globally and kept the best
`MAX_SCENES = 30`. For a single-tile city that is fine. Across a county spanning several
Sentinel-2 MGRS tiles it took nearly all 30 from the clearest tile, and **NDVI came back 37%
valid with 1,723 of 2,859 hexes empty**. Fixed by budgeting scenes per tile: now 101 scenes
across 4 tiles, **100% valid**. This bug was invisible at city scale and would have silently
corrupted any large-area build.

## 5. What was done

**Option 1 was taken: reframed as a canopy-equity map, heat weighted zero.** Heat keeps its
layer, legend and per-hex numbers — all measured — and the "Heat first" preset shows what it
says on its own, which is mostly a map of distance from the Bay. The scored model is now
missing canopy (55%) / no A/C access (25%) / age 65+ (20%), scaled by population.

The resulting top ten is Richmond's Atchison Village, Nystrom Village, Easter Hill Village,
Triangle Court and Barrett Terrace, plus Concord's Monument corridor — 4% to 7% canopy
against a county median of 14.9%.

**On the apparent contradiction** between weighting heat zero and still predicting cooling in
the ROI panel: these are different claims, and the app now says so. Planting shade on a block
cools that block — a measured local effect, and what the WRI coefficient describes. Comparing
absolute temperature between blocks 60 km apart mostly measures distance from the Bay. Adding
trees still cools; ranking Richmond against Antioch by raw thermal reading does not work.

**A/C is scored here (25%), and it is now MEASURED, not modelled from income** — the US Census
Bureau's LACE tract estimates (2023), for 95% of hexes. **This resolves the circularity trap
the earlier build carried:** when A/C was an income transform, the priority score was
mechanically tied to income and could not be used to argue that priority "tracks income."
It no longer is. That said, every equity figure in this document is still computed on **raw
canopy with no score involved**, which is the cleanest way to make the point, and the
**Canopy only** preset lets anyone reproduce it with A/C removed entirely — the Richmond
blocks stay at the top.

### Headline numbers, for copy

| | |
|---|---|
| Populated hexes | 2,695 at H3 res 8 (~0.77 km²) |
| Residents | 1,161,570 (ACS county total 1,161,458 — **0.01%**) |
| Canopy | median **14.9%**, range 0.0–96.0% (USFS 2022 aerial) |
| Under 15% canopy | 1,352 hexes, **577,342 residents (50% of the county)** |
| Top 25 | mean canopy **6.6%**, 90,977 residents, 284.6 km of street frontage |
| To bring top 25 to the county median | **39,566 trees**, ~$19.8M at $500/tree |
| Public right-of-way capacity there | 56,920 trees — 2 of the 25 blocks still fall short |

## 6. What to do next

Three honest options, in the order I would try them:

1. **Reframe as a canopy-equity map and drop or heavily downweight heat.** The defensible
   claim here is "the poorest quarter of this county has half the tree cover of the richest",
   which needs no thermal data at all. This is a one-line weights change plus copy.
2. **Re-scope to one climate zone.** Not simply "the west" — that did not work either. It
   would mean a genuine climate-zone segmentation, and normalising heat *within* zone.
3. **Keep the county as a scale demonstration only** and lead publicly with San Ramon, where
   the mechanism holds.

**Still worth doing:** a genuine climate-zone segmentation would let heat back into the score
honestly, by normalising it within zone rather than across the whole county. That is the
principled version of what weighting it zero does bluntly.
