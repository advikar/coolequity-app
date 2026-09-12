# A first-pass canopy assessment for CAP Measure CS-1b

**Where San Ramon's tree canopy is thinnest, block by block — and what closing the gap
would cost**

Prepared by *[your name]*, an independent student project · Data current as of August 2026
Method, source code and every figure below: `github.com/advikar/coolequity` (`san-ramon` branch)
Interactive map: `advikar.github.io/coolequity/sanramon/app/`

> This is an outside analysis offered for cross-checking. It is not a City product and has
> not been reviewed by the City. Where it is uncertain, it says so.

---

## Why this is addressed to you

San Ramon's **Draft Climate Action Plan (April 10, 2025), Measure CS-1**, commits the City to
work this analysis was independently built to do:

- **CS-1b** — *"Conduct a Tree Canopy assessment … including **identifying areas with below
  average canopy coverage**"*, and set *"a goal of having **no significant difference in canopy
  coverage between census blocks** in the community."*
- **CS-1c** — *"prioritize tree implementation in **areas with populations most at risk to
  extreme heat impacts** (e.g., older adults …)."*
- **CS-1d** — a Tree Trust for *"selected communities with below average tree canopy coverage"*,
  plus USDA / California ReLeaf / Urban and Community Forestry grant applications.
- **CS-1e** — *"an **interactive map** showing the results of the tree canopy assessment along
  with areas identified for new tree canopy."*

**This document is a free first pass at CS-1b and CS-1c, with a working interactive map.** It is
not a substitute for the professional assessment the CAP calls for — it uses a satellite
vegetation proxy, not a tree inventory. It is offered as something to scope that assessment
against, to cross-check a consultant's results, or to attach to a grant application as evidence
that the need is quantified. Every figure is reproducible from public data and open source code.

---

## The finding

**Across San Ramon's 419 populated blocks, summer surface temperature tracks vegetation
cover almost one-for-one — `r = −0.80` — and the 25 blocks with the thinnest cover average
14.5% vegetation against a city median of 20.9%. Those 25 blocks hold 10,113 residents.**

The gap is closable with street trees alone. Those blocks contain **32.1 km of residential
street frontage**; bringing them to the citywide median needs about **4,484 trees**, and the
public right-of-way could hold roughly **6,406** at 10 m spacing on both sides — so **in
aggregate the gap closes without private land.**

Block by block it is less tidy: **9 of the 25 need more trees than their own frontage holds**,
The Preserve and Carmelita S worst among them at roughly 190–210 trees short each. Those blocks
need either planting on adjacent public land or an agreement with the property owner. The other
16 fit entirely in the right-of-way.

At a nominal $500 per planted tree including three years of establishment care, that is about
**$2.24 million** spread over whatever period the City chooses — a capital line item, not a
bond measure.

### The ten thinnest blocks

| # | Area | Surface temp | Vegetation | Residents | 65+ | Street frontage |
|---|---|---|---|---|---|---|
| 1 | Valencia S | 46.9 °C | 12.9% | 925 | 8.6% | 1,279 m |
| 2 | Mosaic Park | 46.8 °C | 15.5% | 887 | 8.0% | 1,447 m |
| 3 | Amador Lakes N | 47.7 °C | 15.7% | 210 | **47.6%** | 1,301 m |
| 4 | Carmelita S | **51.1 °C** | 9.8% | 178 | 10.6% | 493 m |
| 5 | The Preserve | 49.2 °C | **6.0%** | 153 | 18.7% | 1,109 m |
| 6 | Serena & Cordova | 48.6 °C | 6.5% | 261 | 11.8% | 1,280 m |
| 7 | Fairway Village SE | 47.2 °C | 15.6% | 480 | 18.5% | 1,121 m |
| 8 | Carmelita | 49.3 °C | 9.5% | 265 | 10.4% | 1,365 m |
| 9 | The Preserve NE | 47.3 °C | 10.0% | 430 | 8.1% | 1,241 m |
| 10 | Capella ⚠ | 49.3 °C | 11.0% | 263 | 9.7% | 559 m |

⚠ **Capella is flagged, not asserted.** It runs 3.8 °C hotter than its neighbouring blocks —
above the 95th percentile of local anomalies citywide — and carries 6.0 residents per mapped
building against a city median of 3.7. That combination is consistent with either a genuine
hot spot or a mapping error. **It should be checked on the ground before it is acted on.**
Centre point: 37.78122, −121.92628.

## What this is *not*

**There is no income gradient in San Ramon's heat exposure, and this analysis does not claim
one.** Correlation between block median household income and priority score is **−0.02**.
Mean vegetation cover by income quartile is 21.5 / 22.6 / 21.7 / 20.4% — flat, with the
wealthiest quartile marginally the least shaded. The lowest-income quartile of this city has
a median household income of $163,938.

Two other explanations were tested and rejected: housing type (`r = +0.08` against
multi-family floor area, measured from 26,346 building footprints) and housing age
(`r = +0.02` against ACS median year built). What remains is geographic — 8 of the 10 blocks
above sit east of Dougherty Road, where mean vegetation is 19.8% against 22.6% west of it
(t = −4.8) — but a 2.8-point difference is a tilt, not a divide.

## Sources

| Input | Source | Vintage |
|---|---|---|
| Surface temperature | USGS/NASA **Landsat 8/9** thermal (ST_B10), 9 scenes | summers 2022–2024 |
| Vegetation cover | ESA **Sentinel-2** NDVI, 11 scenes, 20% cloud filter | summers 2022–2024 |
| Population, age, income | **US Census ACS** 2023 5-year, block groups | 2019–2023 |
| Buildings, streets, cooling sites | **OpenStreetMap** via Overpass | retrieved Aug 2026 |

Population is placed within block groups by residential floor area (dasymetric), not by area.
The city total reconciles to **85,569 against the ACS place total of 85,734 — 0.19%**.

## Three limitations, stated plainly

1. **"Vegetation cover" is not "tree canopy."** It is an NDVI proxy at 10 m, and NDVI cannot
   distinguish a mature tree from irrigated lawn. In a summer-dry climate this matters: a
   block could read green because it is watered, not because it is shaded. Removing all
   *mapped* parks, turf and woodland changes the heat–vegetation correlation by 0.001
   (−0.800 → −0.799), but only ~6% of the city is mapped that way and most greenness here is
   private yard. **This is the single weakest link in the analysis.** Ground-truthing against
   a real canopy layer would settle it.
2. **Air conditioning is excluded from the score.** The underlying model estimates A/C access
   from income percentile. San Ramon's block-group medians run $100,906–$250,001 — uniformly
   high — so that transform would have invented a 35–95% spread across a city where it does
   not exist. The input is built and viewable but weighted zero. Every scored input is
   measured.
3. **Resolution and thermal sampling.** Blocks are ~0.11 km²; ACS block groups are about nine
   times larger, so **age and income vary smoothly between neighbouring blocks** and should
   not be read at single-block precision. Surface temperature is a median of 9 Landsat scenes
   across three summers, not a continuous record. And surface temperature is not air
   temperature and not indoor temperature — with near-universal A/C here, it is a measure of
   outdoor thermal environment, not of health risk.

**No San Ramon-specific heat health data was found.** California publishes heat-illness
emergency department rates at **county** level (Tracking California); ZIP-level records exist
within HCAI but require a Limited Data Request. County figures are not presented here because
they are not San Ramon figures.

## One ask

**Cross-reference these 25 blocks against whatever street tree records the City already holds.**

If those records show these streets are already planted, then the satellite proxy is measuring
irrigation rather than canopy, this analysis is wrong, and CS-1b's assessment should be scoped
knowing that NDVI alone will not answer it. That is worth finding out cheaply.

If they show these streets are *not* planted, then CS-1b has a ranked, costed starting list —
25 blocks, 10,113 residents, 4,484 trees, 32 km of City right-of-way — and CS-1d has a
quantified need to put in a grant application.

Either outcome is useful to you. No software to adopt, no procurement, no commitment: one
cross-check against data the City already owns.

**Also worth knowing before you act on it:** one block in the top ten (Capella) is flagged above
as possibly a data artifact, and should be looked at before it appears on any list.
