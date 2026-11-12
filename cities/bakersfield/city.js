/* Bakersfield — map settings, loaded by app/index.html before its main script.
 *
 * Everything the map page says or weighs differently for this city lives here;
 * app/index.html itself is shared by every city. The pipeline's copy of the
 * weights is cities/bakersfield/config.py, and tests/ui-contract.cjs fails if the two
 * ever disagree.
 */
/* HEAT IS SCORED IN THIS BUILD (45%), unlike Contra Costa. Every input is
 * normalised min-max WITHIN the study area, which assumes the study area is one
 * climate. Bakersfield is: one flat valley floor about 30 km across with no
 * marine gradient, so a hotter cell here really is a hotter place to live rather
 * than a different climate. Measured summer surface range 32-59 C (summers 2024-2026).
 *
 * A/C ships at 0 because it is NEARLY UNIFORM here: Census LACE 2023 puts A/C
 * in 96.5-100% of occupied homes across ranked cells (median 99.8%). Scaling
 * that 3.5-point modelled spread to 0-1 would score noise, so the input is
 * shown and movable but carries no default weight (the "Homes without A/C"
 * preset turns it on). Do not describe A/C as modelled from income — it is a
 * Census estimate, with the income model surviving only as a per-tract fallback.
 *
 * `access` ships at 0 — present, movable, off. Mirrors cities/bakersfield/config.py WEIGHTS; tests/ui-contract.cjs checks that.
 *
 * `dac` — SB 535 DISADVANTAGED COMMUNITIES (CalEPA, final designation September
 * 2026, CalEnviroScreen 5.0) — ships at 0 in the recommended mix and leads the
 * "Disadvantaged communities" preset. The city's planting program puts at least
 * 80% of new trees in designated tracts, so the preset is the question that
 * program asks: within the commitment, where are heat and missing shade worst?
 * A designation is a policy screen, not a need measurement, which is why it
 * is not in the recommended mix. Also a map layer ("SB 535 community"). */
window.CE_CITY={
  slug:'bakersfield',
  name:"Bakersfield",
  possessive:"Bakersfield’s",   // "Built for …’s urban forestry, climate and public works teams"
  districtUnit:'ward',               // what this city calls its council areas (By ward / By district)
  wardsOutsideLabel:"Unincorporated (Kern County)",
  scope:'city',                         // "relative within this city"
  dataVersion:'20261111-places',
  // How 03_census.py placed residents in this build (guide.html says why); the briefing's source table reads it.
  places:true,                          // schools, bus stops and parks measured by pipeline 04j (data/people_places_bakersfield.geojson)
  nameKind:'streets',                   // areas are named by cross streets (pipeline 04i), not nearest place
  popAllocation:'dasymetric',
  buildingsSource:'City of Bakersfield GIS building footprints (last edited July 2026), residential use type, each weighted by its 2020 Census block’s residents (homes built since are added)',
  centersVersion:'20260908-kern',
  layerNotes:{ac:"Nearly every home here has A/C (96.5–100% of occupied homes across ranked areas), so this layer shows almost no contrast and carries no weight in the recommended mix.",
    dac:"Bakersfield’s planting program commits at least 80% of new trees to SB 535-designated tracts. The “Disadvantaged communities” preset ranks within that commitment."},
  coolingLinkLabel:"County-listed cooling centers & contacts ↗",
  scoreTitle:"Heat & canopy priority",
  weights:{heat:0.45,green:0.35,ac:0.00,age65:0.20,access:0,dac:0.00},
  inputNotes:{heat:"hotter cell → higher risk",ac:"Census LACE estimate — nearly uniform here, starts at 0",dac:"CalEPA 2026 designation — a policy screen, starts at 0"},
  /** Presets set all four weights at once. w:'default' / pop:'default' mean the
   *  recommended weights and population multiplier above. */
  presets:[
  {id:'default',name:'Recommended mix',w:'default',pop:'default',
   why:'Ground heat (45%), missing tree cover (35%) and older residents (20%), adjusted for how many people live in each area. A/C is not scored: nearly every home here has it.'},
  {id:'dac',name:'Disadvantaged communities',w:{heat:.30,green:.30,ac:0,age65:.05,access:0,dac:.35},pop:'default',
   why:'SB 535-designated disadvantaged communities (35%), ground heat (30%) and missing tree cover (30%), with older residents (5%), adjusted for population. The view for a program that commits most of its trees to designated tracts: hot, bare areas inside them lead; the same conditions outside them rank lower but stay on the list.'},
  {id:'canopy',name:'Fewest trees',w:{heat:0,green:1,ac:0,age65:0,access:0,dac:0},pop:.45,
   why:'Tree cover alone, adjusted for population. Ignores heat and age.'},
  {id:'heat',name:'Heat first',w:{heat:.70,green:.15,ac:.10,age65:.05,access:0,dac:0},pop:.45,
   why:'Mostly ground heat. Bakersfield is one valley climate, so a hotter area really is a hotter place to live.'},
  {id:'seniors',name:'Older residents',w:{heat:.25,green:.15,ac:.15,age65:.45,access:0,dac:0},pop:.45,
   why:'Puts most weight on residents aged 65+, with heat, tree cover and A/C still counting.'},
  {id:'ac',name:'Homes without A/C',w:{heat:.25,green:.10,ac:.60,age65:.05,access:0,dac:0},pop:.45,
   why:'Puts most weight on homes without air conditioning. Almost every home here has A/C, so this view changes little.'},
  {id:'stranded',name:'Far from cooling',w:{heat:.30,green:.20,ac:.20,age65:.10,access:.20,dac:0},pop:.45,
   why:'Adds walking distance to the nearest mapped cool place. Those places are not verified as open cooling centers.'},
  {id:'people',name:'Most people',w:'default',pop:.90,
   why:'The recommended mix, but areas with more residents count much more.'},
  ],
};
