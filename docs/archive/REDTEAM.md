# Red team: how a skeptical San Ramon planner takes this apart

Written against my own analysis, strongest objection first. Each one is scored on whether it
is **fatal** (the finding does not survive), **wounding** (the finding survives but the ask
must change), or **survivable** (answerable with what is already measured).

The honest summary: **objection 1 is the one that could sink this, and I could not fully
rule it out.** Everything below it I can answer.

---

## 1. "Your NDVI is measuring irrigation, not trees." — **WOUNDING, possibly fatal**

**The objection.** San Ramon has a Mediterranean climate: bone-dry from June to October
except where something is watered. A summer NDVI composite therefore separates *irrigated*
from *unirrigated* far more sharply than it separates *shaded* from *unshaded*. A block of
lawn with no trees reads green. A block with mature oaks over dry ground reads brown. If
that's what's happening, the ranking is a map of sprinkler coverage, the heat correlation is
the well-known evaporative-cooling effect of wet grass, and "plant 4,484 trees" is the wrong
prescription — you'd get more cooling per dollar from turf, which is the opposite of what
the state's water policy wants.

**What I can say back.** Removing every mapped park, sports pitch, golf course, cemetery and
woodland changes the heat–vegetation correlation from −0.800 to −0.799. So the relationship
is not being carried by the obvious irrigated public land.

**Why that isn't good enough.** Those mapped features are only about 6% of the city's area.
The greenness that matters here is in private front and back yards, which OpenStreetMap does
not map, so my test could not touch it. I have ruled out the public irrigated land and left
the private irrigated land untested.

**What would settle it.** The City's street tree inventory, or any LiDAR/aerial canopy layer
for Contra Costa County. If the thin blocks turn out to be well-planted streets with dry
yards, the analysis is measuring the wrong thing and needs to be rebuilt on a real canopy
raster. **This is why the ask in the brief is a cross-check and not an adoption.**

## 2. "Dense housing has less landscaping by design. You've rediscovered zoning." — **SURVIVABLE, but concede the framing**

**The objection.** The top blocks are the densest in the city (Valencia S is 8,419 people/km²
against a 1,629 median). Small lots mean less planting area. That is a design decision made
at entitlement, not an injustice and not news.

**Answer.** Largely true, and the brief does not call it an injustice — it explicitly reports
no income gradient. But "explained by density" is not "not worth fixing": the people in those
blocks experience the heat regardless of why the lots are small, and 10,113 of them live in
the top 25. The actionable part is precisely that density limits *private* planting area,
which is what makes the 32 km of *public* frontage the relevant lever. The objection actually
strengthens the recommendation.

## 3. "Surface temperature isn't what hurts anyone." — **SURVIVABLE, and already conceded**

**The objection.** Landsat measures skin temperature of the ground. People are harmed by air
temperature, and mostly by *indoor* air temperature. In a city with near-universal central
air, outdoor surface temperature is close to irrelevant to health outcomes.

**Answer.** Correct, and the brief says so in limitation 3. This is not a health-risk model
and it is not presented as one — that is exactly why A/C access was dropped rather than
modelled, and why no mortality or morbidity claim appears anywhere. The claim is narrower:
outdoor thermal environment varies by 12 °C across the city, tracks vegetation, and canopy is
a lever the City controls. Comfort, walkability, and pavement and irrigation costs are real
municipal interests without invoking heat deaths.

## 4. "Population is a multiplier, so this is a density map with extra steps." — **SURVIVABLE**

**The objection.** `corr(priority, population density) = +0.49`. Multiplying by population is
a choice that guarantees dense blocks win.

**Answer.** It is a choice and it is disclosed — the multiplier spans 0.55–1.00 and can be
set to zero in the interface, which re-ranks live. Its purpose is that a cooling dollar
reaches more people in a dense block, which is a defensible thing for a city to want. But the
canopy finding does not depend on it: `corr(LST, vegetation) = −0.80` is computed on the raw
inputs with no weighting or population term anywhere in it.

## 5. "Your blocks are a ninth the size of a census block group." — **SURVIVABLE, one part already fixed**

**The objection.** Age and income are interpolated downward. Reporting them per 0.11 km²
block implies precision that does not exist.

**Answer.** True for age and income, and the brief says not to read those at single-block
precision. Population specifically is no longer interpolated by area — it is placed by
residential floor area from 25,434 building footprints, and reconciles to the ACS place total
within 0.19%. Before that fix, 57 blocks held phantom residents on open space and one ranked
#10. The heat and vegetation inputs are measured per block at 30 m and 10 m and are not
interpolated at all.

**Robustness.** Rebuilt at H3 res 8 (0.82 km², roughly one block group), `corr(LST,
vegetation)` is **−0.837** — slightly stronger than at res 9. The aggregate finding is not a
resolution artifact. Individual block rankings *are* resolution-sensitive: of the 17 res-8
cells containing the res-9 top 25, 11 fall in the res-8 top quartile. **Trust the list as a
screening tool, not as a ranking to three significant figures.**

## 6. "Nine Landsat scenes over three summers is a thin sample." — **SURVIVABLE**

**Answer.** It is thin, and it is why the composite is a median across 2022–2024 rather than
a single date. A per-block anomaly check found no block ranking high on the strength of one
hot pixel: within the top 12, standard deviation of surface temperature is 0.6–1.4 °C across
120–125 pixels each, and the 90th-percentile-minus-median spread is under 2.8 °C. The one
exception is **Capella**, 3.8 °C above its neighbours, which is flagged in the brief as needing
ground-truth rather than presented as a finding.

## 7. "Who are you, and why should we spend staff time?" — **the real one**

No answer from the data, but the framing does most of the work: San Ramon's own Draft Climate
Action Plan (April 10, 2025) **Measure CS-1b** already commits the City to "identifying areas
with below average canopy coverage" and to "no significant difference in canopy coverage
between census blocks", and **CS-1e** to publishing an interactive map of exactly that. This is
not an unsolicited pitch; it is a free first pass at work the City has already said it will do.

The remaining mitigations: the ask costs one cross-check against data the City already owns,
the method and code are public and inspectable, and the brief leads with a **null result** — no
income gradient — which is not what someone selling something would lead with.

**Do not overclaim on this.** CS-1b asks for a canopy assessment *and a tree inventory*. This
delivers neither: it is a satellite vegetation proxy, and objection 1 is precisely the reason it
cannot substitute for the real thing. Say "first pass, to scope or cross-check yours", never
"this satisfies CS-1b".

---

## What I would need to make this bulletproof

1. **A real canopy layer** (City inventory or county LiDAR) to retire objection 1.
2. **Ground-truth on Capella**, and ideally a spot check of five of the top 25.
3. **Air temperature** from any local sensor network, to connect surface temperature to
   something people feel.
4. **The City's planting cost per tree**, replacing the $500 planning assumption.
