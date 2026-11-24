#!/usr/bin/env python3
"""Static layered PSD sanity check, not a substitute for Cubism rig testing."""
import argparse,sys,json

def main(path):
    try:
        from psd_tools import PSDImage
    except ImportError:
        print('Install dependency: python -m pip install psd-tools')
        return 2
    psd=PSDImage.open(path)
    layers=[]
    def walk(group,depth=0):
        for layer in group:
            layers.append({'name':layer.name,'depth':depth,'visible':layer.is_visible(),'group':layer.is_group()})
            if layer.is_group():walk(layer,depth+1)
    walk(psd)
    leaves=[p for p in layers if not p['group']]
    groups=[p for p in layers if p['group']]
    report={'width':psd.width,'height':psd.height,'groups':len(groups),'art_layers':len(leaves),'distinct_names':len({x['name'] for x in leaves}),'warnings':[]}
    if len(leaves)<20:report['warnings'].append('Fewer than 20 artwork layers: likely insufficient for sophisticated full-body facial/hair rigging; inspect manually.')
    if len({x['name'] for x in leaves})!=len(leaves):report['warnings'].append('Duplicate artwork layer names: rename for stable tracking.')
    if not any('eye' in x['name'].lower() for x in leaves):report['warnings'].append('No eye-named layer detected.')
    if not any('mouth' in x['name'].lower() for x in leaves):report['warnings'].append('No mouth-named layer detected.')
    print(json.dumps(report,indent=2))
    return 0 if len(leaves)>=20 and not report['warnings'] else 1

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('psd');a=p.parse_args();sys.exit(main(a.psd))
