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
 * County-wide, position explains 39% of the variance in summer surface
 * temperature (shoreline vs Delta); inside West County it explains 11%, and
 * heat tracks missing greenness (r = -0.64). A hotter area here is mostly a
 * barer area, which is what a shade-planting screen should see.
 *
 * A/C IS SCORED (15%): Census LACE 2023 puts A/C in roughly 46–82% of homes
 * across this area, the widest spread of any build. Mirrors
 * cities/westcc/config.py WEIGHTS. */
window.CE_CITY={
  slug:'westcc',
  name:"West Contra Costa",
  possessive:"West Contra Costa’s",   // "Built for …’s urban forestry, climate and public works teams"
  scope:'study area',                 // "relative within this study area"
  dataVersion:'20260913-build1',
  centersVersion:'20260913-ehsd',
  coolingLinkLabel:"County-listed locations & contacts ↗",
  scoreTitle:"Heat & canopy priority",
  introNote:"Richmond, San Pablo, El Cerrito, Pinole, Hercules and the unincorporated places between them, at seven times the county map’s resolution. Unlike the county map, surface heat is scored here: within West County it tracks missing shade rather than distance from the Bay.",
  weights:{heat:0.35,green:0.35,ac:0.15,age65:0.15,access:0},
  inputNotes:{heat:"hotter area → higher need; one bay-side climate",ac:"Census LACE estimate — scored here"},
  /** Presets set all four weights at once. w:'default' / pop:'default' mean the
   *  recommended weights and population multiplier above. */
  presets:[
  {id:'default',name:'Recommended mix',w:'default',pop:'default',
   why:'Ground heat (35%) and missing tree cover (35%), then homes without A/C (15%) and older residents (15%), adjusted for how many people live in each area.'},
  {id:'canopy',name:'Trees only',w:{heat:0,green:1,ac:0,age65:0,access:0},pop:.45,
   why:'Only tree cover and population. Ignores heat, A/C and age.'},
  {id:'heat',name:'Heat first',w:{heat:.70,green:.15,ac:.10,age65:.05,access:0},pop:.45,
   why:'Mostly ground heat. Within West County a hotter area is mostly a barer one.'},
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
