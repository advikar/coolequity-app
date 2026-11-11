/* West Contra Costa — map settings, loaded by app/index.html before its main script.
 *
 * Everything the map page says or weighs differently for this study area lives
 * here; app/index.html itself is shared by every city. The pipeline's copy of the
 * weights is cities/westcc/config.py, and tests/ui-contract.cjs fails if the two
 * ever disagree.
 *
 * The study area is the west side of Contra Costa County: Richmond, San Pablo,
 * El Cerrito, Pinole, Hercules and the unincorporated places between them
 * (North Richmond, El Sobrante, Rodeo, Crockett, Kensington, Tara Hills,
 * Montalvin Manor, Rollingwood, Bayview, East Richmond Heights, Port Costa).
 * It was cut from the county build because these places hold most of the
 * county's highest-need areas; the grid here is seven times finer (0.04 sq mi).
 *
 * HEAT IS SCORED HERE (35%), unlike the county map this area was cut from.
 * Re-measured on summers 2024-2026: across ranked areas position explains 14%
 * of the variance in summer surface temperature county-wide and 6% inside West
 * County, where heat tracks missing greenness (r = -0.55 over land cells at or
 * above 27 C). A hotter area here is mostly a barer area, which is what a
 * shade-planting screen should see.
 *
 * A/C IS SCORED (15%): Census LACE 2023 puts A/C in roughly 46–82% of homes
 * across this area, the widest spread of any build. Mirrors
 * cities/westcc/config.py WEIGHTS. */
window.CE_CITY={
  slug:'westcc',
  name:"West Contra Costa",
  possessive:"West Contra Costa’s",   // "Built for …’s urban forestry, climate and public works teams"
  scope:'study area',                 // "relative within this study area"
  dataVersion:'20260921-stability',
  // How 03_census.py placed residents in this build (guide.html says why); the briefing's source table reads it.
  popAllocation:'dasymetric',
  centersVersion:'20260913-ehsd',
  layerNotes:{dac:"State-designated disadvantaged communities (CalEPA, September 2026). A funding-eligibility screen, not a measurement; the “Disadvantaged communities” preset ranks within it."},
  coolingLinkLabel:"County-listed locations & contacts ↗",
  scoreTitle:"Heat & canopy priority",
  introNote:"Richmond, San Pablo, El Cerrito, Pinole, Hercules and the unincorporated places between them, at seven times the county map’s resolution. Unlike the county map, surface heat is scored here: within West County it tracks missing shade rather than distance from the Bay.",
  weights:{heat:0.35,green:0.35,ac:0.15,age65:0.15,access:0,dac:0.00},
  inputNotes:{heat:"hotter area → higher need; one bay-side climate",ac:"Census LACE estimate — scored here",dac:"CalEPA 2026 designation — a policy screen, starts at 0"},
  /** Presets set all four weights at once. w:'default' / pop:'default' mean the
   *  recommended weights and population multiplier above. */
  presets:[
  {id:'default',name:'Recommended mix',w:'default',pop:'default',
   why:'Ground heat (35%) and missing tree cover (35%), then homes without A/C (15%) and older residents (15%), adjusted for how many people live in each area.'},
  {id:'dac',name:'Disadvantaged communities',w:{heat:.30,green:.30,ac:0,age65:.05,access:0,dac:.35},pop:'default',
   why:'SB 535-designated disadvantaged communities (35%), ground heat (30%) and missing tree cover (30%), with older residents (5%), adjusted for population. Hot, bare areas inside designated tracts lead; the same conditions outside them rank lower but stay on the list.'},
  {id:'canopy',name:'Fewest trees',w:{heat:0,green:1,ac:0,age65:0,access:0,dac:0},pop:.45,
   why:'Tree cover alone, adjusted for population. Ignores heat, A/C and age.'},
  {id:'heat',name:'Heat first',w:{heat:.70,green:.15,ac:.10,age65:.05,access:0,dac:0},pop:.45,
   why:'Mostly ground heat. Within West County a hotter area is mostly a barer one.'},
  {id:'seniors',name:'Older residents',w:{heat:.25,green:.20,ac:.10,age65:.45,access:0,dac:0},pop:.45,
   why:'Puts most weight on residents aged 65+, with tree cover and A/C still counting.'},
  {id:'ac',name:'Homes without A/C',w:{heat:.20,green:.15,ac:.60,age65:.05,access:0,dac:0},pop:.45,
   why:'Puts most weight on homes without air conditioning (Census estimates).'},
  {id:'stranded',name:'Far from cooling',w:{heat:.30,green:.25,ac:.15,age65:.10,access:.20,dac:0},pop:.45,
   why:'Adds walking distance to the nearest mapped cool place. Those places are not verified as open cooling centers.'},
  {id:'people',name:'Most people',w:'default',pop:.90,
   why:'The recommended mix, but areas with more residents count much more.'},
  ],
};
