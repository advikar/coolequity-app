# CoolEquity — recorded walkthrough script (~4:15)

Longer than `DEMO.md`. That one is the 60–90s live pitch; this is the recorded
version, where you have room to show how it actually works.

**Delivery notes.** Read it once out loud before recording — you'll find your own
phrasing and that's better than mine. Slow down on the numbers and speed up on
the connective tissue. The pauses marked `///` are worth actually taking; they're
where a listener catches up. Don't smooth over the caveats in the last section —
knowing exactly what your data can't say is the thing that reads as depth.

Record at 1440×860 or full screen, browser only, `?flat=1` **off** (you want the
street basemap in the video).

---

### [0:00] Hook — Priority layer, don't touch anything yet

Heat kills more people than any other weather event. Around 489,000 deaths a
year. And it isn't evenly distributed — it lands on the blocks with the least
shade, the oldest housing, and the least air conditioning.

Cities know this. What they don't have is a way to point at one specific block
and say: *that one. First.* ///

That's what I built.

### [0:25] What you're looking at — slow pan / slight zoom

This is Los Angeles. Every hexagon is about eight-tenths of a square kilometre —
that's H3 resolution 8 — and there are 3,008 of them, covering six and a half
million people.

Each one is scored on five things: how hot the surface actually gets, how much
tree canopy it has, how many people live there, how many of them are over 65,
and how far they'd have to walk to the nearest cooling centre.

None of this is hand-drawn or hand-labelled. It all falls out of a pipeline.

### [0:55] How it's built — click through Surface heat, then Greenness

The heat is Landsat 8 and 9 thermal — the ST_B10 band — taken as a summer 2023
median, so one cloudy day can't skew a hexagon. Greenness is Sentinel-2 NDVI
over the same window. Both pulled from Microsoft's Planetary Computer, so
there's no Earth Engine account anywhere in the loop.

Population and age are American Community Survey block groups, area-weighted
into the hexes. Cooling centres — libraries, public pools, community centres —
come out of OpenStreetMap through Overpass. 645 of them.

Then every input is min–max normalised **within the city**. /// That's the part
that matters for portability. 44 degrees is an ordinary afternoon in Phoenix and
an emergency in Seattle. Normalising locally is what lets the same score mean
the same thing anywhere you point it.

### [1:45] The finding — toggle Redlining (HOLC)

Here's where it gets interesting. Let me turn on the 1930s redlining grades.

These are the HOLC maps. The federal government colour-coded neighbourhoods by
lending risk, and the D-graded ones — the ones stamped "hazardous" — were
overwhelmingly Black and immigrant.

Ninety years later: those D-graded blocks run **6.7 degrees Celsius hotter**
than the A-graded ones, with about a third of the tree canopy. Nine percent
against twenty-six. /// And it's monotonic — A, B, C, D, it climbs every single
step.

Now, I want to be careful here. *(toggle Cooling-access gap)* The obvious next
claim is that these areas are also cut off from relief. In LA that's actually
backwards. The redlined core is **closer** to cooling centres — twelve minutes
versus twenty — because dense inner-city neighbourhoods have libraries and low-
density suburbs don't.

So the redlining signal here is heat and missing shade. Not distance. I checked,
and I'm not going to overstate it.

### [2:40] Is the effect real?

And to make sure the heat–canopy relationship isn't just LA's coastal gradient —
cooler and greener near the ocean — I ran the correlation inside separate
longitude bands, and partialled out a quadratic spatial trend.

Minus 0.61 overall. Minus 0.58 after removing the trend. /// Shade is doing the
work, not geography.

### [3:10] The decision — click the #1 ranked hex, then drag the slider

So here's the actual product. Top-ranked hexagon in the city.

Westlake. 47.4 degrees surface temperature, three percent canopy, 15,759
residents.

Drag the canopy slider and it prices the intervention. Getting from three
percent to fifteen is roughly 2,470 trees across that hexagon — that's about
forty square metres of crown per mature tree. WRI's coefficient puts every ten
points of canopy at around three tenths of a degree, so call it a third of a
degree of afternoon cooling, for 15,759 people, 1,797 of them over 65.

About 1.2 million dollars. Seventy-eight dollars a resident. ///

That's the number that moves a city council. Because at that point it isn't a
map anymore — it's a line item.

### [3:55] What's estimated, and the close

Two things I'd flag honestly. Air-conditioning access is modelled from income,
not measured — it's labelled as an estimate in the interface, and it carries
twenty-five percent of the score. And walk time is straight-line distance times
1.273 — that's four over pi, the expected ratio of Manhattan to Euclidean
distance over uniform bearings — not a routed street network. It's the right
correction for a grid city like LA. But it's an estimate, and I say so.

Everything here except the redlining overlay is global. Landsat, Sentinel-2,
OpenStreetMap, population grids. Point it at Lagos or Delhi tomorrow and it
answers the same question. ///

Where does the first tree go?
