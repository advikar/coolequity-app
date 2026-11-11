/* Los Angeles — map settings, loaded by app/index.html before its main script.
 *
 * Everything the map page says or weighs differently for this city lives here;
 * app/index.html itself is shared by every city. The pipeline's copy of the
 * weights is cities/losangeles/config.py, and tests/ui-contract.cjs fails if the two
 * ever disagree.
 */
/* HEAT IS SCORED IN THIS BUILD (35%). Every input is normalised WITHIN the study
 * area, which assumes the study area is close to one climate, and Los Angeles
 * runs from the beach to the San Fernando Valley, so that was measured: across
 * the 9,021 ranked areas position alone explains 8.8% of the variance in summer
 * surface temperature (West Contra Costa, also scored: 6%; Contra Costa
 * County, not scored: 14%), and surface temperature tracks missing tree cover
 * more closely than in any other build (r = -0.66; county -0.20). A hotter
 * area here is mostly a barer area.
 *
 * A/C IS SCORED (15%): Census LACE 2023 runs 44-100% of occupied homes across
 * ranked areas, the widest spread of any build. Do not describe A/C as modelled
 * from income — it is a Census estimate, with the income model surviving only
 * as a fallback for 16 areas whose tract has no estimate (jails, dormitories).
 *
 * `access` ships at 0 — present, movable, off. Mirrors cities/losangeles/config.py
 * WEIGHTS; tests/ui-contract.cjs checks that.
 *
 * `dac` — SB 535 DISADVANTAGED COMMUNITIES (CalEPA, final designation September
 * 2026, CalEnviroScreen 5.0) — ships at 0 in the recommended mix and leads the
 * "Disadvantaged communities" preset. A designation is a funding-eligibility
 * screen, not a need measurement, which is why it is not in the recommended
 * mix. Also a map layer ("SB 535 community").
 *
 * FIRE: 129 ranked areas lie mostly inside the January 2025 Palisades or Hurst
 * fire perimeters. Their tree cover (2022) and residents (2020-2024) predate
 * the fires; the map flags them and the introNote says so. */
window.CE_CITY={
  slug:'losangeles',
  name:"Los Angeles",
  possessive:"Los Angeles’",   // "Built for …’ urban forestry, climate and public works teams"
  districtUnit:'district',               // what this city calls its council areas (By ward / By district)
  wardsOutsideLabel:"City-line areas (center outside the limit)",
  scope:'city',                         // "relative within this city"
  dataVersion:'20261111-la',
  // How 03_census.py placed residents in this build (guide.html says why); the briefing's source table reads it.
  popAllocation:'dasymetric',
  centersVersion:'20261111-lacoa',
  introNote:"Areas inside the January 2025 Palisades and Hurst fire perimeters are flagged: their tree cover (2022) and residents (2020–2024) describe the ground before the fires.",
  layerNotes:{ac:"Home air conditioning varies widely across Los Angeles: near-universal in the Valley, as low as half of homes near the coast and in older housing.",
    dac:"State-designated disadvantaged communities (CalEPA, September 2026). The “Disadvantaged communities” preset ranks hot, bare areas inside them first."},
  coolingLinkLabel:"County-listed cooling centers & contacts ↗",
  scoreTitle:"Heat & canopy priority",
  weights:{heat:0.35,green:0.35,ac:0.15,age65:0.15,access:0,dac:0.00},
  inputNotes:{heat:"hotter cell → higher risk",ac:"Census LACE estimate of homes with A/C",dac:"CalEPA 2026 designation — a policy screen, starts at 0"},
  /** Presets set all the weights at once. w:'default' / pop:'default' mean the
   *  recommended weights and population multiplier above. */
  presets:[
  {id:'default',name:'Recommended mix',w:'default',pop:'default',
   why:'Ground heat (35%), missing tree cover (35%), homes without A/C (15%) and older residents (15%), adjusted for how many people live in each area.'},
  {id:'dac',name:'Disadvantaged communities',w:{heat:.30,green:.30,ac:0,age65:.05,access:0,dac:.35},pop:'default',
   why:'SB 535-designated disadvantaged communities (35%), ground heat (30%) and missing tree cover (30%), with older residents (5%), adjusted for population. Hot, bare areas inside designated tracts lead; the same conditions outside them rank lower but stay on the list.'},
  {id:'canopy',name:'Fewest trees',w:{heat:0,green:1,ac:0,age65:0,access:0,dac:0},pop:.45,
   why:'Tree cover alone, adjusted for population. Ignores heat, A/C and age.'},
  {id:'heat',name:'Heat first',w:{heat:.70,green:.15,ac:.10,age65:.05,access:0,dac:0},pop:.45,
   why:'Mostly ground heat. Expect the San Fernando Valley and the industrial corridors to lead: inland areas run hotter than the coast.'},
  {id:'seniors',name:'Older residents',w:{heat:.25,green:.15,ac:.15,age65:.45,access:0,dac:0},pop:.45,
   why:'Puts most weight on residents aged 65+, with heat, tree cover and A/C still counting.'},
  {id:'ac',name:'Homes without A/C',w:{heat:.25,green:.10,ac:.60,age65:.05,access:0,dac:0},pop:.45,
   why:'Puts most weight on homes without air conditioning. These are mostly coastal and older neighborhoods, which are cooler on average; heat still counts for a quarter.'},
  {id:'stranded',name:'Far from cooling',w:{heat:.30,green:.20,ac:.20,age65:.10,access:.20,dac:0},pop:.45,
   why:'Adds walking distance to the nearest mapped cool place. Those places are not verified as open cooling centers.'},
  {id:'people',name:'Most people',w:'default',pop:.90,
   why:'The recommended mix, but areas with more residents count much more.'},
  ],
};
