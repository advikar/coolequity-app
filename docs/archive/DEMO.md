# CoolEquity — San Ramon demo script (60–90s)

**Every number here is read off `data/sanramon.geojson` and was checked in the
running app, not off a spec.** This is the `san-ramon` branch; the Los Angeles
script is on `master` and its numbers do not transfer.

## Before you start

```bash
cd coolequity
python3 -m http.server 8000       # then open http://localhost:8000/app/
```

- Window at ~1440×860 or full screen. Below ~700px the 366px panel eats the map.
- You land on the **intro screen**; the map is already booted behind it, so the
  button is a fade, not a load. `?go=1` skips it.
- Priority layer, all four cooling-site categories on, weights at **Pipeline
  default**, detail panel closed. That is a fresh load — just reload rather than
  clicking back. The **home button** beside the wordmark returns you here.
- **No Wi-Fi?** Nothing to do. MapLibre and both typefaces are vendored and all
  data is local; you lose only the CARTO basemap. Rehearse with `?flat=1`.
- **There is no redlining layer and the panel says why.** Do not go looking for
  it — see beat 3.

---

## The script

**1 · Hook (10s)** — intro screen.

> "Heat is the deadliest weather hazard on Earth, and it lands hardest on the
> least-shaded blocks. Cities have cooling budgets. What they don't have is a
> precise way to aim them."

Then click **Explore San Ramon**.

**2 · Map (15s)**

> "This is all of San Ramon — every block inside the city limits, 419 populated hexes,
> 85,569 residents, about a tenth of a square kilometre each. Every one scored
> on real satellite heat, real tree canopy, population and age. Nothing here is
> drawn by hand. The darker it is, the more help it needs."

**3 · The suburb result (25s)** — this is the beat that makes San Ramon
interesting rather than a smaller Los Angeles. It is also the beat that got
rewritten after the data contradicted the first version; see "What we checked
and had to drop" below.

> "San Ramon is wealthy and leafy — 21% canopy over the typical resident, median
> household income over $220,000. You'd expect this map to be flat. It isn't.
> Canopy runs from **5% to 41%** of the ground and surface temperature from
> **39 to 51 °C** across four miles, and the two move together almost
> one-for-one: **r = −0.80**, and −0.81 after removing any spatial trend. Shade
> is doing the work.
>
> The thing we expected to find, and didn't, is a **who**. Priority does not
> track income — **r = −0.02**. It doesn't track housing type, and it doesn't
> track how old the housing is. The poorest quarter of this city has a median
> income of $164,000 and *slightly more* canopy than the richest quarter. So
> there is no heat-equity story here, and we're not going to invent one. What
> there is, is a **canopy gap**: the top 25 blocks average 14.5% canopy against
> a city median of 21%."

Where the gap actually is, if asked: **8 of the top 10 hexes are east of
Dougherty Road**, in Dougherty Valley — which holds 37% of the city's populated
hexes. East vs west is 19.8% vs 22.6% canopy (t = −4.8) and +0.9 °C (t = +5.4).
Real and statistically clear, but a 2.8-point canopy difference, so describe it
as a tilt, not a divide.

If asked about redlining: **San Ramon has no HOLC map, and the app says so
rather than showing an empty layer.** HOLC surveyed built-up cities in 1935–40;
San Ramon was farmland and didn't incorporate until 1983.

**4 · The model is not a black box (20s)** — click **Protect seniors**, then
**Pipeline default**.

> "The weights aren't buried in a config file. Ask a different question and the
> whole model recomputes across all 419 populated hexes, live. Ask 'who is most
> likely to *die* of this?' and the top spot moves from Valencia to **Amador
> Lakes North**, where **48% of residents are over 65** — the highest in the
> city."

Verified preset → #1 hex, re-checked against the rebuilt data:

| Preset | #1 |
|---|---|
| Pipeline default | Valencia S |
| Heat first | Valencia S |
| Shade gap | Valencia S |
| Protect seniors | Amador Lakes Apartments N (47.6% aged 65+) |
| No relief nearby | Chantera E |
| Most people | Valencia S |

Then click any hex:

> "And for any block, here's the arithmetic — what we measured, where it sits on
> the city's scale, times the weight, equals points."

**5 · Decision (25s)** — click the **#1 hex** (Valencia S), drag the canopy
slider to **25%**.

> "Number one: Valencia South. 46.9 °C surface temperature, **12.9% canopy**,
> **925 residents** — the densest block in the city at about 8,400 people per
> square kilometre. Raise canopy here to 25%, roughly the city median, and that
> is **333 trees**, an estimated **0.36 °C** cooler afternoon for all 925 of
> them, at about **$167,000** — **$180 a resident**. That's a line item, not a
> bond measure."

**6 · Close (10s)**

> "Every input here is global — Landsat, Sentinel-2, OpenStreetMap, a census.
> This started as Los Angeles, three thousand hexes and six and a half million
> people. Re-pointing it at a town of eighty-five thousand was a config change.
> Point it at Lagos or Delhi tomorrow and it answers the same question: where
> does the first tree go?"

---

## What we checked and had to drop

Both of these were in an earlier version of this script. Both were wrong, and
both were caught by testing them rather than by thinking harder about them. They
are written down so nobody says them from memory.

**"Heat inequity here looks like housing type — apartment complexes."** False.
Measured against OSM building footprints (26,346 of them, effectively complete
coverage for a city of ~30k housing units), the correlation between a hex's
priority score and its share of multi-family floor area is **+0.08**. The median
top-10 hex has **0%** multi-family floor area. The claim came from hex *names* —
"Fairway Village Apartments SE" is named after the nearest landmark and contains
4% apartment floor area. The name was doing the arguing.

**"Newer subdivisions have less canopy."** Also false, and tested because it was
the obvious next hypothesis. Median year built by block group (ACS B25035)
against priority: **r = +0.02**. Mean canopy by construction era is 22.7%
(pre-1980), 22.6% (1980–94), 20.2% (1995–2004), 20.9% (2005+). Flat.

What survived: the canopy–heat coupling (**r = −0.80**, −0.81 detrended) and the
absence of an income gradient (**r = −0.02**). Those are the two things to say.

## Questions you should expect

**"Is this real data?"** Yes, all of it, and the honest caveats are labelled in
the UI. Landsat 8/9 thermal and Sentinel-2 NDVI composited over the summers of
2022–2024 from Microsoft's Planetary Computer. ACS 2023 five-year for Contra
Costa County. City limits from Census TIGERweb. Cooling sites and neighbourhood
names from OpenStreetMap. Nothing is synthetic and nothing is copied from the LA
build.

**"Why three summers, when the LA build used one?"** Because San Ramon is small.
Summer 2023 alone yields **one** Landsat scene under the 20% cloud filter, and
one scene is an afternoon, not a median. Three summers gives 9 Landsat and 11
Sentinel-2 scenes at the *same* strict cloud threshold — more data, not looser
data. The alternative was raising the cloud limit, which buys quantity with
quality, and that's the wrong trade for a thermal median.

**"Is A/C access in the score?"** **No, and that's deliberate — this is the good
question to get.** A/C isn't measured by any census; it's modelled from income
percentile. In LA that works because block-group medians span $20k to $250k. San
Ramon's span **$102k to $250k** — so the same transform would manufacture a
35%-to-95% spread of "A/C access" across a town where essentially everyone can
afford it, and then hand that invented variation a quarter of the score. So it's
built, viewable on the map, and **weighted zero**. Every input the score actually
uses is measured.

**"Isn't a hex smaller than a census block group?"** Yes — about a ninth, at this
resolution. Heat and canopy are genuinely per-hex (30 m satellite rasters).
Population, age and income are real ACS numbers spread by area, so they vary
smoothly across neighbours rather than block by block. That's stated in the app's
footer. The alternative was res 8, which is 71 hexes for the whole city and
doesn't look like a map.

**"Does shade actually cool, or is that just terrain?"** Across the 419 populated
hexes, heat and greenness correlate at **r = −0.800** (−0.808 after removing a
quadratic spatial trend). That's stronger than the
LA build's −0.61, and unlike LA there's no coastline here to confound it.

**"Is the walk time routed?"** No — straight-line × 1.273 (= 4/π, the exact
expected Manhattan-to-Euclidean ratio over uniform bearings) at 4.8 km/h. Say
"estimated walking minutes"; never imply a street route.

**"What counts as a cooling site?"** 25 of them from OpenStreetMap: 12 community
centres, 5 public pools, 5 senior centres/shelters, 3 libraries. Places a
resident with no A/C could walk to and sit in the cool for free — **not** a list
San Ramon has formally designated for a heat emergency.

**"Where does the $500 a tree come from?"** A planning assumption, and the panel
says so in those words — the order of magnitude US municipal programmes budget
for a planted street tree plus about three years of establishment care. Not a
quote. The cooling coefficient is WRI's published figure and 40 m² of crown per
mature tree is a standard planning number. **Don't defend the $500 as a
measurement**; the defensible claim is dollars per resident cooled, which makes
two neighbourhoods comparable whatever unit cost you plug in.

**"Your scale is relative — what if the city just isn't hot?"** Correct, and the
legend concedes it: every input is min–max normalised *within the city*, so 100
means first in line here, not hot in absolute terms. That's the deliberate trade
for portability. Switch to the **Surface temperature** layer for absolute values —
and note San Ramon's max is 51.1 °C surface, which is not nothing.

**"Can I look at my city?"** Not today, and the picker says so rather than
loading San Ramon's numbers under another name. Los Angeles is in the list
without a data flag because it's built on `master`, not on this branch.

---

## The 60s screen capture (do this, it's the last fallback)

Not yet recorded. On macOS: **⌘⇧5 → Record Selected Portion**, frame the browser
window only, run the script above, save as `demo.mp4` next to this file, and
check it plays with Wi-Fi off.
