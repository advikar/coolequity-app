# Surface cooling model decision

September 7, 2026. No surface-change formula has been added to the public calculator.

The current small degree output represents illustrative **air cooling averaged over the
analysis area**, conditional on added canopy. It is not shaded-pavement temperature, thermal
comfort or a measured impact. Trees may yield stronger cooling at shaded surfaces, but the
magnitudes have different spatial and temporal meanings.

Schwaab et al. (2021) compare tree-covered and other surfaces in 293 European cities and
report strong regional variation. That is useful evidence of surface-cooling mechanisms;
it is not a per-tree coefficient transferable to a Contra Costa hex.
https://pmc.ncbi.nlm.nih.gov/articles/PMC8611034/

A credible next model would define its output first: daytime, cell-average satellite LST
change under a specified planting scenario and weather regime. Candidate implementation:
fit LST = f(canopy, impervious cover, low vegetation, elevation, distance to water, local
background climate, acquisition/weather conditions), then evaluate the same covariates with
a feasible canopy intervention and corresponding land-cover changes. The difference is a
conditional modeled association until an intervention design supports causal interpretation.

Required before public forecast use:

1. Matched canopy/LST vintages, assessed-area masks and thermal-resolution support. Do not
   mix unassessed ground or height-map/NDVI fallback values into an aerial calibration.
2. Local matched-area comparisons and spatial holdout testing; compare against a simple
   climate-only baseline. Random cell splits would leak spatial context into validation.
3. Sensitivity to irrigation, species, crown size, built form and climate; prediction intervals
   supported by the model, rather than an invented “low/high” range.
4. A before/after or other defensible intervention check; a spatial correlation alone is not
   evidence that planting that many trees causes the displayed cooling.
5. UI separates cell-average surface cooling, neighborhood air cooling and pedestrian shade.
   Do not substitute a surface temperature reduction for an equivalent felt-temperature or
   health benefit. A pedestrian-comfort model needs radiation, wind, humidity and geometry.

The current 2,859-cell CSV is useful for exploratory diagnostics, but its mixed canopy sources
and cell-aggregate thermal data do not establish a calibrated causal response. A universal
surface multiplier would create false confidence. For now the UI explains shade/surface
benefits qualitatively and keeps the evidence-backed air illustration secondary.
