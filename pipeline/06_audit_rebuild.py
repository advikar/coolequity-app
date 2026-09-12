"""Reproducible rank/source audit: python pipeline/06_audit_rebuild.py --baseline DIR.

DIR contains the previous <slug>.geojson, census and canopy CSVs. Run with
COOLEQUITY_CITY=<slug>; reports go to cities/<slug>/reports/. The report
compares browser-equivalent default ranks, not the legacy dense-rank export.
Weight variations are diagnostics, not confidence intervals or validated policy.
"""
import argparse,json,hashlib
from pathlib import Path
import numpy as np
import pandas as pd
import config as C

def ranked(doc, weights=None, source=None):
    W=C.WEIGHTS; weights=weights or (W['heat'],W['green'],W['ac'],W['age65'])
    d=pd.DataFrame([f['properties'] for f in doc['features']])
    ns={k:((d[k]-lo)/(hi-lo)).clip(0,1) for k,(lo,hi) in doc['norm'].items()}
    risk=weights[0]*ns['lst']+weights[1]*(1-ns['green'])+weights[2]*(1-ns['ac'])+weights[3]*ns['pct65']
    d['priority']=risk*(.55+.45*ns['pop'])
    d=d[d.place=='res']
    if source:d=d[d.canopy_source==source]
    return d.sort_values('priority',ascending=False,kind='stable').set_index('id')

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--baseline',type=Path,required=True);a=parser.parse_args()
    old=json.loads((a.baseline/C.OUT_FILE.name).read_text());new=json.loads(C.OUT_FILE.read_text())
    o,n=ranked(old),ranked(new);op=pd.Series(range(1,len(o)+1),index=o.index);np_=pd.Series(range(1,len(n)+1),index=n.index)
    compare=pd.DataFrame({'previous_rank':op,'current_rank':np_,'previous_score':o.score,'current_score':n.score,'previous_pop':o['pop'],'current_pop':n['pop'],'previous_ac':o.ac,'current_ac':n.ac})
    compare['rank_change']=compare.previous_rank-compare.current_rank
    target=C.REPORTS;target.mkdir(exist_ok=True);compare.to_csv(target/'rebuild_cell_changes.csv',index_label='id')
    rows=[]
    # Sensitivity grid centred on THIS city's canopy weight (0.25 in Bakersfield,
    # 0.55 in Contra Costa), never a fixed list that suits one city only.
    W=C.WEIGHTS; rest=1-W['heat']
    for canopy in sorted({round(min(rest,W['green']*k),4) for k in (0.65,1.0,1.35)}):
        for ac_share in [.25,.50,.75]:
            weights=(W['heat'],canopy,(rest-canopy)*ac_share,(rest-canopy)*(1-ac_share))
            r=ranked(new,weights);pos=pd.Series(range(1,len(r)+1),index=r.index)
            rows.append({'weights':list(weights),'top25_overlap':len(set(n.head(25).index)&set(r.head(25).index)),
                         'median_abs_rank_change':float((pos-np_).abs().median()),'max_abs_rank_change':int((pos-np_).abs().max())})
    nd=pd.DataFrame([f['properties'] for f in new['features']]);can=pd.read_csv(C.CANOPY_CSV)
    report={'residential_before':len(o),'residential_after':len(n),'population_before':int(sum(f['properties']['pop'] for f in old['features'])),
      'population_after':int(nd['pop'].sum()),'top25_overlap':len(set(o.head(25).index)&set(n.head(25).index)),
      'median_abs_rank_change':float(compare.rank_change.abs().median()),'max_abs_rank_change':int(compare.rank_change.abs().max()),
      'canopy_sources_all':nd.canopy_source.value_counts().to_dict(),'canopy_quality_all':nd.canopy_quality.value_counts().to_dict(),
      'residential_scenarios_enabled':int(n.scenario_ok.sum()),'positive_canopy_zero_area':int(((can.canopy_pct>0)&(can.canopy_m2<=0)).sum()),
      'weight_sensitivity':rows,'aerial_only_top25_overlap':len(set(n.head(25).index)&set(ranked(new,source='usfs-2022').head(25).index))}
    (target/'rebuild_summary.json').write_text(json.dumps(report,indent=2)+'\n')
    manifest={'build_date':'2026-09-08','city':C.CITY,'acs':'2020–2024 five-year, block groups','lace':'2023 tract estimates',
      'acs_api':'https://api.census.gov/data/2024/acs/acs5','boundary':'https://www2.census.gov/geo/tiger/GENZ2024/shp/cb_2024_06_bg_500k.zip',
      'weights':C.WEIGHTS,
      'canopy':'USFS/CAL FIRE 2022 aerial; legacy CHM 2009–2020; missing canopy retains NDVI for ranking',
      'canopy_coverage_rule':'Scenarios require mapped street capacity; >=99% USFS coverage only enables whole-cell canopy baseline totals',
      'sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [C.ACS_FILE,C.CENSUS_CSV,C.CANOPY_CSV,C.OUT_FILE,C.CENTERS_FILE,C.OVERLAYS_CSV,C.DATA/f'cooling_directory_{C.SLUG}.json']}}
    (target/'source_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='weight_sensitivity'},indent=2))
if __name__=='__main__':main()
