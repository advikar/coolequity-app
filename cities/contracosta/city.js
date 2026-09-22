/* Contra Costa County — map settings, loaded by app/index.html before its main script.
 *
 * Everything the map page says or weighs differently for this city lives here;
 * app/index.html itself is shared by every city. The pipeline's copy of the
 * weights is cities/contracosta/config.py, and tests/ui-contract.cjs fails if the two
 * ever disagree.
 */
/* HEAT SHIPS AT WEIGHT 0 IN THIS BUILD, and it is the decision most worth
 * understanding here. Every input is normalised min-max WITHIN the study area,
 * which assumes the study area is one climate. A city is. This county is not: it
 * runs from the Richmond shoreline to the Delta, mean summer surface temperature
 * 36.8 °C west against 43.1 °C east, and 38.8% of ALL variance in surface
 * temperature is explained by longitude and latitude alone.
 *
 * The effect is measurable rather than theoretical. In San Ramon
 * corr(LST, canopy) = -0.800, and -0.808 after removing a spatial trend: shade
 * demonstrably cools. Here it is -0.120, -0.149 detrended, and by longitude band
 * it swings from +0.381 to -0.092. There is no consistent shade effect at this
 * scale to score. So heat keeps its layer, its legend and its per-hex numbers —
 * all measured, all real — and carries no weight. The "Heat first" preset shows
 * what it says on its own, which is mostly a map of distance from the Bay.
 *
 * A/C IS scored here (weight 0.25), unlike in San Ramon. It is now
 * MEASURED — US Census LACE 2023 A/C-prevalence per tract (ac_src="measured" for
 * every residential hex; the income model survives only as a per-tract fallback,
 * used on 0 res hexes here). It has real spread: 46–100%, median 93%, std 13.
 *
 * The old CIRCULARITY WARNING is retired: A/C no longer derives from income, so
 * the score is NOT income by construction. Measured A/C prevalence does still
 * correlate with income in reality (corr(ac,income)=0.30 over res hexes), so the
 * canopy-equity finding is still computed on raw measured canopy against income
 * with no score involved, and the "Canopy only" preset still exists so anyone can
 * check the answer with A/C removed entirely. Do NOT reintroduce "A/C is modelled
 * from income" into the copy — it was true pre-LACE and is now wrong.
 *
 * `access` also ships at 0 — present, movable, off — so "Canopy deficit" names
 * exactly what config.py weights. Mirrors cities/contracosta/config.py WEIGHTS; tests/ui-contract.cjs checks that. */
window.CE_CITY={
  slug:'contracosta',
  name:"Contra Costa County",
  possessive:"Contra Costa’s",   // "Built for …’s urban forestry, climate and public works teams"
  scope:'county',                         // "relative within this county"
  dataVersion:'20260921-stability',
  // How 03_census.py placed residents in this build (guide.html says why); the briefing's source table reads it.
  popAllocation:'area',
  centersVersion:'20260907-ehsd',
  coolingLinkLabel:"County-listed locations & contacts ↗",
  scoreTitle:"Canopy priority",
  introNote:"Surface heat is measured and shown here but not scored: across a county that runs from the Bay shoreline to the Delta it mostly tracks distance from the water, not a shade problem. The ranking uses tree cover, homes without A/C and older residents.",
  weights:{heat:0.00,green:0.55,ac:0.25,age65:0.20,access:0},
  inputNotes:{heat:"climate-confounded at county scale — starts at 0",ac:"Census LACE estimate — scored here"},
  /** Presets set all four weights at once. w:'default' / pop:'default' mean the
   *  recommended weights and population multiplier above. */
  presets:[
  {id:'default',name:'Recommended mix',w:'default',pop:'default',
   why:'Mostly missing tree cover (55%), then homes without A/C (25%) and older residents (20%), adjusted for how many people live in each area.'},
  {id:'canopy',name:'Fewest trees',w:{heat:0,green:1,ac:0,age65:0,access:0},pop:.45,
   why:'Tree cover alone, adjusted for population. Ignores heat, A/C and age.'},
  {id:'heat',name:'Heat only',w:{heat:1,green:0,ac:0,age65:0,access:0},pop:.45,
   why:'Only ground heat and population. In this county that mostly shows distance from the Bay, not a shade problem.'},
  {id:'seniors',name:'Older residents',w:{heat:0,green:.35,ac:.15,age65:.50,access:0},pop:.45,
   why:'Puts most weight on residents aged 65+, with tree cover and A/C still counting.'},
  {id:'ac',name:'Homes without A/C',w:{heat:0,green:.30,ac:.60,age65:.10,access:0},pop:.45,
   why:'Puts most weight on homes without air conditioning (Census estimates).'},
  {id:'stranded',name:'Far from cooling',w:{heat:0,green:.40,ac:.20,age65:.15,access:.25},pop:.45,
   why:'Adds walking distance to the nearest mapped cool place. Those places are not verified as open cooling centers.'},
  {id:'people',name:'Most people',w:'default',pop:.90,
   why:'The recommended mix, but areas with more residents count much more.'},
  ],
};
