# app/: the original layout carrying the features of the `app2/` redesign

This is the shipped app. It was built as `app3/`, a merge of the original
`app/` (layout) and the `app2/` comparison copy (features), then moved here.

Same data, same scoring, same script as `app2/` (which is `app/`'s script plus
the shortlist, filters, report and share code). Only the panel structure and
the map controls differ. Open from the repo root server:

- Shipped: http://localhost:8000/app/?go=1
- Redesign copy it drew from: http://localhost:8000/app2/?go=1

## Kept from `app/` (the layout)

- Header with the tagline and visible help buttons (How to use, Data &
  methods, Cooling centers) and the units toggle, instead of an overflow menu.
- Foldable sections in one scroll, ordered by cause and effect: 1 What
  matters most, then Shortlist and 2 Priority areas directly under it (the
  only thing section 1 changes), then a "Map display" group (Color the map
  by, Places to cool off) that changes the map and never the ranking, then
  Export & share. Fold state is remembered per browser as before.
- Map layer and cooling-site controls live in the panel, not behind a
  "Layers" button on the map, so the map stays clear and every control has
  a fixed place.
- Reset zoom, Reset map and the Map/Satellite switch at the top right of the map.
- Export & share as a section with one labelled button per artefact.

## Kept from `app2/` (the features)

- Weights bar under the presets with Adjust; sliders open in place, the
  section pins to the top of the scroll while open, and Reset to recommended.
- Ranked rows with aligned heat / trees / walk columns, a contribution bar in
  the weight colours, and a star; movement chips and the "Re-ranked" notice.
- Shortlist block above the ranking with residents / trees / cost totals,
  Export CSV and Clear; persisted per city in the browser.
- Find: search plus sort (need, residents, heat, tree cover, walk, age 65+)
  and five data-backed filter chips. Rank badges never change.
- Status chip on the map (city, question, layer, selected area) with Share,
  and the URL hash that carries weights, layer and selection.
- Zoom in / out stack at the bottom right.
- Legend hint "Click any area to see why it ranks there" until a selection.
- Detail: "What puts it here" drivers bar, Previous / Next, star, editable
  cost per tree that feeds the scenario, shortlist totals and every export.
- Toast feedback for exports, stars and clears. Print stylesheet.
- Briefing report (Letter-sized page, print to PDF) from Export & share.
- Below 1100px the detail slides over the list and the map stays visible.

## Dropped

- Simple / Explore mode switch. The presets are the simple entry; a second
  mode hid the sections a first-time user needs to find. Its takeaway text
  was one static sentence, now carried by the coach card.
- The floating Layers panel and the overflow menu (both replaced by panel
  sections and header buttons).

## Round 2 (after the critique)

- Light / Dark switch in the header, saved per browser, defaulting to the
  system setting. Light restates the chrome colours for projectors and
  handouts; data colours (badges, ramps, swatches) are unchanged, and the
  text tints computed from them darken instead of lighten on light.
- While Adjust is open the plain-language reading of the mix stays on screen
  under the weights bar.
- Row stars are 24px targets and show at full opacity whenever the row has
  focus. The detail star is 32px.
- Cooling centers link only under Places to cool off, not in the header.

## Round 3

- Shortlist folds like every other section (chevron, state remembered).
- Clear asks first: Keep it, Clear, or Save CSV & clear; × and Escape keep it.
- Sort has an ⓘ describing every option, a "most first / least first" toggle
  (tree cover defaults to least first, everything else to most first), and a
  line under the search saying what the list is sorted by and what that
  measure is. Rank badges never change with a sort.

## Round 4

- The guide has a "Sorting, filtering and searching the list" topic at
  `guide.html#sort`; the sort ⓘ links to it.
- CSV exports drop the `redlining_grade` column when no area in the city
  carries a grade. The JSON field key is unchanged.
- "Take it with you" band and heading separate Export & share from the Map
  display group.
