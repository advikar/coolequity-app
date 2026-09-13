/* San Ramon — map settings, loaded by app/index.html before its main script.
 *
 * Everything the map page says or weighs differently for this city lives here;
 * app/index.html itself is shared by every city. The pipeline's copy of the
 * weights is cities/sanramon/config.py, and tests/ui-contract.cjs fails if the two
 * ever disagree.
 */
/* HEAT IS SCORED IN THIS BUILD (45%), unlike Contra Costa. Every input is
 * normalised min-max WITHIN the study area, which assumes the study area is one
 * climate. San Ramon is: one valley city where corr(LST, canopy) = -0.80 and
 * -0.81 after removing a spatial trend, so shade demonstrably cools and a
 * hotter cell is a hotter place to live rather than a different climate.
 *
 * A/C SHIPS AT WEIGHT 0 here. It is built and viewable (Census LACE 2023,
 * housing-weighted), but San Ramon is uniformly affluent -- block-group median
 * incomes $100,906-$250,001 -- and its A/C prevalence is high and narrow, so
 * the input would add noise rather than need. The "Low A/C access" preset
 * shows what it looks like when it is scored.
 *
 * `access` also ships at 0 -- present, movable, off. Mirrors cities/sanramon/config.py WEIGHTS; tests/ui-contract.cjs checks that. */
window.CE_CITY={
  slug:'sanramon',
  name:"San Ramon",
  possessive:"San Ramon’s",   // "Built for …’s urban forestry, climate and public works teams"
  scope:'city',                         // "relative within this city"
  dataVersion:'20260909-walk',
  centersVersion:'20260908-ehsd',
  layerNotes:{ac:"A/C prevalence is high and narrow across San Ramon, so this layer shows little contrast and carries no weight in the recommended mix."},
  coolingLinkLabel:"County-listed cooling centers & contacts ↗",
  scoreTitle:"Heat & canopy priority",
  weights:{heat:0.45,green:0.33,ac:0.00,age65:0.22,access:0},
  inputNotes:{heat:"hotter cell → higher risk",ac:"Census LACE estimate — not in the shipped model, starts at 0"},
  /** Presets set all four weights at once. w:'default' / pop:'default' mean the
   *  recommended weights and population multiplier above. */
  presets:[
  {id:'default',name:'Recommended mix',w:'default',pop:'default',
   why:'Ground heat (45%), missing tree cover (33%) and older residents (22%), adjusted for how many people live in each area. A/C is not counted here.'},
  {id:'canopy',name:'Trees only',w:{heat:0,green:1,ac:0,age65:0,access:0},pop:.45,
   why:'Only tree cover and population. Ignores heat and age.'},
  {id:'heat',name:'Heat first',w:{heat:.70,green:.18,ac:0,age65:.12,access:0},pop:.45,
   why:'Mostly ground heat. San Ramon is one valley climate, so a hotter area really is a hotter place to live.'},
  {id:'shade',name:'Shade gap',w:{heat:.25,green:.62,ac:0,age65:.13,access:0},pop:.45,
   why:'Leans on missing tree cover while keeping heat and age in view.'},
  {id:'seniors',name:'Older residents',w:{heat:.22,green:.18,ac:0,age65:.60,access:0},pop:.45,
   why:'Puts most weight on residents aged 65+, with heat and tree cover still counting.'},
  {id:'ac',name:'Homes without A/C',w:{heat:.20,green:.15,ac:.60,age65:.05,access:0},pop:.45,
   why:'Puts most weight on homes without air conditioning. Not in the recommended mix; A/C is high and uniform here, so expect small changes.'},
  {id:'stranded',name:'Far from cooling',w:{heat:.34,green:.25,ac:0,age65:.16,access:.25},pop:.45,
   why:'Adds walking distance to the nearest mapped cool place. Those places are not verified as open cooling centers.'},
  {id:'people',name:'Most people',w:'default',pop:.90,
   why:'The recommended mix, but areas with more residents count much more.'},
  ],
};
