# Evidence note: planting cost bands and canopy-source validation

Written September 13, 2026 for the two audit items that were still open after the tenth pass:
"locally justified low/base/high planting costs" and "separating canopy sources instead of
pooling them". Both were marked as needing outside input. This note records what public sources
say, what the app now does with it, and what still needs a city or a dataset.

## 1. Cost per planted tree

No Contra Costa or Kern city publishes a per-tree contract price online that could be fetched
on September 13, 2026 (Pittsburg's urban-forest page and RFP block automated access; Antioch,
Richmond, El Cerrito and Concord agendas do not itemise trees). What is public:

| Figure | What it covers | Source | Year |
|---|---|---|---|
| **$500 per tree** | Bakersfield's own estimate, cited by the Sierra Club and the city's Tree Advisory Group debate; the council's $500,000 funds "roughly 1,000 trees" | [South Kern Sol op-ed, July 16 2026](https://southkernsol.org/2026/07/16/op-ed-bakersfield-still-needs-more-trees/); [KGET, March 2026](https://www.kget.com/news/local-news/80-of-tree-planting-in-bakersfield-to-be-in-underserved-areas-report/) | 2026 |
| **≈$2,000 per tree** | Concord's USDA Forest Service grant: $1 million for 500 trees, including a management plan, school micro-forests and intern workforce | [City of Concord](https://www.cityofconcord.org/1289/USDA-Forest-Service-Grant); [Pioneer](https://pioneerpublishers.com/city-of-concord-granted-1-million-to-cultivate-urban-forest/) | 2024–26 |
| **≈$3,400 per tree** | San Francisco 3500 Trees: $12 million for 3,500 street trees including three years of establishment watering and a workforce program | [SF Public Works](https://sfpublicworks.org/3500treesproject) | 2025–29 |
| **$4,351 per tree** | Los Angeles Board of Public Works, Oct 14 2022: tree $290, labor $1,371, equipment $190, five years of watering $2,500 | [CityWatch LA](https://www.citywatchla.com/neighborhood-politics/26031-it-costs-4-351-12-to-plant-one-tree-in-la) | 2022 |
| ≈$1,150 planting, ≈$2,000–2,800 establishment | San Francisco Urban Forest Plan financing study: planting $3.3–3.4M and establishment $5.6–8M per year for 2,900 trees per year | [SF Planning, exec. summary](https://default.sfplanning.org/plans-and-programs/planning-for-the-city/urban-forest-plan/UFP_Financing_Study_Exec_Sum_131216.pdf) | 2013 |
| 15-gallon stock is the default | CAL FIRE's IRA urban forestry guidelines fund trees "of a stock size other than 15-gallon" only with prior approval; young-tree establishment labor is an eligible cost | [CAL FIRE guidelines, 2024](https://www.fire.ca.gov/what-we-do/grants/urban-and-community-forestry-grants) | 2024 |

Reading: **$500 is a planting-only, city-crew figure** (Bakersfield's own). A program that buys
the tree, plants it and waters it for three years costs **$2,000–4,400** in California cities
that publish it. The gap is establishment watering, which is most of the cost and most of the
survival.

### What the app now does

The planting scenario's cost field has three one-click presets beside it, with the sources on
hover and in every guide's "Trees, maturity & cost" topic:

| Preset | $ per tree | Meaning |
|---|---|---|
| Low | 500 | Planting only, city crews, no establishment budget (Bakersfield's estimate) |
| Base | 2,000 | Planting plus about one year of establishment care, or a grant program's all-in average (Concord) |
| High | 3,500 | Planting plus three years of watering and program overhead (San Francisco 3500 Trees; Los Angeles is higher) |

The default stays at $500 and is labelled as the low band so existing briefings, scenario files
and share links reproduce. Changing the default to the base band is a one-line change
(`DEFAULT_COST_TREE` in `app/index.html`) and the owner's call.

### Still needed from a city

A local unit price. The right ask, in each first email: "what did your last planting contract
cost per tree, and did it include watering?" Pittsburg's grant program and Concord's will have a
number by the end of 2026. Until then the band, not the point, is the honest output.

## 2. Canopy sources: what is pooled and what the literature says about each

The app scores tree cover from one column (`green`) filled from, in order: USFS/EarthDefine 2022
aerial canopy (0.6 m, census urban areas), the Meta/WRI canopy height model where the aerial
product has no coverage, and a satellite greenness stand-in where neither covers at least 10% of
the cell. Cells are labelled by source; they are still ranked on one normalised scale.

| Source | Published accuracy | Known bias | Reference |
|---|---|---|---|
| USFS / EarthDefine California urban canopy, NAIP 2018 and 2022, 0.6 m, deep CNN | No published accuracy figures on the Forest Service page (checked Sept 13, 2026). Comparable NAIP deep-learning canopy work reports Dice 0.82, precision 0.79, recall 0.86 | Crowns under about 1.5 m are frequently missed; shadows and dense structure reduce accuracy | [USFS R5 data page](https://www.fs.usda.gov/r05/state-private-tribal/california-urban-canopy-data); [Remote Sensing 2026 (PMC)](https://pmc.ncbi.nlm.nih.gov/articles/PMC13521618/) |
| Meta / WRI canopy height model, 1 m (the app's "trees · model" cells) | 86.2% overall accuracy, 79.7% balanced accuracy at 7,500 points in 15 cities; per-city canopy share within 3.0 percentage points of reference on average | Underestimates height of tall street trees; trained on a limited geographic range | [Urban Forestry & Urban Greening, May 2026](https://www.sciencedirect.com/science/article/abs/pii/S1618866726002438); [WRI dataset page](https://datasets.wri.org/datasets/meta-tree-canopy-height) |
| ESA WorldCover 10 m (used only to find water and wetland, not to score) | About 75–77% overall accuracy; tree crowns omitted mainly in dense built-up areas with small isolated trees | Omits small urban trees | [ESA validation report](https://worldcover2020.esa.int/data/docs/WorldCover_PVR_V1.1.pdf) |
| NLCD / USFS Tree Canopy Cover 30 m (not used) | Underestimates urban canopy by about 10 points; 14 points in dense urban areas | Systematic low bias | [Scientific Data 2025](https://www.nature.com/articles/s41597-025-04816-0) |

The pipeline's own check (`pipeline/02c_canopy.py`) found the height model 38% low against
Fresno's professional aerial assessment and rank-correlated +0.84 with NLCD. The Meta/WRI urban
validation above says the model's canopy *share* per city is within 3 points on average, so the
Fresno gap is likely the app's 2 m height threshold and crown-edge omission rather than the
model itself. That is testable, not something to assume.

### An independent reference exists for every Contra Costa build

The California Department of Fish and Wildlife published a fine-scale vegetation map of Alameda
and Contra Costa counties in May 2025 (dataset ds3206, 987,000 acres, 140,442 polygons) with
**lidar-derived canopy cover and stand height for every polygon**, based on summer 2020 NAIP and
2023 lidar, licensed CC-BY, overall lifeform accuracy 97%.
[CNRA open data](https://data.cnra.ca.gov/dataset/vegetation-alameda-and-contra-costa-county-ds3206);
download `https://filelib.wildlife.ca.gov/Public/BDB/GIS/BIOS/Public_Datasets/3200_3299/ds3206.zip`
(160 MB, dated August 6, 2025).

That covers Contra Costa County, West Contra Costa, Pittsburg & Bay Point and San Ramon, i.e.
every cell of every source type in four of the five builds. It does not cover Bakersfield; the
USGS 3DEP lidar the audit mentions is the equivalent there.

### Proposed validation step (not run; needs the 160 MB download)

`pipeline/02f_canopy_validate.py`, per Contra Costa build:

1. Intersect ds3206 polygons with the H3 grid; area-weight lidar canopy cover to a per-cell
   `canopy_lidar_pct`.
2. For each source class (aerial full, aerial partial, height model, greenness stand-in),
   report bias, RMSE and Spearman rank correlation against the lidar figure, separately for
   urban, fringe and orchard cells as the audit asks.
3. Either calibrate the height-model cells onto the aerial scale by the fitted bias, or replace
   `green` with the lidar figure where it exists and keep the aerial product for 2022 currency.
4. Re-score, and report top-25 overlap before and after in `reports/canopy_validation_<slug>.json`.

That closes the "pooling" item with data rather than field visits for four builds. Field
checks remain the only validation for Bakersfield until a lidar-based reference is added.

## 3. Survival, for the 70% default

- Berkeley and Oakland street-tree cohorts: 34% dead or removed after two years, 19% annual
  mortality ([Arboriculture & Urban Forestry 16(5)](https://auf.isa-arbor.com/content/16/5/124)).
- Literature median annual mortality for young trees 6.6–7% in the first five years; losing a
  quarter of a cohort in five years is common ([USFS review](https://research.fs.usda.gov/treesearch/58772)).
- Sacramento Shade: 42.4% alive after 22 years (already cited in the guides).

The 70% default sits inside that range for a five-year horizon with some establishment care. A
program with no watering budget should test 50–60%.
