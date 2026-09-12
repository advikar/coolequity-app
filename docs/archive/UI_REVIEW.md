# Contra Costa UI/UX review — September 7, 2026

## Current update — conditional scenarios and official cooling sources

September 7, 2026; Contra Costa branch only. This supersedes the earlier 99%-coverage
scenario gate. Coverage is the fraction assessed, **not a percentage accuracy score**.

- Conditional tree counts, cost, added canopy and illustrative air cooling now require
  mapped street capacity and valid area: **1,832 residential cells**. The former blanket
  exclusion was unnecessarily restrictive for scoping. None of these outputs certify
  plantability or budget accuracy; 10m spacing, 40m² new crown and $500/tree remain assumptions.
- `canopy_baseline_ok` retains the >=99% aerial-coverage check only for displaying a
  whole-cell current-to-future canopy total (788 residential cells). Partial or unknown
  coverage displays added canopy but omits a future total. Known aerial canopy area bounds
  the maximum possible new area without extending partial coverage over unassessed land.
- UI replaces “pts” with **percentage-point canopy gain**. Guide example: 10% → 15% is
  +5 percentage points. Added crowns and cooling require feasible, non-overlapping new cover.
- Cooling is explicitly **summer air cooling**, not surface-temperature change. A surface
  response formula has not been added: cross-sectional tree/urban LST differences are not
  a validated marginal intervention response for Contra Costa. Surface shading benefits are
  explained without inventing a local degree reduction. Source: Schwaab et al. (2021),
  https://pmc.ncbi.nlm.nih.gov/articles/PMC8611034/.
- Added searchable **county-listed cooling directory**, 17 locations with addresses and
  phone links. Source: EHSD bulletin, June 2026 revision, served at the July 2026 URL and
  checked September 7. No open-now status, coordinates, hours or unrestricted eligibility
  are invented. The source asks visitors to call before going.
- The same bulletin identifies El Cerrito and Kensington libraries as lacking A/C. Both
  are excluded by exact name/kind from the discovery inventory (488 → 486); walking
  estimates rebuilt against the remaining discovery sites. The official directory is a
  distinct reference, not the denominator of the walking layer.
- Routing now projects cells before finding centroids, exports the cell-to-network straight
  connection length, and flags connections >100m for approach review. The flag is an
  operational review trigger, not assurance that shorter approaches are safe or accessible.
- Failed optional-site loads now show a status message and retain access to official contacts.

Remaining: official-site coordinates/entrances, hours and eligibility verification; routing
against that service set; local species/growth/survival and cost validation; uncertainty
propagation and full surface-model development. No public deployment has occurred.


## Current rebuild update — September 7, 2026

Public Explore now separates canopy and a 0–100 satellite greenness index. Environmental
layers show the full grid; missing canopy and unsupported A/C estimates are neutral gray.
Scenario hierarchy is trees → added canopy → indicative cost, with air cooling secondary.
Aerial coverage must reach 99% for scenarios; the threshold is operational, not certification.
ACS 2024 and housing-weighted LACE are rebuilt; export/browser ranks agree. Current data:
2,697 residential cells, 788 scenario-eligible residential cells. Earlier counts and descriptions
below are historical. See PRODUCT_READINESS.md and reports/rebuild_summary.json for remaining
production gaps and numerical validation.


The original experience looks more finished than it behaves. Its strongest asset is a useful
question: where should a county investigate tree investment first? Its main weakness is that
a user must decode layers, weighting, geography and a cost model before reaching a clear
next action. This is a strong planning prototype, not yet a complete operational product.

Review scope: the supplied shared conversation, the Contra Costa landing screen, Simple and
Explore modes, layer/preset controls, ranked list, selected-cell metrics, score breakdown,
planting calculator, help, methods, desktop and narrow-screen layouts. Other cities' separate
branches were not edited or represented as tested. Ratings below are heuristic judgments of
the original Contra Costa experience, not usability-study scores or compliance certification.

| Dimension | Original rating | Assessment |
|---|---:|---|
| Visual hierarchy | 7/10 | Distinctive typography and restrained palette, undermined by tiny gray copy and too many similarly weighted explanations. |
| Navigation and discoverability | 5/10 | The shortlist is buried; Simple/Explore hides capability without sufficiently explaining what changes. Help disappears after onboarding. |
| Comprehension | 4/10 | The same concepts are repeatedly explained with different vocabulary: block, hex, neighborhood; heat, need, risk; ROI and planting cost. |
| Decision support | 6/10 | Ranking plus scenario calculation is valuable, but a canopy target lacks an obvious implementation action. No saved scenarios, comparisons or report export. |
| Trust and evidence | 5/10 | Sources exist, but confident labels overstate what the calculations establish. Count inconsistencies compound the problem. |
| Keyboard/accessibility | 4/10 | Clickable divs and offscreen controls impair keyboard and assistive-technology use. The full map still lacks a complete nonvisual data equivalent. |
| Mobile use | 4/10 | Fixed desktop panels were not designed around a narrow viewport. |
| Overall readiness | 5.5/10 | Suitable for guided stakeholder exploration; insufficient for unsupported operational decisions. |

## Assessment of the user's feedback

- **Remove irrelevant story overlays: agree.** In Contra Costa there are no graded cells.
  A long explanation of an absent layer consumes scarce attention. Hide the historical
  heading/control; preserve useful walking access as a separate feature. Lack of coverage
  must not be framed as absence of historical discrimination.
- **Restore a planting-share control: agree.** A share of mapped street capacity is an action
  a planner can explore. Renamed the module Planting scenario because it calculates no
  financial return. “Public right-of-way” requires qualification: OSM road classes do not
  verify ownership or planting room.
- **Keep How to use available: agree.** Added a persistent button and keyboard-accessible
  close/return behavior. Remembering dismissal should prevent nagging, not remove help.
- **Create one comprehensive guide with contextual links: agree.** Added 17 searchable,
  filterable accordion topics. Every topic explains function, purpose, source/method and
  limits. Links from metrics, scoring, layers, walking, planting and cost open the relevant
  topic in a reusable guide tab, preserving the map and scenario.
- **Simplify visible copy and collapse score arithmetic: agree.** The map should show the
  answer and next action. The arithmetic is now a native disclosure; longer evidence moved
  into the guide. The first ranked areas are visible much sooner on desktop.
- **Pitch the product accurately: agree, with a boundary.** Explain a method's advantage and
  its failure modes. Do not call an approximation the most accurate without validation.
  The credible pitch is a transparent shortlist for field assessment, not a guaranteed plan.

## Implemented in this pass

Persistent help and evidence navigation; shorter landing/workspace/preset copy; removal of
irrelevant historical material; 0–100% planting-share slider; tree count/cost/canopy-gain
outputs; explicit illustrative cooling; corrected A/C and site labels; score denominator
consistency; keyboard shortlist buttons; focus management and hidden-content isolation;
mobile stacked layout and full-width detail; searchable source guide and GeoJSON download.

The shared review incorrectly implied the ranked entries were not clickable: they already
were. Their actual defect was lacking native keyboard semantics. The 2,695/2,859 count
mismatch was real and is corrected. The new guide is intentionally concise on first view,
with detail revealed on demand; it is not a new wall of default-visible prose.

## What still prevents a stronger product claim

1. A planner cannot yet find every address/cell through a keyboard-accessible searchable
   browser. The top-25 list is an alternative for those entries only.
2. A planning meeting needs saved scenarios, shareable selections, comparison and an export
   containing assumptions, weights, source vintages and build version.
3. Cooling sites, public land, utilities, tree inventory and planting costs need local
   verification. The UI now admits these gaps; it does not resolve them.
4. Demographic uncertainty and per-cell source/coverage flags are not exposed in the map
   payload. Rounded point values remain more precise-looking than the underlying evidence.
5. The introductory story would benefit from an explicit returning-user shortcut and a
   test with actual county staff: ask them to select an area, explain its rank, scope a
   planting scenario, and identify which claims require field verification without coaching.

Validation completed: source and input inspection; confirmed residential LACE coverage and
published under-15%-canopy resident count; browser checks for desktop, 390px layout, keyboard
selection/close, help, guide hash/search, units and zero planting; syntax/anchor checks and
11,436 scenario cases over 2,859 cells. This is targeted verification, not WCAG certification,
field validation, or a declaration of government procurement readiness.

The changes are local on contra-costa. The public site has not been deployed in this pass.


## Follow-up audit supersedes the original readiness assessment

See `PRODUCT_READINESS.md` for the more complete, sourced review. The first review missed
430 residential vegetation-proxy cells labeled canopy and inconsistent exported canopy areas.
Those findings are release-significant. The UI now identifies proxy cells and prevents their
planting scenarios; underlying canopy coverage still needs repair. The new guide leads with
city use cases and method rationale, uses compact planning notes, and the ranked list is
searchable/paginated beyond the top 25. Do not use the earlier “top 25 only” limitation as the
current state, or the earlier canopy assurance as validation of the county data.
