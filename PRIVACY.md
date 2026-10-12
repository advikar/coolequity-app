# Privacy and resolution policy

CoolEquity is an independent student project. It is not a city or county
product and has not been reviewed by any city or county.

## The line we do not cross

**Nothing is published at address or household resolution.** Every figure
about residents is aggregated to a hexagonal area of roughly 0.04 square
miles (H3 resolution 8 or 9) or coarser. The app, the exports and the briefing
report never show, and the pipeline never stores, a figure tied to a single
home, parcel or person.

## What each layer contains, and why it is safe

| Layer | Resolution | Source | Notes |
|---|---|---|---|
| Residents, age 65+ | Hexagon (allocated from Census block groups) | US Census ACS 5-year | Block groups hold hundreds of households; allocation spreads them, it does not locate them. |
| Home air conditioning | Hexagon (from Census tracts) | Census LACE | Tract-level estimate; no household data. |
| Surface heat | 30 m satellite pixels averaged to the hexagon | Landsat 8/9 | Ground temperature, not people. |
| Tree cover | Aerial classification averaged to the hexagon | USFS / CAL FIRE 2022 | Land cover, not people. |
| Streets | Public street centrelines | OpenStreetMap | Public infrastructure. |
| Building footprints (pipeline input only) | Individual outlines, no attributes | OpenStreetMap | Used once, to allocate block-group totals by residential floor area. Not shown in the app. Carries no owner, occupant or value data. |
| Cooling sites | Public facilities with public addresses | OpenStreetMap, Kern County | Libraries, community centers, pools, senior centers. Public institutions only. |
| 1930s redlining grades | Historical polygons | Mapping Inequality | Historical public record; shown only where a map exists. |

## Rules for contributors

1. Do not add any layer with a parcel, address, household, individual or
   vehicle as its unit. Aggregate to the hexagon first, or leave it out.
2. Do not add per-area fields that could single out a household, for example
   a count that is often 1, or an income figure for an area with very few
   residents. If an area holds fewer than about 20 residents, blank the
   demographic fields for it before publishing.
3. Do not collect anything from visitors. The site sets no cookies, calls no
   analytics, and keeps a user's weights and shortlist only in their own
   browser. Keep it that way.
4. Do not publish photographs of homes or people from ground-truth walks.
   Street trees, pavements and shade are fine. Faces, house numbers and
   licence plates are not.
5. Keep the "independent student project, not a city product" line on every
   page and in every export.
