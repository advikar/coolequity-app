/* Pittsburg & Bay Point — map settings, loaded by app/index.html before its main script.
 *
 * Everything the map page says or weighs differently for this study area lives
 * here; app/index.html itself is shared by every city. The pipeline's copy of the
 * weights is cities/pittsburg/config.py, and tests/ui-contract.cjs fails if the two
 * ever disagree.
 *
 * The study area is the city of Pittsburg plus the unincorporated Bay Point
 * community next to it, on the east side of Contra Costa County. It was cut
 * from the county build because the two together hold 15 of the county's 100
 * highest-need areas; the grid here is seven times finer (0.04 sq mi).
 *
 * HEAT IS NOT SCORED HERE, as in the county map this area was cut from. On
 * this build's own residential cells above 35 C, position still explains 28%
 * of the variance in summer surface temperature (39% county-wide, 11% in West
 * Contra Costa), and heat runs slightly WITH tree cover (r = +0.23): the newer
 * hillside subdivisions are hotter and greener than the older neighbourhoods
 * by the shore. Scoring heat would reward distance from the water, not lack
 * of shade. It is shown and movable at weight 0.
 *
 * A/C IS SCORED (25%): Census LACE 2023 puts A/C in 69–96% of homes across
 * the area. Mirrors cities/pittsburg/config.py WEIGHTS. */
window.CE_CITY={
  slug:'pittsburg',
  name:"Pittsburg & Bay Point",
  possessive:"Pittsburg’s",   // "Built for …’s urban forestry, climate and public works teams"
  scope:'study area',                 // "relative within this study area"
  dataVersion:'20260913-build1',
  // How 03_census.py placed residents in this build (guide.html says why); the briefing's source table reads it.
  popAllocation:'area',
  centersVersion:'20260913-ehsd',
  coolingLinkLabel:"County-listed locations & contacts ↗",
  scoreTitle:"Canopy priority",
  introNote:"Pittsburg and the unincorporated Bay Point community next to it, at seven times the county map’s resolution. As on the county map, surface heat is shown but not scored: here a hotter area is mostly one farther from the water, not one with fewer trees.",
  weights:{heat:0.00,green:0.55,ac:0.25,age65:0.20,access:0},
  inputNotes:{heat:"shown, not scored: tracks distance from the shore, not shade",ac:"Census LACE estimate — scored here"},
  /** Presets set all four weights at once. w:'default' / pop:'default' mean the
   *  recommended weights and population multiplier above. */
  presets:[
  {id:'default',name:'Recommended mix',w:'default',pop:'default',
   why:'Missing tree cover (55%), homes without A/C (25%) and older residents (20%), adjusted for how many people live in each area. Heat is shown but not scored: here it mostly measures distance from the water.'},
  {id:'canopy',name:'Trees only',w:{heat:0,green:1,ac:0,age65:0,access:0},pop:.45,
   why:'Only tree cover and population. Ignores A/C and age.'},
  {id:'heat',name:'Heat first',w:{heat:.70,green:.15,ac:.10,age65:.05,access:0},pop:.45,
   why:'Mostly ground heat. Use with care here: a hotter area is mostly one farther from the shore, not one with fewer trees.'},
  {id:'seniors',name:'Older residents',w:{heat:.25,green:.20,ac:.10,age65:.45,access:0},pop:.45,
   why:'Puts most weight on residents aged 65+, with tree cover and A/C still counting.'},
  {id:'ac',name:'Homes without A/C',w:{heat:.20,green:.15,ac:.60,age65:.05,access:0},pop:.45,
   why:'Puts most weight on homes without air conditioning (Census estimates).'},
  {id:'stranded',name:'Far from cooling',w:{heat:.30,green:.25,ac:.15,age65:.10,access:.20},pop:.45,
   why:'Adds walking distance to the nearest mapped cool place. Those places are not verified as open cooling centers.'},
  {id:'people',name:'Most people',w:'default',pop:.90,
   why:'The recommended mix, but areas with more residents count much more.'},
  ],
};
