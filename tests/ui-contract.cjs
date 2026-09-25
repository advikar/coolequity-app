// Run with node tests/ui-contract.cjs [slug ...]. Uses only Node built-ins.
// With no arguments it checks every city listed in app/cities.js.
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const html=fs.readFileSync('app/index.html','utf8');
for(const m of html.replace(/<!--[\s\S]*?-->/g,'').matchAll(/<script(?:\s[^>]*)?>([\s\S]*?)<\/script>/g))new vm.Script(m[1]);
new vm.Script(fs.readFileSync('app/guide.js','utf8'));
const load=(file,name)=>{const c={window:{}};vm.createContext(c);vm.runInContext(fs.readFileSync(file,'utf8'),c);return JSON.parse(JSON.stringify(c.window[name]));};
const CITIES=load('app/cities.js','CE_CITIES');
// Per-city facts of the committed data, carried over from each city's former branch.
const EXPECT={
  contracosta:{res:2697,ndvi:5},     // after 02f: lidar canopy replaces the stand-in wherever the CDFW map covers the cell
  sanramon:{res:419,ndvi:0},
  bakersfield:{res:3767,ndvi:62},
  westcc:{res:982,ndvi:1},
  pittsburg:{res:570,ndvi:0},
};
const want=process.argv.slice(2);
const slugs=want.length?want:CITIES.map(c=>c.slug);
assert.deepEqual([...slugs].sort(),[...new Set(slugs)].sort());
assert.deepEqual(CITIES.map(c=>c.slug).sort(),Object.keys(EXPECT).sort(),'EXPECT must cover every city in app/cities.js');
for(const slug of slugs){
const CITY=load(`cities/${slug}/city.js`,'CE_CITY');
assert(CITY&&CITY.slug===slug,`cities/${slug}/city.js must declare slug ${slug}`);
console.log(`\n== ${CITY.name} (${slug})`);
// The map's recommended weights and the pipeline's must be the same numbers.
const py=fs.readFileSync(`cities/${slug}/config.py`,'utf8');
const pyW=Object.fromEntries([...py.slice(py.indexOf('WEIGHTS = {'),py.indexOf('}',py.indexOf('WEIGHTS = {'))).matchAll(/"(heat|green|ac|age65)":\s*([0-9.]+)/g)].map(m=>[m[1],Number(m[2])]));
assert.deepEqual(Object.keys(pyW).sort(),['ac','age65','green','heat']);
for(const k of Object.keys(pyW))assert.equal(CITY.weights[k],pyW[k],`${slug}: city.js weight ${k} differs from config.py`);
assert.equal(CITY.weights.access,0);
for(const pr of CITY.presets){if(pr.w!=='default')for(const k of ['heat','green','ac','age65','access'])assert.equal(typeof pr.w[k],'number',`${slug} preset ${pr.id} weight ${k}`);}
assert(CITY.presets.some(pr=>pr.id==='default'&&pr.w==='default'&&pr.pop==='default'),`${slug}: needs the default preset`);
const guide=fs.readFileSync(`cities/${slug}/guide.html`,'utf8');
const ids=new Set([...guide.matchAll(/\bid="([^"]+)"/g)].map(m=>m[1]));
for(const m of html.matchAll(/guide\.html#([a-z0-9-]+)["']/g))assert(ids.has(m[1]),'Missing guide anchor '+m[1]);
for(const id of ['lst','green','pop','pct65','ac','access','score','holc','planting','cost','weights','export','export-area','popweight'])assert(ids.has(id));
const DATA_PATH=`cities/${slug}/data/${slug}.geojson`;
const data=JSON.parse(fs.readFileSync(DATA_PATH,'utf8'));
const nodes=new Map();const node=id=>{if(!nodes.has(id))nodes.set(id,{textContent:'',value:25,disabled:false,setAttribute(){}});return nodes.get(id);};
const ctx={document:{getElementById:node},CE_CITY:CITY,TREE_SPACING_M:10,TREE_M2:40,COST_TREE:500,SURVIVAL:70,costScope:()=>'planting only',areaOf:p=>p.area_m2,fInt:n=>Math.round(n).toLocaleString('en-US'),fTempD:v=>v.toFixed(2)+' C'};
vm.createContext(ctx);
const start=html.indexOf('const plantingShares=new Map();'),end=html.indexOf('function wireHover()',start);
vm.runInContext(html.slice(start,end),ctx);
let cases=0;
for(const f of data.features){const p=f.properties;let last=0;for(const share of [0,25,50,100]){node('roi-slider').value=share;node('roi-slider').disabled=!(p.street_m>0);ctx.p=p;vm.runInContext('updateROI(p)',ctx);if(!p.scenario_ok){assert.equal(node('roi-trees').textContent,'—');assert.equal(node('roi-cost').textContent,'—');assert.match(node("roi-note").textContent,/No (mapped|eligible) street/);cases++;continue;}const trees=Number(node('roi-trees').textContent.replaceAll(',',''));assert(trees>=last);assert(trees<=Math.floor((p.street_m||0)*2/10));const known=p.canopy_baseline_ok?Math.max(p.canopy_m2,p.green/100*p.area_m2):p.canopy_source==='usfs-2022'?p.canopy_m2:0;assert(trees*40<=Math.max(0,p.area_m2-known)+1);if(!p.canopy_baseline_ok&&trees>0)assert(!node('roi-note').textContent.includes('→'));assert(!/NaN|Infinity/.test([...nodes.values()].map(n=>n.textContent).join(' ')));if(share===0){assert.equal(trees,0);assert.equal(node('roi-cost').textContent,'≈$0');}last=trees;cases++;}}
assert.equal(data.features.filter(f=>f.properties.place==='res').length,EXPECT[slug].res);
assert.equal(data.features.filter(f=>f.properties.holc).length,0);
assert.equal(data.features.filter(f=>f.properties.place==='res'&&f.properties.green_src==='ndvi').length,EXPECT[slug].ndvi);
console.log(`PASS: syntax, guide anchors, residential count, HOLC availability, ${cases} scenario cases across ${data.features.length} cells.`);

// Rebuild invariants: stable geography/IDs, complete current schema, consecutive ranks.
const cp=require('node:child_process');
// Compared with the last commit, so a rebuild that moves cells or renumbers IDs fails.
let committed=null;try{committed=cp.execFileSync('git',['show','HEAD:'+DATA_PATH],{maxBuffer:40*1024*1024,encoding:'utf8',stdio:['ignore','pipe','ignore']});}catch(_){console.log('note: '+DATA_PATH+' is not committed yet; geography check compares the file with itself');}
const original=committed?JSON.parse(committed):data;
assert.deepEqual(data.features.map(f=>[f.properties.id,f.geometry]),original.features.map(f=>[f.properties.id,f.geometry]));
const ranked=data.features.filter(f=>f.properties.place==='res');
assert.deepEqual(ranked.map(f=>f.properties.rank).sort((a,b)=>a-b),Array.from({length:ranked.length},(_,i)=>i+1));
for(const f of data.features){assert(['canopy','ndvi'].includes(f.properties.green_src));assert.equal(typeof f.properties.scenario_ok,'boolean');}
for(const f of data.features){const p=f.properties;if(p.place==='res'){assert(Number.isInteger(p.rank_lo)&&Number.isInteger(p.rank_hi)&&p.rank_lo>=1&&p.rank_lo<=p.rank_hi&&p.rank_hi<=ranked.length,'rank band '+p.id);assert(p.rank_top_share>=0&&p.rank_top_share<=1);}else{assert.equal(p.rank_lo,null);}}
assert(data.metadata&&data.metadata.stability&&data.metadata.stability.draws>=100,'stability metadata');
console.log('PASS: stable geography, source/coverage metadata and consecutive rebuilt ranks.');
// Execute the actual browser scorer against the export, including its rounding and tie policy.
const live={score:new Map(),rank:new Map(),order:[]};
const scoring={HEX:data,CE_CITY:CITY,svals:data.norm,LIVE:live,POPW:.45,normW:()=>({...CITY.weights})};
scoring.svals.access_min=[0,Math.max(...data.features.map(f=>f.properties.access_min))];
vm.createContext(scoring);
vm.runInContext(html.slice(html.indexOf('function rescore(){'),html.indexOf('const sc=p=>')),scoring);
vm.runInContext('rescore()',scoring);
for(const f of ranked){const p=f.properties;assert.equal(live.rank.get(p.id),p.rank,'Browser/export rank mismatch '+p.id);assert(Math.abs(live.score.get(p.id)-p.score)<=.050001);}
console.log('PASS: browser/export scoring and rank parity for every residential cell.');

assert(!html.includes("+' pts'"));assert(html.includes('percentage-point canopy gain'));
const directory=fs.readFileSync(`cities/${slug}/cooling.html`,'utf8');for(const m of directory.matchAll(/<script>([\s\S]*?)<\/script>/g))new vm.Script(m[1]);

// Export (CE-06): the builder runs against the export, the CSV is well-formed and
// carries the weights, and a reload of its own JSON is accepted while a foreign
// city or schema is refused.
{
  const ex={HEX:data,CE_CITY:CITY,LIVE:{score:new Map(),rank:new Map(),order:[]},POPW:.45,W_RAW:{heat:.2,green:.5,ac:.2,age65:.1,access:0},W_INPUTS:[{k:'heat'},{k:'green'},{k:'ac'},{k:'age65'},{k:'access'}],
    CITY_NAV:[{slug:'x',name:'X'}],THIS_CITY:'x',CITY_SLUG:'x',DATA_URL:'../data/x.geojson?v=t',TREE_SPACING_M:10,TREE_M2:40,COST_TREE:500,SURVIVAL:70,
    nameOf:p=>p.name,areaOf:p=>p.area_m2,isDefaultW:()=>true,matchPreset:()=>({id:'default'}),selId:null,
    NOTES:new Map(),saveNotes(){},SHORTLIST:new Set(),saveShortlist(){},buildShortlist(){},FC_LABEL:{visit:'To visit',feasible:'Checked · feasible'},toast(){},markCostPreset:()=>{},
    document:{getElementById:()=>null,createElement:()=>({click(){},remove(){},style:{}}),body:{appendChild(){}}},
    Blob:function(){},URL:{createObjectURL:()=>'blob:',revokeObjectURL(){}},crypto:{subtle:{digest:async()=>new ArrayBuffer(32)}},TextEncoder,
    applyWeights(){},selectHex(){},setTimeout};
  ex.normW=()=>({heat:.2,green:.5,ac:.2,age65:.1,access:0});
  ex.noteOf=id=>ex.NOTES.get(id)||{status:'',note:'',updated:null};
  ex.sc=p=>ex.LIVE.score.get(p.id);ex.rk=p=>ex.LIVE.rank.get(p.id);
  vm.createContext(ex);
  vm.runInContext(html.slice(html.indexOf('const plantingShares=new Map();'),html.indexOf('function updateROI(p){')),ex);
  vm.runInContext(html.slice(html.indexOf('const EXPORT_SCHEMA='),html.indexOf('async function boot(){')),ex);
  const res=data.features.filter(f=>f.properties.place==='res');
  res.forEach((f,i)=>{ex.LIVE.score.set(f.properties.id,100-i/res.length*100);ex.LIVE.rank.set(f.properties.id,i+1);});
  ex.LIVE.order=res;
  const cell=res.find(f=>f.properties.scenario_ok)||res[0];
  ex.cellId=cell.properties.id;vm.runInContext('plantingShares.set(cellId,50)',ex);
  // save protection: nothing is dirty at the defaults; a cost-only edit, a survival-only edit and a share the user moved each are; saving or resetting clears it
  vm.runInContext('markSaved()',ex);
  assert.equal(vm.runInContext('isDirty()',ex),false,'defaults are not dirty');
  assert.equal(vm.runInContext('plantingShares.set(cellId,80);isDirty()',ex),false,'opening a cell (share recorded, not moved) is not dirty');
  assert.equal(vm.runInContext('COST_TREE=2000;isDirty()',ex),true,'cost-only edit is dirty');
  assert.equal(vm.runInContext('markSaved();isDirty()',ex),false,'saved state is clean');
  assert.equal(vm.runInContext('SURVIVAL=50;isDirty()',ex),true,'survival-only edit is dirty');
  vm.runInContext('SURVIVAL=70;COST_TREE=500;plantingShares.clear();markSaved()',ex);
  assert.equal(vm.runInContext('userShares.add(cellId);plantingShares.set(cellId,80);isDirty()',ex),true,'a share the user moved is dirty');
  vm.runInContext('plantingShares.clear();userShares.clear();plantingShares.set(cellId,50);markSaved()',ex);
  const header=vm.runInContext('exportHeader()',ex);
  assert.equal(header.export_schema,1);assert.equal(header.dataset.cells,data.features.length);assert.equal(header.dataset.ranked_cells,res.length);
  assert.deepEqual(Object.keys(header.weights),['heat','green','ac','age65','access']);
  ex.cellP=cell.properties;const rec=vm.runInContext('cellRecord(cellP)',ex);
  for(const k of vm.runInContext('EXPORT_FIELDS',ex))assert(k in rec,'export field '+k);
  assert.equal(rec.rank,ex.LIVE.rank.get(cell.properties.id));
  if(cell.properties.scenario_ok){assert.equal(rec.planting_share,50);assert(rec.trees>=0);assert.equal(rec.cost_usd,rec.trees*500);}
  ex.recs=res.slice(0,5).map(f=>vm.runInContext('cellRecord',ex)(f.properties));ex.header=header;
  const csv=vm.runInContext('toCsv(recs,header)',ex).split('\r\n').filter(Boolean);
  assert.equal(csv.length,6);const cols=csv[0].split(',');assert(cols.includes('weight_fewer_trees')&&cols.includes('dataset_sha256'));
  // Audit 2026-09-21: unique headers, the build slug separate from the cell's city, and the planting assumptions on every row.
  assert.equal(new Set(cols).size,cols.length,'duplicate CSV header: '+cols.filter((c,i)=>cols.indexOf(c)!==i));
  for(const c of ['city_or_community','study_area_slug','cost_per_tree_usd','cost_scope','survival_share_pct','tree_spacing_m','crown_m2_per_tree'])assert(cols.includes(c),'CSV column '+c);
  {const i=cols.indexOf('study_area_slug'),j=cols.indexOf('survival_share_pct');for(const line of csv.slice(1)){const v=line.split(',');assert.equal(v[i],'x');assert.equal(v[j],'70');}}
  // Greenness stand-ins export on the 0–100 index the app displays, never the stored 0–45 value; tree cover stays empty for them.
  {const nd=res.find(f=>f.properties.green_src==='ndvi');if(nd){ex.ndP=nd.properties;const r=vm.runInContext('cellRecord(ndP)',ex);
    assert.equal(r.canopy_pct,null);assert(Math.abs(r.greenness_index-nd.properties.green/45*100)<0.06,'greenness scale');}}
  for(const line of csv.slice(1))assert.equal(line.split(',').length,cols.length,'CSV column count');
  ex.doc={...header,kind:'ranked-list',cells:ex.recs};
  assert.equal(vm.runInContext('loadScenario(doc).ok',ex),true);
  assert.equal(vm.runInContext('isDirty()',ex),false,'a freshly loaded file is the saved state');assert.equal(vm.runInContext('COST_TREE=COST_TREE+1;isDirty()',ex),true,'an edit after loading is dirty');vm.runInContext('COST_TREE=COST_TREE-1;markSaved()',ex);
  ex.bad={...header,city_slug:'elsewhere'};assert.equal(vm.runInContext('loadScenario(bad).ok',ex),false);
  ex.old={...header,export_schema:0};assert.equal(vm.runInContext('loadScenario(old).ok',ex),false);
  assert.equal(vm.runInContext('plantingShares.get(cellP.id)',ex),50);
  // Field checks and the shortlist round-trip through a ranked-list file; a newer local note is kept.
  {const a=ex.recs[0].id,b=ex.recs[1].id;ex.NOTES.clear();ex.SHORTLIST.clear();
    ex.NOTES.set(b,{status:'feasible',note:'seen locally',updated:'2026-09-20T00:00:00.000Z'});
    ex.fdoc={...header,kind:'ranked-list',shortlist:[a,b,999999999],cells:ex.recs.map((r,i)=>i===0?{...r,field_status:'To visit',field_note:'check the strip',field_note_updated:'2026-09-19T00:00:00.000Z'}:i===1?{...r,field_status:'To visit',field_note:'older file note',field_note_updated:'2026-09-18T00:00:00.000Z'}:r)};
    const r=vm.runInContext('loadScenario(fdoc)',ex);assert.equal(r.ok,true);
    assert.deepEqual(JSON.parse(JSON.stringify(ex.NOTES.get(a))),{status:'visit',note:'check the strip',updated:'2026-09-19T00:00:00.000Z'});   // via JSON: the record was made inside the vm realm
    assert.equal(ex.NOTES.get(b).note,'seen locally','newer local note must be kept');
    assert.deepEqual([...ex.SHORTLIST],[a,b]);assert.match(r.msg,/1 field check, a shortlist of 2/);assert.match(r.msg,/1 field check in this browser is newer/);}
  console.log('PASS: scenario export builder, CSV shape, and reload acceptance/refusal.');
  // UX round 2: every info button has a popover card and every card points at a real guide topic.
  const tips=vm.runInContext('Object.keys(TIPS)',ex);
  for(const k of tips)assert(ids.has(k),'popover without guide topic '+k);
  for(const m of html.matchAll(/class="info-link" href="guide\.html#([a-z0-9-]+)"/g))assert(tips.includes(m[1]),'info button without popover '+m[1]);
  for(const k of ['lst','green','veg','pop','pct65','ac','access'])assert(tips.includes(k),'metric without popover '+k);
  for(const id of ['city-pick','city-nav','map-reset','map-zoom','legend-min','legend-show','rankwrap','sec-export','leave','legend','rank-change','coach-area','tg-access'])assert(html.includes(`id="${id}"`),'missing control '+id);
  assert(html.includes("let UNITS='imp'"));assert(!html.includes('sw-hint'));
  // Weights and layer are saved per city: one shared key carried them into the next city.
  const sessionKey=[...html.matchAll(/sessionStorage\.(?:getItem|setItem)\(([A-Z_]+)/g)].map(m=>m[1]);
  assert(sessionKey.length>=2&&sessionKey.every(k=>k==='SESSION_KEY'),'sessionStorage must go through SESSION_KEY');
  assert(html.includes("const SESSION_KEY='ce-session-'+CITY_SLUG;"),'SESSION_KEY must be scoped by city');
  console.log('PASS: popover coverage, guide links and wayfinding controls.');
}
}

// Export contracts (runs once, on the last city's data): a starred area exports the
// same scenario the shortlist displays even when its detail was never opened, the
// walking method survives export, and saving one area does not mark another
// area's edited share as saved.
{
  const slug=slugs[slugs.length-1],CITY=load(`cities/${slug}/city.js`,'CE_CITY'),data=JSON.parse(fs.readFileSync(`cities/${slug}/data/${slug}.geojson`,'utf8'));
  const src=(name)=>{const i=html.indexOf('function '+name+'(');assert(i>=0,name);let d=0,j=html.indexOf('{',i);for(;;j++){const c=html[j];if(c==='{')d++;else if(c==='}'&&--d===0)break;}return html.slice(i,j+1);};
  const ex={document:{getElementById:()=>null},console,JSON,Math,Set,Map,TREE_SPACING_M:10,TREE_M2:40,COST_TREE:500,SURVIVAL:70,
    areaOf:p=>p.area_m2,sc:p=>p.score,rk:p=>p.rank,nameOf:p=>p.name||'area',ndviIndex:v=>v,noteOf:()=>({}),FC_LABEL:{},
    W_INPUTS:[{k:'heat'},{k:'green'},{k:'ac'},{k:'age65'},{k:'access'}],normW:()=>({heat:.25,green:.25,ac:.25,age65:.25,access:0}),POPW:.5,
    HEX:data,CITY_SLUG:CITY.slug,selId:null,exportHeader:()=>({dataset:{}}),FIELD_KEY:{},download:()=>{},toCsv:()=>'',stamp:()=>'t',exportStatus:()=>{}};
  vm.createContext(ex);
  vm.runInContext('const plantingShares=new Map();const userShares=new Set();const SHORTLIST=new Set();let SAVED_SIG=null;',ex);
  for(const n of ['effectiveShare','scenarioFor','cellRecord','scenarioSig','markSaved','isDirty','singleAreaCapturesState','exportCell'])vm.runInContext(src(n),ex);
  const ok=data.features.filter(f=>f.properties.place==='res'&&f.properties.scenario_ok&&f.properties.street_m>200);
  assert(ok.length>=2);
  const A=ok[0].properties,B=ok[1].properties;
  // 1) star without opening detail: export must carry the 25% default the shortlist shows
  vm.runInContext(`SHORTLIST.add(${A.id})`,ex);
  ex.p=A;const rec=vm.runInContext('cellRecord(p)',ex),want=vm.runInContext('scenarioFor(p,25)',ex);
  assert.equal(rec.planting_share,25);assert.equal(rec.trees,want.trees);assert.equal(rec.cost_usd,want.cost_usd);
  assert(want.trees>0,'pick a cell with capacity');
  assert.equal(rec.access_src,A.access_src??null);
  ex.p=B;assert.equal(vm.runInContext('cellRecord(p)',ex).planting_share,null,'unstarred, unvisited area has no scenario');
  // 2) edit A and B, save A only: B's edit must stay unsaved
  vm.runInContext(`markSaved();plantingShares.set(${A.id},40);userShares.add(${A.id});plantingShares.set(${B.id},80);userShares.add(${B.id});`,ex);
  assert.equal(vm.runInContext('isDirty()',ex),true);
  ex.selId=A.id;vm.runInContext("exportCell('json')",ex);
  assert.equal(vm.runInContext('isDirty()',ex),true,'one-area save must not clear another area\'s unsaved share');
  // saving the only edited area does capture the state
  vm.runInContext(`plantingShares.delete(${B.id});userShares.delete(${B.id});`,ex);
  vm.runInContext("exportCell('json')",ex);
  assert.equal(vm.runInContext('isDirty()',ex),false);
  console.log('PASS: export contracts (shortlist default share, walk method, one-area save state).');
}
