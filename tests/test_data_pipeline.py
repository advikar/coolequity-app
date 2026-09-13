"""Data contracts for ONE city, chosen with COOLEQUITY_CITY.

Run every city with scripts/test.sh, or one with
    COOLEQUITY_CITY=bakersfield .venv/bin/python -m unittest discover -s tests -p 'test_*.py'
"""
import importlib.util
import sys
import unittest
from pathlib import Path
import numpy as np
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'pipeline'))
import config as C
def module(name, path):
    spec=importlib.util.spec_from_file_location(name,path)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
canopy=module('canopy','pipeline/02d_canopy_usfs.py')
census=module('census','pipeline/03_census.py')
access=module('access','pipeline/04b_routed_access.py')
class DataContracts(unittest.TestCase):
    def test_walk_access_fallback_rules(self):
        # 0 ordinary routed; 1 unreachable; 2 detour + off-network; 3 detour on the
        # network (barrier); 4 ordinary with a long snap.
        routed=np.array([1000.,np.nan,9000.,9000.,1200.])
        crow=np.array([800.,800.,2000.,2000.,1000.])
        snap=np.array([50.,50.,600.,120.,140.])
        detour=access.detour_mask(routed,crow)
        self.assertEqual(detour.tolist(),[False,False,True,True,False])
        src,final,q=access.finalize_access(routed,crow,snap,detour)
        self.assertEqual(src.tolist(),['routed','straightline','straightline','routed','routed'])
        # a flagged cell whose network is a fragment is off-network even with a short snap
        src2,final2,_=access.finalize_access(routed,crow,snap,detour,pocket=[False,False,False,True,False])
        self.assertEqual(src2[3],'straightline');self.assertAlmostEqual(final2[3],2000*access.C.CIRCUITY)
        self.assertEqual(q.tolist(),['network-estimate','network-estimate','detour-review','detour-review','approach-review'])
        self.assertAlmostEqual(final[1],800*access.C.CIRCUITY);self.assertAlmostEqual(final[2],2000*access.C.CIRCUITY)
        self.assertEqual(final[3],9000.);self.assertEqual(final[0],1000.)
    def test_fallback_is_atomic_and_aligned(self):
        out=pd.DataFrame({'h3':['a','b','c'],'canopy_pct':[0,np.nan,np.nan],
            'canopy_m2':[0,0,0],'row_m2':[1,0,0],'row_canopy_pct':[0,0,0],
            'assessed_m2':[100,0,0],'coverage_frac':[1,0,0],
            'canopy_source':['usfs-2022','none','none'],'canopy_year':['2022','',''],
            'canopy_quality':['full','unassessed','unassessed']})
        chm=pd.DataFrame({'h3':['b','a'],'canopy_pct':[20,99],
            'canopy_m2':[200,990],'row_m2':[30,90],'row_canopy_pct':[4,9]})
        result,n=canopy.fill_legacy_canopy(out,chm);r=result.set_index('h3')
        self.assertEqual(n,1);self.assertEqual(r.loc['a','canopy_pct'],0)
        self.assertEqual(r.loc['b','canopy_m2'],200);self.assertEqual(r.loc['b','row_m2'],30)
        self.assertTrue(pd.isna(r.loc['b','coverage_frac']))
        self.assertTrue(pd.isna(r.loc['c','canopy_pct']))
    def test_boundary_mismatch_fails(self):
        with self.assertRaises(ValueError): canopy._match_boundary('Antioch',['Other.shp'])
    def test_housing_weighting_and_reconciliation(self):
        d=pd.DataFrame({'h3':['mix','mix','single','zero','partial','partial'],
            'GEOID':['a'*11+'1','b'*11+'1','a'*11+'1','a'*11+'1','a'*11+'1','c'*11+'1'],
            'occupied':[100,300,100,0,100,100],'frac':[.5,.5,.5,1,.5,.5],
            'pop':[1000,100,1000,0,1000,1000]})
        r=census.aggregate_ac(d,{'a'*11:20,'b'*11:100})
        self.assertAlmostEqual(r.loc['mix','ac_meas'],80)
        self.assertAlmostEqual(r.loc['single','ac_meas'],20)
        self.assertAlmostEqual(r['occupied'].sum(),350)
        self.assertAlmostEqual(r['ac_homes'].sum(),180)
        self.assertTrue(pd.isna(r.loc['zero','ac_meas']))
        self.assertTrue(pd.isna(r.loc['partial','ac_meas']))
        self.assertEqual(r.loc['partial','ac_coverage'],.5)
    def test_missing_housing_fails(self):
        with self.assertRaises(ValueError): census.aggregate_ac(pd.DataFrame({'h3':['a']}),{})
    def test_export_coverage_and_area(self):
        import json
        features=json.loads(C.OUT_FILE.read_text())['features']
        c=pd.read_csv(C.CANOPY_CSV)
        self.assertFalse(((c.canopy_pct>0)&(c.canopy_m2<=0)).any())
        usfs=c[c.canopy_source=='usfs-2022']
        np.testing.assert_allclose(usfs.canopy_m2,usfs.canopy_pct/100*usfs.assessed_m2,atol=.51)
        income_model=0
        for f in features:
            p=f['properties']
            self.assertEqual(p['canopy_baseline_ok'],p['canopy_source']=='usfs-2022' and p['coverage_frac']>=.99)
            self.assertEqual(p['scenario_ok'],p['street_m']>0 and p['area_m2']>0)
            if p['place']=='res':
                # A tract the Census suppresses in LACE keeps the income model, flagged
                # (the app greys it out and says "income estimate"); it must stay rare.
                if p['ac_src']=='income-model' and p.get('ac_coverage') is None: income_model+=1
                else: self.assertIn(p['ac_src'],('lace','lace-pop'))
            self.assertEqual(p['acs_year'],2024)
        nres=sum(1 for f in features if f['properties']['place']=='res')
        self.assertLessEqual(income_model, max(1, nres//200), 'income-model A/C must stay under 0.5% of residential cells')
if __name__=='__main__':unittest.main()

class CoolingSources(unittest.TestCase):
    def test_specific_library_exclusions(self):
        import cooling_sources
        from cooling_sources import eligible_discovery_sites
        def feature(name,kind='library'):
            return {'properties':{'name':name,'kind':kind}}
        original={'features':[feature('Excluded Library'),feature('Excluded Library','community_centre'),feature('Other Library')]}
        saved=cooling_sources.NO_AC_LIBRARIES
        try:
            cooling_sources.NO_AC_LIBRARIES={'Excluded Library'}
            result=eligible_discovery_sites(original)
        finally:
            cooling_sources.NO_AC_LIBRARIES=saved
        self.assertEqual(len(result['features']),2)
        self.assertEqual(len(original['features']),3)
        self.assertEqual(result['features'][0]['properties']['kind'],'community_centre')
        # None of the fixture names is a real exclusion, so the hook must be a no-op.
        self.assertEqual(len(eligible_discovery_sites(original)['features']),3)
    def test_official_directory_has_no_invented_live_status(self):
        import json
        d=json.loads((C.DATA/f'cooling_directory_{C.SLUG}.json').read_text())
        # (site count, revision text) of each city's published directory. Contra
        # Costa and San Ramon share the county EHSD bulletin; Kern lists one phone
        # line for all of its centers instead of a number per site.
        count,revision={'contracosta':(17,'June 2026'),'sanramon':(17,'June 2026'),
                        'bakersfield':(10,'2026 season'),'westcc':(17,'June 2026')}[C.SLUG]
        self.assertEqual(len(d['sites']),count)
        for s in d['sites']:
            self.assertIsNone(s['opening_hours']);self.assertIsNone(s['coordinates'])
            self.assertTrue(s['address']);self.assertTrue(s['phone'] or d['contact_phone'])
        self.assertIn(revision,d['source_revision'])
